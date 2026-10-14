# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. Evaluador del A/B de la caja de 5 x 5 km (D18), experiments/_s151_prereg_caja/PREREGISTRO.md.
Implementa las reglas de §5 y §6 del pre-registro TAL CUAL; si una regla cambia, cambia aca y alla en el mismo commit.

QUE REUSA, SIN REIMPLEMENTAR. Todo lo de experiments/_s151_prereg_fk_11/evaluar_fk.py que no depende de los brazos
de esa prueba: la tabla por pasada (armar_tabla.py, predicado del tablero ejecutado con node, A97), la proteccion
(scripts/clase_mirova.alerta_protegida, lecturas A y B), la referencia congelada con capas y manifiesto, la suma de
errores, las pasadas discordantes como ruido, la magnitud pareada con bootstrap y la lectura de FLAGS_BRAZO por
directorio de logs. La geometria de la caja es la de sustrato.py (= pipeline/scan_geometry.py::roi_mask_bbox).

LOS BRAZOS (§2). Decision: K (el candidato vivo: sin Test 1, conectiva max, banda 22 en MODIS) contra KC (K mas la
caja), con KG (gemelo de K) para el ruido. Mecanismo: B (sin Test 1, conectiva min) contra BC (B mas la caja), donde
la caja tiene sustrato de sobra; es el control positivo de la palanca.

QUE MIDE, POR PASADA, por sensor y lectura:
  P1 veto       protegidas que K publica y KC no.
  P2 suma       alertas Muy Bajo perdidas + publicaciones en negativos limpios, KC contra K; ruido = discordantes K/KG.
  P2b techo     |suma KC - suma K| contra el techo que dio sustrato.py (informa: si se pasa, el sustrato no explica).
  P3 magnitud   d = |log10(KC/MIROVA)| - |log10(K/MIROVA)| en las alertas que publican los dos.
  P4 posicion   fraccion de publicaciones con el cumulo fuera de la caja, en los 8 volcanes con el punto de
                referencia de MIROVA en el crater, contra el techo de MIROVA (Wilson superior de lo que MIROVA mismo
                tiene fuera de su caja en V1, prediccion_mirova_salida.txt).
  Q1 mecanismo  de los negativos limpios que B publica EXPUESTOS (todo su calor del circulo fuera de la caja), BC apaga
                la mitad o mas.
  Q2 control    de los negativos limpios que B publica con calor DENTRO de la caja, BC cambia la publicacion en el
                12 % o menos (heredado de S147, 5 de 42: elegido, no medido).
Controles antes de mirar: cobertura (A108) y K contra produccion, version del producto, cableado de cada brazo desde
FLAGS_BRAZO (incluida la caja: sin esa clave en el log, el brazo es ROTO), huella de la caja en los records (A116,
A118: BC tiene que tener menos pixeles en la corona circulo menos caja que B; si no, la caja no actuo y se traza por
etapa antes de escribir nada), determinismo K contra KG, referencia congelada.

Uso:
  python evaluar_caja.py --ventana V1 --raiz <salidas run V1> --logs <salidas run V1>/logs --out v1.json
  python evaluar_caja.py --ventana D1 --raiz <run D1> --logs <run D1>/logs --out d1.json   (y D2)
  python evaluar_caja.py --combinar v1.json d1.json d2.json
