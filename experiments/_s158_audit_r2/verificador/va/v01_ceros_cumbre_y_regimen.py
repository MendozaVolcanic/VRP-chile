# -*- coding: utf-8 -*-
"""VA, verificacion independiente de los hallazgos 2, 6 y 7 (camino distinto al de RA1/M2).

Lee data/mirova_equivalent/*.json directo (no records_v750.json ni el predicado de node de RA1),
toma inner_radius_km de volcanoes.yaml, aplica el predicado del tablero transcrito de
frontend/index.html:1595-1601 (isValidDetection: pc.vrp_mw > 0) y pareo con MIROVA por pasada
(|dt| <= 8 min, ademas del <= 60 min de RA1).

Preguntas del instrumento:
1. Si el fondo dejara cumulos de cumbre en 0, esto lo ve: cuenta pc.vrp_mw == 0 con centroide <= inner.
   Control positivo: los cumulos de cumbre con pc.vrp_mw > 0 deben ser mayoria y visibles.
2. Si el lector estuviera muerto (sensor mal clasificado, campo con otro nombre) el total de V750 y el
   de MODIS darian 0 o un numero absurdo: se imprimen los totales por sensor.
Denominador y ventana: impresos con cada numero.
"""
import csv, glob, json, os, subprocess, sys
from collections import Counter, defaultdict
from datetime import datetime
import yaml

sys.stdout.reconfigure(encoding="utf-8")
inner = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open("volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
NOM = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}


def bucket(s):
    if s.startswith("MODIS") or s in ("Terra", "Aqua"):
        return "MODIS"
    if s.endswith("_750"):
        return "V750"
    if s.startswith("VIIRS"):
        return "V375"
    return "otro:" + s


recs = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    for r in d["records"]:
        r["_vol"] = d.get("volcano") or os.path.basename(f)[:-5]
        recs.append(r)
print("records totales:", len(recs))
print("por sensor:", Counter(bucket(r.get("sensor", "")) for r in recs))
print("sensores crudos:", Counter(r.get("sensor") for r in recs).most_common(12))

