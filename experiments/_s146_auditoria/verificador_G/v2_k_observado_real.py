# -*- coding: utf-8 -*-
"""V2 (verificador G, item 1) - ¿`test1_k_observed` distingue la noche que MIROVA confirmo
de la pasada en que MIROVA miro y no vio nada? Datos reales, etiquetas del banco de paridad.

(1) Si lo que mide estuviera roto, ¿fallaria?
    Si `test1_k_observed` SI discriminara calor real de ruido, el AUC contra la etiqueta del
    banco daria claramente > 0,5 y la tesis "el criterio se cumple con ruido" quedaria
    debilitada por esta misma salida. El script no puede dar 0,5 por construccion: el campo
    ORACULO (la etiqueta metida como si fuera un campo) tiene que dar AUC 1,0 sobre el mismo
    denominador, y el campo `pc_vrp` (magnitud publicada) es un segundo control que DEBE
    separar si el banco y el pareo estan sanos.

(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si. Barajar las etiquetas DENTRO de cada volcan lleva el AUC a 0,5 (media de 50 barajados):
    si el AUC barajado no cayera a 0,5, el numero seria un artefacto del pareo y no una medida.
    Y se informa la cobertura de cada campo por sensor: un campo ausente daria ceros que se
    leen como confirmacion, asi que se cuenta antes de usarlo.

Etiquetas: se reusa la indexacion de la referencia de `scripts/banco_paridad.py` (importada, no
copiada). El unico codigo propio es el cargador, que ademas de lo que carga el banco trae los
campos del Test 1. No corre node: aqui no se pregunta que se publica, sino que mide el criterio.

Ventana 2026-09-01 en adelante (regimen actual; nunca cruzar 2026-08-28 23:00 UTC). Semilla 20146.
"""
import io
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import (SNAP_CONS, SNAP_OCR,  # noqa: E402
                                         cargar_referencia_unificada)
from auto_audit_weekly import _coords_por_volcan, es_pasada_diurna_descartada  # noqa: E402

SEED = 20146
INICIO, FIN = "2026-09-01", "2026-12-31"
CAMPOS = ["test1_k_observed", "n_test1_pixels", "nti_max", "diag_nti_std",
          "t_max_k", "t_bg_k", "diag_sigma_bg_k"]
OUT = Path(__file__).with_suffix(".json")


def cargar_con_test1(coords, ventana):
    """Igual filtro que banco_paridad.cargar_nuestros (bucket, ventana, diurna descartada),
    mas los campos del Test 1. Sin node."""
    recs = []
    for vol in BP.VOLS:
        with open(BP.DATA / f"{vol}.json", encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = BP.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= r.get("datetime_utc", "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            pc = r.get("primary_cluster") or {}
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                   "pc_vrp": pc.get("vrp_mw"), "triggered_test1": r.get("triggered_test1")}
            for c in CAMPOS:
                rec[c] = r.get(c)
            recs.append(rec)
    return recs


def auc(pares):
    """AUC de Mann-Whitney con empates a 0,5. pares = [(valor, etiqueta 0/1)]."""
    pos = [v for v, y in pares if y == 1]
    neg = [v for v, y in pares if y == 0]
    if not pos or not neg:
        return None
    neg_ord = sorted(neg)
    import bisect
    tot = 0.0
    for v in pos:
        lo = bisect.bisect_left(neg_ord, v)
        hi = bisect.bisect_right(neg_ord, v)
        tot += lo + 0.5 * (hi - lo)
    return tot / (len(pos) * len(neg))


def cuantiles(xs):
    if not xs:
        return {}
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(p * len(s)))]
    return {"n": len(s), "p10": q(0.10), "mediana": q(0.50), "p90": q(0.90),
            "media": sum(s) / len(s)}


