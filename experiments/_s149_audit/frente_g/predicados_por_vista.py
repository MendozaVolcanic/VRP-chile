# -*- coding: utf-8 -*-
"""Frente G S149: cuantos records trata distinto cada predicado del tablero.

Predicados (port literal del JS leido en frontend/index.html):
  MAPA      = (vrp_mw ?? vrp_mir_mw ?? 0) > 0                     index.html:2820 (capa de hotspots por volcan)
  VALIDA    = isValidDetection                                    index.html:1466
  PUBLICA   = mirovaEqVrp(r, inner, false) > 0 y no artefacto     index.html:1043 + 1236
Ventana: CHECKOUT LOCAL de data/mirova_equivalent (ojo: no es el remoto; sirve para proporciones,
no para frescura). Se reporta toda la serie y los ultimos 30 dias de cada archivo.

Preguntas del instrumento:
1. Si el mapa y el grafico usaran el mismo predicado, la celda MAPA-y-no-PUBLICA daria 0. Lo ve.
2. Instrumento muerto: se imprime n total por volcan; un n = 0 es SIN DATO. Control positivo:
   PUBLICA debe ser > 0 en Lascar (volcan con alertas conocidas).
"""
import io, sys, json, pathlib, datetime as dt, collections
ROOT = pathlib.Path(__file__).resolve().parents[3]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "Villarrica": 5, "PuyehueCordonCaulle": 20,
         "Copahue": 4, "NevadosDeChillan": 5, "Llaima": 5, "Chaiten": 5, "PlanchonPeteroa": 3, "Isluga": 5}


def eq(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw")
        if v is None:
            v = r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    if r.get("distance_class") and r["distance_class"] != "summit":
        return 0
    d = pc.get("centroid_dist_km")
    if d is not None and d > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def artefacto(r, inner):
    t = r.get("t_max_k")
    e = eq(r, inner)
    if t is not None and t < 273.15 and e > 10:
        return True
    pc = r.get("primary_cluster")
    if pc and t is not None and t < 278.15 and (pc.get("n_pixels") or 0) >= 100:
        return e >= 50 and e / pc["n_pixels"] < 1.0
    return False


def mapa(r):
    v = r.get("vrp_mw")
    if v is None:
        v = r.get("vrp_mir_mw")
    return (v or 0) > 0


def valida(r):
    pc = r.get("primary_cluster")
    if pc:
        return (pc.get("vrp_mw") or 0) > 0
    return (r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1") is True


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    tot = collections.Counter()
    for vol, inner in INNER.items():
        p = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) else d
        ult = max(r["datetime_utc"] for r in recs)
        corte = (dt.datetime.fromisoformat(ult[:10]) - dt.timedelta(days=30)).strftime("%Y-%m-%d")
        for tramo, sel in (("todo", recs), ("30d", [r for r in recs if r["datetime_utc"] >= corte])):
            c = collections.Counter()
            for r in sel:
                m, va = mapa(r), valida(r)
                pu = eq(r, inner) > 0 and not artefacto(r, inner)
                c["n"] += 1
                c["mapa"] += m
                c["valida"] += va
                c["publica"] += pu
                c["mapa_no_publica"] += (m and not pu)
                c["publica_no_mapa"] += (pu and not m)
                c["mapa_no_valida"] += (m and not va)
                c["publica_con_test1"] += (pu and r.get("triggered_test1") is True)
                c["publica_ancla_test1"] += (pu and r.get("final_hotspot_source") in ("test1_roi", "test1_nti_peak"))
                c["publica_con_f5"] += (pu and isinstance(r.get("f5_core_vrp_mw"), (int, float)))
            for k, v in c.items():
                tot[(tramo, k)] += v
            if tramo == "30d":
                print(f"{vol:22s} ultimo={ult} 30d: " + " ".join(f"{k}={v}" for k, v in c.items()))
    print()
    for tramo in ("todo", "30d"):
        print(tramo, {k: v for (t, k), v in tot.items() if t == tramo})
