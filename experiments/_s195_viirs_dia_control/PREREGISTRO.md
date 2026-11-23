# Pre-registro del control diurno de VIIRS (S195): persistencia nocturna, criterio sellado antes de medir

> **Qué es.** El criterio con que se va a juzgar un control para las manchas diurnas de VIIRS (375 y 750 m), escrito y
> commiteado **antes** de medir sobre los datos que deciden. Lo pidió Nicolás el 2026-11-22, textual, «Sí,
> pre-regístralo», a la pregunta «¿Diseño y pre-registro en el experimental un control para las manchas diurnas de
> VIIRS, por ejemplo exigir que la celda alertada de día haya alertado alguna vez de noche?», el mismo día en que
> decidió no encender VIIRS de día en producción (respuesta transmitida por la coordinadora S195; no la leí de primera
> mano).
>
> **Sello.** El evaluador es `experiments/_s195_viirs_dia_control/evaluar.py`,
> sha256 del evaluador (fin de línea LF): `24050c7ac2072c759ac186181161bc3e4c4593b8bd32b126e1c92d9727d6ed0b`.
> La prueba `tests/test_viirs_dia_control_preregistro_s195.py::test_sello_hash_del_evaluador_en_el_preregistro`
> compara ese hash con el archivo: editar el evaluador sin re-sellar este documento deja el CI en rojo. Base:
> `origin/main` en `3bb44e830` (2026-11-22). Sin cambio de la lógica de detección ni de ningún valor publicado: no toca
> `pipeline/`, perfiles, workflows ni tablero.

## 1. El fenómeno y la pregunta

De día, la banda de 4 µm de VIIRS (I4 en 375 m, M13 en 750 m) no mide sólo calor: suma la luz del Sol que refleja la
superficie y el calentamiento de lo que el Sol ilumina (laderas de roca desnuda, suelo de los cauces, bordes de nube).
El detector de MIROVA (la vía), pensado para la noche, publica entonces manchas que no son calor volcánico. En el A/B
diurno (#813) el brazo con el día encendido recuperó 23 de 34 alertas protegidas de MIROVA en VIIRS 375 (20 de Chillán
en erupción, en la cumbre), pero publicó unas 6 manchas de 1 MW o más fuera de Chillán en unos 5 meses (Láscar flanco
este; Cordón Caulle a 17 y 18,5 km, que su radio interno de 20 km clasifica como cumbre; Tupungatito; Lastarria).

La diferencia física que el control aprovecha: el calor volcánico (lago de lava, cráter, fumarolas, una erupción) está
también de noche, cuando no hay Sol. La mancha solar no. **Pregunta:** si se publica de día sólo lo que cae donde el
detector alertó alguna vez de noche en el último mes, ¿se van las manchas solares sin perder las alertas de cumbre de
MIROVA, y eso es más que lo que lograría suprimir la misma cantidad de publicaciones al azar?

## 2. La regla y su alternativa

**Celda.** Fila y columna de un píxel alertado (`anomaly_pixels[].fila`, `.col`) en la grilla fija de MIROVA del
sensor (`pipeline/grillas_mirova.yaml`): 134 × 134 celdas de 375 m en VIIRS 375 y 67 × 67 de 750 m en VIIRS 750. La
grilla es fija por volcán, así que la misma celda es el mismo lugar del terreno en todas las pasadas (a la precisión de
la geolocalización). Las grillas de 375 y 750 no se mezclan; los tres satélites de cada una sí (Suomi NPP, NOAA-20 y
NOAA-21 ven el mismo terreno).

**Historia nocturna de una pasada diurna.** Las celdas alertadas por los records **nocturnos** (elevación solar menor o
igual a 0 sobre el volcán, `evaluar_diurno_k.es_dia_vol`) del mismo volcán y la misma grilla, con instante en
[pasada − 30 días, pasada), es decir, estrictamente antes: la regla se puede aplicar en tiempo casi real.

**R1 (principal, persistencia nocturna).** Una publicación diurna se conserva si **alguna** de sus celdas alertadas
tiene, a una celda o menos (distancia de Chebyshev 1, vecindad de 3 × 3), una celda de su historia nocturna. Si no, se
suprime: la pasada no se publica. La regla no cambia ni el VRP ni la posición del record.

