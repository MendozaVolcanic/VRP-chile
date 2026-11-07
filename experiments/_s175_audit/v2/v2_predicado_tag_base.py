#!/usr/bin/env python
"""V2: F2-206 por otro camino y otra ventana. Mismo predicado (banco_paridad.correr_node) con el index.html de la base
(752d348bc) y con el del tag del lector (sha256 260b4a19...), sobre TODOS los records de mirova_equivalent y de
sombra_codigo_mirova en 2026-03-01..2026-11-07, por sensor (V375, V750, MODIS), no solo V375 desde el 11-03.
P1: control positivo: un record de la via, summit, frio y de 20 MW tiene que dar publica en la base y no en el tag (S173 S1).
P2: se imprime n por carpeta y sensor; si todo diera 0 diferencias con n=0 se diria SIN DATO.
Uso: python v2_predicado_tag_base.py <arbol_base> <arbol_tag> <ini> <fin> <salida>"""
import collections, json, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
BASE, TAG = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); INI, FIN, OUT = sys.argv[3], sys.argv[4], Path(sys.argv[5])
sys.path.insert(0, str(BASE / "scripts")); sys.path.insert(0, str(BASE)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
inner = bp.inner_desde_html()
casos, meta = [], []
for carpeta in ("mirova_equivalent", "sombra_codigo_mirova"):
    for vol in bp.VOLS:
        for r in json.load(open(BASE / "data" / carpeta / f"{vol}.json", encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if not (INI <= r["datetime_utc"][:10] <= FIN) or b is None:
                continue
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]]); meta.append((carpeta, b, vol, r["datetime_utc"], bool(r.get("via_codigo_mirova"))))
ctrl = {"vrp_mw": 20.0, "distance_class": "summit", "t_max_k": 260.0, "sensor": "VIIRS_NOAA20", "via_codigo_mirova": True,
        "primary_cluster": {"vrp_mw": 20.0, "centroid_dist_km": 0.5, "n_pixels": 3}, "anomaly_pixels": []}
casos.append([ctrl, 5.0]); meta.append(("CONTROL", "VIIRS375", "-", "-", True))
H = bp.HTML
rb = bp.correr_node(casos); bp.HTML = TAG / "frontend" / "index.html"; rt = bp.correr_node(casos); bp.HTML = H
c = collections.Counter(); difs = []
for m, b, t in zip(meta, rb, rt):
    k = (m[0], m[1]); c[k + ("n",)] += 1; c[k + ("via",)] += m[4]; c[k + ("pub_base",)] += b[4]; c[k + ("pub_tag",)] += t[4]
    if b != t:
        c[k + ("dif",)] += 1; difs.append(f"{m} base {b} tag {t}")
L = [f"base index git {bp.sha_git(H)} | tag index git {bp.sha_git(TAG/'frontend'/'index.html')} | ventana {INI}..{FIN}"]
for k in sorted({x[:2] for x in c}):
    L.append(f"  {k}: " + ", ".join(f"{n} {c[k+(n,)]}" for n in ("n", "via", "pub_base", "pub_tag", "dif")))
L.append(f"casos distintos: {len(difs)}"); L += difs[:20]
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
