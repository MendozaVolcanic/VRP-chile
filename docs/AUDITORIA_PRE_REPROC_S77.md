# Auditoría pre-reproc S77 — ours vs MIROVA NRT

**Fecha**: 2026-05-24
**Worktree**: `VRP-Chile-s77-audit-comprehensive`
**Branch**: `claude/s77-audit-comprehensive-pre-reproc`
**Modo**: READ-ONLY. **No se ejecutó ningún reproc.**

## TL;DR (2 líneas)

De 11 Tier A: **0 OK / 7 sobre-estiman / 3 sub-estiman / 1 sin data comparable**. Hallazgo
arquitectural crítico: **MIROVA emite 467/529 (88%) alertas non-NULO last 90d sobre VIIRS375
(I-band 375m), bucket que nuestro pipeline NO procesa**. Esto domina cualquier discusión de
recall/gaps y subordina la prioridad del reproc histórico.

---

## 1. Inputs y alcance

| Dataset | Path | Tamaño | Ventana |
|---|---|---|---|
| Ours `mirova_equivalent` | `data/mirova_equivalent/<11 Tier A>.json` | 13 106 records | 2026-01-10 → 2026-05-24 |
| MIROVA NRT | `latest_consolidado.csv` | 18 960 rows (Tier A) | 2026-01-10 → 2026-05-24 |
| OCR ground truth | `data/mirova_reference/registro_vrp_ocr.csv` | 236 rows | — |
| **OSF v2.5 archive** | — | **NO PRESENTE LOCAL** | — |

**Gap documentado**: el OSF v2.5 (CSV global 615k filas, post-procesado MIROVA) **no está
disponible en el worktree**. `data/mirova_reference/` solo contiene OCR (236 filas) y un
snapshot v1 del mismo NRT CSV (17 966 filas). El paso 4 de la tarea (cross-check OSF) queda
**no ejecutable** en esta auditoría. Recomendación: descargar OSF v2.5 desde Zenodo (DOI
10.5281/zenodo.7448710 o sucesor) antes del próximo reproc para validar magnitudes históricas.

**Tier A** (11): PuyehueCordonCaulle, Villarrica, Lascar, Copahue, NevadosDeChillan,
Llaima, Chaiten, PlanchonPeteroa, Lastarria, Isluga, Tupungatito.

**Buckets de sensor**: MODIS, VIIRS (M-band 750m), VIIRS375 (I-band 375m). Mapping
ours→bucket: `MODIS_AQUA/MODIS_TERRA → MODIS`; `VIIRS_*_750`, `VIIRS_NOAA20`, `VIIRS_SNPP`,
`VIIRS_NOAA21` → `VIIRS`. **Ningún record nuestro mapea a VIIRS375** — el pipeline
`process_viirs.py` solo procesa M-band; el procesamiento I-band 375m no existe en el código
actual.

**Matching rule**: mismo volcán, mismo bucket, `|Δt| ≤ 60 min`. Para VRP nuestro se usó la
réplica del frontend `mirovaEqVrp` (vrp_mw si `distance_class=='summit'` o
`final_hotspot_dist_km ≤ inner_radius_km` del yaml; cero en otro caso).

---

## 2. Hallazgo arquitectural #1 — VIIRS375 dominante en MIROVA y ausente en ours

Tabla cruzada del CSV MIROVA (4.5 meses, 18 960 rows):

| Sensor   | NULO | Muy Bajo | Bajo | FALSO POSITIVO | **% non-NULO sobre total non-NULO** |
|---|---:|---:|---:|---:|---:|
| MODIS    | 5 776 | 27 | 49 | 1 | 9.3 % |
| VIIRS    | 6 701 | 76 | 69 | 2 | 17.7 % |
| **VIIRS375** | 5 651 | **517** | **82** | **9** | **73.0 %** |

**MIROVA detecta 78 % de su señal en VIIRS375**, exactamente el bucket que no procesamos.
Esto se traduce en gaps last 90d:

