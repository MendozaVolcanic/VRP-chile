# Handoff próxima sesión (cierre 2026-05-14)

Sesión maratón S37→S44. Modelo operacional fuertemente refinado.
Reproc S44 corriendo al cierre — esperar resultados antes de cualquier
nueva conclusión sobre Tupungatito.

---

## 🔴 ERRORES METODOLÓGICOS que volví a cometer (LEER PRIMERO)

Estos son los errores que **se repitieron en esta sesión** después de haber
sido documentados en sesiones anteriores. La próxima sesión debe internalizar
esto antes de auditar resultados.

### 1. Llamé "límite físico" a algo detectable por MIROVA

Caso: Lascar 2026-05-06 04:54 VIIRS375, MIROVA reporta vrp=0.03 MW. Nuestro
record vrp=0. Lo cataloqué como "límite físico de detectabilidad".

**Error**: si MIROVA lo detecta físicamente ES detectable. La forma correcta
de decirlo: "**nuestro algoritmo no es lo suficientemente sensible** para
captar lo que MIROVA capta". Hay diferencia entre limitación del sensor
(que sí existe — pixel sub-resuelto) y limitación de NUESTRO algoritmo
(que es lo que pasa cuando MIROVA detecta y nosotros no).

**Regla S45+**: NUNCA usar "límite físico" para justificar FN cuando MIROVA
los detecta. Decir "nuestro algoritmo no replica la sensibilidad MIROVA en
este caso" + diagnóstico específico.

### 2. Llamé "decisiones arquitecturales" a divergencias con MIROVA

Caso: PCC 2026-05-09 05:42 — MIROVA reporta lacolito @ 7.73km (0.18 MW),
nosotros cráter @ 0.69km (4.94 MW). Lo describí como "decisión arquitectural
vent_anchored vs MIROVA main alerted cluster".

**Error**: estamos diciendo que clonamos MIROVA. Si MIROVA reporta otro
feature, NO hay "decisión arquitectural" — hay **divergencia con el target**.
La forma correcta: "nuestro vent_anchored NO replica el cluster selection
de MIROVA en este caso, capturamos cluster distinto".

**Regla S45+**: cuando divergimos con MIROVA, NO racionalizar como "decisión
arquitectural". Documentar como divergencia + hipotetizar cómo MIROVA hace
selection.

### 3. Conté RUTINA como FP

Caso inicial audit S41: usé `Tipo_Registro != ALERTA_TERMICA` como FP →
precision 17%. El doc `~memory/reference_mirova_csv_ground_truth.md` decía
claramente: "**ignorar RUTINA NULO** — solo `FALSO_POSITIVO` es FP marker".

**Error**: no leí mi propia documentación interna antes de auditar.

**Regla S45+**: ANTES de cualquier audit MIROVA, releer
`~memory/reference_mirova_csv_ground_truth.md`. Específicamente:
- ALERTA_TERMICA + Clasificacion {Muy Bajo, Bajo} → TP real
- FALSO_POSITIVO (scraper Mirova-v1) → FP
- RUTINA, NULO → IGNORAR

### 4. Usé `record.vrp_mw` raw en mis audits

Caso: reporté "max_vrp Lastarria=1.6M MW, PCC=1276 MW" creando pánico
falso. Pero `record.vrp_mw` es la sum scene-wide de TODOS los hot pixels,
incluyendo FP lejanos. **El dashboard NO lo usa** — usa `primary_cluster.vrp_mw`
via `mirovaEqVrp(r)`.

**Error**: el dashboard ya tiene la lógica correcta. Yo no la repliqué en
mi audit Python.

**Regla S45+**: para audits Python, USAR siempre `mirovaEqVrp(r)` lógica:
- Si `primary_cluster.centroid_dist_km > inner_radius_km`: vrp=0
- Si `primary_cluster.vrp_mw > 50,000` (sanity cap): vrp=0
- Else: pc.vrp_mw

### 5. Pensé que vent_anchored = lo que MIROVA hace

Hasta esta sesión asumí vent_anchored era el "clon literal" MIROVA. El
análisis del TIF PCC 2026-05-09 05:42 mostró:
- TIF tiene 17,948 pixels VRP>0, sum 2,313 MW
- MIROVA reporta 0.18 MW @ 7.73km (solo lacolito sub-cluster local)
- Filtrado MIROVA descarta 99.99% del TIF

