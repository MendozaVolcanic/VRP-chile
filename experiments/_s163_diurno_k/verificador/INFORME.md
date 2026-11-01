# Informe del verificador: pre-registro diurno sobre K (tarea 1.32)

- Hora del servidor al empezar: Mon, 26 Oct 2026 12:19:23 GMT; al cerrar: 12:36:55 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`). La lista de caminos se selló a las 12:21:16 GMT.
- Commit medido: `ce20f9cf0f5ca867b96a4a4c9b2a2107497ee457` (rama `claude/s163-diurno-k-prereg-5c4f44`). `git status` limpio al empezar y al terminar (sólo aparece mi carpeta `verificador/`, sin trackear).
- Objetos sellados: commit `3a98abfad51f98521ef4873f97e0149637317e8e`. Comprobado con `git show 3a98abfad:<ruta> | sha256sum` contra `objetivos_sha256.txt`: los 16 blobs coinciden. El archivo del árbol de trabajo difiere en sha256 sólo por CRLF (`git ls-files --eol`: `i/lf w/crlf`); quitando los CR el sha de `evaluar_diurno_k.py` es el sellado (5d8afc8b...). `git diff 3a98abfad HEAD --stat` sólo agrega `objetivos_sha256.txt`.
- Modelo: Claude Sonnet 5.5 (`claude-sonnet-5-5`). Esfuerzo: bajo (el encargo no fijó otro).
- Lista previa de caminos, escrita antes de abrir el evaluador: `CAMINOS_PREVIOS.md` en esta carpeta, sha256 `9a38fdb979c7659e09180b5c2ef3bec33ee42060990b882b7493b957c0b7cb36`. Antes de escribirla leí `PREREGISTRO.md`, las instrucciones y `docs/MISSION.md`; no había abierto `evaluar_diurno_k.py`, ni la batería, ni `evaluador_comun.py`.
- Todo número de abajo salió de un comando o lectura de esta sesión. Mis scripts están en esta carpeta (`v_*.py`); necesitan la referencia congelada, que borré al terminar (se regenera con `python -I experiments/_s163_diurno_k/congelar_referencia.py --commit 047bd5692 --salida <carpeta nueva>`; sus 4 sha256 salieron OK contra `sustrato_k.json`).

## Resumen

12 hallazgos: 1 de gravedad 4, 3 de gravedad 3, 5 de gravedad 2, 3 de gravedad 1. Ninguno rompe el cálculo de una rama de la regla (las ramas del §6.2, §6.3 y §6.4 hacen lo que el texto dice y la batería pasa 58 de 58). Los graves son de otra clase: la regla, tal como está escrita, deja un camino ancho por el que el veredicto ADOPTAR sale con el criterio bajo 1 MW en PIERDE (V1), no mira publicaciones en la cuarta parte de las pasadas diurnas (V2), no entrega variantes que MISSION exige (V3) y descarta como «SIN DATO» algo que sí se puede calcular (V4).

---

## Hallazgos (ordenados por gravedad)

### V1 · La opción e-i da ADOPTAR con el criterio bajo 1 MW en PIERDE (p ≈ 1e-4) y afloja la compuerta G2 de la adenda sellada · GRAVEDAD 4 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:80-91` (`veredicto_sensor`, caso e-i en l. 89); `PREREGISTRO.md` §6.2 (caso e) y §6.5; contraste con `experiments/_s151_ab_diurno/PREREGISTRO.md` l. 165 a 170 (G2) y `ADENDA_K.md`.
- QUÉ PASA: en el caso e (neto > 0, P ≥ 1, D cumple) e-i adopta si Q_d ≤ Q_n. Ni el neto ni el resultado de P2 entran. Con la estructura real de W2 a W6 (referencia congelada, producción nocturna de control, como en `nulo_estructural.py`) corrí brazos que recuperan pocas alertas y publican en negativos hasta el tope de Q_n (`v_region_ei.py`, salida abajo). Resultado: V375 con 2 protegidas + 2 alertas bajo 1 MW recuperadas y 50 publicaciones en negativos: P2 PIERDE (neto +48, B 48, p_pierde 0,0001), Q_d 0,0336, D cumple, **e-i ADOPTAR** (e-ii: DECIDE NICOLÁS CON M4). V375 con 4 protegidas, 52 negativos y 300 publicaciones en «otra»: PIERDE (+52), **ADOPTAR**. V750 con 1 protegida recuperada de 6, 18 negativos publicados: PIERDE (+18, p 0,0000), Q_d 0,0081, D cumple, **ADOPTAR**; con 2 protegidas y 20 negativos igual.
- Tres cosas que el pre-registro no muestra: (a) la región de ADOPTAR es de **hasta unas 52 publicaciones de más en V375 y 20 en V750** por tan pocas como 4 alertas recuperadas (V375) o 1 protegida (V750); la frontera sale de `discriminar` y de Q_n (3,51 % y 0,94 %), calculada con las propias funciones del evaluador; (b) la G2 sellada de la adenda (publicar «tan callada como MIROVA de día») fallaba desde **20 pasadas en V375 y 6 en V750** (`_s151_ab_diurno/PREREGISTRO.md` l. 165 a 170, TEXTO: «publicar en 20 pasadas o más en VIIRS 375 y en 6 o más en VIIRS 750») y mandaba a DECIDE NICOLÁS; e-i la reemplaza por una cota 2,6 y 3,3 veces más ancha que decide sola; (c) P cuenta cualquier publicación sobre una pasada protegida, y 13 de las 26 protegidas de V375 y 4 de las 6 de V750 son de reflejo probable según el estudio 1.13 (`v_reflejo.py`): la única protegida que justifica adoptar puede ser un reflejo.
- CÓMO SE VERÍA EN EL RESULTADO: veredicto global ADOPTAR (o ADOPTAR en un sensor) con decenas de falsas alarmas diurnas nuevas por unas pocas alertas. ADOPTAR sólo abre el ciclo de adopción (§6.5), lo que baja el daño, pero el operador y Nicolás leerían «ADOPTAR» sin la región. El pre-registro admite que el criterio «no dice cuánto vale una protegida recuperada contra una publicación de más» y que no lo inventa; e-i sí lo inventa de hecho (una protegida vale hasta 52 o 20 publicaciones).
- CÓMO REPRODUCIRLO: `python experiments/_s163_diurno_k/verificador/v_region_ei.py <ref congelada>`. Líneas de salida de esta sesión:
  `VIIRS375 prot=2 amb=2 neg=50 otra=0 -> P2 PIERDE (neto +48, B 48, p_pierde 0.0001) Qd 0.0336 Qn 0.0351 D True -> e-i ADOPTAR | e-ii DECIDE NICOLÁS CON M4`; `VIIRS750 prot=1 amb=0 neg=18 otra=200 -> P2 PIERDE (neto +18, B 18, p_pierde 0.0000) Qd 0.0081 Qn 0.0094 D True -> e-i ADOPTAR | e-ii DECIDE NICOLÁS CON M4`.
