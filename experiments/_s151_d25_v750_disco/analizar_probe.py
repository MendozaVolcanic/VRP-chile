# -*- coding: utf-8 -*-
"""S151 (loop 1.5): lee la salida del probe D25 V750 y aplica el criterio pre-registrado. Sin red.

CRITERIO (escrito antes de cualquier corrida del probe; misma forma que el de MODIS en
docs/AUDIT_S149.md Fase 3: "la tasa con alerta supera a la tasa sin alerta con intervalos que no se
crucen"). Para cada variante (a, b):
  rescate  = alertas en cero (28) que pasan a publicar con el predicado del tablero.
  costo    = negativos en cero de S149 (268) que pasan a publicar.
  VALE EL A/B si el límite inferior de Wilson 95 % de rescate/28 supera al límite superior de
  costo/268. Si los intervalos se cruzan, el fondo por vecinos publica igual con alerta que sin ella
  y el A/B no se gasta.
  Además se reporta el cociente costo/rescate (S149 lo acotó en ~10 falsas por alerta como techo).
VALIDEZ: el resultado sólo se interpreta si el control C-P1 del probe pasa en >= 90 % de las pasadas
y los brazos a y b llamaron al fondo por vecinos (si un brazo encendido nunca lo llamó, no midió D25).

AUTOPRUEBA (`--autoprueba`, corre local y sin probe): fabrica salidas con los records persistidos
(control = record tal cual; brazo a = sólo las alertas con 0,05 MW; brazo b = todas con 0,05 MW) y
exige que el análisis diga VALE para a y NO VALE para b. Si no, el analizador está roto.
USO: python analizar_probe.py [--out DIR] | --autoprueba
"""
import argparse
import collections
import copy
import io
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))
import banco_paridad as bp  # noqa: E402

C1P_MIN = 0.90


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def evaluar(filas):
    inner = bp.inner_desde_html()
    s149 = json.loads((HERE / "lista_268_s149.json").read_text(encoding="utf-8"))
    claves268 = {tuple(k) for k in s149["negativos"]}
    ok = [f for f in filas if f.get("ok")]
    casos, idx = [], []
    for i, f in enumerate(ok):
        for brazo in ("control", "a", "b"):
            r = f[brazo]["record"]
            casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, inner[f["volcan"]]])
            idx.append((i, brazo))
    res = bp.correr_node(casos) if casos else []
    pub = collections.defaultdict(dict)
    for (i, brazo), p in zip(idx, res):
        pub[i][brazo] = p[4]
    out = {"pasadas": len(filas), "con_tres_brazos": len(ok),
           "control_p1": sum(1 for f in ok if f.get("control_p1")),
           "llamadas_fondo_por_brazo": {b: sum(len(f[b].get("llamadas_fondo") or []) for f in ok) for b in ("control", "a", "b")}}
    out["valido"] = (len(ok) > 0 and out["control_p1"] >= C1P_MIN * len(ok)
                     and out["llamadas_fondo_por_brazo"]["control"] == 0
                     and out["llamadas_fondo_por_brazo"]["a"] > 0 and out["llamadas_fondo_por_brazo"]["b"] > 0)
    for brazo in ("a", "b"):
        r = {}
        for clase in ("neg_cero", "alerta_cero", "control_publica"):
            sel = [i for i, f in enumerate(ok) if f["clase"] == clase
                   and (clase != "neg_cero" or (f["volcan"], f["pasada_utc"], f["sensor"]) in claves268)]
            mw = [((ok[i][brazo]["record"].get("primary_cluster") or {}).get("vrp_mw") or 0) for i in sel]
            gan = [m for m in mw if m > 0]
            r[clase] = {"n": len(sel), "publican_control": sum(pub[i]["control"] for i in sel),
                        "publican_brazo": sum(pub[i][brazo] for i in sel),
                        "con_magnitud": len(gan),
                        "mw_mediana": statistics.median(gan) if gan else None,
                        "mw_p90": sorted(gan)[int(0.9 * (len(gan) - 1))] if gan else None,
                        "mw_max": max(gan) if gan else None,
                        "por_volcan_publican": dict(collections.Counter(ok[i]["volcan"] for i in sel if pub[i][brazo]))}
        resc, cost = r["alerta_cero"], r["neg_cero"]
        wr = wilson(resc["publican_brazo"] - resc["publican_control"], resc["n"])
        wc = wilson(cost["publican_brazo"] - cost["publican_control"], cost["n"])
        r["wilson_rescate"], r["wilson_costo"] = wr, wc
        r["costo_por_alerta"] = ((cost["publican_brazo"] - cost["publican_control"])
                                 / max(1, resc["publican_brazo"] - resc["publican_control"]))
        r["veredicto"] = "VALE EL A/B" if wr[0] > wc[1] else "NO VALE EL A/B"
        out[brazo] = r
    return out


def autoprueba():
    lista = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    recs = {}
    for vol in {f["volcan"] for f in lista}:
        for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
            recs[(vol, r["datetime_utc"], r["sensor"])] = r
    filas = []
    for f in lista:
        r = recs[(f["volcan"], f["pasada_utc"], f["sensor"])]
        ctrl = copy.deepcopy(r)
        a, b = copy.deepcopy(r), copy.deepcopy(r)
        if f["clase"] == "alerta_cero":
            a["primary_cluster"]["vrp_mw"] = 0.05
            a["vrp_mw"] = max(0.05, a.get("vrp_mw") or 0)
        if f["clase"] in ("alerta_cero", "neg_cero"):
            b["primary_cluster"]["vrp_mw"] = 0.05
            b["vrp_mw"] = max(0.05, b.get("vrp_mw") or 0)
        filas.append({**f, "ok": True, "control_p1": True,
                      "control": {"record": ctrl, "llamadas_fondo": []},
                      "a": {"record": a, "llamadas_fondo": [{}]}, "b": {"record": b, "llamadas_fondo": [{}]}})
    o = evaluar(filas)
    ok = (o["valido"] and o["a"]["veredicto"] == "VALE EL A/B" and o["b"]["veredicto"] == "NO VALE EL A/B"
          and o["a"]["alerta_cero"]["publican_brazo"] == 28 and o["a"]["neg_cero"]["publican_brazo"] == 0
          and o["b"]["neg_cero"]["publican_brazo"] == 268)
    print(json.dumps({"autoprueba_ok": ok, "a": o["a"]["veredicto"], "b": o["b"]["veredicto"],
                      "a_rescate": o["a"]["alerta_cero"]["publican_brazo"], "a_costo": o["a"]["neg_cero"]["publican_brazo"],
                      "b_costo": o["b"]["neg_cero"]["publican_brazo"], "n_neg_268": o["b"]["neg_cero"]["n"],
                      "control_publica_en_control": o["a"]["control_publica"]["publican_control"],
                      "control_publica_n": o["a"]["control_publica"]["n"]}, indent=1, ensure_ascii=False))
    return ok


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args()
    if a.autoprueba:
        sys.exit(0 if autoprueba() else 2)
    filas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.out).rglob("*.json"))]
    o = evaluar(filas)
    (HERE / "resultado_probe.json").write_text(json.dumps(o, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(o, indent=1, ensure_ascii=False))
    if not o["valido"]:
        print("INDECIDIBLE: el control C-P1 o el cableado de los brazos falló", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
