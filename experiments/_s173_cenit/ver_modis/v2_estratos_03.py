# -*- coding: utf-8 -*-
"""v2 (verificador S173, MODIS): la confusion cenit-volcan en las protegidas del lote S162 (03_salida.json).

POR QUE: en el lote, las 3 protegidas de Chillan estan todas sobre 50 grados y las 8 de Lascar entre 2 y 41. Un
Spearman sobre las 11 juntas puede medir "Chillan contra Lascar" y no el cenit. Aqui se mide DENTRO de cada volcan
(solo Lascar tiene rango de cenit) y con barajado del cenit dentro del volcan (200, semilla 173).
Pregunta 1: control positivo, una razon construida como cos(z) sobre los mismos cenit de Lascar da Spearman -1.
Pregunta 2: el barajado dentro del volcan da el rango del azar con n 8; un rho dentro del rango no es dependencia.
Uso: python -B v2_estratos_03.py <03_salida.json> <salida.txt>
"""
import json
import math
import random
import statistics
import sys
from pathlib import Path

exec(open(Path(__file__).resolve().parent / "rerun" / "_estadistica.py", encoding="utf-8").read())
d = json.load(open(sys.argv[1], encoding="utf-8"))["pasadas"]
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


prot = [e for e in d.values() if e["protegida"]]
pr(f"protegidas del lote: {len(prot)}; por volcan: " + ", ".join(f"{v}: {sum(e['volcan'] == v for e in prot)}" for v in sorted({e['volcan'] for e in prot})))
pr("cenit por volcan: " + "; ".join(f"{v} [{', '.join(f'{e['z']:.1f}' for e in sorted(prot, key=lambda e: e['z']) if e['volcan'] == v)}]" for v in sorted({e['volcan'] for e in prot})))
pr(f"ventana de observacion de las protegidas: {min(e['hora'] for e in prot)} a {max(e['hora'] for e in prot)}")
zl = [e["z"] for e in prot if e["volcan"] == "Lascar"]
pr(f"control positivo (cos z sobre Lascar, n {len(zl)}): Spearman {spearman([math.cos(math.radians(z)) for z in zl], zl):+.3f}")


def razon(e, b):
    v = (e["K_pc_vrp"] or 0) if b == "K" else (e["brazos"][b]["vrp_mw"] or 0)
    return v / e["mirova"]


brazos = ("K", "V0", "FA", "FSH", "RN", "G5", "NAT", "NAT_AREA")
pr("\n== solo Lascar (n 8): Spearman razon vs cenit, barajado dentro de Lascar; tramos z<30 / z>=30")
for b in brazos:
    las = [e for e in prot if e["volcan"] == "Lascar"]
    rr = [razon(e, b) for e in las]
    zz = [e["z"] for e in las]
    rho, lo, hi = con_barajado(zz, rr)
    a = [r for r, z in zip(rr, zz) if z < 30]
    c = [r for r, z in zip(rr, zz) if z >= 30]
    fuera = "FUERA del rango barajado" if (rho < lo or rho > hi) else "dentro del rango barajado"
    pr(f"   {b:8s} Spearman {rho:+.3f} [{lo:+.3f}; {hi:+.3f}] {fuera}; z<30 n {len(a)} mediana {med(a)}; z>=30 n {len(c)} mediana {med(c)}")

pr("\n== las 11 juntas, barajado del cenit DENTRO de cada volcan (placebo estratificado):")
rng = random.Random(173)
for b in brazos:
    rr = [razon(e, b) for e in prot]
    zz = [e["z"] for e in prot]
    rho = spearman(rr, zz)
    bs = []
    for _ in range(200):
        z2 = zz[:]
        for v in {e["volcan"] for e in prot}:
            idx = [i for i, e in enumerate(prot) if e["volcan"] == v]
            vals = [zz[i] for i in idx]
            rng.shuffle(vals)
            for i, x in zip(idx, vals):
                z2[i] = x
        s = spearman(rr, z2)
        if s is not None:
            bs.append(s)
    bs.sort()
    lo, hi = bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]
    fuera = "FUERA" if (rho < lo or rho > hi) else "dentro"
    pr(f"   {b:8s} Spearman {rho:+.3f}; rango del barajado dentro del volcan [{lo:+.3f}; {hi:+.3f}] -> {fuera}")

pr("\n== Chillan solo (n 3, todas sobre 50): razon por brazo")
for e in sorted([e for e in prot if e["volcan"] == "NevadosDeChillan"], key=lambda e: e["z"]):
    pr(f"   {e['hora']} z {e['z']:.1f} M {e['mirova']}: " + " ".join(f"{b} {razon(e, b):.2f}" for b in brazos))

pr("\n== NAT/V0 por pasada protegida (ordenado por cenit): el efecto de QUITAR el remuestreo, independiente de MIROVA")
for e in sorted(prot, key=lambda e: e["z"]):
    v0 = e["brazos"]["V0"]["vrp_mw"] or 0
    nat = e["brazos"]["NAT"]["vrp_mw"] or 0
    pr(f"   {e['volcan']:18s} {e['hora']} z {e['z']:5.1f} V0 {v0:6.3f} NAT {nat:6.3f} NAT/V0 {nat / v0 if v0 else float('nan'):5.2f} npixV0 {e['brazos']['V0']['npix']} npixNAT {e['brazos']['NAT']['npix']}")
rr = [((e["brazos"]["NAT"]["vrp_mw"] or 0) / (e["brazos"]["V0"]["vrp_mw"] or float("nan"))) for e in prot]
zz = [e["z"] for e in prot]
rho, lo, hi = con_barajado(zz, rr)
pr(f"   Spearman NAT/V0 vs cenit, las 11: {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]")
las = [e for e in prot if e["volcan"] == "Lascar"]
rr = [((e["brazos"]["NAT"]["vrp_mw"] or 0) / (e["brazos"]["V0"]["vrp_mw"] or float("nan"))) for e in las]
zz = [e["z"] for e in las]
rho, lo, hi = con_barajado(zz, rr)
pr(f"   Spearman NAT/V0 vs cenit, solo Lascar: {rho:+.3f} [{lo:+.3f}; {hi:+.3f}]")
Path(sys.argv[2]).write_text("\n".join(L) + "\n", encoding="utf-8")
