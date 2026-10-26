# Verificador V750-B: recalcula la celda del crater con pyproj por mi cuenta (sin objetivos_v750b) y mide
# la distancia vent -> centro de la grilla. Pregunta 1: si celda_crater estuviera en el sistema equivocado (fila sur
# arriba, o x/y invertidos) la celda recalculada aqui no coincidiria. Pregunta 2: si la grilla no cargara, el script
# aborta (no imprime ceros).
import sys, json, math
from pathlib import Path
import yaml
sys.path.insert(0, sys.argv[1] + "/experiments/_s159/n")
sys.path.insert(0, sys.argv[1] + "/experiments/_s162_v750b")
import importlib.util
spec = importlib.util.spec_from_file_location("sel", sys.argv[1] + "/experiments/_s159/n/02_seleccion.py")
SEL = importlib.util.module_from_spec(spec); spec.loader.exec_module(SEL)
import objetivos_v750b as OV
from pyproj import Transformer
G = SEL.grillas(); assert G, "sin grillas"
vy = {v["name"]: v for v in yaml.safe_load(open(sys.argv[1] + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def hav(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c); x=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*6371.0*math.asin(math.sqrt(x))
for vol in ("PuyehueCordonCaulle","Tupungatito","PlanchonPeteroa","Lascar","Villarrica","NevadosDeChillan"):
    g = G[SEL.TIF.get(vol, vol)]; v = vy[vol]
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(vlon, vlat)
    # mi calculo: centros de celda como grillar (xs = ul_x + 750*(i+0.5); ys = ul_y - 750*(j+0.5)); celda = la mas cercana
    col = min(range(67), key=lambda i: abs(g["ul_x"] + 750*(i+0.5) - x))
    fil = min(range(67), key=lambda j: abs(g["ul_y"] - 750*(j+0.5) - y))
    suyo = OV.celda_crater(g, vlat, vlon)
    xc, yc = t.transform(g["centro_lon"], g["centro_lat"])
    print(f"{vol:22s} epsg {g['epsg']} mia (fila,col)=({fil},{col}) suya={suyo} | vent->centro {hav(vlat,vlon,g['centro_lat'],g['centro_lon']):.2f} km "
          f"(dN {(y-yc)/1000:+.2f} dE {(x-xc)/1000:+.2f} km) | centro en celda ({int((g['ul_y']-yc)//750)},{int((xc-g['ul_x'])//750)})")
