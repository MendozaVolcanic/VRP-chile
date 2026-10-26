# -*- coding: utf-8 -*-
"""Control de la lectura de Dist.png como SERIE DE TIEMPO (VIIRS 375).
1. Lee los marcadores del panel Last Month de cada Dist.png archivada de la muestra.
2. Calibra el eje x (fecha de la primera marca semanal y desfase horario) maximizando el pareo con pasadas conocidas.
3. Recall del dibujo: de las pasadas de la TABLA con VRP > 0, cuantas tienen marcador a su hora y a su distancia.
4. Metodo de eliminacion: para cada pasada de la TABLA (control), se la esconde y se estima su distancia con los
   marcadores de su columna (misma noche) menos los que explican las otras pasadas conocidas. Error contra la tabla.
5. Se aplica el mismo metodo a las filas ALERTA_SIN_GEOMETRIA_OCR y a las filas OCR con 0 fijo cubiertas por la muestra.
Uso: python control_dist.py <carpeta_datos> <carpeta_salidas>"""
import sys, json, os
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lector as D

DAT, SAL = sys.argv[1], sys.argv[2]
NOMBRE = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "ChillanNevadosde"}
TOL_T, TOL_KM, W = 0.12, 0.6, 0.15     # dias, km, semiancho de la columna de una noche (dias)
LIM = {"Tupungatito": 7.0}              # limite de alerta del scraper (volcanes.py de Mirova-v1); el resto 5 km

c = pd.read_csv(f"{DAT}/registro_vrp_consolidado.csv")
o = pd.read_csv(f"{DAT}/registro_vrp_ocr.csv")
for df in (c, o):
    df["vol"] = df.Volcan.map(lambda v: NOMBRE.get(v, v))
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC)
tab = c[(c.Sensor == "VIIRS375") & (c.VRP_MW > 0) & c.Distancia_km.notna()][["vol", "t", "VRP_MW", "Distancia_km", "Tipo_Registro"]].assign(fuente="tabla")
ocr = o[o.Sensor == "VIIRS375"].copy()
ocr["fuente"] = "ocr"
ocr_geo = ocr[(ocr.Fecha_Satelite_UTC >= "2026-06-13") & ocr.Distancia_km.notna() & (ocr.Tipo_Registro != "ALERTA_SIN_GEOMETRIA_OCR")]
conocidas = pd.concat([tab, ocr_geo[["vol", "t", "VRP_MW", "Distancia_km", "Tipo_Registro", "fuente"]]], ignore_index=True)
# las filas OCR son "solo OCR"; si alguna duplica una de la tabla (misma pasada a +-3 min), manda la tabla
conocidas = conocidas.sort_values(["vol", "t", "fuente"]).reset_index(drop=True)
dup = (conocidas.vol == conocidas.vol.shift()) & ((conocidas.t - conocidas.t.shift()).dt.total_seconds().abs() < 180)
conocidas = conocidas[~dup].reset_index(drop=True)

mu = pd.read_csv(f"{DAT}/dist375/muestra_VIIRS375.csv")
mu["lm"] = pd.to_datetime(mu.last_modified_utc).dt.tz_localize(None)
lect = {}
for r in mu.itertuples():
    x = D.leer(r.archivo)
    if x is not None:
        lect[r.archivo] = x
print(f"imagenes en la muestra {len(mu)}, con geometria leida {len(lect)}")


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


def calibrar_imagen(r):
    """Por imagen: fecha de la primera marca semanal (L = fecha de cabecera - 30 d; candidatos a 1 dia) y desfase
    horario del dibujo (MIROVA cambio la convencion durante el ano: en julio el punto cae a su hora UTC, en octubre
    unas 11 h antes). Se elige el par que mas pareos da con pasadas conocidas, con la condicion fisica de que ningun
    marcador quede despues de la hora de escritura del archivo (+2 h de holgura). El desfase se ajusta con TODAS las
    pasadas conocidas de la imagen; el sesgo que aporta la pasada de control es uno entre ~25 marcadores."""
    x = lect[r.archivo]; g = x["geo"]
    ref = conocidas[conocidas.vol == r.volcano]
    base = r.lm.normalize()
    ms = list(x["marcadores"]) + ([x["estrella"]] if x["estrella"] else [])
    if not ms:
        return None
    xmax = max(m["x"] for m in ms)
    mejor = None
    for k in (-31, -30, -29):
        L = base + pd.Timedelta(days=k)
        for off in np.arange(-0.30, 0.80, 0.02):
            tmax = L + pd.Timedelta(days=(xmax - g["ticks"][0]) / g["ppd"] + off)
            if tmax > r.lm + pd.Timedelta(hours=2):
                continue
            n = pareos(marcadores_t(x, L, off), ref)
            cand = (n, -abs((r.lm - tmax).total_seconds()), L, round(float(off), 2))
            if mejor is None or cand[:2] > mejor[:2]:
                mejor = cand
    return mejor


