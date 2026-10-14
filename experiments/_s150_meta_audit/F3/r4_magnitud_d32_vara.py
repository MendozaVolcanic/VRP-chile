# -*- coding: utf-8 -*-
"""F3 R4. Re-mide la razon de magnitud de la rebaja de A10 / D32 (docs/audit_s147/VERIFICADOR_F_05.md §1:
1.512 pares publicados, VIIRS 375 publicado 0,706, suma 0,783, ventana 2026-03-01 a 2026-09-20, referencia
CONS mas OCR) con la vara corregida. Copia la logica de experiments/_s147_agentes/medir_f05.py sin tocarlo
(ese script llama a main() al importarse).

Varas de referencia:
  L0 CONS+OCR (como F-05): ref = max(VRP de las alertas pareadas, de cualquier canal).
  L1 CONS sola.
  L2 A119+S150: CONS siempre; OCR solo desde 2026-06-13 y nunca si nuestra pasada es Suomi NPP.
P1: si el OCR desplazara la razon, L0 y L1 diferirian en la mediana. P2: L0 tiene que reproducir el n y las
medianas publicadas (1.512; 0,706 y 0,783), salvo que el corpus haya cambiado; se imprime para decidir.
Ventana de los DATOS: 2026-03-01 a 2026-09-20, nocturno, 11 Tier A."""
import bisect, collections, json, os, statistics, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada
from referencia_mirova_unificada import cargar_referencia_unificada
from banco_paridad import bucket, correr_node, inner_desde_html, VOLS, TOL_S
INI, FIN = "2026-03-01", "2026-09-20"
coords, inner = _coords_por_volcan(), inner_desde_html()
por_vb = collections.defaultdict(list)
for f in cargar_referencia_unificada():
    if not (INI <= f["fecha_utc"][:10] <= FIN) or not f["tipo"].startswith("ALERTA"):
        continue
    v = f.get("vrp_mw") or 0
    if v <= 0:
        continue
    dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    lat, lon = coords[f["volcano"]]
    if es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
        continue
    por_vb[(f["volcano"], f["sensor_bucket"])].append((dt, v, f["source"]))
for l in por_vb.values():
    l.sort(key=lambda x: x[0])
CAMPOS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason", "triggered_test1",
          "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw", "anomaly_pixels"]
recs, casos = [], []
for vol in VOLS:
    d = json.loads((RAIZ / "data" / "mirova_equivalent" / f"{vol}.json").read_text(encoding="utf-8"))
    for r in d["records"]:
        b = bucket(r.get("sensor"))
        if b is None or not (INI <= r.get("datetime_utc", "")[:10] <= FIN):
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        lat, lon = coords[vol]
        if es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        lst = por_vb.get((vol, b), [])
        ts = [x[0] for x in lst]
        i = bisect.bisect_left(ts, dt - timedelta(seconds=TOL_S))
        ref = [lst[j] for j in range(i, len(lst)) if lst[j][0] <= dt + timedelta(seconds=TOL_S)]
        if not ref:
            continue
        ap = r.get("anomaly_pixels") or []
        recs.append({"vol": vol, "b": b, "dt": dt, "ref": ref, "plat": r.get("sensor"),
                     "sum_ap": sum(p.get("vrp_mw") or 0 for p in ap)})
        slim = {k: r.get(k) for k in CAMPOS if k != "anomaly_pixels"}
        slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for p in ap]
        casos.append([slim, inner[vol]])
pred = correr_node(casos) if casos else []
for rec, p in zip(recs, pred):
    rec["disp"], rec["pub"] = p[3], p[4]
pubs = [r for r in recs if r["pub"] == 1]
VARAS = {"L0_cons_ocr": lambda r, x: True, "L1_cons_sola": lambda r, x: x[2] == "CONS",
         "L2_A119_S150": lambda r, x: x[2] == "CONS" or (x[0].strftime("%Y-%m-%d") >= "2026-06-13" and "SNPP" not in str(r["plat"]).upper())}
med = statistics.median
print("pares con alguna alerta (cualquier canal):", len(recs), "| publicados:", len(pubs))
for nombre, f in VARAS.items():
    print("\n==", nombre)
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        s = []
        for r in pubs:
            if r["b"] != b:
                continue
            refs = [x[1] for x in r["ref"] if f(r, x)]
            if refs:
                s.append((r, max(refs)))
        if not s:
            continue
        print("  %-8s n %4d | razon publicada %.3f | razon suma de pixeles %.3f" % (
            b, len(s), med([r["disp"] / v for r, v in s]), med([r["sum_ap"] / v for r, v in s])))
    tot = sum(1 for r in pubs if any(f(r, x) for x in r["ref"]))
    print("  total publicados con referencia bajo esta vara:", tot)
    if nombre == "L2_A119_S150":
        porv = collections.defaultdict(list)
        for r in pubs:
            refs = [x[1] for x in r["ref"] if f(r, x)]
            if r["b"] == "VIIRS375" and refs:
                porv[r["vol"]].append((r["disp"] / max(refs), r["sum_ap"] / max(refs)))
        for v, l in sorted(porv.items(), key=lambda kv: -len(kv[1])):
            print("     %-20s n %3d publicada %.3f suma %.3f" % (v, len(l), med([a for a, _ in l]), med([c for _, c in l])))
