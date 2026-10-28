# VE2: de que capa de la referencia unificada sale la fila FALSO_POSITIVO de cada far_tabla (principal = los 2 commits de
# Mirova-v1; historico = filas perdidas, archivo del repo; respaldo = archivo del repo). P1: ve si el marco depende de archivos
# del repo que el meta del marco no fija. P2: control = cuenta por capa de TODAS las filas (si la capa no se leyera, daria 0).
import sys, json, collections, datetime as dt
from pathlib import Path
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
sys.path.insert(0, str(R/"scripts")); sys.path.insert(0, str(R))
import referencia_mirova_unificada as U
REF = Path(r"D:/vrp-trabajo/temporales/s166_v375e_verif/ref")
filas = U.cargar_referencia_unificada(REF/"registro_vrp_consolidado.csv", REF/"registro_vrp_ocr.csv")
print("filas por origen:", collections.Counter(f["origen"] for f in filas))
print("archivos de capa:", U.HISTORICO_RECUPERADAS, U.HISTORICO_RECUPERADAS.exists(), U.RESPALDO_20260408, U.RESPALDO_20260408.exists())
import hashlib
for p in (U.HISTORICO_RECUPERADAS, U.RESPALDO_20260408):
    print(p.name, hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16])
por = collections.defaultdict(list)
for f in filas:
    por[(f["volcano"], f["sensor_bucket"])].append((dt.datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S"), f))
aut = json.load(open(R/"experiments/_s162_v375/e_adenda2/objetivos_far_v375.json", encoding="utf-8"))["pasadas"]
c = collections.Counter(); ejemplos = []
for o in aut:
    t = dt.datetime.strptime(o["hora_utc"][:16], "%Y-%m-%d %H:%M")
    rows = [f for (tt, f) in por[(o["volcan"], "VIIRS375")] if abs((tt - t).total_seconds()) <= 120]
    fp = [f for f in rows if f["tipo"].startswith("FALSO_POSITIVO")]
    orig = tuple(sorted({(f["source"], f["origen"]) for f in fp}))
    c[orig] += 1
    if any(f["origen"] != "principal" for f in fp):
        ejemplos.append((o["volcan"], o["hora_utc"], o["clase"], [(f["tipo"], f["origen"], f["dist_km"]) for f in rows]))
print("far_ref por (source, origen) de sus filas FP:", dict(c))
print("pasadas cuya fila FP viene de capa NO principal:", len(ejemplos))
for e in ejemplos[:14]: print("  ", e)
