# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. Prueba de evaluar_fk.py ANTES de despachar: cada veredicto que el evaluador puede dar
tiene que poder salir, con un caso que lo produce y otro que no (A110, A116). Los brazos se fabrican desde los
records de produccion de la ventana V1 (11 volcanes, recortados a la ventana) y la referencia congelada de V1,
con la linea FLAGS_BRAZO en el log igual que la escribe el workflow. Ademas, un caso sobre el run REAL de
Nevados de Chillan (38560317428), que tiene que reproducir la suma de errores que publico su verificador.

Casos (nombre: lo sembrado -> lo esperado):
  nulo      cuatro brazos identicos                                  -> controles OK, P1 CUMPLE, P2 EMPATE, P3 y P4 CUMPLE,
                                                                        y el candidato NO CUMPLE (no gana en ningun sensor)
  veto      F y K ocultan una protegida VIIRS 375 que C0 publica      -> P1 VETADO (A y B), global NO CUMPLE (veto)
  gemelo    lo mismo, y el gemelo de C0 tambien la oculta             -> P1 INDECIDIBLE (ruido de C0)
  fk        solo K la oculta (F no)                                   -> P1 de K INDECIDIBLE (ruido del candidato), F CUMPLE
  snpp      F y K ocultan una protegida solo del OCR de Suomi NPP     -> P1 lectura A CUMPLE (se informa), lectura B VETADO
  lecturab  F y K ocultan una pasada protegida solo con la lectura B  -> P1 A CUMPLE, P1 B VETADO
  gana      F y K no publican en los negativos limpios de VIIRS 375   -> P2 GANA y global CUMPLE
  pierde    F y K no publican las alertas Muy Bajo de VIIRS 375       -> P2 PIERDE, global NO CUMPLE (suma)
  empate    el gemelo deja 20 negativos, F y K dejan 10               -> P2 EMPATE (dentro del ruido)
  magnitud  "gana", y ademas F y K publican VIIRS 750 con 1/20 de la magnitud -> P3 FALLA, global CUMPLE EN DETECCION, FALLA EN MAGNITUD
  mueve     F y K corren 2 km el cumulo de VIIRS 375                  -> P4 FALLA
  cable     el log de K dice banda 21 en un volcan                    -> K mal cableado, todo lo de K INDECIDIBLE
  cobert    a K le falta una pasada                                   -> cobertura despareja, todo INDECIDIBLE
  determ    el gemelo cambia la decision en 100 pasadas VIIRS 375     -> determinismo FALLA, todo INDECIDIBLE
  rep_no    V2 sin gemelo (C0 y K): K oculta una protegida; la repeticion no la pierde -> P1 INDECIDIBLE
  rep_si    lo mismo, y la repeticion si la pierde                    -> P1 VETADO
  tabla     con --solo-tabla, F y K ocultan la protegida solo OCR     -> P1 A y B CUMPLE (no es positiva)
  ndc       run real de Nevados de Chillan, gemelo = copia de C0       -> suma C0 52, F 7, K 7; P1 VIIRS CUMPLE; K recupera la MODIS del 1-oct
  combinar  nulo y veto juntos                                        -> K NO CUMPLE

Uso: python probar_evaluar_fk.py <TMP> <DIR_NDC>
  <DIR_NDC> tiene _s146_ab_control/, _s147_ab_sin_test1_max/, _s149_ab_sin_test1_b22_max/ (NevadosDeChillan.json) y
  logs/ del run 38560317428 (rama s146-ab/38560317428). Salida completa de cada caso en <TMP>/<caso>.txt.
