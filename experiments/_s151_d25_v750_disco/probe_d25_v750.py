# -*- coding: utf-8 -*-
"""S151 (loop 1.5): probe de sólo lectura del fondo por vecinos (D25) en VIIRS 750. ESCRITO, NO DESPACHADO.

POR QUÉ HACE FALTA. Los records persistidos no guardan a los vecinos del píxel caliente:
`anomaly_pixels` trae sólo los píxeles alertados y `diag_L_bg_local_w_m2_sr_um` es nulo en V750
(listar_y_techo.py, techo.json). Y lo que decide es justo eso: medido sobre los 268 negativos, CUALQUIER
magnitud positiva bajo 10 MW los hace publicar a todos (techo.json, controles C1 a C4 en verde), así que
la pregunta se reduce al SIGNO del contraste del cráter contra sus vecinos, que sólo el granule conoce.

QUÉ HACE. Por cada pasada de pasadas.json (268+3 negativos en cero, 28 alertas en cero, 40 pasadas que
ya publican como control) baja el L1B y el GEO del MISMO granule que el record (nombre exacto) y corre
`process_viirs_mod.calculate_vrp` tres veces en el mismo proceso, cambiando sólo el global del módulo:
  control  flag D25 apagado (producción). Debe reproducir el record persistido (control C-P1).
  a        flag D25 encendido: media de la radiancia de los vecinos NO alertados (canon 2016a ec. 6),
           max_half_px del perfil.
  b        a + descarte de vecinos con BT11 (M15) < 255 K (Coppola 2014 p. 3412; variante, no canon).
Después `store.append_record` con la escritura anulada (agrega vrp_mw unificado y discarded_reason, que
el predicado del tablero lee). No escribe en data/, no commitea, no hace push.

CONTROL C-P1 (fijado antes de correr; si falla en más del 10 % de las pasadas el resultado es
INDECIDIBLE y no se interpreta): en el brazo control, pc.vrp_mw igual al persistido con
|diferencia| <= max(1e-3 MW, 1 %), mismo pc.n_pixels y pc.centroid_dist_km a <= 0,01 km.
Los envoltorios cuentan cuántas veces se llamó el fondo por vecinos y cuántos vecinos sacó la nube,
para comprobar que cada brazo hizo lo que declara (A118: el flag tiene que llegar a sus consumidores).

Env: PROBE_VOL (filtra volcán), PROBE_PASADAS (ruta), PROBE_MAX (tope de pasadas, para pilotear).
Salida: out/<volcan>/<pasada>_<sensor>.json. Sale 2 si falta alguna pasada (S141).
"""
import io
import json
import os
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")   # ANTES de importar el pipeline
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for p in (ROOT, ROOT / "scripts", HERE):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402
import pipeline.process_viirs_mod as pvm  # noqa: E402
import pipeline.store as store  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from run_pipeline import VOLCANIC_FEATURES, load_volcanoes, vrp_profile  # noqa: E402
import variantes  # noqa: E402

store._save = lambda *a, **kw: None   # sólo lectura

