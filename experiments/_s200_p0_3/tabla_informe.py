"""Tablas que entran al INFORME.md (las arma armar_informe.py). Salida: tabla_informe.md (newline="")."""
import json
import math
from collections import defaultdict

import numpy as np

import comun as C

C.utf8()
regs = [json.loads(x) for x in open(C.AQUI / "resultados.jsonl", encoding="utf-8")]
regs += [json.loads(x) for x in open(C.AQUI / "resultados_posthoc.jsonl", encoding="utf-8")]
idx = defaultdict(dict)
for r in regs:
    if "brazo" in r:
        idx[(r["escena"], r["serie"], r["d"], r["az"], r["T"])][r["brazo"]] = r
umb = json.loads((C.AQUI / "umbrales.json").read_text(encoding="utf-8"))
umbp = json.loads((C.AQUI / "umbrales_posthoc.json").read_text(encoding="utf-8"))


def c(x, nd=2):
    if x is None:
        return "s/d"
    return f"{x:.{nd}f}".replace(".", ",")


def r_med(esc, serie, d, con, sin, T=1000.0):
    rs = [v[con]["vrp_min"] / v[sin]["vrp_min"] for k, v in idx.items()
          if k[0] == esc and k[1] == serie and k[2] == d and k[4] == T and con in v and sin in v
          and v[con].get("vrp_min") and v[sin].get("vrp_min")]
    return (float(np.median(rs)), float(max(rs)), len(rs)) if rs else (None, None, 0)


L = []
L.append("### Tabla 1. Foco a 1000 K: VRP_eq mínimo sin la anomalía y razón con/sin (mediana de las direcciones; máximo)\n")
L.append("R: la escena real con su anomalía contra la misma con la anomalía quitada. T+: trasplante del exceso caliente de "
         "Chillán al cráter, escala 1, 3, 10 y 30 (unos 13, 40, 134 y 403 MW medidos por la vía, "
         "`vrp_trasplantes_salida.txt`), contra la escena destino sin trasplante. Zona: 2 sensible, 1 conservadora, "
         "0 resto de la grilla (umbrales conservadores).\n")
L.append("| escena | cenit | d km | zona | n dir R | VRP_eq mín sin (MW) | r R | n dir T+ | r T+ x1 | r T+ x3 | r T+ x10 | r T+ x30 |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for esc in sorted({k[0] for k in idx}):
    for d in (2.0, 5.0, 10.0, 20.0):
        filas = [v for k, v in idx.items() if k[0] == esc and k[1] == "R" and k[2] == d and k[4] == 1000.0 and "R-sin" in v]
        if not filas:
            continue
        sin = float(np.median([v["R-sin"]["vrp_min"] for v in filas]))
        zonas = ",".join(str(z) for z in sorted({v["R-sin"]["zona"] for v in filas}))
        rr = r_med(esc, "R", d, "R-con", "R-sin")
        celdas = []
        nt = 0
        for s in (1, 3, 10, 30):
            m, mx, n = r_med(esc, "T+", d, f"T+-con-{s}", "T-sin")
            nt = max(nt, n)
            celdas.append("n/a" if m is None else f"{c(m)}; {c(mx)}")
        cen = filas[0]["R-sin"]["cenit"]
        L.append(f"| {esc} | {c(cen, 1)} | {d:.0f} | {zonas} | {rr[2]} | {c(sin)} | {c(rr[0])}; {c(rr[1])} | {nt} | "
                 + " | ".join(celdas) + " |")

L.append("\n### Tabla 2. Razón con/sin agrupada por zona de la caja (todas las escenas y distancias, foco a 1000 K)\n")
L.append("| comparación | zona | n | r mediana | r percentil 90 | r máx |")
L.append("|---|---|---|---|---|---|")
for con, sin, serie, nombre in (("R-con", "R-sin", "R", "R real"), ("T+-con-1", "T-sin", "T+", "T+ x1"),
                                ("T+-con-3", "T-sin", "T+", "T+ x3"), ("T+-con-10", "T-sin", "T+", "T+ x10"),
                                ("T+-con-30", "T-sin", "T+", "T+ x30"),
                                ("T-con-1", "T-sin", "T", "T pre-registrado x1"),
                                ("T-con-3", "T-sin", "T", "T pre-registrado x3"),
                                ("T-con-10", "T-sin", "T", "T pre-registrado x10 (artefacto)"),
                                ("N-con", "N-sin", "N", "C4 ruido (control)")):
    for z in (2, 1, 0):
        rs = [v[con]["vrp_min"] / v[sin]["vrp_min"] for k, v in idx.items() if k[1] == serie and k[4] == 1000.0
              and con in v and sin in v and v[sin]["zona"] == z and v[con].get("vrp_min") and v[sin].get("vrp_min")]
        if rs:
            L.append(f"| {nombre} | {z} | {len(rs)} | {c(float(np.median(rs)), 3)} | {c(float(np.percentile(rs, 90)), 3)} "
                     f"| {c(max(rs), 3)} |")

L.append("\n### Tabla 3. Umbral de NTI de cada pase, sin foco (Chillán real y el trasplante a Láscar 2026-10-08)\n")
L.append("| escena | brazo | celdas alertadas | sd NTI pase 1 | u sensible pase 1 | sd NTI pase 2 | u sensible pase 2 | u conservador pase 2 |")
L.append("|---|---|---|---|---|---|---|---|")
for esc, fuente, brs in (("NevadosDeChillan_2026-10-10_0554", umb, (("R", "R-con"), ("R", "R-sin"), ("N", "N-con"))),
                         ("Lascar_2026-10-08_0542", umb, (("T", "T-sin"), ("T", "T-con-10"))),
                         ("Lascar_2026-10-08_0542", umbp, (("T+", "T+-con-1"), ("T+", "T+-con-3"), ("T+", "T+-con-10"),
                                                            ("T+", "T+-con-30"))),
                         ("Tupungatito_2026-08-21_0548", umb, (("T", "T-con-10"),))):
    for serie, b in brs:
        x = fuente[esc][serie][b]
        p1, p2 = x["pasada1"], x["pasada2"]
        L.append(f"| {esc} | {b} | {x['n_alertadas']} | {c(p1['sd_nti'], 5)} | {c(p1['u_nti2'], 4)} | {c(p2['sd_nti'], 5)} "
                 f"| {c(p2['u_nti2'], 4)} | {c(p2['u_nti1'], 4)} |")

with open(C.AQUI / "tabla_informe.md", "w", encoding="utf-8", newline="") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))
