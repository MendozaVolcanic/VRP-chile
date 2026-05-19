# BLOQUE DE ARRANQUE S63 — VRP Chile

> Pre-escrito S62 (workflows corriendo). Finalizar valores `<X>`, `<Y>`
> post-audit Task 6 (S62 cierre).

---

## 1. Lectura obligatoria al inicio S63

1. **Este doc** (`tasks/BLOQUE_ARRANQUE_S63.md`) — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S62.md`** — contexto S62 (PCC + Lastarria/Tup)
3. **`tasks/BLOQUE_ARRANQUE_S61.md`** — contexto S61 (Villarrica/PP adopción)
4. **`experiments/110_s62_results.md`** — resultado A/B Lastarria/Tup + PCC reproc
5. **`experiments/111_s62_chaiten_pattern_confirms.md`** — patrón Chaiten Muy Bajo
6. **`docs/HYPOTHESIS_LOG.md`** entries S61+S62

---

## 2. Estado al cierre S62

### Adopciones operacionales acumuladas

| Vol | `local_kernel_bg` | `inner_radius_km` | Status calibración |
|---|---|---:|---|
| Villarrica | true (S61) | 5 | ✅ 2.16× |
| PlanchonPeteroa | true (S61) | 5 | ✅ 2.84× |
| **Lastarria** | **<true/false>** (S62) | 3 | **<X>×** post-S62 |
| **Tupungatito** | **<true/false>** (S62) | 7 | **<X>×** post-S62 |
| **PCC** | false | **7** (S62 nuevo) | **<X>×** post-reproc |
| Lascar | false | 5 | ✅ 1.32× (no fix needed) |
| Isluga | false | 5 | ✅ 1.11× |
| Copahue | false | 4 | calibrado (n=1) |
| Llaima | false | 5 | (n=3, poco data) |
| NdC | false | 5 | sin data |
| **Chaiten** | **false** (S63 candidato) | 5 | **LEGACY 10.28×** |

### Métricas S62 (post-workflows)

- Lastarria: LEGACY 7.67× → NEW <Y>× (decisión adopción <SÍ/NO>)
- Tupungatito: LEGACY 8.20× → NEW <Y>× (decisión adopción <SÍ/NO>)
- PCC: LEGACY 3.51× → post-inner=7 <Y>× (decisión revertir/mantener)

### Tests + git
- 335 passed / 16 skipped
- PRs S62 mergeados: #79 (PCC+workflows+plan), #80 (status), <cierre PR S62>

---

## 3. Pendientes priorizados S63

### Prioridad ALTA

1. **A/B Chaiten kernel-bg** — patrón térmico Muy Bajo confirmado (ΔT 10.5K).
   Top outlier 115× (2026-04-07). Replicar workflow S62 Lastarria+Tup pero
   solo Chaiten (~3h GH Actions).
   - Crear `.github/workflows/reproc-ab-chaiten.yml` (clon de A/B Lastarria+Tup)
   - Disparar window 2026-03-01 → 2026-05-19
   - Audit con `experiments/110_*` script adaptado
   - Si valida (recall mantenido, ratio < LEGACY 10.28×): adopción
     `local_kernel_bg: true` en `volcanoes.yaml`.

2. **Verificación post-deploy S62** (cron NRT cycles)
   - Verificar Lastarria/Tupungatito/PCC procesan OK con nuevos flags
   - Monitor magnitudes coherentes en dashboard

### Prioridad MEDIA

3. **Revisar Llaima/Copahue con `pc.vrp_mw`** (S62 finding paralelo):
   - Llaima 3 ALERTAS (1 CONS + 2 OCR) ratios 6.12-11.82× con pc.vrp_mw
     (S60 dijo 1.01× con record.vrp_mw — campo incorrecto ocultó problema)
   - Copahue 1 ALERTA ratio 3.18× con pc.vrp_mw (S60 dijo 1.14×)
   - Régimen Muy Bajo (VRP MIROVA 0.08-0.29 MW)
   - Si más ALERTAS aparecen 2026-05/06: considerar A/B kernel-bg
   - NO modificar S63 sin más data (n=1-3 no representativo)

4. **NdC (Nevados de Chillán)** sigue sin data MIROVA — esperar más actividad
   térmica futura para auditar.

5. **Coord MIROVA validación TIF/KMZ** para vols sin `mirova_center`
   definido — investigar si vent_lat/lon coinciden con donde MIROVA centra
   clusters reportados.

### Predicción S63 Chaiten post-fix

Extrapolación basada en S61 fixes Villarrica/PP:
- Villarrica: LEGACY 15× → NEW 2.17× (-86%)
- PP: LEGACY 11.80× → NEW 2.84× (-76%)
- Chaiten esperado: LEGACY 10.28× → NEW **1.5-2.5×** (extrapolación lineal)

Si valida (recall mantenido, ratio <3×): adopción `local_kernel_bg: true`
Chaiten en `volcanoes.yaml`.

### Prioridad BAJA (refinamientos S64+)

5. **`kernel_size=5` analysis** — DESCARTADO de prioridad S63. Análisis offline
   indica que el lago Villarrica está a 15-18 km del cráter, kernel 5×5
   (~1.9 km en VIIRS-I) NO lo capta. El fix kernel=3 ya cumple su función.
   Solo investigar si gap Villarrica residual 42% sobre OSF target se
   vuelve crítico operacionalmente.

6. **Test 1 path threshold tuning** (`k_sigma`, `mir_relative`) — Coppola 2016a
   Tabla 1 sugiere 5σ summit / 10σ scene (vs nuestro 3σ uniforme). Pero
   afectaría vols ya calibrados (Lascar/Isluga). NO investigar sin test
   sintético controlado.

7. **Refinamiento per-vol thresholds** — algunos vols pueden necesitar
   `nti_k1_night` distinto. Solo si gap residual identificable.

---

## 4. Errores S62 a NO repetir S63

0. **NO investigar kernel_size=5 sin justificación clara**. Análisis offline
   S62 mostró que NO ayuda Villarrica (lago lejos del kernel).

1. **NO disparar A/B kernel-bg para vols sin patrón térmico Muy Bajo**
   (Lascar/Isluga calibrados, NO tocar).

2. **NO modificar `volcanoes.yaml` per-vol flags por intuición** — siempre
   audit empírico con `pc.vrp_mw` + universo CONS+OCR primero.

3. **Verificar timeout workflow antes de disparar** (S60 lesson).

4. **Usar `pc.vrp_mw`** para comparar con MIROVA (S61 lesson).

5. **Pre-escribir audit scripts en paralelo** mientras corren workflows
   (S61/S62 patrón validado — eficiente).

---

## 5. Estado git S62

- Último PR cierre S62: <PR#>
- Workflows S62: ambos completed (runs 26072884472 + 26072886354)
- Main al día con todas las adopciones S61+S62

---

## 6. Quick reference comandos S63

```bash
# Check workflow status
gh run list -R MendozaVolcanic/VRP-chile --limit 5 --json status,name,createdAt

