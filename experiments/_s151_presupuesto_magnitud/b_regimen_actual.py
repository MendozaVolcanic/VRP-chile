# -*- coding: utf-8 -*-
"""Tarea 1.14, parte B: el presupuesto de magnitud en el regimen de 2026, contra la referencia NRT de MIROVA.

POR QUE: el deficit que motiva la tarea (Lascar 0,44, Isluga 0,52, Lastarria 0,56, Tupungatito 0,65 en el
auto-audit del 2026-10-14) es de 2026, y el regimen cambio en #535 (A104). La referencia NRT no trae Npix ni
fondo de MIROVA, asi que aca la razon se separa solo en dos factores exactos:
    R = D / V_M = (D / S_in) * (S_in / V_M) = F_rec * G
F_rec es el recorte del tablero (cumulo, nucleo F5', etiqueta) contra la suma de NUESTROS alertados dentro del
inner; G es todo lo demas (conteo, nivel caliente, fondo, remuestreo), y de G se separa la parte que depende del
angulo cenital, que es la firma del remuestreo de MIROVA (D17). Fondo contra conteo dentro de G lo dan la
parte A (OSF 2025, exacta) y la parte C (brazos de A/B ya corridos).

Uso:  python b_regimen_actual.py [--snapshot] [--dest DIR]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(AQUI))

import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, bajar_remoto, cargar_referencia_unificada  # noqa: E402
from pipeline.f5_core import f5_core_vrp_mw  # noqa: E402
import comun as C  # noqa: E402

TRAMOS = {"pre_535": ("2026-04-01", "2026-08-28"), "post_535": ("2026-08-29", "2026-10-14")}
VENTANA_AUDIT = ("2026-08-15", "2026-10-14")
AUDIT_LATEST = ROOT / "data" / "audit_continuous" / "latest.json"
MINIMA_V375 = 0.05


def cargar(coords, ventana):
    """Records nocturnos de los 11 Tier A en la ventana, con el predicado del tablero ejecutado con node."""
    recs, casos = [], []
    inner_html = BP.inner_desde_html()
    for vol in C.VOLS:
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
            b = C.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if BP.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            recs.append({"vol": vol, "b": b, "dt": dt, "noche_id": f"{vol}|{dt:%Y-%m-%d}", "rec": r})
            slim = {k: r.get(k) for k in BP.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner_html[vol]])
    pred = BP.correr_node(casos) if casos else []
    for x, p in zip(recs, pred):
        x["disp"], x["pub"] = p[3], p[4]
    return recs


def fila_alerta(filas):
    """La fila ALERTA de la pasada: consolidado antes que OCR (misma regla que el evaluador de S143)."""
    al = [f for f in filas if BP.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0]
    if not al:
        return None
    al.sort(key=lambda f: (f["source"] != "CONS", -(f["vrp_mw"] or 0)))
    return al[0]


def emparejar(recs, por_vb, shift_h=0):
    out = []
    for x in recs:
        filas = BP.parear(por_vb.get((x["vol"], x["b"]), []), x["dt"] + timedelta(hours=shift_h))
        a = fila_alerta(filas)
        if a is not None:
            out.append((x, a))
    return out


def separar(x, a):
    """Factores de una pasada positiva; devuelve (fila, motivo de exclusion o None)."""
    r, b, vol = x["rec"], x["b"], x["vol"]
    v_m = a["vrp_mw"]
    f = {"vol": vol, "b": b, "noche_id": x["noche_id"], "t": x["dt"].isoformat(), "V_M": v_m, "fuente_ref": a["source"],
         "dist_ref": a["dist_km"], "D": x["disp"], "pub": x["pub"], "z": r.get("sensor_zenith_deg"),
         "banda_z": C.banda_z(r.get("sensor_zenith_deg")), "fuente": r.get("final_hotspot_source"),
         "n_px_guardados": len(r.get("anomaly_pixels") or [])}
    if b == "VIIRS375" and v_m <= MINIMA_V375:
        return f, "mirova_minima_le_0p05"
    if not x["pub"] or not (x["disp"] and x["disp"] > 0):
        return f, "no_publicada"
    s_in, n_pos, lh, n_cero = C.pixeles_inner(r, vol)
    f.update({"S_in": s_in, "n_pos": n_pos, "n_cero": n_cero, "S_all": sum((p.get("vrp_mw") or 0) for p in r.get("anomaly_pixels") or [])})
    if s_in <= 0:
        return f, "S_in_cero"
    f["R"] = x["disp"] / v_m
    f["ln_rec"] = math.log(x["disp"] / s_in)
    f["ln_G"] = math.log(s_in / v_m)
    f["ln_all"] = math.log(f["S_all"] / v_m) if f["S_all"] > 0 else float("nan")
    return f, None


def controles(recs, positivos, por_vb):
    c1, c1_por_fuente = [], collections.Counter()
    c2, c3, c2_por = [], [], collections.Counter()
    for x in recs:
        r, b, vol = x["rec"], x["b"], x["vol"]
        ok = C.control_un_pixel(r)
        if ok is not None:
            c2.append(ok)
            c2_por[(b, "test1" if r.get("triggered_test1") else "sin_test1", ok)] += 1
        if b == "VIIRS375" and r.get("f5_core_vrp_mw") is not None:
            v = f5_core_vrp_mw(r, C.INNER[vol])
            c3.append(v is not None and abs(v - r["f5_core_vrp_mw"]) <= 0.001)
        lbg = r.get("diag_L_bg_w_m2_sr_um")
        if lbg is None or vol in C.KERNEL or r.get("final_hotspot_source") == "test1_roi":
            continue
        for p in r.get("anomaly_pixels") or []:
            if (p.get("vrp_mw") or 0) > 0 and p.get("bt_k"):
                rec = C.KA[b] * (C.planck(p["bt_k"], b) - lbg) / 1e6
                bien = abs(rec - p["vrp_mw"]) <= max(0.0002, 0.01 * p["vrp_mw"])
                c1.append(bien)
                c1_por_fuente[(b, "test1" if r.get("triggered_test1") else "sin_test1", bien)] += 1
    neg = emparejar(recs, por_vb, shift_h=6)
    frac = len(neg) / max(1, len(positivos))
    return {"C1_pixel_desde_bt_y_fondo": {"n_pixeles": len(c1), "acierto": round(float(np.mean(c1)), 4) if c1 else None,
                                          "pasa": bool(c1) and float(np.mean(c1)) >= 0.95,
                                          "por_sensor_y_test1": _tasas(c1_por_fuente)},
            "C2_cumulo_un_pixel": {"n": len(c2), "acierto": round(float(np.mean(c2)), 4) if c2 else None,
                                   "pasa": bool(c2) and float(np.mean(c2)) >= 0.98,
                                   "por_sensor_y_test1": _tasas(c2_por)},
            "C3_f5_replica": {"n": len(c3), "acierto": round(float(np.mean(c3)), 4) if c3 else None,
                              "pasa": bool(c3) and float(np.mean(c3)) >= 0.99},
            "C5_pareo_corrido_6h": {"positivos_corridos": len(neg), "positivos_reales": len(positivos),
                                    "fraccion": round(frac, 4), "pasa": frac <= 0.02}}


def _tasas(cnt):
    """{(sensor, grupo, acierto): n} -> {"sensor|grupo": [aciertos, total, fraccion]}."""
    out = collections.defaultdict(lambda: [0, 0])
    for (b, g, ok), n in cnt.items():
        out[f"{b}|{g}"][1] += n
        if ok:
            out[f"{b}|{g}"][0] += n
    return {k: [v[0], v[1], round(v[0] / v[1], 4)] for k, v in sorted(out.items())}


def control_auto_audit(filas_ref, coords):
    """C6: la mediana por volcan del auto-audit (noche, max pc.vrp del tablero / max alerta) se reproduce."""
    mir = collections.defaultdict(float)
    for f in filas_ref:
        if not (VENTANA_AUDIT[0] <= f["fecha_utc"][:10] <= VENTANA_AUDIT[1]) or not BP.es_alerta(f["tipo"]):
            continue
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[f["volcano"]]
        if f["sensor_bucket"] not in ("MODIS", "VIIRS375", "VIIRS750") or BP.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
            continue
        k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:10])
        mir[k] = max(mir[k], f["vrp_mw"] or 0.0)
    ours = collections.defaultdict(list)
    for vol in C.VOLS:
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
            dt = r.get("datetime_utc") or ""
            if not (VENTANA_AUDIT[0] <= dt[:10] <= VENTANA_AUDIT[1]):
                continue
            b = C.bucket(r.get("sensor", ""))
            pc = r.get("primary_cluster") or {}
            vrp, cd = pc.get("vrp_mw") or 0.0, pc.get("centroid_dist_km")
            if b and 0 < vrp <= 50000 and cd is not None and cd <= C.INNER[vol] and (r.get("distance_class") in (None, "", "summit")):
                ours[(vol, b, dt[:10])].append(vrp)
    rat = collections.defaultdict(list)
    for (vol, b, d), m in mir.items():
        if m > 0 and ours.get((vol, b, d)):
            rat[vol].append(max(ours[(vol, b, d)]) / m)
    ref = json.load(open(AUDIT_LATEST, encoding="utf-8"))["magnitud_ratio_by_vol"]
    out, malos = {}, []
    for vol, v in ref.items():
        mio = round(statistics.median(rat[vol]), 3) if rat.get(vol) else None
        out[vol] = {"auto_audit": v["ratio_mediano"], "n_auto_audit": v["n_noches"], "reproducido": mio, "n": len(rat.get(vol, []))}
        if v["n_noches"] >= 15 and (mio is None or abs(mio - v["ratio_mediano"]) > 0.05):
            malos.append(vol)
    return {"por_volcan": out, "fuera_de_tolerancia": malos, "pasa": not malos}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--dest", default=str(AQUI / "_dl_referencia"))
    a = ap.parse_args(argv)
    if a.snapshot:
        cons, ocr, proc = SNAP_CONS, SNAP_OCR, {"fuente": "snapshot"}
    else:
        info = bajar_remoto(Path(a.dest))
        cons, ocr = Path(info["registro_vrp_consolidado.csv"]["path"]), Path(info["registro_vrp_ocr.csv"]["path"])
        proc = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    coords = BP._coords_por_volcan()
    filas_ref = cargar_referencia_unificada(cons, ocr)
    out = {"referencia": proc, "tramos": {}, "control_C6_auto_audit": control_auto_audit(filas_ref, coords)}
    txt = [json.dumps(proc), "C6 " + json.dumps(out["control_C6_auto_audit"], ensure_ascii=False)]
    todas = []
    for nombre, ventana in TRAMOS.items():
        por_vb, _, _, _ = BP.indexar_referencia(filas_ref, coords, ventana)
        recs = cargar(coords, ventana)
        pos = emparejar(recs, por_vb)
        filas, excl = [], collections.Counter()
        for x, al in pos:
            f, m = separar(x, al)
            f["tramo"] = nombre
            if m:
                excl[(f["b"], m)] += 1
            else:
                filas.append(f)
        tr = {"ventana": ventana, "records_nocturnos": len(recs), "positivos": len(pos),
              "excluidas": {f"{b}|{m}": n for (b, m), n in sorted(excl.items())},
              "controles": controles(recs, pos, por_vb), "reparto": {}}
        for b in ("VIIRS375", "VIIRS750", "MODIS"):
            for vol in [None] + C.VOLS:
                sub = [f for f in filas if f["b"] == b and (vol is None or f["vol"] == vol)]
                if len(sub) < (10 if vol else 5):
                    continue
                rep = C.reparto_con_ic(sub, ["ln_rec", "ln_G"])
                rep["angulo_en_G"] = C.frac_angulo_con_ic(sub, "ln_G")
                rep["G_gm_por_banda_z"] = {bz: [round(C.gm([math.exp(f["ln_G"]) for f in sub if f["banda_z"] == bz]), 3),
                                                sum(1 for f in sub if f["banda_z"] == bz)]
                                           for bz in ("0-20", "20-35", "35-50", "50-90")}
                rep["n_pos_mediana"] = float(np.median([f["n_pos"] for f in sub]))
                rep["frac_n_px_guardados_100"] = round(float(np.mean([f["n_px_guardados"] >= 100 for f in sub])), 4)
                rep["S_all_sobre_V_M_gm"] = round(C.gm([math.exp(f["ln_all"]) for f in sub]), 4)
                tr["reparto"][f"{b}|{vol or 'todos'}"] = rep
        out["tramos"][nombre] = tr
        todas += filas
        txt.append(f"== {nombre} {ventana}: records {len(recs)}, positivos {len(pos)}, excluidas {tr['excluidas']}")
        txt.append("controles " + json.dumps(tr["controles"], ensure_ascii=False))
        txt.append("estrato | n pas/noches | R med | R gm [IC] | F_rec [IC] | G [IC] | frac rec | frac G | angulo en G (frac, factor) | n+ med | G por banda z | S_all/V_M")
        for k, r in tr["reparto"].items():
            txt.append(f"{k} | {r['n_pasadas']}/{r['n_noches']} | {r['R_mediana']:.3f} | {r['R_gm']} | {r['ln_rec']} | {r['ln_G']} | "
                       f"{r['frac_ln_rec']} | {r['frac_ln_G']} | {r['angulo_en_G']} | {r['n_pos_mediana']} | {r['G_gm_por_banda_z']} | {r['S_all_sobre_V_M_gm']}")
    import csv
    with open(AQUI / "b_regimen_actual_pares.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=sorted({k for f in todas for k in f}))
        w.writeheader()
        w.writerows(todas)
    (AQUI / "b_regimen_actual_salida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=_js), encoding="utf-8")
    (AQUI / "b_regimen_actual_salida.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


def _js(o):
    return o.item() if hasattr(o, "item") else str(o)


if __name__ == "__main__":
    main()
