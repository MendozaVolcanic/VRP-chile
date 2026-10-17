# Tarea 1.23: junta los JSON por job del probe y aplica el criterio pre-registrado en README.md.
# Corre en el job "agregar" del workflow y en local sobre los artefactos bajados.
#
# POR QUE ASI. MxD03 sola es determinista: C y M sobre el mismo L1B con el mismo codigo dan lo mismo
# que en la 1.21 (2 protegidas perdidas, 9 ganadas, salvo deriva de codigo). Por la letra de la regla 1
# (docs/MISSION.md) eso ya es PIERDE PROTEGIDA y este probe no lo puede cambiar. Lo que agrega son tres
# lecturas que la 1.21 no podia dar, cada una con sus estados fijados antes de correr:
#   1. el nulo con distribucion: 20 corrimientos al azar del mismo tamano EN KM por granulo, y la
#      posicion de M entre ellos (rango), en las dos direcciones de la regla 1 (lo que M pierde de lo que
#      C publica, y lo que C pierde de lo que M publica) y en el balance de la regla 2;
#   2. la vara externa: cual de las dos geolocalizaciones pone el pixel caliente mas cerca del objeto
#      que ve VIIRS 375 esa noche (vara_viirs.json, congelada), con direccion y con control de sesgo por
#      satelite (Terra y Aqua corren la grilla en sentidos opuestos);
#   3. el Test 1 y el borde del barrido: si los cruces del umbral y los saltos de cumulo de M son lo que
#      hace cualquier corrimiento de ese tamano o algo propio de MxD03.
# Los rangos son de Monte Carlo: con K nulos el p mas chico posible es 1/(K+1) (0,048 con K = 20; K = 19
# tambien cumpliria p <= 0,05 con 0,050). Los 20 nulos de un granulo no son independientes (rumbos
# vecinos dan resultados parecidos), asi que el p es nominal (README, «Poder»).
#
# Uso: python evaluar_sola.py <carpeta con los <job>.json> [--jobs '["Lascar-1a", ...]'] [--salida x.json]
import argparse
import json
import math
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DIR_117 = AQUI.parent / "_s151_mxd03_etiquetas"
DIR_121 = AQUI.parent / "_s151_mxd03_cumulo_121"
for p in (AQUI, DIR_121, DIR_117, AQUI.parents[1] / "scripts"):
    sys.path.insert(0, str(p))

import evaluar_cumulo as E21  # noqa: E402  (1.21: comparar = regla 1 + balance de la regla 2)
import jobs_123 as J  # noqa: E402

K_NULOS = 20
NULOS = tuple("R%02d" % k for k in range(K_NULOS))
BRAZOS = ("C", "M") + NULOS
ALFA = 0.05
TOL_KM = 0.01             # el nulo tiene el tamano en km del corrimiento real, y el aplicado es el pedido
TOL_RUMBO = 1e-3          # rumbos equiespaciados cada 360/K grados
N_MIN_VARA = 10           # granulos con vara para dar un veredicto de posicion (README, «Poder»)
N_MIN_NOCHES = 5
N_MIN_SATELITE = 5        # granulos de un satelite para usarlo en el control de sesgo
B_BOOT, SEMILLA = 1000, 20261017
SALTO_PAR = 4             # pares de nulos (k, k + 4): separacion 1,18 veces la de C y M
TOL_SALTO_KM = 1.5        # la tolerancia de tipos_de_cambio de la 1.21
BINS_CENIT = ((0, 20), (20, 35), (35, 50), (50, 90))