**MIROVA tiene un paso de cluster selection/filtrado NO documentado** en
Coppola 2016a paper. Puede ser:
- Density-based local maxima
- Threshold absoluto post-detección
- Validación contextual no replicable

**Regla S45+**: cuando alguien dice "clon literal MIROVA", verificar
empíricamente contra TIFs antes de aceptar. El paper documenta detección
pero NO documenta cómo MIROVA extrae el cluster "main alert" del TIF.

---

## ❓ DUDAS ABIERTAS (no resueltas)

### D1: ¿Cómo MIROVA decide CUÁL cluster reportar?

Hipótesis posibles (no validadas):
- Density-based clustering local
- Threshold absoluto por pixel post-detección
- "Main alert" decision arbitraria del algoritmo

**Necesario S45+**: leer Coppola 2025 chapter (`documentacion/coppola2024_chapter.txt`)
sección "Alert classification". Si NO documenta, escribir a Coppola
(diego.coppola@unito.it).

### D2: ¿Por qué nuestro pc.vrp inflado en outliers?

7 records (>5× MIROVA) con `pc.vrp` muy alto vs MIROVA. Patrón: clusters
8-conn nuestros agrupan más pixels que el sub-cluster MIROVA. Solución
requiere replicar el clustering MIROVA real (ver D1).

### D3: ¿Planchón vent_lat/lon offset?

Caso FN: nuestro cluster @ 5.94km del vent oficial, MIROVA reporta 2.37km.
Planchón-Peteroa es complejo de 2 volcanes. Posible que nuestro vent_lat/lon
sea Planchón (W) cuando MIROVA usa Peteroa (E activo).

**Acción S45+**: verificar coords GVP/KML MIROVA oficiales para
Planchón-Peteroa. Si confirmamos offset, actualizar `volcanoes.yaml`.

### D4: ¿D4 selectivo funcionaría en Tupungatito con fix S44?

Combo C.1 S38 mostró regresión Tupungatito con D4 universal **pero ese
test fue PRE-S43+S44 (bug final_hotspot_source). Post-fixes, D4 selectivo
podría ahora funcionar en Tupungatito sin regresión.

**Acción S45+**: si reproc S44 muestra Tupungatito FN persistentes,
A/B incremental con `lbg_global_compatible: true` solo en Tupungatito.

### D5: ¿Lascar 0.03 MW caso 04-54 — qué hacer?

MIROVA detecta sub-pixel extremo. Nuestro pipeline pierde. ¿Es por
threshold absoluto MIR? ¿Por sensor floor 0.02 MW VIIRS 375m? ¿Por
clustering 8-conn que aisla el pixel?

**Acción S45+**: pixel-level audit del granule específico (descargar y
re-procesar con diag verbose).

---

## 📋 COSAS NO PROBADAS / PENDIENTES

### P1: NdC al D4 (PR #36 mergeado, pendiente cron NRT)

NdC tiene `lbg_global_compatible: true` desde S42. Reproc 30d con esta
config ya corrió. Próximo cron NRT 2h aplicará a alertas futuras NdC.
Validar en próxima sesión que NdC FN baje.

### P2: Frontend toggle dual primary vs sum_active

Si S43+ adopta sum_vrp_active reporting, agregar UI toggle en frontend
para alternar entre primary_cluster.vrp_mw y vrp_mw_sum_active. **No
necesario aún** (sum_active está OFF en operacional).

### P3: Pixel-level R2 sistemático

Existe `experiments/85_r2_pixel_audit_h_d8_5.py` pero no se usó
sistemáticamente. Para casos D8/D4/FN cuestionables, correr R2 vs TIFs
mirova-tif-archive para identificar mecanismo exacto de divergencia.

### P4: Eliminar `record.vrp_mw` raw o renombrar

Confunde consumers externos (yo lo confundí esta sesión). Propuesta:
renombrar a `record.vrp_mw_scene_total` y exponer `record.vrp_mw_primary`
= `pc.vrp_mw` cluster_filtered.

### P5: A/B incremental: ¿qué pasa si quito otros paths viejos?

