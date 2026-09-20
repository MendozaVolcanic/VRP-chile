# Verificador v3 S144: funciones comunes segun las reglas de la v3 (solo lectura)
import pandas as pd, numpy as np, rasterio, os, math, yaml, json, warnings, functools
from rasterio.warp import transform as wtransform
warnings.filterwarnings("ignore")
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TD = ROOT + "/experiments/_s144_conteo_tif/_dl_tif/"
cfg = {v["name"]: v for v in yaml.safe_load(open(ROOT + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
CSVN = {"NevadosDeChillan": "Nevados de Chillan", "PuyehueCordonCaulle": "Puyehue-Cordon Caulle"}
TIFN = {"NevadosDeChillan": "ChillanNevadosde"}
TIFN_INV = {v: k for k, v in TIFN.items()}
CUT = pd.Timestamp("2026-08-28 23:00", tz="UTC")
T_KM = 0.75


def hav(a, b, c, d):
    p = np.radians
    x = np.sin(p(c - a) / 2) ** 2 + np.cos(p(a)) * np.cos(p(c)) * np.sin(p(d - b) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(x))


def vent(v):
    y = cfg[v]
    return (y["vent_lat"], y["vent_lon"])


def mc(v):
    y = cfg[v]
    return (y["mirova_center_lat"], y["mirova_center_lon"])


def desplazar(lat, lon, dn_km, de_km):
    """Punto a dn km al norte y de km al este."""
    la = lat + dn_km / 110.574
    lo = lon + de_km / (111.320 * math.cos(math.radians(lat)))
    return la, lo


def reflejo(pt, centro):
    """Reflejo de pt a traves de centro: misma distancia, direccion opuesta (plano local)."""
    dn = (pt[0] - centro[0]) * 110.574
    de = (pt[1] - centro[1]) * 111.320 * math.cos(math.radians(centro[0]))
    return desplazar(centro[0], centro[1], -dn, -de)


def load_idx(sensor="VIIRS375"):
    idx = pd.read_csv(TD + "da4fe36e8920_index.csv")
    for c in ["captured_at_utc", "acquisition_utc", "last_modified_utc"]:
        idx[c] = pd.to_datetime(idx[c], utc=True, format="mixed", errors="coerce")
    if sensor:
        idx = idx[idx.sensor == sensor]
    idx = idx[idx.acquisition_utc.notna() & (idx.size_bytes > 0)].copy()
    idx["firstcap"] = idx.md5.map(idx.groupby("md5").captured_at_utc.min())
    fa = idx.groupby(["volcano", "md5"]).acquisition_utc.min().rename("firstacq_v").reset_index()
    idx = idx.merge(fa, on=["volcano", "md5"], how="left")
    idx["own"] = idx.acquisition_utc == idx.firstacq_v
    idx["lat_h"] = (idx.firstcap - idx.acquisition_utc).dt.total_seconds() / 3600
    idx["path"] = TD + "da4fe36e8920/" + idx.tif_path
    idx["vol"] = idx.volcano.map(lambda v: TIFN_INV.get(v, v))
    idx = idx.sort_values("captured_at_utc").drop_duplicates(["volcano", "acquisition_utc"])
    idx = idx[idx.path.map(os.path.exists)]
    return idx


def ref():
    cons = pd.read_csv(TD + "referencia/3b18c772f65a_registro_vrp_consolidado.csv")
    cons["src"] = "CONS"
    ocr = pd.read_csv(TD + "referencia/7e3438046ca1_registro_vrp_ocr.csv")
    ocr["src"] = "OCR"
    d = pd.concat([cons, ocr])
    d = d[d.Sensor == "VIIRS375"].copy()
    d["t"] = pd.to_datetime(d.Fecha_Satelite_UTC, utc=True)
    inv = {vv: k for k, vv in CSVN.items()}
    d["vol"] = d.Volcan.map(lambda v: inv.get(v, v))
    return d


@functools.lru_cache(maxsize=1500)
def raster(path):
    """z por celda segun la v3: dL0 = L - media de vecinas con dato (>=5 de 8);
    z = dL0 / (1.4826 * MAD de dL0 sobre las celdas con dato del raster)."""
    with rasterio.open(path) as ds:
        L = ds.read(1).astype(float)
        nod = ds.nodata
        crs = ds.crs
        rows, cols = np.indices(L.shape)
        xs, ys = rasterio.transform.xy(ds.transform, rows.ravel(), cols.ravel())
        xs = np.array(xs); ys = np.array(ys)
        if crs is None:
            return None
        if crs.to_epsg() != 4326:
            lon, lat = wtransform(crs, "EPSG:4326", xs, ys); lon = np.array(lon); lat = np.array(lat)
        else:
            lon, lat = xs, ys
    if nod is not None:
        L = np.where(L == nod, np.nan, L)
    lat = lat.reshape(L.shape); lon = lon.reshape(L.shape)
    P = np.pad(L, 1, mode="constant", constant_values=np.nan)
    vec = np.stack([P[1 + di:1 + di + L.shape[0], 1 + dj:1 + dj + L.shape[1]]
                    for di in (-1, 0, 1) for dj in (-1, 0, 1) if (di, dj) != (0, 0)])
    nval = np.isfinite(vec).sum(axis=0)
    nb = np.nanmean(vec, axis=0)
    dL = np.where(nval >= 5, L - nb, np.nan)
    fin = dL[np.isfinite(dL)]
    sig = 1.4826 * np.median(np.abs(fin - np.median(fin))) if fin.size else np.nan
    z = dL / sig if sig and np.isfinite(sig) and sig > 0 else np.full(L.shape, np.nan)
    return dict(z=z, L=L, lat=lat, lon=lon, med=float(np.nanmedian(L)),
                epsg=crs.to_epsg(), shape=L.shape, nan_frac=float(np.mean(~np.isfinite(L))))


def Z(R, pt, T=T_KM):
    """Exceso en un punto: maximo de z sobre las celdas con dL0 a <= T de pt. None si no hay."""
    d = hav(R["lat"], R["lon"], pt[0], pt[1])
    m = (d <= T) & np.isfinite(R["z"])
    if not m.any():
        return None
    return float(np.nanmax(np.where(m, R["z"], -np.inf)))


def nanfrac_disco(R, centro, r_km=4.0):
    d = hav(R["lat"], R["lon"], centro[0], centro[1])
    m = d <= r_km
    if not m.any():
        return 1.0
    return float(np.mean(~np.isfinite(R["L"][m])))


def celda_km(R):
    la, lo = R["lat"], R["lon"]
    i, j = la.shape[0] // 2, la.shape[1] // 2
    dy = hav(la[i, j], lo[i, j], la[i + 1, j], lo[i + 1, j])
    dx = hav(la[i, j], lo[i, j], la[i, j + 1], lo[i, j + 1])
    return float(dy), float(dx)


def usable(row, vol, exigir_nan=True):
    """TIF usable segun la v3 (sin el criterio de pasada, que va en el pareo)."""
    if not row["own"]:
        return None, "md5_repetido"
    R = raster(row["path"])
    if R is None:
        return None, "sin_crs"
    if not np.isfinite(R["med"]) or R["med"] >= 0.2:
        return None, "mediana"
    if exigir_nan and nanfrac_disco(R, vent(vol)) >= 0.10:
        return None, "nan_disco"
    return R, "ok"
