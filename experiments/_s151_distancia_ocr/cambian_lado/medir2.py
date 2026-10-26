# -*- coding: utf-8 -*-
"""(a) Satelite de cada pasada que cambia (y de las solo-OCR que no cambian), pareando con nuestros records
(VIIRS 375: VIIRS_SNPP / VIIRS_NOAA20 / VIIRS_NOAA21) a +-240 s. El hito A119 del 2026-10-09 dice que el defecto
"imagen de otra pasada" es de Suomi NPP: si los cambios caen en SNPP, apoya que yerra el OCR y no la serie.
(b) Cruce con las pasadas de los resultados publicados (meses de S150 B/F, Chillan) y con la ventana de F/K V1.
Uso: python medir2.py [--var C]
"""
import argparse, csv, json, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
AQUI = Path(__file__).resolve().parent
EST = REPO / "experiments" / "_s151_alertas_minimas"


def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--var", default="C"); a = ap.parse_args()
    P = list(csv.DictReader(open(AQUI / f"pasadas_{a.var}.csv", encoding="utf-8")))
    for p in P:
        for k in ("hoy_alerta", "alt_alerta", "hoy_prot", "alt_prot", "nocturna", "con_tabla", "misma_clave_tabla"):
            p[k] = p[k] == "True"
        p["vrp"] = float(p["vrp"])
    # satelite desde nuestros records
    recs = defaultdict(list)
    for vol in sorted({p["vol"] for p in P}):
        f = REPO / "data" / "mirova_equivalent" / f"{vol}.json"
        for r in json.load(open(f, encoding="utf-8"))["records"]:
            s = r.get("sensor") or ""
            if s.startswith("VIIRS_") and not s.endswith("_750"):
                recs[vol].append((t(r["datetime_utc"]), s.replace("VIIRS_", "")))
    def sat(p):
        if p["sensor"] != "VIIRS375":
            return "-"
        c = [s for (tt, s) in recs[p["vol"]] if abs((tt - t(p["t"])).total_seconds()) <= 240]
        return "+".join(sorted(set(c))) or "sin_record"
    for p in P:
        p["sat"] = sat(p)
    camb = [p for p in P if p["hoy_alerta"] != p["alt_alerta"]]
    solo = [p for p in P if p["sensor"] == "VIIRS375" and not p["con_tabla"] and p["serie"] in ("cerca", "lejos")]
    print("== (a) satelite (pareo con nuestros records VIIRS 375 a +-240 s)")
    print("   pasadas que cambian (alerta de cualquier VRP):", dict(Counter(p["sat"] for p in camb)))
    print("     nocturnas:", dict(Counter(p["sat"] for p in camb if p["nocturna"])))
    print("   pasadas solo OCR V375 decididas que NO cambian:", dict(Counter(p["sat"] for p in solo if p["hoy_alerta"] == p["alt_alerta"])))
    print("     nocturnas:", dict(Counter(p["sat"] for p in solo if p["hoy_alerta"] == p["alt_alerta"] and p["nocturna"])))
    print("   protegidas que cambian:", [(p["vol"], p["t"], p["sat"]) for p in camb if p["hoy_prot"] != p["alt_prot"]])

    # (b) resultados publicados
    print("\n== (b) cruce con las pasadas de los resultados publicados (pareo +-120 s, el del etiquetador)")
    meses = list(csv.DictReader(open(EST / "pasadas_meses_B_F.csv", encoding="utf-8")))
    ndc = list(csv.DictReader(open(EST / "pasadas_ndc.csv", encoding="utf-8")))
    for nombre, filas, brazos in (("meses de S150 abril a agosto (B, F)", meses, ["B", "F"]),
                                  ("Chillan 09-14 a 10-07", ndc, ["C0", "T0", "E", "B", "F", "J", "K", "KE", "KET"])):
        idx = defaultdict(list)
        for r in filas:
            v, b, tt = r["clave"].split("|")
            idx[(v, b)].append((t(tt), r))
        print(f"   --- {nombre}")
        n = 0
        for p in camb:
            hits = [r for (tt, r) in idx[(p["vol"], p["sensor"])] if abs((tt - t(p["t"])).total_seconds()) <= 120]
            for r in hits:
                n += 1
                pubs = " ".join(f"{b}={r['pub_' + b]}" for b in brazos)
                print(f"     {p['vol']:16s} {p['sensor']} {p['t']} VRP {p['vrp']:.2f} {'pierde' if p['hoy_alerta'] else 'gana'} "
                      f"{'PROTEGIDA' if (p['hoy_prot'] or p['alt_prot']) else 'bajo 1 MW'} | en la tabla de resultados: {r['clave']} lab={r['lab']} vrp_ref={r['vrp_ref']} {pubs}")
        print(f"     pasadas de esos resultados que cambian de etiqueta: {n}")
    fk = [p for p in camb if "2026-08-29" <= p["t"][:10] <= "2026-10-08" and p["nocturna"]]
    print(f"\n   --- F/K V1 (2026-08-29 a 10-08, 11 volcanes; SIN evaluar aun): pasadas nocturnas que cambian {len(fk)}, "
          f"protegidas {sum(p['hoy_prot'] != p['alt_prot'] for p in fk)}")
    for p in fk:
        print(f"     {p['vol']:16s} {p['t']} VRP {p['vrp']:.2f} {'pierde' if p['hoy_alerta'] else 'gana'} sat {p['sat']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
