# Design doc S53: VRP en 3 regímenes diferenciados (Coppola 2024)

> Tipo: spec_brainstorming_design (skill superpowers-brainstorming)
> Fecha: 2026-05-17
> Autor: Claude + Nicolás
> Status: DRAFT — pendiente review usuario

## Motivación

VRP-chile S52 confirmó **sobre-detección estructural Villarrica VIIRS-I 375m**:
- MIROVA NRT reporta 0.1-0.3 MW para lava lake oculto sub-pixel
- VRP-chile reporta 3-10 MW (factor ~30× inflación)
- Causa raíz: Wooster MIR pixel-level está **fuera de su rango de validez (T>600K)** para señal sub-pixel con BT pixel mezclado

Skill `investigacion` S52 + lectura exhaustiva Coppola 2024 chapter S53 reveló
que MIROVA aplica **diferentes métodos según el régimen térmico** del target:

> "the VRP [Wooster] is inadequate for estimating the radiant power of
> low-temperature VTFs" (Coppola 2024, líneas 1163-1171)

## Las 3 preguntas MISSION.md aplicadas

1. **¿Está en papers MIROVA core?**
   - R1 Wooster MIR Eq.17: SÍ (ya implementado)
   - R2 Lava lake sub-pixel: SÍ (Coppola 2024 §"Lava lakes" líneas 2680-2716, método Burgi-Coppola)
   - R3 Crater lake hidrotermal: SÍ (Coppola 2024 §"Crater lakes" Eq.25 Ruapehu líneas 2738-2774)
2. (no necesita Q2-Q3 si Q1 sí para los 3)

**PASA MISSION.md** ✓ para los 3 regímenes.

## Arquitectura propuesta

### Régimen R1: Lava fresca >600K (status quo)

**Aplica**: erupciones efusivas, lava flows frescos, domos crecientes activos.

**Fórmula** (Wooster 2003, ya implementado):
```
VRP_MIR = A_pix × c × ΔL_MIR    (Eq.17 Coppola 2024)
```
con c = 2.88×10⁻⁹ (= WOOSTER_COEFF k/1e6 según `pipeline/process_viirs.py`).

**Sin cambios**. Mantener pipeline actual.

### Régimen R2: Lava lake magmático sub-pixel ~1000K (a implementar)

**Aplica**: Villarrica, Erebus-tipo, Erta Ale pequeños. Característica: lava
magmática expuesta pero sub-pixel (A_lake ≪ A_pix), BT_pixel mezclado con
background frío.

**Fórmula** (Coppola 2024 §"Lava lakes", inversión Eq.16):
```
1. Asumir T_e = 1000 K (lava lake típico, Burgi-Coppola convention)
2. Asumir ε = 0.95 (literatura volcánica)
3. Despejar A_hot desde ΔL_MIR observado:
   A_hot = ΔL_MIR / [c × B(λ_MIR, T_e)]
   (donde B es Planck radiance pixel-relativo)
4. Calcular VRP via Eq.16:
   φ_rad = A_hot × σ × ε × (T_e⁴ − T_bk⁴)
```

**Implementación**:
- Nueva función `compute_vrp_lava_lake_eq16(L_mir_hot, L_mir_bg, t_bk, T_e=1000, eps=0.95)`
- Activación: cuando `final_hotspot_source == "test1"` y `distance_class == "summit"` y record sub-MW (Wooster VRP < 1 MW)
- Reportar campo `pc.vrp_lava_lake_mw` adicional a `pc.vrp_mw` (Wooster)
- Frontend muestra ambos: "VRP Wooster (>600K)" y "VRP lava lake (sub-pixel ~1000K)"

**Calibración inicial**:
- T_e = 1000 K (Burgi-Coppola convention)
- ε = 0.95 (literatura volcánica)
- Vols aplicables: lista per-vol en `volcanoes.yaml` con flag `lava_lake_magmatic: true`
  - Villarrica: SÍ (verificado S51 detecciones <300m, S52 lava lake)
  - Otros: investigar futuro (NdC dome NO es lava lake, otros chilenos no tienen lava lake conocido)

### Régimen R3: Crater lake hidrotermal <600K (a implementar)

**Aplica**: Copahue (El Agrio), Planchón-Peteroa (laguna), futuros vols con
crater lake de agua.

**Fórmula** (Coppola 2024 Eq.25):
```
L_lake(λ, T_lake) = L_bk(λ, T_bk) + ΔL_tot(λ) × (A_pix / A_lake)
```

