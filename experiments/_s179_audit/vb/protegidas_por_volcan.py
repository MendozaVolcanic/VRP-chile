#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador VB, auditoría S179. Afirmación 455: ¿en qué volcanes se probó con la vía real que no se pierde una
protegida de VIIRS?

Fuentes: experiments/_s178_lectura/lectura.json en ff8a39972 (rama claude/s178-retro-lectura), campos
sensores.<S>.lectura_b (tramo F26-V) y osf.por_sensor; y la semana de la sombra (re_sim_vigilancia_salida.json de esta
carpeta, escenario A, que reproduce el simulacro del auditor sobre datos de 438a60a1e).

Las dos preguntas del instrumento.
1. Si lo medido estuviera roto, ¿lo vería? Control positivo: Láscar tiene que aparecer con protegidas en F26-V y en
   OSF (lo dice la propia lectura); si mi lectura de los campos estuviera mal, Láscar saldría con 0.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Un volcán ausente del campo se imprime como AUSENTE, no 0.
Uso: python protegidas_por_volcan.py  (lee D:/vrp-trabajo/temporales/s179-audit/vb/lectura_ff8a39972.json)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
LECT = Path(r"D:\vrp-trabajo\temporales\s179-audit\vb\lectura_ff8a39972.json")
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "PuyehueCordonCaulle", "Chaiten"]
d = json.loads(LECT.read_text(encoding="utf-8"))
sim = json.loads((AQUI / "re_sim_vigilancia_salida.json").read_text(encoding="utf-8"))
sombra = {o["sensor"]: o["protegidas_por_volcan"] for o in sim if o["escenario"].startswith("A.")}
for s in ("VIIRS375", "VIIRS750"):
    lb = d["sensores"][s]["lectura_b"]
    brazo = d["sensores"][s]["brazo"]
    osf = d["osf"]["por_sensor"][s]["por_volcan"]
    print(f"== {s} (brazo de la lectura {brazo}; F26-V = [vistas por la vía, total], OSF = protegidas)")
    sin = []
    for v in VOLS:
        if v in lb:
            b = lb[v].get(brazo) or {}
            f26 = b.get("protegidas")
            perd = b.get("perdidas")
        else:
            f26, perd = "AUSENTE", None
        o = osf.get(v, 0)
        so = sombra.get(s, {}).get(v, 0)
        tot = (f26[1] if isinstance(f26, list) else 0) + o + so
        if tot == 0:
            sin.append(v)
        print(f"   {v:20s} F26-V {f26} perdidas {perd} | OSF {o} | sombra 11-03 a 11-09 {so} | total {tot}")
    print(f"   volcanes sin ninguna protegida probada con la vía: {len(sin)} {sin}")
print("\nsalida 0")
