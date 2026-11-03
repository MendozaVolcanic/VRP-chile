# -*- coding: utf-8 -*-
"""v03 (verificador S173 ver_tupun375): nulo medido del brazo «fondo de K con recorte a cero» (afirmacion 3), posicion
de los alertados de la via en las 4 alertas grandes solo OCR (afirmacion 5), e identidad de las grillas duplicadas
entre lotes (A104 sobre las grillas).

POR QUE (A110): el auditor muestra que la via con el t_bg de K (recorte a cero) da 0,415 / 0,246 contra 0,394 / 0,251 de
K. Un instrumento que «reproduce a K» con cualquier fondo no mide el fondo. Aqui el mismo brazo se corre con:
  ANIK_REC      t_bg de K de la MISMA pasada (el brazo del auditor; control de que reproduzco su numero)
  BARAJADO      t_bg de K de OTRA pasada (200 barajados dentro de las 24 pasadas, semilla 173): si las medianas por tramo
                y el acuerdo por pasada con K quedan igual que con el t_bg propio, el brazo no discrimina
  CONSTANTE     fondo = T_fondo_local de la via + 6,86 K (la mediana de Kbg - Tfl del auditor): ¿un desplazamiento
                constante reproduce a K tanto como el t_bg real? (nivel contra pendiente)
  ANIK_SIN_REC  t_bg de K SIN recorte: ¿cuanto de la caida la pone el recorte y cuanto el nivel del fondo?
y se mide el acuerdo POR PASADA: K_disp / brazo, con p10, mediana, p90 y cuantas pasadas quedan entre 0,8 y 1,25.
Control positivo: el fondo CERO (techo) debe dar una razon muy distinta de K.
P2: si las grillas no se leyeran, n seria 0; se imprime n y la ventana.
Uso: python -B v03_nulo_fondo.py <raiz repo> <r03_v375e_pasadas.csv> <r01_k_pasadas.csv> <prefijo salida>
"""
import csv, glob, json, math, os, random, statistics, sys

ROOT, VCSV, KCSV, PRE = sys.argv[1:5]
sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from pyproj import Transformer  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

VOL = "Tupungatito"
LOTES = {"S162": r"C:/vrp-trabajo/temporales/s162_v375/run_40116289866",
         "S162b": r"C:/vrp-trabajo/temporales/s162_v375/run_40131572769",
         "S159": r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945",
         "FAR": r"D:/vrp-trabajo/temporales/s167_v375e_far/run_40773794395"}
PLAT = {"VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}
FAM = MV.FAMILIAS["VIIRS375"]
LAM, COEF = FAM["lam_mir"], FAM["coef"]
SEMILLA, NB, CORTE = 173, 200, 30.0
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def f(x):
    try:
        y = float(x)
        return None if math.isnan(y) else y
    except (TypeError, ValueError):
        return None


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    if len(x) < 4:
        return None
    a, b = rank(x), rank(y)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return None if den == 0 else num / den


def rad(T):
    return float(MV.temperatura_a_radiancia(np.array([T]), LAM)[0])


v = [x for x in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"] if x["name"] == VOL][0]
vent_lat, vent_lon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
g = MV.grilla_del_volcan(VOL, paso_m=375.0, clave_roi="roi_v375")
box = MV.caja_v375(g, vent_lat, vent_lon, lado_sensible=13, half_roi1_m=MV.HALF_ROI1_V375_M)
pos = MV.posicion_de(g, vent_lat, vent_lon)
n, paso = int(g["n"]), float(g["paso"])
X, Y = np.meshgrid(g["ul_x"] + paso * (np.arange(n) + 0.5), g["ul_y"] - paso * (np.arange(n) + 0.5))
lo_, la_ = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True).transform(X, Y)
la_, lo_ = np.asarray(la_), np.asarray(lo_)

V = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(VCSV, encoding="utf-8"))}
K = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}

