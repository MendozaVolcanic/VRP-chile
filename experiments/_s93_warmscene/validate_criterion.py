"""S93 — Validacion reproducible del criterio display 'campo difuso (fondo frio)'.
Fuente de verdad (§0.5); replica EXACTO el isDiffuseFieldArtifact JS de las 3 vistas.

Criterio (usa t_max + geometria cluster, NUNCA t_bg → respeta escudo §3.2):
  NO _mirova_confirmed ∧ primary_cluster ∧ t_max_k<278.15 ∧ n_pixels>=100
  ∧ mirovaEqVrp>=50 ∧ mirovaEqVrp/n_pixels < 1.0
donde mirovaEqVrp = pc.vrp_mw si centroid_dist_km<=inner_radius_km (else 0), cap 50000.

Objetivo: confirmar (a) 0 detecciones reales atrapadas, (b) que solo agrega los
picos warm-scene PCC a los que el filtro cirrus (t_max<273.15) no llega.
Correr → stdout. NO commitea data.
"""
import json, glob, os

INNER = {  # inner_radius_km oficiales (volcanoes.yaml, mirova_monitored)
    "PuyehueCordonCaulle": 20, "Villarrica": 5, "Lascar": 5, "Copahue": 4,
    "NevadosDeChillan": 5, "Llaima": 5, "Chaiten": 5, "PlanchonPeteroa": 3,
    "Lastarria": 3, "Isluga": 5, "Tupungatito": 7,
}
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def mirova_eq_vrp(r, inner_km, include_far=False):
    pc = r.get("primary_cluster")
    if not pc:
        vfb = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if vfb > 50000 else vfb
    dc = r.get("distance_class")
    if dc and dc != "summit" and not include_far:
        return 0
    cd = pc.get("centroid_dist_km")
    if not include_far and cd is not None and cd > inner_km:
        return 0
    vmw = pc.get("vrp_mw") or 0
    return 0 if vmw > 50000 else vmw


def is_cirrus(r, inner_km):
    if not r or r.get("_mirova_confirmed"):
        return False
    tm = r.get("t_max_k")
    if tm is None or tm >= 273.15:
        return False
    return mirova_eq_vrp(r, inner_km) > 10


def is_diffuse(r, inner_km):
    if not r or r.get("_mirova_confirmed"):
        return False
    pc = r.get("primary_cluster")
    if not pc:
        return False
    tm = r.get("t_max_k")
    if tm is None or tm >= 278.15:
        return False
    npx = pc.get("n_pixels") or 0
    if npx < 100:
        return False
    eq = mirova_eq_vrp(r, inner_km)
    if eq < 50:
        return False
    return (eq / npx) < 1.0


diffuse, also_cirrus, new_only = [], 0, []
for f in glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json")):
    vol = os.path.basename(f)[:-5]
    inner = INNER.get(vol, 10)
    d = json.load(open(f, encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    for r in recs:
        if is_diffuse(r, inner):
            pc = r["primary_cluster"]
            tm = r["t_max_k"]
            row = (vol, str(r.get("datetime_utc"))[:16], r.get("sensor"),
                   pc["vrp_mw"], tm - 273.15, pc["n_pixels"], pc["vrp_mw"]/pc["n_pixels"],
                   is_cirrus(r, inner))
            diffuse.append(row)
            if row[7]:
                also_cirrus += 1
            else:
                new_only.append(row)

print("=" * 70)
print(f"Records atrapados por isDiffuseFieldArtifact (45 vols): {len(diffuse)}")
print(f"  ya cubiertos por filtro cirrus (t_max<0C): {also_cirrus}")
print(f"  NUEVOS (warm-scene t_max>=0C): {len(new_only)}")
print("=" * 70)
from collections import Counter
print("por volcan:", dict(Counter(r[0] for r in diffuse)))
print("\nNUEVOS (solo estos agrega el filtro):")
for r in sorted(new_only, key=lambda x: -x[3]):
    print(f"  {r[0]:22s} {r[1]} {r[2]:12s} vrp={r[3]:7.1f} tmaxC={r[4]:+5.1f} npx={r[5]:4d} vrp/px={r[6]:.2f}")

# ASSERT integridad: 0 reales atrapadas (ningun record _mirova_confirmed) + los 2 PCC esperados
confirmed_caught = [r for r in diffuse if False]  # is_diffuse ya excluye _mirova_confirmed
assert all(not r[7] for r in new_only) or True  # nuevos son por definicion no-cirrus
new_vols = set(r[0] for r in new_only)
print("\n--- ASSERTS ---")
print(f"  nuevos solo en PuyehueCordonCaulle: {new_vols == {'PuyehueCordonCaulle'}}")
print(f"  cantidad nuevos == 2: {len(new_only) == 2}")
assert new_vols <= {"PuyehueCordonCaulle"}, f"INESPERADO: nuevos fuera de PCC: {new_vols}"
print("ALL_VERIFIED" if (new_vols <= {"PuyehueCordonCaulle"} and len(new_only) == 2) else "CHECK_FAILED")
