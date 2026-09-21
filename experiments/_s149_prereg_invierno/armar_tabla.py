# -*- coding: utf-8 -*-
"""S149. Arma una tabla por pasada con dos brazos, para CUALQUIER ventana y referencia. Generaliza
experiments/_s148_verificador_resultado/r1_tabla.py, que tenia rutas y ventana de septiembre fijas
(verificador del pre-registro, H5). Usa el predicado y el etiquetador del evaluador (node y
banco_paridad), no una copia.

  python armar_tabla.py --control DIR --brazo DIR --cons CSV --ocr CSV --desde 2026-09-01 --hasta 2026-09-20 --out tabla.json
"""
import argparse, json, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp


def main():
    ap = argparse.ArgumentParser()
    for k in ("control", "brazo", "cons", "ocr", "desde", "hasta", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    ventana = (a.desde, a.hasta)
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
    filas = ev.cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
    tabla = {}
    for rol, d in (("control", a.control), ("brazo", a.brazo)):
        recs = ev.cargar_brazo(Path(d), coords, inner, ventana)
        bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
        for r in recs:
            ff = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
            nsr = ns.get((r["vol"], r["b"], r["noche"]), {"alerta": False, "fp": False})
            tabla.setdefault("|".join(ev.clave(r)), {})[rol] = {
                "lab": r["lab"], "pub": int(bool(r["pub"])), "disp": r["disp"], "vrp_ref": r.get("vrp_ref"),
                "pc_lat": r["pc_lat"], "pc_lon": r["pc_lon"], "pc_dist": r["pc_dist"], "z": r["z"],
                "plataforma": r.get("plataforma"),
                "rutina_pasada": any(f["tipo"] == "RUTINA" and f["source"] == "CONS" and (f["vrp_mw"] or 0) == 0 for f in ff),
                "noche_con_alerta_sensor": bool(nsr["alerta"]),
                "alerta_solo_ocr": bool(ff) and all(f["source"] != "CONS" for f in ff if bp.es_alerta(f["tipo"])) and any(bp.es_alerta(f["tipo"]) for f in ff)}
    Path(a.out).write_text(json.dumps({"ventana": ventana, "n_ref": n_ref, "pasadas": tabla}, ensure_ascii=False), encoding="utf-8")
    print("pasadas:", len(tabla), "| en ambos brazos:", sum(1 for v in tabla.values() if len(v) == 2), "| filas de referencia:", n_ref)


if __name__ == "__main__":
    main()
