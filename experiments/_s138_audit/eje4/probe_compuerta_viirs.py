# -*- coding: utf-8 -*-
"""S138 eje 4 (e): probe por etapa (A75, read-only) de la compuerta `bt > t_bg + 3 K` y del
fondo del anillo en VIIRS 375 m y 750 m, sobre pasadas concretas con ALERTA de MIROVA.

POR QUE HACE FALTA. Los JSON persistidos no guardan cuantos pixeles pasaron los Tests 2 y 3
y cayeron SOLO por la compuerta: `first_pass_tests_2_and_3` (pipeline/detection_context.py)
devuelve `n_first_pass_pixels` ya con la compuerta aplicada. Sobre data/ solo se puede inferir
el costo por la puerta trasera del segundo paso sin activos (scripts 01 y 02 de esta carpeta).
Este probe mide el costo directo, en la unidad del fenomeno: pixeles del crater por pasada.

QUE MIDE, por pasada (dentro del inner_radius_km del volcan):
  1. Primer paso descompuesto: n que pasan Test 2, Test 3, ambos, ambos + compuerta; con la
     conectiva de la formula (min) y con la de la prosa (max). El pixel mas cercano al crater y
     el mejor candidato, con dNTI, dETI, BT y BT - t_bg.
  2. Segundo paso: cuantos `newly_active` entran con el conjunto activo vacio y cuantos de esos
     estan bajo la compuerta (deberian ser ~100 %: si no, el segundo paso rescata otra cosa).
  3. Magnitud del cumulo del crater con TRES fondos: anillo 5-25 km (lo de hoy, `t_bg`),
     kernel local 3x3 (`compute_local_background`, opt-in hoy en 5 volcanes) y corona Eq.6
     (`apply_corona_magnitude_v375`, flag OFF hoy). Es el "fondo local" que en S137 devolvio la
     magnitud de Villarrica A6 en MODIS. Aca se mide en VIIRS.

COMO (A75). Envuelve `first_pass_tests_2_and_3`, `second_pass_adjacent` y `cluster_hotspots`
en el NAMESPACE de `pipeline.process_viirs` y de `pipeline.process_viirs_mod` (importan por
nombre; parchear el modulo origen no cambia nada, trampa A89). Los envoltorios devuelven
exactamente lo que devuelve la original: no cambian la deteccion, solo la observan.
No escribe en data/, no toca pipeline/ ni perfiles, no empuja commits.

DONDE. Solo en GitHub Actions (yml en esta misma carpeta, NO en .github/workflows/: copiarlo
ahi es decision del orquestador). Las credenciales validas viven en los secrets (A71).

Entradas: PROBE_PASADAS = ruta a un JSON [{volcan, pasada_utc, sensor, clase, nota}] (default:
pasadas_eje4.json de esta carpeta). PROBE_VOL / PROBE_FECHA filtran.
Salida: experiments/_s138_audit/eje4/out_probe/<vol>_<fecha>_<hhmm>_<sensor>.json + report.txt.

Control positivo pre-registrado: Lascar 2026-06-17 05:42 VIIRS_SNPP (fp > 0 persistido) debe
dar `ambos_y_bt` > 0 y la magnitud con anillo > 0. Control del instrumento: en toda pasada,
`ambos_y_bt` (formula) tiene que coincidir con `n_first_pass_pixels` restringido al inner; si
no coincide, el envoltorio no esta midiendo lo que corre.
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import pipeline.detection_context as dc  # noqa: E402
import pipeline.process_viirs as pv  # noqa: E402
import pipeline.process_viirs_mod as pm  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.vrp_regimes import compute_local_background  # noqa: E402
from run_pipeline import load_volcanoes  # noqa: E402

OUT = HERE / "out_probe"
DEST = HERE / "granules"
PRODUCTOS = {
    "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO", pv),
    "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO", pv),
    "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO", pv),
    "VIIRS_SNPP_750": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO", pm),
    "VIIRS_NOAA20_750": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO", pm),
    "VIIRS_NOAA21_750": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO", pm),
}
# Area nadir fija (A66/A67: el pipeline usa area constante por sensor).
AREA_M2 = {pv: 375.0 * 375.0, pm: 750.0 * 750.0}
LAMBDA = {pv: pv.I04_LAMBDA, pm: pm.M13_LAMBDA}
WOOSTER = {pv: pv.WOOSTER_COEFF, pm: pm.WOOSTER_COEFF}
PATCH = ("first_pass_tests_2_and_3", "second_pass_adjacent", "cluster_hotspots")
_REAL = {(m.__name__, n): getattr(m, n) for m in (pv, pm) for n in PATCH}
_CAP = {}


def _f(x):
    try:
        return None if x is None or not np.isfinite(x) else float(x)
    except TypeError:
        return None


def descomponer_primer_paso(kw, diag):
    """Cuenta cada condicion del primer paso por separado dentro del inner. Funcion pura."""
    nti, bt = kw["nti"], kw["bt"]
    eti = diag.get("eti")
    if eti is None:
        return {"error": "sin eti (pool de fondo insuficiente)", "n_bg_used": diag.get("n_bg_used")}
    mean8 = dc._nanmean_8neighbors_fast
    dnti = nti - mean8(nti)
    deti = eti - mean8(eti)
    dist = kw["dist_km"]
    inner = kw["inner_km"]
    ok = kw["roi_mask"] & np.isfinite(dnti) & np.isfinite(deti) & (dist <= inner)
    t_bg, margen = kw["t_bg"], kw["bt_sanity_k"]
    gate = np.isfinite(bt) & (bt > t_bg + margen)
    c1 = kw["c1_dnti_summit"]
    c2 = kw["c2_dnti_summit"]
    out = {"n_inner": int(ok.sum()), "t_bg": _f(t_bg), "t_bg_mas_margen": _f(t_bg + margen),
           "n_first_pass_escena": diag.get("n_first_pass_pixels"),
           "sd_dnti": _f(diag.get("sd_dnti")), "sd_deti": _f(diag.get("sd_deti"))}
    for nombre, comb in (("formula_min", min), ("prosa_max", max)):
        td = comb(c1, diag["mu_dnti"] + c2 * diag["sd_dnti"])
        te = comb(c1, diag["mu_deti"] + c2 * diag["sd_deti"])
        p2, p3 = ok & (dnti > td), ok & (deti > te)
        out[nombre] = {"thr_dnti": _f(td), "thr_deti": _f(te), "n_test2": int(p2.sum()),
                       "n_test3": int(p3.sum()), "n_ambos": int((p2 & p3).sum()),
                       "n_ambos_y_bt": int((p2 & p3 & gate).sum()),
                       "n_solo_compuerta": int((p2 & p3 & ~gate).sum())}
    if ok.any():
        def px(idx):
            return {"dnti": _f(dnti[idx]), "deti": _f(deti[idx]), "bt": _f(bt[idx]),
                    "bt_menos_t_bg": _f(bt[idx] - t_bg), "pasa_compuerta": bool(gate[idx]),
                    "dist_km": _f(dist[idx])}
        peor = np.where(ok, np.minimum(dnti, deti), -np.inf)
        out["mejor_candidato"] = px(np.unravel_index(int(np.argmax(peor)), nti.shape))
        out["pixel_crater"] = px(np.unravel_index(int(np.argmin(np.where(ok, dist, np.inf))), nti.shape))
    return out


def envolver_fp(mod):
    real = _REAL[(mod.__name__, "first_pass_tests_2_and_3")]

    def w(*a, **kw):
        res = real(*a, **kw)
        try:
            hot, diag = res
            if a:
                _CAP["first_pass"] = {"error": "llamada posicional"}
            else:
                _CAP["first_pass"] = descomponer_primer_paso(kw, diag)
                _CAP["_bt"] = np.array(kw["bt"], dtype=float)
                _CAP["_dist"] = np.array(kw["dist_km"], dtype=float)
                _CAP["_t_bg"] = float(kw["t_bg"])
                _CAP["_inner"] = float(kw["inner_km"])
        except Exception as e:  # observar nunca debe romper la corrida
            _CAP["first_pass"] = {"error": repr(e)}
        return res
    return w


def envolver_sp(mod):
    real = _REAL[(mod.__name__, "second_pass_adjacent")]

    def w(*a, **kw):
        out = real(*a, **kw)
        try:
            act = np.asarray(kw.get("active_mask", a[2] if len(a) > 2 else None), dtype=bool)
            nuevos = np.asarray(out, dtype=bool) & ~act
            bt, dist, t_bg, inner = _CAP["_bt"], _CAP["_dist"], _CAP["_t_bg"], _CAP["_inner"]
            nuevos_inner = nuevos & (dist <= inner)
            bajo = nuevos_inner & ~(np.isfinite(bt) & (bt > t_bg + pv.NTI_BT_SANITY_K))
            _CAP.setdefault("second_pass", []).append({
                "n_active_in": int(act.sum()), "n_newly": int(nuevos.sum()),
                "n_newly_inner": int(nuevos_inner.sum()),
                "n_newly_inner_bajo_compuerta": int(bajo.sum())})
        except Exception as e:
            _CAP.setdefault("second_pass", []).append({"error": repr(e)})
        return out
    return w


def envolver_cl(mod):
    real = _REAL[(mod.__name__, "cluster_hotspots")]

    def w(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
        cl = real(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
        try:
            _CAP.setdefault("clusters", []).append({
                "n_in": int(np.asarray(hot_mask_2d, dtype=bool).sum()),
                "strategy": kw.get("strategy"),
                "primario": ({k: v for k, v in cl[0].items() if k != "pixel_indices"} if cl else None),
                "_idx": (cl[0]["pixel_indices"] if cl else None),
                "_hot": np.asarray(hot_mask_2d, dtype=bool)})
        except Exception as e:
            _CAP.setdefault("clusters", []).append({"error": repr(e)})
        return cl
    return w


def magnitud_tres_fondos(mod, idx, hot):
    """VRP del cumulo con anillo, kernel 3x3 y corona Eq.6 (area nadir fija)."""
    bt = _CAP["_bt"]
    lam, k, area = LAMBDA[mod], WOOSTER[mod], AREA_M2[mod]
    rows = [i for i, _ in idx]
    cols = [j for _, j in idx]
    L_hot = mod.bt_to_spectral_radiance(bt[rows, cols], lam)
    L_ring = mod.bt_to_spectral_radiance(np.float64(_CAP["_t_bg"]), lam)
    vrp_anillo = float(np.sum(area * k * np.maximum(L_hot - L_ring, 0.0) / 1e6))
    t_loc = np.array(compute_local_background(bt, rows, cols, kernel_size=3), dtype=float)
    t_loc = np.where(np.isnan(t_loc), _CAP["_t_bg"], t_loc)
    L_loc = mod.bt_to_spectral_radiance(t_loc, lam)
    vrp_kernel = float(np.sum(area * k * np.maximum(L_hot - L_loc, 0.0) / 1e6))
    out = {"anillo_5_25km": vrp_anillo, "kernel_3x3": vrp_kernel,
           "bt_pico": _f(np.max(bt[rows, cols])), "bt_pico_menos_t_bg": _f(np.max(bt[rows, cols]) - _CAP["_t_bg"])}
    try:
        areas = np.full_like(bt, area, dtype=float)
        v_cor, degr, _pix = pv.apply_corona_magnitude_v375(
            vrp_anillo, bt, areas, idx, hot, enabled=True, mode=pv.LOCAL_CLUSTER_MAG_MODE,
            ring_px=pv.LOCAL_CLUSTER_MAG_RING_PX, min_corona=pv.LOCAL_CLUSTER_MAG_MIN_CORONA)
        out["corona_eq6"] = float(v_cor)
        out["corona_degradada"] = bool(degr) if degr is not None else None
    except Exception as e:
        out["corona_eq6"] = None
        out["corona_error"] = repr(e)
    return out


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def bajar_par(vol, l1b_key, geo_key, dt, stamp):
    paths = {}
    for key in (l1b_key, geo_key):
        grs = search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt)
        sel = [g for g in grs if stamp in gname(g)]
        print(f"    {key}: {len(grs)} granules del dia, {len(sel)} con {stamp}", flush=True)
        if not sel:
            return None
        got = [p for p in download_granules(sel, DEST) if stamp in Path(p).name]
        if not got:
            return None
        paths[key] = Path(got[0])
    return paths[l1b_key], paths[geo_key]


def correr(vol, pasada_utc, sensor, clase, nota):
    dt = datetime.strptime(pasada_utc, "%Y-%m-%d %H:%M")
    stamp = f"A{dt.year}{dt.timetuple().tm_yday:03d}.{dt:%H%M}"
    l1b_key, geo_key, mod = PRODUCTOS[sensor]
    fila = {"volcan": vol["name"], "pasada_utc": pasada_utc, "sensor": sensor, "clase": clase,
            "nota": nota, "stamp": stamp, "ok": False}
    print(f"=== {clase} {vol['name']} {pasada_utc} {sensor} ({stamp}) ===", flush=True)
    par = bajar_par(vol, l1b_key, geo_key, dt, stamp)
    if par is None:
        fila["error"] = "granule no encontrado o no descargado"
        return fila
    l1b, geo = par
    ancla_lat, ancla_lon = get_detection_anchor(vol)
    _CAP.clear()
    try:
        rec = mod.calculate_vrp(
            l1b, geo, vol["lat"], vol["lon"], vol["radius_km"],
            vent_lat=ancla_lat, vent_lon=ancla_lon,
            vent_radius_km=vol.get("vent_radius_km", 4.0),
            inner_radius_km=vol.get("inner_radius_km"),
            exclude_zones=vol.get("exclude_zones"),
            active_water_bodies=vol.get("active_water_bodies"),
            lbg_global_compatible=vol.get("lbg_global_compatible", False),
            local_kernel_bg_compatible=vol.get("local_kernel_bg", False),
            **({"lava_lake_magmatic": vol.get("lava_lake_magmatic", False)} if mod is pv else {}),
        )
    except Exception as e:
        fila["error"] = f"calculate_vrp: {e}"
        fila["traceback"] = traceback.format_exc()
        return fila
    if rec is None:
        fila["error"] = "calculate_vrp devolvio None (granule no cubre el volcan)"
        return fila
    pc = rec.get("primary_cluster") or {}
    fila["record"] = {k: rec.get(k) for k in (
        "t_bg_k", "t_max_k", "final_hotspot_source", "final_hotspot_dist_km", "distance_class",
        "triggered_test1", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture",
        "n_anomalous_pixels", "nti_max")}
    fila["record"]["primary_cluster"] = {k: v for k, v in pc.items()}
    fila["primer_paso"] = _CAP.get("first_pass")
    fila["segundo_paso"] = _CAP.get("second_pass")
    # magnitud con tres fondos del primer cumulo contextual (el que el ancla honesta publica)
    cls = [c for c in _CAP.get("clusters", []) if c.get("_idx")]
    if cls and "_bt" in _CAP:
        c = cls[0]
        fila["cumulo_contextual"] = c["primario"]
        fila["magnitud_tres_fondos"] = magnitud_tres_fondos(mod, c["_idx"], c["_hot"])
    fila["ok"] = True
    fp, sp = fila["primer_paso"] or {}, fila["segundo_paso"] or []
    fm = (fp.get("formula_min") or {}) if isinstance(fp, dict) else {}
    print(f"    record: fuente={rec.get('final_hotspot_source')} pc_vrp={pc.get('vrp_mw')} "
          f"pc_dist={pc.get('centroid_dist_km')} t_bg={rec.get('t_bg_k')} fp={rec.get('diag_n_first_pass_pixels')} "
          f"sp={rec.get('diag_n_second_pass_recapture')}", flush=True)
    print(f"    1er paso (formula): test2={fm.get('n_test2')} test3={fm.get('n_test3')} ambos={fm.get('n_ambos')} "
          f"ambos+compuerta={fm.get('n_ambos_y_bt')} SOLO_COMPUERTA={fm.get('n_solo_compuerta')}", flush=True)
    if isinstance(fp, dict) and fp.get("pixel_crater"):
        pcx = fp["pixel_crater"]
        print(f"    pixel del crater: dNTI={pcx['dnti']} dETI={pcx['deti']} BT={pcx['bt']} "
              f"(BT-t_bg={pcx['bt_menos_t_bg']}) pasa_compuerta={pcx['pasa_compuerta']}", flush=True)
    for s in sp:
        print(f"    2do paso: activos_in={s.get('n_active_in')} nuevos_inner={s.get('n_newly_inner')} "
              f"bajo_compuerta={s.get('n_newly_inner_bajo_compuerta')}", flush=True)
    if fila.get("magnitud_tres_fondos"):
        m = fila["magnitud_tres_fondos"]
        print(f"    magnitud: anillo={m['anillo_5_25km']:.3f} kernel3x3={m['kernel_3x3']:.3f} "
              f"corona={m.get('corona_eq6')} (BT pico - t_bg = {m['bt_pico_menos_t_bg']})", flush=True)
    return fila


def a_json(o):
    if isinstance(o, dict):
        return {k: a_json(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [a_json(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return None
    return o


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    for mod in (pv, pm):
        mod.first_pass_tests_2_and_3 = envolver_fp(mod)
        mod.second_pass_adjacent = envolver_sp(mod)
        mod.cluster_hotspots = envolver_cl(mod)
    src = Path(os.environ.get("PROBE_PASADAS") or (HERE / "pasadas_eje4.json"))
    lista = json.loads(src.read_text(encoding="utf-8"))
    f_vol, f_fecha = os.environ.get("PROBE_VOL", "").strip(), os.environ.get("PROBE_FECHA", "").strip()
    sel = [x for x in lista if (not f_vol or x["volcan"] == f_vol)
           and (not f_fecha or x["pasada_utc"].startswith(f_fecha))]
    print(f"Probe S138 eje 4: {len(sel)} pasadas (perfil {os.environ['VRP_PROFILE']}); "
          f"NTI_BT_SANITY_K={pv.NTI_BT_SANITY_K}; ENABLE_SECOND_PASS_CONDITIONED="
          f"{pv.ENABLE_SECOND_PASS_CONDITIONED}", flush=True)
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    filas = []
    for x in sel:
        try:
            fila = correr(vols[x["volcan"]], x["pasada_utc"], x["sensor"], x.get("clase", ""), x.get("nota", ""))
        except Exception as e:
            fila = {"volcan": x["volcan"], "pasada_utc": x["pasada_utc"], "sensor": x["sensor"],
                    "ok": False, "error": repr(e), "traceback": traceback.format_exc()}
            print(f"    FALLO: {e}", flush=True)
        filas.append(fila)
        dt = datetime.strptime(x["pasada_utc"], "%Y-%m-%d %H:%M")
        (OUT / f"{x['volcan']}_{dt:%Y-%m-%d_%H%M}_{x['sensor']}.json").write_text(
            json.dumps(a_json(fila), indent=1, ensure_ascii=False), encoding="utf-8")
        for p in DEST.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
    (OUT / "resumen.json").write_text(json.dumps(a_json(filas), indent=1, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for f in filas if f.get("ok"))
    print(f"\n{ok}/{len(filas)} pasadas procesadas. Salida en {OUT}", flush=True)


if __name__ == "__main__":
    main()
