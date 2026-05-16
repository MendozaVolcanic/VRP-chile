# Workflow de búsqueda profunda y descarga de literatura

> Documento **genérico, cross-project**. Pensado para consolidarse después con
> aprendizajes de otros proyectos (OpenVIS, Goes, Valles, Automatización web)
> en una guía maestra fuera de los proyectos individuales.
>
> Base inicial: lecciones acumuladas en VRP Chile (S13–S46, abril–mayo 2026)
> sobre búsqueda y procesamiento de papers MIROVA / térmica satelital.
> Última revisión: 2026-05-16.

---

## 0. Principio rector

**Antes de buscar afuera, agotar lo que ya está adentro.** Cada vez que se
saltó este principio en VRP Chile costó entre 30 min y una sesión completa
de trabajo (ver "Anti-patrones" §7). El orden es siempre:

1. **Local del proyecto** (`documentacion/`, `docs/`, código, comentarios).
2. **Memoria del agente** (`~memory/MEMORY.md` y archivos referenciados).
3. **Vault Obsidian** (notas resumidas de papers, conceptos, sensores).
4. **Zotero biblioteca** (PDFs linked en `claude/`).
5. **Recién entonces, online** (Scholar, Web of Science, GitHub, NASA, OSF).

Si el item está en niveles 1–4, **no consultar online**. La búsqueda online
es la última opción, no la primera.

---

## 1. Mapa de dónde vive la información (template genérico)

Todo proyecto de investigación con IA debería tener este mapa explícito
antes de empezar a buscar. Para VRP Chile el mapa es:

| Tipo | Ubicación | Qué guarda | Quién escribe |
|---|---|---|---|
| **PDFs originales** | `<proyecto>/documentacion/` | Papers completos, libros, ATBDs, user guides | Humano (descarga) |
| **Texto extraído** | `<proyecto>/documentacion/*.txt` | `pdftotext` o copy/paste de secciones críticas | IA o humano |
| **Síntesis ejecutiva** | `<proyecto>/documentacion/BIBLIOGRAPHY_SYNTHESIS.md` | Índice consolidado: bandas, umbrales, fórmulas, aplicabilidad | IA, revisado por humano |
| **Auditoría papers** | `<proyecto>/docs/PAPERS_AUDIT.md` | Qué valida cada paper / qué no / gaps abiertos | IA |
| **Drift contra papers** | `<proyecto>/docs/DRIFTS_*.md` | Divergencias código vs paper autoritativo | IA |
| **Notas Vault** | `Vault/10_Bibliografia/<subtema>/<citekey>.md` | Resumen 1 paper, frontmatter ai_generated, links | IA con plugin Zotero |
| **Memoria agente** | `~memory/reference_*.md` | Punteros estables a fuentes, reglas canónicas | IA |
| **Hipótesis log** | `<proyecto>/docs/HYPOTHESIS_LOG.md` | H1, H2… qué se probó, qué refutó | IA |

**Regla**: cuando aparezca una fuente nueva, **decidí dónde vive antes de
guardarla**. Si no encaja en ninguna categoría, primero ampliá el mapa, no
guardes en cualquier lado.

---

## 2. Búsqueda profunda — workflow end-to-end

### 2.1 Definir la pregunta antes de buscar

**Output esperado obligatorio**: una pregunta en una sola línea, con el
tipo de respuesta que buscás.

Ejemplos:
- ❌ "papers sobre VIIRS" — demasiado amplio, no sabés cuándo parar.
- ✅ "¿qué coeficiente k_MIR usa MIROVA para VIIRS I-band 375m, citando paper?"
- ✅ "¿existe paper que valide algoritmo MIROVA en volcanes andinos hidrotermales (no eruptivos)?"
- ✅ "¿hay implementación open-source pública del algoritmo de Coppola 2016a?"

Si no podés escribir la pregunta así, **no estás listo para buscar**.

