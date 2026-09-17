# -*- coding: utf-8 -*-
"""S143: fusiona los artefactos de N tramos de un A/B en una sola ventana por brazo y volcán.

POR QUÉ. Cada job de un A/B arranca de un checkout limpio y su artefacto contiene sólo la ventana
que ese tramo procesó. Evaluar un tramo suelto mide medio experimento con el denominador equivocado
(A90). La plantilla de S135 (`experiments/_s135_ab_d1d2/fusionar_chunks.py`) tenía fijos el
prefijo `s135ab-`, los cinco brazos, los seis volcanes y exactamente dos tramos (hallazgo 3 del
verificador S143). Esta versión recibe todo eso por argumento.

QUÉ HACE. Une los records por `(datetime_utc, sensor)`, la clave de una pasada. Si una misma clave
aparece en dos tramos con contenido distinto lo reporta como CONFLICTO (las ventanas se solaparon o
el código cambió entre tramos, hallazgo 11): el tramo posterior gana, pero el conflicto queda
escrito en el informe y con `--estricto` el script termina con código 1. Si falta el archivo de un
brazo y volcán en algún tramo, NO escribe la fusión de ese par: el evaluador lo verá ausente y lo
excluirá por cobertura, en vez de evaluar una ventana a medias.

Layout de entrada, por tramo: `<dir>/<prefijo><brazo>-<volcán><sufijo>/<volcán>.json`. El sufijo
sirve para los artefactos rescatados, que llevan `__run<id>` en el nombre de la carpeta.

Uso:
    python experiments/_s143_evaluador/fusionar.py --prefijo s143ab- \\
        --brazos _s142_ab_control _s142_ab_literal --volcanes Isluga Lascar \\
        --tramo <dir tramo 1> --tramo <dir tramo 2> --out <dir fusionado>
    # artefactos rescatados en una misma carpeta, distinguidos por run:
        --tramo "<dir>::__run34173711390" --tramo "<dir>::__run34208191011"
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys


def parse_tramo(s: str) -> tuple[str, str]:
    """'dir::sufijo' -> (dir, sufijo); 'dir' -> (dir, '')."""
    if "::" in s:
        d, suf = s.rsplit("::", 1)
        return d, suf
    return s, ""


def ruta(base: str, prefijo: str, brazo: str, vol: str, sufijo: str = "") -> str:
    return os.path.join(base, f"{prefijo}{brazo}-{vol}{sufijo}", f"{vol}.json")


def _canon(r: dict) -> str:
    return json.dumps(r, sort_keys=True, ensure_ascii=False)


def fusionar(tramos, prefijo, brazos, volcanes, out):
    """Fusiona y escribe `<out>/<prefijo><brazo>-<volcán>/<volcán>.json`. Devuelve el informe."""
    informe = {"tramos": [list(t) for t in tramos], "prefijo": prefijo, "archivos": [],
               "conflictos": [], "duplicados_identicos": 0, "faltantes": []}
    for vol in volcanes:
        for brazo in brazos:
            rutas = [ruta(d, prefijo, brazo, vol, suf) for d, suf in tramos]
            ausentes = [i for i, p in enumerate(rutas) if not os.path.exists(p)]
            if ausentes:
                informe["faltantes"].append({"brazo": brazo, "volcan": vol,
                                             "tramos_sin_archivo": ausentes})
                continue
            unido, cabecera, por_tramo = {}, None, []
            for i, p in enumerate(rutas):
                with open(p, encoding="utf-8") as fh:
                    d = json.load(fh)
                if cabecera is None:
                    cabecera = d
                recs = d["records"]
                por_tramo.append(len(recs))
                for r in recs:
                    k = (r["datetime_utc"], r["sensor"])
                    if k in unido:
                        if _canon(unido[k][1]) != _canon(r):
                            informe["conflictos"].append({"brazo": brazo, "volcan": vol,
                                                          "clave": list(k),
                                                          "tramos": [unido[k][0], i]})
                        else:
                            informe["duplicados_identicos"] += 1
                    unido[k] = (i, r)  # el tramo posterior gana; el conflicto queda escrito
            recs = [r for _, r in sorted(unido.values(),
                                         key=lambda x: (x[1]["datetime_utc"], x[1]["sensor"]))]
            salida = dict(cabecera)
            salida["records"] = recs
            dest = os.path.join(out, f"{prefijo}{brazo}-{vol}")
            os.makedirs(dest, exist_ok=True)
            with open(os.path.join(dest, f"{vol}.json"), "w", encoding="utf-8") as fh:
                json.dump(salida, fh, ensure_ascii=False)
            fechas = sorted({r["datetime_utc"][:10] for r in recs})
            informe["archivos"].append({"brazo": brazo, "volcan": vol, "n_por_tramo": por_tramo,
                                        "n_fusion": len(recs),
                                        "ventana_datos": [fechas[0], fechas[-1]] if fechas else None})
    return informe


def main(argv=None) -> int:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tramo", action="append", required=True,
                    help="directorio del tramo, opcionalmente 'dir::sufijo' (repetible, en orden)")
    ap.add_argument("--prefijo", required=True, help="prefijo del artefacto, p. ej. 's143ab-'")
    ap.add_argument("--brazos", nargs="+", required=True)
    ap.add_argument("--volcanes", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--estricto", action="store_true", help="código 1 si hay conflictos o faltantes")
    a = ap.parse_args(argv)
    tramos = [parse_tramo(t) for t in a.tramo]
    inf = fusionar(tramos, a.prefijo, a.brazos, a.volcanes, a.out)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "fusion_informe.json"), "w", encoding="utf-8") as fh:
        json.dump(inf, fh, indent=1, ensure_ascii=False)
    for f in inf["archivos"]:
        print(f"{f['volcan']:<22}{f['brazo']:<30}{str(f['n_por_tramo']):>18}{f['n_fusion']:>7}  "
              f"{f['ventana_datos']}")
    print(f"\n{len(inf['archivos'])} fusionados, {len(inf['faltantes'])} faltantes, "
          f"{len(inf['conflictos'])} conflictos, {inf['duplicados_identicos']} duplicados idénticos")
    if inf["conflictos"]:
        print("AVISO: claves presentes en dos tramos con contenido distinto:",
              inf["conflictos"][:5])
    if a.estricto and (inf["conflictos"] or inf["faltantes"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
