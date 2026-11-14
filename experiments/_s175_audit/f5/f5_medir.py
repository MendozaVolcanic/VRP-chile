# -*- coding: utf-8 -*-
"""F5 S175: mide I1 a I10 sobre los insumos de f5_base.py (base 752d348bc). Salida: f5_medir_out.json + texto.

Las dos preguntas del instrumento van en el encabezado de cada sección del informe (INFORME.md); acá cada
sección guarda su numerador, denominador y ventana, y un control positivo cuando lo hay.
"""
import bisect
import collections
import csv
import json
import os
import pickle
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5"
OUT = os.path.dirname(os.path.abspath(__file__))
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import auto_audit_weekly as aw  # noqa: E402
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402

TOL_KM = {"VIIRS375": 0.75, "VIIRS750": 1.5, "MODIS": 3.0}   # fijada por la tarea (A91)
HITO_V31 = "2026-10-09 14:01"
W_AUDIT = ("2026-09-03", "2026-11-02")   # ventana del latest.json del 2026-11-02
HOY_AUDIT = datetime(2026, 11, 2).date()
R = {}

import math  # noqa: E402
import yaml  # noqa: E402
_V = {v["name"]: v for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
MC = {n: (v["mirova_center_lat"], v["mirova_center_lon"]) for n, v in _V.items() if v.get("mirova_center_lat") is not None}


def hav(a, b, c, d):
    p = math.radians
    return 2 * 6371.0 * math.asin(math.sqrt(math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2))


def dt_of(s):
    return datetime.strptime(s[:19] if len(s) >= 19 else s[:16], "%Y-%m-%d %H:%M:%S" if len(s) >= 19 else "%Y-%m-%d %H:%M")


def cargar():
    with open(os.path.join(TMP, "f5_base.pkl"), "rb") as fh:
        return pickle.load(fh)


def crudo(B, r):
    return B["crudos"].get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")), {})


def dist_mirova(filas_alerta):
    """Distancia de MIROVA de la pasada: la de la tabla (CONS) primero; la del OCR sólo si la tabla no la tiene."""
    cons = [f for f in filas_alerta if f["source"] == "CONS" and f["dist_km"] is not None and f["dist_km"] > 0]
    if cons:
        return cons[0]["dist_km"], "CONS", cons[0]
    ocr = [f for f in filas_alerta if f["source"] == "OCR" and f["dist_km"] is not None and f["dist_km"] > 0]
    if ocr:
        return ocr[0]["dist_km"], "OCR", ocr[0]
    return None, None, (filas_alerta[0] if filas_alerta else None)


def clasificar(d_ours, d_mir, b):
    if d_ours is None or d_mir is None:
        return "iv"
    return "iii" if abs(d_ours - d_mir) > TOL_KM[b] else "i?"


# ------------------------------------------------------------------ I2 posición (pasada pareada)
def i2(B, pv):
    filas_out, cnt = [], collections.Counter()
    for r in B["recs"]:
        if r["lab"] != "pos" or not r["pub"]:
            continue
        alertas = [f for f in bp.parear(pv.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        dm, fuente, f0 = dist_mirova(alertas)
        c = crudo(B, r)
        d_fh = c.get("final_hotspot_dist_km")
        d_pc = (c.get("pc") or {}).get("centroid_dist_km")
        vrp_m = max((f["vrp_mw"] or 0) for f in alertas) if alertas else None
        prot = any(cm.alerta_protegida(f) for f in alertas)
        fecha_m = min(alertas, key=lambda f: abs((dt_of(f["fecha_utc"]).replace(tzinfo=timezone.utc) - r["dt"]).total_seconds()))["fecha_utc"]
        estrato = ("OCR_antes_V31" if fuente == "OCR" and fecha_m[:16] < HITO_V31 else
                   "OCR_desde_V31" if fuente == "OCR" else (fuente or "sin_dist"))
        cl_crudo = clasificar(d_fh, dm, r["b"])
        cl_pc = clasificar(d_pc, dm, r["b"])
        # A3: MIROVA mide desde su centro (mirova_center del KMZ, volcanoes.yaml) y final_hotspot_dist_km desde el
        # ancla de detección (vent). Se compara en un origen común: nuestro punto medido desde mirova_center.
        mc = MC.get(r["vol"])
        la, lo = c.get("final_hotspot_lat"), c.get("final_hotspot_lon")
        d_mc = round(hav(la, lo, mc[0], mc[1]), 3) if (mc and la is not None and lo is not None) else None
        cl = clasificar(d_mc, dm, r["b"])
        cnt[(r["vol"], r["b"], cl)] += 1
        filas_out.append({"vol": r["vol"], "b": r["b"], "sensor": r["sensor"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"),
                          "fecha_mirova": fecha_m, "vrp_mirova": vrp_m, "protegida": prot, "dist_mirova": dm,
                          "fuente_dist": fuente, "estrato": estrato, "d_final_hotspot": d_fh, "d_pc": d_pc,
                          "fh_source": c.get("final_hotspot_source"), "d_desde_mirova_center": d_mc,
                          "clase": cl, "clase_radio_crudo": cl_crudo, "clase_pc": cl_pc,
                          "our_lat": c.get("final_hotspot_lat"), "our_lon": c.get("final_hotspot_lon"),
                          "pc_vrp": (c.get("pc") or {}).get("vrp_mw"), "pub_disp": r.get("disp")})
    with open(os.path.join(OUT, "i2_pares.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas_out[0].keys()))
        w.writeheader()
        w.writerows(filas_out)
    tab = collections.defaultdict(collections.Counter)
    tab_prot = collections.defaultdict(collections.Counter)
    tab_estr = collections.defaultdict(collections.Counter)
    for f in filas_out:
        tab[f"{f['vol']}|{f['b']}"][f["clase"]] += 1
        tab_estr[f"{f['estrato']}|{f['b']}"][f["clase"]] += 1
        if f["protegida"]:
            tab_prot[f"{f['vol']}|{f['b']}"][f["clase"]] += 1
    tot = collections.Counter(f["clase"] for f in filas_out)
    tot_pc = collections.Counter(f["clase_pc"] for f in filas_out)
    tot_crudo = collections.Counter(f["clase_radio_crudo"] for f in filas_out)
    crudo_vs = collections.defaultdict(collections.Counter)
    for f in filas_out:
        crudo_vs[f"{f['vol']}|{f['b']}"][f["clase_radio_crudo"]] += 1
    R["I2"] = {"universo": "recs del banco con lab pos (D-9 SN) y pub=1 (predicado del tablero), ventana " + "/".join(B["win"]),
               "clase_con_origen_comun_mirova_center": dict(tot),
               "clase_radio_crudo_final_hotspot_dist_km": dict(tot_crudo),
               "clase_radio_crudo_pc_centroid_dist_km": dict(tot_pc),
               "radio_crudo_por_vol_sensor": {k: dict(v) for k, v in sorted(crudo_vs.items())},
               "por_vol_sensor": {k: dict(v) for k, v in sorted(tab.items())},
               "protegidas_por_vol_sensor": {k: dict(v) for k, v in sorted(tab_prot.items())},
               "por_estrato_fuente_distancia": {k: dict(v) for k, v in sorted(tab_estr.items())},
               "n": len(filas_out)}
    return filas_out


def control_i2():
    """Línea base roja (2): tres aciertos sintéticos."""
    casos = {"misma_pasada_mismo_pixel": clasificar(7.83, 7.83, "VIIRS750"),
             "otra_fuente_15km": clasificar(7.83 + 15.0, 7.83, "VIIRS750"),
             "sin_dist_mirova": clasificar(7.83, None, "VIIRS750")}
    R["control_I2"] = casos
    return casos


# ------------------------------------------------------------------ I1, I3, I4 sobre la ventana del audit
def audit_ventana(B):
    win = W_AUDIT
    frontera = aw.leer_frontera_k()
    vigente = aw.detector_vigente(frontera)
    coords = B["coords"]
    alertas = B["alertas"]
    mir, inst, n_diur = aw.noches_mirova_con_instante(aw.aplicar_d9(alertas, aw.REGLA_MINIMAS, B["filas"]), coords, win)
    ceses, _ = aw.leer_ceses()
    desde = aw.juzga_desde(ceses, HOY_AUDIT)
    mir, mir_ap = aw.partir_por_plataformas(mir, desde)
    rpv, _ = aw.cargar_records()
    via_modis = aw.frontera_via_modis(rpv)
    nu = aw.nuestros_por_noche(rpv, win, frontera, via_modis=via_modis)
    ours, vistos = nu["ours"], nu["vistos"]
    ev = aw.evaluar_detector(mir, ours, vistos, vigente, frontera, via_modis)
    evv = aw.evaluar_detector(mir, ours, vistos, "VIA_MODIS", frontera, via_modis) if via_modis else None
    est = aw.estratificar_magnitud(mir, ours, frontera, vigente, inst, via_modis)
    c = collections.Counter()
    for k, v in est["por_regimen"].items():
        s = k.split("|")[1]
        for rg, x in v.items():
            c[f"{s}|{rg}|n"] += x["n_noches"]
            c[f"{s}|{rg}|misma"] += x["n_misma_pasada"] or 0
    return {"frontera": frontera, "vigente": vigente, "via_modis": via_modis, "mir": mir, "inst": inst, "ours": ours,
            "vistos": vistos, "ev": ev, "evv": evv, "rpv": rpv, "n_misma": dict(c), "desde": desde}


def alertas_por_pasada(B, win, coords):
    """Pasadas de alerta nocturnas de MIROVA (cargador del audit, D-9 SN) por (vol, b) con su VRP y fuente."""
    al = aw.aplicar_d9(B["alertas"], aw.REGLA_MINIMAS, B["filas"])
    out = collections.defaultdict(list)
    for a in al:
        dt = a["fecha_utc"] or ""
        if not (dt and win[0] <= dt[:10] <= win[1]) or a["sensor_bucket"] not in aw.SENSORS or a["volcano"] not in aw.VOLS:
            continue
        d = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        lat, lon = coords[a["volcano"]]
        if aw.es_pasada_diurna_descartada(a["sensor_bucket"], lat, lon, d):
            continue
        out[(a["volcano"], a["sensor_bucket"])].append((d, a))
    for v in out.values():
        v.sort(key=lambda x: x[0])
    return out


def port_dash(rec, vol):
    pc = rec.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0.0
    cd = pc.get("centroid_dist_km")
    dc = rec.get("distance_class")
    return (0 < vrp <= aw.CAP) and cd is not None and cd <= aw.INNER[vol] and (not dc or dc == "summit")


def i1_i3_i4(B, A):
    win, coords, frontera, via_modis, vig = W_AUDIT, B["coords"], A["frontera"], A["via_modis"], A["vigente"]
    app = alertas_por_pasada(B, win, coords)
    # records por (vol, b) del detector de su noche, como nuestros_por_noche
    recs_vb = collections.defaultdict(list)
    for vol, rs in A["rpv"].items():
        for rec in rs:
            dt = rec.get("datetime_utc")
            if not (dt and win[0] <= dt[:10] <= win[1]):
                continue
            b = aw.our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            if aw.detector_de_record(rec, frontera) != aw.detector_de_noche(dt, frontera, b, via_modis):
                continue
            recs_vb[(vol, b)].append((datetime.strptime(dt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), rec))
    for v in recs_vb.values():
        v.sort(key=lambda x: x[0])
    # control: mis noches dash == las del audit
    mis_noches = {(vol, b, d.strftime("%Y-%m-%d")) for (vol, b), l in recs_vb.items() for d, rec in l if port_dash(rec, vol)}
    audit_noches = {k for k, o in A["ours"].items() if o["dash"]}
    R["control_port"] = {"noches_dash_mias": len(mis_noches), "noches_dash_audit": len(audit_noches),
                         "iguales": mis_noches == audit_noches}
    # I1
    noche_rows, pasada = [], collections.Counter()
    sin_misma = []
    for (vol, b, fecha), mvrp in A["mir"].items():
        if vol not in aw.VOLS or aw.detector_de_noche(fecha, frontera, b, via_modis) not in ("K", "VIA_MODIS"):
            continue
        if (vol, b, fecha) not in A["vistos"]:
            continue
        pases = [(d, a) for d, a in app.get((vol, b), []) if d.strftime("%Y-%m-%d") == fecha]
        hit_noche = bool(A["ours"].get((vol, b, fecha), {}).get("dash"))
        hit_pasadas = []
        for d, a in pases:
            cand = [rec for t, rec in recs_vb.get((vol, b), []) if abs((t - d).total_seconds()) <= aw.TOL_PASADA_S]
            h = any(port_dash(rec, vol) for rec in cand)
            pasada[(b, "n_pasadas", "con_record" if cand else "sin_record")] += 1
            if cand:
                pasada[(b, "hit" if h else "miss")] += 1
            hit_pasadas.append((d, a, bool(cand), h))
        misma = any(h for _, _, _, h in hit_pasadas)
        noche_rows.append((vol, b, fecha, hit_noche, misma))
        if hit_noche and not misma:
            # qué pasada nuestra dio el acierto
            hits = [(t, rec) for t, rec in recs_vb.get((vol, b), []) if t.strftime("%Y-%m-%d") == fecha and port_dash(rec, vol)]
            for t, rec in hits:
                dmin = min(pases, key=lambda x: abs((x[0] - t).total_seconds())) if pases else None
                sin_misma.append({"vol": vol, "b": b, "noche": fecha, "nuestra": t.strftime("%H:%M"), "sat": rec.get("sensor"),
                                  "mirova": [d.strftime("%H:%M:%S") + "/" + (a.get("source") or "") for d, a, _, _ in hit_pasadas],
                                  "mirova_con_record": [cr for _, _, cr, _ in hit_pasadas],
                                  "dt_min_s": round((t - dmin[0]).total_seconds()) if dmin else None,
                                  "pc_dist": (rec.get("primary_cluster") or {}).get("centroid_dist_km"),
                                  "fh_dist": rec.get("final_hotspot_dist_km"),
                                  "d_mc": (round(hav(rec["final_hotspot_lat"], rec["final_hotspot_lon"], *MC[vol]), 3)
                                           if rec.get("final_hotspot_lat") is not None and vol in MC else None),
                                  "dist_mirova": [a.get("dist_km") for _, a, _, _ in hit_pasadas]})
    por = collections.defaultdict(collections.Counter)
    for vol, b, fecha, hn, m in noche_rows:
        for k in (f"{b}", f"{vol}|{b}"):
            por[k]["noches"] += 1
            por[k]["hit_noche"] += hn
            por[k]["hit_misma_pasada"] += m
    R["I1"] = {"ventana": list(win), "detector": vig, "por_sensor_y_volcan": {k: dict(v) for k, v in sorted(por.items())},
               "pasadas_mirova": {"|".join(k): v for k, v in sorted(pasada.items())},
               "audit_recall_reproducido": A["ev"]["recall"], "audit_recall_via": (A["evv"] or {}).get("recall"),
               "n_misma_pasada_estratificar_magnitud": A["n_misma"],
               "aciertos_noche_sin_misma_pasada": sin_misma}
    # I3: port contra node en las mismas noches
    banco_noche = collections.defaultdict(int)
    banco_n = collections.defaultdict(int)
    for r in B["recs"]:
        if win[0] <= r["noche"] <= win[1]:
            banco_noche[(r["vol"], r["b"], r["noche"])] |= r["pub"]
            banco_n[(r["vol"], r["b"], r["noche"])] += 1
    dif = collections.Counter()
    ejemplos = []
    for vol, b, fecha, hn, m in noche_rows:
        node = banco_noche.get((vol, b, fecha), 0)
        dif[(b, f"port{int(hn)}_node{int(node)}")] += 1
        if bool(hn) != bool(node):
            ejemplos.append({"vol": vol, "b": b, "noche": fecha, "port": int(hn), "node": int(node),
                             "recs_banco_noche": banco_n.get((vol, b, fecha), 0)})
    rec_node = collections.Counter()
    for vol, b, fecha, hn, m in noche_rows:
        rec_node[(b, "n")] += 1
        rec_node[(b, "node")] += bool(banco_noche.get((vol, b, fecha), 0))
        rec_node[(b, "port")] += bool(hn)
    R["I3"] = {"ventana": list(win), "conteo": {"|".join(k): v for k, v in sorted(dif.items())}, "difieren": ejemplos,
               "recall_port_vs_node": {b: {"n": rec_node[(b, "n")],
                                           "port_pct": round(100 * rec_node[(b, "port")] / rec_node[(b, "n")], 1) if rec_node[(b, "n")] else None,
                                           "node_pct": round(100 * rec_node[(b, "node")] / rec_node[(b, "n")], 1) if rec_node[(b, "n")] else None}
                                       for b in aw.SENSORS}}
    # I4: ratio de magnitud noche contra misma pasada
    rat_noche, rat_pasada = collections.defaultdict(list), collections.defaultdict(list)
    for (vol, b, fecha), mvrp in A["mir"].items():
        if vol not in aw.VOLS or aw.detector_de_noche(fecha, frontera, b, via_modis) not in ("K", "VIA_MODIS"):
            continue
        o = A["ours"].get((vol, b, fecha))
        if not (o and o["dash"]) or mvrp <= 0:
            continue
        k = f"{vol}|{b}"
        rat_noche[k].append(max(o["pub"]) / mvrp)
        # misma pasada: cada pasada de alerta de MIROVA con record nuestro dash a +-120 s; razón pub/vrp de esa pasada
        rs = []
        for d, a in app.get((vol, b), []):
            if d.strftime("%Y-%m-%d") != fecha or not (a.get("vrp_mw") or 0) > 0:
                continue
            cand = [rec for t, rec in recs_vb.get((vol, b), []) if abs((t - d).total_seconds()) <= aw.TOL_PASADA_S and port_dash(rec, vol)]
            for rec in cand:
                core = rec.get("f5_core_vrp_mw")
                pub = core if (b == "VIIRS375" and isinstance(core, (int, float)) and core > 0) else rec["primary_cluster"]["vrp_mw"]
                rs.append(pub / a["vrp_mw"])
        if rs:
            rat_pasada[k].append(sorted(rs)[len(rs) // 2])
    import statistics as st
    band = aw.RATIO_BAND_MEDIAN
    tab = {}
    for k in sorted(set(rat_noche) | set(rat_pasada)):
        a_, b_ = rat_noche.get(k, []), rat_pasada.get(k, [])
        ma = round(st.median(a_), 3) if a_ else None
        mb = round(st.median(b_), 3) if b_ else None
        fb = lambda m: None if m is None else ("bajo" if m < band[0] else "alto" if m > band[1] else "en_banda")
        tab[k] = {"n_noche": len(a_), "mediana_noche": ma, "banda_noche": fb(ma), "n_misma_pasada": len(b_),
                  "mediana_misma_pasada": mb, "banda_misma_pasada": fb(mb),
                  "cambia_banda": fb(ma) != fb(mb) and mb is not None}
    R["I4"] = {"ventana": list(win), "banda": band, "por_vol_sensor": tab}


def control_i3():
    """Línea base roja (4): record con distance_class None y vrp_vent 0: el port lo cuenta, el tablero no."""
    base = {"vrp_mw": 0.4, "t_max_k": 290, "sensor": "MODIS_AQUA", "vrp_vent_mw": 0.0,
            "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}
    casos = [dict(base, distance_class="summit"), dict(base, distance_class=None), dict(base, distance_class="far")]
    res = bp.correr_node([[c, 5.0] for c in casos])
    port = [port_dash(c, "Lascar") for c in casos]
    R["control_I3"] = {"casos": ["summit", "None", "far"], "port": port, "node_pub": [x[4] for x in res]}


# ------------------------------------------------------------------ I6 tiempo
def i6(B, pv):
    dts = collections.defaultdict(list)
    for r in B["recs"]:
        if r["lab"] != "pos":
            continue
        al = [f for f in bp.parear(pv.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        if al:
            d = min(((dt_of(f["fecha_utc"]).replace(tzinfo=timezone.utc) - r["dt"]).total_seconds() for f in al), key=abs)
            dts[r["b"]].append(d)
    hist = {}
    for b, l in dts.items():
        c = collections.Counter(int(x // 30) * 30 for x in l)
        hist[b] = {"n": len(l), "por_30s_mirova_menos_nuestra": dict(sorted(c.items()))}
    # alertas de MIROVA sin record a +-120 s pero con record a 120-600 s
    nuestros = collections.defaultdict(list)
    for r in B["recs"]:
        nuestros[(r["vol"], r["b"])].append(r["dt"])
    # records crudos de cualquier hora (sin filtro diurno) para ver la convención
    sin = collections.Counter()
    casos = []
    vistos = set()
    for (vol, b), lista in pv.items():
        ts = sorted(nuestros.get((vol, b), []))
        for d, f in lista:
            if not bp.es_alerta(f["tipo"]) or (vol, b, f["fecha_utc"][:16]) in vistos:
                continue
            vistos.add((vol, b, f["fecha_utc"][:16]))
            i = bisect.bisect_left(ts, d - timedelta(seconds=600))
            cerca = [t for t in ts[i:] if t <= d + timedelta(seconds=600)]
            en120 = [t for t in cerca if abs((t - d).total_seconds()) <= 120]
            if en120:
                sin[(b, "par_120")] += 1
                continue
            if cerca:
                sin[(b, "sin_par_pero_record_120_600")] += 1
                t = min(cerca, key=lambda t: abs((t - d).total_seconds()))
                casos.append({"vol": vol, "b": b, "mirova": f["fecha_utc"], "nuestra": t.strftime("%Y-%m-%d %H:%M"),
                              "dt_s": round((d - t).total_seconds()), "vrp": f["vrp_mw"], "fuente": f["source"]})
            else:
                sin[(b, "sin_record_600")] += 1
    R["I6"] = {"ventana": list(B["win"]), "hist_dt": hist, "alertas_mirova": {"|".join(k): v for k, v in sorted(sin.items())},
               "casos_120_600": casos[:80], "n_casos_120_600": len(casos)}
    return casos


# ------------------------------------------------------------------ I9 protegidas diurnas, I10 poder
def i9_i10(B):
    coords = B["coords"]
    prot = {}
    todas_alertas = collections.defaultdict(list)
    for f in B["filas"]:
        if f["volcano"] not in aw.VOLS or f["sensor_bucket"] not in aw.SENSORS:
            continue
        if not ("2026-09-01" <= f["fecha_utc"][:10] <= "2026-11-07"):
            continue
        d = dt_of(f["fecha_utc"]).replace(tzinfo=timezone.utc)
        lat, lon = coords[f["volcano"]]
        diurna = aw.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, d)
        if bp.es_alerta(f["tipo"]):
            todas_alertas[f["volcano"]].append((d, diurna, f["vrp_mw"] or 0, f["sensor_bucket"]))
        if cm.alerta_protegida(f):
            k = cm.clave_pasada(f)
            if k not in prot or (f["vrp_mw"] or 0) > prot[k]["vrp"]:
                prot[k] = {"vol": f["volcano"], "b": f["sensor_bucket"], "dt": d, "vrp": f["vrp_mw"], "diurna": diurna,
                           "fuente": f["source"], "hora_utc": d.hour}
    c = collections.Counter()
    vecinas = collections.Counter()
    lista_d = []
    for k, p in prot.items():
        c[(p["vol"], p["b"], "diurna" if p["diurna"] else "nocturna")] += 1
        if p["diurna"]:
            nv = [x for x in todas_alertas[p["vol"]] if not x[1] and abs((x[0] - p["dt"]).total_seconds()) < 12 * 3600]
            nvp = [x for x in nv if x[2] >= 1.0]
            vecinas[(p["vol"], p["b"], "con_alerta_nocturna_12h")] += bool(nv)
            vecinas[(p["vol"], p["b"], "con_protegida_nocturna_12h")] += bool(nvp)
            lista_d.append({"vol": p["vol"], "b": p["b"], "dt": p["dt"].strftime("%Y-%m-%d %H:%M"), "vrp": p["vrp"],
                            "fuente": p["fuente"], "alerta_noct_12h": len(nv), "protegida_noct_12h": len(nvp)})
    hora = collections.Counter((p["b"], p["hora_utc"]) for p in prot.values() if p["diurna"])
    hora_n = collections.Counter((p["b"], p["hora_utc"]) for p in prot.values() if not p["diurna"])
    # control (8): Chillán, protegida a las 17 UTC y a las 07 UTC, con el filtro real
    lat, lon = coords["NevadosDeChillan"]
    ctrl = {b: {"17UTC_diurna": aw.es_pasada_diurna_descartada(b, lat, lon, datetime(2026, 10, 20, 17, 0, tzinfo=timezone.utc)),
                "07UTC_diurna": aw.es_pasada_diurna_descartada(b, lat, lon, datetime(2026, 10, 20, 7, 0, tzinfo=timezone.utc))}
            for b in aw.SENSORS}
    R["I9"] = {"ventana": ["2026-09-01", "2026-11-07"], "n_protegidas": len(prot),
               "por_vol_sensor_dia_noche": {"|".join(k): v for k, v in sorted(c.items())},
               "diurnas_con_vecina_nocturna": {"|".join(k): v for k, v in sorted(vecinas.items())},
               "diurnas_por_hora_utc": {f"{b}|{h:02d}": n for (b, h), n in sorted(hora.items())},
               "nocturnas_por_hora_utc": {f"{b}|{h:02d}": n for (b, h), n in sorted(hora_n.items())},
               "lista_diurnas": sorted(lista_d, key=lambda x: x["dt"]), "control_8": ctrl}
    pv_ = collections.Counter(p["vol"] for p in prot.values() if not p["diurna"])
    R["I10"] = {"protegidas_nocturnas_por_volcan": {v: pv_.get(v, 0) for v in aw.VOLS},
                "protegidas_todas_por_volcan": dict(collections.Counter(p["vol"] for p in prot.values()))}


# ------------------------------------------------------------------ I8 truncado
def i8(B):
    pat = re.compile(r"real\s*∈\s*\[(\d+),\s*(\d+)\)")
    filas = list(csv.DictReader(open(os.path.join(INS, "snapshot_ocr_base.csv"), encoding="utf-8")))
    trunc = []
    for f in filas:
        m = pat.search(f.get("Nota_Validacion") or "")
        if m:
            trunc.append({"fecha": f["Fecha_Satelite_UTC"], "volcan": f["Volcan"], "sensor": f["Sensor"],
                          "vrp": f["VRP_MW"], "tipo": f["Tipo_Registro"], "lo": int(m.group(1)), "hi": int(m.group(2))})
    por_sensor = collections.Counter(t["sensor"] for t in trunc)
    desde = min((t["fecha"] for t in trunc), default=None)
    # alertas de la referencia unificada a menos de una unidad de truncado del umbral (VRP en [0, 2) MW) que vienen del OCR
    cerca = collections.Counter()
    cambia = collections.Counter()
    ej = []
    for f in B["filas"]:
        if not bp.es_alerta(f["tipo"]) or f["vrp_mw"] is None or f["fecha_utc"][:10] < (desde or "9999")[:10]:
            continue
        if f["source"] != "OCR":
            continue
        v = f["vrp_mw"]
        if 0 <= v < 2:
            cerca[(f["sensor_bucket"], "0-1" if v < 1 else "1-2")] += 1
            # redondeo: hacia arriba (real hasta v+1) y hacia abajo (real desde v-1)
            if v < 1:
                cambia[(f["sensor_bucket"], "pasaria_a_protegida_si_real_v+1")] += 1
            else:
                cambia[(f["sensor_bucket"], "dejaria_de_ser_protegida_si_real_v-1")] += 1
            ej.append((f["volcano"], f["sensor_bucket"], f["fecha_utc"], v))
    ctrl = [t for t in trunc if t["fecha"].startswith("2026-11-06 13:15") and "Chillan" in t["volcan"]]
    # caso de partida: Chillán MODIS 2026-10-30 07:15
    caso = [{k: f[k] for k in ("volcano", "sensor_bucket", "fecha_utc", "source", "tipo", "vrp_mw", "dist_km")}
            for f in B["filas"] if f["volcano"] == "NevadosDeChillan" and f["sensor_bucket"] == "MODIS"
            and f["fecha_utc"].startswith("2026-10-30 07:1")]
    R["I8"] = {"n_filas_ocr_con_nota_truncado": len(trunc), "por_sensor": dict(por_sensor), "primera": desde,
               "tipos": dict(collections.Counter(t["tipo"] for t in trunc)),
               "alertas_ocr_vrp_0_a_2_desde_primera_nota": {"|".join(k): v for k, v in sorted(cerca.items())},
               "cambio_por_redondeo": {"|".join(k): v for k, v in sorted(cambia.items())},
               "ejemplos": ej[:40], "control_5_chillan_20261106_1315": ctrl, "caso_chillan_20261030_0715": caso}


# ------------------------------------------------------------------ I7 la referencia como instrumento
def leer_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def i7(B, pv, borrar=None):
    tabla = leer_csv(os.path.join(INS, "latest_consolidado_base.csv"))
    snap = leer_csv(os.path.join(INS, "snapshot_consolidado_base.csv"))
    ocr = leer_csv(os.path.join(INS, "snapshot_ocr_base.csv"))
    out = {}
    for nom, l in (("tabla_raiz", tabla), ("snapshot_consolidado", snap), ("snapshot_ocr", ocr)):
        fechas = sorted(f["Fecha_Satelite_UTC"] for f in l if f.get("Fecha_Satelite_UTC"))
        out[nom] = {"filas": len(l), "desde": fechas[0], "hasta": fechas[-1],
                    "tipos": dict(collections.Counter(f["Tipo_Registro"] for f in l))}
    k = lambda f: (f["Volcan"].strip(), f["Sensor"].strip(), f["Fecha_Satelite_UTC"][:16])  # noqa: E731
    ks = {k(f) for f in snap}
    falta = [f for f in tabla if k(f) not in ks]
    out["tabla_no_en_snapshot"] = {"n": len(falta), "por_dia": dict(sorted(collections.Counter(f["Fecha_Satelite_UTC"][:10] for f in falta).items())),
                                   "alertas": sum(1 for f in falta if f["Tipo_Registro"].startswith("ALERTA")),
                                   "alertas_hasta_20261102": sum(1 for f in falta if f["Tipo_Registro"].startswith("ALERTA") and f["Fecha_Satelite_UTC"][:10] <= "2026-11-02")}
    kt = {k(f) for f in tabla}
    out["snapshot_no_en_tabla"] = sum(1 for f in snap if k(f) not in kt)
    # cobertura OCR de las alertas de la tabla desde el 2026-06-11, +-120 s, por bucket
    from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
    def idx(l):
        d = collections.defaultdict(list)
        for f in l:
            v = normalize_volcano_name(f.get("Volcan"))
            if v is None or len(f.get("Fecha_Satelite_UTC", "")) < 16:
                continue
            d[(v, normalize_sensor(f.get("Sensor")))].append((dt_of(f["Fecha_Satelite_UTC"]), f))
        for x in d.values():
            x.sort(key=lambda y: y[0])
        return d
    io_ = idx(ocr)
    it = idx(tabla)
    cob = collections.Counter()
    acuerdo = collections.Counter()
    for (v, b), l in it.items():
        for d, f in l:
            if f["Fecha_Satelite_UTC"][:10] < "2026-06-11":
                continue
            ts = io_.get((v, b), [])
            par = [g for t, g in ts if abs((t - d).total_seconds()) <= 120]
            if f["Tipo_Registro"].startswith("ALERTA"):
                cob[(b, "alertas_tabla")] += 1
                cob[(b, "con_fila_ocr")] += bool(par)
                cob[(b, "con_alerta_ocr")] += any(g["Tipo_Registro"].startswith("ALERTA") for g in par)
            if par:
                ta = f["Tipo_Registro"].startswith("ALERTA")
                oa = any(g["Tipo_Registro"].startswith("ALERTA_TERMICA") for g in par)
                acuerdo[(b, f"tabla_{'A' if ta else f['Tipo_Registro'][:4]}_ocr_{'A' if oa else par[0]['Tipo_Registro'][:6]}")] += 1
    solo = collections.Counter()
    solo_ej = []
    for (v, b), l in io_.items():
        for d, g in l:
            if g["Fecha_Satelite_UTC"][:10] < "2026-06-11" or not g["Tipo_Registro"].startswith("ALERTA_TERMICA"):
                continue
            ts = it.get((v, b), [])
            par = [f for t, f in ts if abs((t - d).total_seconds()) <= 120]
            if not par:
                solo[b] += 1
                # ¿hay fila de la tabla de ese volcán y sensor en +-60 min? (otra pasada)
                cerca = [(round((t - d).total_seconds() / 60, 1), f["Tipo_Registro"]) for t, f in ts if abs((t - d).total_seconds()) <= 3600]
                solo_ej.append({"vol": v, "b": b, "fecha": g["Fecha_Satelite_UTC"], "vrp": g["VRP_MW"], "tabla_60min": cerca[:4]})
    sc = collections.Counter()
    for e in solo_ej:
        sc[(e["b"], "con_fila_tabla_en_60min" if e["tabla_60min"] else "sin_fila_tabla_en_60min")] += 1
    out["cobertura_ocr_de_alertas_tabla_desde_20260611"] = {"|".join(k_): v_ for k_, v_ in sorted(cob.items())}
    out["acuerdo_tabla_ocr_misma_pasada"] = {"|".join(k_): v_ for k_, v_ in sorted(acuerdo.items())}
    out["solo_ocr_alertas_desde_20260611"] = dict(solo)
    out["solo_ocr_contexto"] = {"|".join(k_): v_ for k_, v_ in sorted(sc.items())}
    out["solo_ocr_ejemplos"] = solo_ej[:30]
    # pasadas nuestras sin ninguna fila de MIROVA a +-120 s (por satélite, volcán, mes)
    huecos = collections.Counter()
    tot = collections.Counter()
    for r in B["recs"]:
        if borrar and r["sensor"] == borrar[0] and borrar[1] <= r["noche"] <= borrar[2]:
            pass
        filas = bp.parear(pv.get((r["vol"], r["b"]), []), r["dt"])
        if borrar:
            filas = [f for f in filas if not (f["sensor_bucket"] == borrar[3] and borrar[1] <= f["fecha_utc"][:10] <= borrar[2])]
        tot[(r["sensor"], r["noche"][:7])] += 1
        if not filas:
            huecos[(r["sensor"], r["noche"][:7])] += 1
    out["pasadas_nuestras_sin_fila_mirova"] = {f"{s}|{m}": f"{huecos[(s, m)]}/{tot[(s, m)]}" for (s, m) in sorted(tot)}
    hv = collections.Counter()
    tv = collections.Counter()
    for r in B["recs"]:
        filas = bp.parear(pv.get((r["vol"], r["b"]), []), r["dt"])
        tv[r["vol"]] += 1
        hv[r["vol"]] += not filas
    out["sin_fila_por_volcan"] = {v: f"{hv[v]}/{tv[v]}" for v in sorted(tv)}
    return out


def i7_control_hueco(B):
    """Línea base roja (6): copia de la referencia sin las filas VIIRS375 de la semana 2026-10-12 a 2026-10-18."""
    filas = [f for f in B["filas"] if not (f["sensor_bucket"] == "VIIRS375" and "2026-10-12" <= f["fecha_utc"][:10] <= "2026-10-18")]
    pv, ns, nv, n = bp.indexar_referencia(filas, B["coords"], B["win"], regla_minimas=aw.REGLA_MINIMAS)
    h = collections.Counter()
    t = collections.Counter()
    for r in B["recs"]:
        if r["b"] != "VIIRS375":
            continue
        sem = "2026-10-12..18" if "2026-10-12" <= r["noche"] <= "2026-10-18" else "resto"
        t[sem] += 1
        h[sem] += not bp.parear(pv.get((r["vol"], r["b"]), []), r["dt"])
    return {k: f"{h[k]}/{t[k]}" for k in t}


def main():
    B = cargar()
    pv, ns, nv, n = bp.indexar_referencia(B["filas"], B["coords"], B["win"], regla_minimas=aw.REGLA_MINIMAS)
    control_i2()
    i2(B, pv)
    print("I2", json.dumps(R["I2"]["clase_con_origen_comun_mirova_center"]), json.dumps(R["I2"]["clase_radio_crudo_final_hotspot_dist_km"]), R["I2"]["n"], "MC", len(MC))
    i9_i10(B)
    print("I9 listo")
    R["I7"] = i7(B, pv)
    pvb, *_ = bp.indexar_referencia(B["filas"], B["coords"], B["win"], regla_minimas=aw.REGLA_MINIMAS)
    R["control_I7_hueco"] = i7_control_hueco(B)
    print("I7 listo", R["control_I7_hueco"])
    i8(B)
    print("I8 listo")
    A = audit_ventana(B)
    i1_i3_i4(B, A)
    control_i3()
    print("I1 I3 I4 listos", R["control_port"], R["control_I3"])
    i6(B, pv)
    print("I6 listo")
    with open(os.path.join(OUT, "f5_medir_out.json"), "w", encoding="utf-8") as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1, default=str)
    print("escrito", os.path.join(OUT, "f5_medir_out.json"))


if __name__ == "__main__":
    main()