"""
import copy, io, json, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import evaluar_fk as E  # noqa: E402  (ya envuelve sys.stdout en utf-8)
import sustrato as S  # noqa: E402
TMP = Path(sys.argv[1]); TMP.mkdir(parents=True, exist_ok=True)
NDC = Path(sys.argv[2])
V = E.VENTANAS["V1"]; VOLS = list(E.bp.VOLS)
PROD = RAIZ / "data" / "mirova_equivalent"


def recortar():
    out = {}
    for v in VOLS:
        d = json.load(open(PROD / (v + ".json"), encoding="utf-8"))
        out[v] = {"records": [r for r in d["records"] if V["desde"] <= r.get("datetime_utc", "")[:10] <= V["hasta"]]}
        for r in out[v]["records"]:
            r["triggered_test1"] = False   # huella de "sin Test 1"; se aplica a los cuatro para que el nulo sea identico
    return out


BASE = recortar()


def clave_rec(v, r):
    return "|".join((v, E.bp.bucket(r.get("sensor")) or "", r.get("datetime_utc", "")[:16]))


def etiquetas():
    """Etiqueta, publicacion y proteccion de cada pasada del brazo base, con el codigo del evaluador."""
    d = TMP / "_base" / E.BRAZOS["C0"]; d.mkdir(parents=True, exist_ok=True)
    for v in VOLS:
        json.dump(BASE[v], open(d / (v + ".json"), "w", encoding="utf-8"))
    filas = S.cargar_filas(V["ref"], False)
    recs, _ = S.etiquetar_todo(d, filas, (V["desde"], V["hasta"]), set(VOLS))
    claves = {"|".join(ev_k(r)): r for r in recs}
    prot = E.proteccion(set(claves), V["ref"] / "registro_vrp_consolidado.csv", V["ref"] / "registro_vrp_ocr.csv", V["desde"], V["hasta"])
    return claves, prot


def ev_k(r):
    return (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))


L, P = etiquetas()
v375 = [k for k in L if k.split("|")[1] == "VIIRS375"]
K_PROT = next(k for k in sorted(v375) if P[k]["A"] and L[k]["pub"] and L[k]["lab"] == "pos" and not P[k]["alerta_solo_ocr"])
K_SNPP = next(k for k in sorted(v375) if P[k]["A"] and L[k]["pub"] and P[k]["alerta_solo_ocr"] and "SNPP" in (L[k]["plataforma"] or ""))
K_B = next(k for k in sorted(v375) if P[k]["B"] and not P[k]["A"] and L[k]["pub"])
NEG_PUB = sorted(k for k in v375 if L[k]["lab"] == "neg_limpio" and L[k]["pub"])
MB_PUB = sorted(k for k in v375 if L[k]["lab"] == "pos" and not P[k]["A"] and L[k]["pub"])
PUB_V375 = sorted(k for k in v375 if L[k]["pub"])
print("semillas: protegida %s | solo OCR Suomi NPP %s | solo lectura B %s | negativos publicados %d | Muy Bajo publicadas %d" % (
    K_PROT, K_SNPP, K_B, len(NEG_PUB), len(MB_PUB)))


def brazos():
    return {n: copy.deepcopy(BASE) for n in ("C0", "F", "K", "G")}


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


def correr(caso, B, nombres=("C0", "F", "K", "G"), extra=(), logs_cambia=None, rep=None):
    dirr = TMP / caso; shutil.rmtree(dirr, ignore_errors=True)
    escribir(dirr / "raiz", B, nombres, logs_cambia)
    args = [sys.executable, str(AQUI / "evaluar_fk.py"), "--ventana", "V1", "--raiz", str(dirr / "raiz"), "--logs", str(dirr / "raiz" / "logs"),
            "--out", str(dirr / "res.json"), "--tmp", str(dirr / "tmp"), "--brazos", ",".join(nombres)] + list(extra)
    if rep is not None:
        escribir(dirr / "rep", rep, ("C0", "K")); args += ["--repeticion", str(dirr / "rep")]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    return json.loads((dirr / "res.json").read_text(encoding="utf-8")) if (dirr / "res.json").exists() else {}


def V_(res, clave):
    return res.get("veredicto", {}).get(clave)


chk = {}
r = correr("nulo", brazos())
chk["nulo: controles OK"] = r.get("controles_ok") is True and all(r.get("cableado", {}).values())
chk["nulo: P1 sin perdidas"] = all(V_(r, "P1|%s|%s|%s" % (X, s, l)) in ("CUMPLE", "SIN SUSTRATO") for X in "FK" for s in E.SENS_CANDIDATO[X] for l in "AB")
chk["nulo: P2 EMPATE en todo"] = all(V_(r, "P2|%s|%s|%s" % (X, s, l)) == "EMPATE" for X in "FK" for s in E.SENS_CANDIDATO[X] for l in "AB")
chk["nulo: P3 y P4 CUMPLE"] = all(V_(r, "P3|%s|%s" % (X, s)) in ("CUMPLE", "SIN SUSTRATO") for X in "FK" for s in E.SENS_CANDIDATO[X]) and V_(r, "P4|K") == "CUMPLE"
chk["nulo: K NO CUMPLE (no gana)"] = r.get("global", {}).get("K", {}).get("A") == "NO CUMPLE (no gana en ningun sensor)"
NULO = TMP / "nulo" / "res.json"

B = brazos(); ocultar(B["F"], K_PROT); ocultar(B["K"], K_PROT); r = correr("veto", B)
chk["veto: P1 K VIIRS375 A y B VETADO"] = V_(r, "P1|K|VIIRS375|A") == "VETADO" and V_(r, "P1|K|VIIRS375|B") == "VETADO"
chk["veto: global K NO CUMPLE (veto)"] = r.get("global", {}).get("K", {}).get("A") == "NO CUMPLE (veto)"
VETO = TMP / "veto" / "res.json"

B = brazos(); [ocultar(B[n], K_PROT) for n in ("F", "K", "G")]; r = correr("gemelo", B)
chk["gemelo: perdida donde el gemelo de C0 tambien cambia -> INDECIDIBLE"] = V_(r, "P1|K|VIIRS375|A") == "INDECIDIBLE" and r.get("controles_ok") is True

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
chk["empate: dentro del ruido del gemelo -> EMPATE"] = V_(r, "P2|K|VIIRS375|A") == "EMPATE" and r.get("controles_ok") is True

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

B = brazos(); [ocultar(B["G"], k) for k in PUB_V375[:100]]; r = correr("determ", B)
chk["determ: gemelo distinto en 100 pasadas -> determinismo FALLA, INDECIDIBLE"] = r.get("determinismo_ok") is False and r.get("global", {}).get("K", {}).get("A") == "INDECIDIBLE"

B = brazos(); ocultar(B["K"], K_PROT); rep = {"C0": copy.deepcopy(BASE), "K": copy.deepcopy(BASE)}
r = correr("rep_no", B, nombres=("C0", "K"), rep=rep)
chk["rep_no: la perdida no se repite -> INDECIDIBLE"] = V_(r, "P1|K|VIIRS375|A") == "INDECIDIBLE"
rep = {"C0": copy.deepcopy(BASE), "K": copy.deepcopy(BASE)}; ocultar(rep["K"], K_PROT)
r = correr("rep_si", B, nombres=("C0", "K"), rep=rep)
chk["rep_si: la perdida se repite -> VETADO"] = V_(r, "P1|K|VIIRS375|A") == "VETADO"

B = brazos(); ocultar(B["F"], K_SNPP); ocultar(B["K"], K_SNPP); r = correr("tabla", B, extra=("--solo-tabla", "si"))
chk["tabla: con la tabla sola la protegida del OCR no es positiva -> A y B CUMPLE"] = V_(r, "P1|K|VIIRS375|A") == "CUMPLE" and V_(r, "P1|K|VIIRS375|B") == "CUMPLE"

# Run real de Nevados de Chillan
dn = TMP / "ndc"; shutil.rmtree(dn, ignore_errors=True); (dn / "logs").mkdir(parents=True)
for n in ("C0", "F", "K"):
    shutil.copytree(NDC / E.BRAZOS[n], dn / E.BRAZOS[n])
    shutil.copy(NDC / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS[n]), dn / "logs")
shutil.copytree(NDC / E.BRAZOS["C0"], dn / E.BRAZOS["G"])
(dn / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS["G"])).write_text(
    (dn / "logs" / ("%s_NevadosDeChillan.log" % E.BRAZOS["C0"])).read_text(encoding="utf-8").replace(E.BRAZOS["C0"], E.BRAZOS["G"]), encoding="utf-8")
rr = subprocess.run([sys.executable, str(AQUI / "evaluar_fk.py"), "--ventana", "V1", "--raiz", str(dn), "--logs", str(dn / "logs"), "--out", str(dn / "res.json"),
                     "--tmp", str(dn / "tmp"), "--vols", "NevadosDeChillan", "--desde", "2026-09-14", "--hasta", "2026-10-07",
                     "--ref", str(RAIZ / "experiments" / "_s150_ndc" / "_congelado_ndc")], capture_output=True, text=True, encoding="utf-8")
(TMP / "ndc.txt").write_text(rr.stdout + "\n" + rr.stderr, encoding="utf-8")
r = json.loads((dn / "res.json").read_text(encoding="utf-8")) if (dn / "res.json").exists() else {}
suma = {n: sum(r.get("suma", {}).get("%s|%s|A" % (n, s), {}).get("total", -999) for s in E.SENS) for n in ("C0", "F", "K")}
print("ndc: suma total lectura A", suma)
chk["ndc: suma de errores C0 52, F 7, K 7 (verificador de #796)"] = suma == {"C0": 52, "F": 7, "K": 7}
chk["ndc: controles OK y P1 VIIRS CUMPLE en F y K"] = r.get("controles_ok") is True and all(V_(r, "P1|%s|%s|A" % (X, s)) == "CUMPLE" for X in "FK" for s in ("VIIRS375", "VIIRS750"))
chk["ndc: K recupera la MODIS del 2026-10-01 08:35"] = "recuperada (C0 no la publica): NevadosDeChillan|MODIS|2026-10-01 08:35" in rr.stdout

rc = subprocess.run([sys.executable, str(AQUI / "evaluar_fk.py"), "--combinar", str(NULO), str(VETO)], capture_output=True, text=True, encoding="utf-8")
(TMP / "combinar.txt").write_text(rc.stdout + rc.stderr, encoding="utf-8")
chk["combinar: nulo y veto -> K NO CUMPLE"] = "K lectura A: NO CUMPLE" in rc.stdout

print("== RESUMEN (salida completa de cada caso en %s)" % TMP)
for k, v in chk.items():
    print("  ", "OK   " if v else "FALLA", k)
print("%d de %d" % (sum(chk.values()), len(chk)))
sys.exit(0 if all(chk.values()) else 1)
