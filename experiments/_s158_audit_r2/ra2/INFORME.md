# RA2 (S158, segunda ronda): la magnitud contra el OSF v2.5 de MIROVA

Auditor independiente, comparación pareada. Fecha: 2026-10-21. Worktree:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2`.
No leí `docs/AUDIT_S158.md`, `experiments/_s158_audit/`, `experiments/_s158_oraculo_mirova/`, el test del oráculo ni
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`; tampoco el A/B de D25. Las marcas «S158» que CLAUDE.md y `docs/MISSION.md`
me mostraron las traté como afirmaciones a verificar.

Todo lo que sigue sale de scripts de esta carpeta, con su salida cruda al lado (`.txt`):

| script | salida | qué mide |
|---|---|---|
| `01_pareo_osf.py` | `01_pareo_osf.txt`, `pares_osf.csv` | pareo volcán + pasada entre records 2025 y el OSF v2.5 |
| `02_magnitud_pares_osf.py` | `02_magnitud_pares_osf.txt`, `pares_osf_analizados.csv` | afirmaciones 1, 2 (OSF) y 4 |
| `03_identidad_vrp_osf.py` | `03_identidad_vrp_osf.txt` | afirmación 3, identidad VRP del OSF por sensor y cenit |
| `03b_v750_no_cumplen.py`, `03c_maxdist.txt` | `03b_v750_no_cumplen.txt` | qué tienen las filas V750 que no cumplen |
| `04_nrt_cenit.py` | `04_nrt_cenit.txt`, `pares_nrt.csv` | afirmación 2 contra la tabla NRT (`latest_consolidado.csv`) |
| `05_chequeos_extra.txt`, `06_quien_mueve_el_conteo.txt` | | cota física de Npix, control positivo, quién mueve el conteo con el cenit |

## 0. La vara y las fuentes que leí

- `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_VRP.m` l. 61 (`npix = numel(alert)`), l. 83 a 85
  (`L_MIRhot = sum(ZI_M13(alert))`, `L_MIRbk = sum(ZI_M13bk(alert))`, `deltaL = hot - bk`), l. 88 a 91
  (`VRP_MW = deltaL * 1.97e7 * 0.5625 / 1e6`, o sea VRP en W = deltaL × 11.081.250). El fondo (l. 64 a 81) es una
  interpolación 2D (`fillmissing2`) bajo la máscara de alertas dilatada 3, 5 o 7 celdas según npix.
- `MIROVA_VIIRS750_hotspot_detection.m` l. 241 a 248: `alert` es la concatenación de índices de píxel de BOX0, ROI1 y
  ROI2 en dos pasadas más los del umbral absoluto, sin `unique` y sin agrupar en regiones. Los píxeles ya alertados se
  ponen NaN antes de cada pasada (l. 275 a 277), así que en la práctica no hay duplicados.
- Matriz de ejemplo (`Example/VIIRS750_example.mat`, `scipy.io.loadmat`): BOX==1 son 350 celdas (filas 22 a 42,
  columnas 24 a 42) y BOX==2 son 49 celdas (7 × 7, centradas en 33,33; el máximo de M13 está en 35,33). O sea, la
  **cumbre es BOX==2** (la pequeña, con σ × 5 y mínimos 0,003 de noche, l. 181 a 187) y el comentario de l. 111 a 118
  la rotula al revés. No es parte de mi alcance, lo anoto porque el brief lo pedía comprobar.
