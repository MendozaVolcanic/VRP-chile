# Auditoría S139, eje 6: lo que tenemos y nunca usamos, y lo que falta para cumplir la misión

Fecha del servidor al auditar: 2026-09-13 19:53 UTC (`gh api -i repos/MendozaVolcanic/VRP-chile`, header `Date`).
HEAD auditado: `b16bb8fab`. Sólo lectura: ningún archivo del repo modificado fuera de `experiments/_s139_audit/eje6/` y este informe.

Scripts de esta sesión (todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s139_audit\eje6\`):

| script | salida | qué mide |
|---|---|---|
| `01_literatura_no_sintetizada.py` | `01_salida.txt` | PDF de `documentacion/` contra BIBLIOGRAPHY_SYNTHESIS y MISSION, afiliación en p. 1 |
| `02_cruce_osf_2025.py` | `02_salida.txt` | archivo OSF v2.5 de MIROVA contra nuestros records 2025 |
| `03_depurar_cruce_inverso.py` | `03_salida.txt` | depuración de un defecto de mi propio instrumento en 02 (ver nota) |
| `04_rutina_como_negativos_2026.py` | `04_salida.txt` | filas RUTINA del CSV scrapeado como negativos, 2026 |

Nota de instrumento (A93, dicho antes de los hallazgos): la primera versión de 02 contaba sólo 28 detecciones nuestras con respaldo OSF contra 1.499 pareos en sentido directo. La depuración (03) mostró que los records del backfill traen `solar_zenith_deg = None` y mi filtro los trataba como diurnos. Corregido (noche = ángulo solar > 90 o, si falta, hora UTC 00 a 11). Los números del informe son de la versión corregida.

Supuestos declarados:
- S1. "Noche" en 02 y 04 = hora UTC 00 a 11 cuando falta el ángulo solar (noche local chilena).
- S2. Predicado "detección al cráter" = el del auto-audit (`scripts/auto_audit_weekly.py:14-16`): `pc.vrp_mw > 0`, `pc.centroid_dist_km <= inner`, `vrp <= 50000`, `distance_class` summit o None.
- S3. Pareo por pasada: mismo volcán, misma resolución, a menos de 10 minutos.
- S4. Una fila OSF ausente no prueba que MIROVA no detectó: el esquema dice que las filas son pasadas "associated with a target volcano" con píxeles detectados, y no declara si el archivo publicado está filtrado. Por eso lo "sin respaldo OSF" se reporta como tal, nunca como falso positivo.

---

## Parte 1: hallazgos (ordenados por gravedad)

### H601. No existe una definición de terminado: nadie puede decir qué número declara "clon logrado" en ningún sensor

- ARCHIVO:LÍNEA: `docs/MISSION.md:13` ("Reproducir lo más fielmente posible el comportamiento de MIROVA NRT"); `scripts/auto_audit_weekly.py:19-24` y `:60-61,90-92` (bandas); búsqueda sin resultados vigentes (abajo).
- QUÉ PASA: la misión está escrita como dirección ("lo más fielmente posible"), no como meta. Las únicas bandas numéricas vivas son las del auto-audit, y el propio docstring las declara "referencia S119 menos margen 5pp": son bandas de **no regresión** contra un estado de julio, no un criterio de salida. Ninguna combina detección, magnitud y fidelidad literal, ninguna fija conjunto de verdad con negativos, y la de MODIS (recall 95 %) convive con un recall medido de 16 % a 25 % sin disparar nunca porque `MIN_N_RECALL = 15` (l. 53) y la ventana tiene 4 noches MODIS.
- Búsqueda: `grep -rn -i -E "definici[oó]n de (terminado|hecho|listo)|criterio de salida|clon logrado|definition of done" docs tasks CLAUDE.md` da 3 resultados: un diseño de auditoría (`docs/superpowers/specs/2026-08-30-auditoria-s128-design.md:138`) y dos planes archivados de S70 y S1-S14. Ninguno es de la misión.
- CÓMO SE VE EN EL DASHBOARD: invisible. Se ve en la gestión: 139 sesiones sin poder declarar un sensor terminado ni congelarlo.
- CÓMO REPRODUCIRLO: el grep de arriba; `python -c "import json;print(json.load(open('data/audit_continuous/latest.json',encoding='utf-8'))['recall'])"`.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 4. No tuerce una alerta de una noche, pero sin meta cada divergencia nueva reabre el trabajo (es la raíz de la no convergencia que estudia el eje 3).

### H602. La precisión nunca fue una métrica viva: con RUTINA como negativo, el dashboard marca cráter en 47,7 % de las noches en que MIROVA miró y no vio nada

- SCRIPT:SALIDA: `04_rutina_como_negativos_2026.py` → `04_salida.txt`. Unidad: noche por volcán y sensor. Ventana 2026-01-10 a 2026-09-12. Referencia: `latest_consolidado.csv` (37.319 filas) unión `mirova_v1_snapshot/registro_vrp_ocr.csv` (937).
- Encabezado de instrumento. (1) Si el detector gritara todas las noches, la fracción en noches RUTINA subiría hacia 100 %: lo vería. (2) Noche sin fila de referencia se cuenta aparte (SIN_REF, 72), no como negativo. Control positivo: en noches ALERTA el mismo predicado da 90,5 % (1.063 de 1.175); discrimina.
- QUÉ PASA: físicamente, gran parte de lo que detectamos en noches sin publicación de MIROVA es calor real bajo su umbral de publicación (A54: lago de lava, fumarolas, lacolito). Pero eso se midió una vez, en S86, y nunca más: el auto-audit mide sólo recall y magnitud (`auto_audit_weekly.py:14-18`; la palabra RUTINA aparece en él sólo para medir frescura, l. 166 y 312). Resultado por noche:

| sensor | noches ALERTA con detección | noches RUTINA con detección |
|---|---|---|
| VIIRS375 | 98,4 % (852/866) | 81,9 % (1.306/1.595) |
| VIIRS750 | 85,9 % (201/234) | 55,0 % (1.240/2.255) |
| MODIS | 13,3 % (10/75) | 18,3 % (440/2.409) |

  Por volcán, noches RUTINA con detección: Puyehue-Cordón Caulle 91,6 % (493/538), Chaitén 59,6 %, Villarrica 54,5 %, Llaima 48,4 %, Copahue 48,0 % ... Láscar y Nevados de Chillán 27,2 %. Precisión aproximada por noche (ALERTA / (ALERTA + RUTINA con detección)): **26,3 %**.
- Nota sobre MODIS: detecta más en noches RUTINA que en noches ALERTA. Un detector que no distingue la noche con alerta de la noche sin nada no está midiendo la anomalía que publica MIROVA.
- CÓMO SE VE EN EL DASHBOARD: el operador ve anomalía al cráter en la mitad de las noches en que MIROVA no publicó nada, sin un número que le diga cuánto de eso es la categoría "real bajo umbral" y cuánto artefacto.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje6/04_rutina_como_negativos_2026.py`.
- Limitación: RUTINA de una pasada no excluye que otra pasada de la misma noche que MIROVA no scrapeó sí tuviera anomalía (D2, cobertura 79,2 %). El sesgo va en contra de nosotros sólo para ese 21 %.
- CONFIANZA: CONFIRMADO (medido). La interpretación "real vs artefacto" queda SOSPECHA hasta estratificarla.
- GRAVEDAD: 4. Puede torcer la decisión en el sentido "veo algo que MIROVA no ve y el sistema no me dice cuán seguido pasa eso en noches tranquilas".

### H603. El archivo OSF v2.5 de MIROVA (615.470 filas, con fondo, clase y ángulo por pasada) solapa 9,5 meses con nuestro backfill y ninguna métrica viva lo usa

- ARCHIVO: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98,6 MB, 2000-02-24 a 2025-12-31). Esquema: `data/mirova_reference/MIROVA_Database_Schema_v2.5.docx` (convertido en `experiments/_s139_audit/eje6/schema_v25.md`): columnas `Npix`, `Tot_Lmir_hot`, `Tot_Lmir_bk`, `VRP`, `SatZen`, `class` (1 = volcánica, 0 = no volcánica).
- Uso: `grep -rln "VRP_GLOBAL_ARCHIVE\|OSF_CSV" scripts pipeline tests .github` = 0 archivos. Último uso de fondo: `experiments/102_osf_villarrica_deep.py` (commit 2026-05-26, rescate), `experiments/82_osf_v25_audit.py` (2026-05-11). El backfill S120 lo usó como spot-check de 26 noches de Láscar (`docs/BACKFILL_PLAN_S120.md:55-56`). S138 eje 5 lo usó sólo para coordenadas.
- SCRIPT:SALIDA: `02_cruce_osf_2025.py` → `02_salida.txt`. Ventana 2025-02-15 a 2025-11-30, noche (Dayflag 0), 2.335 pasadas OSF de Chile.
- Encabezado de instrumento. (1) Si nuestra detección estuviera muerta el recall caería a 0; si inflara magnitud, el ratio subiría. (2) SIN_DATO (no hay record nuestro a 10 min: 210 pasadas) separado de NO_DETECTA (304). Control positivo: con las horas OSF desplazadas 6 h el pareo cae de 2.125 a 5 pasadas.
- QUÉ PASA (resultados):

