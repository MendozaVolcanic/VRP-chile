# C2 Paso 0 (S122, read-only) — ¿el blob path-D MODIS tiene núcleo separable?
#
# Pregunta física: la magnitud inflada del path-D contextual (PCC 117 MW, etc.) ¿viene
# de 1-2 píxeles pico (foco real sub-píxel → un peak-of-kernel lo aislaría → C2 viable)
# o de un campo plano de muchos píxeles tibios sin núcleo (→ D12 irreducible a 1 km,
# A82/A83 → cerrar el frente)?
#
# Método: sobre cada record MODIS path-D-only con pc.vrp>5 en la ventana del A/B S121,
# medir la concentración de radiancia (vrp_mw per-píxel) del blob y simular qué daría
# un "peak-of-kernel" (conservar solo el píxel pico, y pico+8-vecinos). Contrastar
# Láscar (la CURA, vol activo real) vs los nevados PCC/Tupun/NdC (el DESTAPE artefacto).
#
# Criterio pre-registrado (design 2026-07-17-c2-ctxpeak-modis-ab-design.md):
#   C2 VIABLE   si existe un peak-of-kernel que colapse los destapes nevados <5 MW
#               PERO mantenga la señal de Láscar (separación limpia).
#   C2 NO VIABLE si el peak-of-kernel colapsa AMBOS por igual (sin separación) →
#               no hay discriminante de magnitud a 1 km → D12 irreducible, cerrar.
#
# Los píxeles del blob son invariantes al ancla (verificado S122): el ancla solo cambia
# distance_class. Por eso se usa data/mirova_equivalent (versionado, reproducible, S91).
import json
import io
import sys
import math
import statistics
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "data" / "mirova_equivalent"
LO, HI = "2025-02-15", "2025-05-15"
VOLS = ["Lascar", "NevadosDeChillan", "PuyehueCordonCaulle", "Tupungatito"]
CURE = {"Lascar"}  # vol activo real = la cura; el resto son nevados (destape-watch)


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def is_path_d_only(r):
    d = r.get("diag_n_dnti_ctx_path") or 0
    others = sum(r.get(k) or 0 for k in
                 ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
    return d > 0 and others == 0


def haversine_km(a_lat, a_lon, b_lat, b_lon):
    R = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def peak_kernel_vrp(pixels):
    """Simula peak-of-kernel: VRP del píxel pico solo, y del pico+sus vecinos <=1.5km.
    1.5 km ~ radio de un kernel 3x3 de MODIS 1km (el vecindario inmediato del pico)."""
    if not pixels:
        return 0.0, 0.0, None
    pk = max(pixels, key=lambda p: p.get("vrp_mw") or 0)
    peak_v = pk.get("vrp_mw") or 0
    # pico + 8-vecinos: píxeles a <=1.5 km del pico
    kern = [p for p in pixels
            if haversine_km(pk["lat"], pk["lon"], p["lat"], p["lon"]) <= 1.5]
    kern_v = sum(p.get("vrp_mw") or 0 for p in kern)
    return peak_v, kern_v, pk


print(f"C2 Paso 0 — ¿blob path-D MODIS tiene núcleo? ventana {LO}..{HI}\n")

summary = {}
for vol in VOLS:
    recs = load(BASE / f"{vol}.json")
    rows = []
    for r in recs:
        if not r.get("sensor", "").startswith("MODIS"):
            continue
        dt = r.get("datetime_utc", "")
        if not (LO <= dt[:10] <= HI):
            continue
        pc = r.get("primary_cluster") or {}
        v = pc.get("vrp_mw") or 0
        if not (is_path_d_only(r) and v > 5):
            continue
        ap = r.get("anomaly_pixels") or []
        if not ap:
            continue
        vrps = sorted((p.get("vrp_mw") or 0) for p in ap)
        bts = [p.get("bt_k") or 0 for p in ap]
        s = sum(vrps)
        peak_v, kern_v, _ = peak_kernel_vrp(ap)
        rows.append({
            "dt": dt, "pcv": v, "sum_ap": s, "n": len(ap),
            "peak": vrps[-1], "top2": sum(vrps[-2:]),
            "ft1": vrps[-1] / s * 100 if s else 0,
            "ft5": sum(vrps[-5:]) / s * 100 if s else 0,
            "maxbt": max(bts), "medbt": statistics.median(bts),
            "peak_kernel": kern_v,
        })
    summary[vol] = rows
    tag = "CURA" if vol in CURE else "DESTAPE-watch"
    print(f"=== {vol} [{tag}] — {len(rows)} records path-D-only pc.vrp>5 MODIS")
    if not rows:
        print("    (ninguno)\n")
        continue
    peaks = [x["peak"] for x in rows]
    ft1s = [x["ft1"] for x in rows]
    pcs = [x["pcv"] for x in rows]
    kerns = [x["peak_kernel"] for x in rows]
    maxbts = [x["maxbt"] for x in rows]
    print(f"    pc.vrp_mw:      mediana {statistics.median(pcs):6.1f}  max {max(pcs):6.1f}")
    print(f"    píxel PICO vrp: mediana {statistics.median(peaks):6.2f}  max {max(peaks):6.2f}  (lo que dejaría peak-only)")
    print(f"    peak+kernel:    mediana {statistics.median(kerns):6.2f}  max {max(kerns):6.2f}  (pico+vecinos <=1.5km)")
    print(f"    frac top-1 px:  mediana {statistics.median(ft1s):6.1f}%  min {min(ft1s):.1f}%  max {max(ft1s):.1f}%")
    print(f"    max bt MIR (K): mediana {statistics.median(maxbts):6.1f}  max {max(maxbts):6.1f}")
    # ¿cuántos destapes caerían <5 MW con peak-only? ¿con peak+kernel?
    n_peak_lt5 = sum(1 for x in rows if x["peak"] < 5)
    n_kern_lt5 = sum(1 for x in rows if x["peak_kernel"] < 5)
    print(f"    peak-only <5MW: {n_peak_lt5}/{len(rows)}   peak+kernel <5MW: {n_kern_lt5}/{len(rows)}")
    print()

# Veredicto de separabilidad: solapamiento de píxel-pico entre CURA y DESTAPE
cure_peaks = [x["peak"] for v in CURE for x in summary[v]]
dest_peaks = [x["peak"] for v in VOLS if v not in CURE for x in summary[v]]
print("=" * 68)
print("SEPARABILIDAD peak-of-kernel (píxel pico): ¿separa CURA de DESTAPE?")
if cure_peaks and dest_peaks:
    print(f"  Láscar (cura) píxel-pico:   min {min(cure_peaks):.2f}  mediana {statistics.median(cure_peaks):.2f}  max {max(cure_peaks):.2f}  MW")
    print(f"  Nevados (destape) pico:     min {min(dest_peaks):.2f}  mediana {statistics.median(dest_peaks):.2f}  max {max(dest_peaks):.2f}  MW")
    overlap_lo = max(min(cure_peaks), min(dest_peaks))
    overlap_hi = min(max(cure_peaks), max(dest_peaks))
    print(f"  Rango de solapamiento: [{overlap_lo:.2f}, {overlap_hi:.2f}] MW")
    print(f"  → si solapan fuerte, NO hay umbral de píxel-pico que separe (A83 en magnitud).")
