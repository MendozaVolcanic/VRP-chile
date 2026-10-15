# -*- coding: utf-8 -*-
"""Base comun del verificador (v2). Lecturas: lecturas.pkl (lector del estudio sin cambios, leer_todo.py).
Calibracion vectorizada identica en reglas a control_dist.calibrar_imagen (grilla L=base-31..-29, off -0.30..0.78
cada 0.02, max pareos, desempate por cercania del ultimo marcador a lm, ningun marcador > lm+2h), pero con la
referencia que se le pase (permite excluir pasadas)."""
import pickle, numpy as np, pandas as pd
NOMBRE = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "ChillanNevadosde"}
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
TOL_T, TOL_KM, W = 0.12, 0.6, 0.15
EPOCH = pd.Timestamp("2026-01-01")
EST = "C:/Users/nmend/AppData/Local/Temp/claude/distancia_ocr"
def lim(v): return LIM.get(v, 5.0)
def dias(ts): return (ts - EPOCH).total_seconds() / 86400.0

def cargar():
    c = pd.read_csv(f"{EST}/datos/registro_vrp_consolidado.csv")
    o = pd.read_csv(f"{EST}/datos/registro_vrp_ocr.csv")
    for df in (c, o):
        df["vol"] = df.Volcan.map(lambda v: NOMBRE.get(v, v))
        df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC)
        df["td"] = df.t.map(dias)
    L = pickle.load(open("C:/Users/nmend/AppData/Local/Temp/claude/verifdist/lecturas.pkl", "rb"))
    rows = []
    for k, v in L.items():
        if v["lect"] is None or v.get("solo_nombre_lm"): continue
        lm = pd.Timestamp(v["lm"]); lm = lm.tz_localize(None) if lm.tzinfo else lm
        g = v["lect"]["geo"]; ms = list(v["lect"]["marcadores"]) + ([v["lect"]["estrella"]] if v["lect"]["estrella"] else [])
        if not ms: continue
        x = np.array([(m["x"] - g["ticks"][0]) / g["ppd"] for m in ms]); km = np.array([m["km"] for m in ms])
        est = np.array([m["tipo"] == "estrella" for m in ms])
        rows.append({"archivo": k, "vol": v["volcano"], "lm": lm, "lmd": dias(lm), "x": x, "km": km, "est": est})
    return c, o, pd.DataFrame(rows)

OFFS = np.round(np.arange(-0.30, 0.80, 0.02), 2)
def calibrar(img, rt, rd):
    """rt: tiempos (dias) de referencia, rd: distancias. Devuelve s (dias) tal que t_marcador = x + s, y pareos."""
    x, km = img["x"], img["km"]; base = np.floor(img["lmd"]); lmd = img["lmd"]
    rd = np.where(rd <= 25.3, rd, 999.0)
    dk = np.abs(rd[None, :] - km[:, None]) <= TOL_KM
    best = None
    for k in (-31, -30, -29):
        for off in OFFS:
            s = base + k + off; tm = x + s
            if tm.max() > lmd + 2 / 24: continue
            n = int(((np.abs(rt[None, :] - tm[:, None]) <= TOL_T) & dk).any(1).sum()) if len(rt) else 0
            cand = (n, -abs(lmd - tm.max()), s)
            if best is None or cand[:2] > best[:2]: best = cand
    return best

def eliminar(t, tm, km, otras_d):
    """Igual que control_dist.eliminar. tm, km: marcadores de la imagen; otras_d: distancias conocidas de la noche."""
    col = np.abs(tm - t) <= W
    kc = list(km[col])
    if not kc: return "sin_marcador", None, None, None, 0
    rest = list(kc)
    for d in otras_d:
        if not rest: break
        if d > 25.3: continue
        dk = [abs(m - min(d, 25)) for m in rest]; i = int(np.argmin(dk))
        if dk[i] <= TOL_KM: rest.pop(i)
    if len(rest) == 1: return "unico", rest[0], rest[0], rest[0], len(kc)
    if not rest: return "solapado", None, min(kc), max(kc), len(kc)
    return "ambiguo", None, min(rest), max(rest), len(kc)

def decidir(cl, est, kmin, kmax, U):
    if cl == "sin_marcador": return "sin_marcador"
    lo, hi = (est, est) if cl == "unico" else (kmin, kmax)
    if hi < U - TOL_KM: return "cerca"
    if lo > U + TOL_KM: return "lejos"
    return "indecidible"
