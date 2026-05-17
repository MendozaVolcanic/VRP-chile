# Inventario Excels/CSVs/XLSX del proyecto VRP Chile

> Creado S57 (2026-05-17) tras Nicolás señalar que olvidé archivos Excel/CSVs.
> Búsqueda exhaustiva en `VRP Chile/` y subdirectorios.
>
> **Hallazgo principal**: NO existen archivos `.xlsx` ni `.xls` en el repo (0 encontrados).
> Toda la data tabular vive en `.csv`. Hay, sin embargo, varios CSV con
> información operacional / científica relevante que NO he estado citando
> en sesiones recientes.

## Resumen ejecutivo

| Archivo | Filas | Propósito | ¿Lo estaba usando? |
|---|---|---|---|
| `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` | 615,470 | **OSF v2.5 archivo global MIROVA** (10 volcanes chilenos, 48,360 refs 2001–2025) | A medias — citado pero no leído en S47–S56 |
| `10.04.2026 registro_vrp_ocr.csv` | 281 | OCR mirovaweb early snapshot + validación humana | NO |
| `14042026 registro_vrp_ocr.csv` | 301 | OCR mirovaweb (snapshot S12 baseline) + validación humana | NO |
| `registro_vrp_consolidado_25_04_2026.csv` | 14,138 | Snapshot consolidado intermedio entre S15 (21_04) y `01_05_2026` | NO |
| `Historial_Puyehue_Cordon_Caulle.csv` | 94 | Historial curado PCC (incluye `Origen_Dato`) | NO |
| `data/mirova_reference/mirova_v1_snapshot/registro_Chaiten.csv` | 22 | Per-volcán Chaitén (validación humana) | NO |
| `data/mirova_reference/mirova_v1_snapshot/registro_Lascar.csv` | 301 | Per-volcán Lascar (validación humana) | NO |
| `data/mirova_reference/mirova_v1_snapshot/registro_Tupungatito.csv` | 79 | Per-volcán Tupungatito (validación humana) | NO |
| `experiments/89_r2_candidates_scan_result.csv` | 144 | Output S47 R2 scan TIF vs VRP (mirova-tif-archive) | Sí (es output mío) |
| `experiments/60_audit_mirova_full/download_log.csv` | 132 | Log descarga MIROVA (1 día Lascar/Lastarria/PCC) | Sí (output mío) |

---

## Detalle por archivo NO conocido

### 1. `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` — **OSF v2.5 (CRITICAL)**

