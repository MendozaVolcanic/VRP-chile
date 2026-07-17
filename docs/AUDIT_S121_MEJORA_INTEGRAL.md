# AUDIT S121 — Informe de mejora integral (auditoría multi-modelo, guía Fable 5)

> **Método**: 5 finders paralelos (sonnet, effort alto/medio) + verificadores frescos
> adversariales (principio 9 guía Fable 5) + síntesis Fable. 8 agentes, 0 errores,
> ~1.09M tokens de subagentes, 222 tool calls. Cada hallazgo lleva su evidencia;
> lo refutado se reporta como refutado (no se oculta). Regla de retención GitHub-vs-local:
> **conservadora** (decisión Nicolás): solo va a local lo que ninguna corrida futura de
> GitHub Actions o el frontend publicado puede necesitar.
> Workflow run: wf_2d469601-991 (journal en subagents/workflows/). Fecha: 2026-07-16.

---

## §0 Resumen ejecutivo (síntesis Fable — leer esto primero)

**Estado del proyecto: sano en lo científico, con deuda en infraestructura y display.** El
pipeline de detección NO tiene bugs nuevos que comprometan el número que MIROVA/OVDAS
mira (el dashboard usa `primary_cluster.vrp_mw`, regla A10, y ese camino está limpio).
Lo que la auditoría destapó se agrupa en tres frentes, por orden de urgencia:

**A. Riesgo operacional inmediato (no puede esperar):**
1. **Disco C: al 100 % (3.4 GB libres de 476 GB)** + 338 MB de `tmp_pack` huérfanos de un
   `git gc` interrumpido. Esto es la causa física de que los `push`/`pull` fallen hoy —
   no es solo "el repo es grande", es que **no hay espacio para que git opere**. §4.
2. **El modelo "toda la data JSON commiteada a main para siempre" no es sostenible**: el
   cron NRT genera ~45 commits/día a `data/`, el 84 % de los commits del repo. `.git` creció
   a 3.1 GB en 103 días y no desacelera. Decisión de arquitectura pendiente (Releases /
   repo satélite / branch orphan). §4.

**B. El fix del dashboard quedó a medias (mismo modo de falla en 2 de 3 vistas):**
3. **`mosaico.html` y `diario.html` NO recibieron el fix de peso** que sí apliqué a
   `index.html` — cargan los JSON completos (~171 MB / 13-17 MB) y reproducen el mismo
   dashboard vacío en red real. La regla del propio proyecto (S92 L5: un cambio de display
   se replica en las 3 vistas) se saltó. **Accionable ahora, mismo patrón ya escrito.** §3.

**C. Un falso negativo real + deuda de coherencia:**
4. **D12 — MODIS Láscar pierde ~70/79 alertas MIROVA-confirmadas** (verificado ✓). Es el
   espejo exacto del bug de "ancla honesta" que ya arreglamos para VIIRS375 en S98, nunca
   aplicado a MODIS: el cluster está en el cráter pero el píxel suelto más caliente cae en
   el Salar → se etiqueta `far` → el gate lo anula → el evento desaparece. **Un FN sobre
   señal confirmada es la categoría más grave del glosario.** Requiere ciclo A45. §2.
5. Varias incoherencias de docs que hacen que una sesión fría arranque con mapa viejo
   (GAP #A marcado "pendiente" cuando está cerrado; INDEX.md sin nada post-S105;
   BLOQUE_ARRANQUE_S120 congelado). Baratas de arreglar. §2-§3.

**Sobre qué eliminar (§5, tu pregunta central):** el clasificador + un verificador fresco
revisaron path por path. **Hallazgo clave: los ~45 subdirectorios A/B de `data/` (`_r2_*`,
`_d8_*`, `nsigma_*`, `mirova_equivalent_*_v1`...) son 100 % regenerables** — ningún test ni
workflow lee su contenido (los tests solo hacen `yaml.safe_load` del perfil, no abren los
JSON masivos). Son ~1.7 GB que pueden salir de GitHub sin perder reproducibilidad (el perfil
`.yaml` vivo + `run_pipeline.py` los recrea). **Guardarlos solo local no destruye nada** (el
pedido tuyo: en local no hay problema de espacio). Solo `data/mirova_equivalent/` +
`data/mirova/` + `data/mirova_reference/` son operacionales y quedan en GitHub.

**⚠️ Matiz que cambia la estrategia**: sacar los dirs del working tree con `git rm` **NO
reduce el `.git` de 3.1 GB** — los blobs quedan en la historia. Reducir `.git` de verdad
exige `git filter-repo` (reescribe la historia, destructivo, force-push) — operación aparte
que NO recomiendo sin tu decisión explícita. El adelgazamiento del working tree sí alivia
el disco C: y OneDrive de inmediato.

**Recomendación de secuencia** (detalle en §8): (1) liberar disco C: + `git gc` para
destrabar la red — es lo que desbloquea todo lo demás; (2) completar el fix del dashboard en
las 3 vistas (offline, lo hago ya); (3) decidir con vos la poda de data/ (tag defensivo A38)
y la arquitectura de data a futuro; (4) el FN de MODIS Láscar (D12) como próximo ciclo A45.

*(Refutaciones en §6 — lo que la verificación descartó es tan importante como lo que confirmó.)*

## §1 Bugs pendientes de código (finder: journal cacería + barrido)

