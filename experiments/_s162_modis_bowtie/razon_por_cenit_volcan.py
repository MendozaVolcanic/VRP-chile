# -*- coding: utf-8 -*-
"""S162 MOD-E, paso 1b: la tendencia de la razon port/MIROVA con el cenit (razon_por_cenit.py) separada por volcan, porque
la muestra mezcla Lascar (fuente persistente, casi todo bajo 40 grados) con Chillan (erupcion de octubre, mas oblicua):
una tendencia agrupada puede ser solo composicion (S126, «estratificar por volcan»). Misma entrada y misma razon que el
paso 1; Spearman por volcan con p por permutacion (5.000, semilla 162). Control: la suma de n por volcan tiene que dar
el n agrupado (89).
Uso: python -I razon_por_cenit_volcan.py --art ... --objetivos ...
"""
import argparse, glob, io, json, random, statistics as st, sys
from pathlib import Path


def spearman(x, y, rng, n_perm=5000):
    def rango(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(o): r[i] = k
        return r
    rx, ry, n = rango(x), rango(y), len(x)
    f = lambda a, b: 1 - 6 * sum((p - q) ** 2 for p, q in zip(a, b)) / (n * (n * n - 1))  # noqa: E731
    rho = f(rx, ry)
    c = 0
    for _ in range(n_perm):
        q = ry[:]; rng.shuffle(q); c += abs(f(rx, q)) >= abs(rho)
    return rho, c / n_perm


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--art", required=True); ap.add_argument("--objetivos", required=True)
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.load(open(a.objetivos, encoding="utf-8"))}
    res = []
    for p in sorted(glob.glob(str(Path(a.art) / "s159-portes-MODIS-*" / "resultados_MODIS_*.json"))):
        res += json.load(open(p, encoding="utf-8"))
    por = {}
    for r in res:
        if r.get("estado") != "ok":
            continue
        o = obj[r["id"]]; f = r["port"]["fisica"]
        if o["lab"] == "pos" and o.get("mirova_vrp") and f.get("npix", 0) > 0 and f.get("vrp_mw"):
            z = (r.get("geometria_centro") or {}).get("sensor_zenith", o["z"])
            por.setdefault(o["volcan"], []).append((z, f["vrp_mw"] / o["mirova_vrp"], o["hora_utc"]))
    rng = random.Random(162)
    tot = 0
    for v, xs in sorted(por.items(), key=lambda kv: -len(kv[1])):
        tot += len(xs)
        z = [x[0] for x in xs]; rz = [x[1] for x in xs]
        bajo = [r for zz, r, _ in xs if zz < 25]; alto = [r for zz, r, _ in xs if zz >= 25]
        linea = f"{v}: n {len(xs)}; cenit {min(z):.1f} a {max(z):.1f}; mediana bajo 25 {st.median(bajo):.3f} [{len(bajo)}]" if bajo else f"{v}: n {len(xs)}"
        if alto:
            linea += f", desde 25 {st.median(alto):.3f} [{len(alto)}]"
        if len(xs) >= 6:
            rho, p = spearman(z, rz, rng)
            linea += f"; Spearman rho {rho:.3f} p {p:.4f}"
        print(linea)
        if len(xs) < 12:
            for zz, r, h in sorted(xs):
                print(f"    {h} cenit {zz:.1f} razon {r:.3f}")
    print("control: n total", tot, "(agrupado 89)")


if __name__ == "__main__":
    main()
