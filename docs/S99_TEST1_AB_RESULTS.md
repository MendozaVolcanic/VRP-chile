# S99 — Resultados A/B fix magnitud Test 1 (4 candidatos)

Run GH Actions **26864573601** (success, 12 jobs = 4 perfiles × 3 vols, ventana
2026-04-01..05-31, code_ref=main). Artifacts → `experiments/_s99_audit/_ab_art/`.
Auditoría reproducible: `experiments/_s99_audit/ab_test1_audit.py` (vs MIROVA CONS+OCR
latest). Tabla cruda: `ab_test1_summary.txt`.

## Tabla (matched vs MIROVA)
| Volcán | perfil | alertas | recall | ratio mediano | %∈[0.5,2] | z (FN magnitud) |
|---|---|---|---|---|---|---|
| **Tupungatito** | baseline | 63 | 59 | **18.9×** | 11.9 | 4 |
| | pixfilter (A) | 63 | **22** | 0.64× | 68.2 | **41** |
| | **core/espacial (B)** | 63 | **59** | **2.46×** | 23.7 | **4** |
| | eq16 (LL) | 63 | 59 | 18.9× | 11.9 | 4 |
| **Villarrica** (canario) | todos | 6 | 5 | 1.84× | 80.0 | 0 |
| **Lascar** (control) | baseline/core/eq16 | 162 | 126 | 0.85× | 87.3 | 1 |
| | pixfilter | 162 | 124 | 0.85× | 87.1 | 3 |

## Veredicto
- **Candidato B (recorte compacidad espacial) = GANADOR.** Cura Tupungatito
  18.9×→2.46× (reducción mediana al 0.19× del baseline sobre 256 records test1),
  **preservando recall (59/59)** y **sin sumar FN** (z=4 = baseline). Controles
  Lascar/Villarrica sin cambio. Es uniforme (no per-volcán), proxy de la compacidad
  del cluster MIROVA. Residual 2.46× (apenas sobre el target 2.0) — calibrable con
  R_core (0.5 vs 0.75) si se quiere bajar más, validando que no aparezcan FN.
- **Candidato A (pixfilter) = VETADO.** Catastrófico en Tupungatito: recall 59→22 y
  **41 FN de magnitud** (records con pc.vrp=0 donde MIROVA detectó). Confirma el
  hallazgo S33 (-18.6pp recall): el umbral por-píxel duro anula los sub-píxel que el
  Test 1 integrado existe para capturar. Muerto.
- **eq16 (lava lake) = AFUERA (doble).** (1) Drift del clon (per-volcán, MISSION S99).
  (2) Como está cableado (usa t_bg global como fondo) **anula los records sub-píxel**:
  192 records Villarrica → 0.0 MW (FN masivo si hubieran sido los matcheados). Necesita
  la calibración local-bg + T_e que el diseño 2026-05-17 dejó pendiente. Queda en
  beyond-MIROVA (EXT-11), NO operacional.
- **Villarrica NO es un problema de magnitud** en data actual (1.84×, recall 5/6, z=0).
  El "30×" histórico ya no está (fix ancla S98 + refresh S94/S95). Los 5 matcheados son
  path eruption (señal fuerte), no test1 → por eso core/eq16 no los tocan.

## Decisión pendiente (Nicolás + A45)
Adoptar **Candidato B** a `mirova_equivalent` (flip `enable_test1_spatial_core: true`),
con: MISSION 3-preguntas (compacidad = cierra divergencia magnitud, uniforme, NO
per-volcán — pero R_core 0.75 es parámetro elegido, no constante MIROVA → discutir),
brainstorming gate (cambio de `enable_*`), tag A45 + OK, reproc operacional 3 vols +
verificación 3 vistas. Opcional: A/B R_core 0.5 si se quiere 2.46→<2.0.
