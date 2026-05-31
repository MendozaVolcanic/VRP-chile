# BLOQUE ARRANQUE S95

**Sesión previa S94 (2026-05-31).** MUY larga y productiva (~14 PRs #282-294, un
reinicio de PC de por medio). Re-análisis por sensor + re-centrado en VIIRS + diseño
F5' + reproc de homogenización + **1er cambio operacional al pipeline de la sesión**
(fix Test1 anomaly_pixels). main al día.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S95.md
cat docs/AUDIT_S94_per_sensor_metrics.md           # marco por-sensor + espacial + VIIRS
cat docs/superpowers/specs/2026-05-31-f5-coldfield-magnitude-design.md  # diseño F5' (3 variantes)
```
Memoria: [[reference_s94_per_sensor_corrected]] (índice completo S94).

## §0.5 — Integridad + reglas (vigentes)
Ningún número a mano (script reproducible + verificación). **A48 reforzado**:
`anomaly_pixels.dist_km` es desde el CENTRO del volcán, NO desde el vent → las variantes
F5' recomputan distancia desde vent. A45 para tocar pipeline (tag+OK+TDD+reproc). A47 no
paralelo sobre mismo data_subdir. **VRP_TMP_DIR=C:/vrp_tmp** (fuera de OneDrive, si no el
disco se llena y el cleanup falla). Token Earthdata en `C:/Users/nmend/edl_token.txt`
(⚠️ **ROTAR** — quedó en el chat S94; vence ~60 días).

## §1 — PENDIENTE PRINCIPAL S95: re-reproc con el fix Test1 → calibrar F5'

El fix Test1 (PR #294) ya está en main, **pero la data `data/_s94_reproc_viirs/` actual es
PRE-FIX** (anomaly_pixels vacío en records Test1, salvo Tupun 05-28 que validé). Para
calibrar F5' hace falta data CON anomaly_pixels poblado.

**Paso 1 — re-reproc ventana reciente CON el fix** (~1-1.5h, los 6 clave):
```bash
export EARTHDATA_TOKEN=$(tr -d '[:space:]' < "C:/Users/nmend/edl_token.txt")
export VRP_TMP_DIR="C:/vrp_tmp"
# local (3 paralelo + guard) — Tupun/PCC/Lascar:
python experiments/_s94_audit/disk_guard.py &   # red de seguridad (mata si <8GB)
for V in Tupungatito PuyehueCordonCaulle Lascar; do
  python scripts/run_pipeline.py --profile _s94_reproc_viirs --volcano $V \
    --start 2026-05-01 --end 2026-05-29 --overwrite &
