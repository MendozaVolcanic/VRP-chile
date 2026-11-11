# Copia del script 09 del auditor A, con BASE apuntando a la base propia del verificador VA (unico cambio).
# -*- coding: utf-8 -*-
"""Que hace el audit semanal (scripts/auto_audit_weekly.py de main 438a60a1e) con una protegida MODIS que la via pierde
y que la vigilancia de la guardia no ve (casos M1 y M10 de 04_mutaciones_vigilancia.py).

Metodo: se corre banco_ventana() real sobre la ventana de 60 dias y se alteran EN MEMORIA los records del banco antes de
llamar a alertas_protegidas(), flags_protegidas() y avisos_protegidas_sin_record() (las mismas funciones del audit).

Preguntas del instrumento:
1. Si el audit no viera la perdida, esto lo mostraria? Si: imprime flags y avisos con y sin la alteracion.
2. Instrumento muerto: el caso sin alterar tiene que listar las protegidas MODIS de la via como «publicada» (11 o mas)
   y 0 flags de la via; si no, lo demas no vale.
Ventana: 2026-09-11 a 2026-11-10 (60 dias, como el audit). Referencia: snapshot del repo en el commit.
"""
import io, sys, os, copy
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE); os.chdir(BASE)
import auto_audit_weekly as aa
win = ("2026-09-11", "2026-11-10")
frontera = aa.leer_frontera_k(); vigente = aa.detector_vigente(frontera)
records_por_volcan, integrity = aa.cargar_records()
via_modis = aa.fronteras_via(records_por_volcan)
via = aa.claves_via(records_por_volcan) if via_modis else None
print("frontera K:", frontera, "| vigente:", vigente, "| fronteras de la via:", via_modis)
recs, filas = aa.banco_ventana(win)
def dt(s): return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
def correr(nombre, mut=None):
    r2 = copy.deepcopy(recs)
    if mut: r2 = mut(r2)
    prot = aa.alertas_protegidas(filas, r2, win, frontera, via_modis=via_modis, via=via)
    modis_via = [p for p in prot if p["sensor"] == "MODIS" and p["detector"] == "VIA_MODIS"]
    fl = [f for f in aa.flags_protegidas(prot, vigente, via_modis) if "MODIS" in f]
    av = [a for a in aa.avisos_protegidas_sin_record(prot, vigente, via_modis) if "MODIS" in a]
    import collections
    print(f"\n{nombre}: protegidas MODIS de la via {len(modis_via)} por estado {dict(collections.Counter(p['estado'] for p in modis_via))}")
    print("   flags MODIS (degradan a FUERA_DE_BANDA):", fl)
    print("   avisos de cobertura MODIS (degradan a DEGRADADO):", av)
def callar(vol, cuando):
    def f(rs):
        n = 0
        for r in rs:
            if r["vol"] == vol and r["b"] == "MODIS" and abs((r["dt"] - dt(cuando)).total_seconds()) <= 120: r["pub"] = False; n += 1
        assert n; return rs
    return f
def quitar(vol, cuando):
    def f(rs):
        out = [r for r in rs if not (r["vol"] == vol and r["b"] == "MODIS" and abs((r["dt"] - dt(cuando)).total_seconds()) <= 120)]
        assert len(out) < len(rs); return out
    return f
correr("A0 sin alterar")
correr("A1 (= M1): la via calla Chillan 2026-11-07 07:25 (9,23 MW; la guardia K tampoco publica)", callar("NevadosDeChillan", "2026-11-07 07:25"))
correr("A10 (= M10): produccion sin record de Chillan 2026-11-09 02:35 (7,2 MW, cenit 64,5; descarte de borde)", quitar("NevadosDeChillan", "2026-11-09 02:35"))
