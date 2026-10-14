# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Prueba de evaluar_fk.py ANTES de despachar: cada veredicto que el evaluador puede dar
tiene que poder salir, con un caso que lo produce y otro que no (A110, A116). Los brazos se fabrican desde los
records de produccion de cada ventana (11 volcanes, recortados) y la referencia congelada de esa ventana, con la
linea FLAGS_BRAZO en el log igual que la escribe el workflow. Ademas, un caso sobre el run REAL de Nevados de
Chillan (38560317428), que tiene que reproducir la suma de errores que publico su verificador.

Casos V1 (nombre: lo sembrado -> lo esperado):
  nulo      cuatro brazos identicos                                  -> controles OK, P1 CUMPLE, P2 EMPATE, P3 y P4 CUMPLE,
                                                                        y el candidato NO CUMPLE (no gana en ningun sensor)
  veto      F y K ocultan una protegida VIIRS 375 que C0 publica      -> P1 VETADO (A y B), global NO CUMPLE (veto)
  gemelo    lo mismo, y el gemelo de C0 tambien la oculta             -> P1 INDECIDIBLE (ruido de C0)
  gem_rep   "gemelo" con la repeticion de C0 y K, que la vuelve a perder -> P1 VETADO (camino de resolucion de §5)
  fk        solo K la oculta (F no)                                   -> P1 de K INDECIDIBLE (ruido del candidato), F CUMPLE
  snpp      F y K ocultan una protegida solo del OCR de Suomi NPP     -> P1 lectura A CUMPLE (se informa), lectura B VETADO
  lecturab  F y K ocultan una pasada protegida solo con la lectura B  -> P1 A CUMPLE, P1 B VETADO
  gana      F y K no publican en los negativos limpios de VIIRS 375   -> P2 GANA y global CUMPLE
  pierde    F y K no publican las alertas Muy Bajo de VIIRS 375       -> P2 PIERDE, global NO CUMPLE (suma)
  empate    el gemelo deja 20 negativos, F y K dejan 10               -> P2 EMPATE (20 pasadas discordantes de ruido)
  magnitud  "gana", y F y K publican VIIRS 750 con 1/20 de la magnitud -> P3 FALLA, global CUMPLE EN DETECCION, FALLA EN MAGNITUD
  mueve     F y K corren 2 km el cumulo de VIIRS 375                  -> P4 FALLA
  cable     el log de K dice banda 21 en un volcan                    -> K mal cableado, todo lo de K INDECIDIBLE
  cobert    a K le falta una pasada                                   -> cobertura despareja, todo INDECIDIBLE
  vacio     a los cuatro brazos les falta VIIRS 375 de Copahue        -> la paridad entre brazos no lo ve; C0 contra produccion si
  determ    el gemelo cambia la decision en 100 pasadas VIIRS 375     -> determinismo FALLA, todo INDECIDIBLE
  capa_mod  la capa historica congelada cambio despues del manifiesto -> referencia_ok False, todo INDECIDIBLE
  sin_capas el congelado no trae las capas                            -> referencia_ok False (el cargador leeria las del repo)
  tabla     con --solo-tabla, F y K ocultan la protegida solo OCR     -> P1 A y B CUMPLE (no es positiva)
Casos con C0 y K solos (como V2, sin gemelo):
  sin_rep   K oculta una protegida y no hay repeticion                -> P1 PENDIENTE DE REPETICION
  rep_no    lo mismo, la repeticion no la pierde                      -> ruido confirmado, P1 CUMPLE
  rep_si    lo mismo, la repeticion si la pierde                      -> P1 VETADO
Casos V2 de verdad (dos despachos fusionados, dos --logs, tabla sola, VIIRS desde abril, --ruido-de):
  v2_nulo   C0 y K identicos en V2a y V2b                             -> controles OK, P1 CUMPLE, F derivado de K, ruido de V1
  v2_cable  el log de K en V2b (no en V2a) dice banda 21              -> K mal cableado (con el defecto 1 no se veia)
  v2_marzo  K oculta una protegida VIIRS 375 de marzo                 -> no decide (VIIRS desde abril): P1 CUMPLE
  v2_abril  K oculta una protegida VIIRS 375 de V2b                   -> P1 PENDIENTE DE REPETICION