Después de retirar `bt_path_hot` en S40 (+1.7pp recall), no se ha probado
si `nti_path_hot` (Coppola 2015 Test 1 K1 fijo) también es retirable.
Análisis post-S40 muestra n_nti_path bajo pero no se midió impacto.

### P6: Verificar vent coordinates de TODOS los Tier A

D3 (Planchón) sugiere posible offset. Validar contra GVP / MIROVA KML
para los 11 Tier A.

### P7: NdC tests con `lbg_global_compatible=true` pendiente reproc

NdC se agregó al D4 selectivo en S42 PR #36 PERO reproc 30d S44 está
corriendo. Cuando termine, audit específico NdC para validar mejora.

---

## 🎓 APRENDIZAJES (durables)

### A1: El CSV consolidado Mirova-v1 es incompleto

Nicolás lo confirmó: "no hemos podido guardar todos los datos MIROVA".
También TIFs faltan. Cualquier audit debe asumir cobertura parcial.
RUTINA y NULO son "pasajes registrados sin info significativa" — NO
implican "MIROVA no detectó" para fines de FP.

### A2: TIF MIROVA ≠ alertas MIROVA

El TIF es la imagen térmica scene-wide ETI/VRP que MIROVA publica para
visualización. NO es la alerta. La alerta viene del CSV (latest.php).
TIF tiene 17k+ pixels donde MIROVA reporta solo el cluster main.

### A3: vent_anchored ≠ clon literal MIROVA

Es nuestra mejor aproximación a "cluster cerca del vent". Funciona en
93% de los casos pero diverge cuando MIROVA reporta cluster lejano
(lacolito, satellite peak, etc.) en lugar del cráter principal.

### A4: D4 fix per-volcano es heterogéneo

L_bg global ayuda en cráter caliente permanente (Lascar, Lastarria, NdC).
Empeora en glaciar puro frío (Tupungatito, Planchón). Decidir per-volcán
con field `lbg_global_compatible`.

### A5: Bugs de cluster selection se cascadean a otros fixes

S43 (vent_anchored prefiere vrp>0) y S44 (final_hotspot_source=test1
cuando única fuente) son **fixes de cluster selection lógica** que
multiplican el efecto de fixes anteriores (D4 fix). Sin S43+S44, D4 fix
no aplica a la mayoría de los casos donde debería.

### A6: Sanity cap a `primary_cluster.vrp_mw` necesario

Caso Lastarria garbage 1.6M MW pasaba el cap original (que aplicaba solo
a `record.vrp_mw=0` post-floor). Dashboard mostraba garbage. S41 fix.

### A7: Métricas operacionales reales

Pre-S44 (post-S43):
- Recall **92.2%** (107/116 alertas window 15d)
- Precision **81.7%** (vs FALSO_POSITIVO MIROVA real, no RUTINA)
- F1 **86.6%**
- Mediana diff localización: **0.64 km**
- Mediana ratio MW: **1.21×**

Post-S44 esperado: recall ~95%+ con Tupungatito recuperado.

---

## 📊 ESTADO MODELO OPERACIONAL FINAL

Pipeline `mirova_equivalent.yaml`:
```yaml
enable_vent_anchored_clustering: true       # S38 + S43 fix (vrp>0 priority)
enable_pixel_level_distance_filter: true    # S38 H8
enable_test1_lbg_global: true               # S39+S42 D4 per-vol
enable_bt_path_hot: false                   # S40 retirado
# + S41 sanity cap pc.vrp_mw=50,000 MW (hardcoded store.py)
# + S44 final_hotspot_source=test1 cuando única fuente (3 procesadores)
```

`volcanoes.yaml` D4 selectivo:
- Lascar, Lastarria, NdC: `lbg_global_compatible: true` (cráter caliente)
- Resto: false (glaciares fríos default)

## 🌐 Dashboard publicado

**https://mendozavolcanic.github.io/VRP-chile/** — modelo S44.
- Filtro 🆕 Solo post-S38 REMOVIDO (ya no aplica)
- mirovaEqVrp lee primary_cluster.vrp_mw filtered

## ⏳ Pendiente al cierre

