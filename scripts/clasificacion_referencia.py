# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · clasificacion_referencia.py  ·  SDA: VRP Chile · ID: VRP-CHILE / eje de referencia
# Objetivo      : decirle al geologo de turno, para cada pasada de satelite, si lo que ve en el
#                 dashboard tambien lo publico MIROVA (el sistema de referencia) o si solo lo
#                 vemos nosotros. No decide la alerta ni esconde nada: solo rotula.
# Logica        : se cruza cada pasada nuestra con el registro de MIROVA del mismo volcan y
#                 sensor a +-2 minutos, y con lo que MIROVA publico esa misma noche.
# Modelo/metodo : reglas deterministicas, cinco valores. No hay aprendizaje automatico ni umbral
#                 fisico: es un cruce contra un CSV, verificable fila por fila.
# Datos entrada : records de data/mirova_equivalent/ (solo lectura) y el registro de MIROVA ya
#                 sincronizado en el repo (consolidado + OCR). Satelital, SIN datos personales.
# Variables     : tolerancia del pareo (120 s), tipo de fila de MIROVA (ALERTA, RUTINA, fuera de
#                 limite), ventana movil de fechas.
# Limitaciones  : (a) la referencia llega tarde (el canal OCR se atrasa dias), asi que un valor
#                 puede cambiar entre corridas: por eso es ventana movil y no sello unico;
#                 (b) "MIROVA miro y no publico" NO distingue calor real que MIROVA no publica
#                 (lago de lava, fumarolas, lacolito) de otra cosa: el dato no lo permite y el
#                 rotulo no lo promete; (c) solo los 11 volcanes con serie continua y solo
#                 pasadas nocturnas; (d) MIROVA tambien se equivoca (A76).
# Refs/datos    : docs/audit_s145/CLASSIFICATION_SUSTRATO_Y_DISENO.md §5.2 y §5.3 (diseno
#                 aprobado), scripts/banco_paridad.py (particion de origen), docs/MISSION.md
#                 (puerta 3: etiqueta descriptiva que no filtra ni toca la deteccion).
# ════════════════════════════════════════════════════════════════════
"""Eje de referencia por pasada, calculado FUERA del pipeline (S146).

POR QUE EXISTE. Medido en S145: detectamos todo lo que MIROVA alerta, pero publicamos bastante mas,
y el operador no tiene como saber cual de las dos cosas esta mirando. Mucho de ese extra es calor
real que MIROVA no publica, asi que no se puede borrar ni rotular con un juicio fisico: toda regla
candidata destruye lo que MIROVA confirma (la mejor marca 397 de 414). Lo unico con etiqueta
objetiva es el cruce con la referencia, y eso es lo que este modulo persiste.

POR QUE FUERA DEL PIPELINE. El pipeline escribe cada record una sola vez, cuando procesa el
granulo, y la referencia llega despues. Ademas el cron NRT escribe data/mirova_equivalent/ cada
2 horas (A47): este modulo solo LEE ese directorio y escribe en un archivo aparte.

POR QUE REUTILIZA EL BANCO. `banco_paridad.etiquetar` ya produce la particion por pasada
(pos, far_ref, neg_limpio, sin_info). Aca no se reescribe: se llama tal cual, y encima se agrega
solo la pregunta "¿MIROVA alerto esa misma noche en otra pasada?", con la misma precedencia que
uso el informe de diseno (experiments/_s145_classification/sustrato_clasificacion.py, `reparto`).
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import SNAP_OCR, cargar_referencia_unificada  # noqa: E402

DATA_RECORDS = ROOT / "data" / "mirova_equivalent"
OUT_DEFECTO = ROOT / "data" / "clasificacion_referencia"
# POR QUE estas dos fuentes: son "la referencia ya sincronizada en el repo". El consolidado de la
# raiz lo refresca sync-mirova-csv.yml cada hora; el OCR solo existe en el snapshot, que el
# auto-audit semanal actualiza. No se baja nada de la red.
CONS_DEFECTO = ROOT / "latest_consolidado.csv"
OCR_DEFECTO = SNAP_OCR
# POR QUE un piso: el 2026-08-28 23:00 UTC cambio el regimen (A104, PR #535 y #571). Una ventana
# que lo cruce mezcla dos sistemas distintos. La ventana movil nunca baja de aca.
PISO_REGIMEN = "2026-09-01"
ESQUEMA = 1

# Los cinco valores del diseno aprobado (§5.2), con su lectura en lenguaje llano. Ninguno emite un
# juicio fisico sobre la anomalia: todos describen QUE HIZO LA REFERENCIA con esa pasada.
VALORES = {
    "mirova_confirmed": "Confirmado por MIROVA: publico alerta en esta misma pasada",
    "mirova_same_night": "Confirmado por MIROVA esa noche: publico alerta en otra pasada del mismo volcan",
    "mirova_silent": "Solo nuestro: MIROVA miro esta pasada y no publico nada",
    "mirova_saw_outside": "MIROVA vio calor fuera del limite del volcan: sin informacion sobre el crater",
    "no_reference": "Sin dato de referencia: MIROVA no listo esta pasada o su registro aun no llega",
}


def valor_de(lab, alerta_esa_noche):
    """Del rotulo del banco al valor del eje. Precedencia identica a la del informe de diseno:
    la alerta de la misma noche manda sobre fuera-de-limite y sobre el silencio, porque el evento
    es el mismo y contarlo como "solo nuestro" inflaria la brecha."""
    if lab == "pos":
        return "mirova_confirmed"
    if alerta_esa_noche:
        return "mirova_same_night"
    if lab == "far_ref":
        return "mirova_saw_outside"
    if lab == "neg_limpio":
        return "mirova_silent"
    return "no_reference"


def clasificar_pasadas(recs, filas_ref, coords, ventana):
    """Agrega `valor` (y `dist_ref_km` cuando aplica) a cada pasada de `recs`, en el lugar."""
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas_ref, coords, ventana)
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    for r in recs:
        nv = noche_volcan.get((r["vol"], r["noche"]), {"alerta": False})
        r["valor"] = valor_de(r["lab"], nv["alerta"])
        r["dist_ref_km"] = r["dist_ref"] if r["valor"] == "mirova_saw_outside" else None
    return recs


def cargar_pasadas(data_dir, coords, ventana):
    """Pasadas nocturnas de los 11 Tier A en la ventana. Solo lectura.

    Mismo recorrido y mismos filtros que `banco_paridad.cargar_nuestros`, SIN el predicado de
    publicacion (que necesita node): el eje de referencia no depende de si publicamos. La clave es
    la de deduplicacion de `pipeline/store.py`: (datetime_utc, sensor)."""
    recs = []
    for vol in bp.VOLS:
        with open(Path(data_dir) / f"{vol}.json", encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            if b is None or not (ventana[0] <= (r.get("datetime_utc") or "")[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                         "clave": f'{r["datetime_utc"]}|{r["sensor"]}'})
    return recs


def construir(data_dir, filas_ref, ventana, coords=None):
    """{volcan: {clave: {"valor": ...}}} para la ventana. No escribe nada."""
    coords = coords or bp._coords_por_volcan()
    recs = clasificar_pasadas(cargar_pasadas(data_dir, coords, ventana), filas_ref, coords, ventana)
    out = {vol: {} for vol in bp.VOLS}
    for r in recs:
        e = {"valor": r["valor"]}
        if r["dist_ref_km"] is not None:
            e["dist_ref_km"] = round(float(r["dist_ref_km"]), 2)  # se redondea AL SERIALIZAR (S142)
        out[r["vol"]][r["clave"]] = e
    return out


def sha_contenido(path):
    """Huella de la referencia usada. Normaliza fin de linea para que no dependa del checkout."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def serializar(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def negar_si_dentro_de_records(ruta):
    """POR QUE: el cron NRT escribe data/mirova_equivalent/ cada 2 h y una escritura ajena ahi es
    una carrera (A47). Vale para TODA ruta de salida del post-proceso, no solo para --out."""
    ruta = Path(ruta).resolve()
    base = DATA_RECORDS.resolve()
    if ruta == base or base in ruta.parents:
        raise SystemExit("ERROR: la salida no puede vivir dentro de data/mirova_equivalent/ (A47)")
    return ruta


