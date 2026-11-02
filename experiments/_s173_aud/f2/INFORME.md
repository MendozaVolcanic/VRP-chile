# Auditoría S173, frente F2: integración entre programas del encendido de la vía «código MIROVA» en MODIS

## 1. Encabezado

- Hora del servidor: inicio 2026-11-02 12:20:44 GMT, cierre 2026-11-02 12:54:43 GMT (header `Date` de `gh api -i`).
- Commits medidos:
  - base main `a3c5a9b498c5e2cf57d465aa65ba99938c2b594f` (origin/main local). El main remoto al empezar era `c3540b731`,
    21 commits adelante, todos «NRT update» de `data/` (compare de la API: 0 archivos fuera de `data/`): mismo código.
  - PR A `claude/s172-modd-encendido` = `0a0dae3448f3ad1ef130ec68b37cfbe97db526b8` (nace de `d3cd0b2ae`; desde ahí main
    sólo agrega datos y `latest_consolidado.csv`).
  - PR B `claude/s172-modd-flip` = `c9525f9946ccd03bdaad5ac28b5ef2318bcaee50` (A es ancestro de B).
  - PR #932 `claude/s172-sombra-34` = `28183712aac80dfe987a2d0973acd8718d65c61e` (nace de `14fb62030`).
  - Lector V375-E re-sellado: tag `s172-v375e-lector-resellado` = `fc3912cb2` (nace de `cc3887290`, que está en main).
  - Ramas de VIIRS 750: las 9 remotas con «750» cuyo último commit es de octubre o noviembre de 2026, incluida
    `s169-roi-v750` (lista en `v750_cruce_salida.txt`); las 4 de mayo y junio no las miré. Los refs locales coinciden con
    `git ls-remote` al 2026-11-02.
  - Combinaciones (árboles de `git merge-tree --write-tree`, sin commits): A `9af3a621b`, A+B `dc36546d1`,
    A+#932 `255163095`, A+B+#932 `a4ce2182a`; con la rama `s169-roi-v750`: main+s169 `640dbb25e`, A+B+s169
    `4ec84b957`, main+#932+s169 `aed333572`, A+B+#932+s169 `ca111e018`.
- Modelo y esfuerzo con que corrí: Opus 5.5 (`claude-opus-5-5`, lo que dice el entorno). El esfuerzo no lo declara el
  entorno en ninguna parte que yo pueda leer: SIN DATO (no lo invento).
- Prompt: `D:/vrp-trabajo/temporales/s173_aud/prompts/auditor_f2.txt`. Su sha256 en disco (CRLF) es `db55d751…`; con
  fin de línea LF da `0b38a4f8…`, el que nombró quien orquesta. Es el mismo texto.
- CARPETA: `D:/vrp-trabajo/temporales/s173_aud/f2/` (scripts con su salida al lado). Worktree propio
  `D:/vrp-trabajo/worktrees/s173-f2-combo` (detached en `a3c5a9b49`, llevado a cada combinación con
  `git read-tree -u --reset`), ya quitado con `git worktree remove --force`. No hice commit, push, merge ni tags; no
  despaché workflows; 10 llamadas de lectura a la API de GitHub.
- Disco: D: bajó a 3,6 GB libres a media sesión (otros agentes); nunca bajo 3 GB. Al cerrar, 7,2 GB.
- Qué NO miré (mi silencio aquí no es «todo bien»):
  - la regla de reversión entera (la verifica otro agente; yo sólo su encaje con el código);
  - la calidad de detección de la vía (si publica bien o mal): todas mis simulaciones del audit hacen que «la vía»
    publique exactamente lo mismo que K, para aislar la contabilidad;
  - el tablero en un navegador; el CI real de los PR en GitHub;
  - la batería propia del lector de V375-E (`probar_sombra.py`): el lector corre desde el checkout de su tag y A, B y
    #932 no cambian sus insumos sellados (verificado por S0 y S8, ver VERIFICADO LIMPIO);
  - la rama de V750-B del 2026-11-03: todavía no existe en el remoto; miré las ramas de V750 que existen.

## 2. En una pantalla

1. Grave (205, grav. 4): la primera vez que la vía publique MODIS en una noche con alerta de MIROVA, el audit semanal del PR A se cae (ValueError, `REGIMENES` sin "VIA_MODIS"): sin informe, sin issue, sin monitor, y revertir B no lo arregla.
2. Arreglado eso, el audit deja el recall de MODIS sin juzgar unas 7 a 8 semanas y sin avisarlo (206); y el revert de B choca en cuanto otro PR toque una línea vecina de su flag en el perfil de producción (208).
3. Merge con merge commit: los tres órdenes de A, B y #932 salen limpios y el revert de B deja exactamente main+A+#932 (871 pruebas verdes); con squash, B choca si no se rebasa tras A (203).
4. Entre piezas: B y #932 juntos dejan rojo el guard de B (`sombra_34` fuera de `VIVOS`, 201); #932 rompe 16 de 32 pruebas de la ROI de V750-B (202); B no comparte archivos con V750; el lector de V375-E no ve régimen nuevo.
5. NRT: cota medida de la vía ≤ 33 s por fecha (≤ ~4,4 min por job) contra 50 min de paso: cabe; la guardia y su vigilancia no las vigila nadie (204).

