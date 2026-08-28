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
replica_sin_radio = {}   # lo que el dashboard publica sin acotar al crater
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
    # FEEDBACK NICOLAS (S125): "¿la replica mostro esos valores sin necesidad del
    # radio, o esos datos fueron filtrados?" — SI estan filtrados, y hay que
    # decirlo. `replica_sin_radio` es lo que el dashboard publica de verdad un dia
    # normal (solo el gate `distance_class == summit`, sin recorte al crater).
    replica_sin_radio[f] = max(replica_sin_radio.get(f, 0), v)
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
             f"VIIRS 375 m, desde junio 2026 · las tres series cuentan SOLO lo que cae a menos de "
             f"{FOCO_KM*1000:.0f} m del cráter", fontsize=12.5, fontweight="bold")

C_MIR, C_REP, C_FOC = "#cc3311", "#88a8c8", "#1a7a33"

# Panel A — quién detectó cada noche
axA.set_title("¿Quién detectó, cada noche?", loc="left", fontsize=11)
# FEEDBACK NICOLAS (S125): "poner los umbrales de cada sensor, que tan bajo lee
# MIROVA". Medido sobre el consolidado COMPLETO (todos los volcanes, todas las
# alertas con VRP>0): el piso es practicamente el mismo en los 9 volcanes con
# n>=5 (0,010 a 0,050 MW en VIIRS375), asi que no es un ajuste por volcan.
axA.text(0.9955, 0.03,
         "Lo más bajo que MIROVA llegó a publicar, en todos los volcanes:\n"
         "VIIRS 375 m  0,010 MW   ·   VIIRS 750 m  0,090   ·   MODIS  0,140",
         transform=axA.transAxes, ha="right", va="bottom", fontsize=7.2,
         color="#444", linespacing=1.35, zorder=6,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#bbb", lw=0.6, alpha=0.93))
for y, (serie, color, marker, size) in enumerate([
        (foco,    C_FOC, "s", 42),
        (replica, C_REP, "o", 30),
        (mirova,  C_MIR, "*", 150)]):
    axA.scatter(dts(serie), [y] * len(serie), c=color, marker=marker, s=size,
                edgecolors="k" if marker == "*" else "none", linewidths=0.5, zorder=3)
# FEEDBACK NICOLAS (S125): las estrellas huecas (alertas de MIROVA fuera del
# foco) no aportaban al analisis y agregaban un simbolo mas que descifrar. Se
# quitan del grafico; siguen listadas en la nota al pie.
axA.set_yticks([0, 1, 2])
axA.set_yticklabels(["Experimental\n(umbral 0,005 MW)",
                     "Réplica MIROVA\n(umbral 0,02 MW)",
                     "MIROVA publicó\n(alerta térmica)"], fontsize=9)
axA.set_ylim(-0.85, 2.6)
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
axA.text(_h0 + (_h1 - _h0) / 2, 1.22,
         "seis semanas sin señal EN EL CRÁTER — y MIROVA tampoco publicó nada acá.\n"
         "No es que el volcán se apagara ni que faltaran pasadas: hubo 30 detecciones\n"
         "nuestras a 1–3 km del cráter y sólo 1 dentro de los 500 m. El calor siguió,\n"
         "repartido por el edificio volcánico, sin un foco concentrado en el cráter.",
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
# FEEDBACK NICOLAS (S125): el verde de estas barras se confundia con los cuadrados
# verdes del experimental en el panel de arriba — dos cosas distintas del mismo
# color. Paleta AZUL, que no se usa para ninguna serie de deteccion.
# Y UN SOLO canal de informacion: la ALTURA. Antes habia altura + color (verde
# vs ambar segun un corte en 2 K), que obligaba a preguntarse como se combinan.
# Ahora el color solo distingue "se midio" (azul) de "no se pudo medir" (rojo).
axC.bar([x for x, c in zip(_ox, _ciego) if c], [6.0] * sum(_ciego),
        width=0.9, color="#b0413e", alpha=0.55, linewidth=0)
axC.bar([x for x, c in zip(_ox, _ciego) if not c],
        [v for v, c in zip(_oy, _ciego) if not c],
        width=0.9, color="#4a7fb5", linewidth=0)
axC.set_ylim(0, 6)
axC.set_yticks([0, 3, 6])
axC.set_ylabel("contraste del\nterreno (K)", fontsize=8)
axC.grid(True, axis="x", alpha=0.25)
axC.set_title("¿Se pudo ver el terreno esa noche?   —   barra ALTA = se vio bien · barra BAJA = poco contraste, "
              "probable nube · ROJA = no se pudo medir",
              loc="left", fontsize=9.5)
# AUDIT S125: esta leyenda estaba DENTRO del panel y tapaba las barras rojas de
# julio-agosto, que son justo las que hay que ver. Baja a la nota al pie.
# (_leyenda_C se eliminó en S125: su contenido pasó a la nota al pie, reescrita)

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

# ── Nota al pie — REESCRITA S125 con el feedback de Nicolas ────────────────
# Antes eran 9 lineas con la metodologia entera. Ahora responde 3 preguntas
# concretas, en su orden natural, y la metodologia queda en los comentarios.
_n_sin_radio = len(replica_sin_radio)
nota = (
    f"Las tres series miran lo mismo: el cráter, a menos de {FOCO_KM*1000:.0f} m. Réplica y experimental detectan las mismas "
    f"{len(replica)} noches: bajar el umbral de 0,02 a 0,005 MW no agrega nada acá.\n"
    f"Sin acotar al cráter, la réplica publicaría {_n_sin_radio} noches en el dashboard; las otras "
    f"{_n_sin_radio - len(replica)} son señal del edificio volcánico a 1–3 km, no del cráter.\n\n"
    "MIROVA vio esas noches y las llamó RUTINA, sin alerta: no le faltó el dato. Su umbral no es de energía sino de CONTRASTE contra el fondo, "
    "así que una misma potencia puede pasar\n"
    "o no según qué tan parejo esté el terreno. Por eso hay noches nuestras de 0,04–0,08 MW sin alerta suya, estando por encima de su mínimo publicado.\n\n"
    "Barras: alta = terreno con contraste, se pudo medir · baja = escena pareja, probable nube · "
    f"roja = no hubo fondo medible ({sum(_ciego)} noches, y ninguna tiene detección).\n"
    "Es un proxy del terreno, no una medición de nubes: la máscara oficial del sensor (CLDMSK_L2_VIIRS) sería lo correcto."
)
if mirova_excluidas:
    _exc = "  ·  ".join(x[0] + " " + format(x[1], ".2f") + " MW " + x[3] for x in sorted(mirova_excluidas))
    nota += "\nAlertas de MIROVA que caen fuera del cráter y por eso no se comparan:  " + _exc + "."
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
