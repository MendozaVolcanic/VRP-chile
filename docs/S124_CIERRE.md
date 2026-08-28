# Cierre S124 — todo lo aprendido, probado, refutado y pendiente

> Sesión larga (2026-08-26 al 28). Este documento es el estado completo para
> arrancar S125 sin releer la conversación. Regla: cada afirmación dice **cómo
> se probó**; lo no probado va marcado como tal.

---

## 1. Lo que quedó PROBADO (con script reproducible)

| hallazgo | cómo se probó |
|---|---|
| **La banda de paridad se aplicaba mal.** La auditoría juzgaba la MEDIANA con la banda de una detección suelta ([0,5-2,0] en vez de [0,7-1,4]) | `tests/test_audit_ratio_band_s124.py`; con la banda correcta 4 de 11 sub-reportan |
| **`Distancia_km` de MIROVA está cuantizado a celdas de su grilla** | `experiments/_s124_cuantizacion/01_distancia_es_celdas.py`: 100 % de 10.085 registros MODIS con celda 1 km y 100 % de 11.810 VIIRS375 con 0,375 km. Control con celdas arbitrarias baja a 89-93 % |
| **Los GeoTIFF del archivo llevan la grilla real de MIROVA** | `rasterio` sobre `../mirova-tif-archive`: 134×134 VIIRS375, 51×51 MODIS, origen fijo entre pasadas |
| **El regrid F70 se ejecutó de verdad en los brazos A y B** | coordenadas de píxeles anómalos: dispersas (6-37 m) en el control vs **cuantizadas a 375 m** en A/B |
| **El merge por trozos resucitaba meses sin reprocesar, con el run VERDE** | `experiments/_s124_ndc_focus/05_verificar_reproceso.py`: jun/jul/ago 100 % idénticos byte a byte tras un reproceso "exitoso". Arreglado + test de regresión |
| **Villarrica corría un perfil congelado con 32 constantes distintas** | A/B historia completa (#519): recall VIIRS375 89,7 → **100 %**, VIIRS750 4,86 → **0,88×** |
| **MIROVA NO integra un halo** | dataset Campus 2024 (Vulcano): su Npix mediano es **1**; el 54 % de sus alertas son de un solo píxel |
| **6,1 % de la ground truth es diurna** y entraba al denominador del recall | filtro solar en la auditoría (#518), reusando `_reject_daytime` de store.py |

## 2. Lo REFUTADO (no reabrir sin evidencia nueva — anti-A8)

| hipótesis | cómo cayó |
|---|---|
| **La grilla UTM explica el sub-reporte** (frente F70, D16) | A/B de 4 brazos con criterios pre-registrados: brazo A ≡ control, brazo B ≈ C. Ningún criterio se cumple |
| La ceguera por máscara de nube nos cuesta recall | solo **6 de 276** alertas caen en noches ciegas (2 %) contra una tasa base de ceguera del 23 % — diez veces menos que el azar |
| Las 3 alertas NdC "perdidas" se perdieron por ceguera | estaban a 2,86 · 3,02 · 4,14 km del cráter (una además diurna): irreproducibles **por construcción**, no por ceguera |
| El déficit es atribución de cluster / second-run / piso VRP / fondo del anillo solo | medidos y descartados uno por uno en S124 |
| «Julio en NdC fue un apagón por nube» | julio tuvo **más** detecciones summit (68) que ningún mes |

## 3. Errores propios de esta sesión (patrones a vigilar)

1. **Medir contra el ancla equivocada.** D17 se publicó midiendo el offset contra
   el cráter, y presentó como hallazgo algo que `geo_utils.py:14-22` documenta
   **desde S98**. Trampa A50 pura: estaba en el repo.
2. **Leer una mediana como si fuera un efecto.** «La grilla no hace nada» venía
   de una diferencia mediana de 0,000 que en realidad **promediaba efectos
   opuestos** (Láscar +0,11, PCC −0,10).
3. **Afirmar identidad desde 2 decimales.** «B ≡ C exacto» era falso: 0,00068 de
   diferencia, indistinguible pero no idéntico.
4. **El nombre del campo y el nivel del YAML.** Dos veces: `local_kernel_bg` (no
   `..._compatible`) y `enable_utm_regrid` bajo `thresholds:` (no en la raíz).
   El segundo habría dejado el A/B entero en nulo sin ningún síntoma.
5. **Comparar corridas sin restringir a pasadas comunes** — origen de la falsa
   conclusión «la réplica detecta más que el experimental».
6. **Chequear un evento fuera de la ventana del experimento** y leerlo como
   fallo del brazo.

## 4. LA HIPÓTESIS VIVA — D17 corregida

Nuestro regrid F70 se centró en `volcano["lat"/"lon"]`; MIROVA centra en
`mirova_center` (verificado: el campo del yaml, derivado de los KMZ en S80,
coincide con el centro de los GeoTIFF dentro de 10-408 m).

| volcán | offset | | volcán | offset |
|---|---|---|---|---|
| **Tupungatito** | **2996 m** | | Isluga | 368 m |
| **Planchón-Peteroa** | **1873 m** | | Láscar | 186 m |
| Chaitén | 396 m | | resto | 115-147 m |
| Villarrica | 389 m · NdC 385 m | | | |

Con celda de 375 m, un offset > 187 m desplaza la partición media celda: pasa en
**6 de 11**.

**Y el cabo suelto que la hace verosímil**: `geo_utils.get_grid_center()` existe
desde S98 exactamente para esto (prioridad `mirova_center` → `vent` → `lat/lon`)
y **nadie la llama**. El brazo D es cablearla: una línea en el llamador, con
función ya testeada.

**Evidencia a favor, sugestiva**: el efecto de la grilla correlaciona con la
desalineación (r = −0,47, n=8, p ≈ 0,24). No alcanza para probarla.

## 5. El replanteo de prioridad

Los brazos de F70 mueven **0,11** cuando el hueco es **0,53**: cierran ~20 %.
Optimizar decimales mientras el sesgo de fondo es **factor 2** es mirar el lugar
equivocado.

- **Para detectar**: irrelevante (recall 96 %, ninguna variante lo mueve).
- **Para cuantificar**: sí importa — el VRP alimenta la tasa de efusión
  (`TADR ~ VRP / c_rad`), así que factor 2 en VRP es factor 2 en el volumen de
  magma inferido.

**Lo nunca auditado**: la cadena de MAGNITUD contra Coppola Eq. 6-8, file:line.
La detección se auditó así en S114; la magnitud jamás. Es mi principal sospecha.

## 6. Infraestructura que quedó lista

- **Reprocesos en paralelo**: la concurrencia pasó a ser por perfil
  (`reproc-chunked-<profile>`). El límite real es GitHub (20 jobs concurrentes,
  minutos ilimitados en repo público): entran 2 brazos completos. **No hace
  falta otra cuenta.** El push a main sigue serializado (`push-main`).
- `05_verificar_reproceso.py` — correr tras **todo** reproceso sobre un subdir
  con data previa. Sale con código 1 si detecta meses sin reprocesar.
- `03_leer_brazo.py` / `04_tabla_brazos.py` / `05_poder_estadistico.py` —
  lectura apareada, tabla de brazos, y bootstrap de IC.
- `02_origen_grilla_por_volcan.py` — centros de grilla desde los GeoTIFF.
- Suite en **906 tests verdes**.

## 7. Datos disponibles tras la sesión

| perfil | volcanes | qué es |
|---|---|---|
| `mirova_equivalent` | 45 | operacional (control) |
| `_f70_a` | 11 | grilla sola |
| `_f70_b` | 11 | grilla + kernel global |
| `_s124_kernelbg_ab` | 6 | kernel solo (brazo C) |
| `experimental_ndc_focus` | 1 | NdC v2, verificado |

---

## 8. PENDIENTE para S125 — en orden

### 8.1 Regenerar las figuras de Chillán (TAREA EXPLÍCITA DE NICOLÁS)

Con los datos v2 ya reprocesados **y** las mejoras de visualización aprendidas:

- [ ] Regenerar `plot_simple.py` y `plot_mapa.py` con la serie completa.
- [ ] **Mejoras ya identificadas y no aplicadas:**
  - El panel de observabilidad usa σ del fondo, que es un proxy: una nube
    estratiforme muy pareja y el pipeline ciego se parecen. Anotarlo en la
    figura como limitación, o reemplazarlo por la máscara oficial del sensor
    (`CLDMSK_L2_VIIRS`, verificada disponible con versión NRT).
  - El mapa dibuja la grilla de MIROVA de sus GeoTIFF (reproyección lat/lon).
    Con `get_grid_center()` cableado se podría dibujar la celda de referencia
    exacta.
  - Verificar que las etiquetas sigan coherentes tras cambiar datos (esta sesión
    quedaron tres veces textos que decían «1 km» con radio de 500 m).
- [ ] **Correr el audit adversarial de figuras otra vez** antes de darlas por
  buenas — la vez anterior encontró 9 problemas, 3 graves.

### 8.2 Brazo D — la hipótesis viva

- [ ] Cablear `get_grid_center()` en `run_pipeline.py` tras un flag nuevo
  (`enable_mirova_grid_center`), con test que falle si se desconecta.
- [ ] Perfil `_f70_d.yaml` + control `_f70_control_4m.yaml` (clon del
  operacional con `data_subdir` aislado — el workflow rehúsa correr contra
  `mirova_equivalent`).
- [ ] **Criterio pre-registrado ANTES de correr**, con el control interno que al
  brazo B le faltó: los volcanes de offset chico (Lastarria 115 m, Copahue
  140 m, Llaima 142 m) **no deben cambiar**. Si cambian, el efecto no es la
  alineación. Jueces: Tupungatito y Planchón-Peteroa.
- [ ] Ventana **4 meses** (2026-04-25..08-24): la muestra pasa de 178 a **432**
  noches-alerta. Los dos brazos **en paralelo**, ~9 h.
- [ ] Veredicto con **IC bootstrap que no se solapen** — una mediana sin
  intervalo no decide nada.

### 8.3 El 80 % del hueco (sin consumir CI, en paralelo)

- [ ] Descomponer la brecha por régimen (`n_anomalous_pixels`) en los 4
  sub-reportadores: si el déficit vive solo en el modo de 1-2 píxeles, el
  problema es de integración sub-píxel, no de fondo.
- [ ] Cruce **pixel-level contra el TIF de MIROVA** en noches donde ambos
  detectan (`test_r2_pixel_level.py` ya cruza 9 casos): en la MISMA celda,
  ¿cuánta radiancia reporta cada uno? Separa «medimos distinto el fondo» de
  «medimos distinto el foco».
- [ ] **Auditoría file:line de la cadena de magnitud** contra Coppola Eq. 6-8.

### 8.4 Deuda documentada

- [ ] **D14** — máscara de nube <260 K: `MISSION.md` la declara removida y está
  activa; ciega el 23 % de las pasadas; confunde nieve con nube. No cuesta
  recall, así que es deuda, no urgencia.
- [ ] **D15** — celda de referencia del `Distancia_km`, en UTM (falló 0/4 en la
  reproyección lat/lon).
- [ ] Test de determinismo + manifiesto de cobertura por corrida (diseños).
- [ ] Revisar los hallazgos de las 3 auditorías despachadas al cierre de S124
  (afirmaciones, código huérfano, reglas A) — ver §9.
