# -*- coding: utf-8 -*-
"""Cuantas alertas (protegidas y de cualquier VRP) cambian de lado crater/lejana si la referencia usara la distancia
leida por serie de tiempo en Dist.png (verificador, variante C = imagen mas reciente de 1 a 25 d) en vez de la del OCR,
para las filas OCR del 2026-06-13 al 2026-10-08. Solo lectura del repo VRP Chile.

Regla de intervalos (la del verificador, v2_comun.decidir): la serie decide "cerca" si todo su intervalo esta bajo
limite - 0,6 km, "lejos" si todo esta sobre limite + 0,6 km; si no, indecidible. Una fila cambia de lado solo si la
serie DECIDE el lado contrario al de su tipo actual (ALERTA = crater, FALSO_POSITIVO = lejana).

Uso: python medir.py [--var C|A]   (salida a stdout; se guarda en medir_salida_<var>.txt)
"""
import argparse, csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
for p in (REPO, REPO / "scripts"):
    sys.path.insert(0, str(p))
from calidad_referencia_mirova import avisar  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from pipeline.mirova_csv_loader import normalize_sensor  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402

AQUI = Path(__file__).resolve().parent
LECT = Path(r"C:/Users/nmend/AppData/Local/Temp/claude/verifdist/v2/ocr_vs_serie.csv")
DESDE, HASTA = "2026-06-13", "2026-10-08"
LIM = {"Lastarria": 3.0, "PlanchonPeteroa": 3.0, "Copahue": 4.0, "Tupungatito": 7.0, "PuyehueCordonCaulle": 20.0}
TOL = 0.6
NOMBRE = {"ChillanNevadosde": "NevadosDeChillan"}
ALERTA = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")


def lim(v):
    return LIM.get(v, 5.0)


def lado_punto(d, v):
    return "cerca" if d <= lim(v) else "lejos"


def lado_intervalo(lo, hi, v):
    if hi < lim(v) - TOL:
        return "cerca"
    if lo > lim(v) + TOL:
        return "lejos"
    return "indecidible"


