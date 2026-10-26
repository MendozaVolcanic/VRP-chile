# S159 M: cortes extra sobre analizar_m_tabla.json + jsonl (por volcan, el record que A no reproduce, cambios).
# Uso: python extra_m.py <dir_con_jsonl>
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
t = json.load(open(AQUI / "analizar_m_tabla.json", encoding="utf-8"))
filas = {(json.loads(l)["objetivo"]["volcan"], json.loads(l)["objetivo"]["granulo"]): json.loads(l)
         for p in Path(sys.argv[1]).rglob("probe_m_parte*.jsonl") for l in open(p, encoding="utf-8")}


def med(x):
    x = [v for v in x if v is not None]
    return round(st.median(x), 3) if x else None


print("== Distancia del centroide del cumulo al crater, A contra B, por volcan (S1+S2+S3, records con cumulo en los dos)")
por = defaultdict(list)
for f in t:
    if f["objetivo"]["estrato"][:2] in ("S1", "S2", "S3"):
        r = filas[(f["objetivo"]["volcan"], f["objetivo"]["granulo"])]
        a = ((r["rec_A"] or {}).get("pc") or {}).get("centroid_dist_km")
        b = ((r["rec_B"] or {}).get("pc") or {}).get("centroid_dist_km")
        if a is not None and b is not None:
            por[f["objetivo"]["volcan"]].append((a, b, f["objetivo"]["estrato"][:2]))
for v in sorted(por, key=lambda v: -len(por[v])):
    l = por[v]
    print(f"{v:20s} n={len(l):2d}  A med {med([x for x,_,_ in l])}  B med {med([y for _,y,_ in l])}  B mas cerca en {sum(1 for x,y,_ in l if y<x)}")

print("\n== Records donde A no reproduce el record publicado en data/")
for f in t:
    if not f["reproduce"]:
        r = filas[(f["objetivo"]["volcan"], f["objetivo"]["granulo"])]
        o = f["objetivo"]
        print(o["volcan"], o["datetime_utc"], "data:", o["distance_class"], o["pc_vrp_mw"], o["codigo_sha"],
              "| A:", (r["rec_A"] or {}).get("distance_class"), ((r["rec_A"] or {}).get("pc") or {}).get("vrp_mw"))

print("\n== Records con cambio de clase o de publicacion: posicion del pixel de A respecto del inner con cada geolocalizacion")
vols = __import__("yaml").safe_load(open(AQUI.parents[2] / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
inner = {v["name"]: v.get("inner_radius_km") for v in vols}
for f in t:
    if f["clase_cambia"] or f["pub_cambia"]:
        r = filas[(f["objetivo"]["volcan"], f["objetivo"]["granulo"])]
        o = f["objetivo"]
        a, b = r["rec_A"] or {}, r["rec_B"] or {}
        pa, pb = a.get("pc") or {}, b.get("pc") or {}
        print(f"{o['estrato'][:2]} {o['volcan']:20s} {o['datetime_utc']} cen {o['cenit']:5.1f} inner {inner[o['volcan']]} | "
              f"A: {a.get('distance_class')} d_pc {pa.get('centroid_dist_km')} vrp {pa.get('vrp_mw')} n1p_sum {a.get('diag_n_first_pass_summit')} | "
              f"B: {b.get('distance_class')} d_pc {pb.get('centroid_dist_km')} vrp {pb.get('vrp_mw')} n1p_sum {b.get('diag_n_first_pass_summit')} | "
              f"t_bg {a.get('t_bg_k')}->{b.get('t_bg_k')}")

print("\n== Control de seleccion: distancia al crater A contra B SOLO en records con el MISMO conjunto de pixeles (Lascar, S1+S2+S3)")
l = []
for f in t:
    o = f["objetivo"]
    if o["volcan"] == "Lascar" and o["estrato"][:2] in ("S1", "S2", "S3") and f["mismos_pix"]:
        r = filas[(o["volcan"], o["granulo"])]
        a = ((r["rec_A"] or {}).get("pc") or {}).get("centroid_dist_km")
        b = ((r["rec_B"] or {}).get("pc") or {}).get("centroid_dist_km")
        if a is not None and b is not None:
            l.append((a, b))
print(f"n={len(l)}  A med {med([x for x,_ in l])}  B med {med([y for _,y in l])}  B mas cerca en {sum(1 for x,y in l if y<x)}")

print("\n== Componente hacia el sensor y desplazamiento total en el pixel del crater, por lado REAL y cenit (todos los estratos)")
import math
b = defaultdict(list)
for f in t:
    g = f["geo_crater"]
    z = g["cenit"]
    zb = "<10" if z < 10 else ("10-40" if z < 40 else ("40-50" if z < 50 else ">=50"))
    b[(f["lado_real"], zb)].append((g["obs_hacia_sensor_km"], g["obs_traza_km"], f["total_crater"]))
for k in sorted(b):
    l = b[k]
    print(f"lado {k[0]:4s} cenit {k[1]:6s} n={len(l):2d}  hacia sensor med {med([x for x,_,_ in l])}  traza med {med([y for _,y,_ in l])}"
          f"  total med {med([z for _,_,z in l])}  total max {round(max(z for _,_,z in l),2)}")
