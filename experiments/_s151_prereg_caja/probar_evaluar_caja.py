# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. Prueba de evaluar_caja.py (version 2) ANTES de despachar: cada veredicto que el evaluador puede dar
tiene que poder salir, con un caso que lo produce y otro que no (A110, A116). Los brazos se fabrican desde los records de
produccion de la ventana (11 volcanes, con `triggered_test1` en falso, como en la prueba de F y K) y la referencia
congelada de esa ventana, con la linea FLAGS_BRAZO en el log como la escribe el workflow con la linea de esta tarea.

"Aplicar la caja" a un brazo fabricado (`caja()`): se le quitan los pixeles alertados de la corona (dentro del circulo,
fuera de la caja, con la geometria de sustrato.py) y se apagan las pasadas EXPUESTAS. Es la caja perfectamente eficaz.

Casos con el DESPACHO de la version 2 (V1 solo con B y BC; D1 con K y KC):
  mec          BC con la caja                                -> sin veredicto de KC, mecanismo LA CAJA ACTUA (Q1 por Fisher)
  mec_nulo     BC igual a B                                  -> sin huella: mecanismo INDECIDIBLE
  noapaga      BC sin la corona pero sin apagar nada         -> LA CAJA NO APAGA
  q2           BC apaga ademas lo que tiene calor en la caja  -> Q2 FALLA, mecanismo INDECIDIBLE
  d1 ...       veto de la dirigida: CUMPLE, PENDIENTE, NO CUMPLE y CUMPLE con la repeticion
  combinar     mec + d1 -> CUMPLE (veto); mec_nulo + d1 -> INDECIDIBLE (el mecanismo no paso); + veto -> NO CUMPLE (veto)
Casos con K, KC y KG en V1 (--brazos; fuera del despacho, pero las reglas tienen que funcionar):
  nulo         cinco brazos identicos                        -> sin huella en BC: INDECIDIBLE
  inerte       KC igual a K                                  -> P2 EMPATE (ruido 0), P3 SIN SUSTRATO (ningun par cambia),
                                                                NO CUMPLE (inerte)
  veto/gemelo  KC oculta una protegida centrada; KG tambien   -> VETADO; INDECIDIBLE
  corrido      KC oculta una protegida de un volcan corrido   -> no decide: P1 CUMPLE, se informa
  gana         KC no publica los negativos centrados         -> GANA, CUMPLE, P2b FUERA del techo
  pierde       KC no publica las Muy Bajo centradas          -> PIERDE
  ruido_chico  KG difiere en 2 negativos, KC en 1            -> cambio dentro del ruido: P2 INDECIDIBLE (no inerte, arreglo D4)
  gana_ruido   KG difiere en 1, KC en 5                      -> GANA (supera el ruido)
  ruido_grande KG difiere en 20                              -> ruido no menor que el techo: determinismo FALLA, INDECIDIBLE
  p3_cambian   gana, y 6 pares VIIRS 750 con 1/20 de magnitud -> P3 FALLA (con TODOS los pares la mediana seria 0, arreglo D3)
  p4           gana, y los cumulos corridos 4 km al este     -> P4 de KC FALLA y el global lo anota
  sinclave, cajafalsa, cobert, determ, capa_mod             -> ROTO, ROTO, cobertura, determinismo, referencia: INDECIDIBLE
  log_real     logs REALES del run 38560317428 (sin la clave de la caja) -> K ROTO, INDECIDIBLE

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
CINCO = ("K", "KC", "KG", "B", "BC")


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
    """Apaga la publicacion de una pasada. La etiqueta "far" sola no basta: una pasada MODIS de Lascar seguia publicada
    por el tablero (isSummitDetection la acepta por el cumulo). Por eso tambien se lleva a cero la magnitud del cumulo."""
    v = k.split("|")[0]; n = 0
    for r in B[v]["records"]:
        if clave_rec(v, r) == k:
            r["distance_class"] = "far"; n += 1
            if r.get("primary_cluster"):
                r["primary_cluster"]["vrp_mw"] = 0.0
    assert n >= 1, k


