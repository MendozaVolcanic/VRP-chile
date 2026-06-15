"""S109 (#3) — RESOLVER el método del ratio de magnitud VIIRS vs MIROVA.

Tres números en conflicto en las fuentes:
  - AUDIT_S108_ESTADO.md:  VIIRS375 ~0.52x, VIIRS750 ~0.55x  (sub-estimacion)
  - S103 R3:               VIIRS375 0.78x
  - per_sensor_metrics.json: ratio_median V375 1.996, V750 1.529 (parece STALE/pre-nadir)

Este script computa el ratio mediano (pc.vrp_mw_nuestro / VRP_MW_MIROVA, campo A10
primary_cluster.vrp_mw — NO record.vrp_mw scene-wide) sobre la DATA ACTUAL
(data/mirova_equivalent/*.json) cruzada contra MIROVA (latest_consolidado.csv + OCR),
bajo METODOS EXPLICITOS y por sensor (convencion A48):

  (a) por-pasada +-60min, CONS-only
  (b) por-pasada +-60min, CONS u OCR
  (c) por-noche (agregando pasadas de la misma noche-volcan-sensor)

Cada metodo en 2 alcances espaciales para aislar el efecto:
  - SUMMIT-only (distance_class=='summit'): lo que el dashboard reporta.
  - CRUDO (cualquier distancia, pc.vrp_mw>0): "vimos algo esa noche".

Y ademas la PRUEBA DE STALENESS: recomputa el MISMO metodo declarado en
per_sensor_metrics.json ('CONS+OCR vrp>0, coverage-restricted', match +-60min, vista
RAW = crudo) sobre data actual. Si el json dice ~2x y esto da ~0.5x, el json es stale
(pre-nadir VIIRS S103).

Read-only. Reusa el loader canonico pipeline.mirova_csv_loader (CONS u OCR, A11/A14/A48).
Uso: python experiments/_s94_audit/ratio_method_resolution_s109.py
"""
import sys, os, io, json
import datetime as dt
from statistics import median
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from pipeline.mirova_csv_loader import load_mirova_alertas

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
WIN = 3600  # +-60 min


def our_bucket(s):
    """A48: VIIRS_*_750 = M-band (VIIRS750); VIIRS_SNPP/NOAA* (sin sufijo) = I-band 375m."""
    s = str(s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def parse(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "").strip())
    except Exception:
        return None


def night_key(t):
    """Noche-satelite: la pasada ~05:00-06:00 UTC de un dia es la misma noche que la
    tarde anterior local; agregamos por fecha UTC de la pasada (las pasadas nocturnas
    de un volcan-sensor caen en la misma fecha UTC)."""
    return t.date()


