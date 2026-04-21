"""
S14 Paso 1c — Auditoría geométrica: vent coords y radius_km vs MIROVA v2.5.

Para cada volcán chileno Tier A compara:
  - Vent nuestro (volcanoes.yaml: lat/lon + radius_km y vent_lat/vent_lon)
  - Centro MIROVA (Volc_LAT/Volc_LON promedio en OSF)
  - Distribución de Max_Dist MIROVA (p50, p90, p99, max) sobre 2024-12 a 2025-12

Genera:
  - JSON con números por volcán
  - HTML Leaflet standalone con círculos visibles para decidir a ojo
  - Stdout: tabla resumen con flags rojos

Autor: S14 2026-04-21. Read-only.
"""

import sys, io, json, math
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OSF_CSV = ROOT / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
VOLCANOES_YAML = ROOT / "volcanoes.yaml"
OUT_JSON = ROOT / "experiments" / "24_vent_radius_audit.json"
OUT_HTML = ROOT / "experiments" / "24_vent_radius_audit.html"

NAME_MAP = {
    "Lascar": "Láscar",
    "Chaiten": "Chaitén",
    "PuyehueCordonCaulle": "Puyehue-Cordón Caulle",
    "Lastarria": "Lastarria",
    "Villarrica": "Villarrica",
    "NevadosDeChillan": "Chillán, Nevados de",
    "Isluga": "Isluga",
    "Copahue": "Copahue",
    "PlanchonPeteroa": "Planchón-Peteroa",
    "Llaima": "Llaima",
}
MIROVA_CUTOFF = datetime(2024, 12, 1)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# --- Load ---
print(f"[1/3] Cargando OSF + volcanoes.yaml...")
cfg = yaml.safe_load(open(VOLCANOES_YAML, encoding="utf-8"))
vol_cfg = {v["name"]: v for v in cfg.get("volcanoes", [])}
print(f"      volcanoes.yaml entries: {len(vol_cfg)}")

