# -*- coding: utf-8 -*-
"""S162 MODIS negativos, paso 2: extrae del lote S159 (run 39712862945) las filas por pasada de MODIS, variante
`fisica`, con el MISMO codigo de lectura de S159 (experiments/_s159/portes/04_analizar.py: record_port,
dist_centroide, slim y banco_paridad.correr_node, el predicado del tablero ejecutado con node).

POR QUE. La regla de decision del lote nuevo (PREREGISTRO.md §5) suma dos cosas: el DeltaE de los estratos que S159
ya midio (pos_bajo y neg_pub; pos_prot entra solo por R1) y lo que el port encienda en neg_resto. Para que la
incertidumbre de la primera parte salga de un bootstrap reproducible, y no de una normal ajustada al intervalo
impreso, hacen falta las filas por pasada (clase, peso, K publica, port publica). Este script las congela ANTES de
correr el lote nuevo.

Control (si falla, no se escribe nada): las filas tienen que reproducir las cuentas de 04_analizar_salida.txt de
S159 en MODIS fisica: R1 0 de 48, recall 89 de 92 (K 80), protegidas 50 de 50, bajo 39 de 42 (K 32), negativos 2 de
57 con 0 encendidos y 18 apagados, DeltaE -44,0.

Uso: python -I 02_filas_lote_s159.py --raiz <arbol del commit 0e18e1053 con 04_analizar.py y run_39712862945/>
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    a = ap.parse_args()
    portes = Path(a.raiz) / "experiments/_s159/portes"
    spec = importlib.util.spec_from_file_location("analizar_s159", portes / "04_analizar.py")
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    B = A.B
    obj = {o["id"]: o for o in json.loads((portes / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted((portes / "run_39712862945").glob("resultados_MODIS_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    ok = sorted(i for i, r in res.items() if r.get("estado") == "ok" and r.get("port") and obj[i]["b"] == "MODIS")
    print("MODIS con resultado ok:", len(ok), "de", sum(o["b"] == "MODIS" for o in obj.values()))
    inner = B.inner_desde_html()
    casos = []
    for i in ok:
        o = obj[i]
        p = res[i]["port"]["fisica"]
        if p and p.get("npix"):
            p["_dcen"] = A.dist_centroide(p, o["grilla"])
        rp = A.record_port(p, inner[o["volcan"]], o["sensor"])
        casos.append([A.slim({k: x for k, x in rp.items() if not k.startswith("_")}), inner[o["volcan"]]])
    pubs = B.correr_node(casos)
    filas = []
    for i, p in zip(ok, pubs):
        o = obj[i]
        pf = res[i]["port"]["fisica"]
        filas.append({"i": i, "c": o["clase"], "w": o["peso"], "K": bool(o["pub_prod"]), "X": bool(p[4]),
                      "vol": o["volcan"], "h": o["hora_utc"], "part": bool(o.get("partida")),
                      "motivo_vacio": pf.get("motivo_vacio"), "port_estado": res[i].get("port_estado")})

    def cuenta(c):
        s = [x for x in filas if x["c"] in c]
        return sum(x["X"] for x in s), sum(x["K"] for x in s), len(s)

    prot = [x for x in filas if x["c"] == "pos_prot"]
    r1 = sum(x["K"] and not x["X"] for x in prot)
    neg = [x for x in filas if x["c"] in ("neg_pub", "neg_resto")]
    enc = sum(x["X"] and not x["K"] for x in neg)
    apa = sum(x["K"] and not x["X"] for x in neg)
    bp = sum(x["w"] for x in filas if x["c"] == "pos_bajo" and x["K"] and not x["X"])
    bg = sum(x["w"] for x in filas if x["c"] == "pos_bajo" and not x["K"] and x["X"])
    ne = sum(x["w"] for x in neg if x["X"] and not x["K"])
    na = sum(x["w"] for x in neg if x["K"] and not x["X"])
    de = (bp - bg) + (ne - na)
    print("R1 protegidas que K publica y el port no:", r1, "de", sum(x["K"] for x in prot))
    print("recall todas (port, K, n):", cuenta(("pos_prot", "pos_bajo")), "| prot:", cuenta(("pos_prot",)),
          "| bajo:", cuenta(("pos_bajo",)))
    print("negativos (port, K, n):", cuenta(("neg_pub", "neg_resto")), "encendidos", enc, "apagados", apa)
    print(f"DeltaE = (bajo perdidas {bp:.1f} - ganadas {bg:.1f}) + (neg encendidos {ne:.1f} - apagados {na:.1f}) "
          f"= {de:+.2f}")
    print("neg_resto: n", sum(x["c"] == "neg_resto" for x in filas), "port publica",
          sum(x["X"] for x in filas if x["c"] == "neg_resto"), "| escena invalida en neg_resto:",
          [(x["i"], x["vol"], x["h"]) for x in filas if x["c"] == "neg_resto" and x["motivo_vacio"] == "escena_invalida"])
    esperado = {"r1": 0, "todas": (89, 80, 92), "prot": (50, 48, 50), "bajo": (39, 32, 42), "neg": (2, 20, 57),
                "enc": 0, "apa": 18, "de": -44.0}
    medido = {"r1": r1, "todas": cuenta(("pos_prot", "pos_bajo")), "prot": cuenta(("pos_prot",)),
              "bajo": cuenta(("pos_bajo",)), "neg": cuenta(("neg_pub", "neg_resto")), "enc": enc, "apa": apa,
              "de": round(de, 1)}
    for k in esperado:
        print(f"  control {k}: S159 {esperado[k]} | ahora {medido[k]} -> {'IGUAL' if esperado[k] == medido[k] else 'DISTINTO'}")
    assert esperado == medido, "las filas no reproducen 04_analizar_salida.txt de S159: no se escriben"
    out = AQUI / "filas_lote_s159_modis_fisica.json"
    out.write_bytes(json.dumps({"fuente": "run 39712862945, variante fisica, predicado del tablero con node "
                                          "(04_analizar.py de S159)", "filas": filas},
                               ensure_ascii=False, indent=0).encode("utf-8"))
    print("escrito", out.name, len(filas), "filas")


if __name__ == "__main__":
    main()
