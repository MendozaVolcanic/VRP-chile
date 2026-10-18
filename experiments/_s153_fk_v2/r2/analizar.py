"""R2 F/K: por pasada, baja el GeoTIFF de MIROVA (uno por uno, API), lee la fila de MIROVA y mide
los pixeles de C0 y K contra el calor de la imagen. Escribe recortes PNG para mirarlos."""
import json, csv, math, sys, io, os, subprocess
import numpy as np, rasterio
from rasterio.transform import rowcol, xy
from datetime import datetime
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = "C:/Users/nmend/AppData/Local/Temp/claude/"
OUT = T + "r2_fk/"
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
CONG = {"V1": REPO + "experiments/_s151_prereg_fk_11/_congelado_v1/", "V2": REPO + "experiments/_s151_prereg_fk_11/_congelado_v2/"}
UNI = {"V1": [T + "v1_38639658446/union_2766/"], "V2": [T + "v2a_38648773684/union_2766/", T + "v2b_39033530622/union/"]}
C0, K = "_s146_ab_control", "_s149_ab_sin_test1_b22_max"

VENT = {}
for v in yaml.safe_load(open(REPO + "volcanoes.yaml", encoding="utf-8"))["volcanoes"]:
    VENT[v["name"]] = (v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]), v.get("inner_radius_km", 5))

CASOS = [tuple(x.split("|")) for x in sys.argv[1:]] or [
    ("1 neg borde frio", "V1", "Chaiten", "VIIRS_NOAA20", "2026-09-10 04:36"),
    ("2a neg nadir", "V1", "Lascar", "VIIRS_NOAA20", "2026-09-06 05:42"),
    ("2b neg nadir", "V1", "Copahue", "VIIRS_NOAA21", "2026-09-15 05:24"),
    ("3 protegida V375 Lascar", "V2", "Lascar", "VIIRS_NOAA20", "2026-06-02 05:42"),
    ("4 MODIS K recupera", "V2", "Lascar", "MODIS_TERRA", "2026-05-10 01:25"),
    ("5 cumulo movido", "V2", "Tupungatito", "VIIRS_NOAA20", "2026-06-03 05:24"),
]


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c); dp, dl = p2 - p1, math.radians(d - b)
    return 2 * 6371 * math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))


def rumbo(a, b, c, d):
    y = math.sin(math.radians(d-b))*math.cos(math.radians(c))
    x = math.cos(math.radians(a))*math.sin(math.radians(c)) - math.sin(math.radians(a))*math.cos(math.radians(c))*math.cos(math.radians(d-b))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def record(V, br, vol, sen, dt):
    for d in UNI[V]:
        f = d + br + f"/{vol}.json"
        if os.path.exists(f):
            for r in json.load(open(f, encoding="utf-8"))["records"]:
                if r["sensor"] == sen and r["datetime_utc"] == dt:
                    return r


cand = {(c["V"], c["vol"], c["sen"], c["dt"]): c for c in json.load(open(OUT + "candidatos.json"))}
idx = list(csv.DictReader(open(OUT + "index.csv")))


def filas_mirova(V, vol, b, dt):
    t = datetime.strptime(dt, "%Y-%m-%d %H:%M")
    res = []
    for fn in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        for r in csv.DictReader(open(CONG[V] + fn, encoding="utf-8")):
            if r["Volcan"].replace(" ", "").replace("-", "") != vol or r["Sensor"] != b:
                continue
            try:
                ts = datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            if abs((ts - t).total_seconds()) <= 180:
                res.append((fn[13:17], r["Fecha_Satelite_UTC"], r["VRP_MW"], r["Distancia_km"], r["Tipo_Registro"], r["Clasificacion Mirova"], r.get("Nota_Validacion", "")[:90]))
    return res


def bajar(path):
    loc = OUT + "tif/" + path.replace("/", "_")
    if not os.path.exists(loc):
        raw = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                              f"repos/MendozaVolcanic/mirova-tif-archive/contents/{path}"], capture_output=True, check=True).stdout
        open(loc, "wb").write(raw)
    return loc


