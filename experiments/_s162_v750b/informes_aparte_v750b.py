# -*- coding: utf-8 -*-
"""S162 V750-B, informes aparte pedidos por la coordinadora S173 (2026-11-03). NO deciden: el veredicto es el del
lector de la adenda 3. Escrito antes de abrir los artefactos del run 41615021658 (SESGOS_CONOCIDOS_V750B.md).

POR QUÉ. (1) El oráculo R2 rellena el fondo bajo el píxel caliente con un Delaunay de scipy sin perturbar, y MATLAB con
otro (VPCC750-01). Eso mueve la magnitud y, sólo cuando el VRP queda cerca de cero, la publicación. El probe guarda por
brazo `vrp_banda`, el mínimo y el máximo del VRP con 20 triangulaciones perturbadas al azar: si la pasada publica con
uno y no con el otro, su publicación depende de la diagonal elegida y se marca «sensible a la triangulación».
(2) K cae con el ángulo cenital del sensor y las vías no: corte bajo y sobre 30°. (3) Tupungatito: alertas que publica
K y cada brazo.

Mismas piezas que el analizador sellado (se importan, no se copian): pasadas observadas, K distinto de producción fuera,
record del cúmulo con ancla en el cráter, predicado del tablero con node, etiquetas por canal.
Uso: python informes_aparte_v750b.py --art <sellado/*> --objetivos objetivos_v750b.json --salida <archivo nuevo>
     python informes_aparte_v750b.py --prueba     (escenas sintéticas; tiene que decir PRUEBA OK)
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import statistics
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import analizar_v750b as A  # noqa: E402

CORTE_Z = 30.0


def etiqueta(o, canal):
    """La de analizar_v750b.main (closure, no importable): 'prot', 'baja', 'neg' o None."""
    if canal == "decide":
        canal = "tabla" if o["hora_utc"] < A.FRONTERA_OCR else "todo"
    if o["lab"] == "neg_limpio":
        return "neg"
    if o["lab"] != "pos" or not o.get("decide"):
        return None
    if canal == "tabla" and not o.get("alerta_tabla"):
        return None
    p = (any(A.alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS") if canal == "tabla"
         else o.get("protegida"))
    return "prot" if p else "baja"


def con_vrp(o, v):
    o = copy.deepcopy(o)
    o["vrp_mw"] = v
    return o


def calcular(obj, res, inner):
    oks = [i for i in obj if A.partida(res.get(i) or {}) == "observada" and res[i].get("dayflag") == 0
           and set(A.CAJAS) <= set(res[i].get("oraculo") or {})]
    anc = {i: tuple(obj[i].get("pos_crater") or (A.C, A.C)) for i in oks}
    casos, idx = [], []
    for i in oks:
        o, r, inn = obj[i], res[i], inner[obj[i]["volcan"]]
        casos.append([A.slim((r.get("brazos") or {}).get("K", {}).get("record")), inn])
        idx.append((i, "K", "base"))
        for c in A.CAJAS:
            x = r["oraculo"][c]
            banda = x.get("vrp_banda") if x.get("npix") else None
            for var, v in (("base", None), ("min", banda[0] if banda else None), ("max", banda[1] if banda else None)):
                xx = x if (var == "base" or v is None) else con_vrp(x, v)
                casos.append([A.record_cumulo(xx, inn, o["sensor"], anc[i]), inn])
                idx.append((i, c, var))
    P = {k: bool(p[4]) for k, p in zip(idx, A.B.correr_node(casos))}

    def vrp_k(i):
        rec = (res[i].get("brazos") or {}).get("K", {}).get("record") or {}
        return (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0

    # §7 del pre-registro: las pasadas con K distinto de producción salen de todos los brazos (como el analizador)
    kd = {i for i in oks if bool(obj[i].get("pub_prod")) != P[(i, "K", "base")]
          or abs(vrp_k(i) - (obj[i].get("pc_vrp") or 0)) > 0.001}
    oks = [i for i in oks if i not in kd]

    def pub(i, b, var="base"):
        return P[(i, "K", "base")] if b == "K" else P[(i, A.caja_de(b, obj[i]["volcan"]), var)]

    def vrp(i, b):
        return vrp_k(i) if b == "K" else res[i]["oraculo"][A.caja_de(b, obj[i]["volcan"])].get("vrp_mw") or 0.0

    return oks, len(kd), pub, vrp


def informar(obj, res, inner, pr):
    oks, n_kd, pub, vrp = calcular(obj, res, inner)
    pr(f"pasadas observadas que cuentan: {len(oks)} (fuera por K distinto de producción: {n_kd})")

    pr("\n== 1. sensibles a la triangulación (VPCC750-01): publica con el mínimo de vrp_banda y no con el máximo, o al "
       "revés; canal que decide, T y O juntos")
    for b in A.CANDIDATOS:
        t = collections.Counter()
        prot_s, bloques = [], set()
        for i in oks:
            e = etiqueta(obj[i], "decide")
            if e is None:
                continue
            for bb in {b, "B1"}:
                if pub(i, bb, "min") != pub(i, bb, "max"):
                    if bb == b:
                        t[e] += 1
                        if e == "prot":
                            prot_s.append((obj[i]["volcan"], obj[i]["hora_utc"]))
                    if e in ("baja", "neg"):
                        bloques.add((obj[i]["hora_utc"][:10], obj[i]["volcan"]))
        pr(f"   {b}: prot {t['prot']} baja {t['baja']} neg {t['neg']} | bloques P2 contra B1 con alguna pasada "
           f"sensible: {len(bloques)} | protegidas sensibles: {prot_s or 'ninguna'}")

    pr(f"\n== 2. cenit bajo {CORTE_Z:.0f}° y {CORTE_Z:.0f}° o más (canal que decide, T y O juntos)")
    for b in A.BRAZOS:
        lin = []
        for nom, f in (("z<30", lambda z: z is not None and z < CORTE_Z), ("z>=30", lambda z: z is not None and z >= CORTE_Z)):
            m = collections.Counter()
            rz = []
            for i in oks:
                if not f(obj[i].get("z")):
                    continue
                e = etiqueta(obj[i], "decide")
                if e is None:
                    continue
                pb = pub(i, b)
                m["n_" + e] += 1
                m["P1"] += e == "prot" and not pb
                m["E"] += (e == "baja" and not pb) or (e == "neg" and pb)
                if e in ("prot", "baja") and pb and obj[i].get("mirova_vrp"):
                    rz.append(vrp(i, b) / obj[i]["mirova_vrp"])
            med = f"{statistics.median(rz):.3f} n={len(rz)}" if rz else "-"
            lin.append(f"{nom}: prot {m['n_prot']} P1 {m['P1']} | E {m['E']} (baja {m['n_baja']}, neg {m['n_neg']}) "
                       f"| razón {med}")
        pr(f"   {b:3s} " + " || ".join(lin))
    sin_z = sum(1 for i in oks if obj[i].get("z") is None)
    pr(f"   pasadas sin cenit (fuera de los dos tramos): {sin_z}")

    pr("\n== 3. Tupungatito: alertas publicadas (prot y bajo 1 MW) por K y por cada brazo")
    for canal in ("decide", "tabla"):
        lin = []
        for b in A.BRAZOS:
            m = collections.Counter()
            for i in oks:
                if obj[i]["volcan"] != "Tupungatito":
                    continue
                e = etiqueta(obj[i], canal)
                if e in ("prot", "baja"):
                    m["al"] += 1
                    m["al_pub"] += pub(i, b)
                    m["prot"] += e == "prot"
                    m["prot_pub"] += e == "prot" and pub(i, b)
            lin.append(f"{b} {m['al_pub']}/{m['al']} (prot {m['prot_pub']}/{m['prot']})")
        pr(f"   canal {canal}: " + " | ".join(lin))


def cargar_y_correr(art, objetivos, salida):
    obj = {o["id"]: o for o in json.loads(Path(objetivos).read_text(encoding="utf-8"))}
    res = A.cargar(art)
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    pr("INFORMES APARTE V750-B (no deciden; el veredicto es el del lector de la adenda 3)")
    informar(obj, res, A.B.inner_desde_html(), pr)
    if salida:
        if Path(salida).exists():
            raise SystemExit(f"{salida} ya existe: no se pisa")
        Path(salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    return L


def prueba():
    """Escenas sintéticas con la población de la batería sellada: (a) sin banda nadie es sensible; (b) una protegida de
    Láscar cuya banda cruza el cero sale sensible en todos los brazos de caja; (c) Tupungatito cuenta lo que se le
    pone; (d) el corte de cenit separa."""
    # la batería es un script (lee argumentos al importarse): se toman con ast sólo las piezas que arman la población
    import ast
    import types
    src = (AQUI / "bateria_regla_v750b.py").read_text(encoding="utf-8")
    quiero = {"SENSOR", "PUB", "NOPUB", "COB", "INNER", "CELDA", "k_record", "Pob", "todos", "base"}
    piezas = [ast.get_source_segment(src, n) for n in ast.parse(src).body
              if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in quiero)
              or (isinstance(n, ast.Assign) and {t.id for t in n.targets if isinstance(t, ast.Name)} & quiero)]
    BT = types.ModuleType("bateria_piezas")
    BT.__dict__["json"] = json
    exec(compile("\n\n".join(piezas), "bateria_regla_v750b.py", "exec"), BT.__dict__)
    ok = True
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        p = BT.base()
        p.pasada("Tupungatito", "2026-09-10 05:00", "pos",
                 {"K": False, "B0": False, "B1": True, "B2": True, "B3": True, "B5": False}, vrp_mirova=1.4)
        p.pasada("Tupungatito", "2026-09-11 05:00", "pos", BT.todos(k=False, b=False), vrp_mirova=0.4)
        p.escribir(d / "a")
        La = cargar_y_correr([str(d / "a" / "art")], d / "a" / "objetivos.json", None)
        sens_a = [x for x in La if x.startswith("   B") and "prot 0 baja 0 neg 0" not in x and "bloques" in x]
        tup = [x for x in La if x.startswith("   canal decide")][0]
        ok &= not sens_a and "K 0/2 (prot 0/1)" in tup and "B1 1/2 (prot 1/1)" in tup and "B0 0/2 (prot 0/1)" in tup
        # (b): la protegida 0 de Láscar (id de la primera pasada de Láscar) con banda que cruza el cero
        i0 = next(o["id"] for o in p.objs if o["volcan"] == "Lascar" and o["protegida"])
        for c in A.CAJAS:
            x = copy.deepcopy(p.res[i0]["oraculo"][c])
            x["vrp_banda"] = [-0.01, 0.5]
            p.res[i0]["oraculo"][c] = x
        # (d): la mitad de las pasadas a cenit 15 (la batería las deja en 30, que cae en «30° o más»)
        for o in p.objs[::2]:
            o["z"] = 15.0
        p.escribir(d / "b")
        Lb = cargar_y_correr([str(d / "b" / "art")], d / "b" / "objetivos.json", None)
        b0 = [x for x in Lb if x.startswith("   B0:")][0]
        ok &= "prot 1 baja 0 neg 0" in b0 and "Lascar" in b0
        k = [x for x in Lb if x.startswith("   K  ")][0]
        ok &= all("prot 0 P1" not in t for t in k.split("||"))   # las protegidas quedan en los dos tramos
    print("PRUEBA OK" if ok else "PRUEBA FALLA")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", nargs="+")
    ap.add_argument("--objetivos")
    ap.add_argument("--salida", default="")
    ap.add_argument("--prueba", action="store_true")
    a = ap.parse_args()
    if a.prueba:
        return prueba()
    cargar_y_correr(a.art, a.objetivos, a.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
