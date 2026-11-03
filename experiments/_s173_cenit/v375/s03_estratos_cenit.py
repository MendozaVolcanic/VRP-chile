# -*- coding: utf-8 -*-
"""s03 (S173): razón por pasada contra MIROVA en Chillán VIIRS 375, por tramo de cenit (< 30 y >= 30), con Spearman
razón contra cenit y barajado del cenit dentro del sensor (200 barajados, semilla 173).

POR QUÉ. Si la caída oblicua de K es de una pieza que la vía V375-E cambia, la razón de la vía contra MIROVA debería
quedar plana con el cenit y la razón V375-E / K debería CRECER con el cenit. Si la vía también cae, la pieza que la
causa es común a las dos (o está en MIROVA). Las dos razones se miden sobre las MISMAS pasadas (conjunto B), para que
la diferencia no sea de población.

Conjuntos (denominador y ventana impresos con cada uno):
  A   K de producción, todas las pasadas nocturnas publicadas con alerta de MIROVA (s01, 2026-04-01 a 2026-11-02).
  B   las pasadas de A que están en los lotes retrospectivos (s02, 2026-04-01 a 2026-10-21), con K y con la vía.
  B'  pasadas de los lotes con alerta de MIROVA y VRP de la vía > 0 aunque el tablero no la publique, y K publicada.
  ROI los brazos de V375-C guardados por el probe (misma grilla, sólo cambia la caja) sobre las pasadas de B'.
Una pasada entra a un conjunto si las dos magnitudes son > 0 (una razón con cero no es razón, va a SIN DATO).

P1: control positivo de pendiente, a la razón de A se le multiplica cos(z)^2 (dependencia fabricada): el Spearman debe
    volverse más negativo y salir del rango barajado; y ×2 a la razón debe doblar la mediana.
P2: el Spearman real se compara con el rango [2,5 %; 97,5 %] de 200 barajados del cenit dentro del sensor; con n < 8
    se imprime SIN DATO en vez de un Spearman.
Uso: python -B s03_estratos_cenit.py <s01_k_pasadas.csv> <s02_v375e_pasadas.csv> <salida.json>
"""
import csv, json, math, random, statistics, sys

KCSV, VCSV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SEMILLA, NB, CORTE = 173, 200, 30.0


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
    return round(statistics.median(xs), 3) if xs else None


def resumen(pares, nombre):
    """pares: lista de (z, razón, sensor)."""
    z = [p[0] for p in pares]
    r = [p[1] for p in pares]
    out = {"n": len(pares), "mediana": med(r),
           "z<30": {"n": sum(1 for q in z if q < CORTE), "mediana": med([b for a, b in zip(z, r) if a < CORTE])},
           "z>=30": {"n": sum(1 for q in z if q >= CORTE), "mediana": med([b for a, b in zip(z, r) if a >= CORTE])},
           "z>=50": {"n": sum(1 for q in z if q >= 50), "mediana": med([b for a, b in zip(z, r) if a >= 50])}}
    if len(pares) < 8:
        out["spearman"] = "SIN DATO (n < 8)"
        return out
    s = spearman(z, r)
    rnd = random.Random(SEMILLA)
    sb = []
    for _ in range(NB):
        zz = list(z)
        # barajado dentro del sensor (aquí un solo bucket, VIIRS375; se baraja dentro de cada plataforma no: dentro
        # del sensor, como pide la vara)
        rnd.shuffle(zz)
        sb.append(spearman(zz, r))
    sb = sorted(x for x in sb if x is not None)
    lo, hi = sb[int(0.025 * len(sb))], sb[int(0.975 * len(sb)) - 1]
    out.update({"spearman": round(s, 3), "barajado_95": [round(lo, 3), round(hi, 3)],
                "fuera_del_barajado": not (lo <= s <= hi)})
    return out


K = [r for r in csv.DictReader(open(KCSV, encoding="utf-8")) if r["b"] == "VIIRS375"]
V = list(csv.DictReader(open(VCSV, encoding="utf-8")))
res = {"semilla": SEMILLA, "barajados": NB, "corte_cenit": CORTE}

