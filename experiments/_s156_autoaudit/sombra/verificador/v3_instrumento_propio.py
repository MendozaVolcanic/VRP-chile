# Verificador S156 (instrumento propio, NO importa vigilancia_sombra): toda pasada de MIROVA con fila de
# alerta (cualquier tipo ALERTA*, tambien SIN_GEOMETRIA, y FALSO_POSITIVO para lectura B) en la ventana, de dia
# o de noche, contra produccion (records con regimen.codigo_sha) y sombra (data/experimental_v2), pareo
# a varias tolerancias. "Publica" = predicado del tablero con node (banco_paridad.correr_node, solo el arnes JS).
# Uso: python v3_instrumento_propio.py <worktree> <dir_ref>
import csv, json, sys, math, collections
from datetime import datetime, timezone, timedelta
from pathlib import Path
W = Path(sys.argv[1]); REF = Path(sys.argv[2])
sys.path.insert(0, str(W)); sys.path.insert(0, str(W / "scripts"))
import banco_paridad as bp   # solo correr_node, CAMPOS_JS, inner_desde_html, bucket
import yaml
WIN = ("2026-09-18", "2026-10-19")
NOMBRE = {"Chaiten": "Chaiten", "Copahue": "Copahue", "Isluga": "Isluga", "Lascar": "Lascar", "Lastarria": "Lastarria",
          "Llaima": "Llaima", "Nevados de Chillan": "NevadosDeChillan", "PlanchonPeteroa": "PlanchonPeteroa",
          "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Tupungatito": "Tupungatito", "Villarrica": "Villarrica"}
SENS = {"MODIS": "MODIS", "VIIRS": "VIIRS750", "VIIRS375": "VIIRS375"}
COORD = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(open(W / "volcanoes.yaml", encoding="utf-8"))["volcanoes"] if "lat" in v}


def sol(lat, lon, dt):
    """Elevacion solar (formula NOAA, ~0,5 grados)."""
    doy = dt.timetuple().tm_yday
    h = dt.hour + dt.minute / 60 + dt.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (h - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g)
                    - 0.040849 * math.sin(2 * g))
    tst = h * 60 + eqt + 4 * lon
    ha = math.radians(tst / 4 - 180)
    la = math.radians(lat)
    return math.degrees(math.asin(math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)))