- Lo que sí está bien: el pre-registro declara que e-i puede ADOPTAR hasta 5 % de las veces con un brazo al azar (§5.1) y deja la elección a Nicolás (§10 punto 2). Lo que falta es poner a la vista esta región y el contraste con G2 en el texto del sello.

### V2 · Las publicaciones en pasadas «otra» no entran a ninguna prueba, y «otra» es el 40 % de las pasadas diurnas de V375 · GRAVEDAD 3 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:246` (`otra` sólo se cuenta, `pub_otra`, l. 268); `evaluador_comun.py` `clase_p2` (l. 434 a 444); `PREREGISTRO.md` §4 («las publicaciones del brazo ahí se informan»).
- QUÉ PASA: un negativo exige que el volcán, sensor y **día UTC** no tengan alerta ni FP en ninguna pasada, de noche o de día. Para el día eso excluye pasadas donde MIROVA miró y dijo RUTINA porque una pasada de la noche anterior del mismo día UTC alertó. Desglose de las diurnas «otra» de W2 a W6 (`v_otra.py`): V375 1.024 en total: 604 RUTINA de la tabla en un día con alerta sólo nocturna, 28 con alerta sólo diurna, 27 con las dos, 257 por FALSO_POSITIVO del día, 106 FP propios, 2 sin geometría. V750 270: 185 por alerta nocturna, 6, 5, 56, 17, 1. O sea 789 pasadas diurnas RUTINA (604 + 185) que son «MIROVA miró y no vio nada» y que el criterio de victoria (punto 3: «publicación en negativos limpios (pasadas donde MIROVA miró y no vio nada)») contaría, quedan sin penalización. Son además los volcanes persistentemente activos (los que alertan de noche casi todos los días), justo donde un brazo diurno tiene más material caliente real y de reflejo que publicar.
- CÓMO SE VERÍA EN EL RESULTADO: un brazo que publica masivamente en los volcanes activos y poco en los quietos saca Q_d bajo (el denominador son sólo volcán-días quietos), cumple D y e-i, y sale ADOPTAR. Escenario sintético (`v_escenarios.py`, caso A): 60 publicaciones en «otra» + 1 protegida recuperada en V750 = **ADOPTAR (caso b)**, `pub_otra=60`, sin compuerta ni aviso. Con la estructura real (V1, segundo escenario) 300 publicaciones en «otra» tampoco cambian el veredicto. `imprimir` muestra `pub en «otra»`, pero ninguna regla lo lee, y M4 (que lo menciona) sólo se lee si el veredicto es DECIDE.
- Nota: la definición de día UTC es la de `clase_p2` para noches y se aplica sin cambio al día. Que sea heredada no la hace adecuada para el día; el pre-registro no lo discute.
- CÓMO REPRODUCIRLO: `python v_otra.py <ref congelada>`; `python v_escenarios.py` (caso A).

