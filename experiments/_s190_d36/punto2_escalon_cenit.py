# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): script de medición, sólo lectura. No es detección de producción; no escribe en data/.
"""D36, punto 2: ¿reproducir el escalón de cenit de MIROVA VIIRS 750 (sobre 50°, el OSF v2.5 publica ~0,51 del VRP de
su propio código en el 24 % de las filas, experiments/_s158_audit/f6/INFORME.md) nos acercaría a lo que MIROVA publica
hoy en el NRT?

POR QUÉ: la vía ya reproduce el código (.m) de MIROVA. Si el NRT de MIROVA siguiera aplicando el escalón, nuestra razón
contra MIROVA en la misma pasada sería ~2 sobre 50° (o una mezcla de 1 y 2) y ~1 bajo 50°. Si la razón es ~1 a ambos
lados, el escalón no está en lo que MIROVA publica hoy y reproducirlo nos alejaría.

Pares: criterio de experiments/_s184_cenit/cenit_via.py (alerta MIROVA nocturna, VRP > 0, dedupe por hora y sensor
prefiriendo «consolidado»; valor nuestro = mirovaEqVrp de frontend/index.html), pero sólo la pasada MISMA (la nuestra
más cercana del mismo sensor a 10 min o menos, A109) y sólo fuente «consolidado» (el OCR no sirve para magnitud).
Ventana: desde DESDE (por defecto 2026-03-01, tabla de MIROVA comparable) hasta el último record.
PODER (verificador S190): en el OSF el escalón casi no actúa bajo 20 MW de VRP del código (2 de 12.048 filas con cenit
> 50°) y actúa casi siempre sobre 500 MW (4.050 de 4.111). Por eso los pares sobre 50° se parten por nuestra magnitud
(que es la del código): bajo 20 MW la prueba no tiene poder, y sólo los pares grandes pueden mostrar el escalón. El
«|log| con escalón» se calcula sólo sobre 50° (bajo 50° el escalón nunca actúa en el OSF).
Uso: python experiments/_s190_d36/punto2_escalon_cenit.py <raiz_repo> <salida.json> [DESDE]
"""
import collections
import json
import math
import sys
from datetime import datetime, timedelta

import yaml

ROOT, OUT = sys.argv[1], sys.argv[2]
DESDE = sys.argv[3] if len(sys.argv) > 3 else "2026-03-01"
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "PlanchonPeteroa", "Tupungatito", "Isluga", "Lastarria", "Chaiten"]
FAM_MIROVA = {"MODIS": "MODIS", "VIIRS375": "V375", "VIIRS": "V750"}
ESTRICTA = timedelta(minutes=10)
FACTOR = 0.51   # mediana del escalón en el OSF v2.5 (f6/INFORME.md)


def fam_nuestro(s):
    s = s.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "V750"
    if s.startswith("VIIRS"):
        return "V375"
    return None


def publicado(r, inner):
    """Réplica de mirovaEqVrp (includeFar=false), copiada de experiments/_s184_cenit/cenit_via.py."""
    pc = r.get("primary_cluster")
    if not pc:
        v = r.get("vrp_mw") or r.get("vrp_mir_mw") or 0
        return 0 if v > 50000 else v
    dc = r.get("distance_class")
    if dc and dc != "summit":
        return 0
    cd = pc.get("centroid_dist_km")
    if cd is not None and cd > inner:
        return 0
    v = pc.get("vrp_mw") or 0
    return 0 if v > 50000 else v


