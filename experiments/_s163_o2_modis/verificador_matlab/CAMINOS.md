# Caminos por los que la afirmacion podria estar mal (escritos ANTES de leer regla_contra_matlab_modis.py ni RESULTADO_O2_MODIS_MATLAB.md)

Afirmacion a verificar: la regla de delaunay_perturbado.py reproduce a MATLAB R2026b (fillmissing2 'linear') en 191/191 escenas MODIS distintas (404 escenas corridas), incluidos bloques 2x2, y el port de Python no lo hace en alertas de 1 pixel y de bloques 2x2.

## A. Procedencia e integridad
- A1. resultado_o2_modis.mat no es el de este paquete (md5 distinto, o fue generado desde otras entradas que entradas_o2_modis.mat). Comprobar md5 y que las entradas dentro del resultado coinciden con entradas_o2_modis.mat.
- A2. El .mat de resultado no contiene la salida de fillmissing2 sino otra cosa (p.ej. el VRP final, o la matriz ya enmascarada con NaN fuera del hueco).
- A3. correr_o2_modis.m / MIROVA_VIIRS750_VRP.m no corresponden a lo que se dice (otra funcion, otro metodo 'linear' vs 'natural', otro orden de argumentos, distinta tolerancia). El MATLAB que corrio no es el codigo de MIROVA para MODIS (es el de VIIRS 750 reutilizado: ¿los parametros son los mismos? ¿el relleno de fondo en MODIS usa la misma ventana?).
- A4. Las 404 escenas incluyen duplicadas; 191 distintas puede estar mal contado (hash de entrada vs hash de entrada+hueco; distintas por mascara pero iguales por valores).

## B. Comparacion mal armada
- B1. Orientacion: MATLAB es column-major, h5/scipy.io puede dar la matriz transpuesta; la regla se evalua con (fila,col) cambiados, y entonces el desempate del triangulado sale distinto o coincide por simetria.
- B2. Indices 1-based de MATLAB (si el hueco se guarda como indices) leidos como 0-based.
- B3. El hueco que usa el script no es el del .m: se reconstruye mal (p.ej. dilatacion 3x3 vs 5x5, o la mascara de nube).
- B4. La comparacion se hace en celdas que no son el hueco (toda la matriz, incluidas celdas no tocadas que son identicas trivialmente, inflando el acuerdo), o solo en el anillo, o el estadistico es el promedio de fondo que absorbe discrepancias locales.
- B5. Tolerancia floja: allclose con atol/rtol grandes respecto a la diferencia entre triangulaciones alternativas (que puede ser pequena en radiancia). Si la diferencia entre las dos diagonales posibles es menor que la tolerancia, el criterio no distingue regla de no-regla.
- B6. El control (port de Python) no puede discrepar: p.ej. se compara contra si mismo, o el port se llama con los mismos datos redondeados, o la discrepancia se mide en un estadistico que no depende del desempate.
- B7. Escenas donde el desempate no importa (relleno de 1 pixel con vecinos simetricos, valores constantes) cuentan como confirmacion: 191/191 puede ser trivial si la mayoria no tiene empate real. Falta cuantas escenas SON sensibles al desempate (donde regla y port discrepan entre si).
- B8. La regla se ajusto (calibro) con estas mismas escenas, o con las de VIIRS y luego se retoco para MODIS (sobreajuste a MODIS): «reproduce» seria circular.

## C. Clasificacion y conteo
- C1. La clasificacion «2x2» (bloques de alerta) esta mal: p.ej. incluye bloques 2x2 conexos con otro pixel, o 2x2 diagonal, o cuenta formas 2x2 con hueco dilatado que es otra forma.
- C2. «Incluidos bloques 2x2 antes no probados»: en realidad ya estaban probados en VIIRS (verificador_vara) o no hay ninguno en las 191.
- C3. Cuantas escenas son de 1 pixel / 2x2 / otras no cuadra con la suma 191; el afirmado «el port no lo hace en 1 pixel y 2x2» se calcula sobre un subconjunto distinto.
- C4. 191 distintas pero en el mat solo hay N (p.ej. 404 filas con repeticiones, o la corrida de MATLAB fallo en algunas y quedaron NaN que cuentan como acuerdo).
- C5. NaN == NaN tratado como coincidencia, o escenas donde MATLAB devolvio NaN (no relleno) cuentan como acierto.

## D. Alcance
- D1. Aun si reproduce el fondo (campo rellenado), la afirmacion de que cambia «la vara de magnitud de un censo» exige que el VRP final (no solo el fondo) cambie; eso no esta medido por el hecho de coincidir el fondo.
- D2. Reproduce MATLAB R2026b; MIROVA de produccion pudo correr otra version (desempate de la triangulacion cambia con versiones de MATLAB/qhull). La regla es de una version.
- D3. Un solo sistema, una sola maquina; las escenas son una muestra de ciertos volcanes/fechas.