def dt(f):
    return datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--var", default="C")
    a = ap.parse_args()
    V = a.var
    print("== A119 (avisos de calidad de la ventana, a stdout para que queden en la salida)")
    avisar(DESDE, HASTA, archivo=sys.stdout)
    cons = AQUI / "_dl" / "registro_vrp_consolidado.csv"
    ocr = AQUI / "_dl" / "registro_vrp_ocr.csv"
    print("referencia: remoto Mirova-v1,", (AQUI / "_dl" / "procedencia.json").read_text(encoding="utf-8").replace("\n", " "))
    ref = cargar_referencia_unificada(cons, ocr)
    coords = _coords_por_volcan()

    # lecturas del verificador
    lect = {}
    with open(LECT, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            vol = NOMBRE.get(r["vol"], r["vol"])
            lect[(vol, normalize_sensor(r["sensor"]), r["t"][:16])] = r
    print(f"lecturas del verificador: {len(lect)} filas OCR con Distancia_km > 0 (todas las fechas)")

    # filas OCR de la ventana
    ocr_v = [f for f in ref if f["source"] == "OCR" and DESDE <= f["fecha_utc"][:10] <= HASTA]
    print(f"\n== 1. filas OCR de la ventana {DESDE} a {HASTA}: {len(ocr_v)}; por tipo {dict(Counter(f['tipo'] for f in ocr_v))}")
    # coherencia del tipo con la distancia del OCR
    inco = [f for f in ocr_v if f["dist_km"] is not None and f["tipo"] in ("ALERTA_TERMICA_OCR", "FALSO_POSITIVO_OCR")
            and (f["tipo"] == "ALERTA_TERMICA_OCR") != (f["dist_km"] <= lim(f["volcano"]))]
    print(f"   tipo incoherente con dist OCR <= limite: {len(inco)}",
          [(f['volcano'], f['fecha_utc'][:16], f['tipo'], f['dist_km']) for f in inco][:10])
    sin_dist = [f for f in ocr_v if not f["dist_km"]]
    print(f"   sin distancia OCR (None o 0): {len(sin_dist)}", dict(Counter(f["tipo"] for f in sin_dist)))

    # decision por fila
    for f in ocr_v:
        k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
        r = lect.get(k)
        f["actual"] = "cerca" if f["tipo"].startswith("ALERTA") else ("lejos" if f["tipo"].startswith("FALSO") else None)
        f["serie"] = "sin_lectura"
        f["lect_ocr"] = None
        if r is not None:
            f["lect_ocr"] = float(r["ocr"])
            cl = r.get(f"{V}_clase") or ""
            if cl in ("unico", "solapado", "ambiguo"):
                lo = float(r[f"{V}_est"]) if cl == "unico" else float(r[f"{V}_kmin"])
                hi = float(r[f"{V}_est"]) if cl == "unico" else float(r[f"{V}_kmax"])
                f["serie"] = lado_intervalo(lo, hi, f["volcano"])
                f["serie_iv"] = (round(lo, 2), round(hi, 2))
            elif cl == "sin_marcador":
                f["serie"] = "sin_marcador"
            # control de que la lectura es de la misma fila
            if f["dist_km"] is not None and abs(float(r["ocr"]) - f["dist_km"]) > 0.005:
                f["serie"] = "lectura_de_otra_dist"
        f["cambia"] = f["actual"] is not None and f["serie"] in ("cerca", "lejos") and f["serie"] != f["actual"]
    print("   estado de la lectura por fila:", dict(Counter(f["serie"] for f in ocr_v)))
    print("   por sensor:", {b: dict(Counter(f["serie"] for f in ocr_v if f["sensor_bucket"] == b))
                            for b in ("VIIRS375", "VIIRS750", "MODIS")})
    print(f"   filas que cambian de lado: {sum(f['cambia'] for f in ocr_v)}")

    # tabla del mismo instante (+-180 s), para separar "solo OCR" de "con tabla" y para el control
    cons_por = defaultdict(list)
    for f in ref:
        if f["source"] == "CONS":
            cons_por[(f["volcano"], f["sensor_bucket"])].append(f)
    for f in ocr_v:
        t = dt(f["fecha_utc"])
        f["tabla"] = [c for c in cons_por[(f["volcano"], f["sensor_bucket"])] if abs((dt(c["fecha_utc"]) - t).total_seconds()) <= 180]

    # ---- 2. CONTROL: filas OCR con pasada en la tabla con distancia (ALERTA o FALSO_POSITIVO)
    print("\n== 2. CONTROL: filas OCR de la ventana con la misma pasada en la tabla (+-180 s, ALERTA o FALSO_POSITIVO con distancia)")
    ctl = Counter()
    errs = []
    for f in ocr_v:
        tb = [c for c in f["tabla"] if c["tipo"] in ("ALERTA_TERMICA", "FALSO_POSITIVO") and c["dist_km"] is not None]
        if not tb or f["actual"] is None:
            continue
        verdad = lado_punto(tb[0]["dist_km"], f["volcano"])
        ctl["n"] += 1
        ctl["ocr_acierta"] += f["actual"] == verdad
        # copia de la tabla (reconciliacion de Mirova-v1): el OCR no aporta nada propio en esa fila
        copia = f["dist_km"] is not None and abs(f["dist_km"] - tb[0]["dist_km"]) <= 0.005
        ctl["ocr_copia_exacta_de_tabla"] += copia
        if not copia:
            ctl["ocr_propio_n"] += 1
            ctl["ocr_propio_acierta"] += f["actual"] == verdad
            ctl["ocr_propio_tipo_" + f["tipo"]] += 1
            if f["serie"] in ("cerca", "lejos"):
                ctl["ocr_propio_serie_decide"] += 1
                ctl["ocr_propio_serie_acierta"] += f["serie"] == verdad
        if f["sensor_bucket"] == "VIIRS375" and f["serie"] not in ("sin_lectura", "lectura_de_otra_dist"):
            ctl["v375_con_lectura"] += 1
            ctl["v375_ocr_acierta"] += f["actual"] == verdad
            if f["serie"] in ("cerca", "lejos"):
                ctl["serie_decide"] += 1
                ctl["serie_acierta"] += f["serie"] == verdad
                ctl["ocr_acierta_en_decididas"] += f["actual"] == verdad
                if f["serie"] != verdad or f["actual"] != verdad:
                    errs.append((f["volcano"], f["fecha_utc"][:16], "tabla", tb[0]["dist_km"], "ocr", f["dist_km"], f["actual"], "serie", f.get("serie_iv"), f["serie"]))
            else:
                ctl["serie_no_decide_" + f["serie"]] += 1
            # el intervalo de la serie contiene la distancia de la tabla (+-0,6)?
            iv = f.get("serie_iv")
            if iv:
                ctl["iv_n"] += 1
                ctl["iv_contiene_tabla"] += iv[0] - TOL <= min(tb[0]["dist_km"], 25) <= iv[1] + TOL
                ctl["ocr_a_0p6_de_tabla"] += abs(f["dist_km"] - tb[0]["dist_km"]) <= TOL
        if f["actual"] != verdad:
            ctl["ocr_yerra_lado"] += 1
    for k_, v_ in sorted(ctl.items()):
        print(f"   {k_}: {v_}")
    print("   casos en que alguna de las dos fuentes yerra el lado (volcan, hora, tabla, ocr, lado OCR, intervalo serie, lado serie):")
    for e in errs:
        print("     ", e)

    # ---- 3. pasadas
    print("\n== 3. PASADAS (volcan, sensor, minuto) con fila OCR en la ventana")
    por_pasada = defaultdict(list)
    for f in ref:
        por_pasada[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)
    claves = sorted({(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]) for f in ocr_v})

    def tipo_alt(f):
        if f["source"] == "OCR" and f.get("cambia"):
            return "FALSO_POSITIVO_OCR" if f["serie"] == "lejos" else "ALERTA_TERMICA_OCR"
        return f["tipo"]

    filas_out = []
    for k in claves:
        fs = por_pasada[k]
        es_al = lambda t: t in ALERTA
        hoy_al = any(es_al(f["tipo"]) and (f["vrp_mw"] or 0) > 0 for f in fs)
        alt_al = any(es_al(tipo_alt(f)) and (f["vrp_mw"] or 0) > 0 for f in fs)
        hoy_pr = any(es_al(f["tipo"]) and (f["vrp_mw"] or 0) >= 1 for f in fs)
        alt_pr = any(es_al(tipo_alt(f)) and (f["vrp_mw"] or 0) >= 1 for f in fs)
        o = [f for f in fs if f["source"] == "OCR"][0]
        lat, lon = coords[k[0]]
        noct = not es_pasada_diurna_descartada(k[1], lat, lon, dt(o["fecha_utc"]))
        cons_k = [f for f in fs if f["source"] == "CONS"]
        vrp = max((f["vrp_mw"] or 0) for f in fs)
        filas_out.append(dict(vol=k[0], sensor=k[1], t=k[2], vrp=vrp, tipo_ocr=o["tipo"], dist_ocr=o["dist_km"],
                              serie=o["serie"], intervalo=o.get("serie_iv"), con_tabla=bool(o["tabla"]),
                              tipos_tabla="+".join(sorted({c["tipo"] for c in o["tabla"]})) or "-",
                              misma_clave_tabla=bool(cons_k), nocturna=noct,
                              hoy_alerta=hoy_al, alt_alerta=alt_al, hoy_prot=hoy_pr, alt_prot=alt_pr))
    with open(AQUI / f"pasadas_{V}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas_out[0]))
        w.writeheader()
        w.writerows(filas_out)

    def tabla(nombre, hoy, alt, base):
        print(f"\n   --- {nombre}")
        P = [p for p in filas_out if p[base] or p[alt.replace('alt', 'hoy')] or p[alt]]
        hoy_n = sum(p[hoy] for p in filas_out)
        print(f"   pasadas con fila OCR en la ventana que hoy son {nombre}: {hoy_n} (de {len(filas_out)} pasadas)")
        pierden = [p for p in filas_out if p[hoy] and not p[alt]]
        ganan = [p for p in filas_out if p[alt] and not p[hoy]]
        dep = [p for p in filas_out if p[hoy] and not p["misma_clave_tabla"]]
        print(f"   de esas, sin fila de la tabla en la misma clave (dependen sólo del OCR): {len(dep)}; estado de la lectura: {dict(Counter(p['serie'] for p in dep))}")
        print(f"     por sensor: {dict(Counter(p['sensor'] for p in dep))}")
        print(f"   PIERDEN (crater -> lejana): {len(pierden)}  nocturnas {sum(p['nocturna'] for p in pierden)}")
        print(f"   GANAN   (lejana -> crater): {len(ganan)}  nocturnas {sum(p['nocturna'] for p in ganan)}")
        c = Counter((p["vol"], p["sensor"], "pierde" if p in pierden else "gana", "noct" if p["nocturna"] else "diurna") for p in pierden + ganan)
        for kk, vv in sorted(c.items()):
            print(f"     {kk}: {vv}")
        for p in pierden + ganan:
            print(f"     {'PIERDE' if p in pierden else 'GANA  '} {p['vol']:20s} {p['sensor']:8s} {p['t']} VRP {p['vrp']:7.2f} OCR {p['dist_ocr']} "
                  f"serie {p['intervalo']} ({p['serie']}) tabla {p['tipos_tabla']} {'noct' if p['nocturna'] else 'DIURNA'}")
        return pierden, ganan

    tabla("protegidas (lectura A, VRP >= 1 MW)", "hoy_prot", "alt_prot", "hoy_prot")
    tabla("alertas de cualquier VRP (> 0)", "hoy_alerta", "alt_alerta", "hoy_alerta")
    # regla SN (D-9): una pasada VIIRS 375 cuya alerta es <= 0,05 MW no es alerta
    sn = [p for p in filas_out if (p["hoy_alerta"] != p["alt_alerta"]) and p["sensor"] == "VIIRS375" and p["vrp"] <= 0.05]
    print(f"\n   de los cambios de alerta de cualquier VRP, VIIRS 375 con VRP <= 0,05 (no son alerta bajo la regla SN): {len(sn)}")

    # protegidas que dependen del OCR y quedan sin decidir
    print("\n== 4. PROTEGIDAS de la ventana que dependen solo del OCR, por volcan y sensor y estado de la lectura")
    c = Counter((p["vol"], p["sensor"], p["serie"]) for p in filas_out if p["hoy_prot"] and not p["misma_clave_tabla"])
    for kk, vv in sorted(c.items()):
        print(f"   {kk}: {vv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
