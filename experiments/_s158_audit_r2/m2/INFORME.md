# M2 (S158, segunda ronda): MODIS de punta a punta, store.py y las tres vistas del tablero

Auditor independiente, contexto limpio. Fecha de la corrida: 2026-10-21 17:04 UTC. Worktree
`.claude/worktrees/s158-audit-r2-0eeee2`, HEAD `e81bfadd5`. Corpus: `data/mirova_equivalent/*.json`,
74.811 records en 45 volcanes, último record 2026-10-21 08:10 UTC (`00_censo_records.txt`).

Independencia: no leí `docs/AUDIT_S158.md`, nada bajo `experiments/_s158_audit/`, el oráculo, ni
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`. Las marcas «S158» de `CLAUDE.md` las traté como afirmaciones. Los
dos `.m` de MIROVA y su README los leí sólo para saber qué NO puedo trasladar a MODIS: ninguna afirmación de
este informe sobre MODIS se apoya en ese código; la vara de MODIS es `documentacion/sp426.5.pdf` leído
renderizado (`paper_pages/sp426_p3.png`, `p6`, `p7`, `p8`) y el coeficiente empírico k = 18,9 de `CLAUDE.md`.

Convención de sensores comprobada con un Counter (`00_censo_records.txt`): `VIIRS_SNPP`, `VIIRS_NOAA20`,
`VIIRS_NOAA21` sin sufijo son 29.985 records (I-band 375 m); con `_750`, 29.743; `MODIS_TERRA` 7.429 y
`MODIS_AQUA` 7.654. Flags efectivos leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`
(`flags_efectivos_mirova_equivalent.txt`), nunca del YAML.

Scripts y salidas crudas, todos en esta carpeta:

| script | salida | qué mide |
|---|---|---|
| `01_store_sustrato.py` | `01_store_sustrato.txt`, `01b_nrt_edad_y_tierB.txt` | duplicados, diurnos, geofence, NRT, descartes, cap |
| `02_interp_geo_sintetico.py` | `02_interp_geo_sintetico.txt`, `02a_datadict_line_frame_numbers.txt` | error de `_interp_geo` en píxeles |
| `03_firma_geo_en_records.py` | `03_firma_geo_en_records.txt` | corrimiento hacia el nadir en los records, por sensor y cenit |
| `04_modis_deteccion_sin_magnitud.py` | `04_modis_deteccion_sin_magnitud.txt` | detecciones con cúmulo y VRP cero |
| `05_tres_vistas.js` (node 22) | `05_tres_vistas.txt` | index contra diario contra mosaico, record por record |
| `06` (en línea, guardado) | `06_lambda_y_test1_k1.txt` | efecto de λ en el VRP y en NTI_app; sustrato del Test 1 por píxel |
| `07` (en línea, guardado) | `07_filtro_distancia_vrp_mw.txt` | qué hace el filtro por distancia con `vrp_mw` |

---

## 1. Veredictos sobre las afirmaciones del alcance

### 1.1 MODIS: qué banda es la primaria y dónde se decide la saturación

**CONFIRMADA, con un matiz.** `ENABLE_MODIS_B22_PRIMARY = True` en el perfil efectivo. `pipeline/process_modis.py:593`
arma la banda MIR con `merge_mir_bands(rad21, rad22, True)`, que en `:338-339` devuelve B22 y cae a B21 sólo donde
B22 es NaN. La saturación se decide antes, en `read_modis_l1b` `:251-258`: todo DN > 32767 pasa a NaN, lo que
incluye el centinela 65533 «Detector is saturated» (`MODIS_L1B_UserGuide_C7.md:2482`). Eso coincide con el
paper, p. 3, columna derecha: «band L21ok, by using the L21 or L22 radiance, depending on band 22 saturation
(or not)».

Matiz (hallazgo H4): el mismo párrafo del paper dice que se eliminan los DN > 32 768 «with the exception of the
pixels with DN = 65 533, indicating saturated values». Nosotros no hacemos la excepción: un píxel saturado en B22
y también en B21 (centinela en las dos) queda NaN en `bt_mir` y desaparece de todo (umbrales, cúmulo, `t_max`).
Encima, `:607-608` (`ENABLE_BT_SAT_SECONDARY_GUARD = True`) vuelve NaN cualquier BT MIR sobre 500 K aunque sea
un valor calibrado válido. Sustrato en Chile: ninguno medido (no hay forma de contarlo desde los JSON, porque el
píxel ya no está). Vale para una erupción grande, no para la vigilancia de todos los días.

