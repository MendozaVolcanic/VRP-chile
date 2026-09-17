# -*- coding: utf-8 -*-
"""S143: probe de las 12 noches perdidas por el A/B S135, con seis variantes (A75, sólo lectura, sólo CI).

POR QUÉ. En un cono nevado, de noche, el cráter con un foco débil está más frío que el valle. El A/B
S135 quitó `keep_peak` y condicionó el segundo pase, y perdió 12 noches que MIROVA publica: el Test 1
encontraba la señal, pero sus píxeles se cruzan con la máscara contextual (camino D), y esa máscara
exige `bt > t_bg + 3 K`. Los brazos del A/B S143 quitan esa compuerta sólo en el primer pase, no en la
máscara. Este probe mide, sobre las mismas pasadas, qué recupera las noches y qué cuesta en pasadas
donde MIROVA no vio nada, antes de gastar ~160 horas de runner.

VARIANTES (una por proceso; el perfil se fija ANTES de importar el pipeline):
  control                      _s142_ab_control (producción de hoy)
  s135_d                       _s135_ab_d_ambos (control de instrumento: debe reproducir la pérdida)
  s135_d_sin_compuerta_ctx     s135_d + máscara contextual sin compuerta
  literal                      _s142_ab_literal (D22 primer pase, D25, D2, sin keep_peak)
  literal_sin_compuerta_ctx    literal + máscara contextual sin compuerta (D22 en todas partes)
  literal_t1_sin_filtro        literal + Test 1 como camino propio (sin filtro contextual; D23)

CÓMO. Los parches van en el NAMESPACE de `pipeline.process_viirs` (A89): la máscara contextual se
envuelve forzando `apply_bt_gate=False` (parámetro existente, `detection_context.py:221` y `:345`), y
el filtro del Test 1 se apaga con `pv.ENABLE_TEST1_CONTEXTUAL_FILTER = False`, que sólo lee
`process_viirs.py` (verificado con grep). Cada salida guarda los flags efectivos y cuántas veces se
llamó cada envoltorio, para comprobar que la variante hizo lo que declara.
No escribe en data/, no hace push.

Env: PROBE_VARIANTE (obligatorio), PROBE_VOL (filtra volcán), PROBE_PASADAS (ruta a pasadas.json).
Salida: out/<variante>/<volcan>_<fecha>_<hhmm>_<sensor>.json
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

VARIANTES = {
    "control": ("_s142_ab_control", False, True),
    "s135_d": ("_s135_ab_d_ambos", False, True),
    "s135_d_sin_compuerta_ctx": ("_s135_ab_d_ambos", True, True),
    "literal": ("_s142_ab_literal", False, True),
    "literal_sin_compuerta_ctx": ("_s142_ab_literal", True, True),
    "literal_t1_sin_filtro": ("_s142_ab_literal", False, False),
}  # nombre: (perfil, quitar compuerta en la máscara contextual, filtro contextual del Test 1)

VARIANTE = os.environ.get("PROBE_VARIANTE", "").strip()
if VARIANTE not in VARIANTES:
    raise SystemExit(f"PROBE_VARIANTE debe ser una de {sorted(VARIANTES)}; llegó {VARIANTE!r}")
PERFIL, SIN_COMPUERTA_CTX, FILTRO_T1 = VARIANTES[VARIANTE]
os.environ["VRP_PROFILE"] = PERFIL  # ANTES de importar el pipeline

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")  # una sola vez, aquí (S141)
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import pipeline.process_viirs as pv  # noqa: E402
import pipeline.store as store  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from run_pipeline import VOLCANIC_FEATURES, load_volcanoes, vrp_profile  # noqa: E402

# El predicado del dashboard lee campos que NO existen en el record crudo de `calculate_vrp`
# (`vrp_mw` unificado, `discarded_reason`, `f5_core_vrp_mw`): los agrega `store.append_record`, que en
# producción corre siempre después. Acá se llama igual, con los mismos argumentos que
# `scripts/run_pipeline.py:247-254`, pero con la escritura a disco anulada: el probe es sólo lectura.
store._save = lambda *a, **kw: None

PRODUCTOS = {
    "VIIRS_SNPP": ("VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
    "VIIRS_NOAA20": ("VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
    "VIIRS_NOAA21": ("VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO"),
}
CAMPOS = ("sensor", "datetime", "datetime_utc", "vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "t_bg_k", "t_max_k",
          "t_max_i04_k", "n_anomalous_pixels", "final_hotspot_source", "final_hotspot_dist_km",
          "final_hotspot_lat", "final_hotspot_lon", "distance_class", "discarded_reason", "primary_cluster",
          "triggered_test1", "test1_k_observed", "diag_n_first_pass_pixels", "nti_max", "single_pixel_mode",
          "f5_core_vrp_mw", "diag_bg_vecinos_n_sin_vecinos", "diag_L_bg_vecinos_w_m2_sr_um",
          "diag_n_dnti_ctx_path", "n_dnti_ctx_path", "hotspot_dist_km", "product_version",
          "discarded_reason")
DEST = HERE / "granules"
OUT = HERE / "out" / VARIANTE
LLAMADAS = {"ctx_sin_compuerta": 0, "filtro_t1": 0, "filtro_t1_px_entra": 0, "filtro_t1_px_sale": 0}

_filtro_real = pv.apply_contextual_test1_filter


def _filtro_contado(test1_mask, dnti_ctx_mask, keep_peak_rc=None):
    """Envoltorio de sólo lectura: sin él no se puede saber si el filtro corrió (hallazgo 1 del
    verificador: `only_test1_source` decide si se aplica y esa variable no se persiste)."""
    out = _filtro_real(test1_mask, dnti_ctx_mask, keep_peak_rc=keep_peak_rc)
    LLAMADAS["filtro_t1"] += 1
    LLAMADAS["filtro_t1_px_entra"] += int(test1_mask.sum())
    LLAMADAS["filtro_t1_px_sale"] += int(out.sum())
    return out


pv.apply_contextual_test1_filter = _filtro_contado

if SIN_COMPUERTA_CTX:
    _dual_real, _ctx_real = pv.dual_roi_contextual_dnti_hot_mask, pv.contextual_dnti_hot_mask

    def _dual_sin_compuerta(*a, **kw):
        LLAMADAS["ctx_sin_compuerta"] += 1
        kw["apply_bt_gate"] = False
        return _dual_real(*a, **kw)

    def _ctx_sin_compuerta(*a, **kw):
        LLAMADAS["ctx_sin_compuerta"] += 1
        kw["apply_bt_gate"] = False
        return _ctx_real(*a, **kw)

    pv.dual_roi_contextual_dnti_hot_mask = _dual_sin_compuerta
    pv.contextual_dnti_hot_mask = _ctx_sin_compuerta
if not FILTRO_T1:
    pv.ENABLE_TEST1_CONTEXTUAL_FILTER = False


def flags_efectivos():
    return {k: getattr(pv, k, None) for k in (
        "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375",
        "ENABLE_SECOND_PASS_ADJACENT", "ENABLE_SECOND_PASS_CONDITIONED", "ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK", "ENABLE_TEST1_CONTEXTUAL_FILTER",
        "ENABLE_DNTI_DUAL_ROI", "NTI_BT_SANITY_K")} | {"perfil": PERFIL, "variante": VARIANTE,
                                                     "sin_compuerta_ctx": SIN_COMPUERTA_CTX}


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def bajar_par(vol, platform, dt, stamp):
    """L1B y GEO de la pasada exacta. Reusa lo ya bajado por otra variante (mismo directorio)."""
    paths = {}
    for key in PRODUCTOS[platform]:
        ya = sorted(p for p in DEST.glob(f"*{stamp}*") if p.is_file() and key.split("_")[-1] in _tipo(p.name))
        if ya:
            paths[key] = ya[0]
            continue
        grs = [g for g in search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt) if stamp in gname(g)]
        if not grs:
            return None
        got = [Path(p) for p in download_granules(grs, DEST) if stamp in Path(p).name]
        if not got:
            return None
        paths[key] = got[0]
    return tuple(paths[k] for k in PRODUCTOS[platform])


def _tipo(nombre):
    """'L1B' para VNP02IMG/VJ102IMG/VJ202IMG, 'GEO' para VNP03IMG/VJ103IMG/VJ203IMG."""
    n = nombre.upper()
    return "GEO" if ("03IMG" in n) else ("L1B" if "02IMG" in n else "")


def main():
    lista = json.loads(Path(os.environ.get("PROBE_PASADAS", "").strip() or HERE / "pasadas.json").read_text(encoding="utf-8"))
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    lista = [x for x in lista if not f_vol or x["volcan"] == f_vol]
    fe = flags_efectivos()
    print(f"variante {VARIANTE}: {len(lista)} pasadas | flags {fe}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    auth()
    vols = {v["name"]: v for v in load_volcanoes()}
    n_ok = 0
    for x in lista:
        vol = vols[x["volcan"]]
        dt = datetime.strptime(x["pasada_utc"], "%Y-%m-%d %H:%M")
        stamp = f"A{dt.year}{dt.timetuple().tm_yday:03d}.{dt:%H%M}"
        fila = {**x, "stamp": stamp, "ok": False, "flags": fe}
        for k in LLAMADAS:
            LLAMADAS[k] = 0
        try:
            par = bajar_par(vol, x["sensor"], dt, stamp)
            if par is None:
                fila["error"] = "granule no encontrado o no descargado"
            else:
                ancla_lat, ancla_lon = get_detection_anchor(vol)
                rec = pv.calculate_vrp(
                    par[0], par[1], vol["lat"], vol["lon"], vol["radius_km"],
                    vent_lat=ancla_lat, vent_lon=ancla_lon,
                    vent_radius_km=vol.get("vent_radius_km", 4.0),
                    inner_radius_km=vol.get("inner_radius_km"),
                    exclude_zones=vol.get("exclude_zones"),
                    active_water_bodies=vol.get("active_water_bodies"),
                    lbg_global_compatible=vol.get("lbg_global_compatible", False),
                    local_kernel_bg_compatible=vol.get("local_kernel_bg", False),
                    lava_lake_magmatic=vol.get("lava_lake_magmatic", False),
                )
                if rec is None:
                    fila["error"] = "calculate_vrp devolvió None"
                else:
                    store.append_record(
                        vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"],
                        overwrite=True, max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"),
                        inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=VOLCANIC_FEATURES.get(vol["name"]))
                    fila["record"] = {k: rec.get(k) for k in CAMPOS if k in rec}
                    fila["record"]["anomaly_pixels"] = [
                        {k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k", "dist_km")}
                        for q in (rec.get("anomaly_pixels") or [])]
                    fila["granules"] = [par[0].name, par[1].name]
                    fila["llamadas"] = dict(LLAMADAS)
                    fila["llamadas_ctx_sin_compuerta"] = LLAMADAS["ctx_sin_compuerta"]
                    fila["ok"] = True
                    n_ok += 1
        except Exception as e:
            fila["error"] = str(e)
            fila["traceback"] = traceback.format_exc()
        r = fila.get("record") or {}
        pc = r.get("primary_cluster") or {}
        print(f"  {x['clase']:13s} {x['volcan']} {x['pasada_utc']} {x['sensor']}: ok={fila['ok']} "
              f"fuente={r.get('final_hotspot_source')} clase={r.get('distance_class')} pc_vrp={pc.get('vrp_mw')} "
              f"f5={r.get('f5_core_vrp_mw')} n_fp={r.get('diag_n_first_pass_pixels')} "
              f"vrp={r.get('vrp_mw')} ctx_path={r.get('diag_n_dnti_ctx_path')} "
              f"llamadas={fila.get('llamadas')} err={fila.get('error')}", flush=True)
        nombre = f"{x['volcan']}_{x['pasada_utc'].replace(' ', '_').replace(':', '')}_{x['sensor']}.json"
        (OUT / nombre).write_text(json.dumps(fila, indent=1, ensure_ascii=False, default=_a_json), encoding="utf-8")
    print(f"variante {VARIANTE}: {n_ok} de {len(lista)} pasadas procesadas", flush=True)
    if n_ok < len(lista):
        sys.exit(2)  # un job verde sin datos no se lee como resultado (S141)


def _a_json(o):
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:
        pass
    return str(o)


if __name__ == "__main__":
    main()
