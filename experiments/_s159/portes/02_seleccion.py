# -*- coding: utf-8 -*-
"""S159 frente PORTES, paso 2: elige las pasadas del primer lote (tope 300: 150 VIIRS 375 y 150 MODIS, fijado por el
coordinador) y arma objetivos_portes.json, más 10 pasadas de control de VIIRS 750 tomadas del lote del frente N.

POR QUÉ ASÍ. El criterio de victoria (docs/MISSION.md) pesa dos cosas: no perder ninguna alerta protegida y, bajo
1 MW, contar igual una alerta perdida que una publicación de más. Para cada sensor se toman cuatro clases:

  pos_prot   alerta protegida de MIROVA (lectura A, >= 1 MW)              VIIRS 375: muestra; MODIS: censo
  pos_bajo   alerta de MIROVA bajo 1 MW que decide                        VIIRS 375: muestra; MODIS: censo
  neg_pub    negativo limpio que producción (K) publica                    muestra
  neg_resto  negativo limpio que K no publica                              muestra estratificada volcán x cenit

Las muestras son estratificadas por volcán y cenit (<=40, >40) con asignación igual por estrato y peso N/n del
estrato. En VIIRS 375 entran a pos_prot todas las protegidas que K NO publica (lo que el port puede ganar) y el resto
de la clase por sorteo. Días excluidos (coordinador): 2026-10-17 a 2026-10-20. Alertas sólo OCR antes del 2026-06-13
(A119, no deciden) quedan fuera del sorteo.

Grilla del port (experiments/_s159/geo/INFORME.md H1 y H2): centros de celda en X0-25000 : paso : X0+25000.
VIIRS 375: 134 x 134 celdas de 375 m con la esquina UL del TIF de MIROVA (grilla_tif_salida.txt). MODIS: 51 x 51 de
1 km, esquina = la de 375 m + (-312,5, +437,5) (H1, igual en los 11 volcanes). X0, Y0 = esquina de 375 + (25187,5,
-25062,5).
"""
from __future__ import annotations

