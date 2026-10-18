# Verificador con contexto limpio: posición de lo que VIIRS 375 publica, C0 contra K (S153)

Fecha: 2026-10-18. Repo en `loop/activo` (HEAD `fd6b3f8d8` al terminar; leí, no toqué nada fuera de esta carpeta).
Todos los números de este informe salen de corridas mías de esta sesión; las salidas crudas están en los `salida_*.txt`
de esta misma carpeta y las partes que deciden van pegadas abajo.

## Veredicto por parte

| Parte de la afirmación | Veredicto |
|---|---|
| 1. «Casi todo lo que VIIRS 375 publica viene del Test 1» | PARCIAL |
| 2. «Su cúmulo cae a 2 a 3 km, en el borde del disco de 3 km (Villarrica 2,73, Llaima 2,75, Copahue 2,71; Láscar 0,37)» | CONFIRMADA como número del centroide del cúmulo; REFUTADA como «lo que el operador ve» |
| 3. «Con K las mismas publicaciones se juntan en el cráter (Villarrica 0,18, Tupungatito 0,20, Chaitén 0,20, PP 0,40; Lastarria 1,29)» | REFUTADA: los números se reproducen, la lectura no. No son las mismas publicaciones y K no las mueve |
| 4. «Lastarria 1,29 km es el campo fumarólico real» | SIN DATO (lectura heredada, no medida acá) |
| 5. «Sobre-publicación y mala posición de VIIRS 375 son el mismo mecanismo» | PARCIAL: es la misma población (lo medí), el mecanismo no está demostrado |

## Qué cambia en la historia física

En los volcanes nevados (Villarrica, Llaima, Copahue, Planchón Peteroa) el Test 1 integra la radiancia MIR del
disco de 3 km y el cúmulo que queda es un píxel suelto en el borde del disco, el lado más tibio del gradiente de
altitud (A69). Eso es cierto. Pero el pipeline ya sabía eso desde S106: cuando el record es «Test 1 dominante» (no
hay cúmulo contextual), `pipeline/anchor.py:89` fija la posición oficial en el cráter (`final_hotspot_source =
"test1_roi"`, distancia 0,0) y el tablero pinta ese punto, no el cúmulo (`frontend/index.html:2994-3003`; el
comentario de `index.html:1653-1656` dice explícitamente que el cúmulo de esos records «no es la posición del
record»). O sea que la mayoría de esas publicaciones el geólogo de turno las veía **en el cráter**, no en el flanco.

Y K no relocaliza nada: K publica un **subconjunto estricto** de lo que publica C0 (0 publicaciones nuevas en los 11
volcanes), y las que conserva **ya estaban en el cráter con C0**. Lo que hace K es dejar de publicar las pasadas
cuyo cúmulo estaba en el borde del disco, y esas pasadas son casi todas negativos limpios (713 de 1.363) o sin
información (587), con 21 positivas. Por eso la parte 5 se sostiene como «misma población», no como «mismo
mecanismo».

## Hallazgos

### H1. Las publicaciones que K conserva ya estaban en el cráter con C0: el «se juntan» es selección, no corrección
- Archivo: `experiments/_s153_localizacion/offset_c0_contra_k_v1.py:25-28` (compara C0 entero contra K entero, sin parear).
- Qué pasa: compara la mediana de 161 publicaciones de C0 con la de 6 de K en Villarrica. Pareando por pasada
  (volcán, sensor, hora), las 6 pasadas que K publica tenían el cúmulo de C0 a 0,19 km.
