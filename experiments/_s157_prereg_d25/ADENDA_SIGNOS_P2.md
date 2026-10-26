# Quinta adenda al pre-registro de D25 sobre K: P2 se decide con la prueba de signos por bloque noche-volcán

**SELLADA por Nicolás el 2026-10-22 (D-45).** Respuesta textual, registrada por la sesión dueña del loop (S160) en
`tasks/LOOP_OBJETIVOS.md` §5, fila D-45: «Sí a D-45 opción (ii): P2 se decide con la prueba de signos por bloque
noche-volcán (exacta hasta 20 noches), en una quinta adenda sellada, con implementador, candados y verificador antes
del tag; corrige también V42-21. Hazlo en una sesión nueva tras /cierre.» Redactada en S161 (2026-10-22, desde las
19:01 UTC según el servidor) **antes** de leer el veredicto de V1, V2a y V2b, que siguen sin leer, y antes de abrir el
brazo de sensibilidad del 17 al 19 de octubre (D-35, run 39756261926). Todo lo que esta adenda no toca rige como está
en `PREREGISTRO.md`, `ADENDA_CALIBRACION.md` (D-27), `ADENDA_PLACEBO.md` (D-28, D-30, D-32), `ADENDA_GEMELO.md`
(D-34), la exclusión de días de D-29, `ADENDA_CALIBRACION_P2.md` (D-42), `NOTA_ESTRATO_203.md` y `NOTA_D44.md` (D-44).

## 1. Qué falla

El verificador de D-42, vuelta 3 (`experiments/_s159/instrumentos/verificador_d42/vuelta3/INFORME.md`, V42-20,
commit `bcfdc7c76`), enumeró los 2^B repartos de signo por noche con la función real y mostró que la regla de D-34 (el
intervalo bootstrap al 95 % por bloques) deja el neto entero sobre 0 no sólo cuando todas las noches van del mismo
lado, sino también con 6 contra 1: con **7 noches su tasa exacta de falsos es 6,25 % por cola**. La calibración de
D-42 lo ve y deja P2 INDECIDIBLE, así que **7 noches discordantes todas del mismo lado, el efecto más claro que P2
puede recibir, quedan siempre INDECIDIBLE**, aunque la prueba exacta de signos por noche dé p = 0,78 %. Y con 1.000
sorteos, cerca del 5 % decide la semilla 161 (con tasa verdadera 4,59 %, «11 en 10 noches», la calibración falla el 42
% de las veces). Ya pasó en los placebos de D-44: INDECIDIBLE en 16 de 20 celdas de V1 (c) 25 % con 7 noches.

No es un costo del sorteo discreto: es el intervalo de D-34 con pocos bloques. Subir los sorteos (opción iv) o
enumerar la calibración (opción iii) quitan el ruido de la semilla pero no el 6,25 % de B = 7.

## 2. La regla nueva de P2

Reemplaza como regla que **decide** a `ADENDA_GEMELO.md` §5.3 a §5.6 y a la calibración de `ADENDA_CALIBRACION_P2.md`
§2. Por sensor, como hoy, con las mismas pasadas y los mismos aportes.

1. **La unidad y el signo no cambian** (`ADENDA_GEMELO.md` §5.1 y §5.2): pasadas en que K y D difieren en la suma de
   P2; cada una aporta +1 si el error es sólo de D y -1 si es sólo de K; **positivo es malo para D**. El neto
   observado es la suma de los aportes.
2. **El bloque no cambia**: noche-volcán, con la misma clave que hoy (volcán y fecha UTC de la pasada, la que usa
   `contribuciones_p2`). La **suma del bloque** es la suma de los aportes de sus pasadas: un entero, que puede ser 0
   (una noche con un error sólo de D y otro sólo de K). B es el número de bloques con al menos una pasada discordante,
   incluidos los de suma 0.
3. **El nulo**: D y K son intercambiables dentro de una noche, así que bajo el nulo cada bloque entero cambia de signo
   con probabilidad 1/2, independiente de los demás. El estadístico bajo el nulo es la suma de las sumas de bloque,
   cada una con su signo sorteado. POR QUÉ por bloque: cambiar los brazos de una noche invierte todas sus pasadas a la
   vez; es el mismo nulo de D-42 §2.1 y de `calibrar_simetrico` para M. Los bloques de suma 0 no cambian el
   estadístico: incluirlos o no da el mismo valor-p.
