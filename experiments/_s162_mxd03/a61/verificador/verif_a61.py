# -*- coding: utf-8 -*-
"""Verificador S162 A61 (contexto limpio). Lee los artefactos del A/B y la referencia congelada POR SU CUENTA
(no importa cargar_a61 ni el evaluador). Uso: python -I verif_a61.py  (desde cualquier carpeta)

Mediciones (cada una con sus dos preguntas en el encabezado de su bloque de salida):
 M1  E1: distancias al vent recomputadas contra pc_dist del pipeline; rango real; nulo con los brazos R.
 M2  E2: identidad del pixel con una variable que NO depende de la geolocalizacion (t_max_k, n_first_pass, sigma);
     ruido del residuo en el grupo de pixel conocido; separacion por indice crater-vs-cumulo.
 M3  E3: independencia de la vara VIIRS (separacion temporal, satelite, si X sigue al objeto VIIRS o solo al vent).
 M4  E4: Distancia_km de MIROVA contra la CELDA de la grilla fija de MIROVA (TIF), dos hipotesis de celda de
     referencia, solo CONS (OCR sin distancia medida antes del 2026-06-13, A119).
 M5  H5: final_dist medido desde el centroide del volcan (no del vent).
 M6  H7: lado vs frame del pixel del crater, por hora UTC.
 M7  H1/H6: records con posicion absurda; control de modulo de R.
 M8  H2: modelo de desfase de indice (zoom order=1) recomputado aqui.
 M9  Cobertura del crater en el borde del granulo (hallazgo propio).
"""
import collections
import csv
import glob
import io
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas")
REF = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\ref")
EXP = Path(r"C:\vrp-trabajo\s162-a61\experiments\_s162_mxd03")
TIFD = Path(__file__).resolve().parent / "tif_bajados"
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Planchon-Peteroa": "PlanchonPeteroa", "PlanchonPeteroa": "PlanchonPeteroa"}
CENTRO = {"Lascar": (-23.369, -67.732), "NevadosDeChillan": (-36.863, -71.377), "Villarrica": (-39.42, -71.93)}


def hav(a, b, c, d):
    r = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin(math.radians(c - a) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(x))


def ne(lat0, lon0, lat, lon):
    return (lat - lat0) * 111.32, (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2))


def cargar():
    recs = []
    for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            if r.get("tipo") == "record":
                recs.append(r)
    return recs


def pos(b):
    return (b["pc_lat"], b["pc_lon"]) if b and b.get("pc_lat") is not None else None


def ref_modis():
    out = []
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        for r in csv.DictReader(open(REF / nombre, encoding="utf-8", newline="")):
            if r.get("Sensor") != "MODIS":
                continue
            vol = ALIAS.get(r["Volcan"], r["Volcan"])
            try:
                dt = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            try:
                dist = float(r["Distancia_km"])
            except (TypeError, ValueError):
                dist = None
            try:
                vrp = float(r["VRP_MW"])
            except (TypeError, ValueError):
                vrp = None
            out.append({"vol": vol, "dt": dt, "tipo": r["Tipo_Registro"], "dist": dist, "vrp": vrp, "src": src})
    return out


def tif_grilla(vol):
    import rasterio
    nombre = {"Lascar": "Lascar_20260510_012500_MODIS.tif", "NevadosDeChillan": "ChillanNevadosde_20260509_035703_MODIS.tif",
              "Villarrica": "Villarrica_20260509_040028_MODIS.tif"}[vol]
    with rasterio.open(TIFD / nombre) as ds:
        return ds.transform, ds.shape


def celda(T, lat, lon):
    col = int(math.floor((lon - T.c) / T.a))
    row = int(math.floor((lat - T.f) / T.e))
    return row, col


