"""Con K, el marcador primario del mapa de detalle (pixelesDelMarcador, index.html: final_hotspot cuando la fuente es
ctx_cluster) coincide con el centroide del cumulo publicado (primary_cluster)? Y donde cae el pixel mas caliente.
Pregunta 1: si final_hotspot no fuera el centroide, la distancia saldria > 0; se cuentan los > 50 m.
Pregunta 2: si los campos faltaran, n_comparables seria 0.
Denominador: records K (>= 2026-09-18) de los 11 Tier A con distance_class summit, pc.vrp_mw > 0."""
import json, os, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); x=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"]
n=0; lejos=0; fuentes={}; pico_lejos=0; ej=[]
for v in TIER:
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        if r["datetime_utc"] < "2026-09-18" or r.get("distance_class") != "summit": continue
        pc = r.get("primary_cluster") or {}
        if not (pc.get("vrp_mw") or 0) > 0: continue
        fuentes[r.get("final_hotspot_source")] = fuentes.get(r.get("final_hotspot_source"),0)+1
        if r.get("final_hotspot_lat") is None or pc.get("centroid_lat") is None: continue
        n += 1
        d = hav(r["final_hotspot_lat"], r["final_hotspot_lon"], pc["centroid_lat"], pc["centroid_lon"])
        if d > 0.05: lejos += 1; ej.append((v, r["datetime_utc"], r["sensor"], r.get("final_hotspot_source"), round(d,2)))
        px = r.get("anomaly_pixels") or []
        if px:
            top = max(px, key=lambda p: p.get("vrp_mw") or 0)
            if hav(top["lat"], top["lon"], pc["centroid_lat"], pc["centroid_lon"]) > 0.75: pico_lejos += 1
print("fuentes:", fuentes)
print("comparables:", n, " final_hotspot a > 50 m del centroide:", lejos, " pixel de mas energia a > 0,75 km del centroide:", pico_lejos)
for e in ej[:10]: print("  ", e)
import collections
print("final_hotspot a > 50 m del centroide, por fuente:", collections.Counter(e[3] for e in ej))
