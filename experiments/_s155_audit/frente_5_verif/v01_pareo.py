# -*- coding: utf-8 -*-
"""Verificador F5, paso 1: pareo pasada a pasada Chillan contra MIROVA (ventana K).

Las dos preguntas del instrumento:
1. Si el pareo estuviera roto (pareo con otra pasada o con otro sensor), lo veria? Se imprime la
   tolerancia de minuto usada y cuantas filas de MIROVA quedan sin par a 0 y a +-3 min; si el
   pareo fuese con la pasada equivocada la razon saldria dispersa, no ordenada por cenit.
2. Si el instrumento estuviera muerto (JSON vacio, CSV vacio), saldria 0 pares y el script lo
   dice como SIN DATO, no como razon nula.
Control positivo: la pasada 2026-10-18 06:48 V750 debe dar 2,84 / 22,85 (salida de S154 1.33).

Uso: python v01_pareo.py [fuente_ref]   fuente_ref = remoto (default, ref_remoto/) o snapshot
"""
import csv, io, json, sys, math, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
DESDE, HASTA = "2026-09-28", "2026-10-19"
INNER = 5.0
VLAT, VLON = -36.863, -71.377


def bucket(s):
    s = s.upper()
    return "MODIS" if "MODIS" in s else ("VIIRS750" if s.endswith("_750") or s == "VIIRS" else "VIIRS375")


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def cargar_ref(fuente):
    base = os.path.join(AQUI, "ref_remoto") if fuente == "remoto" else os.path.join(RAIZ, "data", "mirova_reference", "mirova_v1_snapshot")
    ref = {}
    for nombre in ("ocr", "consolidado"):
        for r in csv.DictReader(open(os.path.join(base, "registro_vrp_%s.csv" % nombre), encoding="utf-8")):
            if "hill" not in r["Volcan"].lower() or not (DESDE <= r["Fecha_Satelite_UTC"][:10] <= HASTA):
                continue
            if not r["Tipo_Registro"].startswith("ALERTA"):
                continue
            ref[(r["Fecha_Satelite_UTC"][:16], bucket(r["Sensor"]))] = dict(
                mir=float(r["VRP_MW"] or 0), fuente=nombre, dist=r["Distancia_km"], tipo=r["Tipo_Registro"],
                zen=r.get("Zenith_Sat_deg", ""), clase=r.get("Clasificacion Mirova", ""))
    return ref


def cargar_records():
    d = json.load(open(os.path.join(RAIZ, "data", "mirova_equivalent", "NevadosDeChillan.json"), encoding="utf-8"))
    return [r for r in d["records"] if DESDE <= r["datetime_utc"][:10] <= HASTA]


def publicado(r):
    b = bucket(r["sensor"])
    pc = r.get("primary_cluster") or {}
    if b == "VIIRS375" and r.get("f5_core_vrp_mw") is not None:
        return r["f5_core_vrp_mw"], "f5"
    return pc.get("vrp_mw"), "pc"


def main():
    fuente = sys.argv[1] if len(sys.argv) > 1 else "remoto"
    ref = cargar_ref(fuente)
    recs = cargar_records()
    print("fuente=%s  ventana=%s..%s  records=%d  alertas_MIROVA=%d" % (fuente, DESDE, HASTA, len(recs), len(ref)))
    if not recs or not ref:
        print("SIN DATO"); return
    idx = {}
    for r in recs:
        idx.setdefault((r["datetime_utc"][:16], bucket(r["sensor"])), []).append(r)
    filas, sin_par = [], []
    for k, m in sorted(ref.items()):
        rs = idx.get(k, [])
        if not rs:
            sin_par.append(k); continue
        if len(rs) > 1:
            print("AVISO doble record", k, [x["sensor"] for x in rs])
        r = rs[0]
        pub, cual = publicado(r)
        pc = r.get("primary_cluster") or {}
        ap = r.get("anomaly_pixels") or []
        s_in = sum(p["vrp_mw"] for p in ap if hav(p["lat"], p["lon"], VLAT, VLON) <= INNER)
        s_all = sum(p["vrp_mw"] for p in ap)
        filas.append(dict(t=k[0], b=k[1], sensor=r["sensor"], zen=r.get("sensor_zenith_deg"), pub=pub, cual=cual,
                          mir=m["mir"], fuente=m["fuente"], dmir=m["dist"], pc_vrp=pc.get("vrp_mw"), pc_n=pc.get("n_pixels"),
                          pc_d=pc.get("centroid_dist_km"), spm=pc.get("single_pixel_mode"), d9=pc.get("d9_capped"),
                          foc=pc.get("focal_magnitude"), dc=r.get("distance_class"), nanom=r.get("n_anomalous_pixels"),
                          nap=len(ap), ncl=r.get("n_hotspots_clustered"), rec_vrp=r.get("vrp_mw"), s_in=s_in, s_all=s_all,
                          src=r.get("final_hotspot_source"), t1=r.get("triggered_test1")))
    # sin par exacto: buscar +-3 min
    tol = 0
    for k in sin_par:
        from datetime import datetime, timedelta
        t = datetime.strptime(k[0], "%Y-%m-%d %H:%M")
        for dm in range(-3, 4):
            kk = ((t + timedelta(minutes=dm)).strftime("%Y-%m-%d %H:%M"), k[1])
            if dm and kk in idx:
                tol += 1; print("par a %+d min:" % dm, k, "->", kk[0]); break
    print("pares exactos=%d  alertas sin par exacto=%d (de ellas con record a +-3 min: %d)" % (len(filas), len(sin_par), tol))
    from collections import Counter
    print("por sensor:", Counter(f["b"] for f in filas))
    print("alertas sin par por sensor:", Counter(k[1] for k in sin_par))
    print()
    print("pasada            sens  zen   pub    mir   razon  pc_n spm  d9   ncl nanom  rec_vrp  s_in   s_all  dc      fte")
    for f in filas:
        raz = (f["pub"] / f["mir"]) if (f["pub"] is not None and f["mir"]) else float("nan")
        print("%s %-5s %4.1f %6.2f %6.2f %6.2f %4s %-4s %-4s %3s %5s %7.2f %6.2f %6.2f %-7s %s" % (
            f["t"], f["b"][:5] if f["b"] != "VIIRS750" else "V750", f["zen"] or float("nan"), f["pub"] if f["pub"] is not None else float("nan"),
            f["mir"], raz, f["pc_n"], str(f["spm"])[0] if f["spm"] is not None else "-", str(f["d9"])[0] if f["d9"] else "-",
            f["ncl"], f["nanom"], f["rec_vrp"] or 0, f["s_in"], f["s_all"], f["dc"], f["fuente"][:3]))
    json.dump(filas, open(os.path.join(AQUI, "pares_%s.json" % fuente), "w", encoding="utf-8"), indent=0)
    print("\nsin par (alerta MIROVA sin record nuestro en ese minuto):")
    for k in sin_par:
        print("  ", k, ref[k]["mir"], ref[k]["fuente"], ref[k]["tipo"])


if __name__ == "__main__":
    main()
