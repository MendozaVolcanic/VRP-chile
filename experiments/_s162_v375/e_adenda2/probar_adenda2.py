# -*- coding: utf-8 -*-
"""S166 V375-E, adenda 2: batería del lector de posición y del generador de la lista de pasadas lejanas.

Escenas SINTÉTICAS (nunca los datos del marco: la lectura retrospectiva de E no se mira antes del sello), con el
predicado del tablero ejecutado con node, el almacén real y evaluar.py real. La identidad del brazo radiante y del pico
con `procesar_grilla` se prueba además sobre las 7 grillas reales de `tests/datos_s165_v375/` (sólo distancias; no se
calcula ninguna lectura sobre ellas).

Escenas (cráter en la celda (40, 40), paso 0,375 km, inner 5 km salvo donde se diga):
  LEJANA     alertado débil en el cráter y cúmulo brillante a ~15 km: radiante far, cercano summit, pico far
  BORDE      cúmulo que cruza el radio interior, centroide adentro y pico afuera: radiante summit, pico far
  UNO        un solo alertado: los tres brazos iguales (C1)
  PICOCERCA  el más radiante en el cráter y un cúmulo más débil lejos: los tres summit
  ANILLO     cuadro de alertados a 1,5 km alrededor del cráter, inner 1 km: radiante summit, cercano y pico far
  VACIA      sin alertados
Dependencias fuera de la carpeta (N-4 del verificador corto): RAIZ tiene que ser un repositorio git con el commit
533398f8f (C-G1 lo compara con `git rev-parse`; si se corre desde un árbol extraído, GIT_DIR tiene que apuntar al repo), y
la copia de los records de ese commit en D:/vrp-trabajo/temporales/s159_n/data_main (prueba de CRLF del generador); sin
ellas la batería da FALLA en esas dos pruebas, no SIN DATO. El nulo (`mutar_adenda2.py`) depende además del fin de línea
del checkout (N-5): L42 (`blob_git` sin normalizar CRLF) sólo se atrapa si `pipeline/mirova_v750_codigo.py` está en
CRLF, como en el checkout de Windows con core.autocrlf; en un árbol LF sobrevive y el nulo da 75 de 77.
Uso: python -I probar_adenda2.py [--dir <carpeta con los módulos a probar>]  (exit 0 si todo pasa)
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
V375 = AQUI.parent
RAIZ = V375.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(V375))
RES = []


def cargar(nombre, d):
    spec = importlib.util.spec_from_file_location(f"{nombre}_bat", Path(d) / f"{nombre}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ok(nombre, cond, extra=""):
    RES.append((nombre, bool(cond)))
    print(("PASA " if cond else "FALLA") + f"  {nombre} {extra}", flush=True)


# ---------------------------------------------------------------- escenas sintéticas
N, PASO = 81, 0.375
CR = (40.0, 40.0)


def escena(celdas, crater=CR, ref=CR, inner=5.0, vrp=1.5, rec_mal=None):
    """celdas: [(fila, col, radiancia)]. Devuelve (mascara, m13, dist, rec) con el record como lo arma procesar_grilla
    (los campos que el lector lee)."""
    from pipeline import mirova_v750_codigo as MV
    m = np.zeros((N, N), bool)
    L = np.zeros((N, N))
    for f, c, r in celdas:
        m[f, c] = True
        L[f, c] = r
    dist = LP.distancias(m, L, crater, ref, PASO, MV._cumulo_del_mas_radiante)
    if dist is None:
        rec = {"sensor": "VIIRS_NOAA20", "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None,
               "anomaly_pixels": [], "via_codigo_mirova": True, "triggered_test1": False, "t_max_k": None}
        return m, L, None, rec
    pix = [{"dist_km": round(float(np.hypot(f - crater[0], c - crater[1]) * PASO), 2), "bt_k": 300.0, "fila": f,
            "col": c} for f, c, _ in celdas]
    rec = {"sensor": "VIIRS_NOAA20", "vrp_mw": vrp, "t_max_k": 320.0, "triggered_test1": False, "via_codigo_mirova": True,
           "distance_class": LP.clase_dc(dist["radiante"], inner), "anomaly_pixels": pix,
           "primary_cluster": {"vrp_mw": vrp, "n_pixels": dist["n_cumulo"], "centroid_dist_km": round(dist["radiante"], 3)},
           "hotspot_dist_km": round(dist["pico"], 3), "final_hotspot_dist_km": round(dist["radiante"], 3)}
    if rec_mal:
        rec["primary_cluster"]["centroid_dist_km"] += rec_mal
    return m, L, dist, rec


def celdas_lejana():
    # alertado débil en el cráter; cúmulo brillante de 3 a 15 km al este (40 celdas)
    return [(40, 40, 0.5), (40, 80, 3.0), (41, 80, 2.5), (39, 80, 2.0)]


def celdas_borde():
    # cúmulo horizontal de la columna 50 a la 55 (3,75 a 5,6 km), el pico en la 55 (5,63 km > 5): centroide 4,7 km
    return [(40, c, 1.0 + (2.0 if c == 55 else 0.0)) for c in range(50, 56)]


def celdas_uno():
    return [(41, 41, 1.0)]


def celdas_picocerca():
    return [(40, 40, 4.0), (40, 80, 1.0), (41, 80, 1.0)]


def celdas_anillo():
    # cuadro de lado 9 (Chebyshev 4 celdas = 1,5 km) alrededor del cráter; el más brillante en una esquina
    return [(40 + a, 40 + b, 3.0 if (a, b) == (4, 4) else 1.0) for a in range(-4, 5) for b in range(-4, 5)
            if max(abs(a), abs(b)) == 4]


def pasada(i, celdas, clase, vol="Lascar", hora="2026-07-01 05:00", pub_prod=1, lote="S162", tabla=True, prot=None,
           inner=5.0, crater=CR, ref=CR, vrp=1.5, mirova_vrp=None, dist_ref=None, mirova=None, rec_mal=None,
           vrp_port=None, dc_mal=False, m14=None, ref_m14=None, vrp_port_vieja=None):
    m, L, dist, rec = escena(celdas, crater, ref, inner, vrp, rec_mal)
    prot = clase == "pos_prot" if prot is None else prot
    o = {"id": i, "lote": lote, "clase": clase, "estrato": f"{vol}|z<=40", "volcan": vol, "hora_utc": hora,
         "protegida": prot, "mirova_vrp": (mirova_vrp if mirova_vrp is not None else (1.5 if prot else 0.3)
                                           if clase.startswith("pos") else 0.0),
         "alerta_tabla": tabla, "partida": False, "pub_prod": pub_prod, "z": 20.0, "sensor": "VIIRS_NOAA20",
         "mirova": mirova or [], "dist_ref": dist_ref}
    if ref_m14 is not None:
        o["ref_M14"] = ref_m14
    p = {"rec": rec, "dist": dist, "npix": int(m.sum()), "inner": inner, "inner_v": inner,
         "vrp_port": (vrp if vrp_port is None else vrp_port) if dist else None, "vrp_via": vrp if dist else None,
         "vrp_port_vieja": (vrp if vrp_port_vieja is None else vrp_port_vieja) if dist else None,
         "mascara_igual": True, "k_rec": None,
         "dc_almacen_igual": {a: not (dc_mal and a == "cercano") for a in LP.BRAZOS_POS} if dist else {},
         "m14": m14, "geom": {"sensor_zenith": 20.0}}
    return o, p


def meta_de(obj):
    import collections
    c = collections.Counter((o["clase"], o["estrato"]) for o in obj.values()
                            if o["clase"] in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"))
    meta = {k: {} for k in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto")}
    for (cl, h), n in c.items():
        meta[cl][h] = {"N": n}
    for cl in ("neg_pub", "neg_resto"):
        meta[cl].setdefault("X|z<=40", {"N": 10})
    return meta


def publicar(casos):
    import banco_paridad as B
    return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inner] for r, inner in casos])]


class Nada(dict):
    """Una lectura que no existe (el lector se detuvo antes por un control caído). Cualquier aserción sobre ella da
    falso, así que la batería la ve como FALLA por aserción y no como una excepción (nulo por mutaciones, S156)."""
    def __missing__(self, k):
        return Nada()

    def startswith(self, *a):
        return False


def envolver(x):
    if isinstance(x, dict):
        return Nada({k: envolver(v) for k, v in x.items()})
    return x


def correr(lista, art_far=True, N=None, sin_dato=()):
    """N: {(clase, estrato): N} para pesos distintos de 1; sin_dato: objetivos sin pasada procesada (SIN DATO)."""
    obj = {o["id"]: o for o, _ in lista}
    pas = {o["id"]: p for o, p in lista}
    meta = meta_de(obj)
    for (c, h), n in (N or {}).items():
        meta[c][h] = {"N": n}
    for o in sin_dato:
        obj[o["id"]] = o
    LP.L.clear()
    out, f = LP.analizar(pas, obj, meta, publicar, E, art_far)
    return envolver(out), f


def intento(fn):
    """Lo que devuelve fn() o la excepción como texto: una guarda rota que lanza en vez de devolver 2 es salida
    equivocada, y la aserción del escenario la ve."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        return repr(e)


