# -*- coding: utf-8 -*-
"""Probe S151, tarea 1.18: pixeles saturados en el L1B de Nevados de Chillan y su efecto en el VRP.

Medicion DESCRIPTIVA, sin umbral ni veredicto. Solo lectura: no escribe en data/, no commitea, borra
cada granulo apenas lo usa. Corre en GitHub Actions (pyhdf solo en Linux; credenciales locales no
sirven, A71).

Por cada granulo (L1B + geolocalizacion) de la familia y el tramo de dias pedidos, de dia y de noche:
  - cuenta los pixeles que el L1B trae y produccion borra por saturacion, por banda y por region
    (radio interior alrededor del ancla de deteccion, y la caja de escena de `radius_km`);
  - corre `calculate_vrp` + `store.append_record` de PRODUCCION dos veces sobre el mismo L1B:
      brazo "sin": tal cual (los saturados borrados, como hoy);
      brazo "con": identico, salvo que la lectura del L1B devuelve los saturados en su piso
                   (saturacion.py explica el piso);
  - informa la cota aditiva k * A * (L(piso) - L(t_bg)) de los pixeles MIR borrados en el radio interior.
El predicado y la magnitud del tablero (`mirovaEqVrpDisplay`) se evaluan con node al final (A97).

De dia produccion no procesa (filtro nocturno; ENABLE_DAYTIME_VIIRS apagado): el VRP diurno de este
probe es lo que el procesador de hoy daria sobre ese granulo, con sus umbrales nocturnos, y sirve solo
para ver cuanto cambia al restituir los saturados. El conteo diurno si es del L1B.

Uso (Linux con pyhdf):
  EARTHDATA_TOKEN=... VRP_PROFILE=mirova_equivalent python probe_saturacion.py \
      --familia V375 --desde 2026-09-28 --hasta 2026-10-16 --tramo 0 --n-tramos 4 --out out
  python probe_saturacion.py --listar --familia V375 --desde ... --hasta ...   (solo CMR, sin bajar)
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import saturacion as S  # noqa: E402
from pipeline import store  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402
from pipeline.scan_geometry import haversine_km, roi_mask_bbox  # noqa: E402

VOLCAN = "NevadosDeChillan"
MODULO = {"V375": ("pipeline.process_viirs", "read_viirs_l1b", "read_viirs_geo"),
          "V750": ("pipeline.process_viirs_mod", "read_viirs_mod_l1b", "read_viirs_mod_geo"),
          "MODIS": ("pipeline.process_modis", "read_modis_l1b", None)}


def modulo(familia):
    return importlib.import_module(MODULO[familia][0])


# ------------------------------------------------------------------ argumentos de produccion
def argumentos_calculate_vrp(familia, volcan):
    """Los keyword de `calculate_vrp` tal como los arma scripts/run_pipeline.py (process_date) en
    cada rama. El test los compara contra el AST de run_pipeline."""
    vlat, vlon = get_detection_anchor(volcan)
    kw = {
        "vent_lat": vlat,
        "vent_lon": vlon,
        "vent_radius_km": volcan.get("vent_radius_km", 4.0),
        "inner_radius_km": volcan.get("inner_radius_km"),
        "exclude_zones": volcan.get("exclude_zones"),
        "active_water_bodies": volcan.get("active_water_bodies"),
        "lbg_global_compatible": volcan.get("lbg_global_compatible", False),
        "local_kernel_bg_compatible": volcan.get("local_kernel_bg", False),
    }
    if familia == "V375":
        kw["lava_lake_magmatic"] = volcan.get("lava_lake_magmatic", False)
    return kw


def argumentos_append_record(volcan, overwrite, volcanic_features=None):
    from pipeline import profile as vrp_profile
    return {
        "volcano_lat": volcan["lat"], "volcano_lon": volcan["lon"],
        "overwrite": overwrite,
        "max_hotspot_dist_km": volcan.get("radius_km"),
        "enable_pixel_level_distance_filter": vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
        "max_cluster_pixels": volcan.get("max_cluster_pixels"),
        "inner_radius_km": volcan.get("inner_radius_km"),
        "volcanic_features": volcanic_features,
    }


def _copia(d):
    if isinstance(d, np.ndarray):
        return d.copy()
    if isinstance(d, dict):
        return {k: _copia(v) for k, v in d.items()}
    return d


def correr_brazo(familia, l1b, geo, volcan, datos, volcanic_features=None):
    """calculate_vrp + store.append_record de produccion con la lectura del L1B reemplazada por `datos`
    (cada llamada recibe una copia). El store escribe en un directorio temporal, nunca en data/."""
    mod = modulo(familia)
    lector = MODULO[familia][1]
    with patch.object(mod, lector, lambda _p: _copia(datos)):
        res = mod.calculate_vrp(Path(l1b), Path(geo), volcan["lat"], volcan["lon"], volcan["radius_km"],
                                **argumentos_calculate_vrp(familia, volcan))
    if not res:
        return None
    with tempfile.TemporaryDirectory() as tmp, patch.object(store, "DATA_DIR", Path(tmp)):
        store.append_record(volcan["name"], res, **argumentos_append_record(volcan, True, volcanic_features))
        recs = store.get_records(volcan["name"])
    return recs[-1] if recs else None


def resumir(rec):
    if rec is None:
        return None
    pc = rec.get("primary_cluster") or {}
    return {"dc": rec.get("distance_class"), "vrp_mw": rec.get("vrp_mw"), "vrp_mir_mw": rec.get("vrp_mir_mw"),
            "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"), "pc_n": pc.get("n_pixels"),
            "f5_core_vrp_mw": rec.get("f5_core_vrp_mw"), "t_max_k": rec.get("t_max_k"),
            "t_bg_k": rec.get("t_bg_k"), "n_anom": rec.get("n_anomalous_pixels"),
            "final_dist": rec.get("final_hotspot_dist_km"), "sensor": rec.get("sensor"),
            "datetime_utc": rec.get("datetime_utc"), "cenit": rec.get("sensor_zenith_deg")}


# ------------------------------------------------------------------ medicion de un granulo
def _leer_si_modis(path):
    """SI crudos de las bandas 21, 22 y 31 (EV_1KM_Emissive). Solo en el runner (pyhdf)."""
    from pyhdf.SD import SD, SDC
    from pipeline import process_modis as pm
    sd = SD(str(path), SDC.READ)
    try:
        sds = sd.select("EV_1KM_Emissive")
        a = sds.get()
        sds.endaccess()
    finally:
        sd.end()
    return {"B21": a[pm.BAND21_IDX], "B22": a[pm.BAND22_IDX], "B31": a[pm.BAND31_IDX]}


def preparar(familia, l1b, geo, lector_si=None):
    """Lecturas de produccion, mascaras de borrado, pisos y datos del brazo "con".

    Devuelve dict con: prod (lo que produccion lee), con (lo mismo con los saturados en su piso),
    mascaras (por banda, mas "MIR" = banda MIR que entra al VRP), pisos (K), origen_pisos,
    techos_lut, lat, lon, bt_mir (BT MIR de produccion, para el piso empirico).
    """
    mod = modulo(familia)
    if familia in ("V375", "V750"):
        prod = getattr(mod, MODULO[familia][1])(Path(l1b))
        g = getattr(mod, MODULO[familia][2])(Path(geo))
        crudo = S.leer_viirs_crudo(l1b, S.BANDAS[familia], mod.FLAG_DNS)
        mascaras, pisos, origen, techos = {}, {}, {}, {}
        for b in S.BANDAS[familia]:
            if b not in crudo or b not in prod:
                continue
            techos[b] = crudo[b]["techo_lut"]
            pisos[b], origen[b] = S.techo_banda(familia, b, crudo[b])
            if crudo[b]["bt"] is None:
                continue
            mascaras[b] = S.mascaras_borrado(crudo[b]["bt"], prod[b], crudo[b]["qf"])
        con = S.bandas_con_saturados(prod, mascaras, crudo, pisos)
        mir = S.BANDA_MIR[familia]
        if mir in mascaras:
            mascaras["MIR"] = mascaras[mir]
        return {"prod": prod, "con": con, "mascaras": mascaras, "pisos": pisos, "origen_pisos": origen,
                "techos_lut": techos, "lat": g["lat"], "lon": g["lon"], "bt_mir": prod.get(mir),
                "n_bit_total": {b: crudo[b]["n_bit_total"] for b in crudo}}
    from pipeline import process_modis as pm
    from pipeline import profile as prof
    prod = pm.read_modis_l1b(Path(l1b))
    si = (lector_si or _leer_si_modis)(l1b)
    mascaras = {b: S.mascaras_modis(si[b]) for b in ("B21", "B22", "B31")}
    pisos, origen = S.pisos_modis(prod, None)
    con = S.datos_modis_con_saturados(prod, mascaras, pisos)
    mascaras["MIR"] = S.mir_perdido_modis(mascaras, prof.ENABLE_MODIS_B22_PRIMARY)
    return {"prod": prod, "con": con, "mascaras": mascaras, "pisos": pisos, "origen_pisos": origen,
            "techos_lut": {}, "lat": prod["lat"], "lon": prod["lon"],
            "bt_mir": pm.radiance_to_bt(prod["band21"], pm.BAND21_LAMBDA),
            "n_bit_total": {b: int(mascaras[b]["bit"].sum()) for b in ("B21", "B22", "B31")}}


def lambda_mir(familia):
    if familia == "V375":
        from pipeline.process_viirs import I04_LAMBDA
        return I04_LAMBDA
    if familia == "V750":
        from pipeline.process_viirs_mod import M13_LAMBDA
        return M13_LAMBDA
    from pipeline.process_modis import BAND21_LAMBDA
    return BAND21_LAMBDA


def medir_granulo(familia, l1b, geo, volcan, volcanic_features=None, lector_si=None):
    """Conteo + los dos brazos + cota aditiva de un granulo. Sin el predicado del tablero (va en lote)."""
    mod = modulo(familia)
    p = preparar(familia, l1b, geo, lector_si)
    vlat, vlon = get_detection_anchor(volcan)
    lat, lon = np.asarray(p["lat"]), np.asarray(p["lon"])
    with np.errstate(invalid="ignore"):
        summit = haversine_km(vlat, vlon, lat, lon) <= volcan["inner_radius_km"]
    escena = roi_mask_bbox(lat, lon, volcan["lat"], volcan["lon"], volcan["radius_km"])
    conteo = S.contar(p["mascaras"], {"interior": summit, "escena": escena})
    rec_sin = correr_brazo(familia, l1b, geo, volcan, p["prod"], volcanic_features)
    rec_con = correr_brazo(familia, l1b, geo, volcan, p["con"], volcanic_features)
    n_mir = int((p["mascaras"]["MIR"]["borrado"] & summit).sum()) if "MIR" in p["mascaras"] else 0
    if familia == "MODIS":
        n_mir = int((p["mascaras"]["MIR"]["bit"] & summit).sum())
    t_bg = (rec_sin or {}).get("t_bg_k")
    mir = S.BANDA_MIR[familia]
    piso_decl = p["pisos"].get(mir)
    piso_emp = S.bt_max_valida(p["bt_mir"], escena) if p["bt_mir"] is not None else None
    lam = lambda_mir(familia)
    cota = {"n_mir_borrados_interior": n_mir, "t_bg_k": t_bg, "piso_declarado_k": piso_decl,
            "piso_empirico_k": piso_emp, "k": mod.WOOSTER_COEFF, "area_m2": mod.NADIR_PIXEL_AREA_M2,
            "mw_piso_declarado": S.cota_aditiva_mw(n_mir, piso_decl, t_bg, lam, mod.WOOSTER_COEFF,
                                                  mod.NADIR_PIXEL_AREA_M2),
            "mw_piso_empirico": S.cota_aditiva_mw(n_mir, piso_emp, t_bg, lam, mod.WOOSTER_COEFF,
                                                 mod.NADIR_PIXEL_AREA_M2)}
    return {"conteo": conteo, "pisos_k": p["pisos"], "origen_pisos": p["origen_pisos"],
            "techos_lut_k": p["techos_lut"], "n_bit_granulo_entero": p["n_bit_total"],
            "bt_mir_max_valida_interior_k": S.bt_max_valida(p["bt_mir"], summit) if p["bt_mir"] is not None else None,
            "cota_aditiva": cota, "sin": resumir(rec_sin), "con": resumir(rec_con)}, rec_sin, rec_con


def tablero(records, inner):
    """[display, publica] de cada record con el predicado del tablero ejecutado con node (A97)."""
    import banco_paridad as bp
    casos, idx = [], []
    for i, r in enumerate(records):
        if r is None:
            continue
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                  for q in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner])
        idx.append(i)
    out = [[None, 0] for _ in records]
    for i, res in zip(idx, bp.correr_node(casos) if casos else []):
        out[i] = [res[3], int(res[4])]
    return out


# ------------------------------------------------------------------ E/S (solo en el runner)
def buscar_pares(familia, volcan, dias):
    """Pares (plataforma, granulo L1B, granulo geo) del CMR, de dia y de noche, sin repetir L1B."""
    from pipeline import fetch
    pares, vistos = [], set()
    for dia in dias:
        d = datetime.strptime(dia, "%Y-%m-%d")
        for plat, kl, kg in S.PLATAFORMAS[familia]:
            l1b = fetch.search_granules(kl, volcan["lat"], volcan["lon"], volcan["radius_km"], d)
            if not l1b:
                continue
            geo = fetch.search_granules(kg, volcan["lat"], volcan["lon"], volcan["radius_km"], d)
            for gl, gg in fetch._match_granules(l1b, geo):
                nombre = _nombre(gl)
                if nombre in vistos:
                    continue
                vistos.add(nombre)
                pares.append((plat, gl, gg))
    return pares


def es_l1b(nombre):
    """El L1B lleva 02IMG, 02MOD o 021KM en el nombre; la geolocalizacion, 03IMG, 03MOD o 03."""
    return any(t in nombre for t in ("02IMG", "02MOD", "021KM"))


def _nombre(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        try:
            return Path(g.data_links()[0]).name
        except Exception:
            return str(g)


def _mb(g):
    try:
        return float(g.size())
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--familia", required=True, choices=S.FAMILIAS)
    ap.add_argument("--desde", default="2026-09-28")
    ap.add_argument("--hasta", default=None, help="AAAA-MM-DD; por defecto hoy UTC")
    ap.add_argument("--tramo", type=int, default=0)
    ap.add_argument("--n-tramos", type=int, default=1)
    ap.add_argument("--out", default="out")
    ap.add_argument("--presupuesto-min", type=float, default=80.0)
    ap.add_argument("--listar", action="store_true", help="solo buscar en el CMR y contar (no baja nada)")
    a = ap.parse_args()
    hasta = a.hasta or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dias = S.dias_del_tramo(a.desde, hasta, a.tramo, a.n_tramos)
    import run_pipeline as rp     # el mismo dict de volcan que produccion (overrides del perfil incluidos)
    volcan = rp.load_volcanoes(VOLCAN)[0]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    etiqueta = "%s_t%d" % (a.familia, a.tramo)

    if a.listar:
        pares = buscar_pares(a.familia, volcan, dias)
        filas = []
        for plat, gl, gg in pares:
            dt = S.hora_granulo(_nombre(gl))
            filas.append({"plataforma": plat, "l1b": _nombre(gl), "geo": _nombre(gg),
                          "noche": None if dt is None else bool(rp.is_nighttime(volcan["lat"], volcan["lon"], dt)),
                          "mb": round(_mb(gl) + _mb(gg), 1)})
        res = {"familia": a.familia, "dias": dias, "n": len(filas),
               "n_noche": sum(1 for f in filas if f["noche"]), "mb_total": round(sum(f["mb"] for f in filas), 1),
               "pares": filas}
        (out / ("lista_%s.json" % etiqueta)).write_text(json.dumps(res, indent=1), encoding="utf-8")
        print("%s %s a %s: %d pares (%d de noche), %.0f MB" % (a.familia, dias[0], dias[-1], res["n"],
                                                               res["n_noche"], res["mb_total"]))
        return

    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el probe no usa usuario y clave (A71).")
    from pipeline.fetch import auth, download_granules
    auth()
    t0 = time.time()
    feats = rp.VOLCANIC_FEATURES.get(volcan["name"])
    pares = buscar_pares(a.familia, volcan, dias)
    print("%s: %d pares en %s a %s" % (etiqueta, len(pares), dias[0], dias[-1]), flush=True)
    hdf = out / "hdf"
    filas, recs_sin, recs_con = [], [], []
    for plat, gl, gg in pares:
        nombre = _nombre(gl)
        dt = S.hora_granulo(nombre)
        fila = {"familia": a.familia, "plataforma": plat, "l1b": nombre, "geo": _nombre(gg),
                "datetime_utc": None if dt is None else dt.strftime("%Y-%m-%d %H:%M"),
                "noche": None if dt is None else bool(rp.is_nighttime(volcan["lat"], volcan["lon"], dt))}
        filas.append(fila)
        recs_sin.append(None)
        recs_con.append(None)
        if (time.time() - t0) / 60.0 > a.presupuesto_min:
            fila["estado"] = "sin_tiempo"
            continue
        paths = []
        t1 = time.time()
        try:
            paths = download_granules([gl, gg], hdf / plat)
            l1b = next((p for p in paths if es_l1b(p.name)), None)
            geo = next((p for p in paths if not es_l1b(p.name)), None)
            if l1b is None or geo is None:
                fila["estado"] = "error"
                fila["error"] = "no bajado (%d de 2 archivos)" % len(paths)
                continue
            med, rs, rc = medir_granulo(a.familia, l1b, geo, volcan, feats)
            fila.update(med)
            recs_sin[-1], recs_con[-1] = rs, rc
            fila["estado"] = "ok"
        except Exception as e:  # un granulo roto no tumba el tramo; queda contado como error
            fila["estado"] = "error"
            fila["error"] = "%s: %s" % (type(e).__name__, str(e)[:300])
        finally:
            for p in paths:
                Path(p).unlink(missing_ok=True)
            fila["segundos"] = round(time.time() - t1, 1)
        print(json.dumps({k: fila.get(k) for k in ("l1b", "noche", "estado", "segundos")}, ensure_ascii=False),
              flush=True)
    inner = volcan["inner_radius_km"]
    for fila, ts, tc in zip(filas, tablero(recs_sin, inner), tablero(recs_con, inner)):
        if fila.get("estado") == "ok":
            fila["tablero_sin"], fila["tablero_con"] = ts, tc
    res = {"volcan": VOLCAN, "familia": a.familia, "tramo": a.tramo, "dias": dias, "inner_radius_km": inner,
           "minutos": round((time.time() - t0) / 60.0, 1), "pasadas": filas}
    (out / ("sat_%s.json" % etiqueta)).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    n_ok = sum(1 for f in filas if f.get("estado") == "ok")
    print("%s: %d de %d pasadas medidas en %.1f min" % (etiqueta, n_ok, len(filas), res["minutos"]))


if __name__ == "__main__":
    main()
