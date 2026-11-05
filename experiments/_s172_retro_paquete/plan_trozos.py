# -*- coding: utf-8 -*-
"""Plan de trozos del workflow reproc-retro-paquete.yml (pre-registro SELLADO
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, tag s173-prereg-retro-sellado, §3.2, §10.2 y §10.3).

POR QUÉ CADA REGLA:
- Sólo perfiles que empiezan por `_s172_retro_` (§10.2): el workflow no puede pisar la serie operacional ni una sombra.
- Trozos de 20 días, y de 10 para Nevados de Chillán (§10.2): en el reproceso de K (run 39125546355, trozos de ~36
  días) los 6 fallos fueron todos de Chillán, 5 cortados por el tiempo del paso; su tasa es al menos 4,76 min por
  volcán-día contra 1,76 a 2,64 de los otros diez.
- Tupungatito sólo desde el 2026-02-23 (§3.2): la tabla de MIROVA no lo tiene antes del 02-14 y hasta el 02-23 el
  scraper lo rotulaba con 5 km; en R25 (2025) no tiene filas en el OSF: SIN DATO, no se despacha.
- Ventanas por volcán (`Volcan@inicio:fin`) para el control K del despacho D3 (DM entero, Láscar y Chillán en F26
  enteros, tres días sueltos de cada otro volcán). Un ítem sin volcán vale para todos los de la lista.
- C-via por trozo: mínimo 100 % en 2026 (F26 y DM) y 90 % en 2025 (en R25 decide la lectura, §6); en el perfil K, ninguna
  marca de la vía.
- Trozos cortos del mismo volcán y del mismo tramo (R25, F26, DM) se juntan en un job mientras sumen a lo más el
  tamaño del trozo (§10.3: los «tres días de F26» de cada volcán del despacho D3 son un job, y los tres días del humo
  D1, uno por tramo, son tres). El job corre cada tramo en secuencia.
- Ventanas que se solapan para un mismo volcán se rehúsan (el mismo día dos veces es costo y dos records por pasada);
  más de 256 jobs también (tope de una matriz de Actions).

Emite por stdout `jobs=<json>` (para $GITHUB_OUTPUT) y un resumen por stderr.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from scripts.split_date_window import split_window  # noqa: E402

PREFIJO = "_s172_retro_"
PERFIL_K = "_s172_retro_k"
CHILLAN = "NevadosDeChillan"
TUPUNGATITO = "Tupungatito"
INICIO_TUPUNGATITO = "2026-02-23"
MAX_JOBS = 256
TIER_A = ("Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "Chaiten",
          "Villarrica", "NevadosDeChillan", "Llaima", "Copahue")


class Rehusado(SystemExit):
    pass


def _ventanas(texto, volcanes):
    """'[Volcan@]AAAA-MM-DD:AAAA-MM-DD,...' -> {volcan: [(ini, fin)]}."""
    out = {v: [] for v in volcanes}
    for item in [x.strip() for x in texto.split(",") if x.strip()]:
        vol, _, rango = item.rpartition("@")
        ini, sep, fin = rango.partition(":")
        if not sep:
            raise Rehusado(f"REHUSADO: ventana sin ':' -> {item!r}")
        ini, fin = date.fromisoformat(ini.strip()).isoformat(), date.fromisoformat(fin.strip()).isoformat()
        if fin < ini:
            raise Rehusado(f"REHUSADO: ventana al revés -> {item!r}")
        destino = [vol] if vol else list(volcanes)
        for v in destino:
            if v not in out:
                raise Rehusado(f"REHUSADO: {v} no está en la lista de volcanes")
            out[v].append((ini, fin))
    return out


def tramo_de(dia):
    """R25, F26, DM u OTRO (§3.2). Los días de un job no cruzan de tramo."""
    if dia < "2026-01-01":
        return "R25"
    if "2026-02-01" <= dia <= "2026-03-31":
        return "F26"
    if "2026-10-01" <= dia <= "2026-10-16":
        return "DM"
    return "OTRO"


def _dias(t):
    return (date.fromisoformat(t["end"]) - date.fromisoformat(t["start"])).days + 1


def planificar(perfil, volcanes_txt, ventanas_txt, max_dias=20, max_dias_chillan=10, perfiles_dir=None):
    perfil = perfil.strip()
    if not perfil.startswith(PREFIJO):
        raise Rehusado(f"REHUSADO: el perfil {perfil!r} no empieza por {PREFIJO!r}")
    pd = Path(perfiles_dir) if perfiles_dir else RAIZ / "pipeline" / "profiles"
    import yaml
    ruta = pd / f"{perfil}.yaml"
    if not ruta.exists():
        raise Rehusado(f"REHUSADO: no existe {ruta}")
    sub = ((yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}).get("output") or {}).get("data_subdir")
    if sub != perfil:
        raise Rehusado(f"REHUSADO: {perfil} escribe en {sub!r}, no en su carpeta propia")
    volcanes = [v.strip() for v in volcanes_txt.split(",") if v.strip()]
    if not volcanes or len(set(volcanes)) != len(volcanes):
        raise Rehusado("REHUSADO: lista de volcanes vacía o repetida")
    for v in volcanes:
        if v not in TIER_A:
            raise Rehusado(f"REHUSADO: {v} no es de los 11 Tier A (la retrospectiva es de los 11)")
    por_vol = _ventanas(ventanas_txt, volcanes)
    jobs, saltados = [], []
    for v in volcanes:
        rangos = sorted(por_vol[v])
        for (a0, a1), (b0, b1) in zip(rangos, rangos[1:]):
            if b0 <= a1:
                raise Rehusado(f"REHUSADO: ventanas solapadas en {v}: {a0}:{a1} y {b0}:{b1}")
        tam = max_dias_chillan if v == CHILLAN else max_dias
        piezas = []
        for ini, fin in rangos:
            if v == TUPUNGATITO and ini < INICIO_TUPUNGATITO:
                if fin < INICIO_TUPUNGATITO:
                    saltados.append(f"{v} {ini}:{fin} (antes del {INICIO_TUPUNGATITO}: SIN DATO, §3.2)")
                    continue
                saltados.append(f"{v} {ini}:{INICIO_TUPUNGATITO} recortado (§3.2)")
                ini = INICIO_TUPUNGATITO
            for t in split_window(ini, fin, tam):
                if tramo_de(t["start"]) != tramo_de(t["end"]):
                    raise Rehusado(f"REHUSADO: el trozo {v} {t['start']}:{t['end']} cruza de tramo")
                piezas.append(t)
        grupos = []
        for t in piezas:
            g = grupos[-1] if grupos else None
            if (g and tramo_de(g[-1]["start"]) == tramo_de(t["start"])
                    and sum(_dias(x) for x in g) + _dias(t) <= tam):
                g.append(t)
            else:
                grupos.append([t])
        for n, g in enumerate(grupos, 1):
            jobs.append({"vol": v, "idx": n, "start": g[0]["start"], "end": g[-1]["end"],
                         "tramos": " ".join(f"{x['start']}:{x['end']}" for x in g),
                         "tramo": tramo_de(g[0]["start"]), "dias": sum(_dias(x) for x in g),
                         "minimo": "0.90" if tramo_de(g[0]["start"]) == "R25" else "1.0",
                         "esperado": "k" if perfil == PERFIL_K else "via"})
    if not jobs:
        raise Rehusado("REHUSADO: el plan no tiene ningún trozo")
    if len(jobs) > MAX_JOBS:
        raise Rehusado(f"REHUSADO: {len(jobs)} trozos, más que el tope de {MAX_JOBS} de una matriz")
    return jobs, saltados


def main():
    jobs, saltados = planificar(os.environ["PERFIL"], os.environ["VOLCANES"], os.environ["VENTANAS"],
                                int(os.environ.get("MAX_DIAS") or 20), int(os.environ.get("MAX_DIAS_CHILLAN") or 10))
    print(f"jobs={json.dumps(jobs)}")
    for s in saltados:
        print("AVISO:", s, file=sys.stderr)
    print(f"{len(jobs)} trozos", file=sys.stderr)


if __name__ == "__main__":
    main()
