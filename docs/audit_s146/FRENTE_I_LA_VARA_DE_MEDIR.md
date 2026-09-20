# Frente I: la vara de medir (auditoría del banco de paridad, S146)

> Auditoría de sólo lectura hecha el 2026-09-20. No se modificó ningún archivo existente.
> Todo número de este informe sale de un script de `experiments/_s146_auditoria/frente_I/`
> y lleva al lado la salida cruda que lo respalda (archivos `iNN_salida.txt` de esa carpeta).
> Lo que no pude verificar va marcado **SOSPECHA**. **SIN DATO** no es ni falla ni aprobado.
>
> Los tres números auditados: "detectamos 78 de 78 noches que MIROVA alertó" y "donde MIROVA
> miró y no vio nada publicamos en 86,3 % de las pasadas VIIRS 375, 21,4 % de VIIRS 750 y
> 11,4 % de MODIS". Instrumento: `scripts/banco_paridad.py`, ventana 2026-09-01 a 2026-09-20.

## 1. Cobertura: qué se miró y qué no

| # | qué | estado | dónde |
|---|---|---|---|
| 1 | `scripts/banco_paridad.py` completo, línea por línea | LEÍDO | sección 2 |
| 2 | `scripts/referencia_mirova_unificada.py` (el cargador real del banco) | LEÍDO | sección 2 |
| 3 | `pipeline/mirova_csv_loader.py` (`load_mirova_alertas`, normalizadores) | LEÍDO: confirma que descarta toda fila que no sea alerta (l. 147 a 149); el banco NO lo usa para cargar, sólo reusa la normalización | sección 7 |
| 4 | `scripts/clasificacion_referencia.py` | LEÍDO el encabezado y el diseño: hereda la partición del banco tal cual | I-14 |
| 5 | `docs/audit_s145/PARIDAD_Y_OBJETIVOS_S145.md` | LEÍDO | |
| 6 | Código del scraper Mirova-v1, por la API de GitHub, sin clonar: `scraper.py`, `scraper_ocr.py`, `ocr_utils.py`, `reconciliar_latest.py`, `volcanes.py`, `config.py`, `README.md`, los dos workflows | LEÍDO | sección 2.1 |
| 7 | `merger_maestro.py` del scraper | BAJADO, NO LEÍDO (produce el CSV "publicable", que el banco no consume) | |
| 8 | Los dos CSV que usó el banco de S145 (`experiments/_s145_paridad/_dl_referencia/`, fijados por sha) | MEDIDOS enteros | I-01 script |
| 9 | `latest_consolidado.csv` de la raíz y el snapshot del repo | Sólo conteo de líneas: la raíz es más nueva que la descarga del banco (38.488 contra 38.404 líneas). No se usaron para no mezclar cortes | |
| 10 | Predicado del dashboard en `frontend/index.html` | LEÍDO y comparado por contenido y por sha | sección 2.4 |
| 11 | `frontend/diario.html` y `mosaico.html` | NO MIRADOS (el banco sólo ejecuta `index.html`) | |
| 12 | OSF v2.5 (`VRP_GLOBAL_ARCHIVE_2025.csv`) | MEDIDO: **no se solapa** con la referencia | sección 5.1 |
| 13 | Imágenes de MIROVA y `mirova-tif-archive` | NO MIRADOS (límite de disco y de alcance). Lo que dependería de ellas queda como SOSPECHA | |
| 14 | Reproducción del banco con sus propias funciones | HECHA, idéntica | `i00_salida.txt` |
| 15 | Pareo: distribución de la diferencia de hora, multiplicidad, por plataforma | MEDIDO | `i02_salida.txt` |
| 16 | Sensibilidad a 30 definiciones alternativas | MEDIDA | `i03_salida.txt` |
| 17 | Controles que el banco no trae | MEDIDOS | `i04_salida.txt` |
| 18 | Muestra manual de 26 pasadas, semilla 146 | HECHA | `i05_salida.txt` |
| 19 | Recall exigiendo el mismo objeto | MEDIDO | `i06_salida.txt` |
| 20 | Qué pasadas no tienen fila en la referencia | MEDIDO | `i07_salida.txt`, `i08_salida.txt` |

Ventana distinta de septiembre de 2026: **NO MEDIDA**. Todo lo que sigue vale para esa ventana de
20 días y para el régimen posterior a #571. No extrapolé a meses anteriores (A104).

## 2. Las definiciones, tal como están en el código

### 2.1 Qué es físicamente cada fila de la referencia

La referencia tiene dos canales que miran dos productos distintos de MIROVA.

**La tabla (`registro_vrp_consolidado.csv`, fuente `CONS`).** `scraper.py` baja
`https://www.mirovaweb.it/NRT/latest.php` y recorre las filas de su tabla. Cada fila de esa
tabla es una adquisición: hora, volcán, VRP, distancia y sensor. El scraper no interpreta nada
más que esto (copiado del código):

```
es_dentro_rango = dist <= conf["limite_km"]
if vrp > 0:
    if es_dentro_rango: tipo = "ALERTA_TERMICA"
    else:               tipo = "FALSO_POSITIVO"
else:
    tipo = "RUTINA"
```

- **RUTINA** es una fila que MIROVA listó para esa hora, ese volcán y ese sensor **con VRP igual
  a cero**. No es una inferencia del scraper: si MIROVA no lista la pasada, no hay fila. Lo que
  la fila NO dice es por qué el VRP fue cero: cráter frío, nube tapando, o calor bajo el piso de
  MIROVA. Para el satélite las tres cosas son "no vi nada".
- **ALERTA_TERMICA** es VRP mayor que cero con la distancia que informa MIROVA dentro del
  `limite_km` del volcán.
