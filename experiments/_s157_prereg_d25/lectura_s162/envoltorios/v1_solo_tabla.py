# -*- coding: utf-8 -*-
"""INFORMATIVO, NO DECIDE. Corre el evaluador del tag s161-d25-lectura sobre V1 con la tabla de latest.php sola
(el OCR reetiquetado fuera, igual que V2), sin modificar evaluar_d25.py: sólo cambia el diccionario VENTANAS en
memoria. Pedido del traspaso S162 (memoria feedback_s159_latest_php_mas_creible)."""
import sys
sys.path.insert(0, r"C:\vrp-trabajo\s159-evaluador\experiments\_s157_prereg_d25")
import evaluar_d25 as D  # noqa: E402

D.VENTANAS["V1"]["solo_tabla"] = True
sys.argv = [sys.argv[0]] + sys.argv[1:]
D.main()
