"""O1 (S159): arma las matrices de entrada para correr el .m original de MIROVA en Octave.

Pregunta 1 del instrumento: si un port tuviera un paso mal traducido, ¿esta batería lo vería? Sólo en las escenas que
ejercen ese paso. Por eso se juntan tres familias: la matriz de Etna (control contra un número de producción de
MIROVA), las 10 pasadas chilenas de la segunda ronda S158 (con sus variantes de interpolador, grilla y caja) y las 600
escenas sintéticas de `comparar_oraculos.py` (misma semilla 7, mismo generador copiado sin cambios), que caen a ambos
lados de cada umbral.
Pregunta 2: si el instrumento estuviera muerto (Octave no corre, lee mal el .mat), las listas saldrían vacías o con
otro tamaño; el comparador cuenta escenas con alerta y aborta si Etna no da 5 píxeles.

Sin red. Lee: Example/VIIRS750_example.mat, granulos/run_39641637298/**/recorte_*.npz, granulos/objetivos.json.
Escribe: entradas.mat y entradas_etiquetas.json en esta carpeta.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.interpolate import griddata

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parents[1]
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo"))
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "granulos"))
import mirova_v750_r2 as R2  # noqa: E402
from probe_granulos import caja_mirova, N, CELDA  # noqa: E402

S = sio.loadmat(EXP / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat")
BOX = S["BOX"].astype(float)
M13_E, M15_E = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float)
sg_e = R2.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
ref_mask, _ = R2.detectar(M13_E, M15_E, BOX, 0, sg_e)

M13s, M15s, BOXs, DAYs, SGs, etiq = [], [], [], [], [], []


def agregar(m13, m15, box, day, sg, e):
    M13s.append(np.asarray(m13, float)); M15s.append(np.asarray(m15, float)); BOXs.append(np.asarray(box, float))
    DAYs.append(float(day)); SGs.append(float(sg)); etiq.append(e)


# 1. Etna
agregar(M13_E, M15_E, BOX, int(S["dayflag"].item()), sg_e, {"familia": "etna", "id": "Etna_N20_2023-05-19_0054"})

# 2. Pasadas chilenas (run 39641637298)
GR = EXP / "_s158_audit_r2" / "granulos"
run = GR / "run_39641637298"
res = json.loads(Path(glob.glob(str(run / "**" / "resultados.json"), recursive=True)[0]).read_text())
obj = {(o["volcan"], o["hora_utc"]): o for o in json.loads((GR / "objetivos.json").read_text(encoding="utf-8"))}


def grilla(g, dx=0.0, dy=0.0):  # copia de analizar_variantes.grilla
    xs = g["ul_x"] + dx + CELDA * (np.arange(N) + 0.5)
    ys = g["ul_y"] + dy - CELDA * (np.arange(N) + 0.5)
    return np.meshgrid(xs, ys)


def caja_toda_sensible():  # copia de analizar_variantes.caja_toda_sensible
    b = caja_mirova(); b[(b == 1)] = 2; return b


n_pasadas = 0
for r in res:
    if r.get("estado") != "ok":
        continue
    n_pasadas += 1
    clave = f"{r['volcan']}_{r['hora_utc'].replace(' ', '_').replace(':', '')}"
    z = np.load(glob.glob(str(run / "**" / f"recorte_{clave}.npz"), recursive=True)[0])
    sg = r["sunglint"]; day = r["dayflag"]
    # 2a. las matrices exactas que guardó el run (las que vio el oráculo en el workflow)
    for metodo in ("linear", "nearest"):
        for nc, box in (("caja_def", caja_mirova()), ("anillo_sensible", caja_toda_sensible())):
            agregar(z[f"grilla_{metodo}_M13"], z[f"grilla_{metodo}_M15"], box, day, sg,
                    {"familia": "chile_guardada", "id": clave, "metodo": metodo, "dx": 0, "dy": 0, "caja": nc})
    # 2b. variantes de analizar_variantes.py, recalculadas sin red desde el recorte
    g = obj[(r["volcan"], r["hora_utc"])]["grilla"]
    ok = np.isfinite(z["m13"]) & np.isfinite(z["m15"])
    pts = np.column_stack([z["x"][ok], z["y"][ok]])
    for metodo in ("linear", "nearest", "cubic"):
        for (dx, dy) in ((0, 0), (375, 0), (-375, 0), (0, 375), (0, -375)):
            X, Y = grilla(g, dx, dy)
            m13 = griddata(pts, z["m13"][ok], (X, Y), method=metodo)
            m15 = griddata(pts, z["m15"][ok], (X, Y), method=metodo)
            agregar(m13, m15, caja_mirova(), day, sg,
                    {"familia": "chile_variante", "id": clave, "metodo": metodo, "dx": dx, "dy": dy, "caja": "caja_def"})


# 3. Escenas sintéticas: copia literal de comparar_oraculos.escena (semilla 7, 600 escenas)
def escena(rng, tipo):
    m13 = M13_E.copy(); m15 = M15_E.copy()
    m13[ref_mask] = np.median(M13_E)
    g = np.linspace(-1, 1, 67)
    m13 = m13 * (1 + rng.uniform(-0.05, 0.05) * g[None, :]) * (1 + rng.normal(0, rng.uniform(0.002, 0.02), m13.shape))
    m15 = m15 * (1 + rng.normal(0, 0.003, m15.shape))
    day, sg = 0, 100.0
    nf = rng.integers(0, 6)
    for _ in range(nf):
        zona = rng.choice([0, 1, 2])
        rr, cc = np.nonzero(BOX == zona)
        k = rng.integers(len(rr))
        r, c = rr[k], cc[k]
        if not (1 <= r <= 65 and 1 <= c <= 65):
            continue
        amp = rng.choice([1.02, 1.05, 1.1, 1.2, 1.5, 2.5, 6.0, 15.0])
        m13[r, c] *= amp
        if rng.random() < 0.5:
            m13[r, min(c + 1, 65)] *= 1 + (amp - 1) * rng.uniform(0.05, 0.3)
    if tipo == "dia":
        day = 1
        m13 = m13 * 1.6
    elif tipo == "glint":
        sg = rng.uniform(5, 20)
    elif tipo == "invalida":
        m15[rng.random(m15.shape) < rng.uniform(0.3, 0.6)] = 1e-3
    return m13, m15, day, sg


rng = np.random.default_rng(7)
tipos = ["noche"] * 6 + ["dia", "glint", "invalida"]
for i in range(600):
    tipo = tipos[i % len(tipos)]
    m13, m15, day, sg = escena(rng, tipo)
    agregar(m13, m15, BOX, day, sg, {"familia": "sintetica", "id": f"sint_{i:03d}", "tipo": tipo})

sio.savemat(AQUI / "entradas.mat", {
    "M13": np.stack(M13s, axis=2), "M15": np.stack(M15s, axis=2), "BOX": np.stack(BOXs, axis=2),
    "DAY": np.array(DAYs), "SG": np.array(SGs)}, do_compression=True)
(AQUI / "entradas_etiquetas.json").write_text(json.dumps(etiq, ensure_ascii=False, indent=0), encoding="utf-8")
from collections import Counter  # noqa: E402
print("escenas:", len(etiq), Counter(e["familia"] for e in etiq), "| pasadas chilenas ok:", n_pasadas)
