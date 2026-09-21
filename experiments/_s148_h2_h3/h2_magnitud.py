# -*- coding: utf-8 -*-
"""H2: en las positivas V375 que publican los dos brazos, que pixel se pierde con max, cuanto
aportaba, y a cual de los dos valores (B o F) se parece mas MIROVA, pasada por pasada y por volcan.

La magnitud publicada de VIIRS 375 es el nucleo F5' (pipeline/f5_core.py): el pixel pico del
cumulo mas los pixeles a 0,75 km o menos de el. Aca se reconstruye ese nucleo en cada brazo desde
anomaly_pixels (se comprueba contra f5_core_vrp_mw persistido) y se comparan los dos conjuntos.
"""
import sys
import math
import random
import collections
import statistics as st
from base import cargar, mirova_mw, nucleo, clave_px, BT_GATE_K, INNER, hav, zona

rb, rf, lab, por, comunes = cargar(sys.argv)
ks = [k for k in comunes if k[1] == "VIIRS375" and lab[k] == "pos" and rb[k]["_pub"] and rf[k]["_pub"]]
print("positivas V375 publicadas por los dos brazos:", len(ks))

print("\n#### 0. CONTROL: mi nucleo reconstruido contra f5_core_vrp_mw persistido y contra lo publicado")
mal = 0
for k in ks:
    for nombre, recs in (("B", rb), ("F", rf)):
        nu, _ = nucleo(recs[k], INNER[k[0]])
        tot = sum(p["vrp_mw"] for p in nu) if nu else None
        if tot is None or abs(tot - recs[k]["_disp"]) > 2e-4:
            mal += 1
            print("   difiere", k, nombre, tot, recs[k]["_disp"], recs[k].get("f5_core_vrp_mw"))
print("   records cuyo nucleo reconstruido difiere de lo publicado en mas de 0,0002 MW:", mal, "de", 2 * len(ks))

baja = [k for k in ks if rf[k]["_disp"] < rb[k]["_disp"] - 1e-9]
sube = [k for k in ks if rf[k]["_disp"] > rb[k]["_disp"] + 1e-9]
print("\n#### 1. CUANTAS BAJAN: %d | suben %d | identicas %d" % (len(baja), len(sube), len(ks) - len(baja) - len(sube)))

print("\n#### 2. QUE PIXEL SE PIERDE en las que bajan (nucleo de B menos nucleo de F)")
perdidos = []
tipo = collections.Counter()
for k in baja:
    a, b = rb[k], rf[k]
    na, pka = nucleo(a, INNER[k[0]])
    nb, pkb = nucleo(b, INNER[k[0]])
    todosF = {clave_px(p) for p in (b.get("anomaly_pixels") or [])}
    sa, sb = {clave_px(p): p for p in na}, {clave_px(p): p for p in nb}
    mismo_pico = clave_px(pka) == clave_px(pkb)
    fuera = [p for c, p in sa.items() if c not in sb]
    nuevos = [p for c, p in sb.items() if c not in sa]
    # cambio de vrp en pixeles comunes (deberia ser 0: mismo fondo)
    dcom = max([abs(sa[c]["vrp_mw"] - sb[c]["vrp_mw"]) for c in sa if c in sb] or [0])
    desap = [p for p in fuera if clave_px(p) not in todosF]      # no esta en ningun lado de F: dejo de detectarse
    reubic = [p for p in fuera if clave_px(p) in todosF]          # sigue detectado en F pero ya no entra al nucleo
    tipo["mismo pico" if mismo_pico else "cambia el pico"] += 1
    tipo["pierde pixeles que F ya no detecta"] += bool(desap)
    tipo["pierde pixeles que F detecta pero quedan fuera del nucleo"] += bool(reubic)
    tipo["gana pixeles"] += bool(nuevos)
    m, _ = mirova_mw(k, por)
    for p in desap:
        perdidos.append({"k": k, "vrp": p["vrp_mw"], "ex": p["bt_k"] - a["t_bg_k"],
                         "d_pico": hav(p["lat"], p["lon"], pka["lat"], pka["lon"]),
                         "frac": p["vrp_mw"] / a["_disp"], "pico_ex": pka["bt_k"] - a["t_bg_k"], "pico_vrp": pka["vrp_mw"],
                         "es_pico": clave_px(p) == clave_px(pka)})
    print("  %-20s %s z %4.1f | B %.4f (%d px nucleo; fp %d sp %d) -> F %.4f (%d px; fp %d sp %d) | MIROVA %.3f | %s | dejan de detectarse %d, reubicados %d, nuevos %d | dif max en comunes %.4f" %
          (k[0], k[2], a["sensor_zenith_deg"], a["_disp"], len(na), a.get("diag_n_first_pass_pixels") or 0,
           a.get("diag_n_second_pass_recapture") or 0, b["_disp"], len(nb), b.get("diag_n_first_pass_pixels") or 0,
           b.get("diag_n_second_pass_recapture") or 0, m, "mismo pico" if mismo_pico else "CAMBIA PICO",
           len(desap), len(reubic), len(nuevos), dcom))
