import numpy as np


class DecisionMaker:
    """
    Analizza i rilevamenti e lo stato del veicolo per determinare i pericoli.
    """

    def __init__(self):
        print("DecisionMaker initializzato.")
        # In futuro, qui si potrebbero caricare zone di pericolo, etc.

    def evaluate(self, detected_objects, is_reversing):
        """
        Logica decisionale principale.

        :param detected_objects: Lista di dizionari di rilevamento da RctaPerception
        :param is_reversing: Booleano che indica se il veicolo è in retromarcia
        :return: Lista di stringhe delle classi pericolose rilevate (es. ['car', 'person'])
                 o una lista vuota se non c'è pericolo.
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