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

Uso: python armar_montaje.py --despacho s172-retro-d2 --origen "MOD-D fase 4=TAG" --origen "V375-E=TAG"
     --origen "V750-B=TAG" --via-dm DIR --ab-dm "MOD-D fase 4=DIR" [--ab-dm ...] --salida montaje.json
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
PENDIENTES = (
    "MOD-D fase 4: comparador de la máscara (campo del record sin fijar)",
    "V375-E: comparador de la lectura lejana (campo del record sin fijar)",
    "V750-B: comparador de la banda de triangulación de V750-A §4.1 (campo del record sin fijar)",
    "re-correr cada pasada distinta con el código del tag de origen (para «explicada_por: hunk»)",
    "qué tag de cada A/B es el de origen (TAGS_MONTAJE_ESPERADOS en leer_retro.py)",
)
TOL_VRP = 1e-3


def listar_diff(tags, despacho):
    partes = []
    for o in ORIGENES:
        r = subprocess.run(["git", "diff", tags[o], despacho, "--", *ARCHIVOS_VIA], cwd=RAIZ, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode != 0:
            raise SystemExit(f"MONTAJE: git diff {tags[o]} {despacho} falló: {r.stderr.strip()[:200]}")
        partes.append(f"=== {o}: git diff {tags[o]} {despacho} -- {' '.join(ARCHIVOS_VIA)}\n"
                      + (r.stdout if r.stdout.strip() else "(sin diferencias)\n"))
    return "".join(partes)


def _vrp(r):
    return float(((r or {}).get("primary_cluster") or {}).get("vrp_mw") or 0.0)


def comparar(via, ab):
    """Pasada por pasada (clave volcán, sensor, hora): presencia, VRP del cúmulo a 0,001 MW y clase de distancia."""
    out = []
    for key in sorted(set(via) | set(ab), key=lambda x: (x[0], str(x[1]), str(x[2]))):
        p = "%s|%s|%s" % (key[0], key[1], str(key[2])[:16])
        rv, ra = via.get(key), ab.get(key)
        if rv is None or ra is None:
            out.append({"pasada": p, "campo": "falta_en_via" if rv is None else "falta_en_ab", "explicada_por": None})
            continue
        if abs(_vrp(rv) - _vrp(ra)) > TOL_VRP:
            out.append({"pasada": p, "campo": "vrp_mw", "via": _vrp(rv), "ab": _vrp(ra), "explicada_por": None})
        elif (rv.get("distance_class") or None) != (ra.get("distance_class") or None):
            out.append({"pasada": p, "campo": "distance_class", "via": rv.get("distance_class"),
                        "ab": ra.get("distance_class"), "explicada_por": None})
    return out


def armar(tags, despacho, via_dm, abs_dm):
    difs = []
    for o in ORIGENES:
        sens = {"MOD-D fase 4": ("MODIS",), "V375-E": ("VIIRS375",), "V750-B": ("VIIRS750",)}[o]
        v = {k: r for k, r in via_dm.items() if L.bucket(k[1]) in sens}
        difs += [dict(x, origen=o) for x in comparar(v, abs_dm.get(o) or {})]
    estado = "PENDIENTE: " + "; ".join(PENDIENTES) if PENDIENTES else "OK"
    return {"estado": estado, "tags": dict(tags), "despacho": despacho, "diff_listado": listar_diff(tags, despacho),
            "diferencias": difs, "pendientes": list(PENDIENTES)}


def _par(s):
    o, _, v = s.partition("=")
    if o not in ORIGENES or not v:
        raise SystemExit(f"MONTAJE: origen desconocido o vacío: {s!r} (orígenes {ORIGENES})")
    return o, v


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--despacho", required=True)
    ap.add_argument("--origen", action="append", required=True)
    ap.add_argument("--via-dm", required=True)
    ap.add_argument("--ab-dm", action="append", default=[])
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    tags = dict(_par(x) for x in a.origen)
    if set(tags) != set(ORIGENES):
        raise SystemExit(f"MONTAJE: hace falta un tag por origen {ORIGENES}")
    via, _ = L.cargar_carpeta(a.via_dm)
    abs_dm = {o: L.cargar_carpeta(d)[0] for o, d in (_par(x) for x in a.ab_dm)}
    out = armar(tags, a.despacho, via, abs_dm)
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"C-MONTAJE: {out['estado'][:80]} | {len(out['diferencias'])} diferencias -> {a.salida}")
    print("validar_montaje:", L.validar_montaje(out)["estado"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
