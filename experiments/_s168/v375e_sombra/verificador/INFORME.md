# Verificador limpio del lector de la sombra de V375-E

- Objeto: `experiments/_s162_v375/PREREGISTRO_E.md` §11 (con §3.3, §5.4, §9.7, §9.8, §9.12, §10) y
  `experiments/_s168/v375e_sombra/{leer_sombra_v375e.py, probar_sombra.py, mutar_sombra.py}`.
- Commit medido: `c44665603` (rama `claude/s168-v375e-sello`). Dependencias selladas comprobadas contra el tag
  `s168-v375e-cuerpo-sellado` (sha256 LF de `leer_posicion_v375e.py`, `evaluar.py`, `curva_cenit.py` y
  `evaluador_comun.py`: los cuatro idénticos a los de `SHA_DEPS`, comprobado con `git show <tag>:ruta | sha256sum`).
- Hora de servidor: inicio 2026-10-30 01:14 UTC, fin 2026-10-30 01:26 UTC (`date -u`).
- Modelo: Sonnet 5.5 (claude-sonnet-5-5), contexto limpio.
- No abrí datos de `data/sombra_codigo_mirova/` (no existen en este árbol) ni records de `data/mirova_equivalent/` del
  2026-11-03 en adelante. Sólo corrí la batería. No corrí el nulo de mutaciones.

## Caminos previos (escritos antes de abrir §11 y el código)

1. El control caído imprime o escribe igual la población (resumen previo, detalle de los controles, JSON parcial).
2. Un control se calcula después de un paso que ya imprimió.
3. Borde del radio: pasadas justo en el límite caen a un lado distinto según `<` o `<=`, o según la distancia redondeada.
4. Los controles de la curva caen y (d) igual decide.
5. Mitades en lugar de A104: partición por fecha equivocada, mitad vacía sin significado escrito.
6. La parada medida sobre otra población, o sin regla de qué corte decide.
7. Radiante entra por alguna vía al veredicto.
8. Pesos de censo distintos a la retrospectiva sin decirlo.
9. Pareo, regla de mínimas, diurnas, lectura A y magnitud de K con definiciones distintas a la retrospectiva.
10. `sin_grilla` y Suomi NPP tratadas distinto.
11. Claves de brazo que no calzan con `evaluar.py` o `curva_cenit.py` y devuelven vacío leído como cero.
12. Salidas sin significado escrito (población vacía, mitad vacía, n pequeño, empate, NaN).
13. Batería con aserciones tautológicas o fixtures que no ejercen la rama.
14. Dependencia del reloj o lectura de datos prohibidos.
15. Reproducibilidad (orden de dicts, semillas, directorio de trabajo).

Lo que cada camino dio está en los hallazgos. Los caminos 7, 8 (con la salvedad de VS168-14), 10, 11, 14 y 15 no dieron
nada: radiante sólo entra a `out["brazos"]` y nunca a `estado_final` (l. 349 a 355 usa sólo `DECIDE`); los pesos son
1 en `filas_de` (l. 255); las claves `("VIA", "cercano")` coinciden con las de `E.armar`; el lector no lee el reloj para
decidir (sólo lo imprime en la procedencia).

## Veredicto: SELLABLE CON CAMBIOS

Hay un hallazgo de gravedad 3 (VS168-01: el texto no fija qué corte decide ni la fecha de inicio, y el código deja a
quien lee elegirlos después de ver salidas provisionales). Es de texto más unas pocas líneas de código y no invalida el
diseño. Con VS168-01 cerrado y los de gravedad 2 resueltos o aceptados por escrito por Nicolás, es sellable. La batería
sale 104 de 104.

## Hallazgos

### VS168-01 (gravedad 3): quién elige el corte que decide y la fecha de inicio queda para después de ver

Evidencia.
- `leer_sombra_v375e.py` l. 460 (`--desde` con defecto 2026-11-03) y l. 191 (`control_s1`: `desde >= DESDE_P`). S1
  sólo exige que el inicio no sea anterior al 2026-11-03: un `--desde 2026-11-10` pasa S1 y recorta las primeras noches
  sin que nadie lo vea. La batería prueba `desde` anterior (cae) y `desde` igual (pasa), nunca posterior.