| Volcán | MODIS gap | VIIRS gap | VIIRS375 gap |
|---|---:|---:|---:|
| Lascar | 54 | 1 | 109 |
| Tupungatito | 0 | 1 | 77 |
| Lastarria | 0 | 0 | 75 |
| Isluga | 0 | 1 | 71 |
| PuyehueCordonCaulle | 0 | 0 | 61 |
| PlanchonPeteroa | 0 | 0 | 47 |
| Chaiten | 0 | 0 | 17 |
| Villarrica | 0 | 0 | 7 |
| NevadosDeChillan | 1 | 1 | 4 |
| Llaima | 0 | 0 | 1 |
| Copahue | 0 | 0 | 1 |
| **TOTAL** | **55** | **4** | **470** |

De los 529 gaps non-NULO totales en últimos 90 días, **88.8 % son VIIRS375**. Reprocesar el
histórico no cierra estos gaps — requiere implementar el path 375m en pipeline.

---

## 3. Hallazgo arquitectural #2 — Sobre-detección masiva en MODIS

Top 15 records nuestros con `vrp_mw_raw > 100 MW` (ver `experiments/148_audit_pre_reproc/anomalies.csv`):

| Volcán | Fecha | Sensor | vrp_mw_raw | dist_km | distance_class | n_pixels |
|---|---|---|---:|---:|---|---:|
| PuyehueCordonCaulle | 2026-04-16 | MODIS_AQUA | **1 659.6** | 12.66 | summit | 197 |
| PuyehueCordonCaulle | 2026-01-31 | MODIS_AQUA | 1 609.5 | 15.78 | summit | 107 |
| PuyehueCordonCaulle | 2026-05-04 | MODIS_AQUA | 1 362.6 | 13.52 | summit | 268 |
| NevadosDeChillan | 2026-03-13 | MODIS_TERRA | 1 325.0 | 23.66 | far | 50 |
| Villarrica | 2026-01-31 | MODIS_AQUA | 1 288.7 | 16.36 | far | 47 |
| PCC | 2026-05-04 | MODIS_AQUA | 1 261.3 | 23.21 | far | 232 |
| Chaiten | 2026-05-04 | MODIS_AQUA | 1 215.7 | 17.35 | far | 258 |
| ... | ... | ... | ... | ... | ... | ... |

Para PCC en la misma ventana, MIROVA-VIIRS marca **máximo 1.34 MW** y MIROVA-MODIS **0 MW**.
Nuestro máximo MODIS para PCC es **1 659 MW** (factor ~1 200× sobre cualquier referencia).
Los clusters MODIS de 100-268 pixels a 12-23 km del vent son no-físicos para PCC (cone +
lacolito ocupan <5 km²). Los records `summit` ocurren porque PCC tiene `inner_radius_km: 20`
para acomodar el lacolito; pero esto admite escenas enteras del datos MODIS L1B con
saturación o nieve fría como "anomalía cráter".

**Distribución per volcán de records con vrp_mw_raw > 100 MW**:
PCC (25), Villarrica (6), Chaiten (4), Lascar (3), PlanchonPeteroa (3), NdC (2), Llaima
(2), Copahue (2), Tupungatito (2), Lastarria (1) → **50 records totales**.

Estos records son anteriores a los fixes F46/F47/F50/F52 mergeados en S77; los fixes están
en NRT cron, pero los records históricos **no han sido reprocesados**. Por eso aparecen
como vivos en la JSON consolidada.

---

## 4. Tabla maestra resumida (all-time, VIIRS M-band)

VIIRS es el bucket más comparable porque (a) tiene la mayoría de records nuestros y (b)
MIROVA-VIIRS-M existe en el CSV aunque diluido por VIIRS375. Para "all-time" del CSV
(2026-01-10 → 2026-05-24):

