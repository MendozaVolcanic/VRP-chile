# -*- coding: utf-8 -*-
"""M3b (frente D, S179). Lo mismo que M3, para VIIRS 375: que le pasa a la vigilancia de la guardia K de VIIRS
(scripts/vigilancia_guardia_viirs.py, main 438a60a1e) si, despues de encender B1, se reemplaza la historia de VIIRS 375
con los records del reproceso de la retrospectiva, como escribe el plan #981 (62ccb8830, seccion 5, pasos 10 a 13).

Fenomeno: la regla de reversion sellada (experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md, seccion
4.1) define el encendido como el menor `processed_utc` de un record de produccion con la marca de la via. Los records
del reproceso se procesaron el 2026-11-08 18:04 UTC o despues (medido en M4), ANTES de cualquier encendido de VIIRS.

Tres escenarios sobre los datos de 438a60a1e (VIIRS de produccion es K en la base, asi que el encendido se simula):
  S0  base, sin tocar. Control: reproduce lo guardado por el workflow (VERDE, antes_del_encendido, nulo con pares).
  S1  solo B1: los records VIIRS 375 desde el 2026-11-09 12:00 UTC llevan la marca de la via, con processed_utc
      2026-11-09T12:00:00Z (un encendido ficticio a esa hora; el flag de produccion se simula encendido).
  S2  B1 mas reemplazo: ademas, los records VIIRS 375 del 2026-10-01 al 2026-11-09 12:00 llevan la marca de la via con
      processed_utc 2026-11-08T18:04:23Z (el menor processed_utc real de los records VIIRS 375 de D2 y D4).

Las dos preguntas del instrumento:
1. Si el reemplazo rompiera la vigilancia, esta medicion lo veria?  Si para lo que depende de la MARCA y de
   `processed_utc` (encendido, plazo, nulo, avisos): ejecuta el `evaluar()` real. NO para lo que depende de lo que la via
   publica (los records simulados conservan el contenido de K): reversion, Muy Bajo y sobre-publicacion quedan SIN DATO.
2. Si el instrumento estuviera muerto?  S0 tiene que reproducir el veredicto guardado; S1 tiene que dar el encendido
   ficticio (2026-11-09 12:00:00) y un nulo con pares: si S1 ya saliera ciego, S2 no probaria nada.

Uso: python m3b_vigilancia_viirs_tras_reemplazo.py <snapshot main> <carpeta base> <carpeta sim> <salida.json>
"""
import sys, io, os, json, copy
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
MAIN, BASE, SIM, OUT = sys.argv[1:5]
sys.path.insert(0, MAIN)
sys.path.insert(0, os.path.join(MAIN, "scripts"))
OUT = os.path.abspath(OUT)   # la salida va a la carpeta desde donde se llama, no a la instantanea del codigo
os.chdir(MAIN)
import vigilancia_guardia_viirs as vgv
import vigilancia_guardia_modis as vg
import banco_paridad as bp
import referencia_mirova_unificada as rmu
aa = vg.aa
aa.CONS = os.path.join(BASE, "latest_consolidado.csv")
aa.OCR = os.path.join(BASE, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")
_orig = rmu.cargar_referencia_unificada
_HIST = Path(BASE) / "data" / "mirova_reference" / "union_historica" / "consolidado_filas_perdidas.csv"
_RESP = Path(BASE) / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado_respaldo_20260408.csv"
rmu.cargar_referencia_unificada = lambda cons, ocr, **kw: _orig(cons, ocr, respaldo_path=_RESP, historico_path=_HIST, **kw)
vgv.GUARDIA = os.path.join(BASE, "data", "guardia_k_viirs")
vgv.JUZGADAS = os.path.join(BASE, "no_existe_juzgadas_viirs.json")   # archivo ausente = ninguna juzgada (leer_juzgadas)
HOY = "2026-11-10"
ENC_FICTICIO = "2026-11-09 12:00"
PROC_ENC = "2026-11-09T12:00:00Z"
PROC_REPRO = "2026-11-08T18:04:23Z"
flag_real = vg.flag_produccion_encendido


def correr(prod_dir, flag=None):
    vgv.PRODUCCION = prod_dir
    bp.DATA = Path(prod_dir)
    vg.flag_produccion_encendido = (lambda sensor=vg.SENSOR: flag) if flag is not None else flag_real
    o = vgv.evaluar(HOY, "v375")
    return {"veredicto": o["veredicto"], "fase": o.get("fase"), "encendido_utc": o.get("encendido_utc"),
            "primera_observacion_via": o.get("primera_observacion_via"), "flag_produccion": o.get("flag_produccion"),
            "ventana": o.get("ventana"), "avisos": o.get("avisos"), "nulo_pares": o["nulo"]["pares"],
            "nulo_distintas": o["nulo"]["distintas"], "nulo_sin_medir": o["nulo"]["sin_medir"],
            "guardia_desde": o.get("guardia_desde"), "guardia_hasta": o.get("guardia_hasta"),
            "duracion": o.get("duracion"), "n_pasadas_alerta": o.get("n_pasadas_alerta")}


def es_v375(r):
    s = str(r.get("sensor") or "")
    return s.startswith("VIIRS") and not s.endswith("_750")


def simular(nombre, reemplazo):
    carpeta = os.path.join(SIM, nombre)
    os.makedirs(carpeta, exist_ok=True)
    n_enc = n_rep = 0
    for vol in aa.VOLS:
        with open(os.path.join(BASE, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8") as fh:
            d = json.load(fh)
        recs = []
        for r in d["records"]:
            dt = r.get("datetime_utc") or ""
            if dt[:10] < "2026-10-01":
                continue
            r = copy.deepcopy(r)
            if es_v375(r) and r.get("via_codigo_mirova") is None:
                if dt >= ENC_FICTICIO:
                    r["via_codigo_mirova"] = True
                    r["processed_utc"] = PROC_ENC
                    n_enc += 1
                elif reemplazo:
                    r["via_codigo_mirova"] = True
                    r["processed_utc"] = PROC_REPRO
                    n_rep += 1
            recs.append(r)
        d["records"] = recs
        with open(os.path.join(carpeta, vol + ".json"), "w", encoding="utf-8") as fh:
            json.dump(d, fh)
    return carpeta, n_enc, n_rep


s0 = correr(os.path.join(BASE, "data", "mirova_equivalent"))
with open(os.path.join(BASE, "data", "audit_continuous", "guardia_v375_latest.json"), encoding="utf-8") as fh:
    guardado = json.load(fh)
ctrl0 = s0["veredicto"] == guardado["veredicto"] and s0["encendido_utc"] == guardado["encendido_utc"] and s0["nulo_pares"] > 0
print("== S0 base ==")
print(json.dumps(s0, indent=1, ensure_ascii=False))
print(f"guardado por el workflow en 438a60a1e: {guardado['veredicto']}, fase {guardado['fase']}, encendido {guardado['encendido_utc']}, "
      f"nulo {guardado['nulo']['pares']} pares (corrida {guardado['generated_utc']})")
print("CONTROL S0:", "OK" if ctrl0 else "FALLA")

c1, n1, _ = simular("s1_solo_b1", False)
s1 = correr(c1, flag=True)
ctrl1 = s1["encendido_utc"] == "2026-11-09 12:00:00" and s1["nulo_pares"] > 0
print(f"\n== S1 solo B1 (encendido ficticio {ENC_FICTICIO} UTC; {n1} records VIIRS 375 posteriores marcados como via) ==")
print(json.dumps(s1, indent=1, ensure_ascii=False))
print("CONTROL S1 (encendido ficticio reconocido y nulo con pares):", "OK" if ctrl1 else "FALLA")

c2, n2e, n2r = simular("s2_b1_y_reemplazo", True)
s2 = correr(c2, flag=True)
print(f"\n== S2 B1 mas reemplazo de la historia de VIIRS 375 ({n2r} records anteriores al encendido marcados como via con "
      f"processed_utc {PROC_REPRO}; {n2e} posteriores) ==")
print(json.dumps(s2, indent=1, ensure_ascii=False))
print("\nLECTURA (solo marca y processed_utc):")
print(f"  encendido que informa la vigilancia: S1 {s1['encendido_utc']} -> S2 {s2['encendido_utc']}")
print(f"  plazo de 120 dias, vence: S1 {s1['duracion']['vence_utc']} -> S2 {s2['duracion']['vence_utc']}")
print(f"  nulo: S1 {s1['nulo_pares']} pares -> S2 {s2['nulo_pares']} pares (sin_medir={s2['nulo_sin_medir']})")
print(f"  veredicto: S1 {s1['veredicto']} -> S2 {s2['veredicto']}")
print(f"  avisos nuevos en S2: {[a for a in s2['avisos'] if a not in s1['avisos']]}")
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"hoy": HOY, "s0": s0, "control_s0": ctrl0, "s1": s1, "control_s1": ctrl1, "s2": s2,
               "n_s1": n1, "n_s2_reemplazo": n2r}, fh, indent=1, ensure_ascii=False)
