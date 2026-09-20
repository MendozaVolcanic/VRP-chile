# -*- coding: utf-8 -*-
"""I-04. Controles que la vara no trae: plataforma en los segundos, poder del recall por noche,
coherencia entre los dos canales del scraper, piso de redondeo de MIROVA, cola tras el ultimo OCR.

P1 (si lo medido estuviera roto, fallaria?): cada bloque tiene su contraejemplo posible y lo cuenta
    (pareos con plataforma cruzada, pares CONS=RUTINA con OCR=ALERTA, VRP distintos entre canales).
P2 (instrumento muerto?): el recall por noche se compara contra 200 barajados de `pub`; si el
    barajado da lo mismo que lo real, el numero no discrimina.
"""
import sys, io, json, csv, collections, random
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
ROOT = A.parents[2]
sys.path.insert(0, str(A))
import importlib.util
spec = importlib.util.spec_from_file_location("s", A / "i03_sensibilidad.py")
# no importamos i03 (imprime todo); recargamos caches aqui
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
for r in RECS:
    r["t"] = datetime.fromisoformat(r["dt"]).replace(tzinfo=None)
for f in REF:
    f["t"] = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S")
C = collections.Counter

print("== 1. Los SEGUNDOS de la hora de MIROVA contra NUESTRA plataforma (pareo exacto al minuto)")
idx = {}
for r in RECS:
    idx[(r["vol"], r["b"], r["t"].strftime("%Y-%m-%d %H:%M"))] = r
tab = C()
for f in REF:
    r = idx.get((f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]))
    tab[(f["source"], f["fecha_utc"][17:19], r["sensor"] if r else "SIN RECORD")] += 1
for k in sorted(tab):
    print("  ", k, tab[k])

print("\n== 2. Poder del 'recall por noche': real contra `pub` barajado dentro de cada volcan y sensor (200 veces)")


def etiquetas():
    ref_idx = collections.defaultdict(list)
    for f in REF:
        ref_idx[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)
    labs = []
    for r in RECS:
        filas = ref_idx.get((r["vol"], r["b"], r["t"].strftime("%Y-%m-%d %H:%M")), [])
        labs.append("pos" if any(f["tipo"].startswith("ALERTA") for f in filas) else "otro")
    return labs


LABS = etiquetas()


def recall_noche(pubs, solo_b=None):
    noches = collections.defaultdict(lambda: [False, 0])
    for r, l, p in zip(RECS, LABS, pubs):
        if solo_b and r["b"] != solo_b:
            continue
        e = noches[(r["vol"], r["t"].strftime("%Y-%m-%d"))]
        e[0] |= l == "pos"
        e[1] = max(e[1], p)
    pos = [e for e in noches.values() if e[0]]
    return sum(e[1] for e in pos), len(pos)


real = [r["pub"] for r in RECS]
print("  real, cualquier sensor:", recall_noche(real), "| solo V375:", recall_noche(real, "VIIRS375"), "| solo V750:", recall_noche(real, "VIIRS750"))
rng = random.Random(146)
grupos = collections.defaultdict(list)
for i, r in enumerate(RECS):
    grupos[(r["vol"], r["b"])].append(i)
res = []
for _ in range(200):
    pubs = real[:]
    for ii in grupos.values():
        p = [real[i] for i in ii]
        rng.shuffle(p)
        for i, v in zip(ii, p):
            pubs[i] = v
    res.append(recall_noche(pubs)[0])
res.sort()
print(f"  barajado: noches detectadas de 78 -> min {res[0]} p05 {res[10]} mediana {res[100]} max {res[-1]}")
tot = C()
for r in RECS:
    tot[r["b"]] += 1
    tot[r["b"] + "_pub"] += r["pub"]
print("  tasa de publicacion sobre TODAS las pasadas nocturnas:", {b: f"{tot[b + '_pub']}/{tot[b]} = {100 * tot[b + '_pub'] / tot[b]:.1f}%" for b in ("MODIS", "VIIRS375", "VIIRS750")})
nn = collections.defaultdict(int)
for r in RECS:
    nn[(r["vol"], r["t"].strftime("%Y-%m-%d"))] = max(nn[(r["vol"], r["t"].strftime("%Y-%m-%d"))], r["pub"])
print(f"  noches de volcan en que publicamos algo: {sum(nn.values())} de {len(nn)}")

