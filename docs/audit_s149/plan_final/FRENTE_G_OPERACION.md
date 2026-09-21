# Frente G de la auditoría S149: operación y entrega

> Auditor del frente G. Hora del servidor al empezar: **2026-09-21 18:04 UTC** (`gh api -i`, cabecera `Date`).
> Remoto `main` = `1dba6c5f9` = HEAD local (verificado con `gh api .../commits/main`), así que los
> archivos de datos locales son los del remoto. Scripts propios en `experiments/_s149_audit/frente_g/`.
> Sólo lectura: no se corrió pytest, no se despachó nada, no se leyó ningún valor de credencial.
> Todo lo que no lleva archivo:línea o salida de un comando de esta sesión va rotulado SOSPECHA.

## 0. Lo que el operador ve, en una página

**Fenómeno primero.** El pipeline decide por pasada si hay un cúmulo caliente, dónde y con cuánta
energía, y lo persiste en el JSON del volcán. Pero el operador no mira ese JSON: mira tres vistas que
vuelven a decidir, en JavaScript, si esa pasada "cuenta", con qué magnitud y de qué color. Hoy esa
segunda decisión es coherente entre vistas en lo que importa, y depende de muy pocos campos.

| decisión en pantalla | campos del record que la gobiernan | dónde |
|---|---|---|
| ¿es detección? | `primary_cluster.vrp_mw > 0` (legacy sin cúmulo: `vrp_mw`, `triggered_test1`) | `isValidDetection`, `frontend/index.html:1466`, idéntica en `diario.html:405` y `mosaico.html:393` |
| ¿se publica con magnitud? | `distance_class == "summit"` y `primary_cluster.centroid_dist_km <= inner_radius_km` y tope 50.000 MW | `mirovaEqVrp`, `index.html:1043`, `mosaico.html:245`, `diario.html:239` |
| ¿qué magnitud? (sólo VIIRS 375) | `f5_core_vrp_mw` persistido por el pipeline; respaldo recalculado desde `anomaly_pixels` | `f5CoreMagnitude`, `index.html:1119` (idéntica en las tres) |
| ¿se oculta como artefacto? | `t_max_k`, `primary_cluster.n_pixels`, y `_mirova_confirmed` (cruce en el navegador) | `isCirrusArtifact` / `isDiffuseFieldArtifact`, `index.html:1207` y `1226` |
| ¿rojo o gris en el mapa? | `distance_class`; naranja si `primary_cluster.geo_class == "extension"` | `index.html:2881-2902` |
| ¿"5,00 MW" censurado? | valor exactamente igual a 5,0 (no hay marca en el record) | `esValorCensurado`, `index.html:1098` |
| posición y distancia mostradas | `final_hotspot_*` si `final_hotspot_source` está en `ctx_cluster`, `test1_roi`, `test1_nti_peak` | `index.html:2550`, `2851` |

`comparacion.html` no lleva ninguno de estos helpers (sólo `parseUtcMs`), coherente con lo que declara
`CLAUDE.md`. El recorte `_recent.json` que se sirve por defecto es un filtro puro de fecha de 100 días
(`scripts/build_recent_json.py:41-52`), no recalcula nada.

**Comparación de texto entre vistas** (`experiments/_s149_audit/frente_g/comparar_helpers_js.py --diff`,
cuerpos sin comentarios ni espacios; control positivo: `mirovaEqVrp` de `diario.html` tiene otra firma y
el script lo marca DISTINTO):

| función | index | diario | mosaico | lectura |
|---|---|---|---|---|
| `isValidDetection`, `f5CoreMagnitude`, `esValorCensurado`, `_havKm`, `parseUtcMs` | igual | igual | igual | sanas |
| `isSummitDetection` | igual | ausente | igual | `diario` no la necesita: filtra dentro de `mirovaEqVrp` |
| `mirovaEqVrp` | ref | **distinta** | igual | ver hallazgo G-07 (conocido desde S126, sigue) |
| `mirovaEqVrpCore`, artefactos | ref | sólo cambia la firma (`volcanoName`) | sólo cambia la firma | misma lógica |
| `mirovaEqVrpDisplay`, `isSensorVisible`, `ourSensorBucket` | sólo index | | | |

