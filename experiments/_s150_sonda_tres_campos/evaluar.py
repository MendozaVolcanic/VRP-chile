# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: evaluador con el criterio PRE-REGISTRADO en DISENO.md §5 a §8.

Lee las salidas por pasada (out/*.json de todos los lotes), corre el predicado del tablero con node
sobre el record persistido de cada corrida (A97: "publicamos" es el predicado del operador, no uno
reconstruido a mano) y aplica las reglas en este orden:
  0. los GATES del instrumento, todos ANTES de mirar H1 o D22 (DISENO §5): identidad con las funciones
     reales (sobre el recorte y sobre el granulo entero), cobertura con n minimo por grupo, sigma del
     nativo contra el record del A/B pasada por pasada, reproduccion del A/B POR GRUPO en el nativo,
     validacion del campo contra el GeoTIFF de MIROVA (con el gate de r_L por pasada). Si un gate falla,
     el veredicto es INDETERMINADO POR INSTRUMENTO o POR COBERTURA y no se lee. No hay "salvedades":
     un veredicto con salvedad se leeria igual (verificador S150, hallazgo 1).
  1. H1, la sigma del campo, con R_L como contraste DENTRO de la corrida y guarda de brecha minima.
  2. D22 y D26, por separado y juntas, con control positivo que FRENA.
  3. H3, la tabla de las dos conectivas en cada campo (informa, no decide).

  python evaluar.py --out <carpeta con los json de todos los lotes> [--sin-predicado] [--piloto]

--piloto: NO corre el predicado ni imprime ningun veredicto de deteccion. Solo cobertura de los lotes
presentes, identidad, tiempo, memoria, volumen de la salida y validacion contra el TIF (DISENO §10 bis).

Ninguna regla de aca se cambia despues de ver datos de la sonda: el sha256 de DISENO.md y de este
archivo queda sellado en el pre-registro antes del despacho.
"""
import argparse, collections, io, json, math, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

CAMPOS_TIF = ("tif_lin", "tif_cub", "tif_nn")
# Umbrales pre-registrados (DISENO.md §5 a §8). Su origen esta explicado ahi; los que son una ELECCION
# lo dicen, con su motivo, en DISENO §5 bis (escrito antes de ver ningun dato de la sonda).
VALIDA_R_DL = 0.80
VALIDA_S_RATIO = (0.80, 1.25)
VALIDA_R_L_TIF_NN = 0.90           # gate por pasada para entrar a la validacion (hallazgo 4 b)
FRAC_MIN_TIF_VALIDABLES = 0.50     # de las pasadas con TIF usable esperadas, cuantas deben pasar ese gate
UMBRAL_IDENTIDAD = 1e-9
FRAC_MAX_FALLA_IDENTIDAD = 0.05
ACUERDO_MIN_AB = 0.95              # solo informativo desde la correccion: el gate es por grupo (abajo)
# gate de reproduccion por grupo en el nativo (hallazgo 1)
MAX_FALLAS_REPRO_PERDIDAS = 2      # perdidas confiables donde nativo|max publica o nativo|min no
MAX_FRAC_FALLAS_REPRO_CONSERVADAS = 0.05   # conservadas debiles donde nativo|max no publica
# gate de sigma del nativo contra el record del A/B (hallazgo 1, punto 5)
SD_REL_IDENTICA = 1e-6
FRAC_MIN_SD_IDENTICA = 0.95
# gate de cobertura (hallazgo 2)
MAX_FALTAN_PERDIDAS_CONF = 2       # de las 32 perdidas confiables, cuantas pueden faltar
FRAC_MIN_GRUPO = 0.90              # cada grupo con al menos esto de sus pasadas usables
MAX_FALTAN_PERDIDAS_D22 = 1        # de las 14 perdidas confiables del camino D22
# guarda de la brecha FP(nativo, min) - FP(nativo, max) (hallazgo 1, punto 3)
BRECHA_MIN = 0.10
H1_RECALL_CONFIRMA = 0.50
H1_RECALL_REFUTA = 0.25
H1_DFP_CONFIRMA = 0.25      # fraccion de la brecha FP(min) - FP(max) del nativo que se tolera devolver
H1_DFP_REFUTA = 0.50
H1_PERDIDA_CONSERVADAS = 0.10
D22_RECUP = 0.50
D22_REAPERTURA = 0.25
MAX_FALLAS_CTRL_POS_D22 = 0        # nativo|min tiene que publicar TODAS las perdidas D22 usables
GRUPOS_NEG = ("residual_apagado", "residual_sobrevive", "negativo_b_no_publica")
CAMPOS_JS = ["primary_cluster", "distance_class", "vrp_mw", "vrp_mir_mw", "discarded_reason",
             "triggered_test1", "vrp_vent_mw", "t_max_k", "sensor", "f5_core_vrp_mw", "anomaly_pixels"]
# lo que publica cada brazo del A/B por grupo (definicion de los grupos en seleccionar_pasadas.py)
F_PUBLICA = {"perdida": 0, "conservada_debil": 1, "residual_apagado": 0, "residual_sobrevive": 1,
             "negativo_b_no_publica": 0, "muestra_negativos_d22": 0}
B_PUBLICA = {"perdida": 1, "conservada_debil": 1, "residual_apagado": 1, "residual_sobrevive": 1,
             "negativo_b_no_publica": 0, "muestra_negativos_d22": 1}


def _med(xs):
    xs = sorted(x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x)))
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def _auc(pos, neg):
    pos = [x for x in pos if x is not None]; neg = [x for x in neg if x is not None]
    if not pos or not neg:
        return None
    return sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg))


def _tasa(xs):
    """(tasa, n): el n va SIEMPRE con la tasa (hallazgo 2)."""
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def predicado(filas, usar_node=True):
    """pub[(clave, corrida)] = 1/0 con el predicado del tablero sobre el record persistido."""
    casos, claves = [], []
    import banco_paridad as bp
    inner = bp.inner_desde_html()
    for f in filas:
        vol = f["clave"].split("|")[0]
        for corrida, c in (f.get("corridas") or {}).items():
            r = c.get("record")
            if r is None:
                continue
            slim = {k: r.get(k) for k in CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]]); claves.append((f["clave"], corrida))
    pub = {}
    if usar_node and casos:
        res = bp.correr_node(casos)
        for k, p in zip(claves, res):
            pub[k] = int(p[4])
    for f in filas:
        for corrida, c in (f.get("corridas") or {}).items():
            if c.get("record") is None and "error" not in c:
                pub[(f["clave"], corrida)] = 0     # sin record (granulo sin cobertura o store lo rechazo): no publica
    return pub


def _nuevo_en_cumbre(px, variante, base="max_cc"):
    """Pixel de cumbre activo en la variante y no en la base (para negativos, a nivel de tests)."""
    if not px:
        return None
    fv = px.get(variante); fb = px.get("final_" + base)
    if fv is None or fb is None:
        return None
    return int(any(a and not b and c for a, b, c in zip(fv, fb, px["cumbre"])))


def _objetivo(px, variante, base=None):
    """Pixel del objetivo activo en la variante (y, si se da base, NO activo en la base)."""
    if not px or px.get(variante) is None:
        return None
    fb = px.get("final_" + base) if base else None
    if base and fb is None:
        return None
    return int(any(a and o and not (fb[i] if fb else 0) for i, (a, o) in enumerate(zip(px[variante], px["objetivo"]))))


def _cargar(rutas):
    """Acepta rutas a json o dicts ya cargados (la prueba local arma poblaciones en memoria)."""
    filas, tam = [], {}
    for r in rutas:
        if isinstance(r, dict):
            filas.append(r)
            continue
        p = Path(r)
        f = json.loads(p.read_text(encoding="utf-8"))
        filas.append(f)
        tam[f.get("clave")] = p.stat().st_size
    return filas, tam


def _grupos(m):
    return m.get("grupos") or [m["grupo"]]


def _identidad(ok):
    """Pares pasada-campo que no reproducen las funciones reales (recorte y granulo entero)."""
    malas = []
    for f in ok:
        for campo, ev in (f.get("campos") or {}).items():
            idp = ev.get("identidad_primer_pase") or {}
            dec = (ev.get("decision") or {}).values()
            bien = (bool(idp) and all(v is not None and v < UMBRAL_IDENTIDAD for v in idp.values())
                    and ev.get("identidad_n_pool")
                    and all(d.get("identidad_hot_1") for d in dec)
                    and all(d.get("identidad_final") is not False for d in dec)
                    # hallazgo 6: contra fp_hot y sp_out_n de la corrida sobre el granulo entero
                    and (ev.get("identidad_escena") or {}).get("ok") is True)
            if not bien:
                malas.append((f["clave"], campo))
    n_pc = sum(len(f.get("campos") or {}) for f in ok)
    return malas, n_pc


def _cobertura(meta, filas, usables):
    """Cobertura por grupo (pertenencia) y los gates de n minimo (hallazgo 2)."""
    salida = {f["clave"] for f in filas}
    completas = {f["clave"] for f in filas if f.get("ok")}
    us = {f["clave"] for f in usables}
    esperadas = collections.Counter(g for m in meta.values() for g in _grupos(m))
    tab = {}
    for g in esperadas:
        ks = [k for k, m in meta.items() if g in _grupos(m)]
        tab[g] = {"esperadas": len(ks), "con_salida": sum(k in salida for k in ks),
                  "completas": sum(k in completas for k in ks), "usables": sum(k in us for k in ks)}
    pc = [k for k, m in meta.items() if m["grupo"] == "perdida" and m.get("etiqueta_confiable")]
    pd22 = [k for k in pc if meta[k].get("camino_b") == "d22"]
    tab["perdida_confiable"] = {"esperadas": len(pc), "usables": sum(k in us for k in pc)}
    tab["perdida_confiable_d22"] = {"esperadas": len(pd22), "usables": sum(k in us for k in pd22)}
    fallas = []
    faltan = tab["perdida_confiable"]["esperadas"] - tab["perdida_confiable"]["usables"]
    if faltan > MAX_FALTAN_PERDIDAS_CONF:
        fallas.append("faltan %d de %d perdidas confiables (maximo %d)" % (faltan, len(pc), MAX_FALTAN_PERDIDAS_CONF))
    for g in esperadas:
        if tab[g]["usables"] < FRAC_MIN_GRUPO * tab[g]["esperadas"]:
            fallas.append("grupo %s: %d usables de %d (minimo %.0f %%)" % (g, tab[g]["usables"], tab[g]["esperadas"],
                                                                         100 * FRAC_MIN_GRUPO))
    fallas_d22 = []
    faltan_d22 = tab["perdida_confiable_d22"]["esperadas"] - tab["perdida_confiable_d22"]["usables"]
    if faltan_d22 > MAX_FALTAN_PERDIDAS_D22:
        fallas_d22.append("faltan %d de %d perdidas D22 confiables (maximo %d)" % (faltan_d22, len(pd22), MAX_FALTAN_PERDIDAS_D22))
    return tab, fallas, fallas_d22


def _validacion(usables, meta):
    """Validacion de los campos tif_* contra el GeoTIFF de MIROVA, con el gate de r_L por pasada."""
    entra, descartadas = [], []
    for f in usables:
        vt = f.get("validacion_tif") or {}
        if not vt:
            continue
        nn = vt.get("tif_nn") or {}
        if nn.get("ok") and nn.get("r_L") is not None and nn["r_L"] >= VALIDA_R_L_TIF_NN:
            entra.append(f)
        else:
            descartadas.append({"clave": f["clave"], "r_L_tif_nn": nn.get("r_L"), "error": nn.get("error")})

    def resumen(fs):
        val = {}
        for c in CAMPOS_TIF:
            vs = [f["validacion_tif"][c] for f in fs if (f.get("validacion_tif") or {}).get(c, {}).get("ok")]
            r = _med([v["r_dL"] for v in vs]); s_ = _med([v["s_ratio"] for v in vs])
            val[c] = {"n_pasadas": len(vs), "r_L_mediana": _med([v["r_L"] for v in vs]), "r_dL_mediana": r,
                      "s_ratio_mediana": s_, "rel_mediana": _med([v["rel_mediana"] for v in vs]),
                      "ac1_dL_campo_mediana": _med([v.get("ac1_dL_campo") for v in vs]),
                      "ac1_dL_tif_mediana": _med([v.get("ac1_dL_tif") for v in vs]),
                      "valido": bool(vs) and r is not None and s_ is not None and r >= VALIDA_R_DL
                      and VALIDA_S_RATIO[0] <= s_ <= VALIDA_S_RATIO[1]}
        return val
    esperadas_tif = sum(1 for m in meta.values() if (m.get("tif") or {}).get("usable"))
    val = resumen(entra)
    por_vol = collections.defaultdict(list)
    for f in entra:
        por_vol[f["clave"].split("|")[0]].append(f)
    por_volcan = {v: {c: {k: x[k] for k in ("n_pasadas", "r_dL_mediana", "s_ratio_mediana", "valido")}
                      for c, x in resumen(fs).items()} for v, fs in sorted(por_vol.items())}
    falla = None
    if len(entra) < FRAC_MIN_TIF_VALIDABLES * esperadas_tif:
        falla = "solo %d de %d pasadas con TIF pasan r_L >= %.2f (minimo %.0f %%)" % (
            len(entra), esperadas_tif, VALIDA_R_L_TIF_NN, 100 * FRAC_MIN_TIF_VALIDABLES)
    validos = [c for c in CAMPOS_TIF if val[c]["valido"]] if falla is None else []
    M = max(validos, key=lambda c: (val[c]["r_dL_mediana"], -abs(math.log(val[c]["s_ratio_mediana"])))) if validos else None
    if falla is None and M is None:
        falla = "ningun campo interpolado reproduce el TIF de MIROVA"
    info = {"gate_r_L": {"umbral": VALIDA_R_L_TIF_NN, "esperadas_con_tif": esperadas_tif, "entran": len(entra),
                         "descartadas": len(descartadas), "ejemplos_descartadas": descartadas[:20]},
            "campos": val, "por_volcan": por_volcan, "campo_mirova": M}
    return info, M, falla


def _operativo(filas, tam):
    """Tiempo, memoria y volumen de la salida por lote: lo unico, junto con la validacion, que lee el piloto."""
    por = collections.defaultdict(lambda: {"segundos": [], "rss": [], "bytes": []})
    for f in filas:
        lote = f.get("lote")
        por[lote]["segundos"].append(f.get("segundos"))
        por[lote]["rss"].append(f.get("rss_max_mb"))
        por[lote]["bytes"].append(tam.get(f.get("clave")))
    out = {}
    for lote, v in sorted(por.items(), key=lambda x: str(x[0])):
        seg = [x for x in v["segundos"] if x is not None]; by = [x for x in v["bytes"] if x is not None]
        rss = [x for x in v["rss"] if x is not None]
        out[str(lote)] = {"pasadas": len(v["segundos"]), "segundos_total": round(sum(seg), 1) if seg else None,
                          "segundos_mediana": _med(seg), "segundos_max": max(seg) if seg else None,
                          "rss_max_mb": max(rss) if rss else None,
                          "bytes_mediana": _med(by), "bytes_max": max(by) if by else None,
                          "bytes_total": sum(by) if by else None}
    return out


def evaluar(rutas, pasadas_meta, totales, predicado_node=True, negativos_d22=None, piloto=False):
    filas, tam = _cargar(rutas)
    fuentes = [("(en memoria %d)" % i) if isinstance(r, dict) else str(r) for i, r in enumerate(rutas)]
    pares = [(f, s) for f, s in zip(filas, fuentes) if f.get("clave") in pasadas_meta]
    out = {"instrumento": {}, "h1": {}, "d22_d26": {}, "h3": {}, "veredictos": {}}
    meta = pasadas_meta

    # ---------------- 0. gates del instrumento
    # Pasadas duplicadas (segundo verificador, V2-5): la misma clave dos veces (p. ej. la salida del piloto y la
    # del despacho completo en la misma carpeta) contaria la pasada dos veces en cada tasa. Es una falla del
    # instrumento: se informa con los archivos, se conserva la primera para los diagnosticos y no hay veredicto.
    vistas, duplicadas = {}, collections.defaultdict(list)
    for f, fuente in pares:
        if f["clave"] in vistas:
            duplicadas[f["clave"]].append(fuente)
        else:
            vistas[f["clave"]] = (f, fuente)
    if duplicadas:
        out["instrumento"]["duplicadas"] = {k: [vistas[k][1]] + v for k, v in list(duplicadas.items())[:20]}
    filas = [v[0] for v in vistas.values()]

    ok = [f for f in filas if f.get("ok")]
    malas_id, n_pc = _identidad(ok)
    out["instrumento"]["identidad"] = {"pares_pasada_campo": n_pc, "fallan": len(malas_id), "ejemplos": malas_id[:10]}
    excluir = {k for k, _ in malas_id}
    identidad_ok = n_pc > 0 and len(malas_id) <= FRAC_MAX_FALLA_IDENTIDAD * n_pc
    usables = [f for f in ok if f["clave"] not in excluir]

    # sigma dNTI del nativo contra el record del A/B, pasada por pasada (hallazgo 1, punto 5). Se compara con
    # el brazo F, que es el mismo perfil que la corrida capturada (en el A/B B y F dan la misma sigma: el pozo
    # del primer pase no depende de la conectiva ni de la compuerta). Va ANTES del piloto (V2-4): no es dato de
    # deteccion y es el gate que mas probablemente gaste el despacho si NASA reproceso los granulos. Una sigma
    # ausente, nula o no finita (NaN) cuenta como distinta (V2-10).
    rel_sd, distintas = [], []
    for f in usables:
        ev = (f.get("campos") or {}).get("nativo") or {}
        sd = (ev.get("primer_pase") or {}).get("sd_dnti"); sd_ab = (meta[f["clave"]].get("F") or {}).get("diag_sd_dnti")
        if not (isinstance(sd, (int, float)) and isinstance(sd_ab, (int, float)) and math.isfinite(sd)
                and math.isfinite(sd_ab) and sd_ab > 0):
            distintas.append(f["clave"]); continue
        rel = abs(sd - sd_ab) / sd_ab
        rel_sd.append(rel)
        if not rel < SD_REL_IDENTICA:
            distintas.append(f["clave"])
    frac_ident = (1 - len(distintas) / len(usables)) if usables else None
    out["instrumento"]["sd_dnti_nativo_vs_record_ab"] = {
        "n_usables": len(usables), "n_comparadas": len(rel_sd), "frac_identica": frac_ident,
        "umbral_rel": SD_REL_IDENTICA, "minimo": FRAC_MIN_SD_IDENTICA, "mediana_rel": _med(rel_sd),
        "distintas": distintas[:20]}
    falla_sd = None
    if frac_ident is None or frac_ident < FRAC_MIN_SD_IDENTICA:
        falla_sd = "sigma dNTI del nativo distinta del A/B en %d de %d pasadas (frac identica %s, minimo %.2f)" % (
            len(distintas), len(usables), None if frac_ident is None else round(frac_ident, 3), FRAC_MIN_SD_IDENTICA)
    out["instrumento"]["mismo_granulo_que_ab"] = _tasa([int(bool(f.get("mismo_granulo_que_ab"))) for f in usables])

    if piloto:
        out["instrumento"]["sd_dnti_falla"] = falla_sd
        out["instrumento"]["duplicadas_falla"] = bool(duplicadas)
        # Piloto: solo lo que no es deteccion. La cobertura se mide contra los lotes presentes.
        lotes = {f.get("lote") for f in filas}
        meta_lotes = {k: m for k, m in meta.items() if m.get("lote") in lotes}
        tab, _, _ = _cobertura(meta_lotes, filas, usables)
        out["instrumento"]["cobertura_lotes_presentes"] = {"lotes": sorted(str(x) for x in lotes), "por_grupo": tab}
        out["instrumento"]["operativo"] = _operativo(filas, tam)
        info, M, falla = _validacion(usables, meta_lotes)
        out["instrumento"]["validacion_tif"] = info
        out["instrumento"]["validacion_falla"] = falla
        out["h1"] = out["d22_d26"] = out["h3"] = "NO SE CALCULA EN EL PILOTO"
        out["veredictos"] = {"PILOTO": "sin veredictos de deteccion: el piloto se lee solo en validacion, "
                                       "cobertura, tiempo, memoria y volumen; su lote se vuelve a correr en el despacho completo"}
        return out

    tab_cob, fallas_cob, fallas_cob_d22 = _cobertura(meta, filas, usables)
    out["instrumento"]["cobertura"] = tab_cob
    out["instrumento"]["cobertura_fallas"] = fallas_cob + fallas_cob_d22
    out["instrumento"]["operativo"] = _operativo(filas, tam)

    pub = predicado(ok, predicado_node) if predicado_node else {}

    def P(f, corrida):
        return pub.get((f["clave"], corrida))

    fallas_inst = []
    if duplicadas:
        fallas_inst.append("pasadas duplicadas en la salida: %d claves (ver instrumento.duplicadas)" % len(duplicadas))
    if not identidad_ok:
        fallas_inst.append("identidad: %d de %d pares pasada-campo fallan" % (len(malas_id), n_pc))
    if falla_sd:
        fallas_inst.append(falla_sd)

    # reproduccion del A/B: el acuerdo agregado de antes se informa, pero NO decide
    acuerdo = {}
    for corrida, ref in (("nativo|max", F_PUBLICA), ("nativo|min", B_PUBLICA)):
        xs = [(P(f, corrida), ref[meta[f["clave"]]["grupo"]]) for f in usables if P(f, corrida) is not None]
        acuerdo[corrida] = {"n": len(xs), "acuerdo": (sum(a == b for a, b in xs) / len(xs)) if xs else None}
    out["instrumento"]["acuerdo_agregado_ab_informativo"] = acuerdo

    # gate de reproduccion POR GRUPO (hallazgo 1, punto 1; extendido por V2-2): en cada pasada usable,
    # nativo|max tiene que publicar lo que publico F y nativo|min lo que publico B, en SU grupo primario.
    # Perdidas confiables: maximo 2 fallas. Cualquier otro grupo (conservadas, los tres negativos, la muestra
    # D22): maximo el 5 % del grupo. Las perdidas no confiables no deciden nada y solo se informan. Las perdidas
    # que el nativo reproduce son el denominador de R_L y de la recuperacion de D22.
    perd_conf = [f for f in usables if meta[f["clave"]]["grupo"] == "perdida" and meta[f["clave"]].get("etiqueta_confiable")]
    reproducidas = []
    if predicado_node:
        rep = {}
        for g in sorted({meta[f["clave"]]["grupo"] for f in usables}):
            fs = [f for f in usables if meta[f["clave"]]["grupo"] == g]
            nombre = g
            if g == "perdida":
                fs_nc = [f for f in fs if not meta[f["clave"]].get("etiqueta_confiable")]
                fs = [f for f in fs if meta[f["clave"]].get("etiqueta_confiable")]
                nombre = "perdidas_confiables"
                mal_nc = [f["clave"] for f in fs_nc if P(f, "nativo|max") != F_PUBLICA[g] or P(f, "nativo|min") != B_PUBLICA[g]]
                rep["perdidas_no_confiables_informativo"] = {"n": len(fs_nc), "fallas": len(mal_nc), "ejemplos": mal_nc[:20]}
            mal = []
            for f in fs:
                a, b = P(f, "nativo|max"), P(f, "nativo|min")
                if a == F_PUBLICA[g] and b == B_PUBLICA[g]:
                    if g == "perdida":
                        reproducidas.append(f)
                else:
                    mal.append({"clave": f["clave"], "nativo|max": a, "nativo|min": b})
            maximo = (MAX_FALLAS_REPRO_PERDIDAS if g == "perdida"
                      else int(math.floor(MAX_FRAC_FALLAS_REPRO_CONSERVADAS * len(fs))))
            rep[nombre] = {"n": len(fs), "fallas": len(mal), "maximo": maximo, "ejemplos": mal[:20],
                           "esperado": {"nativo|max": F_PUBLICA[g], "nativo|min": B_PUBLICA[g]}}
            if g == "perdida":
                rep[nombre]["reproducidas"] = len(reproducidas)
            if len(mal) > maximo:
                fallas_inst.append("reproduccion: el nativo no reproduce el A/B en %d de %d pasadas de %s (maximo %d)" % (
                    len(mal), len(fs), nombre, maximo))
        out["instrumento"]["reproduccion_por_grupo"] = rep

    # validacion contra el TIF (con el gate de r_L por pasada)
    info_val, M, falla_val = _validacion(usables, meta)
    out["instrumento"]["validacion_tif"] = info_val["campos"]
    out["instrumento"]["validacion_gate_r_L"] = info_val["gate_r_L"]
    out["instrumento"]["validacion_por_volcan"] = info_val["por_volcan"]
    out["instrumento"]["campo_mirova"] = M

    # ---------------- 1. H1 (sigma del campo), unidad = publicacion por el predicado
    def por_grupo(campo, corrida_nombre, grupo, solo_confiables=False):
        xs = []
        for f in usables:
            m = meta[f["clave"]]
            if m["grupo"] != grupo:
                continue
            if solo_confiables and not m.get("etiqueta_confiable"):
                continue
            xs.append(P(f, "%s|%s" % (campo, corrida_nombre)))
        return _tasa(xs)

    def fp(campo, corrida_nombre):
        tot = sum(totales[g] for g in GRUPOS_NEG); acc = 0.0; ns = {}
        for g in GRUPOS_NEG:
            t, n = por_grupo(campo, corrida_nombre, g)
            ns[g] = n
            if t is None:
                return None, ns
            acc += totales[g] / tot * t
        return acc, ns

    tabla = {}
    if predicado_node:
        for campo in ("nativo", "utm_nn") + CAMPOS_TIF:
            for cn in ("max", "min", "max_sin_compuerta"):
                tabla["%s|%s" % (campo, cn)] = {
                    "recall_perdidas_confiables_absoluto": por_grupo(campo, cn, "perdida", True),
                    "recall_perdidas_todas_absoluto": por_grupo(campo, cn, "perdida"),
                    "conservadas_debiles": por_grupo(campo, cn, "conservada_debil"),
                    "residual_apagado": por_grupo(campo, cn, "residual_apagado"),
                    "residual_sobrevive": por_grupo(campo, cn, "residual_sobrevive"),
                    "negativo_b_no_publica": por_grupo(campo, cn, "negativo_b_no_publica"),
                    "fp_ponderado": fp(campo, cn)}
    # tabla, mecanismo y nulo se calculan aca pero SOLO se escriben en la salida si H1 llega a su regla (V2-3):
    # con un gate caido, una tabla completa se leeria igual que un veredicto con salvedad.
    # mecanismo: razon de sigmas por grupo y AUC del margen z
    mec = {}
    for campo in ("utm_nn",) + CAMPOS_TIF:
        por = collections.defaultdict(lambda: {"sd_dnti": [], "sd_deti": [], "z": [], "fi04": []})
        for f in usables:
            a = (f.get("campos") or {}).get("nativo") or {}; b = (f.get("campos") or {}).get(campo) or {}
            pa, pb = a.get("primer_pase") or {}, b.get("primer_pase") or {}
            g = meta[f["clave"]]["grupo"]
            if pa.get("sd_dnti") and pb.get("sd_dnti"):
                por[g]["sd_dnti"].append(pb["sd_dnti"] / pa["sd_dnti"])
                por[g]["sd_deti"].append(pb["sd_deti"] / pa["sd_deti"])
            por[g]["z"].append(((b.get("decision") or {}).get("max|con_compuerta") or {}).get("z_obj_max"))
            por[g]["fi04"].append(pb.get("frac_var_dnti_termino_i04"))
        mec[campo] = {g: {"razon_sd_dnti_mediana": _med(v["sd_dnti"]), "razon_sd_deti_mediana": _med(v["sd_deti"]),
                          "z_obj_mediana": _med(v["z"]), "frac_var_dnti_i04_mediana": _med(v["fi04"]),
                          "n": len(v["sd_dnti"])} for g, v in por.items()}
        mec[campo]["auc_z_perdidas_vs_residual_apagado"] = _auc(por["perdida"]["z"], por["residual_apagado"]["z"])

    # nulo: fraccion de zonas nulas que pasan con max en M contra nativo con min (control debil, hallazgo 11)
    def nulo(campo, dec):
        xs = []
        for f in usables:
            ev = (f.get("campos") or {}).get(campo) or {}
            d = (ev.get("decision") or {}).get(dec) or {}
            if ev.get("n_zonas_nulas") and d.get("nulo_final") is not None:
                xs.append(d["nulo_final"] / ev["n_zonas_nulas"])
        return {"mediana": _med(xs), "media": (sum(xs) / len(xs) if xs else None), "n": len(xs)}
    nulos = {"nativo|min": nulo("nativo", "min|con_compuerta"), "nativo|max": nulo("nativo", "max|con_compuerta")}
    nulo_ok = None
    if M:
        nulos["%s|max" % M] = nulo(M, "max|con_compuerta")
        a, b = nulos["%s|max" % M]["media"], nulos["nativo|min"]["media"]
        if a is not None and b is not None:
            nulo_ok = a <= b
    # la brecha que el A/B da sobre esta misma muestra, con los pesos de la ventana (V2-2): 766 / 2.324 = 0,330
    tot_neg = sum(totales[g] for g in GRUPOS_NEG)
    brecha_ab = sum(totales[g] * (B_PUBLICA[g] - F_PUBLICA[g]) for g in GRUPOS_NEG) / tot_neg

    def indeterminado(fallas_c, fallas_i):
        if fallas_c and fallas_i:
            return "INDETERMINADO POR COBERTURA E INSTRUMENTO: %s" % "; ".join(fallas_c + fallas_i)
        if fallas_c:
            return "INDETERMINADO POR COBERTURA: %s" % "; ".join(fallas_c)
        return "INDETERMINADO POR INSTRUMENTO: %s" % "; ".join(fallas_i)

    # veredicto H1: primero todos los gates; la regla solo se aplica si pasan todos
    fallas_h1 = list(fallas_inst) + ([("validacion: %s" % falla_val)] if falla_val else [])
    if not predicado_node:
        v1 = "SIN PREDICADO (prueba local)"
    elif fallas_cob or fallas_h1:
        v1 = indeterminado(fallas_cob, fallas_h1)
    else:
        # R_L como contraste DENTRO de la corrida (hallazgo 1, punto 2): sobre las perdidas que el nativo
        # reprodujo (nativo|max no publica), recuperada = M|max publica.
        rl, n_rl = _tasa([P(f, "%s|max" % M) for f in reproducidas])
        fpm, fpn_max, fpn_min = fp(M, "max")[0], fp("nativo", "max")[0], fp("nativo", "min")[0]
        rk_m, n_rk_m = por_grupo(M, "max", "conservada_debil")
        rk_n, n_rk_n = por_grupo("nativo", "max", "conservada_debil")
        if None in (rl, fpm, fpn_max, fpn_min, rk_m, rk_n):
            v1 = "INDETERMINADO POR COBERTURA: faltan grupos para calcular H1"
        else:
            brecha = fpn_min - fpn_max; dfp = fpm - fpn_max
            numeros = {"campo": M, "recall_perdidas_reproducidas": rl, "n_perdidas_reproducidas": n_rl,
                       "fp_M_max": fpm, "fp_nativo_max": fpn_max, "fp_nativo_min": fpn_min,
                       "n_negativos_por_grupo": fp(M, "max")[1], "delta_fp": dfp, "brecha": brecha,
                       "brecha_ab": brecha_ab, "brecha_menos_brecha_ab": brecha - brecha_ab, "brecha_minima": BRECHA_MIN,
                       "conservadas_M_max": rk_m, "conservadas_nativo_max": rk_n, "n_conservadas": n_rk_n,
                       "nulo_ok": nulo_ok}
            # diagnosticos de los dos gates propios de H1 (estos si se escriben aunque fallen)
            out["h1"]["gates_h1"] = {"brecha": brecha, "brecha_ab": brecha_ab, "brecha_minima": BRECHA_MIN,
                                     "conservadas_M_max": rk_m, "conservadas_nativo_max": rk_n, "n_conservadas": n_rk_n,
                                     "tolerancia_conservadas": H1_PERDIDA_CONSERVADAS}
            if brecha < BRECHA_MIN:
                v1 = indeterminado([], ["brecha FP(nativo|min) - FP(nativo|max) = %.3f < %.2f (en el A/B %.3f): el "
                                        "nativo no reproduce lo que `max` compro en falsos" % (brecha, BRECHA_MIN, brecha_ab)])
            elif rk_m < rk_n - H1_PERDIDA_CONSERVADAS:
                # V2-1: un M que no publica las alertas de MIROVA que el nativo publica no es el campo donde
                # MIROVA detecta; su "no recuperar" no dice nada sobre H1. Sin esto un M muerto daba REFUTA.
                v1 = indeterminado([], ["M no publica las alertas de MIROVA que el nativo publica: conservadas %.2f "
                                        "con %s|max contra %.2f con nativo|max (tolerancia %.2f)" % (
                                            rk_m, M, rk_n, H1_PERDIDA_CONSERVADAS)])
            elif rl < H1_RECALL_REFUTA or dfp > H1_DFP_REFUTA * brecha:
                v1 = "REFUTA (R_L %.2f sobre %d perdidas reproducidas; dFP %.3f, brecha %.3f)" % (rl, n_rl, dfp, brecha)
            elif rl >= H1_RECALL_CONFIRMA and dfp <= H1_DFP_CONFIRMA * brecha and rk_m >= rk_n - H1_PERDIDA_CONSERVADAS and nulo_ok:
                v1 = "CONFIRMA (R_L %.2f sobre %d perdidas reproducidas; dFP %.3f, brecha %.3f)" % (rl, n_rl, dfp, brecha)
            else:
                v1 = "INDETERMINADO (R_L %.2f sobre %d; dFP %.3f, brecha %.3f; conservadas %.2f contra %.2f; nulo %s)" % (
                    rl, n_rl, dfp, brecha, rk_m, rk_n, nulo_ok)
            if not v1.startswith("INDETERMINADO POR"):
                # H1 llego a su regla: recien ahora se escriben los numeros de deteccion (V2-3)
                out["h1"]["numeros"] = numeros
                out["h1"]["mecanismo"] = mec
                out["h3"]["tabla"] = tabla
                out["instrumento"]["nulo"] = nulos
    out["veredictos"]["H1_sigma_del_campo"] = v1
    if "tabla" not in out["h3"]:
        out["h3"] = "NO SE ESCRIBE: H1 no llego a su regla (gate caido); ver instrumento"
        out["h1"].setdefault("mecanismo", "NO SE ESCRIBE: H1 no llego a su regla (gate caido)")

    # ---------------- 2. D22 y D26 por separado (campo nativo; y en M si existe)
    negd22 = set((negativos_d22 or {}).get("camino_d22") or [])
    perd_d22 = [f for f in perd_conf if meta[f["clave"]].get("camino_b") == "d22"]
    repro_ids = {f["clave"] for f in reproducidas}
    perd_d22_rep = [f for f in perd_d22 if f["clave"] in repro_ids]
    muestra = [f for f in usables if "muestra_negativos_d22" in _grupos(meta[f["clave"]])]
    dd = {"n_perdidas_d22_confiables_usables": len(perd_d22), "n_perdidas_d22_reproducidas": len(perd_d22_rep),
          "n_muestra_negativos_d22": len(muestra),
          "muestra_en_lista_congelada": (all(f["clave"] in negd22 for f in muestra) if negd22 else None)}
    # control positivo que FRENA (hallazgo 9, D22): nativo|min publica TODAS las perdidas D22 usables
    fallas_d22 = []
    if predicado_node:
        no_pub_min = [f["clave"] for f in perd_d22 if P(f, "nativo|min") != 1]
        dd["control_positivo_nativo_min"] = {"n": len(perd_d22), "no_publica": len(no_pub_min),
                                            "maximo": MAX_FALLAS_CTRL_POS_D22, "ejemplos": no_pub_min}
        if len(no_pub_min) > MAX_FALLAS_CTRL_POS_D22:
            fallas_d22.append("control positivo: nativo|min no publica %d de %d perdidas D22 (maximo %d)" % (
                len(no_pub_min), len(perd_d22), MAX_FALLAS_CTRL_POS_D22))
    # V2-6: la cobertura de D22 se aplica a las perdidas sobre las que se DECIDE (las reproducidas), no solo a
    # las usables: el gate general tolera 2 perdidas no reproducidas que pueden ser todas del camino D22.
    fallas_cob_d22_rep = []
    esp_d22 = tab_cob["perdida_confiable_d22"]["esperadas"]
    if predicado_node and esp_d22 - len(perd_d22_rep) > MAX_FALTAN_PERDIDAS_D22:
        fallas_cob_d22_rep.append("D22 decide sobre %d perdidas reproducidas de %d (pueden faltar %d)" % (
            len(perd_d22_rep), esp_d22, MAX_FALTAN_PERDIDAS_D22))
    for campo in ("nativo",) + ((M,) if M else ()):
        variantes = {}
        if predicado_node:
            # verificador D22 H3 c: cuenta solo si la variante publica Y el `max` de ESTE run (este campo) no
            def nuevo(f):
                a, b = P(f, "%s|max_sin_compuerta" % campo), P(f, "%s|max" % campo)
                return None if a is None or b is None else int(bool(a) and not b)
            rec = _tasa([nuevo(f) for f in perd_d22_rep])
            rea = _tasa([nuevo(f) for f in muestra])
            noches = _tasa([nuevo(f) for f in perd_d22_rep if not meta[f["clave"]].get("f_publica_otra_pasada_esa_noche")])
            variantes["D22_predicado"] = {"recupera": rec, "reabre": rea, "recupera_noches_nuevas": noches,
                                          "max_de_este_run_ya_publica_perdidas": _tasa([P(f, "%s|max" % campo) for f in perd_d22_rep]),
                                          "control_positivo_min_publica": _tasa([P(f, "%s|min" % campo) for f in perd_d22])}
        variantes["base_max_con_compuerta_tests"] = {
            "objetivo_ya_activo": _tasa([_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_cc") for f in perd_d22_rep])}
        # nivel tests (offline, pixel a pixel): D22, D26 y D22+D26
        for nombre, col in (("D22_tests", "final_max_sc"), ("D26_tests", "final_d26_max_cc"), ("D22_D26_tests", "final_d26_max_sc")):
            rec = _tasa([_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), col, "max_cc") for f in perd_d22_rep])
            rea = _tasa([_nuevo_en_cumbre(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), col) for f in muestra])
            variantes[nombre] = {"recupera": rec, "reabre": rea}
        if predicado_node:
            pares = [(_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_sc", "max_cc"), nuevo(f))
                     for f in perd_d22_rep] + [(_nuevo_en_cumbre(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_sc"), nuevo(f))
                                               for f in muestra]
            pares = [(a, b) for a, b in pares if a is not None and b is not None]
            variantes["acuerdo_tests_predicado_D22"] = {"acuerdo": (sum(a == b for a, b in pares) / len(pares)) if pares else None,
                                                        "n": len(pares)}
        ver = {}
        # gates de D22: los del instrumento (salvo la validacion del TIF, que solo importa en M), cobertura
        # propia (sobre las reproducidas) y control positivo. Si falla alguno, ninguna variante tiene veredicto
        # y sus tasas NO se escriben (V2-3).
        f_c = fallas_cob + fallas_cob_d22 + fallas_cob_d22_rep
        f_i = list(fallas_inst) + fallas_d22 + (["validacion: %s" % falla_val] if (campo != "nativo" and falla_val) else [])
        if muestra and negd22 and not dd["muestra_en_lista_congelada"]:
            f_i.append("la muestra de negativos D22 no es la lista congelada")
        dd[campo] = variantes if not (f_c or f_i) else "NO SE ESCRIBE: gate caido; ver el veredicto"
        for nombre, v in variantes.items():
            if not isinstance(v, dict) or "recupera" not in v:
                continue
            r, a = v["recupera"][0], v["reabre"][0]
            nr, na = v["recupera"][1], v["reabre"][1]
            if not predicado_node and nombre == "D22_predicado":
                continue
            if f_c or f_i:
                ver[nombre] = indeterminado(f_c, f_i)
            elif r is None or a is None:
                ver[nombre] = "INDETERMINADO POR COBERTURA: faltan pasadas (n recupera %d, n reabre %d)" % (nr, na)
            elif r < D22_RECUP:
                ver[nombre] = "NO RECUPERA (%.2f de %d perdidas D22 reproducidas)" % (r, nr)
            elif a >= D22_REAPERTURA:
                ver[nombre] = "NO ES EL ARREGLO: recupera %.2f de %d pero reabre %.2f de %d negativos del camino" % (r, nr, a, na)
            else:
                ver[nombre] = "SELECTIVO: recupera %.2f de %d y reabre %.2f de %d" % (r, nr, a, na)
        out["veredictos"]["D22_D26_%s" % campo] = ver
    out["d22_d26"] = dd
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sin-predicado", action="store_true")
    ap.add_argument("--piloto", action="store_true",
                    help="solo cobertura, identidad, tiempo, memoria, volumen y validacion contra el TIF; sin predicado ni veredictos")
    a = ap.parse_args()
    sel = json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))
    meta = {p["clave"]: p for p in sel["pasadas"]}
    negd22 = json.loads((AQUI / "negativos_camino_d22.json").read_text(encoding="utf-8"))
    rutas = sorted(p for p in Path(a.out).rglob("*.json")
                   if not p.name.startswith("cobertura_") and p.name != "evaluacion.json")
    usar_pred = not (a.sin_predicado or a.piloto)
    if not a.sin_predicado:
        # tambien en el piloto (V2-9): ejercita las importaciones de banco_paridad y node con los casos de
        # control del predicado, que no miran ningun dato de la sonda
        import banco_paridad as bp
        validos, pubs = bp.control_identidad_predicado()
        print("control del predicado: isValidDetection", validos, "| publicacion", pubs, "(esperado [1, 0])")
        if list(pubs) != [1, 0]:
            raise SystemExit("el predicado del tablero no da lo esperado en sus casos de control: no se evalua")
    res = evaluar(rutas, meta, sel["totales_ventana"], predicado_node=usar_pred, negativos_d22=negd22, piloto=a.piloto)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    (Path(a.out) / "evaluacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nVEREDICTOS:")
    for k, v in res["veredictos"].items():
        print("  %s: %s" % (k, v))


if __name__ == "__main__":
    main()
