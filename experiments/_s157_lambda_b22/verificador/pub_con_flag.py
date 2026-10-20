# Verificador S157: ¿se abre o se cierra alguna publicación MODIS con K si la magnitud sube por F?
# Predicado del tablero ejecutado con node (banco_paridad.correr_node, A97). Escala pc.vrp_mw, vrp_mw y
# anomaly_pixels[].vrp_mw por un F uniforme (cota: 1,05 y 1,0753) y además simula el modo de un píxel.
import json, sys, os, copy
sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22"); sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp
from auto_audit_weekly import detector_de_record, leer_frontera_k
fr = leer_frontera_k(); inner = bp.inner_desde_html()
base, keys = [], []
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        if "MODIS" not in (r.get("sensor") or "") or detector_de_record(r, fr) != "K": continue
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
        base.append([slim, inner[vol]]); keys.append((vol, r["datetime_utc"]))
def escalar(F):
    out = []
    for slim, inn in base:
        s = copy.deepcopy(slim)
        pc = s.get("primary_cluster")
        if pc and pc.get("vrp_mw") and not pc.get("d9_capped"):
            v = pc["vrp_mw"] * F
            # modo de un píxel: si la suma cruza 5 MW deja el modo (aquí, cota: el valor escalado)
            pc["vrp_mw"] = round(v, 3)
        if s.get("vrp_mw"): s["vrp_mw"] = s["vrp_mw"] * F
        for p in s["anomaly_pixels"]:
            if p.get("vrp_mw"): p["vrp_mw"] = p["vrp_mw"] * F
        out.append([s, inn])
    return out
p0 = bp.correr_node(base)
print("records MODIS K:", len(base), "publicados hoy:", sum(p[4] for p in p0), "artefacto hoy:", sum(p[2] for p in p0))
for F in (1.05, 1.0753, 1.20, 100.0):
    p1 = bp.correr_node(escalar(F))
    cambios = [(keys[i], p0[i][4], p1[i][4], p0[i][2], p1[i][2]) for i in range(len(base)) if p0[i][4] != p1[i][4] or p0[i][2] != p1[i][2]]
    print(f"F={F}: publicados {sum(p[4] for p in p1)}, artefacto {sum(p[2] for p in p1)}, cambios {len(cambios)}", cambios[:5])
