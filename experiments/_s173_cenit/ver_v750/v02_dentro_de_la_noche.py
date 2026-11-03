# -*- coding: utf-8 -*-
"""v02 (verificador S173, cenit V750): tres caminos propios que el auditor no uso.

(a) Spearman de cada factor por separado contra el cenit: VRP de MIROVA (vM) y pc de K. Si MIROVA fuera plano y
    K cayera, la razon cae por K; si los dos cayeran igual, la razon seria plana. Tambien explica el placebo de v01.
(b) Pares DENTRO DE LA MISMA NOCHE con cenit distinto (>= 10 grados): el estado del volcan es el mismo, asi que el
    tiempo no confunde. Signo de (razon en el cenit alto - razon en el cenit bajo). Test de signos exacto.
    Se aplica a K (31 y 53 positivos propios) y a cada brazo del auditor (28 positivos, s03_por_pasada.csv).
(c) Controles del auditor que quedaron sin veredicto: F record pc contra F_pc_central (|dif| max 1,21 MW), y la
    "mitad logaritmica" de la afirmacion 5 calculada explicitamente.
Pregunta 1: el test de signos ve la caida si existe dentro de la noche (control positivo: razon*(1-z/90) tiene que
dar signo negativo en todos los pares). Pregunta 2: razon barajada entre pasadas de la misma noche (semilla 173)
tiene que dar ~50 % de signos.
"""
from __future__ import annotations

import csv
import io
import itertools
import json
import math
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

