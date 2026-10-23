# -*- coding: utf-8 -*-
"""S161, D-45 §6: resume los placebos de placebo_signos.py (placebo_<a|b|c>_<V>.jsonl) con la regla nueva de P2.

Celda = semilla × sensor. Original y SN se cuentan aparte sólo para comprobar que dan lo mismo (las clases se eligieron
iguales en las dos reglas, como en D-44); si dan lo mismo en todas las filas, la cuenta honesta es semilla × sensor.

Lo que tiene que salir (§6): (a) GANA, (b) PIERDE, donde hay sustrato (B >= 5); (c) falsos de 5 % o menos por cola, con
Wilson. En (c) se informa la tasa sobre TODAS las celdas del punto y sobre las celdas CON SUSTRATO (B >= 5), y además la
tasa ESPERADA exacta: para cada celda, con las magnitudes de sus bloques, la probabilidad exacta bajo el nulo de §2.3
de que la prueba decida GANA (o PIERDE), sumada sobre las celdas (prueba_signos_p2 y regla_signos_p2 reales, 2^B
repartos). La observada tiene que ser compatible con la esperada; la esperada, 5 % o menos por construcción.
También: en cuántas celdas D-45 decide distinto de D-42 y de D-34 sin calibrar (informan), y si las semillas de (a) y
(b) tocaron lo mismo que en D-44 (mismas apagadas pedidas por semilla y fracción).
Uso: python resumir_signos.py <jsonl de signos_p2...> [--d44 <jsonl de placebos_d44...>]
"""
import collections
import itertools
import json
import math
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402

CAT = ("GANA", "PIERDE", "BLOQUEA", "EMPATE", "SIN SUSTRATO", "INDECIDIBLE")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def pct(k, n):
    lo, hi = wilson(k, n)
    return "%d/%d (%.1f %% [%.1f, %.1f])" % (k, n, 100 * k / n if n else 0, 100 * lo, 100 * hi)


_cache = {}


