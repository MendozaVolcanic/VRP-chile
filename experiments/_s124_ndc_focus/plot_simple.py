# -*- coding: utf-8 -*-
"""S124 — Figura SIMPLE para Nicolás: qué mostró MIROVA vs qué detectamos nosotros.

Feedback de Nicolás sobre la figura anterior (3 paneles por sensor, escala log):
"me cuesta entender los gráficos". Esta versión responde dos preguntas, una por
panel, en el sensor donde está la historia (VIIRS 375 m — TODAS las alertas que
MIROVA publicó en NdC desde junio son de ese sensor):

  Panel A — ¿QUIÉN detectó cada noche?   (tres filas de puntos, sin números)
  Panel B — ¿CUÁNTA energía?             (escala lineal, MW)

MODIS y VIIRS750 se excluyen a propósito: MIROVA no publicó ninguna alerta con
ellos en este período, y nuestra réplica MODIS ahí sobre-estima (tema conocido
A82) — mezclarlos era lo que hacía ilegible la figura anterior.

Fuente de verdad de los números del informe = este script (regla S91).
Uso:  python plot_simple.py [ruta_json_foco]   (default: data/ del repo)
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
NIC = (-36.867210, -71.378241)
START = "2026-06-01"
FOCO_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/experimental_ndc_focus/NevadosDeChillan.json"


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


# ── MIROVA: alertas VIIRS375 por noche ──────────────────────────────────────
mirova = {}
with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
    for r in csv.DictReader(fh):
        if r.get("Volcan") != "Nevados de Chillan":
            continue
        f = (r.get("Fecha_Satelite_UTC") or "")[:10]
        if f < START or "ALERTA" not in (r.get("Tipo_Registro") or ""):
            continue
        if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
            continue
        try:
            v = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if v > 0:
            mirova[f] = max(mirova.get(f, 0), v)

# ── Réplica operacional: VIIRS375, filtro del dashboard ─────────────────────
replica = {}
d = json.loads((ROOT / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    s = r.get("sensor") or ""
    if f < START or "VIIRS" not in s or "750" in s:
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or r.get("distance_class") != "summit":
        continue
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > 5.0:
        continue
    replica[f] = max(replica.get(f, 0), v)

# ── Píxeles FRÍOS por noche (proxy PARCIAL de nube) ─────────────────────────
# ⚠️ QUÉ MIDE ESTO REALMENTE (S124, a raíz de que Nicolás no reconocía las
# semanas de tormenta): `n_cloud_masked` cuenta los píxeles del ROI con
# I05 < 260 K. Eso detecta nube ALTA Y FRÍA (cirros, topes convectivos) pero
# NO la nube baja de una tormenta invernal, cuyo tope irradia entre −10 y 0 °C
# (263–273 K) y por lo tanto pasa como "despejado". Encima, a esta altitud el
# terreno nevado irradia en ese mismo rango: en el 76 % de las pasadas que este
# proxy llama despejadas el fondo está bajo 0 °C, donde nube baja y nieve son
# INDISTINGUIBLES para un umbral único de temperatura (mismo mecanismo que A68).
#
# Además el DENOMINADOR no se persiste: el pipeline guarda cuántos píxeles
# enmascaró pero no cuántos tenía el ROI, así que un porcentaje exacto no se
# puede reconstruir del JSON (por eso acá se grafica el CONTEO, no un %).
#
# El arreglo correcto NO es una API meteorológica (celdas de ~28 km, horaria,
# modelo y no observación) sino la máscara de nube OFICIAL del propio sensor
# —MOD35_L2 y CLDMSK_L2_VIIRS_*, que existen con versión NRT— que usa ~15
# tests espectrales diseñados justamente para separar nube de nieve.
PIX_ROI_I = (50.0 / 0.375) ** 2          # ROI 50x50 km en píxeles I-band nadir
despejado = {}
_d_op = json.loads((ROOT / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))
for r in _d_op["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    sen = r.get("sensor") or ""
    if f < START or "VIIRS" not in sen or "750" in sen:
        continue
    nc = r.get("n_cloud_masked")
    if nc is None:
        continue
    # conteo crudo de píxeles fríos; la MENOR de la noche (la pasada más limpia)
    prev = despejado.get(f)
    despejado[f] = nc if prev is None else min(prev, nc)

# ── Foco experimental: summit a <=1 km del cráter Nicanor ───────────────────
foco = {}
d = json.loads(FOCO_JSON.read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    if f < START:
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or pc.get("centroid_lat") is None:
        continue
    if hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) <= 1.0:
        foco[f] = max(foco.get(f, 0), v)

ventana_foco = (min(d["records"][0]["datetime_utc"][:10], START),
                d["records"][-1]["datetime_utc"][:10]) if d["records"] else None


def dts(dd):
    return [datetime.fromisoformat(x) for x in sorted(dd)]


# ── Figura ──────────────────────────────────────────────────────────────────
fig, (axA, axC, axB) = plt.subplots(
    3, 1, figsize=(14, 9.6), sharex=True,
    gridspec_kw={"height_ratios": [1, 0.62, 2.6], "hspace": 0.16})
fig.suptitle("Nevados de Chillán, cráter Nicanor — ¿qué mostró MIROVA y qué detectamos nosotros?\n"
             "(VIIRS 375 m, desde junio 2026)", fontsize=13.5, fontweight="bold")

C_MIR, C_REP, C_FOC = "#cc3311", "#88a8c8", "#1a7a33"

# Panel A — quién detectó cada noche
axA.set_title("¿Quién detectó, cada noche?", loc="left", fontsize=11)
for y, (serie, color, marker, size) in enumerate([
        (foco,    C_FOC, "s", 42),
        (replica, C_REP, "o", 30),
        (mirova,  C_MIR, "*", 150)]):
    axA.scatter(dts(serie), [y] * len(serie), c=color, marker=marker, s=size,
                edgecolors="k" if marker == "*" else "none", linewidths=0.5, zorder=3)
axA.set_yticks([0, 1, 2])
axA.set_yticklabels(["Experimental\n(foco 1 km, umbral bajo)",
                     "Réplica MIROVA\n(nuestro dashboard)",
                     "MIROVA publicó\n(alerta térmica)"], fontsize=9)
axA.set_ylim(-0.6, 2.6)
axA.grid(True, axis="x", alpha=0.25)
axA.tick_params(axis="y", length=0)

# Panel intermedio — cuánto pudo ver el sensor esa noche
_of = sorted(despejado)
_ox = [datetime.fromisoformat(f) for f in _of]
_oy = [despejado[f] for f in _of]
_col = ["#3a7d44" if v >= 70 else ("#d9a441" if v >= 30 else "#b0413e") for v in _oy]
axC.bar(_ox, _oy, width=0.9, color=_col, linewidth=0)
axC.axhline(50, color="#666", lw=0.8, ls=":")
axC.set_ylim(0, 100)
axC.set_yticks([0, 50, 100])
axC.set_yticklabels(["tapado", "50%", "despejado"], fontsize=8.5)
axC.grid(True, axis="x", alpha=0.25)
axC.set_title("¿Cuánto del área pudo ver el sensor? (nubosidad medida por el propio granule)"
              "   —   barra corta = esa noche casi no vimos: un cero abajo no significa que el volcán estuviera tranquilo",
              loc="left", fontsize=11)

# Panel B — cuánta energía
axB.set_title("¿Cuánta energía? (misma noche, mismo sensor)", loc="left", fontsize=11)
xs = dts(replica)
axB.plot(xs, [replica[x.strftime("%Y-%m-%d")] for x in xs], "o", ms=5, color=C_REP,
         label="Réplica MIROVA (lo que ve el dashboard hoy)")
# la línea se corta en huecos de observación >5 días: una línea continua sobre
# un hueco de semanas dibujaría una continuidad que la observación no tiene
fx, fy, prev = [], [], None
for f in sorted(foco):
    d_ = datetime.fromisoformat(f)
    if prev is not None and (d_ - prev).days > 5:
        fx.append(prev); fy.append(float("nan"))
    fx.append(d_); fy.append(foco[f]); prev = d_
axB.plot(fx, fy, "s-", ms=6, lw=1.4,
         color=C_FOC, label="Experimental: radio 1 km al cráter + umbral 0.005 MW")
xs = dts(mirova)
axB.plot(xs, [mirova[x.strftime("%Y-%m-%d")] for x in xs], "*", ms=17, color=C_MIR,
         mec="k", mew=0.6, ls="none", zorder=5, label="MIROVA (las veces que publicó alerta)")

# anotar las noches en que MIROVA y el experimental coinciden
for i, f in enumerate(sorted(set(mirova) & set(foco))):
    x = datetime.fromisoformat(f)
    lado = -1 if i % 2 == 0 else 1          # alternar para que no se tapen
    axB.annotate(f"MIROVA {mirova[f]:.2f}\nnosotros {foco[f]:.2f}",
                 xy=(x, max(mirova[f], foco[f])), xytext=(46 * lado, 26),
                 textcoords="offset points", ha="center", fontsize=8,
                 arrowprops=dict(arrowstyle="-", color="#b8a24a", lw=0.7),
                 bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec="#b8a24a", lw=0.6))

axB.set_ylabel("Potencia radiada VRP (MW)")
axB.set_ylim(bottom=0)
axB.margins(y=0.30)
axB.grid(True, alpha=0.25)
axB.legend(loc="upper left", fontsize=9, framealpha=0.95)
axB.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
axB.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
plt.setp(axB.get_xticklabels(), rotation=0, fontsize=8.5)

nota = ("Cómo leerla: cada estrella roja es una noche en que MIROVA publicó alerta térmica; los cuadrados verdes son el foco del cráter\n"
        "Nicanor visto por el perfil experimental (área acotada a 1 km + umbral bajo el mínimo de MIROVA); los puntos celestes, la réplica\n"
        "operacional. Se muestra solo VIIRS 375 m: todas las alertas MIROVA de este período son de ese sensor.")
if ventana_foco and ventana_foco[1] >= "2026-06-25" and min(foco, default="9999") >= "2026-06-25":
    nota += "\nEl experimental aún no cubre el 01–24 de junio (reproceso en curso); esa franja solo muestra réplica y MIROVA."
fig.text(0.06, 0.005, nota, fontsize=8.2, color="#555", va="bottom")
fig.tight_layout(rect=(0, 0.055, 1, 1))
out = Path(__file__).parent / "ndc_simple_s124.png"
fig.savefig(out, dpi=150)
print(f"figura: {out}")

# ── Números (fuente de verdad) ──────────────────────────────────────────────
import statistics as st
print(f"\nMIROVA alertas V375: {len(mirova)}  |  réplica noches: {len(replica)}  |  foco noches: {len(foco)}")
if foco:
    print(f"foco: mediana {st.median(foco.values()):.3f} MW, max {max(foco.values()):.3f}")
for f in sorted(set(mirova) & set(foco)):
    print(f"  coinciden {f}: MIROVA {mirova[f]:.2f} vs foco {foco[f]:.3f}")
solo_m = sorted(set(mirova) - set(foco))
print("alertas MIROVA sin foco nuestro:", solo_m)
