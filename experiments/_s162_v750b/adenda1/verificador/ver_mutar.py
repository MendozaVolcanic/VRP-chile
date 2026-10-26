# -*- coding: utf-8 -*-
"""Verificador de la adenda 1: mutaciones PROPIAS del compañero (no las 7 del autor), para ver cuáles sobreviven a
`probar_adenda1.py`. Cada copia vive en esta carpeta (con la ruta de importación del analizador corregida) y se borra al
terminar. Clasificación igual que `mutar_adenda1.py`: PASA (sobrevive), ATRAPADA (rc 1 con FALLAS), CAÍDA (rc 2).
Uso: python ver_mutar.py --evaluador <evaluar_d25.py> --dest <carpeta>"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ADE = AQUI.parent
ORIG = ADE / "cobertura_cajas_v750b.py"
V750B = ADE.parent
MUT = [
    ("V1 identidad (copia con ruta corregida)", None, None),
    ("V2 2 % estricto: <= pasa a <", "n_sin <= AB.MAX_SIN_DATO * den", "n_sin < AB.MAX_SIN_DATO * den"),
    ("V3 denominador sin restar fuera y sin_crater",
     ' - no_obs["fuera"] - no_obs["sin_crater"])', ")"),
    ("V4 denominador sin las sin gránulo", "len(obj) + len(sin_g) - no_obs", "len(obj) - no_obs"),
    ("V5 una protegida sin gránulo no frena",
     'prot_sin += [(x["volcan"], x["hora_utc"]) for x in sin_g if x.get("protegida")]',
     'prot_sin += [(x["volcan"], x["hora_utc"]) for x in sin_g if False]'),
    ("V6 una protegida SIN DATO del analizador no frena", "for i in sin + falta if", "for i in falta if"),
    ("V7 cuenta también las sin_crater sin cajas", 'part[i] == "observada" and res[i].get("dayflag") == 0 and cajas',
     'part[i] in ("observada", "sin_crater") and res[i].get("dayflag") == 0 and cajas'),
    ("V8 dayflag ausente deja de ser SIN DATO", 'res[i].get("dayflag") != 0)]', 'res[i].get("dayflag") == 1)]'),
    ("V9 caja {} deja de ser faltante: ya es así (control)", "not isinstance(orc.get(c), dict)",
     "not isinstance(orc.get(c), dict)"),
    ("V10 caja {} pasa a ser faltante", "not isinstance(orc.get(c), dict)", "not orc.get(c)"),
    ("V11 lista de protegidas siempre ninguna", 'print("   protegidas SIN DATO:", prot_sin or "ninguna")',
     'print("   protegidas SIN DATO:", "ninguna")'),
    ("V12 falta caja no se nombra con su caja", "cajas faltantes {cajas_faltantes(res[i])}", "cajas faltantes []"),
    ("V13 salida 3 pasa a 1", "return 0 if cob_ok else 3", "return 0 if cob_ok else 1"),
    ("V14 sg_ok ignorado sólo para pasadas protegidas", "cob_ok = sg_ok and n_sin", "cob_ok = (sg_ok or prot_sin) and n_sin"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    src = ORIG.read_text(encoding="utf-8")
    puente = "sys.path.insert(0, str(AQUI.parent))"
    assert src.count(puente) == 1
    src = src.replace(puente, f"sys.path.insert(0, {str(V750B)!r})")
    src = src.replace('AQUI = Path(__file__).resolve().parent', f'AQUI = Path({str(ADE)!r})')
    for nombre, viejo, nuevo in MUT:
        if a.solo and a.solo not in nombre:
            continue
        if viejo is not None and src.count(viejo) != 1:
            print(f"{nombre}: la línea aparece {src.count(viejo)} veces: INVÁLIDA")
            continue
        copia = AQUI / f"_vm_{re.sub(r'[^A-Za-z0-9]+', '_', nombre)[:30]}.py"
        copia.write_text(src if viejo is None else src.replace(viejo, nuevo), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(ADE / "probar_adenda1.py"), "--companero", str(copia),
                                "--evaluador", a.evaluador, "--dest", str(a.dest / copia.stem)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        finally:
            copia.unlink()
        out = r.stdout + r.stderr
        if r.returncode == 0 and "TODOS LOS CHEQUEOS COMO SE ESPERA" in out:
            estado = "SOBREVIVE (la batería pasa)"
        elif r.returncode == 2 and "CAÍDA DEL COMPAÑERO" in out:
            estado = "CAÍDA"
        elif r.returncode == 1 and "FALLAS" in out:
            estado = "ATRAPADA"
        else:
            estado = f"OTRA ({r.returncode})"
        f = re.search(r"FALLAS \(\d+\): (.*)", out)
        print(f"{nombre}: {estado}" + (f" | {f.group(1)[:140]}" if f else ""), flush=True)


if __name__ == "__main__":
    main()