4. **Una cola por dirección.** Valor-p de GANA = fracción de repartos con suma **menor o igual** que el neto
   observado; valor-p de PIERDE = fracción con suma **mayor o igual**. Lectura de esta adenda, porque el texto de D-45
   no nombra las colas: **5 % en cada cola por separado**, igual que el tope de D-42 §2.4 («cada cola por separado»)
   y las colas de M en D-27. Es además la única lectura en que el SIN SUSTRATO de D-45 («4 noches o menos») queda en
   la frontera: a una cola, 5 noches del mismo lado dan p = 1/32 = 3,1 % y deciden; con 4 o menos el p mínimo es
   1/16 = 6,25 % y no pueden. A dos colas, 5 noches tampoco podrían decidir y el corte natural habría sido 5. El
   valor-p a dos colas se informa al lado y no decide.
5. **Cómo se calcula el valor-p.**
   - **Con B de 20 o menos, exacto**: se enumeran los 2^B repartos. El valor-p es una fracción k / 2^B y la
     comparación con el 5 % se hace en enteros (`20 * k <= 2**B`), sin coma flotante.
   - **Con B de 21 o más, 10.000 sorteos** de signos por bloque con semilla fija **162** (`SEMILLA + 5`, la siguiente
     libre después de la 161 de D-42), y valor-p = (1 + m) / (1 + 10.000), donde m es el número de sorteos con suma
     al menos tan extrema como la observada en la cola que se prueba. POR QUÉ el +1: cuenta el reparto observado, que
     es uno de los posibles; sin él, un valor-p por sorteos puede dar 0 y la prueba rechaza algo más que el 5 %
     nominal. La comparación se hace en enteros (`20 * (1 + m) <= 10001`).
6. **El veredicto**:
   - neto < 0 y valor-p de GANA de 5 % o menos: **GANA**;
   - neto > 0 y valor-p de PIERDE de 5 % o menos: **PIERDE**;
   - neto > 0 sin llegar: **BLOQUEA** (bloquea CUMPLE y deja la ventana en DECIDE NICOLAS, como manda
     `ADENDA_GEMELO.md` §5.5);
   - neto de 0 o menos sin llegar: **EMPATE**.
7. **SIN SUSTRATO**: con **B de 4 o menos** (D-44 punto 2 y D-45), P2 da SIN SUSTRATO y no decide ni bloquea.
   Reemplaza el mínimo de D-34 §5.6 (menos de 5 pasadas o menos de 3 noches): con 5 noches hay al menos 5 pasadas.
   Consecuencia que se acepta a sabiendas: con 4 noches o menos en contra de D, P2 tampoco bloquea; lo que protege
   entonces es P1 (el veto de las protegidas) y M. Antes (D-42) esas mismas noches dejaban P2 INDECIDIBLE y con él la
   ventana.
8. **Con los controles generales caídos**, P2 sigue dando INDECIDIBLE, como hoy.
9. **`global_ventana` no cambia** (D-44 punto 1: un PIERDE se mira antes que un INDECIDIBLE). Un P2 INDECIDIBLE ya
   sólo puede salir de controles caídos.

## 3. Lo que deja de decidir, y se informa igual

- El intervalo bootstrap de D-34 (§5.3 y §5.4) y la calibración de D-42 **dejan de hacer falta para P2**: la prueba
  de signos por bloque está calibrada por construcción (es una prueba de permutación exacta sobre el mismo nulo que la
  calibración simulaba). Se siguen calculando y se informan, sin decidir, como pide `ADENDA_GEMELO.md` §5.8 para las
  reglas retiradas: el resultado de D-34 sin calibrar con su intervalo, y el de D-42 (calibrada o no, falsos GANA,
  PIERDE y BLOQUEA, sorteos y semilla 161). Así se ve si el cambio de regla cambia el veredicto.
- Las reglas (a) del gemelo y (b) de D-33 se siguen informando como hoy.

## 4. Lo que se informa en el detalle de P2 del JSON

Siempre que P2 se calcule: neto; B; bloques de suma no nula; las sumas de bloque (multiconjunto); valor-p de GANA, de
PIERDE y a dos colas; método («exacto» o «sorteos»); el p mínimo alcanzable (1 / 2^B con el método exacto); semilla y
número de sorteos cuando se usaron, o None; la regla que decidió (esta adenda, D-45); y lo de §3. La lista de pasadas
discordantes (`ADENDA_GEMELO.md` §5.7) no cambia.

## 5. Los candados (antes del tag de lectura)

