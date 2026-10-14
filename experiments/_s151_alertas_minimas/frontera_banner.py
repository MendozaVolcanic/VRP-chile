# -*- coding: utf-8 -*-
"""Estudio D, parte 2: donde esta la frontera NONE / VERY LOW del banner de MIROVA, y si depende del sensor.

POR QUE. Si MIROVA no llama anomalia a una pasada de 0,03 MW, contarla como alerta en la suma de errores mide
la replica contra el scraper y no contra MIROVA. Hace falta la frontera exacta, y saber si es un corte en el VRP
(con el redondeo a 2 decimales del valor publicado) o si depende de otra cosa.

Tres muestras, de dos instrumentos distintos:
  A. Banner leido por el OCR de Mirova-v1 (columna Nivel_Anomalia_MIROVA, version 30, agosto a octubre).
  B. Color de la estrella del grafico de distancias, segun la nota del OCR (version 29 en adelante): el autor
     del scraper la documenta como gris = "deteccion debil sub-umbral del banner" (ocr_utils.py V29).
  C. Banner leido por nosotros en las imagenes VRP de mayo del archivo local (leer_png_mirova.py), pareado a
     la pasada de la referencia por volcan, sensor y hora (+-120 s). Es la unica muestra con MODIS y VIIRS 750.

Hipotesis y control que puede fallar. H: el banner dice NONE si el VRP verdadero esta bajo un umbral T entre
0,045 y 0,055 MW, y el VRP publicado es el verdadero redondeado a 2 decimales. H predice CERO NONE con VRP
publicado de 0,06 o mas y CERO VERY LOW con 0,04 o menos; solo 0,05 puede salir de los dos lados. Se cuentan las
violaciones de cada regla "NONE si VRP <= c" para c de 0,02 a 0,08: si las muestras no tuvieran poder, todas
las reglas darian cero violaciones y el resultado no diria nada (A110); las reglas desplazadas tienen que fallar.

Uso: python frontera_banner.py > frontera_salida.txt
"""
import csv
import io
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from comun import RAIZ, cargar_referencia_unificada  # noqa: E402
import leer_png_mirova as L  # noqa: E402
from pipeline.mirova_csv_loader import normalize_sensor, normalize_volcano_name  # noqa: E402

OCR = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_ocr.csv"
CORTES = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def tabla(pares, titulo, hasta=0.12):
    """pares: lista de (vrp, banner). Imprime conteo por valor publicado y las violaciones por regla."""
    print(f"  {titulo}: n={len(pares)}")
    por = defaultdict(Counter)
    for v, b in pares:
        if v is not None and 0 < v <= hasta + 1e-9:
            por[round(v, 2)][b] += 1
    for v in sorted(por):
        print(f"     VRP {v:.2f}  " + "  ".join(f"{b} {n}" for b, n in sorted(por[v].items())))
    altos = Counter(b for v, b in pares if v is not None and v > hasta)
    print(f"     VRP > {hasta:.2f}: {dict(altos)}")
    viol = {}
    for c in CORTES:
        e = sum(1 for v, b in pares if v is not None and v > 0 and ((b == "NONE") != (round(v, 2) <= c + 1e-9)))
        viol[c] = e
    print("     violaciones de la regla 'NONE si VRP <= c': " + "  ".join(f"c={c:.2f}: {e}" for c, e in viol.items()))
    h = sum(1 for v, b in pares if v is not None and v > 0 and round(v, 2) != 0.05
            and ((b == "NONE") != (round(v, 2) <= 0.04 + 1e-9)))
    print(f"     H (redondeo, umbral entre 0,045 y 0,055): violaciones fuera de 0,05 = {h}")
    return viol, h


def muestra_a():
    pares, por_sensor, vs_cons = [], defaultdict(list), []
    filas = list(csv.DictReader(open(OCR, encoding="utf-8")))
    for r in filas:
        b = (r.get("Nivel_Anomalia_MIROVA") or "").strip().upper()
        v = _f(r.get("VRP_MW"))
        if b and v is not None:
            pares.append((v, b))
            por_sensor[normalize_sensor(r["Sensor"])].append((v, b))
    return pares, por_sensor, filas


