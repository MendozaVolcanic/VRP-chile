# -*- coding: utf-8 -*-
"""S150. Prueba de medir_ndc.py (version 3) ANTES de despachar: un nulo y un control positivo por cada
defecto que el evaluador dice detectar, sobre los records de produccion de Nevados de Chillan y la
referencia congelada (verificadores del pre-registro, H4 de la v1 y N3/N9 de la v2).

Los brazos se fabrican desde produccion imitando la huella de su flag en los records (sin Test 1: ningun
triggered_test1; sin tope: ningun d9_capped; etiqueta: distance_class MODIS desde el cumulo) y con su linea
FLAGS_BRAZO en el log, igual que la escribe el workflow.

  NULO: todos bien cableados. Esperado: controles y cableado OK, P1 a P5 CUMPLE.
  P1:   F oculta la alerta VIIRS 375 del 2026-09-29 05:18 (5,73 MW)   -> P1 VETADO
  P2:   B oculta la misma                                               -> P2 VETADO
  P4:   KE sin magnitud en la MODIS del 2026-10-01 08:35                -> P4_KE FALLA
  P5:   T0 publica una pasada que C0 tiene topada                       -> P5_T0 FALLA
  FLAG: el log de F dice que leyo la conectiva min                      -> F mal cableado, P1 INDECIDIBLE
  TOPE: T0 con los d9_capped de produccion                              -> T0 mal cableado
  ETIQ: E sin reetiquetar                                               -> E mal cableado

Uso: python probar_medir_ndc.py <TMP>   (escribe solo en <TMP>; salida completa en <TMP>/<caso>.txt)
"""
import copy, json, shutil, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
# medir_ndc ya envuelve sys.stdout en utf-8 al importarse; envolverlo dos veces cierra el flujo.
sys.path.insert(0, str(AQUI)); import medir_ndc as m  # noqa: E402
TMP = Path(sys.argv[1]); TMP.mkdir(parents=True, exist_ok=True)
PROD = json.load(open(RAIZ / "data" / "mirova_equivalent" / "NevadosDeChillan.json", encoding="utf-8"))
INNER = m.bp.inner_desde_html()[m.VOL]
FUERTE_V375, MODIS_0835 = "2026-09-29 05:18", "2026-10-01 08:35"


def fabricar(nombre):
    test1, _, _, etiqueta, tope = m.DECLARADO[nombre]
    d = copy.deepcopy(PROD)
    for r in d["records"]:
        pc = r.get("primary_cluster") or {}
        if not test1:
            r["triggered_test1"] = False
        if tope is None and pc.get("d9_capped"):
            pc["d9_capped"] = False
        if etiqueta and r.get("sensor", "").startswith("MODIS") and r.get("distance_class") is not None and pc.get("centroid_dist_km") is not None:
            r["distance_class"] = "summit" if pc["centroid_dist_km"] <= INNER else "far"
    return d


def registro(d, t, v375=False, modis=False):
    rs = [r for r in d["records"] if r.get("datetime_utc") == t and (
        (v375 and r["sensor"].startswith("VIIRS") and not r["sensor"].endswith("_750")) or (modis and r["sensor"].startswith("MODIS")))]
    assert len(rs) == 1, (t, len(rs))
    return rs[0]


def log(nombre, flags=None):
    dec = dict(zip(m.CLAVES_FLAGS, m.DECLARADO[nombre]))
    if flags:
        dec.update(flags)
    dec.update(PROFILE_NAME=m.BRAZOS[nombre], DATA_SUBDIR=m.BRAZOS[nombre])
    return "FLAGS_BRAZO " + json.dumps(dec) + "\n(salida del pipeline)\n"