### V3 · El evaluador no entrega las variantes de la regla de mínimas (SE, original, 0,05) que MISSION.md manda informar, ni varias salidas que el pre-registro promete · GRAVEDAD 3 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:42` (`REGLA_MINIMAS = "SN"` constante, sin opción de línea de comandos; `main` l. 439 a 452); `docs/MISSION.md` punto 5 del criterio de victoria, TEXTO: «cada evaluación informa además SE (estrato aparte), la regla original y la variante con 0,05 exacto como alerta (umbral 0,04), y dice si algún veredicto cambia»; `PREREGISTRO.md` §6.4 («Las variantes de la regla de mínimas (SE y original, D-9) se informan sin decidir»), §4 (M4 «por sensor y ventana, con la lista de pasadas de cada lado»; magnitud «al lado de la del control de noche»), §7 (publicaciones por elevación solar 0 a 30°, 30 a 60°, más de 60°, y la fracción desproporcionada del instrumento a) de 1.13 aplicado a lo nuestro).
- QUÉ PASA: busqué en el evaluador (grep de `regla_minimas`, `SE`, `original`, `elev`, `ventana` en las funciones de métricas): sólo existe SN. No hay variantes de mínimas, ni M4 por ventana (sólo agregado W2 a W6; las listas de pasadas existen en el JSON de `--salida`, no en pantalla), ni desglose por elevación solar, ni el instrumento a) de 1.13 sobre lo nuestro, ni la mediana de magnitud del control de noche al lado. El evaluador común tiene `--regla-minimas` (l. 644); este no.
- CÓMO SE VERÍA EN EL RESULTADO: no cambia ningún veredicto, pero el sello quedaría diciendo que se informan cosas que el evaluador sellado no puede informar; para cumplir MISSION habría que editar un archivo ya sellado (sha en `objetivos_sha256.txt`). Pesa más en el caso probable (DECIDE NICOLÁS CON M4), donde Nicolás decide con M4 que no trae la apertura por ventana.
- CÓMO REPRODUCIRLO: `grep -n "regla_minimas\|SE\|original\|elev" experiments/_s163_diurno_k/evaluar_diurno_k.py` (sólo l. 42 y 480 usan la regla; ninguna otra variante).

### V4 · «Los records no guardan la geometría de visión (SIN DATO)» es falso: sí la guardan, y con ella se puede calcular el filtro de reflejo de 12° de MIROVA · GRAVEDAD 3 · CONFIRMADO (existentes) / SOSPECHA (records del brazo diurno)

- ARCHIVO:LÍNEA: `PREREGISTRO.md` §2.2 (l. 88 a 92: «los records no guardan la geometría de visión necesaria para calcularlo (SIN DATO)») y §7 (l. 336).
- QUÉ PASA: los records de `data/mirova_equivalent/` traen `sensor_zenith_deg`, `sensor_azimuth_deg`, `solar_zenith_deg` y `solar_azimuth_deg`. En Láscar, Villarrica e Isluga están completos en el 100 % de los records de los 8 sensores o plataformas (p. ej. MODIS_TERRA 1.820 de 1.820, VIIRS_SNPP 2.411 de 2.411, VIIRS_SNPP_750 2.401 de 2.401). El código que los escribe es `pipeline/process_viirs.py:475-480` y `process_viirs_mod.py:338-342` (comentario «S122: resto de la geometría de observación... Solo para estudio posterior»). La fórmula de MIROVA está en `osf_codigo_mirova/README.txt` l. 33 a 36 (`cosSunglint = cosd(sat_zen).*cosd(sun_zen) - sind(sat_zen).*sind(sun_zen).*cosd(sun_azi-sat_azi)`) y el rechazo en `MIROVA_VIIRS750_hotspot_detection.m:87` (`sunglint < 12`). Los records diurnos los arman los mismos procesadores, así que SOSPECHA razonable de que también los traen (no existe ninguno diurno todavía; no lo pude medir).
- CÓMO SE VERÍA EN EL RESULTADO: no cambia la regla. Pero el pre-registro dice que el filtro es el «primer candidato a probar» si V750 publica de más y propone un parche A45 en `pipeline/` para poder medirlo. Un evaluador que calcule el ángulo desde los records del brazo permite una variante «con filtro de 12°» en la misma corrida, sin tocar `pipeline/`. Hoy el texto sellado la descarta por una premisa errónea. No sé desde qué píxel se guardan los ángulos (centro de escena, píxel del volcán o del hotspot): hay que mirarlo antes de equipararlos con el escalar de MIROVA.
- CÓMO REPRODUCIRLO: `python -c` sobre `data/mirova_equivalent/Lascar.json`: último record con las cuatro claves (`sensor_zenith_deg 24.86, solar_zenith_deg 136.74` en el record medido) y conteo por sensor como arriba.

