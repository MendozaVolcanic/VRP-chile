# Marcas A113 aplicadas en S160 (hallazgos F4 281 a 297, veredictos de V4)

- Worktree: `C:\vrp-trabajo\s159-pruebas`, rama `s160-auditoria` (HEAD `0c77f6612` al empezar). Sin commit, push ni
  merge.
- Insumos: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f4\INFORME.md` (propuestas) y
  `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v4\INFORME.md` (veredictos, mandan).
- Antes de cada marca se buscó con grep el pasaje en este worktree y si ya tenía una marca equivalente. Las líneas de
  V4 son de main o de `cda902080`; aquí se citan las del worktree después del cambio.
- Guiones largos (U+2014) y medios (U+2013), antes y después, por archivo: CLAUDE.md 145/3 y 145/3; MISSION 28/0 y
  28/0; SINTOMAS 0/0 y 0/0; MIROVA_DIVERGENCES 292/14 y 292/14; README 19/9 y 19/9; INDEX 20/0 y 20/0. No subió
  ninguno. La única línea añadida con un guion es `CLAUDE.md:147`, que conserva el texto original (la frase del drift D2) delante de la marca.

## 1. Marcas aplicadas (27)

Texto completo de cada marca: apéndice A (sacado de `git diff -U0`).

| # | hallazgo | archivo:línea (después) | marca, en corto | veredicto V4 que la sostiene |
|---|---|---|---|---|
| 1 | 281 | `docs/MISSION.md:19-26` | la frontera de la marca S157 ya no separa detectores; el «se moverá más atrás» ya pasó con #883; 68.072 records K y 0 sin marca del 2025-02-15 al 2026-09-17 | 281 CONFIRMADO EN PARTE, g4 (con el matiz: MISSION avisaba en futuro; la marca lo dice) |
| 2 | 281 | `CLAUDE.md:214-216` | el «en los datos desde la observación del 2026-09-18» de la nota S157 de las reglas S14 ya no rige | 281 (V4 nombra `CLAUDE.md:210` sin marca) |
| 3 | 281 | `CLAUDE.md:1390-1392` (A100) | el cero de `test1`/`test1_roi` vale para todo el histórico: 0 en 74.811 | 281 (V4 nombra `CLAUDE.md:1376`); el número es de `f4/mis_conteos_salida.txt` §1, que V4 re-corrió con salida idéntica |
| 4 | 281 | `docs/SINTOMAS.md:8-11` | el «C0 antes del 2026-09-18, K después» y la frontera del «Régimen vigente» ya no rigen | 281 (V4 nombra SINTOMAS:9 y 19) |
| 5 | 281 | `docs/SINTOMAS.md:23-24` | el «se moverá más atrás» del «Régimen vigente» ya ocurrió | 281 (SINTOMAS:20-21 avisaba en futuro) |
| 6 | 281 | `docs/SINTOMAS.md:218-219` | la frontera del 2026-09-18 del §7 ya no separa detectores | 281 (V4 nombra SINTOMAS:211) |
| 7 | 281 | `docs/MIROVA_DIVERGENCES.md:1480-1483` (D10) | el cero de la marca S157 vale para todo el histórico | 281 (V4 lista la línea en main, 1444) |
| 8 | 281 | `docs/MIROVA_DIVERGENCES.md:1549-1551` (D11) | la frontera de la marca S157 ya no rige | 281 (main 1507) |
| 9 | 281 | `docs/MIROVA_DIVERGENCES.md:1687-1690` (D11-bis) | el «sólo vale para los records anteriores» ya no aplica: los 2365 ya no están en `data/mirova_equivalent/` | 281 (main 1640) |
| 10 | 282 | `CLAUDE.md:428-433` (A23) | 65.705 / 1.565 / 343 / 110 se reproducen en `88e97d84e`; en main 9 en 5,0 (los 9 con `d9_capped`) y 183 sobre 5 MW; bajo K el tope casi no actúa | 282 CONFIRMADO EN PARTE, g3: «las marcas S151 llevan su ventana, no son falsas; falta la marca de que bajo K el tope casi no actúa» |
| 11 | 282 | `CLAUDE.md:1944-1945` | el «hoy hay 343» es del 2026-10-14; en main son 183 | 282 (hijo de A23 con «hoy» sin ventana) |
| 12 | 282 | `docs/MISSION.md:206-212` | igual que la 10 | 282 (V4: el pasaje de MISSION está en 184-189 de main, no en 134-140) |
| 13 | 282 | `docs/MIROVA_DIVERGENCES.md:232-239` (D9) | igual que la 10, más Chillán: 7 topadas `far` en su fecha, 0 de 31 en main | 282 (`v_282_chillan_salida.txt`) |
| 14 | 283 | `docs/MISSION.md:96-101` | 439 y 992 exactos sobre la unión del 2026-10-14 (`03c44eed7`); en main 478 y 1.055 (437 y 993 hasta el 2026-10-13); decide la definición; aviso V4-03 | 283 CONFIRMADO EN PARTE, g2, y V4-03 |
| 15 | 283 | `CLAUDE.md:1770-1773` (glosario, Recall) | igual que la 14, en corto | 283 (V4 nombra `CLAUDE.md:1695-1696` de main) |
| 16 | 283 | `docs/INDEX.md:135` | igual que la 14, en corto | 283 (hijo no listado por V4; mismo número sin ventana) |
| 17 | 285 | `CLAUDE.md:1590-1595` (A118) | la caja se midió en S151 sobre K: KC NO CUMPLE (veto) en D1; el «nunca se ha medido» describe S148 | 285 CONFIRMADO, g3 |
| 18 | 286 (U1) | `docs/MIROVA_DIVERGENCES.md:3360-3365` (D34, Alcance) | la cita de Campus 2022 no separa estructura de números; en tres puntos el paper contradice al código; cada traslado necesita su A/B | 286 CONFIRMADO EN PARTE: U1 sin marca, confirmado |
| 19 | 286 (U3) | `docs/MIROVA_DIVERGENCES.md:2410-2416` (D18, título) | el código dice que las ROI se mueven y redimensionan por volcán; en Cordón Caulle MIROVA tiene una caja propia | 286: U3 sin marca S158 en toda la sección, confirmado |
| 20 | 286 (U8) y 293 | `CLAUDE.md:147-153` | «C1 = 0.003 / 0.010» y «kernel 8-vec» son fieles al paper, no al código de MIROVA (0,02 fuera de la cumbre y 3 × 3 con el central en VIIRS 750) | 286: U8 en parte (`CLAUDE.md:152` sin marca); 293: «C1 = 0.003 summit / 0.010 scene» de `CLAUDE.md:150` sin marca |
| 21 | 289 | `README.md:52-56` | desde K la réplica corre sin el Test 1 integrado; desde #883 todo el histórico es K; lo del Test 1 describe el detector anterior | 289 CONFIRMADO, g3 |
| 22 | 289 | `README.md:97` | en el árbol de archivos: apagado en la réplica desde K | 289 (V4 nombra :92) |
| 23 | 289 | `README.md:134-136` | el párrafo de Detection y el ejemplo de record con `"test1"` son del detector anterior | 289 (V4 nombra :131) |
| 24 | 289 | `README.md:228-229` | el Test 1 del punto 1 de limitaciones está apagado | 289 (V4 nombra :220) |
| 25 | 290 | `docs/MIROVA_DIVERGENCES.md:2961-2966` (D27) | 1.642/37/19/233 exacto en la tabla de `88e97d84e` (sha `edefbbd3e5067cad`); en main 1.589/37/20/228; hash de las dos tablas y script | 290 CONFIRMADO, g2 |
| 26 | 291 | `docs/MIROVA_DIVERGENCES.md:3322-3328` (D33) | el 24 y las 12 son de la ventana 2026-09-18 a 10-20 antes de #883; hoy el script da 581 records y 95 pasadas dominadas por Láscar; el efecto se sostiene | 291 CONFIRMADO, g2 |
| 27 | V4-02 | `CLAUDE.md:1668-1673` | el hueco nov-2025 a ene-2026 de la marca S146 ya no existe: 74 de 74 días en los 11 Tier A | V4-02 CONFIRMADO, g3 |

Comprobación propia para la 27: en este worktree, Láscar, Llaima y Cordón Caulle tienen record en los 111 días del
2025-10-10 al 2026-01-28 (el tramo largo de PCC que la marca S146 cita). No lo puse en la marca: la marca sólo
afirma lo que V4 midió.

## 2. No aplicadas o pendientes

| hallazgo | qué | razón |
|---|---|---|
| 281 | `CLAUDE.md:141` | V4 la da sin marca, pero en este worktree es el «texto original» que la marca S158 R2 (R2-12, `CLAUDE.md:136-140`) ya conserva; esa marca dice que la frontera del 2026-09-18 no separa detectores. No dupliqué. |
| 281 | el punto (c) de la marca S157 de MISSION (reversión) | nadie lo re-midió después de #883; la marca 1 lo dice así. |
| 281 | `docs/SINTOMAS.md` y su «antes y después de #535» | si #883 reprocesó también lo anterior a #535 con el código de hoy, esa frontera tampoco separaría los datos. SIN DATO: ni F4 ni V4 lo midieron. No lo marqué. |
| 282 | `docs/SINTOMAS.md:89` | no cita los números de S151 y su enunciado vale bajo K; no requiere marca. |
| 284 | D-9, 14 pasadas NONE | REFUTADO por V4 (salen enteros de `frontera_banner.py`). No se marca. |
| 286 (U4) | encabezado de D27 («nunca se ejecuta») | V4 lo llama caso de borde por A113 (d): la marca S158 R2 está justo debajo. No sé si cuenta como marcado; pendiente de quien orquesta. |
| 286 (U10, U13) | `experiments/50_FACTOR_42_HALLAZGO.md`; `docs/DISENO_D17_REMUESTREO_UTM.md:282-283` | fuera de los documentos permitidos para esta tarea. |
| 286 (U12), 287, 288 | memoria del agente | fuera de alcance; ver la propuesta del §3. |
| 287 | docs del repo | V4: el SIN EVIDENCIA ya está propagado en `CLAUDE.md`, MISSION y el catálogo; no hay marca que poner en los documentos permitidos. |
| 293 | H8 (`pipeline/detection_context.py`, comentario «MÁSCARA DE SATURACIÓN»), el YAML del perfil, `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` | `pipeline/` y el perfil quedan fuera (A45 además); BIBLIOGRAPHY está fuera de git. |
| V4-01 | `CLAUDE.md` de loop/activo (OneDrive) sin marcas S157 ni S158 | no es de esta rama; es una decisión de integración (merge de main y del linaje `s160-auditoria`), no una marca. |
| 292, 294, 295, 296, 297 | propuestas de F4 sin veredicto de V4 | V4 no los verificó; sin verificador no se marcan. |

## 3. Propuesta para la memoria del agente (no aplicada)

Carpeta: `C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\`.
V4 confirmó 288 (cinco archivos con 0 marcas) y, en 287, los dos archivos de S113.

- `MEMORY.md:50`, en «Hitos»: cambiar «**S27 Test1 cierra D4 (recall 50→80 %)**» por «**S27 Test1 cierra D4 (recall
  50→80 %; ⚠️ SIN EVIDENCIA desde S147, y el Test 1 integrado está apagado en la réplica desde K, #850)**». Es la
  única de la lista que se carga en cada sesión.
- `reference_s113_cirrus_d9_scope.md:3, 22-23, 37` y `project_s113_estado.md:40`: al inicio, «⚠️ S146 (AUDIT_S146
  V-01): el "207 de 214" no se reproduce con ninguna definición basada en alertas (máximo 80 de 214) y el "0 fuga" es
  circular; SIN EVIDENCIA. S160 (V4 287): bajo K no se re-midió.»
- `reference_calidad_referencia_mirova_por_mes.md:11`: «⚠️ S151: el 86 % de enero contaba a Tupungatito, que no tiene
  filas antes del 2026-02-14; sin él, enero da 99,0 % en MODIS (A119).»
- `reference_s123_reglas_a86_a88.md:23`: «⚠️ S146: el ejemplo de los 482 píxeles de A87 está SIN VERIFICAR (ver la
  marca de A87 en `CLAUDE.md`).»
- `reference_mirova_daytime_cloud_artifact.md:29-30` y `feedback_mirova_no_human_supervision.md:37`: «⚠️ S146 (A76):
  el "~5 % aleatorios" es una cita corrupta. S158: el código de MIROVA rechaza de forma automática el reflejo solar
  bajo 12° (D34), así que "supervisión manual" no describe el canal NRT.»
- `milestone_s27_h_s27_1_confirmada.md:3`: la misma marca que `MEMORY.md:50`.
- `project_s155_estado.md:19` y `feedback_s155_marca_en_los_datos.md:13`: «⚠️ S160 (281): desde #883 (2026-10-21) los
  datos son K desde el 2025-02-15; la frontera del 2026-09-18 ya no separa detectores.» La lección de método de
  `feedback_s155` (anclar la marca a la fecha de los datos) se conserva.

Los archivos de esta lista que no nombra V4 (`reference_s123…`, `reference_mirova_daytime…`,
`feedback_mirova_no_human…`, `project_s155…`, `feedback_s155…`) vienen de F4 288 y de U12; V4 confirmó el hallazgo
en bloque, no cada línea.

## 4. Tests que leen los documentos tocados (no corridos)

`grep -rlnE "CLAUDE\.md|MISSION\.md|SINTOMAS\.md|MIROVA_DIVERGENCES\.md|README\.md|INDEX\.md" tests/`:

```
tests/test_audit_metrics.py
tests/test_banco_paridad_s139.py
tests/test_cloud_mask_from_profile_s125.py
tests/test_cluster_hotspots.py
tests/test_coefficients.py
tests/test_conteo_tif_s144.py
tests/test_d22_compuerta_bt_s142.py
tests/test_drift7_nadir_fixed_pixel.py
tests/test_gr1_viirs_parity.py
tests/test_gr2_profile_invariants.py
tests/test_guard_declarado_vs_efectivo_s131.py
tests/test_guard_gap_a_pool_musigma_s128.py
tests/test_guard_keep_peak_s134.py
tests/test_guard_libro_de_pruebas_s146.py
tests/test_instrumentos_chicos_s151.py
tests/test_mxd03_cumulo_121.py
tests/test_mxd03_etiquetas_s151.py
tests/test_mxd03_sola_123.py
tests/test_path_d_d9_fix.py
tests/test_perfiles_d25_k_s157.py
tests/test_rebuild_mirova_diurnas_s151.py
tests/test_regla_minimas_d9_s151.py
tests/test_remapear_citas_s141.py
```

La mayoría sólo nombra el documento en un comentario. Los que lo abren:
`test_guard_libro_de_pruebas_s146.py` (G2: toda ruta `experiments/…\.(py|json|csv|txt)` citada en `docs/**/*.md` y
`CLAUDE.md` tiene que existir; las que cité están en git: `v_281_regimen_por_mes_salida.txt`,
`v_282_d9_capped_salida.txt`, `v_283_d4_en_su_fecha.txt`, `v_nuevo_hueco_salida.txt`, `v_290_d27_conteo.py`,
`f4/mis_conteos_salida.txt`, `f4/t1_medir_efecto_lambda_salida.txt`), `test_guard_declarado_vs_efectivo_s131.py`
(G1 lee `README.md`; G8b lee las citas `archivo:N` de `CLAUDE.md`; G de INDEX), `test_instrumentos_chicos_s151.py`
(bloque A119 de `CLAUDE.md`, no tocado).

## 5. `git -C C:\vrp-trabajo\s159-pruebas diff --stat`

```
 CLAUDE.md                  | 44 +++++++++++++++++++++++++++++++++-----
 README.md                  | 15 +++++++++++--
 docs/INDEX.md              |  2 +-
 docs/MIROVA_DIVERGENCES.md | 53 ++++++++++++++++++++++++++++++++++++++++++++++
 docs/MISSION.md            | 22 +++++++++++++++++++
 docs/SINTOMAS.md           | 10 ++++++++-
 6 files changed, 137 insertions(+), 9 deletions(-)
