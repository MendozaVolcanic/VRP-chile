# -*- coding: utf-8 -*-
"""banco_paridad (recall por pasada en positivos y publicacion en negativos limpios) con los tres pareos,
sobre el espejo de origin/main de hoy, y el detalle de cada pasada fisica cuya etiqueta o publicacion cambia.

Pregunta 1: si el pareo perdiera pasadas, lo veria? Si: comparo pasada a pasada (cadena de granulos) la
etiqueta y la publicacion entre "hoy" y "orbita", y cuento las de "ancha".
Pregunta 2: instrumento vivo: control positivo Chillan 2026-01-19 02:40 MODIS (sin_info hoy; con fila RUTINA
de MIROVA en el granulo de las 02:35 debe pasar a neg_limpio o a otra etiqueta con denominador) y control
sintetico de alertas_protegidas (una alerta a +5 min de un record que publica: hoy sin_record, ancha publicada).
Ventanas: --inicio a --fin, noches UTC; referencia = snapshot de origin/main + respaldo + union historica.
"""
import argparse
import collections
import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent))
import variantes  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--raiz", required=True)
ap.add_argument("--inicio", default="2026-03-01")
ap.add_argument("--fin", default="2026-10-21")
ap.add_argument("--regla", default="original")
ap.add_argument("--out", required=True)
a = ap.parse_args()
ventana = (a.inicio, a.fin)
bp, aaw = variantes.cargar(a.raiz)
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402

coords = aaw._coords_por_volcan()
inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
idx = bp.indexar_referencia(filas, coords, ventana, regla_minimas=a.regla)
por_vb, noche_sensor, noche_volcan, n_ref = idx

# un solo paso por node: los recs se copian para cada variante
orig = {"cargar": bp.cargar_nuestros, "etiquetar": bp.etiquetar, "parear": bp.parear,
        "sin_record": bp.alertas_sin_record, "TOL_S": bp.TOL_S, "TOL_P": aaw.TOL_PASADA_S}
recs0 = bp.cargar_nuestros(coords, inner, ventana)


def restaurar():
    bp.cargar_nuestros, bp.etiquetar, bp.parear = orig["cargar"], orig["etiquetar"], orig["parear"]
    bp.alertas_sin_record, bp.TOL_S, aaw.TOL_PASADA_S = orig["sin_record"], orig["TOL_S"], orig["TOL_P"]


res, recs_v = {}, {}
for v in ("hoy", "ancha", "orbita"):
    restaurar()
    reg = {}
    variantes.aplicar(bp, aaw, v, reg)
    base = copy.deepcopy(recs0)
    if v == "orbita":
        orig_cargar_interno = orig["cargar"]
        bp_cargar = bp.cargar_nuestros
        # cargar_nuestros parcheado llama al original: le entrego los recs ya calculados
        bp.cargar_nuestros = orig_cargar_interno
        import types  # noqa: E402
        recs = None
        f = bp_cargar.__closure__
        # reconstruyo el colapso sin volver a llamar a node: original_cargar es la primera celda libre
        nombres = bp_cargar.__code__.co_freevars
        celdas = dict(zip(nombres, f))
        celdas["original_cargar"].cell_contents = lambda *x, **k: base
        recs = bp_cargar(coords, inner, ventana)
    else:
        recs = base
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    sin_rec = bp.alertas_sin_record(por_vb, recs)
    por_sensor, por_volcan = bp.resumen(recs, sin_rec)
    res[v] = {"por_sensor": por_sensor, "por_volcan": por_volcan, "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
              "n_unidades": len(recs), "registro": {k: (dict(x) if hasattr(x, "items") else x) for k, x in reg.items()}}
    recs_v[v] = recs
restaurar()

# detalle por pasada fisica: hoy (records) contra orbita (cadenas)
hoy_por = {(r["vol"], r["b"], r["sensor"], r["dt"]): r for r in recs_v["hoy"]}
cambios = []
for c in recs_v["orbita"]:
    miembros = [hoy_por[(c["vol"], c["b"], c["sensor"], h)] for h in c["horas_cadena"]]
    con_etq = [m for m in miembros if m["lab"] != "sin_info"]
    hoy_lab = con_etq[0]["lab"] if con_etq else "sin_info"
    hoy_pub = con_etq[0]["pub"] if con_etq else None     # la publicacion que el banco de hoy ve
    if (hoy_lab, hoy_pub) != (c["lab"], c["pub"] if c["lab"] != "sin_info" else None):
        cambios.append({"vol": c["vol"], "b": c["b"], "sensor": c["sensor"],
                        "horas": [h.strftime("%Y-%m-%d %H:%M") for h in c["horas_cadena"]],
                        "pub_por_hora": c["pub_por_hora"], "hoy": [hoy_lab, hoy_pub], "orbita": [c["lab"], c["pub"]],
                        "labs_hoy_miembros": [m["lab"] for m in miembros], "z": c.get("z")})

