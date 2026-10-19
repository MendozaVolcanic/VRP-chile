"""A4, instrumento propio del verificador (no usa alertas_protegidas, aplicar_d9 ni banco_paridad).

Lee los CSV crudos (ref fresca + historico + respaldo del worktree), arma las pasadas con alerta >= 1 MW
(lectura A: Tipo ALERTA_TERMICA / ALERTA_TERMICA_OCR, sin marca de sin geometria), y para cada una lista
TODOS nuestros records del mismo volcan y sensor a +-15 min, con el predicado del tablero evaluado por un
harness node propio sobre el record COMPLETO.
Uso: python a4_protegidas.py <worktree> <dir_ref> <salida.json>
"""
import csv, json, os, subprocess, sys, math
from collections import defaultdict
from datetime import datetime, timedelta, timezone

W, REF, OUT = sys.argv[1:4]
sys.path.insert(0, W)
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor  # preexistentes

DESDE, HASTA = "2026-08-20", "2026-10-19"
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5,
         "Chaiten": 5, "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
COORDS = {}
import yaml
for v in yaml.safe_load(open(os.path.join(W, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]:
    if v["name"] in INNER:
        COORDS[v["name"]] = (v["lat"], v["lon"])


def elev_solar(lat, lon, dt):
    """Elevacion solar aproximada (NOAA), implementacion propia."""
    doy = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (h - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    tst = h * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.asin(max(-1, min(1, cz))))


def filas(path, src):
    out = []
    if not os.path.exists(path):
        print("FALTA", path); return out
    for r in csv.DictReader(open(path, encoding="utf-8")):
        tipo = (r.get("Tipo_Registro") or "").strip()
        if tipo not in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR"):
            continue
        if (r.get("Metodo_Validacion") or "").strip().upper().find("SIN_GEOMETRIA") >= 0 or \
           "SIN_GEOMETRIA" in (r.get("Clasificacion Mirova") or "").upper():
            continue
        vol = normalize_volcano_name(r.get("Volcan"))
        f = (r.get("Fecha_Satelite_UTC") or "").strip()
        if vol not in INNER or len(f) < 16 or not (DESDE <= f[:10] <= HASTA):
            continue
        try:
            vrp = float(r.get("VRP_MW"))
        except (TypeError, ValueError):
            continue
        out.append({"vol": vol, "b": normalize_sensor(r.get("Sensor")), "f": f, "vrp": vrp, "src": src,
                    "tipo": tipo, "metodo": r.get("Metodo_Validacion")})
    return out


todas = (filas(os.path.join(REF, "registro_vrp_consolidado.csv"), "CONS")
         + filas(os.path.join(REF, "registro_vrp_ocr.csv"), "OCR")
         + filas(os.path.join(W, "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"), "HIST")
         + filas(os.path.join(W, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv"), "RESP"))
prot = defaultdict(list)
for f in todas:
    if f["vrp"] >= 1.0:
        prot[(f["vol"], f["b"], f["f"][:16])].append(f)
# alertas de cualquier VRP (para ver si una pasada >=1MW tiene vecinas en otro minuto)
print("filas alerta en ventana:", len(todas), " pasadas >=1MW:", len(prot))

recs = {}
for vol in INNER:
    recs[vol] = json.load(open(os.path.join(W, "data/mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"


casos, idx = [], []
filas_out = []
for k in sorted(prot, key=lambda x: (x[2], x[0], x[1])):
    vol, b, minuto = k
    fs = prot[k]
    dt = datetime.strptime(fs[0]["f"][:19] if len(fs[0]["f"]) >= 19 else fs[0]["f"][:16],
                           "%Y-%m-%d %H:%M:%S" if len(fs[0]["f"]) >= 19 else "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    lat, lon = COORDS[vol]
    el = elev_solar(lat, lon, dt)
    cand = []
    for r in recs[vol]:
        if bucket(r.get("sensor")) != b:
            continue
        try:
            rdt = datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        ds = (rdt - dt).total_seconds()
        if abs(ds) <= 900:
            idx.append((len(filas_out), len(cand)))
            casos.append([r, INNER[vol]])
            pc = r.get("primary_cluster") or {}
            cand.append({"dt": r["datetime_utc"], "dsec": ds, "sensor": r.get("sensor"),
                         "sha": (r.get("regimen") or {}).get("codigo_sha"),
                         "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                         "pc_dist": pc.get("centroid_dist_km"), "f5": r.get("f5_core_vrp_mw")})
    filas_out.append({"vol": vol, "b": b, "minuto": minuto, "fecha_seg": fs[0]["f"],
                      "vrp_max": max(x["vrp"] for x in fs), "fuentes": sorted({x["src"] for x in fs}),
                      "elev_sol": round(el, 1), "cand": cand})

tmp = os.path.join(os.path.dirname(OUT), "_casos_a4.json")
json.dump(casos, open(tmp, "w", encoding="utf-8"))
o = subprocess.run(["node", "--max-old-space-size=4096", os.path.join(os.path.dirname(OUT), "pred.js"),
                    os.path.join(W, "frontend/index.html"), tmp], capture_output=True, text=True)
if o.returncode:
    print(o.stderr); sys.exit(1)
pred = json.loads(o.stdout)
for (i, j), p in zip(idx, pred):
    filas_out[i]["cand"][j].update(p)
json.dump(filas_out, open(OUT, "w", encoding="utf-8"), indent=1, default=str)

print("\nPasadas >=1MW (lectura A) en", DESDE, HASTA, "; elev_sol>0 = diurna aprox; K = fecha>=2026-09-18")
for f in filas_out:
    det = "K" if f["minuto"][:10] >= "2026-09-18" else "C0"
    c120 = [c for c in f["cand"] if abs(c["dsec"]) <= 120]
    pub120 = any(c["pub"] for c in c120)
    estado = "sin_record" if not c120 else ("publicada" if pub120 else "SIN_PUBLICAR")
    otros = [c for c in f["cand"] if abs(c["dsec"]) > 120]
    print(f"{det} {f['minuto']} {f['vol']:<20} {f['b']:<8} {f['vrp_max']:6.2f} MW sol={f['elev_sol']:6.1f} "
          f"{'/'.join(f['fuentes']):<9} {estado:<12} n120={len(c120)} "
          f"shas={sorted({str(c['sha'])[:7] for c in c120})} otros15min={[(int(c['dsec']), c['pub']) for c in otros]}")
    if estado == "SIN_PUBLICAR":
        for c in c120:
            print("      ", c)
