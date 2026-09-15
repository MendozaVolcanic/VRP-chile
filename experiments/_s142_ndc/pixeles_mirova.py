# -*- coding: utf-8 -*-
"""S142 Frente B: cuántas celdas VIIRS 375 m suma MIROVA en cada alerta, reconstruido desde sus GeoTIFF.

POR QUÉ. Nuestra magnitud VIIRS 375 queda ~0,7 de la de MIROVA (S139). Si MIROVA suma más celdas que
nosotros (conteo) o resta un fondo más bajo (fondo) cambia qué hay que corregir. Desde el 14-sep MIROVA
publica el TIF en su grilla UTM nativa de 375 m, así que cada celda del TIF es un píxel de su cálculo.

PROCEDIMIENTO: el de RESULTADOS.md §0, escrito antes de correr este script.
INSTRUMENTO: P1 reproduce los números que S141 transcribió a mano; P2 corre lo mismo en pasadas donde
MIROVA miró y no alertó (control de especificidad).

Entradas (descargadas antes, sólo lectura): _dl_tif/index.csv y _dl_tif/<Volcan>/*.tif (repo
MendozaVolcanic/mirova-tif-archive, remoto); _dl_mirova/registro_vrp_{consolidado,ocr}.csv (repo
MendozaVolcanic/Mirova-v1, remoto); volcanoes.yaml; records de origin/main (git show, sin tocar el árbol).
USO: python experiments/_s142_ndc/pixeles_mirova.py
"""
import csv
import glob
import hashlib
import io
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import yaml
from pyproj import Transformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
K_V375 = 18.0 * 140625.0          # CLAUDE.md, calibración S14
TOL_MW = 0.005                    # redondeo a dos decimales
NOCHE_MED_MAX = 0.2
R_BASE_KM = 0.6
KMAX = 6

# nombre carpeta TIF (MIROVA) -> (nombre en volcanoes.yaml / data, variantes en CSV Mirova-v1, A14)
VOLS = {
    "ChillanNevadosde": ("NevadosDeChillan", {"Nevados de Chillan", "NevadosdeChillan"}),
    "Chaiten": ("Chaiten", {"Chaiten"}),
    "Copahue": ("Copahue", {"Copahue"}),
    "Isluga": ("Isluga", {"Isluga"}),
    "Lascar": ("Lascar", {"Lascar"}),
    "Lastarria": ("Lastarria", {"Lastarria"}),
    "Llaima": ("Llaima", {"Llaima"}),
    "PlanchonPeteroa": ("PlanchonPeteroa", {"PlanchonPeteroa", "Planchon-Peteroa"}),
    "PuyehueCordonCaulle": ("PuyehueCordonCaulle", {"Puyehue-Cordon Caulle", "PuyehueCordonCaulle"}),
    "Tupungatito": ("Tupungatito", {"Tupungatito"}),
    "Villarrica": ("Villarrica", {"Villarrica"}),
}
SENS_375 = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}


def ts(s):
    s = s.strip().replace("T", " ")[:19]
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def cargar_index():
    por_md5, ceros = {}, []
    for r in csv.DictReader(open(HERE / "_dl_tif" / "index.csv", encoding="utf-8")):
        if r["sensor"] != "VIIRS375":
            continue
        if r["size_bytes"] == "0":
            ceros.append({"volcan": r["volcano"], "tif": r["tif_path"], "adquisicion": r["acquisition_utc"]})
        por_md5.setdefault(r["md5"], []).append(r)
    return por_md5, ceros


def cargar_mirova():
    filas = []
    for nombre, fuente in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        for r in csv.DictReader(open(HERE / "_dl_mirova" / nombre, encoding="utf-8")):
            if r["Sensor"] != "VIIRS375":
                continue
            r["_t"] = ts(r["Fecha_Satelite_UTC"])
            r["_src"] = fuente
            filas.append(r)
    return filas


