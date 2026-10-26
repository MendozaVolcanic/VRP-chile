# -*- coding: utf-8 -*-
"""Segunda vuelta: reproduce, en copias `_v2_<id>_...`, las mutaciones del autor que tocan L2, L4, L7 y L18
(M15, M29, M50, M52, M53, M54, M55, M56) y las corre SOLO contra los escenarios que LECTURAS dice que las fijan,
para no duplicar la batería entera del medidor del autor (que corre en paralelo). Una mutación cuenta como atrapada
sólo si la batería sale 1 (falla por aserción) y ningún escenario cae.
Uso: python ver2_mut_autor.py --dest <tmp> --evaluador <evaluar_d25.py>"""
import argparse
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CARPETA = AQUI.parent
sys.path.insert(0, str(CARPETA))
import mutar_evaluar_v750a as MU  # noqa: E402

SEL = {"M15": "E14,E28,E29,E50,E52", "M29": "E14,E28,E50,E52", "M50": "E30", "M52": "E06,E07,E31",
       "M53": "E14,E28,E52", "M54": "E28", "M55": "E28,E50", "M56": "E10,E11,E38,E51"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True)
    a = ap.parse_args()
    a.dest.mkdir(parents=True, exist_ok=True)
    L = []
    for nom, sel in SEL.items():
        que, viejo, nuevo = MU.MUTACIONES[nom]
        copia = CARPETA / f"_v2_{nom}_evaluar_v750a.py"
        src = MU.ORIGINAL.read_text(encoding="utf-8")
        assert src.count(viejo) == 1, (nom, src.count(viejo))
        copia.write_text(src.replace(viejo, nuevo), encoding="utf-8")
        try:
            o = subprocess.run([sys.executable, str(MU.PRUEBAS), "--dest", str(a.dest / f"mut_{nom}"), "--analizador",
                                str(copia), "--evaluador", a.evaluador, "--solo", sel], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=7200, cwd=str(CARPETA))
        finally:
            copia.unlink()
        txt = o.stdout + o.stderr
        linea = next((x for x in txt.splitlines() if x.startswith("== PRUEBAS")), "(sin línea)")
        fallan = [x.split(" | ")[0] for x in txt.splitlines() if " | FALLA" in x]
        est = "ATRAPADA" if o.returncode == 1 else ("CAÍDA" if o.returncode == 2 else "PASA")
        s = f"{nom} [{sel}] | {est} | rc {o.returncode} | {que} | {linea} | fallan {fallan}"
        print(s, flush=True)
        L.append(s)
    (a.dest / "mut_autor_v2_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
