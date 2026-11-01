# Caminos por los que cada afirmación podría estar mal

Escrito ANTES de abrir ningún archivo citado (sólo listé directorios, leí el commit y la hora
del servidor). Verificador con contexto limpio de la ablación real del bow tie MODIS (S162).
Commit sobre el que mido: 6e3084df1fa8c9ca2285666711b9e245494bc0c8 (worktree s162-modis-774bb0).
Hora del servidor al empezar: Sat, 24 Oct 2026 19:18:15 GMT (header Date de api.github.com).

## B1. Reproducción 403 de 403 (npix, VRP, celdas) + control negativo banda 21

1. **Instrumento mide otra cosa**: la "reproducción" compara el port contra el port (misma función
   `mirova_port.py`, misma grilla rearmada por el mismo código), no contra el lote original. Si la
   grilla del lote se construyó con otra rutina (pipeline/ en el runner Linux con pyhdf) y 01 la
   rearma con `comun.py`, lo que se compara es "01 contra sí mismo" salvo que lea npix/VRP/celdas
   del `resultados_MODIS_*.json` del lote. Hay que ver de dónde salen los valores de referencia.
2. **Tolerancia que esconde**: comparar VRP con tolerancia relativa amplia o redondeado (A99 avisa
   de productos de factores opuestos); "celdas" podría ser conteo de celdas y no identidad de
   celdas (fila, columna). 403 iguales en conteo no implica 403 iguales en posición.
3. **Control negativo débil**: "banda 21 cambia 13 de 13 con detección" prueba que el instrumento
   ve un cambio de banda, pero no que vea un cambio en la grilla o en los duplicados. Un control que
   cambia la radiancia de entrada no es un control de la reconstrucción geométrica. Además 13 de 13
   son los controles con detección: en los 390 negativos (sin detección) el control no distingue
   nada porque npix = 0 en ambos lados; un cero que no distingue "no hay" de "no medí".
4. **El npz no es el insumo del lote**: si `nativo_<id>.npz` se guardó DESPUÉS del remuestreo o con
   un recorte distinto (margen, orden de filas), el rearme usa una entrada que el lote no usó, y la
   igualdad en 403 sería porque ambos leen el mismo npz, no porque el método sea el mismo.
5. **403 no es el universo**: 390 + 13 = 403, pero el lote pudo tener pasadas sin npz (fallo de
   descarga, A108) que se descartaron en silencio. Hay que contar los npz en disco y las filas de
   los json de resultados, y los objetivos en `objetivos_neg_resto_modis.json`.
6. **Copia local atrasada**: el `mirova_port.py` del árbol `_s162_modis_verif_cde/arbol/` puede no
   ser el que corrió en el runner (commit distinto). Comparar sha256 o `git show` del commit que el
   lote declara.
7. **Determinismo**: argsort inestable entre CPU (S152): si hay empates, 403 de 403 iguales en la
   misma máquina no prueba reproducción del runner. Ver si los VRP se comparan contra los json del
   runner o contra una corrida local.
8. **Ventana**: qué fechas cubren las 403 pasadas (A90) y si están antes o después de #535 y del
   flip K (A104/A85). Si todo es de un tramo, la conclusión no vale para el otro.

## B2. Método A quita duplicados sin abrir huecos reales; sus huecos son rendijas (huella +20 %); regla B abre huecos

1. **La huella nominal no es la del sensor**: MODIS a 1 km tiene huella que crece ~ sec(θ) en
   along-scan y ~ sec²... no: along-track crece con sec(θ) y along-scan con sec²(θ) (cuestión de
   geometría de barrido; verificar en el código qué fórmula usan, y no asumir). Si la cobertura
   se mide con una huella de 1 × 1 km fija, en el borde (θ > 50°) un píxel real cubre 2 × 4,8 km
   y cualquier "hueco" de la grilla de 1 km es ficticio, o al revés: con huella fija pequeña se
   fabrican huecos que no existen y luego la "huella agrandada 20 %" los cierra por construcción.
   El 20 % es un número elegido: hay que ver si el cierre de rendijas es sensible a 10 %, 15 %, 20 %,
   30 % (si cierra sólo justo en 20 %, el número está ajustado al resultado).
