# Verificación de la regla de reversión de MOD-D (borrador S171) antes de su sello

## 1. Encabezado

- Fecha y hora del servidor (GitHub, `gh api -i`): inicio 2026-11-02 12:20:27 GMT, cierre 12:39:04 GMT.
- Objeto: `origin/loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, 139 líneas, copia en
  `D:/vrp-trabajo/temporales/s173_aud/vr/regla_copia_origen_loop_activo.md` (sha256 `77f7f37c066ab192...a00f6a7`).
  `origin/loop/activo` = `da7cf5535`.
- Código medido: punta de B `c9525f994` (worktree `D:/vrp-trabajo/worktrees/s172-modd-encendido`, sólo lectura), punta
  de A `0a0dae344`, `origin/main` del día `c3540b731` al empezar y `47cdc446f` al simular la reversión. Base real de
  B: merge-base con main `d3cd0b2ae` (el prompt decía `a3c5a9b49`; es anterior, B va 20 commits por delante de main
  y main 36 por delante de B, sin choque).
- Modelo y esfuerzo reales: claude-fable-5-1 (Fable 5.1). El esfuerzo no es visible desde la sesión: lo fijó el
  orquestador, SIN DATO desde aquí.
- CARPETA: `D:/vrp-trabajo/temporales/s173_aud/vr/` (caminos.md sellado, sha256 `24863f402c51...ccc9ba2`, hora del
  servidor 12:22:28 GMT, intacto al cierre; scripts con su salida al lado; `hallazgos.csv`).
- Prompt leído: `D:/vrp-trabajo/temporales/s173_aud/prompts/verificador_vr.txt`, sha256 real
  `4e6d6d8763a9...fae5502`. El orquestador dijo que empezaba en `3fdf1310`: NO coincide. Lo leí entero igual; si el
  archivo cambió después de que el orquestador lo firmó, el orquestador lo sabe mejor que yo.
- Qué NO miré: no corrí la guardia ni la vigilancia en Actions (ningún despacho); no corrí la suite completa de
  pruebas (sólo archivos explícitos, 54 pruebas en total); no abrí el informe de la mini auditoría S172
  (`experiments/_s172_miniaud/`) ni el de la implementación (`INFORME_IMPLEMENTADOR.md`) para no heredar supuestos;
  no leí datos de la ventana P; no verifiqué la calidad geométrica de la cabecera de las imágenes de MIROVA, sólo
  que hoy existen y se siguen capturando.
- Incidente propio, declarado: `git worktree add` con `MSYS_NO_PATHCONV=1` y ruta `/d/...` creó el worktree
  desechable en `C:/d/vrp-trabajo/worktrees/s173-vr-revert` (fuera de mi carpeta). Lo quité con
  `git worktree remove --force` sin haber corrido nada ahí (el `cd` falló antes del merge; el árbol de la
  coordinadora quedó intacto: `git status` sólo con los tres untracked de siempre). Quedan las carpetas VACÍAS
  `C:/d/vrp-trabajo/worktrees/` que el guard de seguridad no me dejó borrar: las borra Nicolás. El segundo worktree,
  en `D:/vrp-trabajo/worktrees/s173-vr-revert`, se usó y se quitó; D: quedó en 4,8 GB libres (bajó a 3,6 GB mientras
  existía).

## 2. En una pantalla

- **Veredicto: SELLABLE CON CAMBIOS.** El instrumento que ejecuta la regla (`scripts/vigilancia_guardia_modis.py`,
  guardia `guardia_k_modis.yaml` + `guardia-k-modis.yml`) existe en B, cubre los cinco casos ciegos que pedía la tarea,
  pasa 45 de 45 pruebas, y la reversión simulada sobre el main de hoy es limpia (0 conflictos, flag `False` por A89,
  árbol idéntico a main). Las cotas 12/10/2 y 42/39/3, neto -44, B 53, el 62,5 % en 16 noches, el 0,56 de Chillán y
  sus tres protegidas de octubre se reproducen desde los archivos citados (sha256 iguales).
- Pero el TEXTO no se puede aplicar tal cual por cinco cosas: (1) nombra una constante que no existe
  (`CAMBIO_DETECTOR_MODIS_UTC`, 0 archivos en B) mientras el instrumento ancla el encendido en los datos; (2) deja las
  cotas (i) y (ii) como «propuesta, la fija Nicolás» y el denominador «SIN DATO» (medido aquí: 43 `bajo1` y 5.321
  `neg_limpio` en 240 días; «más de 2 en 120 días» es el doble de laxo que la tasa del A/B); (3) pre-autoriza sólo
  «calla» y no dice qué pasa con una protegida de la que producción NO tiene record (el borde 171-01, que es el peor
  caso que la propia regla declara); (4) «rachas … (f) de K» apunta a un disparador de persistencia que MODIS no tiene;
  (5) «git revert del PR de encendido» no dice cuál PR, y hoy no hay ningún PR abierto para A ni para B.
- Lista exacta de cambios de texto en §5. Con esos cambios, dos lectores llegan a la misma decisión con los mismos
  datos; sin ellos, no.

## 3. Hallazgos (ordenados por gravedad)

### VR-01
- TÍTULO: La regla ancla la vigilancia en una constante que no existe en el código (`CAMBIO_DETECTOR_MODIS_UTC`); el instrumento usa otro corte
- ARCHIVO:LÍNEA: regla l. 93; `git grep -l CAMBIO_DETECTOR_MODIS_UTC` en B = 0 archivos (control positivo: `CAMBIO_DETECTOR_UTC` de K sí aparece en `frontend/cambio_detector.js:29`); `scripts/vigilancia_guardia_modis.py:33-39` y `:98-115` (`encendido_desde_datos`: el menor `processed_utc` de un record MODIS de producción con `via_codigo_mirova: true`); `frontend/cambio_detector.js:135-136` (la marca del tablero sale de los datos, con «K antes»).
- QUÉ PASA: la regla dice «cuenta desde el encendido (`CAMBIO_DETECTOR_MODIS_UTC`, la hora del merge al segundo)». Nadie llena esa constante y el código decide el corte de otra forma: la primera corrida del NRT que escribió un record de la vía, que llega horas después del merge. Las pasadas observadas entre el merge y esa primera escritura caen del lado retrospectivo (no disparan reversión; si la vía las re-escribe, van a «borde del encendido», investigar). Dos lectores (uno con la hora del merge, otro con el instrumento) clasifican distinto las mismas pasadas.
- CÓMO SE VE EN EL DASHBOARD: invisible (el tablero marca la fecha desde los datos, `insertarAvisoModis`); se ve en el issue de la vigilancia, que puede no abrirse para una pérdida de las primeras horas.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/worktrees/s172-modd-encendido && git grep -n CAMBIO_DETECTOR_MODIS_UTC` (vacío) y `sed -n 98,115p scripts/vigilancia_guardia_modis.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4. Decide qué pasadas pueden revertir y cuáles no, y el texto y el código no coinciden.

### VR-02
- TÍTULO: La regla pre-autoriza sólo «calla» y no nombra el caso ciego que ella misma declara peor: la guardia publica y producción no tiene record (borde 171-01)
- ARCHIVO:LÍNEA: regla l. 25-28 y 96-97; `scripts/vigilancia_guardia_modis.py:82-84` (`ESPERA_SIN_RECORD_H = 24`, «la fija Nicolás al sellar la regla»), `:266-270` (INVESTIGAR, no reversión), `:200-201` (`calla` exige `prod_pub is False`, o sea record presente); `scripts/vigilancia_sombra.py:178-180` («Sin record de producción no es “calla”»); prueba `tests/test_vigilancia_guardia_modis_s172.py:109`.
- QUÉ PASA: la vía descarta en silencio los gránulos que no cubren el volcán (100 celdas a 45 km y centro a más de 5 km, `pipeline/mirova_v750_codigo.py:803-808`, `FAMILIAS["MODIS"]["dist_max_centro_km"] = 5.0` l. 112; VIIRS 750 no tiene ese corte). Para el operador el silencio es el mismo que «calla», pero la regla sólo pre-autoriza revertir cuando hay record que no publica; el instrumento lo resuelve con una espera de 24 h y un issue de investigar, con un número que el texto no menciona y que «fija Nicolás al sellar». Lo mismo pasa con los otros casos ciegos: guardia muerta (`revisar_guardia_modis.py` FALLA el job + aviso de frescura), referencia sin filas de MODIS (`avisos_referencia_modis`), cero pares en el nulo (MA172-208), upgrade NRT a estándar (resuelto con `processed_utc`, no `first_processed_utc`, l. 33-39), vía encendida sin records de la vía (`avisos_via`). El código los cubre todos y los convierte en `VIGILANCIA_CIEGA` o `INVESTIGAR`; la regla sellada no dice ninguno, así que un lector de la regla no sabe que un VERDE con aviso no es VERDE.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero (el operador ve una noche de MODIS sin alerta); visible sólo en el issue «Guardia K de MODIS: investigar» tras 24 h.
- CÓMO REPRODUCIRLO: `python -m pytest -p no:cacheprovider -q tests/test_vigilancia_guardia_modis_s172.py -k "sin_record_de_produccion or ciega or nulo_sin_pares"` en B (pasan); leer regla l. 96-99 y buscar «sin record»: no está.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4. Es el peor caso declarado por la regla y la regla no dice qué hace con él.

### VR-03
- TÍTULO: Las cotas (i) y (ii) quedan como «propuesta» con denominador «SIN DATO»; medido por otro camino, «más de 2 en 120 días» duplica la tasa del A/B
- SCRIPT:SALIDA: `D:/vrp-trabajo/temporales/s173_aud/vr/contar_cotas_f4.py` → `contar_cotas_f4_salida.txt`; `denominador_f4.py` → `denominador_f4_salida.txt`. Insumos: `resultado_f4.json` de `origin/claude/s170-modd-f4-procedencia` (sha256 `312e2050c680...4129d`, igual al de la regla l. 102-103) y `poblacion_f4.json` de la misma rama (sha256 `e8315ba4ff93...3be8`, igual al que `resultado_f4.json` declara en `insumos_lectura`). Signo de `c`: PREREGISTRO_MODD_F4.md l. 155 (TEXTO): «+1 si el error es sólo del brazo, −1 si es sólo de K». Código del instrumento: `scripts/vigilancia_guardia_modis.py:76-78` (`COTA_MUY_BAJO = 2`, `COTA_SOBREPUBLICACION = 3`, `dispara = k > cota`).
- QUÉ PASA: los conteos de la regla se reproducen exactos: 54 discordantes, 12 `bajo1` (10 con c = −1, a favor de la vía; 2 con c = +1, a favor de K), 42 `neg_limpio` (39 y 3), neto −44, B 53, p_gana [1, 10001], discordantes del 2026-03-04 al 2026-10-26. El denominador que la regla declara SIN DATO sí está en la población del A/B: **43 pasadas `bajo1` y 5.321 `neg_limpio`** (tramo C 2026-03-01 a 10-16 más E 10-17 a 10-26, 5.709 pasadas, 240 días). Así, el A/B perdió 2 de 43 Muy Bajo (4,7 %) y sobre-publicó 3 de 5.321 (0,06 %) en ocho meses; la regla propone «más de 2» y «más de 3» en 120 días, o sea tolera el doble por unidad de tiempo, sin decirlo, y en términos absolutos sin proporción (A90). Y lo deja escrito como «propuesta, la fija Nicolás»: una regla sellada con una propuesta adentro no decide sola.
- CÓMO SE VE EN EL DASHBOARD: invisible; es la vara del issue «investigar».
- CÓMO REPRODUCIRLO: `python -I contar_cotas_f4.py resultado_f4_copia.json` y `python -I denominador_f4.py D:/vrp-trabajo/temporales/s173_aud/vr/poblacion_f4_copia.json` (controles: filtrar otra clase da 42; filtro imposible da 0).
- CONFIANZA: CONFIRMADO (los números); la lectura «el doble de laxo» es aritmética sobre esos números.
- GRAVEDAD: 3. No revierte nada por sí sola, pero fija cuándo se investiga, y hoy no está fijada.

### VR-04
- TÍTULO: «Pasadas juzgadas y rachas: como (d) y (f) de K» cita un disparador de persistencia que la regla de MODIS no tiene
- ARCHIVO:LÍNEA: regla l. 110; modelo de K `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` (main) l. 160-163 ((f): «una racha de persistencia ya investigada … deja de disparar») y l. 176-177 ((ii) persistencia: tres noches seguidas); `experiments/_s171_modd_adopcion/sombra_pasadas_juzgadas_modis.json` en B, campo `nota_rachas` (TEXTO): «Sin sección de rachas: el diseño de la vigilancia de MODIS (decisión 3) no tiene disparador de persistencia»; `grep -n -i racha scripts/vigilancia_guardia_modis.py` = 0.
- QUÉ PASA: K investiga tres noches seguidas con una alerta que la sombra publica y producción no; la regla de MODIS no copió ese disparador (sus (i), (ii), (iii) son otros) pero sí copió la cláusula de rachas que sólo tiene sentido con él. Un lector cree que existe vigilancia de persistencia en MODIS; nadie la computa.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n -i "racha\|persist" scripts/vigilancia_guardia_modis.py` (vacío) contra regla l. 110.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Una pérdida repetida tres noches sin protegida no dispara nada y el texto sugiere lo contrario.

