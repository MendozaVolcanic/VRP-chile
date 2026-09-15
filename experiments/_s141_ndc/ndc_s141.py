# -*- coding: utf-8 -*-
"""S141: Nevados de Chillán desde junio, actualización del análisis S124 con lo aprendido desde entonces.

POR QUÉ. La figura S124 (experiments/_s124_ndc_focus/) comparaba MIROVA, la réplica y un perfil
experimental del foco, contando sólo alertas. Desde entonces aprendimos cinco cosas que cambian cómo
hay que leer ese volcán:
  1. La brecha con MIROVA es de SOBRE-PUBLICACIÓN, no de recall (S139): hay que mirar también las
     pasadas donde MIROVA miró y no vio nada. La referencia unificada (consolidado + OCR + respaldo,
     Fase 0) trae esas pasadas RUTINA; el consolidado solo, no.
  2. Lo publicado se decide con el PREDICADO DEL DASHBOARD, no con un filtro reconstruido (S138): se
     ejecuta con node desde frontend/index.html, igual que el banco de paridad.
  3. En VIIRS 375 m el operador ve el núcleo F5, no el cúmulo entero (S132, A10).
  4. Las barras "no se pudo medir el fondo" de S124 eran la máscara de nube de 260 K comiéndose la
     nieve; esa máscara salió de producción con el PR #535 (2026-08-28 23:00 UTC, D14).
  5. El grupo MIROVA no confía en la magnitud de pasadas oblicuas (cenit > 40°, Massimetti et al.
     2020 p. 15; docs/MIROVA_DIVERGENCES.md D17 nota S141): se marcan aparte.
El perfil experimental del foco dejó de actualizarse el 2026-08-27 y no se usa.

INSTRUMENTO. P1 (¿vería lo que dice medir?): el predicado se contrasta con los casos del guard S139
(bp.control_identidad_predicado) y la carga de este script tiene que publicar EXACTAMENTE lo mismo
que el banco de paridad completo filtrado a Nevados de Chillán. P2 (¿mide otra cosa?): una pasada sin
fila de referencia va a sin_info y nunca a un denominador; las distancias de MIROVA son radios desde
su punto de referencia (~470 m al norte del cráter, D15), no posiciones (A93).

Fuente de verdad de los números del informe: este script (regla S91), que escribe ndc_s141.json.
USO: python experiments/_s141_ndc/ndc_s141.py [--snapshot] [--inicio 2026-06-01] [--fin AAAA-MM-DD]
"""
import argparse
import collections
import io
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts", ROOT / "experiments" / "_s124_ndc_focus"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402  (predicado del dashboard, referencia y etiquetas)
from basemap import ATRIBUCION, satelital_km  # noqa: E402

VOL = "NevadosDeChillan"
NIC = (-36.867210, -71.378241)          # cráter Nicanor (S124)
INICIO = "2026-06-01"
CORTE_535 = datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc)
CELDA_MIROVA_KM = 0.38                  # D15: distancia publicada <= 1 celda VIIRS 375 = en el cráter
ZEN_OBLICUO = 40.0
FOCO_KM = 0.5
DATA = ROOT / "data" / "mirova_equivalent" / f"{VOL}.json"


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def km_xy(lat, lon):
    return ((lon - NIC[1]) * 111.32 * math.cos(math.radians(NIC[0])), (lat - NIC[0]) * 111.32)


# ------------------------------------------------------------------ datos
def cargar_ndc(coords, inner, ventana):
    """Records nocturnos de NdC con la decisión de publicar del dashboard (misma lógica que
    bp.cargar_nuestros, restringida a un volcán y con los campos extra que usan las figuras)."""
    lat, lon = coords[VOL]
    recs, casos = [], []
    for r in json.loads(DATA.read_text(encoding="utf-8"))["records"]:
        b = bp.bucket(r.get("sensor"))
        if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
            continue
        try:
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        pc = r.get("primary_cluster") or {}
        recs.append({"vol": VOL, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                     "dc": r.get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                     "pc_dist": pc.get("centroid_dist_km"), "z": r.get("sensor_zenith_deg"),
                     "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"),
                     "n_bg": r.get("diag_n_bg_used_first_pass"), "sensor": r.get("sensor")})
        slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for p in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner[VOL]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs


