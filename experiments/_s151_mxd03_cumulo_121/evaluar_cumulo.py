# Tarea 1.21: junta los JSON por job del probe y aplica el criterio pre-registrado en README.md.
# Corre en el job "agregar" del workflow y tambien en local sobre los artefactos bajados.
#
# POR QUE ASI. La vara es el criterio de victoria de la replica (docs/MISSION.md): regla 1 como
# compuerta (ninguna alerta protegida se pierde, lectura A) y regla 2 como balance (bajo 1 MW una alerta
# perdida y una publicacion de mas pesan igual). A diferencia de la 1.17, el balance suma TODOS los
# estratos de la muestra: la etiqueta desde el cumulo cambia records en cualquier estrato (el modelo de
# corrimiento no decide que entra), asi que no hay estratos "inmoviles" que excluir. Cada celda
# (volcan x estrato de la 1.17) es un muestreo uniforme de sus negativos limpios. El total de la celda
# se estima con lo medido mas (N - n) por la media medida, y su varianza con la de un valor en
# {-1, 0, +1} cuyas frecuencias de -1 y +1 se suavizan con medio conteo (para que una celda de 4
# granulos sin cambios no declare varianza cero). Las celdas medidas enteras entran exactas. La
# cobertura de ese intervalo se MIDIO con respuesta conocida (cobertura_estimador.py, A110); una
# posterior de Dirichlet de Jeffreys se probo primero y cubrio 0 de 150 veces el efecto grande, por
# eso no se usa. El intervalo de Wilson sumado por celda de la 1.17 se informa al lado.
#
# Uso: python evaluar_cumulo.py <carpeta con los <job>.json> [--jobs '["Lascar-1", ...]'] [--salida x.json]
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


AQUI = Path(__file__).resolve().parent
DIR_117 = AQUI.parent / "_s151_mxd03_etiquetas"
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(DIR_117))
sys.path.insert(0, str(AQUI.parents[1] / "scripts"))

import modelo_corrimiento as MC  # noqa: E402
from evaluar_mxd03 import wilson, _bin  # noqa: E402  (1.17)

BRAZOS = ("C", "CC", "M", "MC", "R", "RC")
CUMULO = {"C": False, "CC": True, "M": False, "MC": True, "R": False, "RC": True}
# (X, Y, nombre, que pregunta contesta). La primera es la principal.
COMPARACIONES = (
    ("MC", "C", "principal", "MxD03 + etiqueta desde el cumulo contra produccion"),
    ("CC", "C", "etiqueta", "solo la etiqueta desde el cumulo"),
    ("M", "C", "posicion_produccion", "solo MxD03 (repite la 1.17)"),
    ("MC", "CC", "posicion_cumulo", "MxD03 con la etiqueta desde el cumulo ya puesta"),
    ("RC", "C", "nulo_de_principal", "ruido + etiqueta desde el cumulo: nulo de la principal"),
    ("R", "C", "nulo_de_posicion_produccion", "ruido con la etiqueta de produccion: nulo de M contra C"),
    ("RC", "CC", "nulo_de_posicion_cumulo", "ruido con la etiqueta desde el cumulo: nulo de MC contra CC"),
    ("M", "R", "M_contra_ruido", "MxD03 contra un corrimiento al azar del mismo tamano"),
    ("MC", "RC", "MC_contra_ruido", "lo mismo con la etiqueta desde el cumulo"),
)
NULO_DE = {"principal": "nulo_de_principal", "posicion_produccion": "nulo_de_posicion_produccion",
           "posicion_cumulo": "nulo_de_posicion_cumulo"}
TOL_RUIDO_KM = 0.01        # el ruido aplicado tiene que ser el pedido
MARGEN_KM = 1.0            # banda del modelo = corrimiento predicho con la linea + 1 km (terreno)
BANDA_FRAC = 0.10          # mas de 10 % de los granulos sobre la banda: el modelo se quedo corto (anotacion)
REPLAY_MIN = 0.90          # acuerdo minimo del replay con el brazo CC medido para creerle a la prediccion
Z, SUAVIZADO = 1.96, 0.5   # intervalo normal al 95 %; medio conteo de suavizado en -1 y +1