## 3. Hallazgos (ordenados por gravedad)

### 205. El audit semanal del PR A se cae con ValueError la primera vez que la vía publique MODIS en una noche con alerta de MIROVA

- TÍTULO: A × B: `estratificar_magnitud` ordena los regímenes con `REGIMENES.index` y `regimen_de_pasada` devuelve "VIA_MODIS", que no está en `REGIMENES`
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:764` (`REGIMENES = ("antes_535", "535_a_571", "571_a_K", "K")`), `:780-781` (`regimen_de_pasada` devuelve "VIA_MODIS"), `:841` y `:849` (`sorted(d.items(), key=lambda kv: REGIMENES.index(kv[0]))`), en `0a0dae344` (B no toca este archivo); `.github/workflows/audit-weekly.yml:86-87` («Run weekly audit», sin `continue-on-error`) y `:89` y `:105` («Commit results» y «Open issue if out of band», sin `if: always()`). SCRIPT:SALIDA `repro_estratos_via_salida.txt` (mínimo) y `sim_audit_via_salida.txt` con `audit_via_2026-10-25_stdout.txt` (audit real de punta a punta sobre los datos de main).
- QUÉ PASA: lo dispara justo lo esperado: Chillán, con el domo activo, MIROVA alertando en MODIS y la vía publicando esa noche. El audit agrupa la magnitud publicada por régimen (S157) y el PR A le enseñó a `regimen_de_pasada` un régimen nuevo, «VIA_MODIS», sin agregarlo a la tupla con que después ordena. El primer record MODIS de la vía que publique en una noche con alerta MODIS de MIROVA dentro de la ventana de 60 días hace caer `main()` con «tuple.index(x): x not in tuple». La prueba de punta a punta del PR A (`tests/test_auto_audit_via_modis_s172.py:111-121`, `_escenario`) sólo arma noches en que la vía NO publica (`vrp=0.0 if reciente`): el único camino que no cae es el que prueba.
- CÓMO SE VE EN EL DASHBOARD: invisible para el operador. En Actions, la corrida del lunes queda roja y nada más: no se escribe `latest.json` ni `history.jsonl`, no se commitea la unión histórica de esa semana (el snapshot de la referencia lo refresca igual `sync-mirova-csv.yml` cada hora, l. 18), y no se abre issue (ni FUERA_DE_BANDA ni DEGRADADO), porque los pasos siguientes no corren tras un paso rojo. Ningún workflow vigila `audit-weekly.yml` (en los workflows sólo aparece en comentarios). El último issue del audit sigue siendo #915 (2026-10-26, «recall MODIS 62.5 %, detector K»), que queda como la última palabra. Revertir B no lo arregla: el revert no borra los records de la vía de `data/mirova_equivalent/`, y siguen en la ventana de 60 días.
- CÓMO REPRODUCIRLO: `python -I repro_estratos_via.py <raíz de un checkout de A o de B>` (caso «vía publica 1,5 MW en noche con alerta», NevadosDeChillan MODIS 2026-10-30: ValueError; controles «misma noche sin vía» y «vía que no publica»: OK). De punta a punta: `python sim_audit_via.py <worktree con A+B+#932> 2026-10-25` (marca como vía los 208 records MODIS de los 11 desde el 2026-10-25; el control sin marcar corre y da FUERA_DE_BANDA; con la marca, rc=1 y traceback en la l. 849).
- CONFIANZA: CONFIRMADO (código real, dos instrumentos: función aislada y `main()` sobre los datos de main). Que la vía real publique en una noche con alerta en la primera semana es SOSPECHA muy probable: con K, en la ventana 2026-09-03 a 2026-11-02, MIROVA alertó en MODIS 18 noches y K publicó en 12 (recall 66,7 %, n = 18, `audit_control_latest.json`).
- GRAVEDAD 1-5: 4. No cambia lo que ve el operador, pero apaga en silencio, la semana del encendido, una de las dos redes que miran a la vía (la lista nominal de protegidas sin publicar y el DEGRADADO de los apagones del NRT), y la reversión de B no la repara. Ninguna prueba lo vigila.

### 206. Tras el encendido, el audit semanal deja de poder juzgar el recall de MODIS unas siete u ocho semanas, sin decirlo