# (v01 ya envuelve sys.stdout en utf-8 al importarse; envolverlo dos veces cierra el buffer)
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import v01_pareo_propio as V  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def fl(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def binom_two_sided(k, n):
    """p exacto de signos (H0: p=0,5), dos colas."""
    if n == 0:
        return None
    pmf = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    pk = pmf[k]
    return min(1.0, sum(p for p in pmf if p <= pk + 1e-12))


def pares_noche(items, dz_min=10.0):
    """items: lista de (noche, z, razon). Devuelve lista de (noche, z_lo, z_hi, r_lo, r_hi)."""
    por = {}
    for n, z, r in items:
        por.setdefault(n, []).append((z, r))
    out = []
    for n, v in por.items():
        for (z1, r1), (z2, r2) in itertools.combinations(v, 2):
            if abs(z1 - z2) < dz_min:
                continue
            (zl, rl), (zh, rh) = sorted([(z1, r1), (z2, r2)])
            out.append((n, zl, zh, rl, rh))
    return out


def signos(nombre, items, dz_min=10.0):
    P = pares_noche(items, dz_min)
    neg = sum(1 for _, _, _, rl, rh in P if rh < rl)
    pos = sum(1 for _, _, _, rl, rh in P if rh > rl)
    emp = len(P) - neg - pos
    p = binom_two_sided(min(neg, pos), neg + pos) if neg + pos else None
    med = statistics.median([math.log10(rh / rl) for _, _, _, rl, rh in P if rl > 0 and rh > 0]) \
        if any(rl > 0 and rh > 0 for _, _, _, rl, rh in P) else None
    nn = len({x[0] for x in P})
    pr(f"{nombre:28s} pares={len(P):3d} noches={nn:2d} alto<bajo {neg:3d} | alto>bajo {pos:3d} "
       f"| empates {emp} | p signos {p if p is None else round(p, 4)} | mediana log10(alto/bajo) "
       + ("-" if med is None else f"{med:+.3f}"))
    return P


def main():
    ref = V.cargar_ref()
    d = json.load(open(V.REPO / "data" / "mirova_equivalent" / "NevadosDeChillan.json", encoding="utf-8"))
    recs = [r for r in d["records"] if (r.get("sensor") or "").endswith("_750") and (r.get("solar_zenith_deg") or 0) > 90]

    def positivos(ventana):
        out = []
        for r in recs:
            if not (ventana[0] <= r["datetime_utc"][:10] <= ventana[1]):
                continue
            vm, fm = V.vrp_mirova(V.parear([f for f in ref if ventana[0] <= f["fecha"][:10] <= ventana[1]],
                                           V.dt(r["datetime_utc"]), 120))
            if vm and vm > 0:
                pc = (r.get("primary_cluster") or {}).get("vrp_mw")
                out.append({"t": r["datetime_utc"], "z": r["sensor_zenith_deg"], "vM": vm, "pc": pc,
                            "r0": max(pc or 0, 0) / vm})
        return out

    pr("== (a) factores por separado contra el cenit")
    for ventana in (("2026-09-28", "2026-10-17"), ("2026-04-01", "2026-10-31")):
        pos = positivos(ventana)
        z = [x["z"] for x in pos]
        pr(f"ventana {ventana[0]} a {ventana[1]}: n={len(pos)}")
        for nom, v in (("VRP MIROVA (vM)", [x["vM"] for x in pos]), ("pc de K (0 si falta)", [x["r0"] * x["vM"] for x in pos]),
                       ("razon K/MIROVA", [x["r0"] for x in pos])):
            sp = V.spearman(z, v)
            bj = V.barajado(z, v)
            pr(f"  {nom:24s} Spearman vs z {sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] "
               f"{'FUERA' if sp < bj[0] or sp > bj[1] else 'dentro'}")
        # por que el placebo de v01 (vM barajado) sale FUERA en la ventana larga: pc solo ya cae con z
        pr("  medianas de vM por tramo: z<30", V.q([x["vM"] for x in pos if x["z"] < 30]),
           "| z>=30", V.q([x["vM"] for x in pos if x["z"] >= 30]))

    pr("\n== (b) pares dentro de la misma noche, cenit distinto en >= 10 grados (K, pareo propio)")
    for ventana in (("2026-09-28", "2026-10-17"), ("2026-04-01", "2026-10-31")):
        pos = positivos(ventana)
        it = [(x["t"][:10], x["z"], x["r0"]) for x in pos]
        pr(f"-- ventana {ventana[0]} a {ventana[1]} (n={len(pos)})")
        P = signos("K pc con ceros", it)
        signos("K pc con ceros, dz>=20", it, 20.0)
        signos("CONTROL+ razon*(1-z/90)", [(n, z, r * (1 - z / 90)) for n, z, r in it])
        rng = random.Random(173)
        rr = [r for _, _, r in it]
        rng.shuffle(rr)
        signos("NULO razon barajada", [(n, z, r) for (n, z, _), r in zip(it, rr)])
        # nulo mejor: barajar DENTRO de cada noche
        por = {}
        for n, z, r in it:
            por.setdefault(n, []).append(r)
        cont = Counter()
        for s in range(200):
            rg = random.Random(173 + s)
            it2 = []
            for n, z, r in it:
                pass
            bar = {n: rg.sample(v, len(v)) for n, v in por.items()}
            idx = Counter()
            for n, z, _ in it:
                it2.append((n, z, bar[n][idx[n]]))
                idx[n] += 1
            Pn = pares_noche(it2)
            cont["neg"] += sum(1 for _, _, _, rl, rh in Pn if rh < rl)
            cont["tot"] += sum(1 for _, _, _, rl, rh in Pn if rh != rl)
        pr(f"   nulo barajando dentro de cada noche (200 veces): fraccion alto<bajo = {cont['neg'] / cont['tot']:.3f}")
        if P:
            pr("   detalle (noche, z_bajo, z_alto, razon_bajo, razon_alto):")
            for n, zl, zh, rl, rh in sorted(P):
                pr(f"     {n} {zl:5.1f} {zh:5.1f} {rl:6.3f} {rh:6.3f} {'CAE' if rh < rl else 'sube'}")

    pr("\n== (b bis) lo mismo para los brazos del auditor (28 positivos de s03_por_pasada.csv, razon con ceros)")
    S3 = list(csv.DictReader(open(AQUI / "s03_por_pasada.csv", encoding="utf-8")))

    def r0(x, campo):
        v = fl(x.get(campo))
        return max(v, 0.0) / fl(x["vM"]) if v else 0.0

    brazos = [("K pc (NK_pc)", "NK_pc"), ("K escena", "NK_scene"), ("F nativo pc (NF_pc)", "NF_pc"),
              ("FC nativo pc", "NFC_pc"), ("C nativo pc", "NC_pc"), ("O grilla", "O_vrp"), ("O_fanillo", "O_fanillo_vrp"),
              ("O_sinhalo", "O_sinhalo_vrp"), ("O_rec", "O_rec_vrp"), ("O_comp", "O_comp_vrp"), ("O_comp1", "O_comp1_vrp"),
              ("O_todoK", "O_todoK_vrp"), ("O_todoK_sincomp", "O_todoK_sincomp_vrp"), ("X_fanillo_rec", "X_fanillo_rec_vrp"),
              ("X_todoK_fcodigo", "X_todoK_fcodigo_vrp"), ("X_todoK_sinrec", "X_todoK_sinrec_vrp"),
              ("geo_nearest", "geo_nearest_vrp"), ("r2_linear", "r2_linear_vrp")]
    for nom, campo in brazos:
        signos(nom, [(x["hora_utc"][:10], fl(x["z"]), r0(x, campo)) for x in S3])
    pr("-- los mismos sin ceros (pares donde los dos brazos > 0)")
    for nom, campo in brazos:
        it = [(x["hora_utc"][:10], fl(x["z"]), r0(x, campo)) for x in S3 if r0(x, campo) > 0]
        signos(nom + " >0", it)

    pr("\n== (c) controles del auditor sin veredicto")
    pr("F record pc vs F_pc_central por pasada (|dif| > 0,01 MW):")
    for x in S3:
        a, b = fl(x["NF_pc"]), fl(x["NF_pc_central"])
        if a is not None and b is not None and abs(a - b) > 0.01:
            pr(f"  {x['hora_utc']} z {fl(x['z']):5.1f} NF_pc {a:.3f} F_pc_central {b:.3f} NF_escena_central "
               f"{fl(x['NF_escena_central'])} NK_pc {fl(x['NK_pc'])} vM {x['vM']} NF_nhot {x['NF_nhot']} NF_k {x['NF_k']}")
    medk = {t: statistics.median([r0(x, "NK_pc") for x in S3 if (fl(x["z"]) < 30) == (t == "lo")]) for t in ("lo", "hi")}
    medf = {t: statistics.median([r0(x, "NF_pc") for x in S3 if (fl(x["z"]) < 30) == (t == "lo")]) for t in ("lo", "hi")}
    lk, lf = math.log10(medk["hi"] / medk["lo"]), math.log10(medf["hi"] / medf["lo"])
    pr(f"caida de K: med>=30/med<30 = {medk['hi'] / medk['lo']:.3f} (log10 {lk:+.3f}); F: {medf['hi'] / medf['lo']:.3f} "
       f"(log10 {lf:+.3f}); fraccion de la caida logaritmica que F conserva: {lf / lk:.3f}; Spearman F/K: "
       f"{-0.662 / -0.864:.3f}")
    pr("O_fanillo: valores <= 0 entre los 28 (cenit):",
       sorted(round(fl(x["z"]), 1) for x in S3 if (fl(x["O_fanillo_vrp"]) or 0) <= 0),
       "| X_fanillo_rec = 0 o None:", sorted(round(fl(x["z"]), 1) for x in S3 if not (fl(x["X_fanillo_rec_vrp"]) or 0) > 0),
       "| O_todoK:", sorted(round(fl(x["z"]), 1) for x in S3 if not (fl(x["O_todoK_vrp"]) or 0) > 0))
    (AQUI / "v02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
