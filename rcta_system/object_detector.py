from time import perf_counter
import numpy as np
import config
from ultralytics import YOLO
import time
import multiprocessing


class ObjectDetector:
    def __init__(self, model_path=config.YOLO_MODEL_PATH):
        # ... (Keep your existing __init__ logic exactly as it was) ...
        # I am omitting the print statements for brevity, keep yours
        try:
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            self.target_classes = {'person', 'bicycle', 'car', 'bus', 'truck'}
            self.target_class_indices = [
                k for k, v in self.class_names.items() if v in self.target_classes
            ]
            # Warmup
            dummy_img = np.zeros((config.CAMERA_IMAGE_HEIGHT, config.CAMERA_IMAGE_WIDTH, 3), dtype=np.uint8)
            self.model.track(dummy_img, verbose=False, persist=False)
        except Exception as e:
            print(f"OBJECT_DETECTOR [Error: {e}]")
            self.model = None

    def detect(self, rgb_image):
        # ... (Keep your existing detect logic exactly as it was) ...
        if self.model is None:
            return []

        results = self.model.track(
            rgb_image,
            verbose=False,
            classes=self.target_class_indices,
            conf=0.5,
            persist=True,
            half=True
        )

        if not results or results[0].boxes.id is None:
            return []

        boxes = results[0].boxes.cpu().numpy()
        detections = []

        for box in boxes:
            if box.id is None: continue
            detections.append({
                'id': int(box.id[0]),
                'class': self.class_names[int(box.cls[0])],
                'confidence': float(box.conf[0]),
                'bbox': box.xyxy[0].astype(int).tolist()
            })
        return detections


# --- NEW ADDITION: Worker Function for Multiprocessing ---
def run_detector_process(input_queue, output_queue, model_path):
    """
    This function runs in a separate process.
    It waits for an image, runs detection, and sends back results.
    """
    detector = ObjectDetector(model_path)

    while True:
        try:
            # Block until an image is available
            task = input_queue.get()

            # Sentinel value to kill process safely
            if task is None:
                break

            rgb_image, timestamp = task

            # Run inference
            detections = detector.detect(rgb_image)

            # Send results back to main process
            output_queue.put((detections, timestamp))

        except Exception as e:
            print(f"Process Error: {e}")
            continue