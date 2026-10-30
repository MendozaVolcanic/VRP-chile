# -*- coding: utf-8 -*-
"""S168: pruebas sin red de los arreglos del candado de MOD-D fase 4 en la capa de externos (externos_f4.py,
reetiquetado_f4.py, leer_f4.py). Ninguna toca el evaluador sellado: lo importan y lo llaman.

  SHAS_REF   (VC169-01) todo sha256 de externos_referencia.json que tenga un blob en ESTE repositorio es el sha256 de los
             bytes de ese blob: poblacion_sha256 contra `git -c core.autocrlf=false show HEAD:<poblacion_ruta>`, y el
             sha256_lf de cada capa de capas_referencia contra el blob `blob_head`. Control: el mismo json con el sha de
             la población en CRLF (el defecto que encontró el verificador, 5e0147b0...) tiene que salir con discrepancia,
             y también una capa con un sha cambiado. El campo de las capas es sha256_lf (definido así en poblacion_f4.py)
             y se compara con el blob normalizado a LF: el blob del histórico guarda CRLF dentro de git.
             Las dos copias de Mirova-v1 (copias.*) son de OTRO repositorio y no tienen blob aquí: no se comprueban.
  ATAQUE     (P2-03, VF2-02; el m03 del verificador) en una copia de los archivos del manifiesto: con todo intacto,
             manifiesto y procedencia OK; con evaluar_f4.py cambiado para dar siempre PROPONER ADOPCIÓN y el manifiesto
             regenerado, la comprobación vieja (manifiesto_candado_f4.comprobar sola) sigue en OK, y externos_f4 deja
             manifiesto Y procedencia en INDECIDIBLE (manifiesto distinto del del tag; sha256_evaluar_f4 de las
             cabeceras distinto del archivo local); con el evaluador cambiado SIN regenerar, manifiesto INDECIDIBLE.
  INSUMOS    (P2-02) controles.procedencia.insumos_lectura llega a resultado del evaluador sellado con los sha256 de la
             población, la identidad y externos_referencia.json y la versión de numpy; leer_f4.sellar_resultado agrega
             el sha256 de externos.json y de cada f4_parte*.jsonl.
  FIJOS      (P2-07) el manifiesto lista run_pipeline.py, fetch.py, volcanic_features.yaml y externos_referencia.json.
Uso: python probar_externos_f4.py   (sale 1 si algo falla; sin red, sin node, unos segundos)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_f4 as E  # noqa: E402
import externos_f4 as X  # noqa: E402
import leer_f4 as L  # noqa: E402
import manifiesto_candado_f4 as MC  # noqa: E402

REF = AQUI / "externos_referencia.json"
COMMIT, TAG = "c" * 40, "s168-modd-f4-candado-prueba"


def blob_bytes(spec):
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(RAIZ), "show", spec], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def shas_contra_git(ref, rev="HEAD"):
    """Lista de discrepancias entre los sha256 de externos_referencia.json y los blobs de git. Vacía = todo calza."""
    malos = []
    ruta = ref.get("poblacion_ruta") or "experiments/_s166_modd_f4/poblacion_f4.json"
    b = blob_bytes(f"{rev}:{ruta}")
    if b is None:
        malos.append(("poblacion", "sin blob", ruta))
    elif ref.get("poblacion_sha256") != hashlib.sha256(b).hexdigest():
        malos.append(("poblacion", ref.get("poblacion_sha256"), hashlib.sha256(b).hexdigest()))
    for nom, capa in ((ref.get("referencia") or {}).get("capas_referencia") or {}).items():
        b = blob_bytes(capa.get("blob_head") or "")
        # el campo se llama sha256_lf y así lo define poblacion_f4.py (l. 378): sha256 con CRLF normalizado a LF. Se
        # compara con el blob normalizado igual; el blob del histórico trae CRLF DENTRO de git (2.504 líneas), así que
        # el sha de sus bytes crudos es otro (4ca2f925...) y no es el que se registra
        if b is None:
            malos.append((f"capa {nom}", "sin blob", capa.get("blob_head")))
        else:
            sha_lf = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()
            if capa.get("sha256_lf") != sha_lf:
                malos.append((f"capa {nom}", capa.get("sha256_lf"), sha_lf))
    return malos


def t_shas_ref():
    ref = json.loads(REF.read_text(encoding="utf-8"))
    malos = shas_contra_git(ref)
    assert not malos, f"sha256 de externos_referencia.json que no son el del blob en git: {malos}"
    n_capas = len((ref.get("referencia") or {}).get("capas_referencia") or {})
    assert n_capas == 2, n_capas
    b = blob_bytes(f"HEAD:{ref['poblacion_ruta']}")
    malo = dict(ref, poblacion_sha256=hashlib.sha256(b.replace(b"\n", b"\r\n")).hexdigest())
    assert shas_contra_git(malo), "el control (sha de la población en CRLF) no se vio"
    malo2 = json.loads(json.dumps(ref))
    malo2["referencia"]["capas_referencia"]["historico"]["sha256_lf"] = "0" * 64
    assert shas_contra_git(malo2), "el control (sha de una capa cambiado) no se vio"
    return f"población y {n_capas} capas calzan con sus blobs; los controles (CRLF y capa cambiada) se ven"


def copiar_raiz(d):
    """Copia a d cada archivo del manifiesto vigente y de los FIJOS, y escribe allí un manifiesto propio («el del tag»)."""
    m = json.loads(MC.MANIFIESTO.read_text(encoding="utf-8"))
    arch = sorted(set(m["archivos"]) | {a for a in MC.FIJOS if (RAIZ / a).exists()})
    for a in arch:
        (d / a).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RAIZ / a, d / a)
    return regenerar(d, arch)


def regenerar(d, arch):
    t = {"tag": None, "commit_tag": None, "archivos": {a: MC.sha256_lf(d / a) for a in arch},
         "faltaban_al_escribir": []}
    (d / X.REL_MANIFIESTO).write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    return arch


def art_de_juguete(d, raiz):
    art = d / "art"
    for i in range(2):
        p = art / f"parte-{i}" / f"f4_parte{i:02d}.jsonl"
        p.parent.mkdir(parents=True)
        cab = {"tipo": "cabecera", "parte": i, "de": 2, "modo": "completo", "commit": COMMIT, "tag": TAG,
               "sha256_frontend_index": X.sha_archivo(raiz / "frontend/index.html"),
               "sha256_poblacion": X.sha_archivo(raiz / "experiments/_s166_modd_f4/poblacion_f4.json"),
               "sha256_evaluar_f4": X.sha_archivo(raiz / X.REL_EVALUAR),
               "sha256_probe_f4": X.sha_archivo(raiz / X.REL_PROBE),
               "versiones": {"python": "3.11.0", "numpy": "2.4.4", "scipy": "1.17.1"}}
        p.write_text(json.dumps(cab) + "\n" + json.dumps({"tipo": "pie", "errores": 0}) + "\n", encoding="utf-8")
        (p.parent / f"procedencia_{i}.txt").write_text(f"commit {COMMIT} ref refs/tags/{TAG}\n", encoding="utf-8")
    return art


def armar_en(raiz, art, man_tag):
    C = raiz / "experiments/_s166_modd_f4"
    return X.armar(art, TAG, C / "externos_referencia.json", C / "poblacion_f4.json", raiz=raiz, commit_tag=COMMIT,
                   sha_tag=X.sha_archivo(raiz / "frontend/index.html"), manifiesto_tag=man_tag)


def t_ataque():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "raiz"
        arch = copiar_raiz(d)
        man_tag = (d / X.REL_MANIFIESTO).read_bytes()
        art = art_de_juguete(Path(td), d)
        e0 = armar_en(d, art, man_tag)
        assert e0["manifiesto"]["estado"] == "OK" and e0["procedencia"]["estado"] == "OK", \
            (e0["manifiesto"], e0["procedencia"]["malos"])
        ev = d / X.REL_EVALUAR
        texto = ev.read_text(encoding="utf-8")
        assert "def veredicto(res):" in texto
        ev.write_text(texto.replace("def veredicto(res):", "def veredicto(res):\n    return 'PROPONER ADOPCIÓN'\n\n"
                                                          "def _veredicto_viejo(res):", 1), encoding="utf-8")
        e1 = armar_en(d, art, man_tag)                      # control: cambiado sin regenerar
        assert e1["manifiesto"]["estado"] == "INDECIDIBLE", e1["manifiesto"]
        regenerar(d, arch)                                  # el ataque: manifiesto regenerado con el evaluador cambiado
        viejo = MC.comprobar(d / X.REL_MANIFIESTO, d)
        assert viejo["estado"] == "OK", "la comprobación vieja ya no se deja engañar: el caso no reproduce el m03"
        e2 = armar_en(d, art, man_tag)
        assert e2["manifiesto"]["estado"] == "INDECIDIBLE", e2["manifiesto"]
        assert e2["manifiesto"]["motivo"] == "el manifiesto de la lectura no es el del tag"
        assert e2["procedencia"]["estado"] == "INDECIDIBLE"
        assert {m["motivo"] for m in e2["procedencia"]["malos"]} == {"sha256_evaluar_f4"}, e2["procedencia"]["malos"]
        res = E.evaluar([], [], {}, e2, [], lambda c: [(0, 0.0)] * len(c))
        assert res["veredicto"] == "INDECIDIBLE" and E._rojo(res["controles"]["manifiesto"]) \
            and E._rojo(res["controles"]["procedencia"])
    return "intacto OK; cambiado sin regenerar: manifiesto rojo; cambiado + regenerado: comprobar viejo OK y " \
           "externos con manifiesto y procedencia en rojo, veredicto INDECIDIBLE"


def t_insumos():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "raiz"
        copiar_raiz(d)
        art = art_de_juguete(Path(td), d)
        idn = Path(td) / "identidad.json"
        idn.write_text(json.dumps({"poblacion": "p", "art": "a", "censo": "c", "pasadas": []}), encoding="utf-8")
        C = d / "experiments/_s166_modd_f4"
        ext = X.armar(art, TAG, C / "externos_referencia.json", C / "poblacion_f4.json", raiz=d, commit_tag=COMMIT,
                      sha_tag=X.sha_archivo(d / "frontend/index.html"),
                      manifiesto_tag=(d / X.REL_MANIFIESTO).read_bytes(), ruta_identidad=idn)
        res = E.evaluar([], [], {}, ext, [], lambda c: [(0, 0.0)] * len(c))
        ins = res["controles"]["procedencia"]["insumos_lectura"]
        assert ins["poblacion"]["sha256_lf"] == X.sha_archivo(C / "poblacion_f4.json")
        assert ins["identidad"]["sha256_lf"] == X.sha_archivo(idn) and ins["identidad"]["registra"]["art"] == "a"
        assert ins["externos_referencia"]["sha256_lf"] == X.sha_archivo(C / "externos_referencia.json")
        assert ins["versiones_lectura"]["numpy"] and ins["versiones_runner"] and \
            ins["versiones_runner_distintas_entre_cabeceras"] is False
        assert ins["manifiesto"]["lectura"] == ins["manifiesto"]["tag"]
        rr = Path(td) / "resultado_f4.json"
        rr.write_text(json.dumps(res, default=str), encoding="utf-8")
        ex = Path(td) / "externos.json"
        ex.write_text(json.dumps(ext, default=str), encoding="utf-8")
        s = L.sellar_resultado(rr, art, {"poblacion": C / "poblacion_f4.json", "identidad": idn, "externos": ex})
        assert s["insumos_lectura"]["externos"]["sha256_bytes"] == X.sha_archivo(ex, lf=False)
        assert len(s["insumos_lectura"]["partes_runner"]) == 2
        assert json.loads(rr.read_text(encoding="utf-8"))["veredicto"] == res["veredicto"]
    return "insumos_lectura dentro de controles.procedencia del resultado; leer_f4 agrega externos.json y las 2 partes"


def t_fijos():
    falta = [a for a in ("scripts/run_pipeline.py", "pipeline/fetch.py", "pipeline/volcanic_features.yaml",
                         "experiments/_s166_modd_f4/externos_referencia.json") if a not in MC.FIJOS]
    assert not falta, falta
    assert all((RAIZ / a).exists() for a in MC.FIJOS), [a for a in MC.FIJOS if not (RAIZ / a).exists()]
    return "los 4 archivos de P2-07 están en FIJOS y todos los FIJOS existen"


ESCENARIOS = [t_shas_ref, t_ataque, t_insumos, t_fijos]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("pruebas de la capa de externos (externos_f4.py sha256 LF %s)" % X.sha_archivo(AQUI / "externos_f4.py"))
    res = {}
    for t in ESCENARIOS:
        try:
            res[t.__name__] = ("OK", t())
        except AssertionError as e:
            res[t.__name__] = ("FALLA", str(e)[:400])
        except Exception as e:  # noqa: BLE001
            res[t.__name__] = ("CAE", f"{type(e).__name__}: {e} | {traceback.format_exc()[-500:]}")
        print(f"  {res[t.__name__][0]:5s} {t.__name__:12s} {res[t.__name__][1]}", flush=True)
    n_ok = sum(v[0] == "OK" for v in res.values())
    print(f"RESUMEN: {n_ok} de {len(res)} OK")
    sys.exit(0 if n_ok == len(res) else 1)


if __name__ == "__main__":
    main()
