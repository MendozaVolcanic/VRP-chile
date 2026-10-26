# -*- coding: utf-8 -*-
"""Verificador con contexto limpio del censo MOD-D. Recalcula por su cuenta, desde los records de los jsonl, la
cobertura, los 189 fuera del denominador, P1, P1b, P2, M y Chillan, y los controles que se pueden medir sin el
evaluador. Usa el predicado del tablero (node) a traves de banco_paridad.correr_node, que es la definicion sellada
de «publica», pero arma los records y las pruebas con codigo propio. Escribe un JSON con todo."""
import collections, glob, hashlib, json, math, statistics, sys
from pathlib import Path
import numpy as np

RAIZ = Path("C:/vrp-trabajo/s162-modd")
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
sys.path.insert(0, str(RAIZ / "experiments/_s162_modis_paquete"))
import banco_paridad as bp          # noqa: E402
import importlib.util               # noqa: E402

ART = Path("D:/vrp-trabajo/temporales/s162_modd/censo")
POB = Path("D:/vrp-trabajo/temporales/s162_modd/poblacion.json")
OUT = Path("D:/vrp-trabajo/temporales/s162_modd/verificador_censo")
CAMPOS_JS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason",
             "triggered_test1", "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw", "anomaly_pixels"]
R = {}


def cargar_d25():
    spec = importlib.util.spec_from_file_location("d25", RAIZ / "experiments/_s162_modis_paquete/evaluar_d25_ded217af4.py")
    m = importlib.util.module_from_spec(spec); sys.modules["d25"] = m; spec.loader.exec_module(m); return m


# ---------------------------------------------------------------- 1. carga y cobertura
archivos = sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True))
cab, rec, pie = [], [], []
por_archivo = {}
for a in archivos:
    n = 0
    for x in open(a, encoding="utf-8"):
        r = json.loads(x); r["_archivo"] = a
        t = r.get("tipo")
        (cab if t == "cabecera" else rec if t == "record" else pie).append(r); n += 1
    por_archivo[Path(a).name] = n
pob = json.load(open(POB, encoding="utf-8"))
esperadas = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
vistos = collections.Counter((r["vol"], r["dt"]) for r in rec)
R["cobertura"] = {
    "archivos": len(archivos), "nombres": sorted(Path(a).name for a in archivos),
    "cabeceras": len(cab), "partes_cab": sorted(c["parte"] for c in cab),
    "commits_cab": sorted({c["commit"] for c in cab}), "refs_cab": sorted({c["ref"] for c in cab}),
    "poblacion_checkout_cab": sorted({c["poblacion_checkout"] for c in cab}),
    "pies": len(pie), "errores_pie": sum(p.get("errores", -1) for p in pie), "minutos_pie": sum(p.get("minutos", 0) for p in pie),
    "records": len(rec), "claves_distintas": len(vistos), "repetidas": [k for k, n in vistos.items() if n > 1],
    "esperadas": len(esperadas), "granulos_pob": len(pob["granulos"]), "partes_pob": len(pob["partes"]),
    "faltan": sorted(set(esperadas) - set(vistos)), "sobran": sorted(set(vistos) - set(esperadas)),
    "estados": dict(collections.Counter(r["estado"] for r in rec)),
    "port_estados": dict(collections.Counter(r.get("port_estado") for r in rec)),
    "labs_pob": dict(collections.Counter(f["lab"] for f in esperadas.values())),
    "ids_distintos": len({r["id"] for r in rec}),
    "parte_contiene_sus_granulos": all(
        {r["clave"] for r in rec if r["_archivo"].endswith("ab_parte%02d.jsonl" % c["parte"])} == set(pob["partes"][c["parte"]])
        for c in cab),
}
# etiqueta y cenit del record contra la poblacion
dist_lab = [(r["vol"], r["dt"]) for r in rec if r["lab"] != esperadas[(r["vol"], r["dt"])]["lab"] or r["z"] != esperadas[(r["vol"], r["dt"])]["z"]]
R["cobertura"]["record_distinto_de_poblacion"] = dist_lab[:10]
R["cobertura"]["n_record_distinto"] = len(dist_lab)

