import numpy as np
import config


class DecisionMaker:
    """
    Analizza i dati di percezione (YOLO e Profondità) e lo stato del veicolo
    per determinare i pericoli basati su rilevamenti e TTC.
    """

    def __init__(self):
        print("DecisionMaker initializzato (con logica TTC).")
        # Carica le costanti dalla configurazione
        self.ttc_threshold = config.TTC_THRESHOLD
        self.cross_speed = config.CROSS_TRAFFIC_SPEED_MS  # m/s

    def evaluate(self, perception_data, is_reversing):
        """
        Logica decisionale principale.

        :param perception_data: Dizionario da RctaPerception
                                {'rear': [], 'left': float, 'right': float}
        :param is_reversing: Booleano che indica se il veicolo è in retromarcia
        :return: Lista di stringhe delle classi pericolose (es. ['car', 'depth_left'])
        """

        dangerous_alerts = []

        if not is_reversing:
            return []  # Se non siamo in retromarcia, nessun allarme RCTA

        # --- 1. Analizza la telecamera posteriore (Rilevamenti YOLO) ---
        # Questa logica è per gli oggetti statici *direttamente* dietro
        rear_detections = perception_data.get('rear', [])
        if rear_detections:
            # Estrai solo i nomi unici delle classi
            rear_classes = {obj['class'] for obj in rear_detections}
            dangerous_alerts.extend(list(rear_classes))

        # --- 2. Analizza la telecamera sinistra (TTC da Profondità) ---
        left_distance = perception_data.get('left', float('inf'))
        if left_distance < 100.0:  # Ignora distanze infinite o > 100m
            # Calcola il Time-to-Collision
            # TTC = Distanza (m) / Velocità (m/s)
            ttc_left = left_distance / self.cross_speed

            if ttc_left < self.ttc_threshold:
                # print(f"PERICOLO SINISTRA: TTC {ttc_left:.2f}s")
                dangerous_alerts.append("depth_left")  # Non sappiamo cosa sia, solo che è vicino

        # --- 3. Analizza la telecamera destra (TTC da Profondità) ---
        right_distance = perception_data.get('right', float('inf'))
        if right_distance < 100.0:
            ttc_right = right_distance / self.cross_speed

            if ttc_right < self.ttc_threshold:
                # print(f"PERICOLO DESTRA: TTC {ttc_right:.2f}s")
                dangerous_alerts.append("depth_right")

        # Restituisce una lista di allarmi unici
        return list(set(dangerous_alerts))