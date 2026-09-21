import csv, json, os, datetime as dt, collections
ARCH = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
REPO = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TIF2OURS = {"Chaiten":"Chaiten","ChillanNevadosde":"NevadosDeChillan","Copahue":"Copahue",
 "Isluga":"Isluga","Lascar":"Lascar","Lastarria":"Lastarria","Llaima":"Llaima",
 "PlanchonPeteroa":"PlanchonPeteroa","PuyehueCordonCaulle":"PuyehueCordonCaulle",
 "Tupungatito":"Tupungatito","Villarrica":"Villarrica"}

def tif_rows(sensor="VIIRS375"):
    """Una fila por tif_path unico, con la mejor hora disponible."""
    out = {}
    for r in csv.DictReader(open(os.path.join(ARCH,"index.csv"))):
        if r["sensor"] != sensor: continue
        p = r["tif_path"]
        if p in out: continue
        if r["acquisition_utc"]:
            t = dt.datetime.fromisoformat(r["acquisition_utc"]).replace(tzinfo=None)
            src = "acquisition_utc"
        else:
            fn = p.split("/")[-1][:15]
            t = dt.datetime.strptime(fn, "%Y%m%d_%H%M%S"); src = "filename(last_modified)"
        r["_t"] = t; r["_tsrc"] = src; r["_abs"] = os.path.join(ARCH, p)
        out[p] = r
    return list(out.values())

def records(vol):
    d = json.load(open(os.path.join(REPO,"data","mirova_equivalent",vol+".json"), encoding="utf-8"))
    for r in d["records"]:
        r["_t"] = dt.datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
    return d["records"]


IBAND = {"VIIRS_SNPP","VIIRS_NOAA20","VIIRS_NOAA21"}
def is_iband(s): return s in IBAND
