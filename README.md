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


## step 

### Fase 2: Creazione Scenario di Test
Ora creiamo l'ambiente specifico per l'RCTA.

Step 3: Sviluppo Scenario Statico
Sviluppa la funzione/classe in scenarios/parking_lot_scenario.py.

Questa funzione deve:
- Trovare una mappa adatta (es. Town05 o Town10HD). 
- Trovare una posizione di parcheggio. 
- Spawnare l'ego_vehicle in quel parcheggio. 
- Spawnare 2-3 veicoli statici (senza autopilot) parcheggiati ai lati dell'ego-vehicle per ostruire la visuale.

**Test Milestone**: main.py deve caricare lo scenario e tu devi poter vedere l'auto parcheggiata correttamente.

Step 4: Sviluppo Scenario Dinamico
- Espandi scenarios/parking_lot_scenario.py per spawnare un attore "target".
- Spawna un target_vehicle (o un pedone) in un punto nascosto.
- Imposta una traiettoria per questo attore (usando set_autopilot() o set_target_velocity()) che lo faccia passare dietro l'auto parcheggiata.

**Test Milestone**: Eseguendo main.py, dovresti vedere la tua ego_vehicle ferma e l'auto "target" che le attraversa la strada sul retro.

### Fase 3: Implementazione RCTA (Vision-Only)

Step 5: Setup Telecamere e Object Detection
- Modifica config.py per aggiungere i parametri di 3 telecamere:
REAR_CAMERA_TRANSFORM (centrale, guarda indietro).
RCTA_LEFT_CAMERA_TRANSFORM (angolo posteriore sinistro, guarda a sinistra).
RCTA_RIGHT_CAMERA_TRANSFORM (angolo posteriore destro, guarda a destra).

- Sviluppa carla_bridge/sensor_manager.py con una nuova funzione setup_rcta_cameras() per creare e attaccare queste 
3 telecamere all'ego_vehicle.
- Sviluppa rcta_system/object_detector.py. Questa classe deve:
- Caricare un modello pre-addestrato (es. YOLOv5s) da models/.
- Fornire un metodo detect(image) che riceve un'immagine CARLA (convertita in numpy) e restituisce una lista 
di rilevamenti (es. [{'class': 'car', 'confidence': 0.9, 'bbox': [x1, y1, x2, y2]}]).
- Sviluppa rcta_system/perception.py:
Crea un'istanza di ObjectDetector.
Crea 3 funzioni di callback separate (una per ogni telecamera: rear_cam_callback, left_cam_callback, right_cam_callback).
Ogni callback passa l'immagine ricevuta al metodo detect() dell'ObjectDetector.
Archivia i risultati in una variabile (es. self.detected_objects).

**Test Milestone:** Aggiorna main.py per mostrare i 3 feed video usando cv2.imshow(). I video devono mostrare 
i bounding box disegnati sugli oggetti rilevati (il camion target).


Step 6: Implementazione Logica Decisionale e HMI (MQTT)

- Sviluppa rcta_system/decision_making.py. Questa classe:
Riceve la lista di detected_objects dal modulo di percezione.
Riceve lo stato del veicolo (per sapere se è in retromarcia).
Logica Base: Se (il veicolo è in retromarcia) E (la lista detected_objects non è vuota), restituisce la 
lista degli oggetti pericolosi.

- Sviluppa hmi/mqtt_publisher.py per connettersi al broker.
- Aggiorna main.py: nel ciclo principale, chiama la logica decisionale. Se ci sono oggetti pericolosi, 
usa mqtt_publisher per inviare un messaggio al topic rcta/alerts. Il messaggio deve contenere le classi 
degli oggetti rilevati (es. {"alert": true, "objects": ["car", "person"]}).

Sviluppa hmi/hmi_display.py (script separato) per iscriversi al topic rcta/alerts e stampare i messaggi ricevuti.

**Test Milestone:** Avvia hmi_display.py e main.py. Metti l'auto in retromarcia (puoi forzarlo nel codice all'inizio). 
Quando il camion "target" passa, il terminale HMI deve stampare un messaggio tipo "Rilevato: ['car']".

### Fase 4: Test Finale e Documentazione
Step 7: Test Avanzato e Logica di Rischio

- Migliora la logica in decision_making.py. Invece di un semplice "se rileva, avvisa", rendila più intelligente:
- Direzionalità: Usa l'ID della telecamera che ha fatto il rilevamento per inviare un avviso specifico 
(es. "PERICOLO A SINISTRA" se rilevato dalla left_cam_callback).
- Filtro Classi: Ignora oggetti non pericolosi (es. 'panchina', 'palo') e dai priorità alta a 'person', 'bicycle'.
- Modifica lo scenario in parking_lot_scenario.py per spawnare un pedone invece di un camion e verifica che il 
sistema lo rilevi correttamente.
- Testa i casi limite (es. l'oggetto è lontano? L'oggetto è fermo?).

Step 8: Scrittura Report e Pulizia Codice
- Scrivi il report finale documentando la nuova architettura "vision-only", le posizioni delle telecamere, 
il modello di object detection usato e i risultati dei test.
- Rivedi il codice, aggiungi commenti e assicurati che README.md sia aggiornato.