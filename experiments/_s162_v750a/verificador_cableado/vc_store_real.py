# -*- coding: utf-8 -*-
"""Verificador VC: sobre records reales, (a) record marcado == record sin marca con las 3 compuertas desactivadas a mano
(salvo la clave de la marca); (b) control: marcado != sin marca con compuertas activas en muchos casos;
(c) con marca False/None/'sin_grilla'/1/'true' el almacén es el de siempre (`is True` estricto)."""
import copy, json, os, sys, tempfile, random
from pathlib import Path
RAIZ = Path(r"C:\vrp-trabajo\s162-via-mirova")
os.environ["GITHUB_SHA"] = "vc"; os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import pipeline.profile as PR, pipeline.store as S, run_pipeline as RP

def corre(vol, recs, **over):
    with tempfile.TemporaryDirectory() as t:
        S.DATA_DIR = Path(t)
        for r in recs:
            args = dict(volcano_lat=vol["lat"], volcano_lon=vol["lon"], max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=PR.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"), inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=RP.VOLCANIC_FEATURES.get(vol["name"]))
            args.update(over)
            S.append_record(vol["name"], r, **args)
        f = Path(t) / f"{vol['name']}.json"
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    out = d["records"] if isinstance(d, dict) else d
    for x in out:
        for k in ("processed_utc", "first_processed_utc"): x.pop(k, None)
    return out

rng = random.Random(7)
n = n_a = n_b_dist = n_c = 0
print("filtro por distancia en el perfil:", PR.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER)
for vol in RP.load_volcanoes():
    f = RAIZ / "data/mirova_equivalent" / f"{vol['name']}.json"
    if not f.exists(): continue
    d = json.loads(f.read_text(encoding="utf-8")); todos = d["records"] if isinstance(d, dict) else d
    recs = rng.sample(todos, min(40, len(todos)))
    base = corre(vol, copy.deepcopy(recs))                       # sin marca, compuertas activas = hoy
    marc = copy.deepcopy(recs)
    for r in marc: r["via_codigo_mirova"] = True
    m = corre(vol, marc)
    # (a)
    sin_marca_off = corre(vol, copy.deepcopy(recs), enable_pixel_level_distance_filter=False, max_hotspot_dist_km=1e9, max_cluster_pixels=None)
    m2 = copy.deepcopy(m)
    for x in m2: x.pop("via_codigo_mirova", None)
    n += len(base)
    n_a += json.dumps(m2, sort_keys=True) == json.dumps(sin_marca_off, sort_keys=True)
    n_b_dist += json.dumps(m2, sort_keys=True) != json.dumps(base, sort_keys=True)
    # (c) marcas que no son True
    ok = True
    for valor in (False, None, "sin_grilla", 1, "true", 0):
        mm = copy.deepcopy(recs)
        for r in mm: r["via_codigo_mirova"] = valor
        o = corre(vol, mm)
        for x in o: x.pop("via_codigo_mirova", None)
        ok &= json.dumps(o, sort_keys=True) == json.dumps(base, sort_keys=True)
    n_c += ok
    print(f"{vol['name']:22s} n={len(base):4d} (a) marcado==compuertas-off: {json.dumps(m2, sort_keys=True)==json.dumps(sin_marca_off, sort_keys=True)} | (c) marcas no-True == hoy: {ok}", flush=True)
print(f"TOTAL records {n}; volcanes (a) iguales: {n_a}; control (b) volcanes donde marcado != hoy: {n_b_dist}; volcanes (c) ok: {n_c}")
