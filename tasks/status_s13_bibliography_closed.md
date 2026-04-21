# Status S13 — Fase bibliografía cerrada

Fecha: 2026-04-18. Sesión: S13 (continuación de S12 cerrada 2026-04-16).
Siguiente sesión: S14.

---

## Lo que quedó hecho en S13

### Bibliografía
- **62 PDFs en `documentacion/`**, 58 únicos (duplicados limpiados por MD5).
- **`BIBLIOGRAPHY_SYNTHESIS.md`** completo: secciones 1–9 cubren Wooster 2003 →
  Coppola 2025 book chapter 11 + descubrimientos segunda búsqueda + OSF v2.5.
- **MIROVA Database v2.5 OSF descargada** en `data/mirova_reference/`:
  615,470 filas (CSV 98 MB + schema docx). Reemplaza OCR consolidado como
  ground truth Tier A — Villarrica pasa de 6 refs a 5,211 refs reales.
- **Coppola 2022 Sabancaya confirmado** como el "Coppola 2022" del book chapter
  (no era Campus 2022). Es el paper que oficializa VIIRS 375m en MIROVA.
- **Corrección crítica**: `coppola2015.pdf` y `sp426.5.pdf` eran el mismo PDF.
  Son Coppola et al. **2016a** (SP426.5), no dos papers. Síntesis corregida.

### Fix trivial pipeline
- `pipeline/process_viirs.py` línea 46: `WOOSTER_COEFF = 18.9 → 18.0`
  (Laiolo 2024 Vulcano VIIRS I4 375m). Sesgo 5% en VRP_375m corregido.
  **No corrido aún**: próximo NRT refleja el cambio automático.

### Documentación transversal
- `Volcanologia/claude/bibliography_search_methodology.md` creada — metodología
  de búsqueda bibliográfica reutilizable para OpenVIS, Goes, Valles.
- `claude/Obsidian/00_Investigacion_inicial.md` — evaluación de Obsidian +
  Zotero + Claude Code como stack de "segundo cerebro" multi-proyecto.

### Sistemas competidores identificados (abril 2026)
- MIROVA (UNITO) — canónico
- MOUNTS (GFZ, Valade) — Sentinel + SAR + AI
- NHI (CNR-IMAA, Marchese/Genzano) — GEE global
- HOTSAT/CL-HOTSAT (INGV Catania, Ganci)
- RSDF (INGV, Di Bella) — fusion 4 sensores
- V-STAR (INGV Catania, Corradino) — S-2 ML
- FastVRP (CNR-IMAA, Torrisi)
- VOLCANOMS (UCN Chile, Layana) — **Chile-específico Landsat**
- HotLINK (USGS AVO, Saunders-Shultz) — **benchmark directo vs MIROVA,
  código en GitHub**
- TIRVolcH (UNITO, Aveni) — algoritmo, no NRT público

**Posicionamiento VRP Chile**: nicho = VIIRS+MODIS NRT per-volcán-chileno con
paridad MIROVA cuantificada. Ninguno otro lo cubre con granularidad OVDAS.

---

## Gaps remanentes (bibliografía)

1. **Marchese & Genzano 2023 NHI** (J Geol Soc subscription). Bajar si hay acceso
   institucional SERNAGEOMIN. No crítico — Genzano 2020 GEE ya cubre arquitectura.
2. **Pritchard 2022 USGS**: hay dos archivos (`Pritchard2022_*.pdf` + `sir20225116.pdf`).
   Verificar si son idénticos por MD5, borrar el duplicado.
3. **Coppola 2012 Stromboli MODIS 12 años**: no crítico para S14.
4. **Libro Harris AJL 2013** (Cambridge, paywall): referencia de fondo si
   se quiere documento pedagógico.

---

## Plan S14 — arrancar acá

Del plan estructurado en sesión anterior (ver mensajes S13). Orden:

### Fase 0.5 — bugs triviales antes de tocar nada serio
- Verificar `Pritchard*` duplicado, borrar el redundante.
- Correr NRT una vez con el fix `WOOSTER_COEFF=18.0` → regenerar VRP VIIRS 375m,
  push a dashboard.

### Fase 1 — re-auditoría con OSF v2.5
Este es el cambio más importante estructuralmente. **Antes de Track A/B**:

1. Leer `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` con pandas.
2. Filtrar columnas: `Volc_Name ∈ {nuestros 11 Tier A/B}`, `Satellite`, `Resolution`.
3. Re-correr auditoría S12 contra esta DB (no contra OCR).
4. Tabla esperada:
   - Villarrica recall real (sobre 5,211 refs, no 6)
   - Lascar ratio mediano real (sobre miles de refs, no 191)
   - Copahue entra en Tier A (4,168 refs disponibles)
   - Llaima entra en Tier A (741 refs)

