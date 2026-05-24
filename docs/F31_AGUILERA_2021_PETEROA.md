# F31 — Aguilera et al. 2021 PP crater lakes (extract)

> **Status**: descargado + leído abstract + secciones clave (S75 búsqueda dirigida)
> **Trigger**: ground truth crater lake citado por Aveni 2025 GRL; PP es Tier A nuestro

## Metadata

| Campo | Valor |
|---|---|
| **Citekey** | `aguilera2021evolution` |
| **Autores** | Felipe Aguilera (UCN-Ckelar/CIGIDEN), Javiera Caro, Susana Layana |
| **Año** | 2021 (publicado 28-oct-2021) |
| **Revista** | Frontiers in Earth Science (Open Access) |
| **DOI** | [10.3389/feart.2021.722056](https://doi.org/10.3389/feart.2021.722056) |
| **Archivo local** | `documentacion/aguilera2021peteroa.pdf` (5.6 MB, magic PDF v1.4) |
| **Markdown** | `documentacion/aguilera2021peteroa.md` (2133 líneas) |
| **Vault note** | `Vault/10_Bibliografia/99_por_clasificar/aguilera2021evolution.md` (existe pre-S75, alta calidad) |

## Abstract (verbatim, recortado a esenciales)

> Peteroa volcano (Chile–Argentina border) is part of the Planchón–Peteroa–Azufre Volcanic Complex... formed by a ∼5 km diameter caldera-type crater, which hosts four crater lakes and several fumarolic fields. Here, we used TIR and SWIR bands from Landsat TM, ETM+, and OLI images available from October 1984 to December 2020 to obtain thermal parameters such as thermal radiance, brightness temperature, and heat fluxes... We determined the occurrence of two eruptive/thermal cycles... The maximum Qvolc measured between all crater lakes during quiescent periods was **59 MW**, whereas during unrest episodes Qvolc in single crater lakes varied from **7.1 to 38 MW**, with Peteroa volcano being classified as a **low volcanic heat flux system**.

## Findings clave para VRP Chile

### Numéricos (ground truth Peteroa)

| Parámetro | Valor | Source paper |
|---|---|---|
| **Qvolc pico quiescente (todos los cráteres simultáneos)** | **59 MW** | enero 2006 |
| **Qvolc rango por lago en unrest** | **7.1 – 38 MW** | Cráteres 1–4 |
| Qvolc Cráter 1 (abril 2019, unrest) | 7.1 MW | nested crater |
| Qvolc Cráter 2 (marzo 2001, unrest máx) | 38 MW | máximo individual |
| Qvolc Cráter 3 (feb 2005) | 31 MW | — |
| Qvolc Cráter 4 (marzo 2001) | 23 MW | — |
| **Piso teórico Landsat TIR post-background** | **0.007 MW/pixel** | sensibilidad mínima |
| Diámetro caldera | ~5 km | |
| Coords nominales | 35.240°S 70.570°W, 3,603 m s.n.m. | |

### Implicancias operacionales VRP Chile

1. **Validación cruzada VRPTIR Aveni 2025 (F31)**: Aguilera reporta Qvolc por balance energético completo (Pasternack & Varekamp 1997), no Stefan-Boltzmann puro. Sin embargo, el rango **0.5 – 59 MW** que cubre quiescente → unrest máx en Peteroa es exactamente el régimen donde VRPTIR (Aveni 2025) debería dominar sobre VRP-MIR. Es un caso test natural.

2. **Régimen "Muy Bajo" validado físicamente (A21/S72 AVTOD)**: Peteroa es low-Qvolc system comparable a Copahue pre-2012 (Varekamp et al. 2001, 7–45 MW). Justifica las tolerancias R2 régimen-dependientes del audit S70-1 — PP nunca va a comportarse como Lascar (Tier A Alto).

3. **Migración del vent entre cráteres + nested crater desde dic-2018**: el "vent térmicamente activo" en PP cambia entre eventos. Nuestra coord nominal en `volcanoes.yaml` debería revisarse para eventos post-2018 (nested crater en flanco SW Cráter 1).

4. **Lagos chicos calientes son falsos negativos térmicos** (mar-2011: Cráter 2 a 43 °C pero lago demasiado pequeño → sin anomalía Landsat). Aplicable directamente a sub-pixel MIROVA/VIIRS: un lago activo puede no producir anomalía MIR aunque caliente. **No es bug del pipeline, es física**.

5. **Ground truth fechas críticas para A/B de recall**:
   - Ciclo 1: feb-1991 (formación Cráteres 3/4) · oct-1998–feb-2001 (degas máx) · sep-2010–jul-2011 (erupción)
   - Ciclo 2: jun-2017 (reactivación C3) · jul-2018 (anomalía C1) · oct-2018–abr-2019 (erupción + nested crater)
   - Supplementary Table S1 contiene **todas las fechas con Qvolc Landsat 1984–2020** → gold standard para experimento de calibración recall MODIS/VIIRS sobre PP.

### Método (paridad con VRP Chile)

- **Brightness temperature Landsat**: K1=607.76 W/m²·μm·sr, K2=1260.56 K (Landsat TM).
- **Qrad = ε·σ·T⁴·A_pix** con σ Stefan-Boltzmann = 5.67×10⁻⁸ W/m²·K⁴ — **idéntico a VRP TIR nuestro y a Aveni 2024 RSE / Coppola 2024 Springer Cap.16** (D3 RESUELTO S17).
- Emisividad: agua 0.93–0.95 estacional, suelo 0.98.
- Threshold pixel térmico: DN = mean_no_thermal + 2σ_no_thermal (separación manual preliminar).
- Balance energético completo (Pasternack & Varekamp 1997): Qvolc = Qrad + Qevap + Qcond + Qrain − Qsun − Qatm − Qvolc-cond. Atmosféricos fijos (v=8 m/s, Pa=670 mbar @ 3460 m, precip 0.0029 m/día).

## Conexiones con investigaciones VRP Chile

- **F31 Aveni 2025 VRPTIR** (`docs/F31_AVENI_VRPTIR_PLAN_S74.md`): Aguilera 2021 es candidato directo para validar VRPTIR contra balance energético independiente en Peteroa.
- **S72 AVTOD cross-validation** (`docs/AVTOD_CROSS_VALIDATION_S72.md`): refuerza decisión de no etiquetar régimen "Muy Bajo" PP como FP — la física lo respalda.
- **S70-1 R2 régimen-dependiente** (`docs/R2_GATES_BY_REGIME.md`): Aguilera 2021 es la cita autoritativa para defender tolerancias amplias en PP en el paper VRP Chile (P5).

## Pendientes (no críticos S75)

- [ ] Descargar **Supplementary Table S1** (todas las fechas Qvolc Landsat 1984–2020) cuando se haga calibración recall PP.
- [ ] Revisar coord `mirova_center` PP en `volcanoes.yaml` vs nested crater post-2018.
- [ ] Aguilera 2016 (ciclo 2010–2011) + Romero 2020 (erupción 2018–2020) como referencias secundarias.

## Status descarga

- **Fuente**: Frontiers in Earth Science, Open Access directo
- **URL descarga**: `https://www.frontiersin.org/articles/10.3389/feart.2021.722056/pdf`
- **Búsquedas APIs no necesarias**: DOI ya estaba en nota Vault pre-existente (`aguilera2021evolution.md`, S15 era). Local-first ahorró búsqueda Crossref/OpenAlex.
- **Verificación**: PDF 5.6 MB, magic `PDF document, version 1.4`, conversión markitdown OK (2133 líneas).