- `--hasta` (l. 459) es libre y §11.8 sólo dice que antes de la parada la salida se rotula «PROVISIONAL, no decide». No
  dice cuál corte, una vez alcanzada la parada, es el que decide: el primero que la cumple, el último, o cualquiera.
  El lector imprime el estado completo (`CUMPLE` o `NO CUMPLE`) en cada corte, antes y después de la parada. Si se lee
  cada día, se puede detener la lectura en el primer corte con CUMPLE (o seguir hasta que aparezca). §3.3 dice «hasta 30
  noches o 40 alertas», o sea que la ventana termina en la parada, pero el código no corta ahí: si se corre con un
  `--hasta` posterior, lee todo.
- Cada corte se escribe con `Path(a.salida).write_text` (l. 506) y `--json`: un corte nuevo pisa al anterior si se
  reutiliza la ruta, contra «no se borra: un corte nuevo se agrega al lado» (§11.8). Nada registra cuántos cortes se
  corrieron.

Por qué es 3: el texto deja la elección de la ventana que decide para después de ver salidas provisionales.

Corrección propuesta.
1. S1 exige `desde == 2026-11-03` (igualdad), y se quita `--desde` o se deja sólo para la batería.
2. Texto en §11.8: «El corte que decide es la lectura que termina en la noche en que se alcanza la parada (la primera
   noche N con 30 noches y 40 alertas acumuladas). El lector la calcula y, si `--hasta` es posterior, lee sólo hasta N
   e informa que recortó. Cortes anteriores a N son PROVISIONAL y no se usan para parar antes.»
3. El lector se niega a escribir sobre una `--salida` o `--json` que ya existe (como hace `objetivos_far_v375.py` con
   las salidas de otra corrida), y cada corrida agrega una línea (hora, `--hasta`, sha de la referencia y estado) a un
   registro que no se sobrescribe.
4. Batería: `--desde 2026-11-10` cae por S1; `--hasta` posterior a N se recorta; la escritura sobre un archivo
   existente se rechaza.

### VS168-02 (gravedad 2): con un control caído el lector sí imprime y escribe composición de la población

Evidencia.
- `reporte_controles` (l. 398 a 401) imprime `v['detalle']` de cada control, caído o no. El detalle de S7
  (`control_s7`, l. 238 a 247) es `{clase: {n, sin_dato, lista}}`: cuántas pasadas hay de `pos_prot`, `pos_bajo`,
  `neg_pub`, `neg_resto`, `far_tabla` y `far_ocr`, y los nombres (volcán y hora) de las que no tienen record de la vía.
  S3, S4 y S5 imprimen además `n` y listas de horas. El mismo `detalle` va al `--json` (l. 507 a 509: se escribe
  `controles` completo).
- §11.4 dice: «no se imprime ni se escribe nada de la población», y el traspaso (punto 5) dice «sin imprimir nada del
  marco». Los tamaños por clase y los nombres de las pasadas son composición del marco (el número de protegidas, por
  ejemplo, es justo lo que decide si se alcanza la parada).
- La batería (probar_sombra.py, «main VA168-01») comprueba sólo que no aparezcan las cadenas «== población», «==
  cercano» y «PAQUETE». No aserta nada sobre el detalle de los controles.

Corrección propuesta. Con un control caído, imprimir y escribir sólo «S_ CAE» y una causa corta sin conteos por clase ni
listas (por ejemplo, «cobertura por encima del 10 % en una clase de las que deciden»). El detalle completo se escribe
sólo cuando no cae ninguno. Batería: con S7 caído, la salida no contiene los conteos de `pos_prot` ni nombres de
pasadas.

### VS168-03 (gravedad 2): una protegida SIN DATO que K publica desaparece de P1 sin avisar

Evidencia. `control_s7` tolera hasta 10 % de SIN DATO en cada clase, `pos_prot` incluida (l. 245: `> UMBRAL_COBERTURA`, con
4 de 40 pasa). Las SIN DATO no entran a `filas` (`brazos` las deja fuera de `arms`, `filas_de` sólo toma ids de
`arms`), así que (a) no las ve. La batería lo fija como comportamiento esperado («una protegida sin dato en 13 (7,7 %)
no cae»). §5.4 (a) y §9.7: «ninguna protegida que K publica» puede perderse. Una protegida que K publica y la vía no
tiene record (workflow de la sombra caído esa noche, gránulo que la vía no cubre) cuenta como cero pérdidas.

