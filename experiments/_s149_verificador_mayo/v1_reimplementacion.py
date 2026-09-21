# -*- coding: utf-8 -*-
"""Verificador S149 (mayo). Reimplementacion independiente: lee los JSON de los brazos y los CSV
congelados directamente. Lo unico que se reusa es el predicado de publicar (bp.correr_node, que evalua
frontend/index.html con node) y el filtro diurno de referencia (opcional, se informa con y sin el).

  python v1_reimplementacion.py <carpeta con _s146_ab_sin_test1/ y _s147_ab_sin_test1_max/>
"""
import csv, io, json, sys, collections, bisect
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
S = Path(sys.argv[1]); C = RAIZ / "experiments" / "_s149_prereg_invierno" / "_congelado" / "mayo"
V0, V1 = "2026-05-01", "2026-05-31"
NOMBRE = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()


def leer_ref(nombre, fuente):
    out = []
    for r in csv.DictReader(open(C / nombre, encoding="utf-8")):
        if r["Sensor"] != "VIIRS375": continue
        f = r["Fecha_Satelite_UTC"].strip()
        if not (V0 <= f[:10] <= V1): continue
        vol = NOMBRE.get(r["Volcan"], r["Volcan"])
        dt = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        out.append(dict(vol=vol, dt=dt, tipo=r["Tipo_Registro"], vrp=float(r["VRP_MW"] or 0), fuente=fuente, act=r["Ultima_Actualizacion"]))
    return out