### 1.2 MODIS: cómo se arma el fondo del VRP y si se recorta

**REFUTADA respecto del paper, y con efecto medido.** El paper (p. 8, Ec. 6) define L4bk como «the arithmetic mean
of all the pixels surrounding the active one (or around the active cluster)». El pipeline hace otra cosa:

- en 6 de los 11 Tier A (los que no tienen `local_kernel_bg: true`: Láscar, Isluga, Tupungatito, NdC, Copahue,
  Llaima) el fondo es `L_bg_global` (`process_modis.py:1083`), la mediana de temperatura del anillo de 5 a 25 km
  (`compute_bg_stats`, `detection_context.py:1083`, mediana sobre `bg_mask` = `dist` entre `BG_INNER_KM = 5` y
  `BG_OUTER_KM = 25`, `process_modis.py:582`) convertida a radiancia;
- en los otros 5 (PCC, Villarrica, Chaitén, PP, Lastarria) es la media del kernel 3 × 3 alrededor de cada píxel
  caliente (`:1102-1111`), lo más parecido al paper;
- y en todos, el exceso se recorta a cero: `delta_L = np.maximum(hotpix_rad - L_bg, 0.0)` (`:1118`). El paper no
  recorta.

Efecto físico: en un volcán alto y nevado el cráter es localmente anómalo (lo marca el contraste de 8 vecinos)
pero puede estar más frío que la mediana de un anillo que mete valles a 20 km. Entonces el detector dice
«anómalo» y la magnitud dice 0. Medido (`04_modis_deteccion_sin_magnitud.txt`): de 619 records MODIS con
píxeles anómalos en Tier A (593 antes de la observación del 2026-09-18 y 26 desde entonces), **37 tienen el
cúmulo dentro del inner y `pc.vrp_mw == 0`** (Láscar 30, Isluga 3, NdC 3, Tupungatito 1; ninguno en los 5
volcanes con kernel local). Ejemplo: Láscar 2025-02-28 06:45 MODIS_AQUA, `t_max_k` 284,59, `t_bg_k` 270,05, 2
píxeles, VRP 0. De esos 37, **9 tienen alerta de MIROVA a ±60 min** (`05_tres_vistas.txt`, cruce con
`data/mirova/<volcán>.json` usando `enrichWithMirovaConfirmation` de index.html). Es el hallazgo H2.

Lo mismo pasa, con más volumen, en VIIRS 750 (600 de 2.733 detecciones con `pc.vrp_mw == 0`) y VIIRS 375
(278 de 9.690); está fuera de mi alcance y va en «Fuera de alcance».

### 1.3 MODIS: la geolocalización de la grilla de 5 km (la SOSPECHA de la memoria)

**CONFIRMADA: se sostiene, y tiene la firma en los datos.** Hallazgo H1, el más grave de este informe.

Qué dice el producto. `MOD021KM` trae `Latitude`/`Longitude` a 5 km, 406 × 271 para 2030 × 1354
(`MODIS_L1B_UserGuide_C7.md:1808`). Esos puntos NO son el píxel 0 de cada bloque: son los detectores 3 y 8 de
cada barrido de 10 líneas y los frames 3, 8, 13, ... (atributos `line_numbers` = «3, 8» y `frame_numbers` =
«3, 8, 13, ...», `MODIS_L1B_DataDictionary_C7.pdf`, página impresa 100, texto en
`02a_datadict_line_frame_numbers.txt`). En índice 0 eso es línea 2 + 5k y muestra 2 + 5k: 2 + 5·405 = 2027 y
2 + 5·270 = 1352, que es por qué salen 406 y 271.

Qué hace el pipeline. `_interp_geo` (`process_modis.py:385-396`) llama `scipy.ndimage.zoom(coarse, (2030/406,
1354/271), order=1)`. `zoom` estira la grilla gruesa de modo que su primer punto cae en el píxel 0 y el último en
el píxel 2029 o 1353. No sabe del desfase de 2.

