# -*- coding: utf-8 -*-
"""M3 (frente D, S179). Que le pasa a la vigilancia de la guardia K de MODIS (scripts/vigilancia_guardia_modis.py, main
438a60a1e) si se aplica el reemplazo de la historia de MODIS como lo escribe el plan #981 (62ccb8830, seccion 5, pasos
6 a 8, regla A «apartar»).

Fenomeno: la guardia K corre al lado de produccion para ver si la via calla una alerta que K publicaba. Su control
(«nulo») compara, en los 14 dias ANTERIORES al encendido, la guardia (K) contra produccion (K): tienen que publicar lo
mismo. El reemplazo convierte esos records de produccion en records de la via.

Las dos preguntas del instrumento:
1. Si lo que mido estuviera roto (la vigilancia ciega tras el reemplazo), esta medicion lo veria?  Si: ejecuta el
   `evaluar()` real del script de main sobre los datos de la base y sobre una copia simulada, y lee `veredicto`,
   `avisos` y `nulo.pares` de su salida.
2. Si el instrumento estuviera muerto, el resultado se veria distinto?  Si: el escenario BASE tiene que reproducir lo
   que el propio workflow dejo guardado en data/audit_continuous/guardia_modis_latest.json de 438a60a1e (VERDE, nulo de
   167 pares, encendido 2026-11-02 20:11:43). Si BASE no lo reproduce, el script lo dice y no se lee la simulacion.
   Control positivo de la simulacion: el numero de records MODIS marcados como via tiene que subir.

Limite declarado (NO es el reemplazo real): la simulacion marca como via (`via_codigo_mirova: true`, `processed_utc`
del reproceso) los records K de MODIS de produccion entre 2026-10-01 y 2026-11-02, con su contenido de K. Sirve para
leer lo que depende solo de la MARCA (el nulo, los avisos, el encendido). NO sirve para leer nada que dependa de lo que
la via publica en esas pasadas (borde_del_encendido, retrospectivo): eso queda SIN DATO.

Denominador: pasadas MODIS nocturnas de los 11 Tier A en la ventana de la vigilancia (2026-10-19 a 2026-11-10).
Uso: python m3_vigilancia_tras_reemplazo.py <snapshot main> <carpeta base> <carpeta sim> <salida.json>
"""
import sys, io, os, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MAIN, BASE, SIM, OUT = sys.argv[1:5]
sys.path.insert(0, MAIN); sys.path.insert(0, os.path.join(MAIN, "scripts"))
OUT = os.path.abspath(OUT)   # la salida va a la carpeta desde donde se llama, no a la instantanea del codigo
os.chdir(MAIN)
import vigilancia_guardia_modis as vgm
import banco_paridad as bp
from pathlib import Path
aa = vgm.aa
aa.CONS = os.path.join(BASE, "latest_consolidado.csv")
aa.OCR = os.path.join(BASE, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")
vgm.GUARDIA = os.path.join(BASE, "data", "guardia_k_modis")
vgm.JUZGADAS = os.path.join(BASE, "sombra_pasadas_juzgadas_modis.json")
# El cargador de la referencia trae por defecto la ruta del historico dentro del repo; la instantanea de codigo no
# trae data/, asi que se le pasa la copia extraida de 438a60a1e (mismo archivo, otra carpeta).
import referencia_mirova_unificada as rmu
_orig = rmu.cargar_referencia_unificada
_HIST = Path(BASE) / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv"
_RESP = Path(BASE) / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv"
rmu.cargar_referencia_unificada = lambda cons, ocr, **kw: _orig(cons, ocr, respaldo_path=_RESP, historico_path=_HIST, **kw)
HOY = "2026-11-10"
PROC_REPROCESO = "2026-11-10T12:00:00Z"   # P4 se proceso el 2026-11-10; cualquier hora posterior al encendido da lo mismo

def correr(prod_dir):
    vgm.PRODUCCION = prod_dir
    bp.DATA = Path(prod_dir)
    o = vgm.evaluar(HOY)
    return {"veredicto": o["veredicto"], "fase": o.get("fase"), "encendido": o.get("encendido_modis_utc"),
            "primera_observacion_via": o.get("primera_observacion_via"), "ventana": o.get("ventana"),
            "avisos": o.get("avisos"), "nulo_pares": o["nulo"]["pares"], "nulo_distintas": o["nulo"]["distintas"],
            "nulo_sin_medir": o["nulo"]["sin_medir"], "guardia_desde": o.get("guardia_desde"),
            "guardia_hasta": o.get("guardia_hasta"), "duracion": o.get("duracion"),
            "n_pasadas_alerta": o.get("n_pasadas_alerta"),
            "n_borde_del_encendido": len(o.get("borde_del_encendido", [])),
            "n_retro_guardia_publica_prod_calla": len(o["retrospectivo"]["protegidas_que_la_guardia_publica_y_prod_calla"])}

prod_base = os.path.join(BASE, "data", "mirova_equivalent")
base = correr(prod_base)
guardado = json.load(open(os.path.join(BASE, "data", "audit_continuous", "guardia_modis_latest.json"), encoding="utf-8"))
ctrl = (base["veredicto"] == guardado["veredicto"] and base["encendido"] == guardado["encendido_modis_utc"]
        and base["nulo_pares"] > 0)
print("== BASE (datos de 438a60a1e, sin tocar) ==")
print(json.dumps(base, indent=1, ensure_ascii=False))
print(f"guardado por el workflow en 438a60a1e: veredicto {guardado['veredicto']}, encendido {guardado['encendido_modis_utc']}, "
      f"nulo {guardado['nulo']['pares']} pares (corrida {guardado['generated_utc']})")
print("CONTROL BASE:", "OK" if ctrl else "FALLA: no se lee la simulacion")

# simulacion: K de MODIS anterior a la via, 2026-10-01..2026-11-02, pasa a llevar la marca de la via
os.makedirs(SIM, exist_ok=True)
n_marcados = 0; n_via_antes = 0
for vol in aa.VOLS:
    d = json.load(open(os.path.join(prod_base, vol + ".json"), encoding="utf-8"))
    recs = []
    for r in d["records"]:
        if (r.get("datetime_utc") or "")[:10] < "2026-10-01":
            continue            # recorte: la vigilancia solo mira desde el 2026-10-19; achica la copia
        r = copy.deepcopy(r)
        es_modis = str(r.get("sensor") or "").startswith("MODIS")
        if es_modis and r.get("via_codigo_mirova") is True:
            n_via_antes += 1
        if es_modis and r.get("via_codigo_mirova") is None and r["datetime_utc"][:10] <= "2026-11-02":
            r["via_codigo_mirova"] = True
            r["processed_utc"] = PROC_REPROCESO
            n_marcados += 1
        recs.append(r)
    d["records"] = recs
    json.dump(d, open(os.path.join(SIM, vol + ".json"), "w", encoding="utf-8"))
sim = correr(SIM)
print(f"\n== SIMULACION del paso MODIS del plan (regla A): {n_marcados} records K de MODIS del 2026-10-01 al 11-02 marcados como via "
      f"(antes habia {n_via_antes} de la via desde el 2026-10-01) ==")
print(json.dumps(sim, indent=1, ensure_ascii=False))
print("\nLECTURA (solo lo que depende de la marca):")
print(f"  encendido: base {base['encendido']} -> simulacion {sim['encendido']}")
print(f"  nulo: base {base['nulo_pares']} pares -> simulacion {sim['nulo_pares']} pares (sin_medir={sim['nulo_sin_medir']})")
print(f"  veredicto: base {base['veredicto']} -> simulacion {sim['veredicto']}")
print(f"  avisos nuevos: {[a for a in sim['avisos'] if a not in base['avisos']]}")
json.dump({"hoy": HOY, "base": base, "guardado_workflow": {k: guardado.get(k) for k in ("generated_utc", "veredicto", "encendido_modis_utc")},
           "guardado_nulo_pares": guardado["nulo"]["pares"], "control_base_ok": ctrl, "n_marcados": n_marcados, "simulacion": sim},
          open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
