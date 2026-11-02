# Lanzamiento de VRP Chile a los 34 volcanes fuera del cron: plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** publicar en el tablero los volcanes que hoy no corren en el NRT, con el mismo detector que los 11 Tier A, sólo
después de tener evidencia de que en los 11 estamos funcionando igual que MIROVA.

**Architecture:** cuatro compuertas en serie. Fase 0 junta la evidencia de paridad en los 11 (prueba retrospectiva del
paquete de las tres vías, más las sombras prospectivas que ya corren). Si la retrospectiva cumple, la Compuerta A abre
una sombra aislada de los 34 (perfil y carpeta propios, workflow propio, sin tocar `nrt.yml`, `volcanoes.yaml`,
`grillas_mirova.yaml` ni `pipeline/*.py` mientras corran las sombras de noviembre). Si las sombras prospectivas de los
11 confirman y la sombra de los 34 pasa la revisión del experto, la Compuerta B abre la publicación, rotulada «sin
referencia de MIROVA, paridad no medida».

**Tech Stack:** `scripts/run_pipeline.py` con perfiles YAML (`extends`, `volcano_overrides`), GitHub Actions
(`ubuntu-24.04`, MODIS sólo en Linux), evaluadores existentes (`scripts/clase_mirova.py`, `banco_paridad`), referencia
de MIROVA (tabla del scraper Mirova-v1 y OSF v2.5), frontend estático en tres vistas.

