# -*- coding: utf-8 -*-
"""Verificador S149: la condicion 'cumulo summit 0 MW' (V750/V375) y 'far con energia dentro' (MODIS) en pos vs neg, por volcan."""
import sys, io, json, collections, statistics
from pathlib import Path
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
INI, FIN = sys.argv[1], sys.argv[2]
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (INI, FIN))
recs, casos = [], []
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (INI <= r.get("datetime_utc", "")[:10] <= FIN): continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if bp.es_pasada_diurna_descartada(b, *coords[vol], dt): continue
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": r["datetime_utc"][:10], "r": r})
        casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, inner[vol]])
for rec, p in zip(recs, bp.correr_node(casos)): rec["pub"] = p[4]
bp.etiquetar(recs, por_vb, ns, nv)
def s0(x, dmax=None):
    r = x["r"]; pc = r.get("primary_cluster")
    if not pc or (pc.get("vrp_mw") or 0) != 0 or r.get("distance_class") != "summit": return False
    d = pc.get("centroid_dist_km")
    return d is not None and d <= (dmax if dmax else inner[x["vol"]])
def farE(x):
    r = x["r"]; pc = r.get("primary_cluster")
    return bool(pc) and (pc.get("vrp_mw") or 0) > 0 and r.get("distance_class") == "far" and (pc.get("centroid_dist_km") or 99) <= inner[x["vol"]]
print("ventana", INI, FIN)
for b, cond, nom in (("VIIRS750", s0, "summit0MW"), ("VIIRS375", s0, "summit0MW"), ("MODIS", farE, "far_energia_dentro")):
    print(f"\n== {b} condicion {nom}: por volcan  pos(n, cond, pub) | neg_limpio(n, cond, pub) | rutina_en_noche_con_alerta(n, cond)")
    for vol in bp.VOLS + ["TODOS"]:
        sel = [x for x in recs if x["b"] == b and (vol == "TODOS" or x["vol"] == vol)]
        P = [x for x in sel if x["lab"] == "pos"]; N = [x for x in sel if x["lab"] == "neg_limpio"]
        R = [x for x in sel if x["lab"] == "sin_info" and x["rutina_pasada"] and x["noche_con_alerta_sensor"]]
        print(f"   {vol:20s} pos {len(P):4d} {sum(cond(x) for x in P):4d} {sum(x['pub'] for x in P):4d} | neg {len(N):5d} {sum(cond(x) for x in N):5d} {sum(x['pub'] for x in N):5d} | rut {len(R):4d} {sum(cond(x) for x in R):4d}")
    if nom == "summit0MW":
        for lab in ("pos", "neg_limpio"):
            z = [x for x in recs if x["b"] == b and x["lab"] == lab and s0(x)]
            if not z: continue
            d14 = sum(1 for x in z if x["r"]["primary_cluster"]["centroid_dist_km"] <= 1.4)
            frio = 0; conap = 0; solo_recap = 0; t1 = 0; difs = []
            for x in z:
                r = x["r"]; aps = r.get("anomaly_pixels") or []
                if (r.get("diag_n_first_pass_pixels") or 0) == 0: solo_recap += 1
                if r.get("triggered_test1"): t1 += 1
                if aps and r.get("t_bg_k") is not None:
                    conap += 1; mb = max(p.get("bt_k") or 0 for p in aps)
                    difs.append(mb - r["t_bg_k"]); frio += mb <= r["t_bg_k"]
            print(f"   [{lab}] n={len(z)} dist<=1.4km={d14} | sin pixeles de primer pase={solo_recap} | Test1 disparado={t1} | con anomaly_pixels={conap}, de esos pixel mas caliente <= t_bg: {frio}; mediana (bt_max_ap - t_bg) = {statistics.median(difs) if difs else None} K")
            print("        n_pixels del cumulo:", collections.Counter(x["r"]["primary_cluster"].get("n_pixels") for x in z).most_common(5), "| fuente:", collections.Counter(x["r"].get("final_hotspot_source") for x in z).most_common(4))
