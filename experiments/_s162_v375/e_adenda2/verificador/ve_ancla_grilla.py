# VE2: (1) el punto desde el que el lector mide (v.get("vent_lat", lat)) es el ancla de produccion (get_detection_anchor) en los 11
# volcanes; (2) la grilla de la via (MV.grilla_del_volcan) es la misma que la que guardo el run (o["grilla"] de la lista) en
# epsg, n, ul_x, ul_y, paso, x0, y0. P1: veria una diferencia de ancla o de grilla (control: imprime las 11 filas). P2: si la
# comparacion estuviera muerta no habria columnas distintas ni siquiera en el control de offset (se agrega una perturbacion).
import sys, json
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
V = R/"experiments/_s162_v375"
sys.path.insert(0, str(V/"e_adenda2")); sys.path.insert(0, str(V)); sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"scripts"))
import leer_posicion_v375e as L, evaluar as E
from pipeline import mirova_v750_codigo as MV
from pipeline.geo_utils import get_detection_anchor
Vs = E.volcanes()
obj = L.objetivos(V/"e_adenda2/objetivos_run_far_v375.json")
import banco_paridad as B
malos = 0
for n in B.VOLS:
    v = Vs[n]
    a = get_detection_anchor(v); mio = (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
    g = MV.grilla_del_volcan(n, paso_m=375.0, clave_roi="roi_v375")
    go = next(o["grilla"] for o in obj.values() if o["volcan"] == n and o.get("grilla"))
    dif = {k: (g.get(k), go.get(k2)) for k, k2 in (("epsg","epsg"),("n","n"),("ul_x","ul_x"),("ul_y","ul_y"),("paso","paso"),("x0","X0"),("y0","Y0")) if g.get(k) != go.get(k2)}
    print(f"{n:20s} ancla_igual={a==mio} grilla_dif={dif}")
    malos += (a != mio) + bool(dif)
print("discrepancias:", malos)
# control positivo: perturbar x0 de una grilla y ver que la comparacion la detecta
g = dict(MV.grilla_del_volcan("Lascar", paso_m=375.0, clave_roi="roi_v375")); g["x0"] += 1.0
go = next(o["grilla"] for o in obj.values() if o["volcan"] == "Lascar" and o.get("grilla"))
print("control positivo (x0+1 m) detectado:", g["x0"] != go["X0"])