| resolución | recall al cráter sobre OSF class 1 | ratio mediano nuestro/OSF |
|---|---|---|
| 375 m | 98,0 % (n = 1.530) | 0,551 (n = 1.499) |
| 750 m | 45,9 % (n = 37) | 0,586 (n = 17) |
| 1 km | 16,1 % (n = 224) | 0,665 (n = 36) |

  Ratio por volcán (todas las resoluciones): Láscar 0,475 (442), Isluga 0,491 (333), Lastarria 0,524 (253), PCC 0,632 (234), PP 0,888 (167), Chaitén 1,002 (64), Copahue 0,742 (28), Villarrica 1,186 (16), Nevados de Chillán **0,007** (15).
  - Sub-reporte sistemático: en 2025 la mediana de VIIRS375 cae fuera de la banda de mediana del propio auto-audit (0,7 a 1,4, `auto_audit_weekly.py:90`) sobre 1.499 pasadas, no sobre las 29 a 54 noches con que el auto-audit flaggea a Láscar e Isluga en 2026.
  - Clase 0: en 332 pasadas VIIRS375 que MIROVA etiquetó "no volcánica", nuestro dashboard marca cráter en 269. Es la etiqueta de negativo del propio grupo, y no la miramos.
  - Tupungatito no existe en el archivo OSF (0 filas): el volcán no tiene verdad histórica en esta fuente.
  - Lo que hace valioso al archivo y no se explotó: `Tot_Lmir_bk` por pasada es la radiancia de fondo de MIROVA. D25 (fondo = mediana de anillo regional contra media de vecinos del paper) se puede contrastar contra el fondo de MIROVA pasada por pasada **sin reprocesar**, siempre que el pipeline persista la radiancia de fondo; hoy los records sólo guardan `t_bg_k`, `nti_bg`, `diag_nti_bg`, `diag_sigma_bg_k` (verificado sobre las últimas 50 records de Láscar). `SatZen` permite repetir el gradiente cenital de D17 con 2025 completo.