**R2 (alternativa, celda radiante).** Lo mismo, exigido a la **celda radiante** (la de mayor temperatura de brillo MIR;
empate, la de menor fila y columna). Fundamento: la regla de posición «radiante» (D8', decisión de Nicolás del
2026-11-15) pone el record en el cúmulo de la alertada más radiante. Si una pasada tiene una celda del cráter con
historia y una mancha solar más caliente en la ladera, R1 la conserva y el tablero la publica en la ladera; R2 la
suprime.

**Por qué cada número.** 30 días: un mes cubre varias semanas de nubes y la intermitencia de una fuente débil (una
celda fumarólica que alerta una noche de cada nueve tiene en un mes unas tres oportunidades), y es lo bastante corto
para que la actividad de hace un año no autorice manchas de hoy. Vecindad de 1 celda: la misma fuente cae en celdas
vecinas de una pasada a otra por la geolocalización y el remuestreo a la grilla (la huella de un píxel VIIRS crece
fuera del nadir). Noche estricta: con el Sol bajo el horizonte la banda MIR no tiene reflexión solar, y la superficie
calentada de día ya se enfrió. Una publicación diurna sin celdas no se puede juzgar: se conserva y cuenta en I1.

**Lo que no entra, y por qué.** (a) El borde de la grilla (la celda (35,1) de Villarrica a 26,5 km que se calienta de
día): lo consideré como tercera regla y lo saqué antes de sellar, porque esas celdas dan records lejanos que el
predicado del tablero no publica y cada alternativa resta alfa a R1 (§5). (b) Contraste MIR menos TIR: los records no
guardan la TIR por píxel, y medirlo exige tocar `pipeline/` (A45). (c) Tope de cenit del sensor: no hay mecanismo
físico que separe la mancha solar del calor por el ángulo de vista. (d) Cualquier valor por volcán (A4).

**Costo declarado.** Una erupción que empieza de día no tiene historia: sus pasadas diurnas anteriores a su primera
noche se suprimen (a lo más unas horas, porque cada noche hay varias pasadas VIIRS). Una fuente real que sólo se ve de
día (un píxel chico casi al nadir sobre un foco débil) se suprime si de noche no alcanza el umbral.

## 3. Datos de desarrollo y datos de veredicto

**Desarrollo (ya mirados, no deciden):** las ventanas W2 a W7 del A/B diurno (2026-06-13 a 06-30, 07-20 a 07-31, 08-13
a 08-31, 09-01 a 09-20, 10-01 a 10-14 y 10-15 a 11-15; 115 días), los 11 volcanes Tier A, los dos sensores VIIRS. Todo lo
publicado de día en ellas se miró: las 19 protegidas no recuperadas y las 5 publicaciones sin fila (INFORME del
2026-11-22), las 23 recuperadas (INFORME_RECALCULO), los 8 negativos publicados (nota s195_viirs_dia); y el evaluador
de este pre-registro se corrió sobre ellas (§8). La regla se pensó conociendo esos casos.

**Veredicto (no mirados):** las publicaciones diurnas VIIRS de los 11 Tier A en cinco ventanas, 212 días:

| ventana | fechas | por qué no está mirada |
|---|---|---|
| V1 | 2026-04-01 a 2026-06-12 | el brazo diurno de la vía nunca corrió en esas fechas; empieza en abril porque la tabla de MIROVA trae VIIRS por pasada desde abril (A119) |
| V2 | 2026-07-01 a 2026-07-19 | hueco entre W2 y W3 |
| V3 | 2026-08-01 a 2026-08-12 | hueco entre W3 y W4 |
| V4 | 2026-09-21 a 2026-09-30 | hueco entre W5 y W6 |
| V5 | 2026-11-23 a 2027-02-28 | posterior al sello (verano austral: Sol más alto) |

Lo que sí se sabe de esas fechas y se declara: estudios diurnos anteriores con el detector K (S151, S163, W1 de Láscar
del 2026-03-01 al 03-20, fuera de V1) miraron otros records; y el informe del 2026-11-22 nombra lugares donde las
manchas se repiten (Lastarria 10 km al norte, Láscar 29 km al noreste, Isluga 15 km al noroeste). La regla no usa
ningún lugar: es la misma para todas las celdas.

