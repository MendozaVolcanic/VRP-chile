# Verificador V3 (S158): hallazgos F3-H1 a F3-H4, F4-H1 y F4-H6

Contexto limpio: no leí los informes de F3 ni de F4 antes de medir (abrí sólo sus scripts y salidas, y después, para
comparar cifras, los pasajes H1, H4 y H6). Cada número sale de un script de esta carpeta, corrido en esta sesión sobre
la rama `s158-d17-diseno` (commit `56ec42c6b`), con `VRP_PROFILE=mirova_equivalent`.

Ventanas: 2026 = 2026-03-01 a 2026-10-21, noche según el pipeline (`es_pasada_diurna_descartada`), 11 Tier A,
referencia NRT = snapshot del repo con `banco_paridad`, regla SN (los avisos de A119 salen en stderr: 8 tramos; MODIS y
la tabla sanos desde marzo). 2025 = OSF v2.5, filas nocturnas 2025, 10 volcanes (no trae Tupungatito), clase 1.

## Tabla

| hallazgo | veredicto | mi gravedad | por qué |
|---|---|---|---|
| F3-H1 (V750 en 0,0 MW por fondo de anillo) | **CONFIRMADO, con matiz de impacto** | 3 | 235 cúmulos de cumbre en 0 MW de 855 records con alertados; el mecanismo es el recorte en el 100 % de los explicables. 55 de 304 pasadas con alerta de MIROVA quedan ocultas, pero **0 noches de volcán** se pierden (otra pasada publica) y el VRP de MIROVA en esas 55 es ≤ 0,60 MW (ninguna protegida). Además oculta 68 negativos limpios: arreglarlo cuesta precisión. |
| F3-H2 (pendiente con el cenit es de conteo) | **CONFIRMADO** | 3 | Reproduce con distancia desde el cráter y estratificando por volcán: los 6 volcanes con ≥ 40 pares tienen pendiente negativa; N_M de MIROVA casi plano dentro de cada volcán; el exceso por píxel no cae. |
| F3-H3 (a nadir pierde la selección) | **CON MATIZ** | 2 | Las cifras 0,949 / 0,831 / 0,898 son de **todos** los cenit, no de nadir; a ≤ 20° dan 0,927 / 0,863 / 0,965. En MODIS y V750 el déficit lo hacen pocas pasadas (80 % y 62 % en las 10 peores). Con distancia al cráter, Cordón Caulle V750 baja a 0,644. |
| F3-H4 (fondo de anillo sobreestima en Copahue, Isluga, Láscar) | **CON MATIZ** | 3 | Las cifras reproducen exactas como **medianas** a ≤ 40°; en sumas Isluga pasa a 1,09 y Copahue a 1,37 (n = 18). «Volcanes altos» no es el criterio: Chillán, también sin kernel, va al revés (fondo de MIROVA 1,17 del nuestro). Láscar casi no se mueve (0,79 a 0,83): ahí el fondo no es la palanca. Misma raíz que F3-H1. |
| F4-H1 (el mínimo de escena decide casi siempre) | **CON MATIZ** | 3 | El título es falso para el pipeline de hoy: con nuestro mínimo de 0,010 la rama estadística queda abajo sólo en 10,0 % (V375), 5,7 % (V750), 7,5 % (MODIS). El 92,8 % vale para un mínimo hipotético de 0,02. El defecto real y medible es en V750: el código dice 0,02 para dNTI fuera de la cumbre y usamos 0,010; en unidades nuestras (0,0225) nuestro umbral de escena queda por debajo del de MIROVA en ~79 % de 10.755 pasadas. Para V375: sin dato de MIROVA, confirmado. |
| F4-H6 («lo estructural se traslada con cita») | **CONFIRMADO, y más fuerte** | 2 | Las dos citas hablan del algoritmo entero. Y para el fondo del VRP la contradicción no es «del otro sensor»: Campus 2022 p. 7, ec. 2, **para VIIRS 750 mismo**, dice media aritmética de los vecinos, y el código de VIIRS 750 interpola bajo un hueco dilatado. |
| **V3-1** (propio) | CONFIRMADO | 2 | El tablero rotula «Distancia al cráter» una distancia medida desde el centroide del volcán: 2,7 km de error en Tupungatito, 7,6 km en Cordón Caulle. |
| **V3-2** (propio) | CONFIRMADO | 2 | Arreglar F3-H1 publicaría energía en 68 pasadas que son negativos limpios de MIROVA: el A/B de un fondo local en V750 tiene que contar las dos caras. |

