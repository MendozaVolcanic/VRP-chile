# -*- coding: utf-8 -*-
"""S165 V375-E: compara record por record el JSON de un volcán producido por main y por la rama de la vía de VIIRS 375.

Es `experiments/_s162_v750a/comparar_bitabit_nrt.py` (#907) con el sensor que cambia: aquí VIIRS 375 (I-band), cuyos
records se llaman VIIRS_SNPP, VIIRS_NOAA20 y VIIRS_NOAA21, sin el sufijo _750 (A48: no adivinar la convención). La
corrida la despacha la coordinadora con `experiments/_s162_v750a/probe-s162-bitabit-nrt.yml`, que ya procesa todos los
sensores del día con los dos árboles en el MISMO runner (S152: dos runners pueden desempatar distinto).
Ignora sólo la hora de proceso (`processed_utc`, `first_processed_utc`), que cambia entre corridas por construcción.
Instrumento: si en alguno de los dos lados no hay un solo record de VIIRS 375 el resultado es SIN DATO (salida 2), no
VERDE; si algún record de la rama trae `via_codigo_mirova`, el flag no estaba apagado y es ROJO (salida 1).
Control de que la comparación puede fallar: `--autoprueba` corre tres casos sintéticos (iguales, uno con la marca de la
vía, sin 375) y exige VERDE, ROJO y SIN DATO; con un caso real, `--control` pone la marca en la rama y exige ROJO.
Uso: python comparar_bitabit_nrt_v375.py <json de main> <json de la rama> [--control]
     python comparar_bitabit_nrt_v375.py --autoprueba
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

IGNORAR = ("processed_utc", "first_processed_utc")
SENSORES_375 = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")


def cargar(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return indexar(d if isinstance(d, list) else d.get("records", d))


def indexar(recs):
    recs = copy.deepcopy(recs)
    for r in recs:
        for k in IGNORAR:
            r.pop(k, None)
    return {(r.get("datetime_utc"), r.get("sensor")): r for r in recs}


def comparar(A, B, imprimir=print):
    marcados = [k for k, r in B.items() if "via_codigo_mirova" in r]
    solo_a, solo_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    distintos = [k for k in sorted(set(A) & set(B)) if json.dumps(A[k], sort_keys=True) != json.dumps(B[k], sort_keys=True)]
    imprimir(f"records main {len(A)} rama {len(B)} | sólo en main {len(solo_a)} | sólo en la rama {len(solo_b)} | "
             f"distintos {len(distintos)} | con la marca de la vía {len(marcados)}")
    for k in (solo_a + solo_b + distintos + marcados)[:20]:
        imprimir(f"    {k}")
    por_sensor = lambda D: {s: sum(1 for k in D if k[1] == s) for s in sorted({str(k[1]) for k in D})}  # noqa: E731
    imprimir(f"   por sensor, main: {por_sensor(A)} | rama: {por_sensor(B)}")
    n375 = [sum(1 for k in D if k[1] in SENSORES_375) for D in (A, B)]
    if min(n375) == 0:
        imprimir(f"== bit a bit: SIN DATO (records de VIIRS 375: main {n375[0]}, rama {n375[1]})")
        return 2
    bien = not (solo_a or solo_b or distintos or marcados)
    imprimir(f"== bit a bit: {'VERDE' if bien else 'ROJO'}")
    return 0 if bien else 1


def autoprueba():
    base = [{"datetime_utc": "2026-10-10 06:54", "sensor": "VIIRS_NOAA20", "vrp_mw": 1.2, "processed_utc": "a"},
            {"datetime_utc": "2026-10-10 05:30", "sensor": "VIIRS_NOAA20_750", "vrp_mw": 0.4, "processed_utc": "a"}]
    otra = copy.deepcopy(base)
    otra[0]["processed_utc"] = "b"
    marca = copy.deepcopy(otra)
    marca[0]["via_codigo_mirova"] = True
    sin375 = [base[1]]
    casos = [("iguales salvo la hora de proceso", base, otra, 0), ("la rama con la marca de la vía", base, marca, 1),
             ("sin records de 375", sin375, sin375, 2)]
    ok = True
    for nombre, a, b, esperado in casos:
        rc = comparar(indexar(a), indexar(b), imprimir=lambda *_: None)
        ok &= rc == esperado
        print(f"autoprueba {nombre}: salida {rc}, esperada {esperado} {'OK' if rc == esperado else 'NO'}")
    print("== autoprueba:", "OK" if ok else "FALLA")
    return 0 if ok else 1


def main(argv):
    if argv[:1] == ["--autoprueba"]:
        return autoprueba()
    A, B = cargar(argv[0]), cargar(argv[1])
    if "--control" in argv[2:]:
        for k, r in B.items():
            if k[1] in SENSORES_375:
                r["via_codigo_mirova"] = True
                break
        rc = comparar(A, B)
        print("== control (marca puesta en la rama):", "OK, da ROJO" if rc == 1 else "FALLA, la comparación no lo ve")
        return 0 if rc == 1 else 1
    return comparar(A, B)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