**Una sola mirada.** El veredicto se mide una vez, con V1 a V5 juntas, no antes del **2027-03-07** (fin de V5, más los
±3 días de NHI y la latencia de la referencia); el evaluador se niega a correr la fase «veredicto» antes
(`puede_medir_veredicto`). No se mira V1 a V4 por adelantado.

**Cómo se producen los datos, sin tocar `pipeline/`:**
- Records diurnos: el perfil `_s190_ab_diurno_via_on` (el brazo del A/B, producción más los dos flags del día) sobre V1
  a V5, despachado desde un tag, en carpetas propias. Ningún cambio de código: la regla es una función de los records
  (celdas y noches) que aplica el evaluador.
- Historia nocturna: los records nocturnos VIIRS de producción, `data/mirova_equivalent/<Volcán>.json`, en **el primer
  commit de `main` con fecha posterior al 2027-03-07 00:00 UTC** (es la historia que tendría el laboratorio en
  operación, porque hereda las noches de producción). I4 comprueba que las noches del brazo y las de producción
  coinciden.
- Referencia MIROVA: los 4 CSV de `sustrato_k.ORIGEN_REF` (snapshot de Mirova-v1 en `data/mirova_reference/`) en ese
  mismo commit de `main`, copiados a una carpeta y congelados con su sha256.
- NHI: las series de NHI-v1 en **el primer commit de NHI-v1 con fecha posterior al 2027-03-07 00:00 UTC**
  (`bajar_nhi.py`, que escribe el commit en `COMMIT.txt`; el evaluador lo copia a su salida).
- Las cajas de NHI quedan las de `nhi_cajas.json` (commit `09c45707e9a6`), selladas por prueba. Si NHI-v1 corrige
  Chillán antes de medir, usar la caja nueva exige re-sellar (pregunta 3).

## 4. Etiquetas y qué referencia usa cada parte (A115)

Cada publicación diurna (predicado del tablero ejecutado con node sobre `frontend/index.html`, A97) se parea con la
pasada de MIROVA del mismo volcán y sensor a ±120 s (`clase_mirova.resumir_pasadas`, canal unión) y recibe una
etiqueta (`evaluar.etiquetar`):

- **P, protegida de cumbre:** la **tabla** de MIROVA (`latest.php`, fuente CONS) alertó la pasada con 1 MW o más a no
  más del radio interno. Sólo la tabla, porque la distancia de una fila sólo OCR puede venir de otra pasada (S150;
  INFORME del 2026-11-22: 11 de 19 «protegidas» no eran de cumbre).
- **O, otra:** MIROVA alertó la pasada de otra forma (sólo OCR, bajo 1 MW, lejos, sin geometría). Se informa.
- **menor:** MIROVA no alertó (no tiene la pasada, o la tiene como RUTINA o FALSO_POSITIVO) y lo publicado es menor
  que 1 MW. Se informa; no entra al criterio ni al nulo.
- **R, real con respaldo:** MIROVA no alertó, 1 MW o más, y hay respaldo independiente de calor: (a) SWIR, NHI-v1 alertó
  en una escena a ±3 días de la fecha UTC de la pasada y su caja de análisis (cuadrado de medio lado `buffer_km`,
  `nhi_cajas.json`) contiene la posición publicada; o (b) si MIROVA **no tiene** la pasada, la tabla de MIROVA alertó 1
  MW o más en la cumbre del mismo volcán, cualquier sensor, a ±12 h (la cumbre estaba caliente medio día antes o
  después).
- **A, artefacto sin respaldo:** MIROVA no alertó, 1 MW o más, sin respaldo. Se informa aparte cuántas son
  **desmentibles** (la caja usable de NHI contiene la posición y hay una escena con alerta no nula a ±3 días que no
  alertó) y cuántas no (fuera de toda caja, o sin escena): una fuente real que sólo se ve de día y cae fuera de la caja
  queda como A y su supresión contaría como acierto (crítica 3).

**Qué referencia usa cada parte.**
- **Pérdidas (P): MIROVA, tabla.** Lo que la regla no puede hacer es quitar lo que MIROVA publica en la cumbre: es la
  hoja de respuestas de producción, y lo que se quiere encender es producción.
- **Artefactos (A) y reales (R): MIROVA más SWIR.** «MIROVA no lo publicó» es necesario; SWIR (NHI-v1, Sentinel 2 y
  Landsat) y la cumbre de MIROVA en pasadas vecinas rescatan como reales las publicaciones con calor confirmado, para
  que la regla no gane puntos suprimiendo calor verdadero.
