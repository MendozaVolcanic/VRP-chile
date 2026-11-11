# -*- coding: utf-8 -*-
"""Adaptadores y comparadores de C-montaje por A/B (S178, opción A aprobada por Nicolás el 2026-11-10; declaración en
experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md de la rama loop/activo, commit c592ac2d2, escrita antes de correr).

POR QUÉ, COMO GEÓLOGO. C-montaje pregunta si la vía que corrió en la retrospectiva (D2) ve en la quincena DM lo mismo
que se midió en los tres A/B: las mismas celdas encendidas alrededor del cráter, el mismo VRP y, en MODIS, la misma
clase de distancia. Si no, lo que se lea en febrero, marzo y 2025 sería de otra vía. Los A/B guardaron sus resultados
en formatos propios (MOD-D: líneas jsonl con el record de la vía, `v_slim`; V375-E: el port `C13` sobre las grillas;
V750-B: el oráculo por brazo); este módulo los lleva a una sola forma y compara pasada por pasada, sin tocar los datos.

QUÉ NO HACE: no ensancha tolerancias (el pipeline redondea el VRP a 0,001 MW: ninguna tolerancia más fina tiene
sentido, y ninguna más gruesa está permitida) ni explica diferencias salvo por otro gránulo; la explicación por hunk
exige re-correr la pasada con el código del tag de origen y se escribe a mano después.
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

TOL_VRP = 1e-3
DM = ("2026-10-01", "2026-10-16")
_GRAN = re.compile(r"(MOD|MYD|VNP|VJ1|VJ2)\w*?\.A(\d{7})\.(\d{4})")
_PLAT = {"MOD": "TERRA", "MYD": "AQUA", "VNP": "SNPP", "VJ1": "NOAA20", "VJ2": "NOAA21"}
SENSIBLES_B4 = ("PuyehueCordonCaulle", "Tupungatito")   # scripts/roi_v750b_a_grillas.py (lo ata una prueba)


def identidad_granulo(nombre):
    """(satélite, AAAADDD, HHMM) de un nombre de gránulo, sin producto ni versión de proceso; None si no se lee."""
    m = _GRAN.search(str(nombre or ""))
    return (m.group(1), m.group(2), m.group(3)) if m else None


def plataforma_de_sensor(sensor):
    s = str(sensor or "").upper()
    for p in ("TERRA", "AQUA", "SNPP", "NOAA20", "NOAA21"):
        if p in s:
            return p
    return None


def familia_de_sensor(sensor):
    s = str(sensor or "").upper()
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def nombre_sensor(familia, plataforma):
    """El nombre de sensor del pipeline (el que leer_retro.bucket reconoce)."""
    return {"MODIS": "MODIS_%s", "VIIRS375": "VIIRS_%s", "VIIRS750": "VIIRS_%s_750"}[familia] % plataforma


def en_dm(hora):
    return DM[0] <= str(hora)[:10] <= DM[1]


def clave(vol, familia, plataforma, hora):
    return (vol, familia, plataforma, str(hora)[:16])


def _vrp(x):
    return float(x or 0.0)


# ------------------------------------------------------------------------------------------------- la vía de D2
def ref_de_record(rec):
    """Lo que se compara de un record de la vía de D2."""
    pc = rec.get("primary_cluster") or {}
    pix = rec.get("anomaly_pixels") or []
    fam = familia_de_sensor(rec.get("sensor"))
    if fam == "MODIS":
        celdas = {(round(float(p["lat"]), 5), round(float(p["lon"]), 5)) for p in pix}
    else:
        celdas = {(int(p["fila"]), int(p["col"])) for p in pix}
    return {"vrp": _vrp(pc.get("vrp_mw")), "celdas": celdas, "dc": rec.get("distance_class"),
            "granulo": identidad_granulo(rec.get("granule"))}


def indexar_via(via):
    """`via` = {(vol, sensor, datetime_utc): record} (leer_retro.cargar_carpeta) -> {clave: ref} en DM."""
    out = {}
    for (vol, sensor, dt), rec in via.items():
        if not dt or not en_dm(dt):
            continue
        fam = familia_de_sensor(sensor)
        if fam:
            out[clave(vol, fam, plataforma_de_sensor(sensor), dt)] = ref_de_record(rec)
    return out


# ------------------------------------------------------------------------------------------------- los tres A/B
def cargar_modd(lineas):
    """MOD-D fase 4, brazo V: líneas de pasada (`tipo` distinto de cabecera) con `v_slim`. Devuelve {clave: ref}."""
    out = {}
    for d in lineas:
        if d.get("tipo") == "cabecera" or not en_dm(d.get("dt", "")):
            continue
        v = d.get("v_slim")
        if v is None:
            continue
        r = ref_de_record(dict(v, sensor=d.get("sensor")))
        r["granulo"] = identidad_granulo(v.get("granule") or d.get("l1b_usado"))
        out[clave(d["vol"], "MODIS", plataforma_de_sensor(d.get("sensor")), d["dt"])] = r
    return out


def _celdas_pix(pixeles):
    return {(int(p[0]), int(p[1])) for p in (pixeles or [])}


def _clave_viirs(e, fam):
    g = identidad_granulo(e.get("granule") or " ".join(e.get("archivos") or []))
    return clave(e["volcan"], fam, _PLAT.get(g[0]) if g else None, e["hora_utc"]), g


def cargar_v375e(entradas):
    """V375-E: el port C13 de cada pasada en DM."""
    out = {}
    for e in entradas:
        if not en_dm(e.get("hora_utc", "")):
            continue
        c = (e.get("port") or {}).get("C13")
        if c is None:
            continue
        k, g = _clave_viirs(e, "VIIRS375")
        # S178, decisión de Nicolás («Sí, opción 1», post hoc): la banda de triangulación del port, como en V750
        out[k] = {"vrp": _vrp(c.get("vrp_mw")), "banda": c.get("vrp_banda"), "celdas": _celdas_pix(c.get("pixeles")),
                  "dc": None, "granulo": g}
    return out


def brazo_b4(vol):
    return "B1" if vol in SENSIBLES_B4 else "B0"


def cargar_v750b(entradas, tag=None):
    """V750-B con B4: el oráculo B1 en Cordón Caulle y Tupungatito, B0 en los otros nueve."""
    out = {}
    for e in entradas:
        if not en_dm(e.get("hora_utc", "")):
            continue
        o = (e.get("oraculo") or {}).get(brazo_b4(e["volcan"]))
        if o is None:
            continue
        k, g = _clave_viirs(e, "VIIRS750")
        out[k] = {"vrp": _vrp(o.get("vrp_mw")), "banda": o.get("vrp_banda"), "celdas": _celdas_pix(o.get("pixeles")),
                  "dc": None, "granulo": g, "tag": tag}
    return out


# ------------------------------------------------------------------------------------------------- comparación
def _dist_vrp(v, ref):
    b = ref.get("banda")
    if b and len(b) == 2 and b[0] is not None and b[1] is not None:
        lo, hi = float(b[0]), float(b[1])
        return 0.0 if lo <= v <= hi else min(abs(v - lo), abs(v - hi))
    return abs(v - ref["vrp"])


def comparar(via_idx, refs, origen, comparar_dc=False):
    """Sólo las pasadas que el A/B midió. Una diferencia trae `explicada_por` = otro_granulo si el gránulo de D2 no es
    el del A/B; si no, None (se explica sólo con un hunk re-corrido, a mano)."""
    difs = []
    for k in sorted(refs, key=lambda x: tuple(str(y) for y in x)):
        ref, v = refs[k], via_idx.get(k)
        p = "%s|%s|%s" % (k[0], nombre_sensor(k[1], k[2]), k[3])
        campos = []
        if v is None:
            campos.append("falta_en_via")
        else:
            if v["celdas"] != ref["celdas"]:
                campos.append("celdas")
            if _dist_vrp(v["vrp"], ref) > TOL_VRP:
                campos.append("vrp_mw")
            if comparar_dc and v["dc"] != ref["dc"]:
                campos.append("distance_class")
        if not campos:
            continue
        otro = v is not None and v["granulo"] != ref["granulo"]
        d = {"origen": origen, "pasada": p, "campos": campos, "explicada_por": "otro_granulo" if otro else None,
             "via": None if v is None else {"vrp": v["vrp"], "n_celdas": len(v["celdas"]), "dc": v["dc"],
                                            "granulo": v["granulo"]},
             "ab": {"vrp": ref["vrp"], "banda": ref.get("banda"), "n_celdas": len(ref["celdas"]), "dc": ref.get("dc"),
                    "granulo": ref["granulo"]}}
        if ref.get("tag"):
            d["tag_ab"] = ref["tag"]
        difs.append(d)
    return difs


# ------------------------------------------------------------------------------------------------- lectura de disco
def leer_jsonl(rutas):
    for r in rutas:
        with open(r, encoding="utf-8") as fh:
            for linea in fh:
                if linea.strip():
                    yield json.loads(linea)


def leer_resultados(carpetas, patron="resultados_*.json"):
    for c in carpetas:
        for f in sorted(glob.glob(str(Path(c) / "**" / patron), recursive=True)):
            yield from json.loads(Path(f).read_text(encoding="utf-8"))
