# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): análisis puro del vecindario del foco y criterio pre-registrado.

POR QUÉ. Un foco chico reparte su calor entre el píxel donde cae y sus vecinos. MIROVA suma esos
vecinos tibios y calcula el fondo de cada píxel alertado como la media de sus vecinos no alertados
(Campus et al. 2024, Bull. Volcanol. 86:25, p. 3, ec. 1 y 2; verificado S141 en
docs/audit_s141/lectura/VERIFICADOR_LECTORES.md V-07). Nosotros publicamos uno. Este módulo dice,
para los vecinos del NUESTRO píxel pico, qué les pasó dentro de la ruta que publicó el cúmulo, si
son más tibios que los vecinos de un píxel cualquiera lejos del foco, y cuánto de la brecha
cerrarían con fondo local. Las ocho correcciones del verificador del v1 están mapeadas en el plan.

Sin red y sin pipeline (salvo la distancia de f5_core). Plan y criterio:
docs/superpowers/plans/2026-09-15-fase1-probe-vecinos-v2.md
"""
import collections
import math
import statistics
import sys
from pathlib import Path

import numpy as np

_R = Path(__file__).resolve().parents[2]
if str(_R) not in sys.path:
    sys.path.insert(0, str(_R))

from pipeline.f5_core import F5_BT_EXT_K, F5_R_CORE_KM, _hav_km  # noqa: E402

# ---------------------------------------------------------------- pre-registro (no cambiar tras ver datos)
RADIO_FOCO_KM = 0.75            # §6.1 del verificador
N_MIN_VOLCAN = 3                # pasadas válidas para que un volcán sea evaluable
MIN_VOLCANES = 3                # volcanes evaluables para juzgar un estrato
FRAC_DOMINANTE = 0.6            # fracción para nombrar un destino
FRAC_VOLCANES = 2 / 3           # fracción de volcanes que deben compartir destino, contraste o fondo
CONTRASTE_MIN_K = 1.0           # elección redonda, no un valor instrumental medido
CIERRA, NO_CIERRA = 0.5, 0.2
C1_MIN, C2_MIN = 0.9, 0.95      # control del instrumento; C3 exige 1,0
ANILLO_CONTROL_KM = (3.0, 6.0)
TOL_F5_MW = 1e-3

LAMBDA_I04_UM = 3.74
C1_PLANCK, C2_PLANCK = 1.191042e8, 14388.0
KA_375 = 18.0 * 140625          # coeficiente de Wooster por área nadir, igual que el pipeline


def planck_i04(t_k):
    return C1_PLANCK / (LAMBDA_I04_UM ** 5 * (math.exp(C2_PLANCK / (LAMBDA_I04_UM * t_k)) - 1))


def bt_de_radiancia(l):
    return C2_PLANCK / (LAMBDA_I04_UM * math.log(1 + C1_PLANCK / (LAMBDA_I04_UM ** 5 * l)))


def _fin(x):
    return x is not None and math.isfinite(float(x))


def aporte_mw(bt_k, fondo_k):
    """VRP de un píxel con ese fondo, en MW; nunca negativo (así lo publica el pipeline)."""
    if not (_fin(bt_k) and _fin(fondo_k)):
        return 0.0
    return max(planck_i04(bt_k) - planck_i04(fondo_k), 0.0) * KA_375 / 1e6


# ---------------------------------------------------------------- publicado y núcleo F5

def identificar_publicado(eventos_cluster, pc):
    """§6.3: el cúmulo publicado es la llamada cuyo cúmulo 0 coincide con el `primary_cluster` del record
    (n_pixels y centroide a 5 decimales, que single_pixel_mode no toca). No es "la última llamada": una
    llamada del Test 1 que vuelve vacía no publica (V8)."""
    if not pc:
        return {"identificado": False, "ambiguo": False, "motivo": "sin_primary_cluster"}
    coinc = []
    for e in sorted(eventos_cluster, key=lambda e: e["seq"]):
        if not e.get("clusters"):
            continue
        c = e["clusters"][0]
        if (c.get("n_pixels") == pc.get("n_pixels") and c.get("centroid_lat") is not None
                and round(c["centroid_lat"], 5) == pc.get("centroid_lat")
                and round(c["centroid_lon"], 5) == pc.get("centroid_lon")):
            coinc.append(e)
    if not coinc:
        return {"identificado": False, "ambiguo": False, "motivo": "sin_coincidencia"}
    e = coinc[-1]
    conjuntos = {tuple(sorted(x["clusters"][0]["pixel_indices"])) for x in coinc}
    return {"identificado": True, "ambiguo": len(conjuntos) > 1, "n_coincidencias": len(coinc),
            "ruta": e["ruta"], "seq": e["seq"], "indices": [tuple(ij) for ij in e["clusters"][0]["pixel_indices"]],
            "entrada": e["entrada"], "vrp_per_pixel": e.get("vrp_per_pixel"), "lat": e.get("lat"), "lon": e.get("lon")}


def nucleo_f5(record, inner_km):
    """Réplica de pipeline.f5_core.f5_core_vrp_mw que además devuelve los píxeles y su conteo (§6.5).
    El control C2 exige que el total coincida con la función del pipeline en la misma corrida."""
    vacio = {"total": None, "n": None, "pixeles": []}
    pixels = (record or {}).get("anomaly_pixels")
    if not pixels:
        return vacio
    pc = record.get("primary_cluster")
    if not pc or pc.get("centroid_lat") is None or pc.get("centroid_lon") is None:
        return vacio
    cand = [p for p in pixels if p.get("lat") is not None and p.get("lon") is not None
            and _hav_km(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= inner_km]
    if not cand:
        return vacio
    pk = 0
    for i in range(1, len(cand)):
        if (cand[i].get("vrp_mw") or 0) > (cand[pk].get("vrp_mw") or 0):
            pk = i
    kept = [p for i, p in enumerate(cand)
            if i == pk or _hav_km(p["lat"], p["lon"], cand[pk]["lat"], cand[pk]["lon"]) <= F5_R_CORE_KM
            or (p.get("bt_k") or 0) >= F5_BT_EXT_K]
    return {"total": float(sum((p.get("vrp_mw") or 0) for p in kept)), "n": len(kept), "pixeles": kept}


def n_publicado_hoy(record, nucleo):
    """Píxeles que hoy suman la magnitud publicada: núcleo F5 si existe; si no, 1 con single_pixel_mode
    (publica el máximo, single_pixel_mode.py:181-183); si no, el cúmulo entero."""
    if nucleo.get("total") is not None:
        return nucleo["n"]
    pc = (record or {}).get("primary_cluster") or {}
    if pc.get("single_pixel_mode"):
        return 1
    return pc.get("n_pixels")


# ---------------------------------------------------------------- rótulos dentro de la ruta

def rotular(en_cumulo, en_entrada, marcado):
    if en_cumulo:
        return "incluido"
    if en_entrada:
        return "alertado_fuera_del_cumulo"
    if marcado:
        return "marcado_y_quitado"
    return "nunca_marcado"


def marcado_por_pixel(ruta, eventos, forma):
    """§6.2: un test por píxel de la ruta publicada. Contextual: primer pase ∪ segundo pase por nombre.
    Test 1: la máscara dNTI contextual que entra al filtro (process_viirs.py:1798). `mask_contributing`
    del Test 1 nunca cuenta: es todo exceso sobre el anillo dentro del disco (V3)."""
    m = np.zeros(forma, bool)

    def unir(x):
        if x is not None and np.shape(x) == tuple(forma):
            m[:] |= np.asarray(x, bool)
    for e in eventos:
        if ruta == "contextual" and e["tipo"] == "first_pass":
            unir(e.get("hot"))
        elif ruta == "contextual" and e["tipo"] == "second_pass" and e.get("via_kw"):
            unir(e.get("salida"))
        elif ruta == "test1" and e["tipo"] == "ctx_filter":
            unir(e.get("dnti_ctx"))
    return m


def vecinos8(forma, i, j):
    return [(i + a, j + b) for a in (-1, 0, 1) for b in (-1, 0, 1)
            if (a or b) and 0 <= i + a < forma[0] and 0 <= j + b < forma[1]]


def fondo_local_k(bt, alerta, i, j):
    """BT equivalente a la radiancia media de los vecinos no alertados y con BT finita de (i, j)."""
    ls = [planck_i04(bt[a, b]) for a, b in vecinos8(bt.shape, i, j) if not alerta[a, b] and np.isfinite(bt[a, b])]
    if not ls:
        return None
    return bt_de_radiancia(sum(ls) / len(ls))


def _exceso(bt, alerta, ij):
    if not np.isfinite(bt[ij]):
        return None
    fl = fondo_local_k(bt, alerta, *ij)
    return None if fl is None else float(bt[ij] - fl)


def _calientes(bt, vec, k):
    fin = [v for v in vec if np.isfinite(bt[v])]
    return sorted(fin, key=lambda v: (-float(bt[v]), v))[:k]


def _mediana(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _dist_grid_km(lat, lon, lat0, lon0):
    r = math.pi / 180
    a = (np.sin((lat - lat0) * r / 2) ** 2
         + math.cos(lat0 * r) * np.cos(lat * r) * np.sin((lon - lon0) * r / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def pixel_control(bt, lat, lon, alerta, centro, anillo_km=ANILLO_CONTROL_KM):
    """§6.7: el píxel más caliente a 3 a 6 km del centro, fuera de alertas y sin vecinos alertados.
    Es el caso más exigente para el contraste: un lugar tibio común, no un foco."""
    d = _dist_grid_km(lat, lon, float(lat[centro]), float(lon[centro]))
    al = np.pad(np.asarray(alerta, bool), 1)
    dil = np.zeros(alerta.shape, bool)
    for a in (0, 1, 2):
        for b in (0, 1, 2):
            dil |= al[a:a + alerta.shape[0], b:b + alerta.shape[1]]
    cand = (d >= anillo_km[0]) & (d <= anillo_km[1]) & np.isfinite(bt) & ~dil
    if not cand.any():
        return None
    k = int(np.argmax(np.where(cand, bt, -np.inf)))
    return tuple(int(t) for t in np.unravel_index(k, bt.shape))


def consistencia_rotulos(vecinos, indices, centro):
    """C3: `incluido` ⇔ índice en el cúmulo publicado, y el centro pertenece a él."""
    idx = {tuple(ij) for ij in indices}
    if tuple(centro) not in idx:
        return False
    return all((v["rotulo"] == "incluido") == (tuple(v["ij"]) in idx) for v in vecinos)


def resumir_pasada(bt, lat, lon, publicado, marcado, npix_osf, osf_lat, osf_lon, vent_lat, vent_lon,
                   brecha_mw, t_bg_anillo_k, mask_contributing=None):
    bt = np.asarray(bt, float)
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    forma = bt.shape
    otras = {"lat": lat.shape, "lon": lon.shape, "entrada": np.shape(publicado.get("entrada")),
             "marcado": np.shape(marcado)}
    if publicado.get("vrp_per_pixel") is not None:
        otras["vrp_per_pixel"] = np.shape(publicado["vrp_per_pixel"])
    if mask_contributing is not None:
        otras["mask_contributing"] = np.shape(mask_contributing)
    if any(tuple(s) != forma for s in otras.values()):
        return {"grilla_ok": False, "forma_bt": list(forma), "formas": {k: list(s) for k, s in otras.items()}}

    indices = [tuple(ij) for ij in publicado["indices"]]
    en_cumulo = np.zeros(forma, bool)
    for ij in indices:
        en_cumulo[ij] = True
    alerta = np.asarray(publicado["entrada"], bool) | en_cumulo           # §6.6: alertas de la ruta publicada
    marcado = np.asarray(marcado, bool)
    vrp = (np.asarray(publicado["vrp_per_pixel"], float) if publicado.get("vrp_per_pixel") is not None
           else np.zeros(forma))
    centro = max(indices, key=lambda ij: (float(vrp[ij]), float(bt[ij]) if np.isfinite(bt[ij]) else -math.inf,
                                          -ij[0], -ij[1]))                  # §6.4
    clat, clon = float(lat[centro]), float(lon[centro])
    d_osf = _hav_km(clat, clon, osf_lat, osf_lon)
    d_crater = _hav_km(osf_lat, osf_lon, vent_lat, vent_lon)

    k = max(0, min(int(npix_osf) - 1, 8))
    vec = vecinos8(forma, *centro)
    cal = set(_calientes(bt, vec, k))
    mc = None if mask_contributing is None else np.asarray(mask_contributing, bool)
    filas = []
    for v in vec:
        fl = fondo_local_k(bt, alerta, *v)
        b = float(bt[v]) if np.isfinite(bt[v]) else None
        filas.append({"ij": [int(v[0]), int(v[1])], "bt_k": None if b is None else round(b, 3),
                      "rotulo": rotular(bool(en_cumulo[v]), bool(alerta[v]), bool(marcado[v])),
                      "caliente": v in cal, "en_mask_contributing": None if mc is None else bool(mc[v]),
                      "fondo_local_k": None if fl is None else round(fl, 4),
                      "exceso_local_k": None if (fl is None or b is None) else round(b - fl, 4),
                      "aporte_local_mw": aporte_mw(b, fl), "aporte_anillo_mw": aporte_mw(b, t_bg_anillo_k)})

    control = None
    pc_ij = pixel_control(bt, lat, lon, alerta, centro)
    if pc_ij is not None:
        alerta_ctl = alerta.copy()
        alerta_ctl[pc_ij] = True                                            # fondo simétrico con el centro
        cal_ctl = _calientes(bt, vecinos8(forma, *pc_ij), k)
        control = {"ij": [pc_ij[0], pc_ij[1]], "bt_k": round(float(bt[pc_ij]), 3),
                   "dist_km": round(_hav_km(clat, clon, float(lat[pc_ij]), float(lon[pc_ij])), 3),
                   "exceso_mediano_calientes_k": _mediana([_exceso(bt, alerta_ctl, v) for v in cal_ctl])}

    perdido = sum(f["aporte_local_mw"] for f in filas if f["caliente"] and f["rotulo"] != "incluido")
    return {
        "grilla_ok": True, "centro": [int(centro[0]), int(centro[1])], "bt_centro_k": round(float(bt[centro]), 3),
        "dist_centro_osf_km": round(d_osf, 4), "dist_osf_crater_km": round(d_crater, 4),
        "foco_ok": min(d_osf, d_crater) <= RADIO_FOCO_KM, "k_calientes": k, "vecinos": filas,
        "exceso_mediano_calientes_k": _mediana([f["exceso_local_k"] for f in filas if f["caliente"]]),
        "exceso_mediano_restantes_k": _mediana([f["exceso_local_k"] for f in filas if not f["caliente"]]),
        "control": control, "aporte_perdido_local_mw": perdido,
        "fraccion_brecha": (perdido / brecha_mw) if (brecha_mw is not None and brecha_mw > 0) else None,
        "consistencia_rotulos": consistencia_rotulos(filas, indices, centro),
    }


# ---------------------------------------------------------------- criterio

def fila_valida(f):
    if not f.get("ok"):
        return False, "no_ok"
    if f.get("clase") != "candidato":
        return False, "control"
    pub = f.get("publicado") or {}
    if not pub.get("identificado"):
        return False, "publicado_no_identificado"
    if pub.get("ambiguo"):
        return False, "publicado_ambiguo"
    r = f.get("resumen") or {}
    if not r.get("grilla_ok"):
        return False, "grilla_distinta"
    if not r.get("foco_ok"):
        return False, "foco_mirova_lejos_hoy"
    n, npix = (f.get("hoy") or {}).get("n_publicado"), (f.get("osf") or {}).get("Npix")
    if n is None or npix is None or n >= npix:
        return False, "ya_no_publica_menos"
    return True, None


def _f5_coincide(f):
    h = f.get("hoy") or {}
    a, b = h.get("f5_replica_mw"), h.get("f5_pipeline_mw")
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL_F5_MW


def control_instrumento(ok):
    ident = [f for f in ok if (f.get("publicado") or {}).get("identificado")
             and not (f.get("publicado") or {}).get("ambiguo")]
    res = [f for f in ok if "consistencia_rotulos" in (f.get("resumen") or {})]
    c1 = len(ident) / len(ok) if ok else None
    c2 = sum(_f5_coincide(f) for f in ident) / len(ident) if ident else None
    c3 = sum(bool(f["resumen"]["consistencia_rotulos"]) for f in res) / len(res) if res else None
    estado = ("OK" if None not in (c1, c2, c3) and c1 >= C1_MIN and c2 >= C2_MIN and c3 == 1.0 else "FALLA")
    return {"n_ok": len(ok), "c1": c1, "c2": c2, "c3": c3, "estado": estado}


def _conteo(fs):
    c = collections.Counter()
    for f in fs:
        ruta = f["publicado"]["ruta"]
        for v in f["resumen"]["vecinos"]:
            if v.get("caliente") and v["rotulo"] != "incluido":
                c[f"{ruta}:{v['rotulo']}"] += 1
    return c


def _dominante(c):
    n = sum(c.values())
    if not n:
        return None
    k = sorted(c, key=lambda x: (-c[x], x))[0]
    return k if c[k] / n >= FRAC_DOMINANTE else None


def _clase_fondo(x):
    if x is None:
        return None
    return "CIERRA" if x >= CIERRA else "NO_CIERRA" if x < NO_CIERRA else "PARCIAL"


def _estable(por_vol, campo, clase):
    """La clase la comparten ≥ 2/3 de los volcanes, y lo sigue haciendo al sacar cada uno por turno."""
    vols = list(por_vol)
    n = len(vols)
    cuenta = sum(por_vol[v][campo] == clase for v in vols)
    loo = {v: cuenta - (por_vol[v][campo] == clase) for v in vols}
    base = n > 0 and cuenta >= FRAC_VOLCANES * n - 1e-9
    return base and all(loo[v] >= FRAC_VOLCANES * (n - 1) - 1e-9 for v in vols), loo


def evaluar(filas, regimen=None):
    alcance = [f for f in filas if regimen is None or f.get("regimen") == regimen]
    ok = [f for f in alcance if f.get("ok")]
    control = control_instrumento(ok)
    validas, motivos = [], collections.Counter()
    for f in alcance:
        es, motivo = fila_valida(f)
        if es:
            validas.append(f)
        elif motivo != "control":
            motivos[motivo] += 1

    por_volcan = {}
    for vol in sorted({f["volcan"] for f in validas}):
        fs = [f for f in validas if f["volcan"] == vol]
        c = _conteo(fs)
        exc = _mediana([f["resumen"].get("exceso_mediano_calientes_k") for f in fs])
        ctl = _mediana([(f["resumen"].get("control") or {}).get("exceso_mediano_calientes_k") for f in fs])
        contraste_k = None if (exc is None or ctl is None) else exc - ctl
        frac = _mediana([f["resumen"].get("fraccion_brecha") for f in fs])
        por_volcan[vol] = {
            "n_pasadas": len(fs), "evaluable": len(fs) >= N_MIN_VOLCAN, "conteo": dict(c),
            "destino": _dominante(c) or "DISPERSO", "exceso_calientes_k": exc, "exceso_control_k": ctl,
            "contraste_k": contraste_k,
            "contraste": None if contraste_k is None else
            ("VECINOS_TIBIOS" if contraste_k >= CONTRASTE_MIN_K else "SIN_CONTRASTE"),
            "mediana_fraccion_brecha": frac, "fondo": _clase_fondo(frac)}

    ev = {v: d for v, d in por_volcan.items() if d["evaluable"]}
    total = collections.Counter()
    for v in ev:
        total.update(ev[v]["conteo"])
    clave = _dominante(total)
    loo_destino = {v: _dominante(total - collections.Counter(ev[v]["conteo"])) for v in ev}
    apoyo = sum(ev[v]["destino"] == clave for v in ev)
    patron = (clave is not None and len(ev) >= MIN_VOLCANES and apoyo >= FRAC_VOLCANES * len(ev) - 1e-9
              and all(loo_destino[v] == clave for v in ev))
    destino = f"PATRON:{clave}" if patron else "HETEROGENEO"

    vt, loo_vt = _estable(ev, "contraste", "VECINOS_TIBIOS")
    sc, _ = _estable(ev, "contraste", "SIN_CONTRASTE")
    contraste = "VECINOS_TIBIOS" if vt else "SIN_CONTRASTE" if sc else "HETEROGENEO"
    fondo = "HETEROGENEO"
    for clase in ("CIERRA", "PARCIAL", "NO_CIERRA"):
        if _estable(ev, "fondo", clase)[0]:
            fondo = clase
            break

    if control["estado"] != "OK":
        veredicto = "INDETERMINADO:instrumento"
    elif len(ev) < MIN_VOLCANES:
        veredicto = "INDETERMINADO:pocos_volcanes"
    else:
        veredicto = f"{destino} | {contraste} | fondo {fondo}"
    ctl_filas = [f for f in alcance if f.get("ok") and f.get("clase") == "control"]
    return {
        "n_filas": len(alcance), "n_validas": len(validas), "motivos_fuera": dict(motivos),
        "control": control, "por_volcan": por_volcan, "n_volcanes_evaluables": len(ev),
        "conteo_agrupado": dict(total), "destino": destino, "contraste": contraste, "fondo": fondo,
        "loo": {"destino": loo_destino, "n_vecinos_tibios_sin": loo_vt},
        "veredicto": veredicto,
        "justifica_brazo": (not veredicto.startswith("INDETERMINADO") and destino.startswith("PATRON")
                            and contraste == "VECINOS_TIBIOS"),
        "controles_descriptivo": {
            "n": len(ctl_filas),
            "n_publicado_hoy_ge_2": sum(((f.get("hoy") or {}).get("n_publicado") or 0) >= 2 for f in ctl_filas)},
    }
