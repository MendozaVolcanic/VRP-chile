# -*- coding: utf-8 -*-
"""S162 V750-A (S172): criterio 1 del §4.1 con la vara «MATLAB directo» (decisión de Nicolás del 2026-11-01).

POR QUÉ. El criterio 1 pide que la vía del pipeline (`pipeline/mirova_v750_codigo.py`) dé la misma máscara y el mismo
VRP que el código de MIROVA. Hasta S163 la referencia era el oráculo de Octave (`mirova_v750_r2`), que rellena el fondo
con Qhull; MATLAB, que es lo que corre MIROVA, rellena distinto (S163: 41 de 84 fondos). La vara de esta prueba es la
salida de MATLAB R2026b sobre las 311 escenas de O2 (`experiments/_s163_o2/`), sin intermediario: máscara índice por
índice y VRP con diferencia relativa de 1e-9 o menos (VS171-01). El poder de la vara se mide mutando LA VÍA MISMA y
juzgándola contra MATLAB en las 311 escenas, sin subconjunto (VS171-05).

Lo que esta vara no ve, y cómo se cubre:
- Remuestreo, caja, glint calculado, dayflag y corte de 45 km: las 311 entran ya grilladas. Lo sigue midiendo E3 de
  `equivalencia_v750a.py` (VS171-03).
- Halo de 7 celdas (más de 30 alertados) y celdas NaN en BOX: ninguna de las 311 los recorre (censo del verificador
  S171). Se cubren con escenas sintéticas (un bloque caliente de 8 x 8 sobre una escena real de O2; NaN puestos en BOX)
  juzgadas contra el oráculo de Octave con el relleno de MATLAB, que es un port independiente del .m (VS171-02 y 04).
  Esa parte no es «MATLAB directo»: un O3 en MATLAB con estas escenas la reemplazaría.

Uso: python experiments/_s162_v750a/vara_matlab_v750a.py [--modulo pipeline.mirova_v750_codigo | --ruta <vía.py>]
     [--salida <txt>]
Salida: 0 si la vía es VERDE, todas las mutaciones quedan atrapadas y los controles salen como deben; 1 si no.
"""
import argparse
import hashlib
import importlib
import sys
import types
from pathlib import Path

import numpy as np
import scipy.io as sio

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
O2 = RAIZ / "experiments/_s163_o2"
MD5 = {"entradas_o2.mat": "fb849b6a96a9d348e75cf502e21a326c", "resultado_o2.mat": "1f7fdc4bed0f8cb6223204bbce42ba43"}
TOL = 1e-9

