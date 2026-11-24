#!/usr/bin/env python
"""F2 S175: el lector de la sombra V375-E sella frontend/index.html del tag (sha256 260b4a...), no el de la base. ¿El
predicado del tablero publica distinto sobre los records de la sombra (via) y de produccion (K) con uno y otro?

Corre banco_paridad.correr_node de la BASE dos veces sobre los mismos casos (CAMPOS_JS de la base, que incluye
via_codigo_mirova): una con HTML = index.html de la base y otra con HTML = index.html del arbol del tag. No usa el
lector ni abre ninguna lectura; solo compara el predicado. P1: si los dos predicados fueran identicos en estos casos, la
diferencia es 0, y el control positivo (un record via frio de mas de 10 MW, inyectado) TIENE que diferir: en la base la
via esta exenta del filtro de cirro (S173 S1) y en el tag no. P2: n de casos impreso.
Uso: python predicado_tag_vs_base.py <arbol_base> <arbol_tag> <desde> <hasta> <salida.txt>
"""
import collections, json, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
BASE, TAG = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); INI, FIN, OUT = sys.argv[3], sys.argv[4], Path(sys.argv[5])
sys.path.insert(0, str(BASE / "scripts")); sys.path.insert(0, str(BASE)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
inner = bp.inner_desde_html()
casos, meta = [], []
for carpeta in ("sombra_codigo_mirova", "mirova_equivalent"):
    for vol in bp.VOLS:
        for r in json.load(open(BASE / "data" / carpeta / f"{vol}.json", encoding="utf-8"))["records"]:
            if not (INI <= r["datetime_utc"][:10] <= FIN) or bp.bucket(r.get("sensor")) != "VIIRS375":
                continue
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]]); meta.append((carpeta, vol, r["datetime_utc"], r["sensor"], r.get("t_max_k")))
# control positivo: un record de la via, summit, frio (t_max 260 K) y de 20 MW
ctrl = {"vrp_mw": 20.0, "distance_class": "summit", "t_max_k": 260.0, "sensor": "VIIRS_NOAA20", "via_codigo_mirova": True,
        "primary_cluster": {"vrp_mw": 20.0, "centroid_dist_km": 0.5, "n_pixels": 3}, "anomaly_pixels": []}
casos.append([ctrl, 5.0]); meta.append(("CONTROL", "-", "-", "-", 260.0))
html_base = bp.HTML
res_b = bp.correr_node(casos)
bp.HTML = TAG / "frontend" / "index.html"
res_t = bp.correr_node(casos)
bp.HTML = html_base
c = collections.Counter(); difs = []
for m, b, t in zip(meta, res_b, res_t):
    c[(m[0], "n")] += 1; c[(m[0], "pub_base")] += b[4]; c[(m[0], "pub_tag")] += t[4]
    if b != t:
        difs.append(f"{m} base {b} tag {t}")
L = [f"index base {bp.sha_git(html_base)} | index tag {bp.sha_git(TAG / 'frontend' / 'index.html')} | ventana {INI}..{FIN}",
     json.dumps({f"{k[0]}|{k[1]}": v for k, v in c.items()}), f"casos con salida distinta: {len(difs)}"] + difs
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
