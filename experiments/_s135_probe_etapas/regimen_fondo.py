"""S135 — §3 de RESULTADOS.md: dos regímenes de fondo global en la ventana de D19.

Corte: merge de #535 (2026-08-28 23:00:56 UTC, `gh pr view 535 --json mergedAt`), que es
cuando `process_viirs.py` dejó de fijar `CLOUD_BT_THRESHOLD = 260 K` a mano y pasó a leer
`cloud_mask_bt_k: 0.0` del perfil. #537 (29-ago 14:20) fue sólo documentación.
Persistido en `regimen_fondo.json` (regla S91: ningún número transcrito a mano).

Definiciones (para que el número sea una afirmación, A90):
  ventana   = records VIIRS 375 m (sensor VIIRS_* sin sufijo _750) con datetime_utc >= 2026-06-01
  viejo     = datetime_utc < CORTE ; nuevo = >= CORTE
  fp>0      = diag_n_first_pass_pixels > 0
  recaptura = diag_n_first_pass_pixels == 0 y diag_n_second_pass_recapture > 0 (sobre los fp=0)
  fuentes   = Counter(final_hotspot_source), TODAS las claves (None incluida)
"""
import io
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CORTE = "2026-08-28 23:00"
DESDE = "2026-06-01"
VOLS = ("Villarrica", "Llaima", "Lascar")


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def resumen(g):
    n = len(g)
    fp0 = [r for r in g if r.get("diag_n_first_pass_pixels") == 0]
    return {
        "n": n,
        "t_bg_mediana_k": round(st.median([r["t_bg_k"] for r in g if r.get("t_bg_k") is not None]), 1) if g else None,
        "fp_mayor_0": sum(1 for r in g if (r.get("diag_n_first_pass_pixels") or 0) > 0),
        "fp0_n": len(fp0),
        "fp0_con_recaptura": sum(1 for r in fp0 if (r.get("diag_n_second_pass_recapture") or 0) > 0),
        "summit": sum(1 for r in g if r.get("distance_class") == "summit"),
        "fuentes": {str(k): v for k, v in Counter(r.get("final_hotspot_source") for r in g).most_common()},
    }


def main():
    out = {"corte_utc": CORTE, "desde": DESDE, "volcanes": {}}
    for vol in VOLS:
        recs = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
        rows = [r for r in recs if es_v375(r) and r["datetime_utc"] >= DESDE]
        viejo = [r for r in rows if r["datetime_utc"] < CORTE]
        nuevo = [r for r in rows if r["datetime_utc"] >= CORTE]
        out["volcanes"][vol] = {"viejo": resumen(viejo), "nuevo": resumen(nuevo)}
        for k in ("viejo", "nuevo"):
            s = out["volcanes"][vol][k]
            print(f"{vol:11s} {k:5s} n={s['n']:3d} t_bg={s['t_bg_mediana_k']} K  fp>0 {s['fp_mayor_0']}/{s['n']}  "
                  f"fp0 con recaptura {s['fp0_con_recaptura']}/{s['fp0_n']}  summit {s['summit']}  fuentes {s['fuentes']}")
    (Path(__file__).parent / "regimen_fondo.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
