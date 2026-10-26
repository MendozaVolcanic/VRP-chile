# -*- coding: utf-8 -*-
"""RA1, afirmacion 2: cuantos records VIIRS 750 con cumulo dentro del radio de cumbre quedan con magnitud 0 y
cuantos de ellos el tablero oculta (predicado real ejecutado con node: predicado_tablero_salida.json).

Preguntas del instrumento:
1. Si el fondo dejara en 0 MW cumulos de cumbre, este conteo lo ve: cuenta pc.vrp_mw == 0 con centroide dentro de
   inner_radius_km, y separa la causa fisica (todos los pixeles publicados mas frios que la mediana del anillo) de
   otras causas.
2. Si el instrumento estuviera muerto, el control (cumulos de cumbre con magnitud > 0 que el tablero SI muestra)
   daria 0; y el control positivo del predicado de node (record sintetico) esta en predicado_tablero.txt.
Denominadores y ventana: se imprimen con cada numero. Regimen: fecha de observacion < 2026-09-18 (detector
anterior) o >= (detector K, en los datos desde esa observacion segun el prompt; tambien se cruza con
regimen.codigo_sha de cada record cuando existe).

Cruce con MIROVA: latest_consolidado.csv (raiz, canal tabla) + registro_vrp_ocr.csv del snapshot (canal OCR),
Sensor == "VIIRS" (M-band, misma convencion que frontend/index.html:1419 mirovaSensorBucket), mismo volcan
(mapa de nombres A14), |dt| <= 60 min (TOL_MS del tablero, index.html:1452). Alerta = Tipo_Registro
ALERTA_TERMICA o ALERTA_TERMICA_OCR; protegida = alerta con VRP_MW >= 1 (scripts/clase_mirova.py:46).
Antes de usar la ventana se llama a calidad_referencia_mirova.avisar (A119).
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import calidad_referencia_mirova as crm  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
K_DESDE = "2026-09-18"
NOMBRES = {  # nuestro nombre de archivo -> nombre en el CSV del scraper (A14)
    "Lascar": "Lascar", "Lastarria": "Lastarria", "Isluga": "Isluga", "Tupungatito": "Tupungatito",
    "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan", "Copahue": "Copahue",
    "Llaima": "Llaima", "Villarrica": "Villarrica", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle", "Chaiten": "Chaiten",
}


def dt(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def cargar_referencia():
    ref = defaultdict(list)  # (volcan csv) -> [(datetime, tipo, vrp, canal)]
    for path, canal in (("latest_consolidado.csv", "tabla"),
                        ("data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", "ocr")):
        for row in csv.DictReader(open(path, encoding="utf-8")):
            if row["Sensor"] != "VIIRS":
                continue
            try:
                vrp = float(row["VRP_MW"] or 0)
            except ValueError:
                vrp = 0.0
            ref[row["Volcan"]].append((dt(row["Fecha_Satelite_UTC"]), row["Tipo_Registro"], vrp, canal))
    return ref


def buscar(ref, vol, t):
    """Filas de MIROVA (Sensor VIIRS) del mismo volcan a <= 60 min."""
    return [f for f in ref.get(NOMBRES.get(vol, vol), []) if abs((f[0] - t).total_seconds()) <= 3600]


def inner_del_tablero():
    src = open("frontend/index.html", encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'name:\s*"([A-Za-z]+)".*?inner_radius_km:\s*(\d+)', src):
        out[m.group(1)] = int(m.group(2))
    return out


def main():
    recs = json.load(open(os.path.join(AQUI, "records_v750.json"), encoding="utf-8"))
    pred = json.load(open(os.path.join(AQUI, "predicado_tablero_salida.json"), encoding="utf-8"))
    assert len(recs) == len(pred)
    fechas = sorted(r["datetime_utc"] for r in recs)
    print("records V750 con cumulo: %d ; ventana de observacion %s a %s" % (len(recs), fechas[0], fechas[-1]))
    print("avisos A119 para esa ventana:")
    for a in crm.avisos_de_ventana(fechas[0][:10], fechas[-1][:10]):
        print("   -", a)

    tab = inner_del_tablero()
    for v in sorted({r["volcano"] for r in recs}):
        y = next(r["inner_radius_km"] for r in recs if r["volcano"] == v)
        if v in tab and tab[v] != y:
            print("OJO inner_radius distinto tablero %s vs yaml %s en %s" % (tab[v], y, v))
    print("inner_radius_km del tablero coincide con volcanoes.yaml en los volcanes con records (comprobado arriba si no hay OJO)")

    ref = cargar_referencia()

    filas = []
    for r, p in zip(recs, pred):
        pc = r["primary_cluster"]
        inner = r["inner_radius_km"]
        dentro = pc.get("centroid_dist_km") is not None and inner is not None and pc["centroid_dist_km"] <= inner
        cero = (pc.get("vrp_mw") or 0) == 0
        reg = "K" if r["datetime_utc"][:10] >= K_DESDE else "pre-K"
        t = dt(r["datetime_utc"])
        m = buscar(ref, r["volcano"], t)
        alertas = [f for f in m if f[1] in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")]
        filas.append(dict(r=r, p=p, dentro=dentro, cero=cero, reg=reg, miro=len(m) > 0,
                          alerta=len(alertas) > 0, protegida=any(f[2] >= 1.0 for f in alertas),
                          vrp_mirova=max((f[2] for f in alertas), default=None)))

    def resumen(titulo, sel):
        n = len(sel)
        ocultos = [x for x in sel if (not x["p"]["valid"]) and x["p"]["eq_vrp"] == 0]
        print("\n== %s: n=%d" % (titulo, n))
        if not n:
            return
        print("   tablero: isValidDetection=false y mirovaEqVrp=0 (ocultos): %d ; visibles: %d" % (len(ocultos), n - len(ocultos)))
        print("   MIROVA miro (alguna fila VIIRS a <=60 min): %d ; alerta de MIROVA: %d ; protegida (>=1 MW): %d" % (
            sum(x["miro"] for x in sel), sum(x["alerta"] for x in sel), sum(x["protegida"] for x in sel)))
        print("   por volcan:", dict(Counter(x["r"]["volcano"] for x in sel)))
        print("   distance_class:", dict(Counter(x["r"]["distance_class"] for x in sel)))
        print("   single_pixel_mode:", dict(Counter(bool(x["r"]["primary_cluster"].get("single_pixel_mode")) for x in sel)),
              " n_pixels:", dict(Counter(x["r"]["primary_cluster"].get("n_pixels") for x in sel).most_common(6)))

    cumbre = [x for x in filas if x["dentro"]]
    print("\n#### cumulo dentro de inner_radius_km (centroid_dist_km <= inner): %d de %d" % (len(cumbre), len(filas)))
    for reg in ("pre-K", "K"):
        sel = [x for x in cumbre if x["reg"] == reg]
        fr = sorted(x["r"]["datetime_utc"] for x in sel)
        print("\n######## REGIMEN %s (obs %s a %s): cumulos de cumbre %d" % (reg, fr[0] if fr else "-", fr[-1] if fr else "-", len(sel)))
        resumen("cumbre con pc.vrp_mw == 0", [x for x in sel if x["cero"]])
        resumen("CONTROL cumbre con pc.vrp_mw > 0", [x for x in sel if not x["cero"]])

    # --- causa del cero ---
    print("\n#### causa del cero en cumulos de cumbre (todos los regimenes)")
    ceros = [x for x in cumbre if x["cero"]]
    cat = Counter()
    ejemplos = defaultdict(list)
    for x in ceros:
        r = x["r"]
        tbg, tmax, apmax = r["t_bg_k"], r["t_max_k"], r["ap_bt_max"]
        if r["diag_sanity_cap"] is not None:
            k = "sanity_cap"
        elif r["primary_cluster"].get("d9_capped"):
            k = "d9"
        elif apmax is not None and tbg is not None and apmax <= tbg:
            k = "todos los pixeles publicados <= t_bg (recorte explica)"
        elif apmax is not None and tbg is not None and apmax > tbg:
            k = "hay pixel publicado > t_bg y aun asi 0 (OTRA causa)"
        elif r["n_pixels_json"] == 0:
            k = "sin anomaly_pixels en el record"
        else:
            k = "sin dato"
        cat[k] += 1
        if len(ejemplos[k]) < 3:
            ejemplos[k].append((r["volcano"], r["datetime_utc"], r["sensor"], "t_bg=%s t_max=%s ap_bt_max=%s vrp_mw=%s n_px=%s" % (
                tbg, tmax, apmax, r["vrp_mw"], r["primary_cluster"].get("n_pixels"))))
    for k, v in cat.most_common():
        print("   %-60s %d" % (k, v))
        for e in ejemplos[k]:
            print("        ej:", e)
    # t_max - t_bg en los ceros vs en los no ceros
    def med(v):
        v = sorted(v); return v[len(v) // 2] if v else None
    print("   mediana(t_max_k - t_bg_k) en ceros de cumbre: %s (n=%d) ; en no ceros de cumbre: %s (n=%d)" % (
        med([x["r"]["t_max_k"] - x["r"]["t_bg_k"] for x in ceros if x["r"]["t_max_k"] is not None and x["r"]["t_bg_k"] is not None]), len(ceros),
        med([x["r"]["t_max_k"] - x["r"]["t_bg_k"] for x in cumbre if not x["cero"] and x["r"]["t_max_k"] is not None and x["r"]["t_bg_k"] is not None]),
        len([x for x in cumbre if not x["cero"]])))
    print("   t_bg_k mediana ceros: %s ; no ceros: %s" % (med([x["r"]["t_bg_k"] for x in ceros]), med([x["r"]["t_bg_k"] for x in cumbre if not x["cero"]])))

    # --- recorte PARCIAL: cumulos con magnitud > 0 pero con pixeles publicados en 0 (bt <= t_bg) ---
    print("\n#### recorte parcial en cumulos de cumbre con magnitud > 0")
    parc = [x for x in cumbre if not x["cero"] and x["r"]["ap_bt_min"] is not None and x["r"]["t_bg_k"] is not None
            and x["r"]["ap_bt_min"] <= x["r"]["t_bg_k"]]
    print("   records con algun anomaly_pixel con bt_k <= t_bg_k: %d de %d (anomaly_pixels es top-100 de toda la escena, no solo el cumulo)" % (
        len(parc), len([x for x in cumbre if not x["cero"]])))

    # --- single_pixel_mode en cumulos de cumbre > 0: el record publica el MAX, el .m suma ---
    print("\n#### single_pixel_mode (vrp = max por pixel en vez de suma) en cumulos de cumbre con magnitud > 0")
    spm = [x for x in cumbre if not x["cero"] and x["r"]["primary_cluster"].get("single_pixel_mode") and x["r"]["primary_cluster"].get("n_pixels", 0) >= 2]
    print("   cumulos de cumbre con single_pixel_mode=True y n_pixels>=2: %d de %d" % (len(spm), len([x for x in cumbre if not x["cero"]])))
    razones = []
    for x in spm:
        r = x["r"]
        if r["n_anomalous_pixels"] == r["primary_cluster"]["n_pixels"] and r["ap_vrp_sum"]:
            razones.append(r["ap_vrp_sum"] / r["primary_cluster"]["vrp_mw"])
    razones.sort()
    print("   de ellos, cumulo = toda la escena (n_anomalous_pixels == n_pixels), suma(anomaly_pixels)/pc.vrp_mw: n=%d mediana=%.3f max=%.3f" % (
        len(razones), razones[len(razones) // 2] if razones else float("nan"), razones[-1] if razones else float("nan")))
    por_reg = Counter(x["reg"] for x in spm)
    print("   por regimen:", dict(por_reg), " alertas MIROVA entre ellos:", sum(x["alerta"] for x in spm), " protegidas:", sum(x["protegida"] for x in spm))

    # --- lista de los ceros de cumbre que son alerta de MIROVA ---
    print("\n#### ceros de cumbre que MIROVA publico como alerta (VIIRS 750, <=60 min)")
    for x in ceros:
        if x["alerta"]:
            r = x["r"]
            print("   %s %s %s pc=%s dist=%s t_bg=%s t_max=%s MIROVA=%s MW reg=%s tablero_valid=%s" % (
                r["volcano"], r["datetime_utc"], r["sensor"], r["primary_cluster"]["vrp_mw"], r["primary_cluster"]["centroid_dist_km"],
                r["t_bg_k"], r["t_max_k"], x["vrp_mirova"], x["reg"], x["p"]["valid"]))

    json.dump([dict(volcano=x["r"]["volcano"], datetime_utc=x["r"]["datetime_utc"], sensor=x["r"]["sensor"], reg=x["reg"],
                    dentro=x["dentro"], cero=x["cero"], valid=x["p"]["valid"], eq_vrp=x["p"]["eq_vrp"], miro=x["miro"],
                    alerta=x["alerta"], protegida=x["protegida"], vrp_mirova=x["vrp_mirova"],
                    pc=x["r"]["primary_cluster"], t_bg_k=x["r"]["t_bg_k"], t_max_k=x["r"]["t_max_k"], ap_bt_max=x["r"]["ap_bt_max"])
               for x in filas], open(os.path.join(AQUI, "cruce_v750_salida.json"), "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