- Cómo se ve (salida cruda, `salida_v1_union2766.txt`):
```
volcan               C0 pub (pc)              K pub (pc)               | pareadas C0 (pc)         pareadas K (pc)          | ... | nC0 nK ambos soloK
Lascar               n 142 med 0.31 <1km  58% n  70 med 0.19 <1km  99% | n  70 med 0.20 <1km  99% n  70 med 0.19 <1km  99% | ... | 142 70 70 0
Lastarria            n 141 med 2.36 <1km   3% n  46 med 1.28 <1km   2% | n  46 med 1.29 <1km   7% n  46 med 1.28 <1km   2% | ... | 141 46 46 0
Tupungatito          n 155 med 2.16 <1km  35% n  39 med 0.20 <1km  95% | n  39 med 0.23 <1km  90% n  39 med 0.20 <1km  95% | ... | 155 39 39 0
PlanchonPeteroa      n 160 med 2.44 <1km  17% n  21 med 0.40 <1km  95% | n  21 med 0.42 <1km  95% n  21 med 0.40 <1km  95% | ... | 160 21 21 0
Llaima               n 151 med 2.74 <1km   5% n   0                    | n   0                    n   0                    | ... | 151 0 0 0
Villarrica           n 161 med 2.75 <1km   8% n   6 med 0.18 <1km 100% | n   6 med 0.19 <1km 100% n   6 med 0.18 <1km 100% | ... | 161 6 6 0
Copahue              n 158 med 2.71 <1km   4% n   0                    | n   0                    n   0                    | ... | 158 0 0 0
Chaiten              n 175 med 2.36 <1km  22% n  19 med 0.20 <1km 100% | n  19 med 0.20 <1km  89% n  19 med 0.20 <1km 100% | ... | 175 19 19 0
```
  Y lo que K quita (`salida_quitadas_v1.txt`): cúmulo de C0 a 2,45 a 2,83 km en los 11 volcanes; Villarrica 155
  quitadas a 2,76 km (90 negativos limpios, 62 sin información, 3 far_ref, 0 positivas); total quitadas 713
  negativos limpios, 587 sin información, 42 far_ref, **21 positivas**.
- Reproducir: `python -I experiments/_s153_localizacion/verificador/verif_posicion.py V1 C:/Users/nmend/AppData/Local/Temp/claude/v1_38639658446/union_2766`
  y `python -I experiments/_s153_localizacion/verificador/verif_quitadas.py <misma carpeta>` (desde la raíz del repo).
- Confianza alta (pareo directo, misma unión). Gravedad 4: como está escrita, la afirmación le atribuye a K una
  corrección de posición que no hace; lo que hace es callar.
- Control: si K moviera las publicaciones, la columna «pareadas C0» daría ~2,7 km y «pareadas K» ~0,2. El instrumento
  puede ver esa diferencia; no la ve.

### H2. El campo medido (centroide del cúmulo) no es lo que el tablero pinta para los records Test 1 dominantes
- Archivo: los cinco scripts usan `primary_cluster.centroid_lat/lon` (p. ej. `offset_por_test1.py:21`); el tablero
  pinta `final_hotspot` para `test1_roi` (`frontend/index.html:2994-3003`, marcador primario por defecto
  `onlyPrimaryPixel = true`, l. 904 y 3054-3056), usa `final_hotspot` en el mapa general (l. 3669-3673) y en la tabla
  (l. 2693-2698), y `pipeline/anchor.py:89` pone ese punto en el cráter con distancia 0,0.
- Cómo se ve (V1, brazo C0, `salida_lo_que_ve_v1.txt`), fracción de publicaciones a más de 2 km del cráter:
```
   volcan               n  | >2km pc | >2km marcador detalle | >2km general/tabla (final_hotspot)
   Llaima               151 |  83% |  32% |  24%
   Villarrica           161 |  85% |  31% |  24%
   Copahue              158 |  82% |  24% |  16%
   PlanchonPeteroa      160 |  68% |  18% |  10%
   TOTAL {'n': 1736, 'pc': 1062, 'det': 534, 'fin': 359}
```
  Mediana del marcador del mapa de detalle en producción C0 (datos de `60c45833f`, antes del backfill, 08-29 a 10-17,
  `salida_prod_pre_backfill.txt`): Villarrica 0,00 km (64 % bajo 1 km), Llaima 0,00 (62 %), Copahue 0,00 (70 %),
  PP 0,00 (75 %), contra 2,74 / 2,75 / 2,73 / 2,44 del centroide.