def _cargar(p):
    return json.load(open(p, encoding="utf-8"))


def _unir(pob, salidas):
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


def tramo_a119(fecha):
    """Tramo de calidad de la referencia para MODIS (A119): corta en los hitos que tocan a todos o a
    MODIS. Devuelve la fecha del ultimo hito aplicable anterior o igual a `fecha`."""
    from calidad_referencia_mirova import HITOS
    cortes = sorted({h[0] for h in HITOS if h[2] == "todos" or "MODIS" in h[2]})
    previos = [c for c in cortes if c <= (fecha or "")[:10]]
    return "desde " + previos[-1] if previos else "antes de " + cortes[0]


# ------------------------------------------------------------------ estimador del total de una celda
def total_celda(valores, N, a=SUAVIZADO):
    """(estimacion, varianza) del total de una celda de N unidades de las que se midieron `valores`
    (en {-1, 0, +1}). Medida entera: exacta y sin varianza."""
    n = len(valores)
    s = float(sum(valores))
    if n >= N:
        return s, 0.0
    cp, cm = sum(v == 1 for v in valores), sum(v == -1 for v in valores)
    pp, pm = (cp + a) / (n + 2 * a), (cm + a) / (n + 2 * a)
    var_unidad = pp + pm - (pp - pm) ** 2
    return s + (N - n) * (s / n if n else 0.0), (N - n) * N / max(n, 1) * var_unidad


def wilson_celda(valores, N):
    """Lo de la 1.17: bordes de Wilson sumados por celda (conservador)."""
    n = len(valores)
    if n >= N:
        s = float(sum(valores))
        return s, s
    kg, kp = sum(v == 1 for v in valores), sum(v == -1 for v in valores)
    gl, gh = wilson(kg, n)
    pl, ph = wilson(kp, n)
    return N * gl - N * ph, N * gh - N * pl


def balance(celdas, base):
    """celdas: {nombre: (valores, N)}; base: parte exacta (alertas). Devuelve el resumen de Delta."""
    punto, var = float(base), 0.0
    wl = wh = float(base)
    for vals, N in celdas.values():
        p, v = total_celda(vals, N)
        punto += p
        var += v
        lo_w, hi_w = wilson_celda(vals, N)
        wl += lo_w
        wh += hi_w
    h = Z * math.sqrt(var)
    return {"delta": round(punto, 1), "intervalo": [round(punto - h, 1), round(punto + h, 1)],
            "intervalo_wilson_por_celda": [round(wl, 1), round(wh, 1)]}


