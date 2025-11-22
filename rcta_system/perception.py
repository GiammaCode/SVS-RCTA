import threading
import numpy as np
import cv2
import time
import config
import numba
from queue import Queue, Empty
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


class CameraWorker:
    """
    Worker thread dedicato per elaborazione asincrona di una singola camera.
    Ogni camera ha il suo thread che esegue inferenze YOLO in parallelo.
    """

    def __init__(self, camera_name, detector, perception_ref):
        self.camera_name = camera_name
        self.detector = detector
        self.perception_ref = perception_ref

        # Queue per ricevere coppie (rgb, depth) dalle callback
        self.input_queue = Queue(maxsize=2)  # Buffer di 2 frame max

        # Dati locali del worker per tracking
        self.tracked_objects = {}
        self.last_cleanup_time = 0.0

        # Thread control
        self.running = False
        self.thread = None

    def start(self):
        """Avvia il thread worker"""
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        print(f"PERCEPTION [{self.camera_name.upper()} worker thread started]")

    def stop(self):
        """Ferma il thread worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def enqueue_frame(self, rgb_carla, depth_carla):
        """
        Chiamato dalle callback CARLA per accodare nuovi frame.
        Non-blocking: scarta frame vecchi se la coda è piena.
        """
        try:
            self.input_queue.put_nowait((rgb_carla, depth_carla))
        except:
            pass  # Queue piena, ignora questo frame

    def _worker_loop(self):
        """Loop principale del worker thread - elabora frame continuamente"""
        while self.running:
            try:
                # Aspetta max 0.1s per un nuovo frame
                rgb_carla, depth_carla = self.input_queue.get(timeout=0.1)

                # Elabora il frame (inferenza YOLO + tracking + TTC)
                self._process_frame(rgb_carla, depth_carla)

            except Empty:
                continue  # Timeout, riprova
            except Exception as e:
                print(f"PERCEPTION [{self.camera_name.upper()} worker error: {e}]")

    def _process_frame(self, rgb_carla, depth_carla):
        """Elabora una coppia RGB-Depth (inferenza YOLO + fusione + tracking)"""

        # Converti da CARLA a numpy
        rgb_np = self.perception_ref._to_numpy_rgb(rgb_carla)
        depth_meters = self.perception_ref._to_depth_meters(depth_carla)
        timestamp = depth_carla.timestamp

        # INFERENZA YOLO (parte più lenta - ora in parallelo!)
        detections = self.detector.detect(rgb_np)

        # Fusione detection + depth
        fused_objects = self.perception_ref._fuse_results(detections, depth_meters)

        # Cleanup tracks obsoleti periodicamente
        if timestamp - self.last_cleanup_time > self.perception_ref.STALE_TRACK_THRESHOLD_SEC:
            self.perception_ref._cleanup_stale_tracks(timestamp, self.tracked_objects)
            self.last_cleanup_time = timestamp

        # Aggiorna tracking e calcola TTC
        self.perception_ref._update_tracks_and_calc_ttc(
            fused_objects, timestamp, self.tracked_objects
        )

        # Calcola metriche aggregate per questa zona
        min_dist = min((obj['dist'] for obj in fused_objects), default=float('inf'))
        min_sector_ttc = min((obj['ttc_obj'] for obj in fused_objects), default=float('inf'))

        # Prepara nuovi dati
        new_data = {
            'dist': min_dist,
            'ttc': min_sector_ttc,
            'objects': fused_objects
        }

        # Aggiorna dati condivisi in modo thread-safe
        with self.perception_ref.data_lock:
            self.perception_ref.perception_data[self.camera_name] = new_data
            # Salva frame per debug/visualizzazione
            setattr(self.perception_ref, f'display_frame_{self.camera_name}', rgb_np.copy())


class RctaPerception:
    """
    Sistema di percezione RCTA con architettura asincrona.
    Le 3 camere elaborano frame in parallelo tramite worker threads dedicati.
    """

    def __init__(self):
        print("PERCEPTION [Initializing ASYNC architecture with 3 parallel workers]")

        # Detector YOLO per ogni camera (modelli indipendenti)
        self.detector_rear = ObjectDetector()
        self.detector_left = ObjectDetector()
        self.detector_right = ObjectDetector()

        # Lock per accesso thread-safe ai dati condivisi
        self.data_lock = threading.Lock()

        # Dati di percezione condivisi (letti dal main, scritti dai worker)
        default_data = {'dist': float('inf'), 'ttc': float('inf'), 'objects': []}
        self.perception_data = {
            'rear': default_data.copy(),
            'left': default_data.copy(),
            'right': default_data.copy()
        }

        # Display frames (per debug/visualizzazione)
        self.display_frame_rear = None
        self.display_frame_left = None
        self.display_frame_right = None

        # Configurazione tracking
        self.STALE_TRACK_THRESHOLD_SEC = 1.0
        self.MIN_VELOCITY_FOR_TTC_MPS = 0.5

        # Worker threads - uno per camera
        self.worker_rear = CameraWorker('rear', self.detector_rear, self)
        self.worker_left = CameraWorker('left', self.detector_left, self)
        self.worker_right = CameraWorker('right', self.detector_right, self)

        # Avvia i worker
        self.worker_rear.start()
        self.worker_left.start()
        self.worker_right.start()

        print("PERCEPTION [All workers started - running in PARALLEL mode]")

    def shutdown(self):
        """Chiude tutti i worker threads (chiamare prima di terminare)"""
        print("PERCEPTION [Shutting down workers...]")
        self.worker_rear.stop()
        self.worker_left.stop()
        self.worker_right.stop()

    # ==================== CALLBACK CARLA ====================
    # Le callback sincronizzano RGB+Depth e li accodano ai worker

    def rear_rgb_callback(self, img):
        self._rear_rgb_temp = img
        # Se abbiamo anche depth, accoda la coppia al worker
        if hasattr(self, '_rear_depth_temp'):
            self.worker_rear.enqueue_frame(self._rear_rgb_temp, self._rear_depth_temp)

    def rear_depth_callback(self, img):
        self._rear_depth_temp = img
        if hasattr(self, '_rear_rgb_temp'):
            self.worker_rear.enqueue_frame(self._rear_rgb_temp, self._rear_depth_temp)

    def left_rgb_callback(self, img):
        self._left_rgb_temp = img
        if hasattr(self, '_left_depth_temp'):
            self.worker_left.enqueue_frame(self._left_rgb_temp, self._left_depth_temp)

    def left_depth_callback(self, img):
        self._left_depth_temp = img
        if hasattr(self, '_left_rgb_temp'):
            self.worker_left.enqueue_frame(self._left_rgb_temp, self._left_depth_temp)

    def right_rgb_callback(self, img):
        self._right_rgb_temp = img
        if hasattr(self, '_right_depth_temp'):
            self.worker_right.enqueue_frame(self._right_rgb_temp, self._right_depth_temp)

    def right_depth_callback(self, img):
        self._right_depth_temp = img
        if hasattr(self, '_right_rgb_temp'):
            self.worker_right.enqueue_frame(self._right_rgb_temp, self._right_depth_temp)

    # ==================== UTILITY METHODS ====================

    def _to_numpy_rgb(self, carla_img):
        """Converte immagine CARLA RGB in numpy array"""
        array = np.frombuffer(carla_img.raw_data, dtype=np.uint8)
        array = np.reshape(array, (carla_img.height, carla_img.width, 4))
        return array[:, :, :3]

    def _to_depth_meters(self, carla_img):
        """Converte immagine CARLA depth in mappa di profondità (metri)"""
        array_uint8 = np.frombuffer(carla_img.raw_data, dtype=np.uint8)
        array_uint8 = np.reshape(array_uint8, (carla_img.height, carla_img.width, 4))
        return _decode_depth_to_meters(array_uint8)

    def _fuse_results(self, detections, depth_map):
        """Fonde detection YOLO con depth map per ottenere distanze"""
        h, w = depth_map.shape
        fused = []

        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            # Clipping per evitare out-of-bounds
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)

            obj_dist = float('inf')
            if x1 < x2 and y1 < y2:
                roi = depth_map[y1:y2, x1:x2]
                if roi.size > 0:
                    # Usa percentile per robustezza a outlier
                    obj_dist = np.percentile(roi, 10)

            det['dist'] = obj_dist
            det['ttc_obj'] = float('inf')
            fused.append(det)
        return fused

    def _update_tracks_and_calc_ttc(self, current_objects, current_time, tracker_dict):
        """Aggiorna tracking degli oggetti e calcola TTC"""
        for obj in current_objects:
            track_id = obj['id']
            if track_id in tracker_dict:
                prev_state = tracker_dict[track_id]
                delta_t = current_time - prev_state['time']
                delta_d = prev_state['dist'] - obj['dist']  # positivo = si avvicina

                if delta_t > 0.0:
                    rel_velocity = delta_d / delta_t  # m/s
                    if rel_velocity > self.MIN_VELOCITY_FOR_TTC_MPS:
                        ttc = obj['dist'] / rel_velocity
                        obj['ttc_obj'] = ttc

            # Aggiorna stato tracking
            tracker_dict[track_id] = {
                'dist': obj['dist'],
                'time': current_time,
                'class': obj['class']
            }

    def _cleanup_stale_tracks(self, current_time, tracker_dict):
        """Rimuove tracks non aggiornati da troppo tempo"""
        stale_ids = [
            track_id for track_id, state in tracker_dict.items()
            if current_time - state['time'] > self.STALE_TRACK_THRESHOLD_SEC
        ]
        for track_id in stale_ids:
            del tracker_dict[track_id]

    # ==================== API PUBBLICA ====================

    def get_all_perception_data(self, is_reversing):
        """
        Legge gli ultimi dati di percezione disponibili (NON BLOCCANTE).

        I worker aggiornano i dati in background continuamente.
        Questa funzione ritorna immediatamente con i dati più recenti.

        IMPORTANTE: Nel vecchio sistema questo metodo bloccava per 3 inferenze YOLO (~150ms).
        Ora ritorna istantaneamente (~0.1ms) e i dati sono sempre aggiornati in background!
        """
        if not is_reversing:
            return self.perception_data

        # Leggi dati condivisi in modo thread-safe
        with self.data_lock:
            # Ritorna una copia per evitare race conditions
            return {
                'rear': self.perception_data['rear'].copy(),
                'left': self.perception_data['left'].copy(),
                'right': self.perception_data['right'].copy()
            }