print("\n== 3. Coherencia entre los dos canales del scraper (tabla latest.php contra imagen por volcan), TODA la historia")
DL = ROOT / "experiments/_s145_paridad/_dl_referencia"
cons = {(r["timestamp"], r["Volcan"], r["Sensor"]): r for r in csv.DictReader(open(DL / "registro_vrp_consolidado.csv", encoding="utf-8"))}
ocr = list(csv.DictReader(open(DL / "registro_vrp_ocr.csv", encoding="utf-8")))
par = C()
dif = []
for o in ocr:
    c = cons.get((o["timestamp"], o["Volcan"], o["Sensor"]))
    par[(o["Tipo_Registro"], c["Tipo_Registro"] if c else "SIN FILA EN TABLA")] += 1
    if c and c["Tipo_Registro"] != "RUTINA":
        dif.append(abs(float(o["VRP_MW"]) - float(c["VRP_MW"])))
for k in sorted(par):
    print("  ", k, par[k])
dif.sort()
print(f"  |VRP imagen - VRP tabla| en los pares con ambos > 0: n {len(dif)} iguales (<=0.005) {sum(1 for d in dif if d <= 0.005)} p90 {dif[int(.9 * (len(dif) - 1))]:.3f} max {dif[-1]:.3f}")

print("\n== 4. Piso de MIROVA: VRP de las ALERTAS V375 en toda la historia (tabla + imagen), y nuestras magnitudes en negativos")
v = sorted(float(r["VRP_MW"]) for r in list(cons.values()) + ocr if r["Sensor"] == "VIIRS375" and r["Tipo_Registro"].startswith("ALERTA"))
print(f"  n {len(v)} min {v[0]} | <0.02: {sum(1 for x in v if x < 0.02)} | <0.05: {sum(1 for x in v if x < 0.05)} | <0.10: {sum(1 for x in v if x < 0.10)}")
print("  valores mas chicos y cuantas veces:", C(v).most_common()[:0] or sorted(C(x for x in v if x < 0.06).items()))
dec = C(len(r["VRP_MW"].split(".")[-1]) for r in cons.values() if r["Sensor"] == "VIIRS375" and float(r["VRP_MW"]) > 0)
print("  decimales con que la tabla entrega el VRP V375:", dict(dec))

print("\n== 5. Cola posterior a la ultima fila del canal de imagen")
ult_ocr = max(f["t"] for f in REF if f["source"] == "OCR")
ult_cons = max(f["t"] for f in REF if f["source"] == "CONS")
print("  ultima fila imagen:", ult_ocr, "| ultima fila tabla:", ult_cons, "| ultima pasada nuestra:", max(r["t"] for r in RECS))
ref_idx = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]) for f in REF if f["tipo"] == "RUTINA"}
cola = [r for r in RECS if r["t"] > ult_ocr and (r["vol"], r["b"], r["t"].strftime("%Y-%m-%d %H:%M")) in ref_idx]
print(f"  pasadas nuestras con RUTINA posteriores a la ultima fila de imagen: {len(cola)} (V375: {sum(1 for r in cola if r['b'] == 'VIIRS375')}, de ellas publican {sum(r['pub'] for r in cola if r['b'] == 'VIIRS375')})")
print(f"  pasadas nuestras posteriores a la ultima fila de la TABLA (sin_info por construccion): {sum(1 for r in RECS if r['t'] > ult_cons)}")

print("\n== 6. El predicado binario 'publica' contra su forma reducida (cumulo summit con energia dentro del inner)")
inner = {"Lascar": 5, "Lastarria": 3, "Isluga": 5, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5, "Copahue": 4, "PuyehueCordonCaulle": 20, "Chaiten": 5}
dis = C()
for r in RECS:
    red = int(r["dc"] == "summit" and (r["pc_vrp"] or 0) > 0 and (r["pc_dist"] is None or r["pc_dist"] <= inner[r["vol"]]))
    dis[(r["b"], r["pub"], red)] += 1
print("  (sensor, pub del node, forma reducida):", dict(sorted(dis.items())))
print("  V375 con f5_core_vrp_mw persistido:", sum(1 for r in RECS if r["b"] == "VIIRS375" and r["f5"] is not None), "de", sum(1 for r in RECS if r["b"] == "VIIRS375"))
