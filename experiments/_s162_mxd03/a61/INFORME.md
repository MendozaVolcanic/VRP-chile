# Auditoría espacial A61 de las protegidas que MxD03 mueve (S162, MOD-B, §6 P4 del pre-registro)

## En una pantalla

1. **Las 48 protegidas con cúmulo quedan con X a 0,15 a 0,89 km del cráter (mediana 0,34 km), 48 de 48 dentro del inner y 48 de 48 más cerca que con K (0,81 a 3,20 km, mediana 1,58).** En 44 de 48 el cúmulo de X son **los mismos píxeles** que el de K, reubicados (26 por índice del píxel, 18 por residuo < 0,3 km contra el corrimiento del gránulo); en 4 hay reselección de píxeles vecinos del cráter de Láscar (X/K de 0,73 a 0,97). **Ninguna se fue a otro objeto.** La condición del §6 P4 se cumple.
2. **La fuente independiente de la noche lo confirma**: VIIRS 375 de otros gránulos (47 de 48 con referencia, A109): X queda a 0,38 km del objeto VIIRS (mediana; máximo 0,97 km) contra 1,48 km de K, y más cerca en 46 de 47. **MIROVA**: 30 protegidas traen `Distancia_km` 0,0 (misma celda que su referencia) y X está a 0,75 km o menos del cráter en 30 de 30, K en 4 de 30; el GeoTIFF de MIROVA del 2026-05-10 01:25 pone el calor en la celda del cráter, donde cae X y no K (n 1, informa).
3. **Relleno −999**: `_interp_geo` contamina una celda gruesa (5 líneas) a cada lado del bloque (medido en sintético) y donde el bloque toca el ROI **K pierde más píxeles que X** (−142 y −124 de anillo): la frase del seguimiento S-2, «X pierde píxeles que K conserva», queda **invertida**. Además, en 2 de 5.465 records el cráter cae dentro del bloque y los dos detectores escriben un **negativo sobre una escena sin cráter**: el pipeline no tiene estado «sin dato» de geolocalización (gravedad 3, producción).
4. **El corrimiento de producción es el desfase de índice de `_interp_geo`** (+2 píxeles en el frame 0, −1 en el 1353, ±2 líneas en la traza) multiplicado por el ancho del píxel a ese cenit: el modelo reproduce la mediana por frame dentro de 10 %. Máximo real 11,5 km; los 13 a 16 km de VRB-07 son un gránulo con relleno que además trae **cenit de 68 a 75°, imposible para MODIS** (máximo limpio 65,3°).
5. La protegida frágil (Láscar 2026-03-12) se apaga en 5 R porque `final_hotspot_dist_km` se mide desde el **centro** del volcán (0,68 km al sur del cráter) y la etiqueta cruza los 5 km (asimetría A46), no por el fondo; con X queda a 0,55 km y la fragilidad desaparece. El control del módulo de R con un tope de 20 km marca exactamente el único record absurdo. **Nada de esto mueve el CUMPLE SIN DAÑO.**

## Encabezado

