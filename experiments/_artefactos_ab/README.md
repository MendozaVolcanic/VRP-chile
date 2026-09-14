# Artefactos A/B rescatados (S139)

**Qué es.** Copia local de los artefactos de GitHub Actions de los A/B de S129, S130, S133 y S135,
bajados en S139 antes de que vencieran. Son los JSON por volcán y brazo que produjeron esos
reprocesos. La carpeta está **fuera de git** (`.gitignore`, 433 MB); sólo este README se commitea.

**Por qué importa.** GitHub borra los artefactos a los 90 días. Estos datos **no se pueden volver a
bajar** y **sólo se regeneran reprocesando** (horas de cómputo por brazo, A15). Antes de borrar esta
carpeta, confirmar que ningún análisis la necesita.

**Contenido** (172 artefactos, verificado S140 contra `INVENTARIO.tsv`):

| prefijo | cuántos | qué A/B |
|---|---|---|
| `s129ab-*` | 45 | S129, fondo y magnitud (`_s129_ab_bgmag`) |
| `s130d18-*` | 12 | S130, D18 |
| `s133area-*` | 48 | S133, área de píxel |
| `s133b22-*` | 4 | S133, banda 22 |
| `s135ab-*` | 60 | S135, A/B de cinco brazos |
| `s135-*` | 2 | S135, probe por etapas (A75) |

**Índices.**
- `INVENTARIO.tsv`: una fila por artefacto con estado de la descarga, id del artefacto, nombre, id
  del run, tamaño en bytes y fecha de vencimiento en GitHub.
- `_lista.tsv`: la lista de entrada con que se hizo la descarga.

Cada carpeta se llama `<nombre del artefacto>__run<id del run>`: el run se abre en
`https://github.com/MendozaVolcanic/VRP-chile/actions/runs/<id>`.
