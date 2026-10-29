# Verificador corto: cuerpo de PREREGISTRO_E.md (S162) contra su adenda 2 (S166)

Objeto: `experiments/_s162_v375/PREREGISTRO_E.md` en el tag `s166-v375e-adenda2-sellada` (commit `67838f2a5`). Sólo lectura.
Copias de trabajo (fuera del repo): `D:\vrp-trabajo\temporales\s167_ver_v375e_cuerpo\pre.md` y `...\c\` (evaluar.py,
brazos.py, e_adenda2/leer_posicion_v375e.py, curva_cenit.py, evaluador_comun.py, PREREGISTRO_B/C, objetivos). Las citas de
línea de `pre.md` son las del archivo del tag. Servidor: 2026-10-29.

## Caminos previos (escritos antes de abrir el archivo)

1. §5.4 (veto, "todos los canales") frente a la regla N-3 (§8.13) y frente al "Riesgo conocido" y §7.5, que dicen que
   cambiar la vara es decisión de Nicolás "no de este pre-registro".
2. El §5 del cuerpo escrito para UN paquete P frente a la adenda con TRES brazos: qué brazo se lee, qué hacer con las
   salidas de la regla de posición (RP) que no son "elegido".
3. La vara nueva del paso 1 (§8.6 b) contra §3.1 y §7.3 (¿quedan dos varas vivas?).
4. Las 330 lejanas: ¿entran a lecturas del cuerpo (silencio, MISSION) o sólo a P2-L? ¿Qué ventana y qué peso?
5. Población y pesos: el cuerpo habla de "unión de B y C", "859 pasadas", "pesos de B §3". ¿Es eso lo que lee el lector?
6. Ventanas T, O, O1, O2 (§3.2) frente a lo que corre el lector.
7. Canal que decide (tabla, OCR, unión) por ventana.
8. ¿El lector implementa §4 (controles de cenit, PLACEBO), §5.2 (d, d′), §5.3 (curva) y §5.4 tal como están escritos?
9. Compuertas con "no se sigue" que el lector no hace cumplir.
10. Textos "borrador, pendiente, a decidir" que sobrevivan al sello.

## Veredicto: SELLABLE CON CAMBIOS MENORES

No encontré una contradicción que vuelva inaplicable el cuerpo. Sí encontré (a) dos choques de texto entre el cuerpo y la
adenda (VC167-01 y VC167-02), (b) huecos donde la RP o el §5 no dicen qué hacer y alguien tendría que decidir después de
ver (VC167-03, VC167-04, VC167-05), y (c) texto residual (VC167-06 a 09). Los cinco primeros se arreglan con texto antes
del sello; VC167-04 es el mayor: si no se cierra por texto, sellar deja sin pre-registrar la lectura de magnitud y de
curva del brazo elegido. Nada de esto toca la parte que ya está sellada (la lógica de la RP y N-3 está bien).

## Lo que sí comprobé que concuerda

- `decidir_brazo` (leer:275-292) implementa §8.5 pasos 2 a 4, ciclo incluido (`pre.md` 289-295).
- `err_pos` (leer:253-257) es exactamente el error de posición de §8.5 (`pre.md` 279-281).
- N-3: `no_veta_n3` (leer:308-312) hace lo que dice §8.13. Con los objetivos del tag: las 5 protegidas Suomi NPP sólo OCR que
  K publica (Tupungatito 2026-08-01 y 09-14, Isluga 09-09, 09-28, 10-03) tienen sensor `VIIRS_SNPP`, `alerta_tabla` falso y
  fecha anterior al 2026-10-09; Isluga 2026-06-17 05:06 y Láscar 2026-10-01 05:18 son `VIIRS_NOAA21`, así que siguen
  vetando, como dice `pre.md` 469-471. Hay `pub_prod` 1 en las siete.
- `evaluar.py` del tag tiene el sha256 LF que exige C4 (`2126b743…bc66`). Los sha256 de `objetivos_far_v375.json`,
  `objetivos_run_far_v375.json` coinciden con §8.4 (`a8528424…`, `28468a14…`); `sin_granulo_far_v375.json` está atado al
  primero. La lista run trae 329 far_tabla, 1 far_ocr y 20 de control de vida; por tramo T 117, O1 131, O2 82.
- Tramos de `evaluar.tramo` (T hasta 2026-06-12, O1 hasta 08-28, O2 desde 08-29) concuerdan con B y con §8.4.
- La curva: `curva_cenit.veredicto` implementa el texto de §5.3 (`pre.md` 98-105) sin diferencias.

## Hallazgos

### VC167-01 (gravedad 2): la población y los pesos de la retrospectiva no son los que dice el cuerpo

Cuerpo: §3.1 «859 pasadas con grilla guardada» del lote de B y C (`pre.md` 50-51); §3.2 «unión de B y C … con los pesos de
`PREREGISTRO_B.md` §3» (55-57); §8.5 vara 1 «los pesos de `PREREGISTRO_B.md` §3» (267-268). Lector: `objetivos()`
(leer:207-224) carga además las 1.200 neg_resto de B2 (`b2/objetivos_v375_b2.json`, lote S162b) y las 330 FAR; los pesos
son `N_h / n_ok_h` sobre todo lo cargado (leer:495-496). Con B2 dentro, un estrato como Chaitén z<=40 pasa de peso 143/19
= 7,5 (B §3: «entre 6,8 y 8,5») a 143/71 = 2,0 (B2: «entre 2,72 y 2,83»; el propio §8.5 dice «unas 2», `pre.md` 309-310).
El cuerpo no menciona B2 ni dice que lo cambia. Además B §5.5 (lote S162 solo decide el silencio, la unión confirma) y
B2 (B2 sola decide neg_resto) son reglas de «qué lote decide» heredadas por §5.1 («las de B §5») que chocan entre sí y con
la unión que lee el lector; el cuerpo no elige.
Corrección: una frase en §3.2 y §8.5: «la retrospectiva lee la unión S159 + S162 + S162b (más FAR para la RP); peso
N_h/n_ok_h por estrato; decide la unión, no el lote; la regla B §5.5 y la de B2 no rigen aquí», y reemplazar «859» por el
total real del lector.

### VC167-02 (gravedad 2): §8.5 paso 5 contra §8.7 (qué pasa si cae el control de vida)

§8.5 paso 5 (`pre.md` 296-297): sin run FAR, sin control de vida o más de 10 % de far_tabla SIN DATO, la regla «no decide»
(«NO DECIDE: LAS LEJANAS SIN COBERTURA»). §8.7 (337, 345-346): si cae C7 (control de vida) «sale 3, LECTURA NO LEGIBLE, y no
se lee nada». Código: C7 caído entra a `fallas` (leer:472-473) y `analizar` vuelve antes de la vara 1 (leer:529-530), o sea
no lee ni el marco; «sin run FAR» no es alcanzable por la línea de comandos, porque `--art-far` es obligatorio (leer:625) y
`analizar(..., bool(a.art_far))` recibe siempre verdadero (leer:712). Sólo el 10 % de SIN DATO produce NO DECIDE de verdad
(leer:519). Las dos lecturas dan resultados distintos para Nicolás (sin ningún número del marco, o con todos menos la RP).
Corrección: elegir una y escribirla en las dos secciones (la que hace el código: control de vida caído = no legible).

### VC167-03 (gravedad 2): salidas de la RP y vereditos de las lecturas que el §5.4 no sabe leer

El §5.4 sólo conoce una salida de la RP, «NO RESUELTO» (`pre.md` 311-312). El código y §8.5 producen además «NINGÚN BRAZO
PASA EL VETO», «NO DECIDE: LAS LEJANAS SIN COBERTURA», el ciclo, «SE QUEDA RADIANTE» y la marca A104 con «decide Nicolás»
(leer:275-292, 594-598). Sin regla, quien lea decide después de ver. Del mismo tipo, en los criterios: (b) dice «GANA o
EMPATE (no PIERDE ni BLOQUEA)» pero `regla_signos` también devuelve SIN SUSTRATO con 4 bloques o menos (`evaluar.py`
129-141), muy posible en P2-L si pocas far_tabla tienen alertado en la caja (§8.5 avisa bajo 5, 306-307); (c) tiene la
estructura «MEJORA con d′ MEJORA o, si d no mejora, no EMPEORA», sin decir qué pasa con NEUTRO, SIN SUSTRATO o INDECIDIBLE
(los vereditos de `decidir_estrato`, evaluador_comun:517-565); (d) «el IC de D del paquete queda entero sobre el de K» no
dice si es sobre el extremo superior del IC de K (0,861) o sobre su mediana, ni qué pasa con NULO SESGADO o SIN SUSTRATO
(curva_cenit:155-174).
Corrección: una tabla de cuatro líneas que mapee cada salida a «cumple / no cumple / decide Nicolás» (propuesta: todo lo que
no es explícitamente favorable no cumple, y NINGUN, NO DECIDE y A104 pasan a Nicolás).

### VC167-04 (gravedad 3): el lector no implementa §4 (cenit), §5.2, §5.3, ni los brazos P-def, P-sinfiltro y PLACEBO

El lector corre controles propios (C1 a C7), equivalencia, RP y la vara 1 de `evaluar.py` (P1, P1b, recall, silencio,
MISSION, P2 contra K, y una magnitud que es sólo la mediana de VRP/MIROVA con cuartiles, `evaluar.py` 363-374). Búsqueda en
`leer_posicion_v375e.py`: 0 coincidencias de `curva_cenit`, `evaluador_comun`, `comparar_con_ganancia`, `sesgo_plataforma`,
nulo de cenit o PLACEBO; y `PREREGISTRO_IMPL_V375E.md` §5 (línea 88 de ese archivo) dice «no conecta el evaluador común».
Por eso: (c) del §5.4 (regla D-27 con d y comparador d′, `pre.md` 91-95) no tiene quién lo calcule, (d) tampoco (curva,
nulo de cenit parecido, sesgo de plataforma, ganancia pareja, ganancia que crece con el cenit, `pre.md` 61-78), y los
controles B §4 de control positivo, nulo, NUNCA y PLACEBO no se corren sobre los brazos de la vía. Los brazos P-def,
P-sinfiltro y PLACEBO de §2 (35-41) tampoco aparecen: ni se dice que se descartan ni dónde se leen. La sombra (§3.3) tiene
una función, `distancias_desde_record` (leer:134-143), que no se llama desde `main`.
Lo que el cuerpo deja abierto para §5.2: «por tramo de 10° de cenit, por volcán y por canal» sin decir cuál de esos cortes
decide (c) ni en qué modo (`decidir_estrato` distingue decide, bloquea e informa).
§8.9 (366-367) promete «recién entonces las lecturas del §5 con el brazo elegido»: esa parte tendría que escribirse
sabiendo qué brazo salió de la RP. No es contradicción, pero es el punto donde un pre-registro sellado pierde su valor si
el envoltorio se escribe después de ver.
Corrección: antes del sello, una adenda corta (o un párrafo en §8.9) que fije: el corte y el modo de (c); los campos de
entrada de la curva por brazo; que P-def, P-sinfiltro y PLACEBO se leen con el material de B y C ya existente o quedan
fuera; y que el envoltorio del §5.2 y §5.3 se escribe y se prueba (mutaciones) ANTES de abrir la salida de la RP. Si no se
quiere editar, sellar con la declaración explícita de que esa parte del §5 no está pre-registrada en ejecución.

### VC167-05 (gravedad 2): la compuerta de equivalencia del §3.1 no la hace cumplir el lector

§3.1 (`pre.md` 50-54): si la equivalencia falla «el paquete no es el código y no se sigue»; §8.9 (366-367) ordena controles,
equivalencia, RP, y recién después el §5. En el lector el veredicto «NO EQUIVALENTE» sólo se imprime (leer:455-459); no
cambia el código de salida ni corta la lectura, y sale 3 únicamente por C1 a C7. Tampoco dice qué pasa si la equivalencia
falla para UN brazo (¿se descarta ese brazo o se aborta todo?). La separación de §8.6 a vuelve esto menos probable (la
distancia es idéntica por construcción y sólo el VRP puede separar la publicación), pero el texto no lo cierra.
Corrección: escribir que «NO EQUIVALENTE en cualquier brazo» corta la lectura aquí (o que descarta ese brazo), y decidir si
el lector debe salir con código distinto de 0.

### VC167-06 (gravedad 1): texto de borrador y marcas viejas que sobreviven al sello

- Cabecera (`pre.md` 3-8) «Estado: BORRADOR, sin sellar; depende de PD1, PD3 y del evaluador común»: PD1 y PD3 están
  cumplidas (§7.1, §8.3); el evaluador común, no conectado (VC167-04). Línea 12 «Lo que no es la adenda 2 sigue en
  borrador», y línea 129 (adenda 1) «Sigue en BORRADOR, sin sellar»: hay que decir en qué estado queda el cuerpo.
- Falta una cláusula de precedencia. §5.4 (a) «todos los canales» (110), el «Riesgo conocido» (115-119: cambiar la vara
  «es una decisión de Nicolás … no de este pre-registro») y §7.5 (149-150: «Igual siguen siendo veto») quedan sin marca,
  aunque §8.13 los reemplaza para las protegidas sólo OCR de Suomi NPP anteriores al 2026-10-09. Tampoco se reconcilia
  «todos los canales» con «el canal que decide según la ventana» de C §5.1 (`PREREGISTRO_C.md` 83); en la práctica ya lo
  resuelve `seleccion.py` (14, 98: `pos_prot` sólo con alertas que deciden), pero el texto no lo dice.
- Tabla de verificador (423, 443) y párrafo 448-454 («VE2-07 y VE2-13 quedan abiertos», N-3 «sin aplicar») describen un
  estado anterior al sello; la línea 476 sólo avisa por N-3. Línea 14-15 («caería por 4 protegidas») es el texto previo al
  sello: tras N-3 son 2.
Corrección: una cláusula «donde la adenda 2 contradice el cuerpo, rige la adenda» y marcas «(superado por §8.13)» en esos
puntos.

### VC167-07 (gravedad 1): MISSION no respeta N-3 y se imprime por brazo

`evaluar.lecturas` marca `MISSION_K` «PIERDE PROTEGIDA» con cualquier protegida perdida que K publica (`evaluar.py`
352-353), sin descontar las de N-3; el lector lo imprime por brazo (leer:552-553) junto al P1 con N-3. §5.1 lista MISSION
entre las lecturas, aunque no es criterio del §5.4. Puede mostrarse «PIERDE PROTEGIDA» donde (a) cumple.
Corrección: una frase que diga que MISSION informa y no decide, o que se imprima descontando N-3.

### VC167-08 (gravedad 1): dos «cercano» distintos

En B, C y `evaluar.py` «cercano» es el alertado más cercano al punto de referencia de MIROVA (X0, Y0) y decide en las
lecturas de ROI (`evaluar.py` 9-15, 55; B §2). En la adenda es el alertado más cercano al cráter (`posicion_de`,
`pre.md` 225-231; leer:114-131), mientras X0, Y0 sólo entra en la vara 3. §8.3 reconoce la diferencia para la vía, pero el
mismo nombre en el cuerpo y en la adenda invita a leer mal.
Corrección: llamarlo «cercano al cráter» en §8 y en el reporte del lector.

### VC167-09 (gravedad 1): la sombra con los tres brazos es solo un párrafo

§8.8 (357-359) dice que la sombra lee los tres brazos desde los records con la misma RP, pero la RP exige las far_tabla de la
ventana prospectiva y el cercano de la sombra sale de `anomaly_pixels` redondeado a 0,01 km (frontera inclusiva del radio).
Ninguno de los dos está definido para la ventana P. No bloquea el sello (la sombra empieza el 2026-11-03).
Corrección: una línea que diga que las far_tabla de la sombra se construyen con la misma regla de etiqueta, o que la RP
no se corre en la sombra.

## Lo que no pude comprobar

- No corrí el lector ni la batería (140 de 140) ni el nulo de mutaciones (83 de 84): necesitan artefactos de runs
  (`run_39712862945`, `run_40116289866`, `run_40131572769`) y el run FAR, que no existe aún. Lo dicho sobre el código es
  lectura estática más cálculo sobre los JSON del tag.
- No verifiqué las cifras de §1 y §4 (0,766, 0,778, 0,573, nulo de 37 noches), ni la equivalencia de #921 (289 de 329
  contra 329 de 329).
- No sé cuántas far_tabla tienen un alertado dentro de la caja C13 (lo mide el run FAR). Si son pocas, VC167-03 sobre
  P2-L SIN SUSTRATO se vuelve probable.
- No comprobé que `evaluador_comun` acepte como entrada los records en memoria del lector (sus funciones piden la tabla por
  pasada de records en disco o pares `k, d, m, clave, bloque`); `comparar_con_ganancia` sí acepta pares, así que es
  viable, pero nadie lo cableó.
- Los pesos de VC167-01 los calculé a mano sobre `objetivos_v375_bc.json`, `objetivos_v375_b2.json` y
  `objetivos_portes.json` (los estratos de B2 están todos contenidos en los de la unión B y C), no ejecutando el lector.