## 1. Hallazgos, por gravedad

### G-01. Una adopción cambia el pipeline hacia adelante, pero la pantalla mezcla los dos regímenes sin ninguna marca
- **ARCHIVO:LÍNEA / SCRIPT**: `experiments/_s149_audit/frente_g/predicados_por_vista.py` (salida abajo);
  records sin sello de versión: las claves de nivel superior de `data/mirova_equivalent/Lascar.json` son
  sólo `volcano` y `updated`, y en el record la única clave de versión es `product_version` (comando en
  "cómo reproducirlo"); `grep -n -i "annotation\|pipeline_version\|git_sha\|profile_hash"` sobre las tres
  vistas da 0 líneas.
- **QUÉ PASA**: el Test 1 integrado sostiene hoy la gran mayoría de lo que se publica. En los últimos
  30 días de cada archivo (11 Tier A, n = 3.697 records), de **1.671** pasadas que el tablero publica,
  **1.486 (88,9 %)** llevan `triggered_test1 = true` y **793 (47,5 %)** tienen el ancla
  `final_hotspot_source` en `test1_roi`. Por sensor (desde 2026-08-22): VIIRS 375 tiene `triggered_test1`
  en 1.201 de 1.485 records y ancla `test1_roi` en 599; VIIRS 750, 322 de 1.476 y 236; MODIS, 29 de 736.
  Si la réplica adopta "sin Test 1 integrado más conectiva `max`", cambian en los records nuevos
  `triggered_test1`, `n_test1_pixels`, `test1_k_observed`, `final_hotspot_source` (de `test1_roi` a
  `ctx_cluster` o vacío), `final_hotspot_lat/lon/dist_km`, `distance_class`, `primary_cluster.*` y
  `f5_core_vrp_mw`. Las tres vistas lo reflejan **solas**, porque sólo leen campos persistidos. Lo que
  **no** se refleja solo: (a) la historia. Los ~60.000 records ya escritos quedan bajo el régimen viejo;
  la tendencia de 90 días de `diario.html`, la chispa de 30 días de `mosaico.html` y las métricas en vivo
  de recall y precisión de `index.html` (`index.html:1246-1258`) van a promediar dos regímenes. (b) El
  record no guarda con qué código ni con qué perfil se produjo, así que ni el operador ni una auditoría
  posterior pueden separar los tramos salvo por fecha (es la regla A104 vista desde la pantalla). (c)
  Reprocesar MODIS sólo se puede en GitHub Actions (pyhdf roto en Windows, `CLAUDE.md` §Constraints), con
  el límite de 6 h por job.
- **CÓMO SE VE EN EL DASHBOARD**: el día de la adopción la frecuencia de barras de VIIRS 375 cae de
  golpe (S147 midió 86,1 a 28,7 % en negativos limpios) y el operador lo lee como "el volcán se apagó".
  Ningún rótulo le dice que cambió el instrumento.
- **CÓMO REPRODUCIRLO**: `python experiments/_s149_audit/frente_g/predicados_por_vista.py`;
  `python -c "import json;r=json.load(open('data/mirova_equivalent/Lascar.json',encoding='utf-8'));print([k for k in r if k!='records'])"`.
- **CONFIANZA**: CONFIRMADO lo medido (proporciones, ausencia de sello y de anotación). SOSPECHA la
  magnitud exacta del salto visual: el 86,1 a 28,7 % es de S147, no lo re-medí.
- **GRAVEDAD**: 4. No tuerce una detección, tuerce la lectura de tendencia, que es lo que el OVDAS usa.

