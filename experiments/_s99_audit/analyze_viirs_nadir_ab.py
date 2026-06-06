"""S102 — Análisis A/B medición nadir-fijo VIIRS (NO adopción).

Compara, SOLO sobre records VIIRS (375 + 750), la magnitud y el recall del brazo
nadir-VIIRS-ON (artifacts _viirs_nadir_ab) vs el operacional actual
(data/mirova_equivalent, nadir VIIRS OFF). MODIS es igual en ambos => el DIFF
aísla el efecto del nadir VIIRS.

Mide, por sensor (VIIRS375 / VIIRS750) y por volcán, en la ventana del A/B:
  - RATIO mediana nuestro/MIROVA (A10: pc.vrp_mw) — ¿se acerca a 1.0?
  - FN nuevos: días con MIROVA-VIIRS<sensor> confirmado donde el brazo nadir
    pierde la detección (pc.vrp>0) que el operacional SÍ tenía. CRÍTICO: el área
    no debería afectar la detección; FN nuevos = señal de alarma (interacción
    inesperada con ctxpeak/F5').
  - cobertura (under-fetch guard): nº records VIIRS por brazo.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_viirs_ab_art
  python experiments/_s99_audit/analyze_viirs_nadir_ab.py 2026-04-01 2026-05-31
"""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "experiments/_s99_audit/_viirs_ab_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
NAMEMAP = {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
           "NevadosDeChillan": "Nevados de Chillan"}
W0 = sys.argv[1] if len(sys.argv) > 1 else "2026-04-01"
W1 = sys.argv[2] if len(sys.argv) > 2 else "2026-05-31"

# bucket: nuestro sensor -> VIIRS375 / VIIRS750 / None
def our_vbucket(s):
    s = str(s or "")
    if not s.startswith("VIIRS"):
        return None
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"

# MIROVA CSV: 'VIIRS375' -> VIIRS375 ; 'VIIRS' -> VIIRS750
def mir_vbucket(s):
    if s == "VIIRS375":
        return "VIIRS375"
    if s == "VIIRS":
        return "VIIRS750"
    return None


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _pc(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0


def _in(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def load_mirova():
    m = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # vol->bucket->dia->[vrp]
    for r in csv.DictReader(open(REPO / "latest_consolidado.csv", encoding="utf-8")):
        if r["Tipo_Registro"] != "ALERTA_TERMICA":
            continue
        b = mir_vbucket(r["Sensor"])
        if not b:
            continue
        day = r["Fecha_Satelite_UTC"][:10]
        if W0 <= day <= W1:
            try:
                m[r["Volcan"]][b][day].append(float(r["VRP_MW"]))
            except (ValueError, KeyError):
                pass
    return m


def our_daily(recs):
    """{bucket: {dia: max pc.vrp}} para records VIIRS en ventana."""
    d = defaultdict(lambda: defaultdict(float))
    for r in recs:
        b = our_vbucket(r.get("sensor"))
        if not b or not _in(r):
            continue
        day = str(r.get("datetime_utc", ""))[:10]
        d[b][day] = max(d[b][day], _pc(r))
    return d


def main():
    mir = load_mirova()
    print(f"=== A/B nadir-fijo VIIRS (ventana {W0}..{W1}) — base(OFF) -> nadir(ON) ===")
    print(f"{'Volcan':<20} {'sensor':<9} {'ratioB':>7} {'ratioN':>7} {'nMatch':>6} {'FNnew':>6} {'covB':>5} {'covN':>5}")
    glob = defaultdict(lambda: {"rb": [], "rn": [], "fn": 0})
    for vol in VOLS:
        base_f = REPO / "data/mirova_equivalent" / f"{vol}.json"
        nadir_f = ART / f"viirs-nadir-ab-{vol}" / f"{vol}.json"
        if not nadir_f.exists():
            alt = list(ART.rglob(f"viirs-nadir-ab-{vol}/{vol}.json"))
            nadir_f = alt[0] if alt else None
        if nadir_f is None or not base_f.exists():
            print(f"{vol:<20} (falta artifact o base)")
            continue
        base = our_daily(_recs(json.load(open(base_f, encoding="utf-8"))))
        nad = our_daily(_recs(json.load(open(nadir_f, encoding="utf-8"))))
        mvol = mir.get(NAMEMAP.get(vol, vol), {})
        for sb in ["VIIRS375", "VIIRS750"]:
            mdays = mvol.get(sb, {})
            rb, rn, fn = [], [], 0
            covB = len(base.get(sb, {}))
            covN = len(nad.get(sb, {}))
            for day, vrps in mdays.items():
                mv = max(vrps)
                ob = base.get(sb, {}).get(day, 0)
                on = nad.get(sb, {}).get(day, 0)
                if mv > 0 and ob > 0:
                    rb.append(ob / mv)
                if mv > 0 and on > 0:
                    rn.append(on / mv)
                if ob > 0 and on == 0:  # base detectaba, nadir perdió => FN nuevo
                    fn += 1
            glob[sb]["rb"] += rb
            glob[sb]["rn"] += rn
            glob[sb]["fn"] += fn
            med = lambda xs: statistics.median(xs) if xs else float("nan")
            print(f"{vol:<20} {sb:<9} {med(rb):>7.2f} {med(rn):>7.2f} {len(rb):>6} {fn:>6} {covB:>5} {covN:>5}")
    print("\n=== GLOBAL por sensor ===")
    for sb in ["VIIRS375", "VIIRS750"]:
        g = glob[sb]
        med = lambda xs: statistics.median(xs) if xs else float("nan")
        print(f"  {sb:<9} ratio base={med(g['rb']):.2f} -> nadir={med(g['rn']):.2f}  FN_nuevos_total={g['fn']}")
    print("\nLectura: ratio nadir más cerca de 1.0 = mejora. FN_nuevos>0 = ALARMA")
    print("(área no debe afectar detección; FN = interacción inesperada con ctxpeak/F5').")


if __name__ == "__main__":
    main()
