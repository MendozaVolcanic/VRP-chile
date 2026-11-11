#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría S179, frente B. Simulacro del vigilante de la guardia K de VIIRS con datos reales.

POR QUÉ. La regla de reversión de VIIRS (sellada el 2026-11-10) dispara con cotas calibradas sobre datos anteriores a
noviembre. Nadie corrió el vigilante real sobre la única semana en que ya existen los dos lados: la sombra (las vías
encendidas, data/sombra_codigo_mirova) y producción (K, data/mirova_equivalent). Este script usa las funciones del
vigilante de main 438a60a1e sin copiarlas (import) y sólo cambia los papeles: «producción» = la sombra (lo que
producción publicará con B1 y B2) y «guardia» = producción de hoy (K). Así se ve qué habría informado el vigilante
si la vía hubiese estado encendida desde la primera noche de la sombra.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si lo que mido estuviera roto, ¿lo vería? Control positivo: un brazo mudo (la «producción» nunca publica) tiene que
   dar candidatas a reversión y Muy Bajo perdidas. Control de sobre-publicación: una «producción» que siempre publica
   tiene que dar sobre-publicación mayor que 0.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Control nulo: K contra K tiene que dar 0 y 0 CON pares
   mayores que 0 (un 0 con 0 pares es SIN DATO). Además se informa cada denominador.

