# -*- coding: utf-8 -*-
"""Verificador S159: ¿la referencia congelada de S153 (Mirova-v1@c5944c61, 2026-10-14 14:26Z, + union f3b414213
+ respaldo 20260408) le faltan filas que la tabla tuvo alguna vez en las ventanas V1 y V2? ¿y cambia hoy?

"Alguna vez vista" = CONS de origin/main hoy ∪ filas que historia_completa.json registra como bajas (contenido viejo).
Pregunta 1: si a S153 le faltaran alertas, la resta las mostraria (control positivo: misma resta contra el CSV
upstream del 2026-10-18 17:41, 96cf680ee, debe dar las 4 protegidas que bisect_upstream encontro perdidas ese dia
si caen en ventana). Pregunta 2: cada capa reporta su n; n=0 = SIN DATO, no "no falta nada".
"""
import csv, io, json, subprocess, sys, urllib.request, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = r"C:\vrp-trabajo\s159-pruebas"; sys.path.insert(0, R)
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name
def k(r):
    v = normalize_volcano_name(r.get("Volcan")); f = (r.get("Fecha_Satelite_UTC") or "").strip()
    return (v, normalize_sensor(r.get("Sensor")), f[:16]) if v and len(f) >= 16 else None
def rows(txt):
    out = {}
    for r in csv.DictReader(io.StringIO(txt)):
        kk = k(r)
        if kk: out[kk] = {"tipo": (r.get("Tipo_Registro") or "").strip(), "vrp": float((r.get("VRP_MW") or "0").replace(",", "") or 0)}
    return out
def git(ref, p): return subprocess.run(["git", "-C", R, "show", f"{ref}:{p}"], capture_output=True, text=True, encoding="utf-8").stdout
def up(sha, n="registro_vrp_consolidado.csv"):
    return urllib.request.urlopen(f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/{n}", timeout=120).read().decode("utf-8", "replace")
U = "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"
RESP = "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv"
s153 = rows(up("c5944c6134bff2bdc9380f9005c27055fd74d450")); u14 = rows(git("f3b414213", U)); resp = rows(git("origin/main", RESP))
hoy = rows(git("origin/main", "latest_consolidado.csv")); u19 = rows(git("2e1bc0e31", U)); ctrl = rows(up("96cf680ee"))
print("n capas: s153_cons", len(s153), "union14", len(u14), "respaldo", len(resp), "hoy", len(hoy), "union19", len(u19), "ctrl", len(ctrl))
ref153 = dict(resp); ref153.update(u14); ref153.update(s153)
refhoy = dict(resp); refhoy.update(u19); refhoy.update(hoy)
h = json.load(open(R + r"\experiments\_s159\referencia_estable\historia_completa.json", encoding="utf-8"))
vista = {}
for e in h["CONS"]["eventos"]:
    if e["ev"] == "baja": vista.setdefault(tuple(e["k"]), {"tipo": e["viejo"]["tipo"], "vrp": e["viejo"]["vrp"] or 0})
vista.update(hoy)
def estr(c):
    t = c["tipo"]
    if t.startswith("ALERTA"): return "protegida" if c["vrp"] >= 1 else "alerta<1"
    return "fp" if t.startswith("FALSO") else "rutina"
VENT = {"V1": ("2026-08-29", "2026-10-08 23:59"), "V2": ("2026-03-01", "2026-06-12 23:59")}
for nom, (a, b) in VENT.items():
    en = {kk: c for kk, c in vista.items() if a <= kk[2] <= b}
    for etiqueta, ref in (("S153", ref153), ("hoy", refhoy), ("ctrl_96cf680ee", {**resp, **ctrl})):
        falta = [kk for kk in en if kk not in ref]
        print(nom, etiqueta, "vistas", len(en), "faltan", len(falta), dict(collections.Counter(estr(en[kk]) for kk in falta)),
              sorted(kk for kk in falta if estr(en[kk]) == "protegida"))
    dif = [kk for kk in set(ref153) | set(refhoy) if a <= kk[2] <= b and (kk in ref153) != (kk in refhoy)]
    print(nom, "S153 vs hoy: claves en uno solo", len(dif), dict(collections.Counter(("solo153" if kk in ref153 else "solo_hoy", estr(ref153.get(kk) or refhoy[kk])) for kk in dif)))
    cam = [kk for kk in set(ref153) & set(refhoy) if a <= kk[2] <= b and ref153[kk]["tipo"] != refhoy[kk]["tipo"]]
    print(nom, "S153 vs hoy: cambio de tipo", len(cam))
