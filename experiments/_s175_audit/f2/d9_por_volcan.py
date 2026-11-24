#!/usr/bin/env python
"""F2 S175: por volcan, cuantos negativos limpios publicados (regla SN de D-9) eran alerta bajo la etiqueta original del
scraper, y con que magnitud nuestra (display del tablero). Responde: ¿la sobre-publicacion concentrada en Lastarria y
Puyehue es calor que MIROVA si listo con 0,05 MW o menos (D-9 lo vuelve «no vio nada») o calor donde MIROVA dio 0?
P1: si D-9 no tocara nada, la columna «era_pos» seria 0 en todos (el banco mostro 51 cambios a neg publicados, asi que
puede no ser 0). P2: n de neg limpios por volcan impreso.
Uso: python d9_por_volcan.py <arbol> <inicio> <fin> <salida.txt>
"""
import collections, json, os, statistics, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, OUT = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
recs = [r for r in bp.cargar_nuestros(coords, inner, (INI, FIN)) if r["b"] == "VIIRS375"]
lab = {}
for regla in ("original", "SN"):
    rr = [dict(r) for r in recs]
    bp.etiquetar(rr, *bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas=regla)[:3])
    lab[regla] = [r["lab"] for r in rr]
c = collections.defaultdict(collections.Counter); mags = collections.defaultdict(list)
for r, lo, ls in zip(recs, lab["original"], lab["SN"]):
    if ls != "neg_limpio":
        continue
    c[r["vol"]]["neg"] += 1
    if r["pub"]:
        c[r["vol"]]["neg_pub"] += 1; mags[r["vol"]].append(r["disp"] or 0)
        c[r["vol"]]["neg_pub_era_" + lo] += 1
L = [f"arbol {ARBOL.name} ventana {INI}..{FIN} V375 records nocturnos {len(recs)}"]
for vol in bp.VOLS:
    m = mags[vol]
    L.append(f"  {vol:20s} {dict(c[vol])} | display MW de los publicados: mediana {statistics.median(m):.3f} max {max(m):.3f}" if m
             else f"  {vol:20s} {dict(c[vol])}")
tot = collections.Counter()
for vol in c:
    tot.update(c[vol])
L.append("TOTAL " + json.dumps(dict(tot)))
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
