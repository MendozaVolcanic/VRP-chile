"""S148 - lectura de las predicciones Q1 a Q4 del A/B de la caja de 5 x 5 km (brazos G y H).

EL FENOMENO. MIROVA aplica el umbral permisivo solo en una caja de 5 x 5 km sobre la cumbre y el
estricto en todo el resto de la escena; la replica aplica el permisivo en un circulo de 3 a 20 km
segun el volcan. La pregunta es si los cumulos que la replica publica FUERA de esa caja, donde
MIROVA no vio nada, dejan de publicarse cuando se les aplica el umbral estricto.

Pre-registro: experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md (Q1 a Q4), escrito antes de correr.

QUE MIDE. Clasifica cada pasada VIIRS 375 que el CONTROL publica segun si su cumulo publicado cae
dentro o fuera de la caja (la misma geometria del pipeline: |dx| y |dy| <= 2,5 km desde el ancla
de deteccion, geo_utils.get_detection_anchor), y cuenta cuantas sigue publicando el brazo.
  Q1: negativos limpios publicados FUERA de la caja que dejan de publicarse (la mitad o mas).
  Q2: negativos limpios publicados DENTRO de la caja que cambian (5 o menos): control interno.
  Q3: positivos publicados FUERA de la caja que sobreviven (85 % o mas).
  Q4: recall por pasada.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si el brazo no cambiara nada, esto lo mostraria? SI: corrido con --brazo igual a --control da
   cero apagados y cero cambiados en todas las filas.
2. Si el instrumento estuviera muerto? Aborta si la cobertura del tramo no es exacta, y los
   denominadores del control (fuera y dentro de la caja) tienen que parecerse a los del
   pre-registro (63 fuera y 42 dentro en negativos, 43 fuera en positivos, medidos sobre el run
   35521542153 con la ventana completa). Control positivo: el brazo de la conectiva
   (_s147_ab_sin_test1_max), que se sabe que apaga 85 de 95, tiene que mostrarse aca tambien.

Uso (los datos se traen con git archive CON RUTA a experiments/_s147_lectura, ver lectura_por_tramo.py):
  python experiments/_s148_caja/lectura_caja.py --run <DIR> --control _s146_ab_sin_test1 \
      --brazo _s147_ab_sin_test1_caja --fin 2026-09-17
"""
from __future__ import annotations
import argparse
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)

import banco_paridad as bp  # noqa: E402
from evaluar import cargar_brazo, clave  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

LECTURA = ROOT / "experiments" / "_s147_lectura"
CONGELADO = ROOT / "experiments" / "_s146_ab_sin_test1" / "_congelado"
HALF_KM = 2.5


def anclas():
    cfg = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))
    vols = cfg["volcanoes"] if isinstance(cfg, dict) and "volcanoes" in cfg else cfg
    out = {}
    for v in (vols.values() if isinstance(vols, dict) else vols):
        nombre = v.get("name") or v.get("id")
        out[nombre] = get_detection_anchor(v)
    return out