### G-02. El token de Earthdata vence el 2026-10-03 07:18 UTC: quedan 11,6 días y cualquier reproceso de adopción cae encima
- **SCRIPT:SALIDA**: log del `nrt-healthcheck` run 35631361688 (2026-09-21 17:21 UTC):
  `EARTHDATA_TOKEN: estado=ok vence=2026-10-03T07:18+00:00 dias_restantes=11.6`. Secreto
  `EARTHDATA_TOKEN` actualizado el 2026-08-04T07:19:42Z (`gh api .../actions/secrets`, sólo nombres y
  fechas). `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` sin tocar desde 2026-04-04.
- **QUÉ PASA**: el NRT y todos los A/B autentican por ese token. El aviso automático existe y funciona
  (abre issue con 10 días o menos, o sea desde el 2026-09-23; hoy no hay issues abiertos). El riesgo no
  es que nadie se entere: es que una adopción con reproceso de historia (varios días de jobs) arranque
  antes de rotar y muera a la mitad, dejando la serie publicada a medio reprocesar. El par usuario y
  clave de respaldo está vencido según `CLAUDE.md` §Constraints (SOSPECHA: no lo probé, y no corresponde
  probarlo porque un intento fallido bloquea la cuenta, A71).
- **CÓMO SE VE EN EL DASHBOARD**: si vence sin rotar, la última fecha se congela y los workflows siguen
  en verde hasta que salta el healthcheck de 48 h. Ya pasó del 2026-07-17 al 08-04.
- **CÓMO REPRODUCIRLO**: `gh run view <último nrt-healthcheck> --log | grep dias_restantes`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 4 (3 si la rotación se hace antes de cualquier reproceso).

### G-03. La ficha de transparencia no registra dos cambios de lógica que sí están en producción, y su encabezado dice v1.4 con historial hasta v1.6
- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md:7` ("Versión: v1.4, 2026-08-30") contra `:48` (v1.6,
  2026-09-17) y `:49` (v1.5, 2026-09-02). `grep -c -i` sobre la ficha: "piso" 0, "S130" 0, "cirrus" 0,
  "tope" 0, "cloud" 0, "#535" 0.
- **QUÉ PASA**: entre v1.4 y v1.5 cambió lo que el sistema publica y la ficha no lo dice. (1) #571
  (`d55bcd5e1`, 2026-08-31) llevó los tres pisos de magnitud del perfil operacional a 0,0
  (`min_vrp_mw_viirs375` 0,02, `viirs750` 0,15, `modis` 0,05, los tres a 0.0; hoy
  `pipeline.profile.MIN_VRP_MW_VIIRS375 = 0.0`); según A104 eso movió la publicación de VIIRS 375 en
  negativos limpios de 62,1 a 87,1 % (cifra heredada, no re-medida). (2) La máscara de nube está apagada
  en producción (`pipeline.profile.CLOUD_MASK_BT_K = 0.0`), y la ficha sigue listando "nubosidad" como
  sesgo con "mitigación: filtros de contexto" (`:31`). Además, la ficha describe sólo el pipeline: no
  menciona que la pantalla aplica por su cuenta tres transformaciones que cambian lo que el operador ve
  (ocultar artefactos de cirrus y campo difuso, mostrar la magnitud del núcleo en vez del cúmulo en
  VIIRS 375, y el tope censurado de 5 MW), ni que "clasificar el nivel de actividad" (`:25`) ocurre en el
  navegador (SOSPECHA esto último: no busqué los umbrales de nivel en `pipeline/`).
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Se ve en una solicitud de transparencia: la ficha publicable
  no describe el sistema que corre.
- **CÓMO REPRODUCIRLO**: `sed -n 7p docs/FICHA_SDA_VRP_CHILE.md`; `git show d55bcd5e1 -- pipeline/profiles/mirova_equivalent.yaml`;
  `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.CLOUD_MASK_BT_K, p.MIN_VRP_MW_VIIRS375)"`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.
