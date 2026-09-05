# -*- coding: utf-8 -*-
"""S133 - Mapa de foco de Villarrica: donde detecta cada sistema, sobre el crater real.

FICHA SDA - producto de ANALISIS, read-only. No participa de la deteccion ni escribe en
`data/`. Es una lupa de lectura sobre records ya calculados.

POR QUE ESTE MAPA, y por que Villarrica ahora. Villarrica tiene un lago de lava permanente
y debil, de decimas de MW, y en agosto de 2026 subio: MIROVA publico 12 alertas contra las
0-5 de los meses previos, y el 2026-09-04 a las 07:50 UTC marco 4,75 MW en MODIS. Cuando un
volcan se activa, la pregunta operacional deja de ser "cuanto" y pasa a ser "DONDE": si el
calor esta en el crater o si es el valle tibio de baja altitud que el MIR absoluto capta
como anomalia (A69). Esa pregunta solo se responde mirando, no con un numero de distancia.

EL DETALLE QUE ESTE MAPA HACE VISIBLE. La coordenada de catalogo de Villarrica
(-39,42 / -71,93) NO es el crater: esta a ~0,85 km al NE del crater real
(-39,420292 / -71,939908). Nuestras distancias se miden desde el catalogo, asi que una
deteccion EXACTAMENTE en el crater aparece reportada a ~0,85 km. Es la idiosincrasia que
CLAUDE.md documenta en A13 y por eso el mapa se centra en el CRATER, no en el catalogo:
sobre el crater se ve que 0,85 km no es un error de puntería sino la distancia entre dos
puntos de referencia.

Uso:
    python experiments/_s133_villarrica_focus/plot_mapa_villarrica.py [desde_YYYY-MM-DD]
"""
import io
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "_s124_ndc_focus"))
from basemap import satelital_km, ATRIBUCION  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

# Crater real (S51/S52, verificado; ver A13 en CLAUDE.md). El catalogo GVP esta a 0,85 km.
CRATER = (-39.420292, -71.939908)
CATALOGO = (-39.42, -71.93)              # volcanoes.yaml lat/lon — desde aca medimos dist
MIROVA_CENTRO = (-39.42177, -71.93391)   # centro de grilla del KMZ VIIRS750 (S80)
FOCO_KM = 0.5
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-08-01"
# Media ventana del mapa. POR QUE es argumento y no constante: con 1,6 km se ve el crater
# pero se ESCONDE mas de la mitad de las detecciones (la mediana de VIIRS375 al crater es
# 2,78 km). Un mapa que recorta sin decirlo miente por omision, asi que se generan las dos
# vistas: la del crater y la del inner completo de 5 km.
HALF_KM = float(sys.argv[2]) if len(sys.argv) > 2 else 1.6


def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2
         + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def km_xy(lat, lon):
    """Coordenadas locales en km respecto del CRATER (Este+, Norte+)."""
    return ((lon - CRATER[1]) * 111.32 * math.cos(math.radians(CRATER[0])),
            (lat - CRATER[0]) * 111.32)


