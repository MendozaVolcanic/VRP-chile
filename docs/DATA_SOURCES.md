# Data Sources — VRP Chile S17 2026-04-23

> Inventario de fuentes de datos (satélites, archivos, APIs, repos de código).
> Mantener cuando agreguemos/removamos fuentes.

## 1. Productos satelitales (NASA CMR + LAADS)

### MODIS — Terra (lanzado Dic 1999) y Aqua (Mayo 2002)

| Producto | Short name | Version | Resolución | Banda clave | Uso |
|---|---|---|---|---|---|
| Terra L1B Radiances | `MOD021KM` | 6.1 | 1 km | B21/22 (3.959 μm MIR), B31 (11 μm TIR) | VRP MIR + NTI |
| Terra Geolocation | `MOD03` | 6.1 | 1 km | lat/lon/solar zen | pixel-geo |
| Aqua L1B Radiances | `MYD021KM` | 6.1 | 1 km | B21/22, B31 | VRP MIR |
| Aqua Geolocation | `MYD03` | 6.1 | 1 km | lat/lon | pixel-geo |
| NRT Terra L1B | `MOD021KM_NRT` | 61 | 1 km | idem | fallback <3h latencia |
| NRT Terra GEO | `MOD03_NRT` | 61 | 1 km | — | pair NRT |
| NRT Aqua L1B | `MYD021KM_NRT` | 61 | — | — | idem |
| NRT Aqua GEO | `MYD03_NRT` | 61 | — | — | — |

**Notas**:
- MODIS **fin de vida útil declarado hasta 2026** (Campus 2022). Después pipeline debe correr VIIRS-only.
- MODIS **NRT eliminado ~7-14 días**. Standard tiene lag 3-5 días.
- **pyhdf roto en Windows** — MODIS solo corre en GitHub Actions Linux.

### VIIRS I-band (375m) — Suomi-NPP (2011) y NOAA-20 (2017), NOAA-21 (2022, pendiente)

| Producto | Short name | Version | Resolución | Banda clave | Uso |
|---|---|---|---|---|---|
| SNPP L1B IMG | `VNP02IMG` | 2 | 375 m | I04 (3.74 μm MIR), I05 (11.45 μm TIR) | VRP MIR + TIR |
| SNPP GEO IMG | `VNP03IMG` | 2 | 375 m | lat/lon | pair |
| NOAA-20 L1B IMG | `VJ102IMG` | 2.1, 2, 1 | 375 m | I04, I05 | VRP |
| NOAA-20 GEO IMG | `VJ103IMG` | 2.1, 2, 1 | 375 m | — | — |
| NRT SNPP | `VNP02IMG_NRT`, `VNP03IMG_NRT` | 2 | — | — | fallback |
| NRT NOAA-20 | `VJ102IMG_NRT`, `VJ103IMG_NRT` | 2.1, 2 | — | — | — |
| **NOAA-21 L1B IMG (gap)** | **`VJ202IMG`** | **2.1** | **375 m** | **I04, I05** | **PENDIENTE S18** |
| **NOAA-21 GEO IMG (gap)** | **`VJ203IMG`** | **2.1** | — | — | **PENDIENTE S18** |
| **NOAA-21 NRT (gap)** | **`VJ202IMG_NRT`, `VJ203IMG_NRT`** | **2.1** | — | — | **PENDIENTE S18** |

### VIIRS M-band (750m) — mismas plataformas

| Producto | Short name | Version | Resolución | Banda | Uso |
|---|---|---|---|---|---|
| SNPP L1B MOD | `VNP02MOD` | 2 | 750 m | M13 (4.05 μm MIR), M15 (10.76 μm TIR) | VRP MIR |
| SNPP GEO MOD | `VNP03MOD` | 2 | — | — | — |
| NOAA-20 L1B MOD | `VJ102MOD` | 2.1, 2, 1 | 750 m | M13, M15 | VRP |
| NOAA-20 GEO MOD | `VJ103MOD` | 2.1, 2, 1 | 750 m | — | — |
| NRT versiones | sufijo `_NRT` | — | — | — | fallback |
| **NOAA-21 L1B MOD (gap)** | **`VJ202MOD`, `VJ203MOD`** | **2.1** | **750 m** | **M13, M15** | **PENDIENTE S18** |

