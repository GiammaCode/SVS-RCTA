import carla
import time
import cv2
import config

from carla_bridge.carla_manager import CarlaManager
from carla_bridge.spawner import Spawner
from carla_bridge.sensor_manager import SensorManager
from scenarios.parking_lot_scenario import setup_parking_scenario
from rcta_system.perception import RctaPerception

def draw_detections(image, detections):
    """
    draws bounding box and image tag.
    modify image "in-place"
    """
    for det in detections:
        bbox = det['bbox']
        label = f"{det['class']} {det['confidence']:.2f}"

        cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        cv2.putText(image, label, (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

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
            ego_vehicle, target_vehicle = setup_parking_scenario(manager.world, spawner)

            if not ego_vehicle or not target_vehicle:
                print("Error, scenario creation failed")
                return

            print("Initializing Perception and Sensor Manager...")
            perception_system = RctaPerception()
            sensor_manager = SensorManager(manager.world, manager.actor_list)

            #initialize perception and cameras
            rear_cam, left_cam, right_cam = sensor_manager.setup_rcta_cameras(ego_vehicle)
            if not (rear_cam and left_cam and right_cam):
                print("ERRORE: Fallimento spawn telecamere. Uscita.")
                return

            #initialize callback
            rear_cam.listen(perception_system.rear_cam_callback)
            left_cam.listen(perception_system.left_cam_callback)
            right_cam.listen(perception_system.right_cam_callback)
            print("Camera callback setted.")

            #setting spectator's view
            spectator = manager.world.get_spectator()
            spectator_transform = carla.Transform(
                config.EGO_SPAWN_TRANSFORM.location + carla.Location(x=20, y=10, z=10.0),
                carla.Rotation(pitch=-45, yaw=-150)
            )
            spectator.set_transform(spectator_transform)

            while True:
                manager.world.tick()
                # --- Logica di Test Milestone ---
                frames = perception_system.current_frames
                detections = perception_system.detected_objects

                if frames['rear'] is not None:
                    display_rear = frames['rear'].copy()
                    draw_detections(display_rear, detections['rear'])
                    cv2.imshow('Rear Camera', display_rear)

                if frames['left'] is not None:
                    display_left = frames['left'].copy()
                    draw_detections(display_left, detections['left'])
                    cv2.imshow('Left RCTA Camera', display_left)

                if frames['right'] is not None:
                    display_right = frames['right'].copy()
                    draw_detections(display_right, detections['right'])
                    cv2.imshow('Right RCTA Camera', display_right)

                # Premi 'q' per chiudere le finestre OpenCV e uscire
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\nScript interrotto dall'utente.")
    except Exception as e:(
        print(f"\nSi è verificato un errore: {e}"))

    finally:
        cv2.destroyAllWindows()
        print("all OpenCV windows closed")

if __name__ == '__main__':
    main()
