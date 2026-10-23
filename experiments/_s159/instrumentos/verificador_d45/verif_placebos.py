# -*- coding: utf-8 -*-
"""Verificador de D-45: recuento PROPIO de los placebos de signos_p2 (placebo_<a|b|c>_<V>.jsonl), sin pasar por
resumir_signos.py, y re-decision desde las sumas de bloque guardadas con una enumeracion propia (no la del evaluador).

Pregunta 1: si el implementador hubiera contado mal (otra unidad, celdas duplicadas, semillas repetidas o ampliadas,
corridas caidas contadas), este recuento daria otro numero. Pregunta 2: si el JSONL no trajera los campos, el script
revienta en vez de dar cero.
"""
import collections
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SP2 = AQUI.parent / "signos_p2"
SENS = ("VIIRS375", "VIIRS750")


def redecidir(sumas, neto):
    """Regla de la adenda §2.4 a §2.7 escrita de nuevo aqui, solo para B <= 20 (exacto). None si B > 20."""
    B = len(sumas)
    if B <= 4:
        return "SIN SUSTRATO"
    if B > 20:
        return None
    le = ge = 0
    for signos in itertools.product((-1, 1), repeat=B):
        t = sum(s * x for s, x in zip(signos, sumas))
        le += t <= neto
        ge += t >= neto
    den = 2 ** B
    if neto < 0 and 20 * le <= den:
        return "GANA"
    if neto > 0 and 20 * ge <= den:
        return "PIERDE"
    return "BLOQUEA" if neto > 0 else "EMPATE"


filas = []
comp = []
for f in sorted(SP2.glob("placebo_*_V*.jsonl")):
    for l in open(f, encoding="utf-8"):
        x = json.loads(l)
        if "fraccion" in x:
            x["_archivo"] = f.name
            filas.append(x)
        else:
            comp.append((f.name, x))
print("archivos:", sorted({x["_archivo"] for x in filas}))
print("filas con fraccion:", len(filas), "| caidas:", sum("caido" in x for x in filas))
dup = collections.Counter((x["ventana"], x["placebo"], x["fraccion"], x["semilla"]) for x in filas)
print("celdas (ventana, placebo, fraccion, semilla) repetidas:", {k: v for k, v in dup.items() if v > 1} or "ninguna")
por = collections.defaultdict(list)
for x in filas:
    por[(x["ventana"], x["placebo"], x["fraccion"])].append(x)
print("\nsemillas por punto:")
for k in sorted(por):
    sem = sorted(x["semilla"] for x in por[k])
    print("  %s: n=%d semillas %s..%s contiguas=%s" % (k, len(sem), sem[0], sem[-1], sem == list(range(len(sem)))))

# recuento propio (sobre la regla SN, como resumir; y sobre original, para ver que coinciden)
tot = collections.Counter()
mal_redec = 0; redec = 0; no_redec = 0
por_celda = collections.defaultdict(collections.Counter)
distinto_orig_sn = 0
caidas = [x for x in filas if "caido" in x]
for x in caidas:
    print("   CAIDA (no cuenta):", x["ventana"], x["placebo"], x["fraccion"], x["semilla"], " ".join(str(x["caido"])[:160].split()))