- **Hora del servidor** (GitHub, header `Date`, A86): domingo 25 de octubre de 2026, 02:10:27 GMT al empezar; 02:27:16 GMT al terminar de medir.
- **Commit medido**: worktree `C:\vrp-trabajo\s162-a61`, rama `s162-a61-mxd03` creada sobre `origin/s162-mxd03-codigo` = `afb3fcdea`. Los artefactos son los de las tres tandas (runs 40112510038, 40122029477, 40126381034), 24 cabeceras con `commit ffbb36248` (el tag), leídos en su lugar desde `D:\vrp-trabajo\temporales\s162_mxd03\tandas\` (5.465 records, 24 cabeceras, 0 con `estado` distinto de `ok`). La referencia de MIROVA congelada de `D:\vrp-trabajo\temporales\s162_mxd03\ref\` se comprobó por sha256 LF contra `poblacion.json` (`8ec5d918…` y `fd7a7098…`) en cada corrida. `pipeline/` de `afb3fcdea` igual al del tag: `git diff --stat ffbb36248 afb3fcdea -- pipeline volcanoes.yaml` vacío (ver `VERIFICADO LIMPIO`).
- **Modelo y esfuerzo**: Claude Fable 5.1 (`claude-fable-5-1`); el encargo no declaró esfuerzo, corrí con el del agente.
- **Qué NO miré** (para que el silencio no se lea como «todo bien»): no abrí ningún HDF (no hay gránulos en disco y bajar uno exige credenciales; el relleno lo medí con una grilla sintética y con lo que los artefactos registran); no volví a correr el arnés ni el evaluador del autor; no reconstruí `vara_viirs_mxd03.json` desde `data/` (la usé como tabla de posiciones VIIRS por noche); no verifiqué la posición del cráter de Nevados de Chillán (en `volcanoes.yaml` su `vent` es el centroide del volcán, ver H8); los TIF de MIROVA sólo existen para 2 de las 48 protegidas (el archivo parte el 2026-05-09); no leí los logs de los jobs; no medí nada de VIIRS ni de D17.

## 1. El fenómeno, antes del código

Un píxel MODIS no viene con su latitud y longitud: el archivo de radiancias (L1B) sólo trae la posición de **uno de cada cinco** píxeles en cada dirección, y la posición de los otros 24 hay que inferirla. El producto de geolocalización MxD03 sí trae la posición de cada píxel, corregida por el relieve. Nuestro pipeline estira la grilla gruesa del L1B con una interpolación lineal (`_interp_geo`) y no usa el MxD03 que baja. Dos cosas salen de ahí:

- **Un desfase sistemático.** La grilla gruesa está muestreada en el centro de cada bloque de 5 × 5 (el píxel 5i+2), pero la interpolación la estira como si estuviera en el píxel 5i. El resultado es que cada píxel recibe la posición de otro: dos píxeles hacia el nadir en el borde del frame 0, uno hacia el nadir en el otro borde, dos líneas en la traza en los extremos del gránulo. Cerca del nadir dos píxeles son 2 km; en el borde del barrido, donde el píxel mide 4,7 km de ancho, son casi 10 km. Por eso el cúmulo de Láscar aparece en producción a 1 a 3 km del cráter, siempre corrido hacia el lado del sensor, y en el borde del barrido un píxel puede estar dibujado a 10 km de donde está.
- **Un relleno que se propaga.** Cuando MODIS no tiene efemérides para un escaneo (10 líneas), la geolocalización trae −999 en todo ese escaneo. Con MxD03 ese píxel no tiene posición y se pierde, lo que es honesto. Con la interpolación, el −999 se mezcla con las latitudes reales de los vecinos y produce posiciones absurdas (latitud −400) en una celda gruesa a cada lado: se pierden 10 líneas más que con MxD03, y nadie se entera, porque un píxel con latitud −400 simplemente no cae en ningún volcán.

Lo que esta auditoría tiene que responder no es si X acerca el cúmulo al cráter (eso ya lo midió el A/B), sino si **el calor que X publica es el mismo calor que K publicaba**, movido de sitio, o si al cambiar las posiciones el detector eligió otro objeto (otro píxel caliente, una fumarola lejana, un borde de nube). Un radio no es una posición (A93): dos cúmulos a la misma distancia del cráter pueden estar en lados opuestos. Por eso se miden vectores, índices de píxel y una fuente que no sea el mismo gránulo (A109).

## 2. Instrumentos (las dos preguntas, en cada script)

| instrumento | qué mide | si estuviera roto lo que mido, ¿lo vería? | si el instrumento estuviera muerto, ¿se vería distinto? |
|---|---|---|---|
| `a61_protegidas.py` → `a61_protegidas_salida.txt`, `a61_protegidas.csv` | por protegida: cúmulo K y X (lat, lon, distancia, acimut, inner, clase, VRP, píxeles), vector K→X contra el corrimiento del gránulo en el píxel del cráter (**residuo**), píxel más caliente por índice en las dos grillas, `Distancia_km` de MIROVA, objeto VIIRS 375 de la noche, R que apagan | sí: un cúmulo que cambia de objeto da residuo de kilómetros, otro número de píxeles y se aleja del objeto VIIRS; control positivo: los 17 records con cambio de publicación (residuos 0,5 a 0,6 km o cúmulo sólo en un brazo) | sí: con X = K el residuo sería igual al corrimiento del gránulo (1 a 2,5 km) en las 48 y el hash de grilla sería el mismo (difiere en 48 de 48) |
| `clasificar_cumulos.py` | mismo píxel por índice / mismos píxeles por residuo / reselección | sí: la tercera clase crecería (control positivo: Láscar 2026-03-05 07:55 cae ahí por construcción) | sí: nadie pasaría el criterio 2 |
| `interp_geo_sintetico.py` | desfase de índice de `_interp_geo` de producción (importada, hash de la fuente impreso) y propagación de un bloque −999, sobre una grilla sintética muestreada en 5i+2 | sí: una interpolación correcta da error 0 (control positivo con `RegularGridInterpolator` y nodo en 5i+2: 0,0000 px) y ningún píxel intermedio | sí: si no importara la función de producción, revienta |
| `seguimientos.py` | relleno (forma, anillo K menos X contra el nulo de los 5.429 sin relleno), borde del barrido contra el modelo, cenit imposible, control del módulo de R con tope | sí en cada sección (impreso en el encabezado de cada una) | sí: el nulo del anillo se mide sobre 5.429 records y el modelo se compara con el dato |
| `detalle_casos.py` | los casos marcados, la protegida frágil brazo por brazo, uso estricto de `Distancia_km` 0,0, etiqueta `lado` | sí | sí |
| `tif_mirova_protegidas.py` | celda de máximo local del GeoTIFF MODIS de MIROVA de la misma pasada (2 protegidas), contra K y X | sí: georreferencia comprobada por A106 (máximo local a una celda del cráter) | sí: se imprime el exceso del máximo sobre la mediana |

Denominador y ventana de todo: 48 protegidas (alertas de MIROVA de 1 MW o más, lectura A, pareo ±120 s) que K publica y que tienen cúmulo en K y en X, de las 50 de la ventana 2026-03-01 a 2026-10-16; las otras 2 (Chillán 2026-10-12 07:20 y 2026-10-15 01:05, cenit 58°) no tienen cúmulo en ningún brazo y quedan fuera, como ya declaraba el §1. Nulos sobre los 5.465 records o los 158 con cúmulo en K y X, según se indica.

## 3. La tabla de las 48 (resumen; la fila por protegida está en `a61_protegidas_salida.txt` y `a61_protegidas.csv`)

| qué | K (`_interp_geo`) | X (MxD03) |
|---|---|---|
| distancia del cúmulo al cráter, mediana (p10, p90) | 1,58 km (0,81; 2,42); máximo 3,20 | 0,34 km (0,15; 0,61); máximo 0,89 |
| dentro del inner (5 km) / clase `summit` | 48 de 48 | 48 de 48; 0 cambios de clase |
| a 2 km o más del cráter | 12 | 0 |
| acimut del cúmulo desde el cráter | S 14, NE 11, SW 6, N 5, W 5, NW 4, E 2, SE 1 (dominan S y NE: los dos lados del barrido) | NE 13, E 7, W 7, S 6, N 6, NW 4, SE 3, SW 2 |
| cúmulo = píxel más caliente por índice (cúmulos de 1 píxel) | 27 de 48 | 27 de 48 |
| número de píxeles del cúmulo igual K y X | 47 de 48 (28 de 1 píxel, 17 de 2, 2 de 3, 1 de 4) | |
| residuo (K→X menos el corrimiento del gránulo) | mediana 0,001 km; 42 de 48 < 0,3 km; 46 < 1 km; máximo 2,40 | |
| distancia al objeto VIIRS de la noche (47 con referencia: 42 estricta, 5 amplia) | mediana 1,48 km | mediana 0,38 km; máximo 0,97; más cerca en 46 de 47 |
| objeto VIIRS al cráter / dispersión de sus pasadas | mediana 0,17 km / 0,11 km | |
| compatible con la `Distancia_km` de MIROVA a ±1,5 km (47 con dato) | 44 | 45 (con los dos 42, con ninguno 0) |
| protegidas con `Distancia_km` 0,0 (misma celda): a ≤ 0,75 km del cráter | 4 de 30 | 30 de 30 |
| VRP del cúmulo, X/K | mediana 1,000; más de 10 % en 6 de 48; más de 20 % en 2 (0,73 y 0,88) | |
| alguna R apaga la publicación (40 con R) | 1 (Láscar 2026-03-12 07:25, 5 de 20) | |
| volcanes / satélites / cenit | Láscar 40, Chillán 7, Villarrica 1 / Terra 23, Aqua 25 / mediana 21°, máximo 50,5°, 8 sobre 35° | |

Las 4 protegidas «expuestas» del §5 del pre-registro quedan con X a 0,61, 0,89, 0,27 y 0,42 km del cráter (Láscar 2026-03-09 07:10, 2026-03-27 07:10, 2026-04-08 01:50; Chillán 2026-10-10 07:40): a más de 4 km del borde del inner.

**Clasificación** (`clasificar_cumulos_salida.txt`): **26** son el mismo píxel por índice (cúmulo de 1 píxel en K y X, y en las dos grillas el centroide coincide a menos de 50 m con el píxel más caliente por índice, cuyo índice es el mismo en todos los brazos por construcción); **18** son los mismos píxeles por residuo (< 0,3 km, mismo número de píxeles); **4** son reselección parcial:

| protegida | cenit | K | X | residuo | X/K | qué pasó |
|---|---|---|---|---|---|---|
| Láscar 2026-03-05 07:55 | 48,7° | 0,56 km, 1 px, 0,446 MW | 0,31 km, 1 px, 0,325 MW | 1,86 km | 0,73 | el píxel más caliente por índice (el cúmulo de K) **no pasa el primer pase en X** (`first_pass` 1 → 0) y X publica un vecino recapturado; el píxel caliente en MxD03 queda a 0,93 km del cráter |
| Láscar 2026-03-09 01:55 | 32,0° | 2,16 km, 2 px, 0,566 MW | 0,21 km, 1 px, 0,500 MW | 0,66 km | 0,88 | X conserva el píxel más caliente (que es su centroide) y pierde el segundo |
| Láscar 2026-03-06 01:35 | 9,3° | 1,52 km, 2 px, 0,382 MW | 0,53 km, 2 px, 0,339 MW | 0,53 km | 0,89 | dos recapturas en los dos brazos; el centroide se movió media celda más que el cráter |
| Láscar 2026-04-18 01:50 | 27,6° | 1,10 km, 3 px, 1,310 MW | 0,17 km, 3 px, 1,269 MW | 0,54 km | 0,97 | 3 píxeles en los dos; el centroide se movió 0,4 píxel más que el cráter |

En las 4, X queda a 0,18 a 0,35 km del objeto VIIRS de la noche y K a 0,42 a 2,32 km. Son píxeles vecinos que se reparten el cráter de Láscar a esa resolución (a 49° el píxel mide 2,3 km), no otro objeto: a menos de 1 km del cráter de Láscar no hay nada más que publicar. Nota sobre Chillán 2026-10-01 08:35 (cenit 50,5°, residuo 2,40 km): es el **mismo píxel** en K y X (grupo 1: el centroide coincide con el píxel más caliente por índice en las dos grillas); el residuo grande no es un cambio de píxel sino que el corrimiento medido en el píxel del cráter no es el del píxel del cúmulo, porque en el borde del barrido las líneas de escaneos vecinos se solapan (bow tie) y el campo de corrimiento salta entre líneas. Por eso el residuo sólo clasifica donde el índice no puede, y se usa después del índice.

## 4. Hallazgos (por gravedad)

### H1. Un bloque de relleno de geolocalización que cae sobre el cráter produce un record «negativo» en los dos detectores: no existe el estado «sin dato»
- **SCRIPT:SALIDA**: `seguimientos_salida.txt` §1 (dos records con el píxel del cráter de K en posición absurda); `interp_geo_sintetico_salida.txt` §b. **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:385-396` (`_interp_geo`, `zoom` de orden 1 sin enmascarar), `:560` (`dist` desde el centro, que es lo único que decide si un píxel entra al ROI), `:628` (`min_bg_pixels=10`, el único mínimo de escena); `grep -n -- '-999' pipeline/process_modis.py` da 0 líneas.
- **QUÉ PASA**: el relleno de MxD03 viene en escaneos enteros (5 de los 8 gránulos tienen exactamente 10, 10, 10, 10 y 150 líneas de 1.354 píxeles; `seguimientos_salida.txt` §1). Cuando el bloque pasa por encima del volcán, el cráter no tiene posición: con MxD03 es NaN y con la interpolación es una latitud de cientos de grados (el píxel más cercano al cráter de Lastarria el 2026-04-23 01:50 queda a 25.742 km; el de Planchón Peteroa el 2026-03-18 08:05 a 103.470 km). Los dos brazos escriben igual un record con `n_anom` 0, un `t_bg` y un anillo de fondo recortado (Lastarria: 405 píxeles en K, 441 en X, contra unos 1.800 a ese cenit; Planchón Peteroa: 255 y 397 contra unos 900), y `data/` guarda esa noche como **negativo** (`pub_guardada 0`). No hubo nada que ver porque no se miró el cráter, y el record no lo dice.
- **CÓMO SE VE EN EL DASHBOARD**: una noche sin punto, igual que una noche observada y tranquila. Si el volcán hubiera estado activo, el operador vería un hueco sin aviso. En la ventana son 2 de 5.465 records (0,04 %), los dos negativos limpios; ninguna alerta. Es el caso de manual de «SIN DATO presentado como OK».
- **CÓMO REPRODUCIRLO**: `python -I seguimientos.py` (sección 1, «records con el pixel del crater de K en posicion absurda»); gránulos `MOD021KM.A2026113.0150` y `MYD021KM.A2026077.0805`.
- **CONFIANZA**: CONFIRMADO en los artefactos (posiciones absurdas, anillos recortados, negativos guardados). Que el relleno de la grilla de 5 km del L1B coincida con el de MxD03 y sea −999 es SOSPECHA (no abrí el HDF; es lo que el sintético y los números implican).
- **GRAVEDAD**: 3 para producción (hoy y con X: el defecto es de diseño, no de la geolocalización elegida). Para la adopción: el flag debería dejar un estado explícito cuando el píxel del cráter o el inner no tengan geolocalización (`geo_incompleta` o equivalente) y el tablero no contarlo como negativo. Para este A/B: 0 efecto (los dos records no publican en ningún brazo y no son alertas).

