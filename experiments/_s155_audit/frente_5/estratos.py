# -*- coding: utf-8 -*-
"""S155 frente 5: estratos por sensor y cenit sobre pareo_pasadas.json, y descomposicion multiplicativa del deficit.

Descomposicion por pasada (todas son razones contra el VRP de MIROVA de la misma pasada):
  Rpub    = lo que publica el tablero (f5 en VIIRS 375, pc.vrp_mw en MODIS y VIIRS 750).
  Rpcsum  = el cumulo primario SIN el modo de un pixel (suma de sus pixeles, reconstruida por centroide, n<=3).
  Rinner  = todos los pixeles alertados a <= 5 km del centro del volcan (en esta ventana coincide con la escena).
  Rnobg   = Rinner con fondo CERO (cota superior absoluta de lo que cualquier cambio de fondo puede recuperar).
  Rbg10   = Rinner con el fondo del anillo 10 K mas frio (sensibilidad ilustrativa, no medicion).
  f_req   = (mediana de Rinner en el estrato cenit < 30 del mismo sensor) / Rinner: el factor que haria falta para
            que la pasada quede como las de nadir (metodo de docs/s131/REMUESTREO_LEY_DE_AREA.md §4, por pasada).
  fs, fa  = factores de huella del modelo geometrico (solo barrido, area completa) de pareo_pasadas.huella().

Pregunta 1 del instrumento: si el mecanismo de seleccion no existiera, Rinner/Rpub = 1 en todas; si el fondo no
pesara, Rnobg/Rinner = 1. Pregunta 2: el estrato nadir es el control (fs = fa = 1 ahi por construccion); si el modelo
de area estuviera roto, f_req y fs/fa no tendrian por que ordenarse igual con el cenit.
Poblacion: pares con MIROVA >= 1 MW (alerta protegida) y con cumulo publicado; las FN se cuentan aparte.
"""
import io
import json
import math
import os
import sys
import statistics as st

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import pareo_pasadas as PP  # noqa  (constantes y planck)

