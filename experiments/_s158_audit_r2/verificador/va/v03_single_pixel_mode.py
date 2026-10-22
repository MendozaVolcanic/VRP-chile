# -*- coding: utf-8 -*-
"""VA, hallazgo 3: cuanto cambia la magnitud publicada por single_pixel_mode (max por pixel en vez de suma).

Camino propio: los tres sensores, sobre data/mirova_equivalent directo. Para aislar el cumulo sin reconstruirlo,
uso solo records donde el cumulo ES toda la escena (n_anomalous_pixels == pc.n_pixels <= 100), asi la suma de
anomaly_pixels.vrp_mw es la suma del cumulo (antes del redondeo a 4 decimales).
Pregunta 1: si single_pixel_mode no actuara, max(anomaly_pixels) no coincidiria con pc.vrp_mw y la razon suma/pc
seria 1; el control es el estrato n_pixels == 1 (razon tiene que dar 1).
Pregunta 2: si el lector estuviera muerto, n = 0 en todos los estratos.
Denominador y ventana impresos.
"""
import glob, json, statistics, sys
from collections import Counter, defaultdict
import yaml

sys.stdout.reconfigure(encoding="utf-8")
inner = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}


def bucket(s):
    return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")


est = defaultdict(list)
cnt = Counter()
fechas = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    vol = d["volcano"]
    for r in d["records"]:
        pc = r.get("primary_cluster")
        if not pc or pc.get("centroid_dist_km") is None or inner.get(vol) is None or pc["centroid_dist_km"] > inner[vol]:
            continue
        if (pc.get("vrp_mw") or 0) <= 0:
            continue
        b = bucket(r["sensor"])
        spm = bool(pc.get("single_pixel_mode"))
        cnt[(b, "publicado cumbre")] += 1
        if spm and pc["n_pixels"] >= 2:
            cnt[(b, "spm con >=2 px")] += 1
        if r.get("n_anomalous_pixels") != pc["n_pixels"] or not r.get("anomaly_pixels"):
            continue
        aps = r["anomaly_pixels"]
        s = sum(a["vrp_mw"] for a in aps)
        mx = max(a["vrp_mw"] for a in aps)
        k = (b, "n=1" if pc["n_pixels"] == 1 else ("2-3 spm" if spm else "2+ sin spm"))
        est[k].append((s / pc["vrp_mw"], abs(mx - pc["vrp_mw"]) <= 0.0015, r["datetime_utc"]))
        fechas.append(r["datetime_utc"])
print("ventana obs:", min(fechas), "a", max(fechas))
for k in sorted(cnt):
    print("conteo", k, cnt[k])
for k in sorted(est):
    v = est[k]
    rz = sorted(x[0] for x in v)
    q = lambda p: rz[min(len(rz) - 1, int(p * len(rz)))]
    print("%-28s n=%4d  suma/pc: p25=%.3f med=%.3f p75=%.3f max=%.3f ; pc==max(pixel): %d de %d" % (
        k, len(v), q(.25), statistics.median(rz), q(.75), rz[-1], sum(x[1] for x in v), len(v)))
