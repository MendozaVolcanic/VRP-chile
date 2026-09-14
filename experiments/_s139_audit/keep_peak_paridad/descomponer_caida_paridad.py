# -*- coding: utf-8 -*-
"""S139: ¿por qué apagar keep_peak baja la razón de magnitud 0,708 -> 0,692 en el A/B de S135?

POR QUÉ. Nicolás pregunta si la caída es un cambio real de magnitud (algo que hacemos mal) o sólo un
cambio de QUÉ pasadas entran al cálculo. El criterio 3 de S135 es la mediana de razones por pasada
publicada en el cráter con fila MIROVA a menos de 20 min. Si el brazo B publica otro conjunto de
pasadas, la mediana se mueve aunque ninguna magnitud cambie.

QUÉ HACE. Reusa sin modificar las funciones de `experiments/_s135_ab_d1d2/evaluar_ab.py` (pareo,
predicado del cráter, magnitud, filtro diurno) y parte los pares de cada brazo en:
  comunes : la pasada (datetime_utc, sensor) publica y parea en A y en B
  solo_A  : parea en A y no en B (lo que B deja de publicar)
  solo_B  : parea en B y no en A (lo que B publica de nuevo)
En los comunes compara la magnitud pasada a pasada.

DOS PREGUNTAS DEL INSTRUMENTO.
 1. Si B cambiara las magnitudes, los comunes lo verían (razón B/A por pasada distinta de 1).
    Si sólo cambiara la composición, los comunes darían B/A = 1 y la diferencia viviría en solo_A/solo_B.
 2. Si el instrumento estuviera muerto (no parea nada), n_pares saldría 0 y se imprime SIN DATO.
Control: la mediana de todos los pares de A y de B debe reproducir 0,708 y 0,692 de S135.

Uso: python descomponer_caida_paridad.py --dir <carpeta fusionada de artefactos S135>
"""
import argparse
import io
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "_s135_ab_d1d2"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_ab as E  # noqa: E402
from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402
from run_pipeline import is_nighttime  # noqa: E402
import yaml  # noqa: E402

A, B = "_s135_ab_a_control", "_s135_ab_b_nokeeppeak"


def med(x):
    return round(st.median(x), 3) if x else "SIN DATO"


def pares(recs, inner, mir):
    """(datetime_utc, sensor) -> (nuestro, mirova, record) con el mismo pareo que evaluar_ab."""
    out = {}
    for r in recs:
        if not E.publica_en_crater(r, inner):
            continue
        dt = E.parse_dt(r["datetime_utc"])
        if dt is None:
            continue
        cerca = [(abs((m - dt).total_seconds()), v) for m, v in mir
                 if abs((m - dt).total_seconds()) <= E.PAR_DT_MIN * 60]
        if not cerca:
            continue
        _, mvrp = min(cerca)
        nuestro = E.magnitud(r)
        if nuestro > 0 and mvrp > 0:
            out[(r["datetime_utc"], r["sensor"])] = (nuestro, mvrp, r)
    return out


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()

    alertas = load_mirova_alertas(cons_path=os.path.join(E.SNAP, "registro_vrp_consolidado.csv"),
                                  ocr_path=os.path.join(E.SNAP, "registro_vrp_ocr.csv"))
    vc = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
    coord = {v["name"]: (v["lat"], v["lon"]) for v in vc["volcanoes"]}
    filas_mir = defaultdict(list)
    for a in alertas:
        f = a.get("fecha_utc")
        if not f or a["sensor_bucket"] != "VIIRS375":
            continue
        dt = E.parse_dt(f)
        vol = a["volcano"]
        if dt is not None and vol in coord and not is_nighttime(*coord[vol], dt):
            continue
        if dt and (a.get("vrp_mw") or 0) > 0:
            filas_mir[vol].append((dt, float(a["vrp_mw"])))

    tot = {A: [], B: []}
    com_a, com_b, solo_a, solo_b = [], [], [], []
    ratio_ba, cambia = [], 0
    solo_a_obj = defaultdict(int)
    por_vol = {}
    for vol in E.VOLCANES:
        ra, rb = E.cargar(args.dir, A, vol), E.cargar(args.dir, B, vol)
        if ra is None or rb is None:
            print(f"{vol}: FALTA un brazo, SIN DATO")
            continue
        ra = [r for r in ra if E.es_v375(r)]
        rb = [r for r in rb if E.es_v375(r)]
        mir = sorted(filas_mir.get(vol, []))
        pa, pb = pares(ra, E.INNER[vol], mir), pares(rb, E.INNER[vol], mir)
        tot[A] += [n / m for n, m, _ in pa.values()]
        tot[B] += [n / m for n, m, _ in pb.values()]
        ka, kb = set(pa), set(pb)
        for k in ka & kb:
            com_a.append(pa[k][0] / pa[k][1])
            com_b.append(pb[k][0] / pb[k][1])
            ratio_ba.append(pb[k][0] / pa[k][0])
            if abs(pb[k][0] - pa[k][0]) > 1e-9:
                cambia += 1
        for k in ka - kb:
            n, m, r = pa[k]
            solo_a.append(n / m)
            pc = r.get("primary_cluster") or {}
            solo_a_obj["1px" if pc.get("n_pixels") == 1 else "2+px"] += 1
        for k in kb - ka:
            solo_b.append(pb[k][0] / pb[k][1])
        por_vol[vol] = (len(ka), len(kb), len(ka & kb), len(ka - kb), len(kb - ka),
                        med([pa[k][0] / pa[k][1] for k in ka]), med([pb[k][0] / pb[k][1] for k in kb]))

    print("CONTROL (debe reproducir S135): mediana A", med(tot[A]), "n", len(tot[A]),
          "| mediana B", med(tot[B]), "n", len(tot[B]))
    print(f"\ncomunes n={len(com_a)}: mediana A {med(com_a)} | mediana B {med(com_b)} | "
          f"pasadas con magnitud distinta {cambia} | mediana B/A {med(ratio_ba)}")
    print(f"solo_A (B deja de publicarlas) n={len(solo_a)}: mediana razón {med(solo_a)} | objeto {dict(solo_a_obj)}")
    print(f"solo_B (B publica de nuevo)   n={len(solo_b)}: mediana razón {med(solo_b)}")
    print("\npor volcán: (pares A, pares B, comunes, solo_A, solo_B, mediana A, mediana B)")
    for v, t in por_vol.items():
        print(f"  {v:<22}{t}")


if __name__ == "__main__":
    main()
