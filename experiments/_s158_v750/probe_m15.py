# -*- coding: utf-8 -*-
"""S158: probe de solo lectura de M15 en sentinela junto al crater, VIIRS 750, detector K. ESCRITO ANTES DE CORRER.

POR QUE. Para alertar, un pixel de VIIRS 750 necesita su NTI, que se arma con M13 (MIR, 4,05 um) y M15 (TIR,
10,76 um). Si el lector deja M15 en NaN, ese pixel no tiene NTI y no puede pasar los Tests 2 y 3 aunque su M13 este
sano y caliente. El probe de #880 encontro, sin verificar, 44 de 156 pixeles de una ventana de Chillan con M15 en
sentinela (DN 65532 a 65535) y M13 sano. El lector (`pipeline/process_viirs_mod.read_viirs_mod_l1b`) pone en NaN los
sentinelas, el bit de saturacion (mascara 4) y toda BT de M15 de 342,5 K o mas. Si eso le pasa al pixel del foco, la
alerta se pierde por el lector y no por la fisica. Y hay una explicacion inocente posible, que tambien se mide: el
UserGuide (seccion 2.3) dice que el borrado del bowtie es a bordo para las bandas M de ganancia simple (M15) y que la
agregacion de las de doble ganancia (M13) se hace en tierra; si M13 conserva el pixel duplicado del bowtie y M15 no,
ese terreno lo ve el barrido vecino y no se pierde nada.

QUE HACE, por pasada de `pasadas.json` (grupo P: alertas de MIROVA que K no publica; grupo C: positivas publicadas
pareadas, control de tasa base):
  1. Baja L1B y GEO de VIIRS M-band por nombre exacto del record (pipeline.fetch, autenticacion solo por
     EARTHDATA_TOKEN, A71).
  2. Lee el L1B CRUDO (DN, quality flags) y la BT tal como la deja el lector del pipeline.
  3. Ventana: pixeles a <= inner_radius_km del ancla de deteccion (get_detection_anchor), la del clasificador summit.
  4. Cuenta en la ventana: sentinelas de M15 y M13 por codigo, mascaras 4 (Saturation), 256 (Bowtie_Deleted) y 2048
     (Dead_Detector) de M15, BT cruda de M15 >= 342,5 K, y `nti_perdido` = M13 valido y M15 NaN segun el lector.
     Ademas: si el pixel de M13 mas caliente de la ventana (y los 3 mas calientes) tiene `nti_perdido`.
  5. Cobertura: para cada pixel `nti_perdido`, distancia al pixel mas cercano con M13 y M15 validos. Lo compara con el
     espaciado tipico entre pixeles validos (mediana de la distancia al vecino valido mas cercano en la ventana).
  6. Dos corridas del procesador de produccion (K, perfil mirova_equivalent, sin tocar flags):
       control  tal cual;
       relleno  los pixeles `nti_perdido` reciben en M15 la media de sus vecinos 3x3 con M15 valido (si no hay
                ninguno, quedan NaN). Es el contrafactual: "si el lector no hubiera borrado ese M15".
     Cada record pasa por store.append_record (sin escribir nada) y por el predicado del tablero con node.

CONTROLES (fijados antes de correr):
  C-SIN  `prueba_probe_m15.py`: contador y relleno sobre arreglos sinteticos; mutaciones atrapadas por asercion.
  C-P1   el control reproduce el record persistido (n_anomalous_pixels, distance_class, pc.vrp_mw a 1e-3 MW). Si
         falla, la pasada se informa y no se interpreta.
  C-NULO en toda pasada sin ningun `nti_perdido` en la escena entera, relleno == control exacto (el brazo no puede
         cambiar nada donde no hay nada que rellenar).

Uso (Actions):  python probe_m15.py --parte 0 --partes 4 --out out
Sale 2 si alguna pasada falla (S141).
"""
from __future__ import annotations

import argparse
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
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")   # antes de importar el pipeline: produccion = K
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402

