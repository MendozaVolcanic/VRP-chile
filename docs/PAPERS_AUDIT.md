# Auditoría consolidada de papers — VRP Chile S17 2026-04-23

> Consolidación de 10 papers/documentos auditados en S17 (sesiones S17 contenido).
> Para cada paper: qué aporta al pipeline, qué no aporta, y gaps que deja abiertos.

## Papers Tier-1 auditados (autoridad alta, relevancia directa)

### 1. Coppola et al. 2016a SP 426.5 — "Enhanced automated thermal anomaly detection algorithm"

- **PDF**: `documentacion/sp426.5.pdf`
- **Rol**: paper CORE. El único con algoritmo completo tabulado (K1, C1, C2, N·σ, dual-ROI).
- **Valida**: k=18.9 MODIS (Eq.7), K1=-0.8 noche/-0.6 día, ROI1 5×5 km, ROI2 50×50 km.
- **Tabla 1 (umbrales N·σ dual-ROI/día-noche)**: **5σ ROI1 noche / 10σ ROI2 noche / 15σ diurno**. **Nuestro código usa 3σ uniforme → DRIFT D2.**
- **Kernel 8-vecinos mean aritmético** (no mediana). **Nuestro código usa median → DRIFT D1.**
- **Segundo run**: tras detectar activos, recomputa fondo 8-vec EXCLUYENDO activos. Verificar si pipeline nuestro lo hace.
- **Falsos positivos documentados**: bordes cuerpos de agua, nubes dispersas (coincide con Llaima Conguillío).
- **NO menciona**: VIIRS (paper pre-extensión), NOAA-20/21, SWIR, multi-sensor consolidación.

### 2. Wooster et al. 2003 RSE — "Fire Radiative Energy, BIRD/MODIS"

- **PDF**: `documentacion/1-s2.0-S0034425703000701-main.pdf`
- **Rol**: origen de k=18.9. Derivación FRE_MIR = 1.89×10⁷ · (L_MIR − L_MIR,bg) (Eq.6b, p.88).
- **Valida**: k=18.9 MODIS banda 21 con A_sampl=1×10⁶ m² nadir. Error ±30%.
- **No valida**: VIIRS (no existía en 2003). Extensión a VIIRS requiere re-derivación con a específico del ancho espectral del VIIRS.
- **Conceptual**: usa T⁴ en aproximación Planck→Stefan. No T⁸.

### 3. Campus et al. 2022 Sensors 22:1713 — "Transition MODIS→VIIRS"

- **PDF**: `documentacion/Transition_MODIS_to_VIIRS.pdf` (del agente: archivo principal)
- **Rol**: extensión MIROVA a VIIRS 750m M13.
- **Valida**: **k=1.97×10⁷ VIIRS M13 × A_pix(0.5625 km²) → WOOSTER_COEFF=19.7 confirmado bit-a-bit** (Eq.1 p.7).
- **No valida**: VIIRS I4 375m (remite a Coppola 2022 Sabancaya).
- **Plataformas**: S-NPP (Oct 2011), NOAA-20 (Nov 2017). **NOAA-21: "future JPSS missions" sin nombre** (paper Feb 2022, NOAA-21 lanzado Nov 2022).
- **Nevados de Chillán** incluido en validación cross-sensor — único volcán chileno con data directa del paper.
- **Umbrales**: no reporta N·σ, remite a Coppola 2016a.

### 4. Campus et al. 2024 Bull Volcanol 86:25 — "Vulcano VIIRS 375m dataset"

- **PDF**: `documentacion/s00445-024-01721-z.pdf`
- **Rol**: primera cita publicada operacional de VIIRS 375m I4 en MIROVA.
- **Valida**:
  - **k=18.0 VIIRS I4 textual** (p.4): *"in the case of VIIRS I4 band has a value of 18.0 m sr"*.
  - **A_pix=140,625 m²** confirmado.
  - **bbox 50×50 km UTM**.
  - **Kernel arithmetic mean** (p.3) — resuelve drift D1.
- **NO aborda**: N·σ multipliers, dual-ROI C1/C2, saturación I04.
- **NOAA-21 NO mencionado** (paper Feb 2024).

### 5. Di Bella et al. 2024 Remote Sensing 16:2879 — "NRT Data Fusion RSDF"

