#!/usr/bin/env python
"""F2 S175: de los records V375 que el navegador marca «MIROVA confirmó» (+-60 min), cuantos tienen una fila de MIROVA
de SU pasada (+-TOL_S = 120 s) y cuantos solo la de otra pasada o solo filas de 0,05 MW o menos (D-9).

Es un PORT en Python de la regla de enrichWithMirovaConfirmation (frontend/index.html del arbol), usado solo para contar
el efecto de la tolerancia. Control de identidad: con +-60 min tiene que dar el mismo conteo que la funcion real
ejecutada con node en confirmado_navegador.py (3554 en V375 sobre 2026-03-01..2026-11-07 en la base); si no, el port no
vale y se dice. Uso: python confirmado_tolerancia.py <arbol> <inicio> <fin> <conteo_node_esperado> <salida.txt>
"""
import bisect, collections, json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]); INI, FIN, ESP, OUT = sys.argv[2], sys.argv[3], int(sys.argv[4]), Path(sys.argv[5])
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def ms(s):
    s = str(s).replace(" ", "T")
    return datetime.fromisoformat(s[:16]).replace(tzinfo=timezone.utc).timestamp()


c = collections.Counter(); por_vol = collections.defaultdict(collections.Counter)
for vol in VOLS:
    mir = json.load(open(ARBOL / "data" / "mirova" / f"{vol}.json", encoding="utf-8"))["records"]
    lst = []
    for m in mir:
        cls = str(m.get("clasificacion") or m.get("Clasificacion") or m.get("Clasificacion Mirova") or "").upper()
        if cls in ("NULO", "RUTINA"):
            continue
        try:
            v = float(m.get("VRP_MW") if m.get("VRP_MW") is not None else (m.get("vrp_mw") or 0))
        except (TypeError, ValueError):
            v = 0.0
        if not v > 0 or str(m.get("sensor") or m.get("Sensor") or "").upper() != "VIIRS375":
            continue
        lst.append((ms(m["datetime_utc"]), v))
    lst.sort(); ts = [x[0] for x in lst]
    for r in json.load(open(ARBOL / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        s = r.get("sensor") or ""
        if not s.startswith("VIIRS") or s.endswith("_750") or not (INI <= r["datetime_utc"][:10] <= FIN):
            continue
        t = ms(r["datetime_utc"])
        i, j = bisect.bisect_left(ts, t - 3600), bisect.bisect_right(ts, t + 3600)
        cerca = lst[i:j]
        if not cerca:
            continue
        c["conf_60min"] += 1; por_vol[vol]["conf_60min"] += 1
        propia = [v for (tt, v) in cerca if abs(tt - t) <= 120]
        if propia:
            c["con_fila_de_su_pasada"] += 1; por_vol[vol]["propia"] += 1
            if all(v <= 0.05 + 1e-9 for v in propia):
                c["su_pasada_solo_minimas"] += 1
        else:
            c["solo_otra_pasada"] += 1; por_vol[vol]["solo_otra"] += 1
        if all(v <= 0.05 + 1e-9 for (_, v) in cerca):
            c["solo_minimas_en_60min"] += 1
L = [f"arbol {ARBOL.name} ventana {INI}..{FIN} | control de identidad: port {c['conf_60min']} vs node {ESP} -> "
     + ("PASA" if c["conf_60min"] == ESP else "NO PASA: el port no vale"), json.dumps(dict(c))]
for vol in VOLS:
    L.append(f"  {vol:20s} {dict(por_vol[vol])}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