- **OVDAS y MIROVA OLI/MSI: revisión, sin voto.** En el repo no hay una serie de OVDAS que se pueda leer con un script,
  y las imágenes OLI/MSI de MIROVA son imágenes. Entran como revisión de Nicolás de cada P y R que la regla suprima y de
  las A que conserve, junto al veredicto. No lo cambian.

**Límites de SWIR que se declaran.** NHI no guarda la posición de sus píxeles calientes, sólo si la caja tiene alguno;
una mancha fuera de la caja (Cordón Caulle a 17 km, Lastarria a 10 km) no puede ser respaldada ni desmentida por SWIR.
Lastarria no está en NHI-v1. Y **NHI-v1 mira Nevados de Chillán en el lugar equivocado**: su `config_nhi.py` (commit
`09c45707e9a6`) pone el centro a 60,97 km del de `volcanoes.yaml`, al lado de Antuco (`salida_nhi_cajas.txt`). El
evaluador marca una caja como usable sólo si contiene el punto del volcán de `volcanoes.yaml`; la de Chillán no lo es, y
sus publicaciones sólo pueden ser R por la cumbre de MIROVA. Los otros 9 volcanes con serie tienen el punto dentro de la
caja.

## 5. Criterio de éxito

Sobre las publicaciones diurnas VIIRS de V1 a V5 (`evaluar.evaluar_regla` y `evaluar.veredicto`), con n y q el número
de publicaciones de cada etiqueta y las que la regla suprime:

1. **SIN PODER** si n_A < 6 o n_P < 5. Con menos de 6 artefactos, quitar 2/3 son 4 y no se distingue del azar; con
   menos de 5 protegidas, «no pierde ninguna» no dice nada.
2. Una regla **cumple** si se dan las cuatro condiciones:
   - quita al menos 2/3 de los artefactos: 3 q_A ≥ 2 n_A;
   - **no pierde ninguna protegida de cumbre: q_P = 0** (declarado: cero es lo natural, porque la regla existe para
     encender producción y producción no puede perder lo que MIROVA publica en la cumbre);
   - pierde a lo más 1/3 de las R: 3 q_R ≤ n_R;
   - supera a la **regla al azar con la misma supresión**: si la regla suprime k publicaciones del universo P, A, R y O,
     el nulo suprime k al azar del mismo universo; p = P(X ≥ q_A), X hipergeométrica (exacta, `p_hiper`), y se exige
     p < alfa de la regla. Es el control nulo (A110): una regla que suprime sin distinguir la mancha del calor no lo
     supera aunque quite muchos artefactos, porque también se lleva protegidas, reales y lo que MIROVA alertó de otra
     forma (O entra al universo por la crítica 4).
3. **Elección entre reglas, decidida antes.** Alfa repartido por Bonferroni para que la falsa alarma total quede en
   0,05: R1 con 0,04, R2 con 0,01. Si R1 cumple, CUMPLE con R1 (R2 se informa). Si R1 no cumple y R2 sí, CUMPLE con R2.
   Si ninguna, NO CUMPLE.

**INVALIDO** antes que todo lo anterior si falla el instrumento (§6).

**Se informa sin voto** (crítica 2 y 3), para que Nicolás lea el resultado entero:
- **p estratificado:** el mismo nulo con la supresión al azar dentro de cada volcán y grilla (`p_estratificado`). Mide
  si la regla distingue dentro de un mismo volcán; no vota porque en un volcán donde todo lo diurno es mancha (Cordón
  Caulle en desarrollo) el azar estratificado quita lo mismo que la regla, y eso no es una falla de la regla.
- **R0, persistencia por volcán:** se conserva si el volcán alertó cualquier celda de noche en su grilla en los 30 días.
  Es la regla trivial que hay que superar: si R0 quitara lo mismo que R1, la celda no aportaría nada.
- **A desmentibles y no desmentibles**, con lo que quita cada regla en cada grupo; las cuentas por ventana (V1 a V5),
  porque V5 es verano y el desarrollo fue invierno y primavera; y las supresiones de O y de menor.
- **Límite declarado del nulo:** las A se repiten en los mismos lugares (§3), así que no son unidades independientes
  como supone la hipergeométrica; el p es optimista en esa medida.

