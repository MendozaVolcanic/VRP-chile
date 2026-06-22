#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S114 FRENTE B — recompute N-sigma RATIO forms (no el campo sigma crudo).

OBJETIVO ADVERSARIAL: encontrar UNA definicion de N-sigma (ratio sobre algun sigma
persistido) que separe FOCO REAL (Lascar far->summit noche-ALERTA) de A69 DIFUSO
(nevados far->summit RUTINA). Si ninguna separa, confirmarlo.

Variantes de N-sigma (todas per-record, mismo calculo para todos los vols del sensor):
  (a) (diag_nti_max - diag_nti_bg) / diag_nti_std   [sigma = NTI bg-ring std]
  (b) (diag_nti_max - diag_nti_bg) / diag_sd_dnti   [sigma = dNTI contextual std]
  (c) diag_mu_dnti / diag_sd_dnti                    [z del mean dNTI contextual]
  (d) (t_max_k - t_bg_k) / diag_sigma_bg_k          [N-sigma BT clasico]
  extra (e) (diag_nti_max - diag_mu_dnti?) ... no aplica (mu_dnti es del dNTI, no NTI)
  extra (f) (diag_nti_max - diag_nti_bg)            [ETI absoluto, sin normalizar — control]

AUC = Mann-Whitney U / (n_pos*n_neg) = P(POS > NEG). Separa fuerte si AUC>0.80 o <0.20.
"""
import json, csv, os, statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONS = os.path.join(HERE, "mirova_fresh", "cons.csv")
far = json.load(open(os.path.join(HERE, "parity_s114_result.json"), encoding="utf-8"))["far2summit"]

VOLS = {"Lascar": "Lascar", "Lastarria": "Lastarria", "Tupungatito": "Tupungatito",
        "PlanchonPeteroa": "PlanchonPeteroa", "NevadosDeChillan": "Nevados de Chillan",
        "Chaiten": "Chaiten", "Villarrica": "Villarrica", "Llaima": "Llaima",
        "Copahue": "Copahue", "Isluga": "Isluga", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
NEVADOS = ["Tupungatito", "NevadosDeChillan", "Villarrica", "Copahue", "Lastarria",
           "PlanchonPeteroa", "Llaima", "Isluga", "PuyehueCordonCaulle", "Chaiten"]

# estado MIROVA MODIS por noche
mir = defaultdict(lambda: {"a": 0, "r": 0})
for r in csv.DictReader(open(CONS, encoding="utf-8")):
    if r["Volcan"] in VOLS.values() and r["Sensor"] == "MODIS":
        k = (r["Volcan"], r["Fecha_Satelite_UTC"][:10])
        if r["Tipo_Registro"] == "ALERTA_TERMICA": mir[k]["a"] += 1
        elif r["Tipo_Registro"] == "RUTINA": mir[k]["r"] += 1

# index MODIS records por datetime_utc
recidx = {}
for vj in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vj + ".json"), encoding="utf-8"))
    ri = {}
    for rec in d["records"]:
        if rec.get("sensor", "").startswith("MODIS"):
            ri[rec.get("datetime_utc")] = rec
    recidx[vj] = ri


def fnum(x):
    try:
        v = float(x)
        if v != v:  # nan
            return None
        return v
    except (TypeError, ValueError):
        return None


def variants(rec):
    nti_max = fnum(rec.get("diag_nti_max"))
    nti_bg = fnum(rec.get("diag_nti_bg"))
    nti_std = fnum(rec.get("diag_nti_std"))
    sd_dnti = fnum(rec.get("diag_sd_dnti"))
    mu_dnti = fnum(rec.get("diag_mu_dnti"))
    t_max = fnum(rec.get("t_max_k"))
    t_bg = fnum(rec.get("t_bg_k"))
    sig_bt = fnum(rec.get("diag_sigma_bg_k"))
    out = {}
    # (a) N-sigma NTI sobre bg-ring std
    if nti_max is not None and nti_bg is not None and nti_std and nti_std > 0:
        out["a_nsig_nti_bgring"] = (nti_max - nti_bg) / nti_std
    # (b) (NTI_max - NTI_bg) / sd_dnti  (mezcla: numerador NTI-ring, denom dNTI ctx)
    if nti_max is not None and nti_bg is not None and sd_dnti and sd_dnti > 0:
        out["b_nsig_nti_over_sddnti"] = (nti_max - nti_bg) / sd_dnti
    # (c) z del mean dNTI contextual
    if mu_dnti is not None and sd_dnti and sd_dnti > 0:
        out["c_z_mudnti_over_sddnti"] = mu_dnti / sd_dnti
    # (d) N-sigma BT clasico
    if t_max is not None and t_bg is not None and sig_bt and sig_bt > 0:
        out["d_nsig_bt"] = (t_max - t_bg) / sig_bt
    # (f) control: ETI absoluto sin normalizar
    if nti_max is not None and nti_bg is not None:
        out["f_eti_abs_nti"] = nti_max - nti_bg
    # control BT: dT absoluto
    if t_max is not None and t_bg is not None:
        out["g_dT_abs"] = t_max - t_bg
    return out


POS, NEG = [], []          # task-spec: POS=Lascar far->summit ALERTA, NEG=nevados RUTINA
POS_ALL_LASCAR = []        # sanity: todos los Lascar far->summit MODIS
for x in far:
    if x["sensor"] != "MODIS":
        continue
    rec = recidx[x["vol"]].get(x["datetime"])
    if not rec:
        continue
    v = variants(rec)
    if not v:
        continue
    st_a = mir[(VOLS[x["vol"]], x["date"])]["a"]
    if x["vol"] == "Lascar":
        POS_ALL_LASCAR.append(v)
        if st_a:  # noche-ALERTA
            POS.append(v)
    elif x["vol"] in NEVADOS and st_a == 0:  # RUTINA (no ALERTA esa noche)
        NEG.append(v)


def auc(pos, neg, key):
    p = [r[key] for r in pos if key in r]
    n = [r[key] for r in neg if key in r]
    if len(p) < 3 or len(n) < 3:
        return None, len(p), len(n)
    wins = ties = 0
    for a in p:
        for b in n:
            if a > b:
                wins += 1
            elif a == b:
                ties += 1
    return (wins + 0.5 * ties) / (len(p) * len(n)), len(p), len(n)


KEYS = ["a_nsig_nti_bgring", "b_nsig_nti_over_sddnti", "c_z_mudnti_over_sddnti",
        "d_nsig_bt", "f_eti_abs_nti", "g_dT_abs"]

print("POS (Lascar far->summit, noche-ALERTA): n=%d" % len(POS))
print("POS_ALL (Lascar far->summit, todas):    n=%d" % len(POS_ALL_LASCAR))
print("NEG (nevados far->summit, RUTINA, A69):  n=%d" % len(NEG))
print()


def pctl(vals, q):
    if not vals:
        return None
    vals = sorted(vals)
    import math
    i = q / 100.0 * (len(vals) - 1)
    lo = int(math.floor(i)); hi = int(math.ceil(i))
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (i - lo)


out_variants = []
print("%-26s %6s  %9s %9s %9s  %s" % ("VARIANT", "AUC", "med_POS", "p90_POS", "med_NEG", "separa?"))
print("-" * 84)
for k in KEYS:
    a, npp, nnn = auc(POS, NEG, k)
    if a is None:
        print("%-26s  (insuficiente: nP=%d nN=%d)" % (k, npp, nnn))
        continue
    pvals = [r[k] for r in POS if k in r]
    nvals = [r[k] for r in NEG if k in r]
    mp = statistics.median(pvals); mn = statistics.median(nvals)
    p90 = pctl(pvals, 90)
    sep = (a > 0.80 or a < 0.20)
    flag = "  <== SEPARA" if sep else ("  ~debil" if abs(a - 0.5) > 0.15 else "")
    print("%-26s %.3f  %9.4f %9.4f %9.4f%s" % (k, a, mp, p90, mn, flag))
    out_variants.append({
        "name": k, "auc": round(a, 4),
        "lascar_alerta_med": round(mp, 4), "lascar_alerta_p90": round(p90, 4),
        "nevados_rutina_med": round(mn, 4),
        "n_pos": npp, "n_neg": nnn, "separates": bool(sep),
    })

# best by |AUC-0.5|
best = max(out_variants, key=lambda d: abs(d["auc"] - 0.5)) if out_variants else None
any_sep = any(d["separates"] for d in out_variants)
print()
print("ANY SEPARATES (AUC>0.80 or <0.20):", any_sep)
print("BEST AUC (max |AUC-0.5|):", best["name"] if best else None, best["auc"] if best else None)

json.dump({"variants": out_variants, "any_separates": any_sep,
           "best": best, "n_pos": len(POS), "n_neg": len(NEG)},
          open(os.path.join(HERE, "sigma_ratio_sweep_result.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
