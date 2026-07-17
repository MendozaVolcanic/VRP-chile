# AUDIT S121 — A/B ancla honesta MODIS (D12): VEREDICTO = NO ADOPTAR

> Reproc run 29582035729 (profile aislado `_d12_honest_anchor_modis`, 4 vols × 2025-02-15..05-15).
> Análisis `experiments/_s121_d12_ab/analyze.py` (S91). Diseño: `specs/2026-07-17-d12-...`.
> **El operacional NO se tocó** — el flag `enable_honest_anchor_modis` sigue OFF (correcto).

## Hipótesis (refutada)

D12: 429 noches de Láscar con foco crateriano real se pierden porque el pipeline etiqueta
`far` (el hotspot salta al Salar). El fix (ancla honesta MODIS) está cableado pero OFF por
el bloqueo del design 11-jun ("131 records path-D artefacto pc.vrp>5 se destaparían").
**Hipótesis S121**: el gate `first_pass_summit>0` (S111, 16-jun, posterior) ya filtra esos
path-D → se podría activar sin destape.

## Resultado (números del script)

| Vol | far→summit | noches "curadas" (cluster ≤inner) | **destape path-D pc.vrp>5** | máx destape |
|---|---|---|---|---|
| **Láscar** (cura) | 107 | **76** (reales, vol activo) | 7 | 29 MW |
| NevadosDeChillan | 68 | 51 (¿artefacto A69?) | 5 | 20 MW |
| PuyehueCordonCaulle | 66 | 50 | 9 | **117 MW** |
| Tupungatito | 151 | 89 | 20 | 23 MW |

## Por qué la hipótesis falla (mecanismo, caso PCC 117 MW 2025-02-27)

El record destapado: `pc.vrp=117 MW`, `distance_class` far→**summit**, a 2.7 km, **100%
path-D** (`dnti_ctx=130`, bt/nti/eti=0), `final_source=ctx_cluster`. PERO
`n_first_pass_pixels=109` → **el gate first_pass_summit>0 SE CUMPLE**.

La causa raíz: **el path-D contextual (dNTI) ES parte del first-pass**. El gate cuenta
píxeles del first-pass sin distinguir "señal real (BT/NTI/ETI)" de "blob difuso path-D
contextual". Por eso NO filtra el destape de magnitud. El gate S111 protege contra el
artefacto de **POSICIÓN** (A69, cluster near-crater sin señal) pero el destape es de
**MAGNITUD** (blob path-D con VRP inflado) — un problema **ortogonal** que el gate no mira.

Esto **confirma con datos frescos** el bloqueo del design 11-jun §4: el ancla MODIS no se
puede activar sin el fix de magnitud path-D primero. El gate S111 no alcanza.

## Veredicto

**NO ADOPTAR** el ancla honesta MODIS todavía. Criterio pre-registrado violado (el destape
path-D pc.vrp>5 ocurre en los 4 vols; PCC llega a 117 MW). Flag queda OFF.

La cura de Láscar es **real y valiosa** (76 noches de FN recuperadas), pero viene atada al
destape — no son separables por el gate de posición. Confirma A82/A83: a 1 km no hay
discriminante per-record que separe el foco débil real del blob difuso; el path-D
contextual los mezcla.

## Próximo paso (el fix de magnitud, no la posición)

**C2 — ctxpeak port a MODIS** (espejo del fix S100 que curó VIIRS Tupungatito): recalcular
la magnitud del path-D contextual con el pico del kernel en vez del blob integrado. Es el
candidato del design 11-jun §3.3 nunca probado (C1 cap fue refutado §7). Secuencia:
1. A/B propio de C2 (magnitud path-D MODIS): ¿los 41 destapes (7+5+9+20) caen a <5 MW o se
   suprimen, manteniendo la cura de Láscar?
2. Solo si C2 controla la magnitud → re-correr el A/B del ancla (este) con C2 activo.
3. Solo si ambos → adopción con R2/R3/A45.

D12 sigue ABIERTO. El fix es de dos capas (magnitud path-D + ancla posición), no una.
