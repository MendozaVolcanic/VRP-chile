# -*- coding: utf-8 -*-
"""Tarea 1.7 del loop. ¿Llega el flag de la caja (`enable_roi1_box_paper`) a TODOS sus consumidores? (A118)

POR QUE. En S148 el flag llegaba solo al primer pase y el segundo recapturaba con el umbral permisivo lo que el
primero rechazaba: el A/B de la caja medio el cableado, no la caja. #738 lo arreglo. Antes de pre-registrar una
corrida hay que comprobarlo de nuevo, y por tres caminos que no comparten supuestos:

  1. FLAGS EFECTIVOS, leidos de `pipeline.profile` con VRP_PROFILE de cada brazo (A89: nunca del YAML). Ademas de
     la caja, los flags sin los cuales la caja no tendria donde actuar: que el primer y el segundo pase tengan
     umbral dual (si no, todo el ROI recibe el permisivo y la geometria no importa) y que los umbrales de cumbre y
     de escena sean distintos.
  2. TRAZA DE LLAMADAS por AST en los tres procesadores: cada llamada a una funcion que aplica el umbral dual
     tiene que recibir la geometria de la caja, sea `roi1_mask=_roi1_mask` o un `is_summit` armado por
     `roi1_summit_mask(..., _roi1_mask)`. Y la lista de los consumidores que siguen usando el CIRCULO
     (`inner_radius_km`), que no son umbrales sino etiqueta, seleccion del cumulo, gate del tablero y magnitud:
     se listan para decidir, uno por uno, si deben o no recibir la caja.
  3. EFECTO, con las funciones REALES del pipeline sobre una escena sintetica (la de
     experiments/_s148_caja_traza/demo_sintetica_segundo_pase.py, ahora con la mascara armada como la arman hoy
     los procesadores: `roi_mask_bbox` sobre lat/lon y `roi1_summit_mask` para el segundo pase): un pixel tibio a
     3,5 km del crater (dentro del circulo de 5 km, fuera de la caja) con un exceso entre el umbral de cumbre y el
     de escena tiene que publicarse con el circulo y NO con la caja, con las dos conectivas (`min` y `max`). Un
     pixel identico dentro de la caja tiene que publicarse en los dos casos (control negativo: la caja no toca lo
     que esta adentro).

Uso: python cableado.py > cableado_salida.txt   (sale con 1 si algo no cuadra)
"""
from __future__ import annotations

import ast, json, os, re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))

BRAZOS = {"K": "_s149_ab_sin_test1_b22_max", "KC": "_s151_ab_sin_test1_b22_max_caja", "KG": "_s151_ab_sin_test1_b22_max_gemelo",
          "B": "_s146_ab_sin_test1", "BC": "_s147_ab_sin_test1_caja", "produccion": "mirova_equivalent"}
CAJA_DECLARADA = {"K": False, "KC": True, "KG": False, "B": False, "BC": True, "produccion": False}
FLAGS = ("PROFILE_NAME", "DATA_SUBDIR", "ENABLE_ROI1_BOX_PAPER", "ROI1_BOX_HALF_KM", "ENABLE_TEST1_PATH",
         "ENABLE_TESTS_23_PROSE_BRANCH", "ENABLE_MODIS_B22_PRIMARY", "ENABLE_FIRST_PASS_TESTS_2_AND_3",
         "ENABLE_DUAL_ROI_FIRST_PASS", "ENABLE_SECOND_PASS_ADJACENT", "ENABLE_DUAL_ROI_SECOND_PASS",
         "ENABLE_SECOND_PASS_INTRA_RADIO_GATE", "ENABLE_DUAL_ROI_BT", "ENABLE_DNTI_DUAL_ROI", "ENABLE_ETI_QUADRATIC_SCENE",
         "ENABLE_FINAL_PIXEL_FILTER", "ENABLE_TEST1_PIXEL_FILTER", "ENABLE_VENT_ANCHORED_CLUSTERING",
         "DNTI_CONTEXTUAL_C1_SUMMIT", "DNTI_CONTEXTUAL_C1_SCENE", "C2_DNTI_SUMMIT_NIGHT", "C2_DNTI_SCENE_NIGHT",
         "C1_SUMMIT_OVERRIDE", "C2_SUMMIT_OVERRIDE", "VIIRS_C2_OVERRIDE_NIGHT", "PATH_D_ONLY_CAP_MW")
