# Censo de afirmaciones de cierre (S145)

> Generado por `experiments/_s145_censo_cierres/censo.py`. 89 afirmaciones en 5 documentos rectores. Ningun numero a mano (S91).

**Que es un cierre y por que importa.** Una frase que dice CERRADA, agotado, no reabrir, efecto nulo, irreducible o menor no es una nota al pie: **apaga trabajo futuro**. Nadie vuelve a mirar lo que dice no reabrir. La regla A95 dice que un cierre hereda las premisas de la lectura con que se derivo, y en S145 cayeron cuatro de una sola vez.

**Limite declarado**: el censo busca por palabras clave. Un cierre redactado con otras palabras no aparece. Es un piso del problema, no su medida.

## Por tipo

| tipo | n |
|---|---|
| resuelta | 23 |
| refutada | 19 |
| cerrada | 9 |
| no_reabrir | 9 |
| agotado | 8 |
| despreciable | 7 |
| irreducible | 7 |
| es_fiel | 6 |
| no_adoptar | 6 |
| menor | 2 |
| efecto_nulo | 2 |

## Sin respaldo citable (50)

Estas son las de mayor riesgo: afirman un cierre y no citan script, run, PR, paper, documento ni `archivo:linea` en su entorno. Un cierre que no se puede verificar no es un cierre, es una creencia.

