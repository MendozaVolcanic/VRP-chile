# Auditoría S138, eje 4: qué cuestan en VIIRS 375 y 750 la compuerta de temperatura (D22) y el fondo del anillo

> Auditor del eje 4. Read-only sobre `main` (`6b1dd91ef`). Todo número de este informe lo produjo un
> script de esta sesión en `experiments/_s138_audit/eje4/` (salidas en `out/`), o es una lectura
> archivo:línea del código de hoy. Ventanas y denominadores van con cada tabla (A90). La unidad del
> costo es la NOCHE por volcán y sensor (A94), no el record.

## Resumen (menos de 400 palabras)

**Recomendación: el A/B Tier A de D22 y del fondo debe incluir VIIRS 750 y 375 desde el inicio;
MODIS aporta sólo a D21 (la banda 22 no existe en VIIRS) y hoy no puede evaluarse sobre el
dashboard.** Todo medido sobre `data/mirova_equivalent/`, ventana 2026-01-11 a 2026-09-07:

1. **VIIRS 750 es donde el mecanismo cuesta alertas hoy.** De 246 noches con ALERTA nocturna de
   MIROVA, **33 (13,4 %, IC95 9,3 a 17,9 %) se pierden con un cúmulo del cráter en 0,0 MW como
   única traza nuestra**: Tupungatito 8 de 14, Isluga 11 de 40, Planchón-Peteroa 4 de 9, Láscar
   8 de 136. En 31 de 33 el píxel del cráter está 0,2 a 6 K **más frío** que la mediana del anillo:
   la compuerta lo mata en el primer paso, el segundo paso (sin compuerta) lo rescata y el anillo le
   deja 0,0 MW. El operador no ve nada.
2. **En VIIRS 375 la compuerta ya está neutralizada en detección** por ese segundo paso: 9 a 26 %
   de los records visibles de cada volcán vienen sólo de él. Un brazo "sin compuerta" en VIIRS375
   mostrará poco en detección y todo en magnitud (predicción, SOSPECHA). Costo actual: 6 de 896
   noches (0,7 %), todas por la pata de magnitud de `keep_peak` (D19), no por la compuerta.
3. **D22, D19/D2 y el fondo están acoplados**: condicionar el segundo paso sin quitar la compuerta
   costaría en VIIRS750 entre 10 y 41 de 246 noches; en VIIRS375 entre 0 y 14 de 896 (la cota 0
   coincide con el brazo C de S135). El A/B debe cruzar los tres factores.
4. **MODIS no sirve hoy para evaluar**: 76 de 77 noches ALERTA MODIS son de Láscar y en 59 el
   cúmulo está en el cráter pero `distance_class = far` (A46/A81). Recall dashboard MODIS: 10 de 77.
5. Poder: los IC95 de VIIRS375 y VIIRS750 no se solapan, ni Tupungatito e Isluga con Láscar.
   Isluga es focal: el fenómeno es cráter frío contra anillo tibio, no "nevado".

El pipeline **no persiste** "pasó los Tests 2 y 3 y cayó sólo por la compuerta"
(`detection_context.py:536` cuenta post-compuerta). Queda escrito, sin disparar, el probe por
etapa para VIIRS 375 y 750 (`probe_compuerta_viirs.py` + yml).

Ruta: `docs/audit_s138/EJE_4_d21_d22_viirs.md`; scripts y tablas en `experiments/_s138_audit/eje4/`.

---

## 1. Dónde vive la compuerta y el fondo del anillo (archivo:línea, código de hoy)

### 1.1 La compuerta `bt > t_bg + NTI_BT_SANITY_K`

Valor: `pipeline/profiles/mirova_equivalent.yaml:44` (`nti_bt_sanity_k: 3.0`), leído en
`pipeline/profile.py:88`. Efectivo en producción: `NTI_BT_SANITY_K = 3.0` (verificado importando
`pipeline.process_viirs` y `pipeline.process_viirs_mod` con `VRP_PROFILE=mirova_equivalent`).

| dónde | VIIRS 375 (`process_viirs.py`) | VIIRS 750 (`process_viirs_mod.py`) | MODIS (`process_modis.py`) |
|---|---|---|---|
| Tests 2 y 3, primer paso (`first_pass_tests_2_and_3`, la compuerta está en `detection_context.py:532`) | llamada `:1237-1240` (`bt_sanity_k=NTI_BT_SANITY_K`) | `:829-832` | `:866-869` |
| Path D contextual (`contextual_dnti_hot_mask`, compuerta en `detection_context.py:269`; el dual-ROI `:372-376` la hereda) | `:1038` y `:1046` | `:677` y `:685` | `:693` y `:701` |
| Path B, NTI absoluto | `:976` | `:624` | `:665` |
| Path C, NTI relativo (flag OFF) | `:998` | `:643` | (no existe) |
| Path ETI legacy (post second pass del ETI) | `:1178` | `:780` | `:821` |
| **Segundo paso principal** (`second_pass_adjacent`, `detection_context.py:803-960`) | `:1284` a `:1317`, **sin compuerta** | `:876` a `:909`, **sin compuerta** | `:919` a `:951`, **sin compuerta** |
| Test 1 integrado (`test1_integrated.py`) | sin compuerta (no hay `bt_sanity` en el módulo) | ídem | ídem |

Los tres sensores comparten la misma función y el mismo margen: la compuerta de D22 es una sola
línea (`detection_context.py:532`) llamada desde tres sitios, no tres implementaciones.

Lo que decide todo lo que sigue: **el segundo paso corre con el conjunto activo vacío**
(`ENABLE_SECOND_PASS_CONDITIONED = False`, `experiments/_s138_audit/eje1/profile_flags_efectivos.txt`;
guard en `detection_context.py:887`) y **no reaplica la compuerta** (`:939-948`). Con el
conjunto activo vacío, la media de 8 vecinos no excluye nada y el dNTI es el mismo del primer
paso; bajo la conectiva `min` el piso C1 gobierna (S136), así que un píxel que aparece en el
segundo paso y no en el primero cayó, salvo casos de borde, por la compuerta. Esto es D19/D2
(AUDIT_S134 §D), y es la puerta trasera que permite medir D22 sobre `data/` sin probe.