### H2. El corrimiento de producción es el desfase de índice de `_interp_geo`, y el modelo lo reproduce; los 13 a 16 km de VRB-07 son un gránulo contaminado, con cenit imposible
- **SCRIPT:SALIDA**: `interp_geo_sintetico_salida.txt` §a; `seguimientos_salida.txt` §2 y §3; `detalle_casos_salida.txt` §d.
- **QUÉ PASA**: sobre una grilla sintética muestreada en el píxel 5i+2 (como el SDS de 5 km de MOD021KM), `_interp_geo` devuelve en el frame 0 la posición del píxel que está **2,00 frames hacia el nadir**, 0 en el frame 902 y la del píxel 1,00 frame hacia el nadir en el 1353; en la traza, +2 líneas arriba y −2 abajo. Una interpolación con el nodo en 5i+2 da error 0,0000 (control positivo). Multiplicando ese desfase por el ancho del píxel a cada cenit (geometría esférica: 1,00 km a 0°, 1,91 a 45°, 4,69 a 65°) el modelo da, por frame del píxel del cráter: 9,29 km contra 8,44 medidos en el frame 0 a 9; 7,87 contra 7,05 en el 10 a 39; 5,79 contra 5,15 en el 40 a 99; 3,15 contra 2,97 en el 100 a 299; 4,62 contra 4,26 en el 1340 a 1353 (n 161, 293, 446, 901, 175). Cerca del cruce por cero el dato tiene un piso de 1,1 km que el modelo no incluye (el término de la traza y el bow tie). En los records sin relleno el corrimiento máximo es **11,45 km** (Llaima 2026-05-09 06:45, frame 0, cenit 65,0°), 12 superan 10 km y 150 superan 8 km, todos con frame < 100. Los records de 12,9 a 16,2 km son los del gránulo `MOD021KM.A2026213.0300` (relleno de 13,5 líneas), que además son los **únicos 6 de los 5.465 con cenit sobre 65,6°** (67,97 a 75,31°; el máximo físico de MODIS en el borde del barrido es unos 65,5° y el máximo limpio medido es 65,28°): los ángulos también salen de `_interp_geo` sobre su grilla de 5 km y también se contaminan.
- **CÓMO SE VE EN EL DASHBOARD**: hoy, el marcador MODIS está corrido hacia el lado del sensor 1 a 3 km cerca del nadir y hasta 11 km en el borde del frame 0; en 6 records de `data/` el cenit guardado es físicamente imposible.
- **CÓMO REPRODUCIRLO**: `python -I interp_geo_sintetico.py` y `python -I seguimientos.py` (secciones 2 y 3).
- **CONFIANZA**: CONFIRMADO (función de producción sobre grilla sintética, más el ajuste del modelo al dato). Que el SDS de 5 km esté muestreado en 5i+2 es lo que dice la especificación del L1B; lo sostiene el ajuste al dato, no una lectura del documento (no está en `documentacion/`).
- **GRAVEDAD**: 2 (es el fenómeno que D35 registra, ahora con mecanismo y número; corrige la lectura de VRB-07). Para el catálogo: la frase «el corrimiento llega a 16 km» debe decir «11,5 km en gránulos sanos; más allá, relleno».

