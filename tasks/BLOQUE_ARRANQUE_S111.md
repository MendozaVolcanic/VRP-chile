# BLOQUE ARRANQUE S111

**Sesión S110 (2026-06-16)** — cerró §1 (promoción magnitud focal) y dejó el frente D11
**totalmente diagnosticado con diseño completo y aprobable**, listo para implementar. 6 PRs
(#425-430). Registro: `project_s110_estado` (memoria) + docs (abajo).

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat docs/superpowers/specs/2026-06-16-d11-ancla-modis-crater-gated-design.md   # diseño D11 COMPLETO
cat docs/AUDIT_S110_NDC_PAPERS_SYNTHESIS.md                                    # papers-first 4 agentes
cat docs/AUDIT_S110_NDC_PATH_DIAGNOSTIC.md                                     # probes run-1/run-2
```

## ✅ Cerrado en S110 (todo en main)
- **§1 magnitud focal promovida al histórico** (PR #426): 9/11 Tier A. Detección invariante
  (triggered_test1 0-diffs), magnitud de-inflada (Villarrica 31→1 infl, sum 801→379 MW; Tupun 18→11;
  etc.). Dashboard muestra magnitudes curadas. **PENDIENTE: PCC + Chaitén** (SKIP por guard
  under-fetch 1 granule esa corrida; NRT ya les aplica focal a registros nuevos; histórico = re-reproc
  targeted, frente menor).
- **D11 reformulado a fondo** (PRs #425/#427/#429/#430): NO es Test1, NO es "portar NTI". El leak
  topográfico del valle NdC entra 100% por el piso absoluto C1 (probe run-1); el ETI espectral SÍ
  cancela el grueso (valle ETI abs ≈0, probe run-2) — el leak es textura residual del valle. **El
  cráter es el discriminador** (ETI≈0 artefacto, +0.003 real). Papers-first (4 agentes): código ETI
  fiel a Coppola (A48). **Tarea spec #1 RESUELTA** (probe_ndc_assembly run 27625289232): los píxeles
  near-crater artefacto son 100% recaptura second-pass que el gate S85 preserva (first_pass_summit
  ARTEFACTO=0 / REAL=57). **Confirma A55** (el gate intra-radio S85 fabrica el artefacto near-crater).
- **FICHA SDA transparencia algorítmica** (PR #428): ficha publicable + cabecera vrp_regimes.py +
  bloque CLAUDE.md. Completo como piloto; campos `<completar>` para SERNAGEOMIN.

## §1 — PRIORIDAD S111: implementar el gate del ancla MODIS (D11, A45)
**Diseño COMPLETO y aprobable**: `docs/superpowers/specs/2026-06-16-d11-ancla-modis-crater-gated-design.md`.
Target = **solo el ancla** (no detección). Gate CONFIRMADO con datos:
> **El ancla MODIS far→summit dispara solo si `first_pass_summit > 0`** (≥1 seed del FIRST-PASS
> Tests 2&3 dentro del inner_radius), **excluyendo la recaptura second-pass / gate S85**.
> NdC artefacto (0) → no flip; Láscar D12 (>0) → flip → cura recall.

Pasos (A45, decisión Nicolás antes de empezar):
1. `git tag pre-s111-ancla-modis-crater-gated <sha>` + push.
2. Persistir `n_first_pass_summit` en el record (process_modis) o exponer la máscara first-pass∩inner
   al ancla (anchor.py). NO usar `primary_cluster.centroid` ni `n_anomalous_pixels` (contaminados S85).
3. Flag nuevo default OFF (`enable_honest_anchor_modis` gateado por first_pass_summit).
4. TDD primero (test que captura: NdC artefacto no flip / Láscar flip). A/B 3 brazos (base / ancla-sin-gate
   / ancla-con-gate). Criterios pre-registrados A66 (ver design §5): C1 NdC ≈49 flips no ~141; C2 Láscar
   recall curado; C3 cat-b preservado; C4 detección invariante.
5. R2 pixel-level + R3 audit + preview 3 vistas antes de promover.

## §2 — Follow-ups (menores, decisión Nicolás)
- **A55 ahora con datos**: el gate S85 (y posiblemente S84 path-D) fabrica el cluster near-crater
  artefacto. El gate del ancla lo esquiva SIN tocar S85. Pero queda la pregunta de si S85/S84 deberían
  revisarse en sí (son detección → fuera del scope "solo ancla" de S110, pero el dato ya está).
- **PCC + Chaitén focal**: re-reproc targeted para de-inflar su histórico MODIS (1 granule under-fetch).

## 🔑 Reglas vivas / A-rules candidatas (formalizar con revise-claude-md)
- **Discriminador first_pass_summit para el ancla** (S110): "señal-summit genuina" = seed del first-pass
  en inner, NO la recaptura second-pass/S85. El centroide del cluster y n_anomalous_pixels están
  contaminados por la recaptura intra-radio.
- **ETI espectral ≠ roto aunque el dETI del valle ≠0** (S110): el ETI cancela el gradiente de gran
  escala (valle ETI abs ≈0); el leak es textura residual cruzando el piso absoluto C1. Verificar ETI
  ABSOLUTO (no solo dETI contextual) antes de concluir "normalización rota".
- **Probe de atribución por etapa del ensamblado** (S110 A65): monkeypatch read-only que captura
  masks intermedias (first-pass / second-pass / gate) para atribuir píxeles sin tocar pipeline.

## Estado operacional (sano)
NRT cada 2h (breaker resiliente). Magnitud focal MODIS live (histórico 9/11 + NRT nuevos). VIIRS sano
(paridad). Ancla MODIS OFF (diseño D11 listo, implementación S111 gated A45). Display frescura live.

## Prompt copy-paste S111
```
Sesión S111 — VRP Chile. Sincronizá (git fetch origin --prune && git pull --ff-only) y leé
tasks/BLOQUE_ARRANQUE_S111.md + project_s110_estado (memoria) + el diseño completo
docs/superpowers/specs/2026-06-16-d11-ancla-modis-crater-gated-design.md.
S110 cerró la promoción de magnitud focal MODIS (9/11 Tier A) y dejó el frente D11 TOTALMENTE
diagnosticado con diseño aprobable: 3 probes + papers-first (4 agentes) probaron que el artefacto
topográfico de Nevados de Chillán que el ancla MODIS promovería NO es señal del first-pass (0 seeds
summit) sino recaptura del second-pass que el gate intra-radio S85 preserva (confirma A55). El gate
del ancla está CONFIRMADO con datos: flipear far→summit solo si first_pass_summit>0 (excluye la
recaptura S85) — NdC artefacto no flipea, Láscar D12 sí (cura el recall). PRIORIDAD S111: implementar
ese gate (target solo el ancla, NO detección) siguiendo el design doc — es A45 (tag + tu OK explícito
ANTES de tocar pipeline) + TDD + A/B 3 brazos con criterios pre-registrados + R2/R3/preview. Follow-ups
menores: re-reproc focal de PCC/Chaitén; decidir si S85/S84 se revisan en sí (con los datos S110).
RECORDÁ: A45, MISSION 3-preguntas, A62 adversarial, explicame como geólogo.
```
