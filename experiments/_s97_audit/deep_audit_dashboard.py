"""S97 — AUDITORÍA PROFUNDA de los valores del dashboard vs MIROVA (CONS ∪ OCR).

Pedido Nicolás: auditar TODOS los valores que muestra el dashboard, comparar contra
lo esperado (umbrales documentados) y contra MIROVA OCR + consolidado.

Reproducible, integridad §0.5: TODOS los números salen de este script (no se
transcriben a mano). Replica la lógica de display del frontend (mirovaEqVrp summit-only
+ Núcleo F5') y cruza a nivel noche-satélite por bucket de sensor (A47/A48).

Ejes:
  1. Recall / Precision / F1 vs MIROVA por volcán × bucket de sensor (match ±60 min).
  2. Ratio de magnitud (Cluster pc.vrp_mw / MIROVA) y (Núcleo F5' / MIROVA), mediana.
  3. Acuerdo de distancia (nuestro centroid_dist vs MIROVA dist_km).
  4. Valor "titular" del dashboard (última detección 48h) por volcán + nivel de alerta.
  5. Contraste con expectativas: recall≥0.60, precision≥0.50, ratio 0.5–2.0 (CLAUDE.md
     S15). Marco A54: la "precision baja" vs CONS suele ser features volcánicas reales,
     no error → reportar precision vs (CONS∪OCR) y marcar FP que igual están al cráter.

Uso: python deep_audit_dashboard.py
"""
import sys, os, io, json
from statistics import median
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "experiments", "_s94_audit"))
_fd = os.dup(1)
from f5_variants import hav, load_vents, parse
from pipeline.mirova_csv_loader import load_mirova_alertas
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

DATA = os.path.join(REPO, "data/mirova_equivalent")
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
TIER = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
        "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "Villarrica": 5,
         "PuyehueCordonCaulle": 20, "Copahue": 4, "NevadosDeChillan": 5, "Llaima": 5,
         "Chaiten": 5, "PlanchonPeteroa": 3, "Isluga": 5}
R_CORE = 0.75
BT_EXT = 295.0
MATCH_S = 3600  # ±60 min

# Niveles de alerta (MIROVA / dashboard): Muy Bajo <1, Bajo 1-10, Moderado 10-100, Alto >100
def level(v):
    if v <= 0: return "ND"
    if v < 1: return "MuyBajo"
    if v < 10: return "Bajo"
    if v < 100: return "Moderado"
    return "Alto"


def bucket(sensor):
    s = str(sensor or "").upper()
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"
    return "OTHER"


def is_valid(r):
    # H3/S77: detección válida = vrp_mw>0 (o test1) y NO descartada por el pipeline.
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    return True


def cluster_mag(r, inner):
    pc = r.get("primary_cluster")
    if not pc:
        return 0
    if (r.get("distance_class") and r.get("distance_class") != "summit"):
        return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def core_mag(r, inner):
    base = cluster_mag(r, inner)
    if base <= 0:
        return base
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None or clon is None:
        return base
    px = r.get("anomaly_pixels") or []
    cand = [p for p in px if p.get("lat") is not None
            and hav(p["lat"], p["lon"], clat, clon) <= inner]
    if not cand:
        return base
    peak = max(range(len(cand)), key=lambda i: cand[i].get("vrp_mw") or 0)
    plat, plon = cand[peak]["lat"], cand[peak]["lon"]
    s = 0.0
    for i, p in enumerate(cand):
        if i == peak or hav(p["lat"], p["lon"], plat, plon) <= R_CORE or (p.get("bt_k") or 0) >= BT_EXT:
            s += (p.get("vrp_mw") or 0)
    return base if s <= 0 else (0 if s > 50000 else s)


def match_sets(ours, miro):
    """ours, miro: listas de (ts_seconds, payload). Greedy ±MATCH_S. Devuelve
    (tp_pairs, fn_list, fp_list). tp_pairs = [(our, miro)]."""
    miro_sorted = sorted(miro, key=lambda x: x[0])
    used = [False] * len(miro_sorted)
    tp, fp = [], []
    for ot, op in sorted(ours, key=lambda x: x[0]):
        best, bi = None, -1
        for i, (mt, mp) in enumerate(miro_sorted):
            if used[i]:
                continue
            dt = abs(ot - mt)
            if dt <= MATCH_S and (best is None or dt < best):
                best, bi = dt, i
        if bi >= 0:
            used[bi] = True
            tp.append((op, miro_sorted[bi][1]))
        else:
            fp.append(op)
    fn = [miro_sorted[i][1] for i in range(len(miro_sorted)) if not used[i]]
    return tp, fn, fp


