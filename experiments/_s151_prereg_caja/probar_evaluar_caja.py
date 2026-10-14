# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. Prueba de evaluar_caja.py ANTES de despachar: cada veredicto que el evaluador puede dar tiene que
poder salir, con un caso que lo produce y otro que no (A110, A116). Los brazos se fabrican desde los records de
produccion de la ventana (11 volcanes, con `triggered_test1` en falso, igual que en la prueba de F y K) y la referencia
congelada de esa ventana, con la linea FLAGS_BRAZO en el log como la escribe el workflow con la linea de esta tarea.

"Aplicar la caja" a un brazo fabricado (`caja()`): se le quitan los pixeles alertados de la corona (dentro del circulo,
fuera de la caja, con la geometria de sustrato.py) y se apagan las pasadas EXPUESTAS (todo su calor del circulo en la
corona). Es la caja perfectamente eficaz: lo que el A/B real puede hacer como maximo.

Casos (nombre: lo sembrado -> lo esperado):
  nulo        cinco brazos identicos                        -> sin huella en BC: global INDECIDIBLE (el control positivo no paso)
  efectiva    KC y BC con la caja                           -> controles OK, Q1 y Q2 CUMPLE, mecanismo LA CAJA ACTUA; P1 y P2
                                                               los que dicta la base (calculados aparte, no copiados del evaluador)
  inerte      KC igual a K, BC con la caja                  -> NO CUMPLE (no mejora el criterio: inerte), mecanismo ACTUA
  veto        inerte, y KC oculta una protegida             -> P1 VETADO, NO CUMPLE (veto)
  gemelo      lo mismo y KG tambien la oculta               -> P1 INDECIDIBLE (ruido)
  gana        inerte, KC no publica los negativos VIIRS 375  -> P2 GANA, CUMPLE
  pierde      inerte, KC no publica las Muy Bajo VIIRS 375   -> P2 PIERDE, NO CUMPLE (suma)
  empate      KG deja 20 negativos, KC 10                   -> P2 EMPATE
  magnitud    gana, y KC con 1/20 de magnitud en VIIRS 750  -> CUMPLE EN DETECCION, FALLA EN MAGNITUD
  p4          gana, y KC corre 4 km al este los cumulos     -> P4 de KC FALLA y el global lo anota
  noapaga     BC sin la corona pero sin apagar nada         -> mecanismo LA CAJA NO APAGA
  q2          BC apaga ademas lo que tiene calor en la caja  -> Q2 FALLA, global INDECIDIBLE
  sinclave    el log de KC sin la clave de la caja          -> KC ROTO, INDECIDIBLE
  cajafalsa   el log de KC dice caja apagada                -> KC ROTO
  cobert      a KC le falta una pasada                      -> cobertura despareja, INDECIDIBLE
  determ      KG distinto en 100 pasadas                    -> determinismo FALLA, INDECIDIBLE
  capa_mod    la capa historica congelada cambio            -> referencia_ok False, INDECIDIBLE
  d1          dirigida D1 (Lascar, marzo), K y KC iguales   -> veto CUMPLE
  d1_pend     KC oculta la protegida MODIS del 2026-03-27   -> PENDIENTE DE REPETICION (sin gemelo)
  d1_rep_si   con la repeticion que la vuelve a perder      -> NO CUMPLE (veto)
  d1_rep_no   con la repeticion que no la pierde            -> CUMPLE (veto)
  log_real    logs REALES del run 38560317428 (workflow sin la clave de la caja) -> K ROTO, INDECIDIBLE
  combinar    inerte, d1 y veto                             -> NO CUMPLE (veto)