def cargar():
    """Clusters con centroide, separados por sensor. Solo los que el dashboard publica."""
    d = json.loads((ROOT / "data/mirova_equivalent/Villarrica.json").read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    out = {"VIIRS375": [], "VIIRS750": [], "MODIS": []}
    for r in recs:
        if not isinstance(r, dict):
            continue
        f = str(r.get("datetime_utc") or "")
        if f[:10] < DESDE:
            continue
        s = str(r.get("sensor") or "")
        if s.startswith("MODIS"):
            k = "MODIS"
        elif s.startswith("VIIRS"):
            k = "VIIRS750" if s.endswith("750") else "VIIRS375"
        else:
            continue
        pc = r.get("primary_cluster") or {}
        lat, lon = pc.get("centroid_lat"), pc.get("centroid_lon")
        # La magnitud que el operador ve en VIIRS375 es el nucleo (f5_core), no pc.vrp_mw
        # (regla A10, matiz S132). Para los otros dos sensores el dashboard usa pc.vrp_mw.
        v = r.get("f5_core_vrp_mw") if k == "VIIRS375" else None
        if v is None:
            v = pc.get("vrp_mw")
        if lat is None or lon is None or not v or v <= 0:
            continue
        out[k].append({"lat": lat, "lon": lon, "vrp": float(v), "fecha": f[:16],
                       "clase": r.get("distance_class"),
                       "dist_cat": r.get("final_hotspot_dist_km")})
    return out


def main():
    datos = cargar()
    fig, ax = plt.subplots(figsize=(11.5, 11.5))

    img, extent = satelital_km(CRATER[0], CRATER[1], HALF_KM, zoom=15 if HALF_KM < 3 else 13)
    if img is not None:
        ax.imshow(img, extent=extent, zorder=0)

    # Grilla de MIROVA reproyectada: celdas de ~1 km (MODIS), ancladas a su centro.
    # POR QUE dibujarla: MIROVA no reporta un punto, reporta la celda de su grilla, y por
    # eso su distancia viene cuantizada (D15). Sin la grilla, comparar su "1,41 km" con
    # nuestro "0,85 km" parece un desacuerdo de puntería y es otra cosa.
    cx, cy = km_xy(*MIROVA_CENTRO)
    paso = 1.0
    for i in range(-int(HALF_KM)-1, int(HALF_KM)+2):
        ax.axvline(cx + i * paso, color="#d94801", lw=0.6, alpha=0.55, zorder=1)
        ax.axhline(cy + i * paso, color="#d94801", lw=0.6, alpha=0.55, zorder=1)

    t = [i * math.pi / 180 for i in range(0, 361)]
    ax.plot([FOCO_KM * math.cos(a) for a in t], [FOCO_KM * math.sin(a) for a in t],
            "--", color="#1b7837", lw=2.6, zorder=4,
            label="foco de %d m" % int(FOCO_KM * 1000))

    estilos = {
        "VIIRS375": dict(color="#2171b5", marker="o", label="VIIRS 375 m (nucleo F5')"),
        "VIIRS750": dict(color="#6a51a3", marker="s", label="VIIRS 750 m"),
        "MODIS": dict(color="#cb181d", marker="^", label="MODIS 1 km"),
    }
    for k, st in estilos.items():
        pts = datos[k]
        if not pts:
            continue
        xs, ys, ss = [], [], []
        for p in pts:
            x, y = km_xy(p["lat"], p["lon"])
            xs.append(x); ys.append(y)
            # area proporcional a log(VRP) para que un evento de 4 MW no tape los de 0,05
            ss.append(28 + 120 * math.log10(1 + p["vrp"] / 0.05))
        dentro = sum(1 for p in pts if hav(p["lat"], p["lon"], *CRATER) <= FOCO_KM)
        ax.scatter(xs, ys, s=ss, c=st["color"], marker=st["marker"], alpha=0.72,
                   edgecolors="white", linewidths=0.8, zorder=5,
                   label="%s — %d de %d en el foco" % (st["label"], dentro, len(pts)))

    # El evento que motivo el mapa
    ev = [p for p in datos["MODIS"] if p["fecha"].startswith("2026-09-04 07:50")]
    if ev:
        x, y = km_xy(ev[0]["lat"], ev[0]["lon"])
        ax.annotate("MODIS 04-sep 07:50 UTC\n%.2f MW (MIROVA: 4,75)" % ev[0]["vrp"],
                    xy=(x, y), xytext=(x + 0.42, y + 0.52), zorder=8,
                    fontsize=10, color="#67000d", weight="bold",
                    path_effects=[pe.withStroke(linewidth=3, foreground="white")],
                    arrowprops=dict(arrowstyle="->", color="#67000d", lw=1.8))

    ax.plot(0, 0, marker="*", ms=26, color="#ffd92f", mec="black", mew=1.4, zorder=9,
            label="crater real (-39,420292 / -71,939908)")
    xc, yc = km_xy(*CATALOGO)
    ax.plot(xc, yc, marker="P", ms=15, color="#f16913", mec="black", mew=1.1, zorder=9,
            label="coordenada de catalogo — a %.2f km del crater\n"
                  "(nuestras distancias se miden desde aca: A13)"
                  % hav(*CATALOGO, *CRATER))
    ax.plot(cx, cy, marker="X", ms=13, color="#d94801", mec="black", mew=1.1, zorder=9,
            label="centro de la grilla de MIROVA")

    ax.set_xlim(-HALF_KM, HALF_KM); ax.set_ylim(-HALF_KM, HALF_KM)
    ax.set_aspect("equal")
    ax.set_xlabel("km al Este del crater"); ax.set_ylabel("km al Norte del crater")
    ax.set_title("Villarrica — donde detecta cada sensor desde %s\n"
                 "(coordenadas en km respecto del crater real)" % DESDE,
                 fontsize=14, weight="bold")
    ax.grid(alpha=0.18, lw=0.5)
    ax.text(0.985, 0.015, ATRIBUCION, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="white",
            path_effects=[pe.withStroke(linewidth=2.5, foreground="black")])
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.09), fontsize=10, framealpha=0.95)

    dest = AQUI / ("villarrica_foco_s133.png" if HALF_KM < 3 else "villarrica_inner_s133.png")
    fig.savefig(dest, dpi=155, bbox_inches="tight")
    print("Escrito:", dest)
    for k in ("VIIRS375", "VIIRS750", "MODIS"):
        pts = datos[k]
        if not pts:
            print("  %-9s sin detecciones desde %s" % (k, DESDE)); continue
        dentro = sum(1 for p in pts if hav(p["lat"], p["lon"], *CRATER) <= FOCO_KM)
        med = sorted(hav(p["lat"], p["lon"], *CRATER) for p in pts)[len(pts) // 2]
        print("  %-9s n=%-4d  en el foco de %d m: %-4d  dist mediana al crater: %.2f km"
              % (k, len(pts), int(FOCO_KM * 1000), dentro, med))


if __name__ == "__main__":
    main()