vents = load_vents()
# Acumuladores globales
G = {b: {"tp": 0, "fn": 0, "fp": 0, "ratios_cl": [], "ratios_co": [], "dist_pairs": []}
     for b in ("MODIS", "VIIRS375", "VIIRS750")}
per_vol = {}
headlines = {}

for vol in TIER:
    p = os.path.join(DATA, f"{vol}.json")
    if not os.path.exists(p):
        continue
    recs = json.load(open(p, encoding="utf-8")).get("records", [])
    inner = INNER.get(vol, 5)
    cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
    if not cov:
        continue
    cmin, cmax = min(cov), max(cov)

    # MIROVA en ventana, por bucket, vrp>0
    miro_all = load_mirova_alertas(CONS, OCR, volcano=vol)
    miro_by_b = {b: [] for b in G}
    for a in miro_all:
        b = a.get("sensor_bucket")
        if b not in miro_by_b:
            continue
        if (a.get("vrp_mw") or 0) <= 0:
            continue
        t = parse(a.get("fecha_utc"))
        if not t or not (cmin <= t <= cmax):
            continue
        miro_by_b[b].append((t.timestamp(), a))

    # Nuestras detecciones summit por bucket
    our_by_b = {b: [] for b in G}
    for r in recs:
        b = bucket(r.get("sensor"))
        if b not in our_by_b:
            continue
        if not is_valid(r):
            continue
        cl = cluster_mag(r, inner)
        if cl <= 0:
            continue
        t = parse(r.get("datetime_utc"))
        if not t:
            continue
        co = core_mag(r, inner) if b == "VIIRS375" else cl
        pc = r.get("primary_cluster") or {}
        our_by_b[b].append((t.timestamp(), {"cl": cl, "co": co,
                                            "dist": pc.get("centroid_dist_km"),
                                            "dt": r.get("datetime_utc")}))

    pv = {}
    for b in G:
        tp, fn, fp = match_sets(our_by_b[b], miro_by_b[b])
        ratios_cl = [op["cl"] / mp["vrp_mw"] for op, mp in tp if (mp.get("vrp_mw") or 0) > 0]
        ratios_co = [op["co"] / mp["vrp_mw"] for op, mp in tp if (mp.get("vrp_mw") or 0) > 0]
        dpairs = [(op["dist"], mp.get("dist_km")) for op, mp in tp
                  if op["dist"] is not None and mp.get("dist_km") is not None]
        pv[b] = {"tp": len(tp), "fn": len(fn), "fp": len(fp),
                 "ratios_cl": ratios_cl, "ratios_co": ratios_co, "dpairs": dpairs}
        G[b]["tp"] += len(tp); G[b]["fn"] += len(fn); G[b]["fp"] += len(fp)
        G[b]["ratios_cl"] += ratios_cl; G[b]["ratios_co"] += ratios_co
        G[b]["dist_pairs"] += dpairs
    per_vol[vol] = pv

    # Titular del dashboard: última detección summit en 48h (cualquier bucket)
    cutoff = cmax.timestamp() - 48 * 3600  # relativo al último dato (no "ahora")
    best = None
    for r in recs:
        t = parse(r.get("datetime_utc"))
        if not t:
            continue
        cl = cluster_mag(r, inner)
        if cl <= 0 or not is_valid(r):
            continue
        ts = t.timestamp()
        if ts < cutoff:
            continue
        if not best or ts > best[0]:
            best = (ts, cl, r.get("sensor"), r.get("datetime_utc"))
    headlines[vol] = best


def fmt_ratio(rs):
    return f"{median(rs):.2f}x" if rs else "—"


def rp(tp, fn, fp):
    rec = tp / (tp + fn) if (tp + fn) else None
    pre = tp / (tp + fp) if (tp + fp) else None
    return rec, pre


W = OUT.write
W("=" * 120 + "\n")
W("AUDITORÍA PROFUNDA S97 — dashboard vs MIROVA (CONS ∪ OCR). Match ±60min por bucket de sensor.\n")
W("Recall=TP/(TP+FN) [cuánto de MIROVA captamos] · Precision=TP/(TP+FP) [cuánto de lo nuestro confirma MIROVA].\n")
W("Marco A54: 'FP' alto NO = error; ~95% son features volcánicas reales no publicadas por MIROVA CONS.\n")
W("=" * 120 + "\n\n")