**Estado del documento:** PLAN, sin implementar. Escrito el 2026-11-02 (00:40 a 02:00 UTC) por un agente planificador
de S172, a pedido de Nicolás (2026-11-01: «Sí, prepáralo») y con su corrección del 2026-11-02 ~00:30 UTC: «la idea es
lanzar los 34 que faltan cuando ya sepamos que estamos funcionando igual que MIROVA». No se tocó el repo, no se
despachó nada. Insumos guardados en `D:\vrp-trabajo\temporales\s172_plan_34\`.

---

## 0. Calendario en una pantalla (UTC, estimado)

| fecha | hito | decide |
|---|---|---|
| 2026-11-02 a 11-05 | pre-registro de la prueba retrospectiva, lector, perfil y workflow (PR con tag) | Nicolás: sello y frase de merge |
| 2026-11-03 | V750-B se despacha (ya planificado); primera noche de la sombra prospectiva de los 11 | nadie |
| ~2026-11-04 a 11-06 | lectura de V750-B y merge de `roi_v750` (excepción permitida al congelamiento) | Nicolás |
| ~2026-11-07 | humo y tanda 1 de la retrospectiva (febrero y marzo de 2026 más el control dentro de muestra) | loop |
| ~2026-11-08 a 11-10 | tanda 2 (2025, contra el OSF v2.5) | loop |
| **~2026-11-12** | **evidencia retrospectiva**: lectura sellada y verificador limpio de otro modelo | loop |
| **~2026-11-13** | **Compuerta A**: ¿se abre la sombra de los 34? | **Nicolás** |
| ~2026-11-14 a 11-16 | línea base retrospectiva de los 34 con K (febrero y marzo de 2026) y umbrales de volumen | loop |
| ~2026-11-17 | sombra prospectiva de los 34, etapa K | Nicolás (frase de merge del workflow) |
| 2026-11-27 | rotar `EARTHDATA_TOKEN` (vence 2026-12-07 18:03) | **Nicolás** |
| ~2026-11-30 a 12-08 | paradas de las sombras prospectivas de los 11 (MODIS, VIIRS 375, VIIRS 750) | Nicolás (A45 por sensor) |
| ~2026-12-08 | grillas de los 34 y cambio de la sombra de los 34 a las vías | Nicolás (tag) |
| ~2026-12-22 | fin de la sombra de los 34 (mínimo 14 noches con el detector final) | loop |
| **~2026-12-29** | **Compuerta B**: ¿se publican los 34? | **Nicolás** |
| ~2027-01-05 | publicación en el tablero, ficha SDA y aviso a consumidores | Nicolás (A45) |

Rango honesto: la evidencia retrospectiva puede correrse al 2026-11-16 si V750-B se atrasa o NASA corta; la Compuerta B
puede adelantarse al ~2026-12-15 si Nicolás acepta K como detector final de los 34 en algún sensor (decisión D6), o
atrasarse a enero por las fiestas.

---

## 1. Por qué este orden

**El fenómeno.** En los 34 volcanes hay de todo: campos fumarólicos persistentes en el norte (Guallatiri, Irruputuncu,
Putana, Ollagüe), un campo geotermal (Tolhuaca), calderas grandes con lagos o hielo (Laguna del Maule, Sollipulli,
Hudson), conos nevados de cumbre fría con valles tibios abajo (Osorno, Calbuco, Lanín). Casi todos pasan la mayoría de
las noches sin nada que un satélite de 375 m a 1 km pueda ver. Ahí un detector que confunde el gradiente topográfico
nocturno (A69), el borde de una nube o el lago que retiene calor con una anomalía volcánica no tiene a nadie que lo
corrija: MIROVA no mira esos volcanes, así que no hay hoja de respuestas.

**El costo de cada error.** El geólogo de turno del OVDAS lee el tablero como leería a MIROVA. Un punto rojo sobre un
volcán que nadie venía mirando puede mover una alerta; un silencio donde había calor real esconde una anomalía. En los
11 Tier A los dos errores se miden contra MIROVA todos los días. En los 34 no se pueden medir, sólo acotar.

**Por eso la paridad va primero.** La única garantía que podemos dar en los 34 es indirecta: «este es el mismo detector
que, en los 11 volcanes donde se puede medir, publica lo que MIROVA publica y calla donde MIROVA calla». Si esa
afirmación no está demostrada en los 11, en los 34 publicaríamos un detector sin ninguna garantía. La ventana de abril
de 2026 muestra cómo se ve eso: con el detector de entonces y radio de 5 km, los 34 dieron 476 records con magnitud en
8 noches, hasta 157 MW en Laguna del Maule, una caldera sin erupción (§2, hecho H5).

**Por qué la retrospectiva adelanta la evidencia.** Las sombras prospectivas de los 11 llegan a su parada entre el 30 de
noviembre y el 8 de diciembre. Reprocesar el histórico de los 11 con el paquete completo (las tres vías encendidas) da
en unos 10 días una evidencia sobre ventanas que ninguna regla vio: febrero y marzo de 2026 contra la tabla de MIROVA,
y 2025 contra el OSF v2.5. Con eso se puede abrir la sombra de los 34 en paralelo con las sombras de los 11, en vez de
en serie: se ganan unas cuatro semanas.

**Por qué la sombra prospectiva sigue siendo la prueba final aunque la retrospectiva salga bien.**
1. **Otro régimen.** Desde el 2026-11-02 13:00 UTC no hay Suomi NPP: VIIRS queda con NOAA-20 y NOAA-21. Todo el
   histórico tiene tres satélites; una anomalía débil vista por una sola pasada tenía más oportunidades que ahora.
2. **Otro camino de datos.** La retrospectiva lee gránulos estándar reprocesados; el NRT lee productos de LANCE con
   latencia, cortes de NASA, cron atrasado y ventana de 8 días. La retrospectiva prueba el algoritmo; la sombra prueba
   el sistema que va a publicar.
3. **Otra referencia.** El OSF v2.5 está filtrado (clase automática DBSCAN, A105): sirve para magnitud y para sus
   alertas, no para contar publicaciones de más, porque una noche ausente del OSF no prueba que MIROVA haya callado. La
   tabla de febrero y marzo arrastra los reparos de A119. Sólo la ventana P compara contra el MIROVA vivo de hoy, con
   negativos limpios.
4. **Las reglas ya lo dicen.** V750-A §4.3, V375-E §3.3 y MOD-D fase 4 §12.6 piden la sombra prospectiva como prueba
   confirmatoria. Cambiar la prueba final después de ver un resultado favorable sería exactamente el error que A95 y
   A115 prohíben.
5. **Lo que se eligió con datos.** La ROI de VIIRS 750 y la regla de posición se eligen sobre la ventana O. La
   retrospectiva las prueba fuera de esa ventana, pero sólo la sombra las prueba en pasadas que nadie había visto al
   escribir la regla.

O sea: la retrospectiva basta para **abrir la sombra** de los 34 (que no publica); no basta para **publicar**.

---

## 2. Hechos comprobados que usa el plan

| # | hecho | evidencia |
|---|---|---|
| H1 | `volcanoes.yaml` tiene 45 volcanes: 11 con `radius_km: 25` e `inner_radius_km` del KML de MIROVA, 34 con 5 km y sin `inner_radius_km`; los 45 con `active: true` | `git show origin/main:volcanoes.yaml`, parseado; copia en `volcanoes_main.yaml` |
| H2 | **MIROVA vigila en su NRT sólo los 11 chilenos.** `latest.php` del 2026-11-01 (06:36 a 23:00 UTC) trae 528 filas, las 3 últimas pasadas de cada uno de 176 volcanes, incluidas las de VRP 0; los únicos chilenos son los 11 Tier A | `latest_php_20261101_2333.html` (descargado de `https://www.mirovaweb.it/NRT/latest.php`); el scraper `Mirova-v1/scraper.py` filtra a sus 11 IDs y no guarda el resto |
| H3 | El OSF v2.5 (2000 a 2025-12-31) tiene filas de sólo 10 volcanes chilenos: los Tier A **sin Tupungatito** (0 filas). En 2025: 2.573 filas de 375 m, 78 de 750 m y 283 de 1 km; 477, 78 y 200 de 1 MW o más | `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (local, fuera de git), conteo propio |
| H4 | En `grillas_mirova.yaml` hay grilla sólo para los 11. La regla GEO: centros de celda en X0 ± 25 km; en 8 de 11 (X0, Y0) es el lat/lon del yaml, en Láscar, Planchón-Peteroa y Tupungatito otro punto (233 m a 2,8 km) | cabecera de `pipeline/grillas_mirova.yaml` |
| H5 | **La ventana de abril de los 34 no sirve para fijar umbrales**: 8 noches (2026-04-17 a 04-24), 2.843 records escritos por el NRT del 2026-04-25 con el detector de entonces, sin `primary_cluster` ni `distance_class`, radio 5 km. 476 con magnitud mayor que cero; máximo 157 MW en Laguna del Maule | `abril/resumen_abril_34.json` |
| H6 | El perfil `sombra_codigo_mirova` enciende las tres vías y escribe en `data/sombra_codigo_mirova/`, que lee el lector sellado de V375-E. Corre una vez al día, `max-parallel: 4` | `pipeline/profiles/sombra_codigo_mirova.yaml`, `.github/workflows/sombra-codigo-mirova.yml` |
| H7 | **`extends` resuelve un solo nivel.** Un perfil que extiende `sombra_codigo_mirova` no hereda `mirova_equivalent` (la clave `extends` del padre queda sin resolver). Todo perfil nuevo extiende `mirova_equivalent` y repite los flags | `pipeline/profile.py` l. 47 a 67 |
| H8 | `volcano_overrides` de un perfil cambia la geometría de un volcán sin tocar `volcanoes.yaml` | `scripts/run_pipeline.py`, `apply_volcano_overrides` |
| H9 | El lector de V375-E (tag `s170-v375e-lector`) marca régimen si cambia **cualquier byte** de `volcanoes.yaml`, el AST de un `.py` de `pipeline/` o de `scripts/run_pipeline.py`, el workflow de la sombra, los dos perfiles de régimen, o `grillas_mirova.yaml` fuera de `roi_v750` y `roi_modis` (agregar volcanes cuenta). **No** marca un perfil nuevo en `pipeline/profiles/` ni un workflow nuevo, y `nrt.yml` no está en la lista | `leer_sombra_v375e.py` l. 95 a 98 y 398 a 413 |
| H10 | `reproc-chunked.yml` no instala `pyproj` (la vía lo necesita para remuestrear), pasa usuario y clave de Earthdata además del token (A71 lo prohíbe en workflows nuevos) y su job `merge` empuja a `main` | `.github/workflows/reproc-chunked.yml` l. 127 a 134 y 170 a 280 |
| H11 | Capacidad: el NRT de los 11 tarda 16,7 min de mediana por job; con 45 jobs y `max-parallel: 8` la corrida dura 96 a 104 min contra un ciclo efectivo de 60 min; los 34 en un workflow aparte con `max-parallel: 8` dan 74 a 81 min (ventana de 8 días). Agregar volcanes sólo a la matriz de `nrt.yml` deja jobs verdes que no procesan nada (dos listas `contains(fromJson(...))`). Tope de 20 jobs simultáneos del plan Free: plan SIN DATO | `D:\vrp-trabajo\temporales\s172_capacidad_nrt\INFORME.md` |
| H12 | Precedente de reproceso: el histórico con K (2025-02-15 a 2026-09-17, 11 volcanes) fueron 176 trozos de a 8, estimado 28 a 35 h | `tasks/LOOP_OBJETIVOS.md` l. 372 a 376 (`origin/loop/activo`) |
| H13 | La lista de 43 del workspace es la de la RNVV de SERNAGEOMIN (API `rnvv-backend.sernageomin.cl`, 2026-10-29), la misma que usan NHI-Tool y Landsat-v1 | `Volcanologia/WEBRNVV/fichas_nuevas_json/_lista.json`; `NHI-Tool/config_nhi.py`; `ARSAND/docs/tipos-volcan-chile.md` l. 31 |
| H14 | Vecinos a menos de 25 km: Descabezado Grande y Cerro Azul-Quizapu 8,2 km; Lonquimay y Tolhuaca 9,6; Chaitén y Michinmahuida 17,5; Villarrica y Quetrupillán 19,8; Puyehue-Cordón Caulle y Antillanca 20,2; Irruputuncu y Olca-Paruma 24,1; Quetrupillán y Lanín 24,2; Copahue y Callaqui 24,5 | haversine sobre `volcanoes.yaml` |
| H15 | Tasa de publicación de K en negativos limpios de los 11 (pasadas en que MIROVA miró y no vio nada): VIIRS 375 2,5 y 3,7 %, MODIS 0,8 y 0,9 %, VIIRS 750 0,9 y 1,1 % (dos ventanas) | `docs/FICHA_SDA_VRP_CHILE.md` v1.9; `experiments/_s153_fk_v2/v1.log`, `v2.log` |

---

## 3. Qué ventanas están dentro de muestra (para la prueba retrospectiva)

Una ventana «dentro de muestra» es una que alguien miró para escribir una regla. Medir ahí reproduce, no prueba.

| ventana | fechas | quién la usó para diseñar | referencia de MIROVA | rol en la retrospectiva |
|---|---|---|---|---|
| R25 | 2025-02-15 a 2025-12-31 | ninguna regla de las vías ni la de K. La miraron diagnósticos (A99, pareo de magnitud contra el OSF de 2025) y S14 calibró `WOOSTER_COEFF` contra el OSF v2.5 | OSF v2.5, filtrado, no NRT (A105). Sin Tupungatito | **decide sólo P1-OSF** (alertas del OSF de 1 MW o más) y **magnitud**; no decide conteos de publicación |
| F26 | 2026-02-01 a 2026-03-31 | VIIRS: ninguna regla de las vías (T de V750-B, V750-A y V375-E empieza el 04-01); K usó marzo (V2: 03-01 a 06-12). MODIS: MOD-D usó marzo (tramo C desde 03-01), febrero no | tabla del scraper sola (OCR inestable hasta el 02-24, A119); Tupungatito sin filas antes del 02-14 | **decide todo** (P1, Muy Bajo, negativos limpios, magnitud) en VIIRS 375 y VIIRS 750 de febrero y marzo, y en MODIS de febrero; MODIS de marzo, sólo control |
| E26 | 2026-01-01 a 2026-01-31 | nadie | A119: «enero no se usa» (corrección D5: 99 % sin Tupungatito) | fuera (decisión D7) |
| DM | 2026-03-01 a 2026-11-02 | K (V2 03-01 a 06-12, V1 08-29 a 10-08), MOD-D (C 03-01 a 10-16, E 10-17 a 10-26), V750-B y V750-A (04-01 a 11-02), V375-E (04-01 a 10-21 y corrida lejana) | tabla y OCR | **control de montaje**: sólo 2026-10-01 a 10-16, donde se solapan los tres pre-registros. Tiene que reproducir lo que esos A/B ya midieron; si no, el montaje está roto y no se lee lo demás |
| P | desde 2026-11-03 | nadie (prospectiva) | tabla viva, sin Suomi NPP | prueba final (sombras de los 11) |

Poder aproximado en F26 (filas de la tabla, día y noche sin separar, sin regla SN ni N-3; el pre-registro los recalcula
con `banco_paridad`): alertas de 1 MW o más en febrero y marzo, 34 de VIIRS 375 y 30 de VIIRS 750; en MODIS de
febrero, 7. **MODIS tiene poco poder fuera de muestra con la tabla**: su evidencia retrospectiva descansa en R25 (200
filas del OSF de 1 MW o más) y en la lectura de MOD-D fase 4.

---

## 4. Archivos que se crean o cambian (mapa)

Fase 0 (no toca producción):
- Crear `experiments/_s172_retro_paquete/PREREGISTRO_RETRO.md`: reglas, ventanas, controles, sellado antes de correr.
- Crear `experiments/_s172_retro_paquete/leer_retro.py`: lector sellado (reusa `scripts/clase_mirova.py` y `banco_paridad`).
- Crear `experiments/_s172_retro_paquete/osf_referencia.py`: adaptador del OSF v2.5 a pasadas pareables.
- Crear `experiments/_s172_retro_paquete/controles_via.py`: cuenta records de la vía por sensor (vigilante contra la vuelta silenciosa a K).
- Crear `pipeline/profiles/_s172_retro_paquete.yaml` y `tests/test_perfil_retro_paquete_s172.py`.
- Crear `.github/workflows/reproc-retro-paquete.yml` (copia de `reproc-chunked.yml` con `pyproj`, sólo token, sin push).

Fase 1 y 2 (sombra de los 34, no toca producción):
- Crear `pipeline/profiles/sombra_34.yaml` y `tests/test_perfil_sombra_34_s17x.py`.
- Crear `.github/workflows/sombra-34.yml`.
- Crear `experiments/_s17x_sombra_34/PREREGISTRO_SOMBRA_34.md`, `revision_semanal.py`, `linea_base_34.py`.
- Crear (borrador, sin merge hasta las paradas) `experiments/_s17x_sombra_34/grillas_34_borrador.yaml` y `generar_grillas_34.py`.

Fase 4 (producción, A45):
- Cambiar `volcanoes.yaml` (radio, `inner_radius_km` y una marca `referencia_mirova: false` en los nuevos).
- Cambiar `pipeline/grillas_mirova.yaml` (agregar los nuevos con la regla GEO).
- Crear `.github/workflows/nrt-red-ampliada.yml` (no se toca `nrt.yml`).
- Crear `frontend/red_ampliada.js` y agregar su `<script>` en `index.html`, `diario.html`, `mosaico.html`.
- Mover los JSON de abril de los 34 de `data/mirova_equivalent/` a `data/_archivo_abril_2026_34/` (A38).
- Cambiar `docs/FICHA_SDA_VRP_CHILE.md` y, en el workspace, `MAPA_WORKSPACE.md`.

---

## 5. Fase 0: evidencia de paridad en los 11 Tier A

### Tarea 0.1: pre-registro de la prueba retrospectiva

**Files:** Create `experiments/_s172_retro_paquete/PREREGISTRO_RETRO.md`

**Por qué.** Sin una regla escrita antes de ver los datos, un resultado favorable se lee a favor y uno desfavorable se
explica (A115, A95). La retrospectiva no inventa reglas: aplica, por sensor, la regla de adopción que ya está sellada.

- [ ] **Paso 1: escribir la cabecera de procedencia.** Commit de `main` del que sale el código, tags de las tres reglas
  que se reusan, sha256 de la referencia congelada (tabla del día y OSF local), y la frase: «este pre-registro se
  escribe después de conocer las lecturas dentro de muestra de K, MOD-D fase 4 y V750-B; decide sólo sobre R25 y F26».
- [ ] **Paso 2: copiar la tabla de ventanas del §3 de este plan**, con lo que decide cada una.
- [ ] **Paso 3: fijar la regla por sensor**, sin cambiar una coma de la original:
  - MODIS: tabla de decisión del §7 de `experiments/_s166_modd_f4/PREREGISTRO_MODD_F4.md` (rama
    `claude/s170-modd-f4-procedencia`, `25e3cc3ba`), con P1 y P2', aplicada a F26 febrero.
  - VIIRS 375: §5.4 de `experiments/_s162_v375/PREREGISTRO_E.md` con N-3, aplicada a F26.
  - VIIRS 750: §6 de `experiments/_s162_v750a/PREREGISTRO_V750A.md` si está sellado el día del sello de la
    retrospectiva; si no, ese §6 copiado tal cual y sellado con esta retrospectiva, con la ROI que eligió V750-B.
  - Brazo de posición: el que eligió cada pre-registro; si alguno no eligió todavía, «radiante» (lo que hace hoy
    `procesar_grilla`) y los otros dos se informan.
- [ ] **Paso 4: fijar la lectura de R25 contra el OSF**, antes de leer el OSF con el código:
  - Antes de usar una columna, leer su definición en Coppola et al. 2026 (Scientific Data) renderizando la página a
    imagen (A95): `Dayflag`, `Max_Dist` (unidades), `class`, `Resolution`. Mientras no esté leída, la columna no se usa.
  - Pareo: misma resolución (375 a VIIRS 375, 750 a VIIRS 750, 1000 a MODIS), ±120 s, mismo volcán.
  - **P1-OSF**: toda fila del OSF de 1 MW o más dentro del radio interno es una «protegida OSF». Si la vía no la publica
    (predicado del tablero, A97) y K sí: candidata a veto, se diagnostica (cabecera de la imagen, A61) y **decide
    Nicolás**, porque el OSF no es el NRT. Si ni la vía ni K la publican, se informa.
  - **Magnitud**: razón vía/OSF por pasada pareada, mediana y cuartiles por sensor, volcán y tramo de 10° de cenit, al
    lado de K/OSF. Informa; no decide. Ojo declarado: `WOOSTER_COEFF` se calibró contra el OSF (S14), así que la razón
    de K no es independiente; la de la vía lo es sólo si la vía no usa ese coeficiente (comprobar en el código y
    escribirlo en el pre-registro).
  - Tupungatito no tiene filas en el OSF: queda SIN DATO en R25.
- [ ] **Paso 5: fijar los controles** (si uno falla, no se lee el veredicto):
  - C-via: en cada sensor, al menos 99 % de los records de la vía con `via_codigo_mirova: true`; se cuentan aparte
    `"sin_grilla"` y `"sin_mxd03"`. Un 0 % significa que la vía no corrió (por ejemplo, sin `pyproj`).
  - C-cobertura (A108): pasadas por volcán, día y sensor contra el histórico K de `data/mirova_equivalent/`; un día con
    menos pasadas que K se repite una vez y, si sigue, se declara SIN DATO en la primera línea.
  - C-montaje: en DM (2026-10-01 a 10-16) la vía reproduce, pasada por pasada, los records de las corridas de MOD-D
    fase 4, V750-B y V375-E donde el código es el mismo; cada diferencia se explica antes de leer R25 y F26.
  - C-placebo: K × 1,2 obligatorio (programa §2).
  - C-nulo (A110, A116): el lector corrido sobre K contra K da 0 diferencias, y sobre una mutación que pierde una
    protegida da veto.
- [ ] **Paso 6: escribir el veredicto posible**: CUMPLE, NO CUMPLE (veto), INDECIDIBLE (controles), DECIDE NICOLÁS, por
  sensor. Y qué abre cada uno (§5, Compuerta A).
- [ ] **Paso 7: verificador limpio de otro modelo** sobre el pre-registro (recibe sólo título, ruta y reglas
  reusadas). Aplicar sus hallazgos.
- [ ] **Paso 8: sello.** Frase de Nicolás; commit del pre-registro en `loop/activo` con marca SELLADO, tag
  `s172-retro-prereg-sellado`.

### Tarea 0.2: perfil y workflow de la retrospectiva

**Files:**
- Create `pipeline/profiles/_s172_retro_paquete.yaml`
- Create `tests/test_perfil_retro_paquete_s172.py`
- Create `.github/workflows/reproc-retro-paquete.yml`

**Por qué aparte.** La sombra escribe en `data/sombra_codigo_mirova/` y su lector la lee: mezclar ahí pasadas de 2025
rompería su control de claves (S1) y abriría la carrera de A47. Y `reproc-chunked.yml` sin `pyproj` haría volver la
vía a K en silencio (H10).

- [ ] **Paso 1: tag defensivo** antes del primer edit (A45, aunque no toca producción):
  `git tag pre-s172-retro-paquete origin/main && git push origin pre-s172-retro-paquete`.
- [ ] **Paso 2: escribir la prueba que falla.**

```python
# tests/test_perfil_retro_paquete_s172.py
"""El perfil de la retrospectiva es la sombra con otra carpeta, y nada más (H7: extends resuelve un nivel)."""
import importlib
import os
import sys



