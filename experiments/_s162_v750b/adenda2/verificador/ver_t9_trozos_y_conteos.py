# -*- coding: utf-8 -*-
"""T9: sobre la lista sellada y la suplementaria del ensayo (C:\vrp-trabajo\temporales\v750b_supl_ensayo, main bd711db63):
(a) la lista del run es sellada + suplementaria, ids unicos, orden interno por granulo conservado;
(b) cuantos granulos sellados cambian de trozo (n % 32 sobre granulos ordenados) y cuantos granulos nuevos agrega;
(c) de que fuente sale la distancia de las alertas de la vara 3 (A119) y de las far_ref;
(d) cifras del parrafo 6 de la adenda.
Pregunta 1: si la lista del run no fuera la sellada + supl, (a) lo ve (igualdad exacta). Pregunta 2: control = comparar con
la lista sellada alterada en un objeto debe dar False."""
import collections
import json
from pathlib import Path

B = Path(r"C:\vrp-trabajo\temporales\v750b_supl_ensayo")
sell = json.loads((B / "experiments/_s162_v750b/objetivos_v750b.json").read_text(encoding="utf-8"))
sup = json.loads((B / "supl/objetivos_supl_v750b.json").read_text(encoding="utf-8"))
run = json.loads((B / "supl/objetivos_run_v750b.json").read_text(encoding="utf-8"))
print("(a) run[:n]==sellada", run[:len(sell)] == sell, "| run[n:]==supl", run[len(sell):] == sup, "| ids unicos",
      len({o['id'] for o in run}) == len(run), "| control (sellada alterada) igual:", run[:len(sell)] == sell[1:] + sell[:1])


def grupos(objs):
    g = {}
    for o in objs:
        g.setdefault(o.get("granule") or "~sin", []).append(o)
    return g


gs, gr = grupos(sell), grupos(run)
cs, cr = sorted(gs), sorted(gr)
print("(b) granulos sellados", len(cs), "| run", len(cr), "| nuevos", len(set(cr) - set(cs)),
      "| sellados que cambian de trozo", sum(1 for k in cs if cs.index(k) % 32 != cr.index(k) % 32),
      "| orden interno conservado", all([o['id'] for o in gs[k]] == [o['id'] for o in gr[k] if o['id'] < 100000] for k in cs))
for nombre, g, cl in (("sellada", gs, cs), ("run", gr, cr)):
    tam = [sum(len(g[k]) for n, k in enumerate(cl) if n % 32 == c) for c in range(32)]
    ng = [sum(1 for n, k in enumerate(cl) if n % 32 == c) for c in range(32)]
    print(f"    {nombre}: pasadas por trozo {min(tam)}..{max(tam)}, granulos por trozo {min(ng)}..{max(ng)}")
pos = [o for o in sell if o["lab"] == "pos"]
c = collections.Counter()
for o in pos:
    al = [f for f in o["mirova"] if f["tipo"].startswith("ALERTA") and f.get("dist_km") is not None]
    if al:
        c[(al[0]["source"], "antes del 2026-06-13" if o["hora_utc"] < "2026-06-13" else "desde el 2026-06-13")] += 1
print("(c) fuente de la distancia que toma la vara 3 en las pos (primera fila ALERTA con distancia):", dict(c), "total", sum(c.values()))
print("    far_ref: dist_ref igual a la primera fila FALSO_POSITIVO de la tabla en", sum(
    1 for o in sup if [f['dist_km'] for f in o['mirova'] if f['source'] == 'CONS' and f['tipo'].startswith('FALSO')][:1] == [o['dist_ref']]), "de", len(sup))
print("(d) volcanes", dict(collections.Counter(o['volcan'] for o in sup)), "| dist", min(o['dist_ref'] for o in sup), "a",
      max(o['dist_ref'] for o in sup), "| antes del 2026-06-13", sum(o['hora_utc'] < '2026-06-13' for o in sup),
      "| pub_prod", dict(collections.Counter(o['pub_prod'] for o in sup)), "| con fila OCR ademas",
      sum(any(f['source'] == 'OCR' for f in o['mirova']) for o in sup), "| 20/5841 =", round(20 / 5841 * 100, 2), "%")
