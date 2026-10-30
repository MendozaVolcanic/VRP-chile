# Auditoría S169 f1 (P-G): ¿las cajas que mide V750-B (probe_v750b.cajas) son las que la vía arma con caja_roi
# (pipeline/mirova_v750_codigo.py de main 443da8649), volcán por volcán? Y la grilla del generador (02_seleccion.grillas)
# ¿es la de grillas_mirova.yaml? Si no, el brazo que gane en V750-B no sería el que corre en producción.
# Pregunta 1: si la equivalencia estuviera rota, ¿se vería? Control positivo: una caja B2 corrida una celda se detecta.
# Pregunta 2: instrumento muerto -> la comparación daría 0 celdas comparadas; se imprime el denominador.
import ast, re, sys
from pathlib import Path
import numpy as np, yaml
sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent
sys.path.insert(0, str(D / "roi_run"))
from pipeline import mirova_v750_codigo as MV
# --- cajas() del probe, extraída con ast (sin importar el probe, que arrastra probe_n y la red)
src = (D / "arbol/experiments/_s162_v750b/probe_v750b.py").read_text(encoding="utf-8")
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "cajas")
N, CELDA = 67, 750.0
class PG:   # copia de probe_granulos.caja_mirova (main 443da8649, l. 44-53)
    @staticmethod
    def caja_mirova(n=N, lado_roi1=21, lado_roi2=7):
        b = np.zeros((n, n)); c = n // 2; h1, h2 = lado_roi1 // 2, lado_roi2 // 2
        b[c - h1:c + h1 + 1, c - h1:c + h1 + 1] = 1; b[c - h2:c + h2 + 1, c - h2:c + h2 + 1] = 2
        return b
class PN: CELDA = CELDA
ns = {"np": np, "PG": PG, "PN": PN, "N": N, "C": N // 2}
exec(ast.get_source_segment(src, fn), ns)
cajas = ns["cajas"]
# --- grillas del generador (02_seleccion.grillas, main) y celda_crater (objetivos_v750b.celda_crater)
txt = (D / "grilla_tif_salida_main.txt").read_text(encoding="utf-8")
G = {}
for ln in txt.splitlines():
    m = re.match(r"(\w+)/\S+: EPSG (\d+), 134x134, celda 375.0 m, origen UL \(([-\d.]+), ([-\d.]+)\), centro \(([-\d.]+), ([-\d.]+)\)", ln)
    if m and m.group(1) not in G:
        ux, uy = float(m.group(3)), float(m.group(4))
        G[m.group(1)] = {"epsg": int(m.group(2)), "ul_x": ux - 187.5, "ul_y": uy - 187.5}
vy = {v["name"]: v for v in yaml.safe_load((D / "vy_main.yaml").read_text(encoding="utf-8"))["volcanoes"]}
from pyproj import Transformer
def celda_crater_gen(g, lat, lon):
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True); x, y = t.transform(lon, lat)
    return [int((g["ul_y"] - y) // CELDA), int((x - g["ul_x"]) // CELDA)]
TIF = {"NevadosDeChillan": "ChillanNevadosde"}
PAR = (("B0", "def"), ("B1", "sens"), ("B2", "crater"), ("B3", "inner"), ("B5", "corona"))
tot = dif = 0
for v in MV_VOLC if False else ["Chaiten","NevadosDeChillan","Copahue","Isluga","Lascar","Lastarria","Llaima","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]:
    g = MV.grilla_del_volcan(v); gg = G[TIF.get(v, v)]
    dg = (abs(g["ul_x"] - gg["ul_x"]), abs(g["ul_y"] - gg["ul_y"]))
    lat, lon = vy[v].get("vent_lat", vy[v]["lat"]), vy[v].get("vent_lon", vy[v]["lon"])
    cg = tuple(celda_crater_gen(gg, lat, lon)); cv = tuple(MV.celda_de(g, lat, lon))
    inner = float(vy[v]["inner_radius_km"])
    cj = cajas(cg, inner)
    filas = []
    for b, tipo in PAR:
        bv = MV.caja_roi(tipo, n=g["n"], celda_crater=cv, inner_km=inner, paso_m=g["paso"])
        d = int((cj[b] != bv).sum()); tot += cj[b].size; dif += d; filas.append(f"{b}/{tipo}:{d}")
    print(f"{v:20s} d(ul)=({dg[0]:.3f},{dg[1]:.3f}) m  celda gen {cg} vía {cv}  celdas distintas {' '.join(filas)}")
print(f"== celdas comparadas {tot}, distintas {dif}")
# control positivo: mover una celda el cráter de la vía en Tupungatito tiene que ser visible
g = MV.grilla_del_volcan("Tupungatito"); lat, lon = vy["Tupungatito"]["vent_lat"], vy["Tupungatito"]["vent_lon"]
c = MV.celda_de(g, lat, lon); inner = 7.0
b1 = MV.caja_roi("crater", n=67, celda_crater=(c[0], c[1] + 1), inner_km=inner, paso_m=750.0)
print("control positivo (cráter corrido 1 celda): celdas distintas", int((cajas(tuple(c), inner)["B2"] != b1).sum()), "(tiene que ser > 0)")