def esperado(sumas):
    """Probabilidad exacta, bajo el nulo de §2.3 (signo de cada bloque al azar), de GANA y de PIERDE con la regla real,
    para un conjunto de bloques con estas magnitudes. Recorre los 2^B repartos de signo."""
    mags = tuple(sorted(abs(x) for x in sumas))
    if mags in _cache:
        return _cache[mags]
    B = len(mags)
    g = p = 0
    for signos in itertools.product((-1, 1), repeat=B):
        s = [a * b for a, b in zip(signos, mags)]
        neto = sum(s)
        v = X.regla_signos_p2(neto, B, X.prueba_signos_p2(s, neto))
        g += v == "GANA"
        p += v == "PIERDE"
    _cache[mags] = (g / 2 ** B, p / 2 ** B)
    return _cache[mags]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    d44 = args[args.index("--d44") + 1:] if "--d44" in args else []
    archivos = args[:args.index("--d44")] if "--d44" in args else args
    grupos = collections.defaultdict(list)
    for f in archivos:
        for l in open(f, encoding="utf-8"):
            x = json.loads(l)
            if "fraccion" in x:
                grupos[(x["ventana"], x["placebo"], x["fraccion"])].append(x)
    ref44 = {}
    for f in d44:
        for l in open(f, encoding="utf-8"):
            x = json.loads(l)
            if "fraccion" in x:
                ref44[(x["ventana"], x["placebo"], x["fraccion"], x["semilla"])] = x
    total_c = collections.Counter()
    for (v, pl, f), filas in sorted(grupos.items()):
        ok = [x for x in filas if "caido" not in x]
        print("\n== %s placebo (%s) %.0f %% | semillas %d (caídas %d) | apagadas pedidas %s | encendidas pedidas %s" % (
            v, pl, 100 * f, len(filas), len(filas) - len(ok), sorted({x["apagadas_pedidas"] for x in ok}),
            sorted({x["encendidas_pedidas"] for x in ok})))
        en_tabla = all(x["apagadas_en_tabla"] == x["apagadas_pedidas"] and x["encendidas_en_tabla"] == x["encendidas_pedidas"]
                       and x["otras_diferencias_en_tabla"] == 0 for x in ok)
        print("   tocadas = en tabla y 0 otras diferencias en todas las semillas: %s" % en_tabla)
        if pl in ("a", "b") and ref44:
            m = [x for x in ok if (v, pl, f, x["semilla"]) in ref44]
            iguales = sum(ref44[(v, pl, f, x["semilla"])]["apagadas_pedidas"] == x["apagadas_pedidas"] and
                          ref44[(v, pl, f, x["semilla"])]["apagadas_por_clase"] == x["apagadas_por_clase"] for x in m)
            print("   mismas apagadas pedidas (y por clase) que D-44 con la misma semilla: %d de %d (D-44 tiene %d de "
                  "estas semillas)" % (iguales, len(ok), len(m)))
        if pl == "c":
            falt = collections.Counter()
            for x in ok:
                falt.update(x["simetrico_faltaron"])
            mag = collections.Counter(n["t"] for x in ok for n in x["simetrico_noches"])
            por_celda = collections.Counter((x["semilla"], n["sensor"]) for x in ok for n in x["simetrico_noches"])
            print("   noches tocadas por celda (noches: celdas): %s | magnitud t de cada noche tocada: %s | faltaron "
                  "(pasadas, suma sobre semillas): %s" % (sorted(collections.Counter(por_celda.values()).items()),
                                                         dict(mag), dict(falt)))
        for sen in X.SENS:
            o = [x["P2|original|%s" % sen] for x in ok]
            sn = [x["P2|SN|%s" % sen] for x in ok]
            iguales = sum(a == b for a, b in zip(o, sn))
            c = collections.Counter(a["veredicto"] for a in sn)
            c42 = collections.Counter(a["d42"] for a in sn)
            c34 = collections.Counter(a["d34"] for a in sn)
            dist42 = sum(a["veredicto"] != a["d42"] for a in sn)
            con = [a for a in sn if a["B"] > X.MAX_B_SIN_SUSTRATO_P2]
            print("   %-8s original = SN en %d de %d | B %s | D-45: %s" % (
                sen, iguales, len(ok), sorted(collections.Counter(a["B"] for a in sn).items()),
                ", ".join("%s %d" % (k, c[k]) for k in CAT if c[k])))
            print("            informan: D-42 %s | D-34 sin calibrar %s | D-45 distinto de D-42 en %d de %d" % (
                ", ".join("%s %d" % (k, c42[k]) for k in CAT if c42[k]),
                ", ".join("%s %d" % (k, c34[k]) for k in CAT if c34[k]), dist42, len(sn)))
            if pl == "a" and con:
                print("            (a) con sustrato: GANA %s; dirección equivocada (PIERDE o BLOQUEA) %d" % (
                    pct(sum(a["veredicto"] == "GANA" for a in con), len(con)),
                    sum(a["veredicto"] in ("PIERDE", "BLOQUEA") for a in con)))
            if pl == "b" and con:
                print("            (b) con sustrato: PIERDE %s; dirección equivocada (GANA) %d" % (
                    pct(sum(a["veredicto"] == "PIERDE" for a in con), len(con)), sum(a["veredicto"] == "GANA" for a in con)))
            if pl == "c":
                g, p = sum(a["veredicto"] == "GANA" for a in sn), sum(a["veredicto"] == "PIERDE" for a in sn)
                gc, pc = sum(a["veredicto"] == "GANA" for a in con), sum(a["veredicto"] == "PIERDE" for a in con)
                eg = sum(esperado(a["sumas_bloque"])[0] for a in con)
                ep = sum(esperado(a["sumas_bloque"])[1] for a in con)
                netos = [a["neto"] for a in sn]
                sd = statistics.pstdev(netos) if len(netos) > 1 else 0.0
                print("            (c) todas las celdas: GANA %s, PIERDE %s | con sustrato: GANA %s, PIERDE %s | "
                      "esperado exacto con sustrato: GANA %.2f, PIERDE %.2f de %d (%.1f y %.1f %%) | neto medio %+.2f "
                      "(desvío %.2f)" % (pct(g, len(sn)), pct(p, len(sn)), pct(gc, len(con)), pct(pc, len(con)), eg, ep,
                                         len(con), 100 * eg / len(con) if con else 0, 100 * ep / len(con) if con else 0,
                                         statistics.mean(netos), sd))
                total_c.update({"celdas": len(sn), "con": len(con), "g": g, "p": p, "gc": gc, "pc": pc})
                total_c["eg"] += eg
                total_c["ep"] += ep
    if total_c:
        t = total_c
        print("\n== (c) TOTAL sobre todos los puntos (celdas semilla x sensor): GANA %s, PIERDE %s | con sustrato: GANA %s, "
              "PIERDE %s | esperado exacto con sustrato GANA %.1f %%, PIERDE %.1f %%" % (
                  pct(t["g"], t["celdas"]), pct(t["p"], t["celdas"]), pct(t["gc"], t["con"]), pct(t["pc"], t["con"]),
                  100 * t["eg"] / t["con"], 100 * t["ep"] / t["con"]))


if __name__ == "__main__":
    main()
