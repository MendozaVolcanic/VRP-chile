"""A2 y A3 con implementacion propia (sin banco_paridad, sin aplicar_d9, sin funciones nuevas del audit).

A2: falsas publicaciones = pasadas nuestras nocturnas en negativo limpio (fila RUTINA del consolidado con VRP 0
    a +-120 s, sin alerta ni falso positivo en la pasada ni en la noche del mismo volcan y sensor) que el tablero
    publica (harness node propio sobre el record completo). Ventana 2026-09-01..2026-10-19, por detector.
A3: recall crater del detector K = noches (vol, sensor, fecha UTC) con alerta nocturna de MIROVA, fecha >= frontera,
    en que hay record K, cuya fraccion tiene pc.vrp>0, <=50000 y centroid_dist<=inner. Ventana 2026-08-20..2026-10-19.
Uso: python a2a3_propio.py <worktree> <dir_ref> <dir_salida>
"""
import csv, json, math, os, subprocess, sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone

W, REF, OUTD = sys.argv[1:4]
sys.path.insert(0, W)
from pipeline.mirova_csv_loader import normalize_volcano_name, normalize_sensor, parse_ocr_distance  # noqa

FR = "2026-09-18"
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5,
         "Chaiten": 5, "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
import yaml
COORDS = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(open(os.path.join(W, "volcanoes.yaml"),
          encoding="utf-8"))["volcanoes"] if v["name"] in INNER}


def elev_solar(lat, lon, dt):
    doy = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (h - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    ha = math.radians((h * 60 + eqt + 4 * lon) / 4 - 180)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.asin(max(-1, min(1, cz))))


def ts(f):
    return datetime.strptime(f[:19] if len(f) >= 19 else f[:16],
                             "%Y-%m-%d %H:%M:%S" if len(f) >= 19 else "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def leer(path, src):
    out = {}
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path, encoding="utf-8")):
        vol = normalize_volcano_name(r.get("Volcan"))
        f = (r.get("Fecha_Satelite_UTC") or "").strip()
        if vol not in INNER or len(f) < 16:
            continue
        tipo = (r.get("Tipo_Registro") or "").strip()
        sin_geo = src == "OCR" and (tipo == "ALERTA_SIN_GEOMETRIA_OCR" or (
            ((r.get("Metodo_Validacion") or "").strip() == "vrp_sin_geometria_propia"
             or (r.get("Clasificacion Mirova") or "").strip() == "SIN_GEOMETRIA") and tipo.startswith("ALERTA")))
        try:
            vrp = float(str(r.get("VRP_MW")).strip())
        except (TypeError, ValueError):
            vrp = None
        fila = {"vol": vol, "b": normalize_sensor(r.get("Sensor")), "f": f, "src": src,
                "tipo": "SINGEO" if sin_geo else tipo, "vrp": vrp, "ua": (r.get("Ultima_Actualizacion") or "")}
        k = (vol, fila["b"], f[:16], src)
        if k not in out or fila["ua"] > out[k]["ua"]:
            out[k] = fila
    return out


ref = leer(os.path.join(REF, "registro_vrp_consolidado.csv"), "CONS")
for p, s in ((os.path.join(REF, "registro_vrp_ocr.csv"), "OCR"),
             (os.path.join(W, "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"), "CONS"),
             (os.path.join(W, "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv"), "CONS")):
    for k, v in leer(p, s).items():
        ref.setdefault(k, v)
filas = [f for f in ref.values() if "2026-08-15" <= f["f"][:10] <= "2026-10-19"]
ES_AL = lambda t: t in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")


def d9_sn(filas):
    """Regla SN propia: pasada (vol,b,minuto) minima si todas sus alertas son V375 con VRP<=0.05 y ninguna alerta
    no minima del mismo vol y sensor a <=120 s. Sus alertas pasan a RUTINA VRP 0."""
    mini = lambda f: f["b"] == "VIIRS375" and f["vrp"] is not None and f["vrp"] <= 0.05 + 1e-9
    pas = defaultdict(list); altas = defaultdict(list)
    for f in filas:
        if ES_AL(f["tipo"]):
            pas[(f["vol"], f["b"], f["f"][:16])].append(f)
            if not mini(f):
                altas[(f["vol"], f["b"])].append(ts(f["f"]))
    mins = set()
    for k, fs in pas.items():
        if all(mini(f) for f in fs) and not any(abs((a - ts(f["f"])).total_seconds()) <= 120
                                                for a in altas[(k[0], k[1])] for f in fs):
            mins.add(k)
    out = []
    for f in filas:
        if ES_AL(f["tipo"]) and (f["vol"], f["b"], f["f"][:16]) in mins:
            f = dict(f, tipo="RUTINA", vrp=0.0)
        out.append(f)
    return out, mins


def nocturna(f):
    lat, lon = COORDS[f["vol"]]
    return elev_solar(lat, lon, ts(f["f"])) <= 0


# ---- nuestros records
def bucket(s):
    s = s or ""
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"


