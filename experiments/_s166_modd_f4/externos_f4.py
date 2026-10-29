# -*- coding: utf-8 -*-
"""Controles externos del candado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §8.7 y §8.8): arma externos.json con las cinco
claves que exige evaluar_f4.EXTERNOS_REQUERIDOS.

POR QUÉ. El evaluador sellado no confía en nada que no venga en `externos`: una clave ausente es INDECIDIBLE. Tres de
las cinco se miden aquí, al leer, contra los artefactos del runner; las otras dos (referencia y re-etiquetado) las mide
reetiquetado_f4.py de la otra mitad del candado y vienen en externos_referencia.json:
  referencia, reetiquetado  se copian de externos_referencia.json tal cual, salvo que esa medición sea de OTRA
                            población: su poblacion_sha256 tiene que ser el de la población local (bytes tal cual o con
                            LF) y la población local la misma que leyeron los jobs (sha256 LF de las cabeceras). Si no,
                            las dos quedan INDECIDIBLE con el motivo (no se mide la referencia de una población y se lee
                            otra).
  manifiesto                manifiesto_candado_f4.comprobar() sobre el checkout de la lectura.
  procedencia               todas las cabeceras de f4_parte*.jsonl en el commit del tag y con el tag, modo «completo»,
                            las partes 0..de-1 una vez cada una, y cada procedencia_N.txt con el mismo commit (§8.8,
                            A108: un despacho partido puede caer sobre dos pipelines).
  predicado                 sha256 LF de frontend/index.html en el tag = el de cada cabecera (el tablero con que el
                            runner corrió node) = el del checkout de la lectura (con que el evaluador corre node).
Las dos preguntas del instrumento: (1) si un job hubiera corrido en otro commit, con otro tablero o en modo humo, ¿se
vería? Sí: procedencia o predicado en INDECIDIBLE (ensayo_en_seco_f4.py lo comprueba). (2) Si faltara
externos_referencia.json, ¿se vería? Sí: referencia y reetiquetado en INDECIDIBLE con «ausente».
Uso: python externos_f4.py --art DIR --tag TAG [--referencia externos_referencia.json] [--salida externos.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))

import evaluar_f4 as E  # noqa: E402  (cargar, EXTERNOS_REQUERIDOS: el contrato sellado)
import manifiesto_candado_f4 as MC  # noqa: E402


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_lf(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def git(*a, raiz=RAIZ, binario=False):
    r = subprocess.run(["git", "-C", str(raiz), *a], capture_output=True, text=not binario)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr if not binario else r.stderr.decode(errors='replace')}")
    return r.stdout


def procedencia(cab, art, commit_tag, tag):
    """§8.8: todos los jobs en el commit del tag."""
    malos = []
    if not cab:
        return {"estado": "INDECIDIBLE", "motivo": "sin cabeceras: no hay jobs que comprobar"}
    for c in cab:
        if c.get("commit") != commit_tag:
            malos.append({"parte": c.get("parte"), "motivo": "commit", "commit": c.get("commit")})
        if c.get("tag") != tag:
            malos.append({"parte": c.get("parte"), "motivo": "tag", "tag": c.get("tag")})
        if c.get("modo") != "completo":
            malos.append({"parte": c.get("parte"), "motivo": "modo", "modo": c.get("modo")})
    des = {c.get("de") for c in cab}
    partes = sorted(c.get("parte") for c in cab)
    esperadas = list(range(des.pop())) if len(des) == 1 and None not in des else None
    if esperadas is None or partes != esperadas:
        malos.append({"motivo": "partes", "partes": partes, "de": sorted(str(d) for d in {c.get("de") for c in cab})})
    for p in sorted(Path(art).glob("**/procedencia_*.txt")):
        m = re.search(r"commit ([0-9a-f]{40})", p.read_text(encoding="utf-8", errors="replace"))
        if not m or m.group(1) != commit_tag:
            malos.append({"archivo": p.name, "motivo": "procedencia_txt", "commit": m and m.group(1)})
    return {"estado": "OK" if not malos else "INDECIDIBLE", "commit_tag": commit_tag, "tag": tag,
            "n_cabeceras": len(cab), "partes": partes, "malos": malos[:30], "n_malos": len(malos)}


def predicado(cab, sha_tag, sha_local):
    distintos = sorted({c.get("sha256_frontend_index") for c in cab} - {sha_tag})
    ok = bool(cab) and not distintos and sha_local == sha_tag
    return {"estado": "OK" if ok else "INDECIDIBLE", "sha256_tag": sha_tag, "sha256_lectura": sha_local,
            "sha256_runner_distintos": distintos}


def referencia_y_reetiquetado(ref, cab, pob_bytes):
    out = {}
    if ref is None:
        return {k: {"estado": "INDECIDIBLE", "motivo": "externos_referencia.json ausente"}
                for k in ("referencia", "reetiquetado")}
    shas_pob = {sha256_bytes(pob_bytes), sha256_lf(pob_bytes)} if pob_bytes is not None else set()
    pob_jobs = {c.get("sha256_poblacion") for c in cab}
    motivo = None
    if ref.get("poblacion_sha256") not in shas_pob:
        motivo = "externos_referencia.json se midió sobre otra población que la local"
    elif pob_bytes is None or pob_jobs != {sha256_lf(pob_bytes)}:
        motivo = "la población local no es la que leyeron los jobs"
    for k in ("referencia", "reetiquetado"):
        v = ref.get(k)
        if not isinstance(v, dict) or "estado" not in v:
            out[k] = {"estado": "INDECIDIBLE", "motivo": f"{k} ausente o sin estado en externos_referencia.json"}
        elif motivo:
            out[k] = dict(v, estado="INDECIDIBLE", motivo=motivo, estado_original=v.get("estado"))
        else:
            out[k] = v
    return out


def armar(art, tag, ruta_ref, ruta_pob, raiz=RAIZ, commit_tag=None, sha_tag=None, manifiesto=None):
    """commit_tag, sha_tag y manifiesto se resuelven con git y con el manifiesto si no se dan (el ensayo los da)."""
    _filas, cab = E.cargar(art)
    commit_tag = commit_tag or git("rev-parse", f"{tag}^{{commit}}", raiz=raiz).strip()
    if sha_tag is None:
        sha_tag = sha256_lf(git("show", f"{tag}:frontend/index.html", raiz=raiz, binario=True))
    sha_local = sha256_lf((Path(raiz) / "frontend/index.html").read_bytes())
    ref = json.loads(Path(ruta_ref).read_text(encoding="utf-8")) if ruta_ref and Path(ruta_ref).exists() else None
    pob_bytes = Path(ruta_pob).read_bytes() if ruta_pob and Path(ruta_pob).exists() else None
    ext = referencia_y_reetiquetado(ref, cab, pob_bytes)
    ext["manifiesto"] = manifiesto if manifiesto is not None else MC.comprobar()
    ext["procedencia"] = procedencia(cab, art, commit_tag, tag)
    ext["predicado"] = predicado(cab, sha_tag, sha_local)
    assert set(E.EXTERNOS_REQUERIDOS) <= set(ext)
    return ext


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--referencia", default=str(AQUI / "externos_referencia.json"))
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion_f4.json"))
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    ext = armar(a.art, a.tag, a.referencia, a.poblacion)
    out = Path(a.salida) if a.salida else Path(a.art) / "externos.json"
    out.write_text(json.dumps(ext, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for k in E.EXTERNOS_REQUERIDOS:
        print(f"  {k:14s} {ext[k].get('estado')}  {ext[k].get('motivo') or ''}")
    print("escrito", out)
    return ext


if __name__ == "__main__":
    main()