### V5 · La variante «sin reflejo» (§6.4 c) convierte en negativos a pasadas que no lo son: filtra las pasadas antes de armar la tabla y se pierde la marca «día con alerta» · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:305` (`pas = [p for p in pasadas ... ec.clave(p) not in excl_k]`) y `:312` (`T = ec.tabla_por_pasada(pas, ...)`); `evaluador_comun.py:96-97` (`alertas_noche` se arma con las pasadas recibidas).
- QUÉ PASA: al quitar la protegida de reflejo de la lista, `tabla_por_pasada` ya no ve esa alerta y las demás pasadas RUTINA de ese volcán, sensor y día quedan sin «día con alerta», o sea pasan de «otra» a «negativo». Sobre la referencia real (`v_reflejo.py`): las 17 protegidas de reflejo probable de W2 a W6 (13 de V375, 4 de V750; 0 filas del estudio dentro de las ventanas sin pasada) hacen pasar 12 pasadas de «otra» a «negativo» (todas V750: 6 diurnas y 6 nocturnas; Isluga 09-04, Planchón Peteroa 08-14, Tupungatito 08-20).
- CÓMO SE VERÍA EN EL RESULTADO: la variante c pesa más contra el brazo de lo que dice (cualquier publicación diurna del brazo en esos días, que es lo más probable justo en un día de reflejo, pasa a falsa alarma). El efecto es sobre la robustez: empuja un ADOPTAR a DECIDE NICOLÁS (dirección conservadora) y no al revés. Magnitud pequeña (6 pasadas diurnas V750 de 2.223 negativos), pero la variante deja de medir lo que dice medir.
- CÓMO REPRODUCIRLO: `python v_reflejo.py <ref congelada>` (línea «cambios de clase por quitar las protegidas de reflejo: {('otra', 'negativo'): 12}»).

### V6 · La noche «intacta» (I5) no exige que los dos brazos tengan los mismos records; y un R1 con I5 roja sale INDECIDIBLE en vez de pérdida · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:214-227` (`compuerta_i5` compara sólo `set(ic) & set(ib)`; `solo_control`/`solo_brazo` se informan); `:106-124` (`veredicto_global`: `indecidible` se resuelve antes que R1); `PREREGISTRO.md` §5 I5 («observadas por los dos brazos») y §6.1.
- QUÉ PASA: escenario sintético (`v_escenarios.py`, B1 y B2): le quito al brazo (o al control) un record nocturno de una pasada RUTINA. Resultado: `inval: [] indec: []`, `noche_solo_un_lado` = 1, veredicto global sin cambio. El conteo sólo se imprime. La cobertura del evaluador común (I3) cubre las protegidas, las alertas (aviso) y los días vacíos, no una RUTINA ni un record aislado. Y cuando una discordancia de I5 afecta una protegida nocturna, el global sale INDECIDIBLE y R1 (la pérdida) no se evalúa; la regla del §6.1 («si tras repetir el mismo record sigue distinto... INVÁLIDO y, si es una protegida, también una pérdida que el criterio no acepta») queda a cargo de una persona.
- CÓMO SE VERÍA EN EL RESULTADO: un job diurno que se cae a mitad de una noche, o un gránulo de menos en el brazo, pasa sin marca. Efecto sobre el veredicto diurno: ninguno directo (la noche no entra a P2 diurno), pero la afirmación «noches intactas» queda sin sostén para esos records.
- CÓMO REPRODUCIRLO: `python v_escenarios.py` (líneas B1 y B2).

