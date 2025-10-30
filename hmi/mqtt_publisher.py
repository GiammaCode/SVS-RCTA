import paho.mqtt.client as mqtt
import json
import config


class MqttPublisher:
    """
    Gestisce la connessione e la pubblicazione al broker MQTT.
    """

    def __init__(self, broker_address=config.MQTT_BROKER, port=config.MQTT_PORT):
        self.broker_address = broker_address
        self.port = port
        self.topic = config.MQTT_TOPIC_ALERTS

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self.is_connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"HMI Publisher: Connesso con successo al broker MQTT a {self.broker_address}")
            self.is_connected = True
        else:
            print(f"HMI Publisher: Connessione fallita, codice: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print("HMI Publisher: Disconnesso dal broker MQTT.")

    def connect(self):
        """Tenta di connettersi al broker."""
        try:
            print(f"HMI Publisher: Tentativo di connessione a {self.broker_address}:{self.port}...")
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()  # Gestisce la riconnessione e il traffico in background
        except ConnectionRefusedError:
            print(f"ERRORE CRITICO: Connessione MQTT rifiutata. Il broker è in esecuzione?")
        except Exception as e:
            print(f"ERRORE CRITICO: Impossibile connettersi a MQTT: {e}")

    def disconnect(self):
        """Si disconnette dal broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_status(self, dangerous_objects_list):
        """
        Pubblica lo stato RCTA (allarme o "libero").
        :param dangerous_objects_list: Lista di classi di oggetti pericolosi.
        """
        if not self.is_connected:
            # Non tentare di pubblicare se non siamo connessi
            return

        if dangerous_objects_list:
            # Caso 1: Pericolo rilevato
            payload = {
                "alert": True,
                "objects": dangerous_objects_list
            }
        else:
            # Caso 2: Nessun pericolo
            payload = {
                "alert": False,
                "objects": []
            }

        # Converti il dizionario in una stringa JSON
        payload_str = json.dumps(payload)

        # Pubblica sul topic
        result = self.client.publish(self.topic, payload_str)

        # Controllo di debug
        if result[0] != 0:
            print(f"HMI Publisher: Errore nel pubblicare il messaggio (Codice: {result[0]})")
        # else:
        #     if payload['alert']:
        #         print(f"HMI Publisher: Messaggio di ALLARME pubblicato.")
        #     else:
        #         print(f"HMI Publisher: Messaggio 'Libero' pubblicato.")