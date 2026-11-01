"""S172: revisa que una corrida de la guardia K de MODIS (.github/workflows/guardia-k-modis.yml) haya producido K de MODIS.

POR QUÉ. La guardia es K corriendo aparte mientras producción corre la vía «código MIROVA» en MODIS (regla
experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §3, rama loop/activo). Su vigilancia
(scripts/vigilancia_guardia_modis.py) dispara la reversión cuando la guardia publica una alerta protegida que
producción calla. Una guardia muerta, o una guardia que por error corriera la vía, no da error: da VERDE, porque nunca
publica algo que producción calle. run_pipeline.py atrapa toda excepción por gránulo y sale 0, así que el job quedaría
verde y vacío (el pipeline zombie del CLAUDE.md global, regla 6). Esta revisión es la misma defensa que
scripts/revisar_sombra.py da a la sombra, adaptada a lo que la guardia tiene que ser: K pura, sólo MODIS.

QUÉ HACE (reutiliza por import las piezas de scripts/revisar_sombra.py, sin modificarlo):
  1. ¿Corrió? «De esta corrida» = record de la ventana con `processed_utc` desde el inicio de la corrida y
     `regimen.codigo_sha` igual al sha del disparo. Si esta corrida no escribió ningún record de MODIS, FALLA.
  2. ¿Es K? Un record de la ventana con la clave `via_codigo_mirova` (la vía o su caída a K, que sólo existen con el
     flag encendido) es FALLA: la guardia dejó de ser K. Un record de VIIRS o con otro perfil en la marca de régimen
     también.
  3. ¿Está la ventana completa? Cada día de la ventana tiene que tener un record de MODIS, lo haya escrito esta corrida
     o una anterior, o una prueba escrita de que no hubo pasada (búsqueda sin gránulos o filtro nocturno con 0, las
     mismas pruebas que acepta la sombra). Si no, FALLA.
  4. `ERROR processing` en el log, cobertura ausente o con fallas del último día, `--desde-utc` ilegible: FALLA.
  Nunca sale con traceback por un insumo malo: lo dice en la línea FALLA. Salida 0 = verde, 1 = rojo.

Uso: python scripts/revisar_guardia_modis.py --json data/guardia_k_modis/<Volcan>.json --log pipeline.log
       --cobertura-json cobertura.json --ini A --fin B --desde-utc AAAA-MM-DDTHH:MM:SSZ --sha <GITHUB_SHA>
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))
from revisar_sombra import (_cobertura_bien_formada, _leer_json, _sin_pasada, _solo_de_dia,  # noqa: E402
                            _utc, familia)

PERFIL = "guardia_k_modis"


def _dias(ini, fin):
    try:
        a, b = date.fromisoformat(ini), date.fromisoformat(fin)
    except (TypeError, ValueError):
        return []
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def revisar(registros, log_txt, ini, fin, desde_utc, cobertura, sha=None, errores_lectura=()):
    """(ok, resumen). `registros`: los records del JSON de la guardia, o None si no se pudo leer."""
    fallas, notas = list(errores_lectura), []
    try:
        date.fromisoformat(ini)
        date.fromisoformat(fin)
    except (TypeError, ValueError):
        fallas.append(f"--ini o --fin ilegibles ({ini!r}, {fin!r}): no se puede juzgar la ventana por día")
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
    modis_nuevos = sum(1 for r in nuevos if familia(r.get("sensor")) == "MODIS")
    con_via = {}
    for r in en_ventana:
        if "via_codigo_mirova" in r:
            k = str(r.get("via_codigo_mirova"))
            con_via[k] = con_via.get(k, 0) + 1
    no_modis = sum(1 for r in nuevos if familia(r.get("sensor")) != "MODIS")
    otro_perfil = sum(1 for r in nuevos if (r.get("regimen") or {}).get("perfil") not in (None, PERFIL))
    hay = {str(r.get("datetime_utc") or "")[:10] for r in en_ventana if familia(r.get("sensor")) == "MODIS"
           and "via_codigo_mirova" not in r}
    errores = sum(1 for ln in log_txt.splitlines() if "ERROR processing" in ln)

    if errores:
        fallas.append(f"{errores} gránulos con ERROR processing")
    if cobertura is None:
        fallas.append("no hay JSON de cobertura legible: no se sabe qué se buscó")
    else:
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
            notas.append(f"{viejas[fecha]} búsquedas o descargas fallidas del {fecha}, día anterior al último")
    if "Cobertura INCOMPLETA" in log_txt and not (cobertura and cobertura.get("fallas")):
        fallas.append("el log dice «Cobertura INCOMPLETA»")
    if con_via:
        fallas.append(f"records con marca de la vía en la guardia ({con_via}): la guardia dejó de ser K")
    if no_modis:
        fallas.append(f"{no_modis} records de esta corrida que no son de MODIS: la guardia corre sólo MODIS")
    if otro_perfil:
        fallas.append(f"{otro_perfil} records de esta corrida con otro perfil en la marca de régimen")
    if json_ok and desde is not None and modis_nuevos == 0:
        fallas.append("ningún record de MODIS escrito en esta corrida: la corrida no escribió nada")

    dias = _dias(ini, fin)
    solo_de_dia = _solo_de_dia(log_txt)
    if json_ok:
        for d in dias:
            if d in hay:
                continue
            vacias = _sin_pasada("MODIS", cobertura or {}, d, solo_de_dia)
            if vacias:
                notas.append(f"MODIS {d}: sin records de K; miró y no hubo pasada ({', '.join(vacias)})")
            else:
                fallas.append(f"MODIS {d}: ningún record de K y ninguna prueba de que no hubo pasada")

    resumen = (f"ventana {ini} a {fin}: {len(en_ventana)} records, {len(nuevos)} escritos en esta corrida (desde "
               f"{desde_utc}; {modis_nuevos} de MODIS), {errores} errores de gránulo")
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
    ap.add_argument("--desde-utc", required=True)
    ap.add_argument("--sha", default=None)
    a = ap.parse_args(argv)
    errores = []
    datos = _leer_json(a.json, "JSON de la guardia", errores)
    registros = []
    if Path(a.json).exists() and (datos is None or not isinstance(datos, dict)):
        if datos is not None:
            errores.append("JSON de la guardia ilegible (no es un objeto)")
        registros = None
    elif datos is not None:
        registros = datos.get("records") or []
        if not isinstance(registros, list) or not all(isinstance(r, dict) for r in registros):
            errores.append("JSON de la guardia con `records` de forma inesperada (no es una lista de objetos)")
            registros = None
    lg = Path(a.log)
    try:
        log_txt = lg.read_text(encoding="utf-8", errors="replace") if lg.exists() else ""
    except OSError as e:
        errores.append(f"log ilegible ({type(e).__name__})")
        log_txt = ""
    cobertura = _leer_json(a.cobertura_json, "cobertura", errores)
    if cobertura is not None and (not isinstance(cobertura, dict) or not _cobertura_bien_formada(cobertura)):
        errores.append("cobertura de forma inesperada")
        cobertura = None
    try:
        ok, resumen = revisar(registros, log_txt, a.ini, a.fin, a.desde_utc, cobertura, sha=a.sha or None,
                              errores_lectura=errores)
    except (AttributeError, TypeError, KeyError, ValueError) as e:
        ok = False
        resumen = (f"ventana {a.ini} a {a.fin}: no se pudo revisar\n  FALLA: "
                   + "; ".join(errores + [f"insumo de forma inesperada ({type(e).__name__}: {e})"]))
    print(resumen)
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        try:
            with open(ruta, "a", encoding="utf-8") as fh:
                fh.write("### Revisión de la guardia K de MODIS (%s)\n\n```\n%s\n```\n" % ("OK" if ok else "FALLA",
                                                                                         resumen))
        except OSError:
            pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
