# -*- coding: utf-8 -*-
"""Verificador S159, frente pareo MODIS en el borde del granulo. Script propio, no reusa el pareo del informe.

Pregunta 1 (lo veria?): si MIROVA eligiera el granulo por orden de llegada (el ultimo o el primero), Terra
y Aqua darian lados opuestos; si eligiera el granulo caliente, sus alertas caerian en ambos lados. Separo
por plataforma y miro el lado de las alertas.
Pregunta 2 (instrumento muerto?): controles: (a) noche de todos los records por cenit solar; (b) el indicador
de fraccion del anillo se valida contra un indicador independiente: el miembro que trae un cumulo a menos de
3 km del crater DEBE tener fraccion >= 0,5 si el indicador mide donde esta el crater.
Uso: python -I verif_pareo.py <espejo>   (espejo = git archive de origin/main con data, scripts, pipeline)
"""
import collections, json, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR

VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def bucket(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"


def alerta(t):
    return t.startswith("ALERTA") and t != "ALERTA_SIN_GEOMETRIA_OCR"


filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
ref = collections.defaultdict(lambda: collections.defaultdict(list))
primera = {}
for f in filas:
    t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
    ref[(f["volcano"], f["sensor_bucket"])][t].append(f)
    k = (f["volcano"], f["sensor_bucket"])
    primera[k] = min(primera.get(k, t), t)
primera_vol = {}
for (v, b), t in primera.items():
    primera_vol[v] = min(primera_vol.get(v, t), t)


def filas_cerca(vol, b, t, seg):
    out = []
    for dm in range(-(seg // 60), seg // 60 + 1):
        out += [(dm, f) for f in ref[(vol, b)].get(t + timedelta(minutes=dm), [])]
    return out

# ---------------- 0. noche de todos los records
dia = collections.Counter(); tot = collections.Counter()
recs = {}
for vol in VOLS:
    rr = json.load(open(RAIZ / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    recs[vol] = rr
    for r in rr:
        b = bucket(r["sensor"]); tot[b] += 1
        sz = r.get("solar_zenith_deg")
        if sz is None or sz < 90: dia[(b, "sz<90 o None")] += 1
print("0. records con cenit solar < 90 o sin dato:", dict(dia), "de", dict(tot))

# ---------------- 1. censo MODIS en ventana con referencia
cat = collections.Counter(); cat2 = collections.Counter(); solo_vec = []
for vol in VOLS:
    d = collections.defaultdict(dict)
    for r in recs[vol]:
        d[r["sensor"]][datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")] = r
    for sensor, dd in d.items():
        b = bucket(sensor)
        if b != "MODIS": continue
        for t, r in dd.items():
            for nombre, ini in (("desde_1a_fila_vol", primera_vol.get(vol)), ("desde_1a_fila_MODIS", primera.get((vol, b)))):
                if ini is None or t < ini.replace(hour=0, minute=0) or t.date() > datetime(2026, 10, 21).date():
                    continue
                c = cat if nombre == "desde_1a_fila_vol" else cat2
                if filas_cerca(vol, b, t, 120):
                    c["pareo_120"] += 1
                elif filas_cerca(vol, b, t, 300):
                    c["solo_vecino_5min"] += 1
                    if nombre == "desde_1a_fila_vol":
                        fv = filas_cerca(vol, b, t, 300)
                        dms = sorted({dm for dm, _ in fv})
                        tiene_otro = any((t + timedelta(minutes=dm)) in dd for dm in dms)
                        solo_vec.append({"vol": vol, "sensor": sensor, "t": t, "dms": dms, "otro": tiene_otro,
                                         "tipos": [f["tipo"] for _, f in fv],
                                         "vrp": [f["vrp_mw"] for _, f in fv],
                                         "n_bg": r.get("diag_n_bg_anillo"), "dc": r.get("distance_class"),
                                         "pc": (r.get("primary_cluster") or {}).get("vrp_mw")})
                elif filas_cerca(vol, b, t, 600):
                    c["entre_5_y_10min"] += 1
                else:
                    c["sin_fila_10min"] += 1
                c["total"] += 1
print("1. MODIS (ventana desde la 1a fila del volcan, cualquier sensor):", dict(cat))
print("   MODIS (ventana desde la 1a fila MODIS del volcan):", dict(cat2))
print("   solo_vecino: con record nuestro en el granulo de MIROVA:", sum(x["otro"] for x in solo_vec),
      "sin:", sum(not x["otro"] for x in solo_vec))
print("   tipos en solo_vecino:", collections.Counter(tuple(sorted(set(x["tipos"]))) for x in solo_vec))
print("   max VRP MIROVA en solo_vecino:", max(max(x["vrp"] or [0]) for x in solo_vec))
sin_otro = [x for x in solo_vec if not x["otro"]]
print("   los sin otro record, por volcan:", collections.Counter(x["vol"] for x in sin_otro))
for x in sin_otro:
    if x["vol"] == "NevadosDeChillan":
        print("    Chillan:", x["t"], x["sensor"], x["dms"], x["tipos"], "n_bg", x["n_bg"], x["dc"], x["pc"])

# ---------------- 2. pasadas partidas: que granulo lista MIROVA
SUR_POSTERIOR = {"MODIS_TERRA": False}
lados = collections.Counter(); fr = collections.defaultdict(list); val = collections.Counter()
alert_lado = collections.Counter(); norte = []; pares_sin_ref = collections.Counter()
reg_partidas = []
for vol in VOLS:
    d = collections.defaultdict(dict)
    for r in recs[vol]:
        d[r["sensor"]][datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")] = r
    for sensor, dd in d.items():
        b = bucket(sensor); p = timedelta(minutes=5 if b == "MODIS" else 6)
        plat = sensor.replace("_750", "")
        for t, r1 in dd.items():
            r2 = dd.get(t + p)
            if r2 is None: continue
            n1, n2 = r1.get("diag_n_bg_anillo") or 0, r2.get("diag_n_bg_anillo") or 0
            # validacion del indicador con un cumulo cerca del crater (independiente del anillo)
            for rx, nx in ((r1, n1), (r2, n2)):
                pc = rx.get("primary_cluster") or {}
                dist = pc.get("centroid_dist_km")
                if dist is not None and dist < 3 and (pc.get("vrp_mw") or 0) > 0 and n1 + n2 > 0:
                    val[(b, "frac>=0.5" if nx / (n1 + n2) >= 0.5 else "frac<0.5")] += 1
            m1 = bool(ref[(vol, b)].get(t)); m2 = bool(ref[(vol, b)].get(t + p))
            if t < primera.get((vol, b), datetime(2100, 1, 1)):
                pares_sin_ref[(b, "antes de la referencia")] += 1; continue
            if m1 and m2: lados[(b, "los dos")] += 1; continue
            if not (m1 or m2): pares_sin_ref[(b, "ninguno, en ventana")] += 1; continue
            if n1 + n2 == 0: continue
            sp = SUR_POSTERIOR.get(plat, True)
            sur = (m2 and sp) or (m1 and not sp)
            lados[(b, plat, "sur" if sur else "norte")] += 1
            fm = (n1 if m1 else n2) / (n1 + n2)
            tipos = [x["tipo"] for x in ref[(vol, b)][t if m1 else t + p]]
            cl = "alerta" if any(alerta(x) for x in tipos) else "otro"
            fr[(b, cl)].append(fm)
            if cl == "alerta": alert_lado[(b, "sur" if sur else "norte")] += 1
            if not sur: norte.append((vol, sensor, str(t), round(fm, 2), tipos))
            reg_partidas.append({"vol": vol, "b": b, "plat": plat, "t": str(t), "sur": sur, "fm": fm, "cl": cl})
print("2. lados por plataforma:", {k: v for k, v in sorted(lados.items())})
print("   pares fuera:", dict(pares_sin_ref))
print("   lado de las alertas:", dict(alert_lado))
for k in sorted(fr):
    v = fr[k]
    print("  ", k, "n", len(v), "mediana", round(statistics.median(v), 3), "bajo 0,5:", sum(x < 0.5 for x in v))
print("   casos en que MIROVA lista el norte:", norte)
print("   VALIDACION indicador (miembro con cumulo <3 km del crater):", dict(val))
# alertas por volcan
print("   alertas por volcan:", collections.Counter(x["vol"] for x in reg_partidas if x["cl"] == "alerta"))
# Terra / Aqua en MODIS por separado, fraccion en RUTINA
for plat in ("MODIS_TERRA", "MODIS_AQUA"):
    v = [x["fm"] for x in reg_partidas if x["plat"] == plat and x["cl"] == "otro"]
    print("   ", plat, "RUTINA n", len(v), "mediana fm", round(statistics.median(v), 3), "bajo 0,5", sum(x < 0.5 for x in v))
json.dump({"solo_vecino": [{**x, "t": str(x["t"])} for x in solo_vec], "partidas": reg_partidas},
          open(Path(__file__).with_name("verif_pareo_salida.json"), "w", encoding="utf-8"), indent=1, default=str)
