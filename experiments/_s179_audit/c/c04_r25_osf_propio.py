# -*- coding: utf-8 -*-
"""Frente C, auditoria S179. Instrumento c04: R25 contra el OSF v2.5, con codigo propio (P1-OSF y magnitud por cenit).

QUE MIDE. (1) P1-OSF del §5.2 del pre-registro: por cada protegida OSF (noche del proyecto, class 1, VRP >= 1e6 W,
pixel mas caliente dentro del radio interno), si K y la via publican la pasada pareada a +-120 s. (2) Lo que el §5.3
y la prediccion 5 del §9 piden y el lector NO calcula: la razon via/OSF y K/OSF contra el cenit del satelite en R25
(Spearman con barajado propio), por sensor.

VARAS: `publica` y la magnitud mostrada vienen de la tabla de c02 (banco_paridad.correr_node). La noche es la del
proyecto (banco_paridad.es_pasada_diurna_descartada, instantanea de main 438a60a1e). El volcan del OSF se identifica
por COORDENADAS (el lector lo hace por nombre): implementacion distinta a proposito.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si P1-OSF del lector estuviera roto, lo veria? Si: recuenta protegidas por sensor y volcan (el §7 sellado dice
   317 / 17 / 161) y candidatas; se compara contra lectura.json.
2. Si este instrumento estuviera muerto? 0 filas chilenas o 0 protegidas aborta. Control positivo: el brazo K x 1,2
   tiene que dar la razon K/OSF multiplicada por 1,2 (se imprime) y un brazo mudo tiene que dar tantas candidatas
   como protegidas publica K.
Limite declarado (pre-registro §4.3): la razon contra el OSF esta truncada por el piso del OSF (5 MW en 750 m);
es cota, no decide.

Uso: python c04_r25_osf_propio.py TABLA.json [LECTURA.json]
"""
import collections
import csv
import json
import math
import statistics
import sys
from datetime import datetime, timezone

import numpy as np
import yaml

sys.stdout.reconfigure(encoding="utf-8")
MAIN = "D:/vrp-trabajo/temporales/s179-audit/main"
OSF = "D:/vrp-trabajo/worktrees/s178-lectura/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"
sys.path.insert(0, MAIN + "/scripts")
sys.path.insert(0, MAIN)
RES = {"375": "VIIRS375", "750": "VIIRS750", "1000": "MODIS"}
TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "PlanchonPeteroa", "Chaiten", "Copahue", "Llaima",
          "Villarrica", "NevadosDeChillan", "Tupungatito"]


def hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def spearman(x, y):
    def rang(v):
        v = np.asarray(v, dtype=float)
        o = np.argsort(v, kind="mergesort")
        r = np.empty(len(v))
        r[o] = np.arange(len(v))
        # promedio en empates
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1:
                r[m] = r[m].mean()
        return r
    if len(x) < 5:
        return None
    return float(np.corrcoef(rang(x), rang(y))[0, 1])


