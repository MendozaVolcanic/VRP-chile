# S163, O2 alternativa: el fondo de `fillmissing2` en alertas de un píxel, contra MATLAB y contra lo que MIROVA publicó

Carpeta: `C:\vrp-trabajo\s163-o2alt\experiments\_s163_o2alt\` (rama `s163-o2-alternativa`). Sólo lectura sobre todo
lo existente; nada en `pipeline/`, `data/` ni `frontend/`; sin Earthdata ni GitHub Actions. Todo número de este
informe sale de una salida de script en esta carpeta (se cita al lado).

Insumos ajenos, leídos por ruta y sin copiar:
- Entradas y alertas de S159: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\entradas.mat` y
  `...\o1\o2_paquete\entradas_o2.mat` (311 escenas), con sus etiquetas `.json`.
- Resultado de MATLAB R2026b sobre O2, corrido por la coordinadora el 2026-10-25:
  `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\resultado_o2.mat`, md5
  `1f7fdc4bed0f8cb6223204bbce42ba43` (cada script que lo usa comprueba el md5 antes de leerlo).
- Referencia de MIROVA: `C:\vrp-trabajo\s163-o2alt\latest_consolidado.csv` (canal tabla), `Sensor == "VIIRS"`.

## 0. La respuesta corta

**1. La regla del fondo de MATLAB quedó identificada, y ya no hace falta MATLAB para reproducirla.** Una
triangulación de Delaunay con **perturbación simbólica** (la regla de desempate de CGAL: orden lexicográfico y
orientación) en el marco **x = fila, y = columna**, y relleno lineal sobre ella, da el mismo VRP que MATLAB en
**166 de 166** escenas con alerta de O2 (73 de un píxel, 74 de 2 a 4, 19 de 5 o más), con diferencia relativa máxima
**1,55e-15**, y la misma matriz de fondo completa en **84 de 84** escenas (máximo 1,11e-16 en las celdas rellenadas)
(`pert_contra_matlab_salida.txt`). El mismo algoritmo con los ejes cambiados (x = columna) calza sólo en 42 de 166 y
en 6 de 73 de un píxel: la prueba discrimina. Ningún modelo anterior (shim de Octave, segundo port, primer port) es
MATLAB. Esto lo encontré primero contra Etna, antes de que llegara el resultado de MATLAB: la regla da
Tot_Lmir_bk **1,072886152**, el número exacto del OSF v2.5 (`etna_ancla_salida.txt`).

**2. Contra lo que MIROVA publicó, NO SEPARA.** En 6 pasadas chilenas con alerta de MIROVA y alerta de un píxel en
nuestras matrices, el VRP de MATLAB queda a una mediana de |log(VRP/MIROVA)| de **0,193** (sesgo ×1,20), contra
**0,188** del shim y del segundo port y **0,194** del primer port; por pasada, MATLAB queda más cerca que el shim en
2, más lejos en 2 y empata en 2. El bootstrap por pasada de (mejor modelo − MATLAB) va de **−0,098 a +0,060** (IC
95 %), y el margen observado entre la primera y la segunda variante es **0** (empatan), dentro de cualquier nulo
(`pareo_mirova_salida.txt`). La razón es física y medida: mover nuestra grilla 375 m o cambiar el interpolador del
regrillado mueve el VRP de MATLAB con una dispersión mediana de **0,134** en log por pasada, comparable a la diferencia
entre variantes del fondo cuando difieren (**0,182**) y las variantes sólo difieren en el **39 %** de las escenas
chilenas de un píxel. Con verdad sembrada, harían falta del orden de **50 a 100 pasadas** de un píxel pareadas para
que MATLAB gane en el 80 % de los casos; tenemos 6.

Consecuencia práctica: la pregunta «¿cuál fondo es el de MIROVA?» se cierra por la vía del código (punto 1), no por la
vía del dato (punto 2). La vía del dato no puede cerrarla con lo que hay en disco, porque el ruido de NUESTRA cadena de
regrillado (D17) domina.

## 1. Hallazgos

### H1. Delaunay con perturbación simbólica, x = fila: es `fillmissing2(...,'linear')` de MATLAB en las 166 escenas

- SCRIPT:SALIDA `pert_contra_matlab.py` → `pert_contra_matlab_salida.txt` y `pert_contra_matlab.json`; módulo
  `delaunay_perturbado.py`.
