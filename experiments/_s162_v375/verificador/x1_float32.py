# X1: sensibilidad del control "recalculo sin red = runner" (1e-6 MW) al redondeo float32 de la grilla guardada.
import sys, json, io, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
AQUI = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/s162-viirs375-c1b864/experiments/_s162_v375")
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parents[1])); sys.path.insert(0, str(AQUI.parents[1]/"scripts"))
import evaluar as EV, brazos as BR
V = EV.volcanes()
art = r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945"
obj = {o["id"]: o for o in json.loads((AQUI.parents[1]/"experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))}
res = EV.leer_resultados(art)
rng = np.random.default_rng(1)
for i in (268, 265, 299, 214):
    o, r = obj[i], res[i]
    z = list(Path(art).rglob(f"grilla_{i:03d}.npz"))[0]
    q = np.load(z); mir32, tir32 = q["mir"], q["tir"]
    v = V[o["volcan"]]; xc, yc = BR.crater_xy(o["grilla"], v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
    base = BR.correr_brazos(mir32.astype(np.float64), tir32.astype(np.float64), o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc, v["inner_radius_km"], o["volcan"], r["dayflag"], r["sunglint"], brazos=("M14",))["M14"]
    difs = []
    for t in range(6):
        # "verdad float64" hipotetica = float32 guardado + error de redondeo de media ulp; luego se guarda como float32 (lo que hace el runner)
        e = lambda a: a.astype(np.float64) * (1 + rng.uniform(-6e-8, 6e-8, a.shape))
        m64, t64 = e(mir32), e(tir32)
        a = BR.correr_brazos(m64, t64, o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc, v["inner_radius_km"], o["volcan"], r["dayflag"], r["sunglint"], brazos=("M14",))["M14"]
        b = BR.correr_brazos(m64.astype(np.float32).astype(np.float64), t64.astype(np.float32).astype(np.float64), o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc, v["inner_radius_km"], o["volcan"], r["dayflag"], r["sunglint"], brazos=("M14",))["M14"]
        difs.append((a["npix"] == b["npix"], abs((a["vrp_mw"] or 0) - (b["vrp_mw"] or 0))))
    print(i, o["volcan"], "VRP", round(base["vrp_mw"], 3), "npix", base["npix"], "igual npix / |dVRP| MW:", [(x, f"{y:.2e}") for x, y in difs])