def main():
    import banco_paridad as bp
    tabla = json.load(open(sys.argv[1], encoding="utf-8"))
    lect = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
    vy = {v["name"]: v for v in yaml.safe_load(open(MAIN + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    vol = {n: vy[n] for n in TIER_A}
    idx = collections.defaultdict(list)
    for f in tabla:
        if f["tramo"] == "R25" and f["estado"] != "sobra_en_via":
            idx[(f["vol"], f["b"])].append(f)
    filas, n_chile = [], 0
    with open(OSF, encoding="latin-1") as fh:
        for r in csv.DictReader(fh):
            la, lo = float(r["Volc_LAT"]), float(r["Volc_LON"])
            if not (-56 < la < -17 and -76 < lo < -66):
                continue
            cand = [(hav(la, lo, v["lat"], v["lon"]), n) for n, v in vol.items()]
            d, n = min(cand)
            if d > 10:
                continue
            dt = datetime.strptime(r["timeUTC"], "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
            if not ("2025-02-15" <= dt.strftime("%Y-%m-%d") <= "2025-12-31"):
                continue
            n_chile += 1
            v = vol[n]
            b = RES[r["Resolution"]]
            cl, cn = (v["vent_lat"], v["vent_lon"]) if v.get("vent_lat") is not None else (v["lat"], v["lon"])
            filas.append({"vol": n, "b": b, "dt": dt, "vrp_mw": float(r["VRP"]) / 1e6, "cl": int(float(r["class"])),
                          "noche": not bp.es_pasada_diurna_descartada(b, v["lat"], v["lon"], dt),
                          "dentro": hav(float(r["LAT"]), float(r["LON"]), cl, cn) <= float(v["inner_radius_km"]),
                          "satzen": float(r["SatZen"]), "nombre": r["Volc_Name"]})
    print(f"filas del OSF de los 11 Tier A en R25 (2025-02-15 a 2025-12-31 UTC): {n_chile}; por volcan "
          f"{dict(collections.Counter(f['vol'] for f in filas))}")
    if not filas:
        sys.exit("ABORTA: 0 filas chilenas")
    prot = [o for o in filas if o["noche"] and o["cl"] == 1 and o["vrp_mw"] >= 1.0 and o["dentro"]]
    print("protegidas OSF por sensor (el §7 sellado dice 317 en 375 m, 17 en 750 m y 161 en 1 km):",
          dict(collections.Counter(o["b"] for o in prot)))
    if not prot:
        sys.exit("ABORTA: 0 protegidas OSF")
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        ps = [o for o in prot if o["b"] == s]
        res = collections.Counter()
        cand, sin_rec, pares, dz = [], [], [], []
        for o in ps:
            c = [f for f in idx.get((o["vol"], s), []) if abs((datetime.strptime(f["dt"], "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone.utc) - o["dt"]).total_seconds()) <= 120]
            if not c:
                sin_rec.append((o["vol"], o["dt"].strftime("%Y-%m-%d %H:%M")))
                continue
            if len(c) > 1:
                res["pareada a dos pasadas"] += 1
            f = c[0]
            if f["estado"] != "ok":
                res["via SIN DATO, K publica" if f["pub_K"] else "via SIN DATO, K no publica"] += 1
                if f["pub_K"]:
                    cand.append((o["vol"], f["dt"], f["estado"]))
                continue
            res[("K si" if f["pub_K"] else "K no") + ", " + ("via si" if f["pub_V"] else "via no")] += 1
            if f["pub_K"] and not f["pub_V"]:
                cand.append((o["vol"], f["dt"], "via_no_publica"))
            if f.get("z") is not None:
                dz.append(abs(float(f["z"]) - o["satzen"]))
            if f["pub_K"] and f["pub_V"] and f["mag_K"] > 0 and f["mag_V"] > 0:
                pares.append((o["satzen"], f["mag_V"] / o["vrp_mw"], f["mag_K"] / o["vrp_mw"], f["mag_PL"] / o["vrp_mw"],
                              o["vol"], f["dt"][:10]))
        print("\n" + "=" * 100)
        print(f"{s}: protegidas OSF {len(ps)}; por volcan {dict(collections.Counter(o['vol'] for o in ps))}")
        print(f"  resultado por protegida: {dict(res)}; sin pasada nuestra a +-120 s: {len(sin_rec)} {sin_rec[:5]}")
        print(f"  candidatas a veto (K publica y la via no, o via SIN DATO): {len(cand)} {cand[:10]}")
        kpub = sum(v for k, v in res.items() if k.startswith("K si"))
        print(f"  CONTROL brazo mudo: daria {kpub} candidatas (las que K publica entre las evaluables)")
        if dz:
            print(f"  C-cenit propio: |cenit nuestro - SatZen| maximo {max(dz):.2f} grados, mediana {statistics.median(dz):.2f}, "
                  f"sobre 2 grados {sum(1 for x in dz if x > 2)} de {len(dz)}")
        if pares:
            z = np.array([p[0] for p in pares])
            rv, rk, rp = (np.array([p[i] for p in pares]) for i in (1, 2, 3))
            print(f"  magnitud contra el OSF (cota, n {len(pares)}): mediana via/OSF {np.median(rv):.3f}; K/OSF {np.median(rk):.3f}; "
                  f"control K x 1,2 / OSF {np.median(rp):.3f} (tiene que ser 1,2 x K/OSF = {1.2 * np.median(rk):.3f})")
            print("  por tramo de 10 grados de SatZen (mediana via/OSF, mediana K/OSF, n):")
            for t in range(0, 80, 10):
                m = (z >= t) & (z < t + 10)
                if m.sum():
                    print(f"     {t:2d}-{t + 10:2d}: via {np.median(rv[m]):.3f}  K {np.median(rk[m]):.3f}  n {int(m.sum())}")
            rng = np.random.default_rng(179)
            for nom, r in (("via/OSF", rv), ("K/OSF", rk)):
                rho = spearman(z, r)
                if rho is None:
                    print(f"  Spearman {nom} contra SatZen: SIN SUSTRATO (n {len(z)})")
                    continue
                nul = [spearman(z, rng.permutation(r)) for _ in range(1000)]
                p = (1 + sum(1 for x in nul if abs(x) >= abs(rho))) / 1001
                print(f"  Spearman {nom} contra SatZen: rho {rho:+.3f}; p por barajado (dos colas, 1.000) {p:.4f}; "
                      f"p95 del nulo en valor absoluto {np.percentile(np.abs(nul), 95):.3f}")
            sinl = [p for p in pares if p[4] != "Lascar"]
            if sinl:
                print(f"  sin Lascar: n {len(sinl)}; mediana via/OSF {statistics.median(p[1] for p in sinl):.3f}; "
                      f"K/OSF {statistics.median(p[2] for p in sinl):.3f}; por volcan {dict(collections.Counter(p[4] for p in sinl))}")
        if lect:
            r = lect["osf"]["por_sensor"][s]
            print(f"  LECTOR (objeto): protegidas {r['protegidas']}; candidatas {len(r['candidatas'])}; sin_record {len(r['sin_record'])}; "
                  f"ninguno {len(r['ninguno'])}; pub_via {r['pub_via']}; razon_cota {r['razon_cota_mediana']}")
    # lejanas OSF (class 1, >= 1 MW, fuera del radio): cuantas publica la via como cumbre
    lej = [o for o in filas if o["noche"] and o["cl"] == 1 and o["vrp_mw"] >= 1.0 and not o["dentro"]]
    pubv = pubk = con = 0
    for o in lej:
        c = [f for f in idx.get((o["vol"], o["b"]), []) if f["estado"] == "ok" and abs((datetime.strptime(
            f["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) - o["dt"]).total_seconds()) <= 120]
        if c:
            con += 1
            pubv += c[0]["pub_V"]
            pubk += c[0]["pub_K"]
    print("\n" + "=" * 100)
    print(f"lejanas OSF (class 1, 1 MW o mas, fuera del radio interno): {len(lej)}; por volcan "
          f"{dict(collections.Counter(o['vol'] for o in lej))}; con pasada evaluable {con}; la via las publica como cumbre "
          f"{pubv}; K {pubk}")


if __name__ == "__main__":
    main()