# ---------------------------------------------------------------- 2. fuera del denominador (lectura propia)
def motivo(f):
    if f["estado"] != "ok":
        return "falla_arnes"
    if f.get("port_estado") == "volcan_fuera_del_granulo":
        return "volcan_fuera_del_granulo"
    if f.get("port_estado") != "ok" or not f.get("port"):
        return "falla_port"
    if (f["port"].get("fisica") or {}).get("motivo_vacio") == "escena_invalida":
        return "escena_invalida"
    return None

for r in rec:
    r["_m"] = motivo(r)
    for k, v in esperadas[(r["vol"], r["dt"])].items():   # como unir(): la poblacion aporta vrp_mirova, noche, partida...
        r.setdefault(k, v)
fuera = [r for r in rec if r["_m"]]
R["fuera"] = {
    "n": len(fuera), "por_motivo": dict(collections.Counter(r["_m"] for r in fuera)),
    "labs": {m: dict(collections.Counter(r["lab"] for r in fuera if r["_m"] == m)) for m in set(r["_m"] for r in fuera)},
    "protegidas": [(r["vol"], r["dt"], r["_m"]) for r in fuera if r["lab"] == "protegida"],
    "k_pub_runner": {m: dict(collections.Counter(int((r.get("pub") or {}).get("K") or 0) for r in fuera if r["_m"] == m)) for m in set(r["_m"] for r in fuera)},
    "k_n_anom": {m: dict(collections.Counter(int(((r.get("brazos") or {}).get("K") or {}).get("n_anom") or 0) for r in fuera if r["_m"] == m)) for m in set(r["_m"] for r in fuera)},
    "borde": {m: dict(collections.Counter(bool((r.get("crater_mxd03") or {}).get("borde")) for r in fuera if r["_m"] == m)) for m in set(r["_m"] for r in fuera)},
    "motivo_vacio_fisica": dict(collections.Counter(str((r.get("port") or {}).get("fisica", {}).get("motivo_vacio")) for r in fuera)),
    "nan_mir_escena_invalida": sorted(((r.get("port") or {}).get("fisica", {}).get("nan_mir") or 0) for r in fuera if r["_m"] == "escena_invalida")[:5],
    "vols_fuera_granulo": dict(collections.Counter(r["vol"] for r in fuera if r["_m"] == "volcan_fuera_del_granulo")),
    "pub_k_guardada_pob": {m: dict(collections.Counter(esperadas[(r["vol"], r["dt"])]["pub_guardada"] for r in fuera if r["_m"] == m)) for m in set(r["_m"] for r in fuera)},
}
ev = [r for r in rec if not r["_m"]]
R["n_evaluables"] = len(ev)

# ---------------------------------------------------------------- 3. predicado propio
grillas = json.load(open(RAIZ / "experiments/_s162_modis_paquete/grillas.json", encoding="utf-8"))


