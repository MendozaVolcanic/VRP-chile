# Auditoría S173: qué pieza corrige la caída con el cenit en VIIRS 375, Nevados de Chillán

## 1. Encabezado

- Hora del servidor: inicio Tue, 03 Nov 2026 00:42:13 GMT; última medición 00:52:02 GMT (header `Date` de la API de
  GitHub, `s00_salida.txt`).
- Commits medidos: `origin/main` 5de08ebf62d1ea092c485c0a030f323f2cbdcf2a (records K, referencia de MIROVA, pipeline/,
  frontend/, scripts/; copia por `git archive` en `C:/Users/nmend/vrp-wt/s173_cenit/v375/repo/`, borrada al terminar);
  `origin/loop/activo` ddd83c5b9 (antecedente S172 y experimentos de V375); tag `s172-v375e-lector-resellado`
  (fc3912cb2, lector sellado, sólo leído).
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: bajo, el que fijó la configuración de esta sesión (no lo elegí).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/v375/`
- Qué NO miré: MODIS y VIIRS 750; los otros diez volcanes; gránulos L1B (no bajé nada); el día; el record K que el probe
  corrió sobre cada gránulo (está en los lotes, no lo comparé contra producción); el fondo de MIROVA en los TIF; ningún
  paper; no re-corrí el lector sellado de V375-E ni sus mutaciones; no leí `detectar_mirova` línea por línea (sólo su
  firma y lo que dice el pre-registro que acopla).

## 2. En una pantalla

1. En las mismas 27 pasadas de Chillán (2026-09-28 a 2026-10-16), K cae con el cenit (0,75 bajo 30°, 0,56 sobre 30°,
   Spearman −0,52 fuera del barajado) y V375-E no (0,92 / 1,00, Spearman +0,28 dentro del barajado); V375-E / K sube
   de 1,21 a 1,76 (Spearman +0,56). La pieza que corrige la caída oblicua está dentro de la vía.
2. La sombra de V375-E no tiene ni un record (`data/sombra_codigo_mirova/` no existe en main; parte el 2026-11-03 a las
   15:00 UTC). Todo lo anterior sale de los lotes retrospectivos, no de la sombra.
3. La caja no es la pieza (los seis brazos de ROI dan lo mismo). El fondo cero no aplana a K (0,98 a 0,67); el factor
   de área sí (0,80 a 0,95), y los alertados de la vía crecen con el cenit (6 a 11) mientras los de K no: firma de
   remuestreo (D17), SOSPECHA hasta una ablación.
4. No existe ninguna salida por pasada que aísle remuestreo, fondo, media 3 × 3, umbrales o compuerta en VIIRS 375.
   Las piezas posteriores al remuestreo se pueden ablacionar en local sobre las grillas ya guardadas; el remuestreo
   solo necesita los gránulos.
5. Ojo con el nombre: en el catálogo D25 es el fondo de anillo, no la geometría del borde.

Informe: `C:/Users/nmend/vrp-wt/s173_cenit/v375/INFORME.md`

## 3. El fenómeno, antes que el número

Cuando VIIRS mira Chillán de lado, el píxel de 375 m del barrido se estira en el terreno. El domo no cambia: su
potencia es la misma, pero queda repartida en un píxel más grande, así que la radiancia de ese píxel baja. Si uno
multiplica esa radiancia diluida por el área NOMINAL del píxel, como hace K (área nadir fija), pierde energía en
proporción a cuánto se estiró. MIROVA no trabaja sobre el barrido: interpola cada gránulo a una grilla fija de celdas
de 375 m. Un píxel oblicuo grande cubre varias celdas, cada una recibe su radiancia diluida, y al sumar todas las celdas
alertadas la energía vuelve. Ésa es la hipótesis D17. La competidora es el fondo: si K resta un fondo más tibio que
MIROVA, pierde magnitud, pero eso debería pasar igual de nadir y de lado salvo que el fondo empeore hacia el borde.

Lo que se ve en los datos: con el mismo gránulo y el código de MIROVA, la razón queda en 1 a todos los ángulos; con K
cae. Y lo que crece con el ángulo en la vía es el número de celdas alertadas, no la diferencia de fondo, que es casi
constante (unos 7,6 K más tibio el anillo de K que el fondo bajo el halo de la vía, en todos los tramos). La
diferencia constante de fondo encaja con el déficit que K tiene incluso cerca del nadir (0,75); el crecimiento de
celdas encaja con la caída oblicua.

## 4. Mediciones (cada una con sus dos preguntas)

Todas las razones son por pasada: VRP publicado (predicado del tablero ejecutado con node, `banco_paridad.cargar_nuestros`)
sobre el VRP de la fila ALERTA de MIROVA de la misma pasada (±120 s, D-9 SN, unión CONS+OCR, CONS si existe). Cenit =
`sensor_zenith_deg` del record de K (el de la vía difiere a lo más 1,59°, `s02_v375e_resumen.json`). Barajado: 200,
semilla 173, dentro del sensor (VIIRS 375).

### s00, ¿hay sombra? (`s00_sombra_existe.py`, `s00_salida.txt`)
- P1: el mismo `ls-tree` encuentra `data/mirova_equivalent/NevadosDeChillan.json` (control positivo). P2: la API de
  GitHub sobre el remoto da 404 para la carpeta de la sombra (no es un checkout atrasado, regla 5 del workspace).
- Resultado: la carpeta no existe; el lector sellado fija `DESDE_P = "2026-11-03"`; el workflow corre a las 15:00 UTC y
  hasta el 2026-11-03 sale sin ventana. Ventana real de la sombra: vacía; n = 0.

### s01, K de producción por pasada (`s01_pareo_k_s172.py`, copia sin cambios de `s02_pareo_por_pasada.py` de S172)
- Ventana 2026-04-01 a 2026-11-02; salida `s01_k_resumen.json`, `s01_k_pasadas.csv`.
- P1: ×2 dobla la mediana (0,548 a 1,095); identidad del predicado `[0,1,1,1,0]`, `[1,0]`; lectura directa del JSON
  contra node: 0 diferencias. P2: con la referencia corrida un día quedan 14 pares (el límite que S172 ya describió:
  órbita repetida dentro de ±120 s), contra 66.
- VIIRS 375: 941 pasadas nocturnas, 73 con alerta, 66 pares, razón 0,548; reproduce el antecedente (S172: 0,571 con 53
  pares hasta el 2026-10-26).

### s02, V375-E por pasada desde los lotes (`s02_v375e_retro.py`, `s02_v375e_resumen.json`, `s02_v375e_pasadas.csv`)
- Corre `mirova_v750_codigo.procesar_grilla` de main con `caja_v375` sobre las grillas guardadas de los lotes S159,
  S162, S162b y FAR (las del lector sellado), y pasa el record por node. Ventana de los lotes en Chillán: 2026-04-01 a
  2026-10-21; 248 pasadas únicas, 62 con alertados de la vía, 29 con alerta de MIROVA.
- P1: contra el C13 que guardó el probe (brazos.py, otra implementación): 46 pares, 33 iguales a 1e-3 MW, 13 distintos
  (`s02b_control_c13_detalle.txt`, CV375-08); node contra el `vrp_mw` del record de la vía: 33 publicadas, diferencia 0.
  P2: si las grillas no se leyeran, «via_con_pixeles» sería 0; da 62, y se cuentan las faltantes por lote (0 sin grilla,
  14 con estado no ok).

### s03, estratos por cenit (`s03_estratos_cenit.py`, `s03_salida.json`, `s03_salida.txt`)
- P1: control positivo de pendiente: multiplicar la razón de K por cos²(z) lleva el Spearman de −0,548 a −0,880, fuera
  del barajado; ×2 dobla la mediana. P2: rango del barajado impreso al lado de cada Spearman; con n < 8, SIN DATO.

| conjunto (ventana de los pares) | n | z < 30 | z ≥ 30 | z ≥ 50 | Spearman | barajado 95 % |
|---|---|---|---|---|---|---|
| A: K producción (2026-09-28 a 2026-11-02) | 66 | 0,745 (16) | 0,481 (50) | 0,347 (30) | −0,548 | [−0,202; 0,298] |
| B: K, mismas pasadas que la vía (2026-09-28 a 2026-10-16) | 27 | 0,753 (7) | 0,562 (20) | 0,506 (11) | −0,515 | [−0,432; 0,333] |
| B: V375-E publicada | 27 | 0,922 (7) | 1,000 (20) | 1,000 (11) | +0,283 | [−0,343; 0,327] |
| B: V375-E / K | 27 | 1,205 (7) | 1,758 (20) | 1,788 (11) | +0,556 | [−0,399; 0,438] |
| ROI, brazos M14 = C13 = C21 = CIRC = SENS | 14 | 0,908 (3) | 1,002 (11) | 1,002 (6) | +0,068 | [−0,525; 0,556] |
| ROI, PIX7 | 14 | 0,908 (3) | 1,000 (11) | 0,959 (6) | −0,116 | [−0,525; 0,565] |

En B las 27 pasadas son las mismas en las tres filas (B y B' coinciden: ninguna alerta con vía positiva quedó sin
publicar). Por plataforma, K cae en las tres (NOAA-20 −0,56, NOAA-21 −0,56, Suomi NPP −0,55, cada una fuera de su
barajado).

### s04, firmas de pieza en salidas existentes (`s04_firmas_por_cenit.py`, `s04_salida.json`, `s04_salida.txt`)
- P1: si los conteos no se leyeran saldría n = 0 por tramo; control: cerca del nadir la vía y K ven la misma escena y
  los conteos son del mismo orden (6 contra 3). P2: Spearman con barajado, igual que s03.
- Vía y K, mismas 27 pasadas: alertados de la vía 6 / 7,5 / 11 (z < 30 / ≥ 30 / ≥ 50), Spearman +0,534 fuera de
  [−0,426; 0,417]; píxeles de K con VRP > 0: 3 / 2 / 3, Spearman +0,146 dentro. Fondo del anillo de K menos fondo bajo
  el halo de la vía (en temperatura de brillo de I4): 7,43 / 7,66 / 7,63 K, Spearman −0,007.
- Techos de la tarea 1.33 (`experiments/_s157_magnitud_chillan/a_pasadas_salida.json` en main, ventana 2026-09-18 a
  2026-10-20, generada 2026-10-20 03:59 UTC, 44 positivas V375), partidos por mí: G 0,730 / 0,548 (Spearman −0,429);
  con fondo cero G_fondo0 0,983 / 0,669 (−0,363, barajado [−0,323; 0,299]); con factor de área G_area 0,802 / 0,948
  (+0,235, dentro).

## 5. Hallazgos (orden por gravedad)

### CV375-01
- TÍTULO: V375-E queda plana con el cenit en Chillán y K cae: la pieza que corrige la caída oblicua está dentro de la vía
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_estratos_cenit.py` : `s03_salida.json` (`B_K`, `B_via_publicada`, `B_via_sobre_K`, `detalle_Bp`)
- QUÉ PASA: sobre el mismo gránulo y la misma pasada, el código de MIROVA reproduce el VRP de MIROVA a cualquier ángulo
  (0,92 bajo 30°, 1,00 sobre 30° y sobre 50°), mientras K pierde energía al mirar de lado (0,75 a 0,51). La ganancia de
  la vía sobre K crece con el cenit (1,21 a 1,79; peores casos 5,2 a 8,0 a 62 a 66°, p. ej. Suomi NPP 2026-10-10 04:54,
  z 65,5°: K 0,76 MW, vía 6,06, MIROVA 5,72). Lo que no dice: cuál de las piezas acopladas de la vía lo hace.
