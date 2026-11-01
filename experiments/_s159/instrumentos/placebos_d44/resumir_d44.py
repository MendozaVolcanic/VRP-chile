# -*- coding: utf-8 -*-
"""Resume los placebos de D-44 (placebo_<a|b|c>_<V>_<tN>.jsonl). Por ventana, placebo y fracción (punto):
  * celdas (semilla x regla x sensor) en que la calibración de P2 corrió (falsos_gana no None), y si el punto VALE como
    control (corrió en más de la mitad de sus celdas);
  * por regla y sensor, la fracción de GANA, PIERDE, EMPATE, BLOQUEA, INDECIDIBLE y SIN SUSTRATO calibrada (y sin
    calibrar), con Wilson al 95 %, sobre las semillas;
  * en (a) y (b), qué dan las celdas calibradas (lo esperado: GANA en a, PIERDE en b);
  * en (c), la media del neto de P2 sobre las semillas con su intervalo (el esperado es 0) y la tasa por cola de GANA y
    PIERDE calibradas sobre todas las celdas del punto, con Wilson (criterio: 5 % o menos por cola); y cuántas veces la
    moneda pidió más de lo que había en el pozo («faltaron»).
Uso: python resumir_d44.py <archivos jsonl...>"""
import collections
import json
import math
import statistics
import sys

