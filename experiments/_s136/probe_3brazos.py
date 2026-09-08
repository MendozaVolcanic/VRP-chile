"""S136 - probe de 3 brazos sobre la interseccion contextual del Test 1.

QUE MIDE. Cuanto cambia la magnitud publicada al apagar la interseccion contextual del Test 1
(`process_viirs.py:1773-1791`), con el codigo de HOY. La data persistida no puede responderlo
porque lleva el filtro puesto (`experiments/_s136/RESULTADO_MEDICION.md`), asi que el probe
procesa el MISMO granule tres veces variando solo los dos flags.

COMO (A75, read-only). `process_viirs` importa los flags al namespace del modulo (linea 176),
asi que se reasignan ahi por brazo. No edita ningun modulo, no escribe en `data/`, no hace push.
Parchear el modulo origen (`pipeline.profile`) NO tendria efecto: es la trampa A89 que el probe
de S135 documenta.

BRAZOS: ACTUAL (filtro ON + keep_peak ON, la produccion) / SIN_KEEP (filtro ON, keep OFF) /
SIN_FILTRO (filtro OFF, la hipotesis). Criterio y desenlaces fijados de antemano en
`docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md`.

DONDE. Solo en GitHub Actions (A71): los granules no se bajan al PC (disco al 98 %) y las
credenciales validas viven en los secrets.

Salida: `out/resultado_3brazos.json`.
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.f5_core import f5_core_vrp_mw  # noqa: E402
import pipeline.process_viirs as pv  # noqa: E402
from run_pipeline import load_volcanoes  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
DEST = HERE / "granules"
PRODUCTOS = {
    "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
    "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
    "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
}
# (nombre del brazo, filtro, keep_peak). El orden solo afecta al reporte.
BRAZOS = (("ACTUAL", True, True), ("SIN_KEEP", True, False), ("SIN_FILTRO", False, False))
# Los flags viven en el namespace de pv (A89): parchear pipeline.profile no haria nada.
FLAG_FILTRO = "ENABLE_TEST1_CONTEXTUAL_FILTER"
FLAG_KEEP = "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK"

CLAVES = ("final_hotspot_source", "final_hotspot_dist_km", "final_hotspot_lat",
          "final_hotspot_lon", "distance_class", "vrp_mw", "vrp_mir_mw", "t_bg_k",
          "n_anomalous_pixels", "triggered_test1", "n_test1_pixels", "n_dnti_ctx_path",
          "diag_n_first_pass_pixels", "nti_max")


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def stamp_de(pasada_utc):
    dt = datetime.strptime(pasada_utc, "%Y-%m-%d %H:%M")
    return dt, "A{}{:03d}.{:%H%M}".format(dt.year, dt.timetuple().tm_yday, dt)


def bajar_par(vol, platform, dt, stamp):
    l1b_key, geo_key = PRODUCTOS[platform]
    paths = {}
    for key in (l1b_key, geo_key):
        grs = search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt)
        sel = [g for g in grs if stamp in gname(g)]
        print("    {}: {} del dia, {} con {}".format(key, len(grs), len(sel), stamp), flush=True)
        if not sel:
            return None
        got = [p for p in download_granules(sel, DEST) if stamp in Path(p).name]
        if not got:
            return None
        paths[key] = Path(got[0])
    return paths[l1b_key], paths[geo_key]


def procesar(vol, l1b, geo, ancla_lat, ancla_lon):
    return pv.calculate_vrp(
        l1b, geo, vol["lat"], vol["lon"], vol["radius_km"],
        vent_lat=ancla_lat, vent_lon=ancla_lon,
        vent_radius_km=vol.get("vent_radius_km", 4.0),
        inner_radius_km=vol.get("inner_radius_km"),
        exclude_zones=vol.get("exclude_zones"),
        active_water_bodies=vol.get("active_water_bodies"),
        lbg_global_compatible=vol.get("lbg_global_compatible", False),
        local_kernel_bg_compatible=vol.get("local_kernel_bg", False),
        lava_lake_magmatic=vol.get("lava_lake_magmatic", False),
    )


def magnitud_publicada(rec, inner_km):
    """Lo que ve el operador en VIIRS375: el nucleo (A46/S132); si no, pc.vrp_mw (A10)."""
    if rec is None:
        return None
    try:
        core = f5_core_vrp_mw(rec, inner_km)
    except Exception:
        core = None
    if core is not None:
        return float(core)
    pc = rec.get("primary_cluster") or {}
    return pc.get("vrp_mw")


def correr_pasada(vol, caso):
    dt, stamp = stamp_de(caso["pasada_utc"])
    print("=== {} {} {} {} ===".format(caso["clase"], vol["name"], caso["pasada_utc"],
                                       caso["sensor"]), flush=True)
    fila = dict(caso)
    fila["ok"] = False
    par = bajar_par(vol, caso["sensor"], dt, stamp)
    if par is None:
        fila["error"] = "granule no encontrado o no descargado"
        print("    " + fila["error"], flush=True)
        return fila
    l1b, geo = par
    ancla_lat, ancla_lon = get_detection_anchor(vol)
    inner = vol.get("inner_radius_km")
    fila["brazos"] = {}
    for nombre, filtro, keep in BRAZOS:
        setattr(pv, FLAG_FILTRO, filtro)
        setattr(pv, FLAG_KEEP, keep)
        try:
            rec = procesar(vol, l1b, geo, ancla_lat, ancla_lon)
        except Exception as e:
            fila["brazos"][nombre] = {"error": str(e), "traceback": traceback.format_exc()}
            print("    {:10s} ERROR {}".format(nombre, e), flush=True)
            continue
        if rec is None:
            fila["brazos"][nombre] = {"error": "calculate_vrp devolvio None"}
            print("    {:10s} None (el granule no cubre el volcan)".format(nombre), flush=True)
            continue
        mag = magnitud_publicada(rec, inner)
        fila["brazos"][nombre] = {
            "magnitud_publicada_mw": mag,
            "record": {k: rec.get(k) for k in CLAVES if k in rec},
        }
        gt = caso.get("mirova_vrp_mw")
        ratio = (mag / gt) if (mag and gt) else None
        print("    {:10s} vrp={} MIROVA={} ratio={} source={} d={}".format(
            nombre,
            None if mag is None else round(mag, 4), gt,
            None if ratio is None else round(ratio, 2),
            rec.get("final_hotspot_source"), rec.get("final_hotspot_dist_km")), flush=True)
    # dejar los flags como en produccion por si algo mas corre despues
    setattr(pv, FLAG_FILTRO, True)
    setattr(pv, FLAG_KEEP, True)
    fila["ok"] = any("magnitud_publicada_mw" in b for b in fila["brazos"].values())
    return fila


def main():
    OUT.mkdir(exist_ok=True)
    DEST.mkdir(exist_ok=True)
    casos = json.loads((HERE / "pasadas_s136.json").read_text(encoding="utf-8"))
    solo = os.environ.get("PROBE_VOL")
    if solo:
        casos = [c for c in casos if c["volcan"] == solo]
    print("{} pasadas, {} brazos cada una\n".format(len(casos), len(BRAZOS)), flush=True)
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    filas = []
    for caso in casos:
        vol = vols.get(caso["volcan"])
        if vol is None:
            print("!! {} no esta en volcanoes.yaml".format(caso["volcan"]), flush=True)
            continue
        try:
            filas.append(correr_pasada(vol, caso))
        except Exception as e:
            print("!! {} {}: {}".format(caso["volcan"], caso["pasada_utc"], e), flush=True)
            filas.append(dict(caso, ok=False, error=str(e), traceback=traceback.format_exc()))
        (OUT / "resultado_3brazos.json").write_text(
            json.dumps(filas, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print("\nlistas {}/{} pasadas -> {}".format(
        sum(1 for f in filas if f.get("ok")), len(filas), OUT / "resultado_3brazos.json"),
        flush=True)


if __name__ == "__main__":
    main()