- Nuestra fórmula por píxel: `pipeline/process_viirs.py:1504-1507` (I-band) y `process_viirs_mod.py:1055-1057`
  (M-band): `vrp_i = A × WOOSTER × max(L_i − L_bg, 0) / 1e6`, con A nadir fijo (`ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS`
  y `_MODIS` = True leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`), WOOSTER 18,0 / 19,7 / 18,9
  (`process_viirs.py:77`, `process_viirs_mod.py:66`). El fondo de I-band es el anillo (`t_bg_i04`) o el kernel
  local cuando `ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible` (`process_viirs.py:1471-1483`); en el record
  queda `diag_L_bg_w_m2_sr_um` (anillo) y `diag_L_bg_local_w_m2_sr_um` (local, sólo cuando actúa).
- MODIS: con `ENABLE_MODIS_MIR_LAMBDA_POR_BANDA = False` la radiancia se calcula con `BAND21_LAMBDA = 3.929` en todos
  los píxeles aunque la banda 22 sea primaria (`process_modis.py:364,382`). Lo usé para reconstruir L_i desde `bt_k`.
- OSF v2.5: `VRP_GLOBAL_ARCHIVE_2025.csv`, 615.470 filas, 2000-02-24 a 2025-12-31, fechas `dd/mm/YYYY`, archivo
  **UTF-8** (con latin-1 se pierden Láscar, Chaitén, Chillán, Planchón-Peteroa y Puyehue, 1.764 filas de 2025; me pasó y
  lo corregí, ver `01_pareo_osf.py`). Satellite 1 = Terra, 2 = Aqua, 3 = Suomi NPP, 4 = NOAA-20: deducido del
  pareo por hora de gránulo (matriz en `01_pareo_osf.txt`), no supuesto. NOAA-21 no está en el OSF. Tupungatito no
  está en el OSF.
- Convención de sensores comprobada con `Counter` (`01_pareo_osf.txt`): `VIIRS_SNPP` / `VIIRS_NOAA20` / `VIIRS_NOAA21`
  sin sufijo son I-band (375), con `_750` son M-band, `MODIS_AQUA` / `MODIS_TERRA` son MODIS.
- Tabla NRT: `pipeline/mirova_csv_loader.py:70-81` mapea `VIIRS` a 750 m y `VIIRS375` a 375 m. `scripts/calidad_referencia_mirova.py`
  (A119) avisado para la ventana 2026-04-01 a 2026-10-20: sólo la tabla decide; el OCR no se usó.

### Pareo (denominadores)

OSF 2025, 10 volcanes Tier A presentes: 2.934 filas, 2.880 nocturnas. Records nuestros 2025 en esos 10 volcanes:
34.440. Tolerancia declarada: |dt| ≤ 10 min, vecino más cercano de la misma plataforma y resolución. Resultado:
**2.523 pares, todos con dt = 0 min exacto** (la hora del OSF es la hora de inicio del gránulo); las 411 filas OSF sin
par (14,0 %) tienen el record nuestro más cercano a 30 min o más (402) o a −30 o menos (9): no es tolerancia, es que
no tenemos esa pasada (hallazgo H4). Pares por familia: V375 2.218, MODIS 260, V750 45. Pares con detección nuestra
(`primary_cluster` no nulo y `n_anomalous_pixels > 0`): 2.433 (V375 2.139, MODIS 249, V750 45); en 90 MIROVA alertó y
nosotros no publicamos nada (V375 79, MODIS 11, V750 0). Tabla por volcán en `01_pareo_osf.txt`.

Régimen del detector: los 37.811 records de 2025 de los 11 Tier A fueron procesados desde el 2026-10-18 (0 antes), el
95,7 % con `regimen.codigo_sha = 3695f675` («Reproceso histórico con K», commit del 2026-10-18) y el resto con shas
posteriores; lo mismo los 30.261 de 2026 hasta el 09-17 (95,8 %, 0 antes) (`07_regimen_records.py` →
`07_regimen_records.txt`). Ver H3.

## 1. Veredictos por afirmación

### Afirmación 1. «Con el fondo por píxel de MIROVA del OSF v2.5 sobre nuestros píxeles cambia la razón contra MIROVA en VIIRS 375.»

**VEREDICTO: CONFIRMADA, CON MATIZ (cambia, en los dos sentidos, y sólo explica una fracción menor de la brecha).**

Lectura A (la que declaro principal): tomo nuestros píxeles listados en `anomaly_pixels` (L_i = Planck(bt_k, 3,74 µm)),
sustituyo nuestro fondo por el fondo medio por píxel de MIROVA en la misma pasada, bk_M = Tot_Lmir_bk / Npix, y
recomputo VRP' = Σ A k max(L_i − bk_M, 0) / 1e6. Razón contra MIROVA (mediana, p25, p75), V375, n = 2.139 pares 2025
nocturnos (`02_magnitud_pares_osf.txt`):

| | antes (nuestro fondo) | después (bk_M) |
|---|---|---|
| V375 global | 0,830 (0,564; 1,233) | 0,885 (0,647; 1,215) |
| Isluga (n 474, fondo anillo) | 0,585 | 0,871 |
| Copahue (n 55, anillo) | 0,641 | 1,018 |
| Láscar (n 511, anillo) | 0,671 | 0,738 |
| Chaitén (n 74, kernel local) | 1,177 | 1,010 |
| Lastarria (n 383, local) | 1,384 | 1,242 |
| Villarrica (n 24, local) | 1,233 | 1,117 |
| Planchón-Peteroa (n 217, local) | 0,963 | 0,888 |
| Puyehue (n 330, local) | 0,923 | 0,840 |

En 1.095 de 2.139 pares la razón cambia más de 10 %. Sólo 54 de 4.937 píxeles quedan recortados a 0 con bk_M.
Control positivo: con nuestro fondo × 1,2 la magnitud baja en 1.352 de 1.352 pares de fondo de anillo (en los de kernel
local el control no aplica, porque 1,2 × anillo puede quedar bajo el fondo local; 27 de las 29 excepciones son eso,
`05_chequeos_extra.txt`).

Lectura B (comparar los fondos directamente, `02_magnitud_pares_osf.txt`, lectura B): el fondo nuestro implícito en
la lista (L_i − vrp_i·1e6/(A k)) vale, en mediana, **1,033 × bk_M** en V375 (p25 0,951, p75 1,175), pero el agregado
esconde dos poblaciones: en los cinco volcanes con kernel local (Chaitén 0,966, Lastarria 0,954, PP 0,958, PCC 0,977,
Villarrica 0,933) el fondo coincide con el de MIROVA dentro de ±5 %, y en los de anillo (Isluga 1,192, Láscar 1,163,
Copahue 1,068; Llaima 0,953 y Chillán 0,889 son anillo pero con n chico) nuestro anillo es 7 a 19 % más caliente que
el fondo interpolado de MIROVA. Traducido a MW sobre nuestros n píxeles, la diferencia de fondo explica una mediana del
**12 % de la brecha** VRP_M − VRP_ours en V375 (n = 1.349 pares con brecha positiva), 46 % en MODIS (n 215) y 11,5 % en
V750 (n 34). El resto de la brecha es de conteo (afirmación 2 y 4): nuestra radiancia media del píxel alertado es
1,118 × la de MIROVA y nuestro ΔL medio por píxel 0,0559 contra 0,0462 (más alto, no más bajo).

Por qué físico: el anillo de 5 a 25 km mide el valle y la ladera baja, que de noche están más tibios que la cumbre;
MIROVA interpola el fondo desde los vecinos inmediatos de la anomalía (`fillmissing2` bajo el halo), que en Isluga y
Láscar son cumbre fría. El kernel local nuestro hace lo mismo que MIROVA y por eso coincide. Esta parte es
TRASLADADA: el `.m` describe el fondo de VIIRS 750; que MIROVA haga lo mismo en 375 lo infiero del dato (los fondos
coinciden en los volcanes con kernel), no de un código.

### Afirmación 2. «La razón de magnitud contra MIROVA cae con el cenit, y la caída es de conteo de píxeles.»

**VEREDICTO: CONFIRMADA para VIIRS 375 y MODIS contra el OSF, con la precisión de que es NUESTRO conteo el que cae
con el cenit, no el de MIROVA; SIN DATO suficiente para VIIRS 750 (n 45, y lo poco que hay apunta al factor de
magnitud por píxel, no al conteo); CONFIRMADA la caída contra la tabla NRT en los tres sensores, sin descomposición
posible allí.**

Contra el OSF (`02_magnitud_pares_osf.txt`, afirmación 2; razón de escena r = `vrp_mw` / VRP_M = f_n × f_dL con
f_n = n_anomalous_pixels / Npix y f_dL = ΔL medio por píxel nuestro / ΔL medio por píxel de MIROVA):

| V375, cenit nuestro | n | r escena | f_n | f_dL | r publicada |
|---|---|---|---|---|---|
| 0 a 20 | 531 | 1,023 | 1,000 | 1,257 | 0,833 |
| 20 a 30 | 278 | 0,899 | 0,750 | 1,293 | 0,720 |
| 30 a 40 | 321 | 0,787 | 0,667 | 1,276 | 0,635 |
| 40 a 50 | 382 | 0,691 | 0,600 | 1,235 | 0,597 |
| 50 a 60 | 390 | 0,688 | 0,500 | 1,259 | 0,537 |
| 60 a 70 | 237 | 0,618 | 0,500 | 1,250 | 0,599 |

Spearman con el cenit: r −0,331, **f_n −0,298, f_dL −0,025**. Pendiente de log(·) sobre log(sec z): r −0,71, f_n −0,66,
f_dL −0,03. MODIS (n 249): r 0,76 → 0,33 entre nadir y 40 a 50; f_n −0,42, f_dL −0,04. Por volcán (V375, n ≥ 15),
f_n negativa en 9 de 10 (PP −0,06 apenas; Villarrica +0,25 con n 24 y ninguna pasada sobre 50) y f_dL sin signo
fijo (entre −0,47 en Villarrica y +0,32 en Puyehue, cerca de 0 en los demás): el factor que carga la pendiente es el
conteo en todos los volcanes con muestra.

Quién mueve el conteo (`06_quien_mueve_el_conteo.txt`): Npix de MIROVA es plano con el cenit (mediana 3 en los tres
tramos, Spearman +0,08) y **n_anomalous_pixels nuestro cae** (media 2,78 → 2,46 → 1,92; Spearman −0,24; negativa en los
seis volcanes con n ≥ 60, de −0,09 en PP a −0,62 en Lastarria). El ΔL por píxel es parecido en los dos lados y baja
parejo (0,059/0,050 a nadir, 0,044/0,037 sobre 50). Interpretación física (SOSPECHA, no medida acá): sin remuestreo
(`ENABLE_UTM_REGRID = False`) nuestro píxel nativo crece en el suelo con el ángulo, la fuente sub-píxel se diluye y
menos vecinos pasan el test contextual; MIROVA remuestrea a una grilla fija y su conteo no depende del ángulo.

V750 contra el OSF: n 45 (8 sobre 50 grados); f_n Spearman +0,03, f_dL −0,34: con lo que hay, la poca pendiente está
en el ΔL por píxel. No alcanza para un veredicto.

Contra la tabla NRT (`04_nrt_cenit.txt`; ventana 2026-04-01 a 2026-10-20, 1.284 alertas de la tabla con VRP > 0,
1.254 pareadas a dt ≤ 1 min, 1.128 con detección nuestra), razón publicada (`f5_core_vrp_mw` si existe en V375, si no
`primary_cluster.vrp_mw`) / VRP de la tabla:

| sensor | n | r pub mediana | z < 20 | z ≥ 60 | Spearman r pub vs cenit |
|---|---|---|---|---|---|
| V375 | 897 | 0,66 | 0,796 (239) | 0,524 (74) | −0,226 |
| V750 | 176 | 0,50 | 0,619 (64) | 0,111 (6) | −0,284 |
| MODIS | 55 | 0,57 | 0,747 (29) | 0,076 (1) | −0,515 |

Por volcán V375: Spearman negativo en Isluga (−0,47, n 189), Tupungatito (−0,47, n 105), Chillán (−0,46), Láscar
(−0,35), Chaitén (−0,38); cerca de 0 en Lastarria (−0,02, n 126), PP (+0,10, n 79), PCC (−0,16, n 138). Regímenes:
los records anteriores al 2026-09-18 son sha 3695f675 (reproceso histórico con K) y los posteriores 34cea39e
(adopción de K): los dos son K, no hay régimen anterior en los datos (H3); la pendiente aparece en los dos tramos
(V375: −0,21 con n 755 y −0,33 con n 142).

### Afirmación 3. «Sobre 50 grados de cenit el VRP de VIIRS 750 del OSF v2.5 no cumple la fórmula del código en una parte de las filas.»

**VEREDICTO: CONFIRMADA, con el número: 24,1 % de las filas VIIRS 750 sobre 50 grados (8.239 de 34.250) no cumple
VRP = (Tot_Lmir_hot − Tot_Lmir_bk) × 11.081.250; bajo 50,0 grados cumple el 100 % (66.391 filas). MODIS y VIIRS 375
cumplen el 100 % a cualquier cenit.** (`03_identidad_vrp_osf.txt`.)

- Unidad y constante, deducidas del dato: VRP está en **W**; k = VRP/ΔL tiene mediana exacta 11.081.250 en V750 (=
  1,97e7 × 0,5625 del `.m` l. 88 a 91, razón dato/código 1,000000), 2.531.250 en V375 (= 18,0 × 140.625 m²) y
  18.900.000 en MODIS (= 18,9 × 1e6 m²). Las tres son WOOSTER × área nadir de nuestro pipeline.
- Tolerancia: |VRP/(ΔL k) − 1| ≤ 1e-3 (redondeo a 9 cifras del CSV); el resultado es idéntico al 1 %, o sea no es
  redondeo. Control positivo: una fila con VRP × 1,10 cae fuera (impreso).
- Por tramo (V750, fracción que cumple): [50,55) 0,684 (n 8.753), [55,60) 0,740 (9.019), [60,65) 0,789 (9.029),
  [65,70) 0,836 (7.449). Cenit mínimo de una fila que no cumple: 50,013; máximo de una que cumple: 69,993. Global V750:
  91,8 % (año 2025: 92,6 % de 8.071).
- Qué tienen las que no cumplen (`03b_v750_no_cumplen.txt`): el VRP es siempre **menor** que la fórmula (razón 0,03 a
  0,95, mediana 0,51); nunca ocurre con Npix ≤ 3 (0 de 619) y sube con Npix (4 % con 4 a 5, 31 % con 11 a 30, 82 % con
  más de 30) y con el brillo del píxel (hot/Npix mediana 2,92 contra 0,56 en las que cumplen; razón mediana 0,63 con
  hot/Npix de 1 a 2 y 0,26 sobre 10); de día 20 % y de noche 5,6 %; los dos satélites por igual (8,3 % y 8,0 %).
- Qué NO la explica: la razón no es función del ángulo (Spearman con SatZen +0,13; razón/sec z, /sec² y /sec³ se
  dispersan 2 a 4× entre p5 y p95), ni del acimut (signo de SatAzi 23 % contra 25 %), ni del año (5 a 13 % todos los
  años 2012 a 2025). Npix × razón no cae en enteros más que el azar (4,1 %).
- Otra fórmula candidata (SOSPECHA, no identificable con las columnas agregadas): el VRP de esas filas corresponde a
  un **subconjunto de los píxeles** alertados (el fondo implícito hot − VRP/k es siempre mayor que Tot_Lmir_bk, mínimo
  1,09×, lo que un factor de área no produce), y el subconjunto se activa sólo sobre 50 grados, en detecciones grandes
  y brillantes. Un mecanismo compatible es la supresión de celdas duplicadas por el solapamiento de píxeles (bow tie)
  del barrido oblicuo de VIIRS al remuestrear a 750 m, pero no lo puedo probar sin los píxeles. El código publicado
  (`README.txt`, «Scope») se declara incompleto en «quality screening» e «input preparation»: ahí cabe.
- Consecuencia para nosotros: una calibración de k contra el OSF V750 que use medias o regresión sin filtrar el
  cenit mezcla dos fórmulas (8,2 % de las filas); la mediana no se mueve. Y sobre 50 grados el OSF V750 no sirve como
  vara de magnitud fila a fila sin saber cuál de las dos fórmulas aplicó.

### Afirmación 4. «MIROVA cuenta píxeles, no regiones.»

**VEREDICTO: CONFIRMADA para VIIRS 750 por el código, y el OSF se comporta como conteo de píxeles en los tres sensores;
nuestro conteo es MENOR que el de MIROVA, no mayor.**

- Código: `npix = numel(alert)` (`MIROVA_VIIRS750_VRP.m` l. 61); `alert` son índices lineales de píxel (l. 241 a 248
  del detector), sin ninguna etapa de regiones ni conectividad. CONFIRMADO para V750; TRASLADADO para 375 y MODIS.
- OSF: Npix es entero en 615.470 filas (mínimo 1, máximo 3.963); Tot_Lmir_hot/Npix nunca supera la radiancia de
  saturación del sensor (V750: 0 filas sobre L(634 K) = 404; MODIS: 0 sobre L(500 K) = 84; V375: 81 de 252.374 filas,
  0,03 %, apenas sobre L(367 K) = 4,56 con máximo 4,66). Si Npix contara regiones de muchos píxeles, el «hot por
  unidad» superaría la saturación en las erupciones grandes; no pasa. Las temperaturas de saturación son las nominales
  que conozco (SOSPECHA en el valor exacto; la conclusión no depende de ±20 K).
- Docs: `docs/MISSION.md:348-350` dice «Cluster aggregation (S27): alineación con n_hotspots MIROVA via
  scipy.ndimage.label 8-conn» y lleva una marca S158 encima; el glosario de `CLAUDE.md` («Cluster vs pixel (S23 T14,
  hallazgo factor 42)») dice que MIROVA reporta regiones contiguas y que «para 1 cluster MIROVA esperamos 5-50 pixels
  nuestros». Medido con pares reales 2025 (`02_magnitud_pares_osf.txt`, afirmación 4):

| sensor | n pares | n_anom/Npix mediana (p25, p75) | n_anom > Npix | = | < | Npix MIROVA mediana (máx) | n_anom nuestro mediana (máx) |
|---|---|---|---|---|---|---|---|
| V375 | 2.139 | 0,67 (0,50; 1,00) | 354 (16,6 %) | 535 | 1.250 | 3 (19) | 2 (17) |
| MODIS | 249 | 0,50 (0,50; 1,00) | 6 | 77 | 166 | 3 (18) | 1 (6) |
| V750 | 45 | 0,50 (0,43; 0,83) | 4 | 6 | 35 | 5 (15) | 3 (11) |

  Con `primary_cluster.n_pixels` (lo que publica el tablero) la razón es 0,50 en los tres sensores. Por volcán
  (`05_chequeos_extra.txt`, 05d): sólo Lastarria tiene n_anom > Npix en más casos que < (149 contra 118); Láscar 23
  contra 441. El «5 a 50 píxeles nuestros por cluster de MIROVA» no se observa en ningún volcán.

## 2. Hallazgos nuevos (por gravedad, lo peor primero)

### H1. La magnitud publicada cae con el ángulo de observación porque dejamos de contar píxeles que MIROVA sí cuenta
- SCRIPT:SALIDA: `02_magnitud_pares_osf.py` → `02_magnitud_pares_osf.txt` (afirmación 2), `06_quien_mueve_el_conteo.txt`;
  `04_nrt_cenit.txt`.
- QUÉ PASA: de noche, una fuente sub-píxel calienta un número fijo de celdas en la grilla remuestreada de MIROVA
  (Npix mediana 3, plano con el cenit, Spearman +0,08), pero en nuestro gránulo sin remuestrear el píxel oblicuo es
  más grande y la fuente pasa a menos píxeles (n_anomalous_pixels 2,78 → 1,92 de media entre nadir y 50 grados o más,
  Spearman −0,24, negativo en los seis volcanes con n ≥ 60). Como el ΔL por píxel es parecido al de MIROVA (f_dL
  1,25, plano), la razón de escena V375 pasa de 1,02 a nadir a 0,62 sobre 60 grados y la publicada de 0,83 a 0,54.
  Contra la tabla NRT 2026 la caída está en los tres sensores (V375 0,80 → 0,52, V750 0,62 → 0,11 con n 6, MODIS
  0,75 → 0,08 con n 1).
- CÓMO SE VE EN EL DASHBOARD: el mismo volcán muestra la mitad de los MW de MIROVA cuando la pasada es oblicua; una
  serie temporal con pasadas alternadas nadir y borde oscila por geometría, no por el volcán. Para un operador que
  compara con mirovaweb, el déficit es sistemático en Isluga (0,53), Tupungatito (0,36) y Láscar (0,58).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra2/01_pareo_osf.py && python .../02_magnitud_pares_osf.py`;
  mirar la tabla V375 por tramo de cenit. Ejemplo por volcán: Isluga V375, z < 30 r escena 0,77 (n 167), z ≥ 50 0,37
  (n 161).
- CONFIANZA: CONFIRMADO (medición). El mecanismo del remuestreo es SOSPECHA.
- GRAVEDAD: 3. No cambia una detección en alerta, cambia la magnitud que el operador compara entre noches y contra
  MIROVA, hasta un factor 2.

### H2. Sobre 50 grados el OSF VIIRS 750 mezcla dos fórmulas; un cuarto de sus filas no sigue el código publicado
- SCRIPT:SALIDA: `03_identidad_vrp_osf.py` → `03_identidad_vrp_osf.txt`; `03b_v750_no_cumplen.txt`; `03c_maxdist.txt`.
- QUÉ PASA: 8.239 de 34.250 filas V750 con SatZen ≥ 50 (24,1 %) tienen VRP menor que (hot − bk) × 11.081.250, en
  razón 0,03 a 0,95 (mediana 0,51), con frontera exacta en 50,0 grados, nunca con Npix ≤ 3, más frecuente con muchos
  píxeles y píxeles brillantes. MODIS y V375 cumplen al 100 % a todo cenit. Detalle en la afirmación 3.
- CÓMO SE VE EN EL DASHBOARD: invisible. Afecta a quien calibre o audite contra el OSF V750 fila a fila sobre 50
  grados (26 filas chilenas, 10 de PP, 6 de Villarrica, 5 de Chillán).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra2/03_identidad_vrp_osf.py`; filas de ejemplo en el `.txt`
  (p. ej. Chillán 2025-02-27 19:42 UTC, Npix 23, razón 0,246).
- CONFIANZA: CONFIRMADO (medición); la fórmula alternativa es SOSPECHA (subconjunto de píxeles).
- GRAVEDAD: 2.

### H3. El corpus ya no tiene régimen anterior a K: no se puede «separar antes y después» con `data/mirova_equivalent`
- SCRIPT:SALIDA: `07_regimen_records.py` → `07_regimen_records.txt` (campos `regimen.codigo_sha` y `processed_utc` de
  los 11 Tier A, por tramo 2025 / 2026 hasta 09-17 / 2026 desde 09-18); `04_nrt_cenit.txt` «regimen por fecha».
  `git log -1 3695f675`: «Reproceso historico con K ... (S154)», 2026-10-18; `34cea39e`: «Adopcion de K en la
  replica», 2026-10-18.
- QUÉ PASA: los 37.811 records de 2025 y los 30.261 de 2026 hasta el 09-17 (11 Tier A) tienen `processed_utc` del
  2026-10-18 o posterior, 0 anteriores; 95,7 % y 95,8 % llevan el sha del reproceso histórico con K y el resto shas
  de commits posteriores a la adopción de K. Cualquier comparación «pre-K contra K» hecha hoy sobre estos JSON compara K
  contra K (el brief me pedía separarlos; lo hice por fecha y los dos tramos dan la misma pendiente).
- CÓMO SE VE EN EL DASHBOARD: invisible. Afecta a toda auditoría retrospectiva que crea estar midiendo el detector
  anterior.
- CÓMO REPRODUCIRLO: `python -c "import json,collections;r=json.load(open('data/mirova_equivalent/Lascar.json'))['records'];print(collections.Counter(x['regimen']['codigo_sha'][:8] for x in r if x['datetime_utc']<'2026-09-18'))"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (de método; no toca una alerta).

### H4. Un 14 % de las pasadas nocturnas de 2025 que MIROVA sí procesó no existe en nuestros records
- SCRIPT:SALIDA: `01_pareo_osf.txt` («filas OSF sin par por (vol, Resolution)», histograma de dt).
- QUÉ PASA: 411 de 2.934 filas OSF de 2025 (10 volcanes) no tienen ningún record nuestro de la misma plataforma a
  menos de 30 min: Puyehue 84 de 436, Lastarria 59 de 456, Planchón-Peteroa 59 de 295, Láscar 56 de 815, Isluga 41 de
  521, Copahue 42 de 117, Chaitén 24 de 109, Chillán 31 de 109 (22 de sus 42 de V750), Villarrica 12 de 42, Llaima 3
  de 34. Como el OSF sólo lista pasadas
  con alerta, cada una es una alerta de MIROVA que no está en nuestro denominador de recall ni de magnitud.
- CÓMO SE VE EN EL DASHBOARD: huecos en la serie de 2025; el recall retrospectivo contra MIROVA se calcula sobre un
  denominador que no incluye esas noches.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra2/01_pareo_osf.py`.
- CONFIANZA: CONFIRMADO (que falten); la causa (búsqueda en CMR o descarga) no la medí.
- GRAVEDAD: 2.

### H5. En los volcanes sin kernel local nuestro fondo es 7 a 19 % más caliente que el de MIROVA y eso les cuesta de un cuarto a la mitad de la magnitud
- SCRIPT:SALIDA: `02_magnitud_pares_osf.txt`, afirmación 1 lecturas A y B (tabla por volcán).
- QUÉ PASA: el anillo de 5 a 25 km está en el valle tibio; el fondo interpolado de MIROVA bajo la anomalía está en la
  cumbre fría. Isluga: fondo 1,19 × MIROVA, razón 0,585 → 0,871 al sustituirlo; Copahue 1,07, 0,641 → 1,018; Láscar
  1,16, 0,671 → 0,738. En los cinco volcanes con `local_kernel_bg` el fondo ya coincide (0,93 a 0,98) y sustituirlo
  baja la razón 5 a 14 %. Qué volcanes tienen kernel: lo dice el record (`diag_L_bg_local_w_m2_sr_um` no nulo:
  Chaitén, Lastarria, PP, PCC, Villarrica, 1.028 de 2.139 pares), no lo leí de un YAML.
- CÓMO SE VE EN EL DASHBOARD: Isluga y Láscar en V375 publican 0,44 y 0,60 de lo que publica MIROVA (razón publicada
  mediana, n 474 y 511); el fondo explica la mitad del déficit de Isluga y una parte chica del de Láscar (el resto es
  H1).
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra2/02_magnitud_pares_osf.py`, sección «lectura A ... por volcan».
- CONFIANZA: CONFIRMADO (medición); que MIROVA interpole igual en 375 que en 750 es TRASLADADO del `.m`.
- GRAVEDAD: 3.

### H6. Los dos documentos de entrada siguen diciendo que MIROVA cuenta regiones, y el dato dice lo contrario
- ARCHIVO:LÍNEA: `docs/MISSION.md:348-350` (con marca S158 encima en l. 345 a 347); glosario «Cluster vs pixel» del
  `CLAUDE.md` del proyecto (lleva marca S158 pero conserva «esperamos 5-50 pixels nuestros»).
- QUÉ PASA: ver afirmación 4. Nuestro conteo es 0,5 a 0,67 del de MIROVA y lo supera en 16,6 % de los pares V375.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## 3. VERIFICADO LIMPIO

- **Las tres constantes de magnitud están calibradas con el OSF**: k del dato = 2.531.250 / 11.081.250 / 18.900.000 W
  por unidad de radiancia (medianas exactas, 1e-3 de tolerancia, 100 % de las filas de MODIS y V375 y 100 % de V750
  bajo 50 grados), iguales a WOOSTER × área nadir del pipeline (`process_viirs.py:67,77`, `process_viirs_mod.py:55,66`;
  MODIS 18,9 × 1e6). Comando: `python experiments/_s158_audit_r2/ra2/03_identidad_vrp_osf.py`.
- **El área nadir fija es lo que usa MIROVA**: k no depende del cenit en ninguno de los tres sensores (mediana
  idéntica en los 8 tramos, `03_identidad_vrp_osf.txt`, última tabla); nuestros flags `ENABLE_NADIR_FIXED_PIXEL_AREA_*`
  = True y `ENABLE_GEOLOCATED_PIXEL_AREA` = False (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`).
- **El pareo es exacto**: 2.523 pares con dt = 0 min; el mapa de satélites sale del dato (1 Terra, 2 Aqua, 3 SNPP, 4
  NOAA-20); nuestro `sensor_zenith_deg` y el `SatZen` del OSF difieren 0,07 grados en mediana (p95 0,63).
- **La convención de sensores** de los records es la declarada (`Counter` en `01_pareo_osf.txt`).
- **La unidad del OSF es W** y `VRP` nunca es ≤ 0 ni ΔL ≤ 0 (0 de 615.470).
- **Npix del OSF se comporta como conteo de píxeles** (entero, hot/Npix bajo saturación, `05_chequeos_extra.txt`).
- **El pareo contra la tabla NRT**: 1.254 de 1.284 alertas pareadas a ≤ 1 min; las 30 restantes a más de 10 min (sin
  record nuestro).
- **Lo que la lista `anomaly_pixels` reconstruye**: `sum(vrp_mw)` de la lista coincide con `vrp_mw` del record salvo en
  43 de 2.433 (lista truncada a 100 en 224 records, o tope D9); la reconstrucción de L_i desde `bt_k` con las λ del
  pipeline es consistente (fondo implícito mediana 0,0844 contra `diag_L_bg` del record en los de anillo).
- **`VRP_MW` del `.m` está en MW y el OSF en W**, no hay factor 1e6 perdido en ninguno de los dos lados.

## 4. Fuera de alcance (anotado, no medido a fondo)

- **Recall de VIIRS 750 contra la tabla NRT**: 67 de 243 alertas nocturnas de la tabla en la ventana (28 %) no tienen
  detección nuestra (`04_nrt_cenit.txt`); en V375 son 51 de 948 (5 %), en MODIS 8 de 63. Contra el OSF 2025 fueron 0 de
  45 en V750 y 79 de 2.218 en V375.
- **Magnitud VIIRS 750 contra la tabla**: razón publicada mediana 0,50 (n 176; Láscar 0,51 con n 95, Isluga 0,27 con
  n 16, Chillán 0,41 con n 29). Contra el OSF 2025, 0,70 (n 45).
- **El comentario del `.m` rotula al revés la cumbre** (BOX==2 es la caja chica de 7 × 7 con los mínimos de 0,003;
  BOX==1 la grande con 0,02): lo comprobé en la matriz de ejemplo, no en nuestro código.
- **MODIS**: razón de escena 0,65 y publicada 0,51 contra el OSF (n 249, 223 de Láscar), f_n 0,5: contamos la mitad de
  los píxeles. Contra la tabla, 0,57 (n 55).

## 5. Lo que no pude medir

- **La fórmula exacta de las filas V750 del OSF que no cumplen sobre 50 grados**: con cuatro columnas agregadas por
  pasada (Npix, hot, bk, VRP) sólo se descarta un factor de área o de ángulo y se acota a un subconjunto de píxeles;
  identificar el subconjunto pide los píxeles, que el OSF no trae.
- **La descomposición conteo × magnitud por píxel contra la tabla NRT**: la tabla no trae Npix ni radiancias.
- **VIIRS 750 contra el OSF**: 45 pares, 8 sobre 50 grados, 17 de Láscar y 20 de Chillán; cualquier pendiente con el
  cenit queda sin poder. Los pocos VIIRS 750 chilenos del OSF son del dato, no del pareo (78 filas en 2025).
- **El régimen anterior a K**: no existe en `data/mirova_equivalent` (H3). Separé por fecha como control, no como
  régimen.
- **Tupungatito y NOAA-21** no están en el OSF v2.5; quedan sólo en la parte NRT.
- **Las temperaturas de saturación** que usé como cota (367, 634, 500 K) son las nominales que conozco; no las leí de
  un UserGuide en esta sesión. La conclusión de la afirmación 4 aguanta ±20 K.
- **Si MIROVA interpola el fondo igual en VIIRS 375 y MODIS que en el `.m` de 750**: no hay código; lo infiero del dato
  y lo marco TRASLADADO.
