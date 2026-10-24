# -*- coding: utf-8 -*-
"""S162 V375-B2: segunda muestra de noches limpias neg_resto, disjunta de S159 y de S162 (PREREGISTRO_B2.md §3).

POR QUÉ. V375-B quedó NO RESUELTO por la regla sellada (`../resultado_run40116289866/INFORME.md`). La coordinadora
resolvió con D-48 (2026-10-24) una segunda muestra de neg_resto, pre-registrada antes de mirar nada nuevo, con la misma
regla. El tamaño sale de `tamano_b2.py`: con B2 sola decidiendo neg_resto (la lógica sellada de C §5.5: decide lo no
visto; verificador del borrador, b2/verificador/INFORME.md F1), 1.200 noches dan 93 % de probabilidad de decidir con la
tasa observada.

Mismo marco que `../seleccion.py` (población congelada de S159, sin el 12, 13 y 17 a 20 de octubre, sólo pasadas que
deciden). Asignación por estrato volcán x cenit proporcional al tamaño del estrato EN EL MARCO (B2 decide sola, así que
es B2 la que tiene que ser proporcional), con restos mayores y sin pasar de lo que queda sin medir en cada estrato.
Semilla 163 (la siguiente a la 162 del lote S162). Ids desde 3000.
Uso: python -I seleccion_b2.py
"""
from __future__ import annotations

import collections
import io
import json
import random
import sys
from pathlib import Path

# la salida en utf-8 la deja seleccion.py al importarse
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import seleccion as S  # noqa: E402

SEMILLA = 163
N_NUEVO = 1200
ID0 = 3000
ID_CTL = 5000   # la muestra usa 3000 a 4199
ART162 = Path("C:/vrp-trabajo/temporales/s162_v375/run_40116289866")   # artefactos del lote S162