def _puede_diferir(nombre):
    """Sólo la identidad del perfil y su carpeta."""
    return nombre.startswith("PROFILE") or nombre == "DATA_SUBDIR"


def _constantes(perfil):
    os.environ["VRP_PROFILE"] = perfil
    for m in [k for k in sys.modules if k == "pipeline.profile"]:
        del sys.modules[m]
    p = importlib.import_module("pipeline.profile")
    return {k: getattr(p, k) for k in dir(p) if k.isupper()}


def test_retro_igual_a_sombra_salvo_carpeta():
    sombra = _constantes("sombra_codigo_mirova")
    retro = _constantes("_s172_retro_paquete")
    distintas = {k for k in sombra.keys() | retro.keys()
                 if sombra.get(k) != retro.get(k) and not _puede_diferir(k)}
    assert distintas == set(), distintas
    assert retro["DATA_SUBDIR"] == "_s172_retro_paquete"
    assert retro["ENABLE_V750_CODIGO_MIROVA"] and retro["ENABLE_V375_CODIGO_MIROVA"] and retro["ENABLE_MODIS_CODIGO_MIROVA"]
```

- [ ] **Paso 3: correrla y ver que falla**: `pytest tests/test_perfil_retro_paquete_s172.py -v`. Esperado: FAIL,
  `VRP_PROFILE='_s172_retro_paquete' is not a known profile`.
- [ ] **Paso 4: escribir el perfil.**

```yaml
# pipeline/profiles/_s172_retro_paquete.yaml
# S172. Prueba retrospectiva del paquete (las tres vías «código MIROVA») sobre el histórico de los 11 Tier A.
# POR QUÉ: adelantar la evidencia de paridad antes de la parada de las sombras (PLAN de los 34, §5).
# IDÉNTICO a sombra_codigo_mirova salvo nombre y carpeta (lo vigila tests/test_perfil_retro_paquete_s172.py).
# extends resuelve UN nivel (pipeline/profile.py): por eso extiende mirova_equivalent y repite los flags de la sombra.
# NO OPERACIONAL: carpeta aislada (A47); no la lee el tablero ni el lector de la sombra.
extends: mirova_equivalent
profile: _s172_retro_paquete
description: >
  Retrospectiva del paquete de las tres vías sobre el histórico de los 11 Tier A, en carpeta propia.

