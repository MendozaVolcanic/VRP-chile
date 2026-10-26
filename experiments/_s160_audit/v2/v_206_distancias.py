"""206: distancia entre lat/lon del volcan (centro del anillo 5-25 km) y vent_lat/vent_lon (ancla de deteccion,
geo_utils.get_detection_anchor), y entre lat/lon y mirova_center, para los 11 Tier A. Control: Copahue debe dar 0."""
import math, sys, yaml
sys.stdout.reconfigure(encoding="utf-8")
vs = yaml.safe_load(open(r"D:\vrp-trabajo\temporales\s160_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]
def h(a, b, c, d):
    R = 6371; p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
out = []
for v in vs:
    if v.get("radius_km") == 25:
        out.append(f"{v['name']} centro-vent_km={h(v['lat'],v['lon'],v['vent_lat'],v['vent_lon']):.2f} inner={v.get('inner_radius_km')} "
                   f"centro-mirova_center_km={h(v['lat'],v['lon'],v.get('mirova_center_lat',v['lat']),v.get('mirova_center_lon',v['lon'])):.2f}")
print("\n".join(out))
open(__file__.replace("v_206_distancias.py", "v_206_distancias_salida.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