### [MEDIA] Filtro H8 pixel-por-pixel (store.py) no limpia vrp_mw para MODIS/VIIRS750 — el VRP persistido puede seguir contaminado por el pixel lejano descartado
- **Evidencia**: pipeline/store.py:127-179 (_filter_pixels_by_distance solo recalcula record['vrp_mir_mw'], nunca record['vrp_mw']) + store.py:225-227 (el rescate 'if vrp_mir_mw in record and vrp_mw not in record' NO aplica a MODIS/VIIRS750 porque esos sensores YA traen 'vrp_mw' seteado río arriba: process_modis.py:1319, process_viirs_mod.py:1188) + store.py:227-324 (vrp_eruption = record.get('vrp_mw') se usa sin filtrar y termina en record['vrp_mw'] final, línea 324). Hallazgo original de la cacería S120 (journal wf_3c9b1cd4, agente a9eb2dda7a28f2fa7), CONFIRMADO por un agente verificador con test sintético reproducido (cráter 10 MW @1km + incendio 100 MW @30km → persistido vrp_mw=110 en vez de 10; caso todo-lejos → persistido vrp_mw=100 en vez de 0, peor que el comportamiento legado con el flag apagado). Revisé el HEAD actual (post PR #486 'batch B cacería'): el commit solo tocó store._save (escritura atómica), y esta función _filter_pixels_by_distance NO aparece en su diff — sigue exactamente igual. El flag que activa el filtro (enable_pixel_level_distance_filter: true) está ON en pipeline/profiles/mirova_equivalent.yaml:323, el perfil operacional.
- **Recomendación**: En store.py, después de _filter_pixels_by_distance, sincronizar explícitamente record['vrp_mw'] con el valor filtrado para TODOS los sensores (no solo cuando falta la key) — ej. 'if changed: record["vrp_mw"] = record["vrp_mir_mw"]' inmediatamente tras la llamada al filtro, antes de que vrp_eruption lo lea en la línea 227. Mitigante: el dashboard usa primary_cluster.vrp_mw (A10), no record.vrp_mw, así que el número visible en producción no está comprometido — pero cualquier audit/backfill que siga el schema documentado en store.py:206-211 sí lo está. Agregar un test unitario (caso partial + caso todo-lejos) antes del fix, siguiendo TDD.
- **Verificación**: sin verificación individual

### [MEDIA] Inputs de workflow_dispatch se interpolan sin comillas en bloques `run:` de 3 workflows activos — vector de inyección de comandos con acceso a secrets NASA
- **Evidencia**: .github/workflows/nrt.yml:156-160 (format('--date {0}', github.event.inputs.date) se expande crudo dentro del script bash que tiene EARTHDATA_TOKEN/USERNAME/PASSWORD en env, líneas 149-151) + patrón repetido en backfill-tier-a.yml (líneas ~57-61 y el matrix vía fromJSON(format(...)) ~línea 39) y reproc-s120-eq16-villarrica.yml (~líneas 45-50). Hallazgo original de la cacería (journal, agente a2358ccd51e182fde), severidad acotada por el propio verificador porque workflow_dispatch ya exige permiso de escritura al repo. Verificado en HEAD actual: ni PR #485 ni #486 tocaron estos 3 archivos en esos puntos (solo nrt.yml:289 git-add fue arreglado en #486); el patrón de interpolación cruda sigue idéntico hoy.
- **Recomendación**: Pasar los inputs vía 'env:' del step y referenciarlos en el script como variable de shell ($DATE_INPUT) en vez de interpolarlos directamente con ${{ github.event.inputs.X }} dentro de run:. Es el patrón estándar recomendado por GitHub para bloquear injection en workflow_dispatch/pull_request_target. Aplica a los 3 workflows. Bajo esfuerzo, sin cambio de comportamiento funcional.
- **Verificación**: sin verificación individual

### [BAJA] run_pipeline.py miente 'Cleaned up' cuando los 3 reintentos de borrado del tmp del volcán fallan — granules crudos se acumulan en disco sin aviso
- **Evidencia**: scripts/run_pipeline.py:326-339 — el print(f'  Cleaned up {volcano_tmp}') está FUERA del bucle for/try de 3 reintentos (líneas 332-338) y se ejecuta incondicionalmente aunque las 3 llamadas a shutil.rmtree levanten PermissionError. Hallazgo original de la cacería (journal, agente a39a5f40e9a0836f5), no verificado formalmente en el journal (el ciclo se cortó antes) pero confirmé leyendo el código actual: sigue exactamente igual tras PR #485/#486 (ninguno tocó esas líneas; el diff de run_pipeline.py en ambos PRs solo agregó la validación --start/--end y la llamada a reset_transient_breakers, ambas en otra sección del archivo).
- **Recomendación**: Mover el print dentro del for, solo tras el 'break' exitoso; y agregar un print/warning explícito si el bucle se agota sin éxito (ej. 'WARNING: no se pudo borrar {volcano_tmp} tras 3 intentos'). Relevante para reprocesos largos en la máquina de Nicolás con disco cerca del 98% (ver nota A44 del CLAUDE.md del proyecto).
- **Verificación**: sin verificación individual

### [BAJA] fetch.py todavía tiene un '→' Unicode en un mensaje runtime (_diag), no solo en comentarios — riesgo de crash cp1252 en corridas locales Windows
- **Evidencia**: pipeline/fetch.py:592-593 — f"... host={sorted(hosts)} → blip transitorio, reintentando" dentro de una llamada real a _diag() (no un comentario). PR #486 (batch B) sí limpió OTRA flecha en un mensaje runtime distinto (mencionado en su commit message: "+ flecha → en _diag runtime → '->' "), pero quedó al menos esta instancia sin tocar — confirmado con grep sobre el archivo actual: es el único '→' restante dentro de un string entre comillas (el resto son comentarios '#', que no imprimen en runtime).
- **Recomendación**: Reemplazar '→' por '->' en esa línea, igual que se hizo con la otra instancia en el mismo PR. Es exactamente el patrón de riesgo que el propio CLAUDE.md del proyecto documenta ('scripts Python que imprimen Unicode deben usar PYTHONIOENCODING=utf-8'); ya estaba marcado como diferido en el bloque S120 §3, sigue pendiente. Bajo esfuerzo (1 línea).
- **Verificación**: sin verificación individual

## §2 Ideas propuestas nunca aplicadas (rankeadas)

### [ALTA valor / esfuerzo medio] Backlog Data Integrity (S81) — 6 items de higiene de datos nunca ejecutados, incluye invariante físicamente imposible en 228 records
- **Evidencia**: tasks/backlog_data_integrity_session.md (creado S81, 2026-05-26, último commit al archivo esa misma fecha — 0 commits desde entonces en 40 sesiones). Items confirmados: (1) 15 filas duplicadas PCC con vrp divergente [113.84,309.99,113.84] mismo evento; (2) `pipeline/store.py::append_record` (línea 182, verificado — no existe dedup key por (datetime_utc, sensor, granule)); (3) 2117 records (16% del corpus) con vrp_mw=0 sin razón etiquetada (`vrp_zero_reason` no existe, grep vacío en pipeline/*.py); (4) 228 records con `n_hotspots_clustered > n_anomalous_pixels` (físicamente imposible, concentrado en PP+Lastarria); (5) outlier σ_bg=149.18K en Lastarria (rango físico esperado 3-15K, sin guard); (6) gaps schema diag_* en 10/13207 records.
- **Recomendación**: Abrir la sesión dedicada que Nicolás pidió explícitamente en S81 ("recuerda la sesión de data integrity"). Los items 1, 2 y 5 son acotados (15min-30min c/u con tag defensivo A45) y cierran vectores de corrupción silenciosa del dataset que consume el dashboard operacional; los items 3-4 son more investigativos (2-3h) pero afectan directamente la interpretación de recall/magnitud que usa Nicolás para decidir alertas.
- **Verificación**: **REFUTADO** — El archivo backlog es real y abandonado (git log --follow: 1 commit S81, 0 desde entonces), pero 3 de los 6 items citados como evidencia son obsoletos/falsos al verificar contra data/mirova_equivalent/*.json actual (43618 records, no 13207): (1) 0 duplicados PCC hoy (era 15); (2) la afirmación 'no existe dedup key' es falsa — pipeline/store.py:515-518 ya tiene dedup (datetime_utc,sensor) con overwrite/upgrade; (5) el outlier sigma_bg=149.18K citado puntualmente en Lastarria 2026-04-23 hoy vale 3.562K, ya no existe. Los items 3 y 4 sí siguen vigentes (vrp_zero_reason no existe; n_hotspots_clustered>n_anomalous_pixels ahora son 8825 records, no 228 — más grave, con causa raíz distinta: sobreescritura cross-path en process_modis.py:1264, no bug de clustering). Ejecutar el backlog tal cual está escrito desperdiciaría esfuerzo en ítems ya resueltos; se necesita re-auditoría fresca, no el backlog literal.

### [ALTA valor / esfuerzo medio] D12 — MODIS Láscar pierde ~70/79 alertas MIROVA-confirmadas (falso negativo, no falso positivo)
- **Evidencia**: docs/MIROVA_DIVERGENCES.md §D12 (AUDIT_S106 P1.1, marcada ABIERTA, sin entrada de cierre posterior en el doc). El `primary_cluster` MODIS SÍ está en el cráter (mediana 1.46 km, ≈MIROVA 1.41 km) pero el píxel suelto más caliente cae en el Salar de Atacama (16-32 km) → `distance_class='far'` → el gate `mirovaEqVrp`/`audit_metrics.py:79` lo anula → el evento real desaparece del dashboard. Es el espejo MODIS exacto del bug que la 'ancla honesta' ya resolvió para VIIRS375 (S98), pero nunca se aplicó a MODIS.
- **Recomendación**: FN sobre señal confirmada es la categoría más grave del glosario del proyecto (peor que un FP). Ejecutar el fix ya identificado en el doc: derivar `distance_class` MODIS desde `primary_cluster` (igual que se hizo para VIIRS) en vez del píxel suelto más caliente, con reproc histórico Láscar dirigido. Sigue el ciclo A45 (tag defensivo + confirmación explícita antes de tocar pipeline).
- **Verificación**: verificado por subagente fresco ✓

### [MEDIA valor / esfuerzo medio] D2 — Cobertura del CSV ground truth MIROVA incompleta (~70-80% en VIIRS) sesga todas las métricas de recall/precision
- **Evidencia**: docs/MIROVA_DIVERGENCES.md §D2. MODIS ~100% cobertura pero VIIRS 375m/750m solo ~70-80% scrapeado de latest.php. Sección "Pendiente" explícita: re-scrapear con script Mirova-v1 cubriendo gaps temporales + comparar timestamps NRT actuales vs CSV para identificar pasadas faltantes. Nunca ejecutado (sin entrada de resolución posterior en el catálogo).
- **Recomendación**: Cerrar el gap de scraping en Mirova-v1 antes de citar cifras de recall/precision VIIRS en el paper (Volcanica). Sin esto, cualquier 'FP nuestro' en VIIRS puede ser en realidad un TP que MIROVA sí detectó pero el scraper no capturó — y el recall reportado puede estar subestimado.
- **Verificación**: sin verificación individual

### [MEDIA valor / esfuerzo medio] AUDIT_S119 §8 — 8 de 10 mejoras de auditoría propuestas por Nicolás siguen sin construirse (solo el auto-audit semanal se hizo)
- **Evidencia**: docs/AUDIT_S119.md §8, tabla etapa-por-etapa. Filas sin implementar: cobertura fetch (pasadas esperadas vs procesadas por plataforma — 'un sensor que desaparece en silencio es invisible hasta que cae el recall'), latencia NRT (lag pasada→dashboard, el valor operacional real para OVDAS), validación de schema (jsonschema como test, protege contra el patrón A46 de campo asimétrico), smoke-test CI de frontend (una regresión de display como la de S115 datetime espera a que alguien mire), suite en CI Windows (hoy solo se corre local), linkcheck de docs, checklist trimestral de seguridad (PAT sin rotar, .netrc inválido A71), tracking de duración NRT por volcán (creep silencioso hacia el timeout de 50 min). MEMORY.md confirma que solo la fila 3 (auto-audit semanal) quedó LIVE en S120.
- **Recomendación**: Priorizar 2 filas de mayor apalancamiento operacional: (a) validación de schema jsonschema como test — barata y previene silenciosamente el próximo bug tipo A46; (b) tracking de duración NRT por volcán — barato (parsear duración de steps ya loggeados) y da alerta temprana antes de que un timeout tumbe el cron. El resto puede ir a un backlog sin urgencia.
- **Verificación**: sin verificación individual

### [MEDIA valor / esfuerzo bajo] data/ tiene 2.0 GB de los cuales solo ~180 MB es operacional — plan de poda ya diseñado en S80 nunca ejecutado
- **Evidencia**: docs/DATA_SUBDIRS_INVENTORY_S80.md: inventario clasificatorio completo (regla A38 cumplida) de subdirs experimentales (`_r2_*` 109MB, `_d8_*` 90MB, `_h_*`/`_p3_*`/`_mirova_literal` 130MB) con recomendación explícita 'archivable' y comando de poda ya redactado (tag defensivo + tar backup + rm -rf). La decisión S80 fue diferir a 'S100 para reevaluar' (regla M4) — nunca se ejecutó. `du -sh data/*` hoy confirma 2.0 GB total con `mirova_equivalent_pre_s27` (195M), 6 variantes `mirova_equivalent_*_v1` de A/B tests ya cerrados (32-78M c/u), `nsigma_mir_5`/`_12` (110M) y más de una decena de subdirs `_drift*` de 28M c/u — todos de experimentos ya resueltos/adoptados según MIROVA_DIVERGENCES.md.
- **Recomendación**: Ejecutar el plan ya escrito en DATA_SUBDIRS_INVENTORY_S80.md: tag `pre-s121-data-prune` + backup tar a OneDrive/Drive + `rm -rf` de los subdirs marcados 'archivable'/'validado, ya consolidado en experiments/*_results.json'. Mantener intocados `data/mirova_equivalent/` y `data/mirova/` (regla explícita del doc). Reduce el repo en >1 GB con riesgo bajo porque ya existe el inventario clasificatorio.
- **Verificación**: sin verificación individual

### [MEDIA valor / esfuerzo medio] EXT-8 AVTOD (Reath 2019) — ground truth independiente de MIROVA, ya descargado, nunca integrado al workflow de validación
- **Evidencia**: docs/BEYOND_MIROVA_EXTENSIONS.md §4/§7: catálogo manual ASTER 90m de 330 volcanes latinoamericanos 2000-2017 (Reath, Pritchard, Pieri, **Coppola**, Moruzzi, Alcott 2019), ya validado cross-MIROVA por sus propios autores, cubre todos los vols Tier A chilenos. Marcado explícitamente '**TOP PRIORITY**' y 'más crítico para paper publication' en la tabla de prioridades post-clon-literal (§7, ítem 1). PDF ya en `documentacion/AVTOD_Reath_2019.pdf`. Nunca integrado a ningún script de validación.
- **Recomendación**: Dado que el clon literal ya está cerrado (S114-S119, fiel a Coppola confirmado) y hay un paper en preparación para Volcanica (según MEMORY.md S120), este es el momento indicado: usar AVTOD como segunda fuente de verdad independiente de MIROVA OSF para el paper — reduce la dependencia de una sola fuente de ground truth y da un argumento de robustez metodológica citable.
- **Verificación**: sin verificación individual

### [MEDIA valor / esfuerzo bajo] Zonas 'beyond MIROVA' (display experimental) y verificación cráter El Agrio Copahue — pendientes de revisión de Nicolás en navegador desde S119/S120
- **Evidencia**: tasks/BLOQUE_ARRANQUE_S120.md §1, ítems 1-2: 'Eje 3.1/3.2 — beyond-mirova.html en navegador real: validar las 3 pestañas + afinar zonas 2a por volcán (criterio geológico; hoy solo PCC documentado)' y 'WATCH Copahue: rumbo S ~1.2-1.3 km del pc VIIRS375 (n=110, estable) — cotejar posición cráter El Agrio vs vent configurado'. Explícitamente marcados 'no delegables' (requieren juicio geológico de Nicolás), y no aparecen resueltos en los commits S120 revisados (el trabajo S120 fue Eq.16, backfill, auto-audit, higiene — no estas dos tareas).
- **Recomendación**: Bloquear 30-45 min con Nicolás frente al dashboard (`beyond-mirova.html`) para: (a) validar visualmente las 3 pestañas, (b) definir criterio geológico de zonas 2a para los volcanes restantes (hoy solo PCC tiene zona documentada), (c) cotejar si el sesgo sistemático 1.2-1.3 km al S en Copahue corresponde al cráter El Agrio real o es un artefacto de anclaje sin diagnosticar.
- **Verificación**: sin verificación individual

### [BAJA valor / esfuerzo bajo] PDF duplicado exacto en documentacion/ (26 MB desperdiciados, mismo archivo con 2 nombres)
- **Evidencia**: Verificado con md5sum: `documentacion/Aveni_2024_TIRVolcH_RSE.pdf` y `documentacion/1-s2.0-S0034425724004140-main.pdf` tienen hash MD5 idéntico `ab8addd8fd284cccc195dbbb1e8656ae` (26 MB c/u). BEYOND_MIROVA_EXTENSIONS.md §7 confirma que es el mismo paper Aveni 2024 TIRVolcH renombrado, el original nunca se borró.
- **Recomendación**: Borrar `1-s2.0-S0034425724004140-main.pdf` (mantener el nombre legible `Aveni_2024_TIRVolcH_RSE.pdf`), 5 minutos. Aporta directamente al objetivo explícito de reducir peso del repo (documentacion/ pesa 609 MB).
- **Verificación**: sin verificación individual

### [BAJA valor / esfuerzo bajo] experiments/ 458 MB — 3 subdirs de sesiones puntuales (S98/S104/S109) concentran 366 MB sin archivar
- **Evidencia**: `du -sh experiments/* | sort -rh`: `_s109_modis_mag` 163M, `_s98_anchor` 156M, `_s104_roi_probe` 47M = 366 MB de 458 MB totales. Estas son investigaciones read-only ya cerradas y documentadas (S98 'RESUELTO' en MIROVA_DIVERGENCES.md, S104/S109 cerrados con resultados consolidados en docs). El patrón de archivado usado en S80 para R2/D8 (DATA_SUBDIRS_INVENTORY_S80.md) nunca se extendió a estas carpetas más recientes.
- **Recomendación**: Mismo tratamiento que el ítem anterior: verificar que los resultados numéricos estén consolidados en un .md/.json committeado (parecen estarlo, dado que las secciones S98/S104/S109 de MIROVA_DIVERGENCES.md citan cifras concretas), luego mover los raster/JSON crudos intermedios fuera del repo (tar + backup externo) y dejar solo el resultado consolidado.
- **Verificación**: sin verificación individual

### [BAJA valor / esfuerzo bajo] Documentación contradictoria sobre GAP #A — CLAUDE.md/MISSION.md dicen 'pendiente', MIROVA_DIVERGENCES.md/AUDIT_S114 dicen 'resuelto S115 (mislabel)'
- **Evidencia**: CLAUDE.md líneas 113-114 y docs/MISSION.md línea 94 afirman 'único gap de fidelidad literal pendiente: GAP #A ... flag OFF — backlog'. Pero docs/MIROVA_DIVERGENCES.md línea 1292 y docs/AUDIT_S114_PARITY_BY_SENSOR.md línea 232 dicen explícitamente 'GAP #A RESUELTO S115 = mislabel (no es gap)'. AUDIT_S119.md §7 (fecha posterior a S115) todavía lo lista como candidato #2 de trabajo pendiente — la inconsistencia sobrevivió a 2 auditorías integrales sin corregirse.
- **Recomendación**: Actualizar CLAUDE.md y MISSION.md para reflejar el cierre S115 (mislabel, no gap real) y eliminarlo de cualquier lista de 'próximos pasos'. Riesgo si no se corrige: una sesión futura fría lee CLAUDE.md/MISSION.md primero (regla de arranque del propio proyecto) y relanza una investigación ya cerrada — exactamente el anti-patrón que la regla A50 busca evitar.
- **Verificación**: sin verificación individual

## §3 Coherencia docs/frontend

### [ALTA] tasks/BLOQUE_ARRANQUE_S120.md quedó congelado en el cierre de S119 y ya no refleja el estado real del repo
- **Evidencia**: El archivo (leído completo) dice textualmente en §1 que persisten como pendientes-para-Nicolás cosas que YA se hicieron y están commiteadas en `git log --oneline`: 'Eje 7 — priorizar: backfill VIIRS / Panel 2b Eq.16 / batch higiene' — pero `git log` muestra 'gate P0/P1/P2 backfill APROBADO' (commits c6a1f7e4, 1311f640), 'Panel 2b Eq.16 LIVE' (7116c16a) y 'parametrizar workflow reproc Eq.16 por volcán' (f44cfbdc) ya ejecutados. También dice 'suite 796 passed' (línea 62) mientras `pytest --collect-only` en HEAD actual da 806 tests. Encima faltan 21 commits `feat/fix/data(s120)` posteriores (batch A #485, batch B #486, hotfix #483, auto-audit semanal, 30+ commits de backfill P1-P4) que no aparecen mencionados en absoluto. No existe `tasks/BLOQUE_ARRANQUE_S121.md`, así que cualquier sesión nueva que siga la regla obligatoria del CLAUDE.md ('leer bloque de arranque antes de empezar') parte de un mapa desactualizado en ~1 sesión completa de trabajo.
- **Recomendación**: Al cerrar la sesión S120 actual, generar `tasks/BLOQUE_ARRANQUE_S121.md` con el estado real (git log + MEMORY.md ya lo tienen sintetizado) y no dejar que el bloque de arranque quede como única fuente de verdad desactualizada por más de 1 sesión. Considerar automatizar un chequeo (script) que compare la fecha/hash del último commit contra la fecha citada en el bloque de arranque más reciente y alerte si diverge en más de N commits.

### [MEDIA] docs/INDEX.md — la tabla "CANÓNICOS" no incluye ningún doc posterior a S105; el audit más reciente real (AUDIT_S119.md) no figura
- **Evidencia**: docs/INDEX.md línea 11 declara: `AUDIT_S105.md | Última auditoría A51 (vigente) | S105` como el audit canónico vigente. Pero `ls docs/AUDIT_S1*.md` muestra 19 docs de auditoría posteriores (S106, S108×3, S109×2, S110×2, S111, S112, S114, S116×4, S118, **S119**) que no están en la tabla CANÓNICOS ni en HISTÓRICO — no existen en el índice en absoluto. MEMORY.md (fuente de arranque de sesión) apunta a `docs/AUDIT_S119.md` como "última auditoría", contradiciendo directamente lo que dice el índice maestro del propio repo.
- **Recomendación**: Actualizar docs/INDEX.md: mover AUDIT_S105.md a HISTÓRICO-CERRADO, agregar AUDIT_S119.md (y S116 que es el 'ciclo A51' más reciente completo) a CANÓNICOS, y clasificar los 14 docs S106-S118 sueltos que hoy no aparecen en ninguna tabla (quedan invisibles para cualquiera que confíe en el índice).

### [ALTA] mosaico.html no tiene el fix de dashboard liviano (S120, e90f6499) — carga los 11 JSON completos Tier A (~171 MB) en paralelo en cada carga de página
- **Evidencia**: El commit e90f6499 (rama actual `s120-dashboard-lightweight`, HEAD) documenta el problema en producción: 'el backfill histórico llevó los 11 JSON Tier A a 13-17 MB c/u (~171 MB)... un solo fetch de 16 MB timeoutea >30s → mapa y tabla vacíos'. El fix (`_recent.json` de 100 días + `build_recent_json.py` + `pages-deploy.yml`) SOLO tocó `frontend/index.html` (diff: `frontend/index.html | 36 ++++++++++--`). `frontend/mosaico.html:392-402` (`loadVolcano`) sigue haciendo `fetchJSON(BASE_PATH + "data/mirova_equivalent/" + v.name + ".json")` sin sufijo `_recent`, y `mosaico.html:681,689` ejecuta `Promise.all(TIER_A.map(v => loadVolcano(v)))` — los 11 volcanes completos EN PARALELO en cada carga de `mosaico.html`, que es justamente la vista overview de 48h/30d (el caso de uso más frecuente/liviano en teoría). Este es el mismo modo de falla exacto que motivó el fix de index.html, sin resolver aquí.
- **Recomendación**: Aplicar el mismo patrón `_recent.json` a mosaico.html (que además necesita menos historia que index.html, dado que solo muestra 48h/30d) y a diario.html (fetch de un volcán completo a la vez, igual de vulnerable a timeout en redes lentas). Reusar `build_recent_json.py` ya existente — es cuestión de apuntar el fetch al artefacto `_recent` con fallback al completo, como ya se hizo en index.html.

### [MEDIA] diario.html carga el JSON histórico completo por volcán (13-17 MB) — mismo riesgo de timeout que index.html tenía antes del fix S120, sin mitigar
- **Evidencia**: `frontend/diario.html:176`: `const r = await fetch(BASE_PATH + "data/mirova_equivalent/" + encodeURIComponent(volc.name) + ".json")` — fetch directo del JSON completo, sin `_recent` ni ventana. El commit e90f6499 solo modificó index.html. diario.html es la vista de tendencia 90 días/volcán — un usuario que la abre para un volcán con backfill completo (p.ej. Villarrica, 16 MB) puede reproducir el mismo cuadro vacío que motivó el fix en index.html.
- **Recomendación**: Mismo fix que index.html/mosaico.html: usar `_recent.json` (100 días cubre de sobra la ventana de 90 días que diario.html necesita por defecto) con fallback al completo si `_recent` da 404.

### [MEDIA] diario.html — mirovaEqVrp() no aplica el sanity cap de 50.000 MW en el camino sin primary_cluster (records pre-S27), a diferencia de index.html y mosaico.html
- **Evidencia**: `frontend/diario.html:237-238`: `const pc = r.primary_cluster; if (!pc) return r.vrp_mw ?? 0;` — sin cap. En cambio `frontend/index.html:975-981` y `frontend/mosaico.html:247-249` SÍ aplican `return vfb > 50000 ? 0 : vfb` en la misma rama, y el comentario de index.html línea 977 dice explícitamente 'M1 (S76 audit): paridad sanity cap con diario.html:237' — afirmando una paridad que en el código real de diario.html NO existe (línea 237 solo declara `const pc`, no el cap). Esto es exactamente la regresión que la regla del proyecto (S92 L5, 'un cambio de display/filtro debe replicarse en las 3 vistas') busca prevenir; en este caso el cap SÍ se agregó a 2 de 3 vistas y el comentario de paridad describe una realidad falsa.
- **Recomendación**: Agregar el mismo cap (`vfb > 50000 ? 0 : vfb`) a diario.html:238, y corregir el comentario de index.html:977 para que apunte a la línea correcta una vez sincronizado. Bajo riesgo de impacto real hoy (records pre-S27 son fósiles), pero es la clase de divergencia silenciosa que el proyecto ya documentó como fuente de bugs (A46/S92 L5).

### [MEDIA] beyond-mirova.html (deployado en main/producción) quedó con el Panel 2b "Eq.16" hardcodeado a Villarrica, mientras la generalización multi-volcán existe pero está varada en una rama sin mergear
- **Evidencia**: `git show main:frontend/experimental/beyond-mirova.html` línea 373 tiene `fetch(`${BASE_PATH}data/_s99_test1_eq16/Villarrica.json`)` hardcodeado y el mensaje de error (línea 374) sugiere correr `reproc-s120-eq16-villarrica` (workflow single-volcano). El commit `c4588558` ('Panel 2b Eq.16 multi-volcán (selector + referencia OCR por volcán)') que reemplaza esto por un selector con `EQ16_VOLC` existe en el repo pero `git merge-base --is-ancestor c4588558 origin/main` = no — vive únicamente en la rama `s120-eq16-multivol`, nunca mergeada. Tampoco está en la rama actual `s120-dashboard-lightweight`. El propio workflow que generaliza el reproc por volcán (f44cfbdc, 'era Villarrica-only') SÍ está en main, pero el frontend que lo consume sigue apuntando solo a Villarrica — trabajo a medio camino entre dos ramas paralelas.
- **Recomendación**: Mergear `s120-eq16-multivol` a main (o rebasear sobre el HEAD actual y abrir PR) para que el Panel 2b consuma los reprocs de PCC/Chaitén que el workflow ya generaliza. Antes de mergear, correr `git log main..s120-eq16-multivol` para confirmar que no hay más trabajo huérfano en esa rama.

### [MEDIA] Múltiples ramas locales S120 en paralelo sin consolidar aumentan el riesgo de que trabajo ya hecho se pierda o se re-haga
- **Evidencia**: `git branch -a` sobre la sesión mostró al menos 2 ramas S120 activas y divergentes de main: `s120-dashboard-lightweight` (HEAD actual, con el fix de peso) y `s120-eq16-multivol` (con la generalización del Panel 2b), ninguna conteniendo el trabajo de la otra. Esto contradice el patrón que el propio proyecto documenta como bueno (A44/A45: ciclo tag defensivo → PR → merge) si esas ramas quedan abiertas sin PR. No verificado si hay más ramas S120 sueltas — no se corrió `git branch -a` completo con fecha de último commit por rama.
- **Recomendación**: Antes de cerrar S120, correr `git branch -a --sort=-committerdate` y para cada rama `s120-*` decidir: mergear a main (con PR) o descartar explícitamente documentando por qué. No dejar ramas de feature completas sin mergear al cierre de sesión — regla A53 (cap PRs/sesión) ya empuja a mergear seguido; el gap acá es que el merge no se hizo para 2 features terminadas.

## §4 Infraestructura y ecosistema

### [ALTA] Disco C: al 100% (3.4 GB libres de 476 GB) — riesgo operacional inmediato, no solo de GitHub
- **Evidencia**: `df -h .` → `C: 476G 473G usados 3.4G disponibles 100%`. El repo (.git 3.1 GB + data/ 2.0 GB + documentacion/ 609 MB + experiments/ 458 MB ≈ 4.2 GB) vive dentro de este mismo disco casi lleno, compitiendo con OneDrive sync, Windows, y cualquier build. `git count-objects -vH` ya muestra 4 packs temporales corruptos/huérfanos sin limpiar (`tmp_pack_iQF18N` = 334.9 MB, total garbage 338.23 MiB) — consistente con un `git gc`/repack interrumpido, muy probablemente por falta de espacio en disco o por un lock de OneDrive a mitad de escritura.
- **Recomendación**: Liberar espacio en C: antes de cualquier otra acción (mover documentacion/ 609MB y experiments/ 458MB fuera de OneDrive-sync activo, o a un volumen con más margen). Después correr `git gc --prune=now` para eliminar los 338 MB de tmp_pack huérfanos (verificar antes que no estén en uso: `ls -la .git/objects/pack/tmp_pack_*`). Sin este espacio libre, git gc/fsck y hasta un `git pull` grande pueden fallar a mitad de camino.
- **Verificación**: verificado por subagente fresco ✓

### [ALTA] data/ crece a razón de 5037/6012 commits (83.8%) del repo total desde que existe (Apr-04→Jul-16, ~103 días); .git ya es 3.1 GB con solo 294.7 MB en objetos sueltos y 2.41 GB empaquetados
- **Evidencia**: `git rev-list --count HEAD`=6012; `git log --oneline -- data/`=5037. Ritmo reciente: 204 commits a data/ en 7 días, 1340 en 30 días (≈44.7/día). Un commit típico del cron NRT (`284eafc0`, 'NRT update Lastarria') agrega 849 líneas en 2 archivos JSON; el sync-bot CSV (`24a71389`) toca 22 JSONs con diffs mínimos cada ~2h. A ese ritmo el repo pasó de 0 a 3.1 GB de .git en 103 días ≈ 30 MB/día promedio histórico, con el cron NRT (cada 2h, 11 volcanes Tier A) como motor dominante — no hay señal de que vaya a desacelerar.
- **Recomendación**: El modelo 'toda la data JSON committeada a main, para siempre' no es sostenible al ritmo NRT 2h. Opciones (evaluar con Nicolás, no decidir unilateral por A45/A49-A53): (a) **GitHub Releases periódicos** para snapshots data/mirova_equivalent/ + purgar historia vieja del working tree pero mantener el asset descargable — bajo esfuerzo, rompe `git blame` de data histórica; (b) **repo satélite `VRP-chile-data`** con push automático del bot y submodule/subtree en el repo de código — separa el ciclo de vida del pipeline (pocos commits) de la data (miles), pero exige reconfigurar 9 workflows; (c) **branch orphan `data-archive`** con squash periódico de la historia de data/ + shallow clone en checkout de nrt.yml — mantiene todo en un repo pero acota el crecimiento de `main`. Ninguna opción es trivial: decidir antes de que .git duplique de tamaño otra vez.
- **Verificación**: sin verificación individual

### [ALTA] ../mirova-tif-archive lleva 57 días sin poll (último commit 2026-05-20), degrada el ground truth espacial TIF para auditorías
- **Evidencia**: `git log -1` en `../mirova-tif-archive` → commit `07412357`, 2026-05-20 12:51:36 UTC, 'poll: 46 new MIROVA snapshot(s)'. Hoy es 2026-07-16 → 57 días de brecha. `data/tif/Villarrica/` confirma: el archivo más reciente en el listado es `20260520_...VIIRS750_lm.tif` (May 20). El repo pesa 5.4 GB en disco (`du -sh .` = 5.4G).
- **Recomendación**: Investigar por qué el poller de mirova-tif-archive dejó de correr (¿cron GH Actions deshabilitado, secret expirado, cambio de URL de mirovaweb.it?) — no verificado el motivo, requiere revisar `.github/workflows/` de ese repo hermano. Sin TIF fresco, cualquier verificación espacial tipo R2/A61 (comparar centroide nuestro vs radiancia local MIROVA) queda ciega para eventos posteriores a mayo. Priorizar antes de confiar en el auto-audit semanal para volcanes con actividad reciente (post-mayo).
- **Verificación**: **REFUTADO** — REFUTADO por evidencia directa contra el remoto real. `gh run list --repo MendozaVolcanic/mirova-tif-archive` muestra el workflow 'Poll MIROVA TIF/KMZ' corriendo cada 5 minutos, runs exitosos hasta el momento de la verificación (2026-07-17T02:35 UTC, es decir HOY). `gh api .../commits` confirma commits recientes: 2026-07-17, 2026-07-14, 2026-07-12, 2026-07-10, 2026-07-08 — nada de brecha de 57 días. El hallazgo citó únicamente el clon LOCAL (`git log -1` dentro de `../mirova-tif-archive`), que sí está parado en 2026-05-20 — pero eso es un clon desactualizado, no el estado real del poller. Más aún: **este exacto diagnóstico ya fue hecho y cerrado en la sesión S120** (2026-07-01, hace 15 días), documentado literalmente en `tasks/BLOQUE_ARRANQUE_S120.md` líneas 47-54: 'el poll TIF NUNCA estuvo estancado — el repo remoto mirova-tif-archive está verde (runs cada 5 min...). Era el clon LOCAL desactualizado desde 2026-05-20 (patrón A25: repo 9.2 GB, git fetch local timeoutea)'. La solución ya prescrita es no hacer `git pull` pelado sino bajar TIFs puntuales vía raw.githubusercontent.com. El hallazgo del otro agente es una re-derivación de un problema ya diagnosticado y resuelto — no debe reabrirse como acción nueva (equivalente a anti-A8/A50: verificar contra origin/main y docs antes de etiquetar 'stale').

### [BAJA] Ground truth CSV (mirova_v1_snapshot) SÍ está fresco — no es el riesgo que parecía
- **Evidencia**: `git log -1 -- data/mirova_reference/mirova_v1_snapshot/` → commit `1a247453`, 2026-07-13, 'audit(auto): paridad semanal vs MIROVA (auto-audit S120)'. `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` en disco tienen mtime 2026-07-15 13:38 (sincronizado por el mismo job que corrió el auto-audit semanal). El sync-bot `vrp-mirova-sync-bot` corre cada ~2h regenerando los JSON per-volcano desde este CSV (ver commits `24a71389`, `575581cb`, `deb700f0`, todos julio 15).
- **Recomendación**: Ninguna acción requerida sobre este eje — está sano. Sí vale monitorear que el cron `sync-mirova-csv.yml` (que trae este CSV) no dependa silenciosamente del mismo host caído que mirova-tif-archive, ya que ambos scrapean mirovaweb.it.
- **Verificación**: sin verificación individual

### [MEDIA] `nrt.yml` (cron principal, cada 2h) no tiene `concurrency:` guard a nivel workflow
- **Evidencia**: `grep concurrency .github/workflows/nrt.yml` → 0 matches. El workflow corre `schedule: cron "0 */2 * * *"` con matrix `max-parallel: 8` sobre volcanes, y cada step de descarga tiene `timeout-minutes: 50-60`. Si un run tarda más de 2h (posible bajo degradación NASA LANCE, A64), el siguiente disparo del cron puede solaparse con el anterior y ambos escribir a los mismos `data/mirova_equivalent/*.json`, exactamente el patrón de race condition que A47 (S77) ya documentó como causa de corrupción JSON en reprocesos locales paralelos.
- **Recomendación**: Agregar `concurrency: {group: nrt-cron, cancel-in-progress: false}` a nivel workflow en `nrt.yml`, igual al patrón ya usado en `sync-mirova-csv.yml` y `pages-deploy.yml`. Con `cancel-in-progress: false` la segunda invocación simplemente espera en cola en vez de correr en paralelo — cero pérdida de cobertura NRT, elimina el riesgo de race.
- **Verificación**: sin verificación individual

### [BAJA] `nrt-retry.yml` no tiene `timeout-minutes` en el job
- **Evidencia**: `grep timeout-minutes .github/workflows/nrt-retry.yml` → 0 matches. El job hace varias llamadas `gh api`/`gh run list` a la API de GitHub sin límite de tiempo explícito; por default GitHub Actions aplica 360 min (6h) hard limit, muy por encima de lo que este job (inspección + eventual `gh workflow run`) necesita.
- **Recomendación**: Agregar `timeout-minutes: 10` al job `check-and-retry` — es una llamada API rápida, no hay razón para dejarlo expuesto a 6h de cómputo gratuito consumido en un hang silencioso de `gh api`.
- **Verificación**: sin verificación individual

### [BAJA] `backfill-tier-a.yml` y `reproc-s120-eq16-villarrica.yml` (reprocesos manuales `workflow_dispatch`) no tienen `concurrency:` guard
- **Evidencia**: `grep concurrency` sobre ambos archivos → 0 matches; ambos son `workflow_dispatch`-only (sin cron), y ambos escriben presumiblemente sobre `data/mirova_equivalent/` o subcarpetas del mismo árbol que toca el cron NRT.
- **Recomendación**: Si algún día se disparan dos runs manuales del mismo workflow (o uno manual mientras el NRT cron está en curso sobre el mismo volcán), aplica el mismo riesgo A47. Agregar `concurrency: {group: <nombre-workflow>-${{ github.event.inputs.volcano || 'all' }}, cancel-in-progress: false}` es barato y cierra el gap; prioridad baja porque estos workflows los dispara Claude/Nicolás manualmente y ya hay disciplina A45 de no lanzar en paralelo.
- **Verificación**: sin verificación individual

### [BAJA] Sin `echo`/`print` de secrets detectado en los 9 workflows activos — eje de seguridad sano
- **Evidencia**: `grep -n "echo.*secrets\." .github/workflows/*.yml` sobre los 9 archivos (`audit-weekly.yml`, `backfill-tier-a.yml`, `nrt-healthcheck.yml`, `nrt-monitor.yml`, `nrt-retry.yml`, `nrt.yml`, `pages-deploy.yml`, `reproc-s120-eq16-villarrica.yml`, `sync-mirova-csv.yml`) → 0 matches. `EARTHDATA_PASSWORD`/`EARTHDATA_USERNAME` solo aparecen como `env:` inyectado a pasos, nunca impreso.
- **Recomendación**: Ninguna acción — mantener la disciplina al agregar nuevos workflows (nunca `echo "${{ secrets.X }}"` para debug, ni siquiera temporalmente, porque GitHub enmascara en logs pero no siempre en step summaries).
- **Verificación**: sin verificación individual

### [MEDIA] data/mirova_equivalent_pre_s27/ (195 MB) y ~10 subcarpetas experimentales `data/mirova_equivalent_*` (78+78+78+78+55+55+35+35+32+32 MB ≈ 556 MB) son snapshots de A/B tests históricos ya cerrados, no operacionales
- **Evidencia**: `du -sh data/*` ordenado: `mirova_equivalent_pre_s27` 195M, `mirova_equivalent` (operacional, live) 180M, `mirova_reference` 99M, luego `mirova_equivalent_test1pix_filter/_disabled`, `_lbg_global`, `_mirova_literal`, `nsigma_mir_5/_12`, `mirova_equivalent_path_d_cap_v1/_atm_gate_v1/_bt_path_on_v1`, `_unsuitable_only_v1/_filters_v1`, todas 32-78 MB cada una. Estos corresponden a perfiles A/B con `data_subdir` aislado del patrón documentado en CLAUDE.md ('clonar reproc-ab-*.yml... con 2 profiles _feature_{enabled,disabled} con data_subdir aislado') de experimentos S24-S102 ya decididos (adoptados o descartados) según MEMORY.md.
- **Recomendación**: Confirmar con `git log -5 -- data/mirova_equivalent_pre_s27/` y los demás directorios que corresponden a experimentos ya cerrados (no en uso por ningún workflow activo — verificar con `grep -rl <nombre_subdir> .github/workflows/ pipeline/profiles/`), y si es así, moverlos a un tag/release defensivo (patrón A38: `git tag pre-cleanup-data-experiments` + `git push --tags`) antes de `git rm -r` esas ~750 MB. Esto es candidato directo para reducir el `data/` de 2.0 GB a los ~180 MB operacionales que menciona el pedido, sin tocar el pipeline ni gates S118.
- **Verificación**: sin verificación individual

## §5 Plan de adelgazamiento del repo (regla conservadora, TODO verificado por subagente fresco)

**Notas del clasificador**: MÉTODO: para cada dir de data/ verifiqué (a) tracked=`git ls-files data/<dir> | wc -l`; (b) referenciado=grep en .github/workflows/*.yml, pipeline/profiles/*.yaml (no _archive), frontend/*.html, tests/*.py, scripts/*.py; (c) tamaño=`du -sh`. HALLAZGO METODOLÓGICO CLAVE que cambió la clasificación: de TODO tests/*.py, solo 2 archivos (test_golden_records.py, test_r2_pixel_level.py) abren realmente un JSON bajo data/ — y ambos usan por default "mirova_equivalent". El resto de los tests que mencionan un data_subdir (ej. test_d8_vent_anchored.py, test_dual_roi_bt.py) solo hacen `yaml.safe_load` del perfil (unas pocas KB) y assertan el string `data_subdir` — NO leen los JSON masivos. Esto significa que ningún test local ni workflow de GH Actions necesita el contenido bulk de los ~45 subdirectorios `_*`/`mirova_equivalent_*_v1` de A/B históricos: son 100% regenerables re-corriendo `scripts/run_pipeline.py --profile <nombre> ...` mientras el .yaml del perfil siga vivo (no en _archive/).

CIFRAS VERIFICADAS: repo total tracked (working tree) = 1.8 GB (`git ls-files | du -ch`), de los cuales data/ = 1.7 GB tracked y experiments/ = solo 40 MB tracked (el resto de los 458 MB de experiments/ ya está fuera de git). .git = 3.1 GB — ese exceso sobre 1.8 GB tracked es historial de blobs de commits pasados que ya no están en HEAD; un `git rm` normal NO lo reduce (los objetos siguen en el pack hasta un `git gc --aggressive` post-expiración de reflog, o mejor, `git filter-repo` si se quiere purgar definitivamente). Esa es una operación distinta, más invasiva (reescribe SHAs, rompe cualquier referencia a commits/tags antiguos) — la señalo pero NO la recomiendo ejecutar sin decisión explícita de Nicolás.

documentacion/ (609 MB) NUNCA estuvo en git — `.gitignore:2` lo excluye por completo, `git log -- documentacion/` vacío. No es parte del problema de bloat de GitHub; ya está correctamente aislado según el principio de Data Integrity (raw/PDFs no se versionan).

ACCIÓN DEFENSIVA ANTES DE BORRAR (regla A38/A45 del propio CLAUDE.md del proyecto): cualquier `git rm` de los 44 items en delete_candidates (≈910 MB tracked) debe ir precedido de `git tag pre-s121-data-cleanup <sha> && git push origin <tag>` y, dado que toca >10 archivos y >50MB, confirmación explícita de Nicolás antes de ejecutar — no lo hice en esta sesión porque la tarea pedida fue clasificar, no ejecutar.

DOCUMENTO PREEXISTENTE CLAVE: docs/F28_DATA_ARCHIVE_INVENTORY.md (S73) ya hizo un inventario fila-por-fila de 41 de estos subdirectorios con veredicto SÍ-safe/EVALUAR/NO — nunca se ejecutó el borrado (S80 lo pospuso "hasta que apremie el espacio"). Usé esa tabla como evidencia primaria para ~29 de los 44 delete_candidates, cross-validado contra el estado actual del código (algunos "EVALUAR" de S73 hoy tienen valor renovado porque el paper beyond-MIROVA está activo desde S120; los cerré a keep_github en vez de heredar ciegamente el veredicto de hace 48 sesiones).

VERIFICACIÓN QUE CONTRADIJO LA PREMISA DEL ENUNCIADO: audit-weekly.yml NO referencia experiments/_s119_audit ni _s120_audit (grep vacío) — solo corre scripts/auto_audit_weekly.py, que lee data/mirova_reference/ y data/mirova_equivalent/. Lo señalo explícitamente porque el enunciado pedía verificar antes de asumir, y la asunción resultó falsa.

PENDIENTE NO CUBIERTO A FONDO: no audité individualmente los ~85 subdirectorios restantes de experiments/ (458 MB brutos, pero solo 40 MB tracked) más allá de identificar los 2 archivos de mayor peso tracked (38_forense_Lascar.json, 51_p31_ab/) y los 3 mayores bloques untracked. Dado que el tracked ahí es solo 40 MB (2% del problema de 1.8GB), no es la parte de mayor apalancamiento del pedido — si Nicolás quiere ese nivel de detalle en experiments/, es un segundo pase acotado.

### 5.1 QUEDA EN GITHUB — 32 paths, ~960 MB

| Path | MB | Tracked | Razón |
|---|---|---|---|
| `data/mirova_equivalent/` | 180 | — | NRT operacional. Leído/escrito en vivo por .github/workflows/nrt.yml, backfill-tier-a.yml, nrt-healthcheck.yml, pages-deploy.yml. El dashboard publica desde acá. |
| `data/mirova_reference/` | 99 | — | CSV consolidado/OCR MIROVA. .github/workflows/audit-weekly.yml lo descarga/actualiza en vivo (curl); scripts/auto_audit_weekly.py y build_c2ab_windows.py lo leen. |
| `data/_mirova_literal/` | 78 | — | F28_DATA_ARCHIVE_INVENTORY.md: única referencia canonical "paper-puro Coppola 2016a" conservada; citada activamente en docs/F26_VERDICT_CONSOLIDATED_S72.md como evidencia retroactiva. Recomendación explícita "NO archivar". |
| `data/experimental/` | 67 | — | Perfil secundario vivo: nrt.yml lo corre en cada cron (choice "both"/"experimental"); consumido también por frontend/index.html y frontend/experimental/*.html. |
| `experiments/ (grueso, ~40MB tracked)` | 40 | — | Scripts + FINDINGS.md de auditorías (664 archivos tracked, mayoría KB). Bajo costo, es el audit trail que sostiene el paper beyond-MIROVA activo (S120). NOTA verificada: contrario a lo asumido en el enunciado, .github/workflows/audit-weekly.yml NO referencia experiments/_s119_audit ni _s120_audit (grep vacío) — solo corre scripts/auto_audit_weekly.py sobre data/. Esos dos subdirs (252 KB + similar) son livianos igual, se mantienen por ser parte del trail de auditoría, no por uso del workflow. |
| `data/mirova_equivalent_path_d_atm_gate_v1/` | 35 | — | D9 (path-D dNTI en fondo frío) sigue ABIERTO por catálogo vivo (MEMORY.md: "abiertas: D2, D3, cara-posición D11, NEW-8") y A68 lista "D9/A23 co-validación path-D" como acción futura pendiente. |
| `data/mirova_equivalent_bt_path_on_v1/` | 35 | — | A/B F2.6.e (S72): docs/F26_VERDICT_CONSOLIDATED_S72.md:135 dice "sigue running... cuando vuelva, valida" — el reproc corrió (el dato existe) pero nunca se escribió un veredicto de cierre formal. Es la única evidencia disponible de ese experimento. |
| `data/mirova_equivalent_unsuitable_filters_v1/` | 32 | — | docs/MIROVA_DIVERGENCES.md:459 (nota S116): NEW-8 "sigue siendo un gap de fidelidad literal... re-evaluar urgencia, NO declarar obsoleto". MEMORY.md lo lista entre las divergencias abiertas del catálogo vivo. |
| `data/mirova_equivalent_unsuitable_only_v1/` | 32 | — | Mismo NEW-8 abierto, variante de filtro. |
| `data/mirova_equivalent_no_cap_v1/` | 29 | — | A/B F2.6.b (S72), mismo patrón que bt_path_on_v1: reproc completado, veredicto de cierre nunca redactado (docs/F26_VERDICT_CONSOLIDATED_S72.md:134). |
| `data/_baseline_s44/` | 28 | — | F28 doc: snapshot "antes" canónico de la adopción S46 hacia Coppola literal; resumen ejecutivo del doc lo incluye en el grupo "NO archivar" (reconstruirlo exige re-correr 143 jobs Actions ~3h). |
| `data/_drift1a_only/` | 28 | — | F28 doc: EVALUAR, referencia de drift atómico S46 Ronda 1, valor MEDIO para narrativa beyond-MIROVA. |
| `data/_drift1ab_only/` | 28 | — | F28 doc: EVALUAR, mismo grupo drift atómico S46. |
| `data/_drift1b_only/` | 28 | — | F28 doc: EVALUAR; activable manualmente vía ENABLE_TEST1_K1_BG_EXCLUDE. |
| `data/_drift7_both_only/` | 28 | — | F28 doc: valor ALTO — documenta la decisión arquitectural A_pix nadir-fijo vs sec³(scan-angle), justo el tema que S102-S103 terminó adoptando (A66/A67). Material directo para el paper. |
| `data/low_vent_cap/` | 28 | — | docs/DRIFTS_S17.md:290 instrucción EXPLÍCITA: "Mantener low_vent_cap profile versionado como evidencia A/B y para uso selectivo" cuando el objetivo-2 (recall sub-pixel hidrotermal) sea prioridad. |
| `data/_drift7_modis_only/` | 27 | — | Mismo valor ALTO que _drift7_both_only, aislado MODIS. |
| `data/_drift7_viirs_only/` | 27 | — | Mismo valor ALTO, aislado VIIRS. |
| `data/_dibella_n12_viirs_only/` | 19 | — | F28 doc: valor ALTO paper (comparación régimen alternativo escuela italiana no-MIROVA). Relevante para el paper activo S120. |
| `data/_drift234_only/` | 15 | — | F28 doc: punto de adopción canónico S46 (feature actualmente operacional). Recomendación explícita "NO" (no archivar). |
| `data/_coppola_full/` | 15 | — | F28 doc: valor ALTO para paper beyond-MIROVA (muestra que "paper-puro" es subóptimo vs MIROVA-NRT real). Paper activo desde S120 (venue Volcanica, scope clon+beyond) reactiva este valor. |
| `data/mirova_equivalent_phase2/` | 15 | — | docs/S99_DORMANT_FINDINGS_AUDIT.md DF-5: "Nunca re-evaluado con métrica corregida post-bug S33... Cerrar formalmente o re-correr" — backlog explícito nunca cerrado (~21 sesiones después sigue sin resolución por ID en ningún doc posterior). |
| `data/_no_bt_path/` | 13 | — | F28 doc: valor ALTO, "caso paradigmático" — feature paper-puro que resultó ser carga de FPs regionales (S40 borró 1453 pixels BT Salar de Atacama). EVALUAR con recomendación de conservar mientras el paper esté activo. |
| `data/mirova_equivalent_path_d_covalidation_v1/` | 12 | — | Mismo D9 abierto — variante de co-validación, parte de la misma familia de intentos aún no cerrados. |
| `imagenes/` | 9.9 | — | Publicado en vivo por .github/workflows/pages-deploy.yml (`cp -r imagenes _site/imagenes`), trigger en push a imagenes/**. |
| `data/archive/` | 4.8 | — | docs/DATA_SUBDIRS_INVENTORY_S80.md lo marca "NO TOCAR" (backup histórico). Sin referencia de código activa encontrada, pero tamaño trivial → conservador. |
| `data/backups_pre_scanfix/` | 4.6 | — | Fixture before/after real, leído por scripts/validate_lascar_vs_mirova.py (data/backups_pre_scanfix/Lascar_pre_scanfix.json). Solo uso local (no GH Actions) pero referencia genuina y tamaño trivial. |
| `data/_s99_test1_eq16/` | 1.6 | — | Target vivo de .github/workflows/reproc-s120-eq16-villarrica.yml (`--profile _s99_test1_eq16`); también consumido por frontend/experimental/beyond-mirova.html. |
| `data/mirova/` | 0.5 | — | Ground truth MIROVA por volcán. .github/workflows/sync-mirova-csv.yml lo regenera en vivo desde el CSV; frontend/index.html, mosaico.html y experimental/index.html hacen fetchJSON directo de data/mirova/<vol>.json. |
| `pipeline/profiles/_archive/` | 0.5 | — | 89 archivos, 538 KB — referencia histórica de flags/A-B, costo trivial, no aporta a bloat. |
| `.github/workflows/_archive/` | 0.4 | — | 72 archivos, 396 KB — historial de workflows, costo trivial. |
| `data/audit_continuous/` | 0.005 | — | Escrito en vivo por scripts/auto_audit_weekly.py y comiteado por audit-weekly.yml (`git add data/audit_continuous/`). |

### 5.2 SOLO LOCAL (mover fuera de git / dejar de trackear — no destructivo, el archivo queda en el PC) — 20 paths, ~1225 MB

| Path | MB | Tracked | Razón |
|---|---|---|---|
| `documentacion/` | 609 | no | .gitignore línea 2 excluye documentacion/ por completo — NUNCA estuvo en git (`git log -- documentacion/` vacío). Contribuye 0 al bloat de GitHub. Es el source-of-truth bibliográfico que CLAUDE.md declara (PDFs de papers, probablemente con restricción de copyright) — correctamente local-only por diseño, no requiere acción. |
| `data/mirova_equivalent_pre_s27/` | 195 | no | git ls-files vacío — ya no está en GitHub. El mayor bloque de disco local sin costo de repo. |
| `experiments/_s109_modis_mag/_staging/ y _promo_art/` | 163 | no | Solo 5 de 65 archivos están tracked (scripts + FINDINGS.md, ~40KB). El resto (163MB) son JSON de staging de la A/B S109 (focal magnitude MODIS), ya untracked — limpieza de disco local segura, no toca GitHub. |
| `experiments/_s98_anchor/ (bulk sin los 9 scripts tracked)` | 156 | no | 9 archivos tracked (~52KB de scripts .py/.json/.txt resumen); el resto del directorio (156MB reportado por du) es output de staging sin trackear. |
| `experiments/_s104_roi_probe/ (bulk sin los 14 archivos tracked)` | 47 | no | 14 archivos tracked, el resto es output/probe local sin trackear. |
| `data/_d11_modis_gated/` | 9.2 | no | git ls-files vacío. |
| `data/_d11_modis_nogate/` | 9.2 | no | git ls-files vacío. |
| `data/_s98_anchor/` | 6 | no | git ls-files vacío (distinto de experiments/_s98_anchor). |
| `data/_v750focal_base/` | 5.3 | no | git ls-files vacío. |
| `data/_v750focal_on/` | 5.3 | no | git ls-files vacío. |
| `data/_t1lm_q0_control/` | 2.2 | no | git ls-files vacío. |
| `data/_t1lm_q2_global/` | 2.2 | no | git ls-files vacío. |
| `data/_t1lm_q3_ring15/` | 2.2 | no | git ls-files vacío. |
| `data/_t1lm_q4_te1000/` | 2.2 | no | git ls-files vacío. |
| `data/_t1lm_q3_ring24/` | 2.1 | no | git ls-files vacío. |
| `data/_t1lm_q3_ring35/` | 2.1 | no | git ls-files vacío. |
| `data/_t1lm_q4_te700/` | 2.1 | no | git ls-files vacío. |
| `data/_t1lm_q5_ntilocal/` | 2.1 | no | git ls-files vacío. |
| `data/_t1lm_q6_spatialcore/` | 2.1 | no | git ls-files vacío. |
| `data/mirova_equivalent_backfill_nov2025/` | 1 | no | git ls-files vacío. |

### 5.3 CANDIDATOS A ELIMINAR (requieren tag defensivo A38 + OK de Nicolás) — 46 paths, ~925 MB

| Path | MB | Tracked | Razón |
|---|---|---|---|
| `data/mirova_equivalent_test1pix_filter/` | 78 | sí | Perfil S32 Driver B A/B (header propio yaml). Feature NO adoptada: pipeline/profiles/mirova_equivalent.yaml:274 `enable_test1_pixel_filter: false`. Ningún workflow activo ni test lee el JSON bulk (solo 2 tests en todo tests/ abren data/*/*.json y ambos default a mirova_equivalent). Regenerable: perfil sigue activo en pipeline/profiles/ (no archivado). |
| `data/mirova_equivalent_test1pix_disabled/` | 78 | sí | Control pareado de test1pix_filter, mismo veredicto (flag OFF operacional). Regenerable via perfil activo. |
| `data/mirova_equivalent_lbg_global/` | 78 | sí | Snapshot A/B pre-adopción del concepto lbg_global (S33). El concepto YA fue adoptado per-volcán (gate `lbg_global_compatible`) en docs/S112_TEST1_LOWMAG_AB_RESULTS.md:13-14 (tag pre-s112-intermediate-bg-adoption). Snapshot global (no per-vol) queda superado. |
| `data/nsigma_mir_5/` | 55 | sí | docs/S99_DORMANT_FINDINGS_AUDIT.md DF-10: "D2 nsigma_mir_5/12 veredicto caducado (premisa cap=7K ya no aplica, cap=999 hoy)". El dato ya no representa el pipeline actual. |
| `data/nsigma_mir_12/` | 55 | sí | Mismo DF-10 (S99_DORMANT_FINDINGS_AUDIT.md) que nsigma_mir_5. |
| `data/mirova_equivalent_path_d_cap_v1/` | 35 | sí | Cerrado y distilado: docs/A33_FALSA_ALARMA_F25b.md:25 y docs/F26_VERDICT_CONSOLIDATED_S72.md:19 citan el conteo exacto (467 records d9_capped=True, todos vrp=5.0) y concluyen "no hay bug". Los números ya viven en el doc. |
| `data/mirova_equivalent_test1_retire_only_v1/` | 27 | sí | docs/MIROVA_DIVERGENCES.md:1292 "GAP #A RESUELTO S115 = mislabel ... No queda gap de fidelidad literal accionable; no amerita A/B". Investigación cerrada. |
| `data/_d8_vent_anchored/` | 26 | sí | docs/F28_DATA_ARCHIVE_INVENTORY.md fila: ADOPTADO ya en main (`enable_vent_anchored_clustering: true`), Recomendación SÍ-safe. Regenerable via perfil activo pipeline/profiles/_d8_vent_anchored.yaml. |
| `data/_drift4_only/` | 23 | sí | F28 doc: REFUTADO aislado, SÍ-safe. |
| `data/mirova_equivalent_f_s81_a_intra_radio_disabled/` | 22 | sí | Gates S84/S85 marcados RESUELTO S118 en MEMORY.md/A85 (0 robos de cluster en 214 noches, run 28312968093 → flip OFF definitivo, PR #474). Investigación cerrada con veredicto en docs/AUDIT_S118_C2_GATES_AB.md. |
| `data/mirova_equivalent_f_s81_a_intra_radio_enabled/` | 22 | sí | Mismo cierre S118/A85 que la variante disabled. |
| `data/mirova_equivalent_f_s81_b_prime_2nd_pass_gate_disabled/` | 22 | sí | Mismo cierre S118/A85 (gates second_pass intra-radio). |
| `data/_local_kernel_bg_enabled/` | 20 | sí | F28 doc: ADOPTADO per-vol S61+ ya en main, SÍ-safe. |
| `data/mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/` | 20 | sí | Mismo cierre S118/A85. |
| `data/_drift23_only/` | 19 | sí | F28 doc: REFUTADO (R2 dual-ROI gana), SÍ-safe. |
| `data/s9_vent_permissive/` | 19 | sí | docs/SESSION_INDEX.md fila S16-S17: hipótesis H1 sigma-gating (n_sigma_vent=0) creada S16, "REFUTADA — E1 no mueve recall" en S17. Perfil archivado (pipeline/profiles/_archive/s9_vent_permissive.yaml). |
| `data/_r2_C1_001_summit/` | 18 | sí | F28 doc: REFUTADO (handoff_s47 ninguna variante R2 mejora), SÍ-safe. |
| `experiments/51_p31_ab/` | 18 | sí | Forense de la A/B P3.1 (dual-ROI dNTI), S24. Feature ADOPTADA hace ~96 sesiones y distilada en CLAUDE.md ("S24 A/B P3.1 dual-ROI VALIDADO") y F28_DATA_ARCHIVE_INVENTORY.md. Los JSON forense (7.7+7.3+1.2+1.0+0.18MB) son trabajo intermedio, no el resultado citado. |
| `data/_p3_1_disabled/` | 16 | sí | F28 doc: control, SÍ-safe. |
| `data/_r2_C2_3_summit/` | 16 | sí | F28 doc: REFUTADO, SÍ-safe. |
| `data/_r2_C2_4_summit/` | 15 | sí | F28 doc: REFUTADO, SÍ-safe. |
| `data/_r2_C2_8_summit/` | 15 | sí | F28 doc: REFUTADO, SÍ-safe. |
| `data/_r2_baseline_drift234/` | 15 | sí | F28 doc: control, SÍ-safe. |
| `data/_r2_drift4_alone/` | 15 | sí | F28 doc: "falsa alarma" histórica documentada (preview parcial colapsó a Δ=0 con n=11/11), origen de la regla anti-A18. SÍ-safe. |
| `data/_r2_uniform_no_dual/` | 15 | sí | F28 doc: mismo patrón de falsa alarma histórica, SÍ-safe. |
| `data/_d8_d4_per_vol/` | 13 | sí | F28_DATA_ARCHIVE_INVENTORY.md: ADOPTADO ya en main, SÍ-safe. |
| `data/_h_d8_5_full/` | 13 | sí | F28 doc: REFUTADO 22/22 vols Δ TP=0 (handoff_s38), SÍ-safe. |
| `data/_h_d8_5_disabled/` | 13 | sí | F28 doc: control de _h_d8_5_full, SÍ-safe. |
| `data/_d8_combo_full/` | 13 | sí | F28 doc: REFUTADO universal (regresión Tupungatito/Planchón glaciar frío, handoff_s40), SÍ-safe. |
| `data/_d8_combo_disabled/` | 13 | sí | F28 doc: control, SÍ-safe. |
| `data/_d8_vent_anchored_disabled/` | 12 | sí | F28 doc: control, SÍ-safe. |
| `data/_drift23_dual_only/` | 12 | sí | F28 doc: REFUTADO (drift234 con second-pass es óptimo), SÍ-safe. |
| `data/_p3_1_enabled/` | 12 | sí | F28 doc: ADOPTADO ya en main (`enable_dnti_dual_roi: true`), SÍ-safe. |
| `data/_test1_enabled/` | 12 | sí | F28 doc: ADOPTADO ya en main (`enable_test1_path: true`), SÍ-safe. |
| `data/_test1_disabled/` | 11 | sí | F28 doc: control, SÍ-safe. |
| `data/_r2_drift234_modis_only/` | 9.3 | sí | F28 doc: REFUTADO (pierde VIIRS), SÍ-safe. |
| `experiments/38_forense_Lascar.json` | 8.8 | sí | Forense S38 (investigación D8/vent-anchored) sobre feature ya ADOPTADA y distilada en docs/F28_DATA_ARCHIVE_INVENTORY.md; snapshot de trabajo, no resultado citado en ningún AUDIT posterior. |
| `data/_h8_pixel_filter_disabled/` | 8.5 | sí | F28 doc: control, SÍ-safe. |
| `data/_r2_drift234_viirs_only/` | 5.8 | sí | F28 doc: REFUTADO (pierde recall MODIS 100%), SÍ-safe. |
| `data/_h8_pixel_filter_enabled/` | 5.7 | sí | F28 doc: ADOPTADO ya en main (`enable_pixel_level_distance_filter: true`), SÍ-safe. |
| `data/_dual_roi_bt_disabled/` | 4.2 | sí | F28 doc: control puro (N/A), SÍ-safe. |
| `data/_mirova_legacy/` | 4.2 | sí | F28 doc: control mirror pre-_mirova_literal, marcado borrable desde HANDOFF_S28 y nunca borrado, SÍ-safe. |
| `data/_dual_roi_bt_enabled/` | 4.1 | sí | F28 doc: ADOPTADO (`enable_dual_roi_bt: true`) ya en main, SÍ-safe. |
| `data/_daytime_modis_enabled/` | 3.7 | sí | docs/AUDIT_S105.md:47 lo lista explícitamente entre "~14 ramas if de flags refutados/muertos": "daytime_modis (A/B nunca concluyó)". Perfil ya archivado (pipeline/profiles/_archive/_daytime_modis_enabled.yaml). |
| `data/_daytime_modis_disabled/` | 3.6 | sí | Mismo hallazgo AUDIT_S105.md:47, perfil archivado. |
| `data/_s88_reproc_validation/` | 0.9 | sí | Snapshot puntual de validación S88 (un solo volcán, Lascar.json), sin doc de distillación más allá de tasks/BLOQUE_ARRANQUE_S89.md; superado por 30+ sesiones de auditorías posteriores (S99-S119). |

## §6 Refutaciones (lo que la verificación descartó — igual de importante)

- **[ideas-no-aplicadas]** Backlog Data Integrity (S81) — 6 items de higiene de datos nunca ejecutados, incluye invariante físicamente imposible en 228 records: El archivo backlog es real y abandonado (git log --follow: 1 commit S81, 0 desde entonces), pero 3 de los 6 items citados como evidencia son obsoletos/falsos al verificar contra data/mirova_equivalent/*.json actual (43618 records, no 13207): (1) 0 duplicados PCC hoy (era 15); (2) la afirmación 'no existe dedup key' es falsa — pipeline/store.py:515-518 ya tiene dedup (datetime_utc,sensor) con overwrite/upgrade; (5) el outlier sigma_bg=149.18K citado puntualmente en Lastarria 2026-04-23 hoy vale 3.562K, ya no existe. Los items 3 y 4 sí siguen vigentes (vrp_zero_reason no existe; n_hotspots_clustered>n_anomalous_pixels ahora son 8825 records, no 228 — más grave, con causa raíz distinta: sobreescritura cross-path en process_modis.py:1264, no bug de clustering). Ejecutar el backlog tal cual está escrito desperdiciaría esfuerzo en ítems ya resueltos; se necesita re-auditoría fresca, no el backlog literal.
- **[ecosistema-infra]** ../mirova-tif-archive lleva 57 días sin poll (último commit local 2026-05-20): REFUTADO por evidencia directa contra el remoto real. `gh run list --repo MendozaVolcanic/mirova-tif-archive` muestra el workflow 'Poll MIROVA TIF/KMZ' corriendo cada 5 minutos, runs exitosos hasta el momento de la verificación (2026-07-17T02:35 UTC, es decir HOY). `gh api .../commits` confirma commits recientes: 2026-07-17, 2026-07-14, 2026-07-12, 2026-07-10, 2026-07-08 — nada de brecha de 57 días. El hallazgo citó únicamente el clon LOCAL (`git log -1` dentro de `../mirova-tif-archive`), que sí está parado en 2026-05-20 — pero eso es un clon desactualizado, no el estado real del poller. Más aún: **este exacto diagnóstico ya fue hecho y cerrado en la sesión S120** (2026-07-01, hace 15 días), documentado literalmente en `tasks/BLOQUE_ARRANQUE_S120.md` líneas 47-54: 'el poll TIF NUNCA estuvo estancado — el repo remoto mirova-tif-archive está verde (runs cada 5 min...). Era el clon LOCAL desactualizado desde 2026-05-20 (patrón A25: repo 9.2 GB, git fetch local timeoutea)'. La solución ya prescrita es no hacer `git pull` pelado sino bajar TIFs puntuales vía raw.githubusercontent.com. El hallazgo del otro agente es una re-derivación de un problema ya diagnosticado y resuelto — no debe reabrirse como acción nueva (equivalente a anti-A8/A50: verificar contra origin/main y docs antes de etiquetar 'stale').

---

## §7 Plan de ejecución priorizado (síntesis Fable)

Ordenado por **desbloqueo × riesgo**, no por severidad aislada. Cada fila dice quién
la puede hacer y si necesita red o decisión de Nicolás.

| # | Acción | Frente | Bloquea a | Red? | Decisión Nicolás? | Esfuerzo |
|---|---|---|---|---|---|---|
| 1 | Liberar disco C: (mover documentacion/ + experiments/ fuera de OneDrive-sync) + `git gc --prune=now` (limpia 338 MB tmp_pack) | A | push/pull, todo | no | **sí** (dónde mover) | bajo |
| 2 | Completar fix dashboard liviano en `mosaico.html` + `diario.html` (mismo patrón que index) | B | dashboard usable | no | no | bajo |
| 3 | Push rama `s120-dashboard-lightweight` (con #2 incluido) → PR → merge | B | producción viva | **sí** | no | bajo |
| 4 | Poda data/ A/B (~1.7 GB → local): tag `pre-s121-data-prune` + backup tar + `git rm -r` | A/C | .git deja de crecer por esto | sí (push) | **sí** (lista final) | medio |
| 5 | Fixes docs baratos: GAP #A contradicción, INDEX.md, BLOQUE_ARRANQUE_S121 | C | sesión fría correcta | sí (push) | no | bajo |
| 6 | fetch.py `→`→`->` (1 línea, ciclo A45 ya diferido) | A | — | sí (push) | no (parte de A45) | trivial |
| 7 | Merge rama huérfana `s120-eq16-multivol` (Panel 2b PCC/Chaitén) | B | beyond completo | sí | no | bajo |
| 8 | **D12 MODIS Láscar FN**: derivar distance_class de primary_cluster + reproc | C | recall MODIS real | sí | **sí (A45 tag)** | medio |
| 9 | Decisión arquitectura data (Releases / repo satélite / branch orphan) | A | sostenibilidad | — | **sí** | alto |
| 10 | Backlog: schema-validation test + NRT-duration tracking (AUDIT_S119 §8) · AVTOD para paper · nrt.yml concurrency guard | varios | robustez | sí | no | medio |

**Ruta crítica**: 1 → 2 → 3 destraba producción y la red. 4 + 9 atacan la causa raíz del
peso. 8 es el único bug científico real (FN confirmado). El resto es higiene de fondo.

## §8 Qué NO reabrir (anti-A8, confirmado por esta auditoría)

- El pipeline de detección es fiel a Coppola 2016a (S114-S119) — NO re-auditar fidelidad.
- Poll TIF mirova-tif-archive: **verde en remoto**, el "stale" es el clon local (ya S120).
- Backlog data-integrity S81 literal: 3 de 6 items **ya resueltos** — re-auditar fresco, no
  ejecutar el backlog viejo. Los items vivos: `vrp_zero_reason` inexistente y
  `n_hotspots_clustered > n_anomalous_pixels` (8825 records, causa: sobreescritura cross-path
  en process_modis.py:1264 — distinto del bug que el backlog suponía).
