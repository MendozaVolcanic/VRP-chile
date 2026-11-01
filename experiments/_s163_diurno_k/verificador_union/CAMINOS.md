# Caminos de ruptura (escritos ANTES de abrir el diff)

Hora del servidor (gh api, Date): Mon, 26 Oct 2026 19:14:50 GMT
Commit medido: a1604e25346e2374ed814cd0301a3019cbbba121 (rama claude/s163-diurno-k-prereg-5c4f44)
Modelo: Sonnet 5.5 (claude-sonnet-5-5), esfuerzo por defecto del subagente (no declarado mas alto).

Alcance: git diff 867cb1ec8..a1604e253 de evaluar_con_exclusion.py, test_evaluar_con_exclusion.py,
mutaciones_exclusion.json, PREREGISTRO.md, objetivos_adenda1_sha256.txt.

Caminos por los que la union puede decidir mal:

C1. El script no carga lo mismo que main() sellado de evaluar_diurno_k.py (68687d2d4): otras rutas, otra
    referencia, otro sha de la referencia, otras ventanas, otros brazos/plataformas, otro filtro.
C2. Sacar filas y records "por dia" no equivale a excluir_dias del evaluador: pasadas que cruzan medianoche UTC
    (pareo +-120 s entre record y referencia con fechas distintas), filas sin fecha o con fecha mal parseada,
    zona horaria (fecha UTC vs fecha local), fecha de la referencia vs fecha del record.
C3. Deja fuera algo que main() sellado si hace: logs, chequeo de sha de la referencia, variantes, informativos,
    compuertas I1..I6, placebo, cobertura.
C4. Excluye de mas (dias fuera de la lista) o de menos (dias de la lista que no salen), p. ej. por comparar
    str vs date, por listas vacias que pasan en silencio, o por plataforma (condicion b' por plataforma).
C5. Las pruebas pasan por la razon equivocada (fixtures sin dias a excluir, aserciones triviales, monkeypatch
    que oculta el defecto, mutaciones que "caen" por excepcion y no por asercion).
C6. El sello (objetivos_adenda1_sha256.txt) no coincide con los blobs del commit 038c6904b, o cubre menos de lo
    que dice cubrir.
C7. El texto nuevo de la adenda (puntos 7 a 9) dice algo que el script no hace (o al reves), o contradice el
    resto del §11.
C8. Un denominador que se achica en silencio: tras excluir, quedan n pasadas distintas y nadie lo reporta.
C9. El script modifica estado global del modulo sellado (monkeypatch en import) y deja efectos laterales.
sha256 CAMINOS.md (antes del diff): 52c42fec49480807740fcd4c2b04783591f8f713b09890cac54fab716f6939f4 ; hora servidor 2026-10-26 19:14:50 GMT