Despejar T_lake invirtiendo Planck → calcular φ_rad via Eq.16 con A_lake fijo.

**Implementación**:
- Nueva función `compute_vrp_crater_lake_eq25(L_mir_pixel, L_mir_bg, t_bk, A_lake, lambda_mir, eps=0.95)`
- Activación: cuando vol tiene flag `crater_lake_hydrothermal: true` en yaml
- Reportar campo `pc.vrp_crater_lake_mw`
- Calibración A_lake per-vol:
  - Copahue El Agrio: A_lake = 250,000 m² (Trunk & Bernard 2008)
  - Planchón laguna: A_lake = 50,000 m² (variable, Sentinel-2 baseline)

### Régimen NA: Magnitud no calculable

Cuando ningún régimen aplica (detección summit pero T_hot indeterminada),
reportar `vrp_mw: null` con flag explícito `magnitude_uncertain: true`.
Frontend muestra "Detección sin magnitud calibrada".

## Estructura código

### `pipeline/vrp_regimes.py` (NUEVO)

```python
def detect_regime(record) -> Literal["R1_wooster", "R2_lava_lake", "R3_crater_lake", "NA"]:
    """Determina el régimen VRP aplicable según volcano config + detection."""
    ...

def compute_vrp_lava_lake_eq16(L_mir_hot, L_mir_bg, T_bk, T_e=1000, eps=0.95) -> dict:
    """R2: lava lake magmático sub-pixel. Burgi-Coppola con T_e fijo."""
    ...

def compute_vrp_crater_lake_eq25(L_mir, L_bg, T_bk, A_lake, lambda_mir, eps=0.95) -> dict:
    """R3: crater lake hidrotermal. Coppola 2024 Eq.25 con A_lake calibrado."""
    ...
```

### Integración `pipeline/process_viirs.py` + `process_modis.py`

Después de calcular `pc.vrp_mw` (Wooster MIR actual), si el régimen del
volcán es R2 o R3, calcular campo adicional. NO sobreescribir Wooster.

### `volcanoes.yaml` flags nuevos per-vol

```yaml
- name: Villarrica
  ...
  lava_lake_magmatic: true
  lava_lake_T_e_assumed_K: 1000  # default Burgi-Coppola
  lava_lake_emissivity: 0.95

- name: Copahue
  ...
  crater_lake_hydrothermal: true
  crater_lake_A_m2: 250000
  crater_lake_lambda_mir_um: 3.74  # VIIRS I04 default
```

## Tests sintéticos (TDD obligatorio)

### `tests/test_vrp_regimes_eq16_lava_lake.py`

1. **Caso Villarrica 2026-05-11 06:00 NOAA20**:
   - Input: BT_mir_hot, BT_mir_bg, T_bk known
   - Expected: `vrp_lava_lake_mw ≈ 0.31 MW ± 30%` (MIROVA reporta 0.31)
2. **Caso Villarrica 2026-02-15 05:00 NOAA21** (159m del cráter, MW desconocido):
   - Verificar `vrp_lava_lake_mw < vrp_wooster_mw` (sub-pixel correcto)
3. **Edge cases**:
   - L_hot ≈ L_bg → A_hot → 0 → VRP → 0 (no detección)
   - L_hot >> L_bg → A_hot grande → VRP grande pero limitado a A_pix
   - T_bk = T_e → φ_rad = 0 (sin gradiente)

### `tests/test_vrp_regimes_eq25_crater_lake.py`

1. **Caso Copahue mocked**: A_lake=250000, ΔL pequeño → T_lake ~330K (lago tibio)
2. **Caso Villarrica mocked** (validar que NO se aplica R3):
   - Si volcanoes.yaml NO tiene `crater_lake_hydrothermal: true` → función no se llama
3. **Edge cases**: A_lake >> A_pix (Lago Calbuco hipotético), A_lake = 0 (config inválido)

### `tests/test_vrp_regimes_selector.py`

1. Volcano sin flags → R1 default
2. Volcano con `lava_lake_magmatic` → R2
3. Volcano con `crater_lake_hydrothermal` → R3
4. Conflicto (ambos flags true) → error claro

## Criterios de aceptación

### CA1: Tests verde
- Suite completa: 312 passed + tests nuevos (~15-20) sin regresiones

