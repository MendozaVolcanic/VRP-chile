# -*- coding: utf-8 -*-
"""Cuando se agotan las 29 protegidas del plazo de la reversion pre-autorizada de MODIS (regla, seccion 4.6).
Lee 02_vigilancia_en_la_base.json (salida de vigilancia_guardia_modis.evaluar sobre main 438a60a1e, hoy = 2026-11-10).
Preguntas del instrumento: (1) si el contador estuviera roto se veria: lista cada pasada contada. (2) instrumento
muerto: el total tiene que igualar `protegidas_vistas_en_guardia` del propio script del repo (11).
La proyeccion es lineal y es mia: no es un pronostico de la actividad de Chillan.
Ventana: 2026-11-02 20:11:43 (encendido) a 2026-11-10. Denominador: pasadas MODIS nocturnas protegidas con record de la guardia."""
import io, sys, json, os, collections
from datetime import date, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_vigilancia_en_la_base.json"), encoding="utf-8"))
E = d["out"]["encendido_modis_utc"]
vistas = [p for p in d["pasadas"] if p["instante_utc"] >= E and p["protegida"] and p["guardia_pub"] is not None and p.get("prod_via") is not False]
print("encendido:", E, "| contador del script del repo:", d["out"]["duracion"]["protegidas_vistas_en_guardia"], "| recontadas aqui:", len(vistas))
por_noche = collections.Counter(p["fecha_utc"][:10] for p in vistas)
por_volcan = collections.Counter(p["volcano"] for p in vistas)
print("por volcan:", dict(por_volcan))
print("por noche UTC:", dict(sorted(por_noche.items())))
print("la guardia K publica:", sum(1 for p in vistas if p["guardia_pub"]), "de", len(vistas), "| la via publica:", sum(1 for p in vistas if p["prod_pub"]), "de", len(vistas))
ini, fin = date(2026, 11, 3), date(2026, 11, 9)   # noches completas con guardia despues del encendido
noches = (fin - ini).days + 1
ritmo = len(vistas) / noches
faltan = 29 - len(vistas)
print(f"noches completas {ini} a {fin}: {noches} | ritmo {ritmo:.2f} protegidas por noche | faltan {faltan}")
for nombre, r in (("ritmo de las 7 noches", ritmo), ("ritmo de las ultimas 3 noches", sum(por_noche[str(fin - timedelta(days=i))] for i in range(3)) / 3), ("mitad del ritmo", ritmo / 2)):
    dias = faltan / r
    print(f"  con {nombre} ({r:.2f} por noche): la protegida 29 llega hacia el {fin + timedelta(days=round(dias))} ({dias:.0f} noches mas, dia {(fin + timedelta(days=round(dias)) - date(2026,11,2)).days} desde el encendido)")
print("la regla sellada estima: «a ese ritmo las 29 llegan cerca del día 109» (REGLA_REVERSION_MODD_BORRADOR.md seccion 4.6)")