def referencia(filas, variantes, t):
    fs = [f for f in filas if f["Volcan"] in variantes and abs((f["_t"] - t).total_seconds()) <= 60]
    if not fs:
        return None
    alertas = [f for f in fs if f["Tipo_Registro"] in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")]
    zen = next((float(f["Zenith_Sat_deg"]) for f in fs if f.get("Zenith_Sat_deg") not in (None, "")), None)
    if alertas:
        a = next((f for f in alertas if f["_src"] == "CONS"), alertas[0])
        return {"clase": "ALERTA", "vrp_mw": float(a["VRP_MW"]), "dist_km": float(a["Distancia_km"]),
                "fuentes": sorted({f["_src"] + ":" + f["Tipo_Registro"] for f in fs}), "zen_ocr_deg": zen}
    if all(f["Tipo_Registro"] == "RUTINA" and float(f["VRP_MW"] or 0) == 0 for f in fs):
        return {"clase": "CONTROL", "vrp_mw": 0.0, "dist_km": None,
                "fuentes": sorted({f["_src"] + ":" + f["Tipo_Registro"] for f in fs}), "zen_ocr_deg": zen}
    return {"clase": "OTRO", "fuentes": sorted({f["_src"] + ":" + f["Tipo_Registro"] for f in fs})}


def vecinas(r, c, shape):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < shape[0] and 0 <= c + dc < shape[1]:
                yield r + dr, c + dc


def exceso_local(L):
    d = np.full(L.shape, np.nan)
    for r in range(L.shape[0]):
        for c in range(L.shape[1]):
            if not np.isfinite(L[r, c]):
                continue
            v = [L[x] for x in vecinas(r, c, L.shape) if np.isfinite(L[x])]
            if len(v) >= 3:
                d[r, c] = L[r, c] - float(np.mean(v))
    return d


def vrp(L, conj, variante):
    s = set(conj)
    if variante == "BA":
        tot = 0.0
        for cell in conj:
            v = [L[x] for x in vecinas(*cell, L.shape) if x not in s and np.isfinite(L[x])]
            if not v:
                return None
            tot += L[cell] - float(np.mean(v))
    else:
        anillo = {x for cell in conj for x in vecinas(*cell, L.shape) if x not in s and np.isfinite(L[x])}
        if not anillo:
            return None
        bk = float(np.mean([L[x] for x in anillo]))
        tot = sum(L[cell] - bk for cell in conj)
    return K_V375 * tot / 1e6


def crecer(L, d0, semilla):
    conj = [semilla]
    while len(conj) < KMAX:
        s = set(conj)
        cand = {x for cell in conj for x in vecinas(*cell, L.shape) if x not in s and np.isfinite(d0[x])}
        if not cand:
            break
        conj.append(max(cand, key=lambda x: d0[x]))
    return conj


def celda(ds, lat, lon):
    tr = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
    x, y = tr.transform(lon, lat)
    r, c = ds.index(x, y)
    return int(r), int(c)


def records_origin(nombre):
    raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/main:data/mirova_equivalent/{nombre}.json"],
                         capture_output=True, check=True).stdout
    d = json.loads(raw)
    return d["updated"], [r for r in d["records"] if r["sensor"] in SENS_375]


def nuestro(recs, t):
    best = None
    for r in recs:
        dt = abs((ts(r["datetime_utc"] + ":00") - t).total_seconds())
        if dt <= 120 and (best is None or dt < best[0]):
            best = (dt, r)
    if not best:
        return None
    r = best[1]
    pc = r.get("primary_cluster") or {}
    return {"datetime_utc": r["datetime_utc"], "sensor": r["sensor"], "zen_deg": r.get("sensor_zenith_deg"),
            "f5_core_vrp_mw": r.get("f5_core_vrp_mw"), "pc_n_pixels": pc.get("n_pixels"),
            "pc_vrp_mw": pc.get("vrp_mw"), "n_anomalous_pixels": r.get("n_anomalous_pixels"),
            "final_hotspot_dist_km": r.get("final_hotspot_dist_km"), "distance_class": r.get("distance_class"),
            "diag_L_bg_w_m2_sr_um": r.get("diag_L_bg_w_m2_sr_um"),
            "diag_L_bg_local_w_m2_sr_um": r.get("diag_L_bg_local_w_m2_sr_um")}


