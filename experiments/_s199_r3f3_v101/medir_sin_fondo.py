# -*- coding: utf-8 -*-
"""S199, hallazgo R3F3-V101 de la auditoría externa (Codex, ronda 3): cuántos records publicados suman en su potencia
uno o más píxeles alertados sin fondo estimado (el .m de MIROVA los suma con fondo 0: la potencia de ese píxel es su
radiancia entera, posiblemente inflada; docs/MIROVA_DIVERGENCES.md, D36, «Fondo no estimable»).

POR QUÉ se mide: el tablero no leía esa marca. Antes de poner el aviso, saber cuántas pasadas lo llevarían y cuántas de
ellas el tablero publica en la cumbre (distance_class "summit"), que son las que el geólogo de turno lee como actividad.

CRITERIO (el mismo de CraterNoMedido.fondoNoEstimado en frontend/crater_no_medido.js; la prueba
tests/test_tablero_fondo_no_estimado_r3f3.py exige igualdad record por record):
  - escena medida por la vía (diag_codigo_mirova sin motivo_vacio; la MODIS sin ningún fondo ya es «fondo_no_estimado»);
  - con la clave alertados_sin_fondo (records desde S192): su valor si es > 0;
  - sin la clave (records anteriores a S192): record de la vía con alertados y L_bk = 0. L_bk suma sólo los fondos que
    existen (np.nansum, pipeline/mirova_v750_codigo.py, vrp_mirova), así que 0 con alertados dice que NINGUNO tuvo
    fondo: se cuentan todos. Si sólo una parte quedó sin fondo, el record viejo no lo dice (SIN DATO, no se marca).

Sólo lee. Universo: los 11 volcanes con MIROVA de data/mirova_equivalent/ y los de data/sombra_34/ que muestra el tablero
(ver VOLCANOES en frontend/index.html). Uso: python medir_sin_fondo.py [raíz del repo]
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

TIER_A = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Copahue", "Llaima",
          "Villarrica", "PuyehueCordonCaulle", "Chaiten"]
FUERA = {"OlcaParuma", "Putana"}   # fuera de la matriz desde el 2026-11-17 (el tablero no los muestra)
FAMILIAS = ("MODIS", "VIIRS 375", "VIIRS 750")


def fuentes(raiz):
    out = [(raiz / "data" / "mirova_equivalent" / (v + ".json"), "mirova_equivalent") for v in TIER_A]
    out += [(p, "sombra_34") for p in sorted((raiz / "data" / "sombra_34").glob("*.json")) if p.stem not in FUERA]
    return out


def familia(sensor):
    s = sensor or ""
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS 750" if s.endswith("_750") else "VIIRS 375"


def entero(x):
    return round(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 else 0


def criterio(r):
    """Cuántos alertados del record quedaron sin fondo (0 si no se marca)."""
    d = r.get("diag_codigo_mirova")
    if not isinstance(d, dict) or d.get("motivo_vacio"):
        return 0
    if "alertados_sin_fondo" in d:
        return entero(d["alertados_sin_fondo"])
    total = entero(r.get("n_anomalous_pixels"))
    l_bk = d.get("L_bk")
    heredado = (r.get("via_codigo_mirova") is True and total > 0 and isinstance(l_bk, (int, float))
                and not isinstance(l_bk, bool) and l_bk == 0)
    return total if heredado else 0


def medir(raiz):
    tot, por, ejemplos = Counter(), Counter(), []
    for ruta, grupo in fuentes(raiz):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for r in datos.get("records", []):
            d = r.get("diag_codigo_mirova")
            if not isinstance(d, dict) or d.get("motivo_vacio"):
                continue
            fam = familia(r.get("sensor"))
            con_clave = "alertados_sin_fondo" in d
            tot[(grupo, fam, "pasadas")] += 1
            tot[(grupo, fam, "con_clave_y_alertados")] += con_clave and entero(r.get("n_anomalous_pixels")) > 0
            n = criterio(r)
            if not n:
                continue
            npix = entero(r.get("n_anomalous_pixels"))
            cumbre = r.get("distance_class") == "summit"
            for k, v in (("marcados", 1), ("por_clave", con_clave), ("heredados", not con_clave), ("cumbre", cumbre),
                         ("parciales", n < npix), ("vrp_pos", (r.get("vrp_mw") or 0) > 0)):
                por[(grupo, fam, k)] += bool(v)
            ejemplos.append((r.get("vrp_mw") or 0, datos.get("volcano") or ruta.stem, r.get("sensor"),
                             r.get("datetime_utc"), n, npix, r.get("distance_class"), "clave" if con_clave else "L_bk=0"))
    return tot, por, sorted(ejemplos, reverse=True)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    tot, por, ejemplos = medir(raiz)
    print("Raíz:", raiz)
    print("grupo | familia | pasadas medidas por la vía | con la clave y alertados | MARCADAS | por la clave (>0) |"
          " heredadas (L_bk=0) | en la cumbre | parciales (n<alertados) | con VRP > 0")
    for grupo in ("mirova_equivalent", "sombra_34"):
        for fam in FAMILIAS:
            c = lambda k: por[(grupo, fam, k)]
            print(f"{grupo} | {fam} | {tot[(grupo, fam, 'pasadas')]} | {tot[(grupo, fam, 'con_clave_y_alertados')]} | "
                  f"{c('marcados')} | {c('por_clave')} | {c('heredados')} | {c('cumbre')} | {c('parciales')} | {c('vrp_pos')}")
    s = lambda k: sum(v for kk, v in por.items() if kk[2] == k)
    print(f"TOTAL marcadas: {s('marcados')} (por la clave {s('por_clave')}, heredadas {s('heredados')}) | en la cumbre:"
          f" {s('cumbre')}")
    print("\nTodas, de mayor a menor potencia (MW, volcán, sensor, UTC, sin fondo, alertados, clase, de dónde):")
    for e in ejemplos:
        print(" ", e)


if __name__ == "__main__":
    main()
