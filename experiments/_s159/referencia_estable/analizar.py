# -*- coding: utf-8 -*-
"""Resume historia*.json (salida de historia_referencia.py): bajas, altas tardias, cambios,
cobertura por la union historica. Todos los numeros del INFORME salen de aca.

Uso: python -I analizar.py historia.json [--union <csv>] [--ocr <csv>]
"""
import argparse
import collections
import csv
import io
import json
import subprocess
import sys

REPO = r"C:\vrp-trabajo\s159-pruebas"
sys.path.insert(0, REPO)
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name  # noqa: E402

UNION = "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"
OCR = "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"


def k(row):
    v = normalize_volcano_name(row["Volcan"])
    return (v, normalize_sensor(row["Sensor"]), row["Fecha_Satelite_UTC"].strip()[:16]) if v else None


def claves_git(ruta, ref="origin/main"):
    txt = subprocess.run(["git", "-C", REPO, "show", f"{ref}:{ruta}"], capture_output=True, text=True,
                         encoding="utf-8").stdout
    return {k(x): x for x in csv.DictReader(io.StringIO(txt))}


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("historia")
    a = ap.parse_args()
    r = json.load(open(a.historia, encoding="utf-8"))
    uni, ocr = claves_git(UNION), claves_git(OCR)
    print("ventana desde", r["desde"], "ref", r["ref"][:9])
    print("autotest", json.dumps(r["autotest"]))
    for c in ("CONS", "OCR"):
        vs, ev = r[c]["versiones"], r[c]["eventos"]
        print(f"\n== {c}: versiones {len(vs)} (base {vs[0]['fecha']} n={vs[0].get('n')}, ultima {vs[-1]['fecha']} "
              f"n={vs[-1].get('n')}), duplicados max {r[c]['dups_max']}, variantes de nombre {len(r[c]['variantes'])}")
        print("   eventos", dict(collections.Counter(e["ev"] for e in ev)),
              " solo metadatos", sum(v.get("solo_meta", 0) for v in vs))
        cambios = [e for e in ev if e["ev"] == "cambio"]
        if cambios:
            print("   cambios por campo", dict(collections.Counter(f for e in cambios for f in e["campos"])))
            print("   cambios por estrato viejo->nuevo",
                  collections.Counter((e["estrato"], e["estrato_nuevo"]) for e in cambios).most_common(12))
            print("   edad del cambio (h) p50/p90/max", pct([e["edad_h"] for e in cambios], .5),
                  pct([e["edad_h"] for e in cambios], .9), max(e["edad_h"] for e in cambios))
            print("   cambios por sensor", dict(collections.Counter(e["k"][1] for e in cambios)))
        bajas = [e for e in ev if e["ev"] == "baja"]
        if bajas:
            print("   bajas por estrato", dict(collections.Counter(e["estrato"] for e in bajas)))
            print("   bajas por sensor", dict(collections.Counter(e["k"][1] for e in bajas)))
            print("   bajas por evento", [(v["sha"], v["fecha"][:16], v["baja"], v["alta"]) for v in vs if v.get("baja")])
            print("   edad minima de una fila perdida (h)", min(e["edad_h"] for e in bajas))
            print("   bajas en union_historica de hoy", sum(tuple(e["k"]) in uni for e in bajas), "de", len(bajas))
            print("   reaparecen", sum(1 for e in ev if e["ev"] == "reaparece"))
            for e in sorted((e for e in bajas if e["estrato"] == "alerta_>=1MW"), key=lambda e: e["k"][2]):
                o = ocr.get(tuple(e["k"]))
                print("     PROTEGIDA", tuple(e["k"]), e["viejo"]["vrp"], "MW perdida", e["t"][:16],
                      "| union", tuple(e["k"]) in uni, "| OCR", (o["Tipo_Registro"], o["VRP_MW"]) if o else None)
        altas = [e for e in ev if e["ev"] == "alta"]
        g = collections.defaultdict(list)
        for e in altas:
            g[("sensor", e["k"][1])].append(e["edad_h"])
            g[("estrato", e["estrato"])].append(e["edad_h"])
        for key, v in sorted(g.items()):
            print(f"   alta {key[0]}={key[1]:20s} n={len(v):5d} p50={pct(v,.5):7.1f} p90={pct(v,.9):7.1f} "
                  f"max={max(v):7.1f} >24h={sum(x>24 for x in v)} >48h={sum(x>48 for x in v)}")


if __name__ == "__main__":
    main()