def dividir(B, k, f=0.05):
    v = k.split("|")[0]
    for r in B[v]["records"]:
        if clave_rec(v, r) == k:
            for c in ("vrp_mw", "vrp_mir_mw", "f5_core_vrp_mw"):
                if r.get(c): r[c] *= f
            if r.get("primary_cluster") and r["primary_cluster"].get("vrp_mw"): r["primary_cluster"]["vrp_mw"] *= f
            for q in r.get("anomaly_pixels") or []:
                if q.get("vrp_mw"): q["vrp_mw"] *= f


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


def correr(caso, B, ventana="V1", extra=(), logs_cambia=None, logs_quitar=None, rep=None, cinco=True):
    dirr = TMP / caso; shutil.rmtree(dirr, ignore_errors=True)
    escribir(dirr / "raiz", B, logs_cambia, logs_quitar)
    args = ["--ventana", ventana, "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
            "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp")] + list(extra)
    if ventana == "V1" and cinco:
        args += ["--brazos", ",".join(CINCO)]
    if rep is not None:
        escribir(dirr / "rep", rep); args += ["--repeticion", str(dirr / "rep")]
    r = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py")] + args, capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    out = dirr / "res.json"
    return json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-2000:]}


def V_(r, k):
    return r.get("veredicto", {}).get(k)


def G(r, l="A"):
    return (r.get("global") or {}).get(l, "")


def combinar(*archivos):
    rc = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py"), "--combinar"] + [str(f) for f in archivos],
                        capture_output=True, text=True, encoding="utf-8")
    return rc.stdout


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
bp.etiquetar(recs, por_vb, ns, nv); S.ev.anotar_vrp_mirova(recs, por_vb)
S.anotar(recs, S.crudos(dbase, bp.VOLS, V1["desde"], V1["hasta"]), por_vb, ANCLAS, INNER)
L = {"|".join((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))): r for r in recs}
cen = lambda k: k.split("|")[0] in C.CENTRADOS
v375 = sorted(k for k in L if k.split("|")[1] == "VIIRS375")
K_PROT = next(k for k in v375 if cen(k) and L[k]["prot_A"] and L[k]["pub"] and L[k]["cat"] != "expuesta" and "SNPP" not in (L[k]["plataforma"] or ""))
K_PROT_CORR = next(k for k in sorted(L) if not cen(k) and L[k]["prot_A"] and L[k]["pub"] and "SNPP" not in (L[k]["plataforma"] or ""))
NEG_PUB = [k for k in v375 if cen(k) and L[k]["lab"] == "neg_limpio" and L[k]["pub"]]
MB_PUB = [k for k in v375 if cen(k) and L[k]["lab"] == "pos" and not L[k]["prot_A"] and L[k]["pub"]]
PUB = [k for k in v375 if cen(k) and L[k]["pub"]]
V750_ALERTA = sorted(k for k in L if cen(k) and k.split("|")[1] == "VIIRS750" and L[k]["lab"] == "pos" and L[k]["pub"] and L[k].get("vrp_ref"))
print("semillas: protegida centrada %s | protegida corrida %s | negativos centrados publicados V375 %d | Muy Bajo %d | alertas V750 %d" % (
    K_PROT, K_PROT_CORR, len(NEG_PUB), len(MB_PUB), len(V750_ALERTA)))


def brazos(kc=None, bc=None, kg=None):
    return {"K": copy.deepcopy(BASE), "KC": kc if kc is not None else copy.deepcopy(BASE),
            "KG": kg if kg is not None else copy.deepcopy(BASE), "B": copy.deepcopy(BASE), "BC": bc if bc is not None else caja(BASE)}


def solo_b(bc):
    return {"B": copy.deepcopy(BASE), "BC": bc}


chk = {}
# ---------------- despacho de la version 2: mecanismo en V1 con B y BC
r = correr("mec", solo_b(caja(BASE)), cinco=False)
MEC = TMP / "mec" / "res.json"
chk["mec: sin KC no hay veredicto de KC; LA CAJA ACTUA (Q1 por Fisher, Q2 CUMPLE)"] = r.get("global") is None and V_(r, "Q1|BC") == "CUMPLE" \
    and V_(r, "Q2|BC") == "CUMPLE" and r.get("mecanismo", "").startswith("LA CAJA ACTUA") and r.get("controles_ok") is True
