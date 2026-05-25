---
title: "S78 cierre — Mirova-v1 parity + F53 fix"
session: S78
status: closed
ai_generated: true
confidence: high
explored: true
tags:
  - cierre
  - mirova-v1-parity
  - mosaico
  - bandas
  - regiones
  - f53
related:
  - docs/SESSION_CLOSE_S77.md
  - docs/MIROVA_V1_PARITY_PROPOSAL_S77.md
  - docs/F49_SCRAPER_MIROVA_DOWN_S77.md
---

# S78 cierre — Mirova-v1 parity sprint + F53 fix

## Veredicto operacional

**Sprint "Vista panorámica Mirova-v1" completo en una sesión**. 4 PRs
adicionales mergeados sobre la base S77 (49 PRs S76+S77 → 53 PRs total).
Tests 501 passed, 24 skipped, 0 regresión.

## PRs S78 mergeados (5 total)

| PR | Sha | Contenido |
|---|---|---|
| #198 | `53df8fc6` | F54 sync workflow regenera mirova JSONs (carry-over S77) |
| #199 | `474b7152` | F55 earthaccess Store /profile bypass (carry-over S77) |
| #200 | `28b946e3` | docs(memory) A47+A48 + BLOQUE_ARRANQUE_S78 |
| #201 | `9c36f6fb` | docs(parity) Mirova-v1 proposal (subagente) |
| #202 | `6fa4f106` | **F1 mosaico panorámico** (`frontend/mosaico.html`) |
| #203 | `c1183756` | **F2 bandas MIROVA + F5 tags región N→S** |
| #204 | `347a6b5f` | **F53 fix test1_hot UnboundLocalError [A45]** |

## Lo que vas a ver al refrescar el dashboard

### 1. Selector volcán reorganizado (F5)

```
Zona Volcánica Centro (CVZ)        [Isluga, Lascar, Lastarria]
Zona Volcánica Sur Norte (SVZ-N)   [Tupungatito, PP, NdC, Copahue]
Zona Volcánica Sur (SVZ-S)         [Llaima, Villarrica, PCC]
Zona Volcánica Austral (AVZ)       [Chaitén]
```

Ordenado N→S por latitud. `<optgroup>` por zona. Operador OVDAS busca
por región rápido.

### 2. Bandas MIROVA en chart timeline (F2)

Sombreado horizontal según nivel: verde (Muy Bajo 0-1 MW) / cyan (Bajo
1-10) / amarillo (**Moderado 10-100** — donde caen Villarrica 12 /
Llaima 16) / naranja (Alto 100-1000) / rojo (Muy Alto >1000). Solo las
bandas que la data cruza (no satura visual).

Traduce VRP_MW al lenguaje del operador SERNAGEOMIN sin tabla mental.

### 3. Nueva página `mosaico.html` (F1)

Nav triple: `📊 Detallado · 📅 Diaria · 🗺️ Mosaico`.

Mosaico = grilla 11 mini-cards Chart.js sparkline 30d por volcán,
ordenadas N→S, click → drill-down `index.html?volcano=<Name>`. Es la
vista panorámica multi-volcán tipo Mirova-v1 que pediste.

## Fixes pipeline adicionales S78

- **F53** (PR #204): `test1_hot` defensive init para evitar
  UnboundLocalError. Reduce rate de granule failures esporádicos
  (~7% sanity test). NO toca semántica VRP. A45 + TDD 2/2 GREEN.

## Audit final post-S78 (ratios estables)

| Volcán | Bucket | N matched | Ratio mediano | Veredicto |
|---|---|---|---|---|
| Lascar | VIIRS375 | 81 | 0.78 | ✅ OK |
| Lastarria | VIIRS375 | 69 | 1.08 | ✅ OK |
| Llaima | VIIRS375 | 17 | 0.92 | ✅ OK |
| Isluga | VIIRS375 | 78 | 1.19 | ✅ OK |
| Copahue | VIIRS375 | 13 | 0.57 | ✅ OK |
| PCC | VIIRS375 | 76 | 0.59 | ✅ OK *(F47 recovery)* |
| Chaitén | VIIRS375 | 28 | 2.33 | ⚠️ Over moderado |
| Villarrica | VIIRS375 | 17 | 4.81 | ⚠️ Over (pre-F52-A histórico) |
| PP | VIIRS375 | 72 | 2.55 | ⚠️ Over (pre-F52-B histórico) |
| Tupungatito | VIIRS375 | 69 | 13.22 | 🔴 Over (pre-F52-B histórico) |
| NdC | (sin matches MIROVA) | — | — | sin baseline |

Cambios mínimos vs audit pre-S78 — NRT cron natural necesita 1-2 semanas
para mover medianas de 30d con records frescos post-fixes.

## Tags defensivos en origin (rollback A45)

```
pre-s73-data-cleanup
pre-s75-vrptir-a2-integration
pre-s77-f46-vrp-tir-fix
pre-s77-f47-store-cluster-rescue
pre-s77-f47-distance-class-fix
pre-s77-f50-vrp-mw-cap
pre-s77-f51-fetch-probe-bypass
pre-s77-f52a-villarrica-cluster-cap
pre-s77-f52b-single-pixel-sub-mw
pre-s77-f55-profile-bypass
pre-s78-f53-test1-hot
```

## Aprendizajes meta S78

- **Subagentes son útiles para investigación + features bite-sized**
  pero sus regex/heurísticas necesitan validarse contra convenciones
  reales (A48 documentado S77).
- **Race condition reproc local** documentado A47 — esta sesión NO
  intentó reproc paralelo, evitando el problema.
- **Bg processes mueren al cerrar Claude** (Windows session-bound).
  NRT cron en GH Actions Linux es el reemplazo natural.

## Pendientes S79+

1. **F31 A5 piloto VRPTIR** (tu máquina local, 4-8h) — script `scripts/run_pilot_a5_s76.bat`.
2. **Reproc focalizado Tup/NdC** (opcional, NRT cron natural cubre).
3. **Validación visual** del mosaico + bandas + selector regiones
   (Ctrl+F5 en browser).
4. **Backlog Mirova-v1 parity** S79+: F3, F4, F6+ del doc PR #201
   (no priorizadas en este sprint).
5. **Refactor frontend lib** opcional: extraer `mirovaEqVrp`, `getLevel`
   etc a `frontend/lib/mirova_eq.js` para evitar duplicación entre las
   3 páginas (`index.html`, `diario.html`, `mosaico.html`).

## Métricas S78

- **5 PRs mergeados** (#200-#204 — propios S78; #198-#199 son carry-over S77).
- **3 features Mirova-v1 parity** (F1 mosaico, F2 bandas, F5 regiones).
- **1 fix pipeline crítico** (F53 test1_hot con A45).
- **501 tests passing** (+2 nuevos F53), 24 skipped, 0 regresión.
- **Total acumulado S76+S77+S78**: 53 PRs.
