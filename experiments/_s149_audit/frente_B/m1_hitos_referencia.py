# -*- coding: utf-8 -*-
"""Frente B, S149. M1: re-medir sobre el snapshot de hoy los hitos que declara
scripts/calidad_referencia_mirova.py. Solo lectura.

Las dos preguntas del instrumento:
1. Si la tabla estuviera rota (meses sin filas), lo veria? SI: cuenta noches de volcan con fila.
   Control positivo: borrar el 50 % de junio debe bajar la cobertura.
2. Si el instrumento estuviera muerto daria igual? NO: imprime denominadores (n filas) por mes; un
   mes con 0 filas se imprime como SIN DATO.
Noche = definicion de S139 (UTC antes de 10:42 o desde 22:42), para ser comparable con S139.
"""
import csv, io, sys, random, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
SNAP = ROOT / "data/mirova_reference/mirova_v1_snapshot"
CONS = SNAP / "registro_vrp_consolidado.csv"
OCR = SNAP / "registro_vrp_ocr.csv"


def noche(f):  # f = 'YYYY-MM-DD HH:MM:SS'
    hm = f[11:16]
    return hm < "10:42" or hm >= "22:42"


def noche_key(f):
    # noche de volcan: fecha local aproximada (UTC-5h aprox solar) -> usa fecha UTC-12h para agrupar
    from datetime import datetime, timedelta
    dt = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S") - timedelta(hours=16)
    return dt.strftime("%Y-%m-%d")


def dias_mes(m, tmax):
    import calendar
    y, mm = int(m[:4]), int(m[5:7])
    n = calendar.monthrange(y, mm)[1]
    return n


cons = list(csv.DictReader(open(CONS, encoding="utf-8")))
ocr = list(csv.DictReader(open(OCR, encoding="utf-8")))
print("CONS filas", len(cons), "rango", min(r["Fecha_Satelite_UTC"] for r in cons), "a", max(r["Fecha_Satelite_UTC"] for r in cons))
print("OCR filas", len(ocr), "rango", min(r["Fecha_Satelite_UTC"] for r in ocr), "a", max(r["Fecha_Satelite_UTC"] for r in ocr))
print("Volcanes CONS:", sorted(set(r["Volcan"] for r in cons)))
print("Sensores CONS:", collections.Counter(r["Sensor"] for r in cons))
print("Tipos CONS:", collections.Counter(r["Tipo_Registro"] for r in cons))

# --- hito 2026-01-16: tipos
fp = [r for r in cons if r["Tipo_Registro"] == "FALSO_POSITIVO"]
print("\n[H 01-16] primer FALSO_POSITIVO:", min(r["Fecha_Satelite_UTC"] for r in fp))
rv = [r for r in cons if r["Tipo_Registro"] == "RUTINA" and float(r["VRP_MW"] or 0) > 0]
print("[H 01-16] RUTINA con VRP>0:", len(rv), "ultima:", max(r["Fecha_Satelite_UTC"] for r in rv) if rv else None)
# --- Tupungatito
tu = [r for r in cons if r["Volcan"] == "Tupungatito"]
print("[H 02-14] primera fila Tupungatito:", min(r["Fecha_Satelite_UTC"] for r in tu))
# limite 5 vs 7: alertas/FP de Tupungatito con distancia entre 5 y 7, por fecha
entre = sorted((r["Fecha_Satelite_UTC"], r["Tipo_Registro"], r["Distancia_km"]) for r in tu
               if 5 < float(r["Distancia_km"] or 0) <= 7 and float(r["VRP_MW"] or 0) > 0)
print("[H 02-23] Tupungatito con 5<dist<=7 y VRP>0 (tipo por fecha):")
c = collections.Counter((e[0][:7], e[1]) for e in entre)
for k in sorted(c):
    print("    ", k, c[k])
print("     primeras 6:", entre[:6])


# --- cobertura nocturna por mes y sensor; granulos por noche
def cobertura(filas, etiqueta):
    print("\n[cobertura %s] mes | n filas | volcanes | %% noches de volcan con fila nocturna M/V/V375 | filas nocturnas por noche de volcan M/V/V375" % etiqueta)
    meses = sorted(set(r["Fecha_Satelite_UTC"][:7] for r in filas))
    for m in meses:
        fm = [r for r in filas if r["Fecha_Satelite_UTC"][:7] == m]
        vols = sorted(set(r["Volcan"] for r in fm))
        # noches posibles: dias del mes con datos (entre primera y ultima fecha del mes) x volcanes
        dias = sorted(set(noche_key(r["Fecha_Satelite_UTC"]) for r in fm if noche(r["Fecha_Satelite_UTC"])))
        dias = [d for d in dias if d[:7] == m]
        out_c, out_g = [], []
        for s in ("MODIS", "VIIRS", "VIIRS375"):
            por = collections.Counter((r["Volcan"], noche_key(r["Fecha_Satelite_UTC"])) for r in fm
                                      if r["Sensor"] == s and noche(r["Fecha_Satelite_UTC"]) and noche_key(r["Fecha_Satelite_UTC"])[:7] == m)
            den = len(dias) * len(vols)
            out_c.append("%.1f" % (100.0 * len(por) / den) if den else "SIN DATO")
            out_g.append("%.2f" % (sum(por.values()) / len(por)) if por else "SIN DATO")
        print("  %s | %5d | %2d | %s | %s | (den = %d dias x %d volcanes)" % (m, len(fm), len(vols), " / ".join(out_c), " / ".join(out_g), len(dias), len(vols)))


