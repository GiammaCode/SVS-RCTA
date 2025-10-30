import paho.mqtt.client as mqtt
import json
import sys
import os

# --- Hack per importare 'config' dalla directory principale ---
# Questo aggiunge la directory genitore (la root del progetto) al Python Path
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)
try:
    import config
except ImportError:
    print("ERRORE: Impossibile trovare config.py. Assicurati di eseguire dalla directory 'hmi'.")
    sys.exit(1)


# --- Fine Hack ---


def _on_connect(client, userdata, flags, rc):
    """Callback per quando ci si connette al broker."""
    if rc == 0:
        print(f"HMI Display: Connesso al broker {config.MQTT_BROKER}")
        # Sottoscrivi al topic degli alert
        client.subscribe(config.MQTT_TOPIC_ALERTS)
        print(f"HMI Display: Sottoscritto al topic '{config.MQTT_TOPIC_ALERTS}'")
    else:
        print(f"HMI Display: Connessione fallita, codice {rc}")


def _on_message(client, userdata, msg):
    """Callback per quando si riceve un messaggio."""
    # print(f"Ricevuto messaggio raw: {msg.payload.decode()}")
    try:
        # Decodifica il messaggio da JSON
        data = json.loads(msg.payload.decode())

        if data.get("alert") == True:
            objects = data.get("objects", [])
            print("\n" + "=" * 30)
            print("   --- ! ATTENZIONE RCTA ! ---")
            print(f"     Pericolo Rilevato: {', '.join(objects)}")
            print("=" * 30 + "\n")

        elif data.get("alert") == False:
            print("--- RCTA: Libero ---")

    except json.JSONDecodeError:
        print(f"HMI Display: Ricevuto messaggio non JSON: {msg.payload.decode()}")
    except Exception as e:
        print(f"HMI Display: Errore nell'elaborare il messaggio: {e}")


def main():
    """Funzione principale per avviare il client HMI."""
    client = mqtt.Client()
    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        print("Avvio HMI Display... In attesa di messaggi...")
        # loop_forever() blocca l'esecuzione e attende i messaggi
        client.loop_forever()

    except ConnectionRefusedError:
        print("\nERRORE: Impossibile connettersi al broker MQTT.")
        print(f"Assicurati che un broker (es. Mosquitto) sia in esecuzione su {config.MQTT_BROKER}:{config.MQTT_PORT}")
        print("Puoi avviarne uno con Docker: docker run -it -p 1883:1883 eclipse-mosquitto")
    except KeyboardInterrupt:
        print("\nSpegnimento HMI Display...")
        client.disconnect()


if __name__ == "__main__":
    main()