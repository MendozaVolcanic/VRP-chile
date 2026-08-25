# -*- coding: utf-8 -*-
"""S124 — Gráfica comparativa NdC: MIROVA (3 sensores) vs réplica vs foco Nicanor.

Pedido de Nicolás (2026-08-25): datos de NdC experimental desde junio, comparando
MIROVA vs mirova_equivalent (réplica) vs experimental_ndc_focus, en gráficas.

Tres paneles (uno por bucket de sensor: VIIRS375, VIIRS750, MODIS):
  - MIROVA: sus ALERTAS publicadas (estrellas rojas). Es TODO lo que MIROVA
    publica con magnitud — las noches RUTINA son VRP=0 por definición.
  - Réplica (mirova_equivalent): máximo nocturno de pc.vrp_mw con el MISMO filtro
    del dashboard (summit + centroide dentro del inner de 5 km). Es lo que Nicolás
    ve en la vista operacional.
  - Foco Nicanor (experimental_ndc_focus, solo VIIRS375): máximo nocturno summit
    con centroide a <=1 km del cráter (-36.867210, -71.378241). El laboratorio.

Escala log: las series cruzan 3 órdenes de magnitud (0.01-10 MW).
Fuente de verdad de los números del informe = este script (regla S91).
"""
import csv
import io
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
NIC = (-36.867210, -71.378241)   # cráter Nicanor (coordenada de Nicolás, S124)
INNER_KM = 5.0                   # inner operacional NdC (KML MIROVA)
START = "2026-06-01"


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def bucket(sensor: str) -> str:
    s = sensor or ""
    if "MODIS" in s:
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if "VIIRS" in s:
        return "VIIRS375"
    return "?"


def bucket_mirova(sensor: str) -> str:
    # El CSV del scraper usa VIIRS375 / VIIRS / MODIS; "VIIRS" pelado es 750m.
    s = (sensor or "").strip().upper()
    if s == "VIIRS375":
        return "VIIRS375"
    if s == "VIIRS":
        return "VIIRS750"
    if s == "MODIS":
        return "MODIS"
    return "?"


# ── MIROVA: alertas por (bucket, noche) ─────────────────────────────────────
mirova = defaultdict(dict)   # bucket -> {fecha: max VRP}
with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
    for r in csv.DictReader(fh):
        if r.get("Volcan") != "Nevados de Chillan":
            continue
        f = (r.get("Fecha_Satelite_UTC") or "")[:10]
        if f < START or "ALERTA" not in (r.get("Tipo_Registro") or ""):
            continue
        try:
            v = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if v <= 0:
            continue
        b = bucket_mirova(r.get("Sensor"))
        mirova[b][f] = max(mirova[b].get(f, 0), v)

# ── Réplica: filtro del dashboard, máximo nocturno por bucket ───────────────
replica = defaultdict(dict)
d = json.loads((ROOT / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    if f < START:
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or r.get("distance_class") != "summit":
        continue
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > INNER_KM:
        continue
    b = bucket(r.get("sensor"))
    replica[b][f] = max(replica[b].get(f, 0), v)

# ── Foco Nicanor: summit dentro de 1 km del cráter ──────────────────────────
foco = {}
fp = ROOT / "data/experimental_ndc_focus/NevadosDeChillan.json"
if fp.exists():
    d = json.loads(fp.read_text(encoding="utf-8"))
    for r in d["records"]:
        f = (r.get("datetime_utc") or "")[:10]
        if f < START:
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if v <= 0 or pc.get("centroid_lat") is None:
            continue
        if hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) > 1.0:
            continue
        foco[f] = max(foco.get(f, 0), v)

# ── Figura ──────────────────────────────────────────────────────────────────
def dts(dd):
    return [datetime.fromisoformat(x) for x in sorted(dd)]


fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
fig.suptitle("Nevados de Chillán — MIROVA vs réplica vs foco Nicanor (desde jun-2026)",
             fontsize=14, fontweight="bold")

for ax, b in zip(axes, ("VIIRS375", "VIIRS750", "MODIS")):
    rep = replica.get(b, {})
    if rep:
        xs = dts(rep)
        ax.plot(xs, [rep[x.strftime("%Y-%m-%d")] for x in xs], "o-", ms=4, lw=0.8,
                color="#4477aa", alpha=0.75,
                label=f"Réplica operacional (summit ≤{INNER_KM:.0f} km) — n={len(rep)}")
    if b == "VIIRS375" and foco:
        xs = dts(foco)
        ax.plot(xs, [foco[x.strftime("%Y-%m-%d")] for x in xs], "s-", ms=5, lw=1.2,
                color="#228833",
                label=f"Foco Nicanor (≤1 km, piso 0.005) — n={len(foco)}")
    mir = mirova.get(b, {})
    if mir:
        xs = dts(mir)
        ax.plot(xs, [mir[x.strftime("%Y-%m-%d")] for x in xs], "*", ms=15,
                color="#cc3311", mec="k", mew=0.5, zorder=5,
                label=f"MIROVA (alertas publicadas) — n={len(mir)}")
    ax.set_yscale("log")
    ax.set_ylabel("VRP (MW)")
    ax.set_title(b, loc="left", fontweight="bold")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    ax.axhline(0.02, color="#999", ls=":", lw=0.8)
    ax.text(0.995, 0.03, "piso operacional 0.02 MW", transform=ax.get_yaxis_transform(),
            ha="right", va="bottom", fontsize=7, color="#777")

axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
axes[-1].set_xlabel("2026")
fig.tight_layout()
out = Path(__file__).parent / "ndc_comparison_s124.png"
fig.savefig(out, dpi=150)
print(f"figura: {out}")

# ── Números del informe (fuente de verdad) ──────────────────────────────────
import statistics as st
print("\n=== resumen desde", START, "===")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    m, rep = mirova.get(b, {}), replica.get(b, {})
    print(f"{b}: MIROVA alertas={len(m)}  réplica noches={len(rep)}"
          + (f"  medRep={st.median(rep.values()):.3f}" if rep else ""))
print(f"foco: noches={len(foco)}"
      + (f"  med={st.median(foco.values()):.3f}  max={max(foco.values()):.3f}" if foco else ""))
comunes = [(f, mirova["VIIRS375"][f], foco[f]) for f in mirova.get("VIIRS375", {}) if f in foco]
print("noches comunes MIROVA-V375 ∩ foco:", [(f, mv, round(fv, 3)) for f, mv, fv in comunes])