### 2.2 Búsqueda local (niveles 1–4 del principio rector)

Comandos en orden:

```bash
# Nivel 1 — documentación del proyecto
find "<proyecto>/documentacion/" -iname "*<keyword>*"
grep -r "<keyword>" <proyecto>/docs/ <proyecto>/documentacion/*.md

# Nivel 2 — memoria del agente
grep -l "<keyword>" ~/.claude/projects/<slug>/memory/*.md

# Nivel 3 — Vault
find Vault/10_Bibliografia/ -iname "*<keyword>*"
grep -rl "<keyword>" Vault/10_Bibliografia/

# Nivel 4 — Zotero linked attachments
find claude/ -iname "*.pdf" -path "*<keyword>*"
```

En Claude Code: equivalente con `Glob` + `Grep`. **Siempre usar `-i` (case
insensitive)** — los nombres de archivos científicos son irregulares.

Si encontraste el item en niveles 1–4: leer ese y parar. **No seguir online**.

### 2.3 Búsqueda online — herramientas disponibles

Cuando es genuinamente necesario salir afuera:

| Herramienta | Cuándo usarla | Output esperado |
|---|---|---|
| **WebSearch** | Pregunta amplia, varias fuentes posibles, descubrir landscape | Lista de URLs + snippets — NO contenido completo |
| **WebFetch** | Tenés URL concreta, querés el contenido | Markdown del page — para abstract, tablas, referencias |
| **Agent subagent_type=general-purpose** | 2+ búsquedas encadenadas, evaluación de relevancia | Síntesis estructurada, ahorra contexto principal |
| **Agent subagent_type=Explore** | Buscar dentro de repos GitHub clonados o filesystem local grande | Solo paths/excerpts, no full reads |
| **`gh` CLI** | Buscar en GitHub (issues, PRs, code search) | Resultados estructurados |

**Reglas de uso**:

1. **Empezá con WebSearch amplio** (3-5 keywords), no con WebFetch directo,
   salvo que tengas DOI/URL ya. Costo WebSearch < costo de leer paper irrelevante.
2. **Filtros de query útiles**:
   - `site:scholar.google.com "MIROVA" "VIIRS 375m"`
   - `site:osf.io "MIROVA"`
   - `filetype:pdf "<term>"`
   - `intitle:"<exact phrase>"`
3. **Si la búsqueda devuelve >20 resultados**, refinar antes de leer. No leer todo.
4. **Para review sistemática** (ej. todos los papers de un tema), delegar a
   subagent con prompt explícito de qué incluir/excluir. Ejemplo de prompt
   bueno está en `documentacion/literature_review_vegetation_indices_volcanic_precursors.md`.

### 2.4 Filtrado de relevancia (antes de descargar)

Antes de descargar un paper, contestá las 3 preguntas:

1. **¿Aporta algo que no tenga ya en la síntesis bibliográfica?**
   - Si lo que aporta es un umbral, fórmula, dataset, o validación cuantitativa
     novedosa → SÍ.
   - Si es review/survey de cosas que ya tengo → probablemente NO.
2. **¿La autoría es confiable para mi caso de uso?**
   - Ver §5 "Regla de canonicalidad de autores".
3. **¿Está en idioma/formato accesible?**
   - PDF inglés/español OK. Chino sin traducción → costo > beneficio.

Si las 3 son sí, descargar. Si no, anotar en `tasks/backlog_papers.md` con
razón "no descargado: <motivo>" — útil para volver si cambia el contexto.

### 2.5 Descarga y ubicación

Tres caminos según el origen:

**(a) Paper con DOI publicado** → Zotero plugin "Add by identifier":
- Genera entrada con citekey (Better BibTeX, ej. `coppola2016mirova`).
- PDF queda como **linked attachment** en el árbol `claude/` (NO copiado a
  Zotero storage — usa la base directory configurada).
- Para VRP Chile, el linked attachment usual queda en
  `Volcanologia/Papers/` o similar.

