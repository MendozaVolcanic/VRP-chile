# -*- coding: utf-8 -*-
"""S159, censo del oráculo, paso 5 (post hoc, descriptivo): el código de MIROVA también detecta fuera del recuadro de
21 x 21 (box == 0 entra como m0 con umbrales de escena, mirova_v750_r2.py l. 141-145; sólo el borde de la matriz se
excluye). El record sintético del pre-registro pone TODOS los alertados en un solo centroide, así que un píxel lejano
puede correr el centroide de una detección de cumbre (o al revés). Aquí se cuenta cuántas pasadas mezclan píxeles de
dentro y de fuera del recuadro, y si la publicación cambiaría con un record que sólo usa los píxeles del recuadro.
Pregunta 1: si no hubiera mezcla, la columna «cambia» da 0 por construcción; el control positivo es la detección de
Lastarria 2026-08-25 05:48 con centroide a 22,8 km (04_por_que_no_publica_salida.txt), que tiene que aparecer fuera.
Uso: python 05_pixeles_fuera_del_recuadro.py --art <censo> [<rescate>]
"""
import argparse, collections, importlib.util, json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
R = AQUI.parents[2]
sys.path.insert(0, str(R / "scripts")); sys.path.insert(0, str(R / "experiments/_s158_audit_r2/oraculo"))
spec = importlib.util.spec_from_file_location("cen", R / "experiments/_s159/n/07_censo_analizar.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
import banco_paridad as B
ap = argparse.ArgumentParser(); ap.add_argument("--art", nargs="+", required=True); a = ap.parse_args()
inner = B.inner_desde_html()
obj = {e["id"]: e for e in json.load(open(AQUI / "objetivos.json", encoding="utf-8"))}
res = {}
for d in a.art:
    for f in sorted(Path(d).rglob("resultados_*.json")):
        for r in json.load(open(f)):
            if r.get("estado") == "ok":
                res[r["id"]] = r
casos, idx, cnt = [], [], collections.Counter()
for i, r in res.items():
    for caja in ("geo_linear", "geo_linear_anillo_sensible"):
        o = r["oraculo"][caja]
        if not o.get("npix"):
            continue
        dentro = [p for p in o["pixeles"] if p[2] >= 1]
        fuera = [p for p in o["pixeles"] if p[2] == 0]
        cnt[(caja, obj[i]["lab"], "solo_dentro" if not fuera else ("solo_fuera" if not dentro else "mezcla"))] += 1
        if fuera:
            o2 = dict(o); o2["pixeles"] = dentro; o2["npix"] = len(dentro)
            # VRP del recorte: no se recalcula el fondo; se usa la fraccion de radiancia de los de dentro (aprox. declarada)
            if dentro:
                tot = sum(p[4] for p in o["pixeles"]); o2["vrp_mw"] = o["vrp_mw"] * sum(p[4] for p in dentro) / tot
            for et, oo in (("todo", o), ("recuadro", o2)):
                casos.append([C.record_oraculo(oo, inner[r["volcan"]], obj[i]["sensor"]), inner[r["volcan"]]])
                idx.append((i, caja, et))
print("pasadas con pixeles del oraculo por (caja, clase, region):", dict(sorted(cnt.items())))
P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))} if casos else {}
cambia = [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"], c, P[(i, c, "todo")], P[(i, c, "recuadro")])
          for (i, c, et) in idx if et == "todo" and P[(i, c, "todo")] != P[(i, c, "recuadro")]]
print("con pixeles fuera del recuadro:", sum(1 for x in idx if x[2] == "todo"),
      "| la publicacion cambia al quitar los de fuera:", len(cambia))
for x in cambia:
    print("  ", x)