print("  resumen:", dict(tipo))

print("\n#### 3. COMO ES EL PIXEL QUE DEJA DE DETECTARSE (n=%d pixeles en %d pasadas)" % (len(perdidos), len({p["k"] for p in perdidos})))
if perdidos:
    ex = [p["ex"] for p in perdidos]
    print("   exceso BT sobre el fondo (K): min %.2f | mediana %.2f | max %.2f | bajo la compuerta de 3 K: %d de %d" %
          (min(ex), st.median(ex), max(ex), sum(e <= BT_GATE_K for e in ex), len(ex)))
    print("   exceso BT del pixel PICO de esas pasadas (K): mediana %.2f" % st.median(p["pico_ex"] for p in perdidos))
    print("   pixel perdido es mas frio que su pico en %d de %d" % (sum(p["ex"] < p["pico_ex"] for p in perdidos if not p["es_pico"]), sum(not p["es_pico"] for p in perdidos)))
    print("   el pixel perdido ERA el pico de B en %d casos" % sum(p["es_pico"] for p in perdidos))
    print("   distancia al pico (km): mediana %.2f max %.2f" % (st.median(p["d_pico"] for p in perdidos), max(p["d_pico"] for p in perdidos)))
    print("   MW del pixel perdido: mediana %.4f | suma %.3f | razon perdido/pico mediana %.2f" %
          (st.median(p["vrp"] for p in perdidos), sum(p["vrp"] for p in perdidos), st.median(p["vrp"] / p["pico_vrp"] for p in perdidos)))
    por_pasada = collections.defaultdict(float)
    for p in perdidos:
        por_pasada[p["k"]] += p["frac"]
    fr = sorted(por_pasada.values())
    print("   fraccion de la magnitud de B que aportaban, por pasada: min %.2f | mediana %.2f | max %.2f" % (fr[0], st.median(fr), fr[-1]))

print("\n#### 3b. Umbral efectivo del primer pase en esas pasadas: mu + 5 sigma contra el piso C1 = 0,003")
for nombre, grupo in (("bajan", baja), ("identicas", [k for k in ks if k not in baja and k not in sube])):
    td = [rf[k]["diag_mu_dnti"] + 5 * rf[k]["diag_sd_dnti"] for k in grupo if rf[k].get("diag_sd_dnti") is not None]
    te = [rf[k]["diag_mu_deti"] + 5 * rf[k]["diag_sd_deti"] for k in grupo if rf[k].get("diag_sd_deti") is not None]
    print("   %-9s n=%3d | mu+5sigma dNTI mediana %.4f (sobre C1 en %d) | dETI mediana %.4f (sobre C1 en %d)" %
          (nombre, len(td), st.median(td), sum(x > 0.003 for x in td), st.median(te), sum(x > 0.003 for x in te)))

print("\n#### 4. PARIDAD PAREADA contra MIROVA, pasada por pasada: error = |ln(nuestra / MIROVA)|")


def pareo(grupo, titulo):
    fm, bm, emp = 0, 0, 0
    lb, lf = [], []
    for k in grupo:
        m, _ = mirova_mw(k, por)
        eb, ef = abs(math.log(rb[k]["_disp"] / m)), abs(math.log(rf[k]["_disp"] / m))
        lb.append(rb[k]["_disp"] / m)
        lf.append(rf[k]["_disp"] / m)
        if abs(eb - ef) < 1e-12:
            emp += 1
        elif ef < eb:
            fm += 1
        else:
            bm += 1
    if not grupo:
        return
    print("   %-22s n=%3d | B mas cerca %2d | F mas cerca %2d | iguales %3d | razon mediana B %.3f F %.3f | error mediano B %.3f F %.3f" %
          (titulo, len(grupo), bm, fm, emp, st.median(lb), st.median(lf),
           st.median(abs(math.log(x)) for x in lb), st.median(abs(math.log(x)) for x in lf)))
    return bm, fm