Y:
  ndc       run real de Nevados de Chillan, gemelo = copia de C0       -> suma C0 52, F 7, K 7; P1 VIIRS CUMPLE; K recupera la MODIS del 1-oct
  combinar  nulo y veto juntos                                        -> K NO CUMPLE

Uso: python probar_evaluar_fk.py <TMP> <DIR_NDC>
  <DIR_NDC> tiene _s146_ab_control/, _s147_ab_sin_test1_max/, _s149_ab_sin_test1_b22_max/ (NevadosDeChillan.json) y
  logs/ del run 38560317428 (rama s146-ab/38560317428). Salida completa de cada caso en <TMP>/<caso>.txt.
"""
import copy, json, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import evaluar_fk as E  # noqa: E402  (ya deja sys.stdout en utf-8)
import sustrato as S  # noqa: E402
TMP = Path(sys.argv[1]); TMP.mkdir(parents=True, exist_ok=True)
NDC = Path(sys.argv[2])
VOLS = list(E.bp.VOLS)
PROD = RAIZ / "data" / "mirova_equivalent"
CORTE_V2 = "2026-04-20"   # V2a hasta aca, V2b desde el dia siguiente (§4)


def recortar(desde, hasta):
    out = {}
    for v in VOLS:
        d = json.load(open(PROD / (v + ".json"), encoding="utf-8"))
        out[v] = {"records": [r for r in d["records"] if desde <= r.get("datetime_utc", "")[:10] <= hasta]}
        for r in out[v]["records"]:
            r["triggered_test1"] = False   # huella de "sin Test 1"; se aplica a todos para que el nulo sea identico
    return out


def clave_rec(v, r):
    return "|".join((v, E.bp.bucket(r.get("sensor")) or "", r.get("datetime_utc", "")[:16]))


def etiquetas(base, ventana):
    """Etiqueta, publicacion y proteccion de cada pasada del brazo base, con el codigo del evaluador."""
    cfg = dict(E.VENTANAS[ventana])
    d = TMP / ("_base_" + ventana) / E.BRAZOS["C0"]; d.mkdir(parents=True, exist_ok=True)
    for v in VOLS:
        json.dump(base[v], open(d / (v + ".json"), "w", encoding="utf-8"))
    filas = S.cargar_filas(cfg["ref"], cfg["solo_tabla"])
    recs, _ = S.etiquetar_todo(d, filas, (cfg["desde"], cfg["hasta"]), set(VOLS))
    claves = {"|".join((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))): r for r in recs}
    ref = E.archivos_ref(cfg, TMP / ("_base_" + ventana))
    return claves, E.proteccion(set(claves), ref, cfg["desde"], cfg["hasta"])


V1 = E.VENTANAS["V1"]; V2 = E.VENTANAS["V2"]
BASE = recortar(V1["desde"], V1["hasta"])
L, P = etiquetas(BASE, "V1")
v375 = [k for k in L if k.split("|")[1] == "VIIRS375"]
K_PROT = next(k for k in sorted(v375) if P[k]["A"] and L[k]["pub"] and L[k]["lab"] == "pos" and not P[k]["alerta_solo_ocr"])
K_SNPP = next(k for k in sorted(v375) if P[k]["A"] and L[k]["pub"] and P[k]["alerta_solo_ocr"] and "SNPP" in (L[k]["plataforma"] or ""))
K_B = next(k for k in sorted(v375) if P[k]["B"] and not P[k]["A"] and L[k]["pub"])
NEG_PUB = sorted(k for k in v375 if L[k]["lab"] == "neg_limpio" and L[k]["pub"])
MB_PUB = sorted(k for k in v375 if L[k]["lab"] == "pos" and not P[k]["A"] and L[k]["pub"])
PUB_V375 = sorted(k for k in v375 if L[k]["pub"])
BASE2 = recortar(V2["desde"], V2["hasta"])
L2, P2 = etiquetas(BASE2, "V2")
v375_2 = sorted(k for k in L2 if k.split("|")[1] == "VIIRS375" and P2[k]["A"] and L2[k]["pub"] and L2[k]["lab"] == "pos")
K2_MARZO = next(k for k in v375_2 if k.split("|")[2] < "2026-04-01")
K2_ABRIL = next(k for k in v375_2 if k.split("|")[2][:10] > CORTE_V2)
print("semillas V1: protegida %s | solo OCR Suomi NPP %s | solo lectura B %s | negativos publicados %d | Muy Bajo publicadas %d" % (
    K_PROT, K_SNPP, K_B, len(NEG_PUB), len(MB_PUB)))
print("semillas V2: protegida de marzo %s | protegida de V2b %s" % (K2_MARZO, K2_ABRIL))


def brazos(base=None, nombres=("C0", "F", "K", "G")):
    return {n: copy.deepcopy(base or BASE) for n in nombres}


def ocultar(B, k):
    v = k.split("|")[0]; n = 0
    for r in B[v]["records"]:
        if clave_rec(v, r) == k:
            r["distance_class"] = "far"; n += 1
    assert n >= 1, k


def log(nombre, cambia=None):
    d = dict(zip(E.CLAVES, E.DECLARADO[nombre])); d.update(E.EXTRA)
    d.update(PROFILE_NAME=E.BRAZOS[nombre], DATA_SUBDIR=E.BRAZOS[nombre])
    if cambia:
        d.update(cambia)
    return "FLAGS_BRAZO " + json.dumps(d) + "\n(salida del pipeline)\n"


def escribir(dirr, B, nombres, logs_cambia=None):
    for n in nombres:
        (dirr / E.BRAZOS[n]).mkdir(parents=True, exist_ok=True)
        for v, d in B[n].items():
            json.dump(d, open(dirr / E.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
    (dirr / "logs").mkdir(parents=True, exist_ok=True)
    for n in nombres:
        for v in B[n]:
            cam = (logs_cambia or {}).get((n, v))
            (dirr / "logs" / ("%s_%s.log" % (E.BRAZOS[n], v))).write_text(log(n, cam), encoding="utf-8")


def ejecutar(caso, args):
    r = subprocess.run([sys.executable, str(AQUI / "evaluar_fk.py")] + args, capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    out = TMP / caso / "res.json"
    return (json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}), r.stdout


def correr(caso, B, nombres=("C0", "F", "K", "G"), extra=(), logs_cambia=None, rep=None):
    dirr = TMP / caso; shutil.rmtree(dirr, ignore_errors=True)
    escribir(dirr / "raiz", B, nombres, logs_cambia)
    args = ["--ventana", "V1", "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
            "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp"), "--brazos", ",".join(nombres)] + list(extra)
    if rep is not None:
        escribir(dirr / "rep", rep, ("C0", "K")); args += ["--repeticion", str(dirr / "rep")]
    return ejecutar(caso, args)[0]


def correr_v2(caso, B, logs_cambia_b=None, ruido_de=None):
    """V2 como llega de verdad: dos despachos (V2a y V2b), cada uno con sus JSON y sus logs."""
    dirr = TMP / caso; shutil.rmtree(dirr, ignore_errors=True)
    for nombre, filtro, cambia in (("V2a", lambda t: t <= CORTE_V2, None), ("V2b", lambda t: t > CORTE_V2, logs_cambia_b)):
        parte = {n: {v: {"records": [r for r in d["records"] if filtro(r.get("datetime_utc", "")[:10])]} for v, d in B[n].items()} for n in B}
        escribir(dirr / nombre, parte, ("C0", "K"), cambia)
    args = ["--ventana", "V2", "--raiz", str(dirr / "V2a"), "--raiz", str(dirr / "V2b"), "--logs", str(dirr / "V2a" / "logs"),
            "--logs", str(dirr / "V2b" / "logs"), "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp")]
    if ruido_de:
        args += ["--ruido-de", str(ruido_de)]
    return ejecutar(caso, args)


def V_(res, clave):
    return res.get("veredicto", {}).get(clave)


def con_ref(caso, mutar):
    """Copia del congelado de V1 con un cambio, para probar el control de la referencia."""
    d = TMP / ("_ref_" + caso); shutil.rmtree(d, ignore_errors=True); shutil.copytree(V1["ref"], d)
    mutar(d)
    return ("--ref", str(d))


chk = {}
r = correr("nulo", brazos())
chk["nulo: controles OK"] = r.get("controles_ok") is True and all(r.get("cableado", {}).values())
chk["nulo: P1 sin perdidas"] = all(V_(r, "P1|%s|%s|%s" % (X, s, l)) in ("CUMPLE", "SIN SUSTRATO") for X in "FK" for s in E.SENS_CANDIDATO[X] for l in "AB")
chk["nulo: P2 EMPATE en todo"] = all(V_(r, "P2|%s|%s|%s" % (X, s, l)) == "EMPATE" for X in "FK" for s in E.SENS_CANDIDATO[X] for l in "AB")
chk["nulo: P3 y P4 CUMPLE"] = all(V_(r, "P3|%s|%s" % (X, s)) in ("CUMPLE", "SIN SUSTRATO") for X in "FK" for s in E.SENS_CANDIDATO[X]) and V_(r, "P4|K") == "CUMPLE"
chk["nulo: K NO CUMPLE (no gana)"] = r.get("global", {}).get("K", {}).get("A") == "NO CUMPLE (no gana en ningun sensor)"
chk["nulo: P6 implementado y C0 dentro de la banda"] = r.get("P6", {}).get("dentro") is True
NULO = TMP / "nulo" / "res.json"

B = brazos(); ocultar(B["F"], K_PROT); ocultar(B["K"], K_PROT); r = correr("veto", B)
chk["veto: P1 K VIIRS375 A y B VETADO"] = V_(r, "P1|K|VIIRS375|A") == "VETADO" and V_(r, "P1|K|VIIRS375|B") == "VETADO"
chk["veto: global K NO CUMPLE (veto)"] = r.get("global", {}).get("K", {}).get("A") == "NO CUMPLE (veto)"
VETO = TMP / "veto" / "res.json"

B = brazos(); [ocultar(B[n], K_PROT) for n in ("F", "K", "G")]; r = correr("gemelo", B)
chk["gemelo: perdida donde el gemelo de C0 tambien cambia -> INDECIDIBLE"] = V_(r, "P1|K|VIIRS375|A") == "INDECIDIBLE" and r.get("controles_ok") is True
rep = {"C0": copy.deepcopy(BASE), "K": copy.deepcopy(BASE)}; ocultar(rep["K"], K_PROT)
r = correr("gem_rep", B, rep=rep)
chk["gem_rep: la ruidosa que se repite -> VETADO"] = V_(r, "P1|K|VIIRS375|A") == "VETADO"

B = brazos(); ocultar(B["K"], K_PROT); r = correr("fk", B)
chk["fk: K pierde y F no -> K INDECIDIBLE, F CUMPLE"] = V_(r, "P1|K|VIIRS375|A") == "INDECIDIBLE" and V_(r, "P1|F|VIIRS375|A") == "CUMPLE"

B = brazos(); ocultar(B["F"], K_SNPP); ocultar(B["K"], K_SNPP); r = correr("snpp", B)
chk["snpp: lectura A CUMPLE (informada), lectura B VETADO"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE" and V_(r, "P1|K|VIIRS375|B") == "VETADO"

B = brazos(); ocultar(B["F"], K_B); ocultar(B["K"], K_B); r = correr("lecturab", B)
chk["lecturab: A CUMPLE, B VETADO"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE" and V_(r, "P1|K|VIIRS375|B") == "VETADO"

B = brazos(); [ocultar(B[n], k) for n in ("F", "K") for k in NEG_PUB]; r = correr("gana", B)
chk["gana: P2 GANA en VIIRS 375 y global CUMPLE"] = V_(r, "P2|K|VIIRS375|A") == "GANA" and r.get("global", {}).get("K", {}).get("A", "").startswith("CUMPLE")

B = brazos(); [ocultar(B[n], k) for n in ("F", "K") for k in MB_PUB]; r = correr("pierde", B)
chk["pierde: P2 PIERDE y global NO CUMPLE (suma)"] = V_(r, "P2|K|VIIRS375|A") == "PIERDE" and r.get("global", {}).get("K", {}).get("A") == "NO CUMPLE (suma de errores)"

B = brazos(); [ocultar(B["G"], k) for k in NEG_PUB[:20]]; [ocultar(B[n], k) for n in ("F", "K") for k in NEG_PUB[:10]]; r = correr("empate", B)
chk["empate: dentro del ruido del gemelo (20 discordantes) -> EMPATE"] = V_(r, "P2|K|VIIRS375|A") == "EMPATE" and r.get("controles_ok") is True \
    and abs(r.get("ruido_frac", {}).get("VIIRS375|A", 0) * r["suma"]["C0|VIIRS375|A"]["decide"] - 20) < 1e-6

# Primera version: x4. No fallo, y con razon: en VIIRS 750 C0 subestima (mediana 0,46) y x4 deja la razon en 1,85,
# que en logaritmo esta MAS CERCA de 1. La metrica es simetrica en log, asi que el defecto sembrado tiene que
# alejar de verdad: /20. Y se combina con "gana" porque el global revisa la suma antes que la magnitud.
B = brazos(); [ocultar(B[n], k) for n in ("F", "K") for k in NEG_PUB]
for n in ("F", "K"):
    for v in VOLS:
        for rr in B[n][v]["records"]:
            if (rr.get("sensor") or "").endswith("_750"):
                for c in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw"):
                    if rr.get(c): rr[c] *= 0.05
                if rr.get("primary_cluster") and rr["primary_cluster"].get("vrp_mw"): rr["primary_cluster"]["vrp_mw"] *= 0.05
                for q in rr.get("anomaly_pixels") or []:
                    if q.get("vrp_mw"): q["vrp_mw"] *= 0.05
r = correr("magnitud", B)
chk["magnitud: P3 FALLA en VIIRS 750 y global lo dice"] = V_(r, "P3|K|VIIRS750") == "FALLA" and "FALLA EN MAGNITUD" in r.get("global", {}).get("K", {}).get("A", "")

B = brazos()
for n in ("F", "K"):
    for v in VOLS:
        for rr in B[n][v]["records"]:
            pc = rr.get("primary_cluster") or {}
            if E.bp.bucket(rr.get("sensor")) == "VIIRS375" and pc.get("centroid_lat") is not None:
                pc["centroid_lat"] += 0.02
r = correr("mueve", B)
chk["mueve: P4 FALLA"] = V_(r, "P4|K") == "FALLA" and V_(r, "P4|F") == "FALLA"

r = correr("cable", brazos(), logs_cambia={("K", "Lascar"): {"ENABLE_MODIS_B22_PRIMARY": False}})
chk["cable: K mal cableado -> P1 de K INDECIDIBLE y global INDECIDIBLE"] = r.get("cableado", {}).get("K") is False and V_(r, "P1|K|VIIRS375|A") == "INDECIDIBLE" and r.get("global", {}).get("K", {}).get("A") == "INDECIDIBLE"

B = brazos(); B["K"]["Lascar"]["records"] = [x for x in B["K"]["Lascar"]["records"] if clave_rec("Lascar", x) != clave_rec("Lascar", B["K"]["Lascar"]["records"][0])]
r = correr("cobert", B)
chk["cobert: cobertura despareja -> controles fallan, global INDECIDIBLE"] = r.get("cobertura_ok") is False and r.get("global", {}).get("F", {}).get("A") == "INDECIDIBLE"

B = brazos()
for n in B:
    B[n]["Copahue"]["records"] = [x for x in B[n]["Copahue"]["records"] if E.bp.bucket(x.get("sensor")) != "VIIRS375"]
r = correr("vacio", B)
chk["vacio: un job vacio en todos los brazos -> C0 contra produccion lo ve, INDECIDIBLE"] = r.get("cobertura_ok") is False and r.get("global", {}).get("K", {}).get("A") == "INDECIDIBLE"

B = brazos(); [ocultar(B["G"], k) for k in PUB_V375[:100]]; r = correr("determ", B)
chk["determ: gemelo distinto en 100 pasadas -> determinismo FALLA, INDECIDIBLE"] = r.get("determinismo_ok") is False and r.get("global", {}).get("K", {}).get("A") == "INDECIDIBLE"


def _ensuciar_capa(d):
    p = d / "consolidado_filas_perdidas.csv"
    p.write_text(p.read_text(encoding="utf-8") + p.read_text(encoding="utf-8").splitlines()[-1] + "\n", encoding="utf-8")


r = correr("capa_mod", brazos(), extra=con_ref("capa_mod", _ensuciar_capa))
chk["capa_mod: capa historica cambiada -> referencia_ok False, INDECIDIBLE"] = r.get("referencia_ok") is False and r.get("global", {}).get("K", {}).get("A") == "INDECIDIBLE"
r = correr("sin_capas", brazos(), extra=con_ref("sin_capas", lambda d: [(d / f).unlink() for f in ("consolidado_filas_perdidas.csv", "respaldo_20260408.csv")]))
chk["sin_capas: congelado sin capas -> referencia_ok False"] = r.get("referencia_ok") is False

B = brazos(); ocultar(B["F"], K_SNPP); ocultar(B["K"], K_SNPP); r = correr("tabla", B, extra=("--solo-tabla", "si"))
chk["tabla: con la tabla sola la protegida del OCR no es positiva -> A y B CUMPLE"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE" and V_(r, "P1|K|VIIRS375|B") == "CUMPLE"

B = brazos(nombres=("C0", "K")); ocultar(B["K"], K_PROT)
r = correr("sin_rep", B, nombres=("C0", "K"))
chk["sin_rep: sin gemelo ni repeticion -> PENDIENTE DE REPETICION"] = V_(r, "P1|K|VIIRS375|A") == "PENDIENTE DE REPETICION" and r.get("global", {}).get("K", {}).get("A") == "PENDIENTE DE REPETICION"
r = correr("rep_no", B, nombres=("C0", "K"), rep={"C0": copy.deepcopy(BASE), "K": copy.deepcopy(BASE)})
chk["rep_no: la repeticion no la pierde -> ruido confirmado, CUMPLE"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE"
rep = {"C0": copy.deepcopy(BASE), "K": copy.deepcopy(BASE)}; ocultar(rep["K"], K_PROT)
r = correr("rep_si", B, nombres=("C0", "K"), rep=rep)
chk["rep_si: la repeticion la vuelve a perder -> VETADO"] = V_(r, "P1|K|VIIRS375|A") == "VETADO"

# V2 de verdad
r, out = correr_v2("v2_nulo", brazos(BASE2, ("C0", "K")), ruido_de=NULO)
chk["v2_nulo: dos despachos fusionados, controles y cableado OK, P1 CUMPLE"] = r.get("controles_ok") is True and all(r.get("cableado", {}).values()) \
    and all(V_(r, "P1|K|%s|A" % s) in ("CUMPLE", "SIN SUSTRATO") for s in E.SENS)
chk["v2_nulo: F derivado de K y ruido leido de V1"] = "derivado de K" in r.get("global", {}).get("F", {}).get("A", "") and "fraccion del gemelo de res.json" in out \
    and "decide la tabla sola" in out
r, _ = correr_v2("v2_cable", brazos(BASE2, ("C0", "K")), logs_cambia_b={("K", "Lascar"): {"ENABLE_MODIS_B22_PRIMARY": False}}, ruido_de=NULO)
chk["v2_cable: el log de V2b con banda 21 -> K mal cableado (defecto 1)"] = r.get("cableado", {}).get("K") is False
B = brazos(BASE2, ("C0", "K")); ocultar(B["K"], K2_MARZO)
r, _ = correr_v2("v2_marzo", B, ruido_de=NULO)
chk["v2_marzo: perdida VIIRS de marzo no decide -> P1 CUMPLE"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE"
B = brazos(BASE2, ("C0", "K")); ocultar(B["K"], K2_ABRIL)
r, _ = correr_v2("v2_abril", B, ruido_de=NULO)
chk["v2_abril: perdida VIIRS de V2b sin repeticion -> PENDIENTE DE REPETICION"] = V_(r, "P1|K|VIIRS375|A") == "PENDIENTE DE REPETICION"

# Run real de Nevados de Chillan
dn = TMP / "ndc"; shutil.rmtree(dn, ignore_errors=True); (dn / "logs").mkdir(parents=True)
for n in ("C0", "F", "K"):
    shutil.copytree(NDC / E.BRAZOS[n], dn / E.BRAZOS[n])
    shutil.copy(NDC / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS[n]), dn / "logs")
shutil.copytree(NDC / E.BRAZOS["C0"], dn / E.BRAZOS["G"])
(dn / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS["G"])).write_text(
    (dn / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS["C0"])).read_text(encoding="utf-8").replace(E.BRAZOS["C0"], E.BRAZOS["G"]), encoding="utf-8")
r, out = ejecutar("ndc", ["--ventana", "V1", "--raiz", str(dn), "--logs", str(dn / "logs"), "--out", str(dn / "res.json"),
                          "--tmp", str(dn / "tmp"), "--vols", "NevadosDeChillan", "--desde", "2026-09-14", "--hasta", "2026-10-07",
                          "--ref", str(RAIZ / "experiments" / "_s150_ndc" / "_congelado_ndc"), "--capas-del-repo"])
suma = {n: sum(r.get("suma", {}).get("%s|%s|A" % (n, s), {}).get("total", -999) for s in E.SENS) for n in ("C0", "F", "K")}
print("ndc: suma total lectura A", suma)
chk["ndc: suma de errores C0 52, F 7, K 7 (verificador de #796)"] = suma == {"C0": 52, "F": 7, "K": 7}
chk["ndc: controles OK y P1 VIIRS CUMPLE en F y K"] = r.get("controles_ok") is True and all(V_(r, "P1|%s|%s|A" % (X, s)) == "CUMPLE" for X in "FK" for s in ("VIIRS375", "VIIRS750"))
chk["ndc: K recupera la MODIS del 2026-10-01 08:35"] = "recuperada (C0 no la publica): NevadosDeChillan|MODIS|2026-10-01 08:35" in out

rc = subprocess.run([sys.executable, str(AQUI / "evaluar_fk.py"), "--combinar", str(NULO), str(VETO)], capture_output=True, text=True, encoding="utf-8")
(TMP / "combinar.txt").write_text(rc.stdout + rc.stderr, encoding="utf-8")
chk["combinar: nulo y veto -> K NO CUMPLE"] = "K lectura A: NO CUMPLE" in rc.stdout

print("== RESUMEN (salida completa de cada caso en %s)" % TMP)
for k, v in chk.items():
    print("  ", "OK   " if v else "FALLA", k)
print("%d de %d" % (sum(chk.values()), len(chk)))
sys.exit(0 if all(chk.values()) else 1)
