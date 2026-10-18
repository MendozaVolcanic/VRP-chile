"""Verificador S153: posicion de lo que VIIRS 375 publica, C0 contra K.

Uso (desde la raiz del repo):
  python -I experiments/_s153_localizacion/verificador/verif_posicion.py PROD   [desde hasta]
  python -I experiments/_s153_localizacion/verificador/verif_posicion.py V1     <carpeta_union>

- "publica" = predicado del tablero ejecutado con node (banco_paridad.correr_node, que extrae
  mirovaEqVrp, isValidDetection, isThermalArtifact, isSummitDetection de frontend/index.html).
- noche = banco_paridad/auto_audit_weekly.es_pasada_diurna_descartada (misma regla del evaluador).
- distancias haversine desde vent_lat/vent_lon del frontend (VOLCANOES de index.html), y aparte
  desde volcanoes.yaml para comprobar que no cambia.
- cuatro posiciones: centroide del cumulo (pc), final_hotspot, marcador primario del mapa de
  detalle (port de index.html:2989-3028 con onlyPrimaryPixel=true, l. 904) y posicion del mapa
  general (honestPos, index.html:3669-3673).
"""
import sys, os, json, math, re, statistics as st, collections
from datetime import datetime, timezone
ROOT = os.getcwd()
DATADIR = os.environ.get("DATADIR", os.path.join("data", "mirova_equivalent"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import banco_paridad as bp  # noqa: E402
import yaml  # noqa: E402

VOLS = bp.VOLS
INNER = bp.inner_desde_html()
COORDS = bp._coords_por_volcan()
src = open(os.path.join(ROOT, "frontend", "index.html"), encoding="utf-8").read()
VENT_FE = {}
for m in re.finditer(r'\{ name:\s*"(\w+)".*?vent_lat:\s*(-?[\d.]+),\s*vent_lon:\s*(-?[\d.]+)', src):
    VENT_FE.setdefault(m.group(1), (float(m.group(2)), float(m.group(3))))
d = yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))
vs = d["volcanoes"] if isinstance(d, dict) else d
VENT_Y = {v["name"]: (v.get("vent_lat") or v["lat"], v.get("vent_lon") or v["lon"]) for v in vs}


def hav(a, b, c, e):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(e - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def pos_mapa_detalle(r, vent):
    """Port de index.html:2989-3028, primer elemento de `pixels` (onlyPrimaryPixel = true)."""
    hasFinal = r.get("final_hotspot_lat") is not None
    src_ = r.get("final_hotspot_source")
    ap = r.get("anomaly_pixels") or []
    if hasFinal and src_ in ("test1_roi", "test1_nti_peak"):
        return (r["final_hotspot_lat"], r["final_hotspot_lon"]), "final(" + src_ + ")"
    if ap:
        return (ap[0].get("lat"), ap[0].get("lon")), "anomaly_pixels[0]"
    if hasFinal:
        return (r["final_hotspot_lat"], r["final_hotspot_lon"]), "final"
    if r.get("hotspot_lat") is not None:
        return (r["hotspot_lat"], r["hotspot_lon"]), "hotspot"
    if r.get("vent_hotspot_lat") is not None:
        return (r["vent_hotspot_lat"], r["vent_hotspot_lon"]), "vent_hotspot"
    return vent, "vent"


def pos_mapa_general(r):
    honest = r.get("final_hotspot_source") in ("ctx_cluster", "test1_roi", "test1_nti_peak")
    lat = (r.get("final_hotspot_lat") if honest else None)
    lat = lat if lat is not None else (r.get("hotspot_lat") if r.get("hotspot_lat") is not None else (r.get("final_hotspot_lat") if r.get("final_hotspot_lat") is not None else r.get("vent_hotspot_lat")))
    lon = (r.get("final_hotspot_lon") if honest else None)
    lon = lon if lon is not None else (r.get("hotspot_lon") if r.get("hotspot_lon") is not None else (r.get("final_hotspot_lon") if r.get("final_hotspot_lon") is not None else r.get("vent_hotspot_lon")))
    return (lat, lon) if lat is not None and lon is not None else None


def cargar(path, vol, desde, hasta, solo_noche=True):
    out = []
    for r in json.load(open(path, encoding="utf-8"))["records"]:
        if bp.bucket(r.get("sensor")) != "VIIRS375":
            continue
        dt_s = r.get("datetime_utc") or ""
        if not (desde <= dt_s[:10] <= hasta):
            continue
        dt = datetime.strptime(dt_s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        lat, lon = COORDS[vol]
        if solo_noche and bp.es_pasada_diurna_descartada("VIIRS375", lat, lon, dt):
            continue
        out.append(r)
    casos = []
    for r in out:
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, INNER[vol]])
    pred = bp.correr_node(casos) if casos else []
    for r, p in zip(out, pred):
        r["_pub"] = p[4]
    return out


