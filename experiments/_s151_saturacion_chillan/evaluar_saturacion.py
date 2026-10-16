# -*- coding: utf-8 -*-
"""Tarea 1.18: junta las salidas del probe de saturacion y las cruza con lo que MIROVA publico.

DESCRIPTIVO: entrega conteos y magnitudes, no aplica umbral ni da veredicto.

Referencia: `scripts/referencia_mirova_unificada.py` (consolidado + OCR + historia), bajada del remoto
de Mirova-v1 si hay red; si no, el snapshot commiteado (queda dicho en `procedencia`). Antes de indexar
pasa por `calidad_referencia_mirova.avisar` (A119). Pareo por sensor y +-120 s (banco_paridad.parear,
la misma tolerancia de todo el proyecto).

Uso: python evaluar_saturacion.py <dir con sat_*.json> --salida resumen.json [--tabla tabla.md] [--snapshot]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

VOLCAN = "NevadosDeChillan"
BUCKET = {"V375": "VIIRS375", "V750": "VIIRS750", "MODIS": "MODIS"}


def cargar_salidas(directorio):
    pasadas = []
    for f in sorted(Path(directorio).rglob("sat_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        pasadas.extend(d.get("pasadas", []))
    # un L1B que aparezca en dos tramos (granulo que cruza la medianoche) se cuenta una vez
    vistos, out = set(), []
    for p in sorted(pasadas, key=lambda x: (x.get("datetime_utc") or "", x.get("l1b") or "")):
        if p.get("l1b") in vistos:
            continue
        vistos.add(p.get("l1b"))
        out.append(p)
    return out


def cargar_referencia(snapshot, dest):
    import referencia_mirova_unificada as R
    if snapshot:
        return R.cargar_referencia_unificada(), {"fuente": "snapshot"}
    try:
        info = R.bajar_remoto(Path(dest))
        filas = R.cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                              Path(info["registro_vrp_ocr.csv"]["path"]))
        return filas, {"fuente": "remoto", **{k: v.get("sha") if isinstance(v, dict) else v
                                              for k, v in info.items()}}
    except Exception as e:  # sin red: snapshot, y queda escrito
        return R.cargar_referencia_unificada(), {"fuente": "snapshot (remoto fallo: %s)" % type(e).__name__}


def indexar(filas, desde, hasta):
    """Filas de Chillan de la ventana, por bucket, ordenadas por hora."""
    por_b = defaultdict(list)
    for f in filas:
        if f["volcano"] != VOLCAN or not (desde <= f["fecha_utc"][:10] <= hasta):
            continue
        dt = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
        por_b[f["sensor_bucket"]].append((dt, f))
    for v in por_b.values():
        v.sort(key=lambda x: x[0])
    return por_b


def _mir(conteo, region):
    c = (conteo or {}).get("MIR", {}).get(region, {})
    return {"bit": c.get("bit", 0), "techo": c.get("techo", 0)}


def _tir(p, region):
    fam = p.get("familia")
    b = {"V375": "I05", "V750": "M15", "MODIS": "B31"}.get(fam)
    return ((p.get("conteo") or {}).get(b, {}).get(region, {}) or {}).get("bit", 0)


def fila_tabla(p, ref):
    sin, con = p.get("sin") or {}, p.get("con") or {}
    ts, tc = p.get("tablero_sin") or [None, 0], p.get("tablero_con") or [None, 0]
    cota = p.get("cota_aditiva") or {}
    return {
        "datetime_utc": p.get("datetime_utc"), "familia": p.get("familia"), "plataforma": p.get("plataforma"),
        "noche": p.get("noche"), "estado": p.get("estado"), "l1b": p.get("l1b"),
        "mir_interior": _mir(p.get("conteo"), "interior"), "mir_escena": _mir(p.get("conteo"), "escena"),
        "tir_bit_interior": _tir(p, "interior"),
        "bt_mir_max_valida_interior_k": p.get("bt_mir_max_valida_interior_k"),
        "pc_vrp_sin": sin.get("pc_vrp"), "pc_vrp_con": con.get("pc_vrp"),
        "f5_sin": sin.get("f5_core_vrp_mw"), "f5_con": con.get("f5_core_vrp_mw"),
        "tablero_vrp_sin": ts[0], "tablero_vrp_con": tc[0], "publica_sin": ts[1], "publica_con": tc[1],
        "cota_mw_piso_declarado": cota.get("mw_piso_declarado"), "cota_mw_piso_empirico": cota.get("mw_piso_empirico"),
        "mirova": [{"tipo": f["tipo"], "vrp_mw": f["vrp_mw"], "dist_km": f["dist_km"], "source": f["source"],
                    "fecha_utc": f["fecha_utc"]} for f in ref],
    }


def resumir(filas):
    """Conteos por familia y noche/dia. Sin umbral."""
    g = defaultdict(lambda: defaultdict(float))
    for r in filas:
        k = "%s_%s" % (r["familia"], "noche" if r["noche"] else "dia")
        s = g[k]
        s["pasadas"] += 1
        s["estado_" + str(r["estado"])] += 1
        if r["estado"] != "ok":
            continue
        n = r["mir_interior"]["bit"] + r["mir_interior"]["techo"]
        s["pasadas_con_mir_borrado_interior"] += n > 0
        s["pixeles_mir_borrados_interior_bit"] += r["mir_interior"]["bit"]
        s["pixeles_mir_borrados_interior_techo"] += r["mir_interior"]["techo"]
        s["pixeles_mir_borrados_escena"] += r["mir_escena"]["bit"] + r["mir_escena"]["techo"]
        s["pixeles_tir_bit_interior"] += r["tir_bit_interior"]
        s["pasadas_publica_sin"] += r["publica_sin"] or 0
        s["pasadas_publica_con"] += r["publica_con"] or 0
        s["pasadas_cambia_tablero"] += (r["tablero_vrp_sin"] or 0) != (r["tablero_vrp_con"] or 0)
        s["suma_tablero_vrp_sin_mw"] += r["tablero_vrp_sin"] or 0
        s["suma_tablero_vrp_con_mw"] += r["tablero_vrp_con"] or 0
        s["pasadas_con_mirova_alerta"] += any(m["tipo"].startswith("ALERTA") for m in r["mirova"])
        s["suma_mirova_vrp_alertas_mw"] += sum(m["vrp_mw"] or 0 for m in r["mirova"] if m["tipo"].startswith("ALERTA"))
    return {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in sorted(g.items())}


def mirova_sin_pasada(por_b, filas):
    """Filas de MIROVA de la ventana que no parean con ninguna pasada medida (cobertura, A108)."""
    import banco_paridad as bp
    usadas = set()
    for r in filas:
        for m in r["mirova"]:
            usadas.add((m["fecha_utc"], m["source"]))
    out = []
    for b, lista in por_b.items():
        for dt, f in lista:
            if (f["fecha_utc"], f["source"]) not in usadas and f["tipo"] != "RUTINA":
                out.append({"bucket": b, "fecha_utc": f["fecha_utc"], "tipo": f["tipo"], "vrp_mw": f["vrp_mw"]})
    return sorted(out, key=lambda x: x["fecha_utc"]), bp.TOL_S


def tabla_md(filas, resumen, procedencia, avisos):
    L = ["# Saturacion en Nevados de Chillan (tarea 1.18), tabla generada", "",
         "Referencia MIROVA: %s." % procedencia.get("fuente"), ""]
    if avisos:
        L += ["Avisos de calidad de la referencia (A119):", ""] + ["- " + a for a in avisos] + [""]
    L += ["## Resumen por familia y noche/dia", "", "```", json.dumps(resumen, indent=1, ensure_ascii=False), "```", "",
          "## Pasadas con algun pixel MIR borrado en el radio interior, o con alerta de MIROVA", "",
          "| UTC | familia | noche | MIR bit | MIR techo | TIR bit | tablero sin | tablero con | pc sin | pc con "
          "| cota decl | MIROVA |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in filas:
        n = r["mir_interior"]["bit"] + r["mir_interior"]["techo"]
        alerta = [m for m in r["mirova"] if m["tipo"] != "RUTINA"]
        if r["estado"] != "ok" or (n == 0 and not alerta):
            continue
        mir = "; ".join("%s %s MW" % (m["tipo"], m["vrp_mw"]) for m in r["mirova"]) or "sin fila"
        L.append("| %s | %s | %s | %d | %d | %d | %s | %s | %s | %s | %s | %s |" % (
            r["datetime_utc"], r["familia"], "si" if r["noche"] else "no", r["mir_interior"]["bit"],
            r["mir_interior"]["techo"], r["tir_bit_interior"], r["tablero_vrp_sin"], r["tablero_vrp_con"],
            r["pc_vrp_sin"], r["pc_vrp_con"], r["cota_mw_piso_declarado"], mir))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("salidas")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--tabla", default=None)
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--dest", default=str(AQUI / "_dl_referencia"))
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import calidad_referencia_mirova as Q
    pasadas = cargar_salidas(a.salidas)
    fechas = sorted(p["datetime_utc"][:10] for p in pasadas if p.get("datetime_utc"))
    desde, hasta = (fechas[0], fechas[-1]) if fechas else ("2026-09-28", "2026-09-28")
    avisos = Q.avisar(desde, hasta)                     # A119: antes de indexar
    filas_ref, procedencia = cargar_referencia(a.snapshot, a.dest)
    por_b = indexar(filas_ref, desde, hasta)
    filas = []
    for p in pasadas:
        ref = []
        if p.get("datetime_utc"):
            t = datetime.strptime(p["datetime_utc"], "%Y-%m-%d %H:%M")
            ref = bp.parear(por_b.get(BUCKET[p["familia"]], []), t)
        filas.append(fila_tabla(p, ref))
    resumen = resumir(filas)
    sin_pasada, tol = mirova_sin_pasada(por_b, filas)
    out = {"volcan": VOLCAN, "ventana": [desde, hasta], "procedencia_referencia": procedencia,
           "avisos_calidad": avisos, "tolerancia_pareo_s": tol, "resumen": resumen,
           "mirova_sin_pasada_medida": sin_pasada, "pasadas": filas}
    Path(a.salida).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    if a.tabla:
        Path(a.tabla).write_text(tabla_md(filas, resumen, procedencia, avisos), encoding="utf-8")
    print(json.dumps({"ventana": [desde, hasta], "resumen": resumen,
                      "n_mirova_sin_pasada": len(sin_pasada)}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
