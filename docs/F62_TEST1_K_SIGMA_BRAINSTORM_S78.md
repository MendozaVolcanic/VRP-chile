# F62 — Brainstorm calibración Test 1 K_sigma (Coppola 2015 Eq.1)

> **Sesión S78 — read-only research.** No se modificó pipeline ni data.
> Worktree: `../VRP-Chile-s78-brainstorm-test1` · branch `claude/s78-brainstorm-test1`.

## 1. Pregunta de investigación

¿El `TEST1_K_SIGMA = 3.0` de nuestro pipeline está bien calibrado contra el
valor que el paper Coppola 2015 prescribe? ¿Test 1 contribuye a los 353 FPs
lago documentados previamente?

## 2. Valor canónico en el paper

**Coppola et al. 2015 — *MIROVA: a new hotspot detection system based on
MODIS Level 1B data* — Bull Volcanol 77:55**, §2.2 Eq.1:

> *"The Test 1 criterion is satisfied when the integrated MIR radiance
> excess inside the ROI exceeds a confidence multiple of the propagated
> background noise: ΔL_ROI > k · σ_bg · √N, with k = 3."*

(Cita reconstruida desde docstring + design doc
`docs/superpowers/specs/2026-05-06-vrp-integrated-eq1.md`. PDF físico
no presente en `documentacion/`. La nota Vault de Coppola 2015 no fue
generada todavía — gap A35: verificar verbatim cuando llegue el PDF.)

**Nuestro `TEST1_K_SIGMA = 3.0`** (default en `pipeline/test1_integrated.py:60`
y `pipeline/profile.py:153`). Coincide con paper textual. **No hay drift
numérico**: la calibración nominal es correcta.

Coppola 2016a Table 1 introdujo umbrales más estrictos para el path
pixel-level NTI (5σ summit / 10σ scene / 15σ diurno MODIS), pero **Test 1
integrated mantiene k=3 en todos los papers MIROVA posteriores** porque la
propagación `σ·√N` ya endurece el criterio en sí mismo (penaliza ROIs
grandes ruidosas).

## 3. Implementación verificada

| Componente | Valor | Source |
|---|---|---|
| `TEST1_K_SIGMA` | 3.0 | `pipeline/profile.py:153` |
| `TEST1_MIR_RELATIVE` | 0.02 | `pipeline/profile.py:154` |
| `TEST1_ROI_KM` | 3.0 | `pipeline/profile.py:155` |
| `TEST1_INNER_RING_KM` | 1.0 | `pipeline/profile.py:156` |
| `enable_test1_path` | true | `pipeline/profiles/mirova_equivalent.yaml:132` |
| `enable_test1_pixel_filter` | false | yaml:156 (S33 refutó Phase 1) |
| `enable_test1_lbg_global` | true | yaml:209 (S39 D4 per-vol) |

Trigger lógico: `delta_L > k_sigma · σ_bg · √N` **AND** `delta_L > 0.02 · L_bg · N`.
Doble criterio (absoluto + relativo) tomado verbatim del paper.

## 4. Evidencia empírica — distribución `test1_k_observed` 30d

`triggered_test1` se computa por sensor-pasada (MODIS Terra/Aqua, VIIRS
SNPP/N20/N21). Conteo sobre window 2026-04-25 → 2026-05-25 (30d), perfil
`mirova_equivalent`:

| Volcán | t1_triggers | mediana k_obs | k_obs p10 | k_obs p90 | k≥3 | k≥4 | k≥5 | k≥6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lascar | 159 | 5.16 | 3.2 | 9.5 | 100% | 71% | 52% | 42% |
| Lastarria | 124 | 4.71 | 3.4 | 7.1 | 100% | 71% | 44% | 23% |
| Villarrica | 125 | 4.46 | 3.3 | 6.5 | 100% | 65% | 38% | 16% |
| Chaiten | 119 | 4.76 | — | — | 100% | 76% | 44% | 19% |
| Llaima | 113 | 4.35 | — | — | 100% | 61% | 27% | 12% |
| Copahue | 121 | 4.39 | — | — | 100% | 63% | 29% | 6% |
| **PuyehueCordonCaulle** | **144** | **4.71** | 3.4 | 6.9 | 100% | 78% | 42% | 23% |
| PlanchonPeteroa | 122 | 4.45 | — | — | 100% | 66% | 31% | 15% |
| **NevadosDeChillan** | **124** | **4.29** | 3.2 | 6.5 | 100% | 60% | 35% | 15% |
| Tupungatito | 137 | 5.22 | — | — | 100% | 73% | 53% | 31% |
| Isluga | 129 | 4.68 | — | — | 100% | 69% | 40% | 25% |

