"""VS34 V-4 parte B: que hace la via con el calor de un vecino. Granulo sintetico (sin red) como el de
tests/test_sombra_34_s172.py (fondo 270/265 K con ruido 0.3 K, de noche), pero con el foco puesto en las coordenadas del
VECINO (no en el cráter del objetivo), o en ambos, o en ninguno. Se corre calcular_vrp_granulo del objetivo.
Q1: si la via sumara el calor del vecino al volcan nuevo, esto lo ve: vrp_mw>0 con foco SOLO en el vecino. Control
positivo: foco en el cráter del objetivo (vrp>0 y dist~0). Control negativo: sin foco (vrp=0).
Q2: si el instrumento estuviera muerto (rec None) se imprime None, no 0.
Limite: gránulo limpio, sin textura real; es una prueba del CAMINO del código, no de cuanto calor suma un dia real."""
import sys, os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "D:/vrp-trabajo/worktrees/s172-sombra34")
import numpy as np, yaml
from pipeline import mirova_v750_codigo as MV
W = "D:/vrp-trabajo/worktrees/s172-sombra34"
vols = {v["name"]: v for v in yaml.safe_load(open(f"{W}/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
def granulo(lat0, lon0, familia, focos, n=121, span=0.45):
    cfg = MV.FAMILIAS[familia]
    la = lat0 + np.linspace(-span, span, n)
    lo = lon0 + np.linspace(-span, span, n) / np.cos(np.radians(lat0))
    LO, LA = np.meshgrid(lo, la[::-1])
    rng = np.random.default_rng(172)
    tm = 270.0 + rng.normal(0, 0.3, LA.shape); tt = 265.0 + rng.normal(0, 0.3, LA.shape)
    for (fl, fo, T) in focos:
        i, j = np.unravel_index(np.argmin((LA - fl) ** 2 + ((LO - fo) * np.cos(np.radians(lat0))) ** 2), LA.shape)
        tm[i, j] = T
    b_mir, b_tir = cfg["bandas"]
    rad = {b_mir: MV.temperatura_a_radiancia(tm, cfg["lam_mir"]), b_tir: MV.temperatura_a_radiancia(tt, cfg["lam_tir"])}
    ang = {k: np.full(LA.shape, val) for k, val in (("solar_zenith", 120.0), ("sensor_zenith", 10.0), ("solar_azimuth", 0.0), ("sensor_azimuth", 90.0))}
    return rad, LA, LO, ang
def correr(obj, fam, focos):
    v = vols[obj]
    rad, LA, LO, ang = granulo(v["lat"], v["lon"], fam, focos)
    r = MV.calcular_vrp_granulo(rad, LA, LO, ang, obj, v["lat"], v["lon"], None, "SINTETICO", familia=fam)
    if r is None: return "None (la via no devolvio record)"
    pc = r["primary_cluster"] or {}
    return (f"vrp_mw={r['vrp_mw']:.3f} n_anom={r['n_anomalous_pixels']} dist_cumulo_km={pc.get('centroid_dist_km')} "
            f"final_src={r['final_hotspot_source']} dist_class={r['distance_class']} t_max_k={r['t_max_k']}")
pares = [("Quetrupillan", "Villarrica"), ("Michinmahuida", "Chaiten"), ("AntillancaCasablanca", "PuyehueCordonCaulle"), ("Callaqui", "Copahue"),
         ("Lonquimay", "Tolhuaca"), ("DescabezadoGrande", "CerroAzulQuizapu"), ("Irruputuncu", "OlcaParuma")]
for T in (300.0, 320.0):
    print(f"\n===== foco de {T:.0f} K en un pixel (MIR), fondo 270 K =====")
    for obj, vec in pares:
        for fam in ("VIIRS750", "VIIRS375", "MODIS"):
            o, w = vols[obj], vols[vec]
            solo_vec = correr(obj, fam, [(w["lat"], w["lon"], T)])
            print(f"{obj:21s} {fam:8s} SOLO foco en {vec:20s}: {solo_vec}")
        # control positivo y negativo una vez por objetivo (V750)
        print(f"{obj:21s} VIIRS750 CTRL foco en el crater del objetivo   : {correr(obj, 'VIIRS750', [(vols[obj]['lat'], vols[obj]['lon'], T)])}")
        print(f"{obj:21s} VIIRS750 CTRL sin foco                         : {correr(obj, 'VIIRS750', [])}")
        print(f"{obj:21s} VIIRS750 foco en AMBOS (crater debil 285 K)     : {correr(obj, 'VIIRS750', [(vols[obj]['lat'], vols[obj]['lon'], 285.0), (w['lat'], w['lon'], T)])}")
