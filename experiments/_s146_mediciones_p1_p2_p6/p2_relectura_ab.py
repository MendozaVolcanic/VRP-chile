# -*- coding: utf-8 -*-
"""P2 (S146): RE-LECTURA POSTERIOR Y EXPLORATORIA de las salidas por brazo de los A/B de S135 y S143.
NO es un veredicto nuevo: los dos A/B tienen pre-registro y veredicto (NO ADOPTAR) y eso no cambia.
SOLO LECTURA. No descomprime nada al arbol ni escribe fuera de esta carpeta.

QUE HACE. Lee los JSON por brazo y volcan (S135: experiments/_artefactos_ab/s135ab-*, dos runs de
ventanas disjuntas que se fusionan en memoria; S143: la carpeta fusionada que cita
resultado_ab_s143.json en meta.dir_artefactos). Les aplica el banco de paridad de S145
(scripts/banco_paridad.py: etiquetas pos/neg_limpio, predicado del dashboard con node) con la
referencia fijada por sha de experiments/_s143_evaluador/_dl_referencia. Y tabula POR VOLCAN, en las
unidades del operador:
  * publicacion en negativos limpios por PASADA (pareada contra el control: mismas pasadas);
  * recall por NOCHE: noche de volcan con alguna pasada `pos`; se cuenta publicada (a) si el brazo
    publica CUALQUIER pasada de esa noche y (b) si publica una pasada `pos` (la misma pasada en que
    MIROVA alerto). Ninguna de las dos usa la cota escalar de radios (A93/A107): (b) parea por hora,
    no por distancia. Lo que NO garantizan: que lo publicado sea el mismo objeto.
  * razon de magnitud nuestra / MIROVA, mediana por volcan, sobre los pares que publican control y brazo.

REGLA DE LECTURA, fijada ANTES de mirar la tabla (y aun asi posterior a los veredictos):
  muestra suficiente = volcan con >= 30 pasadas neg_limpio y >= 10 noches pos (umbrales tomados de
  parametros.json y del verificador de S143, no elegidos aca).
  GANA   = 0 noches perdidas (a) y (b) y baja la publicacion en neg_limpio con prueba de signos p < 0,05
  EMPATA = 0 noches perdidas y la diferencia de publicacion no se distingue de cero
  PIERDE = pierde >= 1 noche, o sube la publicacion con p < 0,05

LAS DOS PREGUNTAS DEL INSTRUMENTO.
  (1) Si lo que mido estuviera roto, fallaria? Control positivo: con el control de S143 tengo que
      reproducir n = 1170 negativos limpios, tasa 0,9171 y literal 0,5470 (resultado_ab_s143.json), y
      las noches con alerta por volcan. Si no, ABORTA.
  (2) Si el instrumento estuviera muerto, se veria distinto? Control contra si mismo: control vs
      control debe dar 0 discordantes; y un brazo que se sabe distinto (literal) debe dar cientos. Se
      comprueba ademas que todos los brazos tengan LAS MISMAS pasadas (A108): un volcan con
      cobertura despareja se EXCLUYE y se lista.
"""
from __future__ import annotations
import collections
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

AQUI = Path(__file__).resolve().parent
REFDIR = ROOT / "experiments" / "_s143_evaluador" / "_dl_referencia"
VENTANA = ("2026-06-01", "2026-08-31")
R143 = json.loads((ROOT / "experiments" / "_s143_evaluador" / "resultado_ab_s143.json").read_text(encoding="utf-8"))
N_MIN_NEG, N_MIN_NOCHES = 30, 10

EXP = {
    "S135": {"brazos": ["_s135_ab_a_control", "_s135_ab_b_nokeeppeak", "_s135_ab_c_cond", "_s135_ab_d_ambos", "_s135_ab_e_sp_off"],
             "control": "_s135_ab_a_control",
             "vols": ["Isluga", "Lascar", "Lastarria", "PuyehueCordonCaulle", "PlanchonPeteroa", "Tupungatito"]},
    "S143": {"brazos": R143["meta"]["brazos"], "control": R143["meta"]["control"], "vols": R143["meta"]["volcanes"]},
}


def rutas(exp, brazo, vol):
    if exp == "S135":
        base = ROOT / "experiments" / "_artefactos_ab"
        return sorted(base.glob(f"s135ab-{brazo}-{vol}__run*/{vol}.json"))
    return [Path(R143["meta"]["dir_artefactos"]) / f"s143ab-{brazo}-{vol}" / f"{vol}.json"]


