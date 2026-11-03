# -*- coding: utf-8 -*-
"""Verificador limpio V750-B (2026-11-03): re-agregación independiente de la lectura.

Reutiliza del analizador sellado SOLO las piezas de instrumento (record_cumulo, slim, caja_de, partida, el predicado
del tablero con node y la prueba de signos del evaluador), y rehace por su cuenta: la unión de los dos runs, la
cobertura, las etiquetas, P1 (que veta / todas / N-3), E, P2 por bloque, la regla §6, los controles y los informes
aparte (sensibles a la triangulación con nombre, cenit 30, Tupungatito).
Corre desde el árbol de lectura: cd D:/vrp-trabajo/temporales/v750b_r4_20261103/arbol
"""
import collections
import copy
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "experiments/_s162_v750b")
import analizar_v750b as A  # noqa: E402

R4 = Path("D:/vrp-trabajo/temporales/v750b_r4_20261103")
OBJ = Path("experiments/_s162_v750b/objetivos_v750b.json")
EV = "D:/vrp-trabajo/temporales/evaluar_d25_s161.py"
CENSO_ART = "D:/vrp-trabajo/temporales/s159_oraculo/censo_39713438252"
CENSO_OBJ = R4 / "objetivos_censo_s159.json"
out = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    out.append(s)


obj = {o["id"]: o for o in json.loads(OBJ.read_text(encoding="utf-8"))}
pr("objetivos:", len(obj))

# ---- unión propia de los dos runs (sin usar A.cargar)
primero, relanz = {}, {}
for f in sorted((R4 / "art_41615021658").rglob("resultados_*.json")):
    for r in json.load(open(f, encoding="utf-8")):
        assert r["id"] not in primero
        primero[r["id"]] = r
for f in sorted((R4 / "art_41693265163").rglob("resultados_*.json")):
    for r in json.load(open(f, encoding="utf-8")):
        assert r["id"] not in relanz
        relanz[r["id"]] = r
pr("primer run ids", len(primero), "| relanzamiento ids", len(relanz), "| relanz subconjunto del primero:", set(relanz) <= set(primero))
res = {}
for i, r in primero.items():
    if i >= 100000:
        continue
    rr = relanz.get(i)
    if rr is not None and rr.get("estado") == "ok":
        res[i] = rr
    else:
        res[i] = r
pr("sellados con resultado:", len(res), "| faltan de la lista:", sorted(set(obj) - set(res)), "| sobran:", len(set(res) - set(obj)))
# errores que quedaron
err = [i for i in obj if res[i].get("estado") not in ("ok", "volcan_fuera_del_granulo")]
pr("ids con estado ni ok ni fuera tras la unión:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"], obj[i].get("protegida"), res[i]["estado"][:40], relanz.get(i, {}).get("estado")) for i in err])
# los del mismo gránulo que 1884 en el relanzamiento
g1884 = obj[1884]["granule"]
mismos = [(i, obj[i]["volcan"], relanz[i]["estado"][:30]) for i in relanz if obj.get(i, {}).get("granule") == g1884]
pr("gránulo de 1884:", g1884, "| otros ids del mismo gránulo en el relanzamiento:", mismos)
pr("1884 en el primer run:", primero[1884]["estado"][:60])
# comparación con A.cargar sobre sep/sellado
res_a = A.cargar([str(p) for p in sorted((R4 / "sep/sellado").glob("*"))])
dif = [i for i in obj if (res[i].get("estado"), json.dumps(res[i].get("oraculo"), sort_keys=True)) != (res_a[i].get("estado"), json.dumps(res_a[i].get("oraculo"), sort_keys=True))]
pr("ids donde mi unión difiere de A.cargar(sep/sellado):", dif)