filas, vistas, dup = [], {}, []
for lote, base in LOTES.items():
    for fn in glob.glob(os.path.join(base, "**", "resultados_VIIRS375*.json"), recursive=True):
        for x in json.load(open(fn, encoding="utf-8")):
            if x.get("volcan") != VOL or x.get("estado") != "ok":
                continue
            sensor = PLAT[x["granule"][:3]]
            clave = (sensor, x["hora_utc"])
            gz = os.path.join(os.path.dirname(fn), f"grilla_{x['id']}.npz")
            if not os.path.exists(gz):
                continue
            d = np.load(gz)
            mir, tir = np.asarray(d["mir"], float), np.asarray(d["tir"], float)
            if clave in vistas:
                # A104 sobre las grillas: ¿la misma pasada en dos lotes da la MISMA grilla?
                m0 = vistas[clave]
                igual = np.array_equal(np.nan_to_num(m0["mir"], nan=-1), np.nan_to_num(mir, nan=-1))
                dmax = float(np.nanmax(np.abs(m0["mir"] - mir))) if m0["mir"].shape == mir.shape else None
                dup.append({"clave": clave, "lotes": [m0["lote"], lote], "granulos": [m0["granule"], x["granule"]], "mir_identica": bool(igual), "dif_max": dmax})
                continue
            vistas[clave] = {"lote": lote, "mir": mir, "granule": x["granule"]}
            rec = MV.procesar_grilla(mir, tir, g, box, x["dayflag"], x["sunglint"], pos, v["inner_radius_km"], sensor, familia="VIIRS375")
            kr, vr = K.get(clave) or {}, V.get(clave) or {}
            z = f(vr.get("K_z")) if f(vr.get("K_z")) is not None else (x.get("geometria_centro") or {}).get("sensor_zenith")
            fila = {"sensor": sensor, "dt": x["hora_utc"], "lote": lote, "granule": x["granule"], "z": z, "vrp_M": f(vr.get("vrp_M")), "src_M": vr.get("src_M"),
                    "K_pub": kr.get("pub"), "K_disp": f(kr.get("disp")), "K_t_bg": f(kr.get("t_bg")), "via_dc": rec.get("distance_class"),
                    "npix": int(rec.get("n_anomalous_pixels") or 0), "vrp_via": f(rec.get("vrp_mw")), "Tfl": f(rec.get("t_bg_k"))}
            if fila["npix"]:
                m = np.zeros_like(mir, bool)
                px = []
                for p in rec["anomaly_pixels"]:
                    m[p["fila"], p["col"]] = True
                    la, lo = float(la_[p["fila"], p["col"]]), float(lo_[p["fila"], p["col"]])
                    dist = float(MV._haversine(np.array([la]), np.array([lo]), vent_lat, vent_lon)[0])
                    brg = math.degrees(math.atan2(math.sin(math.radians(lo - vent_lon)) * math.cos(math.radians(la)),
                                                  math.cos(math.radians(vent_lat)) * math.sin(math.radians(la)) - math.sin(math.radians(vent_lat)) * math.cos(math.radians(la)) * math.cos(math.radians(lo - vent_lon)))) % 360
                    px.append({"lat": round(la, 4), "lon": round(lo, 4), "dist_km": round(dist, 2), "rumbo": round(brg), "bt": round(float(MV.radiancia_a_temperatura(np.array([mir[p["fila"], p["col"]]]), LAM)[0]), 1)})
                fila["Lm"] = mir[m].tolist()
                fila["px"] = px
            filas.append(fila)

pr(f"pasadas unicas con grilla: {len(filas)}; con alertados: {sum(1 for x in filas if x['npix'])}; duplicadas entre lotes: {len(dup)}")
for d in dup:
    pr(f"  duplicada {d}")

B = [x for x in filas if x["npix"] and x["vrp_M"] and x["vrp_M"] > 0 and x["via_dc"] == "summit" and x["K_t_bg"]]
pr(f"B (summit de la via, alerta MIROVA > 0, con t_bg de K): n {len(B)}; ventana {min(x['dt'] for x in B)} a {max(x['dt'] for x in B)}")


def brazo(x, T_bg, recorte=True):
    ex = np.array(x["Lm"]) - rad(T_bg)
    return float(np.sum(np.maximum(ex, 0) if recorte else ex)) * COEF


