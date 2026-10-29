# Contexto de cada una de las 13: geometria solar, pixeles, nocturnas +-72 h (brazo y produccion), filas de MIROVA, control.
import sys, io, json, glob, math, csv, unicodedata
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path("D:/vrp-trabajo/temporales/s167_diurno_lectura"); OUT = Path("D:/vrp-trabajo/temporales/s167_diurnas_13")
sys.path.insert(0, str(BASE/"codigo/experiments/_s163_diurno_k")); sys.path.insert(0, str(BASE/"codigo/scripts"))
import os; os.chdir(BASE/"codigo")
import evaluar_diurno_k as e, banco_paridad as bp, yaml
cfg = {v["name"]: v for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
inner = bp.inner_desde_html()
trece = json.loads((OUT/"trece_records.json").read_text(encoding="utf-8"))
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c); dp = p2-p1; dl = math.radians(d-b)
    return 2*R*math.asin(math.sqrt(math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
def rumbo(a, b, c, d):
    y = math.sin(math.radians(d-b))*math.cos(math.radians(c)); x = math.cos(math.radians(a))*math.sin(math.radians(c))-math.sin(math.radians(a))*math.cos(math.radians(c))*math.cos(math.radians(d-b))
    return (math.degrees(math.atan2(y, x))+360) % 360
def slim(r):
    s = {kk: r.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
    if r.get("f5_core_vrp_mw") is None:
        s["anomaly_pixels"] = [{kk: px.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")} for px in (r.get("anomaly_pixels") or [])]
    return s
# produccion: records +-72 h de cada objetivo, todos los sensores, con predicado del tablero
prod_cache = {}
def prod(vol):
    if vol not in prod_cache:
        prod_cache[vol] = json.loads((OUT/("prod/data/mirova_equivalent/%s.json" % vol)).read_text(encoding="utf-8"))["records"]
    return prod_cache[vol]
def norm(s): return "".join(c for c in unicodedata.normalize("NFD", s) if c.isalnum()).lower()
ALIAS = {norm(k): k for k in cfg}
ALIAS.update({"puyehuecordoncaulle": "PuyehueCordonCaulle", "nevadosdechillan": "NevadosDeChillan", "planchonpeteroa": "PlanchonPeteroa"})
ref_rows = []
for fn, canal in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR"), ("consolidado_filas_perdidas.csv", "PERD"), ("respaldo_20260408.csv", "RESP")):
    with open(BASE/"ref"/fn, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            v = ALIAS.get(norm(row["Volcan"]))
            try: t = datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M")
            except Exception: continue
            ref_rows.append((v, t, canal, row))
ctrl = json.loads((OUT/"control_mismo_granulo.json").read_text(encoding="utf-8"))
ctrl_b = json.loads((OUT/"brazo_idx.json").read_text(encoding="utf-8"))
nocb = json.loads((OUT/"nocturnas_brazos.json").read_text(encoding="utf-8"))
res = []
for h in trece:
    vol = h["_vol"]; c = cfg[vol]; vlat, vlon = c["vent_lat"], c["vent_lon"]
    dt = datetime.strptime(h["datetime_utc"], "%Y-%m-%d %H:%M"); b = bp.bucket(h["sensor"])
    r4 = {"sz": h["_sz"], "sa": h["_sa"], "soz": h["_soz"], "soa": h["_soa"], "es_dia": True}
    glint = e.angulo_reflejo(r4)
    pc = h.get("primary_cluster") or {}
    px = [(round(p["lat"], 4), round(p["lon"], 4), round(hav(vlat, vlon, p["lat"], p["lon"]), 2), round(rumbo(vlat, vlon, p["lat"], p["lon"])), p.get("bt_k"), p.get("vrp_mw"), p.get("nti"), p.get("path") or p.get("detection_path"))
          for p in (h.get("anomaly_pixels") or [])]
    pcd = None
    if pc.get("centroid_lat") is not None:
        pcd = (round(hav(vlat, vlon, pc["centroid_lat"], pc["centroid_lon"]), 2), round(rumbo(vlat, vlon, pc["centroid_lat"], pc["centroid_lon"])))
    # nocturnas del brazo (dentro de ventanas)
    nb = [x for x in nocb.get("_s154_ab_diurno_k_on", []) if x["vol"] == vol and abs(datetime.strptime(x["dt"], "%Y-%m-%d %H:%M")-dt) <= timedelta(hours=72)]
    # produccion +-72 h (noche, todos los sensores)
    cand = []
    for r in prod(vol):
        try: t = datetime.strptime(r.get("datetime_utc", ""), "%Y-%m-%d %H:%M")
        except ValueError: continue
        if abs(t-dt) <= timedelta(hours=72): cand.append((t, r))
    pred = bp.correr_node([[slim(r), inner[vol]] for _, r in cand]) if cand else []
    pn = []
    for (t, r), p in zip(cand, pred):
        dia = e.es_dia_vol(vol, t)
        pn.append({"t": t.strftime("%Y-%m-%d %H:%M"), "s": r.get("sensor"), "dia": dia, "pub": bool(p[4]), "disp": p[3],
                   "dist": r.get("final_hotspot_dist_km"), "cls": r.get("distance_class"), "nti": r.get("nti_max"), "tbg": r.get("t_bg_k"),
                   "rumbo": (round(rumbo(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])) if r.get("final_hotspot_lat") is not None else None)})
    pubn = [x for x in pn if x["pub"] and not x["dia"]]
    # MIROVA +-72 h
    mr = [(t, canal, row) for v, t, canal, row in ref_rows if v == vol and abs(t-dt) <= timedelta(hours=72)]
    mal = [(t, canal, row) for t, canal, row in mr if "ALERTA" in row["Tipo_Registro"]]
    mdia = [(t, canal, row) for t, canal, row in mr if t.date() == dt.date()]
    kc = "|".join((vol, b, h["datetime_utc"]))
    res.append({"vol": vol, "sensor": h["sensor"], "b": b, "t": h["datetime_utc"], "raiz": h["_raiz"], "disp": round(h["_disp"], 3),
                "vrp_mw": h.get("vrp_mw"), "pc_vrp": pc.get("vrp_mw"), "f5": h.get("f5_core_vrp_mw"), "dist": h.get("final_hotspot_dist_km"),
                "cls": h.get("distance_class"), "inner": c.get("inner_radius_km"), "src": h.get("final_hotspot_source"), "npx": h.get("n_anomalous_pixels"),
                "tbg": h.get("t_bg_k"), "tmax": h.get("t_max_k"), "nti": h.get("nti_max"), "elev_sol": round(90-h["_soz"], 1), "sz": h["_sz"],
                "glint": None if glint is None else round(glint, 1), "pc_centroide_dist_rumbo": pcd, "pc_npx": pc.get("n_pixels"),
                "pixeles": px, "diag_dia": h.get("diag_umbrales_diurnos"), "geo_class": h.get("geo_class"),
                "cloud": {k: h.get(k) for k in h if "cloud" in k.lower() or "nube" in k.lower()},
                "control_mismo_granulo": ctrl.get(kc),
                "brazo_noct_72h": {"n": len([x for x in nb if True]), "pub": len([x for x in nb if x["pub"]]), "max_disp": max([x["disp"] or 0 for x in nb if x["pub"]], default=0)},
                "prod_noct_72h": {"n": len([x for x in pn if not x["dia"]]), "pub": len(pubn), "max_disp": max([x["disp"] or 0 for x in pubn], default=0),
                                   "pub_lista": [(x["t"], x["s"], round(x["disp"] or 0, 3), x["dist"], x["rumbo"], x["cls"]) for x in pubn]},
                "mirova_alertas_72h": [(t.strftime("%Y-%m-%d %H:%M"), canal, row["Sensor"], row["VRP_MW"], row["Distancia_km"], row["Tipo_Registro"], row["Clasificacion Mirova"]) for t, canal, row in sorted(mal, key=lambda z: z[0])],
                "brazo_mismo_paso": [(k2, v2) for k2, v2 in ctrl_b.items() if k2.split("|")[0] == vol and abs((datetime.strptime(k2.split("|")[2], "%Y-%m-%d %H:%M")-dt).total_seconds()) <= 600],
                "mirova_mismo_dia": [(t.strftime("%H:%M"), canal, row["Sensor"], row["VRP_MW"], row["Distancia_km"], row["Tipo_Registro"]) for t, canal, row in sorted(mdia, key=lambda z: z[0])]})
(OUT/"contexto_13.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
for x in res:
    print("=" * 100)
    for k, v in x.items():
        if k in ("prod_noct_72h",):
            print(" ", k, {kk: vv for kk, vv in v.items() if kk != "pub_lista"}); [print("     ", y) for y in v["pub_lista"][:25]]
        elif k in ("mirova_alertas_72h", "mirova_mismo_dia", "pixeles"):
            print(" ", k, len(v)); [print("     ", y) for y in v[:30]]
        else: print(" ", k, v)