def escribir(out_dir, por_volcan, ventana, procedencia):
    """Un JSON por volcan. POR QUE se fusiona: la ventana es movil, y lo que ya salio de la ventana
    se conserva tal como quedo; lo que esta adentro se recalcula entero, porque la referencia
    llega tarde y un valor de ayer puede cambiar hoy. Sin hora de generacion: dos corridas sobre
    el mismo estado dan los mismos bytes."""
    out_dir = negar_si_dentro_de_records(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for vol, nuevas in por_volcan.items():
        path = out_dir / f"{vol}.json"
        previas = {}
        if path.exists():
            previas = json.loads(path.read_text(encoding="utf-8")).get("clasificacion", {})
        fuera = {k: v for k, v in previas.items() if not (ventana[0] <= k[:10] <= ventana[1])}
        doc = {"esquema": ESQUEMA, "volcan": vol, "valores": VALORES,
               "clave": "datetime_utc|sensor (la de deduplicacion de pipeline/store.py)",
               "ventana_ultima_corrida": list(ventana), "referencia": procedencia,
               "clasificacion": {**fuera, **nuevas}}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(serializar(doc))
    return out_dir


def cargar_referencia(cons=CONS_DEFECTO, ocr=OCR_DEFECTO):
    filas = cargar_referencia_unificada(Path(cons), Path(ocr))
    ultimo = {s: max((f["fecha_utc"] for f in filas if f["source"] == s), default=None)
              for s in ("CONS", "OCR")}
    return filas, {"sha_cons": sha_contenido(cons), "sha_ocr": sha_contenido(ocr),
                   "ultima_fila_cons_utc": ultimo["CONS"], "ultima_fila_ocr_utc": ultimo["OCR"]}
