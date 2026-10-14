# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Evaluador del A/B "F y K contra produccion (C0) en los 11 Tier A"
(experiments/_s151_prereg_fk_11/PREREGISTRO.md). Implementa las reglas de §5 y §6 del pre-registro TAL CUAL
estan escritas; si una regla cambia, cambia aca y en el pre-registro en el mismo commit (lecciones de D22 y #794).

QUE REUSA, SIN REIMPLEMENTAR. La tabla por pasada sale de experiments/_s149_prereg_invierno/armar_tabla.py
(etiquetador de scripts/banco_paridad.py, filtro diurno, referencia unificada y el predicado del tablero
EJECUTADO CON NODE desde frontend/index.html, A97). La alerta protegida es scripts/clase_mirova.alerta_protegida
(lecturas A y B, issue #782). Lo unico que este archivo agrega es la contabilidad del criterio de victoria de
docs/MISSION.md y los controles.

QUE MIDE, POR PASADA (la unidad en que el operador vive la alerta, A94), por sensor y por lectura:
  P1 veto: alertas protegidas que C0 publica y el candidato no.
  P2 suma de errores bajo 1 MW: alertas Muy Bajo que el brazo no publica + publicaciones en negativos limpios.
  P3 razon de magnitud contra MIROVA, pareada sobre las alertas que publican los dos.
  P4 movimiento del cumulo publicado (S147: apagar el Test 1 compite por el ancla).
Y los controles antes de mirar: cobertura pareja (A108), version de producto por pasada, cableado leido de la
linea FLAGS_BRAZO del log y de la huella en los records, determinismo (gemelo de C0, y F contra K en VIIRS,
porque la banda 22 solo la lee process_modis.py).

LAS DOS PREGUNTAS DEL INSTRUMENTO (probar_evaluar_fk.py): con brazos identicos da cero perdidas, EMPATE en la
suma y cero movimiento; con cada defecto sembrado sale el veredicto que corresponde; y sobre el run real de
Nevados de Chillan reproduce la suma de errores que publico su verificador (C0 52, F y K 7).

Uso (una ventana por corrida; V2 llega en dos despachos, se pasan los dos --raiz y los dos --logs):
  python evaluar_fk.py --ventana V1 --raiz <salidas run V1> --logs <salidas run V1>/logs --out v1.json
  python evaluar_fk.py --ventana V2 --raiz <V2a> --raiz <V2b> --logs <V2a>/logs --logs <V2b>/logs --ruido-de v1.json --out v2.json
  python evaluar_fk.py --combinar v1.json v2.json
"""
from __future__ import annotations

import argparse, collections, hashlib, io, json, math, random, statistics, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # reconfigure y no un TextIOWrapper nuevo: importado dos veces, cerraria el flujo
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)
import evaluar as ev  # noqa: E402
import clase_mirova as cm  # noqa: E402
bp = ev.bp
ARMAR = RAIZ / "experiments" / "_s149_prereg_invierno" / "armar_tabla.py"

# ---------------------------------------------------------------- lo que el pre-registro fija (§2, §3)
BRAZOS = {"C0": "_s146_ab_control", "F": "_s147_ab_sin_test1_max", "K": "_s149_ab_sin_test1_b22_max",
          "G": "_s151_ab_control_gemelo"}
# Lo que cada brazo DECLARA, resuelto por el codigo (diff_perfiles_salida.txt).
CLAVES = ("ENABLE_TEST1_PATH", "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY",
          "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER", "PATH_D_ONLY_CAP_MW")
DECLARADO = {"C0": (True, False, False, False, 5.0), "G": (True, False, False, False, 5.0),
             "F": (False, True, False, False, 5.0), "K": (False, True, True, False, 5.0)}
# Flags que el log trae desde S150/S151 y que en los cuatro brazos valen lo de produccion. Si la linea no los
# trae (logs anteriores), no se exigen.
EXTRA = {"ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": False, "ENABLE_VENT_ANCHORED_CLUSTERING": True}
VENTANAS = {"V1": {"desde": "2026-08-29", "hasta": "2026-10-08", "ref": AQUI / "_congelado_v1", "solo_tabla": False,
                   "brazos": ("C0", "F", "K", "G")},
            "V2": {"desde": "2026-03-01", "hasta": "2026-06-12", "ref": AQUI / "_congelado_v2", "solo_tabla": True,
                   "brazos": ("C0", "K")}}
INICIO_VIIRS_POR_PASADA = "2026-04-01"   # A119 (b)
SENS = ("MODIS", "VIIRS375", "VIIRS750")
SENS_CANDIDATO = {"F": ("VIIRS375", "VIIRS750"), "K": SENS}
# F tambien corre en MODIS (sus flags son globales, con banda 21): se imprime para que nadie lo adopte sin K.
SENS_INFORMA = {"F": ("MODIS",)}
UMBRAL_DETERMINISMO = 0.98               # heredado de S149/S150: misma decision en 98 de cada 100 pasadas
MOV_KM = 0.5                             # S147, experiments/_s147_pos/estabilidad_del_cumulo.py
S147_MOVIDAS_EN_ALERTA = (2, 149)        # estabilidad_salida.txt: "alerto 2 de 149"
N_MIN_MAGNITUD = 5
N_BOOT, SEMILLA = 2000, 0
MAX_FALTA_CONTRA_PRODUCCION = 0.05       # umbral del instrumento (elegido): pasadas de produccion que C0 puede no traer
BANDA_P6 = (0.80, 0.92)                  # A114: publicacion en negativos limpios de VIIRS 375 con el Test 1 encendido


def sha_lf(p):
    """sha256 con fin de linea LF (el mismo de congelar.py): autocrlf deja los CSV en CRLF en Windows."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def wilson_sup(k, n, z=1.96):
    p = k / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


# ---------------------------------------------------------------- carga
def fusionar(raices, tmp, brazos, vols):
    """Si V2 llega en dos despachos, junta los records de cada perfil y volcan en un solo directorio."""
    if len(raices) == 1:
        return Path(raices[0])
    dst = tmp / "fusion"
    for n in brazos:
        for v in vols:
            recs = []
            for r in raices:
                p = Path(r) / BRAZOS[n] / (v + ".json")
                if p.exists():
                    recs += json.load(open(p, encoding="utf-8"))["records"]
            if recs:
                (dst / BRAZOS[n]).mkdir(parents=True, exist_ok=True)
                json.dump({"records": recs}, open(dst / BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
    return dst


CAPA_HISTORICO, CAPA_RESPALDO = "consolidado_filas_perdidas.csv", "respaldo_20260408.csv"


def archivos_ref(cfg, tmp):
    """(consolidado, ocr, capas) que se le pasan a armar_tabla y a la proteccion. Con `solo_tabla`, el OCR es un
    CSV con solo el encabezado: reetiquetado de verdad (S150, H7), una alerta solo del OCR no es positiva.
    `capas` son las copias congeladas de la capa historica de la union y del respaldo del 2026-04-08 (verificador
    del PR #797, punto 2); None si el congelado no las trae, y entonces el cargador usa las del repo."""
    cons, ocr = cfg["ref"] / "registro_vrp_consolidado.csv", cfg["ref"] / "registro_vrp_ocr.csv"
    if cfg["solo_tabla"]:
        vacio = tmp / "ocr_vacio.csv"
        vacio.write_text(ocr.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
        ocr = vacio
    capas = {"historico": cfg["ref"] / CAPA_HISTORICO, "respaldo": cfg["ref"] / CAPA_RESPALDO}
    return cons, ocr, (capas if all(p.exists() for p in capas.values()) else None)


def tabla(control, brazo, ref, desde, hasta, out):
    cons, ocr, capas = ref
    extra = ["--historico", str(capas["historico"]), "--respaldo", str(capas["respaldo"])] if capas else []
    r = subprocess.run([sys.executable, str(ARMAR), "--control", str(control), "--brazo", str(brazo), "--cons", str(cons),
                        "--ocr", str(ocr), "--desde", desde, "--hasta", hasta, "--out", str(out)] + extra,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("armar_tabla fallo:\n" + r.stderr[-3000:])
    return json.loads(out.read_text(encoding="utf-8"))["pasadas"]


def crudos(raiz, nombre, vols, desde, hasta):
    """Lo que la tabla no expone: version del producto y disparo del Test 1, por pasada."""
    out = {}
    for v in vols:
        p = raiz / BRAZOS[nombre] / (v + ".json")
        if not p.exists():
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
            if b is None or not (desde <= t[:10] <= hasta):
                continue
            out["|".join((v, b, t[:16]))] = {"pv": r.get("product_version"), "t1": bool(r.get("triggered_test1"))}
    return out


def claves_produccion(dprod, vols, desde, hasta):
    """Pasadas (volcan|sensor|hora) que produccion tiene en la ventana, agrupadas por (volcan, sensor)."""
    out = collections.defaultdict(set)
    for v in vols:
        p = dprod / (v + ".json")
        if not p.exists():
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor")); t = r.get("datetime_utc", "")
            if b is not None and desde <= t[:10] <= hasta:
                out[(v, b)].add("|".join((v, b, t[:16])))
    return out


def flags_leidos(logs, nombre, vol):
    """La linea FLAGS_BRAZO del log de ESTE brazo y volcan en CADA directorio de logs, como [(dir, flags o None)].

    Verificador del PR #797, punto 1: la version anterior devolvia el primer log que encontraba, asi que con dos
    --logs (V2a y V2b) un job de V2b mal cableado pasaba sin que nadie lo leyera. Cada despacho es un job
    distinto y cada uno tiene que probar su cableado: un directorio sin el log cuenta como problema."""
    out = []
    for d in logs:
        p = Path(d) / ("%s_%s.log" % (BRAZOS[nombre], vol)); fl = None
        if p.exists():
            for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if linea.startswith("FLAGS_BRAZO "):
                    fl = json.loads(linea[len("FLAGS_BRAZO "):]); break
        out.append((Path(d).as_posix(), fl))
    return out


def proteccion(claves_, ref, desde, hasta):
    """Por pasada: protegida (lectura A y B, clase_mirova) y si la A descansa SOLO en filas del OCR de Suomi NPP,
    tramo en que la distancia y la clase del OCR pueden ser de otra pasada (A119, hito 2026-10-09). Lee la misma
    referencia que armar_tabla, con las mismas capas."""
    cons, ocr, capas = ref
    coords = bp._coords_por_volcan()
    kw = {"historico_path": capas["historico"], "respaldo_path": capas["respaldo"]} if capas else {}
    filas = ev.cargar_referencia_unificada(Path(cons), Path(ocr), **kw)
    por_vb, _, _, _ = bp.indexar_referencia(filas, coords, (desde, hasta))
    out = {}
    for k in claves_:
        vol, b, t = k.split("|")
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        ff = bp.parear(por_vb.get((vol, b), []), dt)
        pa = [f for f in ff if cm.alerta_protegida(f, lectura="A")]
        al = [f for f in ff if bp.es_alerta(f["tipo"])]
        out[k] = {"A": bool(pa), "B": any(cm.alerta_protegida(f, lectura="B") for f in ff),
                  "alerta_solo_ocr": bool(al) and all(f["source"] == "OCR" for f in al)}
    return out


def referencia_congelada(dref, capas, capas_del_repo):
    """La referencia ENTERA tiene que ser la congelada: los dos CSV principales y las dos capas, cada uno con su
    sha256 LF igual al del manifiesto. Sin capas congeladas el cargador leeria las del repo, que audit-weekly.yml
    reescribe cada semana: eso pone referencia_ok en False, salvo con --capas-del-repo (solo para la prueba sobre
    el congelado de #796, que es anterior a esta regla)."""
    man = dref / "MANIFIESTO.json"
    if not man.exists():
        print("   referencia SIN MANIFIESTO: no es una referencia congelada")
        return False
    m = json.loads(man.read_text(encoding="utf-8"))
    malos = [f for f, d in m["archivos"].items() if sha_lf(dref / f) != d["sha256"]]
    if capas is None or "capas" not in m:
        print("   referencia congelada %s: principales %s | capas NO congeladas (el cargador usa las del repo)%s" % (
            m["fuente"], "OK" if not malos else "CAMBIO %s" % malos, ", aceptado por --capas-del-repo" if capas_del_repo else ""))
        return not malos and bool(capas_del_repo)
    malos += [f for f, d in m["capas"].items() if sha_lf(dref / f) != d["sha256"]]
    print("   referencia congelada %s: principales y capas (%s) %s" % (
        m["fuente"], ", ".join("%s %d filas" % (f, d["filas"]) for f, d in m["capas"].items()), "OK" if not malos else "CAMBIO %s" % malos))
    return not malos


# ---------------------------------------------------------------- contabilidad
def decide_sensor(k, cfg):
    """En V2, VIIRS decide desde abril (A119 b); MODIS toda la ventana."""
    b, t = k.split("|")[1], k.split("|")[2]
    return b == "MODIS" or t[:10] >= INICIO_VIIRS_POR_PASADA or cfg["desde"] >= INICIO_VIIRS_POR_PASADA


def ocr_snpp(k, v, prot):
    """Pasada cuya alerta descansa solo en el OCR de una pasada de Suomi NPP (V1: no decide, se informa)."""
    return prot[k]["alerta_solo_ocr"] and "SNPP" in (v.get("plataforma") or "")


def suma_errores(T, lado, prot, lectura, cfg, sensor, excluir_snpp):
    """Por pasada. Devuelve (alertas Muy Bajo perdidas, publicaciones en negativos limpios, otras publicadas,
    n Muy Bajo, n negativos)."""
    perd = negp = otras = n_mb = n_neg = 0
    for k, v in T.items():
        if lado not in v or k.split("|")[1] != sensor or not decide_sensor(k, cfg):
            continue
        x = v[lado]
        if excluir_snpp and ocr_snpp(k, x, prot):
            continue
        if x["lab"] == "pos" and not prot[k][lectura]:
            n_mb += 1; perd += 1 - x["pub"]
        elif x["lab"] == "neg_limpio":
            n_neg += 1; negp += x["pub"]
        elif x["lab"] in ("sin_info", "far_ref") and not prot[k][lectura]:
            otras += x["pub"]
    return perd, negp, otras, n_mb, n_neg


def errores_por_pasada(T, lado, prot, lectura, cfg, sensor, excluir_snpp):
    """Las pasadas que cuentan como error en la suma de P2 (misma definicion que suma_errores)."""
    out = set()
    for k, v in T.items():
        if lado not in v or k.split("|")[1] != sensor or not decide_sensor(k, cfg):
            continue
        x = v[lado]
        if excluir_snpp and ocr_snpp(k, x, prot):
            continue
        if (x["lab"] == "pos" and not prot[k][lectura] and not x["pub"]) or (x["lab"] == "neg_limpio" and x["pub"]):
            out.add(k)
    return out


def bootstrap_mediana(d, semilla=SEMILLA, n=N_BOOT):
    rnd = random.Random(semilla); ms = []
    for _ in range(n):
        ms.append(statistics.median(rnd.choice(d) for _ in d))
    ms.sort()
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def diferencias_magnitud(T, sensor, cfg):
    """d = |log10(brazo/MIROVA)| - |log10(C0/MIROVA)| en las alertas que publican los dos (S147, pareado)."""
    out = []
    for k, v in T.items():
        if len(v) != 2 or k.split("|")[1] != sensor or not decide_sensor(k, cfg):
            continue
        c, b = v["control"], v["brazo"]
        if c["lab"] == "pos" and c["pub"] and b["pub"] and c["vrp_ref"] and (c["disp"] or 0) > 0 and (b["disp"] or 0) > 0:
            out.append((k, abs(math.log10(b["disp"] / c["vrp_ref"])) - abs(math.log10(c["disp"] / c["vrp_ref"])),
                        math.log10(b["disp"] / c["disp"]), c["disp"] / c["vrp_ref"], b["disp"] / c["vrp_ref"]))
    return out


def movidas(T, lab, sensor=None, detalle=False):
    """Pasadas que los dos publican y en que el cumulo publicado se corre mas de MOV_KM. Con `detalle`, ademas
    cuantas de las movidas quedan MAS CERCA del crater en el brazo (solo radio: no dice hacia donde, A93)."""
    n = m = cerca = 0
    for k, v in T.items():
        if len(v) != 2 or (sensor and k.split("|")[1] != sensor):
            continue
        c, b = v["control"], v["brazo"]
        if c["lab"] != lab or not (c["pub"] and b["pub"]) or None in (c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"]):
            continue
        n += 1
        if ev._hav(c["pc_lat"], c["pc_lon"], b["pc_lat"], b["pc_lon"]) > MOV_KM:
            m += 1; cerca += (b["pc_dist"] or 0) < (c["pc_dist"] or 0)
    return (m, n, cerca) if detalle else (m, n)


# ---------------------------------------------------------------- evaluacion de una ventana
def evaluar(a):
    cfg = dict(VENTANAS[a.ventana])
    if a.desde: cfg["desde"] = a.desde
    if a.hasta: cfg["hasta"] = a.hasta
    if a.ref: cfg["ref"] = Path(a.ref)
    if a.solo_tabla is not None: cfg["solo_tabla"] = a.solo_tabla == "si"
    if a.brazos: cfg["brazos"] = tuple(a.brazos.split(","))
    vols = a.vols.split(",") if a.vols else list(bp.VOLS)
    tmp = Path(a.tmp) if a.tmp else Path(a.out).resolve().parent / ("_tmp_" + a.ventana); tmp.mkdir(parents=True, exist_ok=True)
    brazos = cfg["brazos"]
    raiz = fusionar(a.raiz, tmp, brazos, vols)
    faltan = [(n, v) for n in brazos for v in vols if not (raiz / BRAZOS[n] / (v + ".json")).exists()]
    if faltan:
        raise SystemExit("faltan brazos o volcanes: %s. No se evalua a medias." % faltan[:20])
    res = {"ventana": a.ventana, "desde": cfg["desde"], "hasta": cfg["hasta"], "solo_tabla": cfg["solo_tabla"],
           "brazos": list(brazos), "veredicto": {}}
    sha_html = hashlib.sha256((RAIZ / "frontend" / "index.html").read_bytes()).hexdigest()
    res["sha256_index_html"] = sha_html
    print("== VENTANA %s: %s a %s | volcanes %d | brazos %s | %s" % (a.ventana, cfg["desde"], cfg["hasta"], len(vols), brazos,
          "decide la tabla sola (OCR reetiquetado fuera)" if cfg["solo_tabla"] else "decide tabla y OCR"))
    print("   predicado del tablero: frontend/index.html sha256", sha_html)
    ref = archivos_ref(cfg, tmp)
    res["referencia_ok"] = referencia_congelada(cfg["ref"], ref[2], a.capas_del_repo)

    pares = [("C0", n) for n in brazos if n != "C0"] + ([("F", "K")] if {"F", "K"} <= set(brazos) else [])
    T = {p: tabla(raiz / BRAZOS[p[0]], raiz / BRAZOS[p[1]], ref, cfg["desde"], cfg["hasta"], tmp / ("t_%s_%s.json" % p)) for p in pares}
    R = {n: crudos(raiz, n, vols, cfg["desde"], cfg["hasta"]) for n in brazos}
    todas = set().union(*[set(t) for t in T.values()])
    prot = proteccion(todas, ref, cfg["desde"], cfg["hasta"])
    base = T[pares[0]]   # cualquiera de los pares con C0: el lado control es C0

    # ---------------- sustrato que el evaluador ve
    print("\n== 0. SUSTRATO (pasadas nocturnas de C0, etiqueta del evaluador; en V2, VIIRS desde abril)")
    for s in SENS:
        sel = [(k, v["control"]) for k, v in base.items() if "control" in v and k.split("|")[1] == s and decide_sensor(k, cfg)]
        print("   %-8s pasadas %5d | alertas %4d | protegidas A %3d (C0 publica %3d; solo OCR Suomi NPP %d) | protegidas B %3d | negativos limpios %5d" % (
            s, len(sel), sum(c["lab"] == "pos" for k, c in sel), sum(prot[k]["A"] for k, c in sel),
            sum(prot[k]["A"] and c["pub"] for k, c in sel), sum(prot[k]["A"] and ocr_snpp(k, c, prot) for k, c in sel),
            sum(prot[k]["B"] for k, c in sel), sum(c["lab"] == "neg_limpio" for k, c in sel)))

    # ---------------- 1. cobertura
    print("\n== 1. COBERTURA (A108)")
    claves_ = {n: set(R[n]) for n in brazos}; mal = False
    for n in brazos:
        d1, d2 = claves_["C0"] - claves_[n], claves_[n] - claves_["C0"]
        if d1 or d2:
            mal = True; print("   %-3s le faltan %d pasadas de C0 y tiene %d que C0 no %s" % (n, len(d1), len(d2), sorted(d1 | d2)[:5]))
    protegidas = sorted(k for k in todas if prot[k]["A"] or prot[k]["B"])
    sin_rec = {k: [n for n in brazos if k not in claves_[n]] for k in protegidas}
    sin_rec = {k: v for k, v in sin_rec.items() if v}
    print("   protegidas (A o B) sin record en algun brazo:", sin_rec or "ninguna")
    # Verificador del PR #797, 6b: la paridad entre brazos no ve un job verde sin datos que le pase a TODOS los
    # brazos por igual (A108, S141). Se compara C0 con lo que produccion tiene de esa ventana: si en algun volcan y
    # sensor C0 no trae mas del 5 % de las pasadas que produccion si trae, el reproceso quedo corto. El 5 % es un
    # umbral del INSTRUMENTO, elegido, no medido contra MIROVA.
    prod = claves_produccion(Path(a.produccion), vols, cfg["desde"], cfg["hasta"])
    cortos = []
    for (v, s), ks in sorted(prod.items()):
        falta = {k for k in ks if k not in claves_["C0"]}
        if len(falta) > MAX_FALTA_CONTRA_PRODUCCION * len(ks):
            cortos.append("%s %s: faltan %d de %d" % (v, s, len(falta), len(ks)))
    print("   C0 contra produccion (%s): %s" % (Path(a.produccion).name, "; ".join(cortos) if cortos else
          "en ningun volcan y sensor falta mas del %d %% de las pasadas de produccion" % (100 * MAX_FALTA_CONTRA_PRODUCCION)))
    res["cobertura_ok"] = not (mal or sin_rec or cortos)
    print("   " + ("cobertura pareja: OK" if res["cobertura_ok"] else "COBERTURA DESPAREJA O CORTA: INDECIDIBLE. Repetir los jobs cortos con el mismo codigo."))

    # ---------------- 2. version de producto
    print("\n== 2. VERSION DEL PRODUCTO POR PASADA")
    mezcla = sorted(k for k in claves_["C0"] if len({R[n][k]["pv"] for n in brazos if k in R[n]}) > 1)
    mezcla_p = [k for k in mezcla if k in protegidas]
    print("   pasadas con version distinta entre brazos: %d (protegidas: %d) %s" % (len(mezcla), len(mezcla_p), mezcla_p[:10]))
    res["version_ok"] = not mezcla_p

    # ---------------- 3. cableado
    print("\n== 3. CABLEADO DE CADA BRAZO (linea FLAGS_BRAZO de cada job y huella en los records)")
    cable = {}
    for n in brazos:
        prob = []
        if not a.logs:
            prob.append("sin --logs: no hay con que probar el cableado")
        for v in vols:
            for d, fl in flags_leidos(a.logs, n, v):
                donde = "%s (%s)" % (v, d.rstrip("/").split("/")[-2] if d.count("/") else d)
                if fl is None:
                    prob.append("%s: sin linea FLAGS_BRAZO" % donde); continue
                if fl.get("PROFILE_NAME") != BRAZOS[n] or fl.get("DATA_SUBDIR") != BRAZOS[n]:
                    prob.append("%s: perfil o directorio %s" % (donde, fl.get("PROFILE_NAME")))
                leido = tuple(fl.get(c) for c in CLAVES)
                if leido != DECLARADO[n]:
                    prob.append("%s: flags leidos %s contra declarados %s" % (donde, leido, DECLARADO[n]))
                for c, val in EXTRA.items():
                    if c in fl and fl[c] != val:
                        prob.append("%s: %s=%s, produccion %s" % (donde, c, fl[c], val))
        if not DECLARADO[n][0] and any(x["t1"] for x in R[n].values()):
            prob.append("declara sin Test 1 y hay records con triggered_test1")
        cable[n] = prob
        print("   %-3s %s" % (n, "OK" if not prob else "ROTO: " + "; ".join(prob[:4]) + (" (y %d mas)" % (len(prob) - 4) if len(prob) > 4 else "")))
    res["cableado"] = {n: not p for n, p in cable.items()}

    # ---------------- 4. determinismo
    print("\n== 4. DETERMINISMO (misma decision de publicar, por sensor)")
    det_ok = True; ruido_c0, ruido_cand = set(), set()
    for par, sensores, destino in ((("C0", "G"), SENS, ruido_c0), (("F", "K"), ("VIIRS375", "VIIRS750"), ruido_cand)):
        if par not in T:
            print("   %s contra %s: no esta en esta ventana (las perdidas se confirman repitiendo el job, §5)" % par); continue
        for s in sensores:
            amb = [(k, v) for k, v in T[par].items() if k.split("|")[1] == s and len(v) == 2]
            dif = {k for k, v in amb if v["control"]["pub"] != v["brazo"]["pub"]}
            destino |= dif
            ok = bool(amb) and (len(amb) - len(dif)) / len(amb) >= UMBRAL_DETERMINISMO; det_ok &= ok
            print("   %s contra %s %-8s %5d pasadas, misma decision %5d (%.2f %%) | %s" % (par[1], par[0], s, len(amb), len(amb) - len(dif),
                  100 * (len(amb) - len(dif)) / len(amb) if amb else 0, "OK" if ok else "FALLA"))
    res["determinismo_ok"] = det_ok
    controles = res["cobertura_ok"] and res["version_ok"] and det_ok and res["referencia_ok"]
    res["controles_ok"] = controles
    print("\n== CONTROLES GENERALES:", "OK" if controles else "FALLAN: ningun veredicto decide")

    # repeticion (V2, sin gemelo): tablas de los jobs repetidos
    T_rep = {}
    if a.repeticion:
        rr = Path(a.repeticion)
        for p in pares:
            if p[0] == "C0" and all((rr / BRAZOS[x]).exists() for x in p):
                T_rep[p] = tabla(rr / BRAZOS[p[0]], rr / BRAZOS[p[1]], ref, cfg["desde"], cfg["hasta"], tmp / ("rep_%s_%s.json" % p))

    # ---------------- 5. P1 veto
    print("\n== 5. P1, VETO: alertas protegidas que C0 publica y el candidato no (por pasada)")
    for X in ("F", "K"):
        if X not in brazos:
            continue
        par = ("C0", X)
        for lectura in ("A", "B"):
            for s in SENS_CANDIDATO[X] + SENS_INFORMA.get(X, ()):
                pref = "P1" if s in SENS_CANDIDATO[X] else "P1inf"
                netas, ruidosas, pendientes, descartadas, snpp, recup, n_pub = [], [], [], [], [], [], 0
                for k, v in T[par].items():
                    if len(v) != 2 or k.split("|")[1] != s or not prot[k][lectura] or not decide_sensor(k, cfg):
                        continue
                    c, b = v["control"], v["brazo"]
                    if b["pub"] and not c["pub"]:
                        recup.append(k)
                    if not c["pub"]:
                        continue
                    n_pub += 1
                    if b["pub"]:
                        continue
                    linea = "%s | MIROVA %s MW | %s | lab %s" % (k, c["vrp_ref"], c["plataforma"], c["lab"])
                    # §5. Con la repeticion de los jobs de ese volcan (--repeticion), la pasada se decide ahi: si se
                    # vuelve a perder es neta, si no, es ruido confirmado y no cuenta. Sin repeticion: ruidosa si el
                    # gemelo de C0 (o, en VIIRS, F contra K) tambien cambia; PENDIENTE DE REPETICION si la ventana
                    # no tiene gemelo (V2); neta en otro caso.
                    rep = T_rep.get(par, {}).get(k)
                    if lectura == "A" and not cfg["solo_tabla"] and ocr_snpp(k, c, prot):
                        snpp.append(linea)
                    elif rep is not None and len(rep) == 2:
                        if rep["control"]["pub"] and not rep["brazo"]["pub"]:
                            netas.append(linea + " | se repite en la repeticion")
                        else:
                            descartadas.append(linea + " | no se repite en la repeticion: ruido confirmado")
                    elif k in ruido_c0 or (s != "MODIS" and k in ruido_cand):
                        ruidosas.append(linea)
                    elif "G" not in brazos:
                        pendientes.append(linea)
                    else:
                        netas.append(linea)
                if not (controles and res["cableado"]["C0"] and res["cableado"][X]):
                    ver = "INDECIDIBLE"
                elif netas:
                    ver = "VETADO"
                elif ruidosas:
                    ver = "INDECIDIBLE"
                elif pendientes:
                    ver = "PENDIENTE DE REPETICION"
                elif n_pub == 0:
                    ver = "SIN SUSTRATO"
                else:
                    ver = "CUMPLE"
                res["veredicto"]["%s|%s|%s|%s" % (pref, X, s, lectura)] = ver
                if pref == "P1inf":
                    ver += " (informativo: F no se adopta sin K)"
                print("   %s lectura %s %-8s protegidas que C0 publica %3d | perdidas netas %d, ruidosas %d, pendientes %d, descartadas por repeticion %d, solo OCR Suomi NPP %d | recuperadas %d | %s" % (
                    X, lectura, s, n_pub, len(netas), len(ruidosas), len(pendientes), len(descartadas), len(snpp), len(recup), ver))
                for l in netas: print("      perdida: " + l)
                for l in ruidosas: print("      perdida ruidosa (se resuelve repitiendo los jobs de C0 y %s de ese volcan, §5): %s" % (X, l))
                for l in pendientes: print("      perdida PENDIENTE DE REPETICION (ventana sin gemelo, §5): " + l)
                for l in descartadas: print("      " + l)
                for l in snpp: print("      solo OCR Suomi NPP (no decide; mirar la cabecera de la imagen, docs/S150_IMAGENES_SNPP.md): " + l)
                for k in recup: print("      recuperada (C0 no la publica): %s | MIROVA %s MW" % (k, T[par][k]["control"]["vrp_ref"]))

    # ---------------- 6. P2 suma de errores bajo 1 MW
    print("\n== 6. P2, SUMA DE ERRORES BAJO 1 MW, por pasada (alertas Muy Bajo perdidas + publicaciones en negativos limpios)")
    excluir = not cfg["solo_tabla"]
    res["suma"] = {}; res["ruido_frac"] = {}
    for lectura in ("A", "B"):
        for s in SENS:
            filas_s = {}
            for n in brazos:
                par = ("C0", n) if n != "C0" else pares[0]; lado = "brazo" if n != "C0" else "control"
                filas_s[n] = suma_errores(T[par], lado, prot, lectura, cfg, s, excluir)
                tot = suma_errores(T[par], lado, prot, lectura, cfg, s, False)
                res["suma"]["%s|%s|%s" % (n, s, lectura)] = {"decide": sum(filas_s[n][:2]), "total": sum(tot[:2]),
                                                             "perdidas_mb": filas_s[n][0], "neg_pub": filas_s[n][1], "otras_pub": filas_s[n][2]}
                print("   lectura %s %-8s %-3s Muy Bajo perdidas %4d de %4d | negativos publicados %4d de %5d | suma %5d (con Suomi NPP solo OCR: %5d) | otras publicadas %4d" % (
                    lectura, s, n, filas_s[n][0], filas_s[n][3], filas_s[n][1], filas_s[n][4], sum(filas_s[n][:2]), sum(tot[:2]), filas_s[n][2]))
            s0 = sum(filas_s["C0"][:2])
            if "G" in brazos:
                # Verificador del PR #797, 6d: el ruido no es solo la diferencia NETA de las sumas (dos pasadas que
                # cambian en sentidos opuestos se cancelan), sino las pasadas DISCORDANTES: donde C0 y su gemelo no
                # coinciden en si hay error. Es una cota superior de la neta y es la que se usa.
                Tg = T[("C0", "G")]
                e0 = errores_por_pasada(Tg, "control", prot, lectura, cfg, s, excluir)
                eg = errores_por_pasada(Tg, "brazo", prot, lectura, cfg, s, excluir)
                ruido = len(e0 ^ eg); fuente = "gemelo: %d pasadas discordantes, diferencia neta %d" % (ruido, abs(sum(filas_s["G"][:2]) - s0))
                res["ruido_frac"]["%s|%s" % (s, lectura)] = ruido / s0 if s0 else 0.0
            elif a.ruido_de:
                fr = json.load(open(a.ruido_de, encoding="utf-8"))["ruido_frac"].get("%s|%s" % (s, lectura), 0.0)
                ruido = fr * s0; fuente = "fraccion del gemelo de %s" % Path(a.ruido_de).name
            else:
                ruido = 0.0; fuente = "sin gemelo ni --ruido-de: ruido 0"
            for X in ("F", "K"):
                if X not in brazos or s not in SENS_CANDIDATO[X]:
                    continue
                sx = sum(filas_s[X][:2])
                if not (controles and res["cableado"]["C0"] and res["cableado"][X]):
                    ver = "INDECIDIBLE"
                elif sx < s0 - ruido:
                    ver = "GANA"
                elif sx > s0 + ruido:
                    ver = "PIERDE"
                else:
                    ver = "EMPATE"
                res["veredicto"]["P2|%s|%s|%s" % (X, s, lectura)] = ver
                print("      P2 %s lectura %s %-8s: %d contra C0 %d, ruido %.1f (%s) -> %s" % (X, lectura, s, sx, s0, ruido, fuente, ver))

    # ---------------- 7. P3 magnitud
    print("\n== 7. P3, RAZON DE MAGNITUD contra MIROVA, pareada (d = |log10(brazo/MIROVA)| - |log10(C0/MIROVA)|)")
    for X in ("F", "K"):
        if X not in brazos:
            continue
        for s in SENS_CANDIDATO[X]:
            D = diferencias_magnitud(T[("C0", X)], s, cfg)
            dG = [x[1] for x in diferencias_magnitud(T[("C0", "G")], s, cfg)] if "G" in brazos else []
            ruido = abs(statistics.median(dG)) if dG else 0.0
            if len(D) < N_MIN_MAGNITUD:
                ver = "SIN SUSTRATO"; print("   %s %-8s n %d: SIN SUSTRATO" % (X, s, len(D)))
            else:
                d = [x[1] for x in D]; md = statistics.median(d); lo, hi = bootstrap_mediana(d)
                if not (controles and res["cableado"]["C0"] and res["cableado"][X]):
                    ver = "INDECIDIBLE"
                else:
                    ver = "FALLA" if (lo > 0 and md > ruido) else "CUMPLE"
                print("   %s %-8s n %3d | razon mediana C0 %.3f, %s %.3f | d mediana %+.3f [%+.3f, %+.3f] | ruido del gemelo %.3f -> %s" % (
                    X, s, len(D), statistics.median(x[3] for x in D), X, statistics.median(x[4] for x in D), md, lo, hi, ruido, ver))
            res["veredicto"]["P3|%s|%s" % (X, s)] = ver
        # P3b, informativa: direccion en VIIRS 375 en los volcanes donde S147 vio que el Test 1 recompone la magnitud
        for vol in ("Lascar", "Isluga", "Tupungatito"):
            D = [x for x in diferencias_magnitud(T[("C0", X)], "VIIRS375", cfg) if x[0].startswith(vol + "|")]
            if len(D) >= N_MIN_MAGNITUD:
                m = statistics.median(x[2] for x in D)
                print("   P3b %s VIIRS375 %-12s n %3d | mediana log10(brazo/C0) %+.3f -> %s" % (X, vol, len(D), m, "baja, como predijo S147" if m < 0 else "NO baja"))

    # ---------------- 8. P4 movimiento del cumulo
    tope = wilson_sup(*S147_MOVIDAS_EN_ALERTA)
    print("\n== 8. P4, MOVIMIENTO DEL CUMULO PUBLICADO mas de %.1f km (tope: Wilson superior de S147, %d de %d = %.3f)" % (
        MOV_KM, S147_MOVIDAS_EN_ALERTA[0], S147_MOVIDAS_EN_ALERTA[1], tope))
    for X in [n for n in ("G", "F", "K") if n in brazos]:
        par = ("C0", X)
        mp, npos, cerca = movidas(T[par], "pos", detalle=True); mn, nneg = movidas(T[par], "neg_limpio")
        fp_ = mp / npos if npos else 0.0
        if X != "G":
            if not npos:
                ver = "SIN SUSTRATO"
            elif not (controles and res["cableado"]["C0"] and res["cableado"][X]):
                ver = "INDECIDIBLE"
            else:
                ver = "CUMPLE" if fp_ <= tope else "FALLA"
            res["veredicto"]["P4|%s" % X] = ver
        else:
            ver = "(ruido)"
        print("   %s contra C0: en alertas %d de %d (%.3f; de las movidas, %d quedan mas cerca del crater) | en negativos limpios %d de %d | %s" % (
            X, mp, npos, fp_, cerca, mn, nneg, ver))
        for s in SENS:
            m_, n_ = movidas(T[par], "pos", s)
            print("      %-8s en alertas %d de %d" % (s, m_, n_))

    # ---------------- 9. tres metricas por sensor (informativo)
    print("\n== 9. LAS TRES METRICAS POR SENSOR (informativo): recall de alertas, publicacion en negativos limpios")
    for s in SENS:
        for n in brazos:
            par = ("C0", n) if n != "C0" else pares[0]; lado = "brazo" if n != "C0" else "control"
            sel = [(k, v[lado]) for k, v in T[par].items() if lado in v and k.split("|")[1] == s and decide_sensor(k, cfg)]
            pos = [x for k, x in sel if x["lab"] == "pos"]; pa = [x for k, x in sel if x["lab"] == "pos" and prot[k]["A"]]
            neg = [x for k, x in sel if x["lab"] == "neg_limpio"]
            print("   %-8s %-3s recall %4d de %4d | protegidas A %3d de %3d | negativos limpios publicados %4d de %5d (%.1f %%)" % (
                s, n, sum(x["pub"] for x in pos), len(pos), sum(x["pub"] for x in pa), len(pa), sum(x["pub"] for x in neg), len(neg),
                100 * sum(x["pub"] for x in neg) / len(neg) if neg else 0))
    # P6 (informativa): C0 en negativos limpios de VIIRS 375 tiene que caer en la banda de A114 con el Test 1
    # encendido; fuera de ella el reproceso no se parece a produccion y hay que saber por que antes de leer lo demas.
    neg0 = [v["control"] for k, v in base.items() if "control" in v and k.split("|")[1] == "VIIRS375"
            and decide_sensor(k, cfg) and v["control"]["lab"] == "neg_limpio"]
    tasa = sum(x["pub"] for x in neg0) / len(neg0) if neg0 else None
    res["P6"] = {"tasa": tasa, "n": len(neg0),
                 "dentro": None if tasa is None else BANDA_P6[0] <= tasa <= BANDA_P6[1]}
    print("\n   P6 (informa): C0 publica en negativos limpios de VIIRS 375 %s | banda de A114 %.0f a %.0f %% -> %s" % (
        "%d de %d (%.1f %%)" % (sum(x["pub"] for x in neg0), len(neg0), 100 * tasa) if neg0 else "SIN SUSTRATO",
        100 * BANDA_P6[0], 100 * BANDA_P6[1], "SIN SUSTRATO" if tasa is None else ("DENTRO" if res["P6"]["dentro"] else "FUERA: investigar antes de leer el resto")))
    print("\n   MODIS fuera de Lascar (S150 midio K solo en Lascar), negativos limpios publicados:")
    partes = []
    for n in brazos:
        par = ("C0", n) if n != "C0" else pares[0]; lado = "brazo" if n != "C0" else "control"
        neg = [x[lado] for k, x in T[par].items() if lado in x and "|MODIS|" in k and not k.startswith("Lascar|") and x[lado]["lab"] == "neg_limpio"]
        partes.append("%s %d de %d" % (n, sum(x["pub"] for x in neg), len(neg)))
    print("      todos " + " | ".join(partes))
    for v in vols:
        if v == "Lascar":
            continue
        partes = []
        for n in brazos:
            par = ("C0", n) if n != "C0" else pares[0]; lado = "brazo" if n != "C0" else "control"
            neg = [x[lado] for k, x in T[par].items() if lado in x and k.startswith(v + "|MODIS|") and x[lado]["lab"] == "neg_limpio"]
            partes.append("%s %d/%d" % (n, sum(x["pub"] for x in neg), len(neg)))
        print("      %-20s %s" % (v, " | ".join(partes)))

    # ---------------- veredicto de la ventana por candidato
    res["global"] = {X: {l: global_ventana(res, X, l) for l in ("A", "B")} for X in ("F", "K") if X in brazos}
    if "F" not in brazos and "K" in brazos:
        # Verificador del PR #797, punto 3: en V2 no corre F, pero en VIIRS F y K son el mismo codigo (la banda 22
        # solo la lee process_modis.py), asi que el VIIRS de F se deriva de K. Sin esto, el "peor de las dos
        # ventanas" de F seria solo V1, con el poder de V1 (12,6 %).
        res["global"]["F"] = {l: global_ventana(res, "F", l, fuente="K") + " [derivado de K: mismo codigo en VIIRS]" for l in ("A", "B")}
    print("\n== VEREDICTO DE LA VENTANA %s (reglas de §6):" % a.ventana)
    for X, d in res["global"].items():
        for l, v in d.items():
            print("   %s lectura %s: %s" % (X, l, v))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def global_ventana(res, X, lectura, fuente=None):
    """§6 del pre-registro. Orden: controles, veto, suma, magnitud; el movimiento agrega una condicion.
    `fuente`: brazo del que se leen los veredictos (F en V2 se lee de K, en los sensores de F)."""
    v = res["veredicto"]; Y = fuente or X
    if not (res["controles_ok"] and res["cableado"].get("C0") and res["cableado"].get(Y)):
        return "INDECIDIBLE"
    sens = SENS_CANDIDATO[X]
    p1 = [v.get("P1|%s|%s|%s" % (Y, s, lectura)) for s in sens]
    p2 = [v.get("P2|%s|%s|%s" % (Y, s, lectura)) for s in sens]
    p3 = [v.get("P3|%s|%s" % (Y, s)) for s in sens]
    X = Y
    if "VETADO" in p1:
        return "NO CUMPLE (veto)"
    if "INDECIDIBLE" in p1 + p2 + p3:
        return "INDECIDIBLE"
    if "PENDIENTE DE REPETICION" in p1:
        return "PENDIENTE DE REPETICION"
    if "PIERDE" in p2:
        return "NO CUMPLE (suma de errores)"
    if "GANA" not in p2:
        return "NO CUMPLE (no gana en ningun sensor)"
    out = "CUMPLE"
    if "FALLA" in p3:
        out = "CUMPLE EN DETECCION, FALLA EN MAGNITUD (decide Nicolas)"
    if "SIN SUSTRATO" in p1:
        out += " | veto sin sustrato en %s" % [s for s, x in zip(sens, p1) if x == "SIN SUSTRATO"]
    if v.get("P4|%s" % X) == "FALLA":
        out += " | con auditoria espacial pendiente (P4)"
    return out


def combinar(archivos):
    """§6: el candidato cumple solo si cumple en las dos ventanas; el peor estado manda. Un NO CUMPLE en una
    ventana es definitivo aunque la otra este INDECIDIBLE o PENDIENTE."""
    rs = [json.load(open(f, encoding="utf-8")) for f in archivos]
    orden = ("NO CUMPLE", "INDECIDIBLE", "PENDIENTE DE REPETICION", "CUMPLE EN DETECCION", "CUMPLE")
    print("== VEREDICTO COMBINADO (%s)" % ", ".join(r["ventana"] for r in rs))
    for X in ("F", "K"):
        for l in ("A", "B"):
            estados = [(r["ventana"], r["global"][X][l]) for r in rs if X in r.get("global", {})]
            if not estados:
                continue
            peor = min(estados, key=lambda e: next(i for i, o in enumerate(orden) if e[1].startswith(o)))
            print("   %s lectura %s: %s | por ventana %s" % (X, l, peor[1], estados))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combinar", nargs="+")
    ap.add_argument("--ventana", choices=sorted(VENTANAS))
    ap.add_argument("--raiz", action="append", default=[])
    ap.add_argument("--logs", action="append", default=[])
    ap.add_argument("--out")
    ap.add_argument("--tmp")
    ap.add_argument("--ruido-de", dest="ruido_de")
    ap.add_argument("--repeticion")
    # solo para la prueba del evaluador (probar_evaluar_fk.py): no cambian ninguna regla
    ap.add_argument("--vols"); ap.add_argument("--desde"); ap.add_argument("--hasta"); ap.add_argument("--ref")
    ap.add_argument("--solo-tabla", dest="solo_tabla", choices=("si", "no")); ap.add_argument("--brazos")
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
