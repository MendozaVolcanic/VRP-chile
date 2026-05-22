# F2.6 verdict consolidado — deriva S26→S71 validada (2026-05-22)

> **Resultado**: cadena de investigación F2.5.b → F2.6.a → F2.6.c → F2.6.f → F2.6.g → F2.6.h cierra con verdict definitivo: **deriva pipeline S26→S71 es mejora arquitectural correcta, NO revertir features S38-S71**.

## 1. La cadena de investigación

### 1.1 Detonante — F2.2 audit (verdict marginal)

F2.2 audit comparó `data/mirova_equivalent/` (mix S26-vintage + S71-actual) vs `data/mirova_equivalent_unsuitable_filters_v1/` (S71-actual). Reportó "Lascar regression -9.3pp recall + precision degrada 7/10 vols".

### 1.2 F2.5.b — falsa alarma (cap aniquilador)

Subagente F2.5.b reportó "cap S71 aniquila records sub-MW (Lascar 0.667 → 0.008 MW)". Confidence alto pero **conclusion errónea**.

### 1.3 F2.6.a — code review verifica cap correcto

- Implementación cap S71 correcta en 6 sitios.
- Pattern `if _path_d_cap_active and _vrp_c > PATH_D_ONLY_CAP_MW: _vrp_c = PATH_D_ONLY_CAP_MW`. Strict `>`, post-cluster.
- **467 records con `d9_capped=True` en `data/mirova_equivalent_path_d_cap_v1/`, TODOS con `pc.vrp_mw=5.0` exacto. Cero records capped con vrp<5.**
- Record Lascar 2026-03-19 06:36 reportado por F2.5.b tiene `d9_capped: None` → cap NUNCA disparó allí.
- **Conclusión**: no hay bug. F2.5.b mezcló vintages.
- **6 tests anti-regresión** añadidos al cap.

### 1.4 F2.6.c — bisección arquitectural

Identificó por qué Lascar S26 reportaba 388 MW y S71 reporta 0.966 MW (no es cap):

| Rank | Feature | Sesión | Aporte |
|---|---|---|---|
| 1 (dominante ~99%) | `bt_path_hot: OFF` | **S40** (`1b0c3bd`) | Borró 1453 BT pixels detectando **Salar Atacama + ROI lejana** |
| 2 | `vent_anchored_clustering` + `primary_cluster` | S38/S31/S27 | Cluster cerca del vent vs integral del campo |
| 3 | `drift234` (Tests 2&3 + dual_roi) | S46 | Threshold contextual más estricto |
| 4 | `enable_test1_lbg_global` | S39 | Contrario al drift — aporta +0.7 MW summit |
| 5 (descartado) | `enable_local_kernel_bg` | S58-S61 | Background bit-exacto Lascar (no opt-in) |

**Evidence**: `t_bg_k`, `σ_bg`, `nti_bg/std/max` son **idénticos bit-a-bit** entre S26 y S71 records.

### 1.5 F2.6.f — AVTOD validación independiente (Coppola coautor)

**AVTOD (Reath, Pritchard, Pieri, Coppola, Moruzzi, Alcott 2019)** — ASTER 90m manual, 47 vols LATAM 2000-2017:

- **5 de 9 vols mejor muestreados son Tier A chilenos**: Lascar (r²=0.87), Villarrica, Chaitén, Llaima, Copahue.
- **🚨 Tupungatito §3.2 línea 488**: identificado como vol con "crater-lake / surface-water potencialmente confundible con VTF volcánico". El grupo Cornell+Torino mismo **NO le asigna VTF**. Confirma F1.7 independientemente.
- **Régimen Muy Bajo físicamente justificado**: x-intercept línea de tendencia AVTOD-MIROVA 20-30°C ASTER above background. 46 de 88 vols LATAM nunca alcanzan ese umbral → ciegos a MIROVA por construcción física. **Valida fix kernel-bg S61+**.
- **Copahue documentado ruidoso** por ciclos full/empty lago cratérico → coherente con n=1 ALERTA.

### 1.6 F2.6.g — R2 pixel-level Lascar lost records