### VR-05
- TÍTULO: «`git revert` del PR de encendido» no dice qué PR; no existe PR para A ni para B; y el revert no deshace los records ya escritos por la vía
- SCRIPT:SALIDA: simulación en worktree desechable `D:/vrp-trabajo/worktrees/s173-vr-revert` (ya quitado), salida en este informe: (a) merge `--no-ff` de `c9525f994` sobre `origin/main 47cdc446f` → `9c80a1661`; `git revert -m 1`: 0 conflictos, `ENABLE_MODIS_CODIGO_MIROVA = False` por A89, `git diff --stat origin/main HEAD` vacío (árbol idéntico al main del día); (b) main + A (`0a0dae344`) + squash de los 9 commits del flip, revert del squash: 0 conflictos, flag `False`, `guardia_k_modis.yaml` sigue; pruebas del flag sobre el árbol revertido: 9 pasan (`tests/test_mirova_modis_codigo_s164.py -k flag`, `tests/test_guardia_k_modis_s172.py`). `gh pr list --state all` filtrado por las dos ramas: ninguna fila. Tag `pre-s171-adopcion-modd` = `d3cd0b2ae`, empujado (`git ls-remote --tags`), es el merge-base de B con main.
- QUÉ PASA: la reversión ES ejecutable y limpia hoy por los dos caminos. Lo que la regla no fija: (1) si A y B se mergean como un solo PR, el revert apaga también la guardia, su vigilancia y la marca del tablero (camino a), y la vigilancia de K (`vigilancia_sombra.py`) vuelve a confundir records de la vía con K (ver el diff de B en ese archivo); si se mergean por separado, se revierte sólo el flip y la guardia sigue (camino b). La regla y `vigilancia_guardia_modis.py:17` dicen «PR B» sin definir qué contiene; en B el workflow (`vigilancia-guardia-modis.yml:10`) también. (2) El revert no toca `data/mirova_equivalent/`: los records escritos por la vía entre el encendido y la reversión siguen con `via_codigo_mirova: true` hasta que el NRT los re-escriba (hasta 8 días hacia atrás, `guardia-k-modis.yml:117`), y lo anterior a esa ventana queda de la vía para siempre. La lección ya está escrita para K (`docs/FICHA_SDA_VRP_CHILE.md` l. 25, «la reversión ya no es un git revert limpio … no deshace los datos»): la regla de MODIS no la hereda.
- CÓMO SE VE EN EL DASHBOARD: tras el revert, la marca «desde el … la serie de MODIS viene de la vía» sigue dibujada mientras queden records de la vía (`primeraViaModis` los lee de los datos): el operador vería una marca de encendido sin marca de apagado.
- CÓMO REPRODUCIRLO: `git worktree add --detach D:/vrp-trabajo/worktrees/s173-x origin/main && cd … && git merge --no-ff c9525f994 && git revert -m 1 HEAD && VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"`.
- CONFIANZA: CONFIRMADO (simulado hoy).
- GRAVEDAD: 3. La acción pre-autorizada es ejecutable, pero cuánto apaga depende de cómo se mergee, y eso no está escrito.