Cada mutación cuenta como atrapada sólo si alguna prueba falla por aserción y ninguna por otra excepción (S156),
leyendo el tipo de falla del XML de JUnit, con una copia sin mutar como control. Las pruebas nuevas se escriben antes
del código y se guardan rojas en su versión final (V29-02), cada una fallando por aserción contra el evaluador de
`bcfdc7c76`.

Mutaciones que tienen que quedar atrapadas:

1. dos colas en vez de una (el valor-p duplicado);
2. tope al 10 % en vez del 5 %;
3. cola de GANA calculada con «mayor o igual» (dirección cambiada);
4. SIN SUSTRATO con B de 3 o menos, y con B de 5 o menos (las dos);
5. B contado sin los bloques de suma 0;
6. signo sorteado por pasada en vez de por bloque;
7. el corte del método exacto en otro valor que 20 (por ejemplo 12): la prueba exige el método declarado para B = 20
   y B = 21;
8. semilla de los sorteos distinta de 162, y número de sorteos distinto de 10.000;
9. valor-p por sorteos sin el +1;
10. BLOQUEA con neto de 0 (en vez de EMPATE);
11. la calibración de D-42 todavía decide (un fallo de calibración que deja INDECIDIBLE): la prueba usa 7 noches
    todas del mismo lado, que tiene que dar PIERDE o GANA con p = 1/128;
12. el resultado de D-34 o de D-42 que deja de informarse.

Una mutación equivalente que no se exige: «5 % o menos» contra «menos del 5 %». Con el método exacto el valor-p es
k / 2^B y nunca vale 1/20 justo; con sorteos es (1 + m) / 10.001 y tampoco. Ninguna prueba puede distinguirlas; se
declara así en el informe del implementador en vez de inventar un caso.

Las baterías de candados que ya existen (V34-03, V29-01, D-42 y el estrato 203) se vuelven a correr. Las de D-42 que
sólo tocaban la decisión de P2 se re-apuntan a los campos que ahora informan, o se retiran con su razón escrita, una
por una.

## 6. Los placebos (V42-21 y V42-22)

- **(c) simétrico, sorteando por noche** (V42-21): se eligen noches-volcán tocadas y todas las pasadas tocadas de una
  misma noche reciben el mismo signo (todas se apagan o todas se encienden), de modo que el nulo del placebo sea el
  mismo de §2.3. Sobre los mismos brazos de producción y las mismas fracciones que en D-44.
- **El número de semillas se fija aquí, antes de correr** (V42-22): **40 semillas por punto** en (c), iguales en
  todos los puntos, sin ampliar después de mirar. (a) y (b), con las mismas semillas que en D-44.
- **(a) y (b) se vuelven a decidir con la regla nueva.** Si los JSONL de D-44 guardan los aportes y los bloques de
  cada celda, se re-deciden desde ahí, y se demuestra en una muestra que re-decidir da lo mismo que re-correr; si no
  los guardan, se re-corren.
- **Lo que tiene que salir**: (a) GANA, (b) PIERDE, (c) falsos de 5 % o menos por cola, con su intervalo de Wilson.
  Si (a) o (b) fallan en la dirección o (c) supera el 5 % en una cola, no hay tag: se devuelve a Nicolás.

## 7. Lo que se mide antes del tag, sin datos reales

Con datos sintéticos y la función real, declarado en el informe del implementador:

- la tasa exacta de falsos por cola para B de 5 a 20 con bloques de suma ±1 (tiene que quedar en 5 % o menos por
  construcción; si no, el código está mal);
- los escenarios nulos y de efecto de V34-01 y de `calib_p2/cobertura_p2_calibrada.py`, con la regla nueva al lado de
  la de D-42;
- el caso de V42-20: 7 noches todas del mismo lado decide, y 6 contra 1 con 7 noches no.

Una regla que nunca decide también es un defecto: si el poder cae a casi 0 en el efecto grande, se dice antes del tag.

## 8. Lo que esta adenda no toca

- La unidad, el signo, el bloque, la lista de discordantes y los informes de `ADENDA_GEMELO.md` §5.
- P1, P1b, M y su comparador, P4 y P5, el estrato 203 y la exclusión de días de D-29.
- El brazo de sensibilidad del 17 al 19 de octubre (D-35) se evalúa aparte con la misma regla y no entra al veredicto.
- Esta adenda no lee ni toca ningún dato del A/B: el veredicto de D25 se lee recién después del verificador limpio y
  del tag de lectura.