CAT = ("GANA", "PIERDE", "EMPATE", "BLOQUEA", "INDECIDIBLE", "SIN SUSTRATO")


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
    return "%d/%d (%.0f %% [%.0f, %.0f])" % (k, n, 100 * k / n if n else 0, 100 * lo, 100 * hi)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    grupos, comp = collections.defaultdict(list), {}
    for f in sys.argv[1:]:
        for l in open(f, encoding="utf-8"):
            x = json.loads(l)
            if "composicion" in x:
                comp[x["ventana"]] = x["composicion"]
                continue
            grupos[(x["ventana"], x["placebo"], x["fraccion"])].append(x)
    print("== COMPOSICIÓN de las publicaciones de K en la tabla del nulo (sin días excluidos), por ventana y sensor")
    for v, c in sorted(comp.items()):
        for s, d in c.items():
            print("   %s %-8s publicadas %4d | alertas bajo 1 MW %4d | negativos limpios %3d (%.1f %% de las publicadas; "
                  "%.1f %% de alertas+negativos) | otras %4d | clase distinta entre reglas %3d | sin publicar: alertas %3d, "
                  "negativos %4d" % (v, s, d["publicadas_K"], d["pub_alerta"], d["pub_negativo"],
                                     100 * d["frac_negativos_entre_publicadas"],
                                     100 * d["frac_negativos_entre_alertas_y_negativos_publicados"], d["pub_otra"],
                                     d["pub_distinta"], d["nopub_alerta"], d["nopub_negativo"]))
    veredictos, acum = [], collections.Counter()
    for (v, pl, f), filas in sorted(grupos.items()):
        ok = [x for x in filas if "caido" not in x]
        n = len(ok)
        claves = sorted({k for x in ok for k in x if k.startswith("P2|")})
        celdas = [(x, k) for x in ok for k in claves]
        corrio = sum(x[k]["falsos_gana"] is not None for x, k in celdas)
        vale = corrio > len(celdas) / 2
        print("\n== %s placebo %s fracción %.2f: %d semillas (%d caídas) | apagadas pedidas %s, en tabla %s | encendidas "
              "pedidas %s, en tabla %s | otras diferencias en la tabla %s | controles OK %s" % (
                  v, pl, f, n, len(filas) - n, sorted({x["apagadas_pedidas"] for x in ok}),
                  sorted({x["apagadas_en_tabla"] for x in ok}), sorted({x["encendidas_pedidas"] for x in ok}),
                  sorted({x["encendidas_en_tabla"] for x in ok}), sorted({x["otras_diferencias_en_tabla"] for x in ok}),
                  sorted({x["controles_ok"] for x in ok})))
        print("   celdas con calibración: %d de %d -> %s | por regla y sensor: %s" % (
            corrio, len(celdas), "VALE" if vale else "NO VALE (sin sustrato en la mayoría)",
            ", ".join("%s %d/%d" % (k[3:], sum(x[k]["falsos_gana"] is not None for x in ok), n) for k in claves)))
        if pl == "c":
            falt = collections.Counter()
            for x in ok:
                falt.update(x.get("simetrico_faltaron", {}))
            print("   simétrico: veces que la moneda pidió más de lo que había en el pozo: %s" % (dict(falt) or "ninguna"))
        tot = collections.Counter()
        tot_cal = collections.Counter()
        for k in claves:
            c = collections.Counter(x[k]["calibrada"] for x in ok)
            u = collections.Counter(x[k]["sin_calibrar"] for x in ok)
            cc = collections.Counter(x[k]["calibrada"] for x in ok if x[k]["falsos_gana"] is not None)
            tot.update(c)
            tot_cal.update(cc)
            print("   %-22s calibrada    %s" % (k, " | ".join("%s %s" % (cat, pct(c[cat], n)) for cat in CAT)))
            print("   %-22s sin calibrar %s" % (k, " | ".join("%s %s" % (cat, pct(u[cat], n)) for cat in CAT[:4])))
            netos = [x[k]["neto"] for x in ok]
            m = statistics.mean(netos)
            sd = statistics.stdev(netos) if n > 1 else 0.0
            print("   %-22s neto D menos K: media %+.2f (IC95 %+.2f a %+.2f) | min %d max %d | discordantes mediana %s, "
                  "noches mediana %s | celdas calibradas: %s" % (
                      k, m, m - 1.96 * sd / math.sqrt(n) if n > 1 else m, m + 1.96 * sd / math.sqrt(n) if n > 1 else m,
                      min(netos), max(netos), sorted(x[k]["n"] for x in ok)[n // 2],
                      sorted(x[k]["noches"] for x in ok)[n // 2], dict(cc)))
        N = len(celdas)
        ncal = sum(tot_cal.values())
        # Las clases del placebo se eligen iguales en las dos reglas, así que original y SN pueden dar lo mismo en cada
        # semilla: entonces las celdas por regla no son independientes y la cuenta honesta es semilla x sensor.
        iguales = all(x["P2|original|%s" % s_]["calibrada"] == x["P2|SN|%s" % s_]["calibrada"]
                      for x in ok for s_ in ("VIIRS375", "VIIRS750"))
        ind = collections.Counter(x["P2|SN|%s" % s_]["calibrada"] for x in ok for s_ in ("VIIRS375", "VIIRS750"))
        ni = 2 * n
        print("   original y SN dan lo mismo en todas las semillas: %s | celdas independientes (semilla x sensor, %d): %s"
              % ("sí" if iguales else "NO", ni, " | ".join("%s %s" % (cat, pct(ind[cat], ni)) for cat in CAT)))
        if pl == "c":
            print("   TODAS LAS CELDAS: GANA %s | PIERDE %s | INDECIDIBLE %s" % (
                pct(tot["GANA"], N), pct(tot["PIERDE"], N), pct(tot["INDECIDIBLE"], N)))
            if vale:
                ok_c = tot["GANA"] <= 0.05 * N and tot["PIERDE"] <= 0.05 * N
                veredictos.append("%s c %.2f: GANA %d y PIERDE %d de %d celdas -> %s | independientes (semilla x sensor): "
                                  "GANA %s, PIERDE %s" % (
                    v, f, tot["GANA"], tot["PIERDE"], N, "CUMPLE (5 % o menos por cola)" if ok_c else "NO CUMPLE",
                    pct(ind["GANA"], ni), pct(ind["PIERDE"], ni)))
                acum["GANA"] += ind["GANA"]; acum["PIERDE"] += ind["PIERDE"]; acum["n"] += ni
        else:
            esperado = "GANA" if pl == "a" else "PIERDE"
            print("   CELDAS CALIBRADAS (%d): %s" % (ncal, " | ".join("%s %s" % (cat, pct(tot_cal[cat], ncal))
                                                                   for cat in CAT if tot_cal[cat])))
            if vale:
                veredictos.append("%s %s %.2f: %s en %d de %d celdas calibradas (%d de %d celdas en total)" % (
                    v, pl, f, esperado, tot_cal[esperado], ncal, tot[esperado], N))
    print("\n== PUNTOS QUE VALEN (calibración en la mayoría de las celdas)")
    for x in veredictos:
        print("   " + x)
    if acum["n"]:
        print("   simétrico, todos los puntos que valen juntos (celdas independientes semilla x sensor): GANA %s | PIERDE %s"
              % (pct(acum["GANA"], acum["n"]), pct(acum["PIERDE"], acum["n"])))


if __name__ == "__main__":
    main()
