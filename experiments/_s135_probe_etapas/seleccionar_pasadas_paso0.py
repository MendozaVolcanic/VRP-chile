"""S135 — paso 0 del A/B D1(c): elegir las pasadas de la cara cat-b (RESULTADOS.md §4.2).

POR QUÉ. El probe de las 6 pasadas midió sólo la cara «artefacto» de la tensión A83/A84
(Villarrica) y un control (Láscar) que resultó vacuo porque allí keep_peak nunca corre. La
otra cara —las noches en que el pico del Test 1 SÍ es lo que MIROVA confirma— vive en
Lastarria (60 %), Tupungatito (34 %) e Isluga (30 %) según S134 F3. Sin medirla, apagar
keep_peak es una apuesta.

QUÉ ELIGE (definición dentro, A90):
  cat-b   = record VIIRS375 summit con final_hotspot_source == "test1_roi" y una fila ALERTA
            MIROVA bucket VIIRS375 (CONS ∪ OCR) a |Δt| ≤ 20 min (misma pasada, S131). Lastarria, Tupungatito,
            Isluga: hasta 3 por volcán, prefiriendo el régimen nuevo (≥ 2026-08-28 23:00 UTC,
            D14) y, dentro de él, los más recientes; si no alcanza, se completa con los más
            recientes del régimen viejo desde 2026-06-01 y se marca.
  control = record VIIRS375 summit de Láscar con final_hotspot_source == "test1_roi",
            diag_n_first_pass_pixels == 0 y alerta MIROVA a ±20 min: keep_peak SÍ corre ahí
            (a diferencia del control de las 6 pasadas). Hasta 3.
Salida: pasadas_paso0.json (lista de {volcan, pasada_utc, sensor, clase, regimen, mirova}).
"""
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
CORTE = "2026-08-28 23:00"
DESDE = "2026-06-01"
DT_MAX_MIN = 20   # misma pasada (S131 03_pares_por_pasada); ±90 mezclaba plataformas
CATB = ("Lastarria", "Tupungatito", "Isluga")


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def alertas_por_vol():
    out = {}
    for a in load_mirova_alertas(cons_path=str(SNAP / "registro_vrp_consolidado.csv"),
                                 ocr_path=str(SNAP / "registro_vrp_ocr.csv")):
        if a["sensor_bucket"] != "VIIRS375" or not a.get("fecha_utc"):
            continue
        try:
            dt = datetime.strptime(a["fecha_utc"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        out.setdefault(a["volcano"], []).append((dt, a))
    return out


def candidatos(vol, alertas, control=False):
    recs = json.load(open(ROOT / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    filas = []
    for r in recs:
        if not es_v375(r) or r.get("distance_class") != "summit" or r.get("final_hotspot_source") != "test1_roi":
            continue
        if r["datetime_utc"] < DESDE:
            continue
        if control and r.get("diag_n_first_pass_pixels") != 0:
            continue
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        cerca = [(abs((m - dt).total_seconds()) / 60, a) for m, a in alertas.get(vol, [])
                 if abs((m - dt).total_seconds()) <= DT_MAX_MIN * 60]
        if not cerca:
            continue
        dmin, a = min(cerca, key=lambda x: x[0])
        pc = r.get("primary_cluster") or {}
        filas.append({
            "volcan": vol, "pasada_utc": r["datetime_utc"], "sensor": r["sensor"],
            "clase": "control_fp0" if control else "cat_b",
            "regimen": "nuevo" if r["datetime_utc"] >= CORTE else "viejo",
            "pc_n": pc.get("n_pixels"), "pc_vrp": pc.get("vrp_mw"), "pc_dist_km": pc.get("centroid_dist_km"),
            "t_bg_k": r.get("t_bg_k"), "n_first_pass": r.get("diag_n_first_pass_pixels"),
            "mirova": {"fecha_utc": a["fecha_utc"], "vrp_mw": a["vrp_mw"], "dist_km": a["dist_km"],
                       "source": a["source"], "dt_min": round(dmin, 1)},
        })
    filas.sort(key=lambda f: (f["regimen"] != "nuevo", f["pasada_utc"]), reverse=False)
    # nuevo primero (False < True), y dentro de cada régimen los más recientes primero
    nuevo = sorted([f for f in filas if f["regimen"] == "nuevo"], key=lambda f: f["pasada_utc"], reverse=True)
    viejo = sorted([f for f in filas if f["regimen"] == "viejo"], key=lambda f: f["pasada_utc"], reverse=True)
    return nuevo, viejo


def main():
    al = alertas_por_vol()
    sel = []
    for vol in CATB + ("Lascar",):
        control = vol == "Lascar"
        nuevo, viejo = candidatos(vol, al, control=control)
        elegidas = (nuevo + viejo)[:3]
        print(f"{vol:12s} candidatos nuevo={len(nuevo)} viejo={len(viejo)} → elegidas {len(elegidas)} "
              f"({sum(1 for e in elegidas if e['regimen']=='nuevo')} del régimen nuevo)")
        for e in elegidas:
            print(f"   {e['pasada_utc']} {e['sensor']:13s} {e['regimen']:5s} pc {e['pc_n']}px {e['pc_vrp']} MW a {e['pc_dist_km']} km · "
                  f"fp {e['n_first_pass']} · MIROVA {e['mirova']['vrp_mw']} MW @ {e['mirova']['dist_km']} km ({e['mirova']['source']}, Δt {e['mirova']['dt_min']} min)")
        sel.extend(elegidas)
    (Path(__file__).parent / "pasadas_paso0.json").write_text(json.dumps(sel, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(sel)} pasadas → pasadas_paso0.json")


if __name__ == "__main__":
    main()
