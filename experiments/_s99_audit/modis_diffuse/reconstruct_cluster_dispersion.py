"""S101 — Refinacion: reconstruir el cluster (single-linkage sobre anomaly_pixels) y
medir su DISPERSION real, para validar el discriminante foco-vs-difuso sin reproc.

El schema solo persiste agregados del primary_cluster (centroid, n_pixels, vrp). Aca
re-agrupamos los anomaly_pixels por conectividad (~1.5 km = vecino MODIS 1km) y tomamos
el grupo cuyo centroide ~ primary_cluster.centroid. Medimos:
  - radio_p90: percentil 90 de la distancia de los px del cluster a su centroide.
  - frac_e_core: fraccion de energia del cluster dentro de R_CORE del centroide.
  - n_cluster: px del grupo reconstruido (deberia ~ pc.n_pixels).
Cruce vs MIROVA-MODIS (matched). Hipotesis: foco real -> radio chico / frac alta;
difuso -> radio grande / frac baja.

Fuente S91: este script. Output stdout + JSON.
"""
import json, csv, math, statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LINK_KM = 1.6     # conectividad single-linkage (MODIS 1km, diagonal ~1.4)
R_CORE = 2.0      # radio nucleo para frac_e_core

def hav(a, b, c, d):
    R = 6371; r = math.pi / 180
    p1, p2 = a * r, c * r; dp = (c - a) * r; dl = (d - b) * r
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def single_linkage(pts):
    """pts: list de (lat,lon,vrp). Devuelve lista de grupos (indices)."""
    n = len(pts)
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if hav(pts[i][0], pts[i][1], pts[j][0], pts[j][1]) <= LINK_KM:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return list(groups.values())

# MIROVA MODIS matched
mir = defaultdict(list)
for r in csv.DictReader(open(REPO / 'latest_consolidado.csv', encoding='utf-8')):
    if r['Sensor'] == 'MODIS' and r['Tipo_Registro'] == 'ALERTA_TERMICA':
        try:
            mir[(r['Volcan'], r['Fecha_Satelite_UTC'][:10])].append(float(r['VRP_MW']))
        except ValueError:
            pass
namemap = {'PuyehueCordonCaulle': 'Puyehue-Cordon Caulle', 'NevadosDeChillan': 'Nevados de Chillan'}
VOLS = ['Lascar', 'PuyehueCordonCaulle', 'Tupungatito', 'Chaiten', 'Villarrica', 'Llaima',
        'PlanchonPeteroa', 'Copahue', 'Isluga', 'Lastarria', 'NevadosDeChillan']

def cluster_metrics(r):
    """Reconstruye el cluster del primary y devuelve (radio_p90, frac_e_core, n_cluster, vrp_cluster)."""
    pc = r.get('primary_cluster') or {}
    clat, clon = pc.get('centroid_lat'), pc.get('centroid_lon')
    aps = [(p['lat'], p['lon'], p.get('vrp_mw', 0) or 0) for p in (r.get('anomaly_pixels') or [])
           if p.get('lat') is not None]
    if not aps or clat is None:
        return None
    groups = single_linkage(aps)
    # grupo cuyo centroide (ponderado) esta mas cerca del centroid del primary
    best, bestd = None, 1e9
    for g in groups:
        W = sum(aps[i][2] for i in g) or 1
        glat = sum(aps[i][0] * aps[i][2] for i in g) / W
        glon = sum(aps[i][1] * aps[i][2] for i in g) / W
        d = hav(glat, glon, clat, clon)
        if d < bestd:
            bestd, best = d, g
    if not best:
        return None
    W = sum(aps[i][2] for i in best) or 1
    glat = sum(aps[i][0] * aps[i][2] for i in best) / W
    glon = sum(aps[i][1] * aps[i][2] for i in best) / W
    dists = sorted(hav(aps[i][0], aps[i][1], glat, glon) for i in best)
    radio_p90 = dists[min(len(dists) - 1, int(len(dists) * 0.9))]
    e_core = sum(aps[i][2] for i in best if hav(aps[i][0], aps[i][1], glat, glon) <= R_CORE)
    return round(radio_p90, 2), round(e_core / W, 2), len(best), round(W, 1)

rows_conf, rows_big = [], []
detail = {}
for vol in VOLS:
    p = REPO / 'data/mirova_equivalent' / f'{vol}.json'
    if not p.exists():
        continue
    o = json.load(open(p, encoding='utf-8'))
    recs = o['records'] if isinstance(o, dict) else o
    mname = namemap.get(vol, vol)
    vconf, vbig = [], []
    for r in recs:
        if not r.get('sensor', '').startswith('MODIS'):
            continue
        v = (r.get('primary_cluster') or {}).get('vrp_mw', 0) or 0
        if v <= 0:
            continue
        m = cluster_metrics(r)
        if not m:
            continue
        radio, frac, nc, wc = m
        day = str(r.get('datetime_utc', ''))[:10]
        if (mname, day) in mir:
            rows_conf.append((radio, frac)); vconf.append((radio, frac))
        elif v > 20:
            rows_big.append((radio, frac)); vbig.append((radio, frac, round(v)))
    detail[vol] = {'conf': vconf[:6], 'big': vbig[:6]}

def summ(rows, lbl):
    if not rows:
        print(f"  {lbl}: (vacío)"); return
    radios = [x[0] for x in rows]; fracs = [x[1] for x in rows]
    print(f"  {lbl} (n={len(rows)}): radio_p90 med={statistics.median(radios):.1f}km  "
          f"frac_e_core(R{R_CORE}) med={statistics.median(fracs):.2f}")

print(f"=== Dispersión del cluster reconstruido (link={LINK_KM}km) ===")
summ(rows_conf, "CON MIROVA-MODIS (foco real)")
summ(rows_big, "INFLADOS >20MW sin MIROVA (difuso?)")
print("\nPor volcán [conf: (radio,frac)] [big>20: (radio,frac,vrp)]:")
for vol in VOLS:
    d = detail.get(vol, {})
    if d.get('conf') or d.get('big'):
        print(f"  {vol:<20} conf={str(d.get('conf',[]))[:38]:<40} big={str(d.get('big',[]))[:50]}")

json.dump({'conf': rows_conf, 'big': rows_big, 'detail': detail, 'link_km': LINK_KM, 'r_core': R_CORE},
          open(Path(__file__).parent / 'reconstruct_cluster_result.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print("\n-> reconstruct_cluster_result.json")
