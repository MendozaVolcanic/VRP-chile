# -*- coding: utf-8 -*-
"""Controles del segundo instrumento: si coincide con el evaluador, ¿coincide por la razon correcta?

1. Sensibilidad: pareo a +-60 s y +-300 s; noche por solar_zenith_deg del record en vez de la NOAA.
2. Filas de la referencia que el normalizador de nombres descarta (tienen que ser 0).
3. Atribucion por guarda: en los negativos limpios VIIRS 375 que C0 publica y K no, ¿que guarda del
   predicado cae en K? Si K "callara" por un cambio de esquema (sin primary_cluster, por ejemplo) y no
   por deteccion, aca se veria.
4. Control negativo del predicado: sin isThermalArtifact el conteo tiene que cambiar (el predicado
   esta vivo y no es una constante).
"""
import collections
import csv
import json
import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import segundo_instrumento as S  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

JS_GUARDAS = S.JS.replace("""const out = casos.map(([r, inner]) => {
  if (!isSummitDetection(r)) return 0;
  if (!isValidDetection(r)) return 0;
  if (!isSensorVisible(r)) return 0;
  if (isThermalArtifact(r, inner)) return 0;
  return mirovaEqVrpDisplay(r, inner, false) > 0 ? 1 : 0;
});""", """const out = casos.map(([r, inner]) => [isSummitDetection(r) ? 1 : 0, isValidDetection(r) ? 1 : 0,
  isThermalArtifact(r, inner) ? 1 : 0, mirovaEqVrpDisplay(r, inner, false)]);""")
assert JS_GUARDAS != S.JS


def guardas(casos):
    viejo = S.JS
    S.JS = JS_GUARDAS
    try:
        return S.publica(casos)
    finally:
        S.JS = viejo


def main():
    # 2. nombres descartados
    for v in ("_congelado_v1", "_congelado_v2"):
        for f in sorted((S.PRE / v).glob("*.csv")):
            fuera = collections.Counter(r["Volcan"] for r in csv.DictReader(open(f, encoding="utf-8"))
                                        if S.norm_vol(r["Volcan"]) is None)
            print(f"nombres no reconocidos en {v}/{f.name}: {dict(fuera) or 0}")

    co, inner = S.coords(), S.inner_html()
    for nombre, cfg in S.VENTANAS.items():
        filas = [json.loads(l) for l in open(S.OUT / f"pasadas_{nombre}.jsonl", encoding="utf-8")]
        # 1b. noche por cenit del record contra la NOAA
        C0 = {}
        for vol in S.VOLS:
            recs, _ = S.cargar_brazo(cfg["raices"], S.ARMDIR["C0"], vol)
            C0.update(recs)
        malas = []
        for f in filas:
            r = C0[tuple(f["k"])]
            z = r.get("solar_zenith_deg")
            if z is not None and z < 90:
                malas.append((f["k"], z))
        print(f"{nombre}: pasadas que mi filtro NOAA llama nocturnas y el record trae cenit solar < 90: {len(malas)} {malas[:3]}")

        # 3. atribucion por guarda en negativos VIIRS 375
        K = {}
        for vol in S.VOLS:
            recs, _ = S.cargar_brazo(cfg["raices"], S.ARMDIR["K"], vol)
            K.update(recs)
        sel = [f for f in filas if f["b"] == "VIIRS375" and f["neg"] and f["pub_C0"] == 1 and f["pub_K"] == 0]
        casos = [[{kk: vv for kk, vv in K[tuple(f["k"])].items() if kk != "discarded_anomaly_pixels"},
                  inner[f["k"][0]]] for f in sel]
        g = guardas(casos)
        motivo = collections.Counter()
        esquema = collections.Counter()
        for f, (summ, val, art, disp) in zip(sel, g):
            r = K[tuple(f["k"])]
            pc = r.get("primary_cluster")
            esquema["con primary_cluster" if pc else "sin primary_cluster"] += 1
            esquema["n_anomalous_pixels>0" if (r.get("n_anomalous_pixels") or 0) > 0 else "n_anomalous_pixels=0"] += 1
            esquema["triggered_test1" if r.get("triggered_test1") else "sin test1"] += 1
            if not summ:
                motivo["no summit"] += 1
            elif not val:
                motivo["summit pero cumulo sin energia"] += 1
            elif art:
                motivo["artefacto termico"] += 1
            elif not disp > 0:
                motivo["magnitud de display 0"] += 1
            else:
                motivo["?? publica"] += 1
        print(f"{nombre}: negativos VIIRS 375 que C0 publica y K no: {len(sel)} | guarda que cae en K: {dict(motivo)} | esquema K: {dict(esquema)}")
        # y en C0, por que publicaba: cuantos con triggered_test1
        t1 = sum(1 for f in sel if C0[tuple(f["k"])].get("triggered_test1"))
        print(f"   de esas, en C0 traian triggered_test1: {t1} de {len(sel)}")

        # 4. control negativo del predicado (sin la guarda de artefacto)
        for a in ("C0", "K"):
            br = C0 if a == "C0" else K
            negs = [f for f in filas if f["b"] == "VIIRS375" and f["neg"]]
            gg = guardas([[{kk: vv for kk, vv in br[tuple(f["k"])].items() if kk != "discarded_anomaly_pixels"},
                           inner[f["k"][0]]] for f in negs])
            con = sum(1 for (s_, v_, a_, d_) in gg if s_ and v_ and not a_ and d_ > 0)
            sin = sum(1 for (s_, v_, a_, d_) in gg if v_ and not a_ and d_ > 0)
            print(f"   {a} negativos VIIRS 375 publicados: con todas las guardas {con}; sin la guarda de cumbre {sin}")

    # 1a. sensibilidad al pareo
    for tol in (60, 300):
        print(f"\n=== sensibilidad: pareo a +-{tol} s")
        viejo = S.timedelta

        class TD:
            def __new__(cls, seconds=0, **kw):
                if seconds == 120 and not kw:
                    seconds = tol
                return viejo(seconds=seconds, **kw)
        S.timedelta = TD
        try:
            for nombre, cfg in S.VENTANAS.items():
                res, _, _, _ = S.evaluar(nombre + f"_tol{tol}", dict(cfg), co, inner)
        finally:
            S.timedelta = viejo


if __name__ == "__main__":
    main()
