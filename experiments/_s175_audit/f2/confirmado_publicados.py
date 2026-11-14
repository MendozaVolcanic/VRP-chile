#!/usr/bin/env python
"""F2 S175: lo mismo que confirmado_tolerancia.py pero solo sobre los records V375 que el tablero PUBLICA (predicado
con node, banco_paridad.cargar_nuestros). Mismo port de la regla de confirmacion (su control de identidad contra la
funcion real con node esta en confirmado_tolerancia_base_salida.txt). Uso:
python confirmado_publicados.py <arbol> <inicio> <fin> <salida.txt>"""
import bisect, collections, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, OUT = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402


def ms(s):
    return datetime.fromisoformat(str(s).replace(" ", "T")[:16]).replace(tzinfo=timezone.utc).timestamp()


recs = [r for r in bp.cargar_nuestros(bp._coords_por_volcan(), bp.inner_desde_html(), (INI, FIN)) if r["b"] == "VIIRS375" and r["pub"]]
c = collections.Counter()
lst = {}
for vol in bp.VOLS:
    x = []
    for m in json.load(open(ARBOL / "data" / "mirova" / f"{vol}.json", encoding="utf-8"))["records"]:
        cls = str(m.get("clasificacion") or m.get("Clasificacion") or m.get("Clasificacion Mirova") or "").upper()
        try:
            v = float(m.get("VRP_MW") if m.get("VRP_MW") is not None else (m.get("vrp_mw") or 0))
        except (TypeError, ValueError):
            v = 0.0
        if cls in ("NULO", "RUTINA") or not v > 0 or str(m.get("sensor") or "").upper() != "VIIRS375":
            continue
        x.append((ms(m["datetime_utc"]), v))
    x.sort(); lst[vol] = x
for r in recs:
    x = lst[r["vol"]]; ts = [a for a, _ in x]; t = r["dt"].timestamp()
    cerca = x[bisect.bisect_left(ts, t - 3600):bisect.bisect_right(ts, t + 3600)]
    c["publicados"] += 1
    if not cerca:
        continue
    c["confirmado_navegador"] += 1
    propia = [v for a, v in cerca if abs(a - t) <= 120]
    if not propia:
        c["sin_fila_de_su_pasada"] += 1
    elif all(v <= 0.05 + 1e-9 for v in propia):
        c["su_pasada_solo_minimas"] += 1
    if all(v <= 0.05 + 1e-9 for _, v in cerca):
        c["solo_minimas_en_60min"] += 1
L = [f"arbol {ARBOL.name} ventana {INI}..{FIN} V375 publicados (node)", json.dumps(dict(c))]
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