def main():
    cfg = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    por_md5, ceros = cargar_index()
    mir = cargar_mirova()
    inventario, pasadas = [], []
    for carpeta, (nombre, variantes) in VOLS.items():
        for f in sorted(glob.glob(str(HERE / "_dl_tif" / carpeta / "*_VIIRS375*.tif"))):
            h = md5(f)
            with rasterio.open(f) as ds:
                L = ds.read(1).astype(float)
                epsg = ds.crs.to_epsg()
                dtype = ds.dtypes[0]
            med = float(np.nanmedian(L))
            adq = sorted({r["acquisition_utc"][:19] for r in por_md5.get(h, []) if r["acquisition_utc"]})
            lags = [(ts(r["last_modified_utc"]) - ts(r["acquisition_utc"])).total_seconds() / 3600
                    for r in por_md5.get(h, []) if r["acquisition_utc"]]
            item = {"volcan": carpeta, "archivo": Path(f).name, "md5": h, "epsg": epsg, "dtype": dtype,
                    "mediana_w_m2_sr_um": round(med, 4), "adquisiciones_index": adq,
                    "min_latencia_h": round(min(lags), 2) if lags else None}
            if not (epsg and 32700 < epsg < 32800):
                item["estado"] = "fuera: no UTM"
            elif len(adq) != 1:
                item["estado"] = "fuera: adquisicion ambigua o ausente"
            else:
                t = ts(adq[0])
                noche = 3 <= t.hour < 9
                if not noche or med >= NOCHE_MED_MAX:
                    item["estado"] = f"fuera: no nocturna (hora {t.hour} UTC, mediana {med:.3f})"
                else:
                    item["estado"] = "entra"
                    item["adquisicion"] = adq[0]
            inventario.append(item)
    # una pasada por (volcan, adquisicion): archivos con el mismo md5 son la misma imagen
    vistos = {}
    for it in inventario:
        if it["estado"] == "entra":
            vistos.setdefault((it["volcan"], it["adquisicion"]), it)
    for (carpeta, adq), it in sorted(vistos.items()):
        nombre, variantes = VOLS[carpeta]
        ref = referencia(mir, variantes, ts(adq))
        pasadas.append({"volcan": carpeta, "nombre": nombre, "adquisicion_utc": adq, "archivo": it["archivo"],
                        "epsg": it["epsg"], "min_latencia_h": it["min_latencia_h"], "mirova": ref})
    # radio por volcán (pre-registrado): 0,6 km + mayor distancia de sus alertas nocturnas en la ventana
    rad = {}
    for p in pasadas:
        m = p["mirova"]
        dmax = m["dist_km"] if m and m["clase"] == "ALERTA" else 0.0
        rad[p["volcan"]] = max(rad.get(p["volcan"], 0.0), dmax)
    cache_recs = {}
    for p in pasadas:
        m = p["mirova"]
        if not m or m["clase"] not in ("ALERTA", "CONTROL"):
            p["estado"] = "fuera: sin referencia MIROVA util"
            continue
        v = cfg[p["nombre"]]
        with rasterio.open(HERE / "_dl_tif" / p["volcan"] / p["archivo"]) as ds:
            L = ds.read(1).astype(float)
            ref_cell = celda(ds, v["mirova_center_lat"], v["mirova_center_lon"])
            vent_cell = celda(ds, v["vent_lat"], v["vent_lon"])
            if p["volcan"] == "ChillanNevadosde":   # en volcanoes.yaml vent = GVP; el foco es Nicanor (S124)
                p["celda_nicanor_s124"] = list(celda(ds, -36.867210, -71.378241))
        d0 = exceso_local(L)
        fin = d0[np.isfinite(d0)]
        sigma = 1.4826 * float(np.median(np.abs(fin - np.median(fin))))
        R = R_BASE_KM + rad[p["volcan"]]
        dentro = [(r, c) for r in range(L.shape[0]) for c in range(L.shape[1])
                  if np.isfinite(d0[r, c]) and 0.375 * math.hypot(r - ref_cell[0], c - ref_cell[1]) <= R]
        semilla = max(dentro, key=lambda x: d0[x])
        conj = crecer(L, d0, semilla)
        ks = []
        for k in range(1, len(conj) + 1):
            ks.append({"k": k, "celdas": [list(x) for x in conj[:k]],
                       "vrp_BA_mw": round(vrp(L, conj[:k], "BA"), 4),
                       "vrp_BB_mw": round(vrp(L, conj[:k], "BB"), 4)})
        p.update({
            "celda_referencia_mirova_center": list(ref_cell), "celda_crater": list(vent_cell), "radio_busqueda_km": R,
            "sigma_rob_dL0": sigma, "semilla": list(semilla),
            "semilla_dist_ref_km": round(0.375 * math.hypot(semilla[0] - ref_cell[0], semilla[1] - ref_cell[1]), 3),
            "semilla_dist_crater_km": round(0.375 * math.hypot(semilla[0] - vent_cell[0], semilla[1] - vent_cell[1]), 3),
            "semilla_dL0": float(d0[semilla]), "semilla_z": float(d0[semilla] / sigma), "k": ks, "estado": "ok"})
        if m["clase"] == "ALERTA":
            # POST-HOC (no estaba en §0): fondo común que haría calzar exactamente k celdas con lo publicado
            imp = []
            for k in range(1, len(conj) + 1):
                s = set(conj[:k])
                anillo = {x for cell in conj[:k] for x in vecinas(*cell, L.shape) if x not in s and np.isfinite(L[x])}
                bk_bb = float(np.mean([L[x] for x in anillo]))
                bk_imp = (sum(float(L[c]) for c in conj[:k]) - m["vrp_mw"] * 1e6 / K_V375) / k
                imp.append({"k": k, "bk_implicito": round(bk_imp, 5), "bk_anillo_BB": round(bk_bb, 5),
                            "implicito_menos_anillo": round(bk_imp - bk_bb, 5),
                            "percentil_escena_del_implicito": round(float(np.mean(L[np.isfinite(L)] < bk_imp)) * 100, 1)})
            p["posthoc_fondo_implicito"] = imp
            p["mediana_escena"] = float(np.nanmedian(L))
            for var in ("BA", "BB"):
                p[f"k_compatibles_{var}"] = [x["k"] for x in ks if abs(x[f"vrp_{var}_mw"] - m["vrp_mw"]) <= TOL_MW]
                p[f"k_mas_cercano_{var}"] = min(ks, key=lambda x: abs(x[f"vrp_{var}_mw"] - m["vrp_mw"]))["k"]
        if p["nombre"] not in cache_recs:
            cache_recs[p["nombre"]] = records_origin(p["nombre"])
        p["nuestro_record"] = nuestro(cache_recs[p["nombre"]][1], ts(p["adquisicion_utc"]))
        p["nuestro_json_updated"] = cache_recs[p["nombre"]][0]
    # control P1: celdas de S141 en NdC 15-sep 06:18
    p1 = None
    for p in pasadas:
        if p["volcan"] == "ChillanNevadosde" and p["adquisicion_utc"].replace("T", " ").startswith("2026-09-15 06:18"):
            with rasterio.open(HERE / "_dl_tif" / p["volcan"] / p["archivo"]) as ds:
                L = ds.read(1).astype(float)
            cs = [(68, 66), (67, 66), (68, 67)]
            p1 = {"esperado_s141_mw": [0.030, 0.065, 0.078],
                  "obtenido_BA_mw": [round(vrp(L, cs[:k], "BA"), 4) for k in (1, 2, 3)],
                  "obtenido_BB_mw": [round(vrp(L, cs[:k], "BB"), 4) for k in (1, 2, 3)],
                  "radiancias": [float(L[c]) for c in cs]}
    ok = [p for p in pasadas if p.get("estado") == "ok"]
    al = [p for p in ok if p["mirova"]["clase"] == "ALERTA"]
    co = [p for p in ok if p["mirova"]["clase"] == "CONTROL"]
    resumen = {
        "n_alertas": len(al), "n_controles": len(co),
        "z_semilla_alertas_mediana": statistics.median([p["semilla_z"] for p in al]) if al else None,
        "z_semilla_controles_mediana": statistics.median([p["semilla_z"] for p in co]) if co else None,
        "vrp1_controles_mw": sorted(p["k"][0]["vrp_BA_mw"] for p in co),
        "vrp1_alertas_mw": sorted(p["k"][0]["vrp_BA_mw"] for p in al),
        "controles_con_vrp1_bajo_0p01": sum(p["k"][0]["vrp_BA_mw"] < 0.01 for p in co),
        # POST-HOC: sin los archivos escritos más de 8 h después de la adquisición declarada (la página dice
        # 1-4 h de latencia; varios 06:36/06:42 del 14-sep resultaron escenas diurnas)
        "posthoc_controles_latencia_hasta_8h": {
            "n": sum(1 for p in co if (p["min_latencia_h"] or 0) <= 8),
            "vrp1_mw": sorted(p["k"][0]["vrp_BA_mw"] for p in co if (p["min_latencia_h"] or 0) <= 8),
            "z_mediana": statistics.median([p["semilla_z"] for p in co if (p["min_latencia_h"] or 0) <= 8]) if co else None,
            "excluidos": [(p["volcan"], p["adquisicion_utc"], p["min_latencia_h"]) for p in co if (p["min_latencia_h"] or 0) > 8]},
    }
    out = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "k_v375_w_por_w_m2_sr_um": K_V375, "tol_mw": TOL_MW, "r_base_km": R_BASE_KM,
                    "procedimiento": "RESULTADOS.md seccion 0"},
           "tif_cero_bytes_sin_dato": ceros, "inventario_tif": inventario, "control_P1_s141": p1,
           "pasadas": pasadas, "resumen": resumen}
    (HERE / "pixeles_mirova.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: o.item()), encoding="utf-8")
    for p in ok:
        m = p["mirova"]
        print(p["volcan"], p["adquisicion_utc"], m["clase"], m.get("vrp_mw"), m.get("dist_km"), "zen", m.get("zen_ocr_deg"),
              "seed", p["semilla"], p["semilla_dist_ref_km"], "z %.1f" % p["semilla_z"],
              [(x["k"], x["vrp_BA_mw"], x["vrp_BB_mw"]) for x in p["k"]],
              "compat", p.get("k_compatibles_BA"), p.get("k_compatibles_BB"), "nuestro", p["nuestro_record"])
    for it in inventario:
        if it["estado"] != "entra":
            print("INV", it["volcan"], it["archivo"], it["estado"], it["adquisiciones_index"])
    print("P1", p1)
    print("RESUMEN", resumen)


if __name__ == "__main__":
    main()
