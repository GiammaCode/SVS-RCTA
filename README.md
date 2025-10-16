# Smart Vehicular Systems Project: Rear Cross Traffic Alert (RCTA)

This project consists of the implementation of an advanced **Rear Cross Traffic Alert (RCTA)** system using the 
**CARLA 0.9.15** simulator. 

## Objectives and Deliverables

Develop a Rear Cross Traffic Alert (RCTA) system to detect vehicles and pedestrians approaching 
from both sides while reversing, issuing visual and audio alerts.

The project deliverables include:
* **CARLA Code**: The complete system implementation.
* **Report**: A document describing the architecture, design choices, and results.
* **Live Demo**: A working demonstration of the system in the simulator.
* **Warning System**: Implemented via **MQTT** messages.


### Sensor Selection and Fusion
To ensure robustness and reliability, the system does not rely on a single sensor but implements a **Sensor Fusion** strategy.

* **Sensors Used**:
    * **2 Rear Radars**: For accurate measurement of object **distance and velocity**, reliable in all weather and 
  light conditions.
    * **2 Rear RGB Cameras**: For object **recognition and classification** (e.g., distinguishing a vehicle from a 
  pedestrian), leveraging Deep Learning models.

* **Fusion Technique**:
    * A **Mid-Level Fusion** approach has been chosen. A Deep Learning model separately processes features
  extracted from the camera images and the raw radar data. These features are then combined to allow the system to 
  make more informed and accurate decisions based on enriched data.