r = pareo(baja, "las que bajan")
pareo(ks, "las 124")
print("   por volcan, solo las que bajan:")
for v in sorted({k[0] for k in baja}):
    pareo([k for k in baja if k[0] == v], "  " + v)
print("   por volcan, las 124:")
for v in sorted({k[0] for k in ks}):
    pareo([k for k in ks if k[0] == v], "  " + v)
print("   por zona del barrido, solo las que bajan:")
for z in ("nadir", "medio", "borde"):
    pareo([k for k in baja if zona(rb[k]["sensor_zenith_deg"]) == z], "  " + z)

if r:
    bm, fm = r
    n = bm + fm
    # prueba del signo exacta, dos colas
    p = sum(math.comb(n, i) for i in range(0, min(bm, fm) + 1)) / 2 ** n * 2
    print("\n   prueba del signo sobre las que bajan (sin empates): B %d contra F %d, p dos colas = %.4f" % (bm, fm, min(1.0, p)))

print("\n#### 5. En las que bajan: B estaba por DEBAJO o por ENCIMA de MIROVA?")
c = collections.Counter()
for k in baja:
    m, _ = mirova_mw(k, por)
    rB, rF = rb[k]["_disp"] / m, rf[k]["_disp"] / m
    c["B bajo MIROVA (F se aleja mas)" if rB <= 1 else ("B sobre, F sigue sobre (F se acerca)" if rF >= 1 else "B sobre, F cruza bajo MIROVA")] += 1
    print("   %-20s %s MIROVA %.3f | B/M %.2f -> F/M %.2f" % (k[0], k[2], m, rB, rF))
print("  ", dict(c))

print("\n#### 6. Bootstrap de la razon mediana nuestra/MIROVA en las 124 (remuestreo de pasadas, 5000)")
random.seed(148)
pares = [(rb[k]["_disp"] / mirova_mw(k, por)[0], rf[k]["_disp"] / mirova_mw(k, por)[0]) for k in ks]
difs = []
for _ in range(5000):
    mu = [random.choice(pares) for _ in pares]
    difs.append(st.median(x[1] for x in mu) - st.median(x[0] for x in mu))
difs.sort()
print("   diferencia de medianas F - B: observado %.3f | IC 95 %% %.3f a %.3f" %
      (st.median(x[1] for x in pares) - st.median(x[0] for x in pares), difs[125], difs[4875]))

print()
print("#### 7. DESCOMPOSICION de la baja: pixeles que dejan de detectarse contra cambio de MW en los pixeles comunes")
print("     (los comunes cambian solo donde el fondo es el kernel local 3x3, que excluye a los alertados:")
print("      PuyehueCordonCaulle, Villarrica, Chaiten, PlanchonPeteroa, Lastarria segun volcanoes.yaml)")
tot = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
for k in baja:
    na, _ = nucleo(rb[k], INNER[k[0]])
    nb, _ = nucleo(rf[k], INNER[k[0]])
    sa, sb = {clave_px(p): p for p in na}, {clave_px(p): p for p in nb}
    perd = sum(p["vrp_mw"] for c, p in sa.items() if c not in sb)
    gan = sum(p["vrp_mw"] for c, p in sb.items() if c not in sa)
    com = sum(sb[c]["vrp_mw"] - sa[c]["vrp_mw"] for c in sa if c in sb)
    for g in (k[0], "TODOS"):
        t = tot[g]
        t[0] += perd; t[1] += gan; t[2] += com; t[3] += 1
for g, t in tot.items():
    print("   %-20s n=%2d | MW que se van con pixeles perdidos %.3f | MW de pixeles nuevos %.3f | cambio en pixeles comunes %+.3f | neto %+.3f" %
          (g, t[3], t[0], t[1], t[2], -t[0] + t[1] + t[2]))
print("   suma publicada B - F en las que bajan: %.3f" % sum(rb[k]["_disp"] - rf[k]["_disp"] for k in baja))
