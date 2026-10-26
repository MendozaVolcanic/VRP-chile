"""Verificador S153: en K, por que el marcador primario del mapa de detalle (anomaly_pixels[0]) cae lejos del cumulo.
Uso: ... <carpeta_union> <brazo> <volcan>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verif_posicion as vp  # noqa: E402
U, arm, v = sys.argv[1:4]
recs = [r for r in vp.cargar(os.path.join(U, arm, v + ".json"), v, "2026-08-29", "2026-10-08") if r["_pub"]]
vent = vp.VENT_FE[v]; n = 0; ordenado = 0; lejos = 0
for r in recs:
    ap = r.get("anomaly_pixels") or []; pc = r["primary_cluster"]
    if not ap: continue
    d0 = vp.hav(*vent, ap[0]["lat"], ap[0]["lon"]); dpc = vp.hav(*vent, pc["centroid_lat"], pc["centroid_lon"])
    vr = [p.get("vrp_mw") or 0 for p in ap]; ordenado += vr == sorted(vr, reverse=True)
    dmin = min(vp.hav(*vent, p["lat"], p["lon"]) for p in ap)
    if d0 > 2:
        lejos += 1
        if n < 6:
            print(r["datetime_utc"], r["sensor"], f"src={r.get('final_hotspot_source')} pc_n={pc.get('n_pixels')} dpc={dpc:.2f} ap0={d0:.2f} ap0_vrp={vr[0]:.3f} n_ap={len(ap)} ap_mas_cercano={dmin:.2f} vrp_max_ap={max(vr):.3f} pc_vrp={pc.get('vrp_mw')}")
            n += 1
print(f"{v} {arm}: publicadas con anomaly_pixels {sum(1 for r in recs if r.get('anomaly_pixels'))}, ordenadas desc por vrp {ordenado}, ap0 a >2 km {lejos}")
