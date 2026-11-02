# Auditoría S173, frente F1: censo de consumidores del flag de la vía «código MIROVA» de MODIS

## 1. Encabezado

- Hora del servidor: al empezar 2026-11-02 12:20:07 GMT; durante el censo 12:38:44 GMT; al cerrar 12:47:54 GMT
  (header `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commits medidos:
  - PR B `c9525f9946ccd03bdaad5ac28b5ef2318bcaee50`, en el worktree compartido
    `D:/vrp-trabajo/worktrees/s172-modd-encendido` (sólo lectura; `git status --porcelain` = 0 entradas al terminar);
  - PR A `0a0dae3448f3ad1ef130ec68b37cfbe97db526b8`, en un worktree propio y desechable
    `D:/vrp-trabajo/worktrees/s173-f1-a` (quitado al final con `git worktree remove`);
  - base declarada `a3c5a9b49`; origin/main al medir: `c3540b731` y después `47cdc446f`. Encima de `a3c5a9b49` sólo
    hay commits «NRT update» de `data/mirova_equivalent/*.json` (`git diff --stat a3c5a9b49 origin/main`: 11 archivos,
    todos de data).
- Modelo y esfuerzo: Opus 5.5 (`claude-opus-5-5`, lo declara el entorno). Esfuerzo: el entorno no me lo muestra como
  valor; lo que veo es el presupuesto de razonamiento que el arnés fijó, y es bajo. Lo declaro **bajo**, no el «alto»
  que se pidió.
- CARPETA: `D:/vrp-trabajo/temporales/s173_aud/f1/`.
- Incidente propio: la primera corrida de `m_vistas_via.py` tenía la ruta de salida relativa y, tras su `os.chdir`,
  escribió `vistas_via.json` dentro del worktree compartido. Lo moví a la CARPETA en el mismo minuto (`git status
  --porcelain` volvió a 0 entradas) y corregí el script para que resuelva la ruta antes del `chdir`. No tocó ningún
  archivo versionado.
- Qué NO miré, para que mi silencio no se lea como «todo bien»:
  - No hay ningún record real de la vía de MODIS en el repositorio ni en `D:/vrp-trabajo`: `git grep` sobre B, sobre
    origin/loop/activo y `rg` sobre `D:/vrp-trabajo` dan 0 records con `"final_hotspot_source": "codigo_mirova"`, y
    `data/sombra_codigo_mirova/` no existe en origin/main ni en loop/activo. Los records de la vía que usé los produce el
    procesador real de B sobre el gránulo sintético de Láscar de las pruebas. La conducta de las vistas con records
    reales de la vía es SIN DATO.
  - El CI del PR B en GitHub y cualquier corrida real de la vía en el runner (pyhdf no corre en Windows).
  - La suite completa: corrí 75 archivos de prueba explícitos (lista en `lista_pruebas.txt`).
  - Ninguna vista se abrió en un navegador; las funciones del tablero se ejecutaron con node.
  - Tiempos del NRT, crons, concurrencia y el lector de V375-E: no son de este eje.

## 2. En una pantalla

1. Los arreglos de la mini auditoría S172 de mi eje están de verdad en las puntas y funcionan con la vía encendida:
   pyproj (0 workflows que corran la vía sin él), vigilancia de K (MA172-101), ancla del tablero (MA172-102) y la prueba
   de adopción de K (MA172-103). Pruebas de mi eje: B 1065 pasan y 0 fallan (75 archivos); A 1051 pasan y 0 fallan.
2. Hallazgo nuevo (gravedad 3): **el `git revert` de B se lleva los dos arreglos que leen records de la vía, y los
   records se quedan en `data/`.** Tras la reversión, la vigilancia de K vuelve a culpar a K de una pérdida de la vía
   (medido: REVERSION_CANDIDATA), justo con el evento que habría motivado revertir. Y el mapa vuelve a poner el marcador
   rojo a 14,9 km del cúmulo (B lo pone a 0,3 km). El cuerpo del PR B no lo declara.
3. Siguen abiertos de S172, re-verificados hoy: una excepción de la vía (que no sea pyproj) deja a MODIS mudo hasta 3
   días con el NRT en verde; 55 perfiles heredan la vía sin decirlo; los documentos que siguen diciendo K o APAGADA,
   entre ellos el aviso del tablero, que el operador lee; y la marca del tablero y el audit semanal no saben de una
   reversión.
4. Censo completo: 42 consumidores en la sección 4.

## 3. Comprobación de los arreglos declarados de mi eje (regla C)

| ID S172 | Declarado | Hoy, en las puntas | Evidencia |
|---|---|---|---|
| MA172-201, VMA172-201 (pyproj) | pyproj en los workflows que corren la vía, con un paso de comprobación | CONFIRMADO en A y B: los 32 workflows que corren un perfil con la vía en MODIS la instalan, salvo 3 que no corren el pipeline (`backfill-geometry.yml` sólo baja la geolocalización, `scripts/backfill_geometry.py` l. 47-48; `nrt-healthcheck.yml` y `pages-deploy.yml` sólo leen JSON). Hay paso «Comprobar pyproj» en `nrt.yml` l. 147-149, `backfill-tier-a.yml` l. 76-77 y `reproc-chunked.yml` l. 132-133. Control positivo: los workflows de la base `a3c5a9b49` con los perfiles de B dan 24 sin pyproj, `nrt.yml` entre ellos | `censo_workflows.py` → `wf_B.tsv`, `wf_B.out`, `wf_base.out` |
| MA172-101 (vigilancia de K cuenta la vía como K) | `scripts/vigilancia_sombra.py` excluye la vía por clave | CONFIRMADO con la vía encendida (B, E1 VERDE, E2 REVERSION_CANDIDATA de control). **Cubre un camino de dos**: el arreglo vive sólo en B (hallazgo 161) | `m_postrevert_vigilancia_sombra.py` → `postrevert_vigilancia_salida.txt` |
| MA172-102 (ancla del tablero) | `esAnclaHonesta` con `codigo_mirova` y siete llamadas | CONFIRMADO en B: marcador a 0,318 km (el cúmulo) en V1 y en V2, igual que el control `ctx_cluster`. `diario`, `mosaico` y `comparacion` no tienen lista de anclas (0 apariciones de `final_hotspot` en `mosaico.html` y `comparacion.html`; en `diario.html` sólo en comentarios, l. 242 y 260). **Cubre un camino de dos**: vive sólo en B (hallazgo 162) | `m_vistas_via.py` → `vistas_via.json`, `vistas_via_salida.txt` |
| MA172-103 (prueba de adopción de K roja en B) | la prueba espera la vía en la diferencia del laboratorio | CONFIRMADO: `tests/test_guard_adopcion_k_s153.py` pasa en B y en A | `pytest_B.txt`, `pytest_A.txt` |
| MA172-104, 110, 303 (perfiles que heredan) | no arreglado (pendiente declarado) | SIGUE: hallazgo 166 | `perfiles_B.tsv` |
| MA172-105, 106, VMA172-101 (documentos) | no arreglado (pendiente declarado) | SIGUE: hallazgo 165 | lectura, sección 5 |
| MA172-205, MA172-304 (marca y audit tras revert) | no arreglado (pendiente declarado) | SIGUE: hallazgo 169 | lectura del código de A |
| VMA172-202, 203 (excepción de la vía, stale gate) | no arreglado; el paso de pyproj cubre sólo ese caso | SIGUE: hallazgo 164 | lectura |

## 4. Censo de consumidores (punta de B)

Cómo se armó. `censo_consumidores.py` corre `git grep` sobre el commit (no sobre el árbol) por siete formas:
`ENABLE_MODIS_CODIGO_MIROVA`, `enable_modis_codigo_mirova`, `via_codigo_mirova`, el valor `"codigo_mirova"`,
lecturas indirectas (alias `es_record_via_modis`, `claves_via_modis`, `claves_via`, `FAMILIAS[`, `_CODIGO_MIROVA`) y
lo que identifica a K (`codigo_sha`, `final_hotspot_source`). Salida: `censo_B.tsv` y `censo_A.tsv`. Después tracé a
mano lo que no nombra el flag pero lo consume: los workflows que corren un perfil (`censo_workflows.py`), el corredor
`scripts/run_pipeline.py`, el almacén y las vistas que leen los campos del record.

Preguntas del instrumento. (1) ¿Vería un consumidor que existe? Control positivo: cuatro consumidores que conozco por
lectura previa (`pipeline/process_modis.py` por F1, `scripts/vigilancia_sombra.py` por alias, `frontend/index.html` por
el valor, `guardia_k_modis.yaml` por la clave) aparecen en B. En A faltan justo `vigilancia_sombra.py` e `index.html`,
que en A no leen la vía: el instrumento distingue «consume» de «no consume». (2) ¿Vería un instrumento muerto? Una
cadena inventada da 0 y los totales por forma salen distintos de 0 (B: F1 52, F2 23, F3 173, F4 7 líneas). Valor de
cada perfil: `resolver_perfiles.py`, un subproceso por perfil con `pipeline.profile` (A89). Control: producción da True
en B y False en A, la guardia False en los dos. B: 101 perfiles, 57 con la vía, 47 de ellos con MODIS; A: 1 (la
sombra).

| # | Consumidor | archivo:línea (B) | Cómo lee | Con vía | Tras revert | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Perfil de producción | `pipeline/profiles/mirova_equivalent.yaml:148` | clave en `thresholds:` | sí (True) | sí (vuelve a False) | `perfiles_B.tsv`, `perfiles_A.tsv` |
| 2 | Guardia K | `pipeline/profiles/guardia_k_modis.yaml:28` | clave explícita False | sí: frente a producción difiere sólo en vía, carpeta, nombre y sensores VIIRS | sí | `diff_perfiles_B.txt` |
| 3 | Sombra de los 11 | `pipeline/profiles/sombra_codigo_mirova.yaml:32` | explícita True | sí | sí | `perfiles_B.tsv` |
| 4 | Laboratorio C0 | `pipeline/profiles/experimental.yaml:66` | explícita False (B) | sí | sí (hereda False) | `diff_perfiles_B.txt` |
| 5 | Laboratorio de Chillán | `pipeline/profiles/experimental_ndc_focus.yaml:44` | explícita False; sin MODIS | sí | sí | `perfiles_B.tsv` |
| 6 | Ancla de las pruebas pre-K | `pipeline/profiles/_s146_ab_control.yaml:42` | explícita False | sí | sí | `perfiles_B.tsv` |
| 7 | 55 perfiles derivados sin la clave, entre ellos `_s154_reproc_k_historico` y `experimental_lowT` | `extends: mirova_equivalent` | herencia de un nivel | **NO**: miden la vía y dicen otra cosa (hallazgo 166) | sí | `perfiles_B.tsv` |
| 8 | Perfil deprecado que escribe en la carpeta de producción | `pipeline/profiles/mirova_equivalent_villarrica_test1.yaml` | sin `extends`, False | SIN DATO (ningún workflow lo nombra) | sí | `wf_B.tsv`, `perfiles_B.tsv` |
| 9 | Cargador de perfiles | `pipeline/profile.py:909` | `_t.get("enable_modis_codigo_mirova", False)` | sí; el comentario l. 903-908 dice «entra APAGADA» (165) | sí | lectura |
| 10 | Procesador MODIS | `pipeline/process_modis.py:106, 637-660` | constante importada | sí, salvo excepción de la vía, que no cae a K (164) | sí | `pytest_B.txt` |
| 11 | Procesadores VIIRS | `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py` | no leen el flag de MODIS (0 líneas F1) | sí | sí | `censo_B.tsv` |
| 12 | La vía | `pipeline/mirova_v750_codigo.py:742` | escribe `"codigo_mirova"`; cabecera FICHA l. 3-6 dice APAGADA (165) | sí | sí | lectura |
| 13 | Almacén | `pipeline/store.py:357, 362, 401, 455, 549, 614` | `via_codigo_mirova is True` salta las compuertas de K; marca de régimen en todo record | sí; la lista `_honest_anchor_sources` (l. 413) no trae `codigo_mirova`, pero ese bloque está detrás de `not _via_mirova` (l. 401) | sí | lectura |
| 14 | Corredor | `scripts/run_pipeline.py:253-280` | no lee el flag; atrapa toda excepción por gránulo | **parcial** (164) | sí | lectura |
| 15 | NRT | `.github/workflows/nrt.yml:143-149` | corre producción | sí para pyproj; no busca `ERROR processing` en el log (164) | sí | `wf_B.tsv`; `grep` de `nrt.yml` |
| 16 | Reprocesos operativos | `backfill-tier-a.yml:73-77`, `reproc-chunked.yml:129-133` | corren producción | sí | sí | `wf_B.tsv` |
| 17 | 20 probes y reprocesos de despacho manual | `.github/workflows/probe-*.yml`, `reproc-s1*.yml` | perfiles que heredan la vía | instalan pyproj; miden la vía en MODIS (166) | sí | `wf_B.tsv` |
| 18 | Workflow de la guardia | `.github/workflows/guardia-k-modis.yml:90` | perfil False; sin pyproj a propósito | sí | sí | `wf_B.tsv` |
| 19 | Workflow de la sombra de los 11 | `.github/workflows/sombra-codigo-mirova.yml:91` | perfil True, con pyproj | sí | sí | `wf_B.tsv` |
| 20 | Salud del NRT | `nrt.yml:291` (A57) y `nrt-healthcheck.yml:73` | último record de cualquier sensor | **NO** ve un MODIS mudo (164) | sí | lectura |
| 21 | Audit semanal | `scripts/auto_audit_weekly.py:397-481` | `es_record_via_modis`, `frontera_via_modis` | sí (pruebas verdes) | **NO** (169) | `pytest_B.txt`; l. 446-448 |
| 22 | Banco de paridad | `scripts/banco_paridad.py:289` | no copia la marca; los demás cruzan por clave | sí | sí | lectura |
| 23 | Vigilancia de K (sombra C0) | `scripts/vigilancia_sombra.py:423-489` | `claves_via()` (B) | sí (E1 VERDE) | **NO** (E1 REVERSION_CANDIDATA, hallazgo 161) | `postrevert_vigilancia_salida.txt` |
| 24 | Vigilancia de la guardia | `scripts/vigilancia_guardia_modis.py:98-140, 304-360` | `via_codigo_mirova`, flag por subproceso | sí (pruebas verdes) | sí por lectura (con flag apagado `avisos_via` da []) | `pytest_B.txt`, `pytest_A.txt` |
| 25 | Revisión de la guardia | `scripts/revisar_guardia_modis.py:75-81` | rojo si la guardia trae la clave | sí | sí | lectura |
| 26 | Revisión de la sombra | `scripts/revisar_sombra.py:164-178` | cuenta la vía; rojo con `ERROR processing` | sí | sí | lectura |
| 27 | Predicado del tablero | `frontend/index.html:1162, 1595, 1609` | campos del record | sí (V1 8,962 MW summit; V3 lejano = 0; V4 sin detección no publica) | sí (igual) | `vistas_via_salida.txt` |
| 28 | Ancla del marcador | `frontend/index.html:1618` y 7 llamadas | `esAnclaHonesta` (B) | sí (0,318 km) | **NO** (14,89 km en V2, hallazgo 162) | `vistas_via_salida.txt` |
| 29 | Filtros de artefacto | `frontend/index.html:1336-1367` | calibrados con K | SOSPECHA (170) | igual | lectura |
| 30 | Aviso de métricas | `frontend/index.html:544` | texto: «la réplica usa el detector K» | **NO** (165) | sí | lectura |
| 31 | Exportación CSV | `frontend/index.html:4361-4372` | sin `via_codigo_mirova` ni `regimen` | **NO** distingue (168) | sí | lectura |
| 32 | Tendencia 90 días | `frontend/diario.html:255, 425, 437` | campos del record | sí | sí | `vistas_via_salida.txt` |
| 33 | Mosaico | `frontend/mosaico.html:255, 407, 418` | campos del record | sí | sí | `vistas_via_salida.txt` |
| 34 | Comparación (vista preliminar) | `frontend/comparacion.html:202` | cúmulo summit | sí | sí | `vistas_via_salida.txt` |
| 35 | Marca de cambio de detector | `frontend/cambio_detector.js:135-175` | `via_codigo_mirova === true` | sí | **NO** (169) | lectura del código de A |
| 36 | Prueba de adopción de K | `tests/test_guard_adopcion_k_s153.py:45-53` | diferencia laboratorio contra producción | sí | sí | `pytest_B.txt`, `pytest_A.txt` |
| 37 | Prueba del laboratorio congelado | `tests/test_experimental_congelado_s150.py:48` | diferencias declaradas | sí | sí | ídem |
| 38 | Prueba «serie pura K» | `tests/test_guard_serie_k_pura_s158.py:33-34` | K = trae `codigo_sha` | pasa, pero en MODIS no distingue vía de K (167) | sí | lectura |
| 39 | Guard del encendido | `tests/test_guard_modis_codigo_mirova_encendido_s172.py` | `pipeline.profile` por subproceso | sí | se va con el revert (lo dice su l. 7) | `pytest_B.txt` |
| 40 | Pruebas de los arreglos de B | `tests/test_vigilancia_sombra_via_modis_s172.py`, `tests/test_tablero_ancla_codigo_mirova_s172.py` | no lo leen: prueban los arreglos | sí | se van con el revert; contra el código de A, 3 de 3 de la del tablero fallan, por estructura y no por aserción de conducta | `postrevert_tablero_pytest.txt` |
| 41 | Ficha SDA, MISSION, CLAUDE.md, DIVERGENCES | `docs/FICHA_SDA_VRP_CHILE.md` v1.18, `docs/MISSION.md:8` | marcas A113 (B) | sí | **NO**: vuelven a v1.17 sin registro del período (163) | `git diff 0a0dae344 c9525f994` |
| 42 | README y SINTOMAS | `README.md:52-56`, `docs/SINTOMAS.md:25-28` | texto: producción = K | **NO** (165) | sí | lectura |

## 5. Hallazgos (lo peor primero)

### 161
- TÍTULO: Tras el revert de B, la vigilancia de K vuelve a contar como K los records MODIS de la vía que quedan en
  `data/`, y con el mismo evento que motivó revertir pide revertir K.
- ARCHIVO:LÍNEA: el arreglo vive sólo en B, `scripts/vigilancia_sombra.py:423-447` (`claves_via` y el filtro por clave
  de l. 444-445). En A, que es lo que queda tras el revert, el filtro es `scripts/vigilancia_sombra.py:432`, TEXTO:
  «prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]   # sólo records de K». Todo record trae
  `codigo_sha` (`pipeline/store.py:549`). El cuerpo del PR B no lo declara:
  `experiments/_s171_modd_adopcion/PR_B_CUERPO.md` l. 78-80, TEXTO: «Lo que el revert deja en pie: todo el PR A
  (guardia, su vigilancia, el detector VIA_MODIS del audit, la marca del tablero). Lo que no deshace: los records MODIS
  ya escritos por la vía». SCRIPT:SALIDA `m_postrevert_vigilancia_sombra.py` → `postrevert_vigilancia_salida.txt`,
  `postrevert_trabajo/postrevert_vigilancia_{A_tras_revert,B_control}.json`.
- QUÉ PASA: se revierte cuando la vía calla una alerta protegida que K habría visto. Ese record mudo de la vía queda en
  la serie de producción. La vigilancia de K, de vuelta a su versión anterior, lo toma por un record de K. Si el
  laboratorio C0 publicó esa alerta, atribuye la pérdida a K. Medido con el código real de cada versión (predicado del
  tablero por node), sobre una pasada MODIS sintética de Láscar con una protegida de 2,0 MW que C0 publica:
  - código tras el revert: E1 (la vía calla) da REVERSION_CANDIDATA, igual que E2 (K calla); E3 (la vía publica) da
    VERDE;
  - B, como control: E1 VERDE, E2 REVERSION_CANDIDATA y E3 VERDE.

  La ventana de la vigilancia va desde la frontera de K hacia adelante, así que el record mudo queda dentro para
  siempre.
- CÓMO SE VE EN EL DASHBOARD: invisible en el tablero. Se ve un issue de GitHub de la vigilancia de K
  (`.github/workflows/vigilancia-sombra.yml` l. 9-10) que culpa a K, justo después de revertir la vía. Con los datos
  de hoy el plazo de K está cumplido (dato de la mini auditoría S172, MA172-101, no re-medido aquí), así que saldría
  como candidata fuera de plazo y no como reversión pre-autorizada.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/s173_aud/f1 && python m_postrevert_vigilancia_sombra.py
  D:/vrp-trabajo/worktrees/s173-f1-a A_tras_revert postrevert_trabajo` (el código de A es el de después del revert;
  hay que recrear ese worktree en `0a0dae344`), y como control el mismo comando con
  `D:/vrp-trabajo/worktrees/s172-modd-encendido B_control`. Láscar, pasada MODIS sintética 2026-11-05 07:35 UTC.
- CONFIANZA: CONFIRMADO para el mecanismo (3 escenarios sintéticos por versión, 1 pasada cada uno, ventana 2026-11-01 a
  2026-11-10). Que el laboratorio C0 publique la protegida que la vía calló es SOSPECHA: en MODIS, C0 publicaba 6 de 39
  protegidas en V2 según CLAUDE.md (A117, marca S157), dato no re-medido aquí.
- GRAVEDAD: 3. Atribuye una pérdida al detector equivocado el mismo día en que se toma una decisión de reversión, con
  dos vigilancias que dicen cosas distintas. El arreglo de B es inerte sin records de la vía (lo prueba su propio
  control, `test_control_sin_la_via_una_produccion_sin_modis_si_es_ciega`), así que podría ir en A.

### 162
- TÍTULO: Tras el revert de B, el marcador rojo del mapa de detalle de un record de la vía vuelve a caer en el primer
  píxel alertado (hasta 14,9 km del cúmulo publicado).
- ARCHIVO:LÍNEA: `frontend/index.html:1618` (`esAnclaHonesta`, sólo en B) y la lista vieja de A,
  `frontend/index.html:1631` en `0a0dae344`, TEXTO: «["test1_roi", "test1_nti_peak", "ctx_cluster"].includes(r.final_hotspot_source)».
  SCRIPT:SALIDA `m_vistas_via.py` → `vistas_via.json`, `vistas_via_salida.txt`.
- QUÉ PASA: la vía suma todos los píxeles alertados, también los lejanos, y deja en `final_hotspot` el centroide del
  cúmulo más radiante. Con el código de A, el marcador por defecto es `anomaly_pixels[0]`, el primer alertado en orden
  de barrido. Records producidos por el procesador real de B (gránulo sintético de Láscar, pasados por
  `store.append_record`):
  - V1 (sólo cráter): 0,318 km en B, 0,8 km en A;
  - V2 (cráter y un foco a 15 km al norte; record summit de 14,302 MW): 0,318 km en B, 14,89 km en A;
  - control con el mismo V2 rotulado `ctx_cluster`: 0,318 km en las dos versiones.

  Publicación y magnitud no cambian entre A y B. Sólo cambia el marcador del mapa de detalle; la tarjeta, la tabla y
  la capa de puntos de A caen a `pc.centroid_dist_km` o al pico del cúmulo.
- CÓMO SE VE EN EL DASHBOARD: en el mapa de detalle de un volcán, una pasada MODIS de la época de la vía, rotulada
  «cráter», aparece con su punto rojo sobre la fuente lejana. Se ve durante 100 días en la vista reciente
  (`scripts/build_recent_json.py` l. 20, `--days 100`) y siempre en la vista completa.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/s173_aud/f1 && PYTHONDONTWRITEBYTECODE=1 python m_vistas_via.py
  D:/vrp-trabajo/worktrees/s172-modd-encendido D:/vrp-trabajo/worktrees/s173-f1-a vistas_via.json`; Láscar, pasada
  sintética MYD021KM.A2026306.0735.
- CONFIANZA: CONFIRMADO sobre records sintéticos producidos por el procesador real (5 casos). Con records reales: SIN
  DATO (no existe ninguno).
- GRAVEDAD: 2. Muestra la anomalía en otro lugar del volcán, pero no cambia si se publica ni cuánto.

### 163
- TÍTULO: El revert de B borra de la ficha SDA y de los documentos operativos el registro de que hubo un período de
  MODIS con otro método, y los datos de ese período se quedan.
- ARCHIVO:LÍNEA: `git diff 0a0dae344 c9525f994 -- docs/FICHA_SDA_VRP_CHILE.md docs/MISSION.md CLAUDE.md
  docs/MIROVA_DIVERGENCES.md` (versión v1.18, nota de «Funcionamiento/lógica», fila v1.18 del historial, marca S172 de
  MISSION l. 8 y siguientes). Todo vive en B.
- QUÉ PASA: un `git revert` de B devuelve la ficha a v1.17 y saca las marcas A113. Los records MODIS de la vía siguen
  publicados en la serie. La ficha de transparencia (Resolución CPLT N°372) quedaría sin la versión que describe el
  método que produjo una parte de lo publicado. Nada del PR A ni del cuerpo del PR B prevé una v1.19 que registre la
  reversión.
- CÓMO SE VE EN EL DASHBOARD: invisible. Se ve en la ficha publicable y en lo que lee la sesión siguiente.
- CÓMO REPRODUCIRLO: el comando de arriba; y PR_B_CUERPO.md l. 78-83, que no lo menciona.
- CONFIANZA: CONFIRMADO (lectura del diff: los cuatro documentos cambian sólo en B).
- GRAVEDAD: 2.

### 164
- TÍTULO: Si la vía lanza cualquier excepción que no sea la falta de pyproj, MODIS queda mudo con el NRT en verde, y
  el primer aviso llega a los 3 días.
- ARCHIVO:LÍNEA:
  - `scripts/run_pipeline.py:279-280`, TEXTO: «except Exception as e: print(f"  ERROR processing {l1b.name}: {e}")»;
  - el bloque de la vía en `pipeline/process_modis.py:637-660` no tiene try y cae a K sólo en tres casos con nombre;
  - `nrt.yml` no busca `ERROR processing` (las únicas búsquedas del log son por `NASA_AUTH_UNREACHABLE`, l. 254);
    `revisar_sombra.py` y `revisar_guardia_modis.py` sí la buscan (l. 180 y l. 82);
  - el gate A57 (`nrt.yml:291`) y `nrt-healthcheck.yml:73` miran el último record de cualquier sensor;
  - el único aviso específico de MODIS es `scripts/vigilancia_guardia_modis.py:304-305` (frescura de producción por
    volcán y sensor), con `MAX_DIAS_SOMBRA_SIN_DATOS = 3` (`scripts/vigilancia_sombra.py:61`).
- QUÉ PASA: el paso «Comprobar pyproj» cubre el caso medido en S172, pero no otras fallas de la vía en un gránulo real
  (lectura del HDF, interpolación, grilla). En ese caso el gránulo se pierde, no se escribe record ni se cae a K, y VIIRS
  sigue llenando la serie, así que los gates de frescura ven datos frescos. Es VMA172-202 y VMA172-203 de S172, que
  siguen abiertos.
- CÓMO SE VE EN EL DASHBOARD: MODIS deja de aparecer en los 11 volcanes; VIIRS sigue normal. Si la vigilancia de la
  guardia corre, a los 3 días abre el issue «Guardia K de MODIS: vigilancia ciega».
- CÓMO REPRODUCIRLO: lectura de las líneas citadas. No provoqué la excepción: pyhdf no corre en Windows.
- CONFIANZA: CONFIRMADO por lectura del camino. Que ocurra con un gránulo real es SOSPECHA.
- GRAVEDAD: 2. Hasta 3 días de MODIS ciego sin aviso, con VIIRS cubriendo.

### 165
- TÍTULO: Documentos y comentarios operativos siguen diciendo que producción es K o que la vía está APAGADA; uno de
  ellos lo lee el operador en el tablero.
- ARCHIVO:LÍNEA:
  - `frontend/index.html:544`, TEXTO: «Desde el 18 oct 2026 la réplica usa el detector K»;
  - `pipeline/mirova_v750_codigo.py:5-6` (cabecera FICHA), TEXTO: «APAGADA por flag en cada sensor
    (enable_v750_codigo_mirova, S162; enable_modis_codigo_mirova, S164)»;
  - `pipeline/profile.py:906-907`, TEXTO: «confirmó que entra APAGADA: con False no corre ninguna línea de la vía»;
  - `README.md:52-56` y `docs/SINTOMAS.md:25-28`, sin marca S172.
- QUÉ PASA: es MA172-105, MA172-106 y VMA172-101 de S172. El implementador los declaró pendientes; siguen así en la
  punta de B.
- CÓMO SE VE EN EL DASHBOARD: el aviso de la sección de métricas de `index.html` dice que la réplica usa K. Con B, eso
  vale sólo para VIIRS. La marca de `cambio_detector.js` dice lo contrario en los gráficos.
- CÓMO REPRODUCIRLO: `sed -n 544p frontend/index.html`, `sed -n 3,8p pipeline/mirova_v750_codigo.py` y
  `sed -n 903,909p pipeline/profile.py`, en el worktree de B.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. La cabecera FICHA es transparencia SDA y el aviso lo ve el operador.

### 166
- TÍTULO: 55 perfiles derivados pasan en silencio a la vía en MODIS, entre ellos el de «reproceso histórico con K».
- ARCHIVO:LÍNEA: `pipeline/profiles/_s154_reproc_k_historico.yaml` y `pipeline/profiles/experimental_lowT.yaml` (sin la
  clave; `extends: mirova_equivalent`); `scripts/reemplazar_ventana_reproceso.py:7` lo usa para reemplazar ventanas de
  la serie publicada. SCRIPT:SALIDA `resolver_perfiles.py` → `perfiles_B.tsv`, `perfiles_B.out`.
- QUÉ PASA: de 60 perfiles con `extends: mirova_equivalent`, 56 resuelven la vía en True en B y 55 sin declararla
  (`pipeline.profile`, un subproceso por perfil). En A, 0. La guarda de B
  (`tests/test_guard_modis_codigo_mirova_encendido_s172.py`) cubre sólo los perfiles que nombra un workflow programado.
  Su docstring dice 58 derivados; son 60. Si alguien repite un reproceso «con K» o un A/B viejo después de B, en MODIS
  mide la vía. Es MA172-104, MA172-110 y MA172-303, que siguen abiertos.
- CÓMO SE VE EN EL DASHBOARD: invisible, hasta que un reproceso «con K» se aplica a `data/mirova_equivalent/` con
  `reemplazar_ventana_reproceso.py`.
- CÓMO REPRODUCIRLO: `python resolver_perfiles.py D:/vrp-trabajo/worktrees/s172-modd-encendido perfiles_B.tsv`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 169
- TÍTULO: Lo que el PR A deja en pie tras el revert no sabe que hubo un revert: el audit semanal saca a K de las
  métricas de MODIS y la marca del tablero sigue diciendo «vía».
- ARCHIVO:LÍNEA:
  - `scripts/auto_audit_weekly.py:446-448` (docstring de `_detector`), TEXTO: «Si se revierte el encendido, los records
    MODIS nuevos vuelven a ser K en noches que esta función llama VIA_MODIS y quedan en `fuera_de_detector`»;
  - `frontend/cambio_detector.js:152-167` (`primeraViaModis`) y l. 169-175 (texto «que reemplazó al detector K en
    MODIS»), sin marca de vuelta a K.
- QUÉ PASA: es MA172-304 y MA172-205 de S172; sigue igual en A, que es lo que queda tras el revert.
- CÓMO SE VE EN EL DASHBOARD: tras una reversión, la línea naranja «MODIS: vía MIROVA» y su aviso quedan fijos, y el
  regreso a K no lleva marca. En Chillán, un escalón hacia abajo se leería como que la actividad baja.
- CÓMO REPRODUCIRLO: lectura del código en `0a0dae344`.
- CONFIANZA: CONFIRMADO por lectura (lo declara el propio código).
- GRAVEDAD: 2.

### 167
- TÍTULO: La prueba «serie publicada pura K» identifica K por `codigo_sha` y desde B da por K los records de la vía.
- ARCHIVO:LÍNEA: `tests/test_guard_serie_k_pura_s158.py:33-34`, TEXTO: «def es_k(r: dict) -> bool: return
  bool((r.get("regimen") or {}).get("codigo_sha"))».
- QUÉ PASA: no da falsa alarma, porque los records de la vía traen la marca. Pero su promesa («pura K») deja de
  cumplirse en MODIS sin que la prueba lo vea. Es la regla de la etiqueta.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 168
- TÍTULO: El tablero nunca lee `via_codigo_mirova` y su exportación CSV no la trae: la caída a K y la pasada de la vía
  sin detección no se distinguen de K.
- ARCHIVO:LÍNEA: `frontend/index.html:4361-4372` (encabezados del CSV, sin `via_codigo_mirova` ni `regimen`);
  `grep -c via_codigo_mirova` da 0 en `index.html`, `diario.html`, `mosaico.html` y `comparacion.html`.
- QUÉ PASA: sólo `cambio_detector.js` lee la marca, y sólo para dibujar la fecha. Un record de la vía con detección se
  reconoce por `final_hotspot_source = "codigo_mirova"`; uno sin detección o una caída a K (`"sin_mxd03"`) no. Es
  MA172-210 de S172, que no había pasado por verificador.
- CÓMO SE VE EN EL DASHBOARD: la tabla y el CSV no dicen qué detector produjo cada pasada MODIS después del
  encendido.
- CÓMO REPRODUCIRLO: `grep -c via_codigo_mirova frontend/*.html`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 170
- TÍTULO: Los filtros de artefacto del tablero, calibrados con K, se aplican a records de la vía cuya magnitud y
  conteo de píxeles salen de conjuntos distintos.
- ARCHIVO:LÍNEA: `frontend/index.html:1336-1363` (`isCirrusArtifact`: t_max < 273,15 K y más de 10 MW;
  `isDiffuseFieldArtifact`: n_pixels de 100 o más y VRP/px < 1); en la vía `pc.vrp_mw` es la unión de todos los
  alertados y `pc.n_pixels` es sólo el cúmulo (`pipeline/mirova_v750_codigo.py:735-737`).
- QUÉ PASA: el filtro de campo difuso divide la magnitud de la unión por los píxeles del cúmulo, así que se dispara
  menos. El de cirrus podría ocultar un record de la vía no confirmado por MIROVA con pico frío y más de 10 MW. En los 5
  casos sintéticos ninguno marcó artefacto.
- CÓMO SE VE EN EL DASHBOARD: un record de la vía podría ocultarse del gráfico, o no ocultarse cuando K sí lo habría
  ocultado.
- CÓMO REPRODUCIRLO: no reproducido; habría que construir un record de la vía con t_max < 273 K y más de 10 MW.
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 1.

## 6. SEGUIMIENTOS (fuera de mi eje)

- La vía publica como «summit a 0,318 km» una magnitud que incluye fuentes lejanas: en V2, 14,302 MW, frente a los
  8,962 MW del cráter solo (V1), con un foco de 290 K a 15 km. Es el diseño (D32: MIROVA suma todos los alertados;
  `pipeline/mirova_v750_codigo.py:690-692`), pero el operador ve un número de cráter que en parte no es del cráter.
  Confianza: CONFIRMADO en el caso sintético; decide Nicolás si el tablero lo dice.
- `backfill-tier-a.yml` y `reproc-chunked.yml` siguen pasando `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` (A71), según
  el informe del implementador; no lo re-verifiqué.
- Rama `claude/s172-sombra-34` (`28183712a`): toca `tests/test_sombra_codigo_mirova_s167.py`, que B también toca. La
  simulación de la sección 7 da merge y revert limpios en los dos órdenes.

## 7. VERIFICADO LIMPIO

- **pyproj en los workflows que corren la vía.** Vara: perfiles resueltos con `pipeline.profile` (no el YAML), cruzados
  con las líneas `pip install` no comentadas. `censo_workflows.py` → `wf_B.out`: 32 workflows con la vía en MODIS y 0
  que corran el pipeline sin pyproj. Control rojo: los mismos perfiles contra los workflows de la base dan 24 sin
  pyproj (`wf_base.out`).
- **Los arreglos de MA172-101, 102 y 103 con la vía encendida** (sección 3). Vara: código real de B, predicado del
  tablero por node, control positivo con `ctx_cluster` y con un record de K que calla.
- **La guardia es K.** Vara: todas las constantes de `pipeline.profile`. Frente a producción en B difiere sólo en
  `ENABLE_MODIS_CODIGO_MIROVA`, `DATA_SUBDIR`, `PROFILE_NAME` y los dos sensores VIIRS; en A, sólo en los tres últimos
  (`diff_perfiles_B.txt`, `diff_perfiles_A.txt`). `VALID_PROFILES` sale distinto en todos los pares, también en
  producción contra sí misma, por el orden del `set`: es ruido del instrumento, no una diferencia.
- **Las cuatro vistas publican igual un record de la vía** (V1 a V4 y el control, en index, diario, mosaico y
  comparación): la de cráter se publica con 8,962 MW; la que sólo tiene un foco lejano no se publica (summit false,
  magnitud 0); la que no tiene detección no es válida (`vistas_via_salida.txt`).
- **Pruebas de mi eje.** 75 archivos con `-p no:cacheprovider` y basetemp en D:. B: 1065 pasan, 15 omitidas, 1 xfail y
  0 fallan (`pytest_B.txt`). A, con los 72 que existen en A: 1051 pasan, 15 omitidas, 1 xfail y 0 fallan
  (`pytest_A.txt`). Las 14 de diferencia son los tres archivos que sólo existen en B.
- **Revert limpio en presencia de la rama de la sombra de los 34.** Merges locales en mi worktree, sin push, sobre
  origin/main `47cdc446f`:
  - orden 1, main + A + B + sombra34: el revert del merge de B sale limpio;
  - orden 2, main + A + sombra34 + B: el revert sale limpio y el árbol queda igual al de antes de B (diff vacío sin
    `data/`).

  Salida en `sim_revert_con_sombra34.txt`; pruebas sobre el árbol revertido del orden 2 en
  `pytest_postrevert_orden2.txt`: 73 archivos (los 72 de A más `tests/test_sombra_34_s172.py`), 1152 pasan, 15
  omitidas, 1 xfail y 0 fallan.
- **El almacén no pisa el ancla de la vía.** La lista `_honest_anchor_sources` de `pipeline/store.py:413` no trae
  `codigo_mirova`, pero el rescate está detrás de `not _via_mirova` (l. 401). Vara: lectura, y el record V2 pasado por
  `store.append_record` conserva `final_hotspot_source = "codigo_mirova"` (`vistas_via.json`).

## 8. SIN DATO

- Conducta de las vistas y de las vigilancias con records reales de la vía: no existe ninguno.
- CI del PR B en GitHub: no lo consulté.
- Una excepción real de la vía en el runner (hallazgo 164): no se puede provocar sin pyhdf.
- La vigilancia de la guardia tras el revert: sólo leída (con el flag apagado `avisos_via` devuelve [], l. 345-348); no
  la ejecuté sobre datos con records de la vía.

## 9. FUERA DE ALCANCE

- Tiempos del NRT con la vía, crons, concurrencia, lector de V375-E, la regla de reversión y sus cotas.
- Lo que hace la vía por dentro (detector, fondo, suma).