- Consecuencia: el «POR QUÉ IMPORTA» de la afirmación (el operador ve una anomalía en el flanco) vale para 24 a 32 %
  de las publicaciones de esos volcanes, no para 82 a 85 %. Confianza alta (código leído y portado, control sintético
  OK). Gravedad 4.
- Instrumento: a la pregunta «si lo que el operador ve estuviera roto, ¿el script lo vería?», la respuesta es no; el
  script mide el centroide, que el tablero descarta como posición en esos records.

### H3. Propio, fuera de la afirmación: con K el marcador del mapa de detalle cae lejos del cúmulo en Lastarria, Láscar e Isluga
- Archivo: `frontend/index.html:3004-3006` (rama `anomaly_pixels[0]` para `ctx_cluster`) con `onlyPrimaryPixel`.
- Qué pasa: para records `ctx_cluster` el marcador primario es `anomaly_pixels[0]`, el píxel anómalo de mayor VRP de
  **toda la escena**, que puede estar fuera del cúmulo y fuera del inner. Con K todos los records son `ctx_cluster`,
  así que el defecto queda a la vista. Es la familia A46 (dos representaciones del punto caliente).
- Cómo se ve (`salida_marcador_k.txt`, V1, brazo K):
```
2026-08-30 05:54 VIIRS_SNPP src=ctx_cluster pc_n=2 dpc=0.15 ap0=21.31 ap0_vrp=0.173 n_ap=3 ap_mas_cercano=0.16 vrp_max_ap=0.173 pc_vrp=0.077
Lascar _s149_ab_sin_test1_b22_max: publicadas con anomaly_pixels 70, ordenadas desc por vrp 70, ap0 a >2 km 23
2026-08-29 06:18 VIIRS_SNPP src=ctx_cluster pc_n=1 dpc=1.25 ap0=23.31 ap0_vrp=0.192 n_ap=3 ap_mas_cercano=1.25 vrp_max_ap=0.192 pc_vrp=0.047
Lastarria _s149_ab_sin_test1_b22_max: publicadas con anomaly_pixels 46, ordenadas desc por vrp 46, ap0 a >2 km 34
```
  En V1 con K, marcador a más de 2 km: Láscar 33 %, Lastarria 74 %, Isluga 28 %, Tupungatito 33 %, PP 24 %, contra 0 a
  33 % del centroide. En producción hoy (K desde el backfill del 2026-10-18, 09-18 a 10-18,
  `salida_prod_post_backfill_K.txt`): Láscar centroide 97 % bajo 1 km, marcador 66 %; Lastarria marcador 2,26 km de
  mediana contra 1,31 del centroide.
- Reproducir: `python -I experiments/_s153_localizacion/verificador/verif_marcador_k.py <union_2766> _s149_ab_sin_test1_b22_max Lascar`.
- Confianza alta en el dato; la forma exacta en que Leaflet lo dibuja no la miré en un navegador (SOSPECHA menor:
  que algún filtro posterior oculte ese marcador). Gravedad 4: hoy, en producción, un record del cráter puede
  dibujarse como un punto rojo de cumbre a 20 km.

### H4. La salida guardada de `offset_por_test1.py` ya no se reproduce sobre `data/` de hoy
- Archivo: `experiments/_s153_localizacion/offset_por_test1_salida.txt` y `offset_por_test1.py:14`.
- Qué pasa: entre las 10:55 y 12:27 UTC del 2026-10-18 hubo un backfill con K de 09-18 a 10-18 en los 11 volcanes
  (`5783192c1` Villarrica y siguientes). Re-corrido hoy da Láscar «con Test 1 n 70 / sin Test 1 n 38» en vez de «164 /
  2». Sobre los datos de `60c45833f` (estado del 2026-10-17 20:02 -03) el script reproduce la salida guardada línea por
  línea. «Producción (detector C0)» sólo vale para ese estado; hoy producción mezcla C0 (08-29 a 09-17) y K.
- Confianza alta. Gravedad 2 (el número era correcto cuando se escribió; hay que citar el commit de datos).

