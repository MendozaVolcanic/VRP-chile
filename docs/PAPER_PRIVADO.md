# El manuscrito del paper es privado (S173)

Desde el 2026-11-05 (S173) el manuscrito del paper de VRP Chile ya no vive en este repo público.
Lo decidió Nicolás: el texto es un borrador sin publicar y su lugar es un repo privado, no el
repo público del sistema (el razonamiento detallado de la decisión no está escrito acá).

- **Dónde está**: repo privado `MendozaVolcanic/vrp-chile-paper`, carpeta `manuscrito/`
  (las revisiones van en `revisiones/`). Copia local:
  `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/paper_vrp_chile/`.
- **Qué salió de acá**: `docs/paper/` (README.md, TABLAS.md, numbers.json, sec4_background.md,
  sec5_methods.md, sec6_validation.md) y `docs/PAPER_VRP_CHILE_DRAFT_S72.md`.
- **Lo que queda acá**: `scripts/paper_numbers.py`, que recalcula los números del manuscrito desde
  `data/`. Su salida por defecto es ahora la carpeta del repo privado
  (`../paper_vrp_chile/manuscrito/`); no se vuelve a escribir en este repo.
- **Lo ya publicado no se borró**: todo lo que estuvo en este repo sigue en el historial de git
  (por ejemplo, `git show 84d3a4581:docs/paper/sec5_methods.md`, último `main` con el manuscrito
  antes de este cambio). Sacarlo del árbol no lo retira de lo que ya fue público.
- Los documentos históricos que citan `docs/paper/...` (auditorías, bloques de arranque, bitácora)
  se dejan como están: describen dónde estaba el texto en su momento.