### VR-06
- TÍTULO: «confirmada en la cabecera de la imagen de MIROVA» no dice quién confirma, en cuánto tiempo, ni qué pasa si la imagen falta: la regla «decide sola» pero deja un paso humano sin plazo
- ARCHIVO:LÍNEA: regla l. 96-99; `scripts/vigilancia_guardia_modis.py:16-17` y `:437-439` («Confirmar en la cabecera … antes de revertir»); `.github/workflows/vigilancia-guardia-modis.yml:9-10` y `:132` («La reversion la confirma una persona»). Disponibilidad hoy: `mirova-tif-archive` sigue capturando (3 commits «poll» entre 11:19 y 11:27 UTC del 2026-11-02; `index_png.csv` 164.703 filas, 96 filas MODIS con fecha de hoy).
- QUÉ PASA: la imagen existe hoy, así que la condición es cumplible; pero la regla no acota la confirmación (¿la sesión que detecta? ¿Nicolás? ¿hasta cuándo?) ni dice qué hacer si MIROVA deja de servir imágenes (ya pasó con los TIF en septiembre). Sin plazo, «se vuelve atrás sin esperar a nadie» (l. 23) y «confirmada en la cabecera» (l. 97) se contradicen: un lector revierte el mismo día, otro espera la confirmación indefinidamente.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer l. 23 y l. 96-99; `gh api repos/MendozaVolcanic/mirova-tif-archive/commits?per_page=3`.
- CONFIANZA: CONFIRMADO (la ambigüedad); la disponibilidad futura de la imagen es SIN DATO.
- GRAVEDAD: 3. Puede retrasar o impedir una reversión que la regla dice pre-autorizada.

