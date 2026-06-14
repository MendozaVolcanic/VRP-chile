# AUDIT_S108 — Estado global del clon vs MIROVA (post nadir + ancla V375/V750)

**Fuente**: `experiments/_s94_audit/per_sensor_metrics.py` (S94, loader corregido) sobre
data actual (2026-06-14). Match temporal ±60min, universo CONS∪OCR. Flips ya aplicados:
nadir MODIS (S102) + nadir VIIRS (S103) + ancla honesta V375 (S106) + V750 (S108).
**MODIS sin ancla (flip OFF) — gateado por el A/B §2 en curso.**

## Vista A — CRUDO (¿vimos algo esa noche?, cualquier dist, pc.vrp>0)
| Sensor | N_ours | N_mir | Precision | Recall | Ratio_med |
|---|---|---|---|---|---|
| MODIS | 3153 | 83 | 2.5% | **96.4%** | 0.92× |
| VIIRS375 | 4707 | 762 | 35.6% | 96.2% | 0.52× |
| VIIRS750 | 1709 | 191 | 17.2% | 86.9% | 0.55× |

## Vista B — SUMMIT-GATED (lo que el dashboard muestra)
| Sensor | N_ours | N_mir | Precision | Recall | Ratio_med |
|---|---|---|---|---|---|
| MODIS | 359 | 83 | 2.5% | **10.8%** | 0.80× |
| VIIRS375 | 4664 | 762 | 35.8% | 96.2% | 0.52× |
| VIIRS750 | 1544 | 191 | 18.6% | 86.4% | 0.54× |

## Hallazgo prioritario: el gap más grande es MODIS summit-gated (D12)
MODIS recall **colapsa de 96.4% (crudo) a 10.8% (summit-gated)**. Mecanismo = D12/A68:
el cluster MODIS está al cráter (lo detectamos, recall crudo 96%), pero el píxel suelto
más caliente cae lejos (Salar/halo) → `distance_class=far` → el gate `mirovaEqVrp` lo
anula → no cuenta como summit. **El flip ancla MODIS (`enable_honest_anchor_modis`)
recupera esos far→summit → subiría el recall summit-gated MODIS de 10.8% a ~96%.**
Es el espejo exacto de lo que el ancla ya hizo en V375/V750. **Confirma que el A/B MODIS
§2 + su flip es el frente de MAYOR impacto del proyecto ahora.** (El flip está gateado por
el fix de magnitud §2 para no destapar los 121 inflados como artefacto — ver PREVERDICT_NOTES.)

## Otros frentes (secundarios)
- **Sub-estimación de magnitud VIIRS**: ratio_med 0.52× (V375) / 0.54× (V750). Dentro de
  paridad (0.5–2.0) pero en el borde bajo. (Nota: S103 R3 reportó 0.78× post-nadir; la
  diferencia con 0.52× puede ser de método de medición — verificar antes de accionar, A62.)
- **MODIS precision 2.5%** (sobre-detección): N_ours crudo 3153 vs N_mir 83. MIROVA casi
  no publica MODIS (83, mayoría Lascar). El grueso de nuestros MODIS son cat-b real no
  publicada (A54, 95% física real S86) o cat-d artefacto. El gate summit del frontend ya
  reduce a 359. No es bug del pipeline (A54) — es la diferencia de umbral de publicación.
- **VIIRS375/750 recall 86–96%** ya sólido; los ~25 FN VIIRS750 = señal sub-pixel tiny.

## Implicación para las 6h
1. El A/B MODIS (en curso) es lo más impactante: su veredicto + flip cura el gap MODIS.
2. Riesgo A54 del flip MODIS DESCARTADO (PREVERDICT: no hay foco MODIS-MIROVA salvo Lascar).
3. Frente magnitud VIIRS (0.52×) = candidato siguiente, pero verificar método primero.
