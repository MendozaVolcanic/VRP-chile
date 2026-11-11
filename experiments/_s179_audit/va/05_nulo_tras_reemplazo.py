# -*- coding: utf-8 -*-
"""VA-05 (afirmación 405): ¿qué le pasa al nulo de la vigilancia de la guardia K de MODIS si la historia MODIS anterior
al encendido queda escrita con la vía (plan de #981, docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md en 62ccb8830, fuera de main)?

Simulación EN MEMORIA: los records MODIS de producción anteriores al encendido se marcan como de la vía (`via` True),
que es lo que dejaría el reemplazo (los records de reproc-retro-paquete traen `via_codigo_mirova`, perfil
_s172_retro_paquete con enable_modis_codigo_mirova true). No se cambia `pub` (no sabemos qué publicaría la vía en esas
pasadas): por eso sólo se lee el nulo, que no depende de `pub` para contar pares.
Además: ¿se mueve el encendido? Se calcula con encendido_desde_datos sobre records con processed_utc del reproceso
(posterior al 2026-11-02) para ver que el mínimo no cambia.
Preguntas del instrumento:
1. Control positivo: sin la simulación el nulo tiene que dar los 167 pares del JSON publicado; con ella, si el nulo
   dependiera de otra cosa que la marca, seguiría dando pares.
2. Instrumento muerto: imprime cuántos records de producción se marcaron; 0 marcados invalida la lectura.
Ventana: la de la vigilancia, 2026-10-19 a 2026-11-10, HOY = 2026-11-10.
"""
import io, sys, os, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
HOY = "2026-11-10"
enc = vg.leer_encendido()
E = enc["encendido_utc"]
from datetime import date, timedelta
d0 = min(date.fromisoformat(HOY) - timedelta(days=vg.DIAS_NULO),
         date.fromisoformat(E[:10]) - timedelta(days=max(vg.DIAS_ANTES_DEL_ENCENDIDO, vg.DIAS_NULO)))
win = (d0.isoformat(), HOY)
filas, prod, guardia, n_via_g = vg.cargar_insumos(win, enc["via"], enc.get("caidas"))
pas = vg.pasadas_modis(filas, prod, guardia, win, diurna=vg.vs._diurna_por_defecto())
r0 = vg.disparadores(pas, prod, guardia, HOY, E, juzgadas={}, ahora=f"{HOY} 23:59:59")
print("encendido", E, "| ventana", win)
print("SIN simulación: nulo", {k: r0["nulo"][k] for k in ("pares", "distintas", "sin_medir")}, "| avisos_nulo", vg.avisos_nulo(r0["nulo"]))
Edt = vg._dt(E)
prod2 = copy.deepcopy(prod)
n = 0
for r in prod2:
    if r["dt"] < Edt and r.get("via") is not True:
        r["via"] = True; n += 1
print("records MODIS de producción anteriores al encendido marcados como vía:", n, "de", len(prod2))
pas2 = vg.pasadas_modis(filas, prod2, guardia, win, diurna=vg.vs._diurna_por_defecto())
r1 = vg.disparadores(pas2, prod2, guardia, HOY, E, juzgadas={}, ahora=f"{HOY} 23:59:59")
print("CON simulación: nulo", {k: r1["nulo"][k] for k in ("pares", "distintas", "sin_medir")}, "| avisos_nulo", vg.avisos_nulo(r1["nulo"]))
# ¿se mueve el encendido? records de la vía con processed_utc del reproceso (2026-11-09)
raw = {"X": [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-05-01T05:00:00Z", "via_codigo_mirova": True,
              "processed_utc": "2026-11-09T12:00:00Z"},
             {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-03T05:00:00Z", "via_codigo_mirova": True,
              "processed_utc": E.replace(" ", "T") + "Z"}]}
e2 = vg.encendido_desde_datos(raw)
print("encendido con un record del reproceso (procesado 2026-11-09) de una pasada de mayo:", e2["encendido_utc"],
      "| primera_observacion:", e2["primera_observacion"])
# El nulo se mide en [encendido - 14 d, encendido): la ventana no avanza con el tiempo, así que el aviso no se va solo.
for hoy in ("2026-11-20", "2026-12-31"):
    lim = Edt; desde = lim - timedelta(days=vg.DIAS_NULO)
    print(f"con HOY={hoy}: el nulo mide {desde:%Y-%m-%d %H:%M} a {lim:%Y-%m-%d %H:%M} (fijo, atado al encendido)")
