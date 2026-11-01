# -*- coding: utf-8 -*-
"""INFORMATIVO, NO ENTRA AL VEREDICTO (D-35). Brazo de sensibilidad del 17 al 19 de octubre (run 39756261926),
evaluado con el evaluador del tag s161-d25-lectura y la configuración de V1 (referencia congelada _congelado_v1,
tabla y OCR). Sin modificar evaluar_d25.py: en memoria se vacía la exclusión de días de D-29 (que existe justamente
porque V1 no tenía esos días) y, con el argumento 'solo_tabla', se reetiqueta con la tabla de latest.php sola."""
import sys
sys.path.insert(0, r"C:\vrp-trabajo\s159-evaluador\experiments\_s157_prereg_d25")
import evaluar_d25 as D  # noqa: E402

D.DIAS_EXCLUIDOS["V1"] = ()
if "solo_tabla" in sys.argv:
    sys.argv.remove("solo_tabla")
    D.VENTANAS["V1"]["solo_tabla"] = True
D.main()