- CÓMO SE VE EN EL DASHBOARD: con K, una pasada oblicua de Chillán aparece hasta ocho veces más baja que MIROVA; con la
  vía no.
- CÓMO REPRODUCIRLO: `python -B s01_pareo_k_s172.py <repo> 2026-04-01 2026-11-02 s01_k`; `python -B s02_v375e_retro.py
  <repo> s01_k_pasadas.csv s02_v375e`; `python -B s03_estratos_cenit.py s01_k_pasadas.csv s02_v375e_pasadas.csv
  s03_salida.json` (con `<repo>` = `git archive origin/main scripts frontend pipeline volcanoes.yaml data/mirova_reference
  data/mirova_equivalent/NevadosDeChillan.json`). NdC VIIRS_SNPP 2026-10-10 04:54 UTC.
- CONFIANZA: CONFIRMADO (medido; n 27, retrospectivo, no la sombra)
- GRAVEDAD 1-5: 4 (decide la palanca: no está en el tablero ni en la caja, está en el procesamiento de la vía)

### CV375-02
- TÍTULO: La sombra V375-E no tiene ningún record; la razón de la sombra por pasada es SIN DATO
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s00_sombra_existe.py` : `s00_salida.txt`; `.github/workflows/sombra-codigo-mirova.yml`
  (cron `0 15 * * *`, comentario «hasta el 2026-11-03 cada job sale en segundos porque ventana_sombra.py no devuelve
  ventana», TEXTO)
- QUÉ PASA: el encargo supone records de la sombra desde octubre en `data/sombra_codigo_mirova/NevadosDeChillan.json`;
  esa carpeta no existe en `origin/main` ni en el remoto. Los runs verdes del 30-oct al 2-nov no producen datos por
  diseño (no es un zombie). El primer dato llega como pronto el 2026-11-03 tras las 15:00 UTC, y sin Suomi NPP.
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no la lee el tablero).
- CÓMO REPRODUCIRLO: `python -B s00_sombra_existe.py "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 3 (quien lea «V375-E en la sombra» creyendo que hay datos interpreta un cero como medición)

