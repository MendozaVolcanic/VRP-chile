# Marcador «también hay calor en la cumbre»: medición e implementación (S194)

Script: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s194_marcador_cumbre\medir_marcador.py`;
salida en `medir_marcador_salida.txt` y `resultado.json` de la misma carpeta (datos de main del 2026-11-21) y en
`medir_marcador_salida_base_76f52c7ec.txt` (datos de la base del informe S193; mismos números). Censo de `anomaly_pixels`:
`censo_pixeles.py`, salida `censo_pixeles_salida.txt`. Corrido con `--modulo` (exige igualdad record por
record con `frontend/cumbre.js`). Sólo display: no se tocó `pipeline/`, perfiles ni `data/`.

## 1. El fenómeno y la pregunta

En una pasada nocturna puede haber un píxel tibio sobre el cráter y, a 13 a 23 km, un cúmulo más radiante (en Láscar e
Isluga, típicamente el salar o la roca tibia del altiplano, o un borde de nube). La regla de posición «radiante» (D8',
decisión de Nicolás del 2026-11-15) pone el record en el cúmulo más radiante: la pasada queda lejana y el operador no ve que
también hubo calor en la cumbre. Así quedaban fuera de vista 12 alertas protegidas de MIROVA vistas sólo por su OCR (Codex
F12-V301). Mover la posición a la cumbre se rechazó en S193 (`experiments/_s193_radiante_variante/INFORME.md`: recupera esas 12
pero pone en la cumbre 114 pasadas que la tabla de MIROVA ubica lejos). La salida intermedia es avisar sin mover nada. La
pregunta de esta medición: ¿el aviso alcanza a las 12, y sale en pocas pasadas lejanas como para informar, o en casi todas?

## 2. ¿Los records traen todos los alertados?

Sí, en la vía. `pipeline/mirova_v750_codigo.py` arma `anomaly_pixels` recorriendo la máscara entera de alertados (sin tope)
con `dist_km` medido desde el mismo cráter que `distance_class`; `store.py` sólo recorta píxeles por distancia fuera de la vía.
Censo sobre main del 2026-11-21 (11 Tier A): 74.115 records, todos de la vía; 10.361 con alertados, y en los 10.361
`len(anomaly_pixels) == n_anomalous_pixels` y todos traen `dist_km`. La vía cubre toda la historia publicada (desde el
2025-02-15 en los 11). Los records de otra vía (K, legado) no se marcan: su lista puede estar recortada (A46).

## 3. Criterio

Pasada de la vía que el tablero NO pone en la cumbre (`isSummitDetection` falso; en la vía es `distance_class: "far"`) y con al
menos un alertado a `dist_km` menor o igual al `inner_radius_km` del volcán. Predicado del tablero ejecutado con node desde
`frontend/index.html` (runner de `scripts/banco_paridad.py`). «Publicada como lejana» = lo que el tablero publica con «Incluir
lejanas» (no cumbre, válida, no artefacto térmico, magnitud mayor que 0).

## 4. Resultado (noches del 2026-03-01 al 2026-11-18, 11 Tier A, pasadas nocturnas de la vía)

Controles: 28.840 pasadas, igual que el informe S193 (con los datos de su base `76f52c7ec` y con los de main del 2026-11-21);
claves únicas 28.840; las 12 de Codex están todas en el conjunto; record sintético con un alertado a 0,7 km marca, el mismo sin
ese píxel no marca, uno de otra vía no marca y uno de la cumbre lo pone el tablero en la cumbre; `frontend/cumbre.js` y el
predicado en Python dan lo mismo en las 28.840 (0 distintas).

| | Pasadas | Con alertados | Cumbre (publicadas) | Lejanas (publicables con «Incluir lejanas») | Lejanas con marca |
|---|---|---|---|---|---|
| Total | 28.840 | 3.679 | 2.972 | 707 | **218 (30,8 %)** |
| MODIS | 6.050 | 155 | 144 | 11 | 1 (9,1 %) |
| VIIRS 375 | 11.399 | 2.873 | 2.216 | 657 | 215 (32,7 %) |
| VIIRS 750 | 11.391 | 651 | 612 | 39 | 2 (5,1 %) |

Por volcán y sensor (lejanas con marca de lejanas): Isluga V375 66 de 107, Láscar V375 53 de 102, Lastarria V375 45 de 142,
Tupungatito V375 23 de 79, Planchón-Peteroa V375 19 de 71, Cordón Caulle V375 4 de 7, Chaitén V375 2 de 8, Villarrica V375 2
de 19, Chillán V375 1 de 48, Láscar V750 2 de 4, Láscar MODIS 1 de 2. Llaima y Copahue: ninguna.

En las 218 marcadas hay de 1 a 10 alertados en la cumbre (mediana 2; 61 con uno solo), el más cercano a una mediana de
0,56 km del cráter (0,11 a 5,71 km).

- **Las 12 protegidas sólo OCR: las 12 llevan la marca.** Las 12 son lejanas publicables, hoy no publicadas con «Solo cráter»,
  con 1 a 6 alertados en la cumbre, el más cercano a 0,11 a 1,07 km.
- **Las 114 que la tabla de MIROVA ubica lejos: las 114 llevan la marca.** Es lo esperable y no es un error: hubo calor en los
  dos lados, y la marca no las pone en la cumbre (la clase, la posición y la potencia siguen como hoy).
- **Cruce con S193:** las 218 marcadas son exactamente las 218 pasadas que la variante «cumbre primero» movía (0 fuera de ese
  conjunto, 0 de ese conjunto sin marca).
- **No publicadas con alertado en la cumbre (dato):** 0. En esta ventana toda pasada de la cumbre con alertados se publica y
  toda lejana con alertados es publicable con «Incluir lejanas».

## 5. Veredicto: se sostiene

Recupera la vista de las 12 sin efecto raro: no cambia ninguna cifra, y la marca sale en 3 de cada 10 lejanas (no en casi
todas), concentrada en VIIRS 375 del norte, donde el píxel de 375 m separa el salar del cráter. Es informativa en el sentido
pedido: dice «hubo calor en los dos lados», no «esto es del volcán». En Isluga sale en 6 de cada 10 lejanas: ahí el aviso
será frecuente, y es el volcán donde la clase del OCR de MIROVA más se separa de la tabla.

## 6. Dónde se ve en el tablero

- `index.html`, tabla de pasadas: en la celda «Zona» de las filas lejanas (con «Incluir lejanas») y de las «anomalía no
  publicada» (con «Todas las pasadas»), «◉ también hay calor en la cumbre (1 píxel a 0,9 km)», con la explicación en el
  título.
- `index.html`, mapa: una línea en el popup del marcador lejano (visible con «Incluir lejanas»).
- `index.html` y `mosaico.html`, tarjeta: si en las últimas 48 h hubo una pasada lejana con calor en la cumbre más nueva que la
  detección que muestra la tarjeta (o no hay detección), «◉ Pasada lejana del <fecha> UTC: también hay calor en la cumbre
  (...)». Con «Solo cráter» la tarjeta no la mostraría de otro modo.
- `diario.html`, tarjeta: junto al conteo de detecciones, «(◉ N lejanas con calor también en la cumbre)» del período.

Las tarjetas y el conteo del diario miran sólo pasadas nocturnas, como sus cifras desde #1086 (de día la lectura puede ser
reflejo solar); la tabla y el popup marcan cualquier pasada lejana de la vía que cumpla el criterio, también una diurna.

No cambia: la posición del record, `distance_class`, la potencia publicada, el nivel de alerta, la frescura, los conteos ni
los gráficos. Los 34 de la sombra no se marcan (no tienen `inner_radius_km`; no se midieron).

## 7. Pruebas y mutaciones

`tests/test_tablero_cumbre_s194.py` (7 pruebas, node): marca y su control (el mismo record sin el píxel en la cumbre no
marca; tampoco uno de la cumbre, uno de otra vía, uno sin radio ni uno a 0,01 km fuera del radio; el borde marca), textos,
los píxeles reales de Isluga Suomi NPP 2026-04-07 06:12 (una de las 12) con y sin el píxel a 0,88 km, record congelado (la
marca no escribe en él), la pasada lejana más reciente para las tarjetas, `marcaCumbre` de `index.html` ejecutada en node y
las tres vistas cargando el módulo.

Mutaciones a mano (`mutar.py`, en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s194_marcador_cumbre\`,
salida `mutaciones_salida.txt`), contadas sólo si las atrapa una aserción: **12 de 12**. Borde `>` a `>=`; sin exigir la vía;
sin exigir `far`; elegir la más vieja; sin corte de 48 h; sin filtro de la vista; escribir en el record; singular y plural
cruzados; `marcaCumbre` que marca sin calor en la cumbre; mosaico sin cargar el módulo; tabla con una sola rama; diario sin el
conteo. Una mutación anterior (quitar `isSummitDetection` de `marcaCumbre`) no se atrapaba porque era equivalente: en la vía,
`calorEnCumbre` ya exige `far`. La guarda redundante se quitó de las vistas y el criterio quedó en un solo lugar.

Navegador real (servidor estático local, datos de main del 2026-11-21; capturas en `D:\vrp-trabajo\temporales\s194_marcador\capturas\`):
la fila de Isluga Suomi NPP 2026-04-07 06:12 lleva «◉ también hay calor en la cumbre (1 píxel a 0,9 km)» con «Solo cráter»
(fila «anomalía no publicada») y con «Incluir lejanas» (fila «📍 Fuera», 4,125 MW sin cambio), y la misma línea en el popup
del mapa; la tarjeta de Tupungatito, con «Solo cráter», sigue en «SIN ANOMALÍA» y dice «◉ Pasada lejana del 2026-11-20 05:42
UTC: también hay calor en la cumbre (1 píxel a 0,3 km)»; el mosaico muestra lo mismo en Tupungatito; el diario del
2026-04-07 dice «3 det. nuestras (◉ 1 lejana con calor también en la cumbre)» en Isluga. Sin errores de consola propios (los
404 son los `*_recent.json` que el mosaico pide antes del archivo completo, de antes de este cambio).

## 8. Lo no verificado

Lo que no cubre esta medición: pasadas diurnas (el criterio las marcaría igual si son lejanas de la vía con un alertado en
la cumbre), los 34 de la sombra y la ventana posterior al 2026-11-18.
