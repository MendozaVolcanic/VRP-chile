"""Instrumento propio del verificador 2 (C2). NO importa vigilancia_sombra ni referencia_mirova_unificada
ni clase_mirova ni auto_audit_weekly para la lógica: lee los dos CSV con csv, normaliza nombres a mano,
calcula la elevación solar con su propia fórmula (NOAA simplificada) y parea a +-120 s. Del repo usa sólo
banco_paridad.cargar_nuestros para el predicado del tablero (node), que es lo que se quiere medir.

Uso: python instrumento_propio.py <raiz> <ref> [corte_adopcion 'YYYY-MM-DD HH:MM:SS']
"""
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

raiz, ref = sys.argv[1:3]
ADOP = datetime.strptime(sys.argv[3] if len(sys.argv) > 3 else "2026-10-18 09:57:30",
                         "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
FRONT, HOY = "2026-09-18", "2026-10-19"
sys.path.insert(0, raiz)
sys.path.insert(0, os.path.join(raiz, "scripts"))
os.chdir(raiz)
import yaml  # noqa: E402

NOMBRES = {"lascar": "Lascar", "lastarria": "Lastarria", "isluga": "Isluga", "tupungatito": "Tupungatito",
           "planchonpeteroa": "PlanchonPeteroa", "nevadosdechillan": "NevadosDeChillan",
           "copahue": "Copahue", "llaima": "Llaima", "villarrica": "Villarrica", "chaiten": "Chaiten",
           "puyehuecordoncaulle": "PuyehueCordonCaulle"}
SENS = {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750", "MODIS": "MODIS"}
ALERTA = {"ALERTA_TERMICA", "ALERTA_TERMICA_OCR"}


def norm(v):
    return NOMBRES["".join(ch for ch in v.lower() if ch.isalnum())]


coords = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]
          if "lat" in v}


def elev_solar(lat, lon, dt):
    # NOAA simplificada: declinación y ecuación del tiempo por día del año
    n = dt.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1 + (dt.hour - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = dt.hour * 60 + dt.minute + dt.second / 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cosz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1, min(1, cosz))))


pasadas = defaultdict(list)
for fn in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    for r in csv.DictReader(open(os.path.join(ref, fn), encoding="utf-8")):
        if r["Tipo_Registro"] not in ALERTA:
            continue
        f = r["Fecha_Satelite_UTC"]
        if not (FRONT <= f[:10] <= HOY):
            continue
        try:
            vrp = float(r["VRP_MW"])
        except ValueError:
            continue
        vol, s = norm(r["Volcan"]), SENS[r["Sensor"]]
        dt = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if elev_solar(*coords[vol], dt) > 0:
            continue
        pasadas[(vol, s, f[:16])].append((dt, vrp, fn[13:16]))

import banco_paridad as bp  # noqa: E402  sólo para el predicado del tablero

inner = bp.inner_desde_html()
win = (FRONT, HOY)
prod = bp.cargar_nuestros(coords, inner, win)
sombra = bp.cargar_nuestros(coords, inner, win, data=os.path.join(raiz, "data", "experimental_v2"))


def mira(recs, vol, s, dt):
    c = [r for r in recs if r["vol"] == vol and r["b"] == s and abs((r["dt"] - dt).total_seconds()) <= 120]
    return None if not c else any(r["pub"] for r in c)


res = defaultdict(lambda: defaultdict(int))
casos = []
for (vol, s, minuto), fs in sorted(pasadas.items()):
    vmax = max(v for _, v, _ in fs)
    if vmax < 1.0:
        continue
    dt = fs[0][0]
    tramo = "post" if dt >= ADOP else "retro"
    pp, sp = mira(prod, vol, s, dt), mira(sombra, vol, s, dt)
    res[tramo]["protegidas"] += 1
    res[tramo]["con_sombra"] += sp is not None
    res[tramo]["prod_sin_record"] += pp is None
    if sp is True and pp is False:
        res[tramo]["sombra_si_prod_no"] += 1
        casos.append((tramo, vol, s, minuto, vmax, [x[2] for x in fs]))
    if sp is True and pp is None:
        res[tramo]["sombra_si_prod_sin_record"] += 1
        casos.append((tramo + "_PRODNONE", vol, s, minuto, vmax, [x[2] for x in fs]))
for t, d in res.items():
    print(t, dict(d))
for c in casos:
    print("  caso:", c)
print("sombra hasta:", max(r["noche"] for r in sombra), "n sombra:", len(sombra), "n prod:", len(prod))
