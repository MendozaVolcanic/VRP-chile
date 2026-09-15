# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): junta las salidas por volcán del probe y aplica el criterio pre-registrado.

POR QUÉ. El workflow corre un job por volcán y cada uno ve sólo sus pasadas; el criterio del plan se
juzga por volcán, por estrato y en total, con todas juntas. Este script es la única fuente de los
números del informe (regla S91: ninguno transcrito a mano).

USO: python experiments/_s141_fase1_probe_v2/juntar.py [--dir experiments/_s141_fase1_probe_v2/artefactos]
Salida: criterio_total.json en esta carpeta.
"""
import argparse
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from analisis_v2 import evaluar, fila_valida  # noqa: E402


def cargar(dir_art):
    filas = []
    for p in sorted(Path(dir_art).rglob("*.json")):
        if p.name.startswith("criterio"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "clase" in d and "volcan" in d:
            d["_archivo"] = str(p.relative_to(dir_art))
            filas.append(d)
    return filas


def resumen_total(dir_art):
    filas = cargar(dir_art)
    pasadas = []
    for f in filas:
        r = f.get("resumen") or {}
        valida, motivo = fila_valida(f)
        pasadas.append({"volcan": f["volcan"], "pasada_utc": f.get("pasada_utc"), "clase": f["clase"],
                        "regimen": f.get("regimen"), "ok": f.get("ok"), "valida": valida, "motivo": motivo,
                        "ruta": (f.get("publicado") or {}).get("ruta"), "npix_osf": (f.get("osf") or {}).get("Npix"),
                        "n_publicado_hoy": (f.get("hoy") or {}).get("n_publicado"),
                        "dist_centro_osf_km": r.get("dist_centro_osf_km"), "foco_ok": r.get("foco_ok"),
                        "replica_ok": r.get("replica_ok"), "alineacion_bt": r.get("alineacion_bt"),
                        "limitantes": [v.get("limitante") for v in r.get("vecinos", [])
                                       if v.get("caliente") and not v.get("incluido")],
                        "fraccion_brecha": r.get("fraccion_brecha"), "fraccion_fondo": r.get("fraccion_fondo"),
                        "error": f.get("error"), "error_analisis": f.get("error_analisis")})
    return {"n_filas": len(filas),
            "criterio": {k: evaluar(filas, None if k == "total" else k) for k in ("total", "focal", "nevado")},
            "pasadas": pasadas}


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description="Junta las salidas del probe S141 v2 y aplica el criterio")
    ap.add_argument("--dir", default=str(HERE / "artefactos"))
    a = ap.parse_args(argv)
    out = resumen_total(a.dir)
    (HERE / "criterio_total.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"n_filas": out["n_filas"], "veredictos": {k: v["veredicto"] for k, v in out["criterio"].items()}},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
