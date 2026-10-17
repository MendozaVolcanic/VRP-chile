# Verificador 1.23: controles sobre la vara VIIRS. Solo lectura del repo.
# Uso: python -I controles_vara.py <dir del experimento> <carpeta artefactos>
import json, math, random, statistics as st, sys
from collections import defaultdict
from pathlib import Path

EXP = Path(sys.argv[1]); ART = sys.argv[2]
sys.path.insert(0, str(EXP)); sys.path.insert(0, str(EXP.parent / "_s151_mxd03_cumulo_121"))
sys.path.insert(0, str(EXP.parent / "_s151_mxd03_etiquetas")); sys.path.insert(0, str(EXP.parents[1] / "scripts"))
import evaluar_sola as E
import jobs_123 as J

pob = E._cargar(J.POBLACION)
tabla = E._cargar(EXP / "vara_viirs.json")
aus = {(a["volcan"], a["clave"]) for a in E._cargar(E.DIR_121 / "archivo_cmr.json")["ausentes"]}
salidas = {}
for p in sorted(Path(ART).rglob("*.json")):
    d = E._cargar(p)
    if isinstance(d, dict) and "granulos" in d and "job" in d and "k_nulos" in d:
        salidas[d["job"]] = d
jobs = J.partir(pob)
pedidos = {(jobs[j]["volcan"], c) for j in jobs for c in jobs[j]["granulos"]}
ok = [f for f in E._unir(pob, salidas) if (f["volcan"], f["clave"]) in pedidos
      and (f["volcan"], f["clave"]) not in aus and f.get("estado") == "ok"]
print("ok", len(ok))


def filas(fuente="pico", nivel="estricta", filtro="pos"):
    out = []
    for f in ok:
        t = (tabla["granulos"]).get("%s|%s" % (f["volcan"], f["clave"]))
        if not t or not (t.get(nivel) or {}).get("noche"):
            continue
        if filtro == "pos" and f.get("lab") != "pos":
            continue
        if filtro == "nopos" and f.get("lab") == "pos":
            continue
        c, m = E._pos(f, "C", fuente), E._pos(f, "M", fuente)
        if c is None or m is None:
            continue
        vent = t["vent"]
        v = (t[nivel]["noche"]["n_km"], t[nivel]["noche"]["e_km"])
        out.append(dict(volcan=f["volcan"], noche="%s|%s" % (f["volcan"], f["datetime_utc"][:10]),
                        sat=f["sensor"].replace("MODIS_", ""), cenit=f.get("sensor_zenith_deg"), lab=f.get("lab"),
                        C=E._ne(vent, *c), M=E._ne(vent, *m), v=v))
    return out


def d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def boot(fs, key, b=1000, seed=1):
    rng = random.Random(seed)
    pn = defaultdict(list)
    for x in fs:
        pn[x["noche"]].append(key(x))
    ns = list(pn); meds = []
    for _ in range(b):
        y = []
        for n in (rng.choice(ns) for _ in ns):
            y.extend(pn[n])
        meds.append(st.median(y))
    meds.sort()
    return round(st.median(key(x) for x in fs), 3), [round(meds[25], 3), round(meds[974], 3)]


def dd_v(x, v=None):
    v = x["v"] if v is None else v
    return d(x["C"], v) - d(x["M"], v)


