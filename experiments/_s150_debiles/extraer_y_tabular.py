# -*- coding: utf-8 -*-
"""S150 (alertas debiles que `max` pierde). Paso 1: extrae las salidas de los brazos B y F de abril a
agosto (git archive CON RUTA, a un temporal fuera del repo), une los runs de cada mes (el posterior
pisa: en abril, 37823348991 repite Chaiten del brazo B) y arma la tabla por pasada con el MISMO
armar_tabla.py del pre-registro y las referencias congeladas de cada mes.

  python extraer_y_tabular.py --tmp <dir temporal>

No toca el repo salvo `git fetch` de ramas s146-ab/*. El temporal se borra a mano al terminar.
"""
import argparse, io, json, shutil, subprocess, sys, tarfile
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
PRE = RAIZ / "experiments" / "_s149_prereg_invierno"
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
MESES = {   # nombre: (desde, hasta, runs en orden; el posterior pisa)
    "abril": ("2026-04-01", "2026-04-30", ["35639417826", "37823348991"]),
    "mayo": ("2026-05-01", "2026-05-31", ["35599902448"]),
    "junio": ("2026-06-01", "2026-06-30", ["35675490175"]),
    "julio": ("2026-07-01", "2026-07-31", ["35728617326"]),
    "agosto": ("2026-08-01", "2026-08-27", ["35759688167"]),
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tmp", required=True); a = ap.parse_args()
    tmp = Path(a.tmp); tmp.mkdir(parents=True, exist_ok=True)
    for mes, (d0, d1, runs) in MESES.items():
        base = tmp / mes
        for r in runs:
            subprocess.run(["git", "fetch", "-q", "origin", "refs/heads/s146-ab/%s:refs/remotes/origin/s146-ab/%s" % (r, r)], cwd=RAIZ, check=True)
            for perfil in (B, F):
                ruta = "experiments/_s146_ab_sin_test1/salidas/%s/%s" % (r, perfil)
                ls = subprocess.run(["git", "ls-tree", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, text=True).stdout
                if not ls.strip():
                    continue
                tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
                with tarfile.open(fileobj=io.BytesIO(tar)) as t:
                    for m in t.getmembers():
                        if m.isfile() and m.name.endswith(".json"):
                            dst = base / perfil / Path(m.name).name   # el run posterior pisa
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            dst.write_bytes(t.extractfile(m).read())
                            print("  %s %s %s <- run %s" % (mes, perfil, dst.name, r))
        C = PRE / "_congelado" / mes
        out = base / "tabla.json"
        p = subprocess.run([sys.executable, str(PRE / "armar_tabla.py"), "--control", str(base / B), "--brazo", str(base / F),
                            "--cons", str(C / "registro_vrp_consolidado.csv"), "--ocr", str(C / "registro_vrp_ocr.csv"),
                            "--desde", d0, "--hasta", d1, "--out", str(out)], capture_output=True, text=True, encoding="utf-8")
        print("==", mes, p.stdout.strip(), "| rc", p.returncode)
        if p.returncode:
            print(p.stderr[-2000:])


if __name__ == "__main__":
    main()