def estr(nom, vals):
    """vals: lista de (z, razon)."""
    z = [a for a, _ in vals]
    r = [b for _, b in vals]
    s = spearman(z, r)
    pr(f"  {nom:34s} n {len(vals):3d} med {med(r)}  z<30 {med([b for a, b in vals if a < CORTE])} ({sum(1 for a in z if a < CORTE)})  "
       f"z>=30 {med([b for a, b in vals if a >= CORTE])} ({sum(1 for a in z if a >= CORTE)})  Spearman {s:+.3f}" if s is not None else f"  {nom} n {len(vals)}")
    return {"n": len(vals), "mediana": med(r), "z<30": med([b for a, b in vals if a < CORTE]), "z>=30": med([b for a, b in vals if a >= CORTE]), "spearman": round(s, 3) if s is not None else None}


def acuerdo(nom, vals):
    """vals: lista de K/brazo por pasada."""
    vals = [q for q in vals if q is not None and math.isfinite(q)]
    if not vals:
        pr(f"  acuerdo {nom}: SIN DATO")
        return None
    a = np.array(vals)
    out = {"n": len(a), "p10": round(float(np.percentile(a, 10)), 3), "mediana": round(float(np.median(a)), 3), "p90": round(float(np.percentile(a, 90)), 3),
           "entre_0.8_y_1.25": int(np.sum((a >= 0.8) & (a <= 1.25))), "log_rms": round(float(np.sqrt(np.mean(np.log(a) ** 2))), 3)}
    pr(f"  acuerdo por pasada K/{nom}: {out}")
    return out


res = {"n_B": len(B)}
pr("== brazos sobre la mascara de la via (B), razon contra MIROVA")
res["VIA"] = estr("VIA (fondo propio, sin recorte)", [(x["z"], x["vrp_via"] / x["vrp_M"]) for x in B])
res["K_prod"] = estr("K produccion (mismas, publicada)", [(x["z"], x["K_disp"] / x["vrp_M"]) for x in B if x["K_pub"] == "1" and x["K_disp"] and x["K_disp"] > 0])
res["ANIK_REC"] = estr("ANIK_REC (t_bg K propio, recorte)", [(x["z"], brazo(x, x["K_t_bg"]) / x["vrp_M"]) for x in B])
res["ANIK_SIN_REC"] = estr("ANIK_SIN_REC (t_bg K, sin recorte)", [(x["z"], brazo(x, x["K_t_bg"], False) / x["vrp_M"]) for x in B])
off = med([x["K_t_bg"] - x["Tfl"] for x in B])
res["offset_K_menos_Tfl"] = off
res["CONST"] = estr(f"CONST (Tfl + {off} K, recorte)", [(x["z"], brazo(x, x["Tfl"] + off) / x["vrp_M"]) for x in B])
res["CERO"] = estr("CERO (fondo 0, techo)", [(x["z"], float(np.sum(x["Lm"])) * COEF / x["vrp_M"]) for x in B])
pr("== acuerdo por pasada con K (solo pasadas con K publicada > 0 y brazo > 0)")
Bk = [x for x in B if x["K_pub"] == "1" and x["K_disp"] and x["K_disp"] > 0]
res["acuerdo_ANIK_REC"] = acuerdo("ANIK_REC", [x["K_disp"] / brazo(x, x["K_t_bg"]) if brazo(x, x["K_t_bg"]) > 0 else None for x in Bk])
res["acuerdo_CONST"] = acuerdo("CONST", [x["K_disp"] / brazo(x, x["Tfl"] + off) if brazo(x, x["Tfl"] + off) > 0 else None for x in Bk])
res["acuerdo_VIA"] = acuerdo("VIA", [x["K_disp"] / x["vrp_via"] for x in Bk])
pr(f"  ceros del brazo ANIK_REC (exceso recortado a 0 en todas las alertadas): {sum(1 for x in B if brazo(x, x['K_t_bg']) == 0)} de {len(B)}; en K publicada: {sum(1 for x in Bk if brazo(x, x['K_t_bg']) == 0)} de {len(Bk)}")