**(b) Paper sin DOI estable o preprint** → descarga manual:
- Guardar en `<proyecto>/documentacion/` con nombre descriptivo
  (`autor_año_tema.pdf`).
- Si es texto extraído con copy/paste, guardar también como `.txt` con
  mismo basename.

**(c) Reporte técnico, ATBD, user guide** → `<proyecto>/documentacion/`
con nombre oficial del producto (ej. `MODIS_L1B_ATBD_C7.pdf`).

**Regla anti-duplicación**: antes de guardar, verificar por **hash MD5**
que no es duplicado de algo ya presente. VRP Chile S13 detectó que
`coppola2015.pdf` y `sp426.5.pdf` eran el mismo PDF — solo diferían en
filename (online date vs print date).

### 2.6 Extracción a texto plano (opcional pero recomendado)

Para papers que vas a referenciar repetidamente o citar verbatim:

```bash
pdftotext -layout paper.pdf paper.txt
```

Ventaja: `Grep` corre 1000× más rápido sobre `.txt` que sobre PDF. Para
search "qué umbral usa X paper en sección Y" → la diferencia es 200ms vs
3 min de scan visual del PDF.

Alternativa moderna en Claude Code: usar la skill **markitdown** (auto-invocada
antes de Read sobre PDF) — convierte PDF a Markdown limpio, ahorra 50–80%
tokens vs leer el PDF crudo.

---

## 3. Síntesis — qué guardar del paper

Tres niveles de detalle según relevancia:

### 3.1 Síntesis ejecutiva (`BIBLIOGRAPHY_SYNTHESIS.md` del proyecto)

Para papers **core** del proyecto (algoritmo principal, validación crítica).
Estructura por entrada (ver el de VRP Chile como referencia):

```markdown
### <Autor año short> — <título corto>
- **PDF**: `documentacion/<filename>.pdf`
- **Rol**: <una línea de qué aporta>
- **Valida**: <umbrales, fórmulas, números duros con cita de página>
- **NO aborda**: <gaps>
- **Aplicabilidad a <proyecto>**: <conexión concreta>
```

Una entrada toma ~10-30 líneas. **Numerar fórmulas y citar página** siempre.

### 3.2 Nota Vault Obsidian (`Vault/10_Bibliografia/<subtema>/<citekey>.md`)

Para papers que querés revisitar conceptualmente. Frontmatter obligatorio
(ver `Vault/CLAUDE.md` líneas 73-91):

```yaml
---
ai_generated: true
confidence: high | medium | low
explored: 2026-05-16
source: <citekey | URL>
---
```

Contenido: TL;DR 2-3 líneas → por qué interesa → 4-6 bullets de notas clave
con emojis semánticos → conexiones `[[]]`.

Workflow paso a paso documentado en `Vault/CLAUDE.md` líneas 138-219.

### 3.3 Auditoría detallada (`<proyecto>/docs/PAPERS_AUDIT.md`)

Cuando hay drift entre código del proyecto y paper autoritativo, escribir
**por paper**:
- Qué valida del código actual (con cita de paper).
- Qué deja **abierto** (gap explícito).
- Hipótesis derivada para H-log.

Ejemplo bien hecho: `docs/PAPERS_AUDIT.md` líneas 1-50 (VRP Chile S17).

---

## 4. Cierre del loop — memoria y reglas

Cada paper procesado debe disparar:

1. **Update `BIBLIOGRAPHY_SYNTHESIS.md`** con entrada nueva.
2. **Update `~memory/reference_*.md`** si establece regla canónica nueva
   (ej. "k_MIR para sensor X = N según paper Y").
3. **Update `MEMORY.md` index** (línea ≤150 chars, formato `- [Titulo](file.md) — hook`).
4. **Update `docs/HYPOTHESIS_LOG.md`** si refuta/confirma hipótesis abierta.
5. **Si el paper revela drift**: documentar en `docs/DRIFTS_*.md` con plan
   de A/B o decisión "no aplicar".

