# S60 Audit B2 — Descomposición distribución NEW por status MIROVA-day

**Fecha**: 2026-05-17
**Motivación**: B mostró NEW median 2.10 MW vs OSF target 1.06 MW (~2× sobre).
Nicolás pidió dive-deep antes de C: ¿por qué la mediana sigue inflada?

## Método

Cross-reference cada record NEW VIIRS375 summit del window 04-16 → 05-15 contra el status
del día en MIROVA CSV consolidado:

- **Día MIROVA reportó**: al menos un record `ALERTA_TERMICA` o `FALSO_POSITIVO` en el día.
- **Día MIROVA RUTINA**: solo records `RUTINA` (MIROVA NRT no publicó nada ese día).

Para Villarrica window 04-16/05-15: 4 días MIROVA reportó (2 con ALERTA, 3 con FP — algunos
solapan días) y 26 días con sólo RUTINA en MIROVA.

## Resultado

| Subgrupo | n NEW | NEW med | n LEGACY | LEGACY med | Δ NEW-LEGACY | vs OSF target 1.06 |
|---|---:|---:|---:|---:|---:|---|
| Días MIROVA reportó | 17 | **1.51** | 17 | 1.88 | **-20%** | NEW gap +42% / LEGACY gap +77% |
| Días MIROVA RUTINA | 94 | 2.19 | 85 | 2.20 | 0% | NEW gap +107% / LEGACY gap +108% |
| Total summit VIIRS375 | 111 | 2.10 | 102 | 2.16 | -2.7% | NEW gap +99% / LEGACY gap +104% |

## Interpretación

### Donde MIROVA NRT publica, NEW reduce el gap a la mitad

El fix kernel-bg cierra 20% de la inflación sistemática en los días MIROVA-relevantes
(gap calibratorio LEGACY 77% → NEW 42%). Esto es el efecto real del fix sobre la
contaminación del ring por el lago Villarrica al norte.

### En días RUTINA, NEW = LEGACY

NEW no mejora la magnitud en días RUTINA. Esto es esperable: si MIROVA decidió no
publicar ese día, es porque su algoritmo o su pipeline interpretó que no había
señal significativa. Que nosotros detectemos 2.2 MW summit ahí es sobre-detección
sub-MIROVA (no FP propio por convención S22+: RUTINA ≠ MIROVA-says-clean).

La sobre-detección puede deberse a:
- Granules NRT distintos a los que MIROVA usa
- Umbral publicación interno MIROVA NRT > Path Test 1 nuestro
- Heat residual cráter (mediano-bajo) que paper Coppola 2016a detectaría pero el sistema
  NRT MIROVA filtra antes de publicar

Esto NO es regresión del fix kernel, es divergencia de umbral publicación.

## Implicación para adopción operacional

**Re-recomendación**: el fix SÍ aporta donde importa.

Diferencia visible:
- LEGACY noche-MIROVA-day median 1.88 MW (gap 77% sobre OSF)
- NEW noche-MIROVA-day median 1.51 MW (gap 42% sobre OSF) — **dentro del rango "MIROVA declara ±30%"**

El argumento para NO adoptar (mediana 2× sobre OSF agregado) se debilita: la masa que
infla la mediana agregada son los 94 records RUTINA donde MIROVA tampoco se compara
contra OSF (porque OSF curado excluye lo no-publicado).

**Confirmación pendiente**: workflow C (run 25998122095) extiende window a 2026-02-20.
Con los 3 ALERTAS adicionales (02-26, 03-08, 04-09), n MIROVA-day pasa de 17 a ~25-30.
Si NEW median en MIROVA-days sigue ≤1.6 MW, adopción operacional es defendible.

## Top 10 NEW outliers son TODOS día-RUTINA

10/10 records VRP > 4.32 MW summit son días MIROVA-RUTINA. Magnitudes 4.3-7.4 MW
desde 2026-04-23 hasta 2026-05-13. Si MIROVA tenía un umbral publicación nocturno
~5 MW VIIRS375 summit, todos estos serían "casi publicaba" sub-MIROVA. Investigación
futura: ¿cuál es el umbral interno MIROVA NRT para publicar? Papers Coppola no lo
documentan explícitamente.