def mi_record_port(p, inner, sensor, g):
    """Reescritura propia de 04_analizar.record_port + dist_centroide."""
    if not p or not p.get("npix") or p.get("vrp_mw") is None:
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    px = p["pixeles"]
    fr, fc = np.mean([q[0] for q in px]), np.mean([q[1] for q in px])
    x = g["ul_x"] + g["celda"] * (fc + 0.5); y = g["ul_y"] - g["celda"] * (fr + 0.5)
    dcen = float(np.hypot(x - g["X0"], y - g["Y0"]) / 1000.0)
    v = round(float(p["vrp_mw"]), 4)
    return {"sensor": sensor, "vrp_mw": v, "f5_core_vrp_mw": v, "t_max_k": max(q[5] for q in px), "triggered_test1": False,
            "distance_class": "summit" if dcen <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": p["npix"], "centroid_dist_km": round(dcen, 3)}}


def slim(x):
    s = {k: x.get(k) for k in CAMPOS_JS}
    if s.get("anomaly_pixels") is None:
        s["anomaly_pixels"] = []
    return s


casos, idx = [], []
for i, f in enumerate(ev):
    casos.append([slim(f["k_slim"]), f["inner"]]); idx.append((i, "K"))
    casos.append([slim(f["k33_slim"]), f["inner"]]); idx.append((i, "K33"))
    for b, m in (("PM", "fisica"), ("PM-geo5", "fisica_geo5km"), ("PM-sens", "sensible"), ("PM-pixel", "pixel"), ("PM-b21", "fisica_b21")):
        casos.append([slim(mi_record_port(f["port"].get(m), f["inner"], f["sensor"], grillas[f["vol"]])), f["inner"]]); idx.append((i, b))
res = []
for k in range(0, len(casos), 4000):
    res += bp.correr_node(casos[k:k + 4000])
for (i, b), p in zip(idx, res):
    ev[i].setdefault("_t", {})[b] = (int(p[4]), float(p[3] or 0.0))

# comparar con lo que el arnes dijo de K y K33
R["predicado"] = {
    "K_distinto_runner": [(f["vol"], f["dt"]) for f in ev if f["_t"]["K"][0] != int((f.get("pub") or {}).get("K") or 0)],
    "K33_distinto_runner": [(f["vol"], f["dt"]) for f in ev if f["_t"]["K33"][0] != int((f.get("pub") or {}).get("K33") or 0)],
    "K_pub_distinto_pob_guardada": [(f["vol"], f["dt"]) for f in ev if f["_t"]["K"][0] != esperadas[(f["vol"], f["dt"])]["pub_guardada"]][:20],
    "n_K_pub_distinto_pob_guardada": sum(1 for f in ev if f["_t"]["K"][0] != esperadas[(f["vol"], f["dt"])]["pub_guardada"]),
    "mag_K_distinta_pc_vrp": [(f["vol"], f["dt"], f["_t"]["K"][1], ((f.get("brazos") or {}).get("K") or {}).get("pc_vrp")) for f in ev
                              if f["_t"]["K"][0] == 1 and abs(f["_t"]["K"][1] - (((f.get("brazos") or {}).get("K") or {}).get("pc_vrp") or 0)) > 1e-9][:20],
    "mag_PM_distinta_port_vrp": [(f["vol"], f["dt"], f["_t"]["PM"][1], f["port"]["fisica"].get("vrp_mw")) for f in ev
                                 if f["_t"]["PM"][0] == 1 and abs(f["_t"]["PM"][1] - round(f["port"]["fisica"]["vrp_mw"], 4)) > 1e-9][:20],
    "PM_publica_con_npix0": sum(1 for f in ev if f["_t"]["PM"][0] == 1 and not f["port"]["fisica"].get("npix")),
    "PM_npix_sin_publicar": dict(collections.Counter(("summit" if True else "") for f in ev if f["port"]["fisica"].get("npix") and f["_t"]["PM"][0] == 0)),
    "PM_npix_sin_publicar_detalle": [(f["vol"], f["dt"], f["lab"], f["port"]["fisica"]["npix"], f["port"]["fisica"]["vrp_mw"],
                                      mi_record_port(f["port"]["fisica"], f["inner"], f["sensor"], grillas[f["vol"]])["primary_cluster"]["centroid_dist_km"], f["inner"])
                                     for f in ev if f["port"]["fisica"].get("npix") and f["_t"]["PM"][0] == 0][:40],
    "n_PM_npix_sin_publicar": sum(1 for f in ev if f["port"]["fisica"].get("npix") and f["_t"]["PM"][0] == 0),
    "pub_por_brazo": {b: sum(f["_t"][b][0] for f in ev) for b in ("K", "K33", "PM", "PM-geo5", "PM-sens", "PM-pixel", "PM-b21")},
}

# ---------------------------------------------------------------- 4. pruebas propias
def pub(f, b): return f["_t"][b][0]
def mag(f, b): return f["_t"][b][1]
def bloque(f): return (f["vol"], f["noche"])

prot = [f for f in ev if f["lab"] == "protegida"]
R["labs_evaluables"] = dict(collections.Counter(f["lab"] for f in ev))
R["P1"] = {b: [(f["vol"], f["dt"]) for f in prot if pub(f, "K") == 1 and pub(f, b) == 0] for b in ("PM", "PM-geo5", "PM-sens", "PM-pixel", "PM-b21")}
R["protegidas_K_publica"] = sum(1 for f in prot if pub(f, "K") == 1)
R["protegidas_K_no_publica"] = [(f["vol"], f["dt"], f["z"], pub(f, "PM"), mag(f, "PM"), f["vrp_mirova"]) for f in prot if pub(f, "K") == 0]
R["P1b"] = {}
for b in ("PM", "PM-geo5", "PM-sens", "PM-pixel"):
    baja = [(f["vol"], f["dt"], mag(f, "K"), mag(f, b), f["vrp_mirova"]) for f in prot if pub(f, "K") == 1 and pub(f, b) == 1 and mag(f, "K") >= 1.0 > mag(f, b)]
    sube = [(f["vol"], f["dt"], mag(f, "K"), mag(f, b), f["vrp_mirova"]) for f in prot if pub(f, "K") == 1 and pub(f, b) == 1 and mag(f, "K") < 1.0 <= mag(f, b)]
    R["P1b"][b] = {"baja": baja, "n_sube": len(sube), "sube": sube if b == "PM" else None}


def err(f, b):
    return (f["lab"] == "bajo1" and pub(f, b) == 0) or (f["lab"] == "neg_limpio" and pub(f, b) == 1)


def p2(b):
    sub = [f for f in ev if f["lab"] in ("bajo1", "neg_limpio")]
    s_k = sum(err(f, "K") for f in sub); s_b = sum(err(f, b) for f in sub)
    disc = [f for f in sub if err(f, "K") != err(f, b)]
    por_bloque = collections.Counter()
    for f in disc:
        por_bloque[bloque(f)] += 1 if err(f, b) else -1
    sumas = sorted(por_bloque.values()); neto = sum(sumas); B = len(sumas)
    # prueba de signos exacta propia (convolucion entera), por bloque
    dist = {0: 1}
    for s in sumas:
        nd = collections.Counter()
        for v, k in dist.items():
            nd[v + s] += k; nd[v - s] += k
        dist = nd
    den = 2 ** B
    k_gana = sum(k for v, k in dist.items() if v <= neto)
    return {"s_k": s_k, "s_b": s_b, "n_discordantes": len(disc), "neto": neto, "B": B, "sumas": sumas,
            "p_gana_exacta": k_gana / den, "k_gana": k_gana, "den_log2": B,
            "bloques_son_noche_volcan": True,
            "detalle_k_err": dict(collections.Counter((f["lab"], "K") for f in sub if err(f, "K"))),
            "detalle_b_err": dict(collections.Counter((f["lab"], b) for f in sub if err(f, b))),
            "discordantes_partida": sum(1 for f in disc if esperadas[(f["vol"], f["dt"])].get("partida")),
            "discordantes_hermana_sin_info": sum(1 for f in disc if "sin_info" in (esperadas[(f["vol"], f["dt"])].get("hermanos_lab") or [])),
            "lista_b_err": [(f["vol"], f["dt"], f["lab"], f["z"], mag(f, b)) for f in sub if err(f, b)]}


R["P2"] = {b: p2(b) for b in ("PM", "PM-geo5", "PM-sens", "K33", "PM-pixel", "PM-b21")}

D = cargar_d25()
pr = D.prueba_signos_p2(R["P2"]["PM"]["sumas"], R["P2"]["PM"]["neto"])
R["P2"]["PM"]["sellada"] = {"gana": pr["gana"], "metodo": pr["metodo"], "regla": D.regla_signos_p2(R["P2"]["PM"]["neto"], R["P2"]["PM"]["B"], pr)}


def pares_m(b):
    out = []
    for f in ev:
        if f["lab"] in ("protegida", "bajo1") and pub(f, "K") == 1 and pub(f, b) == 1:
            k, d, m = mag(f, "K"), mag(f, b), f.get("vrp_mirova")
            if k > 0 and d > 0 and m and m > 0:
                out.append({"k": k, "d": d, "m": m, "bloque": bloque(f), "vol": f["vol"], "z": f["z"], "dt": f["dt"],
                            "npix": f["port"]["fisica"].get("npix"), "id": f["id"], "d33": ((f.get("saturados") or {}).get("b22_nan_con_b21") or 0) > 0})
    return out


def m_propia(b, seed=7):
    P = pares_m(b)
    d = np.array([abs(math.log10(p["d"] / p["m"])) - abs(math.log10(p["k"] / p["m"])) for p in P])
    bl = [p["bloque"] for p in P]
    uniq = sorted(set(bl)); idxb = np.array([uniq.index(x) for x in bl])
    rng = np.random.default_rng(seed)
    meds = []
    for _ in range(4000):
        el = rng.integers(0, len(uniq), len(uniq))
        cnt = np.bincount(el, minlength=len(uniq))[idxb]
        w = np.repeat(d, cnt)
        meds.append(np.median(w))
    lo, hi = np.percentile(meds, 2.5), np.percentile(meds, 97.5)
    por_vol = collections.defaultdict(list)
    for p, x in zip(P, d):
        por_vol[p["vol"]].append(x)
    W = D.pesos_bloque(bl)
    regla, lo_s, hi_s = D.regla_m(list(d), W)
    return {"n": len(P), "bloques": len(uniq), "mediana_d": float(np.median(d)), "ic95_propio": [float(lo), float(hi)],
            "regla_propia": "MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO",
            "sellada": {"regla": regla, "ic95": [lo_s, hi_s]},
            "n_d_negativo": int((d < 0).sum()), "n_d_positivo": int((d > 0).sum()),
            "por_volcan": {v: {"n": len(x), "mediana": float(np.median(x)), "n_neg": int(sum(1 for y in x if y < 0))} for v, x in por_vol.items()},
            "mediana_razon_b": float(np.median([p["d"] / p["m"] for p in P])), "mediana_razon_k": float(np.median([p["k"] / p["m"] for p in P])),
            "npix_pares": dict(collections.Counter(p["npix"] for p in P)), "pares_d33": sum(p["d33"] for p in P),
            "labs": dict(collections.Counter("protegida" if any(f["dt"] == p["dt"] and f["vol"] == p["vol"] and f["lab"] == "protegida" for f in ev) else "bajo1" for p in P))}


R["M"] = {b: m_propia(b) for b in ("PM", "PM-geo5", "PM-sens", "K33", "PM-pixel")}

# placebo propio: K x 1,2 por node
cas = []
for f in ev:
    s = json.loads(json.dumps(slim(f["k_slim"])))
    for k in ("vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "f5_core_vrp_mw"):
        if isinstance(s.get(k), (int, float)): s[k] *= 1.2
    if isinstance(s.get("primary_cluster"), dict) and isinstance(s["primary_cluster"].get("vrp_mw"), (int, float)): s["primary_cluster"]["vrp_mw"] *= 1.2
    for p in s.get("anomaly_pixels") or []:
        if isinstance(p.get("vrp_mw"), (int, float)): p["vrp_mw"] *= 1.2
    cas.append([s, f["inner"]])
rp = []
for k in range(0, len(cas), 4000):
    rp += bp.correr_node(cas[k:k + 4000])
for f, p in zip(ev, rp):
    f["_t"]["placebo"] = (int(p[4]), float(p[3] or 0.0))
Pp = pares_m("placebo")
R["placebo"] = {"n": len(Pp), "pub_igual_K": sum(1 for f in ev if pub(f, "placebo") == pub(f, "K")), "n_ev": len(ev),
                "razon_min_max": [min(p["d"] / p["k"] for p in Pp), max(p["d"] / p["k"] for p in Pp)]}

# contador propio: PM con magnitud 0 deja de publicar; 50 negativos inyectados pasan a publicar
pubpm = [f for f in ev if pub(f, "PM") == 1]
cas = []
for f in pubpm:
    r = mi_record_port(f["port"]["fisica"], f["inner"], f["sensor"], grillas[f["vol"]])
    r["vrp_mw"] = 0.0; r["f5_core_vrp_mw"] = 0.0
    if r.get("primary_cluster"): r["primary_cluster"]["vrp_mw"] = 0.0
    cas.append([slim(r), f["inner"]])
a = bp.correr_node(cas)
negs = sorted([f for f in ev if f["lab"] == "neg_limpio" and pub(f, "PM") == 0], key=lambda f: (f["vol"], f["dt"]))
rng = np.random.default_rng(99)
sel = [negs[i] for i in rng.choice(len(negs), 50, replace=False)]
cas = [[slim({"sensor": f["sensor"], "vrp_mw": 0.3, "f5_core_vrp_mw": 0.3, "t_max_k": 350.0, "triggered_test1": False,
              "distance_class": "summit", "primary_cluster": {"vrp_mw": 0.3, "n_pixels": 1, "centroid_dist_km": 0.5}}), f["inner"]] for f in sel]
bb = bp.correr_node(cas)
R["contador"] = {"pm_publica": len(pubpm), "siguen_con_cero": sum(x[4] for x in a), "inyectados": len(sel), "pasan": sum(x[4] for x in bb),
                 "negativos_disponibles": len(negs)}

# ---------------------------------------------------------------- 5. Chillan
al = [f for f in ev if f["vol"] == "NevadosDeChillan" and f["lab"] in ("protegida", "bajo1")]
pares, emp, recup, solo_k, ninguno = [], [], [], [], []
for f in al:
    if pub(f, "K") == 1 and pub(f, "PM") == 1 and f.get("vrp_mirova"):
        dk, db = abs(math.log10(mag(f, "K") / f["vrp_mirova"])), abs(math.log10(mag(f, "PM") / f["vrp_mirova"]))
        (emp if dk == db else pares).append((f["dt"], f["z"], mag(f, "PM") / f["vrp_mirova"], mag(f, "K") / f["vrp_mirova"], db < dk, f["lab"]))
    elif pub(f, "K") == 0 and pub(f, "PM") == 1:
        recup.append((f["dt"], f["z"], mag(f, "PM") / f["vrp_mirova"] if f.get("vrp_mirova") else None, f["lab"], f["vrp_mirova"]))
    elif pub(f, "K") == 1 and pub(f, "PM") == 0:
        solo_k.append((f["dt"], f["lab"]))
    else:
        ninguno.append((f["dt"], f["lab"]))
n = len(pares); k = sum(1 for p in pares if p[4])
razb = [p[2] for p in pares]
R["chillan"] = {"n_alertas": len(al), "labs": dict(collections.Counter(f["lab"] for f in al)), "pares": pares, "empates": emp, "recuperadas": recup,
                "solo_k": solo_k, "ninguno": ninguno, "n": n, "a_favor": k,
                "p_una_cola": [sum(math.comb(n, i) for i in range(k, n + 1)), 2 ** n],
                "mediana": statistics.median(razb), "med_le30": statistics.median([p[2] for p in pares if p[1] <= 30]),
                "med_gt30": statistics.median([p[2] for p in pares if p[1] > 30]), "n_le30": sum(1 for p in pares if p[1] <= 30),
                "particion_estable_23_6_a_35_1": sorted(p[1] for p in pares)}

# ---------------------------------------------------------------- 6. caso P1b
caso = [f for f in ev if f["vol"] == "Lascar" and f["dt"] == "2026-04-25 07:35"]
if caso:
    f = caso[0]
    kb = (f.get("brazos") or {}).get("K") or {}
    R["p1b_caso"] = {"id": f["id"], "lab": f["lab"], "z": f["z"], "vrp_mirova": f["vrp_mirova"], "mag_K_node": mag(f, "K"), "pc_vrp_K": kb.get("pc_vrp"),
                     "k_slim_pc": (f["k_slim"] or {}).get("primary_cluster"), "k_slim_vrp_mw": (f["k_slim"] or {}).get("vrp_mw"),
                     "k_slim_f5": (f["k_slim"] or {}).get("f5_core_vrp_mw"),
                     "mag_PM_node": mag(f, "PM"), "port_vrp_crudo": f["port"]["fisica"]["vrp_mw"], "npix": f["port"]["fisica"]["npix"],
                     "pixeles": f["port"]["fisica"]["pixeles"], "vrp_banda": f["port"]["fisica"].get("vrp_banda"),
                     "geo5": f["port"]["fisica_geo5km"].get("vrp_mw"), "sens": f["port"]["sensible"].get("vrp_mw"), "pixel": f["port"]["pixel"].get("vrp_mw"),
                     "mag_geo5_node": mag(f, "PM-geo5"), "mag_sens_node": mag(f, "PM-sens"), "mag_pixel_node": mag(f, "PM-pixel"),
                     "pub_guardada": esperadas[(f["vol"], f["dt"])]["pub_guardada"], "pc_vrp_guardada": esperadas[(f["vol"], f["dt"])]["pc_vrp_guardada"],
                     "codigo_sha": esperadas[(f["vol"], f["dt"])]["codigo_sha"], "saturados": f.get("saturados"), "crater": f.get("crater_mxd03"),
                     "k_difiere_de_guardado": f.get("k_difiere_de_guardado")}
    # cuantas protegidas de K quedan a menos de 0,05 MW de 1 MW en K o en PM (sensibilidad al corte)
    R["p1b_sensibilidad"] = {"K_en_0.95_1.05": [(x["vol"], x["dt"], mag(x, "K"), mag(x, "PM")) for x in prot if pub(x, "K") == 1 and 0.95 <= mag(x, "K") < 1.05],
                             "PM_en_0.95_1.05": [(x["vol"], x["dt"], mag(x, "K"), mag(x, "PM")) for x in prot if pub(x, "PM") == 1 and 0.95 <= mag(x, "PM") < 1.05]}

# ---------------------------------------------------------------- 7. informativos
R["d33"] = {"n_pasadas": sum(1 for f in ev if ((f.get("saturados") or {}).get("b22_nan_con_b21") or 0) > 0),
            "lista": [(f["vol"], f["dt"], f["lab"], f["saturados"], pub(f, "K"), pub(f, "PM")) for f in ev if ((f.get("saturados") or {}).get("b22_nan_con_b21") or 0) > 0]}
R["dayflag"] = {"ev": dict(collections.Counter(str(f.get("dayflag")) for f in ev)), "s1_estados": dict(collections.Counter(str((f.get("s1") or {}).get("estado")) for f in ev)),
                "diurnas": [(f["vol"], f["dt"], f["lab"], f.get("dayflag"), (f.get("geometria_centro") or {}).get("solar_zenith")) for f in ev if (f.get("s1") or {}).get("estado") == "diurna"]}
R["k33"] = {"igual_k": dict(collections.Counter(bool(f.get("k33_igual_k")) for f in ev)), "pub_distinta": sum(1 for f in ev if pub(f, "K33") != pub(f, "K")),
            "mag_distinta_en_pub": sum(1 for f in ev if pub(f, "K") == 1 and pub(f, "K33") == 1 and abs(mag(f, "K") - mag(f, "K33")) > 1e-9)}
R["k_difiere_de_guardado"] = dict(collections.Counter(str(f.get("k_difiere_de_guardado")) for f in rec))
R["partida"] = {"n_pob": sum(1 for f in esperadas.values() if f.get("partida")), "n_ev": sum(1 for f in ev if esperadas[(f["vol"], f["dt"])].get("partida"))}
# curva de cenit propia
cz = collections.defaultdict(list)
for f in ev:
    if f["lab"] in ("protegida", "bajo1") and pub(f, "PM") == 1 and f.get("vrp_mirova"):
        cz[int(f["z"] // 10) * 10].append(mag(f, "PM") / f["vrp_mirova"])
R["curva_cenit_PM"] = {k: (len(v), float(np.median(v))) for k, v in sorted(cz.items())}
# soporte propio no se recalcula (necesita los records de VIIRS); se deja al evaluador
# costura
R["costura"] = dict(collections.Counter(("costura" if (f.get("crater_mxd03") or {}).get("costura") else "interior", pub(f, "K"), pub(f, "PM")) for f in ev if f["lab"] in ("protegida", "bajo1")))
R["costura"] = {"%s|K%d|PM%d" % k: v for k, v in R["costura"].items()}

for f in ev:
    f.pop("_t", None)
def _claves(x):
    if isinstance(x, dict): return {("|".join(map(str, k)) if isinstance(k, tuple) else k): _claves(v) for k, v in x.items()}
    if isinstance(x, list): return [_claves(v) for v in x]
    return x
R = _claves(R)
OUT.joinpath("verificar_salida.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: v for k, v in R.items() if k not in ("P2",)}, ensure_ascii=False, indent=1, default=str)[:30000])
print("P2 PM:", {k: v for k, v in R["P2"]["PM"].items() if k not in ("lista_b_err", "sumas")})
print("P2 PM lista_b_err:", R["P2"]["PM"]["lista_b_err"])
for b in ("PM-geo5", "PM-sens", "K33", "PM-pixel", "PM-b21"):
    print("P2", b, {k: v for k, v in R["P2"][b].items() if k not in ("lista_b_err", "sumas", "detalle_k_err")})
