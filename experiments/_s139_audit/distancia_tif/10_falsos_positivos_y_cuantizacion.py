# -*- coding: utf-8 -*-
"""S139 - ¿qué se puede hacer con una fila FALSO_POSITIVO, y con qué paso viene la distancia?

TRES COSAS, todas para el banco de prueba de paridad:

1. SEÑAL EN EL CRÁTER CUANDO LA FILA DICE "LEJOS". El scraper marca FALSO_POSITIVO toda
   pasada cuya distancia publicada supera el radio del volcán, y su dashboard la esconde.
   Si el número publicado es el píxel más LEJANO del cúmulo, una de esas filas puede tener
   el cráter caliente adentro. Se mide directo sobre el TIF: ¿hay un máximo local dentro del
   `inner_radius_km` que supere el percentil 99 del campo pasado por alto de esa misma
   escena? Con control en ALERTA (donde tiene que ser alto) y en RUTINA (donde tiene que
   ser bajo).

2. CUANTIZACIÓN. Con qué paso viene `Distancia_km` de la web, comparado con el paso de
   `Max_Dist` del archivo OSF y con el retículo del sensor. Un número que cae siempre sobre
   el retículo es una distancia a un CENTRO DE PÍXEL, no a un punto libre.

3. CONTROL DE PAREO DESPLAZADO 6 h sobre el subconjunto bueno.

Read-only.
"""
import io
import json
import math
import os
import sys

import numpy as np
import pandas as pd
import rasterio
import yaml
from scipy.ndimage import median_filter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARCH = os.path.abspath(os.path.join(ROOT, "..", "mirova-tif-archive"))
DL = os.path.join(AQUI, "_dl_")
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
KERNEL = 9


def senal_en_el_crater(path, vent, inner_km):
    with rasterio.open(path) as src:
        a = src.read(1).astype(float)
        tr = src.transform
        h, w = a.shape
        rows, cols = np.mgrid[0:h, 0:w]
        xs, ys = rasterio.transform.xy(tr, rows.ravel(), cols.ravel())
        lat = np.array(ys).reshape(h, w)
        lon = np.array(xs).reshape(h, w)
    fin = np.isfinite(a)
    if fin.sum() < 200:
        return None
    b = np.where(fin, a, np.nanmedian(a[fin]))
    hp = b - median_filter(b, size=KERNEL)
    hp[~fin] = np.nan
    p99 = float(np.nanpercentile(hp, 99))
    sig = float(np.nanstd(hp))
    dv = np.hypot((lat - vent[0]) * 110.574,
                  (lon - vent[1]) * 111.320 * math.cos(math.radians(vent[0])))
    loc = (dv <= inner_km) & fin
    if loc.sum() < 5 or sig <= 0:
        return None
    pico = float(np.nanmax(np.where(loc, hp, -np.inf)))
    return {"pico_inner": round(pico, 5), "p99_escena": round(p99, 5),
            "sigma_escena": round(sig, 5),
            "supera_p99": bool(pico > p99),
            "pico_inner_sigmas": round(pico / sig, 2),
            "n_px_inner": int(loc.sum())}