- TÍTULO: A × B: con la vía, el recall de MODIS se juzga sólo con noches de la vía; el mínimo de 15 noches deja la banda muda y el aviso de «sensor sin juzgar» existe sólo para ceses de plataforma
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:94` (`MIN_N_RECALL = 15`), `:903` (el flag exige `n_noches >= MIN_N_RECALL`), `:553-575` (`sensores_sin_juzgar`: sólo plataformas que cesan), `:877-886` (`evaluacion_vigente`: en MODIS decide VIA_MODIS desde el primer record de la vía), en `0a0dae344`. SCRIPT:SALIDA `sim_audit_via_parche_salida.txt` (con `REGIMENES` ampliado sólo en memoria por `audit_parchado.py`, para ver qué diría el audit una vez arreglado el 205).
- QUÉ PASA: MIROVA alerta en MODIS unas 18 noches cada 60 días en los 11 (control: n = 18, ventana 2026-09-03 a 2026-11-02). Con la vía marcada desde el 2026-10-25 (8 días, un encendido de hace una semana) la vía tiene n = 5. Medido: desaparece el flag «recall MODIS 66.7% < banda 95.0% (n=18, detector K)», desaparece el de magnitud de Chillán MODIS (0,56x) y no aparece ningún aviso (`avisos_detector` vacío, `plataformas.sin_juzgar` vacío). Hasta juntar 15 noches con alerta MODIS desde la frontera (al ritmo de hoy, unos 50 días) la banda no puede dispararse. Lo que sí sigue: la lista nominal de protegidas (control positivo: Chillán MODIS 2026-10-25 07:20, 3,79 MW, pasa a «detector VIA_MODIS»).
- CÓMO SE VE EN EL DASHBOARD: invisible. En el issue semanal MODIS deja de salir en la línea de recall; quien lo lee entiende «MODIS mejoró» y lo que pasó es «MODIS no se midió». El cuerpo del PR B dice que «se acepta que el issue semanal salte»; en recall pasa lo contrario: se calla.
- CÓMO REPRODUCIRLO: `python sim_audit_via.py <worktree con A+B+#932> 2026-10-25 parche` (control, vía desde 2026-10-25, y mezcla con la frontera el 2026-10-24 sólo con MODIS_AQUA, que además deja 12 records en «K en noche VIA_MODIS»).
- CONFIANZA: CONFIRMADO sobre el audit parchado en memoria (sin parche no llega aquí: se cae, 205).
- GRAVEDAD 1-5: 3. Durante las primeras semanas la única red para pérdidas Muy Bajo y Bajo de MODIS es la vigilancia de la guardia, con cotas (2 y 3) aún por fijar. Ninguna prueba vigila que un detector nuevo con n bajo el mínimo quede rotulado «sin juzgar».

### 208. El revert de B deja de ser limpio en cuanto otro PR toque una línea vecina de su flag en el perfil de producción

- TÍTULO: B × próximos cambios de producción: el bloque que B inserta en `mirova_equivalent.yaml` queda pegado a los tres flags de MxD03, que es donde irán los próximos encendidos
- ARCHIVO:LÍNEA: `pipeline/profiles/mirova_equivalent.yaml:138-140` (los tres flags de MxD03, «se deciden aparte», regla §2) y `:141-148` (bloque de B, `enable_modis_codigo_mirova: true` en la 148), en `c9525f994`. SCRIPT:SALIDA `merge_perfil_vecinos_salida.txt` (`git merge-file` sobre los textos reales).
- QUÉ PASA: la regla pre-autoriza que la sesión que detecte una candidata revierta B «el mismo día» con `git revert`. Git trata como conflicto dos cambios en líneas contiguas. Medido: si en main ya entró un cambio de `enable_modis_dist_desde_crater` (la l. 140) o se agregó `enable_v750_codigo_mirova` junto al bloque de MxD03 o justo después del flag de B, el revert de B choca (3 de 3 casos); el control (un cambio en la l. 1) sale limpio y el control positivo (misma línea) choca. Lo mismo pasa al revés: B choca al mergearse sobre un main que ya trajo uno de esos cambios.
- CÓMO SE VE EN EL DASHBOARD: invisible; lo ve la sesión que tiene que revertir: el revert pre-autorizado se vuelve una cirugía a mano del perfil de producción, bajo apuro.
- CÓMO REPRODUCIRLO: `python -I merge_perfil_vecinos.py` (usa `mf/main.yaml` y `mf/B.yaml`, extraídos con `git show`).
- CONFIANZA: CONFIRMADO el mecanismo; que algún PR toque esas líneas dentro de los 120 días de la regla es SOSPECHA (los flags de MxD03 y la adopción de la vía de V750 están en el programa por sensor).
- GRAVEDAD 1-5: 3. Ataca la definición misma de «reversión limpia» en el único momento en que importa. Ninguna prueba lo vigila.

### 201. Con B y #932 juntos, el guard del propio PR B queda rojo: `sombra_34` es un perfil derivado programado que B no declara