- CÓMO SE VE EN EL DASHBOARD: magnitudes de VIIRS375 cerca de la mitad de las de MIROVA en los volcanes de señal débil, sin que el panel lo diga; y cráter publicado donde MIROVA dijo "no volcánico".
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje6/02_cruce_osf_2025.py`.
- CONFIANZA: CONFIRMADO (medido). SOSPECHA: si el archivo OSF publicado es un subconjunto filtrado del NRT (supuesto S4).
- GRAVEDAD: 4.

### H604. En 750 m MIROVA casi no publica para Chile, y nosotros publicamos cráter en 1.821 noches sin ninguna fila OSF

- SCRIPT:SALIDA: `02_salida.txt`, bloque "noches con detección cráter nuestra, por respaldo OSF". Ventana 2025-02-15 a 2025-11-30.
- QUÉ PASA: en 9,5 meses el archivo OSF trae 45 pasadas nocturnas de 750 m para los 10 volcanes chilenos que contiene. Nuestras noches con detección al cráter en 750 m: 1.836, de las cuales 15 tienen fila OSF clase 1 y 1.821 no tienen ninguna. En 1 km: 504 de 541 sin fila. En 375 m: 1.620 sin fila, 972 con clase 1, 165 sólo con clase 0. En 2026, con el CSV scrapeado, las noches RUTINA de VIIRS750 con detección son 55,0 % (H602). Físicamente, a 750 m el píxel mezcla más fondo frío y la señal débil del cráter queda bajo el umbral de MIROVA; lo que nosotros publicamos en ese sensor es mayoritariamente algo que MIROVA no reporta.
- CÓMO SE VE EN EL DASHBOARD: el canal VIIRS750 aparece activo casi todas las noches en volcanes como Tupungatito, PCC o Isluga, mientras MIROVA calla.
- CÓMO REPRODUCIRLO: igual que H603.
- CONFIANZA: CONFIRMADO el conteo; SOSPECHA la causa física (no estratificado por intensidad).
- GRAVEDAD: 3.

### H605. El archivo de TIF de MIROVA está vivo en GitHub desde hace cuatro meses; lo que está parado es la copia local, y cuatro instrumentos la leen por disco

- ARCHIVO:LÍNEA: `experiments/_s131_audit/ground_truth/_lib.py:23`, `experiments/_s136/isluga_offset_tif.py:36`, `experiments/_s128_tif/03_cuanto_pierde_latest_php.py:36`, `tests/test_r2_pixel_level.py:44`, `scripts/build_mirova_imgs_index.py:60-61`. La excepción correcta: `experiments/_s134_audit/f2/f2_lib.py:17` (raw GitHub). Diagnóstico heredado: `docs/AUDIT_S131.md:185` ("parado desde 2026-05-20: reactivar el poller"), `docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md:125` ("Ventana del archivo: 2026-05-08 a 2026-05-20").
- QUÉ PASA: la copia local `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\mirova-tif-archive` tiene HEAD 2026-05-20 12:51 y `index.csv` de 654.050 bytes, con `poll.yml` modificado sin commitear. El remoto tiene commits de polling hoy (2026-09-13 14:42 UTC) e `index.csv` de 4.913.236 bytes: la copia local tiene el 13,3 % del índice. S131 concluyó que el poller estaba muerto mirando el checkout (regla 5 del workspace: frescura se consulta al remoto). La verificación píxel a píxel contra MIROVA (R2) quedó limitada a 11,5 días cuando hay ~4 meses de TIF.
- CÓMO SE VE EN EL DASHBOARD: invisible directamente; el índice de imágenes MIROVA del frontend se construye desde la copia local (`build_mirova_imgs_index.py`).
- CÓMO REPRODUCIRLO: `gh api repos/MendozaVolcanic/mirova-tif-archive/commits?per_page=1 --jq '.[0].commit.committer.date'`; `git -C ../mirova-tif-archive log -1 --format=%ad`; `gh api repos/MendozaVolcanic/mirova-tif-archive/contents/index.csv --jq .size`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### H606. Nunca se le preguntó nada a Diego Coppola, aunque cuatro documentos lo proponen y hay divergencias que un correo cerraría

- ARCHIVO:LÍNEA: contacto registrado en `docs/DATA_SOURCES.md:125`; propuestas sin ejecutar en `docs/MIROVA_DIVERGENCES_CATALOG_S71.md:69`, `docs/superpowers/specs/2026-05-10-d8-cluster-selection.md:245,289-295`, `docs/superpowers/specs/2026-05-15-s46-coppola-literal-design.md:513`, y la decisión de posponerlo en `docs/PAPER_VRP_CHILE_DRAFT_S72.md:26` ("contactar a Coppola DESPUÉS").
- QUÉ PASA: `grep -rn -i -E "respuesta de coppola|coppola respond|correo (a|enviado)|email sent|preguntarle a coppola" docs tasks` no encuentra ningún registro de envío ni de respuesta. Sin registro en el repo no se puede afirmar que no se escribió por otra vía (A89), por eso la confianza es SOSPECHA. Mientras tanto, S136 a S138 gastaron tres sesiones en leer el paper y encontrar que se contradice en la conectiva de los Tests 2 y 3.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: SOSPECHA (ausencia de registro, no prueba de ausencia).
- GRAVEDAD: 3.

Preguntas concretas, cada una con la divergencia que cerraría (no enviado; lista para que Nicolás decida):

| # | pregunta | cierra |
|---|---|---|
| 1 | En los Tests 2 y 3 del NRT actual, ¿el umbral es `min(C1, mu + C2 sigma)` o `max`? El texto y la ecuación del SP426.5 no coinciden | conectiva de S136, D26 |
| 2 | ¿MODIS usa hoy la banda 22 como primaria y la 21 sólo donde la 22 satura, igual que en 2016? | D21 |
| 3 | ¿Los Tests 2 y 3 tienen alguna condición de temperatura del píxel (del tipo BT > fondo + 3 K)? | D22 |
| 4 | El fondo de la ecuación 6, ¿es la media de los 8 vecinos, de un anillo, y se recorta el exceso negativo? | D25 |
| 5 | Los píxeles con NTI > K1, ¿se declaran activos solos, sin pasar Tests 2 y 3? ¿Y los saturados (DN 65533) entran a la radiancia? | D23, D24, GAP #A |
| 6 | ¿VIIRS 375 y 750 se remuestrean a malla de área constante como MODIS? ¿Con qué centro de grilla por volcán y cómo tratan el bow tie? | D17, D28 |
| 7 | El ROI1, ¿sigue siendo una caja de 5 x 5 km fija, o hay radios por volcán como sugieren los KML? | D18 |
| 8 | ¿Hay refit iterativo a 3 sigma en la regresión de NTIbk? | D29 |
| 9 | ¿Qué es la columna `class` del archivo OSF y cómo se asigna? ¿El archivo publicado es completo o filtrado (distancia, intensidad, doble conteo como en Laiolo 2026)? | supuesto S4, D3 |
| 10 | ¿Por qué Tupungatito no está en el archivo OSF y por qué hay tan pocas pasadas de 750 m para Chile? | H603, H604 |
| 11 | ¿MIROVA usa fondo global o local de modo uniforme para todos los volcanes? | deuda de `lbg_global_compatible` (MISSION, nota S125) |

### H607. Dos papers que MISSION declara "core" no se leyeron a fondo, y hay cuatro del grupo MIROVA sin tocar

- ARCHIVO: `docs/s128/lectura_papers.json` (estado por paper; generado en S128, así que puede estar atrasado: Coppola 2020 Frontiers figura MENCIONADO y se leyó a fondo en S129, `docs/s129/PAPERS_COPPOLA2019_SISTEMA_MIROVA.md`). Afiliación verificada en p. 1 por `01_literatura_no_sintetizada.py`. Lecturas posteriores buscadas por DOI en `docs/`.
- QUÉ PASA:

| paper (archivo) | en MISSION | estado S128 | citas posteriores por DOI | por qué podría importar |
|---|---|---|---|---|
| Coppola et al. 2025, Fernandina, Remote Sens. 17:1191 (`Rapid_Response_to_Effusive_Eruptions_Using_Satelli.pdf`) | sí, "NRT moderno" | SIN_TOCAR | sólo `docs/F28_LIT_SEARCH_S73.md` | descripción más reciente del NRT; puede fijar banda, conectiva y remuestreo de hoy |
| Massimetti et al. 2020, Sentinel-2 vs MODIS-MIROVA (`remotesensing-12-00820-v4.pdf`) | sí | MENCIONADO | ninguna | cómo MIROVA valida su MODIS contra alta resolución (instrumento para A77) |
| Coppola et al. 2021, Klyuchevskoy, Sci. Rep. (`s41598-021-92542-z.pdf`) | no | MENCIONADO | ninguna | serie VRP multivolcán cercano, análoga a complejos como PP |
| Coppola et al. 2017, fumarolas Santa Ana (`1-s2.0-S0377027316305248-main.pdf`) | no | MENCIONADO | `docs/PAPERS_AUDIT.md` | detección de fumarolas de alta T con MIROVA (Lastarria, Copahue) |
| Aveni et al. 2025, enfriamiento de coladas (`remotesensing-17-02543-v2.pdf`) | no | SIN_TOCAR | `docs/F28_LIT_SEARCH_S73.md` | menor para detección |

  Además: de la tesis de Massimetti hay extraídos los capítulos 2, 4 y 5 (`documentacion/_mm_ch2_methods.txt`, `_mm_ch4_dome_methods.txt`, `_mm_ch5_monitoring.txt`) y `_thesis_full.txt`; el capítulo 5 describe "implementation of the Mirova system" (`_thesis_full.txt:134`). No verifiqué si el capítulo 3 tiene detalle de implementación: SOSPECHA.
  Descartados por regla A9 aunque salgan en el corpus: Corradino, Amato, Cariello, Torrisi (Catania).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s139_audit/eje6/01_literatura_no_sintetizada.py`.
