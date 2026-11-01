# S159 M, verificador con contexto limpio

Worktree `C:\vrp-trabajo\s159-m`, commit `cecd4b0f1`. Datos: jsonl crudos del run 39681481914 en
`experiments/_s159/m/resultado/` (85 filas, 0 errores). No despaché nada ni toqué `pipeline/`, `data/` ni `frontend/`.

Scripts propios (código distinto al del agente, mismo dato):
- `verif_m.py` y su salida `verif_m_salida.txt`: afirmaciones 1, 2 y 4. «Publicado» = `mirovaEqVrp` **e**
  `isValidDetection` extraídas de `frontend/index.html` (l. 1162 y 1595) y ejecutadas con node, pasando el record
  completo que guardó el probe (no el mínimo de `analizar_m.py`).
- `pareo_mirova.py` y `pareo_mirova_salida.txt`: pareo con MIROVA a ±10 min y tasa base del desfase de 5 min.

Las dos preguntas del instrumento, para todo lo que sigue:
1. ¿Vería una afirmación rota? Sí: recalculo los conteos desde el jsonl con otro arnés, clasifico cada cambio por
   mecanismo y busco filas de MIROVA fuera de la hora exacta.
2. ¿Distingue «no medí» de «no hay»? Control positivo del arnés (`verif_m_salida.txt` l. 2): cúmulo dentro del inner
   2, fuera 0, `far` 0, sin cúmulo y `vrp_mw` 0 da 0, cúmulo en 0,0 MW da 0, sin cúmulo con `vrp_mw` 0,7 da 0,7
   (el respaldo heredado de `mirovaEqVrp`). Pareo: Láscar 2026-02-11 07:00 sale ALERTA 0,48 a 1,41 km. Tasa base:
   el pareo exacto falla en 121 de 5.815 records MODIS (2026-02-15 a 2026-10-17, 11 Tier A), así que el instrumento sí
   puede ver un desfase de granulo.

## Veredictos

### Afirmación 1: PARCIAL (los números se reproducen; dos partes de la lectura caen)

Se reproduce exacto: S1 + S2 = 63 records, todos `summit` en `data/`, cenit en el cráter 40,6° a 65°; publicados A 57,
B 49; 12 cambios, 10 se apagan y 2 se encienden (`verif_m_salida.txt`, bloque «Afirmación 1»). Con `isValidDetection`
agregada no cambia nada (1 incoherencia, un `far` de 1,724 MW que ninguno de los dos predicados publica).

Lo que cae:

- **El mecanismo «sale del círculo de cumbre» no vale para los 6 que nombra.** Calculé la posición MxD03 de los
  píxeles del cúmulo de A (posición A más el desplazamiento de su mismo i,j). Llaima 4,93 a 8,82 km (inner 5),
  Chillán 06-01 4,73 a 6,94, Chaitén 4,39 a 13,0, Cordón Caulle 06-19 19,23 a 24,73 y 06-30 17,58 a 23,84 (inner 20)
  salen; **Cordón Caulle 2025-08-03 no**: sus dos píxeles pasan de 17,17 y 18,94 km a 13,78 y 15,61 km, más adentro, y
  aun así B pierde la detección (`diag_n_first_pass_summit` 1 a 0, `t_bg` igual, 245,3 K). Ese apagado viene de otra
  cosa que depende de la posición (SOSPECHA: estadística de la caja de ROI o de la regresión del ETI). En cambio hay
  dos apagados que también salen del círculo sin estar en el borde: Lastarria 2026-02-24, 1,20 a 4,45 km con inner 3,
  y Chillán 2026-01-19, 2,66 y 3,12 a 6,51 y 6,83 km (pasa a `far`). Cuenta correcta: **7 de 10 apagados salen del
  inner con MxD03**, 1 se apaga sin salir y 2 son de magnitud (punto siguiente).
- **4 de los 12 cambios no son de posición del píxel sino de magnitud cerca de cero.** Los dos «se enciende» y dos
  «se apaga» son Láscar con el mismo cúmulo y la misma clase en los dos brazos, cuyo `pc.vrp_mw` cruza cero: 2026-02-11
  0,0 a 0,033; 2026-04-01 0,0 a 0,060; 2025-05-23 0,029 a 0,0; 2025-06-02 0,019 a 0,0. En los cuatro `t_bg_k` se mueve
  0,24 a 0,41 K y el píxel está a menos de 0,4 K del fondo (BT 261,7 a 272,0 K). Es el fondo del anillo moviéndose con
  la posición, justo lo que H5 llama «casi no cambia».
- **El conteo contra MIROVA: 9 con referencia, no 8.** Chillán 2026-01-19 02:40 tiene fila de MIROVA MODIS RUTINA a las
  02:35 (`pareo_mirova_salida.txt`). Es el gránulo anterior de la misma pasada de Terra: el cráter cae en la línea 23 de
  2030 del nuestro, y el desfase de 5 min aparece en 121 de 5.815 records MODIS. Con ese pareo (SOSPECHA alta, no
  probada con la imagen de MIROVA) B acerca en **7 de 9** y aleja en 2. Además 3 de los 9 son los cruces de cero de
  Láscar (diferencias de 0,02 a 0,06 MW contra alertas de 0,44 y 0,48 MW).
- **La dirección «10 apagan, 2 encienden» es en buena parte del diseño.** La población está condicionada a que A
  publicó (`summit` en `data/`, `armar_poblacion.py:62-63`); una encendida sólo puede salir de un cúmulo en 0,0 MW o de
  S4. Cualquier perturbación de la posición sobre records elegidos por pasar un umbral apaga más de lo que enciende
  (A109). Lo que se puede leer es el pareo con MIROVA (7 de 9), no el saldo. Los records sin detección no se
  muestrearon, salvo los 2 de S5. S2 es una muestra sistemática (25 de 41), así que «1 de cada 5» no es tasa de censo.