FLAG_DNS = (65532, 65533, 65534, 65535)
M_SAT, M_BOWTIE, M_DEAD = 4, 256, 2048
TECHO_M15_K = 343.0 - 0.5   # process_viirs_mod.BT_LUT_MAX_MBAND["M15"] - 0,5 (aplicar_techo_saturacion_mband)
PRODUCTO = {"VIIRS_SNPP_750": ("VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
            "VIIRS_NOAA20_750": ("VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
            "VIIRS_NOAA21_750": ("VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO")}


# ---------------------------------------------------------------------------------------------------------------
# Funciones puras (las prueba prueba_probe_m15.py)
# ---------------------------------------------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(np.asarray(lon2) - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def contar(dn13, dn15, qf15, bt13_pipe, bt15_pipe, bt15_cruda, ventana):
    """Conteos en la ventana. `nti_perdido` = M13 valido y M15 NaN segun el lector del pipeline."""
    perdido = np.isfinite(bt13_pipe) & ~np.isfinite(bt15_pipe)
    w = ventana
    qf = qf15 if qf15 is not None else np.zeros_like(dn15)
    out = {"n": int(w.sum()),
           "m13_valido": int(np.isfinite(bt13_pipe)[w].sum()),
           "m15_valido": int(np.isfinite(bt15_pipe)[w].sum()),
           "nti_perdido": int(perdido[w].sum()),
           "m15_sentinela": {str(c): int((dn15[w] == c).sum()) for c in FLAG_DNS if int((dn15[w] == c).sum())},
           "m13_sentinela": {str(c): int((dn13[w] == c).sum()) for c in FLAG_DNS if int((dn13[w] == c).sum())},
           "nti_perdido_por_codigo_m15": {str(c): int((perdido & (dn15 == c))[w].sum()) for c in FLAG_DNS
                                          if int((perdido & (dn15 == c))[w].sum())},
           "m15_mask4_sat": int(((qf & M_SAT) != 0)[w].sum()),
           "m15_mask256_bowtie": int(((qf & M_BOWTIE) != 0)[w].sum()),
           "m15_mask2048_dead": int(((qf & M_DEAD) != 0)[w].sum()),
           "m15_sobre_techo": int((np.isfinite(bt15_cruda) & (bt15_cruda >= TECHO_M15_K))[w].sum())}
    otros = perdido & ~np.isin(dn15, FLAG_DNS)
    out["nti_perdido_sin_sentinela"] = int(otros[w].sum())   # saturacion, techo u otra causa
    # pixel de M13 mas caliente de la ventana y los tres mas calientes
    idx = np.flatnonzero(w & np.isfinite(bt13_pipe))
    if idx.size:
        orden = idx[np.argsort(bt13_pipe.ravel()[idx])[::-1]]
        out["m13_max_k"] = float(bt13_pipe.ravel()[orden[0]])
        out["max_m13_nti_perdido"] = bool(perdido.ravel()[orden[0]])
        out["top3_m13_nti_perdido"] = int(perdido.ravel()[orden[:3]].sum())
    return out, perdido


def rellenar_m15(bt15_pipe, perdido):
    """Copia de M15 con los pixeles `perdido` rellenos con la media de sus vecinos 3x3 con M15 valido."""
    out = bt15_pipe.astype(np.float64).copy()
    filas, cols = np.nonzero(perdido)
    H, W = out.shape
    n = 0
    for i, j in zip(filas, cols):
        bloque = bt15_pipe[max(i - 1, 0):min(i + 2, H), max(j - 1, 0):min(j + 2, W)]
        v = bloque[np.isfinite(bloque)]
        if v.size:
            out[i, j] = float(v.mean())
            n += 1
    return out.astype(bt15_pipe.dtype), n


def cobertura(lat, lon, perdido, valido_ambas, ventana, radio_busqueda_km=3.0):
    """Distancia de cada pixel perdido de la ventana al pixel mas cercano con M13 y M15 validos."""
    ip = np.flatnonzero((perdido & ventana).ravel())
    if not ip.size:
        return {"n": 0}
    la, lo = lat.ravel(), lon.ravel()
    iv = np.flatnonzero(valido_ambas.ravel())
    lat0, lon0 = float(np.nanmean(la[ip])), float(np.nanmean(lo[ip]))
    cerca = iv[haversine_km(lat0, lon0, la[iv], lo[iv]) <= radio_busqueda_km + 10]
    d = [float(np.nanmin(haversine_km(la[k], lo[k], la[cerca], lo[cerca]))) if cerca.size else None for k in ip]
    # espaciado tipico entre validos de la ventana
    ivw = np.flatnonzero((valido_ambas & ventana).ravel())
    esp = []
    for k in ivw[:400]:
        dd = haversine_km(la[k], lo[k], la[ivw], lo[ivw])
        dd = dd[dd > 1e-6]
        if dd.size:
            esp.append(float(dd.min()))
    dv = [x for x in d if x is not None]
    return {"n": len(ip), "dist_km_mediana": float(np.median(dv)) if dv else None,
            "dist_km_max": float(np.max(dv)) if dv else None,
            "espaciado_validos_km_mediana": float(np.median(esp)) if esp else None,
            "dist_km": [round(x, 3) if x is not None else None for x in d]}


# ---------------------------------------------------------------------------------------------------------------
# Lectura cruda y corridas (solo en Actions)
# ---------------------------------------------------------------------------------------------------------------
def crudo(l1b):
    import h5py
    with h5py.File(l1b, "r") as f:
        obs = f["observation_data"]
        dn13 = obs["M13"][:].astype(np.int64)
        dn15 = obs["M15"][:].astype(np.int64)
        qf15 = obs["M15_quality_flags"][:].astype(np.int64) if "M15_quality_flags" in obs else None
        lut15 = np.asarray(obs["M15_brightness_temperature_lut"][:], dtype=np.float64)
        bt15 = lut15[np.clip(dn15, 0, len(lut15) - 1)]
        bt15 = np.where(np.isin(dn15, FLAG_DNS) | (bt15 <= 0), np.nan, bt15)
        attrs = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in obs["M15_quality_flags"].attrs.items()} \
            if "M15_quality_flags" in obs else {}
    attrs = {k: ([x.decode() if isinstance(x, bytes) else x for x in v] if isinstance(v, list)
                 else (v.decode() if isinstance(v, bytes) else v)) for k, v in attrs.items()}
    return dn13, dn15, qf15, bt15, attrs


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g.get("umm", {}).get("GranuleUR", g))[:160]