Duplicados fundidos: F3-H1 y F3-H4 son la misma raíz (fondo escalar del anillo de 5 a 25 km contra un fondo local); en
V375 se ve como magnitud baja, en V750, sin kernel ni recorte compensado, como 0,0 MW y ocultamiento.

---

## F3-H1. VIIRS 750: cúmulos de cumbre en 0,0 MW por el fondo del anillo

- **ARCHIVO:LÍNEA**: `pipeline/process_viirs_mod.py:1041` (`L_bg_rad = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)`,
  fondo escalar), `:1056` (`delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`), `:461-468` (docstring: el kernel local
  para M-band «aún no existe»; `local_kernel_bg_compatible` se acepta y no se usa, `grep` sólo lo encuentra en la firma
  y el docstring); `frontend/index.html:1595` (`isValidDetection`: con cúmulo exige `pc.vrp_mw > 0`). Flags leídos de
  `pipeline.profile`: `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False`. Contra el código de MIROVA:
  `MIROVA_VIIRS750_VRP.m` interpola el fondo con `fillmissing2` tras dilatar el hueco 3/5/7 celdas y resta **sumas**,
  sin recorte por píxel.
- **QUÉ PASA**: en una cumbre nevada de noche el cráter es más frío que la mediana del anillo de 5 a 25 km (valles más
  bajos y tibios). El píxel alertado (que pasó por contraste de NTI, no por temperatura) queda con L_hot < L_bg, el
  recorte lo deja en 0, y si todos los del cúmulo quedan así, el cúmulo vale 0,0 MW. Ejemplo leído: Tupungatito
  2026-10-18 05:42, VIIRS SNPP 750, píxel de cumbre a 0,11 km del cráter con BT 252,47 K contra `t_bg_k` 255,54 K.
- **MEDICIÓN** (`h1_recorte_v750.py` → `h1_recorte_v750.out`). Denominador: 855 records V750 nocturnos con ≥ 1
  alertado, ventana 2026.
  - Control de instrumento: mi `11,08125 × ΔL` reproduce el `vrp_mw` persistido en 752 píxeles con energía (error
    relativo mediana 0,0006, p99 0,016): el fondo que reconstruyo es el del pipeline. Ningún cúmulo en 0 está topado
    por D9.
  - Cúmulo en 0 MW: 238 (235 de cumbre); 235 tienen TODOS sus píxeles con L(bt) ≤ L(t_bg); 3 no se explican así.
  - Por volcán (cúmulo 0 / records): Tupungatito 63/84, Isluga 76/134, Planchón-Peteroa 15/29, Villarrica 5/17,
    Láscar 51/328, Cordón Caulle 23/141, Lastarria 3/35, Chillán 2/54, Llaima, Copahue y Chaitén 0. Coincide con F3
    salvo ±3 por la definición de noche (F3 usó hora UTC 03-09).
  - En los cúmulos 0 de cumbre, `max(BT alertados) − t_bg`: mediana −1,42 K, p10 −3,85, p90 −0,19 (n = 235).
  - Contra MIROVA: de 304 pasadas V750 con alerta de MIROVA y record nuestro con alertados, **55** quedan con cúmulo 0
    (Isluga 18 de 35, Tupungatito 11 de 13, Láscar 11 de 166, Cordón Caulle 7 de 41, Planchón 4 de 5, Villarrica 3 de
    8, Chillán 1 de 33). Esas 55 caen en 53 noches de volcán y **en las 53 hay otra publicación de cumbre** (cualquier
    sensor) esa misma noche: 0 noches perdidas. El VRP de MIROVA en esas 55: mediana 0,240 MW, p90 0,470, máximo
    0,600; 0 alertas protegidas (≥ 1 MW).
  - La otra cara: 68 cúmulos 0 de cumbre son negativos limpios de MIROVA y 112 `sin_info`.
