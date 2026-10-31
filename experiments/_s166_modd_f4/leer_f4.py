# -*- coding: utf-8 -*-
"""S168, P2-02 (experiments/_s169/audit_patrones/f2/INFORME.md): envoltorio de la LECTURA de MOD-D fase 4. Arma
externos.json con externos_f4.armar, corre el evaluador sellado (evaluar_f4.main, sin tocarlo) y agrega a
resultado_f4.json la clave `insumos_lectura` con los sha256 de lo que se leyó.

POR QUÉ. El evaluador elige sus insumos por ruta (--poblacion, --identidad, --externos) y no registra cuáles fueron: un
tercero no podía saber con qué archivos se llegó al veredicto, y tras repetir una lectura podía quedar una identidad de
otra corrida. externos_f4 ya deja los sha256 de la población, la identidad y externos_referencia.json, y las versiones,
dentro de controles.procedencia.insumos_lectura (el evaluador copia `procedencia` entera); lo único que no puede ir ahí
es el sha256 del propio externos.json y el de cada f4_parte*.jsonl, y eso lo agrega este envoltorio después de evaluar.
No cambia el veredicto ni ningún control: sólo agrega una clave al resultado.
Uso: python leer_f4.py --art DIR --tag TAG --identidad identidad.json [--poblacion ...] [--referencia ...]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import evaluar_f4 as E  # noqa: E402
import externos_f4 as X  # noqa: E402


def sellar_resultado(ruta_res, art, rutas):
    """Agrega insumos_lectura a resultado_f4.json: sha256 LF y de bytes de cada insumo y de cada f4_parte*.jsonl."""
    res = json.loads(Path(ruta_res).read_text(encoding="utf-8"))
    partes = sorted(glob.glob(str(Path(art) / "**" / "f4_parte*.jsonl"), recursive=True))
    res["insumos_lectura"] = {
        **{k: {"ruta": str(v), "sha256_lf": X.sha_archivo(v), "sha256_bytes": X.sha_archivo(v, lf=False)}
           for k, v in rutas.items()},
        "partes_runner": {Path(p).relative_to(art).as_posix(): X.sha_archivo(p, lf=False) for p in partes},
        "versiones_lectura": X.versiones_lectura(),
    }
    Path(ruta_res).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--identidad", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion_f4.json"))
    ap.add_argument("--referencia", default=str(AQUI / "externos_referencia.json"))
    ap.add_argument("--tag-runner", default=None, help="S170: tag en que corrieron los jobs (procedencia_runner.py)")
    a = ap.parse_args(argv)
    art = Path(a.art)
    ext = X.armar(art, a.tag, a.referencia, a.poblacion, ruta_identidad=a.identidad, tag_runner=a.tag_runner)
    ruta_ext = art / "externos.json"
    ruta_ext.write_text(json.dumps(ext, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ruta_res = art / "resultado_f4.json"
    E.main(["--art", str(art), "--poblacion", a.poblacion, "--identidad", a.identidad, "--externos", str(ruta_ext),
            "--salida", str(ruta_res)])
    sellar_resultado(ruta_res, art, {"poblacion": a.poblacion, "identidad": a.identidad, "externos": ruta_ext,
                                     "externos_referencia": a.referencia})
    print("insumos_lectura agregado a", ruta_res)


if __name__ == "__main__":
    main()