### H3. El seguimiento S-2 está invertido: donde el relleno toca el ROI, K pierde más píxeles que X
- **SCRIPT:SALIDA**: `seguimientos_salida.txt` §1 (anillo K menos X); `interp_geo_sintetico_salida.txt` §b.
- **QUÉ PASA**: en el sintético, un bloque de relleno de 30 celdas gruesas deja 197.684 píxeles finos en −999 exacto y **13.540 más** (10 líneas, 5 a cada lado) con valores intermedios entre la latitud real y −999: con la interpolación se pierden esas 10 líneas además del bloque; con MxD03 se pierde sólo el bloque. En los artefactos: el anillo de fondo de K menos el de X vale, en los 5.429 records sin relleno, mediana +4 con p5 −40 y p95 +14; de los 36 records con relleno, 34 quedan dentro de ese rango (el bloque no toca su ROI) y los 2 que salen son **negativos**: Planchón Peteroa 2026-03-18 08:05 (−142: K tiene 142 píxeles de anillo menos que X) y Lastarria 2026-08-26 01:20 (−124). La única protegida con relleno en su gránulo (Láscar 2026-04-23 01:50, 150 líneas de relleno) da +6, dentro del nulo: el bloque está lejos de Láscar, y publica en K y X (0,786 y 0,762 MW).
- **CÓMO SE VE EN EL DASHBOARD**: invisible en este A/B. Para la adopción: lo honesto es lo que hace X (descartar el píxel sin posición), y además recupera las 10 líneas de halo que hoy se pierden en silencio.
- **CÓMO REPRODUCIRLO**: `python -I seguimientos.py` (sección 1).
- **CONFIANZA**: CONFIRMADO en los artefactos (dirección del signo); el mecanismo del halo, CONFIRMADO en sintético y SOSPECHA en el HDF real.
- **GRAVEDAD**: 2 para el texto de la adopción (la FICHA no debe decir que MxD03 «pierde píxeles que hoy se conservan»: es al revés).