PRODUCTOS = {"VIIRS_SNPP_750": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
             "VIIRS_NOAA20_750": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
             "VIIRS_NOAA21_750": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO")}
CAMPOS = ("sensor", "datetime_utc", "vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "t_bg_k", "t_max_k",
          "n_anomalous_pixels", "final_hotspot_source", "final_hotspot_dist_km", "distance_class",
          "discarded_reason", "primary_cluster", "triggered_test1", "diag_n_first_pass_pixels",
          "diag_n_second_pass_recapture", "f5_core_vrp_mw", "diag_bg_vecinos_n_sin_vecinos",
          "diag_L_bg_vecinos_w_m2_sr_um", "anomaly_pixels", "product_version")
DEST = HERE / "granules"
OUT = HERE / "out"

ESTADO = {"brazo": None, "bands": None, "llamadas": [], }
_leer_real = pvm.read_viirs_mod_l1b
_fondo_real = pvm.vrp_bg_neighbor_mean_v750


def _leer_y_guardar(path, *a, **kw):
    bands = _leer_real(path, *a, **kw)
    ESTADO["bands"] = bands
    return bands


def _fondo_envuelto(bt_grid, alert_mask, hot_rows, hot_cols, legacy_l_bg, *, max_half_px):
    """Brazo b: suma la nube a los alertados. Los dos brazos: registra qué pasó en cada píxel."""
    mask = np.asarray(alert_mask, dtype=bool)
    tir = (ESTADO["bands"] or {}).get("M15")
    diag = {"n_hot": int(len(hot_rows)), "brazo": ESTADO["brazo"]}
    if ESTADO["brazo"] == "b":
        if tir is None:
            raise RuntimeError("brazo b sin M15: no se puede descartar nube")
        diag["vecinos_8"] = variantes.contar_vecinos_nublados(mask, tir, hot_rows, hot_cols)
        mask = variantes.alertados_mas_nube(mask, tir)
    l_bg, n_sin = _fondo_real(bt_grid, mask, hot_rows, hot_cols, legacy_l_bg, max_half_px=max_half_px)
    l_hot = pvm.bt_to_spectral_radiance(np.asarray(bt_grid)[hot_rows, hot_cols].astype(np.float64), pvm.M13_LAMBDA)
    leg = np.broadcast_to(np.asarray(legacy_l_bg, dtype=np.float64), np.shape(l_bg))
    diag.update({"n_sin_vecinos": n_sin, "bt_hot_k": np.round(np.asarray(bt_grid)[hot_rows, hot_cols], 3).tolist(),
                 "L_hot": np.asarray(l_hot).tolist(), "L_bg_hoy": leg.tolist(), "L_bg_nuevo": np.asarray(l_bg).tolist()})
    ESTADO["llamadas"].append(diag)
    return l_bg, n_sin


pvm.read_viirs_mod_l1b = _leer_y_guardar
pvm.vrp_bg_neighbor_mean_v750 = _fondo_envuelto


def _tipo(nombre):
    n = nombre.upper()
    return "GEO" if "03MOD" in n else ("L1B" if "02MOD" in n else "")


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:120]


def bajar_par(vol, fila):
    """L1B con el nombre EXACTO del record (mismo producto y versión) y su GEO del mismo instante."""
    l1b_nombre = fila["granule"]
    stamp = ".".join(l1b_nombre.split(".")[1:3])          # A2026282.0612
    dt = datetime.strptime(fila["pasada_utc"], "%Y-%m-%d %H:%M")
    out = []
    for key in PRODUCTOS[fila["sensor"]]:
        grs = [g for g in search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt) if stamp in gname(g)]
        if key.endswith("_L1B"):
            grs = [g for g in grs if gname(g) == l1b_nombre] or grs
        if not grs:
            return None, f"sin granule {key} {stamp}"
        got = [Path(p) for p in download_granules(grs[:1], DEST) if stamp in Path(p).name]
        if not got:
            return None, f"descarga fallida {key} {stamp}"
        out.append(got[0])
    if out[0].name != l1b_nombre:
        return None, f"L1B distinto del persistido: {out[0].name} contra {l1b_nombre}"
    return tuple(out), None


