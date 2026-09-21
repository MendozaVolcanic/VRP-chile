# -*- coding: utf-8 -*-
"""S149, FRENTE C. Para cada alerta de MIROVA que produccion NO publica: en que paso del predicado del
dashboard (ejecutado con node, A97) se cae. No propone arreglo: solo dice donde muere.

P1: si el predicado estuviera roto, la identidad de bp.control_identidad_predicado falla y se imprime.
P2: cada categoria lleva su n; las alertas publicadas se cuentan aparte (control positivo: existen).

Uso: python atribuir_perdidas.py SENSOR DESDE HASTA
"""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
bp = ev.bp
SENSOR, DESDE, HASTA = sys.argv[1:4]
ventana = (DESDE, HASTA)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
print("identidad del predicado:", bp.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0]))
filas = ev.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
# records crudos + salida completa del predicado
crudos, casos, meta = [], [], []
from datetime import datetime, timezone
for vol in bp.VOLS:
    d = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))
    for r in d["records"]:
        if bp.bucket(r.get("sensor")) != SENSOR or not (DESDE <= r.get("datetime_utc", "")[:10] <= HASTA):
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        ff = bp.parear(por_vb.get((vol, SENSOR), []), dt)
        al = [f for f in ff if bp.es_alerta(f["tipo"])]
        if not al:
            continue
        al.sort(key=lambda f: f["source"] != "CONS")
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for q in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner[vol]]); meta.append((vol, dt, al[0]["vrp_mw"], al[0]["source"], r))
pred = bp.correr_node(casos)
cat = collections.Counter(); porvol = collections.defaultdict(collections.Counter); lineas = []
for (vol, dt, vref, src, r), (summit, valid, art, disp, pub) in zip(meta, pred):
    pc = r.get("primary_cluster") or {}
    if pub:
        c = "PUBLICA"
    elif not (r.get("n_anomalous_pixels") or 0) and not pc:
        c = "sin deteccion (0 pixeles, sin cumulo)"
    elif not summit:
        c = "hay deteccion pero distance_class no es summit"
    elif not valid:
        c = "summit pero isValidDetection falso"
    elif art:
        c = "summit y valida pero marcada artefacto"
    else:
        c = "summit, valida, no artefacto, display 0"
    cat[c] += 1; porvol[vol][c] += 1
    if not pub:
        lineas.append("   %-18s %s | MIROVA %.2f MW (%s) | regimen %s | dc %s | n_px %s | pc.vrp %s | pc.dist %s | vrp_mw %s | t1 %s | z %s | descartado %s" % (
            vol, dt.strftime("%Y-%m-%d %H:%M"), vref or 0, src, "post535" if dt.strftime("%Y-%m-%d %H") >= "2026-08-28 23" else "pre535",
            r.get("distance_class"), r.get("n_anomalous_pixels"), pc.get("vrp_mw"), pc.get("centroid_dist_km"), r.get("vrp_mw"),
            r.get("triggered_test1"), r.get("sensor_zenith_deg"), r.get("discarded_reason")))
print("sensor", SENSOR, "| ventana", ventana, "| alertas de MIROVA con record nuestro:", len(meta))
for c, n in cat.most_common():
    print("  %3d  %s" % (n, c))
print("por volcan:", {v: dict(c) for v, c in porvol.items()})
print("\n".join(lineas[:80]))
