# -*- coding: utf-8 -*-
"""Verificador S157 1.33(a): comprobaciones propias sobre a_pasadas_salida.json (re-corrido)."""
import io, json, math, random, statistics as st, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s157-magnitud-chillan")
d = json.loads((W / "experiments/_s157_magnitud_chillan/a_pasadas_salida.json").read_text(encoding="utf-8"))
P = d["pasadas"]
rec = {(r["sensor"], r["datetime_utc"]): r for r in json.loads((W / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))["records"]}
random.seed(1)

def ols(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return b, my - b * mx

def corr(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))

def ols2(X1, X2, Y):
    # y = a + b1 x1 + b2 x2, por ecuaciones normales
    n = len(Y); m1, m2, my = st.mean(X1), st.mean(X2), st.mean(Y)
    s11 = sum((a - m1) ** 2 for a in X1); s22 = sum((a - m2) ** 2 for a in X2)
    s12 = sum((a - m1) * (b - m2) for a, b in zip(X1, X2))
    s1y = sum((a - m1) * (c - my) for a, c in zip(X1, Y)); s2y = sum((b - m2) * (c - my) for b, c in zip(X2, Y))
    det = s11 * s22 - s12 ** 2
    return (s22 * s1y - s12 * s2y) / det, (s11 * s2y - s12 * s1y) / det

print("== 1. README §1: passes M>=9 en VIIRS375: t_max y t_bg")
g = [p for p in P if p["b"] == "VIIRS375" and p["M"] >= 9]
print("  n", len(g), "t_max", min(p["t_max"] for p in g), max(p["t_max"] for p in g), "t_bg", min(p["t_bg_anillo"] for p in g), max(p["t_bg_anillo"] for p in g))

print("== 2. Tabla 2.1 (06:48 y nadir)")
for p in P:
    if p["pasada"].startswith("2026-10-18") and p["pasada"][11:] in ("06:48", "06:00", "05:42"):
        print("  %s %s z%.1f M%.2f D%.2f R%.2f Frec%.2f G%.2f Gm10 %.2f Gf0 %.2f fa %.2f Ga %.2f" % (p["pasada"], p["b"], p["cenital"], p["M"], p["D"], p["R"], p["F_rec"], p["G"], p["G_fondo_m10"], p["G_fondo0"], p["f_area"], p["G_area"]))
r = rec[("VIIRS_NOAA21_750", "2026-10-18 06:48")]
print("  06:48 V750 pixeles:", [(round(x["bt_k"], 1), round(x["dist_km"], 2), round(x["vrp_mw"], 3)) for x in r["anomaly_pixels"]], "t_bg", r["t_bg_k"])
print("  06:48 V750 primary_cluster:", {k: r["primary_cluster"].get(k) for k in ("n_pixels", "vrp_mw", "single_pixel_mode")})

print("== 3. Recorte a cero")
c = [p for p in P if p["n_recortados_a_cero"] > 0]
fc = [p["F_cero"] for p in c if p["F_cero"] is not None]
print("  pasadas con recorte", len(c), "de", len(P), "F_cero min/max", min(fc), max(fc), "F_cero None", sum(1 for p in c if p["F_cero"] is None))

print("== 4. Seleccion: S_todos vs S_in y n_dentro por banda")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for zb in ("<30", "30-50", ">=50"):
        gg = [p for p in P if p["b"] == b and p["banda_cenital"] == zb]
        if gg:
            print("  %s %s n%d n_dentro med %.1f  S_todos/S_in med %.2f  n_alertados>n_dentro: %d" % (b, zb, len(gg), st.median(p["n_dentro"] for p in gg), st.median(p["S_todos"] / p["S_in"] for p in gg if p["S_in"]), sum(1 for p in gg if p["n_alertados"] > p["n_dentro"])))