- QUÉ PASA. Físicamente, cuando el `.m` quita el píxel caliente y ensancha el hueco, el fondo se estima interpolando
  desde los píxeles del borde. Sobre una grilla regular cuatro centros vecinos están en un mismo círculo y la
  triangulación no es única: cada programa rompe el empate a su manera, y en un hueco simétrico de 3 × 3 el centro cae
  justo sobre esas aristas ambiguas. La regla que usa MATLAB resultó ser una regla determinista conocida: se triangula
  y, en cada empate, se decide como si los puntos estuvieran perturbados de forma infinitesimal según su orden
  lexicográfico, con la fila como primera coordenada. Implementada en aritmética entera exacta (volteos de Lawson
  sobre una triangulación inicial de Qhull hasta que ninguna arista viole el predicado perturbado; 0 aristas ilegales
  en todas las escenas), reproduce a MATLAB al último bit.
- Tabla (de `pert_contra_matlab_salida.txt`, mismas alertas que MATLAB, L_hot idéntico en las 166):

  | variante | iguales a MATLAB (1e-9) | 1 px | 2 a 4 px | 5+ px | fondo completo igual | máx. VRP/MATLAB − 1 |
  |---|---|---|---|---|---|---|
  | perturbada, x = fila | 166 de 166 | 73 de 73 | 74 de 74 | 19 de 19 | 84 de 84 | 1,55e-15 |
  | perturbada, x = columna | 42 de 166 | 6 de 73 | 32 de 74 | 4 de 19 | 17 de 84 | 8,18e-01 |

  Según la lectura de S159 (`leer_o2_salida.txt` de la coordinadora), los tres modelos previos difieren de MATLAB en
  más de 1 % en 32 (shim), 26 (segundo port) y 45 (primer port) de 166 escenas.
- NULO MEDIDO. `nulo_166.py` → `nulo_166_salida.txt`: 20 triangulaciones al azar (rotura de empates aleatoria,
  interpolación exacta) calzan con MATLAB en una mediana de **93** y un máximo de **110** de 166 escenas, y en una mediana de **41** y un máximo de **57** de las 73 de un píxel. Ninguna se acerca a 166. En Etna sola, la probabilidad de que una regla al azar caiga
  en el valor del OSF es **0,0175** por candidato (35 de 2000 triangulaciones al azar; `etna_ancla_salida.txt`), y de
  las 8 simetrías del marco de la regla perturbada sólo 1 acierta: Etna sola no habría bastado, las 166 escenas sí.
- CONFIANZA. CONFIRMADO que la regla reproduce a MATLAB en estas 166 escenas (y en Etna). SOSPECHA, no dato, el
  mecanismo: que MATLAB triangule con CGAL. No lo verifiqué en documentación; lo que está medido es la igualdad de
  resultados. Lo que esta batería no cubre: celdas fuera de la envolvente convexa en escenas que no estén en O2
  (aquí se usa vecino más cercano, como los ports; en las 84 matrices completas calza, pero no separé cuántas celdas
  extrapoladas tenía cada una) y matrices de otro tamaño o con NaN dispersos.
- GRAVEDAD 3 (positiva). Da una vara del VRP del código de MIROVA en Python, sin MATLAB. Antes de usarla en una
  evaluación hay que portarla como función con su prueba de oro contra `resultado_o2.mat` (166 escenas).

### H2. Contra el VRP publicado por MIROVA, ninguna variante del fondo se separa de las otras

- SCRIPT:SALIDA `pareo_mirova.py` → `pareo_mirova_salida.txt` y `pareo_mirova.json`.
- Referencia: 10 pasadas chilenas con matrices (las de la segunda ronda S158); 8 con una fila
  `ALERTA_TERMICA` de VIIRS 750 en la tabla, todas de la tabla (ninguna sólo OCR); Tupungatito 2026-03-01 sin fila y
  Llaima 2026-10-10 RUTINA. Ventana avisada por `calidad_referencia_mirova.avisar("2026-03-01", "2026-10-16")`: decide
  la tabla sola. Todas las alertas pareadas tienen radio propio a menos de 1,5 km del `Distancia_km` de MIROVA (cota
  escalar: descarta lo distinto, no prueba que sea el mismo píxel; A93, A107).
