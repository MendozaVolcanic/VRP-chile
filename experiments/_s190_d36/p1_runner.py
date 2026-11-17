# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): arnés de medición de D36 punto 1 (y 3 en MODIS). Sólo lectura: no escribe en data/, no
# commitea, no hace push. Corre en GitHub Actions (EARTHDATA_TOKEN sólo existe como secreto, A71).
"""Por cada pasada de p1_pasadas.json (elegidas antes de mirar resultados, ver p1_seleccion.py): baja el L1B MODIS y
su MxD03 (misma búsqueda que experiments/_s151_mxd03_etiquetas/probe_etiquetas.py::_bajar), corre la vía de
producción («prod», el módulo sin tocar) y los brazos A, B, B1, B2 de brazos.py, y guarda:
  - el resumen de cada record (sin las marcas de hora) y las celdas alertadas (fila, col), para leer zona y posición;
  - control_copia_igual: A == prod (la copia de detectar_mirova con los números de la vía da el mismo record);
  - control_produccion: prod contra el record guardado en data/mirova_equivalent (vrp_mw, n de píxeles, clase,
    distancia), con el codigo_sha del record guardado (si lo escribió otro commit y difiere, se informa, no se oculta);
  - punto 3: distancia del píxel más cercano al centro de la grilla, píxeles a menos de 45 km, y en las pasadas del
    estrato «borde» los brazos sin el corte de 5 km;
  - el recorte nativo de 60 km (MIR, TIR, lat, lon y ángulos del MxD03) en nativos/<volcan>_<sello>.npz, para repetir
    cualquier brazo en Windows sin volver a NASA.
Uso: python experiments/_s190_d36/p1_runner.py --out out --chunk I --nchunks N
"""
import argparse
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", RAIZ / "experiments/_s151_mxd03_etiquetas", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402

import brazos as BR  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

CAMPOS_CTRL = ("vrp_mw", "n_anomalous_pixels", "distance_class", "final_hotspot_dist_km")


def slim(r):
    if r is None:
        return None
    pc = r.get("primary_cluster") or {}
    dg = r.get("diag_codigo_mirova") or {}
    celdas = [[p["fila"], p["col"], p["bt_k"]] for p in (r.get("anomaly_pixels") or [])]
    return {"vrp_mw": r.get("vrp_mw"), "n": r.get("n_anomalous_pixels"), "dc": r.get("distance_class"),
            "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"), "pc_n": pc.get("n_pixels"),
            "final_dist": r.get("final_hotspot_dist_km"), "t_max_k": r.get("t_max_k"),
            "motivo": dg.get("motivo_vacio"), "n_abs": dg.get("n_abs"), "n_p1": dg.get("n_p1"),
            "n_p2": dg.get("n_p2"), "dayflag": dg.get("dayflag"), "celdas": celdas, "s1": dg.get("s1"),
            "sensor_zenith_deg": r.get("sensor_zenith_deg")}


def guardado(volcan, granule):
    recs = json.load(open(RAIZ / "data" / "mirova_equivalent" / (volcan + ".json"), encoding="utf-8"))["records"]
    g = [r for r in recs if r.get("granule") == granule]
    return g[-1] if g else None


