# -*- coding: utf-8 -*-
"""S162 V750-A: nulo de la prueba de equivalencia contra el MÓDULO REAL de pipeline/ (no contra el oráculo).

POR QUÉ (VA-09 del verificador del analizador, A110). `equivalencia_v750a.py --mutaciones` rompe el ORÁCULO, así que
dice que la prueba sabe ver una pieza cambiada, pero no que sabe verla en `pipeline/mirova_v750_codigo.py`. Aquí se
copia el módulo con UNA línea cambiada (`pipeline/_mut_<id>.py`), se corre la prueba con `--modulo` apuntando a la
copia y se exige que salga 1 con «ROJA:» (falla por aserción). La copia sin cambios tiene que salir VERDE y la mutación
que sólo hace caer el programa tiene que salir con traceback (caída), no como atrapada.
Uso: python mutar_modulo_v750a.py --insumos <...> --grillas <...> --recortes <...> [--hilos 7]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ORIG = RAIZ / "pipeline" / "mirova_v750_codigo.py"
MUT = {
    "identidad": (None, None, "VERDE"),
    "k1_menos_08": ("u_abs, s1, s2, n1, n2, e1, e2 = -0.7,", "u_abs, s1, s2, n1, n2, e1, e2 = -0.8,", "ATRAPADA"),
    "ocho_vecinos": ("for i in range(3) for j in range(3)])", "for i in range(3) for j in range(3) if (i, j) != (1, 1)])",
                     "ATRAPADA"),
    "fondo_sin_halo": ("structure=np.ones((k, k), bool)", "structure=np.ones((1, 1), bool)", "ATRAPADA"),
    "recorte_a_cero": ("L_bk = float(np.nansum(fondo[mascara]))",
                       "L_bk = float(np.nansum(np.minimum(fondo[mascara], m13[mascara])))", "ATRAPADA"),
    "sin_segundo_pase": ("mask = ctx1 | absol | p2[0] | p2[1] | p2[2]", "mask = ctx1 | absol", "ATRAPADA"),
    "piso_cumbre_0010": ("u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.003, 0.01, 0.003",
                         "u_abs, s1, s2, n1, n2, e1, e2 = -0.7, 10, 5, 0.02, 0.010, 0.01, 0.010", "ATRAPADA"),
    "remuestreo_vecino": ('(X, Y), method="linear"))', '(X, Y), method="nearest"))', "ATRAPADA"),
    "radio_recorte_30": ("RADIO_RECORTE_KM = 45.0 ", "RADIO_RECORTE_KM = 30.0 ", "ATRAPADA"),
    # el fillmissing2 de MATLAB (S163): cada pieza del desempate tiene que importar
    "fill_sin_desempate": ("if _lado_perturbado(pts[a], pts[b], pts[c], pts[d]) > 0:",
                           "if _incircle(pts[a], pts[b], pts[c], pts[d]) > 0:", "ATRAPADA"),
    "fill_ejes_cambiados": ("    filas, cols = np.indices(A.shape)\n    ok = np.isfinite(A)",
                            "    cols, filas = np.indices(A.shape)\n    ok = np.isfinite(A)", "ATRAPADA"),
    "fill_lexico_invertido": ("key=lambda t: t[0])", "key=lambda t: t[0][::-1])", "ATRAPADA"),
    # MATLAB no extrapola fuera de la envolvente (S163): un relleno por vecino más cercano ahí tiene que caer en el oro
    "fill_vecino_fuera": ("    B[~ok] = out          # lo que ningún triángulo cubre",
                          "    out = np.where(np.isnan(out), __import__('scipy.interpolate', fromlist=['griddata'])"
                          ".griddata(P.astype(float), val, Q.astype(float), method='nearest'), out)\n"
                          "    B[~ok] = out          # lo que ningún triángulo cubre", "ATRAPADA"),
    # rivales estructurados (verificador de S163, rama s163-o2-alternativa c95483d31): las otras simetrías del marco
    # calzan 159 a 160 de 166 escenas de O2, así que «ejes cambiados» sola es un control débil
    **{f"fill_simetria_{nom}": ("    filas, cols = np.indices(A.shape)\n    ok = np.isfinite(A)",
                                f"    filas, cols = (lambda f, c: {expr})(*np.indices(A.shape))\n    ok = np.isfinite(A)",
                                "ATRAPADA")
       for nom, expr in (("menos_fila", "(-f, c)"), ("menos_col", "(f, -c)"), ("menos_ambas", "(-f, -c)"),
                         ("col_menos_fila", "(c, -f)"), ("menos_col_fila", "(-c, f)"), ("menos_col_menos_fila", "(-c, -f)"))},
    "control_que_se_cae": ("    m13 = np.asarray(m13, float)\n    vacio = np.zeros(m13.shape, bool)",
                           "    raise RuntimeError('mutación de control')", "CAÍDA"),
}


def correr(nombre, viejo, nuevo, a):
    src = ORIG.read_text(encoding="utf-8")
    if viejo is not None:
        assert src.count(viejo) == 1, (nombre, src.count(viejo))
        src = src.replace(viejo, nuevo)
    copia = RAIZ / "pipeline" / f"_mut_{nombre}.py"
    copia.write_text(src, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(AQUI / "equivalencia_v750a.py"), "--insumos", a.insumos, "--grillas",
                            a.grillas, "--recortes", a.recortes, "--modulo", f"pipeline._mut_{nombre}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        # el oro de MATLAB (fondo celda por celda, con su patrón de NaN) corre también contra la copia: hay roturas
        # que ningún VRP de la equivalencia ve, como rellenar fuera de la envolvente (no hay alertados ahí)
        o = subprocess.run([sys.executable, str(AQUI / "oro_fillmissing2_o2.py"), "--o2", a.o2,
                            "--modulo", f"pipeline._mut_{nombre}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace") if a.o2 else None
    finally:
        copia.unlink()
    out = r.stdout + r.stderr
    oro = (o.stdout + o.stderr) if o is not None else ""
    if "Traceback" in out or "Traceback" in oro:
        estado = "CAÍDA"
    elif (r.returncode == 1 and "ROJA:" in out) or (o is not None and o.returncode == 1 and "== oro: ROJO" in oro):
        estado = "ATRAPADA"
    elif r.returncode == 0 and "VERDE:" in out and (o is None or (o.returncode == 0 and "== oro: VERDE" in oro)):
        estado = "VERDE"
    else:
        estado = f"OTRA (salida {r.returncode}/{o.returncode if o is not None else '-'})"
    linea = next((x for x in out.splitlines() if x.startswith(("VERDE", "ROJA"))), out.strip().splitlines()[-1:])
    if o is not None:
        linea = f"{linea} | oro {next((x for x in oro.splitlines() if x.startswith('== oro')), '?')}"
    return nombre, estado, linea


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True)
    ap.add_argument("--grillas", required=True)
    ap.add_argument("--recortes", required=True)
    ap.add_argument("--hilos", type=int, default=7)
    ap.add_argument("--o2", default="", help="carpeta con entradas_o2.mat y resultado_o2.mat: corre también el oro")
    a = ap.parse_args()
    with ThreadPoolExecutor(a.hilos) as ex:
        res = list(ex.map(lambda kv: correr(kv[0], kv[1][0], kv[1][1], a), MUT.items()))
    malas = 0
    for nombre, estado, linea in res:
        esp = MUT[nombre][2]
        malas += estado != esp
        print(f"{nombre:20s} {estado:9s} (se espera {esp}) | {str(linea)[:150]}")
    print("mutaciones del módulo:", "TODAS COMO SE ESPERA" if not malas else f"{malas} NO COMO SE ESPERA")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
