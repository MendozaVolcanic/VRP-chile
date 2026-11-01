# F3 (S158): qué explica físicamente el déficit de magnitud contra MIROVA

Auditor F3, 2026-10-21. Rama `s158-d17-diseno`. Sólo lectura: no se tocó nada fuera de esta carpeta. Todos los
scripts y salidas están acá (`experiments/_s158_audit/f3/`), corridos con `python -B` desde esta carpeta, raíz
`../../..`. OSF v2.5: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv`.

## 0. En una pantalla

La pregunta era cuánto del déficit es del **objeto** (huella, cráter, nieve, lago) y cuánto del **procesamiento**.
El razonamiento de partida: lo que hace el objeto (las paredes de Láscar tapan el foco, el píxel mezcla lava con
nieve) cambia la radiancia que ven **los dos** sistemas por igual, así que se cancela en la razón nuestra/MIROVA. Un
déficit en la razón sólo puede venir del procesamiento: cuántos píxeles se alertan, qué fondo se resta, qué parte se
publica. El OSF v2.5 trae, por pasada de 2025, Npix, la radiancia caliente sumada (L_hot) y la de fondo (L_bk); nuestros
records traen la BT y el VRP de cada alertado. Pareando pasada a pasada (2.523 pares, cenit igual a 0,07° de mediana) se
puede partir la razón en factores. Lo que sale, VIIRS 375, misma región (todos los alertados de MIROVA dentro del
`inner_radius_km`), 1.652 pasadas de 2025:

| cenit | conteo nuestro / MIROVA | energía dentro del inner / MIROVA | publicado / MIROVA |
|---|---|---|---|
| 0 a 10° | 0,89 | **0,98** | 0,86 |
| 10 a 20° | 0,76 | 0,90 | 0,84 |
| 20 a 30° | 0,66 | 0,79 | 0,76 |
| 30 a 40° | 0,64 | 0,72 | 0,67 |
| 40 a 50° | 0,50 | 0,64 | 0,62 |
| 50 a 60° | 0,50 | 0,60 | 0,57 |
| 60 a 75° | 0,42 | 0,48 | 0,47 |

(`dentro_inner_salida.txt`, razones de sumas.) Tres lecturas:

1. **A nadir la energía que alertamos es la de MIROVA** (0,98). Lo que el operador ve a nadir (0,86) lo pierde la
   **selección** (núcleo F5' y cúmulo), no el fondo ni el detector.
2. **El déficit crece con el cenit, y lo hace el conteo**: la cantidad de píxeles de MIROVA no cambia con el ángulo
   (Spearman +0,02) y la nuestra cae (−0,39 en los volcanes de anomalía extendida). Es la huella nativa que crece
   mientras MIROVA trabaja en celdas fijas de 375 m (D17). Entre una pasada a nadir y una a 65° de la **misma** noche,
   nuestra magnitud relativa a MIROVA cambia en un factor 1,8 sin que el volcán cambie.
3. **El fondo pesa por volcán, no en el agregado**: en los volcanes que restan la mediana del anillo de 5 a 25 km
   (Láscar, Isluga, Copahue) nuestro fondo por píxel es 16 a 24 % más alto que el de MIROVA; en los de kernel local
   es 3 a 8 % más bajo. En VIIRS 750, sin kernel en ningún volcán, el fondo de anillo supera a la radiancia del píxel
   alertado y el recorte ΔL ≥ 0 lo deja en 0,0 MW: **Tupungatito, 63 de 81 detecciones nocturnas desde marzo**.

Esto matiza `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6 («el déficit grande es de nivel más que de pendiente»): con
tramos finos y la misma región, el nivel a nadir es chico y es selección; lo grande es la pendiente, y la pendiente es
conteo (hallazgo 2).

## 1. Hallazgos (lo peor primero)

### H1. En VIIRS 750 el fondo de anillo deja en 0,0 MW las cumbres frías: Tupungatito pierde 11 de 13 alertas de MIROVA

