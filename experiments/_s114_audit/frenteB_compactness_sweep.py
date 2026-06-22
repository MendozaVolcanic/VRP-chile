#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 FRENTE B (adversarial fresh) — buscar transformacion MISSION-pura que separe
FOCO REAL (Lascar far->summit ALERTA, desierto) de A69 DIFUSO (nevados far->summit RUTINA).

NOVEDAD vs barrido previo (discriminant_sweep.py): explota anomaly_pixels (per-pixel
lat/lon/bt_k/dist_km/vrp_mw) que el barrido escalar NUNCA toco. Deriva:
  - compacidad espacial del cluster (spread de lat/lon, area envolvente, densidad)
  - distribucion BT per-pixel (peak/cluster ratio, sd, skew)
  - relaciones pico/cluster de VRP (Gini, top1/sum)
  - contrastes NTI normalizados nuevos (sin cross-sensor)
  - relaciones entre paths (fraccion dnti_ctx, recapture/first_pass)
  - ROI percentil vs t_bg / t_max
Todas las features son PER-RECORD, per-sensor uniforme (MODIS), NO cross-sensor, NO per-vol.

Default adversarial: si NINGUNA AUC MISSION-pura > 0.80 -> 'no hay fix'.
v375_coval_mag se incluye SOLO como referencia (cross-sensor, MISSION lo prohibe -> NO valido).
"""
import json, csv, os, math, statistics, itertools
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
far = json.load(open(os.path.join(HERE, "parity_s114_result.json"), encoding="utf-8"))["far2summit"]

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "NevadosDeChillan": 5, "Chaiten": 5, "Villarrica": 5, "Llaima": 5,
         "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
NEVADOS = ["Tupungatito", "NevadosDeChillan", "Villarrica", "Copahue", "Lastarria",
           "PlanchonPeteroa", "Llaima", "Isluga", "PuyehueCordonCaulle", "Chaiten"]

# estado MIROVA MODIS por noche
mir = defaultdict(lambda: {"a": 0, "r": 0})
for r in csv.DictReader(open(CONS, encoding="utf-8")):
    if r["Volcan"] in VOLS.values() and r["Sensor"] == "MODIS":
        k = (r["Volcan"], r["Fecha_Satelite_UTC"][:10])
        if r["Tipo_Registro"] == "ALERTA_TERMICA": mir[k]["a"] += 1
        elif r["Tipo_Registro"] == "RUTINA": mir[k]["r"] += 1

# index records + VIIRS375 magnitud por dia (cross-sensor, solo referencia)
recidx, v375mag = {}, defaultdict(dict)
for vj in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vj + ".json"), encoding="utf-8"))
    inner = INNER[vj]; ri = {}
    for rec in d["records"]:
        s = rec.get("sensor", "")
        if s.startswith("MODIS"):
            ri[rec.get("datetime_utc")] = rec
        elif s.startswith("VIIRS") and not s.endswith("_750"):
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0; cd = pc.get("centroid_dist_km")
            if 0 < vrp <= 50000 and cd is not None and cd <= inner:
                dt = rec.get("datetime_utc")
                if dt: v375mag[vj][dt[:10]] = max(v375mag[vj].get(dt[:10], 0), vrp)
    recidx[vj] = ri


def haversine_km(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1); dl = math.radians(lo2 - lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def gini(vals):
    vals = sorted(v for v in vals if v is not None and v >= 0)
    n = len(vals)
    if n == 0 or sum(vals) == 0: return None
    cum = 0.0
    for i, v in enumerate(vals):
        cum += (2*(i+1) - n - 1) * v
    return cum / (n * sum(vals))


def extract(rec, vj, date):
    """Deriva TODAS las features per-record. Solo MODIS, sin cross-sensor (excepto la ref)."""
    f = {}
    # --- escalares persistidos (replica barrido previo para baseline) ---
    for k in ["diag_nti_max", "diag_nti_bg", "diag_nti_std", "diag_sigma_bg_k",
              "diag_roi_p95_k", "diag_t_max_dist_km", "diag_n_first_pass_summit",
              "diag_n_first_pass_pixels", "diag_n_dnti_ctx_path", "diag_n_eti_path",
              "diag_n_nti_path", "diag_n_bt_path", "diag_n_second_pass_recapture",
              "diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti",
              "t_max_k", "t_bg_k", "n_anomalous_pixels", "n_hotspots_clustered"]:
        f[k] = rec.get(k)
    tmax, tbg = rec.get("t_max_k"), rec.get("t_bg_k")
    f["dT"] = (tmax - tbg) if (tmax is not None and tbg is not None) else None
    pc = rec.get("primary_cluster") or {}
    f["pc_n_pixels"] = pc.get("n_pixels")
    f["pc_vrp"] = pc.get("vrp_mw")

    # --- NTI contrastes normalizados nuevos (sin cross-sensor) ---
    nmax, nbg, nstd = rec.get("diag_nti_max"), rec.get("diag_nti_bg"), rec.get("diag_nti_std")
    if nmax is not None and nbg is not None:
        f["nti_contrast"] = nmax - nbg                       # excedente NTI absoluto
        if nstd not in (None, 0):
            f["nti_nsigma"] = (nmax - nbg) / nstd            # ya en barrido (N-sigma)
        # NTI max sobre piso fisico: lava acerca NTI a 0 desde piso -1
        f["nti_max_floor"] = nmax + 1.0                      # 0 = piso puro nieve
        if nbg != 0:
            f["nti_ratio"] = nmax / nbg                      # cociente (ambos<0)
    # ETI/dNTI mu vs sd (consistencia del campo contextual)
    mdn, sdn = rec.get("diag_mu_dnti"), rec.get("diag_sd_dnti")
    if mdn is not None and sdn not in (None, 0):
        f["dnti_mu_over_sd"] = mdn / sdn
    mde, sde = rec.get("diag_mu_deti"), rec.get("diag_sd_deti")
    if mde is not None and sde not in (None, 0):
        f["deti_mu_over_sd"] = mde / sde

    # --- relaciones entre paths (fracciones, sin cross-sensor) ---
    nfp = rec.get("diag_n_first_pass_pixels")
    fps = rec.get("diag_n_first_pass_summit")
    nrec = rec.get("diag_n_second_pass_recapture")
    nctx = rec.get("diag_n_dnti_ctx_path")
    nbt = rec.get("diag_n_bt_path"); neti = rec.get("diag_n_eti_path"); nnti = rec.get("diag_n_nti_path")
    if nfp not in (None, 0):
        if fps is not None: f["frac_summit_of_fp"] = fps / nfp
        if nctx is not None: f["frac_ctx_of_fp"] = nctx / nfp
    if fps not in (None, 0) and nrec is not None:
        f["recapture_over_summit"] = nrec / fps
    # cuantos paths "fuertes" (BT/ETI/NTI absolutos) disparan vs solo ctx
    strong = sum(x for x in [nbt, neti, nnti] if x) if any(v is not None for v in [nbt, neti, nnti]) else None
    f["n_strong_paths_px"] = strong
    if nctx not in (None, 0) and strong is not None:
        f["strong_over_ctx"] = strong / nctx

    # --- ROI percentil relaciones (sin cross-sensor) ---
    roi95 = rec.get("diag_roi_p95_k")
    if roi95 is not None and tbg is not None:
        f["roi95_minus_tbg"] = roi95 - tbg                  # excedente del 95% del ROI
    if roi95 is not None and tmax is not None:
        f["tmax_minus_roi95"] = tmax - roi95                # cuanto sobresale el pico del 95% (foco discreto)
    sbg = rec.get("diag_sigma_bg_k")
    if tmax is not None and tbg is not None and sbg not in (None, 0):
        f["dT_nsigma_bt"] = (tmax - tbg) / sbg              # N-sigma en BT (no NTI)
    if roi95 is not None and tbg is not None and sbg not in (None, 0):
        f["roi95_nsigma"] = (roi95 - tbg) / sbg

    # --- PER-PIXEL del cluster summit: compacidad + distribucion ---
    # construir el subconjunto de anomaly_pixels que cae en el inner_radius (cluster summit)
    inner = INNER[vj]
    ap = rec.get("anomaly_pixels") or []
    summit_px = [p for p in ap if p.get("dist_km") is not None and p["dist_km"] <= inner]
    # tambien todos los pixels (scene-wide) para densidad relativa
    f["n_summit_px"] = len(summit_px)
    if len(ap) > 0:
        f["frac_px_in_inner"] = len(summit_px) / len(ap)    # difuso=disperso; foco=concentrado dentro
    if len(summit_px) >= 1:
        bts = [p["bt_k"] for p in summit_px if p.get("bt_k") is not None]
        vrps = [p["vrp_mw"] for p in summit_px if p.get("vrp_mw") is not None]
        if bts:
            f["px_bt_max"] = max(bts)
            f["px_bt_max_minus_tbg"] = (max(bts) - tbg) if tbg is not None else None
            if len(bts) >= 2:
                f["px_bt_sd"] = statistics.pstdev(bts)
                f["px_bt_range"] = max(bts) - min(bts)
        if vrps and sum(vrps) > 0:
            f["px_vrp_top1_frac"] = max(vrps) / sum(vrps)   # foco=1 pixel domina; difuso=repartido
            f["px_vrp_gini"] = gini(vrps)
            f["px_vrp_sum"] = sum(vrps)
        # compacidad espacial: radio de dispersion del cluster (km)
        if len(summit_px) >= 2:
            clat = statistics.mean(p["lat"] for p in summit_px)
            clon = statistics.mean(p["lon"] for p in summit_px)
            spread = [haversine_km(p["lat"], p["lon"], clat, clon) for p in summit_px]
            f["px_spread_km"] = statistics.mean(spread)     # difuso=grande; foco=chico
            f["px_spread_max_km"] = max(spread)
            if f.get("px_vrp_sum"):
                # densidad VRP por km^2 aprox (energia concentrada vs dispersa)
                area = math.pi * (max(spread) + 0.5) ** 2
                f["px_vrp_density"] = f["px_vrp_sum"] / area
            # "compacidad" = pixels / area envolvente (foco=denso)
            area_env = math.pi * (max(spread) + 0.5) ** 2
            f["px_compactness"] = len(summit_px) / area_env

    # --- referencia cross-sensor (MISSION lo PROHIBE, solo control) ---
    f["REF_v375_coval_mag"] = v375mag[vj].get(date, 0.0)
    return f


POS, NEG = [], []
for x in far:
    if x["sensor"] != "MODIS": continue
    rec = recidx[x["vol"]].get(x["datetime"])
    if not rec: continue
    feats = extract(rec, x["vol"], x["date"])
    st = "ALERTA" if mir[(VOLS[x["vol"]], x["date"])]["a"] else "RUTINA"
    if x["vol"] == "Lascar":
        POS.append(feats)
    elif x["vol"] in NEVADOS and st == "RUTINA":
        NEG.append(feats)

print("POS (Lascar far->summit, foco real):  n=%d" % len(POS))
print("NEG (nevados RUTINA far->summit, A69): n=%d" % len(NEG))
print()


def auc(pos, neg, key):
    p = [r[key] for r in pos if r.get(key) is not None]
    n = [r[key] for r in neg if r.get(key) is not None]
    if len(p) < 5 or len(n) < 30: return None
    wins = ties = 0
    for a in p:
        for b in n:
            if a > b: wins += 1
            elif a == b: ties += 1
    a_raw = (wins + 0.5 * ties) / (len(p) * len(n))
    return a_raw, len(p), len(n)


# todas las features derivadas
all_keys = set()
for r in POS + NEG:
    all_keys.update(r.keys())
all_keys = sorted(all_keys)

results = []
for k in all_keys:
    out = auc(POS, NEG, k)
    if out is None: continue
    a, np_, nn_ = out
    power = abs(a - 0.5)
    is_ref = k.startswith("REF_")
    results.append((power, a, k, np_, nn_, is_ref))

results.sort(reverse=True)
print("%-24s %6s %6s %6s %s" % ("FEATURE", "AUC", "nPOS", "nNEG", "poder |AUC-.5|"))
print("-" * 78)
for power, a, k, np_, nn_, is_ref in results:
    tag = ""
    if is_ref: tag = "  [REF cross-sensor: MISSION PROHIBE]"
    elif power >= 0.30: tag = "  <== SEPARA (MISSION-puro)"
    elif power >= 0.15: tag = "  ~ debil"
    print("%-24s %.3f  %4d   %4d   %.3f%s" % (k, a, np_, nn_, power, tag))

# === pares: ratios/diferencias entre las top features escalares ===
print("\n=== TOP PARES (ratio/diff de features con mas poder individual) ===")
strong_keys = [k for power, a, k, np_, nn_, is_ref in results if not is_ref and power >= 0.10][:10]


def pair_feature(r, ka, kb, op):
    va, vb = r.get(ka), r.get(kb)
    if va is None or vb is None: return None
    if op == "div":
        if vb == 0: return None
        return va / vb
    if op == "sub": return va - vb
    if op == "mul": return va * vb
    return None


pair_results = []
for ka, kb in itertools.combinations(strong_keys, 2):
    for op in ["div", "sub", "mul"]:
        pf_pos = [pair_feature(r, ka, kb, op) for r in POS]
        pf_neg = [pair_feature(r, ka, kb, op) for r in NEG]
        pp = [v for v in pf_pos if v is not None]
        nn = [v for v in pf_neg if v is not None]
        if len(pp) < 5 or len(nn) < 30: continue
        wins = ties = 0
        for x in pp:
            for y in nn:
                if x > y: wins += 1
                elif x == y: ties += 1
        a = (wins + 0.5*ties)/(len(pp)*len(nn))
        pair_results.append((abs(a-0.5), a, "%s_%s_%s" % (ka, op, kb)))
pair_results.sort(reverse=True)
print("%-50s %6s %s" % ("PAIR FEATURE", "AUC", "poder"))
print("-" * 70)
for power, a, name in pair_results[:15]:
    tag = "  <== SEPARA" if power >= 0.30 else ""
    print("%-50s %.3f  %.3f%s" % (name, a, power, tag))

# resumen veredicto
best_mp = max((r for r in results if not r[5]), key=lambda r: r[0], default=None)
best_pair = pair_results[0] if pair_results else None
print("\n=== VEREDICTO ===")
if best_mp:
    print("Mejor single MISSION-puro: %s AUC=%.3f poder=%.3f" % (best_mp[2], best_mp[1], best_mp[0]))
if best_pair:
    print("Mejor par MISSION-puro:    %s AUC=%.3f poder=%.3f" % (best_pair[2], best_pair[1], best_pair[0]))
ref = next((r for r in results if r[5]), None)
if ref:
    print("Referencia cross-sensor (PROHIBIDA): %s AUC=%.3f" % (ref[2], ref[1]))
sep = best_mp and best_mp[0] >= 0.30 or (best_pair and best_pair[0] >= 0.30)
print("ANY_SEPARATES (AUC>=0.80 MISSION-puro):", bool(sep))