osf = pd.read_csv(OSF_CSV)
osf["dt"] = pd.to_datetime(osf["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
osf = osf.dropna(subset=["dt"])
osf = osf[(osf["Volc_Name"].isin(NAME_MAP.values())) & (osf["dt"] >= MIROVA_CUTOFF)].copy()
osf["max_dist_km"] = osf["Max_Dist"] / 1000.0

# --- Audit ---
print(f"[2/3] Auditando geometría por volcán...")
rows = []
for fname, osf_name in NAME_MAP.items():
    if fname not in vol_cfg:
        continue
    v = vol_cfg[fname]
    our_center_lat = v.get("lat")
    our_center_lon = v.get("lon")
    our_radius = v.get("radius_km", 5.0)
    our_vent_lat = v.get("vent_lat", our_center_lat)
    our_vent_lon = v.get("vent_lon", our_center_lon)
    our_vent_radius = v.get("vent_radius_km", 3.0)

    grp = osf[osf["Volc_Name"] == osf_name]
    if len(grp) < 10:
        continue

    mir_lat = float(grp["Volc_LAT"].median())
    mir_lon = float(grp["Volc_LON"].median())

    offset_center = haversine_km(our_center_lat, our_center_lon, mir_lat, mir_lon)
    offset_vent = haversine_km(our_vent_lat, our_vent_lon, mir_lat, mir_lon)

    max_dist = grp["max_dist_km"]
    p50 = float(max_dist.quantile(0.50))
    p90 = float(max_dist.quantile(0.90))
    p99 = float(max_dist.quantile(0.99))
    mx  = float(max_dist.max())

    proposed_radius = min(25.0, math.ceil(p90) + 2)

    flags = []
    if offset_vent > 1.0:
        flags.append("vent offset >1 km")
    if our_radius < p90:
        flags.append("radius<p90 MIROVA")
    elif our_radius < p99:
        flags.append("radius<p99")

    rows.append({
        "volcano": fname,
        "osf_name": osf_name,
        "our_center_lat": our_center_lat, "our_center_lon": our_center_lon,
        "our_center_radius_km": our_radius,
        "our_vent_lat": our_vent_lat, "our_vent_lon": our_vent_lon,
        "our_vent_radius_km": our_vent_radius,
        "mirova_lat": mir_lat, "mirova_lon": mir_lon,
        "offset_center_km": offset_center,
        "offset_vent_km": offset_vent,
        "mirova_max_dist_p50": p50,
        "mirova_max_dist_p90": p90,
        "mirova_max_dist_p99": p99,
        "mirova_max_dist_max": mx,
        "n_osf": int(len(grp)),
        "proposed_radius_km": proposed_radius,
        "flags": flags,
    })

df = pd.DataFrame(rows)

# --- JSON ---
OUT_JSON.parent.mkdir(exist_ok=True, parents=True)
json.dump({
    "experiment": "24_vent_radius_audit",
    "session": "S14",
    "generated_utc": datetime.now().isoformat() + "Z",
    "results": df.to_dict(orient="records"),
}, open(OUT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)

# --- HTML Leaflet (sin innerHTML; todo vía JSON → createElement en JS) ---
print(f"[3/3] Generando HTML Leaflet...")
map_center = [-40.0, -71.5]
volcanoes_data = df.to_dict(orient="records")

html_parts = []
html_parts.append('<!doctype html>')
html_parts.append('<html lang="es">')
html_parts.append('<head>')
html_parts.append('<meta charset="utf-8">')
html_parts.append('<title>VRP Chile — Auditoría vents y radios vs MIROVA v2.5</title>')
html_parts.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">')
html_parts.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
html_parts.append('<style>')
html_parts.append('body { margin: 0; font-family: system-ui, sans-serif; }')
html_parts.append('#map { height: 92vh; }')
html_parts.append('#top { padding: 8px; background: #222; color: #eee; font-size: 13px; line-height: 1.5; }')
html_parts.append('.swatch { display: inline-block; width: 12px; height: 12px; vertical-align: middle; margin: 0 4px; border: 1px solid #888; }')
html_parts.append('</style>')
html_parts.append('</head>')
html_parts.append('<body>')
html_parts.append('<div id="top">')
html_parts.append('<b>Auditoría geométrica vent + radius vs MIROVA v2.5.</b> ')
html_parts.append('<span class="swatch" style="background:red"></span>radius actual nuestro · ')
html_parts.append('<span class="swatch" style="background:orange"></span>p90 MIROVA (propuesto) · ')
html_parts.append('<span class="swatch" style="background:darkorange"></span>max MIROVA observado · ')
html_parts.append('<span class="swatch" style="background:#d33"></span>📍 vent nuestro · ')
html_parts.append('<span class="swatch" style="background:#36c"></span>📍 vent MIROVA. ')
html_parts.append('Click en marcadores o círculos para números.')
html_parts.append('</div>')
html_parts.append('<div id="map"></div>')
html_parts.append('<script>')
html_parts.append(f'const VOLCANOES = {json.dumps(volcanoes_data, default=str)};')
html_parts.append(f'const MAP_CENTER = {map_center};')
html_parts.append('const map = L.map("map").setView(MAP_CENTER, 5);')
html_parts.append('L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 17, attribution: "© Esri" }).addTo(map);')
html_parts.append('L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OSM", opacity: 0.35 }).addTo(map);')
html_parts.append('const redIcon = L.icon({ iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png", iconSize: [22,36], iconAnchor: [11,36] });')
html_parts.append('const blueIcon = L.icon({ iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png", iconSize: [22,36], iconAnchor: [11,36] });')
html_parts.append('VOLCANOES.forEach(v => {')
html_parts.append('  const ourPop = document.createElement("div");')
html_parts.append('  ourPop.appendChild(Object.assign(document.createElement("b"), {textContent: v.volcano}));')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  ourPop.appendChild(document.createTextNode("Ours center: (" + v.our_center_lat.toFixed(4) + ", " + v.our_center_lon.toFixed(4) + ")"));')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  ourPop.appendChild(document.createTextNode("Ours vent: (" + v.our_vent_lat.toFixed(4) + ", " + v.our_vent_lon.toFixed(4) + ") r=" + v.our_vent_radius_km + " km"));')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  ourPop.appendChild(document.createTextNode("MIROVA: (" + v.mirova_lat.toFixed(4) + ", " + v.mirova_lon.toFixed(4) + ")"));')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  const offB = document.createElement("b"); offB.textContent = "Offset vent vs MIROVA: " + v.offset_vent_km.toFixed(2) + " km"; ourPop.appendChild(offB);')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  ourPop.appendChild(document.createTextNode("Max_Dist MIROVA: p50=" + v.mirova_max_dist_p50.toFixed(1) + " p90=" + v.mirova_max_dist_p90.toFixed(1) + " p99=" + v.mirova_max_dist_p99.toFixed(1) + " max=" + v.mirova_max_dist_max.toFixed(1)));')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  const propB = document.createElement("b"); propB.textContent = "Radius propuesto: " + v.proposed_radius_km + " km"; ourPop.appendChild(propB);')
html_parts.append('  ourPop.appendChild(document.createElement("br"));')
html_parts.append('  ourPop.appendChild(document.createTextNode("Flags: " + (v.flags.length ? v.flags.join(", ") : "ok")));')
html_parts.append('  L.marker([v.our_vent_lat, v.our_vent_lon], {icon: redIcon}).addTo(map).bindPopup(ourPop);')
html_parts.append('  L.marker([v.mirova_lat, v.mirova_lon], {icon: blueIcon}).addTo(map).bindPopup("MIROVA vent: " + v.osf_name);')
html_parts.append('  L.circle([v.our_vent_lat, v.our_vent_lon], {radius: v.our_center_radius_km * 1000, color: "red", weight: 2, fillOpacity: 0.05}).addTo(map);')
html_parts.append('  L.circle([v.our_vent_lat, v.our_vent_lon], {radius: v.mirova_max_dist_p90 * 1000, color: "orange", weight: 1, dashArray: "4,4", fillOpacity: 0.03}).addTo(map);')
html_parts.append('  L.circle([v.our_vent_lat, v.our_vent_lon], {radius: v.mirova_max_dist_max * 1000, color: "darkorange", weight: 1, dashArray: "2,6", fillOpacity: 0.02}).addTo(map);')
html_parts.append('});')
html_parts.append('</script>')
html_parts.append('</body></html>')