### CV375-03
- TÍTULO: El remuestreo deja su firma: los alertados de la vía crecen con el cenit, los de K no, y la diferencia de fondo es constante
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s04_firmas_por_cenit.py` : `s04_salida.json` (`npix_via_por_tramo`, `npos_K_por_tramo`, `tbgK_menos_tbgvia_K`)
- QUÉ PASA: al interpolar el píxel oblicuo grande a celdas fijas, la vía alerta más celdas cuanto más de lado mira (6 a
  11, Spearman +0,53 fuera del barajado); K no cambia su conteo (3 / 2 / 3). El fondo de K es unos 7,6 K más tibio en
  todos los tramos (Spearman −0,007): explica parte del déficit del nadir, no la pendiente. Está en tensión con
  `experiments/_s151_presupuesto_magnitud/README.md` §3.2 (TEXTO, l. 80): «**No crece**: medianas de 3, 5, 5 y 4 en las
  cuatro bandas», medido sobre el Npix del OSF 2025 de varios volcanes, que es otra población; en Chillán en erupción
  la vía que reproduce a MIROVA sí crece. Por qué es SOSPECHA: el conteo de la vía cambia también por los umbrales, la
  media 3 × 3 y la compuerta, no sólo por el remuestreo; y las dos temperaturas de fondo no son la misma magnitud
  (mediana del anillo contra fondo interpolado bajo los alertados).
- CÓMO SE VE EN EL DASHBOARD: invisible (explica CV375-01).
- CÓMO REPRODUCIRLO: `python -B s04_firmas_por_cenit.py s02_v375e_pasadas.csv s01_k_pasadas.csv _s157_a_pasadas.json s04_salida.json`
- CONFIANZA: SOSPECHA (la firma está medida; la atribución a D17 no)
- GRAVEDAD 1-5: 3

### CV375-04
- TÍTULO: Con fondo cero K sigue cayendo con el cenit; con el factor de área se aplana
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s04_firmas_por_cenit.py` : `s04_salida.json` (`s157_G_fondo0`, `s157_G_area`, `s157_f_area`)
- QUÉ PASA: en la salida por pasada de la tarea 1.33, aun suponiendo que el fondo es cero (el techo de cualquier
  arreglo de fondo, D25 incluido) nuestros píxeles dan 0,98 de MIROVA cerca del nadir y 0,67 sobre 30°: el fondo no
  puede cerrar la brecha oblicua. Con el factor de área del modelo geométrico (cuánto se estira el píxel) la razón pasa
  a 0,80 / 0,95, sin pendiente. Es el patrón de D17. El factor de área es un modelo (techo), no una medición del
  remuestreo, y la ventana (2026-09-18 a 2026-10-20) es la de esa tarea, con los records de ese día.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: como CV375-03.