- **SCRIPT:SALIDA**: `recorte_todos.py` → `recorte_todos_salida.txt`; `clip_v750.py` → `clip_v750_salida.txt`;
  `scraper2026.py` → `scraper2026_salida.txt`. Código: `pipeline/process_viirs_mod.py:1040` (fondo
  `bt_to_spectral_radiance(t_bg, M13_LAMBDA)`, escalar del anillo) y `:1055` (`delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`).
  MIROVA: `MIROVA_VIIRS750_VRP.m:64-85` (fondo interpolado bajo los alertados con un hueco dilatado, sin recorte).
- **QUÉ PASA**: de noche, en una cumbre nevada, el píxel de 750 m mezcla el cráter con hielo frío. Su BT en M13 queda
  bajo la mediana del anillo de 5 a 25 km, que es valle sin nieve y más tibio, aunque el NTI lo detecte (el exceso es
  sub-píxel y aparece en la relación M13/M15, no en la BT absoluta). Restar el anillo da exceso negativo y el recorte
  lo deja en cero. MIROVA resta el entorno inmediato (también hielo) y le queda exceso positivo. Medido, noche,
  2026-03-01 a 2026-10-20, pasadas con al menos un alertado: en las pasadas con cúmulo en 0 la BT del alertado más
  caliente menos `t_bg_k` es ≤ 0 en todas (Tupungatito mediana −2,54 K, 63 de 63; Planchón-Peteroa −2,02 K, 15 de 15;
  Isluga −1,09 K, 76 de 76) y en las publicadas es positiva (+9,7, +10,2 y +1,5 K). Fracción de pasadas con todos los
  alertados recortados, V750: Tupungatito 77,8 % (63/81), Isluga 58,0 % (76/131), Planchón-Peteroa 51,7 % (15/29),
  Villarrica 25,0 % (4/16), Cordón Caulle 16,4 % (23/140), Láscar 15,4 % (50/324). En VIIRS 375 los cinco volcanes con
  kernel local dan 0 % (control positivo: el mismo volcán, con fondo local, no se recorta); los de anillo, 4 a 15 %
  (Chillán 14,9 %, Tupungatito 6,4 %, Copahue 5,9 %, Isluga 4,2 %).
- **CÓMO SE VE EN EL DASHBOARD**: MIROVA publica una alerta de 0,2 MW en Tupungatito y nosotros nada:
  `isValidDetection` exige `primary_cluster.vrp_mw > 0` (`frontend/index.html:1595`), así que la detección desaparece
  del contador y del gráfico. Contra la tabla del scraper: Tupungatito V750 11 de 13 alertas de MIROVA sin magnitud
  nuestra, Planchón-Peteroa 8 de 9 (parte por no detección), Isluga 23 de 40.
- **CÓMO REPRODUCIRLO**: `python -B clip_v750.py ../../.. scraper2026_filas.csv`; pasada Tupungatito V750
  2026-03-01 05:36 UTC (BT 267,12 K, `t_bg_k` 269,77 K, cúmulo 0,0 MW, summit a 0,29 km).
- **CONFIANZA**: CONFIRMADO (medido; el mecanismo se lee en el código de los dos lados). Es la cara de D25 en V750,
  medida con K.
- **GRAVEDAD**: 4. Las alertas son bajo 1 MW (no protegidas), pero en los volcanes glaciares la mayoría de las
  detecciones nocturnas de VIIRS 750 se vuelve invisible por un fondo que no es el del cráter.

### H2. La pendiente con el cenit es conteo: MIROVA alerta las mismas celdas a cualquier ángulo y nosotros cada vez menos píxeles

- **SCRIPT:SALIDA**: `cenit_fino.py` → `cenit_fino_salida.txt`; `dentro_inner.py` → `dentro_inner_salida.txt`;
  `analizar_pares.py` → `analizar_V375_cls1_salida.txt`.
