"""S104 — Auditoría A/B co-validación NTI del Test1.

Compara los JSON de los dos brazos (enabled/disabled) contra el ground truth MIROVA.
Criterios de aceptación (docs/superpowers/specs/2026-06-09-test1-nti-covalidation-design.md §7):
  - 0 FN nuevos en las noches ALERTA_TERMICA MIROVA (recall protegido).
  - offset direccional VIIRS375 de los nevados se acerca a ~0 (cráter).
  - cuántos records Test1-puro elimina.
  - controles (Lascar árido, Lastarria fumarólico) SIN cambio.

Uso (tras `gh run download` de los artifacts a dos dirs):
  python audit_ab_test1_nti.py <dir_enabled> <dir_disabled>
"""
import sys, json, math, csv
from pathlib import Path
from collections import Counter

NEVADOS = {"Tupungatito", "Villarrica", "Llaima"}
CONTROLS = {"Lascar", "Lastarria"}
VENT = {  # vent_lat, vent_lon (volcanoes.yaml)
    "Tupungatito": (-33.389044, -69.826374), "Villarrica": (-39.420227, -71.939876),
    "Llaima": (-38.692, -71.729), "Lascar": (-23.36293, -67.731416),
    "Lastarria": (-25.168, -68.507),
}
CSV_CONS = Path(__file__).resolve().parents[2] / "latest_consolidado.csv"


def hav(la1, lo1, la2, lo2):
    R = 6371; p = math.pi / 180
    a = (math.sin((la2-la1)*p/2)**2 + math.cos(la1*p)*math.cos(la2*p)*math.sin((lo2-lo1)*p/2)**2)
    return 2*R*math.asin(min(1, math.sqrt(a)))


def load(d, vol):
    f = Path(d) / f"{vol}.json"
    if not f.exists(): return []
    obj = json.load(open(f))
    return obj.get("records", obj) if isinstance(obj, dict) else obj


def alert_nights(vol):
    out = set()
    if not CSV_CONS.exists(): return out
    for r in csv.DictReader(open(CSV_CONS, encoding="utf-8", errors="replace")):
        if r.get("Volcan") == vol and r.get("Tipo_Registro") in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR"):
            out.add(r["Fecha_Satelite_UTC"][:10])
    return out


def v375(recs):
    return [r for r in recs if r.get("sensor", "").startswith("VIIRS") and not r["sensor"].endswith("750")]


def offset_n(recs, vol):
    vlat, vlon = VENT[vol]
    sub = [r for r in v375(recs) if r.get("final_hotspot_lat") is not None]
    if not sub: return None, 0
    dN = sum((r["final_hotspot_lat"]-vlat)*111320 for r in sub)/len(sub)
    return dN, len(sub)


def report(en_dir, dis_dir):
    print(f"{'VOL':<14}{'arm':<5}{'nV375':>6}{'offN_m':>8}{'test1puro':>10}{'recall_alert':>14}")
    for vol in ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]:
        nights = alert_nights(vol)
        for arm, d in [("EN", en_dir), ("DIS", dis_dir)]:
            recs = load(d, vol)
            vr = v375(recs)
            off, n = offset_n(recs, vol)
            t1pure = sum(1 for r in vr if r.get("triggered_test1") and not (
                r.get("n_nti_path", 0) or r.get("n_nti_rel_path", 0) or r.get("n_dnti_ctx_path", 0)))
            hit = sum(1 for nd in nights if any(r["datetime_utc"][:10] == nd for r in vr))
            tag = "  <-control" if vol in CONTROLS else ""
            print(f"{vol:<14}{arm:<5}{n:>6}{(off if off is not None else 0):>8.0f}{t1pure:>10}"
                  f"{hit:>8}/{len(nights):<5}{tag}")
    print("\nCriterios: offN_m EN debe ↓ vs DIS en nevados (→0); recall_alert EN == DIS "
          "(0 FN nuevos); controles SIN cambio.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("uso: audit_ab_test1_nti.py <dir_enabled> <dir_disabled>"); sys.exit(1)
    report(sys.argv[1], sys.argv[2])