def main():
    vols = {v["name"]: v for v in yaml.safe_load(
        open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
    det = json.load(open(os.path.join(AQUI, "06_hipotesis_caliente_vs_lejano.json"),
                         encoding="utf-8"))
    # La sonda 06 guarda sólo el subconjunto "bueno"; para el punto 1 hace falta todo,
    # así que se re-pare desde la sonda 04, que sí guardó las 1.545 pasadas locales.
    todo = json.load(open(os.path.join(AQUI, "04_pareo_tif_vs_distancia.json"),
                          encoding="utf-8"))["detalle"]
    filas = []
    for f in todo:
        if not f.get("pareado") or "tipo" not in f:
            continue
        vol = f["volcan"]
        vcfg = vols[vol]
        vent = (vcfg.get("vent_lat", vcfg["lat"]), vcfg.get("vent_lon", vcfg["lon"]))
        p = os.path.join(ARCH, f["tif"].replace("/", os.sep))
        if not os.path.exists(p):
            continue
        s = senal_en_el_crater(p, vent, float(vcfg.get("inner_radius_km", 5)))
        if s is None:
            continue
        filas.append({"volcan": vol, "sensor": f["sensor"], "tipo": f["tipo"],
                      "vrp_mw": f["vrp_mw"], "dist_pub_km": f["dist_pub_km"],
                      "acq": f["acq"], **s})
    # Y las descargadas (FALSO_POSITIVO nocturnos posteriores a mayo).
    baj = json.load(open(os.path.join(AQUI, "05_bajados.json"), encoding="utf-8"))["detalle"]
    for o in baj:
        vol = o["volcan"]
        vcfg = vols[vol]
        vent = (vcfg.get("vent_lat", vcfg["lat"]), vcfg.get("vent_lon", vcfg["lon"]))
        p = os.path.join(DL, o["tif_path"].replace("/", os.sep))
        if not os.path.exists(p):
            continue
        s = senal_en_el_crater(p, vent, float(vcfg.get("inner_radius_km", 5)))
        if s is None:
            continue
        filas.append({"volcan": vol, "sensor": o["sensor"], "tipo": o["tipo"],
                      "vrp_mw": o["vrp_mw"], "dist_pub_km": o["dist_pub_km"],
                      "acq": o["acq"], **s})
    d = pd.DataFrame(filas).drop_duplicates(subset=["volcan", "sensor", "acq"])

    R = {"_meta": {
        "n_pasadas": int(len(d)),
        "ventana": [str(d.acq.min()), str(d.acq.max())],
        "definicion_senal": "máximo del campo pasado por alto dentro del inner_radius_km, "
                            "comparado con el percentil 99 del mismo campo en la escena",
        "kernel_px": KERNEL,
        "limite": "el TIF no trae la máscara de píxeles alertados de MIROVA: esto mide si "
                  "hay un foco local en el cráter, no si MIROVA lo alertó."}}
    R["senal_en_el_crater_por_etiqueta"] = {
        t: {"n": int((d.tipo == t).sum()),
            "supera_p99_pct": round(100.0 * float(d.loc[d.tipo == t, "supera_p99"].mean()), 1),
            "pico_inner_sigmas_mediano": round(float(np.median(
                d.loc[d.tipo == t, "pico_inner_sigmas"])), 2)}
        for t in sorted(d.tipo.dropna().unique())}
    fp = d[d.tipo == "FALSO_POSITIVO"]
    R["falsos_positivos_por_volcan"] = {
        v: {"n": int(len(g)),
            "supera_p99_pct": round(100.0 * float(g.supera_p99.mean()), 1),
            "dist_pub_mediana_km": round(float(np.median(g.dist_pub_km)), 2)}
        for v, g in fp.groupby("volcan") if len(g) >= 5}

    # ── 2. Cuantización ────────────────────────────────────────────────────
    w = pd.read_csv(WEB)
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    w = w[(w.Distancia_km > 0) & w.Tipo_Registro.isin(["ALERTA_TERMICA", "FALSO_POSITIVO"])]
    o = pd.read_csv(OSF, usecols=["Volc_Name", "Resolution", "Max_Dist"])
    o["res"] = o.Resolution.round()
    cuant = {}
    for sw, res, paso in (("VIIRS375", 375.0, 0.375), ("VIIRS", 750.0, 0.75),
                          ("MODIS", 1000.0, 1.0)):
        vw = np.sort(w.loc[w.Sensor == sw, "Distancia_km"].unique())
        vo = np.sort((o.loc[o.res == res, "Max_Dist"] / 1000.0).round(3).unique())
        vo = vo[vo > 0]

        def sobre_reticulo(v, paso, tol=0.011):
            """¿v = paso·sqrt(i²+j²) para enteros i,j?"""
            n = (v / paso) ** 2
            return np.abs(n - np.round(n)) <= (2 * np.round(n) + 1) * tol
        cuant[sw] = {
            "n_valores_unicos_web": int(len(vw)),
            "primeros_15_web_km": [round(float(x), 3) for x in vw[:15]],
            "sobre_reticulo_del_sensor_pct_web": round(
                100.0 * float(sobre_reticulo(vw, paso).mean()), 1),
            "sobre_reticulo_del_sensor_pct_osf_maxdist": round(
                100.0 * float(sobre_reticulo(vo, paso).mean()), 1),
            "paso_del_reticulo_km": paso,
            "decimales_publicados": 2}
    R["cuantizacion"] = cuant

    # ── 3. Control de pareo desplazado 6 h sobre el subconjunto bueno ───────
    b = pd.DataFrame(det["detalle"])
    for c in ("dist_pub_km", "d_foco_km"):
        b[c] = pd.to_numeric(b[c], errors="coerce")
    b = b.dropna(subset=["d_foco_km"])
    real = np.abs(b.dist_pub_km.values - b.d_foco_km.values)
    rng = np.random.default_rng(139)
    falso = np.abs(b.dist_pub_km.values[rng.permutation(len(b))] - b.d_foco_km.values)
    R["control_pareo_barajado"] = {
        "n": int(len(b)),
        "nota": "barajar la distancia ENTRE pasadas del mismo conjunto, que es el control "
                "que corresponde: el desplazamiento de 6 h deja muy pocos pares (la mayoría "
                "de los volcanes no tiene otra pasada a esa hora).",
        "abs_dif_mediana_pareo_real_km": round(float(np.median(real)), 3),
        "abs_dif_mediana_barajado_km": round(float(np.median(falso)), 3),
        "dentro_de_0.5km_real_pct": round(100.0 * float((real <= 0.5).mean()), 1),
        "dentro_de_0.5km_barajado_pct": round(100.0 * float((falso <= 0.5).mean()), 1)}

    out = os.path.join(AQUI, "10_falsos_positivos_y_cuantizacion.json")
    R["detalle"] = d.to_dict("records")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    for k in ("_meta", "senal_en_el_crater_por_etiqueta", "falsos_positivos_por_volcan",
              "cuantizacion", "control_pareo_barajado"):
        print()
        print(k.upper())
        print(json.dumps(R[k], ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