import collections
import json
import random
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
SEMILLA = 159
EXCLUIDOS = ("2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
TIF = {"NevadosDeChillan": "ChillanNevadosde"}
CUPOS = {"VIIRS375": {"pos_prot": 40, "pos_bajo": 45, "neg_pub": 20, "neg_resto": 45},
         "MODIS": {"pos_prot": None, "pos_bajo": None, "neg_pub": 20, "neg_resto": 38}}   # None = censo
CONTROL_V750 = 10


def grillas():
    g = {}
    txt = (ROOT / "experiments/_s158_d17_diseno/grilla_tif_salida.txt").read_text(encoding="utf-8")
    for ln in txt.splitlines():
        m = re.match(r"(\w+)/\S+: EPSG (\d+), 134x134, celda 375.0 m, origen UL \(([-\d.]+), ([-\d.]+)\), "
                     r"centro \(([-\d.]+), ([-\d.]+)\)", ln)
        if m and m.group(1) not in g:
            ux, uy = float(m.group(3)), float(m.group(4))
            g[m.group(1)] = {"epsg": int(m.group(2)), "centro_lat": float(m.group(5)), "centro_lon": float(m.group(6)),
                             "X0": ux + 25187.5, "Y0": uy - 25062.5,
                             "VIIRS375": {"ul_x": ux, "ul_y": uy, "n": 134, "celda": 375.0},
                             "MODIS": {"ul_x": ux - 312.5, "ul_y": uy + 437.5, "n": 51, "celda": 1000.0},
                             "VIIRS750": {"ul_x": ux - 187.5, "ul_y": uy - 187.5, "n": 67, "celda": 750.0}}
    return g


def muestra_estratificada(lst, n, rng):
    """Asignación igual por estrato volcán x cenit; lo que sobra al estrato más grande. Devuelve (o, peso)."""
    if n >= len(lst):
        return [(o, 1.0) for o in lst]
    est = collections.defaultdict(list)
    for o in lst:
        est[(o["volcan"], o["estrato_z"])].append(o)
    ks = sorted(est)
    base = n // len(ks)
    asign = {k: min(base, len(est[k])) for k in ks}
    resto = n - sum(asign.values())
    while resto > 0:
        movio = False
        for k in sorted(ks, key=lambda k: -(len(est[k]) - asign[k])):
            if resto <= 0:
                break
            if asign[k] < len(est[k]):
                asign[k] += 1
                resto -= 1
                movio = True
        if not movio:
            break
    out = []
    for k in ks:
        if asign[k]:
            for o in rng.sample(est[k], asign[k]):
                out.append((o, len(est[k]) / asign[k]))
    return out


def main():
    d = json.loads((AQUI / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    d = [o for o in d if o["hora_utc"][:10] not in EXCLUIDOS and o["decide"]]
    rng = random.Random(SEMILLA)
    G = grillas()
    elegidos = []
    for b, cupo in CUPOS.items():
        clases = collections.defaultdict(list)
        for o in d:
            if o["b"] != b:
                continue
            if o["lab"] == "pos":
                k = "pos_prot" if o["protegida"] else "pos_bajo"
            else:
                k = "neg_pub" if o["pub_prod"] else "neg_resto"
            clases[k].append(o)
        tam = {k: len(v) for k, v in clases.items()}
        print(f"{b}: tamaños de clase (sin 17 a 20 de octubre, sólo deciden):", tam)
        for k in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"):
            lst = clases[k]
            n = cupo[k]
            if n is None:
                sel = [(o, 1.0) for o in lst]
            elif k == "pos_prot" and b == "VIIRS375":
                nopub = [o for o in lst if not o["pub_prod"]]
                pub = [o for o in lst if o["pub_prod"]]
                sel = [(o, 1.0) for o in nopub] + muestra_estratificada(pub, n - len(nopub), rng)
                # peso de las publicadas: N_estrato / n_estrato dentro de las publicadas
            else:
                sel = muestra_estratificada(lst, n, rng)
            for o, w in sel:
                elegidos.append({**o, "clase": k, "peso": w})
        print(f"  elegidos {b}:", dict(collections.Counter(e["clase"] for e in elegidos if e["b"] == b)),
              "suma de pesos por clase:", {k: round(sum(e["peso"] for e in elegidos if e["b"] == b and e["clase"] == k), 1)
                                         for k in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto")})
    # control V750: 10 pasadas del lote de N con resultado del oráculo (geo_linear) de distinto tipo
    n_obj = json.loads((ROOT / "experiments/_s159/n/objetivos_n.json").read_text(encoding="utf-8"))
    forzadas = {("Lascar", "2026-10-08 05:42"), ("NevadosDeChillan", "2026-10-10 05:54"),
                ("Villarrica", "2026-09-19 05:48")}
    ctl = [o for o in n_obj if (o["volcan"], o["hora_utc"]) in forzadas and o.get("granule")]
    resto = [o for o in n_obj if o.get("granule") and o["clase"] in ("pos_prot", "pos_nopub", "neg_resto")
             and (o["volcan"], o["hora_utc"]) not in forzadas and o["hora_utc"][:10] not in EXCLUIDOS
             and o["hora_utc"][:10] != "2026-10-12"]
    ctl += rng.sample(resto, CONTROL_V750 - len(ctl))
    for o in ctl:
        elegidos.append({"volcan": o["volcan"], "hora_utc": o["hora_utc"], "sensor": o["sensor"], "b": "VIIRS750",
                         "lab": o["lab"], "clase": "control_v750", "peso": 0.0, "granule": o["granule"],
                         "id_n": o["id"], "protegida": o["protegida"], "mirova_vrp": o.get("mirova_vrp"),
                         "pub_prod": o.get("pub_prod"), "decide": False, "partida": False,
                         "mirova": o.get("mirova"), "z": o.get("z"), "estrato_z": o.get("estrato_z")})
    for e in elegidos:
        g = G[TIF.get(e["volcan"], e["volcan"])]
        e["grilla"] = {"epsg": g["epsg"], "centro_lat": g["centro_lat"], "centro_lon": g["centro_lon"],
                       "X0": g["X0"], "Y0": g["Y0"], **g[e["b"]]}
    elegidos.sort(key=lambda e: (e["b"], e["granule"] or "", e["volcan"]))
    for i, e in enumerate(elegidos):
        e["id"] = i
    n375 = sum(e["b"] == "VIIRS375" for e in elegidos)
    nmod = sum(e["b"] == "MODIS" for e in elegidos)
    print(f"total: VIIRS375 {n375}, MODIS {nmod}, control V750 {len(ctl)}; gránulos únicos",
          len({e['granule'] for e in elegidos}))
    print("partidas elegidas:", dict(collections.Counter((e["b"], e["clase"]) for e in elegidos if e.get("partida"))))
    assert n375 <= 150 and nmod <= 150, "se pasó del tope de 300"
    (AQUI / "objetivos_portes.json").write_text(json.dumps(elegidos, ensure_ascii=False, indent=0, default=str),
                                                encoding="utf-8")
    print("escrito objetivos_portes.json")


if __name__ == "__main__":
    main()
