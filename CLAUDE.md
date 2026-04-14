# VRP Chile

Sistema VRP independiente para volcanes chilenos (equivalente MIROVA, propio).
Repo: https://github.com/MendozaVolcanic/VRP-chile

## Reglas científicas (no negociables)
- **VRP MIR (Wooster)**: `VRP = 18.9 × A_pix × ΔL_MIR` — Coppola 2015 Eq.7. NO Stefan-Boltzmann.
- **VRP TIR (I05)**: Stefan-Boltzmann (Aveni 2024).
- **NTI**: umbral 3σ sobre background, mínimo 0.005.
- **MIR solo nocturno** (contaminación solar diurna).
- Bandas: MODIS 21/22 (3.929/3.959 μm), VIIRS I04 (3.74 μm) / I05 (11.45 μm).
- Constantes físicas **exactas** de los papers, nunca aproximar. Citar paper en cualquier cambio metodológico.
- Si dudas de un método con datos geofísicos, **dilo** — nunca adivines.

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

## Estado
Calibración de sesiones 4-5 **INVALIDADA** en sesión 8 (refs OCR-noisy + pairing débil + sin contar FPs). **No hay baseline validado** hasta terminar auditoría estricta. Leer `tasks/todo.md` antes de cualquier "fix" y `tasks/lessons.md` L7.6-L7.9 para el diagnóstico. Detalles históricos en memoria `project_vrp_chile.md`.
