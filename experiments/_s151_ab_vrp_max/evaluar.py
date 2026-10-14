# -*- coding: utf-8 -*-
"""Evaluador del A/B `vrp_max` contra `vent_anchored` (tarea 1.4). Implementa PREREGISTRO.md §4 y §5 TAL CUAL.

POR QUE ESTE SCRIPT EXISTE ANTES DEL DESPACHO. El verificador del A/B de D22 encontro reglas sin un script que
las implementara y un veredicto impreso con otra vara. Aca cada regla del pre-registro tiene su linea, con el
mismo nombre (K1 a K4, R1 a R4, P1 a P5), y los numeros salen de `parametros.json`, congelado antes de correr.

QUE COMPARA. Un brazo (A1: flag apagado; A2: regla completa, si existe) contra el control A0, pasada por pasada
(volcan, sensor, fecha al minuto), sobre los records que cada brazo escribio en su data_subdir, contra la
referencia de MIROVA congelada (union historica de la tarea 0.1). "Publica" y "magnitud" son el predicado del
tablero ejecutado con node (A97), igual que banco_paridad.

VARIAS CORRIDAS. El despacho va en dos medias ventanas (dos run_id). Cada corrida deja, en la rama
s146-ab/<run_id>, `experiments/_s146_ab_sin_test1/salidas/<run_id>/<perfil>/<volcan>.json` y
`.../logs/<perfil>_<volcan>.log`. Este evaluador recibe cada carpeta `salidas/<run_id>` con `--corrida` (se
repite) y FUSIONA en memoria: concatena los records de cada perfil; una pasada repetida entre corridas es falla de
K1 (no se elige una en silencio). Un relanzamiento parcial (A108) se pasa como corrida aparte SOLO si su volcan no
esta en la original; si lo esta, se reemplazan los JSON y el log de ese volcan en la carpeta original. K3 se mira
por (corrida, perfil, volcan): cada volcan presente en los records de una corrida tiene que traer su log.

LAS DOS PREGUNTAS DEL INSTRUMENTO (probadas en probar_evaluar.py):
  (1) si lo medido estuviera roto, lo veria? Una pasada de menos o repetida da K1 en rojo; un brazo que cambia una
      pasada de un solo cumulo da K2 en rojo; un log con el flag equivocado o ausente da K3 en rojo; un brazo que
      silencia la candidata de P5 da veto; uno que silencia una positiva Muy Bajo da NO ADOPTAR por suma.
  (2) si el instrumento estuviera muerto? El control contra si mismo da K4 = 0 y el veredicto INDECIDIBLE (el
      mecanismo no actuo), nunca INERTE ni GANA.

Uso:
  python evaluar.py --corrida <salidas/run1> --corrida <salidas/run2> --cons <csv> --ocr <csv>
                    [--control _s146_ab_control] [--brazo A1=_s151_ab_vrp_max] [--brazo A2=_s151_ab_vrp_max_total]
  (--sin-logs solo para pruebas: marca K3 como NO VERIFICADO y el veredicto lleva el prefijo PRUEBA)
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comun as C  # noqa: E402
import sustrato as S  # noqa: E402
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
    """{perfil: {volcan: flags}} desde `<perfil>_<volcan>.log` (primera linea FLAGS_BRAZO de cada job)."""
    out = collections.defaultdict(dict)
    for p in sorted(Path(d).glob("*.log")):
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if ln.startswith("FLAGS_BRAZO "):
                    j = json.loads(ln[len("FLAGS_BRAZO "):])
                    perfil = j.get("PROFILE_NAME")
                    if perfil and p.stem.startswith(perfil + "_"):
                        out[perfil][p.stem[len(perfil) + 1:]] = j
                    break
    return out


def k3(logs, registros, perfil, esperado):
    """Cada (corrida, volcan) con records de `perfil` trae su log y el log dice lo esperado."""
    if logs is None:
        return None, "NO VERIFICADO (--sin-logs)"
    pares = sorted({(x.get("corrida"), x["vol"]) for x in registros})
    if not pares:
        return False, f"{perfil} sin records"
    for corrida, vol in pares:
        j = logs.get(corrida, {}).get(perfil, {}).get(vol)
        if j is None:
            return False, f"falta el log FLAGS_BRAZO de {perfil} {vol} en la corrida {corrida}"
        for k, v in esperado.items():
            if k not in j:
                return False, f"el log de {perfil} {vol} no trae {k} (falta en FLAGS_BRAZO del workflow)"
            if j[k] != v:
                return False, f"{perfil} {vol} ({corrida}) leyo {k}={j[k]}, se esperaba {v}"
    return True, f"ok ({len(pares)} pares corrida y volcan)"


def es_regla_D(x, inner):
    """La pasada del control esta en la Regla D: Test 1 y pixel mas energetico de la escena fuera del inner."""
    rec = x["rec"]
    hs = S.hotspot_previo_km(rec, S.escena(rec))
    return bool(rec.get("triggered_test1")) and hs is not None and hs > inner


def evaluar(ctrl, brazos, filas, ventana, logs=None, perfiles=None):
    """ctrl y cada brazo: listas de comun.cargar_records (con x['corrida'] si vienen de varias corridas).

    logs: None (pruebas) o {corrida: leer_logs(...)}. Devuelve (dict de resultados, texto)."""
    txt = []
    P = txt.append
    coords = C._coords_por_volcan()
    _, inner, inner_html = C.anclas_y_inner()
    radio, tol = PAR["radio_objeto_km"], PAR["tolerancia_centroide_km"]
    C.etiquetar(ctrl, filas, coords, ventana)
    for lista in [ctrl] + list(brazos.values()):
        for x, (p, dsp) in zip(lista, C.predicado_completo(lista, inner_html)):
            x["pub"], x["disp"] = p, dsp
    rep_c = [k for k, n in collections.Counter(C.clave(x) for x in ctrl).items() if n > 1]
    idx_c = {C.clave(x): x for x in ctrl}
    perfil_ctrl = (perfiles or {}).get("A0", PAR["brazos"]["A0"])
    res = {}
    for nombre, lista in brazos.items():
        r = {}
        rep_b = [k for k, n in collections.Counter(C.clave(x) for x in lista).items() if n > 1]
        idx_b = {C.clave(x): x for x in lista}
        # ---------------------------------------------------------------- K1 cobertura pareja (A108)
        faltan = sorted(k for k in idx_c if k not in idx_b)
        sobran = sorted(k for k in idx_b if k not in idx_c)
        r["K1"] = {"faltan": len(faltan), "sobran": len(sobran), "repetidas_control": len(rep_c),
                   "repetidas_brazo": len(rep_b),
                   "ok": not faltan and not sobran and not rep_c and not rep_b,
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
        ok3a, msg3a = k3(logs, ctrl, perfil_ctrl, PAR["cableado_esperado"]["A0"])
        ok3b, msg3b = k3(logs, lista, perfil, PAR["cableado_esperado"].get(nombre, {}))
        r["K3"] = {"control": msg3a, "brazo": msg3b, "ok": None if logs is None else bool(ok3a and ok3b)}

        # ---------------------------------------------------------------- K4 el mecanismo actua (A116)
        def lejos(x):
            d = _pc(x).get("centroid_dist_km")
            return d is not None and d > inner[x["vol"]] and (_pc(x).get("vrp_mw") or 0) > 0

        def cerca(x):
            d = _pc(x).get("centroid_dist_km")
            return d is not None and d <= inner[x["vol"]] and (_pc(x).get("vrp_mw") or 0) > 0
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
            # §3: protegidas que NO deciden (solo OCR antes del 2026-06-13, o solo OCR de Suomi NPP antes del
            # 2026-10-09) y que el brazo calla: no vetan, se informan aparte.
            prot_aparte = [list(C.clave(c)) for c, b in s if c["lab"] == "pos" and c["prot_A"] and not c["decide"]
                           and c["pub"] and not b["pub"]]

            def E(i):
                miss = sum(1 for c, b in dec if c["lab"] == "pos" and not c["prot_A"] and not (c, b)[i]["pub"])
                neg = sum(1 for c, b in dec if c["lab"] == "neg_limpio" and (c, b)[i]["pub"])
                return miss, neg
            mc, nc = E(0)
            mb, nb = E(1)
            accidente = sum(1 for c, b in dec if c["lab"] == "neg_limpio" and c["pub"] and not b["pub"] and lejos(b))
            # R3 magnitud: positivas publicadas en los dos, donde la magnitud del tablero cambia
            mas_cerca = mas_lejos = 0
            rat_c, rat_b = [], []
            for c, b in dec:
                if c["lab"] == "pos" and c["pub"] and b["pub"] and (c["vrp_ref"] or 0) > 0:
                    rat_c.append(c["disp"] / c["vrp_ref"])
                    rat_b.append(b["disp"] / c["vrp_ref"])
                    if abs(c["disp"] - b["disp"]) > 1e-9 and c["disp"] > 0 and b["disp"] > 0:
                        if abs(math.log(b["disp"] / c["vrp_ref"])) < abs(math.log(c["disp"] / c["vrp_ref"])):
                            mas_cerca += 1
                        else:
                            mas_lejos += 1
            # cambio CERCANO POR CERCANO: el cumulo publicado cambia por otro dentro del inner (magnitud, no
            # publicacion). Incluye la eleccion entre cumulos del Test 1 en el disco de 3 km (Regla D).
            def otro(c, b):
                pc, pb = _pc(c), _pc(b)
                if pc.get("centroid_lat") is None or pb.get("centroid_lat") is None:
                    return False
                return (C.haversine_km(pc["centroid_lat"], pc["centroid_lon"], pb["centroid_lat"], pb["centroid_lon"]) > tol
                        or pc.get("n_pixels") != pb.get("n_pixels"))
            cc = [(c, b) for c, b in s if cerca(c) and cerca(b) and otro(c, b)]
            fr = [(c, b) for c, b in s if c["lab"] == "far_ref"]
            por[bk] = {
                "n_pos_decide": sum(1 for c, _ in dec if c["lab"] == "pos"),
                "n_pos_protegidas_A": sum(1 for c, _ in dec if c["lab"] == "pos" and c["prot_A"]),
                "n_neg_limpio": sum(1 for c, _ in dec if c["lab"] == "neg_limpio"),
                "R1_veto_A": veto_A, "R1_veto_B_lejanas": veto_B_lejos, "protegidas_que_no_deciden_calladas": prot_aparte,
                "R2_E_control": [mc, nc], "R2_E_brazo": [mb, nb], "R2_delta_E": (mb + nb) - (mc + nc),
                "R2_ganancias_por_accidente": accidente,
                "R3_mas_cerca": mas_cerca, "R3_mas_lejos": mas_lejos,
                "R3_mediana_razon_control": round(statistics.median(rat_c), 3) if rat_c else None,
                "R3_mediana_razon_brazo": round(statistics.median(rat_b), 3) if rat_b else None,
                "R4_objeto_control": sum(objeto(c, inner[c["vol"]], radio) for c, _ in fr),
                "R4_objeto_brazo": sum(objeto(b, inner[b["vol"]], radio) for _, b in fr), "R4_n_far_ref": len(fr),
                "cercano_por_cercano": len(cc),
                "cercano_por_cercano_regla_D": sum(1 for c, _ in cc if es_regla_D(c, inner[c["vol"]])),
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
                cambios = sum(v["silenciadas"] + v["nuevas"] for v in por.values())
                if cambios == 0:
                    return "INERTE"
                # la publicacion cambia, pero solo en pasadas que el criterio no cuenta (far_ref, sin_info,
                # positivas que no deciden) o en cambios que se compensan dentro de un sensor
                return f"NEUTRO EN EL CRITERIO ({cambios} publicaciones cambian fuera de lo que el criterio cuenta)"
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
            # P2 (v2, tras el verificador de #794): en la Regla D el flag SI cambia la eleccion entre cumulos del
            # Test 1 dentro del disco de 3 km (cercano por cercano), asi que eso no cuenta. Lo que la lectura de
            # §1.2 prohibe es que una pasada de Regla D pase de cerca a lejos (o al reves) o cambie de publicacion.
            rd = [list(C.clave(c)) for c, b in pares if es_regla_D(c, inner[c["vol"]])
                  and (c["pub"] != b["pub"] or lejos(c) != lejos(b))]
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
        P(f"\n===== {nombre} ({perfil}) contra A0 ({perfil_ctrl})")
        P(f"K1 cobertura: faltan {r['K1']['faltan']}, sobran {r['K1']['sobran']}, repetidas control "
          f"{r['K1']['repetidas_control']} brazo {r['K1']['repetidas_brazo']} -> {'ok' if r['K1']['ok'] else 'FALLA'}")
        P(f"K2 determinismo (pasadas de un cumulo sin Test 1): distintas {r['K2']['distintas']} -> {'ok' if r['K2']['ok'] else 'FALLA'}")
        P(f"K3 cableado: control {r['K3']['control']}; brazo {r['K3']['brazo']}")
        P(f"K4 mecanismo: cumulos que pasan de cerca (o sin cumulo) a lejos: {r['K4']['cumulo_movido_lejos']}")
        for bk, v in por.items():
            P(f"  {bk:8s} pos {v['n_pos_decide']} (protegidas A {v['n_pos_protegidas_A']}), neg_limpio {v['n_neg_limpio']} | "
              f"veto A {len(v['R1_veto_A'])}, veto B lejanas {len(v['R1_veto_B_lejanas'])}, protegidas que no deciden calladas "
              f"{len(v['protegidas_que_no_deciden_calladas'])} | "
              f"E control {v['R2_E_control']} brazo {v['R2_E_brazo']} delta {v['R2_delta_E']} (accidente {v['R2_ganancias_por_accidente']}) | "
              f"R3 cerca {v['R3_mas_cerca']} lejos {v['R3_mas_lejos']} mediana {v['R3_mediana_razon_control']}->{v['R3_mediana_razon_brazo']} | "
              f"R4 {v['R4_objeto_control']}->{v['R4_objeto_brazo']} de {v['R4_n_far_ref']} | cercano por cercano "
              f"{v['cercano_por_cercano']} (Regla D {v['cercano_por_cercano_regla_D']}) | silenciadas {v['silenciadas']} nuevas {v['nuevas']}")
            for k in v["R1_veto_A"]:
                P(f"     veto A: {k}")
            for k in v["protegidas_que_no_deciden_calladas"]:
                P(f"     protegida que no decide, callada (aparte): {k}")
        P(f"VEREDICTO lectura A: {r['veredicto_A']}")
        P(f"VEREDICTO lectura B: {r['veredicto_B']}")
        P(f"predicciones: {json.dumps(pred, ensure_ascii=False)}")
    return res, "\n".join(txt)


def cargar_corridas(corridas, perfil, ventana, coords):
    """Fusion en memoria de las corridas: records de `perfil` de cada `salidas/<run_id>`, marcados con su corrida."""
    out = []
    for d in corridas:
        for x in C.cargar_records(Path(d) / perfil, ventana, coords):
            x["corrida"] = str(d)
            out.append(x)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corrida", action="append", required=True, help="carpeta salidas/<run_id>; se repite")
    ap.add_argument("--control", default=PAR["brazos"]["A0"])
    ap.add_argument("--brazo", action="append", help="NOMBRE=perfil, NOMBRE en A1 o A2 (por defecto A1)")
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--sin-logs", action="store_true")
    ap.add_argument("--desde", default=PAR["ventana"][0])
    ap.add_argument("--hasta", default=PAR["ventana"][1])
    ap.add_argument("--out", default=str(HERE / "evaluacion_salida.json"))
    a = ap.parse_args(argv)
    ventana = (a.desde, a.hasta)
    coords = C._coords_por_volcan()
    filas = cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    ctrl = cargar_corridas(a.corrida, a.control, ventana, coords)
    brazos, perfiles = {}, {"A0": a.control}
    for s in (a.brazo or [f"A1={PAR['brazos']['A1']}"]):
        n, perfil = s.split("=", 1)
        brazos[n] = cargar_corridas(a.corrida, perfil, ventana, coords)
        perfiles[n] = perfil
    logs = None if a.sin_logs else {str(d): leer_logs(Path(d) / "logs") for d in a.corrida}
    res, txt = evaluar(ctrl, brazos, filas, ventana, logs, perfiles)
    print(txt)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


if __name__ == "__main__":
    main()
    sys.exit(0)
