# -*- coding: utf-8 -*-
"""Coteja pasadas_meses_B_F.csv contra su fuente: las tablas por pasada de los meses de S150.

POR QUE (verificador del PR #810, punto 5). El CSV se commiteo porque las tablas viven en scratchpads que se
borran; hay que mostrar que es copia fiel, en VIIRS 375 y en VIIRS 750, campo por campo. Las tablas tienen
copias en dos scratchpads de la sesion S150 (f3/tabla_<mes>.json, f3/<mes>/tabla.json y, para mayo a agosto,
D/tabla_<mes>.json); se comparan tambien entre si por sha256, para saber si la fuente es una sola.

Uso: python cotejar_tablas.py <scratchpad de la sesion S150> > cotejar_salida.txt
"""
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
MESES = ["abril", "mayo", "junio", "julio", "agosto"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main(base: Path):
    print("== copias de la fuente (sha256, 16 primeros caracteres)")
    for mes in MESES:
        copias = [base / "f3" / f"tabla_{mes}.json", base / "f3" / mes / "tabla.json", base / "D" / f"tabla_{mes}.json"]
        print(f"   {mes:7s} " + "  ".join(f"{p.relative_to(base)}={sha(p)}" for p in copias if p.exists()))
    csvf = {}
    with open(AQUI / "pasadas_meses_B_F.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            csvf[(r["mes"], r["clave"])] = r
    print("\n== CSV contra f3/tabla_<mes>.json, campo por campo")
    tot = Counter()
    for mes in MESES:
        T = json.load(open(base / "f3" / f"tabla_{mes}.json", encoding="utf-8"))
        for sensor in ("VIIRS375", "VIIRS750"):
            fuente = {k: v for k, v in T["pasadas"].items() if k.split("|")[1] == sensor}
            en_csv = {k for (m, k) in csvf if m == mes and k.split("|")[1] == sensor}
            c = Counter()
            c["fuente"], c["csv"] = len(fuente), len(en_csv)
            c["faltan_en_csv"] = len(set(fuente) - en_csv)
            c["sobran_en_csv"] = len(en_csv - set(fuente))
            for k, v in fuente.items():
                r = csvf.get((mes, k))
                if r is None:
                    continue
                x = v.get("control") or v.get("brazo")
                esperado = {"lab": x["lab"], "vrp_ref": "" if x["vrp_ref"] is None else str(x["vrp_ref"]),
                            "pub_B": "" if "control" not in v else str(int(v["control"]["pub"])),
                            "pub_F": "" if "brazo" not in v else str(int(v["brazo"]["pub"])),
                            "ventana": "|".join(T["ventana"])}
                for campo, val in esperado.items():
                    if r[campo] != val:
                        c["distinto_" + campo] += 1
            print(f"   {mes:7s} {sensor}: {dict(c)}")
            tot.update(c)
    malos = sum(v for k, v in tot.items() if k.startswith(("faltan", "sobran", "distinto")))
    print(f"\n== TOTAL: pasadas en la fuente {tot['fuente']}, en el CSV {tot['csv']}, diferencias {malos}")
    return 0 if malos == 0 else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
