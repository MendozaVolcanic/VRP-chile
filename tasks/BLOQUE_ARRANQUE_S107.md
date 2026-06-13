# BLOQUE ARRANQUE S107

**Sesión S106 (2026-06-11/13)** — MUY larga. Cerró el frente del **ancla espacial honesta**
(adoptada VIIRS375) + auditoría integral ultracode (30 agentes). Registro completo:
`project_s106_estado` (memoria) + `docs/AUDIT_S106.md` (19 hallazgos confirmados) +
`docs/MIROVA_DIVERGENCES.md` (D11, D11-bis, D12 nuevas).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S106.md            # marco actual (plan P0-P3 + puntos ciegos)
# estado del A/B V750 (estaba en cola al cerrar S106):
gh run view 27468739388 --json status,jobs
```

## ✅ Cerrado en S106
- **⭐ Ancla espacial honesta ADOPTADA VIIRS375** (PRs #397-#402, #406): la posición del
  record viene del cluster contextual / vent (test1_roi), no del centroide Test1 con sesgo
  topográfico (D11/A69). 11 vols promovidos (6 al 100%, 5 al 64-86% por reproc truncado).
  A/B run 27343409067: 0-diffs trig_t1 pareados → no toca detección ni magnitud. Espejos
  MODIS/V750 implementados flag-OFF. Frontend (mapa+tabla+click) usa el ancla (#403, #405, #409).
- **Fondo-local-NTI REFUTADO** (todo el barrido) — D11 sin candidato activo, costo = posición.
- **AUDIT_S106 integral** (PR #408): clon SANO, P0=ninguno, suite 705. Fixes seguros
  aplicados #409 (frontend coherencia) + #410 (gate reproc + tripwires) + #411 (consolidación).

## §1 — PRIORIDAD S107: el peor FN real (P1.1 + P1.2, AUDIT_S106 D12)
**MODIS Láscar pierde ~70/79 alertas que MIROVA SÍ publica.** El `primary_cluster` está en
el cráter (1.46 km ≈ MIROVA 1.41) pero el píxel suelto cae en el **Salar de Atacama**
(16-32 km) → `distance_class='far'` → `mirovaEqVrp`/`audit_metrics.py:79` lo anula. Es el
**espejo MODIS del bug que el ancla curó en VIIRS375**. Fix: reproc histórico F2 Láscar MODIS
(pipeline actual nadir-fijo) → distance_class desde el cluster. A45 (tag + TDD + OK Nicolás).
Verificar antes/después con `per_sensor_metrics.py`. Corrige el "0 pérdida" fabricado de S95.

## §2 — Frente magnitud MODIS (P2.1, design YA hecho 2026-06-13)
Fondo LOCAL adyacente al cluster (Coppola 2016a Eq.6) para los 134 inflados warm-scene.
GATEA el espejo MODIS del ancla (destape de 134 far→summit). **OJO A48**: el helper
`compute_local_background` (vrp_regimes.py) es kernel per-pixel, NO corona del cluster — el
fix debe promediar la corona del cluster contiguo. A45 (magnitud). Diseño + predicciones
pre-registradas en `docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md`.

## §3 — En vuelo / pendientes operacionales
- **A/B V750** (run 27468739388): estaba en cola al cerrar. Al aterrizar → audit pareado
  (`audit_honest_anchor.py`) → flip `enable_honest_anchor_viirs750` + promoción V750.
  Destape pre-verificado limpio (0 records pc.vrp>5). Profile + workflow ya existen.
- **Reproc dirigido Isluga+PP** (P1.3): su legacy posicional cae en noches ALERTA. Correr
  DESPUÉS de cerrar el gate (ya existe `experiments/reproc_coverage_gate.py` — usarlo
  pre-promoción). Etapa 2: Chaitén/NdC/Copahue (coherencia visual, no noches críticas).

## §4 — Otros hallazgos AUDIT_S106 (orden sugerido)
- P1.6 `fetch.py`: circuit-breaker A64 NO cubre búsqueda CMR (fallo NRT 06-12). Extender a
  `search_data` + marker `NASA_CMR_UNREACHABLE` + `nrt-retry.yml`.
- P2.7 (A61): el cruce recall/precision es SOLO temporal, nunca espacial → sobre-estima.
  Agregar gate espacial a `per_sensor_metrics.py`.
- P2.11 gates intra-radio S84/S85 (decisión Nicolás pendiente, A55).
- P2.13 `audit_paired_trigt1.py` versionado (la evidencia 0-diffs es ad-hoc, viola S91).
- P3.x housekeeping (97 branches, 54 tags, Planck C2 triplicada) — sesión dedicada + OK A38.

## §5 — Puntos ciegos (lo más valioso del informe, AUDIT_S106 §4)
1. La fidelidad de MAGNITUD quedó atrás de la POSICIÓN (fondo regional-vs-local sin
   resolver en paths MIR-absolutos — el mismo principio A69, en otro eje).
2. "conclusion=success" ≠ datos completos (riesgo sistémico de reproc, ya hay gate P2.6).
3. El recall reportado nunca verificó el eje espacial (A61, regla vinculante).
4. Las redes de seguridad tapan los fallos viejos, no los nuevos (A64 cubre auth/download,
   no CMR; nrt-retry solo reacciona a auth).

## Estado caps/reglas
- **PRs S106 ~19** (cap hard M1=20) → S107 puede abrir libremente de nuevo.
- A45 estricto para todo lo de §1/§2/§4-P1.6 (tocan pipeline).
- A47: reproc local NUNCA paralelo sobre mismo data_subdir.

## Prompt copy-paste S107
```
Sesión S107 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S107.md + project_s106_estado (memoria) + docs/AUDIT_S106.md.
S106 adoptó el ancla espacial honesta (VIIRS375, cura el sesgo topográfico D11) + corrió
una auditoría integral ultracode (30 agentes, 19 hallazgos, clon SANO P0=ninguno) y aplicó
los fixes seguros (frontend coherencia #409, gate reproc + tripwires #410, consolidación
docs #411). PRIORIDAD §1: el peor FN real — MODIS Láscar pierde ~70/79 alertas MIROVA por
distance_class del píxel Salar (D12); fix = reproc F2 Láscar MODIS (A45, espejo del ancla).
§2: magnitud MODIS fondo-local Eq.6 (design hecho 2026-06-13; OJO compute_local_background
es per-pixel no corona del cluster, A48). §3: aterrizar A/B V750 (run 27468739388) → flip +
promoción; reproc dirigido Isluga+PP con el gate experiments/reproc_coverage_gate.py.
RECORDÁ: A45 (tag+TDD+OK Nicolás para pipeline), A47, A48, A61 (recall espacial pendiente),
A66, explicame como geólogo. 🔐 .netrc local Earthdata inválido (usar Actions).
```