filas = []
for fn, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
    with open(REF / fn, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            f = row["Fecha_Satelite_UTC"]
            if not (WIN[0] <= f[:10] <= WIN[1]):
                continue
            try:
                v = float(row["VRP_MW"]) if row["VRP_MW"] not in ("", None) else None
            except ValueError:
                v = None
            filas.append({"src": src, "vol": NOMBRE[row["Volcan"]], "b": SENS[row["Sensor"]],
                          "t": datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
                          "vrp": v, "tipo": row["Tipo_Registro"], "dist": row["Distancia_km"],
                          "clase": row["Clasificacion Mirova"]})


def cargar(sub, solo_sha):
    recs, casos = [], []
    inner = bp.inner_desde_html()
    for vol in NOMBRE.values():
        d = json.load(open(W / "data" / sub / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            dtu = r.get("datetime_utc", "")
            if not (WIN[0] <= dtu[:10] <= WIN[1]):
                continue
            sha = (r.get("regimen") or {}).get("codigo_sha")
            if solo_sha and not sha:
                continue
            b = bp.bucket(r.get("sensor"))
            if b is None:
                continue
            recs.append({"vol": vol, "b": b, "dt": datetime.strptime(dtu, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc),
                         "sensor": r.get("sensor"), "sha": sha,
                         "pc": (r.get("primary_cluster") or {}).get("vrp_mw"), "npix": len(r.get("anomaly_pixels") or [])})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    for rec, p in zip(recs, bp.correr_node(casos)):
        rec["pub"] = bool(p[4])
        rec["disp"] = p[3]
    return recs


prod = cargar("mirova_equivalent", True)
prod_todo = cargar("mirova_equivalent", False)
sombra = cargar("experimental_v2", False)
print("records en ventana: prod(sha)", len(prod), "prod(todos)", len(prod_todo), "sombra", len(sombra))
idx = {}
for nombre, rs in (("prod", prod), ("prodall", prod_todo), ("sombra", sombra)):
    d = collections.defaultdict(list)
    for r in rs:
        d[(r["vol"], r["b"])].append(r)
    idx[nombre] = d


def estado(nombre, vol, b, t, tol):
    c = [r for r in idx[nombre].get((vol, b), []) if abs((r["dt"] - t).total_seconds()) <= tol]
    if not c:
        return None
    return any(r["pub"] for r in c)


def noche_pub(nombre, vol, t):
    out = []
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        for r in idx[nombre].get((vol, b), []):
            if r["pub"] and abs((r["dt"] - t).total_seconds()) <= 6 * 3600:
                out.append("%s %s %.3f" % (r["sensor"], r["dt"].strftime("%H:%M"), r["disp"]))
    return out


pas = collections.defaultdict(list)
for f in filas:
    if f["tipo"].startswith("ALERTA") or f["tipo"].startswith("FALSO_POSITIVO"):
        pas[(f["vol"], f["b"], f["t"].strftime("%Y-%m-%d %H:%M"))].append(f)
print("pasadas con fila ALERTA*/FALSO_POSITIVO:", len(pas))
fila_out = []
for (vol, b, m), fs in sorted(pas.items()):
    t = min(f["t"] for f in fs)
    vmax = max((f["vrp"] or 0) for f in fs)
    tipos = sorted({f["tipo"] for f in fs})
    lectA = any(f["tipo"] in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR") and (f["vrp"] or 0) >= 1.0 for f in fs)
    lectB = any(f["tipo"] != "RUTINA" and (f["vrp"] or 0) >= 1.0 for f in fs)
    e = sol(*COORD[vol], t)
    rec = {"vol": vol, "b": b, "t": m, "vrp": vmax, "tipos": tipos, "A": lectA, "B": lectB, "sol": round(e, 1),
           "dist": [f["dist"] for f in fs], "src": sorted({f["src"] for f in fs})}
    for tol in (120, 600, 1800):
        rec["p%d" % tol] = estado("prod", vol, b, t, tol)
        rec["pa%d" % tol] = estado("prodall", vol, b, t, tol)
        rec["s%d" % tol] = estado("sombra", vol, b, t, tol)
    fila_out.append(rec)


def fmt(r):
    return ("%-20s %-8s %s vrp=%.2f sol=%6.1f A=%d B=%d tipos=%s src=%s dist=%s | prod120=%s prodAll120=%s sombra120=%s"
            " | prod600=%s sombra600=%s | prod1800=%s sombra1800=%s" % (
                r["vol"], r["b"], r["t"], r["vrp"], r["sol"], r["A"], r["B"], ",".join(r["tipos"]), r["src"], r["dist"],
                r["p120"], r["pa120"], r["s120"], r["p600"], r["s600"], r["p1800"], r["s1800"]))


print("\n== (1) pasadas >=1 MW (lectura B, cualquier hora) con sombra publicando y K sin publicar, a cualquier tolerancia ==")
for r in fila_out:
    if r["B"] and any(r["s%d" % t] is True and r["p%d" % t] is not True for t in (120, 600, 1800)):
        print(fmt(r))
print("\n== (2) todas las pasadas >=1 MW (lectura B) en que K no publica a +-120 s ==")
for r in fila_out:
    if r["B"] and r["p120"] is not True:
        print(fmt(r))
        print("      K +-6 h publica:", noche_pub("prod", r["vol"], datetime.strptime(r["t"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))[:8])
print("\n== (3) conteos ==")
noct = [r for r in fila_out if r["sol"] < 0]
print("pasadas lectura A:", sum(r["A"] for r in fila_out), "nocturnas (sol<0, formula propia):", sum(r["A"] for r in noct))
print("lectura A nocturnas con record de sombra a +-120:", sum(1 for r in noct if r["A"] and r["s120"] is not None))
print("lectura A nocturnas con record de sombra, posteriores a la adopcion 2026-10-18 09:57:", sum(1 for r in noct if r["A"] and r["s120"] is not None and r["t"] >= "2026-10-18 09:57"))
print("lectura A nocturnas posteriores a la adopcion (con o sin sombra):", sum(1 for r in noct if r["A"] and r["t"] >= "2026-10-18 09:57"))
print("lectura A diurnas (sol>=0):", [(r["vol"], r["b"], r["t"], r["vrp"], r["p120"], r["s120"]) for r in fila_out if r["A"] and r["sol"] >= 0])
print("\n== (4) Muy Bajo nocturnas (tipo de alerta A, <1 MW, y >0,05 en V375) en que sombra publica y K calla a +-120 ==")
mb = collections.Counter()
mbn = collections.Counter()
for r in noct:
    if r["A"]:
        continue
    if not any(t in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR") for t in r["tipos"]):
        continue
    if r["b"] == "VIIRS375" and r["vrp"] <= 0.05 + 1e-9:
        continue
    if r["p120"] is None or r["s120"] is None:
        continue
    mbn[(r["vol"], r["b"])] += 1
    if r["s120"] and not r["p120"]:
        mb[(r["vol"], r["b"])] += 1
        print(fmt(r))
print({"%s|%s" % k: "%d de %d" % (mb[k], mbn[k]) for k in sorted(mbn) if mb[k]})
json.dump(fila_out, open(str(Path(sys.argv[0]).with_suffix(".json")), "w"), indent=0, default=str)