def muestra_b(filas):
    out = []
    for r in filas:
        nota = r.get("Nota_Validacion") or ""
        m = re.search(r"Estrella (gris|verde)", nota)
        v = _f(r.get("VRP_MW"))
        if m and v is not None:
            out.append((v, "NONE" if m.group(1) == "gris" else "VERDE", r.get("Version_OCR", ""),
                        (r.get("Nivel_Anomalia_MIROVA") or "").strip().upper(), normalize_sensor(r["Sensor"])))
    return out


def main():
    print("== A. Banner leido por el OCR de Mirova-v1 (Nivel_Anomalia_MIROVA, snapshot del repo)")
    pares_a, por_sensor_a, filas_ocr = muestra_a()
    print("   cobertura por sensor y banner:", {s: dict(Counter(b for _, b in p)) for s, p in por_sensor_a.items()})
    va, ha = tabla(pares_a, "todas las filas con banner (los tres sensores)")
    print("   corte VERY LOW / LOW (1 MW) por sensor:")
    for s, p in sorted(por_sensor_a.items()):
        mal = sum(1 for v, b in p if b in ("VERY_LOW", "LOW") and ((b == "LOW") != (v >= 1.0)))
        print(f"     {s:8s} filas VERY LOW o LOW {sum(b in ('VERY_LOW', 'LOW') for _, b in p)}, en el lado equivocado de 1 MW: {mal}")
    # El VRP del OCR contra el del consolidado para la misma pasada: el umbral se mide sobre el valor publicado.
    ref = cargar_referencia_unificada()
    cons = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]): f["vrp_mw"] for f in ref if f["source"] == "CONS"}
    igual = dif = sin = 0
    for r in filas_ocr:
        if not (r.get("Nivel_Anomalia_MIROVA") or "").strip():
            continue
        k = (normalize_volcano_name(r["Volcan"]), normalize_sensor(r["Sensor"]), r["Fecha_Satelite_UTC"][:16])
        if k not in cons:
            sin += 1
        elif abs((cons[k] or 0) - float(r["VRP_MW"])) < 1e-9:
            igual += 1
        else:
            dif += 1
    print(f"   VRP del OCR contra el del consolidado en la misma pasada (filas con banner): igual {igual}, distinto {dif}, sin fila en el consolidado {sin}")
    print("   detalle de 0,04 a 0,06 MW (para ver si algo distinto del VRP separa el borde, por ejemplo la distancia):")
    for r in sorted(filas_ocr, key=lambda r: (r["VRP_MW"], r["Fecha_Satelite_UTC"])):
        b = (r.get("Nivel_Anomalia_MIROVA") or "").strip()
        if b and 0.035 < float(r["VRP_MW"]) < 0.065:
            print(f"     {r['VRP_MW']:5s} {b:9s} {r['Volcan'][:14]:14s} {r['Fecha_Satelite_UTC']}  dist {r['Distancia_km']} km  cenit {r.get('Zenith_Sat_deg')}")

    print()
    print("== B. Color de la estrella del grafico de distancias (nota del OCR, version 29 en adelante)")
    pares_b = muestra_b(filas_ocr)
    print("   por version:", dict(Counter(x[2] for x in pares_b)), "| por sensor:", dict(Counter(x[4] for x in pares_b)))
    cruce = Counter((x[1], x[3]) for x in pares_b if x[3])
    print("   estrella contra banner, filas que tienen los dos:", dict(cruce))
    vb, hb = tabla([(x[0], x[1]) for x in pares_b], "estrella gris = NONE, verde = anomalia")
    # Las filas solo OCR pueden llevar la imagen de OTRA pasada (Suomi NPP, arreglo en Mirova-v1#20, A119): el VRP
    # es de la suya pero la estrella sale del grafico de distancias de otra. Se separan las filas cuya pasada
    # tambien esta en el consolidado con el mismo VRP, que son las que no dependen de ese defecto.
    con_cons, solo_ocr = [], []
    for r in filas_ocr:
        m = re.search(r"Estrella (gris|verde)", r.get("Nota_Validacion") or "")
        v = _f(r.get("VRP_MW"))
        if not m or v is None:
            continue
        k = (normalize_volcano_name(r["Volcan"]), normalize_sensor(r["Sensor"]), r["Fecha_Satelite_UTC"][:16])
        par = (v, "NONE" if m.group(1) == "gris" else "VERDE")
        (con_cons if k in cons and abs((cons[k] or 0) - v) < 1e-9 else solo_ocr).append(par)
    vb2, hb2 = tabla(con_cons, "estrella, solo pasadas tambien en el consolidado con el mismo VRP")
    _, hb3 = tabla(solo_ocr, "estrella, filas sin par en el consolidado (pueden llevar la imagen de otra pasada)")

    print()
    print("== C. Banner leido en las imagenes VRP de mayo del archivo local (tres sensores)")
    imgs = L.leer_archivo()
    print(f"   imagenes VRP de un sensor: {len(imgs)}; hora leida: {sum(i['hora'] is not None for i in imgs)}; "
          f"lectura del banner por mascara y por color coinciden: {sum(i['banner_mascara'] == i['banner_color'] for i in imgs)}")
    # Control de la hora leida: la adquisicion tiene que ser anterior a la fecha de modificacion del archivo.
    gaps = []
    for i in imgs:
        lm = datetime.fromisoformat(i["last_modified"])
        gaps.append((lm - i["hora"]).total_seconds() / 3600)
    gaps.sort()
    print(f"   control de la hora: adquisicion posterior a la modificacion del archivo en {sum(g < -0.01 for g in gaps)} imagenes; "
          f"desfase en horas: mediana {gaps[len(gaps) // 2]:.1f}, p95 {gaps[int(len(gaps) * .95)]:.1f}, max {gaps[-1]:.1f}")
    pasadas = {}
    conflicto = 0
    for i in imgs:
        k = (i["volcano"], i["sensor"], i["hora"])
        if k in pasadas and pasadas[k] != i["banner_mascara"]:
            conflicto += 1
        pasadas.setdefault(k, i["banner_mascara"])
    print(f"   pasadas distintas (volcan, sensor, hora): {len(pasadas)}; con dos banners distintos entre copias: {conflicto}")
    idx = defaultdict(list)
    for f in ref:
        dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        idx[(f["volcano"], f["sensor_bucket"])].append((dt, f))
    pares_c = defaultdict(list)
    sin_par = Counter()
    vrp0 = Counter()
    for (vol, sen, hora), ban in pasadas.items():
        cand = [f for dt, f in idx.get((vol, sen), []) if abs((dt - hora).total_seconds()) <= 120]
        if not cand:
            sin_par[sen] += 1
            continue
        cand.sort(key=lambda f: (f["source"] != "CONS", f["origen"] != "principal"))
        v = cand[0]["vrp_mw"]
        if not v:
            vrp0[(sen, ban)] += 1
            continue
        pares_c[sen].append((v, ban))
        if 0.035 < v < 0.065 or (sen == "VIIRS750" and v < 0.2):
            print(f"     detalle C: {sen} {v:.2f} {ban:9s} {vol:20s} {hora:%Y-%m-%d %H:%M}  dist {cand[0]['dist_km']} km  {cand[0]['tipo']}")
    print(f"   sin pasada en la referencia a +-120 s: {dict(sin_par)}")
    print(f"   pareadas con VRP 0 en la referencia (sensor, banner): {dict(vrp0)}")
    vc = {}
    for s in ("VIIRS375", "VIIRS750", "MODIS"):
        vc[s] = tabla(pares_c[s], f"{s}, pasadas con VRP > 0", hasta=1.2)
        mal = sum(1 for v, b in pares_c[s] if b in ("VERY_LOW", "LOW") and ((b == "LOW") != (v >= 1.0)))
        print(f"     corte VERY LOW / LOW en 1 MW, filas en el lado equivocado: {mal} de {sum(b in ('VERY_LOW', 'LOW') for _, b in pares_c[s])}")

    print()
    print("== RESUMEN del control")
    todas = {"A (OCR banner)": va, "B (estrella)": vb, "B con par en CONS": vb2, "C VIIRS375 (mayo)": vc["VIIRS375"][0]}
    for n, v in todas.items():
        mejor = min(v.values())
        print(f"   {n:20s} reglas con el minimo de violaciones ({mejor}): "
              f"{[c for c, e in v.items() if e == mejor]} | reglas desplazadas c=0,03 y c=0,06: {v[0.03]}, {v[0.06]}")
    print(f"   H fuera de 0,05: A {ha}, B {hb} (con par en CONS {hb2}, sin par {hb3}), C VIIRS375 {vc['VIIRS375'][1]}, C VIIRS750 {vc['VIIRS750'][1]}, C MODIS {vc['MODIS'][1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