filas = [x for x in filas if "caido" not in x]
print("filas completas que cuentan:", len(filas))
for x in filas:
    for s in SENS:
        a = x["P2|SN|%s" % s]; o = x["P2|original|%s" % s]
        if a["veredicto"] != o["veredicto"]:
            distinto_orig_sn += 1
        v = a["veredicto"]
        por_celda[(x["ventana"], x["placebo"], x["fraccion"], s)][v] += 1
        por_celda[(x["ventana"], x["placebo"], x["fraccion"], s)]["_B>=5"] += a["B"] >= 5
        if x["placebo"] == "c":
            tot["celdas_c"] += 1
            tot["c_GANA"] += v == "GANA"
            tot["c_PIERDE"] += v == "PIERDE"
            tot["c_B<=4"] += a["B"] <= 4
        # re-decidir desde las sumas guardadas con mi enumeracion
        r = redecidir(a["sumas_bloque"], a["neto"])
        if r is None:
            no_redec += 1
        else:
            redec += 1
            if r != v:
                mal_redec += 1
                print("   RE-DECISION DISTINTA", x["ventana"], x["placebo"], x["fraccion"], x["semilla"], s, v, r, a["sumas_bloque"])
        # coherencia: neto = suma de sumas; B = len(sumas); metodo segun B
        assert a["neto"] == sum(a["sumas_bloque"]), (x["semilla"], s)
        assert a["B"] == len(a["sumas_bloque"]), (x["semilla"], s)
        assert a["metodo"] == ("exacto" if a["B"] <= 20 else "sorteos"), (x["semilla"], s, a["B"], a["metodo"])
        if a["metodo"] == "sorteos":
            assert (a["semilla_signos"], a["n_sorteos_signos"]) == (162, 10000) and a["p_gana"][1] == 10001, a
        else:
            assert a["semilla_signos"] is None and a["p_gana"][1] == 2 ** a["B"], a
print("\noriginal distinto de SN en celdas:", distinto_orig_sn)
print("re-decididas con enumeracion propia (B<=20):", redec, "| distintas:", mal_redec, "| no re-decidibles (B>20, sorteos):", no_redec)
print("\n(c) TOTAL celdas semilla x sensor: %d | GANA %d (%.2f %%) | PIERDE %d (%.2f %%) | celdas con B<=4: %d" % (
    tot["celdas_c"], tot["c_GANA"], 100 * tot["c_GANA"] / tot["celdas_c"], tot["c_PIERDE"], 100 * tot["c_PIERDE"] / tot["celdas_c"], tot["c_B<=4"]))
print("\n(a) y (b): por celda (ventana, fraccion, sensor): veredictos y celdas con sustrato")
for k in sorted(por_celda):
    if k[1] in ("a", "b"):
        c = por_celda[k]
        con = c["_B>=5"]
        esperado = "GANA" if k[1] == "a" else "PIERDE"
        n_esp = c[esperado]
        flag = "" if (con == 0 or n_esp == con) else "  <-- NO TODAS"
        print("  %s: %s | con sustrato %d | %s %d%s" % (k, {a: b for a, b in c.items() if not a.startswith("_")}, con, esperado, n_esp, flag))
print("\n(c): por celda")
for k in sorted(por_celda):
    if k[1] == "c":
        c = por_celda[k]
        print("  %s: GANA %d PIERDE %d de %d" % (k, c["GANA"], c["PIERDE"], sum(v for a, v in c.items() if not a.startswith("_"))))
# ventana temporal de los datos: de la composicion
print("\ncomposicion (primera linea por archivo):")
for n, c in comp:
    print("  ", n, {k: v for k, v in c.items() if k != "composicion"})
# en (c): el signo comun por noche se respeta en las noches tocadas; magnitud t
t_mag = collections.Counter(); signos_por_noche_mixtos = 0
for x in filas:
    if x["placebo"] != "c":
        continue
    vistos = {}
    for n in x["simetrico_noches"]:
        t_mag[n["t"]] += 1
        kk = (n["sensor"], n["noche"])
        if kk in vistos and vistos[kk] != n["signo"]:
            signos_por_noche_mixtos += 1
        vistos[kk] = n["signo"]
print("(c) magnitud t de las noches tocadas:", dict(t_mag), "| noches con signos mixtos dentro del mismo sensor:", signos_por_noche_mixtos)
print("(c) tocadas = en tabla en todas las filas:", all(x["apagadas_en_tabla"] == x["apagadas_pedidas"] and x["encendidas_en_tabla"] == x["encendidas_pedidas"]
                                                     and x["otras_diferencias_en_tabla"] == 0 for x in filas if "caido" not in x))
