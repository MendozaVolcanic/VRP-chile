# -*- coding: utf-8 -*-
"""S150. ¿La sigma de la escena separa perdidas de conservadas DENTRO de cada estrato (A83: Simpson)?
Estratos: cenit (<30, 30-50, >=50), volcan, y tramo de magnitud B (pc_vrp). Tambien: en que fraccion
de las alertas el umbral de F en la cumbre es el estadistico (mu+5sd > C1), y por cuanto lo sube.

  python estratos.py filas.json
"""
import collections, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = json.load(open(sys.argv[1], encoding="utf-8"))
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}
C1S = 0.003


def auc(pos, neg):
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def estratificado(sel, fv, fe, nombre):
    g = collections.defaultdict(lambda: ([], []))
    for r in sel:
        v = fv(r)
        if v is None:
            continue
        g[fe(r)][0 if r["perdida"] else 1].append(v)
    num = den = 0; partes = []
    for k, (L, K) in sorted(g.items(), key=lambda x: str(x[0])):
        a = auc(L, K)
        if a is None:
            continue
        w = len(L) * len(K); num += a * w; den += w
        partes.append("%s %.2f (%d/%d)" % (k, a, len(L), len(K)))
    print("  %-26s AUC ponderado %s | %s" % (nombre, "%.2f" % (num / den) if den else "-", "; ".join(partes)))


def zb(r):
    z = r["B"]["sensor_zenith_deg"]
    return "z<30" if z < 30 else "z30-50" if z < 50 else "z>=50"


def mb(r):
    v = r["B"]["pc_vrp"] or 0
    return "Bvrp<0.02" if v < 0.02 else "Bvrp0.02-0.05" if v < 0.05 else "Bvrp0.05-0.1" if v < 0.1 else "Bvrp>=0.1"


sel = [r for r in F if r["b"] == "VIIRS375" and r["clave"] not in MALAS]
print("VIIRS375, alertas que B publica, sin las 5 filas OCR malas: n =", len(sel), "| perdidas", sum(r["perdida"] for r in sel))
sd = lambda r: r["B"]["diag_sd_dnti"]
sde = lambda r: r["B"]["diag_sd_deti"]
z = lambda r: r["B"]["sensor_zenith_deg"]
v = lambda r: r["B"]["pc_vrp"]
for nom_v, fv in (("sd_dNTI", sd), ("sd_dETI", sde), ("cenit", z), ("B pc_vrp", v)):
    print(nom_v)
    estratificado(sel, fv, zb, "por cenit")
    estratificado(sel, fv, lambda r: r["vol"], "por volcan")
    estratificado(sel, fv, mb, "por magnitud de B")
# umbral efectivo de F en la cumbre
n = len(sel); est = [r for r in sel if r["B"].get("stat_dnti_s") is not None]
print("\numbral de F en la cumbre = estadistico (mu+5sd > C1) en dNTI: %d de %d; en dETI: %d de %d" % (
    sum(r["B"]["stat_dnti_s"] > C1S for r in est), len(est), sum(r["B"]["stat_deti_s"] > C1S for r in est), len(est)))
for nombre, sub in (("perdidas", [r for r in est if r["perdida"]]), ("conservadas", [r for r in est if not r["perdida"]])):
    fac = sorted(r["B"]["stat_dnti_s"] / C1S for r in sub); face = sorted(max(r["B"]["stat_deti_s"], C1S) / C1S for r in sub)
    print("  %-11s factor umbral F / C1 dNTI: mediana %.2f (p10 %.2f, p90 %.2f) | dETI: mediana %.2f" % (
        nombre, fac[len(fac) // 2], fac[len(fac) // 10], fac[(9 * len(fac)) // 10], face[len(face) // 2]))
# sigma por cenit, en TODAS las alertas publicadas por B (perdidas y conservadas juntas)
print("\nsd_dNTI y umbral F (mu+5sd) por cenit, alertas que B publica:")
g = collections.defaultdict(list)
for r in est:
    g[zb(r)].append(r)
for k in ("z<30", "z30-50", "z>=50"):
    xs = sorted(r["B"]["diag_sd_dnti"] for r in g[k]); ys = sorted(r["B"]["stat_dnti_s"] for r in g[k])
    nb = sorted(r["B"]["diag_n_bg_used_first_pass"] for r in g[k])
    print("  %-7s n=%4d sd_dNTI mediana %.5f | mu+5sd mediana %.5f | pool mediana %d | pierde %d" % (
        k, len(xs), xs[len(xs) // 2], ys[len(ys) // 2], nb[len(nb) // 2], sum(r["perdida"] for r in g[k])))