- **Path**: `VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98 MB, gitignored)
- **Propósito**: Archivo global OSF v2.5 MIROVA, 615,470 filas mundiales, 2001–2025
- **Columnas**: `id, timeUTC, IDvolc, Dayflag, Satellite, Resolution, SatZen, SatAzi, Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP, LAT, LON, Max_Dist, Volc_Name, Volc_LAT, Volc_LON, class`
- **Cobertura Chile** (lat -56..-17, lon -76..-66): **48,360 filas, 10 volcanes**:
  - Lascar 10,028 · Chaitén 5,809 · PCC 5,488 · Lastarria 5,368 · Villarrica 5,211
  - Nevados de Chillán 5,042 · Isluga 4,743 · Copahue 4,168 · Planchón-Peteroa 1,762 · Llaima 741
- **Información clave**: contiene `Resolution` (375/750/1000 = sensor), `Dayflag` (0=noche), `SatZen`/`SatAzi` (zenithal/azimuth), `Npix`, `Tot_Lmir_hot/bk` (radiancias separadas), `VRP`, `LAT/LON` hotspot, `Max_Dist`, `class` (clase MIROVA). Es **el ground truth algorítmico canónico** publicado por Coppola/Laiolo.
- **¿Por qué lo olvidé?**: lo citaba como "OSF v2.5 integrado" sin volver a abrirlo. En S45 traté de auditar coords vent / cluster MIROVA cuando ya tenía las 48k filas con `LAT/LON` exactos del hotspot histórico — habría resuelto D9 summit-priority sin TIF.
- **Cómo usarlo S58+**:
  - Vent oficial empírico = mediana(LAT, LON) por `Volc_Name` y `Dayflag=0`
  - Test 1 calibración: `Tot_Lmir_bk` da `L_bg` histórico real
  - Distribución `Max_Dist` por volcán = inner_radius_km defendible (no inventado)
  - `Tot_Lmir_hot` permite reproducir VRP MW exacto sin re-procesar L1B

### 2. `10.04.2026 registro_vrp_ocr.csv` y `14042026 registro_vrp_ocr.csv`

- **Path**: raíz VRP Chile
- **Propósito**: snapshots OCR mirovaweb con **columnas de validación humana** (`Confianza_Validacion`, `Requiere_Verificacion`, `Metodo_Validacion`, `Nota_Validacion`, `Version_OCR`, `Color_Punto_Dist`)
- **Filas**: 281 / 301 (10 volcanes, Tipo: ALERTA_TERMICA_OCR + FALSO_POSITIVO_OCR)
- **Date range**: 2026-01-20 → 2026-04-10 / 2026-04-14
- **Información clave**: el snapshot `01_05_2026_registro_vrp_consolidado.csv` que sí usaba **NO tiene** los 6 campos de validación humana. Estos OCR sí los tienen — útiles para distinguir refs MIROVA confiables vs dudosas.
- **¿Por qué lo olvidé?**: asumí que el consolidado 01_05 era superconjunto. Es superconjunto en filas pero **subconjunto en columnas**.
- **Cómo usar S58+**: en audits de precision, ponderar refs por `Confianza_Validacion` (Alto/Medio/Bajo). Excluir `Requiere_Verificacion=SI` del cómputo P/R por defecto.

### 3. `registro_vrp_consolidado_25_04_2026.csv`

- **Path**: raíz
- **Filas**: 14,138 (date range 2026-01-10 → 2026-04-25). Snapshot intermedio entre `21_04_2026` (S15) y `01_05_2026`.
- **Información clave**: 12 volcanes (incluye `Peteroa` separado de `PlanchonPeteroa` — anomalía de nombres). Tipos: RUTINA 13316, ALERTA_TERMICA 572, FALSO_POSITIVO 250.
- **¿Por qué lo olvidé?**: solapamiento con 01_05. Pero **es snapshot inmediatamente posterior a S15** — útil para reproducir diff S15→S16 sin contaminación posterior.
- **Cómo usar**: validar regressions A/B contra fecha-corte 25_04.

### 4. `Historial_Puyehue_Cordon_Caulle.csv`

- **Path**: raíz
- **Filas**: 94 (2026-01-11 → 2026-04-04). 17 cols incluyendo `Origen_Dato`.
- **Información clave**: única referencia con campo `Origen_Dato` (distingue scrape OCR vs scrape directo). 71 ALERTA_TERMICA + 23 ALERTA_TERMICA_OCR. PCC tiene lacolito (caso S35 R2 confirmado) — este archivo es ground truth curado.
- **¿Por qué lo olvidé?**: nombre con CamelCase no aparece en grep por "consolidado".
- **Cómo usar**: validación específica del bug D8 lacolito + 5 ref reales del periodo S35.

### 5. CSVs per-volcán en `data/mirova_reference/mirova_v1_snapshot/`

- `registro_Chaiten.csv` (22), `registro_Lascar.csv` (301), `registro_Tupungatito.csv` (79)
- **Propósito**: snapshots Mirova-v1 scraper **por volcán individual** con campo `Origen_Dato`
- **Por qué lo olvidé**: siempre fui directo al `registro_vrp_consolidado.csv` del mismo directorio sin ver los per-vol.
- **Cómo usar**: cuando audito un solo volcán (Lascar D9 summit-priority), abrir el per-vol evita filtros sobre 14k filas.

---

## Archivos esperados pero NO encontrados

- ❌ **NO existe** ningún `.xlsx`/`.xls` en el repo.
- ❌ **NO existe** un Excel/CSV con thresholds Coppola 2016a Tabla 1/2 cargados como data (viven en YAML de profiles y en `BIBLIOGRAPHY_SYNTHESIS.md`).
- ❌ **NO existe** una tabla de calibración A_pix por volcán/sensor (está hardcoded en `pipeline/process_*.py` con WOOSTER_COEFF).
- ❌ **NO existe** un Excel de notas SERNAGEOMIN de Nicolás (sus aportes están en `volcanoes.yaml` como `mirova_center_lat/lon` y notas).
- ❌ **NO existe** un export tabular de MIROVA web actual (cada sesión re-scraping vía Mirova-v1, no se persiste como tabla).

## Recomendaciones

1. **OSF Chile como tabla viva**: extraer `Volc_Name in chile_volcanoes` de `VRP_GLOBAL_ARCHIVE_2025.csv` a `data/mirova_reference/osf_v25_chile.csv` (~3 MB, commiteable). Evitar releer 615k filas cada audit.
2. **Tabla vent empírica**: derivar `vent_lat/lon` y `inner_radius_km` empírico desde percentiles de `LAT/LON/Max_Dist` OSF por volcán → `data/mirova_reference/vents_empirical_osf.csv`. Comparar contra `volcanoes.yaml`.
3. **Unificar OCR + validación humana**: las 5 cols extra de los OCR (`Confianza_Validacion` etc.) deberían propagarse al consolidado. Sin esto, audits actuales tratan toda ref MIROVA como igualmente confiable — falso.
4. **Regla S58**: antes de cualquier audit, `grep -r "\.csv" data/mirova_reference/` para verificar qué CSVs hay disponibles localmente. Repetir la lección S36 (PDFs en `documentacion/`) ahora aplicada a CSVs.

---

**Fin del inventario**. 10 CSVs revisados, 7 marcados como NO usados en S47–S56. Top prioridad: re-incorporar OSF Chile (48,360 refs algorítmicas) como ground truth canónico antes que OCR (281 refs, recall-limited).
