# -*- coding: utf-8 -*-
"""S165: el cotejo con la Distancia_km de MIROVA separado por configuración de la escena. Sólo lectura.

POR QUÉ. Las pasadas donde las dos reglas dan distancias distintas son de dos clases físicas: (a) un cúmulo en el
cráter con un borde más cercano que su centro (las dos reglas caen dentro del inner_radius: no cambia la publicación) y
(b) un píxel débil cerca del cráter y una fuente más radiante lejos (una regla cae dentro y la otra fuera: cambia la
publicación). El conteo agregado de modis.py, v750.py y v375.py está dominado por (a), y la pregunta de Nicolás es
sobre (b). Lee los JSON que dejaron esos tres scripts en D:\\vrp-trabajo\\temporales\\s165_regla_posicion.
Uso: python cotejo_por_configuracion.py  (escribe cotejo_por_configuracion_salida.txt)
"""
import collections
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import comun as C  # noqa: E402

V = C.volcanes()
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


for sensor in ("modis", "v750", "v375"):
    d = json.loads((C.TEMP / f"{sensor}.json").read_text(encoding="utf-8"))
    pr(f"\n== {sensor}")
    for par, canales in d["cotejo"].items():
        a, b = par.split("|")
        if par == "pico_ref|cerc_ref":
            continue
        for canal, filas in canales.items():
            grupos = collections.defaultdict(list)
            for x in filas:
                inner = V[x["volcan"]]["inner_radius_km"]
                cruza = (x[a] <= inner) != (x[b] <= inner)
                grupos["(b) una regla dentro del inner y la otra fuera" if cruza else
                       "(a) las dos del mismo lado del inner"].append(x)
            for g in sorted(grupos):
                c = collections.Counter(x["gana"] for x in grupos[g])
                pr(f"   {a} contra {b} | {canal} | {g}: {len(grupos[g])} filas | más cerca de MIROVA: {a} {c[a]}, "
                   f"{b} {c[b]}, empate {c['empate']}")
                if g.startswith("(b)"):
                    for x in grupos[g]:
                        pr(f"      {x['volcan']} {x['hora']} clase {x['clase']} | {x['tipo']} {x['vrp_mirova']} MW a "
                           f"{x['dist_mirova']} km | {a} {x[a]} km, {b} {x[b]} km | inner "
                           f"{V[x['volcan']]['inner_radius_km']} | gana {x['gana']}")
(C.AQUI / "cotejo_por_configuracion_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