r = correr("mec_nulo", solo_b(copy.deepcopy(BASE)), cinco=False)
MEC_NULO = TMP / "mec_nulo" / "res.json"
chk["mec_nulo: BC igual a B -> sin huella, mecanismo INDECIDIBLE"] = r.get("huella", {}).get("BC") is False and r.get("mecanismo", "").startswith("INDECIDIBLE")
r = correr("noapaga", solo_b(caja(BASE, apagar=False)), cinco=False)
chk["noapaga: corona quitada sin apagar -> LA CAJA NO APAGA"] = r.get("mecanismo", "").startswith("LA CAJA NO APAGA")
BC = caja(BASE)
for k, x in L.items():
    if cen(k) and x["lab"] == "neg_limpio" and x["pub"] and x["px"]["CK"] > 0:
        ocultar(BC, k)
r = correr("q2", solo_b(BC), cinco=False)
chk["q2: la caja toca lo de adentro -> Q2 FALLA, mecanismo INDECIDIBLE"] = V_(r, "Q2|BC") == "FALLA" and r.get("mecanismo", "").startswith("INDECIDIBLE")

# ---------------- dirigida D1
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
D1_VETO = TMP / "d1_rep_si" / "res.json"
chk["d1_rep_si: la repeticion la vuelve a perder -> NO CUMPLE (veto)"] = G(r) == "NO CUMPLE (veto)"
r = correr("d1_rep_no", B, ventana="D1", rep={"K": copy.deepcopy(BD), "KC": copy.deepcopy(BD)})
chk["d1_rep_no: la repeticion no la pierde -> CUMPLE (veto)"] = G(r) == "CUMPLE (veto)"

out = combinar(MEC, D1R)
chk["combinar: mec y d1 -> KC CUMPLE (veto)"] = "KC lectura A: CUMPLE (veto)" in out
out = combinar(MEC_NULO, D1R)
chk["combinar: mec_nulo y d1 -> INDECIDIBLE (el mecanismo no paso)"] = "KC lectura A: INDECIDIBLE (el mecanismo de V1 no paso su control)" in out
out = combinar(MEC, D1R, D1_VETO)
chk["combinar: mec, d1 y un veto -> NO CUMPLE (veto)"] = "KC lectura A: NO CUMPLE (veto)" in out

# ---------------- reglas con K, KC y KG en V1
r = correr("nulo", brazos(bc=copy.deepcopy(BASE)))
chk["nulo: sin huella en BC -> INDECIDIBLE (control positivo)"] = r.get("huella", {}).get("BC") is False and G(r).startswith("INDECIDIBLE")
r = correr("inerte", brazos())
chk["inerte: P2 EMPATE con ruido 0, P3 SIN SUSTRATO (ningun par cambia), NO CUMPLE (inerte)"] = \
    all(V_(r, "P2|%s|A" % s) == "EMPATE" for s in C.SENS) and all(V_(r, "P3|%s" % s) == "SIN SUSTRATO" for s in C.SENS) \
    and G(r) == "NO CUMPLE (no mejora el criterio: la caja es inerte sobre el candidato)"
B = brazos(); ocultar(B["KC"], K_PROT); r = correr("veto", B)
chk["veto: protegida centrada -> VETADO, NO CUMPLE (veto)"] = V_(r, "P1|VIIRS375|A") == "VETADO" and G(r) == "NO CUMPLE (veto)"
B = brazos(); ocultar(B["KC"], K_PROT); ocultar(B["KG"], K_PROT); r = correr("gemelo", B)
chk["gemelo: el gemelo tambien la oculta -> P1 INDECIDIBLE"] = V_(r, "P1|VIIRS375|A") == "INDECIDIBLE"
B = brazos(); ocultar(B["KC"], K_PROT_CORR); r = correr("corrido", B)
s_corr = K_PROT_CORR.split("|")[1]
chk["corrido: perdida en un volcan corrido -> no decide (se informa)"] = V_(r, "P1|%s|A" % s_corr) in ("CUMPLE", "SIN SUSTRATO") and "volcan corrido (informa)" in (TMP / "corrido.txt").read_text(encoding="utf-8")
B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]; r = correr("gana", B)
chk["gana: P2 GANA, CUMPLE, P2b FUERA del techo"] = V_(r, "P2|VIIRS375|A") == "GANA" and G(r).startswith("CUMPLE") and (V_(r, "P2b|VIIRS375|A") or "").startswith("FUERA")
B = brazos(); [ocultar(B["KC"], k) for k in MB_PUB]; r = correr("pierde", B)
chk["pierde: P2 PIERDE, NO CUMPLE (suma)"] = V_(r, "P2|VIIRS375|A") == "PIERDE" and G(r) == "NO CUMPLE (suma de errores)"
B = brazos(); [ocultar(B["KG"], k) for k in NEG_PUB[:2]]; ocultar(B["KC"], NEG_PUB[5]); r = correr("ruido_chico", B)
chk["ruido_chico: cambio de 1 dentro de un ruido de 2 -> P2 INDECIDIBLE, global INDECIDIBLE (no inerte)"] = \
    r.get("determinismo_ok") is True and V_(r, "P2|VIIRS375|A") == "INDECIDIBLE" and G(r) == "INDECIDIBLE"