ref = defaultdict(list)
for path, canal in (("latest_consolidado.csv", "tabla"),
                    ("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", "ocr")):
    for row in csv.DictReader(open(path, encoding="utf-8")):
        try:
            v = float(row["VRP_MW"] or 0)
        except ValueError:
            v = 0.0
        ref[(row["Volcan"], row["Sensor"])].append(
            (datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M"), row["Tipo_Registro"], v, canal))
print("referencia desde", min(t for L in ref.values() for t, *_ in L), "claves sensor:", sorted({k[1] for k in ref}))


def pareo(vol, sensor_csv, t, tol_min):
    L = ref.get((NOM.get(vol, vol), sensor_csv), [])
    return [x for x in L if abs((x[0] - t).total_seconds()) <= tol_min * 60]


def analiza(sens_bucket, sensor_csv):
    print("\n==================== %s ====================" % sens_bucket)
    sel = [r for r in recs if bucket(r.get("sensor", "")) == sens_bucket and r.get("primary_cluster")]
    print("records %s con primary_cluster: %d ; sin: %d" % (
        sens_bucket, len(sel), sum(1 for r in recs if bucket(r.get("sensor", "")) == sens_bucket and not r.get("primary_cluster"))))
    cum = []
    for r in sel:
        pc = r["primary_cluster"]
        ir = inner.get(r["_vol"])
        if ir is None or pc.get("centroid_dist_km") is None:
            continue
        if pc["centroid_dist_km"] <= ir:
            cum.append(r)
    ceros = [r for r in cum if (r["primary_cluster"].get("vrp_mw") or 0) == 0]
    print("cumulo de cumbre (centroid_dist_km <= inner yaml): %d ; con pc.vrp_mw == 0: %d (%.1f %%)" % (
        len(cum), len(ceros), 100 * len(ceros) / max(1, len(cum))))
    fe = sorted(r["datetime_utc"] for r in cum)
    print("ventana obs:", fe[0], "a", fe[-1])
    print("ceros por volcan:", dict(Counter(r["_vol"] for r in ceros)))
    print("ceros por distance_class:", dict(Counter(r.get("distance_class") for r in ceros)))
    print("ceros por n_pixels:", dict(Counter(r["primary_cluster"].get("n_pixels") for r in ceros)))
    print("ceros d9_capped:", sum(bool(r["primary_cluster"].get("d9_capped")) for r in ceros),
          " single_pixel_mode:", sum(bool(r["primary_cluster"].get("single_pixel_mode")) for r in ceros))
    caus = Counter()
    for r in ceros:
        ir = inner[r["_vol"]]
        aps = [a for a in (r.get("anomaly_pixels") or []) if a["dist_km"] <= ir + 1.5]
        if not aps:
            caus["sin anomaly_pixels cerca"] += 1
        elif all(a["bt_k"] <= r["t_bg_k"] for a in aps):
            caus["todos bt<=t_bg"] += 1
        else:
            caus["algun bt>t_bg"] += 1
    print("causa (anomaly_pixels a <= inner+1,5 km del centro):", dict(caus))
    for tol in (8, 60):
        for desde in ("2026-01-10", "2026-03-01", "2026-06-13"):
            sub = [r for r in ceros if r["datetime_utc"][:10] >= desde]
            n_m = n_a = n_p = n_ruta = 0
            for r in sub:
                t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
                m = pareo(r["_vol"], sensor_csv, t, tol)
                al = [x for x in m if x[1] in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")]
                n_m += bool(m)
                n_a += bool(al)
                n_p += any(x[2] >= 1 for x in al)
                n_ruta += bool(m) and all(x[1] == "RUTINA" for x in m)
            print("  tol %2d min, obs >= %s: ceros=%d MIROVA miro=%d alerta=%d protegida(>=1MW)=%d solo RUTINA=%d" % (
                tol, desde, len(sub), n_m, n_a, n_p, n_ruta))
    return cum, ceros


cum750, ceros750 = analiza("V750", "VIIRS")
print("\nceros V750 con alerta >=1 MW de MIROVA a <=8 min:")
for r in ceros750:
    t = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
    al = [x for x in pareo(r["_vol"], "VIIRS", t, 8) if x[1].startswith("ALERTA_TERMICA") and x[2] >= 1]
    if al:
        print("  ", r["_vol"], r["datetime_utc"], r["sensor"], "t_bg", r["t_bg_k"], "t_max", r["t_max_k"],
              "MIROVA", [(str(x[0])[11:16], x[1], x[2], x[3]) for x in al])

cumM, cerosM = analiza("MODIS", "MODIS")

print("\n==================== processed_utc ====================")
K = "2026-10-18T09:57:30Z"
con = [r for r in recs if r.get("processed_utc")]
print("records con processed_utc: %d de %d" % (len(con), len(recs)))
print("processed_utc < %s: %d" % (K, sum(r["processed_utc"] < K for r in con)))
print("min processed_utc:", min(r["processed_utc"] for r in con), " max:", max(r["processed_utc"] for r in con))
fp = [r for r in recs if r.get("first_processed_utc")]
print("first_processed_utc presentes: %d ; < K: %d" % (len(fp), sum(r["first_processed_utc"] < K for r in fp)))
sha = Counter((r.get("regimen") or {}).get("codigo_sha") for r in recs)
print("codigo_sha distintos:", len(sha), " records sin regimen.codigo_sha:", sha.get(None, 0))
desc = Counter()
for s, n in sha.items():
    if not s:
        continue
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", "34cea39e", s], capture_output=True).returncode
    desc["contiene K" if rc == 0 else ("NO contiene K" if rc == 1 else "sha desconocido rc=%d" % rc)] += n
print("records por si su codigo_sha desciende del squash de K 34cea39e:", dict(desc))
print("control positivo: 34cea39e ancestro de HEAD rc =",
      subprocess.run(["git", "merge-base", "--is-ancestor", "34cea39e", "HEAD"]).returncode,
      "; control negativo: HEAD ancestro de 34cea39e rc =",
      subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", "34cea39e"]).returncode)
pre = [r for r in recs if r.get("datetime_utc", "") < "2026-09-18"]
print("records con obs < 2026-09-18: %d ; de ellos processed_utc < K: %d ; sin processed_utc: %d" % (
    len(pre), sum((r.get("processed_utc") or "9") < K for r in pre), sum(not r.get("processed_utc") for r in pre)))
print("processed_utc por dia:", sorted(Counter((r.get("processed_utc") or "none")[:10] for r in recs).items()))
print("origen:", Counter((r.get("regimen") or {}).get("origen") for r in recs))