OUT_HTML.write_text("\n".join(html_parts), encoding="utf-8")

# --- Stdout ---
print()
print("=" * 108)
print("AUDITORÍA GEOMÉTRICA vent + radius vs MIROVA  (ordenado por offset vent)")
print("=" * 108)
header = f"{'volcán':<22s} {'off_c':>6s} {'off_v':>6s} {'r_cen':>6s} {'r_vent':>7s} {'p50':>5s} {'p90':>5s} {'p99':>5s} {'max':>5s} {'prop':>5s}  flags"
print(header)
print("-" * 108)
for _, r in df.sort_values("offset_vent_km", ascending=False).iterrows():
    flags_s = ",".join(r["flags"]) if r["flags"] else "ok"
    print(f"{r['volcano']:<22s} {r['offset_center_km']:>6.2f} {r['offset_vent_km']:>6.2f} "
          f"{r['our_center_radius_km']:>6.1f} {r['our_vent_radius_km']:>7.1f} "
          f"{r['mirova_max_dist_p50']:>5.1f} {r['mirova_max_dist_p90']:>5.1f} "
          f"{r['mirova_max_dist_p99']:>5.1f} {r['mirova_max_dist_max']:>5.1f} "
          f"{r['proposed_radius_km']:>5.0f}  {flags_s}")

print()
print(f"HTML:  {OUT_HTML}")
print(f"JSON:  {OUT_JSON}")
print()
print("Abrir el HTML en navegador (doble click) para ver los círculos sobre imagen satelital.")
