# -*- coding: utf-8 -*-
"""Clase de intensidad de una alerta de MIROVA y definicion de "alerta protegida" (tarea 0.2 del loop).

POR QUE. El criterio de victoria de la replica (Nicolas, 2026-10-13; `tasks/LOOP_OBJETIVOS.md` §1.2) no
acepta perder ninguna alerta que MIROVA clasifique de "Bajo" para arriba. Hacia falta saber que mide esa
clase antes de usarla, porque en el CSV hay "Bajo" de 0,04 MW.

Lo que se establecio (detalle y fuentes en `docs/S151_CRITERIO_CLASE_MIROVA.md`):
- La columna `Clasificacion Mirova` la calcula el scraper de Mirova-v1 desde el VRP de la pasada
  (`volcanes.py:63`), no MIROVA. Cambio de escala en el tiempo: en el consolidado es coherente con el VRP
  desde febrero de 2026 y en el OCR desde julio; antes trae etiquetas de escalas retiradas.
- El banner de la imagen (`Nivel_Anomalia_MIROVA`, unico campo que si viene de MIROVA) es por pasada y
  separa sin error VERY_LOW (0,05 a 0,91 MW) de LOW (1,00 a 8,00 MW). Es lo que sostiene el corte de 1 MW:
  Coppola 2016a fig. 11 se contradice entre su pie (Low bajo 1 MW) y su figura (Low bajo 10 MW).

Definicion operativa (lectura A): una PASADA es "alerta protegida" si tiene una fila de alerta
(consolidado u OCR) con VRP_MW de 1 MW o mas, RECALCULADO desde el VRP, nunca leido de la columna.
Lectura B (decision D-4 de Nicolas, pendiente): toda pasada con VRP de 1 MW o mas, aunque el scraper la
llame FALSO_POSITIVO por estar fuera de su radio.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple, Optional

ROOT = Path(__file__).resolve().parents[1]
SNAP_OCR = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_ocr.csv"
SNAP_CONS = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"

UMBRAL_PROTEGIDA_MW = 1.0
TIPOS_ALERTA = ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR")


def clase_por_vrp(vrp_mw: Optional[float]) -> str:
    """Escala de MIROVA con los nombres del sitio actual en castellano (igual que el scraper hoy)."""
    if vrp_mw is None or vrp_mw <= 0:
        return "NULO"
    if vrp_mw < 1:
        return "Muy Bajo"
    if vrp_mw < 10:
        return "Bajo"
    if vrp_mw < 100:
        return "Moderado"
    if vrp_mw < 1000:
        return "Alto"
    return "Muy Alto"


def alerta_protegida(fila: dict, umbral: float = UMBRAL_PROTEGIDA_MW, lectura: str = "A") -> bool:
    """Fila normalizada (`tipo`, `vrp_mw`, como las de referencia_mirova_unificada).

    Lectura A: alerta del scraper con VRP >= umbral. Lectura B: cualquier fila con VRP >= umbral salvo
    RUTINA (incluye FALSO_POSITIVO, calor que MIROVA ve fuera del radio del scraper).
    """
    v = fila.get("vrp_mw")
    if v is None or v < umbral:
        return False
    if lectura == "A":
        return fila.get("tipo") in TIPOS_ALERTA
    if lectura == "B":
        return fila.get("tipo") != "RUTINA"
    raise ValueError(lectura)


def clave_pasada(fila: dict) -> tuple:
    """Una pasada es (volcan, sensor, hora al minuto): junta la fila del consolidado y la del OCR."""
    return (fila["volcano"], fila["sensor_bucket"], fila["fecha_utc"][:16])


# ---------------------------------------------------------------------------------------------------------
# Decision D-9 (issue #811, Nicolas, 2026-10-15): las alertas de 0,05 MW o menos.
#
# POR QUE. Un pixel VIIRS de 375 m que mira una fumarola o un domo tibio deja una senal de centesimas de MW.
# MIROVA la publica en su tabla, pero el banner de su imagen dice NONE ("sin anomalia") en las 14 pasadas
# observadas de 0,04 MW o menos y VERY LOW en las 283 de 0,06 o mas; en 0,05 exacto sale de los dos lados
# (5 y 5), por el paso de dos decimales del valor publicado (experiments/_s151_alertas_minimas/README.md §2).
# El scraper de Mirova-v1 llama ALERTA a todo VRP mayor que cero: sin esta regla, 155 pasadas que MIROVA dice
# no ver entraban como alertas del criterio de victoria.
#
# Modos (Nicolas pidio probarlos todos, asi que cada evaluacion informa los tres):
#   SN        (decidido, por defecto) "MIROVA no vio nada": las filas de alerta de la pasada minima pasan a
#             RUTINA con VRP 0. Re-etiquetada, la pasada y las otras de esa noche pueden volverse negativo
#             limpio. Es la letra de la regla 3 del criterio de victoria (docs/MISSION.md).
#   SE        estrato aparte: las filas pasan a TIPO_MINIMA_SE, que sigue empezando por "ALERTA" (la noche no
#             cambia) y que el etiquetador marca "minima": no cuenta ni como alerta ni como negativo.
#   original  la etiqueta del scraper (lo de antes de D-9).
# 0,05 exacto: el estudio lo dejo abierto (5 NONE y 5 VERY LOW). Se aplica SN con 0,05 incluido
# (UMBRAL_MINIMA_MW) y se informa la variante con umbral 0,04, que deja las de 0,05 como alerta.
# Solo VIIRS 375: la frontera de VIIRS 750 descansa en una imagen por lado y MODIS no tiene alertas bajo 0,13.
UMBRAL_MINIMA_MW = 0.05
UMBRAL_MINIMA_VARIANTE_MW = 0.04
SENSORES_MINIMA = ("VIIRS375",)
MODOS_MINIMAS = ("SN", "SE", "original")
MODO_MINIMAS = "SN"
TIPO_MINIMA_SE = "ALERTA_MINIMA_SE"


class ReglaMinimas(NamedTuple):
    filas: list            # filas listas para etiquetar (copias donde cambio algo)
    minimas: set           # claves de pasada (clave_pasada) que la regla toca, en cualquier modo


def es_alerta_minima(vrp_mw: Optional[float], sensor: str, umbral_mw: float = UMBRAL_MINIMA_MW) -> bool:
    """VRP de una pasada de alerta que MIROVA llama NONE en su banner. El 1e-9 absorbe el float de 0,05."""
    return sensor in SENSORES_MINIMA and vrp_mw is not None and vrp_mw <= umbral_mw + 1e-9


def aplicar_regla_minimas(filas, modo: str = MODO_MINIMAS, umbral_mw: float = UMBRAL_MINIMA_MW) -> ReglaMinimas:
    """Unica implementacion de la regla D-9, sobre filas normalizadas de la referencia (referencia_mirova_unificada).

    El VRP de la pasada es el de su fila de alerta del consolidado si existe, si no el del OCR: el mismo orden
    que usa el evaluador (`experiments/_s146_ab_sin_test1/evaluar.py::anotar_vrp_mirova`), para que el umbral
    corte las mismas pasadas que el evaluador ve. Las protegidas (1 MW o mas) nunca son minimas.
    """
    if modo not in MODOS_MINIMAS:
        raise ValueError("modo %r: tiene que ser uno de %s" % (modo, MODOS_MINIMAS))
    por_pasada = defaultdict(list)
    for f in filas:
        if f.get("tipo") in TIPOS_ALERTA and f.get("vrp_mw") is not None:
            por_pasada[clave_pasada(f)].append(f)
    minimas = set()
    for k, fs in por_pasada.items():
        vrp = sorted(fs, key=lambda f: f.get("source") != "CONS")[0]["vrp_mw"]
        if es_alerta_minima(vrp, k[1], umbral_mw):
            minimas.add(k)
    if modo == "original" or not minimas:
        return ReglaMinimas(list(filas), minimas)
    out = []
    for f in filas:
        if f.get("tipo") in TIPOS_ALERTA and clave_pasada(f) in minimas:
            f = dict(f)
            if modo == "SN":
                f["tipo"], f["vrp_mw"] = "RUTINA", 0.0
            else:
                f["tipo"] = TIPO_MINIMA_SE
        out.append(f)
    return ReglaMinimas(out, minimas)


def pasadas_protegidas(filas, umbral: float = UMBRAL_PROTEGIDA_MW, lectura: str = "A") -> set:
    """Pasadas con al menos una fila protegida (filas como las de cargar_referencia_unificada)."""
    return {clave_pasada(f) for f in filas if alerta_protegida(f, umbral, lectura)}


def _float(v) -> Optional[float]:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def filas_con_banner(path: Path = SNAP_OCR) -> list[dict]:
    """Pasadas del OCR con el banner de MIROVA leido (desde V30, 2026-08-06)."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            banner = (r.get("Nivel_Anomalia_MIROVA") or "").strip().upper()
            v = _float(r.get("VRP_MW"))
            if banner and v is not None:
                out.append({"banner": banner, "vrp_mw": v, "tipo": (r.get("Tipo_Registro") or "").strip(),
                            "fecha_utc": (r.get("Fecha_Satelite_UTC") or "").strip()})
    return out