- **QUÉ PASA**: una anomalía extendida (piso de cráter, lacolito, campo fumarólico) ocupa una superficie fija. En la
  grilla de 375 m de MIROVA esa superficie cubre siempre las mismas celdas; en nuestro barrido nativo el píxel crece
  con el ángulo y la misma superficie cabe en menos píxeles, cada uno con la radiancia diluida, y el área nominal fija
  de la fórmula no lo devuelve. Medido, V375, clase 1 del OSF, 2025: Npix de MIROVA plano con el cenit (Spearman
  +0,02 en el grupo extendido), el nuestro cae (−0,39); conteo nuestro/MIROVA 1,09 a 0-10°, 0,73 a 30-40°, 0,47 a
  60-75° (grupo extendido, sumas). La energía sigue al conteo: 1,08 → 0,75 → 0,52. El L_hot por píxel nuestro es
  1,10 a 1,14 veces el de MIROVA en todos los tramos (`analizar_V375_cls1_salida.txt`), así que no es que nuestros
  píxeles se apaguen: hay menos.
- **CÓMO SE VE EN EL DASHBOARD**: el mismo volcán, la misma noche, da una magnitud distinta según la órbita: relativa a
  MIROVA, 0,86 en una pasada a nadir y 0,47 en una a 65° (factor 1,8). Un operador que lea un salto entre pasadas
  consecutivas como cambio del volcán está leyendo geometría.
- **CÓMO REPRODUCIRLO**: `python -B descomp_osf2025.py ../../.. <OSF> pares_osf2025.csv` y luego
  `python -B cenit_fino.py pares_osf2025.csv` y `python -B dentro_inner.py ../../.. pares_osf2025.csv`.
- **CONFIANZA**: CONFIRMADO como medición. Que el mecanismo sea el remuestreo (D17) y no otra cosa que también crece con
  el ángulo es SOSPECHA fuerte: no se corrió el oráculo sobre un gránulo nativo remuestreado.