def medir(p, out, tmp, rp, P):
    e = {k: p[k] for k in ("volcan", "granule", "sensor", "dt", "estratos")}
    partes = p["granule"].split(".")
    jd = partes[1] + "." + partes[2]
    l1b_short = partes[0]
    geo_short = "MOD03" if l1b_short.startswith("MOD") else "MYD03"
    l1b = P._bajar(l1b_short, jd, tmp)
    geo = P._bajar(geo_short, jd, tmp)
    e["l1b"] = None if l1b is None else Path(l1b).name
    e["geo"] = None if geo is None else Path(geo).name
    if l1b is None or geo is None:
        e["estado"] = "no_bajado"
        return e
    e["otro_granulo"] = Path(l1b).name != p["granule"]
    volcan = rp.load_volcanoes(p["volcan"])[0]
    vlat, vlon = get_detection_anchor(volcan)
    vlat = volcan["lat"] if vlat is None else vlat
    vlon = volcan["lon"] if vlon is None else vlon
    inner = volcan.get("inner_radius_km")
    rad = MV.leer_radiancia_modis(Path(l1b))
    lat, lon, ang = MV.leer_geo_mxd03(Path(geo))
    nombre = MV.volcan_por_coordenadas(volcan["lat"], volcan["lon"])
    e["nombre_grilla"] = nombre
    fam = MV.FAMILIAS["MODIS"]
    g = MV.grilla_del_volcan(nombre, paso_m=fam["paso_m"], clave_roi=fam["clave_roi"])
    d = MV._haversine(np.asarray(lat, float), np.asarray(lon, float), g["centro_lat"], g["centro_lon"])
    sel = np.isfinite(d) & (d < MV.RADIO_RECORTE_KM)
    e["n_sel_45km"] = int(sel.sum())
    e["dist_i0_km"] = float(np.nanmin(np.where(sel, d, np.inf))) if sel.any() else None
    br = BR.correr_brazos(rad, lat, lon, ang, nombre, vlat, vlon, inner, p["sensor"], sin_corte_5km=False)
    e["brazos"] = {k: slim(v) for k, v in br.items()}
    e["control_copia_igual"] = (json.dumps(e["brazos"]["A"], sort_keys=True)
                                == json.dumps(e["brazos"]["prod"], sort_keys=True))
    gr = guardado(p["volcan"], p["granule"])
    e["guardado_codigo_sha"] = ((gr or {}).get("regimen") or {}).get("codigo_sha")
    pr = br["prod"]
    if gr is None or pr is None:
        e["control_produccion"] = None
    else:
        e["control_produccion"] = {c: [pr.get(c), gr.get(c)] for c in CAMPOS_CTRL if pr.get(c) != gr.get(c)}
    if "borde" in p["estratos"]:
        sb = BR.correr_brazos(rad, lat, lon, ang, nombre, vlat, vlon, inner, p["sensor"], sin_corte_5km=True)
        e["brazos_sin_corte_5km"] = {k: slim(v) for k, v in sb.items()}
    rr, cc = np.nonzero(np.isfinite(d) & (d < 60.0))
    if rr.size:
        sl = (slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1))
        (out / "nativos").mkdir(parents=True, exist_ok=True)
        arrs = {"mir": np.asarray(rad["MIR"])[sl].astype(np.float32),
                "tir": np.asarray(rad["TIR"])[sl].astype(np.float32),
                "lat": np.asarray(lat)[sl].astype(np.float64), "lon": np.asarray(lon)[sl].astype(np.float64)}
        for k, v in ang.items():
            if v is not None:
                arrs[k] = np.asarray(v)[sl].astype(np.float32)
        np.savez_compressed(out / "nativos" / ("%s_%s_%s.npz" % (p["volcan"], jd, l1b_short)), **arrs)
    for f in (l1b, geo):
        try:
            os.remove(f)
        except OSError:
            pass
    e["estado"] = "ok"
    return e


def guardar(path, estado):
    t = path.with_suffix(".tmp")
    with open(t, "w", encoding="utf-8") as fh:
        json.dump(estado, fh, indent=1, ensure_ascii=False, default=str)
    os.replace(t, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunk", type=int, default=0)
    ap.add_argument("--nchunks", type=int, default=1)
    a = ap.parse_args()
    if not os.environ.get("EARTHDATA_TOKEN", "").strip():
        sys.exit("EARTHDATA_TOKEN vacio: el arnes no usa usuario y clave (A71).")
    import run_pipeline as rp
    import probe_etiquetas as P
    from pipeline.fetch import auth
    auth()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(os.environ.get("VRP_TMP_DIR") or tempfile.gettempdir()) / "s190_d36"
    pas = json.load(open(AQUI / "p1_pasadas.json", encoding="utf-8"))["pasadas"]
    pas = [p for i, p in enumerate(pas) if i % a.nchunks == a.chunk]
    estado = {"commit": os.environ.get("GITHUB_SHA"), "chunk": a.chunk, "nchunks": a.nchunks, "pasadas": []}
    salida = out / ("p1_resultados_%d.json" % a.chunk)
    for p in pas:
        t0 = time.time()
        try:
            e = medir(p, out, tmp, rp, P)
        except Exception as ex:
            e = {k: p[k] for k in ("volcan", "granule", "dt")}
            e.update({"estado": "error", "error": repr(ex), "traza": traceback.format_exc()[-2500:]})
        e["segundos"] = round(time.time() - t0, 1)
        estado["pasadas"].append(e)
        guardar(salida, estado)
        print(json.dumps({k: e.get(k) for k in ("volcan", "dt", "estado", "control_copia_igual", "segundos")}),
              flush=True)
    n_ok = sum(e.get("estado") == "ok" for e in estado["pasadas"])
    print("FIN chunk %d: %d ok de %d" % (a.chunk, n_ok, len(pas)), flush=True)
    sys.exit(0 if n_ok == len(pas) else 1)


if __name__ == "__main__":
    main()