Corrección propuesta. Toda protegida SIN DATO se lista por nombre en la salida, y si K la publica, el estado no puede
ser CUMPLE (pasa a DECIDE NICOLÁS, o umbral 0 en S7 para `pos_prot`). Texto en §11.4 y §11.7.

### VS168-04 (gravedad 2): ni el régimen de código de la ventana ni los módulos de etiquetado están identificados

Evidencia.
- §11.6 afirma que la ventana P es «un solo régimen». Nada lo comprueba. Cada record trae
  `regimen.codigo_sha` (`pipeline/store.py` l. 89 a 94, 549), que es el commit de `main` al escribirlo: en
  `data/mirova_equivalent/Lascar.json`, los records del 2026-10-20 en adelante traen al menos 5 `codigo_sha` distintos
  en 8 días. Si entre el 2026-11-03 y la parada entra un cambio a `pipeline/` (producción o la vía), la ventana mezcla
  dos detectores sin aviso (A104, A155).
- S0 (`SHA_DEPS`, l. 45 a 50) identifica sólo los cuatro archivos del tag. El lector usa además, sin identificarlos,
  `scripts/banco_paridad.py`, `clase_mirova.py`, `referencia_mirova_unificada.py`, `auto_audit_weekly.py` (pasadas
  diurnas descartadas) y `frontend/index.html` (el predicado, que `banco_paridad.HTML` toma del árbol donde se corre),
  y el propio `leer_sombra_v375e.py`. Corrido desde otro commit de `main`, las etiquetas y el predicado pueden cambiar
  sin que S0 lo note.

Corrección propuesta. S0 agrega el sha256 de esos módulos y de `frontend/index.html` (o exige correr desde el checkout
del tag del lector e imprime `git rev-parse HEAD`). Control nuevo S8: los `codigo_sha` distintos de K y de la vía se
listan, y se exige que `git diff --stat` entre el primero y el último sobre `pipeline/`, `pipeline/profiles/` y
`frontend/index.html` sea vacío; si no, la salida se rotula con el cambio y (b), (c), (d) pasan a DECIDE NICOLÁS.

### VS168-05 (gravedad 2): la referencia se congela por corte, pero el texto no dice qué pasa con filas que MIROVA o el scraper pierden entre cortes ni con el rezago del último día

Evidencia. `referencia_mirova_unificada.py` l. 166 y 167 documenta que existen «filas que la historia de Mirova-v1 tuvo y
perdió». El lector apaga justo esa capa (l. 479: `respaldo_path=None, historico_path=None`) con el argumento de que es
anterior a la ventana; eso vale para el archivo recuperado, no para las filas que se pierdan DENTRO de la ventana. Una
alerta que desaparece del consolidado pasa a `sin_info` y sale de la población: puede desaparecer un veto de (a) o
cambiar la cuenta de la parada. Además `--hasta` puede ser el día de hoy, con la tabla y el OCR todavía incompletos
(el OCR llega con rezago): una pasada puede quedar `neg_limpio` porque su alerta del OCR no llegó.

Corrección propuesta. Cada corte guarda su referencia, y el siguiente la une por clave con las anteriores (capa
prospectiva «vista en cortes previos»), o el texto acepta por escrito que un corte posterior puede cambiar etiquetas y
manda comparar cortes. Y el lector exige `--hasta` menor o igual al último día completo de la referencia menos uno.

### VS168-06 (gravedad 2): (c) SIN SUSTRATO da NO CUMPLE automático, y §5.4 dice que sin sustrato en la sombra decide Nicolás

Evidencia. `estado_c` (lector sellado) manda SIN SUSTRATO a NO CUMPLE, y §11.7 llama NO CUMPLE a cualquier criterio que no
cumple. §5.4, última frase: «Si la retrospectiva cumple y la sombra no tiene sustrato a las 30 noches, la decisión es de
Nicolás con lo que haya». Con pocos pares en (c) (menos de 5 pares o 3 noches, `evaluador_comun.decidir_estrato` l.
523), el lector imprime NO CUMPLE aunque nada empeore. §9.7 dice que las salidas que el §5.4 no previó pasan a Nicolás, y
éste sí lo previó.

