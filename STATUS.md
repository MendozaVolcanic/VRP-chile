# STATUS — VRP Chile

## Estado actual (2026-04-04)
Pipeline operativo con GitHub Actions (cada 6h). Formula VRP **corregida** al metodo Wooster MIR radiance (Coppola 2015). Frontend desplegado en GitHub Pages.

## Arquitectura
```
scripts/run_pipeline.py   → Entry point CLI
pipeline/fetch.py         → Download granulos NASA Earthdata (earthaccess)
pipeline/process_modis.py → MODIS Terra/Aqua Band 21/22 (1km, 3.93µm)
pipeline/process_viirs.py → VIIRS I-band I04/I05 (375m, 3.74µm/11.45µm)
pipeline/process_viirs_mod.py → VIIRS M-band M13 (750m, 4.05µm)
pipeline/store.py         → JSON persistence (data/*.json)
frontend/index.html       → Dashboard MIROVA-style (Chart.js)
.github/workflows/nrt.yml → GitHub Actions NRT pipeline
volcanoes.yaml            → Configuracion volcanes
```

## Formula VRP (CORREGIDA)

### Canal MIR (MODIS, VIIRS I04, VIIRS M13)
**Metodo Wooster** (Coppola et al. 2015, Eq.7):
```
VRP = 18.9 × A_pix × ΔL_MIR
```
Donde:
- `ΔL_MIR = L_MIR,hot - L_MIR,bg` (radiancia espectral excedente, W/m²/sr/µm)
- `L_MIR` se calcula via funcion de Planck: `L = C1 / (λ⁵ × (exp(C2/(λ×T)) - 1))`
- `18.9` = coeficiente empirico Wooster para banda ~4µm
- `A_pix` = area del pixel (m²)

**Equivalencia Campus 2022**: `VRP = 1.97×10⁷ × ΔL_MIR × A_pix(km²)`

### Canal TIR (VIIRS I05, 11.45µm) — TIRVolcH
**Metodo Stefan-Boltzmann** (Aveni et al. 2024):
```
VRP_TIR = A_pix × σ × (T_alert⁴ - T_bg⁴)
```
Este metodo SI es correcto para TIR porque la emision termica a 11µm integra la mayor parte del espectro de cuerpo negro a temperaturas volcanicas.

## Auditoria de papers (hallazgos clave)

### Coppola 2015 (MIROVA core)
- MIROVA usa NTI (Normalized Thermal Index) y ETI (Enhanced Thermal Index) para deteccion
- Umbral contextual: C2 desviaciones estandar (5-15σ segun dia/noche y ROI)
- Filtrado espacial via dNTI/dETI (pixel vs media de 8 vecinos)
- Background = media aritmetica de pixeles circundantes
- ROI1 = 5×5 km, ROI2 = 50×50 km

### Campus 2022 (MODIS→VIIRS)
- Formula: `VRP = 1.97×10⁷ × ΔL_MIR × A_pix(km²)`
- Validacion cruzada MODIS/VIIRS muestra consistencia
- VIIRS 750m es el sensor principal para continuidad post-MODIS

### Aveni 2024 (TIRVolcH)
- 16 tests jerarquicos en cascada para VIIRS I5 (TIR)
- Umbral minimo ΔT = 0.5K sobre background
- Usa escenas de referencia mensuales (REF) y residuales (RES = OBS - REF)
- Umbrales adaptativos basados en percentil 99.5 de residuales
- Stefan-Boltzmann correcto para TIR (no para MIR)

### Coppola 2023 (base de datos MIROVA)
- Datos de volcanes chilenos incluidos
- Coeficientes c_rad basados en composicion del magma

## Bug critico corregido: formula VRP

**Problema**: Nuestro codigo usaba Stefan-Boltzmann `VRP = A × σ × (T⁴ - Tbg⁴)` para canales MIR.
**Impacto**: VRP sobreestimado ~100x vs MIROVA para señales debiles.
**Causa raiz**: Stefan-Boltzmann integra TODO el espectro electromagnetico. A ~290K, la potencia total emitida es enorme, pero el sensor MIR solo ve una ventana estrecha (~4µm). Wooster calibro el coeficiente 18.9 empiricamente para dar potencia radiativa real desde la radiancia espectral MIR.
**Fix aplicado**: Reemplazado en process_modis.py, process_viirs.py, process_viirs_mod.py (2026-04-04).

## Sensores procesados

| Sensor | Producto | Banda | Resolucion | A_pix (m²) |
|--------|----------|-------|------------|------------|
| MODIS Terra | MOD021KM | 21/22 (3.93µm) | 1km | 1,000,000 |
| MODIS Aqua | MYD021KM | 21/22 (3.93µm) | 1km | 1,000,000 |
| VIIRS SNPP 375m | VNP02IMG | I04 (3.74µm) | 375m | 140,625 |
| VIIRS NOAA20 375m | VJ102IMG | I04 (3.74µm) | 375m | 140,625 |
| VIIRS SNPP 750m | VNP02MOD | M13 (4.05µm) | 750m | 562,500 |
| VIIRS NOAA20 750m | VJ102MOD | M13 (4.05µm) | 750m | 562,500 |

## Escala de energia MIROVA
- <1 MW: Muy Bajo
- 1-10 MW: Bajo
- 10-100 MW: Moderado
- 100-1000 MW: Alto
- >1000 MW: Muy Alto

## Volcanes configurados
1. Puyehue-Cordon Caulle (radio 15km, vent tracking)
2. Villarrica (radio 30km)
3. Lascar (radio 30km)
4. Copahue (radio 30km)

## Infraestructura
- GitHub Actions: cron cada 6h (00, 06, 12, 18 UTC)
- GitHub Pages: frontend desplegado automaticamente
- NASA Earthdata: credenciales en GitHub Secrets
- Datos MIROVA referencia: data/mirova/*.json (overlay en dashboard)

## Limitaciones conocidas
1. **Sin cloud masking**: MIROVA usa NTI/ETI, nosotros no filtramos nubes
2. **Coordenadas vent aproximadas**: Cordon Caulle vent (-40.585, -72.020) necesita refinamiento
3. **Deteccion simple vs MIROVA**: Usamos threshold fijo (5K + 3σ), MIROVA usa NTI/ETI contextual
4. **Sin correccion por angulo de vista**: Pixel area asumida constante (nadir)
5. **MODIS no detecta señales debiles**: 1km demasiado grueso para fumarolas

## Proximos pasos
1. **Re-ejecutar pipeline** con formula corregida y validar vs MIROVA CSV
2. **Implementar NTI/ETI** para deteccion mas robusta (Coppola 2015)
3. **Cloud masking** basico usando NTI o datos auxiliares
4. **Refinar coordenadas vent** Cordon Caulle via tracking multi-pasada
5. **Expandir a 43 volcanes** (Copernicus-v1)
