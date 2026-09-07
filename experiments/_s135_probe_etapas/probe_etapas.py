"""S135 — probe A75 por etapa del ensamblado VIIRS 375 m (D19; AUDIT_S134 §D, D1-b).

QUÉ MIDE. `keep_peak` (`pipeline/process_viirs.py:1777-1786`) reduce el footprint del
Test 1 a un solo píxel, `argmax(BT)`, y ese píxel se publica como summit «a 0,0 km».
Lo que ningún JSON persiste es el footprint ANTES del recorte. Este probe lo captura:
cuántos píxeles del cráter había en `mask_contributing`, dónde cayó el pico, qué quedaba
en (Test 1 ∩ dNTI_ctx) sin el pico, y el perfil BT-vs-distancia por octante (A70) que
distingue «borde del disco = cota baja» de «valle de un lado». Y para H2, los
`newly_active` del second pass cuando el first pass quedó vacío.

CÓMO (A75, read-only). Monkeypatch de las funciones en el NAMESPACE de
`pipeline.process_viirs` (importa por nombre; parchear el módulo origen no cambia nada —
trampa A89). No edita ningún módulo, no escribe en `data/`, no hace `git push`.
Diseño: `experiments/_s134_audit/f3/probe_etapas_ci.md`. Plantilla: probe S110
(`experiments/_s110_ndc_probe/probe_ndc_assembly.py`).

DÓNDE. Sólo en GitHub Actions (`.github/workflows/probe-s135-etapas.yml`): los granules
no se bajan al PC (disco al 100 %) y las credenciales válidas viven en los secrets (A71).

Env opcionales: PROBE_VOL (Villarrica|Lascar), PROBE_FECHA (YYYY-MM-DD) para filtrar.
Salida: `experiments/_s135_probe_etapas/out/<vol>_<fecha>_<hhmm>.json` + `report.txt`
+ `criterio.json`.
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
import pipeline.process_viirs as pv  # noqa: E402
from run_pipeline import load_volcanoes  # noqa: E402  (aplica VOLCANO_OVERRIDES del perfil)

from analisis import a_json, evaluar_criterio, resumir_pasada  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
DEST = HERE / "granules"

# Las 6 pasadas de `experiments/_s134_audit/f3/tabla_6_pasadas.json`.
PASADAS = [
    ("Villarrica", "2026-07-01 05:00", "VIIRS_NOAA20", "nevado"),
    ("Villarrica", "2026-08-14 04:42", "VIIRS_NOAA20", "nevado"),
    ("Villarrica", "2026-08-31 05:06", "VIIRS_NOAA21", "nevado"),
    ("Lascar", "2026-06-17 05:42", "VIIRS_SNPP", "control"),
    ("Lascar", "2026-07-09 05:48", "VIIRS_NOAA20", "control"),
    ("Lascar", "2026-07-10 05:30", "VIIRS_NOAA20", "control"),
]
PRODUCTOS = {
    "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
    "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
    "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
}
# Nombres que el probe parchea EN `pipeline.process_viirs`. El test
# `tests/test_probe_etapas_s135.py` verifica que existan ahí (A89).
PATCH_NAMES = ("compute_test1_mir", "apply_contextual_test1_filter",
               "first_pass_tests_2_and_3", "second_pass_adjacent", "cluster_hotspots")

_CAP = {}
_REAL = {n: getattr(pv, n) for n in PATCH_NAMES}


def _wrap_test1(*a, **kw):
    res = _REAL["compute_test1_mir"](*a, **kw)
    _CAP["test1"] = {
        "bt": np.array(kw["bt"], dtype=float),
        "lat": np.array(kw["lat"], dtype=float),
        "lon": np.array(kw["lon"], dtype=float),
        "mask_contributing": np.array(res.get("mask_contributing"), dtype=bool)
        if res.get("mask_contributing") is not None else np.zeros_like(kw["bt"], dtype=bool),
        "triggered": bool(res.get("triggered")),
        "n_contributing": res.get("n_contributing"),
        "k_sigma_observed": res.get("k_sigma_observed"),
        "roi_km": kw.get("roi_km"),
        "vent_lat": kw.get("vent_lat"), "vent_lon": kw.get("vent_lon"),
    }
    return res


def _wrap_ctx(test1_mask, dnti_ctx_mask, keep_peak_rc=None):
    out = _REAL["apply_contextual_test1_filter"](test1_mask, dnti_ctx_mask,
                                                 keep_peak_rc=keep_peak_rc)
    _CAP["ctx_filter"] = {
        "mask_in": np.array(test1_mask, dtype=bool),
        "dnti_ctx": (np.array(dnti_ctx_mask, dtype=bool) if dnti_ctx_mask is not None else None),
        "keep_peak_rc": (tuple(int(x) for x in keep_peak_rc) if keep_peak_rc is not None else None),
        "mask_out": np.array(out, dtype=bool),
    }
    return out


def _wrap_fp(*a, **kw):
    hot, diag = _REAL["first_pass_tests_2_and_3"](*a, **kw)
    d = {}
    for k, v in (diag or {}).items():
        if isinstance(v, (int, float, np.integer, np.floating, bool, np.bool_)):
            d[k] = v
    _CAP["first_pass"] = {"hot": np.array(hot, dtype=bool),
                          "dist_km": np.array(kw["dist_km"], dtype=float),
                          "t_bg": kw.get("t_bg"), "diag": d}
    return hot, diag


def _wrap_sp(*a, **kw):
    out = _REAL["second_pass_adjacent"](*a, **kw)
    active = kw.get("active_mask", a[2] if len(a) > 2 else None)
    _CAP.setdefault("second_pass", []).append({
        "active_in": np.array(active, dtype=bool), "out": np.array(out, dtype=bool)})
    return out


def _wrap_cl(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
    cl = _REAL["cluster_hotspots"](hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
    _CAP.setdefault("clusters", []).append({
        "n_in": int(np.asarray(hot_mask_2d, dtype=bool).sum()),
        "strategy": kw.get("strategy"), "inner_radius_km": kw.get("inner_radius_km"),
        "connectivity": kw.get("connectivity"),
        "clusters": [{k: v for k, v in c.items() if k != "pixel_indices"} for c in cl],
    })
    return cl


pv.compute_test1_mir = _wrap_test1
pv.apply_contextual_test1_filter = _wrap_ctx
pv.first_pass_tests_2_and_3 = _wrap_fp
pv.second_pass_adjacent = _wrap_sp
pv.cluster_hotspots = _wrap_cl


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def stamp_de(pasada_utc):
    dt = datetime.strptime(pasada_utc, "%Y-%m-%d %H:%M")
    return dt, f"A{dt.year}{dt.timetuple().tm_yday:03d}.{dt:%H%M}"


def bajar_par(vol, platform, dt, stamp):
    """Busca y baja el L1B y el GEO de esa pasada exacta. Devuelve (l1b, geo) o None."""
    l1b_key, geo_key = PRODUCTOS[platform]
    paths = {}
    for key in (l1b_key, geo_key):
        grs = search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt)
        sel = [g for g in grs if stamp in gname(g)]
        print(f"    {key}: {len(grs)} granules del día, {len(sel)} con {stamp}", flush=True)
        if not sel:
            return None
        got = download_granules(sel, DEST)
        got = [p for p in got if stamp in Path(p).name]
        if not got:
            return None
        paths[key] = Path(got[0])
    return paths[l1b_key], paths[geo_key]


def correr_pasada(vol, pasada_utc, platform, clase):
    dt, stamp = stamp_de(pasada_utc)
    print(f"=== {clase} {vol['name']} {pasada_utc} {platform} ({stamp}) ===", flush=True)
    fila = {"volcan": vol["name"], "pasada_utc": pasada_utc, "sensor": platform,
            "clase": clase, "stamp": stamp, "ok": False}
    par = bajar_par(vol, platform, dt, stamp)
    if par is None:
        fila["error"] = "granule no encontrado o no descargado"
        print("    " + fila["error"], flush=True)
        return fila
    l1b, geo = par
    fila["l1b"], fila["geo"] = l1b.name, geo.name
    ancla_lat, ancla_lon = get_detection_anchor(vol)
    _CAP.clear()
    try:
        rec = pv.calculate_vrp(
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
    except Exception as e:
        fila["error"] = f"calculate_vrp: {e}"
        fila["traceback"] = traceback.format_exc()
        print("    " + fila["error"], flush=True)
        return fila
    if rec is None:
        fila["error"] = "calculate_vrp devolvió None (granule no cubre el volcán)"
        print("    " + fila["error"], flush=True)
        return fila

    claves = ("sensor", "datetime", "vrp_mw", "vrp_mir_mw", "t_bg_k", "t_max_i04_k",
              "n_anomalous_pixels", "final_hotspot_source", "final_hotspot_dist_km",
              "final_hotspot_lat", "final_hotspot_lon", "distance_class", "primary_cluster",
              "triggered_test1", "test1_k_observed", "diag_n_first_pass_pixels", "nti_max",
              "single_pixel_mode")
    fila["record"] = {k: rec.get(k) for k in claves if k in rec}
    t_bg = rec.get("t_bg_k")
    fila["vent"] = {"vent_lat": vol.get("vent_lat"), "vent_lon": vol.get("vent_lon"),
                    "ancla_lat": ancla_lat, "ancla_lon": ancla_lon,
                    "catalogo_lat": vol["lat"], "catalogo_lon": vol["lon"]}
    vlat = vol.get("vent_lat", ancla_lat)
    vlon = vol.get("vent_lon", ancla_lon)
    fila["resumen"] = resumir_pasada(_CAP, vlat, vlon, ancla_lat, ancla_lon, t_bg)
    fila["ok"] = True

    r = fila["resumen"]
    t1 = r["test1"]
    kp = r.get("keep_peak")
    print(f"    record: source={rec.get('final_hotspot_source')} d_final={rec.get('final_hotspot_dist_km')} "
          f"vrp={rec.get('vrp_mw')} t_bg={t_bg} n_first_pass={rec.get('diag_n_first_pass_pixels')}", flush=True)
    if t1.get("corrio"):
        print(f"    Test1: triggered={t1['triggered']} n_mask={t1['n_contributing']} "
              f"(disco {t1['n_en_disco']} px) | en cráter <0,5 km: {t1['n_mask_a_menos_0_5km']} "
              f"| <1 km: {t1['n_mask_a_menos_1km']} | rango BT del cráter en la máscara: "
              f"{t1['rango_bt_crater_en_mask']}", flush=True)
        pc = t1.get("pixel_mas_cercano_al_vent")
        if pc:
            print(f"    píxel más cercano al vent: {pc['dist_vent_km']} km, BT {pc['bt_k']} K "
                  f"({pc['bt_menos_t_bg_global_k']} K vs fondo global), en mask={pc['en_mask_contributing']}",
                  flush=True)
    else:
        print("    Test1 NO corrió", flush=True)
    if kp:
        print(f"    keep_peak: {kp['dist_vent_km']} km del vent ({kp['octante']}), BT {kp['bt_k']} K "
              f"({kp['bt_menos_t_bg_global_k']} K vs fondo global), argmax del disco={kp['es_argmax_del_disco']}",
              flush=True)
        it = r["interseccion_sin_pico"]
        print(f"    (Test1 ∩ dNTI_ctx) sin pico: {it['n']} px (dNTI_ctx total {it['n_dnti_ctx_total']}); "
              f"salida del filtro: {it['n_mask_out']} px", flush=True)
    else:
        print("    keep_peak no aplicó (filtro contextual no corrió)", flush=True)
    for i, sp in enumerate(r.get("second_pass", [])):
        print(f"    second_pass[{i}]: active_in={sp['n_active_in']} newly={sp['n_newly_active']} "
              f"bajo compuerta 3 K={sp['n_newly_bajo_compuerta_3k']}", flush=True)
    perfil = r.get("perfil_bt") or []
    if perfil:
        print("    perfil BT mediana por anillo (km→K): " + " ".join(
            f"{f['hasta_km']:.2f}:{f['bt_mediana']:.1f}" for f in perfil if f["bt_mediana"] is not None),
            flush=True)
    return fila


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    f_fecha = os.environ.get("PROBE_FECHA", "").strip()
    sel = [p for p in PASADAS
           if (not f_vol or p[0] == f_vol) and (not f_fecha or p[1].startswith(f_fecha))]
    print(f"Probe S135 etapas — {len(sel)} pasadas (perfil {os.environ['VRP_PROFILE']})\n", flush=True)
    print("flags efectivos:", {k: getattr(pv, k, None) for k in (
        "ENABLE_TEST1_CONTEXTUAL_FILTER", "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK",
        "ENABLE_TEST1_PRIORITY_WEAK_CLUSTER", "ENABLE_HONEST_ANCHOR", "TEST1_ROI_KM",
        "ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375")}, "\n", flush=True)
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    filas = []
    for vol_name, pasada_utc, platform, clase in sel:
        vol = vols[vol_name]
        try:
            fila = correr_pasada(vol, pasada_utc, platform, clase)
        except Exception as e:
            fila = {"volcan": vol_name, "pasada_utc": pasada_utc, "sensor": platform,
                    "clase": clase, "ok": False, "error": f"{e}", "traceback": traceback.format_exc()}
            print(f"    FALLO: {e}", flush=True)
        filas.append(fila)
        dt, _ = stamp_de(pasada_utc)
        (OUT / f"{vol_name}_{dt:%Y-%m-%d_%H%M}.json").write_text(
            json.dumps(a_json(fila), indent=1, ensure_ascii=False), encoding="utf-8")
        print("", flush=True)
        # Liberar disco del runner entre pasadas.
        for p in DEST.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass

    crit = evaluar_criterio(filas)
    (OUT / "criterio.json").write_text(json.dumps(a_json(crit), indent=1, ensure_ascii=False),
                                       encoding="utf-8")
    print("=" * 70, flush=True)
    print("CRITERIO PRE-REGISTRADO (probe_etapas_ci.md)", flush=True)
    print(f"  H1 keep_peak: {crit['h1']}  [nevado {crit['n_nevado_confirman']} · control {crit['n_control_ok']}]",
          flush=True)
    print(f"  H2 second pass: {crit['h2']}", flush=True)
    for d in crit["detalle"]:
        print(f"    {d['volcan']} {d.get('pasada_utc')} [{d['clase']}] → {d.get('h1')} "
              f"(cráter en mask: {d.get('n_crater')}, pico a {d.get('keep_peak_dist_vent_km')} km, "
              f"first pass {d.get('n_first_pass')})", flush=True)


if __name__ == "__main__":
    main()