def _cargar(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ rangos de Monte Carlo
def p_rango(obs, nulos, cola):
    """p de Monte Carlo de `obs` contra `nulos`: cola 'alta' = P(nulo >= obs), 'baja' = P(nulo <= obs),
    con el +1 de Davison y Hinkley (el observado cuenta como uno mas)."""
    if obs is None or not nulos:
        return None
    if cola == "alta":
        n = sum(1 for x in nulos if x >= obs)
    else:
        n = sum(1 for x in nulos if x <= obs)
    return round((1 + n) / (len(nulos) + 1), 4)


def lectura_rango(obs, nulos, mas, menos, igual):
    alta, baja = p_rango(obs, nulos, "alta"), p_rango(obs, nulos, "baja")
    if alta is None:
        return {"estado": "SIN DATOS", "p_alta": None, "p_baja": None}
    estado = mas if alta <= ALFA else (menos if baja <= ALFA else igual)
    return {"estado": estado, "observado": obs, "nulos": sorted(nulos), "p_alta": alta, "p_baja": baja,
            "mediana_nulos": st.median(nulos)}


# ------------------------------------------------------------------ union con la poblacion
def _unir(pob, salidas):
    medidas = {}
    for s in salidas.values():
        for g in s.get("granulos", []):
            medidas[(s["volcan"], g["clave"])] = g
    filas = []
    for vol, v in pob["volcanes"].items():
        for g in v["muestra"]:
            m = medidas.get((vol, g["clave"]), {})
            filas.append(dict(g, volcan=vol, **{k: x for k, x in m.items() if k not in g}))
    return filas


# ------------------------------------------------------------------ la vara VIIRS
def _ne(vent, lat, lon):
    return ((lat - vent[0]) * 111.32, (lon - vent[1]) * 111.32 * math.cos(math.radians(vent[0])))


def _pos(f, b, fuente):
    if fuente in ("pico", "pico_centro"):
        p = ((f.get("pico") or {}).get("pos" if fuente == "pico" else "pos_centro") or {}).get(b)
        return None if p is None else (p[0], p[1])
    s = (f.get("brazos") or {}).get(b) or {}
    return None if s.get("pc_lat") is None else (s["pc_lat"], s["pc_lon"])


def _boot_mediana(valores_por_noche, rng, b=B_BOOT):
    noches = list(valores_por_noche)
    if not noches:
        return None
    meds = []
    for _ in range(b):
        x = []
        for n in (rng.choice(noches) for _ in noches):
            x.extend(valores_por_noche[n])
        meds.append(st.median(x))
    meds.sort()
    return [round(meds[int(0.025 * b)], 4), round(meds[int(0.975 * b) - 1], 4)]


def vara(ok, tabla, fuente="pico", nivel="estricta", filtro_modis="pos"):
    """Que geolocalizacion pone la posicion MODIS mas cerca del objeto VIIRS de la noche.
    Por granulo: dd = |C - v| - |M - v| (km; > 0 quiere decir que M queda mas cerca), lambda = proyeccion
    de (v - C) sobre (M - C) en unidades de |M - C| (1 = donde dice M, 0 = donde dice C) y el residuo
    perpendicular. Bootstrap por noche (volcan y fecha UTC), porque Terra y Aqua de una noche comparten v.
    Nulo MEDIDO del estadistico (A110): los nulos k y k + 4 son dos posiciones sin informacion, separadas
    2 sen(36 grados) = 1,18 veces |C - M|. Intercambiarlos solo cambia el signo de su dd y deja igual su
    distribucion (los dos son puntos del mismo circulo con la misma separacion angular y una fase
    uniforme), asi que su dd tiene mediana 0 por construccion. Las 20 medianas de esos pares dicen cuanto
    "prefiere" la vara una posicion sobre otra POR AZAR, con la geometria, el ruido y la vara reales; el
    efecto de M tiene que quedar fuera de todas. Se informa ademas cuantos de los 20 pares tienen un IC que
    excluye el 0 (los pares comparten fase y estan correlacionados: es una anotacion, no una tasa)."""
    rng = random.Random(SEMILLA)
    filas = []
    for f in ok:
        t = (tabla.get("granulos") or {}).get("%s|%s" % (f["volcan"], f["clave"]))
        if not t or not (t.get(nivel) or {}).get("noche"):
            continue
        if filtro_modis == "pos" and f.get("lab") != "pos":
            continue
        c, m = _pos(f, "C", fuente), _pos(f, "M", fuente)
        if c is None or m is None:
            continue
        vent = t["vent"]
        v = (t[nivel]["noche"]["n_km"], t[nivel]["noche"]["e_km"])
        cn, mn = _ne(vent, *c), _ne(vent, *m)
        dc, dm = math.hypot(cn[0] - v[0], cn[1] - v[1]), math.hypot(mn[0] - v[0], mn[1] - v[1])
        ax = (mn[0] - cn[0], mn[1] - cn[1])
        a2 = ax[0] ** 2 + ax[1] ** 2
        lam = ((v[0] - cn[0]) * ax[0] + (v[1] - cn[1]) * ax[1]) / a2 if a2 > 1e-8 else None
        perp = (abs((v[0] - cn[0]) * ax[1] - (v[1] - cn[1]) * ax[0]) / math.sqrt(a2)) if a2 > 1e-8 else None
        nul = {}
        for b in NULOS:
            r = _pos(f, b, fuente)
            if r is not None:
                rn = _ne(vent, *r)
                nul[b] = math.hypot(rn[0] - v[0], rn[1] - v[1])
        par = [(nul[NULOS[k]] - nul[NULOS[(k + SALTO_PAR) % K_NULOS]])
               if (NULOS[k] in nul and NULOS[(k + SALTO_PAR) % K_NULOS] in nul) else None for k in range(K_NULOS)]
        filas.append({"clave": f["clave"], "volcan": f["volcan"], "noche": "%s|%s" % (f["volcan"], f["datetime_utc"][:10]),
                      "satelite": (f.get("sensor") or "?").replace("MODIS_", ""), "cenit": f.get("sensor_zenith_deg"),
                      "dd": dc - dm, "d_C": dc, "d_M": dm, "lambda": lam, "perp": perp, "d_nulos": nul,
                      "pares_nulos": par, "sep_CM": math.sqrt(a2)})
    out = {"fuente": fuente, "nivel": nivel, "filtro_modis": filtro_modis, "n": len(filas),
           "n_noches": len({x["noche"] for x in filas}), "por_volcan": dict(_contar(filas, "volcan"))}
    if not filas:
        out["estado"] = "SIN VARA"
        return out

    def por_noche(clave, sel):
        d = defaultdict(list)
        for x in sel:
            if x[clave] is not None:
                d[x["noche"]].append(x[clave])
        return d
    out["dd_mediana_km"] = round(st.median(x["dd"] for x in filas), 4)
    out["dd_ic95"] = _boot_mediana(por_noche("dd", filas), rng)
    lams = [x["lambda"] for x in filas if x["lambda"] is not None]
    out["lambda_mediana"] = round(st.median(lams), 4) if lams else None
    out["lambda_ic95"] = _boot_mediana(por_noche("lambda", filas), rng)
    perps = [x["perp"] for x in filas if x["perp"] is not None]
    out["perpendicular_mediana_km"] = round(st.median(perps), 4) if perps else None
    out["separacion_CM_mediana_km"] = round(st.median(x["sep_CM"] for x in filas), 4)
    out["M_mas_cerca"] = sum(x["dd"] > 0 for x in filas)
    meds_nulo, excluyen = [], 0
    for k in range(K_NULOS):
        sel = [x for x in filas if x["pares_nulos"][k] is not None]
        if not sel:
            continue
        meds_nulo.append(round(st.median(x["pares_nulos"][k] for x in sel), 4))
        d = defaultdict(list)
        for x in sel:
            d[x["noche"]].append(x["pares_nulos"][k])
        ic = _boot_mediana(d, rng)
        excluyen += ic[0] > 0 or ic[1] < 0
    out["nulo_del_estadistico"] = {"pares": len(meds_nulo), "separacion_relativa": round(2 * math.sin(math.pi * SALTO_PAR / K_NULOS), 3),
                                   "medianas_km": meds_nulo, "ic_que_excluyen_el_0": excluyen,
                                   "max_abs_km": max((abs(x) for x in meds_nulo), default=None)}
    out["por_satelite"] = {}
    for sat in sorted({x["satelite"] for x in filas}):
        sel = [x for x in filas if x["satelite"] == sat]
        out["por_satelite"][sat] = {"n": len(sel), "dd_mediana_km": round(st.median(x["dd"] for x in sel), 4),
                                    "dd_ic95": _boot_mediana(por_noche("dd", sel), rng)}
    out["por_cenit"] = {}
    for lo, hi in BINS_CENIT:
        sel = [x for x in filas if x["cenit"] is not None and lo <= x["cenit"] < hi]
        if sel:
            out["por_cenit"]["%d-%d" % (lo, hi)] = {"n": len(sel), "dd_mediana_km": round(st.median(x["dd"] for x in sel), 4)}
    # M contra el azar con la vara: mediana de |X - v| de M entre las de los 20 nulos (cola baja = M mas cerca)
    t_m = st.median(x["d_M"] for x in filas)
    t_n = [st.median(x["d_nulos"][b] for x in filas if b in x["d_nulos"]) for b in NULOS
           if any(b in x["d_nulos"] for x in filas)]
    out["M_contra_el_azar"] = lectura_rango(round(t_m, 4), [round(v, 4) for v in t_n],
                                            "M MAS LEJOS QUE EL AZAR", "M MAS CERCA QUE EL AZAR", "M COMO EL AZAR")
    out["C_contra_el_azar"] = lectura_rango(round(st.median(x["d_C"] for x in filas), 4), [round(v, 4) for v in t_n],
                                            "C MAS LEJOS QUE EL AZAR", "C MAS CERCA QUE EL AZAR", "C COMO EL AZAR")
    out["estado"] = estado_vara(out)
    out["granulos"] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()
                        if k not in ("d_nulos", "pares_nulos")} for x in filas]
    return out


