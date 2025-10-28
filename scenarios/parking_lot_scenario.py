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


def setup_parking_scenario(world, spawner):
    """
    Creates a static parking lot scenario for RCTA test.
    Spawns ego_vehicle in a parking lot and adds several vehicles (static) around it.
    Spawns also a target vehicle that moves.

    :param world: carla's world object
    :param spawner: Object to spawn actors
    :return: Tuple(ego_vehicle, target_vehicle), or (None,None) if it fails
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
        return None, None

    if not ego_vehicle:
        print(f"Failure to spawn ego_vehicle for the scenario")
        return None, None

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

    #spawning target vehicle
    target_vehicle = spawner.spawn_vehicle(
        model=config.TARGET_VEHICLE_MODEL,
        spawn_point=config.TARGET_SPAWN_TRANSFORM,
        autopilot=False
    )
    if not target_vehicle:
        print("ERROR: target_vehicle not spawned.")
        return ego_vehicle, None

    target_vehicle.set_target_velocity(config.TARGET_VELOCITY)
    print(f"Vehicle spawned in position: {config.TARGET_SPAWN_TRANSFORM.location}")

    return ego_vehicle, target_vehicle
