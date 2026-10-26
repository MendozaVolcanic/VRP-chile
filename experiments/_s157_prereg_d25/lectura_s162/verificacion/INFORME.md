# Verificador con contexto limpio de la lectura de D25 (S162)

- Hora del servidor al empezar: `Sat, 24 Oct 2026 13:22:00 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit medido: worktree `C:\vrp-trabajo\s159-evaluador`, HEAD `e634f819f` (rama `s159-evaluador-d25`, igual al remoto). Tag `s161-d25-lectura` = objeto `724e43452`, apunta a `a7418e01d`, igual en `origin`. `git diff --stat a7418e01d e634f819f`: 19 archivos, todos bajo `experiments/_s157_prereg_d25/lectura_s162/`; el evaluador y sus dependencias no cambian entre el tag y el HEAD.
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo medio. Python 3.12.10, numpy 2.4.4 (las mismas que declara `salidas/versiones.txt`).
- Carpeta de trabajo (CARPETA): `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta1\verificador_d25`. Caminos escritos antes de releer: `caminos.md` (sha256 `3a9aac02a9d85479db229925325cb7ad8b39b70ea1f450ec6b364b394e1db5b0`).
- No modifiqué nada del repositorio ni de los artefactos; no hice commit, push, despacho ni usé credenciales (gh sólo para leer).
- Qué NO miré: el interior de `armar_tabla.py`, `banco_paridad` y `clase_mirova` (sólo leí `alerta_protegida` y los umbrales); el predicado de `frontend/index.html` con node (confié en el sha256 que el evaluador imprime, `f711c61d...`); el manifiesto de la referencia congelada más allá del control que el propio evaluador corre; la línea `FLAGS_BRAZO` de los logs de los jobs (confié en el control de cableado del evaluador); si el generador de numpy da la misma secuencia en otra versión (D-47 lo anota, no lo medí).

## En una pantalla

1. Las siete afirmaciones del README se sostienen en lo que deciden: re-corrí el evaluador del tag sobre V1, V2, V1 tabla sola y el brazo del 17 al 19 de octubre, y los cinco JSON y el combinado salen **idénticos bit a bit** a los de `lectura_s162/salidas/`; los artefactos son los de los cuatro runs declarados (sha256 de cada zip igual al `digest` que GitHub publica para `s146ab-todo`).
2. Recomputé P2 por mi cuenta desde la lista de pasadas discordantes del JSON (neto, B y valor-p exacto por enumeración): V1 VIIRS 750 neto +6 en 26 noches con p PIERDE exacto 0,1635 (el evaluador usa 10.000 sorteos y da 0,1619), V2 VIIRS 375 con SN neto +1 en 11 noches con p 0,50; coinciden con el README.
3. Dos detalles del README están mal escritos y no cambian el veredicto: el brazo del 17 al 19 de octubre queda INDECIDIBLE por la calibración de **d** (cola EMPEORA, 0,055 contra 0,05) en el estrato VIIRS 375 sin kernel con cenit sobre 40°, de **7 pares y 4 noches**, no por la de d′ en «un estrato de 6 pares» (V162-01); y el run de V1 (39530508296, intento 2) terminó en **failure** por un `git push` rechazado al publicar la rama de salidas, con el artefacto y la cobertura pareja en verde (V162-02).
4. El sha256 declarado del evaluador (`93c26d62...`) es el del archivo con CRLF del checkout de Windows; el blob de git (LF) da `2e557697...`; el contenido es el del tag (`git diff` vacío) pero el número no se reproduce en Linux ni con `git show` (V162-03).
5. El comando con que se evaluó el brazo del 17 al 19 de octubre (`--desde 2026-10-17 --hasta 2026-10-19`, además del envoltorio) no está en «Cómo se reproduce» del README; se infiere de la segunda línea de `s17.log`.

## Veredictos por afirmación

### (a) Veredicto combinado DECIDE NICOLÁS; ninguna fila del §8 d lleva a CUMPLE ni a NO CUMPLE. **CONFIRMADO**, gravedad 1.

- `python evaluar_d25.py --combinar out/v1.json out/v2.json` sobre mis JSON reproduce `combinado.log` línea por línea (`diff --strip-trailing-cr`: 0 líneas).
- Contra la tabla del §8 d (PREREGISTRO l. 306 a 314), con los resultados verificados abajo: fila CUMPLE exige M MEJORA en cada ventana y V2 no tiene ninguno (`v2.json`: los cuatro estratos que deciden quedan NEUTRO en las dos reglas); fila NO CUMPLE exige P1 VETADO o P2 PIERDE y no hay ninguno (P1 CUMPLE en los 4 sensores-ventana; P2 toma EMPATE o BLOQUEA, nunca PIERDE); fila «M MEJORA en una sola ventana» da decide Nicolás; fila P1b da decide Nicolás; y D-34 §5.5 y D-45 §2.6 (ADENDA_GEMELO l. 54 a 56, ADENDA_SIGNOS_P2 l. 69 a 73) mandan BLOQUEA a DECIDE NICOLAS. El código hace lo mismo: `global_ventana` l. 891 a 921 y `combinar` l. 1204 a 1228 de `evaluar_d25.py`.
- «Manda la más estricta»: en V2 la regla original da SIN EFECTO y la SN DECIDE NICOLAS; `peor` (l. 935 a 936, `ORDEN` l. 160) elige DECIDE NICOLAS. Es lo que el README dice en la celda «P2 VIIRS 375 ... BLOQUEA con SN».

### (b) P1 CUMPLE en V1 y V2 en los dos sensores; P1b lista exactamente dos protegidas de Chillán que cruzan 1 MW hacia abajo. **CONFIRMADO**, gravedad 1.

- `extraccion_lectura_v1_v2.txt` (script `extraer.py` sobre los JSON de la lectura, idénticos a los míos): V1 P1 CUMPLE con 24 (VIIRS 375) y 22 (VIIRS 750) protegidas que K publica, 0 netas, 0 ruidosas, 0 pendientes, 7 y 2 sólo OCR de Suomi NPP listadas aparte; V2 CUMPLE con 38 y 42, 0 perdidas. Igual bajo las dos reglas.
- P1b: `cruces_1MW` trae exactamente `NevadosDeChillan|VIIRS375|2026-10-11 05:36 | K 1.225 MW -> D 0.909 MW | MIROVA 1.38` y `NevadosDeChillan|VIIRS750|2026-10-14 06:18 | K 1.173 MW -> D 0.632 MW | MIROVA 2.0`, una por sensor, en las dos reglas; en V2 `SIN CRUCES`. Control positivo del instrumento: barrí yo mismo la tabla `tmpV1/t_K_D.json` (4.610 pasadas) buscando K con 1 MW o más y D bajo 1 MW con los dos publicando, sin filtrar protección ni D-29: aparecen 7, las 2 de Chillán (etiqueta `pos`, las únicas protegidas) y 5 de Puyehue Cordón Caulle VIIRS 750 que no son alerta de MIROVA (ver V162-04). O sea que la lista de P1b no está vacía por un cargador mudo: hay más cruces en los datos y P1b conserva justo los que su definición pide (protegida A, `contar` l. 802 a 803; `UMBRAL_PROTEGIDA_MW = 1.0`, `scripts/clase_mirova.py:46`).
- Las fechas 2026-10-11 y 2026-10-14 no están en la exclusión de D-29 (13, 17 a 20).

### (c) P2 BLOQUEA en V1 VIIRS 750 (neto +6, 26 noches) y en V2 VIIRS 375 sólo con SN (neto +1). **CONFIRMADO**, gravedad 1.

- Recomputado por mi cuenta desde `discordantes` (sumo `contribucion`, agrupo por volcán y fecha UTC, enumero los 2^B repartos): V1 VIIRS 750, neto +6, B 26 (16 noches de +1 y 10 de −1), p PIERDE exacto **0,1635**; el JSON, con 10.000 sorteos y semilla 162 (B > 20, D-45 §2.5), da 1.619/10.001 = 0,1619, y PIERDE exigiría 5 % o menos: BLOQUEA. Igual en las dos reglas (SN sólo toca VIIRS 375). V2 VIIRS 375: original neto −1, B 12, EMPATE; **SN neto +1, B 11** (6 de +1, 5 de −1), p PIERDE exacto 1.024/2.048 = **0,50**: BLOQUEA. V1 VIIRS 375 EMPATE en las dos (neto −1 y 0). V2 VIIRS 750 neto −2, B 43, p exacto 0,6704 contra 0,6705 por sorteos: EMPATE. Signo coherente en las 4 ventanas-sensor: cada aporte +1 lleva `error_de = D`.
- Lo que informa y no decide, por si alguien lo lee como veredicto: en V1 VIIRS 750 la regla (a) del gemelo y la (b) de D-33 dan PIERDE, y D-34 y D-42 dan BLOQUEA; la que decide es D-45 (`REGLA_P2`, l. 151). En V1 VIIRS 375 original, D-42 queda INDECIDIBLE (calibración caída) y D-45 EMPATE: el cambio de regla sí cambia esa celda, como anticipa ADENDA_SIGNOS_P2 §1.

### (d) M MEJORA sólo en V1 VIIRS 750 con cenit ≤ 40°; los demás estratos que deciden quedan NEUTRO porque d mejora y d′ no. **CONFIRMADO para el README; la paráfrasis de quien orquesta es CONFIRMADA EN PARTE**, gravedad 1.

- V1 `M|VIIRS750|z<=40` MEJORA: d −0,132 [−0,348; −0,036], d′ −0,099 [−0,240; −0,007], 3 de 3 volcanes con d y con d′ negativas (Láscar 6 pares, Chillán 9, PCC 8), calibraciones OK (falsos MEJORA 0,015, de d′ 0,010). Igual en las dos reglas. Ningún otro estrato que decide da MEJORA en V1 ni en V2.
- Por qué queda NEUTRO cada uno de los otros (JSON, campo `nota` y `regla_dprima`): V1 y V2 `VIIRS375|sin_kernel|z<=40` y V2 `VIIRS750|z<=40`: d MEJORA, d′ NEUTRO, nota «sube en promedio, no en los pares correctos» (la razón que la paráfrasis nombra). V1 y V2 `VIIRS750|z>40`: NEUTRO por la opción A de D-27, «MEJORA sostenida por menos de 2 volcanes»: un solo volcán con 3 pares o más, Chillán (14 de 18 pares) en V1 y Láscar (24 de 27) en V2; d′ también NEUTRO ahí. `VIIRS375|sin_kernel|z>40` (sólo bloquea): d MEJORA, y en ese estrato un MEJORA no cuenta (`decidir_estrato` l. 725 a 726); d′ NEUTRO; no hay EMPEORA, así que no bloquea. El README dice esto mismo celda por celda; la frase «porque d mejora y d′ no» es la razón en 3 de los 5 estratos NEUTRO que deciden, no en los 5.
- Lo que sólo informa y el README reporta bien: V2 `VIIRS375|kernel|z>40` EMPEORA con d +0,003 [+0,002; +0,004] (original) y [+0,003; +0,004] (SN), modo `informa`, fuera de `global_ventana` (l. 890). Placebo K×1,2 MEJORA en V750 ≤ 40° y V375 sin kernel ≤ 40°, las dos ventanas.

### (e) La tabla de latest.php sola en V1 da el mismo veredicto; el envoltorio sólo cambia `VENTANAS` en memoria. **CONFIRMADO**, gravedad 1.

- `envoltorios/v1_solo_tabla.py` (11 líneas, leído entero): inserta la carpeta en `sys.path`, importa el evaluador, pone `D.VENTANAS["V1"]["solo_tabla"] = True` y llama a `D.main()`. Nada más. Que el cambio en memoria llegue de verdad: `evaluar` copia `VENTANAS[a.ventana]` al entrar (l. 941), `E.archivos_ref` escribe un OCR vacío cuando `solo_tabla` es verdadero (`evaluar_fk.py` l. 109 a 118) y `contar` apaga la exclusión de Suomi NPP (l. 788; en `v1_solo_tabla.json` `solo_ocr_snpp` baja de 7 y 2 a 0 y 0); el log dice «decide la tabla sola».
- Re-corrido con el envoltorio sobre el mismo artefacto: `out/v1_solo_tabla.json` **idéntico bit a bit** al de la lectura; log idéntico sin los CR. Estado: el mismo string que V1 (DECIDE NICOLAS por P2 VIIRS 750, M MEJORA, P1b). P1 22 y 21 protegidas, CUMPLE. P2 VIIRS 375 con SN pasa de EMPATE a **BLOQUEA, neto +2, B 13, p PIERDE exacto 3.304/8.192 = 0,4033**, como dice el README. Ver V162-05 sobre cómo el string del estado esconde ese segundo sensor.

### (f) El brazo del 17 al 19 de octubre da INDECIDIBLE «por falta de sustrato»; el envoltorio `s17_sensibilidad.py` no altera ninguna regla salvo vaciar la exclusión de D-29. **CONFIRMADO EN PARTE**, gravedad 2.

- Lo que se confirma: `s17_sensibilidad.py` (14 líneas, leído entero) pone `D.DIAS_EXCLUIDOS["V1"] = ()` y, sólo si recibe la palabra `solo_tabla`, pone también `VENTANAS["V1"]["solo_tabla"] = True`; nada más. Re-corrido en las dos variantes: `out/s17.json` y `out/s17_solo_tabla.json` **idénticos bit a bit** a los de la lectura. Estado INDECIDIBLE en las dos, controles OK, 271 pasadas por brazo (las tres del artefacto, 86 + 86 + 99 por día), P1 CUMPLE con 6 y 6, P2 SIN SUSTRATO (B 0 en VIIRS 375, B 1 en VIIRS 750), Chillán 0,456 → 0,493 y 0,447 → 0,508 como dice el README. No entra al veredicto (`combinar` sólo recibió v1 y v2).
- Lo que no se sostiene tal como está escrito: (1) el INDECIDIBLE de la ventana no sale del sustrato de P2 (SIN SUSTRATO no vuelve INDECIDIBLE nada, `regla_signos_p2` l. 558 a 559 y `global_ventana` l. 895) sino de **M en `VIIRS375|sin_kernel|z>40`**, modo `bloquea`, **7 pares y 4 noches**: la calibración simétrica de **d** da falsos EMPEORA 0,055 contra el tope 0,05, el estrato queda INDECIDIBLE (l. 720 y 723) y arrastra la ventana. El README lo atribuye a «calibración de d′ mal calibrada en un estrato de 6 pares»: el estrato de 6 pares (`VIIRS375|sin_kernel|z<=40`, regla original) es NEUTRO con calibraciones en verde (falsos MEJORA de d 0,050, justo en el tope, y de d′ 0,031); la de d′ en el de 7 pares también falla (0,064) pero no es la que decide, porque la rama de d′ sólo se mira cuando d da MEJORA aceptada (l. 738 a 748). Con 4 noches hay 16 repartos de signo y cada uno pesa 6,25 %: una calibración al 5 % no puede pasar, es el mismo mecanismo que D-44 punto 2 acepta para P2. En ese sentido estricto sí es «falta de sustrato», pero de M, no de P2, y con los números cambiados. Es V162-01. (2) La ventana evaluada no es «la configuración de V1»: se pasaron `--desde 2026-10-17 --hasta 2026-10-19` (segunda línea de `s17.log`: «VENTANA V1: 2026-10-17 a 2026-10-19»); sin eso el 19 habría quedado fuera (`hasta` de V1 es 2026-10-18) y la cobertura habría comparado 51 días contra 3. Esos argumentos no cambian ninguna regla (están declarados como tales en `main`, l. 1246 a 1247) pero faltan en «Cómo se reproduce».

### (g) Evaluador del tag (sha256 `93c26d62...`) y artefactos correctos. **CONFIRMADO EN PARTE**, gravedad 1.

- Contenido: `git diff a7418e01d e634f819f -- experiments/_s157_prereg_d25/evaluar_d25.py` vacío; `sha256sum` del archivo del worktree = `93c26d6262cee07c7bd2e78c295bed6c8e6d195193255fb529c4fbac5c04fec2`, el declarado. Pero el worktree tiene `core.autocrlf = true` y el archivo está en CRLF (`git ls-files --eol`: `i/lf w/crlf`); el blob de git (LF) da `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`. El evaluador es el del tag; el número declarado sólo se reproduce en un checkout con CRLF (V162-03). Las dependencias que importa (`evaluar_fk.py` y lo que éste trae, `volcanoes.yaml`, `frontend/index.html`, la referencia congelada) no cambian entre el tag y el HEAD (diff completo: 19 archivos, todos de `lectura_s162/`).
- Artefactos: sha256 de `V1.zip` = `57dda6e8...` = `digest` del artefacto `s146ab-todo` id 12351166319 del run 39530508296, creado el 2026-10-21 13:55:31 UTC (el del intento 2; el del intento 1, id 12333492433, es de las 09:12:22 y tiene otro digest y otro tamaño). `V2a.zip` = `b9f73f06...` = id 12348568591 del run 39575542584; `V2b.zip` = `57d801ad...` = id 12368769517 del run 39612909810; `S17.zip` = `35b5edfc...` = id 12417916188 del run 39756261926. Los cuatro runs corren el mismo `headSha` `66961f65d` en la rama `s157-d25-k-codigo`. Dentro de los artefactos: 4.610, 3.403, 3.366 y 271 records por brazo, ninguno fuera de su ventana, V2a y V2b sin solape (04-01 a 05-07 y 05-08 a 06-12), sólo sensores VIIRS. Lo que el README omite: el run 39530508296 tiene `conclusion: failure` (V162-02).

## Hallazgos propios

### V162-01. El README atribuye mal el INDECIDIBLE del brazo del 17 al 19 de octubre
- ARCHIVO: `experiments/_s157_prereg_d25/lectura_s162/README.md`, sección «Brazo del 17 al 19 de octubre», frase «M INDECIDIBLE (calibración de d′ mal calibrada en un estrato de 6 pares)». Dato: `lectura_s162/salidas/s17.json`, `por_regla.*.info["M|VIIRS375|sin_kernel|z>40"]`: `n 7, noches 4, calibrada false, falsos_empeora 0.055, falsos_mejora_dprima 0.064`; `info["M|VIIRS375|sin_kernel|z<=40"]`: `n 6, NEUTRO, calibrada true`.
- QUÉ PASA: con 4 noches el nulo tiene 16 repartos y ninguna regla al 5 % calibra; el estrato que sólo bloquea queda INDECIDIBLE por la cola EMPEORA de d (`evaluar_d25.py` l. 720 y 723), y la ventana con él. El texto nombra otra variable (d′) y otro estrato (6 pares).
- CÓMO SE VE EN EL DASHBOARD: invisible; el brazo no decide.
- CÓMO REPRODUCIRLO: `python -I CARPETA\extraer.py <salidas>\s17.json | grep -E "INDECIDIBLE|z>40|z<=40"`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (es el único brazo con los días de Chillán en erupción que D-29 sacó de V1; una razón mal escrita en el informe que Nicolás lee puede torcer cómo se pondera).

### V162-02. El run de V1 (39530508296, intento 2) terminó en failure y el README no lo dice
- SCRIPT:SALIDA: `gh run view 39530508296 --json attempt,conclusion` → `{"attempt":2,"conclusion":"failure"}`; `gh api .../runs/39530508296/attempts/2/jobs`: 45 jobs `reproc` y `plan` en success, `recolectar` en failure; pasos de `recolectar` (job 119262120032): «COBERTURA PAREJA antes de mirar nada (A108)» success, «Publicar las salidas en una rama propia de esta corrida» **failure**, «Subir tambien todo junto como artefacto» success. Log guardado en `CARPETA\recolectar_v1_att2.log`, l. 873 a 911: `! [rejected] s146-ab/39530508296 -> s146-ab/39530508296 (fetch first)`, cinco reintentos.
- QUÉ PASA: el intento 1 ya había creado la rama `s146-ab/39530508296`; el intento 2 no pudo empujar encima. El artefacto (digest verificado) y la cobertura pareja están en verde, así que la lectura es válida; pero quien mire el calendario de runs ve una corrida roja y tiene que cavar para saber que no es el A/B el que falló.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los comandos de arriba.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### V162-03. El sha256 declarado del evaluador depende de los finales de línea del checkout
- ARCHIVO: `README.md` l. 3 a 4 («sha256 `93c26d62...`, igual al del traspaso»). `git ls-files --eol experiments/_s157_prereg_d25/evaluar_d25.py` → `i/lf w/crlf`; `git show a7418e01d:experiments/_s157_prereg_d25/evaluar_d25.py | sha256sum` → `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`.
- QUÉ PASA: el número identifica el archivo con CRLF que Windows escribió, no el blob del tag. Un tercero en Linux, o con `git show`, no lo reproduce y puede concluir que el evaluador no es el del tag cuando sí lo es (`git diff` vacío). ADENDA_CALIBRACION ya anota «sha256 LF comprobados» para la referencia: el evaluador debería declararse igual (LF) o con las dos cifras.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### V162-04. Cinco pasadas no protegidas de Puyehue Cordón Caulle VIIRS 750 también cruzan 1 MW hacia abajo con D (informa)
- SCRIPT:SALIDA: barrido propio de `CARPETA\tmpV1\t_K_D.json` (misma tabla que usa el evaluador, antes de D-29 y de la protección): `PuyehueCordonCaulle|VIIRS750|2026-09-19 05:48` K 1,193 → D 0,482; `09-21 06:06` 1,000 → 0,608; `09-22 05:30` 1,228 → 0,409; `09-26 05:18` 1,722 → 0,813 (las cuatro `neg_limpio`, MIROVA miró y no vio nada); `09-29 06:42` 1,126 → 0,386 (`sin_info`).
- QUÉ PASA: P1b lista sólo protegidas (PREREGISTRO §5) y por eso el README dice «2 en Chillán», lo que es correcto. Pero la decisión que Nicolás tiene que tomar sobre P1b es si tolera que D25 baje de banda una magnitud de 1 MW o más; conviene que vea que en PCC pasa 5 veces en 51 días, en pasadas donde MIROVA no publicó alerta (ahí bajar es, a priori, acercarse a MIROVA). No entran a P2 porque los dos brazos publican en las cuatro `neg_limpio` (error en ambos, no discordante).
- CÓMO SE VE EN EL DASHBOARD: PCC VIIRS 750 pasaría de la banda Bajo a Muy Bajo en esas 5 pasadas si D25 se adoptara.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### V162-05. El string del estado de una ventana conserva el texto de la primera regla cuando las dos empatan en rango
- ARCHIVO: `evaluar_d25.py` l. 935 a 936 (`peor`) y l. 1085. Dato: `v1_solo_tabla.json`: `por_regla.SN.estado` dice «... en VIIRS375, VIIRS750: bloquea CUMPLE», `por_regla.original.estado` dice «... en VIIRS750 ...», y `estado` (el de la ventana) repite el de la original.
- QUÉ PASA: `min` con empate devuelve el primero; el sensor que bloquea sólo bajo la regla más estricta desaparece de la línea final y de lo que `--combinar` imprime. En V1 con tabla y OCR no se pierde nada porque las dos reglas dan el mismo texto; en la tabla sola el README lo rescató leyendo `por_regla`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## VERIFICADO LIMPIO (qué miré y está sano, con la vara)

| ítem | vara | comando |
|---|---|---|
| Reproducción V1 | JSON idéntico bit a bit; log idéntico sin CR (las 4 líneas de más en el de la lectura son el trailer de `time`) | `cmp out/v1.json <salidas>/v1.json`; `diff --strip-trailing-cr out/v1.log <salidas>/v1.log` |
| Reproducción V2 (V2a + V2b, `--ruido-de` con mi v1.json) | idéntico bit a bit; log 0 líneas distintas | `cmp out/v2.json <salidas>/v2.json` |
| Reproducción V1 tabla sola, S17 y S17 tabla sola | idénticos bit a bit; logs 0 líneas distintas | `cmp out/<f>.json <salidas>/<f>.json` |
| Combinado | idéntico | `diff --strip-trailing-cr out/combinado.log <salidas>/combinado.log` |
| Determinismo del evaluador | dos corridas (la de la lectura y la mía) en máquinas y horas distintas dan los mismos bytes; `argsort` y los sorteos con semilla no introdujeron diferencia aquí | lo anterior |
| Artefactos | sha256 de los 4 zips = `digest` de GitHub del `s146ab-todo` de cada run; V1 es el del intento 2 (13:55:31 UTC) | `sha256sum *.zip`; `gh api repos/MendozaVolcanic/VRP-chile/actions/runs/<id>/artifacts` |
| Cobertura de los artefactos | 4.610 / 3.403 / 3.366 / 271 records por brazo, 0 fuera de ventana, V2a y V2b sin solape, sólo VIIRS; en V1 hay 86 records del 17-oct que D-29 saca y 0 del 13 y del 18; los 86 del 17-oct de V1 y de S17 son las mismas pasadas con el mismo `pc.vrp_mw` | script en la sesión (bloque «fechas en artefacto») |
| Evaluador = tag | `git diff a7418e01d e634f819f` sólo toca `lectura_s162/`; tag local = `origin` (`724e43452` → `a7418e01d`) | `git diff --stat a7418e01d e634f819f`; `git ls-remote --tags origin s161-d25-lectura` |
| P2 (D-45) | neto, B y valor-p recomputados por enumeración propia desde `discordantes` coinciden en las 4 ventanas-sensor y en las 2 reglas; con B > 20 los sorteos quedan a menos de 0,002 del exacto | bloque «recomputo independiente P2» y «p exacto B=43» |
| P1b | lista exacta de 2; el barrido sin filtros encuentra 7, lo que prueba que el instrumento ve cruces y filtra por la regla | bloque «estructura t_K_D.json» |
| Envoltorios | cada uno leído entero; sólo tocan lo que declaran; el flag `solo_tabla` llega al OCR vacío y a la exclusión de Suomi NPP | `cat envoltorios/*.py`; `evaluar_fk.py` l. 109 a 118 |
| `tabla()` no cachea | `E.tabla` vuelve a correr `armar_tabla` y sobrescribe `out` en cada llamada: un `--tmp` reutilizado no puede arrastrar una tabla vieja (camino 35 cerrado) | `evaluar_fk.py` l. 123 a 131 |
| §8 d en el código | `global_ventana` y `combinar` reproducen las filas de la tabla y las adendas D-34 §5.5 y D-45 §2.6; el EMPEORA de un estrato `informa` no entra | `evaluar_d25.py` l. 881 a 921, 1201 a 1228 |
| Controles de las dos ventanas | cobertura pareja, versión, determinismo (2.271 y 2.253 de 2.271 y 2.253 en V1; V2 sin gemelo), referencia congelada (V1 Mirova-v1@`35a5ea86`, V2 @`c5944c61`), cableado OK en K, G y D | `grep -n "OK\|FALLA" <salidas>/v1.log v2.log` |
| Versiones | Python 3.12.10, numpy 2.4.4, las de D-47 | `python -c "import sys,numpy;print(sys.version,numpy.__version__)"` |

## SIN DATO

- La relación entre las 24 y 22 protegidas que K publica en V1 según el evaluador y las 31 y 29 «que deciden» de la tabla del §4 del pre-registro (medidas sobre K en disco antes del A/B). En VIIRS 375 cuadra (24 + 7 sólo OCR de Suomi NPP = 31); en VIIRS 750 el evaluador ve 24 que K publica (22 + 2) contra 31 del §4. La diferencia puede venir de los días de D-29 (Chillán en erupción el 13 y el 17) o de que el K del brazo no publique lo mismo que el K de producción; no lo medí y el README no lo afirma.
- Si la secuencia de sorteos de numpy (B > 20, semilla 162) es la misma en otra versión de numpy: D-47 lo deja anotado, aquí sólo comprobé que con la misma versión los bytes coinciden.
- El contenido de los logs de los jobs (`FLAGS_BRAZO`) y el predicado de `index.html` con node: confié en los controles del evaluador, que los leen y los imprimen OK; no los abrí.

## Comandos de la re-corrida (desde `C:\vrp-trabajo\s159-evaluador`, `D25` = carpeta de los artefactos ya bajados)

```bash
python experiments/_s157_prereg_d25/evaluar_d25.py --ventana V1 --raiz $D25/V1 --logs $D25/V1/logs --calibracion simetrica --tmp CARPETA/tmpV1 --out CARPETA/out/v1.json
python experiments/_s157_prereg_d25/evaluar_d25.py --ventana V2 --raiz $D25/V2a --raiz $D25/V2b --logs $D25/V2a/logs --logs $D25/V2b/logs --ruido-de CARPETA/out/v1.json --calibracion simetrica --tmp CARPETA/tmpV2 --out CARPETA/out/v2.json
python experiments/_s157_prereg_d25/lectura_s162/envoltorios/v1_solo_tabla.py --ventana V1 --raiz $D25/V1 --logs $D25/V1/logs --calibracion simetrica --tmp CARPETA/tmpV1t --out CARPETA/out/v1_solo_tabla.json
python experiments/_s157_prereg_d25/lectura_s162/envoltorios/s17_sensibilidad.py --ventana V1 --raiz $D25/S17 --logs $D25/S17/logs --desde 2026-10-17 --hasta 2026-10-19 --calibracion simetrica --tmp CARPETA/tmpS17 --out CARPETA/out/s17.json
python experiments/_s157_prereg_d25/lectura_s162/envoltorios/s17_sensibilidad.py solo_tabla --ventana V1 --raiz $D25/S17 --logs $D25/S17/logs --desde 2026-10-17 --hasta 2026-10-19 --calibracion simetrica --tmp CARPETA/tmpS17t --out CARPETA/out/s17_solo_tabla.json
python experiments/_s157_prereg_d25/evaluar_d25.py --combinar CARPETA/out/v1.json CARPETA/out/v2.json
```

sha256 de mis salidas: v1.json `f95997976f14d98ef1e57bb6a2f5b2c4fb3bfe0a2fda860e35a87b98179984f4`, v2.json `77ba866b1237f43b02c351c917d47abd87fbe61f33d8cf70253562a7970ba20f`, v1_solo_tabla.json `1e945f5770e1aa9a5eafdb41ebf7744aa30aa35392a637ca6b414391ff693748`, s17.json `1e761eff3d84cf3d269c920a129e72b01da165f38d5175b0e6bf1c98845a7555`, s17_solo_tabla.json `96a68c7d4a0c8bb255f1607ba952d1803724b729899d0b23475a2afc40301ebd`. Salidas auxiliares en CARPETA: `extraccion_lectura_v1_v2.txt`, `extraccion_lectura_v1_solo_tabla.txt`, `extraccion_lectura_s17.txt`, `recolectar_v1_att2.log`, `extraer.py`.
