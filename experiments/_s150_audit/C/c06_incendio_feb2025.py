"""C06: misma pasada, dos sensores, sobre una fuente fuerte (incendio a 15-19 km de NdC, feb-2025).
Pregunta: la energia que ve V375 (I04, techo 361,27 K) frente a la que ve V750 (M13, techo 633,5 K)
sobre el mismo objeto. Si I04 saturara y se borrara el pixel, V375 veria mucho menos que V750 y su
pixel mas caliente quedaria bajo 361 K. Instrumento: suma de anomaly_pixels + discarded_anomaly_pixels
entre 12 y 22 km (los dos sensores guardan los mismos campos). Limite: top-100 por record.
Nulo/contraste: la razon V375/V750 en pasadas debiles del mismo objeto deberia ser parecida si no
hay saturacion; si cae en las fuertes, es la huella.
"""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = json.load(open("data/mirova_equivalent/NevadosDeChillan.json", encoding="utf-8"))
por = {}
for r in d["records"]:
    if not ("2025-02-14" <= r["datetime_utc"] <= "2025-03-05"):
        continue
    s = r["sensor"]
    if s.startswith("MODIS"):
        continue
    base = s.replace("_750", "")
    px = (r.get("anomaly_pixels") or []) + (r.get("discarded_anomaly_pixels") or [])
    sel = [p for p in px if 12 <= p["dist_km"] <= 22]
    por.setdefault((r["datetime_utc"], base), {})["750" if s.endswith("_750") else "375"] = (
        round(sum(p["vrp_mw"] for p in sel), 2), len(sel), max([p["bt_k"] for p in sel], default=0),
        r.get("t_max_k"), len(px))
print("dt sat | V375 (suma, n, bt_max, t_max, n_px_guardados) | V750 (idem) | razon 375/750")
for k in sorted(por):
    a = por[k].get("375"); b = por[k].get("750")
    if a and b and b[0] > 1:
        print(k, a, b, round(a[0] / b[0], 2) if b[0] else None)