### VR-07
- TÍTULO: La regla que todo el código de B cita vive sólo en `loop/activo`: no está en B ni en main
- ARCHIVO:LÍNEA: `git ls-files | grep REGLA_REVERSION_MODD` en B = 0; `git ls-tree -r origin/main | grep` = 0; la citan `pipeline/profiles/guardia_k_modis.yaml:1`, `.github/workflows/guardia-k-modis.yml:3`, `vigilancia-guardia-modis.yml:3`, `:132-136` (cuerpo de los issues), `scripts/vigilancia_guardia_modis.py:3`, `:402`, `scripts/revisar_guardia_modis.py:4`, `sombra_pasadas_juzgadas_modis.json`.
- QUÉ PASA: tras el merge, los issues que abre la vigilancia mandan a leer un archivo que main no tiene, y la versión que se selle puede diferir de la que B cita (B cita «borrador»). La sesión que detecte una candidata tiene que saber ir a otra rama para leer la regla que la autoriza.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los dos `git ls-tree` de arriba.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VR-08
- TÍTULO: §3 conserva tres versiones contradictorias de la guardia sin decir cuál rige; la implementada es la última («Guardia recomendada»)
- ARCHIVO:LÍNEA: regla l. 39-44 («Opción preferida (a verificar)»: la sombra con MODIS en K), l. 46-53 (corrección S172), l. 55-72 («Resultado de S172 … texto original»), l. 82-87 («Guardia recomendada»). Lo implementado en B: `pipeline/profiles/guardia_k_modis.yaml` (`extends: mirova_equivalent`, `thresholds.enable_modis_codigo_mirova: false`, sólo MODIS, `data_subdir: guardia_k_modis`, l. 22-40) y `.github/workflows/guardia-k-modis.yml` (cron `40 17 * * *`, ventana «hoy y 7 días atrás», timeout 75 min, revisión `revisar_guardia_modis.py`). Por A89: `VRP_PROFILE=guardia_k_modis` → flag `False`, `DATA_SUBDIR=guardia_k_modis`, MODIS True / V375 False / V750 False, `ENABLE_MODIS_B22_PRIMARY` True (la clave está en la raíz del YAML, l. 42, y `profile.py:636` la lee de la raíz: bien cableada). La sombra sigue con las tres vías (`sombra_codigo_mirova.yaml:30-32`; `sombra-codigo-mirova.yml:110` asserta `p.ENABLE_MODIS_CODIGO_MIROVA`).
- QUÉ PASA: un lector que aplique «Opción preferida» edita la sombra y rompe la aserción de su workflow (que el S8 del lector de V375-E compara como texto, `RUTAS_REGIMEN` l. 95 del lector re-sellado). El texto sellado debe decir la guardia que corre y degradar el resto a historia.
- CÓMO SE VE EN EL DASHBOARD: invisible (la guardia no se publica).
- CÓMO REPRODUCIRLO: los comandos A89 de arriba en B.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VR-09
- TÍTULO: El disparador de reversión (l. 96) no dice «nocturna» y cita «regla SN de D-9», que para MODIS no hace nada
- ARCHIVO:LÍNEA: regla l. 96 contra l. 111 («29 protegidas A nocturnas»); `scripts/vigilancia_sombra.py:132-139` (`pasadas_de_alerta`: «Cada pasada nocturna»; `minima`: «todas sus alertas de 0,05 MW o menos en VIIRS 375»), `:119-125` (`_diurna_por_defecto` → `es_pasada_diurna_descartada`); `ENABLE_DAYTIME_MODIS = False` en producción y en la guardia (A89); `scripts/clase_mirova.py::aplicar_regla_minimas` citada por el prompt (D-9 es de VIIRS 375).
- QUÉ PASA: MODIS diurno no se procesa en ningún perfil, así que una alerta diurna de MIROVA nunca tiene record en guardia ni en producción y no dispara (no es «calla»). El efecto práctico es el que la regla quiere, pero el texto del disparador y el de la duración no usan la misma población, y «regla SN de D-9» le hace creer al lector que hay un corte de 0,05 MW en la protegida de MODIS, cuando el único corte es 1 MW (lectura A).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_DAYTIME_MODIS)"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VR-10
- TÍTULO: (ii) «publicación de MODIS en negativos limpios por sobre lo que midió el A/B» se lee como conteo absoluto; el instrumento cuenta sólo donde la guardia, con la misma pasada, no publica
- ARCHIVO:LÍNEA: regla l. 105-108; `scripts/vigilancia_guardia_modis.py:215-232` (`r["pub"] and not any(x["pub"] for x in g)`, con `g` = records de la guardia a ±120 s; sin guardia, la pasada no cuenta). Tasa absoluta de K en negativos limpios: 12 de 1.194 (1,0 %) en el audit del 2026-10-26 (`latest_audit_20261026.json`, `falsas_publicaciones/por_sensor/MODIS`).
- QUÉ PASA: leído literal, en los primeros 120 días producción publicaría en negativos limpios más de 3 veces casi seguro (K sola ya hizo 12 en 60 días) y el issue se abriría sin que la vía haya cambiado nada. El instrumento mide lo diferencial, que es lo que midió el A/B (c = +1). Falta decirlo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: regla l. 105-108 contra `sed -n 215,232p scripts/vigilancia_guardia_modis.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VR-11
- TÍTULO: «hasta ver 29 protegidas … en la guardia» no dice si «ver» es tener record o publicar; el instrumento cuenta record
- ARCHIVO:LÍNEA: regla l. 111; `scripts/vigilancia_guardia_modis.py:190-191` (`p["protegida"] and p["guardia_pub"] is not None`), `:276-278`; potencia: 1 − 0,9^29 = 0,9529 (calculado), coincide con «95 %». Ritmo: 16 protegidas A de MODIS en 11 noches en los 60 días del audit del 2026-10-26 (`alertas_protegidas.lista`, 13 publicadas y 3 sin publicar): a ese ritmo las 29 llegan hacia el día 110, así que «lo probable es que mande el plazo de 120 días» (l. 115) es borde, no probable.
- QUÉ PASA: con «publica», el plazo se alargaría (la guardia no publica todas las protegidas); con «tiene record», es lo que corre. Y la frase de probabilidad del plazo no se sostiene con el ritmo medido.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I -c "print(1-0.9**29)"`; conteo de protegidas MODIS en `latest_audit_20261026.json`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VR-12
- TÍTULO: Citas con línea corrida o incompleta, y afirmaciones que B ya dejó atrás
- ARCHIVO:LÍNEA: (a) regla l. 47 «`RAIZ = AQUI.parents[2]`, l. 47» → en el lector re-sellado (`s172-v375e-lector-resellado:experiments/_s168/v375e_sombra/leer_sombra_v375e.py`) es l. 49; `SHA_SELLO_LECTOR` l. 63-77 ✓. (b) regla l. 28 «`mirova_v750_codigo.py:805-808`» cubre sólo el corte de 5 km; el de 100 celdas es l. 804 (archivo idéntico entre `478d9c086` y B). (c) regla l. 120-121 «`test_mirova_modis_codigo_s164.py` l. 54 a 81 fijan `False`» → en B ya fijan `True` para `mirova_equivalent` y `False` para `experimental` y `guardia_k_modis` (l. 73-77); `test_guard_declarado_vs_efectivo_s131.py:158` es un comentario ✓; `test_guard_perfiles_congelados_s153.py` existe y cubre los derivados por `extends` (l. 46-50). (d) regla l. 76-77 «consumidores … sólo `process_modis.py` y `process_viirs_mod.py`» vale para las claves del perfil dentro de `pipeline/` (el lector re-sellado lo repite en `CLAVES_PERFIL_OTRO_SENSOR`, l. 111-113, con `git grep` en `ffccf6c9f`), pero el flag lo leen además la guardia, la sombra (`sombra-codigo-mirova.yml:110`), `vigilancia_guardia_modis.py:129-138` y cinco tests: la frase describe el perfil, no «consumidores del flag» en el sentido del prompt. (e) regla l. 5 «Lo marcado A COMPLETAR» → no queda ninguna marca (1 sola aparición, la frase misma). (f) «N-3» (l. 99) no se define en la regla: es la regla de Suomi NPP OCR de las adendas de V375-E/V750 (`tasks/BLOQUE_ARRANQUE_S167.md:22,73`). (g) «sombra prospectiva de 28 noches» (l. 21) y «~19 UTC» (l. 87): SIN LOCALIZAR en `LOOP_OBJETIVOS.md`, `LOOP_VIIRS375.md` ni `PREREGISTRO_E.md` (este último l. 50 sí da el 2026-11-03 como inicio de la ventana P).
- QUÉ PASA: ninguna cambia una decisión; todas hacen que un tercero que repita la cita no la encuentre donde dice.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: cada comando está en la línea.
- CONFIANZA: CONFIRMADO; (g) SIN LOCALIZAR.
- GRAVEDAD: 1.

