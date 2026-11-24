# -*- coding: utf-8 -*-
"""P6 (F5b): TIF de referencia por volcán y sensor para prestar la grilla (transformación y tamaño) a las láminas
posteriores al 2026-09-22, y comprobación de que la grilla es estable en el tiempo.

Por qué: la lámina no trae georreferencia; la toma prestada del TIF del mismo volcán y sensor. Eso sólo vale si la
grilla de MIROVA no se mueve entre pasadas. Se comparan transformaciones de TIF de fechas distintas (junio-agosto
contra 16 a 22 de septiembre, régimen EPSG:4326 según A106) y se mira si los últimos TIF del índice son archivos
distintos o copias con el mismo md5 (memoria: MIROVA sirve el mismo TIF desde el 22-sep).

Pregunta 2 del instrumento: un md5 repetido entre volcanes distintos es una copia, no un dato; se cuenta.
Bajadas sueltas por raw.githubusercontent.com (sin pull). Salida: p6_tif_referencia_out.json y carpeta tif_ref/ en el temporal.
"""
import collections, csv, hashlib, json, os, sys, urllib.request
import rasterio
from rasterio.warp import transform as rtransform

sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b\tif_ref"
os.makedirs(TMP, exist_ok=True)
IDX = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\tif_index.csv"
RAW = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"
# (volcán del archivo, sensor) con aciertos después del 22-sep (p5) más Lascar MODIS (3 alertas sin TIF)
COMBOS = [("Chaiten", "VIIRS375"), ("Chaiten", "VIIRS750"), ("Isluga", "VIIRS375"), ("Lascar", "MODIS"), ("Lascar", "VIIRS375"),
          ("Lascar", "VIIRS750"), ("Lastarria", "VIIRS375"), ("ChillanNevadosde", "MODIS"), ("ChillanNevadosde", "VIIRS375"),
          ("ChillanNevadosde", "VIIRS750"), ("PlanchonPeteroa", "VIIRS375"), ("PuyehueCordonCaulle", "VIIRS375"),
          ("PuyehueCordonCaulle", "VIIRS750"), ("Tupungatito", "VIIRS375")]

rows = [r for r in csv.DictReader(open(IDX, encoding="utf-8")) if not r["tif_path"].endswith("_lm.tif")]
md5_count = collections.Counter(r["md5"] for r in rows)


def bajar(path):
    # Primera corrida (p6_tif_referencia_v0.out.txt): guardaba por nombre base y cuatro volcanes comparten
    # 20260922_045402_VIIRS375.tif, así que el de Chaitén se reutilizó para Chillán, Caulle y Tupungatito (md5_ok False,
    # «grillas distintas» falsas). El control de md5 lo atrapó. Ahora el nombre lleva el volcán.
    dst = os.path.join(TMP, path.split("/")[-2] + "_" + os.path.basename(path))
    if not os.path.exists(dst):
        urllib.request.urlretrieve(RAW + path, dst)
    return dst


def meta(fn):
    with rasterio.open(fn) as ds:
        t = ds.transform
        lon, lat = rtransform(ds.crs, "EPSG:4326", [t.c + t.a * ds.width / 2], [t.f + t.e * ds.height / 2])
        return {"crs": str(ds.crs), "n": [ds.height, ds.width], "a": t.a, "e": t.e, "c": t.c, "f": t.f, "dtype": ds.dtypes[0],
                "centro_latlon": [round(lat[0], 5), round(lon[0], 5)], "nodata": ds.nodata}


out = {}
for vol, sen in COMBOS:
    v = sorted([r for r in rows if r["volcano"] == vol and r["sensor"] == sen], key=lambda r: r["last_modified_utc"])
    # último TIF con md5 que no se repite en otro volcán (una copia compartida no es la grilla de este volcán)
    ult = [r for r in v if md5_count[r["md5"]] == 1 and r["last_modified_utc"] >= "2026-09-16"]
    ago = [r for r in v if "2026-07-15" <= r["last_modified_utc"] < "2026-09-13" and md5_count[r["md5"]] == 1]
    rep = sum(1 for r in v if r["last_modified_utc"] >= "2026-09-16" and md5_count[r["md5"]] > 1)
    sel = {}
    for tag, lst in (("ref_sep", ult[-1:] ), ("control_ago", ago[-1:])):
        if lst:
            r = lst[0]
            fn = bajar(r["tif_path"])
            md5 = hashlib.md5(open(fn, "rb").read()).hexdigest()
            sel[tag] = {"path": r["tif_path"], "acq": r["acquisition_utc"], "last_modified": r["last_modified_utc"],
                        "md5_ok": md5 == r["md5"], **meta(fn)}
    misma = None
    if "ref_sep" in sel and "control_ago" in sel:
        A, B = sel["ref_sep"], sel["control_ago"]
        misma = (A["crs"] == B["crs"] and A["n"] == B["n"] and all(abs(A[k] - B[k]) < 1e-9 for k in "aecf"))
    out[f"{vol}|{sen}"] = {"n_tif_total": len(v), "n_desde_0916_md5_unico": len(ult), "n_desde_0916_md5_repetido": rep, "misma_grilla_sep_vs_ago": misma, **sel}
    print(f"{vol}|{sen}", json.dumps(out[f'{vol}|{sen}'], ensure_ascii=False, default=str))
json.dump(out, open(os.path.join(H, "p6_tif_referencia_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
