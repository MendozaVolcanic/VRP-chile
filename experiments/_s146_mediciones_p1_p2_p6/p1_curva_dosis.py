# -*- coding: utf-8 -*-
"""P1 (S146): curva de dosis del Test 1 integrado. SOLO LECTURA.

QUE MIDE. Reutiliza la carga, las etiquetas, el predicado del dashboard (node) y la clase de sosten
de experiments/_s146_fase1_sustrato/sustrato_caminos.py (importado, no copiado). Para cada umbral k
pregunta, sobre lo PERSISTIDO: si el Test 1 exigiera k sigmas en vez de 3, que pasadas publicadas
quedarian sin sosten y que noches positivas perderian el suyo.

QUE SUPONE (es una cota, no una simulacion de la etapa siguiente):
  S1. k solo entra en abs_criterion = delta_L > k * sigma (pipeline/test1_integrated.py l. 435):
      una pasada con test1_k_observed > k queda IDENTICA (mismo cumulo, misma magnitud). Exacto.
  S2. una pasada T1_SOLO con k_obs <= k queda sin Test 1 y, por la logica de la Fase 1, sin
      publicarse. NO se re-ejecuta el ensamblado: se hereda el supuesto de la Fase 1.
  S3. una pasada T1_SOBRE_CTX con k_obs <= k es SIN DATO (no se persiste la magnitud del cumulo
      contextual que quedaria). AMBOS y CTX_SOLO no dependen del Test 1: siguen.
  S4. subir k no hace publicar nada que hoy no se publica (no medido: SOSPECHA razonable).
  S5. test1_k_observed esta redondeado a 2 decimales y 0.0 significa "no calculado O cero".

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  (1) Si lo que mido estuviera roto, fallaria? Control positivo: a k = 3 la curva tiene que dar
      CERO caidas (todo disparo tiene k_obs > 3). Y antes: 0,8633/373, 0,2138/622, 186/322 y
      89/133 con mi carga; si no, ABORTA. Y toda pasada con triggered_test1 True debe tener
      k_obs > 3: se cuenta cuantas no.
  (2) Si el instrumento estuviera muerto, se veria distinto? Si test1_k_observed fuera constante o
      no existiera en un sensor, la curva seria un escalon (todo cae al mismo k) o plana en cero:
      se reporta cobertura y cuantiles por sensor ANTES de la curva. El nulo baraja pos/neg_limpio
      dentro de cada volcan: un estadistico que no discrimina da contraste dentro del nulo.
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
KS = [3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0]
N_NULO = 1000


def kobs(r):
    return r["diag"]["test1_k_observed"]


def estado(r, k):
    """sigue / cae / sin_dato para una pasada PUBLICADA, al umbral k."""
    c = r["clase"]
    if c in ("CTX_SOLO", "AMBOS"):
        return "sigue"
    ko = kobs(r) or 0.0
    if c == "T1_SOLO":
        return "sigue" if ko > k else "cae"
    if c == "T1_SOBRE_CTX":
        return "sigue" if ko > k else "sin_dato"
    return "sin_dato"  # RESCATE / OTRO


def curva_pasadas(sel_lab):
    n = len(sel_lab)
    pubs = [r for r in sel_lab if r["pub"]]
    out = {}
    for k in KS:
        c = collections.Counter(estado(r, k) for r in pubs)
        out[str(k)] = {"n": n, "pub_hoy": len(pubs), "cae": c["cae"], "sin_dato": c["sin_dato"],
                       "sigue": c["sigue"], "tasa_pub_min": bp._tasa(c["sigue"], n),
                       "tasa_pub_max": bp._tasa(c["sigue"] + c["sin_dato"], n)}
    return out


def curva_noches(recs, filtro):
    nn = collections.defaultdict(list)
    for r in recs:
        if filtro(r):
            nn[(r["vol"], r["noche"])].append(r)
    pos = {kk: rs for kk, rs in nn.items() if any(r["lab"] == "pos" for r in rs)}
    out, detalle = {}, {}
    for k in KS:
        c = collections.Counter()
        for (vol, noche), rs in sorted(pos.items()):
            pubs = [r for r in rs if r["pub"]]
            if not pubs:
                c["no_publicada_hoy"] += 1
                continue
            es = collections.Counter(estado(r, k) for r in pubs)
            st = "sigue" if es["sigue"] else ("sin_dato" if es["sin_dato"] else "se_pierde")
            c[st] += 1
            if st != "sigue":
                detalle.setdefault(str(k), []).append([vol, noche, st])
        out[str(k)] = {"n_noches_pos": len(pos), **dict(c)}
    return out, detalle


def contraste_k(sel, k):
    """frac de publicadas neg_limpio que CAEN a k  -  frac de publicadas pos que dejan de estar seguras a k."""
    a = [r for r in sel if r["lab_x"] == "neg_limpio"]
    b = [r for r in sel if r["lab_x"] == "pos"]
    if not a or not b:
        return None
    fa = sum(1 for r in a if r["_est"][k] == "cae") / len(a)
    fb = sum(1 for r in b if r["_est"][k] != "sigue") / len(b)
    return fa - fb


def nulo_k(recs, b, rng):
    sel = [dict(r, lab_x=r["lab"]) for r in recs if r["b"] == b and r["pub"] and r["lab"] in ("pos", "neg_limpio")]
    for r in sel:
        r["_est"] = {k: estado(r, k) for k in KS}
    por_vol = collections.defaultdict(list)
    for r in sel:
        por_vol[r["vol"]].append(r)
    obs = {k: contraste_k(sel, k) for k in KS}
    if obs[KS[0]] is None:
        return None
    vals = {k: [] for k in KS}
    for _ in range(N_NULO):
        for rs in por_vol.values():
            labs = [r["lab"] for r in rs]
            rng.shuffle(labs)
            for r, l in zip(rs, labs):
                r["lab_x"] = l
        for k in KS:
            vals[k].append(contraste_k(sel, k))
    out = {}
    for k in KS:
        v = sorted(vals[k])
        out[str(k)] = {"observado": round(obs[k], 4), "nulo_media": round(sum(v) / len(v), 4),
                       "nulo_p2.5": round(v[25], 4), "nulo_p97.5": round(v[974], 4),
                       "fuera_del_nulo": bool(obs[k] < v[25] or obs[k] > v[974])}
    return out


def auc(neg, pos):
    """P(k_obs pos > k_obs neg) + 0,5 empates."""
    if not neg or not pos:
        return None
    g = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return round(g / (len(pos) * len(neg)), 4)


def cuant(xs):
    xs = sorted(xs)
    if not xs:
        return None

    def q(f):
        return xs[min(len(xs) - 1, int(f * len(xs)))]
    return {"n": len(xs), "min": xs[0], "p10": q(.1), "p25": q(.25), "p50": q(.5), "p75": q(.75),
            "p90": q(.9), "max": xs[-1]}


def main():
    coords = sc._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = sc.cargar_referencia_unificada(sc.REF / "registro_vrp_consolidado.csv", sc.REF / "registro_vrp_ocr.csv")
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, sc.VENTANA)
    recs = sc.cargar(coords, inner)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r in recs:
        r["clase"], r["sub"] = sc.clase_sosten(r) if r["pub"] else ("NO_PUB", "")

    # ---------- control positivo
    ctrl = {}
    for b in bp.BUCKETS:
        neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio"]
        pubs = [r for r in neg if r["pub"]]
        ctrl[b] = {"n_neg_limpio": len(neg), "tasa_pub_neg": round(len(pubs) / len(neg), 4),
                   "n_pub_neg": len(pubs), "T1_SOLO_neg": sum(1 for r in pubs if r["clase"] == "T1_SOLO")}
    esperado = {"VIIRS375": (373, 0.8633, 322, 186), "VIIRS750": (622, 0.2138, 133, 89)}
    ok = all((ctrl[b]["n_neg_limpio"], ctrl[b]["tasa_pub_neg"], ctrl[b]["n_pub_neg"], ctrl[b]["T1_SOLO_neg"]) == esperado[b]
             for b in esperado)
    # MODIS con el corte de procesamiento de S145
    negm = [r for r in recs if r["b"] == "MODIS" and r["lab"] == "neg_limpio" and (r["diag"]["processed_utc"] or "") <= sc.CORTE_S145]
    ctrl["MODIS_con_corte_S145"] = {"n_neg_limpio": len(negm), "tasa_pub_neg": round(sum(r["pub"] for r in negm) / len(negm), 4)}
    ok = ok and ctrl["MODIS_con_corte_S145"] == {"n_neg_limpio": 438, "tasa_pub_neg": 0.1142}
    ctrl["reproduce_S145_y_Fase1"] = ok
    ctrl["n_records"] = len(recs)
    print("CONTROL POSITIVO", json.dumps(ctrl, ensure_ascii=False))
    if not ok:
        print("ABORTO: no reproduzco el control positivo")
        (AQUI / "p1_resultados.json").write_text(json.dumps({"control_positivo": ctrl}, indent=1), encoding="utf-8")
        return 2

    # ---------- cobertura del campo
    cob = {}
    for b in bp.BUCKETS:
        rs = [r for r in recs if r["b"] == b]
        ks = [kobs(r) for r in rs]
        trig = [r for r in rs if r["diag"]["triggered_test1"] is True]
        cob[b] = {"n_records": len(rs), "k_obs_None": sum(1 for v in ks if v is None),
                  "k_obs_cero": sum(1 for v in ks if v == 0), "k_obs_positivo": sum(1 for v in ks if v),
                  "triggered_True": len(trig),
                  "triggered_True_con_k_le_3": sum(1 for r in trig if (kobs(r) or 0) <= 3.0),
                  "triggered_False_con_k_gt_3_(fallo_el_criterio_relativo_2pct)": sum(
                      1 for r in rs if r["diag"]["triggered_test1"] is not True and (kobs(r) or 0) > 3.0),
                  "cuantiles_k_obs_de_los_disparos": cuant([kobs(r) for r in trig if kobs(r)])}
    print("COBERTURA", json.dumps(cob, ensure_ascii=False))

    res = {"meta": {"ventana": list(sc.VENTANA), "ks": KS, "n_ref_nocturnas": n_ref,
                    "etiquetas": dict(collections.Counter(r["lab"] for r in recs)),
                    "sha_index_html": bp.sha_git(bp.HTML)},
           "control_positivo": ctrl, "cobertura": cob}

    # ---------- distribucion de k_obs por clase y etiqueta
    dist = {}
    for b in bp.BUCKETS:
        dist[b] = {}
        for lab in ("neg_limpio", "pos"):
            for cl in ("T1_SOLO", "T1_SOBRE_CTX", "AMBOS"):
                dist[b][f"{lab}|{cl}"] = cuant([kobs(r) for r in recs if r["b"] == b and r["lab"] == lab
                                                 and r["clase"] == cl and kobs(r)])

        def disparos(lab, v=None):
            return [kobs(r) for r in recs if r["b"] == b and r["lab"] == lab and r["pub"]
                    and r["diag"]["triggered_test1"] is True and (v is None or r["vol"] == v)]
        negs, poss = disparos("neg_limpio"), disparos("pos")
        dist[b]["AUC_kobs_pos_vs_neg_entre_publicadas_con_disparo"] = {"auc": auc(negs, poss), "n_neg": len(negs), "n_pos": len(poss)}
        num = den = 0
        porv = {}
        for v in bp.VOLS:
            n_, p_ = disparos("neg_limpio", v), disparos("pos", v)
            a = auc(n_, p_)
            porv[v] = {"auc": a, "n_neg": len(n_), "n_pos": len(p_)}
            if a is not None:
                num += a * len(n_) * len(p_)
                den += len(n_) * len(p_)
        dist[b]["AUC_por_volcan"] = porv
        dist[b]["AUC_estratificado_por_volcan"] = round(num / den, 4) if den else None
    res["distribucion_k_obs"] = dist
    print("DISTRIBUCION", json.dumps(dist, ensure_ascii=False))

    # ---------- curvas
    res["curva_pasadas"] = {b: {lab: curva_pasadas([r for r in recs if r["b"] == b and r["lab"] == lab])
                                for lab in ("neg_limpio", "pos")} for b in bp.BUCKETS}
    res["curva_noches"], res["noches_afectadas"] = {}, {}
    for b in bp.BUCKETS + [None]:
        c, d = curva_noches(recs, lambda r, b=b: b is None or r["b"] == b)
        res["curva_noches"][b or "CUALQUIERA"] = c
        res["noches_afectadas"][b or "CUALQUIERA"] = d

    # las noches SIN DATO de la Fase 1, DERIVADAS (k = 3 con T1 apagado), no transcritas
    f1 = json.loads((ROOT / "experiments" / "_s146_fase1_sustrato" / "resultados_sustrato.json").read_text(encoding="utf-8"))
    sd = {(v, n) for v, n, st, _ in f1["noches_recall"]["CUALQUIERA"]["noches_que_dependen_de_T1"]}
    res["noches_SIN_DATO_F1_leidas_del_json_de_la_Fase1"] = sorted(list(x) for x in sd)
    c, _ = curva_noches([r for r in recs if (r["vol"], r["noche"]) not in sd], lambda r: True)
    res["curva_noches"]["CUALQUIERA_sin_las_SIN_DATO_F1"] = c
    det4 = {}
    for r in recs:
        if (r["vol"], r["noche"]) in sd:
            det4.setdefault(f'{r["vol"]}|{r["noche"]}', []).append(
                {"b": r["b"], "dt": r["diag"]["datetime_utc"], "lab": r["lab"], "pub": bool(r["pub"]),
                 "clase": r["clase"], "sub": r["sub"], "k_obs": kobs(r), "disp_mw": r["disp"]})
    res["detalle_noches_SIN_DATO_F1"] = det4
    print("NOCHES SIN DATO F1", json.dumps(det4, ensure_ascii=False))

    res["curva_por_volcan"] = {b: {v: {lab: curva_pasadas([r for r in recs if r["b"] == b and r["vol"] == v and r["lab"] == lab])
                                       for lab in ("neg_limpio", "pos")} for v in bp.VOLS} for b in bp.BUCKETS}
    res["curva_noches_por_volcan"] = {v: curva_noches(recs, lambda r, v=v: r["vol"] == v)[0] for v in bp.VOLS}

    rng = random.Random(146)
    res["nulo"] = {b: nulo_k(recs, b, rng) for b in bp.BUCKETS}

    for b in bp.BUCKETS:
        print("==", b)
        for k in KS:
            n_ = res["curva_pasadas"][b]["neg_limpio"][str(k)]
            p_ = res["curva_pasadas"][b]["pos"][str(k)]
            no = res["curva_noches"][b][str(k)]
            nu = (res["nulo"][b] or {}).get(str(k))
            print(f"  k={k:>4}: NEG cae {n_['cae']:>3} sin_dato {n_['sin_dato']:>3} tasa {n_['tasa_pub_min']}-{n_['tasa_pub_max']}"
                  f" | POS pasadas cae {p_['cae']} sd {p_['sin_dato']} | NOCHES {no} | nulo {nu}")
    print("== CUALQUIER sensor, noches:")
    for k in KS:
        print(f"  k={k}: {res['curva_noches']['CUALQUIERA'][str(k)]} | sin las SIN DATO F1: {res['curva_noches']['CUALQUIERA_sin_las_SIN_DATO_F1'][str(k)]}")
    print("NOCHES AFECTADAS (cualquier sensor):", json.dumps(res["noches_afectadas"]["CUALQUIERA"], ensure_ascii=False))
    (AQUI / "p1_resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("->", AQUI / "p1_resultados.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
