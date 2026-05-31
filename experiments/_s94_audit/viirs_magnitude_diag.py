"""S94 — Diagnóstico de MAGNITUD en VIIRS (el sensor operacional real).

Re-centrado pedido por Nicolás: VIIRS es lo que más usamos (MIROVA publica 627-746
alertas VIIRS375 vs 80 MODIS). La detección VIIRS375 ya está bien (90% en el cráter,
spatial_audit). Lo que queda es la MAGNITUD: ratio mediano 2.0× sobre MIROVA.

Pregunta: ¿el 2× es parejo (calibración) o concentrado en fondo frío (artefacto de
campo frío sumando píxeles glaciares, mismo mecanismo que MODIS pero en 375m)?

Para cada record VIIRS375 / VIIRS750 emparejado con una alerta MIROVA (±60min, mismo
bucket), computa ratio = pc.vrp_mw / mirova_vrp y lo cruza con:
  - t_bg_k (fondo frío),
  - si "report-foco" (máximo píxel anómalo del cluster, <= centroid_dist+1km) en vez
    de la suma del cluster acercaría el ratio a 1.

Los anomaly_pixels guardan vrp_mw, bt_k, dist_km por píxel → el estimado report-foco
es offline-válido (NO cambia selección de cluster, solo cómo se reporta el ya
seleccionado; A18 no aplica como en cambios de cluster).

§0.5: fuente reproducible, vuelca JSON. NO toca pipeline.
  python experiments/_s94_audit/viirs_magnitude_diag.py
"""
import sys, os, io, json, datetime as dt
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from pipeline.mirova_csv_loader import load_mirova_alertas

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")


def our_bucket(s):
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


def focus_vrp(rec):
    """VRP del píxel anómalo más caliente dentro del cluster (proxy 'reportar foco').

    El cluster no tiene id por píxel; aproximamos por los píxeles dentro de
    centroid_dist+1km del vent. Devuelve el max vrp_mw de esos píxeles."""
    pc = rec.get("primary_cluster") or {}
    cd = pc.get("centroid_dist_km")
    aps = rec.get("anomaly_pixels") or []
    if not aps:
        return None
    if cd is None:
        cand = aps
    else:
        cand = [p for p in aps if p.get("dist_km") is not None and abs(p["dist_km"] - cd) <= 1.0]
        if not cand:
            cand = aps
    vrps = [p.get("vrp_mw") for p in cand if p.get("vrp_mw") is not None]
    return max(vrps) if vrps else None


def main():
    res = {b: {} for b in ("VIIRS375", "VIIRS750")}
    for vol in TIER_A:
        d = json.load(open(os.path.join(REPO, f"data/mirova_equivalent/{vol}.json"), encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
        cmin, cmax = min(cov), max(cov)
        al = load_mirova_alertas(CONS, OCR, volcano=vol)
        mir = {"VIIRS375": [], "VIIRS750": []}
        for a in al:
            if (a.get("vrp_mw") or 0) <= 0:
                continue
            b = a.get("sensor_bucket")
            if b not in mir:
                continue
            t = parse(a.get("fecha_utc"))
            if t and cmin <= t <= cmax:
                mir[b].append((t, a["vrp_mw"]))
        for b in ("VIIRS375", "VIIRS750"):
            ratios_sum, ratios_focus, tbgs = [], [], []
            for r in recs:
                if our_bucket(r.get("sensor")) != b:
                    continue
                pc = r.get("primary_cluster") or {}
                vrp = pc.get("vrp_mw") or 0
                if vrp <= 0:
                    continue
                t = parse(r.get("datetime_utc"))
                if not t:
                    continue
                near = [mv for (mt, mv) in mir[b] if abs((t - mt).total_seconds()) <= 3600]
                if not near:
                    continue
                mv = min(((mt, m) for (mt, m) in mir[b]), key=lambda x: abs((t - x[0]).total_seconds()))[1]
                if mv <= 0:
                    continue
                ratios_sum.append(vrp / mv)
                fv = focus_vrp(r)
                if fv is not None:
                    ratios_focus.append(fv / mv)
                if r.get("t_bg_k") is not None:
                    tbgs.append(r["t_bg_k"])
            if ratios_sum:
                res[b][vol] = {
                    "n": len(ratios_sum),
                    "ratio_sum_med": round(median(ratios_sum), 2),
                    "ratio_focus_med": round(median(ratios_focus), 2) if ratios_focus else None,
                    "t_bg_med_k": round(median(tbgs), 1) if tbgs else None,
                }

    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viirs_magnitude_diag.json")
    json.dump(res, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    for b in ("VIIRS375", "VIIRS750"):
        print("=" * 80)
        print(f"{b} — ratio magnitud vs MIROVA por volcán (n=pares emparejados)")
        print("=" * 80)
        print(f"{'Volcán':<20}{'n':>5}{'ratio_SUMA':>12}{'ratio_FOCO':>12}{'t_bg_med':>12}")
        rows = sorted(res[b].items(), key=lambda kv: -(kv[1]["ratio_sum_med"]))
        all_sum, all_focus = [], []
        for vol, m in rows:
            rf = f"{m['ratio_focus_med']:.2f}×" if m["ratio_focus_med"] is not None else "-"
            tb = f"{m['t_bg_med_k']:.0f}K" if m["t_bg_med_k"] is not None else "-"
            print(f"{vol:<20}{m['n']:>5}{m['ratio_sum_med']:>11.2f}×{rf:>12}{tb:>12}")
            all_sum.append(m["ratio_sum_med"])
            if m["ratio_focus_med"] is not None:
                all_focus.append(m["ratio_focus_med"])
        if all_sum:
            print("-" * 80)
            print(f"{'MEDIANA cross-vol':<20}{'':>5}{median(all_sum):>11.2f}×"
                  f"{(f'{median(all_focus):.2f}×' if all_focus else '-'):>12}")
        print()
    print(f"JSON → {outp}")
    print("LECTURA: si ratio_SUMA es ~1× en cráteres calientes (Láscar) y alto en")
    print("fondo frío (Tupungatito glaciar), el 2× es campo frío, NO calibración.")
    print("Si ratio_FOCO baja cerca de 1×, reportar foco (F5) cura sin tocar detección.")


if __name__ == "__main__":
    main()