def main():
    random.seed(SEED)
    coords = _coords_por_volcan()
    filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    por_vb, noche_sensor, noche_volcan, n_ref = BP.indexar_referencia(filas, coords, (INICIO, FIN))
    recs = cargar_con_test1(coords, (INICIO, FIN))
    BP.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    out = {"ventana": [INICIO, FIN], "semilla": SEED, "n_filas_ref": n_ref,
           "n_records": len(recs), "etiquetas": dict(Counter(r["lab"] for r in recs)),
           "cobertura_campos": {}, "por_sensor": {}, "por_volcan": {}, "controles": {}}

    # cobertura de cada campo por sensor: un campo ausente da ceros que se leen como dato
    for b in BP.BUCKETS:
        sub = [r for r in recs if r["b"] == b]
        out["cobertura_campos"][b] = {
            "n": len(sub),
            **{c: (sum(1 for r in sub if r.get(c) is not None) / len(sub) if sub else None)
               for c in CAMPOS + ["pc_vrp", "triggered_test1"]}}

    for b in BP.BUCKETS:
        sub = [r for r in recs if r["b"] == b and r["lab"] in ("pos", "neg_limpio")]
        pos = [r for r in sub if r["lab"] == "pos"]
        neg = [r for r in sub if r["lab"] == "neg_limpio"]
        d = {"n_pos": len(pos), "n_neg": len(neg)}
        for campo in ["test1_k_observed", "pc_vrp", "nti_max", "n_test1_pixels"]:
            pares = [(r[campo], 1 if r["lab"] == "pos" else 0) for r in sub if r.get(campo) is not None]
            d[campo] = {
                "auc": auc(pares),
                "pos": cuantiles([r[campo] for r in pos if r.get(campo) is not None]),
                "neg": cuantiles([r[campo] for r in neg if r.get(campo) is not None]),
            }
        d["tasa_triggered_test1"] = {
            "pos": (sum(1 for r in pos if r.get("triggered_test1")) / len(pos)) if pos else None,
            "neg": (sum(1 for r in neg if r.get("triggered_test1")) / len(neg)) if neg else None}
        out["por_sensor"][b] = d

    # estratificado por volcan (A: una mediana agrupada puede invertir el veredicto)
    for vol in BP.VOLS:
        for b in BP.BUCKETS:
            sub = [r for r in recs if r["vol"] == vol and r["b"] == b
                   and r["lab"] in ("pos", "neg_limpio") and r.get("test1_k_observed") is not None]
            pos = [r for r in sub if r["lab"] == "pos"]
            neg = [r for r in sub if r["lab"] == "neg_limpio"]
            if len(pos) < BP.N_MIN_AUC or len(neg) < BP.N_MIN_AUC:
                continue
            out["por_volcan"][f"{vol}|{b}"] = {
                "n_pos": len(pos), "n_neg": len(neg),
                "auc_k": auc([(r["test1_k_observed"], 1 if r["lab"] == "pos" else 0) for r in sub]),
                "auc_pc_vrp": auc([(r["pc_vrp"] or 0.0, 1 if r["lab"] == "pos" else 0) for r in sub]),
                "k_mediana_pos": cuantiles([r["test1_k_observed"] for r in pos])["mediana"],
                "k_mediana_neg": cuantiles([r["test1_k_observed"] for r in neg])["mediana"],
                "trig_pos": sum(1 for r in pos if r.get("triggered_test1")) / len(pos),
                "trig_neg": sum(1 for r in neg if r.get("triggered_test1")) / len(neg),
            }

    # --- CONTROLES ---
    sub375 = [r for r in recs if r["b"] == "VIIRS375" and r["lab"] in ("pos", "neg_limpio")
              and r.get("test1_k_observed") is not None]
    y = lambda r: 1 if r["lab"] == "pos" else 0
    out["controles"]["oraculo_campo_es_etiqueta_auc"] = auc([(y(r), y(r)) for r in sub375])
    barajados = []
    por_vol = defaultdict(list)
    for r in sub375:
        por_vol[r["vol"]].append(r)
    for _ in range(50):
        pares = []
        for vol, lista in por_vol.items():
            labs = [y(r) for r in lista]
            random.shuffle(labs)
            pares += [(r["test1_k_observed"], l) for r, l in zip(lista, labs)]
        barajados.append(auc(pares))
    barajados = [a for a in barajados if a is not None]
    out["controles"]["barajado_dentro_de_volcan_auc_medio"] = sum(barajados) / len(barajados)
    out["controles"]["barajado_min"] = min(barajados)
    out["controles"]["barajado_max"] = max(barajados)
    out["controles"]["n_sub375"] = len(sub375)

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"records {out['n_records']}  etiquetas {out['etiquetas']}")
    print("\ncobertura de campos (fraccion no nula):")
    for b, c in out["cobertura_campos"].items():
        print(" ", b, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in c.items()})
    print("\nPOR SENSOR (pos = MIROVA confirmo | neg = negativo limpio)")
    for b, d in out["por_sensor"].items():
        print(f"\n [{b}] n_pos={d['n_pos']} n_neg={d['n_neg']} "
              f"trig_test1 pos={d['tasa_triggered_test1']['pos']} neg={d['tasa_triggered_test1']['neg']}")
        for campo in ["test1_k_observed", "pc_vrp", "nti_max", "n_test1_pixels"]:
            e = d[campo]
            print(f"   {campo:20s} AUC={e['auc']}  pos_med={e['pos'].get('mediana')}  neg_med={e['neg'].get('mediana')}")
    print("\nPOR VOLCAN (solo n>=5 en ambos grupos)")
    for k, v in out["por_volcan"].items():
        print(f"  {k:32s} n={v['n_pos']}/{v['n_neg']}  AUC_k={v['auc_k']:.3f}  AUC_pcvrp={v['auc_pc_vrp']:.3f}"
              f"  k_med {v['k_mediana_pos']:.2f} vs {v['k_mediana_neg']:.2f}"
              f"  trig {v['trig_pos']:.2f} vs {v['trig_neg']:.2f}")
    print("\nCONTROLES:", json.dumps(out["controles"], ensure_ascii=False, indent=1))
    print("\nJSON:", OUT)


if __name__ == "__main__":
    main()
