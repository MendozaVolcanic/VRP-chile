#!/usr/bin/env python
"""Umbral efectivo de los Tests 2 y 3 en los datos chilenos, contra los mínimos del código de MIROVA.

Por qué. El código OSF de MIROVA (MIROVA_VIIRS750_hotspot_detection.m l. 281 a 285) resta la media
3x3 CON el píxel central, y nosotros la media de los 8 vecinos sin el central
(detection_context.py:147-159 y :483-486). Para un píxel de valor x con vecinos de media m,
MIROVA mide (x - (x + 8m)/9) = (8/9)(x - m). Así, un mínimo de MIROVA de c en su espacio vale
(9/8)·c en el nuestro: 0,02 -> 0,0225; 0,003 -> 0,003375; 0,01 -> 0,01125; y el piso de descarte
-0,1 -> -0,1125. Con la conectiva `max` el umbral efectivo es max(C1, mu + C2·sigma): este script
mide en cuántos records el umbral efectivo nuestro queda por DEBAJO del mínimo de MIROVA
convertido, es decir, dónde publicamos con una vara más laxa que la suya.

Pregunta 1 del instrumento: si los umbrales fueran idénticos la fracción sería 0 en todas las
filas; el control positivo es la fila de escena en VIIRS 750, donde AUDIT_S158 V3 midió ~79 %.
Pregunta 2: n se imprime siempre; un n = 0 es SIN DATO.

Denominador: records con diag_mu_dnti y diag_sd_dnti; ventana K (desde 2026-09-18) y todo.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DATA = Path(r"D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent")
K_DESDE = "2026-09-18 00:00"
C1_SUM, C1_SCE = 0.003, 0.010           # pipeline.profile efectivo (DNTI_CONTEXTUAL_C1_SUMMIT / _SCENE)
C2_SUM, C2_SCE = 5.0, 10.0              # C2_DNTI_SUMMIT_NIGHT / C2_DNTI_SCENE_NIGHT
F = 9.0 / 8.0
MIN_MIROVA = {  # .m l. 183-187, convertidos al espacio de 8 vecinos
    "dnti_sum": 0.003 * F, "dnti_sce": 0.02 * F, "deti_sum": 0.003 * F, "deti_sce": 0.01 * F,
}


def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else "VIIRS750" if s.endswith("_750") else "VIIRS375" if s.startswith("VIIRS") else "?"


def main():
    c = Counter()
    for fp in sorted(DATA.glob("*.json")):
        d = json.load(open(fp, encoding="utf-8"))
        recs = d["records"] if isinstance(d, dict) and "records" in d else d
        for r in recs:
            mu, sd = r.get("diag_mu_dnti"), r.get("diag_sd_dnti")
            mue, sde = r.get("diag_mu_deti"), r.get("diag_sd_deti")
            if mu is None or sd is None or mue is None or sde is None:
                continue
            b = bucket(r.get("sensor"))
            for w in ["todo"] + (["K"] if (r.get("datetime_utc") or "") >= K_DESDE else []):
                k = (w, b)
                c[(k, "n")] += 1
                thr = {
                    "dnti_sum": max(C1_SUM, mu + C2_SUM * sd), "dnti_sce": max(C1_SCE, mu + C2_SCE * sd),
                    "deti_sum": max(C1_SUM, mue + C2_SUM * sde), "deti_sce": max(C1_SCE, mue + C2_SCE * sde),
                }
                for nombre, t in thr.items():
                    if t < MIN_MIROVA[nombre]:
                        c[(k, f"{nombre}: umbral nuestro < minimo MIROVA (8 vec)")] += 1
                # ¿gobierna el piso C1 o el contraste?
                if mu + C2_SUM * sd <= C1_SUM:
                    c[(k, "dnti_sum: gobierna C1=0.003")] += 1
                if mu + C2_SCE * sd <= C1_SCE:
                    c[(k, "dnti_sce: gobierna C1=0.010")] += 1
                if mue + C2_SUM * sde <= C1_SUM:
                    c[(k, "deti_sum: gobierna C1=0.003")] += 1
                if mue + C2_SCE * sde <= C1_SCE:
                    c[(k, "deti_sce: gobierna C1=0.010")] += 1
    lineas = []
    for (w, b) in sorted({k for (k, _) in c}):
        n = c[((w, b), "n")]
        lineas.append(f"== {w} | {b}  n={n}")
        for (k, nombre), v in sorted(c.items()):
            if k == (w, b) and nombre != "n":
                lineas.append(f"  {nombre:52s} {v:6d}  {100.0 * v / n:5.1f} %")
    txt = "\n".join(lineas)
    print(txt)
    Path(__file__).with_name("umbral_efectivo_salida.txt").write_text(txt + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
