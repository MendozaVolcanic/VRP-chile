# -*- coding: utf-8 -*-
"""S159, censo del oráculo en VIIRS 750, paso 1: lista de objetivos (TODAS las pasadas de la población del frente N).

POR QUÉ UN CENSO. El oráculo (código entero de MIROVA en la grilla de GEO) cambia la detección, así que, a diferencia
del brazo F, no tiene techo por censo parcial: puede encender un negativo donde producción no tiene ni un píxel. La
única forma de saber cuántos negativos limpios publica es correrlo en todos (verificador del frente N, afirmación 3).

Población: experiments/_s159/n/poblacion_completa.json (VIIRS 750 nocturno, 2026-04-01 a 2026-10-21, pareo a 120 s,
regla D-9 SN, lectura A de protegidas, records de origin/main 533398f8f), sin el 2026-10-18 ni el 19 (CMR no los
sirve). Se toman los 5.476 negativos limpios y las 270 alertas (256 deciden, 14 sólo OCR antes del 13 de junio).
Grilla del oráculo: la misma de experiments/_s159/n/02_seleccion.py (esquina de GEO).

Además mide el desfase entre el centro de la grilla (centro del TIF de MIROVA, desde donde el record sintético del
oráculo mide la distancia) y la coordenada del volcán en volcanoes.yaml.
Uso: python 01_objetivos.py
"""
import collections
import importlib.util
import json
import math
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
N = RAIZ / "experiments/_s159/n"
spec = importlib.util.spec_from_file_location("sel", N / "02_seleccion.py")
SEL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SEL)


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def main():
    pob = [p for p in json.loads((N / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
           if p["hora_utc"][:10] not in SEL.EXCLUIDOS]
    G = SEL.grillas()
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    # pasadas que N ya midió (control 2): lote y censo
    medidas_n = set()
    for f in ("objetivos_n.json", "objetivos_censo.json"):
        for o in json.loads((N / f).read_text(encoding="utf-8")):
            medidas_n.add((o["volcan"], o["hora_utc"]))
    out = []
    for p in pob:
        g = G[SEL.TIF.get(p["volcan"], p["volcan"])]
        out.append({**p, "grilla": g, "en_n": (p["volcan"], p["hora_utc"]) in medidas_n})
    out.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for n, e in enumerate(out):
        e["id"] = n
    c = collections.Counter(e["lab"] for e in out)
    print("pasadas:", len(out), dict(c), "| granulos unicos", len({e["granule"] for e in out}),
          "| sin granulo", sum(1 for e in out if not e["granule"]), "| ya medidas por N", sum(e["en_n"] for e in out))
    print("alertas: deciden", sum(1 for e in out if e["lab"] == "pos" and e["decide"]),
          "| protegidas que deciden", sum(1 for e in out if e["lab"] == "pos" and e["decide"] and e["protegida"]))
    assert c["neg_limpio"] == 5476, "no reproduce los 5.476 negativos del frente N"
    print("desfase centro de grilla (TIF) contra volcanoes.yaml, km:")
    for v in sorted({e["volcan"] for e in out}):
        g = G[SEL.TIF.get(v, v)]
        print(f"   {v:22s} {hav(g['centro_lat'], g['centro_lon'], vy[v]['lat'], vy[v]['lon']):.3f}"
              f"  inner {vy[v].get('inner_radius_km')}")
    (AQUI / "objetivos.json").write_text(json.dumps(out, ensure_ascii=False, default=str), encoding="utf-8")
    print("escrito objetivos.json")


if __name__ == "__main__":
    main()
