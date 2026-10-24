# Pre-registro V375-B (S162): el silencio del código de MIROVA portado a VIIRS 375 en las noches limpias (D-36)

> Escrito antes de despachar el lote y antes de ver ningún resultado del port sobre las pasadas nuevas. Lo que cambie
> después del sello va en una adenda fechada al final, nunca reescribiendo esto. Es MEDICIÓN: no adopta nada ni toca
> `pipeline/`, `data/` ni `frontend/`. Comparte lote, runner y evaluador con V375-C (`PREREGISTRO_C.md`).
> Estado: **SELLADO el 2026-10-24** (ver «Sello» al final). D-36 lo aprobó Nicolás («300 a 400 negativos de ese estrato por sensor»); el verificador
> limpio ya pasó (`verificador/INFORME.md`, correcciones en `PREREGISTRO_C.md` §8); sellado por D-48 y metido por la coordinadora
> en los despachos de la fase 1.

## 1. Pregunta

De noche, cuando MIROVA miró el volcán y no vio nada, ¿el código de MIROVA llevado a VIIRS 375 también calla, o
enciende puntos que el operador vería como actividad?

El lote de S159 (`experiments/_s159/portes/INFORME.md` P-6) midió que el port publica 7 de 65 negativos limpios,
ponderado 0,9 %, contra 3,85 % de producción (K). Pero el verificador con contexto limpio (V-1) mostró que ese número no
ve el estrato que manda: las noches en que MIROVA calla **y K también calla** (neg_resto) son 3.348 y se sortearon 45;
el port publicó 0 de 45, y con 0 eventos el bootstrap estratificado re-sortea siempre ceros. La cota honesta (Wilson
sobre 45) deja el silencio del port hasta **8,5 %**, más del doble que K. Con 0 en 445 la cota baja a ~0,85 %.

**Por qué importa.** El criterio de victoria (`docs/MISSION.md:59-103`) cuenta igual una alerta débil perdida que una
publicación de más donde MIROVA no vio nada. Si el port encendiera en 3 de cada 100 noches limpias, sobre 3.348 noches
serían ~100 puntos falsos en el tablero: borraría lo que gana en las alertas débiles. Sin esta medición, el «port
gana a K» de VIIRS 375 no se puede afirmar, y V375-E (el paquete contra K) no tiene sustrato.

- **Hipótesis.** El port, con la caja de cumbre de referencia (M14), publica en neg_resto a una tasa del orden de lo que
  K publica en todos los negativos limpios o menos.
- **Refutación.** El intervalo de la tasa de todos los negativos limpios publicados por el port queda **entero sobre**
  la de K (3,85 %): ENCIENDE DE MAS.

## 2. Qué se corre (`probe_v375.py`, `brazos.py`)

El mismo port de S159, sin cambiar nada de lo que el código de MIROVA fija: I4 / I5, 1,80e7 x 0,140625 km², la grilla de
134 x 134 de 375 m con la esquina de los TIF UTM de MIROVA, remuestreo lineal, umbrales de noche del `.m` de VIIRS 750
(NTI absoluto −0,7; 10 y 5 sigma; mínimos 0,02 / 0,003 y 0,01 / 0,003), halo del fondo 3 / 5 / 7, suma de todos los
alertados. Brazo que DECIDE en B: **M14** (caja de cumbre ±2.625 m alrededor del punto de MIROVA, la «física» de S159).
Los otros nueve brazos de ROI (V375-C) se corren en la misma pasada y se informan aquí como estratos.

La producción (K) se re-corre sobre el mismo gránulo y se pasa por `store.append_record` en una carpeta temporal (igual
que S159), como control de que la etiqueta neg_resto («K no publica») sigue siendo cierta.