def medir(r, vol):
    vent = VENT_FE[vol]
    pc = r.get("primary_cluster") or {}
    o = {"key": (vol, r["sensor"], r["datetime_utc"]), "t1": bool(r.get("triggered_test1")),
         "src": r.get("final_hotspot_source")}
    o["pc"] = hav(vent[0], vent[1], pc["centroid_lat"], pc["centroid_lon"]) if pc.get("centroid_lat") is not None else None
    vy = VENT_Y[vol]
    o["pc_yaml"] = hav(vy[0], vy[1], pc["centroid_lat"], pc["centroid_lon"]) if pc.get("centroid_lat") is not None else None
    o["fin"] = hav(vent[0], vent[1], r["final_hotspot_lat"], r["final_hotspot_lon"]) if r.get("final_hotspot_lat") is not None else None
    (la, lo), o["det_src"] = pos_mapa_detalle(r, vent)
    o["det"] = hav(vent[0], vent[1], la, lo) if la is not None else None
    g = pos_mapa_general(r)
    o["gen"] = hav(vent[0], vent[1], g[0], g[1]) if g else None
    return o


def fmt(l):
    l = [x for x in l if x is not None]
    if not l:
        return "n   0"
    return f"n {len(l):3d} med {st.median(l):4.2f} <1km {sum(x < 1 for x in l)/len(l):4.0%}"


if __name__ == "__main__":
    modo = sys.argv[1]
    print("vent frontend vs yaml (km):", {v: round(hav(*VENT_FE[v], *VENT_Y[v]), 3) for v in VOLS})
    if modo == "PROD":
        desde, hasta = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else ("2026-08-29", "2026-12-31")
        print(f"== PRODUCCION data/mirova_equivalent, VIIRS375, noche, publicadas por node, {desde}..{hasta}")
        print(f"{'volcan':20s} {'pc centroide':26s} {'pc (yaml)':26s} {'marcador mapa detalle':26s} {'mapa general':26s} t1%  fuente marcador")
        for v in VOLS:
            recs = [r for r in cargar(os.path.join(DATADIR, v + ".json"), v, desde, hasta) if r["_pub"]]
            m = [medir(r, v) for r in recs]
            t1 = sum(x["t1"] for x in m) / len(m) if m else 0
            srcs = collections.Counter(x["det_src"] for x in m).most_common(3)
            print(f"{v:20s} {fmt([x['pc'] for x in m]):26s} {fmt([x['pc_yaml'] for x in m]):26s} {fmt([x['det'] for x in m]):26s} {fmt([x['gen'] for x in m]):26s} {t1:4.0%} {srcs}")
        # desglose por fuente con triggered_test1
        print("-- pc centroide por (triggered_test1, final_hotspot_source)")
        for v in VOLS:
            recs = [r for r in cargar(os.path.join(DATADIR, v + ".json"), v, desde, hasta) if r["_pub"]]
            g = collections.defaultdict(list)
            for r in recs:
                x = medir(r, v); g[(x["t1"], x["src"])].append(x["pc"])
            print(f"{v:20s}", {f"{'T1' if k[0] else 'noT1'}/{k[1]}": fmt(l) for k, l in sorted(g.items(), key=lambda kv: -len(kv[1]))})
    else:
        U = sys.argv[2]
        desde, hasta = "2026-08-29", "2026-10-08"
        print(f"== V1 {U}, VIIRS375, noche, publicadas por node, {desde}..{hasta}")
        hdr = f"{'volcan':20s} {'C0 pub (pc)':24s} {'K pub (pc)':24s} | {'pareadas C0 (pc)':24s} {'pareadas K (pc)':24s} | {'K mapa detalle':24s} {'C0 mapa detalle':24s} | nC0 nK ambos soloK"
        print(hdr)
        for v in VOLS:
            c0 = {r["datetime_utc"] + r["sensor"]: r for r in cargar(os.path.join(U, "_s146_ab_control", v + ".json"), v, desde, hasta)}
            k = {r["datetime_utc"] + r["sensor"]: r for r in cargar(os.path.join(U, "_s149_ab_sin_test1_b22_max", v + ".json"), v, desde, hasta)}
            pc0 = {kk: medir(r, v) for kk, r in c0.items() if r["_pub"]}
            pk = {kk: medir(r, v) for kk, r in k.items() if r["_pub"]}
            ambos = sorted(set(pc0) & set(pk))
            solok = set(pk) - set(pc0)
            print(f"{v:20s} {fmt([x['pc'] for x in pc0.values()]):24s} {fmt([x['pc'] for x in pk.values()]):24s} | "
                  f"{fmt([pc0[a]['pc'] for a in ambos]):24s} {fmt([pk[a]['pc'] for a in ambos]):24s} | "
                  f"{fmt([x['det'] for x in pk.values()]):24s} {fmt([x['det'] for x in pc0.values()]):24s} | {len(pc0)} {len(pk)} {len(ambos)} {len(solok)}")
