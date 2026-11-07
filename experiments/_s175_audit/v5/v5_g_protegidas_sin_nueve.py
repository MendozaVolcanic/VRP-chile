# -*- coding: utf-8 -*-
"""V5-G: 307. ¿Cambia la lista de protegidas (lectura A, >=1 MW) si se quitan las nueve alertas OCR de 1.0 MW con nota de truncado?
Preg 1: si las nueve 'decidieran' la lista, quitarlas bajaria el conteo; si no, queda igual. Preg 2: control positivo: quitar TODAS las filas OCR
(sensor y ventana iguales) tiene que bajar el conteo (el instrumento ve una baja cuando la hay).
Universo: filas de la referencia unificada de la base (B['filas']), ventanas 2026-09-01..2026-11-07 (la del plan) y 2026-06-11..2026-11-07; protegida =
cm.alerta_protegida; una pasada = clave_pasada (volcan, bucket, minuto). Sensores/volcanes del audit (aw.SENSORS, aw.VOLS)."""
import collections, os, pickle, sys, re, csv
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aw, clase_mirova as cm
B = pickle.load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\f5\f5_base.pkl", "rb"))
ocr = list(csv.DictReader(open(r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_ocr_base.csv", encoding="utf-8")))
nueve = {(f["Fecha_Satelite_UTC"][:16]) for f in ocr if f["Tipo_Registro"] == "ALERTA_TERMICA_OCR" and f["VRP_MW"] and abs(float(f["VRP_MW"]) - 1) < 1e-9 and re.search(r"real\s*\u2208", f["Nota_Validacion"] or "")}
print("fechas de las nueve (por minuto):", len(nueve), sorted(nueve))
def prot(filas, d, h, quitar=None):
    s = {}
    for f in filas:
        if f["volcano"] not in aw.VOLS or f["sensor_bucket"] not in aw.SENSORS or not (d <= f["fecha_utc"][:10] <= h):
            continue
        if quitar and quitar(f):
            continue
        if cm.alerta_protegida(f):
            s[cm.clave_pasada(f)] = s.get(cm.clave_pasada(f), 0) + 1
    return s
es9 = lambda f: f["source"] == "OCR" and f["tipo"] == "ALERTA_TERMICA_OCR" and f["vrp_mw"] == 1.0 and f["fecha_utc"][:16] in nueve
for d, h in (("2026-09-01", "2026-11-07"), ("2026-06-11", "2026-11-07")):
    base = prot(B["filas"], d, h)
    sin9 = prot(B["filas"], d, h, es9)
    sinocr = prot(B["filas"], d, h, lambda f: f["source"] == "OCR")
    perdidas = sorted(set(base) - set(sin9))
    print(f"{d}..{h}: protegidas {len(base)} | sin las nueve {len(sin9)} (pierde {len(perdidas)}) | sin TODO el OCR {len(sinocr)} (CONTROL pierde {len(set(base)-set(sinocr))})")
    for k in perdidas: print("   solo por una de las nueve:", k)