def estado_vara(o):
    """Estados de la vara, en este orden (README, «Estados»): SIN VARA, MXD03 o INTERP MAS CERCA (con o
    sin control de sesgo), SESGO POR SATELITE, INDECIDIBLE."""
    if o["n"] < N_MIN_VARA or o["n_noches"] < N_MIN_NOCHES:
        return "SIN VARA"
    lo, hi = o["dd_ic95"]
    nulo = (o.get("nulo_del_estadistico") or {}).get("max_abs_km")
    # el efecto tiene que salir del IC por noches Y quedar fuera de todo el nulo medido (README, «Estados»)
    fuera_del_nulo = nulo is not None and abs(o["dd_mediana_km"]) > nulo
    sats = [s for s in o["por_satelite"].values() if s["n"] >= N_MIN_SATELITE]
    if (lo > 0 or hi < 0) and fuera_del_nulo:
        signo = 1 if lo > 0 else -1
        if len(sats) < 2:
            return ("MXD03 MAS CERCA" if signo > 0 else "INTERP MAS CERCA") + " SIN CONTROL DE SESGO"
        if all((s["dd_mediana_km"] > 0) == (signo > 0) and s["dd_mediana_km"] != 0 for s in sats):
            return "MXD03 MAS CERCA" if signo > 0 else "INTERP MAS CERCA"
        return "SESGO POR SATELITE"
    return "INDECIDIBLE"