Uso: python probar_evaluar_caja.py <TMP> <DIR_NDC>   (DIR_NDC: logs/ del run 38560317428)
"""
import copy, json, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import evaluar_caja as C  # noqa: E402
E, S, bp = C.E, C.S, C.bp
TMP = Path(sys.argv[1]); TMP.mkdir(parents=True, exist_ok=True)
NDC = Path(sys.argv[2])
PROD = RAIZ / "data" / "mirova_equivalent"
ANCLAS, INNER = S.lc.anclas(), bp.inner_desde_html()
TODOS = ("K", "KC", "KG", "B", "BC")


def recortar(desde, hasta, vols):
    out = {}
    for v in vols:
        d = json.load(open(PROD / (v + ".json"), encoding="utf-8"))
        out[v] = {"records": [r for r in d["records"] if desde <= r.get("datetime_utc", "")[:10] <= hasta]}
        for r in out[v]["records"]:
            r["triggered_test1"] = False
    return out


def clave_rec(v, r):
    return "|".join((v, bp.bucket(r.get("sensor")) or "", r.get("datetime_utc", "")[:16]))


def clases(v, r):
    return [S.clase_pixel(q["lat"], q["lon"], ANCLAS[v], INNER[v]) for q in (r.get("anomaly_pixels") or []) if q.get("lat") is not None]


def caja(base, apagar=True):
    out = copy.deepcopy(base)
    for v, d in out.items():
        for r in d["records"]:
            cl = clases(v, r)
            if "C" not in cl:
                continue
            expuesta = "CK" not in cl
            r["anomaly_pixels"] = [q for q, c in zip([q for q in r["anomaly_pixels"] if q.get("lat") is not None], cl) if c != "C"]
            if expuesta and apagar:
                r["distance_class"] = "far"
                if r.get("primary_cluster"):
                    r["primary_cluster"]["vrp_mw"] = 0.0
    return out


def ocultar(B, k):
    """Apaga la publicacion de una pasada. La etiqueta "far" sola no basta: la primera version de esta prueba solo
    cambiaba distance_class y una pasada MODIS de Lascar (2026-03-27) seguia publicada por el tablero (isSummitDetection
    la acepta por el cumulo). Por eso tambien se lleva a cero la magnitud del cumulo, que isValidDetection exige."""
    v = k.split("|")[0]; n = 0
    for r in B[v]["records"]:
        if clave_rec(v, r) == k:
            r["distance_class"] = "far"; n += 1
            if r.get("primary_cluster"):
                r["primary_cluster"]["vrp_mw"] = 0.0
    assert n >= 1, k


def log(n, cambia=None, quitar=()):
    d = dict(zip(C.CLAVES, C.DECLARADO[n])); d.update(C.EXTRA)
    d.update(PROFILE_NAME=C.BRAZOS[n], DATA_SUBDIR=C.BRAZOS[n])
    d.update(cambia or {})
    for q in quitar:
        d.pop(q, None)
    return "FLAGS_BRAZO " + json.dumps(d) + "\n(salida del pipeline)\n"


def escribir(dirr, B, logs_cambia=None, logs_quitar=None):
    (dirr / "logs").mkdir(parents=True, exist_ok=True)
    for n, datos in B.items():
        (dirr / C.BRAZOS[n]).mkdir(parents=True, exist_ok=True)
        for v, d in datos.items():
            json.dump(d, open(dirr / C.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            (dirr / "logs" / ("%s_%s.log" % (C.BRAZOS[n], v))).write_text(
                log(n, (logs_cambia or {}).get((n, v)), (logs_quitar or {}).get((n, v), ())), encoding="utf-8")


def correr(caso, B, ventana="V1", extra=(), logs_cambia=None, logs_quitar=None, rep=None):
    dirr = TMP / caso; shutil.rmtree(dirr, ignore_errors=True)
    escribir(dirr / "raiz", B, logs_cambia, logs_quitar)
    args = ["--ventana", ventana, "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
            "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp")] + list(extra)
    if rep is not None:
        escribir(dirr / "rep", rep); args += ["--repeticion", str(dirr / "rep")]
    r = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py")] + args, capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    out = dirr / "res.json"
    return json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-2000:]}


def V_(r, k):
    return r.get("veredicto", {}).get(k)


def G(r, l="A"):
    return r.get("global", {}).get(l, "")


# ---------------------------------------------------------------- base y semillas (por un camino que no es el evaluador)
V1 = C.VENTANAS["V1"]
BASE = recortar(V1["desde"], V1["hasta"], bp.VOLS)
coords = bp._coords_por_volcan()
filas = S.filas_ref("v1", False)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (V1["desde"], V1["hasta"]))
dbase = TMP / "_base" / C.BRAZOS["K"]; dbase.mkdir(parents=True, exist_ok=True)
for v, d in BASE.items():
    json.dump(d, open(dbase / (v + ".json"), "w", encoding="utf-8"))
recs = S.ev.cargar_brazo(dbase, coords, INNER, (V1["desde"], V1["hasta"]))
bp.etiquetar(recs, por_vb, ns, nv); S.anotar(recs, S.crudos(dbase, bp.VOLS, V1["desde"], V1["hasta"]), por_vb, ANCLAS, INNER)
L = {"|".join((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))): r for r in recs}
v375 = sorted(k for k in L if k.split("|")[1] == "VIIRS375")
K_PROT = next(k for k in v375 if L[k]["prot_A"] and L[k]["pub"] and L[k]["cat"] != "expuesta" and "SNPP" not in (L[k]["plataforma"] or ""))
NEG_PUB = [k for k in v375 if L[k]["lab"] == "neg_limpio" and L[k]["pub"]]
MB_PUB = [k for k in v375 if L[k]["lab"] == "pos" and not L[k]["prot_A"] and L[k]["pub"]]
PUB = [k for k in v375 if L[k]["pub"]]
EXP_PROT = {s: sum(1 for k, r in L.items() if r["b"] == s and r["pub"] and r["cat"] == "expuesta" and (r["prot_A"] or r["prot_B"])) for s in C.SENS}
EXP_NEG = {s: sum(1 for k, r in L.items() if r["b"] == s and r["pub"] and r["cat"] == "expuesta" and r["lab"] == "neg_limpio") for s in C.SENS}
print("semillas: protegida %s | negativos publicados V375 %d | Muy Bajo publicadas V375 %d | protegidas expuestas %s | negativos expuestos %s" % (
    K_PROT, len(NEG_PUB), len(MB_PUB), EXP_PROT, EXP_NEG))


def brazos(kc=None, bc=None, kg=None):
    b = {n: copy.deepcopy(BASE) for n in ("K", "B")}
    b["KC"] = kc if kc is not None else copy.deepcopy(BASE)
    b["KG"] = kg if kg is not None else copy.deepcopy(BASE)
    b["BC"] = bc if bc is not None else caja(BASE)
    return b


chk = {}
r = correr("nulo", brazos(bc=copy.deepcopy(BASE)))
chk["nulo: sin huella en BC -> INDECIDIBLE (control positivo)"] = r.get("huella", {}).get("BC") is False and G(r).startswith("INDECIDIBLE")

r = correr("efectiva", brazos(kc=caja(BASE)))
chk["efectiva: controles OK, huella en KC y BC"] = r.get("controles_ok") is True and r.get("huella", {}).get("BC") is True and r.get("huella", {}).get("KC") is True
chk["efectiva: Q1 y Q2 CUMPLE, LA CAJA ACTUA"] = V_(r, "Q1|BC") == "CUMPLE" and V_(r, "Q2|BC") == "CUMPLE" and r.get("mecanismo", "").startswith("LA CAJA ACTUA")
chk["efectiva: P1 segun la base (VETADO donde hay protegida expuesta)"] = all(
    V_(r, "P1|%s|B" % s) == ("VETADO" if EXP_PROT[s] else "CUMPLE") for s in C.SENS if V_(r, "P1|%s|B" % s) != "SIN SUSTRATO")
chk["efectiva: P2 VIIRS 375 GANA si la base tiene negativos expuestos"] = V_(r, "P2|VIIRS375|A") == ("GANA" if EXP_NEG["VIIRS375"] else "EMPATE") \
    or G(r).startswith("NO CUMPLE (veto)")

r = correr("inerte", brazos())
INERTE = TMP / "inerte" / "res.json"
chk["inerte: NO CUMPLE (no mejora: inerte), mecanismo ACTUA"] = G(r) == "NO CUMPLE (no mejora el criterio: la caja es inerte sobre el candidato)" \
    and r.get("mecanismo", "").startswith("LA CAJA ACTUA") and all(V_(r, "P2|%s|A" % s) == "EMPATE" for s in C.SENS)

B = brazos(); ocultar(B["KC"], K_PROT); r = correr("veto", B)
VETO = TMP / "veto" / "res.json"
chk["veto: P1 VETADO y NO CUMPLE (veto)"] = V_(r, "P1|VIIRS375|A") == "VETADO" and G(r) == "NO CUMPLE (veto)"
B = brazos(); ocultar(B["KC"], K_PROT); ocultar(B["KG"], K_PROT); r = correr("gemelo", B)
chk["gemelo: el gemelo tambien la oculta -> P1 INDECIDIBLE"] = V_(r, "P1|VIIRS375|A") == "INDECIDIBLE" and r.get("controles_ok") is True

B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]; r = correr("gana", B)
chk["gana: P2 GANA y CUMPLE"] = V_(r, "P2|VIIRS375|A") == "GANA" and G(r).startswith("CUMPLE")
chk["gana: P2b fuera del techo (el sustrato no lo explica)"] = (V_(r, "P2b|VIIRS375|A") or "").startswith("FUERA") == (len(NEG_PUB) > C.TECHO_P2["VIIRS375"])
B = brazos(); [ocultar(B["KC"], k) for k in MB_PUB]; r = correr("pierde", B)
chk["pierde: P2 PIERDE y NO CUMPLE (suma)"] = V_(r, "P2|VIIRS375|A") == "PIERDE" and G(r) == "NO CUMPLE (suma de errores)"
B = brazos(); [ocultar(B["KG"], k) for k in NEG_PUB[:20]]; [ocultar(B["KC"], k) for k in NEG_PUB[:10]]; r = correr("empate", B)
chk["empate: 10 menos con 20 discordantes -> EMPATE"] = V_(r, "P2|VIIRS375|A") == "EMPATE" and r.get("suma", {}).get("VIIRS375|A", {}).get("ruido") == 20

B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]
for v in bp.VOLS:
    for rr in B["KC"][v]["records"]:
        if (rr.get("sensor") or "").endswith("_750"):
            for c in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw"):
                if rr.get(c): rr[c] *= 0.05
            if rr.get("primary_cluster") and rr["primary_cluster"].get("vrp_mw"): rr["primary_cluster"]["vrp_mw"] *= 0.05
            for q in rr.get("anomaly_pixels") or []:
                if q.get("vrp_mw"): q["vrp_mw"] *= 0.05
r = correr("magnitud", B)
chk["magnitud: P3 FALLA en VIIRS 750 y el global lo dice"] = V_(r, "P3|VIIRS750") == "FALLA" and "FALLA EN MAGNITUD" in G(r)

B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]
for v in C.CENTRADOS:
    for rr in B["KC"][v]["records"]:
        pc = rr.get("primary_cluster") or {}
        if bp.bucket(rr.get("sensor")) == "VIIRS375" and pc.get("centroid_lon") is not None:
            pc["centroid_lon"] += 0.05
r = correr("p4", B)
chk["p4: KC con los cumulos fuera de la caja -> P4 FALLA y el global lo anota"] = V_(r, "P4|KC|VIIRS375") == "FALLA" and "P4" in G(r)

r = correr("noapaga", brazos(bc=caja(BASE, apagar=False)))
chk["noapaga: corona quitada sin apagar -> LA CAJA NO APAGA"] = r.get("mecanismo", "").startswith("LA CAJA NO APAGA")

BC = caja(BASE)
for k, x in L.items():
    if x["lab"] == "neg_limpio" and x["pub"] and x["px"]["CK"] > 0:
        ocultar(BC, k)
r = correr("q2", brazos(bc=BC))
chk["q2: la caja toca lo de adentro -> Q2 FALLA, INDECIDIBLE"] = V_(r, "Q2|BC") == "FALLA" and G(r).startswith("INDECIDIBLE")

r = correr("sinclave", brazos(), logs_quitar={("KC", "Lascar"): ("ENABLE_ROI1_BOX_PAPER",)})
chk["sinclave: log sin la clave de la caja -> KC ROTO, INDECIDIBLE"] = r.get("cableado", {}).get("KC") is False and G(r) == "INDECIDIBLE"
r = correr("cajafalsa", brazos(), logs_cambia={("KC", "Villarrica"): {"ENABLE_ROI1_BOX_PAPER": False}})
chk["cajafalsa: log con la caja apagada -> KC ROTO"] = r.get("cableado", {}).get("KC") is False and G(r) == "INDECIDIBLE"

B = brazos(); B["KC"]["Lascar"]["records"] = B["KC"]["Lascar"]["records"][1:]; r = correr("cobert", B)
chk["cobert: a KC le falta una pasada -> INDECIDIBLE"] = r.get("cobertura_ok") is False and G(r) == "INDECIDIBLE"
B = brazos(); [ocultar(B["KG"], k) for k in PUB[:100]]; r = correr("determ", B)
chk["determ: gemelo distinto en 100 pasadas -> INDECIDIBLE"] = r.get("determinismo_ok") is False and G(r) == "INDECIDIBLE"


def _ensuciar_capa(d):
    p = d / "consolidado_filas_perdidas.csv"
    p.write_text(p.read_text(encoding="utf-8") + p.read_text(encoding="utf-8").splitlines()[-1] + "\n", encoding="utf-8")


dref = TMP / "_ref_mod"; shutil.rmtree(dref, ignore_errors=True); shutil.copytree(V1["ref"], dref); _ensuciar_capa(dref)
r = correr("capa_mod", brazos(), extra=("--ref", str(dref)))
chk["capa_mod: capa cambiada -> referencia_ok False, INDECIDIBLE"] = r.get("referencia_ok") is False and G(r) == "INDECIDIBLE"

# Dirigida D1: Lascar, 2026-03-14 a 03-27
D1 = C.VENTANAS["D1"]; BD = recortar(D1["desde"], D1["hasta"], ("Lascar",))
r = correr("d1", {"K": copy.deepcopy(BD), "KC": copy.deepcopy(BD)}, ventana="D1")
D1R = TMP / "d1" / "res.json"
# La semilla sale de la tabla del caso: una alerta MODIS de 1 MW o mas que K publica. (La primera version sembraba la
# pasada del 2026-03-27 07:10, pero en los records de produccion esa pasada NO esta publicada: el caso no probaba nada.)
tk = json.loads((TMP / "d1" / "tmp" / "t_K_KC.json").read_text(encoding="utf-8"))["pasadas"]
P27 = next(k for k, v in sorted(tk.items()) if "|MODIS|" in k and v["control"]["lab"] == "pos" and v["control"]["pub"] and (v["control"]["vrp_ref"] or 0) >= 1)
print("semilla D1: %s" % P27)
chk["d1: K y KC iguales -> veto CUMPLE"] = G(r) == "CUMPLE (veto)" and V_(r, "P1|MODIS|A") == "CUMPLE"
B = {"K": copy.deepcopy(BD), "KC": copy.deepcopy(BD)}; ocultar(B["KC"], P27)
r = correr("d1_pend", B, ventana="D1")
chk["d1_pend: KC la pierde, sin gemelo -> PENDIENTE DE REPETICION"] = V_(r, "P1|MODIS|A") == "PENDIENTE DE REPETICION" and G(r) == "PENDIENTE DE REPETICION"
rep = {"K": copy.deepcopy(BD), "KC": copy.deepcopy(BD)}; ocultar(rep["KC"], P27)
r = correr("d1_rep_si", B, ventana="D1", rep=rep)
chk["d1_rep_si: la repeticion la vuelve a perder -> NO CUMPLE (veto)"] = G(r) == "NO CUMPLE (veto)"
r = correr("d1_rep_no", B, ventana="D1", rep={"K": copy.deepcopy(BD), "KC": copy.deepcopy(BD)})
chk["d1_rep_no: la repeticion no la pierde -> CUMPLE (veto)"] = G(r) == "CUMPLE (veto)"

# Logs REALES del workflow de hoy (antes de esta tarea): no traen la clave de la caja
B = brazos(); dirr = TMP / "log_real"; shutil.rmtree(dirr, ignore_errors=True)
escribir(dirr / "raiz", {n: {"NevadosDeChillan": B[n]["NevadosDeChillan"]} for n in TODOS})
shutil.copy(NDC / "logs" / ("%s_NevadosDeChillan.log" % C.BRAZOS["K"]), dirr / "raiz" / "logs")
rr = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py"), "--ventana", "V1", "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
                     "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp"), "--vols", "NevadosDeChillan"], capture_output=True, text=True, encoding="utf-8")
(TMP / "log_real.txt").write_text(rr.stdout + rr.stderr, encoding="utf-8")
r = json.loads((dirr / "res.json").read_text(encoding="utf-8")) if (dirr / "res.json").exists() else {}
chk["log_real: el log real de K (sin la clave de la caja) -> K ROTO, INDECIDIBLE"] = r.get("cableado", {}).get("K") is False and G(r) == "INDECIDIBLE"

rc = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py"), "--combinar", str(INERTE), str(D1R), str(VETO)], capture_output=True, text=True, encoding="utf-8")
(TMP / "combinar.txt").write_text(rc.stdout + rc.stderr, encoding="utf-8")
chk["combinar: inerte, d1 y veto -> NO CUMPLE (veto)"] = "KC lectura A: NO CUMPLE (veto)" in rc.stdout
rc = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py"), "--combinar", str(INERTE), str(D1R)], capture_output=True, text=True, encoding="utf-8")
chk["combinar: inerte y d1 -> NO CUMPLE (no mejora)"] = "KC lectura A: NO CUMPLE (no mejora" in rc.stdout

print("== RESUMEN (salida completa de cada caso en %s)" % TMP)
for k, v in chk.items():
    print("  ", "OK   " if v else "FALLA", k)
print("%d de %d" % (sum(chk.values()), len(chk)))
sys.exit(0 if all(chk.values()) else 1)
