# Bloque de arranque S164 (cierre de S163, coordinadora, 2026-10-26 ~01:56 a ~12:35 UTC)

Escrito el 2026-10-26 a las 12:35 UTC (servidor) sobre `loop/activo` en `ed7288c2b` (= remoto). **El estado se fijó con
trabajo en curso**: siguen corriendo las hijas `loop-modis-2`, `loop-viirs750-2` y `loop-viirs375`, y las sesiones
`d39-mirova-v1`, `instrumento-pendientes` y `diurno-k-prereg` (ver §a, filas «en vuelo»). El bloque anterior
(`tasks/BLOQUE_ARRANQUE_S163.md`) queda como historia. El detalle de cada paso está en `tasks/LOOP_OBJETIVOS.md` §6
(vueltas 1 a 15 de S163, entradas del 2026-10-26).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| Relevo | S163 coordinó; se separó de S162 a pedido de Nicolás (sesión de nivel superior). Las hijas siguen anidadas bajo S162: sus avisos automáticos le llegan a S162, así que mandan sus resultados por mensaje | bitácora vuelta 1 |
| PR mergeados en S163 | #900, #902, #903, #904, #905 (rebasado tras el squash de #904, tag `pre-s163-rebase-905`), #906, #901, #898, #908 (**loop/activo a main**, merge commit), #910, #909 (**toca el NRT**, tag `pre-s163-merge-909`), #886, #887, #911 (evidencia S159 a S163, 1.091 archivos en `experiments/`) | `git log origin/main`; CI verde en cada uno |
| PR cerrados | #889 (reemplazado por #909), #776, #880, #890, con comentario; ramas conservadas | `gh pr view` |
| PR abiertos | #907 (vía «código MIROVA» V750, borrador, sin archivos A45), #912 (informe del paper, borrador), #913 (plan de la retrospectiva, borrador) | `gh pr list` |
| NRT con #909 | primera corrida (11:10 UTC, `b43f4ee4f`) en verde; el log dice «Cobertura NO COMPLETA: 1 incidencias» en cada volcán porque el día en curso es parcial (previsto) | bitácora vuelta 14 |
| O2 (fondo de MATLAB) | **cerrado en los tres sensores**: MATLAB Online R2026b corrió V750 (Etna exacto al OSF; detección igual a Octave 311/311), MODIS (404 escenas) y V375 (422 escenas, Etna exacto). Regla de `fillmissing2` identificada (Delaunay con desempate simbólico, x = fila) y reproducida: V750 166/166, MODIS 404/404, V375 422/422; dos verificadores limpios con implementación independiente | `s163-o2-paquete`, `s163-o2-alternativa`, ramas de las hijas; vueltas 2, 6, 8, 12 |
| Regla fuera de la envolvente | MATLAB deja NaN; `delaunay_perturbado.rellenar` pone el vecino más cercano. Pedido a `loop-viirs750-2` que la vía devuelva NaN | vuelta «O2-375 cerrado» |
| V375-D | **fuera del programa**: con la vara de MATLAB la magnitud de V375-C no cambia (C13 0,999) | `claude/s162-viirs375-c1b864` `dbe9af431` |
| Decisión 9 | aplicada con D-48 tras verificador limpio: las 6 protegidas SNPP no son de cráter; para el estrato de 128 se informa la lectura A y se separan 11 / 71 / 88 | vuelta 1 |
| Adenda 1 de V750-B | **confirmada con D-48**; analizador sellado idéntico al tag `s162-v750b-sellado` | vuelta «adenda 1» |
| Candado de MOD-D | adenda 4 en curso; **punto (b) aprobado con D-48** (protegida que K publica y sale del denominador → fila 5, DECIDE NICOLÁS); M con la regla deja de ser preliminar | `s162-modd-candado` `ff2ced531` |
| H3 | **refutado** (0 de 9.538 publicados del detector anterior en el tablero de hoy) | `claude/s163-audit-h3-6c292b`; entró a main en #911 |
| Limpieza | 7 carpetas temporales y 6 worktrees integrados a la **papelera de Windows** (no borrado permanente); el espacio se libera al vaciarla | vueltas 5 y 7 |
| **En vuelo** | `loop-modis-2` (candado MOD-D: mutaciones y segunda vuelta del verificador; después pide el humo); `loop-viirs750-2` (cableado de la vía aprobado por Nicolás, flag apagado; NaN fuera de la envolvente; medidor de V750-A; V750-B el 2026-11-03); `loop-viirs375` (V375-E espera la vía y PD1); `d39-mirova-v1` (espera su verificador, rama `claude/s163-d39-mirova-v1-710f72`); `instrumento-pendientes` (placebos D-44 sobre producción, rama `claude/s163-instrumento-pendientes-ab5a2d`); `diurno-k-prereg` (espera su verificador, rama `claude/s163-diurno-k-prereg-5c4f44`) | `git ls-remote`; ids en §f |
| Entregas de difusión | paper (#912), retrospectiva (#913), congreso: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\congreso geologico 2026\2_PRESENTACIONES\PROPUESTA_REVISION_2026-10-26.md` (mazos v2 esperan visto bueno) | vuelta 15 |
| Runs | ninguno del loop; NRT normal | `gh run list` |
| Disco | C: 16 GB, D: 8,4 GB (bajando con varias sesiones; parada bajo 3 GB) | `df -h` |

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Merge del cableado de la vía V750 (cuando `loop-viirs750-2` entregue el PR con producción bit a bit igual y verificador) | mergear con flag apagado; esperar | **mergear** (ya aprobado el cableado; encender queda para después) |
| 2 | D-39: merge de Mirova-v1#26 y reposición de filas | mergear con el plan de `d39-mirova-v1`; esperar | **mergear sólo si el informe demuestra 0 filas perdidas en las dos direcciones**, con tag y pausa del scraper |
| 3 | Mazos v2 del congreso | aprobar la propuesta; pedir cambios | **leer la propuesta y aprobar**, ojo con las cifras de costo marcadas como no verificadas |
| 4 | Revista del paper: Volcanica prohíbe texto generado por IA (SOSPECHA, no comprobada) | ir a Volcanica escribiendo tú la prosa; otra revista | **confirmar la política en la fuente** antes de decidir |
| 5 | Licencia del repositorio (no tiene) | MIT, CC-BY, otra | **elegir antes de publicar o citar el código** |
| 6 | Sello del pre-registro del A/B diurno sobre K (D-10) | sellar; pedir cambios | sellar cuando su verificador dé conforme |
| 7 | Vaciar la papelera de Windows | vaciar; no | **vaciar** (libera ~1 a 2 GB en C: y D:) |
| 8 | Correo a Coppola | enviar; esperar | **esperar** (decisión de Nicolás, vigente) |

## c. Lo aprendido

Reglas generales del workspace (memoria `feedback_s163_lecciones.md`):
- **Un squash rompe los PR apilados**: el siguiente queda en conflicto. Rebasar sólo sus commits propios (`git rebase --onto
  origin/main <base vieja>`), tag defensivo y `--force-with-lease` con el sha esperado.
- **`git hash-object` sin `--no-filters` normaliza fines de línea**: un archivo con CRLF publicado así cambia de md5. Para
  evidencia que debe quedar byte a byte (código del OSF), `--no-filters` o `.gitattributes -text`.
- **MATLAB Online no acepta subidas programáticas** (marco aislado; MATLAB Drive ignora la entrada puesta por programa): se
  publica el paquete en una rama y MATLAB lo baja con `websave` desde `raw.githubusercontent.com`, comprobando md5 dentro de
  MATLAB. En la ventana de comandos, `Escape` borra la línea si no hay menú de autocompletado abierto; los comandos largos
  tipeados por la extensión dan timeout pero sí se escriben.
- **La rama de trabajo del loop tiene que llegar a main seguido y con merge commit**: `loop/activo` llevaba 421 commits sin
  llegar a main, y main no sabía que D25 no se adoptaba.
- **El computador suspendido detiene todo**: 4 horas sin actividad (06:00 a 10:22 UTC) en todas las sesiones.
- **Una regla identificada se confirma con una implementación independiente**, no re-corriendo el script del autor; y el
  control tiene que incluir rivales estructurados (simetrías, otras familias de desempate), no sólo uno débil.

Del proyecto (ya en la bitácora; rutear al catálogo cuando entre a main): la vara M de los tres paquetes es la regla exacta
de MATLAB; V375-D sale del programa; D17 como pieza central de los paquetes.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: el scraper Mirova-v1 pierde filas (hoy faltaban en la copia las filas de tabla de 4 protegidas de Chillán
  del 15 y 16 de octubre); D-39 en investigación.
- **CONFIRMADO**: fuera de la envolvente convexa la regla actual extrapola y MATLAB deja NaN (ninguna alerta afectada en los
  lotes medidos).
- **CONFIRMADO**: las copias viejas del `.m` de MIROVA en main (`_s158_d17_diseno/osf_codigo_mirova`, `_s159/o1/o2_paquete`,
  `prueba_o2_en_octave`) no son byte a byte las del OSF (fines de línea); las de `experiments/_s163_o2/` sí.
- **SOSPECHA**: la cifra de calibración «0,17 %» vendría de la fórmula de Di Bella (agregado al #912 sin verificador); choca
  con el `CLAUDE.md` (calibración empírica contra el OSF). Revisar antes de citarla.
- **SOSPECHA**: Volcanica prohíbe texto generado por IA en el manuscrito (no comprobado en la fuente).
- **SIN DATO**: que MIROVA use el `.m` de VIIRS 750 para el fondo de MODIS y de VIIRS 375.
- Seis citas siguen rotas en main porque esos archivos nunca se commitearon (lista en la bitácora, vuelta 15), entre ellas
  `experiments/_s162_v750b/objetivos_v750b.json`, que hace falta para el despacho del 2026-11-03.

## e. Lo que ya está cerrado y no hay que rehacer

- O2 en los tres sensores (no volver a correr MATLAB salvo una geometría nueva); la regla de `fillmissing2` está verificada.
- H3 refutado. Decisión 9 aplicada. Adenda 1 de V750-B confirmada. V375-D fuera.
- `loop/activo` integrado a main hasta `94fdd7aaf` (#908); la evidencia de S159 a S163 en main (#911).
- Borradores #776, #880, #890 cerrados; #889 reemplazado por #909 (mergeado).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora S164 (relevo de S163, cierre del 2026-10-26 ~12:35 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit de este cierre o más nuevo); hora del servidor con
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S164.md, tasks/LOOP_OBJETIVOS.md §6 (vueltas de S163, 2026-10-26)
   y el programa docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md.
3. Avisa a las sesiones vivas que la coordinadora ahora eres tú (SendMessage con tu id local_...): loop-modis-2
   local_0af7e1d8-7bde-4a4d-b8a3-6cf256a36c67, loop-viirs750-2 local_94f4be0d-2b32-4570-b711-3a6f14cc8a0a,
   loop-viirs375 local_3862f1f0-3d08-49b1-94fb-99e6c46cb39f, d39-mirova-v1 local_57b44db2-3006-49fb-a00c-0228be793b29,
   instrumento-pendientes local_bad70f2d-a64f-4eec-98f8-0497c3601256, diurno-k-prereg
   local_bd4d68e7-100e-412a-9456-3f89c7beb7e4. Comprueba sus ramas con git ls-remote.

Trabajo, en orden:
- Recibir y verificar lo que entreguen: veredicto de D-39 (merge de Mirova-v1#26 sólo con 0 filas perdidas demostradas,
  tag y pausa del scraper); PR del cableado de la vía V750 (mergear si producción queda bit a bit igual con el flag
  apagado y hay verificador limpio); pedido del humo de MOD-D (despachar desde tag); placebos D-44; pre-registro del
  diurno sobre K (al sello de Nicolás).
- 2026-11-03: despacho de V750-B (objetivos con sha256 commiteados, tag, jobs, comando del lector leer_v750b.py) y
  consulta C-06 del cese de Suomi NPP contra CMR.
- Cuando aparezca el issue del auto-audit semanal, cerrar #864 con un comentario que apunte al nuevo.
- Integrar loop/activo a main con merge commit cuando acumule trabajo (no squash).
- Recordar a Nicolás las decisiones de §b del bloque S164.
- Correr como loop propio con la skill loop en modo dinámico sobre tasks/LOOP_OBJETIVOS.md; anotar cada vuelta y
  commitear en loop/activo.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); sólo EARTHDATA_TOKEN
(A71); despachos uno a la vez dentro del cupo de 20 jobs (NRT usa 11), desde tags; verificador limpio de otro modelo
antes de aceptar un resultado; git add por archivo; nunca git stash; las ramas de las hijas tienen que estar en el
remoto; disco justo (C: ~16 GB, D: ~8 GB, parada bajo 3 GB); Claude no borra de forma permanente (papelera de Windows);
español de Chile sin voseo ni guiones largos; rutas absolutas. Si la sesión no alcanza: commitea, anota en la bitácora
qué quedó corriendo y cierra con /cierre.
```
