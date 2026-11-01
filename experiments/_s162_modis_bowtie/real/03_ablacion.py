# -*- coding: utf-8 -*-
"""Paso 3, la ablacion: el port `fisica` con todos los pixeles contra el port con cada metodo de quitar duplicados,
en las 403 pasadas evaluables del lote 40120713181 (390 neg_resto + 13 control_s159, 11 de ellas alertas protegidas
de MIROVA). Se corre DESPUES de 02_cobertura.py, que dice que metodos se pueden usar para concluir.

«Publica» = el predicado del tablero ejecutado con node sobre el record sintetico del port, con el MISMO codigo que
el lector del lote (experiments/_s162_modis_negativos/07_leer_lote.py: 04_analizar.dist_centroide, record_port, slim;
banco_paridad.correr_node, sobre el arbol del commit base).
Pregunta 1 del instrumento: si quitar pixeles no cambiara nada, ¿se veria? El metodo C_sin_det0 (abre huecos) y los
metodos A en las pasadas oblicuas tocan la grilla; se informa en cuantas pasadas la grilla remuestreada cambia y en
cuantas no cambia (en el nadir los metodos A no quitan nada y la grilla tiene que ser identica: nulo por construccion).
Uso: python -I 03_ablacion.py
"""
from __future__ import annotations

import collections
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent


def modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    pr, L = CM.pr_factory()
    A = modulo("analizar_s159", CM.PORTES / "04_analizar.py")
    B = A.B
    inner = B.inner_desde_html()
    obj, res = CM.objetivos(), CM.resultados()
    cob = {int(k): v for k, v in json.loads((AQUI / "02_cobertura.json").read_text(encoding="utf-8")).items()}
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    metodos = CM.ORDEN_METODOS
    out, casos, idx = {}, [], []
    for i in ids:
        o, r, g = obj[i], res[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        out[i] = {}
        grilla_todos = None
        for m in metodos:
            q = CM.mascara_quitar(G, m)
            mir, tir = CM.PP.grillar(CM.crop_desde_nativo(n, q), g, g["epsg"])
            if m == "todos":
                grilla_todos = (mir, tir)
                cambia_grilla = False
            else:
                cambia_grilla = not (np.array_equal(mir, grilla_todos[0], equal_nan=True) and
                                     np.array_equal(tir, grilla_todos[1], equal_nan=True))
            p = CM.MP.correr(mir, tir, g, g["X0"], g["Y0"], r["dayflag"], r["sunglint"], CM.MP.SENSORES["MODIS"],
                             modo="fisica", semillas=0)
            if p.get("npix"):
                p["_dcen"] = A.dist_centroide(p, g)
            rp = A.record_port(p, inner[o["volcan"]], o["sensor"])
            casos.append([A.slim({k: x for k, x in rp.items() if not k.startswith("_")}), inner[o["volcan"]]])
            idx.append((i, m))
            out[i][m] = {"npix": p["npix"], "vrp_mw": p["vrp_mw"], "motivo": p.get("motivo_vacio"),
                         "pixeles": [q_[:4] for q_ in p["pixeles"]], "cambia_grilla": cambia_grilla,
                         "nan_grilla": int(np.isnan(mir).sum())}
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    for (i, m), v in P.items():
        out[i][m]["publica"] = v
    (AQUI / "03_ablacion.json").write_text(json.dumps(out), encoding="utf-8")

    # ------------------------------------------------------------------ controles del instrumento
    pr("== controles")
    pr(f"  'todos' publica en {sum(P[(i, 'todos')] for i in ids)} de {len(ids)} (el lector del lote dio 13: 11 "
       f"protegidas + Llaima 1120 + Lascar 1251)")
    pr(f"  'todos' = resultado del lote en npix: {sum(out[i]['todos']['npix'] == res[i]['port']['fisica']['npix'] for i in ids)} de {len(ids)}")
    for m in metodos[1:]:
        quita = sum(cob[i]["metodos"][m]["frac_quitada"] > 0 for i in ids)
        cg = sum(out[i][m]["cambia_grilla"] for i in ids)
        nulo = [i for i in ids if cob[i]["metodos"][m]["frac_quitada"] == 0 and out[i][m]["cambia_grilla"]]
        pr(f"  {m}: quita algo en {quita} pasadas; la grilla cambia en {cg}; pasadas sin quitar nada con grilla "
           f"distinta (tiene que ser 0): {len(nulo)}")

    # ------------------------------------------------------------------ publicacion
    def estr_z(z):
        return "z<25" if z < 25 else "25-40" if z < 40 else "40-50" if z < 50 else "z>=50"

    grupos = {
        "neg_resto": [i for i in ids if obj[i]["clase"] == "neg_resto"],
        "control_s159 protegidas": [i for i in ids if obj[i]["clase"] == "control_s159" and obj[i]["protegida"]],
        "control_s159 no protegidas": [i for i in ids if obj[i]["clase"] == "control_s159" and not obj[i]["protegida"]],
    }
    pr("\n== cambios de publicacion contra 'todos' (gana = publica con el metodo y no con todos; pierde = al reves)")
    for gname, gi in grupos.items():
        pr(f"  {gname} (n {len(gi)}; 'todos' publica en {sum(P[(i, 'todos')] for i in gi)})")
        for m in metodos[1:]:
            gana = [i for i in gi if P[(i, m)] and not P[(i, "todos")]]
            pierde = [i for i in gi if P[(i, "todos")] and not P[(i, m)]]
            dnp = sum(out[i][m]["npix"] != out[i]["todos"]["npix"] for i in gi)
            pr(f"     {m:24s} publica {sum(P[(i, m)] for i in gi):3d} | gana {len(gana)} {gana} | pierde "
               f"{len(pierde)} {pierde} | npix distinto en {dnp}")

    pr("\n== por estrato (neg_resto + controles): pasadas con publicacion distinta / npix distinto, por metodo")
    est = {
        "cenit": lambda i: estr_z(obj[i]["z"]),
        "crater en det 0 o 9": lambda i: cob[i]["det_crater"] in (0, 9),
        "crater con 2+ huellas (todos)": lambda i: cob[i]["huellas_en_crater_todos"] >= 2,
    }
    for ename, f in est.items():
        c = collections.defaultdict(list)
        for i in ids:
            c[f(i)].append(i)
        pr(f"  por {ename}:")
        for k in sorted(c, key=str):
            gi = c[k]
            fila = []
            for m in metodos[1:]:
                dp = sum(P[(i, m)] != P[(i, "todos")] for i in gi)
                dn = sum(out[i][m]["npix"] != out[i]["todos"]["npix"] for i in gi)
                fila.append(f"{m.split('_')[0]}{'' if m[0] != 'A' else m[1:].replace('_centro_cubierto', 'c').replace('_huella_entera', 'h')}: {dp}/{dn}")
            pr(f"     {str(k):6s} n {len(gi):3d}  " + "  ".join(fila))

    # ------------------------------------------------------------------ magnitud en las pasadas con deteccion
    pr("\n== magnitud en las pasadas donde 'todos' detecta (VRP en MW; razon metodo/todos; MIROVA de la tabla de objetivos)")
    det = [i for i in ids if out[i]["todos"]["npix"]]
    cab = "  id    volcan               hora              z     det_cr hu  MIROVA   todos(np)  " + "  ".join(
        f"{m}" for m in metodos[1:])
    pr(cab)
    for i in det:
        o = obj[i]
        t = out[i]["todos"]
        cols = []
        for m in metodos[1:]:
            v = out[i][m]
            ratio = (v["vrp_mw"] / t["vrp_mw"]) if v["vrp_mw"] else 0.0
            cols.append(f"{(v['vrp_mw'] or 0):.3f}({v['npix']}) x{ratio:.3f} {'P' if P[(i, m)] else '-'}")
        pr(f"  {i:5d} {o['volcan']:20s} {o['hora_utc']} {o['z']:5.1f}  {cob[i]['det_crater']}      "
           f"{cob[i]['huellas_en_crater_todos']}   {o['mirova_vrp']:.3f}   {t['vrp_mw']:.3f}({t['npix']}) "
           + " | ".join(cols))
    prot = [i for i in det if obj[i]["protegida"]]
    for m in metodos:
        r = [out[i][m]["vrp_mw"] / obj[i]["mirova_vrp"] for i in prot if out[i][m]["vrp_mw"]]
        pr(f"  protegidas, port/MIROVA con {m:24s}: n {len(r)} de {len(prot)}, mediana "
           f"{np.median(r) if r else float('nan'):.3f}, rango [{min(r) if r else float('nan'):.3f}; "
           f"{max(r) if r else float('nan'):.3f}]")
    (AQUI / "03_ablacion_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