- CONFIANZA: CONFIRMADO el estado de lectura según el JSON de S128 y la búsqueda por DOI; SOSPECHA el valor de cada paper (no los leí).
- GRAVEDAD: 2 (sube a 3 si Fernandina 2025 describe el NRT actual con parámetros distintos del SP426.5).

### H608. El veredicto semanal FUERA_DE_BANDA lleva 7 semanas y no puede cambiar ninguna decisión: sus dos flags se autodeclaran "déficit conocido"

- ARCHIVO:LÍNEA: `data/audit_continuous/history.jsonl` (12 entradas, 2026-07-02 a 2026-09-07); `scripts/auto_audit_weekly.py:100-116`; `data/audit_continuous/latest.json`.
- QUÉ PASA: VERDE del 2026-07-02 al 2026-07-20; FUERA_DE_BANDA desde el 2026-07-27 hasta el 2026-09-07 (2 a 4 flags). Los flags de hoy: Láscar 0,447 (n = 51) e Isluga 0,574 (n = 54), y el texto del flag los rotula como "déficit de régimen débil S124". Un flag que ya nombra su explicación deja de ser alarma. El brief dice "desde el 28 de mayo": el historial empieza el 2026-07-02, así que esa fecha no se puede verificar con este instrumento. Además el auto-audit no mide precisión (H602), MODIS nunca flaggea (n = 4 < 15, H601) y trata a Lastarria como excepción fija (`UNDER_BAND_KNOWN`, l. 94).
- CÓMO SE VE EN EL DASHBOARD: invisible (abre issues).
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python -c "import json;[print(json.loads(l)['date'],json.loads(l)['verdict']) for l in open('data/audit_continuous/history.jsonl',encoding='utf-8')]"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### H609. Código escrito sin llamador en producción