PROCESADORES = ("process_viirs.py", "process_viirs_mod.py", "process_modis.py")
# Funciones que aplican el umbral DUAL (cumbre contra escena). Cada llamada tiene que recibir la caja.
UMBRALES = {"first_pass_tests_2_and_3": "roi1_mask", "dual_roi_bt_threshold": "roi1_mask",
            "dual_roi_contextual_dnti_hot_mask": "roi1_mask", "second_pass_adjacent": "is_summit"}


# ---------------------------------------------------------------- 1. flags efectivos
def flags_de(perfil):
    codigo = "import json, pipeline.profile as p; print('FLAGS ' + json.dumps({k: getattr(p, k, 'NO_EXISTE') for k in %r}))" % (FLAGS,)
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=str(RAIZ), env=env, capture_output=True, text=True, encoding="utf-8")
    linea = [l for l in r.stdout.splitlines() if l.startswith("FLAGS ")]
    return json.loads(linea[-1][6:]) if linea else {"error": r.stderr[-500:]}


def seccion_flags():
    print("== 1. FLAGS EFECTIVOS (pipeline.profile con VRP_PROFILE de cada brazo, A89)")
    ok = True; fl = {}
    for n, perfil in BRAZOS.items():
        f = fl[n] = flags_de(perfil)
        if "error" in f:
            print("   %-10s %-36s NO CARGA: %s" % (n, perfil, f["error"])); ok = False; continue
        probs = []
        if f["PROFILE_NAME"] != perfil or f["DATA_SUBDIR"] != perfil:
            probs.append("perfil o directorio %s/%s" % (f["PROFILE_NAME"], f["DATA_SUBDIR"]))
        if f["ENABLE_ROI1_BOX_PAPER"] != CAJA_DECLARADA[n]:
            probs.append("caja %s, declarada %s" % (f["ENABLE_ROI1_BOX_PAPER"], CAJA_DECLARADA[n]))
        if n != "produccion" and f["ENABLE_TEST1_PATH"]:
            probs.append("Test 1 encendido: la palanca no puede actuar (A114)")
        # sin umbral dual en los dos pases, o con umbrales iguales, la geometria del ROI1 no decide nada
        for k in ("ENABLE_FIRST_PASS_TESTS_2_AND_3", "ENABLE_DUAL_ROI_FIRST_PASS", "ENABLE_SECOND_PASS_ADJACENT", "ENABLE_DUAL_ROI_SECOND_PASS"):
            if f[k] is not True:
                probs.append("%s=%s" % (k, f[k]))
        if f["DNTI_CONTEXTUAL_C1_SUMMIT"] >= f["DNTI_CONTEXTUAL_C1_SCENE"] or f["C2_DNTI_SUMMIT_NIGHT"] >= f["C2_DNTI_SCENE_NIGHT"]:
            probs.append("umbral de cumbre no es mas permisivo que el de escena")
        for k in ("C1_SUMMIT_OVERRIDE", "C2_SUMMIT_OVERRIDE", "VIIRS_C2_OVERRIDE_NIGHT"):
            if f[k] is not None:
                probs.append("%s=%s (achica la diferencia cumbre contra escena)" % (k, f[k]))
        if n != "produccion" and probs:
            ok = False
        print("   %-10s %-36s caja %-5s semilado %.1f | Test1 %-5s max %-5s b22 %-5s | dual 1er pase %s, 2do pase %s | C1 %.3f/%.3f C2 %g/%g | %s" % (
            n, perfil, f["ENABLE_ROI1_BOX_PAPER"], f["ROI1_BOX_HALF_KM"], f["ENABLE_TEST1_PATH"], f["ENABLE_TESTS_23_PROSE_BRANCH"],
            f["ENABLE_MODIS_B22_PRIMARY"], f["ENABLE_DUAL_ROI_FIRST_PASS"], f["ENABLE_DUAL_ROI_SECOND_PASS"],
            f["DNTI_CONTEXTUAL_C1_SUMMIT"], f["DNTI_CONTEXTUAL_C1_SCENE"], f["C2_DNTI_SUMMIT_NIGHT"], f["C2_DNTI_SCENE_NIGHT"],
            "OK" if not probs else ("(produccion, informa) " if n == "produccion" else "PROBLEMA: ") + "; ".join(probs)))
    # los pares de la prueba difieren SOLO en la caja (y el gemelo en nada), salvo nombre y directorio
    for a, b in (("K", "KC"), ("K", "KG"), ("B", "BC")):
        if "error" in fl[a] or "error" in fl[b]:
            continue
        dif = sorted(k for k in FLAGS if k not in ("PROFILE_NAME", "DATA_SUBDIR") and fl[a][k] != fl[b][k])
        esperado = [] if b == "KG" else ["ENABLE_ROI1_BOX_PAPER"]
        bien = dif == esperado; ok &= bien
        print("   %s contra %s difieren en %s | esperado %s | %s" % (a, b, dif or "nada", esperado or "nada", "OK" if bien else "FALLA"))
    return ok


