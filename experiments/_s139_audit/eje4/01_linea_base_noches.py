"""S139 eje 4: linea base por noche de volcan, 11 Tier A x 3 sensores, predicado del dashboard.

Preguntas del instrumento:
1. Si el predicado estuviera roto (p.ej. todo summit), la variante "por cumulo" lo mostraria
   distinto: se reportan las dos lado a lado.
2. Instrumento muerto: control de fechas barajadas (recall con noches ALERTA desplazadas 183 dias)
   debe caer hacia la tasa de negativos. Si no cae, el instrumento no distingue senal.
SIN DATO: noche sin pasada nuestra del sensor no cuenta ni como acierto ni como perdida.
Unidad: noche local = fecha(datetime_utc - 12 h). Ventana: interseccion de nuestros records con el CSV.
Referencia: CONS U OCR del snapshot (pipeline.mirova_csv_loader). Negativo = noche con fila RUTINA
de MIROVA para ese volcan y sin ALERTA en ningun sensor.
"""
import csv, json, sys, io
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from pipeline.mirova_csv_loader import load_mirova_alertas, normalize_volcano_name  # noqa
import yaml

SNAP = REPO / "data/mirova_reference/mirova_v1_snapshot"
CONS, OCR = SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv"
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]

vy = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
vlist = vy["volcanoes"] if isinstance(vy, dict) and "volcanoes" in vy else vy
inner = {}
for v in vlist:
    inner[v.get("name") or v.get("id")] = v.get("inner_radius_km", 10)


def night(dt):
    return (dt - timedelta(hours=12)).date()


def bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


def mirova_eq_vrp(r, ik):
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    if r.get("distance_class") and r["distance_class"] != "summit":
        return 0
    if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > ik:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def is_summit(r):
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    if r.get("distance_class") == "summit":
        return True
    if r.get("distance_class") == "far":
        return False
    return (r.get("vrp_vent_mw") or 0) > 0


def dash(r, ik):
    return is_summit(r) and mirova_eq_vrp(r, ik) > 0


def cumulo(r, ik):
    pc = r.get("primary_cluster")
    return bool(pc) and (pc.get("vrp_mw") or 0) > 0 and (pc.get("centroid_dist_km") or 1e9) <= ik


# referencia: noches con RUTINA por volcan (cualquier sensor) y noches ALERTA por volcan y sensor
rutina = defaultdict(set)
ref_min, ref_max = None, None
for path in (CONS, OCR):
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vol = normalize_volcano_name(row.get("Volcan"))
            if not vol:
                continue
            try:
                dt = datetime.strptime(row["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            ref_min = dt if ref_min is None or dt < ref_min else ref_min
            ref_max = dt if ref_max is None or dt > ref_max else ref_max
            if (row.get("Tipo_Registro") or "").strip() == "RUTINA":
                rutina[vol].add(night(dt))

out = {"ventana_ref": [str(ref_min), str(ref_max)], "vol": {}}
tot = defaultdict(lambda: defaultdict(int))
for vol in FOCAL + NEVADO:
    ik = inner.get(vol, 10)
    alerts = load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=vol)
    al_s = defaultdict(set)
    al_any = set()
    for a in alerts:
        dt = a["timestamp"] if isinstance(a["timestamp"], datetime) else datetime.utcfromtimestamp(int(a["timestamp"]))
        n = night(dt)
        al_s[a["sensor_bucket"]].add(n)
        al_any.add(n)
    recs = json.load(open(REPO / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]
    have = defaultdict(set)
    det_d = defaultdict(set)
    det_c = defaultdict(set)
    for r in recs:
        dt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
        if ref_min and not (ref_min <= dt <= ref_max + timedelta(days=1)):
            continue
        b, n = bucket(r["sensor"]), night(dt)
        have[b].add(n); have["ANY"].add(n)
        if dash(r, ik):
            det_d[b].add(n); det_d["ANY"].add(n)
        if cumulo(r, ik):
            det_c[b].add(n); det_c["ANY"].add(n)
    al_s["ANY"] = al_any
    res = {"inner_km": ik}
    for b in ("MODIS", "VIIRS750", "VIIRS375", "ANY"):
        pos_own = al_s.get(b, set()) & have[b]          # positivo por su propio sensor
        pos_any = al_any & have[b]                       # positivo por cualquier sensor MIROVA
        neg = (rutina[vol] - al_any) & have[b]
        shuf = {d + timedelta(days=183) for d in al_s.get(b, set())} & have[b] - al_any
        res[b] = {
            "pos_propio": len(pos_own), "rec_dash_propio": len(pos_own & det_d[b]), "rec_cum_propio": len(pos_own & det_c[b]),
            "pos_any": len(pos_any), "rec_dash_any": len(pos_any & det_d[b]), "rec_cum_any": len(pos_any & det_c[b]),
            "neg": len(neg), "fp_dash": len(neg & det_d[b]), "fp_cum": len(neg & det_c[b]),
            "ctrl_barajado_n": len(shuf), "ctrl_barajado_dash": len(shuf & det_d[b]),
            "noches_con_pasada": len(have[b]),
        }
        reg = "focal" if vol in FOCAL else "nevado"
        for k, v in res[b].items():
            if isinstance(v, int):
                tot[f"{reg}_{b}"][k] += v
    out["vol"][vol] = res
out["totales"] = tot
(Path(__file__).parent / "out").mkdir(exist_ok=True)
json.dump(out, open(Path(__file__).parent / "out/linea_base_noches.json", "w"), indent=1, default=str)
print("ventana ref", out["ventana_ref"])
hdr = "vol sensor pos_propio rec_dash rec_cum | pos_any rec_dash rec_cum | neg fp_dash fp_cum | barajado n/dash"
print(hdr)
for vol, res in out["vol"].items():
    for b in ("MODIS", "VIIRS750", "VIIRS375", "ANY"):
        x = res[b]
        print(vol, b, x["pos_propio"], x["rec_dash_propio"], x["rec_cum_propio"], "|", x["pos_any"], x["rec_dash_any"], x["rec_cum_any"], "|",
              x["neg"], x["fp_dash"], x["fp_cum"], "|", x["ctrl_barajado_n"], x["ctrl_barajado_dash"])
print("TOTALES")
for k, x in tot.items():
    print(k, dict(x))
