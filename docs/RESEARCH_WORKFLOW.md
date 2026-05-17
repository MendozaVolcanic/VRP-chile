# Workflow de búsqueda profunda — específico VRP Chile

> **Este documento es la capa específica del proyecto.** Para la metodología
> general (workflow end-to-end, APIs gratis, descarga por editorial, verificación
> magic bytes, anti-patrones cross-project, templates), leer primero la guía maestra:
>
> 📚 [`C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_INVESTIGACION.md`](../../../GUIA_MAESTRA_INVESTIGACION.md)
>
> La maestra consolida lecciones de 4 proyectos (Copernicus-v1, VRP Chile, Papers/Educación, Recuperación). Saltarla typicamente cuesta 1h+ por sesión.
>
> Acá solo está lo que **es exclusivo de VRP Chile** y no aplica a otros proyectos.

---

## 1. Mapa de información del proyecto

| Tipo | Ubicación | Qué guarda |
|---|---|---|
| **PDFs originales** | `VRP Chile/documentacion/` | Papers MIROVA, ATBDs MODIS/VIIRS, user guides, libros |
| **Texto extraído** | `VRP Chile/documentacion/*.txt` | `pdftotext` o markitdown de secciones críticas |
| **Síntesis ejecutiva** | `VRP Chile/documentacion/BIBLIOGRAPHY_SYNTHESIS.md` | **Source of truth bibliográfico** (429 líneas, 30/60 PDFs cubiertos) — leer ANTES de buscar online |
| **Auditoría papers** | `VRP Chile/docs/PAPERS_AUDIT.md` | Qué valida cada paper / qué no / gaps |
| **Drifts código vs paper** | `VRP Chile/docs/DRIFTS_*.md` | Divergencias detectadas |
| **Hipótesis log** | `VRP Chile/docs/HYPOTHESIS_LOG.md` | H-IDs, qué se probó/refutó |
| **Notas Vault** | `Vault/10_Bibliografia/termico/` | Resúmenes 1 paper, frontmatter `ai_generated` |
| **Memoria agente** | `~/.claude/projects/.../memory/reference_papers_*.md` | Reglas canónicas MIROVA |

Para el orden de consulta (local antes que online), ver guía maestra §1.

---

## 2. Canonicalidad de autores MIROVA (regla VRP Chile específica)

**Esta es la lección más cara que pagó el proyecto: 10 sesiones (S16–S26)
citando Di Bella 2024 como "thresholds MIROVA" cuando es INGV Catania.**

### 2.1 Listas canónicas

✅ **MIROVA = grupo autoridad** (Torino + Firenze + Sapienza Roma):
- Coppola (Diego) — autor principal MIROVA, Università di Torino
- Laiolo (Marco)
- Massimetti (Francesco)
- Campus (Adele)
- Aveni (Sofia)
- Cigolini (Corrado)

❌ **NO MIROVA aunque sean italianos**:
- **INGV Catania** → sistemas RSDF / V-STAR / FastVRP / CNN: Del Negro, Corradino, Di Bella, Torrisi, Cariello, Amato, Malaguti
- **CNR-IMAA Potenza** → sistema NHI: Marchese, Pergola, Genzano, Filizzola

### 2.2 Cómo distinguir antes de citar

1. Abrir PDF, leer "Affiliation" en primera página
2. Si la afiliación es Università di Torino / Firenze / Sapienza Roma → autoridad MIROVA
3. Si es INGV Catania o CNR-IMAA → sistema **competidor**, usar como "referencia comparativa", NO como "thresholds MIROVA"

Lista completa en `~/.claude/projects/.../memory/reference_papers_mirova_canonical.md`
(13 papers no-MIROVA confundibles documentados).

---

## 3. Lecciones de sesión específicas VRP Chile

Las anti-patrones generales están en la guía maestra §10 (AP1-AP13).
Acá solo lo que es **específico a la trayectoria de este proyecto**:

### S36 (2026-05-11) — Búsqueda online de Coppola 2016a SP426.5
Busqué el paper online cuando estaba en `documentacion/sp426.5.pdf` **desde abril**,
sintetizado en `BIBLIOGRAPHY_SYNTHESIS.md` desde S13. Costo 1h + falsa conclusión
"no podemos implementar sin paper". → fix: §1 maestra siempre, sin excepciones.

### S26 (2026-04-29) — Di Bella 2024 confundido con MIROVA
10 sesiones de A/B tests basados en "MIROVA usa 12σ noche VIIRS según Di Bella 2024".
Di Bella es INGV Catania (sistema RSDF). → fix: §2 acá + §6 maestra.

### S13 (2026-04-18) — Hash detecta duplicado
`coppola2015.pdf` y `sp426.5.pdf` eran el mismo PDF (online date 2015 vs print
volume 2016). → fix: `md5sum` antes de duplicar entrada en synthesis.

### S21 (2026-04-25) — Persistencia in-vivo, no al cierre
Hallazgo durante sesión (schema gap `std_bg` no persistido) que casi se pierde
al corte de contexto. → fix: persistir en `~memory/` apenas validás, antes de seguir.

