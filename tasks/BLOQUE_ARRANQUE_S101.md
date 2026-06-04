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

## §1 — PRIORIDAD: terminar de promover el reproc histórico ctxpeak (EN CURSO al cierre)
El fix de magnitud ctxpeak YA está adoptado en `mirova_equivalent` (#340, NRT cura
desde ahora). Falta promover el HISTÓRICO abr-may para que la serie de **Diario**
muestre Tupungatito/Lastarria/PP/Llaima curados (hoy esos picos siguen inflados en
la vista 90d).

**Reproc lanzado al cierre: run `26984922901`** (4 vols × 2 chunks abril/mayo, perfil
mirova_equivalent con ctxpeak ON). **Pickup cuando termine:**
```bash
gh run download 26984922901 -D experiments/_s99_audit/_promo_art
python experiments/_s99_audit/merge_promote_ctxpeak.py   # tiene GUARD anti-underfetch
git diff --stat data/mirova_equivalent/   # ver qué cambió
```
El script NO escribe un vol si el reproc trae menos detecciones que el base (guard:
hoy el A/B parcial habría borrado ~130 det/vol — verificado y revertido a tiempo).
Si el guard SKIPea algún vol → ese chunk hizo under-fetch (NASA), re-disparar.
**Tras merge OK**: verif preview 3 vistas (Diario: que el pico de Tupun abr-may baje
a ~1-2 MW) → commit+push data/mirova_equivalent → deploy → R8 público.
Junio (1-4) se cura solo con el NRT cron (ya usa ctxpeak).

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
