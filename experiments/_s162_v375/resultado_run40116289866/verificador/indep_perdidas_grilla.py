import io, sys, json, collections
from pathlib import Path
exec(open(Path(__file__).with_name("indep_decision.py"), encoding="utf-8").read().split("rows162 = ")[0].replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\"utf-8\")", "pass"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def grid(i, art):
    z = sorted(set(list(Path(art).rglob(f"grilla_{i:03d}.npz")) + list(Path(art).rglob(f"grilla_{i:04d}.npz"))))
    q = np.load(z[0]); return q["mir"].astype(float), q["tir"].astype(float)
def stats(i, o, art):
    mir, tir = grid(i, art)
    g = o["grilla"]; n = g["n"]
    xs = g["ul_x"] + g["celda"] * (np.arange(n) + .5); ys = g["ul_y"] - g["celda"] * (np.arange(n) + .5)
    X, Y = np.meshgrid(xs, ys)
    d = np.hypot(X - g["X0"], Y - g["Y0"]) / 1000
    nti = (mir - tir) / (mir + tir)
    near = d <= 8
    med, sd = np.nanmedian(nti), np.nanstd(nti)
    return dict(nan_frac=float(np.isnan(mir).mean()), nti_max_near=float(np.nanmax(np.where(near, nti, np.nan))), z=float((np.nanmax(np.where(near, nti, np.nan)) - med) / sd), mir_max_near=float(np.nanmax(np.where(near, mir, np.nan))), mir_med=float(np.nanmedian(mir)))
print("protegidas perdidas (S159):")
for x in rows:
    if x["c"] == "pos_prot" and not x["pub"]["C13"]:
        o = obj[x["i"]]; print(" ", x["vol"], x["hora"], stats(x["i"], o, A159))
print("Tupungatito bajo 1 MW publicadas por C13 (muestra de 5), mismo estadistico:")
k = 0
for x in rows:
    if x["vol"] == "Tupungatito" and x["c"] == "pos_bajo" and x["pub"]["C13"] and k < 5:
        k += 1; o = obj[x["i"]]; print(" ", x["lote"], x["hora"], stats(x["i"], o, A162 if x["lote"] == "S162" else A159))
print("Tupungatito neg_resto (muestra de 5):")
k = 0
for x in rows:
    if x["vol"] == "Tupungatito" and x["c"] == "neg_resto" and k < 5:
        k += 1; o = obj[x["i"]]; print(" ", x["lote"], x["hora"], stats(x["i"], o, A162 if x["lote"] == "S162" else A159))
