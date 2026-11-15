# -*- coding: utf-8 -*-
"""Recall y razon de magnitud contra MIROVA por tramo de cenit, via "codigo MIROVA".

Uso:
  python cenit_via.py <raiz_repo> <salida_json> [desde=2026-03-01]

Solo lectura del repo. Cada numero del informe sale del JSON que escribe este script.
"""
import io, json, sys, statistics, collections
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import yaml

ROOT = sys.argv[1]
OUT = sys.argv[2]
DESDE = sys.argv[3] if len(sys.argv) > 3 else "2026-03-01"

TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan", "Llaima",
          "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]
BINS = [(0, 20), (20, 40), (40, 55), (55, 70), (70, 90)]
VENT = timedelta(minutes=60)
VENT_ESTRICTA = timedelta(minutes=10)


def bin_de(z):
    for a, b in BINS:
        if a <= z < b:
            return "%d-%d" % (a, b)
    return "SIN_CENIT"


def fam_nuestro(s):
    s = s.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS") and s.endswith("_750"):
        return "V750"
    if s.startswith("VIIRS"):
        return "V375"
    return None


FAM_MIROVA = {"MODIS": "MODIS", "VIIRS375": "V375", "VIIRS": "V750"}


def publicado(r, inner):
    """Replica mirovaEqVrp de frontend/index.html (includeFar=false)."""
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


