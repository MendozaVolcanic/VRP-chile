# S159 M, VERIFICADOR con contexto limpio. Re-mide las afirmaciones 1, 2 y 4 desde los jsonl crudos del run
# 39681481914, sin usar analizar_m.py ni extra_m.py (otro codigo, mismo dato).
#
# Preguntas del instrumento:
# 1. Si la afirmacion estuviera rota, lo veria? Si: recalculo "publicado" con el predicado del tablero
#    (mirovaEqVrp + isValidDetection, extraidos de frontend/index.html y ejecutados con node) pasando el record
#    COMPLETO que guardo el probe, y clasifico cada cambio por mecanismo (deteccion perdida, clase, magnitud a 0,
#    centroide fuera del inner).
# 2. Si el instrumento estuviera muerto, se veria distinto? Control positivo del arnes: casos sinteticos con
#    resultado conocido (dentro del inner > 0, fuera = 0, far = 0, pc nulo con vrp_mw 0 = 0, pc con 0,0 MW = 0).
# Uso: python verif_m.py <dir_jsonl>
import json
import math
import re
import statistics as st
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")
from pipeline.geo_utils import get_detection_anchor  # noqa: E402


def hav(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def med(x):
    x = [v for v in x if v is not None]
    return round(st.median(x), 3) if x else None


def node_pub(recs):
    src = open(RAIZ / "frontend" / "index.html", encoding="utf-8").read()
    f1 = re.search(r"function mirovaEqVrp\(r, innerKm = 10, includeFar = false\) \{.*?\n\}\n", src, re.S).group(0)
    f2 = re.search(r"function isValidDetection\(r\) \{.*?\n\}\n", src, re.S).group(0)
    js = (f1 + f2 + "\nconst d=require(process.argv[2]);\n"
          "console.log(JSON.stringify(d.map(([r,k])=>[mirovaEqVrp(r,k,false), isValidDetection(r)])));\n")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "f.js").write_text(js, encoding="utf-8")
        (Path(td) / "d.json").write_text(json.dumps(recs), encoding="utf-8")
        out = subprocess.run(["node", str(Path(td) / "f.js"), str(Path(td) / "d.json")], capture_output=True,
                             text=True, check=True).stdout
    return json.loads(out)


def completo(r):
    """Record del probe con la forma del JSON de data/ (pc -> primary_cluster)."""
    if r is None:
        return {}
    d = {k: v for k, v in r.items() if k not in ("pc", "anomaly_pixels")}
    d["primary_cluster"] = r.get("pc")
    d["sensor"] = "MODIS_X"
    return d


