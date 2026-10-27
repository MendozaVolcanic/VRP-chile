# -*- coding: utf-8 -*-
"""S165, VIIRS 750: la regla de posición de la vía contra «cercano» sobre el censo del oráculo de S159. Sólo lectura.

QUÉ HACE. El censo del oráculo de S159 (D:\\vrp-trabajo\\temporales\\s159_oraculo, censo 39713438252 más el rescate
39715348772; objetivos en experiments/_s159/oraculo_censo/objetivos.json) corrió el código de MIROVA de VIIRS 750
sobre la grilla de la regla GEO de cada pasada nocturna (5.746 pasadas, 2026-04-01 a 2026-10-21) y guardó los
alertados de la caja «def» (geo_linear: fila, columna, zona, distancia, M13), que es la caja que la vía usa en los 11
volcanes (grillas_mirova.yaml: roi_v750 def). No guardó la grilla, así que aquí no se puede correr procesar_grilla: la
regla de la vía se aplica a esa máscara con la función importada de pipeline/ (comun.reglas, _cumulo_del_mas_radiante)
y el record se arma con comun.record_desde_pixeles, que modis.py y v375.py cotejan contra procesar_grilla. Que la vía
reproduce la máscara del oráculo lo midió V750-A (experiments/_s162_v750a/equivalencia_v750a_salida.txt, 1.020 casos).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) La grilla de la vía tiene que ser la del objetivo, y el punto de referencia del
censo tiene que calzar con la distancia que guardó el oráculo (q[3]); se cuentan las que no. (2) control_predicado.
Uso: python v750.py  (escribe v750_salida.txt)
"""
import collections
import io
import json
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import comun as C  # noqa: E402
import banco_paridad as B  # noqa: E402

MV = C.MV
OBJ = C.RAIZ / "experiments/_s159/oraculo_censo/objetivos.json"
ART = [Path(r"D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252"),
       Path(r"D:\vrp-trabajo\temporales\s159_oraculo\rescate_39715348772")]
CAJA = "geo_linear"
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def cargar(dirs):
    """Como experiments/_s159/oraculo_censo/02_analizar.py::cargar: gana el resultado «ok»."""
    res = {}
    for d in dirs:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    return res


def clase(o):
    if o["lab"] == "pos":
        return "protegida" if o["protegida"] else "bajo1"
    return "neg_limpio" if o["lab"] == "neg_limpio" else "resto"