def alertas_mirova(filas, coords, ventana):
    """Filas ALERTA de NdC en la ventana, separadas en nocturnas (con clase por distancia) y diurnas."""
    lat, lon = coords[VOL]
    noct, diur = [], []
    # Una misma pasada puede venir dos veces, del consolidado y del OCR, con distancias que difieren en
    # el redondeo (0,38 contra 0,41 km el 2026-08-18): se deja una fila por pasada y sensor, y gana la
    # del consolidado, que es la que MIROVA publica como tabla (la del OCR se lee de la imagen).
    unicas = {}
    for f in filas:
        if not bp.es_alerta(f["tipo"]) or not (ventana[0] <= f["fecha_utc"][:10] <= ventana[1]):
            continue
        k = (f["fecha_utc"][:16], f["sensor_bucket"])
        if k not in unicas or (unicas[k]["source"] != "CONS" and f["source"] == "CONS"):
            unicas[k] = f
    for f in unicas.values():
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        d = f["dist_km"]
        fila = {"fecha_utc": f["fecha_utc"][:16], "sensor": f["sensor_bucket"], "vrp_mw": f["vrp_mw"],
                "dist_km": d, "source": f["source"], "dt": dt}
        if bp.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt):
            diur.append(fila)
            continue
        fila["clase"] = ("sin_distancia" if d is None else "crater" if d <= CELDA_MIROVA_KM else "lejana")
        noct.append(fila)
    return noct, diur


def mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 4) if xs else None


def numeros(recs, noct, diur, por_vb, meta):
    v375 = [r for r in recs if r["b"] == "VIIRS375"]
    por_mes = collections.defaultdict(collections.Counter)
    for r in v375:
        c = por_mes[r["noche"][:7]]
        c["pasadas"] += 1
        c["publicadas"] += r["pub"]
        c[r["lab"]] += 1
        c[r["lab"] + "_publicadas"] += r["pub"]
        c["sin_fondo"] += int(r["n_bg"] == 0)
        c["oblicuas"] += int((r["z"] or 0) > ZEN_OBLICUO)
    sin_record = bp.alertas_sin_record(por_vb, recs)
    metricas = {}
    for b in bp.BUCKETS + [None]:
        pas, noc = bp.metricas(recs, sin_record, bp._filtro(vol=VOL, b=b))
        metricas[b or "CUALQUIERA"] = {"pasada": pas, "noche_volcan": noc}
    antes = [r for r in v375 if r["dt"] < CORTE_535]
    despues = [r for r in v375 if r["dt"] >= CORTE_535]
    pos_pub = [r for r in v375 if r["lab"] == "pos" and r["pub"]]
    ratio = []
    for r in pos_pub:
        filas = [f for f in bp.parear(por_vb.get((VOL, "VIIRS375"), []), r["dt"]) if bp.es_alerta(f["tipo"])]
        v = max((f["vrp_mw"] or 0) for f in filas) if filas else 0
        if v > 0 and r["disp"]:
            ratio.append((r["disp"] / v, r["z"]))
    pub = [r for r in v375 if r["pub"]]
    return {
        "meta": meta,
        "definiciones": {
            "publicada": "predicado del dashboard (frontend/index.html, ejecutado con node): summit, válida, no artefacto y magnitud mostrada > 0",
            "magnitud_mostrada": "mirovaEqVrpDisplay: en VIIRS 375 m el núcleo F5",
            "pos / neg_limpio / far_ref / sin_info": "etiquetas por pasada de scripts/banco_paridad.py (±2 min contra la referencia unificada)",
            "sin_fondo": "diag_n_bg_used_first_pass == 0: el primer pase no tuvo ningún píxel de fondo",
            "oblicua": f"sensor_zenith_deg > {ZEN_OBLICUO:.0f}",
            "alerta_crater": f"ALERTA nocturna con Distancia_km <= {CELDA_MIROVA_KM} (una celda VIIRS 375 m, D15)",
        },
        "viirs375_por_mes": {m: dict(c) for m, c in sorted(por_mes.items())},
        "metricas_banco": metricas,
        "sin_fondo_viirs375": {"antes_535": {"n": len(antes), "sin_fondo": sum(1 for r in antes if r["n_bg"] == 0)},
                               "despues_535": {"n": len(despues), "sin_fondo": sum(1 for r in despues if r["n_bg"] == 0)}},
        "oblicuas_viirs375": {"n": len(v375), "oblicuas": sum(1 for r in v375 if (r["z"] or 0) > ZEN_OBLICUO),
                              "publicadas": len(pub), "publicadas_oblicuas": sum(1 for r in pub if (r["z"] or 0) > ZEN_OBLICUO)},
        "ratio_nuestro_mirova_v375_en_alertas": {
            "n": len(ratio), "mediana": mediana([x for x, _ in ratio]),
            "n_cenit_hasta_40": sum(1 for _, z in ratio if z is not None and z <= ZEN_OBLICUO),
            "mediana_cenit_hasta_40": mediana([x for x, z in ratio if z is not None and z <= ZEN_OBLICUO])},
        "alertas_mirova_nocturnas": [{k: v for k, v in a.items() if k != "dt"} for a in noct],
        "alertas_mirova_diurnas": [{k: v for k, v in a.items() if k != "dt"} for a in diur],
        "publicadas_por_distancia_al_crater_viirs375": {
            "hasta_500m": sum(1 for r in pub if r["pc_lat"] is not None and hav(NIC[0], NIC[1], r["pc_lat"], r["pc_lon"]) <= FOCO_KM),
            "de_500m_a_5km": sum(1 for r in pub if r["pc_lat"] is not None and FOCO_KM < hav(NIC[0], NIC[1], r["pc_lat"], r["pc_lon"]) <= 5.0),
            "mas_de_5km": sum(1 for r in pub if r["pc_lat"] is not None and hav(NIC[0], NIC[1], r["pc_lat"], r["pc_lon"]) > 5.0)},
    }


