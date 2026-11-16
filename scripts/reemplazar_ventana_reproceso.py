# -*- coding: utf-8 -*-
"""Reemplaza una ventana de fechas de la serie operacional con los records de un reproceso aislado.

POR QUE (S154): al adoptar K (#850) la historia de `data/mirova_equivalent/` quedo escrita con el detector
anterior. Reprocesarla directo contra la replica (`backfill-tier-a.yml`) toma el grupo `push-main` horas por ola y
deja al NRT esperando. En cambio se reprocesa por trozos en un perfil aislado identico a la replica
(`_s154_reproc_k_historico`, vigilado por tests/test_reproceso_historico_k_s154.py) y este script pasa el
resultado a la serie operacional en un solo commit.

REGLAS, y por que cada una:
- Por clave (datetime_utc, sensor), la misma de `pipeline/store.py`, y solo dentro de [desde, hasta] por la fecha
  de la pasada. Fuera de la ventana no se toca nada: es la parte que el NRT sigue escribiendo.
- Una pasada que esta en la operacional y NO vino en el reproceso se CONSERVA y se informa. El pipeline escribe
  un record por pasada aunque no detecte nada, asi que una pasada ausente es un corte de NASA (A64, A108), no
  «K no la ve»; borrarla perderia un dato. Si son demasiadas (--max-solo-operacional, fraccion por volcan), el
  trozo no se cubrio y el script se niega a escribir: hay que repetir ese trozo.
- `first_processed_utc` se hereda del record operacional como en `store.append_record` (S150): describe cuando
  la pasada se vio por primera vez, no esta version.
- Todo record del reproceso dentro de la ventana debe traer `regimen.perfil` igual al perfil esperado. Asi no se
  puede pasar por K un archivo de otro A/B.
- La marca `regimen` del record queda como la escribio el reproceso (perfil aislado + sha del codigo): dice la
  verdad sobre de donde viene, y el test garantiza que ese perfil resuelve igual que la replica.

S180 (reemplazo de la historia con la vía «código MIROVA»): con --familia y --corte-utc corre
`reemplazar_ventana_via`, que toca sólo esa familia de sensor, nunca pisa un record que la producción escribió con la
vía y no agrega nada del reproceso desde el encendido; con --apartar-sin-par mueve las pasadas K sin par (descarte de
borde de la vía) a un archivo de residuos en vez de conservarlas. Pruebas: tests/test_reemplazo_via_s180.py.

Por defecto es un ENSAYO: informa y no escribe. Con --aplicar escribe el archivo operacional.

Uso:
    python scripts/reemplazar_ventana_reproceso.py --operacional data/mirova_equivalent/Villarrica.json \
        --reproceso data/_s154_reproc_k_historico/Villarrica.json --desde 2025-02-15 --hasta 2026-09-17 \
        --perfil-esperado _s154_reproc_k_historico --informe informe.json [--aplicar]
"""
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _key(r: dict) -> tuple:
    return (r.get("datetime_utc"), r.get("sensor"))


def _en_ventana(r: dict, desde: str, hasta: str) -> bool:
    return desde <= (r.get("datetime_utc") or "")[:10] <= hasta


def reemplazar_ventana(operacional: dict, reproceso: dict, desde: str, hasta: str,
                       perfil_esperado: str) -> tuple[dict, dict]:
    """Devuelve (store nuevo, informe). No modifica las entradas."""
    if operacional.get("volcano") != reproceso.get("volcano"):
        raise ValueError(f"volcanes distintos: {operacional.get('volcano')!r} contra {reproceso.get('volcano')!r}")

    nuevos = {}
    fuera = 0
    for r in reproceso.get("records", []):
        if not _en_ventana(r, desde, hasta):
            fuera += 1
            continue
        perfil = (r.get("regimen") or {}).get("perfil")
        if perfil != perfil_esperado:
            raise ValueError(f"record {_key(r)} del reproceso viene del perfil {perfil!r}, no de {perfil_esperado!r}")
        nuevos[_key(r)] = copy.deepcopy(r)

    salida, reemplazados, solo_op, op_en_ventana = [], 0, [], 0
    for r in operacional.get("records", []):
        if not _en_ventana(r, desde, hasta):
            salida.append(copy.deepcopy(r))
            continue
        op_en_ventana += 1
        k = _key(r)
        if k in nuevos:
            n = nuevos.pop(k)
            if r.get("first_processed_utc"):
                n["first_processed_utc"] = r["first_processed_utc"]
            else:
                n.pop("first_processed_utc", None)
            salida.append(n)
            reemplazados += 1
        else:
            salida.append(copy.deepcopy(r))
            solo_op.append(list(k))
    agregados = len(nuevos)
    salida.extend(nuevos.values())
    salida.sort(key=lambda r: r.get("datetime_utc", ""))

    store = {k: v for k, v in operacional.items() if k != "records"}
    store["records"] = salida
    informe = {
        "volcano": operacional.get("volcano"), "desde": desde, "hasta": hasta,
        "operacional_en_ventana": op_en_ventana, "reemplazados": reemplazados, "agregados": agregados,
        "solo_operacional": len(solo_op), "solo_operacional_claves": solo_op,
        "reproceso_fuera_de_ventana": fuera,
        "records_antes": len(operacional.get("records", [])), "records_despues": len(salida),
    }
    return store, informe


