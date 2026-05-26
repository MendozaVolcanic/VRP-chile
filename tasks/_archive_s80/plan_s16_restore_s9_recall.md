# S16 plan — Restaurar recall S9 en Tupungatito y Chaitén

> Ejecutar en S16 post-push S15. Sistema skill debugging aplicado.

## Pregunta pivotal

**Por qué S9 tenía recall Tupungatito 0.977 y Chaitén 0.929, y S15
post-fixes solo 0.45 y 0.80 respectivamente.** Villarrica siempre fue 0
(gap estructural distinto, no regresión).

## Arqueología — timeline de decisiones arquitecturales

| Commit | Sesión | Qué cambió | Impacto recall sospechoso |
|---|---|---|---|
| `ecb5d66` | S9 F1 | VIIRS-I dual-PATH NTI con OR. Vent-path con `bt > t_bg + 1K` fijo. | Baseline S9 = funcionaba |
| `56a1318` | S10 | **Desactivó `ENABLE_VENT_PATH_MODIS=false`** para bajar FPs 21%. | -MODIS vent Lascar |
| `2ee346e` | S11 | Path C (NTI relativo) en experimental. | Pequeño, sólo experimental |
| `09a6bfe` | S12 | configurable Path C sigma + MODIS sensor-specific vent | Medio |
| `6eaed67` | S12 F1 | **Aplica sigma-gating a vent-path, elimina 85% FPs** | **ALTO — mata TPs sub-pixel débiles** |
| `4c80429` | S12 F1b | Cap `MAX_VENT_SIGMA_CONTRIB_K=3K` sobre F1 | Medio (mitigó F1 pero sigue más estricto que S9) |
| `39e6bb0` | S12 | Pisos VRP por sensor (0.02/0.15/0.27 MW) | Bajo (-2.3% FPs) |
| `652cb25` | S12 E1+E4 | MODIS vent reactivado con threshold 2.5K + floor 0.3 MW | Revirtió parcial S10 |
| `7ded048` | S12 | Geofencing per-volcano store.py | Medio (Lastarria inner=3) |
| `5478bce` | S14 | Schema unificado, radius_km=25 uniforme | — |
| S15 | múltiples | P3.2, P3.1, bbox, sigma-cap eruption | Recupera lo anterior |

## Hipótesis ranked por evidencia

### H1 CONFIRMADA CON GROUND TRUTH — Vent-path sigma-gating (commit 6eaed67 S12 F1)

**Diff exacto del commit 6eaed67 (process_viirs.py, 2026-04-13)**:
```python
# ANTES (S9, S10, S11 — código idéntico):
if t_max_vent > (t_bg_i04 + VENT_THRESHOLD_K):   # = t_bg + 1.0 K fijo

# DESPUES (S12+ actual):
vent_thresh = max(VENT_THRESHOLD_K, N_SIGMA_VENT * std_bg_i04)
if t_max_vent > (t_bg_i04 + vent_thresh):
```

Del commit message: *"N_SIGMA_VENT (2.0) was imported but never actually used
in the vent-path detection logic. The threshold was a fixed 1K above
background"*.

En S9 la variable N_SIGMA_VENT estaba muerta. S12 F1 la "activó" usándola —
y eso eliminó 85% de los FPs PERO también eliminó TPs débiles en volcanes
con σ_bg alto (Tupungatito glaciar, Chaitén domo sub-pixel).

Commit S12 F1b (4c80429) agregó cap `MAX_VENT_SIGMA_CONTRIB_K=3` como
mitigación parcial (3K en vez de 4-6K con σ alto), pero **3K sigue siendo
3× más estricto que los 1K de S9**.

**Escenario Tupungatito glaciar σ_bg ~2K**: S9 threshold=1K. S15 threshold=min(4, 3)=3K.
Pixel fumarólico a ΔT=1.5K pasa S9, no pasa S15. → Recall perdido.

**Evidencia numérica**:
- Commit 6eaed67 message: "elimina 85% FPs" (sin contar TPs perdidos).
- Tupungatito: S9 recall 0.977 → S12 experimental 0.5 → S15 abril 0.45.
- Patrón consistente con vent-path más estricto.

