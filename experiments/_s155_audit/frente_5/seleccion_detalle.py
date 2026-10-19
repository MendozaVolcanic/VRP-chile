# -*- coding: utf-8 -*-
"""S155 frente 5: detalle de seleccion en las pasadas protegidas donde el tablero publica < 0,9 del total alertado
a <= 5 km. Imprime cada pixel alertado (posicion, distancia al centro del volcan, BT, VRP) y marca si pertenece al
cumulo publicado (reconstruccion por centroide para n <= 3, ver pareo_pasadas.miembros_cumulo; para n > 3 se marca
'?'). Ademas, la distancia de cada pixel al centroide publicado. Pregunta del instrumento: si la reconstruccion de
miembros estuviera rota, la suma de los marcados no daria pc_sum; se imprime la comprobacion."""
import io, json, math, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
_o = sys.stdout
import pareo_pasadas as PP  # noqa
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp, dl = p2 - p1, math.radians(d - b)
    return 2 * R * math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
recs = {(r["datetime_utc"][:16], PP.bucket(r["sensor"])): r for r in json.load(open(
    os.path.join(PP.WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]}
ok = json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))
casos = [f for f in ok if f["Rpub"] < 0.9 * f["Rinner"]]
print("casos: %d" % len(casos))
for f in casos:
    r = recs[(f["t"], f["b"])]; pc = r["primary_cluster"]; pix = r["anomaly_pixels"]
    miem = PP.miembros_cumulo(pc, pix) if pc.get("n_pixels", 9) <= 3 else None
    ids = {id(p) for p in miem} if miem else set()
    print("\n%s %s sat=%s zen=%.1f MIROVA=%.2f (dist %s) | pub=%.2f pc_n=%s spm=%s pc_sum=%.2f inner=%.2f nclu=%s granulo=%s" % (
        f["t"], f["b"], r["sensor"], f["zen"], f["mir"], f["dist_mir"], f["pub"], pc["n_pixels"], pc.get("single_pixel_mode"),
        f["pc_sum"], f["inner"], r["n_hotspots_clustered"], r["granule"]))
    for p in pix:
        tag = "PUB" if id(p) in ids else ("?" if miem is None else "fuera")
        print("   %-5s lat=%.5f lon=%.5f dist_volcan=%.2f dist_centroide=%.2f bt=%.2f vrp=%.3f" % (
            tag, p["lat"], p["lon"], p["dist_km"], hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]),
            p["bt_k"], p["vrp_mw"]))
    if miem:
        print("   control: suma de PUB = %.3f (pc_sum %.3f)" % (sum(p["vrp_mw"] for p in miem), f["pc_sum"]))
