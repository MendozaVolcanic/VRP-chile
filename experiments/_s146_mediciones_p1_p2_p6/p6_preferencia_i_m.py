# -*- coding: utf-8 -*-
"""P6 (S146): que le haria a la publicacion la regla de Coppola 2026 (Scientific Data, PDF p. 7 de 25,
seccion "Data aggregation", 3.er parrafo) sobre detecciones VIIRS coincidentes. SOLO LECTURA.

LA REGLA, TAL COMO EL PAPER LA DICE (verificada renderizando la pagina a imagen, _cache/p6_pag7.png):
  "VIIRS 375 m detections without corresponding VIIRS 750 m observations were retained, as were
   VIIRS 750 m detections without corresponding 375 m observations. For coincident VIIRS detections,
   the 750 m observation was retained because ... I4 channel (375 m) is more prone to pixel saturation"
Es una regla de DEDUPLICACION entre DETECCIONES de un archivo FILTRADO (A105: no es el NRT): si las
dos bandas detectan en el mismo paso queda la de 750 m; si detecta una sola, queda esa. NO es un veto
(no dice "si 750 m miro y no vio nada, se descarta la de 375 m").

QUE MIDE. Pasos VIIRS = (volcan, plataforma, datetime_utc) con record de banda I y/o de banda M, en la
ventana del regimen actual (2026-09-01 a 2026-09-20), con etiquetas y predicado del banco de S145
(se importa la carga de la Fase 1). Tres combinaciones, por PASO:
  HOY        : el paso cuenta como publicado si publica la I o la M (lo que ve el operador hoy).
  L1_PAPER   : la regla del paper (union deduplicada; si coinciden, representa la M).
  L2_VETO    : NO ESTA EN EL PAPER. La lectura que reduciria publicacion: la I solo vale si la M del
               mismo paso tambien publica. Se mide para saber cuanto costaria/rendiria, rotulada.
Etiqueta del paso: pos si alguna de sus bandas es pos; neg_limpio si ninguna es pos ni far_ref y al
menos una es neg_limpio; el resto, otro. Se reporta tambien con la etiqueta SOLO de la banda I.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  (1) Si lo que mido estuviera roto, fallaria? Control positivo: 0,8633 (n 373) y 0,2138 (n 622) por
      banda con mi carga, o ABORTA. Y HOY == L1_PAPER en publicacion por construccion: si difieren, bug.
  (2) Si el instrumento estuviera muerto, se veria distinto? Si el pareo I-M no encontrara pares
      (nombres de sensor o minutos distintos), n_pasos_con_ambas seria 0 y L2 == HOY: se imprime el
      conteo de pares y la distribucion del desfase antes de todo. Nulo de L2: se baraja, dentro de
      cada volcan, cual paso M acompana a cada paso I (rompe la coincidencia fisica, conserva las tasas).
"""
from __future__ import annotations
import collections
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "_s146_fase1_sustrato"))
import sustrato_caminos as sc  # noqa: E402
bp = sc.bp
AQUI = Path(__file__).resolve().parent
N_NULO = 1000


def lab_paso(i, m):
    labs = [x["lab"] for x in (i, m) if x is not None]
    if "pos" in labs:
        return "pos"
    if "far_ref" in labs:
        return "far_ref"
    if "neg_limpio" in labs:
        return "neg_limpio"
    return "sin_info"


def tasas(pasos, etiqueta, regla):
    sel = [p for p in pasos if p[etiqueta] == "neg_limpio"]
    return {"n": len(sel), "pub": sum(p[regla] for p in sel), "tasa": bp._tasa(sum(p[regla] for p in sel), len(sel))}


def noches(pasos, regla, modis_pub):
    nn = collections.defaultdict(list)
    for p in pasos:
        nn[(p["vol"], p["noche"])].append(p)
    pos = {k: v for k, v in nn.items() if any(p["lab"] == "pos" for p in v)}
    pub = {k for k, v in pos.items() if any(p[regla] for p in v)}
    pub_con_modis = {k for k in pos if k in pub or k in modis_pub}
    return {"n_noches_pos_viirs": len(pos), "publicadas_viirs": len(pub), "publicadas_con_modis": len(pub_con_modis),
            "perdidas_viirs": sorted([k[0], k[1]] for k in pos if k not in pub)}


