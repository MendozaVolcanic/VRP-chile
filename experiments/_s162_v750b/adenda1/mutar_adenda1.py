# -*- coding: utf-8 -*-
"""Nulo de `probar_adenda1.py`: mutaciones de una línea del compañero; cada una tiene que quedar ATRAPADA por aserción.

POR QUÉ (S156, A110). Una prueba que pasa no dice nada si tampoco falla cuando el compañero se rompe. Cada mutación es
una copia con UNA línea cambiada; cuenta como atrapada sólo si la batería sale 1 con la línea «FALLAS» y sin que el
compañero se haya caído (la batería sale 2 con «CAÍDA DEL COMPAÑERO» si ve un traceback suyo). La mutación de control hace
caer al compañero: tiene que salir CAÍDA, no ATRAPADA. La identidad (copia sin cambios) tiene que pasar.
Uso: python mutar_adenda1.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta temporal>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORIG = AQUI / "cobertura_cajas_v750b.py"
MUT = [
    ("identidad", None, None, "PASA"),
    ("M1 no mira las cajas", "and cajas_faltantes(res[i])]", "and False]", "ATRAPADA"),
    ("M2 caja vacía cuenta como presente", "not isinstance(orc.get(c), dict)", "c not in orc", "ATRAPADA"),
    ("M3 falta caja no frena si es protegida", "for i in sin + falta if", "for i in sin if", "ATRAPADA"),
    ("M4 falta caja fuera del 2 %", "len(sin) + len(sin_g) + len(falta)", "len(sin) + len(sin_g)", "ATRAPADA"),
    ("M5 sin gránulo ajeno aceptado", "cob_ok = sg_ok and", "cob_ok = True and", "ATRAPADA"),
    ("M6 cuenta también las diurnas", 'res[i].get("dayflag") == 0 and cajas', "cajas", "ATRAPADA"),
    ("M7 salida 0 siempre", "return 0 if cob_ok else 3", "return 0", "ATRAPADA"),
    ("control que se cae", "res = AB.cargar(a.art)", "res = AB.cargar(a.art); res[None]['x']", "CAÍDA"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    a = ap.parse_args()
    src = ORIG.read_text(encoding="utf-8")
    malas = 0
    for nombre, viejo, nuevo, espera in MUT:
        if viejo is not None and src.count(viejo) != 1:
            print(f"{nombre}: la línea a mutar aparece {src.count(viejo)} veces, no 1: MUTACIÓN INVÁLIDA")
            malas += 1
            continue
        copia = AQUI / f"_mut_{re.sub(r'[^A-Za-z0-9]+', '_', nombre)}.py"
        copia.write_text(src if viejo is None else src.replace(viejo, nuevo), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(AQUI / "probar_adenda1.py"), "--companero", str(copia),
                                "--evaluador", a.evaluador, "--dest", str(a.dest / copia.stem)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        finally:
            copia.unlink()
        out = r.stdout + r.stderr
        if r.returncode == 0 and "TODOS LOS CHEQUEOS COMO SE ESPERA" in out:
            estado = "PASA"
        elif r.returncode == 2 and "CAÍDA DEL COMPAÑERO" in out:
            estado = "CAÍDA"
        elif r.returncode == 1 and "FALLAS" in out:
            estado = "ATRAPADA"
        else:
            estado = f"OTRA (salida {r.returncode})"
        fallas = re.search(r"FALLAS \(\d+\): (.*)", out)
        print(f"{nombre}: {estado} (se espera {espera})" + (f" | {fallas.group(1)[:160]}" if fallas else ""))
        malas += estado != espera
    print("mutaciones:", "TODAS COMO SE ESPERA" if not malas else f"{malas} NO COMO SE ESPERA")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
