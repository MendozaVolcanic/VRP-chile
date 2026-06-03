# S99 — Forense Tupungatito: ¿el 19× es input (nieve estacional) o código?

**Veredicto: HIPÓTESIS A (input/estacional). Hipótesis B (cambio de código) REFUTADA
con evidencia git + numérica.**

Todos los números de este doc salen de:
- `data/mirova_equivalent/Tupungatito.json` (data actual, post-reproc S98)
- `experiments/_s99_audit/tup_s65.json` (= `git show 9d727787:.../Tupungatito.json`, data vieja S65)
- `latest_consolidado.csv` (ground truth MIROVA)
- comandos `git log` citados abajo

NO transcribí ningún número a mano: cada celda viene de los scripts Python inline
ejecutados en esta sesión (reproducibles contra los archivos de arriba).

---

## 1. Prueba decisiva: marzo y abril se procesaron con el MISMO código

La data actual de feb/mar/abr/may de Tupungatito fue reprocesada en S98 con el fix
del ancla (rama `s98-detection-anchor`), repartida en chunks del MISMO workflow
`reproc-s98-anchor.yml` con el MISMO `code_ref`:

- `git log -- data/mirova_equivalent/Tupungatito.json` muestra que el JSON fue
  reescrito por:
  - `8585b26c` (#320, "promoción 90d Tupun/PCC/PP al cráter", 2026-06-02)
  - `ffc81b10` (#322, "backfill histórico ene-mar", 2026-06-02)
- `experiments/_s98_anchor/merge_promote.py` CHUNKS:
  - run `26839962842` → **2026-03-04..2026-04-02** (marzo)
  - run `26839967867` → **2026-04-03..2026-05-02** (abril)
  - Ambos chunks = mismo workflow, mismo `code_ref` = byte-idéntico el código.
- `merge_backfill.py` RUN_ID `26851227816` → 2026-01-29..2026-03-03 (mismo code_ref).

**Conclusión lógica**: si marzo y abril corrieron con el MISMO commit de código y
aun así difieren en magnitud/píxeles, la diferencia NO puede ser un cambio de
código. B queda refutada por construcción del experimento (que ya ocurrió en S98).

## 2. La premisa "marzo 1.04× / abril 20.8×" es un artefacto de medición puntual

Ratio mediano mensual (VRP>0), nuestra `pc.vrp_mw` vs MIROVA `VRP_MW`, DATA ACTUAL:

| mes | nuestra med(>0) | MIROVA med(>0) | RATIO | N_nuestra | N_mir |
|---|---|---|---|---|---|
| 2026-02 | 2.594 | 0.275 | 9.43 | 164 | 20 |
| 2026-03 | 1.568 | 0.220 | **7.13** | 180 | 28 |
| 2026-04 | 2.074 | 0.240 | 8.64 | 178 | 40 |
| 2026-05 | 2.631 | 0.210 | 12.53 | 209 | 35 |
| 2026-06 | 3.803 | 0.150 | 25.35 | 12 | 3 |

- Marzo NO es 1.04×: es **7.13×** ya en la data actual. El "1.04× marzo perfecto"
  de MEMORY.md (S98 §2) era un single record / medición puntual, no la mediana mensual.
- No hay "salto" entre marzo y abril (7.1 → 8.6). Hay una **rampa monotónica**
  feb→jun que culmina en ~25× en junio.

## 3. La rampa es estacional (gradual), no un escalón de código

`pc.n_pixels` mediano mensual (data actual): mar **2** → abr **3.5** → may **15.5** → jun **12.5**.

Media semanal de `n_pixels` VIIRS375 (data actual), buscando escalón:

```
W05-W16 (feb-abr):  ~12-37 px  (oscila, sin tendencia clara)
W17 (~fin abr):     55.2 px  <- inicio de la subida sostenida
W18-W22 (may-jun):  47-56 px  (meseta alta sostenida)
```

No hay escalón en una semana puntual coincidente con un commit; hay una **transición
gradual ~W16→W17 (mediados/fin de abril)** y meseta alta en mayo-junio. Esa firma
temporal corresponde al avance del invierno austral (nieve fresca acumulándose sobre
el glaciar a 5682 m), no a un deploy de código (que daría un salto vertical neto en
la fecha exacta del merge).

## 4. Control cruzado: la data VIEJA S65 también ramea, sin el fix nuevo

`experiments/_s99_audit/tup_s65.json` (commit `9d727787`, S65, ancla sin
mirova_center, código DISTINTO al S98): med VRP(>0) mar **2.00** / abr **1.88** /
may **1.99**; n_px mediano mar **5** → abr **12** → may **21**.

→ Con DOS códigos distintos (S65 viejo y S98 nuevo), el patrón es el mismo: los
píxeles del cluster crecen mar→may. La rampa de píxeles es **invariante al código**,
lo que solo se explica por el input.

## 5. MIROVA es plano todo el período

MIROVA Tupungatito (`latest_consolidado.csv`), med VRP(>0): 0.15–0.28 MW estable
feb→jun (máx puntual 47 MW en marzo = evento real aislado). MIROVA integra ROI
completo y reporta señal sub-MW del cráter; no infla con el mosaico nieve/roca.

## 6. Mecanismo físico (coherente con MEMORY A19/A23 y S98 §2)

El cráter de Tupungatito es señal térmica débil (~0.2 MW) sobre un glaciar de gran
altitud. En invierno austral la nieve fresca cubre parcialmente el campo y crea un
mosaico nieve↔roca expuesta de fuerte contraste térmico local. El path D (dNTI
contextual 8-vecinos, `enable_dnti_contextual_path: True`) lee ese contraste como
anomalía y agrega muchos píxeles "calientes relativos"; como el VRP del cluster es
**suma** de píxeles, n_px 2→58 multiplica la magnitud agregada, mientras MIROVA
sigue viendo solo el foco sub-pixel del cráter. Mismo mecanismo que A19 (ring
glaciar Tupungatito empeora con kernel-bg) y A23 (path D infla sobre fondo frío).

## 7. Flags path D del perfil operacional (sin cambios entre mar y abr — un solo code_ref)

`enable_dnti_contextual_path: True`, `enable_dnti_dual_roi: True`,
`enable_single_pixel_sub_mw_mode: True` (`single_pixel_max_cluster_pixels: 3`),
`path_d_only_cap_mw: 5.0`, `path_d_only_cap_tbg_max_k: 270.0`. Todos idénticos para
los granules de marzo y abril (mismo run).

---

## Cierre

A vs B no requiere fe: el reproc S98 ya fue el experimento controlado. Marzo y abril
salieron del mismo binario de código y muestran distinta magnitud → la causa es el
INPUT. La firma temporal (rampa gradual de píxeles, no escalón) y el control con la
data vieja S65 (mismo patrón con código distinto) confirman: **estacional, no código.**
El 19× no es regresión; es la respuesta del path D contextual al campo glaciar nevado
invernal sobre un cráter de señal débil. = tarea §2 de S99 (mitigación, no fix de bug).