### 1.2 El fondo del anillo (magnitud)

| path | VIIRS 375 | VIIRS 750 | MODIS |
|---|---|---|---|
| cúmulo contextual: `L_bg` de la mediana del anillo 5-25 km, `ΔL = max(L_hot - L_bg, 0)` | `process_viirs.py:1409` y `:1416` (kernel 3x3 sólo si `local_kernel_bg` per-vol, `:1398`) | `:985` | `:1056` |
| cúmulo Test 1: `effective_L_bg` (cascada anillo intermedio > global > local, `test1_integrated.py:129-153`), `ΔL` recortado a 0 | `:1828`, `:1865`, `:1889` | `:1202`, `:1217` | `:1360`, `:1375` |
| corona Eq.6 (fondo local) | `apply_corona_magnitude_v375`, flag `ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 = False` | `ENABLE_LOCAL_CLUSTER_MAGNITUDE = False` | ídem |

`local_kernel_bg: true` en `volcanoes.yaml` para Lastarria, Planchón-Peteroa, Villarrica, PCC y
Chaitén (5 de 11; leído con `yaml.safe_load`, no del docstring).

### 1.3 Qué se persiste y qué no

Persistido por record (verificado sobre `data/mirova_equivalent/*.json`, presente en el 100 % de
los records de los 11 Tier A): `t_bg_k`, `t_max_k`, `diag_n_first_pass_pixels`,
`diag_n_second_pass_recapture`, `final_hotspot_source`, `triggered_test1`, `primary_cluster`
(`n_pixels`, `vrp_mw`, `centroid_dist_km`, `single_pixel_mode`), `anomaly_pixels` (con `bt_k`).

**No persistido**: el conteo de píxeles que pasan Tests 2 ∧ 3 ANTES de la compuerta.
`detection_context.py:536` (`"n_first_pass_pixels": int(np.sum(hot))`) cuenta después del AND
con `(bt > t_bg + bt_sanity_k)`. Tampoco se guarda la BT del píxel que cayó. Por eso el costo
directo sólo se mide con probe por etapa (§4); sobre `data/` se mide por la vía indirecta de §1.1.

Dos trampas del instrumento encontradas al medir (vale para cualquier auditoría futura):

- `anomaly_pixels` guarda sólo píxeles con VRP > 0, y cuando el Test 1 dispara, el bloque S94
  (`process_viirs.py:1898`, ídem `process_viirs_mod.py:1227`, `process_modis.py:1385`) los
  **reemplaza por el footprint del Test 1** aunque el ancla honesta después rotule la fuente como
  `ctx_cluster`. Un "píxel pico" leído de ahí no es el pico del hot mask contextual en esos records.
  Control: sin excluir `triggered_test1`, 489 records con `fp > 0` mostraban pico bajo el margen
  (imposible por construcción); excluyéndolos, 8 de 9.497.
- `t_max_k` es el máximo de TODA la ROI (hasta 25 km; `diag_t_max_dist_km` llega a 26,7 km en el
  record leído), no del cráter. La métrica literal "t_max_k < t_bg_k + 3" no puede ver el fenómeno
  (da 0 en 21 de 33 celdas volcán x sensor y en las 12 restantes cuenta escenas enteras bajo el
  margen, 1 a 33 records, no el cráter).

## 2. Tablas

Scripts: `01_pc0_noches.py` (a), `02_compuerta_margen.py` (b), `03_solo2p_sin_test1.py` (cota
inferior). Salidas completas: `experiments/_s138_audit/eje4/out/01_salida.txt`, `02_salida.txt`,
`03_salida.txt` y CSV `01a_pc0_records.csv`, `01b_pc0_noches.csv`, `01c_pc0_mecanismos.csv`,
`02_compuerta_margen.csv`.

