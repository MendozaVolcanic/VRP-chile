# -*- coding: utf-8 -*-
"""Reemplaza la serie VIIRS 750 de Puyehue-Cordón Caulle con el reproceso de la caja del cráter (S184, PR #999).

POR QUÉ. En VIIRS 750 la vía «código MIROVA» busca píxeles calientes con un umbral sensible sólo dentro de una región por
volcán. En Cordón Caulle esa región era el cuadrado `sens` (21 × 21 celdas centrado en el punto de referencia, que cae en
el Puyehue) y el PR #999 la cambia por `crater` (7 × 7 celdas en el cráter). Desde el merge, el NRT escribe con `crater`;
la serie anterior quedó con `sens`. Una serie con dos cajas muestra un cambio que no es del volcán (el 2026-10-21 05:48
`sens` publicó 10,1 MW del flanco del Puyehue y `crater` 0,35 MW). Este script pasa a `data/mirova_equivalent/` el
reproceso con `crater` (run 43467764489, despachado desde la rama de #999, commit `4b306b31e`), unido en
`historia_crater/PuyehueCordonCaulle.json.gz`.

POR QUÉ NO SIRVE `aplicar_via.py` (S180). Aquella regla no pisa nunca un record con marca de vía, porque reemplazaba K por
la vía. Aquí la serie publicada YA es de la vía (reemplazo S180 y NRT desde #983); lo que cambia es la caja. Por eso:

REGLAS, y por qué:
- Sólo VIIRS 750 de Cordón Caulle: el cambio de #999 no toca otro volcán ni otro sensor (ficha v1.27).
- Ventana [DESDE, HASTA] con HASTA = último día del reproceso. Lo posterior lo escribe el NRT (con `crater` sólo desde el
  merge de #999; los días entre HASTA y el merge siguen con `sens` y se informan como `tras_ventana`).
- Cada record publicado en la ventana con par en el reproceso (misma pasada: `datetime_utc` y `sensor`) se reemplaza;
  conserva su `first_processed_utc` (cuándo se publicó por primera vez).
- Sin par: el reproceso no tiene esa pasada. Con el mismo código de la vía esto sólo pasa si una descarga falló en el
  reproceso, no porque la vía la descarte. Se CONSERVA (quitarla borra una observación real; dejarla sólo deja la caja
  vieja en esa pasada) y se lista. Si pasan del tope, se rehúsa: un tope pasado es un trozo con descargas fallidas
  (FileExistsError de S182), no un borde.
- Pasadas sólo del reproceso: se agregan (la vía las ve con la caja nueva y el NRT no las tenía).
- Todo record del reproceso tiene que venir del perfil `_s172_retro_paquete`, con `via_codigo_mirova` verdadero y con
  `regimen.codigo_sha` = `CODIGO_SHA` (el commit de la rama de #999 que tiene `crater`; lo vigila la prueba).
- La unión no puede tener huecos de calendario en la ventana (un trozo que falta deja pasadas sin reemplazar).
- TODO O NADA: si algo se rehúsa, no escribe y sale con 2. Por defecto es ENSAYO; `--aplicar` escribe.

Uso:
    python experiments/_s184_pcc_crater_aplicar/aplicar_pcc_v750.py --max-sin-par 0.02 --informe <json> [--aplicar]
Lo llama `aplicar_pcc_v750.sh` desde `.github/workflows/aplicar-reemplazo.yml` (con el sí de Nicolás, A45).
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
VOLCAN = "PuyehueCordonCaulle"
PERFIL = "_s172_retro_paquete"
CODIGO_SHA = "4b306b31ef9ca3fbec9b4a4cf97348187a75288f"
DESDE = "2025-02-15"
UNION = AQUI / "historia_crater" / f"{VOLCAN}.json.gz"
INFORME_UNION = AQUI / "historia_crater" / "informe_union.json"


class Rehusado(Exception):
    pass


def es_v750(sensor) -> bool:
    """Convención A48: VIIRS_*_750 es la banda M (750 m); los demás VIIRS son 375 m."""
    s = str(sensor or "")
    return s.startswith("VIIRS") and s.endswith("_750")


def _clave(r: dict) -> tuple:
    return (r.get("datetime_utc"), r.get("sensor"))


def _dia(r: dict) -> str:
    return (r.get("datetime_utc") or "")[:10]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validar_union(union: dict, informe_union: dict, desde: str, hasta: str) -> None:
    if union.get("volcano") != VOLCAN:
        raise Rehusado(f"REHUSADO: la unión es de {union.get('volcano')!r}")
    for r in union.get("records", []):
        reg = r.get("regimen") or {}
        if reg.get("perfil") != PERFIL:
            raise Rehusado(f"REHUSADO: {_clave(r)} viene del perfil {reg.get('perfil')!r}")
        if reg.get("codigo_sha") != CODIGO_SHA:
            raise Rehusado(f"REHUSADO: {_clave(r)} viene del código {reg.get('codigo_sha')!r}, no de {CODIGO_SHA}")
        if r.get("via_codigo_mirova") is not True:
            raise Rehusado(f"REHUSADO: {_clave(r)} no es de la vía ({r.get('via_codigo_mirova')!r})")
    iv = (informe_union.get("volcanes") or {}).get(VOLCAN) or {}
    if iv.get("huecos"):
        raise Rehusado(f"REHUSADO: la unión tiene huecos de calendario: {iv['huecos'][:10]}")
    if not iv.get("desde") or iv["desde"] > desde or not iv.get("hasta") or iv["hasta"] < hasta:
        raise Rehusado(f"REHUSADO: la unión cubre {iv.get('desde')}..{iv.get('hasta')}, no {desde}..{hasta}")


def reemplazar(operacional: dict, union: dict, desde: str, hasta: str) -> tuple[dict, dict]:
    """Devuelve (store nuevo, informe). No modifica las entradas."""
    if operacional.get("volcano") != VOLCAN:
        raise Rehusado(f"REHUSADO: el store es de {operacional.get('volcano')!r}")
    nuevos = {}
    for r in union.get("records", []):
        if es_v750(r.get("sensor")) and desde <= _dia(r) <= hasta:
            k = _clave(r)
            if k in nuevos:
                raise Rehusado(f"REHUSADO: pasada repetida en la unión: {k}")
            nuevos[k] = r
    salida, sin_par = [], []
    reemplazados = tras = 0
    vistos = set()
    for r in operacional.get("records", []):
        if not es_v750(r.get("sensor")):
            salida.append(copy.deepcopy(r))
            continue
        k = _clave(r)
        if k in vistos:
            raise Rehusado(f"REHUSADO: pasada repetida en la serie publicada: {k}")
        vistos.add(k)
        if _dia(r) < desde:
            salida.append(copy.deepcopy(r))
            continue
        if _dia(r) > hasta:
            tras += 1
            salida.append(copy.deepcopy(r))
            continue
        if k in nuevos:
            n = copy.deepcopy(nuevos.pop(k))
            if r.get("first_processed_utc"):
                n["first_processed_utc"] = r["first_processed_utc"]
            else:
                n.pop("first_processed_utc", None)
            salida.append(n)
            reemplazados += 1
        else:
            sin_par.append(copy.deepcopy(r))
            salida.append(copy.deepcopy(r))
    agregados = [copy.deepcopy(r) for r in nuevos.values()]
    salida.extend(agregados)
    salida.sort(key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
    store = {k: v for k, v in operacional.items() if k != "records"}
    store["records"] = salida
    en_ventana = reemplazados + len(sin_par)
    informe = {
        "volcano": VOLCAN, "familia": "VIIRS750", "desde": desde, "hasta": hasta,
        "publicados_en_ventana": en_ventana, "reemplazados": reemplazados, "agregados": len(agregados),
        "sin_par_conservados": len(sin_par),
        "fraccion_sin_par": round(len(sin_par) / en_ventana, 4) if en_ventana else 0.0,
        "sin_par_claves": [list(_clave(r)) for r in sin_par],
        "agregados_claves": [list(_clave(r)) for r in agregados],
        "tras_ventana_sin_tocar": tras,
        "records_antes": len(operacional.get("records", [])), "records_despues": len(salida),
        "otros_sensores_intactos": sum(1 for r in salida if not es_v750(r.get("sensor"))),
    }
    return store, informe


def correr(datos: Path, union_p: Path, informe_union_p: Path, hasta: str | None, max_sin_par: float,
           aplicar: bool) -> dict:
    union = json.loads(gzip.decompress(union_p.read_bytes()))
    inf_u = json.loads(informe_union_p.read_text(encoding="utf-8"))
    hasta = hasta or (inf_u.get("volcanes") or {}).get(VOLCAN, {}).get("hasta")
    if not hasta:
        raise Rehusado("REHUSADO: no se sabe hasta qué día cubre la unión")
    date.fromisoformat(hasta)
    validar_union(union, inf_u, DESDE, hasta)
    ruta = datos / f"{VOLCAN}.json"
    sha_antes = _sha(ruta)
    operacional = json.loads(ruta.read_text(encoding="utf-8"))
    store, inf = reemplazar(operacional, union, DESDE, hasta)
    inf.update({"aplicado": False, "max_sin_par": max_sin_par, "sha256_antes": sha_antes,
                "union_sha256": _sha(union_p), "codigo_sha_reproceso": CODIGO_SHA})
    if inf["fraccion_sin_par"] > max_sin_par:
        raise Rehusado(f"REHUSADO: sin par {inf['fraccion_sin_par']:.2%} sobre el tope {max_sin_par:.2%}", inf)
    if not aplicar:
        return inf
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    inf["sha256_despues"] = _sha(ruta)
    inf["aplicado"] = True
    return inf


def main(argv=None) -> int:
    # reconfigure y no un TextIOWrapper nuevo: envolver cierra el flujo original (y la captura de pytest).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", default=str(RAIZ / "data" / "mirova_equivalent"))
    ap.add_argument("--union", default=str(UNION))
    ap.add_argument("--informe-union", default=str(INFORME_UNION))
    ap.add_argument("--hasta", default=None, help="último día de la ventana (por defecto, el de la unión)")
    ap.add_argument("--max-sin-par", type=float, required=True)
    ap.add_argument("--informe", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    codigo = 0
    try:
        inf = correr(Path(a.datos), Path(a.union), Path(a.informe_union), a.hasta, a.max_sin_par, a.aplicar)
    except Rehusado as e:
        print(e.args[0], file=sys.stderr)
        print("no se escribe nada", file=sys.stderr)
        inf = e.args[1] if len(e.args) > 1 else {"rehusado": e.args[0]}
        inf["rehusado"] = e.args[0]
        codigo = 2
    Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
    Path(a.informe).write_text(json.dumps(inf, indent=1, ensure_ascii=False), encoding="utf-8")
    if codigo == 0:
        print(f"VIIRS750 {VOLCAN} {inf['desde']}..{inf['hasta']}: publicados {inf['publicados_en_ventana']}, "
              f"reemplazados {inf['reemplazados']}, agregados {inf['agregados']}, sin par {inf['sin_par_conservados']} "
              f"({inf['fraccion_sin_par']:.2%}), tras la ventana {inf['tras_ventana_sin_tocar']}, "
              f"aplicado {inf['aplicado']}")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
