# S93 — Validación detección diurna MODIS: VEREDICTO FIRME (inviable en mayo)

**Cierra pendiente 2.1 de `BLOQUE_ARRANQUE_S93.md`.** Fuente de verdad reproducible:
`solar_check.py` (correr → stdout). Sin transcripción manual (§0.5).

## Pregunta
¿Existe ≥1 ventana (volcán+fecha) con ALERTA MIROVA confirmada **diurna**
(elevación solar > 0°) en algún Tier A, con TIF disponible, para hacer R2
pixel-level de la detección diurna MODIS?

## Datos
- Universo: `latest_consolidado.csv` (CONS) + `data/mirova_reference/registro_vrp_ocr.csv` (OCR).
- Rango: 2026-05-09 → 2026-05-30. Tier A (11 vols, mirova_monitored).
- TIF MIROVA (`../mirova-tif-archive/data/tif/`): cubre **2026-05-09 → 2026-05-20**.
- Elevación solar: fórmula NOAA en `solar_check.py` (sin deps externas).

## Resultado (verificado)
| Métrica | Valor |
|---|---|
| Alertas Tier A VRP>0 (05-09 → 05-30) | 195 (CONS 195, OCR 0) |
| Diurnas (elev>0) | **2** |
| Nocturnas | 193 |
| Alertas en ventana-con-TIF (05-09 → 05-20) | 107 |
| **Diurnas en ventana-con-TIF** | **0** |

Las 2 únicas diurnas de todo mayo:
- Villarrica 2026-05-29 19:55 UTC, MODIS, VRP 1.83 MW, elev +14.5° → **sin TIF** (fuera ventana).
- Chaitén 2026-05-28 20:55 UTC, MODIS, VRP 0.74 MW, elev +4.2° (crepúsculo) → **sin TIF**.

Sanity check: pasadas UTC 04-08 (las más densas, ~190 filas) dan elev solar
**−84° a −42°** = noche profunda (madrugada local Chile UTC-4). Confirma signo correcto.

## Por qué (físico)
MIROVA, como VRP Chile, privilegia la pasada **nocturna** para el MIR ~3.9 µm
(la radiación solar reflejada contamina de día). Por eso 99% de las alertas
confirmadas son de la pasada de madrugada local. Las escasas detecciones diurnas
son señales débiles del atardecer — solo 2 en 22 días, ambas <2 MW.

## Veredicto
**R2 pixel-level inviable en mayo**: 0 casos (alerta diurna confirmada) ∩ (TIF).
Detección diurna MODIS = **inocua pero sin beneficio demostrable** (extiende S92,
que solo miró NdC). `enable_daytime_modis` sigue **OFF**. NO adoptar.
Para un veredicto positivo futuro haría falta una ventana con erupción/actividad
fuerte diurna confirmada por MIROVA + TIF — no la hubo en este período.

## Nota metodológica (A48 + §0.5)
El subagente Explore inicial reportó "83 ventanas diurnas disponibles" con
elevación +25°/+55° para pasadas UTC 05-08 — **error: signo de elevación solar
invertido** (clasificó madrugada local como diurna). Detectado por contradicción
con la física + S92; rehecho con cálculo propio verificable. Los subagentes no son
fuente-de-verdad metodológica para valores numéricos.
