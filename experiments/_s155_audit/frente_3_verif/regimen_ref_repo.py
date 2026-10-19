#!/usr/bin/env python3
"""Sensibilidad: corridas C0 y K con la referencia del REPO (snapshot del 14-oct, sin el refresco del cron).
Sirve para ver si los numeros del auditor salen de esa referencia y no de la que el cron usara hoy."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import simular_cron as sc
R = sc.REPO / "data/mirova_reference"
for reg in ["C0", "K"]:
    d = sc.correr(f"{reg}_ref_repo", raiz=sc.AQUI / f"raiz_{reg}",
                  cons=str(R / "mirova_v1_snapshot/registro_vrp_consolidado.csv"),
                  ocr=str(R / "mirova_v1_snapshot/registro_vrp_ocr.csv"),
                  hist=str(R / "union_historica/consolidado_filas_perdidas.csv"))
    print("RESUMEN", reg, json.dumps({s: (r["n_noches"], r["recall_crater_pct"]) for s, r in d["recall"].items()}),
          json.dumps({s: (x["n_neg_limpio"], x["falsas_pub_pct"]) for s, x in d["falsas_publicaciones"]["por_sensor"].items()}),
          "Tupungatito", d["magnitud_ratio_by_vol"].get("Tupungatito"), "Chillan", d["magnitud_ratio_by_vol"].get("NevadosDeChillan"))
