# Caminos por los que cada afirmacion de la tercera vuelta podria estar mal (escrito ANTES de abrir ningun archivo citado)

Verificador D-42, vuelta 3. Worktree C:\vrp-trabajo\s159-evaluador, commit 20ac098a3 (arbol limpio). Diff: 452956cf8..20ac098a3 (solo instrumentos y salidas en placebos_d44/, mas NOTA_D44.md en 172313c2d; el evaluador no cambia segun el stat).
Hora del servidor al empezar: Thu, 22 Oct 2026 18:20:34 GMT. Lo unico que mire: `git diff --stat`, `git log --oneline -3`, `ls placebos_d44/`.
No abro README.md de placebos_d44 hasta tener escritos los veredictos.

## Afirmacion 1: 444 corridas, brazos desde produccion, P2 calibrada como esta; cada pasada tocada llega cambiada y ninguna otra; evaluador sin M; con una semilla por ventana el evaluador entero da P2 identico

- «444»: contar yo las filas de los JSONL y las caidas; una corrida CAIDA no es una corrida.
- «desde produccion»: el sustrato de V2 (2026-04-01 a 2026-06-12) NO es produccion de esa fecha sino el historico reprocesado con K (`sustrato_k.unir_k`); si el script carga `data/mirova_equivalent` directo para V2, el brazo base no es K. Mirar que funcion carga.
- «P2 calibrada como esta»: `evaluar_sin_m.py` puede ser una COPIA del evaluador con M quitado, y una copia puede divergir (A102); comprobar que importa `evaluar_d25` y reutiliza `contar`/`decidir_p2_bloques`, o que el diff contra el evaluador es solo el salto de M; y que no fija otra semilla ni otro N.
- «cada pasada tocada llega cambiada a la tabla y ninguna otra»: hay que ver que lo comprueban contra la tabla `t_K_D.json` (publicacion de K contra D por pasada) y no contra la lista de elegidas; pasadas tocadas en dias excluidos (V1) no llegan y deben contarse aparte; una pasada «encendida» (de no publicada a publicada) exige que el predicado del tablero la publique de verdad (umbral de VRP, inner radius, distance_class): si se enciende poniendo pc.vrp_mw a un valor pero el record queda far o sin cumulo, no llega. Un record sin primary_cluster no se puede encender.
- «evaluador sin M da P2 identico»: la comparacion tiene que ser por pasada y por campo (veredicto, neto, n, noches, falsos, ic95) y sobre las DOS reglas (original y SN) y los dos sensores; si solo compara el veredicto, una diferencia en falsos pasaria.
- Una semilla por ventana es n = 2: no prueba igualdad en general; lo que prueba es que el salto de M no toca P2 en esos dos casos.

## Afirmacion 2: negativos limpios 4,8 % / 18,2 % (V1) y 2,8 % / 8,7 % (V2) de las publicaciones de K

- El denominador: ¿todas las publicaciones de K en la tabla (incluidas protegidas, sin_info, far_ref) o solo las que cuentan en P2? Contar yo desde la tabla del nulo si existe, o desde los JSONL.
- V1 con dias excluidos: ¿los cuentan? La fraccion cambia poco, pero el numero no se reproduce exacto si no.
- Esa fraccion es por regla (original/SN): bajo SN las alertas de 0,05 MW o menos pasan a negativos limpios, asi que la fraccion de negativos es mayor bajo SN. Ver cual regla declara el numero.

## Afirmacion 3: placebo (a) apagar negativos limpios: GANA 40 de 40 en V1 al 50 %; 26 de 40 en V2 (14 INDECIDIBLE)

- «40 de 40» = 20 semillas x 2 reglas en un sensor, o 20 x 2 sensores. Aclarar el denominador por sensor y regla.
- 14 INDECIDIBLE en V2: ¿por calibracion fallida con todas las noches del mismo lado (punto 5) o por controles? Mirar falsos_gana, falsos_pierde y noches de esas celdas.
- GANA es lo esperado por construccion (solo se quitan errores); lo que mide es PODER, no falsos. Que no se venda como control de falsos.

## Afirmacion 4: placebo (b) apagar alertas bajo 1 MW: PIERDE 40 de 40 en V2 al 10, 25 y 50 %; en V1 solo VIIRS 375 con sustrato, 16 a 20 de 20; nunca direccion equivocada

- Las que no son PIERDE en V1 (hasta 4 de 20): ¿INDECIDIBLE por calibracion, BLOQUEA, SIN SUSTRATO? Contar.
- «apagar alertas bajo 1 MW»: ¿excluye protegidas (que irian a P1, veto) y SNPP solo OCR? Si apaga protegidas, P1 VETADO y el estado de la ventana ya no es de P2.

## Afirmacion 5: con noches desiguales (11 en 10 noches, 8 en 7) la calibracion cae en 4,9 a 6,7 % por cola e INDECIDIBLE aunque todas vayan del mismo lado

