"""S96 — F5' DISPLAY (Núcleo) vs Cluster vs MIROVA, sobre data LIVE.

Responde a Nicolás: (a) ¿hay records que MIROVA confirma y el Núcleo lleva a 0 MW?
(b) ¿cuál aproxima mejor a MIROVA, Cluster o Núcleo? Replica EXACTAMENTE el
algoritmo del display (frontend), NO el de la calibración S95 (que usaba ancla
global). Cruza contra MIROVA CONS+OCR real (VIIRS375).

Integridad §0.5: todo a archivo, números desde el script.
"""
import sys, os, io, json, math
from statistics import median
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "experiments", "_s94_audit"))
_fd = os.dup(1)
from f5_variants import hav, load_vents, parse
from pipeline.mirova_csv_loader import load_mirova_alertas
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

DATA = os.path.join(REPO, "data/mirova_equivalent")  # data LIVE (la del dashboard)
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
TIER = ["PuyehueCordonCaulle","Villarrica","Lascar","Copahue","NevadosDeChillan",
        "Llaima","Chaiten","PlanchonPeteroa","Lastarria","Isluga","Tupungatito"]
# inner_radius_km del frontend (INNER_RADIUS_KM en index/diario/mosaico)
INNER = {"Lascar":5,"Lastarria":3,"Tupungatito":7,"Villarrica":5,"PuyehueCordonCaulle":20,
         "Copahue":4,"NevadosDeChillan":5,"Llaima":5,"Chaiten":5,"PlanchonPeteroa":3,"Isluga":5}
R_CORE = 0.75
BT_EXT = 295.0