### H2 — MODIS vent desactivado S10, revertido parcial S12

**Config S10**: `ENABLE_VENT_PATH_MODIS=false` → 0 vent MODIS.
**Config S15 actual**: `enable_vent_path_modis=true`, threshold 2.5K, floor 0.3 MW.

S9 no tenía esos gates específicos MODIS (usaba default 1.0K sin floor).
Impacto: Lascar MODIS recall 0.83 → 0.058 en S10, parcialmente recuperado S12.

### H3 — Pisos VRP S12

Impacto modesto confirmado por commit doc (-2.3% FPs). No es root cause.

### H4 — Geofencing per-volcano (S12)

Impacto en Lastarria (inner=3 muy restrictivo). Poco para Tupungatito (inner=7).

## Experimento propuesto S16 — probar H1 aislada

**No stackear cambios**. Un experimento por hipótesis. Skill debug: "form new hypothesis if testing fails — do not stack changes".

### E1 — Nuevo profile `s9_vent_permissive.yaml`

Clon de `mirova_equivalent.yaml` con:
```yaml
  vent_threshold_k: 1.0        # igual
  n_sigma_vent: 0.0            # EFECTIVAMENTE DESACTIVA sigma gate vent-path
  max_vent_sigma_contrib_k: 0.0 # no se usa cuando n_sigma_vent=0
```

O equivalentemente, patch en process_viirs.py: si `n_sigma_vent=0`, usar threshold fijo
(como S9).

**Reproceso**: Tupungatito + Chaitén + Lascar abril 2026. 2-3h.

**Hipótesis verificable**:
- Tupungatito recall sube de 0.45 → **>= 0.85** (cerca del S9 0.977).
- Chaitén recall sube de 0.80 → **>= 0.90** (cerca del S9 0.93).
- FPs suben (aceptamos el trade-off S9 original).

**Si se cumple**: H1 confirmada. Decisión arquitectónica: agregar un flag
`enable_vent_sigma_gating: false` por defecto en mirova_equivalent (modo S9),
mantener `true` en experimental (modo S12-conservador).

**Si no se cumple**: descartar H1, probar H2 aislada.

### E2 (solo si E1 no cierra el gap) — revertir MODIS vent

Profile clon con:
```yaml
  modis_vent_threshold_k: 1.0
  modis_vent_vrp_floor_mw: 0.0
```
Reproceso Lascar. Esperar recall MODIS volver a ~0.83 (S9).

### E3 (solo si E1+E2 juntos no cierran todo) — quitar pisos VRP

Profile clon con floors=0. Reproceso. Esperar +poco recall, +pocos FPs.

## Criterios éxito S16 cerrado

- Tupungatito recall ≥ 0.85 en abril (vs S9 0.977).
- Chaitén recall ≥ 0.90 en abril (vs S9 0.93).
- Lascar recall ≥ 0.60.
- Lastarria ratio mediano ≤ 3.
- **Precision no cae debajo de 0.30 en ningún Tier A.**
- FPs globales no suben más de 50% vs baseline S15 post-push.

Si recall sube pero precision < 0.30 → trade-off inaceptable, investigar otra
combinación (ej. n_sigma_vent=1.0 en vez de 0.0).

## Anti-patrones evitar

1. **No stackear fixes**. Cada experimento aislado.
2. **No declarar aprobado sin métricas completas**. Recall + precision + ratio.
3. **Si 3 experimentos fallan**, escalar a re-examen del diseño (skill rule).

## Orden de ejecución S16

1. Push main los fixes S15 validados (precondición — cerramos S15).
2. Leer este plan.
3. E1 primero, medir, commit si funciona.
4. E2 solo si E1 dejó gap.
5. E3 solo si E1+E2 dejaron gap.

## Referencias

- Commit culpable principal: `6eaed67` "S12 F1 sigma gating vent-path".
- Commit mitigación parcial: `4c80429` "S12 F1b cap".
- Snapshots S9 evidencia: `experiments/audit_s9/Tupungatito.json` recall 0.977.
- Agent forense Lascar S11: ya confirmó S10 56a1318 desactivó MODIS vent.
- Agent forense Tupungatito: gate BT demasiado estricto en glaciar.
