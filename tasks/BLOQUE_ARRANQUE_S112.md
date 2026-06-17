# BLOQUE ARRANQUE S112

**Sesión S111 (2026-06-16/17)** cerró 3 frentes: D11 (ancla MODIS) **NO ADOPTAR**;
**reactivación NdC** (Test1-lowmag) Parte A mergeada + Parte B diseñada PENDIENTE; diurno
cerrado. 3 PRs (#433 D11, #434 Test1-lowmag Parte A, #435 rediseño A/B). Registro completo:
`project_s111_estado` (memoria). **Nada operacional cambió — todo flag OFF.**

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/superpowers/specs/2026-06-16-test1-lowmag-recovery-design.md   # diseño Parte B (PRIORIDAD)
cat docs/AUDIT_S111_TEST1_LOWMAG_FN.md                                  # diagnóstico reactivación NdC
```
Leer también en memoria: `project_s111_estado`, `MEMORY.md` (veredicto D11 + frente Test1-lowmag).

## ✅ Cerrado en S111 (todo en main, flags OFF)
- **D11 ancla MODIS gateada por first_pass_summit** (#433, M1, flag OFF). Helper puro
  `honest_anchor_applies`. A/B (run 27662625697 16/16 OK tras rediseño chunks-1-mes #435).
  **VEREDICTO: NO ADOPTAR.** Gate NECESARIO pero NO SUFICIENTE: criterios mecánicos PASS, pero
  cruce C3 con MIROVA (pc.vrp_mw — A10) → solo **Lascar se alinea** (26/70 flips = cura D12 real);
  **NdC/Villarrica/Tupun** promueven 40/51/111 flips ~0.6-1.25 MW que MIROVA MODIS NO ve =
  **campo difuso A69 residual** (focal cortó 68→1.25 pero queda; VIIRS reactivación 0.06 vs MODIS
  1.25 = 20×, no es la misma lava). `enable_honest_anchor_modis` SIGUE OFF.
- **Reactivación NdC — Parte A** (#434, flag OFF): el Test1 gana `source` cuando un cluster rival
  débil (1px vrp≈0) lo tapaba y colapsaba la magnitud a 0. Helper `resolve_test1_source_priority`.
  Verif. adversarial 3 revisores CLEAN. Flag `enable_test1_priority_weak_cluster` OFF.
- Diurno: investigado/CERRADO (inocuo sin beneficio, A76; recall MODIS bajo = física sub-píxel).

## §1 — PRIORIDAD S112: Parte B reactivación NdC (calibrar magnitud "Muy Bajo")
**El caso**: NdC entró en sitio eruptivo NUEVO; MIROVA VIIRS375 **0.06 MW** (06-16 05:30). La
**detectamos espacialmente** (Test1 summit 0.44 km) pero magnitud=0. La Parte A destapa el camino;
la Parte B **calibra el número** contra las 6 ALERTAS MIROVA VIIRS375 NdC.

**CORRECCIÓN CLAVE (verif. adversarial S111)**: NdC/Lascar/Lastarria YA tienen
`lbg_global_compatible=true` + `enable_test1_lbg_global` ON → con Parte A ON su recompute ya usa
fondo GLOBAL → da **~0.26 MW (4.4× alto)**, NO ~0. **La Parte B debe BAJAR del 0.26 al 0.06 SIN
inflar RUTINA**, no "destapar".

**Pasos (A45, tag `pre-s111-test1-lowmag` ya existe)**:
1. Brazos A/B (todos = Parte A ON + una cuantificación): Q3 anillo intermedio (código nuevo:
   fondo 2-4/3-5 km) / Q4 Eq.16 lava lake (`lava_lake_magmatic` NdC en volcanoes.yaml) / Q5 fondo
   NTI local (`enable_test1_local_bg_nti`) / Q6 filtros compacidad (`enable_test1_*_filter`).
2. Perfiles A/B + per-vol config (añadir fields a NdC en volcanoes.yaml — seguro, inerte sin flags
   globales; Edit no rewrite). Audit pre-escrito.
3. A/B **targeted a las 6 fechas ALERTA + muestra RUTINA** (rápido, minutos — NO 2 meses).
   Criterio A66: reproducir 0.02-0.49 (mediana 0.06) + **RUTINA inflada ESTRATIFICADA por
   NdC/Lascar/Lastarria <0.01 MW**.
4. Si gana un brazo → flip + reproc + R2/R3/preview (A45 nuevo OK Nicolás). MODIS = follow-up (la
   Parte A es VIIRS-only; process_modis tiene el mismo bug latente).

**Las 6 ALERTAS MIROVA VIIRS375 NdC** (ground truth, `experiments/_s111_d11/mirova_fresh/cons.csv`):
06-16 05:30 (0.06) · 05-14 05:48 (0.06) · 05-02 05:24 (0.03) · 04-17 06:48 (0.02, src=test1 pero
vrp=0 → sub-problema B fondo) · 03-22 04:54 (0.49, **Parte C: FN detección, Test1 NO disparó**) ·
+1 sin pasada nuestra.

## §2 — Follow-ups (decisión Nicolás)
- **Frente MODIS A69** (D11 reabierto): el ancla MODIS necesita un escalón más (cap magnitud /
  co-validación VIIRS) para los 3 nevados antes de adoptar. Backlog. NO urgente.
- **PCC + Chaitén focal**: re-reproc targeted (guard under-fetch S110). Frente menor.
- Migrar la Parte A del fix Muy Bajo a MODIS (paridad), si la Parte B valida en VIIRS.

## 🔑 Reglas vivas / A-rules candidatas (formalizar revise-claude-md)
- **A10 reforzada**: cruce A/B vs MIROVA SIEMPRE con `pc.vrp_mw`, NO `record.vrp_mw` (scene-wide =
  campo difuso; casi reporté 7 MW FP que con pc.vrp eran ~1 MW).
- **A62 sobre A/B**: el "PASS mecánico" de criterios pre-registrados ENGAÑA sin el cruce contra
  ground-truth (MIROVA). Siempre cruzar antes de adoptar.
- **Gate de detección genuina necesario ≠ suficiente**: first_pass_summit bloquea la recaptura
  artefacto pero el first-pass dispara genuino sobre campo difuso/glaciar (NdC/Villarrica/Tupun) →
  el gate solo no alinea con MIROVA.
- **Magnitud "Muy Bajo" finamente sensible al fondo**: local→0, global→0.26 (4.4×), MIROVA→0.06.
  Calibrar empíricamente, nunca a ojo.
- **Reproc histórico: chunks ≤1 mes** (2 meses × todos los sensores timeoutea >5h20min). A15.

## Estado operacional (sano)
NRT cada 2h. Magnitud focal MODIS live. VIIRS sano. Ancla MODIS OFF (D11 no adoptado). Fix Muy Bajo
OFF (Parte A mergeada, Parte B pendiente). Display frescura live.

## Prompt copy-paste S112
```
Sesión S112 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S112.md + project_s111_estado (memoria) + el diseño
docs/superpowers/specs/2026-06-16-test1-lowmag-recovery-design.md.
S111 dejó la PRIORIDAD clara: la Parte B del frente "Test1-lowmag" — calibrar la magnitud "Muy
Bajo" de la PRIMERA anomalía en el sitio eruptivo NUEVO del cráter de Nevados de Chillán (MIROVA
VIIRS375 0.06 MW, que detectamos espacialmente pero con magnitud 0). La Parte A (que el Test1 gane
la fuente cuando un cluster débil lo tapaba) ya está mergeada flag-OFF (#434). Falta el A/B de
calibración: probar fondo intermedio / Eq.16 lava lake / fondo NTI / compacidad contra las 6
ALERTAS MIROVA VIIRS375 NdC, BAJANDO del 0.26 (que da el fondo global, ya activo en los 3 nevados)
al 0.06 SIN inflar las noches RUTINA. Es A45 (tag pre-s111-test1-lowmag ya existe) + TDD + A/B
targeted a las 6 fechas (rápido) + criterio pre-registrado con RUTINA estratificada por
NdC/Lascar/Lastarria. El frente D11 (ancla MODIS) quedó NO ADOPTADO (gate necesario no suficiente,
campo difuso A69 sigue abierto) — secundario. RECORDÁ: A45, MISSION 3-preguntas, A62 adversarial
(cruzar vs MIROVA con pc.vrp_mw — A10), explicame como geólogo.
```
