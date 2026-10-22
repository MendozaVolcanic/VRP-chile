# -*- coding: utf-8 -*-
"""Verificador: de las bajas de la tabla en la ventana de 60 dias (historia.json), cuantas estan en la union de hoy
(2e1bc0e31) y en la del 14-oct (f3b414213), por estrato; lista las que faltan. Control: las 163 de 81dd25ce3 que
reaparecen NO deben contarse como perdidas (si se contaran, el total seria 2111, no 1948)."""
import csv, io, json, subprocess, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = r"C:\vrp-trabajo\s159-pruebas"; sys.path.insert(0, R)
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
def keys(ref, p):
    t = subprocess.run(["git", "-C", R, "show", f"{ref}:{p}"], capture_output=True, text=True, encoding="utf-8").stdout
    s = set()
    for r in csv.DictReader(io.StringIO(t)):
        v = normalize_volcano_name(r.get("Volcan"))
        if v: s.add((v, normalize_sensor(r.get("Sensor")), r["Fecha_Satelite_UTC"].strip()[:16]))
    return s
U = "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"
u19, u14, hoy = keys("2e1bc0e31", U), keys("f3b414213", U), keys("origin/main", "latest_consolidado.csv")
for f in ("historia.json", "historia_completa.json"):
    h = json.load(open(R + r"\experiments\_s159\referencia_estable\\" + f, encoding="utf-8"))
    ev = h["CONS"]["eventos"]
    rea = {tuple(e["k"]) for e in ev if e["ev"] == "reaparece"}
    bajas = {}
    for e in ev:
        if e["ev"] == "baja": bajas[tuple(e["k"])] = e
    netas = {kk: e for kk, e in bajas.items() if kk not in hoy}
    print(f, "bajas eventos", sum(e["ev"] == "baja" for e in ev), "claves", len(bajas), "reaparecen", len(rea), "netas (no estan hoy)", len(netas))
    print("   netas por estrato", dict(collections.Counter(e["estrato"] for e in netas.values())))
    print("   en union19", sum(kk in u19 for kk in netas), "en union14", sum(kk in u14 for kk in netas))
    print("   tandas netas", sorted(collections.Counter(e["t"][:16] for e in netas.values()).items()))
    for kk, e in netas.items():
        if kk not in u19: print("   FALTA en union19", kk, e["estrato"], "perdida", e["t"], "edad_h", e["edad_h"])
    # filas neta con tipo cambiante? (union guarda la ultima version que la tuvo)
print("n union19", len(u19), "union14", len(u14), "u14-u19", len(u14 - u19))
