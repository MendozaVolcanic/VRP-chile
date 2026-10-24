# Pre-registro V375-B2 (S162): segunda muestra de noches limpias para resolver V375-B

> Escrito antes de despachar la muestra y antes de ver ninguna de sus pasadas. Lo que cambie después del sello va en una
> adenda fechada al final. Es MEDICIÓN: no adopta nada ni toca `pipeline/`, `data/` ni `frontend/`.
> Estado: **BORRADOR, sin sellar.** Lo pidió la coordinadora S162 con D-48 (2026-10-24: «una segunda muestra de neg_resto
> disjunta de la primera, pre-registrada ANTES de mirar nada nuevo, con la misma regla sellada y el tamaño que la regla
> necesite para decidir»). Falta el verificador con contexto limpio, el sello y el despacho.

## 1. Por qué

V375-B quedó **NO RESUELTO** por su regla sellada (`../resultado_run40116289866/INFORME.md`). En las noches en que
MIROVA miró y no vio nada y producción tampoco publica (neg_resto), el código de MIROVA portado a VIIRS 375 encendió 4
de 389 en el lote S162. Contando todas las noches limpias, su cota superior quedó en 4,10 %, sobre la vara de producción
(3,85 %), aunque la unión con S159 quedaba bajo ella (3,39 %). La pregunta sigue siendo la de B: **¿el port calla en las
noches limpias por lo menos tanto como producción?** Si no, un paquete con el código de MIROVA en 375 encendería puntos
que el operador vería como actividad en noches sin nada.

No se reinterpreta el resultado de B (la coordinadora lo prohibió y el sello también): se agrega muestra.

## 2. Qué se corre

Lo mismo que en V375-B, sin cambiar nada: `../probe_v375.py` con los diez brazos de `../brazos.py` y K re-corrido, sobre
el árbol de `ca034d66e` (`pipeline/` idéntico a 533398f8f, el código que escribió los records del marco). Brazo que
decide: **M14**. Publica = el predicado del tablero con node sobre el record sintético, regla del alertado más cercano.

## 3. Muestra (`seleccion_b2.py` → `seleccion_b2_salida.txt`, `objetivos_v375_b2.json`)

- El mismo marco que V375-B (población congelada de S159, sha256 `c08602de…f8f3`, sin el 12, 13 y 17 a 20 de octubre).
- **600 pasadas neg_resto nuevas**, ninguna de S159 ni de S162 (lo comprueba el script), semilla 163 (la siguiente a la
  162 de S162), asignadas por estrato volcán x cenit para que el conjunto que decide (S162 + B2) quede proporcional al
  tamaño del estrato: pesos entre 3,29 y 4,25, ningún estrato sin pasadas. Tramos: T 187, O1 243, O2 170. 18 partidas,
  informadas aparte. 442 gránulos. sha256 de `objetivos_v375_b2.json`: `d536e1d8…8017`.
- **Por qué 600** (`tamano_b2.py` → `tamano_b2_salida.txt`). Las 133 noches neg_pub del marco ya están todas medidas, así
  que en el conjunto que decide su cota queda fija (31 de 113, 36,5 %) y ocupa 48,6 de las 133,0 publicaciones que permite
  la vara. Para decidir, la cota de neg_resto tiene que bajar de 2,80 % a 2,54 % o menos. Simulado sobre las 389 de S162
  (4 publicadas): con la tasa observada (1,16 % ponderada), 400 nuevas deciden en 91 % de los casos, 600 en 95 % y 800
  en 97 %. Si la tasa real del port fuera 2 %, ningún tamaño de hasta 1.200 llega a la mitad: entonces B quedaría NO
  RESUELTO con más muestra, y eso también es una respuesta (el port no queda claramente bajo K). Las 2.878 noches
  neg_resto que quedan sin medir alcanzan.

## 4. Controles (antes de leer)

Los siete de `../PREREGISTRO_B.md` §4, más la cobertura del lote (pasadas con estado ok contra las 600; las que salgan
«volcán fuera del gránulo» con el mismo gránulo que el record de producción son «no observadas» por la regla de #904 y
salen del denominador; si son más del 10 %, la lectura se informa y no decide). La cobertura del marco contra MIROVA ya
está medida (`../cobertura_marco_salida.txt`, COBERTURA OK) y no cambia: es el mismo marco.

## 5. Regla

### 5.1 Decide (la regla sellada de V375-B, sin cambios)

La de `../PREREGISTRO_B.md` §5, aplicada al **conjunto que decide = S162 + B2** (`evaluar.py --deciden S162 S162b`), con
los pesos recalculados dentro de ese conjunto. neg_pub entra como la muestra de 113 de S162 (no como censo: lo pide la
coordinadora y es la regla de B). SILENCIO ACOTADO BAJO K si la cota superior conservadora de todos los negativos limpios
queda bajo 3,85 %; ENCIENDE DE MAS si la inferior queda sobre 3,85 %; NO RESUELTO si no. La unión S159 + S162 + B2
confirma: si el conjunto que decide y la unión no coinciden, B queda NO RESUELTO (§5.5 de C).

### 5.2 Lo que se declara de antemano: es una segunda mirada

S162 ya se vio, y B2 existe porque S162 no decidió. Mirar dos veces la misma pregunta con un intervalo del 95 % infla la
probabilidad de declarar ACOTADO cuando no lo está: con dos miradas, como mucho al doble del nominal de una cola (de 2,5
a 5 %, cota de Bonferroni). Esto no cambia la regla que decide (la coordinadora pidió la misma regla), pero se informa al
lado la **lectura estricta**: la misma cuenta con z = 2,241 (1,25 % por cola, que con dos miradas vuelve a 2,5 %). Si la
regla dice ACOTADO y la estricta no, el informe lo dice en la primera línea. Ya visto, antes de este pre-registro, al probar
el evaluador sobre lo medido: con S162 solo la estricta da 4,49 % (NO RESUELTO) y con la unión S159 + S162, 3,68 %.

## 6. Costo y despacho

600 pasadas a ~25 s, unas 4,2 h de runner, en 24 trozos de 25 con 8 en paralelo (~45 min de reloj). Artefactos ~70 MB.
Workflow `probe-s162-v375-b2.yml`, rama de disparo `s162-v375-b2-disparo`; humo con 2 pasadas y después el lote, como en
V375-B. Lo despacha la coordinadora.

## 7. Lo que no hace

No mide neg_pub nuevo (no queda en el marco). No cambia la regla de B ni cuenta neg_pub como censo. No mide pasadas
fuera del marco congelado. No decide nada de V375-C (ya terminado): los brazos se corren porque son gratis y se informan.