# A
A = [(f(r["z"]), f(r["disp"]) / f(r["vrp_M"]), r["sensor"]) for r in K
     if f(r["vrp_M"]) and f(r["vrp_M"]) > 0 and r["pub"] == "1" and f(r["disp"]) and f(r["disp"]) > 0 and f(r["z"]) is not None]
dtA = sorted(r["dt"] for r in K if f(r["vrp_M"]) and f(r["vrp_M"]) > 0 and r["pub"] == "1" and f(r["disp"]) and f(r["disp"]) > 0)
res["A_K_produccion"] = {"ventana_pares": [dtA[0], dtA[-1]] if dtA else None, **resumen(A, "A")}
res["A_control_pos_cos2"] = resumen([(z, q * math.cos(math.radians(z)) ** 2, s) for z, q, s in A], "A cos2")
res["A_control_pos_x2_mediana"] = med([2 * q for _, q, _ in A])
res["A_por_plataforma"] = {p: resumen([x for x in A if x[2] == p], p) for p in sorted({x[2] for x in A})}

# B y B'
B, Bp, BvK, ROI, solo = [], [], [], {}, {"K_pub_via_no": [], "via_pub_K_no": [], "ninguno": []}
for r in V:
    vm, z = f(r["vrp_M"]), f(r["K_z"]) if f(r["K_z"]) is not None else f(r["z_via"])
    if not vm or vm <= 0:
        continue
    kd = f(r["K_disp"]) if r["K_pub"] == "1" else None
    vd = f(r["via_disp"]) if r["via_pub"] == "1" else None
    vv = f(r["via_vrp_rec"])
    tag = (r["dt"], r["sensor"], round(z, 1), vm, kd, vd, vv)
    if kd and kd > 0 and vd and vd > 0:
        B.append(tag)
    elif kd and kd > 0:
        solo["K_pub_via_no"].append(tag)
    elif vd and vd > 0:
        solo["via_pub_K_no"].append(tag)
    else:
        solo["ninguno"].append(tag)
    if kd and kd > 0 and vv and vv > 0:
        Bp.append(tag)
        for b in ("M14", "C13", "C21", "CIRC", "SENS", "PIX7"):
            vb = f(r.get(f"br_{b}"))
            if vb and vb > 0:
                ROI.setdefault(b, []).append((z, vb / vm, r["sensor"]))
dtB = sorted(t[0] for t in Bp)
res["B_ventana_pares"] = [dtB[0], dtB[-1]] if dtB else None
res["B_K"] = resumen([(t[2], t[4] / t[3], t[1]) for t in B], "B K")
res["B_via_publicada"] = resumen([(t[2], t[5] / t[3], t[1]) for t in B], "B via")
res["B_via_sobre_K"] = resumen([(t[2], t[5] / t[4], t[1]) for t in B], "B via/K")
res["Bp_K"] = resumen([(t[2], t[4] / t[3], t[1]) for t in Bp], "Bp K")
res["Bp_via_vrp"] = resumen([(t[2], t[6] / t[3], t[1]) for t in Bp], "Bp via")
res["Bp_via_sobre_K"] = resumen([(t[2], t[6] / t[4], t[1]) for t in Bp], "Bp via/K")
res["ROI_brazos_sobre_MIROVA"] = {b: resumen(v, b) for b, v in ROI.items()}
res["alertas_sin_par"] = {k: len(v) for k, v in solo.items()}
res["detalle_Bp"] = [{"dt": t[0], "sensor": t[1], "z": t[2], "M": t[3], "K": t[4], "via_pub": t[5], "via_vrp": t[6],
                      "K/M": round(t[4] / t[3], 3), "via/M": round(t[6] / t[3], 3), "via/K": round(t[6] / t[4], 3)}
                     for t in sorted(Bp, key=lambda t: t[2])]
res["detalle_sin_par"] = {k: [list(t) for t in v] for k, v in solo.items()}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("detalle")}, indent=1, ensure_ascii=False))
print("\nDETALLE B' (ordenado por cenit):")
for d in res["detalle_Bp"]:
    print(d)
print("\nALERTAS DE LOS LOTES SIN PAR K+via (dt, sensor, z, M, K_pub, via_pub, via_vrp):")
for k, v in res["detalle_sin_par"].items():
    for t in v:
        print(k, t)
