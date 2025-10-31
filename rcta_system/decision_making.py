import numpy as np


class DecisionMaker:
    """
    Analyze the detected object and the vehicle state.
    """

    def __init__(self):
        print("DecisionMaker initializzato.")
        # In futuro, qui si potrebbero caricare zone di pericolo

    def evaluate(self, detected_objects, is_reversing):
        """
        Main decision logic.

        :param detected_objects: List of detected objects.
        :param is_reversing: Boolean indicating if the vehicle is reversing or not.
        :return: List of string of dangerous objects ['car', 'person'] or void list
        """

        dangerous_objects_found = []

        if is_reversing and detected_objects:
            # Se siamo in retromarcia e abbiamo rilevato *qualcosa*,
            # lo consideriamo un potenziale pericolo.

            # Usiamo un 'set' per estrarre solo i nomi unici delle classi
            # (es. se rileva 3 'car', lo contiamo solo una volta)
            dangerous_classes = {obj['class'] for obj in detected_objects}

            dangerous_objects_found = list(dangerous_classes)

            # Logica di debug
            # print(f"DECISION: PERICOLO! Rilevati: {dangerous_objects_found}")

        return dangerous_objects_found