def load_ours(vol):
    """Devuelve por bucket lista de dicts: {t, vrp (pc.vrp_mw), dc (distance_class)}.
    Solo pc.vrp_mw>0 (A10). cov_min/cov_max = ventana de cobertura del volcan."""
    d = json.load(open(os.path.join(REPO, f"data/mirova_equivalent/{vol}.json"), encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    by_b = defaultdict(list)
    cov = []
    for r in recs:
        t = parse(r.get("datetime_utc"))
        if t is None:
            continue
        cov.append(t)
        b = our_bucket(r.get("sensor"))
        if b is None:
            continue
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
        if v <= 0:
            continue
        by_b[b].append({"t": t, "vrp": v, "dc": r.get("distance_class")})
    return by_b, (min(cov), max(cov)) if cov else (None, None)


def load_mir(vol, universe):
    """universe in {'CONS','CONSOCR'}. Devuelve por bucket lista {t, vrp}."""
    ocr = OCR if universe == "CONSOCR" else None
    by_b = defaultdict(list)
    for a in load_mirova_alertas(CONS, ocr, volcano=vol):
        if (a.get("vrp_mw") or 0) <= 0:
            continue
        b = a.get("sensor_bucket")
        t = parse(a.get("fecha_utc"))
        if t is None:
            continue
        by_b[b].append({"t": t, "vrp": a.get("vrp_mw")})
    return by_b


def ratio_per_pass(ours, mir, summit_only):
    """Por-pasada: por cada deteccion nuestra con vrp>0 (opt. summit), buscar la alerta
    MIROVA mas cercana dentro de +-WIN; ratio = nuestro/MIROVA."""
    rs = []
    pool = [o for o in ours if (not summit_only or o["dc"] == "summit")]
    for o in pool:
        cands = [m for m in mir if abs((o["t"] - m["t"]).total_seconds()) <= WIN]
        if not cands:
            continue
        closest = min(cands, key=lambda m: abs((o["t"] - m["t"]).total_seconds()))
        if closest["vrp"] and closest["vrp"] > 0:
            rs.append(o["vrp"] / closest["vrp"])
    return rs


def ratio_per_night(ours, mir, summit_only):
    """Por-noche: agregar (max) las pasadas nuestras y de MIROVA por fecha UTC, luego
    ratio sobre las noches con ambos lados presentes. Agregamos por MAX (la pasada que
    el dashboard muestra como pico de la noche)."""
    onb, mnb = defaultdict(float), defaultdict(float)
    for o in ours:
        if summit_only and o["dc"] != "summit":
            continue
        k = night_key(o["t"])
        onb[k] = max(onb[k], o["vrp"])
    for m in mir:
        k = night_key(m["t"])
        mnb[k] = max(mnb[k], m["vrp"])
    rs = []
    for k, ov in onb.items():
        if k in mnb and mnb[k] > 0 and ov > 0:
            rs.append(ov / mnb[k])
    return rs


def run_method(universe, agg, summit_only):
    """universe: CONS|CONSOCR ; agg: pass|night ; summit_only: bool.
    Devuelve {bucket: list of ratios} acumulado sobre los 11 Tier A."""
    out = {"VIIRS375": [], "VIIRS750": []}
    for vol in TIER_A:
        ours_b, (cmin, cmax) = load_ours(vol)
        mir_b = load_mir(vol, universe)
        for b in ("VIIRS375", "VIIRS750"):
            ours = ours_b.get(b, [])
            # restringir MIROVA a la ventana de cobertura (no penalizar magnitud por fechas sin data)
            mir = [m for m in mir_b.get(b, []) if cmin and cmin <= m["t"] <= cmax]
            if agg == "pass":
                out[b] += ratio_per_pass(ours, mir, summit_only)
            else:
                out[b] += ratio_per_night(ours, mir, summit_only)
    return out


def fmt(rs):
    return (round(median(rs), 3), len(rs)) if rs else (None, 0)


def main():
    results = []  # for JSON
    print("=" * 96)
    print("S109 #3 — RATIO MAGNITUD VIIRS (pc.vrp_mw nuestro / VRP_MW MIROVA) sobre DATA ACTUAL")
    print("=" * 96)
    print(f"{'scope':<9}{'agg':<7}{'universe':<10}{'sensor':<10}{'ratio_med':>10}{'n_pairs':>9}")
    print("-" * 96)
    for summit_only, scope in [(True, "summit"), (False, "crudo")]:
        for agg, agg_lbl in [("pass", "pasada"), ("night", "noche")]:
            for universe, uni_lbl in [("CONS", "CONS"), ("CONSOCR", "CONS+OCR")]:
                # 'noche' solo lo corremos para CONS+OCR (metodo c canonico) y CONS, ambos utiles
                res = run_method(universe, agg, summit_only)
                for b in ("VIIRS375", "VIIRS750"):
                    rm, n = fmt(res[b])
                    rms = f"{rm:.3f}x" if rm is not None else "-"
                    print(f"{scope:<9}{agg_lbl:<7}{uni_lbl:<10}{b:<10}{rms:>10}{n:>9}")
                    results.append({"scope": scope, "agg": agg, "universe": uni_lbl,
                                    "sensor": b, "ratio_median": rm, "n_pairs": n})
            print()

    # --- PRUEBA DE STALENESS: replicar EXACTAMENTE el metodo del json ---
    # per_sensor_metrics.json 'raw': universe CONS+OCR, match +-60min, vista CRUDO (cualquier
    # dist, pc.vrp_mw>0), por-pasada. Es scope=crudo, agg=pass, universe=CONSOCR.
    print("=" * 96)
    print("PRUEBA STALENESS — replico metodo declarado en per_sensor_metrics.json")
    print("(universe=CONS+OCR, match +-60min, vista RAW/crudo, por-pasada)")
    print("=" * 96)
    stale_now = run_method("CONSOCR", "pass", False)
    json_vals = {"VIIRS375": 1.996, "VIIRS750": 1.529}  # valores actuales del json (S94/pre-nadir)
    for b in ("VIIRS375", "VIIRS750"):
        rm, n = fmt(stale_now[b])
        print(f"  {b}: json dice {json_vals[b]:.3f}x  |  recomputo AHORA = {rm:.3f}x (n={n})")
    print()

    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ratio_method_resolution_s109.json")
    json.dump({"window_min": WIN // 60, "field": "primary_cluster.vrp_mw (A10)",
               "data_date": "current (2026-06-14)", "methods": results,
               "staleness_check": {b: {"json_value": json_vals[b], "recomputed_now": fmt(stale_now[b])[0],
                                       "n_pairs": fmt(stale_now[b])[1]} for b in ("VIIRS375", "VIIRS750")}},
              open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"JSON -> {outp}")


if __name__ == "__main__":
    main()