# ---------------------------------------------------------------- 2. traza de llamadas
def nombre_llamada(n):
    return n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else None)


def asignaciones(tree):
    """{nombre: [(linea, expresion)]} de todas las asignaciones simples del modulo."""
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.setdefault(t.id, []).append((n.lineno, n.value))
    return out


def recibe_caja(call, asig):
    """(True/False, como): la llamada recibe la geometria de la caja."""
    kw = {k.arg: k.value for k in call.keywords}
    param = UMBRALES[nombre_llamada(call)]
    if param not in kw:
        return False, "sin %s (rige el circulo por defecto)" % param
    v = kw[param]
    if param == "roi1_mask":
        return ast.unparse(v) == "_roi1_mask", "roi1_mask=" + ast.unparse(v)
    # is_summit: tiene que salir de roi1_summit_mask(..., _roi1_mask), directo o por un nombre asignado antes
    nombres = {x.id for x in ast.walk(v) if isinstance(x, ast.Name)}
    if any(isinstance(x, ast.Call) and nombre_llamada(x) == "roi1_summit_mask" for x in ast.walk(v)):
        return True, "is_summit=roi1_summit_mask(...) en la llamada"
    for nm in nombres:
        previas = [(l, e) for l, e in asig.get(nm, []) if l < call.lineno]
        if previas:
            l, e = max(previas, key=lambda x: x[0])
            if isinstance(e, ast.Call) and nombre_llamada(e) == "roi1_summit_mask" and "_roi1_mask" in ast.unparse(e):
                return True, "is_summit=%s, asignado en l. %d con %s" % (nm, l, ast.unparse(e))
            return False, "is_summit=%s, asignado en l. %d con %s" % (nm, l, ast.unparse(e))
    return False, "is_summit=" + ast.unparse(v)


def seccion_traza():
    print("\n== 2. TRAZA DE LLAMADAS (AST): umbrales duales que reciben la caja")
    ok = True
    for f in PROCESADORES:
        src = (RAIZ / "pipeline" / f).read_text(encoding="utf-8"); tree = ast.parse(src); asig = asignaciones(tree)
        arma = [(l, ast.unparse(e)) for l, e in asig.get("_roi1_mask", [])]
        caja_bien = any("roi_mask_bbox" in e and "ROI1_BOX_HALF_KM" in e for l, e in arma)
        guardada = re.search(r"if ENABLE_ROI1_BOX_PAPER and vent_lat is not None and vent_lon is not None:\s*\n\s*_roi1_mask = roi_mask_bbox\(", src)
        ok &= caja_bien and bool(guardada)
        print("   %s: _roi1_mask armada %s | bajo `if ENABLE_ROI1_BOX_PAPER` %s" % (f, arma, "SI" if guardada else "NO"))
        llamadas = sorted((n for n in ast.walk(tree) if isinstance(n, ast.Call) and nombre_llamada(n) in UMBRALES), key=lambda n: n.lineno)
        for c in llamadas:
            bien, como = recibe_caja(c, asig); ok &= bien
            print("      l. %4d %-34s %s | %s" % (c.lineno, nombre_llamada(c), "RECIBE LA CAJA" if bien else "NO LA RECIBE", como))
    print("   umbrales duales:", "todos reciben la caja" if ok else "HAY CONSUMIDORES DE UMBRAL SIN LA CAJA")

    print("\n   Consumidores que siguen usando el CIRCULO (inner_radius_km): no son umbrales; se listan para decidir")
    patron = re.compile(r"(?<![A-Za-z0-9_])(inner_radius_km|inner_km|innerKm)(?![A-Za-z0-9_])")
    for ruta in ["pipeline/" + f for f in PROCESADORES] + ["pipeline/store.py", "pipeline/f5_core.py", "pipeline/clustering.py"]:
        lineas = (RAIZ / ruta).read_text(encoding="utf-8").splitlines()
        for i, l in enumerate(lineas, 1):
            s = l.strip()
            if not patron.search(s) or s.startswith("#") or s.startswith('"') or "def " in s or "inner_km=inner_radius_km" in s.replace(" ", ""):
                continue
            if re.search(r"(<=|>=|<|>)", s) or "inner_radius_km=" in s.replace(" ", ""):
                print("      %s:%d  %s" % (ruta, i, s[:120]))
    html = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(html, 1):
        if "centroid_dist_km > innerKm" in l or "distance_class !== \"summit\"" in l:
            print("      frontend/index.html:%d  %s" % (i, l.strip()[:120]))
    return ok


