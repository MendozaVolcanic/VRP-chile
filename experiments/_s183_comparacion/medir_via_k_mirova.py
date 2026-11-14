# -*- coding: utf-8 -*-
"""S183: ¿la vía «código MIROVA» coincide con MIROVA mejor que K? Medida por noche-satélite, sensor por sensor.

POR QUÉ. Nicolás (2026-11-13) quiere asegurarse de que la vía nueva es la más fiable. Las vigilancias de las guardias
(scripts/vigilancia_guardia_*.py) sólo buscan alertas protegidas que la vía calla y K publica; no dicen cuál de los dos
detectores se parece más a MIROVA en conjunto. Esto lo mide con la misma vara para los dos: el etiquetado de
scripts/banco_paridad.py (pos, neg_limpio, far_ref, sin_info) y el predicado del tablero ejecutado con node desde
frontend/index.html. Nada se porta ni se reescribe: se importa.

QUÉ COMPARA. Sólo pasadas que los dos detectores procesaron (misma clave volcán, satélite, minuto): una diferencia de
cobertura no se cuenta como diferencia de detección (se informa aparte).
  * Historia: vía = data/mirova_equivalent de hoy (reemplazada en S181); K = la misma carpeta en el tag
    pre-s180-reemplazo-historia, sólo records sin la clave `via_codigo_mirova` (K puro).
  * Después de la adopción: vía = producción; K = la guardia (data/guardia_k_modis, data/guardia_k_viirs).

UNIDAD: la noche-satélite (volcán, satélite, fecha UTC). pos si alguna pasada tiene ALERTA de MIROVA; neg si hay un
negativo limpio (fila RUTINA de la tabla con VRP 0, sin alerta ni FP esa noche y sensor) y ninguna pasada pos ni far_ref.
TP = pos y publica; FN = pos y no publica; FP = neg y publica; TN = neg y no publica. far_ref y sin_info quedan fuera de
todo denominador. Protegida: alguna fila de alerta con VRP de 1 MW o más (lectura A, clase_mirova.alerta_protegida).
D-9 en modo SN (VIIRS 375 hasta 0,05 MW no es alerta). Dos referencias: combinado (tabla más OCR) y sólo tabla
(source CONS; las capas histórico y respaldo también son tabla).
Cociente nuestro/MIROVA: por pasada pos publicada, el VRP que muestra el tablero (mirovaEqVrpDisplay) sobre el VRP
máximo de las filas de alerta de esa pasada (tabla si la hay, si no OCR); se informa la mediana.

Uso: python experiments/_s183_comparacion/medir_via_k_mirova.py --k-historia <carpeta con los JSON del tag>
"""
from __future__ import annotations

import argparse
import collections
import json
import shutil
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402
from clase_mirova import MODO_MINIMAS, alerta_protegida  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, bajar_remoto, cargar_referencia_unificada  # noqa: E402

PROD = ROOT / "data" / "mirova_equivalent"
GUARDIA = {"MODIS": ROOT / "data" / "guardia_k_modis", "VIIRS375": ROOT / "data" / "guardia_k_viirs",
           "VIIRS750": ROOT / "data" / "guardia_k_viirs"}
VENTANAS = {
    # historia: tabla sana desde marzo (A119); hasta el día antes del primer encendido (MODIS 2026-11-02)
    "historia": {"MODIS": ("2026-03-01", "2026-11-01"), "VIIRS375": ("2026-03-01", "2026-11-01"),
                 "VIIRS750": ("2026-03-01", "2026-11-01")},
    # desde la adopción de cada sensor, contra la guardia
    "adopcion": {"MODIS": ("2026-11-02", "2026-11-13"), "VIIRS375": ("2026-11-11", "2026-11-13"),
                 "VIIRS750": ("2026-11-11", "2026-11-13")},
    # VIIRS: toda la ventana con guardia (la vía de esos días es la historia reemplazada en S181)
    "guardia_viirs": {"VIIRS375": ("2026-11-03", "2026-11-13"), "VIIRS750": ("2026-11-03", "2026-11-13")},
}


def carpeta_filtrada(origen: Path, quiere_via) -> tuple[Path, collections.Counter]:
    """Copia a un temporal los 11 JSON con los records que cumplen `quiere_via(r)`; devuelve la carpeta y un conteo."""
    tmp = Path(tempfile.mkdtemp(prefix="s183_"))
    c = collections.Counter()
    for vol in bp.VOLS:
        d = json.loads((origen / f"{vol}.json").read_text(encoding="utf-8"))
        keep = []
        for r in d.get("records", []):
            ok = quiere_via(r)
            c["dentro" if ok else "fuera"] += 1
            if ok:
                keep.append(r)
        (tmp / f"{vol}.json").write_text(json.dumps({"records": keep}), encoding="utf-8")
    return tmp, c


