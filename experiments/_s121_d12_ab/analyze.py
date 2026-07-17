# D12 A/B — analiza si el ancla honesta MODIS cura el FN Láscar SIN destapar los path-D.
# Compara A/B (ancla ON, artifacts run 29582035729) vs baseline operacional (ancla OFF).
# Ventana: 2025-02-15..2025-05-15 (la del reproc). Números source-of-truth (S91).
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
AB = Path(r"C:/Users/nmend/AppData/Local/Temp/claude/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/b09401b4-086e-4e7d-87bb-d84d2ae39eb9/scratchpad/d12_ab")
BASE = REPO / "data" / "mirova_equivalent"
LO, HI = "2025-02-15", "2025-05-15"
INNER = {"Lascar": 5, "NevadosDeChillan": 5, "PuyehueCordonCaulle": 20, "Tupungatito": 7}


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def modis_in_window(recs):
    """dict (datetime_utc, sensor) -> record, MODIS en ventana."""
    out = {}
    for r in recs:
        if not r.get("sensor", "").startswith("MODIS"):
            continue
        dt = r.get("datetime_utc", "")
        if not (LO <= dt[:10] <= HI):
            continue
        out[(dt, r["sensor"])] = r
    return out


def is_path_d_only(r):
    d = r.get("diag_n_dnti_ctx_path") or 0
    others = sum(r.get(k) or 0 for k in
                 ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
    return d > 0 and others == 0


print(f"D12 A/B — ventana {LO}..{HI}\n")
for vol in ["Lascar", "NevadosDeChillan", "PuyehueCordonCaulle", "Tupungatito"]:
    ab = modis_in_window(load(AB / vol / f"{vol}.json"))
    base = modis_in_window(load(BASE / f"{vol}.json"))
    inner = INNER[vol]
    common = sorted(set(ab) & set(base))

    # transiciones de distance_class base→ab
    far2summit = summit2far = same = 0
    # cura: far→summit con cluster crateriano (pc<=inner) = el FN recuperado
    cured_nights = set()
    # destape: far→summit con path-D-only y pc.vrp>5 = artefacto promovido
    destape = []
    for k in common:
        b, a = base[k], ab[k]
        bc, ac = b.get("distance_class"), a.get("distance_class")
        if bc == "far" and ac == "summit":
            far2summit += 1
            pc = a.get("primary_cluster") or {}
            cd, v = pc.get("centroid_dist_km"), pc.get("vrp_mw") or 0
            if cd is not None and cd <= inner:
                cured_nights.add(k[0][:10])
            if is_path_d_only(a) and v > 5:
                destape.append((k[0][:10], round(v, 1), round(cd or -1, 1)))
        elif bc == "summit" and ac == "far":
            summit2far += 1
        else:
            same += 1

    tag = "CURA (Láscar)" if vol == "Lascar" else "DESTAPE-watch (nevado)"
    print(f"=== {vol} [{tag}] — {len(common)} records MODIS comunes")
    print(f"    far→summit: {far2summit}  | summit→far: {summit2far}  | sin cambio: {same}")
    print(f"    noches curadas (far→summit con cluster ≤{inner}km): {len(cured_nights)}")
    if destape:
        print(f"    ⚠ DESTAPE path-D pc.vrp>5 promovidos: {len(destape)}")
        for d in destape[:8]:
            print(f"       {d[0]}  {d[1]} MW  @{d[2]}km")
    else:
        print(f"    ✓ destape path-D pc.vrp>5: 0")
    print()
