# -*- coding: utf-8 -*-
"""S192: lleva a «escena no medida» los records MODIS de la vía guardados con fondo nulo (sigue a #1065, ficha v1.51).

POR QUÉ. El VRP es el exceso de radiancia del píxel caliente sobre el suelo que tendría sin la anomalía. Cuando todos
los alertados de una pasada quedan junto a un hueco de datos, el código de MIROVA no puede interpolar su fondo y lo
suma como cero: publica la radiancia entera como si fuera exceso. En MODIS, MIROVA nunca publica una detección así
(0 en 262.455 del OSF v2.5) y el único caso cotejable fue un falso positivo nuestro, así que Nicolás decidió el
2026-11-20 (opción a) que esa escena es no medida. #1065 lo hace en `pipeline/mirova_v750_codigo.py::procesar_grilla`
(condición `sin_fondo_modis`), pero sólo para las pasadas nuevas: los records ya guardados siguen con la cifra vieja.

QUÉ HACE. Recorre data/mirova_equivalent, data/historia_34 y data/sombra_34 y, en cada record MODIS de la vía
(`via_codigo_mirova` true) con `diag_codigo_mirova.L_bk == 0` exacto y algún alertado, deja la forma exacta de la rama
vacía de `procesar_grilla`: 0 MW, sin píxeles, cúmulo, clase, temperaturas y posiciones nulas, `motivo_vacio`
«fondo_no_estimado» y `alertados_sin_fondo` = el `n_anomalous_pixels` anterior; conserva `L_hot`, `L_bk` y el resto del
diagnóstico, la geometría, el gránulo, `processed_utc` y `regimen` (la detección la hizo ese código; sólo cambia qué se
publica de ella). No toca VIIRS (MIROVA sí publica con fondo 0 en VIIRS), ni MODIS con fondo, ni records de K.

POR QUÉ EQUIVALE A REPROCESAR. `L_bk` es la suma de los fondos que existen (nansum). Un fondo interpolado es radiancia
de suelo, positiva, así que un solo alertado con fondo da `L_bk > 0`; `L_bk == 0` exacto con alertados significa que
ninguno lo tuvo, que es justo la condición `n_sin_fondo == npix` con que la vía nueva toma la rama vacía. La prueba
tests/test_reemplazo_fondo_nulo_s192.py lo comprueba sobre la pasada real 3933 (Cordón Caulle 2026-03-16 03:10).

FORMA DE ESCRITURA. Cada archivo se reescribe con el mismo formato con que estaba (sangría, ASCII y saltos de línea):
el script prueba los formatos conocidos y rehúsa si ninguno reproduce el archivo byte a byte, para no reformatear un
JSON entero por cambiar un record. Un archivo sin records objetivo no se abre para escribir.

USO
  python experiments/_s192_fondo_nulo/reemplazo_fondo_nulo.py --informe <ruta> [--aplicar]
Sin --aplicar es un ensayo: no escribe nada y el informe dice cuántos records cambiaría por carpeta y volcán.
Determinista e idempotente: una segunda pasada no encuentra nada que cambiar. Lo corre aplicar-reemplazo.yml vía
aplicar_fondo_nulo.sh, sólo con el sí de Nicolás (A45).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CARPETAS = ("data/mirova_equivalent", "data/historia_34", "data/sombra_34")
MOTIVO = "fondo_no_estimado"

# Claves que la rama vacía de procesar_grilla deja nulas (o vacías), en el orden en que las escribe.
NULAS = ("primary_cluster", "t_bg_k", "distance_class", "t_max_k", "hotspot_lat", "hotspot_lon", "hotspot_dist_km",
         "final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km", "final_hotspot_source")
# Claves de primer nivel que un record de la vía puede traer y que el reemplazo conoce: las de procesar_grilla, las
# que agregan calcular_vrp_granulo y process_modis (ángulos, gránulo, fecha) y las de store.py que también llevan las
# escenas vacías (processed_utc, regimen, first_processed_utc). Cualquier otra (p. ej. diag_vrp_raw_mw del piso o una
# marca de descarte de store.py) existe sólo porque había VRP: con ella el record no tendría la forma de una escena
# vacía guardada, y el script rehúsa en vez de adivinar qué hacer.
CONOCIDAS = set(NULAS) | {
    "sensor", "triggered_test1", "vrp_vent_mw", "via_codigo_mirova", "n_anomalous_pixels", "diag_codigo_mirova",
    "vrp_mw", "anomaly_pixels", "sensor_zenith_deg", "sensor_azimuth_deg", "solar_zenith_deg", "solar_azimuth_deg",
    "granule", "product_version", "datetime_utc", "processed_utc", "regimen", "first_processed_utc"}
# Formatos con que el repo escribe estos JSON: store.py (indent 2, ASCII) y aplicar_historia_34.py (indent 1, UTF-8).
FORMATOS = ({"indent": 2, "ensure_ascii": True}, {"indent": 1, "ensure_ascii": False},
            {"indent": 2, "ensure_ascii": False}, {"indent": 1, "ensure_ascii": True})


class Rehusado(Exception):
    pass


def es_objetivo(r: dict) -> bool:
    """Record MODIS de la vía guardado con fondo nulo: ningún alertado tuvo fondo, y todavía publica algo."""
    dg = r.get("diag_codigo_mirova") or {}
    return (str(r.get("sensor", "")).startswith("MODIS") and r.get("via_codigo_mirova") is True
            and dg.get("L_bk") is not None and dg.get("L_bk") == 0 and (r.get("n_anomalous_pixels") or 0) > 0)


def transformar(r: dict) -> dict:
    """El record en la forma de la rama vacía de procesar_grilla con motivo «fondo_no_estimado». Muta y devuelve r.

    vrp_mw queda en 0 entero, como lo guarda store.py en toda escena vacía de la vía (round(max(0, 0.0), 3) da 0):
    así el record es indistinguible de uno que la vía nueva hubiera escrito. Las claves que ya existían conservan su
    posición; alertados_sin_fondo entra tras L_bk, donde la escribe procesar_grilla."""
    extra = set(r) - CONOCIDAS
    if extra:
        raise Rehusado(f"REHUSADO: {r.get('sensor')} {r.get('datetime_utc')} trae claves que una escena vacía no "
                       f"tiene: {sorted(extra)}")
    n = int(r["n_anomalous_pixels"])
    dg = r["diag_codigo_mirova"]
    nuevo = {}
    for k, v in dg.items():
        if k == "alertados_sin_fondo":
            continue
        nuevo[k] = v
        if k == "L_bk":
            nuevo["alertados_sin_fondo"] = n
    nuevo["motivo_vacio"] = MOTIVO
    dg.clear()
    dg.update(nuevo)
    r["n_anomalous_pixels"] = 0
    r["vrp_mw"] = 0
    r["anomaly_pixels"] = []
    for k in NULAS:
        r[k] = None
    return r


def _volcado(obj, fmt: dict) -> str:
    return json.dumps(obj, **fmt)


def formato_de(texto: str, obj) -> tuple[dict, str]:
    """(formato json, salto de línea) que reproducen texto byte a byte, o Rehusado."""
    salto = "\r\n" if "\r\n" in texto else "\n"
    plano = texto.replace("\r\n", "\n")
    for fmt in FORMATOS:
        s = _volcado(obj, fmt)
        if plano == s or plano == s + "\n":
            return fmt, salto
    raise Rehusado("REHUSADO: ningún formato conocido reproduce el archivo; reescribirlo cambiaría todo el JSON")


def _leer(ruta: Path) -> str:
    """Texto tal cual está en disco: newline="" para no traducir CRLF (en Windows, autocrlf deja los JSON en CRLF)."""
    with open(ruta, encoding="utf-8", newline="") as f:
        return f.read()


def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def correr(raiz: Path, aplicar: bool) -> dict:
    inf = {"aplicado": False, "carpetas": {}, "records": [], "total": 0}
    pendientes = []
    for carpeta in CARPETAS:
        por_volcan = {}
        d = raiz / carpeta
        for ruta in sorted(d.glob("*.json")) if d.is_dir() else []:
            texto = _leer(ruta)
            obj = json.loads(texto)
            recs = obj.get("records", []) if isinstance(obj, dict) else []
            objetivos = [r for r in recs if es_objetivo(r)]
            if not objetivos:
                continue
            fmt, salto = formato_de(texto, obj)
            for r in objetivos:
                inf["records"].append({
                    "carpeta": carpeta, "volcan": ruta.stem, "sensor": r["sensor"], "datetime_utc": r["datetime_utc"],
                    "vrp_mw_antes": r.get("vrp_mw"), "n_anomalous_pixels_antes": r.get("n_anomalous_pixels"),
                    "distance_class_antes": r.get("distance_class")})
                transformar(r)
            por_volcan[ruta.stem] = len(objetivos)
            nuevo = _volcado(obj, fmt)
            if texto.replace("\r\n", "\n").endswith("\n"):
                nuevo += "\n"
            pendientes.append((ruta, nuevo.replace("\n", salto), _sha(texto)))
        inf["carpetas"][carpeta] = {"records": sum(por_volcan.values()), "por_volcan": por_volcan}
    inf["total"] = len(inf["records"])
    inf["archivos"] = [{"ruta": p.relative_to(raiz).as_posix(), "sha256_antes": s} for p, _t, s in pendientes]
    if not aplicar:
        return inf
    for ruta, nuevo, _s in pendientes:
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            f.write(nuevo)
    # Postcondición: tras escribir no queda ningún objetivo, y cada archivo escrito se relee igual.
    for ruta, nuevo, _s in pendientes:
        if _leer(ruta) != nuevo:
            raise Rehusado(f"REHUSADO: {ruta} no quedó como se escribió")
        if any(es_objetivo(r) for r in json.loads(nuevo).get("records", [])):
            raise Rehusado(f"REHUSADO: {ruta} sigue con records de fondo nulo")
    for a, (_r, nuevo, _s) in zip(inf["archivos"], pendientes):
        a["sha256_despues"] = _sha(nuevo)
    inf["aplicado"] = True
    return inf


def main(argv=None) -> int:
    # reconfigure y no un TextIOWrapper nuevo: envolver cierra el flujo original (y la captura de pytest).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", default=str(RAIZ), help="raíz del repo (por defecto, la de este script)")
    ap.add_argument("--informe", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    codigo = 0
    try:
        inf = correr(Path(a.raiz), a.aplicar)
    except Rehusado as e:
        print(e.args[0], file=sys.stderr)
        print("no se escribe nada más", file=sys.stderr)
        inf = {"rehusado": e.args[0]}
        codigo = 2
    Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
    with open(a.informe, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(inf, indent=1, ensure_ascii=False) + "\n")
    if codigo == 0:
        for c, v in inf["carpetas"].items():
            print(f"{c}: {v['records']} records {v['por_volcan']}")
        print(f"total {inf['total']}, aplicado {inf['aplicado']}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