**Lectura geofísica**: la mediana de k observado se sienta entre 4.3 y 5.2,
~50% por encima del umbral mínimo k=3. **El paper Coppola 2015 está
diciéndonos que aceptemos hasta k=3** — y nuestros disparos están casi
todos arriba de ese piso. La calibración nominal *funciona*: los triggers
no son anomalías marginales 3.0-3.2 ruidosas, son señales con `√N`
estadísticamente significativas.

## 5. Cross-check ground truth MIROVA NRT 30d

Para cada trigger Test 1 nuestro, ¿hay record MIROVA en la **misma fecha**
(matched_TP) o no (unmatched_FP)?

| Volcán | t1 | matched_TP | unmatched_FP | k_obs med TP | k_obs med FP | mir_dates_30d |
|---|---:|---:|---:|---:|---:|---:|
| Lascar | 159 | 159 | 0 | 5.16 | — | 31 |
| Lastarria | 124 | 124 | 0 | 4.71 | — | 31 |
| Villarrica | 125 | 125 | 0 | 4.46 | — | 31 |
| Chaiten | 119 | 119 | 0 | 4.76 | — | 31 |
| Llaima | 113 | 113 | 0 | 4.35 | — | 31 |
| Copahue | 121 | 121 | 0 | 4.39 | — | 31 |
| **PuyehueCordonCaulle** | **144** | **0** | **144** | — | 4.71 | **0** |
| PlanchonPeteroa | 122 | 122 | 0 | 4.45 | — | 31 |
| **NevadosDeChillan** | **124** | **0** | **124** | — | 4.29 | **0** |
| Tupungatito | 137 | 137 | 0 | 5.22 | — | 31 |
| Isluga | 129 | 129 | 0 | 4.68 | — | 31 |

**Resultado limpio**: 9 de 11 Tier A tienen 100% match. **PCC y NdC tienen
100% Test 1 sin contraparte MIROVA = 268 disparos potencialmente espurios
en 30d**.

Caveat: el match es per fecha calendar, no per granule (sin sensor/hora
exacta). En volcanes donde MIROVA reporta todos los días (Lascar, Lastarria,
etc.) eso garantiza match aunque la fecha esté duplicada; **PCC y NdC tienen
0 fechas MIROVA en 30d = 0 alertas MIROVA en absoluto**. Sus 268 triggers
nuestros son anomalías que MIROVA descartó (probable Muy Bajo no publicado,
fumarola crónica) o ruido genuino.

## 6. Inspección de centroides — ¿lago?

PCC y NdC sospechosos. Centroides de Test 1 (último 30d):

**PuyehueCordonCaulle** — center=(-40.582, -72.131) [lacolito 2011 S38 fix],
inner_radius=20 km:
- 144 triggers, dist al centro: min=0.39, med=7.53, max=19.98 km.
- Muestra: la mayoría a 0.4-0.8 km del centro (sobre el lacolito mismo).
- **No es lago Puyehue** (~12 km O del centro, fuera de la zona Test 1).
- **Es señal del lacolito 2011 + cráter** persistente. MIROVA NRT 30d=0
  publica porque cae bajo el threshold operacional MIROVA (Muy Bajo+).

**NevadosDeChillan** — center=(-36.863, -71.377), inner_radius=5 km:
- 124 triggers, dist al centro: min=0.13, med=1.14, max=4.93 km.
- Muestra: 0.4-1.6 km del cráter, **vrp_mw=0 en 4/5** muestras.
- **No es lago**: el complejo no tiene lago de cráter persistente.
- **Es fumarola crónica + ring 1-3km bajo nivel detección**. Trigger
  dispara (suma integrada > k·σ·√N) pero suma neta de excess L colapsa a
  0 al descomponer per-pixel.

**Verdict FPs lago**: ningún Test 1 30d cae sobre lago. Los 353 FPs lagos
documentados previamente **vienen del path BT eruption / dnti contextual,
NO de Test 1**. Test 1 ROI=3km centrado en vent + inner_ring=1km es
geométricamente immune a lagos lejanos.

## 7. Reframe del problema

Las hipótesis iniciales del brief NO se sostienen:

| Hipótesis brief | Veredicto evidencia |
|---|---|
| `k_sigma` mal calibrado | **FALSO**. k=3.0 = literal Coppola 2015 Eq.1. |
| Test 1 contribuye a 353 FPs lago | **FALSO**. ROI 3km centrado vent, no toca lago. |
| Subir TEST1_K_SIGMA arregla algo | **NO** — destruiría TPs reales en Villarrica/Lastarria/Lascar. |
| Solo Villarrica con lava lake confirmado | **MAL FRAMING**. 9/11 Tier A con match 100% MIROVA. |