- Tabla (resumen por pasada: mediana sobre las variantes de grilla de cada pasada, después mediana entre pasadas):

  | estrato | pasadas | escenas | MATLAB | shim | 2.º port | 1.er port |
  |---|---|---|---|---|---|---|
  | 1 px: mediana |log(VRP/MIROVA)| | 6 | 50 | 0,1928 | 0,1884 | 0,1884 | 0,1936 |
  | 1 px: sesgo mediano (factor) | 6 | 50 | +0,183 (×1,200) | +0,134 (×1,143) | +0,134 (×1,143) | +0,051 (×1,052) |
  | 2 a 4 px (control): mediana |log| | 4 | 22 | 0,0893 | 0,0893 | 0,0893 | 0,0893 |
  | 2 a 4 px: sesgo mediano | 4 | 22 | +0,056 | +0,056 | +0,056 | +0,037 |
  | escena por defecto (lineal, caja por defecto) | 3 | 3 | 0,0600 | 0,0599 | 0,0599 | 0,0585 |

  En las 50 escenas pareadas de un píxel, la variante difiere de MATLAB en 15 (shim), 13 (segundo port) y 29 (primer
  port). Prueba de signos por pasada (1 px): MATLAB más cerca que el shim en 2, más lejos en 2, empate en 2; contra el
  segundo port 2, 1 y 3; contra el primero 2, 1 y 3. En el control de 2 a 4 px las cuatro variantes empatan en todas
  las pasadas salvo una del primer port: ahí la discrepancia con MIROVA (mediana 0,089, con un extremo de +0,93 en
  Cordón Caulle 2026-10-16) es puro ruido de pareo y de regrillado, no de fondo.
- NULOS MEDIDOS (1 px, 6 pasadas): el margen observado entre la primera (segundo port) y la segunda (shim) es 0,0000;
  con el VRP de MIROVA barajado entre pasadas, el margen nulo tiene mediana 0,0202 y p(margen ≥ observado) = 1,000.
  El barajado dentro de cada volcán sólo admite 4 permutaciones distintas (Láscar y Cordón Caulle tienen 2 pasadas;
  los demás, 1): es degenerado y lo informo sólo para que conste. Bootstrap por pasada de (mejor modelo − MATLAB):
  observado −0,0044, IC 95 % [−0,0977, +0,0596], MATLAB mejor en el 19,7 % de las réplicas.
- PISO DEL PAREO. Para una misma variante (MATLAB), mover la grilla 375 m o cambiar el interpolador del regrillado da
  una dispersión (MAD de log VRP) de 0,000 (Chaitén) a 0,172 (Villarrica), mediana **0,134** sobre 5 pasadas. La
  diferencia entre variantes del fondo, en las escenas chilenas de un píxel donde existe, tiene mediana **0,182**, y
  existe sólo en el 38,6 % de ellas.
- POTENCIA (pregunta 2 del instrumento, con verdad sembrada: MIROVA simulada = MATLAB × ruido lognormal, sobre las 73
  escenas de un píxel de O2). Probabilidad de que MATLAB gane estricto:

  | σ del ruido de pareo (log) | n = 6 | n = 20 | n = 50 | n = 100 | n = 300 |
  |---|---|---|---|---|---|
  | 0,132 (control de 2 a 4 px) | 0,38 | 0,64 | 0,81 | 0,93 | 1,00 |
  | 0,198 (piso de la grilla) | 0,37 | 0,60 | 0,78 | 0,88 | 0,99 |
  | 0,286 (lo observado en 1 px) | 0,33 | 0,48 | 0,71 | 0,80 | 0,96 |
  | 0,050 (ruido chico, control) | 0,52 | 0,78 | 0,94 | 1,00 | 1,00 |

  Con 6 pasadas el método no supera mucho el azar (0,25 entre cuatro); con el ruido medido harían falta del orden de
  50 a 100 pasadas de un píxel pareadas para ganar en el 80 % de las veces. El instrumento sí puede dar distinto
  de cero; lo que falta es n.
- CONFIANZA. CONFIRMADO que con estos datos no separa. GRAVEDAD 2: no cambia nada publicado, pero impide usar la
  comparación contra MIROVA como árbitro del fondo; para eso queda H1.

### H3. El extremo de 1,82 que preocupaba en S159 no es ruido de MATLAB: MATLAB elige una de las ramas

- De la tabla de H1 y de `leer_o2_salida.txt`: en Villarrica 2026-09-19 05:48 (vecino más cercano, 1 px) MATLAB da
  0,4212 y los tres modelos 0,7438; la regla perturbada da 0,4212 (`pert_contra_matlab.json`, escena de O2). MIROVA
  publicó 0,45 para esa pasada. En Láscar 2026-10-08 (lineal, 1 px) MATLAB da 0,3284 (como shim y segundo port) y el
  primer port 0,1928; MIROVA publicó 0,36. Son dos casos, no una tendencia: no los uso para decidir nada (H2).

## 2. Las dos preguntas del instrumento, por script

