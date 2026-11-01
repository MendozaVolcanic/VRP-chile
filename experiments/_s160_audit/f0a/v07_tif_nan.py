"""V0a (F6-8): huecos (NaN) en TODOS los GeoTIFF VIIRS750 locales de mirova-tif-archive (no solo los 5 de S158),
con su CRS, y si el hueco cae en la caja central de 7x7 o en el anillo 21x19 (donde el fondo dilatado tocaria al crater).
Se leen archivos locales ya en disco (sin pull, feedback S143). Duplicados por md5 se cuentan aparte (A106).
Pregunta 1: si los TIF no trajeran huecos, todos darian NaN=0. Pregunta 2: control = un TIF con NaN forzado
(se simula sobre la primera matriz poniendo NaN en (33,33)) debe contarse en la caja central."""
import glob, hashlib, io, os, sys, collections
import numpy as np, rasterio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
base = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive/data/tif"
files = sorted(f for f in glob.glob(os.path.join(base, "*", "*VIIRS750*.tif")) if "_lm" not in os.path.basename(f))
print("archivos VIIRS750 (sin _lm):", len(files))
md5s = collections.Counter(); filas = []; crs_c = collections.Counter(); soft = collections.Counter(); shapes = collections.Counter()
for f in files:
    b = open(f, "rb").read(); md5 = hashlib.md5(b).hexdigest(); md5s[md5] += 1
    with rasterio.open(f) as ds:
        a = ds.read(1).astype(float); crs = str(ds.crs); tags = ds.tags()
    shapes[a.shape] += 1; crs_c[crs] += 1; soft[tags.get("TIFFTAG_SOFTWARE", "?")[:40]] += 1
    nan = np.isnan(a)
    if ds.nodata is not None:
        nan |= (a == ds.nodata)
    c = nan.sum(); centro7 = nan[30:37, 30:37].sum() if a.shape == (67, 67) else -1
    anillo = nan[22:43, 24:43].sum() if a.shape == (67, 67) else -1
    filas.append((os.path.basename(os.path.dirname(f)), os.path.basename(f), crs, a.shape, int(c), int(centro7), int(anillo), md5))
print("CRS:", crs_c.most_common()); print("software:", soft.most_common(3)); print("shapes:", shapes.most_common(3))
print("md5 unicos:", len(md5s), "de", len(files), "; el mas repetido:", md5s.most_common(1)[0][1], "veces")
u = {}
for r in filas:
    u.setdefault(r[7], r)
fil = list(u.values())
nans = [r[4] for r in fil]
print(f"TIF unicos: {len(fil)}; con NaN>0: {sum(1 for x in nans if x>0)}; NaN mediana {np.median(nans):.0f} min {min(nans)} max {max(nans)}")
print("con NaN en la caja central 7x7:", sum(1 for r in fil if r[5] > 0), "; con NaN en el anillo 21x19:", sum(1 for r in fil if r[6] > 0))
f67 = [r for r in fil if r[3] == (67, 67)]
print("de los 67x67 unicos:", len(f67), "con NaN>0:", sum(1 for r in f67 if r[4] > 0), "centro7:", sum(1 for r in f67 if r[5] > 0), "anillo:", sum(1 for r in f67 if r[6] > 0))
print("por volcan (unicos 67x67): n, con NaN, con NaN en centro 7x7")
by = collections.defaultdict(lambda: [0, 0, 0])
for r in f67:
    by[r[0]][0] += 1; by[r[0]][1] += r[4] > 0; by[r[0]][2] += r[5] > 0
for k, v in sorted(by.items()): print("  ", k, v)
print("los 5 de S158:")
for r in fil:
    if r[1] in ("20260512_053601_VIIRS750.tif", "20260602_054201_VIIRS750.tif", "20260607_055401_VIIRS750.tif", "20260621_053002_VIIRS750.tif", "20260714_055401_VIIRS750.tif"):
        print("  ", r[:7])
# control positivo
a = np.zeros((67, 67)); a[33, 33] = np.nan
print("control: NaN forzado en (33,33) -> centro7 =", int(np.isnan(a)[30:37, 30:37].sum()), "(esperado 1)")