- **PDF**: `documentacion/Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf`
- **Rol**: primer paper con **umbrales N·σ VIIRS publicados explícitos**.
- **Publica (§3.3 p.6, único paper con tabla completa)**:
  - MODIS: noche 5σ / día 10σ
  - SLSTR: noche 5σ / día 10σ
  - **VIIRS I4+M13: noche 12σ / día 8σ** (contra-intuitivo: noche > día, por resolución fina)
  - SEVIRI: 1σ uniforme
- **Valor crítico**: **nuestro 3σ es ~4× más laxo que MIROVA de noche para VIIRS**.
- **Pero advertencia**: Di Bella mide σ sobre "VA" (mitad-imagen), no sobre anillo ROI 50×50 km. **No intercambiable directo.**
- **Propone k=2.48×10⁷ VIIRS I4**: **refutado empíricamente S14 contra OSF** (error >30%). No adoptar.
- **NO aborda**: dual-ROI, NOAA-21, supervisión humana.
- **Validación**: solo Etna+Stromboli (no volcanes sub-pixel tipo Villarrica).

### 6. Coppola et al. 2023 Front Earth Sci 11:1240107 — "Global MIROVA Database 2000-2019"

- **PDF**: `documentacion/feart-11-1240107.pdf`
- **Rol**: benchmark consolidado + publicación OSF v1.0.
- **Importante**: la base OSF publicada en el paper es **MODIS ONLY 2000-2019** (no multi-sensor).
- **Nuestra referencia local OSF v2.5** es una extensión posterior no documentada en este paper. Verificar README OSF.
- **Volcanes chilenos mencionados**: Lascar, Nevados de Chillán, Chaitén, Puyehue-Cordón Caulle. **Villarrica y Tupungatito NO mencionados nominalmente.**
- **Confirma**:
  - Niveles alerta: **Low / Medium / High / Very High / Extreme** (p.5).
  - **Supervisión humana post-algoritmo** (p.4): filtro manual quita false alerts/fires.
  - MIR solo nocturno.
  - Floor VRP ~1 MW.
- **NO aborda**: N·σ numéricos, mean/median, NOAA-21.

### 7. Aveni et al. 2025 GRL — "Volcanic Radiative Power TIR low-T"

- **PDF**: `documentacion/Geophysical Research Letters - 2025 - Aveni.pdf`
- **Rol**: extensión TIR para low-T features (crater lakes, fumaroles).
- **Propone**: Eq.9 `VRP_TIR = A_pix · k_TIR · ΔL_TIR` con **k_TIR=60.17 μm·sr** para I5 @ 11.45 μm.
- **Conflicto D3**: dice Stefan-Boltzmann puro subestima 90% bajo 600 K. **Coppola 2024 cap Springer usa Stefan-Boltzmann igual**. Conflicto doctrinal.
- **Validación**: 7 case studies, incluye Copahue crater lake. Sin volcanes chilenos.

### 8. Coppola 2024 cap Springer — "Thermal Monitoring of Volcanoes from Space"

- **PDF**: `documentacion/978-3-031-86841-2.pdf` (páginas 325-363, DOI capítulo 10.1007/978-3-031-86841-2_11)
- **Rol**: review pedagógico más reciente por el autor de MIROVA.
- **Confirma**:
  - α=2.96×10⁻¹⁹ MODIS (= k=18.9), α=2.88×10⁻¹⁹ VIIRS 750m (= k=19.7).
  - K1=-0.8 noche/-0.6 día (Table 2, p.336).
  - Multi-sensor integración justificada (Campus 2022, Aveni 2023 citados).
  - **VRP TIR low-T: Eq.16 Stefan-Boltzmann puro** (p.337) — contradice Aveni 2025.
- **NO actualiza**: N·σ tabla (delega a Coppola 2016a).
- **NO menciona NOAA-21** (libro 2024 con fecha corte ~2023).
- **Cero volcanes chilenos en casos de estudio.**

### 9. Thesis Massimetti — "Multi-Sensor Hot-Spot Detection"

- **PDF**: `documentacion/THESIS_MASSIMETTI.pdf`
- **Rol**: marginal para MIR (90% SWIR focus).
- **Confirma**: S-NPP (2012), NOAA-20 (2018), nocturno-only, zenith < 50°, dist < 5 km summit.
- **NO aporta**: coeficientes numéricos MIR, umbrales, NOAA-21.

### 10. Laiolo et al. 2017 JVGR — "Santa Ana (El Salvador) fumarolas"

