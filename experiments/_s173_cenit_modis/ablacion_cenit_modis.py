# -*- coding: utf-8 -*-
"""S173: ablación por pieza de la vía «código MIROVA» de MODIS (MOD-D) sobre las pasadas MODIS de Nevados de Chillán con
alerta de MIROVA, partida por cenit. Corre en GitHub Actions (pyhdf sólo en Linux). Sólo lectura.

POR QUÉ. En Chillán la razón de K contra MIROVA cae con el ángulo cenital del satélite (S172: Spearman -0,87, n 12;
bajo 30° 0,75, sobre 30° 0,20) y tres alertas protegidas MODIS se pierden a ~58°. La vía MOD-D lleva la razón cerca
de 1 en todos los cenit, pero cambia varias piezas a la vez. Este arnés las reemplaza de a una para saber cuál corrige
la caída oblicua: el remuestreo a la grilla fija (D17) o el fondo (D25). Ver piezas.py (brazos) y
experiments/_s173_cenit_modis/README.md (qué haría falta para correrlo y cómo leerlo).

Por pasada (lista en pasadas_chillan_modis.json, con gránulo, cenit y VRP de MIROVA):
  K    process_modis.calculate_vrp + store.append_record con el perfil mirova_equivalent y
       process_modis.ENABLE_MODIS_CODIGO_MIROVA = False EN MEMORIA (desde #934 el perfil lo trae en True; K es el
       brazo de producción hasta el encendido del 2026-11-02; probe_etiquetas.procesar_brazo). Control: igual al record guardado en
       data/mirova_equivalent/NevadosDeChillan.json salvo las marcas de hora (si el record lo escribió otro commit, se
       informa el codigo_sha y no se oculta).
  V    la misma llamada con process_modis.ENABLE_MODIS_CODIGO_MIROVA = True EN MEMORIA (patch.object). Control: en las
       2 pasadas que producción ya escribió con la vía, igual al record guardado; en las demás, V / MIROVA igual a la
       razón del brazo V de la lectura del A/B de MOD-D (la tabla va en el README).
  brazos de piezas.py sobre el mismo gránulo (V0 tiene que dar el VRP y las celdas de V).
Escribe <out>/s173_cenit_modis.json (atómico, una entrada por pasada, también los errores) y el recorte nativo de cada
pasada (<out>/nativos/<dt>.npz) para releer sin volver a NASA. NO escribe en data/, NO commitea, NO hace push.
Uso: python experiments/_s173_cenit_modis/ablacion_cenit_modis.py --out out [--solo 2026-10-17_0850,...]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", RAIZ / "experiments/_s151_mxd03_etiquetas", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402
import yaml  # noqa: E402
import probe_etiquetas as P  # noqa: E402  (procesar_brazo, publica, registros_iguales, _bajar)
import piezas as PZ  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import process_modis as pm  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

VOLCAN = "NevadosDeChillan"
PASADAS = AQUI / "pasadas_chillan_modis.json"
CAMPOS_K = ("vrp_mw", "n_anomalous_pixels", "distance_class", "t_bg_k", "t_max_k", "sensor_zenith_deg")


def volcan_yaml():
    vs = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
    return [v for v in vs if v["name"] == VOLCAN][0]


def features():
    """Como scripts/run_pipeline.py::_load_volcanic_features (l. 96-104 en main de hoy)."""
    f = RAIZ / "pipeline/volcanic_features.yaml"
    if not f.exists():
        return None
    return (yaml.safe_load(open(f, encoding="utf-8")) or {}).get(VOLCAN)


def guardado(dt, sensor):
    d = json.load(open(RAIZ / "data/mirova_equivalent" / f"{VOLCAN}.json", encoding="utf-8"))
    for r in d["records"]:
        if r.get("datetime_utc") == dt and r.get("sensor") == sensor:
            return r
    return None


def comparar_campos(a, b):
    """Diferencias de campo entre dos records (None si uno falta); pc.vrp_mw y la lista de píxeles incluidos."""
    if a is None or b is None:
        return None if (a is None and b is None) else ["uno de los dos es None"]
    dif = [k for k in CAMPOS_K if a.get(k) != b.get(k)]
    if (a.get("primary_cluster") or {}).get("vrp_mw") != (b.get("primary_cluster") or {}).get("vrp_mw"):
        dif.append("primary_cluster.vrp_mw")
    pa = [(p.get("lat"), p.get("lon"), p.get("vrp_mw")) for p in (a.get("anomaly_pixels") or [])]
    pb = [(p.get("lat"), p.get("lon"), p.get("vrp_mw")) for p in (b.get("anomaly_pixels") or [])]
    if pa != pb:
        dif.append("anomaly_pixels")
    return dif


def slim(rec):
    if rec is None:
        return None
    pc = rec.get("primary_cluster") or {}
    return {"vrp_mw": rec.get("vrp_mw"), "pc_vrp_mw": pc.get("vrp_mw"), "npix": rec.get("n_anomalous_pixels"),
            "distance_class": rec.get("distance_class"), "pc_dist_km": pc.get("centroid_dist_km"),
            "via": rec.get("via_codigo_mirova"), "sensor_zenith_deg": rec.get("sensor_zenith_deg"),
            "granule": rec.get("granule")}


def recorte_nativo(lat, lon, centro, radio_km=60.0):
    """Ventana (filas, columnas) del gránulo con los píxeles a menos de radio_km del centro de la grilla."""
    d = MV._haversine(lat, lon, centro[0], centro[1])
    rr, cc = np.nonzero(np.isfinite(d) & (d < radio_km))
    return slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1)


def medir(p, volcan, feats, outdir):
    t0 = time.time()
    e = {"dt": p["dt"], "sensor": p["sensor"], "z_record": p["z"], "vrp_mirova_mw": p["vrp_mirova_mw"]}
    jd = p["granule"].split(".")[1] + "." + p["granule"].split(".")[2]      # A2026274.0835
    l1b_short = p["granule"].split(".")[0]                                  # MOD021KM / MYD021KM
    geo_short = "MOD03" if l1b_short.startswith("MOD") else "MYD03"
    tmp = Path(os.environ.get("VRP_TMP_DIR") or tempfile.gettempdir()) / "s173_cenit"
    l1b = P._bajar(l1b_short, jd, tmp)
    geo = P._bajar(geo_short, jd, tmp)
    e["l1b"], e["geo"] = (None if l1b is None else l1b.name), (None if geo is None else geo.name)
    if l1b is None or geo is None:
        e["estado"] = "no_bajado"
        return e
    e["otro_granulo"] = l1b.name != p["granule"]
    # --- K y V con el pipeline (los dos por store.append_record, como producción)
    # VER937 (verificador S173): desde #934 el perfil mirova_equivalent trae el flag en True, así que K se fuerza a
    # False en memoria; sin esto K era V. El único lector del flag es process_modis (l. 106 y 637).
    with patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", False):
        rk = P.procesar_brazo(l1b, geo, volcan, None, feats)
    with patch.object(pm, "ENABLE_MODIS_CODIGO_MIROVA", True):
        rv = P.procesar_brazo(l1b, geo, volcan, None, feats)
    g = guardado(p["dt"], p["sensor"])
    via_guardado = (g or {}).get("via_codigo_mirova")
    e["guardado"] = slim(g)
    e["guardado_codigo_sha"] = ((g or {}).get("regimen") or {}).get("codigo_sha")
    e["K"], e["V"] = slim(rk), slim(rv)
    ctrl = rv if via_guardado is True else rk
    e["control_produccion_brazo"] = "V" if via_guardado is True else "K"
    e["control_produccion_igual"] = P.registros_iguales(ctrl, g)
    e["control_produccion_dif"] = comparar_campos(ctrl, g)
    # --- brazos de piezas sobre el mismo gránulo
    rad = MV.leer_radiancia_modis(l1b)
    lat, lon, ang = MV.leer_geo_mxd03(geo)
    d5 = pm.read_modis_l1b(l1b)
    grilla = MV.grilla_del_volcan(VOLCAN, paso_m=1000.0, clave_roi="roi_modis")
    dayflag, sg, geom, d0 = PZ.dayflag_sunglint(lat, lon, ang, grilla)
    e.update({"dayflag": dayflag, "sunglint": sg, "geom_i0": geom, "dist_i0_km": d0})
    vent = get_detection_anchor(volcan)
    sl = recorte_nativo(lat, lon, (grilla["centro_lat"], grilla["centro_lon"]))
    cr = {"MIR": rad["MIR"][sl], "TIR": rad["TIR"][sl]}
    # El remuestreo de la vía recorta a 45 km y el recorte nativo es de 60: la grilla sale igual (control V0 == V)
    br = PZ.correr_brazos(cr, lat[sl], lon[sl], np.asarray(d5["lat"], float)[sl], np.asarray(d5["lon"], float)[sl],
                          grilla, vent, (volcan["lat"], volcan["lon"]), volcan.get("inner_radius_km"), p["sensor"],
                          dayflag, sg, np.asarray(ang["sensor_zenith"], float)[sl])
    # publicación con el predicado del tablero (node sobre frontend/index.html); los brazos nativos no arman record
    import banco_paridad as bp
    recs = [br[b].get("_record") for b in PZ.BRAZOS] + [rk, rv]
    pubs = P.publica(recs, bp.inner_desde_html()[VOLCAN])
    for b, pb in zip(list(PZ.BRAZOS) + ["K", "V"], pubs):
        if b in br:
            br[b]["publica"] = pb if "_record" in br[b] else None
        elif b == "K":
            e["K_publica"] = pb
        else:
            e["V_publica"] = pb
    for b in br.values():
        b.pop("_record", None)
    e["brazos"] = br
    e["control_V0_igual_V"] = (rv is not None and br["V0"]["npix"] == rv.get("n_anomalous_pixels")
                               and br["V0"]["vrp_mw"] == rv.get("vrp_mw"))
    (outdir / "nativos").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(outdir / "nativos" / (p["dt"].replace(" ", "_").replace(":", "") + ".npz"),
                        mir=cr["MIR"], tir=cr["TIR"], lat_mxd03=lat[sl], lon_mxd03=lon[sl],
                        lat_5km=np.asarray(d5["lat"], np.float32)[sl], lon_5km=np.asarray(d5["lon"], np.float32)[sl],
                        sensor_zenith=np.asarray(ang["sensor_zenith"], np.float32)[sl],
                        dayflag=dayflag, sunglint=sg, filas=np.array([sl[0].start, sl[0].stop]),
                        columnas=np.array([sl[1].start, sl[1].stop]))
    e["estado"] = "ok"
    e["segundos"] = round(time.time() - t0, 1)
    return e


def guardar(path, estado):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(estado, fh, indent=1, ensure_ascii=False, default=str)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    # VMODIS-01 (verificador S173): sin login, earthaccess.download devuelve [] y las 27 pasadas salían «no bajado».
    # Mismo patrón que probe_etiquetas.main: sólo EARTHDATA_TOKEN (A71) y auth() de producción antes de bajar nada.
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: la ablacion no usa usuario y clave (A71).")
    from pipeline.fetch import auth
    auth()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pas = json.load(open(PASADAS, encoding="utf-8"))["pasadas"]
    if a.solo:
        quiero = set(a.solo.split(","))
        pas = [p for p in pas if p["dt"].replace(" ", "_").replace(":", "") in quiero]
    volcan, feats = volcan_yaml(), features()
    estado = {"commit": os.environ.get("GITHUB_SHA"), "pasadas": []}
    errores = 0
    for p in pas:
        print(f"== {p['dt']} {p['sensor']} z {p['z']}", flush=True)
        try:
            e = medir(p, volcan, feats, out)
        except Exception as ex:   # una pasada que cae se anota y no detiene las demás
            errores += 1
            e = {"dt": p["dt"], "sensor": p["sensor"], "estado": "error", "error": repr(ex),
                 "traza": traceback.format_exc()[-3000:]}
        estado["pasadas"].append(e)
        guardar(out / "s173_cenit_modis.json", estado)
        print(json.dumps({k: e.get(k) for k in ("estado", "control_produccion_igual", "control_V0_igual_V",
                                                 "segundos")}), flush=True)
    n_ok = sum(e.get("estado") == "ok" for e in estado["pasadas"])
    print(f"FIN: {n_ok} ok de {len(pas)}; errores {errores}", flush=True)
    sys.exit(0 if n_ok == len(pas) else 1)


if __name__ == "__main__":
    main()
