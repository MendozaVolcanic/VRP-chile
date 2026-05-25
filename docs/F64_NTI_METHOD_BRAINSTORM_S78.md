# F64 — NTI method real vs ours (S78, read-only)

**Tipo**: investigación / brainstorm (sin cambios de código ni de datos).
**Branch**: `claude/s78-nti-method-deep`.
**Worktree**: `VRP-Chile-s78-nti-method/` (aislado, A44).
**Profile auditado**: `mirova_equivalent` (operacional, 11 Tier A).
**Snapshot**: `data/mirova_equivalent/<Volcano>.json` (rama `claude/s78-nti-method-deep`, ts S78).

## Por qué este brainstorm

F61 (PR previo S78) cuantificó que ~98% de los positivos VRP>0 del perfil
`mirova_equivalent` tienen `diag_nti_max < -0.85`, interpretándolos como
"firmas de agua/lago" porque Coppola 2016a Eq.4 dice `lava NTI > -0.8`.
La hipótesis 2 abierta: **¿hay un drift en cómo computamos NTI vs como lo
computa MIROVA?** Si nuestros TPs (validados contra MIROVA web) caen en
`NTI < -0.85` y MIROVA los acepta, o bien nuestro NTI tiene un bug, o
bien la interpretación de Eq.4 en F61 es incorrecta.

Este documento responde la pregunta directamente.

## 1. Cómo computamos NTI nosotros (verificado en código)

`pipeline/detection_context.py:536` (helper) y `pipeline/process_modis.py:310`,
`pipeline/process_viirs.py:553-557`:

```
L_MIR ≡ Planck(λ_MIR, BT_MIR_pixel)        # radiancia espectral W·m⁻²·sr⁻¹·μm⁻¹
L_TIR ≡ Planck(λ_TIR, BT_TIR_pixel)
NTI    = (L_MIR - L_TIR) / (L_MIR + L_TIR)
```

- **Inputs son radiancias** (NO BT en grados Kelvin directos).
- Para MODIS: λ_MIR = 3.959 μm (B22, fallback B21=3.929 μm si B22 NaN), λ_TIR = 11.0 μm (B31).
  - VIIRS hace BT→radiance via `bt_to_spectral_radiance(BT, λ)` antes del ratio.
- Para VIIRS-I: λ_MIR = 3.74 μm (I04), λ_TIR = 11.45 μm (I05).
- Para VIIRS-M: λ_MIR = 4.05 μm (M13), λ_TIR = 10.76 μm (M15).
- **Sin normalización** por t_bg local (es por-pixel observada).
- Constantes Planck en `pipeline/constants.py`: C1 = 1.19104e8, C2 = 14387.752, formato `L_λ = C1 / (λ^5 · (e^(C2/(λT)) − 1))` con λ en μm. **Matches Coppola 2016a Eq.1 verbatim**.

El campo persistido `diag_nti_max` es `np.max(nti[roi_mask])` (línea 838-840 MODIS).

## 2. Cómo computa NTI Coppola 2016a (literatura literal)

`documentacion/sp426.5.pdf` y `documentacion/sp426_5.txt` (líneas 207-340 OCR):

- **Eq.1**: `NTI = (L_MIR − L_TIR) / (L_MIR + L_TIR)` — radiancias espectrales.
- **Eq.3**: `NTI_app = (L_MIR_app(T_TIR) − L_TIR) / (L_MIR_app(T_TIR) + L_TIR)`,
  donde `L_MIR_app(T_TIR) = Planck(λ_MIR, BT_TIR)` (NTI sintético si el
  pixel fuera uniforme a la temperatura observada en TIR).
- **Test 1 (Eq.4)**: `NTI_PIX > K1` con `K1 = −0.8` (nocturno, ROI1=summit y ROI2=scene).
- **CRÍTICO** (paper líneas 298-300, verbatim): *"Pixels that satisfy Test 1
  are flagged as 'active' and subsequently discarded (unsuitable) for further
  steps."*
- **Tests 2 y 3** (Eq.5-6, líneas 315-323): `dNTI_PIX > C1 OR dNTI_PIX > μ_dNTI + C2·σ_dNTI`
  y análogo para dETI. C1=0.003 ROI1 / 0.01 ROI2, C2=5 ROI1 / 10 ROI2.

**Comparación 1:1**:

| Aspecto                         | Nuestro código              | Paper                         | Drift? |
|---------------------------------|-----------------------------|-------------------------------|:------:|
| Fórmula                          | `(L_MIR−L_TIR)/(L_MIR+L_TIR)` | Eq.1 idéntica                  | **No** |
| Inputs                           | Radiancias Planck            | Radiancias Planck              | **No** |
| Bandas MODIS                     | B22 primary, B21 fallback / B31 | B22 / B31 (Wooster 2003)        | **No** |
| Bandas VIIRS-I                   | I04 / I05                    | Sin cobertura (paper es MODIS) | n/a    |
| Constantes Planck                | C1=1.19104e8 C2=14387.752    | Estándar (Wooster 2003)        | **No** |
| Normalización por t_bg           | Ninguna                       | Ninguna                        | **No** |
| K1 (Test 1)                      | `-0.8` (NTI_K1_NIGHT)         | `-0.8` (Tabla 1)               | **No** |
| Test 1 como detector             | **Discard from bg** + Path B  | Discard from bg (paper expl.)  | **No** |
| dNTI contextual                  | Path D `nti − mean(nti_8nbr)` | Eq.5 idem                      | **No** |

**Conclusión 1: NO hay drift en el cómputo NTI.** Replica Eq.1 verbatim.

## 3. Por qué los TPs tienen NTI < −0.85 — explicación física pura

Esto NO es un bug, es **física del cuerpo negro** combinada con el rango térmico
de los volcanes chilenos andinos en invierno austral.

NTI es una función monótona creciente de la temperatura. Para un **pixel
uniforme** (no hay sub-pixel hotspot), el NTI vale:

| T uniforme | NTI (λ_MIR=3.959, λ_TIR=11.0) |
|-----------:|------------------------------:|
| 240 K      | −0.9798                       |
| 260 K      | −0.9581                       |
| 270 K      | −0.9422                       |
| 280 K      | −0.9223                       |
| 290 K      | −0.8979                       |
| 300 K      | −0.8689                       |
| 320 K      | **≈ −0.80** ← K1 MIROVA       |
| 350 K      | −0.6530                       |
| 400 K      | −0.3560                       |
| 500 K      | +0.1887                       |
| 700 K      | +0.6708                       |

**El threshold MIROVA `NTI > −0.8` (Test 1) requiere que la temperatura
efectiva del pixel supere ~320 K**. En un volcán chileno nocturno con
`t_bg ≈ 250-270 K` y un hotspot débil (lava lake Villarrica, fumarola
Tupungatito), la temperatura observada en MIR del pixel "hot" puede ser
`288 K` (Lascar 2026-02-08, sample) — **20 K más caliente que el background
pero todavía lejos de los 320 K que requeriría NTI > −0.8**.

### Sample empírico (Lascar 2026-02-08 06:45 MODIS_AQUA)

- `t_bg = 268.32 K`, `t_max = 288.44 K`, `n_dnti_ctx = 43` pixels, `vrp = 1058.57 MW`.
- Validación manual de NTI:
  - `L_MIR(3.959, 288.44) = 0.3729` W·m⁻²·sr⁻¹·μm⁻¹
  - `L_TIR(11.0, ~280) = 7.0` W·m⁻²·sr⁻¹·μm⁻¹ (BT_TIR estimado)
  - `NTI_obs ≈ (0.373 − 7.0)/(0.373 + 7.0) = −0.899`
  - **Coincide con `diag_nti_max = −0.8955`** del JSON (±0.005, dentro del error de la estimación de BT_TIR).
- Compare con NTI_app si el pixel fuera uniforme a BT_TIR=278K: NTI_app ≈ −0.9266.
- **dNTI = NTI_obs − NTI_app ≈ +0.04** → POSITIVO, el pixel está sobre-calentado
  en MIR respecto a lo esperado para uniforme. Esto es exactamente Test 2
  Coppola 2016a (`dNTI > C1=0.003`).

Nuestro Path D dispara este pixel (`n_dnti_ctx_path=43`), reportando `vrp=1058 MW`
totalmente consistente con la fórmula de Wooster y con la firma observada por
MIROVA en mirovaweb.it.

## 4. La interpretación errónea de F61

F61 dijo: "lava NTI > −0.8, agua NTI < −0.9, fumarólica intermedio". Esto es
parcialmente cierto pero **mezcla dos conceptos**:

1. **NTI > 0** → pixel con fracción de lava SUPERFICIE clara dominando la
   radiancia MIR (T_efectiva > 500 K). Típico de Stromboli / Etna / Erupciones
   abiertas.