«Publica» = el predicado del tablero con node (`banco_paridad.correr_node`) sobre un record sintético del port (VRP =
suma de todos los alertados; `summit` si el alertado **más cercano** está a `inner_radius_km` o menos del punto de
MIROVA). La regla del **centroide** de S159 se informa al lado. Cambio declarado respecto de S159: el verificador de
S159 (V-2, V-5) mostró que el centroide se corre con un píxel lejano y produce pérdidas que no son de detección;
MIROVA informa el píxel cercano aunque haya uno lejano más brillante (Láscar 2026-06-28 05:00).

## 3. Población y muestra (`seleccion.py` → `seleccion_salida.txt`, `objetivos_v375_bc.json`)

- Marco: la población congelada de S159 (`experiments/_s159/portes/poblacion_completa.json`, sha256
  `c08602de…f8f3`; records de `origin/main` 533398f8f, detector K re-corrido igual a lo publicado en 149 de 149;
  referencia de Mirova-v1 consolidado `fe2d0a57` y OCR `4ddd5481`; pareo ±120 s; regla D-9 en modo SN; ventana VIIRS 375
  del 2026-04-01 al 2026-10-21). Sin los días 12 y 13 de octubre (D-29 y el hueco del 12-oct,
  `experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`) ni del 17 al 20 (programa §2), también para S159.
- neg_resto = pasada nocturna con fila de MIROVA, ninguna alerta que decida (RUTINA, o alerta de 0,05 MW o menos por
  la regla SN), y K no publica. **3.323 noches** en el marco.
- **400 pasadas nuevas**, semilla 162, asignadas por estrato volcán x cenit (≤ 40°, > 40°) para que la unión con las 45
  de S159 quede proporcional al tamaño del estrato (peso de la unión entre 6,8 y 8,5). Tramos de las nuevas: T 116, O1
  174, O2 110. 16 pasadas partidas (otro record nuestro a 7 min o menos), que se informan aparte.
- En el mismo lote van, para V375-C: el censo de las protegidas (41 nuevas, unión 80), el censo de neg_pub (113 nuevas,
  unión 133) y 155 alertas bajo 1 MW nuevas (unión 200). Total del lote nuevo: **709 pasadas, 531 gránulos**.
