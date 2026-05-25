# Propuesta de paridad con dashboard Mirova-v1 — S77

**Fecha**: 2026-05-25
**Worktree**: `VRP-Chile-s77-mirova-v1-parity`
**Branch**: `claude/s77-mirova-v1-parity-proposal`
**Autor**: Claude (Opus 4.7) bajo dirección de Nicolás
**Tipo**: Documento de diseño — NO toca código

---

## Contexto

Nicolás opera dos sistemas hermanos:

1. **Mirova-v1** (`MendozaVolcanic/Mirova-v1`, GitHub Pages: https://mendozavolcanic.github.io/Mirova-v1/).
   Scraper de `mirovaweb.it` (latest.php cada 5 min + OCR cada 1h). **Es la "verdad MIROVA"**
   re-publicada, sin pipeline propio. Dashboard tipo galería con 11 cards (un Plotly por volcán
   embebido en iframe).
2. **VRP-Chile** (este repo, https://mendozavolcanic.github.io/VRP-chile/). Clon MIROVA propio
   con pipeline NRT cron 2h, 11 volcanes Tier A, dashboard rico mono-volcán
   (Chart.js + Leaflet + galería de imágenes pipeline-generated).

Nicolás pidió **"una ventana que nos permita ver los datos como ese dashboard"**:
el dashboard Mirova-v1 tiene una **vista panorámica multi-volcán** que VRP-Chile no tiene
(VRP-Chile fuerza al usuario a elegir un volcán y profundizar; Mirova-v1 muestra 11 a la vez).

Este documento compara ambos lado a lado y propone qué features portar.

---

## 1 · Análisis Mirova-v1

### 1.1 Arquitectura del dashboard

- **Index único** `index.html` (218 líneas, HTML estático) — carga 11 iframes en grilla CSS
  `repeat(auto-fit, minmax(420px, 1fr))`. Cada iframe apunta a
  `monitoreo_satelital/v_html/<Volcan>.html` (Plotly puro pre-renderizado, ~17–70 KB cada uno).
- **Pre-render server-side**: los gráficos se generan offline con Python (Plotly export) y se
  commitean. El cliente solo carga HTML estático — no hace queries ni cálculos en navegador.
- **Toggle escala lineal/log global**: un solo botón intercambia el directorio de iframes entre
  `v_html/` y `v_html_log/`. Misma data, dos renders.
- **Modal de zoom**: click en card abre iframe ocupando 95% de pantalla.
- **Botón CSV per-volcán**: descarga directa de `registro_<Volcan>.csv`.
- **Estado del sistema**: `estado_sistema.json` con 3 campos
  (`estado`, `color`, `ultima_actualizacion`) — semáforo simple.

### 1.2 Cada card (un volcán)

- **Plotly scatter multi-sensor**:
  - **VIIRS 750m** (M-band) → marcador `●` color gris (`#C0C0C0`)
  - **VIIRS 375m** (I-band) → marcador `■` color naranja (`#FF4500`)
  - **MODIS** → marcador `▲` color naranja oscuro (`#FFA500`)
  - Eje X: fecha (formato `dd Mmm`)
  - Eje Y: VRP en MW
  - Tooltip: sensor + volcán + fecha + VRP
- **Anotación "MÁX: X.X MW"** automática sobre el pico del periodo (con flecha).
- **Sombreado dinámico por umbrales MIROVA**: bandas de color de fondo (Muy Bajo, Bajo, Moderado, Alto, Muy Alto)
  **solo si la energía cruza el umbral** (evita "ruido visual" en volcanes en calma — V4.1).
- **Confianza OCR**:
  - 🟢 Alta — grupo de píxeles rojos detectado en ROI (V19)
  - 🟡 Media — estrella verde detectada (V16)
- **Tag de región** (Tarapacá, Antofagasta, Maule, etc.) junto al nombre del volcán.

### 1.3 Layout global

- **Barra audit superior sticky**: estado sistema, último sync UTC, toggles globales.
- **Header** con título + leyenda compacta (confianza + niveles MIROVA + nota UTC).
- **Grilla central** de 11 cards (3 columnas en desktop, 1 en mobile).
- **Footer** con créditos + links (GitHub, MIROVA web, SERNAGEOMIN).
- **Color scheme dark**: fondo `#0b0e14` / `#0d1117` / `#161b22`, accent azul `#58a6ff`, naranja `#FF4500`.
- **Tipografía**: Segoe UI 11 px base.

### 1.4 Datos servidos

CSVs maestros (committed):
- `registro_vrp_consolidado.csv` — latest.php (primaria)
- `registro_vrp_ocr.csv` — eventos recuperados por OCR
- `registro_vrp_maestro_publicable.csv` — combinada final
- `registro_<Volcan>.csv` — individual por volcán

Campos típicos (inferidos del Plotly):
`Sensor`, `Volcan`, `Fecha_Chile` (timestamp con `-03:00`), `VRP_MW`, `confianza`, `nivel_alerta`.

---

## 2 · Análisis VRP-Chile (estado actual S76)

### 2.1 Arquitectura

- **`frontend/index.html`** (~2937 líneas) — dashboard **mono-volcán** Chart.js + Leaflet.
  Cards con selector de volcán (11 Tier A operacional). Cada cambio re-renderiza todo.
- **`frontend/diario.html`** (510 líneas) — vista diaria detallada (cron output del último día).
- **`frontend/mirova_imgs_index.json`** — galería MIROVA scraped (PR #182).

### 2.2 Features presentes (S70+ → S77)

| Feature | PR | Descripción |
|---|---|---|
| Overlay MIROVA per-sensor | #164 | Línea ground truth sobre chart VRP nuestro |
| Spatial layer Leaflet | #166 | Pixels detectados en mapa con halo crater |
| Cards live (latest VRP) | #167 | KPIs grandes con valor más reciente |
| Galería MIROVA imgs | #182 | Lightbox + paginación temporal |
| Banner stale | #184 | Alerta si cron NRT atrasado |
| Modal "Acerca de" | — | Metodología + créditos científicos |
| Distance counts 7d | — | Histograma summit/intermediate/far |
| About modal + glosario | — | Definiciones TP/FP/FN, paths A-D |
| CSV export per-volcán | — | Botón download |
| Audit metrics | — | Recall/precision/F1 vs MIROVA |
| Light/dark theme | — | Toggle persistido |

### 2.3 Gaps clave vs Mirova-v1

| Gap | Severidad |
|---|---|
| **No hay vista panorámica multi-volcán** — siempre se ve UN volcán a la vez | **ALTA** |
| Sin sombreado dinámico por umbrales MIROVA (bandas Muy Bajo→Muy Alto) | MEDIA |
| Sin anotación automática de pico (MÁX X MW) en el chart | BAJA |
| Sin toggle log/lineal global (existe per-chart pero no sincroniza) | MEDIA |
| Sin badge confianza OCR (🟢/🟡) por evento | BAJA |
| Sin tags de región (Tarapacá, Maule, etc.) | BAJA |
| Sin estado sistema unificado (solo banner stale) | BAJA |
| Modal de zoom con iframe (más limpio que abrir vista completa) | BAJA |

### 2.4 Ventajas diferenciadas de VRP-Chile

Para que no se pierda valor al portar:

- ✅ **Pipeline propio NRT** (no scraper) — independencia operacional de mirovaweb.it.
- ✅ **Audit metrics cuantitativas** TP/FP/FN/recall/precision/F1.
- ✅ **Spatial Leaflet** con coords reales de pixels detectados (no solo gráficos PNG).
- ✅ **Overlay comparativo** MIROVA-vs-nuestro per-sensor en el mismo chart.
- ✅ **Sigma context** (dNTI vecinos, paths A-D) visible.
- ✅ **Glosario científico** en About modal.

---

## 3 · Propuesta de features a portar — priorizada

Cinco features, ordenadas por **valor de usuario** (Nicolás como geólogo) × **inverso del esfuerzo**.

### F1 · Vista panorámica multi-volcán "Mosaico" — **VALOR ALTO / ESFUERZO M**

**Por qué**: este es el pedido explícito de Nicolás. Es el feature que diferencia el día a día
de un geólogo monitoreando 11 volcanes (necesita escaneo rápido) vs uno haciendo análisis
profundo (necesita zoom).

**Qué**: nueva vista `frontend/mosaico.html` con grilla 3-4 columnas, una mini-card por
volcán. Cada card:
- Título + región
- Mini-chart Chart.js (sin ejes, sin legenda, 60-100 px de alto) — VRP últimos 30 días
- KPI "último VRP detectado" + timestamp
- Badge nivel actual (Muy Bajo / Bajo / Moderado / Alto / Muy Alto)
- Click → abre `index.html?volcano=<X>` (vista detallada actual)

**Implementación**:
- Reusar `data/mirova_equivalent/<Volcan>.json` (ya committed).
- Reusar `mirovaEqVrp()` y `latestVRP()` de `index.html` (extraer a `frontend/lib/vrp_utils.js`).
- Layout CSS Grid copiado de Mirova-v1 (`repeat(auto-fit, minmax(360px, 1fr))`).
- Link en header de `index.html`: "📊 Vista panorámica".

**Archivos a tocar**:
- ➕ `frontend/mosaico.html` (~300 líneas)
- ➕ `frontend/lib/vrp_utils.js` (extraer 5-6 funciones puras de `index.html`)
- ✏️ `frontend/index.html` — link nav + extraer funciones a lib
- (opcional) ➕ `frontend/styles/mosaico.css`

**Estimación**: 1 sesión (~3-4h con TDD).

---

### F2 · Sombreado dinámico por umbrales MIROVA — **VALOR ALTO / ESFUERZO S**

**Por qué**: los niveles "Muy Bajo / Bajo / Moderado / Alto / Muy Alto" son la nomenclatura
oficial MIROVA. Pintar el fondo del chart según umbral hace que Nicolás (y cualquier geólogo
OVDAS) lea el estado del volcán **en 1 segundo sin mirar números**. Es traducir VRP_MW al
lenguaje del operador, no del satélite.

**Qué**: Chart.js plugin que dibuja bandas horizontales:
- Muy Bajo: 0 – 5 MW (gris)
- Bajo: 5 – 30 MW (verde)
- Moderado: 30 – 100 MW (amarillo)
- Alto: 100 – 1000 MW (naranja)
- Muy Alto: > 1000 MW (carmesí)

**Solo pintar las bandas que la data cruza** (lección V4.1 Mirova-v1) para no ahogar volcanes
en calma con 4 bandas vacías.

Umbrales exactos: a confirmar con tabla MIROVA (Coppola 2016a Tabla 2 / publicación oficial).

**Archivos a tocar**:
- ✏️ `frontend/index.html` función `drawChart()` (línea ~2211) — agregar plugin `annotation`
- ✏️ Reutilizar mismo plugin en `mosaico.html`

**Estimación**: 1-2h.

---

### F3 · Toggle global Log/Lineal con persistencia — **VALOR MEDIO / ESFUERZO S**

**Por qué**: Mirova-v1 lo pone en la barra superior y afecta a los 11 charts a la vez.
Log es esencial para volcanes "callados" (Lastarria, Peteroa) cuyo background queda
aplastado a cero en lineal pero muestra señal real en log.

**Qué**: botón sticky top con icono 📈/📉, persiste preferencia en `localStorage`. Se
aplica a chart principal + mini-charts del mosaico.

**Archivos a tocar**:
- ✏️ `frontend/index.html` — botón en barra audit existente + persistedFlag (ya hay infra)
- ✏️ `frontend/mosaico.html` — mismo botón sincronizado
- ✏️ función `drawChart()` — switch `type: 'logarithmic'`

**Estimación**: 1h.

---

### F4 · Anotación automática del pico (MÁX X MW) — **VALOR MEDIO / ESFUERZO S**

**Por qué**: cuando un volcán tiene un evento puntual (ej. Villarrica 5 MW el martes pasado
sobre baseline 0.3 MW), el ojo del operador busca **inmediatamente el máximo**. Una flecha
con etiqueta "MÁX: 5.0 MW" lo señala sin tener que hover.

**Qué**: en `drawChart()`, encontrar el max(VRP) del periodo visible y agregar una anotación
Chart.js (label + arrow) en ese punto.

**Archivos a tocar**:
- ✏️ `frontend/index.html` `drawChart()` — usar `chartjs-plugin-annotation` (ya cargado)

**Estimación**: 30-45 min.

---

### F5 · Tags de región + reordenamiento N→S por defecto — **VALOR BAJO-MEDIO / ESFUERZO XS**

**Por qué**: Mirova-v1 muestra `Lascar (Antofagasta)`, `Villarrica (Araucanía)`. Para
SERNAGEOMIN, agrupar por zona geográfica (Norte CVZ → Sur SVZ → Austral) es la forma
natural de mirar Chile.

**Qué**: agregar campo `region` y `zone` a `volcanoes.yaml`, ordenar selector y mosaico
por zona N→S (ya está marcado parcialmente en `index.html` líneas 597-643 con comentarios
"Zona Norte CVZ", "Zona Central SVZ", etc. — falta exponerlo en UI).

**Archivos a tocar**:
- ✏️ `volcanoes.yaml` — agregar `region:` y `zone:` per volcán
- ✏️ `frontend/index.html` — selector con `<optgroup>` por zona + render del tag
- ✏️ Mismo en `mosaico.html`

**Estimación**: 30-45 min.

---

### F6 (stretch) · Estado sistema unificado con semáforo — **VALOR BAJO / ESFUERZO S**

**Por qué**: Mirova-v1 tiene un `estado_sistema.json` con un solo campo "Operativo / Degradado /
Caído". Concentra en un símbolo (🟢/🟡/🔴) la salud del cron+pipeline+publicación. Nuestro
banner stale (PR #184) ya cubre el caso "cron atrasado" pero no agrupa con otras señales
(% volcanes con data fresca, último push exitoso).

**Qué**: nuevo `data/system_status.json` generado por workflow cron al final del job, con:
```json
{
  "status": "operativo|degradado|caido",
  "color": "#2ea043|#f0883e|#da3633",
  "last_run_utc": "...",
  "volcanoes_fresh": 10,
  "volcanoes_total": 11,
  "notes": "..."
}
```
Badge en header.

**Archivos a tocar**:
- ➕ `scripts/write_system_status.py`
- ✏️ `.github/workflows/nrt.yml` — paso final que llama al script
- ✏️ `frontend/index.html` y `mosaico.html` — fetch + render badge

**Estimación**: 1h (incluye workflow).

---

## 4 · Roadmap sugerido S78+

Lote priorizado por valor real entregado:

### Sprint S78 — "Vista panorámica" (objetivo: el pedido de Nicolás)
- **F1 mosaico** (3-4h) — el feature central
- **F2 sombreado umbrales** (1-2h) — multiplica el valor del mosaico
- **F5 tags región + N→S** (45 min) — preparatorio para F1

→ Entregable: PR único `feat(frontend): vista panorámica mosaico multi-volcán` con
las 3 features integradas. Demo en GH Pages.

### Sprint S79 — "Lectura rápida"
- **F3 toggle log/lineal global** (1h)
- **F4 anotación pico** (30 min)
- **F6 estado sistema unificado** (1h)

→ Entregable: refinamiento UX del mosaico + index. Lote chico, 1 PR.

### Sprint S80 — "Convergencia con Mirova-v1" (opcional)
- Embed botón "Ver en Mirova-v1" (link cruzado a card homóloga del otro sistema) para que
  Nicolás compare visualmente nuestra detección vs MIROVA original sin abrir 2 ventanas.
- (Si Nicolás quiere) embed iframe Mirova-v1 dentro de modal "Verificación cruzada" en
  vista detallada nuestra — útil para auditoría manual cuando hay divergencia.

---

## 5 · Anti-patrones a evitar (lecciones de Mirova-v1)

- **NO copiar el modelo de iframes Plotly server-rendered**. Tenemos Chart.js cliente que es
  más flexible (interactivo, brushing temporal, overlays) y nuestra data ya vive en JSON,
  no en CSV. Iframes son una solución a un problema (server-render Plotly) que no tenemos.
- **NO copiar el sistema OCR de Mirova-v1**. Es necesario allá porque scrapea pantallazos
  de mirovaweb.it. Nosotros tenemos el pipeline NRT como fuente primaria.
- **NO copiar el campo `Y_LIMITE_PX`** (geofencing en píxeles del gráfico MIROVA). Ese es
  un parche del scraper, no relevante para nosotros.
- **SÍ mantener nuestro overlay MIROVA per-sensor** (PR #164) — es estrictamente mejor que
  los charts separados de Mirova-v1.

---

## 6 · Validación con principios CLAUDE.md

| Principio | Cumplimiento |
|---|---|
| Misión clon literal MIROVA (`docs/MISSION.md`) | ✅ Esta propuesta es 100% UI/visualización, no toca pipeline ni thresholds |
| Simplicity First | ✅ F1 reusa data/funciones existentes, no agrega backend |
| Data Integrity | ✅ Solo lee `data/mirova_equivalent/` que ya está committed |
| Regla publicación dashboard | ✅ Cada feature, al implementarse, va a GH Pages |
| Skill triggers obligatorios (cambios >20 líneas frontend) | Cuando se ejecute: `writing-plans` + `test-driven-development` antes de tocar |
| A45 NRT pipeline crítico | ✅ NO se toca `pipeline/`, solo `frontend/` |

---

## 7 · Próximos pasos (no en este PR)

1. Nicolás revisa esta propuesta, ranking de features.
2. Si aprueba: abrir issue por feature con criterios de aceptación.
3. Iniciar S78 con F1+F2+F5 (lote "Vista panorámica").
4. Cada PR: skill `writing-plans` previa, TDD donde aplique, `verification-before-completion`
   antes del merge, validación visual GH Pages post-deploy.

---

**Resumen ejecutivo (1 línea)**: el feature pedido por Nicolás es la **vista panorámica multi-volcán
(F1)**, complementado por **sombreado dinámico por umbrales MIROVA (F2)** y **tags de región
N→S (F5)** — total ~5-6h para el sprint S78.