- Reproducir con sinteticos: 10 bloques con uno doble (11 contribuciones del mismo signo), 7 bloques con uno doble. Con B bloques todos del mismo lado, la probabilidad de que un sorteo deje todos los bloques del mismo lado es 2^(1-B): B = 10 da 0,2 %, B = 7 da 1,6 %; eso NO explica 4,9 a 6,7 %. Lo que si: con un bloque de peso 2 y el resto de peso 1, el intervalo bootstrap al 95 % del neto de un sorteo queda entero sobre 0 en mas sorteos que «todos del mismo lado»: basta que la mayoria ponderada sea suficientemente grande. O sea que la tasa de falsos de la REGLA DE D-34 (intervalo bootstrap de bloques) bajo el nulo de signos es de 5 a 7 % con pocos bloques, mas que el 2,5 % nominal por cola, y la calibracion la ve y la rechaza. Entonces no es un defecto de la calibracion: es que la regla de D-34 no esta calibrada al 5 % con pocos bloques, y el tope del 5 % con 1.000 sorteos tiene ademas ruido de muestreo (desvio 0,7 puntos): un valor verdadero de 5,0 % cae de un lado u otro al azar (frontera discreta).
- Opciones para Nicolas: (i) dejar como esta (costo: INDECIDIBLE con 7 a 10 noches todas del mismo lado, que es justamente un efecto grande); (ii) decidir P2 DIRECTAMENTE con la prueba de sorteo por bloques (valor-p exacto: fraccion de sorteos con neto tan extremo como el observado; con B bloques el minimo es 2^(1-B), asi que decide desde 6 bloques al 5 % a dos colas o 5 a una cola), que es una prueba de permutacion de signos clasica, calibrada por construccion, y entonces el bootstrap sobra; (iii) subir el tope a algo coherente con el nivel nominal; (iv) mas sorteos para reducir el ruido de la frontera. No decido; informo con numeros.
- Reproducirlo con la funcion real y ademas calcular el valor-p exacto de signos para esos mismos casos.

## Afirmacion 6: placebo (c) simetrico con moneda justa por pasada tocada; neto medio 0; calibrada GANA 7 de 400, PIERDE 7 de 400; en V1 50 % se agregaron 80 semillas

- «la receta pedida no puede dar esperado 0 con K»: cierto si casi no hay alertas bajo 1 MW sin publicar (encender una pasada no publicada casi siempre enciende un negativo limpio, +1): comprobar con la composicion de las no publicadas.
- La moneda justa por pasada: +1 (apagar una alerta publicada o encender un negativo limpio) o -1 (apagar un negativo limpio publicado o encender una alerta no publicada): ¿como eligen la pasada para cada signo? Si para -1 apagan negativos limpios publicados (escasos) y para +1 apagan alertas publicadas, el conjunto tocado no es «al azar entre las publicaciones», es estratificado; el nulo que produce es «signos iid por pasada», que NO es el nulo de la calibracion (signo por BLOQUE noche-volcan). Bajo signos iid por pasada las contribuciones de una noche no comparten signo, asi que el bootstrap por bloques es CONSERVADOR y la calibracion por bloques tambien: la tasa de falsos medida seria una cota inferior de la tasa bajo el nulo por bloques. Es decir, el placebo (c) asi armado mide la tasa de falsos de P2 calibrada bajo un nulo mas facil que el que la regla asume; no mide la tasa bajo el nulo de D-42.
- Con moneda justa, el neto esperado es 0, pero el conjunto de pasadas tocadas sigue sin ser representativo de lo que D25 toca (D25 cambia magnitudes de cumulos reales, correlacionados por noche).
- «agregar 80 semillas en V1 50 % porque con 20 daba PIERDE 2 de 20»: es parada opcional: se decidio ampliar DESPUES de ver un resultado desfavorable y solo en ese punto. Sesga a la baja la tasa agregada (7 de 400) porque los puntos «buenos» quedaron con 20 y el «malo» se diluyo con 80 mas. Lo correcto: declarar n antes, o ampliar TODOS los puntos por igual, o reportar el punto con sus 20 primeras semillas aparte (2 de 20 = 10 %, Wilson 3 a 30 %) y las 80 nuevas aparte. Comprobar si los JSONL x1..x4 son tandas nuevas (semillas distintas) y si el resumen las mezcla.
- 7 de 400 por cola: por cola el nominal de la regla sin calibrar es 2,5 %; 1,75 % con Wilson 0,9 a 3,6 %: compatible con calibrado; pero 400 no son independientes (20 semillas x 2 reglas x 2 sensores x puntos sobre la misma ventana): las dos reglas comparten casi todas las pasadas, los dos sensores no. Contar unidades independientes reales.

## Riesgos propios

- Copias en experiments/_mutv42c_*/ si hago mutaciones; no toco nada del repo mientras corra pytest; no corro el evaluador sobre nada del A/B.

---
sha256 del contenido anterior a esta linea (head -n -4 caminos.md | sha256sum): 6f0d06320bf03ad04f876a06dc1776e287c81a2014d139d9cfb21f5080489017
Hora del servidor al cerrar caminos.md: Date: Thu, 22 Oct 2026 18:22:37 GMT