- ARCHIVO:LÍNEA: `pipeline/geo_utils.py:29` (`get_grid_center`) sólo lo llama `get_effective_vent` (`geo_utils.py:81-87`, marcado DEPRECATED), que no tiene llamador en `pipeline/` ni `scripts/`; `pipeline/audit_metrics.py` y `pipeline/detect_tirvolch.py` no los importa ningún archivo de `pipeline/` ni `scripts/` (sí 2 y 1 tests). `compute_test1_nti` (`test1_integrated.py:185`) sólo existe en `process_viirs.py:210,1079`, detrás de `ENABLE_TEST1_NTI_INTEGRAL = False`.
- QUÉ PASA: `audit_metrics.py` es el módulo de métricas con tests sintéticos que exige la regla R1, pero el instrumento que corre cada semana reimplementa sus criterios por su cuenta, así que esos tests no protegen al auto-audit.
- Flags: de 21 flags `ENABLE_*` en False revisados, 19 aparecen en `true` en algún perfil (vivo o archivado) de `pipeline/profiles/` o workflow, así que "nunca evaluados" es falso para la mayoría. Los dos sin ningún perfil en `true`: `ENABLE_TESTS_23_PROSE_BRANCH` y `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` (pueden haberse probado por otra vía, p. ej. probes S136: SOSPECHA).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -rn "get_grid_center\|get_effective_vent(" --include=*.py pipeline scripts`; bucle `grep -rlE "enable_<flag>\s*:\s*true" pipeline/profiles .github/workflows`.
- CONFIANZA: CONFIRMADO para `pipeline/` y `scripts/` (grep por formas `import`, `from ... import`); no barrí `experiments/`.
- GRAVEDAD: 2.

### H610. Los proyectos hermanos de alta resolución no se consumen, aunque A77 dice que son el instrumento correcto para el foco sub-píxel

- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\MAPA_WORKSPACE.md:194-198` (Landsat-v1, NHI-v1 y Mirova-v1 en verde con Pages); `frontend/index.html:450` (sólo texto: "Sentinel-2 a 20 m, Landsat a 30 m, que este sistema no usa").
- QUÉ PASA: ningún `.py`, `.yml` ni `.html` de VRP Chile lee la salida publicada de NHI-v1 o Landsat-v1. La verdad independiente de MIROVA (hot pixels SWIR) que A77 usó a mano en NdC no está en ningún instrumento.
- CÓMO SE VE EN EL DASHBOARD: el operador no ve la confirmación SWIR al lado de la anomalía VIIRS.
- CÓMO REPRODUCIRLO: `grep -rln -i "NHI-v1\|Landsat-v1" --include=*.py --include=*.yml --include=*.html pipeline scripts frontend .github`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (fuera del clon literal; es objetivo 2 de MISSION).