def _contar(filas, clave):
    d = defaultdict(int)
    for x in filas:
        d[x[clave]] += 1
    return d


# ------------------------------------------------------------------ el Test 1 y el borde del barrido
def test1_lectura(ok):
    """Cruces del umbral del Test 1 respecto de C (en los dos sentidos), M contra los nulos, y la
    descomposicion de log k = log dL - log sigma_bg - 1/2 log n_roi en los cambios C->M y C->R."""
    def cruces(b):
        n = 0
        for f in ok:
            c, x = ((f["brazos"]["C"] or {}).get("test1") or {}), ((f["brazos"][b] or {}).get("test1") or {})
            if c.get("triggered") is None or x.get("triggered") is None:
                continue
            n += bool(c["triggered"]) != bool(x["triggered"])
        return n
    obs = cruces("M")
    nul = [cruces(b) for b in NULOS]
    out = {"cruces": lectura_rango(obs, nul, "MXD03 CRUZA MAS QUE EL AZAR", "MXD03 CRUZA MENOS QUE EL AZAR",
                                   "PROPIEDAD DEL TEST 1 (M CRUZA COMO EL AZAR)")}
    desc = {}
    for nombre, bs in (("M", ("M",)), ("nulos", NULOS)):
        terminos = defaultdict(list)
        anillo = {"entra_al_anillo": 0, "sale_del_anillo": 0, "de": 0, "cruce_con_cambio_de_anillo": 0}
        for f in ok:
            c = (f["brazos"]["C"] or {}).get("test1") or {}
            for b in bs:
                x = (f["brazos"][b] or {}).get("test1") or {}
                vals = [c.get(k) for k in ("delta_L_integrated", "sigma_bg", "n_roi")] + \
                       [x.get(k) for k in ("delta_L_integrated", "sigma_bg", "n_roi")]
                if all(isinstance(v, (int, float)) and v and v > 0 for v in vals):
                    terminos["dlog_dL"].append(math.log(vals[3] / vals[0]))
                    terminos["menos_dlog_sigma"].append(-math.log(vals[4] / vals[1]))
                    terminos["menos_medio_dlog_n"].append(-0.5 * math.log(vals[5] / vals[2]))
                if c.get("caliente_en_anillo") is not None and x.get("caliente_en_anillo") is not None:
                    anillo["de"] += 1
                    anillo["entra_al_anillo"] += (not c["caliente_en_anillo"]) and x["caliente_en_anillo"]
                    anillo["sale_del_anillo"] += c["caliente_en_anillo"] and not x["caliente_en_anillo"]
                    if bool(c.get("triggered")) != bool(x.get("triggered")) and c["caliente_en_anillo"] != x["caliente_en_anillo"]:
                        anillo["cruce_con_cambio_de_anillo"] += 1
        desc[nombre] = {"n": len(terminos["dlog_dL"]),
                        "mediana_abs": {k: round(st.median(abs(v) for v in vs), 4) for k, vs in terminos.items() if vs},
                        "pixel_caliente": anillo}
    out["descomposicion"] = desc
    out["con_signo"] = test1_con_signo(ok)
    return out


