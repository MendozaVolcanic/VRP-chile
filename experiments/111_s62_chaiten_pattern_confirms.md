# S62 Chaiten Pattern Confirmation — gap 10.28× es mismo mecanismo Villarrica/PP

**Fecha**: 2026-05-19 (S62 paralelo mientras corren workflows)

## Hallazgo

Chaiten muestra patrón térmico **idéntico** a Villarrica, PlanchonPeteroa, Lastarria:

| Métrica | Chaiten | Villarrica (pre-fix) | Lastarria | PlanchonPeteroa |
|---|---:|---:|---:|---:|
| ΔT mediano | **10.5K** | 11.3K | 12.6K | ~11K |
| t_bg_k mediano | 270.4K | 273.1K | 264.3K | similar |
| pc.n_pixels mediano | 42 | 49 | 37 | similar |
| Gap LEGACY/MIROVA | **10.28×** | 15× | 7.67× | 9.09× |

**Mecanismo confirmado**: régimen Muy Bajo (ΔT ~10-12K) + ring background frío → Test 1 integrated-ROI suma pixels marginales → magnitud inflada.

## Top outlier Chaiten

| Fecha | Sensor | MIROVA VRP | Nuestro pc.vrp | Ratio |
|---|---|---:|---:|---:|
| 2026-04-07 04:54 | VIIRS_NOAA20 | 0.08 | 9.20 | **115×** |
| 2026-04-13 05:30 | VIIRS_NOAA21 | 0.07 | 3.25 | 46× |
| 2026-03-05 05:12 | VIIRS_NOAA20 | 0.08 | 3.19 | 40× |
| 2026-03-08 06:00 | VIIRS_NOAA20 | 0.23 | 8.92 | 39× |

BT mean pixels 275-283K (frío, régimen Muy Bajo claro). Ring bosque húmedo Patagónico = frío nocturno → ΔL inflado.

## Implicación S63

Chaiten también necesita `local_kernel_bg: true`. **5 vols Tier A con mismo patrón térmico**:
- Villarrica ✅ adoptado S61
- PlanchonPeteroa ✅ adoptado S61
- Lastarria → A/B corriendo S62
- Tupungatito → A/B corriendo S62
- **Chaiten → A/B pendiente S63**

Cuando workflows S62 terminen y validen Lastarria/Tupungatito, replicar para Chaiten:
1. Crear `.github/workflows/reproc-ab-chaiten.yml` (clon de A/B Lastarria+Tup)
2. Disparar ~3h
3. Audit + adopción si valida

## Sobre kernel_size=5 (decisión S63)

Análisis offline sugiere kernel_size=5 NO ayudaría significativamente para vols
con contaminación de ring lejano (lago Villarrica a 15-18km del cráter):
- VIIRS-I 375m → kernel 5×5 = ~1.9×1.9 km
- Lago Villarrica norte centro a 15-18 km del cráter → fuera del kernel 5
- Probable kernel=3 ya captura el contraste local correctamente

Hipótesis alternativa S63+:
- Tunear `k_sigma` (3.0 → 5.0 para summit Coppola 2016a Tabla 1)
- Pero afectaría también Lascar/Isluga (calibrados) → riesgo regresión

**Recomendación**: NO investigar kernel_size=5 ni k_sigma tuning como prioridad
S63. Focus en aplicar kernel-bg sistemáticamente a los 5 vols con patrón
térmico Muy Bajo. Resto refinements son S64+.

## Resumen actualizado por vol Tier A

| Vol | Régimen | Estado fix | Calibración |
|---|---|---|---:|
| **Lascar** | ΔT 22K (Bajo-Medio) | sin fix necesario | 1.32× ✓ |
| **Isluga** | ΔT ~20K | sin fix necesario | 1.11× ✓ |
| **Copahue** | Muy Bajo (n=1, poca data) | sin fix (calibrado 1.14×) | 3.18× (n=1) |
| **Llaima** | Muy Bajo (n=3, poca data) | sin fix (1.01× calibrado) | 8.97× (n bajo) |
| **Villarrica** | Muy Bajo ΔT 10.6K | ✅ fix adoptado S61 | 2.16× |
| **PlanchonPeteroa** | Muy Bajo | ✅ fix adoptado S61 | 2.84× |
| **Lastarria** | Muy Bajo ΔT 12.6K | A/B S62 corriendo | LEGACY 7.67× |
| **Tupungatito** | Muy Bajo | A/B S62 corriendo | LEGACY 8.20× |
| **Chaiten** | Muy Bajo ΔT 10.5K | A/B pendiente S63 | LEGACY 10.28× |
| **PCC** | Muy Bajo | inner=7 S62 + kernel-bg eval | LEGACY 3.51× |
| **NevadosDeChillan** | sin data | sin decisión | - |
