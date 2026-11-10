# -*- coding: utf-8 -*-
"""Mutaciones de montaje_ab.py (S178). Cada una rompe una regla de la declaración de C-montaje en una copia del módulo
y corre tests/test_montaje_ab_s178.py contra ella (MONTAJE_AB_MODULO). ATRAPADA sólo si alguna prueba falla por
AssertionError; si sólo hay excepciones es CAE (S152); si todo pasa, SOBREVIVE. La mutación de control mete un
NameError y tiene que salir CAE.

POR QUÉ. Las pruebas del módulo se escribieron después del módulo (S178, desvío de TDD declarado en la bitácora): las
mutaciones son la evidencia de que pueden ponerse rojas.

Uso: python mutar_montaje_ab.py > mutar_montaje_ab_salida.txt
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ORIGINAL = AQUI / "montaje_ab.py"
BATERIA = RAIZ / "tests" / "test_montaje_ab_s178.py"

MUTACIONES = [
    ("A1 tolerancia de VRP 10 veces más ancha", "TOL_VRP = 1e-3", "TOL_VRP = 1e-2"),
    ("A2 no compara celdas", "            if v[\"celdas\"] != ref[\"celdas\"]:", "            if False:"),
    ("A3 la pasada faltante no cuenta", "            campos.append(\"falta_en_via\")", "            pass"),
    ("A4 todo se explica por otro gránulo", "\"explicada_por\": \"otro_granulo\" if otro else None",
     "\"explicada_por\": \"otro_granulo\""),
    ("A5 la versión de proceso entra en la identidad", r'\.(\d{4})")', r'\.(\d{4}\.\d{3})")'),
    ("A6 B4 usa B0 en todos", "    return \"B1\" if vol in SENSIBLES_B4 else \"B0\"", "    return \"B0\""),
    ("A7 la banda se ignora", "    if b and len(b) == 2", "    if False and b and len(b) == 2"),
    ("A8 MODIS sin clase de distancia", "            if comparar_dc and v[\"dc\"] != ref[\"dc\"]:", "            if False:"),
    ("A9 sin filtro de DM en el A/B", "        if not en_dm(e.get(\"hora_utc\", \"\")):\n            continue\n        o =",
     "        o ="),
    ("A10 V375 lee M13 en vez de C13", "(e.get(\"port\") or {}).get(\"C13\")", "(e.get(\"port\") or {}).get(\"M13\")"),
    ("A11 V375 sin la banda del port (S178, opción 1)", "\"banda\": c.get(\"vrp_banda\")", "\"banda\": None"),
    ("CONTROL de caída: NameError", "    m = _GRAN.search(str(nombre or \"\"))", "    m = _GRAN_NO_EXISTE.search(str(nombre or \"\"))"),
]


def correr(src):
    copia = AQUI / f"_mut_montaje_ab_{os.getpid()}.py"
    copia.write_text(src, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", str(BATERIA), "-q", "-p", "no:cacheprovider", "-rf",
                            "--tb=no"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, MONTAJE_AB_MODULO=str(copia), COLUMNS="2000"))
    finally:
        copia.unlink(missing_ok=True)
    fallas = [l for l in r.stdout.splitlines() if l.startswith("FAILED")]
    asercion = [l for l in fallas if " - AssertionError" in l or re.search(r" - assert", l)]
    if asercion:
        return "ATRAPADA", asercion[:3]
    if fallas or r.returncode not in (0, 1):
        return "CAE", (fallas or [r.stdout[-300:]])[:3]
    return "SOBREVIVE", []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = ORIGINAL.read_text(encoding="utf-8")
    base, _ = correr(src)
    print("base sin mutar (tiene que ser SOBREVIVE = todo verde):", base)
    cuenta = {}
    for nombre, viejo, nuevo in MUTACIONES:
        if src.count(viejo) != 1:
            print(f"{nombre}: BLANCO NO ÚNICO ({src.count(viejo)})")
            cuenta["blanco"] = cuenta.get("blanco", 0) + 1
            continue
        res, det = correr(src.replace(viejo, nuevo))
        cuenta[res] = cuenta.get(res, 0) + 1
        print(f"{nombre}: {res} | {' ; '.join(d[:110] for d in det)}")
    print("resumen:", cuenta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