def test1_con_signo(ok):
    """Verificador del pre-registro, bloqueante 2: la DIRECCION del cambio de k, por etiqueta de MIROVA.
    Si MxD03 pone mejor el calor, el Test 1 deberia ver MAS donde MIROVA alerto (k sube, cruces de 0 a 1)
    y MENOS donde MIROVA miro y no vio nada (k baja, cruces de 1 a 0). Por etiqueta (alertas: lab pos;
    negativos limpios) se mide en M y en cada nulo la mediana de k_X - k_C (granulos con Test 1 calculado
    en C y en X) y los cruces en cada sentido, y se ubica a M entre los 20 nulos."""
    def medir(b, lab):
        dk, sube, baja = [], 0, 0
        for f in ok:
            if f.get("lab") != lab:
                continue
            c = (f["brazos"]["C"] or {}).get("test1") or {}
            x = (f["brazos"][b] or {}).get("test1") or {}
            kc, kx = c.get("k_sigma_observed"), x.get("k_sigma_observed")
            if kc and kx:
                dk.append(kx - kc)
            if c.get("triggered") is not None and x.get("triggered") is not None:
                sube += (not c["triggered"]) and bool(x["triggered"])
                baja += bool(c["triggered"]) and not x["triggered"]
        return (st.median(dk) if dk else None), len(dk), sube, baja
    out = {}
    for lab, nombre in (("pos", "alertas"), ("neg_limpio", "negativos_limpios")):
        m = medir("M", lab)
        nul = [medir(b, lab) for b in NULOS]
        meds = [x[0] for x in nul if x[0] is not None]
        lec = lectura_rango(None if m[0] is None else round(m[0], 4), [round(v, 4) for v in meds],
                            "M SUBE K MAS QUE EL AZAR", "M BAJA K MAS QUE EL AZAR", "M COMO EL AZAR")
        lec.update({"n": m[1], "cruces_M_0_a_1": m[2], "cruces_M_1_a_0": m[3],
                    "cruces_0_a_1": lectura_rango(m[2], [x[2] for x in nul], "M ENCIENDE MAS QUE EL AZAR",
                                                  "M ENCIENDE MENOS QUE EL AZAR", "COMO EL AZAR"),
                    "cruces_1_a_0": lectura_rango(m[3], [x[3] for x in nul], "M APAGA MAS QUE EL AZAR",
                                                  "M APAGA MENOS QUE EL AZAR", "COMO EL AZAR")})
        out[nombre] = lec
    a, n = out["alertas"]["estado"], out["negativos_limpios"]["estado"]
    if "SIN DATOS" in (a, n):
        out["estado"] = "SIN DATOS"
    elif a == "M SUBE K MAS QUE EL AZAR" and n == "M BAJA K MAS QUE EL AZAR":
        out["estado"] = "SENAL DE POSICION MEJOR"
    elif a == "M BAJA K MAS QUE EL AZAR" and n == "M SUBE K MAS QUE EL AZAR":
        out["estado"] = "SENAL DE POSICION PEOR"
    elif a == "M COMO EL AZAR" and n == "M COMO EL AZAR":
        out["estado"] = "SIN DIRECCION (PROPIEDAD DEL TEST 1)"
    else:
        out["estado"] = "MIXTO"
    return out


def tamano_del_nulo(ok):
    """Anotacion por cenit (bloqueante 1 del verificador): el nulo tiene el km de M por construccion; aca
    se mide si tambien PERTURBA lo mismo. Razon del modulo en pixeles nulo / M (jacobiano sobre un barrido)
    y razon de centros que cruzan el borde del disco de 1 y 3 km y del inner, M contra la mediana de los
    nulos (con medio conteo para no dividir por 0). Lejos de 1 quiere decir que en ese cenit el nulo no es
    comparable en esa unidad."""
    out = {}
    for lo, hi in BINS_CENIT:
        sel = [f for f in ok if f.get("sensor_zenith_deg") is not None and lo <= f["sensor_zenith_deg"] < hi]
        if not sel:
            continue
        px = sorted(x["razon_px_nulo_M"] for f in sel for x in (f.get("nulos") or [])
                    if x.get("razon_px_nulo_M") is not None)
        res = {"n": len(sel)}
        if px:
            res["razon_px_nulo_M"] = {"mediana": round(st.median(px), 3), "p10": round(px[int(0.1 * len(px))], 3),
                                      "p90": round(px[min(int(0.9 * len(px)), len(px) - 1)], 3)}
        cruces = defaultdict(list)
        for f in sel:
            cb = f.get("cruces_de_borde") or {}
            if "M" not in cb:
                continue
            for r, vm in cb["M"].items():
                vn = [cb[b][r] for b in NULOS if b in cb]
                mn = st.median(vn) if vn else 0
                if vm or mn:
                    cruces[r].append((vm + 0.5) / (mn + 0.5))
        res["cruces_M_sobre_nulo"] = {r: {"mediana": round(st.median(v), 3), "n": len(v)} for r, v in cruces.items()}
        out["%d-%d" % (lo, hi)] = res
    return out


def _salto(a, b, corr):
    if (a or {}).get("pc_lat") is None or (b or {}).get("pc_lat") is None:
        return False
    d = math.hypot((a["pc_lat"] - b["pc_lat"]) * 111.32,
                   (a["pc_lon"] - b["pc_lon"]) * 111.32 * math.cos(math.radians(a["pc_lat"])))
    return d > corr + TOL_SALTO_KM