Corrección propuesta. En §11.7: con la parada alcanzada, (c) SIN SUSTRATO es DECIDE NICOLÁS (no NO CUMPLE), salvo que otro
criterio ya sea NO CUMPLE. O escribir que §9.7 prevalece sobre la última frase de §5.4.

### VS168-07 (gravedad 2): los controles de la curva se calculan sólo para el brazo, y (d) depende de la curva de K

Evidencia. `controles_curva` (l. 264 a 287) arma `pas` con `x["V"].get(a)` del brazo. §11.6 dice «sobre las pasadas con
alerta de MIROVA del brazo y de K». `estado_d_sombra` exige que la curva de K no sea SIN SUSTRATO ni NULO SESGADO, y su
rama «supera a K» compara el IC del brazo con el de K, pero el sesgo de plataforma, la ganancia pareja y la ganancia que
crece con el cenit de K nunca se calculan. Un sesgo de plataforma en K invalida la comparación igual que uno en el
brazo.

Corrección propuesta. Correr `controles_curva(marco, "K", ...)` y exigirle lo mismo que al brazo (si cae, (d) pasa a
DECIDE NICOLÁS), o corregir el texto para que diga «sólo del brazo».

### VS168-08 (gravedad 2): la batería no ata el cableado de los criterios (b), (c), (d) ni S6

Evidencia (grep del archivo y lectura completa de la batería).
- En la escena principal (`analizar` con 12 noches) sólo se aserta `criterios["a"]` de radiante y de cercano. Para
  `criterios["b"]`, `["c"]`, `["d"]` y `["estado"]` no hay aserción de valor: «estado del paquete es el de cercano»
  compara el campo consigo mismo (`res["estado"] == br[DECIDE]["criterios"]["estado"]`, y `estado_final` sólo lo
  reencamina si hay borde). La línea de `leer_brazo` que arma `criterios_sombra(veta, p2k["veredicto"], silencio,
  p2l["veredicto"], LP.estado_c(...), cae_curva, LP.estado_d_sombra(...))` (l. 333) es posicional: se puede cruzar
  `p2k` con `p2l`, o `est_c` con `est_d`, o pasar `False` a `cae_curva`, y ninguna aserción lo ve.
  `criterios_sombra` en sí se prueba con valores fabricados, bien, pero eso no prueba que `leer_brazo` le pase lo que
  corresponde.
- S6 (`control_placebo_m`, l. 376) no tiene prueba en ninguna dirección: no hay línea con «S6», «placebo» ni
  «control_placebo_m» en `probar_sombra.py`. Además pasa en vacío: con menos de 5 pares o 3 noches,
  `decidir_estrato` da SIN SUSTRATO, que no es MEJORA, y S6 queda OK sin haber probado nada (a diferencia de S5, que sí
  exige al menos un caso). Es el mismo defecto que VA168-07 señaló para C8.
- No hay prueba de la rama `hay_neg` falso (sin `neg_pub` o sin `neg_resto`): el texto la define en §11.6 («SIN SUSTRATO»
  y (b) se lee sin él) pero ninguna escena la ejerce.

Corrección propuesta. Una escena con valores conocidos de P2, silencio, M y curva donde el estado esperado de cada
criterio y del paquete se aserta por valor (idealmente un caso NO CUMPLE por (b) y otro por (d)); una escena con
`neg_pub` en cero; una prueba de S6 en rojo (placebo que da MEJORA) y en verde con al menos un par; y que S6 informe
cuántos pares usó (si son 0, decirlo, como pide VA168-07 para C8).

### VS168-09 (gravedad 1): el borde sólo se prueba con una vuelta conjunta

`estado_final` (l. 349) y `brazos(..., flip=...)` dan vuelta todas las pasadas de borde a la clase contraria, o sea todas
a `far` (en datos reales el cercano redondeado es igual al radio, que es «summit»). Una protegida de borde vuelta a `far`
veta, y eso se ve. Pero el peor caso para (b) es mixto (positivas de borde a `far` y negativas de borde en `summit`) y no
se calcula. Con pocas pasadas de borde es de bajo impacto. Corrección: evaluar también el escenario mixto adverso, o
decir en §11.5 que sólo se mira la vuelta conjunta.

### VS168-10 (gravedad 1): S4 puede caer por redondeo y dejar la lectura ilegible

