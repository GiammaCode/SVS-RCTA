import threading
import multiprocessing
import numpy as np
import cv2
import time
import config
import numba
from rcta_system.object_detector import run_detector_process  # Import the worker


# ... (Keep _decode_depth_to_meters exactly as it was) ...
@numba.jit(nopython=True, fastmath=True)
def _decode_depth_to_meters(array_uint8):
    h, w, _ = array_uint8.shape
    depth_meters = np.empty((h, w), dtype=np.float32)
    inv_max_val = 1.0 / (256.0 * 256.0 * 256.0 - 1.0)
    for y in range(h):
        for x in range(w):
            B = float(array_uint8[y, x, 0])
            G = float(array_uint8[y, x, 1])
            R = float(array_uint8[y, x, 2])
            normalized = (R + G * 256.0 + B * 256.0 * 256.0) * inv_max_val
            depth_meters[y, x] = normalized * 1000.0
    return depth_meters


class RctaPerception:
    def __init__(self):
        print("PERCEPTION [Initializing Multiprocessing System]")

        # Data storage (Main Process)
        default_data = {'dist': float('inf'), 'ttc': float('inf'), 'objects': []}
        self.perception_data = {
            'rear': default_data.copy(),
            'left': default_data.copy(),
            'right': default_data.copy()
        }

        # Depth maps storage (needed for fusion in main thread)
        self.latest_depth_map = {
            'rear': None, 'left': None, 'right': None
        }

        # Tracking state (Main Process)
        self.tracked_objects = {
            'rear': {}, 'left': {}, 'right': {}
        }
        self.last_cleanup_time = {
            'rear': 0, 'left': 0, 'right': 0
        }

        self.STALE_TRACK_THRESHOLD_SEC = 1.0
        self.MIN_VELOCITY_FOR_TTC_MPS = 0.5

        # --- MULTIPROCESSING SETUP ---
        self.queues = {}
        self.processes = {}

        zones = ['rear', 'left', 'right']

        for zone in zones:
            # Create queues (maxsize=1 prevents lag buildup)
            in_q = multiprocessing.Queue(maxsize=1)
            out_q = multiprocessing.Queue(maxsize=1)

            # Start Process
            p = multiprocessing.Process(
                target=run_detector_process,
                args=(in_q, out_q, config.YOLO_MODEL_PATH),
                daemon=True
            )
            p.start()

            self.queues[zone] = {'in': in_q, 'out': out_q}
            self.processes[zone] = p

    # ... (Keep callbacks exactly as they were) ...
    def rear_rgb_callback(self, img):
        self.latest_rear_rgb = img

    def rear_depth_callback(self, img):
        self.latest_rear_depth = img

    def left_rgb_callback(self, img):
        self.latest_left_rgb = img

    def left_depth_callback(self, img):
        self.latest_left_depth = img

    def right_rgb_callback(self, img):
        self.latest_right_rgb = img

    def right_depth_callback(self, img):
        self.latest_right_depth = img

    def _to_numpy_rgb(self, carla_img):
        array = np.frombuffer(carla_img.raw_data, dtype=np.uint8)
        array = np.reshape(array, (carla_img.height, carla_img.width, 4))
        return array[:, :, :3]

    def _to_depth_meters(self, carla_img):
        array_uint8 = np.frombuffer(carla_img.raw_data, dtype=np.uint8)
        array_uint8 = np.reshape(array_uint8, (carla_img.height, carla_img.width, 4))
        return _decode_depth_to_meters(array_uint8)

    def _fuse_results(self, detections, depth_map):
        # (Keep logic identical to your original code)
        h, w = depth_map.shape
        fused = []
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            obj_dist = float('inf')
            if x1 < x2 and y1 < y2:
                roi = depth_map[y1:y2, x1:x2]
                if roi.size > 0:
                    obj_dist = np.percentile(roi, 10)
            det['dist'] = obj_dist
            det['ttc_obj'] = float('inf')
            fused.append(det)
        return fused

    def _update_tracks_and_calc_ttc(self, current_objects, current_time, tracker_dict):
        # (Keep logic identical to your original code)
        for obj in current_objects:
            track_id = obj['id']
            if track_id in tracker_dict:
                prev_state = tracker_dict[track_id]
                delta_t = current_time - prev_state['time']
                delta_d = prev_state['dist'] - obj['dist']
                if delta_t > 0.0:
                    rel_velocity = delta_d / delta_t
                    if rel_velocity > self.MIN_VELOCITY_FOR_TTC_MPS:
                        ttc = obj['dist'] / rel_velocity
                        obj['ttc_obj'] = ttc
            tracker_dict[track_id] = {
                'dist': obj['dist'], 'time': current_time, 'class': obj['class']
            }

    def _cleanup_stale_tracks(self, current_time, tracker_dict):
        stale_ids = [k for k, v in tracker_dict.items() if current_time - v['time'] > self.STALE_TRACK_THRESHOLD_SEC]
        for k in stale_ids: del tracker_dict[k]

    def _send_frame_async(self, zone, rgb_carla, depth_carla):
        """Prepares data and puts it in the worker queue non-blocking."""
        if rgb_carla is None or depth_carla is None: return

        # 1. Store depth map locally for later fusion (Depth is fast, we keep it in main thread)
        self.latest_depth_map[zone] = self._to_depth_meters(depth_carla)

        # 2. Convert RGB and send to Worker
        # Check if queue is empty to avoid lag. If full, we skip this frame (drop strategy)
        if self.queues[zone]['in'].empty():
            rgb_np = self._to_numpy_rgb(rgb_carla)
            # Use carla timestamp
            self.queues[zone]['in'].put((rgb_np, depth_carla.timestamp))

    def _update_results_async(self):
        """Checks all output queues for new YOLO detections."""
        for zone in ['rear', 'left', 'right']:
            out_q = self.queues[zone]['out']

            # Non-blocking check
            try:
                while not out_q.empty():
                    # Drain queue to get the very latest, or just get one
                    detections, timestamp = out_q.get_nowait()

                    # Fuse with the depth map we stored earlier
                    # Note: There might be a slight sync mismatch (ms), usually acceptable
                    depth_map = self.latest_depth_map[zone]

                    if depth_map is not None:
                        fused_objects = self._fuse_results(detections, depth_map)

                        # TTC Logic
                        tracker = self.tracked_objects[zone]
                        if timestamp - self.last_cleanup_time[zone] > self.STALE_TRACK_THRESHOLD_SEC:
                            self._cleanup_stale_tracks(timestamp, tracker)
                            self.last_cleanup_time[zone] = timestamp

                        self._update_tracks_and_calc_ttc(fused_objects, timestamp, tracker)

                        # Update Global State
                        min_dist = min((o['dist'] for o in fused_objects), default=float('inf'))
                        min_ttc = min((o['ttc_obj'] for o in fused_objects), default=float('inf'))

                        self.perception_data[zone] = {
                            'dist': min_dist, 'ttc': min_ttc, 'objects': fused_objects
                        }

                        # Set display frame for main.py debug
                        if zone == 'rear':
                            self.display_frame_rear = self._to_numpy_rgb(getattr(self, f"latest_{zone}_rgb"))
                        elif zone == 'left':
                            self.display_frame_left = self._to_numpy_rgb(getattr(self, f"latest_{zone}_rgb"))
                        elif zone == 'right':
                            self.display_frame_right = self._to_numpy_rgb(getattr(self, f"latest_{zone}_rgb"))

            except Exception:
                pass  # Queue empty

    def tick(self):
        """Called every loop iter to send frames and retrieve results."""
        # 1. Send latest frames to workers
        self._send_frame_async('rear', self.latest_rear_rgb, self.latest_rear_depth)
        self._send_frame_async('left', self.latest_left_rgb, self.latest_left_depth)
        self._send_frame_async('right', self.latest_right_rgb, self.latest_right_depth)

        # 2. Retrieve latest available results
        self._update_results_async()

    def get_perception_data(self):
        """Returns the current state immediately (non-blocking)."""
        return self.perception_data

    def cleanup(self):
        """Shutdown processes safely."""
        print("PERCEPTION [Stopping processes...]")
        for zone, q in self.queues.items():
            q['in'].put(None)  # Send sentinel
        for zone, p in self.processes.items():
            p.join(timeout=1.0)
            if p.is_alive(): p.terminate()