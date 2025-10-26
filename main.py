import carla
import time

import config
import carla_bridge.sensor_callbacks as sensor_manager
import scenarios.parking_lot_scenario as parking_lot
from carla_bridge.carla_manager import CarlaManager
from carla_bridge.spawner import Spawner

def main():
    try:
        with CarlaManager() as manager:
            print(f"Loading map: {config.MAP_NAME}")
            manager.client.load_world(config.MAP_NAME)

            manager.world = manager.client.get_world()
            manager.world.tick()
            print("Map loaded")

            spawner = Spawner(manager.world, manager.actor_list)
            ego_vehicle = parking_lot.setup_static_scenario(manager.world, spawner)

            if not ego_vehicle:
                print("Error, scenario creation failed")
                return

            print("Setting spectator view")
            spectator = manager.world.get_spectator()
            ego_transform = ego_vehicle.get_transform()

            # Posiziona lo spettatore 8m dietro e 5m sopra l'auto
            # uso 'get_forward_vector()' per essere relativi alla rotazione dell'auto
            spectator_transform = carla.Transform(
                ego_transform.location + ego_transform.get_forward_vector() * -8.0 + carla.Location(z=5.0),
                carla.Rotation(pitch=-30, yaw=ego_transform.rotation.yaw)  # Guarda in basso verso l'auto
            )
            spectator.set_transform(spectator_transform)


            print("Static scenario loaded")
            print("WASD to move camera")
            print("Ctrl + C to quit")

            while True:
                manager.world.tick()
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nScript interrotto dall'utente.")
    except Exception as e:(
        print(f"\nSi è verificato un errore: {e}"))

if __name__ == '__main__':
    main()