def informe(nombre, fs):
    if not fs:
        print(nombre, "vacio"); return
    print("\n==", nombre, "n=%d noches=%d" % (len(fs), len({x["noche"] for x in fs})))
    print("  dd con la vara VIIRS        ", boot(fs, dd_v))
    print("  dd con v = ancla (0,0)      ", boot(fs, lambda x: dd_v(x, (0.0, 0.0))))
    print("  |v - ancla| mediana km      ", round(st.median(math.hypot(*x["v"]) for x in fs), 3),
          " p90", round(sorted(math.hypot(*x["v"]) for x in fs)[int(0.9 * len(fs))], 3))
    print("  |M - ancla| mediana, |C - ancla| mediana", round(st.median(math.hypot(*x["M"]) for x in fs), 3),
          round(st.median(math.hypot(*x["C"]) for x in fs), 3))
    for s in ("TERRA", "AQUA"):
        sel = [x for x in fs if x["sat"] == s]
        if sel:
            print("  %-5s n=%3d dd vara %s | dd ancla %s" % (s, len(sel), boot(sel, dd_v), boot(sel, lambda x: dd_v(x, (0.0, 0.0)))))
    for lo, hi in ((0, 35), (35, 90)):
        sel = [x for x in fs if x["cenit"] is not None and lo <= x["cenit"] < hi]
        if sel:
            print("  cenit %2d-%2d n=%3d dd vara %s | dd ancla %s" % (lo, hi, len(sel), boot(sel, dd_v), boot(sel, lambda x: dd_v(x, (0.0, 0.0)))))
    # control de barajado: v de OTRA noche del mismo volcan (borra la informacion propia de la noche)
    rng = random.Random(7)
    por_vol = defaultdict(list)
    for x in fs:
        por_vol[x["volcan"]].append(x)
    meds = []
    for _ in range(500):
        y = []
        for vol, xs in por_vol.items():
            vs = [x["v"] for x in xs]
            rng.shuffle(vs)
            y.extend(dd_v(x, v) for x, v in zip(xs, vs))
        meds.append(st.median(y))
    meds.sort()
    print("  dd con v barajada entre noches (500): mediana %.3f [%.3f, %.3f]" % (st.median(meds), meds[12], meds[487]))
    # cuanto informa la vara mas alla del ancla: componente de (v - ancla) a lo largo de (M - C)
    lam_anc = []
    for x in fs:
        ax = (x["M"][0] - x["C"][0], x["M"][1] - x["C"][1]); a2 = ax[0] ** 2 + ax[1] ** 2
        if a2 > 1e-8:
            lam_anc.append(((0 - x["C"][0]) * ax[0] + (0 - x["C"][1]) * ax[1]) / a2)
    print("  lambda con v = ancla: mediana %.3f" % st.median(lam_anc))
    # correlacion noche a noche: (v - ancla) contra (M - ancla), por componente
    for i, comp in ((0, "norte"), (1, "este")):
        a = [x["v"][i] for x in fs]; b = [x["M"][i] for x in fs]; c = [x["C"][i] for x in fs]
        def corr(p, q):
            mp, mq = st.mean(p), st.mean(q)
            num = sum((u - mp) * (w - mq) for u, w in zip(p, q))
            den = math.sqrt(sum((u - mp) ** 2 for u in p) * sum((w - mq) ** 2 for w in q))
            return round(num / den, 3) if den else None
        print("  corr %s v-M %s  v-C %s  | sd v %.3f sd M %.3f" % (comp, corr(a, b), corr(a, c), st.pstdev(a), st.pstdev(b)))


informe("principal (pico, estricta, pos)", filas())
informe("pico estricta, NO pos (lo que agrega pico_estricta_todos)", filas(filtro="nopos"))
informe("pico estricta todos", filas(filtro="todos"))
informe("pico amplia, pos", filas(nivel="amplia", filtro="pos"))
informe("pico amplia, NO pos", filas(nivel="amplia", filtro="nopos"))
informe("pico amplia todos", filas(nivel="amplia", filtro="todos"))
fp = filas()
print("\nprincipal por volcan:", {v: boot([x for x in fp if x["volcan"] == v], dd_v) for v in sorted({x['volcan'] for x in fp})})
print("principal, cenit >= 35, granulos:")
for x in sorted([x for x in fp if x["cenit"] >= 35], key=lambda x: x["cenit"]):
    print("   %s %s %5.1f C=(%.2f,%.2f) M=(%.2f,%.2f) v=(%.2f,%.2f) dd=%.2f" % (x["noche"], x["sat"], x["cenit"], *x["C"], *x["M"], *x["v"], dd_v(x)))