Medición 1, sintética (`02_interp_geo_sintetico.txt`): fabriqué una geolocalización «verdadera» cuyo valor es
el índice del píxel, la submuestreé como el producto (`[2::5, 2::5]`) y la pasé por la misma `_interp_geo` del
repo. Error en muestras: +2,000 px en la columna 0, +1,25 en la 338, **+0,50 en el nadir (col 677)**, −0,25 en
la 1016, −1,000 en la 1353. En líneas: +2,00 en la línea 0, 0,00 en la 1015, −2,00 en la 2029. En 1.128 de las
1.354 columnas el corrimiento apunta hacia el nadir (en el resto, las 226 columnas entre la 677 y la 902, es
menor a 0,5 px y apunta hacia afuera; el error cruza cero en la columna 902). Convertido a suelo con el ancho de píxel del repo
(`modis_zenith_from_column`): +0,5 km en el nadir, +1,7 km a 31° (lado izquierdo), −2,25 km a 54° (lado
derecho), +5,2 km a 54° (lado izquierdo), y hasta ±6 a 12 km en los bordes. Control: con una grilla que sí
parte en el píxel 0 el error en la columna 0 es 0,000 (el instrumento distingue).

Medición 2, en los records (`03_firma_geo_en_records.txt`): para cada record Tier A con cúmulo dentro del inner
y ángulos (`sensor_azimuth_deg`, `sensor_zenith_deg`, persistidos desde S122), proyecté el vector (centroide del
cúmulo menos cráter) sobre la dirección al satélite. Si la geolocalización corre los píxeles hacia el nadir, la
mediana de esa proyección es positiva y crece con el cenit; VIIRS 375 y 750 (que usan su propio archivo de
geolocalización, `process_viirs.py:758`) son el control, y la proyección perpendicular es el control de
instrumento. Resultado, sin Lastarria ni PCC (sesgos reales conocidos), numerador = records con cúmulo en el
inner, todo el corpus:

| cenit | MODIS mediana hacia el nadir (n) | VIIRS 375 (n) | VIIRS 750 (n) | MODIS perpendicular |
|---|---|---|---|---|
| 0 a 20° | +0,01 km (167) | +0,01 (1.341) | +0,01 (433) | −0,01 |
| 20 a 40° | **+0,94 km** (157) | +0,04 (1.396) | +0,03 (399) | −0,10 |
| 40 a 55° | **+1,66 km** (50) | +0,09 (1.375) | +0,05 (357) | −0,16 |
| 55 a 70° | (n = 2, sin dato) | −0,15 (771) | −0,11 (66) | |

Sólo MODIS muestra el sesgo, sólo en la dirección al satélite, y crece con el cenit; en el nadir el +0,5 km
predicho queda dentro de la cuantización de 1 km. Por volcán, Láscar (n = 336) da +0,56 km en MODIS contra
+0,08 en VIIRS 375 y +0,05 en VIIRS 750. Es la misma firma que predice la medición 1. El desfase en líneas (±2
líneas, 1 a 4 km según el cenit, hacia el centro del gránulo) no lo puedo ver con este instrumento.

Dónde pega: `dist` y `vent_dist_per_pixel` (`:560-566`) salen de esas lat/lon, y de ahí salen la máscara
summit/scene de los umbrales (5σ y C1 0,003 contra 10σ y 0,01), el anillo de fondo, `centroid_dist_km`,
`distance_class` y la posición en el mapa. Un cráter real a 1 km del vent puede quedar a 2,7 km en una pasada
a 45°; con inner de 3 km (Lastarria, PP) eso cruza la frontera summit/far.

La corrección está descargada: `run_pipeline.py` baja y empareja `MOD03/MYD03` (geolocalización a 1 km) y
`calculate_vrp` la recibe como `geo_path` y la ignora (`process_modis.py:513`: «accepted for API compatibility
but not used»). Hallazgo H11.

### 1.4 ¿Lo que MODIS hace es coherente con lo que el detector K dice que hace?

**CONFIRMADA en lo principal, con tres matices menores.** Flags efectivos: `ENABLE_TEST1_PATH = False` (el Test 1
integrado no corre, `process_modis.py:788`), `ENABLE_TESTS_23_PROSE_BRANCH = True` (se pasa como
`use_prose_branch` a `first_pass_tests_2_and_3` `:942` y a `second_pass_adjacent` `:996`; en
`detection_context.py:525` eso es `combinar = max`), `ENABLE_MODIS_B22_PRIMARY = True` (§1.1), `ENABLE_BT_PATH_HOT
= False` (`:711-712` vacía el camino de BT), `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True` (`:944` reemplaza la máscara
combinada por la del primer pase). Umbrales nocturnos K1 = −0,8, C1 = 0,003 / 0,01, C2 = 5 / 10: iguales a la
Tabla 1 del paper (p. 7, renderizada). Nada de lo que afirmo aquí viene del código de VIIRS 750 de MIROVA.