---

## Parte 2: qué falta para cumplir la misión

### 2.1 Tabla de brecha por sensor

Fuentes: A = OSF 2025 (02, 2025-02-15 a 2025-11-30, pasadas); B = CSV scrapeado 2026 por noche (04, 2026-01-10 a 2026-09-12); C = auto-audit (`latest.json`, 61 días a 2026-09-07, noches ALERTA).

| sensor | detección (medido hoy) | magnitud (medido hoy) | fidelidad literal abierta (catálogo) | evidencia que falta | recurso que la cerraría |
|---|---|---|---|---|---|
| MODIS | A: 16,1 % (n = 224). B: 13,3 % en noches ALERTA (n = 75) y 18,3 % en RUTINA (n = 2.409). C: 25 % dashboard (n = 4) | A: 0,665 (n = 36) | D21, D22, D23, D24, D25, D17/D28, D29 (D20 despreciable) | ninguna medición de que MODIS separe noche con alerta de noche tranquila; A/B de D21/D25 contra verdad con negativos | OSF 2000-2025 (9.574 filas de 1 km en Chile, con `Tot_Lmir_bk`); preguntas 2 a 6 a Coppola |
| VIIRS 375 | A: 98,0 % (n = 1.530). B: 98,4 % ALERTA (n = 866), 81,9 % RUTINA (n = 1.595). C: 96,0 % (n = 176) | A: 0,551 (n = 1.499), fuera de banda de mediana | D17 (área, gradiente cenital), D19, D22, D23, D25 | precisión; si el 0,55 es fondo (D25) o área (D17) | `Tot_Lmir_bk` y `SatZen` del OSF; TIF remotos de 4 meses (H605); pregunta 6 |
| VIIRS 750 | A: 45,9 % (n = 37). B: 85,9 % ALERTA (n = 234), 55,0 % RUTINA (n = 2.255). C: 83,7 % (n = 43) | A: 0,586 (n = 17) | D17, D22, D23, D25 (`process_viirs_mod.py:981`, sin alternativa) | casi no hay verdad positiva en OSF (45 pasadas en 9,5 meses) | pregunta 10 a Coppola; TIF VIIRS750 remotos |

