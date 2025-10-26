import carla
import random
import config
from config import EGO_VEHICLE_MODEL


def setup_static_scenario(world, spawner):
    """
    Creates a static parking lot scenario for RCTA test.
    Spawns ego_vehicle in a parking lot and adds several vehicles (static) around it.

    :param world: carla's world object
    :param spawner: Object to spawn actors
    :return: The spawned actor ego_vehicle, or None if it fails
    """
    print("Creating static parking lot scenario")

    try:
        ego_vehicle = spawner.spawn_vehicle(
            model= EGO_VEHICLE_MODEL,
            spawn_point=config.EGO_SPAWN_TRANSFORM,
            autopilot=False
        )
    except AttributeError as e:
        print(f"error: {e}")
        return None

    if not ego_vehicle:
        print(f"Failure to spawn ego_vehicle for the scenario")
        return None

    print(f"Vehicle spawned in position: {config.EGO_SPAWN_TRANSFORM.location}")

    #spawning vehicles around
    spawned_blockers = 0
    for transform in config.BLOCKING_VEHICLE_TRANSFORMS:
        model  = random.choice(config.BLOCKING_VEHICLE_MODELS)
        blocker = spawner.spawn_vehicle(
            model=model,
            spawn_point=transform,
            autopilot=False
        )
        if blocker:
            spawned_blockers += 1

    print(f"Spawned {spawned_blockers} blocker vehicles")
    return ego_vehicle