def base_marco(n_neg=3):
    """Un marco mínimo con controles que pasan: una UNO (C1), negativos vacíos y un control de vida sano."""
    lst = [pasada(1, celdas_uno(), "pos_bajo", vol="Isluga", hora="2026-07-02 05:00")]
    for k in range(n_neg):
        lst.append(pasada(10 + k, [], "neg_resto", vol="Llaima", hora=f"2026-07-0{k + 3} 05:00", pub_prod=0))
    lst.append(pasada(29000, [(40, 40, 1.0), (40, 41, 1.0)], "control_vida", lote="CTLF", m14=(1, 0.5),
                      ref_m14=[1, 0.5]))
    return lst


def main(argv=None):
    global LP, E, GF
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(AQUI))
    a = ap.parse_args(argv)
    LP = cargar("leer_posicion_v375e", a.dir)
    GF = cargar("objetivos_far_v375", a.dir)
    viejo = LP.SHA_EVALUAR_LF
    LP.SHA_EVALUAR_LF = "0" * 64
    ok("C4: con otro sha256 esperado, evaluar.py no se carga", LP.cargar_evaluar()[0] is None)
    LP.SHA_EVALUAR_LF = viejo
    E, s = LP.cargar_evaluar()
    ok("C4 evaluar.py es el del pre-registro", E is not None, s[:12])
    from pipeline import mirova_v750_codigo as MV

    # ---------------- distancias (las tres reglas)
    _, _, d, _ = escena(celdas_lejana())
    ok("LEJANA: radiante far (cúmulo a ~15 km)", abs(d["radiante"] - 15.0) < 0.01 and d["radiante"] > 5, d["radiante"])
    ok("LEJANA: cercano en el cráter", d["cercano"] == 0.0, d["cercano"])
    ok("LEJANA: pico en el cúmulo lejano", abs(d["pico"] - 15.0) < 1e-9, d["pico"])
    _, _, d, _ = escena(celdas_anillo(), inner=1.0)
    ok("ANILLO: centroide en el cráter, cercano y pico a 1,5 km o más", d["radiante"] < 1e-9 and abs(d["cercano"] - 1.5)
       < 1e-9 and d["pico"] > 1.5, d)
    _, _, d, _ = escena(celdas_borde())
    ok("BORDE: centroide adentro, pico afuera", d["radiante"] <= 5.0 < d["pico"], (d["radiante"], d["pico"]))
    ok("BORDE: cercano adentro (3,75 km)", abs(d["cercano"] - 3.75) < 1e-9, d["cercano"])
    _, _, d, _ = escena(celdas_uno())
    ok("UNO: tres brazos iguales", d["radiante"] == d["cercano"] == d["pico"], d)
    _, _, d, _ = escena(celdas_picocerca())
    ok("PICOCERCA: radiante y pico en el cráter", d["radiante"] < 1 and d["pico"] == 0.0, d)
    ok("VACIA: sin distancias", escena([])[2] is None)
    _, _, d, _ = escena(celdas_lejana(), crater=CR, ref=(40.0, 33.0))
    ok("ref corrida: el mismo objeto medido desde X0, Y0", abs(d["cercano_ref"] - 7 * PASO) < 1e-9
       and abs(d["pico_ref"] - 47 * PASO) < 1e-9, (d["cercano_ref"], d["pico_ref"]))
    # cercano: desempate por (fila, columna)
    _, _, d, _ = escena([(40, 44, 1.0), (44, 40, 1.0), (50, 50, 5.0)])
    ok("cercano: a igual distancia, el mismo resultado", abs(d["cercano"] - 1.5) < 1e-9, d["cercano"])
    # distancias desde el record (sombra) contra las exactas
    for nom, cel in (("LEJANA", celdas_lejana()), ("BORDE", celdas_borde()), ("PICOCERCA", celdas_picocerca()),
                     ("ANILLO", celdas_anillo())):
        _, _, d, rec = escena(cel)
        dr = LP.distancias_desde_record(rec)
        ok(f"desde el record = exacto ({nom})", all(abs(dr[k] - d[k]) <= 0.0051 for k in LP.BRAZOS_POS), dr)
    ok("desde el record: None sin anomaly_pixels", LP.distancias_desde_record({"primary_cluster": {"centroid_dist_km": 1}}) is None)

    # ---------------- variante
    _, _, d, rec = escena(celdas_lejana())
    v = LP.variante(rec, d["cercano"], 5.0)
    ok("variante cercano: summit, centroide y final al cráter, VRP igual",
       v["distance_class"] == "summit" and v["primary_cluster"]["centroid_dist_km"] == 0.0
       and v["final_hotspot_dist_km"] == 0.0 and v["vrp_mw"] == rec["vrp_mw"] and rec["distance_class"] == "far")
    ok("variante: frontera inclusiva (5,0 es summit)", LP.variante(rec, 5.0, 5.0)["distance_class"] == "summit"
       and LP.variante(rec, 5.0001, 5.0)["distance_class"] == "far")

    # ---------------- identidad con procesar_grilla sobre grillas reales (C5 en datos reales, sin lecturas)
    esp = json.loads((RAIZ / "tests/datos_s165_v375/esperado.json").read_text(encoding="utf-8"))
    V = E.volcanes()
    n_id = n_px = 0
    for q in esp["pasadas"]:
        z = RAIZ / f"tests/datos_s165_v375/grilla_{q['id']}.npz"
        if not z.exists():
            continue
        g_ = np.load(z)
        mir, tir = g_["mir"].astype(np.float64), g_["tir"].astype(np.float64)
        v_ = V[q["volcan"]]
        g = MV.grilla_del_volcan(q["volcan"], paso_m=375.0, clave_roi="roi_v375")
        rec, mascara, pos = LP.record_de_la_via({"sensor": q["sensor"]}, g, mir, tir,
                                                {"dayflag": q["dayflag"], "sunglint": q["sunglint"]}, v_, MV)
        d = LP.distancias(mascara, mir, pos, LP.pos_ref(g), 0.375, MV._cumulo_del_mas_radiante)
        if d is None:
            continue
        n_px += 1
        pc = rec["primary_cluster"]
        if (abs(d["radiante"] - pc["centroid_dist_km"]) <= LP.TOL_DIST_KM and abs(d["pico"] - rec["hotspot_dist_km"])
                <= LP.TOL_DIST_KM and rec["distance_class"] == LP.clase_dc(d["radiante"], v_["inner_radius_km"])):
            dr = LP.distancias_desde_record(rec)
            if dr and all(abs(dr[k] - d[k]) <= 0.0051 for k in LP.BRAZOS_POS):
                n_id += 1
    ok("procesar_grilla en grillas reales: radiante, pico, clase y distancias desde el record", n_px >= 5 and n_id == n_px,
       f"{n_id} de {n_px}")
    rx, ry = LP.pos_ref({"paso": 375.0, "ul_x": 0.0, "ul_y": 750.0, "x0": 562.5, "y0": 187.5})
    ok("pos_ref: X0, Y0 en índices de celda con el origen de posicion_de", (rx, ry) == (1.0, 1.0), (rx, ry))

    # ---------------- analizar: controles
    out, f = correr(base_marco())
    ok("marco sano sin lejanas: controles en verde", not f, f)
    ok("sin far_tabla la regla no decide", out["regla_posicion"]["veredicto"].startswith("NO DECIDE"),
       out["regla_posicion"]["veredicto"])
    lst = base_marco()
    lst[0] = pasada(1, celdas_lejana(), "pos_bajo", vol="Isluga", hora="2026-07-02 05:00")
    out, f = correr(lst)
    ok("C1 sin ningún caso de un alertado cae", "C1" in f, f)
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", rec_mal=0.01)]
    out, f = correr(lst)
    ok("C5 cae si el record de la vía no es el recalculado", "C5" in f, f)
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", dc_mal=True)]
    out, f = correr(lst)
    ok("C6 cae si el almacén cambia la clase de una variante", "C6" in f, f)
    lst = base_marco()
    lst[-1] = pasada(29000, [(40, 40, 1.0), (40, 41, 1.0)], "control_vida", lote="CTLF", m14=(1, 0.6),
                     ref_m14=[1, 0.5])
    out, f = correr(lst)
    ok("C7 cae si el control de vida no reproduce S162", "C7" in f, f)
    lst = base_marco()[:-1]
    out, f = correr(lst)
    ok("C7 cae si hay run FAR y no hay control de vida", "C7" in f, f)
    out, f = correr(base_marco()[:-1], art_far=False)
    ok("sin run FAR: C7 no se exige y la regla no decide", "C7" not in f
       and out["regla_posicion"]["veredicto"].startswith("NO DECIDE"), (f, out.get("regla_posicion")))

    # ---------------- equivalencia por brazo (paso 1)
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo")]
    out, f = correr(lst)
    ok("equivalencia: mismo VRP => EQUIVALENTE", out["equivalencia"]["veredicto"] == "EQUIVALENTE", out["equivalencia"])
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", vrp_port=0.0)]
    out, f = correr(lst)
    ok("equivalencia: VRP del port en 0 cambia la publicación del brazo que publica",
       out["equivalencia"]["veredicto"] == "NO EQUIVALENTE" and out["equivalencia"]["pub_distinta"]["cercano"] == [2]
       and out["equivalencia"]["pub_distinta"]["radiante"] == [], out["equivalencia"])
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo")]
    lst[-1][1]["mascara_igual"] = False
    out, f = correr(lst)
    ok("equivalencia: máscara distinta => NO EQUIVALENTE", out["equivalencia"]["mascara_distinta"] == [2])

    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", vrp_port=1.502)]
    out, f = correr(lst)
    ok("equivalencia: VRP del port a 2e-3 MW => NO EQUIVALENTE por el VRP, publicación igual",
       out["equivalencia"]["veredicto"] == "NO EQUIVALENTE" and [i for i, _ in out["equivalencia"]["vrp_fuera"]] == [2]
       and not any(out["equivalencia"]["pub_distinta"].values()), out["equivalencia"])
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", vrp_port=1.5009)]
    out, f = correr(lst)
    ok("equivalencia: VRP a 9e-4 MW queda dentro", out["equivalencia"]["veredicto"] == "EQUIVALENTE", out["equivalencia"])
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", vrp_port_vieja=1.6)]
    out, f = correr(lst)
    ok("N-1: la vara vieja se informa (2 de 3 dentro) y no cambia el veredicto (decide la nueva)",
       out["equivalencia"]["vrp_vara_vieja"] == [2, 3] and out["equivalencia"]["vrp"] == [3, 3]
       and out["equivalencia"]["veredicto"] == "EQUIVALENTE", out["equivalencia"])

    # ---------------- decidir entre brazos (veredictos fabricados)
    def tabla(d):
        return lambda a, b: d.get((a, b), "SIN SUSTRATO")
    V3 = ["radiante", "cercano", "pico"]
    ok("decidir: cercano vence a radiante, empata con pico, radiante vence a pico => ELEGIDO CERCANO (nadie lo vence)",
       LP.decidir_brazo(V3, tabla({("cercano", "radiante"): "GANA", ("radiante", "cercano"): "PIERDE",
                                   ("radiante", "pico"): "GANA", ("pico", "radiante"): "PIERDE"}))[0]
       == "ELEGIDO CERCANO (nadie lo vence)")
    ok("decidir: cercano y pico vencen a radiante y empatan entre sí => NO RESUELTO ENTRE CERCANO Y PICO",
       LP.decidir_brazo(V3, tabla({("cercano", "radiante"): "GANA", ("pico", "radiante"): "GANA",
                                   ("radiante", "cercano"): "PIERDE", ("radiante", "pico"): "PIERDE",
                                   ("cercano", "pico"): "EMPATE", ("pico", "cercano"): "EMPATE"}))[0]
       == "NO RESUELTO ENTRE CERCANO Y PICO (decide Nicolas)")
    ok("decidir: sin sustrato en todos los pares => SE QUEDA RADIANTE",
       LP.decidir_brazo(V3, tabla({}))[0].startswith("SE QUEDA RADIANTE"))
    ok("decidir: gana a los dos => ELEGIDO", LP.decidir_brazo(V3, tabla({("pico", "radiante"): "GANA",
                                                                        ("pico", "cercano"): "GANA"}))[0]
       == "ELEGIDO PICO (gana a los demas)")
    ok("decidir: sin brazos y con uno", LP.decidir_brazo([], tabla({}))[0] == "NINGUN BRAZO PASA EL VETO"
       and LP.decidir_brazo(["pico"], tabla({}))[0] == "ELEGIDO PICO (unico que pasa el veto)")
    ok("decidir: dos vivos sin radiante, ninguno vence => NO RESUELTO", LP.decidir_brazo(
        ["cercano", "pico"], tabla({}))[0] == "NO RESUELTO ENTRE CERCANO Y PICO (decide Nicolas)")

    # ---------------- regla de posición
    def lejanas(n, publica_k=0, hora0=10):
        return [pasada(20000 + k, celdas_lejana(), "far_tabla", vol="Lastarria", hora=f"2026-08-{hora0 + k:02d} 05:00",
                       lote="FAR", pub_prod=publica_k, dist_ref=15.0) for k in range(n)]

    def lejana_vacia(i=20500):
        # una far_tabla sin alertados: da cobertura a la clase sin que ningún brazo publique
        return [pasada(i, [], "far_tabla", vol="Lastarria", hora="2026-08-31 05:00", lote="FAR", pub_prod=0,
                       dist_ref=20.0)]
    lst = base_marco() + [pasada(3, celdas_lejana(), "pos_prot", vol="Isluga", hora="2026-06-17 05:06")] + lejanas(6)
    out, f = correr(lst)
    rp = out["regla_posicion"]
    ok("veto: la protegida LEJANA que K publica veta radiante y pico", rp["detalle"]["veto"]["radiante"]
       and rp["detalle"]["veto"]["pico"] and not rp["detalle"]["veto"]["cercano"], rp["detalle"]["veto"])
    ok("veto: el único que lo pasa queda elegido", rp["veredicto"].startswith("ELEGIDO CERCANO (unico"), rp["veredicto"])
    lst = base_marco() + [pasada(3, celdas_lejana(), "pos_prot", vol="Isluga", hora="2026-06-17 05:06", pub_prod=0)] + lejanas(6)
    out, f = correr(lst)
    rp = out["regla_posicion"]
    ok("veto: una protegida que K NO publica no veta", not rp["detalle"]["veto"]["radiante"], rp["detalle"]["veto"])
    out, f = correr(base_marco() + lejanas(6))
    rp = out["regla_posicion"]
    ok("6 lejanas en que sólo cercano publica: SE QUEDA RADIANTE", rp["veredicto"].startswith("SE QUEDA RADIANTE"),
       rp["veredicto"])
    ok("radiante GANA a cercano en el error de posición", rp["detalle"]["pares"]["radiante|cercano"]["veredicto"] == "GANA")
    ok("bloques discordantes por tramo (A104)", rp["detalle"]["pares"]["radiante|cercano"]["bloques_por_tramo"] == {"O1": 6},
       rp["detalle"]["pares"]["radiante|cercano"].get("bloques_por_tramo"))
    prot_nk = [pasada(300 + k, celdas_lejana(), "pos_prot", vol="Lascar", hora=f"2026-09-{10 + k:02d} 05:00", pub_prod=0)
               for k in range(6)]
    out, f = correr(base_marco() + prot_nk + lejana_vacia())
    ok("6 protegidas LEJANA que K no publica: no vetan, pero cuentan como error => ELEGIDO CERCANO (gana a los demas)",
       out["regla_posicion"]["veredicto"].startswith("ELEGIDO CERCANO (gana"), out["regla_posicion"]["veredicto"])
    lst = base_marco() + [pasada(3, celdas_lejana(), "pos_prot", vol="Isluga", hora="2026-06-17 05:06", tabla=False)]
    out, f = correr(lst + lejana_vacia())
    ok("veto con la tabla sola (informa): la protegida sólo del OCR no veta ahí, sí en la regla que decide",
       out["regla_posicion"]["detalle"]["veto"]["radiante"] and not out["regla_posicion_tabla_sola"]["detalle"]["veto"]["radiante"],
       (out["regla_posicion"]["detalle"]["veto"], out["regla_posicion_tabla_sola"]["detalle"]["veto"]))
    bajos = [pasada(100 + k, celdas_lejana(), "pos_bajo", vol="Lascar", hora=f"2026-09-{10 + k:02d} 05:00")
             for k in range(6)]
    out, f = correr(base_marco() + bajos + lejana_vacia())
    rp = out["regla_posicion"]
    ok("6 alertas bajo 1 MW LEJANA en noches distintas: ELEGIDO CERCANO (gana a los demas)",
       rp["veredicto"].startswith("ELEGIDO CERCANO (gana"), rp["veredicto"])
    bor = [pasada(200 + k, celdas_borde(), "pos_bajo", vol="Lascar", hora=f"2026-09-{10 + k:02d} 05:00")
           for k in range(6)]
    out, f = correr(base_marco() + bor + lejana_vacia())
    rp = out["regla_posicion"]
    ok("BORDE en 6 alertas: pico calla, radiante y cercano no se separan: SE QUEDA RADIANTE",
       rp["veredicto"].startswith("SE QUEDA RADIANTE") and rp["detalle"]["pares"]["radiante|pico"]["veredicto"] == "GANA",
       rp["veredicto"])
    out, f = correr(base_marco() + lejana_vacia() + [
        pasada(4, celdas_lejana(), "pos_prot", hora="2026-06-18 05:00"),
        pasada(5, celdas_anillo(), "pos_prot", hora="2026-06-19 05:00", inner=1.0)])
    ok("ningún brazo pasa el veto", out["regla_posicion"]["veredicto"].startswith("NINGUN BRAZO PASA EL VETO"),
       out["regla_posicion"]["veredicto"])

    # ---------------- arreglos del verificador (VE2-01, VE2-04, VE2-06, VE2-09)
    out, f = correr(base_marco() + lejana_vacia() + [
        pasada(7, [], "pos_prot", vol="Tupungatito", hora="2026-08-01 05:00", tabla=False)])
    rp = out["regla_posicion"]
    ok("VE2-01: la protegida que callan los tres brazos no veta la posición; queda como pérdida común",
       not any(rp["detalle"]["veto"][a] for a in LP.BRAZOS_POS)
       and [tuple(x) for x in rp["detalle"]["perdidas_comunes"]] == [("Tupungatito", "2026-08-01 05:00")]
       and rp["veredicto"].startswith("SE QUEDA RADIANTE"), (rp["detalle"].get("perdidas_comunes"), rp["veredicto"]))
    neg5 = [pasada(10, celdas_lejana(), "neg_resto", vol="Llaima", pub_prod=0)]
    out, f = correr(base_marco(n_neg=0) + neg5 + lejana_vacia(), N={("neg_resto", "Llaima|z<=40"): 5})
    ok("VE2-04: un negativo limpio pesa N/n (5) y entra al error de la regla (cercano publica en él)",
       out["pesos"].get("neg_resto|Llaima|z<=40") == 5.0
       and out["regla_posicion"]["detalle"]["pares"]["radiante|cercano"]["neto"] == -5.0,
       (out.get("pesos"), out["regla_posicion"]["detalle"]["pares"].get("radiante|cercano")))
    falt = [pasada(20600 + k, [], "far_tabla", vol="Lastarria", hora=f"2026-09-{k + 1:02d} 05:00", lote="FAR",
                   pub_prod=0, dist_ref=20.0) for k in range(10)]
    out, f = correr(base_marco() + falt[:9], sin_dato=[falt[9][0]])
    ok("VE2-04: regla del 10 %: 9 de 10 lejanas con dato decide", not out["regla_posicion"]["veredicto"].startswith(
        "NO DECIDE"), out["regla_posicion"]["veredicto"])
    out, f = correr(base_marco() + falt[:8], sin_dato=[falt[8][0], falt[9][0]])
    ok("VE2-04: regla del 10 %: 8 de 10 no decide", out["regla_posicion"]["veredicto"].startswith("NO DECIDE"),
       out["regla_posicion"]["veredicto"])
    lst = base_marco()
    lst[-1] = pasada(29000, [(40, 40, 1.0), (40, 41, 1.0)], "control_vida", lote="CTLF", m14=(0, None),
                     ref_m14=[0, None])
    out, f = correr(lst)
    ok("VE2-04: C7 cae si ninguna re-medida tiene píxeles (port muerto que calla igual que la referencia)", "C7" in f, f)
    ok("VE2-04: C3 rango CTLF", LP.control_listas({28999: {"lote": "CTLF", "ref_M14": [1, 1]}}, None, None)
       and LP.control_listas({30000: {"lote": "CTLF", "ref_M14": [1, 1]}}, None, None))
    rx, ry = LP.pos_ref({"paso": 375.0, "ul_x": 0.0, "ul_y": 1500.0, "x0": 562.5, "y0": 375.0})
    ok("VE2-04: pos_ref en una grilla asimétrica (fila 2,5, columna 1)", (rx, ry) == (2.5, 1.0), (rx, ry))
    dm = LP.distancias_mirova({"hora_utc": "2026-06-13 05:00", "clase": "pos_bajo", "mirova": [
        {"tipo": "ALERTA_TERMICA_OCR", "source": "OCR", "dist_km": 2.0, "vrp_mw": 0.4}]})
    ok("VE2-04: el OCR del mismo 2026-06-13 entra (A119, frontera inclusiva)", dm == {"alerta_ocr": 2.0}, dm)

    class MVfalso:
        LAMBDA_I4, LAMBDA_I5 = 3.74, 11.45
        visto = []

        @classmethod
        def posicion_de(cls, g, lat, lon):
            cls.visto.append((lat, lon))
            return (0.0, 0.0)

        caja_v375 = staticmethod(lambda g, lat, lon: cls_box)
        procesar_grilla = staticmethod(lambda *a, **k: {})
        detectar_mirova = staticmethod(lambda *a, **k: np.zeros((2, 2), bool))
    cls_box = np.zeros((2, 2))
    LP.record_de_la_via({"sensor": "x"}, {}, None, None, {"dayflag": 0, "sunglint": 0.0},
                        {"vent_lat": -1.0, "vent_lon": -2.0, "lat": -3.0, "lon": -4.0, "inner_radius_km": 5}, MVfalso)
    ok("VE2-04: la vía se mide desde el cráter (vent), no desde el centro del volcán", MVfalso.visto == [(-1.0, -2.0)],
       MVfalso.visto)
    ok("VE2-09: un ciclo da NO RESUELTO entre los tres, con texto", LP.decidir_brazo(V3, tabla({
        ("radiante", "cercano"): "GANA", ("cercano", "pico"): "GANA", ("pico", "radiante"): "GANA"}))[0]
       == "NO RESUELTO ENTRE RADIANTE Y CERCANO Y PICO (ciclo; decide Nicolas)")
    # VE2-06 (A104): la unión elige cercano por las alertas de O2 y O1 por sí solo elegiría radiante
    o2 = [pasada(400 + k, celdas_lejana(), "pos_bajo", vol="Lascar", hora=f"2026-09-{10 + k:02d} 05:00")
          for k in range(6)]
    o1 = ([pasada(20700 + k, celdas_lejana(), "far_tabla", vol="Lastarria", hora=f"2026-07-{10 + k:02d} 05:00",
                  lote="FAR", pub_prod=0, dist_ref=15.0) for k in range(6)]
          + [pasada(500 + k, celdas_borde(), "pos_bajo", vol="Isluga", hora=f"2026-07-{20 + k:02d} 05:00")
             for k in range(6)])
    out, f = correr(base_marco() + o2 + o1, N={("pos_bajo", "Lascar|z<=40"): 30})
    rp = out["regla_posicion"]
    ok("VE2-06: por tramo O1 ELEGIDO RADIANTE y O2 ELEGIDO CERCANO",
       str(rp["detalle"]["por_tramo"]["O1"]).startswith("ELEGIDO RADIANTE")
       and str(rp["detalle"]["por_tramo"]["O2"]).startswith("ELEGIDO CERCANO"), rp["detalle"].get("por_tramo"))
    ok("VE2-06: la unión elige CERCANO y queda marcada por A104", rp["veredicto"].startswith("ELEGIDO CERCANO")
       and "A104: en O1 el resultado es otro" in rp["veredicto"], rp["veredicto"])
    out, f = correr(base_marco() + o2 + lejana_vacia(), N={("pos_bajo", "Lascar|z<=40"): 30})
    rp = out["regla_posicion"]
    ok("N-2: la unión elige CERCANO, O1 da SE QUEDA RADIANTE: también se marca A104",
       rp["veredicto"].startswith("ELEGIDO CERCANO") and str(rp["detalle"]["por_tramo"]["O1"]).startswith("SE QUEDA")
       and "A104: en O1 el resultado es otro" in rp["veredicto"], (rp["veredicto"], rp["detalle"].get("por_tramo")))
    out, f = correr(base_marco() + lejana_vacia())
    rp = out["regla_posicion"]
    ok("N-2: sin discordancia (O1 y O2 iguales a la unión, T sin pasadas) no hay marca",
       rp["veredicto"] == "SE QUEDA RADIANTE (nadie la vence; la del codigo)"
       and rp["detalle"]["por_tramo"]["T"] == "SIN PASADAS", (rp["veredicto"], rp["detalle"].get("por_tramo")))
    out, f = correr(base_marco() + [pasada(20501, [], "far_tabla", vol="Lastarria", hora="2026-07-31 05:00", lote="FAR",
                                          pub_prod=0, dist_ref=20.0)])
    rp = out["regla_posicion"]
    ok("N-2: un tramo sin pasadas (O2) no es discordancia", rp["detalle"]["por_tramo"]["O2"] == "SIN PASADAS"
       and "A104" not in rp["veredicto"], (rp["veredicto"], rp["detalle"].get("por_tramo")))
    ok("N-2: resultado_rp", [LP.resultado_rp(x) for x in (
        "ELEGIDO PICO (gana a los demas)", "SE QUEDA RADIANTE (nadie la vence; la del codigo)",
        "NO RESUELTO ENTRE CERCANO Y PICO (decide Nicolas)", "NINGUN BRAZO PASA EL VETO",
        "NO DECIDE: LAS LEJANAS SIN COBERTURA")] == ["PICO", "RADIANTE", "NO RESUELTO", "NINGUN", "NO DECIDE"])
    lst = base_marco() + bajos + lejana_vacia() + [pasada(20900 + k, celdas_lejana(), "far_ocr", vol="Lastarria",
                                                       hora=f"2026-08-{20 + k:02d} 05:00", lote="FAR")
                                               for k in range(8)]
    out, f = correr(lst)
    ok("8 far_ocr donde cercano publica no cambian la elección", out["regla_posicion"]["veredicto"].startswith(
        "ELEGIDO CERCANO (gana"), out["regla_posicion"]["veredicto"])
    ok("far_ocr se informa aparte", out["vara2"]["cercano"]["far_ocr"]["publica"] == 8
       and out["vara2"]["radiante"]["far_ocr"]["publica"] == 0, out["vara2"]["cercano"]["far_ocr"])

    # ---------------- vara 2 y P2-L
    lst = base_marco() + lejanas(6) + [pasada(20100, [], "far_tabla", vol="Lastarria", hora="2026-08-30 05:00",
                                              lote="FAR", pub_prod=0, dist_ref=20.0)]
    out, f = correr(lst)
    v2 = out["vara2"]
    ok("vara 2: cercano publica las 6 lejanas con alertado, radiante y pico 0",
       v2["cercano"]["far_tabla"]["publica"] == 6 and v2["radiante"]["far_tabla"]["publica"] == 0
       and v2["pico"]["far_tabla"]["publica"] == 0, {a: v2[a]["far_tabla"]["publica"] for a in v2})
    ok("vara 2: con alertado 6 de 7 (la vacía no cuenta)", v2["radiante"]["far_tabla"]["con_alertado"] == 6
       and v2["radiante"]["far_tabla"]["n"] == 7, v2["radiante"]["far_tabla"])
    ok("vara 2: K por lo publicado", v2["K"]["far_tabla"]["publica"] == 0)
    ok("las lejanas pesan 1 (censo)", out["pesos_far"] == [1.0], out.get("pesos_far"))
    ok("P2-L: cercano contra K PIERDE en 6 lejanas", v2["cercano"]["P2L_K"]["veredicto"] == "PIERDE",
       v2["cercano"]["P2L_K"])
    lk = lejanas(6, publica_k=0)
    for o, p in lk:
        p["k_rec"] = LP.variante(p["rec"], 0.0, 5.0)        # K re-corrido publica en el cráter; lo publicado no
    out, f = correr(base_marco() + lk)
    ok("K re-corrido distinto de lo publicado en más del 5 %: la lectura de K usa lo re-corrido",
       out["vara2"]["K"]["far_tabla"]["publica"] == 6, out["vara2"]["K"]["far_tabla"])
    out, f = correr(base_marco() + lejanas(6, publica_k=1))
    ok("P2-L: radiante contra K GANA cuando K publica las 6", out["vara2"]["radiante"]["P2L_K"]["veredicto"] == "GANA",
       out["vara2"]["radiante"]["P2L_K"])

    # ---------------- vara 1 (lecturas de evaluar.py por brazo)
    lst = base_marco() + [pasada(3, celdas_lejana(), "pos_prot", vol="Isluga", hora="2026-06-17 05:06")] + lejanas(1)
    out, f = correr(lst)
    v1 = out["vara1"]
    ok("vara 1: P1 de radiante pierde la protegida que K publica", v1["radiante"]["lecturas"]["P1"]["perdidas_que_K_publica"] == 1
       and v1["cercano"]["lecturas"]["P1"]["perdidas_que_K_publica"] == 0)
    ok("vara 1: cambios contra radiante por nombre", [c[0] for c in v1["cercano"]["cambios_contra_radiante"]] == ["Isluga"]
       and v1["pico"]["cambios_contra_radiante"] == [], v1["cercano"]["cambios_contra_radiante"])
    lst = base_marco(n_neg=0) + [pasada(10, celdas_lejana(), "neg_resto", vol="Llaima", pub_prod=0)] + lejanas(1)
    out, f = correr(lst)
    ok("vara 1: cercano publica en el negativo limpio con la escena LEJANA",
       out["vara1"]["cercano"]["lecturas"]["silencio"]["neg_resto"]["crudo"] == [1, 1]
       and out["vara1"]["radiante"]["lecturas"]["silencio"]["neg_resto"]["crudo"] == [0, 1])

    # ---------------- vara 3
    mir = [{"tipo": "ALERTA_TERMICA", "source": "CONS", "dist_km": 0.2, "vrp_mw": 0.3},
           {"tipo": "ALERTA_TERMICA_OCR", "source": "OCR", "dist_km": 0.2, "vrp_mw": 0.3}]
    mir07 = [dict(mir[0], dist_km=0.7), mir[1]]
    lst = base_marco() + [pasada(2, celdas_lejana(), "pos_bajo", hora="2026-07-05 05:00", mirova=mir),
                          pasada(6, celdas_lejana(), "pos_bajo", hora="2026-05-05 05:00", mirova=mir07)] + lejanas(1)
    out, f = correr(lst)
    v3 = out["vara3"]
    ok("vara 3: tabla, cercano a una celda en una, a 1 km en las dos, y radiante lejos",
       v3["cercano"]["alerta_tabla"]["a_una_celda"] == 1 and v3["cercano"]["alerta_tabla"]["a_1km"] == 2
       and v3["radiante"]["alerta_tabla"]["a_1km"] == 0, v3["cercano"]["alerta_tabla"])
    ok("vara 3: OCR antes del 2026-06-13 no entra (A119)", v3["cercano"]["alerta_ocr"]["n"] == 1, v3["cercano"]["alerta_ocr"])
    ok("vara 3: far_tabla contra dist_ref", v3["radiante"]["far_tabla"]["n"] == 1
       and v3["radiante"]["far_tabla"]["mediana"] == 0.0, v3["radiante"]["far_tabla"])
    dm = LP.distancias_mirova({"hora_utc": "2026-07-01 05:00", "clase": "pos_bajo", "mirova": [
        {"tipo": "ALERTA_TERMICA", "source": "CONS", "dist_km": 1.0, "vrp_mw": 0.2},
        {"tipo": "ALERTA_TERMICA", "source": "CONS", "dist_km": 3.0, "vrp_mw": 0.9},
        {"tipo": "FALSO_POSITIVO", "source": "CONS", "dist_km": 20.0, "vrp_mw": 4.0},
        {"tipo": "RUTINA", "source": "CONS", "dist_km": 0.0, "vrp_mw": 0.0},
        {"tipo": "ALERTA_TERMICA_OCR", "source": "OCR", "dist_km": 5.0, "vrp_mw": 1.2}]})
    ok("distancias_mirova: la mayor alerta de la tabla (sin OCR, FALSO_POSITIVO ni RUTINA) y aparte la del OCR",
       dm == {"alerta_tabla": 3.0, "alerta_ocr": 5.0}, dm)
    llamada = []
    ok("vara: de 1 a 4 px con la escena de MATLAB de esa máscara, la de MATLAB", LP.elegir_vara(
        3, 0.5, {"npix": 3, "vrp_port_mw": 0.5, "vrp_vara_mw": 0.48}, lambda: llamada.append(1) or 9.0) == 0.48
       and not llamada)
    ok("vara: más de 4 px, la regla de MATLAB", LP.elegir_vara(6, 0.5, None, lambda: 0.7) == 0.7)
    ok("vara: de 1 a 4 px sin escena de MATLAB (pasada FAR), la regla", LP.elegir_vara(2, 0.5, None, lambda: 0.6) == 0.6)
    ok("vara: escena de MATLAB de otra máscara, la regla", LP.elegir_vara(
        3, 0.5, {"npix": 2, "vrp_port_mw": 0.5, "vrp_vara_mw": 0.48}, lambda: 0.6) == 0.6
       and LP.elegir_vara(3, 0.5, {"npix": 3, "vrp_port_mw": 0.51, "vrp_vara_mw": 0.48}, lambda: 0.6) == 0.6)
    ok("vara: sin píxeles, None", LP.elegir_vara(0, None, None, lambda: 1.0) is None)

    # ---------------- listas (C3)
    obj = {1: {"lote": "S162"}, 20000: {"lote": "FAR", "clase": "far_tabla"}, 29000: {"lote": "CTLF", "ref_M14": [1, 1]}}
    ok("C3 sin fallas en listas sanas", LP.control_listas(obj, None, None) == [])
    ok("C3: id FAR fuera de rango", LP.control_listas({**obj, 19999: {"lote": "FAR", "clase": "far_tabla"}}, None, None))
    ok("C3: clase FAR equivocada", LP.control_listas({**obj, 20001: {"lote": "FAR", "clase": "neg_resto"}}, None, None))
    ok("C3: id del marco en el rango FAR", LP.control_listas({**obj, 20002: {"lote": "S162"}}, None, None))
    ok("C3: CTLF sin ref_M14", LP.control_listas({**obj, 29001: {"lote": "CTLF"}}, None, None))
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "objetivos_far_v375.json").write_bytes(b'{"pasadas": []}\n')
        (t / "objetivos_run_far_v375.json").write_bytes(b'{"pasadas": []}\n')
        (t / "sg.json").write_text(json.dumps({"objetivos_far_sha256": LP.sha256_lf(t / "objetivos_far_v375.json")}))
        ok("C3: sin gránulo atado por sha256", LP.control_listas(obj, t / "objetivos_run_far_v375.json", t / "sg.json") == [])
        (t / "objetivos_far_v375.json").write_bytes(b'{"pasadas": [1]}\n')
        ok("C3: sin gránulo desatado", LP.control_listas(obj, t / "objetivos_run_far_v375.json", t / "sg.json"))
        (t / "objetivos_far_v375.json").write_bytes(b'{"pasadas": []}\r\n')
        ok("C3: el sha256 no depende de CRLF", LP.control_listas(obj, t / "objetivos_run_far_v375.json", t / "sg.json") == [])
        ok("C3: run FAR sin --sin-granulo-far", LP.control_listas(obj, t / "objetivos_run_far_v375.json", None))

    # ---------------- generador
    ok("generador: subclase tabla", GF.subclase({"mirova": [{"tipo": "FALSO_POSITIVO", "source": "CONS"}]}) == "far_tabla")
    ok("generador: subclase ocr", GF.subclase({"mirova": [{"tipo": "FALSO_POSITIVO_OCR", "source": "OCR"}]}) == "far_ocr")
    ok("generador: dist_ref prefiere la tabla", GF.dist_ref({"mirova": [
        {"tipo": "FALSO_POSITIVO_OCR", "source": "OCR", "dist_km": 5.0},
        {"tipo": "FALSO_POSITIVO", "source": "CONS", "dist_km": 9.0}]}) == 9.0)
    ok("generador: dist_ref ignora RUTINA y ALERTA", GF.dist_ref({"mirova": [
        {"tipo": "RUTINA", "source": "CONS", "dist_km": 0.0}, {"tipo": "FALSO_POSITIVO_OCR", "source": "OCR",
                                                              "dist_km": 7.0}]}) == 7.0)
    pob = [{"lab": "far_ref", "b": "VIIRS375", "hora_utc": "2026-07-01 05:00", "granule": "g1", "volcan": "Lascar",
            "estrato_z": "z<=40", "mirova": [{"tipo": "FALSO_POSITIVO", "source": "CONS", "dist_km": 9.0}]},
           {"lab": "far_ref", "b": "VIIRS375", "hora_utc": "2026-10-12 05:00", "granule": "g2", "volcan": "Lascar",
            "estrato_z": "z<=40", "mirova": []},
           {"lab": "far_ref", "b": "VIIRS375", "hora_utc": "2026-07-02 05:00", "granule": None, "volcan": "Isluga",
            "estrato_z": "z>40", "mirova": []},
           {"lab": "far_ref", "b": "MODIS", "hora_utc": "2026-07-02 05:00", "granule": "g3", "volcan": "Isluga",
            "estrato_z": "z>40", "mirova": []},
           {"lab": "pos", "b": "VIIRS375", "hora_utc": "2026-07-02 05:00", "granule": "g4", "volcan": "Isluga",
            "estrato_z": "z>40", "mirova": []}]
    far, sg = GF.seleccionar_far(pob)
    ok("generador: selecciona far_ref de 375, sin días excluidos, aparte las sin gránulo",
       [p["granule"] for p in far] == ["g1"] and len(sg) == 1 and sg[0]["volcan"] == "Isluga", (far, sg))
    far = GF.completar(far, {"Lascar": {"n": 134}, "Isluga": {"n": 134}})
    ok("generador: id desde 20000, lote, tramo, estrato y grilla", far[0]["id"] == 20000 and far[0]["lote"] == "FAR"
       and far[0]["tramo"] == "O1" and far[0]["estrato"] == "Lascar|z<=40" and far[0]["grilla"] == {"n": 134})
    try:
        GF.completar([{"granule": "g", "volcan": "Nada", "hora_utc": "2026-07-01", "estrato_z": "z"}], {})
        ok("generador: volcán sin grilla corta", False)
    except SystemExit:
        ok("generador: volcán sin grilla corta", True)
    m1 = [{"a": 1, "lab": "pos"}, {"a": 2, "lab": "neg_limpio"}]
    ok("generador: control C-G3 iguales", GF.comparar(m1 + [{"lab": "far_ref"}], m1)[0])
    ok("generador: control C-G3 distinto si cambia un campo", not GF.comparar([{"a": 1, "lab": "pos"},
                                                                             {"a": 3, "lab": "neg_limpio"}], m1)[0])
    ok("generador: control C-G3 distinto si falta una", not GF.comparar(m1[:1], m1)[0])
    ok("generador: tramos", (GF.tramo("2026-06-12 05:00"), GF.tramo("2026-06-13 05:00"), GF.tramo("2026-08-29 05:00"))
       == ("T", "O1", "O2"))
    ctl = GF.control_vida()
    ok("generador: 20 de control de vida desde 29000 con ref_M14", len(ctl) == 20 and ctl[0]["id"] == 29000
       and ctl[-1]["id"] == 29019 and all(o["lote"] == "CTLF" and o.get("ref_M14") for o in ctl))
    src = (RAIZ / "experiments/_s159/portes/01_poblacion.py").read_text(encoding="utf-8")
    m = GF.poblacion_con_far_ref(RAIZ / "experiments/_s159/portes/01_poblacion.py")
    ok("generador: el filtro de la población cambia exactamente en far_ref", GF.FILTRO_MARCO in src
       and hasattr(m, "main"))
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "x.py"
        p.write_text(src.replace(GF.FILTRO_MARCO, "True"), encoding="utf-8")
        try:
            GF.poblacion_con_far_ref(p)
            ok("generador: sin el filtro no se genera", False)
        except SystemExit:
            ok("generador: sin el filtro no se genera", True)
    ok("generador: blob de git", GF.blob_git(b"hola\n") == "5c1b14949828006ed75a3e8858957f86a2f7e2eb")
    ok("generador: sha256 sin CRLF", GF.sha256_bytes(b"a\r\nb") == GF.sha256_bytes(b"a\nb"))

    # generar() entero con dependencias sintéticas
    marco = {"meta": {"referencia": {"c": "1", "o": "2"}}, "pasadas": [{"lab": "pos", "x": 1}]}

    def dep(ref=None, extra_pos=False, malos=()):
        def poblar(dest, data, ref_dest, shas):
            pas = [{"lab": "pos", "x": 1}] + ([{"lab": "pos", "x": 2}] if extra_pos else []) + pob[:3]
            (Path(dest) / "poblacion_completa.json").write_text(json.dumps(
                {"meta": {"referencia": ref or shas}, "pasadas": pas}), encoding="utf-8")
        return {"poblar": poblar, "vols": ["Lascar"], "control_records": lambda d, v: list(malos),
                "grillas": lambda: {"Lascar": {"n": 134}, "Isluga": {"n": 134}}, "control_vida": GF.control_vida,
                "capas": lambda: {"data/x.csv": "1"}}
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        mr = t / "marco.json"
        mr.write_text(json.dumps(marco), encoding="utf-8")
        r = GF.generar(t / "a", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep())
        run = json.loads((t / "a/objetivos_run_far_v375.json").read_text(encoding="utf-8"))
        sgj = json.loads((t / "a/sin_granulo_far_v375.json").read_text(encoding="utf-8"))
        ok("generar: OK escribe las listas, atadas por sha256", r == 0 and (t / "a/poblacion_far.json").exists()
           and len(run["pasadas"]) == 21 and sgj["objetivos_far_sha256"] == GF.sha256_bytes(
               (t / "a/objetivos_far_v375.json").read_bytes()) and len(sgj["pasadas"]) == 1, (r, len(run["pasadas"])))
        ok("generar: el meta fija las capas locales de la referencia (VE2-02)",
           json.loads((t / "a/objetivos_far_v375.json").read_text(encoding="utf-8"))["meta"]["capas_locales"]
           == {"data/x.csv": "1"})
        ok("generar: segundo intento en la misma carpeta se niega", intento(lambda: GF.generar(
            t / "a", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep())) == 2)
        r = GF.generar(t / "b", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep(extra_pos=True))
        ok("generar: C-G3 caído sale 1 sin listas", r == 1 and not (t / "b/objetivos_far_v375.json").exists()
           and (t / "b/poblacion_far_CONTROL_FALLIDO.json").exists())
        ok("generar: tras un C-G3 caído, la carpeta no se reusa", intento(lambda: GF.generar(
            t / "b", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep())) == 2)
        r = GF.generar(t / "c", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep(ref={"c": "9", "o": "2"}))
        ok("generar: C-G2 caído (otra referencia) sale 1", r == 1 and not (t / "c/objetivos_far_v375.json").exists())
        r = GF.generar(t / "e", "d", "r", marco_ruta=mr, portes=t / "portes", dep=dep(malos=[("Lascar", "x", "y")]))
        ok("generar: C-G1 caído (records de otro commit) sale 1 sin escribir", r == 1 and not (t / "e").exists())
        (t / "portes").mkdir()
        ok("generar: no escribe en la carpeta del marco", GF.generar(t / "portes", "d", "r", marco_ruta=mr,
                                                                    portes=t / "portes", dep=dep()) == 2
           and not (t / "portes/poblacion_completa.json").exists())
    cap = GF.capas_locales()
    ok("generador: capas locales reales con sus sha256 LF (filas perdidas y respaldo del 2026-04-08)", cap == {
        "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv":
            "2613e7cc03e75c2f6b0be41d11051ae847dece00be817d305b7e77d95bbf59e7",
        "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv":
            "183aff7f38c6ca9ef93c8e0951f8190dd12be2690d54dbacb7d7acabaaa93568"}, cap)
    ok("lista del run: el meta trae esas mismas capas", json.loads((AQUI / "objetivos_far_v375.json").read_text(
        encoding="utf-8"))["meta"]["capas_locales"] == cap)

    # ---------------- main() de punta a punta, sin tocar el marco: un artefacto FAR falso cuyo único contenido son 5 de
    # las grillas reales de tests/datos_s165_v375 rotuladas como control de vida (CTLF no entra a ninguna lectura).
    # Corre la vía, el port C13, la vara del VRP, el almacén y node sobre grillas reales; C7 tiene que caer (5 de 20).
    run = json.loads((AQUI / "objetivos_run_far_v375.json").read_text(encoding="utf-8"))
    ctlf = {}
    for o in sorted((o for o in run["pasadas"] if o["lote"] == "CTLF"), key=lambda o: o["id"]):
        ctlf.setdefault(o["volcan"], []).append(o)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "vacio").mkdir()
        (t / "far").mkdir()
        res = []
        for q in esp["pasadas"]:
            if not ctlf.get(q["volcan"]):
                continue
            o = ctlf[q["volcan"]].pop(0)
            shutil.copy2(RAIZ / f"tests/datos_s165_v375/grilla_{q['id']}.npz", t / "far" / f"grilla_{o['id']}.npz")
            res.append({"id": o["id"], "estado": "ok", "dayflag": q["dayflag"], "sunglint": q["sunglint"],
                        "port": {"M14": {"npix": o["ref_M14"][0], "vrp_mw": o["ref_M14"][1]}}})
        (t / "far" / "resultados_VIIRS375_00.json").write_text(json.dumps(res), encoding="utf-8")
        LP.L.clear()
        rc = LP.main(["--art-far", str(t / "far"), "--art-s159", str(t / "vacio"), "--art-s162", str(t / "vacio"),
                      "--art-s162b", str(t / "vacio"), "--json", str(t / "o.json"), "--salida", str(t / "s.txt")])
        oj = json.loads((t / "o.json").read_text(encoding="utf-8")) if (t / "o.json").exists() else {}
        eqv = oj.get("equivalencia", {})
        ok("main() de punta a punta: sale 3 por C7 (5 de 20 re-medidas), con C3 en verde",
           rc == 3 and "C7" in (t / "s.txt").read_text(encoding="utf-8") and "C3 listas: OK" in "\n".join(LP.L), rc)
        ok("main(): el blob de pipeline/mirova_v750_codigo.py se reconoce como el de #921 aunque el checkout tenga CRLF",
           "blob a9c00eaf137896231c5cb43759b1110b1e0d539c: el de #921" in "\n".join(LP.L))
        ok("main() sobre 5 grillas reales: máscara vía = port C13 en todas, VRP contra la vara en todas, publicación por "
           "brazo igual", len(res) == 5 and eqv.get("mascara_distinta") == [] and eqv.get("vrp") == [5, 5]
           and not any((eqv.get("pub_distinta") or {"x": [1]}).values()), eqv)
        log = "\n".join(LP.L)
        ok("main() cableado: C5 en 5 de 5 (posición y referencia de la vía) y C6 sin cambios del almacén",
           "record de la vía: 5 de 5" in log and "distintas 0" in log and "C1 una sola alertada => tres brazos iguales: 1 de 1"
           in log, [x for x in LP.L if x.strip().startswith(("C1", "C5", "C6"))])
        real = LP.por_el_almacen

        def almacen_que_voltea(rec, *a, **k):          # un almacén que cambia la clase de todo lo que escribe
            r = real(rec, *a, **k)
            if r and r.get("distance_class"):
                r["distance_class"] = "far" if r["distance_class"] == "summit" else "summit"
            return r
        LP.por_el_almacen = almacen_que_voltea
        try:
            LP.L.clear()
            LP.main(["--art-far", str(t / "far"), "--art-s159", str(t / "vacio"), "--art-s162", str(t / "vacio"),
                     "--art-s162b", str(t / "vacio")])
        finally:
            LP.por_el_almacen = real
        ok("VE2-05: main() con un almacén que cambia la clase: C6 cae",
           any(x.startswith("LECTURA NO LEGIBLE") and "C6" in x for x in LP.L), [x for x in LP.L if "LEGIBLE" in x])
    # C-G1 con un checkout CRLF: el mismo archivo de records tiene que reconocerse
    lascar = Path(r"D:\vrp-trabajo\temporales\s159_n\data_main\Lascar.json")
    if lascar.exists():
        with tempfile.TemporaryDirectory() as t:
            b = lascar.read_bytes()
            (Path(t) / "Lascar.json").write_bytes(b.replace(GF.LF, GF.CRLF))
            ok("generador C-G1: records con CRLF se reconocen como el blob de 533398f8f",
               GF.control_records(t, ["Lascar"]) == [] and GF.CRLF in (Path(t) / "Lascar.json").read_bytes())
            (Path(t) / "Lascar.json").write_bytes(b[:-2] + b"  ")
            ok("generador C-G1: un byte distinto no pasa", GF.control_records(t, ["Lascar"]) != [])
    else:
        ok("generador C-G1 con CRLF: falta la copia de 533398f8f en D: (SIN DATO)", False)

    # ---------------- la lista real del run (forma, no contenido)
    run = json.loads((AQUI / "objetivos_run_far_v375.json").read_text(encoding="utf-8"))
    claves = ("id", "volcan", "hora_utc", "clase", "granule", "grilla", "lote", "estrato", "sensor", "pub_prod")
    ok("lista del run: lo que leen el probe y el lector", all(all(k in o for k in claves) for o in run["pasadas"])
       and all(k in run["pasadas"][0]["grilla"] for k in ("centro_lat", "centro_lon", "epsg", "X0", "Y0", "n")),
       len(run["pasadas"]))
    ids = [o["id"] for o in run["pasadas"]]
    ok("lista del run: ids únicos, FAR y CTLF en sus rangos", len(set(ids)) == len(ids)
       and all((20000 <= o["id"] < 29000) == (o["lote"] == "FAR") for o in run["pasadas"]))
    ok("lista del run: sha256 de la suplementaria en el meta", run["meta"]["objetivos_far_sha256"] == LP.sha256_lf(
        AQUI / "objetivos_far_v375.json"))

    n_ok = sum(1 for _, c in RES if c)
    print(f"\nRESULTADO: {n_ok} de {len(RES)}")
    return 0 if n_ok == len(RES) else 1


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
