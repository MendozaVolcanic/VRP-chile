# -*- coding: utf-8 -*-
"""Copia a CSV, dentro del repo, lo que suma_errores.py necesita de las tablas por pasada ya medidas.

POR QUE. Las tablas por pasada (salida de armar_tabla.py) de los meses de S150 y de Chillan viven solo en
scratchpads de sesiones anteriores, que se borran. Sin ellas la suma de errores no se puede recontar. Igual que
experiments/_s151_max_v750/extraer_tablas.py, se guarda solo lo que la cuenta usa: clave, etiqueta, VRP de
MIROVA y si cada brazo publica.

Uso: python extraer_tablas.py --meses DIR_CON_tabla_<mes>.json --ndc DIR_CON_t_C0_<brazo>.json
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MESES = ["abril", "mayo", "junio", "julio", "agosto"]
BRAZOS_NDC = ["T0", "E", "B", "F", "J", "K", "KE", "KET"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meses", required=True)
    ap.add_argument("--ndc", required=True)
    a = ap.parse_args()
    filas, labs, solo_un_brazo = [], Counter(), 0
    for mes in MESES:
        T = json.load(open(Path(a.meses) / f"tabla_{mes}.json", encoding="utf-8"))
        for clave, v in sorted(T["pasadas"].items()):
            if clave.split("|")[1] not in ("VIIRS375", "VIIRS750"):
                continue
            c, b = v.get("control"), v.get("brazo")
            if c is None or b is None:
                solo_un_brazo += 1   # se conserva, con el brazo ausente en blanco (el evaluador la cuenta en el otro)
            elif c["lab"] != b["lab"] or c["vrp_ref"] != b["vrp_ref"]:
                raise ValueError(f"{mes} {clave}: etiqueta distinta entre brazos")
            x = c or b
            labs[x["lab"]] += 1
            filas.append({"mes": mes, "ventana": "|".join(T["ventana"]), "clave": clave, "lab": x["lab"],
                          "vrp_ref": "" if x["vrp_ref"] is None else x["vrp_ref"],
                          "pub_B": "" if c is None else int(c["pub"]), "pub_F": "" if b is None else int(b["pub"])})
    with open(AQUI / "pasadas_meses_B_F.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"meses: {len(filas)} pasadas VIIRS 375 y 750 -> pasadas_meses_B_F.csv; etiquetas {dict(labs)}; "
          f"pasadas en un solo brazo (el otro queda en blanco): {solo_un_brazo}")

    tabs = {n: json.load(open(Path(a.ndc) / f"t_C0_{n}.json", encoding="utf-8")) for n in BRAZOS_NDC}
    ventanas = {"|".join(t["ventana"]) for t in tabs.values()}
    if len(ventanas) != 1:
        raise ValueError(f"ventanas distintas entre tablas de Chillan: {ventanas}")
    ventana = ventanas.pop()
    claves = sorted(set().union(*(t["pasadas"] for t in tabs.values())))
    out = []
    for k in claves:
        fila = {"ventana": ventana, "clave": k}
        lab = vrp = None
        for n, t in tabs.items():
            v = t["pasadas"].get(k, {})
            for lado, nombre in (("control", "C0"), ("brazo", n)):
                if lado not in v:
                    continue
                if lab is None:
                    lab, vrp = v[lado]["lab"], v[lado]["vrp_ref"]
                elif (lab, vrp) != (v[lado]["lab"], v[lado]["vrp_ref"]):
                    raise ValueError(f"Chillan {k}: etiqueta distinta entre tablas")
                previo = fila.get("pub_" + nombre)
                if previo is not None and previo != int(v[lado]["pub"]):
                    raise ValueError(f"Chillan {k}: {nombre} publica distinto en dos tablas")
                fila["pub_" + nombre] = int(v[lado]["pub"])
        fila["lab"], fila["vrp_ref"] = lab, "" if vrp is None else vrp
        out.append(fila)
    campos = ["ventana", "clave", "lab", "vrp_ref", "pub_C0"] + ["pub_" + n for n in BRAZOS_NDC]
    with open(AQUI / "pasadas_ndc.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n", restval="")
        w.writeheader()
        w.writerows(out)
    print(f"Chillan: {len(out)} pasadas -> pasadas_ndc.csv; etiquetas {dict(Counter(f['lab'] for f in out))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
