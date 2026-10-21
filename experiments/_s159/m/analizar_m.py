# S159 M: analiza la salida del probe (probe_m_parte*.jsonl) contra el criterio de PREREGISTRO_M.md.
# Uso: python analizar_m.py <dir_con_jsonl>  > analizar_m_salida.txt
# "Publicado" se decide con la funcion mirovaEqVrp de frontend/index.html ejecutada con node (A97), con
# innerKm = inner_radius_km del volcan (volcanoes.yaml), igual que el tablero.
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
RAIZ = AQUI.parents[2]
sys.stdout.reconfigure(encoding="utf-8")


def ne_km(lat0, lon0, lat, lon):
    return ((lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2)))


def rumbo(dn, de):
    return (math.degrees(math.atan2(de, dn)) + 360) % 360


def med(x):
    x = [v for v in x if v is not None]
    return round(st.median(x), 3) if x else None


def publicados_node(recs):
    """recs: lista de (record_minimo, innerKm). Devuelve mirovaEqVrp de cada uno, ejecutado con node."""
    src = open(RAIZ / "frontend" / "index.html", encoding="utf-8").read()
    m = re.search(r"function mirovaEqVrp\(r, innerKm = 10, includeFar = false\) \{.*?\n\}\n", src, re.S)
    js = m.group(0) + "\nconst d=require(process.argv[2]);\nconsole.log(JSON.stringify(d.map(([r,k])=>mirovaEqVrp(r,k,false))));\n"
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "f.js").write_text(js, encoding="utf-8")
        (Path(td) / "d.json").write_text(json.dumps(recs), encoding="utf-8")
        out = subprocess.run(["node", str(Path(td) / "f.js"), str(Path(td) / "d.json")], capture_output=True,
                             text=True, check=True).stdout
    return json.loads(out)


def minimo(r):
    if r is None:
        return None
    return {"primary_cluster": r.get("pc"), "distance_class": r.get("distance_class"), "vrp_mw": r.get("vrp_mw")}