- **GRAVEDAD**: 3. Contradice la lectura de `docs/DISENO_D17_REMUESTREO_UTM.md` §3.6 punto (2) y su consecuencia
  «lo que D17 puede cerrar en la pendiente es como mucho un 23 %»: el estadístico S de ese documento es un cociente de
  medianas en dos tramos anchos (≤40° y >40°), y el tramo ≤40° ya contiene casi toda la caída de 0,98 a 0,72. Si un
  remuestreo devolviera el conteo de MIROVA, la parte cerrable es la mayor parte del déficit oblicuo, no un 23 %. Cambia
  el orden D17 contra D25 de `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §7 bis.

### H3. A nadir, lo que se pierde es la selección: el núcleo F5' y el cúmulo publican 0,86 de una energía que es 0,98

- **SCRIPT:SALIDA**: `dentro_inner_salida.txt`; `cumulo_vs_inner.py` → `cumulo_vs_inner_salida.txt`;
  `seleccion.py` → `seleccion_salida.txt`.
- **QUÉ PASA**: MIROVA suma todos los alertados de su ventana (`MIROVA_VIIRS750_hotspot_detection.m:241-248`,
  `MIROVA_VIIRS750_VRP.m:83-85`; para V375 es TRASLADADA). Nosotros publicamos el núcleo F5' (V375) o el cúmulo (V750,
  MODIS). A 0-10°, misma región: energía 0,976, publicado 0,858. Dentro del inner, 2026 noche, lo publicado sobre la
  suma de alertados dentro del inner: V375 0,949, V750 0,831, MODIS 0,898 (sumas). Los volcanes donde más pesa son los
  extendidos: Cordón Caulle V750 0,694 y V375 0,801, Lastarria V375 0,744, Chillán V750 0,810, Villarrica V750 0,842,
  Láscar V750 0,904 y MODIS 0,906.
- **CÓMO SE VE EN EL DASHBOARD**: magnitudes de Cordón Caulle y Lastarria un 20 a 30 % bajo lo que alertamos dentro
  del inner, en todas las pasadas. Es nivel, no ruido.
- **CÓMO REPRODUCIRLO**: `python -B cumulo_vs_inner.py ../../..`.
- **CONFIANZA**: CONFIRMADO. Es D32/D8' medido por volcán.
- **GRAVEDAD**: 3.

### H4. El fondo de anillo sobreestima el fondo en los volcanes altos sin kernel: explica entero el déficit a nadir de Copahue e Isluga

- **SCRIPT:SALIDA**: `mismo_k.py` → `mismo_k_salida.txt` (bloque 3); `analizar_V375_cls1_salida.txt` (columnas bk_px,
  exc_px, R_cf).
- **QUÉ PASA**: la mediana del anillo de 5 a 25 km toma valles más bajos y, de noche, más tibios que el entorno del
  cráter. El fondo por píxel de MIROVA (interpolado justo fuera del halo) es 0,808 del nuestro en Copahue, 0,824 en
  Isluga, 0,856 en Láscar (V375, 2025, medianas). Con el fondo de MIROVA aplicado a nuestros propios píxeles
  (contrafáctico R_cf), el déficit a ≤40° de Isluga pasa de 0,73 a 1,01 y el de Copahue de 0,42 a 1,08; Láscar sólo de
  0,78 a 0,82, porque su déficit es de conteo. En los cinco volcanes con kernel local pasa lo contrario: el fondo de
  MIROVA es 1,03 a 1,08 veces nuestro kernel.
- **CÓMO SE VE EN EL DASHBOARD**: Copahue y la fumarola de Isluga con la mitad o dos tercios de la magnitud de MIROVA
  a nadir; los cinco volcanes de kernel, algo por encima.
- **CÓMO REPRODUCIRLO**: `python -B mismo_k.py ../../.. pares_osf2025.csv`.
- **CONFIANZA**: CONFIRMADO para VIIRS 375 en 2025 (el instrumento reconstruye nuestro fondo con error 0,0000 de
  mediana, `control_reconstruccion_salida.txt`). Para Tupungatito, Llaima y Chillán, que también usan anillo, es
  TRASLADADA: el OSF no los trae (ver §3).
- **GRAVEDAD**: 3.

### H5. La predicción del «halo tibio» contra D25 no se cumple en VIIRS 375: el fondo de 8 vecinos queda bajo el de MIROVA, no sobre

- **SCRIPT:SALIDA**: `mismo_k_salida.txt` bloque 3 (columna `bgM_local`).
- **QUÉ PASA**: `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §4.3 razona que el halo de un foco sub-píxel lleva calor y que
  un fondo de vecinos (D25) «se come parte del exceso». Nuestro kernel local (`pipeline/vrp_regimes.py:39`, 8 vecinos no
  alertados, análogo al brazo de D25) da, contra el fondo por píxel de MIROVA: Chaitén 1,034, Cordón Caulle 1,025,
  Planchón-Peteroa 1,039, Lastarria 1,046, Villarrica 1,077 (MIROVA / nuestro). Nuestro fondo de vecinos es **más frío**
  que el de MIROVA, no más tibio. La media de BT antes de Planck explica del orden de 1 % (cálculo propio, desigualdad de
  Jensen con 3 K de dispersión); el resto, SOSPECHA: el remuestreo lineal reparte algo del foco a las celdas de donde
  MIROVA interpola su fondo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: ídem H4.
- **CONFIANZA**: CONFIRMADO como número, en V375 y 2025; el mecanismo, SOSPECHA. Para VIIRS 750 SIN DATO.
- **GRAVEDAD**: 2. Afecta cómo se lee el A/B de D25, no una alerta.

### H6. La oclusión del cráter de Láscar es real y se ve en MIROVA, pero se cancela en la razón: la caída de la razón con el ángulo es del procesamiento