### 2.2 Carencias estructurales (no síntomas)

1. **No hay criterio de salida** (H601). Sin un número por sensor que declare "clon logrado" (qué conjunto, qué unidad, qué predicado, qué tolerancia), cada hallazgo nuevo reabre el sensor y ninguna sesión puede congelar nada. Es la condición que hace posible la no convergencia.
2. **La verdad que usamos no tiene negativos** (H602, H603, H608). Todas las métricas vivas son recall y magnitud sobre noches donde MIROVA publicó. Se puede ganar recall publicando todo; nada lo penaliza. Existen 35.018 filas RUTINA y 407 pasadas OSF clase 0 en la ventana 2025 que son negativos del propio MIROVA, y ninguna métrica las usa.
3. **La verdad externa más rica está en disco y sin explotar** (H603, H605). El archivo OSF tiene, por pasada, la radiancia de fondo, la clase y el ángulo de MIROVA: permite contrastar D25 y D17 sin reprocesar, cosa que la batería del Apéndice A (9 figuras) no puede con su tamaño. Los TIF remotos tienen 4 meses; se usaron 11,5 días por leer una copia local vieja.
4. **Se diagnostica leyendo el paper en vez de preguntarle al autor** (H606, H607). Las divergencias D21 a D29 nacieron de ambigüedades de texto; la conectiva de los Tests 2 y 3 es una contradicción interna del paper que ninguna relectura cierra. Once preguntas cortas cierran o acotan nueve divergencias. Y el paper más reciente sobre el NRT (Fernandina 2025) está sin leer.
5. **Lo que se sabe no se persiste en el record** (H603). El pipeline calcula la radiancia de fondo y no la guarda, así que cualquier comparación con `Tot_Lmir_bk` exige reprocesar. Es el patrón A7 ("calculado pero no persistido") sobre justo la variable que S138 señaló como palanca (D25).

