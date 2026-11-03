# -*- coding: utf-8 -*-
"""s02 (S173 tupun375): razón por pasada de K contra MIROVA en Tupungatito VIIRS 375, por tramo de cenit, con Spearman
razón contra cenit y barajado del cenit dentro del sensor (200 barajados, semilla 173).

POR QUÉ. Si el déficit de Tupungatito (auto-audit 0,371 por noche) es el mecanismo de Chillán (el fondo de anillo de K
se come el exceso diluido de las pasadas oblicuas), la razón por pasada tiene que CAER con el cenit (pendiente). Si es
pareja en el cenit, el déficit es de NIVEL y la palanca es otra o es la parte de nivel del fondo.

Conjuntos (cada uno con su denominador y su ventana impresos):
  U    unión CONS+OCR con D-9 SN (la del auto-audit), K publicada con disp > 0 y alerta de MIROVA con VRP > 0.
  C    sólo filas de la tabla (CONS): la etiqueta que DECIDE según A119 en ventanas que pisan hitos del OCR.
  U-S  U sin las filas sólo-OCR de Suomi NPP anteriores al 2026-10-09 (referencia sospechosa, A119).
  S    esas filas sospechosas, aparte.
Ventanas: corpus pareable completo (desde 2026-02-14, primer dato de Tupungatito en la tabla), desde 2026-04-01 (tasa por
pasada VIIRS comparable, A119) y desde 2026-06-13 (OCR con distancia, A119).

P1 (si lo medido estuviera roto, ¿lo vería?): control positivo de pendiente, razón × cos(z)^2 (dependencia fabricada)
    debe dar Spearman más negativo y fuera del barajado; razón × 2 debe doblar la mediana.
P2 (instrumento muerto): el Spearman real se compara con el rango [2,5; 97,5] % de 200 barajados; con n < 8 se imprime
    SIN DATO. Además se imprime el número de pares de cada conjunto: un conjunto vacío no es «plano».
Uso: python -B s02_estratos_k.py s01_k_pasadas.csv s02_salida.json
"""
import csv, json, math, random, statistics, sys
from collections import Counter

KCSV, OUT = sys.argv[1], sys.argv[2]
SEMILLA, NB, CORTE = 173, 200, 30.0
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def f(x):
    try:
        y = float(x)
        return None if math.isnan(y) else y
    except (TypeError, ValueError):
        return None


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    if len(x) < 4:
        return None
    a, b = rank(x), rank(y)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return None if den == 0 else num / den


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def resumen(pares):
    """pares: lista de (z, razón)."""
    z = [p[0] for p in pares]
    r = [p[1] for p in pares]
    out = {"n": len(pares), "mediana": med(r)}
    for nom, cond in (("z<30", lambda q: q < CORTE), ("z>=30", lambda q: q >= CORTE), ("30<=z<50", lambda q: CORTE <= q < 50),
                      ("z>=50", lambda q: q >= 50)):
        sel = [b for a, b in zip(z, r) if cond(a)]
        out[nom] = {"n": len(sel), "mediana": med(sel)}
    if len(pares) < 8:
        out["spearman"] = "SIN DATO (n < 8)"
        return out
    s = spearman(z, r)
    rnd = random.Random(SEMILLA)
    sb = []
    for _ in range(NB):
        zz = list(z)
        rnd.shuffle(zz)  # un solo sensor (VIIRS 375): el barajado ya es dentro del sensor
        sb.append(spearman(zz, r))
    sb = sorted(x for x in sb if x is not None)
    lo, hi = sb[int(0.025 * len(sb))], sb[int(0.975 * len(sb)) - 1]
    out.update({"spearman": round(s, 3), "barajado_95": [round(lo, 3), round(hi, 3)], "fuera_del_barajado": not (lo <= s <= hi)})
    return out


