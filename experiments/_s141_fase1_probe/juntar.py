# -*- coding: utf-8 -*-
"""S141, Fase 1: junta las salidas por volcán del probe del vecino y aplica el criterio pre-registrado.

POR QUÉ. El workflow corre un job por volcán y cada uno escribe su propio criterio.json con sus
pocas pasadas; el criterio del plan se juzga sobre todas juntas (n ≥ 10) y por estrato. Este
script es la única fuente de los números del informe (regla S91: ninguno transcrito a mano).

INSTRUMENTO. P1: el control (pasadas donde publicamos tantos píxeles como MIROVA) viene dentro
de evaluar_criterio. P3: se reportan aparte los candidatos que con el código de hoy ya no
publican un solo píxel, y se recalcula el criterio sólo con los que sí.

USO: python experiments/_s141_fase1_probe/juntar.py [--dir experiments/_s141_fase1_probe/artefactos]
Salida: criterio_total.json en esta carpeta.
"""
import argparse
import collections
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from analisis_vecinos import evaluar_criterio  # noqa: E402


def cargar(dir_art):
    filas = []
    for p in sorted(Path(dir_art).rglob("*.json")):
        if p.name in ("criterio.json", "criterio_total.json"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "clase" in d and "volcan" in d:
            d["_archivo"] = str(p.relative_to(dir_art))
            filas.append(d)
    return filas


def resumen(filas):
    errores = collections.Counter()
    for f in filas:
        if not f.get("ok"):
            errores[(f.get("error") or "sin error")[:80]] += 1
        elif not (f.get("resumen") or {}).get("grilla_ok"):
            errores["grilla_distinta"] += 1
    por_volcan = {}
    for f in filas:
        v = por_volcan.setdefault(f["volcan"], {"candidato": 0, "control": 0, "ok": 0})
        v[f["clase"]] += 1
        v["ok"] += int(bool(f.get("ok") and (f.get("resumen") or {}).get("grilla_ok")))
    solo_1px_hoy = [f for f in filas if f["clase"] == "control" or (f.get("hoy") or {}).get("pc_n") == 1]
    return {
        "n_filas": len(filas),
        "descartes": dict(errores),
        "por_volcan": por_volcan,
        "criterio": {"total": evaluar_criterio(filas), "focal": evaluar_criterio(filas, "focal"),
                     "nevado": evaluar_criterio(filas, "nevado")},
        "criterio_solo_candidatos_con_1px_hoy": {
            "total": evaluar_criterio(solo_1px_hoy), "focal": evaluar_criterio(solo_1px_hoy, "focal"),
            "nevado": evaluar_criterio(solo_1px_hoy, "nevado")},
        "pasadas": [{"volcan": f["volcan"], "pasada_utc": f.get("pasada_utc"), "clase": f["clase"],
                     "regimen": f.get("regimen"), "ok": f.get("ok"),
                     "grilla_ok": (f.get("resumen") or {}).get("grilla_ok"),
                     "npix_osf": (f.get("osf") or {}).get("Npix"),
                     "pub_n_backfill": (f.get("persistido") or {}).get("pub_n"),
                     "pc_n_hoy": (f.get("hoy") or {}).get("pc_n"),
                     "dist_centro_a_osf_km": (f.get("resumen") or {}).get("dist_centro_a_osf_km"),
                     "conteo": (f.get("resumen") or {}).get("conteo"),
                     "fraccion_brecha_fondo_local": (f.get("resumen") or {}).get("fraccion_brecha_fondo_local"),
                     "error": f.get("error")} for f in filas],
    }


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description="Junta las salidas del probe S141 y aplica el criterio")
    ap.add_argument("--dir", default=str(HERE / "artefactos"))
    a = ap.parse_args(argv)
    out = resumen(cargar(a.dir))
    (HERE / "criterio_total.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_filas", "descartes", "criterio", "criterio_solo_candidatos_con_1px_hoy")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
