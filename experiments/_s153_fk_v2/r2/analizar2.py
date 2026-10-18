"""R2 F/K, segunda pasada: mide con el lector de TIF del repo (experiments/_s151_seleccion_mirova/comun_tif.py,
exceso local = campo menos mediana movil, z robusto) en vez del campo crudo, que esta dominado por el gradiente
topografico (A69, S139 §3.2). Agrega el control de atribucion (BT del TIF contra BT de nuestros pixeles de la
misma pasada): si coinciden en < 1 K el TIF es del mismo granulo (A109)."""
import json, sys, io, math, os
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
sys.path.insert(0, REPO + "experiments/_s151_seleccion_mirova")
import comun_tif as ct  # noqa: E402
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt  # noqa: E402
import analizar as A  # noqa: E402  (reusa records, filas de MIROVA y descarga; sus CASOS por defecto)

OUT = A.OUT


def zpt(R, la, lo):
    rc = ct.celda(R, la, lo)
    if rc is None:
        return None
    r0, c0 = rc
    h, w = R["z"].shape
    win = R["z"][max(0, r0-1):min(h, r0+2), max(0, c0-1):min(w, c0+2)]
    return float(R["z"][rc]), float(np.nanmax(win))


res = []
for nombre, V, vol, sen, dt in A.CASOS:
    c = A.cand[(V, vol, sen, dt)]
    b = c["b"]
    rc_, rk_ = A.record(V, A.C0, vol, sen, dt), A.record(V, A.K, vol, sen, dt)
    vlat, vlon, inner = A.VENT[vol]
    loc = A.bajar(c["tif"][0])
    R = ct.leer(loc, b)
    print(f"\n######## {nombre}: {vol} {sen} {dt}  C0={c['C0']} K={c['K']} alerta={c['alerta']} prot={c['protA']} neg={c['neg']} vrpA={c['vrpA']}")
    print(f"  TIF {c['tif'][0]} {R['crs']}  centro raster a {ct.dist_km(R['clat'], R['clon'], vlat, vlon):.2f} km del vent")
    d = ct.dist_desde(R, vlat, vlon)
    fc = ct.foco_en(R, d <= ct.R_CRATER_KM[b])
    fi = ct.foco_en(R, d <= inner)
    fl = ct.foco_en(R, d > inner)
    for etq, f in (("crater", fc), ("inner", fi), ("lejos", fl)):
        if f:
            z, r, cc = f
            print(f"  foco MIROVA {etq:6}: z {z:5.1f} en ({R['lat'][r, cc]:.4f},{R['lon'][r, cc]:.4f}) a {d[r, cc]:.2f} km rumbo {A.rumbo(vlat, vlon, R['lat'][r, cc], R['lon'][r, cc]):.0f}, BT TIF {ct.bt_k(float(R['a'][r, cc]), b):.1f} K, energia ~{ct.energia_mw(R, r, cc):.2f} MW")
    for br, r in (("C0", rc_), ("K", rk_)):
        if r is None:
            continue
        pc = r.get("primary_cluster") or {}
        ap = r.get("anomaly_pixels") or []
        dbt = ct.dbt_mediana(R, ap)
        print(f"  {br}: pc n={pc.get('n_pixels')} vrp={pc.get('vrp_mw')} f5={r.get('f5_core_vrp_mw')} clase={r.get('distance_class')}  atribucion |dBT| mediana {dbt[0] if dbt[0] is None else round(dbt[0], 2)} K (n={dbt[1]})")
        if pc.get("centroid_lat") is not None:
            zz = zpt(R, pc["centroid_lat"], pc["centroid_lon"])
            dd = ct.dist_km(pc["centroid_lat"], pc["centroid_lon"], vlat, vlon)
            dfi = ct.dist_km(pc["centroid_lat"], pc["centroid_lon"], R["lat"][fi[1], fi[2]], R["lon"][fi[1], fi[2]]) if fi else None
            print(f"     centroide ({pc['centroid_lat']:.4f},{pc['centroid_lon']:.4f}) {dd:.2f} km rumbo {A.rumbo(vlat, vlon, pc['centroid_lat'], pc['centroid_lon']):.0f}: z TIF {zz[0]:.1f} (max 3x3 {zz[1]:.1f}); a {dfi:.2f} km del foco MIROVA del inner")
        for p in sorted(ap, key=lambda p: ct.dist_km(p["lat"], p["lon"], vlat, vlon))[:4]:
            zz = zpt(R, p["lat"], p["lon"])
            rc = ct.celda(R, p["lat"], p["lon"])
            btt = ct.bt_k(float(R["a"][rc]), b) if rc else float("nan")
            print(f"     pixel bt {p.get('bt_k')} vrp {p.get('vrp_mw')} a {ct.dist_km(p['lat'], p['lon'], vlat, vlon):.2f} km: z TIF {None if zz is None else round(zz[0], 1)} (3x3 {None if zz is None else round(zz[1], 1)}), BT TIF {btt:.1f}")
    # figura del exceso local, +-10 km
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.pcolormesh(R["lon"], R["lat"], R["z"], cmap="inferno", vmin=-2, vmax=10, shading="auto")
    k = 1 / math.cos(math.radians(vlat))
    ax.add_patch(plt.matplotlib.patches.Ellipse((vlon, vlat), 2 * inner / 111.32 * k, 2 * inner / 111.32, fill=False, color="cyan"))
    ax.plot(vlon, vlat, "c+", ms=14, mew=2)
    for br, r, col, mk in (("C0", rc_, "lime", "o"), ("K", rk_, "deepskyblue", "s")):
        pc = (r or {}).get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            ax.plot(pc["centroid_lon"], pc["centroid_lat"], mk, mfc="none", mec=col, ms=16, mew=2, label=f"{br} cumulo")
        for p in (r or {}).get("anomaly_pixels") or []:
            ax.plot(p["lon"], p["lat"], "x", color=col, ms=7)
    h = 10 / 111.32
    ax.set_xlim(vlon - h * k, vlon + h * k); ax.set_ylim(vlat - h, vlat + h); ax.set_aspect(k)
    ax.set_title(f"{vol} {sen} {dt}\nexceso local MIROVA (z); circulo = inner {inner} km", fontsize=9)
    ax.legend(loc="lower left", fontsize=8)
    png = OUT + f"exceso_{nombre.split()[0]}_{vol}.png"
    fig.savefig(png, dpi=80, bbox_inches="tight"); plt.close(fig)
    print(f"  figura {png}")