def borde_lectura(ok):
    """Saltos de cumulo (otro objeto: el cumulo publicado se mueve mas que el corrimiento + 1,5 km) por
    cenit, M contra los 20 nulos. El corrimiento de cada nulo es su km aplicado."""
    out = {}
    for lo, hi in BINS_CENIT + ((0, 90),):
        sel = [f for f in ok if f.get("sensor_zenith_deg") is not None and lo <= f["sensor_zenith_deg"] < hi]
        if not sel:
            continue
        obs = sum(_salto(f["brazos"]["C"], f["brazos"]["M"], f["desplazamiento"]["km"]) for f in sel)
        nul = []
        for k, b in enumerate(NULOS):
            nul.append(sum(_salto(f["brazos"]["C"], f["brazos"][b], f["nulos"][k]["km_aplicado"]) for f in sel))
        lec = lectura_rango(obs, nul, "MXD03 SALTA MAS QUE EL AZAR", "MXD03 SALTA MENOS QUE EL AZAR",
                            "SALTA COMO EL AZAR")
        lec["n"] = len(sel)
        lec["saltos_M_que_cambian_publicacion"] = [
            {"volcan": f["volcan"], "clave": f["clave"], "pub_C": f["pub"]["C"], "pub_M": f["pub"]["M"],
             "prot": f["prot"], "lab": f["lab"]} for f in sel
            if _salto(f["brazos"]["C"], f["brazos"]["M"], f["desplazamiento"]["km"]) and f["pub"]["C"] != f["pub"]["M"]]
        out["%d-%d" % (lo, hi)] = lec
    return out


