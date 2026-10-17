"""Tarea 1.22: cuántos records MODIS del corpus operacional podrían cambiar con el desempate
explícito, sin reprocesar (no hay L1B). Lee sólo lo que el record guarda.

Lo que se puede saber desde el record:
  A) corte activo: n_anomalous_pixels > 100. El top-100 cae dentro del conjunto de píxeles
     calientes y, con BT cuantizada, el borde suele ser un empate: el CONJUNTO guardado en
     anomaly_pixels puede cambiar (mapa del dashboard, vrp_mir_mw que store recalcula).
  B) empate visible en el primer puesto: anomaly_pixels[0].vrp_mw == anomaly_pixels[1].vrp_mw,
     sólo en records cuya lista guardada es la del camino eruption (no la del Test 1, que
     reemplaza la lista), y sólo entre píxeles que sobrevivieron al filtro de distancia.
  C) de B, los que tienen en el grupo empatado píxeles a ambos lados del inner_radius_km: ahí la
     etiqueta distance_class (MODIS la saca del final_hotspot) PODRÍA cambiar.
Lo que NO se puede saber: el empate con píxeles que el filtro de distancia ya sacó de la lista
(el caso Llaima 2026-10-06, cuyo compañero de empate quedó fuera de radius_km) y el empate en el
camino del Test 1, cuya lista de eruption no se guarda.
"""
import glob, json, os, sys
from collections import Counter
import yaml

ROOT = sys.argv[1]
vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
tot = Counter(); A = Counter(); B = Counter(); C = Counter(); C_pub = Counter()
fechas = []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
    nombre = os.path.basename(f)[:-5]
    v = vols.get(nombre, {})
    inner = v.get("inner_radius_km")
    for r in json.load(open(f, encoding="utf-8"))["records"]:
        if "MODIS" not in r["sensor"]:
            continue
        tot[nombre] += 1
        fechas.append(r["datetime_utc"])
        if (r.get("n_anomalous_pixels") or 0) > 100:
            A[nombre] += 1
        ap = r.get("anomaly_pixels") or []
        src = r.get("final_hotspot_source") or ""
        if len(ap) >= 2 and not src.startswith("test1") and ap[0]["vrp_mw"] == ap[1]["vrp_mw"]:
            B[nombre] += 1
            grupo = [p for p in ap if p["vrp_mw"] == ap[0]["vrp_mw"]]
            if inner is not None and any(p["dist_km"] <= inner for p in grupo) and any(p["dist_km"] > inner for p in grupo):
                C[nombre] += 1
                pc = r.get("primary_cluster") or {}
                pc_ok = (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inner
                C_pub[(r.get("distance_class"), src, "pc_en_inner" if pc_ok else "pc_fuera")] += 1
n = sum(tot.values())
print(f"records MODIS en data/mirova_equivalent: {n} ({min(fechas)} a {max(fechas)})")
print(f"A) corte top-100 activo (n_anomalous_pixels > 100): {sum(A.values())} ({100*sum(A.values())/n:.1f} %)", dict(A.most_common()))
print(f"B) empate visible en el primer puesto (lista eruption): {sum(B.values())} ({100*sum(B.values())/n:.1f} %)", dict(B.most_common()))
print(f"C) de B, grupo empatado a ambos lados del inner: {sum(C.values())}", dict(C.most_common()), "etiqueta hoy", dict(C_pub))
