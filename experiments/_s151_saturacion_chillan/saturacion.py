# -*- coding: utf-8 -*-
"""Tarea 1.18 del loop: logica local del conteo de pixeles saturados en el L1B (sin red, sin HDF4).

POR QUE. Un pixel muy caliente satura el sensor y nuestro pipeline lo BORRA (lo deja en NaN) antes de
detectar. Un pixel borrado no aparece en `t_max_k` de nuestros JSON, asi que el JSON no distingue "no
saturo" de "saturo y se borro" (docs/audit_s150/VERIFICADOR_AUDITORIA.md:205-206). La unica forma de
saberlo es leer el L1B. Este modulo hace tres cosas y no decide nada:

  1. compara, pixel a pixel, la lectura cruda del L1B con la lectura de PRODUCCION (las funciones
     `read_*` del pipeline, llamadas, no copiadas): "borrado" = el L1B trae un valor y produccion
     devuelve NaN. Lo separa por motivo: bit de saturacion de calidad (VIIRS, bit 2 = 4, segun la cita de
     pipeline/process_viirs.py:366-372, Tabla C.1 del User Guide del L1B VIIRS; A37: VIIRS no usa
     centinela) o techo del pipeline (BT >= techo - 0,5 K sin el bit); en MODIS, SI = 65533 (D24);
  2. arma un lector "con saturados": la salida de produccion con esos pixeles restituidos a un PISO
     explicito (ver `PISOS`), para correr el MISMO `calculate_vrp` y ver cuanto cambia la magnitud;
  3. una cota aditiva independiente del detector: k * A * (L(piso) - L(t_bg)) por pixel MIR borrado
     dentro del radio interior, con el k y el A del modulo del pipeline.

PISO DEL PIXEL SATURADO (lo pide la tarea: "propon un valor de piso explicito, el techo del sensor").
Un pixel saturado esta, por definicion, AL MENOS en el techo del sensor: su radiancia real es mayor o
igual. Por eso el techo es un piso de su energia, no una estimacion.
  - VIIRS I04 / I05 y M13 / M15: el maximo de la LUT de temperatura de brillo DEL PROPIO GRANULO (el
    valor al que el L1B clampea, Tabla C.1). Si el granulo no trae LUT, el techo declarado por el
    pipeline (I04 361,77 K e I05 423,33 K de process_viirs.py:373; M13 634 K y M15 343 K de
    process_viirs_mod.BT_LUT_MAX_MBAND).
  - MODIS B21: 499,9 K, justo bajo `BT_SAT_MIR_K_MODIS` = 500 K del perfil (Coppola 2025 cap. 11
    Tabla 1, segun process_modis.py:557-561), porque la defensa secundaria de calculate_vrp borra lo que
    pase de 500 K. B22 y B31 no tienen techo declarado en el pipeline: piso EMPIRICO = la BT valida mas
    alta de esa banda en el mismo granulo (el sensor llego al menos ahi; es una cota inferior debil).
Ademas, para la cota aditiva se informa un piso empirico de la banda MIR (la BT valida mas alta del
granulo en la escena), que es menor o igual al techo: el par (empirico, declarado) acota por abajo.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

SAT_BIT = 0b100            # bit 2 de *_quality_flags, cita en pipeline/process_viirs.py:366-372
SI_SATURADO_MODIS = 65533  # MODIS L1B C7 UserGuide Tabla 5.6.1 (cita en process_modis.py:240-247)
SI_MAX_VALIDO_MODIS = 32767
# Techos declarados de la banda I (variables LOCALES de read_viirs_l1b, process_viirs.py:373, no
# importables). El test `test_techos_i_coinciden_con_el_pipeline` los lee del fuente y falla si cambian.
TECHO_I_DECLARADO = {"I04": 361.77, "I05": 423.33}
MARGEN_TECHO_K = 0.5       # produccion borra bt >= techo - 0,5 K (process_viirs.py:400-402)
MARGEN_GUARDIA_MODIS_K = 0.1

FAMILIAS = ("V375", "V750", "MODIS")
BANDAS = {"V375": ("I04", "I05"), "V750": ("M13", "M15"), "MODIS": ("B21", "B22", "B31")}
BANDA_MIR = {"V375": "I04", "V750": "M13", "MODIS": "B21"}


# ------------------------------------------------------------------ conteo VIIRS
def bt_cruda_desde_lut(dn, lut, flag_dns):
    """BT del L1B sin ninguna defensa de saturacion: LUT, centinelas DN y relleno de la LUT a NaN."""
    bt = np.asarray(lut)[np.asarray(dn)].astype(np.float32)
    bt[np.isin(dn, list(flag_dns))] = np.nan
    bt[bt < 0] = np.nan
    return bt


def techo_lut(lut) -> float:
    lut = np.asarray(lut, dtype=np.float64)
    v = lut[np.isfinite(lut) & (lut > 0)]
    return float(v.max()) if v.size else float("nan")


def mascaras_borrado(bt_cruda, bt_prod, qf):
    """Pixeles que el L1B trae y produccion borra, separados por motivo.

    Devuelve dict de mascaras booleanas: `borrado` (todos), `bit` (con el bit de saturacion) y
    `techo` (sin el bit: los borro la defensa secundaria del techo del pipeline).
    """
    borrado = np.isfinite(bt_cruda) & ~np.isfinite(bt_prod)
    if qf is None:
        bit = np.zeros_like(borrado)
    else:
        bit = borrado & ((np.asarray(qf) & SAT_BIT) != 0)
    return {"borrado": borrado, "bit": bit, "techo": borrado & ~bit}


def leer_viirs_crudo(path, bandas, flag_dns):
    """Por banda: BT cruda, quality flags y techo de la LUT del granulo. Solo h5py."""
    import h5py
    out = {}
    with h5py.File(path, "r") as f:
        obs = f["observation_data"]
        for b in bandas:
            if b not in obs:
                continue
            dn = obs[b][:]
            qf = obs[b + "_quality_flags"][:] if (b + "_quality_flags") in obs else None
            lk = b + "_brightness_temperature_lut"
            if lk in obs:
                lut = obs[lk][:]
                out[b] = {"bt": bt_cruda_desde_lut(dn, lut, flag_dns), "qf": qf,
                          "techo_lut": techo_lut(lut), "con_lut": True,
                          "n_bit_total": int(((qf & SAT_BIT) != 0).sum()) if qf is not None else None}
            else:
                # Sin LUT no hay BT cruda comparable; solo se cuenta el bit.
                out[b] = {"bt": None, "qf": qf, "techo_lut": float("nan"), "con_lut": False,
                          "n_bit_total": int(((qf & SAT_BIT) != 0).sum()) if qf is not None else None}
    return out


def techo_banda(familia, banda, crudo_banda):
    """Piso del pixel saturado de una banda VIIRS: techo de la LUT del granulo, o el declarado."""
    t = crudo_banda.get("techo_lut") if crudo_banda else None
    if t is not None and math.isfinite(t):
        return float(t), "lut_del_granulo"
    if familia == "V375":
        return TECHO_I_DECLARADO[banda], "declarado_process_viirs_373"
    from pipeline.process_viirs_mod import BT_LUT_MAX_MBAND
    return float(BT_LUT_MAX_MBAND[banda]), "declarado_BT_LUT_MAX_MBAND"


def bandas_con_saturados(bandas_prod, mascaras, crudo, pisos):
    """Salida de produccion con los pixeles borrados restituidos.

    Con bit de saturacion: max(BT cruda, piso). Sin bit (los borro el techo del pipeline): la BT
    cruda, que es lo que el sensor midio. Lo demas queda identico a produccion.
    """
    out = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in bandas_prod.items()}
    for b, m in mascaras.items():
        if b not in out or crudo.get(b, {}).get("bt") is None:
            continue
        cruda = crudo[b]["bt"]
        a = out[b]
        a[m["techo"]] = cruda[m["techo"]]
        a[m["bit"]] = np.maximum(cruda[m["bit"]], np.float32(pisos[b]))
    return out


# ------------------------------------------------------------------ conteo MODIS
def mascaras_modis(si_banda):
    """SI de una banda emisiva MODIS: saturado (65533) y otros invalidos (> 32767)."""
    si = np.asarray(si_banda)
    sat = si == SI_SATURADO_MODIS
    return {"borrado": sat | (si > SI_MAX_VALIDO_MODIS), "bit": sat,
            "techo": np.zeros_like(sat), "otros_invalidos": (si > SI_MAX_VALIDO_MODIS) & ~sat}


def pisos_modis(datos_prod, roi):
    """Pisos de MODIS en BT (K): B21 bajo la guardia de 500 K; B22 y B31 empiricos del granulo."""
    from pipeline import process_modis as pm
    from pipeline import profile as prof
    pisos = {"B21": float(prof.BT_SAT_MIR_K_MODIS) - MARGEN_GUARDIA_MODIS_K}
    origen = {"B21": "BT_SAT_MIR_K_MODIS menos 0,1 K"}
    for b, key, lam in (("B22", "band22", pm.BAND22_LAMBDA), ("B31", "band31", pm.BAND31_LAMBDA)):
        bt = pm.radiance_to_bt(datos_prod[key], lam)
        v = bt[np.isfinite(bt)]
        pisos[b] = float(v.max()) if v.size else float("nan")
        origen[b] = "empirico: BT valida mas alta del granulo"
    return pisos, origen


def datos_modis_con_saturados(datos_prod, mascaras, pisos):
    """Radiancias de read_modis_l1b con los SI = 65533 restituidos al piso de su banda."""
    from pipeline import process_modis as pm
    lam = {"B21": pm.BAND21_LAMBDA, "B22": pm.BAND22_LAMBDA, "B31": pm.BAND31_LAMBDA}
    key = {"B21": "band21", "B22": "band22", "B31": "band31"}
    out = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in datos_prod.items()}
    for b, m in mascaras.items():
        p = pisos.get(b)
        if p is None or not math.isfinite(p):
            continue
        out[key[b]][m["bit"]] = np.float32(pm.bt_to_radiance(p, lam[b]))
    return out


# ------------------------------------------------------------------ resumenes
def contar(mascaras, regiones):
    """Cuenta por banda, motivo y region (dict nombre -> mascara booleana)."""
    out = {}
    for b, m in mascaras.items():
        out[b] = {reg: {mot: int((m[mot] & r).sum()) for mot in m} for reg, r in regiones.items()}
    return out


def mir_perdido_modis(mascaras, b22_primaria):
    """Donde la banda MIR combinada queda sin valor por saturacion (merge_mir_bands)."""
    b21, b22 = mascaras["B21"]["borrado"], mascaras["B22"]["borrado"]
    perdido = b21 & b22  # con una sola banda valida, merge_mir_bands rellena con la otra
    sat = (mascaras["B21"]["bit"] | mascaras["B22"]["bit"]) & perdido
    return {"borrado": perdido, "bit": sat, "techo": np.zeros_like(sat)}


def cota_aditiva_mw(n_pixeles, piso_k, t_bg_k, lam_um, wooster_k, area_m2):
    """k * A * max(L(piso) - L(t_bg), 0) * n / 1e6. None si falta el fondo."""
    from pipeline.process_modis import bt_to_radiance
    if n_pixeles == 0:
        return 0.0
    if t_bg_k is None or piso_k is None or not (math.isfinite(t_bg_k) and math.isfinite(piso_k)):
        return None
    dl = float(bt_to_radiance(piso_k, lam_um)) - float(bt_to_radiance(t_bg_k, lam_um))
    return round(n_pixeles * area_m2 * wooster_k * max(dl, 0.0) / 1e6, 4)


def bt_max_valida(bt, region):
    v = np.asarray(bt)[region & np.isfinite(bt)]
    return round(float(v.max()), 2) if v.size else None


# ------------------------------------------------------------------ granulos
def hora_granulo(nombre: str) -> Optional[datetime]:
    """Hora de inicio del granulo desde el nombre (A2026271.0125 -> 2026-09-28 01:25)."""
    try:
        p = nombre.split(".")
        return datetime(int(p[1][1:5]), 1, 1) + timedelta(days=int(p[1][5:8]) - 1,
                                                          hours=int(p[2][:2]), minutes=int(p[2][2:4]))
    except Exception:
        return None


def familia_de_plataforma(plataforma: str) -> str:
    if plataforma.startswith("MODIS"):
        return "MODIS"
    return "V750" if plataforma.endswith("_750") else "V375"


PLATAFORMAS = {
    "V375": [("VIIRS_SNPP", "VIIRS_SNPP_L1B", "VIIRS_SNPP_GEO"),
             ("VIIRS_NOAA20", "VIIRS_NOAA20_L1B", "VIIRS_NOAA20_GEO"),
             ("VIIRS_NOAA21", "VIIRS_NOAA21_L1B", "VIIRS_NOAA21_GEO")],
    "V750": [("VIIRS_SNPP_750", "VIIRS_SNPP_MOD_L1B", "VIIRS_SNPP_MOD_GEO"),
             ("VIIRS_NOAA20_750", "VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA20_MOD_GEO"),
             ("VIIRS_NOAA21_750", "VIIRS_NOAA21_MOD_L1B", "VIIRS_NOAA21_MOD_GEO")],
    "MODIS": [("MODIS_TERRA", "MODIS_TERRA_L1B", "MODIS_TERRA_GEO"),
              ("MODIS_AQUA", "MODIS_AQUA_L1B", "MODIS_AQUA_GEO")],
}


def dias_del_tramo(desde: str, hasta: str, tramo: int, n_tramos: int) -> list[str]:
    """Reparte los dias [desde, hasta] en n tramos contiguos casi iguales; devuelve el tramo i."""
    d0 = datetime.strptime(desde, "%Y-%m-%d")
    d1 = datetime.strptime(hasta, "%Y-%m-%d")
    dias = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((d1 - d0).days + 1)]
    cortes = np.array_split(np.arange(len(dias)), n_tramos)
    return [dias[i] for i in cortes[tramo]]
