# Pre-registro V375-C (S162): dónde rigen los umbrales de cumbre del código de MIROVA en VIIRS 375

> Escrito antes de despachar el lote y antes de ver ningún resultado de los brazos nuevos. Lo que cambie después del
> sello va en una adenda fechada al final. Es MEDICIÓN: no adopta nada ni toca `pipeline/`, `data/` ni `frontend/`.
> Comparte lote, runner y evaluador con V375-B (`PREREGISTRO_B.md`, §2 a §4 valen aquí).
> Estado: **SELLADO el 2026-10-24** (ver «Sello» al final). El verificador con contexto limpio ya pasó (`verificador/INFORME.md`) y sus
> correcciones están en §8; sellado por D-48 (ver al final).

## 1. Pregunta

El código de VIIRS 750 de MIROVA tiene dos juegos de umbrales de noche: uno estricto para toda la escena (10 sigma,
mínimos 0,02 y 0,01) y uno sensible para una caja chica alrededor de la cumbre (5 sigma, 0,003). En la matriz BOX del
`.m` la escena (0) y la ROI1 (1) usan **los mismos** umbrales; sólo la caja de cumbre (2) es distinta. Así que la única
pregunta de ROI es **dónde está la caja sensible**. En 750 es de 7 x 7 celdas (5,25 km) alrededor del centro del TIF.

