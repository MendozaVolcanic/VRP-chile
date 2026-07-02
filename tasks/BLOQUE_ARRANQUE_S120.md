# BLOQUE ARRANQUE S120 — post-auditoría integral S119

**S119 (2026-07-01)** ejecutó la auditoría integral post-flip completa
(`docs/AUDIT_S119.md`, scripts `experiments/_s119_audit/`): **Eje 1 VERDE — MANTENER
gates OFF** (NRT 100%, sin inflación summit, cola path-D tasa plana, JSONs contenidos);
Ejes 2/4/6 por subagentes paralelos (paridad sin regresión, integridad sana, cabos S118
cerrados); Eje 5 docs vivos actualizados (DIVERGENCES→RESUELTO S118, MISSION→Removido
S118, H_S118 REFUTADA, **regla A85** en CLAUDE.md); Eje 3 parcial (Panel 1 barrido,
link agregado, discrepancia Panel1-vs-2.3 EXPLICADA = mezcla de sensores).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S119.md   # estado completo post-auditoría
```

## §1 — Pendientes que requieren a NICOLÁS (no delegables, quedaron de S119)

1. **Eje 3.1/3.2 — beyond-mirova.html en navegador real**: validar las 3 pestañas
   (render de píxeles nunca visto en viewport real) + **afinar zonas 2a por volcán**
   (criterio geológico; hoy solo PCC documentado). Persistir en el objeto ZONES.
2. **WATCH Copahue (§2.4 AUDIT_S119)**: rumbo S ~1.2-1.3 km del pc VIIRS375 (n=110,
   estable) — cotejar posición cráter El Agrio vs vent configurado (−37.856, −71.183).
3. **Villarrica reactivado (§2.4-extra)**: lago de lava REAL desde ~03-jun (OCR MIROVA
   0.28-0.54 MW al cráter; consolidado no lo publica), nuestra magnitud ~3× por régimen
   nevado invernal. Mirarlo en el dashboard; vigilancia, no bug.
4. **Eje 7 — priorizar**: lista en AUDIT_S119 §7 (backfill VIIRS / GAP #A / NEW-8 /
   Panel 2b Eq.16 / zonas 2a / Panel 1 match-por-sensor / batch higiene).
5. **OK para borrar** `experiments/_s118_c2ab/_artifacts/` (86 MB local, results committed).

## §2 — Candidato estrella S120 (si Nicolás prioriza): auto-audit semanal

AUDIT_S119 §8: empaquetar los scripts S91 de la auditoría (recall/ratio A10/espacial
A61/cobertura/integridad) en un workflow cron semanal → `data/audit_continuous/latest.json`
+ issue automático si sale de banda. Convierte A51 de episódico en monitoreo continuo.
Los scripts ya existen en `experiments/_s119_audit/` — es empaquetarlos (~1 sesión).

## §3 — Batch higiene (bajo riesgo, puede ir sin Nicolás salvo el tag)

- ✅ **HECHO (PR #477, 2026-07-01)**: 28 workflows one-shot → `.github/workflows/_archive/`
  + 90 profiles huérfanos → `pipeline/profiles/_archive/` (tag defensivo A38
  `pre-s120-hygiene-archive`; cross-check 0 refs activas; suite 796 passed).
- ✅ **HECHO (PR #477)**: guard utf-8 stdout en los 7 scripts del scan
  (`eje6_2_encoding_scan.json`, patrón reconfigure S118). **Sigue diferido**:
  `→`→`->` en mensajes runtime `fetch.py` (ciclo A45 conjunto con próximo cambio de fetch).
- ✅ R2 pixel-level post-flip **DESBLOQUEADO** (corrección S120, diagnóstico subagente):
  el poll TIF NUNCA estuvo estancado — el repo remoto `mirova-tif-archive` está verde
  (runs cada 5 min, TIFs de 2026-07-02 en index.csv, mirovaweb HTTP 200). Era el **clon
  LOCAL** desactualizado desde 2026-05-20 (patrón A25: repo 9.2 GB, `git fetch` local
  timeoutea). Para R2: bajar TIFs puntuales vía
  `https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/data/tif/<Vol>/<file>.tif`
  (catálogo = index.csv remoto); NO hacer `git pull` pelado (baja GB). Clon local:
  re-clonar con `--filter=blob:none` cuando se necesite completo.

## 🚫 NO reabrir (anti-A8) — sin cambios
far→summit MODIS/D11/A69-como-bug (A82) · re-ancla ctx_cluster (A84) · inner PCC ·
Parte C NdC (A77) · fondo-local-NTI (S105) · per-régimen C2 (MISSION l.77) ·
**gates C2 (CERRADO S118/S119, A85)**.

## Estado operacional al cierre S119
NRT cada 2h gates OFF, 100% verde. Suite **796 passed** (conteo limpio post
`testpaths=tests`; el 797 previo incluía 1 pseudo-test de experiments/). Guard A46 LIVE
(0 violaciones post-flip). Ground truth snapshot fresco (CONS 25,210 / OCR 737).
Recall: VIIRS375 98.4% / V750 84.5% / MODIS-cráter 100%. Magnitud 9/11 en banda.
