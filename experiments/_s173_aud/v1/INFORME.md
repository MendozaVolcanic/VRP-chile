# Verificador V1: censo de consumidores del flag `enable_modis_codigo_mirova` (PR A y PR B del encendido de MODIS)

## 1. Encabezado

- **Fecha y hora del servidor**: inicio `Mon, 02 Nov 2026 12:49:40 GMT`, cierre `Mon, 02 Nov 2026 13:07:12 GMT` (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- **Commits sobre los que medí**: PR A = `0a0dae344` (rama `claude/s172-modd-encendido`), PR B = `c9525f994` (rama `claude/s172-modd-flip`, punta del worktree `D:/vrp-trabajo/worktrees/s172-modd-encendido`), base común de las dos ramas con main = `d3cd0b2ae` (`git merge-base`). `origin/main` al momento de medir = `47cdc446f` (22 commits `NRT update` después del `a3c5a9b49` que nombraba la tarea; ninguno toca código). Tag `pre-s171-adopcion-modd` = `07afb6e84`.
- **Modelo y esfuerzo con que corrí realmente**: modelo `claude-fable-5-1` (Claude Fable 5.1, según mi propio contexto de ejecución). El valor del parámetro de esfuerzo no me fue informado en el contexto ni puedo leerlo desde adentro: lo declaro SIN DATO. Quien orquesta lo tiene en la llamada `Agent` que me lanzó.
- **CARPETA**: `D:/vrp-trabajo/temporales/s173_aud/v1/` (este informe, `caminos.md` sellado con sha256 `621cf468...1ed2ff` a las 12:51:14 GMT antes de abrir ningún archivo citado, los scripts y sus salidas, `hallazgos.csv`).
- **Límite que crucé a propósito y cómo**: para X2 necesité commits. Los hice en un worktree propio y temporal (`D:/vrp-trabajo/worktrees/s173-v1-revert`, HEAD suelto, sin rama, nunca empujado), con identidad `v1 <v1@local>`, y lo quité con `git worktree remove --force` al terminar (`git worktree list` ya no lo trae). No toqué `loop/activo`, el worktree compartido ni ninguna rama o tag. Quedan objetos sueltos en `.git` hasta el próximo `gc`.
- **Qué NO miré** (mi silencio no es «todo bien»): la carpeta del auditor (`f1/`, por regla); la suite completa de pruebas (prohibida; corrí 17 archivos sobre el árbol revertido y 15 sobre el árbol del patrón 6); el comportamiento de la interfaz de GitHub ante el conflicto de V1-01 (sólo git local); records reales de la vía (no existen, X3); las vistas `diario.html`, `mosaico.html` y `comparacion.html` más allá de un `grep` (no tienen lista de ancla honesta ni `exportCSV`); los workflows en `.github/workflows/_archive/`; la vía de VIIRS 750 y 375; la máquina local de Nicolás; la validez científica de la vía (no es mi eje).

## 2. En una pantalla

1. **Ninguno de los 10 hallazgos bloquea el merge del PR A ni el del PR B**: todos son del día después de un `git revert` (161, 162, 163, 169), de documentación o pruebas (165, 167, 168), de perfiles que nadie despacha hoy (166), de filtros de display sin datos reales (170) o de un riesgo residual que el PR A ya vigila (164). Veredictos: 9 CONFIRMADO, 1 CONFIRMADO EN PARTE (168), 0 REFUTADO; 170 CONFIRMADO EN PARTE en su magnitud.
2. **X1 CONFIRMADO** (los 30 workflows que nombran un perfil con vía instalan pyproj, en A y en B, `test_guard_pyproj_vias_s172` verde en B). **X3 CONFIRMADO** (0 records con `via_codigo_mirova` en `data/` de B, de `origin/main 47cdc446f`, de `sombra-34` y de `loop/activo`; control positivo: `codigo_sha` en 11 de 11 Tier A).
3. **X2 CONFIRMADO EN PARTE**: el `git revert` de B sale limpio en las seis secuencias que probé (merge commit, squash, A y luego B rebasado, con `sombra-34` antes o después) y 236 pruebas de 17 archivos pasan sobre el árbol revertido (= main + A, diff vacío). **Lo que falla es el merge, no el revert**: tal como está, B no se puede hacer squash sobre un main que ya tiene el squash de A (conflicto add/add en `tests/test_vigilancia_guardia_modis_s172.py`); hay que rebasar B después de mergear A (V1-01, gravedad 1).
4. **Patrón 6 (mover a A los cambios de B que leen records de la vía) es correcto y no rompe nada**, medido: `a256a75cc` + `087b08ced` + `ffe46a68e` sobre main + A aplican limpio, el flag sigue en `False` y 218 pruebas de 15 archivos pasan. Pero hay que mover los TRES: sin `ffe46a68e` el propio test de A `test_no_modifica_la_vigilancia_de_k` queda rojo (medido, V1-04). Mover también las tres declaraciones `enable_modis_codigo_mirova: false` de los YAML derivados es inerte y deja el laboratorio y el ancla pre-K explícitos.
5. **Lo nuevo**: la regla de reversión §4 no tiene paso para el día después (ni records de la vía que quedan en `data/`, ni ficha; V1-02, gravedad 2), y la vigilancia de la sombra en B deja de exigir frescura de K en MODIS en cuanto existe un record de la vía, sin mirar el flag (V1-03, gravedad 1).

## 3. Veredictos sobre los hallazgos del auditor

Formato: veredicto, mi gravedad, bloquea A / B / ninguno, y después los campos del hallazgo.

### 161. Tras el revert de B la vigilancia de K vuelve a contar como K los records MODIS de la vía y pide revertir K

- **Veredicto**: CONFIRMADO. **Gravedad V1: 3** (el auditor: 3). **Bloquea**: ninguno (es un defecto del estado posterior a un revert de B; hoy no hay records de la vía, X3). Arreglo natural: patrón 6 (sección 5).
- TÍTULO: la versión de A de `scripts/vigilancia_sombra.py` identifica «producción = K» por la marca de régimen, que un record de la vía también lleva.
- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py` en B, l. 423 a 447 (`claves_via`, `cargar_insumos(win, via=None)`, filtro `prod = [... if r.get("sha") and (not via or clave not in via)]`), añadido por `a256a75cc`; en A la misma función (l. 423 a 433 de `git show 0a0dae344:scripts/vigilancia_sombra.py`) filtra sólo por `r.get("sha")`. `scripts/banco_paridad.py:289` llena `sha` con `regimen.codigo_sha`. `pipeline/store.py:549` escribe `record["regimen"] = _marca_regimen()` para todo record que pasa por `append_record`, sin condición (l. 543 a 549 leídas), y `scripts/run_pipeline.py:266` manda el record de la vía por `store.append_record` igual que uno de K. El disparador: `scripts/vigilancia_sombra.py`, `_sombra_si_produccion_no` (pasadas con `sombra_pub True` y `prod_pub False`) y `disparadores` (l. 255 a 290): candidata protegida dentro de plazo → `REVERSION_CANDIDATA`; el issue de `.github/workflows/vigilancia-sombra.yml:135` dice, TEXTO: «pre-autoriza revertir K con git revert del PR de adopcion, DESPUES de confirmar la alerta en la cabecera de la imagen de MIROVA».
- QUÉ PASA: físicamente, una noche en que el detector de la vía (grilla de MIROVA, su fondo) no alerta y el laboratorio C0 sí publica una protegida. Tras un revert de B, el código de A lee ese record de la vía como si fuera K (trae `codigo_sha`), y la vigilancia de la adopción de K abre el issue que pide revertir #850, que es el detector de los tres sensores, por una pasada que K nunca procesó.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero; se ve como un issue «Sombra de K: candidata a reversion» en GitHub, que pide a una sesión revertir el PR de adopción de K previa confirmación con la imagen de MIROVA.
- CÓMO REPRODUCIRLO: `python D:/vrp-trabajo/temporales/s173_aud/v1/169_167_161_simulacion.py` desde el worktree de B (salida en `169_167_161_simulacion_salida.txt`, línea «161 sha que leería el banco para via_rec = abc»); lectura de las líneas citadas. Sin volcán ni pasada real: no existe ningún record de la vía (X3).
- CONFIANZA: CONFIRMADO (mecanismo por lectura y por el script; el disparo real depende de que B esté encendida un tiempo y luego se revierta).
- GRAVEDAD 1-5: 3. Un revert de #850 ejecutado sobre esa base cambiaría VIIRS 375 y VIIRS 750, no sólo MODIS. Lo frena la confirmación humana que pide el issue.

### 162. Tras el revert de B el marcador del mapa de un record de la vía vuelve al primer píxel alertado

- **Veredicto**: CONFIRMADO. **Gravedad V1: 2** (el auditor: 2). **Bloquea**: ninguno (sólo tras un revert, sólo para los records de la vía que queden en la serie). Arreglo natural: patrón 6.
- TÍTULO: `pixelesDelMarcador` de A no tiene `codigo_mirova` en su lista de anclas honestas y cae a `anomaly_pixels[0]`.
- ARCHIVO:LÍNEA: A `frontend/index.html:1630-1631` (lista literal `["test1_roi", "test1_nti_peak", "ctx_cluster"]`); B `frontend/index.html:1618` (`esAnclaHonesta`, con `codigo_mirova`) y 1631 (la llamada); las siete copias de la lista en B pasan por la función (diff A→B leído entero). La vía escribe `anomaly_pixels` en orden de barrido de toda la máscara y `final_hotspot_source: "codigo_mirova"` (`pipeline/mirova_v750_codigo.py:727-742`).
- QUÉ PASA: el marcador rojo de «cráter» de un record de la vía se dibuja en el primer píxel alertado en orden de fila y columna de la grilla, que puede ser un foco lejano, no en el centroide del cúmulo más radiante.
- CÓMO SE VE EN EL DASHBOARD: en la vista de detalle, el marcador por defecto a kilómetros del cráter para un record cuyo cúmulo está en el cráter.
- CÓMO REPRODUCIRLO: `node D:/vrp-trabajo/temporales/s173_aud/v1/162_marcador.js D:/vrp-trabajo/temporales/s173_aud/v1` (usa `index_A.html` e `index_B.html` extraídos con `git show`). Salida `162_marcador_salida.txt`: A `codigo_mirova` → `dist_km 14.89` (el primer `anomaly_pixel` sintético), B → `0.567` (el cúmulo); control: `ctx_cluster` da 0.567 en los dos y `vent` 14.89 en los dos. El 14,89 km es un valor que YO puse en el sintético; no reproduje el caso «V2» del auditor.
- CONFIANZA: CONFIRMADO (mecanismo medido con el predicado real del tablero ejecutado en node, regla A97).
- GRAVEDAD 1-5: 2 (posición en el mapa; la magnitud y la clase `summit/far` no cambian).

### 163. El revert de B borra de la ficha SDA y de MISSION el registro del período de MODIS con la vía; los datos quedan

- **Veredicto**: CONFIRMADO. **Gravedad V1: 2** (el auditor: 2). **Bloquea**: ninguno.
- TÍTULO: toda la v1.18 de la ficha y las marcas A113 del encendido viven sólo en B.
- ARCHIVO:LÍNEA: `git diff 0a0dae344 c9525f994 -- docs/FICHA_SDA_VRP_CHILE.md docs/MISSION.md CLAUDE.md` (leído): la fila `v1.18` del historial, la nota v1.18 de «Funcionamiento/lógica» y la de «Categorías de datos» son líneas `+` de B; A no menciona `v1.18` ni `S172` en la ficha (`git show 0a0dae344:docs/FICHA_SDA_VRP_CHILE.md | grep -n 'v1\.18\|S172'` da vacío). `docs/MISSION.md:8` en adelante (marca S172) es `+` de B. La regla de reversión (`origin/loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`, §4 l. 91 a 116, TEXTO) dice que la reversión «Se ejecuta con `git revert` del PR de encendido (nunca un reset), la hace la sesión que la detecte, abre un issue y avisa a Nicolás el mismo día», y no dice nada de la ficha ni de las marcas después del revert; la ficha sólo aparece en §5 (l. 126 y 127) como parte del PR de encendido.
- QUÉ PASA: tras el revert la ficha vuelve a la v1.17 («sigue apagada») mientras en `data/mirova_equivalent/` quedan records MODIS producidos por otro método, con otra magnitud y otra posición. Un SDA en producción (Res. CPLT N°372) queda con un período sin versión que lo describa.
- CÓMO SE VE EN EL DASHBOARD: invisible (la marca naranja de `cambio_detector.js` sigue, pero dice que la vía «reemplazó» a K, no que se revirtió; ver 169).
- CÓMO REPRODUCIRLO: en la simulación X2 (`X2_revert_escenarios.txt`, S1''): `git diff --stat 93528f597 HEAD` tras el revert da vacío, o sea el árbol es exactamente main + A, sin ficha v1.18.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2 (no tuerce una alerta; tuerce la trazabilidad exigida al SDA). Es el mismo hueco de V1-02.

### 164. Una excepción de la vía distinta de pyproj deja MODIS mudo con el NRT en verde; el primer aviso llega a los 3 días

- **Veredicto**: CONFIRMADO, con una precisión: el primer aviso llega el **cuarto día** (la condición es `dias > 3`), salvo que haya una alerta protegida de MODIS, en cuyo caso la guardia pide INVESTIGAR a las 24 h. **Gravedad V1: 2** (el auditor: 2). **Bloquea**: ninguno (el PR A trae justamente la vigilancia que lo acota; es un riesgo residual declarado).
- TÍTULO: `run_pipeline.py` atrapa toda excepción por gránulo y sigue; la vía no cae a K ante una excepción.
- ARCHIVO:LÍNEA: `scripts/run_pipeline.py:279-280` (`except Exception as e: print(f"  ERROR processing {l1b.name}: {e}")`, dentro del bucle de gránulos MODIS, leído l. 265 a 280); `pipeline/process_modis.py:637-660`: la vía cae a K sólo con `_via_marca` «sin_grilla», «sin_mxd03» o «geo_distinta»; una excepción en `leer_radiancia_modis`, `leer_geo_mxd03` o `calcular_vrp_granulo` sube hasta run_pipeline. `.github/workflows/nrt.yml:291-332`: «Assert Tier A records fresh» mira `records[-1]` de cualquier sensor, y desde S123 sólo avisa (no falla) pasadas 72 h; falla el run sólo con 0 records en el JSON (l. 309 a 311). `.github/workflows/nrt-healthcheck.yml:53,73`: `THRESHOLD_H = 48`, también sobre `records[-1]` sin distinguir sensor. `scripts/vigilancia_guardia_modis.py:304-305` (`avisos_produccion` por sensor MODIS) y `:415-420` (un aviso convierte VERDE en `VIGILANCIA_CIEGA`, y `.github/workflows/vigilancia-guardia-modis.yml` abre el issue «Guardia K de MODIS: vigilancia ciega»); `scripts/vigilancia_sombra.py:61` `MAX_DIAS_SOMBRA_SIN_DATOS = 3` y `:362-381` `_avisos_frescura` (`dias > MAX_DIAS...`). Además `vigilancia_guardia_modis.py:84,268-269`: `ESPERA_SIN_RECORD_H = 24`, protegida que la guardia publica y producción no tiene record → INVESTIGAR. Y `avisos_via` (l. leídas tras `def avisos_via`): si producción escribe MODIS pero la vía no desde hace más de 3 días, aviso; si el flag está encendido y nunca hubo record de la vía, aviso.
- QUÉ PASA: un gránulo MODIS que rompe la vía (archivo MxD03 corrupto, grilla con NaN, un cambio de formato de NASA) deja a MODIS sin record esa pasada; si rompe en todos, MODIS queda mudo en los 11 volcanes mientras VIIRS sigue escribiendo y los dos monitores de frescura (NRT, healthcheck) ven el JSON fresco por VIIRS.
- CÓMO SE VE EN EL DASHBOARD: la serie naranja de MODIS deja de avanzar; nada más. El operador no recibe aviso hasta el issue de la guardia.
- CÓMO REPRODUCIRLO: no lo ejecuté (exige un gránulo real y un fallo inyectado); la lectura de `run_pipeline.py:279-280` es inequívoca: el `except Exception` no distingue `ImportError` de nada. El propio guard del PR A lo documenta (`tests/test_guard_pyproj_vias_s172.py` l. 5 a 10, TEXTO: «La vía no cae a K ante una excepción, sólo ante «sin grilla», «sin MxD03» o «geo distinta»»).
- CONFIANZA: CONFIRMADO por lectura; sin medición con fallo inyectado.
- GRAVEDAD 1-5: 2. Sólo MODIS (VIIRS 375 cubre la noche, A77), acotado a unos 4 días por la guardia; la ventana es la misma que ya tenía K ante cualquier excepción, lo nuevo es que la vía tiene más puntos donde fallar.

### 165. Documentos y comentarios operativos siguen diciendo producción = K o vía APAGADA; el aviso del tablero lo lee el operador

- **Veredicto**: CONFIRMADO. **Gravedad V1: 1** (el auditor: 2). **Bloquea**: ninguno; es un olvido de propagación A113 que cabe en B.
- TÍTULO: B propagó la marca S172 a MISSION, CLAUDE.md, DIVERGENCES y la ficha, pero no a cinco lugares que dicen K.
- ARCHIVO:LÍNEA (todos en la punta de B, y ninguno aparece en `git diff --stat 0a0dae344 c9525f994`): `frontend/index.html:544` («Desde el 18 oct 2026 la réplica usa el detector K», aviso visible en la sección Métricas; el diff A→B de `index.html` sólo toca las anclas); `pipeline/mirova_v750_codigo.py:5-6` («APAGADA por flag en cada sensor ... con los flags apagados no corre nada de este archivo»); `pipeline/profile.py:906-907` («confirmó que entra APAGADA»); `README.md:52-56` (marca S160: «la réplica `mirova_equivalent` corre sin el Test 1 ... con la conectiva `max` ... y la banda 22 primaria en MODIS»); `docs/SINTOMAS.md:25-28` («Régimen vigente: el detector K está en producción ... banda 22 primaria en MODIS»).
- QUÉ PASA: quien lea esos textos creerá que MODIS corre K. El texto de `index.html:544` lo ve el operador; los otros cuatro los ve quien programa o audita.
- CÓMO SE VE EN EL DASHBOARD: `index.html:544` contradice al aviso naranja dinámico de `cambio_detector.js` (que sólo aparece cuando hay records de la vía con uno de K antes).
- CÓMO REPRODUCIRLO: `sed -n '544p' frontend/index.html`, `sed -n '5,6p' pipeline/mirova_v750_codigo.py`, `sed -n '906,907p' pipeline/profile.py`, `sed -n '52,56p' README.md`, `sed -n '25,28p' docs/SINTOMAS.md` en el worktree de B.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 1 (texto; la lógica y la marca dinámica son correctas).

### 166. 55 perfiles derivados heredan la vía sin declararla, entre ellos `_s154_reproc_k_historico`

- **Veredicto**: CONFIRMADO en el conteo y en el mecanismo; CONFIRMADO EN PARTE en el impacto (ningún workflow vivo despacha esos 55). **Gravedad V1: 2** (el auditor: 2). **Bloquea**: ninguno.
- TÍTULO: 60 perfiles hacen `extends: mirova_equivalent`; 55 no declaran `enable_modis_codigo_mirova` y en B los 55 lo heredan en `True`.
- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `166_censo_perfiles_B.txt` (script inline en mi sesión, lee cada perfil con `VRP_PROFILE=<perfil> pipeline.profile`, A89): «perfiles: 101 / extends mirova_equivalent: 60 / heredan ... SIN declarar en thresholds: 55 / de esos con ENABLE_MODIS_CODIGO_MIROVA=True efectivo: 55 / declaran en RAIZ ...: []». `pipeline/profile.py:51-67` (`_deep_merge`, un solo nivel) y `:909` (`_t.get("enable_modis_codigo_mirova", False)`). Quién nombra `_s154_reproc_k_historico` fuera de `experiments/`: sólo `scripts/reemplazar_ventana_reproceso.py` (l. 7, docstring: «perfil aislado identico a la replica»), su propio YAML y `tests/test_reproceso_historico_k_s154.py` (cuyas aserciones, l. 68 a 107, prueban el reemplazo por clave, no el flag); ningún workflow. Los cinco que B sí declara (`experimental`, `experimental_ndc_focus`, `_s146_ab_control`, además de `guardia_k_modis` y `sombra_codigo_mirova`) están fijados por `tests/test_guard_modis_codigo_mirova_encendido_s172.py` (VIVOS, l. 30 a 36), y el implementador dejó por escrito que los demás «no se tocan» (`pipeline/profiles/_s146_ab_control.yaml`, comentario S172 leído en el diff).
- QUÉ PASA: los brazos de A/B viejos (`_s1xx_ab_*`) y el perfil «K histórico» ya no significan lo que su nombre dice: si alguien vuelve a despachar `reproc-s151-ab-diurno.yml`, `reproc-s143-ab-d22d25.yml` o similares (siguen en `.github/workflows/`, no en `_archive/`, y X1 muestra que sí instalan pyproj), sus brazos corren MODIS con la vía y el resultado no es comparable con el que está escrito (A104). `_s154_reproc_k_historico` reprocesaría «K histórico» con la vía y `reemplazar_ventana_reproceso.py` lo pasaría a la serie operacional; eso es coherente con la producción de hoy, pero el nombre y el docstring mienten.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; se vería como un escalón en MODIS si un reproceso con un perfil «K» entrara a la serie creyendo que es K.
- CÓMO REPRODUCIRLO: desde el worktree de B, `VRP_PROFILE=_s154_reproc_k_historico python -c "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"` → `True`; `VRP_PROFILE=experimental_lowT ...` → `True`.
- CONFIANZA: CONFIRMADO (conteo y valores medidos); impacto operativo hoy: ninguno medido (0 workflows vivos los nombran).
- GRAVEDAD 1-5: 2.

### 169. Tras el revert el audit semanal saca a K de MODIS y la marca del tablero sigue diciendo vía

- **Veredicto**: CONFIRMADO, y el propio código de A lo anuncia. **Gravedad V1: 2** (el auditor: 2). **Bloquea**: ninguno (estado posterior a un revert).
- TÍTULO: el detector «vigente» de MODIS y la marca del tablero se derivan de la existencia de records de la vía en los datos, no del flag, y no saben de reversiones.
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:432-438` (`detector_de_noche`: toda noche MODIS desde la primera pasada de la vía es `VIA_MODIS`), `:441-452` (`_detector`, docstring TEXTO: «Si se revierte el encendido, los records MODIS nuevos vuelven a ser K en noches que esta función llama VIA_MODIS y quedan en `fuera_de_detector`: ese día cambia también»), `:471-477` (`frontera_via_modis` = mínima fecha con `via_codigo_mirova: true`), `:633-636` (`nuestros_por_noche`: «cada noche SÓLO con los de su detector. Los demás se cuentan en `fuera_de_detector`»), `:1113-1121`. `frontend/cambio_detector.js:135-170` (`primeraViaModis`: primera pasada de la vía con una de K antes; `textoAvisoModis`: «que reemplazó al detector K en MODIS»); incluido en `index.html:12`, `diario.html:10`, `mosaico.html:24`.
- QUÉ PASA: después de un revert, los records MODIS nuevos (K, sin la clave) caen en noches `VIA_MODIS` y el audit semanal los aparta a `fuera_de_detector`: el recall y la magnitud de MODIS se evalúan sobre un detector que ya no escribe. El tablero sigue mostrando el aviso naranja «la vía reemplazó a K», sin mención de la reversión.
- CÓMO SE VE EN EL DASHBOARD: aviso naranja permanente y línea vertical en la fecha del encendido, con un texto que ya no describe la serie.
- CÓMO REPRODUCIRLO: `python D:/vrp-trabajo/temporales/s173_aud/v1/169_167_161_simulacion.py` (salida `169_167_161_simulacion_salida.txt`): con records K (1-nov), vía (3-nov), caída a K (4-nov) y K tras revert (6-nov), `frontera_via_modis = 2026-11-03`; el record del 6-nov da `detector_de_record=K` pero `detector_de_noche=VIA_MODIS`; `cambio_detector primeraViaModis(...) = 2026-11-03T05:00:00.000Z`; control: sólo records K → `null`, record sin marca → `C0`.
- CONFIANZA: CONFIRMADO (medido con las funciones reales de A, en python y en node).
- GRAVEDAD 1-5: 2.

### 167. La prueba «serie pura K» identifica K por `codigo_sha` y da por K los records de la vía

- **Veredicto**: CONFIRMADO. **Gravedad V1: 1** (el auditor: 1). **Bloquea**: ninguno.
- ARCHIVO:LÍNEA: `tests/test_guard_serie_k_pura_s158.py:33-34` (`es_k`: `bool(regimen.codigo_sha)`); el archivo no cambia entre A y B (no está en el diff). `pipeline/store.py:549` escribe la marca para todo record.
- QUÉ PASA: la prueba fue escrita para separar C0 (sin marca) de K (con marca); un record de la vía trae marca y pasa como «K». La prueba sigue siendo válida para lo que mide (nada sin marca desde la frontera); su nombre y su docstring ya no cubren el tercer detector.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `169_167_161_simulacion_salida.txt`, línea «167 es_k(via_rec) = True ; es_k(k_post) = True ; es_k(c0_ctrl) = False».
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### 168. El tablero no lee `via_codigo_mirova` y el CSV exportado no la trae

- **Veredicto**: CONFIRMADO EN PARTE. La parte que cae: el tablero SÍ lee `via_codigo_mirova`, en `frontend/cambio_detector.js:159-160`, que `index.html`, `diario.html` y `mosaico.html` cargan (es la marca naranja de A). La parte que se sostiene: `frontend/index.html` no lee el campo en ninguna línea (`grep -n via_codigo_mirova frontend/*.html` → 0) y `exportCSV` (`index.html:4361-4373`) no lo exporta. **Gravedad V1: 1** (el auditor: 1). **Bloquea**: ninguno.
- ARCHIVO:LÍNEA: `frontend/index.html:4365-4373` (cabeceras del CSV: trae `final_hotspot_source`, no `via_codigo_mirova`); `pipeline/mirova_v750_codigo.py:742` (`final_hotspot_source: "codigo_mirova"`) y `:711-714` (sin alerta: `final_hotspot_source: None`); `pipeline/process_modis.py:1767` (la caída a K lleva `via_codigo_mirova: "sin_mxd03"` y compañía). Sólo `index.html` exporta CSV (`grep -c exportCSV frontend/*.html`: index 3, las otras 0).
- QUÉ PASA: en el CSV un record de la vía CON alerta se reconoce por `final_hotspot_source = codigo_mirova`; uno de la vía SIN alerta y uno de la caída a K («sin_mxd03», «sin_grilla», «geo_distinta») son indistinguibles de K.
- CÓMO SE VE EN EL DASHBOARD: en el archivo exportado, no en pantalla.
- CÓMO REPRODUCIRLO: `sed -n '4361,4373p' frontend/index.html`; `grep -n 'via_codigo_mirova' frontend/*.html frontend/*.js`.
- CONFIANZA: CONFIRMADO EN PARTE. GRAVEDAD: 1.

### 170. Filtros de artefacto calibrados con K aplicados a records de la vía con magnitud de unión y conteo de cúmulo

- **Veredicto**: CONFIRMADO en el mecanismo, CONFIRMADO EN PARTE en el efecto (dirección medida con sintéticos; magnitud real SIN DATO porque no hay records de la vía). **Gravedad V1: 1** (el auditor: 1). **Bloquea**: ninguno.
- ARCHIVO:LÍNEA: `pipeline/mirova_v750_codigo.py:734-742` (`"vrp_mw": vrp_mw` = suma de TODOS los alertados; `primary_cluster.vrp_mw = vrp_mw` y `n_pixels = len(cu)`, el cúmulo mayor); `frontend/index.html:1162-1183` (`mirovaEqVrp` publica `pc.vrp_mw`), `:1337-1341` (`isCirrusArtifact`: `t_max_k < 273.15` y `mirovaEqVrp > 10`), `:1357-1363` (`isDiffuseFieldArtifact`: `pc.n_pixels >= 100`, `eq >= 50`, `eq / npx < 1.0`), `:1365` y usos en 1425, 1681, 1842, 2432, 3669 (display: ponen la magnitud en 0 o saltan el record).
- QUÉ PASA: los dos filtros fueron calibrados (S90, S93) con `pc.vrp_mw` = suma del cúmulo y `n_pixels` del mismo cúmulo. En un record de la vía el numerador es la unión de la escena y el denominador el cúmulo: el filtro de campo difuso dispara MENOS (la razón MW/píxel se infla) y el de cirrus dispara MÁS (la suma de unión es mayor).
- CÓMO SE VE EN EL DASHBOARD: un record de la vía con fondo frío puede quedar en 0 MW en pantalla por «cirrus» con menos píxeles que antes; uno difuso puede dejar de ocultarse.
- CÓMO REPRODUCIRLO: `node D:/vrp-trabajo/temporales/s173_aud/v1/170_filtros.js D:/vrp-trabajo/temporales/s173_aud/v1/index_B.html` (salida `170_filtros_salida.txt`): difuso K(60 MW/120 px, 276 K) = true, vía (300 MW unión/120 px) = false; cirrus K(8 MW, 270 K) = false, vía (12 MW unión) = true; control con t_max 300 K: ambos false.
- CONFIANZA: CONFIRMADO EN PARTE. GRAVEDAD: 1 (display; sin records reales no se puede decir cuántos).

### X1. En las puntas de A y B ningún workflow que corre un perfil con la vía deja de instalar pyproj

- **Veredicto**: CONFIRMADO. **Bloquea**: nada.
- Evidencia: `X1_pytest_guard_pyproj_B.txt` (4 passed, `tests/test_guard_pyproj_vias_s172.py` en B, con `-p no:cacheprovider`); `X1_workflows_via_sin_pyproj_B.txt` (mi propio barrido con las funciones del guard: 57 perfiles con alguna vía en B, 30 workflows vivos los nombran, los 30 tienen `pip install ... pyproj`, «sin pyproj: []»). Entre A y B no cambia ningún `.yml` (el diff A→B no toca `.github/`; los conteos por archivo son idénticos en las dos puntas, medidos con `git show 0a0dae344:<yml>`). Los siete workflows sin pyproj (`experimental-diario.yml`, `reproc-s121-d12-modis-ab.yml`, `reproc-s124-ndc-focus.yml`, `reproc-s129-ab-fondos.yml`, `reproc-s130-d18-roi1.yml`, `reproc-s133-area-ab.yml`, `reproc-s133-b22-ab.yml`) no nombran ningún perfil con vía en B. `requirements.txt:4` trae `pyproj>=3.5` pero ningún workflow instala desde `requirements.txt` (conteo `requirements=0` en todos): la protección es el `pip install` literal, como fija el guard.
- Pregunta 1 del instrumento: el guard mismo dio rojo en 22 workflows cuando se escribió sobre el perfil de B (docstring l. 18 a 20), así que sí ve la falla. Pregunta 2: el barrido imprime la lista de perfiles y workflows; un instrumento muerto daría 0 perfiles, no 57.

### X2. El `git revert` del merge de B sale limpio sobre main con o sin `sombra-34` mergeada antes, y las pruebas pasan sobre el árbol revertido

- **Veredicto**: CONFIRMADO EN PARTE. El revert sí sale limpio en todas las secuencias; las pruebas que corrí pasan. La parte que no se sostiene no es del revert sino del merge: **PR B no se puede hacer squash sobre main una vez mergeado A sin rebasarlo** (V1-01).
- Evidencia (`X2_revert_escenarios.txt`, sobre `origin/main 47cdc446f`, en mi worktree temporal):
  - S1 (squash de toda la rama B, sin A aparte) y S1b (merge commit `--no-ff`, `revert -m 1`): LIMPIO; árbol = main.
  - S1' (squash A, luego `merge --squash` B): **CONFLICTO add/add en `tests/test_vigilancia_guardia_modis_s172.py`** (A lo agrega, B lo edita, y la rama B no contiene el squash de A); `frontend/index.html` se auto-mergea. Reproducido en S2' y S3'.
  - S1'' (squash A, luego los 9 commits de B rebasados con `cherry-pick 0a0dae344..c9525f994`, squash, revert): cherry-pick LIMPIO, revert LIMPIO, `git diff --stat 93528f597 HEAD` vacío (árbol = main + A); y el árbol B rebasado es igual a `c9525f994` fuera de `data/` (diff vacío).
  - S2'' (`sombra-34` antes de A y B) y S3'' (`sombra-34` después de B): revert LIMPIO; en S3'' el árbol revertido es idéntico a main + A + sombra-34 (diff vacío contra un squash hecho aparte). El único archivo que B y `sombra-34` tocan a la vez es `tests/test_sombra_codigo_mirova_s167.py` y se auto-mergea.
  - Pruebas sobre el árbol revertido S1'' (`X2_pytest_arbol_revertido.txt`): `ENABLE_MODIS_CODIGO_MIROVA = False` leído de `pipeline.profile`; **236 passed en 42,9 s**, 17 archivos: los 10 que A agrega o modifica, los que B modifica (que vuelven a su versión de A) y los guards de flags (`test_guard_adopcion_k_s153`, `test_experimental_congelado_s150`, `test_sombra_codigo_mirova_s167`, `test_mirova_modis_codigo_s164`, `test_process_modis_core`, `test_guard_serie_k_pura_s158`, `test_reproceso_historico_k_s154`). **No es la suite completa** (prohibida en esta tarea): SIN DATO para el resto.
- Pregunta 1: un conflicto se ve como `CONFLICTO` con el nombre del archivo (lo vi en S1'); pregunta 2: un revert «vacío» se distinguiría porque el `diff --stat` contra main + A no daría vacío.

### X3. No existe ningún record real de la vía de MODIS en `data/` (sólo sintéticos)

- **Veredicto**: CONFIRMADO.
- Evidencia: script inline (en mi sesión) que parsea todos los `data/**/*.json` del worktree de B buscando `via_codigo_mirova` o `final_hotspot_source = codigo_mirova`: «TOTAL files con texto: 0». `git grep -l via_codigo_mirova origin/main -- data/` → 0; igual en `origin/claude/s172-sombra-34` y `origin/loop/activo`. Control positivo: `grep -l codigo_sha data/mirova_equivalent/*.json | wc -l` → 11. Lo sintético vive en `tests/` (12 archivos) y `experiments/_s162_*`, `_s164_*`, `_s165_*`.
- Observación fuera de eje (SEGUIMIENTO 1): tampoco hay records de la vía de VIIRS 750 ni de 375 en ningún `data/` del repo, aunque `tests/test_tablero_ancla_codigo_mirova_s172.py` l. 7 habla de «records reales de Chillán de la sombra». Dónde viven esos records: SIN DATO.

## 4. Hallazgos propios

### V1-01. PR B, tal como está, no se puede hacer squash sobre main después del squash de A: conflicto add/add

- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `X2_revert_escenarios.txt`, bloques S1', S2', S3': «CONFLICT (add/add): Merge conflict in tests/test_vigilancia_guardia_modis_s172.py». Causa: A agrega el archivo (0a0dae344) y B lo edita (`ffe46a68e`); la rama B contiene los commits de A, no el squash de A que quedará en main; el merge-base de B con main + A(squash) sigue siendo `d3cd0b2ae`.
- QUÉ PASA: GitHub mostrará el PR B como no mergeable (o lo mergeará mal) en cuanto A entre por squash. Con un merge commit de A (`--no-ff`) no pasa (S1b limpio), pero el repo mergea por squash (regla A39). La salida es rebasar B sobre main después de mergear A (`cherry-pick 0a0dae344..c9525f994` aplicó limpio en S1'') y forzar la rama.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: en un worktree propio sobre `origin/main`: `git merge --squash 0a0dae344 && git commit`, luego `git merge --squash c9525f994` → conflicto.
- CONFIANZA: CONFIRMADO en git local; SOSPECHA sobre cómo lo presenta la interfaz de GitHub (no la miré).
- GRAVEDAD 1-5: 1 (proceso; no toca ninguna alerta). **Bloquea**: el merge de B en su forma actual exige un rebase previo; no bloquea A.

### V1-02. La regla de reversión §4 no tiene paso para el día después: ni los records de la vía que quedan en `data/` ni la ficha

- ARCHIVO:LÍNEA: `origin/loop/activo:experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` l. 91 a 116 (§4, leído entero): `git revert`, issue y aviso; nada sobre qué hacer con los records MODIS de la vía ya escritos ni con la ficha. Los consumidores de A que leen esos records los interpretan mal después del revert: `scripts/vigilancia_sombra.py` de A (161), `frontend/index.html` de A (162), `scripts/auto_audit_weekly.py:441-452` y `frontend/cambio_detector.js:135-170` (169). La ficha vuelve a v1.17 (163).
- QUÉ PASA: 161, 162, 163 y 169 son el mismo hueco visto por cuatro instrumentos: el estado «se encendió y se revirtió» no está diseñado. Un revert deja records de otro detector dentro de una serie que todos los lectores llaman K, y un documento que dice que la vía nunca se encendió.
- CÓMO SE VE EN EL DASHBOARD: lo de 162 y 169.
- CÓMO REPRODUCIRLO: ver 161, 162, 163, 169.
- CONFIANZA: CONFIRMADO (lectura de la regla y mediciones de los cuatro hallazgos).
- GRAVEDAD 1-5: 2. **Bloquea**: ninguno. Qué pide: un párrafo en §4 (apartar o marcar los records de la vía como `data/_c0_residuales/` hizo con C0 en S158, re-fechar `frontera_via_modis` y la marca, ficha v1.19) y el patrón 6 para que los lectores de A sepan de la vía.

### V1-03. La vigilancia de la sombra (B) deja de exigir frescura de K en MODIS en cuanto existe un record de la vía, sin mirar el flag

- ARCHIVO:LÍNEA: `scripts/vigilancia_sombra.py:470-474` en B: `sensores_k = [s for s in aa.SENSORS if not (via and s == "MODIS")]`, con `via = claves_via()` (l. 464), que es el conjunto de claves con `via_codigo_mirova: true` en `data/mirova_equivalent/`, no el flag de `pipeline.profile`.
- QUÉ PASA: mientras B esté encendida es lo buscado (MODIS ya no es K). Después de un revert, los records de la vía siguen en los datos, `via` no es vacío y la vigilancia de la adopción de K nunca vuelve a avisar si MODIS K deja de escribir. Queda cubierto sólo por `scripts/vigilancia_guardia_modis.py:304-305` (`avisos_produccion` por sensor MODIS), que es infraestructura de A y sigue corriendo tras el revert (su workflow no está en el diff de B).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura de las líneas; no lo medí con datos (no hay records de la vía). Para probarlo: `claves_via()` con un JSON que traiga un record `via_codigo_mirova: true` y `avisos_produccion(prod_sin_MODIS, hoy, sensores=sensores_k)` → sin aviso de MODIS.
- CONFIANZA: CONFIRMADO por lectura; efecto SIN MEDIR.
- GRAVEDAD 1-5: 1. **Bloquea**: ninguno. Si el patrón 6 lleva este cambio a A, conviene que `sensores_k` mire también el flag (`VRP_PROFILE=mirova_equivalent` → `ENABLE_MODIS_CODIGO_MIROVA`) además de las claves.

### V1-04. Patrón 6: mover sólo los dos commits de código sin `ffe46a68e` deja rojo un test del propio PR A

- SCRIPT:SALIDA: `P6_mover_a_A_pytest.txt`. Con `a256a75cc` + `087b08ced` + `ffe46a68e` sobre main + A: cherry-pick LIMPIO, flag `False`, **218 passed** (15 archivos, incluidos `test_vigilancia_sombra_via_modis_s172` y `test_tablero_ancla_codigo_mirova_s172`). Con sólo `a256a75cc` + `087b08ced`: `FAILED tests/test_vigilancia_guardia_modis_s172.py::test_no_modifica_la_vigilancia_de_k` (l. 357 a 362 de la versión de A: `git diff pre-s171-adopcion-modd HEAD -- scripts/vigilancia_sombra.py ...` tiene que dar vacío).
- QUÉ PASA: el test de A fija que A no toca `scripts/vigilancia_sombra.py`; mover el cambio de 161 a A exige mover también la enmienda de ese test.
- CONFIANZA: CONFIRMADO (medido). GRAVEDAD: 1. **Bloquea**: ninguno; es la condición para que el patrón 6 salga verde.

## 5. Patrón 6: ¿es correcto mover a A los cambios de B que leen records de la vía?

**Sí, y no rompe nada medible**, con tres condiciones:

1. Mover los tres commits juntos: `a256a75cc` (vigilancia de la sombra + `tests/test_vigilancia_sombra_s156.py` + `tests/test_vigilancia_sombra_via_modis_s172.py`), `087b08ced` (`esAnclaHonesta` en `index.html` + `tests/test_marcador_mapa_ctx_cluster_s154.py` + `tests/test_tablero_ancla_codigo_mirova_s172.py`) y `ffe46a68e` (la enmienda del test de A). Medido: limpio y 218 pruebas verdes con el flag apagado (`P6_mover_a_A_pytest.txt`). Sin `ffe46a68e`, rojo (V1-04).
2. Sin records de la vía, los tres cambios son inertes: `claves_via()` devuelve vacío y el filtro de `cargar_insumos` no quita nada (`not via` corta); `esAnclaHonesta("codigo_mirova")` no se evalúa nunca porque ningún record trae esa fuente (X3); `test_no_modifica_la_vigilancia_de_k` pasa a vigilar sólo el workflow. Los tests de B que SÍ dependen del flag (`test_guard_modis_codigo_mirova_encendido_s172`, las enmiendas de `test_guard_adopcion_k_s153`, `test_experimental_congelado_s150`, `test_sombra_codigo_mirova_s167`, `test_mirova_modis_codigo_s164`, `produccion_pre_k.py`, el fixture de `test_process_modis_core.py`) se quedan en B: esperan `True` en producción y en A darían rojo.
3. Conviene llevar también a A las tres declaraciones `enable_modis_codigo_mirova: false` de `experimental.yaml`, `experimental_ndc_focus.yaml` y `_s146_ab_control.yaml` (hoy en B): en A son inertes (el padre ya está en `False`) y después de un revert dejan explícito que el laboratorio y el ancla pre-K no siguen a la réplica (A117). Lo que NO se mueve: el flip de `mirova_equivalent.yaml`, los dos comentarios de `pipeline/process_modis.py` (A45: en B sólo cambian comentarios, l. 20 y 634 a 636), la ficha v1.18 y las marcas A113.

Lo que el patrón 6 **no** arregla: 163 (la ficha), 169 (la marca naranja y el audit semanal tras un revert, que ya están en A y siguen leyendo los datos), V1-02 y V1-03. Eso es un paso nuevo en la regla §4, no un movimiento de commits.

## 6. SEGUIMIENTOS (fuera de mi eje, dejados reproducibles)

1. **Records de la sombra «código MIROVA» ausentes de `data/`**: `grep -rl via_codigo_mirova data/` en B, `origin/main`, `sombra-34` y `loop/activo` da 0, pero `tests/test_tablero_ancla_codigo_mirova_s172.py` l. 7 cita «records reales de Chillán de la sombra» con el cúmulo a 0,567 km. O viven fuera del repo (artefactos de runner, rama no mirada) o la sombra de VIIRS 750 no escribe en `data/`. Confianza: SOSPECHA. Lo decide quien audite la sombra.
2. **`requirements.txt:4` declara `pyproj>=3.5` y ningún workflow lo usa** (conteo `requirements=0` en los 38 yml que corren perfiles). No es defecto hoy (el guard exige el `pip install` literal), pero un workflow nuevo que confíe en `requirements.txt` sin saber que nadie lo instala así caería en 164. Confianza: CONFIRMADO (conteo).
3. **`index.html:544` y los cuatro textos de 165** son A113 pendiente que cabe en B.
4. **Disco D: al 98 %** (6,0 GB libres al cerrar; bajó a 4,8 GB con mi worktree de 1,3 GB). Un segundo worktree simultáneo de otro agente cruza el límite de 3 GB de la tarea.

## 7. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- **X1**: `python -m pytest -p no:cacheprovider -q tests/test_guard_pyproj_vias_s172.py` en B → 4 passed; barrido propio `X1_workflows_via_sin_pyproj_B.txt` → «sin pyproj: []». Vara: el `pip install` literal de cada yml que nombra un perfil con vía según `pipeline.profile` (A89), no el YAML.
- **X3**: parseo de todos los JSON de `data/` (worktree B) y `git grep` en tres ramas remotas → 0; control positivo 11/11 con `codigo_sha`. Vara: el campo del record, no el flag.
- **X2 revert**: seis secuencias, todas LIMPIO; árbol revertido idéntico a main + A (y a main + A + sombra-34). Vara: `git diff --stat` vacío contra un squash hecho aparte.
- **Pruebas sobre el árbol revertido**: 236 passed, 17 archivos (`X2_pytest_arbol_revertido.txt`), con `-p no:cacheprovider` y rutas explícitas; `ENABLE_MODIS_CODIGO_MIROVA = False` leído de `pipeline.profile`.
- **Patrón 6**: 218 passed sobre main + A + tres commits (`P6_mover_a_A_pytest.txt`).
- **Los `.github/workflows/` son idénticos en A y B** (el diff A→B no los toca; conteos por yml iguales en las dos puntas).
- **`pipeline/process_modis.py` entre A y B cambia sólo en comentarios** (l. 20 y 634 a 636, diff leído): el revert de B no altera lógica del procesador, sólo el flag del YAML.
- **`pipeline/store.py:549` escribe `regimen` a todo record** (base de 161 y 167): leído.
- **Los perfiles vivos de B valen lo que el guard dice**: `166_censo_perfiles_B.txt` (experimental, experimental_ndc_focus, _s146_ab_control, guardia_k_modis en False; mirova_equivalent y sombra_codigo_mirova en True).

## 8. SIN DATO

- El valor del parámetro de esfuerzo con que corrí (no lo recibo en el contexto).
- La magnitud real de 162 y 170 sobre records de la vía (no existen; sólo dirección con sintéticos).
- El «14,89 km en V2» del auditor: no reproducido; el 14,89 de mi salida es un valor que yo puse.
- Comportamiento de la interfaz de GitHub ante V1-01 (no abrí la UI; `gh pr view 932` dice MERGEABLE sólo para `sombra-34`, que es otro PR).
- La suite completa sobre el árbol revertido y sobre el árbol del patrón 6.
- 164 con un fallo inyectado en un gránulo real.
- V1-03 con datos.

## 9. FUERA DE ALCANCE

- La carpeta del auditor y su razonamiento (por regla del verificador).
- Las vías de VIIRS 750 y 375 y la sombra `sombra_codigo_mirova` (salvo el seguimiento 1).
- La validez científica de la vía de MODIS (A/B MOD-D, regla de reversión §1 a §3).
- Los workflows archivados en `.github/workflows/_archive/`.
- Todo lo que corre en la máquina de Nicolás fuera de GitHub Actions.

## 10. Instrumentos en CARPETA

`caminos.md` (sellado), `162_marcador.js` + `162_marcador_salida.txt`, `166_censo_perfiles_B.txt`, `169_167_161_simulacion.py` + `_salida.txt` (+ `cd.js` auxiliar), `170_filtros.js` + `_salida.txt`, `X1_pytest_guard_pyproj_B.txt`, `X1_workflows_via_sin_pyproj_B.txt`, `X2_revert_escenarios.txt`, `X2_sha_revertido.txt`, `X2_sha_s1_revertido.txt`, `X2_pytest_arbol_revertido.txt`, `P6_mover_a_A_pytest.txt`, `index_A.html`, `index_B.html` (copias de `git show` para los scripts de node), `hallazgos.csv`.