### V7 · La tabla de MIROVA tiene más días parciales dentro de W2 a W6 que los dos que el pre-registro declara, y 78 negativos de W6 se etiquetan sin ninguna pasada nocturna del día · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `PREREGISTRO.md` §3 «Por qué no hay W7» (huecos el 12 y el 13 de octubre); `sustrato_k.py:131-140` (negativo por día UTC).
- QUÉ PASA: contando pasadas CONS de VIIRS 375 por día en las ventanas (`v_huecos2.py`, mediana 31 diurnas y 32 nocturnas por día): 2026-10-12 sólo noche (38), 2026-10-13 sólo día (39), 2026-10-14 día 11 (mediana 31), 2026-10-07 noche 11, 2026-07-23, 07-28 y 07-31 noche 11 a 15, 2026-08-18 día 15, 08-28 día 15, 09-19 día 11. El 2026-10-13 aporta 39 negativos V375 y 39 V750 diurnos (`v_w6.py`) sin una sola pasada nocturna de ese día UTC: si MIROVA alertó esa noche, la alerta no está en la tabla y la RUTINA diurna parece negativo limpio. En total 78 de 3.710 negativos (2,1 %) de W2 a W6 dependen de eso.
- CÓMO SE VERÍA EN EL RESULTADO: errores de etiqueta en un sentido (más «negativos» que los reales), que penalizan al brazo; pequeños en el agregado. Un pasada ausente de la tabla tampoco entra a ninguna cuenta, así que un día parcial reduce n sin aviso.
- CÓMO REPRODUCIRLO: `python v_huecos2.py <ref congelada>` y `python v_w6.py <ref congelada>`.

### V8 · «Recuperar» una protegida es publicar cualquier magnitud sobre esa pasada · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:251` (`P = sum(pub(f, brazo) for f in prot)`); la razón de magnitud (l. 253, 270) es sólo informativa.
- QUÉ PASA: el predicado del tablero decide si el brazo «publica», sin comparar con la energía de MIROVA. Una publicación de décimas de MW sobre el 760,6 MW de Láscar del 2026-06-15 (reflejo, A76) cuenta igual que acertar la magnitud. Es consistente con el criterio de victoria (punto 3 separa recall y razón de magnitud como métricas distintas) y con el evaluador común, pero para la decisión de ADOPTAR, que depende de P ≥ 1, una sola publicación pequeña sobre una pasada de reflejo basta. En V1 ya aparece (la protegida que justifica adoptar puede ser de ese tipo).
- CÓMO REPRODUCIRLO: lectura de la l. 251; el test `test_magnitud_brazo_sobre_mirova_en_recuperadas` fija que la magnitud no entra a la decisión.

### V9 · Dos compuertas que casi no pueden fallar justo en el caso donde se decide · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:136-143` (`juzgar_i6`), `:171-188` (`compuerta_i2`).
- QUÉ PASA: (a) I6 exige que el placebo «a» dé GANA sólo si toca 5 bloques o más; con un brazo callado (pocas publicaciones en negativos, el caso en que se adopta) el resultado es SIN SUSTRATO y la compuerta pasa. En el escenario sintético C de `v_escenarios.py` (3 publicaciones en negativos, 1 protegida): `I6: 'a': SIN SUSTRATO, bloques 2; c_falsos 0; problemas []`. Y cuando sí toca 5 o más bloques, el placebo apaga publicaciones del propio brazo y el resultado es GANA por aritmética de la prueba de signos (2^-5 = 0,031), así que I6a verifica la prueba de signos, no el brazo. (b) I2 «la palanca actuó» pasa con **un** record diurno con `diag_umbrales_diurnos` por ventana y sensor (`any(...)`, l. 183-184); lo que protege de un brazo mayormente mudo es I4b/I4c, no I2.
- CÓMO SE VERÍA EN EL RESULTADO: las dos compuertas dan verde en brazos que no ejercen la rama; la protección real está en I4. No es un camino a un veredicto equivocado por sí solo.
- CÓMO REPRODUCIRLO: `python v_escenarios.py` (línea C).

### V10 · I4c tolera 6 pasadas diurnas V375 y 21 de V750 sin record, y las alertas bajo 1 MW no se vigilan una por una · GRAVEDAD 2 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:191-211`; `PREREGISTRO.md` §5 I4.
- QUÉ PASA: con N = 2.547 y p_sup = 0,0011 la cola `P(Bin(N, p_sup) >= x) < 0,05` falla desde x = 7 (V375); con N = 2.499 y p_sup = 0,0059 desde x = 22 (V750) (calculado con `scipy.stats.binom`). La cota viene de la tasa **nocturna** de producción; no hay medida de la tasa diurna del brazo (SIN DATO). La protegida sin record sí falla sola (I4a), pero las 10 alertas bajo 1 MW de V375 pueden perder 6 sin marca: se achican n y X de la prueba D y el neto de P2 en silencio. Dirección del sesgo: perder alertas bajo 1 MW baja la chance de GANA y de D, o sea hacia NO ADOPTAR.
- CÓMO REPRODUCIRLO: la cuenta anterior.

### V11 · La prueba D supone pasadas independientes, y las alertas se agrupan en eventos · GRAVEDAD 1 · CONFIRMADO