ycfg = yaml.safe_load(open(ROOT + "/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
INNER = {v["name"]: v["inner_radius_km"] for v in ycfg if v["name"] in TIER_A}
assert len(INNER) == 11, INNER

res = {"desde_filtro": DESDE, "ventana_min": 60, "por_volcan": {}}
pares = []          # una fila por alerta MIROVA evaluada
pasadas = []        # una fila por pasada nocturna nuestra (via)
contadores = collections.Counter()

for v in TIER_A:
    inner = INNER[v]
    recs = json.load(open(ROOT + "/data/mirova_equivalent/%s.json" % v, encoding="utf-8"))["records"]
    nuestros = collections.defaultdict(list)
    primera_via = {}
    for r in recs:
        fam = fam_nuestro(r.get("sensor", ""))
        if fam is None:
            continue
        contadores["rec_total"] += 1
        if not r.get("via_codigo_mirova"):
            contadores["rec_no_via_" + fam] += 1
            continue
        tt = t(r["datetime_utc"])
        primera_via[fam] = min(primera_via.get(fam, tt), tt)
        sz = r.get("solar_zenith_deg")
        if sz is None or sz <= 90:
            continue
        z = r.get("sensor_zenith_deg")
        pub = publicado(r, inner)
        row = dict(volcan=v, fam=fam, sensor=r["sensor"], t=tt, z=z, pub=pub)
        nuestros[fam].append(row)
        if tt >= t(DESDE + " 00:00"):
            pasadas.append(row)
    ultima = {fam: max(x["t"] for x in L) for fam, L in nuestros.items() if L}
    res["por_volcan"][v] = {"primera_via": {k: str(x) for k, x in primera_via.items()},
                            "ultima_nocturna": {k: str(x) for k, x in ultima.items()}}

    m = json.load(open(ROOT + "/data/mirova/%s.json" % v, encoding="utf-8"))["records"]
    # dedupe por (hora, sensor): preferir 'consolidado' sobre 'ocr'
    ded = {}
    for a in m:
        k = (a["datetime_utc"][:16], a["sensor"])
        if k not in ded or (ded[k]["source"] != "consolidado" and a["source"] == "consolidado"):
            ded[k] = a
    for a in ded.values():
        fam = FAM_MIROVA.get(a["sensor"])
        if fam is None or not a.get("VRP_MW") or a["VRP_MW"] <= 0:
            continue
        if a.get("dia"):
            contadores["mirova_dia_excluida"] += 1
            continue
        if fam == "V375" and a["VRP_MW"] <= 0.05:   # D-9: cuenta como "MIROVA no vio nada"
            contadores["mirova_v375_le_0_05"] += 1
            continue
        ta = t(a["datetime_utc"])
        if ta < t(DESDE + " 00:00"):
            continue
        if fam not in primera_via or ta < primera_via[fam] - VENT or ta > ultima.get(fam, ta) + VENT:
            contadores["mirova_fuera_ventana_via_" + fam] += 1
            continue
        cand = [x for x in nuestros[fam] if abs(x["t"] - ta) <= VENT]
        if not cand:
            # sin pasada nocturna nuestra (o era diurna para nosotros): sin cenit
            todos = [r for r in recs if fam_nuestro(r.get("sensor", "")) == fam and r.get("via_codigo_mirova")
                     and abs(t(r["datetime_utc"]) - ta) <= VENT]
            motivo = "sin_pasada_nuestra" if not todos else "nuestra_pasada_diurna"
            pares.append(dict(volcan=v, fam=fam, t=str(ta), mvrp=a["VRP_MW"], src=a["source"], z=None,
                              bin="SIN_CENIT", tp=False, tp_estricto=False, ours=None, motivo=motivo, dt=None))
            continue
        cerc = min(cand, key=lambda x: abs(x["t"] - ta))
        pos = [x for x in cand if x["pub"] > 0]
        tp = bool(pos)
        par = min(pos, key=lambda x: abs(x["t"] - ta)) if tp else cerc
        tp_e = abs(cerc["t"] - ta) <= VENT_ESTRICTA and cerc["pub"] > 0
        pares.append(dict(volcan=v, fam=fam, t=str(ta), mvrp=a["VRP_MW"], src=a["source"], z=par["z"],
                          z_cerc=cerc["z"], bin=bin_de(par["z"]) if par["z"] is not None else "SIN_CENIT",
                          bin_cerc=bin_de(cerc["z"]) if cerc["z"] is not None else "SIN_CENIT",
                          tp=tp, tp_estricto=tp_e, ours=par["pub"] if tp else 0.0,
                          ours_cerc=cerc["pub"], motivo="ok",
                          dt=(par["t"] - ta).total_seconds() / 60, dt_cerc=(cerc["t"] - ta).total_seconds() / 60))

# ---------- agregados ----------
def med(x):
    return round(statistics.median(x), 3) if x else None


def q(x, p):
    if not x:
        return None
    s = sorted(x)
    return round(s[min(len(s) - 1, int(p * (len(s) - 1) + 0.5))], 3)


binlab = ["%d-%d" % b for b in BINS] + ["SIN_CENIT"]
out = {}
for fam in ["MODIS", "V375", "V750"]:
    P = [p for p in pares if p["fam"] == fam]
    fila = {}
    for b in binlab + ["TODOS"]:
        S = P if b == "TODOS" else [p for p in P if p["bin"] == b]
        if not S:
            continue
        tp = [p for p in S if p["tp"]]
        tpc = [p for p in tp if p["src"] == "consolidado"]
        rat = [p["ours"] / p["mvrp"] for p in tpc]
        Sc = [p for p in S if p["src"] == "consolidado"]
        fila[b] = dict(n_alertas=len(S), n_tp=len(tp), recall=round(len(tp) / len(S), 3),
                       n_alertas_consolidado=len(Sc), n_tp_consolidado=sum(p["tp"] for p in Sc),
                       recall_consolidado=round(sum(p["tp"] for p in Sc) / len(Sc), 3) if Sc else None,
                       n_tp_estricto=sum(p["tp_estricto"] for p in S),
                       n_pares_razon=len(rat), razon_mediana=med(rat), razon_p25=q(rat, .25), razon_p75=q(rat, .75),
                       mirova_vrp_mediana_pares=med([p["mvrp"] for p in tpc]),
                       nuestro_vrp_mediana_pares=med([p["ours"] for p in tpc]),
                       mirova_vrp_mediana_todas=med([p["mvrp"] for p in S]),
                       motivos_sin_cenit=dict(collections.Counter(p["motivo"] for p in S if p["bin"] == "SIN_CENIT")))
    out[fam] = fila
res["por_sensor_tramo"] = out

# por volcan (razon y recall, todos los tramos y por tramo para Chillan y Lascar)
pv = {}
for v in TIER_A:
    pv[v] = {}
    for fam in ["MODIS", "V375", "V750"]:
        P = [p for p in pares if p["fam"] == fam and p["volcan"] == v]
        d = {}
        for b in binlab + ["TODOS"]:
            S = P if b == "TODOS" else [p for p in P if p["bin"] == b]
            if not S:
                continue
            rat = [p["ours"] / p["mvrp"] for p in S if p["tp"] and p["src"] == "consolidado"]
            d[b] = dict(n=len(S), tp=sum(p["tp"] for p in S), recall=round(sum(p["tp"] for p in S) / len(S), 3),
                        n_razon=len(rat), razon_mediana=med(rat))
        pv[v][fam] = d
res["por_volcan_tramo"] = pv

# fraccion de pasadas nocturnas oblicuas (cenit > 40) por sensor, y por volcan
fr = {}
for fam in ["MODIS", "V375", "V750"]:
    L = [x for x in pasadas if x["fam"] == fam and x["z"] is not None]
    Ld = [x for x in L if x["pub"] > 0]
    fr[fam] = dict(n_pasadas=len(L), n_obl=sum(x["z"] > 40 for x in L),
                   frac_obl=round(sum(x["z"] > 40 for x in L) / len(L), 3) if L else None,
                   n_pasadas_con_valor=len(Ld), n_obl_con_valor=sum(x["z"] > 40 for x in Ld),
                   frac_obl_con_valor=round(sum(x["z"] > 40 for x in Ld) / len(Ld), 3) if Ld else None,
                   sin_cenit=sum(1 for x in pasadas if x["fam"] == fam and x["z"] is None),
                   por_tramo=dict(collections.Counter(bin_de(x["z"]) for x in L)),
                   ventana=[str(min(x["t"] for x in L)), str(max(x["t"] for x in L))] if L else None)
res["fraccion_oblicua"] = fr

# ultima pasada nocturna de cada noche (todas las familias juntas): noche = fecha UTC de (t - 12 h)
ult = {}
for v in TIER_A:
    noches = collections.defaultdict(list)
    for x in pasadas:
        if x["volcan"] == v and x["z"] is not None:
            noches[(x["t"] - timedelta(hours=12)).date()].append(x)
    for n, L in noches.items():
        u = max(L, key=lambda x: x["t"])
        ult[(v, n)] = u
U = list(ult.values())
res["ultima_pasada_de_la_noche"] = dict(n_noches_volcan=len(U), n_obl=sum(x["z"] > 40 for x in U),
                                        frac_obl=round(sum(x["z"] > 40 for x in U) / len(U), 3),
                                        sensor_de_la_ultima=dict(collections.Counter(x["fam"] for x in U)))
res["contadores"] = dict(contadores)
res["n_pares"] = len(pares)
res["dt_minutos_tp"] = {fam: dict(collections.Counter(int(round(p["dt"])) // 10 * 10 for p in pares
                                                       if p["fam"] == fam and p["tp"]))
                        for fam in ["MODIS", "V375", "V750"]}
res["ventana_alertas"] = {fam: [min((p["t"] for p in pares if p["fam"] == fam), default=None),
                                max((p["t"] for p in pares if p["fam"] == fam), default=None)]
                          for fam in ["MODIS", "V375", "V750"]}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
json.dump(pares, open(OUT.replace(".json", "_pares.json"), "w", encoding="utf-8"), indent=0, default=str)
print(json.dumps({k: res[k] for k in ["contadores", "n_pares", "ventana_alertas", "fraccion_oblicua",
                                      "ultima_pasada_de_la_noche", "dt_minutos_tp"]}, indent=1, default=str))
for fam, f in out.items():
    print("==", fam)
    for b, d in f.items():
        print(" ", b, {k: d[k] for k in ["n_alertas", "n_tp", "recall", "n_tp_estricto", "recall_consolidado",
                                         "n_pares_razon", "razon_mediana", "razon_p25", "razon_p75",
                                         "mirova_vrp_mediana_pares", "nuestro_vrp_mediana_pares", "motivos_sin_cenit"]})
