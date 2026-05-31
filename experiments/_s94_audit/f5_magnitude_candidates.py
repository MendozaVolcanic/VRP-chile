"""S94 F5' — exploración de diseño: ¿qué fórmula de magnitud-foco aterriza ~1× vs
MIROVA sin romper el cráter caliente (Láscar 0.93×)?

NO implementa nada. Compara candidatas computables desde los anomaly_pixels del
record (lat/lon/dist_km/bt_k/vrp_mw) contra el VRP MIROVA, por volcán, para informar
el diseño del fix de display F5' (elegido por Nicolás: display primero).

Aproximación de cluster (limitación del display, A18): se restringe a anomaly_pixels
dentro de RADIO_PROXY km del centroide del primary_cluster. Para VIIRS375 (90%
centrado, §6) es buen proxy del cluster real.

Candidatas:
  M0_sum_actual  = pc.vrp_mw (suma real del pipeline; baseline)
  M_max          = máximo vrp_mw de un píxel (foco puro)
  M_top3         = suma de los 3 píxeles más calientes
  M_frac10       = suma de píxeles con vrp >= 0.10*max (núcleo, trim halo débil)
  M_frac25       = suma de píxeles con vrp >= 0.25*max (núcleo más estricto)

Objetivo: la candidata cuya mediana cross-vol esté más cerca de 1× Y mantenga
Láscar cerca de 1× (no sub-contar el foco real extendido).
  python experiments/_s94_audit/f5_magnitude_candidates.py

⚠️ RESULTADO (S94): este experimento REVELÓ que NO se puede diseñar F5' sobre la
data histórica. El campo anomaly_pixels[].vrp_mw está poblado INCONSISTENTEMENTE
entre épocas del pipeline: en Tupungatito, records de 2026-01-29 tienen
suma_pixels == pc.vrp_mw (consistente), 2026-01-30 está 10× off, y los recientes
(2026-05-29) tienen vrp por-píxel = 0 mientras pc.vrp_mw es positivo. 74/373
records Tupungatito tienen pc.vrp_mw > 2× la suma de sus propios píxeles. Las
candidatas dan 0.00× porque miden ese campo roto, NO una propiedad real de magnitud.
CONCLUSIÓN: F5' (display o pipeline) necesita per-píxel vrp consistente → BLOQUEADO
por F2 (reproc). Re-correr este experimento sobre data/_s94_reproc/ cuando F2 termine.
Confound A18/A50/S88 (4ª vez la sesión): la data histórica no diagnostica el pipeline.
"""
import sys, os, io, json, math, datetime as dt
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from pipeline.mirova_csv_loader import load_mirova_alertas

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
# S94 F2: VRP_DATA_DIR permite apuntar a data/_s94_reproc tras el reproc (default operacional).
DATA_DIR = os.path.join(REPO, os.environ.get("VRP_DATA_DIR", "data/mirova_equivalent"))
RADIO_PROXY = 3.0  # km alrededor del centroide = proxy del cluster
CANDS = ["M0_sum_actual", "M_max", "M_top3", "M_frac10", "M_frac25"]


def parse(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "").strip())
    except Exception:
        return None


def haversine(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def candidates(rec):
    pc = rec.get("primary_cluster") or {}
    m0 = pc.get("vrp_mw") or 0
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    aps = rec.get("anomaly_pixels") or []
    # proxy cluster: píxeles a <= RADIO_PROXY del centroide (si hay centroide)
    if clat is not None and clon is not None:
        px = [p for p in aps if p.get("lat") is not None
              and haversine(p["lat"], p["lon"], clat, clon) <= RADIO_PROXY]
    else:
        px = aps
    vrps = sorted((p.get("vrp_mw") or 0) for p in px)
    vrps = [v for v in vrps if v > 0]
    if not vrps:
        return {"M0_sum_actual": m0, "M_max": 0, "M_top3": 0, "M_frac10": 0, "M_frac25": 0}
    vmax = vrps[-1]
    return {
        "M0_sum_actual": m0,
        "M_max": vmax,
        "M_top3": sum(vrps[-3:]),
        "M_frac10": sum(v for v in vrps if v >= 0.10 * vmax),
        "M_frac25": sum(v for v in vrps if v >= 0.25 * vmax),
    }


def main():
    per = {vol: {c: [] for c in CANDS} for vol in TIER_A}
    for vol in TIER_A:
        d = json.load(open(os.path.join(DATA_DIR, f"{vol}.json"), encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
        cmin, cmax = min(cov), max(cov)
        mir = []
        for a in load_mirova_alertas(CONS, OCR, volcano=vol):
            if a.get("sensor_bucket") != "VIIRS375" or (a.get("vrp_mw") or 0) <= 0:
                continue
            t = parse(a.get("fecha_utc"))
            if t and cmin <= t <= cmax:
                mir.append((t, a["vrp_mw"]))
        for r in recs:
            s = str(r.get("sensor", "")).upper()
            if not (s.startswith("VIIRS") and not s.endswith("_750")):
                continue
            if (r.get("primary_cluster") or {}).get("vrp_mw", 0) <= 0:
                continue
            t = parse(r.get("datetime_utc"))
            if not t:
                continue
            near = [mv for (mt, mv) in mir if abs((t - mt).total_seconds()) <= 3600]
            if not near:
                continue
            mv = min(mir, key=lambda x: abs((t - x[0]).total_seconds()))[1]
            if mv <= 0:
                continue
            c = candidates(r)
            for k in CANDS:
                per[vol][k].append(c[k] / mv)

    out = {}
    print("=" * 100)
    print(f"F5' candidatas de magnitud — ratio MEDIANO vs MIROVA por volcán (VIIRS375, proxy {RADIO_PROXY}km)")
    print("=" * 100)
    print(f"{'Volcán':<20}{'n':>5}" + "".join(f"{c.replace('M_','').replace('M0_',''):>14}" for c in CANDS))
    for vol in sorted(TIER_A, key=lambda v: -(median(per[v]['M0_sum_actual']) if per[v]['M0_sum_actual'] else 0)):
        row = per[vol]
        n = len(row["M0_sum_actual"])
        if n == 0:
            continue
        meds = {c: median(row[c]) for c in CANDS}
        out[vol] = {"n": n, **{c: round(meds[c], 2) for c in CANDS}}
        print(f"{vol:<20}{n:>5}" + "".join(f"{meds[c]:>13.2f}×" for c in CANDS))
    print("-" * 100)
    # mediana cross-vol (de las medianas por volcán, ponderación pareja por volcán)
    allmeds = {c: median([median(per[v][c]) for v in TIER_A if per[v][c]]) for c in CANDS}
    print(f"{'MEDIANA cross-vol':<20}{'':>5}" + "".join(f"{allmeds[c]:>13.2f}×" for c in CANDS))
    out["_cross_vol_median"] = {c: round(allmeds[c], 2) for c in CANDS}
    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "f5_magnitude_candidates.json")
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nJSON → {outp}")
    print("Buscar: candidata con cross-vol cerca de 1× Y Láscar (cráter caliente) no sub-contado.")


if __name__ == "__main__":
    main()