```

## Apéndice A. Texto añadido, tal como quedó (`git diff -U0`, sólo líneas +)

En la línea de `CLAUDE.md:147` se omite el texto original que precede a la marca (lleva un guion largo).

### CLAUDE.md


`-147 +147,7`

    [...] (⚠️ **S160, propagación de
      S158** (pendientes F2-H7 y U8 de `experiments/_s158_audit_r2/m1/INFORME.md`; hallazgos 286 y 293 de
      `experiments/_s160_audit/v4/INFORME.md` §3): el «C1 = 0.003 summit / 0.010 scene» y el «kernel 8-vec
      aritmético» de abajo son fieles al paper, no a lo que corre MIROVA. En su código de VIIRS 750 el mínimo de dNTI
      fuera de la cumbre es 0,02 y la media local es de 3 × 3 con el píxel central (D34;
      `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3); para MODIS no hay código, y la Tabla 1 renderizada da 0,01 en
      ROI2 (marca S158 R2 de D9 en `docs/MIROVA_DIVERGENCES.md`). Texto original:) Verificado por

`-207,0 +214,4`

    > ⚠️ **S160 (A113; hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: el «en los datos desde la
    > observación del 2026-09-18» de la marca que sigue ya no rige. #883 (`8471add46`, 2026-10-21) reprocesó con K el
    > histórico de los 11 Tier A desde el 2025-02-15; detalle en la marca S160 del inicio de `docs/MISSION.md`.
    >

`-417,0 +428,6`

      ⚠️ **S160, sobre los números de la marca S151 que sigue** (hallazgo 282 de `experiments/_s160_audit/f4/INFORME.md`,
      CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3): el 65.705, el 1.565, el 343 y el 110 son del
      corpus del 2026-10-14 (`88e97d84e`), donde V4 los reproduce exactos; hoy no, porque #883 reemplazó el histórico con
      K (A90). En main `d516b9d8c` (74.811 records) hay 9 cúmulos con `pc.vrp_mw` = 5,0, los 9 con
      `primary_cluster.d9_capped`, y 183 sobre 5 MW (`experiments/_s160_audit/v4/v_282_d9_capped_salida.txt`). Bajo K
      el tope casi no actúa, y la cara de co-validación del path D se midió con el detector anterior.

`-1374 +1390,4`

    - **A100.** ⚠️ **S160 (hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: desde #883 el cero de la marca
      S157 vale para todo el histórico: 0 records con `final_hotspot_source` `test1` o `test1_roi` entre los 74.811 de
      main `d516b9d8c` (`experiments/_s160_audit/f4/mis_conteos_salida.txt` §1; V4 lo re-corrió con salida idéntica).
      ⚠️ **S157**: con K el `keep_peak` de esta regla (el del filtro contextual del Test 1, D10 y D19) no actúa, porque sólo corre sobre records con

`-1571 +1590,6`

      y aun así **no medía la caja**: medía el cableado. (⚠️ **S160, marca que faltaba acá** (hallazgo 285 de
      `experiments/_s160_audit/f4/INFORME.md`, CONFIRMADO en `experiments/_s160_audit/v4/INFORME.md` §3): la caja se
      midió en S151, con el cableado ya arreglado y sobre K, y salió KC NO CUMPLE (veto) en D1 por una alerta
      protegida MODIS de Láscar (marcas S151 de D18 en `docs/MIROVA_DIVERGENCES.md`;
      `experiments/_s151_prereg_caja/resultado_d1/`). El «nunca se ha medido» que sigue describe S148. Texto
      original:) D18 nunca se ha medido, y el «NO ADOPTAR» de

`-1643,0 +1668,6`

    - (⚠️ **S160, el hueco de la marca S146 que sigue ya no existe** (V4-02 en
      `experiments/_s160_audit/v4/INFORME.md` §4): tras #883, los 11 Tier A tienen record en 74 de 74 días del
      2025-11-16 al 2026-01-28 (689 a 880 records cada uno, main `d516b9d8c`;
      `experiments/_s160_audit/v4/v_nuevo_hueco_salida.txt`; control: en el tag `pre-s158-reemplazo-k` Láscar,
      Llaima y PCC dan 0 de 74). La ventana nov-ene se puede parear en los 11, no sólo en Villarrica. Marca S146
      conservada por historia:)

`-1740 +1770,4`

      sostiene el banner de MIROVA, no el paper. (⚠️ **S160** (hallazgo 283, `experiments/_s160_audit/v4/INFORME.md`
      §3): el 439 y el 992 que siguen son de la unión del 2026-10-14 (`03c44eed7`), donde se reproducen exactos; sobre
      la de main `d516b9d8c` dan 478 y 1.055 por corpus vivo (A90), y decide la definición, no el número; ver la marca
      S160 del punto 1 del criterio en `docs/MISSION.md`.) Rige la lectura A (alertas del scraper de 1 MW o más,

`-1911 +1944,2`

       artefacto; hoy hay 343 cúmulos sobre 5 MW, ver la marca S151 de A23. ⚠️ **S160**: ese «hoy» es el corpus del
       2026-10-14; en main `d516b9d8c`, ya con K en todo el histórico, son 183, ver la marca S160 de A23.)

### README.md


`-51,0 +52,5`

    - ⚠️ **S160 (A113; hallazgo 289, CONFIRMADO en `experiments/_s160_audit/v4/INFORME.md` §3)**: desde el detector K
      (#850, 2026-10-18; S153) la réplica `mirova_equivalent` corre sin el Test 1 integrado en el ROI
      (`enable_test1_path: false`, `pipeline/profiles/mirova_equivalent.yaml:268`; D30), con la conectiva `max` en los
      Tests 2 y 3 y la banda 22 primaria en MODIS, y desde #883 todo el histórico publicado está reprocesado con K. Lo
      que este README dice del Test 1 integrado describe el detector anterior y se conserva por historia.

`-92 +97`

    |   |-- test1_integrated.py       Integrated-ROI Test 1 (sub-pixel detection; ⚠️ S160: apagado en la réplica desde K, #850)

`-128,0 +134,4`

    ⚠️ **S160 (hallazgo 289)**: el Test 1 integrado de este párrafo no corre en la réplica desde K (#850, D30), y el
    ejemplo de record de más abajo (`"final_hotspot_source": "test1"`) es del detector anterior; ver la marca S160 de
    «Detection paths». Texto conservado:
    

`-219 +228,3`

    1. ⚠️ **S160 (hallazgo 289)**: el Test 1 integrado que nombra este punto está apagado en la réplica desde K (#850,
       D30); ver la marca S160 de «Detection paths». Texto conservado:
       **Topographic bias of MIR-absolute paths on snow-capped volcanoes** (D11): the

### docs/INDEX.md


`-135 +135`

    | S151_CRITERIO_CLASE_MIROVA.md | Qué es una alerta protegida: alerta de MIROVA con VRP de la pasada de 1 MW o más, recalculado, nunca leído de la columna `Clasificacion Mirova` (que escribe el scraper). Operacionaliza el «de Bajo para arriba» de Nicolás con el banner de MIROVA (no con el paper). (⚠️ **S160** (hallazgo 283, `experiments/_s160_audit/v4/INFORME.md` §3): el 439 y el 992 son de la unión del 2026-10-14, donde se reproducen exactos; sobre la de main `d516b9d8c` dan 478 y 1.055 por corpus vivo, A90; marca S160 del criterio en `docs/MISSION.md`.) Lectura A por defecto (439 pasadas); la lectura B (992, a cualquier distancia) es la decisión pendiente D-4, issue #782 (⚠️ **S157**: D-4 ya está decidida, lectura A, Nicolás el 2026-10-14, issue #782 cerrado; glosario de `CLAUDE.md`, «Recall»); el loop evalúa con las dos. PR #780 | S151 |

### docs/MIROVA_DIVERGENCES.md


`-231,0 +232,9`

    > ⚠️ **S160, sobre los números de la marca S151 que sigue** (hallazgo 282 de `experiments/_s160_audit/f4/INFORME.md`,
    > CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3): el 65.705, el 1.565, el 343 y las 7 pasadas
    > de Chillán (todas `far`) se reproducen exactos en el corpus de su fecha (`88e97d84e`, 2026-10-14) y no en el de
    > hoy, porque #883 reemplazó el histórico con K (A90). En main `d516b9d8c` (74.811 records) hay 9 cúmulos con
    > `pc.vrp_mw` = 5,0, los 9 con `primary_cluster.d9_capped`, 183 sobre 5 MW, y Chillán MODIS tiene 0 topadas en 31
    > pasadas entre el 2026-09-28 y el 2026-10-13 (`experiments/_s160_audit/v4/v_282_d9_capped_salida.txt` y
    > `v_282_chillan_salida.txt`). Bajo K el tope casi no actúa, y la cara de co-validación del path D se midió con el
    > detector anterior.
    

`-1470,0 +1480,5`

    > ⚠️ **S160 (hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: desde #883 el cero de la marca S157 que
    > sigue vale para todo el histórico: 0 records con fuente `test1` o `test1_roi` entre los 74.811 de main
    > `d516b9d8c` (`experiments/_s160_audit/f4/mis_conteos_salida.txt` §1). La frontera del 2026-09-18 ya no separa
    > detectores (marca S160 del inicio de `docs/MISSION.md`).
    

`-1534,0 +1549,4`

    > ⚠️ **S160 (hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: el «en los datos desde la observación
    > del 2026-09-18» de la marca S157 que sigue ya no rige: #883 (2026-10-21) reprocesó con K el histórico de los 11
    > Tier A desde el 2025-02-15 (marca S160 del inicio de `docs/MISSION.md`).
    

`-1668,0 +1687,5`

    > ⚠️ **S160 (hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: el «sólo vale para los records
    > anteriores» de la marca S157 que sigue ya no aplica. #883 reprocesó con K el histórico: entre los 74.811 records
    > de main `d516b9d8c` hay 0 con fuente `test1` o `test1_roi` (`experiments/_s160_audit/f4/mis_conteos_salida.txt`
    > §1), así que los 2365 de abajo ya no están en `data/mirova_equivalent/`.
    

`-2386,0 +2410,8`

    > ⚠️ **S160, propagación de S158 sobre el «igual para todos» del título** (pendiente U3 de
    > `experiments/_s158_audit_r2/m1/INFORME.md`; hallazgo 286 de `experiments/_s160_audit/v4/INFORME.md` §3): los
    > comentarios del código de MIROVA dicen que sus ROI «can be shifted, reshaped or resized» por volcán
    > (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §2), y en Cordón Caulle las dos alertas probadas sólo aparecen si el
    > anillo usa los umbrales de cumbre: MIROVA tiene ahí una caja propia que no conocemos (`docs/AUDIT_S158_R2.md`,
    > punto 4; F1-H3 de S158, premisa REFUTADA en PCC, `docs/AUDIT_S158.md`). La caja de 5 km es la del paper, no
    > necesariamente la de cada volcán. Título conservado.
    

`-2929,0 +2961,7`

    > ⚠️ **S160, sobre los números de la marca S151 que sigue** (hallazgo 290 de `experiments/_s160_audit/f4/INFORME.md`,
    > CONFIRMADO en `experiments/_s160_audit/v4/INFORME.md` §3): el 1.642 / 37 / 19 / 233 se reproduce exacto sobre la
    > tabla de su fecha (`latest_consolidado.csv` de `88e97d84e`, sha256 `edefbbd3e5067cad…`). Sobre la tabla de main
    > `d516b9d8c` (sha256 `bc1522c24c924cb5…`), en la misma ventana cerrada, da 1.589 / 37 / 20 / 228: la tabla perdió
    > 53 alertas y ganó una protegida de tarde (MODIS, Chillán) dentro de la ventana (A90). Las 37 de la tarde se
    > sostienen. Script: `experiments/_s160_audit/v4/v_290_d27_conteo.py` (salida `v_290_d27_conteo_salida.txt`).
    

`-3283,0 +3322,8`

    > ⚠️ **S160, sobre los n del párrafo «Cuánto»** (hallazgo 291 de `experiments/_s160_audit/f4/INFORME.md`, CONFIRMADO
    > en `experiments/_s160_audit/v4/INFORME.md` §3): el 24 y las 12 pasadas son de la ventana 2026-09-18 a 2026-10-20
    > sobre el corpus anterior a #883 (A90). El script toma «todos los records K» según la frontera de
    > `frontend/cambio_detector.js`, que #883 movió al 2025-02-15: corrido sobre main `d516b9d8c` da F mediana 1,0587
    > en 581 records y, contra MIROVA, 95 pasadas con razón mediana 0,4926 → 0,5215, dominadas por Láscar (83) y no por
    > Chillán (11) (`experiments/_s160_audit/f4/t1_medir_efecto_lambda_salida.txt`). El efecto, F entre 1,05 y 1,08, se
    > sostiene; la población cambió.
    

`-3313,0 +3360,7`

    > ⚠️ **S160, propagación de S158 sobre el «Alcance» que sigue** (F4-H6 de `experiments/_s158_audit/f4/INFORME.md`,
    > CONFIRMADO en `docs/AUDIT_S158.md`; pendiente U1 de `experiments/_s158_audit_r2/m1/INFORME.md`; hallazgo 286 de
    > `experiments/_s160_audit/v4/INFORME.md` §3): la cita de Campus 2022 p. 7 habla del algoritmo entero, y es la misma
    > con que se trasladaron K1 y el mínimo de escena, que resultaron distintos, así que no separa estructura de números.
    > En la media local, el piso de -0,1 y el fondo del VRP el paper del otro sensor contradice al código de VIIRS 750:
    > trasladarlos se apoya sólo en que el código es más reciente. Cada traslado necesita su A/B por sensor.
    

### docs/MISSION.md


`-18,0 +19,9`

    > ⚠️ **S160, la frontera de la marca S157 que sigue ya no separa detectores** (A113; hallazgo 281 de
    > `experiments/_s160_audit/f4/INFORME.md` §3, CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3).
    > El punto (b) de abajo avisaba que «la frontera se moverá más atrás cuando se aplique el reproceso histórico con K».
    > Eso ya pasó: #883 (`8471add46`, 2026-10-21) reprocesó con K el histórico de los 11 Tier A, puso
    > `DATOS_K_DESDE_UTC` en 2025-02-15 (`frontend/cambio_detector.js:32`) y apartó los records C0 que quedaban en
    > `data/_c0_residuales/`. En main `d516b9d8c`, del 2025-02-15 al 2026-09-17 hay 68.072 records K y 0 sin marca de
    > régimen (`experiments/_s160_audit/v4/v_281_regimen_por_mes_salida.txt`; control: los 90 residuos salen C0). Una
    > ventana «C0 antes del 2026-09-18» compara K contra K. El punto (c) sobre la reversión no lo midió S160.
    >

`-86,0 +96,6`

       ⚠️ **S160, sobre el 439 y el 992 de este punto** (hallazgo 283 de `experiments/_s160_audit/f4/INFORME.md`,
       CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3): los dos números se reproducen exactos
       sobre la unión de la referencia del 2026-10-14 (`03c44eed7`); sobre la de main `d516b9d8c` dan 478 y 1.055, de
       las cuales 437 y 993 son hasta el 2026-10-13 (corpus vivo, A90; `experiments/_s160_audit/v4/v_283_d4_en_su_fecha.txt`).
       Lo que decide es la definición, no el número. Ojo: `scripts/clase_mirova.py` cuenta las protegidas siempre
       sobre la unión, aunque se le pase `--cons` o `--ocr` (V4-03).

`-190,0 +206,7`

       - ⚠️ **S160, sobre los números de la marca S151 que sigue** (hallazgo 282 de
         `experiments/_s160_audit/f4/INFORME.md`, CONFIRMADO EN PARTE en `experiments/_s160_audit/v4/INFORME.md` §3):
         el 65.705, el 1.565 y el 343 se reproducen exactos en el corpus de su fecha (`88e97d84e`, 2026-10-14) y no en
         el de hoy, porque #883 reemplazó el histórico con K (A90). En main `d516b9d8c` (74.811 records) hay 9 cúmulos
         con `pc.vrp_mw` = 5,0, los 9 con `primary_cluster.d9_capped`, y 183 sobre 5 MW
         (`experiments/_s160_audit/v4/v_282_d9_capped_salida.txt`): bajo K el tope casi no actúa, y la cara de
         co-validación del path D se midió con el detector anterior.

### docs/SINTOMAS.md


`-7,0 +8,5`

    > ⚠️ **S160 (A113; hallazgo 281, `experiments/_s160_audit/v4/INFORME.md` §3)**: el «C0 antes del 2026-09-18, K
    > después» de este párrafo y la frontera del «Régimen vigente» de abajo ya no rigen. #883 (`8471add46`, 2026-10-21)
    > reprocesó con K el histórico de los 11 Tier A desde el 2025-02-15; detalle en la marca S160 del inicio de
    > `docs/MISSION.md`. Texto conservado.
    >

`-17,0 +23,2`

    ⚠️ **S160**: el «se moverá más atrás» de este párrafo ya ocurrió con #883 (2026-10-21): los datos son K desde el
    2025-02-15 (`DATOS_K_DESDE_UTC`), ver la marca S160 de arriba. Texto conservado:

`-211 +218,2`

    - Cambio de régimen: #535 (A104); (⚠️ **S160**: desde #883 los datos son K desde el 2025-02-15 y la frontera que
      sigue ya no separa detectores; marca S160 del inicio de `docs/MISSION.md`. Texto original:) frontera de K en la fecha de observación 2026-09-18, no en el merge