- **SCRIPT:SALIDA**: `objeto_vs_proceso.py` → `objeto_vs_proceso_salida.txt`.
- **QUÉ PASA**: predicción: si las paredes del cráter tapan el foco en vista oblicua, la magnitud propia de MIROVA cae
  con el cenit en Láscar más que en un volcán sin cráter profundo, y nuestra razón no cae más que la de ese otro.
  Medido, V375, 2025, clase 1: el VRP de MIROVA relativo a su mediana móvil cae de 1,50 a 0,16 en Láscar (Spearman
  −0,63) y su L_hot por píxel de 0,255 a 0,110; en Cordón Caulle el L_hot por píxel es plano (0,192 a 0,168) y en
  Isluga el VRP propio también (Spearman −0,00). Pero nuestra razón cae **más** en Isluga (0,71 a 0,25, Spearman −0,60
  entre publicadas) que en Láscar (0,83 a 0,46, −0,48). Isluga no tiene oclusión y su razón se derrumba; Láscar sí la
  tiene y su razón cae como la de Cordón Caulle. El objeto se cancela; la caída es del procesamiento (H2 y H4).
- **CÓMO SE VE EN EL DASHBOARD**: invisible como tal; explica por qué Láscar y MIROVA caen juntos con el ángulo.
- **CÓMO REPRODUCIRLO**: `python -B objeto_vs_proceso.py pares_osf2025.csv`.
- **CONFIANZA**: CONFIRMADO para el patrón; la cancelación total no se puede probar con dos volcanes.
- **GRAVEDAD**: 2.

### H7. Cerca del nadir, cuando nosotros vemos un píxel y MIROVA dos o tres, los suyos llevan el mismo foco repartido y suman 17 a 67 % más

- **SCRIPT:SALIDA**: `reparto_foco.py` → `reparto_foco_salida.txt`; `jepv6_exceso_por_pixel.py` →
  `jepv6_exceso_por_pixel_salida.txt`.
- **QUÉ PASA**: V375, cenit ≤ 30°, pasadas con un solo píxel nuestro, fondo de MIROVA aplicado a ese píxel. Control
  (N_M = 1, n = 63): el exceso del píxel de MIROVA es 0,887 del nuestro (el pico remuestreado queda 11 % más bajo).
  N_M = 2 (n = 48): exceso por píxel de MIROVA 0,58 del nuestro (1/N = 0,50), total 1,17. N_M = 3 (46): 0,45 y 1,35.
  N_M ≥ 4 (9): 0,42 y 1,67. Cada píxel de MIROVA lleva una fracción cercana a 1/N del foco y el total crece con N:
  es lo que predice un foco repartido por interpolación lineal (el sintético de D17 da 1,40 con tres celdas). Pero
  también lo predice un detector más sensible que recoge la derrama real del foco en los vecinos (PSF). En Vulcano
  (datos de MIROVA solos, sin condicionar a nuestro conteo) el exceso por píxel es plano con Npix (0,049; 0,058; 0,044;
  0,058), que no ayuda a separar: allí más píxeles es más superficie caliente.
- **CÓMO SE VE EN EL DASHBOARD**: parte del déficit a nadir de Láscar, Planchón-Peteroa, Villarrica e Isluga (conteo
  0,53 a 0,58 a ≤30°, `dentro_inner_salida.txt`) es energía de vecinos que no detectamos.
- **CÓMO REPRODUCIRLO**: `python -B reparto_foco.py mismo_k_filas.csv`.
- **CONFIANZA**: el número, CONFIRMADO; remuestreo contra PSF y sensibilidad, SOSPECHA (pide un gránulo nativo, su TIF y el oráculo).
- **GRAVEDAD**: 2.

### H8. La clase 1 del OSF no garantiza origen volcánico: Chillán, febrero de 2025

- **SCRIPT:SALIDA**: consulta en esta sesión sobre el OSF (bloque «Chillán» de la sesión; las cifras se reproducen con
  `descomp_osf2025.py` y la tabla de `analizar_V375_cls1_salida.txt`, fila NevadosDeChillan).
- **QUÉ PASA**: 68 alertas de clase 1 en 2025-02, VRP mediano 31,7 MW, mediana de posición −36,825 / −71,547, unos
  15 km al oeste-noroeste del punto del volcán, con Max_Dist mediano 17 km. Para el agregado que la clase 1 «es el
  volcán» (A105) eso no vale: es una fuente persistente a baja cota (SOSPECHA: incendio forestal; no cotejado con FIRMS).
  Nosotros no la publicamos (pub_ok 0 %), que es lo correcto.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; contamina cualquier métrica que use la clase del OSF como etiqueta.
