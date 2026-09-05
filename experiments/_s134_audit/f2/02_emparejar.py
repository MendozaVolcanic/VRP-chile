# -*- coding: utf-8 -*-
"""F2/02 - CONTROL DEL EMPAREJAMIENTO: el TIF, la ALERTA y nuestro record, la MISMA pasada?

LAS DOS PREGUNTAS:
1. Si el emparejamiento estuviera roto (TIF de otra pasada), esto lo veria? SI: mido la
   distribucion de |dt| entre los tres relojes. Si el TIF fuera de otra orbita, el desfase
   se agruparia en ~100 min (periodo orbital), no en <2 min.
2. Si el instrumento estuviera muerto (0 pares), se veria distinto de "no hay pares"? SI:
   reporto n de cada etapa (alertas -> con TIF -> con record) por separado.
Read-only."""
import datetime as dt, sys
import f2_lib as F
F.utf8()

D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
TOL = 1200  # +-20 min

def pares(vol, bucket="VIIRS375", tol=TOL, desde=D0):
    ix = [r for r in F.indice() if r["vol"] == vol and r["sensor"] == bucket and r["ts"] >= desde]
    rec = F.records(vol, F.IBAND if bucket == "VIIRS375" else None, desde)
    out = []
    for a in F.alertas(vol):
        if a["_ts"] < desde or a["sensor_bucket"] != bucket: continue
        t = a["_ts"]
        tf = min(ix, key=lambda r: abs((r["ts"]-t).total_seconds()), default=None)
        rc = min(rec, key=lambda r: abs((r["_ts"]-t).total_seconds()), default=None)
        dtf = abs((tf["ts"]-t).total_seconds()) if tf else None
        drc = abs((rc["_ts"]-t).total_seconds()) if rc else None
        out.append(dict(alerta=a, tif=tf if (dtf is not None and dtf <= tol) else None,
                        rec=rc if (drc is not None and drc <= tol) else None,
                        dt_tif=dtf, dt_rec=drc))
    return out

if __name__ == "__main__":
    VOLS = ["Lascar", "Villarrica", "Llaima", "Copahue", "PuyehueCordonCaulle"]
    print("volcan               alertas  con_TIF  con_record  con_ambos | dt_tif_med_s  dt_rec_med_s")
    tot = []
    for v in VOLS:
        p = pares(v)
        ct = sum(1 for x in p if x["tif"]); cr = sum(1 for x in p if x["rec"])
        ca = sum(1 for x in p if x["tif"] and x["rec"])
        mt = F.mediana([x["dt_tif"] for x in p if x["tif"]])
        mr = F.mediana([x["dt_rec"] for x in p if x["rec"]])
        print("%-20s %7d %8d %11d %10d | %11s %13s" % (v, len(p), ct, cr, ca,
              "%.0f" % mt if mt is not None else "SIN DATO",
              "%.0f" % mr if mr is not None else "SIN DATO"))
        tot += p
    print("\nCONTROL: 3 casos concretos (TIF vs ALERTA vs nuestro record)")
    n = 0
    for x in tot:
        if x["tif"] and x["rec"] and n < 3:
            n += 1
            print("  %-12s ALERTA %s | TIF %s (dt=%.0fs) | record %s (dt=%.0fs) sensor=%s" % (
                x["alerta"]["volcano"], x["alerta"]["_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                x["tif"]["ts"].strftime("%H:%M:%S"), x["dt_tif"],
                x["rec"]["_ts"].strftime("%H:%M:%S"), x["dt_rec"], x["rec"]["sensor"]))
    # distribucion del desfase: distingue "misma pasada" de "otra orbita"
    ds = sorted(x["dt_tif"] for x in tot if x["tif"])
    if ds:
        print("\ndesfase TIF-ALERTA (n=%d): p50=%.0fs p90=%.0fs max=%.0fs ; <=120s: %.1f%%" % (
            len(ds), ds[len(ds)//2], ds[int(.9*len(ds))], ds[-1],
            100*sum(1 for d in ds if d <= 120)/len(ds)))
    dr = sorted(x["dt_rec"] for x in tot if x["rec"])
    if dr:
        print("desfase record-ALERTA (n=%d): p50=%.0fs p90=%.0fs max=%.0fs ; <=120s: %.1f%%" % (
            len(dr), dr[len(dr)//2], dr[int(.9*len(dr))], dr[-1],
            100*sum(1 for d in dr if d <= 120)/len(dr)))