# control positivo
ctrl = [x for x in cambios if x["vol"] == "NevadosDeChillan" and x["horas"][0] == "2026-01-19 02:40"]

# control sintetico de alertas_protegidas: alerta a +5 min de un record que publica
t0 = datetime(2026, 10, 1, 7, 0, tzinfo=timezone.utc)
recs_s = [{"vol": "Lascar", "b": "MODIS", "dt": t0, "noche": "2026-10-01", "pub": 1, "sha": "x", "sensor": "MODIS_AQUA"}]
filas_s = [{"volcano": "Lascar", "sensor_bucket": "MODIS", "fecha_utc": "2026-10-01 07:05:00", "tipo": "ALERTA_TERMICA",
            "vrp_mw": 2.0, "source": "CONS", "dist_km": 1.0}]
sint = {}
for tol in (120, 390):
    aaw.TOL_PASADA_S = tol
    sint[tol] = [p["estado"] for p in aaw.alertas_protegidas(filas_s, recs_s, ("2026-10-01", "2026-10-01"), "2026-09-18",
                                                             diurna=lambda *x: False)]
aaw.TOL_PASADA_S = orig["TOL_P"]

# pasadas partidas (cadena de 2) contra enteras, en la variante orbita, por sensor y etiqueta
partidas = collections.defaultdict(lambda: [0, 0])
quien = collections.Counter()
for c in recs_v["orbita"]:
    partidas[f'{c["b"]}|{c["lab"]}|cadena{c["n_cadena"]}'][0] += c["pub"]
    partidas[f'{c["b"]}|{c["lab"]}|cadena{c["n_cadena"]}'][1] += 1
    if c["n_cadena"] == 2 and c["lab"] in ("pos", "neg_limpio"):
        quien[(c["b"], c["lab"], tuple(c["pub_por_hora"]))] += 1
partidas = {k: {"pub": v[0], "n": v[1]} for k, v in sorted(partidas.items())}
salida = {"partidas_vs_enteras": partidas, "quien_publica_en_partidas": {str(k): v for k, v in quien.items()},
          "ventana": ventana, "regla_minimas": a.regla, "n_filas_ref_nocturnas": n_ref, "resultados": res,
          "cambios_hoy_vs_orbita": cambios, "control_positivo_chillan_0119": ctrl, "control_sintetico_protegidas": sint}
Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

print(f"ventana {ventana} regla {a.regla} filas ref nocturnas {n_ref}")
for v in res:
    print(f"== {v}: unidades {res[v]['n_unidades']} etiquetas {res[v]['etiquetas']} {res[v]['registro']}")
    for b in bp.BUCKETS:
        p = res[v]["por_sensor"][b]["pasada"]
        n = res[v]["por_sensor"][b]["noche_volcan"]
        print(f"   {b:9s} recall pos {p['recall_pos']} (n {p['n_pos']}) pub_neg {p['tasa_pub_neg']} (n {p['n_neg_limpio']}) "
              f"pos_sin_record {p['pos_sin_record']} | noche recall {n['recall_pos']} (n {n['n_pos']}) pub_neg {n['tasa_pub_neg']} (n {n['n_neg']})")
print("cambios hoy -> orbita por (b, hoy, orbita):",
      dict(collections.Counter((x["b"], tuple(x["hoy"]), tuple(x["orbita"])) for x in cambios)))
print("partidas vs enteras (orbita):")
for k, v in partidas.items():
    if v["n"]: print(f"   {k}: {v['pub']}/{v['n']}")
print("quien publica en pasadas partidas (b, lab, pub por granulo):", dict(quien))
print("control positivo Chillan 2026-01-19 02:40:", ctrl)
print("control sintetico protegidas (120 s, 390 s):", sint)
