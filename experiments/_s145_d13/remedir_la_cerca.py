# -*- coding: utf-8 -*-
"""S145 - D13 remedida: cuanta magnitud apaga hoy la cerca `distance_class != summit`.

POR QUE. D13 (docs/MIROVA_DIVERGENCES.md, "## D13") afirma desde S124 que la cerca del
frontend "apaga el 31 % de la magnitud". El numero tiene unas 20 sesiones y entre medio
cambio el regimen del pipeline: el PR #535 (2026-08-28) apago la mascara de nube y el
#571 (2026-08-31) quito el piso VRP del perfil operacional. Una afirmacion numerica sobre
un corpus vivo no es comparable consigo misma entre sesiones (A90), y un numero viejo no
prueba que el mecanismo siga (reciproco de A87). Esto lo vuelve a medir sobre el regimen
de hoy y, sobre todo, mide el MECANISMO: que condicion del helper dispara y sobre que.

QUE MIDE, por sensor y por volcan, sobre la ventana posterior al #571:
  * conteo: records cuya `distance_class` existe y no es "summit" (la unidad que S124
    reporto en su tabla, aunque el titulo de D13 diga "magnitud");
  * MAGNITUD: MW que el grafico dibuja hoy contra los MW que dibujaria con el toggle
    "incluir lejanas" encendido, que es exactamente levantar la cerca. La diferencia es
    lo que la cerca apaga, y su fraccion es el numero que el titulo de D13 promete;
  * cual de las DOS condiciones del helper dispara (S124 reporto la segunda como no-op);
  * el cruce con MIROVA de lo apagado: pasadas donde MIROVA SI alerto contra pasadas
    donde MIROVA miro y no vio nada, y lo mismo en NOCHES de volcan, que es la unidad en
    que el operador vive una alerta (A94).

COMO. "Publica" y "magnitud" salen del predicado real del dashboard EJECUTADO con node
sobre frontend/index.html, nunca reconstruido a mano (A97). Se reusa scripts/banco_paridad.py
entero (cargar_nuestros, etiquetar, indexar_referencia, correr_node); lo unico propio es el
JS, que evalua el MISMO codigo del dashboard dos veces, con includeFar en false y en true.
El JS conserva en sus 5 primeras posiciones exactamente lo que devuelve el de banco_paridad,
asi que el control de identidad del predicado sigue valiendo como control de instrumento
(A110): si ese control no da el valor esperado, ningun conteo de abajo vale.

La magnitud del grafico es `isThermalArtifact(r, inner) ? 0 : mirovaEqVrpDisplay(r, inner,
includeFar)` (frontend/index.html l. 2258). Con USE_F5_CORE=true, que es el default del
dashboard, en VIIRS 375 eso pasa por `f5_core_vrp_mw` y no por `pc.vrp_mw` (A10/A46): el
JS lo resuelve solo porque es el codigo del dashboard, sin que haya que elegir campo aca.

Fuente de verdad: los JSON de al lado (regla S91). Ningun numero se escribe a mano.
USO: python experiments/_s145_d13/remedir_la_cerca.py [--inicio 2026-09-01] [--fin AAAA-MM-DD]
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

SALIDA = HERE / "remedir_la_cerca.json"

# El mismo runner de banco_paridad, con el cuerpo del map cambiado. Posiciones 0..4
# IDENTICAS a las del original (summit, valid, art, disp, pub) para que
# bp.cargar_nuestros y bp.control_identidad_predicado sigan funcionando sin tocarlos.
# Agrega, a partir de la 5, la evaluacion con includeFar=true y el desglose de que
# condicion del helper devolvio cero.
_JS = bp._JS.replace(
    """const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0];
});""",
    """function cualCondicion(r, inner) {
  // Replica el ORDEN de los returns de mirovaEqVrp para saber cual devolvio 0.
  // No es un predicado nuevo: es la misma cascada, etiquetada.
  if (!r) return "sin_record";
  if (!r.primary_cluster) return "legacy_sin_cumulo";
  if (r.distance_class && r.distance_class !== "summit") return "c1_distance_class";
  const pc = r.primary_cluster;
  if (pc.centroid_dist_km != null && pc.centroid_dist_km > inner) return "c2_cumulo_fuera_inner";
  return "pasa";
}
const out = casos.map(([r, inner]) => {
  const summit = isSummitDetection(r), valid = isValidDetection(r);
  const art = isThermalArtifact(r, inner), disp = mirovaEqVrpDisplay(r, inner, false);
  const dispOn = mirovaEqVrpDisplay(r, inner, true);
  // Los dos filtros de artefacto llaman a mirovaEqVrp con includeFar CLAVADO en false
  // (l. 1215 y l. 1233 de index.html), asi que sobre un record que la cerca apaga ven 0 y
  // nunca disparan: encender el toggle no solo levanta la cerca, tambien deja sin efecto
  // los filtros de cirrus y campo difuso. Para medir el otro escenario, el de QUITAR la
  // cerca del codigo, se le pregunta a la MISMA funcion del dashboard por el mismo record
  // con la etiqueta puesta en summit. Es el predicado real sobre el caso contrafactico,
  // no un predicado reescrito a mano (A97).
  const comoSummit = Object.assign({}, r, {distance_class: "summit"});
  const artSiFueraSummit = isThermalArtifact(comoSummit, inner);
  return [summit ? 1 : 0, valid ? 1 : 0, art ? 1 : 0, disp,
          (summit && valid && !art && disp > 0) ? 1 : 0,
          dispOn, mirovaEqVrp(r, inner, false), mirovaEqVrp(r, inner, true),
          cualCondicion(r, inner), artSiFueraSummit ? 1 : 0];
});""")
# Un .replace que no encuentra su patron no da error: da el texto intacto, y el analisis
# correria sobre el JS viejo sin columnas nuevas. Es la forma silenciosa de A92.
if _JS == bp._JS:
    raise RuntimeError("el cuerpo del map de banco_paridad._JS cambio: revisar el parche del JS")

_CAPTURA = []
_CORRER_NODE_ORIGINAL = bp.correr_node


def _correr_node_capturando(casos):
    """bp.correr_node con el JS de aca, guardando la matriz completa.

    bp.cargar_nuestros solo se queda con dos columnas de la salida; el resto del analisis
    vive en las columnas nuevas, asi que hay que retenerlas. Es un envoltorio, no una
    reimplementacion: la llamada a node la sigue haciendo la funcion original de
    banco_paridad, guardada antes de sustituirla (si llamara a bp.correr_node se llamaria
    a si misma).
    """
    res = _CORRER_NODE_ORIGINAL(casos)
    _CAPTURA.append(res)
    return res


def mag_grafico(art, disp):
    """La magnitud que el grafico dibuja: frontend/index.html l. 2258."""
    return 0.0 if art else (disp or 0.0)


def agregar(sub):
    """Conteos y MW de un subconjunto, siempre con su denominador (A90)."""
    hoy = sum(mag_grafico(r["art"], r["disp"]) for r in sub)
    sin_cerca = sum(mag_grafico(r["art"], r["disp_on"]) for r in sub)
    apagados = [r for r in sub if r["cond"] in ("c1_distance_class", "c2_cumulo_fuera_inner")]
    # Un record "silenciado" es el que la cerca apaga Y que sin ella el grafico dibujaria.
    silenciados = [r for r in apagados if mag_grafico(r["art"], r["disp_on"]) > 0]
    # Denominador de S124, reconstruido: su 10.773/34.763 sale de dividir los no-summit por
    # los records con `primary_cluster.vrp_mw > 0`, no por todos los records. Se reporta
    # aparte para que el 31 % sea comparable con el de hoy en la MISMA unidad (A90).
    con_mag = [r for r in sub if (r["pc_vrp"] or 0) > 0]
    ns_con_mag = [r for r in con_mag if r["cond"] == "c1_distance_class"]
    return {
        "n_records": len(sub),
        "n_cumulos_con_magnitud": len(con_mag),
        "n_no_summit_entre_cumulos_con_magnitud": len(ns_con_mag),
        "pct_denominador_s124": round(100.0 * len(ns_con_mag) / len(con_mag), 2) if con_mag else None,
        "n_no_summit": sum(1 for r in sub if r["cond"] == "c1_distance_class"),
        "pct_no_summit_sobre_records": round(100.0 * sum(1 for r in sub if r["cond"] == "c1_distance_class") / len(sub), 2) if sub else None,
        "n_c2_cumulo_fuera_inner": sum(1 for r in sub if r["cond"] == "c2_cumulo_fuera_inner"),
        "n_legacy_sin_cumulo": sum(1 for r in sub if r["cond"] == "legacy_sin_cumulo"),
        "n_publica_hoy": sum(1 for r in sub if r["pub"]),
        "mw_grafico_hoy": round(hoy, 3),
        "mw_grafico_sin_cerca": round(sin_cerca, 3),
        "mw_apagados_por_la_cerca": round(sin_cerca - hoy, 3),
        "pct_mw_apagados_sobre_sin_cerca": round(100.0 * (sin_cerca - hoy) / sin_cerca, 2) if sin_cerca > 0 else None,
        "n_silenciados": len(silenciados),
        "pct_silenciados_sobre_records": round(100.0 * len(silenciados) / len(sub), 2) if sub else None,
        "etiquetas_de_los_silenciados": dict(collections.Counter(r["lab"] for r in silenciados)),
        # Poder estadistico del cruce: "0 pos silenciados" no dice lo mismo con 200 pasadas
        # pos que con 3. El denominador viaja con la afirmacion (A90).
        "etiquetas_de_todas_las_pasadas": dict(collections.Counter(r["lab"] for r in sub)),
        # Escenario "quitar la cerca del codigo": los filtros de artefacto SI verian estos
        # records y taparian parte de lo que el toggle destapa.
        "n_silenciados_que_el_filtro_de_artefacto_taparia": sum(
            1 for r in silenciados if r.get("art_si_summit")),
        "mw_apagados_que_quedarian_si_se_quita_la_cerca": round(sum(
            mag_grafico(r["art"], r["disp_on"]) for r in apagados if not r.get("art_si_summit")) - 0.0, 3),
    }


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    # Regimen actual: posterior al #571 (2026-08-31 20:34 UTC). Una ventana que lo cruce
    # mezcla dos regimenes y no se puede leer (A104).
    ap.add_argument("--inicio", default="2026-09-01")
    ap.add_argument("--fin", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--etiqueta", default="regimen_actual")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    ventana = (a.inicio, a.fin)

    # Referencia de MIROVA: remoto del dueno, nunca la copia local atrasada (S139).
    info = bp.bajar_remoto(HERE / "_dl_referencia")
    cons = Path(info["registro_vrp_consolidado.csv"]["path"])
    ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    por_vb, noche_sensor, noche_volcan, n_ref = bp.indexar_referencia(
        bp.cargar_referencia_unificada(cons, ocr), coords, ventana)

    # Control de instrumento ANTES de leer nada (A110): con el JS de aca puesto, el
    # predicado del dashboard tiene que seguir dando los mismos valores que el guard S139.
    bp._JS = _JS
    identidad = bp.control_identidad_predicado()
    _CAPTURA.clear()

    bp.correr_node = _correr_node_capturando
    try:
        recs = bp.cargar_nuestros(coords, inner, ventana)
    finally:
        bp.correr_node = _CORRER_NODE_ORIGINAL
    pred = _CAPTURA[0] if _CAPTURA else []
    if len(pred) != len(recs):
        raise RuntimeError("la matriz de node no alinea con los records: %d vs %d" % (len(pred), len(recs)))
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r, p in zip(recs, pred):
        r["art"], r["disp_on"] = bool(p[2]), p[5]
        r["eq_off"], r["eq_on"], r["cond"], r["art_si_summit"] = p[6], p[7], p[8], bool(p[9])

    # A94: el operador vive en NOCHES. Una noche solo se pierde si NINGUNA pasada de esa
    # noche publica hoy; si otra pasada del mismo volcan ya publico, lo apagado es redundante.
    noches_publicadas = {(r["vol"], r["noche"]) for r in recs if r.get("pub")}
    silenciados = [r for r in recs
                   if r["cond"] in ("c1_distance_class", "c2_cumulo_fuera_inner")
                   and mag_grafico(r["art"], r["disp_on"]) > 0]
    noches_pos_tapadas = sorted({f"{r['vol']} {r['noche']}" for r in silenciados
                                 if r["lab"] == "pos" and (r["vol"], r["noche"]) not in noches_publicadas})
    noches_neg_que_se_estrenarian = sorted({f"{r['vol']} {r['noche']}" for r in silenciados
                                            if r["lab"] == "neg_limpio"
                                            and (r["vol"], r["noche"]) not in noches_publicadas})

    out = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "etiqueta_ventana": a.etiqueta,
        "ventana": {"inicio": a.inicio, "fin": a.fin,
                    "por_que": "posterior al #571 (2026-08-31 20:34 UTC) y al #535 (2026-08-28 23:00 UTC)"},
        "sha_index_html": bp.sha_git(bp.HTML),
        "referencia_sha": {k: v.get("sha") for k, v in info.items()},
        "n_filas_ref_nocturnas": n_ref,
        "control_identidad_predicado": identidad,
        "control_identidad_ok": identidad == ([0, 1, 1, 1, 0], [1, 0]),
        "definiciones": {
            "cerca": "frontend/index.html l.1056 y l.1060: mirovaEqVrp devuelve 0 si distance_class "
                     "existe y no es 'summit' (c1), o si pc.centroid_dist_km > inner_radius (c2)",
            "mw_grafico": "isThermalArtifact(r,inner) ? 0 : mirovaEqVrpDisplay(r,inner,includeFar), "
                          "que es la expresion de frontend/index.html l.2258, con USE_F5_CORE=true",
            "sin_cerca": "lo mismo con includeFar=true, que es el toggle 'incluir lejanas' del dashboard",
            "silenciado": "record que la cerca apaga y que sin ella el grafico dibujaria (mw>0)",
            "pos": "MIROVA alerto en esa pasada (pareo +-120 s, CONS u OCR)",
            "neg_limpio": "MIROVA miro esa pasada y no vio nada (RUTINA CONS con vrp 0, sin alerta ni FP)",
            "far_ref": "MIROVA marco FALSO_POSITIVO: calor fuera del limite, sin informacion del crater",
            "sin_info": "sin fila de referencia pareable: fuera de todo denominador",
        },
        # Control de atribucion (A110): toda la diferencia de MW entre "hoy" y "sin la cerca"
        # tiene que venir de records que la cerca apaga. Si un record que PASA la cascada
        # cambiara de magnitud al mover includeFar, la diferencia no seria atribuible a la
        # cerca y el numero de arriba estaria midiendo otra cosa. Debe dar 0 y 0,0.
        "control_atribucion": {
            "n_records_que_pasan_con_magnitud_distinta": sum(
                1 for r in recs if r["cond"] in ("pasa", "legacy_sin_cumulo")
                and abs(mag_grafico(r["art"], r["disp"]) - mag_grafico(r["art"], r["disp_on"])) > 1e-9),
            "mw_de_diferencia_fuera_de_la_cerca": round(sum(
                mag_grafico(r["art"], r["disp_on"]) - mag_grafico(r["art"], r["disp"])
                for r in recs if r["cond"] in ("pasa", "legacy_sin_cumulo")), 6),
            "n_apagados_que_igual_no_dibujarian": sum(
                1 for r in recs if r["cond"] in ("c1_distance_class", "c2_cumulo_fuera_inner")
                and mag_grafico(r["art"], r["disp_on"]) == 0),
        },
        "total": agregar(recs),
        "por_sensor": {b: agregar([r for r in recs if r["b"] == b]) for b in bp.BUCKETS},
        "por_volcan": {v: agregar([r for r in recs if r["vol"] == v]) for v in bp.VOLS},
        "por_volcan_y_sensor": {f"{v}|{b}": agregar([r for r in recs if r["vol"] == v and r["b"] == b])
                                for v in bp.VOLS for b in bp.BUCKETS
                                if any(r["vol"] == v and r["b"] == b for r in recs)},
        "cruce_mirova_de_lo_silenciado": {
            "n_silenciados": len(silenciados),
            "por_etiqueta": dict(collections.Counter(r["lab"] for r in silenciados)),
            "mw_por_etiqueta": {lab: round(sum(mag_grafico(r["art"], r["disp_on"])
                                               for r in silenciados if r["lab"] == lab), 3)
                                for lab in ("pos", "neg_limpio", "far_ref", "sin_info")},
            "en_noches_a94": {
                "noches_con_alerta_de_mirova_hoy_sin_cubrir": noches_pos_tapadas,
                "n_noches_con_alerta_de_mirova_hoy_sin_cubrir": len(noches_pos_tapadas),
                "noches_que_se_estrenarian_sin_confirmacion": noches_neg_que_se_estrenarian,
                "n_noches_que_se_estrenarian_sin_confirmacion": len(noches_neg_que_se_estrenarian),
                "n_noches_volcan_en_la_ventana": len({(r["vol"], r["noche"]) for r in recs}),
                "n_noches_volcan_que_publican_hoy": len(noches_publicadas),
            },
            "silenciados_pos_detalle": sorted(
                [{"vol": r["vol"], "sensor": r["b"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"),
                  "dc": r["dc"], "pc_dist_km": r["pc_dist"],
                  "mw_sin_cerca": round(mag_grafico(r["art"], r["disp_on"]), 3),
                  "noche_ya_cubierta": (r["vol"], r["noche"]) in noches_publicadas}
                 for r in silenciados if r["lab"] == "pos"],
                key=lambda x: (x["vol"], x["dt"])),
        },
        "etiquetas_todas_las_pasadas": dict(collections.Counter(r["lab"] for r in recs)),
    }

    Path(a.salida).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    t = out["total"]
    print(f"escrito {a.salida}")
    print(f"ventana {a.inicio} a {a.fin} ({a.etiqueta}) | identidad del predicado OK: {out['control_identidad_ok']}")
    print(f"control de atribucion (debe dar 0 y 0,0): {out['control_atribucion']}")
    print(f"records nocturnos {t['n_records']} | no-summit {t['n_no_summit']} ({t['pct_no_summit_sobre_records']} %)"
          f" | c2 (cumulo fuera del inner) {t['n_c2_cumulo_fuera_inner']}")
    print(f"en el denominador de S124 (cumulos con magnitud): {t['n_no_summit_entre_cumulos_con_magnitud']}"
          f" / {t['n_cumulos_con_magnitud']} = {t['pct_denominador_s124']} %")
    print(f"MW del grafico hoy {t['mw_grafico_hoy']} | sin la cerca {t['mw_grafico_sin_cerca']}"
          f" | apagados {t['mw_apagados_por_la_cerca']} = {t['pct_mw_apagados_sobre_sin_cerca']} %")
    print(f"silenciados (apagados con magnitud >0): {t['n_silenciados']} -> {t['etiquetas_de_los_silenciados']}")
    print(f"si se quitara la cerca del codigo, el filtro de artefacto taparia"
          f" {t['n_silenciados_que_el_filtro_de_artefacto_taparia']} de esos records y quedarian"
          f" {t['mw_apagados_que_quedarian_si_se_quita_la_cerca']} MW nuevos en el grafico")
    c = out["cruce_mirova_de_lo_silenciado"]["en_noches_a94"]
    print(f"en NOCHES: alerta de MIROVA tapada y sin cubrir {c['n_noches_con_alerta_de_mirova_hoy_sin_cubrir']}"
          f" | noches que se estrenarian sin confirmacion {c['n_noches_que_se_estrenarian_sin_confirmacion']}"
          f" | noches-volcan en la ventana {c['n_noches_volcan_en_la_ventana']}")
    for b in bp.BUCKETS:
        s = out["por_sensor"][b]
        print(f"  {b:9s} n {s['n_records']:5d} | no-summit {s['pct_no_summit_sobre_records']:5} %"
              f" | MW hoy {s['mw_grafico_hoy']:10.2f} sin cerca {s['mw_grafico_sin_cerca']:10.2f}"
              f" -> apaga {s['pct_mw_apagados_sobre_sin_cerca']} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
