import carla

class BasicKeyController:
    """
    Un semplice controller per il veicolo che usa i tasti W, A, S, D.
    Pensato per essere usato con il loop di cv2.waitKey().

    W = Frena
    S = Retromarcia
    A = Sinistra
    D = Destra
    """

    def __init__(self, vehicle):
        self.vehicle = vehicle

    def parse_key(self, key):
        """
        Interpreta un tasto premuto da cv2.waitKey() e applica il controllo.
        """
        # Stato di default (nessun tasto premuto)
        throttle = 0.0
        brake = 0.0
        steer = 0.0
        reverse = False

        if key == ord('s'):
            # 's' per retromarcia (South)
            throttle = 0.5
            reverse = True
        elif key == ord('w'):
            # 'w' per frenare (Stop)
            brake = 1.0

        if key == ord('a'):
            # 'a' per sinistra
            steer = -0.5
        elif key == ord('d'):
            # 'd' per destra
            steer = 0.5

        # Applica il controllo al veicolo
        control = carla.VehicleControl(
            throttle=throttle,
            steer=steer,
            brake=brake,
            reverse=reverse
        )
        self.vehicle.apply_control(control)