# ---- cobertura
part = {i: A.partida(res[i]) for i in obj}
sin = [i for i in obj if part[i] is None or (part[i] == "observada" and res[i].get("dayflag") != 0)]
no_obs = collections.Counter(part[i] for i in obj if part[i] in ("fuera", "sin_crater"))
oks = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") == 0 and set(A.CAJAS) <= set(res[i].get("oraculo") or {})]
den = len(obj) - no_obs["fuera"] - no_obs["sin_crater"]
pr(f"cobertura: observadas {len(oks)} | no observadas {dict(no_obs)} | SIN DATO {len(sin)} {[(i, obj[i]['volcan'], obj[i]['hora_utc'], obj[i]['lab']) for i in sin]} | denominador {den} | fracción {len(sin)/den:.5f} | protegidas SIN DATO {[i for i in sin if obj[i].get('protegida')]}")
sg = json.loads(Path("experiments/_s162_v750b/sin_granulo_v750b.json").read_text(encoding="utf-8"))
import hashlib
pr("sin_granulo: pasadas", len(sg.get("pasadas", [])), "| sha atado ok:", sg.get("objetivos_sha256") == hashlib.sha256(OBJ.read_bytes()).hexdigest())
obs_dia = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") != 0]
pr("observadas con dayflag != 0 (cuentan SIN DATO):", len(obs_dia))
sin_cajas = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") == 0 and not set(A.CAJAS) <= set(res[i].get("oraculo") or {})]
pr("observadas nocturnas sin las 5 cajas (hueco de la adenda 1):", len(sin_cajas))
# vrp_banda presente?
nb = collections.Counter()
for i in oks:
    for c in A.CAJAS:
        x = res[i]["oraculo"][c]
        nb[("npix>0" if x.get("npix") else "npix=0", "banda" if x.get("vrp_banda") else "sin banda")] += 1
pr("vrp_banda por caja:", dict(nb))

inner = A.B.inner_desde_html()
pr("inner por volcán:", inner)

# ---- predicado del tablero (node): K, cajas base/min/max, cajas con ancla en el centro
casos, idx = [], []
for i in oks:
    o, r, inn = obj[i], res[i], inner[obj[i]["volcan"]]
    anc = tuple(o.get("pos_crater") or (A.C, A.C))
    casos.append([A.slim((r.get("brazos") or {}).get("K", {}).get("record")), inn]); idx.append((i, "K", "base"))
    for c in A.CAJAS:
        x = r["oraculo"][c]
        casos.append([A.record_cumulo(x, inn, o["sensor"], anc), inn]); idx.append((i, c, "base"))
        casos.append([A.record_cumulo(x, inn, o["sensor"]), inn]); idx.append((i, c, "centro"))
        banda = x.get("vrp_banda") if x.get("npix") else None
        for var, k in (("min", 0), ("max", 1)):
            xx = copy.deepcopy(x)
            if banda:
                xx["vrp_mw"] = banda[k]
            casos.append([A.record_cumulo(xx, inn, o["sensor"], anc), inn]); idx.append((i, c, var))
pr("casos para node:", len(casos))
P = {k: bool(p[4]) for k, p in zip(idx, A.B.correr_node(casos))}


def caja(b, i):
    return A.caja_de(b, obj[i]["volcan"])


def pub(i, b, var="base"):
    return P[(i, "K", "base")] if b == "K" else P[(i, caja(b, i), var)]


