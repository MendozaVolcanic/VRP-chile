# Verificación con contexto limpio: O2 en MATLAB (rama s163-o2-paquete, commit 9b755f315)

Carpeta de trabajo: `C:\vrp-trabajo\s163-verif-o2\`. Lista de caminos de error escrita antes de leer el informe:
`C:\vrp-trabajo\s163-verif-o2\CAMINOS_DE_ERROR.md`. Scripts y salidas guardadas (ningún número transcrito a mano):
`verificar.py` / `verificar_salida.txt`, `diagonal.py` / `diagonal_salida.txt`, `control_mutantes_salida.txt`,
`octave\correr_octave_propio.m` / `octave\salida_octave_propio.txt`.

## Veredicto por afirmación

| # | Afirmación | Veredicto |
|---|---|---|
| 1 | Entradas byte a byte iguales a las del paquete S159 | CONFIRMADO |
| 2 | MATLAB reproduce el OSF v2.5 en Etna | CONFIRMADO (referencia OSF no reabierta por mí) |
| 3 | 0 listas de alertas distintas MATLAB vs Octave, 311 escenas, 166 con alerta | CONFIRMADO |
| 4 | Conteos de VRP por modelo; ningún modelo es el de MATLAB; caso Villarrica | CONFIRMADO (los números); la lectura "ningún modelo" CONFIRMADA EN PARTE |
| 5 | La vara de magnitud no puede ser un port | REFUTADO como está escrito (ver hallazgo H1) |

## Evidencia

**1. Entradas.** md5 calculados por mí: `entradas_o2.mat` fb849b6a..., `MIROVA_VIIRS750_VRP.m` b0ceebb2..., `MIROVA_VIIRS750_hotspot_detection.m` ddffea36... iguales entre rama, paquete S159 y lo declarado. `correr_o2.m`: el blob de la rama (`git show`) y el del paquete S159 dan e6761d86..., igual a lo declarado. Mi extracción con `git archive` dio otro md5 en `correr_o2.m` porque el tar lo dejó con CRLF (artefacto de extracción, el blob es correcto; lo comprobé con `git show` y con el commit 61267289e, desde donde MATLAB los bajó con `websave`). `resultado_o2.mat` md5 1f7fdc4b... idéntico en rama y en `o2_paquete`. Orden de escenas: `IDX_O1` del .mat es de base 1 (1..311); restando 1 es igual a `idx_o1` del JSON, y las 311 matrices (M13, M15, BOX, DAY, SG) son iguales a la escena `idx_o1` de `entradas.mat` de S159. Las etiquetas JSON de la rama y del paquete son iguales. Se deshacen así los caminos "matrices de otro orden" y "entradas regeneradas".

**2. Etna.** Del .mat: Tot_Lmir_bk menos 1,072886152 = -3,0e-10; VRP 9.889.528,3617 W contra 9.889.528,362 del CSV OSF v2.5 (cita de `_s158_audit_r2\oraculo\control_etna_salida.txt`, que lee el CSV del OSF; yo no reabrí el CSV). Control de que el resultado no es Octave: mi Octave 11.3 con el shim da Tot_Lmir_bk 1,062919411 y VRP 9.999.972 W, el segundo port 1,0804 (9,8058 MW), y MATLAB 1,072886152.

**¿Es de MATLAB?** Cabecera del .mat: "MATLAB 5.0 MAT-file, Platform: GLNXA64, Created on: Mon Oct 26 02:15:26 2026" (los de Octave dicen "written by Octave 11.3.0", como `salida_original.mat`); `version_matlab` = 26.2.0.3386108 (R2026b). El patrón no es el del shim: 65 de 166 escenas difieren del shim, y el "ensayo Octave con shim" de S159 reproduce al shim exacto (diferencia 0,0). Consistencia interna que un archivo editado a mano tendría que haber sostenido: VRP = (LHOT-LBK)*1,97e7*0,5625/1e6 con diferencia relativa 0,0 en las 166; LBK = suma de la matriz de fondo guardada bajo las alertas (84 matrices) con error 2e-16; LHOT = suma de M13 bajo las alertas con error 4e-16; NPIX = largo de la lista en las 311. El diario `salida_matlab.txt` es texto editable y no prueba nada por sí solo; lo que sostiene el origen es el .mat.

**3. Detección.** Mi comparación con la salida de Octave de S159: 0 listas distintas, también en secuencia exacta. Además corrí yo el `.m` original en Octave 11.3 sobre `entradas_o2.mat`: 0 distintas (como secuencia y como conjunto), 166 escenas con alerta, 374 píxeles alertados. Control de que el instrumento puede dar distinto de cero: contra las cuatro mutaciones de S159 (`salida_mut_*.mat`) MATLAB difiere en 24 (k1), 104 (min2), 67 (sigma) y 35 (sinp2) de 311 escenas.

**4. VRP.** Recomputado por mí, con tres modelos más mi shim (reproduce el de S159 con diferencia 0,0):

| modelo | >1 % | igual a 1e-9 | entre 1e-9 y 1 % | máximo |
|---|---|---|---|---|
| shim Octave | 32 | 101 | 33 | 0,8182 |
| segundo port (R2) | 26 | 101 | 39 | 0,7660 |
| primer port (O1) | 45 | 86 | 35 | 0,8182 |

Coincide con el informe en los tres conteos y en el máximo 0,82 (que es el de shim y O1, el de R2 es 0,77). El informe no menciona la banda intermedia (33, 39, 35 escenas), que es corta y no cambia la conclusión. Villarrica 2026-09-19 05:48, nearest: MATLAB 0,4212, shim, R2 y O1 0,7438; las alertas son idénticas (un solo píxel, índice 2178), así que la diferencia es del fondo y no de la detección. De los 73 casos de un píxel, 10 son de los que ningún modelo calza a más de 1 % (Villarrica y Chaitén entre ellos).

## Hallazgos propios

**H1 (alta, cambia la consecuencia).** La diferencia de los casos de un píxel no es aleatoria. Con un píxel alertado el hueco es de 3x3 y el centro cae en el cuadrado de cuatro puntos cocirculares a ±2 (misma fila, misma columna); el valor lineal depende de qué diagonal elija la triangulación. En las 51 escenas de un píxel con vecindad 5x5 intacta (26 pares de valores distintos), el fondo guardado de MATLAB es **siempre el promedio de los dos puntos de la misma fila (columnas ±2)**, 51 de 51, a 1e-9. El shim de Octave elige esa diagonal en 35 y la otra en 16. Villarrica: MATLAB 0,17172 = (0,1855+0,1580)/2; el shim 0,14261 = (0,1240+0,1612)/2. Por tanto "ningún modelo es el de MATLAB" es cierto de los tres modelos existentes, pero el desempate de MATLAB parece determinista y un port con esa regla reproduciría estos 51 casos. La conclusión 5 ("la vara tiene que ser la salida de MATLAB o un port nuevo validado contra ella") es correcta en su segunda mitad; la primera ("no puede ser un port") queda refutada para la geometría de un píxel. Sin evidencia todavía para 2 o más píxeles, agujeros mayores (5x5, 7x7) ni vecindades con NaN.

**H2 (media).** Con 26 pares distintos de una sola configuración, 7 de 26 con la diagonal horizontal mayor que la vertical y 19 menor: la regla horizontal no se explica por "elegir el mayor/menor" (MATLAB toma el menor 36 veces y el mayor 15). No tengo el código de MATLAB, así que la regla es empírica.

**H3 (baja).** El informe dice que la detección "de los ports queda validada contra MATLAB"; la comparación hecha es MATLAB contra Octave (el `.m` original), y la validación de los ports contra Octave es la de S159 en 791 escenas. En estas 311 escenas los ports se comparan sólo en VRP. Además la detección no usa `fillmissing2`, así que esta prueba valida `colfilt`/`imdilate` de MATLAB contra los de Octave.

**H4 (baja).** El mapeo escena a Octave usa `IDX_O1` base 1; un lector que olvide el -1 compara contra escenas equivocadas (lo cometí yo en la primera pasada: salían 195 listas distintas y 96 de 166 sobre 1 %). El `leer_o2.py` de S159 usa el JSON (base 0) y está bien.

## Qué no miré

- No abrí el CSV OSF v2.5 (el valor de Etna lo tomo de la salida guardada de S158).
- No puedo descartar que alguien haya editado `resultado_o2.mat` con coherencia interna total; sólo muestro que no es Octave y que es internamente consistente.
- No ejecuté MATLAB ni verifiqué la licencia o la cuenta; el diario de MATLAB no se contrasta con nada externo.
- No probé la regla "misma fila ±2" fuera de los hoyos de un píxel, ni en las 120 escenas sintéticas por separado, ni verifiqué el resto de las 84 matrices de fondo con ella.
- El orden y contenido de `entradas.mat` de S159 lo tomé como bueno (sólo comparé contra él).