Matices:

- H6: `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA = False`, así que la radiancia del píxel y del fondo se reconstruye con
  λ = 3,929 (B21) a partir de temperaturas que vienen de B22 (3,959). Medido con Planck del repo
  (`06_lambda_y_test1_k1.txt`): el ΔL sale 0,950 a 0,970 del medido (T_hot 300 a 400 K, fondo 265 a 275 K), o
  sea **VRP 3 a 5 % bajo** en todo MODIS. El repo lo sabe (S157, flag apagado por A45); lo dejo como número.
- H7: el NTI_app del primer pase se calcula con λ = 3,929 (`process_modis.py:904`) mientras `rad_mir_for_nti`
  es B22. La diferencia de NTI_app es 0,0027 a 0,0044 (260 a 280 K), del orden de C1. SOSPECHA de que lo
  absorbe la regresión cuadrática NTI contra NTI_app (es un corrimiento casi constante del eje x); no lo medí.
- H5: el Test 1 por píxel (`nti > −0,8`, `:713-719`) se calcula pero, con el primer pase encendido, no entra a la
  máscara (`:944` descarta `combine_hot_paths`). En el paper (p. 6) un píxel que pasa el Test 1 queda «flagged
  as active». Sustrato hoy: 15 records MODIS con `diag_n_nti_path > 0`, y en los 15 el contextual también
  alertó (0 perdidos). Es un defecto latente para el interior de un campo de lava (vecinos igual de calientes,
  contraste ~0); en Chile no tiene casos.

### 1.5 store.py entero

| mecanismo | veredicto | evidencia |
|---|---|---|
| deduplicación por `(datetime_utc, sensor)` (`store.py:650-654`) | **CONFIRMADA** | 0 claves repetidas en los 45 archivos (`01_store_sustrato.txt`) |
| rechazo diurno (`_reject_daytime`, `:203-224`, `:636-645`) | **CONFIRMADA** | 0 de 74.811 records darían rechazo hoy con los dos flags OFF; control positivo: Villarrica 18:00 UTC elev +54,7° rechaza, 05:00 UTC elev −42,5° no |
| reemplazo NRT → Standard (`:682-691`) | **CONFIRMADA** | 142 records `nrt`, todos de los últimos 4 días (`01b`): el canal consolida solo |
| filtro de píxeles por distancia (`_filter_pixels_by_distance`, `:259-311`) | **CON MATIZ** | 0 píxeles fuera de `radius_km` en los 11 Tier A; en 32 Tier B hay 1 a 59 píxeles por volcán fuera de 5 km sin `discarded_reason` (H9); y el filtro escribe `vrp_mir_mw` pero no recalcula `vrp_mw` en MODIS y VIIRS 750 (H8) |
| pisos de magnitud (`_apply_vrp_floor`, `:97-137`) | **CONFIRMADA inerte** | los tres pisos valen 0,0 en el perfil; 1 record viejo con `diag_vrp_floor_mw` |
| cap de cordura (`_apply_sanity_cap`, `:140-185`) | **REFUTADA para VIIRS 375** | H3: se aplica en `:551` antes de la normalización `t_max_i04_k → t_max_k` de `:556-557`; `process_viirs.py` no devuelve `t_max_k` (grep vacío), así que los 29.985 records de I-band llegan al cap con `t_max = None` y `bt_imposible = True`. Control: un record con sólo `t_max_i04_k = 420` y 60 GW sale con `vrp_mw = 0` y `discarded_reason = sanity_cap_pc_garbage`; el mismo con `t_max_k = 420` sale 60 GW y marcado |
| rescate de cúmulo F47 (`:378-422`) y guard A46 (`:514-520`) | **SIN DATO** | 0 records con `final_hotspot_source == cluster_rescue` y 0 con `diag_a46_relabel` en todo el corpus: los dos caminos están escritos pero hoy no tienen sustrato que los ejercite |
| regla D vent (`:479-488`) | **SIN DATO en vivo** | `ENABLE_VENT_PATH_MODIS = False` hoy; en el corpus quedan 36 records MODIS con `vrp_vent_mw > 0` (`08_modis_vent.txt`), heredados de cuando el camino estaba encendido; no los dato ni los sigo |
| reproceso sin `--overwrite` sobre clave existente (`:686-692`) | **CONFIRMADA por lectura** | si la clave existe y no es upgrade, no se guarda nada y no se imprime nada (H12, diseño) |
| `first_processed_utc` (`:664-671`) | **CONFIRMADA** | 9.800 records lo traen (desde S150); se hereda en el reemplazo |

