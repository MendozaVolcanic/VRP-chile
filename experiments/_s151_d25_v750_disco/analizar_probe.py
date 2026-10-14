# -*- coding: utf-8 -*-
"""S151 (loop 1.5): lee la salida del probe D25 V750 y aplica el criterio pre-registrado. Sin red.

CRITERIO (escrito antes de cualquier corrida del probe; corregido por el verificador de #790 antes de
despachar). Manda el "Criterio de victoria de la réplica" de docs/MISSION.md:
  Regla 1: si un brazo APAGA una alerta protegida (alerta de MIROVA con VRP de la pasada >= 1 MW, lectura
           A) que el control publica, el veredicto es NO VALE, sin importar lo demás. Se mira en las
           clases `control_publica` y `protegida_publica` de pasadas.json.
  Regla 2: las 28 alertas en cero son todas "Muy Bajo" (bajo 1 MW), así que una alerta rescatada y una
           publicación de más pesan IGUAL y se cuentan en CASOS, no en tasas. Por pasada se cuentan las
           transiciones respecto del control (publica en el brazo y no en el control), así que el conteo
           nunca sale negativo:
             rescate = alertas en cero (28) que el brazo hace publicar.
             costo   = de los 268 negativos de S149, los que el brazo hace publicar.
           VALE sólo si  límite superior Wilson 95 % (costo/268) x 268  <  límite inferior Wilson 95 %
           (rescate/28) x 28: aun en el peor caso estadístico, los errores que se agregan son menos que
           los que se quitan. Con 28 rescatadas el límite inferior es ~24,6 casos, así que tolera a lo
           más unos 17 negativos nuevos.
VALIDEZ (si falla, el resultado es INDECIDIBLE y no se interpreta):
  - cobertura completa: todas las pasadas de pasadas.json presentes y con los tres brazos (A108);
  - control C-P1 del probe en >= 90 % de las pasadas;
  - el control no llamó nunca al fondo por vecinos y cada brazo encendido sí lo llamó (A118).
LO QUE NO MIDE: la magnitud rescatada contra la de MIROVA (regla 3) ni la posición (A107); las 27
pasadas de rutina en noches con alerta (techo.json). Ver README.

AUTOPRUEBA (`--autoprueba`, local, sin probe): fabrica salidas desde los records persistidos y exige
  a  sólo las 28 alertas con 0,05 MW                      -> VALE
  b  las 28 alertas y los 271 negativos con 0,05 MW       -> NO VALE
  c  las 28 alertas y 225 de los 268 negativos con 0,05   -> NO VALE (con el criterio viejo de tasas: VALE)
  d  como a, pero apaga una alerta protegida del control  -> NO VALE (regla 1)
  e  como a, con una pasada menos                         -> INDECIDIBLE (cobertura)
  f  wilson con k negativo o mayor que n no se cae        -> intervalo dentro de [0, 1]
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
PROTEGIDA_MW = 1.0
CLASES_CONTROL = ("control_publica", "protegida_publica")


def wilson(k, n, z=1.96):
    """Intervalo de Wilson 95 %. k se recorta a [0, n]: un conteo neto negativo no tumba el análisis."""
    if n <= 0:
        return (0.0, 1.0)
    k = min(max(k, 0), n)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _clave(f):
    return (f["volcan"], f["pasada_utc"], f["sensor"])


def evaluar(filas, esperadas, brazos=("a", "b")):
    """`esperadas`: la lista de pasadas.json; la cobertura se mide contra ella."""
    inner = bp.inner_desde_html()
    s149 = json.loads((HERE / "lista_268_s149.json").read_text(encoding="utf-8"))
    claves268 = {tuple(k) for k in s149["negativos"]}
    ok = [f for f in filas if f.get("ok") and all("record" in (f.get(b) or {}) for b in ("control",) + tuple(brazos))]
    casos, idx = [], []
    for i, f in enumerate(ok):
        for brazo in ("control",) + tuple(brazos):
            r = f[brazo]["record"]
            casos.append([{k: r.get(k) for k in bp.CAMPOS_JS}, inner[f["volcan"]]])
            idx.append((i, brazo))
    res = bp.correr_node(casos) if casos else []
    pub = collections.defaultdict(dict)
    for (i, brazo), p in zip(idx, res):
        pub[i][brazo] = p[4]
    presentes = {_clave(f) for f in ok}
    faltan = sorted(map(list, {_clave(f) for f in esperadas} - presentes))
    out = {"pasadas_esperadas": len(esperadas), "pasadas_leidas": len(filas), "con_tres_brazos": len(ok),
           "faltan": faltan[:20], "n_faltan": len(faltan),
           "control_p1": sum(1 for f in ok if f.get("control_p1")),
           "llamadas_fondo_por_brazo": {b: sum(len(f[b].get("llamadas_fondo") or []) for f in ok)
                                        for b in ("control",) + tuple(brazos)}}
    llam = out["llamadas_fondo_por_brazo"]
    out["valido"] = (len(ok) > 0 and len(faltan) == 0 and len(filas) == len(ok)
                     and out["control_p1"] >= C1P_MIN * len(ok)
                     and llam["control"] == 0 and all(llam[b] > 0 for b in brazos))
    for brazo in brazos:
        r = {}
        for clase in ("neg_cero", "alerta_cero") + CLASES_CONTROL:
            sel = [i for i, f in enumerate(ok) if f["clase"] == clase
                   and (clase != "neg_cero" or _clave(f) in claves268)]
            mw = [((ok[i][brazo]["record"].get("primary_cluster") or {}).get("vrp_mw") or 0) for i in sel]
            gan = sorted(m for m in mw if m > 0)
            r[clase] = {"n": len(sel), "publican_control": sum(pub[i]["control"] for i in sel),
                        "publican_brazo": sum(pub[i][brazo] for i in sel),
                        "enciende": sum(1 for i in sel if pub[i][brazo] and not pub[i]["control"]),
                        "apaga": sum(1 for i in sel if pub[i]["control"] and not pub[i][brazo]),
                        "con_magnitud": len(gan),
                        "mw_mediana": statistics.median(gan) if gan else None,
                        "mw_p90": gan[int(0.9 * (len(gan) - 1))] if gan else None,
                        "mw_max": gan[-1] if gan else None,
                        "por_volcan_enciende": dict(collections.Counter(
                            ok[i]["volcan"] for i in sel if pub[i][brazo] and not pub[i]["control"]))}
        protegidas_apagadas = [list(_clave(ok[i])) for i, f in enumerate(ok)
                               if f["clase"] in CLASES_CONTROL and (f.get("mirova_vrp_alerta_mw") or 0) >= PROTEGIDA_MW
                               and pub[i]["control"] and not pub[i][brazo]]
        rescate, costo = r["alerta_cero"]["enciende"], r["neg_cero"]["enciende"]
        n_a, n_n = r["alerta_cero"]["n"], r["neg_cero"]["n"]
        rescate_inf = wilson(rescate, n_a)[0] * n_a
        costo_sup = wilson(costo, n_n)[1] * n_n
        r.update({"rescate_casos": rescate, "costo_casos": costo,
                  "rescate_limite_inferior_casos": round(rescate_inf, 2),
                  "costo_limite_superior_casos": round(costo_sup, 2),
                  "protegidas_apagadas": protegidas_apagadas})
        if protegidas_apagadas:
            r["veredicto"] = "NO VALE EL A/B (regla 1: apaga una alerta protegida)"
        elif costo_sup < rescate_inf:
            r["veredicto"] = "VALE EL A/B"
        else:
            r["veredicto"] = "NO VALE EL A/B (regla 2: agrega tantos errores como quita)"
        out[brazo] = r
    return out


def autoprueba():
    lista = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    claves268 = {tuple(k) for k in json.loads((HERE / "lista_268_s149.json").read_text(encoding="utf-8"))["negativos"]}
    recs = {}
    for vol in {f["volcan"] for f in lista}:
        for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
            recs[(vol, r["datetime_utc"], r["sensor"])] = r
    neg268 = sorted(_clave(f) for f in lista if f["clase"] == "neg_cero" and _clave(f) in claves268)
    con225 = set(neg268[:225])
    protegida = next(_clave(f) for f in lista if f["clase"] in CLASES_CONTROL
                     and (f.get("mirova_vrp_alerta_mw") or 0) >= PROTEGIDA_MW)

    def subir(r):
        r["primary_cluster"]["vrp_mw"] = 0.05
        r["vrp_mw"] = max(0.05, r.get("vrp_mw") or 0)

    def apagar(r):
        r["primary_cluster"]["vrp_mw"] = 0.0
        r["vrp_mw"] = 0.0

    filas = []
    for f in lista:
        k = _clave(f)
        r = recs[k]
        brazos = {b: copy.deepcopy(r) for b in ("control", "a", "b", "c", "d")}
        if f["clase"] == "alerta_cero":
            for b in ("a", "b", "c", "d"):
                subir(brazos[b])
        if f["clase"] == "neg_cero":
            subir(brazos["b"])
            if k in con225:
                subir(brazos["c"])
        if k == protegida:
            apagar(brazos["d"])
        filas.append({**f, "ok": True, "control_p1": True,
                      **{b: {"record": brazos[b], "llamadas_fondo": [] if b == "control" else [{}]} for b in brazos}})
    o = evaluar(filas, lista, brazos=("a", "b", "c", "d"))
    o_e = evaluar(filas[1:], lista, brazos=("a",))
    w_neg, w_sobre = wilson(-3, 28), wilson(40, 28)
    casos = {
        "a_vale": o["a"]["veredicto"] == "VALE EL A/B",
        "a_conteos": (o["a"]["rescate_casos"], o["a"]["costo_casos"]) == (28, 0),
        "b_no_vale": o["b"]["veredicto"].startswith("NO VALE"),
        "c_28_con_225_no_vale": o["c"]["veredicto"].startswith("NO VALE EL A/B (regla 2")
                                and (o["c"]["rescate_casos"], o["c"]["costo_casos"]) == (28, 225),
        "d_regla_1": o["d"]["veredicto"].startswith("NO VALE EL A/B (regla 1") and o["d"]["protegidas_apagadas"] == [list(protegida)],
        "e_cobertura": o["valido"] and not o_e["valido"] and o_e["n_faltan"] == 1,
        "f_wilson_borde": 0.0 <= w_neg[0] <= w_neg[1] <= 1.0 and 0.0 <= w_sobre[0] <= w_sobre[1] <= 1.0,
    }
    # el criterio viejo (tasas con intervalos que no se cruzan) daba VALE al caso c: se deja constancia
    viejo_c = wilson(28, 28)[0] > wilson(225, 268)[1]
    ok = all(casos.values()) and viejo_c
    print(json.dumps({"autoprueba_ok": ok, "casos": casos, "criterio_viejo_daba_vale_al_caso_c": viejo_c,
                      "veredictos": {b: o[b]["veredicto"] for b in ("a", "b", "c", "d")},
                      "c_limites_casos": {"rescate_inf": o["c"]["rescate_limite_inferior_casos"],
                                          "costo_sup": o["c"]["costo_limite_superior_casos"]},
                      "a_limites_casos": {"rescate_inf": o["a"]["rescate_limite_inferior_casos"],
                                          "costo_sup": o["a"]["costo_limite_superior_casos"]},
                      "protegida_usada": list(protegida)}, indent=1, ensure_ascii=False))
    return ok


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--autoprueba", action="store_true")
    a = ap.parse_args()
    if a.autoprueba:
        sys.exit(0 if autoprueba() else 2)
    esperadas = json.loads((HERE / "pasadas.json").read_text(encoding="utf-8"))
    filas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.out).rglob("*.json"))]
    o = evaluar(filas, esperadas)
    (HERE / "resultado_probe.json").write_text(json.dumps(o, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(o, indent=1, ensure_ascii=False))
    if not o["valido"]:
        print("INDECIDIBLE: cobertura incompleta, control C-P1 o cableado de los brazos", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
