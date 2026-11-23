# -*- coding: utf-8 -*-
"""Medición previa del ítem P0 del plan S196, parte de la publicación múltiple: ¿cuántas pasadas ya traen más de un foco?

POR QUÉ. La réplica publica una sola posición por pasada (el cúmulo de la alertada más radiante, regla «radiante», D8')
aunque sume la potencia de todos los alertados (D32). Si en la misma pasada hay un segundo cúmulo lejos del primero, el
tablero lo esconde dentro de la suma y en la posición del otro. Antes de diseñar una serie por cúmulo hay que saber
cuántas pasadas tienen un segundo cúmulo, a qué distancia del principal y si el principal es la anomalía conocida
(dentro del radio del cráter) y el segundo está fuera, que es justo el caso que preocupa a Nicolás.

Qué hace, sin reprocesar: con `anomaly_pixels` de cada record nocturno de la vía (fila y columna en la grilla del
sensor; hasta 100 por record, el tope del almacén) arma los cúmulos 8-conexos, toma como principal el que contiene al
píxel de mayor `bt_k` (la BT de MIR: lo más cercano a la regla «radiante» que el píxel guardado permite; el píxel no
guarda su propia potencia), y cuenta las pasadas con algún otro cúmulo cuyo centroide quede a 3 km o más del centroide del principal. 11 Tier A,
2026-03-01 a 2026-11-22.

Uso: python experiments/_s196_plan_mejoras/m0b_cumulos_multiples.py
"""
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402

DESDE, HASTA = "2026-03-01", "2026-11-22"
SEPARACION_KM = 3.0


def cumulos(pix):
    idx = {(p["fila"], p["col"]): i for i, p in enumerate(pix)}
    visto, out = set(), []
    for k in idx:
        if k in visto:
            continue
        pila, comp = [k], []
        visto.add(k)
        while pila:
            f, c = pila.pop()
            comp.append(idx[(f, c)])
            for df in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    v = (f + df, c + dc)
                    if v in idx and v not in visto:
                        visto.add(v)
                        pila.append(v)
        out.append([pix[i] for i in comp])
    return out


def centroide(c):
    return sum(p["lat"] for p in c) / len(c), sum(p["lon"] for p in c) / len(c)


def main():
    import yaml
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    inner = bp.inner_desde_html()
    print("records nocturnos de la vía con alertados, %s a %s; segundo cúmulo = otro cúmulo 8-conexo a >= %.0f km del "
          "principal (el que tiene el píxel de mayor BT de MIR)" % (DESDE, HASTA, SEPARACION_KM))
    print("%-20s %7s %8s %12s %22s %16s" % ("volcán", "con_det", "2+cúm", "segundo>=3km", "principal cráter y", "segundo: píxeles, BT máx"))
    print("%-20s %7s %8s %12s %22s %16s" % ("", "", "", "", "segundo fuera", "(medianas) / BT princ."))
    for vol in bp.VOLS:
        v = vy[vol]
        vlat, vlon = v.get("vent_lat") or v["lat"], v.get("vent_lon") or v["lon"]
        n = n2 = nsep = ncaso = 0
        mw = []
        for r in json.loads((bp.DATA / ("%s.json" % vol)).read_text(encoding="utf-8"))["records"]:
            if not r.get("via_codigo_mirova") or not (DESDE <= r.get("datetime_utc", "")[:10] <= HASTA):
                continue
            if (r.get("diag_codigo_mirova") or {}).get("dayflag") != 0:
                continue
            pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("fila") is not None and p.get("lat") is not None]
            if not pix:
                continue
            n += 1
            cs = cumulos(pix)
            if len(cs) < 2:
                continue
            n2 += 1
            princ = max(cs, key=lambda c: max((p.get("bt_k") or 0) for p in c))
            pc = centroide(princ)
            otros = [c for c in cs if c is not princ and bp._hav_km(*centroide(c), *pc) >= SEPARACION_KM]
            if not otros:
                continue
            nsep += 1
            dprinc = bp._hav_km(*pc, vlat, vlon)
            fuera = [c for c in otros if bp._hav_km(*centroide(c), vlat, vlon) > inner[vol]]
            if dprinc <= inner[vol] and fuera:
                ncaso += 1
                seg = max(fuera, key=lambda c: max((p.get("bt_k") or 0) for p in c))
                mw.append((len(seg), max(p["bt_k"] for p in seg), max(p["bt_k"] for p in princ)))
        import statistics
        txt = ("%d px, %.1f K / %.1f K" % (statistics.median(x[0] for x in mw), statistics.median(x[1] for x in mw),
                                           statistics.median(x[2] for x in mw))) if mw else "-"
        print("%-20s %7d %8d %12d %22d   %s" % (vol, n, n2, nsep, ncaso, txt))


if __name__ == "__main__":
    main()
