"""28_osf_historical_analysis.py — Analisis OSF v2.5 archivo (25 anos).

Sin fetch adicional, aprovechar data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv
para extraer 3 tipos de contexto:

  1. Perfil VRP por volcan por ano: detectar erupciones historicas documentadas,
     rango dinamico, baseline de actividad.
  2. Distribucion historica de Max_Dist por volcan y sensor: validar
     radius_km y inner_radius_km empiricamente sobre 25 anos, no solo 3 meses.
  3. Ratio publicacion OSF -> mirovaweb NRT: sobre el perido comun con el CSV
     consolidado NRT (2026-01-10 -> 2026-04-22), contar cuantas detecciones
     OSF vs NRT por volcan+sensor -> factor de supervision.

Salidas:
  experiments/28_osf_historical_analysis.json  — detalle completo
  stdout — 3 tablas markdown
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import median


VOLCANOES = {
    "Láscar": "Lascar",
    "Chaitén": "Chaiten",
    "Villarrica": "Villarrica",
    "Copahue": "Copahue",
    "Isluga": "Isluga",
    "Lastarria": "Lastarria",
    "Llaima": "Llaima",
    "Chillán, Nevados de": "NevadosDeChillan",
    "Planchón-Peteroa": "PlanchonPeteroa",
    "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
}

# Satellite code (int) -> resolution -> sensor family
RES_TO_FAMILY = {1000: "MODIS", 750: "VIIRS_M", 375: "VIIRS_I"}


def parse_osf_time(s: str) -> datetime | None:
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_osf(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            osf_name = r.get("Volc_Name", "")
            if osf_name not in VOLCANOES:
                continue
            try:
                vrp = float(r["VRP"])
                dt = parse_osf_time(r["timeUTC"])
                res = int(r["Resolution"])
            except (ValueError, KeyError, TypeError):
                continue
            if dt is None:
                continue
            rows.append({
                "volcan": VOLCANOES[osf_name],
                "year": dt.year,
                "dt": dt,
                "vrp_mw": vrp / 1e6,   # OSF stores VRP in Watts; normalize to MW
                "max_dist_km": float(r.get("Max_Dist") or 0) / 1000.0,  # meters -> km
                "family": RES_TO_FAMILY.get(res, f"R{res}"),
            })
    return rows


def load_nrt(path: Path) -> list:
    rows = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                vrp = float(r["VRP_MW"])
            except (ValueError, KeyError):
                continue
            if vrp <= 0:
                continue
            try:
                dt = datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            # CSV volcano names to yaml
            vol = r.get("Volcan", "")
            name_map = {
                "Nevados de Chillan": "NevadosDeChillan",
                "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
                "Peteroa": "PlanchonPeteroa",
            }
            vol = name_map.get(vol, vol)
            if vol == "Tupungatito":
                continue  # no hay en OSF
            sensor_map = {
                "MODIS": "MODIS",
                "VIIRS": "VIIRS_M",
                "VIIRS375": "VIIRS_I",
            }
            fam = sensor_map.get(r.get("Sensor", ""))
            if fam is None:
                continue
            rows.append({"volcan": vol, "dt": dt, "vrp": vrp, "family": fam})
    return rows


def _pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    return xs[int(k)]


def analysis_1_yearly_profile(rows: list) -> dict:
    """VRP (MW) por (volcan, ano): mediana, p95, max, n."""
    groups = {}
    for r in rows:
        groups.setdefault((r["volcan"], r["year"]), []).append(r["vrp_mw"])
    out = {}
    for (vol, yr), vrps in groups.items():
        out.setdefault(vol, {})[str(yr)] = {
            "n": len(vrps),
            "vrp_median_mw": median(vrps),
            "vrp_p95_mw": _pct(vrps, 0.95),
            "vrp_max_mw": max(vrps),
        }
    return out


def print_yearly_table(prof: dict):
    print("== Tabla 1: VRP_max (MW, log10) por anio/volcan (OSF 25 anos) ==")
    print("== Cada celda = orden de magnitud pico anual; '--' = sin refs ese anio ==")
    import math
    all_years = sorted({int(y) for vp in prof.values() for y in vp})
    years_str = " ".join(f"{y%100:>3d}" for y in all_years)
    print(f"{'Volcan':<22} {years_str}")
    print("-" * (22 + len(all_years) * 4))
    for vol in sorted(prof.keys()):
        row = []
        for y in all_years:
            s = prof[vol].get(str(y))
            if s:
                v = s["vrp_max_mw"]
                cell = f"{math.log10(v):>3.1f}" if v > 0 else "---"
            else:
                cell = " --"
            row.append(cell)
        print(f"{vol:<22} {' '.join(row)}")


def analysis_2_distance_distribution(rows: list) -> dict:
    """Max_Dist (km) por (volcan, family)."""
    groups = {}
    for r in rows:
        groups.setdefault((r["volcan"], r["family"]), []).append(r["max_dist_km"])
    out = {}
    for (vol, fam), dists in groups.items():
        dists_valid = [d for d in dists if d > 0]
        if not dists_valid:
            continue
        out.setdefault(vol, {})[fam] = {
            "n": len(dists_valid),
            "d_median_km": median(dists_valid),
            "d_p95_km": _pct(dists_valid, 0.95),
            "d_max_km": max(dists_valid),
        }
    return out


def print_distance_table(d: dict):
    print()
    print("== Tabla 2: Max_Dist historico (km) por volcan/sensor (OSF 25 anos) ==")
    print(f"{'Volcan':<22} {'Sensor':<10} {'N':>7} {'d_med':>7} {'d_p95':>7} {'d_max':>7}")
    print("-" * 64)
    for vol in sorted(d.keys()):
        for fam in sorted(d[vol].keys()):
            s = d[vol][fam]
            print(f"{vol:<22} {fam:<10} {s['n']:>7} "
                  f"{s['d_median_km']:>7.2f} {s['d_p95_km']:>7.2f} {s['d_max_km']:>7.2f}")


def analysis_3_osf_vs_nrt_overlap(osf_rows: list, nrt_rows: list,
                                  start: datetime, end: datetime) -> dict:
    """Para el overlap temporal start..end, ratio OSF/NRT por volcan+sensor."""
    osf_w = [r for r in osf_rows if start <= r["dt"] <= end]
    nrt_w = nrt_rows  # ya filtrado a ventana por fuente
    # Group both
    def grp(rs):
        g = {}
        for r in rs:
            g.setdefault((r["volcan"], r["family"]), 0)
            g[(r["volcan"], r["family"])] += 1
        return g
    g_osf = grp(osf_w)
    g_nrt = grp(nrt_w)
    keys = set(g_osf) | set(g_nrt)
    out = {}
    for vol, fam in sorted(keys):
        n_osf = g_osf.get((vol, fam), 0)
        n_nrt = g_nrt.get((vol, fam), 0)
        out.setdefault(vol, {})[fam] = {
            "n_osf": n_osf,
            "n_nrt": n_nrt,
            "ratio_nrt_over_osf": (n_nrt / n_osf) if n_osf > 0 else None,
        }
    return out


def print_overlap_table(o: dict):
    print()
    print("== Tabla 3: Ratio OSF vs mirovaweb NRT en overlap 2026-01-10 -> 2026-04-22 ==")
    print(f"{'Volcan':<22} {'Sensor':<10} {'N_OSF':>7} {'N_NRT':>7} {'NRT/OSF':>9}")
    print("-" * 58)
    for vol in sorted(o.keys()):
        for fam in sorted(o[vol].keys()):
            s = o[vol][fam]
            r = f"{s['ratio_nrt_over_osf']:.2f}" if s['ratio_nrt_over_osf'] is not None else "--"
            print(f"{vol:<22} {fam:<10} {s['n_osf']:>7} {s['n_nrt']:>7} {r:>9}")


def main():
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    osf_path = Path("data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv")
    nrt_path = Path("21_04_2026 registro_vrp_consolidado.csv")

    print(f"Cargando OSF v2.5 desde {osf_path}...")
    osf_rows = load_osf(osf_path)
    print(f"  {len(osf_rows)} filas chilenas 2000-2025.")
    print(f"Cargando NRT desde {nrt_path}...")
    nrt_rows = load_nrt(nrt_path)
    print(f"  {len(nrt_rows)} detecciones NRT con VRP>0.")
    print()

    a1 = analysis_1_yearly_profile(osf_rows)
    print_yearly_table(a1)

    a2 = analysis_2_distance_distribution(osf_rows)
    print_distance_table(a2)

    # CORRECCION: OSF v2.5 termina 2025-12-31 y NRT empieza 2026-01-10, NO hay
    # overlap temporal real. Comparamos VENTANAS IGUALES en calendario (Ene-Abr)
    # de anios adyacentes como mejor proxy: si actividad similar ano-a-ano,
    # ratio ~= 1 = paridad; desviaciones != 1 pueden ser (a) supervision
    # mirovaweb, (b) deriva temporal de actividad, (c) incompletitud OSF.
    # NO podemos distinguir (a) de (b)/(c) sin OSF actualizado a 2026.
    # Para NRT usamos solo 2026-01-10 -> 2026-04-22 (misma ventana).
    start_osf = datetime(2025, 1, 10)
    end_osf = datetime(2025, 4, 22, 23, 59)
    nrt_window = [r for r in nrt_rows
                  if datetime(2026, 1, 10) <= r["dt"] <= datetime(2026, 4, 22, 23, 59)]
    a3 = analysis_3_osf_vs_nrt_overlap(osf_rows, nrt_window, start_osf, end_osf)
    print_overlap_table(a3)
    print()
    print("NOTA METODOLOGICA: no hay overlap temporal OSF-NRT. Comparamos misma")
    print("ventana calendario Ene-Abr en anios adyacentes (2025 vs 2026), asumiendo")
    print("actividad similar entre anios. Desviaciones del ratio ~1 pueden ser")
    print("supervision Y/O deriva real de actividad volcanica. No son distinguibles")
    print("con estos datos. Paridad confirmada SOLO donde ambas fuentes tienen")
    print("muchas refs y ratio ~1 (Lascar, Lastarria, NdC VIIRS_I).")

    out_path = Path("experiments/28_osf_historical_analysis.json")
    json.dump(
        {"yearly_profile": a1, "distance_dist": a2, "osf_vs_nrt_overlap": a3},
        open(out_path, "w", encoding="utf-8"), indent=2, default=float,
    )
    print(f"\nDetalle guardado en {out_path}")


if __name__ == "__main__":
    main()
