# -*- coding: utf-8 -*-
"""S145: cuanto sustrato tiene D25 en VIIRS 750 antes de correr ningun A/B.

POR QUE. La regla S130 dice que la pregunta previa a "mejora algo?" es "llega a ejecutarse?".
D25 cambia el fondo del VRP: hoy es la mediana de un anillo regional de 5 a 25 km y el paper
(Coppola 2016a p. 8 ec. 6) pide la media de la radiancia de los vecinos NO alertados de cada
pixel activo. En una cumbre nevada de noche el anillo esta lleno de valle tibio, asi que el
crater sale mas frio que su propio fondo, el exceso se recorta a cero y el volcan desaparece
por aritmetica. Este script NO decide si conviene: cuenta en cuantas pasadas el cambio podria
actuar, y sobre todo separa las dos poblaciones que el cambio toca en direcciones opuestas.

LAS DOS POBLACIONES.
  (a) RESCATE: cumulo en el crater con magnitud 0,0 MW. Un fondo mas frio las despega de cero.
      Es el mecanismo de las 5 pasadas de docs/audit_s143/PERDIDAS_V750.md.
  (b) EXPOSICION: pasadas que YA publican. Un fondo mas frio les sube la magnitud. Como la
      brecha del proyecto es de SOBRE-publicacion y no de recall (A98), esta poblacion es el
      riesgo, no el premio, y es mucho mas grande que (a).

Cada celda se reporta con su denominador y su ventana (A90). "Publica" es el predicado del
dashboard ejecutado con node, nunca uno reconstruido a mano (A97).

Fuente de verdad: sustrato.json (regla S91). Ningun numero se escribe a mano.
USO: python experiments/_s145_d25_v750/sustrato.py [--inicio 2026-03-01] [--fin AAAA-MM-DD]
"""
import argparse
import collections
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "scripts"):
    sys.path.insert(0, str(p))

import banco_paridad as bp  # noqa: E402

SALIDA = HERE / "sustrato.json"


def noches(recs, etiqueta, noches_publicadas):
    """Noches-volcan de `recs` con esa etiqueta que NINGUNA pasada publicada cubre hoy.

    Es el numero que decide (A94): una pasada rescatada solo agrega algo si su noche no esta ya
    cubierta. Vive en su propia funcion para poder probarla: es la cuenta con la que se discute la
    prioridad del frente, y un instrumento que decide se valida antes de usarse (A110).
    """
    return sorted({f"{r['vol']} {r['noche']}" for r in recs
                   if r.get("lab") == etiqueta
                   and (r["vol"], r["noche"]) not in noches_publicadas})


