# -*- coding: utf-8 -*-
"""Verificador S162 V375: decision reimplementada por mi cuenta (predicado y P2 propios) desde los port JSON del runner
(S162) y la cache de brazos recalculados (S159). Incluye: reproduccion de la tabla, leave-one-volcano-out del brazo
global, sensibilidad de la prueba de signos a la semilla, ΔE por volcan, el B del lote sin pesos reponderados,
sensibilidad de B a tratar neg_pub como censo, y la lectura con las 11 no observadas contadas como no-publica."""
import collections, itertools, json, math, io, sys
from pathlib import Path
import numpy as np
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864")
AQUI = Path(__file__).resolve().parent
A162 = Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866")
A159 = Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
EXCL = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
BRAZOS = ("M14", "M13", "M21", "C13", "C14", "C21", "PIX7", "SENS", "CIRC", "SENS_PT")

vy = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
vy = vy["volcanoes"] if isinstance(vy, dict) else vy
inner = {v["name"]: v.get("inner_radius_km") for v in vy}
o162 = json.loads((RAIZ / "experiments/_s162_v375/objetivos_v375_bc.json").read_text(encoding="utf-8"))
obj = {o["id"]: dict(o) for o in o162["pasadas"]}
for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
    if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in EXCL:
        obj[o["id"]] = {**o, "lote": "S159", "estrato": f"{o['volcan']}|{o['estrato_z']}"}
N = {c: {h: v["N"] for h, v in est.items()} for c, est in o162["meta"]["estratos"].items()}