**Reproc 30d S44** corriendo (run 25859304952). Cuando termine:
1. Pull data → `data/mirova_equivalent/`
2. Re-audit con criterio correcto (pc.vrp filtered, FP solo vs FALSO_POSITIVO)
3. Pages refresh manual
4. **Resultados se anexarán a este handoff** al final

---

## 🔗 PRs S37→S44

- PR #22: S37 H_D8_5 implementación (refutado)
- PR #28: S38 vent_anchored + H8 ADOPTADO
- PR #31: S39 D4 per-vol Lascar+Lastarria ADOPTADO
- PR #34: S40 retirar bt_path ADOPTADO
- PR #35: S41 sanity cap pc.vrp_mw ADOPTADO
- PR #36: S42 NdC al D4 ADOPTADO
- PR #37: S42 remove filtro post-S38 UI
- PR #38: S43 vent_anchored prefiere vrp>0 ADOPTADO
- PR #39: S44 final_hotspot_source=test1 única fuente ADOPTADO

---

## ✅ RESULTADOS S44 (anexados al cierre)

Reproc S44 (run 25859304952) completó **11/11 success**. Audit final con
criterio correcto (`pc.vrp_mw` filtered, FP solo contra `FALSO_POSITIVO`,
NO RUTINA), window 15d 2026-04-27 → 2026-05-11:

| Métrica | Pre-S44 | **Post-S44** | Δ |
|---|---|---|---|
| TP | 107 | **110** | +3 |
| FN | 9 | **6** | **-3** ✓ |
| FP | 22 | 25 | +3 |
| **Precision** | 81.7% | 81.5% | -0.2 (estable) |
| **Recall** | 92.2% | **94.8%** | **+2.6pp** ✓✓ |
| **F1** | 86.6% | **87.6%** | **+1pp** ✓ |

### Per-volcán S44 wins

| Vol | TP | FN | FP | Precision | Recall |
|---|---|---|---|---|---|
| Lascar | 46 | 2 | 4 | 92.0% | 95.8% |
| **Tupungatito** | **8** | **0** | 2 | **80.0%** | **100%** ✓✓ |
| Lastarria | 16 | 0 | 5 | 76.2% | 100% |
| **PCC** | 14 | 0 | 0 | **100%** | **100%** ✓ |
| Planchón | 8 | 1 | 3 | 72.7% | 88.9% |
| Isluga | 17 | 2 | 5 | 77.3% | 89.5% |
| Villarrica | 1 | 0 | 1 | 50.0% | 100% |
| Llaima/Copahue/NdC | 0 | 1 | 5 | 0% (sin alertas) | — |

**Tupungatito: 62.5% → 100% recall** — los 3 FN persistentes (Test 1
dispara con 100 pixels pero `source="eruption"` y D4 no aplicaba) fueron
recuperados como predicho. Fix S44 funcionó.

### FN persistentes post-S44 (6 totales)

- 2 Lascar (no inspeccionado todavía)
- 2 Isluga (no inspeccionado)
- 1 NdC (granule probable no procesado, alerta 2026-04-20 VIIRS 750m no
  matched)
- 1 Planchón (caso vent offset documentado en D3)

Estos 6 son casos heterogéneos sin patrón único — quedan para
investigación per-caso S45+.

## 📌 PRIMER MENSAJE PRÓXIMA SESIÓN

Leer este archivo COMPLETO. Especialmente "ERRORES METODOLÓGICOS"
(sección 🔴 al inicio). Después:

1. Confirmar modelo operacional S44 en main es el último (PR #39)
2. Dashboard publicado: https://mendozavolcanic.github.io/VRP-chile/
3. Decidir prioridad próximo trabajo:
   - **D1 cluster MIROVA**: investigar cómo MIROVA hace cluster selection
     real (Coppola 2025 chapter `documentacion/coppola2024_chapter.txt`)
   - **D3 Planchón vent**: validar coords GVP/KML Peteroa, posible offset
     ~3km del vent oficial nuestro
   - **D4 D4 ON Tupungatito**: ahora con S44 fix funcionando, probar A/B
     incremental con `lbg_global_compatible: true` en Tupungatito
   - **P3 R2 pixel-level**: usar `experiments/85` sistemáticamente sobre
     6 FN persistentes para identificar mecanismo divergencia
   - **P4 renombrar record.vrp_mw**: confunde consumidores externos
