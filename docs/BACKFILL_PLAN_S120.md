# Plan backfill histórico Tier A — S120

**Objetivo**: extender la serie operacional `mirova_equivalent` hacia atrás
(hoy empieza ~nov-2025) para que el dashboard tenga historia comparable con MIROVA
(años). Momento correcto (bloque S120 §Eje 7): con los gates OFF (S118) + nadir-fijo
(S102-S103) + magnitud focal (S109-S112), **la data backfilled nace ya clon-literal** —
no habrá que reprocesarla cuando cambie la config, porque la config ya convergió.

## Por qué es seguro escribir al operacional

- Los records históricos se agregan por **merge aditivo** (`store.py`, sin
  `--overwrite`): las fechas pre-nov-2025 no colisionan con la serie viva.
- Cada job del workflow escribe **solo el archivo de su volcán** (anti-race A47/S25,
  patrón nrt.yml probado 12×/día).
- Reversible: `git revert` del commit de datos del volcán afectado.

## Fases (gates de verificación entre olas — NO lanzar todo junto)

| Fase | Qué | Ventana | Gate para pasar a la siguiente |
|---|---|---|---|
| **P0 piloto** | 1 volcán (Lascar) | 2025-09-01 → 2025-09-30 | integridad (parse, dupes, orden temporal) + espot-check vs OSF v2.5 (el CSV MIROVA scrapeado NO cubre 2025 — el ground truth histórico es OSF) |
| **P1 ola 1** | 11 Tier A | 2025-08-15 → 2025-11-15 | auto-audit integridad + tamaños JSON razonables + dashboard carga |
| **P2 ola 2** | 11 Tier A | 2025-05-15 → 2025-08-15 | ídem |
| **P3 ola 3** | 11 Tier A | 2025-02-15 → 2025-05-15 | ídem |
| **P4 ola 4** | 11 Tier A | 2025-01-01 → 2025-02-15 | ídem + verdict global |
| P5+ (opcional) | 2024 hacia atrás | por trimestres | decisión Nicolás (costo compute vs valor; OSF cubre hasta 2025 para validar) |

**Cómo se lanza cada ola**: workflow `backfill-tier-a.yml` (Actions → Run workflow)
con inputs `start`/`end` (≤ ~3 meses, A15: 90 días ≈ 175 min/vol) y `volcano`
(`all` u volcán exacto para piloto).

## Verificación por ola (mínimo)

1. `python scripts/auto_audit_weekly.py` NO aplica (ventana rodante 60d) — usar
   `experiments/_s119_audit/eje4_integridad.py` (parse/dupes/coherencia sobre los 45).
2. Conteo de records nuevos por volcán y sensor (`git log --stat` del commit del job).
3. Spot-check magnitud vs **OSF v2.5** (`data/mirova_reference/`, 48k filas chilenas
   2000-2025): 3-5 noches ALERTA del período por volcán activo, ratio en banda [0.5-2.0].
4. Dashboard: la serie histórica renderiza sin romper `diario.html` (rangos de fecha).

## Consideraciones técnicas

- **Standard L1B** (LAADS) para fechas 2025: sin fallback NRT/LANCE → descargas más
  estables que el NRT (A64 no aplica a fechas viejas).
- VIIRS375 + VIIRS750 + MODIS (los 3; MODIS corre en Actions Linux).
- NOAA-21: verificar disponibilidad VJ2 para fechas tempranas 2025 (v2 vs v2.1).
- Si un job muere por timeout: re-dispatch de la misma ola con `volcano=<el que faltó>`
  (el merge es idempotente por granule).

## Estado

- [x] Workflow `backfill-tier-a.yml` creado (S120; fix matrix dinámico PR #481).
- [x] **P0 piloto Lascar sep-2025: GATE APROBADO** (run 28567857281, 2026-07-02).
  Números: 279 records nuevos (8 sensores completos), 0 duplicados, 153 noches
  summit vrp>0 (mediana 0.845 / máx 4.26 MW). **Cruce vs OSF v2.5: 25/26 noches
  detectadas (96%), ratio mediano nuestro/OSF 0.761× (n=25, en banda [0.5-2.0]),**
  consistente con la serie viva (Láscar 0.70×). Parseo OSF: nombre con tilde
  "Láscar", fecha DD/MM/YYYY, VRP en watts (÷1e6).
- [x] P1 ola 1 (11 Tier A, 2025-08-15 → 2025-11-15) despachada 2026-07-02.
- [ ] P1 verificación → P2 (2025-05-15 → 2025-08-15) → P3 → P4.
