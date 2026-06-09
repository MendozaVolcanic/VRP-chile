"""S104 V2 — Auditoría del A/B Test1-NTI integral (brazo NTI) vs baseline MIR.

Compara el brazo NTI-integral (data/_test1_nti_integral, run 27223821692) contra
el baseline MIR (= brazo disabled del A/B V1, run 27186289487). Métricas ROBUSTAS
(mediana, A70) y eje DIRECCIONAL (offN/offE, A70/A61).

Criterios de aceptación (design §V2.4):
  - (R-recall) 0 FN nuevos en noches ALERTA MIROVA → recall_alert NTI == MIR.
  - (R-posición) offN de los nevados (Villarrica/Tupun/Llaima) → ~0 (cráter).
  - (R-concentración) %<3km sube en los nevados.
  - (R-control) Lascar/Lastarria SIN cambio.
  - (R-Test1-vivo) triggered_test1 NO debe caer a 0 (eso fue el fracaso de V1).

Uso: python audit_ab_test1_nti_v2.py <dir_NTI> <dir_MIR_baseline>
"""
import sys, json, math, csv, statistics
from pathlib import Path

NEVADOS = {"Tupungatito", "Villarrica", "Llaima"}
CONTROLS = {"Lascar", "Lastarria"}
VENT = {  # vent_lat, vent_lon (volcanoes.yaml)
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
        return None  # distinguir "no hay dir" de "0 records"
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


def med(xs):
    return statistics.median(xs) if xs else None


def metrics(recs, vol):
    """Devuelve dict de métricas VIIRS375 robustas para un brazo."""
    vlat, vlon = VENT[vol]
    vr = v375(recs)
    loc = [r for r in vr if r.get("final_hotspot_lat") is not None]
    offN = [(r["final_hotspot_lat"]-vlat)*111320 for r in loc]
    offE = [(r["final_hotspot_lon"]-vlon)*111320*math.cos(vlat*math.pi/180) for r in loc]
    dist = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"]) for r in loc]
    n_near = sum(1 for d in dist if d < 3.0)
    t1 = sum(1 for r in vr if r.get("triggered_test1"))
    t1pure = sum(1 for r in vr if r.get("triggered_test1") and not (
        r.get("n_nti_path", 0) or r.get("n_nti_rel_path", 0) or r.get("n_dnti_ctx_path", 0)))
    src_test1 = sum(1 for r in vr if r.get("final_hotspot_source") == "test1")
    nights = alert_nights(vol)
    hit = sum(1 for nd in nights if any((r.get("datetime_utc") or "")[:10] == nd for r in vr))
    return dict(nV375=len(vr), nLoc=len(loc), offN=med(offN), offE=med(offE),
                dist=med(dist), pct_near=(100*n_near/len(dist) if dist else None),
                t1=t1, t1pure=t1pure, src_test1=src_test1,
                recall=f"{hit}/{len(nights)}")


def fmt(v, w, p=0):
    if v is None:
        return f"{'—':>{w}}"
    return f"{v:>{w}.{p}f}"


def report(nti_dir, mir_dir):
    hdr = (f"{'VOL':<13}{'arm':<5}{'nV375':>6}{'offN_m':>8}{'offE_m':>8}"
           f"{'dist_km':>8}{'%<3km':>7}{'trig_t1':>8}{'t1pure':>7}{'srcT1':>6}{'recall':>8}")
    print(hdr); print("-"*len(hdr))
    for vol in ORDER:
        rN, rM = load(nti_dir, vol), load(mir_dir, vol)
        for arm, recs in [("MIR", rM), ("NTI", rN)]:
            if recs is None:
                print(f"{vol:<13}{arm:<5}{'(sin artifact)':>20}")
                continue
            m = metrics(recs, vol)
            tag = "  <ctrl" if vol in CONTROLS else ("  <nevado" if vol in NEVADOS else "")
            print(f"{vol:<13}{arm:<5}{m['nV375']:>6}{fmt(m['offN'],8)}{fmt(m['offE'],8)}"
                  f"{fmt(m['dist'],8,2)}{fmt(m['pct_near'],7,0)}{m['t1']:>8}{m['t1pure']:>7}"
                  f"{m['src_test1']:>6}{m['recall']:>8}{tag}")
        print()
    print("Criterios V2.4: NEVADOS offN->0 + %<3km sube + recall NTI==MIR (0 FN) | "
          "CONTROLES sin cambio | trig_t1 NO debe caer a 0 (eso fue el fracaso de V1).")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("uso: audit_ab_test1_nti_v2.py <dir_NTI> <dir_MIR_baseline>"); sys.exit(1)
    report(sys.argv[1], sys.argv[2])