def leer(art):
    res = {}
    for f in sorted(Path(art).rglob("resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            res[r["id"]] = r
    return res


r162, r159 = leer(A162), leer(A159)
cache = json.loads((AQUI / "cache_copia.json").read_text(encoding="utf-8"))
import hashlib, numpy as np  # noqa


def sha_grilla(i, art):
    z = sorted(set(list(Path(art).rglob(f"grilla_{i:03d}.npz")) + list(Path(art).rglob(f"grilla_{i:04d}.npz"))))
    return hashlib.sha256(z[0].read_bytes()).hexdigest()


def publica(p, vol):
    if not p or not p.get("npix") or not p.get("vrp_mw") or p["vrp_mw"] <= 0:
        return False
    return min(q[3] for q in p["pixeles"]) <= inner[vol] + 1e-12


def vrp_de(p):
    return float(p["vrp_mw"]) if p and p.get("npix") and p.get("vrp_mw") else 0.0


rows = []
for i, o in sorted(obj.items()):
    r = (r162 if o["lote"] == "S162" else r159).get(i)
    if not r or r.get("estado") != "ok":
        continue
    if o["lote"] == "S162":
        port = r["port"]
    else:
        port = cache[f"{i}|{sha_grilla(i, A159)}"]
    h = o["hora_utc"]
    rows.append({"i": i, "lote": o["lote"], "c": o["clase"], "h": o["estrato"], "vol": o["volcan"], "hora": h,
                 "tramo": "T" if h[:10] < "2026-06-13" else ("O1" if h[:10] < "2026-08-29" else "O2"),
                 "bloque": f"{o['volcan']}|{h[:10]}", "K": bool(o["pub_prod"]), "prot": bool(o["protegida"]),
                 "pub": {b: publica(port[b], o["volcan"]) for b in BRAZOS},
                 "vrp": {b: vrp_de(port[b]) for b in BRAZOS}, "mir": float(o["mirova_vrp"] or 0)})
print("filas", len(rows), collections.Counter((x["lote"], x["c"]) for x in rows))


def pesos(rs):
    n = collections.Counter((x["c"], x["h"]) for x in rs)
    return {id(x): N[x["c"]][x["h"]] / n[(x["c"], x["h"])] for x in rs}


def err(x, b):
    pub = x["K"] if b == "K" else x["pub"][b]
    return (x["c"] == "pos_bajo" and not pub) or (x["c"] in ("neg_pub", "neg_resto") and pub)


def p2(rs, W, a, ref, seed=162, nsort=10000):
    blo = collections.defaultdict(float)
    for x in rs:
        ea, er = err(x, a), err(x, ref)
        if ea != er:
            blo[x["bloque"]] += W[id(x)] * (1 if ea else -1)
    s = np.array([blo[k] for k in sorted(blo)])
    neto = float(s.sum())
    B = len(s)
    if B <= 4:
        return neto, B, "SIN SUSTRATO", None
    if B <= 20:
        tot = np.zeros(1)
        for v in s:
            tot = np.concatenate([tot + v, tot - v])
        pg = ((tot <= neto + 1e-9).sum()) / 2 ** B
        pp = ((tot >= neto - 1e-9).sum()) / 2 ** B
    else:
        rng = np.random.default_rng(seed)
        S = rng.choice((-1.0, 1.0), size=(nsort, B))
        tot = S @ s
        pg = (1 + (tot <= neto + 1e-9).sum()) / (nsort + 1)
        pp = (1 + (tot >= neto - 1e-9).sum()) / (nsort + 1)
    if neto < -1e-9 and pg <= 0.05:
        v = "GANA"
    elif neto > 1e-9 and pp <= 0.05:
        v = "PIERDE"
    elif neto > 1e-9:
        v = "BLOQUEA"
    else:
        v = "EMPATE"
    return neto, B, v, (pg, pp)


def dE(rs, W, a, ref):
    return sum(W[id(x)] * (int(err(x, a)) - int(err(x, ref))) for x in rs)


def decidir(rs, veto, etiqueta):
    W = pesos(rs)
    print(f"\n### {etiqueta}: {len(rs)} filas; veto sobre {len(veto)}")
    res = {}
    for b in BRAZOS:
        if b == "M14":
            continue
        nuevas = sum(1 for x in veto if x["c"] == "pos_prot" and x["pub"]["M14"] and not x["pub"][b])
        neto, B, v, p = p2(rs, W, b, "M14")
        de = dE(rs, W, b, "K")
        res[b] = (nuevas, v, neto, B, de)
        print(f"  {b:8s} nuevas_perdidas {nuevas}  P2vsM14 {v:12s} neto {neto:+8.2f} B {B:3d}  p {p}  dE_vs_K {de:+8.2f}")
    cand = sorted([(round(res[b][4], 6), b) for b in res if res[b][0] == 0 and res[b][1] == "GANA"])
    print("  candidatos (dE vs K):", cand)
    return cand, W


rows162 = [x for x in rows if x["lote"] == "S162"]
cand_u, Wu = decidir(rows, rows, "UNION")
cand_s, Ws = decidir(rows162, rows, "S162 solo (veto sobre union)")

print("\n### Leave-one-volcano-out (union), sin cada volcan: el mejor candidato y P2 de C13 vs M14")
for v in sorted({x["vol"] for x in rows}):
    rs = [x for x in rows if x["vol"] != v]
    W = pesos(rs)
    out = []
    for b in ("C13", "C14", "C21", "M21", "SENS", "CIRC", "SENS_PT"):
        neto, B, ver, _ = p2(rs, W, b, "M14")
        out.append(f"{b}:{ver[:5]}({neto:+.0f},B{B})")
    print(f"  sin {v:20s} ", " ".join(out))

print("\n### aporte por volcan a la suma ΔE(C13) - ΔE(M14) contra K (union, ponderado)")
W = Wu
por = collections.defaultdict(float)
for x in rows:
    por[x["vol"]] += W[id(x)] * (int(err(x, "C13")) - int(err(x, "M14")))
tot = sum(por.values())
for v, s in sorted(por.items(), key=lambda t: t[1]):
    print(f"  {v:22s} {s:+8.2f}")
print("  total", round(tot, 2))

print("\n### P2 de C13 vs M14 con otras semillas (union, 10.000 sorteos)")
for sd in (1, 2, 3, 162, 999):
    print("  semilla", sd, p2(rows, Wu, "C13", "M14", seed=sd)[:3])

print("\n### C13 contra C14, C21, SENS_PT (union): P2 y dE vs K; ordenacion de candidatos")
for b2 in ("C14", "C21", "SENS_PT"):
    print("  C13 vs", b2, p2(rows, Wu, "C13", b2)[:3], "dE", round(dE(rows, Wu, "C13", b2), 2))

print("\n### B: neg_resto y negativos, distintos tratamientos")


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0)) / d
    return max(0, c - h), min(1, c + h)


