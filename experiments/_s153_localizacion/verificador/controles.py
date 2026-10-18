"""Controles del verificador S153: predicado node (casos del guard S139), haversine y port del marcador."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verif_posicion as vp  # noqa: E402
print("control_identidad_predicado (esperado [False, True, True, True, False], [1, 0]):", vp.bp.control_identidad_predicado())
la, lo = vp.VENT_FE["Villarrica"]
print("haversine vent->vent:", vp.hav(la, lo, la, lo), "| vent -> 3 km al norte:", round(vp.hav(la, lo, la + 3 / 111.195, lo), 3))
r_t1 = {"final_hotspot_lat": la, "final_hotspot_lon": lo, "final_hotspot_source": "test1_roi", "anomaly_pixels": [{"lat": la + 0.025, "lon": lo}]}
r_ctx = {"final_hotspot_lat": la + 0.001, "final_hotspot_lon": lo, "final_hotspot_source": "ctx_cluster", "anomaly_pixels": [{"lat": la + 0.2, "lon": lo}]}
print("marcador test1_roi (esperado crater):", vp.pos_mapa_detalle(r_t1, (la, lo)), "| ctx_cluster (esperado anomaly_pixels[0]):", vp.pos_mapa_detalle(r_ctx, (la, lo)))