# Crear workflow A/B Chaiten (clon de Lastarria+Tup)
cp .github/workflows/reproc-ab-lastarria-tupungatito.yml \
   .github/workflows/reproc-ab-chaiten.yml
# Edit: matrix volcano: [Chaiten], commit, merge

# Disparar
gh workflow run reproc-ab-chaiten.yml -f start=2026-03-01 -f end=2026-05-19 \
   -R MendozaVolcanic/VRP-chile

# Audit reusable
python experiments/110_s62_audit_pcc_lastarria_tupungatito.py
# Adaptar para Chaiten o crear 112_s63_audit_chaiten.py
```

---

## 7. Persistencia in-vivo (regla meta-meta)

Cuando descubras hallazgo durante S63: persistir INMEDIATAMENTE en
`docs/HYPOTHESIS_LOG.md` o `experiments/` ANTES de continuar. La sesión
puede cortarse abruptamente.

Hallazgo S62 a persistir cuando se confirme post-audit:
- Si Lastarria/Tupungatito kernel-bg valida → `H_S62_LASTARRIA_TUPUNGATITO_ADOPTED`
- Si PCC inner=7 valida → `H_S62_PCC_INNER7_ADOPTED`
- Si Chaiten patrón confirmado → `H_S63_CHAITEN_KERNEL_BG_NEEDED`
