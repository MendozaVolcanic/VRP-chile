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
# Radio del foco: 500 m (pedido de Nicolás, S124). A 375 m de píxel VIIRS I,
# 500 m son ~1,3 píxeles: es el círculo más ajustado que el sensor soporta sin
# volverse un solo píxel. Medido antes de aplicarlo: bajar de 1 km a 500 m
# cuesta 1 noche de la réplica y 0 del experimental, y las 3 alertas de MIROVA
# que reproducimos sobreviven las 3 — las detecciones están en el cráter, no
# desparramadas.
FOCO_KM = 0.5
START = "2026-06-01"
# S125 — RESUELTO. Hubo una ventana no comparable: el 01-11 jun del JSON
# operacional venia de una version anterior del codigo, con 21 pasadas donde el
# experimental daba >=0.02 MW y la replica 0 CON EL MISMO PIXEL (misma
# lat/lon/bt_k, `anomaly_pixels: []`). Se reproceso con --overwrite (run
# 33179840122) y la discrepancia bajo de 21 a 0, verificado sobre las 380
# pasadas comunes. Ya no hace falta sombrear nada.
#
# El `--overwrite` es el punto: sin el, `store.py:554-573` NO reemplaza un record
# con la misma clave (datetime_utc, sensor) salvo upgrade NRT->standard, y esos
# 119 records ya eran "standard" — el run habria cerrado en VERDE sin tocar nada.
NO_COMPARABLE = None
FOCO_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/experimental_ndc_focus/NevadosDeChillan.json"


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


# ── MIROVA: alertas VIIRS375 por noche ──────────────────────────────────────
mirova = {}
mirova_lejanas = {}     # alertas nocturnas fuera del foco (se dibujan huecas)
mirova_excluidas = []   # alertas no comparables (diurnas / lejos del foco)
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
        # AUDIT S124 (hallazgo 3): solo son COMPARABLES las alertas que nuestro
        # foco podria reproducir — nocturnas (nuestro pipeline es night-only) y
        # al crater (Distancia_km <= 0.38, o sea <= 1 celda de la grilla MIROVA,
        # ver D15). Las demas (diurnas A76 o a 2.9-4.1 km) se listan en la nota
        # al pie: dibujarlas como estrellas "que no vimos" era comparar contra
        # algo irreproducible por construccion.
        try:
            _D = float(r.get("Distancia_km"))
        except (TypeError, ValueError):
            _D = None
        _hora = int((r.get("Fecha_Satelite_UTC") or "0000-00-00 12")[11:13] or 12)
        _nocturna = 3 <= _hora <= 9
        if v > 0 and _nocturna and _D is not None and _D <= 0.38:
            mirova[f] = max(mirova.get(f, 0), v)
        elif v > 0:
            mirova_excluidas.append((f, v, _D, "diurna" if not _nocturna else f"@{_D:.2f} km"))
            # AUDIT S125 — las alertas lejanas se dibujan como estrella HUECA en su
            # fecha, no solo al pie. Desterrarlas dejaba el hueco de julio con las
            # tres filas vacias, sugiriendo "MIROVA tampoco vio nada" cuando lo que
            # pasa es que vio algo A 2,86 km del crater: la senal se corrio, no
            # desaparecio. Solo las nocturnas (las diurnas son artefacto solar A76).
            if _nocturna and _D is not None:
                mirova_lejanas[f] = max(mirova_lejanas.get(f, 0), v)

# ── Pasadas COMUNES (hallazgo 7 del audit): las dos corridas difieren en las
# pasadas DESCARGADAS (16 solo-réplica desde junio). Sin esta restricción, el
# panel A atribuye a "umbral" diferencias que son de descarga/cobertura.
def _claves(path):
    dd_ = json.loads((ROOT / path).read_text(encoding="utf-8"))
    return {(r["datetime_utc"], r.get("sensor")) for r in dd_["records"]
            if "VIIRS" in (r.get("sensor") or "") and "750" not in r["sensor"]}
PASADAS_COMUNES = (_claves("data/mirova_equivalent/NevadosDeChillan.json")
                   & _claves("data/experimental_ndc_focus/NevadosDeChillan.json"))

