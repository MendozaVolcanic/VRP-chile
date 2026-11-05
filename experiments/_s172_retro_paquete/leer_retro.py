# -*- coding: utf-8 -*-
"""Lector de la prueba retrospectiva del paquete de las tres vías «código MIROVA» en los 11 Tier A.

Implementa el pre-registro SELLADO experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md (rama loop/activo, tag
s173-prereg-retro-sellado; sello del 2026-11-02 17:12:17 UTC). Si el texto y este código discrepan, manda el texto:
la discrepancia se corrige aquí con marca fechada, nunca el texto. Plan: docs/superpowers/plans/2026-11-02-nrt-34-
volcanes.md, Tareas 0.2 a 0.5.

POR QUÉ, COMO GEÓLOGO. Un cráter activo de noche ocupa una fracción mínima del píxel. Las vías ven ese calor como lo ve
MIROVA (grilla fija, NTI y ETI contextuales, fondo bajo un halo, suma de las celdas alertadas). Dentro de muestra se
equivocan menos que K. La sospecha a refutar es que las reglas se ajustaron a la estación en que se eligieron (otoño a
primavera, cumbres nevadas, A69): febrero y marzo de 2026 son verano y 2025 trae las cuatro estaciones.

QUÉ REUSA SIN REESCRIBIR (cada archivo se identifica por sha256 con fin de línea LF ANTES de importarlo, §11):
  * MODIS: `reglas/evaluar_f4.py`, copia byte a byte del tag s170-modd-f4-candado (blob d78139e6): p1, p1b, p2, P2'
    (lejana), m y la tabla del §7 de MOD-D fase 4 (`veredicto`), sobre el brazo VIA-radiante (§5.1). Sus piezas
    estadísticas vienen de evaluar_d25.py blob 1dbabf65 (D-45 regla_signos_p2, D-27 regla_m, D-28 comparar_con_ganancia).
  * VIIRS 375: `experiments/_s162_v375/evaluar.py` (sha256 LF 2126b743, el del §11) para P2, lecturas y silencio, y
    `reglas/leer_posicion_v375e.py`, copia del tag s170-v375e-lector (blob 4100cfc1), para `criterios_retro` (§9.7 de
    V375-E), `no_veta_n3` (N-3), `p2_con`/`err_pos` (P2-L) y `magnitud` (M, con scripts/evaluador_comun.py).
  * VIIRS 750: §6 punto 2 de V750-A (texto de aa5583646, §6 l. 217 a 243; NO sellado) con las piezas de MOD-D (P1, P2
    con regla_signos_p2 de D-45 como pide el §5.6 del pre-registro, razón en protegidas y M de D-28 para el
    comparador). Si V750-A no está sellado antes de D2, el techo de VIIRS 750 es DECIDE NICOLÁS (§5.1, R-12).
  * Etiquetas: scripts/banco_paridad.py (indexar_referencia con SN, etiquetar, parear, noche por elevación solar) y
    scripts/clase_mirova.py (alerta_protegida, lectura A), con la referencia unificada de
    scripts/referencia_mirova_unificada.py, como experiments/_s172_prereg_retro/recalcular_s7_ref_congelada.py. Decide
    la tabla sola (source CONS); la unión con el OCR informa (§4.1).
  * «Publica» y la magnitud mostrada: el predicado de frontend/index.html ejecutado con node (A97), por
    evaluar_f4.predicado_node. La curva de cenit: experiments/_s162_v375/curva_cenit.py.

LECTURAS DONDE EL TEXTO NO FIJA EL DETALLE (declaradas antes de ver datos; ninguna cambia un umbral):
  L1. (Nicolás la aprobó tal cual el 2026-11-04, VPR940-07: se mantiene la fila 3.)
      Fila 3 del §8.1 («la regla da NO ADOPTAR o no cumple por P2 PIERDE»): en VIIRS 375 cuenta también P2-L PIERDE y
      el silencio ENCIENDE DE MÁS, que son la misma pregunta (la vía se equivoca más que K) con las lejanas y con la
      tasa en negativos. Cualquier otro «no cumple» del §9.7 de V375-E que no esté en las filas 2 o 3 va a la fila 4
      (lo no previsto pasa a Nicolás, como en el propio §9.7).
  L2. La caja de VIIRS 750 que elegirá V750-B no tiene valor por defecto (`--caja-v750` obligatorio para leer VIIRS
      750): cada record de la vía de 750 tiene que traer `diag_codigo_mirova.roi` igual a esa caja (parte de
      C-montaje). Sin caja declarada, VIIRS 750 queda INDECIDIBLE (CONTROLES).
  L3. C-montaje necesita los records de los A/B de MOD-D fase 4, V375-E y V750-B en DM, que viven en otros tags y
      formatos: este lector recibe su resultado como JSON externo (`--montaje`) y queda rojo sin él.
  L4. Las protegidas sólo del OCR de Suomi NPP anteriores al 2026-10-09 (N-3) se informan y no llevan a la fila 4 en
      VIIRS 375 ni en 750 (V375-E §8.13, V750-A §6 ter). En MODIS no aplica.
  L5. El corte por cenit bajo y sobre 30° (pedido del encargo de S173) se informa al lado de los tramos de 10° del
      §5.3 y no decide nada.

ARREGLOS DEL VERIFICADOR LIMPIO DE #940 (Fable 5.1, MERGEABLE CON CAMBIOS, 2026-11-03; informe en
experiments/_s173_aud/ver940/INFORME.md de la rama loop/activo, commit 6e3af852e): VPR940-02 (c_k_puro: K de disco
con la marca de la vía es rojo en todas las ventanas), 03 (C-K exige la cobertura del K-gemelo que manda D3), 04 (el
nulo de runner descuenta las excepciones nombradas), 05 (el placebo mira P1 y P2, con las dos causas de L7), 06
(C-montaje validado), 09 (C-cobertura en R25 por clase del OSF), 11 (sorteo de etiquetas por estrato, §7, informa) y 15
(ENSAYO en cada línea).

LECTURAS APROBADAS POR NICOLÁS (S173, con la recomendación del coordinador; marca A113 sobre el texto del lector, el
pre-registro no cambia):
  VPR940-01. En VIIRS 750 «el comparador separa la vía de K×1,2» es un CONTROL del placebo (§6 PLACEBO), no parte de
      M: si falla, INDECIDIBLE (fila 1). Qué es «separar» lo fija V750-A cuando se selle; hasta entonces es un
      parámetro (`--separa-v750`, DEFINICIONES_SEPARA_V750) y la única candidata está marcada PROVISIONAL.
  VPR940-07. Se mantiene L1: P2-L PIERDE y ENCIENDE DE MAS van a la fila 3.
  VPR940-10. Un defecto del lector (la vía publica una protegida OSF que K no publica) va a la fila 1, como control.

SEGUNDO VERIFICADOR DE #940 (experiments/_s173_aud/ver940b/ en loop/activo, commit 1f32ef1d1): VPR940b-01 (el sorteo
de etiquetas dice que no tiene poder; cómo leer el §7 lo decide Nicolás), 02 (c_k usa _nombradas), 03 (una excepción de
C-K mal formada es rojo, no traza), 05 (esta cabecera cita el repo), 06 (C-montaje por origen y con pasadas de DM), 07
(volcanes Tier A sin F26 en K y sobras del K-gemelo), 08 (aviso de R25 sin OSF), 10 y 11 (escritos en los docstrings).
VPR940b-04 (`is True` en K) espera a Nicolás y no se tocó.

LAS DOS PREGUNTAS DEL INSTRUMENTO (§6): (1) si la vía no corriera, C-via da 0 %; si el lector estuviera roto, el nulo
del lector (K contra K = 0 diferencias; una protegida quitada a la vía = veto; 50 negativos con un cúmulo de cumbre
inyectado por el predicado = P2 sube en 50) y el placebo lo ven; si K de disco no fuera K de hoy, C-K lo ve. (2) Si los
artefactos estuvieran vacíos, C-cobertura da 0 pasadas contra las de K y C-via sale rojo.

Uso: python leer_retro.py --via DIR --k DIR [--kgemelo DIR] --cons CSV --ocr CSV [--osf CSV] --caja-v750 NOMBRE
     --v750a-sellado {si,no} [--separa-v750 NOMBRE] [--montaje JSON] [--excepciones-ck JSON] [--sin-dato-trozos JSON] [--manifiesto JSON |
     --ensayo] [--salida JSON]
Salida: 0 leído; 3 candado o controles en rojo en algún sensor (el veredicto de ese sensor es INDECIDIBLE).
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
REGLAS = AQUI / "reglas"
for p in (RAIZ, RAIZ / "scripts", RAIZ / "experiments" / "_s162_v375"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ---------------------------------------------------------------- identidad de lo que se reusa (§11)
MANIFIESTO_REGLAS = {
    "experiments/_s172_retro_paquete/reglas/evaluar_f4.py":
        "8a1edc1423a88c86b6796f975ed004d5ca6320a8c56ebf8acee3ea1cc626c30c",   # tag s170-modd-f4-candado
    "experiments/_s172_retro_paquete/reglas/leer_posicion_v375e.py":
        "a40364ab01668db5849b0fb7fb8044bafb4e75f66946132f80aa85373221ce06",   # tag s170-v375e-lector
    "experiments/_s162_v375/evaluar.py": "2126b7439809cc541d3e8c3aec26b09b0b4b02eb562ea716d165a8ab2742bc66",
    "experiments/_s162_v375/curva_cenit.py": "7fdd8e40735b3cf9de068755126b4973fdee79df3182422add82de5a6dd84353",
    "experiments/_s157_prereg_d25/evaluar_d25.py": "2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747",
    "scripts/evaluador_comun.py": "c151b29f51f61171b8fd9f115fff73856058628abf79c95da6df4242969ee5c9",
}

# ---------------------------------------------------------------- constantes del pre-registro
SENSORES = ("MODIS", "VIIRS375", "VIIRS750")
TRAMOS = {  # §3.2: fechas UTC de las pasadas nocturnas
    "F26-V": ("2026-02-01", "2026-03-31", ("VIIRS375", "VIIRS750")),
    "F26-M": ("2026-02-01", "2026-02-28", ("MODIS",)),
    "F26-M3": ("2026-03-01", "2026-03-31", ("MODIS",)),
    "R25": ("2025-02-15", "2025-12-31", SENSORES),
    "DM": ("2026-10-01", "2026-10-16", SENSORES),
}
TRAMO_DECIDE = {"MODIS": "F26-M", "VIIRS375": "F26-V", "VIIRS750": "F26-V"}
DM_SIN_VIIRS = ("2026-10-12", "2026-10-13")
TUPUNGATITO, INICIO_TUPUNGATITO = "Tupungatito", "2026-02-23"
BRAZOS = ("V", "V-cercano", "V-pico")            # VIA-radiante, VIA-cercano, VIA-pico (§2)
REGLA_DE = {"V": "radiante", "V-cercano": "cercano", "V-pico": "pico"}
BRAZO_DE = {v: k for k, v in REGLA_DE.items()}
PLACEBO = 1.2
UMBRAL_SIN_DATO = 0.10                             # §6 C-via y C-cobertura (UMBRAL_COBERTURA de leer_sombra_v375e)
CLASES_QUE_DECIDEN = ("protegida", "bajo1", "neg_limpio")
TOL_VRP_CK = 1e-3                                  # §6 C-K: pc.vrp_mw a 0,001 MW
TOPE_EXCEPCIONES_CK = 3                            # R-15
TOL_CENIT_OSF = 2.0                                # §6 C-cenit
TOPE_TABLERO_MW = 50000.0                          # L7 de V750-A §7: el tope de magnitud de frontend/index.html
T_MAX_FILTROS_K = 278.15                           # L7: bajo esto miran la magnitud los filtros de artefacto del tablero
VOLCANES_F26_ENTEROS_D3 = ("Lascar", "NevadosDeChillan")   # §10.3, D3
TIER_A = ("Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Copahue", "Llaima", "Villarrica", "NevadosDeChillan")   # el de plan_trozos.py (lo vigila una prueba)
DIAS_F26_D3 = 3                                    # §10.3, D3: tres días de F26 de cada otro volcán
TRAMOS_F26 = ("F26-V", "F26-M", "F26-M3")
VENTANA_S = 120
CORTE_CENIT_INFORMA = 30.0                         # L5
HITO_N3 = "2026-10-09"
SEMILLA = 172
N_BARAJADOS = 200
N_INYECTADOS = 50
NOMBRES_FILA = {1: "INDECIDIBLE (CONTROLES)", 2: "NO SE SOSTIENE: PIERDE PROTEGIDA", 3: "NO SE SOSTIENE: PEOR QUE K",
                4: "DECIDE NICOLÁS", 5: "SIN PODER FUERA DE MUESTRA", 6: "NO SE CONTRADICE FUERA DE MUESTRA"}

# §3.1 (b): pasadas miradas por nombre en diagnósticos (volcán, sensor o None = cualquiera, hora UTC)
PASADAS_B = (
    ("Lascar", "MODIS", "2026-02-11 01:20"), ("Lascar", "MODIS", "2026-02-11 07:00"),
    ("Lascar", "MODIS", "2026-02-16 01:20"), ("Lastarria", "MODIS", "2026-02-24 07:05"),
    ("Lascar", "VIIRS750", "2026-02-04 05:54"), ("Lascar", "VIIRS750", "2026-02-05 05:36"),
    ("Lascar", "VIIRS750", "2026-02-12 06:24"), ("Lascar", "VIIRS750", "2026-02-21 05:12"),
    ("Lascar", "VIIRS750", "2026-02-25 06:00"), ("Lascar", "VIIRS750", "2026-02-26 05:42"),
    ("Isluga", "VIIRS750", "2026-02-26 05:36"), ("PuyehueCordonCaulle", "VIIRS750", "2026-02-01 05:12"),
    ("Tupungatito", "VIIRS750", "2026-02-26 05:42"), ("Lascar", "VIIRS750", "2026-03-11 06:18"),
    ("Llaima", "MODIS", "2025-02-15 03:15"), ("Lascar", "MODIS", "2025-03-17 06:25"),
    ("Lascar", "MODIS", "2025-05-23 07:25"), ("Lascar", "MODIS", "2025-06-02 07:20"),
    ("PuyehueCordonCaulle", "MODIS", "2025-08-03 06:35"), ("Lascar", "VIIRS750", "2025-07-07 05:24"),
    ("NevadosDeChillan", None, "2025-11-04 06:00"),
)


def sha256_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r", b"")).hexdigest()


def _importar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


class Reglas:
    """Los módulos sellados, cargados sólo si su sha256 LF es el del manifiesto (si no, el lector no sale)."""

    def __init__(self, manifiesto=MANIFIESTO_REGLAS, raiz=RAIZ):
        malos = {r: sha256_lf(raiz / r) for r, s in manifiesto.items() if sha256_lf(raiz / r) != s}
        if malos:
            raise SystemExit(f"CANDADO: archivos de reglas distintos de los sellados: {malos}")
        os.environ.setdefault("F4_RAIZ", str(raiz))          # evaluar_f4 carga evaluar_d25 desde la raíz del repo
        self.F4 = _importar("evaluar_f4_retro", raiz / "experiments/_s172_retro_paquete/reglas/evaluar_f4.py")
        self.LP = _importar("leer_posicion_v375e_retro",
                            raiz / "experiments/_s172_retro_paquete/reglas/leer_posicion_v375e.py")
        # Por ruta y no por nombre: hay más de un `evaluar.py` en experiments/ y el orden de sys.path lo decide quien
        # importó antes (visto en el primer rojo: entraba el de _s146_ab_sin_test1). El sha256 ya se comprobó arriba.
        self.E = _importar("evaluar_v375e_retro", raiz / "experiments/_s162_v375/evaluar.py")
        self.CC = _importar("curva_cenit_retro", raiz / "experiments/_s162_v375/curva_cenit.py")
        self.EC = _importar("evaluador_comun_retro", raiz / "scripts/evaluador_comun.py")


# ---------------------------------------------------------------- carga de records
def bucket(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def cargar_carpeta(carpeta):
    """{(volcán, sensor, datetime_utc): record}, y la lista de claves repetidas (dos records de la misma pasada)."""
    out, rep = {}, []
    if carpeta is None:
        return out, rep
    for f in sorted(Path(carpeta).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        vol = d.get("volcano") or f.stem
        for r in d.get("records", []):
            k = (vol, r.get("sensor"), r.get("datetime_utc"))
            if k in out:
                rep.append(k)
            out[k] = r
    return out, rep


def _dt(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def tramo_de(b, dia):
    for t, (ini, fin, bs) in TRAMOS.items():
        if b in bs and ini <= dia <= fin:
            if t == "DM" and b != "MODIS" and dia in DM_SIN_VIIRS:
                return None
            return t
    return None


def armar_pasadas(via, k, kgem=None, es_noche=None, inner=None, sin_dato_trozos=()):
    """Una fila por pasada nocturna (clave de K o de la vía) en algún tramo. `estado`: ok, sin_dato_cobertura (K sin
    pasada de la vía, §6 C-cobertura), sin_dato_trozo (trozo que falló dos veces), sobra_en_via (la vía sin K: se
    lista), o via_sin_marca:<valor> (C-via)."""
    kgem = kgem or {}
    filas = []
    for key in sorted(set(via) | set(k), key=lambda x: (x[0], str(x[1]), str(x[2]))):
        vol, sensor, dts = key
        b = bucket(sensor)
        if b is None or not dts:
            continue
        dia = dts[:10]
        t = tramo_de(b, dia)
        if t is None or (vol == TUPUNGATITO and (t == "R25" or dia < INICIO_TUPUNGATITO)):
            continue
        dt = _dt(dts)
        if es_noche is not None and not es_noche(vol, b, dt):
            continue
        rk, rv = k.get(key), via.get(key)
        f = {"vol": vol, "sensor": sensor, "b": b, "dt": dts[:16], "noche": dia, "tramo": t,
             "z": (rv or rk or {}).get("sensor_zenith_deg"), "inner": (inner or {}).get(vol, 5.0),
             "k_rec": rk, "via_rec": rv, "kg_rec": kgem.get(key), "en_kgemelo": key in kgem,
             "via_marca": (rv or {}).get("via_codigo_mirova")}
        if rk is None:
            f["estado"] = "sobra_en_via"
        elif rk.get("via_codigo_mirova") is True:
            # VPR940-02: un record de K de disco con la marca de la vía no es K (producción enciende la vía de MODIS
            # desde 33f889bc5); se marca aquí, en todas las ventanas, y c_k_puro deja el instrumento en rojo
            f["estado"] = "k_con_marca:True"
        elif rv is None:
            f["estado"] = "sin_dato_cobertura"
        elif any(x["vol"] == vol and x["start"] <= dia <= x["end"] for x in sin_dato_trozos):
            f["estado"] = "sin_dato_trozo"
        elif rv.get("via_codigo_mirova") is not True:
            f["estado"] = "via_sin_marca:" + str(rv.get("via_codigo_mirova"))
        else:
            f["estado"] = "ok"
        filas.append(f)
    return filas


# ---------------------------------------------------------------- etiquetas (tabla sola decide; unión informa)
def etiquetar_tabla(filas, filas_ref_union, coords, bp=None, clase=None):
    """§4.1: la etiqueta que decide (`lab`) sale de la tabla sola (source CONS); `lab_union` (tabla más OCR) sólo si
    difiere. Etiquetador de banco_paridad con la regla SN y la lectura A (recalcular_s7_ref_congelada.py)."""
    if bp is None:
        import banco_paridad as bp
    if clase is None:
        import clase_mirova as clase
    if not filas:
        return filas
    ventana = (min(f["noche"] for f in filas), max(f["noche"] for f in filas))
    canales = {"tabla": [r for r in filas_ref_union if r["source"] == "CONS"], "union": list(filas_ref_union)}
    for canal, ref in canales.items():
        por_vb, ns, nv, _n = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
        shim = [{"vol": f["vol"], "b": f["b"], "dt": _dt(f["dt"]), "noche": f["noche"]} for f in filas]
        bp.etiquetar(shim, por_vb, ns, nv)
        for f, s in zip(filas, shim):
            lab = s["lab"]
            vrp = None
            if lab == "pos":
                pares = [x for x in bp.parear(por_vb.get((f["vol"], f["b"]), []), s["dt"]) if bp.es_alerta(x["tipo"])]
                lab = "protegida" if any(clase.alerta_protegida(x, lectura="A") for x in pares) else "bajo1"
                vrp = max([x["vrp_mw"] or 0.0 for x in pares] or [0.0])
            elif lab in ("minima", "sin_geometria"):
                lab = "sin_info"
            if canal == "tabla":
                f["lab"], f["vrp_mirova"] = lab, vrp
            else:
                if lab != f["lab"]:
                    f["lab_union"] = lab
                    f["vrp_mirova_union"] = vrp
                    if f["lab"] not in ("protegida", "bajo1"):
                        f["vrp_mirova"] = vrp
    return filas


def alertas_sin_pasada(filas, filas_ref_union, coords, bp=None):
    """§6 C-cobertura: toda alerta o bajo 1 MW de la tabla, nocturna y en la ventana, sin pasada nuestra (de K o de la
    vía) a ±120 s, se lista por volcán y sensor (banco_paridad.alertas_sin_record)."""
    if bp is None:
        import banco_paridad as bp
    if not filas:
        return {}
    ventana = (min(f["noche"] for f in filas), max(f["noche"] for f in filas))
    tabla = [r for r in filas_ref_union if r["source"] == "CONS"]
    por_vb, _ns, _nv, _n = bp.indexar_referencia(tabla, coords, ventana, regla_minimas="SN")
    shim = [{"vol": f["vol"], "b": f["b"], "dt": _dt(f["dt"])} for f in filas]
    return {"|".join(k): n for k, n in sorted(bp.alertas_sin_record(por_vb, shim).items())}


# ---------------------------------------------------------------- brazos y predicado
def _variante(R, rec, regla, inner):
    if rec is None or regla == "radiante":
        return rec
    d = R.LP.distancias_desde_record(rec)
    return R.LP.variante(rec, d[regla], inner) if d else rec


def inyectar_cumulo(rec):
    """§6 nulo del lector (MOD-D §8.5): un cúmulo de cumbre de 0,5 MW a 0,5 km del cráter, dentro de cualquier
    inner_radius_km; el predicado del tablero tiene que publicarlo."""
    r = copy.deepcopy(rec or {})
    r.update({"distance_class": "summit", "vrp_mw": 0.5, "t_max_k": 300.0, "triggered_test1": False,
              "discarded_reason": None, "f5_core_vrp_mw": 0.5,
              "primary_cluster": {"vrp_mw": 0.5, "centroid_dist_km": 0.5, "n_pixels": 2, "single_pixel_mode": False},
              "final_hotspot_dist_km": 0.5, "hotspot_dist_km": 0.5, "t_bg_k": 280.0,
              "anomaly_pixels": [{"lat": 0.0, "lon": 0.0, "vrp_mw": 0.25, "bt_k": 300.0, "dist_km": 0.5},
                                 {"lat": 0.0, "lon": 0.0, "vrp_mw": 0.25, "bt_k": 298.0, "dist_km": 0.6}]})
    return r


def tabla_publica(R, filas, predicado):
    """`_t[brazo] = {pub, mag}` para K, PLACEBO (K×1,2), KG (K-gemelo, si hay) y los tres brazos de posición de VIA,
    con el predicado del tablero (A97). `_evaluable` es estado ok (lo demás sale de los dos brazos, §6)."""
    casos, idx = [], []
    for i, f in enumerate(filas):
        f["_evaluable"] = f["estado"] == "ok"
        f["_t"] = {}
        arms = [("K", f["k_rec"]), ("placebo", R.F4.escalar(f["k_rec"], PLACEBO))]
        if f.get("kg_rec") is not None:
            arms.append(("KG", f["kg_rec"]))
        if f.get("via_rec") is not None:
            arms += [(b, _variante(R, f["via_rec"], REGLA_DE[b], f["inner"])) for b in BRAZOS]
        for b, rec in arms:
            if rec is not None:
                casos.append((rec, f["inner"]))
                idx.append((i, b))
    for (i, b), v in zip(idx, predicado(casos) if casos else []):
        filas[i]["_t"][b] = {"pub": int(v[0]), "mag": float(v[1] or 0.0)}
    for f in filas:
        for b in ("K", "placebo") + BRAZOS:
            f["_t"].setdefault(b, {"pub": 0, "mag": 0.0})
    return filas


def _ev(filas):
    return [f for f in filas if f.get("_evaluable")]


def _pub(f, b):
    return f["_t"][b]["pub"]


def _mag(f, b):
    return f["_t"][b]["mag"]


def es_n3(f):
    """N-3 (L4): protegida sólo del OCR (la tabla no la etiqueta protegida), Suomi NPP, antes del 2026-10-09."""
    return ("SNPP" in (f.get("sensor") or "") and f["dt"][:10] < HITO_N3 and f.get("lab") != "protegida"
            and f.get("lab_union") == "protegida")


def solo_ocr_perdidas(filas, b, n3=True):
    """Protegidas sólo del OCR (lab_union protegida, lab de la tabla no) que K publica y b no: fila 4 (§4.1)."""
    out = []
    for f in _ev(filas):
        if f.get("lab_union") == "protegida" and f["lab"] != "protegida" and _pub(f, "K") and not _pub(f, b):
            if n3 and es_n3(f):
                continue
            out.append((f["vol"], f["dt"], f["sensor"]))
    return out


def protegidas_sin_dato_que_k_publica(filas):
    """§6 C-cobertura y C-via: protegida de la tabla SIN DATO para la vía (sin pasada, trozo caído o sin marca) que K
    publica. En F26 es la fila 2; en R25 no aplica (la referencia de R25 es el OSF)."""
    return [(f["vol"], f["dt"], f["estado"]) for f in filas
            if f["estado"] not in ("ok", "sobra_en_via") and f.get("lab") == "protegida" and _pub(f, "K")]


# ---------------------------------------------------------------- reglas por sensor
def _mejora_d28(m):
    """D-28 (§6 PLACEBO): MEJORA sólo si d y d′ dan MEJORA (comparar_con_ganancia)."""
    return m.get("regla") == "MEJORA" and bool((m.get("dprima") or {}).get("dprima_da_mejora"))


def regla_modis(R, filas, b="V"):
    """§7 de PREREGISTRO_MODD_F4.md (tag s168-modd-f4-sellado), sobre el brazo b, con las funciones selladas."""
    F4 = R.F4
    x = {"p1": F4.p1(filas, b), "p1b": F4.p1b(filas, b), "p2": F4.p2(filas, b),
         "p2l_vs_K": F4.p2(filas, b, "K", lejana=True), "m": F4.m(filas, b)}
    otras = sorted({(y["vol"], y["dt"]) for o in BRAZOS if o != b for y in F4.p1(filas, b, o)["perdidas"]})
    res = {"controles": {"cobertura": {"estado": "OK", "protegidas_k_fuera": []}}, "posicion_elegida": b,
           "brazos": {b: x}, "protegidas_que_otra_posicion_publica": otras}
    regla = F4.veredicto(res)
    est = {x["p2"]["estado"], x["p2l_vs_K"]["estado"]}
    return {"regla": regla, "p1": x["p1"]["estado"], "perdidas_tabla": [(y["vol"], y["dt"]) for y in x["p1"]["perdidas"]
                                                                        if not y["solo_ocr"]],
            "p2": x["p2"]["estado"], "p2_lejana": x["p2l_vs_K"]["estado"], "B": x["p2"]["B"], "neto": x["p2"]["neto"],
            "p1b_decide": x["p1b"]["decide"], "m": x["m"]["regla"], "m_n": x["m"]["n"],
            "otra_posicion_publica": otras,
            "_fila_regla": (2 if x["p1"]["estado"] == "VETADO" else 3 if "PIERDE" in est else
                            5 if regla == "INDECIDIBLE" and "SIN SUSTRATO" in est else
                            4 if regla in ("DECIDE NICOLÁS", "INDECIDIBLE") else 6 if regla == "PROPONER ADOPCIÓN"
                            else 3)}


def filas_v375e(filas, brazos=BRAZOS, tramo_e=None):
    """Las filas con la forma de experiments/_s162_v375/evaluar.py (censo: peso 1, §5.6). Clases con la tabla sola:
    pos_prot, pos_bajo, neg_pub (negativo que K publica), neg_resto, far_tabla."""
    xs = []
    for f in _ev(filas):
        c = {"protegida": "pos_prot", "bajo1": "pos_bajo", "far_ref": "far_tabla"}.get(f["lab"])
        if f["lab"] == "neg_limpio":
            c = "neg_pub" if _pub(f, "K") else "neg_resto"
        if c is None:
            continue
        z = f.get("z")
        xs.append({"c": c, "K": bool(_pub(f, "K")), "VK": _mag(f, "K"), "X": {a: bool(_pub(f, a)) for a in brazos},
                   "V": {a: _mag(f, a) for a in brazos}, "mir": float(f.get("vrp_mirova") or 0.0), "w": 1.0,
                   "h": "%s|%s" % (f["vol"], "z?" if z is None else int(z // 10)), "prot": c == "pos_prot",
                   "tabla": True, "vol": f["vol"], "hora": f["dt"], "bloque": "%s|%s" % (f["vol"], f["noche"]),
                   "z": z, "tramo": tramo_e(f["dt"]) if tramo_e else "T", "sensor": f["sensor"]})
    return xs


def regla_v375(R, filas, a):
    """§5.4 (a) a (c) de V375-E con N-3 y el código de su §9.7 (`criterios_retro`); (d) informa en la retrospectiva."""
    E, LP = R.E, R.LP
    xs = filas_v375e(filas, tramo_e=E.tramo)
    prot = [x for x in xs if x["c"] == "pos_prot"]
    N_neg = {"neg_pub": sum(x["c"] == "neg_pub" for x in xs), "neg_resto": sum(x["c"] == "neg_resto" for x in xs)}
    tot = N_neg["neg_pub"] + N_neg["neg_resto"]
    tasa_k = N_neg["neg_pub"] / tot if tot else float("nan")
    if not tot or not prot:
        lect = {"silencio": {"veredicto": "SIN SUSTRATO"}, "P1b": {"baja": 0}}
    else:
        lect = E.lecturas(xs, a, np.random.default_rng(SEMILLA), N_neg, tasa_k)
    v1 = {"P1_veto_n3": [(x["vol"], x["hora"]) for x in prot if x["K"] and not x["X"][a] and not LP.no_veta_n3(x)],
          "P2_K": E.p2(xs, a, "K"), "lecturas": lect}
    p2l = LP.p2_con(xs, a, "K", E, lambda x, k: LP.err_pos(x, k, E))
    m = LP.magnitud(xs, a, R.EC)
    crit = LP.criterios_retro(v1, p2l, m)
    p2v, p2lv, sil = v1["P2_K"]["veredicto"], p2l["veredicto"], lect["silencio"]["veredicto"]
    if crit["a"] == LP.NO_CUMPLE:
        fila = 2
    elif p2v == "PIERDE" or p2lv == "PIERDE" or sil == "ENCIENDE DE MAS":          # L1
        fila = 3
    elif crit["retrospectiva"] != "CUMPLE (falta la sombra)" or (lect.get("P1b") or {}).get("baja"):
        fila = 4                                                                      # L1: lo no previsto, a Nicolás
    elif p2v == "SIN SUSTRATO":
        fila = 5                                                                      # §8.1 fila 5, VPR2-02
    else:
        fila = 6
    return {"criterios": crit, "P1_veto": v1["P1_veto_n3"], "p2": p2v, "B": v1["P2_K"]["B"], "neto": v1["P2_K"]["neto"],
            "p2_lejana": p2lv, "silencio": sil, "m": m["veredicto"], "m_n": m["n"],
            "p1b_baja": (lect.get("P1b") or {}).get("baja", 0), "N_neg": N_neg, "_fila_regla": fila}


def regla_v750(R, filas, b="V", sellado=False):
    """§6 punto 2 de V750-A (aa5583646, l. 217 a 243; P2 con regla_signos_p2 de D-45, §5.6 del pre-registro)."""
    F4 = R.F4
    p1, p2 = F4.p1(filas, b), F4.p2(filas, b)
    razon = F4.razon_protegidas(filas, b)
    m_v, m_pl = F4.m(filas, b), F4.m(filas, "placebo")
    # VPR940-01 (aprobado por Nicolás, S173): «el comparador separa» es un control del placebo (c_placebo), no M.
    m_ok = bool(razon["en_banda_0_9_1_1"])
    if p1["estado"] == "VETADO":
        fila = 2
    elif p2["estado"] == "PIERDE" or (sellado and not m_ok):
        fila = 3
    elif p2["estado"] == "BLOQUEA" or not sellado:
        fila = 4
    elif p2["estado"] == "SIN SUSTRATO":
        fila = 5
    else:
        fila = 6
    return {"p1": p1["estado"], "perdidas_tabla": [(y["vol"], y["dt"]) for y in p1["perdidas"] if not y["solo_ocr"]],
            "p2": p2["estado"], "B": p2["B"], "neto": p2["neto"], "razon_protegidas": razon,
            "m_regla_via": m_v["regla"], "m_regla_placebo": m_pl["regla"], "v750a_sellado": sellado,
            "_fila_regla": fila}


def _separa_provisional_d28(R, filas, b):
    """PROVISIONAL, no es de V750-A: la vía da MEJORA por D-28 (d y d′) y K×1,2 no. Es la lectura con que #940 armó
    el comparador; V750-A sellado la reemplaza (VPR940-01)."""
    return _mejora_d28(R.F4.m(filas, b)) and not _mejora_d28(R.F4.m(filas, "placebo"))


# VPR940-01: qué es «el comparador separa la vía de K×1,2» (V750-A §6.2) lo fija V750-A al sellarse. Se elige por
# nombre con --separa-v750, sin valor por defecto. Toda definición que no venga del texto sellado de V750-A lleva el
# prefijo PROVISIONAL; cuando V750-A se selle, su definición se agrega aquí con su commit y sha256 LF.
DEFINICIONES_SEPARA_V750 = {"PROVISIONAL_d28_s172": _separa_provisional_d28}


def regla_sensor(R, filas, sensor, brazo, sellado_v750=False):
    if sensor == "MODIS":
        return regla_modis(R, filas, brazo)
    if sensor == "VIIRS375":
        return regla_v375(R, filas, brazo)
    return regla_v750(R, filas, brazo, sellado_v750)


# ---------------------------------------------------------------- controles (§6)
def c_via(filas, tramo):
    tot = [f for f in filas if f["estado"] != "sobra_en_via" and f["estado"] != "sin_dato_cobertura"
           and f["estado"] != "sin_dato_trozo"]
    sin = [f for f in tot if f["estado"].startswith("via_sin_marca")]
    out = {"n": len(tot), "sin_marca": len(sin), "lista": [(f["vol"], f["dt"], f["estado"]) for f in sin][:50]}
    if not tot:
        out["estado"] = "ROJO: 0 records de la vía"
    elif tramo == "R25":
        por = collections.Counter(f.get("lab_osf", "sin_osf") for f in sin)
        den = collections.Counter(f.get("lab_osf", "sin_osf") for f in tot)
        malas = {c: (por[c], den[c]) for c in den if den[c] and por[c] / den[c] > UMBRAL_SIN_DATO}
        out["estado"] = "OK" if not malas else f"ROJO: más de 10 % sin marca en {malas}"
    else:
        out["estado"] = "OK" if not sin else f"ROJO: {len(sin)} records de la vía sin la marca"
    return out


def c_cobertura(filas, repetidas=(), clave="lab", clases=CLASES_QUE_DECIDEN):
    """A108: pasadas de VIA contra K antes de mirar nada; SIN DATO por clase que decide; repetidas, rojo. En R25 la
    clase es la del OSF (clave="lab_osf", VPR940-09)."""
    con_k = [f for f in filas if f["estado"] != "sobra_en_via"]
    sd = [f for f in con_k if f["estado"] in ("sin_dato_cobertura", "sin_dato_trozo")]
    por = collections.Counter(f.get(clave, "?") for f in sd)
    den = collections.Counter(f.get(clave, "?") for f in con_k)
    malas = {c: (por[c], den[c]) for c in clases if den[c] and por[c] / den[c] > UMBRAL_SIN_DATO}
    sobran = [(f["vol"], f["dt"], f["sensor"]) for f in filas if f["estado"] == "sobra_en_via"]
    estado = "OK"
    if not con_k or len(sd) == len(con_k):
        estado = "ROJO: la vía no tiene pasadas"
    elif malas:
        estado = f"ROJO: más de 10 % SIN DATO en {malas}"
    elif repetidas:
        estado = f"ROJO: {len(repetidas)} pasadas repetidas"
    return {"estado": estado, "pasadas_k": len(con_k), "sin_dato": len(sd), "por_clase": dict(por),
            "sobran_en_via": sobran[:50], "n_sobran": len(sobran), "repetidas": list(repetidas)[:20],
            "protegidas_sin_dato_que_k_publica": protegidas_sin_dato_que_k_publica(filas)}


def c_k_puro(filas):
    """VPR940-02: ningún record de K de disco puede traer via_codigo_mirova True, en ninguna ventana (R25 incluida,
    que no tiene C-K). Con uno solo, rojo."""
    malos = [(f["vol"], f["sensor"], f["dt"]) for f in filas if str(f.get("estado", "")).startswith("k_con_marca")]
    return {"estado": "OK" if not malos else f"ROJO: {len(malos)} records de K de disco con la marca de la vía",
            "lista": malos[:50]}


def cobertura_kgemelo(filas, tier_a=None):
    """VPR940-03: el K-gemelo tiene que cubrir lo que manda D3 (§10.3): todas las pasadas de K en DM, todas las de F26
    de Láscar y de Nevados de Chillán, y en cada otro volcán con F26, al menos tres días de F26 con todas sus pasadas.
    VPR940b-07: con `tier_a`, un volcán de la lista sin ninguna pasada de K en F26 tampoco cumple D3 (antes se saltaba
    en silencio); main pasa los 11 Tier A."""
    con_k = [f for f in filas if f.get("k_rec") is not None and f.get("estado") != "sobra_en_via"]
    faltan = []
    sin_f26 = sorted(set(tier_a or ()) - {f["vol"] for f in con_k if f["tramo"] in TRAMOS_F26})
    faltan += [("F26", v, "sin pasadas de K en F26") for v in sin_f26]
    dm = [f for f in con_k if f["tramo"] == "DM"]
    if not dm:
        faltan.append("sin pasadas de K en DM")
    faltan += [("DM", f["vol"], f["dt"]) for f in dm if not f.get("en_kgemelo")]
    f26 = [f for f in con_k if f["tramo"] in TRAMOS_F26]
    for vol in sorted({f["vol"] for f in f26}):
        fv = [f for f in f26 if f["vol"] == vol]
        if vol in VOLCANES_F26_ENTEROS_D3:
            faltan += [("F26", vol, f["dt"]) for f in fv if not f.get("en_kgemelo")]
            continue
        dias_ok = {d for d in {f["noche"] for f in fv}
                   if all(f.get("en_kgemelo") for f in fv if f["noche"] == d)}
        if len(dias_ok) < DIAS_F26_D3:
            faltan.append(("F26", vol, f"{len(dias_ok)} días cubiertos, se piden {DIAS_F26_D3}"))
    return {"estado": "OK" if not faltan else f"ROJO: el K-gemelo no cubre D3 ({len(faltan)} faltas)",
            "faltan": faltan[:50], "volcanes_sin_f26_en_k": sin_f26}


def sobras_kgemelo(kgem, k):
    """VPR940b-07: pasadas (dentro de algún tramo) que trae el K-gemelo y no K de disco. armar_pasadas no las ve (itera
    vía y K), así que se listan aparte en C-K. Informa: C-K mide K de disco contra K de hoy sobre las pasadas de K."""
    out = []
    for key in sorted(set(kgem) - set(k), key=lambda x: (x[0], str(x[1]), str(x[2]))):
        b = bucket(key[1])
        if b is not None and key[2] and tramo_de(b, str(key[2])[:10]) is not None:
            out.append(key)
    return out


def _excepcion_valida(e):
    """VPR940b-03 y VPR946-04: una excepción nombrada de C-K trae volcán, hora al minuto que se lee como fecha
    (AAAA-MM-DD HH:MM) y un sensor de texto reconocible."""
    if not isinstance(e, dict) or not isinstance(e.get("vol"), str) or not e["vol"].strip():
        return False
    try:
        _dt(e["dt"])
    except (KeyError, TypeError, ValueError):
        return False
    s, b = e.get("sensor"), e.get("b")
    return (isinstance(s, str) and bucket(s) in SENSORES) or (s is None and b in SENSORES)


def c_k(filas, excepciones=(), tier_a=None, sobras_kg=()):
    """C-K: K-gemelo contra K de disco, misma publicación y pc.vrp_mw a 0,001 MW, salvo a lo más 3 pasadas nombradas
    por sensor con su empate de argsort escrito (R-15). Una excepción mal formada deja C-K en rojo (VPR940b-03)."""
    con = [f for f in filas if f.get("en_kgemelo") and f.get("k_rec") is not None]
    if not con:
        return {"estado": "ROJO: sin K-gemelo", "n": 0}
    mal_formadas = [e for e in excepciones if not _excepcion_valida(e)]
    excepciones = [e for e in excepciones if _excepcion_valida(e)]
    nombradas = _nombradas(excepciones)                          # VPR940b-02: una sola copia de la regla
    por_sensor = collections.Counter(bucket(e.get("sensor")) or e.get("b") for e in excepciones)
    difs = []
    for f in con:
        kg = f["kg_rec"] or {}
        pv = lambda r: float(((r or {}).get("primary_cluster") or {}).get("vrp_mw") or 0.0)   # noqa: E731
        if _pub(f, "K") != f["_t"].get("KG", {"pub": 0})["pub"] or abs(pv(f["k_rec"]) - pv(kg)) > TOL_VRP_CK:
            difs.append((f["vol"], f["dt"], f["b"]))
    no_expl = [d for d in difs if (d[0], d[1]) not in nombradas]
    excede = {s: n for s, n in por_sensor.items() if n > TOPE_EXCEPCIONES_CK}
    sin_empate = [e for e in excepciones if not str(e.get("empate_argsort", "")).strip()]
    cob = cobertura_kgemelo(filas, tier_a)
    estado = ("OK" if not no_expl and not excede and not sin_empate and not mal_formadas and cob["estado"] == "OK" else
              f"ROJO: {len(no_expl)} diferencias sin nombrar, tope excedido {excede}, sin empate {len(sin_empate)}, "
              f"mal formadas {len(mal_formadas)}, cobertura {cob['estado']}")
    return {"estado": estado, "n": len(con), "diferencias": difs[:50], "no_explicadas": no_expl[:50],
            "excepciones_mal_formadas": [str(e)[:120] for e in mal_formadas[:20]], "cobertura_kgemelo": cob,
            "sobras_kgemelo": list(sobras_kg)[:50], "n_sobras_kgemelo": len(sobras_kg)}


def _nombradas(excepciones):
    """Las pasadas nombradas de C-K (volcán, hora al minuto) que traen el empate de argsort escrito. La usan c_k y
    nulo_runner (VPR940b-02); una excepción mal formada no nombra nada (VPR940b-03)."""
    return {(e["vol"], str(e["dt"])[:16]) for e in excepciones
            if _excepcion_valida(e) and str(e.get("empate_argsort", "")).strip()}


def nulo_runner(R, filas, excepciones=()):
    """B = 0 de K-gemelo contra K en P2 (salvo las nombradas de C-K, que ya cuentan en C-K); y el control de que el
    nulo puede fallar: K-gemelo contra PLACEBO da B mayor que 0 o M distinta. VPR940b-10, escrito: las nombradas salen
    también del control «puede fallar» y de M del K-gemelo (con a lo más 3 por sensor el efecto es nulo)."""
    nombradas = _nombradas(excepciones)          # VPR940-04: «B = 0 salvo las pasadas nombradas de C-K»
    con = [f for f in _ev(filas) if "KG" in f["_t"] and (f["vol"], f["dt"]) not in nombradas]
    if not con:
        return {"estado": "ROJO: sin K-gemelo"}
    p = R.F4.p2(con, "KG", "K")
    ctl = R.F4.p2(con, "KG", "placebo")
    # «M distinta»: la mediana de d de PLACEBO contra K se separa de 0 (la de K-gemelo contra K es 0 si son iguales)
    m_kg, m_pl = R.F4.m(con, "KG"), R.F4.m(con, "placebo")
    puede = ctl["B"] > 0 or (m_pl.get("n", 0) > 0 and abs(m_pl.get("mediana_d") or 0.0) > 1e-12)
    return {"estado": "OK" if p["B"] == 0 and puede else f"ROJO: B={p['B']}, el nulo puede fallar={puede}",
            "B": p["B"], "B_contra_placebo": ctl["B"], "m_kgemelo": m_kg.get("regla"),
            "mediana_d_placebo": m_pl.get("mediana_d")}


def c_placebo(R, filas, sensor, brazo="V", sellado_v750=False, separa_v750=None):
    """K×1,2: M de D-28 no da MEJORA (MODIS y 375); en 750 el comparador de V750-A §6.2 separa la vía de K×1,2.

    VPR940-01 (aprobado): en 750 «separa» es este control. Sin V750-A sellado no se calcula (la fila 4 ya pone el
    techo, §8.1); sellado y sin definición (`separa_v750` None), rojo. VPR940b-11, escrito: las discordancias de P1 y
    P2 se miran pasada por pasada (más estricto que pasar por F4.p2), no por la prueba de signos."""
    m = R.F4.m(filas, "placebo")
    pl = R.F4.p1(filas, "placebo")
    # VPR940-05: P1 y P2 de K×1,2 contra K sin discordancias de publicación, salvo las dos causas de L7 (V750-A §7):
    # t_max de K bajo 278,15 K (los filtros de artefacto del tablero miran la magnitud) o la magnitud que cruza el
    # tope de 50.000 MW del tablero. Una discordancia sin esas causas dice que el predicado mira la magnitud donde no
    # debería: instrumento roto.
    disc, sin_expl = [], []
    for f in _ev(filas):
        if f["lab"] not in ("protegida", "bajo1", "neg_limpio") or _pub(f, "K") == _pub(f, "placebo"):
            continue
        tmax = (f.get("k_rec") or {}).get("t_max_k")
        causa = ("t_max_bajo_278" if tmax is not None and tmax < T_MAX_FILTROS_K else
                 "cruza_tope_50000" if _mag(f, "K") <= TOPE_TABLERO_MW < _mag(f, "K") * PLACEBO else None)
        disc.append((f["vol"], f["dt"], f["lab"], causa))
        if causa is None:
            sin_expl.append((f["vol"], f["dt"], f["lab"]))
    out = {"m_regla": m.get("regla"), "mejora_d28": _mejora_d28(m), "p1_placebo": pl["estado"],
           "discordancias": disc[:50], "discordancias_sin_explicar": sin_expl[:50]}
    rojo_m = None
    if sensor != "VIIRS750":
        rojo_m = "ROJO: el placebo da MEJORA" if out["mejora_d28"] else None
    elif not sellado_v750:
        out["separa_v750"] = "no se calcula: V750-A sin sellar (la fila 4 pone el techo)"
    elif separa_v750 is None:
        rojo_m = "ROJO: V750-A sellado y sin definición de «separa» (VPR940-01: --separa-v750)"
    else:
        out["separa_v750"] = bool(separa_v750(R, filas, brazo))
        rojo_m = None if out["separa_v750"] else "ROJO: el comparador no separa la vía de K×1,2 (VPR940-01)"
    out["estado"] = (rojo_m or
                     (f"ROJO: {len(sin_expl)} discordancias de publicación sin causa de L7" if sin_expl else "OK"))
    return out


def nulo_lector(R, filas, sensor, brazo, predicado, sellado_v750=False):
    """§6 nulo del lector, sobre las filas reales del sensor (y filas sintéticas si no hay sustrato):
    (1) K contra K: la regla con VIA := K da 0 diferencias en P1 y P2;
    (2) quitar a la vía una protegida que K publica lleva a la fila 2;
    (3) 50 negativos limpios con un cúmulo de cumbre inyectado (por el predicado) suben P2 en 50."""
    out = {}
    kk = copy.deepcopy(filas)
    for f in kk:
        for b in BRAZOS:
            f["_t"][b] = dict(f["_t"]["K"])
    p1, p2 = R.F4.p1(kk, brazo), R.F4.p2(kk, brazo)
    out["k_contra_k"] = {"p1": p1["estado"], "perdidas": len(p1["perdidas"]), "B": p2["B"], "neto": p2["neto"]}
    ok1 = p1["estado"] == "SIN PERDIDA" and p2["B"] == 0
    mu = copy.deepcopy(filas)
    cand = [f for f in _ev(mu) if f["lab"] == "protegida" and _pub(f, "K")]
    origen = "real" if cand else "sintetica"
    if not cand:
        base = next((f for f in _ev(mu)), None) or _sintetica()
        s = copy.deepcopy(base)
        s.update({"lab": "protegida", "vrp_mirova": 2.0, "_evaluable": True, "estado": "ok", "dt": "2026-02-15 05:00",
                  "noche": "2026-02-15", "vol": "Lascar"})
        s.pop("lab_union", None)
        s["_t"] = {b: {"pub": 1, "mag": 2.0} for b in ("K", "placebo") + BRAZOS}
        mu.append(s)
        cand = [s]
    cand[0]["_t"][brazo] = {"pub": 0, "mag": 0.0}
    r = regla_sensor(R, mu, sensor, brazo, sellado_v750)
    out["mutacion_protegida"] = {"fila": r["_fila_regla"], "origen": origen}
    ok2 = r["_fila_regla"] == 2
    iny = copy.deepcopy(filas)
    neg = [f for f in _ev(iny) if f["lab"] == "neg_limpio" and not _pub(f, brazo) and not _pub(f, "K")][:N_INYECTADOS]
    while len(neg) < N_INYECTADOS:
        s = _sintetica(len(neg))
        iny.append(s)
        neg.append(s)
    antes = R.F4.p2(iny, brazo)["s_b"]
    casos = [(inyectar_cumulo(f.get("via_rec") or f.get("k_rec")), f["inner"]) for f in neg]
    for f, v in zip(neg, predicado(casos)):
        f["_t"][brazo] = {"pub": int(v[0]), "mag": float(v[1] or 0.0)}
    despues = R.F4.p2(iny, brazo)["s_b"]
    out["contador"] = {"antes": antes, "despues": despues, "inyectados": N_INYECTADOS}
    ok3 = despues - antes == N_INYECTADOS
    out["estado"] = "OK" if ok1 and ok2 and ok3 else f"ROJO: k_contra_k={ok1} mutacion={ok2} contador={ok3}"
    return out


def _sintetica(i=0):
    return {"vol": "Lascar", "sensor": "SINTETICA", "b": "X", "dt": "2026-02-%02d 0%d:00" % (1 + i % 28, i % 10),
            "noche": "2026-02-%02d" % (1 + i % 28), "tramo": "F26-V", "z": 10.0, "inner": 5.0, "estado": "ok",
            "_evaluable": True, "lab": "neg_limpio", "vrp_mirova": None, "k_rec": {}, "via_rec": {},
            "_t": {b: {"pub": 0, "mag": 0.0} for b in ("K", "placebo") + BRAZOS}}


ORIGENES_MONTAJE = ("MOD-D fase 4", "V375-E", "V750-B")     # §6 C-montaje: los A/B donde el código es el mismo
# PENDIENTE (no se inventa): qué tag de cada A/B es el «tag de origen» del §6 C-montaje. Cuando se fije, va aquí como
# {origen: tag} y validar_montaje exige esos tres; mientras sea None, sólo exige uno por origen.
TAGS_MONTAJE_ESPERADOS = None


def _pasada_de_dm(p):
    """'volcán|sensor|AAAA-MM-DD HH:MM' de una pasada del tramo DM (VIIRS sin el 12 ni el 13)."""
    partes = str(p or "").split("|")
    if len(partes) != 3 or len(partes[2]) < 10:
        return False
    b = bucket(partes[1])
    return b is not None and tramo_de(b, partes[2][:10]) == "DM"


def validar_montaje(d):
    """VPR940-06 (§6 C-montaje, VPR2-09): el resultado externo tiene que traer los tags de origen, el `git diff`
    listado y cada diferencia explicada sólo por un hunk de ese diff (con el hunk escrito) o por otro_granulo. Un
    `{"estado": "OK"}` suelto no basta."""
    if not isinstance(d, dict):
        return {"estado": "ROJO: sin resultado de C-montaje (L3)"}
    malas = []
    if not str(d.get("estado", "")).startswith("OK"):
        malas.append("estado no OK")
    tags = d.get("tags")
    # VPR940b-06: un tag por origen (los tres A/B del §6 C-montaje), no una lista cualquiera
    if not (isinstance(tags, dict) and set(tags) == set(ORIGENES_MONTAJE)
            and all(isinstance(t, str) and t.strip() for t in tags.values())):
        malas.append("sin un tag por origen " + str(ORIGENES_MONTAJE))
    elif TAGS_MONTAJE_ESPERADOS is not None and tags != TAGS_MONTAJE_ESPERADOS:
        malas.append("tags de origen distintos de los declarados")
    if not (isinstance(d.get("diff_listado"), str) and d["diff_listado"].strip()):
        malas.append("sin git diff listado")
    difs = d.get("diferencias")
    if not isinstance(difs, list):
        malas.append("sin lista de diferencias")
        difs = []
    for x in difs:
        if not _pasada_de_dm((x or {}).get("pasada")):                  # VPR940b-06: sólo pasadas de DM
            malas.append(("fuera de DM", (x or {}).get("pasada")))
            continue
        por = (x or {}).get("explicada_por")
        if por == "hunk" and str((x or {}).get("hunk", "")).strip():
            continue
        if por == "otro_granulo":
            continue
        malas.append(("sin explicar", (x or {}).get("pasada")))
    return {"estado": "OK" if not malas else f"ROJO: C-montaje inválido ({len(malas)})", "faltas": malas[:50],
            "n_diferencias": len(difs)}


# §11: lo que el manifiesto tiene que traer siempre (el lector, lo que importa, el predicado y los perfiles). Las
# referencias congeladas y el OSF dependen de la corrida: main las agrega desde --cons, --ocr y --osf.
REQUERIDOS_MANIFIESTO = tuple(sorted(set(MANIFIESTO_REGLAS) | {
    "experiments/_s172_retro_paquete/leer_retro.py",
    "scripts/clase_mirova.py", "scripts/banco_paridad.py", "scripts/referencia_mirova_unificada.py",
    "frontend/index.html", "pipeline/profiles/_s172_retro_paquete.yaml", "pipeline/profiles/_s172_retro_k.yaml"}))


def rutas_referencias(rutas, raiz=RAIZ):
    """§11 (VPR946-02): la ruta relativa al repo de cada referencia de la corrida (--cons, --ocr, --osf), para exigirla
    en el manifiesto. Una fuera del repo no puede estar en el manifiesto: queda marcada y deja el candado en rojo."""
    out = []
    for p in rutas:
        if not p:
            continue
        try:
            out.append(Path(p).resolve().relative_to(Path(raiz).resolve()).as_posix())
        except ValueError:
            out.append("FUERA_DEL_REPO:" + str(p))
    return out


def candado(manifiesto, raiz=RAIZ, requeridos=REQUERIDOS_MANIFIESTO):
    """§11: sha256 LF de cada archivo del manifiesto del sello contra el disco, ANTES de leer. Un manifiesto al que le
    falta un archivo requerido no es un candado (un {} daba OK)."""
    if manifiesto is None:
        return {"estado": "ROJO: sin manifiesto del sello"}
    faltan = sorted(set(requeridos) - set(manifiesto))
    malos = {r: (s, sha256_lf(raiz / r) if (raiz / r).exists() else "falta") for r, s in manifiesto.items()
             if not (raiz / r).exists() or sha256_lf(raiz / r) != s}
    estado = ("OK" if not malos and not faltan else
              f"ROJO: {len(malos)} archivos distintos del sello, {len(faltan)} requeridos fuera del manifiesto")
    return {"estado": estado, "distintos": malos, "fuera_del_manifiesto": faltan}


# ---------------------------------------------------------------- R25 contra el OSF (§4.2, §5.2)
NOMBRES_OSF = {"Chaitén": "Chaiten", "Chillán, Nevados de": "NevadosDeChillan", "Láscar": "Lascar",
               "Planchón-Peteroa": "PlanchonPeteroa", "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
               "Copahue": "Copahue", "Isluga": "Isluga", "Lastarria": "Lastarria", "Llaima": "Llaima",
               "Villarrica": "Villarrica", "Tupungatito": "Tupungatito"}
POR_COORD_OSF = {(-42.83, -72.65): "Chaiten", (-36.86, -71.38): "NevadosDeChillan", (-37.86, -71.18): "Copahue",
                 (-19.15, -68.83): "Isluga", (-25.17, -68.51): "Lastarria", (-38.69, -71.73): "Llaima",
                 (-23.37, -67.73): "Lascar", (-35.22, -70.57): "PlanchonPeteroa",
                 (-40.59, -72.12): "PuyehueCordonCaulle", (-39.42, -71.93): "Villarrica"}
RES_OSF = {"375": "VIIRS375", "750": "VIIRS750", "1000": "MODIS"}


def _hav(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def leer_osf(ruta, volcanes, es_noche):
    """Filas chilenas del OSF en R25 (contar_osf.py del segundo verificador): noche por elevación solar del proyecto,
    distancia del píxel más caliente al cráter (vent) de volcanoes.yaml (R-1)."""
    ini, fin, _ = TRAMOS["R25"]
    out = []
    with open(ruta, encoding="latin-1") as fh:
        for r in csv.DictReader(fh):
            n = NOMBRES_OSF.get(r["Volc_Name"]) or POR_COORD_OSF.get((round(float(r["Volc_LAT"]), 2),
                                                                     round(float(r["Volc_LON"]), 2)))
            if n is None or n not in volcanes:
                continue
            dt = datetime.strptime(r["timeUTC"], "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc)
            if not (ini <= dt.strftime("%Y-%m-%d") <= fin):
                continue
            b = RES_OSF[r["Resolution"]]
            v = volcanes[n]
            cl, cn = (v.get("vent_lat"), v.get("vent_lon")) if v.get("vent_lat") is not None else (v["lat"], v["lon"])
            out.append({"vol": n, "b": b, "dt": dt, "vrp_w": float(r["VRP"]), "class": int(float(r["class"])),
                        "noche": es_noche(n, b, dt), "dist_crater_km": _hav(float(r["LAT"]), float(r["LON"]), cl, cn),
                        "inner": float(v["inner_radius_km"]), "satzen": float(r["SatZen"])})
    return out


def p1_osf(filas, osf, brazo="V"):
    """§5.2: por protegida OSF (noche, class 1, VRP ≥ 1e6 W, píxel más caliente dentro del radio interno), la pasada
    nuestra a ±120 s. La vía no y K sí: candidata a veto (fila 4). SIN DATO de la vía que K publica: candidata (C-via
    y C-cobertura en R25). La vía sí y K no: no puede ocurrir (K publica todas): defecto del lector."""
    idx = collections.defaultdict(list)
    for f in filas:
        if f["tramo"] == "R25" and f["estado"] != "sobra_en_via":
            idx[(f["vol"], f["b"])].append(f)
    res = {s: {"protegidas": 0, "candidatas": [], "sin_record": [], "ninguno": [], "defecto": [], "pub_via": 0,
               "por_volcan": collections.Counter(), "dobles": []} for s in SENSORES}
    pares_cenit, lejanas, ambiguas = [], [], []
    for o in osf:
        if not o["noche"]:
            continue
        dentro = o["dist_crater_km"] <= o["inner"]
        prot = o["class"] == 1 and o["vrp_w"] >= 1e6 and dentro
        cand = [f for f in idx.get((o["vol"], o["b"]), []) if abs((_dt(f["dt"]) - o["dt"]).total_seconds()) <= VENTANA_S]
        if o["class"] == 1 and o["vrp_w"] >= 1e6 and not dentro:
            lejanas.append((o["vol"], o["b"], o["dt"].strftime("%Y-%m-%d %H:%M"),
                            any(f.get("_evaluable") and _pub(f, brazo) for f in cand)))
        if o["class"] == 0 and o["vrp_w"] >= 1e6 and dentro:
            ambiguas.append((o["vol"], o["b"], o["dt"].strftime("%Y-%m-%d %H:%M")))
        for f in cand:
            if f.get("z") is not None:
                pares_cenit.append(abs(float(f["z"]) - o["satzen"]))
        if not prot:
            continue
        r = res[o["b"]]
        r["protegidas"] += 1
        r["por_volcan"][o["vol"]] += 1
        clave = (o["vol"], o["dt"].strftime("%Y-%m-%d %H:%M"))
        if len(cand) > 1:
            r["dobles"].append(clave)
        if not cand:
            r["sin_record"].append(clave)
            continue
        f = cand[0]
        f["lab_osf"] = "protegida_osf"
        kpub = _pub(f, "K")
        if not f.get("_evaluable"):
            if kpub:
                r["candidatas"].append(clave + (f["estado"],))
            continue
        vpub = _pub(f, brazo)
        r["pub_via"] += vpub
        if vpub and kpub and _mag(f, brazo) > 0 and _mag(f, "K") > 0:
            r.setdefault("razon_cota", []).append((_mag(f, brazo) / (o["vrp_w"] / 1e6), _mag(f, "K") / (o["vrp_w"] / 1e6)))
        if kpub and not vpub:
            r["candidatas"].append(clave + ("via_no_publica",))
        elif not kpub and not vpub:
            r["ninguno"].append(clave)
        elif vpub and not kpub:
            r["defecto"].append(clave)
    for r in res.values():
        r["por_volcan"] = dict(r["por_volcan"])
        rc = r.pop("razon_cota", [])
        # §4.3: la razón contra el OSF es sólo cota (truncada por el piso del OSF); no decide ni se compara con F26
        r["razon_cota_mediana"] = ({"via": statistics.median(x for x, _ in rc), "K": statistics.median(y for _, y in rc),
                                    "n": len(rc)} if rc else None)
    c_pareo = "OK" if not any(r["dobles"] for r in res.values()) else "ROJO: protegida OSF pareada a dos pasadas"
    # VPR946-01: sin pares no hay nada medido (all([]) daba OK)
    c_cenit = ("ROJO: sin pares de cenit contra SatZen" if not pares_cenit else
               "OK" if all(d <= TOL_CENIT_OSF for d in pares_cenit) else "ROJO: cenit nuestro y SatZen difieren más de 2°")
    return {"por_sensor": res, "c_pareo": c_pareo, "c_cenit": c_cenit, "n_pares_cenit": len(pares_cenit),
            "lejanas": lejanas, "lejanas_publicadas_como_cumbre": [x for x in lejanas if x[3]], "ambiguas": ambiguas}


# ---------------------------------------------------------------- cenit, lectura B y noche (informan)
def _spearman(x, y):
    def rang(v):
        o = np.argsort(v, kind="mergesort")
        r = np.empty(len(v))
        r[o] = np.arange(len(v))
        return r
    if len(x) < 3:
        return None
    return float(np.corrcoef(rang(np.asarray(x)), rang(np.asarray(y)))[0, 1])


def curva_cenit(R, filas, brazo):
    """§5.3: razón brazo/MIROVA y K/MIROVA por tramo de 10° y por el corte de 30° (L5), Spearman contra el cenit con
    200 barajados (semilla 172) y la razón doble dentro de la noche con el veredicto de V375-E §5.3 (curva_cenit.py)."""
    out = {}
    for b in (brazo, "K"):
        pares = [(float(f["z"]), _mag(f, b) / f["vrp_mirova"], f) for f in _ev(filas)
                 if f["lab"] in ("protegida", "bajo1") and f.get("z") is not None and _pub(f, b) and _mag(f, b) > 0
                 and (f.get("vrp_mirova") or 0) > 0]
        por = collections.defaultdict(list)
        for z, r, _ in pares:
            por["%d-%d" % (int(z // 10) * 10, int(z // 10) * 10 + 10)].append(r)
        corte = {"bajo_30": [r for z, r, _ in pares if z < CORTE_CENIT_INFORMA],
                 "sobre_30": [r for z, r, _ in pares if z >= CORTE_CENIT_INFORMA]}
        rho = _spearman([p[0] for p in pares], [p[1] for p in pares])
        rng = np.random.default_rng(SEMILLA)
        nul = []
        if rho is not None:
            ys = np.array([p[1] for p in pares])
            for _ in range(N_BARAJADOS):
                nul.append(_spearman([p[0] for p in pares], rng.permutation(ys)))
        pas = [{"vol": f["vol"], "hora": f["dt"], "z": f["z"], "mir": float(f["vrp_mirova"] or 0.0),
                "plat": f.get("sensor"), "pub": bool(_pub(f, b)), "vrp": _mag(f, b)}
               for f in _ev(filas) if f["lab"] in ("protegida", "bajo1") and f.get("z") is not None]
        try:
            r = R.CC.resumen(R.CC.pares_por_noche(pas, "vrp", "pub", condicionar=True),
                             nulo=R.CC.pares_nulo(pas, "vrp", "pub", condicionar=True))
            dob = {"veredicto": R.CC.veredicto(r), "noches": r["todas"]["n_noches"], "d": r["todas"]["d"]}
        except Exception as e:  # noqa: BLE001  (informa: si no corre, se dice)
            dob = {"veredicto": "SIN SUSTRATO", "error": f"{type(e).__name__}: {e}"[:200]}
        out[b] = {"n": len(pares), "por_tramo_10": {k: [round(statistics.median(v), 3), len(v)] for k, v in sorted(por.items())},
                  "corte_30": {k: [round(statistics.median(v), 3) if v else None, len(v)] for k, v in corte.items()},
                  "spearman": rho, "spearman_nulo_p95_abs": float(np.percentile(np.abs(nul), 95)) if nul else None,
                  "razon_doble": dob}
    return out


def controles_cenit(R, filas, brazo):
    """§6, controles de cenit (los de V375-E §4): el nulo de cenit parecido (pares a menos de 5°) contiene 1; una
    ganancia pareja (×1,5) no mueve la razón doble; una ganancia que crece con el cenit (×(1 + z/20)) la sube. Si uno
    cae, la curva no se lee (no es un control del veredicto entero)."""
    def pas(g):
        return [{"vol": f["vol"], "hora": f["dt"], "z": f["z"], "mir": float(f["vrp_mirova"] or 0.0),
                 "plat": f.get("sensor"), "pub": bool(_pub(f, brazo)), "vrp": _mag(f, brazo) * g(float(f["z"]))}
                for f in _ev(filas) if f["lab"] in ("protegida", "bajo1") and f.get("z") is not None]

    def res(g):
        p = pas(g)
        return R.CC.resumen(R.CC.pares_por_noche(p, "vrp", "pub", condicionar=True),
                            nulo=R.CC.pares_nulo(p, "vrp", "pub", condicionar=True))
    try:
        base, pareja, crece = res(lambda z: 1.0), res(lambda z: 1.5), res(lambda z: 1.0 + z / 20.0)
    except Exception as e:  # noqa: BLE001
        return {"estado": "SIN SUSTRATO", "error": f"{type(e).__name__}: {e}"[:200]}
    v = R.CC.veredicto(base)
    if v == "SIN SUSTRATO":
        return {"estado": "SIN SUSTRATO"}
    d0, d1, d2 = base["todas"]["d"][0], pareja["todas"]["d"][0], crece["todas"]["d"][0]
    ok = v != "NULO SESGADO" and abs(d1 - d0) <= 1e-9 and d2 > d0
    return {"estado": "OK" if ok else "ROJO", "veredicto": v, "d": d0, "d_ganancia_pareja": d1, "d_ganancia_cenit": d2}


def barajar_en_estratos(filas, rng):
    """§7 (GUIA §3b fila 7): copia de las filas evaluables, en su orden, con la etiqueta (lab, lab_union y VRP de
    MIROVA) permutada dentro de cada estrato volcán × tramo de 10° de cenit."""
    ev = _ev(filas)
    por = collections.defaultdict(list)
    for i, f in enumerate(ev):
        por[(f["vol"], None if f.get("z") is None else int(float(f["z"]) // 10))].append(i)
    out = [dict(f) for f in ev]
    for idx in por.values():
        perm = rng.permutation(len(idx))
        for dst, src in zip(idx, perm):
            g = ev[idx[src]]
            out[dst]["lab"], out[dst]["vrp_mirova"] = g["lab"], g.get("vrp_mirova")
            out[dst].pop("lab_union", None)
            if "lab_union" in g:
                out[dst]["lab_union"] = g["lab_union"]
    return out


def sorteo_etiquetas(R, filas, n=N_BARAJADOS, semilla=SEMILLA):
    """§7, último párrafo (VPR940-11; informa, se calcula antes de leer): sobre K contra K (K-gemelo contra K de disco
    si el K-gemelo cubre todas las pasadas evaluables; si no, K contra sí mismo), qué fracción de barajados de las
    etiquetas por estrato da GANA o EMPATE en P2 por azar. No usa la vía."""
    ev = _ev(filas)
    brazos = ("KG", "K") if ev and all("KG" in f["_t"] for f in ev) else ("K", "K")
    rng = np.random.default_rng(semilla)
    cuenta = collections.Counter()
    for _ in range(n):
        cuenta[R.F4.p2(barajar_en_estratos(filas, rng), brazos[0], brazos[1])["estado"]] += 1
    tot = float(n) if n else 1.0
    ge = (cuenta["GANA"] + cuenta["EMPATE"]) / tot
    ss = cuenta["SIN SUSTRATO"] / tot
    # VPR940b-01: con dos brazos iguales (K contra K, o un K-gemelo idéntico a K, que es lo que C-K exige) B = 0 y P2
    # da SIN SUSTRATO en todos los barajados por construcción: el control no puede variar y su 0 no mide el azar. El
    # informe lo dice; cómo leer el §7 (por ejemplo, la vía contra K barajada) lo decide Nicolás.
    poder = ("SIN PODER (VPR940b-01): SIN SUSTRATO en %d de %d barajados (brazos %s); con brazos iguales P2 tiene "
             "B = 0 por construcción y este control no puede variar. Cómo leer el §7 lo decide Nicolás"
             % (cuenta["SIN SUSTRATO"], n, "/".join(brazos))
             if n and cuenta["SIN SUSTRATO"] == n else "puede variar")
    return {"n": n, "brazos": brazos, "gana_o_empate": ge, "sin_sustrato": ss, "otros": 1.0 - ge - ss,
            "por_estado": dict(cuenta), "poder": poder}


def lectura_b(filas, brazo):
    """§5.4 (informa): por volcán, recall de protegidas y bajo 1 MW, tasa en negativos limpios con Wilson, razón."""
    wilson = sys.modules["evaluar_v375e_retro"].wilson
    out = {}
    for v in sorted({f["vol"] for f in _ev(filas)}):
        fv = [f for f in _ev(filas) if f["vol"] == v]
        fila = {}
        for b in (brazo, "K"):
            pr = [f for f in fv if f["lab"] == "protegida"]
            bj = [f for f in fv if f["lab"] == "bajo1"]
            ng = [f for f in fv if f["lab"] == "neg_limpio"]
            k = sum(_pub(f, b) for f in ng)
            rr = [_mag(f, b) / f["vrp_mirova"] for f in pr + bj if _pub(f, b) and _mag(f, b) > 0
                  and (f.get("vrp_mirova") or 0) > 0]
            fila[b] = {"protegidas": [sum(_pub(f, b) for f in pr), len(pr)],
                       "perdidas": [(f["dt"], f["sensor"]) for f in pr if not _pub(f, b)],
                       "bajo1": [sum(_pub(f, b) for f in bj), len(bj)], "neg_limpio": [k, len(ng)],
                       "wilson_neg": wilson(k, len(ng)) if ng else None,
                       "razon_mediana": statistics.median(rr) if rr else None}
        out[v] = fila
    return out


def noche_operador(filas, brazo):
    """§5.5 (informa): ¿publica algo el tablero en las noches con protegida? ¿calla en las limpias?"""
    por = collections.defaultdict(list)
    for f in filas:
        if f["estado"] != "sobra_en_via":
            por[(f["vol"], f["noche"])].append(f)
    out = {b: {"protegidas_con_publicacion": [0, 0], "limpias_calladas": [0, 0]} for b in (brazo, "K")}
    for fs in por.values():
        ev = [f for f in fs if f.get("_evaluable")]
        if len(ev) != len(fs):
            continue
        prot = any(f.get("lab") == "protegida" for f in ev)
        limpia = ev and all(f.get("lab") == "neg_limpio" for f in ev)
        for b in (brazo, "K"):
            alguna = any(_pub(f, b) for f in ev)
            if prot:
                out[b]["protegidas_con_publicacion"][1] += 1
                out[b]["protegidas_con_publicacion"][0] += alguna
            if limpia:
                out[b]["limpias_calladas"][1] += 1
                out[b]["limpias_calladas"][0] += not alguna
    return out


def es_pasada_b(f):
    for vol, b, h in PASADAS_B:
        if f["vol"] == vol and (b is None or f["b"] == b) and abs((_dt(f["dt"]) - _dt(h)).total_seconds()) <= VENTANA_S:
            return True
    return False


# ---------------------------------------------------------------- veredicto (§8.1)
def veredicto(sensor, regla, controles, extra):
    """Primera fila que se cumpla. `regla` trae `_fila_regla` (2, 3, 4, 5 o 6) de la regla del sensor; `extra` las
    condiciones de la fila 4 que no salen de la regla (OSF, sólo OCR, curva, sin (b), cercano contra radiante, V750-A)
    y la de la fila 2 por C-cobertura."""
    rojos = {k: v for k, v in controles.items() if not str((v or {}).get("estado", v)).startswith("OK")}
    if rojos:
        return 1, NOMBRES_FILA[1], sorted(rojos)
    if extra.get("protegidas_sin_dato"):
        return 2, NOMBRES_FILA[2] + " " + str(extra["protegidas_sin_dato"][:5]), extra["protegidas_sin_dato"]
    f = regla["_fila_regla"]
    if f == 2:
        return 2, NOMBRES_FILA[2] + " " + str(regla.get("perdidas_tabla") or regla.get("P1_veto")), []
    if f == 3:
        return 3, NOMBRES_FILA[3], []
    motivos4 = [k for k, v in extra.items() if k != "protegidas_sin_dato" and v]
    if f == 4 or motivos4:
        return 4, NOMBRES_FILA[4], motivos4 + (["regla del sensor"] if f == 4 else [])
    if f == 5:
        return 5, NOMBRES_FILA[5], []
    return 6, NOMBRES_FILA[6], []


def nombre_fila6(filas, osf_res, sensor):
    al = sorted({f["vol"] for f in _ev(filas) if f["lab"] == "protegida"} |
                {v for v, n in ((osf_res or {}).get("por_sensor", {}).get(sensor, {}).get("por_volcan") or {}).items() if n})
    si = sorted({f["vol"] for f in _ev(filas) if f["lab"] == "neg_limpio"})
    sat = " F26-V: NOAA-20 y Suomi NPP oblicuo" if sensor != "MODIS" else ""
    return f"{NOMBRES_FILA[6]} (alertas: {', '.join(al) or 'ninguno'}; silencio: {', '.join(si) or 'ninguno'};{sat})"


def leer_sensor(R, filas_todas, sensor, controles_comunes, predicado, v750a_sellado, caja_v750=None,
                posicion_v750="radiante", osf_res=None, filas_r25=None, separa_v750=None):
    """El veredicto de un sensor: la regla en su tramo que decide, los controles, las condiciones de la fila 4 y lo que
    informa. `filas_todas` son las filas del sensor ya con `_t`."""
    tramo = TRAMO_DECIDE[sensor]
    filas = [f for f in filas_todas if f["b"] == sensor and f["tramo"] == tramo]
    brazo = {"MODIS": "V", "VIIRS375": "V-cercano", "VIIRS750": BRAZO_DE[posicion_v750]}[sensor]
    regla = regla_sensor(R, filas, sensor, brazo, v750a_sellado)
    ctl = dict(controles_comunes)
    ctl["c_via"] = c_via(filas, tramo)
    ctl["c_cobertura"] = c_cobertura(filas, [k for k in controles_comunes.get("_repetidas", ()) if bucket(k[1]) == sensor])
    dm = [f for f in filas_todas if f["b"] == sensor and f["tramo"] == "DM"]
    if dm:
        ctl["c_via_dm"] = c_via(dm, "DM")
    ctl["c_placebo"] = c_placebo(R, filas, sensor, brazo, v750a_sellado, separa_v750)
    ctl["nulo_lector"] = nulo_lector(R, filas, sensor, brazo, predicado, v750a_sellado)
    if sensor == "VIIRS750":
        malas = [(f["vol"], f["dt"]) for f in filas_todas if f["b"] == "VIIRS750" and f.get("_evaluable")
                 and ((f["via_rec"] or {}).get("diag_codigo_mirova") or {}).get("roi") != caja_v750]
        ctl["c_montaje_caja_v750"] = ({"estado": "ROJO: caja de VIIRS 750 no declarada (L2)"} if caja_v750 is None else
                                      {"estado": "OK" if not malas else f"ROJO: {len(malas)} records con otra caja",
                                       "caja": caja_v750, "distintas": malas[:20]})
    if osf_res is not None:
        ctl["c_pareo_osf"] = {"estado": osf_res["c_pareo"]}
        # VPR946-01: C-cenit es un control del §6; §8.1 fila 1 manda INDECIDIBLE si cae (se calculaba y no llegaba)
        ctl["c_cenit_osf"] = {"estado": osf_res["c_cenit"], "n_pares": osf_res["n_pares_cenit"]}
        # VPR940-10 (aprobado): la vía publica una protegida OSF que K no publica; no puede ocurrir (K publica todas,
        # §5.2), es un defecto del lector y va a la fila 1, no a la 4
        dfc = osf_res["por_sensor"][sensor]["defecto"]
        ctl["c_defecto_lector_osf"] = {"estado": "OK" if not dfc else f"ROJO: {len(dfc)} protegidas OSF que la vía "
                                                                        "publica y K no (defecto del lector)",
                                       "lista": dfc[:20]}
        if filas_r25 is not None:
            r25s = [f for f in filas_r25 if f["b"] == sensor]
            ctl["c_via_r25"] = c_via(r25s, "R25")
            ctl["c_cobertura_r25"] = c_cobertura(r25s, clave="lab_osf", clases=("protegida_osf",))   # VPR940-09
    extra = {"protegidas_sin_dato": [x for x in protegidas_sin_dato_que_k_publica(filas)]}
    extra["solo_ocr_que_k_publica"] = solo_ocr_perdidas(filas, brazo, n3=sensor != "MODIS")
    cur = curva_cenit(R, filas, brazo)
    cur["controles_cenit"] = controles_cenit(R, filas, brazo)
    # VPR946-01: los controles de cenit del §6 entran al veredicto (§8.1 fila 1). SIN SUSTRATO (la curva no tiene
    # pares) no es un control caído: no hay curva que leer, y la fila 4 por la curva tampoco se activa.
    _ec = cur["controles_cenit"]["estado"]
    ctl["controles_cenit"] = {"estado": "OK (sin sustrato: la curva no se lee)" if _ec == "SIN SUSTRATO" else _ec,
                              "detalle": cur["controles_cenit"]}
    extra["curva_cae_mas_que_mirova"] = (cur["controles_cenit"]["estado"] == "OK"
                                         and cur[brazo]["razon_doble"].get("veredicto") == "CAE MAS QUE MIROVA")
    if osf_res is not None:
        extra["candidatas_osf"] = osf_res["por_sensor"][sensor]["candidatas"]
    sin_b = [f for f in filas if not es_pasada_b(f)]
    regla_sin_b = regla_sensor(R, sin_b, sensor, brazo, v750a_sellado)
    extra["cambia_sin_pasadas_b"] = (regla_sin_b["_fila_regla"] != regla["_fila_regla"])
    otros = {}
    if sensor == "VIIRS375":
        rad = regla_v375(R, filas, "V")
        otros["radiante"] = {k: v for k, v in rad.items() if k != "criterios"}
        extra["cercano_y_radiante_difieren"] = rad["_fila_regla"] != regla["_fila_regla"]
    if sensor == "VIIRS750":
        extra["v750a_no_sellado"] = not v750a_sellado
    otros["sorteo_etiquetas"] = sorteo_etiquetas(R, filas)
    if sensor == "MODIS":
        m3 = [f for f in filas_todas if f["b"] == "MODIS" and f["tramo"] == "F26-M3"]
        otros["control_f26_m3"] = ({k: v for k, v in regla_modis(R, m3, brazo).items()} if _ev(m3) else "sin pasadas")
    if osf_res is not None:
        extra["candidatas_osf_sin_pasadas_b_informa"] = []      # informa: las candidatas que quedan sin (b)
        for c in extra["candidatas_osf"]:
            if not any(c[0] == v and (bb is None or bb == sensor) and abs((_dt(c[1]) - _dt(h)).total_seconds()) <= VENTANA_S
                       for v, bb, h in PASADAS_B):
                extra["candidatas_osf_sin_pasadas_b_informa"].append(c)
    ctl = {k: v for k, v in ctl.items() if not k.startswith("_")}
    fila, nombre, motivos = veredicto(sensor, regla, ctl, {k: v for k, v in extra.items()
                                                            if not k.endswith("_informa")})
    if fila == 6:
        nombre = nombre_fila6(filas, osf_res, sensor)
    return {"sensor": sensor, "tramo": tramo, "brazo": brazo, "fila": fila, "veredicto": nombre, "motivos": motivos,
            "regla": {k: v for k, v in regla.items()}, "regla_sin_pasadas_b": regla_sin_b["_fila_regla"],
            "controles": ctl, "extra": extra, "otros_brazos": otros, "curva_cenit": cur,
            "lectura_b": lectura_b(filas, brazo), "noche_operador": noche_operador(filas, brazo),
            "n_pasadas": len(filas), "n_evaluables": len(_ev(filas)),
            "etiquetas": dict(collections.Counter(f.get("lab") for f in _ev(filas)))}


# ---------------------------------------------------------------- E/S
def _predicado_por_defecto(R):
    return R.F4.predicado_node


def main(argv=None, predicado=None, reglas=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", required=True)
    ap.add_argument("--k", required=True)
    ap.add_argument("--kgemelo")
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--osf")
    ap.add_argument("--caja-v750", default=None, help="ROI de VIIRS 750 que eligió V750-B (sin valor por defecto, L2)")
    ap.add_argument("--v750a-sellado", required=True, choices=("si", "no"))
    ap.add_argument("--posicion-v750", default="radiante", choices=("radiante", "cercano", "pico"),
                    help="la del §6 bis de V750-A si corrió; si no, radiante (R-3)")
    ap.add_argument("--separa-v750", default=None, choices=sorted(DEFINICIONES_SEPARA_V750),
                    help="definición de «el comparador separa» (VPR940-01); la fija V750-A al sellarse; sin valor por "
                         "defecto: con V750-A sellado y sin ella, el placebo de 750 queda en rojo")
    ap.add_argument("--montaje", help="resultado externo de C-montaje en DM (L3)")
    ap.add_argument("--excepciones-ck", help="lista nombrada antes de leer F26 (R-15)")
    ap.add_argument("--sin-dato-trozos", help="trozos que fallaron dos veces: [{vol, start, end}]")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--manifiesto")
    g.add_argument("--ensayo", action="store_true", help="sin candado: la salida dice ENSAYO y no decide")
    ap.add_argument("--salida")
    a = ap.parse_args(argv)
    R = reglas or Reglas()
    predicado = predicado or _predicado_por_defecto(R)
    import banco_paridad as bp
    import yaml
    from referencia_mirova_unificada import cargar_referencia_unificada
    leer = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if p else None   # noqa: E731
    sin_dato_trozos = leer(a.sin_dato_trozos) or []
    print("PRIMERA LÍNEA: trozos SIN DATO (fallaron dos veces):", sin_dato_trozos or "ninguno")
    avisos = []
    if not a.osf:                                                   # VPR940b-08
        avisos.append("R25 sin OSF: no se lee (sin --osf no hay P1-OSF, C-pareo, C-cenit ni C-cobertura de R25)")
    refs = rutas_referencias((a.cons, a.ocr, a.osf))               # §11: las referencias también van al manifiesto
    cand =({"estado": "OK (ENSAYO: sin candado, NO DECIDE)"} if a.ensayo else
            candado(leer(a.manifiesto), requeridos=REQUERIDOS_MANIFIESTO + tuple(refs)))
    via, rep_v = cargar_carpeta(a.via)
    k, rep_k = cargar_carpeta(a.k)
    kg, _ = cargar_carpeta(a.kgemelo)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    es_noche = lambda vol, b, dt: not bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt)  # noqa: E731
    filas = armar_pasadas(via, k, kg, es_noche, inner, sin_dato_trozos)
    no_r25 = [f for f in filas if f["tramo"] != "R25"]
    ref = cargar_referencia_unificada(Path(a.cons), Path(a.ocr))
    etiquetar_tabla(no_r25, ref, coords)
    sin_pasada = alertas_sin_pasada(no_r25, ref, coords)
    for f in filas:
        f.setdefault("lab", "sin_info")
        f.setdefault("vrp_mirova", None)
    tabla_publica(R, filas, predicado)
    volc = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    osf_res = p1_osf(filas, leer_osf(a.osf, volc, es_noche)) if a.osf else None
    excepciones = leer(a.excepciones_ck) or []
    comunes = {"candado": cand, "_repetidas": rep_v + rep_k, "c_k_puro": c_k_puro(filas),
               "c_k": c_k(filas, excepciones, TIER_A, sobras_kgemelo(kg, k)),
               "nulo_runner": nulo_runner(R, filas, excepciones),
               "c_montaje": validar_montaje(leer(a.montaje))}
    out = {"preregistro": "experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md @ s173-prereg-retro-sellado",
           "ensayo": bool(a.ensayo), "sin_dato_trozos": sin_dato_trozos, "avisos": avisos,
           "pasadas_por_tramo": dict(collections.Counter((f["tramo"], f["b"], f["estado"].split(":")[0]) for f in filas).items()),
           "sensores": {}}
    out["pasadas_por_tramo"] = {"|".join(k): v for k, v in out["pasadas_por_tramo"].items()}
    codigo = 0
    for x in avisos:
        print("AVISO:", x)
    separa = DEFINICIONES_SEPARA_V750[a.separa_v750] if a.separa_v750 else None
    for s in SENSORES:
        r = leer_sensor(R, filas, s, comunes, predicado, a.v750a_sellado == "si", a.caja_v750, a.posicion_v750,
                        osf_res, [f for f in filas if f["tramo"] == "R25"], separa)
        out["sensores"][s] = r
        pref = "ENSAYO (NO DECIDE) " if a.ensayo else ""          # VPR940-15
        print(f"{pref}{s}: fila {r['fila']} | {r['veredicto']} | motivos {r['motivos']}")
        print(f"{pref}{s}, sorteo de etiquetas del §7 (informa): {r['otros_brazos']['sorteo_etiquetas']['poder']}")
        codigo = max(codigo, 3 if r["fila"] == 1 else 0)
    out["osf"] = osf_res
    out["alertas_de_la_tabla_sin_pasada_nuestra"] = sin_pasada
    if a.salida:
        Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
