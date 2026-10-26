# -*- coding: utf-8 -*-
"""Verificador: borde exacto del 2 % (analizador sellado contra compañero). Uso: python ver_borde2.py <evaluar_d25.py> <dest>"""
import importlib.util, sys
from pathlib import Path
ADE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("pa", ADE / "probar_adenda1.py"); PA = importlib.util.module_from_spec(spec); spec.loader.exec_module(PA)
ev, dest = sys.argv[1], Path(sys.argv[2])
for etiqueta, n_total, n_malas, kind in (("2 de 100 (2,00 %) error_K", 100, 2, "error_K"), ("3 de 150 (2,00 %) error_K", 150, 3, "error_K"),
                                         ("2 de 100 (2,00 %) sin caja", 100, 2, "sin_caja"), ("3 de 100 (3 %)", 100, 3, "error_K"), ("2 de 101", 101, 2, "error_K")):
    p = PA.Pob()
    for n in range(4):
        p.pasada(f"2026-05-{10+n:02d} 05:00", "pos", 1.5)
    for n in range(n_total - 4 - n_malas):
        p.pasada(f"2026-04-{1 + n % 28:02d} {n // 28:02d}:00")
    for n in range(n_malas):
        if kind == "error_K":
            p.pasada(f"2026-08-{1+n:02d} 05:00", estado="error_K")
        else:
            p.pasada(f"2026-08-{1+n:02d} 05:00", sin_caja=("B3",))
    d = dest / etiqueta.split(" ")[0] ; d = dest / (etiqueta.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "").replace("%", "p")); d.mkdir(parents=True, exist_ok=True)
    p.escribir(d)
    an, o = PA.analizador(d, ev)
    rc, c, oc = PA.companero(ADE / "cobertura_cajas_v750b.py", d)
    print(f"{etiqueta}: analizador {an}  | compañero {c['cob'] if c else None} total {c['total'] if c else None} rc {rc}")
