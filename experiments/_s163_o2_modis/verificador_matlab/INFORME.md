# Verificación independiente: la regla de `fillmissing2` contra la corrida de MATLAB sobre MODIS (S163 O2)

Verificador con contexto limpio. Todo lo de abajo sale de scripts propios de esta carpeta (m01 a m10, cada uno con su
`_salida.txt`), que leen `resultado_o2_modis.mat` y `entradas_o2_modis.mat` directamente y llaman a `delaunay_perturbado.py`
y al relleno del port sin pasar por `regla_contra_matlab_modis.py`. Los caminos de error, escritos antes de leer el script,
están en `CAMINOS.md`. Sin commit, push ni stash. Lo no medido va como SOSPECHA o SIN DATO.

## En una pantalla

1. La afirmación central se sostiene: la regla coincide con el fondo de MATLAB en las 404 filas y en las 191 escenas distintas, con diferencia máxima de 5,6e-17 en todas las celdas finitas del hueco (no sólo en las alertas); la alternativa más cercana está a 1,1e-4, así que la tolerancia separa por doce órdenes de magnitud (m03, m10).
2. El resultado es de este paquete (md5 de los dos .mat; LHOT y DL de MATLAB recomputados desde mis entradas en 404 de 404; orientación columna primero) y tiene cabecera de MATLAB en Linux, no de Python en esta máquina (m01, m02).
3. El port de Python no es MATLAB en 1 píxel (coincide en 24 de 87 distintas) ni en el bloque 2 x 2 (0 de 6); mis conteos por forma son los mismos que los del script (m06).
4. Lo que la frase empuja más allá de lo medido: los 2 x 2 son sólo 6 escenas distintas, todas de Láscar y centradas, y el 84 % de las 191 distintas es Láscar; la regla es equivalencia empírica en R2026b con huecos de 3 x 3, no un mecanismo probado; que MIROVA use este `.m` en MODIS y que el censo cambie de vara son SIN DATO (VM-01, VM-05).
5. Detalles menores: MATLAB deja NaN en 159 celdas del hueco de 10 escenas (la regla y el port rellenan) sin efecto sobre alertas; el port falla también en pares diagonales y otras formas raras (VM-02, VM-04).

## Veredicto por afirmación

| # | Afirmación | Veredicto | Ancla |
|---|---|---|---|
| 1 | `resultado_o2_modis.mat` es el de este paquete | CONFIRMADO | md5 d20cf7dd... y fbe988bf... coinciden (m01); `LHOT` de MATLAB = suma de `M13(alertas)` con índices columna primero en las 4 escenas que muestreé (m01) y `DL = LHOT - LBK` con mi `LHOT` recomputado en 404 de 404 (m02); cabecera `Platform: GLNXA64` y versión `R2026b` dentro del .mat, mientras `entradas` tiene cabecera `nt` (bytes iniciales de ambos) |
| 2 | Son 404 escenas, 191 distintas | CONFIRMADO | 191 por (grilla + alertas), 191 por grilla sola y 191 matrices `BK` distintas de MATLAB; 116 pasadas; 0 grillas repetidas con alertas distintas (m04) |
| 3 | La regla reproduce el fondo de MATLAB en el hueco | CONFIRMADO en las celdas que MATLAB rellena | diferencia absoluta máxima 5,55e-17 en celdas de alerta y en todas las celdas finitas del hueco, 404 de 404 filas y 191 de 191 distintas (m03); en 5 escenas muestreadas 50 de 68 celdas son idénticas bit a bit y el resto difiere en 1 ulp, lo que descarta que el .mat sea salida de Python (m09) |
| 4 | Incluye bloques 2 x 2 | CONFIRMADO con n pequeño | 19 filas, 6 distintas, regla = MATLAB en las 19 (m06); ver VM-01 |
| 5 | El port no es MATLAB en 1 píxel ni en 2 x 2 | CONFIRMADO | 1 píxel: coincide en 29 de 168 filas, 24 de 87 distintas; 2 x 2: 0 de 19 filas, 0 de 6 distintas (m06). Vale también en otras formas (VM-04) |
| 6 | Con 2 y 3 píxeles casi siempre da lo mismo | EN PARTE | 129 de 132 y 76 de 77 filas; las que fallan son de forma no compacta (pares diagonales 0 de 3, trío 8-conexo 1 de 2) |
| 7 | La clasificación «2 x 2» es correcta | CONFIRMADO | mi clasificador propio (4 píxeles con extensión 1 en fila y columna) da las mismas 19 filas y 6 distintas (m04) |
| 8 | El control del port puede discrepar | CONFIRMADO | el port discrepa de MATLAB en 163 escenas (mínimo no nulo 1,06e-4, mediana 3,4e-3, máximo 3,1e-2) y el marco cambiado (x = columna) en 196 (m03, m10) |
| 9 | La tolerancia distingue | CONFIRMADO | brecha entre 5,6e-17 (regla) y 1,06e-4 (alternativa más cercana): ninguna diferencia entre 1e-12 y 1e-6 (m10) |
| 10 | La matriz de fondo completa dentro del hueco coincide | EN PARTE | vale en las celdas finitas; en 10 escenas MATLAB deja 159 celdas del hueco en NaN y la regla las rellena (VM-02) |
| 11 | Cifras previas «9 % típico, sin sesgo», Llaima 0,43 contra 0,11 MW | EN PARTE | mediana de la diferencia relativa en 1 píxel 9,1 % (8,5 % en distintas), Llaima 0,4304 contra 0,1140: ok; «sin sesgo»: mediana 1,000 y 67 filas sobre 1 contra 72 bajo 1, pero media 1,072 (m09, VM-07) |
| 12 | La regla no se ajustó a estas escenas | CONFIRMADO en lo visible | el blob de `delaunay_perturbado.py` es f273a47a... (el declarado) y su único commit en esta rama es del 2026-10-26 01:39 -0300, seis horas antes del resultado de MATLAB (07:52); la historia previa en `s163-o2-alternativa` no la verifiqué |
| 13 | Es lo que hace MIROVA en MODIS | SIN DATO | el `.m` es el de VIIRS 750 aplicado a rejillas MODIS de 51 x 51; el propio resultado lo reconoce (VM-05) |
| 14 | Esto cambia la vara de magnitud de un censo | SIN DATO | sólo medí el fondo; el efecto en un censo depende de cuántas alertas de 1 píxel y de 2 x 2 contiene, y eso no lo medí |

