# -*- coding: utf-8 -*-
"""s03 (S173, cenit V750): brazos NATIVOS del runner N (K, K2, C, F, FC) y dos brazos de grilla propios, por cenit.

POR QUÉ. La grilla de s01/s02 no puede separar el remuestreo (D17) de lo que K hace después (selección del cúmulo,
fondo, recorte), porque todos sus brazos están en la grilla. El runner de N (S159) guardó, sobre el MISMO gránulo
nativo y sin remuestreo, el brazo F: K con el fondo y la suma del código de MIROVA (halo + fillmissing2, sin recorte,
sin modo de un píxel). Si F nativo es plano con el cenit, la caída de K la pone el fondo/recorte (D25 del catálogo) y
no el remuestreo; si F cae como K, la pone algo que la grilla corrige y el gránulo nativo no (remuestreo o geometría
del píxel, D17). Los brazos de grilla propios aíslan, dentro de la grilla, fondo de anillo CON recorte (como K) y
"todo K salvo el fondo".

Razón «con ceros»: denominador fijo = las 28 pasadas con alerta de MIROVA (s02); un brazo que no publica o da VRP <= 0
cuenta 0. Evita el sesgo de superviviente (s02 descartaba los VRP negativos de O_fanillo, todos oblicuos).

P1: K2 debe ser idéntico a K (nulo del runner); K nativo debe mostrar la caída (control positivo); F_pc_central debe
    coincidir con el pc del record F cuando no hay redondeo (control de lectura).
P2: barajado del cenit 200 veces, semilla 173.
Uso: python -B s03_nativos_y_extra.py
"""
from __future__ import annotations

import csv
import io
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
import banco_paridad as B  # noqa: E402,F401

sys.path.insert(0, str(AQUI / "src" / "s162"))
sys.path.insert(0, str(AQUI))
import oraculo_ablacion as OA  # noqa: E402
import ablacion as AB  # noqa: E402
from s02_razon_por_cenit import spearman, barajado, q, med, fl  # noqa: E402

GRILLAS = Path("D:/vrp-trabajo/temporales/s159_n")
INS = AQUI / "insumos"
VOL = "NevadosDeChillan"
EXTRA = {
    "X_fanillo_rec": {"fondo": "anillo", "recorte": True},
    "X_todoK_fcodigo": {"ocho_vecinos": True, "reg_p1": True, "umbrales_k": True, "compuerta": "p1", "caja": "circ",
                        "recorte": True},
    "X_todoK_sinrec": {"ocho_vecinos": True, "reg_p1": True, "umbrales_k": True, "compuerta": "p1", "caja": "circ",
                       "fondo": "anillo"},
}
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def linea(nombre, pares):
    z = [a for a, _ in pares]
    r = [b for _, b in pares]
    lo = [b for a, b in pares if a < 30]
    hi = [b for a, b in pares if a >= 30]
    sp = spearman(z, r)
    bj = barajado(z, r)
    c = med(hi) / med(lo) if lo and hi and med(lo) else None
    fuera = sp is not None and bj[0] is not None and (sp < bj[0] or sp > bj[1])
    pr(f"{nombre:18s} z<30 {q(lo)} | z>=30 {q(hi)} | med>=30/med<30 " + (f"{c:.3f}" if c is not None else "-")
       + (f" | Spearman {sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
          if sp is not None else ""))


