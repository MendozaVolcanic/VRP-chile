# Caminos por los que las afirmaciones podrian estar mal (escrito ANTES de leer el informe)
Hora del servidor (GitHub Date header): Mon, 26 Oct 2026 03:18:36 GMT

## Afirmacion 1 (regla Delaunay perturbado reproduce MATLAB)
1. El script lee BK/LBK/VRP de resultado_o2.mat y los copia o los usa para elegir entre triangulaciones (oraculo filtrado).
2. La tolerancia (1e-15 relativo) esta bien, pero se compara contra algo que ya es el propio calculo (misma variable en ambos lados).
3. Las "166" escenas no son las 166 de MATLAB (indice base 0 vs 1, IDX_O1 mal usado, escenas repetidas, orden distinto que enmascara).
4. El fondo se calcula solo en los pixeles que MATLAB tiene como NaN; si la mascara viene de MATLAB, hay fuga.
5. La regla "perturbacion simbolica" tiene parametros libres ajustados escena por escena (p. ej. se elige el desempate que mejor ajusta por escena).
6. Control de ejes cambiados (42/166): quiza solo cambia el orden de tuplas y no la geometria; o es trivial (la mayoria de escenas sin empates da igual).
7. Nulo de 20 desempates al azar: puede que los desempates "al azar" produzcan la misma triangulacion en la mayoria de escenas (no son realmente distintos), o el maximo 110/166 sea una cota que no muestra el minimo.
8. Escenas sin cuadrados cocirculares (sin empate) cuentan como aciertos triviales: la potencia real esta en las escenas con empates.
9. Version Octave vs MATLAB: el informe usa salida de Octave como "verdad" en algun paso.
10. La interpolacion lineal sobre triangulos coincide con MATLAB para otras reglas igual de bien (la regla no es unica).

## Afirmacion 2 (6 pasadas, nada separa)
1. Pareo con MIROVA: fecha/hora, volcan o sensor mal emparejado; tolerancia temporal; pasada de otra hora.
2. Agregacion: log-razon vs razon simple vs mediana vs por volcan puede cambiar el veredicto.
3. El nulo por barajado y bootstrap con n=6 tienen poca potencia; "no separa" no es "equivalentes".
4. VRP MIROVA de un pixel incluye regrillado distinto (UTM), ruido dominante: la conclusion puede ser cierta pero la cifra de potencia (50 a 100 pasadas) es una extrapolacion sin script.
5. Las 6 pasadas pueden venir de periodo con calidad de referencia pobre (A119).
