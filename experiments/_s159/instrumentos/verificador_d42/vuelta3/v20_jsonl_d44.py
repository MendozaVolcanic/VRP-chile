# -*- coding: utf-8 -*-
"""Verificador D-42, vuelta 3: lectura propia de los JSONL de placebos_d44/ (no del resumen del implementador).

Por archivo y punto (ventana, placebo, fraccion): corridas, caidas, semillas (rango, para ver tandas agregadas),
pasadas tocadas contra las que llegaron a la tabla y otras diferencias; celdas (semilla x regla x sensor) en que la
calibracion corrio; veredictos calibrados y sin calibrar; en (c): n contra noches (cuantas celdas tienen mas de una
discordante en alguna noche: donde el nulo «signo por pasada» difiere del nulo «signo por bloque»), media del neto y
GANA/PIERDE por cola, por tanda (semillas 0..19 aparte de las agregadas) y en total; en INDECIDIBLE: por que fallo
(falsos_gana o falsos_pierde sobre 0,05) y con cuantas noches.

Pregunta 1 (¿veria un placebo que no toca nada?): si: apagadas/encendidas en tabla contra pedidas. Pregunta 2 (¿veria
un instrumento muerto?): el total de corridas tiene que ser el que dicen (444) y cada fila tener sus 4 celdas.
Uso: python v20_jsonl_d44.py
"""
import collections
import glob
import json
import math
import statistics
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
D44 = AQUI.parents[1] / "placebos_d44"
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
    return "%d/%d (%.1f %% [%.1f, %.1f])" % (k, n, 100 * k / n if n else 0, 100 * lo, 100 * hi)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    archivos = sorted(glob.glob(str(D44 / "placebo_*.jsonl")))
    total = caidas = 0
    comp = {}
    grupos = collections.defaultdict(list)
    for f in archivos:
        for l in open(f, encoding="utf-8"):
            if not l.strip():
                continue
            x = json.loads(l)
            if "composicion" in x:
                comp.setdefault(x["ventana"], []).append((Path(f).name, x["composicion"]))
                continue
            total += 1
            caidas += "caido" in x
            x["_archivo"] = Path(f).name
            grupos[(x["ventana"], x["placebo"], x["fraccion"])].append(x)
    print("== archivos %d | corridas (filas sin 'composicion') %d | caidas %d" % (len(archivos), total, caidas))
    print("== composicion de las publicaciones de K (tabla del nulo), tal como la escribio cada corrida:")
    for v, lst in sorted(comp.items()):
        vistos = set()
        for nombre, c in lst:
            clave = json.dumps(c, sort_keys=True)
            if clave in vistos:
                continue
            vistos.add(clave)
            for s, d in c.items():
                print("   %s %-9s publicadas %4d: alertas %4d, negativos %3d (%.1f %% de publicadas), otras %3d, distinta %3d | "
                      "sin publicar: alertas %3d, negativos %4d   [%s]" % (
                          v, s, d["publicadas_K"], d["pub_alerta"], d["pub_negativo"], 100 * d["frac_negativos_entre_publicadas"],
                          d["pub_otra"], d["pub_distinta"], d["nopub_alerta"], d["nopub_negativo"], nombre))
        print("   (%s: %d corridas escribieron composicion, %d distintas)" % (v, len(lst), len(vistos)))
    for (v, pl, f), filas in sorted(grupos.items()):
        ok = [x for x in filas if "caido" not in x]
        sem = sorted(x["semilla"] for x in ok)
        archs = sorted({x["_archivo"] for x in ok})
        claves = sorted({k for x in ok for k in x if k.startswith("P2|")})
        assert all(len([k for k in x if k.startswith("P2|")]) == 4 for x in ok), "fila sin 4 celdas"
        toc_ok = all(x["apagadas_en_tabla"] == x["apagadas_pedidas"] and x["encendidas_en_tabla"] == x["encendidas_pedidas"]
                     and x["otras_diferencias_en_tabla"] == 0 for x in ok)
        print("\n== %s placebo %s f=%.2f | %d corridas, %d caidas | semillas %d..%d (%d distintas) | archivos %s" % (
            v, pl, f, len(ok), len(filas) - len(ok), sem[0], sem[-1], len(set(sem)), archs))
        print("   tocadas = en tabla y otras diferencias 0 en TODAS las semillas: %s | apagadas %s | encendidas %s | otras %s" % (
            toc_ok, sorted({x["apagadas_pedidas"] for x in ok}), sorted({x["encendidas_pedidas"] for x in ok}),
            sorted({x["otras_diferencias_en_tabla"] for x in ok})))
        if pl == "c":
            falt = collections.Counter()
            for x in ok:
                falt.update(x.get("simetrico_faltaron", {}))
            print("   simetrico faltaron (acumulado): %s" % (dict(falt) or "ninguna"))
        for k in claves:
            cel = [x[k] for x in ok]
            corrio = sum(c["falsos_gana"] is not None for c in cel)
            cal = collections.Counter(c["calibrada"] for c in cel)
            sin = collections.Counter(c["sin_calibrar"] for c in cel)
            ind = [c for c in cel if c["calibrada"] == "INDECIDIBLE"]
            motivos = collections.Counter(("GANA>5%" if c["falsos_gana"] > 0.05 else "") + ("PIERDE>5%" if c["falsos_pierde"] > 0.05 else "")
                                          for c in ind if c["falsos_gana"] is not None)
            noches_ind = sorted(c["noches"] for c in ind)
            multi = sum(c["n"] > c["noches"] for c in cel)
            netos = [c["neto"] for c in cel]
            m = statistics.mean(netos); sd = statistics.stdev(netos) if len(netos) > 1 else 0.0
            print("   %-22s calibro %2d/%2d | calibrada %s | sin calibrar GANA %d PIERDE %d | neto media %+.2f [%+.2f, %+.2f] | "
                  "n>noches en %d celdas | INDECIDIBLE: motivos %s, noches %s" % (
                      k, corrio, len(cel), " ".join("%s %d" % (c_, cal[c_]) for c_ in CAT if cal[c_]), sin["GANA"], sin["PIERDE"],
                      m, m - 1.96 * sd / math.sqrt(len(netos)), m + 1.96 * sd / math.sqrt(len(netos)), multi,
                      dict(motivos), noches_ind[:12]))
        if pl == "c":
            for tanda, sel in (("semillas 0..19", [x for x in ok if x["semilla"] < 20]), ("semillas 20..", [x for x in ok if x["semilla"] >= 20])):
                if not sel:
                    continue
                c_ = collections.Counter(x[k]["calibrada"] for x in sel for k in claves)
                N = 4 * len(sel)
                print("   (c) %-14s %3d corridas, %3d celdas: GANA %s | PIERDE %s | INDECIDIBLE %s" % (
                    tanda, len(sel), N, pct(c_["GANA"], N), pct(c_["PIERDE"], N), pct(c_["INDECIDIBLE"], N)))


if __name__ == "__main__":
    main()