**Notas**:
- Convención CSV MIROVA: `Sensor: VIIRS` = **VIIRS750 M-band**; `Sensor: VIIRS375` = I-band 375m.
- NOAA-21 disponible en CMR desde enero 2023. Documentado por **JPSS VIIRS Radiometric Calibration ATBD Rev C** (`documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf`).

### Autenticación

- **Credenciales Earthdata**: `~/_netrc` en Windows (machine urs.earthdata.nasa.gov). Fallback a env vars `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD`.
- **`earthaccess.login(strategy="environment")`** — ver [fetch.py:75](../pipeline/fetch.py#L75). También funciona con strategy="netrc".

---

## 2. Ground truth — archivos MIROVA

### OSF v2.5 (archivo local, histórico)

- **URL**: https://osf.io/zm62w/ (link oficial del paper Coppola 2023)
- **Cita**: Coppola et al. 2023 Front Earth Sci 11:1240107.
- **Versión publicada en paper**: v1.0 MODIS-only 2000-2019.
- **Versión local nuestra**: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` — etiquetada v2.5, 615k filas globales, 48k chilenas 2000-2025. **No documentada formalmente** en paper.
- **Supervisión humana**: filtrado manual post-algoritmo confirmado (Coppola 2023 p.4 §2.5).
- **Uso**: ground truth calibración empírica (S14 error ≤0.17% vs coeficientes Wooster).

### NRT CSV scraper (archivo operacional)

- **Archivo (S18)**: `21_04_2026 registro_vrp_consolidado.csv` (13.7k filas, 3.5 meses, ~100% MODIS / ~80% VIIRS).
- **Archivo (S19 actualizado)**: `registro_vrp_consolidado_25_04_2026.csv` (14.1k filas, +5 días).
- **Fuente**: `https://www.mirovaweb.it/NRT/latest.php` — scrape con `MendozaVolcanic/Mirova-v1`.
- **Columnas clave**: `Fecha_Satelite_UTC`, `Fecha_Captura_Chile`, `Volcan`, `Sensor` (MODIS / VIIRS / VIIRS375), `VRP_MW`, `Distancia_km`, `Tipo_Registro`.
- **Uso**: ground truth operacional NRT bajo objetivo (1) clon MIROVA.
- **Cobertura por sensor (S19 verificado)**: ~100% MODIS, ~70% VIIRS. El restante 30% VIIRS solo aparece en imágenes (Latest10NTI/Dist/logVRP/VRP) pero no en latest.php.

### IMPORTANTE — Truncamiento VRP en imágenes MIROVA (S19 2026-04-25)

Las imágenes publicadas en mirovaweb.it muestran **VRP truncado por `floor()`** (parte entera, no redondeo). Verificación empírica S19 contra CSV Lascar MODIS:

| Fecha | VRP en CSV | VRP visible en imagen Latest Images |
|---|---|---|
| 2026-04-25 07:35 | **1.28** MW | "1 MW" |
| 2026-04-25 01:30 | **1.6** MW | "1 MW" |
| 2026-04-23 01:50 | **1.7** MW | "1 MW" |

Si fuera redondeo, 1.6 y 1.7 → "2 MW". Como muestran "1", es **floor**.

**Reglas para comparaciones**:
- **Magnitud VRP exacta** → SOLO el CSV.
- **Presencia/ausencia** → imagen `VRP =NaN MW` confiable.
- **Distribución espacial (distancia/dirección)** → imágenes `Dist`/`Latest10NTI` válidas — esos puntos son reales.
- **Categoría de alerta** (Low/Moderate/High/Very High/Extreme) → imágenes `logVRP` válidas, posición sobre eje Y correcta.
- **Tendencia temporal** → series Last Month / Last Year posiciones correctas, solo el label numérico truncado.

---

## 3. Código open-source térmico

### Oficial MIROVA (Coppola/INGV/UNITO)

**NO EXISTE código público.** Verificado exhaustivamente S17:
- GitHub INGV: 71 repos, 0 térmicos volcánicos.
- UNITO-LGS: sin organización GitHub.
- Coppola/Laiolo/Campus/Massimetti: sin repos personales relevantes.
- Contacto oficial: diego.coppola@unito.it.

**La única vía pública de MIROVA es mirovaweb.it + OSF zm62w (data).**

### Tercero relevante

| Tool | Repo/URL | Licencia | Aplicación |
|---|---|---|---|
| **MOUNTS** (Valade) | https://github.com/sebastienValade/mounts | — | Python + ESA SNAP, implementa **Massimetti 2020 SWIR**. Única reimplementación pública cercana a MIROVA. Útil solo para Fase SWIR futura. |
| MODVOLC (Wright 2004) | http://modis.higp.hawaii.edu/algorithm.html | — | Web download ASCII/FTP. Sin GitHub. BT21-BT32>umbral. |
| HOTMAP (Murphy 2016) | — | — | Sin GitHub. Beta ESA G-POD. Landsat-8/Sentinel-2. |
| TIRVolcH (Aveni 2024) | — | — | MATLAB no publicado. Disponible "on request" a S. Aveni. |
| NHI tool | https://sites.google.com/view/nhi-tool | GEE app | Alternativa Sentinel-2/Landsat-8. |
| FastVRP (Silvestri 2023) | Google Colab | — | INGV. SLSTR L2 FRP. |

### APIs externas útiles

| API | URL | Uso |
|---|---|---|
| **NASA FIRMS Active Fire** | https://firms.modaps.eosdis.nasa.gov/api/ | Referencia externa independiente. MAP_KEY gratuito, 5000 req/10min. CSV/JSON/SHP. |
| NASA LAADS DAAC | https://ladsweb.modaps.eosdis.nasa.gov/ | Product pages oficiales NASA VIIRS/MODIS L1B (DOIs formales). |
| NOAA STAR JPSS | https://www.star.nesdis.noaa.gov/jpss/ | ATBDs oficiales VIIRS (descargados S17). |

---

## 4. Documentación NASA (soporte)

| Documento | Path local | Rol |
|---|---|---|
| JPSS VIIRS Radiometric ATBD Rev C | `documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf` | Respalda VJ202 (NOAA-21) |
| JPSS VIIRS Imagery ATBD Rev E | `documentacion/JPSS_ATBD_VIIRS_Imagery_RevE.pdf` | Suplementario |
| VIIRS L1B User Guide Aug 2021 | `documentacion/VIIRS_L1B_UserGuide_Aug2021.pdf` | Uso operacional |
| VIIRS RadCal ATBD 2014 | `documentacion/VIIRS_RadCal_ATBD_2014.pdf` | Histórico |
| VIIRS Geolocation ATBD 2014 | `documentacion/VIIRS_Geolocation_ATBD_2014.pdf` | Histórico |
| MODIS L1B ATBD C7 | `documentacion/MODIS_L1B_ATBD_C7.pdf` | MODIS Collection 7 |
| MODIS L1B User Guide C7 | `documentacion/MODIS_L1B_UserGuide_C7.pdf` | Operacional |
| MCDWD User Guide | `documentacion/MCDWD_UserGuide_RevC.pdf` | Cloud-water mask (no usado actualmente, gap) |

---

## 5. Repos propios del proyecto

| Repo | URL | Rol |
|---|---|---|
| VRP Chile | https://github.com/MendozaVolcanic/VRP-chile | Pipeline NRT propio |
| Mirova-v1 | https://github.com/MendozaVolcanic/Mirova-v1 | Scraper mirovaweb.it (consume latest.php + OCR Latest10NTI.png) |

---

## Pendientes de agregar

- [ ] Cuando se integre NOAA-21 a fetch.py, agregar link al LAADS DAAC page para VJ202IMG.
- [ ] Cuando se integre SWIR (Massimetti 2020), documentar fuentes Copernicus Open Hub (Sentinel-2 MSI) y USGS EarthExplorer (Landsat-8/9 OLI).
- [ ] Cuando se consolide MIROVA NRT vs OSF v2.5 discrepancias, documentar protocolo de comparación.