### H4. Cuatro de las 48 protegidas reseleccionan píxeles vecinos del cráter; la magnitud de alertas individuales se mueve hasta 27 %
- **SCRIPT:SALIDA**: `clasificar_cumulos_salida.txt` (grupo 3); `detalle_casos_salida.txt` §a.
- **QUÉ PASA**: la posición entra a la detección por el fondo y por la máscara de cumbre (§4 del pre-registro). En Láscar 2026-03-05 07:55 (cenit 48,7°) el píxel más caliente por índice pasa el primer pase con las posiciones interpoladas y **no** con las de MxD03 (`diag_n_first_pass_pixels` 1 → 0; recaptura 1 → 2), y X publica un vecino recapturado con 0,325 MW en vez de 0,446. En 2026-03-09 01:55 el cúmulo pasa de 2 a 1 píxel (0,566 → 0,500). En 2026-03-06 y 2026-04-18 el número de píxeles se conserva y el centroide se mueve media celda más que el cráter. En las 48, X/K supera 10 % en 6 y 20 % en 2; la mediana es 1,000. Es VRB-03 visto sobre las protegidas.
- **CÓMO SE VE EN EL DASHBOARD**: si se adopta, en noches sueltas de Láscar la magnitud MODIS cambia hasta un cuarto sin que cambie la alerta; el punto se mueve al cráter.
- **CÓMO REPRODUCIRLO**: `python -I clasificar_cumulos.py`; `python -I detalle_casos.py` (sección a).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (para el aviso a OVDAS y la marca visible: «la magnitud de alertas individuales se mueve hasta ±27 %»; no para el veredicto, que no mide magnitud).

