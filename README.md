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

### Fase 3: Implementazione RCTA (Solo Radar)
Costruiamo la logica RCTA base usando solo il radar. È più semplice e ci dà una base funzionante.

Step 5: Implementazione Percezione (Radar)
- Sviluppa carla_bridge/sensor_manager.py per creare e attaccare un sensore radar (con i parametri da config.py).
- Sviluppa rcta_system/perception.py. In questa fase, conterrà solo la funzione di callback del radar.
- La callback deve elaborare i dati grezzi del radar per identificare i rilevamenti rilevanti (oggetti in movimento, 
con la loro distanza e velocità).
- Test Milestone: main.py deve spawnare il radar e stampare a console i dati rilevati (es. "Oggetto rilevato a X metri,
velocità Y m/s") solo quando l'auto "target" passa.

Step 6: Implementazione Logica Decisionale e HMI (MQTT)
- Sviluppa rcta_system/decision_making.py. Questa classe riceve i dati dal modulo di percezione.

Implementa la logica:

- Controlla se l'ego_vehicle è in retromarcia (dovrai passare l'oggetto ego_vehicle o il suo stato).
- Se sì, calcola il rischio (es. TTC o distanza) in base ai dati del radar.
- Restituisce uno stato: SAFE, WARN_LEFT, WARN_RIGHT.
- Sviluppa hmi/mqtt_publisher.py per inviare questo stato a un topic MQTT.
- Sviluppa hmi/hmi_display.py per ricevere e stampare l'avviso.

**Test Milestone**: Avviando hmi_display.py, main.py e muovendo l'auto in retromarcia, dovresti vedere gli avvisi apparire 
nel terminale HMI solo quando l'auto "target" attraversa.

### Fase 4: Implementazione Sensor Fusion (Aggiunta Camera)
Ora rendiamo il sistema più intelligente aggiungendo la visione.

Step 7: Implementazione Object Detection (Camera)
- Scarica un modello pre-addestrato (es. yolov5s.pt) e salvalo in models/.
- Espandi sensor_manager.py per spawnare anche le due telecamere RGB posteriori.
- Sviluppa rcta_system/object_detector.py. Questa classe deve:
- Caricare il modello YOLO (usando torch.hub.load).
- Fornire un metodo detect(image) che restituisca i bounding box e le classi.
- Espandi rcta_system/perception.py per avere la callback della telecamera.

**Test Milestone**: Usa cv2.imshow per mostrare il feed della telecamera posteriore con i bounding box disegnati sopra. Verifica che l'auto "target" venga riconosciuta.

Step 8: Implementazione Logica di Fusione
Questo è lo step più complesso, tutto dentro rcta_system/perception.py.

- Dovrai implementare la logica di Mid-Level Fusion:
- Proietta i punti 3D del radar (che hanno distance e velocity) sul piano 2D dell'immagine della telecamera.
- Controlla quali punti radar cadono all'interno dei bounding box rilevati da YOLO.
- Crea una nuova lista di "Oggetti Fusi", che contenga: (Classe: 'vehicle', Distanza: 15m, Velocità: 5m/s).
- Modifica il modulo di percezione affinché fornisca questa lista di "Oggetti Fusi" al modulo decisionale.

### Fase 5: Test Finale e Documentazione
Step 9: Aggiornamento Logica Decisionale e Test Completo

- Aggiorna rcta_system/decision_making.py per usare gli "Oggetti Fusi".
- Ora la logica può essere più intelligente (es. "ignora gli oggetti classificati come 'static', dai priorità a 'pedestrian'").

Esegui test completi:

- Funziona con veicoli?
- Funziona con pedoni? (Modifica lo scenario).
- Ignora gli oggetti statici?
- Si attiva solo in retromarcia?
- Step 10: Scrittura Report e Pulizia Codice
- Scrivi il report finale del progetto, documentando l'architettura, la logica di fusione e i risultati dei test.
- Rivedi il codice, aggiungi commenti e assicurati che README.md sia aggiornato.

