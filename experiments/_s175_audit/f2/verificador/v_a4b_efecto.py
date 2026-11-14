# -*- coding: utf-8 -*-
"""A4 (sensibilidad): cuantas publicaciones V375 nocturnas cambian si el predicado ve _mirova_confirmed como en el
navegador. Arma los casos igual que banco_paridad.cargar_nuestros (mismos filtros y campos) y corre bp.correr_node
dos veces: con la marca en false (la vara) y con la marca de enrichWithMirovaConfirmation (ejecutada con node).
Control positivo: un record sintetico cirrus (t_max 260 K, 20 MW en el cumulo summit) debe pasar de 0 a 1.
Uso: python v_a4b_efecto.py <arbol_base> <tmpdir>"""
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(sys.argv[1]).resolve()
TMP = Path(sys.argv[2])
sys.path.insert(0, str(A))
sys.path.insert(0, str(A / "scripts"))
import banco_paridad as bp  # noqa: E402
sys.argv = [sys.argv[0], str(A), str(TMP / "dummy.json"), str(TMP)]
VENT = ("2026-03-01", "2026-11-07")
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()

# confirmacion con node (mismo JS que v_a4.py)
spec = Path(__file__).with_name("v_a4.py").read_text(encoding="utf-8")
JS = spec.split('JS = r"""', 1)[1].split('"""', 1)[0]
import subprocess  # noqa: E402

def node_conf(job):
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "a4b.js").write_text(JS, encoding="utf-8")
    (TMP / "a4b_job.json").write_text(json.dumps(job), encoding="utf-8")
    o = subprocess.run(["node", "--max-old-space-size=4096", str(TMP / "a4b.js"), str(A / "frontend" / "index.html"),
                        str(TMP / "a4b_job.json")], capture_output=True, text=True, timeout=900)
    if o.returncode != 0:
        raise RuntimeError(o.stderr[-2000:])
    return json.loads(o.stdout)

casos, meta = [], []
for vol in bp.VOLS:
    recs = json.load(open(A / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    mir = json.load(open(A / "data" / "mirova" / f"{vol}.json", encoding="utf-8")).get("records") or []
    conf = node_conf([[vol, [{"sensor": r.get("sensor"), "datetime_utc": r.get("datetime_utc")} for r in recs], mir]])[vol]
    for r, (_, _, k) in zip(recs, conf):
        b = bp.bucket(r.get("sensor"))
        if b != "VIIRS375" or not (VENT[0] <= r.get("datetime_utc", "")[:10] <= VENT[1]):
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if bp.es_pasada_diurna_descartada(b, *coords[vol], dt):
            continue
        slim = {kk: r.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{kk: p.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner[vol]])
        meta.append((vol, r["sensor"], r["datetime_utc"], k))
p0 = bp.correr_node(casos)
casos1 = [[dict(s, _mirova_confirmed=bool(m[3])), i] for (s, i), m in zip(casos, meta)]
p1 = bp.correr_node(casos1)
print("casos V375 nocturnos:", len(casos), "| confirmados:", sum(m[3] for m in meta))
print("publicados sin marca (vara):", sum(x[4] for x in p0), "| con marca del navegador:", sum(x[4] for x in p1))
dif = [(m, a[4], b[4]) for m, a, b in zip(meta, p0, p1) if a[4] != b[4]]
print("cambian:", len(dif), dif[:10])
print("artefacto termico sin marca:", sum(x[2] for x in p0), "| con marca:", sum(x[2] for x in p1))
sint = {"vrp_mw": 20.0, "distance_class": "summit", "t_max_k": 260.0, "sensor": "VIIRS_SNPP", "f5_core_vrp_mw": 20.0,
        "primary_cluster": {"vrp_mw": 20.0, "centroid_dist_km": 0.5, "n_pixels": 3}}
c = bp.correr_node([[sint, 5.0], [dict(sint, _mirova_confirmed=True), 5.0]])
print("control cirrus sintetico [art, pub] sin marca:", [c[0][2], c[0][4]], "| con marca:", [c[1][2], c[1][4]])
