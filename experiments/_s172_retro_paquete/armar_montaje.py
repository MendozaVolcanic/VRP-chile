# -*- coding: utf-8 -*-
"""Arma el resultado de C-montaje que lee `leer_retro.py --montaje` (pre-registro SELLADO PREREGISTRO_RETRO_PAQUETE.md,
tag s173-prereg-retro-sellado, §6 C-montaje; VPR2-09, VPR940-06, VPR940b-06).

POR QUÉ, COMO GEÓLOGO. En la ventana DM (2026-10-01 a 10-16) ya corrieron los tres A/B del paquete con el mismo código
de la vía. Si la vía del despacho ve el cráter distinto de como lo vio su A/B en la misma pasada, lo que se lea en F26 y
R25 no es la vía que se midió. C-montaje compara pasada por pasada y exige que cada diferencia la explique un hunk
listado del `git diff` entre el tag de origen y el del despacho, o un cambio de gránulo; nada más cuenta.

QUÉ HACE Y QUÉ NO (no se inventa lo que falta):
  * Hace: el `git diff` del código de la vía entre el tag de cada origen y el del despacho (diff_listado), y la
    comparación pasada por pasada de lo que el §6 nombra para los tres orígenes y se puede leer en cualquier record:
    `primary_cluster.vrp_mw` a 0,001 MW, `distance_class` y la presencia de la pasada.
  * NO hace (PENDIENTES): los campos propios de cada A/B que el §6 nombra y cuyo campo en el record no está fijado
    («máscara» de MOD-D fase 4, «lectura lejana» de V375-E, «banda de triangulación de V750-A §4.1» de V750-B); el
    re-correr una pasada con el código del tag de origen para decidir si un hunk la explica; y qué tag de cada A/B es el
    de origen (TAGS_MONTAJE_ESPERADOS del lector). Mientras PENDIENTES no esté vacío el estado no empieza por OK y
    validar_montaje deja C-montaje en rojo: el control no puede pasar sin esas piezas.
  * Cada diferencia sale con `explicada_por: None`; se llena a mano con «hunk» (y el hunk) u «otro_granulo» después de
    re-correr la pasada, antes de leer F26.

S178 (2026-11-10, opción A aprobada por Nicolás; declaración en experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md de
loop/activo, commit c592ac2d2, escrita antes de correr): los tres comparadores propios y los tags de origen quedan
fijados. Los adaptadores y comparadores viven en montaje_ab.py (pruebas tests/test_montaje_ab_s178.py, mutaciones
mutar_montaje_ab.py). Lo único que sigue a mano es re-correr con el código del tag de origen una diferencia que no
explique otro gránulo: mientras quede una sin explicar, el estado no empieza por OK.

Uso: python armar_montaje.py --despacho s172-retro-d2 --origen "MOD-D fase 4=TAG" --origen "V375-E=TAG"
     --origen "V750-B=TAG" --via-dm DIR --modd DIR [--modd DIR ...] --v375e DIR [...] --v750b DIR=TAG [...]
     --salida montaje.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

_spec = importlib.util.spec_from_file_location("leer_retro_para_montaje", AQUI / "leer_retro.py")
L = importlib.util.module_from_spec(_spec)
sys.modules["leer_retro_para_montaje"] = L
_spec.loader.exec_module(L)

ORIGENES = L.ORIGENES_MONTAJE
# El código de la vía: los archivos de pipeline/ que la escriben o la marcan (grep de via_codigo_mirova y de
# mirova_v750_codigo en pipeline/, 2026-11-05) y la grilla. Es un superconjunto: un hunk fuera de la vía sólo agrega
# texto al diff listado, no explica nada por sí solo.
ARCHIVOS_VIA = ("pipeline/mirova_v750_codigo.py", "pipeline/process_modis.py", "pipeline/process_viirs.py",
                "pipeline/process_viirs_mod.py", "pipeline/profile.py", "pipeline/store.py", "pipeline/grillas_mirova.yaml")
PENDIENTES = ()            # S178: los cinco de S173 quedaron fijados por la declaración (ver arriba)
TOL_VRP = 1e-3

_sm = importlib.util.spec_from_file_location("montaje_ab_para_armar", AQUI / "montaje_ab.py")
MA = importlib.util.module_from_spec(_sm)
sys.modules["montaje_ab_para_armar"] = MA
_sm.loader.exec_module(MA)


def listar_diff(tags, despacho, extra=()):
    partes = []
    for o, t in [(o, tags[o]) for o in ORIGENES] + list(extra):
        r = subprocess.run(["git", "diff", t, despacho, "--", *ARCHIVOS_VIA], cwd=RAIZ, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode != 0:
            raise SystemExit(f"MONTAJE: git diff {t} {despacho} falló: {r.stderr.strip()[:200]}")
        partes.append(f"=== {o}: git diff {t} {despacho} -- {' '.join(ARCHIVOS_VIA)}\n"
                      + (r.stdout if r.stdout.strip() else "(sin diferencias)\n"))
    return "".join(partes)


def armar(tags, despacho, via_idx, refs, extra_tags=()):
    """`via_idx` de montaje_ab.indexar_via; `refs` = {origen: {clave: ref}}. OK sólo si cada origen trae al menos una
    pasada comparada (un A/B sin pasadas no prueba nada) y toda diferencia viene explicada."""
    difs, n = [], {}
    for o in ORIGENES:
        r = refs.get(o) or {}
        n[o] = len(r)
        difs += MA.comparar(via_idx, r, o, comparar_dc=(o == "MOD-D fase 4"))
    vacios = [o for o in ORIGENES if not n[o]]
    sin_expl = [d for d in difs if d["explicada_por"] is None]
    if vacios:
        estado = f"ROJO: sin pasadas comparadas de {vacios}"
    elif sin_expl:
        estado = f"PENDIENTE: {len(sin_expl)} diferencias sin explicar (re-correr con el código del tag de origen)"
    else:
        estado = "OK"
    return {"estado": estado, "tags": dict(tags), "despacho": despacho,
            "diff_listado": listar_diff(tags, despacho, extra_tags), "pasadas_comparadas": n,
            "diferencias": difs, "pendientes": list(PENDIENTES)}


def _par(s, validos=ORIGENES):
    o, _, v = s.partition("=")
    if (validos is not None and o not in validos) or not v:
        raise SystemExit(f"MONTAJE: origen desconocido o vacío: {s!r} (orígenes {ORIGENES})")
    return o, v


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--despacho", required=True)
    ap.add_argument("--origen", action="append", required=True)
    ap.add_argument("--via-dm", required=True)
    ap.add_argument("--modd", action="append", default=[], help="carpeta con f4_parte*.jsonl de MOD-D fase 4")
    ap.add_argument("--v375e", action="append", default=[], help="carpeta con resultados_VIIRS375_*.json de V375-E")
    ap.add_argument("--v750b", action="append", default=[], help="CARPETA=TAG de un run de V750-B")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    tags = dict(_par(x) for x in a.origen)
    if set(tags) != set(ORIGENES):
        raise SystemExit(f"MONTAJE: hace falta un tag por origen {ORIGENES}")
    via, _ = L.cargar_carpeta(a.via_dm)
    via_idx = MA.indexar_via(via)
    modd = MA.cargar_modd(MA.leer_jsonl(sorted(f for c in a.modd for f in Path(c).rglob("f4_parte*.jsonl"))))
    v375 = MA.cargar_v375e(MA.leer_resultados(a.v375e, "resultados_VIIRS375_*.json"))
    v750, extra = {}, []
    for x in a.v750b:
        d, _, t = x.partition("=")
        v750.update(MA.cargar_v750b(MA.leer_resultados([d], "resultados_*.json"), tag=t or None))
        if t and t != tags["V750-B"] and ("V750-B", t) not in extra:
            extra.append(("V750-B", t))
    out = armar(tags, a.despacho, via_idx, {"MOD-D fase 4": modd, "V375-E": v375, "V750-B": v750}, extra)
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    print(f"C-MONTAJE: {out['estado'][:100]} | comparadas {out['pasadas_comparadas']} | "
          f"{len(out['diferencias'])} diferencias -> {a.salida}")
    print("validar_montaje:", L.validar_montaje(out)["estado"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
