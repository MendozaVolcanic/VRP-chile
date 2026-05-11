# OSF v2.5 audit findings (S36 Bloque C)

**Fecha**: 2026-05-11
**Source**: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98 MB, 615,470 filas globales,
descargado 2026-04-18). Filtrado output: `reports/osf_v25_tier_a.csv` (8 MB, 48,360 filas).

## TL;DR

OSF v2.5 (MIROVA archive oficial 2000-2025) tiene **~71× más references Tier A** que
el OCR consolidado scraper Mirova-v1. Cambia fundamentalmente nuestra capacidad de auditar.

**Hallazgo más impactante**: Villarrica "recall 0%" era artefacto de data scarce.
Auditábamos sobre 7 refs OCR. OSF tiene **5,211 refs Villarrica**.

## Tabla refs Tier A: OSF v2.5 vs OCR consolidado

| Volcán | OSF v2.5 | OCR (Mirova-v1) | Ratio | Período OSF |
|---|---:|---:|---:|---|
| **Lascar** | **10,028** | 275 | 36× | 2000-02-25 → 2025-12-31 |
| Chaitén | 5,809 | 0¹ | ∞ | 2008-04-09 → 2025-12-29 |
| PCC | 5,488 | 100 | 55× | 2009-02-05 → 2025-12-31 |
| Lastarria | 5,368 | 88 | 61× | 2003-01-22 → 2025-12-31 |
| **Villarrica** | **5,211** | 7 | **744×** | 2000-04-02 → 2025-12-29 |
| NdC | 5,042 | 5 | 1008× | 2000-03-24 → 2025-12-16 |
| Isluga | 4,743 | 86 | 55× | 2012-01-22 → 2025-12-31 |
| Copahue | 4,168 | 1 | 4168× | 2000-04-12 → 2025-12-17 |
| Planchón-Peteroa | 1,762 | 41 | 43× | 2012-01-27 → 2025-12-15 |
| Llaima | 741 | 0¹ | ∞ | 2000-06-23 → 2025-12-13 |
| **Tupungatito** | **0** | 74 | 0 | — (sub-pixel, post-2025) |
| **TOTAL** | **48,360** | ~677 | ~71× | |

¹ Chaitén y Llaima OCR=0 ALERTA porque no han tenido actividad significativa
durante el período scrapeado por Mirova-v1 (2026).

## Estructura OSF v2.5

```
id, timeUTC, IDvolc, Dayflag, Satellite, Resolution, SatZen, SatAzi,
Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP, LAT, LON, Max_Dist,
Volc_Name, Volc_LAT, Volc_LON, class
```

- `Satellite`: 1=MODIS Terra, 2=MODIS Aqua, 3=VIIRS NPP, 4=VIIRS NOAA-20 (confirmar con schema docx)
- `Resolution`: 1000=MODIS 1km, 750=VIIRS M-band, 375=VIIRS I-band
- `class`: **0 = excluido/FP, 1 = real (alerta válida)**
- `Max_Dist`: distancia al pixel active más lejano (km × 10? Lascar 03:35 dist=2281 km¿?
  Probablemente columna escalada distinta, revisar schema)
- `VRP`: in Watts (no MW). E.g. 1,663,711.666 = 1.66 MW

## Distribución class (real vs FP curado)

| Volcán | class=0 (FP curado) | class=1 (real) | % real |
|---|---:|---:|---:|
| Lascar | 838 | 9,190 | 91.6% |
| Chaitén | 99 | 5,710 | 98.3% |
| PCC | 173 | 5,315 | 96.8% |
| Lastarria | 1,105 | 4,263 | 79.4% |
| Villarrica | 228 | 4,983 | 95.6% |
| NdC | 511 | 4,531 | 89.9% |
| Isluga | 930 | 3,813 | 80.4% |
| Copahue | 686 | 3,482 | 83.5% |
| Planchón | 621 | 1,141 | 64.8% |
| **Llaima** | **411** | **330** | **44.5%** ← muchos FPs curados! |
| Tupungatito | 0 | 0 | — |

**Llaima 44.5% real** = 55% son class=0 curados por MIROVA team como FPs.
Eso es consistente con CLAUDE.md "Llaima thermal noise: 139 FPs son ruido térmico
lago Conguillío ~9km NE". OSF confirma que el equipo MIROVA cura activamente
Llaima.

## Cobertura sensor (Tier A)

VIIRS_SNPP_375 domina en mayoría. Confirmación que **MIROVA usa VIIRS I-band
375m operacionalmente desde 2012** (Coppola 2022 Sabancaya).

Top sensor per volcán:
- Lascar: SNPP_375 (3047), MODIS_T (2641), MODIS_A (2408), NOAA20_375 (1720)
- Villarrica: MODIS_T (1339), SNPP_375 (1249), MODIS_A (1215)
- Lastarria: SNPP_375 (3418), NOAA20_375 (1922)

## Implicaciones para audit pipeline

1. **Audits históricos** (pre-2026) → usar OSF v2.5 (48,360 refs, class=1 only)
2. **Audits NRT 2026+** → usar OCR consolidado (continuo)
3. **Tupungatito** → caso especial. No tiene refs OSF v2.5. Auditar contra OCR
   exclusively. Es la confirmación operacional que es sub-pixel difícil.
4. **Villarrica recall** → re-medir con OSF v2.5 baseline. Predicción: ya no
   es 0%, probablemente 60-80% basado en patrón Lascar/Lastarria.

## Próximos pasos sugeridos

1. **Actualizar `experiments/80_h8_apples_to_apples.py`** para soportar OSF
   v2.5 + OCR consolidado como fuentes alternativas (flag CLI)
2. **Re-correr A/B H8** con OSF como ground truth (período 2025-12 vs nuestros
   records mirova_equivalent del mismo período)
3. **Investigar Llaima 411 FPs curados** — ¿son geográficos (lago Conguillío)
   o temporales? Si geográficos, valida nuestros exclude_zones (que removimos
   en S27 metodología literal MIROVA)
4. **Tupungatito**: aceptar como caso documented "OSF=0 / NRT=ALERTA". Es
   límite arquitectural conocido del MIR.

## Archivos generados

- `experiments/82_osf_v25_audit.py` — script de auditoría replicable
- `reports/osf_v25_tier_a.csv` — 48,360 filas filtradas Tier A (8 MB)
- `reports/osf_v25_findings.md` — este documento