CAL = {}
for r in mu.itertuples():
    if r.archivo in lect:
        cb = calibrar_imagen(r)
        if cb is not None:
            CAL[r.archivo] = cb
LS = {a: v[2] for a, v in CAL.items()}
OFFS = {a: v[3] for a, v in CAL.items()}
cal_df = pd.DataFrame([{"archivo": os.path.basename(a), "lm": mu.set_index("archivo").lm[a], "pareos": v[0], "L": v[2], "desfase": v[3]} for a, v in CAL.items()])
cal_df.to_csv(f"{SAL}/calibracion_por_imagen.csv", index=False)
cal_df["mes"] = pd.to_datetime(cal_df.lm).dt.strftime("%Y-%m")
print("desfase del dibujo por mes (dias; mediana, p10, p90, n):")
for mes, gq in cal_df.groupby("mes"):
    print(f"   {mes}: {gq.desfase.median():+.2f} [{gq.desfase.quantile(.1):+.2f}, {gq.desfase.quantile(.9):+.2f}] n={len(gq)}")
cal_df = cal_df.sort_values("lm")
nmarc = sum(len(lect[a]["marcadores"]) + (1 if lect[a]["estrella"] else 0) for a in LS)
print(f"imagenes calibradas {len(LS)}; marcadores leidos {nmarc}; pareos totales {cal_df.pareos.sum()}")

MT = {a: marcadores_t(lect[a], LS[a], OFFS[a]) for a in LS}
mu2 = mu[mu.archivo.isin(LS)].copy()

# huerfanos: marcadores que ninguna pasada conocida explica (pasadas que MIROVA dibujo y no tenemos con distancia)
nh = nt = 0
for a, ms in MT.items():
    vol = mu2[mu2.archivo == a].volcano.iloc[0]
    ref = conocidas[conocidas.vol == vol]
    for m in ms:
        nt += 1
        dt = (ref.t - m["t"]).dt.total_seconds().abs() / 86400
        dk = (ref.Distancia_km.clip(upper=25) - m["km"]).abs()
        nh += int(not ((dt <= TOL_T) & (dk <= TOL_KM)).any())
print(f"marcadores sin pasada conocida que los explique: {nh} de {nt} ({100*nh/nt:.1f} %)")


def imagen_para(vol, t, min_dias=1.0, max_dias=25.0):
    g = mu2[(mu2.volcano == vol) & (mu2.lm >= t + pd.Timedelta(days=min_dias)) & (mu2.lm <= t + pd.Timedelta(days=max_dias))]
    return None if g.empty else g.sort_values("lm").iloc[0].archivo


def eliminar(vol, t, ms, otras):
    """Distancia de la pasada t por eliminacion en su columna. Devuelve (clase, estimacion, kmin, kmax, n_col)."""
    col = [m for m in ms if abs((m["t"] - t).total_seconds()) / 86400 <= W]
    if not col:
        return "sin_marcador", None, None, None, 0
    restantes = list(col)
    for _, k in otras.iterrows():
        if not restantes: break
        if k.Distancia_km > 25.3: continue          # el panel Last Month llega a 25 km: sobre eso no se dibuja
        dk = [abs(m["km"] - min(k.Distancia_km, 25)) for m in restantes]
        i = int(np.argmin(dk))
        if dk[i] <= TOL_KM:
            restantes.pop(i)
    kms_col = [m["km"] for m in col]
    if len(restantes) == 1:
        return "unico", restantes[0]["km"], restantes[0]["km"], restantes[0]["km"], len(col)
    if len(restantes) == 0:
        return "solapado", None, min(kms_col), max(kms_col), len(col)
    kr = [m["km"] for m in restantes]
    return "ambiguo", None, min(kr), max(kr), len(col)


