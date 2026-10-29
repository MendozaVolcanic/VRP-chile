# -*- coding: utf-8 -*-
"""Ensayo en seco del candado de MOD-D fase 4 (PREREGISTRO_MODD_F4.md §11 punto 6): de punta a punta, sin red, con
población, identidad y externos DE JUGUETE, por evaluar_f4.main (con archivos, como la lectura real) y con el
predicado del tablero corrido con node.

POR QUÉ. La batería del arnés prueba fila por fila; esto prueba que las filas que escribe el arnés, juntadas en
f4_parte*.jsonl con sus cabeceras, más externos.json armado por externos_f4.py, llegan al veredicto del §7 sin que
ningún control quede en rojo por un defecto de forma (claves, tipos, conteos, procedencia), y que un externo en rojo
lleva a INDECIDIBLE. No mide nada de la vía: las magnitudes y etiquetas son de juguete.

CÓMO. Tres plantillas salen del arnés REAL (probe_f4.medir_pasada sobre escenas sintéticas de Láscar de
probar_probe_f4.py, con el pipeline real, store.append_record y node): FOCO (un píxel caliente en el cráter), NADA y
DOS (un débil junto al cráter y una fuente radiante a ~6 km). Cada fila del juguete es una copia de una plantilla con
otro volcán y otra hora; k_difiere_de_guardado se pone en False (la escena sintética no está en data/). La población
de juguete trae C con exactamente 5.321 pasadas con grilla del censo (N_GRILLAS_CENSO del evaluador sellado) y una cola
E; la identidad de juguete declara todas iguales; externos.json lo arma externos_f4.armar con cabeceras de juguete (el
commit y el sha256 del tablero se pasan en vez de resolverlos con git) y un manifiesto de juguete en OK (el manifiesto
real del candado se comprueba aparte con manifiesto_candado_f4.py).
  ENSAYO 1  todo en orden: el veredicto sale de una fila del §7 que no es la 1 (ningún control en rojo).
  ENSAYO 2  el mismo juguete con UNA cabecera en otro commit: procedencia en rojo y veredicto INDECIDIBLE.
Uso: python ensayo_en_seco_f4.py   (sale 1 si alguno de los dos no da lo esperado; necesita node)
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import evaluar_f4 as E  # noqa: E402
import externos_f4 as X  # noqa: E402
import probar_probe_f4 as T  # noqa: E402
import probe_f4 as A  # noqa: E402

VOLCANES = ("Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica")
HORAS = ("01:35", "03:00", "07:35")
N_C, N_E, DE = 5400, 60, 3
COMMIT, TAG = "c" * 40, "s168-modd-f4-candado-juguete"


def plantilla(tipo):
    """Una fila real del arnés sobre una escena sintética (FOCO se arma sobre NADA con el cráter a 360 K)."""
    v = T.A_volcan(A)
    datos, geo, cr = T.escena(A, {"foco": "nada", "dos": "dos_fuentes"}.get(tipo, tipo))
    if tipo == "foco":
        f, c = cr[0] + 15, cr[1] + 15
        for b, lam in (("band21", A.pm.BAND21_LAMBDA), ("band22", A.pm.BAND22_LAMBDA)):
            datos[b][f, c] = np.float32(A.pm.bt_to_radiance(np.array([360.0]), lam)[0])
    rec, _ = T.espia_recorrer({"estado": "reproduce", "reproduce": True})
    with tempfile.TemporaryDirectory() as out, T.Lectores(A, datos, geo):
        fila = A.medir_pasada(dict(T.PASADA), v, None, T.L1B, T.GEO, datos, Path(out), Path(out) / "arb", recorrer=rec)
    assert fila["estado"] == "ok", fila
    fila.update({"k_difiere_de_guardado": False, "k_reproducida_en_su_sha": None})
    fila.pop("k_sha", None)
    return fila


def horarios():
    d, i = date(2026, 3, 1), 0
    while True:
        for h in HORAS:
            for vol in VOLCANES:
                yield vol, f"{d.isoformat()} {h}", d.isoformat()
        d += timedelta(days=1)
        i += 1


def armar_juguete(pl):
    """Filas y población: protegidas y bajo 1 MW con FOCO (V publica), negativos limpios con NADA y con DOS (K publica
    el débil del cráter, V no), far_ref con DOS. vrp_mirova cerca de la magnitud de V en FOCO."""
    mag_v = float(pl["foco"]["v_slim"]["primary_cluster"]["vrp_mw"])
    gen = horarios()
    plan = [("protegida", "foco")] * 40 + [("bajo1", "foco")] * 40 + [("neg_limpio", "dos")] * 80 + \
           [("far_ref", "dos")] * 30
    plan += [("neg_limpio", "nada")] * (N_C - len(plan))
    filas, pasadas = [], []
    for i, (lab, t) in enumerate(plan):
        vol, dt, noche = next(gen)
        f = copy.deepcopy(pl[t])
        f.update({"vol": vol, "dt": dt, "noche": noche})
        filas.append(f)
        pasadas.append({"vol": vol, "dt": dt, "noche": noche, "lab": lab, "tramo": "C",
                        "vrp_mirova": (mag_v * 1.05 if lab == "protegida" else min(0.9, mag_v)) if lab in
                        ("protegida", "bajo1") else None,
                        "grilla_censo": f"grilla_{i:04d}.npz" if i < E.N_GRILLAS_CENSO else False})
    for j in range(N_E):
        vol = VOLCANES[j % len(VOLCANES)]
        dt = f"2026-10-{17 + j // len(VOLCANES):02d} {HORAS[j % 3]}"
        f = copy.deepcopy(pl["nada"])
        f.update({"vol": vol, "dt": dt, "noche": dt[:10]})
        filas.append(f)
        pasadas.append({"vol": vol, "dt": dt, "noche": dt[:10], "lab": "neg_limpio", "tramo": "E", "vrp_mirova": None,
                        "grilla_censo": False})
    assert sum(1 for p in pasadas if p["grilla_censo"]) == E.N_GRILLAS_CENSO
    return filas, {"pasadas": pasadas, "sin_pasada_nuestra": []}


def escribir_art(d, filas, pob_bytes, commit_por_parte=None):
    art = Path(d) / "art"
    for i in range(DE):
        p = art / f"parte-{i}" / f"f4_parte{i:02d}.jsonl"
        p.parent.mkdir(parents=True)
        c = (commit_por_parte or {}).get(i, COMMIT)
        cab = {"tipo": "cabecera", "parte": i, "de": DE, "modo": "completo", "commit": c, "tag": TAG,
               "sha256_frontend_index": A.sha256_lf(RAIZ / "frontend/index.html"),
               "sha256_poblacion": X.sha256_lf(pob_bytes)}
        lineas = [json.dumps(cab)] + [json.dumps(f, default=float, ensure_ascii=False) for f in filas[i::DE]] + \
                 [json.dumps({"tipo": "pie", "errores": 0})]
        p.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        (p.parent / f"procedencia_{i}.txt").write_text(f"commit {c} ref refs/tags/{TAG}\n", encoding="utf-8")
    return art


def ensayo(nombre, filas, pob, commit_por_parte=None):
    with tempfile.TemporaryDirectory() as d:
        pob_ruta = Path(d) / "poblacion.json"
        pob_ruta.write_text(json.dumps(pob), encoding="utf-8")
        pob_bytes = pob_ruta.read_bytes()
        ident = {"pasadas": [{"vol": p["vol"], "dt": p["dt"], "mismo_granulo": True, "misma_mascara": True,
                              "dvrp": 0.0, "misma_clase": True} for p in pob["pasadas"] if p["grilla_censo"]]}
        (Path(d) / "identidad.json").write_text(json.dumps(ident), encoding="utf-8")
        ref = {"referencia": {"estado": "OK"}, "reetiquetado": {"estado": "OK"},
               "poblacion_sha256": X.sha256_bytes(pob_bytes)}
        (Path(d) / "externos_referencia.json").write_text(json.dumps(ref), encoding="utf-8")
        art = escribir_art(d, filas, pob_bytes, commit_por_parte)
        ext = X.armar(art, TAG, Path(d) / "externos_referencia.json", pob_ruta, commit_tag=COMMIT,
                      sha_tag=A.sha256_lf(RAIZ / "frontend/index.html"), manifiesto={"estado": "OK", "juguete": True})
        (Path(d) / "externos.json").write_text(json.dumps(ext, default=str), encoding="utf-8")
        print(f"\n== {nombre}: externos", {k: ext[k]["estado"] for k in E.EXTERNOS_REQUERIDOS})
        t0 = time.time()
        res = E.main(["--art", str(art), "--poblacion", str(pob_ruta), "--identidad", str(Path(d) / "identidad.json"),
                      "--externos", str(Path(d) / "externos.json"), "--salida", str(Path(d) / "resultado.json")])
        print(f"   ({time.time() - t0:.0f} s)")
        return res, ext


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.time()
    pl = {t: plantilla(t) for t in ("foco", "nada", "dos")}
    for t, f in pl.items():
        print(f"plantilla {t:5s}: pub_runner {f['pub_runner']} | dist {f['dist']} | v_marca {f['v_marca']}")
    filas, pob = armar_juguete(pl)
    print(f"juguete: {len(filas)} filas, {sum(1 for p in pob['pasadas'] if p['grilla_censo'])} con grilla del censo, "
          f"tramo E {sum(1 for p in pob['pasadas'] if p['tramo'] == 'E')}")
    ok = True
    r1, _e1 = ensayo("ENSAYO 1 (todo en orden)", filas, pob)
    rojos = [k for k, c in r1["controles"].items() if E._rojo(c)]
    print("ENSAYO 1 veredicto:", r1["veredicto"], "| controles en rojo:", rojos or "ninguno")
    if rojos or r1["veredicto"] == "INDECIDIBLE":
        ok = False
        print("  FALLA: el ensayo 1 tenía que llegar a un veredicto sin controles en rojo")
    r2, e2 = ensayo("ENSAYO 2 (una cabecera en otro commit)", filas, pob, commit_por_parte={1: "d" * 40})
    print("ENSAYO 2 veredicto:", r2["veredicto"], "| procedencia:", e2["procedencia"]["estado"],
          e2["procedencia"]["malos"][:2])
    if r2["veredicto"] != "INDECIDIBLE" or e2["procedencia"]["estado"] != "INDECIDIBLE":
        ok = False
        print("  FALLA: el ensayo 2 tenía que dar INDECIDIBLE por la procedencia")
    print(f"\nensayo en seco: {'OK' if ok else 'FALLA'} ({(time.time() - t0) / 60:.1f} min)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
