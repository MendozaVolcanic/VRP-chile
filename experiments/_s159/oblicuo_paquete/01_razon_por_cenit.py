# -*- coding: utf-8 -*-
"""S159, frente «el paquete de MIROVA y el déficit oblicuo», paso 1: razón contra MIROVA por tramo de cenit.

POR QUÉ. Con el sensor oblicuo (cenit >= 50°) el píxel nativo de VIIRS 750 crece varias veces y un foco sub-píxel queda
diluido; nuestra magnitud de Chillán en erupción quedó en 0,16 de la de MIROVA (PR #869). El frente N midió que el
código entero de MIROVA en la grilla de GEO (oráculo) da razón 0,999 en 145 alertas, pero sólo con dos tramos de
cenit (<=40 y >40). Si el oráculo sigue cerca de 1 sobre 50°, el déficit oblicuo es el paquete (grilla, remuestreo,
fondo, suma); si cae, es otra cosa.

Sólo lee artefactos ya bajados (runs 39682867040 y 39693661527 del frente N); no baja nada, no toca el repositorio.

Pregunta 1 (si lo medido estuviera roto, ¿se vería?): la razón de K tiene que reproducir la del frente N (0,510 n=115),
la de F (0,990 n=163) y la del oráculo (0,999 n=145); si el pareo de alertas o la lectura de las columnas estuviera
mal, esos tres números no salen. Control positivo: placebo K x 1,2 tiene que mover la razón de K en x1,2 exacto.
Pregunta 2 (si el instrumento estuviera muerto): cada celda declara su n; n = 0 se imprime como SIN DATO, nunca como 0.
Las alertas que el oráculo no detecta se cuentan por tramo (no son razón 0, son ausencia).
Denominador: alertas de MIROVA que deciden (lab pos, decide), pasadas VIIRS 750 nocturnas del 2026-04-01 al
2026-10-21 sin el 18 y 19 de octubre, estado ok. Razones crudas (sin pesos) como en el §9 de N, y además ponderadas
por el peso de muestreo de cada clase (pos_resto pesa 3,06).
Uso: python 01_razon_por_cenit.py
"""
from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
N = AQUI.parent / "n"
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

ARTS = [Path(r"D:\vrp-trabajo\temporales\s159_n\run_39682867040")]
TRAMOS = (("<=25", 0, 25), ("25-40", 25, 40), ("40-50", 40, 50), (">50", 50, 99))
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def tramo(z):
    if z is None:
        return "z?"
    for nm, a, b in TRAMOS:
        if a < z <= b or (a == 0 and z <= b):
            return nm
    return "z?"


def wq(xs, ws=None):
    """mediana y cuartiles (ponderados si ws); interpolación por paso, como el §9 de N en el caso sin pesos."""
    if not xs:
        return None
    xs = np.asarray(xs, float)
    if ws is None:
        s = np.sort(xs)
        n = len(s)
        return float(np.median(s)), float(s[n // 4]), float(s[(3 * n) // 4]), n
    ws = np.asarray(ws, float)
    o = np.argsort(xs)
    xs, ws = xs[o], ws[o]
    c = np.cumsum(ws) / ws.sum()
    f = lambda p: float(xs[np.searchsorted(c, p)])
    return f(0.5), f(0.25), f(0.75), len(xs)


def fmt(t):
    return "SIN DATO (n=0)" if t is None else f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}] n={t[3]}"


