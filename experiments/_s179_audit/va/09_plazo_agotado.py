# -*- coding: utf-8 -*-
"""VA-09 (afirmaciones 401 y DEC-12): ¿qué hace la vigilancia con una pérdida de la vía DESPUÉS de la protegida 29?
Se copian las 11 protegidas reales posteriores al encendido (Chillán) corridas +8 y +16 días (33 en total, todas antes
del vencimiento de 120 días) y la vía calla una pasada que la guardia publica: la 5.ª (dentro del plazo) o la 31.ª.
Preguntas del instrumento:
1. Control positivo: callar la 5.ª tiene que dar REVERSION_CANDIDATA; si diera otra cosa, el instrumento no separa nada.
2. Instrumento muerto: sin callar nada tiene que dar VERDE con 33 vistas y fase cumplida.
"""
import io, sys, os, json, copy
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_vigilancia_base.json"), encoding="utf-8"))
E = d["out"]["encendido_modis_utc"]
base = [p for p in d["pasadas"] if p["instante_utc"] >= E and p["protegida"]]
pas = []
for k in (0, 8, 16):
    for p in base:
        q = copy.deepcopy(p)
        t = datetime.strptime(p["instante_utc"], "%Y-%m-%d %H:%M:%S") + timedelta(days=k)
        q["instante_utc"] = t.strftime("%Y-%m-%d %H:%M:%S"); q["fecha_utc"] = t.strftime("%Y-%m-%d %H:%M")
        pas.append(q)
pas.sort(key=lambda p: p["instante_utc"])
HOY = "2026-11-27"
def correr(ps, et):
    r = vg.disparadores(ps, [], [], HOY, E, juzgadas={}, ahora=f"{HOY} 23:59:59")
    print(f"{et}: {r['veredicto']} | reversion {[(p['fecha_utc']) for p in r['reversion']]} | fuera_de_plazo "
          f"{[(p['fecha_utc']) for p in r['fuera_de_plazo']]} | vistas {r['duracion']['protegidas_vistas_en_guardia']} cumplida {r['duracion']['cumplida']}")
correr(pas, "sin callar nada")
pub = [i for i, p in enumerate(pas) if p["guardia_pub"] is True]
for nro in (5, 31):
    q = copy.deepcopy(pas)
    i = nro - 1
    while q[i]["guardia_pub"] is not True:
        i += 1
    q[i]["prod_pub"] = False
    correr(q, f"la vía calla la protegida n.º {i+1} ({q[i]['fecha_utc']}, guardia publica)")