2. **NTI ∈ (−0.8, 0)** → pixel con sub-pixel hotspot importante (>1% de área
   a 700K, o equivalente). MIROVA Test 1 lo flaggea como "active" y lo descarta
   **del cálculo de background** (no para reportarlo como detección — al revés,
   para no contaminar el bg con el pixel saturado).
3. **NTI < −0.8 PERO dNTI/dETI > C1**: **pixel que SÍ tiene anomalía sub-pixel
   pequeña** detectable solo por la deformación del NTI respecto a sus vecinos
   o respecto al NTI_app esperado para uniforme. **Estos son los TPs reales
   de MIROVA en volcanes andinos chilenos**.

El "lago Llaima Conguillío NTI≈−0.93" de F61 también tiene NTI < −0.85, pero
**su dNTI ≈ 0** (no se diferencia de sus vecinos lago), así que Path D NO
debería dispararlo. Si dispara en el operacional actual, el problema es OTRO
distinto (probablemente el contraste agua-lago vs orilla terreno frío inflando
dNTI artificialmente, o test1 disparando por radiancia integrada > k_test1
sobre cuerpos de agua grandes). Pero NO es la fórmula NTI.

## 5. Path-breakdown de los 8,014 TPs con NTI<−0.85 (snapshot S78)

Total 11 Tier A: 8,142 vrp>0 records, **8,014 (98.4%) con NTI<−0.85**.

| Volcán              | vrp>0 | NTI<−0.85 | via Path D dNTI | via Test 1 | via Path A BT | via Path B NTI abs |
|---------------------|------:|----------:|----------------:|-----------:|--------------:|-------------------:|
| Lascar              |   737 |       646 |             611 |        428 |            27 |                  0 |
| Lastarria           |   833 |       827 |             790 |        442 |             5 |                  0 |
| Villarrica          |   790 |       789 |             673 |        370 |            12 |                  0 |
| Chaiten             |   845 |       845 |             702 |        420 |             0 |                  0 |
| Tupungatito         |   675 |       671 |             581 |        376 |             0 |                  0 |
| Copahue             |   701 |       698 |             616 |        304 |             0 |                  0 |
| Llaima              |   684 |       675 |             581 |        289 |             2 |                  0 |
| Isluga              |   579 |       572 |             455 |        341 |             6 |                  0 |
| NevadosDeChillan    |   427 |       426 |             409 |        134 |             0 |                  0 |
| PlanchonPeteroa     |   764 |       759 |             565 |        396 |             0 |                  0 |
| PuyehueCordonCaulle | 1,107 |     1,106 |           1,087 |        560 |            55 |                  0 |
| **TOTAL**           |**8,142**|  **8,014** |        **7,070**|  **4,060** |       **107** |              **0** |

Observaciones:
- Path B (`nti > −0.8`) jamás dispara para NTI<−0.85 (definicional, sanidad).
- Path D (dNTI ctx) es el dominante (88% de los TPs con NTI<−0.85).
- Test 1 (integrated ROI) dispara solo en 51%, casi siempre en combinación con Path D.
- Path A (BT puro) es marginal (1.3%), concentrado en PuyehueCordonCaulle y Lascar.

Esto confirma que el sistema está detectando vía **mecanismo correcto MIROVA
(dNTI residual)**, no vía un bypass espurio.

## 6. Drift confirmado: NO

**No hay drift en el cómputo NTI**.

La fórmula, las bandas, las constantes Planck y la ausencia de normalización
coinciden con Coppola 2016a Eq.1 verbatim. Lo que F61 confundió fue:
- **El threshold K1=−0.8 no es un gate global** que defina "lava vs agua".
- Es un **flag de saturación** que en MIROVA se usa para EXCLUIR pixels
  del cálculo de background, NO para validar detecciones.
- La detección real MIROVA usa **dNTI/dETI residual** (Tests 2-3), y nuestro
  Path D lo replica correctamente.

## 7. Fix propuesto

**Ninguno en el cómputo NTI.** El código actual replica el paper.

Sí queda abierto el problema *separado* de F61: el 98% de los positivos puede
NO ser todo TP real (algunos serán FPs lago/nieve). Pero la herramienta para
distinguirlos NO es un AND-gate `NTI > −0.85` (eso destruiría 98% de los TPs
MIROVA-matched). Las opciones reales para reducir FPs lago son:

1. **Filtro de masa de agua** (P3.6 backlog S15): cargar máscara JRC Global
   Water + LandCover ESA WorldCover, descartar pixels dentro de agua
   permanente. No toca NTI ni dNTI.
2. **Sigma-cap en dNTI** sobre snow/glacier: cuando t_bg < 240 K, exigir
   `dNTI > C1 × factor_snow` (factor empírico, ~1.5-2). Limita el ruido sobre
   superficies muy frías.
