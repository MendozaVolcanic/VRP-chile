"""52_aveni_tir_poc.py — POC Aveni 2025 GRL Eq.9 sobre Villarrica.

Standalone POC: ¿la fórmula VRP_TIR de Aveni 2025 capturaría la señal lava
lake Villarrica (0.05-0.21 MW MIROVA NRT, sub-pixel <600K) que nuestro
pipeline MIR puro pierde?

Aveni 2025 GRL Eq.9 (p.4):
    VRP_TIR = A_pix · k_TIR · ΔL_TIR

donde:
    A_pix    = 140 625 m² (VIIRS I-band 375m)
    k_TIR    = 60.17 sr·μm  (banda I5 11.45 μm, valor empírico Aveni)
    ΔL_TIR   = L(BT_hot) − L(BT_bg)  [W·m⁻²·sr⁻¹·μm⁻¹]
    L(T)     = c1λ⁻⁵ / (exp(c2/(λT))−1)  (Planck en banda)

con c1λ = 1.191e8 W·m⁻²·sr⁻¹·μm⁻¹·μm⁵, c2 = 14387.7 μm·K, λ = 11.45 μm.

Comparación: VRP_TIR_Aveni vs VRP MIROVA NRT (CSV consolidado) por ref Villarrica.

NO integra al pipeline. Reporta viabilidad:
- Si VRP_TIR_Aveni ~ VRP MIROVA → método podría reemplazar/complementar.
- Si VRP_TIR_Aveni ≪ VRP MIROVA → señal sub-pixel también escapa Aveni.
- Si VRP_TIR_Aveni ≫ VRP MIROVA → Aveni sobre-estima sin floor adecuado.
"""
from __future__ import annotations
import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from experiments.forense_h17_replicable import _parse_dt_csv, _parse_dt_record, sensor_match  # noqa

# Constantes Planck en unidades μm
C1_LAMBDA = 1.191e8         # W·m⁻²·sr⁻¹·μm⁻¹·μm⁵  (= 2hc² × 1e24)
C2 = 14387.7                # μm·K  (= hc/k × 1e6)
LAMBDA_I5 = 11.45           # μm

# Constantes Aveni 2025 GRL
A_PIX_VIIRS_I = 140625      # m² (375 m × 375 m)
K_TIR = 60.17               # sr·μm — Aveni 2025 Eq.9 p.4

TOLERANCE = timedelta(minutes=60)


def planck_radiance_um(T_K: float) -> float:
    """Radiancia espectral en banda I5 a temperatura T_K, en W·m⁻²·sr⁻¹·μm⁻¹."""
    if T_K is None or T_K <= 0:
        return 0.0
    expo = C2 / (LAMBDA_I5 * T_K)
    if expo > 700:
        return 0.0
    return (C1_LAMBDA / LAMBDA_I5**5) / (math.exp(expo) - 1)


def vrp_tir_aveni(t_hot_K: float, t_bg_K: float, n_pix: int = 1) -> float:
    """VRP TIR según Aveni 2025 Eq.9, en MW (output convertido de W)."""
    L_hot = planck_radiance_um(t_hot_K)
    L_bg = planck_radiance_um(t_bg_K)
    delta_L = max(L_hot - L_bg, 0.0)
    return A_PIX_VIIRS_I * K_TIR * delta_L * n_pix * 1e-6  # W → MW


def vrp_tir_stefan_boltzmann(t_hot_K: float, t_bg_K: float, n_pix: int = 1) -> float:
    """VRP TIR Stefan-Boltzmann puro (lo que hacemos hoy), en MW."""
    if t_hot_K is None or t_bg_K is None:
        return 0.0
    sigma = 5.67e-8
    delta = max(t_hot_K**4 - t_bg_K**4, 0.0)
    return sigma * A_PIX_VIIRS_I * delta * n_pix * 1e-6