pr("== NULO: t_bg de K de OTRA pasada (200 barajados, semilla 173), medianas por tramo y acuerdo por pasada")
rnd = random.Random(SEMILLA)
tb = [x["K_t_bg"] for x in B]
bl, bh, bm, ac_med, ac_in = [], [], [], [], []
for _ in range(NB):
    tt = list(tb)
    rnd.shuffle(tt)
    vals = [(x["z"], brazo(x, t) / x["vrp_M"]) for x, t in zip(B, tt)]
    bl.append(med([b for a, b in vals if a < CORTE]))
    bh.append(med([b for a, b in vals if a >= CORTE]))
    bm.append(med([b for _, b in vals]))
    q = [x["K_disp"] / brazo(x, t) for x, t in zip(B, tt) if x["K_pub"] == "1" and x["K_disp"] and x["K_disp"] > 0 and brazo(x, t) > 0]
    ac_med.append(float(np.median(q)) if q else None)
    ac_in.append(sum(1 for y in q if 0.8 <= y <= 1.25))


def q95(a):
    a = sorted(x for x in a if x is not None)
    return [round(a[int(0.025 * len(a))], 3), round(statistics.median(a), 3), round(a[int(0.975 * len(a)) - 1], 3)]


res["nulo_barajado"] = {"mediana_total_[2.5,50,97.5]": q95(bm), "z<30": q95(bl), "z>=30": q95(bh), "acuerdo_mediana_K/brazo": q95(ac_med), "acuerdo_entre_0.8_1.25": q95(ac_in)}
pr(f"  barajado: mediana total {q95(bm)}; z<30 {q95(bl)}; z>=30 {q95(bh)}; acuerdo mediana K/brazo {q95(ac_med)}; pasadas entre 0,8 y 1,25 {q95(ac_in)} (real: {res['acuerdo_ANIK_REC']['entre_0.8_y_1.25'] if res['acuerdo_ANIK_REC'] else None} de {len(Bk)})")
pr(f"  real ANIK_REC: total {res['ANIK_REC']['mediana']} z<30 {res['ANIK_REC']['z<30']} z>=30 {res['ANIK_REC']['z>=30']}")

pr("== por pasada (B): z, M, VIA, ANIK_REC, CONST, K, K/ANIK_REC, K/CONST, Kt_bg - Tfl")
res["detalle"] = []
for x in sorted(B, key=lambda y: y["z"]):
    a, c = brazo(x, x["K_t_bg"]), brazo(x, x["Tfl"] + off)
    d = {"dt": x["dt"], "sensor": x["sensor"], "z": x["z"], "M": x["vrp_M"], "VIA": round(x["vrp_via"], 3), "ANIK_REC": round(a, 3), "CONST": round(c, 3), "K": x["K_disp"],
         "K/ANIK_REC": round(x["K_disp"] / a, 2) if x["K_disp"] and a > 0 else None, "K/CONST": round(x["K_disp"] / c, 2) if x["K_disp"] and c > 0 else None, "Kbg-Tfl": round(x["K_t_bg"] - x["Tfl"], 2), "npix": x["npix"]}
    res["detalle"].append(d)
    pr("  " + json.dumps(d, ensure_ascii=False))

pr("== afirmacion 5: alertados de la via en las alertas de MIROVA con via de clase far (posicion, rumbo desde el crater)")
res["far"] = []
for x in filas:
    if x["npix"] and x["vrp_M"] and x["vrp_M"] > 0 and x["via_dc"] != "summit":
        d = {"dt": x["dt"], "sensor": x["sensor"], "z": x["z"], "M": x["vrp_M"], "src_M": x["src_M"], "VIA": round(x["vrp_via"], 3), "via_dc": x["via_dc"], "K_disp": x["K_disp"], "px": x["px"]}
        res["far"].append(d)
        pr("  " + json.dumps(d, ensure_ascii=False))
json.dump(res, open(PRE + "_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
open(PRE + "_salida.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
