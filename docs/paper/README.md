# Manuscrito VRP Chile — cómo se trabaja esta carpeta (S135)

**Revista decidida**: Volcanica (diamond OA; decisión S120, `../PAPER_VRP_CHILE_DRAFT_S72.md` §0).
**Idioma del manuscrito**: inglés. **Idioma de las notas al editor**: español de Chile.

## Regla única de números (S91 + A90)

Ningún número del manuscrito se escribe a mano. El texto lleva `[NUM: clave]` y las tablas
se regeneran con:

```bash
python scripts/paper_numbers.py --tests
```

que produce `numbers.json` (todas las claves, con la **definición** dentro) y `TABLAS.md`
(Tablas 2, 3 y 4 en markdown). Si una sección necesita un número que el script no produce,
se agrega la clave al script primero y recién después se cita. La ventana por defecto es
2026-01-01 → último record; el JSON registra el `git_head` con el que se generó.

## Archivos

| archivo | qué es | estado |
|---|---|---|
| `../PAPER_VRP_CHILE_DRAFT_S72.md` | esqueleto anotado + decisiones §0 + roadmap §C | vigente para §0-§3, §6-§12; §4-§5 quedan reemplazados por los archivos de abajo |
| `sec4_background.md` | §4 Background: el algoritmo MIROVA, prosa | borrador S135 (agente redactor + revisión) |
| `sec5_methods.md` | §5 Methods: la implementación, prosa | borrador S135; 1 placeholder (`n_tests_collected`, ya disponible en `numbers.json`) |
| `sec6_validation.md` | §6 Validation: recall, paridad y por qué no se reporta precisión | borrador S135; 1 placeholder |
| `numbers.json` · `TABLAS.md` | salida del script | regenerar antes de cada revisión |

Cada párrafo de las secciones lleva al final un comentario `<!-- src: archivo:línea -->` con la
fuente de lo que afirma. Las `## Notas para el editor` al pie de cada sección listan lo que el
redactor no pudo verificar: hay que resolverlas antes de pasar la sección a «revisada».

## Orden acordado (S135, con Nicolás)

1. ✅ Script único de números (`scripts/paper_numbers.py`, 6 tests).
2. ✅ §4 y §5 redactados desde `MIROVA_DIVERGENCES.md`, `BIBLIOGRAPHY_SYNTHESIS.md`,
   `FICHA_SDA_VRP_CHILE.md` y `sp426_5.txt` (pendiente: revisión de Nicolás).
3. ✅ §6 Validation redactada desde `TABLAS.md` (pendiente: revisión de Nicolás; el punto más
   discutible es no reportar precisión, y está argumentado en el propio texto).
4. ⬜ §3 Introduction, §7 casos, §8 Discussion, §9 Conclusions.
5. ⬜ Figuras (12+), referencias con DOI (`.bib`), coautores, disclosure IA.
