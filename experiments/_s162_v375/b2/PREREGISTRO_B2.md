# Pre-registro V375-B2 (S162): segunda muestra de noches limpias para resolver V375-B

> Escrito antes de despachar la muestra y antes de ver ninguna de sus pasadas. Lo que cambie después del sello va en una
> adenda fechada al final. Es MEDICIÓN: no adopta nada ni toca `pipeline/`, `data/` ni `frontend/`.
> Estado: **BORRADOR v2, sin sellar.** Lo pidió la coordinadora S162 con D-48 (2026-10-24: «una segunda muestra de neg_resto
> disjunta de la primera, pre-registrada ANTES de mirar nada nuevo, con la misma regla sellada y el tamaño que la regla
> necesite para decidir»). El borrador v1 (commit `987e4f814`) pasó por un verificador limpio (`verificador/INFORME.md`);
> esta versión aplica sus correcciones (§8). Falta un segundo verificador, el sello y el despacho.

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
  2,83, ningún estrato sin pasadas. Tramos: T 346, O1 517, O2 337. 41 partidas, informadas aparte. 658 gránulos. sha256
  de `objetivos_v375_b2.json`: `6328988b…019a`. Quedan 1.678 neg_resto sin medir en el marco.
- **Por qué 1.200 y por qué B2 sola** (`tamano_b2.py` → `tamano_b2_salida.txt`). Las 133 noches neg_pub del marco ya
  están todas medidas, así que la cota de neg_pub queda fija en la de S162 (31 de 113, 36,5 %) y ocupa 48,6 de las 133,0
  publicaciones que permite la vara: para decidir, la cota de neg_resto tiene que quedar en 2,54 % o menos. Decidiendo
  **B2 sola** en neg_resto, con la tasa observada (1,16 % ponderada): 600 nuevas deciden en 59 % de los casos, 1.000 en
  88 %, **1.200 en 93 %**, 1.500 en 98 %. En la frontera (tasa real 2,54 %) la regla declara SILENCIO ACOTADO en 1 a 3 % de
  los casos, el nominal. El borrador v1 (S162 + 600) decidía más barato pero, por reutilizar lo ya visto, declaraba ACOTADO
  en la frontera entre 11 y 20 % de los casos (misma salida, segunda tabla): por eso se descartó. Si la tasa real del port
  fuera 1,7 % o más, ni 1.200 alcanzan a la mitad: entonces B queda NO RESUELTO con más muestra, y eso también es una
  respuesta (el port no queda claramente bajo K).
- **Supuesto que se declara** (verificador v1, F3, SOSPECHA): la simulación supone una tasa pareja. Los 4 eventos de S162
  no lo son (2 de Lastarria, en 2 de 12 pasadas de ese volcán). Si la tasa de un volcán fuera mucho mayor, la probabilidad
  de decidir baja. La asignación proporcional mantiene el peso de cada volcán igual que en el marco, que es lo que la
  regla necesita; la potencia no se garantiza.

## 4. Controles (antes de leer)

Los siete de `../PREREGISTRO_B.md` §4, más:
- **Cobertura por lote** (verificador v1, F4): el umbral de 10 % de SIN DATO se aplica también al lote B2 por separado; si
  B2 lo pasa, la lectura de B2 se informa y no decide. Las pasadas «volcán fuera del gránulo» con el mismo gránulo que el
  record de producción son «no observadas» por la regla de #904: salen del denominador y su estrato se re-pondera.
- **Lote que decide vacío** (verificador v1, F5): si un lote de `--deciden` no tiene ninguna pasada ok, el evaluador
  declara INVALIDO POR INSTRUMENTO.
- La cobertura del marco contra MIROVA ya está medida (`../cobertura_marco_salida.txt`, COBERTURA OK): es el mismo marco.

## 5. Regla

### 5.1 Decide

La regla sellada de V375-B (`../PREREGISTRO_B.md` §5), sin cambios en la cuenta, sobre el **conjunto que decide = neg_resto
de B2 + neg_pub de S162** (`evaluar.py --deciden S162b --neg-pub-de S162`), con los pesos recalculados dentro de ese
conjunto. neg_pub entra como la muestra de 113 de S162 (no como censo: lo pide la coordinadora y es la regla de B) porque
no queda ninguna sin medir. SILENCIO ACOTADO BAJO K si la cota superior conservadora de todos los negativos limpios queda
bajo 3,85 %; ENCIENDE DE MAS si la inferior queda sobre 3,85 %; NO RESUELTO si no.

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
de esta corrida (las secciones 4 y 4b del evaluador) **no se lee** (verificador v1, F10), porque B2 sólo trae neg_resto.

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
