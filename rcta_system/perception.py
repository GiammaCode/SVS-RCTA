import asyncio
import threading
import numpy as np
import cv2
import time
import config
import numba
from rcta_system.object_detector import ObjectDetector


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
        print("PERCEPTION [Initializing with 3 Independent YOLO models]")
        self.detector_rear = ObjectDetector()
        self.latest_rear_rgb = None
        self.latest_rear_depth = None
        self.display_frame_rear = None

        self.detector_left = ObjectDetector()
        self.latest_left_rgb = None
        self.latest_left_depth = None
        self.display_frame_left = None

        self.detector_right = ObjectDetector()
        self.latest_right_rgb = None
        self.latest_right_depth = None
        self.display_frame_right = None

        default_data = {'dist': float('inf'), 'ttc': float('inf'), 'objects': []}
        self.perception_data = {
            'rear': default_data.copy(),
            'left': default_data.copy(),
            'right': default_data.copy()
        }

        self.tracked_objects_rear = {}
        self.tracked_objects_left = {}
        self.tracked_objects_right = {}

        self.last_cleanup_time_rear = 0.0
        self.last_cleanup_time_left = 0.0
        self.last_cleanup_time_right = 0.0

        self.STALE_TRACK_THRESHOLD_SEC = 1.0
        self.MIN_VELOCITY_FOR_TTC_MPS = 0.5

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
                'dist': obj['dist'],
                'time': current_time,
                'class': obj['class']
            }

    def _cleanup_stale_tracks(self, current_time, tracker_dict):
        stale_ids = [
            track_id for track_id, state in tracker_dict.items()
            if current_time - state['time'] > self.STALE_TRACK_THRESHOLD_SEC
        ]
        for track_id in stale_ids:
            del tracker_dict[track_id]

    # ========== METODI ASINCRONI ==========
    
    async def process_rear_camera_async(self):
        """Versione asincrona di process_rear_camera"""
        if self.latest_rear_rgb is None or self.latest_rear_depth is None:
            return

        rgb_carla = self.latest_rear_rgb
        depth_carla = self.latest_rear_depth

        # Conversioni (operazioni CPU-bound, ma veloci)
        rgb_np = self._to_numpy_rgb(rgb_carla)
        depth_meters = self._to_depth_meters(depth_carla)
        timestamp = depth_carla.timestamp

        # YOLO detection - operazione più pesante
        # Usiamo run_in_executor per non bloccare l'event loop
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None, 
            self.detector_rear.detect, 
            rgb_np
        )

        fused_objects = self._fuse_results(detections, depth_meters)

        if timestamp - self.last_cleanup_time_rear > self.STALE_TRACK_THRESHOLD_SEC:
            self._cleanup_stale_tracks(timestamp, self.tracked_objects_rear)
            self.last_cleanup_time_rear = timestamp

        self._update_tracks_and_calc_ttc(fused_objects, timestamp, self.tracked_objects_rear)

        min_dist = min((obj['dist'] for obj in fused_objects), default=float('inf'))
        min_sector_ttc = min((obj['ttc_obj'] for obj in fused_objects), default=float('inf'))

        self.display_frame_rear = rgb_np.copy()
        self.perception_data['rear'] = {
            'dist': min_dist,
            'ttc': min_sector_ttc,
            'objects': fused_objects
        }

    async def process_left_camera_async(self):
        """Versione asincrona di process_left_camera"""
        if self.latest_left_rgb is None or self.latest_left_depth is None:
            return

        rgb_carla = self.latest_left_rgb
        depth_carla = self.latest_left_depth

        rgb_np = self._to_numpy_rgb(rgb_carla)
        depth_meters = self._to_depth_meters(depth_carla)
        timestamp = depth_carla.timestamp

        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None,
            self.detector_left.detect,
            rgb_np
        )

        fused_objects = self._fuse_results(detections, depth_meters)

        if timestamp - self.last_cleanup_time_left > self.STALE_TRACK_THRESHOLD_SEC:
            self._cleanup_stale_tracks(timestamp, self.tracked_objects_left)
            self.last_cleanup_time_left = timestamp

        self._update_tracks_and_calc_ttc(fused_objects, timestamp, self.tracked_objects_left)

        min_dist = min((obj['dist'] for obj in fused_objects), default=float('inf'))
        min_sector_ttc = min((obj['ttc_obj'] for obj in fused_objects), default=float('inf'))

        self.display_frame_left = rgb_np.copy()
        self.perception_data['left'] = {
            'dist': min_dist,
            'ttc': min_sector_ttc,
            'objects': fused_objects
        }

    async def process_right_camera_async(self):
        """Versione asincrona di process_right_camera"""
        if self.latest_right_rgb is None or self.latest_right_depth is None:
            return

        rgb_carla = self.latest_right_rgb
        depth_carla = self.latest_right_depth

        rgb_np = self._to_numpy_rgb(rgb_carla)
        depth_meters = self._to_depth_meters(depth_carla)
        timestamp = depth_carla.timestamp

        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(
            None,
            self.detector_right.detect,
            rgb_np
        )

        fused_objects = self._fuse_results(detections, depth_meters)

        if timestamp - self.last_cleanup_time_right > self.STALE_TRACK_THRESHOLD_SEC:
            self._cleanup_stale_tracks(timestamp, self.tracked_objects_right)
            self.last_cleanup_time_right = timestamp

        self._update_tracks_and_calc_ttc(fused_objects, timestamp, self.tracked_objects_right)

        min_dist = min((obj['dist'] for obj in fused_objects), default=float('inf'))
        min_sector_ttc = min((obj['ttc_obj'] for obj in fused_objects), default=float('inf'))

        self.display_frame_right = rgb_np.copy()
        self.perception_data['right'] = {
            'dist': min_dist,
            'ttc': min_sector_ttc,
            'objects': fused_objects
        }

    async def _get_all_perception_data_async(self, is_reversing):
        """Esegue i tre process in parallelo"""
        if not is_reversing:
            return self.perception_data

        # Lancia le tre task in parallelo
        await asyncio.gather(
            self.process_rear_camera_async(),
            self.process_left_camera_async(),
            self.process_right_camera_async()
        )

        return self.perception_data

    def get_all_perception_data(self, is_reversing):
        """Wrapper sincrono per compatibilità con il main loop"""
        return asyncio.run(self._get_all_perception_data_async(is_reversing))