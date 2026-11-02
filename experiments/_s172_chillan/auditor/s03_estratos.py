# -*- coding: utf-8 -*-
"""s03 (S172, auditoria Chillan): estratos de la razon por pasada (salida de s02) y normalizacion dentro de la noche.

POR QUE: si el deficit vive en un estrato (cenit, plataforma, conteo), la causa comun es ese estrato y no el volcan.
La normalizacion dentro de la noche separa QUIEN depende del cenit: en 1 a 2 h el domo no cambia mucho su potencia,
asi que cada pasada se divide por la pasada mas cercana al nadir de la misma noche y sensor, por separado para
nosotros y para MIROVA. Si la caida esta en nuestra curva y no en la de MIROVA, el deficit oblicuo es nuestro.

P1: si la razon no dependiera de nada, todos los estratos darian lo mismo; control positivo: el estrato por
    "magnitud propia" (disp) debe mostrar dependencia porque la razon la contiene (se imprime como referencia).
P2: control negativo: se barajan los cenits entre pasadas del mismo sensor (semilla fija, 200 veces) y se informa
    el rango de Spearman barajado; un Spearman real fuera de ese rango no es ruido del instrumento.
Ventana y denominador: los de la salida de s02 (pares nocturnos, NdC, D-9 SN).
Uso: python -B s03_estratos.py <pasadas.csv> <salida.json>
"""
import collections, csv, json, math, random, statistics, sys

IN, OUT = sys.argv[1], sys.argv[2]
R = list(csv.DictReader(open(IN, encoding="utf-8")))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


P = []
for r in R:
    vm, d = f(r["vrp_M"]), f(r["disp"])
    if vm and vm > 0 and r["pub"] == "1" and d and d > 0:
        r2 = dict(r)
        r2.update(vm=vm, d=d, z=f(r["z"]), ratio=d / vm, pc_n=f(r["pc_n"]), n_pos=f(r["n_pos"]),
                  n_core=f(r["n_core_pos"]), pcd=f(r["pc_dist"]), dM=f(r["dist_M"]), tbg=f(r["t_bg"]))
        P.append(r2)


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


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
    pr = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pr) < 4:
        return None
    a, b = rank([p[0] for p in pr]), rank([p[1] for p in pr])
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return round(num / den, 3) if den else None


def zb(z):
    return "z?" if z is None else ("z<30" if z < 30 else "z30-50" if z < 50 else "z50-60" if z < 60 else "z>=60")


def estratos(S, clave):
    g = collections.defaultdict(list)
    for x in S:
        g[clave(x)].append(x["ratio"])
    return {k: {"n": len(v), "razon_mediana": med(v)} for k, v in sorted(g.items(), key=lambda kv: str(kv[0]))}


out = {"n_pares": len(P), "por_sensor": {}}
rng = random.Random(172)
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    S = [x for x in P if x["b"] == b]
    if not S:
        continue
    sp_real = spearman([x["z"] for x in S], [x["ratio"] for x in S])
    sh = []
    for _ in range(200):
        zs = [x["z"] for x in S]
        rng.shuffle(zs)
        sh.append(spearman(zs, [x["ratio"] for x in S]))
    sh = sorted(s for s in sh if s is not None)
    plat = lambda x: x["sensor"].replace("_750", "").split("_")[-1]  # noqa: E731
    e = {
        "n": len(S), "razon_mediana": med([x["ratio"] for x in S]),
        "fecha_min": min(x["dt"] for x in S), "fecha_max": max(x["dt"] for x in S),
        "spearman_razon_vs_cenit": sp_real,
        "spearman_barajado_p2.5_p97.5": [sh[int(0.025 * len(sh))], sh[int(0.975 * len(sh)) - 1]] if sh else None,
        "spearman_razon_vs_n_pos": spearman([x["n_pos"] for x in S], [x["ratio"] for x in S]),
        "spearman_razon_vs_vrp_MIROVA": spearman([x["vm"] for x in S], [x["ratio"] for x in S]),
        "spearman_razon_vs_tbg": spearman([x["tbg"] for x in S], [x["ratio"] for x in S]),
        "spearman_razon_vs_dist_cumulo": spearman([x["pcd"] for x in S], [x["ratio"] for x in S]),
        "spearman_cenit_vs_dist_MIROVA": spearman([x["z"] for x in S], [x["dM"] for x in S]),
        "spearman_cenit_vs_n_pos_nuestro": spearman([x["z"] for x in S], [x["n_pos"] for x in S]),
        "por_cenit": estratos(S, lambda x: zb(x["z"])),
        "por_fecha_18sep": estratos(S, lambda x: "antes_2026-09-18" if x["dt"] < "2026-09-18" else "desde_2026-09-18"),
        "por_plataforma": estratos(S, plat),
        "por_plataforma_y_cenit": estratos(S, lambda x: plat(x) + "|" + zb(x["z"])),
        "por_n_pos_nuestro": estratos(S, lambda x: "1" if x["n_pos"] == 1 else "2" if x["n_pos"] == 2 else "3-5" if x["n_pos"] <= 5 else "6+"),
        "por_n_pos_y_cenit<50": estratos([x for x in S if x["z"] is not None and x["z"] < 50],
                                         lambda x: "1" if x["n_pos"] == 1 else "2" if x["n_pos"] == 2 else "3+"),
        "por_vrp_MIROVA": estratos(S, lambda x: "<1" if x["vm"] < 1 else "1-5" if x["vm"] < 5 else "5-15" if x["vm"] < 15 else ">=15"),
        "por_dist_MIROVA": estratos(S, lambda x: "?" if x["dM"] is None else "<=1" if x["dM"] <= 1 else "1-2" if x["dM"] <= 2 else ">2"),
        "por_fuente_MIROVA": estratos(S, lambda x: x["src_M"]),
        "por_noche_dia": "SIN DATO: el pipeline y el banco sólo dejan pasadas nocturnas (es_pasada_diurna_descartada)",
    }
    # normalizacion dentro de la noche: cada pasada / la pasada mas nadir de la noche y sensor
    noches = collections.defaultdict(list)
    for x in S:
        noches[x["noche"]].append(x)
    filas_n = []
    for n, v in noches.items():
        if len(v) < 2:
            continue
        ref = min(v, key=lambda y: y["z"])
        for x in v:
            if x is ref:
                continue
            filas_n.append({"noche": n, "z_ref": ref["z"], "z": x["z"], "dz": x["z"] - ref["z"],
                            "nuestro_rel": x["d"] / ref["d"], "mirova_rel": x["vm"] / ref["vm"]})
    e["dentro_de_la_noche"] = {
        "n_pasadas": len(filas_n), "n_noches": len({x["noche"] for x in filas_n}),
        "por_dz": {k: {"n": len(v), "nuestro_rel_mediana": med([y["nuestro_rel"] for y in v]),
                       "mirova_rel_mediana": med([y["mirova_rel"] for y in v])}
                   for k, v in sorted(collections.defaultdict(list, {
                       kk: [y for y in filas_n if (("dz<15" if y["dz"] < 15 else "dz15-35" if y["dz"] < 35 else "dz>=35") == kk)]
                       for kk in ("dz<15", "dz15-35", "dz>=35")}).items())},
        "spearman_nuestro_rel_vs_dz": spearman([y["dz"] for y in filas_n], [y["nuestro_rel"] for y in filas_n]),
        "spearman_mirova_rel_vs_dz": spearman([y["dz"] for y in filas_n], [y["mirova_rel"] for y in filas_n]),
    }
    out["por_sensor"][b] = e
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