thresholds:
  enable_v750_codigo_mirova: true
  enable_v375_codigo_mirova: true
  enable_modis_codigo_mirova: true

paths:
  enable_test1_path: false
  enable_tests_23_prose_branch: true

sensors:
  modis: true
  viirs_375: true
  viirs_750: true

output:
  data_subdir: _s172_retro_paquete

enable_modis_b22_primary: true
```

- [ ] **Paso 5: correr la prueba nueva y la suite de guards de perfiles**:
  `pytest tests/test_perfil_retro_paquete_s172.py tests/test_guard_perfiles_congelados_s153.py tests/test_guard_laboratorio_no_mas_ciego_s147.py -v`.
  Esperado: PASS. Después, la suite completa sobre un árbol quieto (A112).
- [ ] **Paso 6: escribir el workflow** copiando `reproc-chunked.yml` con cuatro cambios, y nada más:
  1. `pip install pyhdf earthaccess numpy h5py scipy pyyaml pyproj`;
  2. `env:` sólo con `EARTHDATA_TOKEN`, más el corte inmediato si viene vacío (bloque de `sombra-codigo-mirova.yml`);
  3. sin job `merge`: cada trozo sube su carpeta como artifact (`retention-days: 30`) y la unión se hace local;
  4. `max-parallel: 6` (NRT 8 + sombra 4 + experimental 4 + 6 = 22 sólo si coinciden los cuatro; en la franja del
     NRT, 01 a 12 UTC, son 8 + 6 = 14). Grupo `reproc-retro-paquete`, `"on":` entre comillas (A43), `ubuntu-24.04`.
  Y un paso que imprime, por trozo, el conteo de `controles_via.py` en el log.
- [ ] **Paso 7: escribir `controles_via.py`.**

```python
# experiments/_s172_retro_paquete/controles_via.py
"""Cuenta records por sensor y estado de la vía. Uso: python controles_via.py <carpeta_de_jsons>"""
import collections
import json
import pathlib
import sys


def sensor(nombre):
    if nombre.startswith("MODIS"):
        return "MODIS"
    return "V750" if nombre.endswith("_750") else "V375"