### 1.6 Las tres vistas: ¿se replica hoy un cambio de display en las tres?

**CONFIRMADA en el efecto, no en el texto.** Las copias NO son textualmente iguales, pero ejecutadas con node
sobre los 74.811 records (`05_tres_vistas.txt`) dan el mismo valor de gráfico en todos: 0 records con
`index_chart != diario_chart` (45 volcanes), 0 con `index_chart != mosaico_chart` y 0 con `diario_chart !=
mosaico_chart` (11 Tier A), y 0 diferencias en el predicado de tarjeta entre index y mosaico. La única
discrepancia es de otra naturaleza: 2 records de PCC (2025-11-17 06:24 VIIRS_NOAA21 y 2026-01-17 04:54
VIIRS_NOAA20) que diario grafica (0,037 y 0,165 MW) y que la tarjeta de index y mosaico no titularía, porque
`isSummitDetection` (`index.html:1613`) los excluye por `vrp_mw == 0 && discarded_reason` y diario no tiene esa
función. Ninguno cae en los últimos 90 días. Control positivo: un record sintético con esa combinación da
3,3 MW en las tres vistas y `false` en las dos tarjetas (el instrumento ve la diferencia cuando existe).

Divergencias latentes que hoy no mueven ningún record (H10), con `archivo:línea`:

1. `innerKm` para los 34 volcanes fuera de Tier A: index usa `v.inner_radius_km ?? 10` (`index.html:2428`) y
   diario `INNER_RADIUS_KM[volcanoName] ?? 5` (`diario.html:265`, tabla de 11 entradas en `:243-247`). Son 34
   volcanes con umbral 10 contra 5; hoy 0 records con el centroide entre 5 y 10 km que pasen el resto de
   compuertas.
2. `_mirova_confirmed` sólo lo puebla index (`enrichWithMirovaConfirmation`, `index.html:1544`); en diario y
   mosaico el filtro de cirrus y campo difuso (`diario.html:378`, `mosaico.html:363`) opera sin ese cinturón.
   Hoy 0 records confirmados por MIROVA que caigan en ese criterio.
3. Records sin `primary_cluster` (legacy): index y mosaico aplican el tope de 50 GW al `vrp_mw` de respaldo
   (`index.html:1171`, `mosaico.html:259`); diario no (`diario.html:259`), y además diario aplica la compuerta
   de `distance_class` antes del respaldo. Hoy 0 records sin `primary_cluster` (`04`: «sin pc: 0» en todos los
   estratos).
4. `mosaico.eqVrpDisplay` (`:398-401`) no llama a `isValidDetection`; diario sí (`:438`); index lo aplica en
   `getDisplayVrp` (`:2690`) y en la tarjeta. Hoy da igual porque `isValidDetection` con cúmulo es
   `pc.vrp_mw > 0`, el mismo número que publica `mirovaEqVrp` (medido: 0 diferencias).

Día y noche en el frontend: no hay helper de día/noche en ninguna de las tres vistas; el corte lo hace el
pipeline (`store.py`) y el frontend sólo marca las alertas diurnas de MIROVA con `mirovaEsDia`
(`index.html:1074`) y las filas `dia` de `data/mirova/<volcán>.json`. No hay nada que comparar ahí.

---

## 2. Hallazgos, de mayor a menor gravedad