**No publicar conocimiento nuevo en código sin estos updates**. El código
sin trazabilidad bibliográfica es deuda científica.

---

## 5. Regla de canonicalidad de autores (lección S26)

**No todos los papers del mismo país/idioma representan la misma escuela.**
En VRP Chile esto costó 10 sesiones citando Di Bella 2024 como autoridad
MIROVA cuando es de un grupo competidor (INGV Catania, sistema RSDF).

**Template generalizable** — al inicio de cualquier proyecto, listar:

| Grupo target (autoridad) | Grupo confundible (NO autoridad) | Cómo distinguir |
|---|---|---|
| <ej. MIROVA = Torino + Firenze + Roma> | <ej. INGV Catania, CNR Potenza> | Afiliación en footer paper, no nombre país |

Para VRP Chile la lista está en `~memory/reference_papers_mirova_canonical.md`.
Para un proyecto nuevo, generarla en la primera review sistemática y
mantenerla viva.

**Regla operacional**: antes de citar un paper como autoridad metodológica,
abrir el PDF y leer "Affiliation" en la primera página. Si no matchea el
grupo target → marcarlo como "referencia comparativa" no como "autoridad".

---

## 6. Reglas duras (no negociables)

1. **No adivinar valores físicos**. Si el paper no menciona el número, no
   inventarlo. Marcar `confidence: low` y "no queda claro en texto".
2. **No extrapolar del abstract solo**. Abstract = filtro de descarte, no
   fuente de extracción. Si no leíste métodos/resultados, marcar la nota.
3. **Citar página/sección/figura** en toda afirmación específica.
4. **Verificar el filename ≠ identidad del paper**. Usar hash MD5 o leer
   primera página antes de asumir que tenés 2 papers distintos.
5. **No re-fetchear data que ya está local**. Verificar `data/` y `documentacion/`
   antes de cualquier download.
6. **Idioma del paper ≠ idioma de la nota**. Notas siempre en español para
   Nicolás (geólogo SERNAGEOMIN), aunque el paper sea inglés.
7. **Validar antes de cerrar**. Si la conclusión de la búsqueda contradice
   memoria existente, **antes de overwrite** verificar la memoria (puede
   estar stale, puede ser correcta — no asumir).

---

## 7. Anti-patrones documentados (lecciones empíricas)

Cada uno costó tiempo real. Documentados para no repetirlos en proyectos futuros.

### AP1 — Saltarse búsqueda local (S36, costo 1h)

> Busqué Coppola 2016a SP426.5 online cuando el PDF estaba en
> `documentacion/sp426.5.pdf` desde abril, sintetizado en
> `BIBLIOGRAPHY_SYNTHESIS.md` desde S13.
> Concluí falsamente "no podemos implementar sin paper".

**Cura**: ejecutar §2.2 sin excepciones, **siempre**. Costo 30 segundos vs
costo de saltarse 1h+.

### AP2 — Citar paper como autoridad sin verificar afiliación (S26, costo ~10 sesiones)

> Por 10 sesiones cité Di Bella 2024 §3.3 (12σ VIIRS noche) como
> "thresholds MIROVA". Di Bella es del grupo INGV Catania (sistema RSDF),
> NO MIROVA. Auditoría S26 detectó 13 papers más confundibles.

**Cura**: §5 — leer "Affiliation" antes de citar como autoridad.

### AP3 — Asumir paper "no disponible" por filename irregular

> `coppola2015.pdf` y `sp426.5.pdf` parecían 2 papers. Eran el mismo
> (online date 2015, print volume 2016).

**Cura**: hash MD5 + leer primera página antes de duplicar trabajo.

### AP4 — Persistencia al cierre, no in-vivo (S21 meta-lección)

> Hallazgo durante la sesión (schema gap, paper nuevo, dato) → si no se
> persiste en memoria/docs INMEDIATAMENTE, puede perderse si la sesión
> corta.