- TÍTULO: B × #932: `tests/test_guard_modis_codigo_mirova_encendido_s172.py` falla en A+B+#932 porque `sombra_34` no está en `VIVOS`
- ARCHIVO:LÍNEA: `tests/test_guard_modis_codigo_mirova_encendido_s172.py:31-37` (`VIVOS`) y `:98-110` (la prueba), en `c9525f994`; `pipeline/profiles/sombra_34.yaml:26` (`extends: mirova_equivalent`) y `:35` (`enable_modis_codigo_mirova: true`), `.github/workflows/sombra-34.yml:31` (cron `7 13 * * *`), en `28183712a`. SCRIPT:SALIDA `pytest_combo_ABP.txt` (1 failed, 884 passed, 7 skipped) contra `pytest_combo_AB.txt` (783 passed, 6 skipped) y `pytest_combo_AP.txt` (871 passed, 7 skipped); `pytest_guard_B_con_sombra34.txt` (con `"sombra_34": True` agregado sólo en el worktree de medición: 6 passed).
- QUÉ PASA: no hay defecto de detección: la sombra de los 34 declara la vía de MODIS encendida a propósito, igual que la de los 11, así que con B no hereda nada nuevo y es lo que su informe quiere. Son dos piezas correctas: B fija en una lista cerrada qué perfiles derivados programados existen, y #932 agrega uno programado. Juntas, la prueba dice «perfiles vivos sin valor decidido de la vía de MODIS: ['sombra_34']». Es la única falla de 885 en la combinación, y agregar la entrada la deja verde.
- CÓMO SE VE EN EL DASHBOARD: invisible. Se ve en el CI (`tests.yml:13-16`, corre en `pull_request` y en `push` a main): el segundo de B y #932 en entrar deja main en rojo si su CI corrió antes de que entrara el otro (GitHub no re-corre el CI de un PR cuando cambia la base; conocimiento general, no medido aquí). Con main rojo, el PR siguiente (por ejemplo, la reversión de B) arranca con una falla ajena.
- CÓMO REPRODUCIRLO: `bash sim_merges.sh` (árbol `a4ce2182a`), `git read-tree -u --reset a4ce2182a` en un worktree y `python -m pytest -p no:cacheprovider tests/test_guard_modis_codigo_mirova_encendido_s172.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2. Lo vigila el propio guard (hace su trabajo). Lo rompe cualquier orden en que entren los dos; el segundo tiene que agregar `"sombra_34": True` a `VIVOS` o re-correr su CI sobre la base nueva.

### 202. #932 deja rojas 16 de 32 pruebas de la herramienta de V750-B que escribe la ROI en `grillas_mirova.yaml`

- TÍTULO: #932 × V750-B (rama `s169-roi-v750`): las pruebas de `scripts/roi_v750b_a_grillas.py` exigen que la grilla tenga sólo los 11
- ARCHIVO:LÍNEA: `tests/test_roi_v750b_variantes_s169.py:54` (`assert set(nuevo) == set(viejo) == set(R.VOLCANES)`), `:47` y `:136` (comparan el diccionario entero con el de los 11), en `origin/s169-roi-v750` `cd5aa300c`; `pipeline/grillas_mirova.yaml` de `28183712a` (45 entradas). SCRIPT:SALIDA `pytest_roi_v750b_s169.txt`: main+s169 32 passed; A+B+s169 32 passed; main+#932+s169 16 failed y 16 passed; A+B+#932+s169 16 failed y 16 passed (árboles en `arboles_s169.txt`).
- QUÉ PASA: el script en sí sigue bien sobre la grilla de 45: con B0 a B5 pone el brazo en los 11, deja los 34 en `def`, escribe una sola nota de brazo y B0 devuelve el archivo idéntico (`roi_v750b_sobre_45_salida.txt`). Lo que cae es la prueba, que fija «exactamente los 11». B no participa (A+B+s169: 32 de 32).
- CÓMO SE VE EN EL DASHBOARD: invisible; se ve en el CI el día de V750-B (2026-11-03): el segundo en entrar de #932 y la herramienta de la ROI deja `tests.yml` rojo.
- CÓMO REPRODUCIRLO: árbol `aed333572` con `git read-tree -u --reset` en un worktree y `python -m pytest -p no:cacheprovider tests/test_roi_v750b_variantes_s169.py`; `python -I roi_v750b_sobre_45.py <ese worktree>`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2. Fuera del eje de B, pero cae el mismo día. Además, con el brazo puesto, la sombra de los 34 sigue en `def` en VIIRS 750 mientras los 11 cambian: ningún informe dice si eso se quiere (SOSPECHA de decisión pendiente, no de código).

### 204. Nadie vigila que la guardia K de MODIS ni su vigilancia sigan corriendo

- TÍTULO: `nrt-monitor.yml` y el reporte de puntualidad cubren las dos sombras y la vigilancia de la de los 34, pero no `guardia-k-modis.yml` ni `vigilancia-guardia-modis.yml`
- ARCHIVO:LÍNEA: `.github/workflows/nrt-monitor.yml:156` (`workflow_id: 'sombra-codigo-mirova.yml'`) y `:207-217` (paso «Vigilar la sombra de los 34 y su vigilancia», #932); `scripts/medir_cadencia_cron.py:41-46` (`ESPERADO_POR_DIA` suma la sombra de los 34 y su vigilancia, no la guardia), en el árbol A+B+#932: `grep -n guardia` en `nrt-monitor.yml` da 0 líneas. El implementador lo dejó pendiente (`INFORME_IMPLEMENTADOR.md`, «Lo que quedó fuera»).
- QUÉ PASA: la guardia es la red de la regla de reversión: si la vía calla una protegida que K publica, sólo la vigilancia de la guardia lo dice. Si la guardia deja de correr, su vigilancia lo detecta por frescura (cron de respaldo 22:45, `vigilancia-guardia-modis.yml:21`). Si la que deja de dispararse es la vigilancia (workflow desactivado, cron y `workflow_run` que no llegan), no avisa nadie y el silencio se lee como «nada que revertir». #932 resolvió ese caso exacto para la sombra de los 34 (VS34-04, `decidirAusencia`) y no lo extiende a la guardia.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show a4ce2182a:.github/workflows/nrt-monitor.yml | grep -n guardia` (0 líneas) contra `| grep -n sombra-34`.
- CONFIANZA: CONFIRMADO (leído). La probabilidad de que la vigilancia deje de dispararse es SIN DATO.
- GRAVEDAD 1-5: 2. Deja sin vigilante al único instrumento que detecta una pérdida de la vía. Ninguna prueba lo vigila.