Convenciones verificadas en esta sesión: sensor con `Counter(r['sensor'])` sobre Villarrica
(`VIIRS_NOAA20` 892, `VIIRS_NOAA20_750` 888, ..., `MODIS_AQUA` 661: sin sufijo = I-band); nombres
del CSV con `sorted(set(Volcan))` (`Nevados de Chillan`, `PlanchonPeteroa`, `Puyehue-Cordon
Caulle`); loader canónico `pipeline.mirova_csv_loader.load_mirova_alertas` (CONS ∪ OCR, dedup);
noche = fecha UTC de la pasada (`scripts/auto_audit_weekly.py`, clave `dt[:10]`); pasadas diurnas
excluidas con el mismo `_reject_daytime` de `store.py` (110 de 1.952 pasadas-ALERTA); visible en
dashboard = `pc.vrp_mw > 0`, `distance_class` summit o ausente, centroide dentro del inner
(`frontend/index.html:1043-1064`, `mirovaEqVrp`; el núcleo F5' nunca borra una detección, `:1184`).

Controles: positivo, Láscar VIIRS375 2026-09-07 (ALERTA 0,16 MW, record nuestro visible), el
script lo cuenta como cubierta. Negativo, clave `('Lascar','VIIRS375','2024-12-31')` no existe y
no entra en ningún conteo. Diagnósticos `fp`/`sp` ausentes: 0 records (SIN DATO = 0).

### 2.1 (a) Records con cúmulo y VRP 0,0 MW, por volcán y sensor

Ventana: toda la serie persistida, 2025-02-15 a 2026-09-13 (PP hasta 2026-09-12). `n_pc` =
records con `primary_cluster.n_pixels > 0`; `pc0` = de esos, `vrp_mw == 0`. IC95 bootstrap de la
proporción (5.000 remuestreos). `pico<=t_bg` = el píxel persistido más caliente no supera la
mediana del anillo (mecanismo del recorte a 0); `sin_pix` = `anomaly_pixels` vacío (1 píxel de
`keep_peak` con VRP 0, que `build_anomaly_pixels` no guarda).

| volcán | sensor | n_rec | n_pc | pc0 | frac | IC95 | pico<=t_bg | sin_pix |
|---|---|---|---|---|---|---|---|---|
| Lascar | VIIRS375 | 1868 | 1696 | 249 | 0,147 | 0,130 a 0,164 | 8 | 239 |
| Lascar | VIIRS750 | 1852 | 1241 | 268 | 0,216 | 0,193 a 0,238 | 176 | 88 |
| Lascar | MODIS | 949 | 947 | 2 | 0,002 | 0,000 a 0,005 | 0 | 2 |
| Lastarria | VIIRS375 | 1902 | 1680 | 398 | 0,237 | 0,217 a 0,257 | 0 | 392 |
| Lastarria | VIIRS750 | 1870 | 729 | 201 | 0,276 | 0,244 a 0,310 | 145 | 49 |
| Lastarria | MODIS | 955 | 953 | 1 | 0,001 | 0,000 a 0,003 | 0 | 1 |
| Isluga | VIIRS375 | 1819 | 1663 | 35 | 0,021 | 0,014 a 0,028 | 35 | 0 |
| Isluga | VIIRS750 | 1812 | 1020 | 424 | 0,416 | 0,386 a 0,446 | 420 | 2 |
| Isluga | MODIS | 919 | 917 | 1 | 0,001 | 0,000 a 0,003 | 0 | 1 |
| Tupungatito | VIIRS375 | 2106 | 1648 | 50 | 0,030 | 0,022 a 0,039 | 49 | 0 |
| Tupungatito | VIIRS750 | 2090 | 1067 | 617 | 0,578 | 0,549 a 0,607 | 614 | 0 |
| Tupungatito | MODIS | 1067 | 1065 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| PlanchonPeteroa | VIIRS375 | 2110 | 1667 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| PlanchonPeteroa | VIIRS750 | 2091 | 691 | 249 | 0,360 | 0,324 a 0,397 | 248 | 1 |
| PlanchonPeteroa | MODIS | 1102 | 1096 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| NevadosDeChillan | VIIRS375 | 2215 | 1688 | 649 | 0,385 | 0,363 a 0,408 | 55 | 594 |
| NevadosDeChillan | VIIRS750 | 2186 | 525 | 260 | 0,495 | 0,453 a 0,539 | 77 | 182 |
| NevadosDeChillan | MODIS | 1110 | 1106 | 15 | 0,014 | 0,007 a 0,021 | 2 | 13 |
| Llaima | VIIRS375 | 2287 | 1755 | 53 | 0,030 | 0,022 a 0,039 | 53 | 0 |
| Llaima | VIIRS750 | 2278 | 531 | 124 | 0,234 | 0,200 a 0,269 | 121 | 2 |
| Llaima | MODIS | 1135 | 1132 | 2 | 0,002 | 0,000 a 0,004 | 1 | 1 |
| Villarrica | VIIRS375 | 2625 | 2070 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| Villarrica | VIIRS750 | 2618 | 799 | 197 | 0,247 | 0,216 a 0,277 | 196 | 1 |
| Villarrica | MODIS | 1302 | 1300 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| Copahue | VIIRS375 | 2226 | 1791 | 46 | 0,026 | 0,018 a 0,034 | 45 | 0 |
| Copahue | VIIRS750 | 2210 | 425 | 74 | 0,174 | 0,139 a 0,212 | 72 | 1 |
| Copahue | MODIS | 1131 | 1128 | 1 | 0,001 | 0,000 a 0,003 | 1 | 0 |
| PuyehueCordonCaulle | VIIRS375 | 2179 | 1792 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| PuyehueCordonCaulle | VIIRS750 | 2153 | 1536 | 196 | 0,128 | 0,111 a 0,144 | 176 | 1 |
| PuyehueCordonCaulle | MODIS | 1105 | 1096 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| Chaiten | VIIRS375 | 2392 | 1725 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |
| Chaiten | VIIRS750 | 2380 | 644 | 89 | 0,138 | 0,113 a 0,165 | 89 | 0 |
| Chaiten | MODIS | 1250 | 1248 | 0 | 0,000 | 0,000 a 0,000 | 0 | 0 |

Mecanismo de los pc0, agregado por sensor (clasificado con `final_hotspot_source`, `fp`, `sp`):

| sensor | total pc0 | 2do paso sin activos (`ctx_cluster`, fp = 0, sp > 0) | Test 1 `keep_peak` / anillo (`test1_roi`, `test1`) | otro |
|---|---|---|---|---|
| VIIRS375 | 1480 | 300 (20,3 %) | 1157 (78,2 %) | 23 |
| VIIRS750 | 2699 | 2354 (87,2 %) | 317 (11,7 %) | 28 |
| MODIS | 22 | 0 | 16 | 6 |

Lectura física. En VIIRS750 el cero es casi siempre el mismo objeto: un píxel (pc de 1 píxel en
el 60 a 90 % de los casos) que pasa los Tests 2 ∧ 3 en el segundo paso, está por debajo de la
mediana del anillo (614 de 617 en Tupungatito, 420 de 424 en Isluga, 248 de 249 en PP), y por
eso la compuerta lo eliminó en el primer paso y el anillo le deja ΔL ≤ 0. En VIIRS375 el cero es
otro objeto: el píxel de `keep_peak` del Test 1 (NdC 502, Lastarria 395, Láscar 219), sin píxel
persistido, con fuente `test1_roi` y distancia 0,0 km (D19 en su pata de magnitud, AUDIT_S134).
En Villarrica, PCC, Chaitén y PP VIIRS375 el pc0 es exactamente 0: son 4 de los 5 volcanes con
`local_kernel_bg: true`, donde el fondo local evita el recorte (Lastarria es el quinto y su cero
viene del Test 1, que no usa el kernel).

### 2.2 (a) Costo en noches contra MIROVA

Ventana de la referencia: 2026-01-11 a 2026-09-07 (fechas mín/máx del CSV vivo,
`data/mirova_reference/mirova_v1_snapshot/`). `alertas` = noches (fecha UTC) con al menos una
pasada-ALERTA nocturna de ese sensor; `cubiertas` = con al menos un record nuestro visible;
`perd_pc0` = perdidas con al menos un record pc0 y ninguno visible; `perd_sin_rec` = sin ningún
record nuestro ese día (cobertura, no detección); `perd_no_vis` = con records pero ninguno visible
ni pc0 (cúmulo `far` o fuera del inner). IC95 bootstrap de `perd_pc0 / alertas`.

| volcán | sensor | alertas | cubiertas | perdidas | perd_pc0 | perd_sin_rec | perd_no_vis | frac_pc0 | IC95 |
|---|---|---|---|---|---|---|---|---|---|
| Lascar | VIIRS375 | 176 | 166 | 10 | 1 | 9 | 0 | 0,006 | 0,000 a 0,017 |
| Lascar | VIIRS750 | 136 | 123 | 13 | 8 | 5 | 0 | 0,059 | 0,022 a 0,103 |
| Lascar | MODIS | 76 | 9 | 67 | 0 | 2 | 65 | 0,000 | 0,000 a 0,000 |
| Lastarria | VIIRS375 | 156 | 142 | 14 | 4 | 10 | 0 | 0,026 | 0,006 a 0,051 |
| Isluga | VIIRS375 | 160 | 159 | 1 | 0 | 1 | 0 | 0,000 | |
| Isluga | VIIRS750 | 40 | 29 | 11 | 11 | 0 | 0 | 0,275 | 0,150 a 0,425 |
| Tupungatito | VIIRS375 | 107 | 105 | 2 | 0 | 0 | 2 | 0,000 | |
| Tupungatito | VIIRS750 | 14 | 6 | 8 | 8 | 0 | 0 | 0,571 | 0,286 a 0,786 |
| PlanchonPeteroa | VIIRS375 | 93 | 88 | 5 | 0 | 5 | 0 | 0,000 | |
| PlanchonPeteroa | VIIRS750 | 9 | 5 | 4 | 4 | 0 | 0 | 0,444 | 0,111 a 0,778 |
| NevadosDeChillan | VIIRS375 | 10 | 6 | 4 | 1 | 0 | 3 | 0,100 | 0,000 a 0,300 |
| Llaima | VIIRS375 | 2 | 2 | 0 | 0 | 0 | 0 | 0,000 | |
| Villarrica | VIIRS375 | 29 | 29 | 0 | 0 | 0 | 0 | 0,000 | |
| Villarrica | VIIRS750 | 6 | 5 | 1 | 1 | 0 | 0 | 0,167 | 0,000 a 0,500 |
| Villarrica | MODIS | 1 | 1 | 0 | 0 | 0 | 0 | 0,000 | |
| Copahue | VIIRS375 | 4 | 4 | 0 | 0 | 0 | 0 | 0,000 | |
| Copahue | VIIRS750 | 1 | 1 | 0 | 0 | 0 | 0 | 0,000 | |
| PuyehueCordonCaulle | VIIRS375 | 120 | 104 | 16 | 0 | 13 | 3 | 0,000 | |
| PuyehueCordonCaulle | VIIRS750 | 38 | 30 | 8 | 1 | 7 | 0 | 0,026 | 0,000 a 0,079 |
| Chaiten | VIIRS375 | 39 | 35 | 4 | 0 | 4 | 0 | 0,000 | |
| Chaiten | VIIRS750 | 2 | 1 | 1 | 0 | 1 | 0 | 0,000 | |

Celdas sin ALERTA de MIROVA en la ventana (Lastarria/Isluga/Tupungatito/PP/NdC/Llaima/Copahue/PCC/
Chaitén en MODIS, Lastarria/NdC/Llaima en VIIRS750): SIN DATO, no OK.

Totales por sensor (misma ventana):

| sensor | alertas | cubiertas | perdidas | perd_pc0 (IC95) | perd_sin_rec | perd_no_vis | recall dashboard |
|---|---|---|---|---|---|---|---|
| VIIRS375 | 896 | 840 | 56 | **6 = 0,7 % (0,2 a 1,2 %)** | 42 | 8 | 93,8 % |
| VIIRS750 | 246 | 200 | 46 | **33 = 13,4 % (9,3 a 17,9 %)** | 13 | 0 | 81,3 % |
| MODIS | 77 | 10 | 67 | 0 | 2 | **65** | 13,0 % |

Mecanismo en las 33 noches V750 perdidas con pc0: segundo paso sin activos en 31, Test 1
`keep_peak` en 4 (dos noches con ambos), con activos del primer paso en 1. En las 6 de V375: Test 1
`keep_peak` en las 6 (Lastarria 4, Láscar 1, NdC 1).

Ejemplo reproducible (V750): Tupungatito, noche 2026-08-21 UTC, MIROVA VIIRS750 0,19 MW. Tres
pasadas nuestras (`VIIRS_SNPP_750` 05:30, `VIIRS_NOAA20_750` 05:48, `VIIRS_NOAA21_750` 06:30):
cúmulo de 1 píxel a 0,33 / 0,31 / 0,55 km del cráter, fuente `ctx_cluster`, `fp = 0`, `sp = 1`,
BT del píxel 250,39 / 252,70 / 252,32 K contra `t_bg_k` 256,38 / 256,55 / 257,20 K (el cráter 4 a
6 K más frío que el anillo), `pc.vrp_mw = 0.0`. Comando:
`PYTHONIOENCODING=utf-8 python experiments/_s138_audit/eje4/01_pc0_noches.py` (imprime esta
noche entre los ejemplos).

### 2.3 (b) Dependencia del segundo paso sin activos y margen del píxel pico

`n_vis` = records visibles en el dashboard (toda la serie); `solo2p` = visibles cuya única
detección es el segundo paso sin activos (`ctx_cluster`, fp = 0, sp > 0); `pico<3K` = de esos, con
píxel pico persistido bajo `t_bg + 3` (sólo medible cuando el Test 1 NO disparó, ver §1.3;
`sin_instr.` = el resto). Régimen: clasificación del orquestador, coincidente con
`experiments/_s136/medir_fenomeno_test1.py:26` y `_s135_ab_d1d2/evaluar_ab.py:91` donde ambas listan.

| volcán | régimen | sensor | n_vis | solo2p | frac | IC95 | pico<3K | sin_instr. |
|---|---|---|---|---|---|---|---|---|
| Lascar | focal | VIIRS375 | 1437 | 128 | 0,089 | 0,074 a 0,104 | 2 | 126 |
| Lascar | focal | VIIRS750 | 935 | 202 | 0,216 | 0,190 a 0,243 | 103 | 99 |
| Lastarria | focal | VIIRS375 | 1269 | 183 | 0,144 | 0,125 a 0,164 | 3 | 180 |
| Lastarria | focal | VIIRS750 | 455 | 178 | 0,391 | 0,347 a 0,437 | 93 | 85 |
| Isluga | focal | VIIRS375 | 1613 | 296 | 0,183 | 0,164 a 0,202 | 15 | 281 |
| Isluga | focal | VIIRS750 | 555 | 321 | 0,578 | 0,537 a 0,620 | 127 | 193 |
| Tupungatito | nevado | VIIRS375 | 1594 | 228 | 0,143 | 0,126 a 0,161 | 8 | 220 |
| Tupungatito | nevado | VIIRS750 | 405 | 97 | 0,239 | 0,200 a 0,281 | 39 | 58 |
| PlanchonPeteroa | intermedio | VIIRS375 | 1658 | 344 | 0,207 | 0,188 a 0,227 | 5 | 339 |
| PlanchonPeteroa | intermedio | VIIRS750 | 415 | 87 | 0,210 | 0,171 a 0,248 | 14 | 73 |
| NevadosDeChillan | nevado | VIIRS375 | 1007 | 177 | 0,176 | 0,152 a 0,200 | 7 | 170 |
| NevadosDeChillan | nevado | VIIRS750 | 161 | 32 | 0,199 | 0,143 a 0,261 | 26 | 6 |
| Llaima | nevado | VIIRS375 | 1689 | 248 | 0,147 | 0,130 a 0,163 | 34 | 214 |
| Llaima | nevado | VIIRS750 | 378 | 70 | 0,185 | 0,148 a 0,225 | 55 | 15 |
| Villarrica | nevado | VIIRS375 | 2063 | 403 | 0,195 | 0,178 a 0,213 | 55 | 348 |
| Villarrica | nevado | VIIRS750 | 579 | 139 | 0,240 | 0,205 a 0,275 | 83 | 56 |
| Copahue | nevado | VIIRS375 | 1732 | 237 | 0,137 | 0,121 a 0,153 | 8 | 229 |
| Copahue | nevado | VIIRS750 | 312 | 31 | 0,099 | 0,067 a 0,135 | 20 | 11 |
| PuyehueCordonCaulle | nevado | VIIRS375 | 1791 | 179 | 0,100 | 0,086 a 0,115 | 22 | 157 |
| PuyehueCordonCaulle | nevado | VIIRS750 | 1337 | 367 | 0,275 | 0,251 a 0,299 | 182 | 184 |
| Chaiten | nevado | VIIRS375 | 1720 | 446 | 0,259 | 0,239 a 0,280 | 52 | 394 |
| Chaiten | nevado | VIIRS750 | 545 | 124 | 0,228 | 0,193 a 0,262 | 104 | 20 |
| (los 11) | | MODIS | 1327 | SIN DATO | | | | |

MODIS: la fuente `ctx_cluster` no existe (ancla honesta apagada, `ENABLE_HONEST_ANCHOR_MODIS =
False`); con cualquier fuente, 15 de 1.327 visibles tienen fp = 0 y sp > 0 (1,1 %). Sin el rótulo
no se puede separar segundo paso de Test 1 en MODIS: SIN DATO, no "0".

Donde el instrumento existe, el pico bajo el margen se cumple en el 96 a 100 % de los `solo2p`
(p. ej. Chaitén V750 104 de 104 medibles, Villarrica V750 83 de 83): la certeza de que fue la
compuerta la que los eliminó del primer paso.

Noches ALERTA cubiertas ÚNICAMENTE por records `solo2p` (cota superior del costo de cerrar D2 sin
quitar D22) y, de esas, sin Test 1 disparado en ningún record (cota inferior; script 03):

| sensor | alertas | sólo por 2do paso (cota sup.) | IC95 | de esas, sin Test 1 (cota inf.) | IC95 |
|---|---|---|---|---|---|
| VIIRS375 | 896 | 14 (1,6 %) | 0,8 a 2,5 % | 0 (0,0 %) | 0,0 a 0,0 % |
| VIIRS750 | 246 | 41 (16,7 %) | 12,2 a 21,5 % | 10 (4,1 %) | 1,6 a 6,5 % |
| MODIS | 77 | SIN DATO | | | |

La cota inferior 0 de VIIRS375 coincide con el brazo C (segundo paso condicionado) del A/B de
S135: "pierde noches 0" sobre 260 noches confirmadas de 6 volcanes
(`experiments/_s135_ab_d1d2/RESULTADO_FINAL.md:14-20`). Ese A/B no midió VIIRS750 (SOSPECHA: lo
infiero del `evaluar_ab.py`, que filtra I-band; no leí su yml de reproc entero).

Margen del píxel pico (`max bt_k` de `anomaly_pixels` menos `t_bg_k`) en records visibles SIN
Test 1 disparado, por régimen y sensor:

| régimen | sensor | pico < 3 K / medibles | frac | IC95 |
|---|---|---|---|---|
| focal | VIIRS375 | 22 / 37 | 0,595 | 0,432 a 0,757 |
| focal | VIIRS750 | 330 / 484 | 0,682 | 0,640 a 0,725 |
| intermedio | VIIRS375 | 6 / 8 | 0,750 | 0,375 a 1,000 |
| intermedio | VIIRS750 | 14 / 25 | 0,560 | 0,360 a 0,760 |
| nevado | VIIRS375 | 188 / 376 | 0,500 | 0,449 a 0,553 |
| nevado | VIIRS750 | 511 / 1177 | 0,434 | 0,406 a 0,462 |
| focal | MODIS | 2 / 19 | 0,105 | 0,000 a 0,263 |
| nevado | MODIS | 11 / 856 | 0,013 | 0,006 a 0,021 |

Dos lecturas honestas de esta tabla: (i) en VIIRS375 casi todo record visible tiene el Test 1
disparado, así que el instrumento cubre 37 de 4.319 records focales y 376 de 11.595 nevados; los
IC son anchos y el sensor **no** permite concluir "nevado ≠ focal" con este eje. (ii) En VIIRS750
el instrumento cubre 484 y 1.177 records, y la fracción con pico bajo el margen es mayor en los
focales (0,64 a 0,73) que en los nevados (0,41 a 0,46), IC disjuntos: la clasificación
nevado/focal no predice el fenómeno; lo que lo predice es cráter frío frente a un anillo tibio,
que en Isluga (cráter 262,1 K contra anillo 262,4 K, 2026-08-03 05:24) pasa tanto como en
Tupungatito.

## 3. Recomendación: VIIRS desde el inicio, y los tres factores cruzados

**Incluir VIIRS 750 y 375 en el A/B Tier A de D22 y del fondo desde la primera corrida; MODIS
sólo para D21.** Justificación, cada punto anclado arriba:

1. **El costo medible está en VIIRS750** (§2.2): 33 de 246 noches ALERTA (13,4 %) se pierden hoy
   con la firma exacta del mecanismo de S137 (cráter frío, Tests 2 ∧ 3 aprobados, compuerta,
   anillo, 0,0 MW), en 4 volcanes distintos (Tupungatito 8/14, Isluga 11/40, PP 4/9, Láscar 8/136).
   MODIS no tiene ni un caso (0 de 77). Un A/B "MODIS primero" mediría el fenómeno donde no vive.
2. **MODIS no se puede evaluar hoy sobre el dashboard** (§5, hallazgo 3): 76 de las 77 noches
   ALERTA MODIS son de Láscar y 59 quedan `far` por el ancla legacy aunque el cúmulo esté en el
   cráter. Cualquier métrica de noches visibles del brazo MODIS sale dominada por ese rótulo, no
   por D21/D22. El brazo MODIS de D21 debe evaluarse con el criterio "cráter" (`pc.centroid_dist
   <= inner`, como hace `auto_audit_weekly.py:234`), no con `distance_class`, y saberlo antes
   de correr.
3. **Los factores están acoplados y hay que cruzarlos** (§2.3): en VIIRS375 la compuerta ya no
   decide la detección (9 a 26 % de lo visible viene del segundo paso sin compuerta) y la
   magnitud la decide el fondo. Brazos mínimos: {compuerta ON, OFF} × {anillo, fondo local
   (corona Eq.6 o kernel)} × {segundo paso como hoy, condicionado}. Un brazo que quite sólo la
   compuerta va a salir "sin efecto" en detección V375 y engañará; uno que condicione sólo el
   segundo paso costará 10 a 41 noches V750 (§2.3). S137 ya vio en MODIS que las tres correcciones
   juntas devolvieron Villarrica A6 y ninguna sola (`experiments/_s137/RESULTADO_FONDO_LOCAL.md`).
4. **Poder** (T8): VIIRS375 tiene 896 noches ALERTA y VIIRS750 246, contra 77 de MODIS (76 de un
   solo volcán). Los IC de §2.2 ya separan sensores y volcanes; con MODIS solo no se separa nada.
5. **Riesgo pre-registrable**: quitar la compuerta puede devolver falsos positivos fríos (nube,
   borde de disco). El dato de hoy ya contiene ese universo: los 2.354 records V750 y 300 V375
   "segundo paso sin activos" con VRP 0 son exactamente los píxeles que entrarían sin compuerta;
   el A/B debe contar cuántos de ellos MIROVA confirma por noche (en §2.2, 31 de 33 noches
   perdidas V750 sí están confirmadas) y cuántos no.

Criterio de evaluación que propongo pre-registrar: noches por volcán y sensor (A94), recall
"cráter" y "dashboard" por separado, magnitud mediana con IC por bootstrap (método de
`experiments/_s124_f70/05_poder_estadistico.py`), y para VIIRS750 el objetivo concreto de
recuperar las 33 noches de §2.2 sin agregar noches no confirmadas por encima de la tasa actual.

## 4. Probe por etapa (escrito, NO disparado)

Archivos en `experiments/_s138_audit/eje4/`:

- `probe_compuerta_viirs.py`: patrón A75 (envoltorios en los namespaces de `pipeline.process_viirs`
  y `pipeline.process_viirs_mod`, como `experiments/_s135_probe_etapas/probe_etapas.py`). Por
  pasada y dentro del inner: Test 2, Test 3, ambos, ambos + compuerta y **sólo compuerta**, con
  las dos conectivas; píxel del cráter y mejor candidato con dNTI/dETI/BT; `newly_active` del
  segundo paso y cuántos están bajo la compuerta; y la magnitud del cúmulo del cráter con tres
  fondos (anillo 5-25 km, kernel 3x3, corona Eq.6). Compila (`py_compile`) y los seis nombres que
  parchea existen en ambos módulos (verificado con `getattr`).
- `pasadas_eje4.json`: 12 pasadas. Villarrica VIIRS375 (3 "sólo segundo paso", 2 noches sólo
  `test1_roi` con MIROVA 0,53 y 0,08 MW, 1 control con fp > 0), Láscar VIIRS375 control (misma
  pasada del probe S135), Tupungatito/Isluga/Láscar VIIRS750 (5 pasadas de noches perdidas con
  pc0, §2.2).
- `probe-s138-eje4-compuerta-viirs.yml`: parsea con `"on"` como cadena (A43). **No está en
  `.github/workflows/`**: copiarlo y dispararlo es decisión del orquestador.

Por qué hace falta aunque §2 ya cuantifique: el pipeline no persiste el conteo pre-compuerta
(§1.3), así que el "sólo compuerta" de `data/` es una inferencia por la puerta trasera del
segundo paso; el probe lo mide directo, y además mide la magnitud con fondo local en VIIRS, que
S137 sólo midió en MODIS. Controles pre-registrados en el docstring del script.

## 5. Hallazgos (formato del preámbulo, peor primero)

### H1. VIIRS750 pierde 33 de 246 noches ALERTA con el cráter detectado en 0,0 MW
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:532` (compuerta) + `:887` y `:939-948`
  (segundo paso sin activos y sin compuerta) + `pipeline/process_viirs_mod.py:985` (recorte al
  anillo). SCRIPT: `01_pc0_noches.py`, `out/01_salida.txt` tabla (a3).
- QUÉ PASA: en un cráter más frío en BT MIR que la mediana del anillo (Tupungatito 4 a 6 K por
  debajo, Isluga 0,2 K), la lava sub-píxel sube el dNTI pero no la BT; la compuerta lo elimina del
  primer paso, el segundo paso lo recupera sin compuerta y el fondo del anillo deja ΔL ≤ 0.
  Resultado: `primary_cluster` de 1 píxel en el cráter con `vrp_mw = 0.0`.
- CÓMO SE VE EN EL DASHBOARD: invisible (`mirovaEqVrp` devuelve 0 con `pc.vrp_mw = 0`). MIROVA
  publica 0,17 a 0,52 MW esas noches.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s138_audit/eje4/01_pc0_noches.py`;
  Tupungatito 2026-08-21 05:30 UTC `VIIRS_SNPP_750` (BT 250,39 K, `t_bg_k` 256,38 K).
- CONFIANZA: CONFIRMADO sobre data persistida (33 noches, 11 volcanes, ventana 2026-01-11 a
  2026-09-07). La atribución "cayó por la compuerta" es inferencia (fp = 0, sp > 0, BT ≤ t_bg): el
  probe de §4 la vuelve medición directa.
- GRAVEDAD: 4. Tupungatito V750 pierde 8 de 14 noches; en un volcán con anomalía débil y
  persistente es la diferencia entre "sigue" y "se apagó".

### H2. La compuerta está neutralizada de facto en detección por el segundo paso; D22, D19/D2 y el fondo no se pueden A/B-ear por separado
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1284-1317`, `process_viirs_mod.py:876-909`,
  `process_modis.py:919-951` (el hot mask final es `final_active_mask`, sin compuerta);
  `ENABLE_SECOND_PASS_CONDITIONED = False`; guard `detection_context.py:887`. SCRIPT: `02_compuerta_margen.py` (b1, b2),
  `03_solo2p_sin_test1.py`.
- QUÉ PASA: 9 a 26 % de los records visibles de VIIRS375 y 10 a 58 % de VIIRS750 vienen sólo del
  segundo paso sin activos (fp = 0, sp > 0); donde el pico es medible, 96 a 100 % está bajo el
  margen de 3 K. La compuerta decide la magnitud (vía qué píxeles suman) pero ya casi no decide la
  detección. Cerrar D2 sin quitar D22 costaría en VIIRS750 entre 10 y 41 noches de 246.
- CÓMO SE VE EN EL DASHBOARD: hoy, nada distinto; el riesgo es en el A/B (un brazo "sin
  compuerta" sin efecto aparente; un brazo "segundo paso condicionado" con pérdida V750).
- CÓMO REPRODUCIRLO: `python experiments/_s138_audit/eje4/02_compuerta_margen.py` y `03_...py`.
- CONFIANZA: CONFIRMADO (medición); la predicción sobre el A/B es SOSPECHA hasta correrlo.
- GRAVEDAD: 3 (torce decisiones de diseño del A/B, no una alerta directa).

### H3. MODIS Láscar: 59 de 76 noches ALERTA con el cúmulo en el cráter y rótulo `far`
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py`-equivalente en MODIS: `final_hotspot_*` legacy
  (`process_modis.py`, fuente `eruption`) con `ENABLE_HONEST_ANCHOR_MODIS = False`
  (`experiments/_s138_audit/eje1/profile_flags_efectivos.txt`); dashboard
  `frontend/index.html:1056`. SCRIPT: `01_pc0_noches.py` (columna `perd_no_vis`) y la consulta
  ad hoc de esta sesión (Counter: `('far', centroid<=5, vrp>0, 'eruption')` = 59).
- QUÉ PASA: el píxel más caliente de la escena está a 25 a 31 km (Salar), `distance_class = far`,
  mientras `primary_cluster` (vent-anchored) está a 3 a 4 km con 0,1 a 1,8 MW y `geo_class =
  summit`; MIROVA publica 0,6 a 2,3 MW. Es la cara (b) de A81 (far→summit oculto), aquí sin la
  atenuante "otra pasada summit cubre la noche": no la cubre ninguna pasada MODIS.
- CÓMO SE VE EN EL DASHBOARD: Láscar MODIS ausente en 67 de 76 noches; el operador ve Láscar por
  VIIRS375 (166 de 176), así que no pierde el volcán, pierde el sensor.
- CÓMO REPRODUCIRLO: Láscar `MODIS_TERRA` 2026-02-09 01:40 UTC: `final_hotspot_dist_km` 27,07,
  `primary_cluster.centroid_dist_km` 3,515, `vrp_mw` 0,893; MIROVA 1,67 MW.
- CONFIANZA: CONFIRMADO. Conocido en su mecanismo (A46/A81/A82, S114 "MODIS 16 %"); el número de
  hoy y su concentración en Láscar (el único volcán con ALERTAs MODIS en la ventana) son nuevos.
- GRAVEDAD: 3 para el operador (redundancia VIIRS); 4 para el A/B de D21, que sin criterio
  "cráter" no puede medir nada en MODIS.

### H4. VIIRS375: 1.157 records con cúmulo `test1_roi` de 1 píxel en 0,0 MW y sin píxel persistido
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1788-1795` (`keep_peak`), `:1828` (fondo efectivo),
  `:1889` (recorte), `:1898` (`build_anomaly_pixels` descarta VRP 0), `anchor.py:89` (`test1_roi`
  a 0,0 km). SCRIPT: `01_pc0_noches.py` (a1/a2).
- QUÉ PASA: el Test 1 dispara sobre el disco, `keep_peak` deja un píxel que está bajo el fondo
  efectivo, el ΔL se recorta a 0 y el record sale con fuente `test1_roi`, distancia 0,0 km,
  `n_pixels = 1`, `vrp_mw = 0`, `anomaly_pixels = []`. NdC 502, Lastarria 395, Láscar 219.
- CÓMO SE VE EN EL DASHBOARD: invisible; en noches 6 de 896 (0,7 %), porque otra pasada cubre.
- CÓMO REPRODUCIRLO: script 01; Lastarria VIIRS375 noches 2026-06-14/22/27 y 07-27 (MIROVA 0,03 a
  0,05 MW).
- CONFIANZA: CONFIRMADO. Es la "pata de magnitud de keep_peak" de D19 (S134), cuantificada en
  records y noches; no es D22.
- GRAVEDAD: 2 (costo en noches bajo; en records es el 78 % de los ceros de VIIRS375).

### H5. Instrumento: `anomaly_pixels` no es el hot mask contextual cuando el Test 1 disparó
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1898`, `process_viirs_mod.py:1227`,
  `process_modis.py:1385` (bloque S94 dentro de `if final_hotspot_source == "test1"`), seguido
  del re-rotulado del ancla honesta (`:1990-2020`, `resolve_honest_anchor`).
- QUÉ PASA: el record dice `ctx_cluster` pero sus píxeles persistidos son el footprint del Test 1.
  Una auditoría que lea "el píxel pico del cúmulo contextual" de ahí se equivoca; en esta sesión
  produjo 489 falsos "pico bajo el margen con fp > 0" antes de detectarlo.
- CÓMO SE VE EN EL DASHBOARD: el mapa de píxeles de esos records muestra el píxel del Test 1, no
  el cúmulo que da la magnitud (SOSPECHA: no verifiqué el render).
- CÓMO REPRODUCIRLO: `02_compuerta_margen.py` con `margen_pico` sin la exclusión de
  `triggered_test1` (control P1 pasa de 8 a 489 sobre 9.497).
- CONFIANZA: CONFIRMADO (código + control).
- GRAVEDAD: 2 (tuerce auditorías y el A/B si usan `anomaly_pixels`; no la alerta).

### H6. Docstring de `contextual_dnti_hot_mask` dice "median" donde el código usa media
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:220-225` ("8-neighbor median",
  "median(NTI_8_vecinos)") contra `_nanmean_ignore_self` (`:192-204`, media aritmética, D1 S17).
- QUÉ PASA: texto viejo; el código es el correcto (Coppola 2016a, media aritmética).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## 6. VERIFICADO LIMPIO

- La compuerta es UNA (`detection_context.py:532` y `:269`) con el mismo margen 3,0 K en los
  tres sensores; no hay márgenes distintos por sensor. Comando: `grep -n "bt_sanity_k\|NTI_BT_SANITY_K"
  pipeline/process_viirs.py pipeline/process_viirs_mod.py pipeline/process_modis.py pipeline/detection_context.py`
  + `python -c "import pipeline.process_viirs as p, pipeline.process_viirs_mod as m; print(p.NTI_BT_SANITY_K, m.NTI_BT_SANITY_K)"`.
- El Test 1 integrado no tiene compuerta de temperatura (`grep -n "bt_sanity\|t_bg" pipeline/test1_integrated.py`
  sólo devuelve mensajes de fondo insuficiente).
- `ENABLE_SECOND_PASS_CONDITIONED = False`, `ENABLE_FINAL_PIXEL_FILTER = False`,
  `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = False`, `ENABLE_UNSUITABLE_FILTERS_267_273 = True`,
  `ENABLE_TESTS_23_PROSE_BRANCH = False` (eje 1, `profile_flags_efectivos.txt`); consistentes con
  el comportamiento medido (los pc0 con fp = 0 y sp > 0 sólo existen si el segundo paso corre sin
  activos y sin compuerta).
- Diagnósticos `t_bg_k`, `t_max_k`, `diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`
  presentes en el 100 % de los records de los 11 Tier A (conteo por archivo en la primera corrida
  de esta sesión, p. ej. Villarrica 6.545/6.545).
- Convención de sensor verificada con `Counter` (sin sufijo = I-band 375 m; `_750` = M-band);
  nombres de volcán del CSV verificados con `sorted(set(...))` y resueltos por
  `normalize_volcano_name` (11 de 11 Tier A mapean).
- Loader `load_mirova_alertas`: 1.952 pasadas-ALERTA CONS ∪ OCR, 2026-01-11 a 2026-09-07, dedup
  por (timestamp, volcán, sensor); filtro diurno idéntico al del pipeline (110 excluidas).
- Control positivo y negativo del cruce por noche pasan (script 01); control del instrumento del
  pico: 8 de 9.497 tras excluir `triggered_test1` (residuo compatible con kernel local, no
  investigado más: SOSPECHA de causa, no de efecto).
- El criterio "visible" del script reproduce `mirovaEqVrp` (`frontend/index.html:1043-1064`) y
  `mirovaEqVrpCore` nunca borra una detección (`:1184`).
- La cota inferior 0 de noches V375 perdidas al condicionar el segundo paso coincide con el brazo
  C de S135 (0 de 260), instrumento independiente.
- No se modificó nada fuera de `docs/audit_s138/EJE_4_d21_d22_viirs.md` y
  `experiments/_s138_audit/eje4/` (`git status` al cierre); no se disparó ningún workflow ni se
  descargó ningún granule.