## 4. Secciones aparte

### VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- **El flag y su lectura (A89), contra `pipeline.profile` y no el YAML**: B `mirova_equivalent` → `ENABLE_MODIS_CODIGO_MIROVA = True`; `guardia_k_modis` → `False`; `sombra_codigo_mirova` → `True`; A (`0a0dae344`) no tiene la clave en el YAML (default `False`, `profile.py:909`, `_t = _cfg["thresholds"]` l. 79, como dice la regla l. 32-34). La frase «falta comprobarlo importando pipeline.profile antes de sellar» (l. 34) queda cumplida aquí.
- **Los tres flags de MxD03 y las vías de VIIRS siguen apagados en producción**: `[False, False, False]`, `V750_VIA False`, `V375_VIA False` (A89), como piden l. 34-35.
- **S8 del lector de V375-E re-sellado no marca régimen con el PR B** (vara: las funciones del propio lector, copiadas a `s8_regimen_pr_b.py`, sobre `git diff origin/main...c9525f994`): 6 archivos de `RUTAS_REGIMEN` cambian, ninguno cuenta (`process_modis.py` cambia sólo comentarios; `mirova_equivalent.yaml` sólo la clave excluida; los otros perfiles no están en `PERFILES_REGIMEN`). Controles: un comentario da False, una línea de código True, sólo el flag de MODIS False, otra clave True. Sostiene la regla l. 78-79 y 82-85 (`guardia_k_modis.yaml` no está en `PERFILES_REGIMEN`, `guardia-k-modis.yml` no está en `RUTAS_REGIMEN`: verificado en l. 95-96 del lector).
- **Cotas del A/B**: ver VR-03 (reproducidas exactas; denominador resuelto).
- **62,5 % en 16 noches, ventana 2026-08-27 a 2026-10-26**: `489113c1f:data/audit_continuous/latest.json` (`recall/MODIS`: `n_noches 16, recall_dash_pct 62.5`; `window`), copia `latest_audit_20261026.json`. Y el «16 noches con alerta en 60 días» de l. 114 es el mismo número.
- **Chillán 0,56 y tres protegidas de octubre**: 0,56 = `magnitud_publicada_by_vol_sensor["NevadosDeChillan|MODIS"].ratio_mediano` (n 8 noches) del mismo audit; en `resultado_f4.json` la razón de K en Chillán es 0,362 mediana (12 pares) y 0,56 sólo en el tramo de cenit 20-30: la regla toma el número del audit, no del A/B, y no lo cita; las «tres de octubre» son 3 de las 4 `chillan.recuperadas` (`chillan_f4.py`).
- **Veredicto del A/B y tag**: `resultado_f4.json` `veredicto = "PROPONER ADOPCIÓN"`, commit `e0bb1b150` «relectura … desde el tag s170-modd-f4-lectura»; tag existe (`bb2cb9283`).
- **Decisión de Nicolás, verbatim**: `tasks/LOOP_OBJETIVOS.md` §6, entrada «2026-10-31 21:55 UTC (S171)», l. 732-733 (TEXTO): «hagamos todo lo recomiendas, analiza diferentes perspectivas, tenemos que probar todo y acercanos a los objetivos». Coincide con la regla l. 9-10.
- **Modelo de K, paso 9 y decisiones (a) a (f) del 2026-10-19**: `REGLA_ADOPCION.md` (main) l. 137-175, leído; (a) pasada, (b) desde la adopción, (c) D-9, (d) juzgadas, (e) plazo, (f) rachas. La regla de MODIS usa (a), (b), (d), (e), (f) como dice; (f) es VR-04.
- **Descarte de gránulos de la vía**: `RADIO_RECORTE_KM = 45.0` (l. 94), `sel.sum() < 100` (l. 804), `dist_max_centro_km 5.0` para MODIS (l. 112) y `None` para VIIRS 750; pre-mortem 171-01 en `D:/vrp-trabajo/temporales/ver_s171_171_01/INFORME.md` (existe, l. 40-42 lo describe); 171-03 en `D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md` l. 115-135: «75 min» y «1,1 a 1,25 veces K en Láscar (13,3 contra 10,7 y 11,9 min)», con la salvedad del propio pre-mortem: SOSPECHA que un volcán cruce los 75 min (no medido en Villarrica, Chillán ni PCC). La regla l. 138-139 lo cita sin esa salvedad.
- **Programa §12.3 punto 4 y §12.6**: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` (loop/activo) l. 409-411 («encender `ENABLE_MODIS_CODIGO_MIROVA`; los tres flags de MxD03 van aparte») y l. 455-470 (congelamiento, excepciones anotadas en la bitácora, B7). Coinciden con la regla l. 34-35 y 89.
- **Tags y ramas que la regla nombra**: `s170-modd-f4-lectura`, `s170-v375e-lector`, `s172-v375e-lector-resellado`, `pre-s171-adopcion-modd` (empujado, = merge-base `d3cd0b2ae`, como pide l. 132), `claude/s170-modd-f4-procedencia`, `claude/s172-v375e-relector` (y su worktree `D:/vrp-trabajo/worktrees/s172-relector`) existen.
- **Lista del PR (§5) contra B**: flag con guard (`tests/test_guard_modis_codigo_mirova_encendido_s172.py`, 6 pruebas), tests actualizados (s164 l. 70-77), guardia y su prueba (`test_guardia_k_modis_s172.py`), ficha SDA v1.18 (l. 7 y 25), marcas A113 en `CLAUDE.md`, `MISSION.md`, `MIROVA_DIVERGENCES.md` (en el diff), marca en las tres vistas (`cambio_detector.js:128-190`, cargado por `index.html:12`, `diario.html:10`, `mosaico.html:24`; 15 pruebas con node), auto-audit con `VIA_MODIS` (`auto_audit_weekly.py:398-481`). No verificado: el aviso a OVDAS/Integracion_Plataformas/`MAPA_WORKSPACE.md` (fuera del repo) y las bandas del auto-audit (l. 402: «NO se recalibran antes de ver datos»: decidido, como pide l. 125).
- **Batería del instrumento**: 45 de 45 (`test_vigilancia_guardia_modis_s172.py`, `test_cambio_detector_via_modis_s172.py`, `test_guard_modis_codigo_mirova_encendido_s172.py`), incluida `test_no_modifica_la_vigilancia_de_k` (que admite el cambio mínimo de B en `vigilancia_sombra.py`: separar por clave los records de la vía para que la vigilancia de K no pida revertir K).
- **Reversión simulada**: VR-05 (limpia por los dos caminos).
- **Hora de la guardia y «el mismo día»**: guardia 17:40 UTC diaria, vigilancia al terminar y respaldo 22:45 UTC; una pasada de la madrugada del día D se juzga ese mismo día a las ~18 UTC. Factible lo que promete l. 99.

### SEGUIMIENTOS (fuera de mi eje, reproducible, sin perseguir)

- S-1 (`scripts/vigilancia_guardia_modis.py:363-389`, CONFIRMADO, gravedad 2): la vigilancia etiqueta producción con el banco por «regla original; D-9 no toca MODIS» (docstring l. 365-366) mientras el prompt define protegida «con la regla SN de D-9». Para MODIS da lo mismo (VR-09), pero el texto del instrumento y el de la regla usan nombres distintos para la misma vara.
- S-2 (`frontend/cambio_detector.js:135-136`, SOSPECHA, gravedad 2): la marca del tablero exige «una pasada MODIS de K antes» del primer record de la vía; tras una reversión y un re-encendido posterior, o si el NRT re-escribe con la vía los 8 días previos, la fecha dibujada puede no ser la del encendido real. No medido.
- S-3 (`.github/workflows/guardia-k-modis.yml:101-103`, SOSPECHA heredada del pre-mortem 171-03, gravedad 2): el techo de 75 min está anclado al peor K observado (56 min) y no medido con la vía en los volcanes lentos; si el paso muere, el día entero del volcán no se commitea y la guardia queda sin ese día (la vigilancia lo ve como frescura, no como pérdida).
- S-4 (prompt `verificador_vr.txt`, CONFIRMADO, gravedad 1): sha256 real `4e6d6d87…`, no `3fdf1310…` como dijo el orquestador.

### SIN DATO

- El esfuerzo con que corrí (no expuesto por el entorno).
- Si la cabecera de la imagen de MIROVA estará disponible y será legible para una pasada futura (hoy se capturan 96 PNG de MODIS, pero no verifiqué su contenido).
- El comportamiento real de `guardia-k-modis.yml` y `vigilancia-guardia-modis.yml` en Actions (no despaché nada; la guardia aún no tiene `data/guardia_k_modis/` en main, así que el nulo de A110 está por medir).
- Origen de «28 noches» (l. 21) y «~19 UTC» (l. 87): SIN LOCALIZAR.
- Si un volcán lento cruza los 75 min con la vía (171-03 lo deja como SOSPECHA).

### FUERA DE ALCANCE

- Corregir la regla, el instrumento o las citas (sólo se reportan).
- Juzgar si adelantar MODIS fue buena decisión (A/B ya sellado, «PROPONER ADOPCIÓN»).
- La ventana P de VIIRS 375 y el lector re-sellado en sí (sólo medí que el PR B no le marca régimen).

## 5. Veredicto y lista exacta de cambios de texto

**SELLABLE CON CAMBIOS.** La regla es aplicable si, y sólo si, se hacen estos cambios de texto (los números y nombres
que propongo salen de archivos citados arriba, no de memoria):

1. (VR-01) l. 93: reemplazar «(`CAMBIO_DETECTOR_MODIS_UTC`, la hora del merge al segundo)» por «(el menor `processed_utc`
   de un record MODIS de producción con `via_codigo_mirova: true`, como lo calcula
   `scripts/vigilancia_guardia_modis.py::encendido_desde_datos`; es la primera corrida del NRT después del merge, no
   la hora del merge; las pasadas observadas entre el merge y esa corrida son retrospectivas y, si la vía las
   re-escribe, se investigan sin reversión)».
2. (VR-02) después de l. 99, agregar: «Si la guardia publica una protegida y producción no tiene record de la pasada
   (descarte de borde, 171-01), no es “calla”: pasadas 24 h desde la pasada se abre issue de investigar, sin
   reversión pre-autorizada (`ESPERA_SIN_RECORD_H`). Un VERDE con avisos (guardia o producción sin datos frescos de
   MODIS, referencia sin filas de MODIS, nulo sin pares, guardia con records de la vía, flag encendido sin records de
   la vía) no es VERDE: es `VIGILANCIA_CIEGA` y abre issue». Fijar explícitamente las 24 h (o el número que Nicolás
   decida).
3. (VR-03) l. 103-108: quitar «Propuesta, la fija Nicolás» (dos veces) y escribir las cotas decididas en la forma «más de
   N en los primeros 120 días» con su denominador: «en el A/B fueron 2 de 43 pasadas `bajo1` y 3 de 5.321 negativos
   limpios en 240 días (2026-03-01 a 2026-10-26, `poblacion_f4.json` sha256 e8315ba4…)». Si Nicolás mantiene 2 y 3,
   decir que tolera el doble por unidad de tiempo que el A/B; si quiere la misma tasa, 1 y 1 (o 2 y 2 en 240 días).
4. (VR-04) l. 110: o bien quitar «y rachas» y «(f)», o bien agregar el disparador (ii) de K («tres noches seguidas en un
   mismo volcán con una alerta de MIROVA que la guardia publica y producción no») y entonces pedir su implementación
   en el instrumento (hoy no existe).
5. (VR-05) l. 98: «`git revert` del PR de encendido» → «`git revert` del merge del PR que enciende el flag (rama
   `claude/s172-modd-flip`), mergeado por separado y después del PR de la guardia (`claude/s172-modd-encendido`), de
   modo que el revert deje la guardia, su vigilancia y la marca del tablero en pie. El revert no deshace los records
   que la vía ya escribió: el NRT re-escribe con K sólo los 8 días siguientes; lo anterior queda de la vía y se
   informa». Si se mergean juntos, decirlo y aceptar que el revert apaga también la guardia.
6. (VR-06) l. 96-99: fijar quién confirma la cabecera (la sesión que detecta) y un plazo («el mismo día; si la imagen de
   MIROVA de esa pasada no está disponible, decide Nicolás ese día»), para que l. 23 y l. 97 no se contradigan.
7. (VR-07) incluir la regla sellada en el PR del flip (o en main) y que `vigilancia-guardia-modis.yml`, los scripts y
   el perfil la citen por su ruta en main, no «rama loop/activo».
8. (VR-08) §3: dejar como regla sólo «Guardia recomendada (S172)» con lo implementado (perfil `guardia_k_modis.yaml`,
   workflow `guardia-k-modis.yml` a las 17:40 UTC, ventana de 8 días, revisión `revisar_guardia_modis.py`); marcar
   «Opción preferida» y el «Resultado de S172» como historia.
9. (VR-09) l. 96: «una alerta protegida nocturna de MODIS (lectura A, 1 MW o más)»; quitar «regla SN de D-9» o
   escribir «(D-9 no aplica a MODIS: sus mínimas son de VIIRS 375)».
10. (VR-10) l. 105: «publicación de producción en negativos limpios en pasadas que la guardia también procesó y no
    publicó».
11. (VR-11) l. 111: «hasta que la guardia tenga record de 29 protegidas A nocturnas de MODIS»; l. 113-115: cambiar «lo
    probable es que mande el plazo» por «con 16 protegidas en 60 días (audit del 2026-10-26) las 29 llegan cerca del
    día 110: puede mandar cualquiera de los dos».
12. (VR-12) l. 47 «l. 47» → «l. 49»; l. 28 «805-808» → «804-808»; l. 120-121 decir que en B esos tests ya fijan
    `True` en producción; l. 5 borrar la frase de «A COMPLETAR»; l. 99 definir N-3 en una línea; l. 21 y l. 87 citar la
    fuente de «28 noches» y «~19 UTC» o quitarlas; l. 138-139 agregar la salvedad del pre-mortem (los 75 min no están
    medidos con la vía en Villarrica, Chillán ni PCC).

Ruta absoluta de este informe: `D:/vrp-trabajo/temporales/s173_aud/vr/INFORME.md`.
