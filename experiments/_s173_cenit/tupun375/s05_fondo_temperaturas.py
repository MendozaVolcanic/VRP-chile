# -*- coding: utf-8 -*-
"""s05 (S173 tupun375): ¿el fondo de K explica el NIVEL o la PENDIENTE del déficit de Tupungatito VIIRS 375?

FENÓMENO. Tupungatito es una cumbre de 5.600 m con glaciar y un lago cratérico con fumarolas; los valles a 5-25 km son
más bajos y más tibios de noche. K toma como fondo la mediana de la BT MIR (I4) del anillo de 5 a 25 km alrededor de
volcano lat/lon (process_viirs.py:812 y :839, BG 5-25 km del perfil) y recorta el exceso a cero; la vía de MIROVA
interpola el fondo bajo los alertados desde sus vecinos, fuera de un halo (vrp_mirova, mirova_v750_codigo.py:584).
Si el anillo es más tibio que la cumbre, K le resta al foco débil un fondo que no es el suyo: pierde magnitud
(nivel). Si además, de lado, el foco se diluye en un píxel más grande y queda cerca o bajo la mediana del anillo, el
recorte lo borra (pendiente, el mecanismo de Chillán).

MEDICIÓN. Sobre las grillas fijas de 375 m de los lotes retrospectivos (S159, S162, S162b, FAR; las mismas de s03) y
con la máscara de alertados de la vía (record de procesar_grilla, filas/columnas), se calcula por pasada:
  T_cumbre  mediana BT I4 de las celdas a <= 2 km del cráter (vent_lat/lon de volcanoes.yaml)
  T_anillo  mediana BT I4 de las celdas a 5-25 km de volcano lat/lon (el anillo de K, aquí sobre la grilla)
  T_alert   media BT de las alertadas; T_fondo_local = t_bg_k del record de la vía (fondo del .m bajo los alertados)
y tres brazos de magnitud con la MISMA máscara (sólo cambia el fondo):
  VIA        fondo local de la vía, sin recorte (debe reproducir vrp_mw del record: control P1)
  ANI_REC    fondo = radiancia de T_anillo, exceso recortado a cero (el fondo de K, D25)
  ANI        fondo = radiancia de T_anillo, sin recorte
  CERO       fondo cero (techo; control positivo: debe ser mayor que VIA en todas)
Razón de cada brazo contra MIROVA (misma pasada, U con D-9 SN, CONS si existe) por tramo de cenit, Spearman + barajado.
Advertencia: el anillo sobre la grilla no es idéntico al anillo de K sobre el barrido nativo (otra geometría); se
imprime la comparación con el t_bg del record K de producción de la misma pasada (control de que el anillo es el de K).

P1: VIA re-calculado contra vrp_mw del record (diferencia máxima impresa); CERO >= VIA en todas.
P2: si el anillo fuera igual al fondo local, ANI y VIA darían lo mismo y T_anillo - T_fondo_local sería 0; se imprime.
Uso: python -B s05_fondo_temperaturas.py <raiz copia main> <s03_v375e_pasadas.csv> <s01_k_pasadas.csv> <prefijo salida>
"""
import csv, glob, json, math, os, random, statistics, sys

ROOT, VCSV, KCSV, PRE = sys.argv[1:5]
sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from pyproj import Transformer  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402

VOL = os.environ.get("VOL_S173", "Tupungatito")
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


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def estrato(z, r):
    out = {"n": len(z), "mediana": med(r), "z<30": [med([b for a, b in zip(z, r) if a < CORTE]), sum(1 for a in z if a < CORTE)],
           "z>=30": [med([b for a, b in zip(z, r) if a >= CORTE]), sum(1 for a in z if a >= CORTE)]}
    if len(z) < 8:
        out["spearman"] = "SIN DATO (n < 8)"
        return out
    s = spearman(z, r)
    rnd = random.Random(SEMILLA)
    sb = []
    for _ in range(NB):
        zz = list(z)
        rnd.shuffle(zz)
        sb.append(spearman(zz, r))
    sb = sorted(x for x in sb if x is not None)
    lo, hi = sb[int(0.025 * len(sb))], sb[int(0.975 * len(sb)) - 1]
    out.update({"spearman": round(s, 3), "barajado_95": [round(lo, 3), round(hi, 3)], "fuera": not (lo <= s <= hi)})
    return out


