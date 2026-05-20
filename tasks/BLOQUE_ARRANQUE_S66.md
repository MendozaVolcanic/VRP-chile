# BLOQUE DE ARRANQUE S66 — VRP Chile

> Cierre S65: Tupungatito fix mirova_center aplicado (PR #93), workflow
> reproc operacional disparado (run 26143572382), audit script ready
> (experiments/115_*.py). Pendiente validar resultado cuando termine ~3h.

---

## 1. Lectura obligatoria

1. **Este doc** — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S65.md`** — contexto S64 → S65
3. **`docs/HYPOTHESIS_LOG.md`** entries H_S62-H_S65 (top 5)
4. **`experiments/115_s65_audit_tupungatito_post_fix.py`** — audit script ready
5. **`pipeline/profiles/mirova_equivalent.yaml`** — flags actuales
6. **`volcanoes.yaml`** — Tupungatito ya SIN mirova_center

---

## 2. Estado al cierre S65

### Adopciones acumuladas (5 vols Tier A + Tupungatito pendiente)

| Vol | `local_kernel_bg` | `inner_radius_km` | Ratio | Adoptado |
|---|---|---:|---:|---|
| **Villarrica** | true | 5 | 2.17× | S61 |
| **PlanchonPeteroa** | true | 5 | 2.84× | S61 |
| **Lastarria** | true | 3 | 1.07× | S62 |
| **Chaiten** | true | 5 | 2.23× | S63 |
| **PCC** | true | 20 | 0.29× | S63 |
| Lascar | false | 5 | 1.37× | calibrado natural |
| Isluga | false | 5 | 1.33× | calibrado natural |
| **Tupungatito** | false | 7 | 10.37× → ? | **S65 fix mirova_center**, reproc 26143572382 |
| Copahue | false | 4 | (n=1) | poca data |
| Llaima | false | 5 | (n=3) | poca data |
| NdC | false | 5 | (n=0) | sin data |

### Cambio S65 PR #93
- Quitar `mirova_center_lat/lon` Tupungatito de `volcanoes.yaml`
- vent_anchored ahora ancla en vent_lat (cráter activo correcto)
- Workflow `reproc-tupungatito-operacional.yml` creado (PR #94)
- Workflow disparado: run 26143572382, ETA ~2-3h post-trigger 13:00 UTC aprox

---

## 3. Pendientes priorizados S66

### Prioridad ALTA — primer paso S66

1. **Audit Tupungatito post-reproc** (run 26143572382)
   - `git pull --rebase origin main` para traer JSON actualizado
   - `python experiments/115_s65_audit_tupungatito_post_fix.py`
   - **Si valida** (recall ≥70, ratio mediano <3×):
     - Mantener fix mergeado
     - Documentar éxito en HYPOTHESIS_LOG
     - 8/9 vols Tier A calibrados (~89%)
   - **Si NO valida**:
     - Revertir agregando `mirova_center_lat/lon` back a `volcanoes.yaml`
     - Considerar opciones C (inner_radius_km 7→3) o D (combinar)
     - Investigar S66+ por qué falló

### Prioridad MEDIA

2. **MODIS final_hotspot fix** (S62 paralelo identificó):
   - `final_hotspot_lat/lon/dist_km` se asigna al pixel más caliente individual
   - Para MODIS Villarrica: 21/21 records `distance_class=far` aunque cluster cerca cráter
   - Fix: asignar `final_hotspot` al pixel más caliente DEL CLUSTER SUMMIT
   - Implementación: `pipeline/process_modis.py` función que asigna final_hotspot
   - Requiere TDD: test sintético + A/B + reproc
   - Plan completo en bloque S65/S64

3. **Llaima/Copahue con `pc.vrp_mw`** (S62 paralelo finding):
   - Llaima n=3 ratio 6-12× con pc.vrp_mw
   - Copahue n=1 ratio 3.18× con pc.vrp_mw
   - Si llegan más ALERTAS 2026-05/06: considerar A/B kernel-bg
   - Actualmente NO accionable sin más data

### Prioridad BAJA

4. **NRT cron failures intermittentes** (SanJose/Antillanca timeout NASA)
5. **NdC sin data**: esperar actividad
6. **Refinamientos kernel_size=5 / p25**: descartados S62 (lago Villarrica fuera de kernel)

---

## 4. Errores S64-S65 a NO repetir S66

0. **NO asumir bin top centroides = anomalía real**: S62-S64 confundió bin FP (-33.43, -69.79) Tupungatito con actividad.
1. **PNGs MIROVA son dashboards de timeline**, NO mapas con coord del hotspot. Solo PNG Distance es útil.
2. **mirova_center con bbox center KMZ por default es peligroso** (caso Tupungatito S16 con offset 2.99km incorrecto). Validar empíricamente.
3. **Confirmar coord activa con Nicolás** antes de mover (geólogo).
4. **Preview offline cluster selection es engañoso** (S62 PCC inner=7 — Lección A18).
5. **`record.vrp_mw` vs `pc.vrp_mw`** — siempre usar `pc.vrp_mw` para comparar con MIROVA (Lección A10).
6. **CSV vol names variantes** (PlanchonPeteroa sin guión, etc.) (Lección A14).

---

## 5. Estado git al cierre S65

- Último PR S65 mergeado: #94 (workflow reproc Tupungatito)
- Total PRs S62-S65 mergeados: 16
- Workflows operacionales activos:
  - `nrt.yml` cron cada 2h
  - `pages-deploy.yml` (fix S62 #87)
  - Reproc workflows: Villarrica+PP, Lastarria+Chaiten, PCC operacional, Tupungatito operacional
  - A/B workflows: kernel-bg Villarrica/PP/Lastarria/Tup/Chaiten/PCC
- Audit scripts: `experiments/110-115_s62-s65_*`

---

## 6. Resumen objetivo clon literal MIROVA NRT

### Logrado S60-S65 (78% del Tier A)
- 5 vols kernel-bg adoptados operacional
- 2 vols calibrados natural
- Pages-deploy permanente fix
- Tupungatito fix aplicado (pendiente validar)

### Si Tupungatito valida S66
- 8/9 vols = **89% Tier A clon literal MIROVA**
- Solo Llaima/Copahue/NdC quedarán (poca data, no accionables sin más ALERTAS)

### Futuro S67+
- MODIS final_hotspot fix (mejora dashboards MODIS)
- Refinamientos opcionales si surgen casos específicos

---

## 7. Persistencia in-vivo

Cuando S66 audit Tupungatito → persistir resultado INMEDIATAMENTE en HYPOTHESIS_LOG. Sea valida o no, documentar para no repetir investigación.
