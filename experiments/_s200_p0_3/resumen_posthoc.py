"""Tablas de la variante post hoc T+ (ADENDA_POSTHOC.md). Salida: resumen_posthoc_salida.txt (markdown)."""
import json
import math
from collections import defaultdict

import numpy as np

import comun as C

C.utf8()
regs = [json.loads(x) for x in open(C.AQUI / "resultados_posthoc.jsonl", encoding="utf-8")]
umb = json.loads((C.AQUI / "umbrales_posthoc.json").read_text(encoding="utf-8"))
validos = [r for r in regs if "brazo" in r]
desc = [r for r in regs if "motivo" in r]
ESC = (1, 3, 10, 30)
idx = defaultdict(dict)
for r in validos:
    idx[(r["escena"], r["d"], r["az"], r["T"])][r["brazo"]] = r


def razon(a, b):
    va, vb = a.get("vrp_min"), b.get("vrp_min")
    if va is None and vb is None:
        return None
    if va is None:
        return math.inf
    if vb is None:
        return 0.0
    return va / vb


def fmt(x, nd=2):
    if x is None:
        return "s/d"
    if isinstance(x, float) and math.isinf(x):
        return "inf"
    return f"{x:.{nd}f}"


def clase(m):
    if m is None:
        return "s/d"
    return "RELEVANTE" if m >= 1.5 else ("menor" if m >= 1.1 else "nulo")


print("## Variante post hoc T+ (sólo exceso positivo de Chillán)\n")
print(f"Registros {len(regs)}; con barrido {len(validos)}; descartados: "
      + ", ".join(f"{m} {sum(1 for r in desc if r['motivo'] == m)}" for m in sorted({r['motivo'] for r in desc})))
print(f"No monótonos {sum(1 for r in validos if r.get('no_monotono'))}; sobre 634 K "
      f"{sum(1 for r in validos if r.get('sobre_techo_634K'))}; alerta con 0 MW {sum(1 for r in validos if r.get('alerta_0'))}; "
      f"sin alerta a 200 MW {sum(1 for r in validos if r.get('vrp_min') is None)}")
veredicto = defaultdict(list)
for T in (1000.0, 600.0):
    print(f"\n### T_hot {T:.0f} K: VRP_eq mínimo sin la anomalía (mediana) y razón r con/sin (mediana; máx) por escala\n")
    print("| escena | cenit | d km | n dir | zona | sin (MW) | r x1 | r x3 | r x10 | r x30 | dir. sin<=1 y con>1 (x1/x3/x10/x30) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for esc in sorted({k[0] for k in idx}):
        for d in (2.0, 5.0, 10.0, 20.0):
            filas = [v for k, v in idx.items() if k[0] == esc and k[1] == d and k[3] == T and "T-sin" in v]
            if not filas:
                continue
            celdas, perd = [], []
            for s in ESC:
                rs = [razon(v[f"T+-con-{s}"], v["T-sin"]) for v in filas]
                rs = [x for x in rs if x is not None]
                m = float(np.median(rs)) if rs else None
                celdas.append(f"{fmt(m)}; {fmt(max(rs) if rs else None)}")
                p = sum(1 for v in filas if (v["T-sin"].get("vrp_min") or 1e9) <= 1.0
                        and (v[f"T+-con-{s}"].get("vrp_min") or 1e9) > 1.0)
                perd.append(str(p))
                if T == 1000.0 and d >= 5:
                    veredicto[s].append((esc, d, m, p / len(filas)))
            sin = float(np.median([v["T-sin"]["vrp_min"] for v in filas]))
            zonas = sorted({v["T-sin"]["zona"] for v in filas})
            print(f"| {esc} | {filas[0]['T-sin']['cenit']:.1f} | {d:.0f} | {len(filas)} | {zonas} | {sin:.2f} | "
                  + " | ".join(celdas) + f" | {'/'.join(perd)} |")

print("\n### Por zona de la caja (T 1000 K, todas las escenas y distancias)\n")
print("| escala | zona | n | r mediana | r p90 | r máx |")
print("|---|---|---|---|---|---|")
for s in ESC:
    for z in (0, 1, 2):
        rs = [razon(v[f"T+-con-{s}"], v["T-sin"]) for k, v in idx.items() if k[3] == 1000.0 and v["T-sin"]["zona"] == z]
        rs = [x for x in rs if x is not None and not math.isinf(x)]
        if rs:
            print(f"| x{s} | {z} | {len(rs)} | {np.median(rs):.3f} | {np.percentile(rs, 90):.3f} | {max(rs):.3f} |")

print("\n### Umbrales sin foco (pase 1 y pase 2)\n")
print("| escena | brazo | alertadas | sd_nti p1 | u_nti2 p1 | sd_nti p2 | u_nti1 p2 | u_nti2 p2 | u_eti1 p2 | u_eti2 p2 |")
print("|---|---|---|---|---|---|---|---|---|---|")
for esc, u in umb.items():
    for b, x in u["T+"].items():
        p1, p2 = x["pasada1"], x["pasada2"]
        print(f"| {esc} | {b} | {x['n_alertadas']} | {fmt(p1['sd_nti'], 5)} | {fmt(p1['u_nti2'], 4)} | {fmt(p2['sd_nti'], 5)} | "
              f"{fmt(p2['u_nti1'], 4)} | {fmt(p2['u_nti2'], 4)} | {fmt(p2['u_eti1'], 4)} | {fmt(p2['u_eti2'], 4)} |")

print("\n### Veredicto con el criterio de la §7 (d >= 5 km, T 1000 K)\n")
for s in ESC:
    cl = veredicto[s]
    ms = [c[2] for c in cl if c[2] is not None]
    peor = max(cl, key=lambda c: c[2] or 0)
    perd = max(c[3] for c in cl)
    print(f"- x{s}: mayor mediana de r {fmt(max(ms), 3)} ({peor[0]} a {peor[1]:.0f} km); mayor fracción de direcciones "
          f"que pasan de <=1 MW a >1 MW {perd:.2f} -> {clase(max(ms)) if perd < 0.25 else 'RELEVANTE'}")
