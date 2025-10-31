# test_connection.py - VERSIONE CORRETTA
import paho.mqtt.client as mqtt
import time


def test_connection():
    connected = False

    def on_connect(client, userdata, flags, rc, properties):
        nonlocal connected
        if rc == 0:
            print("✓ Connesso al broker MQTT")
            connected = True
        else:
            print(f"✗ Errore connessione: {rc}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    try:
        print("Tentativo di connessione a localhost:1883...")
        client.connect("localhost", 1883, 60)
        client.loop_start()

        # Aspetta massimo 5 secondi per la connessione
        for i in range(50):
            if connected:
                break
            time.sleep(0.1)

        if connected:
            print("Connessione stabilita con successo!")
            input("Premi Enter per terminare...")
        else:
            print("Timeout: connessione non stabilita")

    except Exception as e:
        print(f"Errore durante la connessione: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    test_connection()