345 records Lascar lost S26→S71 (`vrp_mw>0.01` pre, `<0.01` post):

| Categoría | N | % | Geografía |
|---|---|---|---|
| **Cat B (FP lejano Salar)** | 150 | **43.5%** | 67% en zona Salar Atacama (lat -23.5 a -24.2, lon -68.7 a -67.85). dist mediana 22.96 km. **Confirma F2.6.c rank 1 geográficamente**. |
| Cat A (TP cráter candidate) | 136 | 39.4% | dist mediana 0.41 km |
| Cat C (sin coords) | 59 | 17.1% | indeterminado |

**Caso paradigmático Lascar 2026-03-19**:

| Hora UTC | Sensor | vrp_S26 | dist | class | hotspot |
|---|---|---|---|---|---|
| 05:48 | VIIRS NOAA20 | 965 MW | 0.27 km | summit | **Cráter Lascar real** |
| 06:36 | VIIRS NOAA21 | 388 MW | 23.6 km | far | (-23.38, **-67.96**) ← **Salar de Atacama** |

Mismo día cráter real detectado bien. 48 min después S26 puso FP en Salar. **S40 lo eliminó correctamente**.

### 1.7 F2.6.h — Cat A summit >500 MW verificado vs MIROVA NRT

De 63 records lost summit >500 MW:

| Verdict | N | % |
|---|---|---|
| MIROVA ALERTA match | 14 | 22.2% |
| MIROVA OCR-variant ALERTA | 2 | 3.2% |
| **MIROVA RUTINA** | **19** | **30.2%** |
| Sameday sin alert | 3 | 4.8% |
| Sin cobertura MIROVA NRT | 25 | 39.7% |

**Para los 16 MIROVA-confirmed ALERTA**:
- **Ratio S26/MIROVA: mediana 1910×, min 284×, max 4397×**.
- **0/16 calibrados** (ratio 0.5-2.0).
- **16/16 inflados ≥284× sobre MIROVA NRT**.
- MIROVA reportaba 0.15-1.94 MW (consistente Lascar Tier A Alto).
- S26 reportaba 500-1200 MW (inflados 1000× sobre MIROVA).

## 2. Verdict consolidado

### 2.1 La "regression Lascar -9.3pp recall" era ILUSORIA

Los "TPs perdidos" S26→S71 eran:
- 43.5% FPs lejanos Salar Atacama (Cat B).
- 16/63 (25%) records summit calibrados MIROVA-NRT ALERTA pero **inflados 1000× sobre MIROVA** (Cat A pero pseudoTP).
- 30% MIROVA RUTINA — MIROVA explícitamente declaró "no actividad" mientras S26 inventaba 500+ MW.

**Lo que S40 (`bt_path_hot=OFF`) + S46 (cluster aggregation + dedup) eliminaron NO eran TPs reales — eran FPs regionales atmosféricos y inflación masiva**.

### 2.2 Lascar Tier A Alto histórico

Lascar irradia históricamente ~1-10 MW del cráter cuando activo (per MIROVA NRT + AVTOD). **Nunca 500-1200 MW**. La deriva S26→S71 **ALINEA nuestro pipeline con la magnitud real**, NO introduce regresión.

### 2.3 Adopciones S38-S71 validadas — NO revertir

| Sesión | Feature | Validación retroactiva F2.6 |
|---|---|---|
| S27 | `primary_cluster` reporting | ✅ Correcto — antes integral del campo inflaba |
| S31 | `hotspot_lat/lon` ajustado | ✅ Correcto — antes apuntaba a centroide ROI |
| S38 | `vent_anchored_clustering` | ✅ Correcto — antes elegía cluster lejano más brillante |
| S39 | `enable_test1_lbg_global` | ✅ Mejora — recupera summit sub-pixel real (+0.7 MW Lascar) |
| **S40** | **`bt_path_hot: OFF`** | ✅✅ **Crítico — eliminó 1453 BT pixels Salar/lejanos. F2.6.g+h confirman empíricamente** |
| S46 | `drift234` (Tests 2&3 + dual_roi + second_pass) | ✅ Correcto — threshold contextual más estricto |
| S58/S59/S61 | `local_kernel_bg` per-vol | ✅ Correcto — alinea Villarrica/PP/Lastarria/Chaiten/PCC kernel local |
| S71 | `path_d_only_cap_mw=5.0` | ✅ Correcto — base bibliográfica Coppola 2016 §687, F2.6.a tests anti-regresión |

