# ════════════════════════════════════════════════════════════════════
# FICHA SDA · cobertura_publicada.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Que una pasada que el NRT no pudo medir (busqueda en NASA caida, descarga o lectura fallida)
#                 quede escrita en data/ y el tablero la muestre como «no medida», distinta de «sin anomalia».
# Lógica        : Lee la cobertura de la corrida (run_pipeline.py --cobertura-json: busquedas por dia y
#                 plataforma, fallas e incidencias) y actualiza data/cobertura/<volcan>.json: agrega lo que no se
#                 pudo medir, quita lo que una corrida posterior si midio y marca como cerrado el dia-plataforma
#                 buscado con exito despues de terminado el dia mas la latencia de LANCE.
# Modelo/método : Reglas deterministicas (registro de cobertura). Sin aprendizaje automatico.
# Datos entrada : JSON de cobertura de run_pipeline.py; data/cobertura/<volcan>.json previo; records del volcan
#                 (data/mirova_equivalent/<volcan>.json, solo sensor y fecha). SIN datos personales.
# Variables     : fecha, plataforma, busqueda ok o fallida, pasadas no medidas (minuto y etapa), ventana de 30 dias.
# Limitaciones  : No cambia ninguna deteccion ni ningun valor publicado: solo dice que no se midio. Una busqueda
#                 fallida no dice si habia pasada (el catalogo no respondio). Si la corrida muere antes de escribir
#                 su cobertura, no deja nada (el healthcheck y la corrida roja lo avisan por su lado).
# Refs/datos    : Auditoria externa (Codex, ronda 2), hallazgo F6-112; #1114 (F6-104 y F6-114).
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""S199 (auditoría externa con Codex, ronda 2, F6-112): pasadas no medidas, escritas en data/ para el tablero.

POR QUÉ. Una pasada que el sistema no pudo medir no dejaba ninguna fila en los datos publicados: en data/ una pasada no
medida y una noche sin pasada se veían igual (ausencia), y el tablero las mostraba como «sin anomalía». Para el geólogo
de turno, una caída de NASA se leía como un volcán tranquilo. #1114 ya hacía que el NRT reintentara (nrt-retry.yml) y
que un barrido semanal rellenara los huecos (barrido-huecos.yml), pero nada de eso llegaba a data/ ni al tablero.

QUÉ ES «NO MEDIDA». Por día UTC y plataforma (MODIS_TERRA, VIIRS_NOAA20_750...):
  - busqueda_fallida: la búsqueda en el catálogo de NASA (CMR) no respondió. No se sabe si hubo pasada.
  - pasadas_no_medidas: la búsqueda respondió, pero alguna pasada no se pudo bajar (etapa «descarga»), se bajó y el
    procesador falló («procesamiento»), o llegó sin su archivo de geolocalización («geolocalizacion»).
NO cuentan: la búsqueda que respondió vacía (sin_granulos: puede ser que el satélite no pasó), el día en curso
(dia_parcial), el gránulo procesado sin record (sin_record: casi siempre el descarte de borde legítimo, 171-01) y la
plataforma retirada por cese anunciado (el tablero ya lo dice con frontend/cese_plataformas.js).

CÓMO SE RESUELVE. Cada corrida deja, por día y plataforma que intentó, una observación. Una observación sin fallas
borra lo pendiente de ese día y plataforma (lo midió). Si además se hizo después de terminado el día más la latencia
mínima de LANCE (3 h), el día-plataforma queda CERRADO: una falla posterior ya no lo reabre, porque lo que había se midió
entero (si no, cada caída de CMR volvería a marcar los 8 días de la ventana del NRT, ya medidos). Una pasada pendiente
también se borra si su record aparece en los datos (un reproceso la rellenó). Se guardan 30 días, los mismos que mira el
barrido semanal de huecos (días 9 a 30).

Sólo biblioteca estándar. Uso (nrt.yml y barrido-huecos.yml):

    python scripts/cobertura_publicada.py --entrada cobertura_nrt/X.json --volcan X \
        --archivo data/cobertura/X.json --records data/mirova_equivalent/X.json

