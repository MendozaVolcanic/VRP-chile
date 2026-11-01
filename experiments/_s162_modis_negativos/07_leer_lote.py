# -*- coding: utf-8 -*-
"""S162 MODIS negativos, paso 7: lectura del lote, en el orden del pre-registro (PREREGISTRO.md §6 y §5): primero
cobertura y controles, despues x y n, despues el veredicto de 03_regla_decision.py. Escrito ANTES de correr el lote.

«Publica» = el predicado del tablero ejecutado con node sobre el record sintetico del port, con el MISMO codigo que
S159 (04_analizar.py: dist_centroide, record_port, slim; banco_paridad.correr_node), sobre el arbol del commit base.
No evaluable (sale de n, se cuenta aparte): estado distinto de ok (sin granulo, volcan fuera del granulo, error),
escena invalida del .m (motivo_vacio = escena_invalida) o grilla con mas de la mitad sin dato (port_estado =
grilla_incompleta).

Ensayo en seco (control de este lector): con los objetivos y los resultados de S159 tiene que dar las 38 neg_resto
de S159, 37 con resultado, 36 evaluables, x = 0 e INDECIDIBLE (lo mismo que dijo el verificador V-1):
  python -I 07_leer_lote.py --raiz <arbol base> --objetivos <S159>/objetivos_portes.json --art <run_39712862945>
Uso con el lote: python -I 07_leer_lote.py --raiz <arbol base> --art <carpeta del run> --s159 <run_39712862945>
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
T535 = "2026-08-28 23:00"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cargar_res(dirs):
    res = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("resultados_MODIS_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    return res


def evaluable(r):
    if not r or r.get("estado") != "ok" or not r.get("port"):
        return False, (r or {}).get("estado", "sin_resultado")
    if (r["port"].get("fisica") or {}).get("motivo_vacio") == "escena_invalida":
        return False, "escena_invalida"
    if r.get("port_estado") == "grilla_incompleta":
        return False, "grilla_incompleta"
    if (r["port"].get("fisica") or {}).get("motivo_vacio") == "sunglint":     # VCD-14: el .m no mira la escena
        return False, "sunglint"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True, help="arbol del commit base (04_analizar.py, frontend, scripts)")
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_neg_resto_modis.json"))
    ap.add_argument("--s159", default="", help="resultados del lote S159, para el control de instrumento")
    ap.add_argument("--salida", default="")
    a = ap.parse_args()
    A = modulo("analizar_s159", Path(a.raiz) / "experiments/_s159/portes/04_analizar.py")
    R = modulo("regla_s162", AQUI / "03_regla_decision.py")
    B = A.B
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8")) if o["b"] == "MODIS"}
    obj = {i: o for i, o in obj.items() if o["clase"] in ("neg_resto", "control_s159")}
    res = cargar_res(a.art)
    inner = B.inner_desde_html()

    pr("== 1. cobertura (A108): objetivos", len(obj), "| con resultado", sum(i in res for i in obj))
    ev = {i: evaluable(res.get(i)) for i in obj}
    for k, v in sorted(collections.Counter((o["clase"], ev[i][1]) for i, o in obj.items()).items()):
        pr("   ", k, v)
    pr("   no evaluables:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], ev[i][1]) for i in sorted(obj) if not ev[i][0]])

    # publicacion con el predicado del tablero (port fisica y K re-corrido)
    casos, idx = [], []
    for i in sorted(obj):
        r = res.get(i)
        if not ev[i][0]:
            continue
        o = obj[i]
        p = r["port"]["fisica"]
        if p and p.get("npix"):
            p["_dcen"] = A.dist_centroide(p, o["grilla"])
        rp = A.record_port(p, inner[o["volcan"]], o["sensor"])
        casos.append([A.slim({k: x for k, x in rp.items() if not k.startswith("_")}), inner[o["volcan"]]])
        idx.append((i, "port"))
        krec = (r.get("K") or {}).get("record")
        if krec is not None:
            casos.append([A.slim(krec), inner[o["volcan"]]])
            idx.append((i, "K"))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))} if casos else {}

    pr("\n== 2. controles (antes de leer)")
    ids_ev = [i for i in sorted(obj) if ev[i][0]]
    dpub, dvrp, sink = [], [], []
    for i in ids_ev:
        if (i, "K") not in P:
            sink.append(i)
            continue
        if bool(obj[i]["pub_prod"]) != P[(i, "K")]:
            dpub.append((i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["pub_prod"], P[(i, "K")]))
        pk = ((res[i]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw")
        po = obj[i]["pc_vrp"]
        if not ((pk is None and po is None) or (pk is not None and po is not None and abs(pk - po) <= 0.001)):
            dvrp.append((i, obj[i]["volcan"], obj[i]["hora_utc"], po, pk))
    nk = len(ids_ev) - len(sink)
    pr(f"  K re-corrido = publicado: publica igual {nk - len(dpub)} de {nk}; pc.vrp_mw a 0,001 MW {nk - len(dvrp)} de "
       f"{nk}; sin record K {len(sink)}; distintos: {dpub[:20]} {dvrp[:20]}")
    if nk and len(dpub) > 0.05 * nk:
        pr("  AVISO: K re-corrido publica distinto en mas del 5 %: la lectura se informa tambien contra K re-corrido")
    ctl = [i for i in sorted(obj) if obj[i]["clase"] == "control_s159"]
    if ctl:
        prev = cargar_res([a.s159]) if a.s159 else {}
        filas = []
        for i in ctl:
            mine = (res.get(i) or {}).get("port", {}).get("fisica")
            ref = (prev.get(i) or {}).get("port", {}).get("fisica")
            if mine is None or ref is None:
                filas.append((i, "SIN DATO"))
                continue
            igual = mine["npix"] == ref["npix"] and (
                (mine["vrp_mw"] is None and ref["vrp_mw"] is None) or
                (mine["vrp_mw"] is not None and ref["vrp_mw"] is not None and abs(mine["vrp_mw"] - ref["vrp_mw"]) < 1e-6))
            filas.append((i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase_s159"], mine["npix"], ref["npix"],
                          "publica" if P.get((i, "port")) else "calla", "IGUAL" if igual else "DISTINTO"))
        pr(f"  control de instrumento contra S159 (mismo id): iguales {sum(f[-1] == 'IGUAL' for f in filas)} de "
           f"{len(ctl)}; protegidas que publican "
           f"{sum(1 for f in filas if len(f) > 2 and f[3] == 'pos_prot' and f[6] == 'publica')} de "
           f"{sum(1 for i in ctl if obj[i]['clase_s159'] == 'pos_prot')}")
        for f in filas:
            pr("    ", f)
    nat = [i for i in ids_ev if (res[i].get("nativo") or {}).get("guardado")]
    pr(f"  recorte nativo guardado: {len(nat)} de {len(ids_ev)} evaluables; sin guardar:",
       [(i, (res[i].get("nativo") or {}).get("motivo")) for i in ids_ev if i not in nat][:20])

    neg = [i for i in ids_ev if obj[i]["clase"] == "neg_resto"]
    x = sum(P.get((i, "port"), False) for i in neg)
    n = len(neg)
    pr(f"\n== 3. neg_resto: n evaluables {n}, el port publica en x = {x}")
    enc = [i for i in neg if P.get((i, "port"))]
    pr("   publicaciones:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], res[i]["port"]["fisica"]["npix"],
                             res[i]["port"]["fisica"]["vrp_mw"], "partida" if obj[i].get("partida") else "") for i in enc])
    xk = sum(P.get((i, "port"), False) and not P.get((i, "K"), False) for i in neg)
    pr(f"   contra K re-corrido en vez del publicado: x = {xk}")
    w = sum(obj[i]["peso"] for i in neg)
    pr(f"   tasa ponderada {sum(obj[i]['peso'] for i in enc) / w if w else float('nan'):.4f} (cruda "
       f"{x / n if n else float('nan'):.4f})")
    for nombre, f in (("volcan", lambda o: o["volcan"]), ("cenit", lambda o: o["estrato_z"]),
                      ("plataforma", lambda o: o["sensor"]),
                      ("tramo #535", lambda o: "antes" if o["hora_utc"] < T535 else "desde"),
                      ("partida", lambda o: bool(o.get("partida")))):
        c = collections.defaultdict(lambda: [0, 0])
        for i in neg:
            c[f(obj[i])][1] += 1
            c[f(obj[i])][0] += P.get((i, "port"), False)
        pr(f"   por {nombre}:", {k: f"{v[0]}/{v[1]}" for k, v in sorted(c.items(), key=lambda t: str(t[0]))})

    pr("\n== 4. veredicto (03_regla_decision.py)")
    import numpy as np
    F = R.filas()
    de_rep, pp_rep = R.replicas_otros(F, np.random.default_rng(R.SEMILLA))
    if n:
        v = R.veredicto(x, n, de_rep, pp_rep, np.random.default_rng(R.SEMILLA + 1))
        pr(f"  x = {x} de n = {n}: DeltaE punto {v['dE_punto']:+.1f}, IC 95 % [{v['ic'][0]:+.1f}; {v['ic'][1]:+.1f}] "
           f"-> {v['veredicto']}; R3 IC [{v['r3_ic'][0]:.4f}; {v['r3_ic'][1]:.4f}] -> {v['r3']}; cota conservadora "
           f"{v['cota_conservadora']:+.1f}")
    if a.salida:
        Path(a.salida).write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
