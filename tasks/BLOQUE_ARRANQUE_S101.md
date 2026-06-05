# BLOQUE ARRANQUE S101

**Sesión previa S100 (2026-06-04).** MUY larga. ~10 PRs (#332-341). Cerró el fix de
magnitud 19× Tupungatito (adopción ctxpeak) + auditoría de coherencia del dashboard +
mejoras de tarjetas + arreglo del refresh. Detalle: `docs/S100_TEST1_FULL_AB.md`,
`docs/S100_DASHBOARD_AUDIT.md`, `project_s100_estado` (memoria).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
```

## §1 — Reproc histórico ctxpeak: CASI COMPLETO (solo falta Llaima + R8)
El fix ctxpeak adoptado (#340) + histórico abr-may promovido (#343): **Tupun/Lastarria/PP
curados** (Tupun mediana Test1 2.68→0.27 MW, detecciones conservadas). Reproc fresco
run 26984922901 (4×2 chunks) + `merge_promote_ctxpeak.py` con guard anti-underfetch.

**Pendiente §1**:
1. **Llaima** quedó SKIP (guard: reproc trajo 416<421 det base = under-fetch en un chunk).
   Re-reproc Llaima abr-may (re-disparar `reproc-s100-promote-ctxpeak.yml`, o solo Llaima)
   y promover (el guard lo deja pasar si esta vez baja todas las det). Es menor (poca
   actividad Test1). Su pico viejo 6.12× sigue en Diario hasta entonces.
2. **R8 público**: verificar en el sitio live (post-deploy #343) que la serie de Diario
   de Tupungatito abr-may bajó (pico ~7→~0.3 MW). Junio se cura solo con NRT cron.

## §2 — FRENTE MODIS (próximo gran tema, acordado tras cerrar magnitud)
Auditoría S100 lo dejó mapeado (`docs/S100_DASHBOARD_AUDIT.md` hallazgos #1+#4 +
`experiments/_s99_audit/modis_diffuse/scope.md`). Es OTRO mecanismo (MODIS 1km lee
contraste nube/nieve como anomalía), distinto de la magnitud Test1 ya resuelta.
**3 patas, mismo reproc MODIS (GH/Linux, pyhdf roto local), brainstorming + A45:**
1. **`distance_class` corrupto** (#1, A46/Eje5-S95): se calcula del hotspot SUELTO, no
   del cluster → casi todos los MODIS salen "far" con cluster cerca (o Villarrica
   "summit" a 21km). Fix: derivar del primary_cluster (espejo del fix ancla S98).
   ⚠️ reclasifica summit/far en TODOS los vols → afecta recall, verif pixel-level.
2. **MODIS artefacto pasa filtros** (#4): campo difuso/cirrus sobre escena gélida entra
   como summit (Chaitén 206 MW, 545px, t_bg -48°C). Filtros display S92/S93 no lo
   atrapan. Fix: ampliar criterio (campo disperso n_px alto + fondo gélido).
3. **Magnitud campo difuso** (§2): MODIS infla (PCC 264-630 MW) por suma de campo tibio.
**Riesgo A55**: no meter parches que oculten detecciones reales → brainstorming primero.
**Mitigación parcial ya aplicada**: fix #2 (tabla NRT gatea distancia) oculta los MODIS
far de la tabla; pero pills de sensores y serie Diario aún reflejan MODIS artefacto.

## §3 — Pendientes menores
- **76 ramas remotas `claude/sNN-*` stale**: pendiente confirmación Nicolás para podar.
- DF-2 (integrated Eq.1) → beyond-MIROVA EXT-11.
- (S99) NEW-7 ya reclasificado (#333), issue #1 cerrado.

## Lecciones de método S100 (para no repetir)
- **A/B con jobs separados → confounder de granules** (cada job fetchea NASA distinto;
  con timeouts CMR bajan sets distintos). Solución: paired (ambos perfiles MISMO runner)
  → granules idénticos. Auditar SIEMPRE sobre records comunes (ab_test1_fair.py).
- **Promover artifacts de A/B parcial PIERDE detecciones** (bajó menos granules que el
  operacional acumulado). Verificar detecciones base-vs-reproc ANTES de commitear;
  guard anti-underfetch en el merge.
- Reproc eficiente: solo los vols/ventana que el flag realmente cambia; chunks 1 mes.

## Tags defensivos S100
`pre-s100-test1-magnitude-adopt` (pre-flip ctxpeak).

## Worktree canónico
Raíz `VRP Chile/` en main al día.