B = brazos(); ocultar(B["KG"], NEG_PUB[0]); [ocultar(B["KC"], k) for k in NEG_PUB[1:6]]; r = correr("gana_ruido", B)
chk["gana_ruido: 5 menos con ruido 1 -> GANA"] = V_(r, "P2|VIIRS375|A") == "GANA"
B = brazos(); [ocultar(B["KG"], k) for k in NEG_PUB[:20]]; [ocultar(B["KC"], k) for k in NEG_PUB[:10]]; r = correr("ruido_grande", B)
chk["ruido_grande: ruido 20 no menor que el techo 3 -> determinismo FALLA, INDECIDIBLE"] = r.get("determinismo_ok") is False and G(r) == "INDECIDIBLE"
B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]; [dividir(B["KC"], k) for k in V750_ALERTA[:6]]; r = correr("p3_cambian", B)
chk["p3_cambian: 6 pares VIIRS 750 por 20 -> P3 FALLA solo con los pares que cambian"] = V_(r, "P3|VIIRS750") == "FALLA" and "FALLA EN MAGNITUD" in G(r)
B = brazos(); [ocultar(B["KC"], k) for k in NEG_PUB]
for v in C.CENTRADOS:
    for rr in B["KC"][v]["records"]:
        pc = rr.get("primary_cluster") or {}
        if bp.bucket(rr.get("sensor")) == "VIIRS375" and pc.get("centroid_lon") is not None:
            pc["centroid_lon"] += 0.05
r = correr("p4", B)
chk["p4: cumulos fuera de la caja -> P4 de KC FALLA y el global lo anota"] = V_(r, "P4|KC|VIIRS375") == "FALLA" and "P4" in G(r)
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

# Logs REALES del workflow anterior a esta tarea: no traen la clave de la caja
B = brazos(); dirr = TMP / "log_real"; shutil.rmtree(dirr, ignore_errors=True)
escribir(dirr / "raiz", {n: {"NevadosDeChillan": B[n]["NevadosDeChillan"]} for n in CINCO})
shutil.copy(NDC / "logs" / ("%s_NevadosDeChillan.log" % C.BRAZOS["K"]), dirr / "raiz" / "logs")
rr = subprocess.run([sys.executable, str(AQUI / "evaluar_caja.py"), "--ventana", "V1", "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
                     "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp"), "--vols", "NevadosDeChillan", "--brazos", ",".join(CINCO)],
                    capture_output=True, text=True, encoding="utf-8")
(TMP / "log_real.txt").write_text(rr.stdout + rr.stderr, encoding="utf-8")
r = json.loads((dirr / "res.json").read_text(encoding="utf-8")) if (dirr / "res.json").exists() else {}
chk["log_real: el log real de K (sin la clave de la caja) -> K ROTO, INDECIDIBLE"] = r.get("cableado", {}).get("K") is False and G(r) == "INDECIDIBLE"

print("== RESUMEN (salida completa de cada caso en %s)" % TMP)
for k, v in chk.items():
    print("  ", "OK   " if v else "FALLA", k)
print("%d de %d" % (sum(chk.values()), len(chk)))
sys.exit(0 if all(chk.values()) else 1)