def contar(carpeta):
    c = collections.Counter()
    for f in sorted(pathlib.Path(carpeta).glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            c[(sensor(r["sensor"]), str(r.get("via_codigo_mirova")))] += 1
    return c


if __name__ == "__main__":
    c = contar(sys.argv[1])
    for s in ("MODIS", "V375", "V750"):
        tot = sum(n for (ss, _), n in c.items() if ss == s)
        via = c[(s, "True")]
        frac = via / tot if tot else 0.0
        print(f"{s}: {via}/{tot} de la via ({frac:.1%}); otros: "
              f"{ {e: n for (ss, e), n in c.items() if ss == s and e != 'True'} }")
        if tot and frac < 0.99:
            print(f"::error::C-via falla en {s}: la via no corrio en {tot - via} records")
            sys.exit(3)
```

- [ ] **Paso 8: commit y PR** (`git add` por archivo; nunca `git stash`):

```bash
git add pipeline/profiles/_s172_retro_paquete.yaml tests/test_perfil_retro_paquete_s172.py \
        .github/workflows/reproc-retro-paquete.yml experiments/_s172_retro_paquete/controles_via.py
git commit -m "S172 retro: perfil aislado y workflow de la prueba retrospectiva del paquete (sin push a main)"
```

  `workflow_dispatch` sólo funciona con el yml en `main` (S73): el PR se mergea con frase de Nicolás y
  `gh pr merge <N> --match-head-commit <sha>`. **No cambia nada de lo que publica producción** y no marca régimen en
  el lector de V375-E (H9: perfil y workflow nuevos).

### Tarea 0.3: humo

- [ ] **Paso 1:** despachar desde el tag del despacho un solo volcán, Láscar, tres días: 2025-06-15, 2026-02-10 y
  2026-10-05 (ventanas R25, F26 y DM), `max_days: 1`.
- [ ] **Paso 2:** esperado: tres artifacts, `controles_via.py` con más de 99 % en los tres sensores, y tiempo por
  volcán y día anotado (hoy SIN DATO para la vía: el informe de capacidad lo acota en 1,06 a 1,25 veces K). Si falla
  C-via, se arregla el workflow y se repite; no se sigue.

### Tarea 0.4: tandas (de a una, desde un tag)

**Por qué en este orden.** F26 tiene negativos limpios y es la única ventana fuera de muestra que puede juzgar la
publicación de más antes de noviembre: va primero. R25 sólo juzga protegidas y magnitud.

- [ ] **Paso 1, tanda 1** (el día siguiente al merge de `roi_v750`, ~2026-11-07): los 11 volcanes, 2026-02-01 a
  2026-03-31 más 2026-10-01 a 10-16. Son 825 volcán-día; a 1,8 a 3,2 min por volcán-día y 6 en paralelo, **4 a 7 h**.
- [ ] **Paso 2, tanda 2** (~2026-11-08): los 11, 2025-02-15 a 2025-12-31: 3.520 volcán-día, **16 a 31 h**.
- [ ] **Paso 3:** antes de mirar ningún veredicto, contar pasadas de cada trozo contra K (A108); trozos cortados por
  NASA (`SEARCH_CMR_TIMEOUT`, A64) se repiten una vez con la misma ventana.
- [ ] **Paso 4:** bajar artifacts a `D:\vrp-trabajo\temporales\s17x_retro\` (parada bajo 3 GB libres en D:), unir por
  volcán en un solo proceso secuencial (A47).

### Tarea 0.5: lectura y verificador

- [ ] **Paso 1:** comprobar con `sha256sum` que cada archivo del lector y de la referencia es el del sello (lección S171).
- [ ] **Paso 2:** correr `leer_retro.py` una sola vez por ventana y guardar la salida entera.
- [ ] **Paso 3:** verificador limpio de otro modelo (recibe ruta de la salida, pre-registro y scripts, no la conclusión).
- [ ] **Paso 4:** informe en `experiments/_s172_retro_paquete/INFORME.md` con el veredicto por sensor, sus números con
  numerador, denominador y ventana, y lo que queda SIN DATO.

**Criterio de salida de la Fase 0 retrospectiva** (escrito antes de ver datos): veredicto leído y verificado en los tres
sensores; los controles C-via, C-cobertura, C-montaje y C-nulo en verde.

### Tarea 0.6: seguimiento de las sombras prospectivas de los 11

No hay trabajo nuevo: se leen con sus lectores sellados en sus paradas (programa §12.7): MODIS ~2026-11-30 (o la regla
de reversión de MOD-D si se adelanta), VIIRS 375 cuando sume 30 noches y 40 alertas (~2026-12-02 o después), VIIRS 750
al menos 4 semanas después del cambio de ROI (~2026-12-04 a 12-08).

### Compuerta A: abrir la sombra de los 34

Se abre si la retrospectiva da, en cada sensor, **CUMPLE** con controles en verde. Si un sensor da NO CUMPLE o
INDECIDIBLE, la Compuerta A **no se abre para ningún sensor** (los 34 se publican con los tres sensores o con ninguno:
un volcán con un sensor apagado se lee como silencio). Lo decide Nicolás con el informe y el verificador.

---

## 6. Fase 1: preparación de los 34 (en paralelo con la Fase 0, sin runner)

### Tarea 1.1: la lista

- [ ] Llevar a Nicolás la decisión D1 (¿43 o 45?, §11) con la comparación de H13. Nada se crea para un volcán que salga.

### Tarea 1.2: geometría de los nuevos

**Por qué.** K y las vías calculan la estadística de fondo sobre la escena de 51 × 51 km de MIROVA; con 5 km de radio
el detector de los 34 no sería el de los 11, aunque el código sea el mismo.

- [ ] **Paso 1:** radio 25 km para todos (decisión D4). En la sombra va por `volcano_overrides` del perfil (H8); en
  `volcanoes.yaml` recién en la Fase 4.
- [ ] **Paso 2:** `inner_radius_km` (decisión D5): 5 km por defecto, que es el valor de 6 de los 11 KML de MIROVA, con
  las excepciones que Nicolás justifique como geólogo (calderas y campos: Laguna del Maule, Sollipulli, Hudson,
  Carrán-Los Venados, Antillanca, Descabezado y Cerro Azul). Cada excepción con su razón escrita, porque no hay valor de
  MIROVA que copiar (A5).
- [ ] **Paso 3:** borrador de grillas con la regla GEO (H4): `generar_grillas_34.py` convierte el lat/lon del yaml a UTM
  (zona 18 o 19 según longitud, como los 11), `roi_v750` con el valor que elija V750-B como general. Se guarda en
  `experiments/_s17x_sombra_34/grillas_34_borrador.yaml`, **sin tocar `pipeline/grillas_mirova.yaml`** (H9). Prueba:
  aplicada a los 8 Tier A cuyo punto es el lat/lon del yaml, reproduce sus (X0, Y0) a 1 m.

### Tarea 1.3: perfil de la sombra de los 34

**Files:** Create `pipeline/profiles/sombra_34.yaml`, `tests/test_perfil_sombra_34_s17x.py`

- [ ] **Paso 1:** tag defensivo `pre-s17x-sombra-34`.
- [ ] **Paso 2:** prueba que falla: el perfil resuelve las mismas constantes que `sombra_codigo_mirova` salvo nombre,
  carpeta y `VOLCANO_OVERRIDES`, y cada override trae `radius_km: 25` e `inner_radius_km` de la Tarea 1.2.
- [ ] **Paso 3:** el perfil (forma; la lista sale de D1):

```yaml
# pipeline/profiles/sombra_34.yaml
# Sombra de los volcanes sin referencia de MIROVA. Mismo detector que la sombra de los 11; geometría de MIROVA por
# override (no toca volcanoes.yaml, que el lector de V375-E compara byte a byte). Mientras no haya grilla, las vías
# vuelven a K y el record lo dice (via_codigo_mirova: "sin_grilla").
extends: mirova_equivalent
profile: sombra_34
description: >
  Sombra aislada de los volcanes sin referencia de MIROVA; no publica.
thresholds:
  enable_v750_codigo_mirova: true
  enable_v375_codigo_mirova: true
  enable_modis_codigo_mirova: true
paths:
  enable_test1_path: false
  enable_tests_23_prose_branch: true
output:
  data_subdir: sombra_34
enable_modis_b22_primary: true
volcano_overrides:
  Antuco: {radius_km: 25, inner_radius_km: 5}
  Calbuco: {radius_km: 25, inner_radius_km: 5}
  # ... una línea por cada volcán de la lista que decida Nicolás (D1), con su inner de D5
```

- [ ] **Paso 4:** prueba en verde, suite completa sobre árbol quieto, commit.

### Tarea 1.4: workflow de la sombra de los 34

**Files:** Create `.github/workflows/sombra-34.yml`

- [ ] Molde `sombra-codigo-mirova.yml` con estos cambios: matriz con la lista de D1; **ventana de 3 días** (no 8: el
  costo dominante es bajar gránulos, H11, y 3 días cubren la latencia de LANCE y el paso a estándar); una corrida al día;
  `max-parallel: 4`; grupo propio y bucle de reintento de push (guard G4); `--volcano X` explícito por job (el script
  respeta el nombre aunque el volcán no sea `mirova_monitored`, H11); y un paso final que falla si el job no escribió
  ningún record nuevo en 3 días seguidos para ese volcán (contra el «job verde sin datos», lección de S141, y H11).
- [ ] Estimado: 34 jobs de unos 6 a 9 min, 50 a 80 min de pared por día. Es SIN DATO hasta el primer despacho; la
  propia sombra lo mide para la Fase 4.

### Tarea 1.5: instrumento de revisión semanal

**Files:** Create `experiments/_s17x_sombra_34/revision_semanal.py`

- [ ] Genera `D:\vrp-trabajo\temporales\sombra_34\REVISION_<fecha>.html` (ruta absoluta para Nicolás) con, por volcán y
  semana: pasadas con dato por sensor, publicaciones (predicado del tablero, A97) por nivel, y para cada publicación:
  posición sobre mapa, coherencia con VIIRS 375 de la misma noche, escena SWIR más cercana y nivel de alerta de la RNVV
  (§8). Una casilla por publicación: real, artefacto, indeterminado.

---

## 7. Fase 2: sombra de los 34

### Tarea 2.1: línea base retrospectiva de los 34 (tras la Compuerta A)

**Por qué.** La ventana de abril no sirve (H5). Antes de mirar hacia adelante conviene ver cómo se comporta el detector
de hoy en estos volcanes, con su geometría de MIROVA, en un tramo conocido.

- [ ] Despachar `reproc-retro-paquete.yml` con el perfil `sombra_34` (carpeta propia), los 34, 2026-02-01 a 03-31:
  2.006 volcán-día, **10 a 18 h**. Las vías corren como K (sin grilla).
- [ ] Salida: publicaciones por volcán, sensor y semana; las de 1 MW o más, a la revisión de Nicolás antes de abrir la
  sombra prospectiva. Un volcán con artefactos sistemáticos (por ejemplo, un lago o una cumbre nevada que publica todas
  las noches) se discute antes, no después.

### Tarea 2.2: pre-registro de la sombra de los 34

- [ ] Escribir y sellar `PREREGISTRO_SOMBRA_34.md` con los criterios del §8, el umbral de volumen de la decisión D10 y
  la regla de salida de la Fase 2. Verificador limpio, frase de sello de Nicolás.

### Tarea 2.3: sombra prospectiva, etapa K (~2026-11-17 a ~12-08)

- [ ] Merge del perfil y el workflow (frase de Nicolás); primer despacho manual de un volcán con `medir`; después, cron
  diario. Revisiones semanales: 2026-11-24, 12-01, 12-08.

### Tarea 2.4: etapa de las vías (~2026-12-08 en adelante)

**Por qué recién ahí.** Las vías necesitan grilla; agregar los nuevos a `grillas_mirova.yaml` marca régimen en el
lector de V375-E (H9) y, SOSPECHA a comprobar, en el de VIIRS 750. Se espera a que los dos lleguen a su parada.

- [ ] Tag `pre-s17x-grillas-34`, PR que agrega los nuevos a `pipeline/grillas_mirova.yaml` desde el borrador de la
  Tarea 1.2, con prueba de la regla GEO; sí de Nicolás (A45: el archivo lo leen las vías de producción si se adoptan).
- [ ] Anotar en la bitácora la noche del cambio. Desde ahí cuentan las noches con el detector final; revisiones
  semanales 2026-12-15 y 12-22.

**Criterio de salida de la Fase 2** (escrito antes de ver datos; los números finos los sella la Tarea 2.2):
1. Al menos 14 noches con el detector final en cada sensor y al menos 90 % de las noches con dato por volcán.
2. Ninguna publicación de 1 MW o más que Nicolás clasifique como artefacto sin explicación física.
3. Cada volcán bajo su umbral de volumen (D10), o sobre él con todas sus publicaciones revisadas y clasificadas.
4. El cuaderno de revisión (§8) completo para todas las semanas.

---

## 8. Cómo se valida sin MIROVA

**Volumen por volcán y semana.** En un volcán tranquilo, casi todas las pasadas son físicamente negativas. Si el detector
se comporta como en los 11, debería publicar en ellas a la tasa de K en negativos limpios (H15). Recomendación (D10):
marcar un volcán cuando sus publicaciones superan el cuantil 99 % de una binomial con esa tasa. Con unas 60 pasadas por
sensor en 4 semanas (dos satélites por noche): más de 6 en VIIRS 375 (tasa 3,7 %), más de 3 en VIIRS 750 (1,1 %), más
de 3 en MODIS (0,9 %). Si la vía de un sensor se adopta, la tasa sale de la lectura que la adoptó. **Marcar no es
excluir**: en los 11, el 95 % de lo que publicábamos de más eran anomalías reales que MIROVA no publica (A54), y en los
fumarólicos del norte se espera eso mismo. Lo marcado va a revisión.

**Revisión del experto (A62).** Nicolás conoce los volcanes: clasifica cada publicación de 1 MW o más y una muestra de
las de Muy Bajo. La pregunta es la del geólogo: ¿hay un objeto térmico ahí (fumarola, domo, lago caliente, campo
geotermal) o es nieve, nube, borde de barrido, lago que guarda el calor de la tarde?

**Coherencia con VIIRS 375 de la misma noche.** Una publicación de MODIS o VIIRS 750 sin nada en VIIRS 375 a menos de
1 km en la misma noche (con pasada VIIRS 375 disponible) es sospechosa: el píxel grande amplifica el gradiente (A80).
Se informa, no excluye: un foco sub-píxel puede caer bajo el umbral de 375 m en una pasada.

**Actividad conocida del OVDAS.** El nivel de alerta técnica de cada volcán está en la API pública de la RNVV (campo
`nivel`, `rnvv-backend.sernageomin.cl:8443/api/volcanes`; su significado exacto, SIN VERIFICAR) y en los reportes de
actividad publicados. Un volcán en verde que publica todas las noches pide revisión; uno en amarillo que calla, también.

**SWIR de alta resolución (A77).** Donde haya escena Sentinel-2 o Landsat a ±3 días sin nube, la salida publicada de
NHI-v1 y Landsat-v1 (consumir su salida, nunca su `data/` por disco: regla 4 del mapa) dice si hay píxeles calientes a
20 a 30 m. Un foco que SWIR ve y VIIRS no es sub-píxel (no es un error del detector); uno que VIIRS publica y SWIR no ve
en noches despejadas cercanas es candidato a artefacto. Cubre los 43 de la RNVV; Tolhuaca, Olca-Paruma, Putana y
Cerro Azul-Quizapu no están en esas listas (H13).

**Vecinos (H14).** Toda publicación de un nuevo cuya posición caiga dentro del radio interno de otro volcán se marca:
puede ser la misma anomalía publicada dos veces (Descabezado y Cerro Azul a 8,2 km; Lonquimay y Tolhuaca a 9,6 km) o
el cráter de un Tier A visto desde la grilla del vecino (Chaitén desde Michinmahuida, Villarrica desde Quetrupillán).

**Umbrales que no salen de datos y quedan para Nicolás:** la fracción de artefactos aceptable en Muy Bajo, y cuántas
semanas sin artefactos de 1 MW o más hacen falta. Recomendación: cero artefactos de 1 MW o más en las dos últimas
semanas, y en Muy Bajo no más artefactos que la tasa de K en negativos limpios de los 11.

---

## 9. Cómo se ve en el tablero

- **Separados de los 11.** Una sección «Red ampliada: sin referencia de MIROVA, paridad no medida», debajo de los 11.
  En los nuevos no se dibuja la serie de MIROVA ni se muestran métricas de paridad; el rótulo va en la tarjeta, en el
  gráfico del diario y en la celda del mosaico.
- **Un solo lugar para el cambio.** Archivo nuevo `frontend/red_ampliada.js` con la lista de los nuevos, el rótulo y la
  fecha de entrada (con su línea vertical, como `cambio_detector.js`). Las tres vistas lo cargan con un `<script>` en la
  misma línea de los otros (para no correr las citas `archivo:línea` que vigila el guard G8) y lo leen en vez de copiar
  la lista. `comparacion.html` no se toca (es preview).
- **Las regiones** de los nuevos salen de `volcanoes.yaml` (guard G9 exige que las tres vistas coincidan).
- **Verificación**: preview real en el navegador de las tres vistas (no `node --check`), en escritorio y celular, y R8
  sobre el sitio publicado después del deploy.

---

## 10. Transparencia algorítmica (Resolución CPLT N°372)

El SDA cambia de alcance: pasa de 11 a 43, 44 o 45 volcanes (D1), y en los nuevos no hay contraste externo. Antes de la
publicación (Fase 4), en el mismo PR:
- `docs/FICHA_SDA_VRP_CHILE.md`: versión nueva con (a) universo de casos y la lista; (b) limitación nueva: «en estos
  volcanes no existe referencia de MIROVA; la paridad se demostró en los 11 Tier A y se supone, no se mide, en los
  demás»; (c) el procedimiento de revisión experta y sus criterios (§8); (d) la evidencia (retrospectiva, sombras de los
  11 y de los 34); (e) la reversión pre-autorizada (D13); (f) la geometría elegida para los nuevos (radio 25, radio
  interno y su razón, grilla por regla GEO, no copiada de MIROVA). Entrada nueva en el historial.
- Cabecera FICHA y comentario «POR QUÉ» en todo archivo nuevo que participe en la decisión (workflow de publicación,
  `red_ampliada.js` si filtra, el perfil).
- `MAPA_WORKSPACE.md` (workspace): ficha de VRP Chile con la salida consumible ampliada, el rótulo, la cadencia del
  workflow nuevo y el aviso a sus consumidores (Integracion_Plataformas, mirova-tif-archive): los nuevos no son
  «equivalentes a MIROVA».
- Aviso humano: Nicolás avisa al OVDAS antes de la publicación (D14).

---

## 11. Decisiones para Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| D1 | **¿43 o 45?** | (a) los 45 del yaml; (b) la lista de 43 de la RNVV (H13) más Lastarria, que es Tier A de MIROVA aunque la RNVV no lo liste: 44, lo que obliga a agregar Tatara-San Pedro, separar Yate de Hornopirén y Macá de Cay, y sacar Tolhuaca, Olca-Paruma, Putana y Cerro Azul-Quizapu; (c) 45 menos dos. **Candidatos a «los dos que sobran»**: Cerro Azul-Quizapu (a 8,2 km de Descabezado Grande, la RNVV los agrupa como «Grupo Descabezados»: con grilla de 51 km verían la misma escena y podrían publicar la misma anomalía dos veces); Tolhuaca (a 9,6 km de Lonquimay, no está en la RNVV, y su campo geotermal es fuente probable de publicaciones que no son volcánicas); Olca-Paruma y Putana (fronterizos, no están en la RNVV). Lastarria no es candidato aunque falte en la RNVV | Preguntarte primero qué querías decir con 43. Si es la lista de la RNVV, la (b): el tablero hablaría la misma lista que vigila el OVDAS. No lo decido |
| D2 | Detector de los nuevos, por sensor | igual al de producción de los 11 el día de la publicación; siempre K; siempre las vías | **Igual al de producción de los 11**: nunca publicar en los nuevos un detector que no esté demostrado en los 11 |
| D3 | Grilla de los nuevos | regla GEO con el lat/lon del yaml; centrada en el cráter; sin grilla (K) | **Regla GEO con el lat/lon del yaml** (8 de 11 Tier A cumplen esa regla a 1 m) |
| D4 | Radio de los nuevos | 25 km (escena de MIROVA); 5 km (hoy) | **25 km**: con 5 km la estadística de fondo es otra y el detector no es el de los 11 |
| D5 | Radio interno de los nuevos | 5 km uniforme; por volcán según la geología | **5 km de partida**, con excepciones tuyas justificadas por escrito en calderas y campos |
| D6 | Si un sensor no se adopta en los 11 (sombra NO CUMPLE) | los nuevos publican K en ese sensor; esperar | Depende de si aceptas K como «igual a MIROVA» en ese sensor (K CUMPLIÓ su regla, #848). Si lo aceptas, la Compuerta B puede adelantarse a ~2026-12-15 |
| D7 | Ventanas de la retrospectiva | febrero y marzo de 2026 más 2025; sólo febrero y marzo; agregar enero | **Febrero y marzo más 2025**. Enero fuera (A119) |
| D8 | Rigor de la Compuerta A | abrir la sombra de los 34 con la retrospectiva; esperar las paradas de los 11 | **Con la retrospectiva**: la sombra no publica y se ganan unas cuatro semanas. Esperar las paradas lleva la publicación a fines de enero |
| D9 | Sombra de los 34 antes de tener grillas | etapa K desde la Compuerta A y cambio a vías tras las paradas; esperar las paradas y partir con vías | **Etapa K y después vías**: da volumen y costo temprano; se cuentan para la salida sólo las noches con el detector final |
| D10 | Umbral de volumen | cuantil 99 % binomial con la tasa de K en negativos limpios (§8); factor fijo sobre esa tasa; sin umbral | **Binomial 99 %**: sale de datos de MIROVA (A115); marcar no es excluir |
| D11 | Cómo correr los nuevos en producción | workflow aparte, cada 3 h, ventana de 3 días, `max-parallel` 4 a 6; meterlos en `nrt.yml` con `max-parallel: 20` | **Workflow aparte**: no arriesga el NRT de los 11 (hoy 33 min de pared contra 60 de ciclo, H11) |
| D12 | Orden en el runner | retrospectiva antes que la corrida de V750-A; al revés | **Tanda 1 de la retrospectiva primero** (4 a 7 h) y V750-A cuando esté sellada; la tanda 2 en el hueco |
| D13 | Reversión de los nuevos | pre-autorizar retirar del tablero un volcán nuevo el mismo día si publica un artefacto de 1 MW o más; caso a caso | **Pre-autorizar**, sin tocar los 11 |
| D14 | Fecha de publicación | antes de las fiestas; primera semana de enero | **Primera semana de enero**, con el OVDAS avisado y alguien mirando el tablero los primeros días |
| D15 | Los JSON de abril de los 34 | archivarlos con tag (A38); borrarlos | **Archivarlos** en `data/_archivo_abril_2026_34/` antes del primer record nuevo: son del detector viejo y se mezclarían con los nuevos |

---

## 12. Qué toca producción (A45: tag defensivo y tu sí ese día)

| paso | toca producción | requisito |
|---|---|---|
| Pre-registro, lector, adaptador del OSF, controles (`experiments/`) | no | tu frase de sello |
| Perfil `_s172_retro_paquete.yaml` y workflow de la retrospectiva | no (carpeta aislada, no lo lee nada) | tag `pre-s172-retro-paquete` y tu frase de merge (el yml tiene que estar en `main`) |
| Despachos de la retrospectiva y de la línea base de los 34 | no (artifacts, sin push) | ninguno; de a uno, desde un tag |
| Perfil `sombra_34.yaml` y workflow `sombra-34.yml` | no (carpeta `data/sombra_34/`, el tablero no la lee) | tag `pre-s17x-sombra-34` y tu frase de merge |
| Grillas de los nuevos en `pipeline/grillas_mirova.yaml` | **sí**: archivo de las vías de producción | tag `pre-s17x-grillas-34`, tu sí; sólo después de las paradas de los lectores |
| Archivar los JSON de abril | **sí** (`data/mirova_equivalent/`) | tag `pre-s17x-archivo-abril-34` (A38), tu sí |
| `volcanoes.yaml` (radio, radio interno, marca) | **sí** | tag `pre-s17x-publicacion-34`, tu sí, después de las paradas |
| Workflow de publicación `nrt-red-ampliada.yml` (escribe en `data/mirova_equivalent/`) con su vigilancia de frescura (A57) y su entrada en `nrt-monitor` | **sí** | mismo tag, tu sí |
| `frontend/red_ampliada.js` y las tres vistas | **sí** | mismo tag, tu sí, preview real |
| Ficha SDA y mapa | sí (documento público del SDA) | en el mismo PR de la publicación |

Lo que no se toca nunca en este plan: `nrt.yml`, `pipeline/profiles/mirova_equivalent.yaml`, `pipeline/*.py`,
`scripts/run_pipeline.py` y `sombra-codigo-mirova.yml`.

---

## 13. Riesgos y cómo se ven si fallan

| riesgo | cómo se ve si falla | defensa |
|---|---|---|
| Vigilante ciego en la retrospectiva: la vía vuelve a K en silencio (sin `pyproj`, sin grilla, sin MxD03) | todo verde, records con `via_codigo_mirova` distinto de `true`, y un «CUMPLE» que mide K | C-via en cada trozo y en la lectura (Tarea 0.2 paso 7) |
| Job verde sin datos en la sombra de los 34 o en la publicación | jobs de 1,5 min «No changes to commit» (pasa si un volcán está en la matriz y no en la lista del paso) | sin listas `contains`; paso que falla si no hay record nuevo en 3 días; frescura A57 por volcán |
| Tiempo del NRT | corridas de los 11 que pasan de 60 min y despachos desplazados en `push-main` | los nuevos nunca en `nrt.yml`; workflow aparte con grupo propio (H11) |
| Tope de 20 jobs simultáneos (plan SIN DATO) | jobs en cola; la sombra de los 11 o la experimental se atrasan | `max-parallel` 6 en la retrospectiva y 4 en la sombra de los 34; horarios fuera de la franja 01 a 12 UTC cuando se pueda |
| Cortes de NASA (`SEARCH_CMR_TIMEOUT`, LANCE caído, A64) | trozos o noches con menos pasadas que K | conteo A108 antes de leer; repetir una vez; declarar SIN DATO |
| Carga en LAADS y en la cuenta Earthdata (4 veces las descargas de hoy con 45 volcanes; tope SIN DATO) | errores 429 o bloqueo de la cuenta (A71) | retrospectiva en tandas; sólo token; humo antes de cada tanda |
| Token Earthdata: rotación el 2026-11-27, vence el 2026-12-07 18:03 | 401 en todos los workflows; un token vencido puede no dar error si el guard de #894 no corta | rotar el 27; ese día comprobar `nrt-healthcheck` y un job de cada workflow nuevo; ninguna tanda larga cruzando la rotación |
| Régimen marcado en el lector de V375-E | criterios que pasan a «DECIDE NICOLÁS» por un cambio que no era de su vía | nada en las rutas de H9 hasta la parada; perfiles y workflows nuevos; grillas después |
| Doble publicación entre vecinos (H14) | el mismo punto rojo en dos tarjetas | marca de vecinos en la revisión; D1 |
| Falsa alarma en un volcán sin vigilancia | el operador ve rojo en un volcán que nadie venía mirando | rótulo, sección aparte, revisión experta, reversión pre-autorizada (D13), aviso al OVDAS |
| Retrospectiva dentro de muestra disfrazada | un «CUMPLE» que reproduce lo que ya se sabía | sólo R25 y F26 deciden; DM es control |
| Referencia OSF mal leída | un veto o un acierto que dependen de una columna mal entendida (`Max_Dist`, `Dayflag`, `class`) | leer Coppola et al. 2026 renderizado antes de usar la columna |
| Disco local (D: con 14 GB el 2026-10-31) | unión de artifacts cortada | parada bajo 3 GB; unir por volcán y borrar lo bajado a la papelera |
| Cron de GitHub atrasado 4 a 5 h | revisiones del día sin la sombra del día | calendarios con la hora real de llegada |

---

## 14. Lo que no sé

- SIN DATO: costo de la vía en el runner (la sombra de los 11 empieza a medirlo el 2026-11-03), costo de los nuevos con
  radio 25, plan de la cuenta (tope de jobs), tope de LAADS.
- SIN DATO: si el lector sellado de la sombra de VIIRS 750 marca régimen al agregar volcanes a `grillas_mirova.yaml`
  (el de V375-E sí, H9).
- SIN VERIFICAR: semántica de las columnas del OSF v2.5 (`Dayflag`, `Max_Dist`, `class`) y del campo `nivel` de la RNVV.
- SOSPECHA: que la ROI general que elija V750-B sirva para volcanes sin grilla de MIROVA.
- SIN VERIFICAR: si la vía usa `WOOSTER_COEFF` (calibrado contra el OSF) o la constante del código de MIROVA; decide
  cuán independiente es la razón de magnitud en R25.
- El poder de MODIS fuera de muestra con la tabla es bajo (7 alertas de 1 MW o más en febrero).

---

## 15. Autorrevisión contra el encargo

- Fases con fecha y criterio de salida escrito antes de ver datos: §0, §5 a §7. Fase 0 es la evidencia de paridad por
  sensor y el lanzamiento cuelga de ella (Compuertas A y B).
- Prueba retrospectiva del paquete completo, perfil aislado, por trozos en GitHub Actions después de V750-B, de a uno,
  MODIS en Linux, con los criterios de victoria de `docs/MISSION.md` (P1 lectura A con regla SN, Muy Bajo, negativos
  limpios, magnitud, por sensor y tramo): §5. Dentro y fuera de muestra, por pre-registro: §3. Por qué la sombra sigue
  siendo la prueba final: §1. Fechas de la evidencia retrospectiva (~2026-11-12) y de las decisiones (~11-13 y ~12-29): §0.
- Validación sin MIROVA con umbrales sólo desde datos y el resto como decisión: §8, D10. La ventana de abril no sirve
  (H5).
- Tablero, transparencia, riesgos, tabla de decisiones con 43 o 45, A45: §9 a §13.
- MIROVA vigila otros chilenos: comprobado que no (H2).