# ── Réplica operacional: VIIRS375, filtro del dashboard ─────────────────────
replica = {}
d = json.loads((ROOT / "data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    s = r.get("sensor") or ""
    if f < START or "VIIRS" not in s or "750" in s:
        continue
    if (r["datetime_utc"], r.get("sensor")) not in PASADAS_COMUNES:
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or r.get("distance_class") != "summit":
        continue
    # MISMO RADIO que el experimental (FOCO_KM = 500 m al cráter Nicanor). Antes
    # se usaba el inner de 5 km del KML MIROVA, y comparar 5 km contra el foco
    # hacía que la réplica pareciera más sensible cuando lo único que tenía era
    # más ÁREA: de
    # sus 135 detecciones, 96 caían a 2-4 km del cráter (S124). Con el radio
    # igualado la única diferencia que queda entre las dos series es el umbral,
    # que es la variable del experimento.
    if pc.get("centroid_lat") is None:
        continue
    if hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) > FOCO_KM:
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
    # QUÉ SE MIDE: si hubo fondo, y qué tan estructurado estaba.
    #   n_bg == 0  -> el pipeline no pudo establecer NINGÚN píxel de fondo:
    #                 ceguera real, no "no detectamos". Medido: las 3 alertas de
    #                 MIROVA que perdemos caen las 3 en noches así, y solo el
    #                 17 % de las noches lo son.
    #   sigma_bg   -> dispersión térmica del terreno. Noche despejada = hay
    #                 estructura (roca, parches de nieve, valle) y la dispersión
    #                 es alta; manto de nubes = escena uniforme y colapsa.
    # Es mejor que el umbral de 260 K del pipeline (D14) porque NO mira la
    # temperatura absoluta, así que no confunde nieve fría con nube.
    sg = r.get("diag_sigma_bg_k")
    nb = r.get("diag_n_bg_used_first_pass")
    valor = 0.0 if (nb == 0 or sg is None) else float(sg)
    prev = despejado.get(f)
    despejado[f] = valor if prev is None else max(prev, valor)

# ── Foco experimental: summit a <= FOCO_KM (500 m) del cráter Nicanor ───────
foco = {}
d = json.loads(FOCO_JSON.read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    if f < START:
        continue
    if (r["datetime_utc"], r.get("sensor")) not in PASADAS_COMUNES:
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or pc.get("centroid_lat") is None:
        continue
    if hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) <= FOCO_KM:
        foco[f] = max(foco.get(f, 0), v)

# cobertura REAL del experimental, de los RECORDS (audit h6: inferirla de las
# detecciones confunde "no detecto" con "no hay data").
_dias_exp = sorted(set(r["datetime_utc"][:10] for r in d["records"]))
fin_exp = _dias_exp[-1] if _dias_exp else START


def dts(dd):
    return [datetime.fromisoformat(x) for x in sorted(dd)]


# ── Figura ──────────────────────────────────────────────────────────────────
fig, (axA, axC, axB) = plt.subplots(
    3, 1, figsize=(14, 11.4), sharex=True,
    gridspec_kw={"height_ratios": [1, 0.62, 2.6], "hspace": 0.30})
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
# estrellas HUECAS: MIROVA publico esa noche, pero lejos del crater (fuera del foco)
if mirova_lejanas:
    axA.scatter(dts(mirova_lejanas), [2] * len(mirova_lejanas), facecolors="none",
                edgecolors=C_MIR, marker="*", s=150, linewidths=1.2, zorder=3)
axA.set_yticks([0, 1, 2])
axA.set_yticklabels([f"Experimental\n(foco {FOCO_KM*1000:.0f} m, umbral bajo)",
                     "Réplica MIROVA\n(nuestro dashboard)",
                     "MIROVA publicó\n(alerta térmica)"], fontsize=9)
axA.set_ylim(-0.6, 2.6)
axA.grid(True, axis="x", alpha=0.25)
axA.tick_params(axis="y", length=0)

# ── AUDIT S125: las dos zonas que la figura tiene que explicar ──────────────
# (a) ventana no comparable (hoy None: se reproceso, ver cabecera)
if NO_COMPARABLE is not None:
    _nc0 = datetime.fromisoformat(NO_COMPARABLE[0])
    _nc1 = datetime.fromisoformat(NO_COMPARABLE[1])
    for _ax in (axA, axC, axB):
        _ax.axvspan(_nc0, _nc1, color="#999999", alpha=0.16, zorder=0, lw=0)
    axA.text(_nc0 + (_nc1 - _nc0) / 2, 2.45, "réplica\ndesactualizada", ha="center",
             va="top", fontsize=6.6, color="#555", linespacing=1.15, zorder=4)

# (b) el silencio de julio: el crater se apaga en las TRES series a la vez
_h0, _h1 = datetime.fromisoformat("2026-07-07"), datetime.fromisoformat("2026-08-16")
axA.annotate("", xy=(_h0, 0.35), xytext=(_h1, 0.35),
             arrowprops=dict(arrowstyle="<->", color="#8a6d3b", lw=1.1))
axA.text(_h0 + (_h1 - _h0) / 2, 1.05,
         "seis semanas sin foco en el cráter, y MIROVA también calló:\n"
         "su única alerta fue el 15-jul a 2,86 km (estrella hueca).\n"
         "No se apagó, se corrió: 1 detección a ≤500 m contra 30 a 1–3 km.",
         ha="center", va="center", fontsize=6.9, color="#5c4a25", linespacing=1.3,
         zorder=6,
         bbox=dict(boxstyle="round,pad=0.28", fc="#fdf6e3", ec="#c9b458", lw=0.7, alpha=0.96))

# Panel intermedio — ¿se pudo ver el terreno esa noche?
_of = sorted(despejado)
_ox = [datetime.fromisoformat(f) for f in _of]
_oy = [despejado[f] for f in _of]
# Las noches CIEGAS tienen σ = 0, o sea barra de altura cero: invisibles, y son
# justo las que hay que ver. Se dibujan a altura completa en rojo — la franja
# llena significa "acá no sabemos", no "acá hubo mucha señal".
_ciego = [v <= 0.01 for v in _oy]
axC.bar([x for x, c in zip(_ox, _ciego) if c], [6.0] * sum(_ciego),
        width=0.9, color="#b0413e", alpha=0.5, linewidth=0)
_col = ["#d9a441" if v < 2.0 else "#3a7d44" for v in _oy]
axC.bar([x for x, c in zip(_ox, _ciego) if not c],
        [v for v, c in zip(_oy, _ciego) if not c],
        width=0.9, color=[c for c, cc in zip(_col, _ciego) if not cc], linewidth=0)
axC.axhline(2.0, color="#666", lw=0.8, ls=":")
axC.set_ylim(0, 6)
axC.set_yticks([0, 2, 4, 6])
axC.set_ylabel("σ fondo (K)\n↑ más despejado", fontsize=8)
axC.grid(True, axis="x", alpha=0.25)
axC.set_title("¿Se pudo ver el terreno esa noche? (dispersión térmica del fondo, σ — proxy, no medición de nubosidad)",
              loc="left", fontsize=11)
# AUDIT S125: esta leyenda estaba DENTRO del panel y tapaba las barras rojas de
# julio-agosto, que son justo las que hay que ver. Baja a la nota al pie.
_leyenda_C = (
    "Panel del medio (σ del fondo): verde alto = despejado, se ve la estructura del terreno · barra baja = escena uniforme,\n"
    f"nube probable · rojo lleno = CIEGO ({sum(_ciego)} noches), ni el fondo pudo medirse: sin información, NO es calma. Es un\n"
    "PROXY, no una medición de nubosidad: mide cuán estructurado está el terreno, así que una nube estratiforme muy pareja\n"
    "y un cielo limpio sobre nieve homogénea se parecen. La máscara oficial del sensor (CLDMSK_L2_VIIRS, disponible en NRT)\n"
    "sería la medición real.")

# Panel B — cuánta energía
axB.set_title("¿Cuánta energía? (misma noche, mismo sensor)", loc="left", fontsize=11)
ax_foco_x = dts(foco)
axB.plot(ax_foco_x, [foco[x.strftime("%Y-%m-%d")] for x in ax_foco_x], "s", ms=7,
         color=C_FOC, zorder=3, label=f"Experimental: radio {FOCO_KM*1000:.0f} m al cráter + umbral 0.005 MW")
xs = dts(mirova)
axB.plot(xs, [mirova[x.strftime("%Y-%m-%d")] for x in xs], "*", ms=17, color=C_MIR,
         mec="k", mew=0.6, ls="none", zorder=5, label="MIROVA (las veces que publicó alerta)")

# anotar las noches en que MIROVA y el experimental coinciden
for i, f in enumerate(sorted(set(mirova) & set(foco))):
    x = datetime.fromisoformat(f)
    lado = -1 if i % 2 == 0 else 1          # alternar para que no se tapen
    axB.annotate(f"MIROVA {mirova[f]:.2f} ★\nnosotros {foco[f]:.2f} ■",
                 xy=(x, mirova[f]), xytext=(58 * lado, 40),
                 textcoords="offset points", ha="center", fontsize=8,
                 arrowprops=dict(arrowstyle="-", color="#b8a24a", lw=0.7),
                 bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec="#b8a24a", lw=0.6))

