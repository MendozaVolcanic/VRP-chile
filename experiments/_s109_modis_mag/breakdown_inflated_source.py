"""S109 §1 — desglose de records MODIS inflados (pc.vrp_mw>5) por path de origen.
Pivote: ¿son src=test1 (ctxpeak aplicaría) o path-D/eruption (no)? Read-only sobre JSON."""
import json, statistics as st
from collections import Counter

VOLS = ["Chaiten","Villarrica","Llaima","Tupungatito","PuyehueCordonCaulle","Lascar"]
DATA = "data/mirova_equivalent/{}.json"

def is_modis(s):
    s = (s or "").upper()
    return s.startswith("MODIS") or s.startswith("AQUA") or s.startswith("TERRA")

def med(xs):
    return round(st.median(xs),2) if xs else None

print(f"{'VOL':<22}{'nMODIS':>7}{'nInfl':>6} | source breakdown of inflated (pc.vrp>5)")
print("-"*100)
all_sensors = Counter()
grand = Counter()
for v in VOLS:
    try:
        d = json.load(open(DATA.format(v), encoding="utf-8"))
    except FileNotFoundError:
        print(f"{v:<22} FILE NOT FOUND"); continue
    recs = d["records"] if isinstance(d,dict) and "records" in d else d
    modis = [r for r in recs if is_modis(r.get("sensor"))]
    for r in modis: all_sensors[r.get("sensor")] += 1
    infl = []
    for r in modis:
        pc = r.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw")
        if vrp is not None and vrp > 5:
            infl.append(r)
    src_ct = Counter(r.get("final_hotspot_source") for r in infl)
    trig_t1 = sum(1 for r in infl if r.get("triggered_test1"))
    # de los inflados: ¿cuántos tienen dNTI contextual disponible (ingrediente de ctxpeak)?
    has_dnti = sum(1 for r in infl if (r.get("diag_n_dnti_ctx_path") or 0) > 0)
    npix = [ (r.get("primary_cluster") or {}).get("n_pixels") for r in infl ]
    npix = [n for n in npix if n is not None]
    dt = [ (r.get("t_max_k") or 0) - (r.get("t_bg_k") or 0) for r in infl if r.get("t_max_k") and r.get("t_bg_k") ]
    for k,c in src_ct.items(): grand[k]+=c
    print(f"{v:<22}{len(modis):>7}{len(infl):>6} | src={dict(src_ct)} trig_t1={trig_t1} dNTI>0={has_dnti} medNpix={med(npix)} medDT={med(dt)}K")

print("-"*100)
print("SENSORS MODIS encontrados:", dict(all_sensors))
print("GRAND source breakdown inflados:", dict(grand))

# --- S109 adendum: qué path marca los píxeles en los inflados eruption ---
print("\n\n=== PATH COUNTS en inflados eruption (qué test marca el campo difuso) ===")
print(f"{'VOL':<22}{'n':>4} | medianas de diag_n_*_path por record inflado-eruption")
for v in VOLS:
    try:
        d = json.load(open(DATA.format(v), encoding="utf-8"))
    except FileNotFoundError:
        continue
    recs = d["records"] if isinstance(d,dict) and "records" in d else d
    infl_e = [r for r in recs if is_modis(r.get("sensor"))
              and (r.get("primary_cluster") or {}).get("vrp_mw",0) > 5
              and r.get("final_hotspot_source")=="eruption"]
    if not infl_e: 
        print(f"{v:<22}{0:>4} | (sin inflados eruption)"); continue
    def mp(key): 
        xs=[r.get(key,0) or 0 for r in infl_e]; return round(st.median(xs),1)
    print(f"{v:<22}{len(infl_e):>4} | bt={mp('diag_n_bt_path')} nti_abs={mp('diag_n_nti_path')} "
          f"dnti_ctx={mp('diag_n_dnti_ctx_path')} eti={mp('diag_n_eti_path')} "
          f"2ndpass={mp('diag_n_second_pass_recapture')} nAnom={mp('n_anomalous_pixels')} pcNpix={round(st.median([(r.get('primary_cluster') or {}).get('n_pixels',0) for r in infl_e]),1)}")
