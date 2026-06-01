"""S97 — Verificación A2: ¿el reproc (staging, post-#294/#297) entrega lo prometido?

Corre la MISMA métrica F5' (Núcleo vs Cluster vs MIROVA) que S96 pero parametrizando
el directorio de data y restringiendo a una ventana común, para comparar apples-to-apples:
  - LIVE  (data/mirova_equivalent, código viejo, anomaly_pixels ralo)
  - STAGING (data/_s94_reproc_viirs, post-#294/#297, anomaly_pixels poblado)

Agrega lo que S96 no tabulaba: TASA DE FALLBACK (records VIIRS375 con Núcleo>0 que caen
al cluster por no tener anomaly_pixels que cubran el cluster). Hipótesis: en staging cae
fuerte porque #294 puebla anomaly_pixels.

Uso: python verify_staging_vs_live.py <data_dir> [YYYY-MM-DD start] [YYYY-MM-DD end]
Integridad §0.5: todo a archivo, números desde el script.
"""
import sys, os, io, json
from statistics import median
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "experiments", "_s94_audit"))
_fd = os.dup(1)
from f5_variants import hav, load_vents, parse
from pipeline.mirova_csv_loader import load_mirova_alertas
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "data/mirova_equivalent")
if not os.path.isabs(DATA):
    DATA = os.path.join(REPO, DATA)
WIN_START = sys.argv[2] if len(sys.argv) > 2 else None
WIN_END = sys.argv[3] if len(sys.argv) > 3 else None
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
TIER = ["PuyehueCordonCaulle","Villarrica","Lascar","Copahue","NevadosDeChillan",
        "Llaima","Chaiten","PlanchonPeteroa","Lastarria","Isluga","Tupungatito"]
INNER = {"Lascar":5,"Lastarria":3,"Tupungatito":7,"Villarrica":5,"PuyehueCordonCaulle":20,
         "Copahue":4,"NevadosDeChillan":5,"Llaima":5,"Chaiten":5,"PlanchonPeteroa":3,"Isluga":5}
R_CORE = 0.75
BT_EXT = 295.0


def is_viirs375(sensor):
    s = str(sensor or "").upper()
    return s.startswith("VIIRS") and not s.endswith("_750")


def cluster_mag(r, inner):
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
    """Devuelve (valor, fallback_bool). fallback=True → se usó el cluster (no se curó)."""
    base = cluster_mag(r, inner)
    if base <= 0:
        return base, False
    if not is_viirs375(r.get("sensor")):
        return base, True
    pc = r.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None or clon is None:
        return base, True
    px = r.get("anomaly_pixels") or []
    cand = [p for p in px if p.get("lat") is not None and p.get("lon") is not None
            and hav(p["lat"], p["lon"], clat, clon) <= inner]
    if not cand:
        return base, True
    peak = max(range(len(cand)), key=lambda i: cand[i].get("vrp_mw") or 0)
    plat, plon = cand[peak]["lat"], cand[peak]["lon"]
    s = 0.0
    for i, p in enumerate(cand):
        if i == peak or hav(p["lat"], p["lon"], plat, plon) <= R_CORE or (p.get("bt_k") or 0) >= BT_EXT:
            s += (p.get("vrp_mw") or 0)
    if s <= 0:
        return base, True
    return (0 if s > 50000 else s), False


def in_win(t):
    if WIN_START and t.strftime("%Y-%m-%d") < WIN_START:
        return False
    if WIN_END and t.strftime("%Y-%m-%d") > WIN_END:
        return False
    return True


vents = load_vents()
rows_all = []  # (vol, dt, cluster, core, mirova, fallback)
for vol in TIER:
    p = os.path.join(DATA, f"{vol}.json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    recs = d.get("records", []) if isinstance(d, dict) else d
    cov = [parse(r.get("datetime_utc")) for r in recs if parse(r.get("datetime_utc"))]
    cov = [t for t in cov if in_win(t)]
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
        if not t or not in_win(t):
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

OUT.write("=" * 116 + "\n")
OUT.write(f"S97 VERIFY — DATA={os.path.relpath(DATA, REPO)}  win=[{WIN_START or '-'}..{WIN_END or '-'}]\n")
OUT.write("F5' Núcleo vs Cluster vs MIROVA (VIIRS375 ±60min). FALLBACK = Núcleo>0 pero usó cluster (no curó).\n")
OUT.write("=" * 116 + "\n")
OUT.write(f"{'Volcán':<20}{'n':>4}{'REGRES':>8}{'FALLBK':>8}{'fb%':>7}{'n(Co>0)':>9}{'medCl/MIR':>11}{'medCo/MIR':>11}{'mejor':>8}\n")
OUT.write("-" * 116 + "\n")
tot_reg = tot_fb = 0
for vol in TIER:
    rr = [x for x in rows_all if x[0] == vol]
    if not rr:
        continue
    reg = sum(1 for (_, _, cl, co, mv, fb) in rr if cl > 0 and co <= 0)
    # fallback entre los que tienen señal (cl>0): se usó cluster en vez de curar
    elig = [x for x in rr if x[2] > 0]
    fb_n = sum(1 for (_, _, cl, co, mv, fb) in elig if fb)
    fbpct = (100 * fb_n / len(elig)) if elig else 0
    tot_reg += reg; tot_fb += fb_n
    sub = [(cl, co, mv) for (_, _, cl, co, mv, fb) in rr if co > 0]
    if sub:
        mcl = median([cl / mv for (cl, co, mv) in sub])
        mco = median([co / mv for (cl, co, mv) in sub])
        better = "Núcleo" if abs(mco - 1) < abs(mcl - 1) else "Cluster"
        OUT.write(f"{vol:<20}{len(rr):>4}{reg:>8}{fb_n:>8}{fbpct:>6.0f}%{len(sub):>9}{mcl:>10.2f}×{mco:>10.2f}×{better:>8}\n")
    else:
        OUT.write(f"{vol:<20}{len(rr):>4}{reg:>8}{fb_n:>8}{fbpct:>6.0f}%{0:>9}{'—':>11}{'—':>11}{'—':>8}\n")
OUT.write("-" * 116 + "\n")
sub_all = [(cl, co, mv) for (_, _, cl, co, mv, fb) in rows_all if co > 0]
elig_all = [x for x in rows_all if x[2] > 0]
fbpct_all = (100 * tot_fb / len(elig_all)) if elig_all else 0
if sub_all:
    mcl = median([cl / mv for (cl, co, mv) in sub_all])
    mco = median([co / mv for (cl, co, mv) in sub_all])
    OUT.write(f"{'GLOBAL':<20}{len(rows_all):>4}{tot_reg:>8}{tot_fb:>8}{fbpct_all:>6.0f}%{len(sub_all):>9}{mcl:>10.2f}×{mco:>10.2f}×"
              f"{('Núcleo' if abs(mco-1)<abs(mcl-1) else 'Cluster'):>8}\n")
OUT.write(f"\nMatcheados: {len(rows_all)} | con señal Cluster>0: {len(elig_all)} | FALLBACK: {tot_fb} ({fbpct_all:.0f}%) | REGRESIONES: {tot_reg}\n")
OUT.flush()
