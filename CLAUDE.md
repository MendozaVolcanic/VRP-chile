# VRP Chile

Sistema VRP independiente para volcanes chilenos (equivalente MIROVA, propio).
Repo: https://github.com/MendozaVolcanic/VRP-chile

## Integración con el vault Obsidian

Las notas de papers, conceptos, volcanes y sensores que se usan en VRP Chile
viven en el vault Obsidian: `C:\Users\nmend\OneDrive\Escritorio\claude\Vault\`.

- **Procesar papers**: ver `..\..\Vault\CLAUDE.md` sección "Workflow de procesamiento
  de papers". Invocación típica: "procesá el paper coppola2016fifteen" o
  "procesá todos los papers de VRP Chile". Claude aplica el workflow documentado
  sin necesidad de prompt adicional.
- **Índice de proyectos** (para cross-project linking de papers):
  `..\..\Vault\00_Meta\proyectos.md`.
- **Convenciones del vault** (kebab-case, frontmatter `ai_generated`/`confidence`/
  `explored`, links `[[]]`, tags jerárquicos): ver `..\..\Vault\CLAUDE.md`.

## Reglas científicas (no negociables)
- **VRP MIR (Wooster)** por sensor, coeficientes **empíricamente validados S14
  contra MIROVA v2.5 OSF (error ≤0.17% sobre 48,360 filas)**:
  - MODIS 1 km (B21/22): `k = 18.9 × A_pix(1e6)` = **18,900,000** (`WOOSTER_COEFF=18.9`)
  - VIIRS M-band 750m (M13): `k = 1.97×10⁷ × A_pix(km²)` = **11,081,250** (`WOOSTER_COEFF=19.7`)
  - VIIRS I-band 375m (I4): `k = 18.0 × A_pix(140625)` = **2,531,250** (`WOOSTER_COEFF=18.0`)
  - MIROVA usa **A_pix nadir fijo** (sin corrección zenithal) para los 3 sensores.
  - NO usar Di Bella 2024 k=2.48×10⁷ para VIIRS 375m — no reproduce OSF (empírico).
- **VRP TIR (I05)**: Stefan-Boltzmann (Aveni 2025 GRL, `σ = 5.67×10⁻⁸`).
- **NTI**: umbral 3σ sobre background, mínimo 0.005.
- **MIR solo nocturno** (contaminación solar diurna).
- Bandas: MODIS 21/22 (3.929/3.959 μm) + 31 (11 μm TIR),
  VIIRS I04 (3.74 μm) / I05 (11.45 μm), VIIRS M13 (4.05 μm) / M15 (10.76 μm).
- Constantes físicas **exactas** de los papers, nunca aproximar. Citar paper en cualquier cambio metodológico.
- Si dudas de un método con datos geofísicos, **dilo** — nunca adivines.

## Reglas geométricas S14 (MIROVA-equivalent)
- **`radius_km = 25 km` uniforme** para volcanes chilenos — replica grilla
  MIROVA UTM 51×51 km (radio inscrito 25.5 km).
- **`inner_radius_km` por volcán** (valores oficiales MIROVA de los KML):
  | Volcán | inner | Volcán | inner |
  |---|---|---|---|
  | Lastarria | 3 | Lascar, Isluga, NdC, Llaima, Villarrica, Chaiten | 5 |
  | Planchón-Peteroa | 3 | Tupungatito | 7 |
  | Copahue | 4 | PuyehueCordonCaulle | **20** |
- **Esquema dual "detectar amplio + clasificar visual"**: detecciones dentro
  de `inner_radius_km` → `distance_class="summit"` (rojo, anomalía real).
  Fuera → `"far"` (gris, posible lejana). **No se filtran**, se clasifican.
- **Campo unificado `final_hotspot_lat/lon/dist_km`** con fallback
  eruption→vent. El dashboard y las auditorías usan **solo** este campo, no
  `hotspot_*` o `vent_hotspot_*` por separado.

## Reglas operacionales S14 (aprendizajes)
- **A1. Calibración empírica > derivación teórica**: cuando haya data pública
  del mismo grupo (OSF, Zenodo), calcular coeficientes empíricos antes de
  confiar en un número de paper. Resolvió en 1 min discrepancia Di Bella vs
  Laiolo que ocupó un mes de discusión teórica.
- **A2. Diagnósticos paralelos antes de reprocesos caros**: agotar análisis
  sobre data ya en disco antes de descargar más. Paso 0+1a+diagnósticos
  A/B/D resolvieron 80% de dudas sin fetch. Solo entonces tiene sentido
  reprocesar.
- **A3. Campos "distance" en schema deben documentar desde qué punto miden**:
  `hotspot_dist_km` se medía desde `volcano_lat/lon` (centro) no desde el
  vent. Ahora `final_hotspot_dist_km` unifica y documenta.
- **A4. MIROVA es arquitecturalmente más simple que lo que creíamos**:
  no hay máscaras geométricas ni radios adaptativos. Es grilla UTM 51×51 +
  NTI/ETI/contextual (Coppola 2016a) + clasificación visual post-detección.
  La complejidad está en los umbrales, no en la geometría.
- **A5. Los valores MIROVA oficiales (KML, OSF) son datos no opiniones**:
  usarlos tal cual es más defendible que inventar umbrales. Solo divergir
  con experimentos propios y en el perfil `experimental`, no en
  `mirova_equivalent`.

## Regla de comunicación con Nicolás
**Explicar como geólogo, no como programador.** Cuando discutas resultados, bugs,
decisiones de umbrales, o cambios metodológicos:

1. **Primero el fenómeno físico**: qué está pasando realmente en el volcán, el
   pixel del satélite, la atmósfera, el background. Describirlo en lenguaje natural
   — "el cráter mantiene calor residual después del atardecer y produce un gradiente
   térmico local", "la nube fina alta enfría el background porque irradia desde
   -40°C", "el pixel VIIRS de 375m mezcla roca caliente con nieve y el promedio queda
   en valores intermedios".
2. **Después el mecanismo del pipeline**: cómo el código interpreta ese fenómeno,
   qué umbrales lo filtran, qué paths lo capturan. Explicar por qué esa elección de
   código tiene o no tiene sentido frente al fenómeno físico.
3. **Recién al final, si aplica, los números y fórmulas**, y solo los estrictamente
   necesarios para apoyar el razonamiento. Nunca empezar por la fórmula.
4. **El "por qué" antes del "cómo"**. Si hay un trade-off científico (por ejemplo
   falsos positivos vs falsos negativos en monitoreo volcánico), nombrarlo
   explícitamente y decir cuál es el costo de cada lado.
5. **Tablas comparativas y métricas agregadas sí**, son útiles. Pero las derivaciones
   matemáticas largas, constantes de Planck, conversiones de radiancia — esas viven
   en los papers y en los comentarios de código, no en la conversación con Nicolás.
6. **Nunca adivinar** un valor físico o un dato instrumental. Si no sabés el ΔT real
   de un volcán, dilo y andá a mirarlo antes de proponer un umbral.

## Arquitectura
- `pipeline/`: fetch.py (earthaccess), process_modis.py, process_viirs.py, process_viirs_mod.py, store.py, scan_geometry.py
- `frontend/index.html` (Chart.js + Leaflet, GitHub Pages)
- `volcanoes.yaml` (45 configurados, 11 con data, 34 sin pull)
- `.github/workflows/nrt.yml` (cron 6h)
- `data/` JSON por volcán (committed). Raw L1B/HDF **nunca** committed.

## Skill triggers (invocar proactivamente)

Claude debe invocar `Skill` sin que Nicolás lo pida cuando el tipo de trabajo
encaje con la tabla. Esto es vinculante, no opcional.

| Situación | Skill a invocar | Por qué |
|---|---|---|
| Cualquier bug, FP/FN inesperado, anomalía en auditoría, "no entiendo por qué pasa esto" | `systematic-debugging` o `superpowers-systematic-debugging` | Forzar hipótesis → evidencia → root cause, no "miro y opino" |
| Antes de escribir fix que toque `pipeline/` con >20 líneas de cambio | `writing-plans` | Plan formal con criterios de aceptación y reversión antes de tocar código |
| Ejecutar un plan ya escrito paso a paso | `executing-plans` | Checkpoints y no saltarse pasos |
| Antes de editar `pipeline/process_*.py` o `scan_geometry.py` | `test-driven-development` | Primero el test que captura el bug, después el fix |
| Antes de declarar un fix "listo", pushear a main, o cerrar un RF | `verification-before-completion` | Re-audit obligatoria sobre Tier A completo antes del push |
| 2+ investigaciones independientes que se pueden hacer en paralelo (ej. RF1 en Lascar + RF2 en MODIS a la vez) | `dispatching-parallel-agents` | Paralelismo real vía subagentes, no serie |
| Nicolás pide "automatiza X", "cada vez que Y", "antes de Z hacé W" | `update-config` | Esto es un hook, no una instrucción conversacional |
| Cualquier trabajo con HDF/NetCDF/DataFrames grandes de records satelitales | `pandas-pro` | Operaciones vectorizadas correctas, no loops |
| Antes de correr una auditoría que requiere perfilar/memoria | `python-performance-optimization` | Si el audit script tarda >5 min, perfilarlo antes de "optimizar a ojo" |
| Diseñar un nuevo experimento (`experiments/NN_*.py`) | `writing-plans` + `test-driven-development` | Mismo rigor que código de producción |
| Cerrar sesión con learnings nuevos | `revise-claude-md` | Consolidar lecciones en CLAUDE.md y memoria |

**Regla meta**: si estoy por hacer algo y hay una skill listada arriba que
aplica, la invoco **antes** de actuar. Si dudo si aplica, la invoco igual —
el costo de invocar de más es bajo, el costo de saltarla es un fix mal hecho.

## Glosario obligatorio (usar estos términos siempre en discusiones de resultados)

Pensá la auditoría como un examen donde MIROVA es la hoja de respuestas y nuestro
pipeline es el alumno. Cada noche-satélite de cada volcán es una pregunta.

- **TP (True Positive)** — MIROVA detectó anomalía térmica esa noche y nosotros
  también. Acertamos: hay actividad real y la vimos.
- **FP (False Positive)** — Nosotros detectamos, MIROVA no. Ejemplos físicos
  típicos: lago que retiene calor post-atardecer, nube fina que deforma el
  background, ruido sobre nieve parcial. "Grito de fuego" sin fuego.
- **FN (False Negative)** — MIROVA detectó, nosotros perdimos. **Lo más grave en
  monitoreo**: un evento real sin alerta. Típico en señales sub-pixel (lava lake
  Villarrica, 0.05–0.2 MW) que MIROVA ve integrando ROI completo.
- **TN (True Negative)** — Ambos coinciden en que no hay nada. No se tabula.

Métricas derivadas:
- **Precision** = TP / (TP+FP). De lo que gritamos, cuánto era real. Baja =
  ruido de falsa alarma, operador deja de confiar.
- **Recall** = TP / (TP+FN). De lo real, cuánto detectamos. Baja = perdemos
  eventos. **Para `mirova_equivalent` priorizamos recall sobre precision**.
- **F1** = media armónica de ambas. Un solo número para comparar.
- **Ratio ours/mirova** = VRP nuestro / VRP MIROVA en la misma noche. 1.0 =
  calibración perfecta. Mediana sobre muchas noches = sesgo sistemático.

Conceptos de detección:
- **Tier A/B/C** — A ≥30 refs MIROVA (calibración), B 5–29 (corroboración), C <5
  (solo NRT, no calibramos).
- **vent-path** — detecta un solo pixel del cráter cuando supera background
  (señal débil persistente). Más sensible, menos específico.
- **eruption-path** — requiere clúster de varios pixels (señal fuerte). Más
  específico, ciego a sub-pixel.
- **σ_bg** — desvío estándar de T en el anillo de fondo. Se infla con terreno
  heterogéneo (nieve parcial, orografía) y rompe gates `N·σ`.
- **Path A / B / C** — A=umbral BT clásico; B=NTI absoluto (>-0.8);
  C=NTI relativo (supera 3σ local, S11+).

## Regla de publicación en dashboard (obligatorio)

Cualquier cambio que modifique detecciones (nuevo perfil, ajuste de umbral,
reproceso masivo, fix en pipeline/) **debe reflejarse en el dashboard antes
de declarar el trabajo completo**. Flujo:

1. Correr el reproceso/fix.
2. Commit + push del JSON bajo `data/mirova_equivalent/`.
3. Verificar que GitHub Pages publicó la nueva data (o que el JSON local abrió
   correctamente en el dashboard) antes de cerrar el tema.
4. Si el cambio es solo del perfil `experimental`, mencionarlo explícitamente
   y no contaminar la vista operacional.

El dashboard es el entregable final para Nicolás/SERNAGEOMIN. Auditoría en
stdout es trabajo interno — no cuenta como resultado hasta que es visible.

## Regla de delegación a subagentes (control de contexto)

Para minimizar compactaciones automáticas ("session continued..."):

- **Lecturas exploratorias** de archivos >500 líneas o de múltiples archivos
  relacionados → delegar a `Explore` subagent con pedido de resumen <500 tokens,
  no cargar el archivo completo al contexto principal.
- **Salidas de auditoría largas** (>200 líneas stdout) → leer directamente el
  JSON del snapshot (`experiments/audit_s*/Volcano.json`) en vez de reimprimir
  el stdout crudo.
- **Investigaciones paralelas** (2+ volcanes independientes, 2+ RF a la vez)
  → `dispatching-parallel-agents`, cada rama en su propio contexto.
- **Estado entre sesiones** → memoria (`MEMORY.md` + archivos) en vez de
  re-derivar al inicio de cada sesión.
- No re-leer archivos ya leídos en la misma sesión salvo que haya cambio
  observable.

## Constraints técnicos
- **pyhdf roto en Windows** → MODIS solo corre en GitHub Actions Linux.
- NASA LANCE NRT ~3h latencia.
- NOAA-20: buscar v2 **y** v2.1 (disponibilidad variable).
- Secrets en GitHub: EARTHDATA_USERNAME, EARTHDATA_PASSWORD.
- **NRT vs Standard L1B**: fetch.py intenta Standard primero, cae a `_NRT`
  (LANCE). Records llevan `product_version: "standard"|"nrt"`. store.py
  auto-upgrade NRT→Standard. Delta BT <0.1K, despreciable para VRP.
- **Encoding Windows**: scripts Python que imprimen Unicode (σ, →, ✓) deben
  usar `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`.
- **volcanoes.yaml**: `yaml.safe_dump` destruye comentarios. Preferir `Edit`
  tool para cambios puntuales, no rewrite completo con Python.
- **GitHub Actions**: repo público = minutos ilimitados. Matrix 45 volcanes,
  max-parallel=8, fail-fast=false, cron cada 2h. Timeout 25 min/step puede
  ser corto para reprocess full history (NdC timeout recurrente).
- **Radios geofencing MIROVA-OVDAS**: cada volcán tiene radius_km propio
  (3-15 km). store.py usa `max_hotspot_dist_km` per-volcano, no global 5km.
  Refs: https://github.com/MendozaVolcanic/Mirova-v1
- **Refs MIROVA son NRT**: los CSV consolidado/OCR scrapeados de mirovaweb.it
  contienen datos NRT. Comparar contra NRT es operacionalmente correcto.
  OCR cubre ~80% VIIRS, MODIS completo. No re-scrapear para homogeneizar.
- **Frontend chart gotcha**: VIIRS 375m debe usar `vrp_mw` (filtrado), no
  `vrp_mir_mw` (pre-filtro). Bug S12: barras fantasma de detecciones
  descartadas por geofencing.

## Estado
**S14 en curso (2026-04-21) — fix geometría MIROVA-equivalent SIN COMMITEAR.**
Leer `tasks/status_s14_handoff.md` al arrancar próxima sesión. Cambios pendientes:
radius_km=25 uniforme + inner_radius_km oficial MIROVA + schema unificado
final_hotspot_* + distance_class + WOOSTER_COEFF 19.7 VIIRS_M + dashboard con
About/credits + CLAUDE.md actualizado. OSF v2.5 descargada en
`data/mirova_reference/` (no commitear 98 MB). Validación empírica coeficientes
(error ≤0.17%) en `experiments/21_results.json`.

**S12 baseline (2026-04-16)**: 45 volcanes operacionales, 11 con refs MIROVA
(14042026 consolidado, 494 refs). Auditoría contra MIROVA:
- Recall top: Chaitén 87%, Lastarria 85%, Tupungatito 83%, PCC 82%.
- Lascar (Tier A): recall 55%, precision OCR-adj 0.69, ratio 1.11.
- Villarrica 0% recall: gap arquitectural, requiere Test 1 integrado-ROI
  (plan en `tasks/plan_s13_test1_integrated_roi.md`).
- FPs principales: vent-only detecciones sub-MIROVA-threshold (0.1-1 MW).
- Experimental prueba `min_vent_pixels=2` (E4): −39% FPs vs meq.
- Leer `tasks/status_s12_overnight.md` y `tasks/todo.md` para pendientes.
- Coords de vent actualizadas por Nicolás (campo): PCC lacolito, Chaitén
  domo, Villarrica lava lake, Lascar cráter V.