def vrp(i, b):
    if b == "K":
        rec = (res[i].get("brazos") or {}).get("K", {}).get("record") or {}
        return (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0
    return res[i]["oraculo"][caja(b, i)].get("vrp_mw") or 0.0


# ---- controles
camb = collections.Counter((c, obj[i]["volcan"]) for i in oks for c in A.CAJAS if P[(i, c, "base")] != P[(i, c, "centro")])
pr("cráter vs centro (cambian):", dict(sorted(camb.items())))
n_pub = sum(1 for i in oks for c in A.CAJAS if P[(i, c, "base")])
neg_no = [i for i in oks if obj[i]["lab"] == "neg_limpio" and not P[(i, "B0", "base")]]
pr(f"publicadas (caja x pasada) {n_pub} -> perturbaciones esperadas {2*n_pub} + inyecciones {min(50, len(neg_no))} = {2*n_pub + min(50, len(neg_no))}")
# nulo propio: las publicadas con VRP 0 y con far
nulo, nidx = [], []
for i in oks:
    for c in A.CAJAS:
        if P[(i, c, "base")]:
            base = A.record_cumulo(res[i]["oraculo"][c], inner[obj[i]["volcan"]], obj[i]["sensor"], tuple(obj[i].get("pos_crater") or (A.C, A.C)))
            a0 = copy.deepcopy(base); a0["primary_cluster"]["vrp_mw"] = 0.0; a0["vrp_mw"] = 0.0
            b0 = copy.deepcopy(base); b0["distance_class"] = "far"
            nulo += [[a0, inner[obj[i]["volcan"]]], [b0, inner[obj[i]["volcan"]]]]; nidx += ["vrp0", "far"]
NP = [bool(p[4]) for p in A.B.correr_node(nulo)]
pr("nulo propio: siguen publicando tras VRP 0:", sum(1 for t, p in zip(nidx, NP) if t == "vrp0" and p), "| tras far:", sum(1 for t, p in zip(nidx, NP) if t == "far" and p), "| de", len(nidx))
# ¿un record far con VRP > 0 a distancia < inner publica? (el predicado mira distance_class o la distancia?)
k_dist = sorted({i for i in oks if bool(obj[i].get("pub_prod")) != pub(i, "K")} | {i for i in oks if abs(vrp(i, "K") - (obj[i].get("pc_vrp") or 0)) > 0.001})
pr("K = producción: distintas", len(k_dist), "| pub_prod True entre oks:", sum(1 for i in oks if obj[i].get("pub_prod")), "| K publica:", sum(1 for i in oks if pub(i, "K")))
oks = [i for i in oks if i not in set(k_dist)]
# censo
cobj = {(o["volcan"], o["hora_utc"]): o["id"] for o in json.loads(CENSO_OBJ.read_text(encoding="utf-8"))}
cres = A.cargar([CENSO_ART])
cnt = collections.Counter()
for i in oks:
    j = cobj.get((obj[i]["volcan"], obj[i]["hora_utc"]))
    rc = cres.get(j) if j is not None else None
    if not rc or rc.get("estado") != "ok":
        cnt["sin_par_o_no_ok"] += 1
        continue
    for c, ref in (("B0", "geo_linear"), ("B1", "geo_linear_anillo_sensible")):
        x, y = res[i]["oraculo"][c], (rc.get("oraculo") or {}).get(ref) or {}
        igual = (x.get("npix") == y.get("npix") and abs((x.get("vrp_mw") or 0) - (y.get("vrp_mw") or 0)) < 1e-6
                 and sorted((p[0], p[1]) for p in x.get("pixeles") or []) == sorted((p[0], p[1]) for p in y.get("pixeles") or []))
        cnt[f"{c}_{'igual' if igual else 'DISTINTO'}"] += 1
        if x.get("npix"):
            cnt[f"{c}_con_pixeles"] += 1
pr("censo S159: objetivos del censo", len(cobj), "| resultados del censo", len(cres), "|", dict(cnt))

# ---- etiquetas
def prot_tabla(o):
    return any(A.alerta_protegida(f) for f in o.get("mirova") or [] if f.get("source") == "CONS")


def etiqueta(o, canal):
    if canal == "decide":
        canal = "tabla" if o["hora_utc"] < A.FRONTERA_OCR else "todo"
    if o["lab"] == "neg_limpio":
        return "neg"
    if o["lab"] != "pos" or not o.get("decide"):
        return None
    if canal == "tabla" and not o.get("alerta_tabla"):
        return None
    return "prot" if (prot_tabla(o) if canal == "tabla" else o.get("protegida")) else "baja"


def n3(o):
    return bool(o.get("protegida")) and not o.get("alerta_tabla") and o.get("sensor") == "VIIRS_SNPP_750" and o["hora_utc"][:10] < "2026-10-09"


def ventana(o, v):
    h = o["hora_utc"]
    return v == "TO" or (v == "T" and h < A.FRONTERA_OCR) or (v == "O" and h >= A.FRONTERA_OCR)


EVm = A.cargar_signos(EV)
n3_lista = [i for i in oks if n3(obj[i]) and etiqueta(obj[i], "todo") == "prot"]
pr("N-3 observadas:", [(obj[i]["volcan"], obj[i]["hora_utc"], [b for b in A.CANDIDATOS if pub(i, b)]) for i in n3_lista])
pr("N-3 en la lista completa de objetivos (sin filtrar por observada):", [(obj[i]["volcan"], obj[i]["hora_utc"]) for i in obj if n3(obj[i]) and obj[i].get("decide") and obj[i]["lab"] == "pos"])

ver = {}
for canal in ("decide", "tabla"):
    for v in ("T", "O", "TO"):
        for b in A.BRAZOS:
            m = collections.Counter()
            for i in oks:
                o = obj[i]; e = etiqueta(o, canal)
                if e is None or not ventana(o, v):
                    continue
                pb = pub(i, b)
                if e == "prot" and not pb:
                    m["P1_todas"] += 1
                    m["P1_n3" if n3(o) else "P1"] += 1
                if e == "baja" and not pb:
                    m["E"] += 1
                if e == "neg" and pb:
                    m["E"] += 1
            reg, neto, nb_ = None, 0, 0
            if b not in ("K", "B1"):
                sumas = collections.defaultdict(int)
                for i in oks:
                    o = obj[i]; e = etiqueta(o, canal)
                    if e not in ("baja", "neg") or not ventana(o, v):
                        continue
                    err_ = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))
                    c = err_(b) - err_("B1")
                    if c:
                        sumas[(o["hora_utc"][:10], o["volcan"])] += c
                s = [sumas[k] for k in sorted(sumas)]
                neto, nb_ = sum(s), len(s)
                prr = EVm.prueba_signos_p2(s, neto)
                reg = EVm.regla_signos_p2(neto, nb_, prr)
            ver[(b, v, canal)] = (m["P1"], m["P1_todas"], m["P1_n3"], m["E"], reg, neto, nb_)
            pr(f"   {v} {canal} {b}: P1 veta {m['P1']} todas {m['P1_todas']} n3 {m['P1_n3']} | E {m['E']} | P2 {reg} neto {neto} bloques {nb_}")

