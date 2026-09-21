# -*- coding: utf-8 -*-
"""V3: nulos por barajado, corte de magnitud equivalente, incertidumbre de la razon borde/nadir,
estratos por volcan y cambio de zona entre brazos.

Uso: python v3_nulos.py <dir_salidas_run> <dir_congelado> <fin>
"""
import sys
import random
import collections
from verif_base import B, F, cargar_brazo, cargar_ref, etiquetar, zona

D, CONG, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
rb, _ = cargar_brazo(D + "/" + B)
rf, _ = cargar_brazo(D + "/" + F)
lab, _ = etiquetar(rb, cargar_ref(CONG), "2026-09-01", FIN)
S = "VIIRS375"
ks = [k for k in lab if k[1] == S and k in rf and lab[k] in ("neg", "pos")
      and rb[k].get("sensor_zenith_deg") is not None and rb[k].get("t_bg_k") is not None]
neg = [k for k in ks if lab[k] == "neg"]
pos = [k for k in ks if lab[k] == "pos"]
Z = {k: zona(rb[k]["sensor_zenith_deg"]) for k in ks}
nz = collections.Counter(Z[k] for k in neg)
print("negativas por zona", dict(nz), "| positivas", len(pos))


def razon(sobreviven):
    b = sum(1 for k in sobreviven if lab[k] == "neg" and Z[k] == "borde") / nz["borde"]
    n = sum(1 for k in sobreviven if lab[k] == "neg" and Z[k] == "nadir") / nz["nadir"]
    return b / n if n else float("inf")


pubB = [k for k in ks if rb[k]["_pub"]]
pubF = [k for k in ks if rf[k]["_pub"]]
print("publica B:", len(pubB), "(neg %d, pos %d) | publica F: %d (neg %d, pos %d)" % (
    sum(lab[k] == "neg" for k in pubB), sum(lab[k] == "pos" for k in pubB), len(pubF),
    sum(lab[k] == "neg" for k in pubF), sum(lab[k] == "pos" for k in pubF)))
obs_r = razon(pubF)
obs_pos = sum(lab[k] == "pos" for k in pubF)
print("observado: razon borde/nadir F = %.3f, positivas que sobreviven = %d" % (obs_r, obs_pos))

rnd = random.Random(148)
N = 20000
print("\n## NULO 1: endurecimiento parejo. De las %d publicadas por B se conservan %d al azar, sin mirar etiqueta" % (len(pubB), len(pubF)))
pos_n, neg_n, r_n = [], [], []
for _ in range(N):
    s = rnd.sample(pubB, len(pubF))
    pos_n.append(sum(lab[k] == "pos" for k in s))
    neg_n.append(len(s) - pos_n[-1])
    r_n.append(razon(s))