- **CONFIANZA**: CONFIRMADO el dato; el origen, SOSPECHA. **GRAVEDAD**: 1.

## 2. El déficit por tipo de volcán

V375, 2025, clase 1 del OSF, cenit ≤ 30°, misma región (`dentro_inner_salida.txt`), más el mecanismo dominante
según los factores de `analizar_V375_cls1_salida.txt` y `mismo_k_salida.txt`.

| tipo | volcán | conteo | energía | publicado | qué lo explica |
|---|---|---|---|---|---|
| lago de lava | Villarrica (n = 17) | 0,57 | 0,99 | 0,99 | foco puntual; MIROVA reparte el foco en más celdas (H7), nuestro píxel más caliente y nuestro fondo de kernel más bajo lo compensan. Sin déficit a nadir. V750: 25 % recortado (H1) |
| cráter profundo | Láscar (117) | 0,53 | 0,82 | 0,81 | conteo (H7) y fondo de anillo 17 % alto (H4); la oclusión baja a los dos sistemas por igual (H6) |
| glaciar | Tupungatito | SIN DATO OSF | | | contra la tabla 2026, V375 publicado/MIROVA 0,41 a ≤40° y 0,27 a >40°, energía 0,60 y 0,31; V750 78 % recortado (H1). Fondo de anillo: TRASLADADA de H4 |
| lacolito difuso | Cordón Caulle (92) | 1,15 | 1,17 | 0,84 | a nadir alertamos tanto como MIROVA; pierde la selección (H3). En oblicuo, conteo (H2) |
| nevado débil | Copahue (14) | 0,94 | 0,47 | 0,47 | fondo de anillo 24 % alto: con el fondo de MIROVA queda en 1,08 (H4) |
| nevado débil | Llaima | SIN DATO | | | ninguna alerta de clase 1 en el OSF 2025; 1 alerta en la tabla 2026 |
| nevado débil | Chillán | SIN DATO volcánico | | | clase 1 de 2025 = fuente a 15 km (H8). Tabla 2026 (erupción): V375 0,64 a ≤40°, recorte 14,9 % de las detecciones nocturnas |
| (otros) | Isluga (127) | 0,58 | 0,66 | 0,66 | fondo de anillo 22 % alto más conteo; con el fondo de MIROVA, 1,01 a ≤40° (H4) |
| | Planchón-Peteroa (96) | 0,55 | 0,89 | 0,89 | conteo (H7); V750 52 % recortado (H1) |
| | Lastarria (104) | 1,23 | 1,43 | 0,81 | alertamos más que MIROVA; la selección recorta (H3) |
| | Chaitén (37) | 1,18 | 1,34 | 1,31 | sobre MIROVA |

Predicción que separaría cada mecanismo y su prueba: conteo por huella (H2): conteo nuestro que cae con el cenit y el
de MIROVA no, probado. Fondo (H4): con el fondo de MIROVA el déficit desaparece en los de anillo y no en los de kernel,
probado. Selección (H3): a igual región la energía coincide y lo publicado no, probado. Oclusión (H6): cae MIROVA, no
cae más la razón, probado en el patrón. Reparto del foco (H7): la fracción por píxel ~1/N la predicen dos mecanismos;
falta la prueba que los separe.

## 3. Lo que no pude medir

- **VIIRS 750 con Npix y L_bk**: el OSF de 2025 trae 45 pasadas V750 nocturnas en Chile (Láscar 17, Chillán 20, que es
  la fuente de H8). No alcanza para descomponer; lo de V750 sale de la tabla del scraper (sólo VRP).
- **Tupungatito**: no está en el OSF v2.5. **Llaima**: sin alertas de clase 1 en 2025. Para los dos, sólo VRP de la tabla 2026.
- **MODIS, factores de radiancia**: mi reconstrucción del fondo por píxel no reproduce el `diag_L_bg_w_m2_sr_um` de
  MODIS (razón 1,088 de mediana, contra 1,0000 en V375 y V750, `control_reconstruccion_salida.txt`): la λ con que
  convierto `bt_k` no es la del pipeline en MODIS (B21 contra B22, no lo resolví). Las columnas hot_px y bk_px de
  `analizar_MODIS_cls1_salida.txt` **no valen**; el conteo y las energías (que salen del VRP por píxel) sí.
