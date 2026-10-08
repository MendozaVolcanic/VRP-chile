"""C02: pareo por pasada de los 11 Tier A contra MIROVA (S150, frente C).

Por que: medir, sobre records reales, que hacen las compuertas de magnitud (tope D9, modo de un
solo pixel, magnitud focal, eleccion del cumulo primario) cuando la senal es fuerte.

Instrumento:
1. Si una compuerta recortara magnitud real, este pareo lo veria: compara pc.vrp_mw contra la
   suma de todos los pixeles alertados dentro del inner_radius (crater_sum, reconstruida de
   anomaly_pixels) y contra el VRP que MIROVA publico en la misma pasada.
2. Si el instrumento estuviera muerto (pareo vacio, horas desfasadas), el numero de pares
   seria 0 y se imprime; el control positivo es el ejemplo conocido 2026-10-01 08:35 MODIS_AQUA
   de Nevados de Chillan (MIROVA 5,18), que debe aparecer pareado.
Limites: anomaly_pixels guarda solo los 100 pixeles de mayor VRP, asi que crater_sum es un piso
cuando n_anomalous_pixels > 100. dist_km de anomaly_pixels mide desde (lat, lon) del volcan.
Referencia: CSV consolidado (tabla, decide) y OCR (aparte), descargados 2026-10-08 de
MendozaVolcanic/Mirova-v1 main. Tolerancia de pareo +-8 min, misma familia de sensor.
Salida: c02_pares.csv (todas las pasadas desde DESDE, pareadas o no).
"""
import csv
import io
import json
import sys
from datetime import datetime, timedelta

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-03-01"
AQUI = "experiments/_s150_audit/C/"
NOMBRE = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}


def familia_nuestra(s):
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS" if s.endswith("_750") else "VIIRS375"


def cargar(fn):
    idx = {}
    for r in csv.DictReader(open(AQUI + fn, encoding="utf-8")):
        if r["Fecha_Satelite_UTC"] < DESDE:
            continue
        if not r["Tipo_Registro"].startswith("ALERTA"):
            continue
        v = NOMBRE.get(r["Volcan"], r["Volcan"])
        t = datetime.strptime(r["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M")
        idx.setdefault((v, r["Sensor"]), []).append((t, float(r["VRP_MW"] or 0), r["Distancia_km"]))
    return idx


def parear(idx, v, fam, t):
    best = None
    for (tm, vrp, dk) in idx.get((v, fam), []):
        dt = abs((tm - t).total_seconds())
        if dt <= 480 and (best is None or dt < best[0]):
            best = (dt, vrp, dk)
    return best


cons = cargar("mirova_consolidado.csv")
ocr = cargar("mirova_ocr.csv")
vols = {x["name"]: x for x in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]
        if x.get("inner_radius_km") is not None}
out = open(AQUI + "c02_pares.csv", "w", newline="", encoding="utf-8")
w = csv.writer(out)
w.writerow(["volcan", "dt", "sensor", "fam", "pc_vrp", "pc_n", "pc_dist", "spm", "focal", "focal_deg",
            "d9", "scene_vrp", "f5", "n_anom", "n_clu", "dclass", "t_bg", "n_nti", "crater_sum",
            "crater_n", "crater_max", "inner", "m_cons", "m_cons_dist", "m_ocr"])
n_par = 0
for v, cfg in vols.items():
    d = json.load(open(f"data/mirova_equivalent/{v}.json", encoding="utf-8"))
    inner = cfg["inner_radius_km"]
    for r in d["records"]:
        if r["datetime_utc"] < DESDE:
            continue
        pc = r.get("primary_cluster")
        if not pc:
            continue
        fam = familia_nuestra(r["sensor"])
        t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        mc = parear(cons, v, fam, t)
        mo = parear(ocr, v, fam, t)
        if mc:
            n_par += 1
        cr = [p for p in r.get("anomaly_pixels", []) if p["dist_km"] <= inner]
        w.writerow([v, r["datetime_utc"], r["sensor"], fam, pc.get("vrp_mw"), pc.get("n_pixels"),
                    pc.get("centroid_dist_km"), pc.get("single_pixel_mode"), pc.get("focal_magnitude"),
                    pc.get("focal_degraded"), pc.get("d9_capped", False), r.get("vrp_mw"),
                    r.get("f5_core_vrp_mw"), r.get("n_anomalous_pixels"), r.get("n_hotspots_clustered"),
                    r.get("distance_class"), r.get("t_bg_k"), r.get("diag_n_nti_path"),
                    round(sum(p["vrp_mw"] for p in cr), 4), len(cr),
                    round(max([p["vrp_mw"] for p in cr], default=0), 4), inner,
                    mc[1] if mc else "", mc[2] if mc else "", mo[1] if mo else ""])
out.close()
print(f"pasadas con primary_cluster pareadas a una ALERTA de la tabla: {n_par} (desde {DESDE})")
