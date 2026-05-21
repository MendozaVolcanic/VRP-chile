# Tupungatito — fix anchor `mirova_center` para paridad cluster selection S72

> **Status**: hallazgo importante que reabre decisión S65 PR #93 — con interpretación corregida.
>
> **Bottom line**: el cluster térmico que MIROVA NRT publica como ALERTA_TERMICA Muy Bajo para Tupungatito (64 records CONS, **TODOS sub-MW**, max 0.59 MW) está consistentemente **3.94 km ESE del vent yaml actual**. NO es violación de assumption MIROVA (todos <5 MW per Coppola 2016 §687). PERO nuestro pipeline elige OTROS features regionales más brillantes (probable Maipo, glaciar) como `primary_cluster` → ratio 10× inflado. Fix: restaurar `mirova_center` empírico (anchor para cluster selection), NO como verdad geológica.

## 1. Cadena de evidencia

### 1.1 F1.1 audit (S71) — coord vent vs centroide MIROVA

| Vol | OSF p50 dist vent | CONS NRT p50 dist | Verdict |
|---|---|---|---|
| Villarrica | 0.57 km | 14.07 km | ✅ Coords OK (cluster cerca del vent) |
| PCC | 0.40 km | 8.02 km | ✅ Coords OK |
| Chaiten | 0.46 km | 0.53 km | ✅ Coords OK |
| PlanchonPeteroa | 0.56 km | n=0 | ✅ Coords OK |
| **Tupungatito** | OSF gap | **5.21 km SE** | **⚠️ Drift sistémico ESE** |

### 1.2 F1.6 audit (S72) — análisis espacial 504 records VIIRS

- 84% records VIIRS dentro de 7 km vent
- Centroide MEDIANA cluster térmico: **(-33.40642, -69.78945)**
- Offset desde vent: **3.94 km ESE**
- Estabilidad: <0.5 km drift en 4 meses (cluster espacialmente estable)
- Modalidad: **unimodal** (1 cluster térmico bien definido)

### 1.3 F1.7 audit (S72) — distribución magnitud

64 ALERTA_TERMICA CONS Tupungatito (todas `Muy Bajo`):

| stat | mean | median | p10 | p90 | max |
|---|---|---|---|---|---|
| VRP_MW | **0.21** | 0.22 | 0.08 | 0.32 | **0.59** |

**100% records <1 MW**. Consistente con régimen Tier A Muy Bajo (Villarrica 0.11, Chaiten 0.15, PP 0.12).

**Coppola 2016 SP 426.5 §687**: *"these false detections typically radiate **less than 5 MW**"*. Las 64 ALERTA cumplen. NO es violación de assumption.

### 1.4 Verificación geológica Nicolás (2026-05-21)

> *"ya investigué, las coordenadas que me diste (-33.40642, -69.78945) no hay volcánico allá"*

Esto es **insight de Nicolás independiente del paper MIROVA**. MIROVA mismo no aplica QC visual sistemático sobre Tupungatito — sus 64 ALERTA Muy Bajo entran a la database OSF/CONS sin verificación geológica adicional.

### 1.5 Hallazgo arqueológico — bug fallback chain