def leer_records(exp, brazo, vol):
    """Une los chunks por (datetime_utc, sensor). Devuelve (records, n_conflictos, n_archivos)."""
    por = {}
    conf = 0
    ps = rutas(exp, brazo, vol)
    for p in ps:
        if not p.exists():
            return None, 0, 0
        for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
            k = (r.get("datetime_utc"), r.get("sensor"))
            if k in por and por[k].get("primary_cluster") != r.get("primary_cluster"):
                conf += 1
            por[k] = r
    return list(por.values()), conf, len(ps)


def cargar(exp, brazo, vols, coords, inner):
    recs, casos, meta = [], [], {}
    for vol in vols:
        rs, conf, narch = leer_records(exp, brazo, vol)
        if rs is None:
            meta[vol] = "FALTA"
            continue
        meta[vol] = {"archivos": narch, "conflictos": conf}
        for r in rs:
            b = bp.bucket(r.get("sensor"))
            if b != "VIIRS375" or not (VENTANA[0] <= (r.get("datetime_utc") or "")[:10] <= VENTANA[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "key": (vol, r["sensor"], r["datetime_utc"]),
                   "src": r.get("final_hotspot_source"), "proc": r.get("processed_utc")}
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], bool(p[4])
    return recs, meta


def p_signos(a, b):
    """Prueba de signos bilateral exacta sobre discordantes (a = solo control, b = solo brazo)."""
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, p), 6)