En VIIRS 375 no hay código. El port de S159 (`experiments/_s159/portes/INFORME.md` P-4) midió que con la caja del
mismo tamaño en metros (14 x 14 celdas de 375 m) el código no ve 11 de las 14 alertas bajo 1 MW que pierde, todas de
**Cordón Caulle** (el campo del lacolito, a 5 a 8 km del punto de MIROVA) y **Tupungatito** (el cráter, a 4,8 km al NW
del centro del TIF): ahí rige el umbral de escena y una anomalía débil no lo pasa. Con todo el ROI1 en umbrales de
cumbre las recupera (31 a 42 de 45), pero enciende más negativos (7 a 11 de 65). El `.m` dice que las ROI se ajustan
por volcán. La medición de 750 (`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §1.5) dice que la ROI
por volcán es el mayor riesgo para las protegidas.

- **Hipótesis.** Existe una caja de cumbre (global o por volcán, del conjunto cerrado de §2) que reproduce la detección
  débil de MIROVA en VIIRS 375 sin perder protegidas ni encender negativos de más que M14.
- **Refutación.** Ningún brazo GANA a M14 en P2 sin perder protegidas que K publica, y el elegido por volcán en T no
  valida en O.

**Por qué importa.** Las alertas bajo 1 MW de Cordón Caulle y Tupungatito son 274 de 949 en el marco (29 %). Con la
caja por defecto, un paquete del código en 375 dejaría al operador sin punto nuestro justo en los dos volcanes donde la
anomalía no está en el centro del TIF. Y una caja más grande en todos los volcanes puede encender nieve tibia o nube en
los otros nueve.

## 2. Brazos (`brazos.py`, conjunto cerrado: no se agrega ninguno después del sello)

Centro **M** = punto de referencia de MIROVA (X0, Y0, centro del TIF UTM de 2026-09-14/15). Centro **C** = cráter de
`volcanoes.yaml` (`vent_lat`, `vent_lon`) proyectado a la grilla. Distancias de C a M (`probar_brazos_salida.txt`):
Cordón Caulle 7,58 km, Tupungatito 4,83, Planchón-Peteroa 2,06, Villarrica 0,85, Láscar 0,80, Chaitén 0,59; los otros
cinco, 0,00.

| brazo | caja de cumbre (BOX = 2) | celdas | qué representa (equivalente en V750-B) |
|---|---|---|---|
| **M14** | ±2.625 m alrededor de M | 196 | la «física» de S159; **referencia** (O-def) |
| M13 | 13 x 13 celdas centradas en la celda más cercana a M | 169 | la caja impar más cercana a 5,25 km |
| M21 | 21 x 21 centradas en M | 441 | caja de 7,9 km (alcanza el cráter de Tupungatito) |
| C13, C14, C21 | lo mismo alrededor del cráter | 169, 196, 441 | «caja en el cráter del yaml» |
| PIX7 | 7 x 7 celdas alrededor de M | 49 | la «pixel» de S159 (descriptivo; S159: peor, 23 de 45) |
| SENS | ±7.875 m alrededor de M | 1.764 | la «sensible» de S159 (O-sens) |
| CIRC | celdas a `inner_radius_km` o menos del cráter | 201 a 8.746 | «círculo del tablero como caja sensible» |
| SENS_PT | SENS en Cordón Caulle y Tupungatito, M14 en los demás | | «O-sens sólo en PCC y Tupungatito» |

La caja de escena (ROI1) y todo lo demás del código quedan iguales en todos los brazos. En 9 de los 11 volcanes el
cráter está a 2,1 km o menos de M y las cajas C y M casi coinciden: en la práctica el brazo global se decide en Cordón
Caulle y Tupungatito, que es para lo que existe el compuesto por volcán de §5.2. Controles virtuales: NUNCA y
PLACEBO (M14 x 1,2), definidos en `PREREGISTRO_B.md` §4.

## 3. Población y muestra

La de `PREREGISTRO_B.md` §3: unión de S159 y S162 sin el 12, 13 y 17 a 20 de octubre. Para C cuentan:

| clase | marco | unión | cómo |
|---|---|---|---|
| pos_prot (alerta de MIROVA de 1 MW o más que decide, lectura A) | 80 | 80 | censo |
| pos_bajo (alerta bajo 1 MW que decide) | 949 | 200 | 45 de S159 + 155 nuevas, peso 1,0 a 5,3 |
| neg_pub (negativo limpio que K publica) | 133 | 133 | censo |
| neg_resto (negativo limpio que K no publica) | 3.323 | 445 | ver B |

Ventanas (programa §2, A119): **T** del 2026-04-01 al 06-12 (las alertas sólo OCR no deciden); **O** del 2026-06-13 al
10-21, con O1 hasta el 2026-08-28 y O2 desde #535. 14 alertas de MIROVA del marco no tienen record nuestro: quedan fuera
y se informan con la cobertura del instrumento.

## 4. Controles

Los siete de `PREREGISTRO_B.md` §4, más: (8) los brazos son los que dicen ser: M14, PIX7 y SENS dan la ROI2 idéntica a
las cajas de S159, los tamaños de la tabla de §2 se cumplen, y en una escena sintética con un foco débil en el cráter de
Tupungatito M14 no lo ve y C13, C14, C21, M21, SENS, SENS_PT y CIRC sí (`probar_brazos.py`, también corre en el runner
antes de bajar nada).

## 5. Lecturas y veredicto (`evaluar.py` §4)

Por brazo, con la regla del alertado más cercano (DECIDE) y la del centroide (informa):

- **P1, veto de protegidas** (lectura A, regla SN, el canal que decide según la ventana): protegidas que el brazo no
  publica, en total, las que K publica, y con la tabla sola. Se informa al lado la «protegida de cráter» de V375-A cuando
  la sesión del instrumento la entregue; **no reemplaza** a la lectura A.
- **P1b, cruces de 1 MW en las dos direcciones**: protegidas publicadas bajo 1 MW (baja) y pasadas no protegidas
  publicadas con 1 MW o más (sube), en particular en negativos limpios.
- **P2, suma de errores bajo 1 MW** (alerta bajo 1 MW sin publicar + negativo limpio publicado), por la **prueba de signos
  por bloque noche-volcán de D-45** (exacta hasta 20 bloques; 10.000 sorteos con semilla 162 más allá; SIN SUSTRATO con
  4 o menos), contra M14 y contra K. Las pasadas llevan el peso de su estrato, así que la suma de un bloque es real y no
  entera; el nulo es el mismo (cada bloque entero cambia de signo) y con pesos 1 la función da lo mismo que la sellada en
  2.000 de 2.000 juegos (`probar_evaluar.py`).
- **Recall** ponderado de protegidas y de bajo 1 MW con Wilson sobre n efectivo; **silencio** y **MISSION contra K** como
  en B.
- **M**: razón VRP del brazo / VRP de MIROVA en las alertas que publica, mediana, cuartiles, fracción en [0,8; 1,25] y por
  tramo de 10° de cenit. Descriptivo en C (la caja mueve la detección, la magnitud la midió S159: 1,000).

### 5.1 Brazo global

Es candidato todo brazo que **no pierde ninguna protegida que M14 publica** (veto relativo: la caja no puede quitar
una protegida que la caja de referencia ve) y **GANA a M14 en P2**. Entre los candidatos gana el de menor ΔE contra K;
a igual ΔE (a 1e-6), la caja de cumbre más chica, en este orden: PIX7, M13, C13, M14, C14, M21, C21, SENS_PT, CIRC,
SENS (la más chica es la más conservadora con los negativos). Si no hay candidatos, **M14 se queda**. La pérdida
absoluta de protegidas contra K se informa por brazo y es veto de **adopción** (V375-E), no de elección de caja: una
protegida que pierden los diez brazos por igual no la causa la caja.

### 5.2 Brazo por volcán (A115: se elige en T, se valida en O)

En la ventana T, para cada volcán, entre los diez brazos sin protegida perdida en T, el de menor suma ponderada de
errores bajo 1 MW en T; a igual suma, M14 si está entre los empatados y si no la caja más chica (el orden de §5.1). El
compuesto (cada volcán con su brazo) se lee **sólo en O**: VALIDA EN O si no pierde ninguna protegida que M14 publica y
P2 contra M14 da **GANA** (la misma vara que el brazo global); SIN SUSTRATO EN O con 4 bloques o menos; NO VALIDA EN O en
otro caso. Se informa también contra K.

### 5.3 Disparador de V375-D (números propios de 375)

V375-D se abre si: (a) B da ENCIENDE DE MAS; o (b) con el brazo global el intervalo del recall bajo 1 MW queda entero bajo
el recall de K **en el marco entero** (K tiene `pub_prod` en cada pasada de la población, así que su recall no se
estima: es censo, 0,957 en las 949 alertas bajo 1 MW); o (c) el brazo global pierde protegidas **de la tabla** (`latest.php`) que K publica. Las protegidas sólo OCR
que se pierden se informan con su número y esperan la etiqueta de cráter de V375-A: el verificador de S159 (V-2, V-3)
mostró que en Suomi NPP antes del 2026-10-09 la distancia de la fila OCR puede ser de otra pasada, y con la tabla sola el
port no pierde ninguna. Si no se cumple ninguna, V375-D no se abre por B ni por C (el programa §4 lo deja «sólo si B o C
lo exigen»).

### 5.4 Qué va a PD1

El brazo global, el compuesto por volcán con su validación en O, y el disparador de V375-D. La decisión de qué ROI lleva
el paquete de 375 (V375-E) es de Nicolás en PD1, con esto delante; el correo a Coppola
(`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`) puede preguntar la ROI real por volcán y vale más que cualquier brazo.

### 5.5 Qué lote decide

El **veto de protegidas** (§5.1, §5.2 y §5.3 c) se cuenta siempre sobre la **unión**: las protegidas son censo (80 de
80), el veto no se estima sino que se cuenta, y si decidiera sólo el lote nuevo 39 de las 80 quedarían fuera.
Las 149 pasadas de S159 ya se vieron (el informe de S159 con M14, PIX7 y SENS, y el humo de este evaluador con los diez
brazos, §6). Por eso **decide el lote S162 solo** (709 pasadas no vistas, con los pesos recalculados dentro del lote) y
la unión confirma. Para cada decisión (B, brazo global, validación por volcán, disparador de V375-D): si el lote y la
unión no coinciden, esa decisión queda **NO RESUELTO (depende del lote visto)**.

## 6. Lo que ya se vio antes del sello (humo sobre el lote de S159, `humo_s159_salida.txt`)

El evaluador se probó de punta a punta sobre las 149 pasadas de S159 con grilla guardada (sin el 12-oct). Sirvió para
dos cosas, y las dos se declaran:

1. **Control del evaluador**: reproduce con una implementación independiente los números del informe de S159 (M14 =
   «física»: recall bajo 1 MW ponderado 0,616 contra 0,618, negativos 0,0091 contra 0,0090, neg_resto 0 de 45; SENS =
   «sensible»: 0,905 y 0,0481 contra 0,905 y 0,0480; ΔE de M14 contra K +150 contra +148, sin el 12-oct). Los siete
   controles de `PREREGISTRO_B.md` §4 dieron OK (NUNCA pierde las 36 protegidas que K publica; PLACEBO publica igual y su
   M es 1,200 la de M14).
2. **Cambió dos reglas de este pre-registro, y se dice**: (i) con el veto de protegidas contra K, los diez brazos
   perdían las mismas 3 protegidas (las tres sólo OCR, ninguna de la tabla), así que ningún brazo de ROI podía ganar y
   V375-D salía siempre necesario: el veto de §5.1 pasó a ser relativo a M14 y el de §5.3 a contar la tabla sola;
   (ii) C13, C14 y SENS_PT empataron: se agregó el desempate por caja más chica. Lo que el humo mostró de los brazos
   nuevos (en S159 ganan a M14 C13, C14, C21 y SENS_PT; el compuesto por volcán elige C13 en Cordón Caulle y M21 en
   Tupungatito y valida en O) es la razón de §5.5: esas pasadas no deciden.

## 7. Lo que este pre-registro no hace

No elige umbrales distintos de los del `.m` (eso es V375-D). No mide el día. No mide pasadas después del 2026-10-21. No
toca la regla de publicación del tablero (decisión 5 del programa: «mantener el predicado de cumbre y medir
P-sinfiltro», que es de V375-E). No reemplaza la lectura A.

## 8. Revisión tras el verificador limpio (2026-10-24, `verificador/INFORME.md`, Sonnet)

El verificador midió el commit `041e7fc43` (los pre-registros no cambiaron durante su trabajo). Lo que cambió aquí por
él, todo antes del sello y antes de ver ningún dato del lote nuevo:

| hallazgo del verificador | gravedad | cambio |
|---|---|---|
| VALIDA EN O aceptaba EMPATE y SIN SUSTRATO (podía perder hasta 4 alertas contra M14 y validar) | 3 | §5.2 exige GANA, como el global; prueba nueva en `probar_evaluar.py` §3 |
| el disparador (b) comparaba el extremo del port contra el PUNTO de K en la muestra | 3 | §5.3 (b) contra el recall de K en el marco entero (censo, 0,957) |
| el desempate por volcán seguía el orden de la tabla y no la caja más chica (en el humo elegía M21 en Tupungatito, peor en O) | 3 | §5.2 usa el orden de §5.1 |
| «decide el lote S162 solo» dejaba sin representar 15 de 80 protegidas, 29 de 949 alertas bajo 1 MW y 17 de 3.323 negativos | 2 | el veto se cuenta sobre la unión (§5.5); la cobertura del lote se imprime en cada decisión |
| las cajas C y M casi coinciden en 9 de 11 volcanes | 2 | se declara en §2 |
| el veredicto no repetía que falta la cobertura contra la referencia | 1 | el evaluador termina con «VEREDICTO: PROVISIONAL» mientras falte |
| la grilla se guarda en float32 y el runner corría en float64 | 1 | el runner corre los brazos sobre la grilla ya redondeada a float32 (`probe_v375.py`) |

Lo que el verificador CONFIRMÓ: la población, los pesos de la unión (6,8 a 8,5 en neg_resto), la cota de Wilson con 0
de 445 (0,86 %), el hash de la selección, el evaluador idéntico línea a línea al humo con la caché, la prueba de signos
igual a la sellada en 2.000 de 2.000 juegos, y 0 falsos GANA o PIERDE en 400 corridas con brazos intercambiables.
Con las correcciones, el humo sobre S159 (visto, no decide) elige C13 en Cordón Caulle y en Tupungatito y valida en O
con GANA contra M14 y contra K.

## Sello (2026-10-24)

**SELLADO** por la coordinadora S162 («Retomar», local_4152952c) con la autorización vigente de Nicolás, **D-48
(2026-10-24): «sobre las decisiones mías haz lo que tú recomiendes»** (registrada en `tasks/LOOP_OBJETIVOS.md` de la
coordinadora), sobre la recomendación de esta sesión: el lote completo de 709 pasadas nuevas. D-36 (el lote de negativos)
y la medición de la ROI ya estaban aprobadas. **Revocable por Nicolás.** Desde este sello el texto de arriba no se
reescribe: lo que cambie va en una adenda fechada debajo.

Commit del sello: el que lleva el tag `s162-v375-bc-sello`. El disparo corre sobre el árbol de `ca034d66e` (rama
`s159-portes`, con `pipeline/` idéntico a `533398f8f`, el código que escribió los records del marco: así el control
«K re-corrido = publicado» compara el mismo detector) más `experiments/_s162_v375/` de este commit y el workflow. Esto
se decidió antes del sello: el `pipeline/` de `loop/activo` difiere del de 533398f8f en 12 archivos (trabajo de S157,
apagado por flag o sólo MODIS), y no se quiso que esa diferencia, por chica que sea, entrara al control de K.

La cobertura contra la referencia de MIROVA se aplica al evaluar con el código de la sesión del instrumento (PR #904,
rama `instrumento/evaluador-comun`, sin mergear), declarando su commit (instrucción de la coordinadora, 2026-10-24).

## Adenda 1 (2026-10-24, después del humo del run 40115765406 y antes del lote)

El humo (pasadas 1011 y 1062) fue la primera vez que el evaluador corrió con datos del lote S162, y destapó un error en
el camino que sólo corre con ellos: cuando decide el lote, el veto se cuenta sobre la unión (§5.5), y la unión trae
volcanes sin pasadas en el lote; el compuesto por volcán no les encontraba brazo y el evaluador caía (KeyError). Arreglo
en `evaluar.py::compuesto`: un volcán sin elección queda en M14, la misma regla que §5.2 ya aplica a un volcán sin
pasadas en T. **No cambia ninguna regla de este pre-registro**: con el lote de S159 solo la salida queda idéntica byte a
byte (`humo_s159_salida.txt`), y hay una prueba nueva en `probar_evaluar.py` §3. El runner no usa el evaluador, así que
los commits de disparo no cambian. Salida del evaluador con el humo: `humo_run40115765406_salida.txt` (controles en
verde: recálculo sin red = runner 467 de 467, K re-corrido = publicado 151 de 151; sus lecturas no se leen).

## Adenda 2 (2026-10-24, antes del lote): cobertura del marco contra la referencia de MIROVA

El control §4.1 de `PREREGISTRO_B.md` pedía la cobertura contra la referencia de la sesión del instrumento. Se aplicó con
su evaluador común sin mergear (PR #904, commit `ff452671c72e477e466ef7fa2ed59432be96f8b5`, extraído con `git archive` y
corrido tal cual), como indicó la coordinadora. Como el lote es una muestra sorteada desde los records de producción, la
pregunta es si alguna alerta de MIROVA del marco no tenía record de producción y nunca pudo sortearse:
`cobertura_marco.py` corre `evaluador_comun.cobertura` con producción (records de 533398f8f) como único lado, sobre la
ventana del marco sin los días excluidos y con las cuatro capas de la referencia que cargó el marco de S159.

Resultado (`cobertura_marco_salida.txt`): **COBERTURA OK en los dos canales**. Las 1.208 alertas nocturnas de VIIRS 375
(unión) y las 882 de la tabla tienen record de producción; 0 alertas y 0 protegidas sin record. Control: las 1.029 alertas
«pos» del marco están todas entre las observadas, y las 179 observadas que no están en el marco son exactamente las
alertas sólo OCR anteriores al 2026-06-13, que por A119 no deciden. El evaluador lee este archivo con
`--cobertura cobertura_marco.json` y el veredicto deja de ser PROVISIONAL por esa causa. No cambia ninguna regla.