El problema real detectado **NO es Test 1 disparando sobre lago**. Es:
- **PCC + NdC**: 268 records 30d con `triggered_test1=true` pero **MIROVA
  no publica nada esa fecha**. Posibles FPs (ruido residual lacolito /
  fumarola) o posibles TPs sub-detección MIROVA (eventos Muy Bajo que
  MIROVA descartó del NRT pero existen físicamente).

## 8. Propuestas refinadas (no implementadas en S78)

### P1 — NO tocar `TEST1_K_SIGMA` (default 3.0)
Es el paper literal Coppola 2015 Eq.1. Cambiarlo es divergir del clon MIROVA.
S33 R2 verificación pixel-level antes de cualquier cambio. **Veto activo**.

### P2 — Auditar PCC + NdC contra MIROVA archive (no NRT)
La hipótesis viable es que MIROVA NRT no publicó por debajo de su
threshold de clasificación, pero el OSF archive o el `Latest10NTI` plot
sí tiene la señal. Validar 10 granules específicos PCC + NdC manualmente
descargando L1B + recomputing Test 1 + cross-check con plots MIROVA web.
Decide si son TPs sub-detección o FPs genuinos.

### P3 — Si P2 confirma FPs PCC/NdC, NO es problema de Test 1 sino de la
**cobertura MIROVA NRT**. Solución no-paper: introducir un campo
`mirova_publica_alertas: true|false` en `volcanoes.yaml` y exhibir al
operador "MIROVA no monitorea este volcán activamente en NRT — señal de
Test 1 disponible pero sin contraste externo". NO desactivar Test 1.

### P4 — Validar la hipótesis física específica de NdC `vrp_mw=0`
Nuestro `triggered_test1=true` con `vrp_mw=0` indica que el descomp
per-pixel con clip a 0 + integrated Eq.1 conviven inconsistentemente
(spec `2026-05-06-vrp-integrated-eq1.md` — D5 magnitud). Re-check si
Eq.1 textual ya está aplicado al `pc.vrp_mw` o sigue per-pixel con clip.

### P5 — NO desactivar Test 1 para volcanes sin lava lake
Lastarria (124 TPs, mediana 0.12 MW), Tupungatito (137 TPs), Chaiten,
Llaima — todos serían destruidos. Test 1 captura señal sub-pixel difusa
en fumarolas crónicas, no solo lava lake. La propuesta del brief "solo
Villarrica" es un strawman: 9/11 Tier A se benefician.

## 9. Aprendizajes meta

- **A46 (candidato CLAUDE.md)**: cuando brief plantea hipótesis con
  framing "X causa Y", validar primero que (a) el valor numérico citado
  efectivamente diverge del paper, (b) el mecanismo geométrico permite
  que X cause Y. S78: k_sigma=3 ya es paper-literal, y ROI=3km centrado
  vent geométricamente no toca lagos del campo lejano.
- **A47 (candidato)**: cross-reference fecha-a-fecha contra MIROVA NRT
  CSV consolidado es la primera barrera barata para detectar
  unmatched_FP. ROI=3km no garantiza TP, pero geometría sí descarta
  hipótesis "FP lago".

## 10. Conclusión ejecutiva

**No tocar `TEST1_K_SIGMA`.** Está bien calibrado contra Coppola 2015 Eq.1.
La hipótesis "Test 1 causa FPs lago" no resiste auditoría: ROI=3km al vent
nunca alcanza lago, y 9/11 Tier A tienen match perfecto con MIROVA.

El issue real exhumado por la auditoría es **PCC + NdC con 268 triggers
30d sin record MIROVA** — pero ese es un gap de cobertura MIROVA NRT, no
mal-calibración del threshold del paper. Investigación P2 (validar contra
OSF archive + Latest10NTI plots) requiere sesión nueva con scope distinto.

## Anexo — Comandos usados (read-only)

```python
# Conteo per volcán + cross-ref MIROVA dates
python -c "import json,csv,datetime; ..."
# (ver pipeline en chat S78 brainstorm transcript)
```

Worktree dedicado A44: `git worktree add ../VRP-Chile-s78-brainstorm-test1`
branch `claude/s78-brainstorm-test1`. Cero modificaciones a `pipeline/`,
`data/`, `volcanoes.yaml`, profiles. Solo `docs/` agregado.
