# -*- coding: utf-8 -*-
"""S159 frente N, paso 2: elige las pasadas del primer lote (tope 400, aprobado por Nicolás) y arma objetivos_n.json.

POR QUÉ ASÍ. El criterio de victoria (docs/MISSION.md) pesa dos cosas: no perder ninguna alerta protegida y, bajo
1 MW, contar igual una alerta perdida que una publicación de más. Las pasadas donde un brazo puede cambiar algo
respecto de producción (K) son de cuatro clases, y cada una se toma ENTERA (censo) o por muestra con su peso:

  pos_nopub   alertas de MIROVA que K no publica (lo que un brazo puede ganar)        censo
  pos_prot    alertas protegidas que K sí publica (lo que un brazo puede perder)     censo
  pos_resto   alertas bajo 1 MW que K publica (puede perder o cambiar magnitud)       muestra aleatoria
  neg_pub     negativos limpios que K publica (lo que un brazo puede apagar)          censo
  neg_resto   negativos limpios que K no publica (lo que un brazo puede encender)     muestra estratificada por
                                                                                      volcán y cenit (<=40, >40)
Además: las pasadas del bloque R2 (experiments/_s158_audit_r2/granulos/objetivos.json) que CMR todavía sirve, y las
dos alertas protegidas diurnas de Chillán (estrato diurno, sólo oráculo con la rama de día del código).

Días excluidos de las muestras (declarado): 2026-10-18 y 2026-10-19, que CMR no sirve hoy (COB, R2-13). El 17 y el
20 entran y, si una pasada no baja, queda SIN DATO por pasada.

Grilla del oráculo: la de 750 m de MIROVA según GEO (experiments/_s159/geo/INFORME.md H1): esquina de la de 375 m
menos 187,5 m en x y en y. Se guarda también la esquina vieja de R2 (la de 375 m) para la variante de comparación.
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
TOPE = 400
EXCLUIDOS = ("2026-10-18", "2026-10-19")
N_POS_RESTO = 36       # se ajusta abajo para que el total quepa en el tope
TIF = {"NevadosDeChillan": "ChillanNevadosde"}


def grillas():
    g = {}
    txt = (ROOT / "experiments/_s158_d17_diseno/grilla_tif_salida.txt").read_text(encoding="utf-8")
    for ln in txt.splitlines():
        m = re.match(r"(\w+)/\S+: EPSG (\d+), 134x134, celda 375.0 m, origen UL \(([-\d.]+), ([-\d.]+)\), "
                     r"centro \(([-\d.]+), ([-\d.]+)\)", ln)
        if m and m.group(1) not in g:
            ux, uy = float(m.group(3)), float(m.group(4))
            g[m.group(1)] = {"epsg": int(m.group(2)), "ul_x": ux - 187.5, "ul_y": uy - 187.5,
                             "ul_x_r2": ux, "ul_y_r2": uy,
                             "centro_lat": float(m.group(5)), "centro_lon": float(m.group(6))}
    return g


def main():
    d = json.loads((AQUI / "poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    d = [o for o in d if o["hora_utc"][:10] not in EXCLUIDOS]
    rng = random.Random(SEMILLA)
    G = grillas()
    clases = collections.defaultdict(list)
    for o in d:
        if o["lab"] == "pos":
            k = "pos_nopub" if not o["pub_prod"] else ("pos_prot" if o["protegida"] else "pos_resto")
        else:
            k = "neg_pub" if o["pub_prod"] else "neg_resto"
        clases[k].append(o)
    tam = {k: len(v) for k, v in clases.items()}
    print("tamaños de clase (sin 10-18 y 10-19):", tam)

    r2 = json.loads((ROOT / "experiments/_s158_audit_r2/granulos/objetivos.json").read_text(encoding="utf-8"))
    r2 = [o for o in r2 if o["hora_utc"][:10] not in EXCLUIDOS]
    clave = lambda v, h: (v, h)
    en_pob = {clave(o["volcan"], o["hora_utc"]): o for o in d}
    r2_extra = [o for o in r2 if clave(o["volcan"], o["hora_utc"]) not in en_pob]
    diurnas = [  # rb/06 de R2: protegidas diurnas de Chillán; la del 10-18 no la sirve CMR
        {"volcan": "NevadosDeChillan", "hora_utc": "2026-10-01 18:42", "mirova_vrp": 3.71},
        {"volcan": "NevadosDeChillan", "hora_utc": "2026-10-10 18:18", "mirova_vrp": 3.33},
    ]
    censo = len(clases["pos_nopub"]) + len(clases["pos_prot"]) + len(clases["neg_pub"])
    fijos = len(r2_extra) + len(diurnas)
    # pos y neg en igual número: n_pos = nopub + prot + resto; n_neg = neg_pub + neg_resto
    libre = TOPE - censo - fijos
    n_pos_resto = min(N_POS_RESTO, tam.get("pos_resto", 0))
    n_pos = len(clases["pos_nopub"]) + len(clases["pos_prot"]) + n_pos_resto
    n_neg_resto = n_pos - len(clases["neg_pub"])
    while n_pos_resto + n_neg_resto > libre:
        n_pos_resto -= 1
        n_neg_resto -= 1
    print(f"censo {censo}, fijos {fijos} (R2 fuera de la población {len(r2_extra)}, diurnas {len(diurnas)}); "
          f"pos_resto {n_pos_resto} de {tam.get('pos_resto')}, neg_resto {n_neg_resto} de {tam.get('neg_resto')}")

    elegidos = []
    for k in ("pos_nopub", "pos_prot", "neg_pub"):
        for o in clases[k]:
            elegidos.append({**o, "clase": k, "peso": 1.0})
    m = rng.sample(clases["pos_resto"], n_pos_resto)
    for o in m:
        elegidos.append({**o, "clase": "pos_resto", "peso": tam["pos_resto"] / n_pos_resto})
    # neg_resto: estratificado por volcán y cenit, asignación igual por estrato (lo que sobre, al más grande)
    est = collections.defaultdict(list)
    for o in clases["neg_resto"]:
        est[(o["volcan"], o["estrato_z"])].append(o)
    ks = sorted(est)
    base = n_neg_resto // len(ks)
    asign = {k: min(base, len(est[k])) for k in ks}
    resto = n_neg_resto - sum(asign.values())
    for k in sorted(ks, key=lambda k: -len(est[k])):
        if resto <= 0:
            break
        if asign[k] < len(est[k]):
            asign[k] += 1
            resto -= 1
    for k in ks:
        for o in rng.sample(est[k], asign[k]):
            elegidos.append({**o, "clase": "neg_resto", "peso": len(est[k]) / asign[k]})
    # R2 en la población: marcar
    sel = {clave(o["volcan"], o["hora_utc"]) for o in elegidos}
    forzados_r2 = 0
    for o in r2:
        c = clave(o["volcan"], o["hora_utc"])
        if c in en_pob and c not in sel:
            p = en_pob[c]
            k = ("pos_nopub" if not p["pub_prod"] else ("pos_prot" if p["protegida"] else "pos_resto")) \
                if p["lab"] == "pos" else ("neg_pub" if p["pub_prod"] else "neg_resto")
            elegidos.append({**p, "clase": k, "peso": 0.0, "nota": "forzada R2, fuera del sorteo (peso 0)"})
            forzados_r2 += 1
    for e in elegidos:
        e["r2"] = clave(e["volcan"], e["hora_utc"]) in {clave(o["volcan"], o["hora_utc"]) for o in r2}
    for o in r2_extra:
        n = o["nuestros"][0] if o["nuestros"] else {}
        elegidos.append({"volcan": o["volcan"], "hora_utc": o["hora_utc"], "clase": "r2_fuera", "peso": 0.0,
                         "lab": "fuera_ventana", "r2": True, "granule": n.get("granule"), "sensor": n.get("sensor"),
                         "mirova": o["mirova"], "pc_vrp": n.get("pc_vrp_mw"), "z": n.get("cenit"),
                         "dc": n.get("clase"), "pub_prod": None, "protegida": False, "decide": False})
    for o in diurnas:
        elegidos.append({**o, "clase": "diurna", "peso": 0.0, "lab": "diurna_pos", "r2": False, "granule": None,
                         "protegida": True, "decide": False, "pub_prod": None})
    for e in elegidos:
        e["grilla"] = G[TIF.get(e["volcan"], e["volcan"])]
    print("forzadas R2 fuera del sorteo:", forzados_r2, "| total:", len(elegidos),
          "| granulos unicos:", len({e["granule"] for e in elegidos if e["granule"]}))
    print("por clase:", dict(collections.Counter(e["clase"] for e in elegidos)))
    print("por volcan:", dict(collections.Counter(e["volcan"] for e in elegidos)))
    assert len(elegidos) <= TOPE, "se pasó del tope de 400"
    elegidos.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for i, e in enumerate(elegidos):
        e["id"] = i
    (AQUI / "objetivos_n.json").write_text(json.dumps(elegidos, ensure_ascii=False, indent=0, default=str),
                                           encoding="utf-8")
    print("escrito objetivos_n.json")


if __name__ == "__main__":
    main()
