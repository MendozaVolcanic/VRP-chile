# Censo de citas `archivo:linea` tras #919 a #922 (A101 y A113)

Base: `cc16b3a7f` (main antes de #919). Hoy: `7a17af8c4` (main con #919, #920, #921 y #922). Los documentos se leyeron con `git show origin/loop/activo:<ruta>` (rama en `97daf7662`). Comprobado: `git diff --quiet 7a17af8c4 origin/loop/activo -- pipeline scripts` da exit 0, o sea que `pipeline/` y `scripts/` de `loop/activo` son idénticos a `7a17af8c4`.

Carpeta de trabajo: `C:/Users/nmend/AppData/Local/Temp/claude/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/2485296a-920d-4331-9b89-693a0f21f408/scratchpad/propagacion_a113/` (scripts `censo.py`, `tool.py`, `gen.py`; datos `res.json`; copias de los documentos en `docs/` y de las fuentes en `src/<commit>/`).

## 1. Archivos que cambiaron entre los dos commits

`git diff --stat cc16b3a7f 7a17af8c4 -- pipeline/ scripts/` (9 archivos, 436 inserciones, 58 borrados). El corrimiento se calculó con `difflib.SequenceMatcher` sobre las líneas de cada archivo en los dos commits (sólo bloques iguales).

| Archivo | Cambios | Dónde cae el corrimiento de líneas |
|---|---|---|
| `pipeline/process_modis.py` | 167 | +2 desde la l. 20 (cabecera FICHA), +6 desde la 104, +75 desde la 500, +117 desde la 547, +127 desde la 554, +135 desde la 567 hasta la 1143; total +147 (1646 a 1793 líneas) |
| `pipeline/process_viirs.py` | 38 | +1 desde la 91, +32 desde la 756, +36 desde la 2251 (2302 a 2338 líneas) |
| `pipeline/mirova_v750_codigo.py` | 206 | 734 a 862 líneas. Ningún documento revisado lo cita con número de línea |
| `pipeline/profile.py` | 31 | +31 desde la l. 904 (cinco flags nuevos, ver sección 5). Líneas 1 a 903 sin corrimiento |
| `pipeline/profiles/mirova_equivalent.yaml` | 6 | +6 desde la l. 135 (tres claves `enable_modis_*`). Líneas 1 a 134 sin corrimiento |
| `pipeline/fetch.py` | 6 | +4 desde la l. 786. Líneas 1 a 785 sin corrimiento |
| `pipeline/store.py` | 7 | +5 desde la l. 609. Líneas 1 a 608 sin corrimiento |
| `scripts/run_pipeline.py` | 27 | +1 desde la 263, +3 desde la 318, +12 desde la 398, +14 desde la 451, +15 desde la 525. Líneas 1 a 262 sin corrimiento |
| `scripts/evaluador_comun.py` | 6 | 897 a 903 líneas. Ningún documento revisado lo cita con número de línea |

`pipeline/process_viirs_mod.py`, `detection_context.py`, `anchor.py` y `test1_integrated.py` NO cambiaron (`git diff --stat` vacío para esos cuatro), así que sus citas no se tocan.

## 2. Resultado en una tabla

| Documento | Citas revisadas | OK hoy | Corridas por #919 a #922 | Ya viejas antes de #919 |
|---|---|---|---|---|
| CLAUDE.md | 9 | 9 | 0 | 0 |
| MIROVA_DIVERGENCES.md | 54 | 2 | 1 | 51 |
| FICHA_SDA_VRP_CHILE.md | 0 | 0 | 0 | 0 |
| MISSION.md | 6 | 0 | 0 | 6 |
| SINTOMAS.md | 2 | 0 | 0 | 2 |
| META_RULES_S80.md | 0 | 0 | 0 | 0 |
| **Total** | **71** | **11** | **1** | **59** |

Una "cita revisada" es un número de línea o un rango citado (por ejemplo `process_modis.py:696/704` cuenta 2). Se cuentan sólo las que apuntan a archivos que cambiaron. Las citas históricas deliberadas de la sección 4 no entran en estos totales, salvo `fetch.py:74`, que sí está en la tabla marcada como histórica por contexto.

**Lectura clave.** Sólo UNA cita estaba correcta en `cc16b3a7f` y quedó corrida por los cuatro PR: `MIROVA_DIVERGENCES.md` l. 1487, `process_viirs.py:1876` que hoy es 1908 (el bloque de VIIRS 375 creció +32 desde la l. 756 por #921). Todas las demás citas desactualizadas ya estaban viejas ANTES de #919: apuntan a versiones de los archivos de S125 a S146 y nunca se remaparon. Las de `CLAUDE.md` ya vienen remapeadas a `7a17af8c4` por la sesión que hizo los PR (las nueve coinciden). Por eso la corrección es un remapeo por contenido contra `7a17af8c4`, no un `+N` sobre el número viejo.

## 3. Tabla de citas

Método por fila: el texto citado se deduce de la frase del documento; se busca con una expresión regular en `cc16b3a7f` y en `7a17af8c4`, tomando la ocurrencia equivalente (misma posición ordinal entre las coincidencias). Si la línea citada coincide con la de `7a17af8c4`: OK hoy. Si coincide con la de `cc16b3a7f` pero no con la de hoy: corrida. Si no coincide con ninguna: ya vieja antes. En rangos, la "línea hoy" es el inicio y el fin supone que el bloque conserva su largo (no verificado extremo a extremo).

| Documento | Línea del doc | Cita actual | Texto citado | Línea en cc16b3a7f | Línea correcta hoy (7a17af8c4) | Veredicto | Evidencia |
|---|---|---|---|---|---|---|---|
| CLAUDE.md | 252 | `run_pipeline.py:252` | get_detection_anchor, llamada MODIS | 252 | 252 | OK (sin cambio) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 252) y en `7a17af8c4` (linea 252) |
| CLAUDE.md | 252 | `run_pipeline.py:296` | get_detection_anchor, llamada VIIRS 375 | 295 | 296 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 295) y en `7a17af8c4` (linea 296) |
| CLAUDE.md | 252 | `run_pipeline.py:345` | get_detection_anchor, llamada VIIRS 750 | 342 | 345 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 342) y en `7a17af8c4` (linea 345) |
| CLAUDE.md | 438 | `process_modis.py:1191` | _path_d_cap_active (tope D9) | 1056 | 1191 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1056) y en `7a17af8c4` (linea 1191) |
| CLAUDE.md | 953 | `process_viirs.py:214` | import compute_test1_nti | 213 | 214 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 213) y en `7a17af8c4` (linea 214) |
| CLAUDE.md | 953 | `process_viirs.py:1170` | bloque compute_test1_nti | 1138 | 1170 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1138) y en `7a17af8c4` (linea 1170) |
| CLAUDE.md | 953 | `process_modis.py:64` | import compute_test1_mir | 62 | 64 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 62) y en `7a17af8c4` (linea 64) |
| CLAUDE.md | 1254 | `run_pipeline.py:262` | puente local_kernel_bg_compatible (MODIS) | 262 | 262 | OK (sin cambio) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 262) y en `7a17af8c4` (linea 262) |
| CLAUDE.md | 1403 | `process_modis.py:1356` | keep_peak= en la llamada | 1221 | 1356 | OK hoy (ya actualizada) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1221) y en `7a17af8c4` (linea 1356) |
| MIROVA_DIVERGENCES.md | 245 | `process_modis.py:1009` | _path_d_cap_active (tope D9) | 1056 | 1191 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1056) y en `7a17af8c4` (linea 1191) |
| MIROVA_DIVERGENCES.md | 307 | `mirova_equivalent.yaml:482` | comentario "Gaua" en el YAML | 497 | 503 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/profiles/mirova_equivalent.yaml` (linea 497) y en `7a17af8c4` (linea 503) |
| MIROVA_DIVERGENCES.md | 507 | `profile.py:676` | default ENABLE_UNSUITABLE_FILTERS_267_273 | 711 | 711 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/profile.py` (linea 711) y en `7a17af8c4` (linea 711) |
| MIROVA_DIVERGENCES.md | 511 | `process_modis.py:696` | apply_unsuitable_filters (1.ª llamada) | 747 | 882 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 747) y en `7a17af8c4` (linea 882) |
| MIROVA_DIVERGENCES.md | 511 | `process_modis.py:704` | apply_unsuitable_filters (2.ª llamada) | 755 | 890 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 755) y en `7a17af8c4` (linea 890) |
| MIROVA_DIVERGENCES.md | 511 | `process_modis.py:866` | _unsuit_dnti = -0.1 | 920 | 1055 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 920) y en `7a17af8c4` (linea 1055) |
| MIROVA_DIVERGENCES.md | 511 | `process_modis.py:867` | _unsuit_deti = -0.1 | 921 | 1056 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 921) y en `7a17af8c4` (linea 1056) |
| MIROVA_DIVERGENCES.md | 511 | `process_viirs.py:1071` | apply_unsuitable_filters (1.ª) | 1098 | 1130 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1098) y en `7a17af8c4` (linea 1130) |
| MIROVA_DIVERGENCES.md | 511 | `process_viirs.py:1079` | apply_unsuitable_filters (2.ª) | 1106 | 1138 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1106) y en `7a17af8c4` (linea 1138) |
| MIROVA_DIVERGENCES.md | 511 | `process_viirs.py:1272` | _unsuit_dnti = -0.1 | 1302 | 1334 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1302) y en `7a17af8c4` (linea 1334) |
| MIROVA_DIVERGENCES.md | 511 | `process_viirs.py:1273` | _unsuit_deti = -0.1 | 1303 | 1335 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1303) y en `7a17af8c4` (linea 1335) |
| MIROVA_DIVERGENCES.md | 1158 | `fetch.py:74` | VJ202IMG configurado (caso 2026-04-29, handoff S44) | 243 | 243 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [historica por contexto] | grep del texto en `git show cc16b3a7f:pipeline/fetch.py` (linea 243) y en `7a17af8c4` (linea 243) |
| MIROVA_DIVERGENCES.md | 1487 | `process_viirs.py:1876` | filtro contextual sólo con fuente test1 | 1876 | 1908 | CORRIDA por #919-#922 | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1876) y en `7a17af8c4` (linea 1908) |
| MIROVA_DIVERGENCES.md | 1937 | `process_modis.py:507` | máscara de nube MODIS (fondo) | 621 | 756 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 621) y en `7a17af8c4` (linea 756) |
| MIROVA_DIVERGENCES.md | 1937 | `process_modis.py:715` | máscara de nube MODIS (2.ª) | 831 | 966 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 831) y en `7a17af8c4` (linea 966) |
| MIROVA_DIVERGENCES.md | 2078 | `process_viirs.py:800` | umbral de nube viene de la perilla | 850 | 882 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 850) y en `7a17af8c4` (linea 882) |
| MIROVA_DIVERGENCES.md | 2436 | `process_modis.py:342` | _interp_geo (interpolación 5 a 1 km) | 385 | 391 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 385) y en `7a17af8c4` (linea 391) |
| MIROVA_DIVERGENCES.md | 2592 | `process_viirs.py:1832`-1841 | bloque filtro contextual Test 1 (inicio del rango 1832-1841) | 1876-1885 | 1908-1917 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1876) y en `7a17af8c4` (linea 1908) |
| MIROVA_DIVERGENCES.md | 2714 | `process_modis.py:74`-78 | calibración banda 31 (inicio del rango 74-78) | 80-84 | 82-86 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 80) y en `7a17af8c4` (linea 82) |
| MIROVA_DIVERGENCES.md | 2759 | `process_modis.py:327` | docstring: ON sigue al paper | 332 | 338 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 332) y en `7a17af8c4` (linea 338) |
| MIROVA_DIVERGENCES.md | 2787 | `mirova_equivalent.yaml:44` | nti_bt_sanity_k: 3.0 | 48 | 48 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/profiles/mirova_equivalent.yaml` (linea 48) y en `7a17af8c4` (linea 48) |
| MIROVA_DIVERGENCES.md | 2816 | `process_modis.py:662`-668 | K1: nti > NTI_K1_NIGHT (inicio de 662-668) | 717-723 | 852-858 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 717) y en `7a17af8c4` (linea 852) |
| MIROVA_DIVERGENCES.md | 2816 | `process_modis.py:824` | combine_hot_paths | 880 | 1015 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 880) y en `7a17af8c4` (linea 1015) |
| MIROVA_DIVERGENCES.md | 2816 | `process_modis.py:888` | hot_mask_2d = fp_hot | 944 | 1079 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 944) y en `7a17af8c4` (linea 1079) |
| MIROVA_DIVERGENCES.md | 2816 | `process_modis.py:857`-859 | test1_mask (inicio de 857-859) | 913-915 | 1048-1050 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 913) y en `7a17af8c4` (linea 1048) |
| MIROVA_DIVERGENCES.md | 2816 | `process_viirs.py:971`-976 | K1 (inicio de 971-976) | 1034-1039 | 1066-1071 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1034) y en `7a17af8c4` (linea 1066) |
| MIROVA_DIVERGENCES.md | 2816 | `process_viirs.py:1188` | combine_hot_paths (VIIRS 375) | 1255 | 1287 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1255) y en `7a17af8c4` (linea 1287) |
| MIROVA_DIVERGENCES.md | 2816 | `process_viirs.py:1259` | hot_mask_2d = fp_hot (VIIRS 375) | 1329 | 1361 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1329) y en `7a17af8c4` (linea 1361) |
| MIROVA_DIVERGENCES.md | 2828 | `process_modis.py:337`-338 | B22 primaria, cae a B21 (rango 337-338) | 339-340 | 345-346 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 339) y en `7a17af8c4` (linea 345) |
| MIROVA_DIVERGENCES.md | 2832 | `process_modis.py:246`-252 | rad[dn > 32767] = NaN (rango 246-252) | 257-263 | 263-269 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 257) y en `7a17af8c4` (linea 263) |
| MIROVA_DIVERGENCES.md | 2832 | `process_modis.py:555` | guard BT > 500 K a NaN | 608 | 743 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 608) y en `7a17af8c4` (linea 743) |
| MIROVA_DIVERGENCES.md | 2832 | `process_modis.py:331`-333 | NaN de B21 cae a B22 (rango 331-333) | 340-342 | 346-348 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 340) y en `7a17af8c4` (linea 346) |
| MIROVA_DIVERGENCES.md | 2863 | `process_modis.py:571`-579 | fondo por anillo, np.median (rango 571-579) [contenido INFERIDO] | 622-630 | 757-765 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 622) y en `7a17af8c4` (linea 757) |
| MIROVA_DIVERGENCES.md | 2863 | `process_modis.py:1023` | L_bg desde la mediana de BT [contenido INFERIDO] | 1080 | 1215 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1080) y en `7a17af8c4` (linea 1215) |
| MIROVA_DIVERGENCES.md | 2863 | `process_modis.py:1044`-1052 | kernel 3x3 opt-in (rango 1044-1052) | 1102-1110 | 1237-1245 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1102) y en `7a17af8c4` (linea 1237) |
| MIROVA_DIVERGENCES.md | 2863 | `process_modis.py:1060` | delta_L recortado a 0 | 1118 | 1253 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1118) y en `7a17af8c4` (linea 1253) |
| MIROVA_DIVERGENCES.md | 2961 | `process_modis.py:361`-383 | _select_thresholds (rango 361-383) | 404-426 | 410-432 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 404) y en `7a17af8c4` (linea 410) |
| MIROVA_DIVERGENCES.md | 2962 | `process_modis.py:798`-804 | primer pase con C2 noche (rango 798-804) | 845-851 | 980-986 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 845) y en `7a17af8c4` (linea 980) |
| MIROVA_DIVERGENCES.md | 2962 | `process_modis.py:815`-821 | réplica del primer pase (rango 815-821) | 862-868 | 997-1003 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 862) y en `7a17af8c4` (linea 997) |
| MIROVA_DIVERGENCES.md | 2963 | `process_modis.py:862`-863 | bloque con overrides (862-863) | 909-910 | 1044-1045 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 909) y en `7a17af8c4` (linea 1044) |
| MIROVA_DIVERGENCES.md | 2963 | `process_modis.py:888`-891 | bloque con overrides (888-891) | 935-938 | 1070-1073 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 935) y en `7a17af8c4` (linea 1070) |
| MIROVA_DIVERGENCES.md | 2965 | `fetch.py:825` | filtro previo a la descarga | 1240 | 1244 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/fetch.py` (linea 1240) y en `7a17af8c4` (linea 1244) |
| MIROVA_DIVERGENCES.md | 2966 | `run_pipeline.py:185` | _check_night | 203 | 203 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 203) y en `7a17af8c4` (linea 203) |
| MIROVA_DIVERGENCES.md | 3007 | `process_modis.py:357`-380 | _select_thresholds (rango 357-380) | 404-427 | 410-433 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 404) y en `7a17af8c4` (linea 410) |
| MIROVA_DIVERGENCES.md | 3007 | `run_pipeline.py:185`-195 | _check_night (rango 185-195) | 203-213 | 203-213 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 203) y en `7a17af8c4` (linea 203) |
| MIROVA_DIVERGENCES.md | 3007 | `store.py:171`-182 | _reject_daytime (rango 171-182) | 203-214 | 203-214 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/store.py` (linea 203) y en `7a17af8c4` (linea 203) |
| MIROVA_DIVERGENCES.md | 3013 | `process_modis.py:501`-512 | sin regrid (rango 501-512) | 551-562 | 668-679 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 551) y en `7a17af8c4` (linea 668) |
| MIROVA_DIVERGENCES.md | 3013 | `profile.py:606` | ENABLE_UTM_REGRID | 894 | 894 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/profile.py` (linea 894) y en `7a17af8c4` (linea 894) |
| MIROVA_DIVERGENCES.md | 3072 | `process_modis.py:16` | cabecera FICHA, Refs/datos (contenido cambió en S147, no por los 4 PR) | 16 | 16 | OK (sin cambio) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 16) y en `7a17af8c4` (linea 16) |
| MIROVA_DIVERGENCES.md | 3098 | `process_viirs.py:1763`-1786 | asignación de final_hotspot_source (rango 1763-1786) [contenido INFERIDO] | 1812-1835 | 1844-1867 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) [contenido INFERIDO, SIN VERIFICAR contra el texto de la epoca] | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1812) y en `7a17af8c4` (linea 1844) |
| MIROVA_DIVERGENCES.md | 3224 | `mirova_equivalent.yaml:128`-134 | N·sigma summit/scene (rango 128-134) | 128-134 | 128-134 | OK (sin cambio) | grep del texto en `git show cc16b3a7f:pipeline/profiles/mirova_equivalent.yaml` (linea 128) y en `7a17af8c4` (linea 128) |
| MIROVA_DIVERGENCES.md | 3226 | `mirova_equivalent.yaml:279`-282 | enable_dual_roi_bt: true (rango 279-282) | 290-293 | 296-299 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/profiles/mirova_equivalent.yaml` (linea 290) y en `7a17af8c4` (linea 296) |
| MIROVA_DIVERGENCES.md | 3237 | `process_viirs.py:997` | bt_path_hot puesta en cero | 1025 | 1057 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1025) y en `7a17af8c4` (linea 1057) |
| MIROVA_DIVERGENCES.md | 3237 | `process_modis.py:660` | bt_path_hot puesta en cero (MODIS) | 712 | 847 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 712) y en `7a17af8c4` (linea 847) |
| MISSION.md | 332 | `process_viirs.py:1642`-1710 | bloque Regla D (inicio de 1642-1710) | 1750-1818 | 1782-1850 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1750) y en `7a17af8c4` (linea 1782) |
| MISSION.md | 332 | `process_viirs.py:1695` | flag cluster rival debil | 1803 | 1835 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 1803) y en `7a17af8c4` (linea 1835) |
| MISSION.md | 332 | `process_modis.py:1196`-1230 | bloque Regla D MODIS (inicio de 1196-1230) | 1319-1353 | 1454-1488 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_modis.py` (linea 1319) y en `7a17af8c4` (linea 1454) |
| MISSION.md | 333 | `process_viirs.py:786` | umbral de nube desde el perfil | 850 | 882 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/process_viirs.py` (linea 850) y en `7a17af8c4` (linea 882) |
| MISSION.md | 334 | `store.py:72`-103 | _apply_vrp_floor (rango 72-103) | 97-128 | 97-128 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/store.py` (linea 97) y en `7a17af8c4` (linea 97) |
| MISSION.md | 334 | `store.py:497` | llamada a _apply_vrp_floor | 561 | 561 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/store.py` (linea 561) y en `7a17af8c4` (linea 561) |
| SINTOMAS.md | 202 | `fetch.py:475`-482 | comentario del cortacircuito de CMR (rango 475-482) | 397-404 | 397-404 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:pipeline/fetch.py` (linea 397) y en `7a17af8c4` (linea 397) |
| SINTOMAS.md | 210 | `run_pipeline.py:404` | default_date_window | 413 | 425 | YA VIEJA ANTES (cc16 ya no la tenia en esa linea) | grep del texto en `git show cc16b3a7f:scripts/run_pipeline.py` (linea 413) y en `7a17af8c4` (linea 425) |