def pasadas(data_dir: Path, ventana, coords, inner, ref):
    por_vb, ns, nv, _ = ref
    recs = bp.cargar_nuestros(coords, inner, ventana, data=data_dir)
    bp.etiquetar(recs, por_vb, ns, nv)
    out = {}
    for r in recs:
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        al = [f for f in filas if bp.es_alerta(f["tipo"])]
        tab = [f["vrp_mw"] for f in al if f["source"] == "CONS" and f["vrp_mw"] is not None]
        todos = [f["vrp_mw"] for f in al if f["vrp_mw"] is not None]
        r["vrp_mirova"] = max(tab) if tab else (max(todos) if todos else None)
        r["protegida"] = r["lab"] == "pos" and any(alerta_protegida(f) for f in al)
        out[(r["vol"], r["sensor"], r["dt"])] = r
    return out


def noches(rs):
    """Agrega pasadas a noche-satélite."""
    g = collections.defaultdict(list)
    for r in rs:
        g[(r["vol"], r["sensor"], r["noche"])].append(r)
    out = {}
    for k, lst in g.items():
        labs = {r["lab"] for r in lst}
        if "pos" in labs:
            lab = "pos"
        elif "neg_limpio" in labs and "far_ref" not in labs:
            lab = "neg"
        else:
            continue
        out[k] = {"lab": lab, "pub": max(r["pub"] for r in lst), "prot": any(r["protegida"] for r in lst),
                  "vrp_mirova": max((r["vrp_mirova"] for r in lst if r["vrp_mirova"] is not None), default=None),
                  "vrp_nuestro": max((r["disp"] for r in lst if r["pub"]), default=None)}
    return out


def tabla(ns_, pas):
    c = collections.Counter()
    for e in ns_.values():
        if e["lab"] == "pos":
            c["TP" if e["pub"] else "FN"] += 1
            if e["prot"]:
                c["prot_TP" if e["pub"] else "prot_FN"] += 1
        else:
            c["FP" if e["pub"] else "TN"] += 1
    ratios = [r["disp"] / r["vrp_mirova"] for r in pas if r["lab"] == "pos" and r["pub"]
              and r["vrp_mirova"] and r["disp"] is not None]
    tp, fn, fp = c["TP"], c["FN"], c["FP"]
    return {"TP": tp, "FN": fn, "FP": fp, "TN": c["TN"],
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "pub_en_negativos": round(fp / (fp + c["TN"]), 4) if fp + c["TN"] else None,
            "protegidas": c["prot_TP"] + c["prot_FN"], "protegidas_perdidas": c["prot_FN"],
            "mediana_cociente": round(statistics.median(ratios), 3) if ratios else None, "n_cociente": len(ratios),
            "cuartiles_cociente": ([round(q, 3) for q in statistics.quantiles(ratios, n=4)] if len(ratios) > 1
                                   else None),
            "frac_cociente_a_5pct": round(sum(abs(x - 1) <= 0.05 for x in ratios) / len(ratios), 3) if ratios else None}


