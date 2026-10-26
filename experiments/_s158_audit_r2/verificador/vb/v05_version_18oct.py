"""VB v05: version de producto y fecha de produccion del granulo en los records del 2026-10-18 (11 Tier A).
Si "el Standard todavia no los traia" fuera cierto, los records del 18-oct serian NRT o tendrian un Standard
producido despues del 21-oct 05:10 UTC. Control: el 2026-10-16 (dia que CMR hoy si tiene completo).
El sello de produccion es el 4.o campo del nombre (AAAADDDHHMMSS). Denominador: records del dia."""
import json, glob, os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
for dia in ("2026-10-16", "2026-10-18"):
    c = Counter(); sellos = []
    for f in glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json")):
        for r in json.load(open(f))["records"]:
            if r["datetime_utc"][:10] != dia: continue
            nrt = "_NRT" in r["granule"] or "NRT" in r["granule"].split(".")[3:4]
            c[(r["sensor"].split("_")[0], r.get("product_version"), "nombre_NRT" if "_NRT" in r["granule"] else "nombre_std")] += 1
            sellos.append(r["granule"].split(".")[4] if r["granule"].count(".") >= 5 else r["granule"].split(".")[3])
    print(dia, dict(c))
    print("   sello de produccion min/max:", min(sellos), max(sellos), " (2026294 = 21-oct)")
