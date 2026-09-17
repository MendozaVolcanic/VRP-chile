import sys, io, json, collections, math
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts")); sys.path.insert(0, str(ROOT/"experiments/_s135_ab_d1d2"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
import yaml
V = ("2026-06-01","2026-08-31")
D = ROOT/"experiments/_s143_preregistro/_dl_referencia"
filas = bp.cargar_referencia_unificada(D/"registro_vrp_consolidado.csv", D/"registro_vrp_ocr.csv")
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
recs = bp.cargar_nuestros(coords, inner, V)
bp.etiquetar(recs, por_vb, ns, nv)
# raw records to get centroid
vc = yaml.safe_load(open(ROOT/"volcanoes.yaml", encoding="utf-8"))
cm = {v["name"]:(v.get("mirova_center_lat"), v.get("mirova_center_lon")) for v in vc["volcanoes"]}
def hav(a,b,c,d):
    p=math.radians; R=6371.0088
    x=math.sin(p(c-a)/2)**2+math.cos(p(a))*math.cos(p(c))*math.sin(p(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
distref = collections.defaultdict(list)
for (vol,b), lst in por_vb.items():
    if b!="VIIRS375": continue
    for dt,f in lst:
        if bp.es_alerta(f["tipo"]) and f.get("dist_km") is not None:
            distref[(vol, f["fecha_utc"][:10])].append(float(f["dist_km"]))
VOLS8 = ["Isluga","Lascar","Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica","NevadosDeChillan","Chaiten"]
raw = {}
for vol in VOLS8:
    d = json.load(open(ROOT/"data/mirova_equivalent"/f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        raw[(vol, r["datetime_utc"], r.get("sensor"))] = r
# align recs to raw: recs lack datetime string; rebuild
out = {}
for vol in VOLS8:
    alert_n = {n for (v,b,n),dd in ns.items() if v==vol and b=="VIIRS375" and dd["alerta"]}
    dash, pcpub, dash_same, lejana = set(), set(), set(), set()
    for r in recs:
        if r["vol"]!=vol or r["b"]!="VIIRS375" or r["noche"] not in alert_n: continue
        key = None
        # find raw by datetime minute
        s = r["dt"].strftime("%Y-%m-%d %H:%M")
        cands = [v for k,v in raw.items() if k[0]==vol and k[1]==s and bp.bucket(k[2])=="VIIRS375"]
        if not cands: continue
        rr = cands[0]
        pc = rr.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0; cd = pc.get("centroid_dist_km"); dc = rr.get("distance_class")
        ev = (0 < vrp <= 50000 and cd is not None and cd <= inner[vol] and (not dc or dc=="summit"))
        same = True
        c = cm.get(vol)
        dm = distref.get((vol, r["noche"])) or []
        if pc.get("centroid_lat") is not None and c and c[0] is not None and dm:
            nuestra = hav(c[0],c[1],pc["centroid_lat"],pc["centroid_lon"])
            if min(abs(nuestra-x) for x in dm) > 0.55: same=False
        if ev: pcpub.add(r["noche"])
        if r["pub"]: dash.add(r["noche"])
        if ev and same: dash_same.add(r["noche"])
        if ev and not same: lejana.add(r["noche"])
    out[vol] = dict(alert=len(alert_n), evalab_pub=len(pcpub), dash_pub=len(dash), evalab_pub_mismo_objeto=len(dash_same), solo_lejana=len(lejana-dash_same), centro_mirova=cm.get(vol))
    print(vol, out[vol])