---

## 4. Convenciones específicas del proyecto

### 4.1 Entrada en `BIBLIOGRAPHY_SYNTHESIS.md`

Formato canónico VRP Chile (ver §1-§9 del archivo para ejemplos):

```markdown
### <Autor año> — <título corto>
- **PDF**: `documentacion/<filename>.pdf`
- **Rol**: <una línea de qué aporta a MIROVA-equivalent>
- **Valida**: <k_MIR, thresholds N·σ, fórmulas con cita de página>
- **NO aborda**: <gaps>
- **Aplicabilidad a VRP Chile**: <conexión concreta — sensor, banda, volcán>
```

### 4.2 Tabla canónica de umbrales (§6 BIBLIOGRAPHY_SYNTHESIS)

Cualquier paper nuevo que toque umbrales por sensor debe actualizar
esta tabla. Estructura fija:

| Sensor | Banda | Res | k_MIR | A_pix (m²) | Umbrales noche |
|---|---|---|---|---|---|

Valores actuales validados empíricamente contra OSF v2.5 (error ≤0.17%):
- MODIS B21/22: k=18.9, A=1e6
- VIIRS M13: k=19.7 (Campus 2022), A=562500
- VIIRS I4: k=18.0 (Campus 2024 Vulcano), A=140625
- VIIRS I5 TIR: Stefan-Boltzmann puro

### 4.3 Cuándo actualizar drifts

Si un paper revela divergencia entre código y autoridad MIROVA:
1. Anotar drift en `docs/DRIFTS_S<N>.md` con cita exacta paper + línea código
2. Si es accionable: diseñar A/B test (ver `.github/workflows/reproc-ab-*.yml` como template)
3. Si NO es accionable (paper investigación, no operacional): documentar y dejar
4. Update `HYPOTHESIS_LOG.md` con H-ID

---

## 5. Templates específicos VRP Chile

### 5.1 Prompt para subagente buscando paper MIROVA

```
Proyecto VRP Chile (monitoreo térmico volcanes chilenos, clon MIROVA).
Necesito: <pregunta concreta una línea>.

ANTES de buscar online:
1. `find "VRP Chile/documentacion/" -iname "*<keyword>*"`
2. `grep -i "<keyword>" VRP Chile/documentacion/BIBLIOGRAPHY_SYNTHESIS.md`
3. Si encontrás algo local → reportar y parar.

Si NO está local:
- Priorizar autores MIROVA canonical: Coppola, Laiolo, Massimetti, Campus, Aveni
- NO citar como autoridad MIROVA: Del Negro, Corradino, Di Bella (INGV Catania), Marchese, Pergola (CNR Potenza)
- APIs gratis primero (Crossref, Semantic Scholar, arXiv) antes de Perplexity

Output: <300 palabras. Si paper encontrado, dar DOI + dónde está OA si aplica.
```

### 5.2 Triaje para descarga (VRP Chile-specific)

Antes de bajar un paper nuevo de remote sensing volcánico:

1. **¿Es del grupo MIROVA?** → Sí: bajar siempre. No: aplicar criterio normal.
2. **¿Aporta umbral / k_MIR / fórmula numérica?** → Sí: bajar + entrada synthesis.
3. **¿Valida sobre volcán chileno o andino?** → Sí: prioridad alta (Lascar, Villarrica, NdC, Lastarria, PCC).
4. **¿Sensor del pipeline?** (MODIS B21/22, VIIRS I4/I5, VIIRS M13/M15) → Sí: bajar.
5. **¿Solo abstract en inglés sin acceso al full text?** → Anotar en backlog, no insistir.

---

## 6. Mantenimiento

Cuando descubras una regla **que aplique solo a VRP Chile**: agregar acá.

Cuando descubras una regla **cross-project** (aplica a OpenVIS, Goes, Papers, etc.):
agregar a la guía maestra `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_INVESTIGACION.md`,
no acá.

Regla: si una lección termina con "esto pasa también en otros proyectos satelitales",
va a la maestra. Si termina con "esto es de la trayectoria S<N> de VRP Chile",
va acá.

---

## 7. Referencias rápidas

- **Source of truth bibliográfico**: `documentacion/BIBLIOGRAPHY_SYNTHESIS.md`
- **Lista canónica autores**: `~/.claude/projects/.../memory/reference_papers_mirova_canonical.md`
- **Apunte memoria a synthesis**: `~/.claude/projects/.../memory/reference_bibliography_synthesis.md`
- **Hipótesis activas**: `docs/HYPOTHESIS_LOG.md`
- **Auditoría papers**: `docs/PAPERS_AUDIT.md`
- **Drifts conocidos**: `docs/DRIFTS_S17.md`, `docs/MIROVA_DIVERGENCES.md`
- **Guía maestra cross-project**: `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_INVESTIGACION.md`
- **Skill auto-invocable**: `investigacion` (instalado en `~/.claude/skills/investigacion/`)
