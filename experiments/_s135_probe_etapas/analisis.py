"""S135 — análisis puro del probe por etapa (D19 / decisión D1-b de AUDIT_S134 §D).

Este módulo NO toca granules ni el pipeline: recibe arrays y diccionarios y devuelve
números. Está separado del runner (`probe_etapas.py`) para poder testearlo offline
(`tests/test_probe_etapas_s135.py`) y para re-evaluar el criterio pre-registrado sobre
los JSON que el workflow sube como artefacto, sin volver a correr nada en CI.

El fenómeno que se mide (AUDIT_S134 §3, D19): en un cono nevado el píxel más caliente
en el infrarrojo medio de un disco de 3 km alrededor de la cumbre es el borde del disco
(cota más baja), no el cráter. `keep_peak` conserva sólo ese píxel. Lo que ningún JSON
persiste es el footprint del Test 1 ANTES del recorte: cuántos píxeles del cráter había,
y con qué temperatura. Eso es lo que `resumir_pasada` cuantifica.

Criterio pre-registrado (copiado de `experiments/_s134_audit/f3/probe_etapas_ci.md`,
en las unidades del objeto — A91):
  H1 confirmada a nivel granule si, en las 3 pasadas de Villarrica, `mask_contributing`
     contiene >=1 píxel a <0,5 km del cráter Y el `keep_peak_rc` está a >2 km, Y en las
     3 de Láscar el `keep_peak_rc` (si aplica) está a <0,5 km.
  H1 refutada si en Villarrica el cráter no está en `mask_contributing`.
  H2 confirmada si >=90 % de los `newly_active` con `n_first_pass==0` tienen
     `bt - t_bg <= 3 K`.
"""
from __future__ import annotations

import math

import numpy as np

R_TIERRA_KM = 6371.0
OCTANTES = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