## Hallazgos

**VM-01. Los 2 x 2 y la composición de las 191 escenas (gravedad 2, confianza alta).** Los bloques 2 x 2 son 6 escenas
distintas (19 filas por repetición entre variantes), todas de Láscar, con filas 23 a 26 y columnas 23 a 26, o sea en el centro
de la grilla (m08). De las 191 distintas, 161 son de Láscar, 18 de Nevados de Chillán y 12 de otros siete volcanes; los centros
de alerta caen en filas 18 a 31 y columnas 22 a 32 (69 posiciones). Todas usan hueco de 3 x 3 (npix de 4 o menos). Dentro de ese
dominio la coincidencia es total; fuera (huecos de 5 x 5 o 7 x 7 en MODIS, alertas cerca del borde, volcanes con fondo muy
distinto) este paquete no dice nada. Alertas a 2 celdas o menos del borde: 0 de 404 (m07).

**VM-02. MATLAB no extrapola; la regla y el port sí (gravedad 2, confianza alta en el hecho, media en la consecuencia).** En 10
escenas `BK` de MATLAB trae 2356 NaN dentro del hueco, de los cuales 159 eran celdas finitas de `M13` (halo dilatado junto a NaN
originales); `fillmissing2(...,'linear')` no las rellenó (fuera de la envolvente convexa), mientras la regla cae al vecino más
cercano y el port también (m02, m09). `regla_contra_matlab_modis.py` calcula la diferencia con `np.nanmax`, que ignora en silencio
esas celdas, así que «fondo completo dentro del hueco» está medido sólo donde MATLAB rellenó. En estas 404 escenas ninguna celda de
alerta quedó en NaN, así que el VRP no se ve afectado. SOSPECHA (no ocurrió acá): una alerta fuera de la envolvente de celdas con
valor daría NaN en `BK`, y `sum(bk(a),'omitnan')` la sacaría de LBK, con lo que MATLAB y la regla discreparían justo ahí.

**VM-03. El control NPIX es débil; el que vale es otro (gravedad 1, confianza alta).** `NPIX` en el `.m` es `numel(alert)`, así
que «NPIX de MATLAB = máscara en 404 de 404» sólo prueba que se pasó un vector del largo correcto, no los índices ni la
orientación. Lo que sí cubre eso es `LHOT` (suma de `M13(alertas)` en orden columna primero, que en las escenas que muestreé da
distinto con fila primero, 0,3811 contra 0,3043 en la escena 0) y la igualdad `DL = LHOT - LBK` con mi propia suma, 404 de 404 (m01, m02).

**VM-04. El port falla también fuera de lo que la frase nombra (gravedad 1, confianza alta).** Escenas distintas donde el port
difiere de MATLAB: 1 píxel 63 de 87; 2 x 2 6 de 6; pares diagonales 3 de 3; trío 8-conexo 1 de 2; cuatro píxeles dispersos 1 de 1
(n pequeños) (m06). «1 píxel y 2 x 2» es correcto pero incompleto; la regla coincide con MATLAB en todos esos casos.