# ------------------------------------------------------------------ una comparacion
def comparar(X, Y, ok, pob, vols):
    def d(f):
        return f["pub"][X] - f["pub"][Y]

    prot = [f for f in ok if f["prot"]]
    r1 = {"medidas": len(prot), "publica_" + Y: sum(f["pub"][Y] for f in prot),
          "publica_" + X: sum(f["pub"][X] for f in prot),
          "perdidas": sum(d(f) == -1 for f in prot), "ganadas": sum(d(f) == 1 for f in prot),
          "perdidas_detalle": [{"volcan": f["volcan"], "clave": f["clave"], "datetime_utc": f["datetime_utc"],
                                "vrp_ref": f.get("vrp_ref")} for f in prot if d(f) == -1]}
    alertas = [f for f in ok if f["lab"] == "pos" and not f["prot"]]
    a_perd, a_gan = sum(d(f) == -1 for f in alertas), sum(d(f) == 1 for f in alertas)
    celdas, por_celda = {}, {}
    for vol in sorted(vols):
        for e, cuenta in sorted(pob["volcanes"][vol]["N"].items()):
            N = cuenta.get("neg_limpio", 0)
            if not N or e == "sin":   # estrato sin distancias (18 records, 12 negativos limpios): fuera desde la 1.17
                continue
            vals = [d(f) for f in ok if f["volcan"] == vol and f["estrato"] == e and f["lab"] == "neg_limpio"]
            celdas["%s/%s" % (vol, e)] = (vals, N)
            por_celda["%s/%s" % (vol, e)] = {"N": N, "n": len(vals), "0->1": vals.count(1), "1->0": vals.count(-1)}
    r2 = {"alertas_medidas": len(alertas), "alertas_perdidas": a_perd, "alertas_ganadas": a_gan,
          "por_celda": por_celda}
    r2.update(balance(celdas, a_perd - a_gan))
    hubo = any(d(f) != 0 or (f["brazos"][X] or {}).get("dc") != (f["brazos"][Y] or {}).get("dc") for f in ok)
    if r1["perdidas"] > 0:
        ver = "PIERDE PROTEGIDA"
    elif not hubo:
        ver = "SIN CAMBIO OBSERVADO"
    elif r2["intervalo"][1] < 0:
        ver = "MEJORA"
    elif r2["intervalo"][0] > 0:
        ver = "EMPEORA"
    else:
        ver = "INDETERMINADO"
    # cortes informativos: por volcan, satelite, cenit y tramo A119 (conteos observados, sin expandir)
    cortes = defaultdict(lambda: {"n": 0, "0->1": 0, "1->0": 0, "alertas_0->1": 0, "alertas_1->0": 0})
    for f in ok:
        sat = (f.get("sensor") or "?").replace("MODIS_", "")
        for clave in (("volcan", f["volcan"]), ("satelite", sat), ("cenit", _bin(f.get("sensor_zenith_deg"))),
                      ("tramo_a119", tramo_a119(f.get("datetime_utc")))):
            c = cortes["%s=%s" % clave]
            c["n"] += 1
            c["0->1"] += d(f) == 1
            c["1->0"] += d(f) == -1
            if f["lab"] == "pos":
                c["alertas_0->1"] += d(f) == 1
                c["alertas_1->0"] += d(f) == -1
    return {"X": X, "Y": Y, "veredicto": ver, "regla1": r1, "regla2": r2, "hubo_cambio": hubo,
            "tipos_de_cambio": tipos_de_cambio(X, Y, ok), "cortes": dict(sorted(cortes.items()))}


def tipos_de_cambio(X, Y, ok):
    """Particion del verificador de la 1.17 (v3_mismo_pixel.py), para los granulos que cambian de
    publicacion o de etiqueta: cambia la fuente del hotspot final, o con la misma fuente el hotspot se
    movio a lo sumo el corrimiento + 1,5 km (el mismo pixel reubicado) o mas (otro pixel). Y lo mismo
    para el cumulo, que es de donde sale la etiqueta de los brazos con cumulo."""
    out = defaultdict(int)
    for f in ok:
        a, b = f["brazos"][Y] or {}, f["brazos"][X] or {}
        if f["pub"][X] == f["pub"][Y] and a.get("dc") == b.get("dc"):
            continue
        tope = (f.get("desplazamiento") or {}).get("km", 0.0) + 1.5
        if a.get("fuente") != b.get("fuente"):
            out["hotspot: cambia la fuente"] += 1
        elif _km(a, b, "final") <= tope:
            out["hotspot: mismo pixel reubicado"] += 1
        else:
            out["hotspot: otro pixel"] += 1
        if a.get("pc_lat") is None or b.get("pc_lat") is None:
            out["cumulo: aparece o desaparece"] += 1
        elif _km(a, b, "pc") <= tope and abs((a.get("pc_vrp") or 0) - (b.get("pc_vrp") or 0)) <= 0.01 * max(
                abs(a.get("pc_vrp") or 0), 1e-9):
            out["cumulo: el mismo, reubicado"] += 1
        else:
            out["cumulo: otro o con otra magnitud"] += 1
    return dict(out)


