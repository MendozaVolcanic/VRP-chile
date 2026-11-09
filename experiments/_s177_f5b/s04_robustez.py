# -*- coding: utf-8 -*-
"""s04: robustez de lo que dice s03.

Fenómeno: nuestro punto y la mancha de MIROVA son dos medidas del mismo píxel de satélite en una pasada; si el foco es fijo
(el cráter), la posición del píxel que lo contiene depende sólo de la geometría de visada de esa pasada (ángulo de barrido,
lado de la órbita). Entonces «la mancha cae donde cae nuestro punto, pasada a pasada» puede venir de (a) que ambos ven el mismo
píxel de ESA pasada (coincidencia de píxel) o (b) que ambos están en el cráter y la geometría de visada se parece. Las dos se
distinguen con un nulo que iguala la geometría: puntos nuestros de otras pasadas con zenit y azimut de visada parecidos.

Pre-registro (escrito antes de correr):
  A. Umbral de sin dato U en {100, 200, 400, 1000, 1500} px con C2: la posición de la mancha de Chillán no debe cambiar entre 200 y 1500
     (el histograma de componentes no tiene nada entre 200 y 2000 px). Se cuenta cuántos records cambian de celda.
  B. Control positivo de instrumento: desplazar nuestro punto k km (k = 0, 0,25, 0,5, 1, 1,5, 2, 3) en 8 direcciones; la fracción de «i»
     (C2p, mismo código lib177.clase) tiene que bajar de ~1 a ~0 al pasar la tolerancia + el radio de la mancha. Si no baja, la clase no
     puede detectar un foco desplazado.
  C. Nulo N3 con geometría igualada: otras pasadas del mismo volcán y sensor con |dif. zenit| <= 5 grados y |dif. azimut| <= 30 grados
     (zenit y azimut de sensor del record de Chillán de la base 752d348bc, copiado por V5B). Si el AUC se queda en ~0,5 con N3, lo que
     separa en N1 es la geometría de visada y no la identidad del foco de esa noche.
  D. Transiciones de clase F5b -> C1, F5b -> C2p y F5b -> C2_nc en Chillán (qué cambia por la máscara, qué por el control).
  E. MODIS de Chillán separado por régimen del detector (vía código MIROVA desde 2026-11-02 18:00 UTC).
Salida: salidas/s04_robustez.out.txt
"""
import collections, datetime as dt, json, os, sys
import numpy as np
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib177 as M
L = M.L
sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(1770)
V = {v["name"]: v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
S2 = json.load(open(os.path.join(HERE, "salidas", "s02_manchas.json"), encoding="utf-8"))
CH = "NevadosDeChillan"
ARCH = {CH: "ChillanNevadosde"}
refs = json.load(open(os.path.join(HERE, "orig", "p6_tif_referencia_out.json"), encoding="utf-8"))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
gr = {}


def grilla(vol, b):
    if (vol, b) not in gr:
        ref = refs[f"{ARCH.get(vol, vol)}|{b}"]["ref_sep"]
        g = L.grilla(os.path.join(TMP, "tif_ref", ARCH.get(vol, vol) + "_" + os.path.basename(ref["path"])))
        g["mc"] = (V[vol]["mirova_center_lat"], V[vol]["mirova_center_lon"])
        g["inner"] = L.mascara_inner(g, g["mc"], V[vol]["inner_radius_km"])
        g["celda_km"] = abs(g["transform"].e) * 111.0
        gr[(vol, b)] = g
    return gr[(vol, b)]


for o in S2:
    g = grilla(o["vol"], o["b"])
    o["MC2"] = M.Mancha(o["C2"], g, g["mc"])
    o["MC1"] = M.Mancha(o["C1"], g, g["mc"])
    o["MA"] = M.Mancha(o["A"], g, g["mc"])
    o["t"] = dt.datetime.strptime(o["dt"], "%Y-%m-%d %H:%M")
    o["pt"] = (o["our_lat"], o["our_lon"])
    o["dist"] = float(o["dist_tabla"]) if o["dist_tabla"] not in (None, "") else None
    o["estrato"] = (o["vol"], o["b"])


def c2p(o, punto=None):
    return M.clase(o["MC2"], punto or o["pt"], o["dist"], o["b"], o["celda_km"], "any", "cent", False)


# ---------------------------------------------------------------------------------------------------------------- A
print("== A. Umbral de «sin dato» (px) con C2: ¿cambia la mancha? ==")
base = {(o["vol"], o["sensor"], o["dt"]): o["C2"]["rc"] + [o["C2"]["px_principal"]] for o in S2}
for U in (100, 200, 400, 1000, 1500):
    camb, camb_ch = 0, 0
    for o in S2:
        g = grilla(o["vol"], o["b"])
        im = L.abrir_png(os.path.join(TMP, "png", o["png"].split("/")[-2] + "_" + os.path.basename(o["png"])))
        bb = L.bbox_marco(im, o["panel"])
        P = M.preparar(im, bb, g)
        s = M.seleccionar(P, g, "B", True, umbral=U)
        k = (o["vol"], o["sensor"], o["dt"])
        if s is None or s["rc"] + [s["px_principal"]] != base[k]:
            camb += 1
            camb_ch += o["vol"] == CH
    print(f"  U = {U:5d} px: records con otra celda o área de mancha que con U = 400: {camb} de {len(S2)} (Chillán {camb_ch})")

# ---------------------------------------------------------------------------------------------------------------- B
print("\n== B. Control positivo: desplazar nuestro punto k km (8 direcciones) y ver cuánto sigue siendo «i» (C2p) ==")
ks = (0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
print(f"{'estrato (n con control ok)':40s} " + " ".join(f"{k:>6.2f}" for k in ks) + "   km")
for nom, est in (("Chillán VIIRS 375", (CH, "VIIRS375")), ("Chillán VIIRS 750", (CH, "VIIRS750")), ("Chillán MODIS (sin validar)", (CH, "MODIS"))):
    sub = [o for o in S2 if o["estrato"] == est and c2p(o) != "iv"]
    fila = []
    for k in ks:
        fr = []
        for o in sub:
            for ang in range(0, 360, 45):
                dla = k * np.cos(np.radians(ang)) / 110.57
                dlo = k * np.sin(np.radians(ang)) / (111.32 * np.cos(np.radians(o["our_lat"])))
                fr.append(c2p(o, (o["our_lat"] + dla, o["our_lon"] + dlo)) == "i")
        fila.append(np.mean(fr))
    print(f"{nom + ' (' + str(len(sub)) + ')':40s} " + " ".join(f"{f:6.2f}" for f in fila) + f"   (tolerancia {L.TOL[est[1]]} km)")

# ---------------------------------------------------------------------------------------------------------------- C
print("\n== C. Nulo N3 con geometría de visada igualada (Chillán): otras pasadas con |dif zenit| <= 5 grados y |dif azimut| <= 30 grados ==")
d = json.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\chillan_base.json", encoding="utf-8"))
geo = {(r["sensor"], str(r["datetime_utc"])[:16]): (r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg")) for r in d["records"]}


def dazi(a, b):
    x = abs(a - b) % 360
    return min(x, 360 - x)


for nom, est in (("Chillán VIIRS 375", (CH, "VIIRS375")), ("Chillán VIIRS 750", (CH, "VIIRS750")), ("Chillán MODIS (sin validar)", (CH, "MODIS"))):
    sub = [o for o in S2 if o["estrato"] == est]
    for o in sub:
        o["zen"], o["azi"] = geo.get((o["sensor"], o["dt"]), (None, None))
    con_geo = [o for o in sub if o["zen"] is not None and o["azi"] is not None]
    print(f"{nom}: {len(con_geo)} de {len(sub)} con zenit y azimut")
    for etiq, fz, fa in (("N1 todas", 999, 999), ("N3 zenit +-5, azimut +-30", 5, 30), ("N3b zenit +-3, azimut +-15", 3, 15)):
        obs, nul, auc, dp, do_ = [], [], [], [], []
        for i, oi in enumerate(con_geo):
            if c2p(oi) == "iv":
                continue
            vec = [oj for j, oj in enumerate(con_geo) if j != i and abs(oj["zen"] - oi["zen"]) <= fz and dazi(oj["azi"], oi["azi"]) <= fa]
            if len(vec) < 2:
                continue
            obs.append(c2p(oi) == "i")
            nul.append(np.mean([c2p(oi, oj["pt"]) == "i" for oj in vec]))
            dprop = oi["MC2"].d_cent(*oi["pt"])
            dd = np.array([oi["MC2"].d_cent(*oj["pt"]) for oj in vec])
            auc.append(np.mean((dd > dprop + 1e-6) + 0.5 * (np.abs(dd - dprop) <= 1e-6)))
            dp.append(dprop)
            do_.append(dd.mean())
        n = len(obs)
        if n == 0:
            print(f"   {etiq:28s} sin datos")
            continue
        obs, nul, auc = np.array(obs, float), np.array(nul), np.array(auc)
        idx = rng.integers(0, n, size=(2000, n))
        print(f"   {etiq:28s} n={n:3d} obs {obs.mean():.3f} nulo {nul.mean():.3f} dif {obs.mean() - nul.mean():+.3f} "
              f"[{np.percentile(obs[idx].mean(1) - nul[idx].mean(1), 2.5):+.3f}, {np.percentile(obs[idx].mean(1) - nul[idx].mean(1), 97.5):+.3f}] | "
              f"AUC {auc.mean():.3f} [{np.percentile(auc[idx].mean(1), 2.5):.3f}, {np.percentile(auc[idx].mean(1), 97.5):.3f}] | d propia {np.mean(dp):.2f} km, d otras (igual geometría) {np.mean(do_):.2f} km")

# ---------------------------------------------------------------------------------------------------------------- D
print("\n== D. Transiciones de clase en Chillán (F5b guardada -> variante); 'iv' incluye los sin lámina ==")


def cl_var(o, v):
    if v == "C1":
        return M.clase(o["MC1"], o["pt"], o["dist"], o["b"], o["celda_km"], "cent", "cent", False)
    if v == "C2p":
        return c2p(o)
    if v == "C2_nc":
        return M.clase(o["MC2"], o["pt"], o["dist"], o["b"], o["celda_km"], "any", "cent", True)


for b in ("VIIRS375", "VIIRS750", "MODIS"):
    sub = [o for o in S2 if o["vol"] == CH and o["b"] == b]
    for v in ("C1", "C2p", "C2_nc"):
        tr = collections.Counter((o["claseF5b"].rstrip("?"), cl_var(o, v)) for o in sub)
        print(f"  Chillán {b:9s} F5b -> {v:6s}: " + ", ".join(f"{a}->{c}: {n}" for (a, c), n in sorted(tr.items())))
print("  Los 2 records de C2p que pasan de i a iii:")
for o in S2:
    if o["claseF5b"].rstrip("?") == "i" and c2p(o) == "iii":
        print("    ", o["vol"], o["sensor"], o["dt"], f"{float(o['vrp']):.2f} MW", "d_cent %.2f km, tol %.2f" % (o["MC2"].d_cent(*o["pt"]), L.TOL[o["b"]]), "celdas", o["MC2"].n_celdas, "comps", o["MC2"].n_comps, "F5b d_png_nuestro", o["F5b_lat"] and round(L.hav(o["F5b_lat"], o["F5b_lon"], *o["pt"]), 2))
print("  (iii) que quedan en C2p en Chillán:")
for o in S2:
    if o["vol"] == CH and c2p(o) == "iii":
        print("    ", o["sensor"], o["dt"], f"{float(o['vrp']):.2f} MW prot={o['prot']}", "d_cent %.2f km (tol %.2f) d_min %.2f; mancha %d celdas" % (o["MC2"].d_cent(*o["pt"]), L.TOL[o["b"]], o["MC2"].d_min(*o["pt"]), o["MC2"].n_celdas))

# ---------------------------------------------------------------------------------------------------------------- E
print("\n== E. MODIS de Chillán por régimen del detector (vía código MIROVA desde 2026-11-02 18:00 UTC; antes, K) ==")
corte = dt.datetime(2026, 11, 2, 18, 0)
sub = [o for o in S2 if o["vol"] == CH and o["b"] == "MODIS"]
for nom, f in (("antes (K)", lambda o: o["t"] < corte), ("desde la vía", lambda o: o["t"] >= corte)):
    s = [o for o in sub if f(o)]
    if not s:
        print(f"  {nom}: 0")
        continue
    dc = [o["MC2"].d_cent(*o["pt"]) for o in s]
    print(f"  {nom}: n={len(s)}; d(mancha, nuestro) mediana {np.median(dc):.2f} km, rango {min(dc):.2f} a {max(dc):.2f}; clases C2p: {dict(collections.Counter(c2p(o) for o in s))}")