- **CÓMO SE VE EN EL DASHBOARD**: la serie V750 de Tupungatito, Isluga y Planchón-Peteroa muestra pocas detecciones de
  cumbre; las pasadas existen pero no cuentan como detección ni entran al gráfico. La noche sigue alertada por VIIRS 375.
- **CÓMO REPRODUCIRLO**: `python -B experiments/_s158_audit/v3/h1_recorte_v750.py`; caso: Tupungatito, VIIRS_SNPP_750,
  2026-10-18 05:42 UTC.
- **CONFIANZA**: CONFIRMADO el mecanismo y los conteos. SOSPECHA: que el fondo interpolado de MIROVA dé exceso positivo
  en esos mismos píxeles (no tengo el L1B remuestreado); lo apoya que MIROVA publicó VRP > 0 en las 55 y, en V375
  2025, que su fondo por píxel es 0,84 del nuestro en Isluga (F3-H4).
- **GRAVEDAD**: 3, no 4. Ninguna noche de alerta se pierde y las alertas afectadas son débiles; lo que se tuerce es la
  serie y el recall por sensor de VIIRS 750 (55 de 304, 18 %), que es el sensor donde el código es la vara.

## F3-H2. La pendiente de la magnitud V375 con el cenit es de conteo

- **SCRIPT:SALIDA**: `h2_cenit.py` → `h2_cenit.out`, sobre `pares_osf2025_v3.csv`, que re-generé con
  `f3/descomp_osf2025.py` y es idéntico celda a celda al de F3 (2.880 × 32). Control de pareo: |cenit nuestro − cenit
  MIROVA| mediana 0,07°, p95 0,54° en V375. Control positivo del OSF: k·A = 2.531.250 exacto en las 2.568 filas V375.
- **QUÉ PASA**: un mismo foco visto en oblicuo cae en menos píxeles nativos (más grandes); MIROVA remuestrea a una
  grilla fija y lo sigue contando en las mismas celdas. Como nosotros multiplicamos por el área de nadir, la energía
  perdida es proporcional a los píxeles que faltan.
- **MEDICIÓN** (1.652 pares clase 1 con todo MIROVA dentro del inner y lista completa; distancia desde el cráter, no
  desde el centroide):

  | cenit | n | N_M medio | n nuestro medio | Σn/ΣN_M | ΣE/ΣM | exceso por píxel |
  |---|---|---|---|---|---|---|
  | 0-10 | 213 | 2,88 | 2,60 | 0,902 | 0,979 | 1,08 |
  | 30-40 | 256 | 3,40 | 2,21 | 0,649 | 0,716 | 1,10 |
  | 60-75 | 192 | 3,22 | 1,36 | 0,422 | 0,481 | 1,12 |

  Dentro de cada volcán (≥ 40 pares) la razón E/M cae con el cenit en los 6 (Spearman −0,12 Planchón a −0,61 Isluga),
  mientras N_M de MIROVA va de −0,26 a +0,21. Promediando volcanes con igual peso: 1,00 (≤ 20°), 0,83 (20-40°), 0,65
  (> 40°). Medir desde el cráter o desde el centroide cambia 19 pares y nada del resultado.