def _km(a, b, p):
    la, lo, lb, lob = a.get(p + "_lat"), a.get(p + "_lon"), b.get(p + "_lat"), b.get(p + "_lon")
    if None in (la, lo, lb, lob):
        return float("inf")
    return math.hypot((la - lb) * 111.32, (lo - lob) * 111.32 * math.cos(math.radians(la)))


# ------------------------------------------------------------------ evaluacion completa
def evaluar(pob, salidas, ausentes=(), esperados=None, prediccion=None):
    esperados = list(pob["jobs"]) if esperados is None else list(esperados)
    aus = {(a["volcan"], a["clave"]) for a in ausentes}
    vols = {pob["jobs"][j]["volcan"] for j in esperados}
    filas = [f for f in _unir(pob, salidas) if f["volcan"] in vols]
    pedidas = [f for f in filas if (f["volcan"], f["clave"]) not in aus]
    ok = [f for f in pedidas if f.get("estado") == "ok"]

    # ---- cobertura (A108): todo lo pedido medido, y todos los brazos en cada granulo medido
    incompleto = []
    faltan_jobs = [j for j in esperados if j not in salidas]
    # un solo pipeline (verificador v2, A108): todos los artefactos del mismo commit
    commits = sorted({str(s.get("commit")) for j, s in salidas.items() if j in esperados})
    sin_commit = sorted(j for j, s in salidas.items() if j in esperados and not s.get("commit"))
    if sin_commit:
        incompleto.append("artefactos sin commit: %s" % sin_commit)
    if len([c for c in commits if c != "None"]) > 1:
        incompleto.append("artefactos de mas de un commit (dos pipelines): %s" % commits)
    if faltan_jobs:
        incompleto.append("faltan jobs: %s" % faltan_jobs)
    sin_medir = [f["clave"] for f in pedidas if f.get("estado") != "ok"]
    if sin_medir:
        incompleto.append("%d granulos pedidos sin medir: %s" % (len(sin_medir), sin_medir[:20]))
    for j in esperados:
        s = salidas.get(j)
        if s is not None and not any(g.get("cprima_igual") is not None for g in s.get("granulos", [])):
            incompleto.append("%s sin brazo C'" % j)
    conteo = {b: {"granulos": 0, "con_record": 0} for b in BRAZOS}
    for f in ok:
        for b in BRAZOS:
            if b in (f.get("pub") or {}) and b in (f.get("brazos") or {}):
                conteo[b]["granulos"] += 1
                conteo[b]["con_record"] += f["brazos"][b] is not None
    if len({c["granulos"] for c in conteo.values()}) != 1 or conteo["C"]["granulos"] != len(ok):
        incompleto.append("los brazos no tienen la misma cantidad de granulos medidos: %s" % conteo)
        ok = [f for f in ok if all(b in (f.get("pub") or {}) and b in (f.get("brazos") or {}) for b in BRAZOS)]
    aus_censo = [a for a in ausentes if a["volcan"] in vols and (a["prot"] or a["lab"] == "pos")]

    # ---- instrumento: C', cableado del flag y ruido aplicado
    invalido = []
    invalido += ["C' distinto de C en %s" % f["clave"] for f in ok if f.get("cprima_igual") is False]
    for f in ok:
        for b in BRAZOS:
            visto = (f.get("flag_visto") or {}).get(b, [])
            if visto not in ([], [CUMULO[b]]):
                invalido.append("%s: el brazo %s vio desde_cluster=%s" % (f["clave"], b, visto))
        r = f.get("ruido") or {}
        if abs((r.get("km_aplicado") or 0) - (r.get("km_objetivo") or 0)) > TOL_RUIDO_KM:
            invalido.append("%s: ruido aplicado %s km contra %s pedido" % (f["clave"], r.get("km_aplicado"),
                                                                            r.get("km_objetivo")))
    llamadas = {b: sum(1 for f in ok if (f.get("flag_visto") or {}).get(b)) for b in BRAZOS}
    if ok and any(v == 0 for v in llamadas.values()):
        invalido.append("algun brazo nunca llamo a derivar_distance_class: %s" % llamadas)

    comps = {nombre: comparar(X, Y, ok, pob, vols) for X, Y, nombre, _ in COMPARACIONES}
    for nombre, nulo in NULO_DE.items():
        # FRAGIL es por PASADA (verificador del pre-registro, bloqueante 2): la misma protegida se pierde
        # tambien con el sorteo de un corrimiento al azar. Que el nulo pierda OTRA protegida no dice nada
        # de esta.
        propias = {(x["volcan"], x["clave"]) for x in comps[nombre]["regla1"]["perdidas_detalle"]}
        del_nulo = {(x["volcan"], x["clave"]) for x in comps[nulo]["regla1"]["perdidas_detalle"]}
        comunes = sorted(propias & del_nulo)
        comps[nombre]["fragil"] = bool(comunes)
        comps[nombre]["fragil_pasadas"] = ["%s|%s" % x for x in comunes]
        comps[nombre]["perdidas_que_el_nulo_no_pierde"] = ["%s|%s" % x for x in sorted(propias - del_nulo)]
    if invalido:
        ver = "INVALIDO"
    elif incompleto:
        ver = "INCOMPLETO"
    else:
        ver = comps["principal"]["veredicto"]

    # ---- anotaciones: modelo de corrimiento, deriva y prueba del replay
    exc = [f["clave"] for f in ok if _excede(f)]
    banda = {"n": len(exc), "de": len(ok), "modelo_corto": bool(ok) and len(exc) / len(ok) > BANDA_FRAC,
             "casos": exc[:30]}
    replay = None
    if prediccion:
        # por grupo (verificador del pre-registro, bloqueante 1c): en la fuente test1 el replay no ve el
        # cumulo con que se etiqueta, asi que ahi su prediccion es una cota y se informa aparte; la
        # credibilidad se decide con el resto.
        replay = {}
        for f in ok:
            p = prediccion["granulos"].get("%s|%s" % (f["volcan"], f["clave"]))
            if p is None:
                continue
            g = "protegidas" if f["prot"] else ("fuente_test1" if p.get("fuente") == "test1" else "resto")
            if ((f["brazos"]["C"] or {}).get("fuente")) == "test1":   # la fuente medida hoy, no la guardada
                h = replay.setdefault("fuente_test1_medida_en_C", {"acuerdo": 0, "de": 0})
                h["de"] += 1
                h["acuerdo"] += f["pub"]["CC"] == p["pub_cc_replay"]
            r = replay.setdefault(g, {"acuerdo": 0, "de": 0, "CC_medido_1_replay_0": 0, "CC_medido_0_replay_1": 0})
            r["de"] += 1
            r["acuerdo"] += f["pub"]["CC"] == p["pub_cc_replay"]
            r["CC_medido_1_replay_0"] += f["pub"]["CC"] == 1 and p["pub_cc_replay"] == 0
            r["CC_medido_0_replay_1"] += f["pub"]["CC"] == 0 and p["pub_cc_replay"] == 1
        resto = replay.get("resto", {"acuerdo": 0, "de": 0})
        replay["creible_fuera_de_test1"] = bool(resto["de"]) and resto["acuerdo"] / resto["de"] >= REPLAY_MIN
        replay["prediccion_delta_poblacion_CC_vs_C_cota"] = prediccion["total"].get("delta")
    otro_cumulo = {}
    for b in BRAZOS:
        cl = [f["clave"] for f in ok if ((f.get("cumulo_etiqueta") or {}).get(b) or {}).get("distinto")]
        otro_cumulo[b] = {"n": len(cl), "claves": cl[:30]}
    prot_ok = [f for f in ok if f["prot"]]
    deriva_prot = [{"volcan": f["volcan"], "clave": f["clave"], "pub_guardada": f.get("pub_guardada"),
                    "pub_C": f["pub"]["C"]} for f in prot_ok if f.get("pub_guardada") != f["pub"]["C"]]
    return {"veredicto": ver, "adoptable_en_la_replica": ver == "MEJORA",
            "motivos_invalido": invalido[:50], "motivos_incompleto": incompleto,
            "ausentes_del_archivo": {"n": len([a for a in ausentes if a["volcan"] in vols]),
                                     "en_censo": aus_censo},
            "commits": [c for c in commits if c != "None"],
            "conteo_por_brazo": conteo, "comparaciones": comps, "banda_modelo_traza": banda,
            "c_igual_a_guardada": {"si": sum(1 for f in ok if f.get("c_igual_a_guardada")), "de": len(ok)},
            "deriva_protegidas": {"distintas": deriva_prot, "de": len(prot_ok)},
            "etiqueta_con_otro_cumulo": otro_cumulo,
            "prueba_del_replay": replay}