def main():
    d = Path(sys.argv[1])
    fs = [json.loads(l) for p in sorted(d.rglob("probe_m_parte*.jsonl")) for l in open(p, encoding="utf-8")]
    vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    print("filas", len(fs), "errores", sum("error" in f for f in fs))

    # --- control positivo del arnes
    ctl = [[{"primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 1.0}, "distance_class": "summit"}, 5],
           [{"primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 6.0}, "distance_class": "summit"}, 5],
           [{"primary_cluster": {"vrp_mw": 2.0, "centroid_dist_km": 1.0}, "distance_class": "far"}, 5],
           [{"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0}, 5],
           [{"primary_cluster": {"vrp_mw": 0.0, "centroid_dist_km": 1.0}, "distance_class": "summit"}, 5],
           [{"primary_cluster": None, "distance_class": None, "vrp_mw": 0.7}, 5]]
    print("control arnes (esperado 2,0,0,0,0,0.7):", node_pub(ctl))

    lote = []
    for f in fs:
        k = vols[f["objetivo"]["volcan"]].get("inner_radius_km") or 10
        lote += [[completo(f["rec_A"]), k], [completo(f["rec_B"]), k]]
    pub = node_pub(lote)
    for n, f in enumerate(fs):
        f["pA"], f["vA"] = pub[2 * n]
        f["pB"], f["vB"] = pub[2 * n + 1]

    # --- afirmacion 1
    print("\n== Afirmacion 1: S1 + S2")
    s12 = [f for f in fs if f["objetivo"]["estrato"][:2] in ("S1", "S2")]
    # cenit por MxD03 en el crater y por el record
    print("n", len(s12), "cenit objetivo min", min(f["objetivo"]["cenit"] for f in s12),
          "cenit MxD03 crater min", round(min(f["geo_crater"]["cenit"] for f in s12), 2),
          "clase data", Counter(f["objetivo"]["distance_class"] for f in s12))
    pubA = sum(1 for f in s12 if f["pA"] > 0)
    pubB = sum(1 for f in s12 if f["pB"] > 0)
    incoh = sum(1 for f in s12 if (f["pA"] > 0) != f["vA"] or (f["pB"] > 0) != f["vB"])
    print("publicados A", pubA, "B", pubB, "| incoherencias mirovaEqVrp vs isValidDetection:", incoh)
    camb = [f for f in s12 if (f["pA"] > 0) != (f["pB"] > 0)]
    print("cambios", len(camb), "apagan", sum(1 for f in camb if f["pA"] > 0), "encienden",
          sum(1 for f in camb if f["pB"] > 0))
    print("\nmecanismo de cada cambio (A -> B):")
    mec = Counter()
    for f in camb:
        o = f["objetivo"]
        v = vols[o["volcan"]]
        alat, alon = get_detection_anchor(v)
        inner = v.get("inner_radius_km")
        a, b = f["rec_A"], f["rec_B"]
        pa, pb = a.get("pc") or {}, b.get("pc") or {}
        if not pa or not pb:
            m = "deteccion perdida" if pa else "deteccion ganada"
        elif a.get("distance_class") != b.get("distance_class"):
            m = f"clase {a.get('distance_class')}->{b.get('distance_class')}"
        elif (pa.get("vrp_mw") or 0) > 0 and (pb.get("vrp_mw") or 0) == 0 or (pa.get("vrp_mw") or 0) == 0 and (pb.get("vrp_mw") or 0) > 0:
            m = "magnitud cruza 0 (cumulo en los dos brazos, misma clase)"
        else:
            m = "otro"
        mec[m] += 1
        # posicion en B de los pixeles calientes de A (A + desplazamiento MxD03 en el mismo i,j)
        pix = a.get("anomaly_pixels") or []
        dp = f["desp_pixeles_A"]
        filas = []
        for q, s in zip(pix, dp):
            dA = hav(alat, alon, q["lat"], q["lon"])
            latB = q["lat"] + s["dn_km"] / 111.32
            lonB = q["lon"] + s["de_km"] / (111.32 * math.cos(math.radians(q["lat"])))
            dB = hav(alat, alon, latB, lonB)
            filas.append((round(dA, 2), round(dB, 2), q.get("bt_k")))
        dentroA = [x for x in filas if x[0] <= inner]
        print(f"  {o['estrato'][:2]} {o['volcan'][:14]:14s} {o['datetime_utc']} cen {f['geo_crater']['cenit']:.1f} inner {inner} "
              f"| A {a.get('distance_class')} pc_d {pa.get('centroid_dist_km')} vrp {pa.get('vrp_mw')} n1ps {a.get('diag_n_first_pass_summit')} "
              f"n1p {a.get('diag_n_first_pass_pixels')} | B {b.get('distance_class')} pc_d {pb.get('centroid_dist_km')} vrp {pb.get('vrp_mw')} "
              f"n1ps {b.get('diag_n_first_pass_summit')} n1p {b.get('diag_n_first_pass_pixels')} | tbg {a.get('t_bg_k')}->{b.get('t_bg_k')} "
              f"| {m}")
        print(f"      pixeles de A dentro del inner (d_A, d_B si MxD03, bt): {dentroA[:6]}  (total pix A {len(filas)})")
    print("mecanismos:", dict(mec))

    # --- afirmacion 2
    print("\n== Afirmacion 2: desplazamiento total en el pixel del crater por lado real y cenit (todas las filas)")
    b2 = defaultdict(list)
    for f in fs:
        g = f["geo_crater"]
        z = g["cenit"]
        zb = "<10" if z < 10 else ("10-40" if z < 40 else ("40-50" if z < 50 else ">=50"))
        lado = "f0" if g["frame"] < (f["n_frames"] - 1) / 2 else "otro"
        assert lado == ("f0" if g["volcan_del_lado_del_frame0"] else "otro")
        b2[(lado, zb)].append((math.hypot(g["obs_barrido_km"], g["obs_traza_km"]), g["obs_hacia_sensor_km"],
                               f["objetivo"]["volcan"], f["objetivo"]["granulo"]))
    for k in sorted(b2):
        l = b2[k]
        print(f"  {k}: n={len(l)} total med {med([x[0] for x in l])} hacia sensor med {med([x[1] for x in l])} "
              f"max {round(max(x[0] for x in l), 2)}  granulos unicos {len({x[3] for x in l})}")
    # sin S4/S5 (solo summit S1-S3), para ver si la mezcla de estratos mueve la mediana
    print("  solo S1-S3:")
    b3 = defaultdict(list)
    for f in fs:
        if f["objetivo"]["estrato"][:2] not in ("S1", "S2", "S3"):
            continue
        g = f["geo_crater"]
        z = g["cenit"]
        zb = "<10" if z < 10 else ("10-40" if z < 40 else ("40-50" if z < 50 else ">=50"))
        lado = "f0" if g["volcan_del_lado_del_frame0"] else "otro"
        b3[(lado, zb)].append(math.hypot(g["obs_barrido_km"], g["obs_traza_km"]))
    for k in sorted(b3):
        print(f"    {k}: n={len(b3[k])} total med {med(b3[k])}")
    # el pixel caliente del cumulo (metrica 1) contra el crater: consistencia
    # independencia: hay volcanes repetidos? por volcan en f0 40-50
    print("  volcanes en (f0, 40-50):", Counter(x[2] for x in b2[("f0", "40-50")]))
    print("  volcanes en (f0, >=50):", Counter(x[2] for x in b2[("f0", ">=50")]))
    print("  volcanes en (otro, 40-50):", Counter(x[2] for x in b2[("otro", "40-50")]))
    print("  volcanes en (otro, >=50):", Counter(x[2] for x in b2[("otro", ">=50")]))

    # --- afirmacion 4
    print("\n== Afirmacion 4: Lascar, mismos pixeles en A y B")
    las = [f for f in fs if f["objetivo"]["volcan"] == "Lascar" and f["objetivo"]["estrato"][:2] in ("S1", "S2", "S3")]
    v = vols["Lascar"]
    alat, alon = get_detection_anchor(v)
    print("ancla Lascar", alat, alon, "vent en yaml", v.get("vent_lat"), v.get("vent_lon"))
    mismos = []
    for f in las:
        a, b = f["rec_A"], f["rec_B"]
        pa, pb = a.get("pc") or {}, b.get("pc") or {}
        same_ij = sorted(map(tuple, f["ij_A"])) == sorted(map(tuple, f["ij_B"]))
        if not (same_ij and pa and pb):
            continue
        # comprobacion propia: misma cantidad de pixeles, mismo VRP del cumulo, mismos BT
        btA = sorted(round(q["bt_k"], 2) for q in a["anomaly_pixels"])
        btB = sorted(round(q["bt_k"], 2) for q in b["anomaly_pixels"])
        # distancia recomputada del centroide (no la del pipeline)
        dA = hav(alat, alon, pa["centroid_lat"], pa["centroid_lon"])
        dB = hav(alat, alon, pb["centroid_lat"], pb["centroid_lon"])
        mismos.append(dict(dA=pa["centroid_dist_km"], dB=pb["centroid_dist_km"], dA2=dA, dB2=dB,
                           npA=pa["n_pixels"], npB=pb["n_pixels"], vA=pa["vrp_mw"], vB=pb["vrp_mw"],
                           bt_igual=btA == btB, lado="f0" if f["geo_crater"]["volcan_del_lado_del_frame0"] else "otro",
                           est=f["objetivo"]["estrato"][:2], z=f["geo_crater"]["cenit"], n_anom=len(btA)))
    print("n", len(mismos), "| n_pixels del cumulo igual en", sum(m["npA"] == m["npB"] for m in mismos),
          "| BT de los pixeles iguales en", sum(m["bt_igual"] for m in mismos),
          "| vrp cumulo igual en", sum(m["vA"] == m["vB"] for m in mismos))
    print("dist pipeline A med", med([m["dA"] for m in mismos]), "B med", med([m["dB"] for m in mismos]),
          "B mas cerca en", sum(m["dB"] < m["dA"] for m in mismos))
    print("dist recomputada A med", med([m["dA2"] for m in mismos]), "B med", med([m["dB2"] for m in mismos]))
    for lado in ("f0", "otro"):
        z = [m for m in mismos if m["lado"] == lado]
        print(f"  lado {lado}: n={len(z)} A med {med([m['dA'] for m in z])} B med {med([m['dB'] for m in z])} "
              f"B mas cerca en {sum(m['dB'] < m['dA'] for m in z)}")
    for e in ("S1", "S2", "S3"):
        z = [m for m in mismos if m["est"] == e]
        print(f"  {e}: n={len(z)} A med {med([m['dA'] for m in z])} B med {med([m['dB'] for m in z])}")
    print("  n_pixels del cumulo:", Counter(m["npA"] for m in mismos), " anomaly_pixels por record:",
          Counter(m["n_anom"] for m in mismos))
    # control: los Lascar que NO tienen los mismos pixeles
    otros = [f for f in las if not sorted(map(tuple, f["ij_A"])) == sorted(map(tuple, f["ij_B"]))]
    print("  Lascar S1-S3 total", len(las), "con pixeles distintos", len(otros))


if __name__ == "__main__":
    main()
