"""C04: cuan cerca del techo de saturacion de I04 (361,77 K, se borra todo >= 361,27 K) llegan
los records VIIRS 375 de la flota; y el maximo VRP por pixel observado por sensor.
Instrumento: si el techo nunca se alcanza, el maximo de t_max_k queda lejos de 361 K; si se
alcanza, el pixel saturado se vuelve NaN y no aparece, asi que una cola que se corta justo bajo
361,27 K seria la huella. Denominador: todos los records de los 11 Tier A, toda la historia.
"""
import io, json, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
filas = []
for fn in glob.glob("data/mirova_equivalent/*.json"):
    if os.path.getsize(fn) < 3_000_000:
        continue
    v = os.path.basename(fn)[:-5]
    for r in json.load(open(fn, encoding="utf-8"))["records"]:
        s = r["sensor"]
        fam = "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
        aps = r.get("anomaly_pixels") or []
        pxmax = max([p["vrp_mw"] for p in aps], default=0)
        btmax = max([p["bt_k"] for p in aps], default=0)
        filas.append((v, fam, r["datetime_utc"], r.get("t_max_k") or 0, btmax, pxmax))
for fam in ("V375", "V750", "MODIS"):
    f = [x for x in filas if x[1] == fam]
    print(fam, "records:", len(f))
    print("  top 8 por bt de pixel alertado:")
    for x in sorted(f, key=lambda x: -x[4])[:8]:
        print("   ", x)
    print("  top 5 por VRP de un pixel:")
    for x in sorted(f, key=lambda x: -x[5])[:5]:
        print("   ", x)
    for lim in (340, 350, 355, 360):
        print(f"  records con pixel alertado >= {lim} K:", sum(1 for x in f if x[4] >= lim))