filas = json.load(open(os.path.join(D, "pareo_pasadas.json"), encoding="utf-8"))
recs = {(r["datetime_utc"][:16], PP.bucket(r["sensor"])): r for r in json.load(open(
    os.path.join(PP.WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]}


def rbg(f, dT):
    r = recs[(f["t"], f["b"])]
    lam, kw, A = PP.CONST[f["b"]]
    Lb = PP.planck(r["t_bg_k"] - dT, lam)
    s = sum(A * kw * max(PP.planck(p["bt_k"], lam) - Lb, 0.0) / 1e6 for p in r["anomaly_pixels"] if p["dist_km"] <= 5.0)
    return s / f["mir"]


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[o[k]] = (i + j) / 2.0
            i = j + 1
        return rk
    if len(x) < 3:
        return float("nan")
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


prot = [f for f in filas if f["mir"] >= 1.0]
fn = [f for f in prot if f["pc"] is None]
ok = [f for f in prot if f["pc"] is not None]
print("pares con MIROVA >= 1 MW: %d; sin cumulo publicado (FN): %d -> %s" % (
    len(prot), len(fn), ", ".join("%s %s %.1f deg %.2f MW" % (f["t"], f["b"], f["zen"], f["mir"]) for f in fn)))
for f in ok:
    m = f["mir"]
    f["Rpub"], f["Rpcsum"], f["Rinner"], f["Rnobg"] = f["pub"] / m, f["pc_sum"] / m, f["inner"] / m, f["nobg_inner"] / m
    f["Rbg10"] = rbg(f, 10.0)
    f["Rbg20"] = rbg(f, 20.0)

BINS = [(0, 30), (30, 45), (45, 60), (60, 90)]
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    S = [f for f in ok if f["b"] == b]
    nad = [f["Rinner"] for f in S if f["zen"] < 30]
    ref = st.median(nad) if nad else float("nan")
    for f in S:
        f["f_req"] = ref / f["Rinner"] if f["Rinner"] else float("nan")
    print("\n== %s  (n=%d; referencia nadir Rinner mediana=%.2f con n=%d)" % (b, len(S), ref, len(nad)))
    print("bin     n  zen_med | Rpub Rpcsum Rinner Rbg10 Rbg20 Rnobg | sel=Rinner/Rpub bgmax=Rnobg/Rinner | f_req  fs   fa | Rinner*fs Rinner*fa")
    for lo, hi in BINS:
        T = [f for f in S if lo <= f["zen"] < hi]
        if not T:
            print("%2d-%2d   0" % (lo, hi))
            continue
        md = lambda k: st.median([f[k] for f in T])  # noqa
        print("%2d-%2d %3d  %5.1f  | %4.2f %5.2f %6.2f %5.2f %5.2f %5.2f | %14.2f %18.2f | %5.2f %4.2f %4.2f | %8.2f %9.2f" % (
            lo, hi, len(T), md("zen"), md("Rpub"), md("Rpcsum"), md("Rinner"), md("Rbg10"), md("Rbg20"), md("Rnobg"),
            st.median([f["Rinner"] / f["Rpub"] for f in T]), st.median([f["Rnobg"] / f["Rinner"] for f in T]),
            md("f_req"), md("fs"), md("fa"), st.median([f["Rinner"] * f["fs"] for f in T]),
            st.median([f["Rinner"] * f["fa"] for f in T])))
    z = [f["zen"] for f in S]
    for k in ("Rpub", "Rinner", "Rnobg", "Rbg20"):
        print("  spearman(cenit, %s) = %+.2f" % (k, spearman(z, [f[k] for f in S])))
    print("  spearman(cenit, Rinner*fs) = %+.2f ; (cenit, Rinner*fa) = %+.2f ; (cenit, frac_bg) = %+.2f" % (
        spearman(z, [f["Rinner"] * f["fs"] for f in S]), spearman(z, [f["Rinner"] * f["fa"] for f in S]),
        spearman(z, [f["frac_bg"] for f in S])))
    print("  pasadas donde el tablero publica menos de 0,9 del total alertado a <=5 km (seleccion): %d de %d" % (
        sum(1 for f in S if f["Rpub"] < 0.9 * f["Rinner"]), len(S)))
    print("    de ellas, por el modo de un pixel (pc_sum > 1,05 pub): %d; por cumulo vecino descartado (inner > 1,05 pc_sum): %d" % (
        sum(1 for f in S if f["Rpub"] < 0.9 * f["Rinner"] and f["pc_sum"] > 1.05 * f["pub"]),
        sum(1 for f in S if f["Rpub"] < 0.9 * f["Rinner"] and f["inner"] > 1.05 * f["pc_sum"])))
    print("  frac_bg del pixel pico: min %.2f mediana %.2f max %.2f" % (
        min(f["frac_bg"] for f in S), st.median([f["frac_bg"] for f in S]), max(f["frac_bg"] for f in S)))
    print("  BT maxima del corpus pareado: %.2f K (techo de descarte del codigo %.2f K)" % (
        max(f["btmax"] for f in S), PP.TECHO[b]))

print("\nTABLA POR PASADA (protegidas con cumulo): t b zen MIR | Rpub Rpcsum Rinner Rbg20 Rnobg | f_req fs fa | spm nclu")
for f in sorted(ok, key=lambda f: (f["b"], f["zen"])):
    print("%s %-8s %5.1f %6.2f | %4.2f %4.2f %4.2f %4.2f %4.2f | %5.2f %4.2f %4.2f | %-5s %s" % (
        f["t"], f["b"], f["zen"], f["mir"], f["Rpub"], f["Rpcsum"], f["Rinner"], f["Rbg20"], f["Rnobg"],
        f["f_req"], f["fs"], f["fa"], f["spm"], f["n_clu"]))
json.dump(ok, open(os.path.join(D, "estratos.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
