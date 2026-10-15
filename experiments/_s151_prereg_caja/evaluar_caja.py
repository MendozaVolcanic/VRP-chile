# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. Evaluador del A/B de la caja de 5 x 5 km (D18), experiments/_s151_prereg_caja/PREREGISTRO.md
(version 2). Implementa las reglas de §6 y §7 del pre-registro TAL CUAL; si una regla cambia, cambia aca y alla en el
mismo commit.

QUE REUSA, SIN REIMPLEMENTAR. Lo de experiments/_s151_prereg_fk_11/evaluar_fk.py que no depende de los brazos de esa
prueba: la tabla por pasada (armar_tabla.py, predicado del tablero ejecutado con node, A97), la proteccion
(scripts/clase_mirova.alerta_protegida, lecturas A y B), la referencia congelada con capas y manifiesto, la suma de
errores, las pasadas discordantes, la magnitud pareada con bootstrap y la lectura de FLAGS_BRAZO por directorio de
logs. La geometria de la caja es la de sustrato.py (= pipeline/scan_geometry.py::roi_mask_bbox).

QUE DECIDE (version 2, tras el verificador del PR #800):
  - El VETO de KC (K mas la caja) contra K, en las dos pasadas dirigidas D1 y D2: son las unicas protegidas del
    candidato que la caja puede perder (sustrato.py). Sin gemelo: una perdida queda PENDIENTE DE REPETICION.
  - El MECANISMO en V1 con B y BC: Q1 (lo expuesto se apaga mas que lo de adentro, prueba exacta de Fisher contra la
    tasa de cambio de lo de adentro, que es el nulo medido del propio run), Q2 (lo de adentro casi no cambia; tope del
    instrumento, elegido) y P4 (fraccion de publicaciones fuera de la caja contra la de MIROVA).
  - TODO se decide en los 8 volcanes donde el centro de grilla de MIROVA esta junto al crater; Tupungatito, Puyehue
    Cordon Caulle y Planchon Peteroa se informan aparte (la caja del brazo, centrada en el crater, no es la de MIROVA).
  - Si alguien corre K, KC y KG en V1 (--brazos), el evaluador tambien aplica P2 y P3 con las reglas de ruido de la
    version 2: un cambio que no supera el ruido es INDECIDIBLE, no "inerte"; el ruido tiene que ser menor que el techo
    de lo que la caja puede mover; P3 se mide solo sobre los pares cuya magnitud cambia.
  - Seccion 11 (INFORMA, agregada tras la decision D-9 del 2026-10-15, issue #811): el mismo evaluador, sobre las
    mismas tablas, con las reglas de las alertas de 0,05 MW o menos (SN, SE, original y variantes con 0,04). DECIDE
    la original, vigente al sellar el pre-registro (nota D-9 en PREREGISTRO.md). El JSON suma la clave `reglas_d9`
    y conserva todas las anteriores.

Uso:
  python evaluar_caja.py --ventana V1 --raiz <run V1> --logs <run V1>/logs --out v1.json       (B y BC)
  python evaluar_caja.py --ventana D1 --raiz <run D1> --logs <run D1>/logs --out d1.json       (K y KC; igual D2)
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

# ---------------------------------------------------------------- lo que el pre-registro fija
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
           "brazos": ("B", "BC"), "vols": None},
    "D1": {"desde": "2026-03-14", "hasta": "2026-03-27", "ref": CONG_V2, "solo_tabla": True, "brazos": ("K", "KC"), "vols": ("Lascar",)},
    "D2": {"desde": "2026-06-10", "hasta": "2026-06-10", "ref": CONG_V2, "solo_tabla": True, "brazos": ("K", "KC"), "vols": ("Isluga",)},
}
SENS = ("MODIS", "VIIRS375", "VIIRS750")
CORRIDOS = ("Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa")
CENTRADOS = [v for v in bp.VOLS if v not in CORRIDOS]
# distancia_mirova_salida.txt y prediccion_mirova_salida.txt, V1, 8 centrados (las dos lecturas del centro de la caja
# coinciden alli): alertas de MIROVA fuera de su caja, contando las ambiguas de 2,5 a 3,54 km como fuera (cota superior).
MIROVA_FUERA = {"VIIRS375": (5, 223), "VIIRS750": (0, 34), "MODIS": (0, 8)}
# sustrato_salida.txt, "CENTRADOS CONTRA CORRIDOS": techo de lo que la caja puede mover la suma bajo 1 MW del candidato en
# V1, 8 centrados (F en VIIRS, K en MODIS). Solo se usa si alguien corre K, KC y KG en V1.
TECHO_P2 = {"VIIRS375": 3, "VIIRS750": 1, "MODIS": 1}
ALFA_Q1 = 0.05      # prueba exacta de Fisher, una cola
Q2_TOPE = 0.12      # umbral del INSTRUMENTO, elegido (heredado de S147, 5 de 42), sin nulo medido
Q1_S147 = 0.5       # la regla de S147 ("la mitad o mas"): se informa, no decide
N_MIN_MAGNITUD = 5