# ------------------------------------------------------------------ evaluacion completa
def evaluar(pob, salidas, ausentes=(), esperados=None, tabla_vara=None):
    jobs = J.partir(pob)
    esperados = list(jobs) if esperados is None else list(esperados)
    aus = {(a["volcan"], a["clave"]) for a in ausentes}
    pedidos = {(jobs[j]["volcan"], c) for j in esperados for c in jobs[j]["granulos"]}
    vols = {jobs[j]["volcan"] for j in esperados}
    filas = [f for f in _unir(pob, salidas) if (f["volcan"], f["clave"]) in pedidos]
    ped = [f for f in filas if (f["volcan"], f["clave"]) not in aus]
    ok = [f for f in ped if f.get("estado") == "ok"]

    # ---- cobertura (A108)
    incompleto = []
    commits = sorted({str(s.get("commit")) for j, s in salidas.items() if j in esperados})
    if any(not salidas[j].get("commit") for j in esperados if j in salidas):
        incompleto.append("artefactos sin commit")
    if len([c for c in commits if c != "None"]) > 1:
        incompleto.append("artefactos de mas de un commit (dos pipelines): %s" % commits)
    faltan = [j for j in esperados if j not in salidas]
    if faltan:
        incompleto.append("faltan jobs: %s" % faltan)
    sin_medir = [f["clave"] for f in ped if f.get("estado") != "ok"]
    if sin_medir:
        incompleto.append("%d granulos pedidos sin medir: %s" % (len(sin_medir), sin_medir[:20]))
    for j in esperados:
        s = salidas.get(j)
        if s is not None and not any(g.get("cprima_igual") is not None for g in s.get("granulos", [])):
            incompleto.append("%s sin brazo C'" % j)
    conteo = {b: sum(1 for f in ok if b in (f.get("pub") or {}) and b in (f.get("brazos") or {})) for b in BRAZOS}
    if len(set(conteo.values())) != 1 or conteo["C"] != len(ok):
        incompleto.append("los brazos no tienen la misma cantidad de granulos medidos: %s" % conteo)
        ok = [f for f in ok if all(b in (f.get("pub") or {}) and b in (f.get("brazos") or {}) for b in BRAZOS)]

    # ---- instrumento
    invalido = []
    for j, s in salidas.items():
        if j in esperados and s.get("flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER") is not False:
            invalido.append("%s: la etiqueta no es la de produccion (flag %s)" % (
                j, s.get("flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER")))
    for f in ok:
        if f.get("cprima_igual") is False:
            invalido.append("C' distinto de C en %s" % f["clave"])
        real = (f.get("desplazamiento") or {}).get("km")
        nulos = f.get("nulos") or []
        if len(nulos) != K_NULOS or real is None:
            invalido.append("%s: %d nulos" % (f["clave"], len(nulos)))
            continue
        for x in nulos:
            # dos cosas distintas: el aplicado es el pedido (aritmetica de la traslacion) y el pedido tiene
            # el tamano del corrimiento real (el diseno del nulo)
            if abs(x["km_aplicado"] - x["km"]) > TOL_KM:
                invalido.append("%s: nulo %d aplicado %s km contra %s pedido" % (f["clave"], x["k"], x["km_aplicado"], x["km"]))
            if abs(x["km"] - real) > TOL_KM:
                invalido.append("%s: nulo %d de %s km contra %s del corrimiento real" % (f["clave"], x["k"], x["km"], real))
        difs = sorted((x["angulo_grados"] - nulos[0]["angulo_grados"]) % 360.0 for x in nulos)
        if any(abs(b - a - 360.0 / K_NULOS) > TOL_RUMBO for a, b in zip(difs[:-1], difs[1:])):
            invalido.append("%s: rumbos no equiespaciados" % f["clave"])
        llam_c = (f["brazos"]["C"] or {}).get("test1_llamadas")
        for b in BRAZOS:
            if f["brazos"][b] is not None and (f["brazos"][b].get("test1_llamadas") or 0) != (llam_c or 0) \
                    and f["brazos"]["C"] is not None:
                invalido.append("%s: el espia del Test 1 vio %s llamadas en %s y %s en C" % (
                    f["clave"], f["brazos"][b].get("test1_llamadas"), b, llam_c))

    # ---- regla 1 y regla 2: M contra C y cada nulo contra C (evaluador de la 1.21, sin tocar)
    comp_M = E21.comparar("M", "C", ok, pob, vols)
    comp_N = {b: E21.comparar(b, "C", ok, pob, vols) for b in NULOS}
    prot = [f for f in ok if f["prot"]]
    perd = {b: c["regla1"]["perdidas"] for b, c in comp_N.items()}
    gan = {b: c["regla1"]["ganadas"] for b, c in comp_N.items()}
    regla1 = {
        "letra": "PIERDE PROTEGIDA" if comp_M["regla1"]["perdidas"] > 0 else "NO PIERDE",
        "M_pierde_lo_que_C_publica": [x["clave"] for x in comp_M["regla1"]["perdidas_detalle"]],
        "C_pierde_lo_que_M_publica": [f["clave"] for f in prot if f["pub"]["M"] == 1 and f["pub"]["C"] == 0],
        "publica_C": sum(f["pub"]["C"] for f in prot), "publica_M": sum(f["pub"]["M"] for f in prot),
        "de": len(prot),
        "perdidas": lectura_rango(comp_M["regla1"]["perdidas"], list(perd.values()),
                                  "PERDIDAS ESPECIFICAS DE MXD03", "MENOS PERDIDAS QUE EL AZAR", "PERDIDAS COMO EL AZAR"),
        "ganadas": lectura_rango(comp_M["regla1"]["ganadas"], list(gan.values()),
                                 "GANANCIAS ESPECIFICAS DE MXD03", "MENOS GANANCIAS QUE EL AZAR", "GANANCIAS COMO EL AZAR"),
        "neto": lectura_rango(comp_M["regla1"]["ganadas"] - comp_M["regla1"]["perdidas"],
                              [gan[b] - perd[b] for b in NULOS],
                              "NETO MEJOR QUE EL AZAR", "NETO PEOR QUE EL AZAR", "NETO COMO EL AZAR"),
        # fragilidad por pasada: de los nulos, cuantos pierden (o ganan) cada protegida
        "por_pasada": [{"clave": f["clave"], "datetime_utc": f["datetime_utc"], "vrp_ref": f.get("vrp_ref"),
                        "pub_C": f["pub"]["C"], "pub_M": f["pub"]["M"],
                        "nulos_que_publican": sum(f["pub"][b] for b in NULOS)} for f in prot],
    }
    balance = {"M": comp_M["regla2"], "veredicto_M_contra_C": comp_M["veredicto"],
               "rango": lectura_rango(comp_M["regla2"]["delta"], [c["regla2"]["delta"] for c in comp_N.values()],
                                      "BALANCE PEOR QUE EL AZAR", "BALANCE MEJOR QUE EL AZAR", "BALANCE COMO EL AZAR")}

    varas = {}
    if tabla_vara:
        varas["principal"] = vara(ok, tabla_vara, "pico", "estricta", "pos")
        varas["pico_centro_estricta_pos"] = vara(ok, tabla_vara, "pico_centro", "estricta", "pos")
        varas["pico_estricta_todos"] = vara(ok, tabla_vara, "pico", "estricta", "todos")
        varas["cumulo_estricta_pos"] = vara(ok, tabla_vara, "cumulo", "estricta", "pos")
        varas["pico_amplia_todos"] = vara(ok, tabla_vara, "pico", "amplia", "todos")

    if invalido:
        ver = "INVALIDO"
    elif incompleto:
        ver = "INCOMPLETO"
    else:
        ver = "MEDIDO"
    return {"veredicto": ver, "adoptable_en_la_replica": ver == "MEDIDO" and regla1["letra"] == "NO PIERDE"
            and comp_M["veredicto"] == "MEJORA",
            "motivos_invalido": invalido[:50], "motivos_incompleto": incompleto,
            "commits": [c for c in commits if c != "None"], "conteo_por_brazo": conteo,
            "ausentes_del_archivo": len([a for a in ausentes if a["volcan"] in vols]),
            "regla1": regla1, "balance_regla2": balance,
            "vara": varas, "test1": test1_lectura(ok) if ok else None, "borde": borde_lectura(ok) if ok else None,
            "tamano_del_nulo": tamano_del_nulo(ok) if ok else None,
            "M_contra_C_completo": {k: comp_M[k] for k in ("veredicto", "regla1", "tipos_de_cambio", "cortes")},
            "c_igual_a_guardada": {"si": sum(1 for f in ok if f.get("c_igual_a_guardada")), "de": len(ok)}}


