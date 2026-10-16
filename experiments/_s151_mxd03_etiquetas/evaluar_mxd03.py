# Tarea 1.17: junta los JSON por job del probe y aplica el criterio pre-registrado en README.md.
# Corre en el job "agregar" del workflow y tambien en local sobre los artefactos bajados.
# Version 2 (arreglos del verificador de #834): la vara principal es el criterio de victoria de la
# replica (docs/MISSION.md): regla 1 como compuerta (ninguna alerta protegida se pierde) y regla 2 como
# balance (bajo 1 MW, una alerta perdida y una publicacion de mas pesan igual). Los umbrales de 2 % y
# 5 % de la v1 quedan como lectura informativa de magnitud, no deciden (A115).
#
# Uso: python evaluar_mxd03.py <carpeta con los <job>.json> [--poblacion poblacion.json]
#                              [--jobs '["Lascar-1", ...]'] [--salida resumen.json]
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent

MARGEN_TRAZA_KM = 1.0    # el mismo de seleccionar_mxd03: banda = corrimiento predicho + 1 km
BANDA_FRAC = 0.10        # si mas de 10 % de los granulos se corre mas que su banda, la poblacion quedo corta
MAX_FALTAN = 0.20        # mas de 20 % de la muestra de un volcan sin medir -> INCOMPLETO
CONTROL_MAX = 0.10       # mas de 10 % del control cambia de etiqueta -> se anota
ESTRATOS_MUESTREADOS = ("A", "B_summit", "B_far", "control", "fuera")
# Lectura informativa de magnitud (v1): publicaciones movidas estimadas / publicaciones MODIS del tramo
POCO_PUB, MUCHO_PUB = 0.02, 0.05
BINES_CENIT = ((0, 20), (20, 35), (35, 50), (50, 91))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def _bin(z):
    if z is None:
        return "sin_cenit"
    for a, b in BINES_CENIT:
        if a <= z < b:
            return "%d-%d" % (a, min(b, 90))
    return "sin_cenit"


def _unir(pob, salidas):
    """Una fila por granulo de la muestra: lo que dice poblacion.json mas lo que midio el probe."""
    medidas = {}
    for s in salidas.values():
        for g in s.get("granulos", []):
            medidas[(s["volcan"], g["clave"])] = g
    filas = []
    for vol, v in pob["volcanes"].items():
        for g in v["muestra"]:
            m = medidas.get((vol, g["clave"]), {})
            filas.append(dict(g, volcan=vol, **{k: x for k, x in m.items() if k not in g}))
    return filas


