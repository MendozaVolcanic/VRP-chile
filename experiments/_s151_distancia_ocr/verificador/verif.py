# -*- coding: utf-8 -*-
"""Verificador del estudio distancia_ocr. Usa las lecturas de leer_todo.py (lector del estudio, sin cambios).

Diferencias deliberadas con el estudio, para medir independencia:
  * CAL_TABLA: el eje de tiempo de cada imagen se cala SOLO con pasadas de la tabla (sin OCR), y para el control
    se cala SIN la pasada de control (leave-one-out por pasada de control no es viable en tiempo: se cala sin TODAS
    las pasadas de control de esa imagen que caen en las primeras 25 d; ver calibrar(excluir=...)).
  * Ancla independiente del tiempo: la estrella amarilla (pasada de la cabecera) debe caer pocas horas antes de
    la hora de escritura del archivo. Se mide su desfase con la calibracion.
  * Pregunta 5: para cada fila OCR con distancia > 0 se mira la columna de la noche en la Dist.png de la muestra
    1 a 25 dias despues: (a) hay marcador a +-1 km de la distancia OCR; (b) estimacion por eliminacion con
    pasadas conocidas SOLO de la tabla; (c) si la distancia OCR no esta en su columna, si esta en una columna
    POSTERIOR (hasta 3 d), firma de "imagen de otra pasada".
Uso: python verif.py <carpeta_estudio> <lecturas.pkl> <carpeta_salida> <carpeta_vrp_chile>"""
import sys, os, json, pickle, glob
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
EST, PKL, SAL, VRP = sys.argv[1:5]
os.makedirs(SAL, exist_ok=True)
NOMBRE = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "ChillanNevadosde"}
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
TOL_T, TOL_KM, W = 0.12, 0.6, 0.15
lim = lambda v: LIM.get(v, 5.0)

c = pd.read_csv(f"{EST}/datos/registro_vrp_consolidado.csv")
o = pd.read_csv(f"{EST}/datos/registro_vrp_ocr.csv")
for df in (c, o):
    df["vol"] = df.Volcan.map(lambda v: NOMBRE.get(v, v))
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC)
EPOCH = pd.Timestamp("2026-01-01")
dias = lambda ts: (ts - EPOCH).total_seconds() / 86400.0

LECT = pickle.load(open(PKL, "rb"))
IMG = pd.DataFrame([{"archivo": k, "volcano": v["volcano"], "sensor": v["sensor"],
                     "lm": pd.Timestamp(v["lm"]).tz_localize(None) if pd.Timestamp(v["lm"]).tzinfo else pd.Timestamp(v["lm"])}
                    for k, v in LECT.items() if v["lect"] is not None])


def tab_de(sensor):
    t = c[(c.Sensor == sensor) & (c.VRP_MW > 0) & c.Distancia_km.notna()].copy()
    return t[["vol", "t", "VRP_MW", "Distancia_km", "Tipo_Registro"]]


def marc_x(lect):
    g = lect["geo"]
    ms = list(lect["marcadores"]) + ([lect["estrella"]] if lect["estrella"] else [])
    x = np.array([(m["x"] - g["ticks"][0]) / g["ppd"] for m in ms])
    km = np.array([m["km"] for m in ms])
    tipo = [m["tipo"] for m in ms]
    return x, km, tipo


def calibrar(lect, lm, ref, base_off=None):
    """Igual que el estudio: s = L + off en una grilla (L en base-31..-29, off -0,30..0,78 cada 0,02), max pareos,
    desempate por cercania del ultimo marcador a lm, y ningun marcador despues de lm + 2 h."""
    x, km, _ = marc_x(lect)
    if len(x) == 0:
        return None
    base = dias(lm.normalize()); lmd = dias(lm)
    rt = np.array([dias(t) for t in ref.t]) if len(ref) else np.zeros(0)
    rd = ref.Distancia_km.where(ref.Distancia_km <= 25.3, 999).to_numpy() if len(ref) else np.zeros(0)
    dk_ok = np.abs(rd[None, :] - km[:, None]) <= TOL_KM if len(rt) else np.zeros((len(x), 0), bool)
    best = None
    for k in (-31, -30, -29):
        for off in np.arange(-0.30, 0.80, 0.02):
            s = base + k + off
            tm = x + s
            if tm.max() > lmd + 2 / 24:
                continue
            n = int(((np.abs(rt[None, :] - tm[:, None]) <= TOL_T) & dk_ok).any(1).sum()) if len(rt) else 0
            cand = (n, -abs(lmd - tm.max()), s)
            if best is None or cand[:2] > best[:2]:
                best = cand
    return best   # (pareos, -dist, s)