def main():
    P = list(csv.DictReader(open(AQUI / "s02_por_pasada.csv", encoding="utf-8")))
    pos = [x for x in P if fl(x["vM"]) and fl(x["vM"]) > 0]
    res, obj = AB.cargar(INS)
    inn = B.inner_desde_html()[VOL]
    pr("== denominador: pasadas con alerta MIROVA pareada (s02):", len(pos),
       "| ventana", min(x["hora_utc"] for x in pos), "a", max(x["hora_utc"] for x in pos))

    # brazos de grilla propios
    for x in pos:
        i = int(x["id"])
        r = res[i]
        z = np.load(AB.buscar_grilla(GRILLAS, i))
        for b, cambio in EXTRA.items():
            Pz = dict(OA.PIEZAS_MIROVA)
            Pz.update(cambio)
            mask = OA.detectar(z["m13"], z["m15"], r["dayflag"], r["sunglint"], Pz, inner_km=inn)
            v = OA.vrp(z["m13"], mask, Pz, inner_km=inn)
            rr, cc = np.nonzero(mask)
            pix = [(int(a), int(c), float(z["m13"][a, c])) for a, c in zip(rr, cc)]
            x[f"{b}_vrp"] = v["VRP_MW"] if v["npix"] else None
            x[f"{b}_pub"] = str(AB.publica(v["npix"], v["VRP_MW"], pix, inn))
        br = r["brazos"]
        for b in ("K", "K2", "C", "F", "FC"):
            rec = (br.get(b) or {}).get("record") or {}
            pc = rec.get("primary_cluster") or {}
            x[f"N{b}_pc"] = pc.get("vrp_mw")
            x[f"N{b}_scene"] = rec.get("vrp_mw")
            x[f"N{b}_dc"] = rec.get("distance_class")
        x["NF_pc_central"] = (br.get("F") or {}).get("F_pc_central")
        x["NF_escena_central"] = (br.get("F") or {}).get("F_escena_central")
        x["NF_k"] = (br.get("F") or {}).get("F_k")
        x["NF_nhot"] = (br.get("F") or {}).get("n_hot")
        x["NK_nhot"] = (br.get("K") or {}).get("n_hot")

    pr("\n== CONTROLES")
    d = sum(1 for x in pos if x["NK_pc"] != x["NK2_pc"] or x["NK_scene"] != x["NK2_scene"])
    pr("K2 distinto de K (pc o escena):", d, "de", len(pos))
    dk = sum(1 for x in pos if fl(x["k_pc_vrp"]) != x["NK_pc"])
    pr("K del runner (s01) distinto de N K pc:", dk)
    dmain = [(fl(x["k_main_disp"]), x["NK_pc"]) for x in pos]
    dm = sum(1 for a, b in dmain if (a or 0) > 0 and b is not None and abs(a - b) > 0.006)
    pr("K main (tablero) distinto de K del runner pc (|dif| > 0,006 MW) entre los que publican:", dm)
    cf = [(x["NF_pc"], x["NF_pc_central"]) for x in pos if x["NF_pc"] is not None and x["NF_pc_central"] is not None]
    pr("F record pc vs F_pc_central: n", len(cf), "| |dif| máx",
       round(max(abs(a - b) for a, b in cf), 4) if cf else None)
    pr("F record distance_class:", {k: sum(1 for x in pos if x["NF_dc"] == k) for k in {x["NF_dc"] for x in pos}})

    def cc(x, b, campo="vrp", pub=None):
        """razón con ceros: brazo VRP / MIROVA, 0 si no hay o es <= 0."""
        v = fl(x.get(f"{b}_{campo}")) if campo else None
        if pub is not None and x.get(pub) not in ("True", "1", 1, True):
            v = None
        return max(v, 0.0) / fl(x["vM"]) if v else 0.0

    pr("\n== RAZÓN CON CEROS (n = 28 fijo; 0 si el brazo no da VRP > 0)")
    filas = [("K main tablero", lambda x: (fl(x["k_main_disp"]) or 0) / fl(x["vM"]) if x["k_main_pub"] == "1" else 0.0),
             ("N K pc", lambda x: max(x["NK_pc"] or 0, 0) / fl(x["vM"])),
             ("N K escena", lambda x: max(x["NK_scene"] or 0, 0) / fl(x["vM"])),
             ("N C pc", lambda x: max(x["NC_pc"] or 0, 0) / fl(x["vM"])),
             ("N F pc", lambda x: max(x["NF_pc"] or 0, 0) / fl(x["vM"])),
             ("N F escena centr", lambda x: max(x["NF_escena_central"] or 0, 0) / fl(x["vM"])),
             ("N FC pc", lambda x: max(x["NFC_pc"] or 0, 0) / fl(x["vM"]))]
    for b in ["O", "O_comp", "O_fanillo", "O_sinhalo", "O_rec", "O_todoK", "O_todoK_sincomp", "geo_nearest",
              "geo_cubic", "r2_linear", "r2_nearest"] + list(EXTRA):
        filas.append((b, lambda x, b=b: cc(x, b)))
    for nombre, fn in filas:
        linea(nombre, [(fl(x["z"]), fn(x)) for x in pos])

    pr("\n== RAZÓN SIN CEROS (sólo pasadas con VRP > 0 del brazo), brazos nativos y propios")
    for nombre, campo in (("N K pc", "NK_pc"), ("N F pc", "NF_pc"), ("N F escena centr", "NF_escena_central"),
                          ("N FC pc", "NFC_pc"), ("N C pc", "NC_pc")):
        linea(nombre, [(fl(x["z"]), x[campo] / fl(x["vM"])) for x in pos if (x[campo] or 0) > 0])
    for b in EXTRA:
        linea(b, [(fl(x["z"]), fl(x[f"{b}_vrp"]) / fl(x["vM"])) for x in pos if (fl(x[f"{b}_vrp"]) or 0) > 0])

    pr("\n== CONTEO: celdas alertadas en la grilla (O) contra píxeles alertados nativos (n_hot de N), por cenit")
    for nombre, fn in (("n_hot K nativo", lambda x: x["NK_nhot"]), ("n_hot F nativo", lambda x: x["NF_nhot"]),
                       ("npix O grilla", lambda x: fl(x["O_npix"])),
                       ("O npix / n_hot K", lambda x: fl(x["O_npix"]) / x["NK_nhot"] if x["NK_nhot"] else None)):
        linea(nombre, [(fl(x["z"]), fn(x)) for x in pos if fn(x) is not None])

    pr("\n== DETALLE (orden de cenit): razón por pasada")
    pr("hora_utc        z     NK_pc  NF_pc  NFesc  O      O_fan  Xfrec  XtKfc  O_todoK nhotK npixO")
    for x in sorted(pos, key=lambda y: fl(y["z"])):
        def g(v):
            return f"{fl(v) / fl(x['vM']):6.3f}" if fl(v) is not None else "   -  "
        pr(f"{x['hora_utc']} {fl(x['z']):5.1f} {g(x['NK_pc'])} {g(x['NF_pc'])} {g(x['NF_escena_central'])} "
           f"{g(x['O_vrp'])} {g(x['O_fanillo_vrp'])} {g(x['X_fanillo_rec_vrp'])} {g(x['X_todoK_fcodigo_vrp'])} "
           f"{g(x['O_todoK_vrp'])} {x['NK_nhot']!s:>5} {x['O_npix']:>5}")
    cols = list(pos[0].keys())
    with open(AQUI / "s03_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(pos)
    (AQUI / "s03_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