def otras_de(vol, t):
    dd = (conocidas.t - t).dt.total_seconds().abs()
    return conocidas[(conocidas.vol == vol) & (dd / 86400 <= W + 0.05) & (dd > 180)]


# ---------------- 3 y 4: control sobre pasadas de la tabla
filas = []
for r in tab.itertuples():
    a = imagen_para(r.vol, r.t)
    if a is None: continue
    ms = MT[a]
    presente = any(abs((m["t"] - r.t).total_seconds()) / 86400 <= TOL_T and abs(m["km"] - min(r.Distancia_km, 25)) <= TOL_KM for m in ms)
    otras = otras_de(r.vol, r.t)
    cl, est, kmin, kmax, ncol = eliminar(r.vol, r.t, ms, otras)
    filas.append({"vol": r.vol, "t": str(r.t), "tipo": r.Tipo_Registro, "vrp": r.VRP_MW, "dist": r.Distancia_km,
                  "presente": presente, "clase": cl, "est": est, "kmin": kmin, "kmax": kmax, "n_col": ncol,
                  "n_otras": len(otras), "imagen": os.path.basename(a)})
F = pd.DataFrame(filas)
F.to_csv(f"{SAL}/control_tabla.csv", index=False)
sobre = F[F.dist > 24.5]
print(f"\n== pasadas de control con distancia > 24,5 km (fuera del panel 0-25 km): {len(sobre)} de {len(F)}; con marcador a su hora y a 24-25 km: {sobre.presente.sum()}")
F = F[F.dist <= 24.5].copy()
print(f"\n== CONTROL: pasadas de la tabla VIIRS 375 con VRP > 0 y Dist.png de la muestra 1 a 25 dias despues: {len(F)}")
print("   ventana:", F.t.min(), "a", F.t.max())
print(f"   recall del dibujo (marcador a +-{TOL_T} d y +-{TOL_KM} km): {F.presente.sum()} de {len(F)} ({100*F.presente.mean():.1f} %)")
for tp, g in F.groupby("tipo"):
    print(f"      {tp}: {g.presente.sum()} de {len(g)}")
print("   clase de la eliminacion:", F.clase.value_counts().to_dict())
u = F[F.clase == "unico"]
err = (u.est - u.dist.clip(upper=25)).abs()
print(f"   'unico' (un solo marcador sin explicar en la columna): n={len(u)}, error |est - tabla| mediana {err.median():.2f} km, p90 {err.quantile(.9):.2f} km, max {err.max():.2f} km")
for tp, g in u.groupby("tipo"):
    e = (g.est - g.dist.clip(upper=25)).abs()
    print(f"      {tp}: n={len(g)}, mediana {e.median():.2f}, p90 {e.quantile(.9):.2f}")
nu = F[F.clase.isin(["solapado", "ambiguo"])]
dentro = ((nu.dist.clip(upper=25) >= nu.kmin - TOL_KM) & (nu.dist.clip(upper=25) <= nu.kmax + TOL_KM))
print(f"   'solapado'/'ambiguo': n={len(nu)}; la distancia real cae en [kmin, kmax] +-{TOL_KM}: {dentro.sum()} ({100*dentro.mean():.1f} %); ancho del intervalo mediana {(nu.kmax-nu.kmin).median():.2f} km, p90 {(nu.kmax-nu.kmin).quantile(.9):.2f}")
res = {}
for nombre, umbral in (("limite MIROVA (5 km, Tupungatito 7)", None), ("3 km", 3.0), ("10 km", 10.0)):
    ok = mal = indec = 0
    for r in F[F.clase != "sin_marcador"].itertuples():
        U = umbral if umbral else LIM.get(r.vol, 5.0)
        lo, hi = (r.est, r.est) if r.clase == "unico" else (r.kmin, r.kmax)
        if hi < U - TOL_KM: dec = "cerca"
        elif lo > U + TOL_KM: dec = "lejos"
        else: indec += 1; continue
        real = "cerca" if r.dist <= U else "lejos"
        ok += dec == real; mal += dec != real
    res[nombre] = (ok, mal, indec)
    print(f"   cerca/lejos a {nombre}: correctas {ok}, incorrectas {mal}, indecidibles {indec} (sobre {len(F[F.clase!='sin_marcador'])})")
