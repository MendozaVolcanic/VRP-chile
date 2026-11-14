#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F1 (auditoría S175): mutaciones sobre la vigilancia de la guardia K de MODIS (scripts/vigilancia_guardia_modis.py
de la base, copia en root_base), para saber qué regresiones vería y cuáles no (vigilante ciego, guía §3).

Cada mutación copia los JSON de producción y de la guardia a una carpeta propia, los altera y corre
`vigilancia_guardia_modis.evaluar(hoy)` con las constantes del módulo apuntando a la copia. La referencia es la
que se pase con --cons/--ocr (la de la base por defecto).

Pregunta 1 (¿vería la regresión?): cada mutación declara el veredicto esperado si el vigilante viera el defecto.
Pregunta 2 (¿el instrumento está vivo?): M0 es la corrida sin mutar (tiene que reproducir el VERDE) y M1 es un
control positivo (una candidata inyectada tiene que dar REVERSION_CANDIDATA).

Uso: python mutaciones_vigilancia.py <root_base> <hoy AAAA-MM-DD> [--cons CSV --ocr CSV]
"""
import copy
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = sys.argv[1]
HOY = sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import vigilancia_guardia_modis as vgm  # noqa: E402

if "--cons" in sys.argv:
    vgm.aa.CONS = sys.argv[sys.argv.index("--cons") + 1]
if "--ocr" in sys.argv:
    vgm.aa.OCR = sys.argv[sys.argv.index("--ocr") + 1]

MUT = Path(ROOT).parent / "mutaciones"
PROD0 = Path(ROOT) / "data" / "mirova_equivalent"
GUARD0 = Path(ROOT) / "data" / "guardia_k_modis"
VOLS = bp.VOLS


def preparar(nombre):
    d = MUT / nombre
    if d.exists():
        shutil.rmtree(d)
    (d / "prod").mkdir(parents=True)
    (d / "guardia").mkdir(parents=True)
    for v in VOLS:
        shutil.copy(PROD0 / f"{v}.json", d / "prod" / f"{v}.json")
        shutil.copy(GUARD0 / f"{v}.json", d / "guardia" / f"{v}.json")
    return d


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, d):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)


def correr(d):
    vgm.PRODUCCION = str(d / "prod")
    vgm.GUARDIA = str(d / "guardia")
    bp.DATA = d / "prod"
    out = vgm.evaluar(HOY)
    res = {"veredicto": out["veredicto"], "avisos": out["avisos"], "encendido": out["encendido_modis_utc"],
           "reversion": [(p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]) for p in out["reversion"]],
           "sin_record": [(p["volcano"], p["fecha_utc"]) for p in out["protegidas_sin_record_produccion"]],
           "borde_enc": [(p["volcano"], p["fecha_utc"]) for p in out["borde_del_encendido"]],
           "muy_bajo": {k: v for k, v in out["muy_bajo"].items() if k != "pasadas"},
           "sobrepub": {k: v for k, v in out["sobrepublicacion"].items() if k != "pasadas"},
           "nulo": {k: v for k, v in out["nulo"].items() if k not in ("detalle", "nota")},
           "duracion": out["duracion"], "n_pasadas_alerta": out["n_pasadas_alerta"],
           "n_con_guardia": out["n_pasadas_alerta_con_guardia"]}
    return res, out


def pasadas_protegidas_post(out):
    """Protegidas posteriores al encendido con record en guardia y producción (candidatas a mutar)."""
    enc = out["encendido_modis_utc"]
    return [p for p in out.get("protegidas_sin_publicar_produccion", []) + _todas(out)
            if p["protegida"] and p["instante_utc"] >= enc and p["guardia_pub"] is not None]


def _todas(out):
    return []


def publicar(rec, inner):
    rec["vrp_mw"] = 2.5
    rec["distance_class"] = "summit"
    rec["t_max_k"] = 310.0
    rec["primary_cluster"] = {"vrp_mw": 2.5, "n_pixels": 2, "centroid_lat": rec.get("final_hotspot_lat") or 0.0,
                              "centroid_lon": rec.get("final_hotspot_lon") or 0.0, "centroid_dist_km": 0.5,
                              "single_pixel_mode": False}


def callar(rec):
    rec["vrp_mw"] = 0.0
    rec["primary_cluster"] = None
    rec["distance_class"] = None
    rec["anomaly_pixels"] = []


def main():
    resultados = {}
    # M0: sin mutar
    d = preparar("M0_sin_mutar")
    r0, out0 = correr(d)
    resultados["M0_sin_mutar (esperado VERDE, como el commiteado)"] = r0

    # Elegir una protegida posterior al encendido con record en los dos lados: la primera de `vistas`.
    # Reconstruimos las pasadas con las funciones del módulo para elegir con criterio.
    import referencia_mirova_unificada as rmu
    enc = vgm.leer_encendido()
    win = tuple(out0["ventana"])
    filas, prod, guardia, _ = vgm.cargar_insumos(win, enc["via"])
    pas = vgm.pasadas_modis(filas, prod, guardia, win, diurna=vgm.vs._diurna_por_defecto())
    post = [p for p in pas if p["instante_utc"] >= enc["encendido_utc"] and p["guardia_pub"] is not None
            and p["prod_pub"] is not None and p["prod_via"] is True]
    resultados["_pasadas_alerta_post_encendido_con_record_en_ambos_y_prod_via"] = [
        (p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"], p["protegida"], p["prod_pub"], p["guardia_pub"]) for p in post]
    objetivo = next((p for p in post if p["protegida"]), None) or (post[0] if post else None)
    if objetivo is None:
        resultados["M1"] = "SIN DATO: no hay pasada posterior al encendido con alerta de MIROVA y record en ambos lados"
    else:
        vol, minuto = objetivo["volcano"], objetivo["fecha_utc"]
        # M1: producción (vía) calla y la guardia publica → REVERSION_CANDIDATA (control positivo)
        d = preparar("M1_candidata")
        for lado, fn in (("prod", callar), ("guardia", publicar)):
            j = leer(d / lado / f"{vol}.json")
            n = 0
            for rec in j["records"]:
                if str(rec.get("sensor", "")).startswith("MODIS") and str(rec.get("datetime_utc"))[:16] == minuto:
                    (fn(rec, None) if fn is publicar else fn(rec)); n += 1
            escribir(d / lado / f"{vol}.json", j)
            resultados.setdefault("_M1_records_mutados", {})[lado] = n
        # si la protegida elegida no es protegida (<1 MW) la subimos en la referencia no: la dejamos y leemos el nivel
        r, _ = correr(d)
        esperado = "REVERSION_CANDIDATA" if objetivo["protegida"] else "INVESTIGAR (muy bajo, bajo la cota) o VERDE"
        resultados[f"M1_prod_calla_guardia_publica {vol} {minuto} MIROVA {objetivo['vrp_mirova_mw']} MW (esperado {esperado})"] = r

        # M4: producción sin record de esa pasada y la guardia publica → INVESTIGAR (sin_record) si pasaron 24 h
        d = preparar("M4_sin_record")
        j = leer(d / "prod" / f"{vol}.json")
        j["records"] = [rec for rec in j["records"] if not (str(rec.get("sensor", "")).startswith("MODIS")
                                                           and str(rec.get("datetime_utc"))[:16] == minuto)]
        escribir(d / "prod" / f"{vol}.json", j)
        j = leer(d / "guardia" / f"{vol}.json")
        for rec in j["records"]:
            if str(rec.get("sensor", "")).startswith("MODIS") and str(rec.get("datetime_utc"))[:16] == minuto:
                publicar(rec, None)
        escribir(d / "guardia" / f"{vol}.json", j)
        r, _ = correr(d)
        resultados[f"M4_prod_sin_record_guardia_publica {vol} {minuto} (esperado INVESTIGAR si protegida y >24 h)"] = r

    # M6: el record de producción de la protegida es la CAÍDA a K de la vía ("sin_mxd03": K corrió, no la vía) y
    # calla, la guardia publica. La regla §4.3 pide que «producción (la vía) tiene record y no publica»; si el
    # instrumento no mira la marca, revierte la vía por algo que hizo K.
    if objetivo is not None:
        d = preparar("M6_candidata_con_record_caida_k")
        j = leer(d / "prod" / f"{vol}.json")
        for rec in j["records"]:
            if str(rec.get("sensor", "")).startswith("MODIS") and str(rec.get("datetime_utc"))[:16] == minuto:
                callar(rec); rec["via_codigo_mirova"] = "sin_mxd03"
        escribir(d / "prod" / f"{vol}.json", j)
        j = leer(d / "guardia" / f"{vol}.json")
        for rec in j["records"]:
            if str(rec.get("sensor", "")).startswith("MODIS") and str(rec.get("datetime_utc"))[:16] == minuto:
                publicar(rec, None)
        escribir(d / "guardia" / f"{vol}.json", j)
        r, _ = correr(d)
        resultados[f"M6_prod_record_es_caida_K_y_calla_guardia_publica {vol} {minuto} (si distingue el detector: INVESTIGAR o aviso, no REVERSION_CANDIDATA)"] = r

    # M2: la vía muere en UN volcán: todos sus records de la vía pasan a caída K ("sin_grilla"), el resto sigue.
    d = preparar("M2_via_muerta_un_volcan")
    vol2 = "Chaiten"
    j = leer(d / "prod" / f"{vol2}.json")
    n = 0
    for rec in j["records"]:
        if rec.get("via_codigo_mirova") is True:
            rec["via_codigo_mirova"] = "sin_grilla"; n += 1
    escribir(d / "prod" / f"{vol2}.json", j)
    r, _ = correr(d)
    resultados[f"M2_via_cae_a_K_solo_en_{vol2} ({n} records; esperado si viera la regresión: aviso o INVESTIGAR)"] = r

    # M2b: la vía muere en TODOS los volcanes (todos los records de la vía pasan a caída K).
    d = preparar("M2b_via_muerta_todos")
    n = 0
    for v in VOLS:
        j = leer(d / "prod" / f"{v}.json")
        for rec in j["records"]:
            if rec.get("via_codigo_mirova") is True:
                rec["via_codigo_mirova"] = "sin_mxd03"; n += 1
        escribir(d / "prod" / f"{v}.json", j)
    r, _ = correr(d)
    resultados[f"M2b_via_cae_a_K_en_todos ({n} records; esperado VIGILANCIA_CIEGA)"] = r

    # M2c: la vía deja de escribir desde hace 4 días en UN volcán (records de la vía de los últimos 4 días borrados,
    # y repuestos como K sin clave): frescura de producción sigue verde en ese volcán.
    d = preparar("M2c_via_detenida_un_volcan")
    j = leer(d / "prod" / f"{vol2}.json")
    n = 0
    for rec in j["records"]:
        if rec.get("via_codigo_mirova") is True and str(rec.get("datetime_utc"))[:10] >= "2026-11-04":
            rec.pop("via_codigo_mirova"); n += 1
    escribir(d / "prod" / f"{vol2}.json", j)
    r, _ = correr(d)
    resultados[f"M2c_via_detenida_desde_2026-11-04_solo_en_{vol2} ({n} records sin clave; esperado si viera: aviso)"] = r

    # M3: falta el JSON de la guardia de un volcán → VIGILANCIA_CIEGA
    d = preparar("M3_guardia_sin_villarrica")
    os.remove(d / "guardia" / "Villarrica.json")
    r, _ = correr(d)
    resultados["M3_guardia_sin_Villarrica.json (esperado VIGILANCIA_CIEGA)"] = r

    # M5: la guardia trae un record con la marca de la vía → aviso de perfiles
    d = preparar("M5_guardia_con_via")
    j = leer(d / "guardia" / "Lascar.json")
    for rec in j["records"][-3:]:
        rec["via_codigo_mirova"] = True
    escribir(d / "guardia" / "Lascar.json", j)
    r, _ = correr(d)
    resultados["M5_guardia_con_3_records_marcados_via (esperado VIGILANCIA_CIEGA)"] = r

    print(json.dumps(resultados, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