- **Qué habría que actualizar si se adopta "sin Test 1 más `max`"** (hoy `ENABLE_TEST1_PATH = True`,
  `ENABLE_TESTS_23_PROSE_BRANCH = False`): una versión nueva con (a) el retiro de la integral del Test 1
  como camino de detección y la conectiva de los Tests 2 y 3; (b) el párrafo de `:32`, que describe el
  sesgo topográfico "en la integral del Test 1", deja de aplicar tal como está; (c) la frase de `:25`
  "en el régimen de muy baja energía se recuperan focos sub-píxel débiles... mediante un anillo de fondo
  intermedio" describe una pieza del Test 1 (`ENABLE_TEST1_INTERMEDIATE_BG`) y cae con él; (d) el costo
  declarado: las pasadas que se dejan de publicar; (e) de paso, los dos cambios omitidos de arriba y la
  capa de pantalla; (f) las cabeceras FICHA de `test1_integrated.py` y de los tres procesadores.

### G-04. El tablero del perfil experimental se sigue desplegando con datos congelados hace 27 días
- **SCRIPT:SALIDA**: último commit remoto de `data/experimental/<vol>.json` para los 11 Tier A:
  **2026-08-25** entre 15:14 y 15:59 UTC (`gh api .../commits?path=...`). `curl -sI` a
  `https://mendozavolcanic.github.io/VRP-chile/experimental/index.html` y a
  `.../data/experimental/Llaima.json` dan 200 con `Last-Modified` de hoy 17:03 (se redepliegan, pero el
  contenido es el de agosto). `nrt.yml:200`: el paso experimental sólo corre con despacho manual
  `profile=experimental`; `nrt.yml:195-196`: escribe en `data/experimental_v2/`, que "nunca se commitea".
  El workflow se sigue llamando "NRT VRP Pipeline (both profiles)" (`nrt.yml:1`).
- **QUÉ PASA**: fue una decisión (S141, tag `pre-s141-t8a-experimental`), no un accidente. Lo que queda
  es una página pública viva que muestra un volcán de hace un mes como si fuera el estado del
  laboratorio. No verifiqué si la página avisa de la fecha (SOSPECHA que no).
- **CÓMO SE VE**: quien entre a `/experimental/` ve series que terminan el 25 de agosto.
- **CONFIANZA**: CONFIRMADO el congelamiento. **GRAVEDAD**: 3. Es la mitad del objetivo del dueño
  ("más detecciones en el experimental") y hoy no produce nada. Desarrollo: frente F.

### G-05. El cron entrega el 43 % de lo declarado y el dato llega con brechas de 5 a 7 horas; los monitores diarios corren con 5 a 7 horas de atraso
- **SCRIPT:SALIDA**: `experiments/_s149_audit/frente_g/cadencia_14d.py` (salida en `cadencia_14d.txt`),
  eventos `schedule`, ventana 2026-09-07 18:07 a 2026-09-21 18:07 UTC, denominador = lo que declara cada
  cron:

  | workflow | cron | ocurrieron / esperadas | resultado |
  |---|---|---|---|
  | `nrt.yml` | `0 */2 * * *` | 73 / 168 (**43 %**) | 73 success |
  | `nrt-retry.yml` | `30 1-23/2` | 78 / 168 (46 %) | 78 success |
  | `pages-deploy.yml` | `50 */2` | 74 / 168 (44 %) | 72 success, 1 failure, 1 cancelled |
  | `sync-mirova-csv.yml` | `12 * * * *` | 81 / 336 (**24 %**) | 81 success |
  | `nrt-monitor`, `nrt-healthcheck`, `audit-weekly`, `reproc-watchdog` | | 54, 14, 2, 82 | todos success |

  NRT: brecha mediana entre corridas **4,89 h**, p90 5,93 h, máxima **7,08 h** (2026-09-17 00:06 UTC),
  7 brechas sobre 6 h y ninguna sobre 8 h; atraso mediano respecto de la hora par 57 min; duración
  mediana de la corrida 69 min, máxima 100 min. Estable: 4 a 6 corridas por día todos los días.
  El healthcheck de hoy corrió a las 17:20 con cron de las 12:00, y el audit semanal a las 15:43 con
  cron de las 09:00.