lejanas = F[F.dist > F.vol.map(lambda v: LIM.get(v, 5.0))]
print(f"   solo pasadas de la tabla LEJANAS (dist > limite): n={len(lejanas)}; recall del dibujo {lejanas.presente.sum()}; clases {lejanas.clase.value_counts().to_dict()}")
ul = lejanas[lejanas.clase == "unico"]
if len(ul):
    e = (ul.est - ul.dist.clip(upper=25)).abs()
    print(f"      'unico' lejanas: n={len(ul)}, error mediana {e.median():.2f} km, p90 {e.quantile(.9):.2f} km")
mal_l = F[(F.clase == "unico") & ((F.est - F.dist.clip(upper=25)).abs() > 2)]
print(f"   'unico' con error > 2 km: {len(mal_l)}")
print(mal_l[["vol", "t", "tipo", "dist", "est", "n_col", "n_otras", "imagen"]].head(15).to_string() if len(mal_l) else "")


# ---------------- 5: aplicacion a las filas OCR sin distancia propia
def aplicar(df, titulo):
    out = []
    for r in df.itertuples():
        a = imagen_para(r.vol, r.t, min_dias=0.2)
        if a is None:
            out.append({"vol": r.vol, "t": str(r.t), "vrp": r.VRP_MW, "clase": "sin_imagen"}); continue
        otras = otras_de(r.vol, r.t)
        cl, est, kmin, kmax, ncol = eliminar(r.vol, r.t, MT[a], otras)
        out.append({"vol": r.vol, "t": str(r.t), "vrp": r.VRP_MW, "clase": cl, "est": est, "kmin": kmin, "kmax": kmax,
                    "n_col": ncol, "n_otras": len(otras), "imagen": os.path.basename(a)})
    X = pd.DataFrame(out)
    print(f"\n== {titulo}: {len(X)}; clases {X.clase.value_counts().to_dict()}")
    return X


sg = ocr[ocr.Tipo_Registro == "ALERTA_SIN_GEOMETRIA_OCR"]
X1 = aplicar(sg, "ALERTA_SIN_GEOMETRIA_OCR VIIRS 375")
print(X1.to_string())
X1.to_csv(f"{SAL}/sin_geometria.csv", index=False)
cero = ocr[(ocr.Distancia_km == 0) & (ocr.Fecha_Satelite_UTC < "2026-06-13") & (ocr.Tipo_Registro == "ALERTA_TERMICA_OCR")]
X2 = aplicar(cero, "ALERTA_TERMICA_OCR VIIRS 375 con 0 fijo (antes del 2026-06-13)")
X2.to_csv(f"{SAL}/cero_fijo.csv", index=False)
cub = X2[X2.clase != "sin_imagen"]
print("   cubiertas por la muestra:", len(cub), "desde", cub.t.min() if len(cub) else None, "| sin imagen:", (X2.clase == "sin_imagen").sum(), "(la mas nueva sin imagen:", X2[X2.clase == "sin_imagen"].t.max(), ")")
lim_c = cub.vol.map(lambda v: LIM.get(v, 5.0))
lejos = cub[(cub.clase == "unico") & (cub.est > lim_c + TOL_KM)]
lejos_int = cub[(cub.clase != "unico") & (cub.kmin > lim_c + TOL_KM)]
print(f"   'unico' que caen LEJOS del limite de alerta: {len(lejos)}; intervalo entero lejos: {len(lejos_int)}")
print(lejos[["vol", "t", "vrp", "est", "imagen"]].to_string() if len(lejos) else "")
json.dump({"huerfanos": [nh, nt], "control_n": len(F),
           "recall_dibujo": float(F.presente.mean()), "unico_n": int(len(u)), "unico_err_mediana": float(err.median()),
           "unico_err_p90": float(err.quantile(.9)), "cerca_lejos": res}, open(f"{SAL}/control_resumen.json", "w"), indent=1, default=str)
