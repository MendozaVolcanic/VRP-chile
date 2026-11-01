# -*- coding: utf-8 -*-
"""S162 V375-B y V375-C: elige las pasadas VIIRS 375 del lote nuevo y arma objetivos_v375_bc.json.

POR QUÉ ASÍ. El lote de S159 (experiments/_s159/portes/, 150 pasadas VIIRS 375) dejó dos cosas sin resolver: (B) el
silencio del port en las noches en que MIROVA no vio nada y producción tampoco publica (neg_resto, 3.348 noches):
0 de 45 sorteadas, cota de Wilson 8,5 % (verificador V-1, D-36); (C) cuál ROI reproduce la detección débil de MIROVA,
medida con 45 alertas bajo 1 MW de 952. Las dos se miden sobre el MISMO lote: el runner guarda la grilla de cada pasada y
los brazos de ROI se recalculan sin red. El lote nuevo se SUMA al de S159 (cuyas grillas siguen guardadas): dentro de
cada estrato volcán x cenit el sorteo de S159 fue al azar y el nuevo sortea al azar entre lo que quedó, así que la
unión es una muestra al azar del estrato y su peso es N_h / (n_S159 + n_nuevo).

Marco: la población congelada de S159 (poblacion_completa.json; records de origin/main 533398f8f, referencia de
Mirova-v1 consolidado fe2d0a57 y OCR 4ddd5481, pareo ±120 s, regla D-9 en modo SN, protegida = lectura A, en VIIRS 375
las alertas sólo OCR antes del 2026-06-13 no deciden, A119). Sin los días 12 y 13 (D-29 y el hueco del 12-oct,
RECORD_FALTANTE_CHILLAN_12OCT.md) y 17 a 20 de octubre (programa §2), también para las pasadas de S159.

Cupos (PREREGISTRO_B.md §3 y PREREGISTRO_C.md §3):
  neg_resto  400 nuevas (D-36: «300 a 400»; con 0 en 445, Wilson ~0,85 %)
  pos_bajo   la unión llega a 200 (S159 tenía 45)
  pos_prot   censo (todas las que quedan)
  neg_pub    censo
La asignación de las nuevas busca que la UNIÓN quede proporcional al tamaño del estrato (así el peso es casi parejo y la
cota de Wilson sobre n efectivo de Kish se acerca a la cruda). Semilla 162.
Uso: python -I seleccion.py
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import random
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
POB = RAIZ / "experiments/_s159/portes/poblacion_completa.json"
OBJ159 = RAIZ / "experiments/_s159/portes/objetivos_portes.json"
SEMILLA = 162
EXCLUIDOS = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
CUPO_NUEVO = {"neg_resto": 400}
CUPO_UNION = {"pos_bajo": 200}
CENSO = ("pos_prot", "neg_pub")
ID0 = 1000          # los ids del lote nuevo empiezan aquí (los de S159 van de 0 a 309)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clase(o):
    if o["lab"] == "pos":
        return "pos_prot" if o["protegida"] else "pos_bajo"
    return "neg_pub" if o["pub_prod"] else "neg_resto"


def tramo(h):
    """T (2026-04-01 a 06-12, decide la tabla sola), O1 (06-13 a 08-28, antes de #535), O2 (desde el 2026-08-29)."""
    d = h[:10]
    return "T" if d < "2026-06-13" else ("O1" if d < "2026-08-29" else "O2")


def estrato(o):
    return f"{o['volcan']}|{o['estrato_z']}"


def asignar(N, viejos, n_nuevo):
    """Nuevas por estrato para que la unión quede lo más proporcional posible a N_h, con n_nuevo en total y sin pasar
    de lo que queda en cada estrato. Restos mayores (orden estable por clave)."""
    tot = sum(N.values())
    meta = sum(viejos.values()) + n_nuevo
    ideal = {h: meta * N[h] / tot for h in N}
    nuevo = {h: max(0, min(N[h] - viejos.get(h, 0), int(ideal[h]) - viejos.get(h, 0))) for h in N}
    falta = n_nuevo - sum(nuevo.values())
    while falta != 0:
        if falta > 0:
            cand = [h for h in N if nuevo[h] < N[h] - viejos.get(h, 0)]
            cand.sort(key=lambda h: (-(ideal[h] - viejos.get(h, 0) - nuevo[h]), h))
            nuevo[cand[0]] += 1
            falta -= 1
        else:
            cand = [h for h in N if nuevo[h] > 0]
            cand.sort(key=lambda h: ((ideal[h] - viejos.get(h, 0) - nuevo[h]), h))
            nuevo[cand[0]] -= 1
            falta += 1
    return nuevo


def main():
    pob = json.loads(POB.read_text(encoding="utf-8"))
    o159 = json.loads(OBJ159.read_text(encoding="utf-8"))
    grilla = {}
    for o in o159:
        if o["b"] == "VIIRS375":
            grilla.setdefault(o["volcan"], o["grilla"])
    marco = [o for o in pob["pasadas"] if o["b"] == "VIIRS375" and o["decide"] and o["hora_utc"][:10] not in EXCLUIDOS]
    s159 = {(o["volcan"], o["hora_utc"]): o for o in o159 if o["b"] == "VIIRS375"}
    s159_fuera = [k for k in s159 if k[1][:10] in EXCLUIDOS]
    print("marco: poblacion_completa.json sha256", sha256(POB))
    print("       objetivos_portes.json sha256", sha256(OBJ159))
    print("       pasadas VIIRS 375 que deciden, sin", EXCLUIDOS, ":", len(marco))
    print("       pasadas de S159 que salen por los días excluidos:", s159_fuera)
    por_clase = collections.defaultdict(list)
    for o in marco:
        por_clase[clase(o)].append(o)
    rng = random.Random(SEMILLA)
    elegidos, meta_estr = [], {}
    for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"):
        lst = sorted(por_clase[c], key=lambda o: (o["volcan"], o["hora_utc"]))
        N = collections.Counter(estrato(o) for o in lst)
        viejos = collections.Counter(estrato(o) for o in lst if (o["volcan"], o["hora_utc"]) in s159)
        # coherencia: la clase de S159 tiene que ser la misma que la del marco
        for o in lst:
            k = (o["volcan"], o["hora_utc"])
            if k in s159:
                assert s159[k]["clase"] == c, (k, s159[k]["clase"], c)
        quedan = [o for o in lst if (o["volcan"], o["hora_utc"]) not in s159]
        if c in CENSO:
            sel = quedan
        else:
            n_nuevo = CUPO_NUEVO.get(c, CUPO_UNION.get(c, 0) - sum(viejos.values()))
            asig = asignar(N, viejos, n_nuevo)
            por_h = collections.defaultdict(list)
            for o in quedan:
                por_h[estrato(o)].append(o)
            sel = []
            for h in sorted(asig):
                if asig[h]:
                    sel += rng.sample(por_h[h], asig[h])
        nuevos = collections.Counter(estrato(o) for o in sel)
        meta_estr[c] = {h: {"N": N[h], "n_s159": viejos.get(h, 0), "n_nuevo": nuevos.get(h, 0)} for h in sorted(N)}
        for o in sel:
            elegidos.append({**o, "clase": c, "lote": "S162", "tramo": tramo(o["hora_utc"]), "estrato": estrato(o),
                             "grilla": grilla[o["volcan"]]})
        uni = {h: v["n_s159"] + v["n_nuevo"] for h, v in meta_estr[c].items()}
        w = [meta_estr[c][h]["N"] / uni[h] for h in uni if uni[h]]
        sin = [h for h in uni if not uni[h]]
        print(f"\n{c}: N {len(lst)}, S159 {sum(viejos.values())}, nuevas {len(sel)}, unión {sum(uni.values())}; "
              f"peso de la unión mín {min(w):.2f} máx {max(w):.2f}; estratos sin ninguna pasada en la unión: {sin}")
        print("   por tramo (nuevas):", dict(sorted(collections.Counter(tramo(o['hora_utc']) for o in sel).items())))
        print("   partidas (nuevas):", sum(bool(o.get("partida")) for o in sel))
    elegidos.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for i, e in enumerate(elegidos):
        e["id"] = ID0 + i
    claves = [(e["volcan"], e["hora_utc"]) for e in elegidos]
    assert len(set(claves)) == len(claves), "pasada repetida"
    assert not set(claves) & set(s159), "pasada ya medida en S159"
    print("\ntotal nuevas:", len(elegidos), dict(collections.Counter(e["clase"] for e in elegidos)),
          "gránulos únicos", len({e["granule"] for e in elegidos}))
    salida = {"meta": {"semilla": SEMILLA, "excluidos": EXCLUIDOS, "poblacion_sha256": sha256(POB),
                       "objetivos_s159_sha256": sha256(OBJ159), "estratos": meta_estr,
                       "marco": pob["meta"]}, "pasadas": elegidos}
    (AQUI / "objetivos_v375_bc.json").write_text(json.dumps(salida, ensure_ascii=False, indent=0, default=str),
                                                 encoding="utf-8")
    print("escrito objetivos_v375_bc.json")


if __name__ == "__main__":
    main()
