# -*- coding: utf-8 -*-
"""Clase de intensidad de una alerta de MIROVA y definicion de "alerta protegida" (tarea 0.2 del loop).

POR QUE. El criterio de victoria de la replica (Nicolas, 2026-10-13; `tasks/LOOP_OBJETIVOS.md` §1.2) no
acepta perder ninguna alerta que MIROVA clasifique de "Bajo" para arriba. Hacia falta saber que mide esa
clase antes de usarla, porque en el CSV hay "Bajo" de 0,04 MW.

Lo que se establecio (detalle y fuentes en `docs/S151_CRITERIO_CLASE_MIROVA.md`):
- La columna `Clasificacion Mirova` la calcula el scraper de Mirova-v1 desde el VRP de la pasada
  (`volcanes.py:63`), no MIROVA. Cambio de escala en el tiempo: en el consolidado es coherente con el VRP
  desde febrero de 2026 y en el OCR desde julio; antes trae etiquetas de escalas retiradas.
- Los cortes son los de la escala de MIROVA, Coppola et al. 2016a (Geol. Soc. Spec. Publ. 426, fig. 11,
  p. 16 del PDF): 1, 10, 100 y 1.000 MW. Los nombres del paper (Low, Moderate...) estan corridos un nivel
  respecto de los del sitio actual; el banner de mirovaweb hoy dice VERY LOW bajo 1 MW y LOW de 1 a 10.
- El banner de la imagen (`Nivel_Anomalia_MIROVA`, unico campo que si viene de MIROVA) es por pasada y
  separa sin error VERY_LOW (0,05 a 0,91 MW) de LOW (1,00 a 8,00 MW).

Definicion operativa: una pasada es "alerta protegida" si es alerta (consolidado u OCR) y su VRP_MW es
de 1 MW o mas, RECALCULADO desde el VRP, nunca leido de la columna.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

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


def alerta_protegida(fila: dict) -> bool:
    """Fila normalizada (`tipo`, `vrp_mw`, como las de referencia_mirova_unificada)."""
    v = fila.get("vrp_mw")
    return fila.get("tipo") in TIPOS_ALERTA and v is not None and v >= UMBRAL_PROTEGIDA_MW


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