## 6. Instrumento (INVALIDO)

- **I1:** más del 1 % de las publicaciones diurnas sin celdas (la regla no se puede aplicar).
- **I2:** para algún volcán, grilla y ventana, menos del 90 % de los días de [inicio − 30, fin] con algún record nocturno
  de producción (un hueco de historia fabrica supresiones).
- **I3:** más del 5 % de las pasadas diurnas VIIRS de la tabla de MIROVA sin record del brazo a ±120 s (un hueco del
  brazo esconde publicaciones).
- **I4:** menos del 95 % de los records nocturnos del brazo con par en producción tienen las mismas celdas alertadas
  (la historia de producción no sería la del brazo).
- **I5:** los records del brazo no tienen un solo perfil (`_s190_ab_diurno_via_on`) y un solo sha de código.

## 7. Qué se hace con cada resultado

- **CUMPLE:** la regla elegida va al perfil `laboratorio` (implementarla toca `pipeline/`: PR con tag defensivo y
  confirmación de Nicolás, A45) y, con eso, Nicolás decide si VIIRS de día se enciende en producción con el control.
  Un control que no está en el código de MIROVA es una divergencia nueva (catálogo D) y una fila de la ficha SDA.
- **NO CUMPLE:** VIIRS de día sigue apagado en producción. Se anota con los números en
  `docs/BEYOND_MIROVA_EXTENSIONS.md` §12. No se re-corre con otro umbral, otra ventana u otra etiqueta sin un
  pre-registro nuevo que diga que es el segundo intento.
- **SIN PODER:** se extiende V5 hasta el 2027-05-31 y se re-evalúa **una vez** con este mismo criterio (no antes del
  2027-06-07); si sigue SIN PODER, se informa y decide Nicolás.
- **SIN PODER**, detalle: la extensión cambia sólo el fin de V5 y `FECHA_MIN_VEREDICTO` en el evaluador, con un
  re-sello que lo diga, antes de correr la segunda mirada.
- **INVALIDO:** el evaluador no calcula ni muestra ninguna métrica cuando hay un problema de instrumento (crítica 5),
  así que el arreglo se hace sin ver el resultado. Arreglos permitidos, lista cerrada: re-despachar los días faltantes
  del brazo, re-bajar la referencia o NHI con la regla de commits del §3, o esperar que producción tenga la historia.
  Ninguno toca el evaluador. Se corre el mismo criterio **una sola vez más**; si vuelve a dar INVALIDO, decide Nicolás.

## 8. Lo que da el evaluador en los datos de desarrollo (no decide)

`evaluar.py evaluar --fase desarrollo` sobre W2 a W7 (salida `salida_desarrollo.txt`; referencia congelada del A/B,
`ref_db04d930...`; NHI en `09c45707e9a6`; historia de `data/mirova_equivalent` en `3bb44e830`):

- **Etiquetas:** P 58 (57 de Chillán, 1 de Láscar), A 7 (Cordón Caulle 3, Láscar 2, Tupungatito 1, Lastarria 1),
  R 14 (12 de Chillán por la cumbre de MIROVA, 2 de Villarrica por SWIR), O 29, menor 13.
- **R1 y R2 dan lo mismo:** suprimen 6 de 7 A, 0 de 14 R, 1 P, 7 O y 9 menor; p = 1,025e-05 (universo P, A, R y O).
- **Lo informativo:** p estratificado 0,6 (en Cordón Caulle todo lo diurno es A, y el azar dentro del volcán quita lo
  mismo); R0 no quita ningún artefacto (todos los volcanes alertan alguna celda de noche cada mes en una grilla de
  50 km), así que lo que quita R1 sale de la celda, no del volcán; de las 7 A, 1 es desmentible y R1 la quita, y de
  las 6 no desmentibles quita 5.
- **La A que queda** es Lastarria 2026-10-12 17:42 (6,2 MW, 9 celdas, algunas vecinas de las celdas fumarólicas que
  alertan de noche). **La P que se pierde** es Láscar 2026-11-01 19:06: la tabla de MIROVA la alertó con 3,4 MW a
  4,06 km y nosotros la vemos en 7 celdas a 4,1 a 4,4 km sin historia nocturna; el INFORME_RECALCULO la leyó como
  «posible artefacto compartido» (SOSPECHA). Con el criterio sellado, el desarrollo daría NO CUMPLE sólo por esa
  pérdida.