pos_n.sort(); neg_n.sort()
print("   positivas conservadas bajo el nulo: p2.5 %d, mediana %d, p97.5 %d, max %d | observado %d | P(nulo >= obs) = %.5f" %
      (pos_n[int(.025 * N)], pos_n[N // 2], pos_n[int(.975 * N)], pos_n[-1], obs_pos, sum(x >= obs_pos for x in pos_n) / N))
print("   negativas conservadas bajo el nulo: p2.5 %d, mediana %d, p97.5 %d, min %d | observado %d" %
      (neg_n[int(.025 * N)], neg_n[N // 2], neg_n[int(.975 * N)], neg_n[0], sum(lab[k] == "neg" for k in pubF)))

print("\n## NULO 2: solo dentro de las negativas. De las 95 publicadas por B se conservan 10 al azar: razon borde/nadir")
negB = [k for k in pubB if lab[k] == "neg"]
nF = sum(lab[k] == "neg" for k in pubF)
r2 = []
for _ in range(N):
    r2.append(razon(rnd.sample(negB, nF)))
r2s = sorted(r2)
print("   razon bajo el nulo: p2.5 %.2f, mediana %.2f, p97.5 %.2f | observado %.3f | P(nulo <= obs) = %.5f | P(nulo <= 1.3) = %.4f" %
      (r2s[int(.025 * N)], r2s[N // 2], r2s[int(.975 * N)], obs_r, sum(x <= obs_r for x in r2) / N, sum(x <= 1.3 for x in r2) / N))
bf = [k for k in negB if Z[k] == "borde" and rb[k]["t_bg_k"] < 260]
c = []
for _ in range(N):
    s = set(rnd.sample(negB, nF))
    c.append(sum(1 for k in bf if k in s))
obs_bf = sum(1 for k in bf if rf[k]["_pub"])
print("   borde con fondo frio conservadas bajo el nulo: mediana %d, p2.5 %d | observado %d | P(nulo <= obs) = %.4f" %
      (sorted(c)[N // 2], sorted(c)[int(.025 * N)], obs_bf, sum(x <= obs_bf for x in c) / N))

print("\n## NULO 3: etiquetas de zona barajadas entre las 324 negativas (la zona no importa): razon F")
zl = [Z[k] for k in neg]
fpub = [rf[k]["_pub"] for k in neg]
r3 = []
for _ in range(N):
    rnd.shuffle(zl)
    b = sum(p for p, z in zip(fpub, zl) if z == "borde") / nz["borde"]
    n = sum(p for p, z in zip(fpub, zl) if z == "nadir") / nz["nadir"]
    r3.append(b / n if n else float("inf"))
print("   P(razon <= %.3f) con la zona barajada = %.4f (mediana del nulo %.2f)" % (obs_r, sum(x <= obs_r for x in r3) / N, sorted(r3)[N // 2]))

print("\n## INCERTIDUMBRE de la razon F (2 de 153 contra 6 de 116): bootstrap por pasada")
bs = []
for _ in range(N):
    s = [rnd.choice(neg) for _ in neg]
    nb = sum(Z[k] == "borde" for k in s); nn = sum(Z[k] == "nadir" for k in s)
    pb = sum(rf[k]["_pub"] for k in s if Z[k] == "borde"); pn = sum(rf[k]["_pub"] for k in s if Z[k] == "nadir")
    bs.append((pb / nb) / (pn / nn) if pn else float("inf"))
bs.sort()
print("   IC 95 %% bootstrap: %.2f a %.2f | fraccion de remuestras con razon <= 1.3: %.3f" % (bs[int(.025 * N)], bs[int(.975 * N)], sum(x <= 1.3 for x in bs) / N))

print("\n## CORTE DE MAGNITUD EQUIVALENTE: si en vez de `max` se pusiera un piso de MW sobre lo que B publica")
vals = sorted(set(rb[k]["_disp"] for k in pubB))
print("   piso_MW  neg_pub  pos_pub  razon_b/n")
for piso in (0.0, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1):
    s = [k for k in pubB if rb[k]["_disp"] >= piso]
    print("   %.3f   %4d     %4d     %.2f" % (piso, sum(lab[k] == "neg" for k in s), sum(lab[k] == "pos" for k in s), razon(s)))
# mejor corte que conserva >=124 positivas
mejor = None
for v in vals:
    s = [k for k in pubB if rb[k]["_disp"] >= v]
    if sum(lab[k] == "pos" for k in s) >= obs_pos:
        mejor = (v, sum(lab[k] == "neg" for k in s), sum(lab[k] == "pos" for k in s))
print("   piso mas alto que conserva >= %d positivas: %s (piso, neg, pos)" % (obs_pos, mejor))
print("   magnitud B de las 85 negativas apagadas: mediana %.4f | de las 10 que sobreviven: mediana %.4f | de las 124 pos: mediana %.4f" % (
    sorted(rb[k]["_disp"] for k in negB if not rf[k]["_pub"])[42], sorted(rb[k]["_disp"] for k in negB if rf[k]["_pub"])[5],
    sorted(rb[k]["_disp"] for k in pubF if lab[k] == "pos")[62]))
cerca = lambda k: (rb[k]["primary_cluster"] or {}).get("centroid_dist_km")
print("   distancia al crater (B) de las 85 apagadas: mediana %.2f km | de las 10 que sobreviven: %.2f | de las pos: %.2f" % (
    sorted(cerca(k) for k in negB if not rf[k]["_pub"])[42], sorted(cerca(k) for k in negB if rf[k]["_pub"])[5],
    sorted(cerca(k) for k in pubF if lab[k] == "pos")[62]))

print("\n## POR VOLCAN (V375): negativas pub B -> F por zona, y positivas")
for v in sorted(set(k[0] for k in ks)):
    fila = []
    for z in ("nadir", "medio", "borde"):
        s = [k for k in neg if k[0] == v and Z[k] == z]
        fila.append("%s %d>%d/%d" % (z, sum(rb[k]["_pub"] for k in s), sum(rf[k]["_pub"] for k in s), len(s)))
    p = [k for k in pos if k[0] == v]
    print("   %-20s %s | pos %d>%d/%d" % (v, "  ".join(fila), sum(rb[k]["_pub"] for k in p), sum(rf[k]["_pub"] for k in p), len(p)))

print("\n## ZONA: el cenit del record cambia entre brazos? (el instrumento clasifica cada brazo con SU cenit)")
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    kk = [k for k in lab if k[1] == s and k in rf and rb[k].get("sensor_zenith_deg") is not None and rf[k].get("sensor_zenith_deg") is not None]
    d = [abs(rb[k]["sensor_zenith_deg"] - rf[k]["sensor_zenith_deg"]) for k in kk]
    flips = [k for k in kk if zona(rb[k]["sensor_zenith_deg"]) != zona(rf[k]["sensor_zenith_deg"])]
    print("   %s n=%d | cenit distinto en %d | dif max %.2f grados | cambian de zona %d (de ellas neg: %d)" %
          (s, len(kk), sum(x > 0 for x in d), max(d), len(flips), sum(lab[k] == "neg" for k in flips)))