print("== 5. Area: regresion log G contra log f_area (y cenital) por sensor")
for b in ("VIIRS375", "VIIRS750"):
    gg = [p for p in P if p["b"] == b and p["G"] > 0]
    x = [math.log(p["f_area"]) for p in gg]; y = [math.log(p["G"]) for p in gg]; z = [p["cenital"] for p in gg]
    sl, ic = ols(x, y)
    # bootstrap pendiente
    bs = []
    for _ in range(2000):
        idx = [random.randrange(len(gg)) for _ in gg]
        xx = [x[i] for i in idx]; yy = [y[i] for i in idx]
        if len(set(xx)) > 2:
            bs.append(ols(xx, yy)[0])
    bs.sort()
    b1, b2 = ols2(x, [math.radians(v) for v in z], y)
    zz = [1 / math.cos(math.radians(v)) for v in z]
    b1s, b2s = ols2(x, zz, y)
    print("  %s n%d pendiente log G ~ log f = %.2f [%.2f; %.2f] (−1 = el área lo explica todo; 0 = nada)" % (b, len(gg), sl, bs[50], bs[1949]))
    print("     multiple: log f %.2f, cenital(rad) %.2f | con sec(z): log f %.2f, sec %.2f  corr(log f, sec z) %.2f" % (b1, b2, b1s, b2s, corr(x, zz)))
    # pesos: excluir pasadas debiles M<1
    g2 = [p for p in gg if p["M"] >= 1]
    sl2, _ = ols([math.log(p["f_area"]) for p in g2], [math.log(p["G"]) for p in g2])
    print("     solo M>=1 MW: n%d pendiente %.2f" % (len(g2), sl2))

print("== 6. Diente de sierra: pasadas VIIRS375 con cenital 50-58 (agregacion 1:1, f chica) contra 44-50 (2:1, f grande)")
for b in ("VIIRS375", "VIIRS750"):
    A = [p for p in P if p["b"] == b and 44 <= p["cenital"] < 52.6]
    B = [p for p in P if p["b"] == b and 52.6 <= p["cenital"] < 58.5]
    for nom, gg in (("44-52.6 (2:1)", A), ("52.6-58.5 (1:1)", B)):
        if gg:
            print("  %s %s n%d f med %.2f G med %.2f Gf0 med %.2f  Gs %s" % (b, nom, len(gg), st.median(p["f_area"] for p in gg), st.median(p["G"] for p in gg), st.median(p["G_fondo0"] for p in gg), [round(p["G"], 2) for p in gg]))