def tiempos(lect, s):
    x, km, tipo = marc_x(lect)
    return x + s, km, tipo


def eliminar(tp, tm, km, otras_d):
    col = np.nonzero(np.abs(tm - tp) <= W)[0]
    if len(col) == 0:
        return "sin_marcador", None, None, None, []
    rest = list(col)
    for d in otras_d:
        if not rest: break
        if d > 25.3: continue
        dk = [abs(km[i] - min(d, 25)) for i in rest]
        j = int(np.argmin(dk))
        if dk[j] <= TOL_KM:
            rest.pop(j)
    kc = sorted(float(km[i]) for i in col)
    if len(rest) == 1:
        e = float(km[rest[0]]); return "unico", e, e, e, kc
    if not rest:
        return "solapado", None, min(kc), max(kc), kc
    kr = [float(km[i]) for i in rest]
    return "ambiguo", None, min(kr), max(kr), kc


# ---------------------------------------------------------------- calibracion de cada imagen
def calibrar_todas(sensor, ref_fn):
    out = {}
    for r in IMG[IMG.sensor == sensor].itertuples():
        lect = LECT[r.archivo]["lect"]
        ref = ref_fn(r)
        b = calibrar(lect, r.lm, ref)
        if b is not None:
            out[r.archivo] = b
    return out


T375 = tab_de("VIIRS375")
ocr375 = o[o.Sensor == "VIIRS375"]
ocr_geo = ocr375[(ocr375.Fecha_Satelite_UTC >= "2026-06-13") & ocr375.Distancia_km.notna() & (ocr375.Tipo_Registro != "ALERTA_SIN_GEOMETRIA_OCR")]

# calibracion A: como el estudio (tabla + OCR); B: solo tabla
CA = calibrar_todas("VIIRS375", lambda r: pd.concat([T375, ocr_geo[T375.columns]])[lambda d: d.vol == r.volcano])
CB = calibrar_todas("VIIRS375", lambda r: T375[T375.vol == r.volcano])
cal = pd.DataFrame([{"archivo": a, "pareos_A": CA[a][0], "s_A": CA[a][2], "pareos_B": CB.get(a, (None, None, None))[0],
                     "s_B": CB.get(a, (None, None, None))[2]} for a in CA])
cal["ds_AB_h"] = (cal.s_A - cal.s_B) * 24
print(f"imagenes VIIRS375 calibradas A {len(CA)} B {len(CB)}; |s_A - s_B| > 1 h: {(cal.ds_AB_h.abs() > 1).sum()}")

# ancla independiente: la estrella frente a la hora de escritura del archivo
filas = []
for a, (n, _, s) in CB.items():
    lect = LECT[a]["lect"]; lm = IMG.set_index("archivo").lm[a]
    if lect["estrella"] is None: continue
    g = lect["geo"]
    ts = (lect["estrella"]["x"] - g["ticks"][0]) / g["ppd"] + s
    # ultima pasada de la tabla (cualquier VRP) antes de lm, mismo volcan
    vol = LECT[a]["volcano"]
    prev = c[(c.vol == vol) & (c.Sensor == "VIIRS375") & (c.t <= lm)].t.max()
    filas.append({"archivo": a, "estrella_menos_lm_h": (ts - dias(lm)) * 24,
                  "estrella_menos_ultima_pasada_tabla_h": (ts - dias(prev)) * 24 if pd.notna(prev) else None, "pareos": n})