- **FALSO_POSITIVO es una etiqueta del scraper, no de MIROVA.** MIROVA sí detectó calor (VRP
  mayor que cero); el scraper lo rotula así sólo porque la distancia supera el límite. Los
  límites (`volcanes.py`) son 5, 5, 3, 7, 3, 5, 4, 5, 5, 20 y 5 km, **idénticos** a los
  `inner_radius_km` que el banco lee de `frontend/index.html` (salida de `i00`, campo
  `inner_radius_km` del JSON del banco). Ojo con el origen: esa distancia la mide MIROVA desde
  SU centro de grilla, no desde el cráter (ver I-07).

**La imagen (`registro_vrp_ocr.csv`, fuente `OCR`).** `scraper_ocr.py` corre cada hora, baja la
imagen `Latest10NTI.png` de cada volcán y sensor (las últimas 10 adquisiciones con su hora y su
VRP escritos) y las lee por OCR. Sólo guarda las de las últimas 24 h con VRP válido, y **sólo si
esa hora no está ya en la tabla** (`verificar_evento_no_existe`). La distancia la estima sobre
otra imagen (`Dist.png`). Por eso una `ALERTA_TERMICA_OCR` es, casi siempre, una pasada que la
imagen de MIROVA muestra con calor y que `latest.php` no listó (o todavía no listaba).
`FALSO_POSITIVO_OCR` es lo mismo con distancia estimada fuera del límite, o una alerta OCR que
`reconciliar_latest.py` degradó porque la tabla, que manda, la dio fuera de límite.

**La hora.** La tabla trae la hora como texto y el scraper la trata como UTC. Verificado de tres
maneras independientes (sección 7): el epoch coincide con la hora leída como UTC en las 3.295
filas; al parear contra nuestras pasadas la diferencia es exactamente 0 minutos; y desplazar
nuestras horas 180 o 240 minutos (lo que produciría una confusión con hora de Chile) deja cero
pareos.

**Hallazgo lateral útil: los segundos de la hora de MIROVA codifican la plataforma.** `:00` es
SNPP (y MODIS), `:01` es NOAA-20, `:02` es NOAA-21, sin una sola excepción en las 1.849 filas pareadas (suma en `i09_salida.txt`)
(salida en I-09). La referencia sí trae plataforma, aunque nadie la usaba.

### 2.2 El pareo

`parear()` busca, para cada pasada nuestra, todas las filas de referencia del **mismo volcán y
mismo sensor genérico** (MODIS, VIIRS375, VIIRS750) a más o menos 120 s. No mira plataforma.
Nuestra hora viene al minuto (`%Y-%m-%d %H:%M`); la de MIROVA con segundos 00, 01 o 02.

### 2.3 Negativo limpio, positivo y noche, como están escritos

Precedencia exacta de `etiquetar()`:

1. **pos**: alguna fila pareada cuyo tipo empieza con `ALERTA` (tabla u OCR).
2. **far_ref**: si no, alguna fila pareada cuyo tipo empieza con `FALSO_POSITIVO`. Queda fuera
   de todo denominador.
3. **neg_limpio**: si no, alguna fila pareada que sea `RUTINA`, de la **tabla**, con VRP 0, **y
   además** que esa fecha UTC, ese volcán y **ese mismo sensor genérico** no tengan ninguna
   ALERTA ni FALSO_POSITIVO nocturno en la referencia. Otro sensor puede haber alertado esa
   noche: no lo excluye (eso es la variante "estricta", que el banco informa aparte).
4. **sin_info**: todo lo demás. Fuera de todo denominador.

**Noche** es `fecha_utc[:10]`: se corta a medianoche UTC. **Nocturna** es elevación solar menor
o igual a cero en el volcán, con la misma función que usa el pipeline, aplicada igual a nuestras
pasadas y a las filas de MIROVA. MODIS diurno también se descarta (el flag está apagado: las 436
RUTINA diurnas de MODIS quedan fuera).

**Noche de volcán** (`metricas()`): es positiva si alguna pasada de esa fecha es `pos`. Cuenta
como detectada si **cualquier pasada de esa fecha publica**, incluidas las `sin_info`, las
`far_ref` y las de otro sensor. Es negativa si hay algún `neg_limpio` y ninguna `pos` ni
`far_ref`, y "publica" con la misma regla laxa.

### 2.4 "Publicamos"

El banco extrae de `frontend/index.html` el texto de diez funciones y dos constantes, las evalúa
con node y calcula `summit && valid && !artefacto && magnitud_mostrada > 0`, con
`_mirova_confirmed` siempre falso y el `inner_radius_km` de cada volcán leído del mismo HTML. Es
la misma composición que usa `latestDetection` del dashboard (líneas 1508 a 1512 de
`index.html`). Verificado:

```
sha index.html hoy: 24fba8a157136bf76509ed647c7d086d3f9f45aa      (i00; igual al del banco S145)
git status frontend/index.html -> sin cambios; último commit b973ccc39 del 2026-09-13
```

Para VIIRS 375 la magnitud mostrada es el núcleo F5 (`f5_core_vrp_mw`, o recalculado desde los
píxeles cuando el campo falta: 846 de 954 lo traen), pero **para el sí o no da lo mismo**: el
núcleo nunca borra una detección que el cúmulo muestra. Medido contra la forma reducida "cúmulo
summit con energía dentro del inner":

```
(sensor, pub del node, forma reducida): {('MODIS', 0, 0): 403, ('MODIS', 0, 1): 1, ('MODIS', 1, 1): 53,
 ('VIIRS375', 0, 0): 121, ('VIIRS375', 1, 1): 833, ('VIIRS750', 0, 0): 742, ('VIIRS750', 1, 1): 207}
```

Una sola discrepancia en 2.360 (un MODIS que el filtro de artefacto térmico oculta). El
predicado se aplica igual a los tres sensores.

