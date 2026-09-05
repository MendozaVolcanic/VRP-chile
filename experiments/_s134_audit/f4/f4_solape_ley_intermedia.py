# -*- coding: utf-8 -*-
"""S134 - F4: el solape del barrido VIIRS y la ley de area intermedia.

FICHA SDA (Resolucion CPLT N.372)
================================
Rol       : medicion off-line, READ-ONLY. No participa de la deteccion NRT, no escribe
            en `data/`, no toca `pipeline/`. Es una AUDITORIA, no una adopcion.
Entradas  : ~/ab_area/s133area-_s133_area_{control,geoloc,corona}-<Vol>/<Vol>.json
            (artefactos del A/B de S133, ventana 2026-04-01 -> 2026-05-31, VIIRS375)
            ground truth MIROVA CONS union OCR del repo principal (solo lectura).
Salida    : experiments/_s134_audit/f4/resultados.json  (regla S91: los numeros que se
            citen despues salen de ahi y no de esta consola).

EL FENOMENO, primero
====================
El VRP de un pixel es radiancia x AREA x coeficiente. Hacia el borde del barrido el
pixel de VIIRS cubre mas terreno, asi que la misma anomalia sub-pixel diluye su
radiancia y, con area nadir fija, la magnitud sale corta: S133 midio razon contra
MIROVA 0,879 en el nadir y 0,619 en el borde. Usar el area MEDIDA en la geolocalizacion
corrige el gradiente pero se pasa: 0,958 y 1,360.

La hipotesis de por que se pasa es geometrica y es del instrumento, no del codigo. El
espejo de VIIRS barre una franja de 32 filas I-band que en el terreno mide 11,87 km a lo
largo de la orbita en el nadir y 25,60 km en el borde del barrido (ATBD de
geolocalizacion 423-ATBD-002, seccion 3.4.2.1, pag. 95). Pero el satelite AVANZA lo
mismo entre barrido y barrido -11,87 km- porque eso lo fija la orbita y el periodo de
barrido, no el angulo. O sea que hacia el borde cada barrido vuelve a mirar terreno que
el barrido anterior ya miro: es el efecto "bow tie", y el mismo ATBD lo cuantifica en
"maximum overlap over 50 percent at 56.063 degrees".

Consecuencia para la magnitud: un foco caliente en el borde del barrido aparece en
pixeles de DOS barridos, y al sumar el cumulo se cuenta su energia dos veces. El area
geolocalizada -que es el producto de las distancias entre centros vecinos- describe
correctamente el terreno que el detector integra, pero NO descuenta esa duplicacion.
De ahi la prediccion: la ley correcta esta ENTRE el area nadir fija y el area
geolocalizada completa.

LA DERIVACION DE f(theta), con las citas
========================================
Todo lo que sigue esta leido en los PDF de `documentacion/`, no de memoria:

  (G1) Tamano del pixel I-band, tabla 2.2-1 pag. 13 del ATBD de geolocalizacion:
       nadir 0,371 km (a lo largo del vuelo) x 0,388 km (a lo ancho del barrido);
       fin de barrido 0,80 x 0,789 km.
  (G2) Extension de UN barrido a lo largo del vuelo, seccion 3.4.2.1 pag. 95:
       "from 11.87 kilometers at nadir to 25.60 kilometers at a scan angle of 56.063
       degrees". Coherente con (G1): 32 x 0,371 = 11,87 y 32 x 0,80 = 25,60.
  (G3) El solape es a lo largo del vuelo y NO lo toca la agregacion:
       "This overlap is unaffected by the VIIRS pixel aggregation strategy which
       applies only in the cross-track direction" (misma pag. 95). Por eso el descuento
       va en un solo eje.
  (G4) Zonas de agregacion, seccion 2.2.1 pag. 12 y 3.3.2.1.2:
       3:1 hasta 31,589 grados de angulo de barrido, 2:1 hasta 44,680, 1:1 hasta 56,063.
  (G5) Borrado bow-tie, JPSS ATBD VIIRS Imagery RevE seccion 3.2.4 pag. 22-23, VERBATIM:
       "deleting 4 of the 32 detectors from the output data steam for the middle
       (Aggregate 2) part of the scan and 8 of the 32 detectors for the edge (No
       aggregation) part of the scan". O sea que de las 32 filas del barrido llegan al
       suelo 32, 28 y 24 segun la zona. Ese borrado YA quita parte del solape, y por eso
       entra en la derivacion en vez de ignorarse.

Con eso, la fraccion de terreno NUEVO que aporta un barrido en el angulo theta:

    D(theta) = 11,87 km * r(theta) * k(theta)/32      (extension entregada)
    f(theta) = min(1, 11,87 / D(theta)) = min(1, 32 / (k(theta) * r(theta)))

donde k = 32 / 28 / 24 segun la zona (G5) y r(theta) es el crecimiento del pixel a lo
largo del vuelo, que es el cociente de distancia oblicua: r = S(theta)/S(0). No hay
sec(zenital) en este eje -el eje de vuelo es perpendicular al plano de barrido y no se
proyecta-, y eso es justamente lo que explica que a lo largo del vuelo el pixel crezca
2,16x mientras a lo ancho creceria 6x sin agregacion (ATBD pag. 12).

SIMPLIFICACIONES, declaradas
============================
  · S1. f se aplica como factor MULTIPLICATIVO a la magnitud publicada del record. Es
        exacto si todos los pixeles del cumulo comparten angulo y zona; para un cumulo
        de pocos pixeles la variacion de angulo dentro del cumulo es despreciable, pero
        NO es exacto y por eso se dice. El area por pixel no esta persistida en los JSON
        del brazo geoloc (verificado: las claves del record no la traen), asi que el
        factor es la unica via sin volver a bajar granules -y bajar granules esta
        prohibido en esta sesion.
  · S2. La altura efectiva H se CALIBRA para que r(56,063) reproduzca exactamente el
        25,60/11,87 = 2,1567 del ATBD, en vez de fijar un valor de orbita de memoria.
        Se reporta ademas la version con H = 829 km nominal como sensibilidad.
  · S3. El record trae `sensor_zenith_deg`, que es el angulo cenital en la SUPERFICIE,
        no el angulo de barrido. Se convierte con sin(theta) = Re/(Re+H) * sin(zenital).
  · S4. El ATBD dice en la seccion 2.2.2 que el solape empieza "a partir de unos 19
        grados", mientras que esta derivacion lo hace empezar en cuanto theta > 0. La
        tension esta declarada y no se resuelve aca: hace que f sea una cota INFERIOR
        del terreno nuevo cerca del nadir, o sea que si esta mal, esta mal en el sentido
        de tocar de mas el bin del nadir. El control negativo de abajo lo vigila.

LAS DOS PREGUNTAS DEL INSTRUMENTO
=================================
  1. Si lo que mido estuviera completamente roto, esta medicion lo veria?
     Si. El objeto medido es la razon contra MIROVA por pasada. Si la ley de area no
     hiciera nada, las tres columnas darian identicas; si f estuviera invertido, el bin
     del borde subiria en vez de bajar. Ambas cosas serian visibles en la tabla.
  2. Si el instrumento mismo estuviera muerto, el resultado se veria distinto?
     Si, y se comprueba con dos controles que corren SIEMPRE y abortan si fallan:
       · CONTROL POSITIVO: reproducir los numeros publicados de S133 (control 0,879 /
         0,619; geoloc 0,958 / 1,360) ANTES de aplicar f. Si no se reproducen, el
         instrumento esta mal y el resto no vale.
       · CONTROL NEGATIVO: f ~ 1 en el nadir. Si f mueve el bin del nadir mas de 3 %,
         la derivacion esta mal.
     Ademas cada bin declara su n; un bin con n < MIN_N se marca "no evaluable" y NO se
     cuenta como cero: SIN DATO no es lo mismo que FALLA ni que OK.

CRITERIO PRE-REGISTRADO (congelado ANTES de correr, no se mueve el poste)
=========================================================================
El mismo de S132/S133, sobre el brazo geoloc x f(theta):
  (C1) los dos bins juzgados -0-15 grados y 50+ grados de cenital- con razon MEDIANA
       entre 0,90 y 1,10;
  (C4) pares con razon > 2 en <= 10 %.
Si no se cumple, se reporta el incumplimiento tal cual. Si se cumple, es una PROPUESTA
de A/B para S135 con tag defensivo y confirmacion de Nicolas (A45), NUNCA una adopcion:
este script no escribe en `pipeline/` ni en ningun perfil.

USO
===
    python experiments/_s134_audit/f4/f4_solape_ley_intermedia.py
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
# El worktree de S134 es sparse: no tiene `data/` ni `documentacion/`. El ground truth
# se lee por ruta absoluta del repo principal, SOLO LECTURA.
REPO_PPAL = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
WORKTREE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(WORKTREE, "experiments"))
from _s126_lib import ALIAS, SENSOR_MAP, bucket  # noqa: E402

AB_DIR = os.path.expanduser("~/ab_area")
BRAZOS = ["_s133_area_control", "_s133_area_geoloc", "_s133_area_corona"]
VOLCANES = ["Lascar", "Isluga", "Lastarria", "PuyehueCordonCaulle",
            "PlanchonPeteroa", "Tupungatito", "Chaiten", "Villarrica"]
FUENTES_GT = (os.path.join(REPO_PPAL, "latest_consolidado.csv"),
              os.path.join(REPO_PPAL, "data", "mirova_reference", "mirova_v1_snapshot",
                           "registro_vrp_ocr.csv"))

BANDA = (0.90, 1.10)
RAZON_COLA = 2.0
FRACCION_COLA_MAX = 0.10
MIN_N = 15
BINS = ("0-15", "15-25", "25-35", "35-50", "50+")
BINS_JUZGADOS = ("0-15", "50+")
TOL = timedelta(minutes=20)
HORAS_NOCHE = (3, 9)
N_BOOTSTRAP = 5000
SEMILLA = 20260905

# Numeros publicados por S133 que el control positivo tiene que reproducir.
S133_PUBLICADO = {"_s133_area_control": {"0-15": 0.879, "50+": 0.619, "cola": 0.042},
                  "_s133_area_geoloc": {"0-15": 0.958, "50+": 1.360, "cola": 0.201},
                  "_s133_area_corona": {"50+": 1.303}}
TOL_CONTROL_POSITIVO = 0.005     # las medianas vienen redondeadas a 3 decimales
TOL_CONTROL_NEGATIVO = 0.03      # f no puede mover el bin del nadir mas de 3 %

SALIDA = os.path.join(HERE, "resultados.json")

# ══════════════════════════ la geometria del ATBD ══════════════════════════

RE_KM = 6371.0                    # radio terrestre medio
W_NADIR_KM = 11.87                # (G2) extension del barrido a lo largo del vuelo
W_EOS_KM = 25.60                  # (G2) idem en el borde
THETA_EOS_DEG = 56.063            # (G4) angulo de barrido maximo
ZONA_1_2_DEG = 31.589             # (G4) frontera 3:1 -> 2:1
ZONA_2_3_DEG = 44.680             # (G4) frontera 2:1 -> 1:1
FILAS_POR_ZONA = (32, 28, 24)     # (G5) filas I-band entregadas por zona
H_NOMINAL_KM = 829.0              # altura nominal SNPP, solo como sensibilidad (S2)


def _slant_km(theta_deg, h_km):
    """Distancia oblicua sensor-superficie para un angulo de barrido theta."""
    t = math.radians(theta_deg)
    rh = RE_KM + h_km
    disc = RE_KM ** 2 - (rh * math.sin(t)) ** 2
    if disc <= 0:
        return float("nan")
    return rh * math.cos(t) - math.sqrt(disc)


def _calibrar_h():
    """Altura efectiva que reproduce el 25,60/11,87 del ATBD (S2). Biseccion."""
    objetivo = W_EOS_KM / W_NADIR_KM
    lo, hi = 700.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        r = _slant_km(THETA_EOS_DEG, mid) / mid
        if r > objetivo:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


H_EFECTIVA_KM = _calibrar_h()


def theta_de_zenital(zen_deg, h_km):
    """Angulo de barrido a partir del cenital de superficie (S3)."""
    s = (RE_KM / (RE_KM + h_km)) * math.sin(math.radians(abs(float(zen_deg))))
    s = max(-1.0, min(1.0, s))
    return min(math.degrees(math.asin(s)), THETA_EOS_DEG)


def filas_entregadas(theta_deg):
    """Filas I-band que sobreviven al borrado bow-tie en ese angulo (G5)."""
    if theta_deg < ZONA_1_2_DEG:
        return FILAS_POR_ZONA[0]
    if theta_deg < ZONA_2_3_DEG:
        return FILAS_POR_ZONA[1]
    return FILAS_POR_ZONA[2]


def f_solape(zen_deg, h_km=None):
    """Fraccion del area entregada que corresponde a terreno NUEVO.

    f = min(1, 32 / (k * r)); r = S(theta)/S(0) es el crecimiento del pixel a lo largo
    del vuelo y k las filas entregadas. f = 1 significa "no hay duplicacion".
    """
    h = H_EFECTIVA_KM if h_km is None else h_km
    th = theta_de_zenital(zen_deg, h)
    r = _slant_km(th, h) / h
    k = filas_entregadas(th)
    return min(1.0, 32.0 / (k * r)), th, r, k


# ══════════════════════════ utilidades numericas ══════════════════════════

def _es_finito(x):
    if x is None or isinstance(x, bool):
        return False
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v)


def _f(x):
    return float(x) if _es_finito(x) else None


def _mediana(xs):
    ys = sorted(float(x) for x in xs if _es_finito(x))
    if not ys:
        return None
    m = len(ys) // 2
    return ys[m] if len(ys) % 2 else (ys[m - 1] + ys[m]) / 2.0


def _ic_bootstrap(xs, n=N_BOOTSTRAP):
    """IC 95 % de la MEDIANA por bootstrap con semilla fija (reproducible)."""
    ys = [float(x) for x in xs if _es_finito(x)]
    if len(ys) < 3:
        return None
    rng = random.Random(SEMILLA)
    meds = []
    k = len(ys)
    for _ in range(n):
        meds.append(_mediana([ys[rng.randrange(k)] for _ in range(k)]))
    meds.sort()
    return [meds[int(0.025 * n)], meds[int(0.975 * n) - 1]]


def _parse_dt(s):
    s = (s or "").replace("T", " ").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _bin_de(zen):
    z = abs(float(zen))
    return ("0-15" if z < 15 else "15-25" if z < 25 else
            "25-35" if z < 35 else "35-50" if z < 50 else "50+")


def magnitud_publicada(rec):
    """La magnitud que ve el operador (A10 + matiz S132 para VIIRS375)."""
    pc = rec.get("primary_cluster") or {}
    v_pc = _f(pc.get("vrp_mw"))
    if bucket(rec.get("sensor")) != "v375":
        return v_pc, "primary_cluster.vrp_mw"
    v_f5 = _f(rec.get("f5_core_vrp_mw"))
    if v_f5 is not None:
        return v_f5, "f5_core_vrp_mw"
    return v_pc, "primary_cluster.vrp_mw (fallback A46)"


# ══════════════════════════ carga ══════════════════════════

def _ruta(brazo, vol):
    return os.path.join(AB_DIR, "s133area-%s-%s" % (brazo, vol), vol + ".json")


def cargar_brazo(brazo, vol):
    with io.open(_ruta(brazo, vol), encoding="utf-8") as fh:
        doc = json.load(fh)
    recs = doc["records"] if isinstance(doc, dict) else doc
    out = {}
    for r in recs:
        if bucket(r.get("sensor")) != "v375":
            continue
        g = r.get("granule")
        if g and g not in out:
            out[g] = r
    return out


def cargar_gt():
    out = defaultdict(list)
    n = 0
    for path in FUENTES_GT:
        if not os.path.exists(path):
            raise SystemExit("falta el ground truth: " + path)
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                nom = (r.get("Volcan") or "").strip()
                vol = next((v for v, al in ALIAS.items() if nom in al), None)
                if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                    continue
                bk = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
                if not bk:
                    continue
                try:
                    vrp = float(r.get("VRP_MW") or 0)
                    d = datetime.strptime((r.get("Fecha_Satelite_UTC") or "")[:19],
                                          "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if vrp <= 0 or not (HORAS_NOCHE[0] <= d.hour <= HORAS_NOCHE[1]):
                    continue
                out[(vol, bk)].append((d, vrp))
                n += 1
    return out, n


def _mirova_de(gt, vol, dt):
    if dt is None:
        return None
    c = [(abs(d - dt), v) for d, v in gt.get((vol, "v375"), ()) if abs(d - dt) <= TOL]
    return min(c)[1] if c else None


def pares_de(brazo, gt):
    """Pares por PASADA contra MIROVA, con f(theta) calculado para cada uno."""
    pares = []
    diag = defaultdict(int)
    for vol in VOLCANES:
        for g, r in cargar_brazo(brazo, vol).items():
            diag["n_records"] += 1
            mw, fuente = magnitud_publicada(r)
            if mw is None or mw <= 0:
                diag["sin_magnitud"] += 1
                continue
            zen = r.get("sensor_zenith_deg")
            if not _es_finito(zen):
                diag["sin_zenith"] += 1
                continue
            m = _mirova_de(gt, vol, _parse_dt(r.get("datetime_utc")))
            if m is None:
                diag["sin_alerta_mirova"] += 1
                continue
            fac, th, rr, k = f_solape(zen)
            fac_nom, _, _, _ = f_solape(zen, H_NOMINAL_KM)
            pares.append({
                "volcano": vol, "granule": g, "datetime_utc": r.get("datetime_utc"),
                "zenital_deg": float(zen), "bin": _bin_de(zen),
                "theta_barrido_deg": th, "r_crecimiento_track": rr, "filas_entregadas": k,
                "f_solape": fac, "f_solape_h_nominal": fac_nom,
                "vrp_ours_mw": mw, "fuente_magnitud": fuente, "vrp_mirova_mw": m,
                "razon": mw / m, "razon_x_f": (mw * fac) / m,
                "razon_x_f_h_nominal": (mw * fac_nom) / m,
            })
    return pares, dict(diag)


# ══════════════════════════ resumen por bin ══════════════════════════

def por_bin(pares, campo):
    out = {}
    for b in BINS:
        rs = [p[campo] for p in pares if p["bin"] == b]
        med = _mediana(rs)
        evaluable = len(rs) >= MIN_N
        out[b] = {
            "n_pares": len(rs),
            "mediana_razon": med,
            "ic95_bootstrap": _ic_bootstrap(rs) if evaluable else None,
            "evaluable": evaluable,
            "en_banda": (BANDA[0] <= med <= BANDA[1]) if (evaluable and med) else None,
            "f_solape_mediano": _mediana([p["f_solape"] for p in pares if p["bin"] == b]),
        }
    return out


def cola(pares, campo):
    rs = [p[campo] for p in pares]
    n = len(rs)
    c = sum(1 for r in rs if r > RAZON_COLA)
    return {"n_pares": n, "n_sobre_2": c,
            "fraccion": (c / float(n)) if n else None,
            "pasa": bool(n and (c / float(n)) <= FRACCION_COLA_MAX)}


def main():
    gt, n_gt = cargar_gt()
    faltan = [_ruta(b, v) for b in BRAZOS for v in VOLCANES if not os.path.exists(_ruta(b, v))]
    if faltan:
        print("Faltan JSON de brazos:", len(faltan))
        for p in faltan[:5]:
            print("  -", p)
        return 2

    leyes, pares_por_brazo = {}, {}
    for b in BRAZOS:
        pares, diag = pares_de(b, gt)
        pares_por_brazo[b] = pares
        leyes[b] = {"n_pares": len(pares), "diagnostico": diag,
                    "por_bin": por_bin(pares, "razon"), "cola": cola(pares, "razon")}

    pg = pares_por_brazo["_s133_area_geoloc"]
    leyes["geoloc_x_f_solape"] = {
        "n_pares": len(pg),
        "por_bin": por_bin(pg, "razon_x_f"), "cola": cola(pg, "razon_x_f"),
        "_que_es": "brazo geoloc con la magnitud multiplicada por f(theta) del ATBD",
    }
    leyes["geoloc_x_f_solape_H_nominal_829km"] = {
        "n_pares": len(pg),
        "por_bin": por_bin(pg, "razon_x_f_h_nominal"),
        "cola": cola(pg, "razon_x_f_h_nominal"),
        "_que_es": "sensibilidad S2: misma ley con H = 829 km en vez de la calibrada",
    }

    # ── CONTROL POSITIVO: reproducir S133 antes de creerle nada a f ──
    cp = {"tolerancia": TOL_CONTROL_POSITIVO, "detalle": {}, "pasa": True}
    for b, esp in S133_PUBLICADO.items():
        for clave, val in esp.items():
            obs = (leyes[b]["cola"]["fraccion"] if clave == "cola"
                   else leyes[b]["por_bin"][clave]["mediana_razon"])
            ok = obs is not None and abs(obs - val) <= TOL_CONTROL_POSITIVO
            cp["detalle"]["%s|%s" % (b, clave)] = {
                "publicado_S133": val, "reproducido": obs, "ok": bool(ok)}
            cp["pasa"] = cp["pasa"] and ok

    # ── CONTROL NEGATIVO: f no puede mover el bin del nadir mas de 3 % ──
    a = leyes["_s133_area_geoloc"]["por_bin"]["0-15"]["mediana_razon"]
    z = leyes["geoloc_x_f_solape"]["por_bin"]["0-15"]["mediana_razon"]
    cn = {"tolerancia_relativa": TOL_CONTROL_NEGATIVO,
          "mediana_nadir_geoloc": a, "mediana_nadir_geoloc_x_f": z,
          "cambio_relativo": (abs(z - a) / a) if (a and z) else None,
          "pasa": bool(a and z and abs(z - a) / a <= TOL_CONTROL_NEGATIVO)}

    pb = leyes["geoloc_x_f_solape"]["por_bin"]
    c1 = all(pb[b]["evaluable"] and pb[b]["en_banda"] for b in BINS_JUZGADOS)
    ver = {"C1_los_dos_bins_en_banda": bool(c1),
           "C4_cola_menor_10pct": leyes["geoloc_x_f_solape"]["cola"]["pasa"],
           "pasa_el_criterio_preregistrado":
               bool(c1 and leyes["geoloc_x_f_solape"]["cola"]["pasa"])}

    out = {
        "_que_es": ("S134 F4 - el solape del barrido VIIRS y la ley de area intermedia. "
                    "AUDITORIA read-only; no adopta nada (A45)."),
        "_ventana_utc": {"desde": min(p["datetime_utc"] for p in pg),
                         "hasta": max(p["datetime_utc"] for p in pg)},
        "_denominador": ("pares POR PASADA contra ALERTA nocturna de MIROVA (<=20 min, "
                         "CONS union OCR), VIIRS375, 8 volcanes"),
        "_volcanes": VOLCANES,
        "_ground_truth": {"n_filas_alerta_nocturnas": n_gt,
                          "fuentes": list(FUENTES_GT)},
        "_criterio_preregistrado": {
            "C1": "los bins 0-15 y 50+ con mediana en [0,90 , 1,10]",
            "C4": "pares con razon > 2 en <= 10 %",
            "min_n_por_bin": MIN_N,
            "congelado_antes_de_correr": True},
        "geometria_atbd": {
            "fuentes": [
                "VIIRS_Geolocation_ATBD_2014.pdf (423-ATBD-002): tabla 2.2-1 pag.13; "
                "sec. 2.2.2 pag.19; sec. 3.4.2.1 pag.95; sec. 2.2.1/3.3.2.1.2 zonas",
                "JPSS_ATBD_VIIRS_Imagery_RevE.pdf sec. 3.2.4 pag.22-23 (borrado bow-tie)"],
            "extension_barrido_nadir_km": W_NADIR_KM,
            "extension_barrido_eos_km": W_EOS_KM,
            "avance_por_barrido_km": W_NADIR_KM,
            "theta_eos_deg": THETA_EOS_DEG,
            "fronteras_zona_deg": [ZONA_1_2_DEG, ZONA_2_3_DEG],
            "filas_I_band_entregadas_por_zona": list(FILAS_POR_ZONA),
            "H_efectiva_calibrada_km": H_EFECTIVA_KM,
            "H_nominal_sensibilidad_km": H_NOMINAL_KM,
            "f_en_angulos_notables": {
                ("zenital_%d" % z): dict(zip(
                    ("f", "theta_barrido_deg", "r_crecimiento", "filas"), f_solape(z)))
                for z in (0, 10, 20, 30, 40, 50, 55, 60, 65, 70)},
        },
        "control_positivo_reproduce_S133": cp,
        "control_negativo_f_no_toca_el_nadir": cn,
        "leyes": leyes,
        "veredicto": ver,
    }

    with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False))

    print("Escrito:", SALIDA)
    print("H efectiva calibrada: %.1f km" % H_EFECTIVA_KM)
    print("CONTROL POSITIVO (reproduce S133):", cp["pasa"])
    for k, v in cp["detalle"].items():
        print("   %-34s pub=%.3f  obs=%s  %s" % (
            k, v["publicado_S133"],
            "None" if v["reproducido"] is None else "%.3f" % v["reproducido"],
            "OK" if v["ok"] else "DIFIERE"))
    print("CONTROL NEGATIVO (f no toca el nadir):", cn["pasa"],
          "cambio=%.4f" % (cn["cambio_relativo"] or 0))
    print()
    print("%-38s %-22s %-22s %s" % ("ley", "nadir 0-15", "borde 50+", "cola>2"))
    for nom in ("_s133_area_control", "_s133_area_geoloc", "geoloc_x_f_solape",
                "geoloc_x_f_solape_H_nominal_829km"):
        d = leyes[nom]
        cel = []
        for b in BINS_JUZGADOS:
            e = d["por_bin"][b]
            ic = e["ic95_bootstrap"]
            cel.append("n=%3d %.3f [%s]" % (
                e["n_pares"], e["mediana_razon"] or 0,
                "-" if not ic else "%.2f-%.2f" % (ic[0], ic[1])))
        print("%-38s %-22s %-22s %.1f%%" % (nom, cel[0], cel[1],
                                            100 * (d["cola"]["fraccion"] or 0)))
    print()
    print("VEREDICTO contra el criterio pre-registrado:", ver)
    print("Los numeros se citan del JSON, no de esta consola (S91).")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
