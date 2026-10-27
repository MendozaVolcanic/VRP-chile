# -*- coding: utf-8 -*-
"""Verificador S165 (regla de posición), 2: de qué está hecho el universo de VIIRS 375 y quiénes son las 66 SIN DATO.
Sólo lectura.

POR QUÉ. v375.py junta tres lotes (S162, S162b, S159) y mapea las clases del censo a las cuatro del informe; «resto»
dio 0 aunque el lote S162b trae 20 «control_vida». Y las 66 pasadas sin resultado ok pueden no ser al azar (si son todas
de una clase o de un volcán, el conteo de cambios está censurado ahí). Reproduce objetivos() y leer_resultados() de
v375.py sin tocar nada.
Uso: python 02_universo_v375.py  (escribe 02_universo_v375_salida.txt)
"""
import collections
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(RAIZ / "experiments/_s162_v375"))
import evaluar as E  # noqa: E402

V375 = RAIZ / "experiments/_s162_v375"
ART = {"S162": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866"),
       "S162b": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"),
       "S159": Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")}
CLASE = {"pos_prot": "protegida", "pos_bajo": "bajo1", "neg_pub": "neg_limpio", "neg_resto": "neg_limpio"}
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def objetivos():
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in E.EXCLUIDOS:
            obj[o["id"]] = {**o, "lote": "S159"}
    return obj


def main():
    obj = objetivos()
    pr("== objetivos:", len(obj))
    pr("   por lote y clase del censo:", dict(collections.Counter((o["lote"], o.get("clase")) for o in obj.values())))
    pr("   por lote, lab y protegida:", dict(collections.Counter((o["lote"], o.get("lab"), o.get("protegida"))
                                                                for o in obj.values())))
    pr("   clase mapeada:", dict(collections.Counter(CLASE.get(o.get("clase"), "resto") for o in obj.values())))
    pr("   S159 sin clave 'clase':", sum(1 for o in obj.values() if o["lote"] == "S159" and "clase" not in o))
    res = {}
    for lote, art in ART.items():
        for i, r in E.leer_resultados(art).items():
            if i in obj and obj[i]["lote"] == lote:
                res[i] = r
    sin = [o for i, o in obj.items() if res.get(i) is None or res[i].get("estado") != "ok"]
    pr(f"\n== sin resultado ok: {len(sin)}")
    pr("   por lote y clase:", dict(collections.Counter((o["lote"], o.get("clase")) for o in sin)))
    pr("   por volcán:", dict(collections.Counter(o["volcan"] for o in sin)))
    pr("   por estado:", dict(collections.Counter((res[o["id"]] or {}).get("estado", "sin_resultado")
                                                  if o["id"] in res else "sin_resultado" for o in sin)))
    pr("   protegidas sin resultado:", [(o["id"], o["volcan"], o["hora_utc"], o.get("mirova_vrp")) for o in sin
                                       if o.get("lab") == "pos" and o.get("protegida")])
    con = [o for i, o in obj.items() if i not in {s["id"] for s in sin}]
    sin_grilla = sum(1 for o in con if E.grilla_npz(ART[o["lote"]], o["id"]) is None)
    pr("   con resultado ok pero sin grilla guardada:", sin_grilla)
    pr("\n== cobertura de las clases del censo contra la población completa de S159 (VIIRS 375)")
    pob = json.loads((RAIZ / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    pob = [p for p in pob if p["b"] == "VIIRS375" and p["hora_utc"][:10] not in E.EXCLUIDOS]
    pr("   población VIIRS 375 (sin excluidos):", len(pob), dict(collections.Counter(
        ("pos_prot" if p["protegida"] else "pos_bajo") if p["lab"] == "pos" else ("neg_pub" if p["pub_prod"] else "neg_resto")
        for p in pob if p["decide"])), "| no deciden (sólo OCR antes del 06-13):", sum(1 for p in pob if not p["decide"]))
    pr("   muestra evaluada por clase del censo:", dict(collections.Counter(o.get("clase") for o in con)))
    (AQUI / "02_universo_v375_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