### Afirmación 2: CONFIRMADA (con un matiz de comparación)

Recalculado con la regla de lado sobre el frame real: frame 0, 40 a 50°, mediana 2,817 km (n 36); sobre 50°, 5,041
(n 15, máximo 9,42); lado contrario 1,101 (n 15) y 2,475 (n 11). No es un efecto de Láscar, que es 27 de los 36 del
primer estrato: sin Láscar da 2,951 (n 9). Sólo con S1 a S3 (sin `far` ni Chillán) da 2,808 y 5,879 del lado del frame
0. Matiz: son desplazamientos **totales**; el plan hablaba de «hacia el nadir». La componente hacia el sensor da 2,27 y
4,46 del lado del frame 0 (sobre el plan) pero **0,61 km** del lado contrario a 40 a 50°, bajo el «1 a 1,7» del plan.
«Mayor que el plan» vale para el lado del frame 0 con cualquiera de las dos medidas; del otro lado depende de cuál se
use.

### Afirmación 3: CONFIRMADA

CMR (mi consulta, sin credenciales): `MYD021KM.A2026285.0720.061.2026286023420.hdf`, `MYD03.A2026285.0720`,
`MOD021KM.A2026288.0105.061.2026288131238.hdf` y `MOD03.A2026288.0105` existen en LAADS (6.1 y 7) y en LANCE.
`data/mirova_equivalent/NevadosDeChillan.json` tiene los dos records con **esos mismos nombres de archivo**, cenit
58,19° y 57,58°, `primary_cluster` nulo y `diag_n_first_pass_pixels` 0. En el probe, A y B: `diag_n_first_pass_pixels`
0, `n_anomalous_pixels` 0, píxel más caliente de la escena a 24,17 / 29,06 km (10-12) y 29,12 / 32,54 km (10-15).
MIROVA (CSV del scraper): ALERTA 2,18 MW a 2,24 km (10-12 07:20) y 1,72 MW a 2,24 km (10-15 01:05). El cráter está en
la línea 981 y 187 del gránulo, lejos del borde, así que no es un problema de gránulo vecino. Alcance: la frase
prueba que **arreglar sólo la geolocalización** no las recupera, con el perfil de hoy (B22 primaria y `max`).

### Afirmación 4: CONFIRMADA

n 38 de 39 Láscar de S1 a S3 tienen el mismo conjunto de píxeles (sólo 1 distinto, así que no hay selección que
explique el efecto). Comprobé que es la misma detección: `n_pixels` del cúmulo igual en 38 de 38 y BT de cada píxel
igual en 38 de 38 (el VRP difiere en 35, por el fondo). Distancia del pipeline: 2,543 a 0,588 km, B más cerca en 35;
recomputada con haversine desde el ancla (`vent_lat/vent_lon` de `volcanoes.yaml`, -23,36293, -67,731416): 2,544 a
0,587. Por lado: frame 0 2,877 a 0,707 (27 de 27); contrario 0,980 a 0,415 (8 de 11). Ningún `anomaly_pixels` llega
al tope de 80 del resumen del probe, así que la comparación de conjuntos no está truncada.

## Hallazgos propios

1. **Un apagado sin salir del círculo** (Cordón Caulle 2025-08-03 06:35, Terra, cenit 44,7°): el píxel entra 3,4 km y
   la detección igual se pierde. `verif_m_salida.txt`. CONFIANZA: CONFIRMADO el hecho, SOSPECHA el mecanismo.
   GRAVEDAD 3: la geolocalización decide publicaciones por más de un camino, y un arreglo pensado sólo para el borde
   del inner (MEJ-7) no lo cubre.
2. **El fondo del anillo sí decide publicaciones cerca de cero**: 4 de 12 cambios. GRAVEDAD 2 (magnitudes de 0,02 a
   0,06 MW, pero el tablero las publica igual, `isValidDetection` sólo pide más de 0).
3. **Pareo exacto pierde la pasada en el borde del gránulo**: 121 de 5.815 records MODIS sólo parean a ±5 min. Afecta
   a cualquier evaluación MODIS que paree por hora exacta, no sólo a este frente. GRAVEDAD 2.
4. **Población condicionada al resultado de A** (diseño): el saldo de apagados contra encendidos no se puede leer como
   dirección. GRAVEDAD 2 para la conclusión «la brecha es sobre-publicación» del informe H1.

## VERIFICADO LIMPIO

- Brazo B sólo cambia lat/lon: `calculate_vrp` llama a `read_modis_l1b` por nombre de módulo
  (`pipeline/process_modis.py:547`), que el probe parcha; los ángulos siguen de `_interp_geo` (`:294`).
- `store.append_record` del probe usa los mismos argumentos que `scripts/run_pipeline.py:247-254`.
- jsonl: 85 filas, `rec_A`/`rec_B` nunca nulos, `crudo_*_none` 0, error de ubicación del i,j de A máx 0,0008 km.
- `process_modis.py:838` es `is_summit = roi1_summit_mask(vent_dist_per_pixel, inner_radius_km, _roi1_mask)` y la
  distancia del cúmulo se mide desde el ancla (`process_modis.py:1167`, `clustering.py:104`).
- OSF 2025 re-corrido sobre el archivo del checkout principal: Láscar 2025-05-23 07:25, 0,44 MW a 1,41 km; 0 filas para
  los otros tres a ±10 min; control 235 filas de Láscar MODIS.
- Filas exactas de MIROVA de los otros 7 casos de 2026, con ±10 min: una sola fila cada uno, la misma que usó el agente.