def is_viirs375(sensor):
    s = str(sensor or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def cluster_mag(r, inner):
    """Replica frontend mirovaEqVrp(r, inner, includeFar=false): summit-only."""
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def core_mag(r, inner):
    """Replica frontend mirovaEqVrpCore (display S96): VIIRS375 + ancla dentro de
    inner del centroide del cluster + guard A46/A07. Devuelve (valor, fallback_bool)."""
    base = cluster_mag(r, inner)
    if base <= 0:
        return base, False
    if not is_viirs375(r.get("sensor")):
        return base, True  # MODIS/V750 → cluster
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None or clon is None:
        return base, True
    px = r.get("anomaly_pixels") or []
    cand = [p for p in px if p.get("lat") is not None and p.get("lon") is not None
            and hav(p["lat"], p["lon"], clat, clon) <= inner]
    if not cand:
        return base, True  # guard: anomaly_pixels no cubre el cluster
    peak = max(range(len(cand)), key=lambda i: cand[i].get("vrp_mw") or 0)
    plat, plon = cand[peak]["lat"], cand[peak]["lon"]
    s = 0.0
    for i, p in enumerate(cand):
        if i == peak or hav(p["lat"], p["lon"], plat, plon) <= R_CORE or (p.get("bt_k") or 0) >= BT_EXT:
            s += (p.get("vrp_mw") or 0)
    # Guard S96: core <= 0 con base > 0 → anomaly_pixels no cargan la energía del
    # cluster (A46/A07) → fallback al cluster (nunca borrar una detección real).
    if s <= 0:
        return base, True
    return (0 if s > 50000 else s), False


vents = load_vents()
rows_all = []  # (vol, dt, cluster, core, mirova, fallback)
for vol in TIER:
    p = os.path.join(DATA, f"{vol}.json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    recs = d.get("records", [])
    cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
    if not cov:
        continue
    cmin, cmax = min(cov), max(cov)
    mir = []
    for a in load_mirova_alertas(CONS, OCR, volcano=vol):
        if a.get("sensor_bucket") != "VIIRS375" or (a.get("vrp_mw") or 0) <= 0:
            continue
        t = parse(a.get("fecha_utc"))
        if t and cmin <= t <= cmax:
            mir.append((t, a["vrp_mw"]))
    inner = INNER.get(vol, 5)
    for r in recs:
        if not is_viirs375(r.get("sensor")):
            continue
        t = parse(r.get("datetime_utc"))
        if not t:
            continue
        near = [mv for (mt, mv) in mir if abs((t - mt).total_seconds()) <= 3600]
        if not near:
            continue
        mv = min(mir, key=lambda x: abs((t - x[0]).total_seconds()))[1]
        if mv <= 0:
            continue
        cl = cluster_mag(r, inner)
        co, fb = core_mag(r, inner)
        rows_all.append((vol, r.get("datetime_utc"), cl, co, mv, fb))

OUT.write("=" * 108 + "\n")
OUT.write("F5' DISPLAY (Núcleo) vs Cluster vs MIROVA — data LIVE, VIIRS375 matcheado ±60min\n")
OUT.write("REGRESIÓN = Cluster>0 pero Núcleo=0 (señal real que el Núcleo BORRA). FN_pre = Cluster YA era 0.\n")
OUT.write("Ratios medianos calculados SOLO sobre records donde Núcleo>0 (excluye los ceros).\n")
OUT.write("=" * 108 + "\n")
OUT.write(f"{'Volcán':<20}{'n':>4}{'REGRES':>8}{'FN_pre':>8}{'n(Co>0)':>9}{'medCl/MIR':>11}{'medCo/MIR':>11}{'mejor':>8}\n")
OUT.write("-" * 108 + "\n")
tot_reg = tot_fnpre = 0
for vol in TIER:
    rr = [x for x in rows_all if x[0] == vol]
    if not rr:
        continue
    reg = sum(1 for (_, _, cl, co, mv, fb) in rr if cl > 0 and co <= 0)
    fnpre = sum(1 for (_, _, cl, co, mv, fb) in rr if cl <= 0 and co <= 0)
    tot_reg += reg; tot_fnpre += fnpre
    sub = [(cl, co, mv) for (_, _, cl, co, mv, fb) in rr if co > 0]
    if sub:
        mcl = median([cl / mv for (cl, co, mv) in sub])
        mco = median([co / mv for (cl, co, mv) in sub])
        better = "Núcleo" if abs(mco - 1) < abs(mcl - 1) else "Cluster"
        OUT.write(f"{vol:<20}{len(rr):>4}{reg:>8}{fnpre:>8}{len(sub):>9}{mcl:>10.2f}×{mco:>10.2f}×{better:>8}\n")
    else:
        OUT.write(f"{vol:<20}{len(rr):>4}{reg:>8}{fnpre:>8}{0:>9}{'—':>11}{'—':>11}{'—':>8}\n")
OUT.write("-" * 108 + "\n")
sub_all = [(cl, co, mv) for (_, _, cl, co, mv, fb) in rows_all if co > 0]
mcl = median([cl / mv for (cl, co, mv) in sub_all])
mco = median([co / mv for (cl, co, mv) in sub_all])
OUT.write(f"{'GLOBAL':<20}{len(rows_all):>4}{tot_reg:>8}{tot_fnpre:>8}{len(sub_all):>9}{mcl:>10.2f}×{mco:>10.2f}×"
          f"{('Núcleo' if abs(mco-1)<abs(mcl-1) else 'Cluster'):>8}\n")
OUT.write(f"\nRegresiones (Cluster>0 → Núcleo 0): {tot_reg}/{len(rows_all)} = {100*tot_reg/len(rows_all):.1f}% "
          f"de los matcheados.  FN pre-existentes (Cluster ya 0): {tot_fnpre}.\n\n")

# Detalle SOLO de las REGRESIONES (Cluster>0 → Núcleo 0) — lo que vio Nicolás
OUT.write("REGRESIONES (Cluster>0 → Núcleo 0, MIROVA>0) — señal real que el Núcleo borraría:\n")
reg_rows = [(v, dt, cl, co, mv) for (v, dt, cl, co, mv, fb) in rows_all if cl > 0 and co <= 0]
if not reg_rows:
    OUT.write("  NINGUNA.\n")
else:
    for (v, dt, cl, co, mv) in reg_rows[:40]:
        OUT.write(f"  {v:<20} {dt}  cluster={cl:.3f}  MIROVA={mv:.3f}\n")
OUT.write(f"\nTotal matcheados: {len(rows_all)} | REGRESIONES: {len(reg_rows)}\n")