Subagente F1.6 detectó que post-S65 (PR #93 removió `mirova_center`):
- Pipeline fallbackea a `volcano_lat/lon = (-33.4, -69.8)` (Smithsonian GVP nominal).
- **NO** a `vent_lat/lon = (-33.3890, -69.8264)` (cráter Nicolás-verificado).
- Por casualidad `volcano_lat` cae DENTRO del cluster térmico ESE.
- Resultado: records aparecen con `final_hotspot_dist_km ≈ 0.2 km` (medido desde volcano_lat).

**Bug fallback**: `get_effective_vent()` debería fallbackar a `vent_lat` cuando `mirova_center` ausente. La actual cae a `volcano_lat`. Documentar para fix S73+.

## 2. Re-interpretación correcta del caso Tupungatito

**❌ Lectura inicial errónea**: "MIROVA tiene FP sistémico no-volcánico en Tupungatito".

**✅ Lectura correcta** (post-F1.7):

1. MIROVA detecta correctamente 64 hotspots sub-MW (0.05-0.59 MW) en cluster ESE.
2. Esos hotspots son **dentro del régimen "Muy Bajo"** declarado por MIROVA (similar a Villarrica/Chaiten/PP).
3. Que las coords no correspondan a cráter activo verificado geológicamente es **insight de Nicolás** que MIROVA mismo no aplica.
4. **El problema NO es MIROVA. El problema es que nuestro `primary_cluster` no converge al mismo cluster ESE que MIROVA elige.**
5. Probable causa: nuestro pipeline escoge features regionales más brillantes (Maipo, glaciar Tupungato, FPs regionales) como `primary_cluster` porque tienen mayor `vrp_mw` → ratio 10× inflado.

## 3. Acción derivada — restaurar `mirova_center` como ANCHOR

### 3.1 Propuesta concreta

```yaml
# En volcanoes.yaml, entry Tupungatito:
mirova_center_lat: -33.40642
mirova_center_lon: -69.78945
# (centroide mediana cluster térmico VIIRS CONS NRT, n=420)
```

### 3.2 Justificación bibliográfica + empírica

- **El `mirova_center` no es "vent geológico" — es "anchor empírico de cluster selection"**. Función: dirigir `primary_cluster` hacia donde MIROVA puntea, no hacia donde está geológicamente el cráter activo.
- Mismo principio que **S64 Tupungatito mirova_center fix** previo (que se quitó S65 prematuramente).
- Conceptualmente equivalente a "tracking the thermal centroid MIROVA reports" para garantizar cluster paridad.

### 3.3 NO confundir vent_lat con mirova_center

| Campo | Significado | Tupungatito |
|---|---|---|
| `vent_lat/lon` | Cráter activo verificado geológicamente | (-33.388686, -69.826254) — cráter Nicolás S64 |
| `mirova_center_lat/lon` | Anchor empírico cluster térmico MIROVA NRT | (-33.40642, -69.78945) — propuesta S72 |
| `volcano_lat/lon` | Smithsonian GVP nominal | (-33.4, -69.8) — actual fallback erróneo |

### 3.4 Validación requerida pre-adopción (regla S33)

1. **R1 tests sintéticos**: confirmar que `mirova_center` afecta solo cluster selection, no detección.
2. **A/B reproc Tupungatito**: profile aislado con `mirova_center` nuevo + reproc 90d.
3. **Audit primario**: ratio mediano post-fix debe caer 10× → 1-3× (range Tier A Muy Bajo típico).
4. **R2 pixel-level**: cross-check con TIFs MIROVA archive si disponibles para Tupungatito.
5. **Si pasa todo** → adopción operacional en `volcanoes.yaml`.

## 4. Plan de implementación

| Paso | Acción | Costo |
|---|---|---|
| 1 | Crear `volcanoes_tupungatito_mc_v2.yaml` o profile + override `mirova_center` | ⚡ |
| 2 | Workflow A/B `reproc-tupungatito-mc-v2.yml` — 1 vol × 90d | 🔥 ~15 min |
| 3 | Audit primario vs CONS NRT (`pc.vrp_mw / mirova_vrp`) | ⚡ |
| 4 | R3 audit independiente | ⚡ |
| 5 | Si pasa → PR a main + adopción `volcanoes.yaml` | ⚡ |

Estimación impacto: ratio 10× → 1-3× (proyección F1.6 + razonamiento F1.7).

## 5. Aprendizaje meta A30

**A30 (S72 2026-05-21)** — **el `mirova_center` es anchor empírico, no verdad geológica**. Para clon literal MIROVA, debemos anclar a donde MIROVA puntea sus detecciones, independiente de si geológicamente corresponde a un cráter activo conocido.

**Heurística operacional**:
- Si MIROVA NRT publica consistentemente ALERTAs sub-MW en coord X sistemáticamente offset del `vent_lat` (Nicolás-verificado).
- Y el cluster es estable temporalmente (<1 km drift).
- → Setear `mirova_center: X` para que pipeline convergence en cluster MIROVA.
- Independiente de la interpretación geológica del cluster.

**Aplicación a otros vols**: revisar centroides térmicos en CONS NRT vs vent_lat actual para Lascar, Lastarria, Isluga, Llaima, Copahue, NdC. Si hay offset sistemático sub-MW similar a Tupungatito → candidato `mirova_center` similar.

## 6. Bug `get_effective_vent` fallback chain (S73+)

Issue: cuando `mirova_center` ausente, pipeline cae a `volcano_lat/lon` (Smithsonian GVP) en lugar de `vent_lat/lon` (cráter activo Nicolás-verificado).

Fix sugerido: en `pipeline/...py` función `get_effective_vent()`:
```python
def get_effective_vent(vol_config):
    if vol_config.get("mirova_center_lat") is not None:
        return vol_config["mirova_center_lat"], vol_config["mirova_center_lon"]
    if vol_config.get("vent_lat") is not None:
        return vol_config["vent_lat"], vol_config["vent_lon"]
    return vol_config["volcano_lat"], vol_config["volcano_lon"]  # final fallback
```

Verificar si la implementación actual respeta este orden. Si NO, fix S73+.

## 7. Referencias

- F1.1 audit S71 — coord vent vs centroide MIROVA 5 vols.
- F1.6 audit S72 — análisis espacial 504 records VIIRS Tupungatito + bug arqueológico fallback.
- F1.7 audit S72 — distribución magnitud 64 ALERTA: todas sub-MW.
- Coppola 2016 SP 426.5 §687 (FPs <5 MW), §675-696 (false alerts section).
- Coppola 2019 §1283-1288 (0-3% FP rate aceptado).
- S62 PR #93 (decisión S65 remover mirova_center — re-abrir).
- S64 verificación geológica cráter Nicolás (-33.388686, -69.826254).
