# -*- coding: utf-8 -*-
"""¿El tablero publica el cumulo topado D9 que K produjo (PCC 2026-10-03 01:25 MODIS_TERRA) y los dos
records C0 residuales de PCC con etiqueta summit (2026-09-28 01:25 y 2026-10-10 01:05)? Predicado node
de banco_paridad (isSummit && isValid && !isThermalArtifact && display > 0). P2: control de identidad
del predicado afirmado antes de usarlo."""
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
assert B.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
recs = B.cargar_nuestros(coords, inner, ("2026-09-28", "2026-10-10"))
for r in recs:
    if r["vol"] == "PuyehueCordonCaulle" and r["b"] == "MODIS" and r["dt"].strftime("%Y-%m-%d %H:%M") in ("2026-10-03 01:25", "2026-09-28 01:25", "2026-10-10 01:05"):
        print(r["dt"], "dc", r["dc"], "pc", r["pc_vrp"], r["pc_dist"], "display", r["disp"], "publica", r["pub"])