### H1. La geolocalización MODIS corre cada píxel hacia el nadir (0,5 km en el nadir, 1 a 2 km a 20 a 55°, más en el borde)
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:385-396` (`_interp_geo`, `zoom` sin desfase) y `:292-293` (uso);
  `:513` (MOD03 ignorado). Convención del producto: `MODIS_L1B_DataDictionary_C7.pdf` p. impresa 100.
- QUÉ PASA: la grilla de 5 km de MOD021KM está centrada en el píxel 2 de cada bloque; `zoom` la estira como si
  partiera en el píxel 0. A cada píxel se le asigna la posición de otro píxel, 2 muestras más hacia el nadir
  en un borde, 0,5 en el nadir, 1 en el otro borde, y ±2 líneas en los extremos del gránulo. Distancias al
  cráter, máscara summit/scene, anillo de fondo, `centroid_dist_km`, `distance_class` y el mapa heredan el error.
- CÓMO SE VE EN EL DASHBOARD: el punto MODIS cae sistemáticamente al lado del cráter que mira al satélite;
  en pasadas oblicuas un cúmulo del cráter puede quedar fuera del inner (gris o invisible) y, al revés, un
  píxel del flanco puede entrar al inner y recibir el umbral más sensible (5σ, C1 0,003).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/m2/02_interp_geo_sintetico.py` (error por columna) y
  `python experiments/_s158_audit_r2/m2/03_firma_geo_en_records.py` (firma en Láscar, n = 336 MODIS). Con un
  gránulo a mano: comparar `data["lat"]` de `read_modis_l1b` contra `Latitude` del MOD03 del mismo minuto.
- CONFIANZA: CONFIRMADO (lectura del código, prueba sintética sobre la función real, firma en los records con
  dos controles negativos y uno de instrumento).
- GRAVEDAD: 4.

### H2. MODIS detecta el cráter y publica VRP 0: el fondo es la mediana del anillo de 5 a 25 km y el exceso se recorta a cero
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:1083` (fondo global), `:1118` (recorte), `:582` (anillo),
  `detection_context.py:1083` (mediana). Paper: `sp426.5.pdf` p. 8, Ec. 6 («arithmetic mean of all the pixels
  surrounding the active one»).
- QUÉ PASA: en los 6 Tier A sin `local_kernel_bg` el fondo del VRP no es el entorno del píxel sino el anillo
  regional; un cráter más frío que ese anillo da ΔL negativo, se recorta a 0 y el cúmulo queda con `vrp_mw =
  0`. 37 records MODIS (de 619 con píxeles anómalos) tienen cúmulo dentro del inner y VRP 0; 9 coinciden con
  alerta de MIROVA a ±60 min.
- CÓMO SE VE EN EL DASHBOARD: invisible por construcción: `isValidDetection` exige `pc.vrp_mw > 0`
  (`index.html:1603`), así que esas 37 noches no aparecen en gráfico, tarjeta ni contadores. El operador ve
  «sin detección MODIS» donde el detector sí marcó el cráter.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/m2/04_modis_deteccion_sin_magnitud.py`; caso: Láscar
  2025-02-28 06:45 UTC MODIS_AQUA (`t_max_k` 284,59, `t_bg_k` 270,05, 2 px, VRP 0).
- CONFIANZA: CONFIRMADO (código y conteo). Que la causa del cero sea exactamente el fondo regional y no el
  recálculo focal (`cluster_focal_vrp_mw`, `:1218-1222`) es SOSPECHA fuerte: ambos caminos terminan en el mismo
  `np.maximum(..., 0)` y los 37 casos están en volcanes sin kernel local.
- GRAVEDAD: 3.

### H3. El cap de cordura anula cualquier VIIRS 375 sobre 50 GW sin mirar la temperatura, porque corre antes de que exista `t_max_k`
- ARCHIVO:LÍNEA: `pipeline/store.py:551` (cap) contra `:556-557` (normalización `t_max_i04_k → t_max_k`);
  `:165-166` (`bt_imposible = t_max is None or ...`).
- QUÉ PASA: la discriminación por causa que el docstring promete (`:150-155`) nunca llega a VIIRS 375: con
  `t_max = None` se toma la rama conservadora y se escribe 0 en `vrp_mw` y en `pc.vrp_mw`. Es el escenario
  raro pero peor: la erupción más grande posible se publica como noche tranquila.
- CÓMO SE VE EN EL DASHBOARD: invisible (VRP 0, `discarded_reason = sanity_cap_pc_garbage`). Hoy 0 records lo
  muestran porque ningún VIIRS 375 del corpus superó 50 GW.
- CÓMO REPRODUCIRLO: control positivo del `01_store_sustrato.py` (último bloque): record con sólo
  `t_max_i04_k = 420` y 60 GW sale en 0,0.
- CONFIANZA: CONFIRMADO (código y prueba unitaria sobre la función real).
- GRAVEDAD: 3 (frecuencia mínima, consecuencia máxima).

