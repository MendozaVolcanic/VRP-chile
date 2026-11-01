# -*- coding: utf-8 -*-
"""Verificador: la vara VIIRS por OTROS caminos que el del autor (fuente pico = centroide 3x3 pesado), para ver si
MXD03 MAS CERCA depende de la construccion del estadistico.
  a) fuente pico_centro (centro del pixel caliente, sin 3x3)
  b) fuente cumulo (centroide del cumulo primario publicado: pc_lat/pc_lon), que SI pasa por la seleccion del pipeline
  c) nivel amplia (VIIRS publicada aunque MIROVA no haya alertado esa pasada VIIRS)
  d) solo Chillan (el volcan que no es Lascar), solo descriptivo
  e) placebo: la referencia VIIRS de OTRA alerta del mismo volcan (barajada con semilla), deberia dar dd ~ 0 si la vara
     mide algo de ESA noche; con fuente permanente (Lascar) A110 avisa que este control es ciego en parte, se informa.
Las dos preguntas: (1) si X no moviera el pico, dd = 0 en todas y el estado INDECIDIBLE; (2) si la vara estuviera
muerta (sin pasadas) da SIN VARA. Las dos salidas son distintas de MXD03 MAS CERCA.
Uso (desde la raiz del worktree): python -I experiments/_s162_mxd03/resultado/verificador/vara_alternativas.py <art>
"""
import glob
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "experiments/_s162_mxd03"))
import vara_mxd03 as VM  # noqa: E402  (a_formato_123, CENIT, sys.path de la 1.23)
import evaluar_sola as ES  # noqa: E402

ART = Path(sys.argv[1])
tabla = json.load(open(RAIZ / "experiments/_s162_mxd03/vara_viirs_mxd03.json", encoding="utf-8"))
filas = []
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    filas += [json.loads(x) for x in open(p, encoding="utf-8")]
ok = []
for f in filas:
    if f.get("tipo") == "record" and f.get("estado") == "ok":
        g = VM.a_formato_123(f)
        # para fuente "cumulo": evaluar_sola lee brazos C/M; en este arnes se llaman K/X
        g["brazos"] = {"C": f["brazos"].get("K"), "M": f["brazos"].get("X"), **{b: f["brazos"].get(b) for b in ES.NULOS}}
        ok.append(g)
le35 = [f for f in ok if f["sensor_zenith_deg"] is not None and f["sensor_zenith_deg"] <= VM.CENIT]


def resumen(nombre, v):
    print("%-40s estado=%-32s n=%s noches=%s dd_med=%s ic=%s M_mas_cerca=%s nulo_max=%s sat=%s" % (
        nombre, v.get("estado"), v.get("n"), v.get("n_noches"), v.get("dd_mediana_km"), v.get("dd_ic95"), v.get("M_mas_cerca"),
        (v.get("nulo_del_estadistico") or {}).get("max_abs_km"),
        {k: (s["n"], s["dd_mediana_km"]) for k, s in (v.get("por_satelite") or {}).items()}))


print("== caminos alternativos de la vara (cenit <= 35, el estrato que decide)")
resumen("autor: pico / estricta / pos", ES.vara(le35, tabla, "pico", "estricta", "pos"))
resumen("a) pico_centro / estricta / pos", ES.vara(le35, tabla, "pico_centro", "estricta", "pos"))
resumen("b) cumulo / estricta / pos", ES.vara(le35, tabla, "cumulo", "estricta", "pos"))
resumen("c) pico / amplia / pos", ES.vara(le35, tabla, "pico", "amplia", "pos"))
resumen("c') pico / amplia / todos", ES.vara(le35, tabla, "pico", "amplia", "todos"))
resumen("d) solo Chillan, pico/estricta/pos", ES.vara([f for f in le35 if f["volcan"] == "NevadosDeChillan"], tabla, "pico", "estricta", "pos"))
resumen("d') solo Lascar, pico/estricta/pos", ES.vara([f for f in le35 if f["volcan"] == "Lascar"], tabla, "pico", "estricta", "pos"))
print("\n== todo el cenit (descriptivo)")
resumen("pico / estricta / pos, todos", ES.vara(ok, tabla, "pico", "estricta", "pos"))
resumen("cumulo / estricta / pos, todos", ES.vara(ok, tabla, "cumulo", "estricta", "pos"))
resumen("pico / estricta / pos, cenit > 35", ES.vara([f for f in ok if f["sensor_zenith_deg"] is not None and f["sensor_zenith_deg"] > VM.CENIT], tabla, "pico", "estricta", "pos"))

print("\n== e) placebo: referencia VIIRS de otra alerta del mismo volcan (5 barajados)")
claves = {k: v for k, v in tabla["granulos"].items() if v["estricta"]["noche"]}
for sem in range(5):
    rng = random.Random(1000 + sem)
    t2 = {"granulos": {}}
    por_vol = {}
    for k, v in claves.items():
        por_vol.setdefault(k.split("|")[0], []).append(k)
    for vol, ks in por_vol.items():
        perm = ks[:]
        rng.shuffle(perm)
        for a, b in zip(ks, perm):
            t2["granulos"][a] = dict(claves[a], estricta=claves[b]["estricta"])
    resumen("placebo semilla %d" % sem, ES.vara(le35, t2, "pico", "estricta", "pos"))

print("\n== f) distancia del pico a la referencia VIIRS en cada brazo (km, medianas, <= 35)")
v = ES.vara(le35, tabla, "pico", "estricta", "pos")
import statistics
print("   |C - v| mediana %.3f | |M - v| mediana %.3f | separacion C-M mediana %.3f | perpendicular mediana %.3f | lambda mediana %s" % (
    statistics.median(g["d_C"] for g in v["granulos"]), statistics.median(g["d_M"] for g in v["granulos"]),
    v["separacion_CM_mediana_km"], v["perpendicular_mediana_km"], v["lambda_mediana"]))
print("   referencia VIIRS al ancla (km) en los 65:", "mediana %.3f" % statistics.median(
    (t["estricta"]["noche"]["n_km"] ** 2 + t["estricta"]["noche"]["e_km"] ** 2) ** 0.5
    for k, t in tabla["granulos"].items() if t["estricta"]["noche"] and any(g["clave"] == k.split("|")[1] and g["volcan"] == k.split("|")[0] for g in v["granulos"])))