**VM-05. Alcance de «es la regla de MATLAB» (gravedad 3, confianza alta).** (a) Es equivalencia empírica bajo R2026b
(`26.2.0.3386108`) en un solo sistema; el docstring de `delaunay_perturbado.py` dice que el mecanismo (perturbación simbólica tipo
CGAL) es SOSPECHA, y esta comparación no lo prueba. Si el desempate cambia entre versiones de MATLAB, la regla puede no valer para
la versión con que MIROVA calculó su archivo: SIN DATO. (b) La corrida usa el `.m` de VIIRS 750 sobre rejillas MODIS de 51 x 51 ya
remuestreadas por nuestro port y con alertas decididas por nuestro port (MATLAB no detectó nada); el `.m` de MODIS de MIROVA no es
público, como admite el propio resultado. (c) Las frases «cualquier vía código MIROVA en `pipeline/` tendría que rellenar con esta
regla» y «esa columna deja de ser preliminar» pasan de lo medido a una decisión, y dependen de (a) y (b).

**VM-06. Cosas que el resultado afirma y yo no puedo ver (gravedad 1, confianza alta).** «Entradas comprobadas por md5 dentro de
MATLAB», «la coordinadora lo corrió en MATLAB Online» y «la adenda 4 de MOD-D ya informa M con la regla» no tienen evidencia en el
material entregado. Lo que sí veo apoya autenticidad: la ruta `/MATLAB/toolbox/matlab/datafun/fillmissing2.m` en
`salida_matlab_modis.txt`, la cabecera `GLNXA64` con fecha 2026-10-26 10:43:19 (la de `entradas` es `nt`, escrita por scipy en
Windows) y diferencias de 1 ulp entre regla y `BK` que una copia de Python no tendría (m09). El md5 de `salida_matlab_modis.txt`
(da9e409f...) coincide con el citado.

**VM-07. «Sin sesgo» (gravedad 1, confianza media).** En 1 píxel la razón port/MATLAB tiene mediana 1,0000, 67 filas sobre 1 y 72
bajo 1, pero media 1,072 por una cola alta (Llaima x3,78). Es ruido simétrico en conteo y asimétrico en promedio; un censo que
sume VRP vería la cola.

## VERIFICADO LIMPIO

- Procedencia: md5 de resultado, entradas, `.m` y salida de MATLAB coinciden con lo declarado; LHOT, LBK y DL de MATLAB cuadran con mis entradas (no hay mezcla de paquetes ni de orientación).
- Reconstrucción propia del hueco desde el `.m` (alerta a NaN, dilatación cuadrada de 3 con `strel`): fuera del hueco `BK` es exactamente `M13` en 404 de 404 y las celdas modificadas están todas dentro del hueco (m02).
- Comparación hecha en las celdas correctas (alertas y todo el hueco finito), no sobre la matriz entera; diferencia máxima regla contra MATLAB 5,6e-17 con brecha de 12 órdenes a la alternativa más cercana.
- Conteo de escenas distintas y clasificación de formas: confirmados con definiciones propias; mis conteos por forma coinciden con los del script (1 píxel 24 de 87, 2 píxeles 54 de 57, 3 píxeles 36 de 37, 4 píxeles en otra forma 3 de 4, 2 x 2 0 de 6 en port = MATLAB; regla = MATLAB en todas).
- Forma cerrada independiente para 1 píxel: en las 167 escenas donde las dos parejas dan distinto, el centro de `BK` de MATLAB es la media de la pareja de columna (c-2, c+2), sin usar la regla (m05). En la escena restante (386) la pareja de columna tiene un NaN original y la forma cerrada no aplica; la regla coincide igual con MATLAB.
- El nulo de la regla (marco cambiado) discrepa de MATLAB en 196 escenas, así que la coincidencia no es de simetría.
- Sin circularidad visible: la regla se commiteó antes del resultado y no cambió.

## Archivos

Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-2-0dd578\experiments\_s163_o2_modis\verificador_matlab\`
con `CAMINOS.md`, `m01_integridad.py`, `m02_hueco_y_bk.py`, `m03_regla_vs_bk.py` (y `.json`), `m04_distintas_y_formas.py`,
`m05_un_pixel_directo.py`, `m06_por_forma.py`, `m07_vrp_y_bordes.py`, `m08_posiciones.py`, `m09_resto.py` y `m10_tolerancia_salida.txt`,
cada uno con su `_salida.txt`.