def main():
    # 1. Refs MIROVA Villarrica
    csv = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    df = pd.read_csv(csv)
    refs = df[(df.Volcan == "Villarrica") & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()
    refs["dt"] = refs["Fecha_Satelite_UTC"].apply(_parse_dt_csv)
    print(f"# Refs MIROVA Villarrica: {len(refs)}")
    print(f"# VRP_MW range: {refs.VRP_MW.min():.2f} - {refs.VRP_MW.max():.2f} (median {refs.VRP_MW.median():.2f})")
    print()

    # 2. Records nuestros
    records = json.loads((ROOT / "data" / "mirova_equivalent" / "Villarrica.json").read_text())["records"]

    # 3. Match cada ref a su record
    rows = []
    for _, ref in refs.iterrows():
        ref_dt = ref["dt"]
        ref_sensor_csv = ref["Sensor"]  # 'VIIRS375'
        ref_vrp = ref["VRP_MW"]
        # Buscar record dentro de ±60min y mismo sensor
        match = None
        for rec in records:
            try:
                rec_dt = _parse_dt_record(rec["datetime_utc"])
            except Exception:
                continue
            if abs((rec_dt - ref_dt).total_seconds()) > TOLERANCE.total_seconds():
                continue
            if not sensor_match(ref_sensor_csv, rec["sensor"]):
                continue
            match = rec
            break
        rows.append((ref_dt, ref_vrp, match))

    # 4. Tabla comparativa
    print("| Fecha (UTC)        | VRP MIROVA | VRP nuestro (MIR) | t_max | t_bg  | n_anom | VRP_TIR Aveni | VRP_TIR SB | Aveni/MIROVA |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    n_aveni_match = 0
    for dt, mirova_vrp, rec in rows:
        if rec is None:
            print(f"| {dt} | {mirova_vrp:.3f} | (no record) | - | - | - | - | - | - |")
            continue
        vrp_mir = rec.get("vrp_mw", 0) or 0
        t_max = rec.get("t_max_k")
        t_bg = rec.get("t_bg_k")
        n_anom = rec.get("n_anomalous_pixels", 0) or 0
        # VRP_TIR sobre t_max,t_bg (proxy: pixel más caliente del ROI; no
        # sabemos cuál es el lava lake exacto, pero t_max es el candidato).
        # Si n_anom>0 multiplica; si n_anom=0 reportamos n=1 como "si fuera"
        n_test = max(n_anom, 1)
        vrp_aveni = vrp_tir_aveni(t_max, t_bg, n_test)
        vrp_sb = vrp_tir_stefan_boltzmann(t_max, t_bg, n_test)
        ratio = vrp_aveni / mirova_vrp if mirova_vrp > 0 else float('nan')
        if 0.5 <= ratio <= 2.0:
            n_aveni_match += 1
        t_max_s = f"{t_max:.1f}" if t_max else "?"
        t_bg_s = f"{t_bg:.1f}" if t_bg else "?"
        print(f"| {dt} | {mirova_vrp:.3f} | {vrp_mir:.3f} | {t_max_s} | {t_bg_s} | {n_anom} | {vrp_aveni:.3f} | {vrp_sb:.3f} | {ratio:.2f} |")

    print()
    print(f"# Aveni dentro de [0.5, 2.0]× MIROVA: {n_aveni_match}/{len(rows)}")
    print()
    print("# Sanity: ΔBT esperado para VRP_TIR_Aveni = 0.1 MW (mediana MIROVA Villarrica) con n_pix=1, T_bg=250K:")
    # Resolver: 0.1e6 = 140625 * 60.17 * delta_L  →  delta_L = 1.18e-2 W·m⁻²·sr⁻¹·μm⁻¹
    target_delta_L = 0.1e6 / (A_PIX_VIIRS_I * K_TIR)
    L_bg_250 = planck_radiance_um(250)
    L_hot_target = L_bg_250 + target_delta_L
    # Invertir Planck para obtener T_hot
    # L = (C1_LAMBDA / λ⁵) / (exp(C2/(λT))-1)
    # exp(C2/(λT)) = 1 + (C1_LAMBDA / λ⁵) / L
    # T = C2 / (λ * ln(1 + (C1_LAMBDA/λ⁵)/L))
    if L_hot_target > 0:
        T_hot = C2 / (LAMBDA_I5 * math.log(1 + (C1_LAMBDA / LAMBDA_I5**5) / L_hot_target))
        print(f"  → T_bg=250K, ΔL={target_delta_L:.4e}, T_hot≈{T_hot:.1f}K → ΔBT≈{T_hot-250:.2f} K")


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