- **PDF**: `documentacion/1-s2.0-S0377027316305248-main.pdf` (también duplicado en `nuevos/laiolo2017.pdf`)
- **Aclaración**: NO es "Turrialba" como decía CLAUDE.md — es **Santa Ana, El Salvador**.
- **DOI**: 10.1016/j.jvolgeores.2017.04.013.
- **Rol**: caso de aplicación MIROVA a fumarolas alta-T. No redefine algoritmo.

---

## Documentos de soporte (NASA/operacionales)

### JPSS VIIRS Radiometric Calibration ATBD Rev C
- **PDF**: `documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf` (descargado S17)
- **Fuente**: https://nsidc.org/sites/default/files/jpss-atbd-viirs-sdr-c.pdf
- **Rol**: respaldo académico para VJ202IMG/VJ202MOD (NOAA-21). Aplica mismo algoritmo a SNPP/NOAA-20/NOAA-21.

### JPSS VIIRS Imagery Products ATBD Rev E
- **PDF**: `documentacion/JPSS_ATBD_VIIRS_Imagery_RevE.pdf` (descargado S17)
- **Fuente**: https://www.star.nesdis.noaa.gov/jpss/documents/ATBD/D0001-M01-S01-008_JPSS_ATBD_VIIRS-Imagery_E.pdf

---

## Papers pendientes auditar (futuras sesiones)

| Paper | PDF | Gap que cubre | Prioridad |
|---|---|---|---|
| Aveni 2024 TIRVolcH RSE | `1-s2.0-S0034425724004140-main.pdf` | Resolver D3 TIR Stefan vs Eq.9 | 🔴 Alta — S19 |
| Coppola 2022 Sabancaya Bull Volcanol | `s00445-022-01523-1.pdf` | Origen histórico k=18.0 | 🟡 Media — S19 |
| Massimetti 2020 RS 12:820 (SWIR) | `remotesensing-12-00820-v4.pdf` | Base SWIR | 🟢 Baja — Fase SWIR |
| Torrisi 2023 Fast VRP VIIRS SLSTR | `Torrisi2023_FastVRP_VIIRS_SLSTR.pdf` | Cross-validación | 🟢 Baja |
| Reath 2018 JGR (47 volcanes) | `JGR Solid Earth - 2018 - Reath.pdf` | Thermal time-series 2000-2017 | 🟢 Baja |

---

## Mapa de referencias por componente del pipeline

| Componente | Constante/umbral | Paper que lo sustenta | Página/Ecuación |
|---|---|---|---|
| MODIS k Wooster | 18.9 | Wooster 2003 | Eq.6b p.88 |
| VIIRS M13 k | 19.7 | Campus 2022 | Eq.1 p.7 |
| VIIRS I4 k | 18.0 | Campus 2024 | p.4 (literal) |
| NTI K1 noche | -0.8 | Coppola 2016a, Coppola 2024 | Tabla 1 / Table 2 p.336 |
| NTI K1 día | -0.6 | Coppola 2016a | Tabla 1 |
| ROI1 summit bbox | 5×5 km | Coppola 2016a, Coppola 2023 | §"ROI" / p.2 |
| ROI2 scene bbox | 50×50 km UTM | Coppola 2016a, Campus 2024 | §"ROI" / p.3 |
| Kernel 8-vec | mean aritmético | Coppola 2016a, Campus 2024 | §"Spatial" / p.3 |
| N·σ MODIS noche | 5 (ROI1) / 10 (ROI2) | Coppola 2016a / Di Bella 2024 | Tabla 1 / p.6 |
| N·σ MODIS día | 15 (uniforme) / 10 (Di Bella) | Coppola 2016a / Di Bella 2024 | — |
| N·σ VIIRS noche | 12 | Di Bella 2024 | p.6 |
| N·σ VIIRS día | 8 | Di Bella 2024 | p.6 |
| TIR Stefan-Boltzmann | σ=5.67×10⁻⁸ | Coppola 2024 | Eq.16 p.337 |
| TIR Aveni Eq.9 | k_TIR=60.17 μm·sr | Aveni 2025 | Eq.9 p.4 |
| Niveles alerta | Low/Medium/High/Very High/Extreme | Coppola 2016a, Coppola 2023 | — / p.5 |
| NRT latencia | 1-4h MIR, 6-24h SWIR | mirovaweb.it about.php | web |