2. **"Visto 2+ veces" no mide duplicados**: en el borde del barrido, el traslape bow tie es real, pero
   "una celda de la grilla cubierta por 2 huellas" también ocurre dentro del mismo barrido por la
   huella agrandada (píxeles vecinos del mismo barrido que se traslapan en la grilla de 1 km
   cuando la huella es de 2 km). Es decir, "2+ veces" mezcla traslape intra-barrido (no es bow
   tie) con traslape inter-barrido (sí es bow tie). Hay que ver si el conteo distingue barridos
   distintos.
3. **El método A conserva "el barrido anterior"**: ¿cómo identifica el barrido? Si usa `fila // 10`
   sobre el recorte, y el recorte no empieza en una frontera de barrido (offset de la fila 0 del
   recorte respecto a la fila 0 del gránulo), los grupos de 10 quedan corridos y lo que llama
   "detector 0" y "detector 9" son otros detectores. Ese mismo error contamina B4.
4. **Hueco "real" definido por la grilla, no por el suelo**: si la grilla objetivo es de 1 km y la
   huella nativa en el borde es ~4,8 km along-scan, no hay huecos posibles por along-scan; los
   huecos de bow tie son along-track (entre barridos, en el centro de cada barrido NO hay traslape
   y hacia el borde el traslape crece). Al quitar duplicados por barrido anterior, lo que se quita
   son píxeles del detector 0 (o 9) del barrido siguiente; si la huella along-track en el borde es
   ~2 km, quitar una fila entera deja un hueco de ~1 km que la huella al 120 % tapa. Es decir, el
   cierre puede ser un artefacto del 20 %.
5. **Regla B "sí abre huecos"**: puede abrirlos porque borra filas enteras sin mirar si son
   duplicadas (en el nadir las filas de borde no duplican nada). Eso no refuta a B como regla de
   duplicados, refuta a B como regla ciega: comprobar si B se aplica sólo sobre θ > umbral.
6. **La cobertura se mide dentro del recorte**: en los bordes del recorte, celdas de la grilla cerca
   del borde pueden quedar sin huella porque el recorte no las cubre (efecto borde), no por bow tie.
   Si los huecos de B o de A se cuentan sin excluir un margen, se infla el conteo.
7. **Los png o la salida muestran una pasada**: si la conclusión "sin huecos reales" se extrapoló de
   pocas pasadas y no de las 403, o sólo de las de borde.

## B3. Con A, 11 protegidas publican; 2 publicaciones del port en neg_resto se apagan (copia anterior) o queda 1 (copia siguiente); donde A no quita nada, grilla idéntica

1. **"Publica" no es el predicado del tablero**: la vara es `isSummitDetection && isValidDetection
   && !isThermalArtifact && mirovaEqVrpDisplay > 0` ejecutado con node por `banco_paridad.correr_node`.
   Si 03 usa `npix > 0` o `vrp > 0` del port como "publica", mide otra cosa (el port no pasa por el
   tablero; para el port la vara es el record sintético `record_port` de `_s159/portes/04_analizar.py`).
2. **Las 2 publicaciones en neg_resto se apagan por otra razón**: si A quita píxeles por fila entera
   en el borde, puede apagar un foco porque le quitó el píxel caliente (no un duplicado), es decir,
   el método fabrica el apagado. Hay que ver en 04_casos si el píxel alertado estaba duplicado
   (misma celda vista dos veces) o si simplemente estaba en la fila que A borra.
3. **"Queda 1 conservando la siguiente"**: si el resultado depende de qué copia se conserva, el
   detector decide por una diferencia de radiancia entre dos copias del mismo suelo; eso
   indica que el foco está en el umbral y es ruido de selección, no efecto del bow tie en sí.
4. **"Grilla idéntica donde A no quita nada"** es tautológico si el método es "quitar y remuestrear";
   sólo es informativo si el remuestreo tiene un paso no determinista (argsort) o si la "huella
   agrandada" entra al remuestreo (si el remuestreo del port cambió por la huella, la grilla no
   sería idéntica). Verificar que el remuestreo de 03 sea el del port sin cambios.
