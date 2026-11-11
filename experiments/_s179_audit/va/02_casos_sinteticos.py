# -*- coding: utf-8 -*-
"""VA-02 (afirmación 402): qué veredicto da `disparadores` de scripts/vigilancia_guardia_modis.py (438a60a1e) cuando la
vía calla una protegida posterior al encendido, según lo que hizo la guardia en esa pasada.

Insumo: las pasadas reales de 01_vigilancia_base.json (11 protegidas posteriores al encendido, Chillán). Cada caso
cambia UNA pasada y re-evalúa sólo `disparadores` (sin avisos de frescura, que vienen de evaluar()).
Preguntas del instrumento:
1. ¿Vería una vigilancia rota? El control positivo (caso C: la guardia publica, la vía calla) tiene que dar
   REVERSION_CANDIDATA; si diera VERDE, el instrumento no distingue nada.
2. ¿Instrumento muerto? El caso base tiene que dar VERDE (el mismo veredicto que el JSON publicado) y los otros casos
   se leen contra él.
Denominador: 11 protegidas posteriores al encendido (2026-11-02 20:11:43 a 2026-11-10), Chillán.
"""
import io, sys, os, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
AQUI = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(AQUI, "01_vigilancia_base.json"), encoding="utf-8"))
E = d["out"]["encendido_modis_utc"]
pas = d["pasadas"]
HOY = "2026-11-10"
AHORA = "2026-11-10 23:59:59"


def correr(pasadas, etiqueta):
    r = vg.disparadores(pasadas, [], [], HOY, E, juzgadas={}, ahora=AHORA)
    ver = r["veredicto"]
    calladas = [(p["volcano"], p["fecha_utc"]) for p in pasadas if p["protegida"] and p["prod_pub"] is False
                and p["instante_utc"] >= E]
    print(f"{etiqueta}: veredicto {ver} | reversion {len(r['reversion'])} | sin_record {len(r['protegidas_sin_record_produccion'])}"
          f" | calladas_por_k {len(r['protegidas_calladas_por_k_de_produccion'])} | plazo vistas {r['duracion']['protegidas_vistas_en_guardia']}"
          f" | protegidas posteriores que la via calla: {calladas}")
    return ver


def mutar(fecha, **cambios):
    q = copy.deepcopy(pas)
    hit = 0
    for p in q:
        if p["volcano"] == "NevadosDeChillan" and p["fecha_utc"].startswith(fecha):
            p.update(cambios); hit += 1
    assert hit == 1, (fecha, hit)
    return q


correr(pas, "A base (sin cambios)")
correr(mutar("2026-11-09 00:55", prod_pub=False), "B la via calla una protegida que K tampoco publica (11-09 00:55, guardia_pub False)")
correr(mutar("2026-11-08 01:55", prod_pub=False), "C CONTROL POSITIVO la via calla una que K publica (11-08 01:55)")
correr(mutar("2026-11-08 01:55", prod_pub=False, guardia_pub=None), "D la via calla y la guardia no tiene record (11-08 01:55)")
correr(mutar("2026-11-08 01:55", prod_pub=None, guardia_pub=None), "E ni la via ni la guardia tienen record (11-08 01:55)")
correr(mutar("2026-11-08 01:55", prod_pub=None), "F la guardia publica y la via no tiene record (control de MA172-202)")
q = copy.deepcopy(pas)
for p in q:
    if p["instante_utc"] >= E and p["protegida"] and p["guardia_pub"] is False:
        p["prod_pub"] = False
correr(q, "G la via calla las 3 que K no publica (3 de 11)")
