# -*- coding: utf-8 -*-
"""Runner del A/B de los dos fondos autorreferentes — S129/S130.

`lectura.py` trae las funciones y sus tests; faltaba lo que las corre sobre los
datos y aplica los criterios de `docs/s129/PREREGISTRO_AB_FONDOS.md`. Escrito con
el chunk 2 todavia corriendo (A16) y VALIDADO contra el chunk 1 ya rescatado, para
que al llegar el resto sea inmediato.

Los chunks son DISJUNTOS en el tiempo, asi que combinar es concatenar por volcan y
brazo. El emparejamiento va sobre la INTERSECCION de pasadas de los tres brazos:
sin eso, un brazo que proceso mas granules parece "detectar mas" cuando lo unico
que hizo fue mirar mas veces.

Uso:
    python experiments/_s129_ab_fondos/veredicto.py                    # chunk 1
    python experiments/_s129_ab_fondos/veredicto.py --extra <dir2>     # + chunk 2
"""
import argparse
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from lectura import BUCK, _noches, firmas_de_brazo                 # noqa: E402
from _s126_lib import cargar_mirova                                # noqa: E402

BRAZOS = ["control", "pool", "bgmag"]


def cargar_brazo(dirs):
    """{volcan: [records]} concatenando los directorios dados (chunks disjuntos)."""
    brazo = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            vol = fn[:-5]
            doc = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            recs = doc.get("records", doc) if isinstance(doc, dict) else doc
            brazo.setdefault(vol, []).extend(recs)
    return brazo


def noches_comunes(brazos):
    """Interseccion de (volcan, fecha) presentes en los TRES brazos."""
    sets = []
    for b in brazos.values():
        s = set()
        for vol, recs in b.items():
            for f in _noches(recs):
                s.add((vol, f))
        sets.append(s)
    return set.intersection(*sets) if sets else set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(ROOT, "data"),
                    help="directorio con _s129_ab_<brazo>/ (chunk 1)")
    ap.add_argument("--extra", default=None,
                    help="directorio del chunk 2 (con sus _s129_ab_<brazo>/ dentro)")
    args = ap.parse_args()

    brazos = {}
    for b in BRAZOS:
        dirs = [os.path.join(args.base, f"_s129_ab_{b}")]
        if args.extra:
            # el artefacto puede venir plano o anidado; se aceptan las dos formas
            for cand in (os.path.join(args.extra, f"_s129_ab_{b}"),
                         os.path.join(args.extra, f"_s129_ab_{b}", f"_s129_ab_{b}")):
                if os.path.isdir(cand):
                    dirs.append(cand)
                    break
        brazos[b] = cargar_brazo(dirs)

    comunes = noches_comunes(brazos)
    pasadas = {f for (_v, f) in comunes}
    mirova, _ = cargar_mirova(("2026-01-01", "2026-12-31"))

    print("=" * 74)
    print("A/B S129 — los dos fondos autorreferentes")
    print("=" * 74)
    print(f"noches (volcan, fecha) comunes a los TRES brazos: {len(comunes)}")
    for b in BRAZOS:
        n = sum(len(v) for v in brazos[b].values())
        print(f"  {b:8s} {len(brazos[b])} volcanes · {n} records")
    print()

    res = {}
    for b in BRAZOS:
        res[b] = firmas_de_brazo(brazos[b], mirova, pasadas)

    print(f"{'firma':26s} " + "".join(f"{b:>12s}" for b in BRAZOS))
    print("-" * 74)
    filas = [
        ("F1 ratio mediano", lambda r: r["ratio_mediano"]),
        ("F2 n detecciones", lambda r: r["n_detecciones"]),
        ("F4 umbral mediano (K)", lambda r: r["umbral_mediano"]),
        ("   n pares vs MIROVA", lambda r: r["n_pares"]),
        ("F3 ratio tercil debil", lambda r: r["regimen"]["debil"]),
        ("F3 ratio tercil fuerte", lambda r: r["regimen"]["fuerte"]),
        ("F3 BRECHA (debil-fuerte)", lambda r: r["regimen"]["brecha"]),
    ]
    for et, fn in filas:
        print(f"{et:26s} " + "".join(f"{str(fn(res[b])):>12s}" for b in BRAZOS))

    print()
    print("ATRIBUCION esperada (pre-registro): `pool` mueve F2 y F4; `bgmag` mueve")
    print("F1 SIN tocar F2. Si los dos mueven F1 y solo uno F2, la atribucion es limpia.")
    print()
    print("CRITERIO QUE NO SE NEGOCIA: si un brazo pierde aunque sea UNA noche que")
    print("MIROVA confirmo, es NO ADOPTAR aunque mejore la paridad.")

    # el criterio duro, medido: noches MIROVA-confirmadas que el brazo pierde
    def confirmadas(b):
        out = set()
        for vol, recs in brazos[b].items():
            for f, (v, _dt, _t) in _noches(recs).items():
                if v > 0 and (mirova.get(vol) or {}).get((f, BUCK)):
                    out.add((vol, f))
        return out

    base = confirmadas("control")
    print()
    for b in ("pool", "bgmag"):
        perdidas = base - confirmadas(b)
        ganadas = confirmadas(b) - base
        veredicto = "NO ADOPTAR" if perdidas else "sin perdidas"
        print(f"  {b:8s} noches MIROVA perdidas vs control: {len(perdidas):3d}"
              f"   ganadas: {len(ganadas):3d}   -> {veredicto}")
        if perdidas:
            for x in sorted(perdidas)[:10]:
                print(f"      perdida: {x[0]} {x[1]}")

    out = os.path.join(HERE, "veredicto.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"n_noches_comunes": len(comunes), "firmas": res}, f,
                  indent=2, ensure_ascii=False)
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
