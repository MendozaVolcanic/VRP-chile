# Verificador v3 (tercera vuelta, sólo el delta v2 a v3) del pre-registro V750-B

## Encabezado

- Hora del servidor (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`): al empezar **Sat, 24 Oct 2026
  17:36:59 GMT**; al cerrar **Sat, 24 Oct 2026 17:50:42 GMT**.
- Worktree: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4`, rama
  `claude/s162-viirs750-f63ef4`, HEAD `9b851942f` (un commit después de `439968ec1`, que toca sólo
  `tasks/LOOP_VIIRS750.md`: `git diff --stat 439968ec1 HEAD` da ese único archivo). El árbol de trabajo es idéntico al
  commit en `experiments/_s162_v750b/` (`git diff --stat HEAD -- experiments/_s162_v750b/` vacío; `git status` sólo
  muestra `?? experiments/_s162_v750b/verificador_v3/`). `origin/main` sin fetch (no hice ningún git que escriba):
  `710ea22ca`, 2026-10-24 17:26:53 UTC.
- Delta auditado: `git diff 607062ba7 439968ec1 -- experiments/_s162_v750b/` (20 archivos, +1545 / −42). Los archivos de
  `verificador_v2/` se leyeron DESPUÉS de escribir la lista de caminos de abajo.
- Modelo y esfuerzo que declaro: Claude Fable 5.1, esfuerzo medio, contexto limpio (sin la sesión del autor ni la de
  la segunda vuelta).
- Qué NO miré: el probe (`probe_v750b.py`, `probe-s162-v750b.yml`); el generador de objetivos más allá de las 3 líneas
  del delta y de cómo la población (`experiments/_s159/n/01_poblacion.py:111-118` de `origin/main`) define
  `protegida`, `alerta_tabla` y `decide`; el oráculo (`mirova_v750_r2.py`); `banco_paridad.correr_node`; las secciones
  §1 a §5, §8 y §10 del pre-registro; la cobertura contra la referencia (fase 0, #904); las grillas de N en `D:` y el
  censo S159 (el control real del censo lo corrió la segunda vuelta, no yo). Nada del run real existe todavía: todo lo
  que medí es sobre poblaciones sintéticas en el formato del probe.
- Ningún archivo del repositorio fue modificado. Lo escrito vive sólo en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4\experiments\_s162_v750b\verificador_v3\`
  (`mutar_v3.py` y su salida `mutar_v3_salida.txt`, `escenarios_v3.py` y su salida `escenarios_v3_salida.txt`,
  `bateria_base_salida.txt`, este informe) y en el scratchpad de la sesión
  (`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-f63ef4\b455f415-8036-418a-afd4-61523e9603ae\scratchpad\`:
  árboles `arbol_v3` (limpio) y `arbol_esc`, carpetas `bat_v3`, `mut_A`, `mut_B`, `mut_C`, `esc`). Discos al cerrar:
  C: 41 GB libres, D: 9,6 GB (no bajaron de 3 GB).

## sha256 de los archivos del delta (blob del commit `439968ec1`, finales de línea LF)

El árbol de trabajo tiene CRLF (`file` lo confirma; git convierte al sacar), así que el sha256 del archivo en disco NO
coincide con el del blob; normalizando con `tr -d '\r'` coinciden los cuatro que lo necesitan. Los sha de abajo son los
del blob, que es lo que GitHub Actions baja.

| archivo | sha256 (blob `439968ec1`) |
|---|---|
| `experiments/_s162_v750b/PREREGISTRO_V750B.md` | `8111f8eb6c2c87e92b46f12ee6ff848053dd9d8e0b7b048240e438e8175c7efd` |
| `experiments/_s162_v750b/analizar_v750b.py` | `e01ad843b80120bed34642632e98a40d416eb0947e82c717295733e8dfa9f621` |
| `experiments/_s162_v750b/bateria_regla_v750b.py` | `e63d52324df195a03cccc00b15b29b112bd74857517dbef8d1741b7a17eb3d58` |
| `experiments/_s162_v750b/bateria_regla_v750b_salida.txt` | `20ecfc79b486c39070ad45ad2d0787a324552a677ab988f05950f691f78edfbc` |
| `experiments/_s162_v750b/ensayo_analizador_salida.txt` | `4dba44fd655260aa2296c0056c6ae67531fec720460957345421a58f091e3fba` |
| `experiments/_s162_v750b/objetivos_v750b.py` | `063f4780bebdbfb8cd8defca4b129f54ec7b002a23b79b5716bf2fb3550253dd` |
| `experiments/_s157_prereg_d25/evaluar_d25.py` (tag `s161-d25-lectura`) | `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747` (igual a `SHA_EVALUADOR`, `analizar_v750b.py:47`) |
| `experiments/_s162_v750b/sin_granulo_v750b.json` | **NO EXISTE** ni en el árbol ni en git (`git ls-files experiments/_s162_v750b/` da 35 archivos, ninguno con ese nombre; `git check-ignore` rc 1: tampoco está ignorado) |

## Caminos por los que el delta podría estar mal (escritos ANTES de releer el código y de abrir `verificador_v2/`)

Regla §6 (`no_peor`, `ganan`, `cand`):

1. C1. `no_peor` acepta como «no peor» un resultado con el neto en contra (EMPATE o BLOQUEA con neto > 0, o SIN
   SUSTRATO con neto > 0), o rechaza uno con neto a favor.
2. C2. El signo de `neto` está al revés del que el evaluador usa (c = e(brazo) − e(B1): positivo = peor); un cambio de
   signo elegiría al peor.
3. C3. `ganan` deja pasar un brazo que GANA con el canal que decide pero es peor con la tabla sola (la segunda
   condición de §6.2 no se aplica, o se aplica sobre la ventana o canal equivocados).
4. C4. `cand` (§6.3) deja pasar un brazo peor en el canal que decide, o peor con la tabla sola, o uno que no es
   elegible; o excluye a B1.
5. C5. Desempate entre dos o más ganadores: «el de menor E» a igual E no está escrito; el código decide por un orden
   que el pre-registro no quiso (el de `CANDIDATOS`, con B0 primero, no el de fidelidad al `.m`).
6. C6. El orden de `PREF` o la lista de `CANDIDATOS` cambiaron respecto del texto (B4, B2, B5, B1, B3).
7. C7. La condición «P1 = 0 en O con la tabla sola» declarada redundante no lo es (habría una protegida en la tabla que
   no es protegida con el canal que decide).
8. C8. `ver[...]` cambió de 3 a 4 campos y algún consumidor sigue leyendo 3 (desempaque roto o índice corrido).

Compuerta:

9. C9. Una combinación de banderas abre la compuerta sin marcar el veredicto ni cambiar el código de salida.
10. C10. `--leer-con-faltantes` cubre más de lo que §9 dice (K = producción, nulo del contador, control de la ROI).
11. C11. `--censo-omitido-solo-pruebas` abre la cobertura (el defecto que la propia batería dice haber atrapado) o
    sobrevive a un censo que SÍ se corrió y FALLÓ.
12. C12. Los códigos de salida 0, 3, 4, 5 no distinguen «sin veredicto» de «veredicto marcado» (o `--solo-controles`
    devuelve 0 con la compuerta cerrada).
13. C13. El control positivo (B0 pierde ≥ 1 de Cordón Caulle y B1 publica ≥ 3 de ésas) no detecta un oráculo muerto, o
    sus umbrales dejan fuera a B0 de los elegibles siempre (consecuencia lógica no declarada).
14. C14. El control negativo (B4 contra B1 en Cordón Caulle y Tupungatito) no tiene filo: compara la misma clave consigo
    misma y sólo puede fallar si el evaluador falla con una lista vacía.
15. C15. La cobertura con `sin_g`: una protegida sin gránulo no frena; el 2 % se calcula con numerador y denominador
    inconsistentes; `sin_crater` cuenta en el denominador pero se imprime como «fuera del denominador».

`sin_granulo_v750b.json`:

16. C16. El archivo no existe hoy y el analizador trata «ausente» como «0 pasadas sin gránulo» sin cerrar nada: SIN DATO
    leído como cero.
17. C17. El archivo y `objetivos_v750b.json` pueden venir de corridas distintas del generador (ningún sha ni fecha los
    ata).
18. C18. El generador escribe `protegida` desde `p.get("protegida")` de la población; si la población no define ese
    campo para pasadas sin gránulo, siempre sale `None` (= no protegida).

Batería `bateria_regla_v750b.py`:

19. C19. Escenarios que pasan igual con la regla rota: medir el nulo rompiendo a mano una copia del analizador (una
    línea por mutación) y mirando si la batería sale 1.
20. C20. Un escenario cuyo título dice una cosa y cuya población produce otra (el resultado esperado se cumple por una
    razón que no es la del título).
21. C21. La batería nunca escribe `sin_granulo_v750b.json`: VB2-07 queda sin cobertura.
22. C22. La batería siempre pasa `--censo-omitido-solo-pruebas`: el camino del censo real y `--leer-con-faltantes`
    quedan sin cobertura.
23. C23. La salida sellada `bateria_regla_v750b_salida.txt` no se reproduce con el árbol de hoy.
24. C24. La expresión regular que lee «ROI elegida» o la marca falla con el texto real (marca con dos banderas, motivo
    con paréntesis).

Resultado por camino, en una línea: C1 limpio · C2 limpio · C3 limpio en el código, sin cobertura en la batería
(VB3-03) · C4 limpio en el código, mitad sin cobertura (VB3-03) · C5 **hallazgo VB3-01** · C6 limpio · C7 limpio
(redundante de verdad) · C8 limpio · C9 limpio · C10 limpio · C11 limpio (la mitad «censo corrido y FALLA»: ver
VB3-06) · C12 hallazgo menor VB3-05 · C13 limpio para el oráculo muerto; la consecuencia sobre B0 está en VB3-04 ·
C14 declarado, filo limitado · C15 hallazgo menor VB3-07 · C16 **hallazgo VB3-02** · C17 parte de VB3-02 · C18 limpio ·
C19 y C20 **hallazgo VB3-03** · C21 parte de VB3-03 · C22 parte de VB3-03, declarado · C23 limpio · C24 limpio.

## Instrumentos y sus dos preguntas

**Batería sellada, línea base** (`bateria_base_salida.txt`): corrida sobre el árbol limpio
(`git archive origin/main experiments/_s159/n experiments/_s158_audit_r2 scripts pipeline volcanoes.yaml
frontend/index.html`, más `experiments/_s162_v750b/` del worktree y `evaluar_d25.py` del tag), rc 0; su
`mutaciones_salida.txt` es idéntico al sellado salvo la línea final «== BATERÍA», que el sellado trae y el archivo del
`--dest` no (va sólo a stdout). Ventana: las 11 poblaciones sintéticas de la batería (19 a 49 pasadas cada una).

**`mutar_v3.py`** (nulo de la batería): copia el árbol entero, cambia UNA línea de `analizar_v750b.py` por mutación
(reemplazo exacto, exigiendo una sola coincidencia y que el mutante compile), corre la batería sin tocarla y anota si
sale 1 (ATRAPADA) o 0 (SOBREVIVE). Pregunta 1: si la batería fuera siempre verde, las 11 sobrevivirían; control
positivo M6 (la bandera de pruebas abriendo la cobertura, el defecto que la v3 declara haber atrapado): ATRAPADA por
E3, como la batería dice. Pregunta 2: un mutante que no compila se detiene antes de correr (assert), así que una
ATRAPADA no puede venir de un analizador muerto; además se guarda el stdout entero por mutación. Denominador: 11
mutaciones, elegidas por los caminos C1 a C15, no al azar.

**`escenarios_v3.py`** (escenarios que la batería no tiene): poblaciones sintéticas con las mismas piezas que la
batería sellada, corridas contra el analizador v3 tal cual y, en S1 y S2, contra una copia con la condición quitada
(mutaciones M2 y M3), para mostrar que el escenario sí distingue. Pregunta 2: si el analizador no imprime «ROI
elegida», el campo queda `None`. Mi propio nulo: en la primera corrida S1, S2 y S3 salieron rc 3 porque no pasaba
`--censo-omitido-solo-pruebas` (la compuerta cerraba por el censo y el escenario no medía la regla); queda dicho en
el docstring de `correr` y corregido. Todos los escenarios llevan la bandera salvo S5a, S5c y S5d, que miden
justamente qué pasa sin ella.

## Hallazgos (por gravedad, lo peor primero)

### VB3-01. §6.2 no escribe el desempate a igual E, y el código lo resuelve por el orden de `CANDIDATOS`, que es el de menor fidelidad al `.m`  [TOCA LA REGLA §6]

- ARCHIVO:LÍNEA: `experiments/_s162_v750b/analizar_v750b.py:438` (`elegido = min(ganan, key=lambda b: ver[(b, "TO",
  "decide")][2])`; `min` devuelve el primero de los empatados en el orden de `ganan`, que hereda el de `elegibles`,
  que hereda el de `CANDIDATOS = ("B0", "B1", "B2", "B3", "B4", "B5")`, l. 45) contra `PREREGISTRO_V750B.md:129-130`
  («Si ganan dos o más, el de menor E») y l. 135-137 (orden de cercanía al `.m`: B4, B2, B5, B1, B3).
- QUÉ PASA: dos ROI que ganan contra B1 con el mismo número de errores bajo 1 MW son, para el pre-registro, iguales
  en desempeño; §6.3 dice que a igual desempeño manda la fidelidad al código de MIROVA (decisión de Nicolás del
  2026-10-21). En §6.2 ese caso no está escrito, y el código elige al que aparece primero en la lista de candidatos:
  B3 antes que B4, B2 antes que B4, B3 antes que B5. Es decir, en un empate el código prefiere la ROI que el propio
  pre-registro declara menos fiel (B3 «usa nuestra configuración, no la de MIROVA»).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (nada corre en producción). Si pasa, el paquete V750-A llevaría una ROI
  distinta de la que la regla escrita quiso; la diferencia en píxeles es la que haya entre las dos cajas empatadas.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/verificador_v3/escenarios_v3.py --arbol <árbol> --dest <tmp>`,
  bloque `== S3` (B3 y B4 apagan los mismos 6 negativos de Láscar que B1 publica: los dos GANA, neto −6 en 6 bloques,
  p = 1/64, E idéntico): `ROI=B3 (gana contra B1 (§6.2)`, elegibles `['B1', 'B2', 'B3', 'B4']`. Con la lista de
  fidelidad sería B4. La batería sellada no tiene ningún escenario con dos ganadores (ver VB3-03).
- CONFIANZA: CONFIRMADO (lectura de l. 45, 427, 436, 438 y corrida S3). SOSPECHA sólo en su frecuencia real: no puedo
  saber cuántos empates habrá en el run (B4 = B0 en nueve volcanes y B2 = B0 donde el cráter cae en la celda central,
  así que dos brazos con E idéntico no son un caso raro por construcción).
- GRAVEDAD: 2. Qué decisión tuerce: cuál ROI pasa a V750-A en un empate; no toca ninguna alerta de hoy. Arreglo de una
  frase y una clave: en §6.2 «a igual E, el orden de §6.3» y `min(ganan, key=lambda b: (E, PREF.index(b)))`. La
  alternativa (declarar que a igual E manda el orden de `CANDIDATOS`) contradice la razón de §6.3 y no la recomiendo.

### VB3-02. Si `sin_granulo_v750b.json` no está donde el analizador lo busca, cuenta 0 pasadas sin gránulo y la compuerta se abre; hoy el archivo no existe en el repositorio

- ARCHIVO:LÍNEA: `experiments/_s162_v750b/analizar_v750b.py:215-217` (`sin_g = json.loads(...) if sg.exists() else
  []` e imprime «archivo ausente»); `objetivos_v750b.py:104-106` (lo escribe al lado del generador);
  `PREREGISTRO_V750B.md:194-195` («se commitea con los objetivos»). `git ls-files` no lo tiene.
- QUÉ PASA: una pasada sin gránulo es una noche que el run nunca mira; el pre-registro quiere que cuente como SIN DATO
  y que una protegida ahí frene la lectura (VB2-07). El analizador cumple eso cuando el archivo está (S4a, S4c), pero
  si el archivo falta, por no haberse commiteado, por leer el analizador desde otro árbol, o por pasarle una ruta
  mal escrita con `--sin-granulo`, el resultado es el mismo que «0 pasadas sin gránulo»: SIN DATO leído como cero,
  sin cerrar nada ni marcar el veredicto. Además nada ata el archivo a `objetivos_v750b.json` (ni sha ni fecha): puede
  quedar uno de una corrida del generador y el otro de otra.
- CÓMO SE VE EN EL DASHBOARD: invisible. En la lectura del run, «protegidas SIN DATO: ninguna» con una protegida menos
  de las que hay.
- CÓMO REPRODUCIRLO: `escenarios_v3.py`, bloque `== S4b` (misma población que S4a, ruta inexistente en
  `--sin-granulo`): `compuerta: ABIERTA`, `sin_granulo: ('archivo ausente', '0')`, `ROI=B4`, rc 4; contra `== S4a`
  (archivo con una protegida): `cobertura: INSUFICIENTE`, rc 3.
- CONFIANZA: CONFIRMADO (lectura y corrida). Que el archivo vaya a estar en el despacho es SOSPECHA en los dos
  sentidos: hoy no está, y la segunda vuelta midió 0 pasadas sin gránulo con los datos del 24-oct.
- GRAVEDAD: 2. Fuera de la regla §6 (compuerta). Arreglo: con el archivo ausente, SIN DATO del control de cobertura
  (compuerta cerrada, o al menos `--leer-con-faltantes` obligatorio), y que el generador escriba dentro del json el
  sha256 de `objetivos_v750b.json` para que el analizador lo compruebe.

### VB3-03. La batería sellada deja vivas 6 de 11 mutaciones, incluidas 4 que la segunda vuelta ya había matado con sus escenarios; E5 no prueba lo que su título dice; y §11 afirma que la v3 «suma los escenarios que las mataban»

- ARCHIVO:LÍNEA: `experiments/_s162_v750b/bateria_regla_v750b.py:237-245` (E5: «B2 y B3 GANAN contra B1; B2 con más
  E»), `:225-230` (E3), `:269-293` (V1, V3, V6 agregados); `PREREGISTRO_V750B.md:213-218` (§11); informe de la segunda
  vuelta `verificador_v2/VERIFICADOR_V2_PREREGISTRO_V750B.md`, VB2-05 (lista de mutaciones que sobrevivían y de los
  escenarios que las mataban).
- QUÉ PASA: la batería es la evidencia del sello («comprueba sola el resultado esperado de 11 escenarios, sale 1 si
  alguno no coincide»). Medido su nulo (`mutar_v3_salida.txt`, 11 mutaciones de una línea):
  - ATRAPADAS (5): M1 (SIN SUSTRATO sin mirar el neto, por V3), M4 (§6.3 sin la tabla sola, por V1), M6 (la bandera de
    pruebas abre la cobertura, por E3; control positivo del instrumento), M8 (control positivo sin exigir que B1
    publique, por V6), M11 (la marca SIN CENSO no se escribe, por los 8 escenarios con veredicto).
  - SOBREVIVEN (6): **M2** (§6.2 sin la condición de la tabla sola), **M3** (§6.3 sin la condición del canal que
    decide), **M5** (las pasadas sin gránulo no se leen), **M7** (entre los que ganan se elige el de MAYOR E), **M9**
    (una protegida SIN DATO deja de frenar la lectura; en E3 el 2 % la tapa: 2 de 39), **M10** (K = producción deja de
    cerrar la compuerta; ningún escenario tiene una K distinta).
  - E5 pasa por otra razón que la del título: B2 queda EMPATE (neto −4 en 8 bloques, p gana 37/256,
    `bat_v3/base/E5/salida.txt`), no GANA; sólo B3 gana, y la regla «el de menor E» nunca se ejercita. Por eso M7
    sobrevive. La segunda vuelta ya lo había dicho (VB2-05: «E5 dice probar el desempate por menor E pero solo gana
    un brazo») y lo había cubierto con su S19; ese escenario no se sumó.
  - M2, M7 (M19 en la numeración de la segunda vuelta), M9 y M10 están en la lista de VB2-05 como «caen con mis
    escenarios dirigidos». La v3 sumó V1, V3 y V6 (tres de los once de la segunda vuelta) y §11 dice «la v3 suma los
    escenarios que las mataban»: eso vale para tres, no para las cuatro que siguen vivas.
  - Lo que la batería no puede medir por construcción y está declarado: el censo real y `--leer-con-faltantes`
    (siempre pasa la bandera de pruebas, docstring l. 5-6).
- CÓMO SE VE EN EL DASHBOARD: invisible. Es la calidad de la evidencia del sello.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/verificador_v3/mutar_v3.py --arbol <árbol limpio> --dest <tmp>`
  (unos 3 minutos por mutación; `--solo M2,M7` para dos). Para ver que el código SÍ aplica lo que M2 y M3 quitan:
  `escenarios_v3.py`, bloques `S1` (ROI B4 con el analizador v3; B2 con M2) y `S2` (ROI B2 con la v3; B4 con M3).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Fuera de la regla §6: la regla está bien implementada en los puntos que las mutaciones tocan (S1 y S2 lo
  muestran); lo que falla es que la batería no lo vigila. Arreglo antes del despacho, no del sello: sumar a la batería
  S1, S2 y S3 de este verificador (o los de la segunda vuelta), un E5 donde B2 GANE de verdad, un E3 partido (una
  protegida SIN DATO con menos del 2 %) y un escenario con K distinta; y corregir §11.

### VB3-04. B0 no puede ser elegido nunca cuando hay veredicto: el control positivo lo garantiza, y el texto lo trata como predicción

- ARCHIVO:LÍNEA: `analizar_v750b.py:384-391` (`pcc` = protegidas de Cordón Caulle que deciden y que B0 no publica;
  `ctrl_roi` exige `len(pcc) >= 1`), `:340-351` y `:427` (P1 de B0 en T ∪ O con el canal que decide cuenta esas
  mismas pasadas, así que P1(B0) ≥ 1 y B0 sale de `elegibles`); `PREREGISTRO_V750B.md:158` (§8: «B0: pierde 6 o más
  protegidas; no elegible») y l. 45 (`CANDIDATOS` incluye B0; `PREF` no).
- QUÉ PASA: con la compuerta abierta, B0 tiene por construcción al menos una protegida perdida, así que nunca es
  elegible. No es un defecto (B0 es la caja del ejemplo del `.m`, y el lacolito de Cordón Caulle cae fuera de ella),
  pero el pre-registro lo presenta en §8 como predicción falsable y es una certeza lógica de §7.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `escenarios_v3.py`, bloque `S3`: B0 GANA (neto −6, p 1/64) y no está en `elegibles`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Una frase en §7 o §8.

### VB3-05. `--solo-controles` sale 0 también con la compuerta CERRADA

- ARCHIVO:LÍNEA: `analizar_v750b.py:406-408` (`return salir(0 if a.solo_controles else 3)`). No es del delta (la línea
  venía de la v2), pero el delta reescribió la compuerta alrededor.
- QUÉ PASA: el ensayo del pre-registro (§11) usa `--solo-controles`; si alguien automatiza ese ensayo y mira el código
  de salida, una compuerta cerrada se lee como éxito.
- CÓMO REPRODUCIRLO: `escenarios_v3.py`, bloque `S5c`: `compuerta: CERRADA`, rc 0.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1. Fuera de la regla.

### VB3-06. Con `--censo-omitido-solo-pruebas` Y el censo real pasado, un censo que FALLA no cierra la compuerta, y la marca dice «SIN CENSO» aunque el censo corrió

- ARCHIVO:LÍNEA: `analizar_v750b.py:288-307` (si vienen `--censo-art` y `--censo-objetivos`, el censo se calcula y
  `censo_ok` puede ser False), `:398-401` (`censo_pasa = censo_ok or a.censo_omitido_solo_pruebas or ...`; la marca
  «[SIN CENSO, NO VALE PARA EL RUN]» y rc 4 se ponen por la bandera sola).
- QUÉ PASA: la bandera está pensada para baterías sin censo; si se combina con el censo real y éste falla, el veredicto
  sale igual, marcado y con rc 4. No es silencioso (la marca y el rc 4 lo invalidan para el run), pero la marca
  describe otra situación. No lo corrí (no tengo el censo); es lectura.
- CONFIANZA: CONFIRMADO por lectura, SIN CORRER. GRAVEDAD: 1. Fuera de la regla. Arreglo: que la bandera sea
  incompatible con `--censo-art` (error de argumentos).

### VB3-07. En el 2 % de cobertura, `sin_crater` queda en el denominador y se imprime como «fuera del denominador»

- ARCHIVO:LÍNEA: `analizar_v750b.py:206-209` (imprime `no observadas (fuera del denominador): {fuera, sin_crater}`) y
  `:223` (`len(obj) + len(sin_g) - no_obs["fuera"]`: sólo resta `fuera`). La resta de `fuera` venía de la v2; el delta
  sumó `sin_g` a los dos lados y dejó la inconsistencia.
- QUÉ PASA: una pasada con celdas sin dato en el 7 × 7 del cráter no se mide en ningún brazo, pero engorda el
  denominador del 2 %: el umbral queda un poco más laxo de lo que dice el texto. Con pocas `sin_crater` (el ensayo
  real tiene 1 de 506) no cambia nada.
- CONFIANZA: CONFIRMADO por lectura. GRAVEDAD: 1. Fuera de la regla.

## SIN DATO (no medido, no inferido)

- Frecuencia de empates de E entre ganadores en los datos reales (VB3-01): no hay run.
- Si `sin_granulo_v750b.json` existirá y coincidirá con los objetivos al despachar (VB3-02): hoy no existe; la segunda
  vuelta midió 0 pasadas sin gránulo el 24-oct.
- Control del censo real y K = producción sobre records reales: no los corrí (la segunda vuelta corrió el censo).
- El brazo nativo (N0, N1) y las descriptivas por cenit: fuera del alcance (no cambian en el delta salvo el texto de §7).
- El control negativo con «filo» (B4 contra B1 en Cordón Caulle y Tupungatito): por lectura de `caja_de`
  (l. 142-145) B4 y B1 leen la MISMA clave de `P` en esos volcanes, así que la diferencia es 0 por identidad y el
  control sólo puede fallar si `regla_signos_p2` falla con una lista vacía. Está declarado así en §7 («el evaluador
  cuenta diferencias que no existen»); no lo cuento como verificación de nada más.

## VERIFICADO LIMPIO

- **`no_peor` es exactamente «neto ≤ 0»** (C1): `regla_signos_p2` (`evaluar_d25.py:552-566` del tag) da GANA sólo con
  neto < 0, EMPATE sólo con neto ≤ 0, PIERDE y BLOQUEA sólo con neto > 0, y SIN SUSTRATO con cualquier neto; con el
  filtro `neto <= 0` de `analizar_v750b.py:433` la función equivale a «no tiene más errores netos que B1», que es lo
  que §6.2 escribe («GANA o EMPATE, o SIN SUSTRATO con el neto en 0 o a favor»). Monótona: no hay región donde un
  bloque a favor de más la haga «peor». Comando: `git show s161-d25-lectura:experiments/_s157_prereg_d25/evaluar_d25.py
  | sed -n 552,566p`.
- **Signo de la contribución** (C2): `c = err(b) − err(B1)` (l. 371-372), positivo = peor; S1 (B2 publica 15 bajas que
  B1 no) da `GANA neto -9`, E1 (8 negativos de más) da PIERDE. Dirección coherente con el evaluador.
- **§6.2, segunda condición** (C3): el código la aplica; S1 (B2 GANA con el canal que decide, `PIERDE neto 6 B 6` con
  la tabla sola) da ROI B4 y B2 no entra a §6.3; con M2 da B2. `escenarios_v3_salida.txt`, bloques S1.
- **§6.3, las dos condiciones** (C4): S2 (B4 `SIN SUSTRATO neto 4` con el canal que decide, neto 0 con la tabla) da
  ROI B2; con M3 da B4. V1 de la batería y M4 cubren la otra condición. B1 entra siempre (`b == "B1"`, l. 443).
- **VB2-02 efectiva**: M1 ATRAPADA por V3 (ROI B4 ≠ B1).
- **`PREF` y `CANDIDATOS`** (C6): l. 45-46 = B4, B2, B5, B1, B3 = `PREREGISTRO_V750B.md:135-136`.
- **La segunda condición de §6.1 es redundante de verdad** (C7): `protegida` se calcula sobre todas las filas pareadas
  (`01_poblacion.py:111`) y `alerta_tabla` sobre las CONS (l. 112); `alerta_protegida` no mira la fuente
  (`scripts/clase_mirova.py:65-77`); `etiqueta(o, "tabla")` sólo da «prot» con una CONS protegida (l. 319-334), que
  entonces también es protegida con `todo`. No puede vetar nada aparte. Mutante equivalente, como dijo VB2-10.
- **`ver` de 4 campos** (C8): consumidores en l. 424 (escritura), 427 `[0]`, 432 (desempaque de 4), 436 `[1]`,
  438 `[2]`. Ninguno lee 3.
- **Banderas y códigos de salida** (C9, C10, C12): S5a (`--leer-con-faltantes` solo, sin censo): ABIERTA, marcada
  «LEÍDO CON FALTANTES», rc 5. S5b (las dos): marcada «SIN CENSO», rc 4 (la bandera de pruebas ya puso `censo_ok`
  en True, así que no hay «faltantes» que marcar: coherente). S5e (oráculo muerto + las dos banderas): CERRADA, rc 3.
  S5f (K distinta en 1 de 41, protegida, + las dos banderas): CERRADA, rc 3. S5d (censo con 0 pasadas comunes):
  FALLA, rc 3. M11 (marca que no se escribe): ATRAPADA en los 8 escenarios con veredicto. No encontré ninguna
  combinación que abra sin marcar.
- **Cobertura con pasadas sin gránulo, cuando el archivo existe** (C15, C18): S4a (una protegida) INSUFICIENTE rc 3;
  S4c (una no protegida, 1/42 = 2,4 %) INSUFICIENTE rc 3: numerador y denominador la incluyen (l. 223). `protegida`
  está definida para toda la población antes de filtrar por gránulo (`01_poblacion.py:111, 117`).
- **Control positivo detecta el oráculo muerto** (C13): V6 rc 3; M8 (sin exigir que B1 publique) ATRAPADA por V6.
- **La salida sellada se reproduce** (C23): `bateria_base_salida.txt` = `bateria_regla_v750b_salida.txt` salvo la línea
  final de stdout; rc 0.
- **Expresiones regulares de la batería** (C24): `marca` y `ROI elegida` leen bien el texto real; `p2_TO_todo` recorre
  desde «TO, canal decide» hasta el final y se queda con el ÚLTIMO bloque («TO, canal todo»), que coincide con su
  etiqueta; es informativo, no decide nada. (Mi primer `escenarios_v3.py` tenía el mismo recorrido y por eso mostraba
  el canal «todo» como «tabla»; corregido acotando al bloque.)
- **sha256 del evaluador**: `cargar_signos` (l. 59-87) comprueba `2e5576…` y las constantes 162, 20, 20; el archivo del
  tag da ese sha (tabla de arriba).
- **El delta no toca `pipeline/`, `data/` ni `frontend/`**: `git diff --stat 607062ba7 439968ec1 -- experiments/_s162_v750b/`
  es el delta entero (20 archivos, todos bajo esa carpeta).

## Línea final

**Cambios en la regla: uno, el desempate a igual E de §6.2 (VB3-01: una frase en el texto y una clave de orden en
`analizar_v750b.py:438`). Cambios fuera de la regla, antes del despacho y no del sello: VB3-02 (archivo de pasadas
sin gránulo ausente leído como cero; atarlo a los objetivos), VB3-03 (batería: sumar S1, S2, S3, un E5 que gane de
verdad, un E3 partido y una K distinta; corregir §11), y los menores VB3-04 a VB3-07.**