def comparar_con_121(ok_123, carpeta_121):
    """Anotacion: C y M de la 1.23 contra los de la 1.21 (mismo L1B; difieren solo por deriva de codigo)."""
    viejo = {}
    for p in Path(carpeta_121).rglob("*.json"):
        d = _cargar(p)
        if isinstance(d, dict) and "granulos" in d and "brazos" in d:
            for g in d["granulos"]:
                if g.get("estado") == "ok":
                    viejo[(d["volcan"], g["clave"])] = g
    dif = {"C": [], "M": []}
    for f in ok_123:
        g = viejo.get((f["volcan"], f["clave"]))
        if g is None:
            continue
        for b in ("C", "M"):
            if g["pub"][b] != f["pub"][b] or (g["brazos"][b] or {}).get("dc") != (f["brazos"][b] or {}).get("dc"):
                dif[b].append(f["clave"])
    return {b: {"n": len(v), "claves": v[:30]} for b, v in dif.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--poblacion", default=str(J.POBLACION))
    ap.add_argument("--archivo", default=str(DIR_121 / "archivo_cmr.json"))
    ap.add_argument("--vara", default=str(AQUI / "vara_viirs.json"))
    ap.add_argument("--jobs", default=None)
    ap.add_argument("--art121", default=None, help="artefactos de la 1.21 para la anotacion de reproduccion")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    from calidad_referencia_mirova import avisar
    pob = _cargar(a.poblacion)
    avisar(*pob["meta"]["ventana"])
    salidas = {}
    for p in sorted(Path(a.carpeta).rglob("*.json")):
        d = _cargar(p)
        if isinstance(d, dict) and "granulos" in d and "job" in d and "k_nulos" in d:
            salidas[d["job"]] = d
    if not salidas:
        sys.exit("no encontre salidas del probe en %s" % a.carpeta)
    r = evaluar(pob, salidas, _cargar(a.archivo)["ausentes"], json.loads(a.jobs) if a.jobs else None,
                _cargar(a.vara))
    if a.art121:
        ok = [f for f in _unir(pob, salidas) if f.get("estado") == "ok"]
        r["reproduce_la_121"] = comparar_con_121(ok, a.art121)
    texto = json.dumps(r, indent=1, ensure_ascii=False)
    if a.salida:
        Path(a.salida).write_text(texto, encoding="utf-8")
    print("VEREDICTO:", r["veredicto"], "| adoptable:", r["adoptable_en_la_replica"],
          "| invalido:", r["motivos_invalido"][:3] or "-", "| incompleto:", r["motivos_incompleto"] or "-")
    g = r["regla1"]
    print("  regla 1 (letra): %s | M pierde %d, gana %d de %d | perdidas: %s (p alta %s) | ganadas: %s (p alta %s)" % (
        g["letra"], len(g["M_pierde_lo_que_C_publica"]), len(g["C_pierde_lo_que_M_publica"]), g["de"],
        g["perdidas"]["estado"], g["perdidas"].get("p_alta"), g["ganadas"]["estado"], g["ganadas"].get("p_alta")))
    b = r["balance_regla2"]
    print("  regla 2: delta M %s %s (%s) | contra el azar: %s" % (b["M"]["delta"], b["M"]["intervalo"],
                                                               b["veredicto_M_contra_C"], b["rango"]["estado"]))
    for k, v in r["vara"].items():
        print("  vara %-22s %-34s n=%s dd=%s %s lambda=%s" % (k, v.get("estado"), v.get("n"), v.get("dd_mediana_km"),
                                                          v.get("dd_ic95"), v.get("lambda_mediana")))
    if r["test1"]:
        print("  test 1: %s | con signo: %s" % (r["test1"]["cruces"]["estado"], r["test1"]["con_signo"]["estado"]))
    if r["borde"]:
        print("  borde (50-90): %s" % (r["borde"].get("50-90") or {}).get("estado"))


if __name__ == "__main__":
    main()
