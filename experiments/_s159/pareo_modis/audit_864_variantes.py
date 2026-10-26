# -*- coding: utf-8 -*-
"""Corre auto_audit_weekly.main() del espejo en el commit del run que abrio #864 (2e1bc0e31), con la fecha
congelada a la del run, en las tres variantes de pareo. La salida va a --out, nunca al repo.

Pregunta 1: si el pareo cambiara algo de #864, lo veria? Si: comparo latest.json completo (flags, recall,
magnitud, protegidas, falsas, n_misma_pasada) entre variantes.
Pregunta 2: instrumento vivo: la variante "hoy" debe reproducir los flags de #864 tal cual (control de
reproduccion), y las variantes deben mover algo que se sabe que mueven (n_neg_limpio del banco).
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import variantes  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--raiz", required=True)
ap.add_argument("--variante", required=True, choices=["hoy", "ancha", "orbita"])
ap.add_argument("--hoy", default="2026-10-19T16:29:28")
ap.add_argument("--out", required=True)
a = ap.parse_args()
bp, aaw = variantes.cargar(a.raiz)
reg = {}
variantes.aplicar(bp, aaw, a.variante, reg)

T = datetime.fromisoformat(a.hoy).replace(tzinfo=timezone.utc)


class Congelada(datetime):
    @classmethod
    def now(cls, tz=None):
        return T if tz else T.replace(tzinfo=None)


aaw.datetime = Congelada
Path(a.out).mkdir(parents=True, exist_ok=True)
aaw.OUTDIR = a.out
aaw.main()
print("REGISTRO cadenas:", {k: (dict(v) if hasattr(v, "items") else v) for k, v in reg.items()})
