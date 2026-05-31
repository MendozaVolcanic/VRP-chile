"""S94 F5' — calibración de las 3 variantes espaciales de magnitud campo-frío.

Pre-escrito mientras corre el reproc (A16). Implementa D1/D2/D3 del design doc
(docs/superpowers/specs/2026-05-31-f5-coldfield-magnitude-design.md) y las compara
contra MIROVA por volcán. Correr sobre data REPROCESADA consistente:
  VRP_DATA_DIR=data/_s94_reproc_viirs python experiments/_s94_audit/f5_variants.py

⚠️ A48: `anomaly_pixels[].dist_km` está medido desde el CENTRO del volcán, NO desde
el vent (verificado: pixel a 0.06km del vent reporta dist_km=2.76). Por eso TODAS las
variantes recomputan la distancia desde el vent (volcanoes.yaml vent_lat/lon) con
haversine sobre lat/lon. NO usar dist_km.

Cada variante toma los anomaly_pixels (lat/lon/bt_k/vrp_mw) del record y devuelve una
magnitud. Detección NO se toca (esto es post-proceso del set ya detectado).
"""
import sys, os, io, json, math, datetime as dt
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
import yaml
from pipeline.mirova_csv_loader import load_mirova_alertas

DATA_DIR = os.path.join(REPO, os.environ.get("VRP_DATA_DIR", "data/mirova_equivalent"))
CONS = os.path.join(REPO, "latest_consolidado.csv")
OCR = os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv")
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]

# Parámetros default (a barrer en calibración fina)
D1_R, D1_KMIN = 1.5, 3       # densidad: radio km, vecinos mínimos
D2_RCORE, D2_BTEXT = 2.0, 295.0  # radial: radio km del pico, bt_k extensión (lava real)
D3_C = 3.0                   # trimming: factor MAD


def load_vents():
    y = yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml"), encoding="utf-8"))
    vs = y["volcanoes"] if isinstance(y, dict) and "volcanoes" in y else y
    out = {}
    for v in vs:
        n = v.get("name") or v.get("id")
        if n in TIER_A:
            out[n] = (v.get("vent_lat") or v.get("lat"), v.get("vent_lon") or v.get("lon"))
    return out


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "").strip())
    except Exception:
        return None


# === Variantes ===

def baseline(pixels, vent):
    """Suma de todos los píxeles = magnitud actual (lo que infla)."""
    return sum(p.get("vrp_mw") or 0 for p in pixels)


def variant_d1(pixels, vent, r=D1_R, k_min=D1_KMIN):
    """Núcleo por densidad (DBSCAN-like): core points con >=k_min vecinos en r km.
    Excepción de seguridad: siempre conservar el píxel pico + sus vecinos <0.5km."""
    n = len(pixels)
    if n == 0:
        return 0.0
    co = [(p["lat"], p["lon"]) for p in pixels]
    keep = set()
    for i in range(n):
        cnt = sum(1 for j in range(n) if j != i and hav(*co[i], *co[j]) <= r)
        if cnt >= k_min:
            keep.add(i)
    peak = max(range(n), key=lambda i: pixels[i].get("vrp_mw") or 0)
    keep.add(peak)
    for j in range(n):
        if hav(*co[peak], *co[j]) <= 0.5:
            keep.add(j)
    return sum(pixels[i].get("vrp_mw") or 0 for i in keep)


def variant_d2(pixels, vent, r_core=D2_RCORE, bt_ext=D2_BTEXT):
    """Radial desde el pico (anclado al vent). Suma píxeles dentro de r_core del pico;
    extiende a píxeles calientes de verdad (bt>=bt_ext = lava, no halo)."""
    n = len(pixels)
    if n == 0:
        return 0.0
    # pico = píxel más cercano al vent entre el top-5 por vrp (vent-anchored)
    top = sorted(range(n), key=lambda i: -(pixels[i].get("vrp_mw") or 0))[:5]
    peak = min(top, key=lambda i: hav(pixels[i]["lat"], pixels[i]["lon"], *vent))
    pc = (pixels[peak]["lat"], pixels[peak]["lon"])
    tot = 0.0
    for p in pixels:
        d = hav(p["lat"], p["lon"], *pc)
        if d <= r_core or (p.get("bt_k") or 0) >= bt_ext:
            tot += p.get("vrp_mw") or 0
    return tot


def variant_d3(pixels, vent, c=D3_C):
    """Trimming robusto de outliers de distancia al VENT (mediana + c·MAD)."""
    n = len(pixels)
    if n == 0:
        return 0.0
    dists = [hav(p["lat"], p["lon"], *vent) for p in pixels]
    med = median(dists)
    mad = median([abs(d - med) for d in dists]) or 0.001
    thr = med + c * mad
    return sum(p.get("vrp_mw") or 0 for p, d in zip(pixels, dists) if d <= thr)


VARIANTS = {"baseline": baseline, "D1_dens": variant_d1, "D2_radial": variant_d2, "D3_trim": variant_d3}


def main():
    vents = load_vents()
    per = {v: {k: [] for k in VARIANTS} for v in TIER_A}
    for vol in TIER_A:
        p = os.path.join(DATA_DIR, f"{vol}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
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
        vent = vents.get(vol)
        if not vent or vent[0] is None:
            continue
        for r in recs:
            s = str(r.get("sensor", "")).upper()
            if not (s.startswith("VIIRS") and not s.endswith("_750")):
                continue
            if (r.get("primary_cluster") or {}).get("vrp_mw", 0) <= 0:
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
            px = [p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
            for k, fn in VARIANTS.items():
                per[vol][k].append(fn(px, vent) / mv)

    print("=" * 96)
    print(f"F5' VARIANTES — ratio mediano vs MIROVA por volcán | data={os.path.relpath(DATA_DIR, REPO)}")
    print(f"params: D1(r={D1_R},k={D1_KMIN}) D2(R={D2_RCORE},bt={D2_BTEXT}) D3(c={D3_C})")
    print("=" * 96)
    print(f"{'Volcán':<20}{'n':>5}{'baseline':>11}{'D1_dens':>11}{'D2_radial':>11}{'D3_trim':>11}")
    agg = {k: [] for k in VARIANTS}
    for vol in TIER_A:
        row = per[vol]
        n = len(row["baseline"])
        if n == 0:
            continue
        meds = {k: median(row[k]) for k in VARIANTS}
        for k in VARIANTS:
            agg[k].append(meds[k])
        print(f"{vol:<20}{n:>5}" + "".join(f"{meds[k]:>10.2f}×" for k in VARIANTS))
    print("-" * 96)
    print(f"{'MEDIANA cross-vol':<20}{'':>5}" + "".join(
        f"{(median(agg[k]) if agg[k] else 0):>10.2f}×" for k in VARIANTS))
    print("\nObjetivo: la variante con cross-vol más cerca de 1× Y Láscar 0.9-1.1× Y")
    print("ningún volcán <<1 (sub-conteo). Barrer params después de elegir la forma.")


if __name__ == "__main__":
    main()