## 3. Hallazgos, por gravedad

Gravedad de 1 a 5 = cuánto movería o cuánto cambia la lectura de los tres números.

### I-01. "78 de 78 noches" es cierto y no discrimina nada. GRAVEDAD 4, CONFIANZA alta

Físicamente: en septiembre nuestro sistema publica algo en la cumbre casi todas las noches de
casi todos los volcanes. Con eso, acertar las noches en que MIROVA alertó es inevitable, igual
que acertaría un sistema que gritara siempre.

```
real, cualquier sensor: (78, 78) | solo V375: (75, 75) | solo V750: (13, 14)
barajado: noches detectadas de 78 -> min 77 p05 78 mediana 78 max 78
tasa de publicacion sobre TODAS las pasadas nocturnas: {'MODIS': '53/457 = 11.6%', 'VIIRS375': '833/954 = 87.3%', 'VIIRS750': '207/949 = 21.8%'}
noches de volcan en que publicamos algo: 218 de 219
```

Barajé al azar nuestros "publica" entre las pasadas de cada volcán y sensor, 200 veces: el
recall por noche sigue siendo 78 de 78 (mínimo 77). El control que trae el banco
(`todo_publica` da 1, `nada_publica` da 0) prueba que la cuenta está bien hecha, no que el
número informe algo. **No mueve el número; le quita el significado.** "El recall está resuelto"
es una frase más fuerte que lo que esta vara puede sostener: lo que sostiene es "no perdemos
noches", que con 218 de 219 noches publicadas es casi una tautología. El recall por pasada de
VIIRS 750 (13 de 18, con 21,8 % de tasa base) sí tiene poder, y es el único que lo tiene.

### I-02. El 86,3 % vive entre 0,02 y 0,05 MW: es hipersensible al piso de magnitud. GRAVEDAD 4, CONFIANZA alta

Físicamente: lo que publicamos donde MIROVA dio cero es casi siempre un solo píxel de 375 m
apenas más tibio que sus vecinos, de pocas centésimas de megawatt. No es una alerta grande que
MIROVA se perdió.

```
publica solo si magnitud mostrada >= 0.02 MW  | noches 78/78 | V375  74.0% (276/373) | V750 20.4% | MODIS 11.4% | recall pasada 96.3% (156/162)
publica solo si magnitud mostrada >= 0.05 MW  | noches 78/78 | V375  26.3% (98/373)  | V750 19.8% | MODIS 11.4% | recall pasada 85.8% (139/162)
publica solo si magnitud mostrada >= 0.1 MW   | noches 62/78 | V375   3.2% (12/373)  | V750 17.2% | MODIS 11.4% | recall pasada 54.9% (89/162)
magnitud mostrada V375 publicada, neg: n 322 p10 0.017 p25 0.027 p50 0.041 p75 0.054 p90 0.074
magnitud mostrada V375 publicada, pos: n 143 p10 0.048 p25 0.067 p50 0.110 p75 0.199 p90 0.470
ALERTAS V375 de MIROVA, toda la historia: n 1914 min 0.01 | <0.02: 1 | <0.05: 89 | <0.10: 464
decimales con que la tabla entrega el VRP V375: {2: 1711, 1: 182}
```

MIROVA entrega el VRP con dos decimales y casi nunca alerta bajo 0,02 MW (1 caso en 1.914). Un
cuarto de lo que publicamos en negativos está bajo 0,027 MW. Con un piso de 0,02 MW (el mínimo
práctico de MIROVA) el número baja a 74,0 % sin perder ninguna noche; con 0,05 MW baja a 26,3 %
y se pierde 11 % del recall por pasada. **Esto no es un defecto de la referencia sino de la
unidad "publicamos": cuenta igual 0,016 MW que 5 MW.** La vara mide bien "cuántas veces
aparece algo en el dashboard"; no mide "cuánta energía de más publicamos", y leerla como lo
segundo exagera la brecha. Cualquier cambio futuro que mueva magnitudes cerca de ese borde
moverá el 86,3 % decenas de puntos sin que cambie nada físico.

**SOSPECHA** asociada: no sé si MIROVA muestra como 0,00 (y por lo tanto como RUTINA) un VRP
menor que 0,005 MW. Si lo hace, una parte de las RUTINA son "calor bajo el redondeo". No se
puede verificar sin las imágenes.

### I-03. Las pasadas que MIROVA no lista no faltan al azar. GRAVEDAD 3, CONFIANZA alta en el dato, media en la causa

Físicamente: MIROVA no lista todas las pasadas. De SNPP lista menos de la mitad (y ninguna de
las de las 04 UTC), y las noches con dos pasadas SNPP por volcán son las que pierden filas. Las
pasadas que MIROVA se salta son, con más frecuencia, aquellas donde nosotros tampoco publicamos
(probablemente geometría mala: volcán al borde de la escena).

```
VIIRS_NOAA20  272/300 = 90.7%   VIIRS_NOAA21 283/299 = 94.6%   VIIRS_SNPP 132/319 = 41.4%   MODIS 96 a 97 %
SNPP I-band por hora UTC: 04 -> 0/41 ; 05 -> 51/132 ; 06 -> 67/128 ; 07 -> 14/18
VIIRS I-band segun si publicamos: no publica 64/117 = 54.7% con fila | publica 623/801 = 77.8% con fila
```

Como esas pasadas van a `sin_info` (fuera del denominador), el banco es honesto con ellas; pero
el denominador queda enriquecido en pasadas "buenas". Cota de cuánto podría mover:

