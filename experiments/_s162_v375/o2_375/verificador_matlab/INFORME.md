# Verificador con contexto limpio: la vara PRELIMINAR contra MATLAB (O2-375)

Fecha de la verificación: 2026-10-26. Carpeta de entradas y salidas:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375\`

Scripts propios (no reutilizan `comparar_matlab_375.py`), todos con `python -I`, numpy 2.4.4 y scipy 1.17.1, en la misma carpeta `verificador_matlab\`:
`verificar.py` (afirmaciones 1 a 6 y caminos de falla), `modulo_vs_bk.py`, `nanpat.py`, `sens_scipy.py`, `extra.py`; salidas en `salida_verificar.txt`, `salida_modulo_vs_bk.txt`, `salida_sens_scipy.txt`.

## Veredicto global: CONFIRMADO

La vara calza con MATLAB en las 422 escenas, con un margen de seis órdenes de magnitud sobre la tolerancia, y no encontré un camino por el cual el resultado de MATLAB provenga de la vara o de otras entradas. Hay reservas menores de documentación, ninguna que cambie el veredicto (ver hallazgos). La vara puede dejar de ser PRELIMINAR **para el fondo en alertas de 1 a 4 píxeles dentro de la envolvente de los datos, que es lo que se midió**; la condición de que ninguna alerta quede fuera de esa envolvente la cumplen las 422 (MATLAB no deja ningún NaN en BK sobre una alerta).

## Afirmaciones

**1. ΔL de MATLAB contra la vara: CONFIRMADA.**
Salida de `verificar.py`: `1. DL MATLAB vs vara: max rel 1.03e-15, escenas > 1e-9: 0, mediana 0.00e+00`; diferencia absoluta máxima 2.22e-16; `DL == LHOT-LBK: max abs 0.00e+00`; mínimo |DL| 3.6e-3 (sin ΔL cercano a cero que infle o esconda el relativo), 0 negativos. Además `DL != dl de la vara exactamente` en 32 de 422 y `LBK != l_bk` exacto en 37: es decir, la igualdad no es una copia bit a bit sino aritmética independiente con diferencias de 1 ulp (firma de un cálculo hecho por otro programa, no de un archivo derivado de la vara).

**2. Control positivo de Etna: CONFIRMADA.**
`.mat`: NPIX 5, LHOT 1.965342180, LBK 1.072886152, VRP 9889528.4 W. Residuo contra el valor del OSF: LBK -3.0e-10 (redondeo de 9 decimales) y VRP -0.038 W (redondeo a 0,1 W). La consola `salida_matlab_v375.txt` dice lo mismo y registra `MATLAB 26.2.0.3386108 (R2026b)`.

**3. LHOT es la radiancia de las alertas en RAD con ALE en columna mayor base 1: CONFIRMADA, con el contrario comprobado.**
Decodificando `fila = (idx-1) mod 134`, `col = (idx-1) div 134`: `LHOT vs RAD[ALE col-mayor]: max rel 0.00e+00, escenas > 1e-12: 0`; coincide con `l_hot` de la vara (0.00e+00) y con `l_hot_port` de las etiquetas (0.00e+00). Decodificando por fila mayor (con nansum): `407 de 422` no calzan, error relativo máximo 1.594 (las 15 que calzan son simetrías del patrón). Además NPIX == NAL == npix de las etiquetas en las 422, `alertas_matlab` de las etiquetas == ALE en las 422, índices dentro de 1..17956 y sin duplicados. Ninguna alerta cae sobre un NaN de RAD (`extra.py`: `NaN de RAD en alertas: 0`).

**4. El control de que la comparación puede fallar: CONFIRMADA.**
`4. MATLAB vs port: escenas > 1e-9: 137, max rel 0.830` (con el denominador del port el máximo es 4.879, el mismo número que la salida de la vara contra el port). El conjunto de escenas donde MATLAB difiere del port es idéntico al conjunto donde la vara difiere del port (`True`), y en las demás el ΔL coincide con el port a 6.3e-16. Control adicional propio (`sens_scipy.py`): un Delaunay de scipy sin perturbar contra MATLAB difiere (>1e-9) en 22 de 58 escenas muestreadas (cada 3.ª escena sin NaN en RAD, índices < 180), máximo relativo 0.207. O sea que la tolerancia de 1e-9 distingue triangulaciones, no las esconde.

**5. LBK es la suma de BK en los píxeles de alerta: CONFIRMADA dentro de la precisión de single.**
`LBK vs sum(BK single en alertas): max rel 5.85e-08, escenas > 1e-6: 0, > 1e-9: 253`. El 5.85e-8 es el redondeo de double a single (2^-24 ≈ 6e-8), como se esperaba por ser BK single. No hay NaN de BK en ninguna alerta (`extra.py`), de modo que el `'omitnan'` del `.m` y de la vara no descarta nada (si descartara píxeles, el ΔL quedaría inflado en silencio, tanto en MATLAB como en la vara).

**6. md5: CONFIRMADA.** `71d0f8218a445c337560efd73d904374 OK`.

## Caminos por los que "la vara calza con MATLAB" podría estar mal

| Camino | Qué comprobé | Resultado |
|---|---|---|
| `resultado_v375.mat` no viene de estas entradas | Fuera del hueco (dilatación 3x3 o 5x5 de alertas y de los NaN previos de RAD, como hace `imdilate(isnan(...))` del `.m`), `BK` debe ser `single(RAD)` exacto | 0 de 422 escenas con diferencia. Eso ata el resultado a `entradas_v375.mat`, escena por escena. El encabezado del `.mat` dice `Platform: GLNXA64, Created on: Mon Oct 26 10:47:41 2026`, y el de las entradas `Platform: nt`, 2026-10-25 23:37:15: otra máquina y otro sistema |
| La vara se fabricó a partir de MATLAB | `vara_preliminar_375.json` está commiteado en `04d7151d2` el 2026-10-26 00:52:34 -0300; `resultado_v375.mat` tiene fecha de modificación 2026-10-26 07:52:12 -0300 (unas 7 h después) y no está commiteado. El módulo de la regla es de `cd812c746` (00:16:09), sha256 `5e8905cd...` igual al que la vara declara. `comparar_matlab_375.py` se modificó a las 07:53 | Orden temporal correcto. Las 32/37 escenas con diferencias de 1 ulp descartan que MATLAB sea una copia de la vara |
| La vara se fabricó a partir de MATLAB O2 con las mismas escenas | Según el docstring de la vara, la regla se contrastó con las 166 escenas de O2 (VIIRS 750, 67 x 67), no contra estas 422 (134 x 134) | Fuera de muestra. Mi corrida de ese mismo módulo contra el BK completo de MATLAB (`modulo_vs_bk.py`, 53 escenas: cada 10.ª más las 12 con NaN): `max abs dif 7.45e-09` sobre los 134 x 134, igual al redondeo single |
| El orden de las escenas no coincide | `posicion` 1..422 en etiquetas y en vara, mismos `id` en el mismo orden, `posicion` igual por índice; NPIX y LHOT calzan por índice, lo que sólo ocurriría con el orden correcto | Sin problema. Nota: la `k` de las etiquetas es k+1 por la escena de Etna (el JSON lo dice); `comparar_matlab_375.py` indexa por `posicion`, correcto |
| La tolerancia esconde algo | Tolerancia 1e-9, observado 1.03e-15; denominador con piso 1e-15 en el script de la sesión, pero mínimo |DL| real 3.6e-3, así que el piso nunca actúa. Probé también con diferencia absoluta (2.2e-16) | Sin problema. La sensibilidad se muestra con scipy sin perturbar (22/58 difieren) y con el port (137/422) |
| Entradas compartidas | Vara y MATLAB usan los mismos RAD y ALE: si RAD o ALE no correspondieran a la escena real (error del armado del paquete), ambos lo heredarían | **No se comparó contra la fuente.** `grilla_sha256` es el hash de la grilla guardada original, no de `RAD`: no se reproduce con ninguna de las 4 variantes de bytes que probé, así que no pude atar RAD a su archivo de origen. SIN VERIFICAR; no afecta "vara = MATLAB", sí afecta "estas 422 escenas son las que dicen ser" |
| Que MATLAB sea de verdad R2026b | Sólo la cadena `version_matlab` y el texto de consola | SIN VERIFICAR de forma independiente; el control de Etna al noveno decimal y las diferencias de 1 ulp son consistentes con una corrida real de `fillmissing2` |
| Zona horaria de "Created on: 10:47:41" | Hora del servidor de MATLAB Online, huso desconocido | SIN VERIFICAR; sin importar el huso, es posterior al commit de la vara si es UTC (03:52 UTC) y la fecha de modificación local lo respalda |

## Hallazgos propios

1. **(gravedad 1) Comportamiento fuera de la envolvente convexa distinto.** En las 12 escenas cuya RAD trae NaN previos (23, 61, 166, 196, 228, 229, 281, 366, 368, 373, 383, 390 en `posicion`; 37 614 celdas), MATLAB deja 38 955 celdas de BK en NaN (fuera del casco convexo de los puntos válidos) y la regla Python las rellena (`modulo_vs_bk.py`: celdas con patrón NaN distinto 38955, todas "NaN sólo en MATLAB"; `nanpat.py`, mínimo 52 celdas de distancia a una alerta). Es irrelevante para las 422 porque ninguna alerta cae ahí (0 NaN de BK en alertas) y coincide con la reserva ya commiteada en `da0693783`. Pero la regla Python, usada sin esa comprobación en otra población, podría devolver un fondo extrapolado donde MATLAB daría NaN (y `omitnan` lo tiraría). Condición para dar la vara por no preliminar: mantener el chequeo "alerta dentro de la envolvente".
2. **(gravedad 1) Cinco escenas con el hueco dilatado tocando el borde de la grilla.** Calzan igual (ya están dentro de las 422 con 0 diferencias), pero el borde es el caso que el docstring de la vara declaraba no cubierto por O2; queda cubierto sólo para estas 5. SIN VERIFICAR para alertas en el borde mismo: ninguna de las 422 tiene alertas en fila o columna 0/133.
3. **(gravedad 1) `grilla_sha256` de las etiquetas no se puede usar para auditar RAD** (es hash de otro objeto). Documentarlo o guardar también el hash de RAD.
4. **(gravedad 1) El 0.83 y el 4.88 son el mismo hecho con denominadores distintos** (MATLAB frente al port); conviene citar el denominador en las notas para no parecer dos cifras.
5. **(gravedad 2) Cobertura de la afirmación.** "La vara calza con MATLAB" está probado para escenas de 1 a 4 píxeles (NAL 1: 188, 2: 105, 3: 73, 4: 56). No dice nada de 5 o más píxeles (dilatación 5x5 o 7x7); la regla Python se probó en esa rama sólo con las muestras de `modulo_vs_bk.py`, que no incluyen escenas de más de 4 píxeles porque no las hay en las 422.

Lo que no encontré: ninguna escena donde MATLAB y la vara difieran, ningún NaN sobre una alerta, ninguna inconsistencia de orden, ningún dato de MATLAB anterior a la vara.