def comparar(via, k, b, por_volcan=True):
    claves = sorted(x for x in via.keys() & k.keys() if via[x]["b"] == b)
    pv, pk = [via[x] for x in claves], [k[x] for x in claves]
    nvia, nk = noches(pv), noches(pk)
    disc = collections.Counter()
    perdidas = []
    for kk in nvia.keys() & nk.keys():
        a, z = nvia[kk], nk[kk]
        if a["pub"] != z["pub"]:
            disc[f"{a['lab']}_solo_{'via' if a['pub'] else 'k'}"] += 1
            if a["lab"] == "pos" and a["prot"]:
                perdidas.append({"volcan": kk[0], "satelite": kk[1], "noche": kk[2],
                                 "publica": "via" if a["pub"] else "K", "vrp_mirova": a["vrp_mirova"]})
    def sin_par(a, otro):
        """Pasadas de un lado sin record del otro: una alerta de MIROVA aquí es una pérdida que el pareo esconde."""
        xs = [a[x] for x in a if a[x]["b"] == b and x not in otro]
        c = collections.Counter(r["lab"] for r in xs)
        return {"n": len(xs), "pos": c["pos"], "pos_publica": sum(r["pub"] for r in xs if r["lab"] == "pos"),
                "protegidas": sum(r["protegida"] for r in xs),
                "protegidas_publica": sum(r["pub"] for r in xs if r["protegida"]),
                "neg_limpio": c["neg_limpio"], "neg_publica": sum(r["pub"] for r in xs if r["lab"] == "neg_limpio"),
                "protegidas_detalle": [{"volcan": r["vol"], "satelite": r["sensor"], "dt": r["dt"].isoformat(),
                                        "vrp_mirova": r["vrp_mirova"], "publica": r["pub"]}
                                       for r in xs if r["protegida"]]}
    detalle = []
    for kk in nvia.keys() & nk.keys():
        if nvia[kk]["lab"] == "pos" and nvia[kk]["prot"] and nvia[kk]["pub"] != nk[kk]["pub"]:
            for x in claves:
                if (x[0], x[1], via[x]["noche"]) == kk and via[x]["lab"] == "pos":
                    detalle.append({"volcan": x[0], "satelite": x[1], "dt": x[2].isoformat(),
                                    "vrp_mirova": via[x]["vrp_mirova"], "dist_ref_tabla": via[x]["dist_ref_tabla"],
                                    "via_pub": via[x]["pub"], "via_disp": via[x]["disp"], "via_dc": via[x]["dc"],
                                    "via_d_mc": via[x]["d_mc"], "k_pub": k[x]["pub"], "k_disp": k[x]["disp"],
                                    "k_dc": k[x]["dc"], "k_d_mc": k[x]["d_mc"]})
    res = {"n_pasadas_pareadas": len(claves),
           "solo_via_sin_par": sum(1 for x in via if via[x]["b"] == b and x not in k),
           "solo_k_sin_par": sum(1 for x in k if k[x]["b"] == b and x not in via),
           "sin_par_via": sin_par(via, k), "sin_par_k": sin_par(k, via),
           "protegidas_discordantes_pasadas": sorted(detalle, key=lambda d: d["dt"]),
           "via": tabla(nvia, pv), "k": tabla(nk, pk), "discordancias": dict(disc),
           "protegidas_discordantes": sorted(perdidas, key=lambda d: (d["noche"], d["volcan"]))}
    if por_volcan:
        res["por_volcan"] = {}
        for vol in bp.VOLS:
            cv = [x for x in claves if x[0] == vol]
            if cv:
                res["por_volcan"][vol] = {"via": tabla(noches([via[x] for x in cv]), [via[x] for x in cv]),
                                          "k": tabla(noches([k[x] for x in cv]), [k[x] for x in cv])}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--k-historia", required=True, help="carpeta con los 11 JSON de data/mirova_equivalent del tag")
    ap.add_argument("--out", default=str(Path(__file__).parent / "salida" / "via_k_mirova.json"))
    ap.add_argument("--remoto", metavar="CARPETA", help="bajar la referencia del remoto de Mirova-v1 a CARPETA (el "
                    "snapshot del repo sólo lo refresca el auto-audit semanal)")
    a = ap.parse_args(argv)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    cons, ocr, proc = SNAP_CONS, SNAP_OCR, {"fuente": "snapshot"}
    if a.remoto:
        info = bajar_remoto(Path(a.remoto))
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
        proc = {"fuente": "remoto", "commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    filas = cargar_referencia_unificada(cons, ocr)
    refs = {"combinado": filas, "tabla": [f for f in filas if f["source"] == "CONS"]}
    temporales = []
    try:
        via_dir, cv = carpeta_filtrada(PROD, lambda r: True)
        k_dir, ck = carpeta_filtrada(Path(a.k_historia), lambda r: "via_codigo_mirova" not in r)
        caidas, _ = carpeta_filtrada(PROD, lambda r: r.get("via_codigo_mirova") is not True)
        n_caidas = sum(len(json.loads((caidas / f"{v}.json").read_text(encoding="utf-8"))["records"]) for v in bp.VOLS)
        temporales += [via_dir, k_dir, caidas]
        salida = {"meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "sha_index_html": bp.sha_git(bp.HTML), "referencia": proc,
                           "sha_cons": bp.sha_git(cons), "sha_ocr": bp.sha_git(ocr), "regla_minimas": MODO_MINIMAS,
                           "records_produccion": cv["dentro"], "records_produccion_sin_via_true": n_caidas,
                           "records_k_tag_k_puro": ck["dentro"], "records_k_tag_con_via_excluidos": ck["fuera"],
                           "ventanas": VENTANAS}, "resultados": {}}
        for nombre_ref, fil in refs.items():
            for vent, por_b in VENTANAS.items():
                for b, (ini, fin) in por_b.items():
                    ref = bp.indexar_referencia(fil, coords, (ini, fin), regla_minimas=MODO_MINIMAS)
                    via = pasadas(via_dir, (ini, fin), coords, inner, ref)
                    kdir = k_dir if vent == "historia" else GUARDIA[b]
                    k = pasadas(kdir, (ini, fin), coords, inner, ref)
                    r = comparar(via, k, b)
                    salida["resultados"][f"{nombre_ref}|{vent}|{b}"] = r
                    v_, k_ = r["via"], r["k"]
                    print(f"{nombre_ref:9s} {vent:13s} {b:8s} {ini}..{fin} pares {r['n_pasadas_pareadas']:6d} | "
                          f"VIA TP {v_['TP']:4d} FN {v_['FN']:4d} FP {v_['FP']:4d} TN {v_['TN']:5d} rec {v_['recall']} "
                          f"prec {v_['precision']} prot {v_['protegidas']}/-{v_['protegidas_perdidas']} "
                          f"med {v_['mediana_cociente']} | K TP {k_['TP']:4d} FN {k_['FN']:4d} FP {k_['FP']:4d} "
                          f"TN {k_['TN']:5d} rec {k_['recall']} prec {k_['precision']} prot {k_['protegidas']}/"
                          f"-{k_['protegidas_perdidas']} med {k_['mediana_cociente']} | disc {r['discordancias']}",
                          flush=True)
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        print("meta:", {k: v for k, v in salida["meta"].items() if k != "ventanas"})
        print("->", a.out)
    finally:
        for t in temporales:
            shutil.rmtree(t, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
