# -*- coding: utf-8 -*-
"""Verificador S165: qué publicaría el tablero (predicado JS real, con node) para un record de la vía de 375
(fixture 1305, Nevados de Chillán, 20 alertados, 14,073 MW) en tres estados:
  (a) como lo deja el store de HEAD (sin f5_core_vrp_mw);
  (b) con f5_core_vrp_mw = 0.0 forzado (lo que el store del tag habría persistido si f5 diera 0);
  (c) como lo deja el store del TAG (pre-s165-via-375), cargado desde D:/.../verificador_tag.
Mide también lo que pipeline/f5_core.py devuelve para ese record."""
import importlib.util, io, json, sys, tempfile
from pathlib import Path
import numpy as np, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from pipeline import mirova_v750_codigo as MV, store, f5_core
import banco_paridad as B
V = {x["name"]: x for x in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
esp = {p["id"]: p for p in json.loads((RAIZ / "tests/datos_s165_v375/esperado.json").read_text(encoding="utf-8"))["pasadas"]}
def rec_via(pid):
    p = esp[pid]; v = V[p["volcan"]]
    g = MV.grilla_del_volcan(p["volcan"], paso_m=375.0, clave_roi="roi_v375")
    z = np.load(RAIZ / f"tests/datos_s165_v375/grilla_{pid}.npz"); mir, tir = z["mir"].astype(float), z["tir"].astype(float)
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    r = MV.procesar_grilla(mir, tir, g, MV.caja_v375(g, vlat, vlon), p["dayflag"], p["sunglint"], MV.posicion_de(g, vlat, vlon), v["inner_radius_km"], p["sensor"], familia="VIIRS375")
    r.update({"granule": "x", "product_version": "standard", "datetime_utc": p["hora_utc"]}); return r, v
def por_store(mod, r, v):
    r = json.loads(json.dumps(r)); tmp = Path(tempfile.mkdtemp()); viejo = mod.DATA_DIR; mod.DATA_DIR = tmp
    try: mod.append_record(v["name"], r, max_hotspot_dist_km=v.get("radius_km"), enable_pixel_level_distance_filter=True, max_cluster_pixels=v.get("max_cluster_pixels"), inner_radius_km=v.get("inner_radius_km"), overwrite=True)
    finally: mod.DATA_DIR = viejo
    return r
spec = importlib.util.spec_from_file_location("pipeline.store_tag", r"D:\vrp-trabajo\temporales\s165_v375_via\verificador_tag\pipeline\store.py")
store_tag = importlib.util.module_from_spec(spec); store_tag.__package__ = "pipeline"; spec.loader.exec_module(store_tag)
for pid in (1305, 1708, 1032):
    r0, v = rec_via(pid); inner = v["inner_radius_km"]
    print(f"\n== fixture {pid} {v['name']} npix={r0['n_anomalous_pixels']} vrp={r0['vrp_mw']} dc={r0['distance_class']} dist={r0['final_hotspot_dist_km']}")
    print("   f5_core.f5_core_vrp_mw(record de la vía) =", f5_core.f5_core_vrp_mw(json.loads(json.dumps(r0)), inner))
    a = por_store(store, r0, v); b = dict(a); b["f5_core_vrp_mw"] = 0.0; c = por_store(store_tag, r0, v)
    print("   (a) HEAD store: f5_core_vrp_mw =", a.get("f5_core_vrp_mw", "AUSENTE"), "| (c) TAG store: f5_core_vrp_mw =", c.get("f5_core_vrp_mw", "AUSENTE"))
    casos = [[{k: x.get(k) for k in B.CAMPOS_JS} | {"anomaly_pixels": x.get("anomaly_pixels") or []}, inner] for x in (a, b, c)]
    for nombre, res in zip(("a_HEAD", "b_f5=0", "c_TAG"), B.correr_node(casos)):
        print(f"   {nombre}: summit={res[0]} valid={res[1]} artefacto={res[2]} display_mw={res[3]} publica={res[4]}")