def bajar(vol, sensor, nombre, dest):
    from pipeline.fetch import download_granules, search_granules
    stamp = ".".join(nombre.split(".")[1:3])
    dt = datetime.strptime(stamp[1:], "%Y%j.%H%M")
    out = []
    for key in PRODUCTO[sensor]:
        grs = [g for g in search_granules(key, vol["lat"], vol["lon"], vol["radius_km"], dt) if stamp in gname(g)]
        if key.endswith("_L1B"):
            grs = [g for g in grs if gname(g) == nombre] or grs
        if not grs:
            raise RuntimeError("sin granulo %s %s" % (key, stamp))
        got = [Path(p) for p in download_granules(grs[:1], dest) if stamp in Path(p).name]
        if not got:
            raise RuntimeError("descarga fallida %s %s" % (key, stamp))
        out.append(got[0])
    nota = None if out[0].name == nombre else "L1B distinto: %s en lugar de %s" % (out[0].name, nombre)
    return out[0], out[1], nota


CAMPOS = ("sensor", "datetime_utc", "granule", "vrp_mw", "vrp_vent_mw", "vrp_mir_mw", "t_bg_k", "t_max_k",
          "n_anomalous_pixels", "distance_class", "discarded_reason", "primary_cluster", "triggered_test1",
          "f5_core_vrp_mw", "anomaly_pixels", "final_hotspot_source", "diag_n_first_pass_pixels",
          "diag_n_second_pass_recapture", "nti_max")


