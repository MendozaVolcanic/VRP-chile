# Verificación de PREREGISTRO_B2.md (V375-B2, S162)

- Hora del servidor al empezar: Sat, 24 Oct 2026 19:17:05 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date).
- Commit revisado: `987e4f814` (worktree `s162-viirs375-c1b864`). Modelo: Sonnet 5.5, contexto limpio.
- Carpeta de trabajo y scripts propios: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\b2\verificador\`.
- NO miré: las pasadas reales de B2 (no existen, el lote no se ha corrido); el código de `probe_v375.py` y `brazos.py` ni la física del port (sólo que el workflow y los objetivos sean consistentes); la cobertura del marco contra MIROVA (la tomé de `cobertura_marco.json`, COBERTURA OK); el verificador anterior de V375-B/C más allá de lo citado. Una corrida la hice con datos FABRICADOS (copias de pasadas neg_resto de S162 del mismo volcán, en el scratchpad `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs375-c1b864\3314638d-6b0b-401c-8eb1-92df9921586d\scratchpad\verif\fake1`): sirve sólo para probar el cableado, no dice nada del port.
- Nada editado fuera de mi carpeta. Sin commits, stash, push, workflows ni credenciales. Disco: C: 41 GB y D: 9,7 GB libres (sobre 3 GB).

## En una pantalla

1. El pre-registro se sostiene: B2 son 600 pasadas neg_resto del mismo marco, disjuntas de S159 y S162, el hash de `objetivos_v375_b2.json` se reproduce (`d536e1d8…8017`) y los pesos del conjunto que decide quedan entre 3,29 y 4,25 sin estratos vacíos.
2. El evaluador extendido no cambia nada de lo publicado (JSON idéntico salvo las claves nuevas) y, con datos fabricados, su Wilson sobre S162 + B2 coincide con mi cálculo independiente.
3. La decisión de diseño que más pesa y que el texto no dice con todas sus letras: el conjunto que decide incluye S162, que ya se vio; la lógica sellada (C §5.5) era que decida lo no visto. B2 sola decidiría con ~65 % de probabilidad (con la tasa observada), S162 + B2 con ~93 a 95 %.
4. La «segunda mirada» está sobredeclarada y la lectura estricta no hace lo que dice: la cota de 5 % es de Bonferroni, el error real a la vara mide ~1,2 %, y z = 2,241 no «vuelve a 2,5 %» porque la primera mirada ya se tomó con 1,96. Además deja una zona (~10 %) donde la regla dice ACOTADO y la estricta no, sin instrucción de qué hacer.
5. Tres arreglos baratos antes de sellar: el control de cobertura mira las tres muestras juntas y no B2 sola; omitir `--objetivos-extra` imprime «S162+S162b (DECIDE)» sobre S162 solo; y el bloque de V375-C de la corrida nueva puede cambiar (compuesto por volcán) sin que el texto diga que no se lee.

## Caminos escritos ANTES de leer las salidas (copia de `CAMINOS_ANTES.md`)

C1 muestra no disjunta de S162/S159 o de otro marco. C2 pesos del conjunto que decide mal o estratos fuera. C3 «la misma regla» no es la misma (el conjunto que decide cambia lo que la regla sellada llamaba «lote nuevo»). C4 tamaño con supuestos que no valen (peso parejo, neg_pub fijo, 4 de 389; neg_pub no puede achicarse y la regla nunca decide). C5 inflación por segunda mirada mal declarada. C6 lectura estricta no hace lo que dice. C7 evaluador extendido cambia lo ya publicado. C8 el workflow corre otra cosa. C9 neg_pub/censo contado distinto; neg_resto con otra definición. C10 el hash no reproduce.

## Veredictos por afirmación principal

| # | Afirmación | Veredicto | Grav. |
|---|---|---|---|
| 1 | 600 pasadas neg_resto nuevas, del mismo marco, disjuntas de S159 y S162, semilla 163 | CONFIRMADO | 0 |
| 2 | Pesos de S162 + B2 entre 3,29 y 4,25, ningún estrato sin pasadas | CONFIRMADO (salvedad F7: el peso real se mueve al quitar las no observadas) | 1 |
| 3 | «La misma regla sellada» aplicada a S162 + B2 | CONFIRMADO EN PARTE: misma cuenta, pero se redefine qué lote decide (F1) | 3 |
| 4 | 600 deciden en 95 %; con tasa 2 % ningún tamaño ≤ 1.200 llega a la mitad | CONFIRMADO EN PARTE: 95 % reproducido (93 a 95 %) bajo homogeneidad; lo de 2 % es falso en 1.200 (F3, F6) | 2 |
| 5 | Segunda mirada infla «como mucho al doble» (2,5 a 5 %) | CONFIRMADO EN PARTE: es una cota, el error real es ~1,2 % (F2) | 2 |
| 6 | La lectura estricta (z 2,241) hace lo declarado | CONFIRMADO EN PARTE: el código hace lo que dice (z en neg_resto y neg_pub; 4,49 % y 3,68 % reproducidas); «vuelve a 2,5 %» no es cierto (F2) | 2 |
| 7 | El evaluador extendido no cambia lo publicado | CONFIRMADO | 1 |
| 8 | El workflow corre lo mismo que V375-B | CONFIRMADO | 0 |
| 9 | neg_pub no se achica y toda la mejora debe venir de neg_resto (cota ≤ 2,54 %) | CONFIRMADO; la regla puede decidir (se necesita ≤ 2,54 %, alcanzable) | 0 |

## Hallazgos

**F1. El conjunto que decide reutiliza S162, que ya se vio (gravedad 3, confianza alta).**
`PREREGISTRO_C.md` §5.5 (y `PREREGISTRO_B.md` §5, último punto) dicen que decide el lote que no se vio y la unión confirma; así quedó B en NO RESUELTO. `b2\PREREGISTRO_B2.md` §5.1 cambia «lote nuevo» a S162 + B2 y lo presenta como «la regla sellada, sin cambios». La cuenta es la misma, el principio no. Lo declara en §5.2 como segunda mirada, pero no dice que existe la alternativa fiel (B2 sola decide, S162 y la unión confirman) ni lo que cuesta. Medido con mi simulación (`v_b2sola.py`, `v_potencia.py`): con la tasa observada (1,16 %), B2 sola decide 65 %, S162 + B2 93 a 95 %; con 0,95 %, 81 % contra 98 %. La reutilización compra ~30 puntos de potencia; el texto debería decirlo para que la coordinadora o Nicolás elijan sabiéndolo. Reproducir: `python -I b2\verificador\v_b2sola.py` y `python -I b2\verificador\v_potencia.py`.
Contexto: lo que obliga a gastar B2 es tratar neg_pub como muestra de 113 (cota 36,5 %). Con neg_pub como censo (133, 38 publicadas) el presupuesto de neg_resto sube de 2,54 % a 2,86 % y S162 solo (cota 2,80 %) ya decidía. Eso lo dice el informe del resultado, no este texto, y la coordinadora prohibió cambiarlo; sólo conviene que §1 de B2 lo recuerde.

**F2. La «segunda mirada» está sobredeclarada y la lectura estricta deja una zona sin instrucción (gravedad 2, confianza alta en la medición, media en la lectura).**
(a) `PREREGISTRO_B2.md` §5.2 dice que z = 2,241 «con dos miradas vuelve a 2,5 %». La primera mirada ya se tomó con z = 1,96, así que, aun leyendo la segunda con 2,241, la cota de Bonferroni es 2,5 + 1,25 = 3,75 %, no 2,5 %. (b) La cota ni siquiera es la medida: `v_alfa.py` simula con el total exactamente en la vara (3,85 %) y neg_pub verdadera de 20, 30 y 40 %: P(declarar ACOTADO en la primera o la segunda mirada con la regla normal) = 1,15 %, 1,15 % y 0,78 %; con la estricta 0,85 %, 0,87 % y 0,52 %. La regla (suma de dos cotas de 95 %) ya es muy conservadora y la inflación real es ~1 %. (c) `v_potencia.py`: a la tasa observada la regla normal decide en 93 % y la estricta en 83 %; hay ~10 % de casos (15 % si la tasa es 1,4 %) donde la regla dice ACOTADO y la estricta NO RESUELTO. El texto sólo promete decirlo «en la primera línea»; no dice qué se concluye para PD1 y V375-E en ese caso. Con datos fabricados el caso aparece (`f1.txt` líneas 80 y 81: estricta 0,0392 NO RESUELTO, regla ACOTADO). Sugerencia (no la aplico): bajar el texto a «es una cota gruesa, el error medido es ~1 %», o fijar de antemano que ACOTADO con estricta NO RESUELTO se informa como «ACOTADO, no a prueba de segunda mirada».

**F3. La potencia del 95 % supone una tasa homogénea; los eventos de S162 están concentrados (gravedad 2, confianza media).**
Los 4 eventos de S162 son Lastarria z>40 (dos: ids 1562 y 1704), Tupungatito z<=40 (1189) y Llaima z>40 (1473), con VRP de 0,05, 0,013, 0,010 y 0,012 MW. Lastarria z>40 tuvo 2 eventos en 10 pasadas (2 de 12 en Lastarria). `tamano_b2.py` simula binomial parejo sobre el total. Con la cuenta por estrato (`v_potencia.py`, que replica 0,01156 y 0,02805 de S162): si Lastarria publicara 20 % y el resto 0,95 %, la potencia de S162 + B2 baja de 0,98 a 0,64; con el resto en 1,16 %, a 0,49. Es sospecha de heterogeneidad con 2 eventos en 12 pasadas, no un hecho; el peso de Lastarria en el marco es 118 de 3.323 noches. No cambia el diseño, pero «95 %» es el techo y no la expectativa.

**F4. El control de cobertura no es de B2 sino de las tres muestras juntas (gravedad 2, confianza alta).**
`PREREGISTRO_B2.md` §4: pasadas con estado ok contra las 600, y si son más del 10 % de no observadas la lectura se informa y no decide. `evaluar.py:589-593` calcula `n_s / n_c` por clase sobre todos los objetivos (S159 + S162 + B2 = 1.045 neg_resto): B2 podría perder hasta ~93 de 600 (15,5 %) sin que salte el AVISO (11 ya perdidas en S162 más 93 son 104 de 1.045, justo el 10 %). Con B2 sin artefactos el AVISO sí salta (611 de 1.045, `x.txt` líneas 11 a 13), pero es otro caso. Arreglo barato: calcular la cobertura también por lote y hacer que el AVISO la mire.

**F5. Una invocación incompleta imprime «S162+S162b (DECIDE)» sobre S162 solo (gravedad 2, confianza alta, reproducido).**
`evaluar.py:794-796`: `f162 = repesar([x ... if x["lote"] in a.deciden], meta)` y la etiqueta sale de `a.deciden`, sin comprobar que cada lote pedido tenga filas. Si se pasa `--deciden S162 S162b` y se olvida `--objetivos-extra`, la salida dice «lotes S162+S162b (DECIDE) (698 pasadas ...)» sin AVISO (`mal.txt` línea 77). El comando completo tampoco está escrito en `PREREGISTRO_B2.md` (§5.1 menciona sólo `--deciden`). Conviene fijar la línea de comandos en el pre-registro y un `assert` de que cada lote de `--deciden` tiene pasadas ok.

**F6. «Con 2 %, ningún tamaño de hasta 1.200 llega a la mitad» es falso en 1.200 (gravedad 1, confianza alta).**
`b2\tamano_b2_salida.txt`, fila `tasa real 0.0200`: 400: 0,45; 600: 0,46; 800: 0,46; 1000: 0,48; 1200: 0,55. En 1.200 pasa la mitad. Mi simulación con pesos da 0,45 para 600. No cambia la decisión de 600.

**F7. Los pesos «entre 3,29 y 4,25» son el diseño, no lo que verá el evaluador (gravedad 1, confianza alta).**
El evaluador re-pondera entre las pasadas ok: con ~2,75 % de no observadas (11 de 400 en S162) y estratos chicos (Isluga z<=40 tendrá 4 pasadas), el peso real puede subir (una pasada menos en ese estrato lo lleva de 4,25 a 5,67). Efecto en el n efectivo de Kish: despreciable (988 de 989 en mi corrida fabricada). Sólo se anota.

**F8. Formalmente son tres miradas, no dos (gravedad 1, confianza alta).**
Quedaron NO RESUELTO la de S159 (0 de 45, cota 8,5 a 10,4 %) y la de S162; B2 es la tercera. La de S159, con n = 45, no podía declarar ACOTADO nunca (poder ~0), así que el efecto es nulo; basta decir «dos miradas efectivas».

**F9. Cambios cosméticos en la salida por defecto (gravedad 1, confianza alta).**
Sin B2, el evaluador imprime «lotes S162 (DECIDE)» donde antes decía «lote S162 solo (DECIDE)», y la clave del JSON sigue llamándose `decision_s162` aunque contenga S162 + B2. Los números son idénticos (comparé mi corrida base contra `resultado_run40116289866\evaluar.json`: sólo difieren las claves nuevas `B_estricto`).

**F10. El bloque de V375-C de la corrida nueva puede cambiar y el texto no dice que no se lee (gravedad 2, confianza media).**
El conjunto que decide pasa a incluir 600 negativos más, que entran en P2, en el brazo global y en el compuesto por volcán. En mi corrida con datos fabricados (`f1.txt` línea 90) el compuesto por volcán pasó de {Puyehue: C13, Tupungatito: C13} a {Llaima: PIX7, Puyehue: C13, Tupungatito: C13} y M13 entró a los candidatos. Es un artefacto de mis copias fabricadas, pero el mecanismo es real. `PREREGISTRO_B2.md` §7 dice que no decide nada de V375-C; convendría añadir «el bloque de C de esta corrida no se lee; vale el publicado en `resultado_run40116289866`».

## VERIFICADO LIMPIO (y contra qué vara)

- Disjunción y marco (vara: mi script `v_disjunto.py` contra `poblacion_completa.json`, sha `c08602de…`): 600 de 600 en la población, todas `decide`, negativo limpio, `pub_prod` 0 (neg_resto), ninguna en los días excluidos (12, 13, 17 a 20 de octubre); 0 pares (volcán, hora) en común con S159 ni con S162 (de ninguna clase); ids 3000 a 3599 sin choque; sin duplicados; 0 de 600 a 10 minutos o menos de una neg_resto previa del mismo volcán (252 de 600 a 24 h o menos, lo esperable en noches consecutivas).
- Estratos y pesos (vara: `v_pesos.py`, recomputo desde cero): N por estrato de la población coincide con `meta` de S162 (22 estratos, 3.323); `estrato` de B2 consistente con volcán|cenit; pesos de S162 + B2 de 3,29 a 4,25; ningún estrato vacío (en S162 solo, Isluga z<=40 tenía 0).
- Reproducción de la selección: `re_seleccion_b2.py` (copia de `seleccion_b2.py` con rutas ajustadas y salida a mi carpeta) da `d536e1d895aad9274a9475090f09a405dabf2e0f87d45877370b2cdda6a38017`, igual al del pre-registro, `cmp` byte a byte idéntico. Tramos T 187, O1 243, O2 170, 18 partidas, 442 gránulos, 2.878 sin medir: todo igual a lo declarado.
- Aritmética de §3 (vara: `tamano_b2.py` y su salida): vara 133/3.456 = 3,85 %; cota de neg_pub 0,3652 (la Wilson cruda de 31/113 da 0,3630; la diferencia es el n efectivo de Kish) ocupa 48,6 de 133; cota necesaria de neg_resto 2,541 %. Mi réplica con pesos reproduce 0,01156 y 0,02805 de S162.
- Evaluador extendido (vara: `resultado_run40116289866\evaluar_salida.txt` y `evaluar.json`): la corrida sin B2 difiere sólo en la línea nueva `B estricto` y en la etiqueta; JSON idéntico salvo las claves `B_estricto`. La corrida de las instrucciones (con `--objetivos-extra` y `--deciden S162 S162b`, B2 sin artefactos) da los mismos números de S162 (698 pasadas) y marca 600 `sin_resultado`. ~3 min.
- Lectura estricta, valores ya vistos (vara: `base.txt`): S162 solo 4,49 % NO RESUELTO; unión S159 + S162 3,68 % ACOTADO. Coinciden con §5.2.
- Cableado con datos fabricados (`v_fake.py` + `v_indep.py`): neg_resto [14, 989], pond 0,01432, Wilson [0,00857; 0,02383], coincide al dígito con mi cálculo independiente.
- Workflow (vara: `diff probe-s162-v375.yml b2\probe-s162-v375-b2.yml`): sólo cambian nombre, rama de disparo, grupo de concurrencia, ruta de OBJETIVOS, 24 trozos de 25 (600/24), `--nchunks 24` y el nombre del artefacto. Mismo `pipeline` (`git diff 533398f8f ca034d66e -- pipeline` vacío). Esquema de claves de los objetivos de B2 idéntico al de S162 (diferencia simétrica vacía).
- Costo: 600 × 25 s = 4,2 h; artefactos ~70 MB (mis copias fabricadas pesaron 73 MB).

## SIN DATO

- Qué hará el port en las 600 pasadas: no están corridas.
- Heterogeneidad real del port por volcán (F3): con 4 eventos sólo es sospecha.
- Si los 442 gránulos siguen bajándose de NASA hoy: no probé la red ni usé credenciales.
- Si `ca034d66e` más la rama de disparo y los archivos de `b2\` reproducen el runner en Actions: no despaché nada.
- La gravedad de F1 depende de qué lote quiera la coordinadora o Nicolás que decida; yo sólo mido el costo.

Scripts y salidas en `b2\verificador\`: `v_disjunto.py`, `v_pesos.py`, `re_seleccion_b2.py`, `v_potencia.py`, `v_b2sola.py`, `v_alfa.py`, `v_fake.py`, `v_indep.py`, `base.txt`, `x.txt`, `f1.txt`, `mal.txt`, `CAMINOS_ANTES.md`.