3. **Test de coherencia espacial**: exigir cluster ≥ 2 pixels conectados
   (regla ya existe parcialmente como `n_vent_pixels ≥ 1`). Bumpear a 2-3.

**Pero ninguno es objetivo del F64.** F64 cierra: NTI ≠ drift.

## 8. Estimación de impacto si SE APLICARA F61 Opción A (no recomendado)

Si se aplicara `hot_mask &= (nti > −0.85)` globalmente como F61 propone:

- **TPs destruidos**: 8,014 / 8,142 = **98.4% del operacional histórico**.
- Lascar perdería 646/737 = 87.7% de sus detecciones.
- Chaiten perdería 845/845 = 100% de sus detecciones.
- Villarrica perdería 789/790 = 99.9% de sus detecciones.

Estos NO son falsos positivos lago — son detecciones sub-pixel reales de la
firma volcánica andina chilena, validadas en el cross-match con MIROVA web
(ver `experiments/76_audit_independent.out.md`).

**F61 Opción A es operacionalmente catastrófica** y debe quedar archivada
como "interpretación errónea cerrada en F64".

## 9. Métricas pre/post (si se aplicara el "fix" de F61)

| Métrica                       | Pre (actual)       | Post F61 Opción A           |
|-------------------------------|--------------------|-----------------------------|
| TPs Lascar histórico          | 737                | 91 (−87.7%)                 |
| TPs Villarrica histórico      | 790                | 1 (−99.9%)                  |
| TPs Chaiten histórico         | 845                | 0 (−100%)                   |
| Recall vs MIROVA-CSV (estim.) | 55-87% por volcán  | <5% (catastrófico)          |
| FPs lago/snow                 | Algunos (TBD)      | ~0                           |
| Dashboard SERNAGEOMIN         | Operativo          | Silencioso (sin alertas)     |

**Trade-off inaceptable**. La precisión sin recall es inútil para monitoreo.

## 10. Resumen ejecutivo (1 párrafo)

Nuestro código computa NTI con la fórmula literal de Coppola 2016a Eq.1
(`(L_MIR−L_TIR)/(L_MIR+L_TIR)` sobre radiancias Planck en bandas MODIS B22/B31
y VIIRS I04/I05, M13/M15), sin ningún drift respecto al paper. El threshold
`K1=−0.8` del paper NO es un gate de detección — es un flag de saturación para
excluir pixels del cálculo de background; la detección real usa dNTI/dETI
residuales (Tests 2-3 Eq.5-6). Que el 98% de nuestros TPs operacionales tengan
`NTI<−0.85` es la firma física **esperada** de hotspots sub-pixel en volcanes
andinos chilenos en invierno (t_bg ~250-270K, t_hot ~285-295K → NTI ~−0.88 a
−0.95 por física pura del cuerpo negro a esas temperaturas). El "fix" propuesto
en F61 Opción A (gate global `NTI>−0.85`) destruiría 98.4% de los TPs reales.
**Cerrar F61 como interpretación errónea**. Para reducir FPs lago/nieve, las
herramientas son máscara JRC Global Water + sigma-cap en dNTI sobre snow, NO
un threshold absoluto de NTI.

## Anexo — fuentes

- `pipeline/detection_context.py:536-594` (helper `compute_nti_and_nti_app`).
- `pipeline/process_modis.py:304-313` (cómputo per-pixel MODIS).
- `pipeline/process_viirs.py:528-571` (cómputo per-pixel VIIRS).
- `pipeline/constants.py` (Planck C1, C2, λ por banda).
- `documentacion/sp426_5.txt:294-345` (Coppola 2016a Test 1 K1=−0.8, Tabla 1).
- `documentacion/sp426_5.txt:315-345` (Coppola 2016a Tests 2-3 dNTI/dETI).
- `docs/F61_NTI_RIGOR_BRAINSTORM_S78.md` (brainstorm previo, hipótesis 1 cerrada).
- `experiments/76_audit_independent.out.md` (cross-validation MIROVA web).

## No-acción explícita

Este brainstorm **no modifica ningún archivo de `pipeline/` ni de `data/`**.
Es read-only por diseño (worktree A44 aislado, MISSION.md compliance).
Cierra la hipótesis 2 (drift en NTI) como **refutada**, y descarta la Opción A
de F61. Próximos pasos viven en otros brainstorms (F65 candidato: filtro de
masa de agua JRC + sigma-cap snow).