### Observaciones sobre la tabla

- **`CLAUDE.md`**: las nueve citas (l. 252 con 252/296/345, 438 con 1191, 953 con 214/1170/64, 1254 con 262, 1403 con 1356) ya coinciden con `7a17af8c4`. La cadena histórica del `_path_d_cap_active` de la l. 438 (1056 hasta S164, 1094 hasta S165, 1185, 1191) coincide con lo que dan los merges de main: `cc16b3a7f` 1056, `d94f25191` (#919) 1094, `ab3ff9fe3` (#920) y `bd711db63` (#921) 1185, `7a17af8c4` (#922) 1191 (comando: `git show <commit>:pipeline/process_modis.py | grep -n '_path_d_cap_active = ('`).
- **Posible error menor en la cadena histórica de `CLAUDE.md` l. 1403 (A100)**: dice `keep_peak=` en 1356, "era 1350 hasta #922, 1259 hasta #920 y 1172 hasta #919". Con el mismo tipo de comando sobre main: `cc16b3a7f` 1221, #919 1259, #920 1350, #921 1350, #922 1356. O sea que 1259, 1350 y 1356 están bien, pero lo que el texto da como "1172 hasta #919" es 1221 en `cc16b3a7f` (el 1172 sería un valor anterior a #918). No cambia la cita vigente (1356).
- **`MIROVA_DIVERGENCES.md` l. 511**: las ocho citas de `UNSUITABLE_FILTERS` (modis 696/704 y 866/867; viirs 1071/1079 y 1272/1273) son de la verificación S146; la distancia a `cc16b3a7f` es 51 en MODIS y 27 a 30 en VIIRS, o sea que el desfase viene de sesiones anteriores. Las `process_viirs_mod.py:736/744, 854/855` de esa misma frase están en un archivo que no cambió y no las revisé contra su propia historia (SIN VERIFICAR).
- **Filas con contenido inferido** (l. 2816 VIIRS 375: 971, 1188 y 1259, con desfases 63, 67 y 70 hasta `cc16b3a7f`; l. 2863 MODIS: 571 y 1023, con 51 y 57; l. 3098): son las únicas donde el texto citado es una deducción mía a partir de la frase. Los cuatro bloques de MODIS de la l. 2816 (662, 824, 857, 888) tienen desfase casi constante (55 y 56) y son más seguros.
- **`MIROVA_DIVERGENCES.md` l. 2078 (`process_viirs.py:800`) y `MISSION.md` l. 333 (`process_viirs.py:786`)** apuntan a la misma línea de código (`CLOUD_BT_THRESHOLD = CLOUD_MASK_BT_K`) con dos números distintos; hoy es la 882.
- **`MIROVA_DIVERGENCES.md` l. 2965 y 3007 (`fetch.py:825`, `run_pipeline.py:185-195`, `store.py:171-182`) y `MISSION.md` l. 334 (`store.py:72-103`, `:497`) y `SINTOMAS.md` l. 202**: en `fetch.py` (antes de la l. 786), `store.py` (antes de la 609) y `run_pipeline.py` (antes de la 263) los cuatro PR no movieron esas líneas, pero las citas ya estaban viejas (fetch 1240, run_pipeline 203, store 203/561, fetch 397 en `cc16b3a7f`). `SINTOMAS.md` l. 210 (`run_pipeline.py:404`) estaba en 413 en `cc16b3a7f` y hoy está en 425 (corrimiento de los PR desde la 398, pero la cita ya estaba corrida antes). El remapeo va contra `7a17af8c4`.

## 4. Citas a NO tocar (históricas o ancladas a un commit)

| Documento | Línea | Cita | Razón |
|---|---|---|---|
| CLAUDE.md | 247 | `process_viirs.py:518` | Ejemplo de la regla A6 (S21): cita deliberada de la época. A101 la nombra como caso que no se remapea. |
| CLAUDE.md | 251 | `run_pipeline.py:220` | Ejemplo original de A6; la frase siguiente da las líneas de hoy (252/296/345) y ya coinciden con `7a17af8c4`. |
| CLAUDE.md | 727 | `process_modis.py:316` | Regla A49 (regresión S80), línea del commit `a73775cd`: cita histórica deliberada (A101 la nombra). |
| CLAUDE.md | 953 | "eran 674/665; líneas actualizadas S131", y la cadena "era 213/1138 ... 958 antes", "era 62 ... 59", "163" | Cadenas de valores anteriores con su sesión: historia deliberada (formato "era N hasta Sxxx"). |
| CLAUDE.md | 438, 1403, 252, 1254 | Cadenas "era N hasta ..." de `process_modis.py:1191` y `:1356` y de `run_pipeline.py:252/296/345` y `:262` | Formato "era N hasta Sxxx" o "#NNN": historia. Salvo el "1172 hasta #919" de la l. 1403 (ver observaciones). |
| CLAUDE.md | 1591 | `process_viirs.py:1313` | A118: "al momento del hallazgo" y marcado como arreglado en S149. El defecto descrito ya no existe en esa forma. |
| MIROVA_DIVERGENCES.md | 1922 | `process_viirs.py:702-710` | Bloque del parche S27 con el literal `CLOUD_BT_THRESHOLD = 260.0` ("Qué hace el código"). El literal se retiró en #535 (hoy `= CLOUD_MASK_BT_K` en la 882). Describe un estado que ya no existe. |
| MIROVA_DIVERGENCES.md | 1940, 1941 | `process_viirs.py:702` y `:678-681` | Corrección S125 que describe el literal 260.0 "hardcodeado"; ya resuelto (l. 2078 del mismo documento). Historia. |
| MIROVA_DIVERGENCES.md | 1937 | `process_modis.py:507` y `:715` | Corrección S125 fechada. Quedó en la tabla porque el hecho que afirma (MODIS lee la perilla) sigue vigente; si prefieres dejarla como estaba en S125, ignora esas dos filas. |
| MIROVA_DIVERGENCES.md | 1158 | `fetch.py` "líneas 74-76" | Caso del 2026-04-29 con handoff S44. Está en la tabla por si decides remapear (hoy 243), pero es narración de un incidente. |
| MIROVA_DIVERGENCES.md | 2454 | `process_viirs.py:1313`, `process_modis.py:923`, `process_viirs_mod.py:923` | Hallazgo S148 (la caja no llega al segundo pase), arreglado en S149 con `roi1_summit_mask(..., _roi1_mask)`. Describe el defecto de entonces; hoy ese renglón es `process_viirs.py:1378` y `process_modis.py:1112` (la ubicación actual, por si la quieres). |
| MIROVA_DIVERGENCES.md | 3342-3343 | `process_modis.py` "en el tag `pre-s157-lambda-b22`: l. 1036, 1040, 1062 ... 1528" | Anclada a un tag con nombre. No se remapea. |
| MIROVA_DIVERGENCES.md | 3415-3418 | `process_modis.py` (main `f9e22f8d6`): l. 265-266, 292-294, 385, 513; `run_pipeline.py:247-250` | Anclada al commit `f9e22f8d6`. Nota: `run_pipeline.py:247-250` sí sigue correcta hoy (sin corrimiento: `geo = geo_by_time.get(...)` e `if geo is None`, comprobado en las dos versiones). |
| MIROVA_DIVERGENCES.md | 3072 | `process_modis.py:16` | La línea 16 (Refs/datos) no se movió; lo que cambió es su contenido (la cita Coppola 2015 se retiró en S147) y la frase del documento ya lo cuenta como historia. |
| MISSION.md | 333 | `process_viirs.py:674` y `:678-681` | Texto "anterior, por historia" (SIGUE ACTIVA en S125), reemplazado por la retirada de S126. |
| MISSION.md | 334 | `store.py:467-476` y `mirova_equivalent.yaml:64-71` | Texto "anterior, por historia" (S124). Hoy los pisos viven en yaml 94 a 96 y valen 0.0. |

También quedan fuera de este censo, por apuntar a archivos que NO cambiaron: `process_viirs_mod.py:164`, `:671`, `:736/744`, `:854-855`, `:1043`, `:1100` y las de `detection_context.py`, `anchor.py` y `test1_integrated.py`. No las revisé contra su propia historia (SIN VERIFICAR si están al día; sólo sé que los cuatro PR no las movieron).

## 5. FICHA SDA (`docs/FICHA_SDA_VRP_CHILE.md`)

Flags agregados a `pipeline/profile.py` entre los dos commits (`git diff cc16b3a7f 7a17af8c4 -- pipeline/profile.py`, l. 904 a 934 de hoy):

| Flag | PR | Clave en `mirova_equivalent.yaml` | Valor |
|---|---|---|---|
| `ENABLE_MODIS_CODIGO_MIROVA` | #919 | no está escrita (manda el default de `profile.py`) | False |
| `ENABLE_MODIS_GEO_MXD03` | #920 | `enable_modis_geo_mxd03` (yaml l. 138) | false |
| `ENABLE_MODIS_CRATER_SIN_DATO` | #920 (lo usa también #922) | `enable_modis_crater_sin_dato` | false |
| `ENABLE_MODIS_DIST_DESDE_CRATER` | #920 | `enable_modis_dist_desde_crater` | false |
| `ENABLE_V375_CODIGO_MIROVA` | #921 | no está escrita (default) | False |

#922 no agrega flag nuevo (cablea la pasada sin dato bajo `ENABLE_MODIS_CRATER_SIN_DATO`). `ENABLE_V750_CODIGO_MIROVA` ya existía en `cc16b3a7f`.

**Resultado.** La FICHA no tiene tabla de flags ni nombres `ENABLE_*` de estas opciones (los únicos `ENABLE_*` que nombra son `ENABLE_EXCLUDE_ZONES`, `ENABLE_TEST1_NTI_INTEGRAL` y `ENABLE_VRPTIR_AVENI`, en las l. 61 y 64 del historial). Está escrita en prosa para el público y cubre los cuatro PR así: v1.14 (#919, vía "código MIROVA" de MODIS, desactivada), v1.15 (#920, tres opciones MxD03, desactivadas), v1.16 (#921, vía de VIIRS 375, desactivada) y v1.17 (#922, pasada sin dato anotada en el registro; la opción sigue apagada). La cabecera (l. 7) declara v1.17 y encadena las versiones anteriores. La l. 29 sigue siendo cierta hoy ("el pipeline baja MOD03/MYD03 pero hoy no lo usa"), porque los tres flags de #920 están apagados; no menciona que ahora existe, apagada, la opción de usarlo (v1.15 sí lo dice). Conclusión: al día en contenido; no hay tabla de flags que actualizar. La FICHA no tiene ninguna cita `archivo:linea` (sólo nombres de archivo y de función).

Aparte, fuera de alcance pero relevante para tu regla de estilo: `grep -c` de guion largo o medio sobre `docs/FICHA_SDA_VRP_CHILE.md` en `origin/loop/activo` da 12 líneas con esos caracteres (por ejemplo el título "Ficha de Transparencia Algorítmica" con su guion largo). Es previo, no lo toqué.

## 6. META_RULES_S80.md

Sin citas con número de línea a los archivos cambiados (sólo comandos `grep ... pipeline/profile.py` y el nombre de función `fetch.py:_patched_set_requests_session`, l. 292). Nada que remapear.

## 7. Límites de este censo (SIN VERIFICAR)

- El texto citado en cada fila se dedujo de la frase del documento. En seis filas la deducción es débil y está marcada (2816 VIIRS 375, 2863 MODIS 571 y 1023, 3098).
- Busqué citas con la extensión del archivo (`.py`, `.yaml`) y con las formas elididas `:N` o `l. N` en las mismas frases. Una cita que nombre el archivo sin extensión y sin número cercano (por ejemplo "en process_modis, línea 300") no la habría visto; el grep adicional que hice con nombres sin extensión no encontró ninguna relevante.
- Los fines de rango de la columna "hoy" suponen que el bloque conserva su largo.
- Leí sólo los seis documentos pedidos, en `origin/loop/activo`.