print("== 7. G_area: tendencia relativa a nadir y bootstrap de medianas por banda")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for zb in ("<30", "30-50", ">=50"):
        gg = [p["G_area"] for p in P if p["b"] == b and p["banda_cenital"] == zb]
        g0 = [p["G"] for p in P if p["b"] == b and p["banda_cenital"] == zb]
        if len(gg) < 3:
            continue
        bs = sorted(st.median(random.choices(gg, k=len(gg))) for _ in range(2000))
        bs0 = sorted(st.median(random.choices(g0, k=len(g0))) for _ in range(2000))
        q = sorted(gg)
        print("  %s %-5s n%2d G med %.2f [%.2f; %.2f]  G_area med %.2f [%.2f; %.2f] cuartiles %.2f-%.2f  G_area>=1: %d" % (b, zb, len(gg), st.median(g0), bs0[50], bs0[1949], st.median(gg), bs[50], bs[1949], q[len(q) // 4], q[3 * len(q) // 4], sum(1 for v in gg if v >= 1)))

print("== 8. Techo con fondo cero, cuantas oblicuas (z>=30) 375 no cierran, y con pixel MAS CALIENTE replicado")
gg = [p for p in P if p["b"] == "VIIRS375" and p["cenital"] >= 30]
print("  n", len(gg), "G_f0<1:", sum(1 for p in gg if p["G_fondo0"] < 1), " G_area_fondo0<1:", sum(1 for p in gg if p["G_area_fondo0"] < 1))
# cuantos pixeles adicionales a la temperatura del fondo+X harian falta: pixeles al t_max (cota) necesarios para cerrar con fondo de anillo
import importlib
sys.path.insert(0, str(W)); sys.path.insert(0, str(W / "experiments/_s157_magnitud_chillan"))
print("  n_dentro mediana oblicuas 375:", st.median(p["n_dentro"] for p in gg), " nadir:", st.median(p["n_dentro"] for p in P if p["b"] == "VIIRS375" and p["cenital"] < 30))

print("== 9. Testigo de saturacion: nulo")
T = d["testigo_saturacion_i4"]
zmap = {(p["pasada"], p["b"]): p["cenital"] for p in P}
xs = [math.log(t["S750_sobre_S375"]) for t in T]; ys = [math.log(t["M750"] / t["M375"]) for t in T]
zs = [zmap.get((t["pasada"][:16], "VIIRS375")) for t in T]
print("  corr", round(corr(xs, ys), 3), "n", len(T), " pendiente y~x", round(ols(xs, ys)[0], 2))
print("  corr(x, cenital)", round(corr(xs, zs), 3), " corr(y, cenital)", round(corr(ys, zs), 3))
# parcial controlando cenital
bx, ax = ols(zs, xs); by, ay = ols(zs, ys)
rx = [x - (ax + bx * z) for x, z in zip(xs, zs)]; ry = [y - (ay + by * z) for y, z in zip(ys, zs)]
print("  corr parcial (control cenital lineal)", round(corr(rx, ry), 3))
# nulo por barajado dentro de bandas de cenital
nul = []
for _ in range(5000):
    yy = ys[:]
    random.shuffle(yy)
    nul.append(corr(xs, yy))
nul.sort()
print("  nulo barajado libre: p95 %.2f p99 %.2f" % (nul[4750], nul[4950]))
# t_max 375 vs ratio
tm = [ (next(p for p in P if p["pasada"] == t["pasada"][:16] and p["b"] == "VIIRS375"))["t_max"] for t in T]
print("  corr(x, t_max375)", round(corr(xs, tm), 3), " corr(y, t_max375)", round(corr(ys, tm), 3))
# residuo: log(G750/G375) = x - y. ¿depende de algo?
res = [x - y for x, y in zip(xs, ys)]
print("  log(G750/G375): mediana %.2f, sd %.2f, corr con cenital %.2f, con t_max375 %.2f" % (st.median(res), st.pstdev(res), corr(res, zs), corr(res, tm)))
print("  sd(x) %.2f sd(y) %.2f" % (st.pstdev(xs), st.pstdev(ys)))
# pixeles 375 cerca del techo
print("  pasadas 375 con cerca_del_techo:", sum(1 for p in P if p["b"] == "VIIRS375" and p["cerca_del_techo"]))

print("== 10. G375 vs G750 por pasada (fondo/area comun?)")
pairs = []
for t in T:
    a = next(p for p in P if p["pasada"] == t["pasada"][:16] and p["b"] == "VIIRS375")
    b = next(p for p in P if p["pasada"] == t["pasada"][:16] and p["b"] == "VIIRS750")
    pairs.append((math.log(a["G"]), math.log(b["G"]), a["cenital"]))
print("  corr(logG375, logG750)", round(corr([p[0] for p in pairs], [p[1] for p in pairs]), 3))

print("== 11. Sensibilidad al fondo en 750: dT exceso (t_max - t_bg) contra cenital, y alza -10K contra dT")
for b in ("VIIRS750", "VIIRS375"):
    gg = [p for p in P if p["b"] == b]
    dT = [p["t_max"] - p["t_bg_anillo"] for p in gg]; al = [p["G_fondo_m10"] / p["G"] for p in gg]; z = [p["cenital"] for p in gg]
    print("  %s corr(dT, cenital) %.2f  corr(log alza, log dT) %.2f  corr(log alza, cenital) %.2f" % (b, corr(dT, z), corr([math.log(a) for a in al], [math.log(max(x, .1)) for x in dT]), corr([math.log(a) for a in al], z)))
    b1, b2 = ols2([math.log(max(x, .1)) for x in dT], z, [math.log(a) for a in al])
    print("     multiple log alza ~ log dT + cenital: %.3f, %.4f" % (b1, b2))
