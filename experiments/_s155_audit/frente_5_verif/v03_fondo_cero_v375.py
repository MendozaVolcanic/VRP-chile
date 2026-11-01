# -*- coding: utf-8 -*-
"""Verificador F5, paso 3: en VIIRS 375, cuanto puede subir la magnitud cambiando SOLO el fondo.

Fisica: la energia de un pixel es area x k x (L_pixel - L_fondo). Ningun fondo puede tener radiancia
negativa, asi que el fondo CERO es la cota superior de lo que cualquier cambio de fondo (D25 incluido)
puede hacer sobre el MISMO conjunto de pixeles. Si con fondo cero la razon contra MIROVA sigue cayendo
con el cenit, el fondo no explica la caida.

Paso previo obligatorio (control de formula): reconstruir la VRP de cada pixel guardado desde bt_k y
t_bg_k con la formula de process_viirs.py:1459-1507 (fondo global del anillo, porque Chillan no tiene
local_kernel_bg en volcanoes.yaml -> scripts/run_pipeline.py:244 da False) y comparar con vrp_mw
guardado. Si no calza, la cota no vale y se dice.

Preguntas del instrumento:
1. Si la formula reconstruida no fuera la del codigo, lo veria? Si: control de reconstruccion por pixel.
2. Instrumento muerto: pasada sin anomaly_pixels -> se excluye y se cuenta aparte.
Control positivo: con fondo cero la magnitud tiene que SUBIR en todas las pasadas (si no sube en
alguna, la reconstruccion esta mal).
"""
import io, json, math, os, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
C1, C2 = 1.191042e8, 14388.0
LAM, K, A = 3.740, 18.0, 140625.0
F5_R, F5_BT = 0.75, 295.0
INNER = 5.0


def L(t):
    return C1 / (LAM ** 5 * (math.exp(C2 / (LAM * t)) - 1))


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def f5_conjunto(ap, pc):
    cand = [p for p in ap if hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= INNER]
    if not cand:
        return []
    pk = max(range(len(cand)), key=lambda i: cand[i]["vrp_mw"])  # el JS toma el primer maximo; aqui igual
    pk = [i for i in range(len(cand)) if cand[i]["vrp_mw"] == cand[pk]["vrp_mw"]][0]
    return [p for i, p in enumerate(cand) if i == pk or hav(p["lat"], p["lon"], cand[pk]["lat"], cand[pk]["lon"]) <= F5_R or p["bt_k"] >= F5_BT]


def main():
    pares = json.load(open(os.path.join(AQUI, "pares_remoto.json"), encoding="utf-8"))
    d = json.load(open(os.path.join(AQUI, "..", "..", "..", "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
    idx = {(r["datetime_utc"][:16], r["sensor"]): r for r in d["records"]}
    errs, filas, sin = [], [], 0
    for f in pares:
        if f["b"] != "VIIRS375":
            continue
        r = idx[(f["t"], f["sensor"])]
        ap, pc = r.get("anomaly_pixels") or [], r.get("primary_cluster")
        if not ap or not pc or not f["mir"]:
            sin += 1; continue
        tbg = r["t_bg_k"]
        for p in ap:
            rec = max(L(p["bt_k"]) - L(tbg), 0) * A * K / 1e6
            errs.append(abs(rec - p["vrp_mw"]) / max(p["vrp_mw"], 1e-3) if p["vrp_mw"] > 0.001 else abs(rec - p["vrp_mw"]))
        s = f5_conjunto(ap, pc)
        pub_f5 = sum(p["vrp_mw"] for p in s)
        cero = sum(L(p["bt_k"]) * A * K / 1e6 for p in s)
        todos_inner = sum(p["vrp_mw"] for p in ap if hav(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= INNER)
        filas.append(dict(t=f["t"], zen=f["zen"], pub=f["pub"], f5=pub_f5, cero=cero, todos=todos_inner, mir=f["mir"],
                          tbg=tbg, n=len(s), nap=len(ap), btmax=max(p["bt_k"] for p in ap)))
    errs.sort()
    print("control de formula: %d pixeles; error relativo mediano %.4f, p95 %.4f, max %.4f" % (
        len(errs), statistics.median(errs), errs[int(0.95 * len(errs))], errs[-1]))
    print("control F5 reconstruido vs f5_core_vrp_mw guardado: max |dif| = %.4f MW" % max(abs(x["f5"] - x["pub"]) for x in filas))
    print("pasadas V375 pareadas usables=%d, excluidas sin pixeles/pc=%d" % (len(filas), sin))
    print("control positivo (cero >= publicado en todas): %s" % all(x["cero"] >= x["f5"] - 1e-9 for x in filas))
    print("\npasada           zen   tbg    n  btmax   publ  cero   mir   r_pub r_cero  x_cero")
    for x in sorted(filas, key=lambda x: x["zen"]):
        print("%s %5.1f %6.1f %3d %6.1f %6.2f %6.2f %6.2f  %5.2f %5.2f  %5.2f" % (
            x["t"], x["zen"], x["tbg"], x["n"], x["btmax"], x["f5"], x["cero"], x["mir"], x["f5"] / x["mir"], x["cero"] / x["mir"], x["cero"] / x["f5"] if x["f5"] else float("nan")))
    print("\nbandas de cenit (medianas por pasada):")
    print("banda    n  r_pub  r_cero  x_cero_mediano  x_cero_max")
    for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
        e = [x for x in filas if lo <= x["zen"] < hi and x["f5"] > 0]
        if not e:
            continue
        print("%2d-%2d %4d  %5.2f  %5.2f  %6.2f  %6.2f" % (lo, hi, len(e), statistics.median(x["f5"] / x["mir"] for x in e),
              statistics.median(x["cero"] / x["mir"] for x in e), statistics.median(x["cero"] / x["f5"] for x in e), max(x["cero"] / x["f5"] for x in e)))
    print("\nmisma tabla solo con MIROVA >= 1 MW (alertas protegidas):")
    for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
        e = [x for x in filas if lo <= x["zen"] < hi and x["f5"] > 0 and x["mir"] >= 1]
        if not e:
            continue
        print("%2d-%2d %4d  %5.2f  %5.2f  %6.2f  %6.2f" % (lo, hi, len(e), statistics.median(x["f5"] / x["mir"] for x in e),
              statistics.median(x["cero"] / x["mir"] for x in e), statistics.median(x["cero"] / x["f5"] for x in e), max(x["cero"] / x["f5"] for x in e)))
    # Spearman simple razon_cero vs cenit
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); rr = [0] * len(v)
        for k, i in enumerate(o): rr[i] = k
        return rr
    e = [x for x in filas if x["f5"] > 0]
    a, b = rank([x["zen"] for x in e]), rank([x["cero"] / x["mir"] for x in e])
    n = len(e); ma, mb = sum(a) / n, sum(b) / n
    rho = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / math.sqrt(sum((v - ma) ** 2 for v in a) * sum((v - mb) ** 2 for v in b))
    b2 = rank([x["f5"] / x["mir"] for x in e])
    mb2 = sum(b2) / n
    rho2 = sum((a[i] - ma) * (b2[i] - mb2) for i in range(n)) / math.sqrt(sum((v - ma) ** 2 for v in a) * sum((v - mb2) ** 2 for v in b2))
    print("\nSpearman(cenit, razon publicada)=%.2f   Spearman(cenit, razon fondo cero)=%.2f   n=%d" % (rho2, rho, n))
    json.dump(filas, open(os.path.join(AQUI, "v375_fondo.json"), "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    main()
