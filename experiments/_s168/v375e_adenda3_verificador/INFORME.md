# Verificador con contexto limpio: adenda 3 (§9) de PREREGISTRO_E.md (V375-E) contra su código

- Objeto: `experiments/_s162_v375/PREREGISTRO_E.md` (cuerpo §1 a §7, adenda 2 §8 sellada, adenda 3 §9 sin sellar) y
  `experiments/_s162_v375/e_adenda2/` (lector, batería, nulo, repaso, conteo de diseño).
- Commit medido: `e6675da85c5779d84d85731c1032c835b726c298` (worktree `cranky-payne-f7d913`, rama `claude/s168-v375e-sello`).
- Hora del servidor (`date -u`): inicio 2026-10-29 19:35:03 UTC; fin 2026-10-29 19:55 UTC.
- Modelo: Sonnet 5.5 (`claude-sonnet-5-5`).
- Sólo lectura. No abrí `D:\vrp-trabajo\temporales\s167_v375e_far\` ni artefactos de runs del marco; no corrí el lector sobre
  datos reales. Lo que corrí: la batería sintética y dos mutaciones (detalle al final). Mis temporales: 
  `D:\vrp-trabajo\temporales\s168_ver_adenda3\`.

## Caminos previos

Los fijé después de leer el informe del verificador anterior (VC167-01 a 09) y antes de abrir el pre-registro y el código.
No los escribí en un archivo en ese momento; los transcribo aquí tal como los tenía.

1. El texto de §9.4 a §9.7 promete cosas que el lector no hace (en particular los controles de la curva del §4: sesgo de
   plataforma y las dos ganancias, y el rol de P-def).
2. La tabla del §9.7 y el código discrepan en alguna salida (precedencia entre «EMPEORA» y la marca A104, ramas extra del
   código que la tabla no menciona, salidas de la RP sin mapear).
3. Las compuertas (§9.3) no cortan de verdad: un control que cae pero el lector sigue leyendo (cuál: C3, que se calcula en
   `main` y no en `analizar`).
4. Las aserciones de la batería no pueden fallar (pruebas vacuas, controles que pasan con cero casos).
5. Las cifras de §9.11 (111 de 114, 113 de 114, L20 equivalente) no coinciden con los `*_salida.txt`, o la salvedad de las
   111 no re-corridas esconde una caída.
6. Marcas de precedencia incompletas (§9.1) y texto viejo que contradice a la adenda 3.
7. Decisiones diferidas para después de ver datos (la sombra, los controles de la curva, la marca A104).
8. Llamadas con firma equivocada a `evaluador_comun` o `curva_cenit` (modo «decide», d′, campos de entrada de la curva).
9. La batería o el conteo de diseño leen datos del marco o del run FAR.
10. El «SIN SUSTRATO por construcción» de la curva (28 y 5 noches) no sale de lo que dice.

## Veredicto: SELLABLE CON CAMBIOS MENORES

No encontré ningún hallazgo de gravedad 3. El lector implementa lo que §9.4 a §9.7 dicen de la magnitud (M), la curva, P-sinfiltro,
PLACEBO, la equivalencia como compuerta y la tabla de criterios; las llamadas alcanzan desde `main`, los argumentos son los
del texto, y la batería (165 de 165, la corrí) prueba esas ramas con aserciones que pueden fallar. Quedan dos hallazgos de
gravedad 2 que recomiendo arreglar antes del sello porque son de una línea cada uno: **VA168-01** (la caída de C3 no corta
la lectura, y §9.3 a dice que sí) y **VA168-02** (los controles de la curva del §4 que el texto manda «con la curva» no
existen en el código ni tienen consecuencia escrita). Ninguno cambia la lectura de la retrospectiva; el segundo sí toca el
criterio (d) de la sombra.

## Estado de VC167-01 a 09

| id | gravedad previa | estado | por qué |
|---|---|---|---|
| VC167-01 población y pesos | 2 | **cerrado** | §9.2 dice la unión S159 + S162 + S162b (149 + 709 + 1.200 = 2.058, comprobado contra las listas) más 330 lejanas y 20 de control de vida, peso `N_h / n_ok_h`, decide la unión, B §5.5 y B2 no rigen. El lector hace eso (`objetivos()` l. 211-228, `pesos` l. 667-671); recalculé el peso de Chaitén z<=40 y da 2,01, como dice §9.2. «859» queda marcado en §3.1. |
| VC167-02 control de vida vs «no decide» | 2 | **cerrado** (con VA168-01) | §9.3 a elige «control caído = no legible»; en el código C7 entra a `fallas` (l. 642-643) y `analizar` vuelve antes de la vara 1 (l. 708-709). NO DECIDE queda sólo para más de 10 % de `far_tabla` SIN DATO (l. 691). |
| VC167-03 salidas sin regla | 2 | **cerrado** | Tabla de §9.7 y `criterios_retro` (l. 505-516), `regla_adopcion` (l. 519-537), `estado_d_sombra` (l. 489-502). Revisé las filas una por una (ver abajo); la batería las prueba (16 casos de criterios, 8 de la regla del paquete). Quedan matices de forma (VA168-03, VA168-04). |
| VC167-04 §4, §5.2, §5.3, brazos | 3 | **en parte** | Cerrado: M con `decidir_estrato` en modo «decide» sobre la unión (l. 427-444), cortes que informan, A104 por tramo, curva con `curva_cenit` (l. 473-486), P-sinfiltro (l. 662, 743-746), PLACEBO como C8/C9, P-def justificado, controles de B §4 explicados. **Abierto**: sesgo de plataforma y las dos ganancias de la curva (§4) no se calculan ni tienen consecuencia (VA168-02); el lector de la sombra no existe (diferido por diseño en §9.8). |
| VC167-05 compuerta de equivalencia | 2 | **cerrado** | `analizar` l. 713-717 devuelve `corte = NO EQUIVALENTE` antes de la RP y del §5; `codigo_salida` da 4 (l. 540-545). Batería: «§9.3 compuerta» y «código de salida». Mutaciones L77 y L78 en el nulo. |
| VC167-06 borrador y marcas | 1 | **cerrado** (restos en VA168-05) | §9.1 da la cláusula de precedencia; hay marcas ⚠️ en cabecera, §3.1 a §3.3, §4, §5.1 a §5.4, riesgo conocido, §7, §7.5, §8.5, §8.8, §8.9 y §8.12. |
| VC167-07 MISSION | 1 | **cerrado** | §9.7 la declara informativa; el lector la rotula «MISSION (informa; cuenta también las de §8.13)» (l. 741). Probado. |
| VC167-08 «cercano» | 1 | **cerrado** | §9.9; el encabezado de la vara 1 dice «cercano = ... al CRÁTER, no al punto X0, Y0» (l. 723-724). Probado. |
| VC167-09 sombra | 1 | **cerrado en parte** | §9.8 resuelve lo central (la RP no se corre en la sombra). Queda el redondeo de 0,01 km del «cercano» desde `anomaly_pixels` si el brazo elegido es cercano (VA168-08). |

## Hallazgos nuevos

### VA168-01 (gravedad 2): C3 cae y el lector igual lee el marco

§9.3 a: «si cae cualquiera de C1 a C9 ... sale 3, LECTURA NO LEGIBLE, y no se lee nada, ni el marco» (repite §8.7). En el
código, C3 (`control_listas`) se calcula en `main` (l. 866-867) y su lista de fallas se guarda en `fallas`, pero `analizar`
(l. 930) no la recibe: sigue hasta el final (vara 1, vara 2, RP, M, curva, criterios) e imprime y escribe `--salida` y
`--json` con todos los números; sólo al final `codigo_salida` devuelve 3 (l. 932-938). C4 sí corta temprano (l. 855-857);
C1, C2, C5 a C9 cortan dentro de `analizar` (l. 708-709). La batería sólo prueba el caso C3 en verde con `main`
(`probar_adenda2.py` l. 947, «con C3 en verde») y C3 por separado con `control_listas`; no hay prueba ni mutación de «C3 cae ⇒ no se imprime
el marco». La deriva viene de la adenda 2 (§8.7 ya lo decía), pero la adenda 3 la reafirma como cerrada.
Probabilidad baja (C3 compara listas fijas por sha256), pero la promesa literal es falsa para ese control.
Corrección: pasar las fallas de C3 a `analizar` (o `if fallas: return` antes de la cobertura) y agregar una prueba por
`main()` con una lista FAR atada a otro sha256 (el caso ya está armado en «C3: sin gránulo desatado») más su mutación;
o, si no se quiere tocar código, escribir en §9.3 a que C3 sale 3 pero no corta la impresión.

### VA168-02 (gravedad 2): los controles de la curva del §4 no existen en el código

§9.4: «Controles de la curva (§4: nulo de cenit parecido, sesgo de plataforma, ganancias): van con la curva, y en la
retrospectiva informan (§9.6)». En el lector el único que corre es el nulo de cenit parecido, y sólo porque
`curva_cenit.veredicto` lo usa (l. 482-485). `grep` de `sesgo_plataforma`, `ganancia` y `curva_mirova_separada` en
`leer_posicion_v375e.py`: 0 coincidencias (sólo aparece `placebo_ganancia`, que es el C9 de M). §9.6 no vuelve a hablar de
ellos y `estado_d_sombra` (l. 489-502) no los usa. En la retrospectiva no importa (la curva da SIN SUSTRATO por
construcción), pero (d) se decide en la sombra, y el §4 dice que sin la «ganancia que crece con el cenit» «el instrumento
no ve el cenit»: qué pasa con (d) si ese control o el sesgo de plataforma fallan no está escrito en ninguna parte. Es una
decisión que quedaría para el momento en que se escriba el lector de la sombra, con datos de la ventana P ya acumulados.
Corrección: una frase en §9.6 o §9.8: «sesgo de plataforma, ganancia pareja y ganancia que crece con el cenit se calculan
sólo en el lector de la sombra; informan y no anulan (d)» (o «si fallan, (d) pasa a DECIDE NICOLAS»), la que Nicolás prefiera,
y quitar «van con la curva» de §9.4 para la retrospectiva.

### VA168-03 (gravedad 1): `estado_d_sombra` tiene una condición que la tabla no dice

Tabla §9.7 (d) sombra, CUMPLE: «... el extremo inferior del IC de D del paquete sobre el extremo superior del IC de D de K
... sin CAER MENOS QUE MIROVA». El código (l. 499-501) agrega que la curva de K no sea SIN SUSTRATO ni NULO SESGADO. La
batería la prueba (último caso de «§9.7 (d)») y es una exigencia razonable, pero el texto no la menciona. Además la función
no verifica que reciba la curva condicionada (el lector produce las dos). Corrección: una cláusula en la tabla.

### VA168-04 (gravedad 1): precedencia de la marca A104 y qué es «otro estado de (c)»

Tabla §9.7 (c): EMPEORA va en la columna NO CUMPLE y «marca A104 en M» en DECIDE NICOLÁS, sin decir cuál manda cuando
ocurren juntas. El código (l. 512) hace que A104 gane («M EMPEORA con A104 ⇒ DECIDE NICOLAS» está probado), y la marca
compara el estado binario CUMPLE / NO CUMPLE (`estado_c`, l. 442), no el veredicto crudo: unión MEJORA y O1 NEUTRO no saltan;
unión SIN SUSTRATO y O1 MEJORA sí. Es una decisión deliberada, pero el texto de §9.5 («otro estado de (c)») no la deja clara.
Corrección: una línea.

### VA168-05 (gravedad 1): marcas y cifras viejas que sobreviven

- La tabla de brazos de §2 (P-def, P-sinfiltro, PLACEBO) no lleva marca ⚠️ hacia §9.4, donde P-def pasa a «no se corre».
- §8.11 sigue diciendo «140 de 140» y «83 de 84» sin marca de que §9.11 las reemplaza (165 de 165, 113 de 114).
- §9.1 enumera «8.4» entre los puntos marcados; en §8.4 la única llamada nueva es la aclaración de «cercano» (VC167-08),
  no una marca de superado.

### VA168-06 (gravedad 1): la justificación de no correr P-def es más corta que el papel de P-def

§9.4 dice que el papel de P-def (separar el efecto de la ROI) «ya lo midió V375-C». V375-C midió la ROI sobre las lecturas de
detección (P1, P2, recall, silencio) y una mediana de magnitud (0,999, n 265, `resultado_run40116289866/INFORME.md` l. 26),
sobre los lotes S159 y S162; no sobre M con `decidir_estrato`, ni sobre la curva, ni sobre S162b. La decisión es explícita y
PD1 ya fijó C13, así que no queda nada abierto; sólo conviene decir que la atribución de la ROI a la magnitud y la curva se
renuncia.

### VA168-07 (gravedad 1): dos controles pasan vacíos y una cifra de diseño dice «por construcción»

- C8 (PLACEBO) con cero pasadas con record de K da «0 de 0» y no cae (l. 586-590); en datos reales hay records de K, pero el
  código no lo exige, a diferencia de C1 que sí pide al menos un caso (l. 596).
- §9.6 dice que el nulo de cenit parecido da a lo más 5 noches y que por eso la curva da SIN SUSTRATO «por construcción».
  El conteo (`contar_pares_curva.py`, salida: 28 noches de lectura, 5 de nulo) usa el cenit de la lista; el lector usa el del
  run. El mismo texto lo reconoce («puede diferir algo»). Como (d) no decide en la retrospectiva, no cambia nada.

### VA168-08 (gravedad 1): redondeo de «cercano» en la sombra

Si la retrospectiva elige cercano, la sombra obtendría su distancia del menor `dist_km` de `anomaly_pixels`, redondeado a 0,01
km por la vía, con frontera inclusiva del radio (`distancias_desde_record`, l. 138-147; probada «exacto» a 0,0051 km). §9.8 no
dice cómo se trata un cercano a menos de 0,005 km del radio. Es el residuo de VC167-09; el lector de la sombra aún no
existe.

## Cómo revisé lo que pedía (b)

**Trazado de llamadas.** `main` (l. 841-938) llama a `analizar(pasadas, obj, meta, publicar, E, bool(a.art_far))`. Dentro de
`analizar`, en orden: C2 y C8 (l. 574-590), C1, C5, C6, equivalencia por brazo (l. 593-629), C7 (l. 631-645), K re-corrido
(l. 648-653), filas con P-sinfiltro (l. 656-680), cobertura (l. 685-698), C9 (l. 701-707), salida si hay fallas (l. 708-709),
compuerta de equivalencia (l. 713-717), vara 1 con sinfiltro (l. 719-752), vara 2 con P2-L (l. 755-769), vara 3, RP con A104
(l. 779-811), M por brazo (l. 817-824), curva (l. 825-829), criterios por brazo (l. 830-833) y `regla_adopcion` (l. 834-836).
La salida es 3 si `fallas`, 4 si `corte`, 0 si no (l. 540-545 y 938).

**Firmas reales.** `evaluador_comun.decidir_estrato(P, modo, comparador=True, ok_ctrl=True)` (l. 517) existe con modo
`"decide"` | `"bloquea"` | `"informa"`; en «decide» con comparador, una MEJORA sin d′ calibrado da INDECIDIBLE y sin d′ MEJORA
da NEUTRO (l. 552-560), o sea exige d′ como dice §9.5. `placebo_ganancia(P, modo)` (l. 564) da x1,2 y x0,8 y el d′ del
placebo es 0 por construcción (comprobé la aritmética de `comparar_con_ganancia`). `tramo_cenit(z)` (l. 252) es de 10°. De
`curva_cenit`: `pares_por_noche`, `pares_nulo`, `resumen`, `veredicto`, y `r["todas"]["d"] = (mediana, (lo, hi), n)`
(`mediana_ic`), con lo cual `cur_p["d"][1][0]` es el extremo inferior y `cur_k["d"][1][1]` el superior, como dice §9.7.
El nulo de cenit parecido ordena con la regla de la lectura y la condición de ≥8 noches está en `veredicto` (`curva_cenit.py` l. 155-174).

**Tabla §9.7 contra código, fila por fila.**
(a) `P1_veto_n3` vacío ⇒ CUMPLE; sale de las protegidas que K publica y el brazo calla, sin las de §8.13, con las pérdidas
comunes dentro (l. 731-735). (b) P2 contra K en {GANA, EMPATE, SIN SUSTRATO}, silencio distinto de ENCIENDE DE MAS y P2-L
fuera de {PIERDE, BLOQUEA} (l. 509-511); el silencio NO RESUELTO cumple, igual que el texto. (c) MEJORA y NEUTRO cumplen, el
resto no (l. 421-424); A104 manda (VA168-04). (d) retrospectiva INFORMA. Retrospectiva por brazo: NO CUMPLE > DECIDE NICOLAS >
CUMPLE (l. 514-515). `regla_adopcion`: NINGUN ⇒ NO CUMPLE; NO DECIDE ⇒ los tres; NO RESUELTO ⇒ `no_vencidos` (en el ciclo,
los tres vivos); ELEGIDO y SE QUEDA RADIANTE ⇒ el del brazo salvo marca A104 ⇒ NICOLAS salvo que no cumpla (l. 524-537). Todo
coincide con la tabla. Probé a leer los casos de la batería (l. 371-389) y cada fila de la tabla tiene al menos un caso con
resultado esperado distinto de las demás.

**M.** Pares (`pares_magnitud`, l. 399-418): `pos_prot` y `pos_bajo` con MIROVA > 0, publicados por el brazo y por K con
magnitud > 0; los que publica uno solo salen aparte (`salen`). Regla: `decidir_estrato(P, "decide")` sobre la unión (l. 432);
cortes por cenit, volcán, canal y clase en modo «informa» (l. 433-440); A104 en O1 y O2 con sustrato (l. 441-442). Coincide
con §9.5.

**Qué prueba la batería de lo nuevo** (l. 223-390): pares de M, estado de (c), M por tramo con A104 en O1, el comparador d′
que baja una ganancia pareja a NEUTRO, cortes que informan, C9 en verde y en rojo, el PLACEBO en los tres campos, C8 en verde
y en rojo, la compuerta (exit 4 / 3 / 0), P-sinfiltro que publica la lejana que radiante calla, la curva con K = VK y brazo =
V, el caso «el brazo calla en el cenit alto», los siete casos de (d) y los 16 de los criterios.

## Sobre las mutaciones (§9.11), lo que comprobé

- `mutar_adenda2_salida.txt`: 118 líneas; 111 `ATRAPADA`, `L20 SOBREVIVE`, `L94 SOBREVIVE`, `L85 CAIDA (KeyError: 'ningun')`,
  `RESULTADO: 111 de 114`. Coincide con §9.11 (111 + 2 + 1 = 114). Identidad PASA y control CAIDA.
- `repasar_mutaciones_salida.txt`: identidad PASA, control CAIDA, `L85 ATRAPADA` y `L94 ATRAPADA`. Coincide.
- **L20 es equivalente.** Cambia `regla_posicion(marco + far_t, ...)` por `marco + far`: agrega las `far_ocr`. En
  `regla_posicion` el marco se vuelve a filtrar sin FAR (l. 323), y `err_pos` (l. 257-261) no cuenta nunca una `far_ocr`
  (`E.err` sólo mira pos_bajo y negativos; `far_tabla` es la única FAR en la línea de `pub`), así que `p2_con` ve `ea == er`
  y no suma. La cadena de texto aparece una sola vez (la de `solo_tabla=True` es distinta).
- **La salvedad está dicha con claridad** («las otras 111 no se volvieron a correr ... eso no se midió»). Razonamiento
  propio de que no cambia nada: la prueba nueva sólo toca `LP.curva`, `E.publica` y las funciones de `curva_cenit`, y las
  únicas mutaciones que cambian `curva` son L93 y L94; una mutación atrapada por aserción antes de esa prueba sólo se volvería
  CAIDA si la prueba nueva lanzara una excepción bajo ella, y ninguna de las otras 111 toca esas rutas. Es un argumento, no
  una medición. No re-corrí el nulo completo: cada mutación tarda unos 2 minutos (la batería sola, 5,5 minutos la primera
  vez) y las 114 con dos trabajadores serían unas 2 horas; con un solo proceso pesado a la vez no lo hice.
- **Re-corridas mías** (con las mismas funciones de `mutar_adenda2.py`, batería de 165; salidas en
  `D:/vrp-trabajo/temporales/s168_ver_adenda3/repaso_mio_salida.txt` y `repaso_mio2_salida.txt`): `L94 ATRAPADA`
  («§9.6 curva: si el brazo calla en el cenit alto ...»), `L85 ATRAPADA` («§9.7 regla del paquete ...»), y como muestra de
  las 111 que no se re-corrieron: `L70 ATRAPADA` (MODO_M «informa»), `L77 ATRAPADA` (compuerta de equivalencia),
  `L89 ATRAPADA` (extremo del IC en (d)), `L93 ATRAPADA` (la curva lee V y VK). Seis de seis, ninguna CAIDA. No son las 111;
  son seis.
- **Batería re-corrida** (`python -I probar_adenda2.py`; salida en `D:/vrp-trabajo/temporales/s168_ver_adenda3/bateria.txt`):
  `RESULTADO: 165 de 165`, exit 0, de 19:35 a 19:41 UTC. Coincide con §9.11 y con `probar_adenda2_salida.txt`.

## Lo que no pude comprobar

- No corrí el lector sobre datos reales ni la parte de `main()` con el marco (a propósito); toda la lectura es estática más la
  batería sintética.
- El nulo completo de 114 mutaciones con la batería de 165 (ver arriba): las 111 siguen sin re-medir.
- Que `D:\vrp-trabajo\temporales\s159_n\data_main` y el commit `533398f8f` existan en el equipo del dueño: la batería los usa
  y pasó aquí, que es el mismo equipo.
- Si el run FAR (14 de 14 trabajos, 350 de 350 según la coordinadora) cubre lo que el lector pide: no lo abrí.
- Cuántas `far_tabla` tienen un alertado en la caja C13 y cuántos bloques discordantes tendrá P2-L: eso sale del run.
- El lector de la sombra (no existe): sólo comprobé las dos funciones que ya están (`estado_d_sombra` y las del lector).