# ---------------------------------------------------------------- 3. efecto, con las funciones reales
def seccion_efecto():
    import numpy as np
    from pipeline.detection_context import first_pass_tests_2_and_3, second_pass_adjacent, roi1_summit_mask
    from pipeline.scan_geometry import roi_mask_bbox
    print("\n== 3. EFECTO con las funciones reales (escena sintetica de S148, mascara armada como en los procesadores)")
    rng = np.random.default_rng(148)
    N, PX, LAT0, LON0, INNER = 161, 0.375, -39.42, -71.94, 5.0
    yy, xx = np.mgrid[0:N, 0:N]; c = N // 2
    dx, dy = (xx - c) * PX, (yy - c) * PX
    lat = LAT0 + dy / 111.0; lon = LON0 + dx / (111.0 * np.cos(np.radians(LAT0)))
    dist = np.hypot(dx, dy)
    roi = dist <= 25.0
    caja = roi_mask_bbox(lat, lon, LAT0, LON0, 2.5)
    nti_app = -0.95 + rng.normal(0, 0.002, (N, N)); nti0 = nti_app + rng.normal(0, 0.0004, (N, N))
    bt = 270.0 + rng.normal(0, 0.3, (N, N))
    afuera = (c, c + int(round(3.5 / PX)))     # 3,5 km al este: en el circulo, fuera de la caja
    adentro = (c + int(round(1.5 / PX)), c)    # 1,5 km al norte: en la caja
    ok = True
    for conectiva, prosa, exceso in (("min", False, 0.006), ("max", True, 0.015)):
        for nombre, px in (("afuera de la caja", afuera), ("adentro de la caja", adentro)):
            nti = nti0.copy(); nti[px] += exceso; b = bt.copy(); b[px] = 275.0
            res = {}
            for geom, roi1 in (("circulo", None), ("caja", caja)):
                fp, diag = first_pass_tests_2_and_3(nti=nti, nti_app=nti_app, bt=b, roi_mask=roi, dist_km=dist, t_bg=270.0, bt_sanity_k=3.0,
                                                    c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5, c2_deti_summit=5,
                                                    inner_km=INNER, roi1_mask=roi1, c1_dnti_scene=0.010, c1_deti_scene=0.010,
                                                    c2_dnti_scene=10, c2_deti_scene=10, unsuitable_dnti_floor=-np.inf,
                                                    unsuitable_deti_floor=-np.inf, use_prose_branch=prosa)
                # como en process_viirs.py: is_summit_mask = roi1_summit_mask(vent_dist_per_pixel, inner_radius_km, _roi1_mask)
                fin = second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=fp, c1_dnti=0.003, c1_deti=0.003, c2_dnti=5, c2_deti=5,
                                           is_summit=roi1_summit_mask(dist, INNER, roi1), c1_dnti_scene=0.010, c1_deti_scene=0.010,
                                           c2_dnti_scene=10, c2_deti_scene=10, use_prose_branch=prosa)
                res[geom] = (bool(fp[px]), bool(fin[px]))
            esperado = {"circulo": True, "caja": nombre == "adentro de la caja"}
            bien = all(res[g][1] == esperado[g] for g in res); ok &= bien
            print("   conectiva %s, exceso %.3f, pixel %-19s (dist %.2f km, en caja %s) | circulo: 1er pase %s, final %s | caja: 1er pase %s, final %s | %s" % (
                conectiva, exceso, nombre, dist[px], bool(caja[px]), *res["circulo"], *res["caja"], "OK" if bien else "FALLA"))
    return ok


def main():
    ok1 = seccion_flags(); ok2 = seccion_traza(); ok3 = seccion_efecto()
    print("\n== RESUMEN: flags %s | umbrales con la caja %s | efecto %s" % ("OK" if ok1 else "FALLA", "OK" if ok2 else "FALLA", "OK" if ok3 else "FALLA"))
    return 0 if (ok1 and ok2 and ok3) else 1


if __name__ == "__main__":
    sys.exit(main())