### 207. Tres programas fechan el encendido de tres maneras, y dos de ellas lo ponen hasta ~9 días antes del merge

- TÍTULO: A × B (persiste MA172-206 en el tablero y el audit): la marca del tablero y la frontera del audit usan la primera OBSERVACIÓN de la vía; la vigilancia usa la primera ESCRITURA; la regla, una constante que no existe
- ARCHIVO:LÍNEA: `frontend/cambio_detector.js:135-160` (`primeraViaModis`, por `datetime_utc`), `scripts/auto_audit_weekly.py:471-476` (`frontera_via_modis`, por `datetime_utc`), `scripts/vigilancia_guardia_modis.py:98-116` (`encendido_desde_datos`, menor `processed_utc`), en `c9525f994`; regla `REGLA_REVERSION_MODD_BORRADOR.md:93` (`CAMBIO_DETECTOR_MODIS_UTC`, ausente en A y B). SCRIPT:SALIDA `desfase_upgrade_modis_salida.txt`.
- QUÉ PASA: el NRT re-escribe pasadas ya escritas (la versión estándar reemplaza a la NRT). Medido en los records MODIS de los 11 observados del 2026-10-01 al 2026-11-02 cuya primera escritura fue en tiempo casi real: 543 de 579 se re-escriben, con desfase observación→última escritura de mediana 0,77 días, p90 7,1 y máximo 9,42 (control: los 36 nunca re-escritos, máximo 0,84 días). Tras el merge, esa re-escritura sale de la vía, así que el tablero dibuja la línea naranja «MODIS: vía MIROVA» y el audit pone su frontera hasta ~9 días antes del merge, en una franja donde conviven pasadas de K y de la vía; la vigilancia, en cambio, cuenta desde la primera escritura (el merge). El «~4,5 días» del implementador queda corto.
- CÓMO SE VE EN EL DASHBOARD: la marca naranja de MODIS en Chillán cae días antes del cambio real, y lo que hay entre la marca y el merge es una mezcla: un escalón ahí se atribuye a la vía y puede ser de K.
- CÓMO REPRODUCIRLO: `python -I desfase_upgrade_modis.py <worktree con data/ de main>`.
- CONFIANZA: CONFIRMADO (desfase medido sobre K; que la vía herede ese mismo desfase al re-escribir es la lectura directa del código, no medida con records de la vía).
- GRAVEDAD 1-5: 2. Ninguna prueba compara las tres fechas entre sí.

### 209. Persisten VMA172-202 y 203: una excepción de la vía que no sea la falta de pyproj deja MODIS mudo con el NRT en verde; lo ve la vigilancia de la guardia al tercer día

