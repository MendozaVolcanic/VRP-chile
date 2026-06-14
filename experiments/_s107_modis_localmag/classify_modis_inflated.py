"""S108 — Clasificación A54/A68 de los records MODIS inflados (pc.vrp_mw > 5 MW)
que el A/B fondo-local (run 27480234385) debe curar. Sobre data base (flip OFF).

Pregunta (obligatoria ANTES de adoptar un fix de magnitud, A54/A68): ¿los inflados
son ARTEFACTO de método (cat-d: campo difuso MODIS 1km sumado, lejos del cráter, ΔT
bajo, MIROVA no publica) o SEÑAL REAL (cat-b: foco al cráter, ΔT alto, MIROVA publica)?
Si V-B cura cat-d -> bueno. Si destruye cat-b -> destruye valor (NO adoptar).

Ejes:
  - ESPACIAL (A61): dist al cráter (final_hotspot_dist_km / pc.centroid_dist_km).
  - TÉRMICO (A12): ΔT = t_max_k - t_bg_k. <12K difuso/sub-pixel; >20K foco caliente.
  - CRUCE MIROVA: ¿hubo ALERTA_TERMICA esa noche en latest_consolidado.csv?

Read-only. S91: este script es la fuente de verdad de los números.
Uso: python experiments/_s107_modis_localmag/classify_modis_inflated.py
"""
import csv
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VOLS = ["Chaiten", "Villarrica", "PuyehueCordonCaulle", "Tupungatito", "Llaima", "Lascar"]
INFLATE = 5.0
CSV_CONS = REPO / "latest_consolidado.csv"


def _recs(o):
    return o.get("records", o) if isinstance(o, dict) else o


def alert_nights(vol):
    out = set()
    if not CSV_CONS.exists():
        return out
    for r in csv.DictReader(open(CSV_CONS, encoding="utf-8", errors="replace")):
        if r.get("Volcan") == vol and str(r.get("Tipo_Registro", "")).startswith("ALERTA_TERMICA"):
            f = r.get("Fecha_Satelite_UTC") or r.get("Fecha_UTC") or ""
            if f:
                out.add(f[:10])
    return out


def main():
    print("=== Inflados MODIS pc.vrp>5 (data base, flip OFF) — clasificación A54 ===\n")
    grand = {"catd": 0, "catb": 0, "ambig": 0, "total": 0}
    for vol in VOLS:
        path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        recs = _recs(json.load(open(path, encoding="utf-8")))
        nights = alert_nights(vol)
        inflated = []
        for r in recs:
            if not str(r.get("sensor", "")).startswith("MODIS"):
                continue
            if str(r.get("datetime_utc", ""))[:4] != "2026":
                continue
            pc = r.get("primary_cluster") or {}
            pcv = pc.get("vrp_mw") or 0
            if pcv <= INFLATE:
                continue
            # A48/A68: la dist del CLUSTER (pc.centroid_dist_km) es la relevante para
            # clasificar el inflado — NO final_hotspot_dist_km (= píxel suelto lejano,
            # ej. Salar de Atacama D12). pc.vrp_mw es la magnitud DEL cluster.
            dist = pc.get("centroid_dist_km")
            dist_pixel = r.get("final_hotspot_dist_km")  # píxel suelto (diagnóstico)
            tmax = r.get("t_max_k")
            tbg = r.get("t_bg_k")
            dT = (tmax - tbg) if (tmax is not None and tbg is not None) else None
            nd = str(r.get("datetime_utc", ""))[:10]
            mirova = nd in nights
            inflated.append({"dt": r.get("datetime_utc"), "pcv": pcv, "dist": dist,
                             "dist_pixel": dist_pixel,
                             "dT": dT, "dc": r.get("distance_class"), "mirova": mirova,
                             "npx": pc.get("n_pixels")})
        if not inflated:
            print(f"{vol:<20} 0 inflados")
            continue

        # heurística de clasificación A54
        catd = catb = ambig = 0
        for x in inflated:
            far = x["dist"] is not None and x["dist"] > 5
            cool = x["dT"] is not None and x["dT"] < 12
            if x["mirova"]:
                catb += 1            # MIROVA publicó -> señal real (no destruir)
            elif far or cool:
                catd += 1            # difuso/lejos/frío sin MIROVA -> artefacto
            else:
                ambig += 1
        grand["catd"] += catd
        grand["catb"] += catb
        grand["ambig"] += ambig
        grand["total"] += len(inflated)

        dists = [x["dist"] for x in inflated if x["dist"] is not None]
        distsP = [x["dist_pixel"] for x in inflated if x["dist_pixel"] is not None]
        dTs = [x["dT"] for x in inflated if x["dT"] is not None]
        pcvs = [x["pcv"] for x in inflated]
        med = lambda xs: statistics.median(xs) if xs else None
        fmt = lambda v, s=".1f": (format(v, s) if v is not None else "—")
        print(f"{vol:<20} n={len(inflated):>3} | med pc.vrp={fmt(med(pcvs)):>6} "
              f"med dist_CLUSTER={fmt(med(dists),'.2f'):>7}km med dist_pixel={fmt(med(distsP),'.1f'):>6}km "
              f"med ΔT={fmt(med(dTs)):>5}K | cat-d={catd} cat-b={catb} ambig={ambig} "
              f"| max pc.vrp={fmt(max(pcvs)):>7}")

    print(f"\nTOTAL inflados={grand['total']} | cat-d artefacto={grand['catd']} "
          f"| cat-b real(MIROVA)={grand['catb']} | ambiguo={grand['ambig']}")
    print("Interpretación: V-B debe curar cat-d (artefacto difuso). Si baja cat-b "
          "(MIROVA publicó) bajo 5MW, revisar (¿destruye señal real?). Ambiguos -> "
          "inspección espacial/térmica individual (A61/A62).")


if __name__ == "__main__":
    main()