def main():
    recs = cargar()
    ok = [r for r in recs if r.get("estado") == "ok"]
    print("records tipo=record: %d | estado ok: %d | estados: %s" % (len(recs), len(ok), dict(collections.Counter(r.get("estado") for r in recs))))
    prot = [r for r in ok if r["lab"] == "protegida"]
    P = [r for r in prot if r["pub"]["K"] == 1 and pos(r["brazos"]["K"]) and pos(r["brazos"]["X"])]
    print("protegidas %d | K publica y cumulo en K y X: %d | claves (vol,dt) unicas: %d" % (len(prot), len(P), len({(r['vol'], r['dt']) for r in P})))

    # ------------------------------------------------------------------ M1
    print("\n== M1 (E1) distancias al vent")
    print("   P1: si X se hubiera ido lejos, dx creceria; P2: si X==K, dx==dk en todas (se cuenta). Control: pc_dist del pipeline vs mi haversine desde r['vent'].")
    dk, dx, err, inn, dcc = [], [], [], [], 0
    for r in P:
        v = r["vent"]
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        a, b = hav(v[0], v[1], *pos(K)), hav(v[0], v[1], *pos(X))
        dk.append(a); dx.append(b)
        err.append(max(abs(a - K["pc_dist"]), abs(b - X["pc_dist"])))
        inn.append((a <= r["inner"], b <= r["inner"]))
        dcc += K["dc"] != X["dc"]
    print("   max |mi dist - pc_dist del pipeline|: %.4f km (n %d) -> el vent del arnes es el ancla del pipeline" % (max(err), len(err)))
    print("   X: min %.3f mediana %.3f max %.3f | K: min %.3f mediana %.3f max %.3f | X<K en %d de %d | dx==dk en %d" % (
        min(dx), statistics.median(dx), max(dx), min(dk), statistics.median(dk), max(dk), sum(b < a for a, b in zip(dk, dx)), len(dx),
        sum(abs(a - b) < 1e-6 for a, b in zip(dk, dx))))
    print("   X p10 (indice n//10 ordenado) %.3f | X en orden: %s" % (sorted(dx)[len(dx) // 10], [round(x, 2) for x in sorted(dx)[:6]]))
    print("   dentro del inner K %d X %d | dc K!=X: %d | dc de K: %s" % (sum(i[0] for i in inn), sum(i[1] for i in inn), dcc,
                                                                    dict(collections.Counter(r["brazos"]["K"]["dc"] for r in P))))
    # nulo: brazos R (traslacion del mismo modulo en rumbo arbitrario): cuantas acercan el cumulo
    acerca, tot = 0, 0
    for r in P:
        if not r["r_nulos"]:
            continue
        dK = r["brazos"]["K"]["pc_dist"]
        for b in ["R%02d" % k for k in range(20)]:
            br = r["brazos"].get(b)
            if br and br.get("pc_dist") is not None:
                tot += 1
                acerca += br["pc_dist"] < dK
    print("   NULO R (mismo modulo, rumbo sorteado): el cumulo queda mas cerca del vent que K en %d de %d brazos (%.1f %%); X: %d de %d" % (
        acerca, tot, 100.0 * acerca / max(tot, 1), sum(b < a for a, b in zip(dk, dx)), len(dx)))

    # ------------------------------------------------------------------ M2
    print("\n== M2 (E2) identidad del pixel con variables que NO dependen de la geolocalizacion")
    print("   P1: si X tomara otro pixel, t_max (BT del pixel mas caliente del cumulo) cambiaria salvo empate; P2: control: brazos R con cambio de npx o de pc_vrp>5 %.")
    tab = {(f["vol"], f["dt"]): f for f in csv.DictReader(open(EXP / "a61" / "a61_protegidas.csv", encoding="utf-8"))}
    g = {}
    for r in P:
        f = tab[(r["vol"], r["dt"])]
        if f["K_npx"] == "1" and f["X_npx"] == "1" and f["pico_es_pcK"] == "True" and f["pico_es_pcX"] == "True":
            g[(r["vol"], r["dt"])] = 1
        elif f["K_npx"] == f["X_npx"] and float(f["residuo_km"]) < 0.3:
            g[(r["vol"], r["dt"])] = 2
        else:
            g[(r["vol"], r["dt"])] = 3
    print("   grupos recomputados desde el csv: %s" % dict(collections.Counter(g.values())))
    for grp in (1, 2, 3):
        rs = [r for r in P if g[(r["vol"], r["dt"])] == grp]
        tm = sum(1 for r in rs if r["brazos"]["K"]["t_max_k"] == r["brazos"]["X"]["t_max_k"])
        fp = sum(1 for r in rs if r["brazos"]["K"]["diag_n_first_pass_pixels"] == r["brazos"]["X"]["diag_n_first_pass_pixels"])
        print("   grupo %d (n %d): t_max_k igual K/X en %d | n_first_pass igual en %d" % (grp, len(rs), tm, fp))
        if grp >= 2:
            for r in rs:
                K, X = r["brazos"]["K"], r["brazos"]["X"]
                f = tab[(r["vol"], r["dt"])]
                d = r["desplazamiento"]
                pk = r.get("pico") or {}
                print("      %s %s z=%.1f npx %s/%s t_max %s/%s first %s/%s recap %s/%s res %s | crater idx (%d,%d) pico idx (%s,%s)" % (
                    r["vol"][:7], r["dt"], r["z"], K["pc_n_pixels"], X["pc_n_pixels"], K["t_max_k"], X["t_max_k"],
                    K["diag_n_first_pass_pixels"], X["diag_n_first_pass_pixels"], K["diag_n_second_pass_recapture"],
                    X["diag_n_second_pass_recapture"], f["residuo_km"], d["linea"], d["frame"], pk.get("linea"), pk.get("frame")))
    # control positivo del t_max: brazos R donde el cumulo cambia de npx
    cam, tmd = 0, 0
    for r in ok:
        K = r["brazos"]["K"]
        if not K or K.get("pc_n_pixels") is None:
            continue
        for b, br in r["brazos"].items():
            if b in ("K", "K2") or not br or br.get("pc_n_pixels") is None:
                continue
            if br["pc_n_pixels"] != K["pc_n_pixels"]:
                cam += 1
                tmd += br["t_max_k"] != K["t_max_k"]
    print("   CONTROL POSITIVO t_max: brazos (X y R, todos los records) con npx distinto a K: %d; t_max distinto en %d (%.1f %%)" % (cam, tmd, 100.0 * tmd / max(cam, 1)))
    # que es t_max: escena o cumulo? brazos con npx igual pero t_max distinto
    igual_npx_tdist = 0
    n_igual = 0
    for r in ok:
        K = r["brazos"]["K"]
        if not K or K.get("pc_n_pixels") is None:
            continue
        for b in ["X"] + ["R%02d" % k for k in range(20)]:
            br = r["brazos"].get(b)
            if br and br.get("pc_n_pixels") == K["pc_n_pixels"]:
                n_igual += 1
                igual_npx_tdist += br["t_max_k"] != K["t_max_k"]
    print("   brazos con npx igual a K: %d; con t_max distinto: %d" % (n_igual, igual_npx_tdist))
    # ruido del residuo en el grupo 1 (pixel conocido): contra cenit y separacion por indice crater-pico
    print("   residuo en grupo 1 (mismo pixel por indice) contra cenit y separacion |crater-pico| en indices:")
    filas1 = []
    for r in P:
        if g[(r["vol"], r["dt"])] != 1:
            continue
        f = tab[(r["vol"], r["dt"])]
        d, pk = r["desplazamiento"], r["pico"]
        filas1.append((float(f["residuo_km"]), r["z"], abs(d["linea"] - pk["linea"]), abs(d["frame"] - pk["frame"]), r["vol"], r["dt"]))
    for x in sorted(filas1, reverse=True)[:6]:
        print("      res %.3f z %.1f dlinea %d dframe %d %s %s" % x)
    print("      res > 0,3 en grupo 1: %d de %d | dlinea >= 10 (otro escaneo) en: %d" % (sum(1 for x in filas1 if x[0] > 0.3), len(filas1), sum(1 for x in filas1 if x[2] >= 10)))

    # ------------------------------------------------------------------ M3
    print("\n== M3 (E3) vara VIIRS")
    print("   P1: si la vara fuera el mismo granulo, dt VIIRS == dt MODIS; P2: si la vara solo midiera el vent, X->VIIRS no seria menor que X->vent.")
    vara = json.load(open(EXP / "vara_viirs_mxd03.json", encoding="utf-8"))
    print("   meta: main_congelado %s | ventana_h %s | sensores %s" % (vara["meta"]["main_congelado"][:10], vara["meta"]["ventana_h"], vara["meta"]["sensores"]))
    gaps, sats, xv_lt_xvent, nv, xvent_l, xv_l, vv_l = [], collections.Counter(), 0, 0, [], [], []
    for r in P:
        vv = vara["granulos"].get("%s|%s" % (r["vol"], r["clave"]))
        if not vv:
            continue
        nivel = "estricta" if vv["estricta"]["pasadas"] else "amplia"
        ps = vv[nivel]["pasadas"]
        if not ps:
            continue
        nv += 1
        t0 = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
        gaps.append(min(abs((datetime.strptime(p["datetime_utc"], "%Y-%m-%d %H:%M") - t0).total_seconds()) / 60 for p in ps))
        for p in ps:
            sats[p["sensor"]] += 1
        vlat, vlon = statistics.median(p["lat"] for p in ps), statistics.median(p["lon"] for p in ps)
        px = pos(r["brazos"]["X"])
        x_v, x_vent = hav(px[0], px[1], vlat, vlon), hav(px[0], px[1], *r["vent"])
        vvent = hav(vlat, vlon, *r["vent"])
        xv_lt_xvent += x_v < x_vent
        xv_l.append(x_v); xvent_l.append(x_vent); vv_l.append(vvent)
    print("   con vara: %d | separacion temporal minima MODIS-VIIRS (min): min %.0f mediana %.0f max %.0f | iguales a 0: %d" % (
        nv, min(gaps), statistics.median(gaps), max(gaps), sum(1 for x in gaps if x == 0)))
    print("   satelites VIIRS: %s" % dict(sats))
    print("   objeto VIIRS al vent: mediana %.2f, max %.2f | X al objeto VIIRS mas cerca que X al vent en %d de %d | mediana X->VIIRS %.2f vs X->vent %.2f" % (
        statistics.median(vv_l), max(vv_l), xv_lt_xvent, nv, statistics.median(xv_l), statistics.median(xvent_l)))
    print("   correlacion de Spearman-aprox (rangos) entre X->VIIRS y X->vent: %.2f" % (
        np.corrcoef(np.argsort(np.argsort(xv_l)), np.argsort(np.argsort(xvent_l)))[0, 1]))

    # ------------------------------------------------------------------ M4
    print("\n== M4 (E4) Distancia_km de MIROVA contra la celda de la grilla FIJA de MIROVA (TIF 51x51)")
    print("   P1: si la hipotesis de celda de referencia fuera la equivocada, las distancias predichas no calzarian; P2: control: distancia predicha con posicion al azar dentro de 2 km.")
    ref = ref_modis()
    idx = collections.defaultdict(list)
    for f in ref:
        idx[f["vol"]].append(f)
    resumen = collections.Counter()
    rng = np.random.default_rng(0)
    nulo_hits = collections.Counter()
    nulo_tot = 0
    det = []
    for r in P:
        t = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        al = [f for f in idx[r["vol"]] if abs((f["dt"] - t).total_seconds()) <= 120 and f["tipo"].startswith("ALERTA")
              and f["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR" and f["dist"] is not None]
        cons = sorted({f["dist"] for f in al if f["src"] == "CONS"})
        ocr = sorted({f["dist"] for f in al if f["src"] == "OCR"})
        T, sh = tif_grilla(r["vol"])
        cc = (sh[0] // 2, sh[1] // 2)
        ccr = celda(T, *r["vent"])
        dd = {}
        for b in ("K", "X"):
            rc = celda(T, *pos(r["brazos"][b]))
            for nom, c0 in (("centro", cc), ("crater", ccr)):
                dd[(b, nom)] = round(math.hypot(rc[0] - c0[0], rc[1] - c0[1]), 2)
        for k_, v_ in dd.items():
            resumen[(k_, "CONS")] += any(abs(v_ - m) < 0.02 for m in cons)
        resumen["n_cons"] += bool(cons)
        resumen["cons0"] += 0.0 in cons
        resumen["cualquiera0"] += 0.0 in (cons + ocr)
        resumen["ocr0_sin_cons0"] += (0.0 in ocr) and (0.0 not in cons)
        if cons:
            for _ in range(20):
                ang, rad = rng.uniform(0, 2 * math.pi), 2.0 * math.sqrt(rng.uniform())
                la = r["vent"][0] + rad * math.cos(ang) / 111.32
                lo = r["vent"][1] + rad * math.sin(ang) / (111.32 * math.cos(math.radians(r["vent"][0])))
                rc = celda(T, la, lo)
                nulo_tot += 1
                for nom, c0 in (("centro", cc), ("crater", ccr)):
                    nulo_hits[nom] += any(abs(round(math.hypot(rc[0] - c0[0], rc[1] - c0[1]), 2) - m) < 0.02 for m in cons)
        det.append((r["vol"], r["dt"], cons, ocr, dd, ccr, cc))
    print("   protegidas con alguna distancia CONS: %d | con 0,0 en CONS: %d | con 0,0 en CONS u OCR: %d | 0,0 solo por OCR: %d" % (
        resumen["n_cons"], resumen["cons0"], resumen["cualquiera0"], resumen["ocr0_sin_cons0"]))
    for b in ("K", "X"):
        for nom in ("centro", "crater"):
            print("   brazo %s, referencia = celda del %s de la grilla: calza con alguna distancia CONS en %d de %d" % (
                b, nom, resumen[((b, nom), "CONS")], resumen["n_cons"]))
    print("   NULO (posicion al azar a <= 2 km del vent, 20 por protegida): calza ref centro %.1f %%, ref crater %.1f %%" % (
        100.0 * nulo_hits["centro"] / nulo_tot, 100.0 * nulo_hits["crater"] / nulo_tot))
    print("   celda del vent y celda central por volcan: %s" % {v: (c[5], c[6]) for v, c in {d[0]: d for d in det}.items()})
    print("   detalle (vol dt | CONS | OCR | K centro/crater | X centro/crater):")
    for vol, dt, cons, ocr, dd, ccr, cc in det:
        print("      %s %s | CONS %s | OCR %s | K %s/%s | X %s/%s" % (vol[:7], dt, cons, ocr, dd[("K", "centro")], dd[("K", "crater")],
                                                                   dd[("X", "centro")], dd[("X", "crater")]))
    # E4 tal como lo enuncio el auditor, pero separado por fuente
    z30 = [d for d in det if 0.0 in (d[2] + d[3])]
    print("   E4 literal: con 0,0 (CONS u OCR) %d | de ellas con 0,0 en CONS %d" % (len(z30), sum(1 for d in z30 if 0.0 in d[2])))

    # ------------------------------------------------------------------ M5
    print("\n== M5 (H5) final_dist medido desde el centroide del volcan")
    print("   P1: si final_dist se midiera desde el vent, final_dist == pc_dist en cumulos de 1 pixel con final==pc; P2: se cuenta cuantas veces coincide con cada ancla.")
    nc = nv_ = n1 = 0
    for r in ok:
        cen = CENTRO.get(r["vol"])
        for b, br in r["brazos"].items():
            if not br or br.get("final_lat") is None or br.get("final_dist") is None:
                continue
            n1 += 1
            if cen:
                nc += abs(hav(cen[0], cen[1], br["final_lat"], br["final_lon"]) - br["final_dist"]) <= 0.011
            nv_ += abs(hav(r["vent"][0], r["vent"][1], br["final_lat"], br["final_lon"]) - br["final_dist"]) <= 0.011
    print("   brazos con final (todos los records, todos los brazos): %d | final_dist == dist desde vent (±11 m): %d | == desde centroide (solo Lascar/NdC/Villarrica): %d" % (n1, nv_, nc))
    print("   Lascar: centroide a %.3f km del vent, rumbo %s" % (hav(-23.36293, -67.731416, -23.369, -67.732), "S" if -23.369 < -23.36293 else "N"))
    r = next(x for x in ok if x["vol"] == "Lascar" and x["dt"] == "2026-03-12 07:25")
    far = [(b, br["pc_dist"], br["final_dist"], br["dc"], r["pub"][b]) for b, br in r["brazos"].items() if br and br["dc"] == "far"]
    print("   Lascar 2026-03-12 07:25 brazos far: %s" % far)
    print("   en esos, pc_dist <= inner (5) y final_dist > 5: %d de %d | pub 0 en %d" % (
        sum(1 for x in far if x[1] <= 5 and x[2] > 5), len(far), sum(1 for x in far if x[4] == 0)))

    # ------------------------------------------------------------------ M6
    print("\n== M6 (H7) lado contra frame del pixel del crater")
    pob = json.load(open(EXP / "poblacion.json", encoding="utf-8"))
    mal = collections.Counter()
    malh = collections.Counter()
    for r in ok:
        fr = r["desplazamiento"]["frame"]
        if fr < 100 and r["lado"] == "otro":
            mal["f<100 otro"] += 1
            malh[(r["sensor"], r["dt"][11:13])] += 1
        if fr < 100:
            mal["f<100"] += 1
        if fr > 1253 and r["lado"] == "f0":
            mal["f>1253 f0"] += 1
        if fr > 1253:
            mal["f>1253"] += 1
        if 100 <= fr <= 1253:
            mal["centro"] += 1
    print("   %s | horas UTC de los mal etiquetados: %s" % (dict(mal), dict(malh)))
    noct = collections.Counter((r["sensor"], r["dt"][11:13]) for r in ok)
    crep = {k: v for k, v in noct.items() if k[1] in ("12", "21", "22", "11", "23")}
    print("   records por (sensor, hora UTC) en horas 11,12,21,22,23: %s" % crep)
    # con frame < 100 y hora de crepusculo, cuantos quedan bien etiquetados
    cre = [r for r in ok if r["dt"][11:13] in ("12", "21", "22") ]
    print("   records en horas 12/21/22 UTC: %d | de ellos lado 'otro': %d | frame<100: %d | frame>1253: %d" % (
        len(cre), sum(1 for r in cre if r["lado"] == "otro"), sum(1 for r in cre if r["desplazamiento"]["frame"] < 100),
        sum(1 for r in cre if r["desplazamiento"]["frame"] > 1253)))
    print("   protegidas en horas 12/21/22: %d" % sum(1 for r in prot if r["dt"][11:13] in ("12", "21", "22")))

    # ------------------------------------------------------------------ M7
    print("\n== M7 (H1/H6) posiciones absurdas y modulo de R")
    absur = [r for r in ok if r["desplazamiento"]["km"] > 100]
    for r in absur:
        print("   %s %s lab %s z %.1f n_fill %s desp %.1f km | K anillo %s n_anom %s | X anillo %s n_anom %s | pub %s/%s | nulos km_pedido %s aplicado %s" % (
            r["vol"], r["dt"], r["lab"], r["z"], r.get("n_fill_mxd03"), r["desplazamiento"]["km"],
            r["brazos"]["K"] and r["brazos"]["K"]["diag_n_bg_anillo"], r["brazos"]["K"] and r["brazos"]["K"]["n_anom"],
            r["brazos"]["X"] and r["brazos"]["X"]["diag_n_bg_anillo"], r["brazos"]["X"] and r["brazos"]["X"]["n_anom"],
            r["pub"]["K"], r["pub"]["X"], (r["nulos"] or [{}])[0].get("km_pedido"), (r["nulos"] or [{}])[0].get("km_aplicado")))
    nf = [r for r in ok if r.get("n_fill_mxd03", 0) > 0]
    difs = [r["brazos"]["K"]["diag_n_bg_anillo"] - r["brazos"]["X"]["diag_n_bg_anillo"] for r in nf if r["brazos"]["K"] and r["brazos"]["X"]]
    sin = [r["brazos"]["K"]["diag_n_bg_anillo"] - r["brazos"]["X"]["diag_n_bg_anillo"] for r in ok if r.get("n_fill_mxd03", 0) == 0 and r["brazos"]["K"] and r["brazos"]["X"]]
    sp5, sp95 = np.percentile(sin, 5), np.percentile(sin, 95)
    print("   records con n_fill>0: %d | anillo K-X: >0 en %d, <0 en %d, =0 en %d | fuera del p5-p95 del nulo (%.0f, %.0f): <p5 %d, >p95 %d" % (
        len(nf), sum(1 for d in difs if d > 0), sum(1 for d in difs if d < 0), sum(1 for d in difs if d == 0), sp5, sp95,
        sum(1 for d in difs if d < sp5), sum(1 for d in difs if d > sp95)))
    print("   mediana anillo K-X con relleno %.1f vs sin relleno %.1f" % (statistics.median(difs), statistics.median(sin)))

    # ------------------------------------------------------------------ M8
    print("\n== M8 (H2) error de indice de scipy.ndimage.zoom(order=1) con nodo grueso en 5i+2")
    from scipy.ndimage import zoom
    for n_c, n_f in ((271, 1354), (406, 2030)):
        c = (5 * np.arange(n_c) + 2).astype(np.float64)
        f = zoom(c, n_f / n_c, order=1)
        e = f - np.arange(n_f)
        cero = int(np.argmin(np.abs(e)))
        print("   %d->%d: error en 0 %+.2f, en el ultimo %+.2f, cruza 0 en %d, min %+.2f max %+.2f" % (n_c, n_f, e[0], e[-1], cero, e.min(), e.max()))
    salida = open(EXP / "a61" / "seguimientos_salida.txt", encoding="utf-8").read().splitlines()
    print("   modelo vs mediana por tramo de frame (de seguimientos_salida.txt §2):")
    for l in salida:
        if l.strip().startswith("[") and "px *" in l:
            p = [x.strip() for x in l.split("|")]
            med = float(p[3]); mod = float(p[5].split("=")[-1].replace("km", ""))
            print("      %s mediana %.2f modelo %.2f -> %+.0f %%" % (p[0], med, mod, 100 * (mod - med) / med))

    # ------------------------------------------------------------------ M9
    print("\n== M9 (propio) pixel del crater pegado al borde del granulo (crater posiblemente fuera del granulo)")
    print("   P1: si el crater estuviera fuera del granulo, el pixel MxD03 mas cercano estaria en la primera/ultima linea o frame; P2: se reporta la distancia de ese pixel al vent no disponible: SIN DATO de distancia.")
    borde = [r for r in ok if r["desplazamiento"]["linea"] in (0, 1, 2028, 2029) or r["desplazamiento"]["frame"] in (0, 1353)]
    print("   records con el pixel del crater en linea 0/1/2028/2029 o frame 0/1353: %d | por lab: %s | publica K: %d" % (
        len(borde), dict(collections.Counter(r["lab"] for r in borde)), sum(r["pub"]["K"] for r in borde)))
    for r in borde[:12]:
        d = r["desplazamiento"]
        print("      %s %s %s lab %s linea %d frame %d z %.1f n_anom K %s pub K %s anillo K %s" % (
            r["vol"], r["dt"], r["clave"], r["lab"], d["linea"], d["frame"], r["z"], r["brazos"]["K"] and r["brazos"]["K"]["n_anom"],
            r["pub"]["K"], r["brazos"]["K"] and r["brazos"]["K"]["diag_n_bg_anillo"]))


if __name__ == "__main__":
    main()
