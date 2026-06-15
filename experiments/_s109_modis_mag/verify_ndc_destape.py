"""S109 — verificación del destape NdC del flip ancla MODIS (¿real cat-b o ruido?).
Read-only. Destape = record MODIS 'far' con cluster AL CRÁTER (lo que el ancla flipea a summit)."""
import json, statistics as st
from collections import Counter

INNER = 5.0  # NdC inner_radius_km
VENT = (-36.868, -71.378)  # cráter Nuevo/Arrau aprox (GVP NdC)
d = json.load(open('data/mirova_equivalent/NevadosDeChillan.json', encoding='utf-8'))
recs = d['records']
def is_modis(s): return (s or '').upper().startswith(('MODIS','AQUA','TERRA'))
def is_v375(s):
    s=(s or '').upper(); return s.startswith('VIIRS') and not s.endswith('_750')
def night(dt): return (dt or '')[:10]
def pcv(r): return float((r.get('primary_cluster') or {}).get('vrp_mw') or 0)

# destape: MODIS far, cluster al cráter, vrp>0
destape=[r for r in recs if is_modis(r.get('sensor'))
         and r.get('distance_class')=='far'
         and (r.get('primary_cluster') or {}).get('centroid_dist_km') is not None
         and (r.get('primary_cluster') or {})['centroid_dist_km'] <= INNER
         and pcv(r)>0]

# noches con VIIRS375 summit nuestro (señal real cross-sensor)
v375_nights={night(r.get('datetime_utc')) for r in recs
             if is_v375(r.get('sensor')) and r.get('distance_class')=='summit' and pcv(r)>0}
# noches MODIS summit ya (no-destape, ya contadas)
print(f"=== NdC destape MODIS (far con cluster al cráter = lo que el ancla flipea) ===")
print(f"total destape: {len(destape)}")
if destape:
    conf=sum(1 for r in destape if night(r.get('datetime_utc')) in v375_nights)
    vrps=sorted(pcv(r) for r in destape)
    dts=[ (r.get('t_max_k') or 0)-(r.get('t_bg_k') or 0) for r in destape if r.get('t_max_k') and r.get('t_bg_k')]
    cdist=[(r.get('primary_cluster') or {})['centroid_dist_km'] for r in destape]
    clat=[(r.get('primary_cluster') or {}).get('centroid_lat') for r in destape if (r.get('primary_cluster') or {}).get('centroid_lat')]
    clon=[(r.get('primary_cluster') or {}).get('centroid_lon') for r in destape if (r.get('primary_cluster') or {}).get('centroid_lon')]
    print(f"  VIIRS375-confirmados (NUESTRO VIIRS vio summit esa noche): {conf}/{len(destape)} = {conf/len(destape):.0%}")
    print(f"  pc.vrp_mw: mediana {st.median(vrps):.2f}  p90 {vrps[int(len(vrps)*0.9)]:.2f}  max {max(vrps):.2f}")
    print(f"  ΔT (t_max-t_bg): mediana {st.median(dts):.1f} K" if dts else "")
    print(f"  centroid_dist al cráter: mediana {st.median(cdist):.2f} km")
    print(f"  centroid lat/lon mediana: {st.median(clat):.4f} / {st.median(clon):.4f}  (cráter ~{VENT[0]}/{VENT[1]})")
    yrs=Counter(night(r.get('datetime_utc'))[:7] for r in destape)
    print(f"  por mes: {dict(sorted(yrs.items()))}")
# cuántas noches MODIS summit YA (sin ancla) + cuántas destape agregaría
modis_summit_now={night(r.get('datetime_utc')) for r in recs if is_modis(r.get('sensor')) and r.get('distance_class')=='summit' and pcv(r)>0}
destape_nights={night(r.get('datetime_utc')) for r in destape}
print(f"\n  noches MODIS-summit YA: {len(modis_summit_now)} | noches que el destape AGREGA: {len(destape_nights - modis_summit_now)}")
print(f"  de las noches destape, con VIIRS375 summit nuestro: {len(destape_nights & v375_nights)}/{len(destape_nights)}")

# refinamiento A62: en las noches de destape MODIS, ¿VIIRS375 tuvo pasada y qué vio?
print("\n=== Refinamiento: cobertura VIIRS375 en las noches de destape ===")
v375_by_night={}  # night -> list of (distance_class, vrp)
for r in recs:
    if is_v375(r.get('sensor')):
        v375_by_night.setdefault(night(r.get('datetime_utc')),[]).append((r.get('distance_class'), pcv(r)))
cat=Counter()
for r in destape:
    n=night(r.get('datetime_utc'))
    passes=v375_by_night.get(n)
    if not passes:
        cat['sin pasada VIIRS (gap, inconcluso)']+=1
    elif any(dc=='summit' and v>0 for dc,v in passes):
        cat['VIIRS summit (REAL cat-b)']+=1
    elif any(v>0 for dc,v in passes):
        cat['VIIRS detecta far (parcial)']+=1
    else:
        cat['VIIRS pasó y NO vio nada (sospechoso A69)']+=1
tot=len(destape)
for k,v in sorted(cat.items(), key=lambda x:-x[1]):
    print(f"  {k:<42} {v:>4} ({v/tot:.0%})")