- CONFIANZA: CONFIRMADO el número; el mecanismo es SOSPECHA
- GRAVEDAD 1-5: 3

### CV375-05
- TÍTULO: La caja o ROI no es la pieza en Chillán
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_estratos_cenit.py` : `s03_salida.json` (`ROI_brazos_sobre_MIROVA`)
- QUÉ PASA: en Chillán el cráter cae en el centro de la grilla de MIROVA (0,00 km, log del probe de S162) y el domo
  queda dentro de cualquier caja: M14, C13, C21, CIRC y SENS dan la misma razón en los tres tramos (n 14), PIX7 casi
  igual. Cambiar la caja no mueve la magnitud.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: como CV375-01; el detalle por brazo está en las columnas `br_*` de `s02_v375e_pasadas.csv`.
- CONFIANZA: CONFIRMADO (sólo Chillán y los lotes con brazos, S162 y FAR)
- GRAVEDAD 1-5: 3 (descarta una palanca)

### CV375-06
- TÍTULO: El encargo llama D25 a la geometría del borde; en el catálogo D25 es el fondo del anillo con recorte a cero
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `docs/MIROVA_DIVERGENCES.md:2861` (origin/main), TEXTO: «D25: El fondo del VRP es la
  mediana de un anillo regional de 5 a 25 km, no la media de los píxeles que rodean al activo; y el exceso se recorta a cero.»
- QUÉ PASA: la pregunta «remuestreo (D17) o geometría del borde (D25)» mezcla dos cosas. Según lo medido aquí, el fondo
  (D25 de verdad) explica el residuo del nadir y no la pendiente (CV375-03 y 04). Lo que en el borde depende de la
  geometría es justamente D17 (área y remuestreo), y además el «cuenta doble en el borde» de AUDIT_S155 F5-09 citado en
  `docs/SINTOMAS.md` §1. Si se decide la palanca con el nombre del encargo, se puede elegir D25 creyendo elegir geometría.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show origin/main:docs/MIROVA_DIVERGENCES.md | sed -n 2861p`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 3

