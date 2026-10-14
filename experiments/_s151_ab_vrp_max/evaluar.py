# -*- coding: utf-8 -*-
"""Evaluador del A/B `vrp_max` contra `vent_anchored` (tarea 1.4). Implementa PREREGISTRO.md §4 y §5 TAL CUAL.

POR QUE ESTE SCRIPT EXISTE ANTES DEL DESPACHO. El verificador del A/B de D22 encontro reglas sin un script que
las implementara y un veredicto impreso con otra vara. Aca cada regla del pre-registro tiene su linea, con el
mismo nombre (K1 a K4, R1 a R4, P1 a P5), y los numeros salen de `parametros.json`, congelado antes de correr.

QUE COMPARA. Un brazo (A1: flag apagado; A2: regla completa, si existe) contra el control A0, pasada por pasada
(volcan, sensor, fecha al minuto), sobre los records que cada brazo escribio en su data_subdir, contra la
referencia de MIROVA congelada (union historica de la tarea 0.1). "Publica" y "magnitud" son el predicado del
tablero ejecutado con node (A97), igual que banco_paridad.

LAS DOS PREGUNTAS DEL INSTRUMENTO (probadas en probar_evaluar.py):
  (1) si lo medido estuviera roto, lo veria? Un brazo con una pasada de menos da K1 en rojo; un brazo que cambia
      una pasada de un solo cumulo da K2 en rojo; un brazo que silencia la candidata de P5 da veto.
  (2) si el instrumento estuviera muerto? El control contra si mismo da K4 = 0 y el veredicto INDECIDIBLE (el
      mecanismo no actuo), nunca INERTE ni GANA.

Uso:
  python evaluar.py --control <dir A0> --brazo A1=<dir> [--brazo A2=<dir>] --cons <csv> --ocr <csv> --logs <dir>
  (--sin-logs solo para pruebas: marca K3 como NO VERIFICADO y el veredicto lleva el prefijo PRUEBA)
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comun as C  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

PAR = json.loads((HERE / "parametros.json").read_text(encoding="utf-8"))


def _pc(x):
    return x["rec"].get("primary_cluster") or {}


def objeto(x, inner, radio):
    """El cumulo publicado es el objeto lejano que MIROVA informo: lejos del crater y a `radio` km de su radio.

    Diferencia de RADIOS (A93): sin acimut es una cota inferior de la separacion, sirve para descartar, no para
    identificar. Distancia nuestra desde el crater (pc.centroid_dist_km, ancla de deteccion), nunca del catalogo."""
    pc = _pc(x)
    d = pc.get("centroid_dist_km")
    return (d is not None and (pc.get("vrp_mw") or 0) > 0 and d > inner and x.get("dist_ref") is not None
            and abs(d - x["dist_ref"]) <= radio)


def leer_logs(d):
    """Primera linea FLAGS_BRAZO de cada log de job: {perfil: [dict, ...]}."""
    out = collections.defaultdict(list)
    for p in glob.glob(str(Path(d) / "**" / "*.log"), recursive=True):
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if ln.startswith("FLAGS_BRAZO "):
                    j = json.loads(ln[len("FLAGS_BRAZO "):])
                    out[j.get("PROFILE_NAME")].append(j)
                    break
    return out


def k3(logs, perfil, esperado):
    if logs is None:
        return None, "NO VERIFICADO (--sin-logs)"
    vistos = logs.get(perfil, [])
    if len(vistos) != len(C.VOLS):
        return False, f"{len(vistos)} logs con FLAGS_BRAZO para {perfil}, se esperaban {len(C.VOLS)}"
    for j in vistos:
        for k, v in esperado.items():
            if k not in j:
                return False, f"el log no trae {k} (falta agregarlo a FLAGS_BRAZO del workflow)"
            if j[k] != v:
                return False, f"{perfil} leyo {k}={j[k]}, se esperaba {v}"
    return True, "ok"


def evaluar(ctrl, brazos, filas, ventana, logs=None, perfiles=None):
    """ctrl y cada brazo: listas de comun.cargar_records. Devuelve (dict de resultados, texto)."""
    txt = []
    P = txt.append
    coords = C._coords_por_volcan()
    _, inner, inner_html = C.anclas_y_inner()
    radio, tol = PAR["radio_objeto_km"], PAR["tolerancia_centroide_km"]
    C.etiquetar(ctrl, filas, coords, ventana)
    for lista in [ctrl] + list(brazos.values()):
        for x, (p, dsp) in zip(lista, C.predicado_completo(lista, inner_html)):
            x["pub"], x["disp"] = p, dsp
    idx_c = {C.clave(x): x for x in ctrl}
    res = {}
    for nombre, lista in brazos.items():
        r = {}
        idx_b = {C.clave(x): x for x in lista}
        # ---------------------------------------------------------------- K1 cobertura pareja (A108)
        faltan = sorted(k for k in idx_c if k not in idx_b)
        sobran = sorted(k for k in idx_b if k not in idx_c)
        r["K1"] = {"faltan": len(faltan), "sobran": len(sobran), "ok": not faltan and not sobran,
                   "ejemplos_faltan": [list(k) for k in faltan[:5]]}
        pares = [(idx_c[k], idx_b[k]) for k in idx_c if k in idx_b]
        for c, b in pares:
            for campo in ("lab", "dist_ref", "vrp_ref", "prot_A", "prot_B", "decide", "tramo", "solo_ocr"):
                b[campo] = c[campo]
        # ---------------------------------------------------------------- K2 determinismo
        k2 = []
        for c, b in pares:
            rc = c["rec"]
            if (rc.get("n_hotspots_clustered") or 0) <= 1 and not rc.get("triggered_test1"):
                pc_c, pc_b = _pc(c), _pc(b)
                igual = (all(pc_c.get(f) == pc_b.get(f) for f in ("vrp_mw", "centroid_lat", "centroid_lon", "n_pixels"))
                         and rc.get("distance_class") == b["rec"].get("distance_class") and c["pub"] == b["pub"])
                if not igual:
                    k2.append(list(C.clave(c)))
        r["K2"] = {"distintas": len(k2), "ok": not k2, "ejemplos": k2[:5]}
        # ---------------------------------------------------------------- K3 cableado (log FLAGS_BRAZO)
        perfil = (perfiles or {}).get(nombre, PAR["brazos"].get(nombre))
        ok3a, msg3a = k3(logs, PAR["brazos"]["A0"], PAR["cableado_esperado"]["A0"])
        ok3b, msg3b = k3(logs, perfil, PAR["cableado_esperado"].get(nombre, {}))
        r["K3"] = {"control": msg3a, "brazo": msg3b,
                   "ok": None if logs is None else bool(ok3a and ok3b)}
        # ---------------------------------------------------------------- K4 el mecanismo actua (A116)
        def lejos(x):
            d = _pc(x).get("centroid_dist_km")
            return d is not None and d > inner[x["vol"]] and (_pc(x).get("vrp_mw") or 0) > 0
        movidas = [(c, b) for c, b in pares if not lejos(c) and lejos(b)]
        r["K4"] = {"cumulo_movido_lejos": len(movidas), "ok": len(movidas) > 0}
        # ---------------------------------------------------------------- reglas por sensor
        por = {}
        for bk in C.BUCKETS:
            s = [(c, b) for c, b in pares if c["b"] == bk]
            dec = [(c, b) for c, b in s if c["decide"]]
            veto_A = [list(C.clave(c)) for c, b in dec if c["lab"] == "pos" and c["prot_A"] and c["pub"] and not b["pub"]]
            veto_B_lejos = [list(C.clave(c)) for c, b in s if c["lab"] == "far_ref" and c["prot_B"]
                            and objeto(c, inner[c["vol"]], radio) and not objeto(b, inner[b["vol"]], radio)]

            def E(i):
                miss = sum(1 for c, b in dec if c["lab"] == "pos" and not c["prot_A"] and not (c, b)[i]["pub"])
                neg = sum(1 for c, b in dec if c["lab"] == "neg_limpio" and (c, b)[i]["pub"])
                return miss, neg
            mc, nc = E(0)
            mb, nb = E(1)
            accidente = sum(1 for c, b in dec if c["lab"] == "neg_limpio" and c["pub"] and not b["pub"] and lejos(b))
            # R3 magnitud: positivas publicadas en los dos, donde la magnitud del tablero cambia
            cerca = lejosm = 0
            rat_c, rat_b = [], []
            for c, b in dec:
                if c["lab"] == "pos" and c["pub"] and b["pub"] and (c["vrp_ref"] or 0) > 0:
                    rat_c.append(c["disp"] / c["vrp_ref"])
                    rat_b.append(b["disp"] / c["vrp_ref"])
                    if abs(c["disp"] - b["disp"]) > 1e-9 and c["disp"] > 0 and b["disp"] > 0:
                        if abs(math.log(b["disp"] / c["vrp_ref"])) < abs(math.log(c["disp"] / c["vrp_ref"])):
                            cerca += 1
                        else:
                            lejosm += 1
            fr = [(c, b) for c, b in s if c["lab"] == "far_ref"]
            por[bk] = {
                "n_pos_decide": sum(1 for c, _ in dec if c["lab"] == "pos"),
                "n_pos_protegidas_A": sum(1 for c, _ in dec if c["lab"] == "pos" and c["prot_A"]),
                "n_neg_limpio": sum(1 for c, _ in dec if c["lab"] == "neg_limpio"),
                "R1_veto_A": veto_A, "R1_veto_B_lejanas": veto_B_lejos,
                "R2_E_control": [mc, nc], "R2_E_brazo": [mb, nb], "R2_delta_E": (mb + nb) - (mc + nc),
                "R2_ganancias_por_accidente": accidente,
                "R3_mas_cerca": cerca, "R3_mas_lejos": lejosm,
                "R3_mediana_razon_control": round(statistics.median(rat_c), 3) if rat_c else None,
                "R3_mediana_razon_brazo": round(statistics.median(rat_b), 3) if rat_b else None,
                "R4_objeto_control": sum(objeto(c, inner[c["vol"]], radio) for c, _ in fr),
                "R4_objeto_brazo": sum(objeto(b, inner[b["vol"]], radio) for _, b in fr), "R4_n_far_ref": len(fr),
                "silenciadas": sum(1 for c, b in s if c["pub"] and not b["pub"]),
                "nuevas": sum(1 for c, b in s if not c["pub"] and b["pub"]),
            }
        r["por_sensor"] = por
        # ---------------------------------------------------------------- veredicto (PREREGISTRO §5)
        instrumento_ok = r["K1"]["ok"] and r["K2"]["ok"] and r["K3"]["ok"] is not False
        def veredicto(lectura):
            if not instrumento_ok:
                return "INDECIDIBLE POR INSTRUMENTO"
            if not r["K4"]["ok"]:
                return "INDECIDIBLE: EL MECANISMO NO ACTUO"
            vetos = sum(len(v["R1_veto_A"]) + (len(v["R1_veto_B_lejanas"]) if lectura == "B" else 0) for v in por.values())
            if vetos:
                return f"NO ADOPTAR (veto, {vetos} alertas protegidas perdidas)"
            ds = [v["R2_delta_E"] for v in por.values()]
            if any(d > 0 for d in ds):
                return "NO ADOPTAR (la suma de errores sube en " + ", ".join(b for b, v in por.items() if v["R2_delta_E"] > 0) + ")"
            if all(d == 0 for d in ds):
                return "INERTE"
            acc = sum(v["R2_ganancias_por_accidente"] for v in por.values())
            ganan = -sum(ds)
            if acc >= ganan:
                # PREREGISTRO §5, R2: la baja sale entera de callar el crater detras de un cumulo lejano que
                # MIROVA no vio (negativo limpio). Dos errores que se cancelan no son fidelidad (A100).
                return f"GANA SOLO POR ACCIDENTE (suma de errores baja {ganan}; ganancias por accidente {acc})"
            return f"GANA EL CRITERIO (suma de errores baja {ganan}; ganancias por accidente {acc})"
        pref = "PRUEBA " if logs is None else ""
        r["veredicto_A"] = pref + veredicto("A")
        r["veredicto_B"] = pref + veredicto("B")
        # ---------------------------------------------------------------- predicciones
        pred = {}
        if nombre == "A1":
            mx = PAR["prediccion_P1_A1_max_silenciadas"]
            pred["P1"] = all(por[bk]["silenciadas"] <= mx[bk] for bk in mx)
            rd = [list(C.clave(c)) for c, b in pares
                  if (c["pub"] != b["pub"] or _pc(c) != _pc(b)) and c["rec"].get("triggered_test1")
                  and (c["rec"].get("hotspot_dist_km") or 0) > inner[c["vol"]]]
            pred["P2"] = not rd
            pred["P2_ejemplos"] = rd[:5]
            pred["P3"] = (all(not v["R1_veto_A"] for bk, v in por.items() if bk != "MODIS")
                          and all(abs(v["R2_delta_E"]) <= PAR["prediccion_P3_A1_abs_delta_E_max"]
                                  for bk, v in por.items() if bk != "MODIS"))
        if nombre == "A2":
            pred["P4_silenciadas"] = por["VIIRS375"]["silenciadas"] >= PAR["prediccion_P4_A2_min_silenciadas_VIIRS375"]
            pred["P4_R4"] = sum(v["R4_objeto_brazo"] for v in por.values()) >= PAR["prediccion_P4_A2_R4_min"]
            cand = PAR["prediccion_P5_A2_candidata_veto"].split("|")
            pred["P5_veto_en_candidata"] = any(v[0] == cand[0] and v[2] == cand[2] for v in por["VIIRS375"]["R1_veto_A"])
        r["predicciones"] = pred
        res[nombre] = r
        P(f"\n===== {nombre} ({perfil}) contra A0")
        P(f"K1 cobertura: faltan {r['K1']['faltan']}, sobran {r['K1']['sobran']} -> {'ok' if r['K1']['ok'] else 'FALLA'}")
        P(f"K2 determinismo (pasadas de un cumulo sin Test 1): distintas {r['K2']['distintas']} -> {'ok' if r['K2']['ok'] else 'FALLA'}")
        P(f"K3 cableado: control {r['K3']['control']}; brazo {r['K3']['brazo']}")
        P(f"K4 mecanismo: cumulos que pasan de cerca (o sin cumulo) a lejos: {r['K4']['cumulo_movido_lejos']}")
        for bk, v in por.items():
            P(f"  {bk:8s} pos {v['n_pos_decide']} (protegidas A {v['n_pos_protegidas_A']}), neg_limpio {v['n_neg_limpio']} | "
              f"veto A {len(v['R1_veto_A'])}, veto B lejanas {len(v['R1_veto_B_lejanas'])} | "
              f"E control {v['R2_E_control']} brazo {v['R2_E_brazo']} delta {v['R2_delta_E']} (accidente {v['R2_ganancias_por_accidente']}) | "
              f"R3 cerca {v['R3_mas_cerca']} lejos {v['R3_mas_lejos']} mediana {v['R3_mediana_razon_control']}->{v['R3_mediana_razon_brazo']} | "
              f"R4 {v['R4_objeto_control']}->{v['R4_objeto_brazo']} de {v['R4_n_far_ref']} | silenciadas {v['silenciadas']} nuevas {v['nuevas']}")
            for k in v["R1_veto_A"]:
                P(f"     veto A: {k}")
        P(f"VEREDICTO lectura A: {r['veredicto_A']}")
        P(f"VEREDICTO lectura B: {r['veredicto_B']}")
        P(f"predicciones: {json.dumps(pred, ensure_ascii=False)}")
    return res, "\n".join(txt)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", action="append", required=True, help="NOMBRE=dir, NOMBRE en A1 o A2")
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--logs")
    ap.add_argument("--sin-logs", action="store_true")
    ap.add_argument("--desde", default=PAR["ventana"][0])
    ap.add_argument("--hasta", default=PAR["ventana"][1])
    ap.add_argument("--out", default=str(HERE / "evaluacion_salida.json"))
    a = ap.parse_args(argv)
    if not a.logs and not a.sin_logs:
        ap.error("falta --logs (K3); --sin-logs solo para pruebas")
    ventana = (a.desde, a.hasta)
    coords = C._coords_por_volcan()
    filas = cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    ctrl = C.cargar_records(Path(a.control), ventana, coords)
    brazos = {}
    for s in a.brazo:
        n, d = s.split("=", 1)
        brazos[n] = C.cargar_records(Path(d), ventana, coords)
    logs = leer_logs(a.logs) if a.logs else None
    res, txt = evaluar(ctrl, brazos, filas, ventana, logs)
    print(txt)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