Escribe el archivo sólo si cambió lo que dice (no la hora), para no sumar un commit por corrida.
Prueba: tests/test_cobertura_publicada_s199.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESQUEMA = 1
VENTANA_DIAS = 30
# La misma latencia mínima de LANCE NRT que pipeline/fetch.py (LATENCIA_MINIMA_NRT_H); la prueba exige que coincidan.
# No se importa para que este script corra sin las dependencias del pipeline.
LATENCIA_MINIMA_NRT_H = 3
# Incidencias de run_pipeline.py que son una pasada que existió y no se midió, con la etapa que se publica.
ETAPA_DE_INCIDENCIA = {"error_procesamiento": "procesamiento", "sin_geolocalizacion": "geolocalizacion"}


def _utc(s) -> datetime | None:
    try:
        return datetime.strptime(str(s)[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cierre_del_dia(fecha: str) -> datetime:
    """Desde cuándo una búsqueda del día UTC `fecha` ve el día entero: su fin más la latencia mínima de LANCE."""
    d = datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return d + timedelta(days=1, hours=LATENCIA_MINIMA_NRT_H)


def observaciones(cobertura: dict, volcan: str) -> dict:
    """{(fecha, plataforma): {"busqueda_ok", "utc", "pasadas"}} de una corrida, sólo del volcán pedido.

    Una entrada por cada búsqueda que la corrida hizo (cobertura["busquedas"], S199). Una falla o incidencia sin su
    búsqueda (cobertura de antes de S199) abre su propia observación con la hora de la corrida."""
    generado = cobertura.get("generado_utc")
    obs: dict = {}

    def nueva(fecha, plataforma, utc):
        return obs.setdefault((fecha, plataforma), {"busqueda_ok": True, "utc": utc or generado, "pasadas": []})

    for b in cobertura.get("busquedas") or []:
        if b.get("volcan") != volcan or not b.get("fecha") or not b.get("plataforma"):
            continue
        o = nueva(b["fecha"], b["plataforma"], b.get("utc"))
        o["busqueda_ok"] = o["busqueda_ok"] and bool(b.get("ok"))
    for f in cobertura.get("fallas") or []:
        if f.get("volcan") != volcan or not f.get("fecha") or not f.get("plataforma"):
            continue
        o = nueva(f["fecha"], f["plataforma"], None)
        if f.get("etapa") == "busqueda":
            o["busqueda_ok"] = False
        else:
            o["pasadas"].append({"minuto": f.get("pasada"), "etapa": str(f.get("etapa") or "descarga")})
    for i in cobertura.get("incidencias") or []:
        etapa = ETAPA_DE_INCIDENCIA.get(i.get("tipo"))
        if not etapa or i.get("volcan") != volcan or not i.get("fecha") or not i.get("plataforma"):
            continue
        nueva(i["fecha"], i["plataforma"], None)["pasadas"].append({"minuto": i.get("pasada"), "etapa": etapa})
    return obs


def _clave_pasada(p: dict):
    return (str(p.get("minuto") or ""), str(p.get("etapa") or ""))


def actualizar(estado: dict | None, cobertura: dict, volcan: str, ahora: datetime,
               records: list | None = None) -> dict:
    """El estado nuevo de data/cobertura/<volcan>.json después de una corrida (sin la hora de actualización)."""
    estado = estado or {}
    pendientes = {(it["fecha"], it["plataforma"]): dict(it) for it in estado.get("no_medidas") or []
                  if it.get("fecha") and it.get("plataforma")}
    cerrados = {f: set(ps) for f, ps in (estado.get("dias_cerrados") or {}).items()}

    for (fecha, plat), o in sorted(observaciones(cobertura, volcan).items()):
        if plat in cerrados.get(fecha, set()):
            continue                                   # medido entero antes: una falla posterior no lo reabre
        if o["busqueda_ok"] and not o["pasadas"]:
            pendientes.pop((fecha, plat), None)        # esta corrida lo midió
            t = _utc(o["utc"])
            if t is not None and t >= cierre_del_dia(fecha):
                cerrados.setdefault(fecha, set()).add(plat)
            continue
        previo = pendientes.get((fecha, plat)) or {}
        pasadas = sorted({_clave_pasada(p): p for p in o["pasadas"]}.values(), key=_clave_pasada)
        pendientes[(fecha, plat)] = {
            "fecha": fecha, "plataforma": plat,
            "motivo": "busqueda_fallida" if not o["busqueda_ok"] else "pasadas_no_medidas",
            "pasadas": [{"minuto": p.get("minuto"), "etapa": p.get("etapa")} for p in pasadas],
            "desde_utc": previo.get("desde_utc") or o["utc"],
        }

    # Una pasada pendiente cuyo record ya está en los datos (un reproceso o el barrido la rellenó) se midió.
    con_record = {(r.get("sensor"), str(r.get("datetime_utc") or "")[:16]) for r in (records or [])}
    for clave, it in list(pendientes.items()):
        if it["motivo"] != "pasadas_no_medidas":
            continue
        quedan = [p for p in it["pasadas"] if not p.get("minuto") or (it["plataforma"], p["minuto"]) not in con_record]
        if not quedan:
            pendientes.pop(clave)
        else:
            it["pasadas"] = quedan

    desde = (ahora.astimezone(timezone.utc) - timedelta(days=VENTANA_DIAS)).strftime("%Y-%m-%d")
    no_medidas = sorted((it for it in pendientes.values() if it["fecha"] >= desde),
                        key=lambda it: (it["fecha"], it["plataforma"]), reverse=True)
    return {"volcan": volcan, "esquema": ESQUEMA, "ventana_dias": VENTANA_DIAS,
            "no_medidas": no_medidas,
            "dias_cerrados": {f: sorted(ps) for f, ps in sorted(cerrados.items()) if f >= desde and ps}}


def _sin_hora(estado: dict | None) -> dict:
    return {k: v for k, v in (estado or {}).items() if k != "actualizado_utc"}


def _leer_json(ruta: Path):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _escribir_atomico(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(ruta.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, ruta)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entrada", required=True, help="JSON de run_pipeline.py --cobertura-json")
    ap.add_argument("--volcan", required=True)
    ap.add_argument("--archivo", required=True, help="data/cobertura/<volcan>.json (se lee y se reescribe)")
    ap.add_argument("--records", default=None, help="JSON del volcán con sus records (para quitar pasadas ya medidas)")
    ap.add_argument("--ahora", default=None, help="AAAA-MM-DDTHH:MM:SSZ (pruebas)")
    a = ap.parse_args(argv)

    cob = _leer_json(Path(a.entrada))
    if not isinstance(cob, dict):
        print(f"Sin cobertura en {a.entrada}: data/cobertura no cambia (la corrida no la escribió).")
        return 0
    ahora = _utc(a.ahora) if a.ahora else datetime.now(timezone.utc)
    ruta = Path(a.archivo)
    previo = _leer_json(ruta)
    previo = previo if isinstance(previo, dict) else None
    datos = _leer_json(Path(a.records)) if a.records else None
    records = datos.get("records") if isinstance(datos, dict) else None
    nuevo = actualizar(previo, cob, a.volcan, ahora, records=records)
    n = len(nuevo["no_medidas"])
    if previo is not None and _sin_hora(previo) == nuevo:
        print(f"Cobertura publicada de {a.volcan}: sin cambios ({n} día-plataforma no medidos).")
        return 0
    nuevo = {"volcan": nuevo["volcan"], "esquema": nuevo["esquema"], "actualizado_utc": _iso(ahora),
             **{k: v for k, v in nuevo.items() if k not in ("volcan", "esquema")}}
    _escribir_atomico(ruta, nuevo)
    print(f"Cobertura publicada de {a.volcan}: {n} día-plataforma no medidos en {VENTANA_DIAS} días -> {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
