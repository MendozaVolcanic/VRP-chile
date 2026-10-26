# Pre-registro V375-B2 (S162): segunda muestra de noches limpias para resolver V375-B

> Escrito antes de despachar la muestra y antes de ver ninguna de sus pasadas. Lo que cambie después del sello va en una
> adenda fechada al final. Es MEDICIÓN: no adopta nada ni toca `pipeline/`, `data/` ni `frontend/`.
> Estado: **BORRADOR v3, sin sellar.** Lo pidió la coordinadora S162 con D-48 (2026-10-24: «una segunda muestra de neg_resto
> disjunta de la primera, pre-registrada ANTES de mirar nada nuevo, con la misma regla sellada y el tamaño que la regla
> necesite para decidir»). El borrador v1 (commit `987e4f814`) pasó por un verificador limpio (`verificador/INFORME.md`);
> el v2 (commit `7ff23cc3a`) pasó por un segundo verificador (`verificador_v2/INFORME.md`); esta versión aplica las
> correcciones de los dos (§8 y §9). Falta el sello y el despacho.

## 1. Por qué

V375-B quedó **NO RESUELTO** por su regla sellada (`../resultado_run40116289866/INFORME.md`). En las noches en que
MIROVA miró y no vio nada y producción tampoco publica (neg_resto), el código de MIROVA portado a VIIRS 375 encendió 4
de 389 en el lote S162. Contando todas las noches limpias, la cota superior quedó en 4,10 %, sobre la vara de producción
(3,85 %), aunque la unión con S159 quedaba bajo ella (3,39 %). La pregunta sigue siendo la de B: **¿el port calla en las
noches limpias por lo menos tanto como producción?** Si no, un paquete con el código de MIROVA en 375 encendería puntos
que el operador vería como actividad en noches sin nada.

No se reinterpreta el resultado de B (la coordinadora lo prohibió y el sello también): se agrega muestra nueva, y la
muestra nueva es la que decide.

## 2. Qué se corre

Lo mismo que en V375-B, sin cambiar nada: `../probe_v375.py` con los diez brazos de `../brazos.py` y K re-corrido, sobre
el árbol de `ca034d66e` (`pipeline/` idéntico a 533398f8f, el código que escribió los records del marco). Brazo que
decide: **M14**. Publica = el predicado del tablero con node sobre el record sintético, regla del alertado más cercano.

## 3. Muestra (`seleccion_b2.py` → `seleccion_b2_salida.txt`, `objetivos_v375_b2.json`)

- El mismo marco que V375-B (población congelada de S159, sha256 `c08602de…f8f3`, sin el 12, 13 y 17 a 20 de octubre).
- **1.200 pasadas neg_resto nuevas**, ninguna de S159 ni de S162 (lo comprueba el script), semilla 163 (la siguiente a
  la 162 de S162), asignadas por estrato volcán x cenit proporcional al tamaño del estrato en el marco: pesos entre 2,72 y
  2,83, ningún estrato sin pasadas. Tramos: T 346, O1 517, O2 337. 41 partidas, informadas aparte. Quedan 1.678
  neg_resto sin medir en el marco. Al archivo se agregan las 20 pasadas del control de vida (§4), sin tocar la muestra:
  1.220 entradas, 667 gránulos, sha256 de `objetivos_v375_b2.json` `f3285f3a…b419` (ids de la muestra 3000 a 4199, del control 5000 a 5019).