### CV375-07
- TÍTULO: No existe ninguna salida por pasada que aísle remuestreo, fondo, media 3 × 3, umbrales o compuerta en VIIRS 375
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `pipeline/mirova_v750_codigo.py` l. 198, 322, 397, 584 a 605, 687 (origin/main);
  `experiments/_s162_v375/brazos.py` (sólo ROI); `s172/v375e_PREREGISTRO_E.md` l. 56 a 59
- QUÉ PASA: el pre-registro lo dice, TEXTO (copia de `experiments/_s172_chillan/auditor/v375e_PREREGISTRO_E.md` l. 59):
  «La atribución pieza a pieza no es de aquí: va en ablaciones locales sobre las grillas guardadas.» Las únicas
  salidas por pasada que existen son los brazos de ROI (CV375-05) y los techos de 1.33 (CV375-04, del lado de K). Lo
  que haría falta está en la sección 6.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git ls-tree -r origin/loop/activo experiments/_s162_v375/`; ramas `s162-v375*`, `s166-v375e*`.
- CONFIANZA: CONFIRMADO (búsqueda en loop/activo, main y las ramas nombradas; no recorrí todas las ramas del repo)
- GRAVEDAD 1-5: 2

### CV375-09
- TÍTULO: La vía publica dos alertas débiles de MIROVA que K calla
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.txt` (bloque `via_pub_K_no`)
- QUÉ PASA: NOAA-21 2026-08-20 05:12 (z 43,1°, MIROVA 0,06 MW, vía 0,073) y Suomi NPP 2026-09-05 05:48 (z 9,2°, 0,14
  contra 0,196). Son de la clase CH172-06 (K tiene el píxel con VRP 0). No entran a ninguna razón.