```
VIIRS375: base 322/373 = 86.3% | sin fila: 231, publican 178 (77.1%) | si TODAS fueran negativos: 82.8% | extremo: 75.6%
VIIRS750: base 133/622 = 21.4% | sin fila: 237, publican 42 (17.7%)  | si TODAS fueran negativos: 20.4% | extremo: 16.3%
MODIS:    base 50/439 = 11.4%  | sin fila: 14                         | 11.3% | 11.1%
```

Causa: **SOSPECHA**. Dos candidatas que no pude separar: que MIROVA procese sólo una de las dos
pasadas SNPP de la noche, o que `latest.php` sea una ventana rodante global y el scraper (cron
de 5 minutos, que en GitHub Actions se atrasa) pierda filas cuando MIROVA vuelca un lote. El
canal de imagen apoya que hay pérdidas reales de la tabla: en toda la historia, **565 de 896
alertas leídas de la imagen no tienen fila en la tabla**.

### I-04. El 11,4 % de MODIS es Cordón Caulle, y el 21,4 % de VIIRS 750 va de 5 a 57 % según el volcán. GRAVEDAD 3, CONFIANZA alta

```
PuyehueCordonCaulle | V375 94.4% (17/18) | V750 57.5% (23/40) | MODIS 67.4% (31/46)
Lastarria           | V375 87.5% (21/24) | V750  5.3% (3/57)  | MODIS  2.8% (1/36)
MODIS: promedio simple entre volcanes 10.4% | min 0.0% max 67.4%
dejando un volcan afuera: MODIS 4.8% a 12.5% | VIIRS375 85.5% a 87.7% | VIIRS750 18.9% a 23.0%
```

De las 50 pasadas MODIS publicadas en negativos, 31 son de Cordón Caulle. Sin ese volcán MODIS
publica en 4,8 %. El agregado de MODIS no describe "MODIS", describe el lacolito con
`inner_radius_km` de 20 km. En cambio el 86,3 % de VIIRS 375 **sí es parejo**: los 11 volcanes
están entre 77,8 y 94,4 %, y sacar cualquiera lo deja entre 85,5 y 87,7 %. No hay paradoja de
Simpson en VIIRS 375; sí la hay, en el sentido de que un volcán domina, en MODIS.

### I-05. La tasa "por noche" en negativos cuenta publicaciones de pasadas que MIROVA nunca listó, y se mueve sola. GRAVEDAD 2, CONFIANZA alta

El documento de S145 dice que por noche VIIRS 375 publica en el 100 % y el banco de S145 daba
para "cualquiera" 0,9268. Hoy, con la **misma referencia** y sólo 75 records nuestros más (74 de ellos
`sin_info`, posteriores al fin de la tabla), da 0,9919:

```
CUALQUIERA HOY  ... noche recall 1.0 n78 pub_neg 0.9919 n124
           S145 ... noche recall 1.0 n78 pub_neg 0.9268 n123
noches negativas: pub de 'todas' 99.2% (123/124) | pub de 'pareadas' 91.1% (113/124)
```

Causa: en `metricas()` la noche "publica" si publica cualquier pasada de la fecha, tenga o no
fila de MIROVA. Si sólo cuentan las pasadas pareadas da 91,1 %. No toca los tres números de
cabecera (el recall por noche da 78 de 78 con cualquiera de las tres reglas), pero la cifra por
noche en negativos no es comparable entre dos corridas.

### I-06. El recall cuenta cualquier publicación en la cumbre, no el mismo objeto. GRAVEDAD 2, CONFIANZA media

Exigiendo además que el radio de nuestro cúmulo y el de MIROVA difieran en 2 km o menos,
**medidos los dos desde el centro de grilla de MIROVA**:

```
radios (mismo origen) a <= 2 km: pasadas 147/162 = 90.7% | noches 77/78 = 98.7%
radios (mismo origen) a <= 3 km: pasadas 152/162 = 93.8% | noches 78/78 = 100.0%
control barajado dentro de volcan-sensor, pasadas a <= 2 km: mediana 147 rango 144-150 | real 147
```

El recall apenas se mueve (77 de 78). Pero el control barajado da lo mismo que lo real: dentro
de un volcán MIROVA alerta casi siempre en el mismo sitio, así que el radio no distingue una
noche de otra. Es una cota inferior de separación y nada más (A93, A107).

**Trampa que encontré haciendo esto, y la dejo escrita porque alguien la va a pisar:** con los
radios crudos (el nuestro desde el cráter, el de MIROVA desde su centro) el mismo cálculo da
Cordón Caulle 0 de 43 y Tupungatito 1 de 26, y el recall por noche "cae" a 54 de 78. Es falso:
los dos orígenes distan 7,57 km en Cordón Caulle, 4,86 km en Tupungatito y 2,02 km en
Planchón-Peteroa. Re-anclado, Cordón Caulle da 37 de 43 con medianas de 8,02 y 7,73 km.

### I-07. FALSO_POSITIVO es del scraper y se decide con una distancia medida desde otro punto. GRAVEDAD 2, CONFIANZA alta

En Planchón-Peteroa el centro de MIROVA está a 2,02 km de nuestro cráter y el límite es 3 km.
Caso de la muestra (M12):

```
REF TABLA: 2026-09-16 06:00:01 | VIIRS375 | VRP_MW=2.4 | Distancia_km=3.46 | FALSO_POSITIVO
NUESTRO:   distance_class=summit pc.vrp=0.116 pc.dist_km=0.566 ... f5=1.9855  -> publica 1.99 MW
```

MIROVA vio 2,4 MW a 3,46 km de su centro; nosotros 1,99 MW a 0,57 km del cráter. Un geólogo
diría que es el mismo foco y que MIROVA sí lo detectó. El banco lo manda a `far_ref`, fuera de
todo: es la decisión conservadora y está bien, pero significa que en los volcanes con centro
corrido (Planchón-Peteroa, Tupungatito, Cordón Caulle) hay alertas reales de MIROVA que no
cuentan como positivos. Son 32 pasadas en total; mover todas a positivos no cambia el 78 de 78
y subiría el recall por pasada. Además la exclusión de noche ("sin FP esa noche y sensor") saca
de los negativos las noches con fuego lejano, lo que es correcto.