def correr(caso, brazos, logs):
    raiz, dl = TMP / caso / "raiz", TMP / caso / "logs"
    shutil.rmtree(TMP / caso, ignore_errors=True)
    for n, perfil in m.BRAZOS.items():
        (raiz / perfil).mkdir(parents=True)
        json.dump(brazos[n], open(raiz / perfil / (m.VOL + ".json"), "w", encoding="utf-8"))
    dl.mkdir(parents=True)
    for n, perfil in m.BRAZOS.items():
        (dl / ("%s_%s.log" % (perfil, m.VOL))).write_text(logs[n], encoding="utf-8")
    out = TMP / caso / "res.json"
    r = subprocess.run([sys.executable, str(AQUI / "medir_ndc.py"), "--raiz", str(raiz), "--logs", str(dl), "--ref", str(AQUI / "_congelado_ndc"),
                        "--out", str(out), "--tmp", str(TMP / caso / "tmp")], capture_output=True, text=True, encoding="utf-8")
    (TMP / (caso + ".txt")).write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    return json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}


def base():
    return {n: fabricar(n) for n in m.BRAZOS}, {n: log(n) for n in m.BRAZOS}


chk = {}
B, L = base(); nulo = correr("nulo", B, L)
chk["nulo: controles generales OK"] = nulo.get("controles_ok") is True
chk["nulo: los diez brazos bien cableados"] = nulo.get("cableado") and all(nulo["cableado"].values())
chk["nulo: P1 a P5 sin falla"] = nulo.get("veredicto") and all(v in ("CUMPLE", "SIN DATO") for v in nulo["veredicto"].values()) and nulo["veredicto"].get("P5_T0") == "CUMPLE"

B, L = base(); registro(B["F"], FUERTE_V375, v375=True)["distance_class"] = "far"
chk["P1: perdida sembrada en F -> VETADO"] = correr("p1", B, L).get("veredicto", {}).get("P1") == "VETADO"

B, L = base(); registro(B["B"], FUERTE_V375, v375=True)["distance_class"] = "far"
r = correr("p2", B, L); chk["P2: perdida sembrada en B -> VETADO"] = r.get("veredicto", {}).get("P2") == "VETADO"

B, L = base(); rk = registro(B["KE"], MODIS_0835, modis=True); rk["vrp_mw"] = 0.0; rk["primary_cluster"]["vrp_mw"] = 0.0
chk["P4: KE sin la alerta MODIS 08:35 -> FALLA"] = correr("p4", B, L).get("veredicto", {}).get("P4_KE") == "FALLA"

B, L = base()
topada = next(r for r in B["C0"]["records"] if (r.get("primary_cluster") or {}).get("d9_capped") and r.get("distance_class") == "far"
              and m.DESDE <= r["datetime_utc"][:10] <= m.HASTA)
registro(B["T0"], topada["datetime_utc"], modis=topada["sensor"].startswith("MODIS"), v375=not topada["sensor"].startswith("MODIS"))["distance_class"] = "summit"
chk["P5: T0 cambia la decision en una pasada topada -> FALLA"] = correr("p5", B, L).get("veredicto", {}).get("P5_T0") == "FALLA"

B, L = base(); L["F"] = log("F", {"ENABLE_TESTS_23_PROSE_BRANCH": False})
r = correr("flag", B, L); chk["FLAG: F leyo min -> mal cableado y P1 INDECIDIBLE"] = r.get("cableado", {}).get("F") is False and r.get("veredicto", {}).get("P1") == "INDECIDIBLE"

B, L = base(); B["T0"] = copy.deepcopy(PROD)
chk["TOPE: T0 con d9_capped -> mal cableado"] = correr("tope", B, L).get("cableado", {}).get("T0") is False

B, L = base(); B["E"] = copy.deepcopy(PROD)
chk["ETIQ: E sin reetiquetar -> mal cableado"] = correr("etiq", B, L).get("cableado", {}).get("E") is False

print("== RESUMEN (salida completa de cada caso en %s)" % TMP)
for k, v in chk.items():
    print("  ", "OK  " if v else "FALLA", k)
sys.exit(0 if all(chk.values()) else 1)