### H5. La protegida frágil se apaga por la asimetría A46 (distancia desde el centro contra distancia desde el cráter) en el borde del inner, no por el fondo ni por las zonas excluidas
- **SCRIPT:SALIDA**: `detalle_casos_salida.txt` §b. **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:560` (`dist = haversine_km(volcano_lat, volcano_lon, lat, lon)`, desde `lat/lon` del volcán, no desde el `vent`), `:1143` (`dist_km` de cada píxel anómalo sale de ese `dist`), `:1151` (`hotspot_dist_km = anomaly_pixels[0]["dist_km"]`), `:1363` (`final_hotspot_dist_km = hotspot_dist_km`, fuente `eruption`), `:1382-1384` (`derivar_distance_class` con `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`: la etiqueta sale de `final_hotspot_dist_km`). `volcanoes.yaml`: Láscar `lat/lon` (−23,369, −67,732) está 0,68 km al sur de `vent` (−23,36293, −67,731416).
- **QUÉ PASA**: Láscar 2026-03-12 07:25 (cenit 3,6°, 2,19 MW) tiene el píxel 2,69 km al NE del cráter en K. Las 20 R lo trasladan 2,15 km en 20 rumbos; en las 5 de rumbo 348° a 60° (hacia el N y NE) `pc_dist` queda en 4,38 a 4,83 km (dentro de los 5 km del inner) pero `final_dist`, medido desde el centro que está al sur, queda en 5,05 a 5,41 km, la etiqueta pasa a `far` y el tablero no publica. El VRP del cúmulo apenas cambia (2,09 a 2,26 MW en los 22 brazos; `t_bg` 266,1 a 267,4 K): no es el fondo. `final_dist` menos `pc_dist` vale 0,59 a 0,66 km en los 22 brazos, igual a la separación centro-cráter. Con X el píxel queda a 0,55 km (`final_dist` 1,15): a 3,9 km del borde. La lectura del seguimiento S-4 («depende de la posición también por el fondo o las zonas excluidas») queda refutada para este caso.
- **CÓMO SE VE EN EL DASHBOARD**: hoy, una alerta fuerte de Láscar puede estar a 1,7 km de caer en `far` por la geolocalización; con X, las 48 protegidas quedan a 4,1 km o más de ese borde.
- **CÓMO REPRODUCIRLO**: `python -I detalle_casos.py` (sección b).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 para este A/B (es un argumento más a favor de X); para producción es la asimetría A46/A81 ya catalogada, en su cara de posición.

### H6. El control del módulo de R acepta un módulo absurdo; un tope físico lo marca
- **ARCHIVO:LÍNEA**: `experiments/_s162_mxd03/evaluar_mxd03.py:324-334` (`control_r_modulo`: 20 nulos, aplicado = pedido a 10 m, rumbos cada 18°, sin tope). **SCRIPT:SALIDA**: `seguimientos_salida.txt` §4.
- **QUÉ PASA**: reproducido: el control de hoy marca 0 de los 2.046 records con R; con un tope de 20 km marca exactamente 1 (Lastarria 2026-04-23 01:50, 25.741,9 km, el record de H1). El módulo máximo entre records sin relleno es 2,96 km, así que un tope de 20 km está a casi 7 veces del dato real y no roza ningún caso legítimo. Los otros dos records con brazos R `None` (Chaitén 2026-09-21 01:45, 10 R; Láscar 2026-09-23 01:35, 7 R) tienen módulos de 2,1 y 2,5 km: borde de escena, como el §4 prevé.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: `python -I seguimientos.py` (sección 4).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (confirma VRB-01; recomendación concreta: tope de 20 km en `control_r_modulo` y en `desplazamiento_crater` si el arnés se reutiliza).

### H7. La etiqueta `lado` de la población está al revés en 47 de los 906 records con el cráter en el frame 0 a 99
- **ARCHIVO:LÍNEA**: `experiments/_s162_mxd03/poblacion_mxd03.py:77-81` (`lado`: `f0` si Aqua con acimut > 0 o Terra con acimut < 0). **SCRIPT:SALIDA**: `detalle_casos_salida.txt` §e.
- **QUÉ PASA**: la regla vale para las pasadas nocturnas típicas (Terra 00 a 03 UTC, Aqua 06 a 09 UTC). La población trae 52 records de crepúsculo (43 de Aqua a las 21 UTC y 9 de Terra a las 12 UTC, de mayo a agosto, todos negativos limpios) donde la geometría orbital es la opuesta y el acimut cambia de signo: 47 de ellos tienen el píxel del cráter en el frame 0 a 99 y la etiqueta `otro`. El frame del artefacto es la verdad; la etiqueta sólo estratifica un informe (P2 por lado no decide).
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: `python -I detalle_casos.py` (sección e).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### H8. El `vent` de Nevados de Chillán es el centroide del volcán, y las distancias de sus 7 protegidas llevan un desplazamiento de referencia sin medir
- **ARCHIVO:LÍNEA**: `volcanoes.yaml` (NevadosDeChillan: `vent_lat`/`vent_lon` = `lat`/`lon` = −36,863, −71,377); `pipeline/geo_utils.py:68-71` (`get_detection_anchor` usa ese `vent`). **SCRIPT:SALIDA**: `detalle_casos_salida.txt` §c.
- **QUÉ PASA**: en Láscar el cráter está verificado en terreno (A5) y las 40 protegidas de X caen a 0,05 a 0,89 km de él. En Chillán las 7 de X caen a 0,14 a 0,66 km del `vent`, pero ese punto no es un cráter verificado, y MIROVA da `Distancia_km` 1,0 a 2,24 para esas mismas pasadas (2,24 en dos, incompatible a ±1,5 km con X en esas dos). Como la referencia de MIROVA es su centro de grilla (D15) y la nuestra es un centroide, la comparación en Chillán no tiene poder. Lo que sí vale es la fuente independiente: el objeto VIIRS de la noche está a 0,47 a 0,69 km del `vent` y X a 0,34 a 0,67 km de ese objeto (K a 0,34 a 3,02).
- **CÓMO SE VE EN EL DASHBOARD**: la distancia al cráter que se muestra en Chillán se mide desde un punto que no es el cráter activo. **CÓMO REPRODUCIRLO**: `grep -n -A 6 "name: NevadosDeChillan" volcanoes.yaml`.
- **CONFIANZA**: CONFIRMADO que `vent` = centroide; SOSPECHA que esté lejos del cráter activo (no medido; no adivino coordenadas). **GRAVEDAD**: 1 para este A/B (no cambia nada: la condición es «no se fue a otro objeto», y el objeto VIIRS lo sostiene); para el proyecto es una referencia que falta fijar con dato de terreno.

### H9. V-TIF (informa, n 1): el GeoTIFF de MIROVA del 2026-05-10 01:25 pone el calor en la celda del cráter, donde cae X; K cae en la celda de al lado
- **SCRIPT:SALIDA**: `tif_mirova_protegidas_salida.txt`. Índice `index.csv` de `MendozaVolcanic/mirova-tif-archive` leído por la API (5.674 filas MODIS); sólo 2 de las 48 protegidas tienen TIF de su pasada (el archivo parte el 2026-05-09; las de Chillán son posteriores al congelamiento del 2026-09-22, A106).
- **QUÉ PASA**: Láscar 2026-05-10 01:25 (cenit 19,4°): TIF EPSG:4326 de 51 × 51 celdas de 0,99 km; el máximo local a 5 km del cráter es la **celda del cráter** (24, 25), 0,026 sobre la mediana, a 0,29 km del cráter: georreferencia OK por A106. El cúmulo de X cae en esa misma celda, a 0,18 km de su centro; el de K cae en la celda (25, 25), 1,34 km al sur. Láscar 2026-06-27 01:35: el TIF no distingue el cráter del fondo (máximo local a 3,3 km con 0,0055 sobre la mediana): SIN DATO, no contradicción.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: bajar los dos TIF con `gh api -H "Accept: application/vnd.github.raw" repos/MendozaVolcanic/mirova-tif-archive/contents/data/tif/Lascar/<f>_MODIS.tif` a una carpeta y `python -I tif_mirova_protegidas.py <carpeta>`.
- **CONFIANZA**: CONFIRMADO (n 1; no es independiente, A109). **GRAVEDAD**: 1 (informa; coincide con todo lo demás).

## 5. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

| qué | comando | vara |
|---|---|---|
| 5.465 records `ok`, 24 cabeceras `commit ffbb36248`; referencia congelada con sha256 LF igual al sellado | `python -I a61_protegidas.py` (encabezado de la salida) | `poblacion.json` del tag |
| `pipeline/` y `volcanoes.yaml` del commit medido iguales a los del tag | `git diff --stat ffbb36248 afb3fcdea -- pipeline volcanoes.yaml` (vacío) | tag `s162-mxd03-tag` |
| 48 protegidas con cúmulo = las 48 que K publica; hash de grilla X ≠ K en 48 de 48; las 2 que K no publica sin cúmulo en ningún brazo | `a61_protegidas_salida.txt` | §6 P1 |
| X a 0,15 a 0,89 km del cráter, 48 de 48 dentro del inner, 0 cambios de clase, 48 de 48 más cerca que K | `a61_protegidas_salida.txt` (agregados) | A61 |
| 44 de 48 mismos píxeles (26 índice, 18 residuo < 0,3 km); 4 reselección de vecinos del cráter, ninguna a otro objeto | `clasificar_cumulos_salida.txt` | §6 P4 |
| residuo K→X menos corrimiento del gránulo: mediana 0,001 km en las 48; en los 158 con cúmulo, mediana 0,014, 15 > 1 km y 3 > 3 km (todos con cenit > 48°) | `a61_protegidas_salida.txt` (nulo) | control positivo: los 17 cambios de publicación |
| VIIRS de la noche: X a ≤ 0,97 km del objeto en 47 de 47; más cerca que K en 46 de 47 | `a61_protegidas_salida.txt` | `vara_viirs_mxd03.json` (estricta 42, amplia 5) |
| `Distancia_km` 0,0 de MIROVA: X ≤ 0,75 km en 30 de 30, K en 4 de 30; a ±1,5 km nadie queda incompatible con los dos brazos | `detalle_casos_salida.txt` §c | CSV congelado |
| `_interp_geo` de producción: desfase +2/0/−1 frames y ±2 líneas; control positivo 0,0000 px; halo de 5 líneas por lado | `python -I interp_geo_sintetico.py` | grilla sintética en 5i+2 |
| modelo de desfase contra el dato: dentro de 10 % en los frames < 300 y > 1300 | `seguimientos_salida.txt` §2 | artefactos sin relleno (n 5.429) |
| control del módulo de R: 0 marcados hoy, 1 con tope de 20 km; máximo limpio 2,96 km | `seguimientos_salida.txt` §4 | §8 control 2 |
| anillo K menos X en records sin relleno: p5 −40, p95 +14 (nulo medido) | `seguimientos_salida.txt` §1 | 5.429 records |
| georreferencia del TIF del 2026-05-10 (máximo local en la celda del cráter) | `tif_mirova_protegidas_salida.txt` | A106 |

## 6. SIN DATO

- No se midió sobre un HDF si la grilla de 5 km del L1B trae el mismo relleno que MxD03 ni con qué valor: el halo de 5 líneas es sintético y los anillos recortados lo sostienen, pero no lo vi en el archivo.
- La posición de MIROVA con dirección (V-TIF) sólo existe para 2 de las 48 protegidas, y una de las dos no muestra el cráter: n 1.
- Villarrica 2026-09-04 07:50 no tiene referencia VIIRS esa noche: la única comprobación independiente le falta (X a 0,33 km del cráter, misma celda que K menos 1,14 km).
- El cráter activo de Nevados de Chillán no está fijado con dato de terreno: las distancias de sus 7 protegidas se miden desde el centroide.
- El mecanismo por el que los ángulos del gránulo `MOD021KM.A2026213.0300` salen de 68 a 75°: contaminación del relleno en el SDS de ángulos, inferido, no leído.
- Esfuerzo del modelo: no declarado por quien orquesta.

## 7. Lo que recomiendo a quien orquesta (no es un arreglo, es la evaluación)

- La condición del §6 P4 **se cumple**: el cúmulo movido es el mismo calor, al cráter, y no se fue a otro objeto. No hay nada en el eje espacial que frene el ciclo de adopción de la tabla del §10.
- El texto de la adopción (FICHA SDA, D35, aviso a OVDAS) debería decir: (a) que el marcador MODIS se corre 1 a 3 km hacia el cráter cerca del nadir y hasta 11 km en el borde del barrido, por el desfase de índice de `_interp_geo` (H2); (b) que la magnitud de alertas individuales se mueve hasta ±27 % (H4); (c) que un píxel sin geolocalización se descarta, y que eso **recupera** 10 líneas por bloque que hoy se pierden sin aviso (H3), no al revés; (d) que falta un estado «sin dato» cuando el bloque de relleno pasa por el cráter, que hoy se guarda como negativo en los dos detectores (H1), y que ese estado conviene diseñarlo en el mismo flag.
- Con X, las 48 protegidas quedan a 4,1 km o más del borde del inner medido desde el centro: la fragilidad de la etiqueta (H5) desaparece para ellas.

## 8. Archivos de esta carpeta

`INFORME.md` (este), `cargar_a61.py`, `a61_protegidas.py` + `a61_protegidas_salida.txt` + `a61_protegidas.csv`, `clasificar_cumulos.py` + `_salida.txt`, `detalle_casos.py` + `_salida.txt`, `seguimientos.py` + `_salida.txt`, `interp_geo_sintetico.py` + `_salida.txt`, `tif_mirova_protegidas.py` + `_salida.txt`. Los dos TIF bajados y el `index.csv` del archivo quedaron fuera del repo (datos descargados, en el scratchpad de la sesión).
