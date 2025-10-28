import numpy as np
from rcta_system.object_detector import ObjectDetector

class RctaPerception:
    """
    Manages vision-only perception for the rcta system.
    contains sensor callback.
    """
    def __init__(self):
        print("Strating RctaPerception (Vision-only)...")
        self.detector = ObjectDetector()

        self.detected_objects = {'rear': [], 'left': [], 'right': []}
        self.current_frames = {'rear': None, 'left': None, 'right': None}

    def _process_carla_image(self, carla_image):
        """
        Convert CARLA image in an NumPy array BGR
        """
        array = np.frombuffer(carla_image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (carla_image.height, carla_image.width, 4))  # RGBA
        array_bgr = array[:, :, :3]  # Prendi solo RGB (che è BGR in OpenCV)
        return array_bgr

    def rear_cam_callback(self, image):
        np_image = self._process_carla_image(image)
        self.detected_objects['rear'] = self.detector.detect(np_image)
        self.current_frames['rear'] = np_image

    def left_cam_callback(self, image):
        np_image = self._process_carla_image(image)
        self.detected_objects['left'] = self.detector.detect(np_image)
        self.current_frames['left'] = np_image

    def right_cam_callback(self, image):
        np_image = self._process_carla_image(image)
        self.detected_objects['right'] = self.detector.detect(np_image)
        self.current_frames['right'] = np_image

    def get_all_detections(self):
        """
        return a list of all object found
        """
        return (
                self.detected_objects['rear'] +
                self.detected_objects['left'] +
                self.detected_objects['right']
        )