`control_s4` (l. 218 a 222) recalcula la clase de radiante con `centroid_dist_km`, que la vía redondea a 3 decimales
(`mirova_v750_codigo.py` de `origin/main` l. 738, `round(dcen, 3)`), mientras que `distance_class` del record salió de `dcen` sin
redondear. Si `dcen` cae entre el radio y el radio más 0,0005 km, el redondeo da exactamente el radio, `clase_dc` dice
summit y el record dice far: S4 cae y la lectura es ilegible. El lector sellado lo evitaba con `TOL_DIST_KM` (l. 71, usado en C5, l. 599). Probabilidad
estimada chica (del orden de 1 % sobre unos cientos de pasadas con alertados; SIN VERIFICAR con datos). Corrección:
excluir de S4 las pasadas con `|radiante - inner| <= 0,0005` y listarlas.

### VS168-11 (gravedad 1): pasadas con alertados sin distancias se tratan como «no publica» sin contarlas

`brazos` (l. 163 a 169): si `distancias_desde_record` da `None` con alertados (falta `primary_cluster`, `hotspot_dist_km`
o algún `dist_km`), cercano y radiante quedan en `(False, 0.0, npix)` sin contarlo ni listarlo, y S3/S4 las ignoran.
Con el código de la vía actual no debería ocurrir (si hay alertados siempre trae cúmulo y pico), pero si ocurre es una
pérdida silenciosa. Corrección: contar estas pasadas, listarlas, y que su número sea un control (debe ser 0).

### VS168-12 (gravedad 1): cosas que la retrospectiva informaba y la sombra no

(a) `partida` se fija en `False` (l. 127): la retrospectiva marcaba las pasadas partidas (`01_poblacion.py` l. 88 a 106 y 114) y las informaba aparte (`evaluar.py` l. 906). (b) `B.alertas_sin_record` (alertas de MIROVA sin record de K) no se
llama: una alerta sin record de K es invisible para P1 y para la parada, y la retrospectiva la imprimía como cobertura
aparte. (c) `far_ocr` se cuenta por clase pero sus lecturas (`lecturas_far(...)["far_ocr"]`) no se imprimen, aunque §11.2
dice que informa. (d) Las listas «por nombre» se truncan a 10, 15 u 20 en pantalla. Corrección: informar (a) a (c) con
una línea cada uno y escribir las listas completas en el JSON.

### VS168-13 (gravedad 1): radiante y P-sinfiltro imprimen un `estado` que se lee como veredicto

`reporte` (l. 401 a 434) imprime `criterios: {...'estado': ...}` también para radiante y P-sinfiltro. §10 dice que la línea
de radiante «no decide nada». El rótulo de la cabecera lo dice, pero el estado calculado queda al lado de ese bloque.
Corrección: para los brazos que informan, no imprimir `criterios` ni `estado`, sólo las lecturas.

### VS168-14 (gravedad 1): `--commit` opcional, referencia sólo por ruta, mitades sin consecuencia

§11.1 dice que el lector «recibe y escribe» el commit y que la referencia es «bajada por el lector o pasada por ruta»:
`--commit` tiene defecto `None` (se imprime «None») y no hay descarga (`--cons` y `--ocr` son obligatorios). Las mitades
informan por texto, así que si discrepan no pasa nada, a diferencia de A104 en la retrospectiva (que mandaba a Nicolás);
está dicho en §11.6, pero conviene que §11.7 lo repita. Corrección: `--commit` obligatorio, y precisar el texto de la
referencia.

## Código contra texto (resumen de lo comprobado y bien)

