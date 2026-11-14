# -*- coding: utf-8 -*-
"""m6 (V5B): recuentos finales de las afirmaciones y reclasificacion con la mancha entera.

Que mide y sobre que: las 303 pasadas con panel de p8_clases.json (aciertos 2026-09-22 a 2026-11-06). Clase B se define
en m1 (control: alguna celda de la mancha reproduce la tabla; d por centroide de la mancha). Cuando A borra la mancha,
B la conserva; donde A no borra nada, A y B pueden diferir solo en la cuenta de celdas.
Pregunta 1: si el arreglo fuera inutil, A y B darian lo mismo en los casos sin mancha borrada (se cuenta).
Pregunta 2: si la lectura de la tabla estuviera muerta, ninguna fila de control apareceria (se cuenta).
Control positivo: las 4 de 351 se listan una a una.
"""
import collections, csv, hashlib, json, os, sys, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "..", "f5b"))
import f5b_lib as L
import yaml
sys.stdout.reconfigure(encoding="utf-8")
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
BASE = "752d348bc67190e53b610989877e2405d238a1bc"
m1 = json.load(open(os.path.join(HERE, "m1_mancha.json"), encoding="utf-8"))
p8 = [x for x in json.load(open(os.path.join(HERE, "..", "f5b", "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
print("== universo p8 ==", len(p8), collections.Counter(x["b"] for x in p8))


def claseB(o):
    if o["ctrl_B"] is not True:
        return "iv"
    return "i" if o["d_B_ours_cent"] <= o["tol"] else "iii"


for b in ("VIIRS375", "VIIRS750", "MODIS"):
    for etiqueta, f in (("todas", lambda o: True), ("protegidas", lambda o: o["prot"] == "True")):
        g = [o for o in m1 if o["b"] == b and f(o)]
        print(f"{b} {etiqueta}: n={len(g)} A", dict(collections.Counter(o["claseA"].rstrip("?") for o in g)), " B", dict(collections.Counter(claseB(o) for o in g)))
ch = [o for o in m1 if o["vol"] == "NevadosDeChillan"]
print("Chillan:")
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    g = [o for o in ch if o["b"] == b]
    print(f"  {b}: n={len(g)} A {dict(collections.Counter(o['claseA'].rstrip('?') for o in g))} B {dict(collections.Counter(claseB(o) for o in g))}; A borro mancha en {sum(1 for o in g if o['comps_borradas_por_A']>0)}")
print("Clase A iii que siguen iii en B (todas):", [(o["vol"], o["sensor"], o["dt"], o["prot"], o["d_A_ours"], o["d_B_ours_cent"], o["d_B_ours_min"]) for o in m1 if o["claseA"].startswith("iii") and claseB(o) == "iii"])
print("Clase A iii que pasan a i en B:", [(o["vol"], o["sensor"], o["dt"]) for o in m1 if o["claseA"].startswith("iii") and claseB(o) == "i"])
print("Clase A iii que pasan a iv en B:", [(o["vol"], o["sensor"], o["dt"]) for o in m1 if o["claseA"].startswith("iii") and claseB(o) == "iv"])
print("MODIS Chillan clase A iii:", [(o["sensor"], o["dt"], "dA", o["d_A_ours"], "dBcen", o["d_B_ours_cent"], "dBmin", o["d_B_ours_min"], "comp borrada", o["comps_borradas_por_A"]) for o in ch if o["b"] == "MODIS" and o["claseA"].startswith("iii")])

print("\n== 354: conteos MODIS de p8 ==")
print("MODIS por clase A (toda fila, con y sin panel):", collections.Counter(x["clase"].rstrip("?") for x in p8 if x["b"] == "MODIS"))
print("Motivos iv MODIS:", collections.Counter(x.get("motivo_iv", "").split(" (")[0] for x in p8 if x["b"] == "MODIS" and x["clase"].startswith("iv")))

print("\n== 352: las 30 protegidas de Chillan con control A fallido ==")
fall = [o for o in ch if o["controlA"] is False and o["prot"] == "True" and o["b"] != "MODIS"]
CEL = {"VIIRS375": 0.374, "VIIRS750": 0.747}
xx = {(x["vol"], x["b"], x["dt"]): x for x in p8}
print("n:", len(fall), collections.Counter(o["b"] for o in fall))
for b in ("VIIRS375", "VIIRS750"):
    g = [o for o in fall if o["b"] == b]
    dif = [abs(xx[(o["vol"], o["b"], o["dt"])]["d_png_mirova_center_km"] - o["dist_tabla"]) for o in g]
    print(f"  {b}: n={len(g)}; |d-tabla| por celdas <= 1 sobre tol: {sum(1 for d, o in zip(dif, g) if d <= o['tol'] + CEL[b])}; |d-tabla| p50 {np.median(dif):.2f} max {max(dif):.2f}; d_A_ours p50 {np.median([o['d_A_ours'] for o in g]):.2f}; ctrl_B pasa {sum(1 for o in g if o['ctrl_B'])}")

print("\n== tabla de MIROVA, filas de las tres V750 de 351 (sensor textual) ==")
tabla = list(csv.DictReader(open(r"C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_consolidado_base.csv", encoding="utf-8")))
print("Sensores en la tabla:", collections.Counter(r["Sensor"] for r in tabla))
for h in ("2026-10-29 06:42", "2026-10-10 06:54", "2026-10-16 06:42"):
    print(" ", h, [(r["Sensor"], r["Fecha_Satelite_UTC"], r["VRP_MW"], r["Distancia_km"], r["Tipo_Registro"], r["Clasificacion Mirova"]) for r in tabla if r["Volcan"].lower().startswith("nevados") and r["Fecha_Satelite_UTC"][:16] == h])

print("\n== sha256 de los insumos contra el prompt y la base ==")


def sha(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
print("snapshot_consolidado_base.csv", sha(INS + r"\snapshot_consolidado_base.csv")[:16], "(prompt f833bfdef7c3fc5f) | latest_consolidado_base.csv", sha(INS + r"\latest_consolidado_base.csv")[:16], "(prompt dee768374b84d49b)")
print("snapshot_ocr_base.csv", sha(INS + r"\snapshot_ocr_base.csv")[:16], "(prompt 577a336e76383a67)")
ym_base = subprocess.run(["git", "-C", REPO, "show", f"{BASE}:volcanoes.yaml"], capture_output=True).stdout
ym_main = open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml", "rb").read()
print("volcanoes.yaml copia == base:", hashlib.sha256(ym_base.replace(b"\r\n", b"\n")).hexdigest()[:16], hashlib.sha256(ym_main.replace(b"\r\n", b"\n")).hexdigest()[:16])
y = {v["name"]: v for v in yaml.safe_load(ym_base.decode("utf-8"))["volcanoes"]}["NevadosDeChillan"]
print("Chillan yaml base: mc", y["mirova_center_lat"], y["mirova_center_lon"], "vent", y.get("vent_lat"), y.get("vent_lon"), "d km", round(L.hav(y["mirova_center_lat"], y["mirova_center_lon"], y["vent_lat"], y["vent_lon"]), 3))
pares = list(csv.DictReader(open(os.path.join(HERE, "..", "f5", "i2_pares.csv"), encoding="utf-8")))
print("i2_pares filas:", len(pares), "post 09-22:", sum(1 for r in pares if r["dt"] >= "2026-09-22"))
