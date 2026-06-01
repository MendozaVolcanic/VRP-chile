"""S95 — barrido fino de D2 (radial desde el pico, anclado al vent).

D2 fue la única variante que mordió el campo frío en el primer barrido (mediana
5.64×→1.92×) sin romper Láscar. Acá barremos R_core (radio km desde el pico) y
bt_ext (umbral de extensión por lava real) para acercar Tupungatito/Villarrica a
~1× sin sub-contar el cráter caliente (Láscar ≥0.9×) ni vaciar records reales.

Reusa la lógica de f5_variants.py (misma data reprocesada, mismo matching MIROVA,
recompute de distancia desde el vent — A48/Eje3). Correr:
  VRP_DATA_DIR=data/_s94_reproc python experiments/_s95_audit/f5_d2_sweep.py

Salida: tabla ratio por volcán para cada R_core + criterio de seguridad
(# records cuya magnitud F5' cae a 0 = posible pérdida de señal real).
"""
import sys, os, io, json, math, datetime as dt
from statistics import median

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "experiments", "_s94_audit"))
import yaml
from pipeline.mirova_csv_loader import load_mirova_alertas
# f5_variants reconfigura sys.stdout=TextIOWrapper(sys.stdout.buffer) en import-time,
# lo que cierra el buffer original cuando este script redirige a archivo. Guardamos
# el fd real y reabrimos un stdout limpio tras el import.
_fd = os.dup(1)
from f5_variants import hav, load_vents, parse, variant_d2, baseline
sys.stdout = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

DATA_DIR = os.path.join(REPO, os.environ.get("VRP_DATA_DIR", "data/_s94_reproc"))
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]

R_CORE_GRID = [0.75, 1.0, 1.25, 1.5, 2.0]
BT_EXT = 295.0  # umbral lava real para extensión (fijo en este barrido)


def collect():
    """Devuelve por volcán: lista de (pixels, vent, mv) de records VIIRS375 con match MIROVA."""
    vents = load_vents()
    per = {}
    for vol in TIER_A:
        p = os.path.join(DATA_DIR, f"{vol}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
        if not cov:
            continue
        cmin, cmax = min(cov), max(cov)
        mir = []
        for a in load_mirova_alertas(CONS, OCR, volcano=vol):
            if a.get("sensor_bucket") != "VIIRS375" or (a.get("vrp_mw") or 0) <= 0:
                continue
            t = parse(a.get("fecha_utc"))
            if t and cmin <= t <= cmax:
                mir.append((t, a["vrp_mw"]))
        vent = vents.get(vol)
        if not vent or vent[0] is None or not mir:
            continue
        rows = []
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
            px = [p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
            rows.append((px, vent, mv))
        if rows:
            per[vol] = rows
    return per


def main():
    per = collect()
    print("=" * 100)
    print(f"F5' D2 barrido R_core | data={os.path.relpath(DATA_DIR, REPO)} | bt_ext={BT_EXT}")
    print("=" * 100)
    header = f"{'Volcán':<20}{'n':>4}{'base':>8}" + "".join(f"R={r:>4}" for r in R_CORE_GRID)
    print(header)
    aggr = {r: [] for r in R_CORE_GRID}
    zeros = {r: 0 for r in R_CORE_GRID}  # records que caen a magnitud 0
    ztot = 0
    for vol in TIER_A:
        if vol not in per:
            continue
        rows = per[vol]
        n = len(rows)
        base_med = median([baseline(px, vent) / mv for (px, vent, mv) in rows])
        cells = []
        for r in R_CORE_GRID:
            ratios = []
            for (px, vent, mv) in rows:
                mag = variant_d2(px, vent, r_core=r, bt_ext=BT_EXT)
                ratios.append(mag / mv)
                if mag <= 0:
                    zeros[r] += 1
            med = median(ratios)
            aggr[r].append(med)
            cells.append(med)
        print(f"{vol:<20}{n:>4}{base_med:>7.2f}×" + "".join(f"{c:>5.2f}×" for c in cells))
    print("-" * 100)
    print(f"{'MEDIANA cross-vol':<20}{'':>4}{'':>8}" +
          "".join(f"{median(aggr[r]):>5.2f}×" for r in R_CORE_GRID))
    print(f"{'records a magnitud 0':<20}{'':>4}{'':>8}" +
          "".join(f"{zeros[r]:>6}" for r in R_CORE_GRID))
    print("\nCriterio: cross-vol→1×, Láscar≥0.9×, 'records a magnitud 0'=0 (no perder señal).")


if __name__ == "__main__":
    main()
