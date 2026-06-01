"""S97 — Promover el snapshot de staging ensamblado a la data operacional.

Por volcán Tier A, reemplaza en data/mirova_equivalent/<vol>.json los records que
caen DENTRO de la cobertura del staging (por bucket de sensor × ventana de fechas que
el staging efectivamente cubre) por los records del staging (data/_s97_refresh). Los
records live FUERA de esa cobertura (ej. MODIS may30-31, VIIRS posteriores) se preservan.

Esto (a) elimina artefactos viejos en la ventana (records que el código actual ya no
detecta) y (b) puebla anomaly_pixels + magnitud corregida. La detección no cambia
respecto a lo que el código ACTUAL produce (es exactamente el staging).

Report-first: sin --apply solo reporta el diff. Con --apply escribe (PRECEDER de tag
defensivo git + OK Nicolás, A45/A38).

Integridad §0.5: salida a archivo, números desde el script.
Uso: python promote_refresh.py [--apply]
"""
import os, io, sys, json
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_fd = os.dup(1)
OUT = io.TextIOWrapper(os.fdopen(_fd, "wb"), encoding="utf-8", write_through=True)

LIVE_DIR = os.path.join(REPO, "data/mirova_equivalent")
STAGE_DIR = os.path.join(REPO, "data/_s97_refresh")
APPLY = "--apply" in sys.argv
TIER = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
        "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]


def bucket(sensor):
    s = str(sensor or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if s.endswith("_750"):
        return "V750"
    if s.startswith("VIIRS"):
        return "V375"
    return "OTHER"


def load(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def recs_of(d):
    return d.get("records", []) if isinstance(d, dict) else (d or [])


OUT.write("=" * 104 + "\n")
OUT.write(f"S97 — PROMOTE staging→operacional  (APPLY={APPLY})\n")
OUT.write("Regla: dropear live dentro de cobertura staging (bucket×[min,max]); reemplazar por staging; preservar fuera.\n")
OUT.write("=" * 104 + "\n")
OUT.write(f"{'Volcán':<22}{'live':>6}{'stage':>6}{'final':>6}{'dropped':>8}{'added':>7}{'replaced':>9}{'preserved':>10}\n")
OUT.write("-" * 104 + "\n")
tot = dict(live=0, final=0, dropped=0, added=0, replaced=0, preserved=0)
for vol in TIER:
    live = load(os.path.join(LIVE_DIR, f"{vol}.json"))
    stage = load(os.path.join(STAGE_DIR, f"{vol}.json"))
    if live is None or stage is None:
        OUT.write(f"{vol:<22}  (falta live o staging — skip)\n")
        continue
    lrecs, srecs = recs_of(live), recs_of(stage)
    # cobertura staging: por bucket, [min,max] de fechas presentes
    cov = {}
    for r in srecs:
        b = bucket(r.get("sensor")); dt = (r.get("datetime_utc") or "")[:10]
        if not dt:
            continue
        lo, hi = cov.get(b, (dt, dt))
        cov[b] = (min(lo, dt), max(hi, dt))
    skey = {(r.get("datetime_utc"), r.get("sensor")): r for r in srecs}
    final = {}
    preserved = dropped = 0
    for r in lrecs:
        b = bucket(r.get("sensor")); dt = (r.get("datetime_utc") or "")[:10]
        in_cov = b in cov and dt and cov[b][0] <= dt <= cov[b][1]
        if in_cov:
            dropped += 1  # será reemplazado/eliminado por el staging
        else:
            final[(r.get("datetime_utc"), r.get("sensor"))] = r
            preserved += 1
    replaced = sum(1 for k in skey if k in {(r.get("datetime_utc"), r.get("sensor")) for r in lrecs})
    added = len(skey) - replaced
    for k, r in skey.items():
        final[k] = r
    final_recs = sorted(final.values(), key=lambda r: (r.get("datetime_utc", ""), str(r.get("sensor", ""))))
    OUT.write(f"{vol:<22}{len(lrecs):>6}{len(srecs):>6}{len(final_recs):>6}{dropped:>8}{added:>7}{replaced:>9}{preserved:>10}\n")
    tot["live"] += len(lrecs); tot["final"] += len(final_recs); tot["dropped"] += dropped
    tot["added"] += added; tot["replaced"] += replaced; tot["preserved"] += preserved
    if APPLY:
        out = {"volcano": live.get("volcano", vol) if isinstance(live, dict) else vol,
               "updated": live.get("updated") if isinstance(live, dict) else None,
               "records": final_recs}
        with open(os.path.join(LIVE_DIR, f"{vol}.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
OUT.write("-" * 104 + "\n")
OUT.write(f"{'TOTAL':<22}{tot['live']:>6}{'':>6}{tot['final']:>6}{tot['dropped']:>8}{tot['added']:>7}{tot['replaced']:>9}{tot['preserved']:>10}\n")
OUT.write(f"\n{'APLICADO a data/mirova_equivalent.' if APPLY else 'REPORT-ONLY (sin --apply no se escribió nada).'}\n")
OUT.flush()