# ---- regla §6 a mano, con la definición del texto
eleg = [b for b in A.CANDIDATOS if ver[(b, "TO", "decide")][0] == 0 and ver[(b, "O", "tabla")][0] == 0]
eleg_todas = [b for b in A.CANDIDATOS if ver[(b, "TO", "decide")][1] == 0 and ver[(b, "O", "tabla")][1] == 0]
pr("elegibles (P1 que veta = 0):", eleg, "| contando N-3:", eleg_todas)


def no_peor(b, canal):
    reg, neto = ver[(b, "TO", canal)][4], ver[(b, "TO", canal)][5]
    return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO" and neto <= 0)


ganan = [b for b in eleg if b != "B1" and ver[(b, "TO", "decide")][4] == "GANA" and no_peor(b, "tabla")]
pr("ganan (§6.2):", ganan)
pr("estado de cada elegible contra B1 (decide / tabla):", {b: (ver[(b, 'TO', 'decide')][4], ver[(b, 'TO', 'decide')][5], ver[(b, 'TO', 'tabla')][4], ver[(b, 'TO', 'tabla')][5]) for b in eleg if b != "B1"})
cand = [b for b in ("B4", "B2", "B5", "B1", "B3") if b in eleg and (b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]
pr("§6.3 candidatos en orden de cercanía:", cand, "-> ROI:", cand[0] if cand else None)
# control negativo y positivo propios
sumas = collections.defaultdict(int)
for i in oks:
    o = obj[i]
    if o["volcan"] not in A.VOL_SENS:
        continue
    e = etiqueta(o, "decide")
    if e in ("baja", "neg"):
        err_ = lambda x: int((e == "baja" and not pub(i, x)) or (e == "neg" and pub(i, x)))
        c = err_("B4") - err_("B1")
        if c:
            sumas[(o["hora_utc"][:10], o["volcan"])] += c
pr("control negativo propio: bloques", len(sumas), "| B4 y B1 usan la misma caja en VOL_SENS:", all(caja("B4", i) == "B1" for i in oks if obj[i]["volcan"] in A.VOL_SENS))
pcc = [i for i in oks if obj[i]["volcan"] == "PuyehueCordonCaulle" and etiqueta(obj[i], "decide") == "prot" and not pub(i, "B0")]
pr("control positivo propio: B0 pierde en PCC", len(pcc), "| B1 publica de esas", sum(1 for i in pcc if pub(i, "B1")), "| protegidas PCC total", sum(1 for i in oks if obj[i]["volcan"] == "PuyehueCordonCaulle" and etiqueta(obj[i], "decide") == "prot"))

# ---- informes aparte
pr("\n== sensibles a la triangulación (pub min != pub max), canal decide, por caja")
sens = collections.defaultdict(list)
for i in oks:
    e = etiqueta(obj[i], "decide")
    if e is None:
        continue
    for c in A.CAJAS:
        if P[(i, c, "min")] != P[(i, c, "max")]:
            x = res[i]["oraculo"][c]
            sens[c].append((obj[i]["volcan"], obj[i]["hora_utc"], e, x.get("vrp_mw"), x.get("vrp_banda"), P[(i, c, "base")], P[(i, c, "min")], P[(i, c, "max")]))
for c in A.CAJAS:
    pr(f"   {c}: {sens[c]}")
# ¿alguna sensible en una protegida o en un bloque que decide P2 de B4 contra B1?
sens_ids = {i for i in oks for c in A.CAJAS if P[(i, c, "min")] != P[(i, c, "max")]}
for i in sens_ids:
    pr("   sensible:", obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["lab"], etiqueta(obj[i], "decide"), {b: (pub(i, b, "min"), pub(i, b, "base"), pub(i, b, "max")) for b in A.CANDIDATOS})
# cenit 30
pr("\n== cenit < 30 y >= 30 (decide, TO)")
for b in A.BRAZOS:
    lin = []
    for nom, f in (("z<30", lambda z: z is not None and z < 30), ("z>=30", lambda z: z is not None and z >= 30)):
        m = collections.Counter(); rz = []
        for i in oks:
            if not f(obj[i].get("z")):
                continue
            e = etiqueta(obj[i], "decide")
            if e is None:
                continue
            pb = pub(i, b)
            m["n_" + e] += 1
            m["P1"] += e == "prot" and not pb
            m["E"] += (e == "baja" and not pb) or (e == "neg" and pb)
            if e in ("prot", "baja") and pb and obj[i].get("mirova_vrp"):
                rz.append(vrp(i, b) / obj[i]["mirova_vrp"])
        lin.append(f"{nom}: prot {m['n_prot']} P1 {m['P1']} E {m['E']} (baja {m['n_baja']} neg {m['n_neg']}) razón {statistics.median(rz):.3f} n={len(rz)}" if rz else f"{nom}: -")
    pr(f"   {b}: " + " || ".join(lin))
pr("sin cenit:", sum(1 for i in oks if obj[i].get("z") is None))
# Tupungatito
for canal in ("decide", "tabla"):
    lin = []
    for b in A.BRAZOS:
        al = [i for i in oks if obj[i]["volcan"] == "Tupungatito" and etiqueta(obj[i], canal) in ("prot", "baja")]
        lin.append(f"{b} {sum(pub(i, b) for i in al)}/{len(al)}")
    pr(f"Tupungatito {canal}: " + " | ".join(lin))
# razón descriptiva
for b in A.BRAZOS:
    rz = sorted(vrp(i, b) / obj[i]["mirova_vrp"] for i in oks if etiqueta(obj[i], "decide") in ("prot", "baja") and pub(i, b) and obj[i].get("mirova_vrp"))
    pr(f"razón {b}: {statistics.median(rz):.3f} n={len(rz)}")
(R4 / "verif/reagregar_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