def es_centrado(k):
    return k.split("|")[0] in CENTRADOS


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


def fisher_una_cola(a, n1, b, n0):
    """P(X >= a) con X hipergeometrica: a exitos de n1 en el grupo 1, b de n0 en el grupo 0 (margenes fijos)."""
    tot, k = n1 + n0, a + b
    den = math.comb(tot, k)
    return sum(math.comb(n1, x) * math.comb(n0, k - x) for x in range(a, min(n1, k) + 1)) / den if den else 1.0


def diferencias_que_cambian(T, s, cfg):
    """P3 (arreglo D3): solo los pares cuya magnitud publicada cambia; en los demas d = 0 por construccion."""
    return [x for x in E.diferencias_magnitud(T, s, cfg) if es_centrado(x[0]) and abs(x[2]) > 1e-9]


# ---------------------------------------------------------------- evaluacion de una ventana
def evaluar(a):
    cfg = dict(VENTANAS[a.ventana])
    for k in ("desde", "hasta"):
        if getattr(a, k):
            cfg[k] = getattr(a, k)
    if a.ref:
        cfg["ref"] = Path(a.ref)
    if a.brazos:
        cfg["brazos"] = tuple(a.brazos.split(","))
    vols = a.vols.split(",") if a.vols else list(cfg["vols"] or bp.VOLS)
    brazos = cfg["brazos"]; base = brazos[0]
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / ("_tmp_" + a.ventana); tmp.mkdir(parents=True, exist_ok=True)
    raiz = E.fusionar(a.raiz, tmp, brazos, vols)
    faltan = [(n, v) for n in brazos for v in vols if not (raiz / BRAZOS[n] / (v + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos o volcanes: %s. No se evalua a medias." % faltan[:20])
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); anclas = S.lc.anclas()
    res = {"ventana": a.ventana, "desde": cfg["desde"], "hasta": cfg["hasta"], "brazos": list(brazos), "veredicto": {},
           "sha256_index_html": hashlib.sha256((RAIZ / "frontend" / "index.html").read_bytes()).hexdigest()}
    print("== VENTANA %s: %s a %s | volcanes %s | brazos %s | %s | decide en los 8 centrados" % (
        a.ventana, cfg["desde"], cfg["hasta"], ",".join(vols), brazos, "decide la tabla sola" if cfg["solo_tabla"] else "decide tabla y OCR"))
    print("   predicado del tablero: frontend/index.html sha256", res["sha256_index_html"])
    ref = E.archivos_ref(cfg, tmp)
    res["referencia_ok"] = E.referencia_congelada(cfg["ref"], ref[2], a.capas_del_repo)

    pares = [p for p in (("K", "KC"), ("K", "KG"), ("B", "BC")) if set(p) <= set(brazos)]
    # D-9 (seccion 11): la corrida anidada con otra regla reusa las tablas de la principal (mismas publicaciones).
    T = getattr(a, "_T_base", None) or {p: E.tabla(raiz / BRAZOS[p[0]], raiz / BRAZOS[p[1]], ref, cfg["desde"], cfg["hasta"], tmp / ("t_%s_%s.json" % p)) for p in pares}
    a._T_base = T
    R = {n: E.crudos(raiz, n, vols, cfg["desde"], cfg["hasta"]) for n in brazos}
    PX = {n: clases_por_pasada(raiz, n, vols, cfg["desde"], cfg["hasta"], anclas, inner) for n in brazos}
    todas = set().union(*[set(t) for t in T.values()])
    if getattr(a, "_regla", None) is not None:
        T = reetiquetar(a, T, todas, ref, cfg)
    prot = E.proteccion(todas, ref, cfg["desde"], cfg["hasta"])

    # ---------------- 1. cobertura
    print("\n== 1. COBERTURA (A108), contra el brazo %s" % base)
    claves_ = {n: set(R[n]) for n in brazos}; mal = False
    for n in brazos:
        d1, d2 = claves_[base] - claves_[n], claves_[n] - claves_[base]
        if d1 or d2:
            mal = True; print("   %-3s le faltan %d pasadas de %s y tiene %d que %s no %s" % (n, len(d1), base, len(d2), base, sorted(d1 | d2)[:5]))
    protegidas = sorted(k for k in todas if prot[k]["A"] or prot[k]["B"])
    sin_rec = {k: [n for n in brazos if k not in claves_[n]] for k in protegidas}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    print("   protegidas (A o B) sin record en algun brazo:", sin_rec or "ninguna")
    prod = E.claves_produccion(Path(a.produccion), vols, cfg["desde"], cfg["hasta"])
    cortos = ["%s %s: faltan %d de %d" % (v, s, len(ks - claves_[base]), len(ks)) for (v, s), ks in sorted(prod.items())
              if len(ks - claves_[base]) > E.MAX_FALTA_CONTRA_PRODUCCION * len(ks)]
    print("   %s contra produccion: %s" % (base, "; ".join(cortos) if cortos else "en ningun volcan y sensor falta mas del 5 % de las pasadas de produccion"))
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
                    prob.append("%s: el log no trae %s (workflow anterior a esta tarea)" % (donde, falta)); continue
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
        if not {c, x} <= set(brazos):
            continue
        tc = sum((PX[c][k] for k in PX[c]), collections.Counter()); tx = sum((PX[x][k] for k in PX[x]), collections.Counter())
        bien = tx["C"] < tc["C"]
        res["huella"][x] = bien
        print("   %s: corona C %d -> %d | caja CK %d -> %d | %s" % (x, tc["C"], tx["C"], tc["CK"], tx["CK"],
              "la caja actuo" if bien else "SIN HUELLA en la corona" + (" (control positivo: INDECIDIBLE, trazar por etapa, A118)" if x == "BC" else " (informa)")))

    # ---------------- 5. determinismo (solo si hay gemelo)
    ruido = set(); det_ok = True; res["ruido_por_sensor"] = {}
    if ("K", "KG") in T:
        print("\n== 5. DETERMINISMO K contra KG, 8 centrados: las discordantes tienen que ser MENOS que el techo de la caja (arreglo D4)")
        for s in SENS:
            amb = [(k, v) for k, v in T[("K", "KG")].items() if k.split("|")[1] == s and len(v) == 2 and es_centrado(k)]
            dif = {k for k, v in amb if v["control"]["pub"] != v["brazo"]["pub"]}; ruido |= dif
            ok = bool(amb) and len(dif) < TECHO_P2[s]; det_ok &= ok
            res["ruido_por_sensor"][s] = len(dif)
            print("   %-8s %5d pasadas, distintas %d | techo %d | %s" % (s, len(amb), len(dif), TECHO_P2[s], "OK" if ok else "FALLA"))
    res["determinismo_ok"] = det_ok
    res["controles_ok"] = res["cobertura_ok"] and res["version_ok"] and det_ok and res["referencia_ok"]
    print("\n== CONTROLES GENERALES:", "OK" if res["controles_ok"] else "FALLAN: ningun veredicto decide")

    T_rep = None
    if a.repeticion:
        rr = Path(a.repeticion)
        T_rep = E.tabla(rr / BRAZOS["K"], rr / BRAZOS["KC"], ref, cfg["desde"], cfg["hasta"], tmp / "rep_K_KC.json")

    # ---------------- 6. mecanismo B -> BC
    if ("B", "BC") in T:
        mecanismo_seccion(res, T[("B", "BC")], PX, anclas)
    huella_ok = res["huella"].get("BC", True); q2_ok = res["veredicto"].get("Q2|BC") != "FALLA"

    if ("K", "KC") not in T:
        res["global"] = None; res["mecanismo"] = mecanismo(res)
        print("\n== VEREDICTO DE LA VENTANA %s: no hay K ni KC (solo mecanismo) | mecanismo: %s" % (a.ventana, res["mecanismo"]))
        return cerrar(a, res)
    TK = T[("K", "KC")]
    decide = res["controles_ok"] and res["cableado"]["K"] and res["cableado"]["KC"] and res["cableado"].get("KG", True) and huella_ok and q2_ok

    # ---------------- 7. P1 veto
    print("\n== 7. P1, VETO: protegidas que K publica y KC no (decide en los 8 centrados)")
    for lectura in ("A", "B"):
        for s in SENS:
            netas, ruidosas, pend, desc, snpp, recup, info, n_pub = [], [], [], [], [], [], [], 0
            for k, v in TK.items():
                if len(v) != 2 or k.split("|")[1] != s or not prot[k][lectura]:
                    continue
                c, b = v["control"], v["brazo"]
                if b["pub"] and not c["pub"]:
                    recup.append(k)
                if not c["pub"] or b["pub"]:
                    n_pub += bool(c["pub"]) and es_centrado(k)
                    continue
                linea = "%s | MIROVA %s MW | %s | pixeles de K: %s" % (k, c["vrp_ref"], c["plataforma"], dict(PX["K"].get(k, {})))
                if not es_centrado(k):
                    info.append(linea); continue
                n_pub += 1
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
            ver = ("INDECIDIBLE" if not decide else "VETADO" if netas else "INDECIDIBLE" if ruidosas
                   else "PENDIENTE DE REPETICION" if pend else "SIN SUSTRATO" if n_pub == 0 else "CUMPLE")
            res["veredicto"]["P1|%s|%s" % (s, lectura)] = ver
            print("   lectura %s %-8s protegidas que K publica %3d | perdidas netas %d, ruidosas %d, pendientes %d, descartadas %d, solo OCR Suomi NPP %d | recuperadas %d | corridos (informa) %d | %s" % (
                lectura, s, n_pub, len(netas), len(ruidosas), len(pend), len(desc), len(snpp), len(recup), len(info), ver))
            for etq, xs in (("perdida", netas), ("perdida ruidosa", ruidosas), ("PENDIENTE DE REPETICION", pend),
                            ("ruido confirmado por la repeticion", desc), ("solo OCR Suomi NPP (no decide)", snpp), ("volcan corrido (informa)", info)):
                for l in xs:
                    print("      %s: %s" % (etq, l))

    if ("K", "KG") not in T:
        res["global"] = {l: global_ventana(res, l, solo_veto=True) for l in ("A", "B")}
        res["mecanismo"] = mecanismo(res) if "BC" in brazos else None
        print("\n== VEREDICTO DE LA VENTANA %s (solo veto, sin gemelo):" % a.ventana)
        for l, v in res["global"].items():
            print("   KC lectura %s: %s" % (l, v))
        return cerrar(a, res)

    # ---------------- 8. P2 suma (solo si se corre K, KC y KG en V1)
    print("\n== 8. P2, SUMA DE ERRORES BAJO 1 MW, 8 centrados (arreglo D4: un cambio dentro del ruido es INDECIDIBLE, no inerte)")
    excluir = not cfg["solo_tabla"]; res["suma"] = {}
    Tc = {k: v for k, v in TK.items() if es_centrado(k)}; Tgc = {k: v for k, v in T[("K", "KG")].items() if es_centrado(k)}
    for lectura in ("A", "B"):
        for s in SENS:
            fk = E.suma_errores(Tc, "control", prot, lectura, cfg, s, excluir)
            fc = E.suma_errores(Tc, "brazo", prot, lectura, cfg, s, excluir)
            sk, sc = sum(fk[:2]), sum(fc[:2])
            rd = len(E.errores_por_pasada(Tgc, "control", prot, lectura, cfg, s, excluir) ^ E.errores_por_pasada(Tgc, "brazo", prot, lectura, cfg, s, excluir))
            if not decide or rd >= TECHO_P2[s]:
                ver = "INDECIDIBLE"
            elif sc < sk - rd:
                ver = "GANA"
            elif sc > sk + rd:
                ver = "PIERDE"
            elif sc == sk and rd == 0:
                ver = "EMPATE"
            else:
                ver = "INDECIDIBLE"
            techo = "DENTRO" if abs(sc - sk) <= TECHO_P2[s] else "FUERA (el sustrato no lo explica: trazar antes de leer)"
            res["veredicto"]["P2|%s|%s" % (s, lectura)] = ver; res["veredicto"]["P2b|%s|%s" % (s, lectura)] = techo
            res["suma"]["%s|%s" % (s, lectura)] = {"K": sk, "KC": sc, "ruido": rd}
            print("   lectura %s %-8s K: Muy Bajo perdidas %d de %d, negativos publicados %d de %d, suma %d | KC: %d, %d, suma %d | ruido %d (techo %d) -> %s | techo: %s" % (
                lectura, s, fk[0], fk[3], fk[1], fk[4], sk, fc[0], fc[1], sc, rd, TECHO_P2[s], ver, techo))

    # ---------------- 9. P3 magnitud, solo pares que cambian
    print("\n== 9. P3, MAGNITUD contra MIROVA, SOLO en los pares cuya magnitud cambia (arreglo D3), 8 centrados")
    for s in SENS:
        D = diferencias_que_cambian(TK, s, cfg)
        dG = [x[1] for x in diferencias_que_cambian(T[("K", "KG")], s, cfg)]
        rz = abs(statistics.median(dG)) if dG else 0.0
        if len(D) < N_MIN_MAGNITUD:
            ver = "SIN SUSTRATO"; print("   %-8s pares que cambian %d: SIN SUSTRATO" % (s, len(D)))
        else:
            d = [x[1] for x in D]; md = statistics.median(d); lo, hi = E.bootstrap_mediana(d)
            ver = "INDECIDIBLE" if not decide else ("FALLA" if (lo > 0 and md > rz) else "CUMPLE")
            print("   %-8s pares que cambian %3d | d mediana %+.3f [%+.3f, %+.3f] | ruido %.3f -> %s" % (s, len(D), md, lo, hi, rz, ver))
        res["veredicto"]["P3|%s" % s] = ver

    p4_seccion(res, T, anclas)
    res["global"] = {l: global_ventana(res, l) for l in ("A", "B")}
    res["mecanismo"] = mecanismo(res) if "BC" in brazos else None
    print("\n== VEREDICTO DE LA VENTANA %s (reglas de §7):" % a.ventana)
    for l, v in res["global"].items():
        print("   KC lectura %s: %s" % (l, v))
    print("   mecanismo (B -> BC): %s" % res["mecanismo"])
    return cerrar(a, res)


# ---------------------------------------------------------------- D-9 (issue #811), seccion 11: INFORMA, no decide
def reetiquetar(a, T, todas, ref, cfg):
    """Las tablas con la etiqueta de MIROVA segun la regla D-9 de `a._regla` (modo, umbral); las publicaciones no
    cambian. Como en evaluar_fk.p2_tres_reglas: si la etiqueta original re-calculada difiere de la de la tabla en una
    pasada, se conserva la de la tabla y la regla solo mueve las pasadas que ella misma cambia."""
    modo, umbral = a._regla
    claves_ = sorted(todas)
    base = E.etiquetas_regla(claves_, ref, cfg["desde"], cfg["hasta"], "original")
    labs = base if modo == "original" else E.etiquetas_regla(claves_, ref, cfg["desde"], cfg["hasta"], modo, umbral)
    tabla_lab = {}
    for t in T.values():
        for k, v in t.items():
            for x in v.values():
                tabla_lab.setdefault(k, x["lab"])
    nuevo = {k: (labs[k] if labs[k] != base[k] else tabla_lab.get(k, base[k])) for k in claves_}
    a._distintas = sum(1 for k in claves_ if k in tabla_lab and tabla_lab[k] != base[k])
    a._cambian = {"%s->%s" % kk: n for kk, n in collections.Counter(
        (tabla_lab.get(k), nuevo[k]) for k in claves_ if nuevo[k] != tabla_lab.get(k)).items()}
    return {p: {k: {lado: dict(x, lab=nuevo[k]) for lado, x in v.items()} for k, v in t.items()} for p, t in T.items()}


def seccion_d9(a, res):
    """El pre-registro de la caja se sello antes de D-9 y DECIDE con la etiqueta original (todo lo de arriba). Aqui
    se vuelve a correr el mismo evaluador sobre las mismas tablas con cada regla (SN, SE, original y las variantes con
    0,04), en silencio, y se informa su veredicto. La regla original tiene que reproducir lo de arriba (autocontrol).
    P1 (el veto) no depende de la etiqueta; lo que puede moverse es el mecanismo (Q1, Q2, P4), P2 y P3."""
    import contextlib, copy, io
    print("\n== 11. VEREDICTO CON LAS REGLAS DE D-9 (issue #811; INFORMA. Decide la del pre-registro: original)")
    out = {}
    for nombre, modo, umbral in E.REGLAS_D9:
        b = copy.copy(a); b._regla = (modo, umbral)
        with contextlib.redirect_stdout(io.StringIO()):
            evaluar(b)
        r = b._res
        out[nombre] = {"global": r.get("global"), "mecanismo": r.get("mecanismo"), "veredicto": r["veredicto"],
                       "cambian": b._cambian, "control_distintas": b._distintas}
        dif = sorted(k for k in set(r["veredicto"]) | set(res["veredicto"]) if r["veredicto"].get(k) != res["veredicto"].get(k))
        print("   regla %-8s (%s, umbral %s) etiquetas que cambian: %s | control, original re-calculada distinta de la tabla en %d" % (
            nombre, modo, umbral, b._cambian or "ninguna", b._distintas))
        for l in ("A", "B"):
            if r.get("global"):
                g = r["global"][l]
                print("      KC lectura %s: %s%s" % (l, g, "" if g == (res.get("global") or {}).get(l) else "   <-- DISTINTO del que decide"))
        if r.get("mecanismo") is not None:
            print("      mecanismo: %s%s" % (r["mecanismo"], "" if r["mecanismo"] == res.get("mecanismo") else "   <-- DISTINTO del que decide"))
        if dif:
            print("      veredictos distintos del que decide: %s" % ", ".join("%s %s -> %s" % (k, res["veredicto"].get(k), r["veredicto"].get(k)) for k in dif))
    o = out["original"]
    out["autocontrol_original_ok"] = (o["global"] == res.get("global") and o["mecanismo"] == res.get("mecanismo")
                                      and o["veredicto"] == res["veredicto"])
    print("   autocontrol: la regla original reproduce lo que decide: %s" % ("OK" if out["autocontrol_original_ok"] else "FALLA (la seccion 11 no es comparable)"))
    return out


def cerrar(a, res):
    """Fin de una ventana. En la corrida anidada de la seccion 11 solo devuelve el resultado; en la principal agrega la
    seccion 11 y escribe la salida (el JSON conserva todas las claves de antes y suma `reglas_d9`)."""
    if getattr(a, "_regla", None) is not None:
        a._res = res
        return 0
    res["reglas_d9"] = seccion_d9(a, res)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def mecanismo_seccion(res, TB, PX, anclas):
    print("\n== 6. MECANISMO B -> BC (control positivo de la palanca), 8 centrados; corridos aparte")
    ok_ctrl = res["controles_ok"] and res["cableado"]["B"] and res["cableado"]["BC"]
    for grupo, sel in (("8 centrados (decide)", es_centrado), ("3 corridos (informa)", lambda k: not es_centrado(k))):
        base = [(k, v) for k, v in TB.items() if len(v) == 2 and sel(k) and v["control"]["lab"] == "neg_limpio" and v["control"]["pub"]]
        exp = [k for k, v in base if PX["B"].get(k, collections.Counter())["CK"] == 0 and PX["B"].get(k, collections.Counter())["C"] > 0]
        den = [k for k, v in base if PX["B"].get(k, collections.Counter())["CK"] > 0]
        apag = sum(1 for k in exp if not TB[k]["brazo"]["pub"]); camb = sum(1 for k in den if not TB[k]["brazo"]["pub"])
        p = fisher_una_cola(apag, len(exp), camb, len(den))
        if grupo.startswith("8"):
            if not ok_ctrl:
                q1 = q2 = "INDECIDIBLE"
            else:
                q1 = ("SIN SUSTRATO" if not exp or not den else
                      "CUMPLE" if (apag / len(exp) > camb / len(den) and p < ALFA_Q1) else "FALLA")
                q2 = "CUMPLE" if (not den or camb <= Q2_TOPE * len(den)) else "FALLA"
            res["veredicto"].update({"Q1|BC": q1, "Q2|BC": q2})
        else:
            q1 = q2 = "(informa)"
        print("   %s: negativos limpios expuestos que B publica %d, BC apaga %d (%.1f %%) | con calor en la caja %d, BC cambia %d (%.1f %%) | Fisher una cola p = %.4g" % (
            grupo, len(exp), apag, 100 * apag / len(exp) if exp else 0, len(den), camb, 100 * camb / len(den) if den else 0, p))
        print("      Q1 (lo expuesto se apaga mas que lo de adentro, p < %.2f) -> %s | Q2 (lo de adentro cambia 12 %% o menos, umbral del instrumento) -> %s | regla S147, la mitad o mas: %s" % (
            ALFA_Q1, q1, q2, "si" if exp and apag >= math.ceil(Q1_S147 * len(exp)) else "no"))
        pexp = [k for k, v in TB.items() if len(v) == 2 and sel(k) and v["control"]["lab"] == "pos" and v["control"]["pub"]
                and PX["B"].get(k, collections.Counter())["CK"] == 0 and PX["B"].get(k, collections.Counter())["C"] > 0]
        print("      (informa) alertas de MIROVA expuestas que B publica: %d; BC conserva %d" % (len(pexp), sum(TB[k]["brazo"]["pub"] for k in pexp)))
    p4_seccion(res, {("B", "BC"): TB}, anclas)


def p4_seccion(res, T, anclas):
    print("\n== P4, PUBLICACIONES CON EL CUMULO FUERA DE LA CAJA (8 centrados) contra el techo de MIROVA")
    for s in SENS:
        tope = E.wilson_sup(*MIROVA_FUERA[s])
        partes = []
        for n, par, lado in (("K", ("K", "KC"), "control"), ("KC", ("K", "KC"), "brazo"), ("B", ("B", "BC"), "control"), ("BC", ("B", "BC"), "brazo")):
            if par not in T:
                continue
            xs = [(k, v[lado]) for k, v in T[par].items() if lado in v and k.split("|")[1] == s and v[lado]["pub"] and es_centrado(k)]
            f = sum(fuera_de_caja(x, k.split("|")[0], anclas) for k, x in xs)
            frac = f / len(xs) if xs else None
            ver = "SIN SUSTRATO" if frac is None else ("CUMPLE" if frac <= tope else "FALLA")
            if n in ("KC", "BC"):
                res["veredicto"]["P4|%s|%s" % (n, s)] = ver
            partes.append("%s %d de %d%s" % (n, f, len(xs), (" (%.1f %%) %s" % (100 * frac, ver)) if frac is not None else ""))
        print("   %-8s techo MIROVA %d de %d, Wilson superior %.1f %% | %s" % (s, MIROVA_FUERA[s][0], MIROVA_FUERA[s][1], 100 * tope, " | ".join(partes)))


def mecanismo(res):
    v = res["veredicto"]
    if not res["huella"].get("BC", False):
        return "INDECIDIBLE: la caja no dejo huella en BC (cableado o instrumento; trazar por etapa, A118)"
    q1, q2 = v.get("Q1|BC"), v.get("Q2|BC")
    if "INDECIDIBLE" in (q1, q2) or q2 == "FALLA":
        return "INDECIDIBLE: Q1 %s, Q2 %s" % (q1, q2)
    return {"CUMPLE": "LA CAJA ACTUA: apaga lo expuesto mas que lo de adentro", "FALLA": "LA CAJA NO APAGA: lo expuesto sobrevive al umbral estricto",
            "SIN SUSTRATO": "SIN SUSTRATO"}[q1] + " | P4 de BC en VIIRS 375: %s" % v.get("P4|BC|VIIRS375")


def global_ventana(res, lectura, solo_veto=False):
    """§7. Orden: controles, huella y Q2; veto; indecidibles; pendientes; suma; magnitud."""
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
    """§7: el peor estado de las ventanas con KC manda, por lectura; y si el mecanismo de V1 no paso su control (sin
    huella o Q2 FALLA), el veto de las dirigidas no se puede leer: la caja podria no haber actuado."""
    rs = [json.load(open(f, encoding="utf-8")) for f in archivos]
    print("== VEREDICTO COMBINADO (%s)" % ", ".join(r["ventana"] for r in rs))
    _combinar(rs, "   ")
    # D-9 (issue #811): lo mismo con cada regla de las alertas minimas. INFORMA; decide lo de arriba.
    if all("reglas_d9" in r for r in rs):
        print("== CON LAS REGLAS DE D-9 (informa; decide lo de arriba)")
        for nombre, _, _ in E.REGLAS_D9:
            _combinar([{**r, "global": r["reglas_d9"][nombre]["global"], "mecanismo": r["reglas_d9"][nombre]["mecanismo"]}
                       for r in rs], "   regla %-8s " % nombre)
    return 0


def _combinar(rs, pref):
    orden = ("NO CUMPLE (veto)", "NO CUMPLE (suma", "INDECIDIBLE", "PENDIENTE DE REPETICION", "NO CUMPLE (no mejora", "CUMPLE EN DETECCION", "CUMPLE", "SIN SUSTRATO")
    mec = [(r["ventana"], r.get("mecanismo")) for r in rs if r.get("mecanismo")]
    mec_mal = [m for m in mec if m[1].startswith("INDECIDIBLE")]
    for l in ("A", "B"):
        estados = [(r["ventana"], r["global"][l]) for r in rs if r.get("global")]
        if not estados:
            print("%sKC lectura %s: SIN VENTANA CON KC" % (pref, l)); continue
        peor = min(estados, key=lambda e: next(i for i, o in enumerate(orden) if e[1].startswith(o)))
        final = peor[1]
        if mec_mal and not final.startswith("NO CUMPLE (veto)"):
            final = "INDECIDIBLE (el mecanismo de %s no paso su control)" % mec_mal[0][0]
        print("%sKC lectura %s: %s | por ventana %s" % (pref, l, final, estados))
    for m in mec:
        print("%smecanismo (%s): %s" % ((pref,) + m))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combinar", nargs="+")
    ap.add_argument("--ventana", choices=sorted(VENTANAS))
    ap.add_argument("--raiz", action="append", default=[])
    ap.add_argument("--logs", action="append", default=[])
    ap.add_argument("--out"); ap.add_argument("--tmp"); ap.add_argument("--repeticion")
    ap.add_argument("--brazos", help="solo para correr K, KC y KG en V1 (fuera del despacho de este pre-registro) o en la prueba")
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