- **Las 7 A coinciden con la lectura en imagen:** son las 6 manchas de 1 MW o más fuera de Chillán (Cordón Caulle 06-13
  y 07-20, Láscar 09-05 y 09-19, Tupungatito 08-30, Lastarria 10-12) más Cordón Caulle VIIRS 750 2026-10-21 18:48, que
  la revisión en imagen no cubrió.

Lo que cambié después de ver el desarrollo, y lo que no:
- Agregué el respaldo (b) por la cumbre de MIROVA. En la primera corrida, las 12 publicaciones de Chillán en erupción
  que MIROVA no tiene quedaban como A (su caja NHI está mal puesta) y el criterio de 2/3 fallaba por calor real mal
  etiquetado.
- Saqué la tercera regla (borde de grilla): en desarrollo no movía ninguna publicación (§2).
- **No** cambié el cero de protegidas perdidas, aunque Láscar 11-01 lo hace fallar en desarrollo: es la pregunta 1.

## 9. El crítico

Un subagente con contexto limpio leyó sólo este documento (con §9 y §10 vacías) y buscó hasta cinco debilidades.
Encontró cinco; las resumo con lo que hice.

**Debilidad 1. P puede contener las manchas solares de MIROVA, y la tolerancia es cero.** P exige sólo que la tabla de
MIROVA haya alertado la cumbre; nada la separa de un artefacto diurno que MIROVA también publique. En desarrollo pasa
(Láscar 11-01, §8), y en Cordón Caulle el radio de 20 km hace cumbre de manchas a 17 km. **Qué hice:** no cambié el
cero, que es lo natural para encender producción y lo que pidió la coordinadora; queda como pregunta 1.

**Debilidad 2. El nulo es débil porque Chillán domina el universo.** Con 57 de 58 P en Chillán, ganarle al azar es casi
separar «volcán en erupción» de «los demás»; y las A se repiten en los mismos lugares, así que no son independientes.
**Qué hice:** O entra al universo del nulo (más difícil de superar); agregué sin voto el p estratificado por volcán y
grilla y la regla trivial R0 (persistencia por volcán); declaré la dependencia de las A como límite del nulo (§5). No
hice votar al estratificado: en un volcán donde todo lo diurno es mancha, el azar dentro del volcán quita lo mismo que
la regla y eso no dice que la regla falle. En desarrollo R0 no quita ninguna A y R1 quita 6, así que lo que quita R1
sale de la celda.

**Debilidad 3. El costo declarado no se ve con estas etiquetas.** Una fuente real que sólo se ve de día, fuera de la caja
de NHI y sin MIROVA, es A, y suprimirla cuenta como acierto. Y el respaldo R (b), cumbre de MIROVA a ±12 h, está
correlacionado con tener historia nocturna, así que «pierde a lo más 1/3 de las R» casi no puede fallar. **Qué hice:**
informo aparte las A desmentibles y no desmentibles (§4) y lo que quita cada regla en cada grupo. El 2/3 sigue sobre
todas las A: sobre las desmentibles solas no habría poder (1 en desarrollo). La correlación de R (b) queda declarada:
el criterio de R protege sobre todo el calor confirmado por SWIR.

**Debilidad 4. O y menor quedaban fuera del criterio y del nulo.** En desarrollo R1 suprime 7 O y 9 menor contra 6 A.
**Qué hice:** O entra al universo del nulo; menor (lo que MIROVA no alertó y no llega a 1 MW) se informa.

**Debilidad 5. Grados de libertad abiertos después de mirar.** INVALIDO sin límite de reintentos y mostrando métricas;
historia y referencia de «un commit fijado al medir». **Qué hice:** con INVALIDO el evaluador no calcula ni muestra
ninguna métrica; un solo reintento, con lista cerrada de arreglos (§7); los commits de historia, referencia y NHI quedan
fijados por regla (§3). Menores: cuentas por ventana (V5 es verano) informadas; la decisión de Nicolás llegó
transmitida y así lo dice la cabecera.

## 10. Preguntas para Nicolás

