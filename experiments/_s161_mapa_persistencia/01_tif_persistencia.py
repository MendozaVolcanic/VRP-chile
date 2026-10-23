# -*- coding: utf-8 -*-
"""S161, persistencia de los focos térmicos en los GeoTIFF VIIRS 375 de MIROVA, mes a mes, noche y día por separado.

Fenómeno: un foco recurrente (cráter, campo fumarólico, lago, borde de nieve, fuego) aparece como un píxel más tibio que
su entorno en muchas escenas. De noche eso es calor; de día el MIR (3,7 um) suma reflejo solar, y una nube, una ladera
asoleada o una superficie brillante también resaltan (A76). Por eso noche y día se cuentan por separado y nunca se
suman: la «fuente» del E de Cordón Caulle de S160 resultó ser 13 de 15 TIF diurnos de mayo (VE-08).

Instrumento (mismo residuo que S139 y S160 02b, para que los números se comparen):
- residuo = TIF menos su mediana móvil de 9 x 9 píxeles (3,4 km); z = residuo / desviación estándar del residuo de
  toda la escena (prominencia).
- Un foco está PRESENTE en un TIF si el z máximo dentro de 1,0 km del foco es >= 4.
- Focos: (a) forzados, los que ya nombró S160 y su verificador (cráter, fuente E de Cordón Caulle, N de Tupungatito y de
  Isluga, la fuente de VE-01, el S del Puyehue); (b) descubiertos: máximos locales del mapa de frecuencia (cuántos TIF
  tienen z >= 4 en ese píxel o sus 8 vecinos), dentro de 20 km del cráter, con frecuencia >= 3 veces la mediana del área
  y >= 5 TIF, hasta 6 de noche y 4 de día por volcán. Un descubierto a 1,5 km o menos de otro foco se funde con él.
- Nulo (A110, medido, no razonado): en cada TIF, 300 puntos al azar (semilla fija) dentro de 20 km del cráter y a más de
  3 km de todo foco; su tasa de «presente» es lo que el instrumento marca sin foco. Un foco es persistente si su tasa
  supera claramente ese nulo en el mismo mes y franja.
- Hora de cada TIF: acquisition_utc del índice del archivo (experiments/_s147_tif/index_remoto.csv, hasta el
  2026-09-22); sin ella, la hora del nombre, salvo los «_lm» (nombrados por Last-Modified: hora no confiable, se
  excluyen y se cuentan). Franja por elevación solar en el cráter: noche <= -6 grados, día > 0, crepúsculo entre ambos.
- A106: los TIF son EPSG:4326 salvo 8 adquisiciones UTM del 14-15 de septiembre (se procesan con su propia
  transformación; no entran al mapa de frecuencia, que exige grilla idéntica). Una imagen re-servida con md5 repetido se
  cuenta una sola vez (la primera adquisición).
- Pareo con la tabla de MIROVA: fila del mismo volcán y VIIRS 375 a 120 s o menos (verificador S160, v10).

P1 (roto): el cráter de noche debe estar presente bastante más que el nulo en Tupungatito y Cordón Caulle (S160: el calor
de las alertas cae en el cráter); y en los TIF nocturnos con ALERTA de MIROVA, más que en los RUTINA.
P2 (muerto): n de TIF por volcán, mes y franja; una celda con n = 0 es SIN DATO.
Uso: python -I 01_tif_persistencia.py > 01_tif_persistencia_salida.txt
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import matplotlib
from PIL import Image
from pyproj import Transformer
from scipy.ndimage import maximum_filter, median_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun161 as C  # noqa: E402

sys.path.insert(0, str(C.WT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

C.utf8_stdout()
OUT = Path(__file__).resolve().parent
Z_UMBRAL = 4.0
R_FOCO_KM = 1.0
R_AREA_KM = 20.0
FORZADOS = {
    "Tupungatito": [("crater", "cráter", None), ("N_s160", "5,6 km N del cráter (S160, 02d)", (-33.34, -69.84)),
                    ("VE01", "fuente de VE-01, 9,4 km E del cráter", (-33.36927, -69.72791))],
    "PuyehueCordonCaulle": [("crater", "cráter", None), ("E_s160", "10,7 km E del cráter (S160, VE-08)", (-40.5297, -72.0192)),
                            ("S_puyehue", "S de la cumbre del Puyehue (S160, seguimiento)", (-40.62, -72.175))],
    "Isluga": [("crater", "cráter (coordenada del yaml)", None), ("N_s160", "5,7 km N del cráter (S160, 02d)", (-19.10, -68.84))],
}


def p(*a):
    print(" ".join(str(x) for x in a))


def listar_tifs(vol):
    pats = [str(C.TIF_ARCHIVE / "data" / "tif" / vol / "*VIIRS375*.tif"),
            str(C.REPO / "experiments" / "**" / f"*{vol}*" / "*VIIRS375*.tif"),
            str(C.REPO / "experiments" / "**" / f"*{vol}*VIIRS375*.tif")]
    fs = set()
    for pt in pats:
        fs.update(glob.glob(pt, recursive=True))
    return sorted(f for f in fs if f"{os.sep}{vol}{os.sep}" in f or f"__{vol}__" in f)


def leer(path):
    with rasterio.open(path) as ds:
        A = ds.read(1).astype(float)
        T, crs, b = ds.transform, ds.crs, ds.bounds
    A[~np.isfinite(A) | (A <= 0)] = np.nan
    rows, cols = np.indices(A.shape)
    xs, ys = rasterio.transform.xy(T, rows.ravel(), cols.ravel())
    xs, ys = np.array(xs), np.array(ys)
    if crs.to_epsg() != 4326:
        lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xs, ys)
    else:
        lon, lat = xs, ys
    return A, np.array(lat).reshape(A.shape), np.array(lon).reshape(A.shape), crs.to_epsg(), (b.left, b.bottom, b.right, b.top)


def zmapa(A):
    fill = np.where(np.isnan(A), np.nanmedian(A), A)
    res = fill - median_filter(fill, size=9, mode="nearest")
    res[np.isnan(A)] = np.nan
    sd = np.nanstd(res)
    return res / sd if sd > 0 else res * np.nan


def dist_grid(lat, lon, lat0, lon0):
    dn = (lat - lat0) * 111.195
    de = (lon - lon0) * 111.195 * np.cos(np.radians(lat0))
    return np.hypot(dn, de)


def main():
    ix = pd.read_csv(C.REPO / "experiments" / "_s147_tif" / "index_remoto.csv")
    ix = ix[ix.sensor == "VIIRS375"]
    acq = {os.path.basename(t): a for t, a in zip(ix.tif_path, ix.acquisition_utc) if isinstance(a, str)}
    ref = defaultdict(list)
    for f in cargar_referencia_unificada():
        if f["volcano"] in C.VOLS and f["sensor_bucket"] == "VIIRS375":
            ref[f["volcano"]].append((datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc), f))
    resumen = {}
    filas_tif, filas_foco = [], []
    for vol in C.VOLS:
        g = C.GEO[vol]
        vent = g["vent"]
        files = listar_tifs(vol)
        vistos, md5s = {}, {}
        n_lm_sin_hora = n_md5 = n_vacio = 0
        cand = []
        for f in files:
            base = os.path.basename(f).split("__")[-1]
            if base in vistos:
                continue
            vistos[base] = f
            if base in acq:
                t = datetime.fromisoformat(acq[base]).astimezone(timezone.utc)
                origen_t = "acquisition_utc"
            elif "_lm" in base:
                n_lm_sin_hora += 1
                continue
            else:
                t = datetime.strptime(base[:15], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
                origen_t = "nombre"
            cand.append((t, base, f, origen_t))
        cand.sort()
        tifs = []
        for t, base, f, origen_t in cand:
            md5 = hashlib.md5(open(f, "rb").read()).hexdigest()
            if md5 in md5s:
                n_md5 += 1
                continue
            md5s[md5] = base
            A, lat, lon, epsg, bnd = leer(f)
            if np.isnan(A).mean() > 0.5:
                n_vacio += 1
                continue
            el = C.elevacion_solar(*vent, t)
            tifs.append(dict(t=t, base=base, epsg=epsg, bnd=bnd, A=A, lat=lat, lon=lon, z=zmapa(A), el=el,
                             franja=C.franja(el), origen_t=origen_t, nan=float(np.isnan(A).mean())))
        p(f"\n===== {vol}: archivos {len(files)}, nombres únicos {len(vistos)}, _lm sin hora {n_lm_sin_hora}, md5 repetido "
          f"{n_md5}, >50 % sin dato {n_vacio}, analizados {len(tifs)} (UTM {sum(1 for x in tifs if x['epsg'] != 4326)}); "
          f"de {min(x['t'] for x in tifs):%Y-%m-%d} a {max(x['t'] for x in tifs):%Y-%m-%d}")
        p("  por franja:", {fr: sum(1 for x in tifs if x["franja"] == fr) for fr in ("noche", "dia", "crepusculo")},
          "; hora por nombre (sin acquisition_utc):", sum(1 for x in tifs if x["origen_t"] == "nombre"))
        # ---- mapa de frecuencia por franja (sólo grilla 4326 idéntica)
        geo = [x for x in tifs if x["epsg"] == 4326]
        bnd0 = max(set(x["bnd"] for x in geo), key=lambda b: sum(1 for x in geo if x["bnd"] == b))
        geo = [x for x in geo if x["bnd"] == bnd0]
        lat0, lon0 = geo[0]["lat"], geo[0]["lon"]
        dv = dist_grid(lat0, lon0, *vent)
        area = dv <= R_AREA_KM
        focos = [dict(id=fid, nombre=nom, lat=(ll or vent)[0], lon=(ll or vent)[1], origen="S160") for fid, nom, ll in FORZADOS[vol]]
        frec = {}
        for fr, maxn in (("noche", 6), ("dia", 4)):
            sel = [x for x in geo if x["franja"] == fr]
            if not sel:
                continue
            E = sum(maximum_filter(np.nan_to_num(x["z"], nan=-9) >= Z_UMBRAL, size=3).astype(int) for x in sel)
            frec[fr] = (E, len(sel))
            med = float(np.median(E[area]))
            pk = (E == maximum_filter(E, size=9)) & area & (E >= max(5, 3 * med))
            ys, xs = np.where(pk)
            orden = np.argsort(-E[ys, xs])
            p(f"  mapa de frecuencia {fr}: n TIF {len(sel)}, mediana del área {med:.0f} TIF ({100 * med / len(sel):.1f} %), "
              f"máximos que pasan el corte {len(ys)}")
            k_add = 0
            for k in orden:
                if k_add >= maxn:
                    break
                la, lo = float(lat0[ys[k], xs[k]]), float(lon0[ys[k], xs[k]])
                cerca = [fo for fo in focos if C.dist_km(fo["lat"], fo["lon"], la, lo) <= 1.5]
                txt = (f"    máximo {E[ys[k], xs[k]]} de {len(sel)} TIF en {la:.4f} / {lo:.4f}, {C.dist_km(*vent, la, lo):.2f} km "
                       f"{C.octante(C.rumbo(*vent, la, lo))} del cráter")
                if cerca:
                    p(txt + f" -> se funde con «{cerca[0]['id']}»")
                    cerca[0].setdefault("visto_en", []).append(fr)
                    continue
                k_add += 1
                d = C.dist_km(*vent, la, lo)
                fid = f"{fr[0]}{k_add}"
                focos.append(dict(id=fid, nombre=f"descubierto ({fr}), {d:.1f} km {C.octante(C.rumbo(*vent, la, lo))} del cráter",
                                  lat=la, lon=lo, origen=f"frecuencia_{fr}", visto_en=[fr]))
                p(txt + f" -> foco nuevo «{fid}»")
            # imagen de frecuencia para el mapa (transparente bajo el 2x de la mediana)
            fq = E / len(sel)
            vmax = max(0.25, float(np.percentile(fq[area], 99.5)))
            rgba = (matplotlib.colormaps["inferno"](np.clip(fq / vmax, 0, 1)) * 255).astype("uint8")
            rgba[..., 3] = np.where(E >= max(3, 2 * med), (180 * np.clip(fq / vmax, 0.25, 1)).astype("uint8"), 0)
            Image.fromarray(rgba).save(OUT / f"01_frecuencia_{vol}_{fr}.png")
        # ---- presencia por foco y TIF, y nulo
        rng = np.random.default_rng(161)
        for x in tifs:
            dvx = dist_grid(x["lat"], x["lon"], *vent)
            lejos = np.ones_like(dvx, bool)
            for fo in focos:
                lejos &= dist_grid(x["lat"], x["lon"], fo["lat"], fo["lon"]) > 3.0
            zz = x["z"]
            ok = (dvx <= R_AREA_KM) & lejos & np.isfinite(zz)
            idx = np.flatnonzero(ok)
            nulo = None
            if len(idx) > 50:
                pts = rng.choice(idx, size=300, replace=True)
                hits = 0
                for k in pts:
                    i, j = np.unravel_index(k, zz.shape)
                    m = dist_grid(x["lat"], x["lon"], x["lat"][i, j], x["lon"][i, j]) <= R_FOCO_KM
                    hits += np.nanmax(np.where(m, zz, -np.inf)) >= Z_UMBRAL
                nulo = hits / 300
            # pareo con MIROVA a 120 s
            mr = [f for (dt, f) in ref[vol] if abs((dt - x["t"]).total_seconds()) <= 120]
            mtipo = "ALERTA" if any(f["tipo"].startswith("ALERTA") for f in mr) else (mr[0]["tipo"] if mr else "")
            filas_tif.append(dict(vol=vol, base=x["base"], t=x["t"].strftime("%Y-%m-%d %H:%M"), mes=x["t"].strftime("%Y-%m"),
                                  franja=x["franja"], elev_sol=round(x["el"], 1), epsg=x["epsg"], nan_pct=round(100 * x["nan"], 1),
                                  origen_t=x["origen_t"], mirova=mtipo, nulo=nulo))
            for fo in focos:
                m = (dist_grid(x["lat"], x["lon"], fo["lat"], fo["lon"]) <= R_FOCO_KM)
                vals = zz[m & np.isfinite(zz)]
                if len(vals) < max(1, m.sum() // 2):
                    zmax, pres = None, None
                else:
                    zmax = float(vals.max())
                    pres = int(zmax >= Z_UMBRAL)
                filas_foco.append(dict(vol=vol, base=x["base"], t=x["t"].strftime("%Y-%m-%d %H:%M"), mes=x["t"].strftime("%Y-%m"),
                                       franja=x["franja"], foco=fo["id"], zmax=None if zmax is None else round(zmax, 2),
                                       presente=pres, mirova=mtipo))
        resumen[vol] = dict(focos=focos, bounds=bnd0, n_tif=len(tifs))
    # ---- tablas mensuales
    df = pd.DataFrame(filas_foco)
    dt_ = pd.DataFrame(filas_tif)
    df.to_csv(OUT / "01_tif_foco_por_tif.csv", index=False)
    dt_.to_csv(OUT / "01_tif_por_tif.csv", index=False)
    for vol in C.VOLS:
        p(f"\n===== {vol}: presencia mensual (presentes / TIF con dato en el disco del foco; nulo = media de la tasa al azar)")
        for fr in ("noche", "dia"):
            d = df[(df.vol == vol) & (df.franja == fr) & df.presente.notna()]
            dn = dt_[(dt_.vol == vol) & (dt_.franja == fr)]
            meses = sorted(dn.mes.unique())
            if not meses:
                p(f"  {fr}: SIN DATO")
                continue
            p(f"  --- {fr}")
            p("    " + "foco".ljust(10) + "".join(m[2:].rjust(9) for m in meses) + "    total")
            nulo_m = {m: dn[dn.mes == m].nulo.mean() for m in meses}
            p("    " + "nulo %".ljust(10) + "".join(f"{100 * nulo_m[m]:8.1f}%" for m in meses) + f"  {100 * dn.nulo.mean():6.1f}%")
            p("    " + "n TIF".ljust(10) + "".join(f"{(dn.mes == m).sum():9d}" for m in meses) + f"  {len(dn):7d}")
            tabla = {}
            for fo in resumen[vol]["focos"]:
                dd = d[d.foco == fo["id"]]
                cel = []
                for m in meses:
                    s = dd[dd.mes == m]
                    cel.append((int(s.presente.sum()), len(s)))
                tot = (int(dd.presente.sum()), len(dd))
                tabla[fo["id"]] = {"meses": dict(zip(meses, cel)), "total": tot, "nulo_mes": {m: nulo_m[m] for m in meses},
                                   "nulo_total": float(dn.nulo.mean())}
                p("    " + fo["id"].ljust(10) + "".join((f"{a}/{b}" if b else "-").rjust(9) for a, b in cel)
                  + f"  {tot[0]}/{tot[1]} ({100 * tot[0] / tot[1] if tot[1] else 0:.0f} %)")
                # control P1: ALERTA vs RUTINA (sólo noche)
                if fr == "noche":
                    a = dd[dd.mirova == "ALERTA"]
                    r = dd[dd.mirova == "RUTINA"]
                    tabla[fo["id"]]["alerta"] = (int(a.presente.sum()), len(a))
                    tabla[fo["id"]]["rutina"] = (int(r.presente.sum()), len(r))
            resumen[vol].setdefault("tabla", {})[fr] = tabla
            if fr == "noche":
                p("    control P1 (noche): presentes en TIF con ALERTA de MIROVA vs con RUTINA:")
                for fo in resumen[vol]["focos"]:
                    t = tabla[fo["id"]]
                    pa = 100 * t["alerta"][0] / t["alerta"][1] if t["alerta"][1] else float("nan")
                    pr = 100 * t["rutina"][0] / t["rutina"][1] if t["rutina"][1] else float("nan")
                    p(f"      {fo['id']:10s} ALERTA {t['alerta'][0]}/{t['alerta'][1]} ({pa:.0f} %)   RUTINA {t['rutina'][0]}/{t['rutina'][1]} ({pr:.0f} %)")
    json.dump(resumen, open(OUT / "01_tif_persistencia.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    p("\nfocos:")
    for vol in C.VOLS:
        for fo in resumen[vol]["focos"]:
            p(f"  {vol:20s} {fo['id']:10s} {fo['lat']:.5f} / {fo['lon']:.5f}  {C.dist_km(*C.GEO[vol]['vent'], fo['lat'], fo['lon']):5.2f} km "
              f"{C.octante(C.rumbo(*C.GEO[vol]['vent'], fo['lat'], fo['lon']))} del cráter  [{fo['origen']}] {fo['nombre']}")


if __name__ == "__main__":
    main()
