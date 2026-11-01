# -*- coding: utf-8 -*-
"""Verificador VC: escenarios propios del cableado, con el flag apagado y encendido. Sólo lee el repo; no escribe en él."""
import copy, json, os, sys, tempfile
from pathlib import Path
from unittest.mock import patch
RAIZ = Path(r"C:\vrp-trabajo\s162-via-mirova")
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np, yaml

# ---------------- E1: import sin efectos con el flag apagado (proceso fresco)
import pipeline.profile as P
print("E1 flag en perfil mirova_equivalent:", P.ENABLE_V750_CODIGO_MIROVA)
import pipeline.process_viirs_mod as PVM, pipeline.store as ST
print("E1 modulo de la via cargado tras importar PVM y store:", "pipeline.mirova_v750_codigo" in sys.modules, "(debe ser False)")

vols = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
class K(Exception): pass
class Via(Exception): pass

def intento(v, flag):
    """Devuelve 'K' si llegó al lector de K, 'VIA' si llegó al lector de la vía."""
    from pipeline import mirova_v750_codigo as MV
    with patch.object(PVM, "ENABLE_V750_CODIGO_MIROVA", flag), \
         patch.object(PVM, "read_viirs_mod_l1b", side_effect=K()), \
         patch.object(MV, "leer_radiancia_l1b", side_effect=Via()):
        try:
            PVM.calculate_vrp(Path("VJ102MOD.A2026290.0554.021.nc"), Path("g.nc"), v["lat"], v["lon"], v["radius_km"],
                              vent_lat=v.get("vent_lat"), vent_lon=v.get("vent_lon"))
        except K: return "K"
        except Via: return "VIA"
    return "otro"

import collections
c_off = collections.Counter(intento(v, False) for v in vols)
res_on = {v["name"]: intento(v, True) for v in vols}
from pipeline import mirova_v750_codigo as MV
con_grilla = set(MV._referencias())
print("E2 flag apagado, 45 volcanes ->", dict(c_off))
print("E2 flag encendido: volcanes que van a la via:", sorted(n for n, r in res_on.items() if r == "VIA"))
print("E2 coincide con grillas_mirova.yaml:", {n for n, r in res_on.items() if r == "VIA"} == con_grilla, "| resto a K:", all(r == "K" for n, r in res_on.items() if n not in con_grilla))
print("E2 nombres en grillas ausentes de volcanoes.yaml:", con_grilla - {v["name"] for v in vols})
# duplicados de coordenadas
d = collections.Counter((round(v["lat"], 6), round(v["lon"], 6)) for v in vols)
print("E2 coordenadas duplicadas en volcanoes.yaml:", [k for k, n in d.items() if n > 1])
# tipos de coordenadas
for lat, lon in [(np.float32(-38.69255), np.float32(-71.72974)), ("-38.69255", "-71.72974"), (-38, -71), (float("nan"), float("nan"))]:
    try: print("E8 tipos", type(lat).__name__, "->", MV.volcan_por_coordenadas(lat, lon))
    except Exception as e: print("E8 tipos", type(lat).__name__, "-> EXCEPCION", repr(e))
ll = [v for v in vols if v["name"] == "Llaima"][0]
print("E8 Llaima yaml exacto ->", MV.volcan_por_coordenadas(ll["lat"], ll["lon"]), "| np.float32 de Llaima (yaml) ->", MV.volcan_por_coordenadas(np.float32(ll["lat"]), np.float32(ll["lon"])))

# ---------------- E3: record K con el flag encendido y volcán sin grilla (escena sintética del arnés)
sys.path.insert(0, str(RAIZ / "tests"))
import arnes_sintetico_s142 as AR
def corre(flag):
    with patch.object(PVM, "ENABLE_V750_CODIGO_MIROVA", flag):
        return AR.correr_v750("nevado")
