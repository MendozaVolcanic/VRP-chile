# -*- coding: utf-8 -*-
"""Prueba del medidor de mutaciones (S168, VS-01 y VS-03 del tercer verificador). La salida «NO VALE» con código 1 no
tenía prueba: si alguien la borra, el medidor podría informar 86 de 86 con un control roto y salir en verde. Aquí se
ejercen la clasificación y el resumen sin correr la batería (correr se reemplaza por resultados fijos).
Uso: python probar_mutar_f4.py  (escribe probar_mutar_f4_salida.txt)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mutar_evaluar_f4 as M  # noqa: E402

BUENOS = [("IDENTIDAD", "VIVA", ""), ("CONTROL_CAIDA", "CAE", ""), ("CONTROL_CAIDA_VALUEERROR", "CAE", ""),
          ("CONTROL_ROTA", "ROTA", ""), ("M01_x", "ATRAPADA", "")]


def chk(cond, msg):
    if not cond:
        raise AssertionError(msg)


def P01_clasificar():
    chk(M.clasificar(1, ["E01"], []) == "ATRAPADA", "aserción sin caídas")
    chk(M.clasificar(1, ["E53"], ["E01"]) == "ATRAPADA_CON_CAIDAS", "aserción con caídas no cuenta (VS-01)")
    chk(M.clasificar(1, [], []) == "ROTA", "código 1 sin aserción")
    chk(M.clasificar(2, [], ["E01"]) == "CAE", "sólo caídas")
    chk(M.clasificar(0, [], []) == "VIVA", "pasa entera")
    chk(M.clasificar(3, [], []) == "ROTA", "no carga")


def P02_resumen_vale():
    txt, cod = M.resumir(BUENOS)
    chk(cod == 0 and "NO VALE" not in txt, "controles buenos: código %s" % cod)
    chk("MUTACIONES: 1 de 1 atrapadas" in txt, "cuenta la atrapada")


def P03_resumen_no_vale():
    for i, (c, _clase, _x) in enumerate(BUENOS[:4]):
        malo = list(BUENOS)
        malo[i] = (c, "ATRAPADA", "")
        txt, cod = M.resumir(malo)
        chk(cod == 1 and "NO VALE" in txt and c in txt.split("NO VALE")[1], "%s mal: código %s" % (c, cod))
    txt, cod = M.resumir([r for r in BUENOS if r[0] != "CONTROL_CAIDA_VALUEERROR"])
    chk(cod == 1 and "NO VALE" in txt, "un control ausente no vale")


def P04_atrapada_con_caidas_no_cuenta():
    txt, _cod = M.resumir(BUENOS[:4] + [("M02_y", "ATRAPADA_CON_CAIDAS", "")])
    chk("MUTACIONES: 0 de 1 atrapadas" in txt and "M02_y" in txt.split("atrapadas con caídas")[1], "no cuenta")


def P05_main_sale_con_1():
    viejo = M.correr
    M.correr = lambda nombre, v, n, tmp: (nombre, "ATRAPADA" if nombre == "CONTROL_CAIDA" else
                                          {r[0]: r[1] for r in BUENOS}.get(nombre, "ATRAPADA"), "")
    argv = sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "salida.txt"
        sys.argv = ["mutar_evaluar_f4.py", "--solo", "M01", "--paralelo", "1", "--salida", str(out)]
        try:
            M.main()
            cod = 0
        except SystemExit as e:
            cod = e.code
        finally:
            M.correr, sys.argv = viejo, argv
        chk(cod == 1, "main con un control malo sale con %s" % cod)
        chk("NO VALE" in out.read_text(encoding="utf-8"), "la salida escrita dice NO VALE")


PRUEBAS = [P01_clasificar, P02_resumen_vale, P03_resumen_no_vale, P04_atrapada_con_caidas_no_cuenta,
           P05_main_sale_con_1]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    lineas, malas = [], 0
    for p in PRUEBAS:
        try:
            p()
            lineas.append("OK              %s" % p.__name__)
        except AssertionError as x:
            malas += 1
            lineas.append("FALLA ASERCION  %s | %s" % (p.__name__, x))
    lineas.append("RESUMEN: %d pruebas, %d OK" % (len(PRUEBAS), len(PRUEBAS) - malas))
    txt = "\n".join(lineas)
    print(txt)
    (AQUI / "probar_mutar_f4_salida.txt").write_text(txt + "\n", encoding="utf-8")
    sys.exit(1 if malas else 0)


if __name__ == "__main__":
    main()