def main():
    d = Path(sys.argv[1])
    filas = [json.loads(l) for p in sorted(d.rglob("probe_m_parte*.jsonl")) for l in open(p, encoding="utf-8")]
    vols = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    print("filas:", len(filas), "con error:", sum(1 for f in filas if "error" in f))
    for f in filas:
        if "error" in f:
            print("  ERROR", f["objetivo"]["volcan"], f["objetivo"]["granulo"], f["error"][:200])
    ok = [f for f in filas if "error" not in f]

    # ---- validez del instrumento
    print("\n== Validez del instrumento")
    print("nulo geometria = 0 en", sum(1 for f in ok if f["nulo_geo_crater_km"] == 0), "de", len(ok))
    print("A identico a A2 en", sum(1 for f in ok if f["nulo_A_A2_identico"]), "de", len(ok))
    s6 = [f for f in ok if f["objetivo"]["estrato"] == "S6_control_lascar_s151"]
    for f in s6:
        print("control S6", f["objetivo"]["granulo"], "hacia sensor", f["geo_crater"]["obs_hacia_sensor_km"],
              "(S151: 2.581)", "traza", f["geo_crater"]["obs_traza_km"], "(S151: -0.431)")
    print("versiones l1b:", Counter(f["version_l1b"] for f in ok), "geo:", Counter(f["version_geo"] for f in ok))
    print("pixeles MxD03 con relleno (en el granulo entero):", Counter(f["n_fill_mxd03"] > 0 for f in ok))

    # ---- publicado con node
    lote = []
    for f in ok:
        k = vols[f["objetivo"]["volcan"]].get("inner_radius_km") or 10
        o = f["objetivo"]
        guard = {"primary_cluster": ({"vrp_mw": o["pc_vrp_mw"], "centroid_dist_km": o["pc_centroid_dist_km"]}
                                     if o["pc_vrp_mw"] is not None else None),
                 "distance_class": o["distance_class"], "vrp_mw": None}
        lote += [[minimo(f["rec_A"]) or {}, k], [minimo(f["rec_B"]) or {}, k], [guard, k]]
    pub = publicados_node(lote)
    for n, f in enumerate(ok):
        f["pub_A"], f["pub_B"], f["pub_data"] = pub[3 * n], pub[3 * n + 1], pub[3 * n + 2]

    # ---- por record
    print("\n== Por record (A = produccion, B = MxD03)")
    cab = ("estrato volcan fecha cenit lado_regla lado_real linea/n extremo | crater: hacia_sensor traza total | "
           "pixel_caliente_A: d rumbo | clase data/A/B | centroide A->B d | dist_pc A/B (inner) | t_bg A/B | "
           "pc_vrp A/B | pub A/B | mismos_pixeles")
    print(cab)
    por = defaultdict(list)
    for f in ok:
        o, g = f["objetivo"], f["geo_crater"]
        a, b = f["rec_A"] or {}, f["rec_B"] or {}
        pa, pb = a.get("pc") or {}, b.get("pc") or {}
        n = f["n_lineas"]
        f["extremo"] = g["linea"] < 400 or g["linea"] > n - 1 - 400
        f["lado_real"] = "f0" if g["volcan_del_lado_del_frame0"] else "otro"
        f["total_crater"] = math.hypot(g["obs_barrido_km"], g["obs_traza_km"])
        dp = f["desp_pixeles_A"]
        hot = max(dp, key=lambda x: (x["bt_k"] or 0)) if dp else None
        f["hot_d"] = hot["d_km"] if hot else None
        f["hot_rumbo"] = hot["rumbo"] if hot else None
        cdesp = None
        if pa.get("centroid_lat") is not None and pb.get("centroid_lat") is not None:
            dn, de = ne_km(pa["centroid_lat"], pa["centroid_lon"], pb["centroid_lat"], pb["centroid_lon"])
            cdesp = math.hypot(dn, de)
        f["cent_d"] = cdesp
        f["clase_cambia"] = a.get("distance_class") != b.get("distance_class")
        f["pub_cambia"] = (f["pub_A"] > 0) != (f["pub_B"] > 0)
        f["mismos_pix"] = sorted(map(tuple, f["ij_A"])) == sorted(map(tuple, f["ij_B"]))
        f["d_tbg"] = (b["t_bg_k"] - a["t_bg_k"]) if (a.get("t_bg_k") is not None and b.get("t_bg_k") is not None) else None
        f["reproduce"] = (a.get("distance_class") == o["distance_class"]
                          and (pa.get("vrp_mw") if pa else None) == o["pc_vrp_mw"])
        inner = vols[o["volcan"]].get("inner_radius_km")
        print(f"{o['estrato'][:2]} {o['volcan'][:12]:12s} {o['datetime_utc']} {o['cenit']:5.1f} {o['lado']:4s} "
              f"{f['lado_real']:4s} {g['linea']:4d}/{n} {'E' if f['extremo'] else 'C'} | "
              f"{g['obs_hacia_sensor_km']:+.2f} {g['obs_traza_km']:+.2f} {f['total_crater']:.2f} | "
              f"{(f['hot_d'] if f['hot_d'] is not None else float('nan')):.2f} "
              f"{(f['hot_rumbo'] if f['hot_rumbo'] is not None else float('nan')):5.0f} | "
              f"{o['distance_class']}/{a.get('distance_class')}/{b.get('distance_class')} | "
              f"{(cdesp if cdesp is not None else float('nan')):.2f} | "
              f"{pa.get('centroid_dist_km')}/{pb.get('centroid_dist_km')} ({inner}) | "
              f"{a.get('t_bg_k')}/{b.get('t_bg_k')} | {pa.get('vrp_mw')}/{pb.get('vrp_mw')} | "
              f"{f['pub_A']:.3g}/{f['pub_B']:.3g} | {f['mismos_pix']}")
        por[o["estrato"]].append(f)

    # ---- resumen por estrato
    print("\n== Resumen por estrato (medianas; n = records sin error)")
    for e in sorted(por):
        l = por[e]
        print(f"{e}: n={len(l)}  lado real f0={sum(1 for f in l if f['lado_real']=='f0')}  "
              f"regla=real en {sum(1 for f in l if f['lado_real']==f['objetivo']['lado'])}")
        print(f"   crater: hacia sensor med {med([f['geo_crater']['obs_hacia_sensor_km'] for f in l])}  "
              f"traza med {med([f['geo_crater']['obs_traza_km'] for f in l])}  total med {med([f['total_crater'] for f in l])}")
        print(f"   metrica 1 (pixel caliente de A, mismo i,j): med {med([f['hot_d'] for f in l])} km  "
              f"n con pixel={sum(1 for f in l if f['hot_d'] is not None)}  >=1 km: {sum(1 for f in l if (f['hot_d'] or 0)>=1)}"
              f"  <0,5 km: {sum(1 for f in l if f['hot_d'] is not None and f['hot_d']<0.5)}")
        print(f"   rumbos pixel caliente: {Counter(int(((f['hot_rumbo']+45)%360)//90) for f in l if f['hot_rumbo'] is not None)} (0=N 1=E 2=S 3=O)")
        print(f"   centroide A->B med {med([f['cent_d'] for f in l])} km  n={sum(1 for f in l if f['cent_d'] is not None)}")
        print(f"   clase cambia: {sum(1 for f in l if f['clase_cambia'])}  "
              f"{Counter((f['rec_A'] or {}).get('distance_class') and str((f['rec_A'] or {}).get('distance_class'))+'->'+str((f['rec_B'] or {}).get('distance_class')) for f in l if f['clase_cambia'])}")
        print(f"   publicado cambia: {sum(1 for f in l if f['pub_cambia'])}  (A>0: {sum(1 for f in l if f['pub_A']>0)}, B>0: {sum(1 for f in l if f['pub_B']>0)})")
        print(f"   mismos pixeles detectados: {sum(1 for f in l if f['mismos_pix'])} de {len(l)}")
        dt = [f["d_tbg"] for f in l if f["d_tbg"] is not None]
        print(f"   delta t_bg B-A: med {med(dt)} K  |max| {round(max(map(abs, dt)),3) if dt else None}  n={len(dt)}")
        rv = [((f['rec_B'] or {}).get('pc') or {}).get('vrp_mw', 0) / ((f['rec_A'] or {}).get('pc') or {}).get('vrp_mw')
              for f in l if ((f['rec_A'] or {}).get('pc') or {}).get('vrp_mw') and (f['rec_B'] or {}).get('pc')]
        print(f"   pc_vrp B/A: med {med(rv)}  n={len(rv)}")
        print(f"   A reproduce data/: {sum(1 for f in l if f['reproduce'])} de {len(l)}")
        for zona in (True, False):
            z = [f for f in l if f["extremo"] == zona]
            if z:
                print(f"   {'extremo' if zona else 'centro '}: n={len(z)} traza med {med([f['geo_crater']['obs_traza_km'] for f in z])}"
                      f"  metrica1 med {med([f['hot_d'] for f in z])}  clase cambia {sum(1 for f in z if f['clase_cambia'])}")

    # ---- veredicto pre-registrado
    print("\n== Veredicto (PREREGISTRO_M.md)")
    valido = (all(f["nulo_geo_crater_km"] == 0 for f in ok) and all(f["nulo_A_A2_identico"] for f in ok)
              and s6 and all(abs(f["geo_crater"]["obs_hacia_sensor_km"] - 2.581) <= 0.05 for f in s6))
    m1_s1 = med([f["hot_d"] for f in por.get("S1_summit_f0_mas40", [])])
    m1_s2 = med([f["hot_d"] for f in por.get("S2_summit_otro_mas40", [])])
    m2 = sum(1 for e in ("S1_summit_f0_mas40", "S2_summit_otro_mas40", "S4_far_f0_mas40")
             for f in por.get(e, []) if f["clase_cambia"])
    print("instrumento valido:", bool(valido), "| metrica1 S1", m1_s1, "S2", m1_s2, "| metrica2", m2)
    if any("error" in f for f in filas):
        v = "INCOMPLETO"
    elif not valido:
        v = "INSTRUMENTO ROTO"
    elif (m1_s1 is not None and m1_s1 < 0.5 and m1_s2 is not None and m1_s2 < 0.5) or m2 == 0:
        v = "REFUTA"
    elif m1_s1 is not None and m1_s1 >= 1.0 and m2 >= 1:
        v = "CONFIRMA"
    else:
        v = "PARCIAL"
    print("VEREDICTO:", v)
    json.dump([{k: f.get(k) for k in ("objetivo", "lado_real", "extremo", "total_crater", "hot_d", "hot_rumbo",
                                      "cent_d", "clase_cambia", "pub_A", "pub_B", "pub_data", "pub_cambia",
                                      "mismos_pix", "d_tbg", "reproduce", "geo_crater")} for f in ok],
              open(AQUI / "analizar_m_tabla.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