- ARCHIVO:LÍNEA: `evaluar_diurno_k.py:94-103`.
- QUÉ PASA: las 26 protegidas de V375 caen en 21 volcán-días, y las 36 alertas (con las 10 bajo 1 MW) en 30; las 6 de V750 en 6. Láscar (7) y Lastarria (6) son 13 de las 26 (`v_bloques.py`). La binomial trata 36 como independientes; el n efectivo es algo menor (30 bloques). Efecto: D es levemente anticonservadora. El nulo del §5.1 sortea pasada por pasada y no modela esa agrupación (SOSPECHA de que subestima el ADOPTAR de un brazo con errores agrupados; no medido).

### V12 · Errores de texto en el pre-registro · GRAVEDAD 1 · CONFIRMADO

- `PREREGISTRO.md` §2.2: «K1 diurno -0,5 (l. 190)» y «mínimos... (l. 192 a 199)». En el `.m` son l. 189 (`absoluteNTIthreshold = -0.5`), 191 y 192 (σ 15) y 194 a 198 (mínimos 0,02); el rechazo de reflejo está en l. 83 a 89 (la condición en l. 87) y sí coincide. Los valores son correctos, las líneas están corridas en uno.
- `PREREGISTRO.md` §3 «sus 12 positivos» de W2: la tabla de sustrato de la misma sección da, para W2, 11 protegidas + 1 alerta bajo 1 MW en V375 y 1 protegida en V750 = 13. Los 12 son los de V375.
- `PREREGISTRO.md` §5.2 y `mutaciones_salida.txt`: «41 de 41 atrapadas por aserción»; la salida dice `atrapadas por asercion: 41 de 42`, porque el 42 es la mutación de control `C-CAIDA`, que tiene que quedar fuera. Es coherente, pero se lee distinto.
- §3 dice «la tabla de MIROVA del árbol se corta el 2026-10-19» (confirmado: el 10-19 sólo tiene noche, del 10-20 al 10-25 sólo filas OCR); la salida `sustrato_k_salida.txt` no muestra los huecos, y el pre-registro lo avisa.

### V13 · Defaults del workflow y sello con fines de línea · GRAVEDAD 1 · CONFIRMADO

- `reproc-s151-ab-diurno.yml`: los defaults de `brazos` y `control` son los de C0 (`_s151_ab_diurno_control`, `_s151_ab_diurno_on`) y la descripción del candado apunta al `PREREGISTRO.md` de `_s151_ab_diurno`, no al de `_s163`. Si un despacho omite esas entradas corre brazos C0 durante horas de runner; el evaluador lo atraparía (I1 por flags y por sha), pero tarde. El pre-registro dice «sin cambios» al workflow (§8) y da las entradas que hay que pasar, y el paso «El brazo LEE lo que declara» exige `DATA_SUBDIR == PROFILE_NAME` y el flag según `control`.
- En este árbol de trabajo (Windows, CRLF) `sha256sum` de 15 de los 16 archivos de `objetivos_sha256.txt` da distinto del sellado; el sello vale sobre los blobs de git (lo dice la cabecera del archivo). Quien verifique con el árbol sin normalizar verá 15 diferencias falsas.

---

## Veredicto por afirmación central