def tasa(rs, W, f):
    w = np.array([W[id(x)] for x in rs]); k = np.array([f(x) for x in rs], float)
    p = (w * k).sum() / w.sum(); ne = w.sum() ** 2 / (w ** 2).sum()
    return p, wilson(p * ne, ne), ne


Ntot_pub = sum(N["neg_pub"].values()); Ntot_resto = sum(N["neg_resto"].values())
vara = Ntot_pub / (Ntot_pub + Ntot_resto)
print("vara K", vara, "N_pub", Ntot_pub, "N_resto", Ntot_resto)
for etiqueta, rs in (("union", rows), ("S162", rows162)):
    W = pesos(rs)
    resto = [x for x in rs if x["c"] == "neg_resto"]
    pub = [x for x in rs if x["c"] == "neg_pub"]
    pr_, icr, ner = tasa(resto, W, lambda x: x["pub"]["M14"])
    pp_, icp, nep = tasa(pub, W, lambda x: x["pub"]["M14"])
    # neg_pub censo: tasa exacta con el census union
    allpub = [x for x in rows if x["c"] == "neg_pub"]
    pcen = sum(x["pub"]["M14"] for x in allpub) / len(allpub)
    for nom, (ppx, ic_pub) in (("neg_pub como lo hace el evaluador", (pp_, icp)),
                                ("neg_pub como censo exacto de 133 (S159+S162)", (pcen, (pcen, pcen)))):
        pn = (Ntot_pub * ppx + Ntot_resto * pr_) / (Ntot_pub + Ntot_resto)
        lo = (Ntot_pub * ic_pub[0] + Ntot_resto * icr[0]) / (Ntot_pub + Ntot_resto)
        hi = (Ntot_pub * ic_pub[1] + Ntot_resto * icr[1]) / (Ntot_pub + Ntot_resto)
        print(f"  {etiqueta:6s} {nom}: neg_resto {pr_:.4f} {tuple(round(v,4) for v in icr)}; negativos {pn:.4f} [{lo:.4f}, {hi:.4f}] vs vara {vara:.4f}")

print("\n### B con las 11 no observadas contadas como NO publica (sensibilidad)")
n_unobs = collections.Counter(obj[i]["estrato"] for i, o in obj.items() if o["lote"] == "S162" and (r162.get(i) or {}).get("estado") != "ok")
print("  no observadas por estrato:", dict(n_unobs))
for etiqueta, rs, lote in (("union", rows, None), ("S162", rows162, "S162")):
    # pesos con n_ok + n_unobs en el denominador
    nn = collections.Counter((x["c"], x["h"]) for x in rs)
    for h, v in n_unobs.items():
        nn[("neg_resto", h)] += v
    resto = [x for x in rs if x["c"] == "neg_resto"]
    w = np.array([N["neg_resto"][x["h"]] / nn[("neg_resto", x["h"])] for x in resto])
    # el peso total de las no observadas se cuenta como 0 publicaciones
    wun = sum(N["neg_resto"][h] / nn[("neg_resto", h)] * v for h, v in n_unobs.items())
    k = np.array([x["pub"]["M14"] for x in resto], float)
    p = (w * k).sum() / (w.sum() + wun)
    ne = (w.sum() + wun) ** 2 / ((w ** 2).sum() + sum((N["neg_resto"][h] / nn[("neg_resto", h)]) ** 2 * v for h, v in n_unobs.items()))
    print(f"  {etiqueta}: neg_resto {p:.4f} Wilson {tuple(round(v,4) for v in wilson(p*ne, ne))} n_eff {ne:.0f}")