- **Sobre la contradicción con `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6**: el doc ya lleva una marca de rebaja de F3
  «pendiente del verificador» (l. 282-288). La confirmo: en esta población la pendiente completa es 2×, no el 23 % que
  daba S, y es de conteo.
- **CÓMO SE VE EN EL DASHBOARD**: la misma actividad publica la mitad de magnitud en una pasada oblicua que en una de
  nadir; un salto de VRP entre pasadas puede ser geometría.
- **CONFIANZA**: CONFIRMADO para V375, 2025, clase 1. Lo que no prueba: que el remuestreo D17 sea la causa y no una
  dilución de la señal que hace fallar la detección en píxeles grandes. El exceso por píxel no cae (1,08 a 1,27), lo
  que favorece el remuestreo, pero lo decide el A/B de D17.
- **GRAVEDAD**: 3 (magnitud y tendencia, no detección).

## F3-H3. Selección: lo publicado contra la suma de los alertados dentro del inner

- **SCRIPT:SALIDA**: `h3_seleccion.py` → `h3_seleccion.out`. Ventana 2026, records summit con cúmulo dentro del inner y
  lista completa: MODIS 129, V375 2.278, V750 480 (salen como SIN DATO los que no tienen energía dentro: V750 235, que
  son los de F3-H1).
- **MEDICIÓN**: Σpublicado / ΣE dentro del inner (desde el cráter): MODIS 0,900, V375 0,946, V750 0,821; desde el
  centroide (como F3): 0,900 / 0,953 / 0,834. **A ≤ 20°**: MODIS 0,965 (n = 64), V375 0,927 (589), V750 0,863 (177). La
  razón por pasada es 1 exacta en el 77 % (MODIS), 84 % (V375) y 72 % (V750) de las pasadas. En MODIS el 81 % del
  déficit lo aportan 10 pasadas; en V750 el 62 %. Peores: Cordón Caulle V750 0,644 (con distancia al cráter; 0,715
  desde el centroide), Lastarria V375 0,744, Cordón Caulle V375 0,792, Chillán V750 0,810.
- **Matiz**: el título «a nadir» no corresponde a las cifras (son de todo cenit). En MODIS y V750 es un efecto de pocas
  pasadas con varios cúmulos dentro del inner (Cordón Caulle, Chillán), no un sesgo de nivel. La vara de MIROVA es la
  suma de todos sus alertados (Coppola 2026 p. 5, «All resampled pixels exhibiting anomalous thermal behavior within
  this area were retained for VRP calculation»; código `VRP.m` l. 83-85), así que la dirección del hallazgo es correcta.
- **CÓMO SE VE EN EL DASHBOARD**: Cordón Caulle y Lastarria publican 20 a 35 % menos de lo que ellos mismos alertaron en
  la cumbre.
- **CONFIANZA**: CONFIRMADO con el matiz. **GRAVEDAD**: 2.

## F3-H4. Fondo por píxel de MIROVA contra el nuestro (V375, 2025)

- **SCRIPT:SALIDA**: `h4_fondo.py` → `h4_fondo.out`. Control de reconstrucción: en 735 pasadas sin recorte y sin kernel,
  mi fondo reconstruido iguala a `diag_L_bg_w_m2_sr_um` con error mediana 0,00017 (p99 0,0012).
- **MEDICIÓN** (fondo por píxel MIROVA / nuestro, mediana [p25, p75], pasadas sin recorte): Copahue 0,849 [0,79,
  0,86], Isluga 0,835 [0,79, 0,87], Láscar 0,860 [0,82, 0,91]; volcanes con kernel 1,03 a 1,08; **Chillán (sin
  kernel) 1,169**. Contrafactual con el fondo de MIROVA sobre nuestros píxeles, cenit ≤ 40°: en medianas Copahue 0,420
  → 1,079, Isluga 0,733 → 1,006, Láscar 0,779 → 0,819 (reproduce exacto a F3); en sumas Copahue 0,605 → 1,366 (n = 18),
  Isluga 0,822 → 1,094, Láscar 0,792 → 0,834.
- **Matiz**: (1) «explica entero» vale en medianas; en sumas Isluga y Copahue se pasan. (2) No es «volcanes altos»:
  Chillán, sin kernel, tiene el fondo de MIROVA por encima del nuestro. (3) En Láscar el fondo explica poco: su déficit
  es de conteo (F3-H2). (4) La comparación supone que el fondo es homogéneo entre los píxeles de MIROVA y los nuestros
  (no son los mismos píxeles). (5) El OSF es filtrado (A105) por pasada, no por píxel; no sesga la razón por píxel.
- **CÓMO SE VE EN EL DASHBOARD**: Copahue e Isluga con la mitad a tres cuartos de la magnitud de MIROVA a nadir.
- **CONFIANZA**: CONFIRMADO con matiz. **GRAVEDAD**: 3, como la misma raíz que F3-H1.

## F4-H1. El mínimo fijo de dNTI fuera de la cumbre

- **ARCHIVO:LÍNEA**: `pipeline/detection_context.py:525` y `:532` (la misma expresión se repite en `:943` y `:947`, en otra función que no leí) (`combinar = max if use_prose_branch else min`;
  `thr_dnti_sce = combinar(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti)`, el mismo C1 para dNTI y dETI);
  `pipeline.profile`: `DNTI_CONTEXTUAL_C1_SCENE = 0.01`, `C2_DNTI_SCENE_NIGHT = 10`, `ENABLE_TESTS_23_PROSE_BRANCH =
  True`. Código de MIROVA, `MIROVA_VIIRS750_hotspot_detection.m` l. 178-198: noche, ROI1 y BOX0 10σ con mínimos 0,02
  (dNTI) y 0,01 (dETI); ROI2 5σ y 0,003. La matriz de ejemplo (`Example/VIIRS750_example.mat`, leída con scipy) tiene la
  clase 2 como caja central de 7 × 7 (filas y columnas 30-36) y la clase 1 alrededor (21 × 19): «fuera de la cumbre» es
  clase 0 y 1, con 0,02. Sp426.5 p. 5 (renderizada): media de los ocho vecinos; el código usa 3 × 3 con central, así que
  su 0,02 equivale a 0,0225 en nuestras unidades.
- **MEDICIÓN** (`h5_minimo_escena.py` → `h5_minimo_escena.out`; todos los records nocturnos 2026, no sólo pos y
  negativos limpios: V375 10.768, V750 10.755, MODIS 5.582; sin diagnóstico 76 / 1 / 8, SIN DATO): fracción con μ+10σ
  bajo el mínimo:

  | sensor | < 0,010 (nuestro) | < 0,020 | < 0,0225 (MIROVA en nuestras unidades) | mediana μ+10σ |
  |---|---|---|---|---|
  | V375 | 0,100 | 0,924 | 0,963 | 0,0136 |
  | V750 | 0,057 | 0,749 | 0,845 | 0,0161 |
  | MODIS | 0,075 | 0,517 | 0,635 | 0,0197 |

  Reproduce las fracciones de F4 sobre el doble de población. Control: en la cumbre (C1 0,003, 5σ) el mínimo decide en
  0,0 a 0,8 %, así que la medición sí separa «decide» de «no decide».
- **Matiz**: el título dice que el mínimo fija el umbral de escena «casi siempre»; con el 0,010 que corre hoy lo fija en
  10 % de V375. Lo que la medición prueba es otra cosa, y es más útil: (a) en V750, donde manda el código, nuestro umbral
  de dNTI fuera de la cumbre queda por debajo del de MIROVA en ~79 % de las pasadas (84,5 − 5,7); (b) en V375 el número
  que se adopte va a decidir casi siempre y no hay dato de MIROVA (F4, sin re-verificar por mí en el OSF). El dETI fuera
  de la cumbre: el mínimo 0,010 coincide con el código y decide en 53 % (V375) y 76 % (V750).
- **CÓMO SE VE EN EL DASHBOARD**: los píxeles de escena son `far` y no se muestran; pueden entrar al segundo pase y a un
  cúmulo de cumbre por contigüidad (SOSPECHA, no medida). El efecto grande en lo visible está en la franja entre la caja
  de 2,6 km de MIROVA y nuestro `inner_radius_km` (3 a 20 km), que recibe nuestros umbrales sensibles y los conservadores
  en MIROVA: es D18, no este hallazgo.
- **CONFIANZA**: CONFIRMADO el sustrato; el título, REFUTADO tal como está escrito. **GRAVEDAD**: 3.

## F4-H6. «Lo estructural se traslada con apoyo citable»

- **Leído renderizando la página**: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §5 (l. 189-196). Campus 2022 p. 7
  (`f4/paginas/campus2022_sensors_2_p7.png`): «The hot-spot detection algorithm is the same used for MODIS» y «steps 1 to
  4 have been slightly modified ... and adapted to VIIRS». Coppola 2026 p. 5: «the hotspot-detection code used by
  MIROVA». Sp426.5 p. 5 (`v3/sp426_p5.png`, render propio): «the average (arithmetic mean) of the eight neighbouring
  pixels» y unsuitable «all the pixels with dNTI or dETI < −0.1». Sp426.5 p. 8 (texto): L4bk «estimated from the
  arithmetic mean of all the pixels surrounding the active one (or around the active cluster)».
- **Contra el código V750**: `colfilt([3 3], mean)` incluye el central (`.m` l. 285 para NTI y 362 para ETI); el piso de −0,1 se
  aplica sólo al contraste de NTI (`.m` l. 298), no al de ETI; el fondo del VRP es
  `fillmissing2` tras `imdilate`. Las tres diferencias leídas.
- **Más fuerte que lo que dijo F4**: Campus 2022 p. 7, ec. 2, describe el fondo del VRP **de VIIRS 750** como «the
  arithmetic mean of pixels surrounding the active one/s». O sea que para el fondo el paper del mismo sensor ya
  contradice al código: la cita no respalda ni el traslado ni la propia descripción de V750. Lo único que las citas sí
  sostienen para los tres sensores es la suma de todos los alertados (Coppola 2026 p. 5).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (juicio documental; el A/B que el plan pide es lo que protege).

## Hallazgos propios

### V3-1. El tablero rotula «Distancia al cráter» una distancia al centroide del volcán

- **ARCHIVO:LÍNEA**: `frontend/index.html:3159` (popup: «Distancia al cráter: ${px.dist_km}»); `dist_km` de cada
  `anomaly_pixels` sale de `dist` (`pipeline/process_viirs_mod.py:517`, `process_viirs.py:780`, `process_modis.py:560`:
  `haversine_km(volcano_lat, volcano_lon, lat, lon)`), mientras el ancla del pipeline es el cráter
  (`pipeline/geo_utils.py:53-78`, `vent_lat/vent_lon` primero). Separación centroide-cráter en `volcanoes.yaml`:
  Cordón Caulle 7,58 km, Tupungatito 2,73 km, Villarrica 0,85, Láscar 0,68, Chaitén 0,59, Planchón 0,50, resto 0.
- **QUÉ PASA**: el mismo píxel de Tupungatito 2026-10-18 05:42 (V750) figura a 2,79 km en `anomaly_pixels` y a 0,111 km
  en `primary_cluster.centroid_dist_km` y `final_hotspot_dist_km`. El popup del píxel le muestra al operador 2,79 km «al
  cráter». En Cordón Caulle el error llega a 7,6 km. También usan `anomaly_pixels[0].dist_km` los respaldos de
  `index.html:2739`, `:3035` y `:3286` (rutas legacy; no medí cuántos records las alcanzan hoy).
- **CÓMO SE VE EN EL DASHBOARD**: con «Todos los pixels», un píxel en el cráter de Tupungatito aparece a casi 3 km;
  un geólogo puede leerlo como fuente lateral. Las auditorías que filtran `dist_km <= inner` (F3 lo hizo) usan otro
  origen que el pipeline; en F3-H2 y F3-H3 el efecto resultó chico (19 de 1.652 pares; Cordón Caulle V750 0,715 → 0,644).
- **CÓMO REPRODUCIRLO**: `python -B -c "import json;r=[x for x in json.load(open('data/mirova_equivalent/Tupungatito.json',encoding='utf-8'))['records'] if x['datetime_utc']=='2026-10-18 05:42' and x['sensor'].endswith('_750')][0];print(r['anomaly_pixels'][0]['dist_km'],r['primary_cluster']['centroid_dist_km'])"`
- **CONFIANZA**: CONFIRMADO (leído). Es la familia A3 del proyecto. **GRAVEDAD**: 2.

### V3-2. Arreglar F3-H1 tiene costo de precisión que hay que medir

- **SCRIPT:SALIDA**: `h1_recorte_v750.out`: de los 235 cúmulos 0 de cumbre, 55 son alertas de MIROVA, 68 negativos
  limpios y 112 `sin_info`. Un fondo local en V750 (D25 V750 o el del código) devolvería energía a los dos grupos. El
  A/B tiene que contar las 68 como publicaciones nuevas en negativo limpio, no sólo las 55 recuperadas.
- **CONFIANZA**: CONFIRMADO el conteo; el efecto del arreglo, SOSPECHA. **GRAVEDAD**: 2.

## VERIFICADO LIMPIO

- La copia de F3 de los pares OSF 2025 es reproducible: `python -B experiments/_s158_audit/f3/descomp_osf2025.py . <OSF>
  experiments/_s158_audit/v3/pares_osf2025_v3.csv` da un CSV idéntico celda a celda al de F3 (`descomp_rerun.out`).
- El fondo que F3 reconstruye es el del pipeline: en V750 2026 (`h1_recorte_v750.out`, 752 píxeles) y en V375 2025
  (`h4_fondo.out`, 735 pasadas), error mediana bajo 0,1 %.
- V750 no tiene kernel local de fondo: `local_kernel_bg_compatible` sólo aparece en la firma y el docstring de
  `process_viirs_mod.py` (`grep -n local_kernel_bg_compatible pipeline/process_viirs_mod.py` → l. 447 y 461).
- El tope D9 no participa en los cúmulos en 0 de V750 (0 de 238 con `d9_capped`).
- La identidad VRP = k·A·(L_hot − L_bk) del OSF se cumple exacta en V375, V750 y MODIS de 2025 (`descomp_rerun.out`).
- El rótulo invertido de ROI1/ROI2 en los comentarios del `.m` ya está documentado en
  `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:90-91`; la matriz de ejemplo lo confirma (clase 2 = caja central 7 × 7).
- `isValidDetection` oculta todo cúmulo con `vrp_mw = 0` (`frontend/index.html:1595`), leído.

## Lo que no pude verificar

- Que el fondo interpolado de MIROVA dé exceso positivo en los píxeles de V750 que nosotros dejamos en 0 (no hay L1B
  remuestreado; el oráculo `experiments/_s158_oraculo_mirova/` podría correrse sobre granulos reales).
- Si la pendiente de F3-H2 la cierra el remuestreo D17 o es pérdida de detección en píxeles grandes: lo decide el A/B.
- El mínimo de dNTI de MIROVA en V375 y MODIS operacional: no busqué en el OSF ni en Campus 2024.
- Cuánto aporta la escena sobre-alertada en V750 (umbral 0,010 contra 0,02) a los cúmulos de cumbre por contigüidad.
- F3-H2 y F3-H4 en Tupungatito, Llaima y Chillán V375: el OSF 2025 no trae Tupungatito y tiene pocos pares de los otros.
