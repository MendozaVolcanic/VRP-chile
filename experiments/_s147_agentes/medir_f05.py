# -*- coding: utf-8 -*-
"""F-05: cuanto se mueve la razon de magnitud si publicaramos la suma en vez del nucleo.

Solo lectura. Reusa los pareadores del repo (referencia_mirova_unificada, banco_paridad)
y el predicado del dashboard ejecutado con node (A97).
"""
from __future__ import annotations
import bisect, collections, json, os, statistics, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
from referencia_mirova_unificada import cargar_referencia_unificada
from banco_paridad import bucket, correr_node, inner_desde_html, VOLS, TOL_S

DATA = ROOT / "data" / "mirova_equivalent"
CORTE = datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc)  # #535


def es_alerta(t): return t.startswith("ALERTA")


def main():
    ini, fin = sys.argv[1], sys.argv[2]
    coords, inner = _coords_por_volcan(), inner_desde_html()
    filas = cargar_referencia_unificada()

    # referencia: solo ALERTAS con VRP > 0, nocturnas, en ventana
    por_vb = collections.defaultdict(list)
    for f in filas:
        if not (ini <= f["fecha_utc"][:10] <= fin):
            continue
        if not es_alerta(f["tipo"]):
            continue
        try:
            v = float(f.get("vrp_mw") or 0)
        except (TypeError, ValueError):
            continue
        if v <= 0:
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[f["volcano"]]
        if es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
            continue
        por_vb[(f["volcano"], f["sensor_bucket"])].append((dt, v))
    for lst in por_vb.values():
        lst.sort(key=lambda x: x[0])
    print("filas de referencia ALERTA con VRP>0 en ventana:", sum(len(v) for v in por_vb.values()))

    CAMPOS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason",
              "triggered_test1", "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw",
              "anomaly_pixels"]
    recs, casos = [], []
    for vol in VOLS:
        d = json.loads((DATA / f"{vol}.json").read_text(encoding="utf-8"))
        for r in d["records"]:
            b = bucket(r.get("sensor"))
            if b is None or not (ini <= r.get("datetime_utc", "")[:10] <= fin):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            # pareo con la referencia
            lst = por_vb.get((vol, b), [])
            ts = [x[0] for x in lst]
            i = bisect.bisect_left(ts, dt - timedelta(seconds=TOL_S))
            ref = [lst[j][1] for j in range(i, len(lst)) if lst[j][0] <= dt + timedelta(seconds=TOL_S)]
            if not ref:
                continue
            ap = r.get("anomaly_pixels") or []
            pc = r.get("primary_cluster") or {}
            recs.append({
                "vol": vol, "b": b, "dt": dt, "ref": max(ref),
                "scene": r.get("vrp_mw"), "pc": pc.get("vrp_mw"), "f5": r.get("f5_core_vrp_mw"),
                "sum_ap": sum(p.get("vrp_mw") or 0 for p in ap),
                "n_ap": len(ap), "n_anom": r.get("n_anomalous_pixels"),
                "pc_n": pc.get("n_pixels"),
            })
            slim = {k: r.get(k) for k in CAMPOS if k != "anomaly_pixels"}
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in ap]
            casos.append([slim, inner[vol]])

    print("pares nuestros-MIROVA:", len(recs))
    pred = correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]

    pubs = [r for r in recs if r["pub"] == 1]
    print("de esos, PUBLICADOS por el dashboard:", len(pubs))

    def med(xs): return statistics.median(xs) if xs else None

    for etiqueta, sel in [("TODA LA VENTANA", pubs),
                          ("ANTES de #535", [r for r in pubs if r["dt"] < CORTE]),
                          ("DESDE #535", [r for r in pubs if r["dt"] >= CORTE])]:
        print("\n" + "=" * 78)
        print(etiqueta, " n =", len(sel), " (%s a %s)" % (ini, fin))
        print("=" * 78)
        print(f"{'sensor':10} {'n':>4} {'razon PUBLICADA':>16} {'razon suma_px':>14} "
              f"{'razon escena':>13} {'razon cumulo':>13} {'%truncado':>10}")
        for b in ["MODIS", "VIIRS375", "VIIRS750", "TODOS"]:
            s = sel if b == "TODOS" else [r for r in sel if r["b"] == b]
            if not s:
                continue
            trunc = sum(1 for r in s if (r["n_anom"] or 0) > r["n_ap"])
            print(f"{b:10} {len(s):>4} "
                  f"{med([r['disp'] / r['ref'] for r in s]):>16.3f} "
                  f"{med([r['sum_ap'] / r['ref'] for r in s]):>14.3f} "
                  f"{med([(r['scene'] or 0) / r['ref'] for r in s]):>13.3f} "
                  f"{med([(r['pc'] or 0) / r['ref'] for r in s]):>13.3f} "
                  f"{100.0 * trunc / len(s):>9.1f}%")

    # diagnostico de truncamiento y de cuanto agrega la suma
    print("\n--- diagnostico de la lista anomaly_pixels (sobre los publicados, toda la ventana) ---")
    for b in ["MODIS", "VIIRS375", "VIIRS750"]:
        s = [r for r in pubs if r["b"] == b]
        if not s:
            continue
        trunc = [r for r in s if (r["n_anom"] or 0) > r["n_ap"]]
        print(f"{b:10} n={len(s):>4}  con n_anomalous_pixels > len(anomaly_pixels): {len(trunc)} "
              f"({100.0*len(trunc)/len(s):.1f}%)  mediana n_anom={med([r['n_anom'] or 0 for r in s]):.0f} "
              f"mediana len(ap)={med([r['n_ap'] for r in s]):.0f} "
              f"mediana n_pixels del cumulo={med([r['pc_n'] or 0 for r in s]):.0f}")

    json.dump([{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items()} for r in recs],
              open(sys.argv[3], "w", encoding="utf-8"))
    print("\nescrito:", sys.argv[3])


main()