def correr(vol, par, brazo):
    pvm.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = brazo in ("a", "b")
    ESTADO.update({"brazo": brazo, "bands": None, "llamadas": []})
    ancla_lat, ancla_lon = get_detection_anchor(vol)
    rec = pvm.calculate_vrp(par[0], par[1], vol["lat"], vol["lon"], vol["radius_km"],
                            vent_lat=ancla_lat, vent_lon=ancla_lon,
                            vent_radius_km=vol.get("vent_radius_km", 4.0),
                            inner_radius_km=vol.get("inner_radius_km"),
                            exclude_zones=vol.get("exclude_zones"),
                            active_water_bodies=vol.get("active_water_bodies"),
                            lbg_global_compatible=vol.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=vol.get("local_kernel_bg", False))
    if rec is None:
        return {"error": "calculate_vrp devolvió None"}
    store.append_record(vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"], overwrite=True,
                        max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"),
                        inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=VOLCANIC_FEATURES.get(vol["name"]))
    return {"record": {k: rec.get(k) for k in CAMPOS if k in rec}, "llamadas_fondo": list(ESTADO["llamadas"]),
            "flag_efectivo": bool(pvm.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750)}


def control_p1(persistido, ctrl):
    pc = (ctrl.get("record") or {}).get("primary_cluster") or {}
    if persistido["pc_vrp_mw"] is None:
        return pc == {}
    a, b = pc.get("vrp_mw"), persistido["pc_vrp_mw"]
    if a is None:
        return False
    da = pc.get("centroid_dist_km"), persistido["pc_centroid_dist_km"]
    return (abs(a - b) <= max(1e-3, 0.01 * abs(b)) and pc.get("n_pixels") == persistido["pc_n_pixels"]
            and da[0] is not None and da[1] is not None and abs(da[0] - da[1]) <= 0.01)


def main():
    lista = json.loads(Path(os.environ.get("PROBE_PASADAS", "").strip() or HERE / "pasadas.json").read_text(encoding="utf-8"))
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    lista = [x for x in lista if not f_vol or x["volcan"] == f_vol]
    tope = int(os.environ.get("PROBE_MAX", "0") or 0)
    if tope:
        lista = lista[:tope]
    print(f"{len(lista)} pasadas | perfil {os.environ['VRP_PROFILE']} | max_half_px {pvm.VRP_BG_NEIGHBOR_MAX_HALF_PX}", flush=True)
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    n_ok = n_cp1 = 0
    for fila in lista:
        vol = vols[fila["volcan"]]
        res = {**fila, "ok": False}
        try:
            par, err = bajar_par(vol, fila)
            if par is None:
                res["error"] = err
            else:
                for brazo in ("control", "a", "b"):
                    res[brazo] = correr(vol, par, brazo)
                res["control_p1"] = control_p1(fila["persistido"], res["control"])
                res["ok"] = all("record" in res[b] for b in ("control", "a", "b"))
                n_ok += res["ok"]
                n_cp1 += bool(res["control_p1"])
                for p in par:
                    p.unlink(missing_ok=True)      # el runner tiene ~14 GB; no se acumulan granules
        except Exception as e:
            res["error"] = str(e)
            res["traceback"] = traceback.format_exc()
        pcs = {b: ((res.get(b) or {}).get("record") or {}).get("primary_cluster") or {} for b in ("control", "a", "b")}
        print(f"  {fila['clase']:15s} {fila['volcan']} {fila['pasada_utc']} {fila['sensor']}: ok={res['ok']} "
              f"cp1={res.get('control_p1')} pc_vrp persist={fila['persistido']['pc_vrp_mw']} "
              f"control={pcs['control'].get('vrp_mw')} a={pcs['a'].get('vrp_mw')} b={pcs['b'].get('vrp_mw')} "
              f"err={res.get('error')}", flush=True)
        d = OUT / fila["volcan"]
        d.mkdir(parents=True, exist_ok=True)
        nombre = f"{fila['pasada_utc'].replace(' ', '_').replace(':', '')}_{fila['sensor']}.json"
        (d / nombre).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=_a_json), encoding="utf-8")
    shutil.rmtree(DEST, ignore_errors=True)
    print(f"{n_ok} de {len(lista)} pasadas con los tres brazos; control C-P1 en {n_cp1}", flush=True)
    if n_ok < len(lista):
        sys.exit(2)


def _a_json(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


if __name__ == "__main__":
    main()
