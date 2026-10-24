# -*- coding: utf-8 -*-
"""Verificador S158. Llama a auto_audit_weekly.evaluar_detector TAL CUAL (no a una copia de su lógica) sobre la
ventana de #864 y lee magnitud_publicada_by_vol_sensor de Tupungatito|VIIRS375, con dos fronteras de K.
Si da 0,266 con la frontera 2026-09-18, c_noche_audit.py reproduce el auto-audit por el mismo camino.

Uso: python -I v2_auto_audit_directo.py
"""
import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw  # noqa: E402

L = []
coords = aw._coords_por_volcan()
recs, _ = aw.cargar_records()
filas_ref = aw.cargar_filas_referencia()
alertas = aw.aplicar_d9(aw.alertas_mirova(), aw.REGLA_MINIMAS, filas_ref)
win = ("2026-08-20", "2026-10-19")
L.append(f"referencia {aw.CONS}; D-9 {aw.REGLA_MINIMAS}; ventana {win}")
for frontera in ("2026-09-18", "2025-01-01"):
    mir, _ = aw.noches_mirova(alertas, coords, win)
    nn = aw.nuestros_por_noche(recs, win, frontera)
    ev = aw.evaluar_detector(mir, nn["ours"], nn["vistos"], "K", frontera)
    m = ev["magnitud_publicada_by_vol_sensor"].get("Tupungatito|VIIRS375")
    L.append(f"frontera {frontera}: Tupungatito|VIIRS375 publicada {m}")
    L.append(f"   (por pc, ratio_by_vol Tupungatito: {ev['magnitud_ratio_by_vol'].get('Tupungatito')})")
txt = "\n".join(L)
print(txt)
(AQUI / "v2_auto_audit_directo_salida.txt").write_text(txt + "\n", encoding="utf-8")