xs = dts(replica)
axB.plot(xs, [replica[x.strftime("%Y-%m-%d")] for x in xs], "o", ms=4.5, color=C_REP,
         mec="#1f4e79", mew=0.7, zorder=4, label="Réplica MIROVA (lo que ve el dashboard hoy)")

axB.set_ylabel("Potencia radiada VRP (MW)")
axB.set_ylim(bottom=0)
axB.margins(y=0.30)
axB.grid(True, alpha=0.25)
axB.legend(loc="upper left", fontsize=9, framealpha=0.95)
for _ax in (axA, axC, axB):
    _ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
    _ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
    _ax.xaxis.set_minor_locator(mdates.DayLocator())
    _ax.grid(True, axis="x", which="minor", alpha=0.10)
    _ax.grid(True, axis="x", which="major", alpha=0.30)
    # sharex oculta las fechas de los paneles de arriba; se reactivan para
    # poder contar dias sin bajar la vista al panel B (pedido de Nicolas)
    _ax.tick_params(axis="x", labelbottom=True, labelsize=7.2)
plt.setp(axB.get_xticklabels(), rotation=0, fontsize=8.5)

nota = ("Cómo leerla: cada estrella roja es una noche en que MIROVA publicó alerta térmica; los cuadrados verdes son el foco del cráter\n"
        "Nicanor visto por el perfil experimental (área acotada a 500 m + umbral bajo el mínimo de MIROVA); los puntos celestes, la réplica\n"
        "operacional. Se muestra solo VIIRS 375 m: todas las alertas MIROVA de este período son de ese sensor.")