- **Por qué 1.200 y por qué B2 sola** (`tamano_b2.py` → `tamano_b2_salida.txt`). Las 133 noches neg_pub del marco ya
  están todas medidas, así que la cota de neg_pub queda fija en la de S162 (31 de 113, 36,5 %) y ocupa 48,6 de las 133,0
  publicaciones que permite la vara: para decidir, la cota de neg_resto tiene que quedar en 2,54 % o menos. Decidiendo
  **B2 sola** en neg_resto, con la tasa observada (1,16 % ponderada): 600 nuevas deciden en 59 % de los casos, 1.000 en
  88 %, **1.200 en 93 %**, 1.500 en 98 %. Ese 93 % es condicional a la tasa puntual: integrando la incertidumbre de 4 de
  389, la probabilidad de decidir baja a 0,74 a 0,80 (verificador v2). En la frontera (tasa real 2,54 %) la regla declara
  SILENCIO ACOTADO en 1 a 3 % de los casos, el nominal. El borrador v1 (S162 + 600) se descartó por reutilizar lo ya
  visto: condicionado a las 4 de 389 ya observadas, declaraba ACOTADO en la frontera entre 11 y 20 % de los casos (misma
  salida, segunda tabla); sin condicionar, cerca de 2 % (verificador v2, H5). La razón de fondo es la de C §5.5. Si la tasa real del port
  fuera 1,7 % o más, ni 1.200 alcanzan a la mitad: entonces B queda NO RESUELTO con más muestra, y eso también es una
  respuesta (el port no queda claramente bajo K).
- **Supuesto que se declara** (verificador v1, F3, SOSPECHA): la simulación supone una tasa pareja. Los 4 eventos de S162
  no lo son (2 de Lastarria, en 2 de 12 pasadas de ese volcán). Si la tasa de un volcán fuera mucho mayor, la probabilidad
  de decidir baja. La asignación proporcional mantiene el peso de cada volcán igual que en el marco, que es lo que la
  regla necesita; la potencia no se garantiza.

## 4. Controles (antes de leer)

Los siete de `../PREREGISTRO_B.md` §4, más:
- **Cobertura por lote** (verificador v1, F4): el umbral de 10 % de SIN DATO se aplica también al lote B2 por separado; si
  B2 lo pasa, el veredicto de B es NO DECIDE (`evaluar.py` lo escribe en la línea del veredicto, verificador v2). Las pasadas «volcán fuera del gránulo» con el mismo gránulo que el
  record de producción son «no observadas» por la regla de #904: salen del denominador y su estrato se re-pondera.
- **Lote que decide vacío** (verificador v1, F5): si un lote de `--deciden` no tiene ninguna pasada ok, el evaluador
  declara INVALIDO POR INSTRUMENTO.
- **Control de vida en el mismo run** (verificador v2, hallazgo 3): B2 sólo trae neg_resto, así que los controles
  positivos de B (que leen S159 y S162) no prueban que el port esté vivo en ESTE run; un port muerto o una dependencia
  rota darían 0 de 1.200 y «calla». Por eso el run re-mide 20 pasadas ya medidas en S162 (lote CTL, fuera de todo
  denominador): 12 protegidas de Láscar y Chillán con píxeles (sorteadas, semilla 164), las 4 neg_resto que M14
  publicó y 4 neg_resto en 0. M14 tiene que dar los mismos npix y VRP que en S162 (a 1e-6 MW) en todas las que salgan
  ok, al menos 18 de 20 tienen que salir ok y alguna tiene que tener píxeles; si no, INVALIDO POR INSTRUMENTO
  (`evaluar.py`, control 2.2b). Las dependencias de Python del workflow no están fijadas a versión (igual que en B):
  este control es el que ve si una cambió algo.
- La cobertura del marco contra MIROVA ya está medida (`../cobertura_marco_salida.txt`, COBERTURA OK): es el mismo marco.

## 5. Regla

### 5.1 Decide

La regla sellada de V375-B (`../PREREGISTRO_B.md` §5), sin cambios en la cuenta, sobre el **conjunto que decide = neg_resto
de B2 + neg_pub de S162** (`evaluar.py --deciden S162b --neg-pub-de S162`), con los pesos recalculados dentro de ese
conjunto. neg_pub entra como la muestra de 113 de S162 (no como censo: lo pide la coordinadora y es la regla de B) porque
no queda ninguna sin medir. SILENCIO ACOTADO BAJO K si la cota superior conservadora de todos los negativos limpios queda
bajo 3,85 %; ENCIENDE DE MAS si la inferior queda sobre 3,85 %; NO RESUELTO si no. **El veredicto es la línea
«VEREDICTO B» de la sección 4b de `evaluar_salida.txt`**; la sección 3 (B sobre todas las pasadas) se informa y no
decide (verificador v2, hallazgo 5).