| Promesa | Dónde | Resultado |
|---|---|---|
| Cercano decide, radiante y P-sinfiltro informan, pico no se lee | `DECIDE`, `INFORMAN` (l. 39 a 42); `estado_final` sólo usa `DECIDE` | Bien |
| Cercano = menor `dist_km` del record; radiante = `centroid_dist_km` | `LP.distancias_desde_record` (sellado l. 138 a 148) | Bien |
| La vía publica por el predicado del tablero con node, vía `store.append_record` no filtra | `publicar` (main) = `B.correr_node`; store l. 357, 362, 401 y 455 de `origin/main` | Bien |
| Controles se calculan antes de imprimir población | `analizar` l. 363 a 383 corta con `fallas` antes de `paquete` | Bien en orden; mal en lo que imprime (VS168-02) |
| S0 carga nada si un sha no calza | `cargar_deps` l. 78 a 90 | Bien (y los cuatro sha coinciden con el tag) |
| S1 a S7 como en §11.4 | l. 188 a 247 | Bien, con VS168-01, 03, 10 |
| Borde < 0,005 km, regla inclusiva, vuelta conjunta, DECIDE NICOLÁS si cambia | l. 181 a 185, 349 a 355 | Bien con VS168-09. El único caso real de borde es cercano redondeado igual al radio (radios enteros, dist a 0,01 km) |
| (a) toda protegida perdida veta (sin RP, sin pérdidas comunes) | `leer_brazo` l. 327 | Bien |
| (b) P2 contra K, silencio, P2-L; SIN SUSTRATO si faltan clases de negativos | `leer_brazo` l. 323 a 333 | Bien |
| (c) M con `decidir_estrato` modo «decide»; A104 reemplazado por mitades que informan | `LP.magnitud`, `mitades` | Bien. En la ventana P `a104` da vacío porque todos los records son O2 |
| (d) curva condicionada decide; controles de la curva llevan (d) a DECIDE NICOLÁS | `controles_curva`, `criterios_sombra` | Bien para el brazo; K sin controles (VS168-07) |
| Mitades: la noche de la mediana va a la primera | `mitades` l. 290 a 300, `(len-1)//2` | Bien |
| Parada: 30 noches y 40 alertas (pos_prot y pos_bajo con dato) | `parada` l. 357 a 360 | Bien. Sin regla de qué corte decide (VS168-01) |
| Suomi NPP fuera y contado | `poblacion` l. 107 a 110 | Bien |
| Solo la vía (`is True`), sólo VIIRS 375, sólo la ventana | `cargar_records` | Bien. `sin_grilla` queda SIN DATO |
| N-3 no toca ninguna fila en la ventana | `LP.no_veta_n3` con hora >= 2026-10-09 | Bien |

## Fidelidad con la retrospectiva

Iguales: pareo a 120 s (`B.parear`, `TOL_S`), regla D-9 en SN (`regla_minimas="SN"`), protegida lectura A
(`alerta_protegida`), clases (`clase_de` coincide con `seleccion.py` l. 55 y 56 y con `objetivos_far_v375.py` l. 83 a 85),
descarte de pasadas diurnas (`B.cargar_nuestros`), K = lo que publica el tablero sobre el record de producción, magnitud de
K = `disp` del predicado (igual a `vk_rerun` del lector sellado), inner leído de `index.html` (coincide con
`volcanoes.yaml` en los 11, comprobado). Diferencias dichas en §11: pesos 1 (censo), sin capas locales de la referencia, sin
Suomi NPP. Diferencias NO dichas: `partida` y alertas sin record de K (VS168-12); cenit tomado de
`sensor_zenith_deg` del record de K (el sellado usaba `geometria_centro.sensor_zenith` del run; ambos son el píxel más
cercano al centro, SIN VERIFICAR que coincidan); `E.lecturas` aplica Wilson a `neg_resto` como si fuera muestra aunque aquí
es censo (más conservador para detectar ENCIENDE DE MAS que un conteo exacto, y la función sellada se usa sin cambios;
informativo, no pasa nada si el texto lo reconoce).

## Lo que el texto deja abierto (salidas sin significado escrito)

1. Qué corte decide y desde cuándo se lee (VS168-01).
2. Protegida SIN DATO que K publica (VS168-03).
3. (c) SIN SUSTRATO con la parada alcanzada, contra la última frase de §5.4 (VS168-06).
4. Cambio de régimen de código dentro de la ventana (VS168-04).
5. Filas de la referencia perdidas entre cortes (VS168-05).
6. `neg_pub` en cero: (b) se lee sin silencio y, si además P2 tiene 4 bloques o menos, (b) cumple sin que se haya medido
   la sobrepublicación de la vía en negativos limpios. Está dicho en §11.6 («SIN SUSTRATO»), pero no que eso, junto con
   P2 sin sustrato, sea un CUMPLE de (b) por falta de evidencia. Conviene que la salida lo rotule.
7. Parada alcanzada con el control S7 en el límite (por ejemplo 4 de 40 protegidas SIN DATO) y estado CUMPLE: sin salida
   escrita (resuelto por VS168-03).

