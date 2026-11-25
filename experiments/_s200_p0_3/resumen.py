"""Tablas del informe desde resultados.jsonl y umbrales.json. Salida: resumen_salida.txt (markdown)."""
import json
import math
from collections import defaultdict

import numpy as np

import comun as C

C.utf8()
regs = [json.loads(x) for x in open(C.AQUI / "resultados.jsonl", encoding="utf-8")]
umb = json.loads((C.AQUI / "umbrales.json").read_text(encoding="utf-8"))
validos = [r for r in regs if "brazo" in r]
desc = [r for r in regs if "motivo" in r]

# índice (escena, serie, d, az, T) -> brazo -> registro
idx = defaultdict(dict)
for r in validos:
    idx[(r["escena"], r["serie"], r["d"], r["az"], r["T"])][r["brazo"]] = r


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


def med(xs):
    xs = [x for x in xs if x is not None]
    return float(np.median(xs)) if xs else None


def clase(m):
    if m is None:
        return "s/d"
    return "RELEVANTE" if m >= 1.5 else ("menor" if m >= 1.1 else "nulo")


def bloque(serie, con, sin, T, titulo):
    print(f"\n### {titulo} (T_hot {T:.0f} K)\n")
    print("| escena | cenit | d km | n dir | zona huella | VRP_eq min sin (mediana, MW) | con (mediana, MW) | "
          "r mediana | r máx | dir. sin<=1 y con>1 | clase |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    clases = []
    for esc in sorted({k[0] for k in idx if k[1] == serie}):
        for d in (2.0, 5.0, 10.0, 20.0):
            filas = [v for k, v in idx.items() if k[0] == esc and k[1] == serie and k[2] == d and k[4] == T
                     and con in v and sin in v]
            if not filas:
                continue
            rs = [razon(v[con], v[sin]) for v in filas]
            rs = [x for x in rs if x is not None]
            zonas = sorted({v[sin]["zona"] for v in filas})
            perd = sum(1 for v in filas if (v[sin].get("vrp_min") or 1e9) <= 1.0 and (v[con].get("vrp_min") or 1e9) > 1.0)
            m = med(rs)
            cenit = filas[0][sin]["cenit"]
            clases.append((esc, d, m, perd / len(filas)))
            print(f"| {esc} | {cenit:.1f} | {d:.0f} | {len(filas)} | {zonas} | {fmt(med([v[sin].get('vrp_min') for v in filas]))} "
                  f"| {fmt(med([v[con].get('vrp_min') for v in filas]))} | {fmt(m)} | {fmt(max(rs) if rs else None)} | "
                  f"{perd} | {clase(m) if d >= 5 else clase(m) + ' (borde del cráter)'} |")
    return clases


print("## Resultados (generado por resumen.py)\n")
print(f"Registros: {len(regs)}; con barrido: {len(validos)}; puntos descartados por motivo: "
      + ", ".join(f"{m} {sum(1 for r in desc if r['motivo'] == m)}" for m in sorted({r['motivo'] for r in desc})))
print(f"No monótonos: {sum(1 for r in validos if r.get('no_monotono'))} de {len(validos)}; "
      f"sobre el techo de 634 K: {sum(1 for r in validos if r.get('sobre_techo_634K'))}; "
      f"alerta con 0 MW: {sum(1 for r in validos if r.get('alerta_0'))}; "
      f"sin alerta a 200 MW: {sum(1 for r in validos if r.get('vrp_min') is None)}")

todas = {}
for T in (1000.0, 600.0):
    todas[("R", T)] = bloque("R", "R-con", "R-sin", T, "Serie R: escena real con su anomalía contra la misma sin ella")
    todas[("R9", T)] = bloque("R", "R-con", "R-sin9", T, "Serie R, sensibilidad: brazo sin con halo de 9 celdas")
    for s in (1, 3, 10):
        todas[(f"T{s}", T)] = bloque("T", f"T-con-{s}", "T-sin", T, f"Serie T: trasplante de Chillán a escala {s}")
    todas[("N", T)] = bloque("N", "N-con", "N-sin", T, "Control C4: ruido que duplica sd")

print("\n### Umbrales sin foco, pase 2 (u_nti2 zona sensible, u_nti1 zonas 0 y 1)\n")
print("| escena | brazo | alertadas | sd_nti p1 | u_nti2 p1 | sd_nti p2 | u_nti1 p2 | u_nti2 p2 | u_eti1 p2 | u_eti2 p2 |")
print("|---|---|---|---|---|---|---|---|---|---|")
for esc, u in umb.items():
    for serie, brs in u.items():
        for b, x in brs.items():
            if b == "origen":
                continue
            p1, p2 = x["pasada1"], x["pasada2"]
            print(f"| {esc} | {b} | {x['n_alertadas']} | {fmt(p1['sd_nti'], 5)} | {fmt(p1['u_nti2'], 4)} | "
                  f"{fmt(p2['sd_nti'], 5)} | {fmt(p2['u_nti1'], 4)} | {fmt(p2['u_nti2'], 4)} | {fmt(p2['u_eti1'], 4)} | "
                  f"{fmt(p2['u_eti2'], 4)} |")

print("\n### Por zona de la caja (todas las escenas y distancias juntas, T 1000 K)\n")
print("| comparación | zona | n | r mediana | r p90 | r máx |")
print("|---|---|---|---|---|---|")
for con, sin, serie in (("R-con", "R-sin", "R"), ("T-con-1", "T-sin", "T"), ("T-con-3", "T-sin", "T"),
                        ("T-con-10", "T-sin", "T"), ("N-con", "N-sin", "N")):
    for z in (0, 1, 2):
        rs = [razon(v[con], v[sin]) for k, v in idx.items() if k[1] == serie and k[4] == 1000.0 and con in v
              and sin in v and v[sin]["zona"] == z]
        rs = [x for x in rs if x is not None and not math.isinf(x)]
        if rs:
            print(f"| {con}/{sin} | {z} | {len(rs)} | {np.median(rs):.3f} | {np.percentile(rs, 90):.3f} | {max(rs):.3f} |")

print("\n### Control C3 (Llaima, sin calor; serie R, brazo R-con)\n")
ll = [r for r in validos if r["escena"].startswith("Llaima") and r["brazo"] == "R-con"]
for T in (1000.0, 600.0):
    x = [r for r in ll if r["T"] == T]
    n0 = sum(1 for r in x if r["alerta_0"])
    n200 = sum(1 for r in x if r["vrp_min"] is not None)
    print(f"- T {T:.0f} K: puntos válidos {len(x)}; alertan con 0 MW {n0}; alertan con 200 MW o menos {n200}; "
          f"VRP_eq mín mediana {fmt(med([r['vrp_min'] for r in x]))} MW. "
          f"{'PASA' if n0 == 0 and n200 >= min(30, len(x)) else 'NO PASA'}")

print("\n### Control C4 (ruido): mediana de r en zona sensible\n")
rs = [razon(v["N-con"], v["N-sin"]) for k, v in idx.items() if k[1] == "N" and k[4] == 1000.0 and "N-con" in v
      and v["N-sin"]["zona"] == 2]
rs = [x for x in rs if x is not None and not math.isinf(x)]
print(f"- zona 2: n {len(rs)}, mediana {np.median(rs):.3f} -> {'PASA' if np.median(rs) >= 1.3 else 'NO PASA'}")
rs = [razon(v["N-con"], v["N-sin"]) for k, v in idx.items() if k[1] == "N" and k[4] == 1000.0 and "N-con" in v]
rs = [x for x in rs if x is not None and not math.isinf(x)]
print(f"- todas las zonas: n {len(rs)}, mediana {np.median(rs):.3f}")

print("\n### Veredicto por el criterio pre-registrado (d >= 5 km, T 1000 K)\n")
for clave, nombre in (("R", "escenas reales"), ("T1", "trasplante x1"), ("T3", "trasplante x3"),
                      ("T10", "trasplante x10 (evento grande)")):
    cl = [c for c in todas[(clave, 1000.0)] if c[1] >= 5]
    ms = [c[2] for c in cl if c[2] is not None]
    mx = max(ms) if ms else None
    perd = max(c[3] for c in cl) if cl else None
    peor = max(cl, key=lambda c: c[2] or 0) if cl else None
    print(f"- {nombre}: mayor mediana de r {fmt(mx, 3)} ({peor[0]} a {peor[1]:.0f} km); mayor fracción de direcciones "
          f"que pasan de <=1 MW a >1 MW {fmt(perd, 2)} -> {clase(mx) if (perd or 0) < 0.25 else 'RELEVANTE'}")
