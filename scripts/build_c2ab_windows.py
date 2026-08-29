"""S118 C2 A/B — constructor de ventanas dirigidas para el reproc de los gates intra-radio.

POR QUÉ (fenómeno → mecanismo): el A/B de los gates intra-radio decide por "robo de
cluster espacial" en volcanes FOCALES durante noches MIROVA-confirmadas. Para observar
ese robo necesitamos reprocesar exactamente las noches donde MIROVA reportó actividad
(clusters de fechas ALERTA) + una muestra RUTINA de control. NO historia full ciega:
ventanas estrechas (≤14 días) evitan el timeout por descargas LANCE lentas (A15/A64/A26),
patrón validado en reproc-s112.

Salida: experiments/_s118_c2ab/windows.json con el `include` del matrix de GH Actions
(producto profiles × volcán × ventana). Reproducible y determinista (S91: ningún número
ni fecha transcrito a mano; este script es la fuente de verdad).

Loader canónico: pipeline/mirova_csv_loader.py (resuelve A11/A14/A48/F-B2).
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# stdout Windows default cp1252 no imprime Unicode (regla encoding del proyecto);
# reconfigure no re-envuelve el stream (patrón S118 analyze.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

# --- Config (todo explícito; cambiarlo acá, no a mano en el yaml) ---
PROFILES = [
    "_c2ab_baseline",   # path_d ON,  2pass ON   (= operacional, aislado)
    "_c2ab_pathd_off",  # path_d OFF, 2pass ON
    "_c2ab_2pass_off",  # path_d ON,  2pass OFF
    "_c2ab_both_off",   # path_d OFF, 2pass OFF   (clon-literal puro)
]
# 11 Tier A. Régimen (A21/R2_GATES_BY_REGIME) — solo para anotar; el reproc corre todos.
FOCAL = ["Lascar", "Lastarria", "Isluga", "PlanchonPeteroa", "PuyehueCordonCaulle"]
NEVADO = ["Llaima", "Copahue", "Villarrica", "NevadosDeChillan", "Tupungatito", "Chaiten"]
TIER_A = FOCAL + NEVADO

CLUSTER_GAP_DAYS = 7      # gap > este valor inicia un cluster ALERTA nuevo
PAD_DAYS = 2             # padding a cada lado del cluster
MAX_CHUNK_DAYS = 14      # cota dura por job (anti-timeout)
# Por volcán: top-N chunks de ≤14 días MÁS DENSOS en noches ALERTA. Los focales
# (Láscar/Lastarria) están casi continuamente activos → un mega-cluster de meses;
# muestrear los chunks más densos basta para observar robo de cluster (no historia
# full ciega). 4 alerta + 1 rutina ≤ 5/vol × 11 × 4 profiles = ≤220 jobs (< 256).
MAX_ALERTA_CHUNKS = 4

# S126 fix — los dos canales del ground truth tienen que salir del MISMO snapshot.
# Antes `CONS` apuntaba al snapshot y `OCR` a una copia suelta un nivel más arriba que
# quedó congelada el 2026-03-28 (236 filas) mientras el snapshot llega al 2026-08-24
# (888 filas), porque `audit-weekly.yml:57` sólo refresca el del snapshot. El script
# estaba construyendo las ventanas del A/B con cinco meses menos de canal OCR: 844
# fechas ALERTA en vez de 903 sobre los 11 Tier A (+59, y +11 en Planchón-Peteroa).
# El canal OCR NO es validación del consolidado sino COMPLEMENTO (A11), así que lo que
# falta no se recupera por el otro lado. Guard: tests/test_ground_truth_mismo_snapshot_s126.py
_SNAP = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot"
CONS = _SNAP / "registro_vrp_consolidado.csv"
OCR = _SNAP / "registro_vrp_ocr.csv"
OUT_DIR = REPO / "experiments" / "_s118_c2ab"


def _alerta_dates(volcano: str) -> list[date]:
    """Fechas (UTC) únicas con ALERTA MIROVA para el volcán, ordenadas."""
    recs = load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=volcano)
    days = set()
    for r in recs:
        fu = r.get("fecha_utc")
        if not fu:
            continue
        try:
            days.add(datetime.strptime(str(fu)[:10], "%Y-%m-%d").date())
        except ValueError:
            continue
    return sorted(days)


def _cluster(days: list[date]) -> list[tuple[date, date, int]]:
    """Agrupa fechas en clusters (gap > CLUSTER_GAP_DAYS). Devuelve (ini, fin, n_dias)."""
    if not days:
        return []
    clusters = []
    start = prev = days[0]
    n = 1
    for d in days[1:]:
        if (d - prev).days > CLUSTER_GAP_DAYS:
            clusters.append((start, prev, n))
            start = d
            n = 1
        else:
            n += 1
        prev = d
    clusters.append((start, prev, n))
    return clusters


def _split_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Parte una ventana en sub-chunks de ≤ MAX_CHUNK_DAYS (cota anti-timeout)."""
    out = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=MAX_CHUNK_DAYS - 1), end)
        out.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return out