### CA2: Magnitud Villarrica converge a MIROVA
- A/B reproc 30d Villarrica
- Ratio mediano `vrp_lava_lake_mw / MIROVA_VRP` ∈ [0.5, 2.0]
- (vs ratio actual ~30× con Wooster)

### CA3: Sin regresión recall otros vols
- F1 global mantiene ≥98% (era 98.3% S48)
- Recall otros Tier A sin cambio

### CA4: Audit espacial-aware mantiene
- FP(a) drift real ≤ 5 (era 2 S48)
- Coincidencia espacial ≤5km como S48

### CA5: Dashboard claridad
- Frontend muestra 2 valores cuando aplica R2/R3:
  - "VRP Wooster" (Eq.17, lava fresca, hist convention)
  - "VRP lava lake" o "VRP crater lake" (Eq.16/25, MIROVA-like)
- Disclaimer: cuál usar según contexto volcanológico

## Roadmap implementación (en paralelo Tracks)

### Track A — R2 Lava lake Villarrica (PRIORITARIO, S53-S54)

- [ ] S53 (esta sesión): design doc (este archivo) + approval Nicolás
- [ ] S53 cierre: tests sintéticos TDD `test_vrp_regimes_eq16_lava_lake.py`
- [ ] S54: implementación `vrp_regimes.py` función R2 + integración process_viirs.py
- [ ] S54: A/B reproc Villarrica window 30d
- [ ] S54 cierre: validación CA2 (magnitud converge MIROVA)

### Track B — R3 Crater lake hidrotermal (S55)

- [ ] S55: tests sintéticos R3 + implementación Eq.25
- [ ] S55: A/B Copahue / Planchón con calibración A_lake

### Track C — Documentación + Frontend (S56)

- [ ] S56: dashboard muestra 2 valores cuando aplica
- [ ] S56: docs/HYPOTHESIS_LOG entries H_S53_R2_LAVA_LAKE + H_S55_R3_CRATER_LAKE
- [ ] S56: docs/MIROVA_DIVERGENCES update sección magnitud

### Track D — Aveni 2025 Eq.9 backlog (NO prioritario, S57+)

- [ ] Backlog `tasks/backlog_no_mirova.md` entry: Aveni 2025 Eq.9 NO aplica
      Villarrica, postergado a profile experimental Lascar fumarólico

## Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| T_e=1000K asumido puede no ser exacto Villarrica | Validar empíricamente vs CSV MIROVA Villarrica; calibrar por vol si necesario |
| ε=0.95 puede variar | Default 0.95, configurable per-vol en yaml |
| R2 R3 selector mal aplicado a otro vol | Tests selector exhaustivos |
| Sobre-engineering 3 regímenes para un solo problema (Villarrica) | Empezar minimalista: solo R2 Villarrica. R3 después. R1 sin cambios. |
| Magnitud R2 nueva confunde a operadores SERNAGEOMIN | Dashboard claridad obligatoria CA5 |

## Pre-mortem (R4)

Si esto fracasa en S54 A/B:
- **Hipótesis fracaso 1**: T_e=1000K incorrecto Villarrica → calibrar 800-1400K rango
- **Hipótesis fracaso 2**: Wooster background actual contaminado → afecta ΔL → fix L_bg primero
- **Hipótesis fracaso 3**: MIROVA usa método diferente al Coppola 2024 chapter publicado → buscar reverse engineering en mirovaweb.it gráficos

Si las 3 fallan: documentar como divergencia metodológica MIROVA, mantener Wooster status quo, no engañar SERNAGEOMIN con magnitudes inventadas.

## Self-review (skill brainstorming step 7)

- ✅ Placeholders: ninguno crítico (constantes con valores específicos)
- ✅ Contradicciones: ninguna detectada
- ✅ Ambigüedad: Track D Aveni 2025 explícito como descartado, no ambiguo
- ✅ Scope: 3 regímenes pero implementación R2 primero (minimalista), R3 después
- ⚠️ Riesgo principal: T_e=1000K asumption — mitigado con CA2 cuantitativa
- ✅ MISSION.md: 3 preguntas explícitas, R2 y R3 ambos PASAN
- ✅ Tests TDD: detallados antes de implementación

## Próximos pasos

1. **Nicolás review** este design doc
2. Si OK: skill `test-driven-development` → escribir tests sintéticos
3. Implementar R2 Villarrica
4. A/B reproc Villarrica 30d
5. Validar CA1-CA5
6. Si CA2 cumple: adoptar y replicar R3
7. Si CA2 no cumple: pre-mortem hipótesis fracaso
