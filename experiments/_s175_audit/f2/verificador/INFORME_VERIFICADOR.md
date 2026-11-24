# Verificador S175 F2: seis afirmaciones del auditor (VIIRS 375, 2026-03-01 a 2026-11-07)

- Hora del servidor: `Sat, 07 Nov 2026 04:39:23 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera Date).
- Modelo: Claude Opus 5.5 (`claude-opus-5-5`). Esfuerzo real: SIN DATO.
- Carpeta de scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2\verificador\`
  (abajo, `VER\` es esa carpeta). Temporales en `C:\Users\nmend\vrp-temporales\s175_audit\f2\verificador\` (`TMP\`).
- Llamadas a la API de GitHub: 4 (Date, sha de main, contenido del lector en main y en fc3912cb2).
- No usé los scripts del auditor para medir. Leí `confirmado_publicados.py` y la línea 145 de su `INFORME.md`
  sólo después de tener mi número de A4, para saber qué contó él.

## Integridad del material

Antes de medir comparé el blob git de la base con el archivo del árbol, sin filtros de fin de línea
(`git show 752d348bc:<ruta> | git hash-object --stdin` contra `git hash-object --no-filters <arbol>/<ruta>`), en
`frontend/index.html`, `scripts/banco_paridad.py`, `scripts/clase_mirova.py`, `data/mirova_equivalent/Lastarria.json` y
el consolidado del snapshot: los cinco iguales. Las copias de `insumos\snapshot_*_base.csv` tienen el mismo md5 que el
snapshot del árbol. El lector del árbol del tag tiene el mismo blob (`e720dbc46`) que `fc3912cb2:<ruta>`, y el tag
`s172-v375e-lector-resellado` apunta a `fc3912cb2357f6afe65445818c53a44e87316bbb`.

Vara aplicada: `cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)` (snapshot de la base, con historia y respaldo),
`indexar_referencia(..., regla_minimas="SN")`, `cargar_nuestros`, `etiquetar` y `correr_node` del árbol base, todo
importado desde el árbol (el script verifica que `banco_paridad.__file__` cuelgue del árbol). `flag_viirs_diurno()` da
False, así que el filtro nocturno sí actúa. Protegida = `clase_mirova.alerta_protegida` (lectura A, 1 MW) sobre las
filas que `parear` devuelve a ±120 s, después de la regla SN.

## A1. 171 protegidas, 166 publicadas, 5 no publicadas; todas las noches protegidas publican: CONFIRMADO

Dos preguntas. Si el conteo de protegidas estuviera roto, ¿lo vería? Sí: el control con umbral 0 sube el conteo a
1.469 (todas las `pos`) y con umbral 1e9 da 0; y las 171 tienen etiqueta `pos` (deben tenerla). Si el predicado
estuviera muerto, ¿se vería distinto? Sí: el control de identidad del predicado da `([0,1,1,1,0],[1,0])`, el esperado,
y entre las 166 publicadas hay 110 con display de 1 MW o más (un predicado muerto daría 0 publicadas o displays nulos).

Mi número: 171 pasadas protegidas con record (171 claves únicas volcán, sensor y hora; 0 duplicadas), 166 publicadas,
5 no publicadas, exactamente las cinco que nombra el auditor:

| Pasada | Sensor | Cenit | Fila MIROVA (única, OCR) | Nuestro record |
|---|---|---|---|---|
| Láscar 2026-08-22 05:06 | SNPP | 59,32 | OCR 1,65 MW, 1,22 km | 1 píxel a 8,86 km (inner 5), 0,51 MW, far |
| Lastarria 2026-04-18 04:42 | NOAA-20 | 67,02 | OCR 1,29 MW, 2,48 km | 1 píxel a 19,63 km (inner 3), 0,53 MW, far |
| Lastarria 2026-05-02 05:06 | SNPP | 59,49 | OCR 2,36 MW, 2,48 km | 1 píxel a 19,55 km (inner 3), 1,11 MW, far |
| Tupungatito 2026-09-28 05:18 | SNPP | 48,77 | OCR 2,51 MW, 5,27 km | 1 píxel a 21,25 km (inner 7), 0,15 MW, far |
| Tupungatito 2026-09-29 04:54 | SNPP | 62,41 | OCR 1,86 MW, 5,68 km | 1 píxel a 7,52 km (inner 7), 1,11 MW, far |

Distancias de píxel calculadas por mí (haversine desde las coordenadas de `volcanoes.yaml`); control positivo: las
pasadas publicadas de la misma noche (Láscar NOAA-20 05:24, Tupungatito NOAA-20 05:36) salen `summit` con píxeles
dentro del inner, así que el cálculo distingue. Por noche: 111 noches de volcán con alguna protegida; las 111 tienen
alguna pasada publicada de VIIRS 375 (y por tanto de cualquier sensor). En las 5 noches de las pérdidas publicó otra
pasada VIIRS 375 de la misma noche (tabla en la salida).

Dos cosas que el auditor no dice y que cambian la lectura de las 5:
1. **El píxel de Tupungatito 2026-09-29 está apenas fuera del inner**: 7,52 km desde la coordenada de
   `volcanoes.yaml` contra 9,40 km del `centroid_dist_km` del record (el pipeline mide desde otro ancla). Con inner 7,
   la pérdida depende de medio kilómetro y del ancla. Láscar: 8,86 contra 8,23.
2. **Las 5 filas OCR tienen una salvedad de calidad conocida**: 4 son Suomi NPP anteriores al 2026-10-09 (hito del
   propio `calidad_referencia_mirova`: en filas sólo OCR de Suomi NPP la distancia puede ser de OTRA pasada) y las
   dos de Lastarria son anteriores al 2026-06-11 (OCR mal calibrado, A119). Además la distancia de MIROVA (1,2 a 5,7
   km, dentro del cráter) y la nuestra (7,5 a 21,6 km) no describen el mismo foco. SOSPECHA, no medido: parte de las
   5 «pérdidas» puede no ser pérdida de un foco que MIROVA vio en esa pasada.

Comando: `python VER\v_a1_a3.py <arbol_base> TMP\v_a1_a3.json` y `python VER\v_a1_pixeles.py <arbol_base>`.
Salidas: `VER\v_a1_a3_salida.txt`, `VER\v_a1_pixeles_salida.txt`.

## A2. Cenit de 50° o más: se pierden 4 de 36; bajo 50°: 1 de 135: CONFIRMADO

Dos preguntas. Si el campo de cenit estuviera roto (None o constante), ¿lo vería? Sí: imprimo cuántas protegidas
tienen cenit None (0) y los cenits de las 5 pérdidas (59,32; 67,02; 59,49; 48,77; 62,41), que varían. Si el
instrumento estuviera muerto, el cruce daría todo en una celda; da cuatro celdas pobladas.

Mi número: (cenit ≥ 50, publica) = 32; (≥ 50, no publica) = 4; (< 50, publica) = 134; (< 50, no publica) = 1. O sea
4 de 36 y 1 de 135. Sensibilidad al corte (Fisher exacto, mío): con corte 48,5° quedan 5 de 50 contra 0 de 121
(p 0,0018); con 50°, p 0,0073; con 58°, 4 de 26 contra 1 de 145 (p 0,0019); con 60° se diluye (2 de 21 contra 3 de 150,
p 0,11). El contraste no depende de los tres Láscar en 49,5° a 49,8° (los tres publicados). Salvedad: son 5 eventos,
y los 5 tienen además la salvedad de la referencia de A1.

Comando: `python VER\v_a1_a3.py ...` (bloque A2) y el bloque Fisher sobre `TMP\v_a1_a3.json`.
Salidas: `VER\v_a1_a3_salida.txt`, `VER\v_a2_fisher_salida.txt`.

## A3. Publicación en negativos limpios: 161 de 4.087; Lastarria 49 de 191; Puyehue 43 de 371; ninguno con display ≥ 1 MW: CONFIRMADO

Dos preguntas. Si la etiqueta estuviera rota, ¿lo vería? Sí: el reparto de etiquetas V375 es 1.469 `pos`, 4.087
`neg_limpio`, 374 `far_ref`, 64 `sin_geometria`, 5.531 `sin_info` (no colapsa en una clase). Si el display estuviera
muerto, el máximo en negativos daría 0 y también en positivos: en las protegidas publicadas hay 110 de 166 con display
≥ 1 MW, así que el campo puede pasar de 1.

Mi número: 4.087 negativos limpios, 161 publicados. Lastarria 49 de 191, PuyehueCordonCaulle 43 de 371 (también Chaitén
24 de 544, Tupungatito 13 de 258, Planchón 11 de 320, Láscar 8 de 135, Chillán 6 de 457, Isluga 3 de 68, Villarrica 3 de
560, Llaima 1 de 602, Copahue 0 de 581). Display máximo en un negativo publicado: 0,378 MW (Puyehue 2026-10-08 05:30); 0
con 1 MW o más. Último negativo limpio: 2026-11-02 (ver A6: sin consolidado después, no puede haber negativos limpios
del 3 al 7 de noviembre; las protegidas de esos días sólo pueden venir del OCR).

Comando y salida: los de A1 (bloque A3).

## A4. Confirmación del tablero: código CONFIRMADO; «más de 600 sin ninguna fila de MIROVA a ±120 s»: CONFIRMADO EN PARTE

Código (leído en `frontend/index.html` de la base, l. 1544 a 1583 y 1336 a 1363): `enrichWithMirovaConfirmation` salta
sólo clasificación NULO o RUTINA y VRP no mayor que 0, exige el mismo bucket de sensor, usa `TOL_MS = 60 * 60000`, guarda
la distancia sólo para el tooltip y no aplica D-9. `isCirrusArtifact` e `isDiffuseFieldArtifact` devuelven false con
`r._mirova_confirmed`. Lo ejecuté con node (función extraída del HTML, no portada).

Dos preguntas. Si la función estuviera rota, ¿lo vería? Control sintético: una alerta de 0,03 MW a 40 km y 59 min
confirma (1), a 61 min no (0), VRP 0 no, RUTINA no, otro bucket no, 750 contra 750 sí: salida `[1,0,0,0,0,1]`, la
esperada. Si estuviera muerta: con la lista de MIROVA vacía da todo 0, y con datos reales da 3.554 de 11.525, no 0 ni
todo.

Mi número: de 2.632 records V375 nocturnos publicados por la vara, 2.225 quedan confirmados. Sin fila en
`data/mirova/<volcán>.json` (lo que lee el tablero, sólo alertas) a ±120 s: **647**, igual que el auditor. Pero sin
NINGUNA fila de MIROVA a ±120 s en la referencia unificada (consolidado, OCR, historia y respaldo, todos los tipos):
**448**; sin fila en ninguna de las dos fuentes: **431**. Las otras 216 de las 647 sí tienen fila de su propia pasada:
143 RUTINA del consolidado (MIROVA miró esa pasada y no vio nada, y el tablero dice «MIROVA confirmó») y 73 FALSO_POSITIVO.
El título del auditor («647 no tienen ninguna fila de MIROVA de su propia pasada») es falso para esas 216; lo cierto es
que 647 no tienen ALERTA de su pasada, y 143 de ellas tienen una RUTINA explícita, lo que es peor de lo que él dice.

Dos hallazgos que el auditor no informa en esta pregunta:
1. **La marca no cambia ninguna publicación V375 en la ventana**: corriendo el predicado del tablero con la marca del
   navegador puesta, publican 2.632, igual que con la marca en false; 0 records cambian, porque 0 de los 11.525 son
   artefacto térmico. Control: un cirrus sintético (260 K, 20 MW, summit) pasa de artefacto y no publicado a publicado
   con la marca. El defecto es de etiqueta y color, no de publicación (en VIIRS 375 y en esta ventana).
2. **53 de los 161 negativos limpios publicados salen «confirmados por MIROVA» en el tablero**; 48 de esos 53 sólo
   tienen alertas de 0,05 MW o menos a ±60 min (las que D-9 convierte en negativo). Port en Python validado contra el
   conteo con node (53 en ambos).

Comandos: `python VER\v_a4.py <arbol_base> TMP\v_a1_a3.json TMP\node_a4`, `python VER\v_a4b_efecto.py <arbol_base>
TMP\node_a4b`, `python VER\v_a4c_neg_confirmados.py <arbol_base> TMP\v_a1_a3.json`.
Salidas: `VER\v_a4_salida.txt`, `VER\v_a4b_efecto_salida.txt`, `VER\v_a4c_salida.txt`.

## A5. Lector del tag: (b) CUMPLE con P2 contra K y silencio en SIN SUSTRATO; S7 no cae con negativos en n 0: CONFIRMADO

Ejecuté `criterios_sombra` y `control_s7` del archivo del tag con entradas sintéticas (sin llamar a `main`, sin leer
ninguna lectura de la sombra). Dos preguntas: si la función no reaccionara a nada, ¿lo vería? Sí, con controles que
deben dar NO CUMPLE y caída.

- p2k = SIN SUSTRATO, silencio = «SIN SUSTRATO (faltan negativos de alguna clase)» (el literal que pone `leer_brazo`),
  p2l = SIN SUSTRATO o EMPATE: (b) CUMPLE y estado CUMPLE. Controles: p2l PIERDE, p2k PIERDE o silencio ENCIENDE DE MAS
  dan NO CUMPLE. Precisión que la afirmación omite: hace falta además que P2-L no sea PIERDE ni BLOQUEA, y con la marca
  de régimen caída el CUMPLE pasa a DECIDE NICOLAS. El reporte del lector marca el caso como «CUMPLE POR FALTA DE
  EVIDENCIA» (`b_sin_evidencia`, l. 627 y 750), así que no es silencioso en el texto, pero el criterio sí cuenta CUMPLE.
- `control_s7` con `neg_pub` y `neg_resto` en n 0 y el resto completo: pasa (True). Control: `neg_pub` con 50 % sin
  dato cae; población vacía cae. Algo más: con una sola pasada `far_tabla` y ninguna protegida ni negativo, S7 también
  pasa (la condición es `if c in CLASES_DECIDEN and n and ...`).

Comando: `python VER\v_a5.py <arbol_tag>\experiments\_s168\v375e_sombra\leer_sombra_v375e.py`. Salida: `VER\v_a5_salida.txt`.

## A6. Consolidado de la base sin VIIRS375 después del 2026-11-02; el lector no está en la base ni en main: CONFIRMADO

Dos preguntas. Si el lector del CSV estuviera roto, ¿lo vería? Sí: lee 46.351 filas con los tres sensores y 19 filas
VIIRS375 del mismo 2026-11-02. Si la búsqueda en git estuviera muerta, ¿daría lo mismo? No: el mismo `ls-tree` encuentra
el archivo en `fc3912cb2` y en el tag, y la API devuelve su blob con `ref=fc3912cb2` mientras da 404 con `ref=main`.

Mi número: VIIRS375 máximo `2026-11-02 06:24:01`, 0 filas después del 2026-11-02 (igual VIIRS 750 y MODIS; máximo global
`2026-11-02 12:20:00`). Ojo: el OCR del snapshot sí llega más lejos (la referencia unificada tiene VIIRS375 hasta
`2026-11-06 06:42:01`), así que la ventana hasta el 7 de noviembre tiene positivos pero no negativos limpios.
`git ls-tree` del lector: vacío en `752d348bc` y en `origin/main` (`c33b9d5df`, que es el mismo sha que devuelve la API
para main, 2026-11-07T04:32:06Z); presente en `fc3912cb2`. Ningún archivo `leer_sombra*` existe en la base ni en main
(tampoco en `origin/loop/activo` local, `6dc46f573`, ref local no contrastada con el remoto: SOSPECHA de frescura).

Comandos: script csv en línea (salida en esta sesión), `git ls-tree --name-only <ref> -- <ruta>`, `gh api
repos/MendozaVolcanic/VRP-chile/contents/<ruta>?ref=main` y `?ref=fc3912cb2`. Salida del conteo del CSV:
`VER\v_a6_salida.txt`; las salidas de git y de la API son tool results de esta sesión, sin archivo.

## Resumen

| | Veredicto | Número del verificador |
|---|---|---|
| A1 | CONFIRMADO | 171 / 166 / 5, las mismas 5; 111 de 111 noches publican |
| A2 | CONFIRMADO | 4 de 36 contra 1 de 135; robusto entre 45° y 58° |
| A3 | CONFIRMADO | 161 de 4.087; 49 de 191; 43 de 371; máx 0,378 MW |
| A4 | CONFIRMADO EN PARTE | código tal cual; 647 sin alerta de su pasada, pero sólo 448 sin ninguna fila (143 con RUTINA); 0 publicaciones cambian |
| A5 | CONFIRMADO | (b) CUMPLE si además P2-L no PIERDE ni BLOQUEA; S7 pasa con negativos en 0 |
| A6 | CONFIRMADO | 0 filas VIIRS375 después del 2026-11-02; lector ausente en base y main |
