# Mutaciones del verificador sobre una COPIA (C:\vrp-trabajo\vc_tmp\mut, git archive de 3a02ad28f; el worktree no se tocó)

Suite usada: tests/test_mirova_v750_cableado_s162.py (7 pruebas, base verde) y, para las de flag apagado,
tests/test_apagado_no_cambia_nada_s142.py (8 pruebas, base verde, con tests/golden_s142/apagado.json).

| id | mutación | resultado |
|---|---|---|
| M1 | `if ENABLE_V750_CODIGO_MIROVA:` -> `if True:` (process_viirs_mod.py) | ATRAPADA (test_flag_apagado_no_toca_la_via) |
| M2 | store: `record.get("via_codigo_mirova") is True` -> `bool(record.get("via_codigo_mirova"))` (el "sin_grilla" de K saltaría las compuertas) | NO atrapada (7 passed) |
| M3 | store: quitar `and not _via_mirova` de la geocerca | ATRAPADA (test_almacen..[True-4.0]) |
| M4 | store: quitar `and not _via_mirova` del filtro de píxeles por distancia | NO atrapada (7 passed) |
| M5 | store: quitar `and not _via_mirova` del tope de píxeles por cúmulo | ATRAPADA |
| M6 | process_viirs_mod: `if _via_sin_grilla:` final -> `if True:` (marca "sin_grilla" en todo record) | NO atrapada por cableado_s162; ATRAPADA por test_apagado_no_cambia_nada_s142 (2 fallas) |
| M7 | process_viirs_mod: `_via_sin_grilla = False` -> `True` | NO atrapada por cableado_s162; ATRAPADA por test_apagado_no_cambia_nada_s142 (2 fallas) |
