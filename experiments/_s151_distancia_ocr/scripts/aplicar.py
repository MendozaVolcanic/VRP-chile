# -*- coding: utf-8 -*-
"""(a) Pasadas de la tabla a mas de 25 km: que dice de ellas el metodo de eliminacion (el panel no las dibuja).
(b) Aplicacion a las 15 filas ALERTA_SIN_GEOMETRIA_OCR (VIIRS 375 y VIIRS 750) con la Dist.png archivada mas
    cercana posterior a la pasada (bajada por raw de mirova-tif-archive, sin clone).
Mismas funciones y tolerancias que control_dist.py (copiadas, porque ese script corre todo al importarse).
Uso: python aplicar.py <carpeta_datos> <carpeta_salidas>"""
import sys, os, urllib.request
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dist_png as D

DAT, SAL = sys.argv[1], sys.argv[2]
NOMBRE = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "ChillanNevadosde"}
SENS = {"VIIRS375": "VIIRS375", "VIIRS": "VIIRS750"}
TOL_T, TOL_KM, W = 0.12, 0.6, 0.15
LIM = {"Tupungatito": 7.0}

c = pd.read_csv(f"{DAT}/registro_vrp_consolidado.csv")
o = pd.read_csv(f"{DAT}/registro_vrp_ocr.csv")
for df in (c, o):
    df["vol"] = df.Volcan.map(lambda v: NOMBRE.get(v, v))
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC)


def conocidas_de(sensor_csv):
    tab = c[(c.Sensor == sensor_csv) & (c.VRP_MW > 0) & c.Distancia_km.notna()][["vol", "t", "VRP_MW", "Distancia_km", "Tipo_Registro"]].assign(fuente="tabla")
    oc = o[(o.Sensor == sensor_csv) & (o.Fecha_Satelite_UTC >= "2026-06-13") & o.Distancia_km.notna()
           & (o.Tipo_Registro != "ALERTA_SIN_GEOMETRIA_OCR")][["vol", "t", "VRP_MW", "Distancia_km", "Tipo_Registro"]].assign(fuente="ocr")
    k = pd.concat([tab, oc], ignore_index=True).sort_values(["vol", "t", "fuente"]).reset_index(drop=True)
    dup = (k.vol == k.vol.shift()) & ((k.t - k.t.shift()).dt.total_seconds().abs() < 180)
    return k[~dup].reset_index(drop=True), tab


def marcadores_t(x, L, off):
    g = x["geo"]; ms = list(x["marcadores"]) + ([x["estrella"]] if x["estrella"] else [])
    return [dict(m, t=L + pd.Timedelta(days=(m["x"] - g["ticks"][0]) / g["ppd"] + off)) for m in ms]


def pareos(ms, ref):
    n = 0
    for m in ms:
        dt = (ref.t - m["t"]).dt.total_seconds().abs() / 86400
        dk = (ref.Distancia_km.where(ref.Distancia_km <= 25.3, 999) - m["km"]).abs()
        n += int(((dt <= TOL_T) & (dk <= TOL_KM)).any())
    return n


def calibrar(x, ref, lm):
    g = x["geo"]; base = lm.normalize()
    ms = list(x["marcadores"]) + ([x["estrella"]] if x["estrella"] else [])
    xmax = max(m["x"] for m in ms)
    mejor = None
    for k in (-31, -30, -29):
        L = base + pd.Timedelta(days=k)
        for off in np.arange(-0.30, 0.80, 0.02):
            tmax = L + pd.Timedelta(days=(xmax - g["ticks"][0]) / g["ppd"] + off)
            if tmax > lm + pd.Timedelta(hours=2):
                continue
            n = pareos(marcadores_t(x, L, off), ref)
            cand = (n, -abs((lm - tmax).total_seconds()), L, float(off))
            if mejor is None or cand[:2] > mejor[:2]:
                mejor = cand
    return marcadores_t(x, mejor[2], mejor[3]), mejor


def eliminar(t, ms, otras):
    col = [m for m in ms if abs((m["t"] - t).total_seconds()) / 86400 <= W]
    if not col:
        return "sin_marcador", None, None, None, 0, []
    restantes = list(col)
    for _, k in otras.iterrows():
        if not restantes: break
        if k.Distancia_km > 25.3: continue
        dk = [abs(m["km"] - k.Distancia_km) for m in restantes]
        i = int(np.argmin(dk))
        if dk[i] <= TOL_KM:
            restantes.pop(i)
    kc = sorted(round(m["km"], 2) for m in col)
    if len(restantes) == 1:
        return "unico", restantes[0]["km"], restantes[0]["km"], restantes[0]["km"], len(col), kc
    if not restantes:
        return "solapado", None, min(kc), max(kc), len(col), kc
    kr = [m["km"] for m in restantes]
    return "ambiguo", None, min(kr), max(kr), len(col), kc