### I-08. MIROVA sí alerta de día, y esas alertas quedan fuera del "78". GRAVEDAD 1, CONFIANZA alta

```
('VIIRS375', 'CONS', 'RUTINA', 'DIA') 525   ('VIIRS375', 'CONS', 'ALERTA_TERMICA', 'DIA') 2   ('VIIRS375', 'OCR', 'ALERTA_TERMICA_OCR', 'DIA') 3
ALERTA DIURNA Chaiten VIIRS375 OCR 2026-09-11 18:12:01 1.89 | misma fecha UTC con alerta nocturna: False
ALERTA DIURNA Villarrica VIIRS375 OCR 2026-09-18 19:06:00 1.38 | ... False
ALERTA DIURNA Lascar VIIRS375 CONS 2026-09-19 19:06:01 0.36 0.84 | ... False
```

Seis alertas diurnas, tres de ellas en fechas sin alerta nocturna. El banco las excluye con la
misma regla con que el pipeline descarta lo diurno, así que "78 de 78" significa "78 de 78
noches", no "todas las veces que MIROVA alertó". A76 advierte que lo diurno de MIROVA es
sospechoso (reflexión solar), así que excluirlas es defendible; hay que decirlo. De paso: el
comentario de `pipeline/store.py:175` dice que MIROVA procesa "VIIRS sólo de noche", y la tabla
muestra 525 RUTINA diurnas de VIIRS 375 en 20 días. No es asunto de la vara; lo anoto.

### I-09. La tolerancia de 2 minutos es irrelevante: el pareo es exacto. GRAVEDAD 1, CONFIANZA alta

```
MODIS     n=457 {'0': 441, '2-5': 11, '>130': 5}
VIIRS375  n=954 {'0': 687, '5-10': 19, '10-30': 182, '30-75': 28, '75-130': 2, '>130': 36}
VIIRS750  n=949 {'0': 676, '5-10': 18, '10-30': 159, '30-75': 59, '75-130': 1, '>130': 36}
tol 60 s = tol 120 s = tol 300 s (V375 86.3%, V750 21.4%); tol 600 s: V375 85.0% (328/386), V750 21.0%
tol 120s: minutos distintos de referencia por pasada -> {0: 556, 1: 1804}
```

Toda pasada pareada lo está a 0 minutos: MIROVA y nosotros rotulamos el mismo gránulo con la
misma hora de inicio. No hay segunda moda dentro de la ventana; la siguiente acumulación está a
5 o 6 minutos (el gránulo vecino de la misma órbita) y recién a 10 minutos el pareo empieza a
unir cosas que no debe (46 filas con dos pasadas nuestras). Ninguna pasada tiene más de una
fila candidata. Con tolerancia 0 s sólo sobrevive SNPP, porque NOAA-20 y NOAA-21 llevan 1 y 2
segundos: bajar la tolerancia de 60 s rompería el banco. Pareo por sensor genérico y no por
plataforma: no produce ningún cruce, comprobado con los segundos:

```
('CONS','00','VIIRS_SNPP') 107  ('CONS','01','VIIRS_NOAA20') 267  ('CONS','02','VIIRS_NOAA21') 283   (y ninguna combinación cruzada)
```

### I-10. La cola de la ventana está incompleta por construcción. GRAVEDAD 1, CONFIANZA alta

```
ultima fila imagen: 2026-09-19 06:24 | ultima fila tabla: 2026-09-20 02:45 | ultima pasada nuestra: 2026-09-20 08:10
pasadas nuestras con RUTINA posteriores a la ultima fila de imagen: 46 (V375: 11, de ellas publican 9)
latencia pasada->primera captura de la tabla (h): p05 1.7 p50 3.3 p95 6.2 max 17.3
```

Las 74 pasadas posteriores a la tabla van a `sin_info` (bien). Las 11 negativas VIIRS 375
posteriores al último OCR podrían, en teoría, pasar a positivas si la imagen mostrara una
alerta; por I-11 eso casi no ocurre. Máximo efecto: 11 de 373.

### I-11. ¿RUTINA garantiza que MIROVA no vio nada? La evidencia disponible dice que sí; la prueba definitiva no está a mi alcance. GRAVEDAD 2 si fallara, CONFIANZA media

La amenaza concreta: que la tabla dé VRP 0 mientras la imagen de esa misma pasada muestra
calor. Si eso pasara seguido, el 86,3 % no sería sobre-publicación. Hay un experimento natural:
cuando el OCR corre antes de que la tabla liste la pasada, guarda su lectura, y después la tabla
agrega su fila. Esos pares existen:

```
('ALERTA_TERMICA_OCR', 'ALERTA_TERMICA') 331
('ALERTA_TERMICA_OCR', 'SIN FILA EN TABLA') 565
('FALSO_POSITIVO_OCR', 'FALSO_POSITIVO') 69
('FALSO_POSITIVO_OCR', 'SIN FILA EN TABLA') 22
```

**Cero** pares de "imagen con calor, tabla RUTINA" en 400 pares de toda la historia. Si la
contradicción fuera frecuente tendría que aparecer ahí. Límite de la prueba: el OCR descarta
toda lectura cuya hora ya esté en la tabla, así que sólo se ven los casos en que el OCR llegó
primero; y no revisé si algún paso del scraper borra una alerta OCR al aparecer una RUTINA
(`reconciliar_latest.py` no lo hace: sólo toca FALSO_POSITIVO; `merger_maestro.py` no lo leí).
Por eso CONFIANZA media y no alta.