| afirmación | veredicto |
|---|---|
| §3, cifras del sustrato (W1 a W6, totales 26/10/1.487/2.547 y 6/0/2.223/2.499, y «tabla sola»: 6, 7, 1.539; 2, 0, 2.229) | CONFIRMADO contra `sustrato_k_salida.txt` (sumas rehechas a mano: protegidas 11+1+5+4+5 = 26; alerta_mb 1+2+4+2+1 = 10; negativos 336+281+310+315+245 = 1.487). Salvo «sus 12 positivos» de W2 (V12). |
| §3, «13 de 2.522» y «2 de 2.494» pasadas diurnas con alerta de la tabla | CONFIRMADO (6+7 y 2; suma de diurnas 573+424+540+575+410 = 2.522) |
| §3/§4, I4c: p_sup 0,0011 y 0,0059 (Clopper-Pearson una cola) | CONFIRMADO (`beta.ppf(0.95, ...)`: 0,0011028 y 0,0059190) |
| Cita de la Tabla 1 (PDF p. 7) | CONFIRMADO, RENDER (`page.get_pixmap(dpi=200)`, página índice 6 de 25): noche K1 -0,8 en ROI1 y ROI2, C1 0,003 y 0,01, C2 5 y 10; día K1 -0,6 y -0,6, C1 0,02 y 0,02, C2 15 y 15. El párrafo previo dice que los parámetros difieren «for night-time and daytime data (because solar effects amplify the variability in NTI and ETI matrices in daytime data)» (Coppola et al. 2016a, PDF p. 7, RENDER) |
| §2.2, K1 diurno -0,5 y mínimos y σ del código de MIROVA | CONFIRMADO en valores (líneas corridas en uno, V12) |
| §2.2, filtro de reflejo <12° rechaza la detección entera | CONFIRMADO (`.m:83-88`) |
| §2.2/§7, «SIN DATO» la geometría | REFUTADO (V4) |
| I1 (log y por record) | CONFIRMADO por lectura: `compuerta_i1` y `problemas_de_logs` hacen lo escrito (flags declarados, `triggered_test1`, `test1`/`test1_roi`, sha de 40 caracteres) |
| I2 | CONFIRMADO EN PARTE: hace lo escrito, pero es débil (V9) |
| I3 | CONFIRMADO: `ec.cobertura` sobre las pasadas nocturnas de los tres sensores (`Tn`) |
| I4 (a, b, c) | CONFIRMADO en la mecánica; tolerancia ancha (V10) |
| I5 | CONFIRMADO EN PARTE (V6) |
| I6 | CONFIRMADO EN PARTE (V9) |
| Casos a a e de §6.2 | CONFIRMADO: `veredicto_sensor` (l. 75-91) los implementa tal cual y los 13 casos paramétricos de la batería coinciden. El problema es de diseño (V1), no de implementación |
| §6.3, veredicto global | CONFIRMADO (`veredicto_global`, l. 106-124, y 9 casos de la batería) |
| §6.4, robustez | CONFIRMADO EN PARTE: las tres variantes existen, la «sin reflejo» tiene el defecto de V5; las variantes SE/original no existen (V3) |
| §6.1, lectura de R1 («por construcción») | CONFIRMADO: sin noche distinta R1 es vacío; con I5 roja el global es INDECIDIBLE y R1 no se mira (V6) |
| Prueba D y su necesidad (1 - 0,995^26 = 12 %) | CONFIRMADO (0,12219; calculado). Que D sea necesaria con e-i también: el nulo (4 y 10 de 200) lo muestra, y V1 muestra que con D igual quedan regiones anchas |
| §5.1 contra la salida del nulo | CONFIRMADO: repetí `nulo_estructural.py --ref <congelada>` y la salida es **idéntica** línea por línea a `nulo_estructural_salida.txt` (diff vacío); los números de §5.1 coinciden con la salida (GANA 0 de 200 en las ocho combinaciones, e-i 4/4/0/0 en V375 y 10/0/0/0 en V750, e-ii 0 en todas, controles positivo y negativo, Q_n 3,51 % y 0,94 %) |
| §5.2, 58 pruebas, 53 rojas contra el stub, 41 mutaciones | 58: CONFIRMADO (corrí `python -m pytest -q -p no:cacheprovider experiments/_s163_diurno_k/test_evaluar_diurno_k.py`: 58 passed en 11,22 s). 53 rojas: CONFIRMADO en `probar_salida_roja.txt` («53 failed»). 41 de 41: leído en `mutaciones_salida.txt`; NO re-corrí las mutaciones (SIN DATO propio, ver abajo) |
| §2.1, 3 pruebas de perfiles en verde | CONFIRMADO (`tests/test_perfiles_diurno_k_s154.py`: 3 passed en 0,86 s) |
| §8, cuentas de costo | CONFIRMADO aritméticamente: 11 × 83 × (2,2 + 5,5) min = 117,2 h; /3 = 39,1 h; /6 = 19,5 h; 300/66 = 4,5; 58/40 = 1,45. Las 83 días = 18+12+19+20+14. Las premisas (15 a 24 y 40 a 58 min de la corrida sobre C0) vienen de otra corrida y bajo K están sin medir: SIN DATO, como el texto ya dice |
| §8, workflow (comillas en `on`, sólo `EARTHDATA_TOKEN` con salida inmediata, candado `si`, grupo propio con un pendiente, `max-parallel: 3`, timeout 300 por paso y 330 por job, `pipefail`, sin `--no-night-filter`) | CONFIRMADO por lectura (l. 40 a 180) |
| Intacto lo sellado de la adenda (ventanas, perfiles, tag, H2a) | CONFIRMADO por lectura de ADENDA_K.md §2 y §4 contra §0 y §5; ver pérdidas en V1 (G2) y la sustitución de G1 por D |

---

## VERIFICADO LIMPIO (qué miré y contra qué vara)