E = pd.DataFrame(filas)
E.to_csv(f"{SAL}/estrella_ancla.csv", index=False)
print("estrella - hora de escritura (h): n=%d mediana %.2f p10 %.2f p90 %.2f" % (len(E), E.estrella_menos_lm_h.median(), E.estrella_menos_lm_h.quantile(.1), E.estrella_menos_lm_h.quantile(.9)))
e2 = E.estrella_menos_ultima_pasada_tabla_h.dropna()
print("estrella - ultima pasada de la tabla antes del archivo (h): mediana %.2f; |.|<=3h: %d de %d; |.|>9h: %d" % (e2.median(), (e2.abs() <= 3).sum(), len(e2), (e2.abs() > 9).sum()))

# calibracion del eje y: altura 0-25 km en px y ppd por imagen
geo = pd.DataFrame([{"archivo": a, "vol": v["volcano"], "sensor": v["sensor"], "h_px": v["lect"]["geo"]["eje"] - v["lect"]["geo"]["techo"],
                     "eje": v["lect"]["geo"]["eje"], "ppd": v["lect"]["geo"]["ppd"], "nticks": len(v["lect"]["geo"]["ticks"])}
                    for a, v in LECT.items() if v["lect"] is not None])
geo.to_csv(f"{SAL}/geometria_por_imagen.csv", index=False)
print("eje y: alto 0-25 km en px por sensor:")
print(geo.groupby("sensor").h_px.describe().round(2).to_string())
print("eje x: px por dia:", geo.groupby("sensor").ppd.describe().round(3).to_string())

# ---------------------------------------------------------------- control: con cal A y con cal B
def imagen_para(vol, t, sensor="VIIRS375", mn=1.0, mx=25.0, cal_=None, ultima=False):
    g = IMG[(IMG.volcano == vol) & (IMG.sensor == sensor) & (IMG.lm >= t + pd.Timedelta(days=mn)) & (IMG.lm <= t + pd.Timedelta(days=mx))]
    if cal_ is not None:
        g = g[g.archivo.isin(cal_)]
    if g.empty: return None
    g = g.sort_values("lm")
    return (g.iloc[-1] if ultima else g.iloc[0]).archivo


