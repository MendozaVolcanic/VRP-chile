# -*- coding: utf-8 -*-
"""Verificador S149: magnitud cero en produccion. Solo lectura. 'Publica' = predicado node de banco_paridad."""
import sys, io, json, collections, csv
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR

INI = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
FIN = sys.argv[2] if len(sys.argv) > 2 else "2026-09-21"
DATA = Path(sys.argv[3]) if len(sys.argv) > 3 else bp.DATA
ventana = (INI, FIN)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)

recs, casos = [], []
for vol in bp.VOLS:
    p = DATA / f"{vol}.json"
    if not p.exists(): continue
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (INI <= r.get("datetime_utc", "")[:10] <= FIN): continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if bp.es_pasada_diurna_descartada(b, *coords[vol], dt): continue
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": r["datetime_utc"][:10], "r": r})
        slim = {k: r.get(k) for k in bp.CAMPOS_JS}
        casos.append([slim, inner[vol]])
pred = bp.correr_node(casos)
for rec, p in zip(recs, pred):
    rec["summit_js"], rec["valid_js"], rec["art"], rec["disp"], rec["pub"] = p
bp.etiquetar(recs, por_vb, ns, nv)

def clase(rec):
    r = rec["r"]; pc = r.get("primary_cluster"); dc = r.get("distance_class")
    if rec["pub"]: return "PUBLICA"
    if not pc:
        return "sin_cumulo(vrp_mw=%s)" % ("0" if not (r.get("vrp_mw") or 0) else ">0")
    v = pc.get("vrp_mw") or 0; d = pc.get("centroid_dist_km")
    dentro = d is not None and d <= inner[rec["vol"]]
    if dc == "summit" and dentro and v == 0: return "summit_cumulo_0MW"
    if dc == "summit" and not dentro: return "summit_pc_fuera_inner(v%s0)" % (">" if v > 0 else "=")
    if dc != "summit" and v > 0: return "%s_cumulo_con_energia%s" % (dc, "_dentro" if dentro else "_fuera")
    if dc != "summit" and v == 0: return "%s_cumulo_0MW%s" % (dc, "_dentro" if dentro else "_fuera")
    if rec["art"]: return "artefacto_display"
    return "otro"

out = {}
for b in bp.BUCKETS:
    for lab in ("pos", "neg_limpio"):
        sel = [x for x in recs if x["b"] == b and x["lab"] == lab]
        c = collections.Counter(clase(x) for x in sel)
        print(f"\n=== {b} {lab} ventana {INI}..{FIN} n={len(sel)} publica={c['PUBLICA']}")
        for k, v in c.most_common(): print(f"   {k:45s} {v:5d}  {100*v/max(1,len(sel)):.1f}%")
        out[f"{b}|{lab}"] = dict(c)
        if lab == "pos":
            cv = collections.Counter((x["vol"], clase(x)) for x in sel)
            for k, v in sorted(cv.items()): print("      ", k, v)
sr = bp.alertas_sin_record(por_vb, recs)
print("\nalertas sin record:", dict(sr))
out["sin_record"] = {f"{a}|{b}": n for (a, b), n in sr.items()}

# detalle del summit_cumulo_0MW en pos V750
det = []
for x in recs:
    if x["lab"] == "pos" and clase(x) != "PUBLICA":
        r = x["r"]; pc = r.get("primary_cluster") or {}
        aps = r.get("anomaly_pixels") or []
        filas_ref = bp.parear(por_vb.get((x["vol"], x["b"]), []), x["dt"])
        det.append({"vol": x["vol"], "b": x["b"], "dt": r["datetime_utc"], "clase": clase(x),
                    "ref": [(f["tipo"], f["source"], f["vrp_mw"], f["dist_km"], f["fecha_utc"]) for f in filas_ref],
                    "dc": r.get("distance_class"), "reason": r.get("discarded_reason"), "vrp_mw": r.get("vrp_mw"), "vrp_mir_mw": r.get("vrp_mir_mw"),
                    "f5": r.get("f5_core_vrp_mw"), "pc": pc, "t_max_k": r.get("t_max_k"), "t_bg_k": r.get("t_bg_k"),
                    "t_max_dist": r.get("diag_t_max_dist_km"), "n_anom": r.get("n_anomalous_pixels"),
                    "aps": aps[:6], "n_aps": len(aps), "max_bt_ap": max([p.get("bt_k") or 0 for p in aps], default=None),
                    "sum_ap_vrp": sum((p.get("vrp_mw") or 0) for p in aps),
                    "trig_t1": r.get("triggered_test1"), "t1k": r.get("test1_k_observed"), "fp": r.get("diag_n_first_pass_pixels"),
                    "recap": r.get("diag_n_second_pass_recapture"), "src": r.get("final_hotspot_source"), "zen": r.get("sensor_zenith_deg")})
tag = INI.replace("-", "")
Path(__file__).with_name(f"v1_out_{tag}.json").write_text(json.dumps({"resumen": out, "detalle_pos_no_pub": det}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
print("detalle:", len(det))
