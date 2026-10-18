# -*- coding: utf-8 -*-
"""A61 de P4, paso 1: por cada pasada movida (lista exacta del verificador, a4_p4_mag.json), posicion del cumulo
de C0 y de K (lat, lon, distancia y rumbo desde vent), proteccion A, filas de MIROVA pareadas (+-120 s) con su
Distancia_km, y la distancia de cada cumulo al centro de grilla de MIROVA (mirova_center), que es desde donde
MIROVA mide. Solo lee. Salida: s1_tabla.json y s1_tabla.txt."""
import json, sys, math
from datetime import datetime, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11"))
import evaluar_fk as E
import yaml
OUT = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\a61_p4")
VER = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\verif_fk_v2")
REP = VER / "rep"
mov_all = json.load(open(VER / "a4_p4_mag.json", encoding="utf-8"))
Y = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}


def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def rumbo(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    dl = math.radians(d - b)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def card(b):
    return ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][int((b + 22.5) // 45) % 8]


filas_out = []
for w in ("V1", "V2"):
    cfg = dict(E.VENTANAS[w]); tmp = REP / ("tmp_" + w.lower())
    T = json.load(open(tmp / "t_C0_K.json", encoding="utf-8"))["pasadas"]
    # referencia COMPLETA (con OCR) para la distancia de MIROVA; la proteccion se toma con la del evaluador
    ref = E.archivos_ref(cfg, tmp)
    keys = [m["k"] for m in mov_all[w]["mov"]]
    prot = E.proteccion(set(keys), ref, cfg["desde"], cfg["hasta"])
    cons = cfg["ref"] / "registro_vrp_consolidado.csv"; ocr = cfg["ref"] / "registro_vrp_ocr.csv"
    capas = ref[2]
    kw = {"historico_path": capas["historico"], "respaldo_path": capas["respaldo"]} if capas else {}
    filas = E.ev.cargar_referencia_unificada(Path(cons), Path(ocr), **kw)
    coords = E.bp._coords_por_volcan()
    por_vb, _, _, _ = E.bp.indexar_referencia(filas, coords, (cfg["desde"], cfg["hasta"]))
    for m in mov_all[w]["mov"]:
        k = m["k"]; vol, s, t = k.split("|")
        a, b = T[k]["control"], T[k]["brazo"]
        y = Y[vol]; vl, vo = y["vent_lat"], y["vent_lon"]; ml, mo = y["mirova_center_lat"], y["mirova_center_lon"]
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        ff = E.bp.parear(por_vb.get((vol, s), []), dt)
        mir = [{"tipo": f.get("tipo"), "source": f.get("source"), "vrp": f.get("vrp_mw", f.get("vrp")),
                "dist": f.get("dist_km", f.get("distancia_km")), "dt": str(f.get("dt", f.get("datetime_utc", ""))),
                "clase": f.get("clase", f.get("nivel"))} for f in ff]
        r = {"w": w, "k": k, "vol": vol, "s": s, "t": t, "prot_A": prot[k]["A"], "prot_B": prot[k]["B"],
             "solo_ocr": prot[k]["alerta_solo_ocr"], "decide": m["decide"], "mov_km": m["mov_km"],
             "vrp_ref": a["vrp_ref"], "plataforma": a.get("plataforma"), "filas_mirova": mir, "raw_keys": sorted(ff[0].keys()) if ff else []}
        for lado, x in (("C0", a), ("K", b)):
            la, lo = x["pc_lat"], x["pc_lon"]
            r[lado] = {"lat": la, "lon": lo, "disp": x["disp"], "d_vent": round(hav(vl, vo, la, lo), 3),
                       "rumbo": round(rumbo(vl, vo, la, lo)), "card": card(rumbo(vl, vo, la, lo)),
                       "d_mcenter": round(hav(ml, mo, la, lo), 3)}
        filas_out.append(r)
json.dump(filas_out, open(OUT / "s1_tabla.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("n =", len(filas_out))
print(filas_out[0]["raw_keys"])
for r in filas_out:
    md = [(f["tipo"], f["source"], f["vrp"], f["dist"]) for f in r["filas_mirova"]]
    print("%s %-38s A=%d mov=%.2f | C0 %.2fkm %s mc=%.2f | K %.2fkm %s mc=%.2f | MIROVA %s" % (
        r["w"], r["k"], r["prot_A"], r["mov_km"], r["C0"]["d_vent"], r["C0"]["card"], r["C0"]["d_mcenter"],
        r["K"]["d_vent"], r["K"]["card"], r["K"]["d_mcenter"], md))