def mediana(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return round(xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2, 4)


def evaluar(exp, cfg, coords, inner, por_vb, noche_sensor, noche_volcan):
    out = {"cobertura": {}, "por_brazo": {}}
    datos = {}
    for brazo in cfg["brazos"]:
        recs, meta = cargar(exp, brazo, cfg["vols"], coords, inner)
        bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
        datos[brazo] = {r["key"]: r for r in recs}
        out["cobertura"][brazo] = {"archivos": meta, "n_pasadas": dict(collections.Counter(r["vol"] for r in recs)),
                                   "processed_utc_min": min((r["proc"] or "" for r in recs), default=None),
                                   "processed_utc_max": max((r["proc"] or "" for r in recs), default=None)}
    ctl = datos[cfg["control"]]
    excl = {}
    for brazo in cfg["brazos"]:
        for vol in cfg["vols"]:
            kc = {k for k in ctl if k[0] == vol}
            kb = {k for k in datos[brazo] if k[0] == vol}
            if kc != kb:
                excl.setdefault(vol, {})[brazo] = {"control": len(kc), "brazo": len(kb), "solo_control": len(kc - kb), "solo_brazo": len(kb - kc)}
    out["volcanes_con_cobertura_despareja"] = excl
    # pareo con MIROVA para magnitud
    for brazo in cfg["brazos"]:
        res = {}
        for vol in cfg["vols"] + ["TODOS"]:
            vs = [v for v in cfg["vols"] if v not in excl] if vol == "TODOS" else [vol]
            if vol != "TODOS" and vol in excl:
                res[vol] = {"EXCLUIDO_por_cobertura": excl[vol]}
                continue
            keys = [k for k in ctl if k[0] in vs]
            neg = [k for k in keys if ctl[k]["lab"] == "neg_limpio"]
            pc = sum(ctl[k]["pub"] for k in neg)
            pb = sum(datos[brazo][k]["pub"] for k in neg)
            sc_ = sum(1 for k in neg if ctl[k]["pub"] and not datos[brazo][k]["pub"])
            sb_ = sum(1 for k in neg if datos[brazo][k]["pub"] and not ctl[k]["pub"])
            # noches
            nn = collections.defaultdict(list)
            for k in keys:
                nn[(k[0], ctl[k]["noche"])].append(k)
            pos_n = {n: ks for n, ks in nn.items() if any(ctl[k]["lab"] == "pos" for k in ks)}
            a_c = sum(1 for ks in pos_n.values() if any(ctl[k]["pub"] for k in ks))
            a_b = sum(1 for ks in pos_n.values() if any(datos[brazo][k]["pub"] for k in ks))
            b_c = sum(1 for ks in pos_n.values() if any(ctl[k]["pub"] for k in ks if ctl[k]["lab"] == "pos"))
            b_b = sum(1 for ks in pos_n.values() if any(datos[brazo][k]["pub"] for k in ks if ctl[k]["lab"] == "pos"))
            perd_a = sorted([n[0], n[1]] for n, ks in pos_n.items() if any(ctl[k]["pub"] for k in ks) and not any(datos[brazo][k]["pub"] for k in ks))
            perd_b = sorted([n[0], n[1]] for n, ks in pos_n.items()
                            if any(ctl[k]["pub"] for k in ks if ctl[k]["lab"] == "pos")
                            and not any(datos[brazo][k]["pub"] for k in ks if ctl[k]["lab"] == "pos"))
            gan_b = sorted([n[0], n[1]] for n, ks in pos_n.items()
                           if not any(ctl[k]["pub"] for k in ks if ctl[k]["lab"] == "pos")
                           and any(datos[brazo][k]["pub"] for k in ks if ctl[k]["lab"] == "pos"))
            # magnitud pareada: pasadas pos publicadas por los dos, con VRP de MIROVA > 0
            rc, rb = [], []
            for k in keys:
                if ctl[k]["lab"] != "pos" or not (ctl[k]["pub"] and datos[brazo][k]["pub"]):
                    continue
                filas = bp.parear(por_vb.get((k[0], "VIIRS375"), []), ctl[k]["dt"])
                vm = [f["vrp_mw"] for f in filas if bp.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0]
                if not vm or not ctl[k]["disp"] or not datos[brazo][k]["disp"]:
                    continue
                rc.append(ctl[k]["disp"] / vm[0])
                rb.append(datos[brazo][k]["disp"] / vm[0])
            d = {"neg_n": len(neg), "neg_pub_control": pc, "neg_pub_brazo": pb,
                 "neg_tasa_control": bp._tasa(pc, len(neg)), "neg_tasa_brazo": bp._tasa(pb, len(neg)),
                 "neg_solo_control": sc_, "neg_solo_brazo": sb_, "p_signos": p_signos(sc_, sb_),
                 "noches_pos": len(pos_n), "noches_pub_a_control": a_c, "noches_pub_a_brazo": a_b,
                 "noches_pub_b_control": b_c, "noches_pub_b_brazo": b_b,
                 "perdidas_a": perd_a, "perdidas_b": perd_b, "ganancias_b": gan_b,
                 "mag_n_pares": len(rc), "mag_mediana_control": mediana(rc), "mag_mediana_brazo": mediana(rb)}
            suf = d["neg_n"] >= N_MIN_NEG and d["noches_pos"] >= N_MIN_NOCHES
            d["muestra_suficiente"] = suf
            if brazo == cfg["control"]:
                d["lectura"] = "CONTROL"
            elif perd_a or perd_b:
                d["lectura"] = "PIERDE(noches)"
            elif sb_ > sc_ and d["p_signos"] < 0.05:
                d["lectura"] = "PIERDE(sube_pub)"
            elif sc_ > sb_ and d["p_signos"] < 0.05:
                d["lectura"] = "GANA"
            else:
                d["lectura"] = "EMPATA"
            res[vol] = d
        out["por_brazo"][brazo] = res
    return out


def nulo_brazos(exp, out, cfg, rng, n=1000):
    """Nulo del instrumento: si 'control' y 'brazo' fueran la misma cosa, los discordantes se repartirian
    al azar. Se reporta, por brazo, cuantos volcanes con muestra suficiente 'GANAN' bajo ese nulo."""
    res = {}
    for brazo, pv in out["por_brazo"].items():
        if brazo == cfg["control"]:
            continue
        vols = [v for v, d in pv.items() if v != "TODOS" and d.get("muestra_suficiente")]
        cnt = []
        for _ in range(n):
            g = 0
            for v in vols:
                m = pv[v]["neg_solo_control"] + pv[v]["neg_solo_brazo"]
                a = sum(rng.random() < 0.5 for _ in range(m))
                if a > m - a and p_signos(a, m - a) < 0.05:
                    g += 1
            cnt.append(g)
        cnt.sort()
        res[brazo] = {"n_vol_suficientes": len(vols), "gana_bajo_nulo_media": round(sum(cnt) / n, 3), "gana_bajo_nulo_p97.5": cnt[int(.975 * n)]}
    return res


def main():
    coords = _coords_por_volcan()
    inner = bp.inner_desde_html()
    cons = next(REFDIR.glob("*consolidado.csv"))
    ocr = next(REFDIR.glob("*ocr.csv"))
    filas = cargar_referencia_unificada(cons, ocr)
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(filas, coords, VENTANA)
    print("REFERENCIA", cons.name, ocr.name, "filas nocturnas en ventana:", n_ref, "| evaluador S143 uso:", R143["meta"]["n_filas_referencia_nocturnas"])
    res = {"meta": {"ventana": list(VENTANA), "ref": [cons.name, ocr.name], "n_ref": n_ref,
                    "n_min_neg": N_MIN_NEG, "n_min_noches": N_MIN_NOCHES,
                    "identidad_predicado": bp.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0]),
                    "caracter": "re-lectura posterior y exploratoria; los veredictos pre-registrados no cambian"}}
    rng = random.Random(146)
    for exp in ("S143", "S135"):
        cfg = EXP[exp]
        out = evaluar(exp, cfg, coords, inner, por_vb, noche_sensor, noche_volcan)
        if exp == "S143":
            t = out["por_brazo"][cfg["control"]]["TODOS"]
            lit = out["por_brazo"]["_s142_ab_literal"]["TODOS"]
            esperado = {"neg_n": R143["control"]["neg_limpio_n"], "tasa_control": round(R143["control"]["neg_limpio_tasa_publica"], 4),
                        "tasa_literal": round(R143["brazos"]["_s142_ab_literal"]["criterio2"]["total"]["tasa_brazo"], 4),
                        "solo_control_literal": R143["brazos"]["_s142_ab_literal"]["criterio2"]["total"]["solo_control"],
                        "noches_alerta": R143["control"]["noches_con_alerta_nocturna_v375"]}
            mio = {"neg_n": t["neg_n"], "tasa_control": t["neg_tasa_control"], "tasa_literal": lit["neg_tasa_brazo"],
                   "solo_control_literal": lit["neg_solo_control"],
                   "noches_alerta": {v: out["por_brazo"][cfg["control"]][v]["noches_pos"] for v in cfg["vols"]}}
            ok = all(mio[k] == esperado[k] for k in ("neg_n", "tasa_control", "tasa_literal", "solo_control_literal"))
            res["control_positivo_S143"] = {"esperado_del_json_de_S143": esperado, "mio": mio, "reproduce": ok,
                                            "noches_alerta_iguales": mio["noches_alerta"] == esperado["noches_alerta"]}
            print("CONTROL POSITIVO S143", json.dumps(res["control_positivo_S143"], ensure_ascii=False))
            if not ok:
                print("ABORTO: no reproduzco el control de S143")
                (AQUI / "p2_resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
                return 2
        ctl = out["por_brazo"][cfg["control"]]["TODOS"]
        res.setdefault("control_contra_si_mismo", {})[exp] = {"solo_control": ctl["neg_solo_control"], "solo_brazo": ctl["neg_solo_brazo"], "perdidas": len(ctl["perdidas_a"]) + len(ctl["perdidas_b"])}
        out["nulo_reparto_al_azar"] = nulo_brazos(exp, out, cfg, rng)
        res[exp] = out
        print("=====", exp, "cobertura despareja:", json.dumps(out["volcanes_con_cobertura_despareja"]))
        print("   processed_utc:", {b: (c["processed_utc_min"], c["processed_utc_max"]) for b, c in out["cobertura"].items()})
        for brazo, pv in out["por_brazo"].items():
            print("--", brazo)
            for vol, d in pv.items():
                if "EXCLUIDO_por_cobertura" in d:
                    print(f"   {vol:20s} EXCLUIDO", d)
                    continue
                print(f"   {vol:20s} neg {d['neg_pub_brazo']:>4}/{d['neg_n']:<4} tasa {d['neg_tasa_brazo']} (ctl {d['neg_tasa_control']}) -{d['neg_solo_control']} +{d['neg_solo_brazo']} p={d['p_signos']}"
                      f" | noches pos {d['noches_pos']:>3} pubA {d['noches_pub_a_brazo']}/{d['noches_pub_a_control']} pubB {d['noches_pub_b_brazo']}/{d['noches_pub_b_control']} perdA {len(d['perdidas_a'])} perdB {len(d['perdidas_b'])} ganB {len(d['ganancias_b'])}"
                      f" | mag n={d['mag_n_pares']} {d['mag_mediana_brazo']} (ctl {d['mag_mediana_control']}) | suf={d['muestra_suficiente']} -> {d['lectura']}")
        print("   NULO:", json.dumps(out["nulo_reparto_al_azar"]))
    print("CONTROL CONTRA SI MISMO", res["control_contra_si_mismo"])
    (AQUI / "p2_resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("->", AQUI / "p2_resultados.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
