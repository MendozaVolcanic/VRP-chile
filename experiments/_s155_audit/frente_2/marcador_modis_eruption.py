"""D-24 en MODIS con K: records publicados cuya fuente NO es ctx_cluster ('eruption'). pixelesDelMarcador (index.html)
dibuja entonces anomaly_pixels[0] (o final_hotspot si no hay pixeles). Distancia de ese marcador al centroide del
cumulo publicado, y la distancia que muestra la tabla (cascada: hotspot_dist_km primero, porque no es ancla honesta).
Pregunta 1: si el marcador coincidiera con el cumulo, todas las distancias serian ~0.
Pregunta 2: si no hubiera records 'eruption' publicados, la lista sale vacia y se dice.
Denominador: records >= 2026-09-18, 11 Tier A, distance_class summit, pc.vrp_mw > 0, pc dentro del inner (lo que el
grafico publica), fuente no honesta. Marca de regimen impresa (sin marca = C0 sin reprocesar)."""
import json, os, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INNER = {'Lascar':5,'Lastarria':3,'Tupungatito':7,'Villarrica':5,'PuyehueCordonCaulle':20,'Copahue':4,'NevadosDeChillan':5,'Llaima':5,'Chaiten':5,'PlanchonPeteroa':3,'Isluga':5}
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); x=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
filas = []
for v, inner in INNER.items():
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        if r["datetime_utc"] < "2026-09-18" or r.get("distance_class") != "summit": continue
        pc = r.get("primary_cluster") or {}
        if not (pc.get("vrp_mw") or 0) > 0 or (pc.get("centroid_dist_km") or 0) > inner: continue
        if r.get("final_hotspot_source") in ("ctx_cluster","test1_roi","test1_nti_peak"): continue
        px = r.get("anomaly_pixels") or []
        m = px[0] if px else {"lat": r.get("final_hotspot_lat"), "lon": r.get("final_hotspot_lon")}
        dm = hav(m["lat"], m["lon"], pc["centroid_lat"], pc["centroid_lon"]) if m.get("lat") is not None else None
        dtab = r.get("hotspot_dist_km") if r.get("hotspot_dist_km") is not None else r.get("final_hotspot_dist_km")
        filas.append((v, r["datetime_utc"], r["sensor"], r.get("final_hotspot_source"), "K" if (r.get("regimen") or {}).get("codigo_sha") else "SIN_MARCA",
                      round(pc["vrp_mw"],3), round(pc["centroid_dist_km"],2), None if dm is None else round(dm,2), dtab, len(px)))
print("publicados no-ctx_cluster en ventana K:", len(filas), " con marcador a > 1 km del cumulo:", sum(1 for f in filas if f[7] is not None and f[7] > 1))
print("(vol, dt, sensor, fuente, regimen, pc_vrp, pc_dist_crater, marcador_a_centroide_km, dist_tabla_km, n_px)")
for f in sorted(filas, key=lambda f: -(f[7] or 0)): print("  ", f)