---

## VERIFICADO LIMPIO (no volver a mirar salvo que cambie el comando)

| qué | resultado | comando |
|---|---|---|
| Tests en CI | `tests.yml` corre pytest en PR y push a main | `sed -n 12,17p .github/workflows/tests.yml` |
| Canal OCR en el auto-audit | el criterio declara loader CONS unión OCR | `python -c "import json;print(json.load(open('data/audit_continuous/latest.json',encoding='utf-8'))['criteria'])"` |
| Frescura de la referencia | `gt_stale_dias = 0` al 2026-09-07; `latest_consolidado.csv` llega a 2026-09-13 12:35 | `04_salida.txt` y `latest.json` |
| Cobertura propia del auto-audit | 100 % (61/61 días) | `latest.json` campo `cobertura` |
| Integridad del archivo OSF | 615.470 filas, 28 fechas no parseables, Npix mínimo 1 | `02_salida.txt` y consulta de la Parte 1 |
| Coppola 2020 Frontiers (sistema MIROVA) | leído a fondo en S129 (el JSON de S128 está atrasado en ese punto) | `ls docs/s129/PAPERS_COPPOLA2019_SISTEMA_MIROVA.md` |
| KML/KMZ oficiales | consumidos para centros (`scripts/extract_mirova_centers_from_kmz.py`) | `ls scripts/extract_mirova_centers_from_kmz.py` |
| Tablas suplementarias Coppola 2019 (xlsx) | son inventario de sistemas y observatorios, sin detalle de implementación: no hay pérdida | `python -c "import pandas as pd;print(pd.read_excel('documentacion/Coppola_2019_supp_Table1.xlsx').columns.tolist())"` |
| `registro_<Volcan>.csv` | sólo 3 volcanes (Chaitén 22, Láscar 301, Tupungatito 79 filas, 2026-01 a 2026-04), un consumidor (`experiments/136_*`); valor bajo frente al consolidado | `wc -l data/mirova_reference/mirova_v1_snapshot/registro_*.csv` |
| Flags en False "nunca evaluados" | falso para 19 de 21: tienen perfil con `true` | bucle grep de H609 |
| Poller del archivo TIF | vivo en el remoto (commits 2026-09-13) | `gh api repos/MendozaVolcanic/mirova-tif-archive/commits?per_page=1` |
