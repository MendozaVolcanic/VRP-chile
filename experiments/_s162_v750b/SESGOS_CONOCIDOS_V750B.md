# V750-B: sesgos conocidos e informes aparte, escritos ANTES de leer (2026-11-03)

Pedido por la coordinadora S173 (aviso aprobado por Nicolás, 2026-11-03), antes del despacho y la lectura de V750-B.
No cambia nada de lo sellado: ni el pre-registro, ni las adendas 1 a 3, ni el analizador, ni los controles. Todo lo
de abajo es informativo y no decide el veredicto, que sigue siendo el del lector de la adenda 1 (adenda 2 §8).
Escrito sin haber abierto la referencia de la ventana nueva ni ningún artefacto del run.

## 1. El fondo del oráculo no es el de MATLAB (VPCC750-01, gravedad 3)

**El fenómeno.** Bajo un píxel caliente, MIROVA estima cuánto habría radiado la roca sin la anomalía rellenando el
hueco con una superficie lineal tendida entre los vecinos fríos (`fillmissing2`). En una grilla regular esa superficie
no es única: en cada cuadrado de cuatro celdas hay dos diagonales posibles, y el fondo bajo el píxel depende de cuál se
elige. MATLAB elige siempre la misma (desempate simbólico); scipy elige otra según el orden interno de Qhull.

**Qué usa V750-B.** Los brazos del probe salen del oráculo R2
(`experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py`, importado por `experiments/_s159/n/probe_n.py:52`), no de
`oraculo_ablacion.py`. Comparte el defecto que S173 encontró en ese:
- `_fillmissing2_lineal` (l. 179 a 198) usa `scipy.interpolate.griddata` lineal **sin perturbar**; la vía de
  producción (`pipeline/mirova_v750_codigo.py`, `_triangular_perturbado`, l. 505 y sgts.) usa el Delaunay perturbado
  que iguala a MATLAB R2026b en 166 de 166 escenas (S163 O2).
- Fuera de la envolvente convexa el oráculo rellena con el **vecino más cercano** (l. 193 a 196); MATLAB y la vía dejan
  **NaN**, que el `sum(..., 'omitnan')` del `.m` salta.

**Qué puede tocar y qué no.**
- La detección (máscaras, P1 en su parte de «hay píxel alertado») no depende del fondo del VRP: no cambia.
- La magnitud sí. S173 midió en Cordón Caulle que la vía da 1,3 a 40 % más VRP que el oráculo de V750-C en 11 de 27
  pasadas. En V750-B eso entra a la **razón VRP brazo/MIROVA**, que es descriptiva (§5): se lee como sesgada.
- El veredicto sólo se toca por un camino: el predicado del tablero publica un cúmulo si `pc.vrp_mw > 0`
  (`frontend/index.html`, `isValidDetection`, l. 1595 en `origin/main`). Un cúmulo cuyo VRP del oráculo esté cerca de
  cero o bajo cero puede publicar con una triangulación y no con la otra.
- El control «B0 y B1 = censo S159» exige este mismo oráculo, así que **no se cambia antes de leer**: cambiarlo rompería
  un control sellado.

**Cómo se informa (aparte, sin decidir).** El probe ya guarda para cada brazo con píxeles `vrp_banda`, el mínimo y el
máximo del VRP sobre 20 triangulaciones con las coordenadas perturbadas al azar (`probe_v750b.py`, `oraculo_caja`).
No es la triangulación de MATLAB, pero mide si la elección de diagonal puede mover el signo. En la lectura cuento, por
brazo y por canal, cuántas pasadas que entran a P1 o a E tienen `vrp_banda` con mínimo ≤ 0 < máximo. Si alguna
protegida o algún bloque que decide la prueba de signos cae ahí, lo digo junto al veredicto como «sensible a la
triangulación» y no lo reinterpreto. Si son cero, el veredicto no hereda VPCC750-01; las razones sí.

**El anillo (CPCC750-05) no aplica a V750-B.** El anillo de `inner` a 25 km es la compuerta `t_bg + 3 K` de
`oraculo_ablacion.py` (l. 177). El oráculo R2 no tiene esa compuerta (no hay `t_bg` ni anillo en el archivo; comprobado
con `grep` sobre el árbol de esta rama). Aplica a toda lectura de V750-C hecha con `oraculo_ablacion.py`.

## 2. Cenit, corte bajo y sobre 30°

El pre-registro informa por tramos de 10° de cenit (§5). Agrego al lado, sin que decida, el corte en dos tramos (bajo
30° y 30° o más) para cada brazo y para K: protegidas perdidas, E y razón VRP contra MIROVA. Motivo (S173): K cae con el
ángulo cenital del sensor y las vías no; en Nevados de Chillán la caída de K sale del fondo de anillo.

## 3. Tupungatito

El pre-registro ya informa Tupungatito aparte. Agrego, sin que decida, cuántas alertas de MIROVA de Tupungatito en la
ventana publica K y cuántas publica cada brazo, con el canal que decide y con la tabla sola. S173 midió que K deja sin
publicar 12 de 14; con la vía no está medido. Si el número de alertas de la ventana no es 14, informo el de la ventana
y no el de S173.

## 4. Cordón Caulle con la ROI `def`

S173 midió (verificador limpio: CONFIRMADA EN PARTE) que la vía con la ROI `def` publica 0 de 72 pasadas en Cordón
Caulle y pierde las 8 protegidas, y que B1, B2, B3 o B5 dejan la razón en 0,96 a 1,00. Es el mismo fenómeno que el
control positivo de §7 del pre-registro espera ver con B0 («B0 pierde al menos 1 protegida de Cordón Caulle y B1
publica 3 o más»). No agrega nada que decida; en la lectura lo pongo al lado del control positivo.
