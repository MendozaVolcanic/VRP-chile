# Mirova-v1#26: pasos 2 a 6 para copiar y pegar

Para qué: mergear el arreglo del scraper de MIROVA sin perder una sola fila de la referencia. La evidencia está en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-d39-mirova-v1-710f72\experiments\_s163_d39_mirova_v1\INFORME.md`.
El paso 1 ya lo hizo S164 el 2026-10-26: `fix/referencia-estable` está en `dd606a65a108790fe8ca824bd9d5250accff979b` y el
CI de #26 dio 6 de 6 en verde.

Todo va en **Git Bash** (no PowerShell), con `gh` autenticado como MendozaVolcanic. Un comando por bloque. Hay que hacerlo
de una sentada: entre el paso 2 y el paso 5 el scraper está detenido, y a los 60 minutos sin dato el vigilante nuevo
manda un correo en rojo (esperable, no es una falla).

## Paso 0. Comprobar que nada cambió desde la revisión

```bash
gh api repos/MendozaVolcanic/Mirova-v1/branches/fix/referencia-estable --jq .commit.sha
```
Esperado: `dd606a65a108790fe8ca824bd9d5250accff979b`. Si da otro sha, **parar**: alguien empujó a la rama del PR después
de la revisión.

```bash
gh pr checks 26 -R MendozaVolcanic/Mirova-v1
```
Esperado: las 6 líneas en `pass`.

## Paso 2. Pausar los dos escritores de datos

```bash
gh workflow disable main.yml -R MendozaVolcanic/Mirova-v1
```
```bash
gh workflow disable ocr_workflow.yml -R MendozaVolcanic/Mirova-v1
```
Deshabilitar no corta la corrida que ya está andando. Repetir este comando cada minuto hasta que **no imprima nada**:
```bash
gh run list -R MendozaVolcanic/Mirova-v1 --limit 20 --json workflowName,status,databaseId --jq '.[]|select(.status!="completed")|select(.workflowName|test("Monitor|OCR"))'
```

## Paso 3. Regenerar la reposición contra el main ya quieto

Por si el scraper perdió filas otra vez entre la revisión y la pausa. Usa el clon parcial que ya está en el disco
(`D:\vrp-trabajo\s163-d39\mirova-v1`, nada de clonar el repo entero).

```bash
git -C D:/vrp-trabajo/s163-d39/mirova-v1 fetch -q origin main fix/referencia-estable
```
```bash
MSYS_NO_PATHCONV=1 git -C D:/vrp-trabajo/s163-d39/mirova-v1 show origin/fix/referencia-estable:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv > D:/vrp-trabajo/s163-d39/reposicion_actual.csv
```
```bash
python -I D:/vrp-trabajo/s163-d39/s16_regenerar_reposicion.py "D:\vrp-trabajo\s163-d39\mirova-v1" "D:\vrp-trabajo\s163-d39\reposicion_actual.csv" "D:\vrp-trabajo\s163-d39\reposicion_paso3.csv" --hasta origin/main
```
Esperado: una sola línea `firma de mezcla: 53b1e6d3c0...` y, en la línea siguiente, `ya en el archivo del PR 241`,
**`nuevas 0`** y `filas del PR que hoy SI estan en main 0`. (Probado el 2026-10-26 contra main `6a2af49cdd`, 13:16 UTC: así salió.)
Si aparece una segunda línea `firma de mezcla`, hubo otro episodio: mira el conteo de `nuevas`. Si dice `nuevas` mayor que 0, **parar**: hubo otra pérdida, y hay que agregar esas filas a la rama del PR
(`reposicion_paso3.csv` ya las trae) y actualizar el conteo de `tests/test_reponer_filas.py` antes de seguir. Pídeselo a
Claude con la salida pegada.

## Paso 4. Tag defensivo en main

```bash
SHA=$(gh api repos/MendozaVolcanic/Mirova-v1/commits/main --jq .sha); echo $SHA
```
```bash
gh api repos/MendozaVolcanic/Mirova-v1/git/refs -f ref=refs/tags/pre-pr26-referencia-estable -f sha=$SHA --jq .object.sha
```
Esperado: imprime el mismo `$SHA` del comando anterior. Anótalo: es el punto de vuelta atrás.

## Paso 5. Mergear y reactivar

```bash
gh pr merge 26 -R MendozaVolcanic/Mirova-v1 --merge
```
```bash
gh workflow enable main.yml -R MendozaVolcanic/Mirova-v1
```
```bash
gh workflow enable ocr_workflow.yml -R MendozaVolcanic/Mirova-v1
```
```bash
gh workflow run main.yml -R MendozaVolcanic/Mirova-v1 --ref main
```

## Paso 6. Verificar que no se perdió nada

Esperar a que termine la primera corrida de `main.yml` (unos 2 minutos) y mirar su registro:
```bash
ID=$(gh run list -R MendozaVolcanic/Mirova-v1 --workflow main.yml --limit 1 --json databaseId,conclusion --jq '.[0].databaseId'); gh run view $ID -R MendozaVolcanic/Mirova-v1 --log < /dev/null | grep -E "reponer_filas|Guarda de llaves|push OK|push falló"
```
Esperado: `reponer_filas: 2351 filas repuestas`, `Guarda de llaves OK` y `push OK`. (Si el paso 3 dio filas nuevas y se
agregaron, el número es 2351 más esas.)

Después, la comparación fila a fila del tag contra main, sin clonar:
```bash
python -I D:/vrp-trabajo/s163-d39/s20_verificar_post_merge.py --antes pre-pr26-referencia-estable --despues main
```
Esperado: `consolidado: ... llaves perdidas 0; repetidas despues 0; nuevas` 2.351 o más (las de la reposición más las
pasadas nuevas); `reposicion (main): 2351 filas, faltan en despues 0`; `OCR: ... llaves perdidas 0`; y la última línea
**`VERDE`**. Esta herramienta se probó con un nulo (main contra main: 0 perdidas) y con el episodio real del 24-oct
(`53b1e6d3c0`: 241 perdidas, 1.565 repetidas, ROJO).

La segunda corrida de `main.yml` (unos 5 min después) tiene que decir `reponer_filas: 0 filas repuestas`:
```bash
ID=$(gh run list -R MendozaVolcanic/Mirova-v1 --workflow main.yml --limit 1 --json databaseId --jq '.[0].databaseId'); gh run view $ID -R MendozaVolcanic/Mirova-v1 --log < /dev/null | grep -E "reponer_filas|Guarda de llaves"
```

Primera corrida del OCR (a la hora y 5, o forzarla con `gh workflow run ocr_workflow.yml -R MendozaVolcanic/Mirova-v1 --ref main`):
```bash
ID=$(gh run list -R MendozaVolcanic/Mirova-v1 --workflow ocr_workflow.yml --limit 1 --json databaseId --jq '.[0].databaseId'); gh run view $ID -R MendozaVolcanic/Mirova-v1 --log < /dev/null | grep -E "reparar_mojibake|Guarda de llaves|Push exitoso|rebase choco"
```
Esperado: `reparar_mojibake: 647 notas reparadas`, `Guarda de llaves OK`, `Push exitoso`. Después, `s20` otra vez tiene que
mostrar `notas con mojibake despues: 0`.

Y del lado de VRP Chile, el sync de la hora siguiente tiene que salir verde:
```bash
gh run list -R MendozaVolcanic/VRP-chile --workflow sync-mirova-csv.yml --limit 2
```

## Vuelta atrás

El PR sólo agrega filas y cambia código. Si algo sale mal **en el código** (por ejemplo, la guarda deja todas las corridas
en rojo):
```bash
gh api repos/MendozaVolcanic/Mirova-v1/commits/main --jq '.sha + " " + .commit.message' | head -c 200
```
y revertir el merge desde la página del PR #26 (botón Revert), que abre un PR de reversión. Las filas repuestas son reales y
se quedan. **No** restaurar el CSV del tag encima de main: borraría las pasadas nuevas desde el tag.

Una corrida del OCR en rojo con «el rebase choco con otro escritor» es esperable (~6 % de las corridas, dos corridas del OCR
solapadas): no pierde datos, la siguiente vuelve a leer las imágenes. Es un seguimiento aparte, no una razón para revertir.