def en_caja(lat, lon, c):
    # misma geometria que pipeline/scan_geometry.py::roi_mask_bbox
    dy = (lat - c[0]) * 111.0
    dx = (lon - c[1]) * 111.0 * math.cos(math.radians(c[0]))
    return abs(dy) <= HALF_KM and abs(dx) <= HALF_KM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", required=True)
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default="2026-09-20")
    ap.add_argument("--sensor", default="VIIRS375")
    a = ap.parse_args()
    D = LECTURA / "experiments" / "_s146_ab_sin_test1" / "salidas" / a.run
    V = (a.inicio, a.fin)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(CONGELADO / "registro_vrp_consolidado.csv",
                                        CONGELADO / "registro_vrp_ocr.csv")
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
    anc = anclas()

    def carga(br):
        recs = cargar_brazo(D / br, coords, inner, V)
        bp.etiquetar(recs, por_vb, ns, nv)
        return {clave(r): r for r in recs}

    C, B = carga(a.control), carga(a.brazo)
    print(f"cobertura del tramo {V[0]} a {V[1]}: control {len(C)}, brazo {len(B)}, "
          f"faltan en el control {len(set(B) - set(C))}, faltan en el brazo {len(set(C) - set(B))}")
    if set(C) != set(B):
        print("::error::la cobertura del tramo NO es exacta: no se lee.")
        return 1

    sin_ancla = set()
    filas_out = {}
    for lab in ("neg_limpio", "pos"):
        for donde in ("fuera", "dentro", "sin_posicion"):
            filas_out[(lab, donde)] = [0, 0, 0]  # publicadas en control, siguen en brazo, cambian magnitud
    por_vol = {}
    for k, rc in C.items():
        if rc["b"] != a.sensor or rc["lab"] not in ("neg_limpio", "pos") or not rc["pub"]:
            continue
        vol = k[0]
        c = anc.get(vol)
        if c is None or c[0] is None:
            sin_ancla.add(vol)
            donde = "sin_posicion"
        elif rc.get("pc_lat") is None or rc.get("pc_lon") is None:
            donde = "sin_posicion"
        else:
            donde = "dentro" if en_caja(rc["pc_lat"], rc["pc_lon"], c) else "fuera"
        rb = B[k]
        f = filas_out[(rc["lab"], donde)]
        f[0] += 1
        f[1] += int(bool(rb["pub"]))
        cambia = (not rb["pub"]) or (rb.get("pc_lat"), rb.get("pc_lon")) != (rc.get("pc_lat"), rc.get("pc_lon"))
        f[2] += int(cambia)
        pv = por_vol.setdefault((rc["lab"], donde, vol), [0, 0])
        pv[0] += 1
        pv[1] += int(bool(rb["pub"]))
    if sin_ancla:
        print("AVISO: volcanes sin ancla en volcanoes.yaml:", sorted(sin_ancla))

    completa = V == ("2026-09-01", "2026-09-20")
    print(f"\n{'VENTANA COMPLETA' if completa else 'PRELIMINAR: tramo parcial, NO es el veredicto'} | "
          f"{a.sensor} | control {a.control} | brazo {a.brazo}")
    print(f"{'etiqueta':12} {'cumulo del control':20} {'publica control':>16} {'sigue en brazo':>15} "
          f"{'apagadas':>9} {'cambian (apaga o mueve)':>24}")
    for (lab, donde), (n, s, ch) in filas_out.items():
        print(f"{lab:12} {donde:20} {n:16d} {s:15d} {n - s:9d} {ch:24d}")
    nf = filas_out[("neg_limpio", "fuera")]
    nd = filas_out[("neg_limpio", "dentro")]
    pf = filas_out[("pos", "fuera")]
    print(f"\nQ1 negativos de FUERA que se apagan: {nf[0] - nf[1]} de {nf[0]} (prediccion: la mitad o mas)")
    print(f"Q2 negativos de DENTRO que cambian: {nd[2]} de {nd[0]} (prediccion: 5 o menos de 42)")
    print(f"Q3 positivos de FUERA que sobreviven: {pf[1]} de {pf[0]} (prediccion: 85 % o mas)")
    pos_c = sum(1 for r in C.values() if r["b"] == a.sensor and r["lab"] == "pos" and r["pub"])
    pos_b = sum(1 for r in B.values() if r["b"] == a.sensor and r["lab"] == "pos" and r["pub"])
    n_pos = sum(1 for r in C.values() if r["b"] == a.sensor and r["lab"] == "pos")
    print(f"Q4 recall por pasada: control {pos_c} de {n_pos}, brazo {pos_b} de {n_pos}")
    print("\npor volcan (etiqueta, donde, volcan): publica control -> sigue en brazo")
    for (lab, donde, vol), (n, s) in sorted(por_vol.items()):
        print(f"  {lab:11} {donde:13} {vol:22} {n:4d} -> {s:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