def main():
    t0 = time.time()
    pr("== 0. procedencia")
    pr("   código:", json.dumps(C.procedencia_codigo()))
    pr("   regla de posición importada igual a origin/main:", json.dumps(C.misma_regla_que_main()))
    pr("   objetivos:", OBJ, "sha256", C.sha256(OBJ))
    ctl = C.control_predicado()
    pr("   control del predicado (summit a 1 km publica, far a 9 km no):", ctl, "OK" if ctl == [True, False] else "FALLA")
    obj = {o["id"]: o for o in json.loads(OBJ.read_text(encoding="utf-8"))}
    res = cargar(ART)
    pr(f"   objetivos {len(obj)}, ventana {min(o['hora_utc'] for o in obj.values())} a "
       f"{max(o['hora_utc'] for o in obj.values())}; resultados {len(res)}:",
       dict(collections.Counter(r.get("estado") for r in res.values())))
    V = C.volcanes()
    inner_html = B.inner_desde_html()
    lam = MV.FAMILIAS["VIIRS750"]["lam_mir"]
    sin = collections.Counter()
    filas = []
    dif_g, ref_mal = [], 0
    for i in sorted(obj):
        o, r = obj[i], res.get(i)
        if r is None or r.get("estado") != "ok":
            sin[(r or {}).get("estado", "sin_resultado")] += 1
            continue
        p = (r.get("oraculo") or {}).get(CAJA)
        if p is None:
            sin["sin_caja_def"] += 1
            continue
        v = V[o["volcan"]]
        g = MV.grilla_del_volcan(o["volcan"])
        go = o["grilla"]
        dif_g.append(max(abs(g["ul_x"] - go["ul_x"]), abs(g["ul_y"] - go["ul_y"])))
        la, lo = C.get_detection_anchor(v)
        pos = MV.posicion_de(g, la, lo)
        ref = (33.0, 33.0)                     # el oráculo mide q[3] desde la celda (33, 33): se comprueba abajo
        f = {"id": i, "volcan": o["volcan"], "hora": o["hora_utc"], "lab": o["lab"], "clase": clase(o),
             "npix_via": int(p.get("npix") or 0)}
        if f["npix_via"]:
            celdas = [(q[0], q[1]) for q in p["pixeles"]]
            rad = [q[4] for q in p["pixeles"]]
            ref_mal += sum(1 for q in p["pixeles"] if abs(((q[0] - 33) ** 2 + (q[1] - 33) ** 2) ** 0.5 * 0.75 - q[3]) > 6e-3)
            d = C.reglas(celdas, rad, g["n"], pos, ref, 0.75)
            rec = C.record_desde_pixeles(celdas, rad, g, pos, v["inner_radius_km"], o["sensor"], p["vrp_mw"], lam)
            f["d"] = d
            f["vrp_via"] = rec["vrp_mw"]
            f["_rec"] = {"via": rec, "cerc_cr": C.variante(rec, d["cerc_cr"], v["inner_radius_km"]),
                         "cerc_ref": C.variante(rec, d["cerc_ref"], v["inner_radius_km"])}
        filas.append(f)
    con = [f for f in filas if f["npix_via"]]
    pr("   SIN DATO:", dict(sin), "| evaluadas:", len(filas), "| por clase:",
       dict(collections.Counter(f["clase"] for f in filas)))
    pr(f"   con alertados (caja def del oráculo): {len(con)}; máx diferencia de grilla vía contra objetivo (m): "
       f"{max(dif_g):.4f}; píxeles cuya distancia guardada no calza con la celda (33, 33): {ref_mal}")
    pr("   (X0, Y0 de grillas_mirova.yaml está en la fila 32,67 y la columna 33,33 de esta grilla; el oráculo mide desde "
       "el centro de la celda 33, 33, a 0,35 km o menos de X0, Y0)")

    casos, idx = [], []
    for n, f in enumerate(con):
        v = V[f["volcan"]]
        for regla, rr in f["_rec"].items():
            st = C.por_el_almacen(rr, f["volcan"], v, f["hora"])
            f.setdefault("dc_store", {})[regla] = None if st is None else st.get("distance_class")
            casos.append((st, inner_html[f["volcan"]]))
            idx.append((n, regla))
    P = C.publicar(casos)
    for (n, regla), p in zip(idx, P):
        con[n][f"pub_{regla}"] = p
    for f in filas:
        if not f["npix_via"]:
            f.update({"pub_via": False, "pub_cerc_cr": False, "pub_cerc_ref": False})
    pr("   el almacén cambió la distance_class de alguna variante:",
       sum(1 for f in con for regla, rr in f["_rec"].items() if f["dc_store"][regla] != rr.get("distance_class")))

    pr("\n== 1. cambios de publicación (predicado del tablero con node)")
    res_c = C.resumen_cambios(filas, pr, "VIIRS 750")
    pr("   distancias distintas por más de una celda (0,75 km) entre vía y cercano, sin importar la publicación:",
       {r: sum(1 for f in con if abs(f["d"]["via"] - f["d"][r]) > 0.75) for r in ("cerc_cr", "cerc_ref")})
    cambios = []
    for f in con:
        if f["pub_via"] != f["pub_cerc_cr"] or f["pub_via"] != f["pub_cerc_ref"]:
            cambios.append({k: f[k] for k in ("id", "volcan", "hora", "lab", "clase", "npix_via", "vrp_via",
                                              "pub_via", "pub_cerc_cr", "pub_cerc_ref")} |
                           {"d": {k: round(f["d"][k], 3) for k in ("via", "cerc_cr", "cerc_ref", "via_ref")},
                            "n_cumulo": f["d"]["n_cumulo"], "inner": V[f["volcan"]]["inner_radius_km"]})
    idxr, proc = C.cargar_referencia()
    pr("   referencia de MIROVA del cotejo:", json.dumps({k: {kk: v[kk] for kk in ("sha_commit", "fecha_commit", "sha256")}
                                                         for k, v in proc.items() if k.endswith(".csv")}))
    pr("   detalle de las que cambian (con lo que MIROVA tiene hoy en esa pasada):")
    for c in cambios:
        c["mirova_hoy"] = [{k: x[k] for k in ("source", "tipo", "vrp_mw", "dist_km")}
                           for x in C.parear(idxr, c["volcan"], "VIIRS750", c["hora"])]
        pr("     ", json.dumps(c, ensure_ascii=False))
    det = C.cotejo([{"volcan": f["volcan"], "hora": f["hora"], "clase": f["clase"], "d": f["d"]} for f in con],
                   idxr, "VIIRS750", C.CELDA_KM["VIIRS750"], pr, "VIIRS 750")
    (C.AQUI / "v750_cambios.json").write_text(json.dumps({"resumen": res_c, "cambios": cambios}, ensure_ascii=False,
                                                         indent=1), encoding="utf-8")
    (C.TEMP / "v750.json").write_text(json.dumps({"resumen": res_c, "cambios": cambios, "cotejo": det,
                                                  "sin_dato": dict(sin), "n": len(filas)}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    pr(f"\nlisto en {time.time() - t0:.0f} s")
    (C.AQUI / "v750_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