# Umbrales del criterio pre-registrado (km / K / fracción). No se ajustan a posteriori.
CRATER_KM = 0.5
PICO_LEJOS_KM = 2.0
DISCO_KM = 3.0
ANILLO_PASO_KM = 0.25
H2_COMPUERTA_K = 3.0
H2_FRACCION_MIN = 0.90
NUBE_DELTA_K = 10.0        # disco 3 km más de 10 K bajo el fondo global → sospechar nube
PASO0_PIERDE_MIN = 2       # pre-registro paso 0: ≥2 cat-b perdidas con OFF y pico en cráter → tensión real


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia sobre la esfera, en km. Acepta escalares o arrays numpy."""
    lat1 = np.radians(np.asarray(lat1, dtype=float))
    lon1 = np.radians(np.asarray(lon1, dtype=float))
    lat2 = np.radians(np.asarray(lat2, dtype=float))
    lon2 = np.radians(np.asarray(lon2, dtype=float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(a))


def rumbo_deg(lat0, lon0, lat, lon):
    """Rumbo inicial desde (lat0, lon0) hacia (lat, lon), en grados [0, 360)."""
    lat0 = np.radians(np.asarray(lat0, dtype=float))
    lon0 = np.radians(np.asarray(lon0, dtype=float))
    lat = np.radians(np.asarray(lat, dtype=float))
    lon = np.radians(np.asarray(lon, dtype=float))
    dlon = lon - lon0
    x = np.sin(dlon) * np.cos(lat)
    y = np.cos(lat0) * np.sin(lat) - np.sin(lat0) * np.cos(lat) * np.cos(dlon)
    return (np.degrees(np.arctan2(x, y)) + 360.0) % 360.0


def octante(rumbo):
    """Nombre del octante (N, NE, ...) para un rumbo en grados."""
    idx = (np.round(np.asarray(rumbo, dtype=float) / 45.0).astype(int)) % 8
    return np.asarray(OCTANTES, dtype=object)[idx]


def perfil_bt_vs_distancia(bt, dist_km, rumbo, paso_km=ANILLO_PASO_KM, max_km=DISCO_KM):
    """Mediana de BT por anillo de `paso_km` hasta `max_km`, total y por octante (A70).

    Devuelve una lista de dicts, uno por anillo, con `n`, `bt_mediana` y un dict
    `por_octante` {octante: {"n":…, "bt_mediana":…}}. NaN → None para el JSON.
    Distingue «borde = cota baja en todas direcciones» (todos los octantes suben con
    la distancia) de «valle de un lado» (sólo uno o dos suben).
    """
    bt = np.asarray(bt, dtype=float)
    dist_km = np.asarray(dist_km, dtype=float)
    oct_arr = octante(rumbo)
    out = []
    bordes = np.arange(0.0, max_km + 1e-9, paso_km)
    for a, b in zip(bordes[:-1], bordes[1:]):
        sel = (dist_km >= a) & (dist_km < b) & np.isfinite(bt)
        fila = {
            "desde_km": round(float(a), 3),
            "hasta_km": round(float(b), 3),
            "n": int(sel.sum()),
            "bt_mediana": (float(np.median(bt[sel])) if sel.any() else None),
            "por_octante": {},
        }
        for o in OCTANTES:
            s = sel & (oct_arr == o)
            fila["por_octante"][o] = {
                "n": int(s.sum()),
                "bt_mediana": (float(np.median(bt[s])) if s.any() else None),
            }
        out.append(fila)
    return out


def _px_info(r, c, bt, lat, lon, dist_vent, dist_ancla, t_bg_global):
    b = float(bt[r, c])
    return {
        "row": int(r), "col": int(c),
        "lat": round(float(lat[r, c]), 5), "lon": round(float(lon[r, c]), 5),
        "bt_k": round(b, 2),
        "dist_vent_km": round(float(dist_vent[r, c]), 3),
        "dist_ancla_km": round(float(dist_ancla[r, c]), 3),
        "bt_menos_t_bg_global_k": (round(b - t_bg_global, 2)
                                   if t_bg_global is not None and np.isfinite(b) else None),
    }


def resumir_pasada(cap, vent_lat, vent_lon, ancla_lat, ancla_lon, t_bg_global):
    """Reduce lo capturado por los monkeypatches de UNA pasada a números.

    `cap` es el dict que llena el runner. Claves esperadas (todas opcionales; lo que
    falte se reporta como ausente en vez de reventar):
      test1: {"bt","lat","lon","mask_contributing","triggered","n_contributing",
              "roi_km", ...}
      ctx_filter: {"mask_in","dnti_ctx","keep_peak_rc","mask_out"}
      first_pass: {"hot","dist_km","t_bg","diag"}
      second_pass: [ {"active_in","out"} , ... ]
      clusters: [ {"n_in","strategy","inner_radius_km","clusters":[...] }, ... ]

    Distancias: se reportan las dos —al `vent_*` de `volcanoes.yaml` y al ancla de
    detección (`get_detection_anchor`)— porque no son el mismo punto en todos los
    volcanes (A3/A93). El criterio usa la distancia al vent (el cráter físico).
    """
    res = {"t_bg_global_k": t_bg_global}
    t1 = cap.get("test1")
    if not t1:
        res["test1"] = {"corrio": False}
        return res

    bt = np.asarray(t1["bt"], dtype=float)
    lat = np.asarray(t1["lat"], dtype=float)
    lon = np.asarray(t1["lon"], dtype=float)
    mask = np.asarray(t1["mask_contributing"], dtype=bool)
    dist_vent = haversine_km(vent_lat, vent_lon, lat, lon)
    dist_ancla = haversine_km(ancla_lat, ancla_lon, lat, lon)
    rumbo = rumbo_deg(vent_lat, vent_lon, lat, lon)
    disco = (dist_vent < DISCO_KM) & np.isfinite(bt)

    # --- 1. ¿Está el cráter dentro del Test 1 antes del recorte? ---
    crater = mask & (dist_vent < CRATER_KM)
    rr, cc = np.where(crater)
    px_crater = [_px_info(r, c, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
                 for r, c in zip(rr, cc)]
    # Rango del píxel más caliente del cráter dentro de la máscara (1 = el más caliente).
    rango_crater = None
    if mask.any() and crater.any():
        bts_mask = np.sort(bt[mask])[::-1]
        bt_crater_max = float(np.nanmax(bt[crater]))
        rango_crater = int(np.sum(bts_mask > bt_crater_max)) + 1
    disco_lat_lon = None
    # Píxel más cercano al vent en el disco (para saber cuál "es" el cráter en la grilla).
    if disco.any():
        k = int(np.nanargmin(np.where(disco, dist_vent, np.inf)))
        r0, c0 = np.unravel_index(k, bt.shape)
        disco_lat_lon = _px_info(r0, c0, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
        disco_lat_lon["en_mask_contributing"] = bool(mask[r0, c0])
    res["test1"] = {
        "corrio": True,
        "triggered": bool(t1.get("triggered")),
        "n_contributing": int(mask.sum()),
        "n_en_disco": int(disco.sum()),
        "roi_km": t1.get("roi_km"),
        "k_sigma_observed": t1.get("k_sigma_observed"),
        "mediana_dist_vent_mask_km": (round(float(np.median(dist_vent[mask])), 3)
                                      if mask.any() else None),
        "n_mask_a_menos_0_5km": int(crater.sum()),
        "n_mask_a_menos_1km": int((mask & (dist_vent < 1.0)).sum()),
        "pixeles_crater_en_mask": px_crater,
        "rango_bt_crater_en_mask": rango_crater,
        "pixel_mas_cercano_al_vent": disco_lat_lon,
    }

    # --- 2. El píxel keep_peak ---
    cf = cap.get("ctx_filter")
    if cf and cf.get("keep_peak_rc") is not None:
        r, c = cf["keep_peak_rc"]
        info = _px_info(r, c, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
        # ¿Es el argmax del DISCO entero o sólo de la máscara?
        argmax_disco = None
        if disco.any():
            k = int(np.nanargmax(np.where(disco, bt, -np.inf)))
            rd, cd = np.unravel_index(k, bt.shape)
            argmax_disco = _px_info(rd, cd, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
        info["es_argmax_del_disco"] = (argmax_disco is not None
                                      and argmax_disco["row"] == info["row"]
                                      and argmax_disco["col"] == info["col"])
        info["argmax_del_disco"] = argmax_disco
        info["octante"] = str(octante(rumbo[r, c]))
        res["keep_peak"] = info
        # --- 3. (Test1 ∩ dNTI_ctx) sin el pico ---
        m_in = np.asarray(cf["mask_in"], dtype=bool)
        dn = cf.get("dnti_ctx")
        inter = (m_in & np.asarray(dn, dtype=bool)) if dn is not None else np.zeros_like(m_in)
        ri, ci = np.where(inter)
        res["interseccion_sin_pico"] = {
            "dnti_ctx_disponible": dn is not None,
            "n_dnti_ctx_total": (int(np.asarray(dn, dtype=bool).sum()) if dn is not None else None),
            "n": int(inter.sum()),
            "pixeles": [_px_info(r, c, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
                        for r, c in zip(ri, ci)],
            "n_mask_out": int(np.asarray(cf["mask_out"], dtype=bool).sum()),
        }
    else:
        res["keep_peak"] = None
        res["interseccion_sin_pico"] = None

    # --- 3b. Nube sobre la cumbre (paso 0, S135): el disco entero muy por debajo del fondo
    # global no es cota (un lapso ambiental da ~8-9 K sobre 1.300 m); I05 ayuda si vino.
    i04_med = float(np.median(bt[disco])) if disco.any() else None
    l1b = cap.get("l1b") or {}
    bt5 = l1b.get("I05") if isinstance(l1b, dict) else None
    i05_med = None
    if bt5 is not None and np.shape(bt5) == bt.shape:
        b5 = np.asarray(bt5, dtype=float)
        s5 = disco & np.isfinite(b5)
        i05_med = float(np.median(b5[s5])) if s5.any() else None
    delta = (round(i04_med - t_bg_global, 2) if (i04_med is not None and t_bg_global is not None) else None)
    res["nube"] = {
        "i04_disco_mediana_k": (round(i04_med, 2) if i04_med is not None else None),
        "i04_disco_menos_t_bg_k": delta,
        "i05_disco_mediana_k": (round(i05_med, 2) if i05_med is not None else None),
        "sospechada": (bool(delta is not None and delta < -NUBE_DELTA_K)),
        "criterio": f"disco I04 mediana < t_bg_global - {NUBE_DELTA_K} K",
    }

    # --- 4. Perfil BT vs distancia por octante ---
    res["perfil_bt"] = perfil_bt_vs_distancia(bt[disco], dist_vent[disco], rumbo[disco])
    for a, b in ((1.0, 3.0), (1.5, 3.0)):
        s = (dist_vent >= a) & (dist_vent < b) & np.isfinite(bt)
        res[f"bt_mediana_anillo_{a}_{b}_km"] = (float(np.median(bt[s])) if s.any() else None)

    # --- 5. H2: second pass sin conjunto activo ---
    fp = cap.get("first_pass")
    n_fp = int(np.asarray(fp["hot"], dtype=bool).sum()) if fp else None
    sps = []
    for sp in cap.get("second_pass", []):
        act = np.asarray(sp["active_in"], dtype=bool)
        out = np.asarray(sp["out"], dtype=bool)
        nuevos = out & ~act
        rn, cn = np.where(nuevos)
        px = [_px_info(r, c, bt, lat, lon, dist_vent, dist_ancla, t_bg_global)
              for r, c in zip(rn, cn)]
        bajo = [p for p in px if p["bt_menos_t_bg_global_k"] is not None
                and p["bt_menos_t_bg_global_k"] <= H2_COMPUERTA_K]
        sps.append({
            "n_active_in": int(act.sum()),
            "n_out": int(out.sum()),
            "n_newly_active": int(nuevos.sum()),
            "n_newly_bajo_compuerta_3k": len(bajo),
            "newly_active": px,
        })
    res["first_pass"] = {"n_hot": n_fp,
                         "diag": (fp.get("diag") if fp else None)}
    res["second_pass"] = sps

    # --- clusters ---
    res["clusters"] = cap.get("clusters", [])
    return res


def evaluar_criterio(pasadas):
    """Aplica el criterio pre-registrado sobre la lista de resúmenes por pasada.

    `pasadas`: lista de dicts con claves `volcan`, `clase` ("nevado"|"control"),
    `ok` (bool: la pasada se procesó) y `resumen` (salida de `resumir_pasada`).
    Devuelve un dict con el veredicto de H1 y H2 y el detalle por pasada.
    """
    det = []
    h1_ok_nevado, h1_crater_ausente = [], []
    h1_ok_control = []
    h2_num, h2_den = 0, 0
    for p in pasadas:
        fila = {"volcan": p["volcan"], "pasada_utc": p.get("pasada_utc"),
                "clase": p["clase"], "ok": bool(p.get("ok"))}
        if not p.get("ok") or not p.get("resumen") or not p["resumen"].get("test1", {}).get("corrio"):
            fila["h1"] = "no_evaluable"
            det.append(fila)
            continue
        r = p["resumen"]
        t1 = r["test1"]
        kp = r.get("keep_peak")
        crater_en_mask = t1["n_mask_a_menos_0_5km"] >= 1
        d_pico = kp["dist_vent_km"] if kp else None
        fila.update(crater_en_mask=crater_en_mask, n_crater=t1["n_mask_a_menos_0_5km"],
                    keep_peak_dist_vent_km=d_pico,
                    keep_peak_bt_menos_t_bg=(kp["bt_menos_t_bg_global_k"] if kp else None))
        if p["clase"] == "nevado":
            if not crater_en_mask:
                h1_crater_ausente.append(fila)
                fila["h1"] = "crater_fuera_del_test1"
            elif d_pico is not None and d_pico > PICO_LEJOS_KM:
                h1_ok_nevado.append(fila)
                fila["h1"] = "confirma"
            else:
                fila["h1"] = "no_confirma"
        else:  # control
            if kp is None:
                fila["h1"] = "keep_peak_no_aplica"
                h1_ok_control.append(fila)   # «si aplica»: sin pico no hay contraejemplo
            elif d_pico < CRATER_KM:
                fila["h1"] = "control_ok"
                h1_ok_control.append(fila)
            else:
                fila["h1"] = "control_falla"
        # H2: sólo cuenta cuando el first pass quedó vacío.
        n_fp = (r.get("first_pass") or {}).get("n_hot")
        if n_fp == 0:
            for sp in r.get("second_pass", []):
                h2_den += sp["n_newly_active"]
                h2_num += sp["n_newly_bajo_compuerta_3k"]
        fila["n_first_pass"] = n_fp
        det.append(fila)

    n_nev = sum(1 for p in pasadas if p["clase"] == "nevado")
    n_ctl = sum(1 for p in pasadas if p["clase"] == "control")
    if h1_crater_ausente:
        h1 = "REFUTADA (el cráter no está en mask_contributing: el problema es anterior a keep_peak)"
    elif len(h1_ok_nevado) == n_nev and len(h1_ok_control) == n_ctl and n_nev > 0:
        h1 = "CONFIRMADA a nivel granule"
    else:
        h1 = "INDETERMINADA (no se cumple en todas las pasadas; ver detalle)"
    if h2_den == 0:
        h2 = "NO EVALUABLE (ningún newly_active con first pass vacío)"
    else:
        frac = h2_num / h2_den
        h2 = (f"CONFIRMADA ({h2_num}/{h2_den} = {frac:.0%} ≤ 3 K)" if frac >= H2_FRACCION_MIN
              else f"NO CONFIRMADA ({h2_num}/{h2_den} = {frac:.0%} ≤ 3 K; se exigía ≥ 90 %)")
    return {
        "h1": h1, "h2": h2,
        "n_nevado_confirman": f"{len(h1_ok_nevado)}/{n_nev}",
        "n_control_ok": f"{len(h1_ok_control)}/{n_ctl}",
        "h2_newly_bajo_compuerta": f"{h2_num}/{h2_den}",
        "detalle": det,
    }


def a_json(obj):
    """Convierte numpy → tipos nativos para `json.dumps`."""
    if isinstance(obj, dict):
        return {str(k): a_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [a_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return a_json(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def evaluar_paso0(pasadas):
    """Paso 0 del A/B D1(c) — criterio PRE-REGISTRADO (S135, escrito antes de correr):

    Para cada pasada cat-b (Lastarria/Tupungatito/Isluga con alerta MIROVA en la misma
    pasada) y cada control_fp0 (Láscar, first pass vacío, con alerta):
      off_pierde = (Test1 ∩ dNTI_ctx) sin pico == 0 px  Y  first pass == 0
                   (con keep_peak OFF no queda ningún píxel del Test 1 y no hay otro path:
                    la pasada MIROVA-confirmada desaparece del dashboard).
      pico_en_crater = keep_peak a < 0,5 km del vent.
      nube_sospechada = disco I04 mediana < t_bg_global − 10 K (esas pasadas NO cuentan).
    Veredicto:
      TENSIÓN REAL     si ≥ 2 pasadas cat-b (sin nube) tienen off_pierde y pico_en_crater
                       → el A/B debe medir FN sobre cat-b; keep_peak no se apaga a ciegas.
      TENSIÓN APARENTE si ninguna cat-b (sin nube) se pierde con OFF
                       → apagar keep_peak no destruye señal MIROVA-confirmada en estas pasadas.
      INTERMEDIA       en cualquier otro caso (se pierden pasadas cuyo pico NO está en el
                       cráter: el A/B debe decidir con la distancia de MIROVA como referencia).
    """
    det = []
    reales, perdidas_borde = 0, 0
    for p in pasadas:
        if p.get("clase") not in ("cat_b", "control_fp0"):
            continue
        fila = {"volcan": p["volcan"], "pasada_utc": p.get("pasada_utc"), "clase": p["clase"],
                "ok": bool(p.get("ok")), "mirova": p.get("mirova")}
        r = p.get("resumen") or {}
        if not p.get("ok") or not r.get("test1", {}).get("corrio"):
            fila["estado"] = "no_evaluable"
            det.append(fila)
            continue
        kp = r.get("keep_peak")
        it = r.get("interseccion_sin_pico") or {}
        n_fp = (r.get("first_pass") or {}).get("n_hot")
        nube = bool((r.get("nube") or {}).get("sospechada"))
        off_pierde = bool(kp is not None and it.get("n") == 0 and n_fp == 0)
        fila.update(
            pico_dist_vent_km=(kp["dist_vent_km"] if kp else None),
            pico_bt_menos_t_bg=(kp["bt_menos_t_bg_global_k"] if kp else None),
            n_crater=r["test1"]["n_mask_a_menos_0_5km"],
            n_interseccion_sin_pico=it.get("n"),
            n_first_pass=n_fp,
            off_pierde=off_pierde,
            pico_en_crater=(bool(kp and kp["dist_vent_km"] < CRATER_KM)),
            nube_sospechada=nube,
            keep_peak_aplico=(kp is not None),
        )
        fila["estado"] = "evaluada"
        if p["clase"] == "cat_b" and not nube and off_pierde:
            if fila["pico_en_crater"]:
                reales += 1
            else:
                perdidas_borde += 1
        det.append(fila)
    n_catb = sum(1 for d in det if d["clase"] == "cat_b" and d.get("estado") == "evaluada"
                 and not d.get("nube_sospechada"))
    if reales >= PASO0_PIERDE_MIN:
        v = (f"TENSIÓN REAL: {reales}/{n_catb} cat-b (sin nube) se pierden con keep_peak OFF y su pico "
             f"está en el cráter → el A/B debe medir FN sobre cat-b")
    elif reales == 0 and perdidas_borde == 0:
        v = f"TENSIÓN APARENTE: 0/{n_catb} cat-b (sin nube) se pierden con keep_peak OFF"
    else:
        v = (f"INTERMEDIA: {reales} perdidas con pico en cráter + {perdidas_borde} perdidas con pico "
             f"fuera del cráter, de {n_catb} cat-b sin nube")
    return {"veredicto": v, "reales": reales, "perdidas_borde": perdidas_borde,
            "n_catb_evaluadas_sin_nube": n_catb, "detalle": det}