- Sello de objetos: sha256 de los 16 blobs contra `objetivos_sha256.txt` (`git show 3a98abfad:<ruta>`).
- Nulo estructural: repetido sobre la referencia congelada (sha256 de los 4 CSV iguales a `sustrato_k.json`) y la producción de este árbol; salida idéntica byte a byte (modulo CR).
- Batería: 58 de 58, y los perfiles 3 de 3.
- Las ramas de `veredicto_sensor`, `veredicto_global` y `veredicto_final` contra el texto de §6.2 a §6.4 (por lectura y por la batería).
- Frontera día/noche: de 10.411 pasadas VIIRS de W2 a W6 ninguna cae a menos de 3° del terminador (`v_crepusculo.py`), así que la diferencia entre la hora de la pasada de MIROVA y la del record no cambia la clase en ninguna. La regla del evaluador (`elevación > 0` con `pipeline.store._solar_elevation`) es la de `store.py` (`_reject_daytime`) y la de `pipeline/diurno.py::pasada_es_diurna`.
- Pareo y clases: negativo, alerta_mb y protegida salen de `evaluador_comun.clase_p2`/`cm.es_protegida`; las protegidas no entran a P2 (caen en «otra» por construcción de `clase_p2`), y P las cuenta aparte.
- Filtro de reflejo del estudio 1.13: 94 filas, 40 desproporcionadas o aisladas, 17 emparejan con pasadas de W2 a W6 y 0 filas dentro de las ventanas quedan sin pasada (23 fuera de ventana).
- Cobertura nocturna de producción: lo escrito en `sustrato_k.json` coincide con lo que usa `main` (`vara_cobertura_nocturna_produccion`).
- Brazos y perfiles: `_s154_ab_diurno_k_on.yaml` sólo agrega `enable_daytime_viirs: true`; `diag_umbrales_diurnos` se escribe sólo si `_umbrales_diurnos` (`process_viirs.py:2249`, `process_viirs_mod.py:1510`).
- La referencia se verifica por sha256 antes de decidir (`evaluar_diurno_k.py:458-461`).
- Las ventanas faltantes no pasan en silencio: un día con pasadas de MIROVA y sin records del brazo da I4b, y un job que falta da I3 o I4; lo probé por lectura y por los casos `test_i4_*`, no con una corrida real.

## SIN DATO (lo que no pude medir)

- Mutaciones: no las re-corrí. `experiments/_s162_instrumento/mutar.py` modifica archivos del repo (los restaura), y el encargo prohíbe tocar archivos fuera de mi carpeta. Dejé 41 de 41 como lo informa el autor.
- Comportamiento del brazo diurno bajo K: no existen records diurnos. Todo lo que dice cuántas publicaciones habrá (V1, V2) es de escenarios sobre la estructura real, no de datos del brazo.
- Si los records del brazo diurno traen los ángulos de visión (V4, SOSPECHA razonable) y desde qué píxel se guardan.
- Que Q_n del control de la corrida real se parezca al de producción hoy (3,51 % y 0,94 % salen de `data/mirova_equivalent/` de este árbol, que es un corpus vivo; A90). No verifiqué la afirmación «ya aceptada al adoptar K (S153)» (§6.2/§6.5).
- La tasa de falso fallo de I6c en la corrida real (con pocos bloques elegibles el placebo c puede no tener poder).
- `main()` de punta a punta sobre datos de K: sólo existe la prueba de humo sobre C0 (leí su salida; no la re-corrí, necesita un artefacto de Actions que no tengo).
- Las citas «Campus et al. 2022, p. 16 y 17» y los números de la corrida sobre C0 (2.000 de 2.077): el segundo está en `experiments/_s151_ab_diurno/salidas/W2_W6_s154/verificador/INFORME.md` l. 19 y 54 y en `evaluar_salida.txt` l. 99 (89,3 %, 2.077/2.325); el primero no lo abrí.

## QUÉ NO MIRÉ

- `pipeline/process_viirs.py`, `process_viirs_mod.py`, `store.py` y `fetch.py` más allá de las líneas citadas; no verifiqué que la rama diurna aplique los umbrales de la Tabla 1 (sólo leí `diurno.py::umbrales_viirs` y las constantes de `profile.py` l. 202 a 220: K1 -0,6, C1 0,02, σ 15, C2 15).
- `scripts/clase_mirova.py` (pareo, SN, ventana), `banco_paridad.py` y el predicado `isValidDetection` con node: los uso como cajas negras de `main` y no los auditué. En particular no revisé si el predicado del tablero (calibrado de noche, ver `diurno.py` «MAGNITUD diurna») se comporta distinto con records diurnos.
- `unir_ventana.py`, `cobertura.txt` y el flujo de repetición de jobs.
- El pre-registro original (`_s151_ab_diurno/PREREGISTRO.md`) fuera de G1 a G3 y §5.4/§11; el candado `verificador_candado_k*` de la adenda.
- Los tiempos del workflow y la cuota real de runners.
- Ortografía y estilo del pre-registro (no revisé si trae guiones largos, regla del usuario).
- Coppola 2016a fuera de la p. 7.
