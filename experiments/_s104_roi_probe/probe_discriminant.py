"""S105 Fase 2 — Probe del DISCRIMINANTE lava vs topografía (Villarrica VIIRS375).

Pregunta decisiva: ¿el NTI máximo CONCENTRADO en el núcleo (<1 km del cráter)
separa las pasadas con lava (MIROVA ALERTA) de las pasadas de pura topografía
(noche sin ALERTA)? El centroide promediado NO separa (pierde recall, S105 offline).
La hipótesis es que el PICO de NTI sí: lava = NTI_max en el núcleo destaca sobre el
anillo; topografía = el NTI_max cae en el anillo/valle, el núcleo no destaca.

Si el discriminante existe → fix = gate de foco NTI en el inner-radius (Enfoque 1) o
contraste núcleo/anillo (Enfoque 2). Si NO existe (la lava débil es inseparable del
ruido topográfico) → el offset es una limitación física irreducible, documentar.

Corre en GitHub Actions (secrets EARTHDATA; .netrc local roto A71). Parámetros:
  PROBE_DATE  (YYYY-MM-DD)
  PROBE_GROUP (lava|topo) — solo etiqueta para el reporte
  PROBE_TIMES (csv de tokens horarios a preferir, ej ".0548.,.0554.,.0600.")
"""
import sys, io, math, os
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline.fetch import search_granules, download_granules, _match_granules, auth
from pipeline.process_viirs import read_viirs_l1b, read_viirs_geo
from pipeline.test1_integrated import bt_to_radiance_um

auth()
VENTS = {  # vent_lat, vent_lon (volcanoes.yaml) — nevados
    "Villarrica": (-39.420227, -71.939876),
    "Tupungatito": (-33.389044, -69.826374),
    "Llaima": (-38.692, -71.729),
}
VOLCANO = os.environ.get("PROBE_VOLCANO", "Villarrica")
VLAT, VLON = VENTS[VOLCANO]
HERE = Path(__file__).parent
DEST = HERE / "granules_disc"; DEST.mkdir(exist_ok=True)
DATE = datetime.strptime(os.environ.get("PROBE_DATE", "2026-05-22"), "%Y-%m-%d")
GROUP = os.environ.get("PROBE_GROUP", "?")
TIMES = [t for t in os.environ.get(
    "PROBE_TIMES", ".0548.,.0554.,.0600.,.0542.,.0530.,.0536.,.0524.,.0506.,.0648.,.0642.").split(",") if t]
I04_L, I05_L = 3.74, 11.45
INNER_KM, ROI_KM = 1.0, 3.0
print(f"PROBE_VOLCANO={VOLCANO} PROBE_DATE={DATE.date()} GROUP={GROUP}", flush=True)


def gname(g):
    try: return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception: return str(g)[:60]


def analyze(sat, l1b_path, geo_path):
    bands = read_viirs_l1b(l1b_path)
    g = read_viirs_geo(geo_path)
    lat, lon = g["lat"], g["lon"]
    if "I04" not in bands or "I05" not in bands:
        print(f"  {sat}: falta I04/I05"); return
    i04, i05 = bands["I04"], bands["I05"]
    dist = np.hypot((lat - VLAT) * 111320,
                    (lon - VLON) * 111320 * math.cos(VLAT * math.pi / 180)) / 1000.0
    valid = np.isfinite(i04) & np.isfinite(i05)
    L4 = bt_to_radiance_um(i04, I04_L)
    L5 = bt_to_radiance_um(i05, I05_L)
    nti = np.where((L4 + L5) > 0, (L4 - L5) / (L4 + L5), np.nan)

    core = (dist <= INNER_KM) & valid & np.isfinite(nti)   # núcleo <1km
    ring = (dist > INNER_KM) & (dist <= ROI_KM) & valid & np.isfinite(nti)  # anillo 1-3km
    if core.sum() == 0 or ring.sum() < 20:
        print(f"  {sat}: cobertura insuficiente (core={int(core.sum())} ring={int(ring.sum())})"); return

    nti_bg = float(np.median(nti[ring]))
    nti_std = 1.4826 * float(np.median(np.abs(nti[ring] - nti_bg)))
    if nti_std <= 0:
        print(f"  {sat}: sigma_bg=0"); return

    # NTI máx en el núcleo y en el anillo (con su posición)
    def maxat(mask):
        m = np.where(mask, nti, -np.inf)
        iy, ix = np.unravel_index(np.argmax(m), m.shape)
        return nti[iy, ix], dist[iy, ix]
    nc, dc = maxat(core)   # pico del núcleo
    nr, dr = maxat(ring)   # pico del anillo
    sig_core = (nc - nti_bg) / nti_std   # cuántos σ destaca el pico del núcleo
    sig_ring = (nr - nti_bg) / nti_std
    # discriminante: el núcleo destaca Y supera al anillo
    disc = sig_core - sig_ring
    print(f"  {sat}: NTI_core_max={nc:.4f}@{dc:.2f}km ({sig_core:+.1f}sig) | "
          f"NTI_ring_max={nr:.4f}@{dr:.2f}km ({sig_ring:+.1f}sig) | "
          f"DISC(core-ring)={disc:+.1f}sig | bg={nti_bg:.4f} std={nti_std:.4f}", flush=True)
    # contraste integral (Enfoque 2): Σ exceso NTI núcleo vs anillo, normalizado por área
    exc = np.maximum(0.0, nti - nti_bg)
    sum_core = float(np.sum(exc[core])) / max(1, int(core.sum()))
    sum_ring = float(np.sum(exc[ring])) / max(1, int(ring.sum()))
    print(f"    excNTI/px nucleo={sum_core:.5f} anillo={sum_ring:.5f} ratio={sum_core/sum_ring if sum_ring>0 else float('inf'):.2f}", flush=True)


print(f"TIMES_pref={TIMES}", flush=True)
for sat in ["VIIRS_NOAA20", "VIIRS_SNPP", "VIIRS_NOAA21"]:
    print(f"\n=== {sat} ===", flush=True)
    try:
        l1b = search_granules(f"{sat}_L1B", VLAT, VLON, 25, DATE)
        geo = search_granules(f"{sat}_GEO", VLAT, VLON, 25, DATE)
    except Exception as e:
        print("  search FAIL", e); continue
    pairs = _match_granules(l1b, geo)
    picked = None
    for lg, gg in pairs:
        if any(t in gname(lg) for t in TIMES):
            picked = (lg, gg); break
    if not picked and pairs: picked = pairs[0]
    if not picked: print("  sin pares"); continue
    print("  granule:", gname(picked[0]), flush=True)
    try:
        paths = download_granules([picked[0], picked[1]], DEST)
        l1b_path = next(p for p in paths if "02IMG" in p.name)
        geo_path = next(p for p in paths if "03IMG" in p.name)
    except Exception as e:
        print("  download FAIL", type(e).__name__, str(e)[:80]); continue
    analyze(sat, l1b_path, geo_path)

print("\nDONE", flush=True)
