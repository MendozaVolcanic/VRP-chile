# BLOQUE ARRANQUE S110

**Sesión S109 (2026-06-14/16)** — sesión larga: replanteó+adoptó la magnitud MODIS, resolvió 2
frentes VIIRS, arregló el NRT (breaker + display), y dejó el ancla MODIS para D11.
Registro completo: `project_s109_estado` (memoria) + docs (abajo).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md   # veredicto magnitud focal + verificación NdC
gh run view 27584249199 --json status,conclusion,jobs   # reproc-promote: ¿completó? ¿jobs timeout?
```

## ✅ Cerrado en S109 (todo mergeado a main)
- **Magnitud núcleo-focal MODIS ADOPTADA** (PR #423, A45 OK Nicolás): flip `enable_focal_cluster_
  magnitude:true`+`focal_cluster_keep_peak:true`. De-infla el campo difuso topográfico (A69/D11) sin
  tocar detección. A/B 36/36 (run 27521928757): C1 0-diffs, C3 Láscar 1.000, C4 foco 1.000, C2 71%
  (mediana 0.42×). Tag pre-s109-focal-magnitude-promote. **NRT ya lo aplica a registros nuevos.**
- **Frentes VIIRS resueltos sin acción** (PR #419, `docs/AUDIT_S109_VIIRS_FRENTES.md`): #3 ratio =
  paridad (canónico por-noche 0.78/0.81×; el 0.5× era por-pasada; json regenerado). #2 ctxpeak V750
  refutado (dispersión ya curada; riesgo FN, A66).
- **Display frescura de monitoreo** (PR #420, LIVE 3 vistas): 🟢 monitoreado / 🟠 atrasado / 🔴 sin
  pasadas — distingue "tranquilo" de "sin data" (resolvió confusión NdC) + surfacea gap LANCE.
- **Breaker LANCE resiliente** (PR #421, VERIFICADO): probe TCP 5s antes de tripear → los 3 vols
  atrasados (Láscar/Isluga/Villarrica) se pusieron al día. A64 extendido.
- **Scroll al mapa** desde la tabla NRT (PR #422).

## §1 — PRIORIDAD S110a: completar la promoción de magnitud focal (corto, mecánico)
**Reproc histórico run 27584249199** (11 Tier A MODIS × 2 chunks, perfil `_s109_focal_promote`):
1. Verificar que completó. **OJO timeouts**: jobs a ~240 min cerca del límite 290 (NASA lenta este
   período, no el breaker — ver project_s109). Re-correr chunks fallidos si hay (`gh workflow run
   reproc-s109-focal-promote.yml --ref main` o re-run del job).
2. `gh run download 27584249199 -D experiments/_s109_modis_mag/_promo_art`
3. `python experiments/_s109_modis_mag/merge_promote_focal.py` (YA pre-escrito: MODIS curado, VIIRS
   byte-idéntico, guard cobertura anti-underfetch). Esperado: `MODIS infl>5MW` baja fuerte por vol.
4. R3 / preview 3 vistas (las magnitudes MODIS de-infladas visibles en diario/mosaico) → commit data.

## §2 — PRIORIDAD S110b: frente D11 (detección MODIS A69-inmune) — desbloquea el ancla
**Decisión metodológica (MISSION) → brainstorming + papers-first ANTES de implementar.** El ancla
MODIS (`enable_honest_anchor_modis`) sigue OFF porque su destape NdC es **71% artefacto A69**
(verificado S109: VIIRS375 pasa y NO ve nada mientras MODIS sobre-detecta el campo tibio topográfico;
25% real cat-b). El root fix = **detección MODIS por NTI contextual** (como VIIRS, inmune a la
topografía A69), NO MIR absoluto. Eso limpia NdC en la raíz → después el ancla va limpio y cura el
recall D12 (10.8%→~96%). Relacionado: D11 en MIROVA_DIVERGENCES (cara-detección; la cara-magnitud se
cerró S109). Script de diagnóstico NdC: `experiments/_s109_modis_mag/verify_ndc_destape.py`.

## 🔑 Reglas vivas / A-rules candidatas (formalizar con revise-claude-md)
- **Discriminante A62 cross-sensor para artefacto A69**: "VIIRS375 (más fino) pasa y NO ve nada
  mientras MODIS detecta" = artefacto topográfico, no señal real (VIIRS más sensible debería ver MÁS).
  Usado para verificar el destape NdC (71% artefacto).
- **El breaker resiliente (S109) agrega ~6 min/job worst-case** ante LANCE flapping (trips una vez,
  después skip). NO es la causa de reprocesos lentos — esa es NASA. Bounded, no toca el anti-cuelgue.
- **Promoción magnitud MODIS = patrón merge_promote_nadir** (MODIS-only, guard cobertura, VIIRS intacto).
- **A53**: ~10 PRs esta sesión (#418-423 + frontend). Cerca del cap soft 12. S110 consolidar.

## Estado operacional (sano)
NRT corre cada 2h (breaker resiliente). Magnitud focal MODIS live (registros nuevos curados; histórico
en reproc). Display frescura live. VIIRS sano (paridad). Ancla MODIS OFF (D11). Reproc en vuelo.

## Prompt copy-paste S110
```
Sesión S110 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S110.md + project_s109_estado (memoria) + docs/AUDIT_S109_MODIS_FOCAL_VEREDICTO.md.
S109 ADOPTÓ la magnitud núcleo-focal MODIS (A/B 36/36, de-infla el campo difuso topográfico sin tocar
el foco; PR #423) y dejó corriendo el reproc histórico (run 27584249199) para curar lo viejo. También
resolvió los 2 frentes VIIRS (paridad, sin acción), arregló el NRT (breaker LANCE resiliente +
display de frescura de monitoreo en las 3 vistas) y agregó scroll al mapa. El ANCLA MODIS sigue OFF
adrede: su destape de Nevados de Chillán es 71% artefacto topográfico A69 (verificado), que se arregla
en la DETECCIÓN, no mostrándolo. PRIORIDAD S110: (a) completar la promoción de magnitud — verificar el
reproc 27584249199 (ojo timeouts ~240min), download → merge_promote_focal.py (pre-escrito) → R3 +
preview → commit la data curada; (b) arrancar el frente D11: detección MODIS por NTI contextual
(A69-inmune, como VIIRS), que desbloquea el ancla y cura el recall D12 — es decisión metodológica
(MISSION) → brainstorming + papers-first ANTES de implementar. RECORDÁ: A45 (flip→tag+OK), MISSION
3-preguntas, A62 adversarial, explicame como geólogo.
```
