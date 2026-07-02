# Eje 1 S119 — Verificación post-flip C2 (gates intra-radio OFF desde 2026-06-28 ~21:00 UTC)
# Compara records post-flip vs pre-flip: recaptura second-pass, records/noche,
# magnitud summit (pc.vrp_mw, regla A10) vs mediana histórica 30d por vol/sensor.
# Output: experiments/_s119_audit/eje1_postflip.json (números source-of-truth, regla S91)
import json
import io
import sys
from pathlib import Path
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "mirova_equivalent"

TIER_A = [
    "Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
    "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
    "NevadosDeChillan",
]

FLIP = "2026-06-28 21:00"          # primer NRT run post-merge #474
PRE_WEEK_START = "2026-06-21 00:00"  # semana pre-flip comparable (1.2)
HIST_START = "2026-05-28 00:00"      # ventana 30d histórica para magnitud (1.3)


def night(dt: str) -> str:
    return dt[:10]


def load(vol: str):
    d = json.load(open(DATA / f"{vol}.json", encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


out = {"flip_utc": FLIP, "volcanoes": {}}
flags = []

for vol in TIER_A:
    recs = load(vol)
    post = [r for r in recs if r.get("datetime_utc", "") >= FLIP]
    pre = [r for r in recs
           if PRE_WEEK_START <= r.get("datetime_utc", "") < FLIP]
    hist = [r for r in recs
            if HIST_START <= r.get("datetime_utc", "") < FLIP]

    # 1.2 recaptura second-pass mediana + records/noche
    def recap_med(rs):
        vals = [r["diag_n_second_pass_recapture"] for r in rs
                if r.get("diag_n_second_pass_recapture") is not None]
        return round(median(vals), 2) if vals else None

    def per_night(rs):
        if not rs:
            return None
        nights = {night(r["datetime_utc"]) for r in rs}
        return round(len(rs) / len(nights), 2)

    # 1.3 magnitud summit pc.vrp_mw post vs mediana histórica por sensor
    def summit_pc(rs):
        res = {}
        for r in rs:
            if r.get("distance_class") != "summit":
                continue
            pc = r.get("primary_cluster") or {}
            v = pc.get("vrp_mw")
            if v is None or v <= 0:
                continue
            res.setdefault(r.get("sensor", "?"), []).append(v)
        return res

    hist_by_sensor = {s: median(v) for s, v in summit_pc(hist).items()}
    post_by_sensor = summit_pc(post)
    ratios = {}
    for s, vals in post_by_sensor.items():
        if s in hist_by_sensor and hist_by_sensor[s] > 0:
            ratios[s] = {
                "n_post": len(vals),
                "median_post_mw": round(median(vals), 3),
                "median_hist30d_mw": round(hist_by_sensor[s], 3),
                "ratio": round(median(vals) / hist_by_sensor[s], 2),
            }
            if not (0.5 <= ratios[s]["ratio"] <= 2.0) and len(vals) >= 3:
                flags.append(f"{vol}/{s}: ratio summit {ratios[s]['ratio']}x "
                             f"fuera de banda [0.5,2.0] (n={len(vals)})")

    # PCC vigilancia especial: noches con algún summit pc.vrp > 20 MW (modo difuso)
    pcc_big = None
    if vol == "PuyehueCordonCaulle":
        nights_post = {night(r["datetime_utc"]) for r in post}
        big = {night(r["datetime_utc"]) for r in post
               if r.get("distance_class") == "summit"
               and ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 20}
        pcc_big = {"nights_post": len(nights_post), "nights_big": len(big),
                   "frac": round(len(big) / len(nights_post), 3) if nights_post else None}
        if pcc_big["frac"] is not None and pcc_big["frac"] > 0.10:
            flags.append(f"PCC: {pcc_big['frac']*100:.0f}% noches con summit >20MW (>10% = candidato rollback)")

    out["volcanoes"][vol] = {
        "n_post": len(post), "n_pre_week": len(pre),
        "recapture_median_post": recap_med(post),
        "recapture_median_pre": recap_med(pre),
        "records_per_night_post": per_night(post),
        "records_per_night_pre": per_night(pre),
        "summit_ratio_vs_hist30d": ratios,
        **({"pcc_watch": pcc_big} if pcc_big else {}),
    }

out["flags"] = flags
outp = Path(__file__).parent / "eje1_postflip.json"
outp.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

print(f"{'vol':<22}{'n_post':>7}{'rec_post':>9}{'rec_pre':>8}{'r/n post':>9}{'r/n pre':>8}")
for vol, v in out["volcanoes"].items():
    print(f"{vol:<22}{v['n_post']:>7}{str(v['recapture_median_post']):>9}"
          f"{str(v['recapture_median_pre']):>8}{str(v['records_per_night_post']):>9}"
          f"{str(v['records_per_night_pre']):>8}")
    for s, r in v["summit_ratio_vs_hist30d"].items():
        print(f"    {s}: ratio {r['ratio']}x (post {r['median_post_mw']} MW n={r['n_post']} "
              f"vs hist {r['median_hist30d_mw']} MW)")
    if v.get("pcc_watch"):
        print(f"    PCC watch: {v['pcc_watch']}")
print("\nFLAGS:", len(flags))
for f in flags:
    print(" ⚠", f)