- TÍTULO: el paso «Comprobar pyproj» cubre un camino de dos (patrón 6): cualquier otra excepción de la vía no cae a K ni pone rojo el job
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:636-661` (el bloque de la vía no atrapa excepciones; sólo «sin_grilla», «sin_mxd03» y «geo_distinta» caen a K), `scripts/run_pipeline.py:279-280` (`except Exception` por gránulo, sigue), `.github/workflows/nrt.yml:291-330` (A57 mira el último record de cualquier sensor), en `c9525f994`. Lo que lo ataja: `scripts/vigilancia_guardia_modis.py:304-305` con `scripts/vigilancia_sombra.py:362-382` y `:61` (frescura de producción en MODIS por volcán, más de 3 días sin datos = aviso).
- QUÉ PASA: si la vía falla en un gránulo por otra razón (lectura del MxD03, triangulación de la interpolación), no se escribe record, no corre K y el NRT sale verde; VIIRS sigue escribiendo, así que el aviso de frescura del NRT no salta. Si falla en todos los gránulos MODIS, la vigilancia de la guardia avisa a los 3 días por volcán; si falla en algunos, sólo aparece en el conteo semanal (iii), que no dispara.
- CÓMO SE VE EN EL DASHBOARD: menos puntos MODIS de lo normal, sin aviso.
- CÓMO REPRODUCIRLO: lectura de los tres archivos citados; no lo provoqué en un runner.
- CONFIANZA: CONFIRMADO (leído; el implementador lo dejó pendiente por A45).
- GRAVEDAD 1-5: 2. Ninguna prueba lo vigila del lado del NRT.

### 203. Mergear B por squash sin rebasarlo después del squash de A choca (conflicto add/add)

- TÍTULO: orden A → B con squash: B choca en `tests/test_vigilancia_guardia_modis_s172.py` si no se rebasa sobre el main que ya trae A
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `sim_merges_salida.txt`, bloque «Estrategia squash» (`rc=1 ... CONFLICT (add/add)`), en los tres órdenes. Con merge commit los tres salen limpios.
- QUÉ PASA: A y B agregan el mismo archivo nuevo con contenido distinto (B lo cambia sobre A). Con merge commit la base del merge de B es la punta de A; con squash es `d3cd0b2ae` y el archivo figura «agregado por los dos lados». Lo escribió el implementador (`INFORME_IMPLEMENTADOR.md`, ronda 2, punto 6); el cuerpo del PR B («Orden recomendado») no lo dice.
- CÓMO SE VE EN EL DASHBOARD: invisible; GitHub marca el PR B con conflicto (falla ruidosa).
- CÓMO REPRODUCIRLO: `bash sim_merges.sh`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1. El riesgo real es arreglar el conflicto a mano el día del encendido.

### 210. Referencias de la regla y del issue que no calzan con el código de B

- TÍTULO: la regla cita una constante inexistente, un tag y una línea viejos, y el issue de reversión manda a leer una regla que no está en main
- ARCHIVO:LÍNEA: `REGLA_REVERSION_MODD_BORRADOR.md:93` (`CAMBIO_DETECTOR_MODIS_UTC`: 0 apariciones en `git grep` de `c9525f994`; el código usa la fecha desde los datos, 207), `:43` (manda a comprobar en el tag `s170-v375e-lector`; el vigente es `s172-v375e-lector-resellado`), `:47` («`RAIZ = AQUI.parents[2]`, l. 47»: en `fc3912cb2` está en la l. 49); `.github/workflows/vigilancia-guardia-modis.yml:132` (el issue «candidata a reversion» remite a `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, que existe en `origin/loop/activo` y no en main, A ni B). Calzan: `pipeline/profile.py:909` y `:79`, la aserción de `sombra-codigo-mirova.yml:110`, `SHA_SELLO_LECTOR` en l. 63 a 77, el corte de 5 km (hoy `mirova_v750_codigo.py:807-808`), 29 protegidas, 120 días, cotas 2 y 3, 0,05 MW, el tag `pre-s171-adopcion-modd` (`d3cd0b2ae`) y `sombra_pasadas_juzgadas_modis.json`.
- QUÉ PASA: es texto, no código: la sesión que tenga que revertir lee el issue, busca la regla en main y no la encuentra.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git ls-tree --name-only c9525f994 experiments/_s171_modd_adopcion/` y `git grep -n CAMBIO_DETECTOR_MODIS_UTC c9525f994`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1.

### 211. #932 cambia lo que haría producción en los 34 volcanes si alguien la corre ahí después de B

- TÍTULO: B × #932: con la vía encendida y las 34 grillas nuevas, un `mirova_equivalent` corrido a mano sobre uno de los 34 ya no cae a K («sin_grilla»): corre la vía con una grilla que no salió de un TIF de MIROVA y escribe en `data/mirova_equivalent/`
- ARCHIVO:LÍNEA: `pipeline/process_modis.py:638-643` (`volcan_por_coordenadas` y `grilla_del_volcan`: sin grilla, «sin_grilla» y K), en `c9525f994`; `pipeline/grillas_mirova.yaml` de `28183712a` (34 entradas por «la regla de la mayoría», `experiments/_s172_sombra34/INFORME.md` §1).
- QUÉ PASA: hoy ningún workflow programado corre producción sobre los 34 (la matriz y las dos listas de `nrt.yml` son los 11; `backfill-tier-a.yml` es Tier A). Queda el despacho manual (`reproc-chunked.yml` con volcán de entrada): ahí el record diría `via_codigo_mirova: true` igual que en los 11, sin rastro de que la grilla no es de MIROVA.
- CÓMO SE VE EN EL DASHBOARD: sólo si alguien lo corre; el record se vería como uno de producción.
- CÓMO REPRODUCIRLO: lectura; no corrí el pipeline. Que `--volcano X` explícito salte el filtro de monitoreados lo dice el informe de capacidad de S172; no lo verifiqué en `run_pipeline.py`.
- CONFIANZA: SOSPECHA (mecanismo leído, camino manual).
- GRAVEDAD 1-5: 1.

## 4. SEGUIMIENTOS (vistos fuera de mi eje o fuera de B)

- Ningún monitor vigila `audit-weekly.yml` (205 lo vuelve urgente, pero el hueco existe sin B). Confianza: CONFIRMADO por `grep -l audit-weekly .github/workflows/*.yml` (sólo comentarios en otros workflows).
- `tests/test_roi_v750b_variantes_s169.py:47`, `:54`, `:136` asumen 11 entradas (202): lo decide la sesión de V750 o la de #932. CONFIRMADO.
- La rama vieja `origin/loop/1.5-d25-v750-disco` choca con A en `.github/workflows/probe-s151-d25-v750.yml` (A le agrega pyproj); contra main ya chocaba en tres archivos más (`v750_cruce_salida.txt`). Gravedad 1.
- La regla l. 139 sigue con «la vía cuesta 1,1 a 1,25 veces K» (MA172-209): la cota que medí está en VERIFICADO LIMPIO (d).
- El tag del lector viejo y la línea 47 de la regla (210) vienen de antes del re-sellado: corregir en el texto de la regla.

## 5. VERIFICADO LIMPIO (con el comando y la vara)

- (a) Merge y reversión con merge commit. Vara: «reversión limpia» del prompt (revert del merge de B sin conflictos y
  con pruebas verdes). `bash sim_merges.sh` → `sim_merges_salida.txt`: A→B→#932, A→#932→B y #932→A→B con rc=0 y el
  mismo árbol final `a4ce2182a`; el revert de B (merge commit y squash, inmediato o después de #932) da exactamente
  `255163095` (= main+A+#932); control positivo: un conflicto forzado en `mirova_equivalent.yaml` da rc=1. Sobre ese
  árbol, los 48 archivos de prueba de la lista que existen ahí: 871 passed, 7 skipped (`pytest_combo_AP.txt`). Limpio hoy, con la salvedad
  del 208 si entra otro cambio vecino, y del 205, que el revert no repara.
- (a) VMA172-102 (orden de merge): A es ancestro de B (`git merge-base --is-ancestor 0a0dae344 c9525f994`).
- (a) La sombra de los 34 con B: `sombra_34` declara las tres vías encendidas y extiende producción directo; leído desde
  `pipeline.profile` en A+B+#932: MODIS True, V750 True, V375 True, igual que `sombra_codigo_mirova`; producción MODIS
  True, V750 y V375 False; guardia y laboratorios False. B no le cambia nada a la sombra de los 34. Las pruebas de
  #932 (`test_sombra_34_s172.py`, `test_mirova_v375_codigo_s165.py`, `test_sombra_codigo_mirova_s167.py`) pasan en
  A+B+#932: la única falla de la corrida es la del 201.
- (a) Pruebas de A con #932, sin B: 871 passed, 7 skipped (`pytest_combo_AP.txt`). De A con B, sin #932: 783 passed,
  6 skipped (`pytest_combo_AB.txt`). Lista de 51 archivos en `lista_pruebas.txt` (las de A, B y #932, los censos de
  workflows y perfiles, monitor, cadencia y vías). No es la suite completa.
- (b) Lector re-sellado de V375-E. Vara: sus propias funciones `cambio_significativo` y `SHA_SELLO_LECTOR` del tag
  `fc3912cb2`. `python s8_lector_combinaciones.py` → `s8_lector_combinaciones_salida.txt`: los archivos de
  `RUTAS_REGIMEN` que cambian contra main en A (1), A+B (6), A+#932 (3) y A+B+#932 (8) dan 0 significativos (el
  `process_modis.py` de B cambia sólo comentarios; el perfil de producción, sólo una clave de `CLAVES_PERFIL_OTRO_SENSOR`;
  las 34 grillas nuevas quedan fuera de `VOLCANES_GRILLA_REGIMEN`). Controles: `anomaly_k` en el perfil, `x0` de Láscar
  +1 m y una línea de código en `process_modis.py` dan True; sólo el flag de MODIS, las 34 grillas y un comentario dan
  False. El predicado del tablero (`isValidDetection` y `mirovaEqVrp`, l. 1162 y 1595) no cambia en A ni en B: los
  hunks de `index.html` caen fuera de esas funciones (`git diff -U0 a3c5a9b49 c9525f994 -- frontend/index.html`). S0:
  el lector corrido desde el checkout de su tag ve 16 de 16; corrido desde main ya falla hoy (falta
  `leer_posicion_v375e.py`) y con A o B fallan además `auto_audit_weekly.py`, `index.html` y, con B, el perfil: es la
  falla cerrada que el lector declara («Se corre desde un checkout del tag del lector»), no un defecto.
- (c) Ventana entre el merge de B y la primera corrida de la guardia. Vara: el código de B. La guardia corre a las 17:40
  UTC sobre «hoy y 7 atrás» (`guardia-k-modis.yml:25` y `:117-118`), así que las pasadas posteriores al merge quedan
  cubiertas en su corrida siguiente; mientras tanto la vigilancia ve pasadas de producción sin par de guardia, que no
  pueden ser candidatas (`calla` exige `guardia_pub is True`, `vigilancia_guardia_modis.py`, `disparadores`). Es atraso,
  no pérdida: hasta la corrida siguiente de la guardia (cron diario, más su atraso de horas). Si A y B entran el mismo
  día, el nulo igual tiene los 8 días de la primera corrida de la guardia. `encendido_desde_datos` usa el menor
  `processed_utc` (MA172-206 aplicado en la vigilancia). El issue «Guardia K de MODIS: candidata a reversion» existe
  (`vigilancia-guardia-modis.yml:132`).
- (d) NRT. Vara: `nrt.yml` de B: paso del pipeline 50 min (l. 185), job 80 min (l. 69). Medido con logs reales (`python
  tiempos_via.py` → `tiempos_via_salida.txt`): Láscar, mismas 3 fechas (2026-10-28 a 30) y los mismos 29 gránulos (5
  MODIS): la sombra con las tres vías (run 41034796854, job 123992887697; la revisión de la corrida dice «27 de la vía,
  K caídos 0») tarda 98,3 s en procesar contra 267,6 s de K en el NRT (run 41038778013, job 124006081054), que además
  escribe el JSON grande de producción. El log imprime la salida de todos los sensores en bloque, así que el costo de
  MODIS no se puede aislar: tomo como cota todo el procesamiento de la sombra, ≤ 33 s por fecha, ≤ ~4,4 min por job de
  8 fechas. El paso del NRT en el run 41353423746 (11 jobs, 2026-11-01 21:42 UTC) va de 11,1 a 20,0 min: con la cota,
  ≤ ~24,4 min contra 50. Cabe. Denominador: 1 volcán, 3 fechas, 5 gránulos MODIS de la vía; no mide volcanes del sur ni
  días con más gránulos.
- (e) Lo que sí funciona del detector VIA_MODIS (sobre el audit parchado en memoria): `detector_por_sensor` pasa a
  MODIS VIA_MODIS, la frontera sale de los datos, K se informa aparte, la protegida nominal cambia de dueño
  (`sim_audit_via_parche_salida.txt`). Lo que no funciona: 205 y 206.
- (f) VIIRS 750. Vara: `git diff --name-only` contra la base de cada rama y `git merge-tree` contra A+B+#932, con
  control contra main (`v750_cruce_salida.txt`). Ninguna de las 9 ramas toca `pipeline/`; ninguna comparte archivo con
  B; la única en común con A es la vieja `loop/1.5-d25-v750-disco` (SEGUIMIENTOS). Las que chocan contra A+B+#932
  (`s162-viirs750-f63ef4`, `s162-v750a-evaluador`, `s158-v750-probe` y `probe2`) chocan igual contra main sola, en
  archivos de `experiments/`: no lo causan A, B ni #932. La herramienta de la ROI de V750-B
  (`s169-roi-v750`) pasa 32 de 32 con A+B (`pytest_roi_v750b_s169.txt`); lo que la rompe es #932 (202). `s162-viirs750-2`
  (2026-11-01) entra limpia sobre A+B+#932.
- Regla C, MA172-201 (pyproj): censo por JOB (el guard del PR A mide por archivo) de los 21 jobs que llaman
  `run_pipeline.py` en A+B+#932 (`censo_workflows_pyproj.txt`): todo job cuyo perfil tiene una vía instala pyproj en
  el mismo job (nrt, backfill, reproc-chunked, sombra-codigo-mirova, sombra-34, probes, reproc de S135 a S151); los que
  no lo instalan corren perfiles sin vía (experimental, guardia, `experimental_ndc_focus`, `_d12_honest_anchor_modis`) o
  brazos de S129, S130 y S133 que no extienden producción (leídos con `git show`). El guard del PR A pasa en A+B+#932.
- Regla C, MA172-101 (vigilancia de la sombra de K): `git diff 0a0dae344 c9525f994 -- scripts/vigilancia_sombra.py`:
  la exclusión por clave entra en `cargar_insumos` (la única entrada de records de producción a `pasadas_de_alerta`,
  `disparadores` y `avisos_perfiles`) y la frescura de MODIS se deja de exigir sólo con records de la vía. No llama a
  `estratificar_magnitud`, así que el 205 no la alcanza (tampoco a `vigilancia_guardia_modis.py`).
- Regla C, MA172-102 (tablero): en `index.html` de B las siete copias llaman `esAnclaHonesta` (l. 1618, 1631, 1696,
  2734, 2765, 3282, 3677, 3683); `diario.html`, `mosaico.html` y `comparacion.html` no tienen listas de fuentes de ancla
  (0 apariciones de `ctx_cluster` y de `final_hotspot_source`).
- Regla C, MA172-103: el guard de adopción de K pasa en A+B y en A+B+#932 (dentro de los verdes).

## 6. SIN DATO

- Esfuerzo con que corrí: el entorno no me lo declara.
- Costo de la vía de MODIS aislado en el runner: el log no separa sensores; sólo hay cota (VERIFICADO LIMPIO, d).
- Si la protección de la rama main exige ramas al día antes de mergear (cambia cuán probable es el main rojo del 201).
- Qué publica la vía real en Chillán la primera semana (205 y 206 se midieron con «la vía» publicando como K).
- La rama de V750-B del 2026-11-03: no existe todavía en el remoto (`git ls-remote`), así que no sé qué archivos tocará
  aparte de lo que ya preparó `s169-roi-v750`.
- Probabilidad de que `vigilancia-guardia-modis.yml` deje de dispararse (204).

## 7. FUERA DE ALCANCE

- La regla de reversión como tal (umbrales, plazos, potencia): otro agente.
- La calidad de detección de la vía y su comparación con MIROVA.
- El tablero en el navegador y el texto que ve el operador.
- Arreglar cualquiera de los hallazgos (A45 en `pipeline/`; decisión de quien orquesta en el resto).