### I-12. "MIROVA miró y no vio nada" no dice si había nube. GRAVEDAD 1, CONFIANZA alta

La tabla no trae nubosidad. Como los dos sistemas parten del mismo gránulo, la nube es la misma
para ambos y la comparación sigue siendo justa; pero "no vio nada" incluye "no podía ver". No
mueve los números.

### I-13. El contraste con el OSF no se puede hacer: no hay solape. SIN DATO

Ver sección 5.1.

### I-14. El rótulo que verá el operador hereda esta partición. GRAVEDAD 2, CONFIANZA alta

`scripts/clasificacion_referencia.py` llama a `banco_paridad.etiquetar` tal cual. Todo lo dicho
en I-03 (pasadas sin fila) e I-07 (FALSO_POSITIVO por distancia desde otro punto) llega al
dashboard como etiqueta por pasada. No es un defecto nuevo; es el mismo con más alcance.

### I-15. El VRP leído de la imagen no siempre coincide con el de la tabla. GRAVEDAD 1, CONFIANZA alta

```
|VRP imagen - VRP tabla| en los pares con ambos > 0: n 400 iguales (<=0.005) 333 p90 0.290 max 0.970
```

67 de 400 difieren (OCR mal leído, truncado a entero en VIIRS 750 y MODIS, o actualización de
NRT a estándar). No afecta ningún sí o no del banco; sí afecta a quien use la magnitud OCR.

### I-16. El 86,3 % deriva dentro de la propia ventana. GRAVEDAD 1, CONFIANZA alta

```
01 al 10 de septiembre | V375 89.3% (201/225) | V750 22.2% | MODIS  8.7% (20/229)
11 al 20 de septiembre | V375 81.8% (121/148) | V750 20.4% | MODIS 14.3% (30/210)
bootstrap por noche de volcan, IC 95 %: MODIS 7.9% a 14.9% | VIIRS375 82.5% a 89.6% | VIIRS750 17.6% a 25.3%
```

El tercer decimal no significa nada. "86 %" es en realidad "entre 82 y 90 %".

### I-17. Dependencia del ángulo de vista. GRAVEDAD 1, CONFIANZA alta

```
cenital z<30  | V375 93.1% (94/101) | V750 32.7% (50/153) | MODIS 16.4% (21/128)
cenital z>=50 | V375 80.3% (151/188)| V750 16.9% (52/308) | MODIS  9.6% (16/166)
```

Mirando de frente publicamos más que mirando de lado, en los tres sensores. La mezcla de ángulos
de cada ventana mueve el agregado. El banco ya lo informa para VIIRS 375 (`cenital_v375`).

## 4. Tabla de sensibilidad

Cada fila cambia UNA definición respecto del banco. Salida cruda completa en `i03_salida.txt`.

| definición alternativa | noches | VIIRS 375 | VIIRS 750 | MODIS |
|---|---|---|---|---|
| **banco (base)** | 78/78 | 86,3 % (322/373) | 21,4 % (133/622) | 11,4 % (50/439) |
| tolerancia 60 s | 78/78 | 86,3 % | 21,4 % | 11,4 % |
| tolerancia 300 s | 78/78 | 86,3 % | 21,4 % | 11,3 % (51/450) |
| tolerancia 600 s | 78/78 | 85,0 % (328/386) | 21,0 % (134/639) | 11,3 % |
| negativo = toda RUTINA pareada, sin excluir noches | 78/78 | 88,1 % (453/514) | 21,6 % (142/656) | 11,4 % (50/440) |
| negativo = sin alerta ni FP esa noche, cualquier sensor | 78/78 | 86,3 % (316/366) | 19,4 % (73/377) | 9,1 % (23/252) |
| ídem, y tampoco la noche anterior ni la siguiente | 78/78 | 86,4 % (178/206) | 21,1 % (45/213) | 9,1 % (13/143) |
| noche cortada por fecha local en vez de UTC | 78/78 | 86,3 % | 21,4 % | 11,4 % |
| positivos sólo de la tabla, sin OCR | 76/76 | 86,3 % (327/379) | 21,4 % | 11,4 % |
| noche detectada sólo si publica una pasada positiva | 78/78 | igual | igual | igual |
| sólo SNPP | 42/42 | 83,6 % (46/55) | 21,6 % (30/139) | |
| sólo NOAA-20 | 50/50 | 87,9 % (138/157) | 23,3 % (55/236) | |
| sólo NOAA-21 | 49/49 | 85,7 % (138/161) | 19,4 % (48/247) | |
| sólo Aqua / sólo Terra | | | | 10,1 % / 12,6 % |
| primera / segunda mitad de la ventana | 32/32, 46/46 | 89,3 % / 81,8 % | 22,2 % / 20,4 % | 8,7 % / 14,3 % |
| sin Cordón Caulle (el volcán que más pesa; `i09_salida.txt`) | | 85,9 % (305/355) | 18,9 % (110/582) | **4,8 %** (19/393) |
| pasadas sin fila contadas como negativos (cota) | | 82,8 % | 20,4 % | 11,3 % |
| ídem, sólo las que no publicamos (cota extrema) | | 75,6 % | 16,3 % | 11,1 % |
| recall exigiendo radio a 2 km, mismo origen | 77/78 | | | |
| *cambiando el predicado:* publica sólo si magnitud mayor o igual a 0,02 MW | 78/78 | **74,0 %** | 20,4 % | 11,4 % |
| *ídem* 0,05 MW | 78/78 | **26,3 %** | 19,8 % | 11,4 % |

**Rangos.** Moviendo sólo definiciones de la referencia, del pareo y de la noche:

- noches: **77 a 78 de 78** (y 76 de 76 sin OCR). Estable, y sin poder discriminante (I-01).
- VIIRS 375: **82 a 88 %** en las alternativas medidas, **75,6 a 88,1 %** contando la cota
  extrema de I-03. La vara sirve para este número.
- VIIRS 750: **16 a 23 %** en agregado; entre volcanes, de 5 a 57 %.
- MODIS: **9 a 13 %** en agregado; **4,8 %** sin Cordón Caulle.

Lo único que mueve el 86,3 % "entre 40 y 90" no es la referencia: es el piso de magnitud de lo
que llamamos publicar (I-02).

## 5. Contraste independiente y muestra manual

### 5.1 OSF v2.5: SIN DATO, no hay solape

```
%d/%m/%Y %H:%M total 615470 no parsean 28 max 2025-12-31 23:45:00 max TierA Chile 2025-12-31 06:30:00
grep -c "/2026 " -> 0        (segunda herramienta)
referencia del scraper: 2026-01-10 19:06:00 a 2026-09-20 02:45:00
```

El OSF termina el 2025-12-31 y la referencia del scraper empieza el 2026-01-10. No hay un solo
día en común, así que la comparación pedida no se puede hacer. Aviso para quien lo intente: las
fechas del OSF son **día/mes/año**; leídas como mes/día/año fallan 373.722 filas de 615.470 en
silencio y el máximo aparente es el 12 de diciembre.

El único contraste independiente que sí existe es interno al scraper: tabla contra imagen, que
son dos productos distintos de MIROVA leídos por dos caminos distintos (I-11): 331 alertas
coinciden, 69 fuera de límite coinciden, **0 contradicciones** de tipo, y 565 alertas de la
imagen no están en la tabla. Esa última cifra es la cota que importa: **la tabla sola pierde
cerca de dos de cada tres alertas que la imagen muestra**, y por eso el canal OCR no es opcional
para los positivos. Para los negativos no hay segundo canal: la imagen sólo se guarda cuando hay
calor.

### 5.2 Muestra manual: 26 pasadas, semilla 146

Dos por sensor y por rótulo (donde había). Filas crudas completas en `i05_salida.txt`. Mi juicio
"como geólogo" mirando fila y record:

| # | pasada | rótulo del banco | ¿es el rótulo que pondría? |
|---|---|---|---|
| M01 | Villarrica MODIS 09-04 07:50, MIROVA 4,75 MW a 1,41 km, nosotros 3,86 MW | pos | sí |
| M02, M03 | Lastarria y Copahue MODIS, MIROVA 0, nosotros `far` sin publicar | neg_limpio | sí |
| M04 | Villarrica MODIS 02:15, RUTINA la misma noche que M01 | sin_info | sí: el lago de lava estaba activo esa noche, no es un negativo limpio |
| M05, M06 | MODIS sin fila en MIROVA | sin_info | sí |
| M07 | Tupungatito V375, MIROVA 0,13 MW a 5,21 km (tabla e imagen coinciden), nosotros 0,109 MW | pos | sí; las distancias 5,21 y 0,10 km son el mismo sitio medido desde dos orígenes (I-06) |
| M08 | Lastarria SNPP, sólo imagen: 0,03 MW a 1,49 km; nosotros 0,10 MW a 1,07 km | pos | sí |
| M09 | Llaima V375, MIROVA 0, nosotros 0,066 MW, 1 píxel a 2,78 km, cenital 67° | neg_limpio | sí. Un píxel tibio de lado, lejos del cráter: es el caso típico de I-02 |
| M10 | Láscar V375, MIROVA 0, nosotros **0,016 MW**, t_max 267,5 K | neg_limpio | sí. Bajo el piso de MIROVA |
| M11 | Lastarria V375, MIROVA 2,68 MW a 28 km; nosotros 0,026 MW en cumbre | far_ref | sí: MIROVA vio un foco lejano, no informa del cráter |
| M12 | Planchón-Peteroa V375, MIROVA 2,4 MW a 3,46 km; nosotros 1,99 MW a 0,57 km | far_ref | **no**: es el mismo foco y MIROVA lo detectó (I-07). Conservador, no dañino |
| M13, M14 | Copahue y Planchón-Peteroa V375, RUTINA en noche con alerta | sin_info | sí |
| M15, M16 | V375 sin fila (M16 es SNPP) | sin_info | sí |
| M17 | Cordón Caulle V750 SNPP, MIROVA 0,49 MW; nosotros cúmulo en 0,0 MW | pos, no publica | sí: es una de las 5 pérdidas D25 |
| M18 | Cordón Caulle V750, MIROVA 0,8 MW; nosotros 0,052 MW | pos, publica | sí como detección; la magnitud es 15 veces menor |
| M19, M20 | V750 MIROVA 0, nosotros nada | neg_limpio | sí |
| M21, M22 | V750 MIROVA 1,48 MW a 26,4 km y 1,36 MW a 24,6 km; nosotros 2,70 MW a 26,1 km y 2,13 MW a 24,7 km, `far` | far_ref | sí, y además son un control positivo lindo: los dos sistemas ven el mismo fuego lejano en el mismo radio |
| M23, M24 | V750 RUTINA en noche con alerta | sin_info | sí |
| M25, M26 | V750 sin fila | sin_info | sí |

25 de 26 rótulos son los que pondría. El que no (M12) es un error del lado conservador.

## 6. Veredicto

**La vara SIRVE CON ESTAS SALVEDADES.**

Lo que mide, lo mide bien: la referencia está en UTC, sin duplicados, el pareo es exacto al
minuto y nunca cruza plataformas, el predicado se extrae del `index.html` de hoy (mismo sha), los
límites de distancia son los mismos en los dos lados, y el 86,3 % de VIIRS 375 aguanta todas las
definiciones alternativas razonables de negativo, de noche y de tolerancia (82 a 88 %), es parejo
en los 11 volcanes y en las tres plataformas.