def coherencia_por_mes(path: Path) -> dict:
    """Por mes de satelite: alertas cuya columna coincide con la clase recalculada desde el VRP."""
    por_mes = defaultdict(Counter)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("Tipo_Registro") or "").strip() not in TIPOS_ALERTA:
                continue
            ok = (r.get("Clasificacion Mirova") or "").strip() == clase_por_vrp(_float(r.get("VRP_MW")))
            por_mes[(r.get("Fecha_Satelite_UTC") or "")[:7]]["coherente" if ok else "incoherente"] += 1
    return {m: dict(c) for m, c in sorted(por_mes.items())}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cons", default=str(SNAP_CONS))
    ap.add_argument("--ocr", default=str(SNAP_OCR))
    a = ap.parse_args(argv)
    for nombre, p in (("consolidado", a.cons), ("OCR", a.ocr)):
        print(f"columna 'Clasificacion Mirova' contra la clase recalculada, alertas del {nombre}, por mes:")
        for m, c in coherencia_por_mes(Path(p)).items():
            print(f"  {m}  {c}")
    sys.path.insert(0, str(ROOT))
    from scripts.referencia_mirova_unificada import cargar_referencia_unificada
    ref = cargar_referencia_unificada()
    for lectura in ("A", "B"):
        pp = pasadas_protegidas(ref, lectura=lectura)
        print(f"pasadas protegidas, lectura {lectura}: {len(pp)}  por sensor {dict(Counter(k[1] for k in pp))}")
    print("banner de MIROVA (Nivel_Anomalia_MIROVA) contra el VRP de la pasada:")
    por_banner = defaultdict(list)
    for f in filas_con_banner(Path(a.ocr)):
        por_banner[f["banner"]].append(f["vrp_mw"])
    for b, vs in sorted(por_banner.items(), key=lambda x: min(x[1])):
        print(f"  {b:9s} n={len(vs):4d}  VRP {min(vs):.2f} a {max(vs):.2f} MW  "
              f"protegidas (>= {UMBRAL_PROTEGIDA_MW} MW): {sum(v >= UMBRAL_PROTEGIDA_MW for v in vs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
