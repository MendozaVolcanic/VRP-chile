# -*- coding: utf-8 -*-
"""Identidad del cumulo K vs X con una magnitud que NO depende de la geolocalizacion: la radiancia MIR total del
cumulo, reconstruida como  SUM(L_i) = pc_vrp / 18,9 + n * L_bg(t_bg)  (VRP = 18,9 * A_nadir * SUM(L_i - L_bg), A66).
Si K y X agrupan los mismos pixeles, SUM(L_i) es igual en los dos brazos aunque el fondo (t_bg) cambie.

P1 (¿veria un cambio de pixel?): control positivo con los brazos R cuyo cumulo cambia de numero de pixeles.
P2 (¿el instrumento esta vivo?): control con el grupo de pixel conocido por indice (grupo 1): si la formula o la
lambda fueran las equivocadas, la diferencia no daria ~0 ahi. Se prueban las dos lambdas MIR (3,929 y 3,959 um).
Denominador: las 48 protegidas con cumulo en K y X (ventana del A/B 2026-03-01 a 2026-10-16) y, para el nulo,
todos los pares (K, brazo) de los 5.465 records con cumulo en ambos.
Uso: python -I verif_identidad_radiancia.py
"""
import collections
import csv
import glob
import io
import json
import math
import statistics
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas")
EXP = Path(r"C:\vrp-trabajo\s162-a61\experiments\_s162_mxd03")
C1, C2 = 1.191042e8, 1.4387752e4  # W um^4 m^-2 sr^-1, um K (forma de pipeline/process_modis.py::bt_to_radiance)


def planck(t, lam):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t)) - 1))


def suma_l(br, lam):
    return br["pc_vrp"] / 18.9 + br["pc_n_pixels"] * planck(br["t_bg_k"], lam)


def main():
    import re
    src = open(r"C:\vrp-trabajo\s162-a61\pipeline\process_modis.py", encoding="utf-8").read()
    m1 = re.search(r"^C1\s*=\s*([0-9.eE+-]+)", src, re.M)
    m2 = re.search(r"^C2\s*=\s*([0-9.eE+-]+)", src, re.M)
    print("constantes del pipeline: C1 %s C2 %s (uso %g %g)" % (m1 and m1.group(1), m2 and m2.group(1), C1, C2))
    recs = []
    for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            if r.get("tipo") == "record" and r.get("estado") == "ok":
                recs.append(r)
    tab = {(f["vol"], f["dt"]): f for f in csv.DictReader(open(EXP / "a61" / "a61_protegidas.csv", encoding="utf-8"))}

    def grupo(f):
        if f["K_npx"] == "1" and f["X_npx"] == "1" and f["pico_es_pcK"] == "True" and f["pico_es_pcX"] == "True":
            return 1
        if f["K_npx"] == f["X_npx"] and float(f["residuo_km"]) < 0.3:
            return 2
        return 3

    ok = lambda b: b and b.get("pc_vrp") is not None and b.get("pc_n_pixels") and b.get("t_bg_k") is not None
    for lam in (3.929, 3.959):
        print("\n== lambda %.3f um" % lam)
        por = collections.defaultdict(list)
        for r in recs:
            if r["lab"] != "protegida" or r["pub"]["K"] != 1:
                continue
            K, X = r["brazos"]["K"], r["brazos"]["X"]
            if not (ok(K) and ok(X)):
                continue
            g = grupo(tab[(r["vol"], r["dt"])])
            rel = (suma_l(X, lam) - suma_l(K, lam)) / suma_l(K, lam)
            por[g].append((rel, r["vol"], r["dt"], K["pc_n_pixels"], X["pc_n_pixels"]))
        for g in (1, 2, 3):
            v = [abs(x[0]) for x in por[g]]
            print("   grupo %d (n %d): |dSUM(L)|/SUM(L) mediana %.2e max %.2e | > 1e-3: %d" % (g, len(v), statistics.median(v), max(v), sum(1 for x in v if x > 1e-3)))
            if g >= 2:
                for x in sorted(por[g], key=lambda x: -abs(x[0])):
                    print("      %+.2e %s %s npx %s/%s" % x)
        # nulo / control positivo sobre todos los pares K-brazo
        mismo, distinto = [], []
        for r in recs:
            K = r["brazos"]["K"]
            if not ok(K):
                continue
            for b, br in r["brazos"].items():
                if b in ("K", "K2") or not ok(br):
                    continue
                rel = abs(suma_l(br, lam) - suma_l(K, lam)) / suma_l(K, lam)
                (mismo if br["pc_n_pixels"] == K["pc_n_pixels"] else distinto).append(rel)
        print("   CONTROL POSITIVO (brazos con npx distinto a K, n %d): mediana %.2e, < 1e-3 en %d" % (
            len(distinto), statistics.median(distinto) if distinto else float("nan"), sum(1 for x in distinto if x < 1e-3)))
        print("   brazos con npx igual a K (n %d): < 1e-3 en %d (%.1f %%), > 1e-2 en %d" % (
            len(mismo), sum(1 for x in mismo if x < 1e-3), 100.0 * sum(1 for x in mismo if x < 1e-3) / len(mismo), sum(1 for x in mismo if x > 1e-2)))


if __name__ == "__main__":
    main()
