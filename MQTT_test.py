import time
import sys
import os

import config
from hmi.mqtt_publisher import MqttPublisher

def main():
    """
    Script test to try MQTT system
    """
    print("Starting MQTT test")
    publisher = None
    try:
        publisher = MqttPublisher(
            broker_address=config.MQTT_BROKER,
            port=config.MQTT_PORT
        )
        publisher.connect()

        print("Waiting broker connection")
        time.sleep(1)
        if not publisher.is_connected:
            print("ERROR: Broker not connected")
            return

        while True:
            alert1=["car"]
            print(f"Alert: {alert1} send")
            publisher.publish_status(alert1)
            time.sleep(3)

            safe=[]
            print(f"Safe send")
            publisher.publish_status(safe)
            time.sleep(3)

            alert2 = ["person", "truck"]
            print(f"Alert: {alert2} send")
            publisher.publish_status(alert2)
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n--- Test interrotto dall'utente ---")
    except Exception as e:
        print(f"\nSi è verificato un errore inatteso: {e}")
    finally:
        if publisher and publisher.is_connected:
            publisher.disconnect()
            print("Publisher disconnesso.")

if __name__ == '__main__':
        main()