"""
from __future__ import annotations

import argparse, collections, hashlib, json, math, statistics, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s151_prereg_fk_11")); sys.path.insert(0, str(AQUI))
import evaluar_fk as E  # noqa: E402  (deja sys.stdout en utf-8)
import sustrato as S  # noqa: E402
bp = E.bp

# ---------------------------------------------------------------- lo que el pre-registro fija (§2, §3)
BRAZOS = {"K": "_s149_ab_sin_test1_b22_max", "KC": "_s151_ab_sin_test1_b22_max_caja", "KG": "_s151_ab_sin_test1_b22_max_gemelo",
          "B": "_s146_ab_sin_test1", "BC": "_s147_ab_sin_test1_caja"}
E.BRAZOS.update(BRAZOS)   # las funciones reusadas (tabla, crudos, flags_leidos, fusionar) leen este diccionario
CLAVES = ("ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY", "ENABLE_ROI1_BOX_PAPER", "ROI1_BOX_HALF_KM")
DECLARADO = {"K": (False, True, True, False, 2.5), "KC": (False, True, True, True, 2.5), "KG": (False, True, True, False, 2.5),
             "B": (False, False, False, False, 2.5), "BC": (False, False, False, True, 2.5)}
EXTRA = {"ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": False, "ENABLE_VENT_ANCHORED_CLUSTERING": True,
         "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER": False, "PATH_D_ONLY_CAP_MW": 5.0}
CONG_V2 = RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v2"
VENTANAS = {
    "V1": {"desde": "2026-08-29", "hasta": "2026-10-08", "ref": E.VENTANAS["V1"]["ref"], "solo_tabla": False,
           "brazos": ("K", "KC", "KG", "B", "BC"), "vols": None},
    # Dirigidas a las dos unicas protegidas del candidato que caen EXPUESTAS en los datos en disco (sustrato.py):
    # la caja solo puede perder una alerta asi, y en V1 no hay ninguna.
    "D1": {"desde": "2026-03-14", "hasta": "2026-03-27", "ref": CONG_V2, "solo_tabla": True, "brazos": ("K", "KC"), "vols": ("Lascar",)},
    "D2": {"desde": "2026-06-10", "hasta": "2026-06-10", "ref": CONG_V2, "solo_tabla": True, "brazos": ("K", "KC"), "vols": ("Isluga",)},
}
SENS = ("MODIS", "VIIRS375", "VIIRS750")
CENTRADOS = [v for v in bp.VOLS if v not in ("Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa")]
# prediccion_mirova_salida.txt, V1, 8 volcanes centrados: alertas fuera de la caja con cualquier acimut o ambiguas
# (cota superior: tramo 2,5 a 3,54 km + tramo > 3,54 km) sobre el total.
MIROVA_FUERA = {"VIIRS375": (5, 223), "VIIRS750": (0, 34), "MODIS": (0, 8)}
# sustrato_salida.txt: techo de lo que la caja puede mover la suma del candidato en V1, extrapolado de los runs
# mensuales (abril a agosto: 4,4 negativos expuestos por mes en VIIRS 375 y 2,6 en VIIRS 750) a 41 dias, mas las
# Muy Bajo expuestas (1 por mes en VIIRS 375); MODIS con el techo del brazo B en V1 en disco (11 en 18 dias).
TECHO_P2 = {"VIIRS375": 8, "VIIRS750": 4, "MODIS": 25}
Q1_FRACCION = 0.5
Q2_TOPE = 0.12
DETERMINISMO = 0.98
N_MIN_MAGNITUD = 5


# ---------------------------------------------------------------- pixeles por pasada
def clases_por_pasada(raiz, nombre, vols, desde, hasta, anclas, inner):
    out = {}
    for v in vols:
        p = Path(raiz) / BRAZOS[nombre] / (v + ".json")
        if not p.exists():
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
            if b is None or not (desde <= t[:10] <= hasta):
                continue
            out["|".join((v, b, t[:16]))] = collections.Counter(
                S.clase_pixel(q["lat"], q["lon"], anclas[v], inner[v]) for q in (r.get("anomaly_pixels") or []) if q.get("lat") is not None)
    return out


def fuera_de_caja(x, vol, anclas):
    return x["pc_lat"] is not None and not S.lc.en_caja(x["pc_lat"], x["pc_lon"], anclas[vol])


# ---------------------------------------------------------------- evaluacion de una ventana
def evaluar(a):
    cfg = dict(VENTANAS[a.ventana])
    for k in ("desde", "hasta"):
        if getattr(a, k):
            cfg[k] = getattr(a, k)
    if a.ref:
        cfg["ref"] = Path(a.ref)
    vols = a.vols.split(",") if a.vols else list(cfg["vols"] or bp.VOLS)
    brazos = cfg["brazos"]
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / ("_tmp_" + a.ventana); tmp.mkdir(parents=True, exist_ok=True)
    raiz = E.fusionar(a.raiz, tmp, brazos, vols)
    faltan = [(n, v) for n in brazos for v in vols if not (raiz / BRAZOS[n] / (v + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos o volcanes: %s. No se evalua a medias." % faltan[:20])
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); anclas = S.lc.anclas()
    res = {"ventana": a.ventana, "desde": cfg["desde"], "hasta": cfg["hasta"], "brazos": list(brazos), "veredicto": {},
           "sha256_index_html": hashlib.sha256((RAIZ / "frontend" / "index.html").read_bytes()).hexdigest()}
    print("== VENTANA %s: %s a %s | volcanes %s | brazos %s | %s" % (a.ventana, cfg["desde"], cfg["hasta"], ",".join(vols), brazos,
          "decide la tabla sola" if cfg["solo_tabla"] else "decide tabla y OCR"))
    print("   predicado del tablero: frontend/index.html sha256", res["sha256_index_html"])
    ref = E.archivos_ref(cfg, tmp)
    res["referencia_ok"] = E.referencia_congelada(cfg["ref"], ref[2], a.capas_del_repo)

    pares = [("K", n) for n in ("KC", "KG") if n in brazos] + ([("B", "BC")] if {"B", "BC"} <= set(brazos) else [])
    T = {p: E.tabla(raiz / BRAZOS[p[0]], raiz / BRAZOS[p[1]], ref, cfg["desde"], cfg["hasta"], tmp / ("t_%s_%s.json" % p)) for p in pares}
    R = {n: E.crudos(raiz, n, vols, cfg["desde"], cfg["hasta"]) for n in brazos}
    PX = {n: clases_por_pasada(raiz, n, vols, cfg["desde"], cfg["hasta"], anclas, inner) for n in brazos}
    todas = set().union(*[set(t) for t in T.values()])
    prot = E.proteccion(todas, ref, cfg["desde"], cfg["hasta"])
    TK = T[("K", "KC")]

    # ---------------- 1. cobertura
    print("\n== 1. COBERTURA (A108)")
    claves_ = {n: set(R[n]) for n in brazos}; mal = False
    for n in brazos:
        d1, d2 = claves_["K"] - claves_[n], claves_[n] - claves_["K"]
        if d1 or d2:
            mal = True; print("   %-3s le faltan %d pasadas de K y tiene %d que K no %s" % (n, len(d1), len(d2), sorted(d1 | d2)[:5]))
    protegidas = sorted(k for k in todas if prot[k]["A"] or prot[k]["B"])
    sin_rec = {k: [n for n in brazos if k not in claves_[n]] for k in protegidas}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    print("   protegidas (A o B) sin record en algun brazo:", sin_rec or "ninguna")
    prod = E.claves_produccion(Path(a.produccion), vols, cfg["desde"], cfg["hasta"])
    cortos = ["%s %s: faltan %d de %d" % (v, s, len(ks - claves_["K"]), len(ks)) for (v, s), ks in sorted(prod.items())
              if len(ks - claves_["K"]) > E.MAX_FALTA_CONTRA_PRODUCCION * len(ks)]
    print("   K contra produccion: %s" % ("; ".join(cortos) if cortos else "en ningun volcan y sensor falta mas del 5 % de las pasadas de produccion"))
    res["cobertura_ok"] = not (mal or sin_rec or cortos)
    print("   " + ("cobertura pareja: OK" if res["cobertura_ok"] else "COBERTURA DESPAREJA O CORTA: INDECIDIBLE. Repetir los jobs cortos con el mismo codigo."))

    # ---------------- 2. version de producto
    mezcla_p = sorted(k for k in protegidas if len({R[n][k]["pv"] for n in brazos if k in R[n]}) > 1)
    print("\n== 2. VERSION DEL PRODUCTO: protegidas con version distinta entre brazos %d %s" % (len(mezcla_p), mezcla_p[:5]))
    res["version_ok"] = not mezcla_p

    # ---------------- 3. cableado
    print("\n== 3. CABLEADO (linea FLAGS_BRAZO de cada job; la clave de la caja es obligatoria)")
    cable = {}
    for n in brazos:
        prob = [] if a.logs else ["sin --logs: no hay con que probar el cableado"]
        for v in vols:
            for d, fl in E.flags_leidos(a.logs, n, v):
                donde = "%s (%s)" % (v, d)
                if fl is None:
                    prob.append("%s: sin linea FLAGS_BRAZO" % donde); continue
                if fl.get("PROFILE_NAME") != BRAZOS[n] or fl.get("DATA_SUBDIR") != BRAZOS[n]:
                    prob.append("%s: perfil o directorio %s" % (donde, fl.get("PROFILE_NAME")))
                falta = [c for c in CLAVES if c not in fl]
                if falta:
                    prob.append("%s: el log no trae %s (workflow sin la linea de #794 y de esta tarea)" % (donde, falta)); continue
                leido = tuple(fl[c] for c in CLAVES)
                if leido != DECLARADO[n]:
                    prob.append("%s: flags leidos %s contra declarados %s" % (donde, leido, DECLARADO[n]))
                for c, val in EXTRA.items():
                    if c in fl and fl[c] != val:
                        prob.append("%s: %s=%s, produccion %s" % (donde, c, fl[c], val))
        if any(x["t1"] for x in R[n].values()):
            prob.append("declara sin Test 1 y hay records con triggered_test1")
        cable[n] = prob
        print("   %-3s %s" % (n, "OK" if not prob else "ROTO: " + "; ".join(prob[:3]) + (" (y %d mas)" % (len(prob) - 3) if len(prob) > 3 else "")))
    res["cableado"] = {n: not p for n, p in cable.items()}

    # ---------------- 4. huella de la caja
    print("\n== 4. HUELLA DE LA CAJA (pixeles alertados por zona, todas las pasadas: CK caja y circulo, C solo circulo)")
    res["huella"] = {}
    for c, x in (("K", "KC"), ("B", "BC")):
        if x not in brazos:
            continue
        tc = sum((PX[c][k] for k in PX[c]), collections.Counter()); tx = sum((PX[x][k] for k in PX[x]), collections.Counter())
        bien = tx["C"] < tc["C"]
        res["huella"][x] = bien
        print("   %s: corona C %d -> %d | caja CK %d -> %d | %s" % (x, tc["C"], tx["C"], tc["CK"], tx["CK"],
              "la caja actuo" if bien else "SIN HUELLA en la corona" + (" (control positivo: INDECIDIBLE, trazar por etapa, A118)" if x == "BC" else " (informa)")))
    huella_ok = res["huella"].get("BC", True)

    # ---------------- 5. determinismo
    print("\n== 5. DETERMINISMO (K contra KG, misma decision de publicar)")
    det_ok = True; ruido = set()
    if ("K", "KG") in T:
        for s in SENS:
            amb = [(k, v) for k, v in T[("K", "KG")].items() if k.split("|")[1] == s and len(v) == 2]
            dif = {k for k, v in amb if v["control"]["pub"] != v["brazo"]["pub"]}; ruido |= dif
            ok = bool(amb) and (len(amb) - len(dif)) / len(amb) >= DETERMINISMO; det_ok &= ok
            print("   %-8s %5d pasadas, distintas %d | %s" % (s, len(amb), len(dif), "OK" if ok else "FALLA"))
    else:
        print("   sin gemelo en esta ventana: una perdida queda PENDIENTE DE REPETICION (§5)")
    res["determinismo_ok"] = det_ok
    res["controles_ok"] = res["cobertura_ok"] and res["version_ok"] and det_ok and res["referencia_ok"]
    print("\n== CONTROLES GENERALES:", "OK" if res["controles_ok"] else "FALLAN: ningun veredicto decide")
    decide = res["controles_ok"] and res["cableado"]["K"] and res["cableado"]["KC"] and res["cableado"].get("KG", True)

    T_rep = None
    if a.repeticion:
        rr = Path(a.repeticion)
        T_rep = E.tabla(rr / BRAZOS["K"], rr / BRAZOS["KC"], ref, cfg["desde"], cfg["hasta"], tmp / "rep_K_KC.json")

    # ---------------- 6. mecanismo B -> BC
    q2_ok = True
    if ("B", "BC") in T:
        print("\n== 6. MECANISMO B -> BC (control positivo de la palanca)")
        TB = T[("B", "BC")]
        exp = [k for k, v in TB.items() if len(v) == 2 and v["control"]["lab"] == "neg_limpio" and v["control"]["pub"]
               and PX["B"].get(k, collections.Counter())["CK"] == 0 and PX["B"].get(k, collections.Counter())["C"] > 0]
        den = [k for k, v in TB.items() if len(v) == 2 and v["control"]["lab"] == "neg_limpio" and v["control"]["pub"]
               and PX["B"].get(k, collections.Counter())["CK"] > 0]
        apag = sum(1 for k in exp if not TB[k]["brazo"]["pub"]); camb = sum(1 for k in den if not TB[k]["brazo"]["pub"])
        if not (res["controles_ok"] and res["cableado"]["B"] and res["cableado"]["BC"]):
            q1 = q2 = "INDECIDIBLE"
        else:
            q1 = "SIN SUSTRATO" if not exp else ("CUMPLE" if apag >= math.ceil(Q1_FRACCION * len(exp)) else "FALLA")
            q2 = "CUMPLE" if (not den or camb <= Q2_TOPE * len(den)) else "FALLA"
        q2_ok = q2 != "FALLA"
        res["veredicto"].update({"Q1|BC": q1, "Q2|BC": q2})
        print("   Q1 negativos limpios expuestos que B publica: %d; BC apaga %d (exige la mitad o mas) -> %s" % (len(exp), apag, q1))
        print("   Q2 negativos limpios con calor dentro de la caja que B publica: %d; BC cambia %d (tope 12 %%) -> %s" % (len(den), camb, q2))
        pexp = [k for k, v in TB.items() if len(v) == 2 and v["control"]["lab"] == "pos" and v["control"]["pub"]
                and PX["B"].get(k, collections.Counter())["CK"] == 0 and PX["B"].get(k, collections.Counter())["C"] > 0]
        print("   (informa) alertas de MIROVA expuestas que B publica: %d; BC conserva %d" % (len(pexp), sum(TB[k]["brazo"]["pub"] for k in pexp)))

    # ---------------- 7. P1 veto
    print("\n== 7. P1, VETO: protegidas que K publica y KC no")
    for lectura in ("A", "B"):
        for s in SENS:
            netas, ruidosas, pend, desc, snpp, recup, n_pub = [], [], [], [], [], [], 0
            for k, v in TK.items():
                if len(v) != 2 or k.split("|")[1] != s or not prot[k][lectura]:
                    continue
                c, b = v["control"], v["brazo"]
                if b["pub"] and not c["pub"]:
                    recup.append(k)
                if not c["pub"]:
                    continue
                n_pub += 1
                if b["pub"]:
                    continue
                linea = "%s | MIROVA %s MW | %s | pixeles de K: %s" % (k, c["vrp_ref"], c["plataforma"], dict(PX["K"].get(k, {})))
                rep = (T_rep or {}).get(k)
                if lectura == "A" and not cfg["solo_tabla"] and E.ocr_snpp(k, c, prot):
                    snpp.append(linea)
                elif rep is not None and len(rep) == 2:
                    (netas if (rep["control"]["pub"] and not rep["brazo"]["pub"]) else desc).append(linea)
                elif k in ruido:
                    ruidosas.append(linea)
                elif "KG" not in brazos:
                    pend.append(linea)
                else:
                    netas.append(linea)
            ver = ("INDECIDIBLE" if not (decide and huella_ok and q2_ok) else "VETADO" if netas else "INDECIDIBLE" if ruidosas
                   else "PENDIENTE DE REPETICION" if pend else "SIN SUSTRATO" if n_pub == 0 else "CUMPLE")
            res["veredicto"]["P1|%s|%s" % (s, lectura)] = ver
            print("   lectura %s %-8s protegidas que K publica %3d | perdidas netas %d, ruidosas %d, pendientes %d, descartadas %d, solo OCR Suomi NPP %d | recuperadas %d | %s" % (
                lectura, s, n_pub, len(netas), len(ruidosas), len(pend), len(desc), len(snpp), len(recup), ver))
            for etq, xs in (("perdida", netas), ("perdida ruidosa", ruidosas), ("PENDIENTE DE REPETICION", pend), ("ruido confirmado por la repeticion", desc), ("solo OCR Suomi NPP (no decide)", snpp)):
                for l in xs:
                    print("      %s: %s" % (etq, l))

    if "KG" not in brazos:
        res["global"] = {l: global_ventana(res, l, solo_veto=True) for l in ("A", "B")}
        print("\n== VEREDICTO DE LA VENTANA %s (solo veto, sin gemelo):" % a.ventana)
        for l, v in res["global"].items():
            print("   KC lectura %s: %s" % (l, v))
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    # ---------------- 8. P2 suma
    print("\n== 8. P2, SUMA DE ERRORES BAJO 1 MW (Muy Bajo perdidas + negativos limpios publicados), por pasada")
    excluir = not cfg["solo_tabla"]; res["suma"] = {}
    for lectura in ("A", "B"):
        for s in SENS:
            fk = E.suma_errores(TK, "control", prot, lectura, cfg, s, excluir)
            fc = E.suma_errores(TK, "brazo", prot, lectura, cfg, s, excluir)
            sk, sc = sum(fk[:2]), sum(fc[:2])
            Tg = T[("K", "KG")]
            rd = len(E.errores_por_pasada(Tg, "control", prot, lectura, cfg, s, excluir) ^ E.errores_por_pasada(Tg, "brazo", prot, lectura, cfg, s, excluir))
            ver = ("INDECIDIBLE" if not (decide and huella_ok and q2_ok) else "GANA" if sc < sk - rd else "PIERDE" if sc > sk + rd else "EMPATE")
            techo = "DENTRO" if abs(sc - sk) <= TECHO_P2[s] else "FUERA (el sustrato no lo explica: trazar antes de leer)"
            res["veredicto"]["P2|%s|%s" % (s, lectura)] = ver; res["veredicto"]["P2b|%s|%s" % (s, lectura)] = techo
            res["suma"]["%s|%s" % (s, lectura)] = {"K": sk, "KC": sc, "ruido": rd}
            print("   lectura %s %-8s K: Muy Bajo perdidas %d de %d, negativos publicados %d de %d, suma %d | KC: %d, %d, suma %d | ruido %d -> %s | techo %d: %s" % (
                lectura, s, fk[0], fk[3], fk[1], fk[4], sk, fc[0], fc[1], sc, rd, ver, TECHO_P2[s], techo))

    # ---------------- 9. P3 magnitud
    print("\n== 9. P3, MAGNITUD contra MIROVA, pareada (d = |log10(KC/MIROVA)| - |log10(K/MIROVA)|)")
    for s in SENS:
        D = E.diferencias_magnitud(TK, s, cfg)
        dG = [x[1] for x in E.diferencias_magnitud(T[("K", "KG")], s, cfg)]
        rz = abs(statistics.median(dG)) if dG else 0.0
        if len(D) < N_MIN_MAGNITUD:
            ver = "SIN SUSTRATO"; print("   %-8s n %d: SIN SUSTRATO" % (s, len(D)))
        else:
            d = [x[1] for x in D]; md = statistics.median(d); lo, hi = E.bootstrap_mediana(d)
            ver = "INDECIDIBLE" if not (decide and huella_ok and q2_ok) else ("FALLA" if (lo > 0 and md > rz) else "CUMPLE")
            print("   %-8s n %3d | razon mediana K %.3f, KC %.3f | d mediana %+.3f [%+.3f, %+.3f] | ruido %.3f -> %s" % (
                s, len(D), statistics.median(x[3] for x in D), statistics.median(x[4] for x in D), md, lo, hi, rz, ver))
        res["veredicto"]["P3|%s" % s] = ver

    # ---------------- 10. P4 posicion contra MIROVA
    print("\n== 10. P4, PUBLICACIONES CON EL CUMULO FUERA DE LA CAJA (8 volcanes centrados) contra el techo de MIROVA")
    for s in SENS:
        tope = E.wilson_sup(*MIROVA_FUERA[s])
        partes = []
        for n, par, lado in (("K", ("K", "KC"), "control"), ("KC", ("K", "KC"), "brazo"), ("B", ("B", "BC"), "control"), ("BC", ("B", "BC"), "brazo")):
            if par not in T:
                continue
            xs = [(k, v[lado]) for k, v in T[par].items() if lado in v and k.split("|")[1] == s and v[lado]["pub"] and k.split("|")[0] in CENTRADOS]
            f = sum(fuera_de_caja(x, k.split("|")[0], anclas) for k, x in xs)
            frac = f / len(xs) if xs else None
            ver = "SIN SUSTRATO" if frac is None else ("CUMPLE" if frac <= tope else "FALLA")
            if n in ("KC", "BC"):
                res["veredicto"]["P4|%s|%s" % (n, s)] = ver
            partes.append("%s %d de %d%s" % (n, f, len(xs), (" (%.1f %%) %s" % (100 * frac, ver)) if frac is not None else ""))
        print("   %-8s techo MIROVA %d de %d, Wilson superior %.1f %% | %s" % (s, MIROVA_FUERA[s][0], MIROVA_FUERA[s][1], 100 * tope, " | ".join(partes)))

    res["global"] = {l: global_ventana(res, l) for l in ("A", "B")}
    res["mecanismo"] = mecanismo(res)
    print("\n== VEREDICTO DE LA VENTANA %s (reglas de §6):" % a.ventana)
    for l, v in res["global"].items():
        print("   KC lectura %s: %s" % (l, v))
    print("   mecanismo (B -> BC): %s" % res["mecanismo"])
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def mecanismo(res):
    v = res["veredicto"]
    if not res["huella"].get("BC", False):
        return "INDECIDIBLE: la caja no dejo huella en BC (cableado o instrumento; trazar por etapa, A118)"
    q1, q2 = v.get("Q1|BC"), v.get("Q2|BC")
    if "INDECIDIBLE" in (q1, q2) or q2 == "FALLA":
        return "INDECIDIBLE: Q1 %s, Q2 %s" % (q1, q2)
    return {"CUMPLE": "LA CAJA ACTUA: apaga la mitad o mas de lo expuesto", "FALLA": "LA CAJA NO APAGA: lo expuesto sobrevive al umbral estricto",
            "SIN SUSTRATO": "SIN SUSTRATO"}[q1] + " | P4 de BC en VIIRS 375: %s" % v.get("P4|BC|VIIRS375")


def global_ventana(res, lectura, solo_veto=False):
    """§6. Orden: controles, huella y Q2; veto; indecidibles; pendientes; suma; magnitud."""
    v = res["veredicto"]
    if not (res["controles_ok"] and res["cableado"].get("K") and res["cableado"].get("KC") and res["cableado"].get("KG", True)):
        return "INDECIDIBLE"
    if not res.get("huella", {}).get("BC", True) or v.get("Q2|BC") == "FALLA":
        return "INDECIDIBLE (el control positivo de la palanca no paso: huella o Q2)"
    p1 = [v.get("P1|%s|%s" % (s, lectura)) for s in SENS]
    if "VETADO" in p1:
        return "NO CUMPLE (veto)"
    if solo_veto:
        return ("INDECIDIBLE" if "INDECIDIBLE" in p1 else "PENDIENTE DE REPETICION" if "PENDIENTE DE REPETICION" in p1
                else "SIN SUSTRATO" if all(x == "SIN SUSTRATO" for x in p1) else "CUMPLE (veto)")
    p2 = [v.get("P2|%s|%s" % (s, lectura)) for s in SENS]; p3 = [v.get("P3|%s" % s) for s in SENS]
    if "INDECIDIBLE" in p1 + p2 + p3:
        return "INDECIDIBLE"
    if "PENDIENTE DE REPETICION" in p1:
        return "PENDIENTE DE REPETICION"
    if "PIERDE" in p2:
        return "NO CUMPLE (suma de errores)"
    if "GANA" not in p2:
        return "NO CUMPLE (no mejora el criterio: la caja es inerte sobre el candidato)"
    out = "CUMPLE"
    if "FALLA" in p3:
        out = "CUMPLE EN DETECCION, FALLA EN MAGNITUD (decide Nicolas)"
    if "SIN SUSTRATO" in p1:
        out += " | veto sin sustrato en %s" % [s for s, x in zip(SENS, p1) if x == "SIN SUSTRATO"]
    if any(v.get("P4|KC|%s" % s) == "FALLA" for s in SENS):
        out += " | publica fuera de la caja mas que MIROVA (P4)"
    return out


def combinar(archivos):
    """§6: el peor estado manda, por lectura. Un NO CUMPLE en una ventana es definitivo."""
    rs = [json.load(open(f, encoding="utf-8")) for f in archivos]
    orden = ("NO CUMPLE (veto)", "NO CUMPLE (suma", "INDECIDIBLE", "PENDIENTE DE REPETICION", "NO CUMPLE (no mejora", "CUMPLE EN DETECCION", "CUMPLE", "SIN SUSTRATO")
    print("== VEREDICTO COMBINADO (%s)" % ", ".join(r["ventana"] for r in rs))
    for l in ("A", "B"):
        estados = [(r["ventana"], r["global"][l]) for r in rs]
        peor = min(estados, key=lambda e: next(i for i, o in enumerate(orden) if e[1].startswith(o)))
        print("   KC lectura %s: %s | por ventana %s" % (l, peor[1], estados))
    for r in rs:
        if "mecanismo" in r:
            print("   mecanismo (%s): %s" % (r["ventana"], r["mecanismo"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combinar", nargs="+")
    ap.add_argument("--ventana", choices=sorted(VENTANAS))
    ap.add_argument("--raiz", action="append", default=[])
    ap.add_argument("--logs", action="append", default=[])
    ap.add_argument("--out"); ap.add_argument("--tmp"); ap.add_argument("--repeticion")
    # solo para la prueba del evaluador (probar_evaluar_caja.py): no cambian ninguna regla
    ap.add_argument("--vols"); ap.add_argument("--desde"); ap.add_argument("--hasta"); ap.add_argument("--ref")
    ap.add_argument("--capas-del-repo", dest="capas_del_repo", action="store_true")
    ap.add_argument("--produccion", default=str(RAIZ / "data" / "mirova_equivalent"))
    a = ap.parse_args()
    if a.combinar:
        return combinar(a.combinar)
    if not (a.ventana and a.raiz and a.out):
        ap.error("--ventana, --raiz y --out son obligatorios")
    return evaluar(a)


if __name__ == "__main__":
    sys.exit(main())