## Batería

Corrida en este equipo, un proceso, `python -I experiments\_s168\v375e_sombra\probar_sombra.py` (salida en
`D:\vrp-trabajo\temporales\s168_ver_sombra\bateria.txt`): **RESULTADO: 104 de 104, exit 0**, unos 5 minutos. Las
aserciones pueden fallar y prueban lo que dicen en: clases, población (Suomi NPP, MODIS, sin_info), `cargar_records`, brazos con
escena lejana, borde (+ vuelta), S0 a S5 y S7 en verde y rojo, `criterios_sombra` con valores fabricados, controles de la
curva (sesgo, ganancias, sin sustrato, sin cenit), parada, `main` de punta a punta (incluye S1 caído y S0 caído).
Sin prueba: S6, la rama `hay_neg` falso, el valor de los criterios (b), (c), (d) y del estado en `analizar`, las mitades
más allá del corte, la salida de `far_ocr`, el `--desde` posterior al 2026-11-03.

### Mutaciones que creo que sobrevivirían (no las corrí)

1. `("S6", ok6, d6)` a `("S6", True, d6)` en `analizar` (l. 378): S6 no tiene prueba en rojo.
2. `hay_neg = all(...)` a `hay_neg = True` (l. 323): ninguna escena tiene una clase de negativos en cero.
3. `LP.estado_c(m["veredicto"])` a `CUMPLE` o `NO_CUMPLE` (l. 333): el valor de (c) no se aserta en la escena principal.
4. Cruzar `p2k["veredicto"]` con `p2l["veredicto"]` en esa misma llamada.
5. Cruzar `cur_p["condicionada"]` con `cur_k["condicionada"]` en `estado_d_sombra(...)`: en la escena ambos son SIN
   SUSTRATO.
6. `cae_curva` fijo en `False` en esa llamada (M46 muta `criterios_sombra`, no esta línea).
7. `mitades`: `x["noche"] > corte` a `>=`; `E.p2(sel, a, "K")` a otra cosa; `"informa"` a `"decide"`. Sólo se aserta
   `corte_noche`.
8. `TOL_UNO_KM = 0.0051` a `0.0101` o a `0.0011` (M26 sólo lo lleva a 1,0).
9. `BORDE_KM = 0.005` a `0.0045` (M19 lo baja a 0,002, que sí se atrapa).
10. `UMBRAL_COBERTURA = 0.10` a `0.12`.
11. `INFORMAN` sin `("VIA", "sinfiltro")`: nadie aserta que esté en `br`.
12. `1.2` a `1.0` en la ganancia pareja de `controles_curva`: el control sigue en OK.
13. `n_max=20` de `control_s2`.
14. Mutación de `DESDE_P` a una fecha posterior en `control_s1` sólo se atrapa porque la prueba pasa «2026-11-03»; un
    `desde >= DESDE_P` a `desde >= "2026-11-01"` también se atrapa. En cambio, nada atrapa que S1 deje pasar un `desde`
    posterior (VS168-01), porque ninguna prueba lo espera.

## Lo que no pude comprobar

- Nada contra datos reales de la ventana P ni de la sombra (no corresponde abrirlos; `data/sombra_codigo_mirova/` no
  existe en este árbol).
- Que los `centroid_dist_km` reales caigan o no cerca del radio (VS168-10): la probabilidad es una estimación.
- Que el cenit del record de K coincida con el `geometria_centro.sensor_zenith` del run en las pasadas de la
  retrospectiva.
- Que `anomaly_pixels` de los records de la vía lleve siempre `dist_km` en todos los píxeles en el `origin/main` actual
  (leí `mirova_v750_codigo.py` de `origin/main` 5e03f0db: sí lo escribe; no vi records reales).
- Que el almacén de `origin/main` más nuevo que `c42ee0eb7` siga sin filtrar los records de la vía (vi `store.py` de
  `origin/main` 5e03f0db: las condiciones `not _via_mirova` están).
- El nulo de 55 mutaciones: no lo corrí (por instrucción), así que ignoro cuántas son atrapadas, aparte de las 14 de la
  lista de arriba que sospecho que no.
- Que la lista de fechas de reglas A119 para el OCR siga igual en la ventana P (no abrí `calidad_referencia_mirova.py`).
