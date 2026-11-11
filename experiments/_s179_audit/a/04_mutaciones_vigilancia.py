# -*- coding: utf-8 -*-
"""Que ve y que no ve la vigilancia de la guardia K de MODIS (scripts/vigilancia_guardia_modis.py de main 438a60a1e).

Metodo: se cargan los insumos reales de la base (produccion, guardia, referencia) UNA vez y se alteran EN MEMORIA
(nunca en disco) antes de llamar a las mismas funciones del script: pasadas_modis() y disparadores().
Ventana de datos: 2026-10-19 a 2026-11-10. Denominador: las 11 pasadas protegidas MODIS posteriores al encendido.

Las dos preguntas del instrumento:
1. Si la logica de disparo estuviera rota, esto lo veria? Si para los casos sembrados: el control positivo C1
   (protegida que la guardia publica y produccion calla) tiene que dar REVERSION_CANDIDATA; si no, todo lo demas es invalido.
2. Si este instrumento estuviera muerto, se veria distinto? Si: el caso C0 (sin alterar) tiene que dar el mismo
   veredicto y los mismos conteos que 02_vigilancia_en_la_base.txt, y C1 tiene que cambiar.
"""
import io, sys, os, copy, collections
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
vs = vg.vs
HOY = "2026-11-10"; AHORA = "2026-11-10 23:59:59"
enc = vg.leer_encendido(); E = enc["encendido_utc"]
win = ("2026-10-19", HOY)
filas, PROD, GUARDIA, n_via_g = vg.cargar_insumos(win, enc["via"], enc.get("caidas"))
diurna = vs._diurna_por_defecto()

def dt(s): return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

def correr(nombre, mut_prod=None, mut_guardia=None, objetivo=None, hoy=HOY, ahora=AHORA, flag=True):
    prod = copy.deepcopy(PROD); guardia = copy.deepcopy(GUARDIA)
    if mut_prod: prod = mut_prod(prod)
    if mut_guardia: guardia = mut_guardia(guardia)
    viejo = vg.PROTEGIDAS_OBJETIVO
    if objetivo is not None: vg.PROTEGIDAS_OBJETIVO = objetivo
    try:
        pas = vg.pasadas_modis(filas, prod, guardia, win, diurna=diurna)
        d = vg.disparadores(pas, prod, guardia, hoy, E, juzgadas={}, ahora=ahora)
    finally:
        vg.PROTEGIDAS_OBJETIVO = viejo
    ciegos = (vs.avisos_referencia(filas, hoy) + vg.avisos_referencia_modis(filas, hoy) + vg.avisos_guardia(guardia, hoy)
              + vg.avisos_produccion(prod, hoy) + vg.avisos_perfiles(prod, guardia, n_via_g)
              + vg.avisos_via(flag, E, prod) + vg.avisos_nulo(d["nulo"]))
    avisos = ciegos + vg.avisos_caidas(flag, E, prod, hoy)
    v = d["veredicto"]
    if v == "VERDE" and avisos: v = "VIGILANCIA_CIEGA"
    print(f"{nombre}: veredicto={v} | reversion={len(d['reversion'])} fuera_de_plazo={len(d['fuera_de_plazo'])} "
          f"sin_record={len(d['protegidas_sin_record_produccion'])} calladas_por_k={len(d['protegidas_calladas_por_k_de_produccion'])} "
          f"muy_bajo={d['muy_bajo']['k']}/{d['muy_bajo']['n']} sobrepub={d['sobrepublicacion']['k']}/{d['sobrepublicacion']['n']} "
          f"vistas={d['duracion']['protegidas_vistas_en_guardia']} cumplida={d['duracion']['cumplida']} avisos={len(avisos)}")
    for a in avisos: print("     aviso:", a[:230])
    return v, d

def callar(vol, cuando):
    def f(prod):
        n = 0
        for r in prod:
            if r["vol"] == vol and abs((r["dt"] - dt(cuando)).total_seconds()) <= 120:
                r["pub"] = False; n += 1
        assert n, "no se encontro el record a callar"
        return prod
    return f

def quitar(vol, cuando):
    def f(recs):
        out = [r for r in recs if not (r["vol"] == vol and abs((r["dt"] - dt(cuando)).total_seconds()) <= 120)]
        assert len(out) < len(recs), "no se encontro el record a quitar"
        return out
    return f

def quitar_dias(vol, desde):
    def f(recs):
        out = [r for r in recs if not (r["vol"] == vol and r["noche"] >= desde)]
        assert len(out) < len(recs)
        return out
    return f

def a_k(vol, cuando):
    def f(prod):
        for r in prod:
            if r["vol"] == vol and abs((r["dt"] - dt(cuando)).total_seconds()) <= 120:
                r["via"] = False; r["pub"] = False
        return prod
    return f