- CÓMO SE VE EN EL DASHBOARD: con K, noche sin punto VIIRS 375 cuando MIROVA marcó una alerta bajo 1 MW.
- CÓMO REPRODUCIRLO: como CV375-01.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### CV375-08
- TÍTULO: La vía re-corrida y el C13 del probe difieren más de 1e-3 MW en 13 de 46 pasadas
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02b_control_c13_detalle.txt`
- QUÉ PASA: 9 son de 1 a 4 píxeles (lo que el pre-registro §8.6 b atribuye al relleno de MATLAB contra el port viejo;
  la mayor, 0,32 contra 0,41 MW, 2026-05-31 06:24), pero 4 tienen 5, 8, 11 y 14 píxeles (diferencias bajo 1 %). Ninguna
  de las 13 es una alerta de MIROVA del conjunto B salvo 2026-09-29 06:00 (3,919 contra 3,928) y 2026-10-05 06:24
  (8,464 contra 8,461), y no mueven las medianas. No verifiqué si las de más de 4 píxeles salen también del relleno.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B s02_v375e_retro.py <repo> s01_k_pasadas.csv s02_v375e`
- CONFIANZA: SOSPECHA
- GRAVEDAD 1-5: 1

## 6. Objetivo 2: piezas que separan a V375-E de K y qué correr para aislarlas

Piezas leídas en origin/main (TEXTO): la vía es otro camino entero, no un cambio dentro de K
(`pipeline/process_viirs.py` l. 766 a 787 (retorno en l. 786): si el flag está encendido y hay grilla, llama a
`_MV.calcular_vrp_granulo` y retorna).

| pieza | V375-E (`pipeline/mirova_v750_codigo.py`) | K | ¿salida por pasada existente? |
|---|---|---|---|
| remuestreo a grilla fija (D17) | `remuestrear_grilla` l. 198, `griddata` lineal a 134 × 134 celdas de 375 m | barrido nativo, área nadir fija (`resolve_viirs_pixel_areas`, `process_viirs.py` l. 803) | no |
| caja / ROI | `caja_v375` l. 296, C13 en el cráter | círculo de `inner_radius_km` | sí, brazos V375-C (CV375-05) |
| media de contraste | `_media_3x3_omitnan` l. 322, 3 × 3 con el central | 8 vecinos | no |
| umbrales y pasadas | `detectar_mirova` l. 397 (umbrales del `.m`, Test 1 como alerta, segundo pase con regresión recalculada) | dual-ROI, `max`, sin Test 1 integrado | no |
| compuerta de 3 K (D22) | no tiene | sí salvo flag (`process_viirs.py` l. 1271 a 1274, 1357 a 1359) | no |
| fondo (D25) | `vrp_mirova` l. 584: halo de 3/5/7 celdas, `fillmissing2`, sin recorte (l. 600 a 605) | anillo regional, recorte a cero | no (sólo techos de 1.33, CV375-04) |
| qué se suma (D32) | todos los alertados (`procesar_grilla` l. 687, sin modo de un píxel ni tope D9) | núcleo F5 del cúmulo | no |
| coeficiente | 18,0 × 0,140625 (l. 85) | el mismo (Reglas científicas, S14) | no hace falta |

Qué haría falta correr:

