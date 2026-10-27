# -*- coding: utf-8 -*-
"""S165 V375-E, paso 1 (equivalencia, PREREGISTRO_E.md §3 con la adenda 1 §7.3; PREREGISTRO_IMPL_V375E.md §3).

QUÉ MIDE. Sobre las grillas guardadas de los lotes de V375-B y V375-C (S162, S162b y S159), si la vía de pipeline/
(`mirova_v750_codigo`, familia VIIRS375, caja de `caja_v375`) hace lo mismo que el port de `brazos.py` con el brazo
C13, pasada por pasada:
  (1) la grilla de la vía (volcanoes.yaml + grillas_mirova.yaml, paso 375) es la que guardó el lote;
  (2) la MÁSCARA de alertados es idéntica índice por índice;
  (3) el VRP: en escenas de 1 a 4 píxeles contra la salida de MATLAB (o2_375/matlab_v375.json; el port viejo tenía otro
      fondo, adenda §7.3), sobre 4 contra el port tal cual; tolerancia 1e-3 MW, exigido en el 99 % o más;
  (4) la PUBLICACIÓN, con el predicado del tablero ejecutado con node (banco_paridad.correr_node, el mismo de
      evaluar.py), del record de la vía pasado por store.append_record (como en producción) contra el record sintético
      del port de evaluar.py con la regla «cercano» (la que decide en evaluar.py) y con «centroide» (informa).
      Exigido: 100 % y las protegidas idénticas.
Las dos preguntas del instrumento: (a) si la vía no hiciera nada, (2) y (4) fallarían en toda pasada con alertas del port
(hay control: el número de pasadas con alertas se imprime antes); (b) el control negativo del predicado: el record del
port con el VRP x 0 tiene que dejar de publicar en toda pasada donde publicaba (si no, el predicado no mira el VRP).
Una pasada sin grilla o sin resultado es SIN DATO y se cuenta aparte, antes de cualquier número.

Uso: python -I equivalencia_v375e.py [--salida equivalencia_v375e_salida.txt] [--json equivalencia_v375e.json]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
V375 = RAIZ / "experiments/_s162_v375"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(V375))
import banco_paridad as B  # noqa: E402
import brazos as BR  # noqa: E402
import evaluar as E  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
sys.path.insert(0, str(RAIZ / "experiments/_s163_o2alt"))
import delaunay_perturbado as DP  # noqa: E402

TOL_VRP_MW = 1e-3
ART = {"S162": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40116289866"),
       "S162b": Path(r"C:\vrp-trabajo\temporales\s162_v375\run_40131572769"),
       "S159": Path(r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")}
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def objetivos():
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = dict(o)
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        assert o["id"] not in obj
        obj[o["id"]] = dict(o)
    for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in E.EXCLUIDOS:
            assert o["id"] not in obj
            obj[o["id"]] = {**o, "lote": "S159"}
    return obj


def _rellenar_matlab(A, jitter=0.0, semilla=0):
    """La regla de MATLAB por código INDEPENDIENTE de la vía (el del subagente de S163, delaunay_perturbado.py, como
    equivalencia_v750a.py): Delaunay con desempate simbólico en el marco x = fila, y = columna, y NaN fuera de la
    envolvente convexa (MATLAB no extrapola; el DP.rellenar original pone el vecino más cercano ahí)."""
    from scipy.spatial import Delaunay
    Bm = DP.rellenar(A, "xy_fila_col")[0]
    h = ~np.isfinite(np.asarray(A, float))
    if h.any() and (~h).any():
        fil, col = np.indices(A.shape)
        fuera = Delaunay(np.column_stack([fil[~h], col[~h]]).astype(float)).find_simplex(
            np.column_stack([fil[h], col[h]]).astype(float)) < 0
        hh = np.argwhere(h)[fuera]
        Bm[hh[:, 0], hh[:, 1]] = np.nan
    return Bm


def vrp_port_con_regla_matlab(mir, pixeles):
    """«Si sobre 4 no calza, se mira primero el relleno» (adenda §7.3): el VRP del port sobre SU máscara, con el fondo
    de la regla de MATLAB en vez del de Qhull. Diagnóstico: informa, no cambia la vara que decide."""
    ORA = BR.MP.ORA
    mask = np.zeros(mir.shape, bool)
    for q in pixeles:
        mask[q[0], q[1]] = True
    viejo = ORA._fillmissing2_lineal
    ORA._fillmissing2_lineal = _rellenar_matlab
    try:
        return float(BR.MP.vrp(mir, mask, BR.MP.SENSORES["VIIRS375"])["VRP_MW"])
    finally:
        ORA._fillmissing2_lineal = viejo


def record_de_la_via(o, g, mir, tir, r, v):
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    box = MV.caja_v375(g, vlat, vlon)
    rec = MV.procesar_grilla(mir, tir, g, box, r["dayflag"], r["sunglint"], MV.posicion_de(g, vlat, vlon),
                             v["inner_radius_km"], o["sensor"], familia="VIIRS375")
    mascara = MV.detectar_mirova(mir, tir, box, r["dayflag"], r["sunglint"], lam_mir=MV.LAMBDA_I4,
                                 lam_tir=MV.LAMBDA_I5)
    vrp = MV.vrp_mirova(mir, mascara, coef=MV.COEF_VRP_V375)
    return rec, mascara, vrp


def por_el_almacen(rec, nombre, v, tmp):
    """El record de la vía como lo deja store.append_record en producción (las compuertas de K no lo tocan)."""
    from pipeline import store
    rec = json.loads(json.dumps(rec))
    rec.setdefault("datetime_utc", "2026-01-01 05:00")
    rec.setdefault("product_version", "standard")
    viejo = store.DATA_DIR
    store.DATA_DIR = Path(tmp)
    try:
        store.append_record(nombre, rec, max_hotspot_dist_km=v.get("radius_km"),
                            enable_pixel_level_distance_filter=True, max_cluster_pixels=v.get("max_cluster_pixels"),
                            inner_radius_km=v.get("inner_radius_km"), overwrite=True)
    finally:
        store.DATA_DIR = viejo
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(AQUI / "equivalencia_v375e_salida.txt"))
    ap.add_argument("--json", default=str(AQUI / "equivalencia_v375e.json"))
    ap.add_argument("--max", type=int, default=None, help="sólo para probar el script: las primeras N pasadas")
    a = ap.parse_args(argv)
    V = E.volcanes()
    inner_html = B.inner_desde_html()
    obj = objetivos()
    res = {}
    for lote, art in ART.items():
        for i, r in E.leer_resultados(art).items():
            if i in obj and obj[i]["lote"] == lote:
                res[i] = r
    mat = {e["id"]: e for e in json.loads((V375 / "o2_375/matlab_v375.json").read_text(encoding="utf-8"))["escenas"]
           if "C13" in e["brazos"]}

    pr("== 0. cobertura: objetivos", len(obj), dict(collections.Counter(o["lote"] for o in obj.values())))
    filas, sin = [], collections.Counter()
    ids = sorted(obj)[: a.max] if a.max else sorted(obj)
    n_inner_distinto = sum(1 for n, v in V.items() if n in inner_html and v.get("inner_radius_km") != inner_html[n])
    pr("   inner_radius_km de volcanoes.yaml distinto del del tablero en", n_inner_distinto, "volcanes")
    with tempfile.TemporaryDirectory() as tmp:
        for k, i in enumerate(ids):
            o, r = obj[i], res.get(i)
            if r is None or r.get("estado") != "ok":
                sin["sin_resultado_ok"] += 1
                continue
            gz = E.grilla_npz(ART[o["lote"]], i)
            if gz is None:
                sin["sin_grilla_guardada"] += 1
                continue
            mir, tir, _sha = gz
            v = V[o["volcan"]]
            g = MV.grilla_del_volcan(o["volcan"], paso_m=375.0, clave_roi="roi_v375")
            go = o["grilla"]
            dif_g = max(abs(g["ul_x"] - go["ul_x"]), abs(g["ul_y"] - go["ul_y"]), abs(g["x0"] - go["X0"]),
                        abs(g["y0"] - go["Y0"]))
            misma_grilla = g["epsg"] == go["epsg"] and g["n"] == go["n"] and dif_g <= 0.06
            # el port: brazo C13 sobre la grilla del lote (lo que evaluar.py recalcula sin red)
            xc, yc = BR.crater_xy(go, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
            box_p = BR.caja(go, "C13", go["X0"], go["Y0"], xc, yc, v["inner_radius_km"], o["volcan"])
            port = BR.correr_box(mir, tir, go, box_p, go["X0"], go["Y0"], r["dayflag"], r["sunglint"],
                                 BR.MP.SENSORES["VIIRS375"], semillas=0, modo="C13")
            mask_p = {(q[0], q[1]) for q in port["pixeles"]}
            vara, fuente = port["vrp_mw"], "port"
            if 1 <= port["npix"] <= 4:
                m = mat.get(i)
                if m is not None and m["npix"] == port["npix"] and abs(m["vrp_port_mw"] - port["vrp_mw"]) <= 1e-6:
                    vara, fuente = m["vrp_vara_mw"], "matlab"
                else:
                    fuente = "port_sin_matlab"
            # la vía
            rec, mascara, vrp = record_de_la_via(o, g, mir, tir, r, v)
            mask_v = set(zip(*[x.tolist() for x in np.nonzero(mascara)]))
            box_v = MV.caja_v375(g, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
            dvrp = None if port["npix"] == 0 else abs(float(vrp["VRP_MW"]) - float(vara))
            dvrp_regla = None
            if port["npix"] > 0 and dvrp is not None and dvrp > TOL_VRP_MW:
                dvrp_regla = abs(float(vrp["VRP_MW"]) - vrp_port_con_regla_matlab(mir, port["pixeles"]))
            port_vara = {**port, "vrp_mw": vara}
            filas.append({"i": i, "lote": o["lote"], "volcan": o["volcan"], "hora": o["hora_utc"],
                          "clase": o.get("clase"), "prot": bool(o["protegida"]), "misma_grilla": misma_grilla,
                          "dif_grilla_m": round(dif_g, 4), "misma_caja": bool(np.array_equal(box_v, box_p)),
                          "npix_p": port["npix"], "npix_v": len(mask_v), "misma_mascara": mask_v == mask_p,
                          "vrp_vara": vara, "vrp_via": None if not len(mask_v) else float(vrp["VRP_MW"]),
                          "dvrp": dvrp, "dvrp_regla": dvrp_regla, "fuente": fuente,
                          "rec_via": por_el_almacen(rec, o["volcan"], v, tmp),
                          "rec_port": {reg: E.record_sintetico(port_vara, go, v["inner_radius_km"], o["sensor"], reg)
                                       for reg in E.REGLAS},
                          "rec_port_cero": E.record_sintetico(port_vara, go, v["inner_radius_km"], o["sensor"],
                                                              E.REGLA_DECIDE, factor=0.0),
                          "inner": inner_html.get(o["volcan"], v["inner_radius_km"])})
            if (k + 1) % 100 == 0:
                print(f"   ... {k + 1} de {len(ids)}", flush=True)
    pr("   SIN DATO:", dict(sin), "| comparadas:", len(filas), dict(collections.Counter(f["lote"] for f in filas)))
    pr("   con alertas del port:", sum(f["npix_p"] > 0 for f in filas), "| protegidas:", sum(f["prot"] for f in filas))

    # publicación con node
    casos, idx = [], []
    for n, f in enumerate(filas):
        casos.append([E.slim(f["rec_via"]), f["inner"]]); idx.append((n, "via"))
        for reg in E.REGLAS:
            casos.append([E.slim(f["rec_port"][reg]), f["inner"]]); idx.append((n, reg))
        casos.append([E.slim(f["rec_port_cero"]), f["inner"]]); idx.append((n, "cero"))
    P = {k: bool(p[4]) for k, p in zip(idx, B.correr_node(casos))}
    for n, f in enumerate(filas):
        f["pub_via"] = P[(n, "via")]
        f["pub_port"] = {reg: P[(n, reg)] for reg in E.REGLAS}
        f["pub_cero"] = P[(n, "cero")]

    N = len(filas)
    pr("\n== 1. controles del instrumento")
    pub_p = [f for f in filas if f["pub_port"][E.REGLA_DECIDE]]
    pr(f"   el port publica (regla {E.REGLA_DECIDE}) en {len(pub_p)} de {N}; con el VRP x 0 sigue publicando en "
       f"{sum(f['pub_cero'] for f in pub_p)} (tiene que ser 0)")
    ctl_ok = len(pub_p) > 0 and not any(f["pub_cero"] for f in pub_p)

    pr("\n== 2. grilla y caja")
    pr(f"   misma grilla (<= 0,06 m): {sum(f['misma_grilla'] for f in filas)} de {N}; máx diferencia "
       f"{max(f['dif_grilla_m'] for f in filas):.4f} m")
    pr(f"   misma caja (vía con su grilla contra brazos.caja C13 con la del lote): {sum(f['misma_caja'] for f in filas)}"
       f" de {N}")

    pr("\n== 3. máscara y VRP")
    mm = sum(f["misma_mascara"] for f in filas)
    pr(f"   misma máscara índice por índice: {mm} de {N}")
    con = [f for f in filas if f["npix_p"] > 0 and f["misma_mascara"]]
    ok_vrp = [f for f in con if f["dvrp"] is not None and f["dvrp"] <= TOL_VRP_MW]
    frac_vrp = len(ok_vrp) / len(con) if con else float("nan")
    por_fuente = collections.Counter((f["fuente"], f["dvrp"] <= TOL_VRP_MW) for f in con)
    pr(f"   VRP a {TOL_VRP_MW} MW: {len(ok_vrp)} de {len(con)} con alertas ({frac_vrp:.4f}); por vara {dict(por_fuente)}")
    peores = sorted(con, key=lambda f: -(f["dvrp"] or 0))[:8]
    pr("   mayores diferencias:", [(f["i"], f["volcan"], f["npix_p"], f["fuente"], round(f["dvrp"], 6)) for f in peores])
    fuera = [f for f in con if f["dvrp"] is not None and f["dvrp"] > TOL_VRP_MW]
    calza_regla = [f for f in fuera if f["dvrp_regla"] is not None and f["dvrp_regla"] <= TOL_VRP_MW]
    pr(f"   relleno (diagnóstico, adenda §7.3): de las {len(fuera)} fuera de tolerancia, {len(calza_regla)} calzan a "
       f"{TOL_VRP_MW} MW con el port usando el fondo de la regla de MATLAB (código independiente de S163)")
    pr("     ", [(f["i"], f["volcan"], f["npix_p"], f["fuente"], round(f["dvrp"], 6),
                  None if f["dvrp_regla"] is None else round(f["dvrp_regla"], 9)) for f in fuera][:40])
    dif_m = [(f["i"], f["lote"], f["volcan"], f["hora"], f["npix_p"], f["npix_v"]) for f in filas
             if not f["misma_mascara"]]
    if dif_m:
        pr("   máscaras distintas:", dif_m[:40])

    pr("\n== 4. publicación (predicado del tablero con node)")
    out_pub = {}
    for reg in E.REGLAS:
        ig = [f for f in filas if f["pub_via"] == f["pub_port"][reg]]
        dif = [f for f in filas if f["pub_via"] != f["pub_port"][reg]]
        prot_dif = [f for f in dif if f["prot"]]
        out_pub[reg] = {"iguales": len(ig), "de": N, "distintas": [(f["i"], f["volcan"], f["hora"], f["pub_via"],
                                                                     f["pub_port"][reg], f["npix_p"],
                                                                     (f["rec_via"].get("primary_cluster") or {})
                                                                     .get("centroid_dist_km"),
                                                                     f["rec_port"][reg]["primary_cluster"]
                                                                     and f["rec_port"][reg]["primary_cluster"]
                                                                     ["centroid_dist_km"], f["inner"], f["prot"])
                                                                    for f in dif],
                        "protegidas_distintas": len(prot_dif)}
        pr(f"   regla {reg}{' (DECIDE en evaluar.py)' if reg == E.REGLA_DECIDE else ''}: igual en {len(ig)} de {N}; "
           f"protegidas distintas {len(prot_dif)}")
        for d in out_pub[reg]["distintas"][:30]:
            pr("     ", d)
    dif_solo_dist = [f for f in filas if f["pub_via"] != f["pub_port"][E.REGLA_DECIDE] and f["misma_mascara"]
                     and (f["dvrp"] is None or f["dvrp"] <= TOL_VRP_MW)]
    pr(f"   de las distintas con la regla que decide, con máscara y VRP iguales (sólo la regla de distancia): "
       f"{len(dif_solo_dist)}")

    pr("\n== 5. veredicto (PREREGISTRO_IMPL_V375E.md §3)")
    equiv_det = mm == N and all(f["misma_grilla"] and f["misma_caja"] for f in filas)
    equiv_vrp = frac_vrp >= 0.99
    pub_ok = out_pub[E.REGLA_DECIDE]["iguales"] == N
    if not ctl_ok:
        v = "INVALIDO POR INSTRUMENTO"
    elif not (equiv_det and equiv_vrp):
        v = "NO EQUIVALENTE"
    elif pub_ok:
        v = "EQUIVALENTE"
    elif len(dif_solo_dist) == N - out_pub[E.REGLA_DECIDE]["iguales"]:
        v = "NO EQUIVALENTE POR LA REGLA DE DISTANCIA"
    else:
        v = "NO EQUIVALENTE"
    pr(f"   detección (grilla, caja, máscara): {'SI' if equiv_det else 'NO'}; VRP >= 99 %: {'SI' if equiv_vrp else 'NO'};"
       f" publicación 100 % con «{E.REGLA_DECIDE}»: {'SI' if pub_ok else 'NO'}")
    pr("   VEREDICTO:", v)
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(a.json).write_text(json.dumps({"veredicto": v, "publicacion": out_pub,
                                        "filas": [{k: f[k] for k in ("i", "lote", "volcan", "hora", "clase", "prot",
                                                                     "npix_p", "npix_v", "misma_mascara", "vrp_vara",
                                                                     "vrp_via", "dvrp", "dvrp_regla", "fuente",
                                                                     "pub_via",
                                                                     "pub_port")} for f in filas]},
                                       ensure_ascii=False, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