recs, casos = [], []
for vol in INNER:
    for r in json.load(open(os.path.join(W, "data/mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc") or ""
        b = bucket(r.get("sensor"))
        if not b or not ("2026-08-20" <= dt[:10] <= "2026-10-19"):
            continue
        t = ts(dt)
        lat, lon = COORDS[vol]
        if elev_solar(lat, lon, t) > 0:
            continue
        sha = (r.get("regimen") or {}).get("codigo_sha")
        det = "K" if sha else ("C0" if dt[:10] < FR else "sin_marca")
        pc = r.get("primary_cluster") or {}
        v, cd = pc.get("vrp_mw") or 0.0, pc.get("centroid_dist_km")
        recs.append({"vol": vol, "b": b, "t": t, "noche": dt[:10], "det": det, "z": r.get("sensor_zenith_deg"),
                     "crater": 0 < v <= 50000 and cd is not None and cd <= INNER[vol]})
        casos.append([r, INNER[vol]])
tmp = os.path.join(OUTD, "_casos_a2.json")
json.dump(casos, open(tmp, "w", encoding="utf-8"))
o = subprocess.run(["node", "--max-old-space-size=6000", os.path.join(OUTD, "pred.js"),
                    os.path.join(W, "frontend/index.html"), tmp], capture_output=True, text=True, encoding="utf-8")
if o.returncode:
    print(o.stderr[-2000:]); sys.exit(1)
for r, p in zip(recs, json.loads(o.stdout)):
    r["pub"] = p["pub"]
os.remove(tmp)


def etiquetas(filas_reg):
    noc = [f for f in filas_reg if nocturna(f)]
    por_vb = defaultdict(list); ns = defaultdict(lambda: [False, False])
    for f in noc:
        por_vb[(f["vol"], f["b"])].append(f)
        d = ns[(f["vol"], f["b"], f["f"][:10])]
        d[0] |= ES_AL(f["tipo"]); d[1] |= f["tipo"].startswith("FALSO_POSITIVO")
    lab = {}
    for i, r in enumerate(recs):
        cerca = [f for f in por_vb[(r["vol"], r["b"])] if abs((ts(f["f"]) - r["t"]).total_seconds()) <= 120]
        al, fp = ns[(r["vol"], r["b"], r["noche"])]
        if any(ES_AL(f["tipo"]) for f in cerca):
            lab[i] = "pos"
        elif any(f["tipo"].startswith("FALSO_POSITIVO") for f in cerca):
            lab[i] = "far_ref"
        elif any(f["tipo"] == "RUTINA" and f["src"] == "CONS" and (f["vrp"] or 0) == 0 for f in cerca) \
                and not al and not fp:
            lab[i] = "neg"
        else:
            lab[i] = "sin_info"
    return lab


sn, mins = d9_sn(filas)
res = {}
for nombre, fr in (("SN", sn), ("original", filas)):
    lab = etiquetas(fr)
    tab = {}
    for det in ("C0", "K", "sin_marca"):
        for b in ("MODIS", "VIIRS750", "VIIRS375"):
            neg = [i for i, r in enumerate(recs) if lab[i] == "neg" and r["det"] == det and r["b"] == b
                   and "2026-09-01" <= r["noche"] <= "2026-10-19"]
            p = sum(recs[i]["pub"] for i in neg)
            tab[f"{det}|{b}"] = (len(neg), p, round(100 * p / len(neg), 1) if neg else None)
    res[nombre] = tab
    print(nombre, json.dumps(tab))

# ---- A3 recall crater K
def noches_alerta(filas_reg):
    s = set()
    for f in filas_reg:
        if ES_AL(f["tipo"]) and "2026-08-20" <= f["f"][:10] <= "2026-10-19" and nocturna(f):
            s.add((f["vol"], f["b"], f["f"][:10]))
    return s


por_noche = defaultdict(list)
for r in recs:
    por_noche[(r["vol"], r["b"], r["noche"])].append(r)
for nombre, fr in (("SN", sn), ("original", filas)):
    na = noches_alerta(fr)
    out = {}
    for det in ("K", "C0"):
        for b in ("MODIS", "VIIRS750", "VIIRS375"):
            ks = [k for k in na if k[1] == b and (k[2] >= FR) == (det == "K")]
            con = [k for k in ks if any(r["det"] == det for r in por_noche.get(k, []))]
            hit = [k for k in con if any(r["det"] == det and r["crater"] for r in por_noche[k])]
            out[f"{det}|{b}"] = (len(con), len(hit), round(100 * len(hit) / len(con), 1) if con else None,
                                 "sin_datos", len(ks) - len(con))
    print("recall", nombre, json.dumps(out))
    if nombre == "SN":
        perd = sorted(k for k in na if k[2] >= FR and any(r["det"] == "K" for r in por_noche.get(k, []))
                      and not any(r["det"] == "K" and r["crater"] for r in por_noche[k]))
        print("noches K con alerta y sin crater:", perd)
print("pasadas minimas D-9 (SN) en ventana:", len(mins))
