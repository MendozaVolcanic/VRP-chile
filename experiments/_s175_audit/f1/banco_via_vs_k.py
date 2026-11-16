#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F1 (auditoría S175): la vía MODIS contra el predicado del tablero (node) y la sobre-publicación vía contra K.

Corre con el código de la base (752d348bc, copia en root_base) sobre los records de e75a7d52d y la referencia
de la base (los CSV del snapshot). Todo lo que publica sale de scripts/banco_paridad.py::correr_node (regla A97);
las etiquetas, de banco_paridad.etiquetar con la regla original (D-9 no toca MODIS).

Pregunta 1: si la vía guardara una cosa y el tablero publicara otra, ¿esto lo ve? Sí: compara, record por
record de la vía, `pub` de node con lo que la vía dice que produce (cúmulo más radiante en la cumbre con VRP > 0)
y lista cada discrepancia. Si la vía publicara en negativos limpios más que K, ¿lo ve? Sí: tasa por detector con
numerador, denominador y ventana.
Pregunta 2: control positivo: un record de la vía mutado a `distance_class: "far"` tiene que caer de pub 1 a 0, y
uno mutado a `primary_cluster.vrp_mw: 0` también. Si node estuviera muerto, correr_node lanza.

Uso: python banco_via_vs_k.py <root_base> <desde AAAA-MM-DD> <hasta AAAA-MM-DD>
"""
import copy
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = sys.argv[1]
DESDE, HASTA = sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

# --cons / --ocr: otra referencia (p. ej. latest_consolidado.csv de la raíz, que el banco NO lee; se rotula).
if "--cons" in sys.argv:
    aa.CONS = sys.argv[sys.argv.index("--cons") + 1]
if "--ocr" in sys.argv:
    aa.OCR = sys.argv[sys.argv.index("--ocr") + 1]

ENCENDIDO = "2026-11-02T20:11:43Z"


def claves_via(data_dir):
    via, raw = set(), {}
    for vol in bp.VOLS:
        with open(os.path.join(data_dir, vol + ".json"), encoding="utf-8") as fh:
            recs = json.load(fh)["records"]
        raw[vol] = {(r.get("datetime_utc"), r.get("sensor")): r for r in recs}
        for r in recs:
            if r.get("via_codigo_mirova") is True and str(r.get("sensor") or "").startswith("MODIS"):
                via.add((vol, r.get("sensor"), str(r.get("datetime_utc"))[:16]))
    return via, raw


def main():
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    win = (DESDE, HASTA)
    filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
    via, raw = claves_via(str(bp.DATA))
    recs = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == "MODIS"]
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, win)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r in recs:
        r["via"] = (r["vol"], r.get("sensor"), r["dt"].strftime("%Y-%m-%d %H:%M")) in via
        r["det"] = "VIA" if r["via"] else "K"
    out = {"root": ROOT, "ventana": list(win), "n_records_modis": len(recs), "n_filas_referencia_en_ventana": n_ref,
           "identidad_predicado": bp.control_identidad_predicado()}

    # 1) La vía contra el predicado: lo que la vía dice (cúmulo más radiante en la cumbre y VRP > 0) contra `pub`.
    disc, resumen = [], Counter()
    far_con_pixeles_cumbre = []
    for r in recs:
        if not r["via"]:
            continue
        rec = raw[r["vol"]][(r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"])]
        pc = rec.get("primary_cluster") or {}
        dice = bool(pc and (pc.get("vrp_mw") or 0) > 0 and rec.get("distance_class") == "summit"
                    and (pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= inner[r["vol"]]))
        resumen[f"dice={int(dice)} pub={int(bool(r['pub']))}"] += 1
        if dice != bool(r["pub"]):
            disc.append({"vol": r["vol"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "sensor": r["sensor"],
                         "dice": dice, "pub": r["pub"], "disp": r["disp"], "vrp_mw": rec.get("vrp_mw"),
                         "distance_class": rec.get("distance_class"), "pc": pc, "t_max_k": rec.get("t_max_k")})
        if rec.get("distance_class") == "far" and (rec.get("vrp_mw") or 0) > 0:
            pix_cumbre = [p for p in rec.get("anomaly_pixels") or [] if (p.get("dist_km") or 99) <= inner[r["vol"]]]
            far_con_pixeles_cumbre.append({"vol": r["vol"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"),
                                           "vrp_mw": rec.get("vrp_mw"), "n_pix": len(rec.get("anomaly_pixels") or []),
                                           "n_pix_dentro_inner": len(pix_cumbre),
                                           "pc_dist": pc.get("centroid_dist_km")})
    out["via_vs_predicado"] = {"resumen": dict(resumen), "discrepancias": disc,
                               "far_con_vrp": far_con_pixeles_cumbre}

    # 2) Control positivo del predicado sobre records reales de la vía publicados.
    pubs = [r for r in recs if r["via"] and r["pub"]]
    control = {"n_via_publicados": len(pubs)}
    if pubs:
        r0 = pubs[0]
        rec0 = raw[r0["vol"]][(r0["dt"].strftime("%Y-%m-%d %H:%M"), r0["sensor"])]
        slim = {k: rec0.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        m_far = copy.deepcopy(slim); m_far["distance_class"] = "far"
        m_cero = copy.deepcopy(slim); m_cero["primary_cluster"] = dict(m_cero["primary_cluster"], vrp_mw=0.0)
        m_frio = copy.deepcopy(slim); m_frio["t_max_k"] = 250.0; m_frio["primary_cluster"] = dict(m_frio["primary_cluster"], vrp_mw=20.0); m_frio["vrp_mw"] = 20.0
        m_frio_k = copy.deepcopy(m_frio); m_frio_k.pop("via_codigo_mirova", None)
        res = bp.correr_node([[slim, inner[r0["vol"]]], [m_far, inner[r0["vol"]]], [m_cero, inner[r0["vol"]]],
                              [m_frio, inner[r0["vol"]]], [m_frio_k, inner[r0["vol"]]]])
        control.update({"record": f"{r0['vol']} {r0['dt']:%Y-%m-%d %H:%M} {r0['sensor']}",
                        "original_pub": res[0][4], "mutado_far_pub": res[1][4], "mutado_vrp0_pub": res[2][4],
                        "mutado_frio_20mw_via_pub": res[3][4], "mutado_frio_20mw_sin_marca_via_pub": res[4][4],
                        "mutado_frio_20mw_sin_marca_via_art": res[4][2]})
    out["control_positivo"] = control

    # 3) Sobre-publicación: negativos limpios publicados, por detector, con denominador.
    def tasa(rs):
        n = len(rs); k = sum(1 for r in rs if r["pub"])
        return {"publicados": k, "neg_limpios": n, "tasa": round(k / n, 4) if n else None,
                "noches": len({r["noche"] for r in rs}), "volcanes": sorted({r["vol"] for r in rs})}
    negs = [r for r in recs if r["lab"] == "neg_limpio"]
    out["sobrepublicacion"] = {
        "VIA_desde_encendido": tasa([r for r in negs if r["via"]]),
        "K_antes_del_encendido_misma_ventana": tasa([r for r in negs if not r["via"]]),
        "K_ultimos_30_dias_antes_del_encendido": tasa([r for r in negs if not r["via"] and r["noche"] >= "2026-10-03"]),
        "por_volcan": {v: {"VIA": tasa([r for r in negs if r["via"] and r["vol"] == v]),
                           "K": tasa([r for r in negs if not r["via"] and r["vol"] == v])} for v in bp.VOLS},
        "publicados_via_en_neg_limpio": [{"vol": r["vol"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "disp": r["disp"]}
                                         for r in negs if r["via"] and r["pub"]],
        "etiquetas_via": dict(Counter(r["lab"] for r in recs if r["via"])),
        "etiquetas_k": dict(Counter(r["lab"] for r in recs if not r["via"])),
    }

    # 4) Pareo: alertas MODIS de MIROVA en la ventana sin record a ±120 s, y desfase MIROVA-record más cercano.
    sin_record = bp.alertas_sin_record(por_vb, recs)
    desf = []
    por_vol_dt = defaultdict(list)
    for r in recs:
        por_vol_dt[r["vol"]].append(r["dt"])
    for (vol, b), lista in por_vb.items():
        if b != "MODIS":
            continue
        for dt, f in lista:
            if not bp.es_alerta(f["tipo"]):
                continue
            cand = por_vol_dt.get(vol, [])
            d = min((abs((c - dt).total_seconds()) for c in cand), default=None)
            desf.append({"vol": vol, "fecha_utc": f["fecha_utc"][:16], "vrp": f["vrp_mw"], "src": f["source"],
                         "desfase_s_record_mas_cercano": d, "pareada_120s": (d is not None and d <= bp.TOL_S)})
    out["pareo"] = {"alertas_modis_sin_record_120s_por_volcan": {f"{k[0]}": v for k, v in sin_record.items() if k[1] == "MODIS"},
                    "alertas_modis": desf}
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