def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def mediana(x):
    x = sorted(x)
    n = len(x)
    if not n:
        return None
    return x[n // 2] if n % 2 else 0.5 * (x[n // 2 - 1] + x[n // 2])


def cuantil(x, p):
    x = sorted(x)
    if not x:
        return None
    k = (len(x) - 1) * p
    a, b = int(math.floor(k)), int(math.ceil(k))
    return x[a] + (x[b] - x[a]) * (k - a)


ycfg = yaml.safe_load(open(ROOT + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
INNER = {v["name"]: v["inner_radius_km"] for v in ycfg if v["name"] in TIER_A}
assert len(INNER) == 11

pares, cont = [], collections.Counter()
for v in TIER_A:
    recs = json.load(open(ROOT + "/data/mirova_equivalent/%s.json" % v, encoding="utf-8"))["records"]
    nuestros = collections.defaultdict(list)
    for r in recs:
        fam = fam_nuestro(r.get("sensor", ""))
        if fam is None or not r.get("via_codigo_mirova"):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is None or sz <= 90:
            continue
        nuestros[fam].append(dict(t=t(r["datetime_utc"]), z=r.get("sensor_zenith_deg"), pub=publicado(r, INNER[v]),
                                  sensor=r["sensor"]))
    m = json.load(open(ROOT + "/data/mirova/%s.json" % v, encoding="utf-8"))["records"]
    ded = {}
    for a in m:
        k = (a["datetime_utc"][:16], a["sensor"])
        if k not in ded or (ded[k]["source"] != "consolidado" and a["source"] == "consolidado"):
            ded[k] = a
    for a in ded.values():
        fam = FAM_MIROVA.get(a["sensor"])
        if fam is None or not a.get("VRP_MW") or a["VRP_MW"] <= 0 or a.get("dia"):
            continue
        if fam == "V375" and a["VRP_MW"] <= 0.05:
            continue
        ta = t(a["datetime_utc"])
        if ta < t(DESDE + " 00:00"):
            continue
        cont["alertas_" + fam] += 1
        if a["source"] != "consolidado":
            cont["ocr_excluida_" + fam] += 1
            continue
        cand = [x for x in nuestros[fam] if abs(x["t"] - ta) <= ESTRICTA]
        if not cand:
            cont["sin_misma_pasada_" + fam] += 1
            continue
        c = min(cand, key=lambda x: abs(x["t"] - ta))
        if c["z"] is None:
            cont["sin_cenit_" + fam] += 1
            continue
        if c["pub"] <= 0:
            cont["nuestro_cero_" + fam] += 1
            pares.append(dict(volcan=v, fam=fam, t=str(ta), z=c["z"], mvrp=a["VRP_MW"], ours=0.0))
            continue
        pares.append(dict(volcan=v, fam=fam, t=str(ta), z=c["z"], mvrp=a["VRP_MW"], ours=c["pub"]))


def resumen(P, escalon=True):
    pos = [p for p in P if p["ours"] > 0]
    r = [p["ours"] / p["mvrp"] for p in pos]
    r_esc = [FACTOR * x for x in r] if escalon else list(r)
    err = [abs(math.log(x)) for x in r]
    err_esc = [abs(math.log(x)) for x in r_esc]
    return {"n_pares": len(P), "n_nuestro_positivo": len(pos),
            "razon_mediana": mediana(r), "razon_p25": cuantil(r, 0.25), "razon_p75": cuantil(r, 0.75),
            "frac_razon_0_9_a_1_1": (sum(0.9 <= x <= 1.1 for x in r) / len(r)) if r else None,
            "n_razon_0_9_a_1_1": sum(0.9 <= x <= 1.1 for x in r),
            "frac_razon_1_7_a_2_3": (sum(1.7 <= x <= 2.3 for x in r) / len(r)) if r else None,
            "n_razon_1_7_a_2_3": sum(1.7 <= x <= 2.3 for x in r),
            "err_log_mediano_hoy": mediana(err), "err_log_mediano_con_escalon": mediana(err_esc),
            "n_mas_cerca_con_escalon": sum(e2 < e1 for e1, e2 in zip(err, err_esc))}


res = {"desde": DESDE, "factor_escalon": FACTOR, "contadores": dict(cont), "por_familia": {}, "por_volcan_v750": {}}
for fam in ("V750", "V375", "MODIS"):
    P = [p for p in pares if p["fam"] == fam]
    res["por_familia"][fam] = {"z_le_50": resumen([p for p in P if p["z"] <= 50], escalon=False),
                               "z_gt_50": resumen([p for p in P if p["z"] > 50]),
                               "ultima_hora_par": max((p["t"] for p in P), default=None)}
for v in TIER_A:
    P = [p for p in pares if p["fam"] == "V750" and p["volcan"] == v and p["z"] > 50]
    if P:
        res["por_volcan_v750"][v] = resumen(P)
TRAMOS = [(0, 20), (20, 100), (100, 500), (500, 1e9)]
res["v750_z_gt_50_por_magnitud_nuestra"] = {}
for a, b in TRAMOS:
    P = [p for p in pares if p["fam"] == "V750" and p["z"] > 50 and a < p["ours"] <= b]
    res["v750_z_gt_50_por_magnitud_nuestra"]["%g-%g MW" % (a, b)] = resumen(P)
res["pares_v750_z_gt_50"] = sorted([p for p in pares if p["fam"] == "V750" and p["z"] > 50], key=lambda p: p["t"])
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for fam, d in res["por_familia"].items():
    for k in ("z_le_50", "z_gt_50"):
        x = d[k]
        print(fam, k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in x.items()})
print("contadores", dict(cont))
for k, d in res["v750_z_gt_50_por_magnitud_nuestra"].items():
    print("V750 z>50 tramo", k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in d.items()
                                 if kk in ("n_nuestro_positivo", "razon_mediana", "razon_p25", "razon_p75", "n_razon_1_7_a_2_3")})
print("por volcan V750 z>50:", {v: (d["n_nuestro_positivo"], round(d["razon_mediana"], 3) if d["razon_mediana"] else None)
                               for v, d in res["por_volcan_v750"].items()})