def otras_de(con, vol, t):
    dd = (con.t - t).dt.total_seconds().abs()
    return con[(con.vol == vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]


# ------------------------------------------------ (a) pasadas a mas de 25 km
con375, tab375 = conocidas_de("VIIRS375")
mu = pd.read_csv(f"{DAT}/dist375/muestra_VIIRS375.csv")
mu["lm"] = pd.to_datetime(mu.last_modified_utc).dt.tz_localize(None)
lejos = tab375[tab375.Distancia_km > 24.5]
cache, filas = {}, []
for r in lejos.itertuples():
    g = mu[(mu.volcano == r.vol) & (mu.lm >= r.t + pd.Timedelta(days=1)) & (mu.lm <= r.t + pd.Timedelta(days=25))]
    if g.empty: continue
    a = g.sort_values("lm").iloc[0]
    if a.archivo not in cache:
        x = D.leer(a.archivo)
        cache[a.archivo] = calibrar(x, con375[con375.vol == r.vol], a.lm)[0]
    cl, est, kmin, kmax, n, kc = eliminar(r.t, cache[a.archivo], otras_de(con375, r.vol, r.t))
    U = LIM.get(r.vol, 5.0)
    if cl == "unico": lo = hi = est
    elif cl == "sin_marcador": lo = hi = None
    else: lo, hi = kmin, kmax
    dec = None if lo is None else ("cerca" if hi < U - TOL_KM else ("lejos" if lo > U + TOL_KM else "indecidible"))
    filas.append({"vol": r.vol, "t": str(r.t), "dist": r.Distancia_km, "clase": cl, "est": est, "kmin": kmin, "kmax": kmax, "decision": dec})
A = pd.DataFrame(filas)
A.to_csv(f"{SAL}/control_sobre_25km.csv", index=False)
print(f"== (a) pasadas de la tabla VIIRS 375 a mas de 24,5 km con Dist.png de la muestra: {len(A)}")
print("   clase:", A.clase.value_counts().to_dict())
print("   decision cerca/lejos al limite de alerta:", A.decision.value_counts(dropna=False).to_dict())
print("   => 'cerca' aqui es un ERROR del metodo: la pasada era lejana y el panel no la dibuja")

# ------------------------------------------------ (b) las filas sin geometria
idx = pd.read_csv(f"{DAT}/index_png.csv")
idx = idx[idx.kind == "Dist"].drop_duplicates("md5").copy()
idx["lm"] = pd.to_datetime(idx.last_modified_utc).dt.tz_localize(None)
sg = o[o.Tipo_Registro == "ALERTA_SIN_GEOMETRIA_OCR"].copy()
os.makedirs(f"{DAT}/dist_sg", exist_ok=True)
out = []
for r in sg.itertuples():
    sensor = SENS[r.Sensor]
    con, _ = conocidas_de(r.Sensor)
    vol_idx = r.vol if r.vol != "Nevados de Chillan" else "ChillanNevadosde"
    g = idx[(idx.volcano == vol_idx) & (idx.sensor == sensor) & (idx.lm >= r.t + pd.Timedelta(hours=3)) & (idx.lm <= r.t + pd.Timedelta(days=25))].sort_values("lm")
    if g.empty:
        out.append({"vol": r.vol, "sensor": sensor, "t": str(r.t), "vrp": r.VRP_MW, "clase": "sin_imagen"}); continue
    a = g.iloc[-1]   # la mas reciente archivada: la noche completa ya dibujada y la estrella lejos de esa columna
    loc = f"{DAT}/dist_sg/" + a.png_path.replace("/", "_")
    if not os.path.exists(loc):
        urllib.request.urlretrieve("https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/" + a.png_path, loc)
    x = D.leer(loc)
    ms, cal = calibrar(x, con[con.vol == r.vol], a.lm)
    otras = otras_de(con, r.vol, r.t)
    otras = otras[otras.t <= a.lm]   # solo pasadas que ya podian estar dibujadas en esa imagen
    cl, est, kmin, kmax, n, kc = eliminar(r.t, ms, otras)
    out.append({"vol": r.vol, "sensor": sensor, "t": str(r.t), "vrp": r.VRP_MW, "clase": cl, "est": est, "kmin": kmin, "kmax": kmax,
                "marcadores_columna_km": kc, "otras_conocidas_km": sorted(otras.Distancia_km.round(2).tolist()),
                "pareos_calibracion": cal[0], "imagen": os.path.basename(loc), "lm_imagen": str(a.lm)})
B = pd.DataFrame(out)
B.to_csv(f"{SAL}/sin_geometria_aplicado.csv", index=False)
pd.set_option("display.width", 250)
print(f"\n== (b) ALERTA_SIN_GEOMETRIA_OCR: {len(B)}")
print(B.drop(columns=["imagen"]).to_string())
