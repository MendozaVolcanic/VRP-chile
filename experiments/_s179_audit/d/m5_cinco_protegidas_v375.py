# -*- coding: utf-8 -*-
"""M5 (frente D, S179). Detalle de las pasadas VIIRS 375 que M4 marco como «protegida de MIROVA que K publica y el
record de la via no publica» (ventanas F26 y DM, artefactos D2).

Para cada pasada imprime: las filas de la referencia de 438a60a1e a +-120 s (fuente tabla u OCR, VRP, distancia), el
record K de produccion y el record de la via (clase de distancia, VRP del cumulo, distancia del cumulo, punto final), y
lo que da el predicado del tablero en cada uno (summit, valid, artefacto, VRP mostrado, publica).

Las dos preguntas del instrumento:
1. Si la perdida fuera un artefacto de mi medicion (por ejemplo una fila OCR con la distancia de otra pasada), este
   detalle lo dejaria ver?  En parte: muestra la fuente de cada fila y si hay fila de la tabla. No abre la imagen de MIROVA.
2. Si el instrumento estuviera muerto?  Control: para cada pasada se imprime tambien el record K, que el predicado
   tiene que dar como publicado (si no, M4 y M5 no hablan de la misma pasada).

Uso: python m5_cinco_protegidas_v375.py <snapshot main> <carpeta base> <carpeta union> <m4_salida.json> <salida.json>
"""
import sys, io, os, json
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MAIN, BASE, UNION, M4, OUT = sys.argv[1:6]
sys.path.insert(0, MAIN)
sys.path.insert(0, os.path.join(MAIN, "scripts"))
OUT = os.path.abspath(OUT)   # la salida va a la carpeta desde donde se llama, no a la instantanea del codigo
M4 = os.path.abspath(M4)
os.chdir(MAIN)
import banco_paridad as bp
import referencia_mirova_unificada as rmu
import clase_mirova as cm
import vigilancia_sombra as vs
aa = vs.aa
PROD = Path(BASE) / "data" / "mirova_equivalent"
filas = rmu.cargar_referencia_unificada(
    os.path.join(BASE, "latest_consolidado.csv"),
    os.path.join(BASE, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv"),
    respaldo_path=Path(BASE) / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv",
    historico_path=Path(BASE) / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv")
inner = bp.inner_desde_html()
m4 = json.load(open(M4, encoding="utf-8"))
casos = []
for nombre, fila in m4["ventanas"].items():
    for f in ("MODIS", "VIIRS375", "VIIRS750"):
        for x in fila[f]["protegidas_K_publica_y_via_calla"] + fila[f]["protegidas_K_publica_y_via_sin_record"]:
            casos.append((nombre, f, x[0], x[1], x[2]))

CAMPOS = ["sensor", "datetime_utc", "distance_class", "vrp_mw", "final_hotspot_dist_km", "final_hotspot_source",
          "via_codigo_mirova", "sensor_zenith_deg", "n_hotspots", "f5_core_vrp_mw", "product_version"]


def cerca(recs, t, b):
    out = []
    for r in recs:
        if bp.bucket(r.get("sensor")) != b:
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if abs((dt - t).total_seconds()) <= bp.TOL_S:
            out.append(r)
    return out


def resumen(r):
    pc = r.get("primary_cluster") or {}
    d = {k: r.get(k) for k in CAMPOS}
    d["pc_vrp_mw"] = pc.get("vrp_mw")
    d["pc_centroid_dist_km"] = pc.get("centroid_dist_km")
    d["pc_n_pixels"] = pc.get("n_pixels")
    d["n_anomaly_pixels"] = len(r.get("anomaly_pixels") or [])
    return d


def predicado(r, vol):
    slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    if r.get("f5_core_vrp_mw") is None:
        slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in (r.get("anomaly_pixels") or [])]
    s, v, a, disp, pub = bp.correr_node([[slim, inner[vol]]])[0]
    return {"summit": s, "valid": v, "artefacto": a, "vrp_mostrado": disp, "publica": pub}


salida = []
for nombre, f, vol, minuto, vrp in casos:
    t = datetime.strptime(minuto, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    ref = [x for x in filas if x["volcano"] == vol and x["sensor_bucket"] == f
           and abs((datetime.strptime(x["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) - t).total_seconds()) <= bp.TOL_S + 60]
    k = cerca(json.loads((PROD / (vol + ".json")).read_text(encoding="utf-8"))["records"], t, f)
    v = cerca(json.loads((Path(UNION) / (vol + ".json")).read_text(encoding="utf-8"))["records"], t, f)
    item = {"ventana": nombre, "familia": f, "volcan": vol, "minuto_mirova": minuto, "vrp_mirova_mw": vrp, "inner_km": inner[vol],
            "referencia": [{kk: x.get(kk) for kk in ("fecha_utc", "tipo", "source", "origen", "vrp_mw", "dist_km", "sensor")} for x in ref],
            "protegida_por_fila": [bool(cm.alerta_protegida(x)) for x in ref],
            "K": [dict(resumen(r), predicado=predicado(r, vol)) for r in k],
            "via": [dict(resumen(r), predicado=predicado(r, vol)) for r in v]}
    salida.append(item)
    print(f"\n=== {nombre} {f} {vol} {minuto} UTC, MIROVA {vrp} MW (radio interno del tablero {inner[vol]} km) ===")
    for x, p in zip(item["referencia"], item["protegida_por_fila"]):
        print("  REF:", x, "protegida" if p else "")
    for r in item["K"]:
        print("  K  :", r)
    for r in item["via"]:
        print("  VIA:", r)
ok = all(any(r["predicado"]["publica"] for r in it["K"]) for it in salida)
print("\nCONTROL (el record K de cada pasada sale publicado por el predicado):", "OK" if ok else "FALLA")
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(salida, fh, indent=1, ensure_ascii=False, default=str)