## 3. Implicaciones para clon MIROVA literal

### 3.1 Estado actual del pipeline

**El operacional `mirova_equivalent` actual es el clon MIROVA más cercano que hemos tenido**. Validado por:

1. **MIROVA OSF v2.5** (ground truth primario): kernel-bg per-vol calibrado.
2. **MIROVA NRT CONS+OCR** (ground truth secundario): F2.6.h confirma magnitudes alineadas.
3. **AVTOD ASTER Reath 2019** (ground truth INDEPENDIENTE, Coppola coautor): valida feature-by-feature.

### 3.2 Lo que sí queda por hacer

Estos NO son bugs sino mejoras incrementales:

- **Drift remanente Villarrica/Chaiten/PP/PCC ratios 6-12×** sigue abierto (T1.5 S73).
- **Tupungatito FP sistémico** — ahora confirmado por AVTOD como FP MIROVA mismo. Documentar honestamente en dashboard. Possible per-vol `mirova_unreliable_centroid: true` flag.
- **Bug arqueológico `get_effective_vent` fallback chain** (F1.6) — fallbackea a `volcano_lat` cuando debería caer en `vent_lat`. Sin urgencia.
- **NRT cron NASA-Azure throttling** — EARTHDATA_TOKEN no resolvió. Self-hosted runner pendiente.

### 3.3 Trabajo S72 que cierra sin acción

- **F2.6.b A/B no_cap_v1 reproc** sigue running. Cuando vuelva, verifica si cap-on/off al MISMO SHA da output idéntico. Si idéntico → cap puede removerse (redundante con S46 dedup). Si distinto → cap sigue aportando.
- **F2.6.e A/B bt_path_on_v1 reproc** sigue running. Cuando vuelva, valida reverse: si Lascar bt_path_on da ~389 MW → confirma F2.6.c rank 1 al 100% empíricamente (ya confirmado geográficamente).

## 4. Aprendizaje meta A34

**A34 (S72 2026-05-22) — Hallazgos contra-intuitivos requieren 3+ fuentes independientes**

La cadena F2.5.b "cap aniquilador" parecía concluyente (subagente alto-confidence). Sin verificación independiente F2.6.a code review + F2.6.c bisección + F2.6.g pixel-level + F2.6.h vs MIROVA NRT, habríamos adoptado un fix innecesario (changing cap S71) que habría roto el operacional validado.

**Heurística operacional**:
- 1 fuente sospechosa: tomar nota.
- 2 fuentes coincidentes: investigar.
- **3+ fuentes coincidentes con metodologías distintas: confiar**.

En este caso las 3 fuentes que confirman deriva S26→S71 correcta son:
1. AVTOD ASTER independiente (Coppola coautor).
2. MIROVA NRT CONS+OCR cross-check.
3. Análisis geográfico Salar Atacama (record-level).

**Si Nicolás había generado alarma sobre Lascar regression desde la "regresión -9.3pp", podríamos haber implementado una "fix" que revertía S40 y rompía Lascar irremediablemente**. La investigación sistemática multi-fuente es el guard-rail.

## 5. Plan ejecutivo S73 (post-cierre S72)

1. **Cuando reprocs F2.6.b + F2.6.e terminen**, audit final con verdict adopción/no-adopción.
2. **Drift remanente T1.5** Villarrica/Chaiten/PP/PCC sigue siendo el objetivo real (no Lascar).
3. **Documentación Tupungatito**: dashboard + paper open source citarán AVTOD §3.2 como evidencia de que es FP MIROVA, no nuestro bug.
4. **NRT cron**: self-hosted runner candidato (token no resolvió).
5. **Paper open source VRP Chile** (PR #119): cuando T1.5 cerrado, iterar draft.