### H4. Un píxel MODIS saturado en B22 y B21 desaparece; el paper lo conserva como saturado
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:251-258` (NaN para DN > 32767 sin excepción), `:607-608` (NaN para
  BT > 500 K). Paper p. 3 («with the exception of the pixels with DN = 65 533»).
- QUÉ PASA: el núcleo de una erupción grande (ambas bandas saturadas) sale de la escena: no se cuenta, no suma
  magnitud, no fija `t_max`, y sus vecinos pierden un vecino en la media de 8.
- CÓMO SE VE EN EL DASHBOARD: magnitud y extensión subestimadas en el peor momento; hoy sin caso.
- CÓMO REPRODUCIRLO: requiere un gránulo con 65533 en B21; no hay ninguno en disco.
- CONFIANZA: CONFIRMADO en el código, SIN DATO en efecto.
- GRAVEDAD: 2.

### H5. Con el primer pase encendido, el Test 1 por píxel de MODIS no alerta por sí solo
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:713-719` (se calcula), `:944` (`hot_mask_2d = fp_hot` lo descarta),
  `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`. Paper p. 6, Test 1.
- QUÉ PASA: un píxel con NTI > K1 sólo se publica si además pasa Tests 2 y 3; en el interior de un campo
  caliente extenso el contraste local es ~0 y el píxel se pierde.
- CÓMO SE VE EN EL DASHBOARD: hoy en nada: 15 records MODIS con píxeles sobre K1, y los 15 con alerta
  contextual (`06_lambda_y_test1_k1.txt`).
- CONFIANZA: CONFIRMADO en el código, sin sustrato en Chile.
- GRAVEDAD: 2.

### H6. VRP MODIS 3 a 5 % bajo por λ = 3,929 sobre temperaturas de B22
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:600-601` con `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA = False`; `:1083`,
  `:1088`.
- QUÉ PASA: ΔL reconstruido / ΔL medido = 0,950 (300 K sobre 270 K) a 0,970 (400 K). Se multiplica por k =
  18,9 y por el área, así que el VRP baja en la misma proporción.
- CÓMO SE VE EN EL DASHBOARD: todo MODIS un 3 a 5 % más bajo. Ya está documentado como flag apagado (S157).
- CONFIANZA: CONFIRMADO (Planck del repo). GRAVEDAD: 1.

### H7. NTI_app del primer pase con λ de B21 mientras la radiancia es de B22
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:901-906`. Diferencia 0,0027 a 0,0044 en NTI_app (260 a 280 K),
  comparable a C1 = 0,003. SOSPECHA de que la regresión cuadrática la absorbe. GRAVEDAD: 1.

### H8. El filtro por distancia no recalcula `vrp_mw` en MODIS ni en VIIRS 750
- ARCHIVO:LÍNEA: `pipeline/store.py:300-302` escribe `vrp_mir_mw`; `:357-358` sólo copia a `vrp_mw` si no
  existe, y MODIS y VIIRS 750 ya lo traen. `07_filtro_distancia_vrp_mw.txt`: 5 MODIS y 19 VIIRS 750 con
  `partial_eruption_hotspot_too_far` tienen `vrp_mw > vrp_mir_mw` (Copahue 2025-11-18 06:45 MODIS_AQUA: 10,25
  contra 5,27). Invisible: el tablero publica `pc.vrp_mw`, no `vrp_mw`. GRAVEDAD: 1. (313 VIIRS 375 muestran la
  misma desigualdad por otra vía que no identifiqué: SIN DATO sobre la causa.)

### H9. 32 volcanes Tier B tienen píxeles fuera de su geofence de 5 km sin marca de descarte
- `01_store_sustrato.txt`: de 1 (Hudson) a 59 (Laguna del Maule) píxeles por volcán con `dist_km > 5`, en records
  sin `processed_utc` ni `regimen` (anteriores a S132) y con `discarded_reason = None`. El filtro de `store.py`
  no los tocó; no sé si porque corrió con otro flag o por otro script. Fuera del cron NRT. SIN DATO en causa.
  GRAVEDAD: 1.

### H10. Divergencias latentes entre las tres vistas (0 records afectados hoy)
- Las cuatro de §1.6 con sus líneas. No cambian ningún record medido; se separan en silencio el día que
  alguien edite una sola copia. GRAVEDAD: 1.