### H5. «Viene del Test 1» está medido con la bandera, no con la causa
- Archivo: `offset_por_test1.py:22` (`triggered_test1`).
- Qué pasa: la bandera dice que el Test 1 disparó, no que decidió. Cota inferior de «decide el Test 1» = records
  `test1_roi` (sin cúmulo contextual, `anchor.py:84-89`): Villarrica 115 de 189, Llaima 111 de 181, Copahue 130 de 189,
  PP 112 de 192, pero Láscar 52 de 166, Isluga 29 de 171, PCC 13 de 228. Bandera encendida: 89 a 100 %. El A/B no
  aísla el Test 1: F y K apagan el Test 1 y además cambian la conectiva a `max` (F y K dan la misma decisión en 1.944 de
  1.944 pasadas, `v1.log` sección 4), así que «lo que K quita» es Test 1 más `max`.
- Confianza alta. Gravedad 2.

### H6. K pierde 21 pasadas que el evaluador etiqueta positivas (fuera de la afirmación)
- Fuente: `salida_quitadas_v1.txt`, TOTAL `('quita', 'pos'): 21` (Lascar 0, Lastarria 4, Isluga 4, Tupungatito 4,
  NdC 4, Llaima 1, Copahue 2, PCC 1, Chaitén 1). No es el veto P1 (que mira sólo protegidas de 1 MW o más, y `v1.log`
  lo da CUMPLE); lo anoto porque la afirmación habla de «las mismas publicaciones» y no lo son. Gravedad 2, confianza
  media (etiqueta por pasada del evaluador, sin regla SN ni lectura A aplicadas acá).

## VERIFICADO LIMPIO

- Los números de C0 de la afirmación se reproducen: con los datos de `60c45833f`, centroide con Test 1 Villarrica 2,73,
  Llaima 2,75, Copahue 2,71, Láscar 0,37 (salida de `opt1_offset_por_test1_sobre_60c4583.py`, copia de `offset_por_test1.py` apuntada a los JSON extraídos con `git show 60c45833f:data/mirova_equivalent/<volcan>.json` al temporal).
  Con mi script (noche + predicado node, 08-29 a 10-17): 2,74 / 2,75 / 2,73 / 0,38.
- Los números de K se reproducen: Villarrica 0,18 (6, 100 %), Tupungatito 0,20 (39, 95 %), Chaitén 0,20 (19, 100 %),
  PP 0,40 (21, 95 %), Lastarria 1,28 a 1,29 (46).
- «Borde del disco de 3 km»: `TEST1_ROI_KM = 3.0` (`pipeline/profile.py:178`, el perfil no lo sobrescribe); p90 del
  centroide 2,97 a 2,99 en Villarrica, Llaima y Copahue.
- Punto de medida: `vent_lat/vent_lon` de `volcanoes.yaml` y del `VOLCANOES` de `index.html` coinciden a 0,000 km en
  los 11 volcanes.
- «Publicado»: el `publica()` a mano de los scripts da los mismos n que el predicado node (Villarrica 161 en V1, 189 en
  producción); el filtro nocturno no quita ningún record VIIRS 375 publicado.
- Ventana V1 (2026-08-29 a 2026-10-08) no cruza #535 (A104).
- `union_d16_v2` (la que usa el script) y `union_2766` (la del README) son idénticas byte a byte en los 22 archivos.
- Controles (`salida_controles.txt`): predicado node da `[0,1,1,1,0], [1,0]` (esperado); haversine 0,0 y 3,0 km; el port
  del marcador devuelve el cráter para `test1_roi` y `anomaly_pixels[0]` para `ctx_cluster`.

## Scripts de esta carpeta

`verif_posicion.py` (PROD con `DATADIR`, o V1), `verif_quitadas.py`, `verif_lo_que_ve_el_operador.py`,
`verif_marcador_k.py`, `controles.py`. Correr desde la raíz del repo con `python -I`. El port del marcador
(`pos_mapa_detalle`) es una transcripción de `index.html:2989-3028`, no código ejecutado con node: es la parte
menos blindada del informe.