r_off, r_on = corre(False), corre(True)
dif = {k for k in set(r_off) | set(r_on) if json.dumps(r_off.get(k), default=str, sort_keys=True) != json.dumps(r_on.get(k), default=str, sort_keys=True)}
print("E3 escena V750 (coords no son de ningun yaml): record no None:", r_off is not None, "| claves distintas entre flag off y on:", dif, "| marca:", r_on.get("via_codigo_mirova"), "| marca con flag off:", "via_codigo_mirova" in r_off)

# ---------------- E4: vía de punta a punta sobre escena sintética en Llaima (coordenadas del yaml)
n = 121
lat0, lon0 = ll["lat"], ll["lon"]
d_km = (np.arange(n) - n // 2) * 0.75
y, x = np.meshgrid(d_km, d_km, indexing="ij")
lat = lat0 + y / 111.0; lon = lon0 + x / (111.0 * np.cos(np.radians(lat0)))
rng = np.random.default_rng(3)
Tb = 272 + rng.normal(0, 0.3, y.shape)
T15 = Tb - 1.0
c = n // 2
Tb[c, c], T15[c, c] = 330.0, 280.0
Tb[c, c + 1], T15[c, c + 1] = 300.0, 278.0
rad = {"M13": MV.temperatura_a_radiancia(Tb, MV.LAMBDA_M13), "M15": MV.temperatura_a_radiancia(T15, 10.763)}
ang = {k: np.full(lat.shape, v) for k, v in {"sensor_zenith": 20.0, "sensor_azimuth": 100.0, "solar_zenith": 120.0, "solar_azimuth": 200.0}.items()}
with patch.object(PVM, "ENABLE_V750_CODIGO_MIROVA", True), patch.object(MV, "leer_radiancia_l1b", return_value=rad), \
     patch.object(MV, "leer_geo_l1b", return_value=(lat, lon, ang)):
    rv = PVM.calculate_vrp(Path("VJ102MOD.A2026290.0554.021.nc"), Path("g.nc"), ll["lat"], ll["lon"], ll["radius_km"],
                           vent_lat=ll.get("vent_lat"), vent_lon=ll.get("vent_lon"), inner_radius_km=ll.get("inner_radius_km"))
print("E4 record de la via:", None if rv is None else {k: rv.get(k) for k in ("sensor", "vrp_mw", "via_codigo_mirova", "granule", "product_version", "datetime_utc", "n_anomalous_pixels", "t_bg_k", "t_max_k", "distance_class")})
for k in ("sensor", "vrp_mw", "t_bg_k", "t_max_k", "n_anomalous_pixels"):
    assert rv is not None and k in rv, f"run_pipeline lee result['{k}'] y falta"
print("E4 claves que run_pipeline lee tras append_record: presentes")

# ---------------- E5: almacén; el record de la vía vs el mismo record sin marca con las 3 compuertas desactivadas
import pipeline.store as S
def almacena(rec, **kw):
    with tempfile.TemporaryDirectory() as t:
        S.DATA_DIR = Path(t)
        r = copy.deepcopy(rec); 
        args = dict(volcano_lat=ll["lat"], volcano_lon=ll["lon"], max_hotspot_dist_km=ll["radius_km"],
                    enable_pixel_level_distance_filter=True, max_cluster_pixels=ll.get("max_cluster_pixels") or 12,
                    inner_radius_km=ll.get("inner_radius_km"))
        args.update(kw)
        S.append_record("Llaima", r, **args)
        out = json.loads((Path(t) / "Llaima.json").read_text(encoding="utf-8"))
    out = out["records"] if isinstance(out, dict) else out
    o = out[0]
    for k in ("processed_utc", "first_processed_utc"): o.pop(k, None)
    return o
os.environ["GITHUB_SHA"] = "vc"
rv["datetime_utc"] = "2026-10-10 05:54"
a = almacena(rv)
b_marca_fuera = copy.deepcopy(rv); b_marca_fuera.pop("via_codigo_mirova")
b = almacena(b_marca_fuera, enable_pixel_level_distance_filter=False, max_hotspot_dist_km=1e9, max_cluster_pixels=None)
b["via_codigo_mirova"] = True
print("E5 via (compuertas saltadas) == sin marca y con las 3 compuertas desactivadas a mano:", json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True))
