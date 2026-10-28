# VE2: conteo INDEPENDIENTE de las far_ref de VIIRS 375 (sin banco_paridad ni 01_poblacion), directo de la copia de la
# referencia en los commits fijos (bajada por objetivos_far_v375.py a D:/.../ref) y de los records de 533398f8f.
# P1: ve un desacuerdo si la lista del autor tiene pasadas de mas o de menos (comparo por (volcan, hora) con la suya).
# P2: control positivo = el conteo de 'pos' (ALERTA) y de RUTINA tambien se imprime; si el pareo estuviera muerto daria 0.
import csv, json, collections, datetime as dt, sys
from pathlib import Path
REF = Path(r"D:/vrp-trabajo/temporales/s166_v375e_verif/ref")
DATA = Path(r"D:/vrp-trabajo/temporales/s159_n/data_main")
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
EXCL = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
def t(s): return dt.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S") if len(s) >= 19 else dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
cons = list(csv.DictReader(open(REF/"registro_vrp_consolidado.csv", encoding="utf-8")))
ocr = list(csv.DictReader(open(REF/"registro_vrp_ocr.csv", encoding="utf-8")))
ALIAS = {}   # nombre del csv -> nombre del volcan (se imprime lo que no calza)
def clave(n): return n.replace(" ", "").replace("-", "").lower()
filas = collections.defaultdict(list)
for src, rows in (("CONS", cons), ("OCR", ocr)):
    for x in rows:
        if x["Sensor"] != "VIIRS375": continue
        filas[clave(x["Volcan"])].append((t(x["Fecha_Satelite_UTC"]), x["Tipo_Registro"], src, x["Sensor"], x["Distancia_km"], x["VRP_MW"]))
print("sensores en tabla:", collections.Counter(x["Sensor"] for x in cons))
out = []; cnt = collections.Counter(); sens = collections.Counter()
for f in sorted(DATA.glob("*.json")):
    vol = f.stem
    d = json.load(open(f, encoding="utf-8")); rc = d["records"] if isinstance(d, dict) else d
    for r in rc:
        s = r.get("sensor", "")
        if not s.startswith("VIIRS") or s.endswith("_750"): continue
        h = r["datetime_utc"]
        if not ("2026-04-01" <= h[:10] <= "2026-10-21") or h[:10] in EXCL: continue
        tt = t(h)
        cand = [x for x in filas[clave(vol)] if abs((x[0]-tt).total_seconds()) <= 120]
        if not cand: cnt["sin_fila"] += 1; continue
        tip = [x[1] for x in cand]
        alerta = any(a.startswith("ALERTA") and a != "ALERTA_SIN_GEOMETRIA_OCR" for a in tip)
        fp_t = any(x[1] == "FALSO_POSITIVO" and x[2] == "CONS" for x in cand)
        fp_o = any(x[1] == "FALSO_POSITIVO_OCR" for x in cand)
        if alerta: cnt["pos"] += 1
        elif fp_t: cnt["far_tabla"] += 1; out.append((vol, h[:16], "far_tabla"))
        elif fp_o: cnt["far_ocr"] += 1; out.append((vol, h[:16], "far_ocr"))
        else: cnt["otro"] += 1
print("conteo independiente (sensor VIIRS sin _750 en el record, filas a +-120 s, SIN filtro de noche ni de gránulo):", dict(cnt))
aut = json.load(open(R/"experiments/_s162_v375/e_adenda2/objetivos_far_v375.json", encoding="utf-8"))["pasadas"]
A = {(o["volcan"], o["hora_utc"][:16]): o["clase"] for o in aut}
M = {(v, h): c for v, h, c in out}
print("autor", len(A), "mio", len(M), "solo en autor:", sorted(set(A)-set(M))[:10], "solo mio:", sorted(set(M)-set(A))[:10])
print("clases distintas en comunes:", [(k, A[k], M[k]) for k in A if k in M and A[k] != M[k]][:10])
