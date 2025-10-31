Larghezza tipica veicolo: ~1.8m
Distanza camera: 2m dal retro
FOV 90° copre: ~4m a 2m di distanza
FOV 120° copre: ~6.9m (eccessivo, distorsione elevata)
```

**Pro FOV 90°:**
- ✅ YOLO accuracy migliore (meno distorsione barrel)
- ✅ Oggetti ai bordi ancora riconoscibili
- ✅ Sufficiente per detection centrale

### **3. Perché 110° per camere laterali depth?**

**Requisiti RCTA:**
- Deve rilevare veicoli in avvicinamento **laterale** a 5-15m
- Angolo di approccio tipico: 70-90° rispetto all'asse del veicolo
- Necessita copertura **ampia** del blind spot

**Pro FOV 110°:**
- ✅ Early warning efficace (rileva veicoli prima)
- ✅ Overlap con camera centrale (~20°)
- ✅ Depth precision accettabile
- ✅ Copertura completa zone critiche

## **Schema di Copertura**
```
Vista dall'alto:

        [Camera Posteriore 90°]
              |      |
              |  EGO |
              |      |
    [L 110°]  |______| [R 110°]
       /                    \
      /                      \
     /    BLIND SPOT          \
    /     COVERAGE             \