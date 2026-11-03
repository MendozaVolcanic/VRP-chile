# -*- coding: utf-8 -*-
"""v03 (verificador S173, cenit V750): (1) el placebo "+1 dia" del auditor sobre sus 47 pasadas, con mi pareo;
(2) cuanto crecimiento de area haria falta (f_req, como experiments/_s131_remuestreo/factor_requerido.py) para
aplanar K y F nativo, comparado con el disponible del ATBD (4,39x al borde) y con dos leyes crudas:
la del repo (`viirs_pixel_areas`, lineal con tope 2,0) y sec(z); (3) el multiplicador realizado en la grilla
(celdas O alertadas / pixeles nativos alertados de K) aplicado a F.
Es una comprobacion de CONDICION NECESARIA para la SOSPECHA del auditor (resto = area/remuestreo), no una prueba.
"""
from __future__ import annotations

import csv
import math
import statistics
import sys
from datetime import timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / "repo"))
import v01_pareo_propio as V  # noqa: E402
from v02_dentro_de_la_noche import signos, fl  # noqa: E402
from pipeline.scan_geometry import viirs_pixel_areas  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def main():
    S1 = list(csv.DictReader(open(AQUI / "s01_por_pasada.csv", encoding="utf-8")))
    ref = [f for f in V.cargar_ref() if "2026-04-01" <= f["fecha"][:10] <= "2026-10-31"]
    pr("== (1) placebo +1 dia sobre las 47 pasadas del auditor, con mi pareo (+-120 s)")
    n1 = n0 = 0
    det = []
    for x in S1:
        t = V.dt(x["hora_utc"])
        v0 = V.vrp_mirova(V.parear(ref, t, 120))[0]
        v1 = V.vrp_mirova(V.parear(ref, t, 120, timedelta(days=1)))[0]
        n0 += bool(v0)
        n1 += bool(v1)
        if v1:
            det.append((x["hora_utc"], v1))
    pr("pares hoy:", n0, "| pares con +1 dia:", n1, "de", len(S1), det[:10])
    pr("(los 82 records de la ventana corta daban 9 con +1 dia en v01: la diferencia es el subconjunto, no el pareo)")

    S3 = list(csv.DictReader(open(AQUI / "s03_por_pasada.csv", encoding="utf-8")))
    z = [fl(x["z"]) for x in S3]
    rk = [max(fl(x["NK_pc"]) or 0, 0) / fl(x["vM"]) for x in S3]
    rf = [max(fl(x["NF_pc"]) or 0, 0) / fl(x["vM"]) for x in S3]
    base_k = statistics.median([r for a, r in zip(z, rk) if a < 30])
    base_f = statistics.median([r for a, r in zip(z, rf) if a < 30])
    pr("\n== (2) f requerido = mediana(z<30) / mediana(bin), K y F nativo (28 positivos del auditor)")
    pr("bin        n  z_med   K ratio  f_req_K   F ratio  f_req_F   | S131 I-band f_req (mismo bin)")
    s131 = {"15-25": 1.27, "25-35": 1.59, "35-50": 1.90, "50+": 2.93}
    for nom, lo, hi in (("0-15", 0, 15), ("15-25", 15, 25), ("25-35", 25, 35), ("35-50", 35, 50), ("50+", 50, 91)):
        sel = [i for i, a in enumerate(z) if lo <= a < hi]
        if not sel:
            continue
        mk = statistics.median([rk[i] for i in sel])
        mf = statistics.median([rf[i] for i in sel])
        pr(f"{nom:8s} {len(sel):3d} {statistics.median([z[i] for i in sel]):5.1f}   {mk:.3f}   "
           f"{base_k / mk if mk else float('inf'):5.2f}     {mf:.3f}   {base_f / mf if mf else float('inf'):5.2f}"
           f"     | {s131.get(nom, '-')}")
    pr("disponible segun ATBD (docs/s131/REMUESTREO_LEY_DE_AREA.md tabla, fila M13): 4,39x al fin del swath")

    pr("\n== (2 bis) razones corregidas por dos leyes crudas de area (solo direccion; ninguna es la del ATBD)")
    for nom, ley in (("lineal repo (viirs_pixel_areas, tope 2)", lambda a: float(viirs_pixel_areas(a, 1.0))),
                     ("sec(z)", lambda a: 1 / math.cos(math.radians(a))),
                     ("sec^2(z)", lambda a: 1 / math.cos(math.radians(a)) ** 2)):
        for et, r in (("K", rk), ("F", rf)):
            v = [b * ley(a) for a, b in zip(z, r)]
            sp = V.spearman(z, v)
            bj = V.barajado(z, v)
            lo_ = statistics.median([b for a, b in zip(z, v) if a < 30])
            hi_ = statistics.median([b for a, b in zip(z, v) if a >= 30])
            pr(f"  {et} x {nom:40s} med<30 {lo_:.3f} med>=30 {hi_:.3f} Spearman {sp:+.3f} "
               f"[{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if sp < bj[0] or sp > bj[1] else 'dentro'}")
            signos(f"    {et} x {nom[:20]} (signos)", [(x["hora_utc"][:10], a, b) for x, a, b in zip(S3, z, v)])

    pr("\n== (3) multiplicador realizado en la grilla: celdas O alertadas / pixeles nativos alertados (n_hot K)")
    it = []
    for x in S3:
        nh = fl(x["NK_nhot"])
        no = fl(x["O_npix"])
        if nh and no:
            m = no / nh
            it.append((x["hora_utc"][:10], fl(x["z"]), (max(fl(x["NF_pc"]) or 0, 0) / fl(x["vM"])) * m, m))
    pr("multiplicador mediano z<30:", statistics.median([m for _, a, _, m in it if a < 30]),
       "z>=30:", statistics.median([m for _, a, _, m in it if a >= 30]))
    sp = V.spearman([a for _, a, _, _ in it], [r for _, _, r, _ in it])
    bj = V.barajado([a for _, a, _, _ in it], [r for _, _, r, _ in it])
    pr(f"F x multiplicador: med<30 {statistics.median([r for _, a, r, _ in it if a < 30]):.3f} med>=30 "
       f"{statistics.median([r for _, a, r, _ in it if a >= 30]):.3f} Spearman {sp:+.3f} [{bj[0]:+.3f}, {bj[1]:+.3f}]")
    signos("F x multiplicador (signos)", [(n, a, r) for n, a, r, _ in it])
    (AQUI / "v03_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