FAMILIAS = ("MODIS", "VIIRS375", "VIIRS750")
MOTIVO_SIN_PAR = "borde_via"
MOTIVO_RESIDUO = (
    "Pasadas que el detector K escribia y la via «codigo MIROVA» descarta: el granulo roza el volcan por el borde de "
    "la franja (la via exige ver el volcan como lo ve MIROVA: al menos 100 pixeles a 45 km y, en MODIS y VIIRS 375, un "
    "pixel a menos de 5 km del centro, pipeline/mirova_v750_codigo.py). La produccion con la via no las escribe. "
    "Apartadas de la serie publicada al reemplazar la historia con la via (S180) por decision de Nicolas del "
    "2026-11-11 (opcion A del plan docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md); se conservan aca sin cambios salvo la "
    "clave _apartado.")


def familia_sensor(sensor) -> str | None:
    """Convención A48 (la de frontend/cambio_detector.js::familiaSensor): VIIRS_*_750 es M-band, los demás VIIRS I-band."""
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if not s.startswith("VIIRS"):
        return None
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def _minuto(dt) -> str:
    """'2026-11-11T13:09:21Z' y '2026-11-11 13:09' -> '2026-11-11 13:09' (los records usan el espacio)."""
    return str(dt or "").strip().replace("T", " ")[:16]


def reemplazar_ventana_via(operacional: dict, reproceso: dict, desde: str, hasta: str, perfil_esperado: str,
                           familia: str, corte_utc: str, apartar_sin_par: bool = False,
                           fecha_apartado: str | None = None) -> tuple[dict, dict, list]:
    """Reemplazo de la historia con la vía (S180), una familia de sensor por vez. Devuelve (store, informe, apartados).

    POR QUE cada regla (tests/test_reemplazo_via_s180.py):
    - Solo la familia pedida: cada una cambió de método en su fecha (#934, #974, #983).
    - Un record operacional con cualquier marca de vía (`true` o texto de caída a K) lo escribió la producción con la
      vía encendida: es la fuente y no se pisa, ni antes ni después del corte.
    - Nada del reproceso desde `corte_utc` (el encendido de la familia) se agrega: desde ahí manda el NRT. El K
      operacional desde el corte tampoco se toca; se cuenta, porque no debería existir.
    - La pasada K sin par (la vía descarta el gránulo de borde) se aparta si `apartar_sin_par`; si no, se conserva.
    """
    if familia not in FAMILIAS:
        raise ValueError(f"familia {familia!r} desconocida; una de {FAMILIAS}")
    if operacional.get("volcano") != reproceso.get("volcano"):
        raise ValueError(f"volcanes distintos: {operacional.get('volcano')!r} contra {reproceso.get('volcano')!r}")
    corte = _minuto(corte_utc)
    if len(corte) != 16:
        raise ValueError(f"corte_utc ilegible: {corte_utc!r}")

    def antes_del_corte(r):
        return _minuto(r.get("datetime_utc")) < corte

    nuevos, fuera, otra, tras = {}, 0, 0, 0
    for r in reproceso.get("records", []):
        if familia_sensor(r.get("sensor")) != familia:
            otra += 1
            continue
        if not _en_ventana(r, desde, hasta):
            fuera += 1
            continue
        if not antes_del_corte(r):
            tras += 1
            continue
        perfil = (r.get("regimen") or {}).get("perfil")
        if perfil != perfil_esperado:
            raise ValueError(f"record {_key(r)} del reproceso viene del perfil {perfil!r}, no de {perfil_esperado!r}")
        nuevos[_key(r)] = copy.deepcopy(r)

    salida, apartados, solo_op = [], [], []
    reemplazados = k_en_ventana = via_conservados = k_desde_corte = 0
    for r in operacional.get("records", []):
        if familia_sensor(r.get("sensor")) != familia or not _en_ventana(r, desde, hasta):
            salida.append(copy.deepcopy(r))
            continue
        k = _key(r)
        if r.get("via_codigo_mirova") not in (None, False):
            if nuevos.pop(k, None) is not None:
                via_conservados += 1
            salida.append(copy.deepcopy(r))
            continue
        if not antes_del_corte(r):
            k_desde_corte += 1
            salida.append(copy.deepcopy(r))
            continue
        k_en_ventana += 1
        if k in nuevos:
            n = nuevos.pop(k)
            if r.get("first_processed_utc"):
                n["first_processed_utc"] = r["first_processed_utc"]
            else:
                n.pop("first_processed_utc", None)
            salida.append(n)
            reemplazados += 1
        else:
            solo_op.append(list(k))
            if apartar_sin_par:
                a = copy.deepcopy(r)
                a["_apartado"] = {"motivo": MOTIVO_SIN_PAR, "familia": familia, "corte_utc": corte,
                                  "fecha": fecha_apartado or datetime.now(timezone.utc).strftime("%Y-%m-%d")}
                apartados.append(a)
            else:
                salida.append(copy.deepcopy(r))
    agregados = len(nuevos)
    salida.extend(nuevos.values())
    salida.sort(key=lambda r: r.get("datetime_utc", ""))

    store = {k: v for k, v in operacional.items() if k != "records"}
    store["records"] = salida
    informe = {
        "volcano": operacional.get("volcano"), "familia": familia, "desde": desde, "hasta": hasta, "corte_utc": corte,
        "operacional_en_ventana": k_en_ventana, "reemplazados": reemplazados, "agregados": agregados,
        "solo_operacional": len(solo_op), "solo_operacional_claves": solo_op,
        "sin_par_apartados": len(apartados), "via_operacional_conservados": via_conservados,
        "k_desde_el_corte": k_desde_corte, "reproceso_tras_corte": tras, "reproceso_otra_familia": otra,
        "reproceso_fuera_de_ventana": fuera,
        "records_antes": len(operacional.get("records", [])), "records_despues": len(salida),
    }
    return store, informe, apartados


