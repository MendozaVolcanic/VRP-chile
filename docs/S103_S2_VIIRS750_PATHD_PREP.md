# S103 — Prep §2 path D: verificación A48 del residuo glaciar VIIRS750

**Fecha**: 2026-06-07 · Read-only, sobre data pre-promoción (el path de disparo NO
cambia con nadir; nadir solo escala magnitud). Hecho mientras corría el reproc
nadir VIIRS (run 27098410956), sin interferir.

## Pregunta (A48)
El agente S102 recomendó "portar ctxpeak a VIIRS750" afirmando que el residuo
glaciar de Tupun/PP/Isluga "dispara por Test1 sub-píxel (NO path D contextual),
cap D9 no lo toca". El arranque marcó **verificar con datos antes de implementar**
(A48: el agente pudo inventar la heurística).

## Verificación de código
- **ctxpeak (`ENABLE_TEST1_CONTEXTUAL_FILTER` + `_KEEP_PEAK`, `apply_contextual_test1_filter`)
  está SOLO en `process_viirs.py` (VIIRS375)** — líneas 140-145, 1451-1462.
- **AUSENTE en `process_viirs_mod.py` (VIIRS750)** (0 matches) **y en `process_modis.py`** (0).
- ⇒ "Portar ctxpeak a VIIRS750" es una palanca REAL y no-hecha. (Confirmado.)

## Verificación de datos (VIIRS750, pc.vrp>0, ventana 2026-01-29..06-07)
| Vol | n | source=test1 | triggered_test1 | source=eruption | d9_capped | ctx-only (BT=NTI=ETI=0) | t_bg<270K |
|---|---|---|---|---|---|---|---|
| Tupungatito | 81 | 55 (68%) | 57 (70%) | 25 (31%) | 28 (35%) | 63 (78%) | 81/81 |
| PlanchonPeteroa | 102 | 88 (86%) | 90 (88%) | 13 (13%) | 10 (10%) | 47 (46%) | 41/102 |
| Isluga | 150 | 79 (53%) | 99 (66%) | 70 (47%) | 22 (15%) | 72 (48%) | 142/150 |

## Conclusión (matiza al agente)
1. **CONFIRMADO el núcleo**: Test1 es la fuente dominante (53-86%), mismo mecanismo
   que ctxpeak curó en VIIRS375 (S100: el Test1 integrado suma el anillo nival frío
   → infla). Portar ctxpeak a VIIRS750 atacará la mayoría del residuo.
2. **NO es Test1 puro** (el agente sobre-simplificó): hay fracción 'eruption'-source
   (Tupun 31%, Isluga 47%) que ctxpeak NO toca, y co-firing de path D contextual alto
   (46-78% contextual-only). El **D9 cap YA toca 15-35%** (Tupun: los 81 con t_bg<270K)
   — contradice el "cap D9 no lo toca". Ctxpeak ayudará pero **no resolverá todo**.
3. ⇒ §2 NO es un único fix. Plan sugerido: (a) portar ctxpeak a VIIRS750 (espejo
   VIIRS375, keep-peak preserva cat-b) para el grueso Test1; (b) re-medir el residuo
   'eruption'-source + contextual restante; (c) recién entonces decidir si el D9 cap
   o algo más cubre la cola. Brainstorming + A45 + re-medir DESPUÉS de la promoción
   nadir VIIRS (la magnitud baseline cambia ~0.80×).

## Caveat de secuencia
Re-medir VIIRS750 **después** de promover nadir VIIRS (§1). El A/B noctx S102 mostró
que nadir solo baja Tupun VIIRS750 19→16.6 (modesto: el driver es la suma Test1, no
el área) → el grueso lo cortaría ctxpeak, no nadir. El path de disparo (esta tabla)
es estable a nadir; las magnitudes/ratios no.
