"""S167: revisa que una corrida de la sombra (.github/workflows/sombra-codigo-mirova.yml) haya producido records de la vía.

POR QUÉ. run_pipeline.py atrapa toda excepción por gránulo, imprime `ERROR processing` y termina con salida 0. Si en el
runner falta una dependencia de la vía (sin pyproj, cada gránulo da error) o el MxD03 no calza, el job queda verde con
«sin cambios» y la sombra no mide nada durante semanas sin que nadie lo note: el pipeline zombie del CLAUDE.md global
(regla 6). Y si la vía no puede correr en un gránulo (`via_codigo_mirova` = "sin_grilla", "sin_mxd03" o
"geo_distinta"), el procesador cae a K y el record de K queda en la carpeta de la sombra: el lector lo tiene que poder
filtrar, pero además hay que verlo el mismo día.

S169 (experiments/_s169/audit_patrones/f3/INFORME_F3.md P3-02 y P3-03, verificador VF3-01, en loop/activo). Hasta
S168 se contaban los records de TODA la ventana de 8 días, que el JSON del checkout ya trae de las corridas
anteriores: desde el segundo día una corrida que no produjo nada salía verde con los records de ayer, un sensor entero
podía faltar mientras los otros dos sostenían el verde, y un record de K caído un día dejaba el job rojo los 8 días
siguientes, tapando cualquier falla nueva. Las rondas 2 y 3 de verificación (experiments/_s169/vigilancia_sombra/
INFORME.md) mostraron que juzgar sólo «lo que escribió hoy» deja pasar un día perdido desde el día siguiente y deja que
la víspera tape un catálogo vacío de hoy. Por eso se juzgan dos cosas distintas:

QUÉ HACE.
  1. ¿Corrió? «De esta corrida» = record de la ventana con `processed_utc` igual o posterior al inicio de la corrida
     (lo anota el workflow antes de llamar a run_pipeline) y con `regimen.codigo_sha` igual al sha del disparo.
     pipeline/store.py reescribe los dos campos cada vez que guarda un record (nuevo o reemplazo NRT->estándar) y no
     toca los que ya estaban. Si esta corrida no escribió ningún record de la vía, es FALLA (corrida muerta).
  2. ¿Está la ventana completa? Después del commit, para cada día d de la ventana desde el 2026-11-03
     (scripts/ventana_sombra.py::FECHA_MINIMA; los días anteriores no son de la sombra) y cada sensor (MODIS, VIIRS 750,
     VIIRS 375), tiene que haber al menos un record de la vía con pasada del día d en el JSON, lo haya escrito esta
     corrida o una anterior. Si no lo hay, la única excusa es una prueba escrita de que no hubo pasada: la cobertura de
     ESTA corrida dice que todas las plataformas vivas del sensor respondieron sin gránulos el día d (incidencia
     `sin_granulos` de pipeline/fetch.py), o que el log de ESTA corrida dice que el filtro nocturno les dejó 0
     gránulos ese día (VR3-01: MODIS con sólo pasadas de día, ver `_solo_de_dia`), o están retiradas por cese
     anunciado. Eso va en una línea NOTA. Sin esa
     prueba es FALLA, sea el día de hoy o uno anterior: un día perdido se sigue viendo hasta que sale de la ventana.
     Un record de K caído no cuenta como record de la vía.
  3. Catálogo vacío (VV169-02): si un mismo día quedan «sin pasada» los tres sensores, o VIIRS 750 y VIIRS 375 a la
     vez, es FALLA. Con dos plataformas VIIRS vivas y 3.000 km de franja, que ninguna pase de noche sobre un volcán
     chileno no es físico: es un catálogo de CMR vacío, como el del 2026-10-18 (R2-13, comentario S159 en fetch.py).
  4. Otras FALLAS: `ERROR processing` en el log; cobertura ausente o ilegible; JSON de la sombra ilegible;
     `--desde-utc` vacío o ilegible; búsquedas o descargas fallidas del día `fin` o sin fecha; algún record de esta
     corrida que no es de la vía. Una falla de búsqueda de un día ANTERIOR a `fin` es NOTA (VV169-03): si ese día quedó
     sin records, el control 2 lo marca por su cuenta.
  5. K caídos (VV169-05): un record de K no se reemplaza solo (pipeline/store.py sólo reemplaza con overwrite o NRT a
     estándar), así que el rojo del día en que se escribe dura una corrida y el record queda. Por eso cada revisión
     escribe, también en verde y también si algo no se pudo leer, la línea «K caídos en la ventana: N», en la salida y
     en el resumen del job (GITHUB_STEP_SUMMARY).
  Nunca sale con traceback por un insumo malo: lo dice en la línea FALLA. Salida 0 = verde, 1 = rojo.

Uso: python scripts/revisar_sombra.py --json data/sombra_codigo_mirova/<Volcan>.json --log pipeline.log
       --cobertura-json cobertura.json --ini A --fin B --desde-utc AAAA-MM-DDTHH:MM:SSZ --sha <GITHUB_SHA>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SENSORES = ("MODIS", "VIIRS750", "VIIRS375")
FECHA_MINIMA = "2026-11-03"   # la misma de scripts/ventana_sombra.py (lo vigila tests/test_revisar_sombra_corrida_s169.py)


def familia(nombre):
    """Sensor o plataforma (MODIS_AQUA, VIIRS_NOAA20, VIIRS_NOAA20_750) a su familia; la convención es la de A48."""
    s = str(nombre or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("_750") else "VIIRS375"
    return None


def _utc(texto):
    try:
        t = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _dias(ini, fin):
    """Los días AAAA-MM-DD de [max(ini, FECHA_MINIMA), fin]; vacío si las fechas no se leen."""
    try:
        a = max(date.fromisoformat(ini), date.fromisoformat(FECHA_MINIMA))
        b = date.fromisoformat(fin)
    except (TypeError, ValueError):
        return []
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


_CABECERA = re.compile(r"^>>> .* \| (\d{4}-\d{2}-\d{2})\s*$")
_FILTRO_NOCHE = re.compile(r"^\s*(\S+): kept (\d+) of (\d+) granules \(night filter\)\s*$")


def _solo_de_dia(log_txt):
    """{(día, plataforma)} cuya búsqueda trajo gránulos y el filtro nocturno los descartó TODOS.

    VR3-01 (S170, experiments/_s169/vigilancia_sombra_verificador/ronda3/INFORME_VERIFICACION_R3.md en loop/activo):
    Terra y Aqua pasan de día y de noche, así que la búsqueda de MODIS casi nunca responde vacía, y pipeline/fetch.py
    no deja `sin_granulos` cuando el filtro nocturno vacía la lista (`if not l1b_granules: continue`). La única
    prueba escrita de que esa noche no hubo pasada es la línea «kept 0 of N granules (night filter)» que fetch.py
    imprime bajo la cabecera «>>> volcán | día» de run_pipeline.py. Si el mismo día y plataforma dejó algún gránulo
    nocturno en otra línea, no es prueba."""
    dia, cero, algo = None, set(), set()
    for ln in log_txt.splitlines():
        m = _CABECERA.match(ln)
        if m:
            dia = m.group(1)
            continue
        m = _FILTRO_NOCHE.match(ln)
        if m and dia is not None:
            (cero if int(m.group(2)) == 0 else algo).add((dia, m.group(1)))
    return cero - algo


def _sin_pasada(sensor, cobertura, dia, solo_de_dia=frozenset()):
    """Lista de plataformas vivas de `sensor` si TODAS respondieron sin gránulos el día `dia`, o sólo con gránulos de
    día (`solo_de_dia`, del log), o están retiradas por cese desde antes de ese día; None si alguna pudo traer gránulos
    nocturnos o si la cobertura no nombra ninguna."""
    plataformas = [p for p in (cobertura.get("plataformas") or {}) if familia(p) == sensor]
    if not plataformas:
        return None
    vacias = {i.get("plataforma") for i in cobertura.get("incidencias") or []
              if i.get("tipo") == "sin_granulos" and i.get("fecha") == dia}
    vacias |= {p for d, p in solo_de_dia if d == dia}
    inicio_dia = _utc(dia + "T00:00:00Z")
    vivas = []
    for p in plataformas:
        c = cobertura["plataformas"][p] or {}
        cese = _utc(c.get("cese_desde")) if c.get("retirada") else None
        if cese is not None and inicio_dia is not None and inicio_dia >= cese:
            continue                                   # retirada ese día (pipeline/fetch.py::cese_cumplido)
        if p not in vacias:
            return None
        vivas.append(p)
    return vivas or None


def revisar(registros, log_txt, ini, fin, desde_utc, cobertura, sha=None, sensores=SENSORES, errores_lectura=()):
    """(ok, resumen). ini y fin en AAAA-MM-DD, inclusive, sobre la fecha UTC de la pasada. `registros`: los records
    del JSON de la sombra, o None si no se pudo leer. `desde_utc`: inicio de la corrida (ISO UTC). `cobertura`: el dict
    de --cobertura-json de run_pipeline, o None. `sha`: el del disparo (GITHUB_SHA); si viene, un record sólo es de esta
    corrida si lo trae. `errores_lectura`: insumos que main no pudo leer, que van como FALLA."""
    fallas, notas = list(errores_lectura), []
    desde = _utc(desde_utc) if desde_utc else None
    if desde is None:
        fallas.append(f"--desde-utc vacío o ilegible ({desde_utc!r}): no se sabe qué escribió esta corrida")
    json_ok = registros is not None
    en_ventana = [r for r in (registros or []) if ini <= str(r.get("datetime_utc") or "")[:10] <= fin]

    def de_esta_corrida(r):
        t = _utc(r.get("processed_utc"))
        if desde is None or t is None or t < desde:
            return False
        return sha is None or (r.get("regimen") or {}).get("codigo_sha") == sha

    nuevos = [r for r in en_ventana if de_esta_corrida(r)]
    via_nuevos = sum(1 for r in nuevos if r.get("via_codigo_mirova") is True)
    otros = {}
    for r in nuevos:
        if r.get("via_codigo_mirova") is not True:
            k = str(r.get("via_codigo_mirova"))
            otros[k] = otros.get(k, 0) + 1
    k_ventana = {}
    for r in en_ventana:
        if r.get("via_codigo_mirova") is not True:
            k = str(r.get("via_codigo_mirova"))
            k_ventana[k] = k_ventana.get(k, 0) + 1
    # pasadas de la vía por (día, sensor), lo haya escrito esta corrida o una anterior
    hay = set()
    for r in en_ventana:
        if r.get("via_codigo_mirova") is True:
            hay.add((str(r.get("datetime_utc") or "")[:10], familia(r.get("sensor"))))
    errores = sum(1 for ln in log_txt.splitlines() if "ERROR processing" in ln)

    if errores:
        fallas.append(f"{errores} gránulos con ERROR processing")
    if cobertura is None:
        fallas.append("no hay JSON de cobertura legible: no se sabe qué se buscó")
    else:
        # VV169-03: sólo las del último día (o sin fecha) dejan rojo; las de días anteriores van como NOTA
        de_hoy, viejas = 0, {}
        for fl in cobertura.get("fallas") or []:
            fecha = str(fl.get("fecha") or "")
            if fecha and fecha < fin:
                viejas[fecha] = viejas.get(fecha, 0) + 1
            else:
                de_hoy += 1
        if de_hoy:
            fallas.append(f"cobertura incompleta: {de_hoy} búsquedas o descargas fallidas del {fin} o sin fecha")
        for fecha in sorted(viejas):
            notas.append(f"{viejas[fecha]} búsquedas o descargas fallidas del {fecha}, día anterior al último "
                         f"(el control por día dice si ese día quedó sin records)")
    if "Cobertura INCOMPLETA" in log_txt and not (cobertura and cobertura.get("fallas")):
        fallas.append("el log dice «Cobertura INCOMPLETA»")
    if otros:
        fallas.append(f"records de esta corrida que no son de la vía: {otros}")
    if json_ok and desde is not None and via_nuevos == 0:
        fallas.append("ningún record de la vía escrito en esta corrida: la corrida no produjo nada")

    dias = _dias(ini, fin)
    solo_de_dia = _solo_de_dia(log_txt)
    if json_ok:
        for d in dias:
            sin_pasada_d = []
            for s in sensores:
                if (d, s) in hay:
                    continue
                vacias = _sin_pasada(s, cobertura or {}, d, solo_de_dia)
                if vacias:
                    sin_pasada_d.append(s)
                    de_dia = [p for p in vacias if (d, p) in solo_de_dia]
                    notas.append(f"{s} {d}: sin records de la vía; miró y no hubo pasada "
                                 f"(búsqueda sin gránulos en {', '.join(vacias)}"
                                 + (f"; de ellas sólo con gránulos de día: {', '.join(de_dia)}" if de_dia else "")
                                 + ")")
                else:
                    fallas.append(f"{s} {d}: ningún record de la vía y ninguna prueba de que no hubo pasada")
            # VV169-02: ningún sensor, o ningún VIIRS, con pasada el mismo día es un catálogo vacío, no la órbita
            if set(sensores) <= set(sin_pasada_d) or {"VIIRS750", "VIIRS375"} <= set(sin_pasada_d):
                fallas.append(f"{d}: sin pasada a la vez en {', '.join(sin_pasada_d)}: catálogo de CMR vacío, "
                              f"no la órbita")

    juzgados = f"{dias[0]} a {dias[-1]}" if dias else "ninguno (antes del %s)" % FECHA_MINIMA
    resumen = (f"ventana {ini} a {fin} (días juzgados: {juzgados}): {len(en_ventana)} records, {len(nuevos)} "
               f"escritos en esta corrida (desde {desde_utc}; {via_nuevos} de la vía), {sum(otros.values())} de "
               f"otra fuente en esta corrida, {errores} errores de gránulo")
    if json_ok:
        resumen += (f"\n  K caídos en la ventana: {sum(k_ventana.values())}"
                    + (f" {k_ventana} (quedan en el JSON: pipeline/store.py no los reemplaza)" if k_ventana else ""))
    else:
        resumen += "\n  K caídos en la ventana: sin dato (el JSON de la sombra no se pudo leer)"
    for n in notas:
        resumen += "\n  NOTA " + n
    if fallas:
        resumen += "\n  FALLA: " + "; ".join(fallas)
    return not fallas, resumen


def _leer_json(ruta, nombre, errores):
    """El contenido de `ruta`, o None si no existe o no se puede leer (y el motivo va a `errores`)."""
    p = Path(ruta)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errores.append(f"{nombre} ilegible ({type(e).__name__})")
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--cobertura-json", required=True)
    ap.add_argument("--ini", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--desde-utc", required=True, help="inicio de la corrida, AAAA-MM-DDTHH:MM:SSZ")
    ap.add_argument("--sha", default=None, help="GITHUB_SHA del disparo")
    a = ap.parse_args(argv)
    errores = []
    datos = _leer_json(a.json, "JSON de la sombra", errores)
    if Path(a.json).exists() and datos is not None and not isinstance(datos, dict):
        errores.append("JSON de la sombra ilegible (no es un objeto)")
        datos = None
    if datos is None and Path(a.json).exists():
        registros = None
    else:
        registros = list((datos or {}).get("records") or [])
    lg = Path(a.log)
    try:
        log_txt = lg.read_text(encoding="utf-8", errors="replace") if lg.exists() else ""
    except OSError as e:
        errores.append(f"log ilegible ({type(e).__name__})")
        log_txt = ""
    cobertura = _leer_json(a.cobertura_json, "cobertura", errores)
    if cobertura is not None and not isinstance(cobertura, dict):
        errores.append("cobertura ilegible (no es un objeto)")
        cobertura = None
    ok, resumen = revisar(registros, log_txt, a.ini, a.fin, a.desde_utc, cobertura, sha=a.sha or None,
                          errores_lectura=errores)
    print(resumen)
    # VV169-05: el resumen del job (GITHUB_STEP_SUMMARY) lleva siempre la línea de K caídos, también en verde
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        try:
            with open(ruta, "a", encoding="utf-8") as fh:
                fh.write("### Revisión de la sombra (%s)\n\n```\n%s\n```\n" % ("OK" if ok else "FALLA", resumen))
        except OSError:
            pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
