# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún archivo citado)

Vara: pre-registro sellado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §4, §11, §13), tag s168-modd-f4-sellado sobre 3768e9431. Árbol: 3db87f50d.

## A1 Población
- El json cuenta 5.709 pero los dos tramos (C, E) se definen con una ventana distinta de la del pre-registro §4.
- "5.321 con grilla_censo, todas de C" puede contar claves presentes pero vacías/null; o contar pasadas duplicadas (misma pasada, dos sensores/granulos).
- "56 protegidas" puede salir de una etiqueta (clase_mirova) calculada con otro corte (1 MW, lectura A vs B) o con la referencia sin A119 (OCR).
- `sin_pasada_nuestra` vacía puede ser vacía porque el script nunca la llena (control que no puede fallar).
- contrato_poblacion_f4.py "calza" con control_cobertura/control_identidad comparando archivos derivados del mismo json (circular).
- La población se leyó de data/ que no está en el árbol: no puedo recomputar; solo consistencia interna.

## A2 HEAD tramo E
- head_e.json registra 200 pero el script HEAD sigue redirecciones (un 302 a una página de login responde 200 final).
- 106 de 106 puede ser el denominador de URL construidas, no de las pasadas del tramo E (244 pasadas).
- "sin credenciales" no verificable por mí sin red; sólo veo que el script no manda auth.
- Un día excluido pudo omitirse de la lista en vez de registrarse.

## A3 Referencia
- sha256 comparado contra un archivo que es la propia copia (compara consigo mismo).
- "0 distintas en 5.465" compara etiquetas derivadas del mismo reetiquetado (circular); no prueba la referencia.
- Los sha de S165 vienen de un doc, no del archivo real; no hay data/ para recomputar.
- Normalización de saltos de línea (autocrlf, A92/S163): sha cambia entre CRLF y LF.

## A4 Arnés (probe_f4.py)
- "16 de 16 atrapadas por aserción": la mutación puede caer por excepción y contarse como atrapada; o la aserción atrapa por un mensaje de error y no por un valor.
- Las mutaciones se aplican a una copia mal ubicada (no la que importa el probe) → siempre "atrapadas" por caída de import.
- "18 de 18" pruebas que no ejercen el camino real (mocks).
- Control caída "CAE" y rota "ROTA" son sintéticos, no mutaciones del probe real.
- No puedo re-correr el probe real si requiere node sobre ~27.000 records o data/ ausente → SIN DATO.

## A5 Identidad
- 8 escenarios sobre 101 grillas reales: las grillas vienen de grilla_censo del json (el mismo que se compara), identidad circular: la vía corrida y el censo comparten el código del port.
- "cruzados con control_identidad": control_identidad mide una tolerancia floja (allclose con atol grande) o compara solo conteos.
- Identidad "escenario por escenario" pero redondeo float entre runners (argsort inestable por CPU, S152).
- 101 grillas ≠ 5.321 grillas: muestra, no cobertura.

## A6 Manifiesto
- "64 archivos" puede contar rutas que no existen en el árbol, o omitir archivos que el workflow/probe importan (los pipeline/ del port, frontend/ predicado, volcanoes.yaml).
- Los sha del manifiesto pueden estar calculados con CRLF vs LF; git archive con autocrlf=false da LF.
- tag/commit null: verificable; pero el manifiesto debe incluir el propio manifiesto, el workflow y los tests → circularidad/omisión.

## A7 Workflow
- `"on":` con comillas pero `workflow_call`/`schedule`/`push`/`pull_request` presente en otra parte.
- Secreto: EARTHDATA_TOKEN usado pero también EARTHDATA_USERNAME/PASSWORD heredado (A71 bloqueo cuenta).
- "falla si viene vacío": la verificación puede ser `[ -z "$X" ]` sobre un env que se define con `${{ secrets.X }}` — sirve; o puede estar en un step que no corre antes del uso (orden), o `continue-on-error`.
- permissions: sin bloque `permissions:` → hereda default del repo (puede ser write). Debe ser contents: read.
- "no hace push ni commit": git push dentro de un script llamado por el workflow (no visible en yml); upload-artifact está bien, pero actions/checkout con persist-credentials.
- procedencia: compara `git rev-parse HEAD` con `github.sha` (que con --ref tag es el commit del tag) pero no con el tag pedido en inputs; un input `tag` con un valor que apunta a otro commit; checkout con `ref: inputs.tag` vs `--ref`: tag anotado (SHA del objeto tag ≠ commit).
- concurrency: group sin cancel-in-progress:false puede cancelar la tanda en curso; group por ref permite dos tandas con distintos tags.
- timeouts: 50 min per-step (hang de red, A64) vs matriz; max job 6 h.
- Mergear a main antes del tag: workflow_dispatch solo existe en default branch (A42/limitation) → ayuda; pero un cambio de `main` después del tag no afecta el tag. Riesgo: el workflow en main apunta a scripts que cambian (§13 y manifiesto regenerados), el workflow usa rutas que deben existir en el tag; si el yml en main tiene hash que se incluye en el manifiesto, mergear altera... pues el manifiesto referencia el workflow.
- Otras ramas: el tag no incluye el workflow si el workflow se agrega al tag; `--ref tag` requiere que el yml exista en ese tag.
- El workflow lee archivos que cambiarán (PREREGISTRO §13, MANIFIESTO) → regenerados tras mutaciones.

## A8 Evaluador
- 66 de 66 pasa, pero contra el vacío "fallan por aserción" puede ser por TypeError capturado como aserción.
- `git diff 3768e9431 3db87f50d -- evaluar_f4.py` vacío no basta: el evaluador importa otros módulos (clase_mirova, banco_paridad) que sí pudieron cambiar.
- VS-01..VS-08 "cerrados" puede ser cerrados por cambio en el instrumento que sí cambió la regla (en otro archivo), o cerrados en un doc sin test.
- No puedo correr la batería si necesita data/ ausente.

## Generales
- La copia del árbol está atrasada o extraída con cambios de salto de línea (autocrlf=false dado: ok).
- El árbol no trae data/ → todo recómputo de poblacion/censo es SIN DATO; solo consistencia interna.
- Las cifras del informe del autor pueden ser de otro commit (3768e9431) y no de 3db87f50d.
- La vara real es el pre-registro §11: el candado debe tener TODO lo que §11 enumera; una verificación contra el INFORME del autor (vara equivocada) no podía fallar.

---
sha256 (calculado antes de añadir esta línea): 3acc2229c5f5110fb0ce014f50d02b3d23455a708ea8e329055aafb84b12233e
hora servidor: Fri Oct 30 00:42:12 UTC 2026 (no se vuelve a editar)