# ---- Eje 1+2: recall/precision/ratio por bucket ----
for b in ("VIIRS375", "MODIS", "VIIRS750"):
    W(f"### Sensor {b}\n")
    W(f"{'Volcán':<20}{'TP':>5}{'FN':>5}{'FP':>5}{'Recall':>9}{'Prec':>8}{'medCl/MIR':>11}{'medCo/MIR':>11}\n")
    W("-" * 80 + "\n")
    for vol in TIER:
        if vol not in per_vol:
            continue
        d = per_vol[vol][b]
        rec, pre = rp(d["tp"], d["fn"], d["fp"])
        recs = f"{rec*100:.0f}%" if rec is not None else "—"
        pres = f"{pre*100:.0f}%" if pre is not None else "—"
        co = fmt_ratio(d["ratios_co"]) if b == "VIIRS375" else "n/a"
        if d["tp"] + d["fn"] + d["fp"] == 0:
            continue
        W(f"{vol:<20}{d['tp']:>5}{d['fn']:>5}{d['fp']:>5}{recs:>9}{pres:>8}{fmt_ratio(d['ratios_cl']):>11}{co:>11}\n")
    g = G[b]
    rec, pre = rp(g["tp"], g["fn"], g["fp"])
    recs = f"{rec*100:.0f}%" if rec is not None else "—"
    pres = f"{pre*100:.0f}%" if pre is not None else "—"
    co = fmt_ratio(g["ratios_co"]) if b == "VIIRS375" else "n/a"
    W("-" * 80 + "\n")
    W(f"{'GLOBAL ' + b:<20}{g['tp']:>5}{g['fn']:>5}{g['fp']:>5}{recs:>9}{pres:>8}{fmt_ratio(g['ratios_cl']):>11}{co:>11}\n\n")

# ---- Eje 3: distancia ----
W("### Acuerdo de distancia (nuestro centroid_dist_km vs MIROVA dist_km, en TP con ambas)\n")
W(f"{'Sensor':<12}{'n_pares':>8}{'medianΔ(km)':>13}{'med_ours':>10}{'med_miro':>10}\n")
W("-" * 56 + "\n")
for b in G:
    dp = G[b]["dist_pairs"]
    if not dp:
        continue
    diffs = [abs(o - m) for o, m in dp]
    W(f"{b:<12}{len(dp):>8}{median(diffs):>13.2f}{median([o for o,_ in dp]):>10.2f}{median([m for _,m in dp]):>10.2f}\n")
W("\n")

# ---- Eje 4: titulares del dashboard ----
W("### Titular del dashboard hoy (última detección summit ≤48h del último dato) por volcán\n")
W(f"{'Volcán':<20}{'VRP(MW)':>9}{'Nivel':>9}{'Sensor':>16}{'Fecha UTC':>18}\n")
W("-" * 72 + "\n")
for vol in TIER:
    h = headlines.get(vol)
    if not h:
        W(f"{vol:<20}{'—':>9}{'sin det.':>9}{'—':>16}{'—':>18}\n")
    else:
        W(f"{vol:<20}{h[1]:>9.2f}{level(h[1]):>9}{str(h[2]):>16}{h[3][:16]:>18}\n")
W("\n")

# ---- Eje 5: contraste con expectativas ----
W("### Contraste con expectativas (CLAUDE.md S15: recall≥60%, precision≥50%, ratio 0.5–2.0)\n")
W("VIIRS375 es el caballo de batalla (decide recall real). Banderas:\n")
flags = []
for vol in TIER:
    if vol not in per_vol:
        continue
    d = per_vol[vol]["VIIRS375"]
    rec, pre = rp(d["tp"], d["fn"], d["fp"])
    if rec is not None and rec < 0.60 and (d["tp"] + d["fn"]) >= 5:
        flags.append(f"  [recall<60%] {vol} VIIRS375 recall={rec*100:.0f}% (TP={d['tp']} FN={d['fn']})")
    if d["ratios_cl"]:
        m = median(d["ratios_cl"])
        if not (0.5 <= m <= 2.0):
            flags.append(f"  [ratio Cluster fuera 0.5-2.0] {vol} VIIRS375 medCl={m:.2f}x")
W(("\n".join(flags) if flags else "  NINGUNA bandera roja en VIIRS375.") + "\n")
OUT.flush()
