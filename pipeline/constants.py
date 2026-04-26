"""Constantes físicas centralizadas (S23 T17 audit followup).

Antes: SIGMA, C1, C2 Planck duplicados en 3-4 archivos process_*.py.
Ahora: una sola definición canónica importada por todos.

Fuentes: CODATA 2018.
"""
from __future__ import annotations

# Stefan-Boltzmann constant — W/m²/K⁴
# CODATA 2018: σ = 5.670374419e-8 (exacto desde 2019 SI redefinition).
# Usado en VRP_TIR (Stefan-Boltzmann puro, Coppola 2024 cap Springer Eq.16,
# Aveni 2024 RSE Eq.5).
SIGMA = 5.670374419e-8

# Planck radiation constants — para conversión radiancia ↔ BT (banda térmica).
# B(λ, T) = C1 / [λ⁵ · (exp(C2 / (λ·T)) - 1)]
# C1 = 2hc² en W·µm⁴/m²/sr — CODATA 2018: 1.191042869e8 (redondeado).
# C2 = hc/k_B en µm·K — CODATA 2018: 14387.769 (redondeado a 14388).
C1 = 1.191042e8
C2 = 14388.0

# Aliases para retrocompatibilidad con process_viirs_mod.py (que usaba
# C1_PLANCK / C2_PLANCK localmente).
C1_PLANCK = C1
C2_PLANCK = C2