def linea(nom, rs, ventana=None):
    sp = rs.get("spearman")
    sps = sp if isinstance(sp, str) else f"{sp:+.3f} [{rs['barajado_95'][0]:+.3f}; {rs['barajado_95'][1]:+.3f}] {'FUERA' if rs['fuera_del_barajado'] else 'dentro'}"
    pr(f"  {nom:38s} n {rs['n']:4d} med {rs['mediana']}  z<30 {rs['z<30']['mediana']} ({rs['z<30']['n']})  "
       f"z>=30 {rs['z>=30']['mediana']} ({rs['z>=30']['n']})  30-50 {rs['30<=z<50']['mediana']} ({rs['30<=z<50']['n']})  "
       f"z>=50 {rs['z>=50']['mediana']} ({rs['z>=50']['n']})  Spearman {sps}" + (f"  ventana pares {ventana}" if ventana else ""))


K = [r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"]
res = {"semilla": SEMILLA, "barajados": NB, "corte_cenit": CORTE, "conjuntos": {}}


def sospechosa(r):
    return r["src_M"] == "OCR" and r["sensor"] == "VIIRS_SNPP" and r["dt"][:10] < "2026-10-09"


def pares(desde, conj):
    out, dts = [], []
    for r in K:
        if r["dt"][:10] < desde or r["pub"] != "1":
            continue
        d, z = f(r["disp"]), f(r["z"])
        if not d or d <= 0 or z is None:
            continue
        if conj == "C":
            m = f(r["vrp_M_cons"])
        else:
            m = f(r["vrp_M"])
            if conj == "U-S" and sospechosa(r):
                continue
            if conj == "S" and not sospechosa(r):
                continue
        if not m or m <= 0:
            continue
        out.append((z, d / m, r))
        dts.append(r["dt"])
    return out, ([min(dts), max(dts)] if dts else None)


pr("== Tupungatito VIIRS 375, K de producción (origin/main), razón por pasada = disp (node) / VRP de MIROVA de la MISMA pasada")
for desde in ("2026-02-14", "2026-04-01", "2026-06-13"):
    pr(f"-- desde {desde}")
    for conj in ("U", "C", "U-S", "S"):
        P, v = pares(desde, conj)
        rs = resumen([(z, q) for z, q, _ in P])
        rs["ventana_pares"] = v
        res["conjuntos"][f"{desde}|{conj}"] = rs
        linea(conj, rs, v)

# controles sobre U completo
P, v = pares("2026-02-14", "U")
c1 = resumen([(z, q * math.cos(math.radians(z)) ** 2) for z, q, _ in P])
res["control_pos_cos2"] = c1
res["control_pos_x2_mediana"] = med([2 * q for _, q, _ in P])
linea("control P1: U × cos(z)^2", c1)
pr(f"  control P1: U × 2, mediana {res['control_pos_x2_mediana']} (U {res['conjuntos']['2026-02-14|U']['mediana']})")

# por plataforma
res["por_plataforma_U"] = {}
pr("-- por plataforma (U, desde 2026-02-14)")
for p in sorted({r["sensor"] for _, _, r in P}):
    rs = resumen([(z, q) for z, q, r in P if r["sensor"] == p])
    res["por_plataforma_U"][p] = rs
    linea(p, rs)

# la razón contra la magnitud de MIROVA (¿déficit de régimen débil?) y la magnitud de MIROVA contra el cenit
pr("-- U desde 2026-02-14: razón contra VRP de MIROVA, y VRP de MIROVA contra el cenit")
vm = [f(r["vrp_M"]) for _, _, r in P]
rr = [q for _, q, _ in P]
zz = [z for z, _, _ in P]
s_rm = spearman(vm, rr)
s_mz = spearman(zz, vm)
terc = sorted(vm)
t1, t2 = terc[len(terc) // 3], terc[2 * len(terc) // 3]
res["razon_vs_vrpM"] = {"spearman": round(s_rm, 3), "cortes_tercil_MW": [t1, t2],
                        "tercil_bajo": {"n": sum(1 for x in vm if x < t1), "mediana": med([q for q, x in zip(rr, vm) if x < t1])},
                        "tercil_medio": {"n": sum(1 for x in vm if t1 <= x < t2), "mediana": med([q for q, x in zip(rr, vm) if t1 <= x < t2])},
                        "tercil_alto": {"n": sum(1 for x in vm if x >= t2), "mediana": med([q for q, x in zip(rr, vm) if x >= t2])}}
res["vrpM_vs_cenit"] = {"spearman": round(s_mz, 3), "mediana_z<30": med([x for x, z in zip(vm, zz) if z < CORTE]),
                        "mediana_z>=30": med([x for x, z in zip(vm, zz) if z >= CORTE])}
pr(f"  Spearman razón vs VRP MIROVA {s_rm:+.3f}; terciles (cortes {t1}, {t2} MW): {res['razon_vs_vrpM']}")
pr(f"  VRP MIROVA vs cenit: {res['vrpM_vs_cenit']}")

# tasas por tramo: cuántas pasadas, cuántas con alerta de MIROVA, cuántas publica K (selección por cenit)
pr("-- tasas por tramo de cenit, todas las pasadas nocturnas desde 2026-04-01 (no sólo pares)")
tasas = {}
for nom, lo, hi in (("z<30", 0, 30), ("30<=z<50", 30, 50), ("z>=50", 50, 90)):
    R = [r for r in K if r["dt"][:10] >= "2026-04-01" and f(r["z"]) is not None and lo <= f(r["z"]) < hi]
    al = [r for r in R if f(r["vrp_M"]) and f(r["vrp_M"]) > 0]
    pu = [r for r in R if r["pub"] == "1"]
    pa = [r for r in al if r["pub"] == "1" and f(r["disp"]) and f(r["disp"]) > 0]
    tasas[nom] = {"pasadas": len(R), "alerta_MIROVA": len(al), "K_publica": len(pu), "pares": len(pa),
                  "tasa_alerta": round(len(al) / len(R), 3) if R else None, "tasa_K_publica": round(len(pu) / len(R), 3) if R else None,
                  "alerta_sin_publicar_K": len(al) - len(pa)}
    pr(f"  {nom:9s} {tasas[nom]}")
res["tasas_por_tramo_desde_0401"] = tasas

# por noche como el auto-audit (control de reconciliación con 0,371): ventana del auto-audit 2026-09-03 a 2026-11-02
pr("-- reconciliación con el auto-audit (ventana 2026-09-03 a 2026-11-02, U)")
Pa, va = pares("2026-09-03", "U")
noches = {}
for z, q, r in Pa:
    noches.setdefault(r["noche"], []).append((z, q, r))
rn = [max(vv, key=lambda t: f(t[2]["vrp_M"]))[1] for vv in noches.values()]
rs = resumen([(z, q) for z, q, _ in Pa])
res["ventana_autoaudit"] = {**rs, "n_noches_par": len(rn), "mediana_por_noche_pasada_de_mayor_M": med(rn)}
linea("U 2026-09-03..", rs, va)
pr(f"  por noche (pasada de mayor VRP de MIROVA): n {len(rn)} mediana {med(rn)} (auto-audit: max/max por noche, 0,371 n 25)")

# detalle de pares (para leer a mano)
res["detalle_U"] = [{"dt": r["dt"], "sensor": r["sensor"], "z": z, "M": f(r["vrp_M"]), "src_M": r["src_M"], "K": f(r["disp"]),
                     "razon": round(q, 3), "t_bg": f(r["t_bg"]), "t_max": f(r["t_max"]), "pc_n": r["pc_n"], "n_pos": r["n_pos"],
                     "dist_M": r["dist_M"], "pc_dist": r["pc_dist"], "sospechosa": sospechosa(r)} for z, q, r in sorted(P, key=lambda t: t[0])]
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(OUT.replace(".json", ".txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
