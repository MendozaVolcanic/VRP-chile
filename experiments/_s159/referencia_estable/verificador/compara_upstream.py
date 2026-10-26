# -*- coding: utf-8 -*-
"""Compara versiones upstream de Mirova-v1 por clave (volcan normalizado, sensor normalizado, minuto)
con la misma normalizacion que historia_referencia.py. Imprime n filas, duplicados, bajas/altas vs la primera."""
import csv, io, sys, urllib.request, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\vrp-trabajo\s159-pruebas")
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
REPO = "MendozaVolcanic/Mirova-v1"
def leer(ref, P="monitoreo_satelital/registro_vrp_consolidado.csv"):
    if ref.startswith("local:"):
        import subprocess
        t = subprocess.run(["git", "-C", r"C:\vrp-trabajo\s159-pruebas", "show", ref[6:] + ":latest_consolidado.csv"],
                           capture_output=True, text=True, encoding="utf-8").stdout
    else:
        t = urllib.request.urlopen(f"https://raw.githubusercontent.com/{REPO}/{ref}/{P}", timeout=60).read().decode("utf-8", "replace")
    d, dup, notier = {}, 0, 0
    for r in csv.DictReader(io.StringIO(t)):
        v = normalize_volcano_name(r.get("Volcan"))
        if not v: notier += 1; continue
        k = (v, normalize_sensor(r.get("Sensor")), (r.get("Fecha_Satelite_UTC") or "")[:16])
        if k in d: dup += 1
        d[k] = r
    return d, dup, notier
refs = sys.argv[1:]
base, *_ = leer(refs[0]); print(refs[0], len(base))
for ref in refs[1:]:
    d, dup, nt = leer(ref)
    baja = [k for k in base if k not in d]; alta = [k for k in d if k not in base]
    prot = [k for k in baja if base[k]["Tipo_Registro"].startswith("ALERTA") and float(base[k]["VRP_MW"] or 0) >= 1]
    print(ref, "n", len(d), "dup", dup, "no_tier", nt, "bajas", len(baja), "altas", len(alta), "protegidas_bajas", sorted(prot))
    print("   bajas por mes de pasada", sorted(collections.Counter(k[2][:7] for k in baja).items()))