| archivo:linea | tipo | texto |
|---|---|---|
| `docs/MIROVA_DIVERGENCES.md:289` | resuelta | **Estado D9 — PARCIALMENTE RESUELTO**: mitigación defensiva adoptada. Cubre 100% del bug original (records con magnitud absurda en cirrus). **Causa ra |
| `docs/MIROVA_DIVERGENCES.md:455` | es_fiel | OFF permanentemente; el código actual ya es fiel.** Esto NO afecta a NEW-8 (gaps |
| `docs/MIROVA_DIVERGENCES.md:515` | resuelta | - **El impacto OPERACIONAL-VISIBLE está RESUELTO** (la cara FP de detección): cirrus FAR genuino |
| `docs/MIROVA_DIVERGENCES.md:534` | resuelta | **Estado D9 (actualizado S113) — EFECTIVAMENTE RESUELTA en sus dos caras**: (1) FP de detección |
| `docs/MIROVA_DIVERGENCES.md:1088` | resuelta | ### D8 Background ring contaminado — RESUELTO |
| `docs/MIROVA_DIVERGENCES.md:1090` | refutada | **Hipótesis inicial S52-S58** (refutada): "Lascar/Lastarria ring 5-25 km |
| `docs/MIROVA_DIVERGENCES.md:1129` | resuelta | ### D-PCC: inner_radius_km demasiado permisivo — RESUELTO S62 |
| `docs/MIROVA_DIVERGENCES.md:1186` | resuelta | ## D8' Cluster selection Puyehue (S35) — RESUELTO S38 |
| `docs/MIROVA_DIVERGENCES.md:1214` | refutada | **Alternativas descartadas** (S99): pixfilter (41 FN, recall 59→22); kernel-bg local (refutado S62/A19, empeora glaciar denso 10→18×); eq16 lava lake  |
| `docs/MIROVA_DIVERGENCES.md:1319` | resuelta | del pool μ/σ, flag OFF) — backlog con A/B propio.~~ **GAP #A RESUELTO S115 = mislabel** (no es gap): |
| `docs/MIROVA_DIVERGENCES.md:1368` | no_reabrir | VIIRS375 (375 m) resuelve el foco y cubre el recall (A77). **NO reabrir** el far→summit MODIS con un |
| `docs/MIROVA_DIVERGENCES.md:1405` | refutada | > quedó **refutado en S122**. La divergencia sigue abierta como fenómeno; el camino que |
| `docs/MIROVA_DIVERGENCES.md:1504` | irreducible | que a 1 km es irreducible (A82). Levantar la cerca destaparía ambas cosas |
| `docs/MIROVA_DIVERGENCES.md:1509` | no_reabrir | **Anti-A8**: no reabrir como "hay que levantar la cerca" sin antes clasificar por |
| `docs/MIROVA_DIVERGENCES.md:1545` | cerrada | **Estado S126**: clasificación **CERRADA**; la divergencia queda como documental |
| `docs/MIROVA_DIVERGENCES.md:1819` | resuelta | **RESUELTO en la misma sesión — los GeoTIFF del archivo TIENEN la grilla.** |
| `docs/MIROVA_DIVERGENCES.md:1857` | cerrada, refutada | ## D16 — La grilla UTM NO explica el sub-reporte — **CERRADA (refutada) S124** |
| `docs/MIROVA_DIVERGENCES.md:1886` | no_adoptar | daño real del experimento, y refuerza el NO ADOPTAR. Las lecturas 1 y 2 de |
| `docs/MIROVA_DIVERGENCES.md:1999` | menor, no_adoptar | ## D18 — El ROI1 del paper es una CAJA de 5 km igual para todos; el nuestro es un CÍRCULO de 3 a 20 km por volcán — **ABIERTA (A/B corrido S130 → NO A |
| `docs/MIROVA_DIVERGENCES.md:2039` | irreducible | **Relación con A82**: A82 concluyó «irreducible» y S124 la rebajó porque la auditoría |
| `docs/MIROVA_DIVERGENCES.md:2088` | es_fiel | diferenciación summit/scene es fiel al paper en sus valores y **casi inerte** en la |
| `docs/MIROVA_DIVERGENCES.md:2205` | despreciable | > propio sistema nuestro código coincide. No se propone cambio: el efecto ya era despreciable (S128) y ahora |
| `docs/MIROVA_DIVERGENCES.md:2222` | despreciable | nunca registrado, numéricamente despreciable.** |
| `docs/MIROVA_DIVERGENCES.md:2304` | despreciable | **Fenómeno**: en un paroxismo el píxel del foco satura la banda 21 (~500 K) y es el más caliente de la escena; queda NaN, no entra al NTI, al pool ni  |
| `CLAUDE.md:948` | agotado, irreducible | - **A82. ⚠️ REBAJADA S124: «agotado» ya no aplica.** ⚠️ **Rebajada también por la vía espectral en S138 (AUDIT_S138 C3)**: los ejes que la regla da po |
| `CLAUDE.md:952` | agotado | (D17). Un eje no auditado ≠ eje agotado. Sigue valiendo todo lo que la regla |
| `CLAUDE.md:953` | no_reabrir | descartó por vía espectral/de magnitud; **NO** sigue valiendo el «no reabrir» si |
| `CLAUDE.md:967` | no_reabrir | por bug. **How to apply**: NO reabrir el far→summit MODIS buscando un gate/discriminante/cap |
| `CLAUDE.md:983` | agotado | apply**: (1) NO buscar un escalar físico mágico para gatear cat-b-vs-artefacto — está agotado (anti-A8). |
| `CLAUDE.md:989` | irreducible | - **A84. La POSICIÓN within-inner del `ctx_cluster` es irreducible igual que el far→summit (A82); NO |
| `CLAUDE.md:996` | agotado | están agotadas: (a) snap-a-vent (`test1_roi`) **destruye el cat-b real** (Lastarria); (b) el `nti_peak` |
| `CLAUDE.md:1001` | no_reabrir | (1) NO reabrir el re-ancla `ctx_cluster` (anti-A8) — es cosmético (los records ya están bien |
| `CLAUDE.md:1114` | refutada | el conjunto que dice contar** (S134, cinco enunciados refutados por los verificadores, cuatro |
| `CLAUDE.md:1238` | refutada | cinco veces** con 5 referencias: habría certificado como limpio un instrumento ya refutado; |
| `CLAUDE.md:1512` | refutada | y **D12** (FN MODIS; C2 peak-of-kernel refutado en S122, cierre formal pendiente |
| `CLAUDE.md:1513` | cerrada, no_reabrir | de Nicolás). **CERRADAS, no reabrir** (anti-A8): D9 (S113, sus dos caras), |
| `docs/HYPOTHESIS_LOG.md:143` | refutada | - **Hipótesis inicial (refutada)**: TIF archive scraper parado desde 2026-05-11 (agente C audit S67). |
| `docs/HYPOTHESIS_LOG.md:163` | refutada | - **Hipótesis inicial (refutada)**: `exclude_zones` y `min_vrp_mw_*` por sensor son violación activa de MISSION.md. |
| `docs/HYPOTHESIS_LOG.md:262` | refutada | - **Hipótesis inicial S62-S63 (refutada)**: anomalía Tupungatito en (-33.43, -69.79) (bin top 49% records). Era considerada actividad persistente flan |
| `docs/HYPOTHESIS_LOG.md:296` | no_adoptar | - **VEREDICTO: ❌ NO ADOPTAR**. Decisión S59 (kernel-bg false) era CORRECTA. |
| `docs/HYPOTHESIS_LOG.md:337` | refutada | - **Hipótesis inicial S61 (refutada parcialmente)**: Lastarria gap LEGACY/MIROVA 1.04× con CONS y `record.vrp_mw` → no necesita fix kernel-bg. |
| `docs/HYPOTHESIS_LOG.md:365` | refutada | - **Hipótesis inicial (parcialmente refutada)**: MIROVA reporta dist desde coord Smithsonian GVP a centroide del cluster MIROVA. Verificación: vent Ni |
| `docs/HYPOTHESIS_LOG.md:385` | refutada | - **Hipótesis (refutada parcialmente)**: el patrón "Test 1 over-detection 70+ pixels" en Lastarria/Isluga/Tupungatito/PCC implica fix arquitectural Te |
| `docs/HYPOTHESIS_LOG.md:427` | refutada | - **Hipótesis inicial (refutada)**: PCC gap 52.77× LEGACY/MIROVA es similar a Villarrica (lago en ring) o PlanchonPeteroa (glaciar heterogéneo), por t |
| `docs/HYPOTHESIS_LOG.md:451` | refutada | **ACTUALIZACIÓN S68 (cierre formal)**: Hipótesis **PARCIALMENTE REFUTADA**. La predicción "fix Test 1 cura 4 vols simultáneamente (Lastarria, Isluga,  |
| `docs/HYPOTHESIS_LOG.md:458` | refutada | - **Hipótesis inicial (refutada paralelo S61)**: Tupungatito debería tener `local_kernel_bg: true` porque gap LEGACY/MIROVA NRT es 9.8× similar a Vill |
| `docs/HYPOTHESIS_LOG.md:632` | resuelta | - **Estado**: **✅ CONFIRMADA y RESUELTA** (S18 2026-04-24). |
| `docs/HYPOTHESIS_LOG.md:662` | resuelta | - **Estado**: **PARCIALMENTE RESUELTA S20 (2026-04-25 tarde)**. |
| `docs/HYPOTHESIS_LOG.md:817` | resuelta | - **Estado**: **✅ CONFIRMADA y RESUELTA** S23 (commit `2646fe2`). |
| `docs/META_RULES_S80.md:44` | refutada | hipótesis confirmada/refutada, regresión introducida) → persistir |

## Todas

| archivo:linea | tipo | respaldo citado |
|---|---|---|
| `docs/MIROVA_DIVERGENCES.md:224` | resuelta | paper, sesion |
| `docs/MIROVA_DIVERGENCES.md:289` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:435` | es_fiel | script, sesion |
| `docs/MIROVA_DIVERGENCES.md:455` | es_fiel | sesion |
| `docs/MIROVA_DIVERGENCES.md:515` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:534` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:656` | despreciable | run_ci, sesion |
| `docs/MIROVA_DIVERGENCES.md:1088` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:1090` | refutada | sesion |
| `docs/MIROVA_DIVERGENCES.md:1129` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:1186` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:1196` | resuelta | doc_interno, sesion |
| `docs/MIROVA_DIVERGENCES.md:1214` | refutada | sesion |
| `docs/MIROVA_DIVERGENCES.md:1249` | resuelta | script, sesion |
| `docs/MIROVA_DIVERGENCES.md:1259` | cerrada, agotado, irreducible | archivo_linea, doc_interno, paper, script, sesion |
| `docs/MIROVA_DIVERGENCES.md:1315` | es_fiel | paper |
| `docs/MIROVA_DIVERGENCES.md:1319` | resuelta | sesion |
| `docs/MIROVA_DIVERGENCES.md:1368` | no_reabrir | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:1403` | no_adoptar | doc_interno, sesion |
| `docs/MIROVA_DIVERGENCES.md:1405` | refutada | sesion |
| `docs/MIROVA_DIVERGENCES.md:1421` | resuelta | pr, sesion |
| `docs/MIROVA_DIVERGENCES.md:1441` | resuelta | doc_interno, pr, run_ci, sesion |
| `docs/MIROVA_DIVERGENCES.md:1504` | irreducible | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:1509` | no_reabrir | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:1545` | cerrada | sesion |
| `docs/MIROVA_DIVERGENCES.md:1550` | cerrada | paper, sesion |
| `docs/MIROVA_DIVERGENCES.md:1819` | resuelta | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:1857` | cerrada, refutada | sesion |
| `docs/MIROVA_DIVERGENCES.md:1886` | no_adoptar | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:1999` | menor, no_adoptar | sesion |
| `docs/MIROVA_DIVERGENCES.md:2039` | irreducible | sesion |
| `docs/MIROVA_DIVERGENCES.md:2067` | no_adoptar | doc_interno |
| `docs/MIROVA_DIVERGENCES.md:2088` | es_fiel | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:2194` | despreciable | paper, sesion |
| `docs/MIROVA_DIVERGENCES.md:2200` | despreciable | paper, sesion |
| `docs/MIROVA_DIVERGENCES.md:2205` | despreciable | sesion |
| `docs/MIROVA_DIVERGENCES.md:2222` | despreciable | sesion |
| `docs/MIROVA_DIVERGENCES.md:2304` | despreciable | **ninguno** |
| `docs/MIROVA_DIVERGENCES.md:2353` | efecto_nulo | paper, sesion |
| `docs/MIROVA_DIVERGENCES.md:2377` | menor | archivo_linea, paper, script, sesion |
| `CLAUDE.md:24` | no_reabrir | doc_interno, sesion |
| `CLAUDE.md:102` | resuelta | doc_interno, paper, sesion |
| `CLAUDE.md:112` | es_fiel | paper, sesion |
| `CLAUDE.md:119` | efecto_nulo | doc_interno, paper, script, sesion |
| `CLAUDE.md:120` | resuelta | doc_interno, paper, script, sesion |
| `CLAUDE.md:124` | resuelta | paper, sesion |
| `CLAUDE.md:324` | cerrada | doc_interno, sesion |
| `CLAUDE.md:948` | agotado, irreducible | sesion |
| `CLAUDE.md:952` | agotado | sesion |
| `CLAUDE.md:953` | no_reabrir | **ninguno** |
| `CLAUDE.md:963` | no_adoptar | paper, sesion |
| `CLAUDE.md:965` | es_fiel | paper |
| `CLAUDE.md:967` | no_reabrir | **ninguno** |
| `CLAUDE.md:968` | agotado | doc_interno |
| `CLAUDE.md:983` | agotado | **ninguno** |
| `CLAUDE.md:989` | irreducible | sesion |
| `CLAUDE.md:996` | agotado | sesion |
| `CLAUDE.md:1001` | no_reabrir | sesion |
| `CLAUDE.md:1114` | refutada | sesion |
| `CLAUDE.md:1160` | agotado, no_reabrir | doc_interno, paper, sesion |
| `CLAUDE.md:1238` | refutada | **ninguno** |
| `CLAUDE.md:1246` | refutada | pr, sesion |
| `CLAUDE.md:1412` | despreciable | script |
| `CLAUDE.md:1512` | refutada | sesion |
| `CLAUDE.md:1513` | cerrada, no_reabrir | sesion |
| `CLAUDE.md:1515` | irreducible | doc_interno, sesion |
| `docs/MISSION.md:106` | cerrada, irreducible | doc_interno, paper, sesion |
| `docs/MISSION.md:107` | agotado | doc_interno, paper, sesion |
| `docs/MISSION.md:110` | resuelta, no_reabrir | run_ci, sesion |
| `docs/MISSION.md:142` | cerrada | archivo_linea, doc_interno, paper, pr, script, sesion |
| `docs/HYPOTHESIS_LOG.md:143` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:163` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:262` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:296` | no_adoptar | sesion |
| `docs/HYPOTHESIS_LOG.md:337` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:365` | refutada | **ninguno** |
| `docs/HYPOTHESIS_LOG.md:385` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:427` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:451` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:458` | refutada | sesion |
| `docs/HYPOTHESIS_LOG.md:472` | refutada | paper, script, sesion |
| `docs/HYPOTHESIS_LOG.md:632` | resuelta | sesion |
| `docs/HYPOTHESIS_LOG.md:662` | resuelta | sesion |
| `docs/HYPOTHESIS_LOG.md:724` | resuelta | script, sesion |
| `docs/HYPOTHESIS_LOG.md:743` | resuelta | script, sesion |
| `docs/HYPOTHESIS_LOG.md:780` | resuelta | paper |
| `docs/HYPOTHESIS_LOG.md:817` | resuelta | sesion |
| `docs/HYPOTHESIS_LOG.md:1536` | cerrada | doc_interno, sesion |
| `docs/META_RULES_S80.md:44` | refutada | **ninguno** |