- **El oráculo de MIROVA sobre nuestras escenas**: los records no guardan las matrices M13/M15 remuestreadas, así
  que no se pudo correr `experiments/_s158_oraculo_mirova/mirova_v750.py` sobre ninguna pasada chilena. Separar
  remuestreo de PSF (H7) y confirmar el mecanismo de H2 lo pide.
- **La ley de área de la huella con el cenit**: no la ajusté; el conteo cae del orden de lo esperable, pero no medí la
  curva teórica contra la observada.
- **Los píxeles más allá del top 100**: no hubo ninguna pasada pareada con más de 100 alertados, así que no limitó nada.

## 4. Fuera de alcance

- `scraper2026.py` usa una columna llamada `clip` que choca con el método de pandas al imprimir ejemplos
  (`clip_v750_salida.txt` muestra el objeto en vez del número); los valores están en la tabla de arriba de la misma
  salida. Defecto mío, sin efecto en los números.

## 5. VERIFICADO LIMPIO

| qué | contra qué vara | comando y resultado |
|---|---|---|
| El pareo pasada a pasada OSF 2025 contra nuestros records es la misma pasada | cenit del OSF contra `sensor_zenith_deg` | `descomp_osf2025_salida.txt`: |Δcenit| mediana 0,067° (V375, 2.218 pares), p95 0,54°; MODIS 0,059° |
| k·A de MIROVA: 2.531.250 (V375), 11.081.250 (V750), 18.900.000 (MODIS), en todas las filas de 2025 | datos del OSF; para V750 además el código (`MIROVA_VIIRS750_VRP.m:88-91`) | `descomp_osf2025_salida.txt`, min = max en los tres; coincide con 18,0 × 140.625, 19,7 × 562.500 y 18,9 × 10⁶ |
| Coeficiente de Vulcano V375 igual | OSF jepv6 | `jepv6_exceso_por_pixel_salida.txt`: 2.531.250 en las 354 |
| Nuestro fondo por píxel se reconstruye exacto desde `bt_k` y `vrp_mw` (V375, V750) | `diag_L_bg_w_m2_sr_um` persistido | `control_reconstruccion_salida.txt`: 1,0000 de mediana, p5 0,9994 y p95 1,0005 en V375 |
| La descomposición es consistente | identidad R_esc = R_N × exc_px | `analizar_V375_cls1_salida.txt`: error relativo máximo 3,3 × 10⁻¹⁶ |
| Los records de 2025 son de K | `regimen.codigo_sha` | sha `3695f675` (#852, reproceso histórico con K) en 2.932 a 3.819 records de 2025 por volcán; Chillán tiene además 1.225 con `57d18ad7` y 217 con `cd372013`, los dos descendientes de #850 (`git merge-base --is-ancestor 34cea39e <sha>`) |
| En V375 el recorte ΔL ≥ 0 no actúa en las pasadas en que MIROVA alertó (clase 1) | píxeles con VRP 0 | `analizar_V375_cls1_salida.txt`, `clipfrac` 0,0 en todas las filas |
| Los volcanes con kernel local no se recortan en V375 | control positivo de H1 | `recorte_todos_salida.txt`: 0,0 % en Chaitén, Lastarria, Planchón-Peteroa, Cordón Caulle y Villarrica |
| Nuestro píxel más caliente es el mismo que el único de MIROVA cuando MIROVA alerta uno | L_hot | `mismo_k_salida.txt` bloque 2: 1,036 de mediana a ≤40°, 1,025 a >40° (V375) |
| La ventana del scraper | `scripts/calidad_referencia_mirova.py` (A119) | `scraper2026_salida.txt`: avisos impresos, sólo la tabla; 1.281 alertas, 2 sin record |
