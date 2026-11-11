# -*- coding: utf-8 -*-
"""Reemplaza la historia publicada de los 11 Tier A con la unión de la vía, por familia de sensor (S180).

POR QUÉ. Nicolás pidió el 2026-11-11 que el tablero muestre una sola metodología en toda la serie: «publiquemos todo con
la vía nueva [...] K puede seguir corriendo pero en el dashboard debe quedar la más correcta». Las pasadas nuevas ya
salen con la vía (MODIS desde #934, VIIRS 375 desde #974, VIIRS 750 desde #983); la historia sigue con K. Este script
pasa a `data/mirova_equivalent/` la unión commiteada en `experiments/_s180_reemplazo_via/historia_via/` con las reglas
de `scripts/reemplazar_ventana_reproceso.py::reemplazar_ventana_via` (familia, corte en el encendido, la vía de
producción nunca se pisa) y aparta las pasadas K sin par a `data/_k_residuales_via/<V>.json` (opción A, decisión de
Nicolás del 2026-11-11).

TODO O NADA. Calcula las familias pedidas en los 11 volcanes antes de escribir: si un volcán pasa el tope de sin par
en una familia, no escribe nada (un tope pasado es un trozo que falta, no un descarte de borde) y sale con 2.

Por defecto es ENSAYO (no escribe nada) y deja un informe por volcán y familia. `--datos` permite correrlo sobre una
copia fuera del repo. Lo llama `aplicar_historia_via.sh` desde `.github/workflows/aplicar-reemplazo.yml`.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from scripts.reemplazar_ventana_reproceso import (_escribir_residuo, familia_sensor,  # noqa: E402
                                                 reemplazar_ventana_via)

TIER_A = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"]
PERFIL = "_s172_retro_paquete"
DESDE = "2025-02-15"
# Encendido de cada familia en producción: instante del merge del PR que prendió la vía (gh pr view N --json mergedAt).
CORTES = {
    "MODIS": "2026-11-02 17:18",      # #934, merge 2026-11-02T17:18:17Z
    "VIIRS375": "2026-11-11 13:09",   # #974, merge 2026-11-11T13:09:21Z
    "VIIRS750": "2026-11-11 13:22",   # #983, merge 2026-11-11T13:22:13Z
}
UNION = RAIZ / "experiments" / "_s180_reemplazo_via" / "historia_via"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def correr(familias: list[str], datos: Path, residuos: Path, union: Path, max_sin_par: float, aplicar: bool,
           fecha: str | None = None) -> dict:
    """Calcula todas las familias en memoria (en cadena sobre el mismo store) y escribe sólo si ninguna se rehúsa."""
    informe = {"aplicado": False, "max_sin_par": max_sin_par, "familias": {}}
    stores = {v: json.loads((datos / f"{v}.json").read_text(encoding="utf-8")) for v in TIER_A}
    sha_antes = {v: _sha(datos / f"{v}.json") for v in TIER_A}
    uniones = {v: json.loads(gzip.decompress((union / f"{v}.json.gz").read_bytes())) for v in TIER_A}
    apartados_todos = {v: [] for v in TIER_A}
    rehusado = False
    for fam in familias:
        corte = CORTES[fam]
        rehusados, vols = [], {}
        for v in TIER_A:
            store, inf, apartados = reemplazar_ventana_via(stores[v], uniones[v], DESDE, corte[:10], PERFIL, fam,
                                                           corte, apartar_sin_par=True, fecha_apartado=fecha)
            n = inf["operacional_en_ventana"]
            inf["fraccion_sin_par"] = round(inf["sin_par_apartados"] / n, 4) if n else 0.0
            # K de la familia que queda antes del corte en la serie publicada: tiene que ser 0
            inf["k_restante_antes_del_corte"] = sum(
                1 for r in store["records"] if familia_sensor(r.get("sensor")) == fam
                and r.get("via_codigo_mirova") is None and (r.get("datetime_utc") or "").replace("T", " ")[:16] < corte)
            inf.pop("solo_operacional_claves", None)
            inf["sin_par_claves"] = [[r["datetime_utc"], r["sensor"]] for r in apartados]
            if inf["fraccion_sin_par"] > max_sin_par:
                rehusados.append(v)
            stores[v] = store
            apartados_todos[v] += apartados
            vols[v] = inf
        informe["familias"][fam] = {"corte_utc": corte, "rehusados": rehusados, "volcanes": vols}
        if rehusados:
            rehusado = True
            print(f"REHUSADO {fam}: sin par sobre {max_sin_par:.0%} en {rehusados}", file=sys.stderr)
    informe["sha256_antes"] = sha_antes
    if rehusado or not aplicar:
        if rehusado:
            print("no se escribe nada", file=sys.stderr)
        return informe
    for v in TIER_A:
        if apartados_todos[v]:
            _escribir_residuo(residuos / f"{v}.json", v, apartados_todos[v])
        with open(datos / f"{v}.json", "w", encoding="utf-8") as f:
            json.dump(stores[v], f, indent=2)
    informe["sha256_despues"] = {v: _sha(datos / f"{v}.json") for v in TIER_A}
    informe["aplicado"] = True
    return informe


def main(argv=None) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--familias", default="MODIS,VIIRS375,VIIRS750")
    ap.add_argument("--datos", default=str(RAIZ / "data" / "mirova_equivalent"))
    ap.add_argument("--residuos", default=str(RAIZ / "data" / "_k_residuales_via"))
    ap.add_argument("--union", default=str(UNION))
    ap.add_argument("--max-sin-par", type=float, required=True)
    ap.add_argument("--informe", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    fams = [f.strip() for f in a.familias.split(",") if f.strip()]
    for f in fams:
        if f not in CORTES:
            ap.error(f"familia desconocida {f!r}")
    inf = correr(fams, Path(a.datos), Path(a.residuos), Path(a.union), a.max_sin_par, a.aplicar)
    Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
    Path(a.informe).write_text(json.dumps(inf, indent=1, ensure_ascii=False), encoding="utf-8")
    for fam, x in inf["familias"].items():
        for v, i in x["volcanes"].items():
            print(f"{fam:8s} {v:20s} K en ventana {i['operacional_en_ventana']:5d}  reemplazados {i['reemplazados']:5d}  "
                  f"agregados {i['agregados']:4d}  sin par {i['sin_par_apartados']:4d} ({i['fraccion_sin_par']:.2%})  "
                  f"vía conservada {i['via_operacional_conservados']:3d}  K desde el corte {i['k_desde_el_corte']}  "
                  f"K restante {i['k_restante_antes_del_corte']}")
    rehusado = any(x["rehusados"] for x in inf["familias"].values())
    return 2 if rehusado else 0


if __name__ == "__main__":
    raise SystemExit(main())