1. **¿Una protegida de cumbre que la regla pierde cuenta siempre como pérdida (lo sellado), aunque MIROVA haya publicado
   una mancha que no tiene noche?** En desarrollo, la única pérdida (Láscar 2026-11-01 19:06, 3,4 MW a 4,06 km, siete
   celdas sin historia) se leyó como «posible artefacto compartido», y por ella el desarrollo da NO CUMPLE. La
   alternativa sería tolerar una pérdida con revisión obligatoria en imagen. **Recomiendo mantener el cero:** una
   alerta de cumbre de MIROVA es la hoja de respuestas de producción, y una tolerancia decidida después de ver Láscar
   sería ajustada al desarrollo. Si dice que sí a la tolerancia, se re-sella antes de medir.
2. **¿Una sola mirada en marzo de 2027 (lo sellado) o una mirada antes, sólo con V1 a V4, que ya ocurrieron?** V1 a V4
   suman 114 días y se podrían medir apenas corra el brazo; habría que repartir el alfa entre dos miradas y con menos
   datos lo más probable es SIN PODER (en desarrollo, fuera de Chillán, hubo 1 protegida en 115 días). **Recomiendo
   una sola mirada.**
3. **NHI-v1 mira Nevados de Chillán 61 km al sur, junto a Antuco.** Es de otro repo y afecta también al voto de Chillán
   en el pre-registro de la zona A del laboratorio (`experiments/_s194_lab_zona_a/`). ¿Se corrige NHI-v1, y si se
   corrige antes de medir, se re-sella este pre-registro con la caja nueva de Chillán? **Recomiendo sí a las dos:** el
   re-sello antes de medir no mira datos de veredicto.

## 11. Cómo se probó el instrumento antes de medir

- `tests/test_viirs_dia_control_preregistro_s195.py` (en CI): con datos sintéticos de verdad conocida el evaluador da
  CUMPLE, NO CUMPLE (mancha en celdas con calor nocturno; historia en otro lugar), SIN PODER (5 artefactos) e INVALIDO
  (historia incompleta, pasadas de MIROVA sin record, noches del brazo distintas de producción, publicaciones sin
  celdas); la historia es estrictamente previa, de 30 días, por grilla y sólo de noche; una mancha diurna que vuelve
  todos los días a la misma celda se suprime; R1 y R2 se separan cuando la radiante es la ladera; las etiquetas en sus
  bordes (1 MW, radio interno, tabla contra OCR, ±3 días de NHI, caja, ±12 h de MIROVA); el criterio en sus bordes (2/3
  exacto, una protegida perdida, 1/3 de R exacto, p = 15/330 contra alfa 0,04); la caja de NHI de Chillán no usable; y
  cuatro pruebas de sello (valores, hash del evaluador, ventanas de veredicto sin desarrollo, Chillán); además, con
  INVALIDO no sale ninguna métrica, O entra al nulo, el p estratificado, R0 y las A desmentibles.
- `experiments/_s195_viirs_dia_control/mutar.py` (salida `resultado_mutaciones.json`): mutaciones del criterio sobre
  copias del evaluador, corridas sin las pruebas de sello. Cuenta como atrapada sólo si alguna prueba falla **por
  aserción** (resumen de pytest «AssertionError» o «assert»); una prueba que cae por excepción no atrapa (control de
  caída, S152). El control sin mutar pasa entero, y una copia que sólo hace caer (excepción en `con_historia`) da 13
  fallas por caída, 0 por aserción y no cuenta como atrapada. Resultado: 39 de 39 mutaciones atrapadas por aserción.

## 12. Archivos

| archivo | qué es |
|---|---|
| `experiments/_s195_viirs_dia_control/PREREGISTRO.md` | este documento |
| `experiments/_s195_viirs_dia_control/evaluar.py` | evaluador sellado |
| `experiments/_s195_viirs_dia_control/extraer_nhi_cajas.py`, `nhi_cajas.json`, `salida_nhi_cajas.txt` | cajas de NHI-v1 en `09c45707e9a6` y su distancia al volcán |
| `experiments/_s195_viirs_dia_control/bajar_nhi.py` | series NHI a un commit fijo |
| `experiments/_s195_viirs_dia_control/mutar.py`, `resultado_mutaciones.json` | control de mutaciones |
| `experiments/_s195_viirs_dia_control/salida_desarrollo.txt` | el evaluador sobre los datos de desarrollo |
| `tests/test_viirs_dia_control_preregistro_s195.py` | pruebas del evaluador |