def main():
    pob = json.loads(S.POB.read_text(encoding="utf-8"))
    o159 = json.loads(S.OBJ159.read_text(encoding="utf-8"))
    bc = json.loads((AQUI.parent / "objetivos_v375_bc.json").read_text(encoding="utf-8"))
    grilla = {o["volcan"]: o["grilla"] for o in o159 if o["b"] == "VIIRS375"}
    vistos = {(o["volcan"], o["hora_utc"]) for o in o159 if o["b"] == "VIIRS375"}
    vistos |= {(o["volcan"], o["hora_utc"]) for o in bc["pasadas"]}
    marco = [o for o in pob["pasadas"] if o["b"] == "VIIRS375" and o["decide"] and o["hora_utc"][:10] not in S.EXCLUIDOS
             and S.clase(o) == "neg_resto"]
    print("marco neg_resto:", len(marco), "| poblacion sha256", S.sha256(S.POB))
    print("objetivos_v375_bc.json sha256", S.sha256(AQUI.parent / "objetivos_v375_bc.json"))
    N = collections.Counter(S.estrato(o) for o in marco)
    s162 = collections.Counter(S.estrato(o) for o in bc["pasadas"] if o["clase"] == "neg_resto")
    quedan = sorted([o for o in marco if (o["volcan"], o["hora_utc"]) not in vistos],
                    key=lambda o: (o["volcan"], o["hora_utc"]))
    disp = collections.Counter(S.estrato(o) for o in quedan)
    print("quedan sin medir:", len(quedan))
    tot = sum(N.values())
    ideal = {h: N_NUEVO * N[h] / tot for h in N}
    asig = {h: min(disp.get(h, 0), int(ideal[h])) for h in N}
    while sum(asig.values()) < N_NUEVO:
        cand = sorted([h for h in N if asig[h] < disp.get(h, 0)], key=lambda h: (-(ideal[h] - asig[h]), h))
        asig[cand[0]] += 1
    rng = random.Random(SEMILLA)
    por_h = collections.defaultdict(list)
    for o in quedan:
        por_h[S.estrato(o)].append(o)
    sel = []
    for h in sorted(asig):
        if asig[h]:
            sel += rng.sample(por_h[h], asig[h])
    meta = {h: {"N": N[h], "n_s162": s162.get(h, 0), "n_b2": sum(1 for o in sel if S.estrato(o) == h)} for h in sorted(N)}
    w = [m["N"] / m["n_b2"] for m in meta.values() if m["n_b2"]]
    print(f"nuevas {len(sel)}; peso de B2 sola mín {min(w):.2f} máx {max(w):.2f}; estratos sin pasadas de B2: "
          f"{[h for h, m in meta.items() if not m['n_b2']]}")
    print("por tramo:", dict(sorted(collections.Counter(S.tramo(o["hora_utc"]) for o in sel).items())),
          "| partidas:", sum(bool(o.get("partida")) for o in sel))
    out = []
    for o in sel:
        out.append({**o, "clase": "neg_resto", "lote": "S162b", "tramo": S.tramo(o["hora_utc"]), "estrato": S.estrato(o),
                    "grilla": grilla[o["volcan"]]})
    out.sort(key=lambda e: (e["granule"] or "", e["volcan"]))
    for i, e in enumerate(out):
        e["id"] = ID0 + i
    claves = [(e["volcan"], e["hora_utc"]) for e in out]
    assert len(set(claves)) == len(claves) and not set(claves) & vistos
    # Control de vida (PREREGISTRO_B2.md §4; verificador v2, hallazgo 3): B2 sólo trae neg_resto, así que un port
    # muerto daría 0 de 1.200 y «calla». Se re-miden en el mismo run 20 pasadas ya medidas en S162: 12 protegidas de
    # Láscar y Chillán con píxeles en M14 (sorteadas, semilla 164), las 4 neg_resto que M14 publicó y 4 neg_resto en 0.
    # El runner tiene que reproducirlas EXACTAS (mismo gránulo, mismo código). Lote «CTL», clase «control_vida»: no
    # entran a ningún denominador.
    R = {}
    for f in sorted(ART162.rglob("resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            R[r["id"]] = r
    o162 = {o["id"]: o for o in bc["pasadas"]}
    def con_px(i):
        return R.get(i, {}).get("estado") == "ok" and R[i]["port"]["M14"]["npix"] > 0
    prot = sorted(i for i, o in o162.items() if o["clase"] == "pos_prot" and o["volcan"] in ("Lascar", "NevadosDeChillan")
                  and con_px(i))
    enc = sorted(i for i, o in o162.items() if o["clase"] == "neg_resto" and con_px(i))
    cero = sorted(i for i, o in o162.items() if o["clase"] == "neg_resto" and R.get(i, {}).get("estado") == "ok"
                  and not R[i]["port"]["M14"]["npix"])
    rc = random.Random(SEMILLA + 1)
    ctl = rc.sample(prot, 12) + enc + rc.sample(cero, 4)
    for n, i in enumerate(ctl):
        o = o162[i]
        out.append({**o, "id": ID_CTL + n, "id_ref": i, "lote": "CTL", "clase": "control_vida",
                    "clase_ref": o["clase"], "ref_M14": [R[i]["port"]["M14"]["npix"], R[i]["port"]["M14"]["vrp_mw"]]})
    print(f"control de vida: {len(ctl)} pasadas de S162 (protegidas {12}, neg_resto encendidas {len(enc)}, en 0 4); "
          f"artefactos de referencia {ART162}")
    print("gránulos únicos (muestra + control):", len({e["granule"] for e in out}))
    (AQUI / "objetivos_v375_b2.json").write_text(json.dumps(
        {"meta": {"semilla": SEMILLA, "excluidos": S.EXCLUIDOS, "estratos_neg_resto": meta,
                  "poblacion_sha256": S.sha256(S.POB),
                  "objetivos_bc_sha256": S.sha256(AQUI.parent / "objetivos_v375_bc.json")}, "pasadas": out},
        ensure_ascii=False, indent=0, default=str), encoding="utf-8")
    print("escrito objetivos_v375_b2.json")


if __name__ == "__main__":
    main()