# ------------------------------------------------------------------ figuras
C_POS, C_NEG, C_SIN, C_MIR = "#1a7a33", "#c0392b", "#8a8a8a", "#cc3311"


MERGE_571 = datetime(2026, 8, 31, 20, 34, 53, tzinfo=timezone.utc)   # PR #571: sale el piso VRP del perfil


def tasa_semanal(recs_todos, vol=None):
    """Publicadas / negativos limpios VIIRS 375 m por semana (lunes). vol=None: los 11 Tier A."""
    c = collections.defaultdict(lambda: [0, 0])
    for r in recs_todos:
        if r["b"] != "VIIRS375" or r.get("lab") != "neg_limpio" or (vol is not None and r["vol"] != vol):
            continue
        lunes = (r["dt"] - __import__("datetime").timedelta(days=r["dt"].weekday())).strftime("%Y-%m-%d")
        c[lunes][0] += 1
        c[lunes][1] += r["pub"]
    return {k: (v[1] / v[0], v[0]) for k, v in sorted(c.items()) if v[0]}


def figura_serie(recs, noct, diur, out, ventana, recs_todos):
    v375 = [r for r in recs if r["b"] == "VIIRS375"]
    noches = collections.defaultdict(lambda: {"pub": 0, "labs": set(), "disp": 0.0, "oblicua_todas": True,
                                              "n": 0, "sin_fondo": 0})
    for r in v375:
        e = noches[r["noche"]]
        e["labs"].add(r["lab"])
        e["n"] += 1
        e["sin_fondo"] += int(r["n_bg"] == 0)
        if r["pub"]:
            e["pub"] = 1
            e["disp"] = max(e["disp"], r["disp"] or 0)
            e["oblicua_todas"] &= (r["z"] or 0) > ZEN_OBLICUO
    D = lambda s: datetime.fromisoformat(s)

    fig, (axA, axC, axD, axB) = plt.subplots(4, 1, figsize=(14, 14.5), sharex=True,
                                             gridspec_kw={"height_ratios": [1.15, 0.6, 0.9, 2.0], "hspace": 0.34})
    fig.suptitle("Nevados de Chillán: ¿qué publicó MIROVA y qué publica nuestro dashboard?\n"
                 f"VIIRS 375 m, pasadas nocturnas del {ventana[0]} al {ventana[1]} (actualización S141 del análisis S124)",
                 fontsize=12.5, fontweight="bold")

    # Panel A
    axA.set_title("¿Quién vio algo, cada noche?", loc="left", fontsize=11)
    cr = [a for a in noct if a["sensor"] == "VIIRS375" and a["clase"] == "crater"]
    le = [a for a in noct if a["sensor"] == "VIIRS375" and a["clase"] != "crater"]
    axA.scatter([D(a["fecha_utc"][:10]) for a in cr], [3] * len(cr), marker="*", s=170, c=C_MIR, edgecolors="k", lw=0.5, zorder=4)
    axA.scatter([D(a["fecha_utc"][:10]) for a in le], [2] * len(le), marker="*", s=150, facecolors="none", edgecolors=C_MIR, lw=1.1, zorder=4)
    miro_sin_ver = sorted({n for n, e in noches.items() if "neg_limpio" in e["labs"] and "pos" not in e["labs"]})
    axA.scatter([D(n) for n in miro_sin_ver], [1] * len(miro_sin_ver), marker="|", s=90, c="#555", zorder=3)
    for n, e in sorted(noches.items()):
        if not e["pub"]:
            continue
        col = C_POS if "pos" in e["labs"] else (C_NEG if "neg_limpio" in e["labs"] else C_SIN)
        axA.scatter([D(n)], [0], marker="o", s=34, c=col, zorder=4)
    axA.axvline(CORTE_535.replace(tzinfo=None), color="#555", ls=":", lw=1)
    axA.set_yticks([0, 1, 2, 3])
    axA.set_yticklabels(["Nuestro dashboard\npublicó", "MIROVA miró y\nno vio nada", "MIROVA: alerta\nlejos del cráter",
                         "MIROVA: alerta\nen el cráter"], fontsize=8.6)
    axA.set_ylim(-0.7, 3.7)
    axA.tick_params(axis="y", length=0)
    axA.scatter([], [], c=C_POS, s=34, label="publicamos y MIROVA alertó esa noche")
    axA.scatter([], [], c=C_NEG, s=34, label="publicamos en una noche en que MIROVA miró sin ver nada")
    axA.scatter([], [], c=C_SIN, s=34, label="publicamos sin pasada de MIROVA para comparar")
    axA.legend(loc="upper left", bbox_to_anchor=(0.0, -0.13), fontsize=8, ncol=3, frameon=False)

    # Panel C
    axC.set_title("¿Tuvo fondo el primer pase? (pasadas VIIRS 375 m por noche)", loc="left", fontsize=10)
    ns = sorted(noches)
    axC.bar([D(n) for n in ns], [noches[n]["n"] for n in ns], width=0.85, color="#c9d6e3", lw=0, label="pasadas")
    axC.bar([D(n) for n in ns], [noches[n]["sin_fondo"] for n in ns], width=0.85, color="#b0413e", lw=0,
            label="pasadas sin ningún píxel de fondo")
    axC.axvline(CORTE_535.replace(tzinfo=None), color="#555", ls=":", lw=1)
    axC.set_ylabel("pasadas", fontsize=8)
    axC.legend(loc="upper left", bbox_to_anchor=(0.0, -0.2), fontsize=8, ncol=2, frameon=False)
    axC.annotate("28-ago: sale la máscara de nube de 260 K (PR #535)", xy=(CORTE_535.replace(tzinfo=None), 1.0),
                 xycoords=("data", "axes fraction"), xytext=(-6, -4), textcoords="offset points",
                 ha="right", va="top", fontsize=7.6, color="#333",
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))

    # Panel D: cambio de régimen de publicación (todos los volcanes, no sólo NdC)
    axD.set_title("¿En qué fracción de las pasadas donde MIROVA miró y no vio nada publicamos igual? (por semana)",
                  loc="left", fontsize=10)
    for vol, col, nombre in ((VOL, "#1a3d5c", "Nevados de Chillán"), (None, "#b07d2b", "los 11 Tier A")):
        t = tasa_semanal(recs_todos, vol)
        xs = [datetime.fromisoformat(k) + __import__("datetime").timedelta(days=3) for k in t]
        axD.plot(xs, [v for v, _ in t.values()], "-o", ms=4, color=col, lw=1.6, label=nombre)
    for m, txt in ((CORTE_535, "sale la máscara de nube (#535)"), (MERGE_571, "sale el piso VRP (#571)")):
        axD.axvline(m.replace(tzinfo=None), color="#555", ls=":", lw=1)
    axD.annotate("#535 máscara de nube · #571 piso VRP", xy=(CORTE_535.replace(tzinfo=None), 0.04), xycoords=("data", "axes fraction"),
                 xytext=(-6, 0), textcoords="offset points", ha="right", fontsize=7.6, color="#333")
    axD.set_ylim(0, 1.05)
    axD.set_ylabel("fracción", fontsize=8)
    axD.legend(loc="upper left", fontsize=8, ncol=2, frameon=False)
    axD.axvline(MERGE_571.replace(tzinfo=None), color="#555", ls=":", lw=1)

    # Panel B
    axB.set_title("¿Cuánta energía? (lo que ve el operador, núcleo F5; hueco = todas las pasadas publicadas de la noche con el sensor a más de 40°)",
                  loc="left", fontsize=9.6)
    for n, e in sorted(noches.items()):
        if not e["pub"]:
            continue
        col = C_POS if "pos" in e["labs"] else (C_NEG if "neg_limpio" in e["labs"] else C_SIN)
        axB.plot([D(n)], [e["disp"]], "o", ms=6, mfc="none" if e["oblicua_todas"] else col, mec=col, mew=1.3, zorder=4)
    axB.plot([D(a["fecha_utc"][:10]) for a in cr], [a["vrp_mw"] for a in cr], "*", ms=16, color=C_MIR, mec="k", mew=0.6,
             ls="none", zorder=5, label="MIROVA, alerta en el cráter")
    axB.axvline(CORTE_535.replace(tzinfo=None), color="#555", ls=":", lw=1)
    axB.set_ylabel("Potencia radiada VRP (MW)")
    axB.set_ylim(bottom=0)
    axB.legend(loc="upper left", fontsize=8.5)
    for ax in (axA, axC, axD, axB):
        ax.grid(True, axis="x", alpha=0.25)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
        ax.tick_params(axis="x", labelbottom=True, labelsize=7.4)
    nota = ("Alertas diurnas de MIROVA, fuera de la comparación (artefacto solar A76): "
            + ("  ·  ".join(f"{a['fecha_utc']} {a['sensor']} {a['vrp_mw']:.2f} MW" for a in diur) or "ninguna")
            + ".\nAlertas lejanas: la distancia de MIROVA es un radio desde su punto de referencia, ~470 m al norte del cráter, y está cuantizada a su grilla (D15).")
    fig.text(0.05, 0.012, nota, fontsize=7.4, color="#555", va="bottom", linespacing=1.5)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.915, bottom=0.08, hspace=0.5)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figura_mapa(recs, out, ventana):
    pub = [r for r in recs if r["b"] == "VIIRS375" and r["pub"] and r["pc_lat"] is not None]
    fig, axs = plt.subplots(1, 2, figsize=(16, 8.6))
    fig.suptitle(f"Nevados de Chillán: dónde está lo que publicamos (VIIRS 375 m, {ventana[0]} a {ventana[1]})",
                 fontsize=12.5, fontweight="bold")
    for ax, lim, zoom, titulo in ((axs[0], 5.5, 13, "Radio interno del dashboard (5 km)"),
                                  (axs[1], 0.8, 17, "Zoom al cráter Nicanor (800 m)")):
        img, ext = satelital_km(NIC[0], NIC[1], lim, zoom=zoom)
        if img is not None:
            ax.imshow(img, extent=ext, origin="upper", zorder=0, interpolation="bilinear")
            ax.add_patch(plt.Rectangle((-lim * 2, -lim * 2), lim * 4, lim * 4, fc="white", alpha=0.22, zorder=1, ec="none"))
        for rkm, ls, lab in ((5.0, "-", "radio interno del dashboard (5 km)"), (FOCO_KM, "--", "foco de 500 m (S124)")):
            ax.add_patch(plt.Circle((0, 0), rkm, fill=False, color="#1a3d5c", lw=1.8, ls=ls, zorder=2, label=lab,
                                    path_effects=[pe.withStroke(linewidth=3.4, foreground="white")]))
        for lab, col, nombre in (("pos", C_POS, "MIROVA alertó en esa pasada"), ("neg_limpio", C_NEG, "MIROVA miró esa pasada y no vio nada"),
                                 ("far_ref", "#e67e22", "MIROVA vio calor fuera de su radio"), ("sin_info", C_SIN, "sin pasada de MIROVA para comparar")):
            sel = [r for r in pub if r["lab"] == lab]
            if not sel:
                continue
            xs, ys = zip(*[km_xy(r["pc_lat"], r["pc_lon"]) for r in sel])
            oblic = [(r["z"] or 0) > ZEN_OBLICUO for r in sel]
            ax.scatter([x for x, o in zip(xs, oblic) if not o], [y for y, o in zip(ys, oblic) if not o], s=30, c=col,
                       edgecolors="k", lw=0.4, zorder=5, label=f"{nombre} ({len(sel)})")
            ax.scatter([x for x, o in zip(xs, oblic) if o], [y for y, o in zip(ys, oblic) if o], s=30, facecolors="none",
                       edgecolors=col, lw=1.1, zorder=5)
        ax.plot(0, 0, "^", ms=13, c="#cc3311", mec="k", zorder=6, label="cráter Nicanor")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_title(titulo, fontsize=10.5)
        ax.set_xlabel("km al Este del cráter")
        ax.set_ylabel("km al Norte del cráter")
        ax.text(0.995, 0.005, ATRIBUCION, transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color="white",
                path_effects=[pe.withStroke(linewidth=2, foreground="#00000088")])
    axs[0].legend(loc="upper left", bbox_to_anchor=(0.0, -0.09), fontsize=8, ncol=2, framealpha=0.95)
    axs[1].text(0.02, 0.02, "Punto lleno: sensor a 40° o menos · hueco: más de 40°\nPosición = centroide del cúmulo publicado",
                transform=axs[1].transAxes, fontsize=8, va="bottom",
                bbox=dict(boxstyle="round,pad=0.3", fc="#f7f7f7", ec="#bbb"))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.2, wspace=0.18)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description="Nevados de Chillán desde junio (S141)")
    ap.add_argument("--snapshot", action="store_true", help="referencia desde el snapshot del repo (sin red)")
    ap.add_argument("--inicio", default=INICIO)
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    if a.snapshot:
        cons, ocr = bp.SNAP_CONS, bp.SNAP_OCR
        procedencia = {"fuente": "snapshot", "sha_cons": bp.sha_git(cons), "sha_ocr": bp.sha_git(ocr)}
    else:
        info = bp.bajar_remoto(HERE / "_dl_referencia")
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
        procedencia = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                       "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}

    identidad = bp.control_identidad_predicado()
    assert identidad == ([0, 1, 1, 1, 0], [1, 0]), f"el predicado del dashboard no da los casos del guard: {identidad}"
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = bp.cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = cargar_ndc(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    # Control P1: la carga de este script publica lo mismo que el banco completo filtrado a NdC.
    # Los records de los 11 volcanes se conservan etiquetados para el panel del cambio de régimen.
    recs_todos = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs_todos, por_vb, noche_sensor, noche_volcan)
    banco = {(r["b"], r["dt"]): r["pub"] for r in recs_todos if r["vol"] == VOL}
    mias = {(r["b"], r["dt"]): r["pub"] for r in recs}
    discrepan = sum(1 for k in set(banco) | set(mias) if banco.get(k) != mias.get(k))
    assert discrepan == 0, f"la carga de NdC no coincide con el banco de paridad en {discrepan} pasadas"

    noct, diur = alertas_mirova([f for f in filas if f["volcano"] == VOL], coords, ventana)
    meta = {"ventana": list(ventana), "referencia": procedencia, "sha_index_html": bp.sha_git(bp.HTML),
            "n_records_nocturnos": len(recs), "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
            "control_identidad_predicado": True, "control_carga_igual_banco": {"pasadas": len(mias), "discrepan": discrepan},
            "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out = numeros(recs, noct, diur, por_vb, meta)
    (HERE / "ndc_s141.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    out["tasa_semanal_publicacion_neg_limpio_v375"] = {
        "definicion": "publicadas / negativos limpios VIIRS 375 m por semana (clave = lunes); valor [tasa, n]",
        "NevadosDeChillan": tasa_semanal(recs_todos, VOL), "11_tier_a": tasa_semanal(recs_todos)}
    (HERE / "ndc_s141.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    figura_serie(recs, noct, diur, HERE / "ndc_serie_s141.png", ventana, recs_todos)
    figura_mapa(recs, HERE / "ndc_mapa_s141.png", ventana)
    print(json.dumps({k: out[k] for k in ("meta", "sin_fondo_viirs375", "oblicuas_viirs375",
                                          "ratio_nuestro_mirova_v375_en_alertas",
                                          "publicadas_por_distancia_al_crater_viirs375")}, indent=1, ensure_ascii=False, default=str))
    print("metricas V375:", json.dumps(out["metricas_banco"]["VIIRS375"], ensure_ascii=False))
    print("por mes V375:", json.dumps(out["viirs375_por_mes"], ensure_ascii=False))
    print("alertas nocturnas:", [(x["fecha_utc"], x["sensor"], x["vrp_mw"], x["dist_km"], x["clase"]) for x in out["alertas_mirova_nocturnas"]])
    print("alertas diurnas:", [(x["fecha_utc"], x["sensor"], x["vrp_mw"], x["dist_km"]) for x in out["alertas_mirova_diurnas"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
