# -*- coding: utf-8 -*-
"""F2 M3. Etiquetador INDEPENDIENTE (escrito desde cero sobre los CSV congelados, sin banco_paridad) para las
pasadas V375 de las tablas abril-agosto: (a) distribucion de etiquetas y desfase temporal al vecino mas
cercano de la referencia; (b) cuantas pasadas cambiarian de etiqueta con tolerancia 2, 5 y 10 min.
Pregunta 1: si el pareo de +-2 min estuviera roto (desfase sistematico), el histograma de desfases lo mostraria
y la etiqueta cambiaria al ampliar la tolerancia. Pregunta 2: control positivo, con +-2 min mi etiquetador
debe coincidir casi siempre con el de banco_paridad (si da 0 coincidencias, el instrumento esta muerto).
No filtra pasadas diurnas (las tablas ya traen solo las nocturnas); la referencia se filtra por hora UTC 00-12
como aproximacion nocturna, declarado."""
import csv, json, sys, io, collections, bisect
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_prereg_invierno\_congelado"
ALIAS = {"PlanchonPeteroa": "PlanchonPeteroa", "Planchon-Peteroa": "PlanchonPeteroa", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Nevados de Chillan": "NevadosDeChillan", "Cordon Caulle": "PuyehueCordonCaulle"}
def nv(x): x = x.strip(); return ALIAS.get(x, x.replace(" ", ""))
def bk(s):
    s = s.upper()
    if "MODIS" in s: return "MODIS"
    if "375" in s: return "VIIRS375"
    if "VIIRS" in s: return "VIIRS750"
    return None
def leer(mes):
    ref = collections.defaultdict(list)
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        for r in csv.DictReader(open("%s\%s\%s" % (RAIZ, mes, nombre), encoding="utf-8")):
            t = (r.get("Fecha_Satelite_UTC") or "")[:19]
            if len(t) < 16: continue
            try: dt = datetime.strptime(t[:16], "%Y-%m-%d %H:%M")
            except ValueError: continue
            if not (0 <= dt.hour <= 12): continue
            b = bk(r.get("Sensor", ""))
            if b is None: continue
            try: vrp = float(r.get("VRP_MW") or 0)
            except ValueError: vrp = 0
            ref[(nv(r["Volcan"]), b)].append((dt, src, r.get("Tipo_Registro", ""), vrp))
    for v in ref.values(): v.sort()
    return ref
def etiqueta(filas, ns):
    if any(t.startswith("ALERTA") for _, s, t, _ in filas): return "pos"
    if any(t.startswith("FALSO") for _, s, t, _ in filas): return "far_ref"
    if any(s == "CONS" and t == "RUTINA" and v == 0 for _, s, t, v in filas) and not ns: return "neg_limpio"
    return "sin_info"
T = sys.argv[1]
tot = collections.Counter(); desf = collections.Counter(); cambia = collections.Counter(); coincide = collections.Counter()
for mes in ("abril", "mayo", "junio", "julio", "agosto"):
    ref = leer(mes)
    noche = collections.defaultdict(bool)
    for (vol, b), L in ref.items():
        for dt, s, t, v in L:
            if t.startswith("ALERTA") or t.startswith("FALSO"): noche[(vol, b, dt.strftime("%Y-%m-%d"))] = True
    tab = json.load(open("%s/%s/tabla.json" % (T, mes), encoding="utf-8"))["pasadas"]
    for k, v in tab.items():
        vol, b, d = k.split("|")
        if b != "VIIRS375" or "control" not in v: continue
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M"); L = ref.get((vol, b), []); ts = [x[0] for x in L]
        i = bisect.bisect_left(ts, dt)
        cand = [abs((ts[j] - dt).total_seconds()) for j in (i - 1, i) if 0 <= j < len(ts)]
        m = min(cand) if cand else 1e9
        desf["<=2min" if m <= 120 else "2-5min" if m <= 300 else "5-10min" if m <= 600 else ">10min"] += 1
        labs = {}
        for tol in (120, 300, 600):
            fil = [x for x in L if abs((x[0] - dt).total_seconds()) <= tol]
            labs[tol] = etiqueta(fil, noche[(vol, b, d[:10])])
        tot[labs[120]] += 1
        coincide["igual" if labs[120] == v["control"]["lab"] else "distinta:%s->%s" % (v["control"]["lab"], labs[120])] += 1
        if labs[300] != labs[120]: cambia["120->300 %s->%s" % (labs[120], labs[300])] += 1
        if labs[600] != labs[120]: cambia["120->600 %s->%s" % (labs[120], labs[600])] += 1
print("pasadas V375 (control), abril-agosto:", sum(tot.values()))
print("mis etiquetas +-2 min:", dict(tot))
print("coincidencia con banco_paridad:", dict(coincide.most_common()))
print("desfase al vecino mas cercano de la referencia:", dict(desf))
print("cambios al ampliar la tolerancia:", dict(cambia.most_common()))
