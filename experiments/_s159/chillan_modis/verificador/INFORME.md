# S159, verificador con contexto limpio del frente «Chillán MODIS»

Fecha 2026-10-21. Sólo lectura: no toqué `pipeline/`, `data/` ni `frontend/`, no hice git ni despaché workflows. Mis
scripts están en esta carpeta (`v1_pixeles.py`, `v2_geometria.py`, `v3_estrato.py`) con su salida al lado. Trabajé sobre
los jsonl ya bajados de los runs 39692725826 y 39693552091 (`..\resultado\`) y sobre el código de hoy.

Antes de leer el informe enumeré estos caminos de ruptura: (a) que el probe no corra producción (flags leídos del YAML,
otro código, otro gránulo, el `geo_path` que producción sí pasara); (b) que el «mejor píxel» esté elegido después de
mirar; (c) que el umbral salga de otra sección o de otra rama; (d) que los contrafactuales cambien más de un factor o no
el que dicen; (e) que la geolocalización ponga el «píxel de cumbre» en otro lugar; (f) que el estrato dependa del loader
local o de una copia atrasada de la referencia.

## Control de que el probe es producción

- Pregunta 1: si el probe no corriera producción, el `t_bg`, μ y σ del dNTI no coincidirían exactos con el record
  publicado. Pregunta 2: con el probe muerto los campos salen `None` y el script lo declara SIN DATO.
- `git diff origin/main HEAD -- pipeline/` en `C:\vrp-trabajo\s159-pruebas`: vacío. Flags leídos de `pipeline.profile`
  con `VRP_PROFILE=mirova_equivalent` (no del YAML): `ENABLE_TESTS_23_PROSE_BRANCH True`, `ENABLE_MODIS_B22_PRIMARY
  True`, `C2_DNTI_SUMMIT_NIGHT 5.0`, `DNTI_CONTEXTUAL_C1_SUMMIT 0.003`, `NTI_BT_SANITY_K 3.0`, `BG 5.0 a 25.0`,
  `CLOUD_MASK_BT_K 0.0`, `ENABLE_SECOND_PASS_CONDITIONED False`, `ENABLE_DAYTIME_MODIS False`.
- `calculate_vrp` ignora `geo_path` (`pipeline/process_modis.py:513`), así que pasar el L1B dos veces, como hace el
  probe, equivale a lo que hace `scripts/run_pipeline.py:235-245`. Los argumentos por volcán son los mismos.
- Reejecuté `analizar.py` sobre el jsonl de 39693552091: salida idéntica a la guardada salvo la línea de cabecera del
  perfil. Reejecuté `resumen.py` (nulo entre runs, 0 diferencias en 12 campos × 7 gránulos) y `publicacion.py` con node
  (salida idéntica, identidad del predicado `([0, 1, 1, 1, 0], [1, 0])`).
- Los 7 records objetivo son iguales en `origin/main` (commit `1f0b47570`) y en el checkout: 0 de 1.360 records MODIS
  difieren en `primary_cluster`, primer pase, `t_bg_k` o clase; el único cambio es un gránulo del 2026-10-21 01:40.

## Veredicto por afirmación

### 1. Test 2: CONFIRMADA (con un matiz de geometría, ver 7)
- `v1_salida.txt`: T1 μ = −0,00006, σ = 0,00390, μ + 5σ = 0,01944 > C1 = 0,003 (rige la rama estadística, porque
  `combinar = max`, `pipeline/detection_context.py:525`); el mejor píxel tiene dNTI 0,01469, z = +3,78. T2: σ = 0,00369,
  umbral 0,01833, dNTI 0,01362, z = +3,72. Recalculé el umbral desde μ y σ guardados y coincide con el del píxel.
- No depende de qué píxel se llame «mejor»: en T1 **0 de 28** píxeles a 5 km o menos pasan el Test 2, y en T2 **0 de
  32** (`v1_salida.txt`, bloque v1b). El criterio del mejor píxel estaba sellado en `PREREGISTRO.md` antes del dato.
- Test 3 pasa en el mejor píxel: 0,01249 contra 0,00960 (T1) y 0,01375 contra 0,01006 (T2).

### 2. Compuerta de 3 K: PARCIAL
- Aritmética CONFIRMADA: BT MIR del mejor píxel menos `t_bg` = −3,70 K (269,23 contra 272,94) y −4,37 K (268,69 contra
  273,06); con el `t_bg` de C1 (265,30) daría +3,93 y +3,39, o sea pasaría. TIR del píxel más cercano al cráter menos
  mediana del anillo: −9,69 y −12,35 K (`resumen.py`).
- La causa física («la cumbre nevada está más fría que el anillo») queda SOSPECHA, no medida: los píxeles se ubican con
  una geolocalización que en estas pasadas está comprimida (punto 7), así que «el píxel del cráter» de T1 no es
  necesariamente el que contiene el cráter, y la nube no se descartó.
- La compuerta no decide la detección: el segundo pase corre sin condicionar y sin compuerta (`pipeline/process_modis.py`
  bloque `second_pass_adjacent`, `conditioned=False`). Su falla es un hecho, no una causa.

### 3. Saturación, banda, σ y nube descartadas; «sólo min más sin compuerta juntos»: PARCIAL
- CONFIRMADO: 0 DN > 32767 en bandas 21 y 22 a 4 km (21 píxeles en T1, 18 en T2; BT22 máxima 276,06 y 270,01 K). B21
  primaria da 0 dentro del inner; el contrafactual cambia los cinco consumidores del flag en `process_modis.py`
  (l. 593, 597, 600, 601, 614), así que no es un cambio a medias. F4 (σ de los controles, 0,00355) deja z en 4,15, bajo 5.
  `CLOUD_MASK_BT_K = 0.0`.
- Lo que NO se sostiene tal como está resumido: F2 aplica `min` **sólo al primer pase**, una configuración que no existe
  en producción, porque el flag `ENABLE_TESTS_23_PROSE_BRANCH` gobierna los dos pases (l. 942 y 996). El brazo MIN, que es
  el flag de verdad, detecta dentro del inner por sí solo: 2 píxeles nuevos en T1 y 3 en T2, cúmulo `summit` a 3,40 y
  0,92 km (`publicacion_salida.txt`). Para la DETECCIÓN, la conectiva sola es causa suficiente; la compuerta sobra. Para la
  PUBLICACIÓN ninguna basta (punto 4). El informe lo dice en su adenda, pero la frase del encargo invierte la lectura.

### 4. Magnitud 0 MW: CONFIRMADA
- Brazos MIN y MINSC: `pc.vrp_mw` = 0,0, clase `summit`, predicado del tablero «no publica» (rerun con node idéntico).
- Mecanismo leído: Chillán no tiene `local_kernel_bg` en `volcanoes.yaml:245-269` (sí `lbg_global_compatible: true`, que
  es del Test 1), así que `L_bg = L_bg_global` del `t_bg` del anillo y `delta_L = np.maximum(hotpix_rad - L_bg, 0.0)`
  (`pipeline/process_modis.py:1083` y `:1118`). `ENABLE_LOCAL_CLUSTER_MAGNITUDE = False`, no hay corona que lo cambie.
  BT del píxel bajo `t_bg` da 0.

### 5. Controles: CONFIRMADA
- Réplica idéntica a producción en primer y segundo pase, 7 de 7 (líneas «CONTROL instrumento»); no es trivial porque en
  C1 a C3 la máscara no es vacía. Record reproducido en 6 de 7 con `t_bg`, μ y σ en diferencia relativa 0,0; E2 no
  reproduce (μ dNTI 0,057 relativo). C1, C2 y C3 «pasan las cuatro». Matiz: ningún control positivo está a ~58°; el más
  oblicuo es C2 (54,0°), y E2 (62,8°) publica sólo por el segundo pase.

### 6. Estrato: CONFIRMADA, por un camino independiente
- `v3_estrato.py` lee los CSV **remotos** de Mirova-v1 bajados hoy (no el loader unificado ni la copia local) y el JSON
  publicado. Ventana 2026-09-01 a 2026-10-21, Chillán MODIS: 211 pasadas, 17 con alerta, **16 protegidas**: 11 con
  cúmulo `summit` de magnitud mayor que 0, 2 con record y cúmulo nulo (2026-10-12 07:20 y 2026-10-15 01:05), 3 sin record
  a ±5 min, a las ~10, ~09 y ~17 h locales (diurnas). Coincide con `estrato_salida.txt`. Nota: el «22 de alerta» del
  informe cuenta filas (CONS más OCR); en pasadas son 17. «Publicada» en mi script es un proxy, el predicado real es node.

## Lo propio

### 7. La geolocalización con que se eligen los píxeles está comprimida en estas pasadas
- `v2_salida.txt`: distancia en tierra entre filas consecutivas de los píxeles que usa producción: T1 mediana **0,40 km**
  (mínimo 0,31), T2 0,81, E1 1,56, C3 (nadir) **1,00** (control positivo). Un detector MODIS nunca está a 0,3 o 0,4 km
  del siguiente; es la interpolación lineal de la grilla de 5 km (`_interp_geo`, `pipeline/process_modis.py:292` y
  `:385`) que ignora el bow tie. El frente M ya midió con MxD03 que el cráter se mueve 5,75 km en T1 y 1,50 km en T2
  (`experiments/_s159/m/analizar_m_salida.txt` l. 96 y 20, que leí, no rehice).
- Efecto sobre este frente: la detección no cambia (el frente M da primer pase 0 también con MxD03), pero el «píxel de
  cumbre a 3,47 km», el «píxel del cráter» con TIR −9,7 K y los vecinos «a 0,3 km» con 12 a 17 K de diferencia están en
  una geometría que no es la real. La narrativa física de la afirmación 2 descansa en eso. CONFIRMADO que la geometría
  está comprimida; SOSPECHA que explique los contrastes de BT. Gravedad 2 para este frente (el defecto de fondo ya está
  registrado desde S151).

### 8. La lectura correcta de los contrafactuales, para quien decida
Con la conectiva `min` en los dos pases T1 y T2 se detectan, y se pierden en la magnitud por el fondo escalar del anillo.
Un A/B que mida sólo el primer pase, o sólo la compuerta, no ve ninguna de las dos cosas. Gravedad 2.

## VERIFICADO LIMPIO
- Probe igual a producción: `git diff origin/main HEAD -- pipeline/` vacío; flags desde `pipeline.profile`.
- Salidas reproducibles: `analizar.py`, `resumen.py` y `publicacion.py` rerun con salida idéntica.
- Records objetivo frescos contra `origin/main`.
- Estrato contra la referencia remota: `python experiments/_s159/chillan_modis/verificador/v3_estrato.py <dir con CSV>
  data/mirova_equivalent/NevadosDeChillan.json`.
- Umbral y z por píxel: `python experiments/_s159/chillan_modis/verificador/v1_pixeles.py
  experiments/_s159/chillan_modis/resultado/run39693552091/probe_chillan.jsonl`.

Temporales en `D:\vrp-trabajo\temporales\s159_chillan_verif\` borrados al terminar.
