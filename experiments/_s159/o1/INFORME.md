# O1 (S159): los dos ports en Python contra el `.m` original de MIROVA, corrido en GNU Octave 11.3

Carpeta: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\`. Sin red, sin git, sin tocar `pipeline/`, `data/` ni
`frontend/`. Los `.m` originales no se editaron: md5 antes y después iguales (detección `ddffea3672a08e5aa17c702f72d72170`,
VRP `b0ceebb2b7864cd27c145dc8d41968cc`, ejemplo `32f28ea6259b91f03e7970ea32e2620e`).

## 0. La respuesta corta

**En la detección, los dos ports son el `.m`.** Corrí `MIROVA_VIIRS750_hotspot_detection.m` sin modificar, en Octave
11.3 con el paquete `image` de Octave Forge (que trae el instalador: `colfilt`, `imdilate`, `strel`), sobre 791
escenas: Etna, las 10 pasadas chilenas de la segunda ronda (40 matrices tal como las guardó el run y 150 variantes de
interpolador y grilla recalculadas sin red) y las 600 escenas sintéticas de la comparación de oráculos. La lista de
alertas de cada port coincide con la de Octave en **791 de 791 escenas**, no sólo como conjunto sino en la **secuencia
exacta** (el orden de concatenación del `.m`, sin `unique`). Cuatro mutaciones del `.m` se ven en Octave y producen
exactamente lo mismo que la misma mutación en el segundo port. Para la detección no hubo que escribir ningún shim.

**En el VRP, ninguno de los tres modelos de `fillmissing2` es el de MATLAB, y en una alerta de un solo píxel la
diferencia entre ellos llega a 1,82 veces.** Eso matiza la frase de `docs/AUDIT_S158_R2.md` §2 de que un port es «vara
del VRP dentro de unos pocos por ciento»: vale con 2 o más píxeles, no con 1. Para cerrarlo dejé listo el paquete O2
para MATLAB Online.

## 1. Hallazgos, de mayor a menor gravedad

### H1. El VRP de una alerta de un píxel no lo fija ningún port: hasta 1,82 veces entre modelos del fondo

- SCRIPT:SALIDA `vrp_por_npix.py` → `vrp_por_npix_salida.txt`; detalle por escena en `comparar_vrp_salida.txt`.
- QUÉ PASA. Físicamente, cuando la alerta es un solo píxel caliente, MIROVA estima la radiancia que habría tenido ese
  píxel sin el foco interpolando desde el anillo de píxeles que lo rodean. El `.m` quita el píxel, ensancha el hueco a
  3 × 3 y rellena con `fillmissing2` lineal. Ese hueco es simétrico respecto del píxel alertado, así que el centro cae
  justo sobre aristas que la triangulación puede trazar de varias maneras igual de válidas, y cada una da otro fondo.
  Como el VRP es la diferencia entre la radiancia observada y ese fondo, una diferencia chica en el fondo es grande en
  el VRP. Con las mismas máscaras (las de Octave) y el mismo L_hot (0 diferencias en 462 escenas), la razón entre el
  mayor y el menor VRP de los tres modelos (shim de Octave, segundo port, primer port) es:

  | píxeles alertados | escenas | mediana | percentil 90 | máximo | > 5 % | > 25 % |
  |---|---|---|---|---|---|---|
  | 1 | 178 | 1,0016 | 1,1946 | **1,8208** | 45 | 15 |
  | 2 a 4 | 235 | 1,0004 | 1,0196 | 1,2453 | 9 | 0 |
  | 5 a 30 | 49 | 1,0014 | 1,0198 | 1,2124 | 3 | 0 |

  Denominador: las 462 escenas con alerta de las 791. Ventana: Etna 2023-05-19; pasadas chilenas del 2026-03-01 al
  2026-10-16. En pasadas chilenas guardadas por el run: Tupungatito 2026-03-01 05:36 (vecino más cercano, anillo
  sensible, 1 px) da 0,717 MW con el shim y el primer port y 0,394 con el segundo; Láscar 2026-10-08 05:42 (lineal,
  caja por defecto, 1 px) da 0,328 con el shim y el segundo y 0,193 con el primero (la misma banda que ya anotó el
  verificador de la segunda ronda, 0,19 a 0,33).
- CÓMO SE VE EN EL DASHBOARD. Invisible: es una propiedad de la vara, no de producción. Lo que tuerce es una decisión
  de diseño: comparar el VRP de nuestro detector con «lo que el código de MIROVA da» en alertas de un píxel, que en Chile
  son la mayoría de las débiles (Láscar, Chaitén, Cordón Caulle, Tupungatito). El §2 de la segunda ronda dice que para
  decidir el fondo «basta, porque la diferencia que se discute es de 2 a 4 veces»; con un píxel la banda de la vara ya
  llega a 1,8, así que una diferencia de 2 veces queda casi dentro del ruido del instrumento.
- CÓMO REPRODUCIRLO. `PYTHONIOENCODING=utf-8 python armar_entradas.py`, luego Octave con `correr_octave` (ver §3) y
  `correr_vrp_octave`, luego `python vrp_por_npix.py`, todo desde esta carpeta.
- CONFIANZA. CONFIRMADO que los tres modelos difieren así. SOSPECHA cuál está más cerca de MATLAB: sólo O2 lo dice.
- GRAVEDAD 3. No cambia ninguna publicación de hoy, pero puede hacer pasar por resuelta (o por refutada) una
  diferencia de fondo de un factor 2 en alertas de un píxel. Marca A113 sugerida para `docs/AUDIT_S158_R2.md` §2,
  «Consecuencia práctica»: «dentro de unos pocos por ciento» vale con 2 o más píxeles; con 1 píxel, hasta 1,82 veces.

### H2. El Delaunay de Octave da un 68.º fondo para Etna, tampoco el del OSF

- SCRIPT:SALIDA `correr_vrp_octave.m` (Octave) imprime: `Etna: npix 5 L_hot 1.965342180 L_bk 1.062919411 VRP 9999972.3 W`
  contra el OSF v2.5 `L_bk 1.072886152, VRP 9889528.4 W`.
- QUÉ PASA. Con el `.m` de VRP original y un shim de `fillmissing2` (interpolación lineal sobre la triangulación de
  Octave, `shim_fillmissing2/fillmissing2.m`), el fondo de Etna queda 0,93 % bajo el del OSF y el VRP 1,1 % sobre él.
  Cae dentro de la banda de 1,060077 a 1,085909 que la segunda ronda midió con 67 triangulaciones, pero no es la del
  OSF. O sea: Octave no puede servir de vara del VRP; sólo MATLAB.
- CÓMO SE VE EN EL DASHBOARD. Invisible.
- CÓMO REPRODUCIRLO. Octave, desde esta carpeta: `correr_vrp_octave`.
- CONFIANZA. CONFIRMADO.
- GRAVEDAD 1. Informativo: confirma que la triangulación decide y que el paquete O2 es necesario.

### H3. K1 sí decide algo, en 3 de 791 escenas (la segunda ronda vio 0 de 200)

- SCRIPT:SALIDA `comparar_octave_ports.py` → `comparar_octave_ports_salida.txt`, bloque «Controles positivos», `k1`.
- QUÉ PASA. Bajar el umbral absoluto de NTI nocturno de -0,7 a -0,8 cambia la lista en 3 escenas: dos variantes
  cúbicas de Nevados de Chillán 2026-10-10 05:54 (grilla movida 375 m al este y al oeste: de 4 a 6 píxeles; agrega
  2245 y 2247 en una y 2312 y 2314 en la otra) y la sintética 576 (agrega 2377). Es un foco intenso con vecinos
  tibios; no separé si los píxeles agregados entran directo por el test absoluto (NTI entre -0,8 y -0,7) o porque su
  salida de la población de fondo cambia el contraste de otros (SOSPECHA, cualquiera de las dos). La segunda ronda corrió esta
  mutación sólo sobre 200 escenas y dijo «no cambia ninguna máscara»; sobre 791 cambia 3. Octave y el segundo port
  mutado coinciden en las 3.
- CÓMO SE VE EN EL DASHBOARD. Invisible (es la vara).
- CÓMO REPRODUCIRLO. Octave con `MDIR='.../_s159/o1/mut_k1'` y luego `python comparar_octave_ports.py`.
- CONFIANZA. CONFIRMADO.
- GRAVEDAD 1. «K1 casi no decide qué se publica» sigue en pie; «nunca» no.

No encontré ningún hallazgo de gravedad 4 o 5.

## 2. Las mediciones

### 2.1 Encabezado del instrumento (vale para las tres mediciones)

1. *Si lo que mido estuviera roto, ¿se vería?* Un port que tradujera mal un paso daría otra lista en las escenas que
   ejercen ese paso. Las 791 escenas caen a ambos lados de los umbrales (Etna, focos de 1,02 a 15 veces en las tres
   zonas, vecino débil para el segundo pase, día, sun-glint de 5 a 20°, escenas con 30 a 60 % de M15 inválido, y las
   pasadas chilenas). Se compara además la secuencia, no sólo el conjunto. Lo que esta batería **no** vería: un error
   de lectura que Octave comparta con los ports, es decir, una función de Octave que se comporte distinto de la de
   MATLAB justo donde los ports también se equivocan. Lo acoto en el §2.4.
2. *Si el instrumento estuviera muerto, ¿se vería distinto?* Sí: el comparador exige que Etna dé los 5 píxeles y el
   Tot_Lmir_hot del OSF (1,965342180) antes de seguir, e informa el conteo de escenas con alerta por familia (462 de
   791; con Octave muerto sería 0). Además corrí el `.m` directo sobre el `VIIRS750_example.mat` original, sin pasar
   por mi copia: mismas 5 alertas `[2180 2181 2247 2314 2248]`, Tot_Lmir_hot 1,965342180, sun-glint 113,1165°.
3. *Control positivo*: cuatro copias mutadas del `.m` (§2.3).

### 2.2 Detección: Octave contra los dos ports

`comparar_octave_ports.py` → `comparar_octave_ports_salida.txt`.

| familia | escenas | con alerta en Octave | conjunto distinto, 2.º port | secuencia distinta, 2.º port | conjunto distinto, 1.er port | secuencia distinta, 1.er port |
|---|---|---|---|---|---|---|
| Etna | 1 | 1 | 0 | 0 | 0 | 0 |
| chilenas guardadas por el run | 40 | 21 | 0 | 0 | 0 | 0 |
| variantes chilenas (lineal, vecino, cúbico × 5 posiciones de grilla) | 150 | 62 | 0 | 0 | 0 | 0 |
| sintéticas (semilla 7, generador copiado de `comparar_oraculos.py`) | 600 | 378 | 0 | 0 | 0 | 0 |

Las 600 sintéticas son todas, no una muestra; con alerta salen 378, igual que reporta la segunda ronda, lo que confirma
que regeneré las mismas escenas. Ninguna escena tiene índices repetidos en la salida del `.m` (`NUNICO == NALERT` en
las 791), así que el `.m` sin `unique` y un port que use máscaras dan lo mismo.

Las 10 pasadas chilenas, con la caja por defecto y la matriz lineal guardada por el run, dan en Octave lo mismo que la
tabla del §3 de la segunda ronda: Láscar 2026-10-08 1 px (2244), Chillán 2026-10-10 5 px, Villarrica 2026-09-19 2 px,
Láscar 2026-09-26 0 (1 px con vecino más cercano), Chaitén 2026-10-06 0 (1 px con vecino más cercano), Cordón Caulle
2026-10-10 y 2026-10-16 0 (1 px con anillo sensible), Tupungatito 2026-08-21 0, Tupungatito 2026-03-01 0 (1 px con
vecino más cercano y anillo sensible) y Llaima 2026-10-10 0. La tabla de la segunda ronda queda confirmada por el
código original: **ninguna de las 10 cambia**.

### 2.3 Control positivo: el `.m` mutado

`preparar_mutantes.py` escribe copias en `mut_*/` (cada reemplazo exigido único; diffs de una o dos líneas
comprobados). Denominador: 791 escenas.

| mutación del `.m` | escenas en que cambia la salida de Octave | en que cambia el 2.º port mutado | Octave mutado distinto del 2.º port mutado |
|---|---|---|---|
| mínimo NTI de ROI2 (cumbre) de noche 0,003 → 0,03 | 185 (Etna 1, chilenas 19 + 55, sintéticas 110) | 185 | 0 |
| sigma de ROI1 y ROI2 intercambiados | 114 | 114 | 0 |
| sin segundo pase | 83 (Etna pasa de 5 a 4 píxeles) | 83 | 0 |
| K1 nocturno -0,7 → -0,8 | 3 (ver H3) | 3 | 0 |

El instrumento ve, y ve lo mismo que el port, también en las matrices chilenas.

### 2.4 ¿Puede MATLAB decidir distinto que Octave?

`margenes.py` → `margenes_salida.txt`. Que Octave y los ports coincidan prueba la traducción; que Octave sea MATLAB es
otra cosa. Revisé las funciones de las que depende la detección:

- `colfilt(...,'sliding',...)` de Octave rellena con ceros fuera de la matriz (probado con `magic(4)`: la esquina da
  2,875 = 23/8), igual que dice la documentación de MATLAB. Además el relleno sólo entra en los píxeles del marco, que
  el `.m` excluye (`BOX(:,[1 end]) = NaN`), así que no decide nada.
- `mean(...,'omitnan')` y `std(...,0,'omitnan')` existen en Octave 11.3 y dan lo esperado (`[1 NaN 3]`: 2 y 1,4142).
- Queda la aritmética: otro orden de suma o otro `polyfit` cambia los números en el orden de 1e-16 relativo. Medí la
  decisión más ajustada de cada escena (la distancia mínima entre un contraste y su umbral, o entre el NTI y K1, que
  haría cambiar la decisión de algún píxel): mínimo **2,8e-5** en unidades de índice (Chaitén 2026-10-06, vecino más
  cercano, grilla movida 375 m), percentil 1 entre 4e-5 y 6e-5 por familia, sobre 739 escenas con margen finito (las
  52 sintéticas sin margen son las rechazadas antes del test). Son once órdenes de magnitud sobre el redondeo de doble
  precisión: por esa vía MATLAB no puede cambiar ninguna máscara de esta batería.

Lo que esto no cubre es una diferencia de semántica entre Octave y MATLAB que yo no haya listado; la única prueba
completa es O2, que además compara la detección.

## 3. Cómo reproducir todo

Desde Git Bash, en `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\`, con
`OCT="/c/Users/nmend/AppData/Local/Programs/GNU Octave/Octave-11.3.0/mingw64/bin/octave-cli.exe"`:

```
PYTHONIOENCODING=utf-8 python armar_entradas.py          # entradas.mat (791 escenas), entradas_etiquetas.json
PYTHONIOENCODING=utf-8 python preparar_mutantes.py       # mut_min2, mut_k1, mut_sigma, mut_sinp2
"$OCT" --no-gui --eval "MDIR='C:/vrp-trabajo/s159-pruebas/experiments/_s158_d17_diseno/osf_codigo_mirova'; SALIDA='salida_original.mat'; correr_octave"
for m in min2 k1 sigma sinp2; do "$OCT" --no-gui --eval "MDIR='C:/vrp-trabajo/s159-pruebas/experiments/_s159/o1/mut_$m'; SALIDA='salida_mut_$m.mat'; correr_octave"; done
PYTHONIOENCODING=utf-8 python comparar_octave_ports.py   # tabla del §2.2 y §2.3
PYTHONIOENCODING=utf-8 python margenes.py                # §2.4
"$OCT" --no-gui --eval "correr_vrp_octave"               # VRP con shim (MODELO)
PYTHONIOENCODING=utf-8 python comparar_vrp.py            # H1 por escena
PYTHONIOENCODING=utf-8 python vrp_por_npix.py            # H1, tabla
```

Octave tarda unos 13 s por corrida de 791 escenas. `correr_octave.m` imprime la ruta del `.m` que usa, para que no se
confunda el original con una copia mutada.

**Qué decide el shim y qué decide el `.m`.** La detección no usa shim: todo lo decide el `.m` original más funciones
estándar de Octave. El VRP usa el `.m` original de VRP (qué píxeles se quitan, `imdilate` y `strel` del paquete image,
núcleo de 3, 5 o 7 según el número de píxeles, la suma y el coeficiente) y un **shim de `fillmissing2`**
(`shim_fillmissing2/fillmissing2.m`) que es un MODELO: lineal sobre el Delaunay de Octave y vecino más cercano fuera de
la envolvente convexa. Ningún número de VRP de esta carpeta es una reproducción del interpolador de MATLAB.

## 4. Paquete O2 para MATLAB Online (preparado, no corrido)

Carpeta `C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete\`: copias sin cambios de los dos `.m` y de la
licencia MIT, `entradas_o2.mat` (311 escenas: Etna, las 190 chilenas y las 120 primeras sintéticas; 17 MB),
`correr_o2.m` y las instrucciones en `LEEME_O2.md`. El lector `leer_o2.py` (en esta carpeta) compara el resultado de
MATLAB con Octave escena a escena y dice cuál de los tres modelos de fondo coincide.

Ensayé `correr_o2.m` y `leer_o2.py` en Octave con el shim puesto, para comprobar que corren y que el lector funciona:
311 escenas, 166 con alerta, 0 listas distintas de Octave. Ese ensayo quedó en
`prueba_o2_en_octave\resultado_o2_ENSAYO_OCTAVE_CON_SHIM_no_es_MATLAB.mat` con un nombre que no se puede confundir con
el resultado real. Lo que fija O2: si MATLAB da Tot_Lmir_bk 1,072886152 en Etna, el resultado es vara del VRP, y la
tabla de H1 se puede rehacer contra MATLAB en vez de entre modelos.

## 5. Lo que no pude medir

- **MATLAB.** Todo lo de arriba es Octave. La detección queda acotada por el §2.4; el VRP no, hasta que corra O2.
- **`fillmissing2`**, incluida su extrapolación en el borde de la grilla.
- **Las 4 pasadas sin dato de la segunda ronda** (las 3 del 2026-10-18 e Isluga 2026-10-12): no hay matrices
  guardadas y reconstruirlas pide red y Earthdata (A71). Fuera.
- **La variante cúbica con anillo sensible** de `analizar_variantes.py`: no la incluí (sí la cúbica con caja por
  defecto en las 5 posiciones de grilla y las lineales y de vecino con las dos cajas). Son 10 matrices.
- **Que el código publicado sea el operacional completo de MIROVA**, y que la grilla de 750 m de la segunda ronda sea
  la de MIROVA. Esta prueba fija la traducción del `.m`, no la cadena de remuestreo ni la caja de cada volcán.
- No comparé con la función de producción de VRP Chile: fuera del frente O1.

## 6. VERIFICADO LIMPIO

- **Detección de los dos ports = `.m` original**, conjunto y secuencia, en 791 de 791 escenas, incluidas las 10
  pasadas chilenas en 19 variantes cada una. No hay que volver a mirarlo salvo que cambie un port o el `.m`:
  `PYTHONIOENCODING=utf-8 python comparar_octave_ports.py` (líneas `r2_conj`, `r2_sec`, `o1_conj`, `o1_sec`: total 0).
- **Etna reproduce el OSF en la detección** también con el `.m` corrido directo sobre el `.mat` original (5 píxeles,
  Tot_Lmir_hot 1,965342180): comando en el §2.1.
- **El `.m` no devuelve índices repetidos** en ninguna de las 791 escenas: línea «escenas con duplicados 0» de
  `correr_octave`.
- **Los ports siguen el código y no el comentario** en las zonas de la caja: el comentario del `.m` llama ROI 1 a la
  zona central, pero en el ejemplo `BOX == 2` es el cuadro central de 7 × 7 (filas y columnas 30 a 36, 49 píxeles) y
  `BOX == 1` el bloque de 21 × 19 (filas 22 a 42, columnas 24 a 42, 350 píxeles); los umbrales sensibles de noche van a
  `BOX == 2` en el `.m`, y Octave y los ports coinciden. No hay error de lectura compartido ahí.
- **L_hot** (la suma de radiancia de los píxeles alertados) es idéntico entre Octave y el segundo port en las 462
  escenas con alerta: `comparar_vrp.py`, «L_hot distinto 0».
- **La regeneración de las sintéticas es fiel**: 378 con alerta, el mismo número de la segunda ronda.
- **Los `.m` originales no se tocaron**: `md5sum` de §0, antes y después.
- **Octave 11.3 tiene lo necesario para la detección sin instalar nada**: `pkg load image` da `colfilt`, `imdilate` y
  `strel`; no instalé ningún paquete. No cargues el paquete `nan` de Forge: redefine `mean` y `std`.
