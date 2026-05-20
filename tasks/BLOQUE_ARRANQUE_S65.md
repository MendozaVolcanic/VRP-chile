# BLOQUE DE ARRANQUE S65 — VRP Chile

> Cierre S64: PCC adoptado kernel-bg, reproc operacional completo
> (Lastarria, Chaiten, PCC), Tupungatito diagnóstico identificado pero
> implementación diferida.

---

## 1. Lectura obligatoria al inicio S65

1. **Este doc** — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S64.md`** — si existe / contexto S62-S63
3. **`docs/HYPOTHESIS_LOG.md`** entries S62-S64 (top 5)
4. **`docs/MIROVA_DIVERGENCES.md`** sección S60-S62
5. **`pipeline/profiles/mirova_equivalent.yaml`** — confirmar flags actuales
6. **`volcanoes.yaml`** — verificar per-vol flags

---

## 2. Estado al cierre S64

### Adopciones operacionales acumuladas (5 vols Tier A con kernel-bg)

| Vol | `local_kernel_bg` | `inner_radius_km` | Ratio | Adoptado |
|---|---|---:|---:|---|
| **Villarrica** | true | 5 | 2.17× | S61 |
| **PlanchonPeteroa** | true | 5 | 2.84× | S61 |
| **Lastarria** | true | 3 | 1.07× | S62 |
| **Chaiten** | true | 5 | 2.23× | S63 |
| **PCC** | true | 20 | 0.29× | S63 |
| Lascar | false | 5 | 1.37× | calibrado natural |
| Isluga | false | 5 | 1.33× | calibrado natural |
| Tupungatito | false (mirova_center offset) | 7 | 10.37× | **diferido S65+** |
| Copahue | false | 4 | (n=1) | poca data |
| Llaima | false | 5 | (n=3) | poca data |
| NdC | false | 5 | (n=0) | sin data |

### Pages-deploy permanente fix
- `if: != 'cancelled'` (PR #87 S62) — dashboard live se actualiza aunque NRT falle parcial
- 4+ deploys success consecutivos validan

### Reproc operacional completos S62-S64
- S62: Villarrica + PlanchonPeteroa (run 26068910717)
- S63: Lastarria + Chaiten (run 26116630144)
- S64: PCC (run 26138869110)

Dashboard live refleja calibración para 5 vols adoptados.

---

## 3. Pendientes priorizados S65

### Prioridad ALTA — implementación Tupungatito

**Diagnóstico S64 confirmado** (H_S64_TUPUNGATITO_MIROVA_CENTER_OFFSET):
- `vent_lat` Nicolás ya apunta al cráter activo correcto (lago cratérico, fumarolas)
- `mirova_center` (-33.4269, -69.8004) puesto S16 con offset 2.99 km SE = bbox center KMZ, NO actividad
- vent_anchored elige FPs flanco SE por mirova_center mal posicionado

**Fix S65**:
1. Editar `volcanoes.yaml` Tupungatito: quitar `mirova_center_lat/lon` (o igualar a vent_lat)
2. Disparar A/B reproc Tupungatito (workflow ya existe: `reproc-ab-lastarria-tupungatito.yml` adaptable)
3. Audit: si ratio LEGACY 10.37× → NEW <3×, ADOPTAR

Predicción: similar Lastarria post-fix (1-3× MIROVA).

### Prioridad MEDIA

2. **MODIS final_hotspot fix** (identificado S62):
   - `final_hotspot_lat/lon/dist_km` se asigna al pixel más caliente individual de la escena
   - Cuando cluster summit está cerca del vent pero hay pixels más calientes lejos (e.g. Villarrica MODIS 21/21 records `far`), dashboard excluye records summit válidos
   - Fix: asignar `final_hotspot` al pixel más caliente DEL CLUSTER SUMMIT
   - Implementación en `pipeline/process_modis.py`
   - Requiere test sintético + A/B + reproc

3. **Investigar Llaima/Copahue con `pc.vrp_mw`** (S62 paralelo finding):
   - Llaima n=3 (1 CONS + 2 OCR) ratio 6-12× con pc.vrp_mw
   - Copahue n=1 ratio 3.18× con pc.vrp_mw
   - Régimen Muy Bajo (VRP MIROVA 0.08-0.29 MW)
   - Solo si llegan más ALERTAS 2026-05/06: considerar A/B kernel-bg

### Prioridad BAJA (refinamientos)

4. **NRT cron 1 vol no-Tier-A failures** (SanJose/Antillanca etc.):
   - 6 vols fallan intermitentemente por NASA timeout
   - Cron sigue marked failure aunque Tier A OK
   - Pages-deploy ya tolera (PR #87 S62)
   - Fix opcional: retry específico para vols problemáticos

5. **NdC sin data MIROVA**: esperar más actividad para auditar

6. **kernel_size=5 / percentile p25**: descartados S62 análisis offline (lago Villarrica está a 15-18 km, fuera del kernel 1.9km). NO investigar a menos que justificación nueva.

---

## 4. Errores S64 a NO repetir

0. **NO asumir que el bin top de centroides = anomalía real**. Puede ser bin de FPs sistemáticos.
1. **PNGs MIROVA son dashboards de timeline, NO mapas con coord del hotspot**. Solo Distance chart muestra dist consistente.
2. **Validar coord activa con Nicolás** antes de mover (geólogo, conoce el cráter).
3. **`mirova_center` NO debe usar bbox center KMZ por default** — usa eso solo si centroide actividad coincide. Confirmar empíricamente.

---

## 5. Estado git S64

- Último PR S64 mergeado: #91 (PCC adopción) + 4-5 paralelos
- Total PRs S62-S64 mergeados: 14
- Workflows operacionales:
  - `nrt.yml` (cron cada 2h)
  - `pages-deploy.yml` (fix S62 #87)
  - Reproc workflows: Villarrica+PP, Lastarria+Chaiten, PCC operacional, PCC A/B, varios A/B kernel-bg
- Audit scripts: `experiments/110-114_s62-s63_*`

---

## 6. Verificación post-cierre S64

- Tests: 335 passed / 16 skipped ✓
- Dashboard live https://mendozavolcanic.github.io/VRP-chile/ refrescado ✓
- 5 vols Tier A con kernel-bg activo en cron NRT ✓
- 78% Tier A calibrado ≤3× (clon literal MIROVA NRT logrado parcialmente)

---

## 7. Persistencia in-vivo (regla meta-meta)

Cuando S65 descubra hallazgo nuevo: persistir INMEDIATAMENTE en `docs/HYPOTHESIS_LOG.md`. NO esperar al cierre.