print("Encendido:", E, "| prod", len(PROD), "| guardia", len(GUARDIA))
print("\nC0 sin alterar (debe igualar 02_vigilancia_en_la_base.txt: VERDE, vistas 11, sobrepub 1/152)")
correr("C0")
print("\nC1 CONTROL POSITIVO: Chillan 2026-11-08 08:00 (22,46 MW; la guardia K publica). Produccion (la via) calla.")
v1, _ = correr("C1", mut_prod=callar("NevadosDeChillan", "2026-11-08 08:00"))
assert v1 == "REVERSION_CANDIDATA", "el control positivo no disparo: instrumento invalido"
print("\nM1: Chillan 2026-11-07 07:25 (9,23 MW; la guardia K NO publica). Produccion (la via) calla tambien.")
correr("M1", mut_prod=callar("NevadosDeChillan", "2026-11-07 07:25"))
print("\nM2: Chillan 2026-11-08 08:00: la via calla Y la guardia no tiene record de esa pasada (job de la guardia caido esa noche).")
correr("M2", mut_prod=callar("NevadosDeChillan", "2026-11-08 08:00"), mut_guardia=quitar("NevadosDeChillan", "2026-11-08 08:00"))
print("\nM3: la guardia de Chillan sin records desde el 2026-11-08 (3 noches) y la via calla el 2026-11-08 08:00 y el 2026-11-09 08:40.")
def m3p(prod): return callar("NevadosDeChillan", "2026-11-09 08:40")(callar("NevadosDeChillan", "2026-11-08 08:00")(prod))
correr("M3", mut_prod=m3p, mut_guardia=quitar_dias("NevadosDeChillan", "2026-11-08"))
print("\nM4: produccion SIN record de Chillan 2026-11-08 08:00 (descarte de borde) y la guardia publica.")
correr("M4", mut_prod=quitar("NevadosDeChillan", "2026-11-08 08:00"))
print("\nM5: plazo. Objetivo bajado a 5 protegidas (simula que ya se vieron 29); la via calla Chillan 2026-11-08 08:00 (la 8.a vista).")
correr("M5", mut_prod=callar("NevadosDeChillan", "2026-11-08 08:00"), objetivo=5)
print("\nM6: la via cae a K en Chillan 2026-11-08 08:00 y calla; la guardia publica.")
correr("M6", mut_prod=a_k("NevadosDeChillan", "2026-11-08 08:00"))
print("\nM7: TODAS las protegidas posteriores al encendido calladas por la via, pero solo donde la guardia K no publica (3 pasadas).")
def m7(prod):
    for c in ("2026-11-07 07:25", "2026-11-09 00:55", "2026-11-09 02:35"): prod = callar("NevadosDeChillan", c)(prod)
    return prod
correr("M7", mut_prod=m7)
print("\nM8: la guardia de TODOS los volcanes sin records desde el 2026-11-08 (corte de NASA de 3 dias) y la via calla Chillan 2026-11-09 08:40.")
def m8g(recs): return [r for r in recs if r["noche"] < "2026-11-08"]
correr("M8", mut_prod=callar("NevadosDeChillan", "2026-11-09 08:40"), mut_guardia=m8g)
print("\nM9: como M8 pero leido 4 dias despues (hoy = 2026-11-12): la frescura de la guardia ya pasa de 3 dias.")
correr("M9", mut_prod=callar("NevadosDeChillan", "2026-11-09 08:40"), mut_guardia=m8g, hoy="2026-11-12", ahora="2026-11-12 23:59:59")

print("\nM10: produccion SIN record de Chillan 2026-11-09 02:35 (7,2 MW, cenit 64,52; la guardia K tiene record y NO publica). Es el descarte de borde 0,5 grados mas alla.")
correr("M10", mut_prod=quitar("NevadosDeChillan", "2026-11-09 02:35"))

print()
print("M11: produccion de Villarrica deja de escribir MODIS desde el 2026-11-06 (la via devuelve None en todas sus pasadas); hoy = 2026-11-10.")
correr("M11", mut_prod=quitar_dias("Villarrica", "2026-11-06"))
print()
print("M12: en Villarrica la via cae a K (sin marca) desde el 2026-11-05; hoy = 2026-11-10.")
def m12(prod):
    for r in prod:
        if r["vol"] == "Villarrica" and r["noche"] >= "2026-11-05": r["via"] = False
    return prod
correr("M12", mut_prod=m12)
print()
print("M13: la referencia de MIROVA sin filas MODIS desde el 2026-11-01 (scraper sin MODIS) y la via calla Chillan 2026-11-08 08:00.")
FILAS_ORIG = filas
filas = [f for f in FILAS_ORIG if not (f.get("sensor_bucket") == "MODIS" and f["fecha_utc"][:10] >= "2026-11-01")]
correr("M13", mut_prod=callar("NevadosDeChillan", "2026-11-08 08:00"))
correr("M13b (misma referencia, leida el 2026-11-12)", mut_prod=callar("NevadosDeChillan", "2026-11-08 08:00"), hoy="2026-11-12", ahora="2026-11-12 23:59:59")
filas = FILAS_ORIG

print()
print("M14: reemplazo de la historia (plan #981): TODOS los records MODIS de produccion anteriores al encendido pasan a ser de la via (via=True), sin cambiar lo que publican.")
def m14(prod):
    for r in prod:
        r["via"] = True
    return prod
correr("M14", mut_prod=m14)