def evaluar(pob, salidas, esperados=None):
    """pob: poblacion.json; salidas: {job: salida del probe}; esperados: jobs pedidos (por defecto todos)."""
    esperados = list(pob["jobs"]) if esperados is None else list(esperados)
    filas = _unir(pob, salidas)
    vol_pedidos = {pob["jobs"][j]["volcan"] for j in esperados}
    filas = [f for f in filas if f["volcan"] in vol_pedidos]
    ok = [f for f in filas if f.get("estado") == "ok"]
    motivos_incompleto = []
    faltan_jobs = [j for j in esperados if j not in salidas]
    if faltan_jobs:
        motivos_incompleto.append("faltan jobs: %s" % faltan_jobs)
    for vol in sorted(vol_pedidos):
        fv = [f for f in filas if f["volcan"] == vol]
        n_ok = sum(1 for f in fv if f.get("estado") == "ok")
        if fv and (len(fv) - n_ok) / len(fv) > MAX_FALTAN:
            motivos_incompleto.append("%s: %d de %d sin medir" % (vol, len(fv) - n_ok, len(fv)))
    prot_sin = [f["clave"] for f in filas if f["prot"] and f.get("estado") != "ok"]
    if prot_sin:
        motivos_incompleto.append("protegidas sin medir: %s" % prot_sin)
    for j in esperados:
        s = salidas.get(j)
        if s is not None and not any(g.get("cprima_igual") is not None for g in s.get("granulos", [])):
            motivos_incompleto.append("%s sin brazo C' (instrumento sin control negativo)" % j)
    cprima_mal = [f["clave"] for f in ok if f.get("cprima_igual") is False]

    def cambio(f, campo, valor=None):
        c = f["comparacion"][campo]
        return c != "igual" if valor is None else c == valor

    # ---- regla 1: compuerta sobre las protegidas (censo)
    prot = [f for f in ok if f["prot"]]
    regla1 = {"medidas": len(prot), "publicadas_C": sum(f["pub_c"] for f in prot),
              "publicadas_M": sum(f["pub_m"] for f in prot),
              "perdidas": sum(cambio(f, "pub", "1->0") for f in prot),
              "ganadas": sum(cambio(f, "pub", "0->1") for f in prot),
              "perdidas_detalle": [{"volcan": f["volcan"], "clave": f["clave"], "datetime_utc": f["datetime_utc"]}
                                   for f in prot if cambio(f, "pub", "1->0")]}

    # ---- regla 2: balance bajo 1 MW. Alertas (censo, exacto) + negativos limpios (estimados por estrato)
    alertas = [f for f in ok if f["lab"] == "pos" and not f["prot"]]
    a_perd = sum(cambio(f, "pub", "1->0") for f in alertas)
    a_gan = sum(cambio(f, "pub", "0->1") for f in alertas)
    neg = {"ganadas_est": 0.0, "perdidas_est": 0.0, "lo": 0.0, "hi": 0.0, "observadas_ganadas": 0,
           "observadas_perdidas": 0, "por_estrato": {}}
    for vol in sorted(vol_pedidos):
        N = pob["volcanes"][vol]["N"]
        for e in ESTRATOS_MUESTREADOS:
            Ne = (N.get(e) or {}).get("neg_limpio", 0)
            if not Ne:
                continue
            s = [f for f in ok if f["volcan"] == vol and f["estrato"] == e and f["lab"] == "neg_limpio"]
            kg = sum(cambio(f, "pub", "0->1") for f in s)
            kp = sum(cambio(f, "pub", "1->0") for f in s)
            n = len(s)
            gl, gh = wilson(kg, n)
            pl, ph = wilson(kp, n)
            neg["ganadas_est"] += Ne * kg / n if n else 0.0
            neg["perdidas_est"] += Ne * kp / n if n else 0.0
            neg["lo"] += Ne * gl - Ne * ph
            neg["hi"] += Ne * gh - Ne * pl
            neg["observadas_ganadas"] += kg
            neg["observadas_perdidas"] += kp
            neg["por_estrato"]["%s/%s" % (vol, e)] = {"N": Ne, "n": n, "0->1": kg, "1->0": kp}
    base = a_perd - a_gan
    delta = base + neg["ganadas_est"] - neg["perdidas_est"]
    regla2 = {"alertas_medidas": len(alertas), "alertas_perdidas": a_perd, "alertas_ganadas": a_gan,
              "negativos_limpios": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in neg.items()},
              "delta_errores": round(delta, 1),
              "delta_intervalo": [round(base + neg["lo"], 1), round(base + neg["hi"], 1)]}

    # ---- anotaciones de instrumento
    excede = [f for f in ok if f.get("corrimiento_predicho_km") is not None and f.get("desplazamiento")
              and f["desplazamiento"]["km"] > f["corrimiento_predicho_km"] + MARGEN_TRAZA_KM]
    banda_corta = bool(ok) and len(excede) / len(ok) > BANDA_FRAC
    ctrl = [f for f in ok if f["estrato"] == "control"]
    ctrl_k = sum(cambio(f, "etiqueta") for f in ctrl)
    control_cambia = bool(ctrl) and ctrl_k / len(ctrl) > CONTROL_MAX

    # ---- veredicto principal
    hubo_cambio = any(cambio(f, "pub") or cambio(f, "etiqueta") for f in ok)
    if cprima_mal:
        ver = "INVALIDO"
    elif motivos_incompleto:
        ver = "INCOMPLETO"
    elif regla1["perdidas"] > 0:
        ver = "PIERDE PROTEGIDA"
    elif banda_corta:
        ver = "BANDA CORTA"
    elif not hubo_cambio:
        ver = "SIN CAMBIO OBSERVADO"
    elif regla2["delta_intervalo"][1] < 0:
        ver = "MEJORA"
    elif regla2["delta_intervalo"][0] > 0:
        ver = "EMPEORA"
    else:
        ver = "INDETERMINADO"

    # ---- magnitud (informativa): bruto, neto, tipo de cambio y estimacion contra las publicaciones
    bruto = {"1->0": sum(cambio(f, "pub", "1->0") for f in ok), "0->1": sum(cambio(f, "pub", "0->1") for f in ok)}
    por_tipo = {"misma_deteccion_otra_etiqueta": 0, "otra_deteccion": 0}
    for f in ok:
        if cambio(f, "pub") or cambio(f, "etiqueta"):
            por_tipo["otra_deteccion" if f["comparacion"]["deteccion_cambia"] else "misma_deteccion_otra_etiqueta"] += 1
    E_pub = 0.0
    for vol in sorted(vol_pedidos):
        N = pob["volcanes"][vol]["N"]
        for e in ESTRATOS_MUESTREADOS:
            Ne = sum((N.get(e) or {}).values())
            s = [f for f in ok if f["volcan"] == vol and f["estrato"] == e and not f.get("censo")]
            cen = [f for f in ok if f["volcan"] == vol and f["estrato"] == e and f.get("censo")]
            E_pub += sum(cambio(f, "pub") for f in cen)
            resto = Ne - len([f for f in filas if f["volcan"] == vol and f["estrato"] == e and f.get("censo")])
            if s and resto > 0:
                E_pub += resto * sum(cambio(f, "pub") for f in s) / len(s)
    P_total = sum(pob["volcanes"][v].get("n_pub_tramo") or 0 for v in vol_pedidos)
    frac = E_pub / P_total if P_total else None
    if motivos_incompleto:
        nivel = "INCOMPLETO"
    elif frac is not None and frac >= MUCHO_PUB:
        nivel = "CAMBIA MUCHO"
    elif frac is not None and frac < POCO_PUB and not banda_corta:
        nivel = "CAMBIA POCO"
    else:
        nivel = "INTERMEDIO" if not banda_corta else "PISO (banda corta)"
    magnitud = {"nivel": nivel, "bruto": bruto, "neto_observado": bruto["0->1"] - bruto["1->0"],
                "por_tipo": por_tipo, "publicaciones_movidas_estimadas": round(E_pub, 1),
                "publicaciones_modis_del_tramo": P_total,
                "fraccion": None if frac is None else round(frac, 4)}

    # ---- tabla volcan x satelite x cenit
    tabla = defaultdict(lambda: {"n": 0, "etiqueta": 0, "pub": 0, "desp": [], "pred": []})
    for f in ok:
        sat = (f.get("sensor") or "?").replace("MODIS_", "")
        for clave in ((f["volcan"], sat, _bin(f.get("sensor_zenith_deg"))), ("TODOS", sat, _bin(f.get("sensor_zenith_deg")))):
            t = tabla[clave]
            t["n"] += 1
            t["etiqueta"] += cambio(f, "etiqueta")
            t["pub"] += cambio(f, "pub")
            if f.get("desplazamiento"):
                t["desp"].append(f["desplazamiento"]["km"])
            if f.get("corrimiento_predicho_km") is not None:
                t["pred"].append(f["corrimiento_predicho_km"])
    tabla_out = []
    for (vol, sat, b), t in sorted(tabla.items()):
        med = lambda xs: round(sorted(xs)[len(xs) // 2], 2) if xs else None  # noqa: E731
        tabla_out.append({"volcan": vol, "satelite": sat, "cenit": b, "n": t["n"], "cambia_etiqueta": t["etiqueta"],
                          "cambia_pub": t["pub"], "desp_mediana_km": med(t["desp"]),
                          "desp_max_km": round(max(t["desp"]), 2) if t["desp"] else None,
                          "predicho_mediana_km": med(t["pred"])})
    alertas_movidas = [{"volcan": f["volcan"], "clave": f["clave"], "datetime_utc": f["datetime_utc"],
                        "protegida": f["prot"], "vrp_ref": f.get("vrp_ref"), "pub": f["comparacion"]["pub"]}
                       for f in ok if f["lab"] == "pos" and cambio(f, "pub")]
    return {"veredicto": ver, "motivos_incompleto": motivos_incompleto, "cprima_distinto": cprima_mal,
            "regla1": regla1, "regla2": regla2, "banda_corta": banda_corta,
            "banda_excedida": {"n": len(excede), "de": len(ok)},
            "control_cambia": control_cambia, "control": {"n": len(ctrl), "cambia_etiqueta": ctrl_k},
            "c_igual_a_guardada": {"si": sum(1 for f in ok if f.get("c_igual_a_guardada")), "de": len(ok)},
            "alertas_movidas": alertas_movidas,
            "noches_con_alerta_movida": len({(a["volcan"], (a["datetime_utc"] or "")[:10]) for a in alertas_movidas}),
            "magnitud": magnitud, "tabla_volcan_satelite_cenit": tabla_out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion.json"))
    ap.add_argument("--jobs", default=None, help="lista JSON de jobs pedidos (por defecto, todos)")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args()
    pob = json.load(open(args.poblacion, encoding="utf-8"))
    salidas = {}
    for p in sorted(Path(args.carpeta).rglob("*.json")):
        d = json.load(open(p, encoding="utf-8"))
        if isinstance(d, dict) and "granulos" in d and "job" in d:
            salidas[d["job"]] = d
    esperados = json.loads(args.jobs) if args.jobs else None
    r = evaluar(pob, salidas, esperados)
    texto = json.dumps(r, indent=1, ensure_ascii=False)
    if args.salida:
        Path(args.salida).write_text(texto, encoding="utf-8")
    print("VEREDICTO:", r["veredicto"], "| motivos:", r["motivos_incompleto"] or "-",
          "| regla 1: %d protegidas medidas, %d perdidas" % (r["regla1"]["medidas"], r["regla1"]["perdidas"]),
          "| regla 2: delta %s %s" % (r["regla2"]["delta_errores"], r["regla2"]["delta_intervalo"]),
          "| banda corta:", r["banda_corta"], "| control cambia:", r["control_cambia"],
          "| magnitud:", r["magnitud"]["nivel"])
    if not salidas:
        sys.exit("no encontre salidas del probe en %s" % args.carpeta)


if __name__ == "__main__":
    main()
