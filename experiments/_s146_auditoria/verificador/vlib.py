# -*- coding: utf-8 -*-
"""Verificador S146: carga propia e independiente (no usa dlib ni _s126_lib de los auditores).
(1) Si la carga estuviera rota, fallaria? Si: assert de n_records contra el JSON crudo y se imprime el total.
(2) Si el instrumento estuviera muerto, se veria distinto? Si: cada script que lo usa imprime n y un control positivo.
Referencia MIROVA: latest_consolidado.csv (CONS) union snapshot OCR, leidos crudos con csv, sin el loader del proyecto."""
import csv, io, json, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Planchon-Peteroa": "PlanchonPeteroa"}
CACHE = os.path.join(HERE, "v_cache.json")
DROP = ("anomaly_pixels", "discarded_anomaly_pixels")


def bucket(s):
    s = (s or "").upper()
    if "MODIS" in s: return "modis"
    if "750" in s: return "v750"
    if "VIIRS" in s: return "v375"
    return None


def bucket_ref(s):
    s = (s or "").upper().strip()
    return {"MODIS": "modis", "VIIRS": "v750", "VIIRS375": "v375"}.get(s)


def cargar():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    out = {}
    for v in VOLS:
        rs = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]
        L = [{k: x for k, x in r.items() if k not in DROP} for r in rs]
        assert len(L) == len(rs) and len(L) > 0
        out[v] = L
    json.dump(out, open(CACHE, "w", encoding="utf-8"))
    return out


def referencia(incluir_ocr=True):
    """Devuelve filas crudas: dict(vol, fecha(YYYY-MM-DD), dt, sensor_bucket, vrp, dist, tipo, fuente)."""
    filas = []
    fuentes = [("cons", os.path.join(ROOT, "latest_consolidado.csv"))]
    if incluir_ocr:
        fuentes.append(("ocr", os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")))
    for nombre, p in fuentes:
        with open(p, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                vol = ALIAS.get(row["Volcan"].strip(), row["Volcan"].strip())
                try: vrp = float(row["VRP_MW"])
                except Exception: vrp = None
                try: dist = float(row["Distancia_km"])
                except Exception: dist = None
                filas.append({"vol": vol, "dt": row["Fecha_Satelite_UTC"], "fecha": row["Fecha_Satelite_UTC"][:10],
                              "b": bucket_ref(row["Sensor"]), "vrp": vrp, "dist": dist,
                              "tipo": row["Tipo_Registro"].strip(), "fuente": nombre})
    return filas


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    d = cargar()
    for v in VOLS:
        fs = [r["datetime_utc"][:10] for r in d[v]]
        print(v, len(d[v]), min(fs), max(fs))
    print("total", sum(len(x) for x in d.values()), "cache MB", round(os.path.getsize(CACHE) / 1e6, 1))
    ref = referencia()
    from collections import Counter
    print("ref filas", len(ref), Counter((f["fuente"], f["tipo"]) for f in ref))
    print("ref vols sin alias", sorted({f["vol"] for f in ref} - set(VOLS)))
    print("ref min/max", min(f["dt"] for f in ref), max(f["dt"] for f in ref))