- **QUÉ PASA**: no se pierden datos (cada corrida procesa el día completo) pero una anomalía nocturna
  puede tardar hasta unas 7 h en corridas más las ~3 h de latencia de NASA. El instrumento que lo mide
  ya corre dentro del healthcheck (`nrt-healthcheck.yml:303`) y hoy informó "Entrega global: 33 %" en 24 h.
  El disparador externo planeado en S142 **no existe**: en 14 días `nrt.yml` tuvo 76 eventos `schedule`
  y 2 `workflow_dispatch`, y la fila 31 de `REGISTRO_CREDENCIALES.md:57` sigue "por crear".
- **CÓMO SE VE**: "Último dato" con 6 a 10 h de edad a media mañana. Al momento de medir, el último
  record de la mayoría de los volcanes era de las 08:45 UTC y eran las 18:04.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 operativa; **no bloquea** una adopción.

### G-06. La copia del CSV de MIROVA que alimenta el tablero va a una cuarta parte de la cadencia declarada
- **SCRIPT:SALIDA**: `sync-mirova-csv.yml` 81 de 336 corridas en 14 días (24 %). Último commit remoto de
  `latest_consolidado.csv` y `data/mirova/Lascar.json`: 2026-09-21 14:06 UTC; fila más nueva del
  `latest_consolidado.csv` local: 2026-09-21 08:50; el scraper `Mirova-v1` ya tenía filas de las 12:50
  (primeras filas del CSV remoto, leídas con `curl -r 0-700`).
- **QUÉ PASA**: `_mirova_confirmed` se calcula en el navegador contra esa copia (`index.html:1442-1454`)
  y decide que un record confirmado por MIROVA **nunca** se oculte como artefacto (`index.html:1208`).
  Con la copia 4 a 6 h atrás, una pasada reciente que MIROVA sí publicó puede quedar oculta como cirrus
  hasta la siguiente sincronización. Ventana chica y sólo afecta records con `t_max_k` bajo cero y más
  de 10 MW.
- **CONFIANZA**: CONFIRMADO el atraso; SOSPECHA que haya ocurrido alguna vez (no busqué un caso).
  **GRAVEDAD**: 2.

### G-07. `mirovaEqVrp` de `diario.html` sigue distinta a las otras dos, y sólo `isValidDetection` tiene guard entre vistas
- **ARCHIVO:LÍNEA**: `frontend/diario.html:239` contra `frontend/index.html:1043`. `diario` mira
  `distance_class` antes de preguntar por el cúmulo, cae a `vrp_mw` sin tope de 50.000 MW y sin respaldo
  a `vrp_mir_mw`. Documentado en `tests/test_audit_metrics_paridad_frontend_s126.py:14-23` como
  "documentado, no unificado". El guard de tres vistas cubre **sólo** `isValidDetection`
  (`tests/test_guard_predicado_tres_vistas_s147.py:9-15`). `grep -ln "INNER_RADIUS_KM\|F5_R_CORE" tests/*.py`
  sólo encuentra el test del puerto a Python, no un guard entre vistas.
- **QUÉ PASA**: sin efecto hoy (todo record moderno trae cúmulo). Pero el radio interno por volcán está
  copiado a mano en **cuatro** lugares (`volcanoes.yaml`, `index.html:714-755`, `diario.html:227-231`,
  `mosaico.html:207-217`); hoy los cuatro coinciden en los 11 (comparado en esta sesión), y nada lo
  vigila. El radio interno decide qué se publica, así que una edición en un solo lugar haría que una
  vista publique lo que otra calla.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (latente).

### G-08. El mapa por volcán usa otro predicado que el gráfico, con efecto medido chico
- **ARCHIVO:LÍNEA**: `frontend/index.html:2820` filtra por `(r.vrp_mw ?? r.vrp_mir_mw ?? 0) > 0` y
  `:2902` por `distance_class`; no pasa por `isValidDetection`, `mirovaEqVrp` ni los filtros de artefacto.
