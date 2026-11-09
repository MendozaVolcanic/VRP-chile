# -*- coding: utf-8 -*-
"""s05: ¿coincide el cúmulo y no sólo el punto? Superposición de los píxeles alertados NUESTROS (anomaly_pixels del record de Chillán,
base 752d348bc, copiado por V5B) con la mancha de MIROVA (todas las celdas de C2), contra el nulo de otras pasadas.

Fenómeno: MIROVA suma TODOS los píxeles alertados de una pasada y la lámina los dibuja juntos (la mancha). Nosotros publicamos un
punto (final_hotspot) pero el record guarda los píxeles alertados. Comparar conjunto con conjunto evita usar «una celda de la mancha»
como si fuera «el píxel» y mira si el tamaño y la forma del cúmulo calzan, no sólo el punto.

Pre-registro (escrito antes de correr):
  - cov_N = fracción de nuestros píxeles alertados que caen a <= 1 celda (de la grilla de la lámina) de alguna celda de la mancha.
  - cov_M = fracción de las celdas de la mancha que caen a <= 1 celda de alguno de nuestros píxeles alertados.
  - Observado = nuestros píxeles de la pasada i contra la mancha de i; nulo = píxeles de otra pasada j (mismo volcán y sensor) contra la
    mancha de i. Mismo código para los dos (función `cobertura`). N1 = todas las otras; N3 = zenit +-5 y azimut +-30 grados.
  - Una mancha que NO es el cúmulo nuestro daría cov_N y cov_M cerca del nulo. Si cov_N ~ 1 pero cov_M << 1, nuestro cúmulo está dentro de la
    mancha pero la mancha es más grande (MIROVA alerta más píxeles que nosotros), y si cov_M ~ 1 y cov_N << 1, al revés.
  - Control del instrumento: contar píxeles alertados nuestros por pasada (si fueran todos 1, cov_N sería el mismo estadístico del punto).
Universo: aciertos de Chillán VIIRS 375 y 750 con lámina (los mismos de s03), sin filtrar por control (posición sola).
Salida: salidas/s05_cumulo.out.txt
"""
import datetime as dt, json, os, sys
import numpy as np
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib177 as M
L = M.L
sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(1771)
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
S2 = json.load(open(os.path.join(HERE, "salidas", "s02_manchas.json"), encoding="utf-8"))
CH = "NevadosDeChillan"
refs = json.load(open(os.path.join(HERE, "orig", "p6_tif_referencia_out.json"), encoding="utf-8"))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
d = json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\chillan_base.json", encoding="utf-8"))
rec = {(r["sensor"], str(r["datetime_utc"])[:16]): r for r in d["records"]}
gr = {}


def grilla(b):
    if b not in gr:
        ref = refs[f"ChillanNevadosde|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", "ChillanNevadosde_" + os.path.basename(ref["path"])))
        g["mc"] = (V[CH]["mirova_center_lat"], V[CH]["mirova_center_lon"])
        g["celda_km"] = abs(g["transform"].e) * 111.0
        gr[b] = g
    return gr[b]


def dazi(a, b):
    x = abs(a - b) % 360
    return min(x, 360 - x)


def cobertura(Mn, pix, celda):
    """(cov_N, cov_M) de un conjunto de píxeles nuestros `pix` [(lat, lon), ...] contra la mancha Mn."""
    if not pix:
        return None
    dN = [Mn.d_min(la, lo) for la, lo in pix]
    cov_N = float(np.mean([x <= celda * 1.0 + 1e-9 for x in dN]))
    cov_M = float(np.mean([min(L.hav(la, lo, mla, mlo) for la, lo in pix) <= celda * 1.0 + 1e-9 for mla, mlo in zip(Mn.lats, Mn.lons)]))
    return cov_N, cov_M


for nom, b in (("Chillán VIIRS 375", "VIIRS375"), ("Chillán VIIRS 750", "VIIRS750")):
    g = grilla(b)
    sub = [o for o in S2 if o["vol"] == CH and o["b"] == b]
    for o in sub:
        r = rec.get((o["sensor"], o["dt"]))
        o["pix"] = [(p["lat"], p["lon"]) for p in (r or {}).get("anomaly_pixels", [])]
        o["zen"], o["azi"] = ((r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg")) if r else (None, None))
        o["Mn"] = M.Mancha(o["C2"], g, g["mc"])
    ok = [o for o in sub if o["pix"]]
    npix = [len(o["pix"]) for o in ok]
    print(f"\n== {nom}: {len(ok)} de {len(sub)} aciertos con píxeles alertados nuestros en el record; píxeles alertados por pasada p50 {np.median(npix):.0f}, p90 {np.percentile(npix, 90):.0f}, max {max(npix)}; "
          f"celdas de la mancha p50 {np.median([o['Mn'].n_celdas for o in ok]):.0f}, p90 {np.percentile([o['Mn'].n_celdas for o in ok], 90):.0f}")
    print(f"   razón (celdas de la mancha) / (nuestros píxeles): mediana {np.median([o['Mn'].n_celdas / len(o['pix']) for o in ok]):.2f}")
    for etiq, fz, fa in (("N1 todas las otras", 999, 999), ("N3 zenit +-5 azimut +-30", 5, 30)):
        res = []
        for i, oi in enumerate(ok):
            if oi["zen"] is None:
                continue
            otros = [oj for j, oj in enumerate(ok) if j != i and oj["zen"] is not None and abs(oj["zen"] - oi["zen"]) <= fz and dazi(oj["azi"], oi["azi"]) <= fa]
            if len(otros) < 2:
                continue
            ob = cobertura(oi["Mn"], oi["pix"], g["celda_km"])
            nu = np.array([cobertura(oi["Mn"], oj["pix"], g["celda_km"]) for oj in otros], float)
            res.append((ob[0], ob[1], nu[:, 0].mean(), nu[:, 1].mean()))
        a = np.array(res)
        n = len(a)
        idx = rng.integers(0, n, size=(2000, n))
        def ic(x):
            bb = x[idx].mean(axis=1)
            return f"{x.mean():.2f} [{np.percentile(bb, 2.5):.2f}, {np.percentile(bb, 97.5):.2f}]"
        dN, dM = a[:, 0] - a[:, 2], a[:, 1] - a[:, 3]
        print(f"   {etiq:26s} n={n:3d} cov_N propio {ic(a[:, 0])} | nulo {ic(a[:, 2])} || cov_M propio {ic(a[:, 1])} | nulo {ic(a[:, 3])}")
        print(f"   {'':26s} diferencia propio - nulo (pareada por pasada): cov_N {ic(dN)} | cov_M {ic(dM)}")
