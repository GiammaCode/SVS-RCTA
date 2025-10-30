import numpy as np
import config
from ultralytics import YOLO



class ObjectDetector:
    """
    Wrapper for the model YOLOv8
    """
    def __init__(self, model_path = config.YOLO_MODEL_PATH):
        """
        Charges the model from the path
        """
        print(f"loading of YOLO model from {model_path}")
        try:
            # 1. Carica il modello usando la nuova API
            self.model = YOLO(model_path)

            # 2. Ottieni i nomi delle classi dal modello (es. 'car', 'person')
            self.class_names = self.model.names

            # 3. Definisci le classi che ci interessano
            # (Questi sono i nomi delle classi di YOLOv8)
            self.target_classes = {'person', 'bicycle', 'car', 'bus', 'truck'}

            # Converti i nomi delle classi target in indici numerici
            self.target_class_indices = [
                k for k, v in self.class_names.items() if v in self.target_classes
            ]

            print(f"Modello YOLOv8 caricato. Classi target: {self.target_classes}")

        except Exception as e:
            print(f"ERRORE CRITICO: Impossibile caricare il modello YOLOv8 da {model_path}.")
            print(f"Assicurati che 'ultralytics' sia installato (pip install ultralytics)")
            print(f"Errore: {e}")
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

        # Esegui l'inferenza (questo è il nuovo modo)
        # Filtriamo già qui per classi e confidenza per essere più veloci
        results = self.model.predict(
            rgb_image,
            verbose=False,
            classes=self.target_class_indices,
            conf=0.5
        )

        detections = []

        # Estrai i risultati (questo è il nuovo modo, NIENTE PIÙ PANDAS)
        # results[0] contiene i rilevamenti per la prima (e unica) immagine
        for box in results[0].boxes.cpu().numpy():
            # Estrai le coordinate del Bounding Box
            bbox = [int(coord) for coord in box.xyxy[0]]

            # Estrai la confidenza
            conf = float(box.conf[0])

            # Estrai l'ID della classe e ottieni il nome
            class_id = int(box.cls[0])
            class_name = self.class_names[class_id]

            detections.append({
                'class': class_name,
                'confidence': conf,
                'bbox': bbox
            })

        return detections
