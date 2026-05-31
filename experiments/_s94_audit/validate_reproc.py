"""S94 F2 — validación del reproc (correr cuando data/_s94_reproc/ esté poblado).

Pre-escrito mientras el workflow corre (A16). Compara cada volcán reprocesado
(data/_s94_reproc/<vol>.json) contra el operacional (data/mirova_equivalent/<vol>.json)
para responder las 3 preguntas de validación F2:

  Q1 — CONSISTENCIA per-píxel (lo que bloqueó F5'): ¿en la data reprocesada
       pc.vrp_mw ≈ sum(anomaly_pixels.vrp_mw)? Si sí en TODOS los records, el código
       actual es consistente y la inconsistencia era 100% histórica → F5' desbloqueado.
       Si los records recientes siguen con anomaly_pixels.vrp_mw=0 → schema gap del
       código ACTUAL (A07), a arreglar antes de F5'.

  Q2 — DEUDA LÁSCAR: ¿los records MODIS de Láscar feb ahora anclan en el cráter
       (distance_class=summit, dist<6km) en vez del Salar (far, 18-29km)?

  Q3 — DEUDA CAMPO FRÍO: ¿los picos inflados (Tupungatito 190 MW, PCC 337 MW) bajaron
       (cap D9 5 MW o menos)? Comparar max pc.vrp_mw operacional vs reprocesado.

Solo lee; no toca nada. Uso:
  python experiments/_s94_audit/validate_reproc.py
"""
import sys, os, io, json
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPER = os.path.join(REPO, "data/mirova_equivalent")
REPROC = os.path.join(REPO, "data/_s94_reproc")
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]


def load(path):
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def is_v375(r):
    s = str(r.get("sensor", "")).upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def consistency(recs):
    """Fracción de records VIIRS375 con pc.vrp_mw ≈ sum(anomaly_pixels) (±20%)."""
    ok = bad = zero = 0
    for r in recs:
        if not is_v375(r):
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v <= 0:
            continue
        sp = sum(p.get("vrp_mw") or 0 for p in (r.get("anomaly_pixels") or []))
        if sp <= 0:
            zero += 1
        elif 0.8 <= v / sp <= 1.25:
            ok += 1
        else:
            bad += 1
    return ok, bad, zero


def main():
    if not os.path.isdir(REPROC):
        print(f"⏳ {REPROC} todavía no existe — el reproc no escribió nada aún.")
        return
    done = [v for v in TIER_A if os.path.exists(os.path.join(REPROC, f"{v}.json"))]
    print(f"Volcanes reprocesados disponibles: {len(done)}/11 → {done}\n")
    if not done:
        print("⏳ Ningún JSON reprocesado todavía.")
        return

    print("=" * 88)
    print("Q1 — CONSISTENCIA per-píxel (pc.vrp_mw vs suma anomaly_pixels) en data reprocesada")
    print("=" * 88)
    print(f"{'Volcán':<20}{'OK':>6}{'≠(>20%)':>10}{'vrp=0':>8}  veredicto")
    for vol in done:
        ok, bad, zero = consistency(load(os.path.join(REPROC, f"{vol}.json")))
        tot = ok + bad + zero
        verdict = "✓ consistente" if tot and ok / tot > 0.9 else (
            "⚠ vrp=0 (schema gap actual?)" if zero > bad else "⚠ descuadrado")
        print(f"{vol:<20}{ok:>6}{bad:>10}{zero:>8}  {verdict}")

    print("\n" + "=" * 88)
    print("Q2/Q3 — DEUDA: max VRP y ancla de cluster, operacional vs reprocesado")
    print("=" * 88)
    print(f"{'Volcán':<20}{'maxVRP_op':>11}{'maxVRP_rep':>12}{'%far_op':>9}{'%far_rep':>10}")
    for vol in done:
        op = load(os.path.join(OPER, f"{vol}.json")) or []
        rp = load(os.path.join(REPROC, f"{vol}.json")) or []

        def stats(recs):
            vrps = [(r.get("primary_cluster") or {}).get("vrp_mw") or 0 for r in recs
                    if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0]
            far = [r for r in recs if r.get("distance_class") == "far"
                   and ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0]
            npos = len(vrps)
            return (max(vrps) if vrps else 0, (100 * len(far) / npos) if npos else 0)

        mvo, faro = stats(op)
        mvr, farr = stats(rp)
        print(f"{vol:<20}{mvo:>11.1f}{mvr:>12.1f}{faro:>8.0f}%{farr:>9.0f}%")
    print("\nLECTURA: Q1 todos ✓ → F5' desbloqueado (re-correr viirs_magnitude_diag.py +")
    print("f5_magnitude_candidates.py con DATA_DIR=data/_s94_reproc). maxVRP_rep << maxVRP_op")
    print("y %far_rep < %far_op en Láscar/Tupungatito → F2 limpió la deuda.")


if __name__ == "__main__":
    main()