**Criterio**: re-definir Tier A con umbral ≥100 refs MIROVA v2.5 (no ≥30).
Probablemente 8–10 volcanes califican Tier A con esto.

### Fase 1 continuación — Plan tracks paralelos

Recordatorio estructura (detalle en mensajes S13):

- **Track A `mirova_equivalent`** por sensor:
  - MODIS: ETI cuadrático + dNTI/dETI contextual + ROI1/ROI2 dual + second-pass.
  - VIIRS 750m: Campus 2022 con k=1.97×10⁷ o Di Bella k=1.11×10⁷ (resolver
    discrepancia antes de implementar).
  - VIIRS 375m: Coppola 2016a adaptado + umbrales Di Bella n=12 nocturno.

- **Track B `experimental`** por sensor:
  - MODIS: integrated-ROI Coppola 2023 Eq.1 (Test 1, ya planificado).
  - VIIRS 375m: TIRVolcH sobre I5 (Aveni 2024 completo).
  - VRP_TIR Stefan-Boltzmann (Aveni 2025 GRL).
  - Isolation Forest (Trasatti 2024) como path alternativo al NTI.

### Fase 2 — benchmark externo
Replicar protocolo evaluación **HotLINK** (Saunders-Shultz 2024, código público
en `github.com/csaundersshultz/HotLINK`) sobre Villarrica y Lascar. Comparar
recall/precision nuestro vs MIROVA vs HotLINK.

### Fase 3 — productos post-paridad
- Galetto 2025 `c_rad` → volumen acumulado (Chaitén dacítico, Villarrica basáltico).
- Coppola 2013 refinamiento de `c_rad` por reología.
- Aveni 2025 GRL VRP_TIR formalizado para Copahue/Planchón-Peteroa crater lakes.

---

## Discrepancias técnicas abiertas (resolver antes de implementar)

### k_MIR VIIRS 375m
- Laiolo 2024 Vulcano: `18.0 × A_pix` con `A_pix = 140,625 m²` → efectivo `2.53×10⁶`
- Di Bella 2024: `k = 2.48×10⁷` (embebido, factor 10 más grande)
- **Acción S14**: releer derivación exacta en Di Bella 2024 (`Advancing_Volcanic...pdf`),
  sección de ecuaciones, para resolver unidades.

### k_MIR VIIRS 750m
- Campus 2022: `1.97×10⁷ / A_pix=0.5625 km²`
- Di Bella 2024: `1.11×10⁷` (embebido)
- **Acción S14**: mismo método, releer Di Bella.

### Umbrales Di Bella vs Coppola
- Di Bella publica n=12 nocturno VIIRS. Coppola no publica el equivalente.
- **Decisión S14**: arrancar con n=12 Di Bella para Track A, medir recall
  sobre OSF v2.5, ajustar.

---

## Archivos clave para próxima sesión

Leer en orden al arranque S14:
1. `tasks/status_s13_bibliography_closed.md` (este archivo)
2. `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` secciones §7bis, §8bis, §9
3. `data/mirova_reference/MIROVA_Database_Schema_v2.5.docx` para confirmar códigos
   `Satellite` (1=Terra, 2=Aqua, 3=VIIRS-SNPP, 4=VIIRS-NOAA20 asumido pero verificar)

Consulta bajo demanda:
- `documentacion/Advancing_Volcanic_Activity_Monitoring_A_Near-Real.pdf` (Di Bella RSDF)
- `documentacion/s00445-022-01523-1.pdf` (Coppola 2022 Sabancaya)
- `documentacion/feart-12-1345104.pdf` (HotLINK Saunders-Shultz, benchmark)

---

## Estado pipeline y data

- NRT funcionando: 45 volcanes, cron cada 2h, matrix paralelizada.
- Data `data/mirova_equivalent/` actualizada al 2026-04-18 (PlanchonPeteroa
  reproceso pendiente según `git status`).
- Dashboard `frontend/index.html`: Celsius, coord real pixel, filtros 24h-1año.
- **Cambio no pusheado**: `WOOSTER_COEFF=18.0` en `pipeline/process_viirs.py`.
  Commitear en S14 arranque.

---

## Contexto personal (para sesión fresca)

- Nicolás: geólogo SERNAGEOMIN, comunicación en español, razonamiento físico
  antes que numérico, "por qué" antes que "cómo".
- Regla biblio: ningún umbral se cambia sin paper + verificación propia.
- Regla comunicación: fenómeno físico → pipeline → números. Nunca al revés.
- Trabajo distribuido entre 3+ carpetas: `Volcanologia/` (proyectos),
  `OVDAS/` (institucional), `Automatizacion web/` (scraping MIROVA).
  Propuesta de unificación vía Obsidian en `claude/Obsidian/00_Investigacion_inicial.md`.
