# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: evaluador con el criterio PRE-REGISTRADO en DISENO.md §6 a §8.

Lee las salidas por pasada (out/*.json de todos los lotes), corre el predicado del tablero con node
sobre el record persistido de cada corrida (A97: "publicamos" es el predicado del operador, no uno
reconstruido a mano) y aplica las reglas en este orden:
  0. el instrumento (cobertura, identidad con las funciones reales, reproduccion del A/B, validacion del
     campo contra el GeoTIFF de MIROVA, nulo). Si el instrumento no pasa, los veredictos se imprimen como
     INDETERMINADO POR INSTRUMENTO y no se leen.
  1. H1, la sigma del campo.
  2. D22 y D26, por separado y juntas.
  3. H3, la tabla de las dos conectivas en cada campo.

  python evaluar.py --out <carpeta con los json de todos los lotes> [--sin-predicado]

Ninguna regla de aca se cambia despues de ver datos de la sonda: el sha256 de DISENO.md y de este
archivo queda sellado en el pre-registro antes del despacho.
"""
import argparse, collections, io, json, math, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

CAMPOS_TIF = ("tif_lin", "tif_cub", "tif_nn")
# Umbrales pre-registrados (DISENO.md §6 a §8). Su origen esta explicado ahi.
VALIDA_R_DL = 0.80
VALIDA_S_RATIO = (0.80, 1.25)
UMBRAL_IDENTIDAD = 1e-9
FRAC_MAX_FALLA_IDENTIDAD = 0.05
ACUERDO_MIN_AB = 0.95
H1_RECALL_CONFIRMA = 0.50
H1_RECALL_REFUTA = 0.25
H1_DFP_CONFIRMA = 0.25      # fraccion de la brecha FP(min) - FP(max) del nativo que se tolera devolver
H1_DFP_REFUTA = 0.50
H1_PERDIDA_CONSERVADAS = 0.10
D22_RECUP = 0.50
D22_REAPERTURA = 0.25
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


def evaluar(rutas, pasadas_meta, totales, predicado_node=True, negativos_d22=None):
    filas = [json.loads(Path(r).read_text(encoding="utf-8")) for r in rutas]
    filas = [f for f in filas if f.get("clave") in pasadas_meta]
    out = {"instrumento": {}, "h1": {}, "d22_d26": {}, "h3": {}, "veredictos": {}}
    meta = pasadas_meta

    def grupos_de(f):
        m = meta[f["clave"]]
        return m.get("grupos") or [m["grupo"]]

    # ---------------- 0. instrumento
    ok = [f for f in filas if f.get("ok")]
    cob = collections.Counter(); cob_ok = collections.Counter()
    for f in filas:
        for g in grupos_de(f):
            cob[g] += 1; cob_ok[g] += bool(f.get("ok"))
    esperadas = collections.Counter(g for m in meta.values() for g in (m.get("grupos") or [m["grupo"]]))
    out["instrumento"]["cobertura"] = {g: {"esperadas": esperadas[g], "con_salida": cob[g], "completas": cob_ok[g]}
                                       for g in esperadas}
    malas_id = []
    for f in ok:
        for campo, ev in (f.get("campos") or {}).items():
            idp = ev.get("identidad_primer_pase") or {}
            bien = (all(v is not None and v < UMBRAL_IDENTIDAD for v in idp.values()) and ev.get("identidad_n_pool")
                    and all(d.get("identidad_hot_1") for d in (ev.get("decision") or {}).values())
                    and all(d.get("identidad_final") is not False for d in (ev.get("decision") or {}).values()))
            if not bien:
                malas_id.append((f["clave"], campo))
    n_pc = sum(len(f.get("campos") or {}) for f in ok)
    out["instrumento"]["identidad"] = {"pares_pasada_campo": n_pc, "fallan": len(malas_id), "ejemplos": malas_id[:10]}
    excluir = {k for k, _ in malas_id}
    instrumento_ok = n_pc > 0 and len(malas_id) <= FRAC_MAX_FALLA_IDENTIDAD * n_pc

    pub = predicado(ok, predicado_node) if predicado_node else {}
    usables = [f for f in ok if f["clave"] not in excluir]

    def P(f, corrida):
        return pub.get((f["clave"], corrida))

    # reproduccion del A/B
    acuerdo = {}
    for corrida, ref in (("nativo|max", F_PUBLICA), ("nativo|min", B_PUBLICA)):
        xs = [(P(f, corrida), ref[meta[f["clave"]]["grupo"]]) for f in usables if P(f, corrida) is not None]
        acuerdo[corrida] = {"n": len(xs), "acuerdo": (sum(a == b for a, b in xs) / len(xs)) if xs else None,
                            "desacuerdos": [f["clave"] for f in usables if P(f, corrida) is not None
                                            and P(f, corrida) != ref[meta[f["clave"]]["grupo"]]][:20]}
    out["instrumento"]["reproduccion_ab"] = acuerdo
    out["instrumento"]["mismo_granulo_que_ab"] = _tasa([int(bool(f.get("mismo_granulo_que_ab"))) for f in usables])
    rel_sd = []
    for f in usables:
        ev = (f.get("campos") or {}).get("nativo") or {}
        sd = (ev.get("primer_pase") or {}).get("sd_dnti"); sd_ab = (meta[f["clave"]].get("B") or {}).get("diag_sd_dnti")
        if sd and sd_ab:
            rel_sd.append(abs(sd - sd_ab) / sd_ab)
    out["instrumento"]["sd_dnti_nativo_vs_record_ab"] = {"n": len(rel_sd), "frac_bajo_1e-6": (sum(x < 1e-6 for x in rel_sd) / len(rel_sd)) if rel_sd else None,
                                                         "mediana_rel": _med(rel_sd)}
    reproduce_ab = all(v["acuerdo"] is not None and v["acuerdo"] >= ACUERDO_MIN_AB for v in acuerdo.values()) if predicado_node else None

    # validacion contra el TIF
    val = {}
    for c in CAMPOS_TIF:
        vs = [f["validacion_tif"][c] for f in usables if (f.get("validacion_tif") or {}).get(c, {}).get("ok")]
        r = _med([v["r_dL"] for v in vs]); s_ = _med([v["s_ratio"] for v in vs])
        val[c] = {"n_pasadas_con_tif": len(vs), "r_L_mediana": _med([v["r_L"] for v in vs]), "r_dL_mediana": r,
                  "s_ratio_mediana": s_, "rel_mediana": _med([v["rel_mediana"] for v in vs]),
                  "ac1_dL_campo_mediana": _med([v.get("ac1_dL_campo") for v in vs]),
                  "ac1_dL_tif_mediana": _med([v.get("ac1_dL_tif") for v in vs]),
                  "valido": bool(vs) and r is not None and s_ is not None and r >= VALIDA_R_DL
                  and VALIDA_S_RATIO[0] <= s_ <= VALIDA_S_RATIO[1]}
    out["instrumento"]["validacion_tif"] = val
    validos = [c for c in CAMPOS_TIF if val[c]["valido"]]
    M = max(validos, key=lambda c: (val[c]["r_dL_mediana"], -abs(math.log(val[c]["s_ratio_mediana"])))) if validos else None
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
        tot = sum(totales[g] for g in GRUPOS_NEG); acc = 0.0
        for g in GRUPOS_NEG:
            t, n = por_grupo(campo, corrida_nombre, g)
            if t is None:
                return None
            acc += totales[g] / tot * t
        return acc

    tabla = {}
    for campo in ("nativo", "utm_nn") + CAMPOS_TIF:
        for cn in ("max", "min", "max_sin_compuerta"):
            tabla["%s|%s" % (campo, cn)] = {
                "recall_perdidas_confiables": por_grupo(campo, cn, "perdida", True),
                "recall_perdidas_todas": por_grupo(campo, cn, "perdida"),
                "conservadas_debiles": por_grupo(campo, cn, "conservada_debil"),
                "residual_apagado": por_grupo(campo, cn, "residual_apagado"),
                "residual_sobrevive": por_grupo(campo, cn, "residual_sobrevive"),
                "negativo_b_no_publica": por_grupo(campo, cn, "negativo_b_no_publica"),
                "fp_ponderado": fp(campo, cn)}
    out["h3"]["tabla"] = tabla
    # mecanismo: razon de sigmas por grupo y AUC del margen z
    mec = {}
    for campo in ("utm_nn",) + CAMPOS_TIF:
        por = collections.defaultdict(lambda: {"sd_dnti": [], "sd_deti": [], "z": []})
        for f in usables:
            a = (f.get("campos") or {}).get("nativo") or {}; b = (f.get("campos") or {}).get(campo) or {}
            pa, pb = a.get("primer_pase") or {}, b.get("primer_pase") or {}
            g = meta[f["clave"]]["grupo"]
            if pa.get("sd_dnti") and pb.get("sd_dnti"):
                por[g]["sd_dnti"].append(pb["sd_dnti"] / pa["sd_dnti"])
                por[g]["sd_deti"].append(pb["sd_deti"] / pa["sd_deti"])
            por[g]["z"].append(((b.get("decision") or {}).get("max|con_compuerta") or {}).get("z_obj_max"))
        mec[campo] = {g: {"razon_sd_dnti_mediana": _med(v["sd_dnti"]), "razon_sd_deti_mediana": _med(v["sd_deti"]),
                          "z_obj_mediana": _med(v["z"]), "n": len(v["sd_dnti"])} for g, v in por.items()}
        mec[campo]["auc_z_perdidas_vs_residual_apagado"] = _auc(por["perdida"]["z"], por["residual_apagado"]["z"])
    out["h1"]["mecanismo"] = mec
    # nulo: fraccion de zonas nulas que pasan con max en M contra nativo con min
    def nulo(campo, dec):
        xs = []
        for f in usables:
            ev = (f.get("campos") or {}).get(campo) or {}
            d = (ev.get("decision") or {}).get(dec) or {}
            if ev.get("n_zonas_nulas") and d.get("nulo_final") is not None:
                xs.append(d["nulo_final"] / ev["n_zonas_nulas"])
        return _med(xs), (sum(xs) / len(xs) if xs else None)
    out["instrumento"]["nulo"] = {"nativo|min": nulo("nativo", "min|con_compuerta"), "nativo|max": nulo("nativo", "max|con_compuerta")}
    if M:
        out["instrumento"]["nulo"]["%s|max" % M] = nulo(M, "max|con_compuerta")
    nulo_ok = None
    if M and out["instrumento"]["nulo"]["%s|max" % M][1] is not None and out["instrumento"]["nulo"]["nativo|min"][1] is not None:
        nulo_ok = out["instrumento"]["nulo"]["%s|max" % M][1] <= out["instrumento"]["nulo"]["nativo|min"][1]

    # veredicto H1
    if not instrumento_ok:
        v1 = "INDETERMINADO POR INSTRUMENTO (identidad)"
    elif M is None:
        v1 = "INDETERMINADO POR INSTRUMENTO (ningun campo interpolado reproduce el TIF de MIROVA)"
    elif not predicado_node:
        v1 = "SIN PREDICADO (prueba local)"
    else:
        rl = tabla["%s|max" % M]["recall_perdidas_confiables"][0]
        fpm, fpn_max, fpn_min = tabla["%s|max" % M]["fp_ponderado"], tabla["nativo|max"]["fp_ponderado"], tabla["nativo|min"]["fp_ponderado"]
        rk_m, rk_n = tabla["%s|max" % M]["conservadas_debiles"][0], tabla["nativo|max"]["conservadas_debiles"][0]
        if None in (rl, fpm, fpn_max, fpn_min, rk_m, rk_n):
            v1 = "INDETERMINADO (faltan grupos)"
        else:
            brecha = fpn_min - fpn_max; dfp = fpm - fpn_max
            out["h1"]["numeros"] = {"campo": M, "recall_perdidas_confiables": rl, "fp_M_max": fpm, "fp_nativo_max": fpn_max,
                                    "fp_nativo_min": fpn_min, "delta_fp": dfp, "brecha": brecha,
                                    "conservadas_M_max": rk_m, "conservadas_nativo_max": rk_n, "nulo_ok": nulo_ok}
            if rl < H1_RECALL_REFUTA or dfp > H1_DFP_REFUTA * brecha:
                v1 = "REFUTA"
            elif rl >= H1_RECALL_CONFIRMA and dfp <= H1_DFP_CONFIRMA * brecha and rk_m >= rk_n - H1_PERDIDA_CONSERVADAS and nulo_ok:
                v1 = "CONFIRMA"
            else:
                v1 = "INDETERMINADO"
    if reproduce_ab is False and v1 in ("CONFIRMA", "REFUTA"):
        v1 += " (con salvedad: el nativo no reproduce el A/B en %s; ver instrumento)" % \
              [k for k, v in acuerdo.items() if (v["acuerdo"] or 0) < ACUERDO_MIN_AB]
    out["veredictos"]["H1_sigma_del_campo"] = v1

    # ---------------- 2. D22 y D26 por separado (campo nativo; y en M si existe)
    negd22 = set((negativos_d22 or {}).get("camino_d22") or [])
    perd_d22 = [f for f in usables if meta[f["clave"]]["grupo"] == "perdida" and meta[f["clave"]].get("camino_b") == "d22"
                and meta[f["clave"]].get("etiqueta_confiable")]
    muestra = [f for f in usables if "muestra_negativos_d22" in (meta[f["clave"]].get("grupos") or [])]
    dd = {"n_perdidas_d22_confiables": len(perd_d22), "n_muestra_negativos_d22": len(muestra),
          "muestra_en_lista_congelada": (all(f["clave"] in negd22 for f in muestra) if negd22 else None)}
    for campo in ("nativo",) + ((M,) if M else ()):
        variantes = {}
        # nivel predicado (corrida real): solo D22
        if predicado_node:
            # verificador D22 H3 c: cuenta solo si la variante publica Y el `max` de ESTE run no publica
            def nuevo(f):
                a, b = P(f, "%s|max_sin_compuerta" % campo), P(f, "%s|max" % campo)
                return None if a is None or b is None else int(bool(a) and not b)
            rec = _tasa([nuevo(f) for f in perd_d22])
            rea = _tasa([nuevo(f) for f in muestra])
            noches = _tasa([nuevo(f) for f in perd_d22 if not meta[f["clave"]].get("f_publica_otra_pasada_esa_noche")])
            variantes["D22_predicado"] = {"recupera": rec, "reabre": rea, "recupera_noches_nuevas": noches,
                                          "max_de_este_run_ya_publica_perdidas": _tasa([P(f, "%s|max" % campo) for f in perd_d22]),
                                          # control positivo (A116): con `min` estas perdidas se publican (B las publico);
                                          # si aca no, el instrumento no puede ver una recuperacion y el cero no vale
                                          "control_positivo_min_publica": _tasa([P(f, "%s|min" % campo) for f in perd_d22])}
        variantes["base_max_con_compuerta_tests"] = {
            "objetivo_ya_activo": _tasa([_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_cc") for f in perd_d22])}
        # nivel tests (offline, pixel a pixel): D22, D26 y D22+D26
        for nombre, col in (("D22_tests", "final_max_sc"), ("D26_tests", "final_d26_max_cc"), ("D22_D26_tests", "final_d26_max_sc")):
            rec = _tasa([_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), col, "max_cc") for f in perd_d22])
            rea = _tasa([_nuevo_en_cumbre(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), col) for f in muestra])
            variantes[nombre] = {"recupera": rec, "reabre": rea}
        # control del proxy: tests contra predicado en la misma variante (D22, donde existen los dos)
        if predicado_node:
            pares = [(_objetivo(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_sc", "max_cc"), nuevo(f))
                     for f in perd_d22] + [(_nuevo_en_cumbre(((f.get("campos") or {}).get(campo) or {}).get("pixeles"), "final_max_sc"), nuevo(f))
                                           for f in muestra]
            pares = [(a, b) for a, b in pares if a is not None and b is not None]
            variantes["acuerdo_tests_predicado_D22"] = (sum(a == b for a, b in pares) / len(pares)) if pares else None
        dd[campo] = variantes
        ver = {}
        for nombre, v in variantes.items():
            if not isinstance(v, dict) or "recupera" not in v:
                continue
            r, a = v["recupera"][0], v["reabre"][0]
            if r is None or a is None:
                ver[nombre] = "INDETERMINADO (faltan pasadas)"
            elif r < D22_RECUP:
                ver[nombre] = "NO RECUPERA (%.2f de las perdidas del camino D22)" % r
            elif a >= D22_REAPERTURA:
                ver[nombre] = "NO ES EL ARREGLO: recupera %.2f pero reabre %.2f de los negativos del camino" % (r, a)
            else:
                ver[nombre] = "SELECTIVO: recupera %.2f y reabre %.2f" % (r, a)
        out["veredictos"]["D22_D26_%s" % campo] = ver
    out["d22_d26"] = dd
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sin-predicado", action="store_true")
    a = ap.parse_args()
    sel = json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))
    meta = {p["clave"]: p for p in sel["pasadas"]}
    negd22 = json.loads((AQUI / "negativos_camino_d22.json").read_text(encoding="utf-8"))
    rutas = sorted(p for p in Path(a.out).rglob("*.json") if not p.name.startswith("cobertura_"))
    if not a.sin_predicado:
        import banco_paridad as bp
        validos, pubs = bp.control_identidad_predicado()
        print("control del predicado: isValidDetection", validos, "| publicacion", pubs, "(esperado [1, 0])")
        if list(pubs) != [1, 0]:
            raise SystemExit("el predicado del tablero no da lo esperado en sus casos de control: no se evalua")
    res = evaluar(rutas, meta, sel["totales_ventana"], predicado_node=not a.sin_predicado, negativos_d22=negd22)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    (Path(a.out) / "evaluacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\nVEREDICTOS:")
    for k, v in res["veredictos"].items():
        print("  %s: %s" % (k, v))


if __name__ == "__main__":
    main()