def _rutina_window(days: list[date]) -> tuple[date, date] | None:
    """Ventana RUTINA de control: punto medio del mayor hueco ALERTA-free, ±7 días.

    Determinista (S91). Si hay <2 fechas ALERTA no hay hueco interno → None.
    """
    if len(days) < 2:
        return None
    gaps = [(days[i + 1] - days[i], days[i], days[i + 1]) for i in range(len(days) - 1)]
    gaps.sort(key=lambda g: (g[0].days, g[1]))  # mayor gap; desempate por fecha (determinista)
    biggest = gaps[-1]
    mid = biggest[1] + timedelta(days=biggest[0].days // 2)
    return (mid - timedelta(days=3), mid + timedelta(days=3))  # 7 días, dentro del hueco


def build() -> dict:
    include = []
    summary = {}
    for vol in TIER_A:
        days = _alerta_dates(vol)
        day_set = set(days)
        clusters = _cluster(days)
        # Generar TODOS los chunks ≤14d (split de cada cluster con padding), luego
        # rankear por densidad de noches ALERTA y quedarnos con los top-N. Esto acota
        # el matrix y prioriza las ventanas más informativas para el robo de cluster.
        candidate_chunks = []  # (start, end, n_alerta_dentro)
        for (ci, cf, _n) in clusters:
            wi, wf = ci - timedelta(days=PAD_DAYS), cf + timedelta(days=PAD_DAYS)
            for (cs, ce) in _split_chunks(wi, wf):
                n_in = sum(1 for d in day_set if cs <= d <= ce)
                candidate_chunks.append((cs, ce, n_in))
        candidate_chunks.sort(key=lambda c: (c[2], c[0]), reverse=True)  # densidad; desempate fecha
        kept = candidate_chunks[:MAX_ALERTA_CHUNKS]
        dropped = candidate_chunks[MAX_ALERTA_CHUNKS:]

        windows = [(cs, ce, "alerta") for (cs, ce, _n) in kept]
        rut = _rutina_window(days)
        # Solo agregar RUTINA si NO se solapa con ninguna ALERTA mantenida: en focales
        # continuamente activos no existe período quieto → un "control" solapado sería
        # ALERTA mal etiquetada (y reproc redundante). Lo omitimos en ese caso.
        if rut and not any(rut[0] <= ce and cs <= rut[1] for (cs, ce, _k) in windows):
            windows.append((rut[0], rut[1], "rutina"))

        for (cs, ce, kind) in windows:
            for prof in PROFILES:
                include.append({
                    "profile": prof,
                    "volcano": vol,
                    "start": cs.isoformat(),
                    "end": ce.isoformat(),
                    "kind": kind,
                    "regime": "focal" if vol in FOCAL else "nevado",
                })
        summary[vol] = {
            "n_alerta_dates": len(days),
            "n_clusters_total": len(clusters),
            "n_chunks_candidate": len(candidate_chunks),
            "n_chunks_kept": len(kept),
            "n_chunks_dropped": len(dropped),  # NO silencioso (log explícito)
            "n_windows": len(windows),
        }
    return {"include": include, "summary": summary,
            "config": {"CLUSTER_GAP_DAYS": CLUSTER_GAP_DAYS, "PAD_DAYS": PAD_DAYS,
                       "MAX_CHUNK_DAYS": MAX_CHUNK_DAYS, "MAX_ALERTA_CHUNKS": MAX_ALERTA_CHUNKS,
                       "profiles": PROFILES}}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = build()
    out = OUT_DIR / "windows.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    n_jobs = len(data["include"])
    print(f"windows.json escrito: {out}")
    print(f"TOTAL jobs (matrix include): {n_jobs}  (cap GH Actions = 256)")
    if n_jobs > 256:
        print("  *** ADVERTENCIA: supera 256 — bajar MAX_ALERTA_CHUNKS ***")
    print("\nPor volcán (régimen | fechas ALERTA | chunks cand/kept/drop | ventanas):")
    for vol, s in data["summary"].items():
        reg = "focal " if vol in FOCAL else "nevado"
        drop = f" DROP={s['n_chunks_dropped']}" if s["n_chunks_dropped"] else ""
        print(f"  {vol:22s} {reg} | alertas={s['n_alerta_dates']:4d} | "
              f"chunks {s['n_chunks_candidate']:2d}/{s['n_chunks_kept']}{drop} | "
              f"ventanas={s['n_windows']}")


if __name__ == "__main__":
    main()