- **SCRIPT:SALIDA**: `mapa_vs_grafico.py`. Últimos 30 días: 1.653 marcadores visibles contra 1.671
  publicadas; **0** marcadores sin publicación y **18** publicadas sin marcador (las 18 de Villarrica:
  `vrp_mw = 0` con cúmulo con energía). Toda la serie (n = 60.247): 41 marcadores sin publicación (todos
  "cúmulo en cero") y 297 publicadas sin marcador.
- **CÓMO SE VE**: en Villarrica, una barra en el gráfico sin punto en el mapa, unas 18 veces al mes.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2. Ojo para la adopción: si el cambio altera la relación
  entre `vrp_mw` del record y `primary_cluster.vrp_mw`, esta brecha puede crecer; conviene contarla en
  el evaluador del A/B.

### G-09. `REGISTRO_CREDENCIALES.md` se contradice a sí mismo sobre el token
- **ARCHIVO:LÍNEA**: `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md:28` (vigente,
  vence 2026-10-03) contra `:16` y `:138` ("AHORA: vencido, VRP Chile sin ingesta térmica desde el
  2026-07-17"). Lo mismo en `MAPA_WORKSPACE.md:390` ("expirado, sin datos hace 13 días") contra la ficha
  de `:150-158`, que sí está al día (verificada 2026-09-15, con la caducidad, la cadencia real de ~4,75
  corridas por día y la advertencia de buscar commits `NRT update`).
- **QUÉ PASA**: la fila y la ficha están bien; las secciones de "qué hacer ahora" quedaron de agosto.
  Quien lea primero el calendario cree que hay un apagón. Es el eje de esta auditoría en chico.
- **Credenciales en texto claro**: no abrí ningún archivo de credenciales. El registro declara
  (`:29`) una clave de cuenta en claro en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.env`.
  Verifiqué sin leerlo: existe (232 bytes, de abril), está ignorado por `.gitignore:13`, `git ls-files .env`
  da 0 y `git log --all -- .env` da 0. Vive dentro de OneDrive sincronizado. `CLAUDE.md` global declara
  además un PAT de GitHub en `~/.claude/settings.json` pendiente de rotar (no lo abrí).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### G-10. Deuda que estorba (sólo informar)
- **Ramas remotas**: 269 (`gh api .../branches --paginate`); 100 `claude/*`, 14 `s146*`, 13 `s149*`.
  Locales: 188. Tags remotos: 111. PR abiertos: 0. Issues abiertos: 0.
- **Ramas de datos `s146-ab/*`**: son **7**, la última escrita hoy 17:32 UTC por una corrida viva. El
  árbol de cada una pesa ~912 MB, **pero el de `main` pesa 884 MB**: comparten los blobs, y lo nuevo por
  rama es del orden de **30 MB** (355 MB bajo `data/_*` que ya están en `main`). El "900 MB cada una" es
  cierto como tamaño de árbol y engañoso como costo. No estorban al disco local mientras no se haga
  `fetch` de ellas.
- **Disco**: 17 GB libres de 476 (97 %). `.git` local 7,0 GB; `data/` 1,1 GB; tamaño del repo en GitHub
  9,4 GB; `Mirova-v1` 11,25 GB (`gh api repos/... .size`). SOSPECHA: ambos superan con holgura el tamaño
  que GitHub recomienda para un repositorio; no verifiqué ningún aviso de GitHub.
- **Stashes**: 4, del 2026-05-22 al 05-25 (S72 a S78), los mismos que A96 manda no tocar sin tag.
- **Worktrees**: sólo la raíz. **Sin seguimiento**: 4 rutas (`docs/PLAN_AUDITORIA_S149.md`,
  `docs/audit_s149/plan_final/`, `experiments/_s140/` de 5,8 MB, `experiments/_s149_audit/`); 563
  entradas ignoradas.
- **Workflows**: 32 yml vivos en `.github/workflows/`, de los que 22 empiezan con `probe-` o `reproc-`;
  descontando los dos de infraestructura (`reproc-chunked`, `reproc-watchdog`) quedan 20 de sesiones
  S120 a S146 (la convención de `CLAUDE.md` es devolverlos a `_archive/`).
- **Corrida en vuelo**: "A/B S146: sin el Test 1 integrado" en curso desde 12:30 UTC, con 3 fallas del
  mismo workflow en las últimas 24 h. Usa el mismo token que el NRT.
- **GRAVEDAD**: 1 a 2. Nada de esto bloquea.

## 2. Lo que bloquea una adopción y lo que no

**Bloquea (hay que resolverlo antes o en el mismo paso):**
1. **Decidir qué pasa con la historia** (G-01): reprocesar los 11 Tier A en los tres sensores, o marcar
   el cambio de régimen en pantalla y en el record. Sin una de las dos, la adopción se ve como un volcán
   que se apaga. El reproceso de MODIS sólo cabe en GitHub Actions.
2. **Rotar el token de Earthdata antes de cualquier reproceso** (G-02): vence el 2026-10-03 07:18 UTC.
3. **Ficha de transparencia** (G-03): la regla del proyecto exige mantenerla al día al tocar la
   detección; hoy ya debe dos cambios, y la adopción sería el tercero.
4. **Regla A45**: tag defensivo y confirmación de Nicolás (no es hallazgo, es el procedimiento).

**No bloquea:**
- La pantalla en sí: las tres vistas leen campos persistidos y reflejan solas el cambio en los records
  nuevos. No hay lógica de detección duplicada en JavaScript que haya que tocar; `triggered_test1` sólo
  aparece en la rama legacy de `isValidDetection` y en una cláusula de `isSummitDetection`.
- La cadencia del cron (G-05), el atraso del CSV (G-06), las copias del radio interno (G-07), el mapa
  (G-08), el registro de credenciales (G-09) y la deuda de ramas y disco (G-10).
- La salud del NRT y del scraper: los dos producen hoy.

**Conocimiento que estaba escrito y no donde se lee primero** (el eje de S149, en este frente):
- `CLAUDE.md` §Constraints todavía abre con "Secrets: EARTHDATA_USERNAME, EARTHDATA_PASSWORD" y la
  corrección va debajo; la caducidad exacta vive en el log del healthcheck y en el registro, no en el
  bloque de arranque.
- "Ramas de datos de 900 MB cada una": tamaño de árbol, no costo (G-10).
- El workflow se llama "both profiles" y corre uno (G-04).
- La ficha SDA dice v1.4 arriba y v1.6 abajo (G-03).

## 3. VERIFICADO LIMPIO

| qué miré | resultado | comando |
|---|---|---|
| Frescura del dato propio contra el remoto (detector de zombie) | 11 de 11 Tier A con commit `NRT update` de hoy (8 entre 10:22 y 10:44 UTC; Llaima, Villarrica y Chaitén 16:40 a 16:57); último run `schedule` verde 16:12 UTC; último record local (= remoto) 06:06 a 08:50 UTC de hoy | `gh api "repos/MendozaVolcanic/VRP-chile/commits?path=data/mirova_equivalent/<vol>.json&per_page=1"` |
| NRT: corridas fallidas en 14 días | 0 de 73 `schedule` | `cadencia_14d.py` |
| Healthcheck | "OK (11/11)", sin stale, sin issue abierto, token ok | log del run 35631361688 |
| Despliegue de Pages | 200 en las 4 vistas, el JSON de Llaima y el CSV, `Last-Modified` 17:03:44 UTC de hoy; últimos 5 despliegues success | `curl -sI https://mendozavolcanic.github.io/VRP-chile/...` |
| CI en `main` | últimos 6 `push` en success, incluido HEAD `1dba6c5f9` | `gh api .../workflows/tests.yml/runs?branch=main` |
| Scraper `Mirova-v1` | vivo: commit 18:05 UTC de hoy; fila más nueva del consolidado 2026-09-21 12:50 UTC y del OCR 06:06 UTC; "Monitor Volcanico VRP" 46 de 46 success y "Scraper OCR" 8 de 8 en las últimas ~4 h | `gh api repos/MendozaVolcanic/Mirova-v1/commits`, `curl -r 0-700` al CSV |
| Copia viva del OCR en el repo | `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` llega al 2026-09-21 06:06. La copia congelada `data/mirova_reference/registro_vrp_ocr.csv` sigue en 2026-03-28 (conocido, A17) | `head -2` de ambos |
| `isValidDetection`, `f5CoreMagnitude`, `esValorCensurado`, `_havKm`, `parseUtcMs` | texto idéntico en las vistas que las llevan | `comparar_helpers_js.py` |
| Constantes del núcleo y del tope | `F5_R_CORE_KM = 0.75`, `F5_BT_EXT_K = 295.0`, `PATH_D_CAP_MW = 5.0` iguales en las tres; `pipeline.profile.PATH_D_ONLY_CAP_MW = 5.0` | `grep -n "F5_R_CORE_KM =\|PATH_D_CAP_MW =" frontend/*.html` |
| Radio interno: 4 copias | coinciden en los 11 Tier A | `grep` de las tres vistas contra `yaml.safe_load(volcanoes.yaml)` |
| `_recent.json` | filtro de fecha puro, 100 días, no recalcula | `scripts/build_recent_json.py:41-52` |
| `.env` | ignorado, nunca commiteado | `git check-ignore -v .env; git ls-files .env; git log --all -- .env` |
| Ficha de VRP Chile en `MAPA_WORKSPACE.md` | al día (2026-09-15): ruta, repo, salida, credenciales con caducidad, cadencia real | `MAPA_WORKSPACE.md:150-158` |
| Evaluadores del A/B usan la magnitud de pantalla | `f5_core_vrp_mw` aparece en `_s143_evaluador/evaluar.py` y `_s146_ab_sin_test1/evaluar.py`; el predicado vía node en `_s143_evaluador` (sólo por `grep`, no leí la lógica) | `grep -ln` |

## 4. SIN VERIFICAR

- No corrí `tests/test_cadencia_cron_s133.py` ni ningún test (prohibido en esta auditoría).
- No abrí el tablero en un navegador: todo lo de pantalla sale de leer el JavaScript y de portar sus
  predicados a Python. El port de los filtros de artefacto no incluye `_mirova_confirmed`, así que el
  conteo de "publica" puede quedar corto en unos pocos records.
- No medí el salto visual de la adopción sobre los datos de los brazos del A/B (viven en ramas de datos
  que no corresponde bajar con el disco al 97 %).
- No verifiqué si `frontend/experimental/index.html` avisa que sus datos son de agosto.
- No busqué dónde se definen los umbrales de "nivel de actividad" que menciona la ficha.
- No revisé los pusher con `push-main` o retry: lo mide el guard G4 y no se podía correr.

## 5. Para otros frentes

- **F**: `data/experimental/*.json` congelado el 2026-08-25; `nrt.yml:192-200` y `:337`; el experimental
  escribe en `data/experimental_v2/`, que no se commitea.
- **C / D**: el evaluador del A/B debería contar aparte las pasadas que el tablero oculta por
  `isThermalArtifact` (`index.html:1236`) y la brecha mapa contra gráfico (G-08).
- **E**: `final_hotspot_source` vale `test1` y `eruption` en MODIS (21 y 706 de 736 en 30 días) y esos
  valores no están en la lista de "ancla honesta" de `index.html:2550`; en VIIRS 750, 946 de 1.476 records
  tienen la fuente vacía.
- **B**: `sync-mirova-csv` al 24 % de su cadencia; la copia congelada del OCR sigue en el repo.
- **A**: `CLAUDE.md` §Constraints (secretos) y `REGISTRO_CREDENCIALES.md:138` contradicen a sus propias
  correcciones.