for nombre, V, vol, sen, dt in ([] if __name__ != "__main__" else CASOS):
    c = cand[(V, vol, sen, dt)]
    b = c["b"]
    rc, rk = record(V, C0, vol, sen, dt), record(V, K, vol, sen, dt)
    vlat, vlon, inner = VENT[vol]
    print(f"\n######## {nombre}: {vol} {sen} {dt} ({V})")
    print(f"  etiqueta: alerta={c['alerta']} protA={c['protA']} neg_limpio={c['neg']} vrpA={c['vrpA']} | publica C0={c['C0']} K={c['K']}")
    print(f"  zenit {c['zen']}  t_bg {c['tbg']}  vent ({vlat},{vlon}) inner {inner} km")
    for f in filas_mirova(V, vol, b, dt):
        print("  MIROVA fila:", f)
    tp, dts, md5, nmd5, acq = c["tif"]
    filas_md5 = [r for r in idx if r["md5"] == md5]
    print(f"  TIF {tp} acq={acq} dt={dts}s; filas con ese md5: " + "; ".join(f"{r['tif_path'].split('/')[-1]} acq={r['acquisition_utc']} lm={r['last_modified_utc']} cap={r['captured_at_utc'][:16]}" for r in filas_md5))
    loc = bajar(tp)
    with open(loc, "rb") as fh:
        import hashlib
        print(f"  md5 local {hashlib.md5(fh.read()).hexdigest()} (indice {md5})")
    with rasterio.open(loc) as s:
        a = s.read(1).astype(float); tr = s.transform; crs = s.crs
    med = np.nanmedian(a); mad = 1.4826 * np.nanmedian(np.abs(a - med))
    z = (a - med) / mad
    H, W = a.shape
    lat = np.empty_like(a); lon = np.empty_like(a)
    for i in range(H):
        xs, ys = xy(tr, [i]*W, list(range(W)))
        lon[i] = xs; lat[i] = ys
    if crs and crs.to_epsg() != 4326:
        from pyproj import Transformer
        tf = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        lon, lat = tf.transform(lon, lat)
    print(f"  CRS {crs} forma {a.shape} paso ({tr.a:.6f},{tr.e:.6f}) | mediana {med:.4f} sigma_rob {mad:.4f} max {np.nanmax(a):.4f} (z {np.nanmax(z):.1f})")
    dist = np.vectorize(hav)(vlat, vlon, lat, lon)
    m_in = dist <= inner
    i_in = np.unravel_index(np.nanargmax(np.where(m_in, a, -np.inf)), a.shape)
    i_gl = np.unravel_index(np.nanargmax(a), a.shape)

    def desc(i):
        return f"({lat[i]:.4f},{lon[i]:.4f}) a {dist[i]:.2f} km rumbo {rumbo(vlat, vlon, lat[i], lon[i]):.0f} del vent, z {z[i]:.1f}"
    print(f"  pico MIROVA dentro de {inner} km: {desc(i_in)}")
    print(f"  pico MIROVA global: {desc(i_gl)}")
    print(f"  pixeles z>=4: {int((z >= 4).sum())} en la imagen, {int(((z >= 4) & m_in).sum())} dentro del inner; z>=8: {int((z >= 8).sum())} / {int(((z >= 8) & m_in).sum())}")
    marcas = {}
    for br, r in (("C0", rc), ("K", rk)):
        if r is None:
            print(f"  {br}: sin record"); continue
        pc = r.get("primary_cluster") or {}
        print(f"  {br}: distance_class={r.get('distance_class')} pc n={pc.get('n_pixels')} vrp={pc.get('vrp_mw')} geo={pc.get('geo_class')} f5={r.get('f5_core_vrp_mw')} t1={r.get('triggered_test1')} n_t1={r.get('n_test1_pixels')} src={r.get('final_hotspot_source')} n_anom={r.get('n_anomalous_pixels')}")
        pts = []
        if pc.get("centroid_lat") is not None:
            pts.append(("centroide", pc["centroid_lat"], pc["centroid_lon"]))
        if r.get("final_hotspot_lat") is not None:
            pts.append(("final_hotspot", r["final_hotspot_lat"], r["final_hotspot_lon"]))
        ap = sorted(r.get("anomaly_pixels") or [], key=lambda p: hav(vlat, vlon, p["lat"], p["lon"]))
        for p in ap[:5]:
            pts.append((f"anom bt={p.get('bt_k')} vrp={p.get('vrp_mw')}", p["lat"], p["lon"]))
        marcas[br] = pts
        for etq, la, lo in pts:
            rr, cc = rowcol(tr, lo, la) if (crs is None or crs.to_epsg() == 4326) else (None, None)
            if rr is None:
                dd = np.vectorize(hav)(la, lo, lat, lon); rr, cc = np.unravel_index(np.argmin(dd), dd.shape)
            if 0 <= rr < H and 0 <= cc < W:
                zn = np.nanmax(z[max(0, rr-1):rr+2, max(0, cc-1):cc+2])
                dpk = hav(la, lo, lat[i_in], lon[i_in])
                print(f"     {etq}: ({la:.4f},{lo:.4f}) {hav(vlat, vlon, la, lo):.2f} km rumbo {rumbo(vlat, vlon, la, lo):.0f} | MIROVA z={z[rr, cc]:.1f} (max 3x3 {zn:.1f}) | a {dpk:.2f} km del pico interior")
            else:
                print(f"     {etq}: ({la:.4f},{lo:.4f}) {hav(vlat, vlon, la, lo):.2f} km, FUERA de la imagen")
    # figura: imagen entera (z) y ampliacion +-8 km
    fig, ax = plt.subplots(1, 2, figsize=(13, 6))
    for k, axx in enumerate(ax):
        axx.pcolormesh(lon, lat, z, cmap="inferno", vmin=-2, vmax=8, shading="auto")
        rkm = inner / (111.32 * math.cos(math.radians(vlat)))
        axx.add_patch(plt.matplotlib.patches.Ellipse((vlon, vlat), 2 * rkm, 2 * inner / 111.32, fill=False, color="cyan", lw=1))
        axx.plot(vlon, vlat, "c+", ms=14, mew=2)
        for br, col, mk in (("C0", "lime", "o"), ("K", "deepskyblue", "s")):
            for etq, la, lo in marcas.get(br, []):
                if etq == "centroide":
                    axx.plot(lo, la, mk, mfc="none", mec=col, ms=14, mew=2, label=f"{br} centroide")
                elif etq.startswith("anom"):
                    axx.plot(lo, la, "x", color=col, ms=6)
        if k == 1:
            d8 = 8 / 111.32
            axx.set_xlim(vlon - d8 / math.cos(math.radians(vlat)), vlon + d8 / math.cos(math.radians(vlat)))
            axx.set_ylim(vlat - d8, vlat + d8)
        axx.set_aspect(1 / math.cos(math.radians(vlat)))
        axx.set_title(f"{vol} {sen} {dt} z robusto" + (" (+-8 km)" if k else ""), fontsize=9)
    ax[0].legend(loc="lower left", fontsize=8)
    png = OUT + f"caso_{nombre.split()[0]}_{vol}.png"
    fig.savefig(png, dpi=80, bbox_inches="tight"); plt.close(fig)
    print(f"  figura {png}")
