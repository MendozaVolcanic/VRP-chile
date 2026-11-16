#!/usr/bin/env python
"""F2 S175: las protegidas VIIRS 375 no publicadas (salida de f2_banco_v375.py) vistas por dentro.

Para cada una: (a) que dice el record nuestro dentro del inner_radius (pixeles de anomaly_pixels a <= inner del crater
de volcanoes.yaml, su VRP y BT), para saber si la cumbre tenia calor y el cumulo elegido fue otro; (b) las filas de
MIROVA de esa pasada en los CSV crudos del snapshot (tipo, VRP, distancia, Ruta Foto = lamina, Version_OCR, cenit OCR),
con clase_mirova.protegida_de_crater (V375-A) para ver si la distancia es de su propia pasada; (c) las laminas que
mirova-tif-archive guardo de ese volcan VIIRS375 entre la pasada y 6 h despues (png_index.csv de insumos).
P1: si el record tuviera calor en la cumbre, la columna n_px_inner lo muestra. P2: si el record no se encontrara, lo
dice (no se cuenta como cero).
Uso: python perdidas_protegidas.py <arbol> <banco.json> <png_index.csv> <salida.txt>
"""
import csv, json, math, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); BANCO = json.load(open(sys.argv[2], encoding="utf-8")); PNG = sys.argv[3]; OUT = Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import yaml  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
vy = {v["name"]: v for v in yaml.safe_load(open(ARBOL / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
inner = BANCO["meta"]["inner"]


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


crudo = []
for path, src in ((SNAP_CONS, "CONS"), (SNAP_OCR, "OCR")):
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            crudo.append((src, r))
png = list(csv.DictReader(open(PNG, encoding="utf-8")))
pas = cm.resumir_pasadas(cargar_referencia_unificada(SNAP_CONS, SNAP_OCR), canal="union", regla_minimas="SN")
L = []
casos = BANCO["protegidas_no_publicadas"]
for x in casos:
    vol = x["vol"]; t = datetime.strptime(x["pasada_utc"], "%Y-%m-%d %H:%M")
    rec = next((r for r in json.load(open(ARBOL / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
                if r["datetime_utc"] == x["pasada_utc"] and r["sensor"] == x["sensor"]), None)
    L.append(f"=== {vol} {x['pasada_utc']} {x['sensor']} cenit {x['cenit']} tramo {x['tramo']} inner {inner[vol]} km")
    if rec is None:
        L.append("  RECORD NO ENCONTRADO"); continue
    vl, vo = vy[vol]["vent_lat"], vy[vol]["vent_lon"]
    px = rec.get("anomaly_pixels") or []
    pin = [(round(hav(vl, vo, p["lat"], p["lon"]), 2), p.get("vrp_mw"), p.get("bt_k")) for p in px
           if p.get("lat") is not None and hav(vl, vo, p["lat"], p["lon"]) <= inner[vol]]
    pc = rec.get("primary_cluster") or {}
    L.append(f"  nuestro: distance_class {rec.get('distance_class')} | pc vrp {pc.get('vrp_mw')} dist {pc.get('centroid_dist_km')} "
             f"n {pc.get('n_pixels')} | n_px total {len(px)} | n_px_inner {len(pin)} {sorted(pin)[:6]} | f5_core {rec.get('f5_core_vrp_mw')} "
             f"| final_hotspot_dist {rec.get('final_hotspot_dist_km')} | vrp_mw {rec.get('vrp_mw')}")
    clus = rec.get("clusters") or rec.get("all_clusters") or []
    if clus:
        L.append("  cumulos: " + "; ".join(f"vrp {c.get('vrp_mw')} dist {c.get('centroid_dist_km')} n {c.get('n_pixels')}" for c in clus[:6]))
    for src, r in crudo:
        if r["Fecha_Satelite_UTC"][:16] != x["pasada_utc"] or r["Sensor"] != "VIIRS375":
            continue
        if vol.lower()[:5] not in r["Volcan"].replace(" ", "").replace("-", "").lower():
            continue
        L.append(f"  MIROVA {src}: {r['Fecha_Satelite_UTC']} {r['Tipo_Registro']} VRP {r['VRP_MW']} dist {r['Distancia_km']} "
                 f"foto {r.get('Ruta Foto')} | OCR v{r.get('Version_OCR','')} cenitOCR {r.get('Zenith_Sat_deg','')} banner {r.get('Nivel_Anomalia_MIROVA','')} "
                 f"conf_geo {r.get('Confianza_Geometria','')} nota {(r.get('Nota_Validacion') or '')[:120]}")
    p = [q for q in pas if q.volcano == vol and q.sensor_bucket == "VIIRS375" and abs((q.instante - t).total_seconds()) <= 120]
    for q in p:
        ok, mot = cm.protegida_de_crater(q, inner[vol], x["sensor"])
        L.append(f"  resumir_pasadas: estado {q.estado} vrp {q.vrp_mw} dist {q.dist_km} fuente {q.fuente} solo_ocr {q.solo_ocr} "
                 f"| protegida A {cm.es_protegida(q)} | de_crater {ok} {mot}")
    tz = t.replace(tzinfo=timezone.utc)
    lam = [r["png_path"] for r in png if r["volcano"] == vol and r["sensor"] == "VIIRS375" and r["kind"] == "VRP"
           and tz <= datetime.fromisoformat(r["last_modified_utc"]) <= tz + timedelta(hours=6)]
    L.append(f"  laminas mirova-tif-archive VIIRS375 VRP en [pasada, +6 h]: {lam[:3]}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