| script | ¿mide lo que dice medir? | ¿puede dar distinto de cero? |
|---|---|---|
| `correr_octave_s163.m` | re-corre la detección y el shim de S159 sobre las mismas entradas; Etna da 5 px, L_hot 1,965342180 y L_bk 1,062919411, lo mismo que S159 H2 (`correr_octave_s163_salida.txt`) | sí: 462 de 791 escenas con alerta |
| `etna_ancla.py` | L_hot de Etna igual al OSF; 0 aristas ilegales en los 8 candidatos | sí: las 8 simetrías dan 5 valores distintos; nulo de 2000 triangulaciones con 70 valores distintos |
| `pert_contra_matlab.py` | mismas alertas que MATLAB y L_hot idéntico en las 166; sólo cambia el fondo | sí: el marco cambiado falla en 124 de 166 |
| `nulo_166.py` | mismo VRP del `.m`, con roturas de empate al azar | sí: 20 roturas al azar dan entre 78 y 110 calces, nunca 166 |
| `pareo_mirova.py` | L_hot de MATLAB en todas las variantes; pareo por volcán, sensor y minuto; radio comprobado | sí: verdad sembrada (potencia); con σ chico 0,05 y n = 100 gana en ≈ 0,99 |

## 3. Qué NO miré y qué queda SIN DATO

- **Más pasadas de un píxel pareadas.** Sólo hay matrices de las 10 pasadas de la segunda ronda S158; las 4 sin dato
  de esa ronda y cualquier otra piden red y Earthdata (fuera de esta tarea). Es lo único que podría convertir H2 en un
  veredicto, y por la potencia medida haría falta un orden de magnitud más.
- **La grilla de MIROVA.** Nuestras matrices son un regrillado propio (D17); la alerta de un píxel del `.m` sobre ellas
  no tiene por qué ser el píxel de MIROVA. El piso de 0,134 es exactamente eso. SIN DATO sobre cuánto se reduciría
  con la grilla verdadera.
- **El OCR.** Las 8 alertas están en la tabla; no consulté el OCR. SIN DATO.
- **La regla perturbada fuera de O2**: celdas extrapoladas fuera de la envolvente convexa, matrices con NaN dispersos
  (M15 inválido no entra al fondo, pero M13 inválido sí), otros tamaños. Calza en las 166, pero la batería de O2 no
  ejerce esos casos de forma deliberada.
- **El mecanismo dentro de MATLAB** (si `fillmissing2` usa `scatteredInterpolant` y CGAL): SOSPECHA, no verificada.
- **La familia de 67 triangulaciones de S158 para Chile**: no la recorrí en las escenas chilenas; ya no hace falta,
  porque la regla de MATLAB está identificada.

## 4. Qué debería mirar un verificador con contexto limpio

1. Correr `PYTHONIOENCODING=utf-8 python pert_contra_matlab.py` y confirmar 166 de 166; leer `delaunay_perturbado.py`
   contra la regla de CGAL (`side_of_oriented_circle` con `perturb=true`) y buscar un caso donde los volteos de Lawson
   no terminen en la triangulación única (por ejemplo, cuatro puntos cocirculares y colineales a la vez).
2. Que el calce no sea por construcción: el script usa las alertas y L_hot de MATLAB, pero el fondo lo calcula de
   cero desde `entradas_o2.mat`; comprobar que no lee `BK` ni `LBK` de MATLAB salvo para comparar.
3. En `pareo_mirova.py`, la elección de la mediana por pasada antes de la mediana entre pasadas, y si otra agregación
   (todas las escenas iguales, o sólo la escena por defecto) cambia el veredicto.
4. La potencia: el modelo de ruido lognormal independiente de la variante es un supuesto; el sesgo ×1,20 de un píxel
   contra MIROVA es común a las variantes y no entra en la simulación.

## 5. Cómo reproducir

Desde Git Bash, en `C:\vrp-trabajo\s163-o2alt\experiments\_s163_o2alt\`, con
`OCT="/c/Users/nmend/AppData/Local/Programs/GNU Octave/Octave-11.3.0/mingw64/bin/octave-cli.exe"`:

```
"$OCT" --no-gui --eval "cd('C:/vrp-trabajo/s163-o2alt/experiments/_s163_o2alt'); correr_octave_s163"   # salida_octave_s163.mat
PYTHONIOENCODING=utf-8 python etna_ancla.py         > etna_ancla_salida.txt          # ~15 min (nulo de 2000)
PYTHONIOENCODING=utf-8 python pert_contra_matlab.py > pert_contra_matlab_salida.txt  # ~3 min
PYTHONIOENCODING=utf-8 python nulo_166.py           > nulo_166_salida.txt
PYTHONIOENCODING=utf-8 python pareo_mirova.py       > pareo_mirova_salida.txt 2>&1
```
