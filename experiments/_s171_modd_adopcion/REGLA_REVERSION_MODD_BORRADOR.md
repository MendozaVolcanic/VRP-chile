# Regla de adopción y reversión de la vía «código MIROVA» en MODIS (MOD-D)

**BORRADOR, RONDA 5, SIN SELLO.** Ronda 5 (S173): los cuatro cambios del verificador VB4 (fast-forward, citas de
`loop/activo`, `pipeline/` fuera del flag, comentario del script), tabla del final. D1 a D7 contestadas por Nicolás el 2026-11-02 (servidor 15:42 UTC): «de1 a d7
si», las siete con la recomendación. La ronda 3 la leyó un verificador limpio (VB3: regla SELLABLE CON CAMBIOS, PR B
MERGEABLE CON CAMBIOS); esta ronda 4 aplica esos cambios. Falta la frase de sello de Nicolás.

- **Ronda 4** (S173): aplica los cambios de texto del verificador limpio de la ronda 3 (Fable, informe VB3,
  hallazgos VB3-01 a VB3-08, §9; vive fuera de git, en `C:/Users/nmend/vrp-wt/ver_s173_regla3_b/INFORME.md`; la ronda 3
  que leyó tiene sha256 LF `18887bac...` y está en la rama `loop/activo`, commit `e617ad667`). Esta ronda ya vive en
  el PR B (#934, rama `claude/s173-modd-flip`) en esta misma ruta, y B corrige las citas de main que decían que la
  regla estaba en `loop/activo` o que era borrador (§5). Cambios: el revert de B puede chocar en cualquier hunk de B
  y B entra por merge commit (§4.3); qué hace de verdad el monitor del NRT con un job rojo (§4.4 (a)); de dónde se lee
  a mano la procedencia de la protegida para D6 (§4.3); citas que no resuelven desde main, con la rama y el commit donde
  vive cada evidencia (nota «Dónde vive la evidencia», más abajo); `sombra_34` en §2; el merge-base del tag (§5); el
  revert también saca de main esta regla (§4.7, punto 6). La tabla del final dice qué se hizo con cada VB3.
- **Ronda 3** (S173): D1 a D7 contestadas (todas «Sí»); el PR A ya está en main (#933, merge commit `eb4ae1c96`,
  2026-11-02 15:25:53 UTC) **sin** esta regla, así que la regla entra a main con el PR B (#934), no con A (§5); 208 y
  209 tratados en el PR B a pedido de Nicolás («en el resto haz lo que recomiendes», misma frase): el flag se aparta
  de las claves de MxD03 (§4.3) y el NRT revisa que MODIS haya salido (§4.4 (a)).

Ronda 2, hora del servidor al escribirla (GitHub, `gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`):
2026-11-02 13:27:30 GMT.

- **Ronda 1**: escrita el 2026-10-31 por la coordinadora S171; sha256 LF
  `77f7f37c066ab192b82de5e29f0ec96bc3db712c0799281c227fb6b67a00f6a7`, último commit que la tocó `71c96b410` (rama
  `loop/activo`). Es la misma copia que leyó el verificador (`experiments/_s173_aud/vr/INFORME.md` §1). Lo que de ella
  se degradó a historia está en el Anexo A; el resto sigue en git.
- **Ronda 2** (S173): aplica los doce cambios del verificador limpio (Fable, `experiments/_s173_aud/vr/INFORME.md` §5,
  hallazgos VR-01 a VR-12, veredicto SELLABLE CON CAMBIOS), el V1-02 de la segunda auditoría
  (`experiments/_s173_aud/v1/INFORME.md`) y los 207 y 210 (`experiments/_s173_aud/f2/INFORME.md`, confirmados en
  `experiments/_s173_aud/v2/INFORME.md`). La tabla del final dice qué se hizo con cada uno. Lo que es decisión de
  Nicolás no se decidió aquí: va como pregunta en la tabla de decisiones que sigue.
- **Cómo se sella**: Nicolás contesta D1 a D7, un verificador limpio de otro modelo lee esta ronda, y la frase de sello
  de Nicolás. El encendido pide además el tag defensivo y su sí de A45 (dos frases distintas de la del sello).
- **Código citado**: PR A = rama `claude/s172-modd-encendido` (guardia, vigilancia, marca del tablero; punta `0a0dae344`
  al escribir), PR B = rama `claude/s172-modd-flip` (el flag; punta `c9525f994`, apilada sobre A:
  `git merge-base --is-ancestor` da A ancestro de B). Hoy no hay PR abierto para ninguna de las dos
  (`gh pr list --state all`: no aparecen). (⚠️ **Ronda 4** (A113): eso era cierto en la ronda 2. Hoy el PR A es #933,
  ya en main (merge commit `eb4ae1c96`), y el PR B es #934, rama `claude/s173-modd-flip`.) En paralelo otro agente mueve al PR A los arreglos que leen records de la
  vía y agrega `VIA_MODIS` al audit semanal, así que el código se cita por **función y archivo**, no por línea; las
  líneas que quedan son de tags o de commits fijos.

Decisión que lo origina: Nicolás, 2026-10-31, ante «¿Adelantamos MODIS así?» (encender sin esperar la parada de la
sombra, con K de guardia): «hagamos todo lo recomiendas, analiza diferentes perspectivas, tenemos que probar todo y
acercanos a los objetivos» (`tasks/LOOP_OBJETIVOS.md` §6, entrada «2026-10-31 21:55 UTC (S171)»).

Modelo: el paso 9 de la regla con que se adoptó K, `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` (main), con las
decisiones (a) a (f) de Nicolás del 2026-10-19. Se cambia lo que MODIS pide y nada más; donde MODIS se aparta de K, se
dice.

**Dónde vive la evidencia (ronda 4, VB3-06).** Esta regla vive en main desde el merge del PR B, pero no toda su
evidencia. Comprobado con `git cat-file -e` el 2026-11-02:
- `experiments/_s173_aud/...` (los informes `vr`, `v1`, `f2`, `v2`, `s8_regimen_pr_b.py`,
  `desfase_upgrade_modis_salida.txt`, `contar_cotas_f4_salida.txt`): sólo en la rama `loop/activo` (presentes en el
  commit `e617ad667`); no están en main ni en B.
- `experiments/_s166_modd_f4/poblacion_f4.json`, `experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` y
  `experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json` (entró en `e0bb1b150`): rama
  `claude/s170-modd-f4-procedencia` (punta `25e3cc3ba`); el pre-registro también en `claude/s166-modd-f4`. No están en
  main. El VB3 dio `resultado_f4.json` por no localizado; está en esa ruta, con el sha256 LF que cita §4.4 (i).
- `D:/vrp-trabajo/temporales/...` (pre-mortem S171, hallazgos 171-01 y 171-03): fuera de git, en el disco local de
  Nicolás.
- `tasks/LOOP_OBJETIVOS.md` y el programa por sensor existen en main, pero lo que esta regla cita de ellos (la entrada
  de la bitácora «2026-10-31 21:55 UTC (S171)», el §12 del programa con 12.3 punto 4, 12.6 y las «28 noches») está sólo
  en la rama `loop/activo` (ronda 5, VB4-02).
- Lo demás que se cita por ruta (código, perfiles, workflows, `PREREGISTRO_E.md`, `data/audit_continuous/latest.json`
  en `489113c1f`) resuelve desde main.

## Decisiones de Nicolás antes del sello

**Contestadas el 2026-11-02: D1 a D7, «Sí» las siete** (Nicolás: «de1 a d7 si»). El texto de la regla ya estaba
escrito con esas respuestas; las frases «si D4 se contesta No» y «si D5 se contesta No» quedan sin efecto.

Cada una se contesta con una palabra. La recomendación y el número que la sostiene salen de archivos citados; los
cálculos de probabilidad son de esta ronda (Poisson con la tasa del A/B, `python -I`), no de un informe previo.

| # | Pregunta | Recomendación | Número que la sostiene | Dónde rige |
|---|---|---|---|---|
| D1 | ¿Aceptas que (i) investigue con **más de 2** alertas Muy Bajo perdidas en los 120 días? | Sí | En el A/B la vía perdió 2 de 43 pasadas `bajo1` en 240 días (2026-03-01 a 2026-10-26), o sea se esperaría 1 en 120 días. Con la cota en 2 la falsa alarma, si la vía rinde igual que en el A/B, es 8 %; con la cota en 1 sube a 26 %. Investigar no revierte nada. | §4.4 (i) |
| D2 | ¿Aceptas que (ii) investigue con **más de 3** sobre-publicaciones diferenciales en los 120 días? | Sí | En el A/B la vía publicó de más en 3 de 5.321 negativos limpios en 240 días: se esperaría 1,5 en 120 días. Cota 3: falsa alarma 7 %; cota 1: 44 %. | §4.4 (ii) |
| D3 | ¿Aceptas **24 h** de espera antes de leer como silencio una protegida sin record de producción? | Sí | El NRT corre cada 2 h y LANCE tarda unas 3 h (`CLAUDE.md` del proyecto, «Constraints técnicos»); la guardia corre a las 17:40 UTC y la vigilancia al terminar, así que 24 h deja pasar el atraso normal y aun así avisa al día siguiente. Es el valor que ya usa el instrumento (`ESPERA_SIN_RECORD_H`). | §4.4 (a) |
| D4 | ¿Aceptas **quitar** «rachas» (el disparador de persistencia de K) de la regla de MODIS? | Sí | El instrumento no lo computa (0 líneas con «racha» o «persist» en `scripts/vigilancia_guardia_modis.py`, VR-04) y `sombra_pasadas_juzgadas_modis.json` dice que el diseño no lo tiene. En el A/B hubo 2 pérdidas Muy Bajo en 240 días en los 11 volcanes: tres noches seguidas en un mismo volcán no tienen sustrato, y agregarlo pide código, pruebas y otro verificador antes del encendido. (i) ya cuenta las pérdidas acumuladas. | §4.5 |
| D5 | ¿Aceptas que A y B entren **separados** (A primero) y que la reversión revierta sólo B? | Sí | Simulado por el verificador sobre el main del 2026-11-02: revertir sólo el flag deja 0 conflictos, el flag en `False` por A89 y la guardia en pie; si entran juntos, el mismo revert apaga también la guardia, su vigilancia y la marca del tablero, y la vigilancia de K vuelve a leer records de la vía como K (VR-05, 161 de la segunda auditoría). | §4.3, §5 |
| D6 | ¿Aceptas revertir **sin la imagen** de MIROVA cuando la protegida viene de la tabla (`latest.php`) y la imagen no está disponible el mismo día? | Sí | La confirmación en la imagen protege contra errores del OCR. MODIS está completo en la tabla: al S151 sólo 5 alertas MODIS dependían del OCR, todas de Láscar (`CLAUDE.md` del proyecto, A119, marca S151). Con la regla de ronda 1, una imagen que falta deja la reversión pre-autorizada en espera indefinida (VR-06). Si la protegida es sólo del OCR y no hay imagen, decide Nicolás. | §4.3 |
| D7 | ¿Aceptas el paso del día después (§4.7): apartar los records de la vía que el NRT no re-escribe y reponerlos con K en un PR aparte, con tag defensivo? | Sí | El revert no toca `data/`: el NRT re-escribe con K sólo 8 fechas hacia atrás (`default_date_window` de `scripts/run_pipeline.py`: el día y 7 atrás), y todo lo anterior queda de la vía para siempre en una serie que el tablero, el audit y la vigilancia de K leen como K (V1-02; 161, 162, 163 y 169 de la segunda auditoría). Es lo que #883 hizo con C0 en `data/_c0_residuales/` (`docs/MISSION.md`, marca S160). | §4.7 |

## 1. Por qué, como geólogo

Hoy MODIS en producción (detector K) pierde más de un tercio de las noches en que MIROVA alerta (recall 62,5 % en
16 noches, audit del 2026-10-26, ventana 2026-08-27 a 2026-10-26, `data/audit_continuous/latest.json` en `489113c1f`) y
subestima la magnitud donde más importa: en Chillán, con el domo activo, queda en 0,56 de MIROVA (razón mediana de 8
noches en ese mismo audit, `magnitud_publicada_by_vol_sensor`) y el A/B le recupera cuatro protegidas que K callaba,
tres de ellas de octubre (`chillan.recuperadas` de `resultado_f4.json`, rama `claude/s170-modd-f4-procedencia`, ruta en
«Dónde vive la evidencia»). La vía que corre el código publicado por
MIROVA ganó el A/B pre-registrado de MOD-D (PROPONER ADOPCIÓN, verificador limpio confirmado; tag
`s170-modd-f4-lectura`). El programa preveía 28 noches de sombra antes del encendido
(`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §12.3 punto 4 y su calendario; hoy también en main),
que darían la prueba más limpia, pero cada mes de espera es un mes de alertas de MODIS perdidas. Se adopta antes y la
sombra pasa a ser guardia: si la vía calla una alerta protegida que K habría publicado, se vuelve atrás sin esperar a
nadie.

El peor caso a vigilar es el mismo que con K, visto desde el otro lado: una señal **débil o de borde de barrido** que
K publica y la vía no. La vía descarta en silencio los gránulos que no cubren el volcán: menos de 100 celdas a 45 km del
centro de la grilla, o la celda más cercana a más de 5 km (hallazgo 171-01 del pre-mortem S171,
`D:/vrp-trabajo/temporales/ver_s171_171_01/INFORME.md`, fuera de git). Los dos cortes están en `calcular_vrp_granulo` de
`pipeline/mirova_v750_codigo.py` (en main `47cdc446f`, l. 804 a 808; la ronda 4 comprobó la línea con `git show`), y el de 5 km rige para MODIS por
`FAMILIAS["MODIS"]["dist_max_centro_km"] = 5.0`; VIIRS 750 no lo tiene. Para el operador, ese descarte es silencio, igual
que «calla»: por eso tiene paso propio en §4.4 (a).

## 2. Qué se enciende

`enable_modis_codigo_mirova: true` bajo `thresholds:` de `pipeline/profiles/mirova_equivalent.yaml`, leído por
`pipeline/profile.py` como `ENABLE_MODIS_CODIGO_MIROVA = bool(_t.get("enable_modis_codigo_mirova", False))` con
`_t = _cfg["thresholds"]`. Comprobado por A89 importando `pipeline.profile`: en el árbol de esta rama (sin B) da
`False`; en B, `mirova_equivalent` da `True`, `guardia_k_modis` `False` y `sombra_codigo_mirova` `True`
(`experiments/_s173_aud/vr/INFORME.md` §4, «VERIFICADO LIMPIO», rama `loop/activo`). **Ronda 4 (VB3-06)**: la sombra
de los 34 volcanes (`sombra_34`, #932, `extends: mirova_equivalent`) también hereda `True`, y `experimental` da
`False` (A89 corrido en la punta de B el 2026-11-02, y por el VB3). Los tres flags de MxD03 quedan como están (se deciden
aparte, programa §12.3 punto 4) y siguen en `False`; VIIRS 375 y VIIRS 750 de producción no cambian (sus vías siguen en
`False`, mismo informe).

## 3. La guardia: K de MODIS corriendo aparte

Rige la guardia implementada en el PR A. Las opciones que la ronda 1 discutió (la sombra con MODIS en K, el resultado
de la lectura estática del lector de V375-E, el orden de re-sellado) quedan como historia en el Anexo A y **no se
aplican**: editar la sombra rompe la aserción de su workflow, que el S8 del lector de V375-E compara como texto (VR-08).

- **Perfil**: `pipeline/profiles/guardia_k_modis.yaml`: `extends: mirova_equivalent`,
  `thresholds.enable_modis_codigo_mirova: false`, sólo MODIS, `data_subdir: guardia_k_modis` (A47: no comparte carpeta
  con producción). La sombra (`sombra_codigo_mirova.yaml`) no se toca y sigue corriendo las tres vías; tras el
  encendido su MODIS es igual a producción.
- **Workflow**: `.github/workflows/guardia-k-modis.yml`, una vez al día a las 17:40 UTC, sobre las mismas 8 fechas que
  el NRT (el día y 7 atrás), con un techo de 75 min en el paso de cálculo; antes de correr asserta por
  `pipeline.profile` que es K pura, sólo MODIS y con MxD03 apagado. Revisión propia: `scripts/revisar_guardia_modis.py`
  (falla el job si la corrida no escribió MODIS, si algún record trae la clave de la vía, si falta un día de la ventana
  o si el log trae `ERROR processing`: una guardia muerta o que corriera la vía daría VERDE para siempre).
- **Vigilancia**: `scripts/vigilancia_guardia_modis.py`, corrida por `.github/workflows/vigilancia-guardia-modis.yml`
  al terminar la guardia, con respaldo diario a las 22:45 UTC. Escribe `data/audit_continuous/guardia_modis_latest.json`
  y abre issues; **no revierte**.
- **Régimen de V375-E**: ni el perfil de la guardia (fuera de `PERFILES_REGIMEN`) ni su workflow (fuera de
  `RUTAS_REGIMEN`) cuentan para el S8 del lector re-sellado de VIIRS 375 (tag `s172-v375e-lector-resellado`), y el PR
  B tampoco marca régimen nuevo: medido con las funciones del propio lector, con controles positivo y negativo
  (`experiments/_s173_aud/vr/s8_regimen_pr_b.py` y su salida; X3 de `experiments/_s173_aud/v2/INFORME.md`; los dos en la
rama `loop/activo`).

La excepción al congelamiento de `pipeline/` (programa §12.6) se anota en la bitácora con el commit y el sensor (MODIS).

## 4. Reversión e investigación

### 4.1 Desde cuándo cuenta

- **Encendido** = el menor `processed_utc` de un record MODIS de producción con `via_codigo_mirova: true`, como lo
  calcula `encendido_desde_datos` de `scripts/vigilancia_guardia_modis.py` y lo publica
  `guardia_modis_latest.json` en el campo `encendido_modis_utc`. Es la primera corrida del NRT que escribió con la vía,
  no la hora del merge. No existe ninguna constante `CAMBIO_DETECTOR_MODIS_UTC` (la ronda 1 la nombraba; `git grep` en
  B da 0, VR-01) y nadie tiene que llenar nada.
- **Franja del encendido.** El NRT re-escribe en cada corrida las 8 fechas que van del día a 7 atrás
  (`default_date_window` de `scripts/run_pipeline.py`), y tras el merge esa re-escritura sale de la vía. Así, la
  primera **observación** con record de la vía (`primera_observacion_via` en el mismo JSON) cae hasta unos 8 días antes
  del merge; en los records MODIS de octubre de 2026 re-escritos, el desfase observación a última escritura llegó a
  9,42 días (`experiments/_s173_aud/f2/desfase_upgrade_modis_salida.txt`, rama `loop/activo`; el noveno día queda SIN DATO de origen, V2
  sobre 207). La marca del tablero (`primeraViaModis` de `frontend/cambio_detector.js`) y la frontera del audit
  (`frontera_via_modis` de `scripts/auto_audit_weekly.py`) usan esa fecha de observación, no el encendido (207). Las
  pasadas observadas entre la primera observación de la vía y el encendido son **retrospectivas**: no disparan la
  reversión (decisión (b) de K); una protegida de esa franja que la guardia publica y producción, ya con record de la
  vía, calla, se **investiga** (`borde_del_encendido`, §4.4 (b)).
- **Plazo**: los 120 días de §4.6 cuentan desde el encendido así definido. La hora del merge se anota en la bitácora
  y no decide nada.

### 4.2 Unidad: la pasada nocturna

La unidad es la pasada (decisión (a) de K), y sólo **nocturna**: MODIS diurno no se procesa en ningún perfil
(`ENABLE_DAYTIME_MODIS = False` en producción y en la guardia, A89), así que una alerta diurna de MIROVA nunca tiene
record de ningún lado y no entra a la regla (VR-09).

**Protegida** = alerta de MIROVA en MODIS de 1 MW o más (lectura A, D-4). D-9 no aplica a MODIS: sus mínimas son de
VIIRS 375; para MODIS el único corte es 1 MW. N-3 tampoco aplica: es la regla de las adendas de V375-E que deja fuera
del veto las protegidas sólo del OCR de Suomi NPP anteriores al 2026-10-09 (`experiments/_s162_v375/PREREGISTRO_E.md`
§8.13, tag `s166-v375e-adenda2-sellada`), y MODIS no tiene canal de Suomi NPP.

### 4.3 Reversión inmediata, pre-autorizada

- **Disparador**: una pasada nocturna posterior al encendido, dentro del plazo de §4.6, con una protegida que MIROVA
  publica, la guardia K publica y producción (la vía) **tiene record y no publica** («calla»). La vigilancia la informa
  como `REVERSION_CANDIDATA` y abre el issue «Guardia K de MODIS: candidata a reversion».
- **Quién**: la sesión que lee el issue. **Cuándo**: el mismo día UTC del issue.
- **Confirmación**: la sesión mira la cabecera de la imagen de MIROVA de esa pasada (la captura `mirova-tif-archive`;
  el 2026-11-02 seguía capturando, VR-06). Si la imagen muestra la alerta, revierte. Si la imagen no está disponible
  ese día: **según D6**, revierte igual cuando la protegida viene de la tabla (`latest.php`), y avisa y deja la decisión
  a Nicolás ese mismo día cuando es sólo del OCR. Si la imagen contradice la alerta (la imagen no muestra alerta de 1
  MW o más en esa pasada), no revierte, anota la pasada como juzgada (§4.5) y avisa.
- **De dónde sale la procedencia para D6 (ronda 4, VB3-04).** La vigilancia no publica si la protegida viene de la
  tabla o del OCR (`guardia_modis_latest.json` trae volcán, sensor, minuto y VRP, sin la fuente). Mientras no la
  publique, la sesión la mira a mano: busca la pasada (volcán, MODIS, minuto de `Fecha_Satelite_UTC`) en
  `monitoreo_satelital/registro_vrp_consolidado.csv` del repo `MendozaVolcanic/Mirova-v1` (la tabla, `latest.php`). Si
  está ahí con 1 MW o más, viene de la tabla; si sólo está en `registro_vrp_ocr.csv`, es sólo del OCR. Ojo con las
  variantes de nombre del scraper (A14). La copia de `data/mirova_reference/mirova_v1_snapshot/` puede ir hasta una
  hora atrasada.
- **Cómo**: `git revert -m 1` del commit de merge del PR B (el que enciende el flag), nunca un reset. **Según D5**, B
  entra después de A y por separado, así que el revert deja en pie la guardia, su vigilancia y la marca del tablero. Si
  D5 se contesta «No» y entran juntos, el revert apaga también la guardia y su vigilancia: hay que decirlo en el issue.
  Comprobación después del revert: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p;
  print(p.ENABLE_MODIS_CODIGO_MIROVA)"` debe dar `False` (A89).
- **Sólo con commit de merge (ronda 5, VB4-01).** B se mergea con el botón de merge commit de GitHub
  (`gh pr merge 934 --merge --match-head-commit <sha>`) o `git merge --no-ff`; **nunca fast-forward ni «Rebase and
  merge»**: B está hoy adelante de main sin divergencia, así que un merge sin `--no-ff` no deja commit que revertir, y
  el VB4 midió que entonces `git revert -m 1` de la punta deja el flag en `True` y `git revert main..B` falla en el merge
  interno. Si aun así entró por fast-forward o rebase, se revierte el rango de commits de B (`git revert -m 1` sobre
  cada merge interno y `git revert` simple sobre el resto) o se escribe a mano un commit que deje
  `enable_modis_codigo_mirova: false`, y la comprobación A89 decide.
- **B entra por merge commit (ronda 4, VB3-08).** El repo mezcla squash (#932) y merge commit (#933); el `-m 1` de
  arriba supone que B entra con merge commit, y así se mergea. Si B hubiera entrado por squash, se revierte el commit
  del squash con `git revert <sha>`, sin `-m` (el git 2.53 de hoy ignora el `-m` en un commit que no es merge; uno
  anterior falla con «mainline was specified but commit is not a merge»). En los dos casos la comprobación A89 es la
  misma.
- **Si el revert choca**: hoy es limpio (simulado el 2026-11-02 sobre `47cdc446f` por dos caminos, 0 conflictos,
  VR-05). Choca si otro PR toca las líneas vecinas del flag en `mirova_equivalent.yaml` (las tres claves de MxD03 están
  justo antes; V2 sobre 208 lo provocó y vio el conflicto). **Ronda 3**: el PR B pone el flag en un bloque propio,
  separado de las claves de MxD03 por líneas que B no toca, y deja una prueba con `git merge-file` que comprueba que un
  cambio en esas claves no choca con el revert de B; la frase que sigue queda como respaldo. En ese caso se resuelve a mano dejando
  `enable_modis_codigo_mirova` en `false` (o sin la clave) y conservando el otro cambio; no se espera a nadie.
  **Ronda 4 (VB3-02)**: lo anterior cubre sólo las claves de MxD03, que es lo que mide la prueba de B
  (`tests/test_revert_flag_modis_no_choca_s173.py`). El revert puede chocar en **cualquier hunk de B**, no sólo en el
  YAML. Medido por el VB3 sobre el main del 2026-11-02 con `git revert -m 1` real: choca si otro PR agrega una clave
  pegada a `thresholds:` o pegada al flag en `mirova_equivalent.yaml`, y si otro PR toca el final de
  `.github/workflows/nrt.yml` (el paso «Revisar errores de MODIS en el log» es el último del job). Por la misma
  mecánica, no simulado, puede chocar en las marcas A113 que B agrega al inicio de `docs/MISSION.md`,
  `docs/MIROVA_DIVERGENCES.md` y `CLAUDE.md` (donde cada sesión agrega marcas), en la ficha, en esta regla y en las
  citas que B corrigió. Cómo se resuelve, en todos: a mano, sin esperar a nadie; el flag queda en `false` (o sin la
  clave), lo que agregó B sale y lo ajeno se conserva (en los documentos, las marcas de otras sesiones quedan y salen
  sólo las de B). Después, la comprobación A89 de arriba.
- **Después**: issue de la reversión, aviso a Nicolás el mismo día, la pasada en `sombra_pasadas_juzgadas_modis.json`, y
  el paso del día después (§4.7).

### 4.4 Investigación, sin reversión automática

Cada una abre el issue «Guardia K de MODIS: investigar». Investigar es mirar y decidir, no revertir.

- **(a) Protegida sin record de producción.** La guardia publica una protegida posterior al encendido y producción
  **no tiene record** de esa pasada (el descarte de borde 171-01 o una excepción de la vía). No es «calla»: pasadas
  **24 h (D3)** desde la pasada (`ESPERA_SIN_RECORD_H`), se investiga. Es el peor caso que declara §1; si la
  investigación muestra que la vía descartó un gránulo con el volcán bien cubierto, eso se lleva a Nicolás el mismo día.
  **Ronda 3 (209, V2-02)**: una excepción de la vía en un gránulo no cae a K y `run_pipeline` sigue con el siguiente,
  así que el job del NRT sale verde. El PR B agrega a `nrt.yml` un paso como el «Revisar que salio K de MODIS» de la
  guardia: si el log de la corrida trae `ERROR processing` en un gránulo MODIS, el job falla (rojo), y eso lo ve el
  monitor del NRT el mismo día, sin esperar los 3 días de frescura de la vigilancia. No revierte nada: se investiga.
  ⚠️ **Ronda 4 (VB3-03)**: «lo ve el monitor del NRT el mismo día» promete de más. Lo seguro es el **job rojo** en la
  página de la corrida, con el `::error` del paso, que nombra el volcán. El monitor (`.github/workflows/nrt-monitor.yml`,
  cada 6 h, `scripts/nrt_monitor_decision.js`) abre issue sólo si las **3 corridas seguidas** más recientes fallaron, y
  ese issue («NRT cron: 3+ corridas consecutivas fallaron») habla de NASA y del token: no distingue esta causa. Un error
  que aparece en una sola corrida nunca llega al monitor. Además, un gránulo malo se vuelve a procesar en cada corrida
  mientras su fecha esté en la ventana de 8 días (`default_date_window` de `scripts/run_pipeline.py`), así que un solo
  gránulo puede dejar el NRT rojo hasta 8 días, en las 12 corridas de cada día. Por eso la sesión que vea el NRT rojo,
  o ese issue, mira primero el paso **«Revisar errores de MODIS en el log»** del job, antes de buscar una caída de NASA
  o el token vencido; si el paso nombra un gránulo MODIS, se investiga como este punto (a).
- **(b) Borde del encendido.** Protegida de la franja de §4.1 que la guardia publica y producción, con record de la
  vía, calla (`borde_del_encendido`).
- **(c) Nulo de la guardia.** Antes del encendido, guardia y producción son el mismo detector K y tienen que publicar
  lo mismo en cada pasada pareada (14 días antes del encendido, o de hoy mientras no haya encendido). Una diferencia se
  investiga (A110).
- **(i) Muy Bajo.** Alertas de MIROVA sobre 0,05 MW y bajo 1 MW que la guardia publica y producción calla, contadas en
  los 120 días, sólo en pasadas con record en los dos lados. Investiga con **más de 2 (D1)**. Se informa siempre con su
  denominador: cuántas pasadas Muy Bajo tuvieron record en los dos lados (`muy_bajo.n`). Referencia: en el A/B, 2 de 43
  pasadas `bajo1` en 240 días (`experiments/_s166_modd_f4/poblacion_f4.json`, sha256 LF `e8315ba4ff93...3be8`, y
  `brazos.V.p2.discordantes` de `experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json`, sha256
  `312e2050c680...4129d`; los dos en la rama `claude/s170-modd-f4-procedencia`, no en main; la ronda 4 recalculó los dos
  prefijos de sha256 en LF).
- **(ii) Sobre-publicación diferencial.** Pasadas de negativo limpio en que producción publica y la guardia, **que
  procesó la misma pasada**, no publica; sin record de la guardia la pasada no cuenta. No es la publicación absoluta de
  producción en negativos limpios: K sola publicó en 12 de 1.194 (1,0 %) en el audit del 2026-10-26, y con la vara
  absoluta el issue se abriría sin que la vía cambiara nada (VR-10). Investiga con **más de 3 (D2)** en los 120 días,
  con su denominador (`sobrepublicacion.n`). Referencia: en el A/B, 3 de 5.321 negativos limpios en 240 días, mismos
  archivos.
- **(iii) Borde 171-01, por semana.** Pasadas que la guardia registra y producción no, contadas por semana ISO. Se
  informa y no dispara: la regla no tiene vara para ese número y A115 prohíbe inventarla.
- **Vigilancia ciega.** Un VERDE con avisos **no es VERDE**: la vigilancia lo marca `VIGILANCIA_CIEGA` y abre issue.
  Los avisos son: guardia o producción sin datos frescos de MODIS en algún volcán (más de 3 días), referencia de MIROVA
  detenida o sin filas de MODIS, nulo sin pares (0 pares es «no medí», no «coinciden»), guardia con records de la vía,
  perfiles cruzados, y flag de producción encendido sin records de la vía o con la vía detenida más de 3 días
  (`avisos_produccion`, `avisos_referencia_modis`, `avisos_guardia`, `avisos_via` y el aviso del nulo, en
  `scripts/vigilancia_guardia_modis.py`). Una vigilancia ciega se resuelve antes de leer la falta de disparos como
  ausencia de pérdidas.

Nota de lectura para quien recuente las cotas: en el A/B, c = +1 es error sólo de la vía y c = -1 error sólo de K
(`experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md`, fila P2; rama `claude/s170-modd-f4-procedencia`, no en main). La
salida de `experiments/_s173_aud/vr/contar_cotas_f4_salida.txt` (rama `loop/activo`) rotula al revés («c=+1 (a favor de la vía)»), pero sus conteos
son los de arriba: `bajo1` 2 con c = +1 y 10 con c = -1; `neg_limpio` 3 con c = +1 y 39 con c = -1; neto -44, B 53.

### 4.5 Pasadas juzgadas

Como (d) de K: una pasada ya decidida por una persona se anota en
`experiments/_s171_modd_adopcion/sombra_pasadas_juzgadas_modis.json` (un commit por entrada, con quién, cuándo y la
evidencia) y no vuelve a disparar. **Según D4**, la regla de MODIS **no tiene rachas**: K investiga tres noches
seguidas con una alerta que la sombra publica y producción no, y su (f) existe para esa racha; MODIS no copió ese
disparador, así que tampoco su (f) (VR-04). Si D4 se contesta «No», hay que escribir el disparador, implementarlo en el
instrumento y probarlo antes del encendido.

### 4.6 Duración

Hasta que la guardia **tenga record** de 29 protegidas nocturnas de MODIS posteriores al encendido, o 120 días desde el
encendido, lo que ocurra primero (misma potencia que K: con 29, una pérdida de una de cada diez se ve con 95 %,
1 - 0,9^29 = 0,953). «Tener record» es lo que cuenta el instrumento; no hace falta que la guardia la publique (VR-11).
Una candidata está dentro del plazo si es una de las primeras 29 protegidas con record en la guardia (la 29.ª incluida) y
anterior al vencimiento. Cumplido el plazo, una candidata se sigue informando (`CANDIDATA_FUERA_DE_PLAZO`) pero ya no
está pre-autorizada: decide Nicolás (decisión (e) de K). Ritmo esperado: el audit del 2026-10-26 tiene 16 protegidas de
MODIS en 11 noches en 60 días; a ese ritmo las 29 llegan cerca del día 109, así que puede mandar cualquiera de los dos
límites. Se informa cuántas hubo.

### 4.7 El día después de una reversión

El revert apaga el flag pero no deshace los datos (V1-02, 207). Tras él:

1. **Datos (según D7).** El NRT re-escribe con K las 8 fechas de su ventana; lo observado antes queda con
   `via_codigo_mirova: true` en `data/mirova_equivalent/`. Dentro de los 7 días siguientes, en un PR aparte y con tag
   defensivo antes (A38): esos records se apartan a `data/_via_modis_residuales/` y se reponen con K para las mismas
   pasadas, con un reproceso en Actions (MODIS no corre en Windows, pyhdf) o con los records de la guardia de esas
   pasadas si el nulo de §4.4 (c) dio 0 diferencias; cuál de los dos lo decide ese PR con su prueba. Hasta entonces,
   la serie MODIS mezcla dos detectores y así se dice en el issue de la reversión.
2. **Lectores de la vía.** Mientras queden records de la vía, el tablero sigue dibujando la marca naranja de MODIS sin
   marca de fin (`primeraViaModis`, VR-05), el audit separa `VIA_MODIS` por su frontera (`frontera_via_modis`) y la
   vigilancia de K separa los records de la vía (`claves_via` y el filtro de `cargar_insumos` de
   `scripts/vigilancia_sombra.py`, 161) y deja de exigir frescura de K en MODIS en cuanto existe uno (V1-03). Por eso esos arreglos van en el PR A (D5) y no se revierten con B. Apartados
   los records, la marca y la frontera desaparecen solas porque salen de los datos.
3. **Guardia.** La guardia y su vigilancia siguen corriendo hasta que Nicolás decida apagarlas: después del revert
   comparan K con K, y cubren la frescura de MODIS que la vigilancia de K deja de mirar (V1-03).
4. **Ficha.** El revert devuelve `docs/FICHA_SDA_VRP_CHILE.md` a la v1.17, que dice que la vía nunca se encendió (163).
   En el mismo PR del revert, o el mismo día, se escribe la v1.19: se encendió el día X, se revirtió el día Y por la
   pasada Z, y los records de la vía quedan apartados (o todavía mezclados) desde tal fecha.
5. **Marcas A113** en `docs/MISSION.md`, `CLAUDE.md` y `docs/MIROVA_DIVERGENCES.md`: las del PR B se van con el revert;
   se agrega una marca que diga que MODIS volvió a K y desde cuándo.
6. **Esta regla (ronda 4).** Como entra a main con el PR B, el revert de B la borra de main y devuelve a «rama
   loop/activo» o «borrador» las citas que B corrigió; la guardia, su vigilancia y sus issues la siguen citando por esta
   ruta. En el mismo PR del revert, o el mismo día, se repone con
   `git checkout <commit de merge de B> -- experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (si B
   entró por squash, el sha del squash; si entró por fast-forward o rebase, la punta de B, §4.3) y se le agrega una
   marca con la fecha de la reversión. Simulado por el VB4: tras el revert la reposición no re-enciende el flag.

## 5. Lista de los PR de encendido (sobre el modelo del paso 8 de K)

Según D5: **PR A** primero (guardia, vigilancia, lectores de la vía, regla) y **PR B** después (el flag).

- ⚠️ **Ronda 4 (VB3-01)**: la regla **ya está en el PR B** (#934, rama `claude/s173-modd-flip`) en esta misma ruta,
  con esta ronda; la frase de sello y el encabezado de sellada se le agregan en B antes del merge. En el mismo PR, B
  corrige las citas de main que decían «rama loop/activo» o «borrador» (workflows de la guardia y de su vigilancia,
  `scripts/revisar_guardia_modis.py`, `scripts/vigilancia_guardia_modis.py` con el texto del JSON publicado, las
  pruebas, el diseño y el informe del implementador; el texto viejo, cierto en su fecha, queda con marca A113 donde
  era documento). El perfil `pipeline/profiles/guardia_k_modis.yaml` conserva su comentario «rama loop/activo»: B no
  toca ese perfil (fuera del flag, B sólo cambia dos comentarios de `pipeline/process_modis.py`, sin efecto en el
  código ni en el S8 del lector de V375-E; VB4-03). B entra por merge commit (§4.3).
- ⚠️ **Ronda 3**: el PR A entró a main (#933) sin la regla, así que **entra con el PR B**, en la misma ruta y con el
  encabezado de sellada; el issue de `vigilancia-guardia-modis.yml` la cita y hoy apunta a una ruta que no existe en
  main (210). Los lectores de la vía y el 205 sí entraron con A (comprobado en `eb4ae1c96`). La ficha v1.18 de B se
  corrige ahí mismo («No se reprocesan datos anteriores» y «rige desde el merge» no son exactos, §4.1). Texto de ronda 2:
- **La regla sellada entra a main en el PR A**, en esta misma ruta, con el encabezado de sellada (VR-07, 210): hoy vive
  sólo en `loop/activo` y la citan el perfil de la guardia, los dos workflows, el cuerpo de los issues,
  `scripts/vigilancia_guardia_modis.py`, `scripts/revisar_guardia_modis.py` y `sombra_pasadas_juzgadas_modis.json`.
  Mantener la ruta evita tocar esas citas; las que dicen «rama loop/activo» o «borrador» se corrigen en el mismo PR.
- **Lectores de records de la vía en el PR A** (en curso en paralelo): `claves_via` y el filtro de `cargar_insumos` en
  `scripts/vigilancia_sombra.py` (161), que el audit semanal de `scripts/auto_audit_weekly.py` reconozca
  `VIA_MODIS` (205: si no, cae con ValueError la primera vez que la vía publique MODIS en una noche con alerta), para que revertir B no los
  deshaga. Antes del merge de B se comprueba que estén en A.
- **El flag**, con su guard (`tests/test_guard_modis_codigo_mirova_encendido_s172.py` en B).
- **Los tests que fijaban el flag apagado**, ya actualizados en B: `tests/test_mirova_modis_codigo_s164.py` fija hoy
  `True` en `mirova_equivalent` y `False` en `experimental` y `guardia_k_modis`;
  `tests/test_guard_declarado_vs_efectivo_s131.py` cita el import sólo en un comentario;
  `tests/test_guard_perfiles_congelados_s153.py` cubre los derivados por `extends`.
- **La guardia** (§3) y sus pruebas (`tests/test_guardia_k_modis_s172.py`, `tests/test_vigilancia_guardia_modis_s172.py`).
- **El auto-audit**: las bandas de MODIS no se recalibran antes de ver datos (decidido en el código de B).
- **La ficha** `docs/FICHA_SDA_VRP_CHILE.md` v1.18 (en B) y las marcas A113 donde MODIS aparece como K (`docs/MISSION.md`,
  `CLAUDE.md`, `docs/MIROVA_DIVERGENCES.md`). La v1.18 de B dice «No se reprocesan datos anteriores» y «rige desde el
  merge»; con la re-escritura de 8 días del NRT (§4.1, 207) eso no es exacto: los últimos 8 días antes del merge quedan
  con la vía. Corregir esa frase antes del merge de B. (⚠️ **Ronda 4**: corregida en B, commit `8c89552cf`; la ronda
  4 agrega a la v1.18 el caso de la excepción de la vía, VB3-07.)
- **Una marca visible de la fecha del cambio** en las tres vistas (`index.html`, `diario.html`, `mosaico.html`), ya en B
  (`frontend/cambio_detector.js`): con la vía la magnitud de MODIS sube y aparecen alertas que K callaba; en Chillán ese
  escalón no debe leerse como «la erupción crece». La marca cae en la primera observación de la vía, hasta unos 8 días
  antes del merge (§4.1).
- **El aviso a los consumidores** (OVDAS, Integracion_Plataformas, `MAPA_WORKSPACE.md`).
- **Tag defensivo** `pre-s171-adopcion-modd` (existe y está empujado, `d3cd0b2ae`, merge-base de B con main; si al
  merge de B main ya avanzó, se agrega un tag nuevo sobre el commit de main previo al merge, sin mover el viejo) y el sí de Nicolás antes del merge (A45), que incluye la
  pre-autorización de la reversión de §4.3. ⚠️ **Ronda 4 (VB3-06)**: `d3cd0b2ae` era el merge-base cuando se creó el
  tag. B ya mergeó main dos veces (`126844bdc`, y el 2026-11-02 tras #935): hoy el merge-base de B con main es
  `438a010ab`. Main avanzó, así que el tag nuevo sobre el commit de main previo al merge de B **sí hace falta**.

## 6. Pre-mortem

Si la adopción está mal, se vería como: (a) una protegida que la guardia publica y producción calla (dispara §4.3); (b)
una protegida que la guardia publica y de la que producción no tiene record (§4.4 (a)); (c) la sobre-publicación
diferencial de MODIS subiendo sobre lo medido (§4.4 (ii)); (d) pasadas de borde que producción deja de registrar
(§4.4 (iii), 171-01); (e) el paso de la guardia pasando su tiempo: la vía cuesta 1,1 a 1,25 veces K en Láscar (13,3
contra 10,7 y 11,9 min, pre-mortem 171-03, `D:/vrp-trabajo/temporales/audit_s171_dia3/INFORME.md`, fuera de git), pero eso **no está
medido con la vía en los volcanes lentos** (Villarrica, Chillán, PCC): que alguno cruce los 75 min del paso es
SOSPECHA del propio pre-mortem, y si pasa, ese día del volcán no se commitea y la vigilancia lo ve como frescura, no
como pérdida; (f) una excepción de la vía que no es la falta de pyproj deja a MODIS sin record con el NRT en verde
(209 de la segunda auditoría), y lo ve la vigilancia de la guardia al cuarto día por volcán, antes si hay una protegida
(§4.4 (a)). (⚠️ **Ronda 4** (A113): con el paso que agrega B a `nrt.yml`, esa excepción deja el job del NRT en rojo,
posiblemente hasta 8 días por un solo gránulo; qué ve el monitor y qué mira la sesión, en §4.4 (a).)

## Anexo A: historia de la ronda 1 (no rige)

Se conserva por A113. Lo que sigue es el texto de §3 de la ronda 1 que esta ronda dejó de aplicar (VR-08), copiado tal
cual salvo una marca: las citas de línea del lector de VIIRS 375 están corridas («l. 47» es la l. 49 en los tags
`s170-v375e-lector` y `s172-v375e-lector-resellado`) y el tag que manda comprobar ya no es el vigente (el vigente es
`s172-v375e-lector-resellado`) (VR-12 (a), 210). El «~19 UTC» del último párrafo no tiene fuente localizada (VR-12 (g));
la fecha 2026-11-03 sí (`experiments/_s162_v375/PREREGISTRO_E.md` l. 50, rama `loop/activo`).

> **Opción preferida (a verificar):** que la sombra existente (`pipeline/profiles/sombra_codigo_mirova.yaml`) pase a
> correr MODIS con K (vía de MODIS apagada en ese perfil) desde el mismo commit del encendido. Así la sombra de MODIS
> queda como K y producción como la vía, con el mismo workflow, la misma ventana y los mismos gránulos. Por qué no
> contamina VIIRS: los lectores de sombra comparan sólo lo que lee su vía (regla B7 del verificador del lector de
> VIIRS 375, programa §12.6); **comprobar en el lector sellado `s170-v375e-lector` que un cambio en las claves de MODIS
> no marca régimen nuevo en VIIRS 375** antes de elegir esta opción.
>
> ⚠️ **S172, corrección del punto (1) que sigue** (misma sesión, al preparar el re-sellado): el S0 **no cae** con el PR
> de MODIS. El lector calcula los sha256 sobre su propio checkout (`RAIZ = AQUI.parents[2]`, l. 47; el docstring dice «Se
> corre desde un checkout del tag del lector»), no sobre `main`, y los 16 archivos del sello coinciden en el checkout del
> tag (comprobado el 2026-11-01). Lo único que el encendido toca es el S8, y lo toca por dos lados: el perfil
> (`viejo != nuevo` sobre el texto entero) y, si la guardia edita la sombra, la aserción del workflow
> `.github/workflows/sombra-codigo-mirova.yml` l. 110 (`assert ... p.ENABLE_MODIS_CODIGO_MIROVA`), que está en
> `RUTAS_REGIMEN` y se compara como texto. El re-sellado por claves cubre el perfil; el workflow no: por eso la guardia
> va mejor en un perfil y un workflow nuevos (ver «Guardia recomendada» al final de esta sección). Texto original:
>
> **Resultado de S172 (lectura estática del lector en el tag, no corrido): SÍ lo marca, y la opción preferida no es
> gratis.** (1) Control S0: el lector exige el sha256 de `pipeline/profile.py`, `pipeline/store.py`,
> `pipeline/profiles/mirova_equivalent.yaml` y `frontend/index.html` iguales a los del sello (`SHA_SELLO_LECTOR`, l. 63 a
> 77); el PR de encendido cambia el YAML de producción y la marca de `index.html` (§5), así que S0 cae y el lector no
> lee. (2) Control S8: cualquier cambio de código bajo `pipeline/` (por AST) o de los dos perfiles
> (`PERFILES_REGIMEN`, `viejo != nuevo`) cuenta como régimen nuevo, y un CUMPLE de (b), (c) o (d) pasa a DECIDE NICOLAS.
> (3) La sombra ya corre las tres vías en un solo perfil (`enable_modis_codigo_mirova: true`, `sombra_codigo_mirova.yaml`),
> así que dejar a MODIS en K ahí también edita ese perfil. Consecuencia: el encendido de MODIS exige re-sellar el lector
> de V375-E (nueva lista de sha256 y base de régimen) con su verificador limpio, o aceptar que la ventana P de VIIRS 375
> quede en DECIDE NICOLAS por régimen. **Decisión de Nicolás, 2026-11-01 (S172): re-sellar el lector de V375-E.** Orden, porque los sha256 dependen del PR
> final: (1) el PR de encendido de MODIS queda con su contenido definitivo (YAML, `profile.py` si cambia, marca de
> `index.html`, perfil de la sombra); (2) con ese commit se calcula la lista nueva de `SHA_SELLO_LECTOR` y la base de
> régimen S8, sin abrir datos de la ventana P; (3) verificador limpio de otro modelo sobre el lector re-sellado
> (batería y nulo como en `s170-v375e-lector`); (4) tag nuevo y frase de sello de Nicolás; (5) recién ahí el merge de
> MODIS (A45). La ventana P de VIIRS 375 empieza el 2026-11-03: si el re-sellado no llega antes, esa noche queda
> informada con el lector actual y el encendido de MODIS espera. Alternativa: un perfil de guardia nuevo, aislado
> (`data_subdir` propio, A47), sumado al workflow de la sombra; cuesta tiempo de runner (pre-mortem 171-03: el paso
> tiene 75 min).
>
> **Re-sellado por claves (decisión de Nicolás, 2026-11-01, «Sí, por claves»).** En el S8 los dos perfiles se comparan
> como YAML leído y sin las claves de `thresholds` que lee sólo otro sensor (`enable_modis_codigo_mirova`,
> `enable_v750_codigo_mirova` y los tres de MxD03; consumidores comprobados con `git grep` en `origin/main`: sólo
> `pipeline/process_modis.py` y `pipeline/process_viirs_mod.py`), igual que ya se hacía con `roi_v750` en la grilla.
> Con eso el orden de arriba cambia: los sha256 del S0 no dependen del PR de MODIS, así que el re-sellado **no espera** al
> contenido final del PR y el encendido puede llegar cualquier día de la ventana P sin marcar régimen en VIIRS 375.
> Rama `claude/s172-v375e-relector`, worktree `D:/vrp-trabajo/worktrees/s172-relector`.
>
> **Guardia recomendada (S172):** un perfil nuevo `guardia_k_modis.yaml` (`extends: mirova_equivalent`,
> `enable_modis_codigo_mirova: false`, sólo MODIS, `data_subdir` propio) corrido por un workflow nuevo. Ni el perfil (no
> está en `PERFILES_REGIMEN`) ni el workflow (no está en `RUTAS_REGIMEN`) cuentan para el S8 del lector de VIIRS 375, y no
> hay que tocar la aserción del workflow de la sombra. La sombra sigue con la vía de MODIS, que tras el encendido es
> igual a producción. Editar la sombra sólo serviría si ese cambio del workflow se mergea **antes** del primer record de
> la vía de la ventana P (la base del S8), o sea antes del 2026-11-03 ~19 UTC.

Nota sobre el «consumidores comprobados ... sólo `process_modis.py` y `process_viirs_mod.py`» de arriba (VR-12 (d)): vale
para las claves del perfil dentro de `pipeline/`. El flag lo leen además la guardia, la aserción de la sombra, la
vigilancia de la guardia y varias pruebas.

## Hallazgo, tratamiento

| Hallazgo | Qué decía | Tratamiento (ronda 2; las filas VB3, ronda 4) |
|---|---|---|
| VR-01 | La regla anclaba el conteo en `CAMBIO_DETECTOR_MODIS_UTC`, que no existe; el instrumento usa los datos | Aplicado: §4.1 define el encendido con `encendido_desde_datos` (menor `processed_utc` de un record de la vía) y dice qué pasa en la franja entre el merge y esa corrida |
| VR-02 | Sólo pre-autorizaba «calla»; nada sobre la protegida sin record de producción ni sobre la vigilancia ciega | Aplicado: §4.4 (a) y «Vigilancia ciega»; las 24 h convertidas en pregunta (D3) |
| VR-03 | Cotas (i) y (ii) como «propuesta» con denominador SIN DATO | Denominador aplicado (2 de 43 y 3 de 5.321 en 240 días, §4.4); las cotas convertidas en pregunta (D1, D2) con su falsa alarma calculada; se informan siempre con su denominador |
| VR-04 | «rachas ... (f) de K» sin disparador de persistencia | Convertido en pregunta (D4, recomendación: quitar); §4.5 escrito con D4 en «Sí» |
| VR-05 | «git revert del PR de encendido» sin decir cuál; el revert no deshace los records | Aplicado: §4.3 (revert del merge de B, comprobación A89, conflicto posible) y §4.7; A y B separados convertido en pregunta (D5) |
| VR-06 | La confirmación en la imagen de MIROVA sin quién ni plazo | Aplicado quién (la sesión que lee el issue) y cuándo (el mismo día UTC); qué hacer sin imagen convertido en pregunta (D6) |
| VR-07 | La regla vive sólo en `loop/activo` y todo B la cita | Aplicado: §5, la regla sellada entra a main en el PR A en esta misma ruta |
| VR-08 | §3 con tres versiones de la guardia | Aplicado: §3 describe sólo la guardia implementada; las otras al Anexo A como historia |
| VR-09 | Disparador sin «nocturna» y cita de D-9 que no aplica a MODIS | Aplicado: §4.2 (pasada nocturna, `ENABLE_DAYTIME_MODIS = False`; D-9 y N-3 no aplican, N-3 definida) |
| VR-10 | (ii) se leía como conteo absoluto | Aplicado: §4.4 (ii) es sobre-publicación diferencial, con la tasa absoluta de K (12 de 1.194) para mostrar por qué |
| VR-11 | «ver 29 protegidas» ambiguo; «lo probable es que mande el plazo» no se sostiene | Aplicado: §4.6 («tener record»; las 29 llegan cerca del día 109 al ritmo de 16 en 60 días) |
| VR-12 | Citas corridas o incompletas | Aplicado: (a) l. 49 y tag vigente, en el Anexo A; (b) 804 a 808 y función `calcular_vrp_granulo`, §1; (c) tests de B, §5; (d) nota de consumidores, Anexo A; (e) frase «A COMPLETAR» borrada; (f) N-3 definida, §4.2; (g) «28 noches» con fuente (programa §12.3 punto 4), «~19 UTC» marcado sin fuente en el Anexo A; salvedad de 171-03, §6 |
| V1-02 | §4 sin paso para el día después: records de la vía en `data/`, ficha | Aplicado como §4.7 (datos, lectores, guardia, ficha v1.19, marcas A113); el apartado de los records convertido en pregunta (D7) |
| 207 | Tres fechas del encendido; la re-escritura del NRT pone la primera observación hasta ~8 días antes del merge | Aplicado: §4.1 (encendido por escritura, franja por observación, retrospectiva salvo `borde_del_encendido`); §5 pide corregir «no se reprocesan datos anteriores» de la ficha v1.18; unificar las tres funciones queda para el código (no es texto de la regla) |
| 210 | Constante inexistente, tag y línea viejos, issue que remite a una regla que no está en main | Aplicado: constante quitada (§4.1), tag y línea corregidos en el Anexo A, la regla entra a main (§5) |
| VB3-01 | La regla no estaba en el PR B ni en main, y las citas de main a su ruta decían «rama loop/activo» o «borrador» | Aplicado: la regla entra en B en esta ruta (§5, marca de ronda 4) y B corrige esas citas; el perfil de la guardia queda como está porque B no toca ese perfil |
| VB3-02 | «Reversión limpia» medida sólo contra las claves de MxD03; el revert choca con clave pegada a `thresholds:` o al flag y con el final de `nrt.yml` | Aplicado en texto: §4.3 dice que puede chocar en cualquier hunk de B y cómo se resuelve. La prueba de B no se amplió y el paso de `nrt.yml` sigue último (cambios opcionales del VB3, no pedidos en esta ronda) |
| VB3-03 | «Lo ve el monitor del NRT el mismo día» es sólo el job rojo; el monitor pide 3 corridas seguidas y rotula NASA o token | Aplicado: §4.4 (a) dice qué hace el monitor, que un gránulo malo puede dejar el NRT rojo hasta 8 días y que la sesión mira el paso «Revisar errores de MODIS en el log»; §6 (f) marcada |
| VB3-04 | D6 necesita la procedencia tabla u OCR y el instrumento no la publica | Aplicado en texto: §4.3 dice cómo se mira a mano (CSV consolidado contra CSV del OCR de Mirova-v1). Publicar la fuente en la vigilancia queda como seguimiento, fuera de esta regla |
| VB3-05 | Las marcas A113 de B decían «desde el merge del PR B (rama claude/s172-modd-flip)» | Aplicado en B (no es texto de esta regla): las tres marcas dicen desde la primera corrida del NRT con la vía, con la franja de unos 8 días, y la rama `claude/s173-modd-flip`, PR #934 |
| VB3-06 | Citas que no resuelven desde main; tag y merge-base viejos; `sombra_34` omitido | Aplicado: nota «Dónde vive la evidencia», marcas de rama o de «fuera de git» en cada cita, `resultado_f4.json` localizado (ruta completa, mismo sha256), merge-base de hoy en §5, `sombra_34` en §2 |
| VB3-07 | La ficha v1.18 no decía que una excepción de la vía deja la pasada sin record y el NRT en rojo | Aplicado en B (en la ficha, no en esta regla) |
| VB3-08 | La regla mandaba `git revert -m 1` sin decir que B no puede entrar por squash | Aplicado: §4.3, B entra por merge commit; si entró por squash, `git revert <sha>` sin `-m` |
| VB4-01 | B es fast-forward sobre main; un merge sin `--no-ff` o «Rebase and merge» no deja commit que revertir | Aplicado: §4.3 «Sólo con commit de merge», y el sha alternativo en §4.7 punto 6 |
| VB4-02 | La nota decía que la bitácora y el programa por sensor resuelven desde main; lo citado está sólo en `loop/activo` | Aplicado: nota «Dónde vive la evidencia» |
| VB4-03 | «B no toca `pipeline/` fuera del flag» era inexacto (dos comentarios de `process_modis.py`) | Aplicado: §5 y fila VB3-01 |
| VB4-04 | `vigilancia_guardia_modis.py` decía «borrador, propuestas que fija Nicolás al sellar»; el cuerpo del PR no conocía la ronda 4 ni el tag nuevo | Aplicado: comentario del script y cuerpo del PR B |
