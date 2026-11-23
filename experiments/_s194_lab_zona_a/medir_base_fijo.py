# -*- coding: utf-8 -*-
"""Corre `medir_base.py` de un árbol dado con la referencia de MIROVA fijada a dos shas (re-sello S196).

POR QUÉ. `medir_base.py` lee producción del `data/mirova_equivalent` de su árbol y baja la referencia de MIROVA
fresca (`referencia_mirova_unificada.bajar_remoto` pide el último sha). Para que el re-sello del 2026-11-23 cambie sólo
lo que depende de la serie NHI de Chillán, se corre sobre un árbol del commit original (`1c6ac41e1`, el padre del
primer sello) con la referencia en los shas que registró la corrida original (`salida_medir_base.json`, `referencia`).
Con el NHI de esa corrida la salida se reproduce byte a byte; con el NHI nuevo cambia sólo lo de NHI.

Uso: python medir_base_fijo.py <raiz del árbol> <sha consolidado> <sha OCR> --nhi-dir <dir> --dest <tmp> --fin AAAA-MM-DD
(los argumentos desde --nhi-dir son los de medir_base.py; escribe las salidas junto al medir_base.py del árbol).
"""
import runpy
import sys

raiz, sha_cons, sha_ocr = sys.argv[1:4]
sys.path.insert(0, raiz + "/scripts")
import referencia_mirova_unificada as rmu  # noqa: E402

fijos = {"registro_vrp_consolidado.csv": sha_cons, "registro_vrp_ocr.csv": sha_ocr}
rmu.sha_remoto = lambda nombre: fijos[nombre]
sys.argv = [raiz + "/experiments/_s194_lab_zona_a/medir_base.py"] + sys.argv[4:]
runpy.run_path(sys.argv[0], run_name="__main__")