1. Piezas posteriores al remuestreo (fondo, suma, 3 × 3, umbrales, compuerta): un script local sobre las grillas que
   ya están en disco (`C:/vrp-trabajo/temporales/s162_v375/run_40116289866`, `run_40131572769`,
   `D:/vrp-trabajo/temporales/s159_portes/run_39712862945`, `D:/vrp-trabajo/temporales/s167_v375e_far/run_40773794395`),
   reemplazando de a una la pieza de la vía por la de K en una copia de `procesar_grilla` (no en pipeline/), sobre las
   27 pasadas de B, partido en z < 30 / ≥ 30. Sólo numpy, scipy y pyproj (los tengo: 2.4.4, 1.17.1, 3.7.2), sin pyhdf
   (VIIRS es netCDF) y sin bajar nada; disco: sólo salidas, unos MB. Advertencia: el fondo de anillo de K sobre la
   grilla no es idéntico al de K sobre el barrido (otra geometría de píxeles), así que el brazo «fondo de K» es una
   aproximación y hay que decirlo. Si el fondo de K dentro de la vía no rompe la planitud, el fondo no es la pieza
   oblicua (lo que ya sugiere CV375-04).
2. El remuestreo solo (D17): correr el detector y el fondo de la vía sobre el barrido NATIVO (sin `remuestrear_grilla`,
   con área nadir) y, al revés, K sobre el barrido regrillado (`ENABLE_UTM_REGRID`, F70.2, `process_viirs.py` l. 794 a
   795, con la salvedad de D17 de que F70 no es la grilla de MIROVA). Eso necesita los L1B VJ102IMG/VNP02IMG y
   VJ103IMG/VNP03IMG de las 27 pasadas (lista en `s03_salida.txt`, `detalle_Bp`). Cabe en local sin pyhdf; la bajada
   exige `EARTHDATA_TOKEN`, que esta tarea no me autoriza, o un workflow (despacharlo es decisión de quien orquesta).
   Tamaño por gránulo: SIN DATO (no lo encontré en los logs del probe).
3. Con las dos anteriores, el residuo del nadir (0,75 en K) se reparte entre fondo y suma, y la pendiente se asigna o
   no al remuestreo.

## 7. SEGUIMIENTOS (fuera de mi eje)

- `docs/SINTOMAS.md` §1 retira «El ángulo es D17» apoyándose en 1.14 §3.2 (Npix de MIROVA del OSF 2025 que no crece).
  En Chillán 2026, la vía que reproduce el VRP de MIROVA alerta más celdas con el cenit (CV375-03). No refuta 1.14 en
  su población, pero el retiro no debería leerse como válido para Chillán en erupción. SOSPECHA, gravedad 2.
- El control negativo de S172 (referencia corrida un día) deja 14 pares de 66 en VIIRS 375 (`s01_k_resumen.json`): no es
  un nulo limpio, como ya dijo S172. Gravedad 1.

## 8. VERIFICADO LIMPIO

1. El pareo de S172 se reproduce sobre main de hoy (vara: su propio resumen; 0,548 n 66 contra 0,571 n 53 con ventana
   más corta; identidad del predicado y lectura JSON contra node: 0 diferencias; `s01_k_resumen.json`).
2. La magnitud que publica el tablero para un record de la vía es su `vrp_mw` (vara: node; 33 de 33, diferencia 0,
   `s02_v375e_resumen.json`). Responde la duda de si el tablero recalcula un núcleo F5 sobre la vía: no lo hace.
3. El cenit del record de la vía y el de K difieren a lo más 1,59° en las 248 pasadas (vara: los dos records;
   `s02_v375e_resumen.json`): estratificar por uno u otro no cambia los tramos salvo en el borde de 30°.
4. Los 248 records de la vía son nocturnos para el banco (vara: `es_pasada_diurna_descartada` de banco_paridad).

## 9. SIN DATO

- Razón de la sombra V375-E por pasada y por tramo: n = 0 (CV375-02).
- Ablación pieza a pieza en VIIRS 375: no existe (CV375-07).
- Chillán antes del 2026-09-28: 0 pares con magnitud en los lotes (las alertas de agosto y septiembre son las dos de
  CV375-09, sin par).
- Comparación entre el K del probe (record en cada lote) y el K de producción de hoy.

## 10. FUERA DE ALCANCE

MODIS, VIIRS 750, otros volcanes, reprocesos, descargas, cambios en pipeline/, data/ o frontend/, propuestas de arreglo.