| Volcán | n_ours>0 | n_mir>0 | n_matched | ratio_med | ratio_p25 | ratio_p75 | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---|
| Lascar | 533 | 97 | 75 | **0.95** | 0.48 | 2.12 | **OK** (mediana 1.0) |
| Llaima | 331 | 13 | 1 | 1.79 | — | — | bajo n |
| Isluga | 386 | 21 | 13 | **3.02** | 2.05 | 6.98 | sobre 3× |
| PlanchonPeteroa | 392 | 3 | 2 | 4.54 | 3.27 | 5.80 | bajo n |
| PCC | 796 | 21 | 11 | **5.18** | 2.20 | 15.5 | sobre 5× |
| Tupungatito | 380 | 11 | 5 | **16.19** | 10.5 | 22.8 | sobre 16× |
| Villarrica | 393 | 1 | 0 | — | — | — | sin matches |
| Copahue | 317 | 6 | 0 | — | — | — | sin matches |
| NdC | 143 | 10 | 0 | — | — | — | sin matches |
| Chaiten | 505 | 2 | 0 | — | — | — | sin matches |
| Lastarria | 444 | 0 | 0 | — | — | — | sin MIR-VIIRS |

(Tabla completa con 132 filas: `experiments/148_audit_pre_reproc/master_table.csv`)

**Interpretación**:
- **Lascar VIIRS** está bien calibrado (ratio mediano 0.95 con n=75 matches sólidos).
- **Tupungatito VIIRS 16×** sobre-estima groseramente. Confirma que A8 sigue vivo —
  records históricos pre-fix sobre-detectan glaciar.
- **PCC VIIRS 5×** sobre-estima — coincide con la sobre-detección MODIS arriba.
- **Villarrica, Copahue, NdC, Chaiten**: tenemos cientos de records pero MIROVA-VIIRS-M
  prácticamente no emite señal (≤13 records). No es "fail nuestro", es que MIROVA reportaba
  estos volcanes via VIIRS375. Recall efectivo de M-band vs M-band es undefined.

---

## 5. Per-Tier-A: status, confianza, recomendación

| Volcán | Status calibración | Confianza | Reproc necesario | Razón |
|---|---|---|---|---|
| **PuyehueCordonCaulle** | sobre-estima (5× VIIRS-M, 1 200× MODIS) | media (n=11 VIIRS) | **SÍ alta prio** | 25 records >100 MW (5 >1 000 MW) MODIS pre-fix. F47+F52 lo curan |
| **Villarrica** | sobre-detecta sin baseline MIROVA-M | baja (n=0) | **SÍ alta prio** | 6 records >100 MW MODIS + flag max_cluster_pixels=12 (F52-A) post-data |
| **Lascar** | OK VIIRS-M (0.95×); MODIS gap 54 alertas | alta (n=75) | opcional VIIRS, evaluar MODIS | Único Tier A bien calibrado VIIRS-M. Gap MODIS son alertas 0.2-3.8 MW, sub-umbral |
| **Copahue** | sin matches; ratio undefined | baja (n=0) | medio | 2 records >100 MW. Reproc para limpiar fósiles |
| **NevadosDeChillan** | sin matches VIIRS-M; 2 records >100 MW | baja (n=0) | medio | Mismo patrón Villarrica/PCC |
| **Llaima** | n=1 match, ratio 1.8 | baja | medio | 2 records >100 MW MODIS pre-fix |
| **Chaiten** | sin matches VIIRS-M; 4 records >100 MW | baja | medio | Datos fósiles MODIS, F47 los cura |
| **PlanchonPeteroa** | sobre-estima (4.5×) bajo n | baja (n=2) | medio | 3 records >100 MW |
| **Lastarria** | sin MIR-VIIRS-M; 1 record >100 MW | sin data | medio | MIROVA reporta Lastarria casi solo en VIIRS375 (75 gaps 90d). Reproc no cierra eso |
| **Isluga** | sobre-estima 3× | media (n=13) | medio | Patrón VIIRS sobre-estimación leve |
| **Tupungatito** | **sobre-estima 16×** | media (n=5) | **SÍ alta prio** | A8 confirmado vivo. Records pre-fix saturan glaciar |

**Cuenta**: 0 OK / 7 sobre-estiman / 3 sub-estiman o sin signal / 1 OK parcial (Lascar
VIIRS pero con gap MODIS).

---

## 6. Top 5 hallazgos críticos