Es fiel a la lógica sellada de C §5.5 (decide lo no visto) en la parte que puede serlo: los datos de neg_resto que deciden
son todos nuevos. La parte de neg_pub ya se vio y no tiene reemplazo; se declara.

### 5.2 Confirma

La unión S159 + S162 + B2 confirma. Si el conjunto que decide y la unión no coinciden, B queda NO RESUELTO (§5.5 de C).
La lectura estricta de `evaluar.py` (z = 2,241) se sigue imprimiendo, pero con B2 sola decidiendo no hace falta corregir
por una segunda mirada sobre neg_resto: se informa y no se interpreta.

## 6. Costo y despacho

1.200 pasadas a ~25 s, unas 8,3 h de runner, en 48 trozos de 25 con 8 en paralelo (~90 min de reloj). Artefactos ~140 MB,
a `C:\vrp-trabajo\temporales\s162_v375\`. Workflow `probe-s162-v375-b2.yml`, rama de disparo `s162-v375-b2-disparo`;
humo con 2 pasadas y después el lote, como en V375-B. Lo despacha la coordinadora.

## 7. Lo que no hace

No mide neg_pub nuevo (no queda en el marco). No cambia la regla de B ni cuenta neg_pub como censo. No mide pasadas fuera
del marco congelado. No decide nada de V375-C (terminado): los brazos se corren porque son gratis, y el bloque de V375-C
de esta corrida **no se lee** (verificador v1, F10), porque B2 sólo trae neg_resto: de las secciones 4 y 4b del evaluador
sólo se leen la decisión B, su acuerdo con la unión y la línea «VEREDICTO B».

## 8. Revisión tras el verificador del borrador v1 (2026-10-24, `verificador/INFORME.md`, Sonnet)

| hallazgo | gravedad | cambio |
|---|---|---|
| F1: el conjunto que decide reutilizaba S162, ya visto; la lógica sellada era que decida lo no visto | 3 | decide B2 sola en neg_resto; tamaño de 600 a 1.200 para conservar la potencia (93 %); el v1 declaraba ACOTADO en la frontera entre 11 y 20 % de las veces |
| F2: la «segunda mirada» estaba sobredeclarada (Bonferroni da 5 %, la simulación ~1,2 %) y la lectura estricta no vuelve a 2,5 % | 2 | ya no aplica: con B2 sola no hay segunda mirada sobre neg_resto; la estricta sólo se informa |
| F3: la potencia supone tasa pareja; 2 de los 4 eventos son de Lastarria | 2 | declarado en §3 como SOSPECHA |
| F4: la cobertura miraba los tres lotes juntos (B2 podía perder 15 % sin aviso) | 2 | umbral también por lote (`evaluar.py`) |
| F5: `--deciden` con un lote sin pasadas imprimía DECIDE sin aviso | 2 | INVALIDO POR INSTRUMENTO (`evaluar.py`) |
| F6: «con 2 % ningún tamaño de hasta 1.200 llega a la mitad» era falso en 1.200 (0,55) | 1 | reescrito con la tabla nueva |
| F7 a F9: pesos al quitar las no observadas, tres miradas formales, etiquetas | 1 | los pesos se re-ponderan como en B (se informa); el resto, cosmético |
| F10: el bloque de V375-C de la corrida nueva puede cambiar y no se dice que no se lee | 1 | §7 |

## 9. Revisión tras el segundo verificador (2026-10-24, `verificador_v2/INFORME.md`, Sonnet, sobre el v2 `7ff23cc3a`)

Confirmó la muestra (disjunta, del marco, sha reproducible), la cuenta de «decide B2 sola» (con 1.200 pasadas fabricadas,
su cuenta a mano coincide a 15 cifras), el tamaño en la frontera y el workflow, y que los hallazgos del primer verificador
quedaron atendidos.

| hallazgo | gravedad | cambio |
|---|---|---|
| 3: ningún control prueba que el port esté vivo en el run de B2; un port muerto da «calla» con el instrumento en OK (reproducido) | 3 | control de vida de 20 pasadas re-medidas de S162 (§4) |
| 4: el 93 % es condicional a la tasa puntual (predictiva 0,74 a 0,80); la cobertura por lote sólo avisaba | 2 | declarado en §3; la cobertura del lote que decide da NO DECIDE |
| 5: tres lecturas de B en la salida, 4b rotulaba «S162» y §7 decía que 4 y 4b no se leen | 2 | la línea «VEREDICTO B» es la que decide; rótulo del conjunto que decide; §7 corregido |
| H5: el 11 a 20 % del v1 era condicional a lo ya visto (sin condicionar, ~2 %) | 1 | §3 |
| H6: dependencia temporal y por noche que la binomial no modela (SOSPECHA) | 1 | se declara: la potencia es aproximada |
| H7: el reparto por trozos descarga 1.220 gránulos contra 667 únicos | 1 | se acepta (el runner borra cada gránulo después de usarlo); costo, no sesgo |

## Sello (2026-10-24)

**SELLADO** por la coordinadora S162 con la autorización vigente de Nicolás, **D-48 (2026-10-24: «sobre las decisiones mías
haz lo que tú recomiendes»)**: tamaño de 1.200 aprobado y sello condicionado a dos cosas que se cumplieron. (1) Una
re-verificación con contexto limpio y otro modelo (Fable) del delta v2→v3 que rompió el port a mano:
`verificador_v3/INFORME.md`, **CONFORME**; el control de vida atrapa por sí solo, sin el recálculo, un port que no detecta
nada, uno que detecta todo, uno con la magnitud doblada, uno muerto sólo en el control, una caída de 3 de 20 y el control
ausente, y con un lote sano y completo el veredicto sale SILENCIO ACOTADO (el control no bloquea siempre). (2) El humo
(run 40128648709): control 5000 reproducido exacto, muestra 3000 en 0 píxeles. Revocable por Nicolás. Texto sellado: el
del tag `s162-v375-b2-listo` (commit `ae65eaaaf`); lo que cambie va abajo como adenda.

## Adenda 1 (2026-10-24, tras el verificador v3 y antes del lote)

- **H1 (gravedad 3)**: el control de vida existía sólo si el archivo de objetivos traía el lote CTL. `evaluar.py` ahora
  declara INVALIDO POR INSTRUMENTO si decide un lote nuevo y no hay control (`sin_control_vida`). El archivo del disparo
  sí lo trae: el blob de `objetivos_v375_b2.json` es el mismo en `s162-v375-b2-listo` y en `s162-v375-b2-disparo-lote`
  (`1999237b…`); su sha256 es `a7dd6b0d…e955` con fin de línea LF (como lo lee el runner) y `f3285f3a…b419` con CRLF (como
  lo escribe Python en Windows, el que cita §3). Es el mismo contenido.
- **H2 (gravedad 2)**: el control CTL sí entra a los controles 2.1 (recálculo) y 2.2 (K re-corrido), que cuentan pares por
  pasada; «fuera de todo denominador» vale para las lecturas que deciden y la cobertura. No mueve veredictos.
- **H3 (gravedad 1)**: el NO DECIDE por cobertura mira los lotes de `--deciden`, no el lote del que sale neg_pub (S162:
  113 de 113 ok). Se declara.
- **H4 (SOSPECHA)**: 20 pasadas de control no ven una rotura limitada a una plataforma o tramo ausente de ellas. Límite de
  diseño.
- **H5 (SOSPECHA, error conservador)**: si NASA reprocesó un gránulo del control, el control puede dar INVALIDO sin port
  roto; antes de concluir «port roto» se leen la lista `distintas` y los nombres de archivo.
- Ninguno de estos cambios toca el runner ni los commits de disparo.