def cargar(perfil):
    recs, casos = [], []
    for p in sorted((S / perfil).glob("*.json")):
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            s = r.get("sensor") or ""
            if not s.startswith("VIIRS") or s.endswith("_750"): continue
            d = r.get("datetime_utc", "")
            if not (V0 <= d[:10] <= V1): continue
            dt = datetime.strptime(d, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            pc = r.get("primary_cluster") or {}
            recs.append(dict(vol=p.stem, dt=dt, plat=s, z=r.get("sensor_zenith_deg"), pc_vrp=pc.get("vrp_mw"), pc_dist=pc.get("centroid_dist_km")))
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")} for q in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[p.stem]])
    for rec, q in zip(recs, bp.correr_node(casos)): rec["pub"] = q[4]
    return {(r["vol"], r["dt"]): r for r in recs}


def etiquetar(claves, ref, filtro_diurno):
    if filtro_diurno:
        ref = [f for f in ref if not bp.es_pasada_diurna_descartada("VIIRS375", *coords[f["vol"]], f["dt"])]
    por = collections.defaultdict(list)
    for f in ref: por[f["vol"]].append(f)
    for v in por.values(): v.sort(key=lambda f: f["dt"])
    noche_al = {(f["vol"], f["dt"].strftime("%Y-%m-%d")) for f in ref if f["tipo"].startswith("ALERTA")}
    noche_fp = {(f["vol"], f["dt"].strftime("%Y-%m-%d")) for f in ref if f["tipo"].startswith("FALSO")}
    lab = {}
    for (vol, dt) in claves:
        L = por[vol]; ts = [f["dt"] for f in L]; i = bisect.bisect_left(ts, dt - timedelta(seconds=120)); ff = []
        while i < len(L) and L[i]["dt"] <= dt + timedelta(seconds=120): ff.append(L[i]); i += 1
        n = (vol, dt.strftime("%Y-%m-%d")); al = [f for f in ff if f["tipo"].startswith("ALERTA")]
        if al: e = "pos"
        elif any(f["tipo"].startswith("FALSO") for f in ff): e = "far_ref"
        elif any(f["tipo"] == "RUTINA" and f["fuente"] == "CONS" and f["vrp"] == 0 for f in ff) and n not in noche_al and n not in noche_fp: e = "neg_limpio"
        else: e = "sin_info"
        lab[(vol, dt)] = dict(lab=e, al=al, ff=ff)
    return lab


B = cargar("_s146_ab_sin_test1"); F = cargar("_s147_ab_sin_test1_max")
print("V375 pasadas: B %d | F %d | comunes %d" % (len(B), len(F), len(set(B) & set(F))))
claves = sorted(set(B) & set(F))
cons = leer_ref("registro_vrp_consolidado.csv", "CONS"); ocr = leer_ref("registro_vrp_ocr.csv", "OCR")
print("filas V375 en ventana: tabla %d (alertas %d) | OCR %d (alertas %d)" % (len(cons), sum(f["tipo"].startswith("ALERTA") for f in cons), len(ocr), sum(f["tipo"].startswith("ALERTA") for f in ocr)))

for nombre, ref, fd in (("TABLA + OCR, con filtro diurno (como el evaluador)", cons + ocr, True), ("TABLA + OCR, sin filtro diurno", cons + ocr, False),
                        ("TABLA SOLA de punta a punta (el OCR no existe), con filtro", cons, True)):
    L = etiquetar(claves, ref, fd)
    neg = [k for k in claves if L[k]["lab"] == "neg_limpio"]; pos = [k for k in claves if L[k]["lab"] == "pos"]
    print("\n=== %s" % nombre)
    print("  etiquetas:", dict(collections.Counter(v["lab"] for v in L.values())))
    print("  negativos limpios n %d | B publica %d (%.1f %%) | F publica %d (%.1f %%)" % (len(neg), sum(B[k]["pub"] for k in neg), 100 * sum(B[k]["pub"] for k in neg) / len(neg), sum(F[k]["pub"] for k in neg), 100 * sum(F[k]["pub"] for k in neg) / len(neg)))
    for et, sel in (("positivas (todas)", pos), ("positivas con alguna alerta de la TABLA", [k for k in pos if any(f["fuente"] == "CONS" for f in L[k]["al"])]),
                    ("positivas solo por OCR", [k for k in pos if all(f["fuente"] != "CONS" for f in L[k]["al"])])):
        nb = [k for k in sel if B[k]["pub"]]; keep = [k for k in nb if F[k]["pub"]]; gan = [k for k in sel if not B[k]["pub"] and F[k]["pub"]]
        print("  %-42s n %3d | B publica %3d | F conserva %3d | F gana %d" % (et, len(sel), len(nb), len(keep), len(gan)))
    print("  perdidas (B publica, F no), con TODAS las filas de referencia pareadas:")
    for k in pos:
        if B[k]["pub"] and not F[k]["pub"]:
            print("     %-20s %s %-13s z %5.1f | B pc_vrp %.3f a %.1f km | ref: %s" % (k[0], k[1].strftime("%Y-%m-%d %H:%M"), B[k]["plat"], B[k]["z"] or -1, B[k]["pc_vrp"] or 0, B[k]["pc_dist"] or -1,
                  "; ".join("%s %s %.2f MW %s" % (f["fuente"], f["tipo"], f["vrp"], f["dt"].strftime("%H:%M:%S")) for f in L[k]["ff"])))
    if nombre.startswith("TABLA + OCR, con"):
        # vrp_ref: que fila decide la magnitud cuando hay dos alertas pareadas
        dobles = [k for k in pos if len(L[k]["al"]) > 1]
        print("  positivas con mas de una alerta pareada: %d" % len(dobles))
        peor = [(k, max(f["vrp"] for f in L[k]["al"])) for k in pos if B[k]["pub"] and not F[k]["pub"]]
        print("  perdidas con MAXIMO de cualquier alerta pareada >= 0,5 MW:", [(k[0], k[1].strftime("%m-%d %H:%M"), v) for k, v in peor if v >= 0.5])
        # destino de las solo-OCR si el OCR no existiera
        Lt = etiquetar(claves, cons, True); so = [k for k in pos if all(f["fuente"] != "CONS" for f in L[k]["al"])]
        print("  las %d positivas solo-OCR, con la tabla sola quedan como:" % len(so), dict(collections.Counter(Lt[k]["lab"] for k in so)))
        print("     por plataforma:", dict(collections.Counter(B[k]["plat"] for k in so)))