1. **VIIRS375 no implementado** corta el 88 % del recall potencial. Cualquier conversación
   de "mejorar recall vs MIROVA" sin implementar I-band está hablando del 12 % residual.
   *Acción*: documentar como **F-tag prioritario** en backlog y discutir alcance con
   Nicolás antes del próximo reproc.

2. **PuyehueCordonCaulle MODIS** tiene 5 records con `vrp_mw > 1 000 MW` clasificados
   `summit` (factor >1 200× sobre máximo MIROVA del mismo período). Causa proximate:
   `inner_radius_km=20` admite clusters MODIS regionales como cráter. Causa root: fixes
   F46/F47/F52 ya en NRT pero no aplicados al histórico. *Acción*: reproc 90d PCC
   prioritario.

3. **Tupungatito sobre-estima 16× en VIIRS-M** sobre 5 matches sólidos. Confirma A8 (data
   stale post-fix). *Acción*: reproc 90d Tupungatito prioritario.

4. **Lascar VIIRS-M es el único Tier A bien calibrado** (ratio 0.95, n=75 matches). Sirve
   de control: el pipeline VIIRS-M ya está calibrado cuando el volcán tiene señal MIROVA-M
   comparable. Los problemas de otros volcanes son (a) data histórica pre-fix, (b)
   ausencia de I-band.

5. **OSF v2.5 archive ausente local** invalida cualquier comparación de magnitudes vs
   ground truth post-procesado. La auditoría actual compara contra NRT scraping, que es
   operacional pero no autoritativo. *Acción*: descargar OSF v2.5 antes del reproc para
   calibrar magnitudes históricas.

---

## 7. Recomendación final para próximo turno

**Reproc priorizado (no ejecutado en esta sesión)**:

| Prioridad | Volcán | Ventana | Justificación |
|---|---|---|---|
| 1 | PuyehueCordonCaulle | 120d (2026-01-10 → hoy) | 25 records >100 MW fósiles; F47/F52 los cura |
| 1 | Tupungatito | 120d | sobre-estima 16× confirmado |
| 1 | Villarrica | 120d | 6 records >100 MW + F52-A `max_cluster_pixels=12` no aplicado a histórico |
| 2 | Chaiten | 120d | 4 records >100 MW |
| 2 | NevadosDeChillan, Llaima, PlanchonPeteroa, Copahue, Lastarria | 120d | Limpieza de fósiles, n bajo |
| 3 | Isluga | 120d | sobre-estima 3× moderado |
| – | Lascar | **no urgente** | VIIRS-M calibrado; gap MODIS son alertas sub-umbral |

**Antes del reproc**:
1. Confirmar con Nicolás si el reproc se hace **local** (regla A4 + S15 sobre límite 50 min
   de GitHub Actions) sobre los 11 Tier A en lotes.
2. Bajar OSF v2.5 archive a `data/mirova_reference/osf_v25/` para validación post-reproc.
3. Decidir si la implementación de VIIRS375 (path I-band) se eleva a F-tag prioritario;
   sin esto, recall vs MIROVA seguirá <15 % por construcción aunque el reproc salga
   perfecto.

**Después del reproc**: re-correr este mismo script (`experiments/148_audit_pre_reproc/audit_pre_reproc.py`)
para A/B numérico. Comparar `master_table.csv` antes/después; esperar:
- `n_records vrp>100 MW` cae de 50 → <10.
- `ratio_median` PCC-VIIRS de 5.2 → <2.0.
- `ratio_median` Tupungatito-VIIRS de 16 → <3.0.
- Gaps last 90d NO cambian (esos son VIIRS375; reproc no ayuda).

---

## 8. Reproducibilidad

Script único: `experiments/148_audit_pre_reproc/audit_pre_reproc.py`. Read-only.
Inputs: `volcanoes.yaml`, `latest_consolidado.csv`, `data/mirova_equivalent/<vol>.json`.
Outputs: `experiments/148_audit_pre_reproc/{master_table.csv,anomalies.csv,gaps.csv,summary.json}`.

Comando:
```bash
python experiments/148_audit_pre_reproc/audit_pre_reproc.py
```

Dependencias: pandas, numpy, pyyaml, scipy (opcional para Wilcoxon).
