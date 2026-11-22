# -*- coding: utf-8 -*-
"""Línea base del pre-registro (S194): lo que se puede medir HOY sin datos del laboratorio, para el crítico.

POR QUÉ. Antes de sellar un criterio hay que saber si puede dar distinto de cero (A116) y dónde se satura (A114).
Todo sale de producción (`data/mirova_equivalent/`) y de NHI-v1; nada de esto mira al laboratorio, que no existe aún,
así que no adelanta el resultado:
  1. tasa de publicación de producción en negativos limpios, por pasada y por noche de volcán, por sensor, en los 10
     volcanes de la zona A (`banco_paridad`, mismo etiquetador y predicado del tablero que usará la calibración);
  2. cuántos negativos limpios tiene cada noche de volcán (para ver qué hace una tasa del 30 % por pasada a la noche);
  3. series NHI desde 2026-02-15: escenas, alertas, tasa basal, nubosidad por sensor;
  4. cuántas escenas NHI se parean con una noche observada de producción (techo de unidades S + N por volcán) y
     cuántas de esas noches producción no publica (techo de N).

Uso: python experiments/_s194_lab_zona_a/medir_base.py --nhi-dir <carpeta con las 9 series> --dest <tmp> --fin AAAA-MM-DD
Escribe salida_medir_base.json y salida_medir_base.txt junto a este archivo.
"""
import argparse
import collections
import importlib.util
import json
import statistics
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("evaluar_s194", AQUI / "evaluar.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhi-dir", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--fin", required=True)
    a = ap.parse_args()
    import banco_paridad as bp
    lineas, out = [], {"fin": a.fin}

    def p(s=""):
        lineas.append(s)
        print(s, flush=True)

    # 1 y 2: negativos limpios de producción
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    ventana = (E.VENTANA_CALIBRACION_INICIO, a.fin)
    info = bp.bajar_remoto(Path(a.dest))
    filas = bp.cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                           Path(info["registro_vrp_ocr.csv"]["path"]))
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    recs = [r for r in bp.cargar_nuestros(coords, inner, ventana, excluir_escenas_invalidas=True)
            if r["vol"] in E.VOLCANES_ZONA_A]
    bp.etiquetar(recs, por_vb, ns, nv)
    out["referencia"] = {"commit_cons": info["registro_vrp_consolidado.csv"]["sha"],
                         "commit_ocr": info["registro_vrp_ocr.csv"]["sha"]}
    p("== 1. Producción en negativos limpios, %s a %s, 10 volcanes de la zona A (sin Cordón Caulle)" % ventana)
    out["neg_limpio"] = {}
    for sen in E.SENSORES + (None,):
        neg = [r for r in recs if r["lab"] == "neg_limpio" and (sen is None or r["b"] == sen)]
        noches = collections.defaultdict(list)
        for r in neg:
            noches[(r["vol"], r["noche"])].append(r["pub"])
        n_pub = sum(r["pub"] for r in neg)
        n_noche_pub = sum(any(v) for v in noches.values())
        k = [len(v) for v in noches.values()]
        q = statistics.quantiles(k, n=4) if len(k) > 1 else [None, None, None]
        nombre = sen or "TRES SENSORES"
        d = {"pasadas": len(neg), "pasadas_pub": n_pub, "tasa_pasada": round(n_pub / len(neg), 4) if neg else None,
             "noches": len(noches), "noches_pub": n_noche_pub,
             "tasa_noche": round(n_noche_pub / len(noches), 4) if noches else None,
             "neg_por_noche_mediana": statistics.median(k) if k else None, "neg_por_noche_q1_q3": [q[0], q[2]],
             "noche_si_30_por_pasada_independiente": round(1 - 0.7 ** statistics.median(k), 4) if k else None}
        out["neg_limpio"][nombre] = d
        p("%-13s pasadas %5d pub %4d (%.4f) | noches %4d pub %4d (%.4f) | negativos por noche: mediana %s, q1 %s, "
          "q3 %s | noche con 30 %% por pasada, si fueran independientes (SOSPECHA): %.4f"
          % (nombre, d["pasadas"], d["pasadas_pub"], d["tasa_pasada"] or 0, d["noches"], d["noches_pub"],
             d["tasa_noche"] or 0, d["neg_por_noche_mediana"], q[0], q[2], d["noche_si_30_por_pasada_independiente"] or 0))

    # 3: NHI
    nhi = E.cargar_nhi(a.nhi_dir)
    p()
    p("== 3. NHI-v1 desde %s hasta %s" % (E.VENTANA_INICIO, a.fin))
    out["nhi"] = {}
    for vol in E.VOLCANES_NHI:
        es = [x for x in nhi[vol] if E.VENTANA_INICIO <= x.get("fecha", "") <= a.fin and x.get("alerta") is not None]
        al = sum(bool(x["alerta"]) for x in es)
        nub = {s: sorted(x["cloud_cover"] for x in es if x.get("sensor") == s and x.get("cloud_cover") is not None)
               for s in ("Sentinel-2", "Landsat")}
        estr = collections.Counter(E.estrato_nube(x.get("cloud_cover")) for x in es)
        out["nhi"][vol] = {"escenas": len(es), "alertas": al, "tasa": round(al / len(es), 4) if es else None,
                           "nube_min_mediana_max": {s: ([v[0], statistics.median(v), v[-1]] if v else None)
                                                    for s, v in nub.items()},
                           "estratos_nube": [estr.get(0, 0), estr.get(1, 0), estr.get(2, 0)]}
        p("%-17s escenas %3d alertas %3d tasa %.3f | estratos nube <=20/20-50/>50: %s | nube S2 %s L %s"
          % (vol, len(es), al, al / len(es) if es else 0, out["nhi"][vol]["estratos_nube"],
             out["nhi"][vol]["nube_min_mediana_max"]["Sentinel-2"], out["nhi"][vol]["nube_min_mediana_max"]["Landsat"]))

    # 4: techo de unidades, con producción en los dos lados (A o N: nunca S, no hay laboratorio)
    pas = E.cargar_pasadas(ROOT / "data" / "mirova_equivalent", E.VENTANA_INICIO, a.fin)
    noches = E.clasificar_noches(pas, [dict(x) for x in pas])
    p()
    p("== 4. Escenas NHI pareadas con una noche observada de producción (techo de S + N) y de esas, noches en que "
      "producción no publica (techo de N)")
    out["pareo"] = {}
    for vol in E.VOLCANES_NHI:
        nv_ = {n: i for (v, n), i in noches.items() if v == vol}
        todas = {n: dict(i, clase="N" if i["clase"] in ("A", "N") else i["clase"]) for n, i in nv_.items()}
        techo = E.parear_nhi(nhi[vol], todas, fin=a.fin)
        solo_n = E.parear_nhi(nhi[vol], nv_, fin=a.fin)
        out["pareo"][vol] = {"noches_observadas": sum(i["clase"] is not None for i in nv_.values()),
                             "unidades_techo": len(techo), "unidades_N_hoy": len(solo_n),
                             "alertas_en_N_hoy": sum(u["alerta"] for u in solo_n.values())}
        p("%-17s noches observadas %4d | unidades pareadas %3d | de ellas sin publicación de producción %3d "
          "(alerta NHI en %d)" % (vol, out["pareo"][vol]["noches_observadas"], len(techo), len(solo_n),
                                  out["pareo"][vol]["alertas_en_N_hoy"]))
    (AQUI / "salida_medir_base.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                 encoding="utf-8", newline="\n")
    (AQUI / "salida_medir_base.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