def _excede(f):
    d = f.get("desplazamiento")
    if not d or f.get("sensor_zenith_deg") is None or f.get("sensor_azimuth_deg") is None:
        return False
    p = MC.corrimiento_predicho_traza(f["sensor_zenith_deg"], f["sensor_azimuth_deg"], f["sensor"], d["linea"])
    return d["km"] > p + MARGEN_KM


# ------------------------------------------------------------------ control del estimador
def control_estimador(pob, prediccion):
    """Respuesta conocida (A110): con el replay como si fuera la medida, el estimador sobre la muestra
    tiene que contener el total de la poblacion que el replay da por censo. Devuelve (total, resumen)."""
    celdas = {}
    for vol, v in pob["volcanes"].items():
        for e, cuenta in v["N"].items():
            N = cuenta.get("neg_limpio", 0)
            if N and e != "sin":
                vals = []
                for g in v["muestra"]:
                    if g["estrato"] == e and g["lab"] == "neg_limpio":
                        p = prediccion["granulos"]["%s|%s" % (vol, g["clave"])]
                        vals.append(p["pub_cc_replay"] - p["pub_c_guardada"])
                celdas["%s/%s" % (vol, e)] = (vals, N)
    t = prediccion["total"]
    total = t.get("neg_limpio|0->1", 0) - t.get("neg_limpio|1->0", 0)
    return total, balance(celdas, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--poblacion", default=str(DIR_117 / "poblacion.json"))
    ap.add_argument("--archivo", default=str(AQUI / "archivo_cmr.json"))
    ap.add_argument("--prediccion", default=str(AQUI / "prediccion_cumulo.json"))
    ap.add_argument("--jobs", default=None)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    from calidad_referencia_mirova import avisar
    pob = _cargar(a.poblacion)
    avisar(*pob["meta"]["ventana"])
    salidas = {}
    for p in sorted(Path(a.carpeta).rglob("*.json")):
        d = _cargar(p)
        if isinstance(d, dict) and "granulos" in d and "job" in d and "brazos" in d:
            salidas[d["job"]] = d
    r = evaluar(pob, salidas, _cargar(a.archivo)["ausentes"], json.loads(a.jobs) if a.jobs else None,
                _cargar(a.prediccion))
    texto = json.dumps(r, indent=1, ensure_ascii=False)
    if a.salida:
        Path(a.salida).write_text(texto, encoding="utf-8")
    print("VEREDICTO:", r["veredicto"], "| adoptable:", r["adoptable_en_la_replica"],
          "| invalido:", r["motivos_invalido"][:3] or "-", "| incompleto:", r["motivos_incompleto"] or "-")
    for nombre, c in r["comparaciones"].items():
        print("  %-28s %-4s vs %-3s %-22s regla 1: %d perdidas, %d ganadas de %d | delta %s %s%s" % (
            nombre, c["X"], c["Y"], c["veredicto"], c["regla1"]["perdidas"], c["regla1"]["ganadas"],
            c["regla1"]["medidas"], c["regla2"]["delta"], c["regla2"]["intervalo"],
            " | FRAGIL" if c.get("fragil") else ""))
    if not salidas:
        sys.exit("no encontre salidas del probe en %s" % a.carpeta)


if __name__ == "__main__":
    main()
