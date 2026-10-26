# -*- coding: utf-8 -*-
"""Verificador S162 V375: recuento independiente desde los JSON del runner (sin brazos.py ni evaluar.py).
Predicado propio: publica = npix>0 y vrp>0 y el pixel alertado MAS CERCANO a (X0,Y0) esta a <= inner_radius_km.
Uso: python -I indep_recuento.py"""
import collections, glob, json, math, re, sys, io
from pathlib import Path
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864")
A162 = Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866")
A159 = Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
EXCL = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")

vy = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
vy = vy["volcanoes"] if isinstance(vy, dict) else vy
inner = {v["name"]: v.get("inner_radius_km") for v in vy}

o162 = json.loads((RAIZ / "experiments/_s162_v375/objetivos_v375_bc.json").read_text(encoding="utf-8"))
obj = {o["id"]: dict(o) for o in o162["pasadas"]}
for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
    if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in EXCL:
        assert o["id"] not in obj, ("id repetido entre lotes", o["id"])
        obj[o["id"]] = {**o, "lote": "S159", "estrato": f"{o['volcan']}|{o['estrato_z']}"}
print("objetivos", len(obj), collections.Counter((o["lote"], o["clase"]) for o in obj.values()))

# duplicados volcan+hora entre lotes
vh = collections.Counter((o["volcan"], o["hora_utc"]) for o in obj.values())
print("volcan+hora repetidos:", [k for k, v in vh.items() if v > 1])
gr = collections.Counter(o.get("granule") for o in obj.values())
print("granulos compartidos entre objetivos (volcan distinto, mismo granulo):", sum(1 for v in gr.values() if v > 1))

def leer(art, patron="resultados_VIIRS375_*.json"):
    res, dup = {}, []
    for f in sorted(Path(art).rglob(patron)):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["id"] in res:
                dup.append((r["id"], res[r["id"]]["estado"], r["estado"], str(f)))
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    return res, dup

r162, d162 = leer(A162)
r159, d159 = leer(A159)
print("resultados S162", len(r162), "dup", d162[:5], "| S159", len(r159), "dup", d159[:5])
res = {}
for i, o in obj.items():
    res[i] = (r162 if o["lote"] == "S162" else r159).get(i)
print("estados:", collections.Counter((obj[i]["lote"], (r or {}).get("estado")) for i, r in res.items()))
print("ids de resultados S162 que no son objetivo S162:", [i for i in r162 if i not in obj or obj[i]["lote"] != "S162"][:10])

def publica(p, vol):
    if not p or not p.get("npix") or not p.get("vrp_mw") or p["vrp_mw"] <= 0:
        return False
    return min(q[3] for q in p["pixeles"]) <= inner[vol] + 1e-12

ok = [i for i, r in res.items() if r and r.get("estado") == "ok" and r.get("port")]
# nombres de brazo en S159
b159 = {"M14": "fisica", "SENS": "sensible", "PIX7": "pixel"}
def arm(i, b):
    o, r = obj[i], res[i]
    nm = b if o["lote"] == "S162" else b159.get(b)
    if nm is None:
        return None
    return publica(r["port"].get(nm), o["volcan"])

# pesos: N / n_ok por (clase, estrato)
N = {c: {h: v["N"] for h, v in est.items()} for c, est in o162["meta"]["estratos"].items()}
nok = collections.Counter((obj[i]["clase"], obj[i]["estrato"]) for i in ok)
W = {k: N[k[0]][k[1]] / v for k, v in nok.items()}
sin_peso = [(c, h) for c in N for h in N[c] if N[c][h] and not nok.get((c, h))]
print("estratos sin pasada ok:", sin_peso)

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)

out = {}
for b in ("M14", "C13"):
    pub = {i: arm(i, b) for i in ok}
    if b == "C13":
        pub = {i: v for i, v in pub.items() if v is not None}
    print(f"\n=== brazo {b}: pasadas con valor {len(pub)}")
    for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"):
        for lote in ("S159", "S162", "ambos"):
            ids = [i for i in pub if obj[i]["clase"] == c and (lote == "ambos" or obj[i]["lote"] == lote)]
            if not ids:
                continue
            k = sum(pub[i] for i in ids)
            print(f"  {c:9s} {lote:5s}: publica {k} de {len(ids)}")
    # neg_resto union
    ids = [i for i in pub if obj[i]["clase"] == "neg_resto"]
    w = [W[(obj[i]["clase"], obj[i]["estrato"])] for i in ids]
    k = [pub[i] for i in ids]
    p = sum(wi * ki for wi, ki in zip(w, k)) / sum(w)
    ne = sum(w) ** 2 / sum(x * x for x in w)
    print(f"  neg_resto union: {sum(k)} de {len(ids)}; ponderado {p:.5f}; n_eff {ne:.1f}; Wilson {wilson(p*ne, ne)}")
    # solo S162 con pesos reponderados dentro del lote
    ids2 = [i for i in ids if obj[i]["lote"] == "S162"]
    n2 = collections.Counter(obj[i]["estrato"] for i in ids2)
    w2 = [N["neg_resto"][obj[i]["estrato"]] / n2[obj[i]["estrato"]] for i in ids2]
    k2 = [pub[i] for i in ids2]
    p2 = sum(wi * ki for wi, ki in zip(w2, k2)) / sum(w2)
    ne2 = sum(w2) ** 2 / sum(x * x for x in w2)
    print(f"  neg_resto S162 solo: {sum(k2)} de {len(ids2)}; ponderado {p2:.5f}; n_eff {ne2:.1f}; Wilson {wilson(p2*ne2, ne2)}")
    out[b] = pub

# lista de los 4 neg_resto que M14 publica
print("\nneg_resto que M14 publica:")
for i in ok:
    o = obj[i]
    if o["clase"] == "neg_resto" and out["M14"][i]:
        p = res[i]["port"]["M14" if o["lote"] == "S162" else "fisica"]
        print("  ", i, o["lote"], o["volcan"], o["hora_utc"], "npix", p["npix"], "vrp", p["vrp_mw"], "dmin", min(q[3] for q in p["pixeles"]), "inner", inner[o["volcan"]])
print("neg_resto que C13 publica y M14 no, o al reves:")
for i in ok:
    o = obj[i]
    if o["lote"] == "S162" and o["clase"] == "neg_resto" and out["M14"][i] != out["C13"][i]:
        print("  ", i, o["volcan"], o["hora_utc"], "M14", out["M14"][i], "C13", out["C13"][i])

# por clase, publicacion de K (pub_prod) y de C13 vs M14 en neg_pub etc.
print("\nK (pub_prod) por clase en ok:", {c: sum(obj[i]["pub_prod"] for i in ok if obj[i]["clase"] == c) for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto")})
json.dump({"ok": len(ok)}, open(Path(__file__).with_name("indep_recuento.json"), "w"))