# mutaciones de UNA línea de la vía, juzgadas contra MATLAB en las 311 (las cinco del §4.1 que se pueden escribir en la
# vía, más los caminos raros del .m que el verificador S171 mutó)
MUT_311 = {
    "k1_y_minimos": ("u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003",
                     "u_abs, s1, s2, n1, n2, e1, e2 = -0.8, 10, 5, 0.010, 0.003, 0.01, 0.003"),
    "ocho_vecinos": ("for i in range(3) for j in range(3)])", "for i in range(3) for j in range(3) if (i, j) != (1, 1)])"),
    "fondo_sin_halo": ("    enm[excl] = np.nan ", "    pass  # mutación "),
    "recorte": ("dL = L_hot - L_bk", "dL = float(np.nansum(np.maximum(m13[mascara] - fondo[mascara], 0.0)))"),
    "umbral_diurno": ("u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 15, 15, 0.02, 0.02, 0.02, 0.02",
                      "u_abs, s1, s2, n1, n2, e1, e2 = -0.5, 20, 20, 0.02, 0.02, 0.02, 0.02"),
    "sin_rechazo_glint": ("sunglint < 12", "sunglint < 0"),
    "sin_corte_200K": ("frio = bt15 <= 200", "frio = bt15 <= 0"),
}
# las que las 311 no recorren: se juzgan sobre las escenas sintéticas
MUT_SINT = {
    "halo_7_a_9": ("(5 if npix <= 30 else 7)", "(5 if npix <= 30 else 9)"),
    "ignora_nan_de_box": ("excl = np.isnan(box)", "excl = np.zeros(box.shape, bool)"),
}
CONTROL_CAIDA = ("def vrp_mirova(m13, mascara, coef=COEF_VRP_V750):",
                 "def vrp_mirova(m13, mascara, coef=COEF_VRP_V750):\n    raise RuntimeError('mutación de control')")


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def cargar_via(nombre, src, cambio=None):
    """La vía como módulo, desde su texto; con `cambio` (viejo, nuevo) reemplazado una sola vez."""
    if cambio:
        assert src.count(cambio[0]) == 1, (nombre, "el ancla aparece", src.count(cambio[0]), "veces")
        src = src.replace(cambio[0], cambio[1])
    m = types.ModuleType(f"pipeline._vara_{nombre}")
    m.__package__ = "pipeline"
    m.__file__ = str(RAIZ / "pipeline/mirova_v750_codigo.py")   # la vía resuelve sus rutas desde su archivo
    exec(compile(src, f"<vía {nombre}>", "exec"), m.__dict__)
    return m


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", default="pipeline.mirova_v750_codigo")
    ap.add_argument("--ruta", default="", help="texto de otra vía (p. ej. la de fb87ef554, control rojo)")
    ap.add_argument("--salida", default=str(Path(__file__).with_name("vara_matlab_v750a_salida.txt")))
    a = ap.parse_args()
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    ruta = Path(a.ruta) if a.ruta else Path(importlib.import_module(a.modulo).__file__)
    src = ruta.read_text(encoding="utf-8")
    pr(f"vía {ruta.name}: sha256 del texto {hashlib.sha256(src.encode('utf-8')).hexdigest()}")
    for f, esperado in MD5.items():
        got = md5(O2 / f)
        pr(f"referencia {f}: md5 {got} ({'igual al fijado' if got == esperado else 'DISTINTO DEL FIJADO ' + esperado})")
        if got != esperado:
            pr("== VARA MATLAB: SIN DATO (la referencia no es la fijada en el §4.1)")
            Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
            return 1
    E, R = sio.loadmat(O2 / "entradas_o2.mat"), sio.loadmat(O2 / "resultado_o2.mat")
    pr(f"MATLAB: {str(R['version_matlab'].ravel()[0])[:60]}")
    NE = E["M13"].shape[2]
    alert = R["NPIX"][:, 0] > 0

    def mask_matlab(i):
        m = np.zeros(67 * 67, bool)
        idx = R["ALERTAS"][i, 0].ravel().astype(int)
        if idx.size:
            m[idx - 1] = True
        return m.reshape((67, 67), order="F")

    def esc(i):
        return E["M13"][:, :, i], E["M15"][:, :, i], E["BOX"][:, :, i], float(E["DAY"][0, i]), float(E["SG"][0, i])

    def estado(mod, m13, m15, box, day, sg, ref_m, ref_v):
        m = np.asarray(mod.detectar_mirova(m13, m15, box, day, sg), bool)
        if not np.array_equal(m, ref_m):
            return "mascara"
        if not ref_m.any():
            return "ok"
        v = mod.vrp_mirova(m13, m)["VRP_MW"]
        return "ok" if np.isclose(v, ref_v, rtol=TOL, atol=0) else "vrp"

    def contra_matlab(mod):
        return [estado(mod, *esc(i), mask_matlab(i), R["VRP"][i, 0]) for i in range(NE)]

    malos = 0
    # [1] criterio 1: la vía contra MATLAB
    via = cargar_via("identidad", src)
    st = contra_matlab(via)
    ok = st.count("ok")
    dif = max(abs(via.vrp_mirova(esc(i)[0], mask_matlab(i))["VRP_MW"] - R["VRP"][i, 0]) / R["VRP"][i, 0]
              for i in range(NE) if alert[i])
    pr(f"== VARA MATLAB (criterio 1, §4.1): {'VERDE' if ok == NE else 'ROJA'}: {ok} de {NE} escenas iguales "
       f"({int(alert.sum())} con alerta; máscara distinta {st.count('mascara')}, VRP distinto {st.count('vrp')}); "
       f"diferencia relativa máxima de VRP {dif:.2e} (tolerancia {TOL:g})")
    malos += ok != NE

    # [2] poder: la vía mutada contra MATLAB en las 311
    pr("== mutaciones de la vía contra MATLAB, en las 311 escenas (ATRAPADA si alguna difiere; el conteo es el poder):")
    ORA = importlib.import_module("equivalencia_v750a").ORA   # oráculo de Octave con el relleno de MATLAB (main)
    mutadas = {k: cargar_via(k, src, v) for k, v in MUT_311.items()}
    mq = cargar_via("relleno_qhull", src)
    mq._fillmissing2_lineal = _qhull_relleno()   # VS171-01: la vía con el relleno de la vara vieja (Qhull)
    mutadas["relleno_qhull"] = mq
    for k, mod in mutadas.items():
        try:
            r = contra_matlab(mod)
            n = NE - r.count("ok")
            pr(f"   {k:20s} {'ATRAPADA' if n else 'NO ATRAPADA'}: {n} escenas distintas (máscara {r.count('mascara')}, "
               f"VRP {r.count('vrp')})")
            malos += n == 0
        except Exception as e:  # noqa: BLE001
            pr(f"   {k:20s} CAÍDA ({type(e).__name__}: {e}): una caída no cuenta como atrapada")
            malos += 1
    try:
        contra_matlab(cargar_via("control_caida", src, CONTROL_CAIDA))
        pr("   control_que_se_cae     NO SE CAYÓ: el control está roto")
        malos += 1
    except RuntimeError:
        pr("   control_que_se_cae     CAÍDA, como debe (no se cuenta como atrapada)")

    # [3] escenas sintéticas para los caminos que las 311 no recorren (VS171-02, VS171-04)
    sint = []
    noche = [i for i in range(NE) if E["DAY"][0, i] == 0 and np.isfinite(E["M13"][:, :, i]).all()
             and np.isfinite(E["SG"][0, i]) and E["SG"][0, i] >= 12]
    for i in noche[:8]:
        m13, m15, box, day, sg = (np.array(x, copy=True) if isinstance(x, np.ndarray) else x for x in esc(i))
        c = 33
        bloque = m13[c - 4:c + 4, c - 4:c + 4]
        m13[c - 4:c + 4, c - 4:c + 4] = bloque * (4.0 + 0.1 * np.arange(64).reshape(8, 8))   # erupción: 64 celdas
        sint.append(("halo", i, m13, m15, box, day, sg))
    for i in noche[8:16]:
        m13, m15, box, day, sg = (np.array(x, copy=True) if isinstance(x, np.ndarray) else x for x in esc(i))
        c = 33
        m13[c, c] = m13[c, c] * 6.0                                    # un foco en el cráter
        box = box.astype(float)
        box[c - 6:c - 3, c - 6:c - 3] = np.nan                         # celdas excluidas por volcán, junto al foco
        m13[c - 6:c - 3, c - 6:c - 3] = m13[c - 6:c - 3, c - 6:c - 3] * 5.0
        sint.append(("boxnan", i, m13, m15, box, day, sg))
    ref = []
    for tipo, i, m13, m15, box, day, sg in sint:
        rm = np.asarray(ORA.detectar(m13, m15, box, day, sg)[0], bool)
        rv = ORA.vrp(m13, rm)["VRP_MW"] if rm.any() else np.nan
        ref.append((rm, rv))
    npix = [int(r[0].sum()) for r in ref]
    n_halo = sum(1 for (t, *_), n in zip(sint, npix) if t == "halo" and n > 30)
    n_box = sum(1 for t, *_ in sint if t == "boxnan")
    pr(f"== escenas sintéticas contra el oráculo de Octave con el relleno de MATLAB: {len(sint)} ({n_halo} con más de "
       f"30 alertados, halo de 7; {n_box} con NaN en BOX); npix del oráculo {npix}")

    def contra_oraculo(mod):
        return [estado(mod, m13, m15, box, day, sg, rm, rv)
                for (_t, _i, m13, m15, box, day, sg), (rm, rv) in zip(sint, ref)]

    st = contra_oraculo(via)
    pr(f"   identidad (vía sin mutar): {'VERDE' if st.count('ok') == len(sint) else 'ROJA'}: {st.count('ok')} de "
       f"{len(sint)} (máscara distinta {st.count('mascara')}, VRP distinto {st.count('vrp')})")
    malos += st.count("ok") != len(sint) or n_halo == 0
    for k, v in MUT_SINT.items():
        r311 = NE - contra_matlab(cargar_via(k, src, v)).count("ok")
        r = contra_oraculo(cargar_via(k, src, v))
        n = len(sint) - r.count("ok")
        pr(f"   {k:20s} {'ATRAPADA' if n else 'NO ATRAPADA'} en las sintéticas: {n} distintas (máscara "
           f"{r.count('mascara')}, VRP {r.count('vrp')}); en las 311 de MATLAB: {r311} distintas")
        malos += n == 0

    # [4] censo de caminos de las 311 (VS171-04): cuántas escenas recorren cada rama del .m
    dia = int((E["DAY"][0] != 0).sum())
    glint = int(sum(1 for i in range(NE) if not (np.isfinite(E["SG"][0, i]) and E["SG"][0, i] >= 12)))
    frio = int(sum(1 for i in range(NE) if (via.radiancia_a_temperatura(E["M15"][:, :, i], via.LAMBDA_M15) <= 200).any()))
    boxnan = int(sum(1 for i in range(NE) if np.isnan(E["BOX"][:, :, i]).any()))
    pr(f"== censo de las 311 por rama del .m: de día {dia}, glint bajo 12° {glint}, alguna celda M15 a 200 K o menos "
       f"{frio}, NaN en BOX {boxnan}, más de 30 alertados {int((R['NPIX'][:, 0] > 30).sum())}")
    pr(f"== RESUMEN: {'TODO COMO SE ESPERA' if malos == 0 else f'{malos} FUERA DE LO ESPERADO'}")
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if malos == 0 else 1


def _qhull_relleno():
    """El fillmissing2 de Qhull del oráculo de Octave original (antes del parche de main), tomado de una copia fresca del
    módulo del oráculo: es la vía con el relleno de la vara vieja."""
    p = RAIZ / "experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py"
    m = types.ModuleType("mirova_v750_r2_qhull")
    exec(compile(p.read_text(encoding="utf-8"), str(p), "exec"), m.__dict__)
    return m._fillmissing2_lineal


if __name__ == "__main__":
    sys.exit(main())