def alerta_o(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inner


def main():
    obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
    tab = {int(r["id"]): r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
    res = {}
    for d in ARTS:
        for f in sorted(d.rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    inner = B.inner_desde_html()
    fl = lambda s: None if s in ("", None) else float(s)
    tb = lambda s: s == "True"

    pos = [i for i, o in obj.items() if o["lab"] == "pos" and o["decide"] and (res.get(i) or {}).get("estado") == "ok"
           and o["clase"] != "diurna"]
    pr(f"alertas que deciden con estado ok: {len(pos)} (esperado 181, N)")

    # cenit: el del centro de la grilla (lo mide el probe en el gránulo) y el del record de producción
    zc = {i: (res[i].get("geometria_centro") or {}).get("sensor_zenith") for i in pos}
    zr = {i: obj[i].get("z") for i in pos}
    d = [abs(zc[i] - zr[i]) for i in pos if zc[i] is not None and zr[i] is not None]
    pr(f"cenit centro de grilla vs cenit del record: n={len(d)}, |dif| mediana {np.median(d):.2f}, max {max(d):.2f};"
       f" sin cenit de centro {sum(zc[i] is None for i in pos)}")
    cambia = sum(tramo(zc[i]) != tramo(zr[i]) for i in pos if zc[i] is not None and zr[i] is not None)
    pr(f"pasadas que cambian de tramo segun cual cenit se use: {cambia} de {len(d)}")
    Z = {i: zc[i] if zc[i] is not None else zr[i] for i in pos}

    def fila(i):
        t = tab[i]
        o = res[i]["oraculo"]
        return {
            "v": obj[i]["volcan"], "m": obj[i]["mirova_vrp"], "w": obj[i]["peso"], "prot": obj[i]["protegida"],
            "Kpub": tb(t["K_pub"]), "Kpc": fl(t["K_pc"]), "Kn": fl(t["K_n"]),
            "Fpub": tb(t["F_pub"]), "Fpc": fl(t["F_pc"]), "Fn": fl(t["F_n"]),
            "Odet": alerta_o(o.get("geo_linear"), inner[obj[i]["volcan"]]),
            "Ovrp": (o.get("geo_linear") or {}).get("vrp_mw"), "On": (o.get("geo_linear") or {}).get("npix"),
            "Sdet": alerta_o(o.get("geo_linear_anillo_sensible"), inner[obj[i]["volcan"]]),
            "Svrp": (o.get("geo_linear_anillo_sensible") or {}).get("vrp_mw"),
            "Rdet": alerta_o(o.get("r2_linear"), inner[obj[i]["volcan"]]),
            "Rvrp": (o.get("r2_linear") or {}).get("vrp_mw"),
            "Ndet": alerta_o(o.get("geo_nearest"), inner[obj[i]["volcan"]]),
            "Nvrp": (o.get("geo_nearest") or {}).get("vrp_mw"),
            "Opub_tab": tb(t["O_pub"]),
        }
    FI = {i: fila(i) for i in pos}
    dis = sum(FI[i]["Odet"] != FI[i]["Opub_tab"] for i in pos)
    pr(f"control: deteccion del oraculo releida contra la columna O_pub de N: {dis} discrepancias de {len(pos)}")

    def razones(ids, brazo, pesos=False):
        xs, ws = [], []
        for i in ids:
            f = FI[i]
            if not f["m"]:
                continue
            if brazo == "K" and f["Kpub"]:
                xs.append(f["Kpc"] / f["m"])
            elif brazo == "placebo" and f["Kpub"]:
                xs.append(1.2 * f["Kpc"] / f["m"])
            elif brazo == "F" and f["Fpub"]:
                xs.append(f["Fpc"] / f["m"])
            elif brazo == "O" and f["Odet"]:
                xs.append(f["Ovrp"] / f["m"])
            elif brazo == "S" and f["Sdet"]:
                xs.append(f["Svrp"] / f["m"])
            else:
                continue
            ws.append(f["w"])
        return wq(xs, ws if pesos else None)

    pr("\n== 0. controles contra el §9 de N (todas, crudo)")
    for b, esp in (("K", "0.510 [0.370, 0.733] n=115"), ("F", "0.990 [0.703, 1.290] n=163"),
                   ("O", "0.999 [0.978, 1.007] n=145"), ("placebo", "0.612")):
        pr(f"   {b:8s} {fmt(razones(pos, b))}   (N: {esp})")

    def tabla(ids, titulo):
        pr(f"\n== {titulo}")
        pr("   tramo  | alertas | K publica / razon | F publica / razon | oraculo detecta / razon | oraculo no detecta"
           " | recuadro sensible detecta / razon")
        for nm, _, _ in TRAMOS + (("todas", 0, 0),):
            ss = ids if nm == "todas" else [i for i in ids if tramo(Z[i]) == nm]
            if not ss:
                pr(f"   {nm:6s} | 0 | SIN DATO")
                continue
            kp = sum(FI[i]["Kpub"] for i in ss)
            fp = sum(FI[i]["Fpub"] for i in ss)
            od = sum(FI[i]["Odet"] for i in ss)
            sd = sum(FI[i]["Sdet"] for i in ss)
            pr(f"   {nm:6s} | {len(ss):3d} | K {kp:3d} {fmt(razones(ss, 'K'))} | F {fp:3d} {fmt(razones(ss, 'F'))} |"
               f" O {od:3d} {fmt(razones(ss, 'O'))} | no det {len(ss) - od:3d} | S {sd:3d} {fmt(razones(ss, 'S'))}")

    chi = [i for i in pos if FI[i]["v"] == "NevadosDeChillan"]
    sin = [i for i in pos if FI[i]["v"] != "NevadosDeChillan"]
    tabla(pos, "1. todas las alertas que deciden, crudo")
    tabla(sin, "2. sin Chillan, crudo")
    tabla(chi, "3. Chillan sola, crudo")

    pr("\n== 4. ponderado por peso de muestreo (todas)")
    for nm, _, _ in TRAMOS:
        ss = [i for i in pos if tramo(Z[i]) == nm]
        pr(f"   {nm:6s} K {fmt(razones(ss, 'K', True))} | F {fmt(razones(ss, 'F', True))} | "
           f"O {fmt(razones(ss, 'O', True))}")

    pr("\n== 5. por volcan y tramo (crudo): n alertas, razon K / F / O (mediana y n)")
    for v in sorted({FI[i]["v"] for i in pos}):
        partes = []
        for nm, _, _ in TRAMOS:
            ss = [i for i in pos if FI[i]["v"] == v and tramo(Z[i]) == nm]
            if not ss:
                continue
            g = lambda b: (lambda t: "-" if t is None else f"{t[0]:.2f}({t[3]})")(razones(ss, b))
            partes.append(f"{nm}: n{len(ss)} K{g('K')} F{g('F')} O{g('O')} Odet{sum(FI[i]['Odet'] for i in ss)}")
        pr(f"   {v:20s} " + " | ".join(partes))

    # ---------------- 6. atribución por pares
    pr("\n== 6. atribucion por pares (mediana [q1,q3] n del cociente en las alertas donde AMBOS tienen magnitud > 0)")
    pares = (
        ("F/K  (fondo y suma del codigo, misma deteccion nativa)", lambda f: f["Kpub"] and f["Fpub"] and f["Kpc"] > 0,
         lambda f: f["Fpc"] / f["Kpc"]),
        ("O/F  (deteccion + grilla + remuestreo; mismo fondo y suma)", lambda f: f["Fpub"] and f["Odet"] and f["Fpc"] > 0,
         lambda f: f["Ovrp"] / f["Fpc"]),
        ("O/F  solo pares con 1 px en F y en O", lambda f: f["Fpub"] and f["Odet"] and f["Fpc"] > 0
         and f["Fn"] == 1 and f["On"] == 1, lambda f: f["Ovrp"] / f["Fpc"]),
        ("O/K  (todo el paquete)", lambda f: f["Kpub"] and f["Odet"] and f["Kpc"] > 0, lambda f: f["Ovrp"] / f["Kpc"]),
        ("O_geo/O_r2 lineal (posicion de la grilla)", lambda f: f["Odet"] and f["Rdet"] and f["Rvrp"] > 0,
         lambda f: f["Ovrp"] / f["Rvrp"]),
        ("O_lineal/O_vecino (interpolador, grilla GEO)", lambda f: f["Odet"] and f["Ndet"] and f["Nvrp"] > 0,
         lambda f: f["Ovrp"] / f["Nvrp"]),
    )
    for nom, cond, val in pares:
        pr(f"   {nom}")
        for nm, _, _ in TRAMOS + (("todas", 0, 0),):
            ss = pos if nm == "todas" else [i for i in pos if tramo(Z[i]) == nm]
            xs = [val(FI[i]) for i in ss if cond(FI[i])]
            pr(f"      {nm:6s} {fmt(wq(xs))}")

    # ---------------- 7. lista de las alertas con cenit > 50
    pr("\n== 7. alertas con cenit > 50: volcan hora z MIROVA | K pub pc n | F pub pc n | O det vrp npix | S det vrp")
    for i in sorted([i for i in pos if tramo(Z[i]) == ">50"], key=lambda i: (FI[i]["v"], obj[i]["hora_utc"])):
        f = FI[i]
        pr(f"   {i:3d} {f['v']:20s} {obj[i]['hora_utc']} z{Z[i]:5.1f} M{f['m']:6.2f} | K {int(f['Kpub'])} {f['Kpc']} "
           f"{f['Kn']} | F {int(f['Fpub'])} {f['Fpc']} {f['Fn']} | O {int(f['Odet'])} "
           f"{None if f['Ovrp'] is None else round(f['Ovrp'], 3)} {f['On']} | S {int(f['Sdet'])} "
           f"{None if f['Svrp'] is None else round(f['Svrp'], 3)}")

    # ---------------- 8. Chillán: cuántas alertas en la ventana y con qué cenit
    pr("\n== 8. Chillan en el lote: alertas por tramo y magnitud de MIROVA")
    for nm, _, _ in TRAMOS:
        ss = [i for i in chi if tramo(Z[i]) == nm]
        pr(f"   {nm:6s} n={len(ss)} MIROVA: {sorted(round(FI[i]['m'], 2) for i in ss)}")
    (AQUI / "01_razon_por_cenit_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