def main():
    coords = sc._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = sc.cargar_referencia_unificada(sc.REF / "registro_vrp_consolidado.csv", sc.REF / "registro_vrp_ocr.csv")
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, sc.VENTANA)
    recs = sc.cargar(coords, inner)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    ctrl = {}
    for b in ("VIIRS375", "VIIRS750"):
        neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio"]
        ctrl[b] = [len(neg), round(sum(r["pub"] for r in neg) / len(neg), 4)]
    ok = ctrl == {"VIIRS375": [373, 0.8633], "VIIRS750": [622, 0.2138]}
    print("CONTROL POSITIVO", ctrl, "reproduce:", ok)
    if not ok:
        print("ABORTO")
        return 2

    # ---- la referencia NRT, trae filas de las dos bandas para el mismo paso? (deduplica MIROVA en el NRT?)
    ref_t = collections.defaultdict(set)
    for (vol, b), lista in por_vb.items():
        if b in ("VIIRS375", "VIIRS750"):
            for dt, f in lista:
                ref_t[(vol, dt.strftime("%Y-%m-%d %H:%M"))].add(b)
    ref_coinc = collections.Counter(tuple(sorted(v)) for v in ref_t.values())
    # y entre las ALERTAS: cuando MIROVA NRT alerta en una banda, tiene fila de la otra en ese minuto?
    al = collections.Counter()
    for (vol, b), lista in por_vb.items():
        if b not in ("VIIRS375", "VIIRS750"):
            continue
        otra = "VIIRS750" if b == "VIIRS375" else "VIIRS375"
        for dt, f in lista:
            if bp.es_alerta(f["tipo"]):
                fo = bp.parear(por_vb.get((vol, otra), []), dt)
                al[(b, "otra_banda_alerta" if any(bp.es_alerta(x["tipo"]) for x in fo) else ("otra_banda_fila_sin_alerta" if fo else "otra_banda_sin_fila"))] += 1
    print("REFERENCIA NRT minutos con fila por banda:", dict(ref_coinc))
    print("REFERENCIA NRT alertas y la otra banda:", {f"{k[0]}|{k[1]}": v for k, v in al.items()})

    # ---- pasos
    por = collections.defaultdict(dict)
    for r in recs:
        if r["b"] in ("VIIRS375", "VIIRS750"):
            plat = (r["diag"]["sensor"] or "").replace("_750", "")
            por[(r["vol"], plat, r["diag"]["datetime_utc"])][r["b"]] = r
    pasos = []
    for (vol, plat, dtu), d in sorted(por.items()):
        i, m = d.get("VIIRS375"), d.get("VIIRS750")
        p = {"vol": vol, "plat": plat, "dt": dtu, "noche": dtu[:10], "tiene_I": i is not None, "tiene_M": m is not None,
             "pub_I": bool(i and i["pub"]), "pub_M": bool(m and m["pub"]),
             "lab": lab_paso(i, m), "lab_I": i["lab"] if i else None, "lab_M": m["lab"] if m else None}
        p["HOY"] = p["pub_I"] or p["pub_M"]
        p["L1_PAPER"] = p["pub_I"] or p["pub_M"]          # union deduplicada: mismo conjunto de pasos publicados
        p["L1_representa"] = "M" if p["pub_M"] else ("I" if p["pub_I"] else None)
        p["L2_VETO"] = p["pub_M"] or (p["pub_I"] and not p["tiene_M"])
        pasos.append(p)
    cob = collections.Counter(("I" if p["tiene_I"] else "-") + ("M" if p["tiene_M"] else "-") for p in pasos)
    print("PAREO I-M: pasos", len(pasos), dict(cob))
    ambos = [p for p in pasos if p["tiene_I"] and p["tiene_M"]]
    res = {"meta": {"ventana": list(sc.VENTANA), "cita": "Coppola et al. 2026, Scientific Data, s41597-026-08100-7, PDF p. 7 de 25, seccion Data aggregation, 3er parrafo",
                    "imagen_de_la_cita": "_cache/p6_pag7.png (se borra al final; se regenera con fitz page 6, dpi 200)"},
           "control_positivo": ctrl, "referencia_nrt_minutos_por_banda": {"|".join(k): v for k, v in ref_coinc.items()},
           "referencia_nrt_alertas_vs_otra_banda": {f"{k[0]}|{k[1]}": v for k, v in al.items()},
           "pareo": {"n_pasos": len(pasos), "cobertura": dict(cob)}}

    # ---- tabla 2x2 por etiqueta de la banda I
    t22 = {}
    for lab in ("neg_limpio", "pos"):
        sel = [p for p in ambos if p["lab_I"] == lab]
        t22[lab] = {"n": len(sel), "I_si_M_si": sum(p["pub_I"] and p["pub_M"] for p in sel), "I_si_M_no": sum(p["pub_I"] and not p["pub_M"] for p in sel),
                    "I_no_M_si": sum(p["pub_M"] and not p["pub_I"] for p in sel), "I_no_M_no": sum(not p["pub_I"] and not p["pub_M"] for p in sel),
                    "lab_M": dict(collections.Counter(p["lab_M"] for p in sel))}
    res["tabla_2x2_pasos_con_ambas_bandas_por_etiqueta_de_I"] = t22
    print("2x2 (etiqueta de la banda I):", json.dumps(t22, ensure_ascii=False))

    # ---- reglas
    modis_pub = {(r["vol"], r["noche"]) for r in recs if r["b"] == "MODIS" and r["pub"]}
    reglas = {}
    for regla in ("HOY", "L1_PAPER", "L2_VETO"):
        reglas[regla] = {"neg_limpio_por_paso(etiqueta_del_paso)": tasas(pasos, "lab", regla),
                         "neg_limpio_por_paso(etiqueta_de_I)": tasas([p for p in pasos if p["tiene_I"]], "lab_I", regla),
                         "noches": noches(pasos, regla, modis_pub),
                         "por_volcan": {v: {"neg": tasas([p for p in pasos if p["vol"] == v], "lab", regla),
                                            "noches": {k: x for k, x in noches([p for p in pasos if p["vol"] == v], regla, modis_pub).items() if k != "perdidas_viirs"}}
                                        for v in bp.VOLS}}
    res["reglas"] = reglas
    # records que deja de mostrar la L1 (duplicados I cuando M tambien publica)
    res["L1_records_I_reemplazados_por_M"] = {lab: sum(1 for p in ambos if p["lab"] == lab and p["pub_I"] and p["pub_M"]) for lab in ("neg_limpio", "pos", "sin_info", "far_ref")}
    res["L1_cambia_pasos_publicados"] = sum(1 for p in pasos if p["HOY"] != p["L1_PAPER"])

    # ---- nulo de L2: barajar dentro de volcan que M acompana a cada I
    rng = random.Random(146)
    selI = [p for p in ambos if p["lab_I"] in ("neg_limpio", "pos")]
    por_vol = collections.defaultdict(list)
    for p in selI:
        por_vol[p["vol"]].append(p)

    def stat(pubM):
        neg = [(p, m) for p, m in pubM if p["lab_I"] == "neg_limpio" and p["pub_I"]]
        pos = [(p, m) for p, m in pubM if p["lab_I"] == "pos" and p["pub_I"]]
        a = sum(1 for p, m in neg if not m) / len(neg) if neg else None      # frac de I publicadas en neg que el veto borra
        b = sum(1 for p, m in pos if not m) / len(pos) if pos else None      # idem en pos
        return a, b
    obs = stat([(p, p["pub_M"]) for p in selI])
    dif = []
    for _ in range(N_NULO):
        pares = []
        for ps in por_vol.values():
            ms = [p["pub_M"] for p in ps]
            rng.shuffle(ms)
            pares += list(zip(ps, ms))
        a, b = stat(pares)
        dif.append(a - b)
    dif.sort()
    res["nulo_L2"] = {"frac_I_neg_borradas": round(obs[0], 4), "frac_I_pos_borradas": round(obs[1], 4), "contraste_obs": round(obs[0] - obs[1], 4),
                      "nulo_media": round(sum(dif) / N_NULO, 4), "nulo_p2.5": round(dif[25], 4), "nulo_p97.5": round(dif[974], 4),
                      "fuera_del_nulo": bool(obs[0] - obs[1] < dif[25] or obs[0] - obs[1] > dif[974])}

    for regla in reglas:
        x = reglas[regla]
        print(f"== {regla}: neg por paso {x['neg_limpio_por_paso(etiqueta_del_paso)']} | con etiqueta de I {x['neg_limpio_por_paso(etiqueta_de_I)']} | noches {x['noches']}")
    print("L1 cambia pasos publicados:", res["L1_cambia_pasos_publicados"], "| records I reemplazados por M:", res["L1_records_I_reemplazados_por_M"])
    print("NULO L2:", res["nulo_L2"])
    print("L2 por volcan:", json.dumps({v: x for v, x in reglas["L2_VETO"]["por_volcan"].items()}, ensure_ascii=False))
    print("HOY por volcan:", json.dumps({v: x for v, x in reglas["HOY"]["por_volcan"].items()}, ensure_ascii=False))
    (AQUI / "p6_resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
