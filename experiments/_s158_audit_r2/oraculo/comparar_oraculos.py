"""Compara el segundo oráculo (mirova_v750_r2) con el primero (experiments/_s158_oraculo_mirova/mirova_v750.py),
usado como caja negra, en Etna y en escenas sintéticas que ejercen los umbrales.

Pregunta 1: si uno de los dos ports tuviera un umbral, una máscara o un pase mal traducido, ¿se vería? Sólo en las
escenas que ejercen ese umbral; por eso las escenas se construyen para caer a ambos lados de cada uno (NTI absoluto,
mínimos de la caja externa y del ROI de cumbre, segundo pase, día y noche, sun-glint, escena inválida). Pregunta 2:
si la comparación estuviera muerta (por ejemplo, comparar listas vacías), el conteo de escenas con alertas sería 0;
se informa. Control positivo: una mutación deliberada del segundo oráculo (umbral NTI absoluto -0,7 -> -0,8) tiene
que producir discrepancias.

Lo que se compara: el CONJUNTO de píxeles alertados (exacto) y L_hot (exacto). El VRP se compara aparte porque el
fondo depende de la triangulación de Delaunay, que el .m no fija (firma_fillmissing2_salida.txt).
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mirova_v750_r2 as R2  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "o1", AQUI.parents[1] / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O1)

S = sio.loadmat(AQUI.parents[1] / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat")
BOX = S["BOX"].astype(float)
M13_E, M15_E = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float)


def mask_o1(m13, m15, box, day, sg):
    al = np.asarray(O1.hotspot_detection(m13, m15, box, day, sg), dtype=int).ravel()
    mk = np.zeros(m13.shape, bool)
    if al.size:
        # índices lineales en orden de columnas; se prueban base 0 y base 1 una sola vez abajo
        # ojo: ravel(order="F") de una matriz en orden C es una COPIA; escribir en ella no marca nada
        mk[np.unravel_index(al - BASE_O1, m13.shape, order="F")] = True
    return mk, al


# Detecta la base de índices del primer oráculo con Etna (5 píxeles conocidos).
sg_e = R2.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
ref_mask, ref_lista = R2.detectar(M13_E, M15_E, BOX, 0, sg_e)
al_e = np.asarray(O1.hotspot_detection(M13_E, M15_E, BOX, 0, sg_e), dtype=int).ravel()
BASE_O1 = 1 if set(al_e.tolist()) == set(ref_lista) else (0 if set((al_e + 1).tolist()) == set(ref_lista) else None)
assert BASE_O1 is not None, "los oraculos no coinciden en Etna"
print("base de indices del primer oraculo:", BASE_O1, "| alertas O1 Etna:", sorted(al_e.tolist()),
      "| R2:", sorted(ref_lista))


def escena(rng, tipo):
    """Fondo realista: el de Etna con el núcleo caliente aplanado + ruido + gradiente; fuentes insertadas."""
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
        if rng.random() < 0.5:  # vecino débil para ejercer el segundo pase
            m13[r, min(c + 1, 65)] *= 1 + (amp - 1) * rng.uniform(0.05, 0.3)
    if tipo == "dia":
        day = 1
        m13 = m13 * 1.6
    elif tipo == "glint":
        sg = rng.uniform(5, 20)
    elif tipo == "invalida":
        m15[rng.random(m15.shape) < rng.uniform(0.3, 0.6)] = 1e-3  # BT muy fría -> NaN
    return m13, m15, day, sg


def comparar(det_r2, n=600, semilla=7, etiqueta=""):
    rng = np.random.default_rng(semilla)
    tipos = ["noche"] * 6 + ["dia", "glint", "invalida"]
    dif, con_alerta, dif_lhot, rel_vrp = 0, 0, 0, []
    ejemplos, grandes = [], []
    for i in range(n):
        tipo = tipos[i % len(tipos)]
        m13, m15, day, sg = escena(rng, tipo)
        a, _ = det_r2(m13, m15, BOX, day, sg)
        b, _ = mask_o1(m13, m15, BOX, day, sg)
        if a.any() or b.any():
            con_alerta += 1
        if not np.array_equal(a, b):
            dif += 1
            if len(ejemplos) < 5:
                ejemplos.append((i, tipo, int(a.sum()), int(b.sum())))
            continue
        if a.any():
            r2 = R2.vrp(m13, a)
            o1 = O1.vrp(m13, np.flatnonzero(a.ravel(order="F")) + BASE_O1)
            if abs(r2["L_hot"] - o1[4]) > 1e-12:
                dif_lhot += 1
            rel_vrp.append(r2["VRP_MW"] / o1[0] - 1 if o1[0] else np.nan)
            if abs(rel_vrp[-1]) > 0.05 and len(grandes) < 4:
                rr, cc = np.nonzero(a)
                grandes.append((i, tipo, int(a.sum()), round(r2["VRP_MW"], 4), round(o1[0], 4),
                                list(zip(rr.tolist(), cc.tolist()))[:4]))
    rel = np.array(rel_vrp, float)
    print(f"[{etiqueta}] escenas={n} con_alerta(alguno)={con_alerta} mascaras_distintas={dif} "
          f"L_hot_distinto={dif_lhot} | VRP R2/O1-1: mediana {np.nanmedian(np.abs(rel)) if rel.size else float('nan'):.2e} "
          f"max {np.nanmax(np.abs(rel)) if rel.size else float('nan'):.2e} (n={rel.size})")
    if rel.size:
        for t in (0.001, 0.01, 0.05):
            print(f"   VRP |R2/O1-1| > {t}: {int(np.sum(np.abs(rel) > t))} de {rel.size}")
    for g in grandes:
        print("   VRP muy distinto (i, tipo, npix, VRP_R2, VRP_O1, pixeles):", g)
    for e in ejemplos:
        print("   ejemplo discrepancia (i, tipo, npix R2, npix O1):", e)


comparar(R2.detectar, etiqueta="R2 vs O1")


def mutante(viejo, nuevo):
    import types
    src = Path(R2.__file__).read_text(encoding="utf-8")
    assert viejo in src, viejo
    mod = types.ModuleType("r2m"); exec(compile(src.replace(viejo, nuevo), "r2m", "exec"), mod.__dict__)
    return mod.detectar


# Controles positivos (mutaciones del segundo oráculo que deben producir máscaras distintas):
NOCHE = "u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003"
comparar(mutante(NOCHE, NOCHE.replace("-0.7,", "-0.8,")), n=200, etiqueta="MUTANTE K1 -0.7->-0.8")
comparar(mutante(NOCHE, NOCHE.replace("0.02, 0.003, 0.01", "0.02, 0.03, 0.01")), n=200,
         etiqueta="MUTANTE minimo NTI ROI2 0.003->0.03")
comparar(mutante(NOCHE, NOCHE.replace("10, 5,", "5, 10,")), n=200, etiqueta="MUTANTE sigma ROI1<->ROI2")
comparar(mutante("p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1,",
                 "p2 = _pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol | ctx1 | True,"),
         n=200, etiqueta="MUTANTE sin segundo pase")

# VRP de Etna en ambos
o1e = O1.vrp(M13_E, al_e)
r2e = R2.vrp(M13_E, ref_mask)
print(f"Etna VRP_W: O1={o1e[0]*1e6:.1f} R2={r2e['VRP_MW']*1e6:.1f} OSF=9889528.4 | L_bk O1={o1e[5]:.9f} "
      f"R2={r2e['L_bk']:.9f} OSF=1.072886152")