### H11. MOD03/MYD03 se descarga y se ignora
- `scripts/run_pipeline.py:224-229` lo empareja por minuto; `process_modis.py:513` lo descarta. Es ancho de
  banda perdido en cada corrida y es la corrección de H1 ya en el disco. GRAVEDAD: 1.

### H12. Un reproceso sobre una clave existente sin `--overwrite` se descarta en silencio
- `pipeline/store.py:686-692`: si la clave existe y no es upgrade NRT → Standard, no se guarda y no se avisa.
  Diseño; sólo importa cuando se cambia el detector y se reprocesa sin `--overwrite`. GRAVEDAD: 1.

---

## 3. VERIFICADO LIMPIO

| qué miré | está sano | comando |
|---|---|---|
| Claves `(datetime_utc, sensor)` únicas en los 45 JSON | 0 duplicados | `python experiments/_s158_audit_r2/m2/01_store_sustrato.py` |
| Ningún record diurno almacenado (74.811, los dos flags OFF) | 0 | ídem |
| Canal NRT → Standard | 142 `nrt`, edad máxima 4 días | `01b_nrt_edad_y_tierB.txt` |
| Geofence de 25 km en los 11 Tier A | 0 píxeles fuera | `01_store_sustrato.py` |
| Pisos de magnitud | 0,0 los tres en el perfil (inerte) | `flags_efectivos_mirova_equivalent.txt` |
| Banda primaria MODIS y regla de saturación B22 → B21 | como el paper p. 3 | lectura `process_modis.py:251-258, 338-339, 593-597` |
| Umbrales nocturnos MODIS K1, C1, C2 contra Tabla 1 del paper | iguales | `flags_efectivos_mirova_equivalent.txt`; `paper_pages/sp426_p7.png` |
| Flags de K en MODIS (Test 1 integrado OFF, `max`, B22) | cableados a las funciones que deciden | `process_modis.py:788, 942, 996, 593` |
| Posición de VIIRS 375 y 750 respecto del cráter (control de H1) | sin sesgo hacia el nadir en ningún estrato de cenit | `03_firma_geo_en_records.py` |
| Gráfico y tabla: index contra diario contra mosaico sobre 74.811 records | 0 valores distintos | `node experiments/_s158_audit_r2/m2/05_tres_vistas.js` |
| Predicado de tarjeta index contra mosaico (11 Tier A) | 0 diferencias | ídem |
| `isValidDetection`, cuerpo textual igual en las tres vistas | sí (`index.html:1595`, `diario.html:425`, `mosaico.html:407`) | lectura |
| Día y noche en MODIS: fetch, procesador y store usan la misma `_solar_elevation` | sí (`fetch.py:1014`, `process_modis.py:435`, `store.py:640`) | lectura |

## 4. Fuera de alcance (anotado, no auditado)

- El mismo cero de magnitud de H2 en VIIRS 750 (600 de 2.733 detecciones con `pc.vrp_mw == 0`, 568 antes de K y
  32 con K; Isluga 193, Tupungatito 202, Láscar 95) y en VIIRS 375 (278 de 9.690; Tupungatito 139). Si el
  fondo de esos procesadores es también un anillo regional, aplica lo mismo; no lo leí.
- El código de MIROVA para VIIRS 750 (`MIROVA_VIIRS750_VRP.m:61-85`) usa como fondo del VRP una interpolación
  bidimensional bajo una máscara dilatada y no recorta. No lo traslado a MODIS; lo dejo para quien audite
  VIIRS 750.

## 5. Lo que no pude medir

- El efecto de H1 sobre `distance_class` record a record (cuántos `far` serían `summit` y al revés): hace falta
  reprocesar gránulos con la geolocalización de MOD03, y el alcance prohíbe descargar.
- El desfase en líneas de H1 (±2 líneas, hacia el centro del gránulo): la proyección sobre el acimut sólo ve
  el eje de barrido.
- H4 y H3 en efecto real: no hay gránulo saturado en disco ni record VIIRS 375 sobre 50 GW.
- La causa de las 313 desigualdades `vrp_mw > vrp_mir_mw` en VIIRS 375 (H8) y de los píxeles fuera de geofence
  en Tier B (H9): records sin sello de proceso, sin forma de saber con qué código se escribieron.
- Si H7 lo absorbe la regresión: habría que correr el primer pase con las dos λ sobre un gránulo.
- `cluster_rescue` y el guard A46 en vivo: 0 records con sustrato en el corpus.
