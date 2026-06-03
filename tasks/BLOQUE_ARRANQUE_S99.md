# BLOQUE ARRANQUE S99

**Sesión previa S98 (2026-06-02).** Fix del ancla de detección (Tupungatito/PCC/PP)
implementado, validado y **promovido a operacional**. ~6 PRs (#317-#320 + infra).
main al día. Detalle: `docs/S98_ANCHOR_FIX_RESULTS.md`,
`docs/superpowers/specs/2026-06-02-detection-anchor-crater-design.md`,
`docs/S98_PROMOTION_PROCEDURE.md`.

## §0 — Primer comando
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S99.md
cat docs/S98_ANCHOR_FIX_RESULTS.md   # veredicto + diagnóstico del 19× + estado promoción
```

## §0.5 — Integridad + proceso (vinculante, igual que S97/S98)
- Entorno entrelaza stdout: número/conclusión NUNCA antes del dato; un tool call por
  mensaje si entrelaza; PYTHONIOENCODING=utf-8 para Unicode; pytest con `-s`.
- A61 AUDIT-SPATIAL (ubicación, no número), A62 AUDIT-ADVERSARIAL (insistencia de
  Nicolás = señal), A63 (consolidar no debe revertir fixes). Chrome MCP + TIF en
  ../mirova-tif-archive disponibles.
- A45: tag defensivo + OK Nicolás antes de tocar pipeline/process_*.py, store.py,
  clustering.py, profiles/mirova_equivalent.yaml.

## §1 — Backfill histórico: ✅ COMPLETADO en S98 (no queda nada)
El histórico pre-90d (2026-01-29..2026-03-03) de Tupun/PCC/PP se reprocesó al cráter
(run 26851227816, success) y se promovió a operacional (PR #322, merge_backfill.py).
Verificado público R8: ene-mar det→cráter 1.21/1.26/1.56 km; histórico completo al
cráter. **El dashboard quedó 100% coherente.** S99 arranca directo en §2.

## §2 — TAREA PRINCIPAL S99: el 19× de Tupungatito (magnitud sobre glaciar)
**Diagnóstico ya hecho S98 (NO re-investigar, ver docs/S98_ANCHOR_FIX_RESULTS.md
sección "El 19× de Tupungatito"):**
- Empezó **abril 2026** (marzo era 1.04×, perfecto). MIROVA estable ~0.2 MW.
- Mecanismo: el cluster explota de **2 px (marzo) a 58 px (abril)** por el mosaico
  nieve/roca invernal sobre el glaciar a 5682 m. El **path dNTI contextual** (8
  vecinos) lo lee como anomalía; VRP = SUMA del cluster → ~4 MW (20× MIROVA, que usa
  pico/NTI). Solo Tupungatito (señal débil ~0.2 MW + glaciar de altura + nieve
  estacional). Lascar no sufre (señal fuerte, desierto seco).
- El fix del ancla NO lo toca (cluster en el cráter, pero traga el halo nival).
- Mitigación YA existente: dashboard usa Núcleo F5' (#313, R_core 0.75km) → S95 lo
  calibró ~2.5×. El 19× es el Cluster crudo.

**Plan S99 (brainstorm OBLIGATORIO antes de tocar pipeline — A26/CLAUDE.md):**
1. `superpowers-brainstorming` sobre las vías de fix:
   - Gate del path dNTI contextual cuando t_bg muy frío (A23, fondo glaciar).
   - Cap de n_pixels del cluster en régimen "Muy Bajo".
   - Usar pico NTI en vez de suma del campo (estilo MIROVA).
   - ¿O es suficiente con el Núcleo F5' display y NO tocar el pipeline? (evaluar
     si el problema es solo de Cluster crudo, que casi no se muestra).
2. Papers-first (Coppola 2016a SP426.5 §dNTI, Campus 2024, Coppola 2024) +
   BIBLIOGRAPHY_SYNTHESIS.md ANTES de inventar umbrales.
3. Si se decide tocar pipeline: TDD + A45 (tag + OK) + A/B con profile aislado +
   reproc real (A18) + verificación 3 vistas. Mismo rigor que el fix del ancla S98.
4. Cuidado A55: no meter un gate que el frontend ya hace (verificar Núcleo F5').

## §3 — Otros pendientes (menores)
- Gates intra-radio redundantes (A55, identificados S86) — revisar/remover.
- El "segundo problema" original (selección de cluster por VRP sumado) quedó
  subsumido en §2 (es el mismo fenómeno: composición del cluster sobre glaciar).

## Estado operacional al cierre S98 (no romper)
- Fix del ancla en main (PR #318, commit 588cc8fc): NRT ancla al cráter (vent_lat)
  vía `get_detection_anchor`. Guard anti-revert: `tests/test_detection_anchor.py`.
- Data operacional: 90d (mar-jun) reprocesada al cráter + promovida; ene-mar pendiente
  (§1). Tarjetas muestran distancia al cráter (Tupun 0.4km, PCC 2.1km, PP 0.4km).
- Tags defensivos: pre-s98-detection-anchor, pre-s98-promote-operational.
- Workflow reproc-s98-anchor.yml (artifacts, dispatch-only, timeout 350) reutilizable.