5. **Las 11 protegidas**: ¿siguen publicando con la misma magnitud o sólo con npix > 0? Si una
   protegida pierde 40 % de VRP pero sigue "publicando", el "siguen publicando" esconde el daño.
   Ver B4.
6. **Denominador**: 13 controles con 11 protegidas; ¿los otros 2 controles? Si son alertas < 1 MW,
   su resultado también importa (bajo 1 MW pesan igual perdida y publicación de más).
7. **2 de 390 publicaciones en neg_resto**: con K en producción, neg_resto son negativos donde la
   producción calla; el port publica 2. Apagar 2 es "mejora" de 0,5 % con n = 2: sin poder
   estadístico; cualquier conclusión sobre "A mejora la paridad" es sobreinterpretación.

## B4. Magnitud de protegidas cambia sólo donde el foco sale dos veces; signo depende de la copia; "cráter en detector 0 o 9" no delimita la franja sobre 50°; estrato útil es "cráter cubierto por 2+ huellas"

1. **Identificación del detector**: ver B2.3: si el recorte no arranca en frontera de barrido, el
   detector asignado al cráter está corrido y la conclusión "0 o 9 no delimita" sería un artefacto
   del offset, no una propiedad de la geometría.
2. **"Cubierto por 2+ huellas"** con la huella agrandada 20 % cuenta traslapes intra-barrido (B2.2),
   así que el estrato "útil" podría incluir cráteres que no están duplicados por bow tie. Si el
   estrato se define con la misma huella que cierra las rendijas, la conclusión es circular.
3. **El signo depende de la copia**: si conservar la anterior baja y conservar la siguiente sube (o
   al revés), hay que ver si es un efecto de ángulo de visión real (la copia más cercana al nadir
   del barrido tiene menor huella, mayor radiancia por m²?) o si es simplemente que las dos copias
   difieren por ruido. Con n chico (cuántas protegidas duplicadas: 2, 3?) el signo es anécdota.
4. **"Sobre 50°"**: ¿cuántas protegidas hay sobre 50°? Si son 2 o 3, "no delimita" se afirma sobre
   un n que no delimita nada. Y el umbral de 50° viene de dónde (paper, D28, elegido).
5. **La franja duplicada**: en MODIS el traslape bow tie empieza alrededor de 25° (a 1 km, los
   barridos vecinos se traslapan a partir de ~ 24-25° de zenit de escaneo; esto hay que verificarlo
   en la referencia, no de memoria: marcar SOSPECHA). Si el análisis supone que los duplicados
   sólo existen sobre 50°, pierde la franja 25-50° donde hay traslape parcial (sólo detector 0/9).
6. **Magnitud "cambia sólo donde el foco sale dos veces"**: el remuestreo con/ sin duplicados también
   cambia el FONDO (μ, σ del ROI) aunque el foco salga una vez, porque los píxeles de fondo
   duplicados cambian la estadística. Si la magnitud (VRP del cúmulo) depende de t_bg, puede
   cambiar sin que el foco esté duplicado. Hay que mirar si "cambia" se mide con tolerancia 0 o
   con tolerancia que oculta cambios de fondo.

## Transversales

- La hora de la corrida del lote y la del json: si el lote corrió sobre un commit distinto del port
  que el que está en `arbol/`, toda la reproducción está contra una copia atrasada.
- El port es MATLAB portado (S158: validar contra Octave); si el bow tie en MATLAB original hace algo
  que el port no, D28 se mide contra el port, no contra MIROVA. La conclusión "qué cambia al quitar
  duplicados" vale para el port.
- No leer el INFORME.md del auditor hasta terminar caminos (este archivo). Después sí, sólo para
  comparar títulos con lo medido.
- Control positivo que debo correr yo: una mutación que seguro cambia la grilla (por ejemplo,
  desplazar el recorte una fila, o quitar un píxel caliente) y ver que 01/03 lo detectan.
- Denominadores y ventanas de cada número.

---
sha256 (antes de esta línea): c34554d66b42de05c682eb07d5a34baefecf70da361130755c91ee53e5aa554f
Hora del servidor al cerrar: Date: Sat, 24 Oct 2026 19:20:12 GMT