if fin_exp < "2026-08-27":
    nota += ("\nCobertura del experimental hasta el " + fin_exp + ": después solo hay réplica y MIROVA "
             "(reproceso en curso). Paneles restringidos a pasadas que AMBAS corridas procesaron.")
if mirova_excluidas:
    _exc = "  ·  ".join(x[0] + " " + format(x[1], ".2f") + " MW (" + x[3] + ")" for x in sorted(mirova_excluidas))
    nota += ("\nAlertas MIROVA fuera del foco de 500 m (estrellas HUECAS en el panel de arriba; no entran a la comparación de energía): "
             + _exc + ".")
if NO_COMPARABLE is not None:
    nota += ("\nFranja gris: la serie operacional ahí viene de una versión anterior del código, así que en esos días la "
             "diferencia\nentre réplica y experimental NO es atribuible al umbral.")
else:
    # S125: el resultado que quedó al reprocesar el 01-11 jun con --overwrite.
    # Antes parecía que el umbral bajo aportaba 3 noches; era version de codigo.
    nota += (f"\nRéplica y experimental detectan las MISMAS {len(replica)} noches en el foco: bajar el umbral de 0.02 a "
             "0.005 MW no aporta ninguna noche acá. Las 3\nnoches que antes parecían ganadas por el umbral eran una "
             "ventana del operacional sin reprocesar (01–11 jun), corregida el 2026-08-28 (21 discrepancias → 0).")
nota += "\n" + _leyenda_C
fig.text(0.055, 0.008, nota, fontsize=7.4, color="#555", va="bottom", linespacing=1.5)
# AUDIT S125: tight_layout avisa 'Axes not compatible' por los axvspan/annotate
# y deja el eje del panel B encima de la nota. Margenes explicitos en su lugar.
fig.subplots_adjust(left=0.145, right=0.985, top=0.915, bottom=0.225, hspace=0.34)
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