**Cura**: regla "persistencia in-vivo": apenas validás un hallazgo,
update memoria antes de seguir trabajando.

### AP5 — Búsqueda sin pregunta concreta

> "Buscar papers sobre VIIRS" → 2h leyendo cosas irrelevantes vs
> "¿k_MIR para VIIRS 375m?" → 15 min al paper Campus 2024.

**Cura**: §2.1 — pregunta antes de buscar, output esperado definido.

### AP6 — Re-derivar conocimiento existente en otro proyecto

> Proyecto A descubre regla X, no la persiste cross-project. Proyecto B
> meses después re-descubre regla X.

**Cura**: este documento + memoria cross-project. Si la regla aplica a
varios proyectos, vive en `Volcanologia/<doc maestro>.md`, no en uno
específico.

---

## 8. Checklist de auto-review (al cerrar una sesión de búsqueda)

Antes de declarar "búsqueda completa":

- [ ] La pregunta original (§2.1) tiene respuesta o gap explícito.
- [ ] Niveles locales (1–4) fueron consultados antes de online.
- [ ] PDFs descargados nuevos tienen entrada en `BIBLIOGRAPHY_SYNTHESIS.md`.
- [ ] Memoria actualizada con regla nueva si aplica.
- [ ] `MEMORY.md` index actualizado.
- [ ] Si el paper revela drift en código: documento en `DRIFTS_*.md` o
      decisión explícita "no aplicar y porqué".
- [ ] Hipótesis abiertas afectadas: update `HYPOTHESIS_LOG.md`.
- [ ] Si descubriste una regla cross-project (no específica al proyecto):
      anotar para mover al doc maestro Volcanologia/.

---

## 9. Herramientas y comandos de referencia rápida

```bash
# === Búsqueda local ===
# PDFs por nombre (case insensitive)
find <proyecto>/documentacion/ -iname "*<keyword>*"

# Contenido en sintesis bibliográfica
grep -i "<keyword>" <proyecto>/documentacion/BIBLIOGRAPHY_SYNTHESIS.md

# Memoria del agente
grep -l "<keyword>" ~/.claude/projects/<slug>/memory/*.md

# Vault notas
find Vault/10_Bibliografia/ -iname "*<keyword>*"

# === Extracción ===
pdftotext -layout paper.pdf paper.txt
md5sum *.pdf | sort  # detectar duplicados

# === Online (último recurso) ===
# Google Scholar: usar interface web o WebSearch tool
# DOI directo: WebFetch https://doi.org/<DOI>
# GitHub code search: gh search code "<term>" --language=python
# OSF dataset: WebSearch site:osf.io "<keyword>"
# arXiv: WebSearch site:arxiv.org "<keyword>"
# NASA ATBD: WebSearch "<sensor> ATBD" filetype:pdf
```

---

## 10. Consolidación futura (TODO para próximos proyectos)

Cuando este documento se consolide en doc maestro cross-project
(probablemente `Volcanologia/RESEARCH_WORKFLOW_MASTER.md` o equivalente
en `claude/`), incorporar también aprendizajes de:

- **OpenVIS** (infrasonido): cómo manejaron literatura sismo-acústica,
  cuánto reutilizable.
- **Goes / Valles** (placeholders): qué workflow tienen previsto.
- **Automatizacion web**: 8 subproyectos de scraping institucional —
  ¿tienen patrón de research propio?
- **Vault `00_Meta/proyectos.md`**: índice maestro de cross-linking ya
  existe — el doc consolidado debería referenciar esto, no duplicarlo.

**Pendiente al consolidar**: decidir qué partes son verdaderamente
cross-project vs cuáles son específicas de proyectos de monitoreo
satelital. La sección §5 (autoría canónica) por ejemplo es genérica;
los nombres concretos (MIROVA, INGV) son específicos de VRP Chile.
