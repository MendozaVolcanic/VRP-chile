# -*- coding: utf-8 -*-
"""s04 (S172, auditoria Chillan): descomposicion conteo x VRP por pixel contra el OSF v2.5 de MIROVA, 2025.

POR QUE: la tabla NRT de MIROVA (latest.php, OCR) no trae conteo de pixeles; el OSF v2.5 si (Npix) y ademas la
radiancia MIR sumada de los alertados y de su fondo. Con eso la razon de la escena se parte en
    VRP_nuestro / VRP_MIROVA = (N_nuestro / N_MIROVA) x (VRP por pixel nuestro / VRP por pixel MIROVA)
y la razon publicada agrega un factor de seleccion (lo publicado / lo alertado en la escena).
Nuestros records de 2025 son del detector K (reproceso #883 desde el 2025-02-15). El OSF es la base filtrada de MIROVA
(A105: clase automatica y umbrales por sensor), no el NRT: sirve para la forma de la descomposicion, no para la tasa NRT.

P1 (si estuviera roto, lo veria): identidad numerica, el producto de los dos factores debe dar la razon de escena
    fila por fila (se imprime el maximo error); control de pareo: |cenit nuestro - cenit MIROVA| debe ser < 1 grado.
P2 (instrumento muerto): pasadas pareadas con 0 pixeles nuestros se cuentan aparte (SIN DATO), no como razon 0;
    control positivo k*A del OSF = 2.531.250 / 11.081.250 / 18.900.000 por sensor, fila por fila.
Ventana: 2025-02-15 a 2025-12-31, nocturnas (Dayflag 0 del OSF y es_pasada_diurna_descartada nuestro).
Uso: python -B s04_osf2025_descomposicion.py <osf_chillan.csv> <pasadas_2025.csv> <json records> <salida prefijo>
"""
import collections, csv, json, statistics, sys
from datetime import datetime

OSF, PAS, JS, PRE = sys.argv[1:5]
RES = {"375": "VIIRS375", "750": "VIIRS750", "1000": "MODIS"}
KA = {"VIIRS375": 18.0 * 140625, "VIIRS750": 19.7 * 562500, "MODIS": 18.9 * 1e6}

ours = collections.defaultdict(list)
for r in csv.DictReader(open(PAS, encoding="utf-8")):
    ours[r["b"]].append((datetime.strptime(r["dt"], "%Y-%m-%d %H:%M"), r))
recs = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(JS, encoding="utf-8"))["records"]}

rows, sin_record, ka_err = [], 0, collections.defaultdict(float)
for m in csv.DictReader(open(OSF, encoding="utf-8")):
    t = datetime.strptime(m["timeUTC"], "%d/%m/%Y %H:%M")
    if not ("2025-02-15" <= t.strftime("%Y-%m-%d") <= "2025-12-31") or m["Dayflag"] != "0":
        continue
    b = RES[m["Resolution"]]
    vrp_M = float(m["VRP"]) / 1e6
    ka = float(m["VRP"]) / (float(m["Tot_Lmir_hot"]) - float(m["Tot_Lmir_bk"]))
    ka_err[b] = max(ka_err[b], abs(ka / KA[b] - 1))
    cand = [x for x in ours[b] if abs((x[0] - t).total_seconds()) <= 120]
    if not cand:
        sin_record += 1
        rows.append({"b": b, "t": t.isoformat(), "pareo": "sin_record", "N_M": int(m["Npix"]), "vrp_M": vrp_M,
                     "z_M": float(m["SatZen"])})
        continue
    _, o = min(cand, key=lambda x: abs((x[0] - t).total_seconds()))
    rec = recs.get((o["sensor"], o["dt"]), {})
    px = rec.get("anomaly_pixels") or []
    vpos = [p["vrp_mw"] for p in px if (p.get("vrp_mw") or 0) > 0]
    n_all = rec.get("n_anomalous_pixels") or 0
    scene = sum(vpos)
    disp = float(o["disp"]) if o["pub"] == "1" else 0.0
    N_M = int(m["Npix"])
    row = {"b": b, "t": t.isoformat(), "pareo": "ok", "sensor": o["sensor"], "z_o": float(o["z"]) if o["z"] else None,
           "z_M": float(m["SatZen"]), "N_M": N_M, "vrp_M": vrp_M, "Lhot_M_px": float(m["Tot_Lmir_hot"]) / N_M,
           "Lbk_M_px": float(m["Tot_Lmir_bk"]) / N_M, "maxdist_M_m": float(m["Max_Dist"]), "class_M": m["class"],
           "n_all": n_all, "n_list": len(px), "n_pos": len(vpos), "scene_o": scene, "pub": o["pub"], "disp": disp,
           "pc_n": o["pc_n"]}
    if vpos:
        row["r_escena"] = scene / vrp_M
        row["f_conteo_pos"] = len(vpos) / N_M
        row["f_vpp_pos"] = (scene / len(vpos)) / (vrp_M / N_M)
        row["f_conteo_all"] = n_all / N_M
        row["identidad_err"] = abs(row["f_conteo_pos"] * row["f_vpp_pos"] - row["r_escena"])
        row["r_pub"] = disp / vrp_M
        row["f_seleccion"] = disp / scene if scene else None
    rows.append(row)

with open(PRE + "_filas.csv", "w", newline="", encoding="utf-8") as fh:
    keys = sorted({k for r in rows for k in r})
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def zb(z):
    return "z<30" if z < 30 else "z30-50" if z < 50 else "z>=50"


out = {"ka_err_rel_max": dict(ka_err), "n_filas_osf_nocturnas_ventana": len(rows), "sin_record": sin_record,
       "por_sensor": {}}
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    ok = [r for r in rows if r["b"] == b and r["pareo"] == "ok"]
    con = [r for r in ok if "r_escena" in r]
    def bloque(S):
        return {"n": len(S), "r_escena": med([r["r_escena"] for r in S]),
                "f_conteo_pos": med([r["f_conteo_pos"] for r in S]), "f_vpp_pos": med([r["f_vpp_pos"] for r in S]),
                "f_conteo_all": med([r["f_conteo_all"] for r in S]),
                "r_pub": med([r["r_pub"] for r in S]), "n_publica": sum(1 for r in S if r["pub"] == "1"),
                "N_M_mediana": med([r["N_M"] for r in S]), "n_pos_mediana": med([r["n_pos"] for r in S])}
    zz = collections.defaultdict(list)
    for r in con:
        zz[zb(r["z_M"])].append(r)
    out["por_sensor"][b] = {
        "n_osf": sum(1 for r in rows if r["b"] == b), "n_pareadas": len(ok),
        "n_pareadas_sin_pixel_nuestro_SIN_DATO": len(ok) - len(con),
        "dz_max": max([abs(r["z_o"] - r["z_M"]) for r in ok if r["z_o"] is not None], default=None),
        "identidad_err_max": max([r["identidad_err"] for r in con], default=None),
        "todas": bloque(con), "por_cenit": {k: bloque(v) for k, v in sorted(zz.items())}}
json.dump(out, open(PRE + "_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