def control(calib, nombre, otras_fuente):
    rows = []
    for r in T375.itertuples():
        if r.Distancia_km > 24.5: continue
        a = imagen_para(r.vol, r.t, cal_=calib)
        if a is None: continue
        tm, km, _ = tiempos(LECT[a]["lect"], calib[a][2])
        dd = (otras_fuente.t - r.t).dt.total_seconds().abs()
        otr = otras_fuente[(otras_fuente.vol == r.vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]
        cl, est, kmin, kmax, kc = eliminar(dias(r.t), tm, km, otr.Distancia_km.tolist())
        rows.append({"vol": r.vol, "t": r.t, "dist": r.Distancia_km, "clase": cl, "est": est, "kmin": kmin, "kmax": kmax, "n_col": len(kc), "n_otras": len(otr)})
    F = pd.DataFrame(rows)
    u = F[F.clase == "unico"]; err = (u.est - u.dist).abs()
    u2 = u[u.n_col >= 2]; err2 = (u2.est - u2.dist).abs()
    print(f"[{nombre}] control n={len(F)} clases {F.clase.value_counts().to_dict()}")
    print(f"   unico n={len(u)} mediana {err.median():.2f} p90 {err.quantile(.9):.2f} >2km {(err>2).sum()} | "
          f"con n_col=1: {(u.n_col==1).sum()} | con n_col>=2: n={len(u2)} mediana {err2.median():.2f} p90 {err2.quantile(.9):.2f} >2km {(err2>2).sum()}")
    return F


KN_A = pd.concat([T375, ocr_geo[T375.columns]]).sort_values("t")
FA = control(CA, "cal A tabla+OCR (estudio)", KN_A)
FB = control(CB, "cal B solo tabla", T375)
FA.to_csv(f"{SAL}/control_A.csv", index=False); FB.to_csv(f"{SAL}/control_B.csv", index=False)

# control de dificultad: pasadas de noches con >=2 pasadas de la tabla con VRP>0 y distancias DISTINTAS (> 2 km)
def dificiles(F):
    out = []
    for r in F.itertuples():
        dd = (T375.t - r.t).dt.total_seconds().abs()
        otr = T375[(T375.vol == r.vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]
        out.append(bool(len(otr)) and bool((otr.Distancia_km.sub(r.dist).abs() > 2).any()))
    return np.array(out)
dfB = dificiles(FB)
uB = FB[(FB.clase == "unico") & dfB]
eB = (uB.est - uB.dist).abs()
print(f"   [cal B] noches con otra pasada a >2 km de distinta distancia: n={dfB.sum()}, de ellas unico {len(uB)}: mediana {eB.median():.2f}, >1 km {(eB>1).sum()}")

# leave-the-pass-out real en el subconjunto 'unico' de cal B: recalibrar la imagen sin la pasada de control
loo = []
for r in FB[FB.clase == "unico"].sample(min(250, (FB.clase == "unico").sum()), random_state=1).itertuples():
    a = imagen_para(r.vol, r.t, cal_=CB)
    lm = IMG.set_index("archivo").lm[a]
    ref = T375[(T375.vol == r.vol) & ((T375.t - r.t).dt.total_seconds().abs() > 180)]
    b = calibrar(LECT[a]["lect"], lm, ref)
    tm, km, _ = tiempos(LECT[a]["lect"], b[2])
    dd = (T375.t - r.t).dt.total_seconds().abs()
    otr = T375[(T375.vol == r.vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]
    cl, est, *_ = eliminar(dias(r.t), tm, km, otr.Distancia_km.tolist())
    loo.append({"cl": cl, "err": abs(est - r.dist) if est is not None else None, "ds_h": (b[2] - CB[a][2]) * 24})
L = pd.DataFrame(loo)
print(f"   leave-one-out (250 unico al azar, recalibrando sin la pasada): misma clase unico {(L.cl=='unico').sum()}, "
      f"|ds| > 1 h {(L.ds_h.abs()>1).sum()}, err mediana {L.err.median():.2f} >2 km {(L.err>2).sum()}")

# linealidad del eje y: error por banda de distancia (cal B, unico con n_col=1, marcador de su propia pasada)
u1 = FB[(FB.clase == "unico") & (FB.n_col == 1)].copy(); u1["res"] = u1.est - u1.dist
u1["banda"] = pd.cut(u1.dist, [0, 2, 5, 10, 15, 20, 25])
print("linealidad eje y (est - tabla, n_col=1):"); print(u1.groupby("banda", observed=True).res.describe()[["count", "mean", "50%", "std"]].round(3).to_string())
u1["mes"] = u1.t.dt.strftime("%m"); print("sesgo por mes:", u1.groupby("mes").res.median().round(3).to_dict())
print("sesgo por volcan:", u1.groupby("vol").res.median().round(3).to_dict())

# ---------------------------------------------------------------- Pregunta 5: filas OCR con distancia > 0
# satelite por hora de la pasada: de los records VIIRS I-band del pipeline (cualquier volcan Tier A, +-6 min)
sat = []
for p in glob.glob(f"{VRP}/data/mirova_equivalent/*.json"):
    if os.path.getsize(p) < 5e6: continue
    d = json.load(open(p, encoding="utf-8"))
    for r in d["records"]:
        s = r.get("sensor", "")
        if s.startswith("VIIRS_") and not s.endswith("_750") and r.get("datetime_utc"):
            sat.append((r["datetime_utc"], s))
    del d
S = pd.DataFrame(sat, columns=["t", "sat"]).drop_duplicates()
S["t"] = pd.to_datetime(S.t); S = S.sort_values("t")


def satelite(t):
    k = S[(S.t - t).abs() <= pd.Timedelta(minutes=6)]
    if k.empty: return "sin_dato"
    v = k.sat.value_counts()
    return v.index[0].replace("VIIRS_", "")


Q = o[(o.Distancia_km > 0)].copy()
print(f"\n== P5: filas OCR con distancia > 0: {len(Q)}; por sensor {Q.Sensor.value_counts().to_dict()}")
cortes = [("2026-03-01", "a <03-01"), ("2026-06-11", "b 03-01..06-10"), ("2026-06-13", "c 06-11..06-12"),
          ("2026-08-06", "d 06-13..08-05"), ("2026-10-09", "e 08-06..10-08"), ("9999", "f >=10-09")]
Q["tramo"] = Q.Fecha_Satelite_UTC.str[:10].map(lambda f: next(n for cc, n in cortes if f < cc))
call = c[c.Sensor.isin(["VIIRS375", "VIIRS", "MODIS"])]
out = []
for r in Q.itertuples():
    sensor = {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750", "MODIS": "MODIS"}[r.Sensor]
    # fila de la tabla de la misma pasada (+-3 min)
    tt = call[(call.vol == r.vol) & (call.Sensor == r.Sensor) & ((call.t - r.t).dt.total_seconds().abs() <= 180)]
    en_tabla = "no" if tt.empty else ("si_vrp>0" if (tt.VRP_MW > 0).any() else "si_vrp0")
    d_tab = float(tt.Distancia_km.iloc[0]) if len(tt) and pd.notna(tt.Distancia_km.iloc[0]) else None
    row = {"vol": r.vol, "t": r.t, "sensor": sensor, "tipo": r.Tipo_Registro, "vrp": r.VRP_MW, "d_ocr": r.Distancia_km,
           "tramo": r.tramo, "sat": satelite(r.t) if sensor == "VIIRS375" else "", "en_tabla": en_tabla, "d_tabla": d_tab,
           "version": r.Version_OCR}
    if sensor != "VIIRS375":
        row["clase"] = "sin_metodo"; out.append(row); continue
    a = imagen_para(r.vol, r.t, cal_=CB)
    if a is None:
        a = imagen_para(r.vol, r.t, mn=0.2, cal_=CB)
    if a is None:
        row["clase"] = "sin_imagen"; out.append(row); continue
    tm, km, _ = tiempos(LECT[a]["lect"], CB[a][2])
    tp = dias(r.t)
    col = np.abs(tm - tp) <= W
    kc = km[col]
    row["imagen"] = a; row["n_col"] = int(col.sum()); row["col_km"] = sorted(np.round(kc, 2).tolist())
    row["hay_marcador_1km"] = bool((np.abs(kc - min(r.Distancia_km, 25)) <= 1.0).any()) if len(kc) else False
    row["min_dif_col"] = float(np.abs(kc - min(r.Distancia_km, 25)).min()) if len(kc) else None
    # posterior: marcador a +-1 km de la distancia OCR en columnas de 0,15 a 3 d despues (otras noches/pasadas)
    post = (tm - tp > W) & (tm - tp <= 3.0) & (np.abs(km - min(r.Distancia_km, 25)) <= 1.0)
    row["en_columna_posterior"] = bool(post.any())
    # eliminacion con conocidas SOLO de la tabla (independiente del OCR)
    dd = (T375.t - r.t).dt.total_seconds().abs()
    otr = T375[(T375.vol == r.vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]
    cl, est, kmin, kmax, _ = eliminar(tp, tm, km, otr.Distancia_km.tolist())
    row.update({"clase": cl, "est": est, "kmin": kmin, "kmax": kmax, "n_otras_tabla": len(otr)})
    # decision cerca/lejos con el limite del volcan: OCR vs metodo
    U = lim(r.vol)
    row["dec_ocr"] = "cerca" if r.Distancia_km <= U else "lejos"
    if cl == "sin_marcador": dm = "sin_marcador"
    else:
        lo, hi = (est, est) if cl == "unico" else (kmin, kmax)
        dm = "cerca" if hi < U - TOL_KM else ("lejos" if lo > U + TOL_KM else "indecidible")
    row["dec_metodo"] = dm
    # segunda imagen (estabilidad): la siguiente de la muestra
    g = IMG[(IMG.volcano == r.vol) & (IMG.sensor == "VIIRS375") & (IMG.lm > IMG.set_index("archivo").lm[a]) & (IMG.lm <= r.t + pd.Timedelta(days=25)) & IMG.archivo.isin(CB)].sort_values("lm")
    if len(g):
        a2 = g.iloc[0].archivo; tm2, km2, _ = tiempos(LECT[a2]["lect"], CB[a2][2])
        k2 = km2[np.abs(tm2 - tp) <= W]
        row["hay_marcador_1km_img2"] = bool((np.abs(k2 - min(r.Distancia_km, 25)) <= 1.0).any()) if len(k2) else False
    out.append(row)
P = pd.DataFrame(out)
P.to_csv(f"{SAL}/p5_ocr_vs_columna.csv", index=False)


def resumen(P):
    m = P[P.clase.isin(["unico", "solapado", "ambiguo", "sin_marcador"])]
    u = m[m.clase == "unico"]
    du = (u.est - u.d_ocr.clip(upper=25)).abs()
    return pd.Series({"filas": len(P), "con_imagen": len(m), "marcador_a_1km": int(m.hay_marcador_1km.sum()),
                      "sin_marcador_a_1km": int((~m.hay_marcador_1km.astype(bool)).sum()),
                      "col_vacia": int((m.n_col == 0).sum()),
                      "unico": len(u), "unico_coincide_1km": int((du <= 1).sum()), "unico_difiere_1a3": int(((du > 1) & (du <= 3)).sum()),
                      "unico_difiere_>3": int((du > 3).sum()),
                      "no_a_1km_y_en_posterior": int(((~m.hay_marcador_1km.astype(bool)) & m.en_columna_posterior.astype(bool)).sum()),
                      "cambia_decision": int(((m.dec_metodo.isin(["cerca", "lejos"])) & (m.dec_metodo != m.dec_ocr)).sum()),
                      "decidible": int(m.dec_metodo.isin(["cerca", "lejos"]).sum())})


pd.set_option("display.width", 250)
print("\n-- total VIIRS375"); print(resumen(P[P.sensor == "VIIRS375"]).to_string())
print("\n-- por tramo A119"); print(P[P.sensor == "VIIRS375"].groupby("tramo").apply(resumen, include_groups=False).to_string())
print("\n-- por satelite"); print(P[P.sensor == "VIIRS375"].groupby("sat").apply(resumen, include_groups=False).to_string())
print("\n-- por presencia en la tabla"); print(P[P.sensor == "VIIRS375"].groupby("en_tabla").apply(resumen, include_groups=False).to_string())
print("\n-- antes/desde 10-09"); print(P[P.sensor == "VIIRS375"].groupby(P.t >= "2026-10-09").apply(resumen, include_groups=False).to_string())
print("\n-- por tipo"); print(P[P.sensor == "VIIRS375"].groupby("tipo").apply(resumen, include_groups=False).to_string())
print("\n-- por clase de la eliminacion", P.clase.value_counts().to_dict())
x = P[P.sensor == "VIIRS375"]
print("\n-- OCR vs tabla en la misma pasada (independiente de la imagen): filas OCR con fila de tabla con distancia:",
      int(x.d_tabla.notna().sum()), "| |d_ocr - d_tabla| <= 1 km:", int(((x.d_ocr - x.d_tabla).abs() <= 1).sum()))
cam = x[(x.dec_metodo.isin(["cerca", "lejos"])) & (x.dec_metodo != x.dec_ocr)]
print("\n-- filas que cambian de decision:"); print(cam[["vol", "t", "sat", "tipo", "vrp", "d_ocr", "est", "kmin", "kmax", "col_km", "dec_ocr", "dec_metodo", "en_tabla", "en_columna_posterior", "hay_marcador_1km"]].to_string())
nomarc = x[x.clase.isin(["unico", "solapado", "ambiguo", "sin_marcador"]) & (~x.hay_marcador_1km.astype(bool))]
print("\n-- filas SIN marcador a 1 km de su distancia OCR:"); print(nomarc[["vol", "t", "sat", "tramo", "tipo", "vrp", "d_ocr", "col_km", "clase", "est", "en_tabla", "en_columna_posterior", "hay_marcador_1km_img2"]].to_string())
