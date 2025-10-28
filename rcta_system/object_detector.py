import torch
import numpy as np
import config

class ObjectDetector:
    """
    Wrapper for the model YOLOv5
    """
    def __init__(self, model_path = config.YOLO_MODEL_PATH):
        """
        Charges the model from the path
        """
        print(f"loading of YOLO model from {model_path}")
        try:
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            self.model.conf = 0.5 #Soglia di confidenza
            self.model.iou = 0.45 #soglia IoU per NMS
            #setting filter class [car, pedestrian, bike]
            self.model.classes = [1, 2, 3, 5, 7]  # person, bicycle, car, bus, truck

            print("YOLO model loaded with successfully")

        except Exception as e:
            print("ERROR: not possible to load YOLOv5")
            self.model = None

    def detect(self, bgr_image):
        """
        Catalogues a single image, NumPy format BGR

        :param brg_image: image in NumPy format
        :return: List of detected dictionary
        """
        if self.model is None:
            return[]

        # YOLO = RGB --> OpenCV (e CARLA) usa BGR.
        rgb_image = bgr_image[:, :, ::-1]

        #esegue inferenza
        result= self.model(rgb_image)

        #Estract result
        detections = []
        df = result.pandas.xyxy[0] #dataframe pandas

        for _, row in df.iterrows():
            detections.append({
                'class': row['name'],
                'confidence': row['confidence'],
                'bbox': [int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])]
            })

        return detections