cobertura(cons, "CONS snapshot")
random.seed(1)
cons_ctrl = [r for r in cons if not (r["Fecha_Satelite_UTC"][:7] == "2026-06" and random.random() < 0.5)]
print("\nCONTROL POSITIVO (borrar 50 % de junio): solo la fila de junio debe bajar")
cobertura([r for r in cons_ctrl if r["Fecha_Satelite_UTC"][:7] == "2026-06"], "control")

# --- OCR por mes
print("\n[OCR] mes | filas | ALERTA/FALSO | versiones | Distancia_km==0 | notas mojibake | metodos distintos | ALERTA_OCR / ALERTA cons")
al_cons = collections.Counter(r["Fecha_Satelite_UTC"][:7] for r in cons if r["Tipo_Registro"] == "ALERTA_TERMICA")
for m in sorted(set(r["Fecha_Satelite_UTC"][:7] for r in ocr)):
    fm = [r for r in ocr if r["Fecha_Satelite_UTC"][:7] == m]
    a = sum(1 for r in fm if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR")
    f = sum(1 for r in fm if r["Tipo_Registro"] == "FALSO_POSITIVO_OCR")
    ver = dict(collections.Counter(r["Version_OCR"] for r in fm))
    d0 = sum(1 for r in fm if float(r["Distancia_km"] or 0) == 0)
    moj = sum(1 for r in fm if "Ã" in r["Nota_Validacion"] or "â" in r["Nota_Validacion"])
    met = len(set(r["Metodo_Validacion"] for r in fm))
    print("  %s | %3d | %3d/%3d | %s | %3d | %3d | %2d | %d / %d = %.2f" % (m, len(fm), a, f, ver, d0, moj, met, a, al_cons[m], a / al_cons[m] if al_cons[m] else float("nan")))
print("Tipos OCR:", collections.Counter(r["Tipo_Registro"] for r in ocr))
print("Sensores OCR:", collections.Counter(r["Sensor"] for r in ocr))
# primera fila con distancia medida, primera v30, primera con geometria
dm = [r for r in ocr if float(r["Distancia_km"] or 0) > 0]
print("[H 06-13] primera fila OCR con Distancia_km>0 (por Fecha_Satelite):", min(r["Fecha_Satelite_UTC"] for r in dm), "| por Fecha_Proceso:", min(r["Fecha_Proceso_GitHub"] for r in dm if r["Fecha_Proceso_GitHub"]))
v30 = [r for r in ocr if r["Version_OCR"] == "30.0"]
print("[H 08-06] primera fila Version_OCR 30.0: satelite", min(r["Fecha_Satelite_UTC"] for r in v30), "| proceso", min(r["Fecha_Proceso_GitHub"] for r in v30))
geo = [r for r in ocr if r["Zenith_Sat_deg"].strip()]
print("[V30 geometria] filas con Zenith:", len(geo), "primera satelite", min(r["Fecha_Satelite_UTC"] for r in geo))
limpias = [r for r in ocr if not ("Ã" in r["Nota_Validacion"] or "â" in r["Nota_Validacion"])]
print("[mojibake] ultima fila con mojibake (proceso):", max(r["Fecha_Proceso_GitHub"] for r in ocr if ("Ã" in r["Nota_Validacion"] or "â" in r["Nota_Validacion"])))
# MODIS en OCR
print("[A119 'MODIS no depende del OCR'] ALERTA_OCR por sensor:", collections.Counter(r["Sensor"] for r in ocr if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR"))
# ALERTA OCR MODIS que no estan en cons
kc = set((r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"][:16]) for r in cons if r["Tipo_Registro"] == "ALERTA_TERMICA")
solo = collections.Counter(r["Sensor"] for r in ocr if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR" and (r["Volcan"], r["Sensor"], r["Fecha_Satelite_UTC"][:16]) not in kc)
print("   ALERTA_OCR sin ALERTA cons en la misma llave (minuto), por sensor:", solo)
# VRP >= 1000 en cons
print("[H202] filas CONS con VRP>=1000:", sum(1 for r in cons if float(r["VRP_MW"] or 0) >= 1000), "| max VRP cons:", max(float(r["VRP_MW"] or 0) for r in cons))