def _escribir_residuo(path: Path, volcano: str, apartados: list) -> int:
    """Une por clave con el residuo previo (no duplica: gana el que ya estaba). Devuelve cuántos quedaron nuevos."""
    if path.exists():
        d = json.loads(path.read_text(encoding="utf-8"))
        if d.get("volcano") != volcano:
            raise ValueError(f"el residuo {path} es de {d.get('volcano')!r}, no de {volcano!r}")
    else:
        d = {"volcano": volcano, "motivo": MOTIVO_RESIDUO, "records": []}
    ya = {_key(r) for r in d["records"]}
    nuevos = [r for r in apartados if _key(r) not in ya]
    d["records"] = sorted(d["records"] + nuevos, key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    return len(nuevos)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--operacional", required=True)
    ap.add_argument("--reproceso", required=True)
    ap.add_argument("--desde", required=True, help="YYYY-MM-DD, inclusive")
    ap.add_argument("--hasta", required=True, help="YYYY-MM-DD, inclusive")
    ap.add_argument("--perfil-esperado", required=True)
    ap.add_argument("--informe", required=True, help="JSON con el conteo")
    ap.add_argument("--max-solo-operacional", type=float, default=0.02,
                    help="fraccion maxima de pasadas operacionales de la ventana ausentes del reproceso")
    ap.add_argument("--aplicar", action="store_true", help="escribir el archivo operacional (si no, ensayo)")
    ap.add_argument("--familia", choices=FAMILIAS,
                    help="S180: sólo esta familia de sensor; exige --corte-utc (reemplazo con la vía)")
    ap.add_argument("--corte-utc", help="S180: encendido de la familia; la vía de producción no se pisa y nada del "
                                        "reproceso desde aquí se agrega")
    ap.add_argument("--apartar-sin-par", metavar="RESIDUO_JSON",
                    help="S180: mueve las pasadas K sin par a este archivo (une por clave) en vez de conservarlas")
    a = ap.parse_args(argv)
    if bool(a.familia) != bool(a.corte_utc) or (a.apartar_sin_par and not a.familia):
        ap.error("--familia y --corte-utc van juntos, y --apartar-sin-par sólo con ellos")

    op_path = Path(a.operacional)
    with open(op_path, encoding="utf-8") as f:
        op = json.load(f)
    with open(a.reproceso, encoding="utf-8") as f:
        re_ = json.load(f)
    apartados = []
    if a.familia:
        store, inf, apartados = reemplazar_ventana_via(op, re_, a.desde, a.hasta, a.perfil_esperado, a.familia,
                                                       a.corte_utc, apartar_sin_par=bool(a.apartar_sin_par))
    else:
        store, inf = reemplazar_ventana(op, re_, a.desde, a.hasta, a.perfil_esperado)

    frac = inf["solo_operacional"] / inf["operacional_en_ventana"] if inf["operacional_en_ventana"] else 0.0
    inf["fraccion_solo_operacional"] = round(frac, 4)
    inf["max_solo_operacional"] = a.max_solo_operacional
    rehusado = frac > a.max_solo_operacional
    inf["aplicado"] = bool(a.aplicar and not rehusado)
    print(f"{inf['volcano']}: {inf['operacional_en_ventana']} en ventana, {inf['reemplazados']} reemplazados, "
          f"{inf['agregados']} agregados, {inf['solo_operacional']} solo operacional ({frac:.2%}), "
          f"{inf['records_antes']} -> {inf['records_despues']} records")
    if rehusado:
        print(f"REHUSADO: {frac:.2%} de las pasadas de la ventana no vinieron en el reproceso "
              f"(tope {a.max_solo_operacional:.2%}); repetir los trozos faltantes", file=sys.stderr)
    if inf["aplicado"]:
        store["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if a.apartar_sin_par:
            inf["residuo_nuevos"] = _escribir_residuo(Path(a.apartar_sin_par), inf["volcano"], apartados)
        with open(op_path, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    Path(a.informe).write_text(json.dumps(inf, indent=2, ensure_ascii=False), encoding="utf-8")
    return 2 if rehusado else 0


if __name__ == "__main__":
    raise SystemExit(main())