- Las pasadas de S159 no se re-bajan: sus grillas siguen en `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\` y
  el evaluador corre sobre ellas los mismos brazos (el recálculo sin red de M14, PIX7 y SENS da lo mismo que el runner
  de S159 en 149 de 149 pasadas, `probar_brazos_salida.txt`).

## 4. Controles, que se leen ANTES de cualquier lectura (`evaluar.py` §1 y §2)

1. **Cobertura (A108)**: pasadas con estado ok por clase y lote; las que faltan, SIN DATO por pasada, fuera de todo
   denominador, y su estrato se re-pondera entre las ok. Si una clase tiene más del 10 % SIN DATO, su lectura se informa
   y no decide. **Cobertura contra la referencia de MIROVA**: la entrega la sesión del instrumento (fase 0, programa §8.1);
   sin ella el veredicto no se declara final (el evaluador lo marca).
2. **Recálculo sin red = runner**: los diez brazos recalculados sobre la grilla guardada dan npix y VRP iguales (a 1e-6
   MW) a lo que calculó el runner, en el 100 % de las pasadas x brazo. Si no, INVALIDO POR INSTRUMENTO. El runner corre
   los brazos sobre la grilla ya redondeada a float32, la misma que guarda, para que este control no falle por precisión.
3. **K re-corrido = publicado**: si la publicación de K re-corrido difiere de la del record de `data/` en más del 5 %
   de las pasadas, la lectura de K usa lo re-corrido y se dice.
4. **Control positivo**: alguna protegida de Láscar o Chillán tiene píxeles en M14; si no, el port está muerto.
5. **Nulo**: M14 contra sí mismo da 0 bloques discordantes.
6. **NUNCA** (brazo virtual que no publica nunca): recall 0, pierde todas las protegidas que K publica y P2 contra M14
   sale PIERDE (si hay más de 4 bloques).
7. **PLACEBO** (M14 con el VRP x 1,2, programa §2): publica exactamente lo mismo que M14, 0 discordantes en P2, y la
   mediana de su razón de magnitud es 1,2 veces la de M14 (a 0,02). Prueba que M mide magnitud y P2 no.

Las dos preguntas del instrumento: (1) si el port no publicara nunca, el control 6 lo mostraría y el veredicto de B
sería SILENCIO ACOTADO por razones vacías: por eso B sólo se lee si el control positivo (4) y el recall de protegidas
del port son distintos de 0; (2) si el port publicara siempre, la tasa en neg_resto daría 1. Ninguna de las dos se
puede esconder en la cuenta: las dos salen impresas antes del veredicto.

## 5. Lectura y veredicto (`evaluar.py` §3)

- **Tasa en neg_resto**: ponderada por los pesos de la unión; intervalo de Wilson sobre el **n efectivo de Kish**
  (con pesos casi parejos es la Wilson cruda). Es la cota que el verificador de S159 pidió.
- **Tasa en todos los negativos limpios**: (N_pub x tasa en neg_pub + N_resto x tasa en neg_resto) / (N_pub + N_resto),
  con neg_pub censo (tasa exacta) y el intervalo conservador que suma los extremos de cada estrato. Vara: la de K en el
  mismo marco, **133 / 3.456 = 3,85 %** (K publica todo neg_pub y nada de neg_resto, por definición).
- **Veredicto B**: SILENCIO ACOTADO BAJO K si el extremo superior queda bajo 3,85 %; ENCIENDE DE MAS si el inferior
  queda sobre 3,85 %; NO RESUELTO si el intervalo la contiene.
- **MISSION del port contra K** (la regla de S159 §5, con la corrección de V-1): ΔE = (alertas bajo 1 MW perdidas −
  ganadas) + (negativos encendidos − apagados), ponderado; IC por bootstrap estratificado por clase y estrato (2.000,
  semilla 162) **y** una cota honesta superior que reemplaza la tasa observada de encendidos en neg_resto por su extremo
  de Wilson. PIERDE PROTEGIDA si pierde alguna protegida que K publica; GANA sólo si la cota honesta queda bajo 0;
  ENCIENDE DE MAS si el IC bootstrap queda entero sobre 0; si no, NO RESUELTO.
- Se informan siempre: regla del centroide; los diez brazos; volcán, tramo (T, O1, O2: #535 el 2026-08-29), cenit cada
  10°, canal, lote (S159 o S162) y pasadas partidas aparte; la lista de cada negativo que el port publica con su VRP.
- **Qué lote decide** (`PREREGISTRO_C.md` §5.5): el lote S162 solo, con los pesos recalculados dentro del lote; la
  unión con S159 (ya vista: 0 de 45 en neg_resto) confirma. Si el veredicto B del lote y el de la unión no coinciden,
  B queda NO RESUELTO (depende del lote visto). En el humo sobre S159 solo (`humo_s159_salida.txt`), B da NO RESUELTO
  con cota 10,4 % en neg_resto (Wilson sobre n efectivo 33: la muestra de S159 tenía pesos desparejos), que es
  justamente lo que este lote viene a resolver.

## 6. Lo que este pre-registro no hace

No mide el día. No mide pasadas después del 2026-10-21 (el marco es el congelado de S159; extenderlo hasta el
2026-11-02 12:59 UTC es una adenda posible, no parte de esto). No decide la adopción del port (eso es V375-E, después de
PD3). Agrandar el lote más allá de 709 pasadas es decisión de Nicolás. El lote corre fuera de producción, en una rama de
disparo que no se mergea, y el despacho lo pide la coordinadora (S162) con la lista de brazos de §2.

## 7. Costo

709 pasadas a ~25 s cada una (S159: 24,6 s con K re-corrido) ≈ 4,9 h de runner; en 28 trozos de ~25 pasadas, ~12 min
cada uno; con 8 en paralelo, ~50 min de reloj. Artefactos: grillas de ~110 kB por pasada, ~80 MB en total.

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