done
# GitHub (toma el fix de main) — Villarrica/PP/Lastarria:
gh workflow run reproc-s94-f2-viirs.yml --ref main -f start=2026-05-01 -f end=2026-05-29
```
Verificar: ~3-4 vols en paralelo max (disco ~5GB/vol transitorio; guard activo).

**Paso 2 — validar + calibrar F5'**:
```bash
python experiments/_s94_audit/merge_reproc_arms.py        # une MODIS+VIIRS → _s94_reproc
python experiments/_s94_audit/validate_reproc.py          # Q1 consistencia (debe dar OK ahora)
VRP_DATA_DIR=data/_s94_reproc_viirs python experiments/_s94_audit/f5_variants.py  # 3 variantes vs MIROVA
```
Elegir la variante (D1/D2/D3 — ver design doc §3-4) que cumpla: Láscar 0.9-1.1×, campo frío
→ ~1×, ningún confirmado a 0, R2 pixel-level. Barrer params. Después: implementar F5' display
(brainstorming gate ya pasado; calibración decide la forma). A45 si baja a pipeline.

## §1.5 — AUDITORÍA de errores similares (PRIORITARIO, antes de cerrar el reproc)

Pedido de Nicolás (cierre S94): los gaps que descubrimos suelen ser **sistémicos**.
Auditar errores del mismo patrón Y el impacto más amplio de los que ya encontramos.
**Hacer ANTES de dar el reproc por bueno** — puede cambiar el alcance.

1. **¿El gap Test1 anomaly_pixels existe TAMBIÉN en los otros 2 procesadores?**
   El fix #294 fue SOLO en `process_viirs.py`. `process_modis.py` y
   `process_viirs_mod.py` (VIIRS750) tienen su propio path Test1 — muy probable que
   dejen `anomaly_pixels=[]` igual. **Verificar** (grep del path Test1 + revisar un
   record MODIS/VIIRS750 Test1 reprocesado: ¿n_aps=0 con pc.vrp>0?). Si sí:
   - Aplicar el mismo helper `build_anomaly_pixels` (ya existe) en esos paths (A45,
     TDD, tag).
   - **El reproc MODIS ya está hecho (data/_s94_reproc_modis/) — re-reproc MODIS** si
     tiene el gap (afecta el mapa de píxeles MODIS del dashboard + cualquier análisis).

2. **Otros "calculado pero no persistido" (patrón A07)** en los 3 procesadores:
   buscar variables que se computan pero no entran al return dict / record (como
   S21 H_S21_11: std_bg_i04/threshold_mir/nti_std). Grep de asignaciones locales
   vs campos del record.

3. **Otros campos con punto de referencia engañoso** (A48/A3): `anomaly_pixels.dist_km`
   es desde el CENTRO del volcán, no el vent. ¿Hay otros campos `*_dist_km` /
   coords medidos desde un punto que no coincide con su nombre? (revisar store.py +
   los 3 procesadores).

4. **Impacto más amplio del gap Test1** (ya fijado pero verificar arrastre): ¿qué
   scripts/audits/R2 leyeron `anomaly_pixels` de records Test1 y dieron resultados
   FALSOS por la lista vacía? (ej. cualquier audit pixel-level, el mapa del dashboard,
   experiments que sumen anomaly_pixels). Listar y re-verificar.

5. **Asimetría de esquema hotspot single vs primary_cluster** (A46): ¿hay gates
   downstream que usen una representación del hotspot y den incoherencia con la otra,
   como el bug F47 H4? Revisar gates que decidan rollup vs zero-out.

Producir `docs/AUDIT_S95_gaps_sistemicos.md` con lo encontrado + clasificación
(real/falso, impacto, fix needed). Usar subagentes en paralelo (A26) si hay >3 ejes.

## §2 — Estado del reproc S94 (qué hay)
- **MODIS GitHub COMPLETO** (11 vols full window, `data/_s94_reproc_modis/`). ✓
- **VIIRS recent PRE-FIX** (Tupun/PCC/Lascar local, ~completo; Villarrica/PP/Lastarria GitHub
  cancelado pre-fix). → re-reproc paso 1.
- FASE 2 (enero-abril homogenización completa) = task #11, multi-día, después de F5'.
- `data/_s94_reproc_viirs/` local NO commiteado (pre-fix, descartable).

## §3 — Hallazgos durables S94 (no re-derivar)
- Métricas por sensor: VIIRS750 recall 83-87% (NO 0; era bug bucketing). MODIS recall-cráter
  11.8% = deuda Salar. VIIRS375 es el caballo de batalla (95%).
- Magnitud campo-frío VIIRS: Láscar 0.93× (cráter caliente OK), Tupun 10.78× (glaciar). NO es
  calibración ni suma-vs-foco — es QUÉ píxeles entran (halo path D). Discriminante = ESPACIAL.
- Path-type NO distingue real-débil de halo (ambos path-D) → co-validación/excluir-path-D-only
  BORRA reales. Refutado.
- Gap Test1 anomaly_pixels = FIJADO (PR #294).
- Reproc: solo MODIS necesita GitHub (pyhdf); VIIRS local OK con token + VRP_TMP_DIR.

## §4 — Escudo anti-drift
NO gate t_bg ciego (S86). NO ocultar VIIRS750 (MIROVA lo usa). NO tocar detección VIIRS375.
NO co-validación VIIRS (borra reales). PCC lacolito = cat. b real, no forzar (A55). Detección
NUNCA se toca en F5' (magnitud es post-proceso). Calibrar SOLO sobre data reprocesada.
