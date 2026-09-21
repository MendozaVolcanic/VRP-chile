# -*- coding: utf-8 -*-
"""Frente G S149: marcador rojo en el MAPA por volcan contra lo que PUBLICA el grafico/tarjeta.

MAPA_VISIBLE = (vrp_mw ?? vrp_mir_mw) > 0  y  distance_class != 'far'   (index.html:2820 y 2902,
               toggle por defecto "Solo crater")
PUBLICA      = mirovaEqVrp(inner) > 0 y no artefacto termico            (index.html:1043, 1236)
Ventana: checkout local de data/mirova_equivalent; ultimos 30 dias de cada archivo y toda la serie.
Instrumento: 1) si coincidieran, mapa_sin_publicar = 0: lo ve. 2) n impreso; control positivo:
PUBLICA > 0 en Lascar. Desglosa la causa de cada discrepancia.
"""
import io, sys, json, pathlib, collections, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.argv = sys.argv[:1]
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import predicados_por_vista as P  # noqa

tot = collections.Counter()
for vol, inner in P.INNER.items():
    d = json.loads((P.ROOT / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    ult = max(r["datetime_utc"] for r in recs)
    corte = (dt.datetime.fromisoformat(ult[:10]) - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    for r in recs:
        tramos = ["todo"] + (["30d"] if r["datetime_utc"] >= corte else [])
        mv = P.mapa(r) and r.get("distance_class") != "far"
        pu = P.eq(r, inner) > 0 and not P.artefacto(r, inner)
        causa = None
        if mv and not pu:
            pc = r.get("primary_cluster")
            if P.eq(r, inner) > 0:
                causa = "artefacto_termico"
            elif pc and (pc.get("centroid_dist_km") or 0) > inner:
                causa = "summit_con_cumulo_fuera_del_inner"
            elif pc and not (pc.get("vrp_mw") or 0) > 0:
                causa = "cumulo_en_cero"
            else:
                causa = "otra"
        for t in tramos:
            tot[(t, "n")] += 1
            tot[(t, "mapa_visible")] += mv
            tot[(t, "publica")] += pu
            tot[(t, "publica_sin_marcador")] += (pu and not mv)
            if causa:
                tot[(t, "mapa_sin_publicar")] += 1
                tot[(t, "causa:" + causa)] += 1
for t in ("todo", "30d"):
    print(t, {k: v for (tt, k), v in sorted(tot.items()) if tt == t})
