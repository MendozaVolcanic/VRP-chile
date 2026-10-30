"""P2-11, sustrato: pasadas SIN grilla_censo (las únicas donde un «volcán fuera del gránulo» sale del denominador sin la
protección N-01 de control_identidad), por tramo y etiqueta. Pregunta 1: si no hubiera pasadas expuestas, el conteo
daría 0 y se ve. Pregunta 2: control positivo, el total con grilla debe dar 5.321 (N_GRILLAS_CENSO). Denominador:
5.709 pasadas de poblacion_f4.json (árbol 743e89c48)."""
import json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
C = "D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol/experiments/_s166_modd_f4/"
pas = json.load(open(C + "poblacion_f4.json", encoding="utf-8"))["pasadas"]
con = sum(1 for p in pas if p.get("grilla_censo"))
print("con grilla_censo:", con, "sin:", len(pas) - con)
sin = [p for p in pas if not p.get("grilla_censo")]
print("sin grilla por tramo:", dict(collections.Counter(p.get("tramo") for p in sin)))
print("sin grilla por lab:", dict(collections.Counter(p.get("lab") for p in sin)))
print("sin grilla por lab_censo:", dict(collections.Counter(str(p.get("lab_censo")) for p in sin)))
print("sin grilla, tramo C, por lab:", dict(collections.Counter(p.get("lab") for p in sin if p.get("tramo") == "C")))