def clasificar(r, inner_km):
    """Donde cae esta pasada respecto de lo que D25 puede mover.

    El orden importa: es el mismo con que el predicado del dashboard descarta.
    """
    d, v = r.get("pc_dist"), r.get("pc_vrp")
    if d is None:
        return "sin_cumulo"
    if inner_km is not None and d > inner_km:
        return "cumulo_fuera_del_inner"
    if (v or 0) == 0:
        return "rescate_crater_en_cero"
    return "expuesta_ya_tiene_magnitud"


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default=bp.INICIO_DEFECTO)
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    # Referencia de MIROVA: remoto del dueno, nunca la copia local atrasada (S139).
    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(
        bp.cargar_referencia_unificada(cons, ocr), coords, ventana)

    # Control de instrumento antes de leer nada (A110): el predicado de node debe ser el del
    # dashboard. Si el control de identidad falla, los conteos de "publica" no valen.
    identidad = bp.control_identidad_predicado()

    recs = bp.cargar_nuestros(coords, inner, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)

    out = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ventana": {"inicio": a.inicio, "fin": a.fin},
        "control_identidad_predicado": identidad,
        "referencia_sha": {k: v.get("sha") for k, v in info.items()},
        "definiciones": {
            "rescate_crater_en_cero": "cumulo dentro del inner_radius con primary_cluster.vrp_mw == 0",
            "expuesta_ya_tiene_magnitud": "cumulo dentro del inner_radius con magnitud > 0",
            "publica": "predicado del dashboard de frontend/index.html ejecutado con node",
            "pos": "MIROVA alerto en esa pasada (pareo +-120 s)",
            "neg_limpio": "MIROVA miro esa pasada y no vio nada (RUTINA CONS con vrp 0)",
        },
        "por_sensor": {},
    }

    # A94: el operador vive en NOCHES, no en records. Una pasada rescatada solo agrega recall si
    # esa noche de ese volcan no esta ya cubierta por otra pasada que SI publica (de cualquier
    # sensor). Sin esta cuenta, 1035 candidatos parecen 1035 alertas nuevas y no lo son.
    noches_publicadas = {(r["vol"], r["noche"]) for r in recs if r.get("pub")}

    for b in bp.BUCKETS:
        sub = [r for r in recs if r["b"] == b]
        clases = collections.Counter(clasificar(r, inner.get(r["vol"])) for r in sub)
        rescate = [r for r in sub if clasificar(r, inner.get(r["vol"])) == "rescate_crater_en_cero"]
        expuesta = [r for r in sub if clasificar(r, inner.get(r["vol"])) == "expuesta_ya_tiene_magnitud"]
        out["por_sensor"][b] = {
            "n_pasadas_nocturnas": len(sub),
            "clases": dict(clases),
            "rescate": {
                "n": len(rescate),
                "n_pos_mirova_alerto": sum(1 for r in rescate if r["lab"] == "pos"),
                "n_neg_limpio": sum(1 for r in rescate if r["lab"] == "neg_limpio"),
                "n_publica_hoy": sum(1 for r in rescate if r.get("pub")),
                "por_volcan": dict(collections.Counter(r["vol"] for r in rescate)),
                # El premio real, en noches: pasadas con ALERTA de MIROVA cuya noche-volcan NO
                # esta ya cubierta por otra pasada que publica. Todo lo demas es redundante.
                "noches_alerta_hoy_sin_cubrir": noches(rescate, "pos", noches_publicadas),
                # El riesgo real, en noches: pasadas que MIROVA miro y no vio, cuya noche-volcan
                # hoy no publica nada. Despegarlas de cero estrena una alerta que nadie confirma.
                "noches_neg_limpio_que_se_estrenarian": noches(
                    rescate, "neg_limpio", noches_publicadas),
            },
            "expuesta": {
                "n": len(expuesta),
                "n_publica_hoy": sum(1 for r in expuesta if r.get("pub")),
                "n_publica_hoy_y_mirova_no_vio": sum(
                    1 for r in expuesta if r.get("pub") and r["lab"] == "neg_limpio"),
                "n_publica_hoy_y_mirova_alerto": sum(
                    1 for r in expuesta if r.get("pub") and r["lab"] == "pos"),
                "por_volcan": dict(collections.Counter(r["vol"] for r in expuesta)),
            },
        }

    SALIDA.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"escrito {SALIDA}")
    print(f"ventana {a.inicio} a {a.fin} | control de identidad del predicado: {identidad}")
    for b in bp.BUCKETS:
        s = out["por_sensor"][b]
        print(f"\n{b}: {s['n_pasadas_nocturnas']} pasadas nocturnas")
        print(f"  rescate (crater en cero): {s['rescate']['n']}"
              f" | de esas, MIROVA alerto en {s['rescate']['n_pos_mirova_alerto']}")
        print(f"    en NOCHES (A94): alerta hoy sin cubrir"
              f" {len(s['rescate']['noches_alerta_hoy_sin_cubrir'])}"
              f" | noches nuevas que MIROVA no confirma"
              f" {len(s['rescate']['noches_neg_limpio_que_se_estrenarian'])}")
        print(f"  expuesta (ya tiene magnitud): {s['expuesta']['n']}"
              f" | publican hoy {s['expuesta']['n_publica_hoy']}"
              f" | de esas, MIROVA no vio nada en {s['expuesta']['n_publica_hoy_y_mirova_no_vio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
