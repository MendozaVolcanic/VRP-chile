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
siguientes, tapando cualquier falla nueva. Ahora se juzga sólo lo que escribió ESTA corrida, y por sensor.

QUÉ HACE.
  - «De esta corrida» = record de la ventana con `processed_utc` igual o posterior al inicio de la corrida (lo anota el
    workflow antes de llamar a run_pipeline) y con `regimen.codigo_sha` igual al sha del disparo. pipeline/store.py
    reescribe los dos campos cada vez que guarda un record (nuevo o reemplazo NRT->estándar) y no toca los que ya
    estaban, así que un record de ayer no puede pasar por uno de hoy.
  - Falla (salida 1, job rojo) si: hubo `ERROR processing` en el log; la cobertura de run_pipeline (--cobertura-json)
    falta o trae búsquedas o descargas fallidas; algún record de esta corrida no es de la vía; o un sensor esperado
    (MODIS, VIIRS 750, VIIRS 375) no tiene ningún record de la vía de esta corrida.
  - La única excepción, escrita en una línea propia: un sensor sin records cuyas plataformas vivas respondieron SIN
    GRÁNULOS el día de hoy (incidencia `sin_granulos` de pipeline/fetch.py) o están retiradas por cese anunciado. Eso es
    «miró y no hubo pasada»: la vía no tiene que inventar records, pero la revisión dice que miró.
  Imprime el resumen igual.

Uso: python scripts/revisar_sombra.py --json data/sombra_codigo_mirova/<Volcan>.json --log pipeline.log
       --cobertura-json cobertura.json --ini A --fin B --desde-utc AAAA-MM-DDTHH:MM:SSZ --sha <GITHUB_SHA>
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SENSORES = ("MODIS", "VIIRS750", "VIIRS375")


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


def _sin_pasada_hoy(sensor, cobertura, fin):
    """Lista de plataformas vivas de `sensor` si TODAS respondieron sin gránulos el día `fin` (o están retiradas por
    cese desde antes de ese día); None si alguna pudo traer gránulos o si la cobertura no nombra ninguna."""
    plataformas = [p for p in (cobertura.get("plataformas") or {}) if familia(p) == sensor]
    if not plataformas:
        return None
    vacias = {i.get("plataforma") for i in cobertura.get("incidencias") or []
              if i.get("tipo") == "sin_granulos" and i.get("fecha") == fin}
    inicio_dia = _utc(fin + "T00:00:00Z")
    vivas = []
    for p in plataformas:
        c = cobertura["plataformas"][p] or {}
        cese = _utc(c.get("cese_desde")) if c.get("retirada") else None
        if cese is not None and inicio_dia is not None and inicio_dia >= cese:
            continue                                   # retirada hoy (pipeline/fetch.py::cese_cumplido)
        if p not in vacias:
            return None
        vivas.append(p)
    return vivas or None


def revisar(registros, log_txt, ini, fin, desde_utc, cobertura, sha=None, sensores=SENSORES):
    """(ok, resumen). ini y fin en AAAA-MM-DD, inclusive, sobre la fecha UTC de la pasada. `desde_utc`: inicio de la
    corrida (ISO UTC). `cobertura`: el dict de --cobertura-json de run_pipeline, o None si no se escribió. `sha`: el del
    disparo (GITHUB_SHA); si viene, un record sólo es de esta corrida si lo trae."""
    desde = _utc(desde_utc)
    if desde is None:
        raise ValueError("desde_utc ilegible: %r" % (desde_utc,))
    en_ventana = [r for r in registros if ini <= str(r.get("datetime_utc") or "")[:10] <= fin]

    def de_esta_corrida(r):
        t = _utc(r.get("processed_utc"))
        if t is None or t < desde:
            return False
        return sha is None or (r.get("regimen") or {}).get("codigo_sha") == sha

    nuevos = [r for r in en_ventana if de_esta_corrida(r)]
    por_sensor = {s: 0 for s in sensores}
    otros = {}
    for r in nuevos:
        if r.get("via_codigo_mirova") is True:
            f = familia(r.get("sensor"))
            if f in por_sensor:
                por_sensor[f] += 1
        else:
            k = str(r.get("via_codigo_mirova"))
            otros[k] = otros.get(k, 0) + 1
    errores = sum(1 for ln in log_txt.splitlines() if "ERROR processing" in ln)

    fallas, notas = [], []
    if errores:
        fallas.append(f"{errores} gránulos con ERROR processing")
    if cobertura is None:
        fallas.append("no hay JSON de cobertura: no se sabe qué se buscó")
    else:
        n_fallas = len(cobertura.get("fallas") or [])
        if n_fallas:
            fallas.append(f"cobertura incompleta: {n_fallas} búsquedas o descargas fallidas")
    if "Cobertura INCOMPLETA" in log_txt and not (cobertura and cobertura.get("fallas")):
        fallas.append("el log dice «Cobertura INCOMPLETA»")
    if otros:
        fallas.append(f"records de esta corrida que no son de la vía: {otros}")
    for s in sensores:
        if por_sensor[s]:
            continue
        vacias = _sin_pasada_hoy(s, cobertura or {}, fin)
        if vacias:
            notas.append(f"{s}: sin records de esta corrida; miró y no hubo pasada el {fin} "
                         f"(búsqueda sin gránulos en {', '.join(vacias)})")
        else:
            fallas.append(f"{s}: ningún record de la vía escrito en esta corrida")

    detalle = ", ".join(f"{s} {por_sensor[s]}" for s in sensores)
    resumen = (f"ventana {ini} a {fin}: {len(en_ventana)} records, {len(nuevos)} escritos en esta corrida (desde "
               f"{desde_utc}; {detalle}), {sum(otros.values())} de otra fuente, {errores} errores de gránulo")
    for n in notas:
        resumen += "\n  NOTA " + n
    if fallas:
        resumen += "\n  FALLA: " + "; ".join(fallas)
    return not fallas, resumen


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
    p = Path(a.json)
    registros = json.loads(p.read_text(encoding="utf-8")).get("records", []) if p.exists() else []
    lg = Path(a.log)
    log_txt = lg.read_text(encoding="utf-8", errors="replace") if lg.exists() else ""
    pc = Path(a.cobertura_json)
    cobertura = json.loads(pc.read_text(encoding="utf-8")) if pc.exists() else None
    ok, resumen = revisar(registros, log_txt, a.ini, a.fin, a.desde_utc, cobertura, sha=a.sha or None)
    print(resumen)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