def correr(mod, store, vrp_profile, vol, l1b, geo, features):
    from pipeline.geo_utils import get_detection_anchor
    lat, lon = get_detection_anchor(vol)
    rec = mod.calculate_vrp(l1b, geo, vol["lat"], vol["lon"], vol["radius_km"], vent_lat=lat, vent_lon=lon,
                            vent_radius_km=vol.get("vent_radius_km", 4.0), inner_radius_km=vol.get("inner_radius_km"),
                            exclude_zones=vol.get("exclude_zones"), active_water_bodies=vol.get("active_water_bodies"),
                            lbg_global_compatible=vol.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=vol.get("local_kernel_bg", False))
    if rec is None:
        return None
    store.append_record(vol["name"], rec, volcano_lat=vol["lat"], volcano_lon=vol["lon"], overwrite=True,
                        max_hotspot_dist_km=vol.get("radius_km"),
                        enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                        max_cluster_pixels=vol.get("max_cluster_pixels"), inner_radius_km=vol.get("inner_radius_km"),
                        volcanic_features=features)
    return {k: rec.get(k) for k in CAMPOS if k in rec}


def c_p1(pers, ctrl):
    if not ctrl:
        return False
    pp, pc = pers.get("pc_vrp"), ((ctrl.get("primary_cluster") or {}).get("vrp_mw"))
    mismo_pc = (pp is None and pc is None) or (pp is not None and pc is not None and abs(pp - pc) <= 1e-3)
    return bool(mismo_pc and (pers.get("n_anomalous_pixels") or 0) == (ctrl.get("n_anomalous_pixels") or 0)
                and pers.get("dc") == ctrl.get("distance_class"))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--parte", type=int, required=True)
    ap.add_argument("--partes", type=int, required=True)
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    import pipeline.process_viirs_mod as mod
    import pipeline.store as store
    from pipeline import profile as vrp_profile
    from pipeline.fetch import auth
    from run_pipeline import VOLCANIC_FEATURES, load_volcanoes
    store._save = lambda *x, **k: None   # solo lectura: nada se escribe en data/
    print("perfil %s | TEST1 %s | PROSE %s | D25_750 %s" % (os.environ["VRP_PROFILE"], vrp_profile.ENABLE_TEST1_PATH,
          vrp_profile.ENABLE_TESTS_23_PROSE_BRANCH, getattr(vrp_profile, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750", None)))
    if vrp_profile.ENABLE_TEST1_PATH or not vrp_profile.ENABLE_TESTS_23_PROSE_BRANCH:
        print("el perfil no es K: no se corre")
        return 2

    pasadas = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    por_gran = {}
    for p in pasadas:
        por_gran.setdefault(p["granule"], []).append(p)
    grans = sorted(por_gran)[a.parte::a.partes]
    vols = {v["name"]: v for v in load_volcanoes()}
    auth()
    dest = Path(os.environ.get("VRP_TMP_DIR", str(HERE / "_granulos")))
    lector_original = mod.read_viirs_mod_l1b
    faltan = 0
    resultados = []
    for g in grans:
        print("\n== %s (%d pasadas)" % (g, len(por_gran[g])), flush=True)
        try:
            l1b, geo, nota = bajar(vols[por_gran[g][0]["vol"]], por_gran[g][0]["sensor"], g, dest)
            dn13, dn15, qf15, bt15c, attrs = crudo(l1b)
            bandas = lector_original(l1b)
            geod = mod.read_viirs_mod_geo(geo)
            perdido_escena = np.isfinite(bandas["M13"]) & ~np.isfinite(bandas["M15"])
            for p in por_gran[g]:
                res = {"pasada": p, "nota_granulo": nota, "ok": False}
                try:
                    vol = vols[p["vol"]]
                    from pipeline.geo_utils import get_detection_anchor
                    alat, alon = get_detection_anchor(vol)
                    dist = haversine_km(alat, alon, geod["lat"], geod["lon"])
                    ventana = np.isfinite(dist) & (dist <= vol.get("inner_radius_km"))
                    conteo, perdido = contar(dn13, dn15, qf15, bandas["M13"], bandas["M15"], bt15c, ventana)
                    valido = np.isfinite(bandas["M13"]) & np.isfinite(bandas["M15"])
                    res["ventana"] = conteo
                    res["cobertura"] = cobertura(geod["lat"], geod["lon"], perdido, valido, ventana)
                    res["escena_nti_perdido"] = int(perdido_escena.sum())
                    res["qf_attrs_m15"] = attrs
                    sz = (geod.get("angles") or {}).get("sensor_zenith_deg")
                    if sz is not None and ventana.any():
                        res["cenit_ventana_mediana"] = float(np.nanmedian(sz[ventana]))
                    feats = VOLCANIC_FEATURES.get(vol["name"])
                    mod.read_viirs_mod_l1b = lector_original
                    res["control"] = correr(mod, store, vrp_profile, vol, l1b, geo, feats)
                    relleno, n_rell = rellenar_m15(bandas["M15"], perdido_escena)

                    def lector_relleno(path, _r=relleno):
                        b = lector_original(path)
                        b["M15"] = _r
                        return b
                    mod.read_viirs_mod_l1b = lector_relleno
                    res["relleno"] = correr(mod, store, vrp_profile, vol, l1b, geo, feats)
                    mod.read_viirs_mod_l1b = lector_original
                    res["n_rellenados_escena"] = n_rell
                    res["C_P1"] = c_p1(p, res["control"])
                    if res["escena_nti_perdido"] == 0:
                        res["C_NULO"] = json.dumps(res["control"], sort_keys=True, default=str) == \
                            json.dumps(res["relleno"], sort_keys=True, default=str)
                    res["ok"] = True
                    pcc = ((res["control"] or {}).get("primary_cluster") or {})
                    pcr = ((res["relleno"] or {}).get("primary_cluster") or {})
                    print("   %s %s %s | ventana n %d nti_perdido %d (%s) max_m13_perdido %s | C-P1 %s | "
                          "pc control %s relleno %s" % (p["grupo"], p["vol"], p["dt"], conteo["n"], conteo["nti_perdido"],
                                                       conteo["nti_perdido_por_codigo_m15"], conteo.get("max_m13_nti_perdido"),
                                                       res["C_P1"], pcc.get("vrp_mw"), pcr.get("vrp_mw")), flush=True)
                except Exception as e:  # noqa: BLE001
                    mod.read_viirs_mod_l1b = lector_original
                    res["error"] = "%s: %s" % (type(e).__name__, e)
                    res["traceback"] = traceback.format_exc()
                    print("   ERROR", res["error"], flush=True)
                    faltan += 1
                resultados.append(res)
        except Exception as e:  # noqa: BLE001
            print("   ERROR granulo", type(e).__name__, e, flush=True)
            for p in por_gran[g]:
                resultados.append({"pasada": p, "ok": False, "error": "%s: %s" % (type(e).__name__, e)})
                faltan += 1
        finally:
            shutil.rmtree(dest, ignore_errors=True)
    # predicado del tablero (node) sobre los records control y relleno de esta parte
    import banco_paridad as bp
    casos, idx = [], []
    for i, r in enumerate(resultados):
        for brazo in ("control", "relleno"):
            rec = r.get(brazo)
            if rec:
                slim = {k: rec.get(k) for k in bp.CAMPOS_JS}
                casos.append([slim, r["pasada"]["inner"]])
                idx.append((i, brazo))
    if casos:
        pred = bp.correr_node(casos)
        for (i, brazo), pr in zip(idx, pred):
            resultados[i]["pub_" + brazo] = pr[4]
    (out / ("probe_m15_parte%d.json" % a.parte)).write_text(
        json.dumps(resultados, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nfaltan %d de %d pasadas" % (faltan, sum(len(por_gran[g]) for g in grans)))
    return 2 if faltan else 0


if __name__ == "__main__":
    sys.exit(main())
