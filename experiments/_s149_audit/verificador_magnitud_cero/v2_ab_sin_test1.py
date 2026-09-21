# -*- coding: utf-8 -*-
"""Verificador S149, afirmacion 2: A/B sin Test 1 (run 35521542153). Solo lectura; datos fuera del repo."""
import sys, io, json, collections
from pathlib import Path
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
BASE = Path(sys.argv[1])
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
def cargar(brazo):
    recs, casos = {}, []
    for vol in bp.VOLS:
        for r in json.load(open(BASE / brazo / f"{vol}.json", encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            if b is None: continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if bp.es_pasada_diurna_descartada(b, *coords[vol], dt): continue
            k = (vol, r["sensor"], r["datetime_utc"])
            recs[k] = {"vol": vol, "b": b, "dt": dt, "noche": r["datetime_utc"][:10], "r": r}
            casos.append((k, [{c: r.get(c) for c in bp.CAMPOS_JS}, inner[vol]]))
    pred = bp.correr_node([c for _, c in casos])
    for (k, _), p in zip(casos, pred):
        recs[k]["pub"], recs[k]["disp"] = p[4], p[3]
    return recs
C = cargar("_s146_ab_control"); S = cargar("_s146_ab_sin_test1")
fechas = sorted(x["noche"] for x in C.values()); ventana = (fechas[0], fechas[-1])
print("ventana de los DATOS:", ventana, "| control", len(C), "sin_test1", len(S), "| claves comunes", len(set(C) & set(S)))
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana)
bp.etiquetar(list(C.values()), por_vb, ns, nv)
for b in bp.BUCKETS:
    for lab in ("pos", "neg_limpio"):
        ks = [k for k, x in C.items() if x["b"] == b and x["lab"] == lab and k in S]
        pc_, ps_ = sum(C[k]["pub"] for k in ks), sum(S[k]["pub"] for k in ks)
        per = [k for k in ks if C[k]["pub"] and not S[k]["pub"]]; gan = [k for k in ks if not C[k]["pub"] and S[k]["pub"]]
        # condicion summit 0 MW en el brazo
        def s0(x):
            r = x["r"]; pc = r.get("primary_cluster")
            return bool(pc) and (pc.get("vrp_mw") or 0) == 0 and r.get("distance_class") == "summit" and (pc.get("centroid_dist_km") or 0) <= inner[x["vol"]]
        print(f"{b:9s} {lab:10s} n={len(ks):4d} pub control={pc_} sin_test1={ps_} pierde={len(per)} gana={len(gan)} | summit0MW control={sum(s0(C[k]) for k in ks)} brazo={sum(s0(S[k]) for k in ks)}")
        if lab == "pos":
            for k in per:
                rc, rs = C[k]["r"], S[k]["r"]
                ref = [(f["tipo"][:6], f["source"], f["vrp_mw"], f["dist_km"]) for f in bp.parear(por_vb.get((k[0], b), []), C[k]["dt"])]
                def d(r):
                    pc = r.get("primary_cluster") or {}
                    aps = r.get("anomaly_pixels") or []
                    return dict(dc=r.get("distance_class"), src=r.get("final_hotspot_source"), T1=r.get("triggered_test1"), vrp=r.get("vrp_mw"),
                                pc_n=pc.get("n_pixels"), pc_v=pc.get("vrp_mw"), pc_d=pc.get("centroid_dist_km"), pc_lat=pc.get("centroid_lat"), pc_lon=pc.get("centroid_lon"),
                                tmax=r.get("t_max_k"), tbg=r.get("t_bg_k"), n_aps=len(aps), maxbt=max([p.get("bt_k") or 0 for p in aps], default=None), f5=r.get("f5_core_vrp_mw"),
                                Lbg=r.get("diag_L_bg_w_m2_sr_um"), fp=r.get("diag_n_first_pass_pixels"), rec=r.get("diag_n_second_pass_recapture"))
                print("   ", k, "ref", ref); print("       control:", d(rc)); print("       brazo  :", d(rs))