Las salvedades, en orden de importancia:

1. **"78 de 78 noches" no es evidencia de buen recall.** Es verdadero y lo daría igual un
   sistema que publicara al azar con nuestra tasa (I-01). No debe usarse para decir "el recall
   está resuelto". La cifra con poder es la de VIIRS 750 por pasada, 13 de 18.
2. **El 86,3 % cuenta apariciones, no energía.** La mitad de esas publicaciones está bajo
   0,041 MW y un cuarto bajo 0,027 MW, donde MIROVA prácticamente no publica. Con el piso
   práctico de MIROVA (0,02 MW) es 74 % (I-02). Como medida de "cuánto más ruidoso se ve el
   dashboard" sirve; como medida de "cuánto nos alejamos de MIROVA" exagera.
3. **MODIS 11,4 % y VIIRS 750 21,4 % no deben citarse sin el volcán**: uno es Cordón Caulle,
   el otro va de 5 a 57 % (I-04).
4. El denominador está sesgado hacia pasadas de buena geometría (I-03): el valor real de
   VIIRS 375 puede estar unos puntos más abajo, no más arriba. Cota: 75,6 a 82,8 %.
5. El significado de RUTINA ("MIROVA listó esa pasada con VRP cero") está respaldado por cero
   contradicciones en 400 pares, no por las imágenes (I-11). Es la pieza con menos prueba
   directa de toda la vara.

Nada de lo encontrado invierte la dirección del proyecto: sobre-publicamos en VIIRS 375, mucho,
y en todos los volcanes. Lo que cambia es el tamaño aparente del problema (son centésimas de
megawatt) y que el recall no está "demostrado" por esta vara, sólo "no refutado".

## 7. Verificado limpio

Cosas que fui a buscar como posible defecto y no lo son, con su evidencia:

| sospecha | resultado | evidencia |
|---|---|---|
| El banco no se reproduce | Se reproduce idéntico con sus funciones; las diferencias de hoy (1 negativo MODIS más, 74 `sin_info` más) son data nueva del cron | `i00_salida.txt` |
| Hora local contra UTC | No. Epoch igual a la hora leída como UTC en 3.295 de 3.295 filas; pareo a 0 minutos; desplazar 180 o 240 minutos deja `{'sin_info': 2360}` | `i01`, `i03` |
| Filas duplicadas | 0 claves repetidas en los dos CSV, en toda la historia | `i01` |
| Dos filas de MIROVA para una pasada nuestra | 0 casos hasta 600 s de tolerancia | `i02` bloque C |
| Dos pasadas nuestras para una fila | 0 a 120 s; 10 a 300 s; 46 a 600 s | `i02` bloque C2 |
| Pareo cruzando plataformas | 0 cruces; los segundos de MIROVA identifican la plataforma | `i04` bloque 1 |
| Filas de MIROVA sin pasada nuestra | 7 de 1.856 (6 MODIS, 1 VIIRS 750); ninguna alerta: `alertas_sin_record` vacío | `i02` bloque B, banco |
| La noche cortada a medianoche UTC parte noches chilenas | No: las filas nocturnas caen todas entre las 00 y las 08 UTC; cortar por fecha local da los mismos números | `i01`, `i03` |
| El predicado no es el del dashboard de hoy | Es el mismo archivo (sha igual, sin cambios locales) y la misma composición que `latestDetection` | sección 2.4 |
| VIIRS 375 usa otra regla para el sí o no | No: el núcleo F5 cambia la magnitud, nunca el sí o no (833 de 833 coinciden con la forma reducida) | `i04` bloque 6 |
| Límites de FALSO_POSITIVO distintos de nuestro `inner` | Idénticos en los 11 volcanes | `volcanes.py` contra `inner_radius_km` del banco |
| El respaldo de abril mete filas en la ventana | No: `origen: {'principal': 3374}` | `i01` |
| `load_mirova_alertas` contamina el banco | No: el banco usa `cargar_referencia_unificada`, que conserva todas las filas; del cargador viejo sólo importa normalizadores. La advertencia de la memoria es cierta para **el resto** del proyecto (l. 147 a 149 descartan todo lo que no sea alerta) | sección 1 |
| RUTINA con VRP distinto de cero | 0 casos | `i01` |
| Control del instrumento muerto | Todo publica da 373 de 373 y 78 de 78; nada publica da 0 y 0 | `i03` |
| Mi primer control de desplazamiento (+37 min) dio 238 pareos | Era un mal control mío, no un defecto: los gránulos VIIRS van en grilla de 6 minutos y 37 cae a 1 minuto de la grilla, así que pareaba con la pasada de otra plataforma 36 minutos después. Con +39, +180 y +240 da cero. Lo dejo escrito porque el +37 sigue en `i02_salida.txt` | `i02` bloque D, `i03` |

## Anexo: cómo repetir

```
cd "VRP Chile"
python experiments/_s146_auditoria/frente_I/i00_base.py          # reproduce el banco y crea _cache_recs.json (usa node)
python experiments/_s146_auditoria/frente_I/i01_referencia.py    # crea _cache_ref.json
python experiments/_s146_auditoria/frente_I/i02_pareo.py ... i08_cota_sin_fila.py
```

Los dos caches se borraron al terminar (se regeneran con `i00` e `i01`). Las salidas crudas
`i00_salida.txt` a `i08_salida.txt` quedan en la carpeta. Los scripts leen la referencia fijada
de `experiments/_s145_paridad/_dl_referencia/` para medir sobre los mismos CSV que el banco de
S145; nuestros records son los de hoy.