def bt(Lr):
    return MV.radiancia_a_temperatura(np.asarray(Lr, float), LAM)


v = [x for x in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"] if x["name"] == VOL][0]
vent_lat, vent_lon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
g = MV.grilla_del_volcan(VOL, paso_m=375.0, clave_roi="roi_v375")
box = MV.caja_v375(g, vent_lat, vent_lon, lado_sensible=13, half_roi1_m=MV.HALF_ROI1_V375_M)
pos = MV.posicion_de(g, vent_lat, vent_lon)
n, paso = int(g["n"]), float(g["paso"])
X, Y = np.meshgrid(g["ul_x"] + paso * (np.arange(n) + 0.5), g["ul_y"] - paso * (np.arange(n) + 0.5))
lo_, la_ = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True).transform(X, Y)
d_cent = MV._haversine(np.asarray(la_), np.asarray(lo_), v["lat"], v["lon"])
d_vent = MV._haversine(np.asarray(la_), np.asarray(lo_), vent_lat, vent_lon)
ANI = (d_cent >= 5.0) & (d_cent <= 25.0)
CUM = d_vent <= 2.0
pr(f"grilla {n}x{n} paso {paso} m EPSG {g['epsg']}; celdas anillo 5-25 km {int(ANI.sum())}; celdas cumbre <=2 km {int(CUM.sum())}")

V = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(VCSV, encoding="utf-8"))}
K = {(r["sensor"], r["dt"]): r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"}

filas, vistas = [], set()
for lote, base in LOTES.items():
    for fn in glob.glob(os.path.join(base, "**", "resultados_VIIRS375*.json"), recursive=True):
        for x in json.load(open(fn, encoding="utf-8")):
            if x.get("volcan") != VOL or x.get("estado") != "ok":
                continue
            sensor = PLAT[x["granule"][:3]]
            clave = (sensor, x["hora_utc"])
            if clave in vistas:
                continue
            gz = os.path.join(os.path.dirname(fn), f"grilla_{x['id']}.npz")
            if not os.path.exists(gz):
                continue
            vistas.add(clave)
            d = np.load(gz)
            mir, tir = np.asarray(d["mir"], float), np.asarray(d["tir"], float)
            rec = MV.procesar_grilla(mir, tir, g, box, x["dayflag"], x["sunglint"], pos, v["inner_radius_km"], sensor, familia="VIIRS375")
            btm = bt(mir)
            t_cum = float(np.nanmedian(btm[CUM & np.isfinite(btm)]))
            t_ani = float(np.nanmedian(btm[ANI & np.isfinite(btm)]))
            L_ani = float(MV.temperatura_a_radiancia(np.array([t_ani]), LAM)[0])
            kr = K.get(clave) or {}
            vr = V.get(clave) or {}
            fila = {"sensor": sensor, "dt": x["hora_utc"], "lote": lote, "z": f(vr.get("K_z")) if f(vr.get("K_z")) is not None else (x.get("geometria_centro") or {}).get("sensor_zenith"),
                    "T_cumbre": t_cum, "T_anillo_grilla": t_ani, "anillo_menos_cumbre": t_ani - t_cum,
                    "K_t_bg_prod": f(kr.get("t_bg")), "K_t_max_prod": f(kr.get("t_max")), "K_pub": kr.get("pub"), "K_disp": f(kr.get("disp")),
                    "K_n_pos": f(kr.get("n_pos")), "K_pc_n": f(kr.get("pc_n")),
                    "vrp_M": f(vr.get("vrp_M")), "src_M": vr.get("src_M"), "via_pub": vr.get("via_pub"), "via_dc": rec.get("distance_class"),
                    "npix_via": int(rec.get("n_anomalous_pixels") or 0), "vrp_via_rec": f(rec.get("vrp_mw"))}
            if fila["npix_via"]:
                m = np.zeros_like(mir, bool)
                for p in rec["anomaly_pixels"]:
                    m[p["fila"], p["col"]] = True
                via = MV.vrp_mirova(mir, m, coef=COEF)
                exc_ani = mir[m] - L_ani
                ta = bt(mir[m])
                fila.update({"T_alert_media": float(np.mean(ta)), "T_alert_max": float(np.max(ta)), "T_fondo_local": f(rec.get("t_bg_k")),
                             "anillo_menos_local": t_ani - f(rec.get("t_bg_k")), "alert_sobre_anillo": int(np.sum(exc_ani > 0)),
                             "VIA": via["VRP_MW"], "ANI_REC": float(np.sum(np.maximum(exc_ani, 0))) * COEF,
                             "ANI": float(np.sum(exc_ani)) * COEF, "CERO": float(np.sum(mir[m])) * COEF,
                             "dist_min_alert_km": min(p["dist_km"] for p in rec["anomaly_pixels"])})
                if fila["K_t_bg_prod"]:
                    L_k = float(MV.temperatura_a_radiancia(np.array([fila["K_t_bg_prod"]]), LAM)[0])
                    fila["ANIK_REC"] = float(np.sum(np.maximum(mir[m] - L_k, 0))) * COEF
                    fila["Tal_menos_Tfl"] = fila["T_alert_media"] - fila["T_fondo_local"]
                    fila["Kbg_menos_Tfl"] = fila["K_t_bg_prod"] - fila["T_fondo_local"]
            filas.append(fila)

pr(f"pasadas con grilla: {len(filas)}; con alertados de la vía: {sum(1 for x in filas if x['npix_via'])}; "
   f"ventana {min(x['dt'] for x in filas)} a {max(x['dt'] for x in filas)}")

# controles
dP1 = [abs(x["VIA"] - x["vrp_via_rec"]) for x in filas if x["npix_via"]]
pr(f"control P1: |VIA recalculado - vrp_mw del record| max {max(dP1):.4f} MW (vrp_mw redondeado a 1e-3) sobre {len(dP1)}")
pr(f"control P1: CERO >= VIA en {sum(1 for x in filas if x['npix_via'] and x['CERO'] >= x['VIA'])} de {len(dP1)}")
kk = [(x["T_anillo_grilla"], x["K_t_bg_prod"]) for x in filas if x["K_t_bg_prod"]]
dk = [a - b for a, b in kk]
pr(f"control anillo: T_anillo_grilla - t_bg del record K de producción, misma pasada: n {len(dk)} mediana {med(dk)} "
   f"p10 {round(float(np.percentile(dk, 10)), 2)} p90 {round(float(np.percentile(dk, 90)), 2)}; Spearman entre ambos {round(spearman([a for a, _ in kk], [b for _, b in kk]), 3)}")

# temperaturas por tramo (todas las pasadas con grilla, y las con alertados)
pr("== temperaturas de brillo I4 por tramo de cenit (todas las pasadas nocturnas con grilla)")
zt = [x["z"] for x in filas]
for k in ("T_cumbre", "T_anillo_grilla", "anillo_menos_cumbre", "K_t_bg_prod"):
    zz = [x["z"] for x in filas if x[k] is not None]
    vv = [x[k] for x in filas if x[k] is not None]
    pr(f"  {k:22s} {estrato(zz, vv)}")
A = [x for x in filas if x["npix_via"]]
pr("== pasadas con alertados de la vía (cualquier clase de distancia)")
for k in ("T_alert_media", "T_alert_max", "T_fondo_local", "anillo_menos_local", "anillo_menos_cumbre", "npix_via", "alert_sobre_anillo"):
    pr(f"  {k:22s} {estrato([x['z'] for x in A], [x[k] for x in A])}")
pr(f"  P2: T_anillo - T_fondo_local == 0 en {sum(1 for x in A if abs(x['anillo_menos_local']) < 1e-6)} de {len(A)}")

# brazos contra MIROVA, misma máscara (sólo summit de la vía y alerta de MIROVA > 0; las de clase far van aparte)
B = [x for x in A if x["vrp_M"] and x["vrp_M"] > 0 and x["via_dc"] == "summit"]
Bf = [x for x in A if x["vrp_M"] and x["vrp_M"] > 0 and x["via_dc"] != "summit"]
pr(f"== brazos de fondo con la máscara de la vía, contra MIROVA (summit, alerta MIROVA > 0): n {len(B)}; ventana "
   f"{min(x['dt'] for x in B) if B else None} a {max(x['dt'] for x in B) if B else None}; far aparte n {len(Bf)}")
res = {"filas": filas}
for br in ("VIA", "ANI", "ANI_REC", "CERO"):
    rs = estrato([x["z"] for x in B], [x[br] / x["vrp_M"] for x in B])
    res[f"brazo_{br}"] = rs
    pr(f"  {br:8s} / MIROVA  {rs}")
for br in ("ANIK_REC",):
    rs = estrato([x["z"] for x in B], [x[br] / x["vrp_M"] for x in B])
    res[f"brazo_{br}"] = rs
    pr(f"  {br:8s} / MIROVA  {rs}   (fondo = t_bg del record K de producción de la misma pasada, recorte a cero)")
for k in ("Tal_menos_Tfl", "Kbg_menos_Tfl", "anillo_menos_local"):
    rs = estrato([x["z"] for x in B], [x[k] for x in B])
    res[f"B_{k}"] = rs
    pr(f"  B {k:16s} {rs}")
rs = estrato([x["z"] for x in B], [x["ANI_REC"] / x["VIA"] for x in B])
res["B_ANI_REC_sobre_VIA"] = rs
pr(f"  B ANI_REC/VIA      {rs}")
Bk = [x for x in B if x["K_pub"] == "1" and x["K_disp"] and x["K_disp"] > 0]
rs = estrato([x["z"] for x in Bk], [x["K_disp"] / x["vrp_M"] for x in Bk])
res["K_prod_mismas"] = rs
pr(f"  K prod / MIROVA (mismas, K publicada) {rs}")
rs = estrato([x["z"] for x in Bk if x["ANIK_REC"] > 0], [x["K_disp"] / x["ANIK_REC"] for x in Bk if x["ANIK_REC"] > 0])
res["K_prod_sobre_ANIK_REC"] = rs
pr(f"  K prod / ANIK_REC (mismas, ANIK_REC > 0) {rs}")
for x in sorted(B, key=lambda y: y["z"]):
    pr(f"  {x['dt']} {x['sensor']:12s} z {x['z']:5.1f} M {x['vrp_M']:.3f} VIA {x['VIA']:.3f} ANI {x['ANI']:+.3f} ANI_REC {x['ANI_REC']:.3f} "
       f"K {x['K_disp'] if x['K_disp'] is not None else '-'} npix {x['npix_via']} sobre_anillo {x['alert_sobre_anillo']} "
       f"Tal {x['T_alert_media']:.1f} Tfl {x['T_fondo_local']:.1f} Tani {x['T_anillo_grilla']:.1f} Tcum {x['T_cumbre']:.1f} Kt_bg {x['K_t_bg_prod']}")
pr("-- alertas de MIROVA con vía de clase far (aparte):")
for x in Bf:
    pr(f"  {x['dt']} {x['sensor']} z {x['z']:.1f} M {x['vrp_M']} src {x['src_M']} VIA {x['VIA']:.3f} dist_min {x['dist_min_alert_km']} km K {x['K_disp']}")
json.dump(res, open(PRE + "_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
open(PRE + "_salida.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")
