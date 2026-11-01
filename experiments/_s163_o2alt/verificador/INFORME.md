# Verificación S163 de la regla de fondo de fillmissing2 (rama s163-o2-alternativa, commit cd812c746)

Carpeta: `C:\vrp-trabajo\s163-verif-regla\`. Hora del servidor al inicio: Mon, 26 Oct 2026 03:18:36 GMT. Lista de caminos de falla,
escrita antes de leer el informe: `C:\vrp-trabajo\s163-verif-regla\CAMINOS_DE_FALLA.md`. Todo número sale de una salida guardada acá.
No hubo commits, ni push, ni cambios en pipeline, data o frontend. El worktree `C:\vrp-trabajo\s163-o2alt` quedó limpio
(`git status` vacío): los scripts del subagente escriben su `.json` dentro de su propia carpeta, lo copié a la mía y restauré el original con `git checkout`.

## Veredictos

| Afirmación | Veredicto |
|---|---|
| 1. La regla (Delaunay con perturbación simbólica estilo CGAL, x = fila, y = columna, relleno lineal) reproduce a MATLAB: 166 de 166 en VRP, 84 de 84 en matriz de fondo | **CONFIRMADO**, por dos caminos independientes |
| 1b. Control de ejes cambiados (42 de 166) y nulo de 20 desempates al azar (máx. 110) muestran que la prueba discrimina | **CONFIRMADO EN PARTE**: discrimina, pero el nulo es débil y subestima lo parecido que puede ser un rival serio (ver H1) |
| 2. Contra el VRP publicado por MIROVA en 6 pasadas de un píxel ninguna variante se separa | **CONFIRMADO** (con alternativas de agregación el veredicto de no-separación se mantiene) |
| 2b. «Harían falta 50 a 100 pasadas» | **CONFIRMADO EN PARTE**: sale de una simulación con supuestos propios (lognormal independiente, escenas tratadas como independientes); el orden de magnitud es plausible, no es una cota |

## Parte 1

### Mi implementación (independiente de `delaunay_perturbado.py`)
- `C:\vrp-trabajo\s163-verif-regla\mi_cgal.py` (salida `mi_cgal_salida.txt`): triangulación inicial de Qhull, volteos de Lawson con mi propio
  predicado en enteros de Python, interpolación baricéntrica mía, dilatación de la máscara mía (desplazamientos de arreglo, sin `scipy.ndimage`),
  vecino más cercano con `cKDTree` fuera de la envolvente. El desempate lo escribí desde mi recuerdo de `Delaunay_triangulation_2::side_of_oriented_circle`
  de CGAL (bucle completo i = 3..1), no desde el código del subagente. Alertas y L_hot de MATLAB se toman como entrada (aísla el fondo, igual que el subagente).
- Resultado en el marco (x = fila, y = columna): **166 de 166** a 1e-9 relativo, máximo 1,55e-15; matriz de fondo en celdas rellenadas **84 de 84**, máximo 1,11e-16.
  Es la misma cifra que da el subagente, por otra vía de código. Re-corrí también su `pert_contra_matlab.py` y su salida es idéntica byte a byte
  (`rerun_pert_salida.txt`).
- Fuga de datos: `grep_fuga.txt` muestra que sus scripts leen `BK` sólo para comparar (`pert_contra_matlab.py` l. 55 en adelante), `LHOT` sólo para chequear L_hot, y
  `VRP` sólo como denominador. El fondo se calcula de cero desde `entradas_o2.mat`. Los míos igual.

### Hallazgo H1 (gravedad 2): el control de ejes y el nulo subestiman a los rivales serios
Corrí las 8 simetrías del marco con mi implementación (`mi_cgal_salida.txt`):

| marco | calzan de 166 | máx. rel. VRP |
|---|---|---|
| fila, columna (el correcto) | 166 | 1,55e-15 |
| reflejar columna | 160 | 5,7e-2 |
| reflejar fila | 160 | 4,4e-2 |
| reflejar ambas | 159 | 1,1e-2 |
| intercambiar ejes (el «control» del subagente) y sus reflexiones | 42, 42, 43, 43 | 8,2e-1 |

Además, un desempate distinto y sin relación con CGAL (levantar la parábola con ±eps·x·y y desempatar el resto con monomios de orden mayor,
`mi_regla.py`, `mi_regla_salida.txt`) da **153 de 166** con signo +, y 43 con signo −. O sea: el grueso del calce lo da una sola decisión, que en las
celdas cuadradas la diagonal sea la misma en toda la grilla y con cierta orientación; los 13 casos restantes los resuelve el orden lexicográfico de CGAL
en conjuntos cocirculares no cuadrados. El informe presenta 166 contra 42 y contra un nulo de 110; el rival real más cercano queda en 159 a 160 y 153.
Sigue siendo una separación nítida (errores relativos de 1 a 6 %, sin fallar por redondeo), pero «el marco cambiado calza 42» no es la medida del margen.
El nulo de 20 triangulaciones al azar se reproduce exactamente (`rerun_nulo_salida.txt`: mediana 93, máximo 110). Puede dar distinto de cero y el
resultado no es suerte, pero ese nulo no se parece a las alternativas estructuradas que un lector se preguntaría.

### Otros puntos (gravedad 1)
- Las 166 escenas no son 166 casos independientes: 83 son variantes (grilla, interpolador, caja) de 10 pasadas chilenas, 1 es Etna y 82 son sintéticas.
- Celdas fuera de la envolvente convexa (relleno por vecino más cercano): ocurren en 83 de las 166 escenas, pero sólo 1 de ellas tiene matriz `BK` de MATLAB
  con la que comparar (`fuera_salida.txt`). Que el VRP calce 166 de 166 incluye alertas a 2 px del borde (5 escenas), pero la extrapolación está casi sin probar contra la matriz de fondo. El informe lo reconoce a medias.
- Mi primera versión (sólo ±eps·x·y, sin monomios de respaldo) dejaba 3.797 empates sin resolver y daba 100 de 166, con ±1 idénticos; no guardé esa salida.
  Lo cito porque muestra que el resultado depende de resolver los empates no cuadrados.
- El mecanismo (si MATLAB usa CGAL) sigue siendo una sospecha, como el informe dice. Lo que está medido es la igualdad de resultados.

## Parte 2

Re-corrí `pareo_mirova.py` (`rerun_pareo_salida.txt`): mismos números, salvo caracteres acentuados mal decodificados por mi consola. `agrega_alt.py` (`agrega_alt_salida.txt`) prueba otras agregaciones sobre su `pareo_mirova.json`:

| agregación, 1 px, 6 pasadas | MATLAB | shim | 2.º port | 1.er port |
|---|---|---|---|---|
| mediana de \|log\| (la del informe) | 0,1928 | 0,1884 | 0,1884 | 0,1936 |
| media de \|log\| entre variantes | 0,2097 | 0,2256 | 0,2341 | 0,2292 |
| razón sin log, mediana | 0,2002 | 0,2074 | 0,2074 | 0,2002 |
| razón sin log, media | 0,1971 | 0,2316 | 0,2316 | 0,2399 |
| por volcán (4), \|log\| | 0,1825 | 0,2829 | 0,2761 | 0,2197 |
| por escena (50, no independientes), mediana | 0,1782 | 0,1987 | 0,1987 | 0,2558 |

Con agregaciones que usan la media, por volcán o por escena, MATLAB queda algo más cerca de MIROVA que los otros, que es el sentido esperable si MATLAB es la
vara; con la mediana de las pasadas el orden se invierte por centésimas. Prueba de signos exacta sobre pasadas con variantes distintas: MATLAB mejor 2, peor 2
contra el shim (p = 1,00), 2 y 1 contra los otros dos. Con todas las pasadas a favor haría falta n ≥ 6 informativas para p < 0,05 bilateral. No hay
separación significativa con ninguna agregación probada: **la conclusión se mantiene**. El informe no oculta nada; sólo conviene no leer «MATLAB 0,1928 contra shim 0,1884» como que el shim gana (hay un empate de hecho).

Hallazgo H2 (gravedad 1): la potencia (50 a 100 pasadas) viene de una simulación que muestrea escenas como si fueran independientes y supone ruido lognormal
sin sesgo; el sesgo común ×1,20 y el hecho de que sólo 6 pasadas existan hacen del número una orden de magnitud, no una cota.

## Qué no miré
- La detección (alertas): se toma de MATLAB igual que el subagente; que Octave y MATLAB detecten lo mismo es de S159 y no lo re-verifiqué.
- Las cifras de S159 de «32, 26 y 45 de 166» para los modelos previos: no tengo sus salidas, SIN DATO.
- La cronología «lo encontré primero con Etna, antes del resultado de MATLAB»: no verificable desde acá.
- Si el mecanismo es CGAL en MATLAB; la salida de Octave del subagente; el OCR; matrices de otros tamaños o con NaN dispersos; la extrapolación fuera de la envolvente contra matrices de fondo de MATLAB (sólo 1 escena).
