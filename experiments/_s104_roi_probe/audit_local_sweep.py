"""S105 — Auditoría multi-brazo del A/B del fondo-local-NTI + barrido k_sigma.

Compara N brazos contra el ground truth MIROVA, métricas robustas (mediana A70),
VIIRS375. Brazos esperados (label, dir bajo experiments/_s104_roi_probe o data/):
  MIR-anillo  = baseline_mir            (= disabled del A/B V1)
  NTI-anillo  = nti_integral            (V2)
  local-k3.0  = _test1_nti_local        (descargar+mergear del run 27275241269)
  local-k2.0  = _test1_nti_local_ks20   (del barrido 27276651420)
  local-k2.5  = _test1_nti_local_ks25   (del barrido 27276651420)

Criterios (design 2026-06-10 §4): offset N→0 nevados + %<3km sube + 0 FN noches ALERTA
en los 5 + Tupun cat-b conservado (trig_t1 no se desploma) + Lascar/Lastarria sin cambio.

Uso: python audit_local_sweep.py <label1>:<dir1> <label2>:<dir2> ...
"""
import sys, json, math, csv, statistics
from pathlib import Path

NEVADOS = {"Tupungatito", "Villarrica", "Llaima"}
CONTROLS = {"Lascar", "Lastarria"}
VENT = {
    "Tupungatito": (-33.389044, -69.826374), "Villarrica": (-39.420227, -71.939876),
    "Llaima": (-38.692, -71.729), "Lascar": (-23.36293, -67.731416),
    "Lastarria": (-25.168, -68.507),
}
ORDER = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
CSV_CONS = Path(__file__).resolve().parents[2] / "latest_consolidado.csv"


def hav(la1, lo1, la2, lo2):
    R = 6371.0; p = math.pi / 180
    a = (math.sin((la2-la1)*p/2)**2 +
         math.cos(la1*p)*math.cos(la2*p)*math.sin((lo2-lo1)*p/2)**2)
    return 2*R*math.asin(min(1, math.sqrt(a)))


def load(d, vol):
    f = Path(d) / f"{vol}.json"
    if not f.exists():
        return None
    obj = json.load(open(f, encoding="utf-8"))
    return obj.get("records", obj) if isinstance(obj, dict) else obj


def alert_nights(vol):
    out = set()
    if not CSV_CONS.exists():
        return out
    for r in csv.DictReader(open(CSV_CONS, encoding="utf-8", errors="replace")):
        if r.get("Volcan") == vol and r.get("Tipo_Registro", "").startswith("ALERTA_TERMICA"):
            f = r.get("Fecha_Satelite_UTC") or r.get("Fecha_UTC") or ""
            if f:
                out.add(f[:10])
    return out


def v375(recs):
    return [r for r in recs
            if r.get("sensor", "").startswith("VIIRS") and not r["sensor"].endswith("750")]


def metrics(recs, vol):
    vlat, vlon = VENT[vol]
    vr = v375(recs)
    loc = [r for r in vr if r.get("final_hotspot_lat") is not None]
    offN = [(r["final_hotspot_lat"]-vlat)*111320 for r in loc]
    dist = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"]) for r in loc]
    n_near = sum(1 for d in dist if d < 3.0)
    t1 = sum(1 for r in vr if r.get("triggered_test1"))
    nights = alert_nights(vol)
    hit = sum(1 for nd in nights if any((r.get("datetime_utc") or "")[:10] == nd for r in vr))
    return dict(n=len(vr),
                offN=statistics.median(offN) if offN else None,
                dist=statistics.median(dist) if dist else None,
                near=(100*n_near/len(dist)) if dist else None,
                t1=t1, recall=f"{hit}/{len(nights)}")


def report(arms):
    for vol in ORDER:
        tag = "NEVADO" if vol in NEVADOS else "control"
        print(f"\n=== {vol} ({tag}) ===")
        print(f"  {'brazo':<14}{'nV375':>6}{'offN_m':>8}{'dist_km':>8}{'%<3km':>7}{'trig_t1':>8}{'recall':>9}")
        for label, d in arms:
            recs = load(d, vol)
            if recs is None:
                print(f"  {label:<14}{'(sin data)':>20}")
                continue
            m = metrics(recs, vol)
            offN = f"{m['offN']:.0f}" if m['offN'] is not None else "—"
            dist = f"{m['dist']:.2f}" if m['dist'] is not None else "—"
            near = f"{m['near']:.0f}" if m['near'] is not None else "—"
            print(f"  {label:<14}{m['n']:>6}{offN:>8}{dist:>8}{near:>7}{m['t1']:>8}{m['recall']:>9}")
    print("\nCriterios: NEVADOS offN->0 + %<3km sube + recall == MIR-anillo (0 FN) | "
          "Tupun trig_t1 no se desploma (cat-b real) | controles sin cambio.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: audit_local_sweep.py <label>:<dir> ..."); sys.exit(1)
    arms = [tuple(a.split(":", 1)) for a in sys.argv[1:]]
    report(arms)