Base: código main 438a60a1e (instantánea D:/vrp-trabajo/temporales/s179-audit/main, sha256 comprobado contra git show);
datos de 438a60a1e extraídos con git show a D:/vrp-trabajo/temporales/s179-audit/b/datos. Referencia (la vara del
plan): latest_consolidado.csv de 438a60a1e y data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv.
No escribe nada fuera de su carpeta. No llama a NASA ni a GitHub.
"""
import copy
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAIN = Path(r"D:\vrp-trabajo\temporales\s179-audit\main")
DATOS = Path(r"D:\vrp-trabajo\temporales\s179-audit\b\datos")
AQUI = Path(__file__).resolve().parent
os.environ["VRP_PROFILE"] = "mirova_equivalent"
for p in (str(MAIN), str(MAIN / "scripts")):
    sys.path.insert(0, p)

import vigilancia_guardia_viirs as vv  # noqa: E402
import banco_paridad as bp  # noqa: E402
import referencia_mirova_unificada as rmu  # noqa: E402

vg, vs, aa = vv.vg, vv.vs, vv.aa
CONS = MAIN / "latest_consolidado.csv"
OCR = DATOS / "ref" / "registro_vrp_ocr.csv"
RESPALDO = DATOS / "ref" / "registro_vrp_consolidado_respaldo_20260408.csv"
HISTORICO = DATOS / "union" / "consolidado_filas_perdidas.csv"
PROD_K = DATOS / "mirova_equivalent"
SOMBRA = DATOS / "sombra_codigo_mirova"
GUARDIA = DATOS / "guardia_k_viirs"
HOY = "2026-11-10"
SENSORES = ["VIIRS375", "VIIRS750"]


def referencia():
    return rmu.cargar_referencia_unificada(CONS, OCR, respaldo_path=RESPALDO, historico_path=HISTORICO)


def crudos(carpeta):
    raw = {}
    for vol in aa.VOLS:
        with open(Path(carpeta) / f"{vol}.json", encoding="utf-8") as fh:
            raw[vol] = json.load(fh).get("records") or []
    return raw


def cargar_lado(carpeta, sensor, win, coords, inner):
    """Records de un lado con el predicado del tablero (node), marcados con `via` y `caida_k` como hace el vigilante."""
    enc = vg.encendido_desde_datos(crudos(carpeta), sensor=sensor)
    recs = [r for r in bp.cargar_nuestros(coords, inner, win, data=carpeta) if r["b"] == sensor]
    for r in recs:
        clave = (r["vol"], r.get("sensor"), r["dt"].strftime("%Y-%m-%d %H:%M"))
        r["via"] = clave in enc["via"]
        r["caida_k"] = enc["caidas"].get(clave)
    return recs, enc


def poisson_sf(k, lam):
    """P(X > k) con X ~ Poisson(lam)."""
    if lam <= 0:
        return 0.0
    acc, term = 0.0, math.exp(-lam)
    for i in range(k + 1):
        acc += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - acc)


def resumen(nombre, d, pasadas, prod, guardia, sensor, dias):
    mb, sp = d["muy_bajo"], d["sobrepublicacion"]
    prot = [p for p in pasadas if p["protegida"] and p["instante_utc"] >= (d["duracion"]["encendido"] or "9999")]
    por_vol = Counter(p["volcano"] for p in prot)
    out = {
        "escenario": nombre, "sensor": sensor, "veredicto": d["veredicto"], "dias_ventana": dias,
        "encendido": d["duracion"]["encendido"],
        "protegidas_posteriores": len(prot), "protegidas_por_volcan": dict(por_vol),
        "protegidas_vistas_en_guardia": d["duracion"]["protegidas_vistas_en_guardia"],
        "n_reversion": len(d["reversion"]),
        "reversion": [(p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]) for p in d["reversion"]],
        "n_fuera_de_plazo": len(d["fuera_de_plazo"]),
        "n_sin_record": len(d["protegidas_sin_record_produccion"]),
        "sin_record": [(p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]) for p in d["protegidas_sin_record_produccion"]],
        "n_calladas_por_k": len(d["protegidas_calladas_por_k_de_produccion"]),
        "muy_bajo_k": mb["k"], "muy_bajo_n": mb["n"], "muy_bajo_cota": mb["cota"], "muy_bajo_dispara": mb["dispara"],
        "muy_bajo_pasadas": [(p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"]) for p in mb["pasadas"]],
        "sobrepub_k": sp["k"], "sobrepub_n": sp["n"], "sobrepub_cota": sp["cota"], "sobrepub_dispara": sp["dispara"],
        "sobrepub_pasadas": [(p["volcano"], p["fecha_utc"]) for p in sp["pasadas"]],
        "borde_171_01_total": d["borde_171_01"]["total"],
        "nulo_pares": d["nulo"]["pares"], "nulo_distintas": d["nulo"]["distintas"],
        "n_prod": len(prod), "n_guardia": len(guardia),
        "n_prod_via": sum(1 for r in prod if r.get("via") is True),
        "prod_lab": dict(Counter(r.get("lab") for r in prod)),
    }
    if dias:
        for clave, k, cota in (("muy_bajo", mb["k"], mb["cota"]), ("sobrepub", sp["k"], sp["cota"])):
            lam120 = k / dias * 120.0
            out[f"{clave}_proyeccion_120d"] = round(lam120, 2)
            out[f"{clave}_p_superar_cota_si_tasa_sigue"] = round(poisson_sf(cota, lam120), 4) if cota is not None else None
    return out


def imprimir(o):
    print(f"\n--- {o['escenario']} · {o['sensor']} · veredicto {o['veredicto']} · encendido {o['encendido']} · "
          f"{o['dias_ventana']} días")
    print(f"    records: producción {o['n_prod']} (de la vía {o['n_prod_via']}), guardia {o['n_guardia']}; etiquetas "
          f"de producción {o['prod_lab']}")
    print(f"    protegidas posteriores al encendido: {o['protegidas_posteriores']} {o['protegidas_por_volcan']}; "
          f"vistas en la guardia (plazo 29): {o['protegidas_vistas_en_guardia']}")
    print(f"    reversión candidata: {o['n_reversion']} {o['reversion']}; fuera de plazo {o['n_fuera_de_plazo']}; "
          f"sin record de producción {o['n_sin_record']} {o['sin_record']}; calladas por K {o['n_calladas_por_k']}")
    print(f"    (i) Muy Bajo que la guardia publica y producción calla: {o['muy_bajo_k']} de {o['muy_bajo_n']} "
          f"(cota {o['muy_bajo_cota']}; dispara {o['muy_bajo_dispara']}) {o['muy_bajo_pasadas']}")
    print(f"    (ii) negativos limpios que producción publica y la guardia no: {o['sobrepub_k']} de {o['sobrepub_n']} "
          f"(cota {o['sobrepub_cota']}; dispara {o['sobrepub_dispara']}) {o['sobrepub_pasadas']}")
    if o.get("muy_bajo_proyeccion_120d") is not None:
        print(f"    proyección a 120 días si la tasa de esta ventana siguiera: (i) {o['muy_bajo_proyeccion_120d']} "
              f"(P de superar la cota {o['muy_bajo_p_superar_cota_si_tasa_sigue']}); (ii) "
              f"{o['sobrepub_proyeccion_120d']} (P {o['sobrepub_p_superar_cota_si_tasa_sigue']})")
    print(f"    guardia registra y producción no (iii): {o['borde_171_01_total']}; nulo: {o['nulo_distintas']} "
          f"distintas de {o['nulo_pares']} pares")


def correr(nombre, prod, guardia, filas, sensor, win, encendido, coords, hoy=HOY):
    prod = copy.deepcopy(prod)
    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])
    pasadas = vg.pasadas_modis(filas, prod, guardia, win, diurna=vs._diurna_por_defecto(), sensor=sensor)
    d = vg.disparadores(pasadas, prod, guardia, hoy, encendido, juzgadas={}, ahora=f"{hoy} 23:59:59", sensor=sensor,
                        cotas=vv.COTAS[sensor])
    dias = None
    if encendido:
        dias = round((datetime.strptime(f"{hoy} 23:59:59", "%Y-%m-%d %H:%M:%S")
                      - datetime.strptime(encendido, "%Y-%m-%d %H:%M:%S")).total_seconds() / 86400.0, 2)
    o = resumen(nombre, d, pasadas, prod, guardia, sensor, dias)
    imprimir(o)
    return o, d, pasadas, prod


def main():
    print(f"== simulacro del vigilante de VIIRS · código main 438a60a1e · hoy simulado {HOY}")
    print(f"   referencia: {CONS.name} + {OCR.name}; cotas del vigilante: {vv.COTAS}")
    coords = aa._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = referencia()
    fechas = [f["fecha_utc"][:10] for f in filas if (f.get("fecha_utc") or "")[:4].isdigit()]
    print(f"   filas de referencia {len(filas)}; última fecha {max(fechas)}")
    win = ("2026-10-20", HOY)
    salida = []
    for sensor in SENSORES:
        print(f"\n================ {sensor}")
        sombra, enc_s = cargar_lado(SOMBRA, sensor, win, coords, inner)
        prodk, enc_k = cargar_lado(PROD_K, sensor, win, coords, inner)
        guardia, enc_g = cargar_lado(GUARDIA, sensor, win, coords, inner)
        noches_s = sorted({r["noche"] for r in sombra})
        noches_g = sorted({r["noche"] for r in guardia})
        print(f"   sombra: {len(sombra)} records nocturnos, noches {noches_s[0]} a {noches_s[-1]} ({len(noches_s)}); "
              f"de la vía {sum(1 for r in sombra if r['via'])}; caídas a K {sum(1 for r in sombra if r['caida_k'])}; "
              f"menor processed_utc de la vía {enc_s['encendido_utc']}; primera observación {enc_s['primera_observacion']}")
        print(f"   producción K: {len(prodk)} records nocturnos en la ventana; de la vía {sum(1 for r in prodk if r['via'])}")
        print(f"   guardia K de VIIRS: {len(guardia)} records, noches {noches_g[0]} a {noches_g[-1]} ({len(noches_g)})")
        primera = min(r["dt"] for r in sombra if r["via"]).strftime("%Y-%m-%d %H:%M:%S")

        # A. Simulacro: producción := sombra (vía), guardia := producción de hoy (K). Encendido := primera observación.
        o, d, pasadas, prod_et = correr("A. sombra como producción, K de producción como guardia", sombra, prodk, filas,
                                        sensor, win, primera, coords)
        salida.append(o)
        # A2. Igual, con la guardia K de VIIRS real como guardia (cubre menos noches).
        o2, *_ = correr("A2. sombra como producción, guardia K de VIIRS real como guardia", sombra, guardia, filas,
                        sensor, win, primera, coords)
        salida.append(o2)
        # A3. Igual que A, encendido := menor processed_utc de la vía en la sombra (como lo define la regla §4.1).
        o3, *_ = correr("A3. como A, encendido = menor processed_utc de la sombra", sombra, prodk, filas, sensor, win,
                        enc_s["encendido_utc"], coords)
        salida.append(o3)

        # N. Control nulo: K contra K (producción de hoy en los dos lados), marcando «vía» para que entren a las cotas.
        prodk_como_via = copy.deepcopy(prodk)
        for r in prodk_como_via:
            r["via"] = True
        on, *_ = correr("N. control nulo: K contra K (tiene que dar 0 y 0, con n mayor que 0)", prodk_como_via, prodk,
                        filas, sensor, win, primera, coords)
        salida.append(on)
        # M. Control positivo: brazo mudo (la «producción» nunca publica).
        mudo = copy.deepcopy(prodk_como_via)
        for r in mudo:
            r["pub"] = 0
        om, *_ = correr("M. control positivo: producción muda (tiene que dar reversión y Muy Bajo)", mudo, prodk, filas,
                        sensor, win, primera, coords)
        salida.append(om)
        # P. Control positivo de (ii): una «producción» que siempre publica.
        todo = copy.deepcopy(prodk_como_via)
        for r in todo:
            r["pub"] = 1
        op, *_ = correr("P. control positivo: producción que siempre publica (sobre-publicación mayor que 0)", todo,
                        prodk, filas, sensor, win, primera, coords)
        salida.append(op)

        # Detalle de A: cada pasada con alerta de MIROVA posterior al encendido, con lo que hizo cada lado.
        print("\n   detalle de A (pasadas nocturnas con alerta de MIROVA desde la primera noche de la sombra):")
        cuenta = Counter()
        for p in pasadas:
            if p["instante_utc"] < primera:
                continue
            clase = "protegida" if p["protegida"] else ("minima" if p["minima"] else "muy_bajo")
            cuenta[(clase, p["guardia_pub"], p["prod_pub"])] += 1
        for (clase, g, pr), n in sorted(cuenta.items(), key=lambda x: str(x)):
            print(f"      {clase:10s} guardia_pub={g} via_pub={pr}: {n}")
    with open(AQUI / "re_sim_vigilancia_salida.json", "w", encoding="utf-8") as fh:
        json.dump(salida, fh, indent=1, ensure_ascii=False, default=str)
    print("\nsalida 0")


if __name__ == "__main__":
    main()
