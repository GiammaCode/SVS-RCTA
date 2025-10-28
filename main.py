import carla
import time

import config
import scenarios.parking_lot_scenario as parking_lot
from carla_bridge.carla_manager import CarlaManager
from carla_bridge.spawner import Spawner

def main():
    try:
        with CarlaManager() as manager:
            #load map
            print(f"Loading map: {config.MAP_NAME}")
            manager.client.load_world(config.MAP_NAME)
            manager.world = manager.client.get_world()
            manager.world.tick()
            print("Map loaded")

            #initialize spawner
            spawner = Spawner(manager.world, manager.actor_list)
            ego_vehicle, target_vehicle = parking_lot.setup_parking_scenario(manager.world, spawner)

            if not ego_vehicle or not target_vehicle:
                print("Error, scenario creation failed")
                return

            #setting spectator's view
            print("Setting spectator view")
            spectator = manager.world.get_spectator()

            spectator_transform = carla.Transform(
                config.EGO_SPAWN_TRANSFORM.location + carla.Location(x=20, y=10, z=10.0),
                carla.Rotation(pitch=-45, yaw=-150)  # Angolazione per vedere l'incrocio
            )
            spectator.set_transform(spectator_transform)

            print("Static scenario loaded")
            print("WASD to move camera")
            print("Ctrl + C to quit")

            while True:
                manager.world.tick()
                time.sleep(0.05) #20FPS

    except KeyboardInterrupt:
        print("\nScript interrotto dall'utente.")
    except Exception as e:(
        print(f"\nSi è verificato un errore: {e}"))

if __name__ == '__main__':
    main()
