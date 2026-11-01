# -*- coding: utf-8 -*-
"""Pruebas de brazos.py, sin red. Las dos preguntas del instrumento:

(1) ¿Los brazos son los que dicen ser? (a) M14, PIX7 y SENS dan la BOX idéntica a mirova_port.caja «fisica», «pixel» y
    «sensible»; (b) recalculados SIN RED sobre las 150 grillas guardadas del lote de S159 (run 39712862945) dan npix y
    VRP idénticos a lo que el runner calculó entonces; (c) los tamaños de la ROI2 son 14 x 14, 13 x 13, 21 x 21 y 7 x 7
    celdas (salvo recorte en el borde) y el círculo tiene el área de inner_radius_km; (d) los brazos centrados en el
    cráter caen donde el cráter está (Tupungatito: a ~4,8 km al NW de M).
(2) ¿Puede dar distinto? Control positivo: sobre una escena sintética con un foco débil a 5 km al NW de M, M14 no lo ve
    y C14 / CIRC sí; sin foco ningún brazo ve nada. Si los brazos fueran todos el mismo, (2) fallaría.
Uso: python -I probar_brazos.py [--art D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import brazos as BR  # noqa: E402

MP, ORA = BR.MP, BR.ORA


def volcanes():
    d = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    lst = d["volcanoes"] if isinstance(d, dict) else d
    return {v["name"]: v for v in lst}


def prueba_cajas(V):
    obj = json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))
    vistos = {}
    for o in obj:
        if o["b"] == "VIIRS375" and o["volcan"] not in vistos:
            vistos[o["volcan"]] = o["grilla"]
    for vol, g in sorted(vistos.items()):
        v = V[vol]
        xc, yc = BR.crater_xy(g, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
        X0, Y0 = g["X0"], g["Y0"]
        for b, m in BR.EQUIV_S159.items():
            # La ROI2 tiene que ser idéntica; la ROI1 de «pixel» en S159 era 21 x 21 celdas y aquí es la física, pero
            # 0 y 1 tienen los mismos umbrales (lo comprueba la parte 3 sobre grillas reales).
            assert np.array_equal(BR.caja(g, b, X0, Y0, xc, yc, v["inner_radius_km"], vol) == 2,
                                  MP.caja(g, X0, Y0, m) == 2), (vol, b)
            if b != "PIX7":
                assert np.array_equal(BR.caja(g, b, X0, Y0, xc, yc, v["inner_radius_km"], vol), MP.caja(g, X0, Y0, m))
        tam = {b: int((BR.caja(g, b, X0, Y0, xc, yc, v["inner_radius_km"], vol) == 2).sum()) for b in BR.BRAZOS}
        esperado = {"M14": 196, "M13": 169, "M21": 441, "C13": 169, "C21": 441, "PIX7": 49}
        for b, n in esperado.items():
            assert tam[b] == n, (vol, b, tam[b], n)
        circ = np.pi * (v["inner_radius_km"] * 1000 / 375.0) ** 2
        assert abs(tam["CIRC"] - circ) / circ < 0.05 or v["inner_radius_km"] * 1000 > 25000, (vol, tam["CIRC"], circ)
        d_c = np.hypot(xc - X0, yc - Y0) / 1000
        print(f"  {vol:20s} cráter a {d_c:5.2f} km de M (dx {(xc - X0) / 1000:+.2f}, dy {(yc - Y0) / 1000:+.2f}); "
              f"celdas ROI2 {tam}")
    return vistos


def prueba_sintetica(V, grillas):
    vol = "Tupungatito"
    g, v = grillas[vol], V[vol]
    xc, yc = BR.crater_xy(g, v["vent_lat"], v["vent_lon"])
    X, Y = MP.centros(g)
    rng = np.random.default_rng(162)
    T = 262 + rng.normal(0, 0.8, X.shape)
    tir = ORA.temperatura_a_radiancia(T, MP.SENSORES["VIIRS375"]["lam_tir"])
    with MP.longitudes(MP.SENSORES["VIIRS375"]):
        mir0 = ORA.temperatura_a_radiancia(T - 2.0, 3.74)
    i = int(np.argmin(np.abs(Y[:, 0] - yc)))
    j = int(np.argmin(np.abs(X[0, :] - xc)))
    res = {}
    for foco in (False, True):
        mir = mir0.copy()
        if foco:
            mir[i, j] *= 1.4   # entre el umbral de cumbre y el de escena (barrido 1,2 a 1,6: M14 0, C14 1)
        res[foco] = BR.correr_brazos(mir, tir, g, g["X0"], g["Y0"], xc, yc, v["inner_radius_km"], vol, 0, 100.0)
    sin = {b: r["npix"] for b, r in res[False].items()}
    con = {b: r["npix"] for b, r in res[True].items()}
    print("  sintético Tupungatito, foco en el cráter, sin foco:", sin)
    print("  sintético Tupungatito, foco en el cráter, con foco:", con)
    assert all(n == 0 for n in sin.values()), "sin foco algún brazo detecta: la escena no es neutra"
    assert con["M14"] == 0 and con["C14"] >= 1 and con["CIRC"] >= 1, \
        "el foco débil del cráter debería verse sólo con umbrales de cumbre en el cráter"
    assert con["SENS_PT"] >= 1, "SENS_PT tiene que ser SENS en Tupungatito"


def prueba_s159(V, art):
    obj = {o["id"]: o for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json")
                                          .read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(Path(art).rglob("resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            res[r["id"]] = r
    n_ok = n_igual = 0
    distintos = []
    for i, r in sorted(res.items()):
        if r.get("estado") != "ok":
            continue
        z = list(Path(art).rglob(f"grilla_{i:03d}.npz"))
        assert len(z) == 1, (i, z)
        q = np.load(z[0])
        o = obj[i]
        g, v = o["grilla"], V[o["volcan"]]
        xc, yc = BR.crater_xy(g, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
        mine = BR.correr_brazos(q["mir"].astype(np.float64), q["tir"].astype(np.float64), g, g["X0"], g["Y0"], xc, yc,
                                v["inner_radius_km"], o["volcan"], r["dayflag"], r["sunglint"],
                                brazos=tuple(BR.EQUIV_S159))
        n_ok += 1
        todo = True
        for b, m in BR.EQUIV_S159.items():
            a, c = mine[b], r["port"][m]
            igual = a["npix"] == c["npix"] and ((a["vrp_mw"] is None and c["vrp_mw"] is None) or (
                a["vrp_mw"] is not None and c["vrp_mw"] is not None and abs(a["vrp_mw"] - c["vrp_mw"]) < 1e-6))
            if not igual:
                todo = False
                distintos.append((i, b, a["npix"], a["vrp_mw"], c["npix"], c["vrp_mw"]))
        n_igual += todo
    print(f"  S159 sin red: {n_igual} de {n_ok} pasadas con M14, PIX7 y SENS iguales al runner (npix y VRP a 1e-6 MW)")
    if distintos:
        print("   distintos:", distintos[:10])
    assert n_ok >= 140 and n_igual == n_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
    a = ap.parse_args()
    V = volcanes()
    print("1. cajas y tamaños")
    grillas = prueba_cajas(V)
    print("2. escena sintética (control positivo y negativo)")
    prueba_sintetica(V, grillas)
    print("3. recálculo sin red de las grillas de S159")
    if Path(a.art).exists():
        prueba_s159(V, a.art)
    else:
        print("  SIN DATO: no está la carpeta", a.art)
    print("PRUEBAS DE BRAZOS OK")


if __name__ == "__main__":
    main()
