#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ════════════════════════════════════════════════════════════════════
# FICHA SDA · vigilar_plataformas.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Avisar cuando un satelite deja de entregar datos al sistema. NO participa de la
#                 deteccion ni de la clasificacion: es instrumentacion operacional sobre los records ya
#                 publicados, para que el operador sepa cuantas miradas por noche tiene cada volcan.
# Lógica        : Cuenta, sobre los 11 Tier A, los records de cada plataforma y sensor en las ultimas
#                 72 h. Plataforma con cese anunciado que calla despues de su fecha: aviso informativo,
#                 una vez. Cualquier otra que calle mientras las demas producen: alarma. Todas calladas:
#                 caida general (la cubre el paso de frescura del mismo healthcheck).
# Modelo/método : Reglas deterministicas de conteo. Sin aprendizaje automatico.
# Datos entrada : data/mirova_equivalent/<Tier A>.json (campos `sensor` y `datetime_utc`) y
#                 scripts/ceses_esperados.json. SIN datos personales.
# Variables     : Ventana de 72 h (medida, ver VENTANA_H), lista de ceses esperados.
# Limitaciones  : Ve la AUSENCIA de records, no su causa (satelite caido, coleccion renombrada, cambio de
#                 version en CMR). Una plataforma que siga entregando pero con menos pasadas no alarma.
# Refs/datos    : Aviso de NASA del cese de Suomi NPP (URL en ceses_esperados.json); informe del frente
#                 S159 «cese de Suomi NPP». Ficha: docs/FICHA_SDA_VRP_CHILE.md (v1.10).
# ════════════════════════════════════════════════════════════════════
"""Vigilancia por plataforma: avisa cuando un satélite deja de entregar datos (S159).

POR QUÉ (fenómeno → mecanismo). Suomi NPP deja de entregar el 2026-11-02 a las 13:00 UTC. Cuando un satélite
calla, CMR devuelve cero gránulos y `pipeline/fetch.py` lo vive exactamente como una noche en que el satélite no
pasó: no registra falla, el job dice «Cobertura: completa» y sale 0. El tablero pierde esa plataforma sin aviso.
Y las vigilancias que había miraban por volcán (edad del último record) o por bucket de sensor (MODIS, VIIRS 375,
VIIRS 750): mientras NOAA-20 o NOAA-21 entreguen una pasada, el bucket VIIRS sigue «vivo». Con eso, la muerte
silenciosa de NOAA-20 o NOAA-21 pasaría igual de inadvertida que el cese anunciado de Suomi NPP.

Qué hace: cuenta por sensor (que distingue plataforma y resolución: VIIRS_SNPP es Suomi NPP a 375 m,
VIIRS_SNPP_750 la misma plataforma a 750 m, MODIS_TERRA y MODIS_AQUA) los records de los 11 Tier A en las
últimas VENTANA_H horas, y da uno de tres estados:
- `ok`: todas las plataformas esperadas producen (las que tienen un cese ya cumplido se informan aparte);
- `alarma`: una plataforma sin cese anunciado (o con cese todavía no cumplido) calla mientras otras producen;
- `caida_general`: no hay ningún record en la ventana. No se culpa a ninguna plataforma; eso ya lo ve, antes,
  el paso de frescura del mismo healthcheck (48 h).

Medición de la ventana (A115, no un número de gusto): `python scripts/vigilar_plataformas.py --medir`, salida en
experiments/_s159/vigilar_plataformas/medicion.txt.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data" / "mirova_equivalent"
CESES_JSON = Path(__file__).resolve().parent / "ceses_esperados.json"

TIER_A = (
    "Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
    "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue",
)

# El valor del campo `sensor` que escriben los procesadores (A48: verificado en los JSON de los Tier A; el
# sufijo _750 es la banda M de 750 m, sin sufijo es la banda I de 375 m).
PLATAFORMA = {
    "VIIRS_SNPP": "Suomi NPP", "VIIRS_SNPP_750": "Suomi NPP",
    "VIIRS_NOAA20": "NOAA-20", "VIIRS_NOAA20_750": "NOAA-20",
    "VIIRS_NOAA21": "NOAA-21", "VIIRS_NOAA21_750": "NOAA-21",
    "MODIS_TERRA": "Terra", "MODIS_AQUA": "Aqua",
}
SENSORES = tuple(PLATAFORMA)

# POR QUÉ 72 h (medido, experiments/_s159/vigilar_plataformas/medicion.txt): del 2026-01-29 (fin del hueco del
# backfill) al 2026-10-21, el hueco más largo entre dos records consecutivos de NOAA-20, NOAA-21, Terra o Aqua sobre
# los 11 Tier A fue de 47,7 h (Terra, un día sin pasada), y la regla repetida a las 12:00 UTC de cada uno de esos 266
# días no alarma ni una vez por esas cuatro plataformas. Con 48 h tampoco alarma a las 12:00, pero el margen sobre ese
# hueco de 47,7 h es de 0,3 h: bastaría que la pasada siguiente llegara con media hora más de latencia (el NRT entrega
# con 3 a 7 h, S133) o que alguien despachara el job a otra hora. 72 h deja una noche entera de margen. Suomi NPP tuvo
# huecos reales de 71 a 166 h, propios del satélite más viejo de los tres: con 72 h alarman 8 de los 266 días, en
# cuatro episodios (marzo, abril, julio y agosto; el de agosto incluye las pasadas del 3 al 6 que la serie K apartó a
# data/_c0_residuales/), que es lo que se quiere de un satélite mientras no se cumpla su cese anunciado. Con 96 h el
# primer aviso de esos episodios llega un día más tarde y dos de ellos no avisan.
VENTANA_H = 72

LABEL_CESE = "plataforma-cese"
LABEL_ALARMA = "plataforma-sin-datos"
TITULO_ALARMA = "ALARMA: una plataforma satelital dejó de producir records (vigilancia por plataforma)"
MARCA = "<!-- s159-plataformas:"


def titulo_cese(plataforma: str) -> str:
    return f"Cese esperado confirmado: {plataforma} dejó de producir records (informativo)"


def _utc(texto: str) -> datetime:
    t = datetime.fromisoformat(str(texto).strip().replace("Z", "+00:00").replace(" ", "T"))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def cargar_ceses(ruta: Path | None = None) -> list[dict]:
    datos = json.loads(Path(ruta or CESES_JSON).read_text(encoding="utf-8"))
    return [{**c, "sensores": list(c["sensores"]), "desde": _utc(c["desde_utc"])} for c in datos.get("ceses", [])]


def cargar_registros(directorio: Path = DATOS, volcanes=TIER_A) -> list[tuple[str, datetime]]:
    """(sensor, datetime UTC) de cada record de los Tier A. Un JSON ausente o ilegible se salta (lo ve el
    paso de frescura del healthcheck); si no hay ninguno, la lista vacía da `caida_general`."""
    regs = []
    for v in volcanes:
        p = Path(directorio) / f"{v}.json"
        if not p.exists():
            continue
        try:
            records = json.loads(p.read_text(encoding="utf-8")).get("records", [])
        except (OSError, ValueError):
            continue
        for r in records:
            s, t = r.get("sensor"), r.get("datetime_utc") or r.get("acq_datetime_utc")
            if s and t:
                try:
                    regs.append((s, _utc(t)))
                except ValueError:
                    continue
    return regs


def evaluar(registros, ahora: datetime, ceses: list[dict], ventana_h: int = VENTANA_H) -> dict:
    """Veredicto de la ventana (ahora - ventana_h, ahora]. Los records posteriores a `ahora` no cuentan."""
    desde = ahora - timedelta(hours=ventana_h)
    conteo: Counter = Counter()
    ultimo: dict[str, datetime] = {}
    desconocidos: Counter = Counter()
    for s, t in registros:
        if t > ahora:
            continue
        if s not in PLATAFORMA:
            if t > desde:
                desconocidos[s] += 1
            continue
        if s not in ultimo or t > ultimo[s]:
            ultimo[s] = t
        if t > desde:
            conteo[s] += 1

    base = {
        "ahora_utc": ahora.strftime("%Y-%m-%d %H:%M"), "ventana_h": ventana_h,
        "conteo": {s: conteo.get(s, 0) for s in SENSORES},
        "ultimo_utc": {s: (ultimo[s].strftime("%Y-%m-%d %H:%M") if s in ultimo else None) for s in SENSORES},
        "desconocidos": dict(desconocidos), "alarmas": [], "ceses_confirmados": [], "ceses_pendientes": [],
    }
    if sum(conteo.values()) == 0:
        # POR QUÉ no se culpa a nadie: si callan todas a la vez, la causa es común (NRT detenido, token vencido,
        # NASA caída), no un satélite. El paso de frescura del healthcheck ya abre su issue a las 48 h.
        return {**base, "estado": "caida_general"}

    cese_de = {s: c for c in ceses for s in c["sensores"]}
    alarma_por_plat: dict[str, list[str]] = defaultdict(list)
    cese_por_plat: dict[str, dict] = {}
    pendiente_por_plat: dict[str, dict] = {}
    for s in SENSORES:
        c = cese_de.get(s)
        cumplido = c is not None and ahora >= c["desde"]
        if conteo.get(s, 0) == 0:
            if cumplido:
                fila = cese_por_plat.setdefault(c["plataforma"], {"plataforma": c["plataforma"], "sensores": [],
                                                                  "desde_utc": c["desde_utc"], "fuente": c["fuente"]})
                fila["sensores"].append(s)
            else:
                alarma_por_plat[PLATAFORMA[s]].append(s)
        elif cumplido:
            # El cese anunciado ya debió ocurrir y la plataforma sigue entregando: NASA pudo mover la fecha.
            fila = pendiente_por_plat.setdefault(c["plataforma"], {"plataforma": c["plataforma"], "sensores": [],
                                                                   "desde_utc": c["desde_utc"]})
            fila["sensores"].append(s)

    alarmas = [{"plataforma": p, "sensores": ss} for p, ss in alarma_por_plat.items()]
    return {**base, "estado": "alarma" if alarmas else "ok", "alarmas": alarmas,
            "ceses_confirmados": list(cese_por_plat.values()), "ceses_pendientes": list(pendiente_por_plat.values())}


def informe(v: dict) -> str:
    """Resumen legible (markdown) del veredicto, para el resumen del job y el cuerpo de los issues."""
    ln = [f"## Vigilancia por plataforma, {v['ahora_utc']} UTC", "",
          f"Ventana: últimas **{v['ventana_h']} h**, 11 Tier A. Estado: **{v['estado']}**.", ""]
    if v["estado"] == "caida_general":
        ln += ["**Caída general**: ninguna plataforma tiene records en la ventana. No es un satélite: es el NRT, "
               "la autenticación o NASA. Mira el issue de frescura (`nrt-stale`) y las corridas de `nrt.yml`.", ""]
    for a in v["alarmas"]:
        ln.append(f"- **ALARMA**: {a['plataforma']} ({', '.join(a['sensores'])}) sin records en {v['ventana_h']} h "
                  "mientras las demás plataformas sí producen.")
    for c in v["ceses_confirmados"]:
        ln.append(f"- Informativo: {c['plataforma']} ({', '.join(c['sensores'])}) dejó de producir, como anunció "
                  f"su operador para el {c['desde_utc']} ({c['fuente']}).")
    for c in v["ceses_pendientes"]:
        ln.append(f"- Nota: {c['plataforma']} sigue entregando después de su cese anunciado ({c['desde_utc']}); "
                  "revisa si NASA movió la fecha (scripts/ceses_esperados.json y frontend/cese_plataformas.js).")
    for s, n in v["desconocidos"].items():
        ln.append(f"- Nota: sensor desconocido en los records, `{s}` ({n}); agrégalo a PLATAFORMA si es nuevo.")
    ln += ["", "| sensor | plataforma | records en la ventana | último record (UTC) |", "|---|---|---:|---|"]
    for s in SENSORES:
        ln.append(f"| `{s}` | {PLATAFORMA[s]} | {v['conteo'][s]} | {v['ultimo_utc'][s] or 'sin records'} |")
    return "\n".join(ln) + "\n"


def planear_issues(v: dict, abiertos_alarma: list[dict], existentes_cese: list[dict]) -> list[tuple]:
    """Acciones sobre issues, sin ejecutarlas: ('create', titulo, label, cuerpo), ('comment', n, cuerpo),
    ('close', n, None).

    `abiertos_alarma`: issues ABIERTOS con LABEL_ALARMA. `existentes_cese`: issues con LABEL_CESE en cualquier
    estado (el informativo se abre una sola vez en la vida del cese, aunque alguien lo cierre)."""
    acciones: list[tuple] = []
    if v["estado"] == "caida_general":
        return acciones
    cuerpo = informe(v)

    titulos_cese = {i.get("title") for i in existentes_cese}
    for c in v["ceses_confirmados"]:
        t = titulo_cese(c["plataforma"])
        if t not in titulos_cese:
            acciones.append(("create", t, LABEL_CESE,
                             f"El cese anunciado de **{c['plataforma']}** se confirmó en los datos: sin records "
                             f"desde hace más de {v['ventana_h']} h. Es esperado, no hay nada que arreglar. "
                             "El tablero ya lo avisa al operador (frontend/cese_plataformas.js) y la ficha SDA "
                             "lo declara (v1.10). Este issue se abre una sola vez.\n\n" + cuerpo))

    alarma = next((i for i in abiertos_alarma if i.get("title") == TITULO_ALARMA), None)
    if v["alarmas"]:
        marca = MARCA + " " + ",".join(sorted(s for a in v["alarmas"] for s in a["sensores"])) + " -->\n\n"
        if alarma is None:
            acciones.append(("create", TITULO_ALARMA, LABEL_ALARMA, marca + cuerpo))
        else:
            acciones.append(("comment", alarma["number"], marca + cuerpo))
    elif alarma is not None:
        # S123: un semáforo que sólo sabe ponerse en rojo deja de ser semáforo; se cierra al recuperarse.
        acciones.append(("comment", alarma["number"], "## Recuperado\n\nTodas las plataformas esperadas vuelven "
                         "a producir records. Cierro el issue.\n\n" + cuerpo))
        acciones.append(("close", alarma["number"], None))
    return acciones


def repetir(registros, desde: datetime, hasta: datetime, ceses: list[dict], ventana_h: int = VENTANA_H) -> dict:
    """Corre la regla una vez por día (a la hora de `desde`) entre `desde` y `hasta`, como el cron diario."""
    regs = sorted(registros, key=lambda x: x[1])
    alarmas: Counter = Counter()
    fechas_alarma: dict[str, list[str]] = defaultdict(list)
    caidas = dias = 0
    t = desde
    while t <= hasta:
        dias += 1
        v = evaluar(regs, t, ceses, ventana_h)
        if v["estado"] == "caida_general":
            caidas += 1
        for a in v["alarmas"]:
            for s in a["sensores"]:
                alarmas[s] += 1
                fechas_alarma[s].append(t.date().isoformat())
        t += timedelta(days=1)
    return {"dias": dias, "alarmas_por_sensor": dict(alarmas), "fechas_alarma": dict(fechas_alarma),
            "caidas_generales": caidas}


def huecos(registros, desde: datetime) -> dict:
    """Por sensor: los cinco huecos más largos (h) entre records consecutivos desde `desde`, y el p99."""
    por: dict[str, list[datetime]] = defaultdict(list)
    for s, t in registros:
        if t >= desde:
            por[s].append(t)
    res = {}
    for s in SENSORES:
        ts = sorted(set(por.get(s, [])))
        g = sorted(((b - a).total_seconds() / 3600, a) for a, b in zip(ts, ts[1:]))
        if not g:
            res[s] = None
            continue
        res[s] = {"n_horas_distintas": len(ts), "p99_h": round(g[int(0.99 * (len(g) - 1))][0], 1),
                  "mayores_h_desde": [(round(h, 1), a.strftime("%Y-%m-%d %H:%M")) for h, a in g[-5:]]}
    return res


def _medir(registros, ceses) -> None:
    desde = datetime(2026, 1, 29, 12, 0, tzinfo=timezone.utc)
    hasta = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
    print("Medición de la ventana de la vigilancia por plataforma (S159)")
    print(f"Datos: {len(registros)} records de los 11 Tier A en data/mirova_equivalent/")
    print(f"Desde {desde.date()} (fin del hueco del backfill, nov-2025 a ene-2026) hasta {hasta.date()}.\n")
    print("1) Huecos más largos entre dos records consecutivos de cada sensor (los 11 Tier A juntos):")
    for s, h in huecos(registros, desde).items():
        print(f"   {s:18s} {h}")
    for ventana in (48, 72, 96):
        rep = repetir(registros, desde, hasta, ceses, ventana)
        print(f"\n2) Regla repetida a las 12:00 UTC de cada día, ventana {ventana} h: {rep['dias']} días, "
              f"caídas generales {rep['caidas_generales']}")
        for s in SENSORES:
            n = rep["alarmas_por_sensor"].get(s, 0)
            fechas = rep["fechas_alarma"].get(s, [])
            print(f"   {s:18s} días con alarma={n:3d}  {fechas[:14]}")


def _gh(args, stdin=None, fallos=None):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", input=stdin)
    if r.returncode != 0 and fallos is not None:
        fallos.append(f"gh {' '.join(args[:3])}: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def _ejecutar_issues(v: dict) -> int:
    """Ejecuta el plan con `gh`. Un canal de alerta que falla mudo no es un canal de alerta (S124): si alguna
    llamada falla, sale con 1."""
    repo = os.environ["GH_REPO"]
    fallos: list[str] = []
    raw = _gh(["issue", "list", "--repo", repo, "--label", LABEL_ALARMA, "--state", "open", "--limit", "20",
               "--json", "number,title,body"], fallos=fallos)
    abiertos = json.loads(raw) if raw else []
    raw = _gh(["issue", "list", "--repo", repo, "--label", LABEL_CESE, "--state", "all", "--limit", "50",
               "--json", "number,title,state"], fallos=fallos)
    existentes = json.loads(raw) if raw else []
    if fallos and any("not found" not in f for f in fallos):
        # Sin saber qué issues existen no se puede garantizar «una sola vez»: mejor no crear nada y fallar.
        for f in fallos:
            print(f"WARN {f}")
        return 1
    fallos.clear()   # una etiqueta que todavía no existe da «not found» y equivale a cero issues
    for acc in planear_issues(v, abiertos, existentes):
        if acc[0] == "create":
            _, titulo, label, cuerpo = acc
            color = "BFD4F2" if label == LABEL_CESE else "D93F0B"
            _gh(["label", "create", label, "--repo", repo, "--color", color, "--force",
                 "--description", "Vigilancia por plataforma (S159)"], fallos=fallos)
            _gh(["issue", "create", "--repo", repo, "--title", titulo, "--label", label, "--body-file", "-"],
                stdin=cuerpo, fallos=fallos)
        elif acc[0] == "comment":
            _gh(["issue", "comment", str(acc[1]), "--repo", repo, "--body-file", "-"], stdin=acc[2], fallos=fallos)
        elif acc[0] == "close":
            _gh(["issue", "close", str(acc[1]), "--repo", repo, "--reason", "completed"], fallos=fallos)
        print(f"accion: {acc[0]} {acc[1]}")
    for f in fallos:
        print(f"WARN {f}")
    return 1 if fallos else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Vigilancia por plataforma (S159)")
    ap.add_argument("--datos", default=str(DATOS))
    ap.add_argument("--ahora", help="UTC ISO; por defecto, la hora actual")
    ap.add_argument("--issues", action="store_true", help="abrir, comentar o cerrar issues con gh")
    ap.add_argument("--medir", action="store_true", help="medir huecos y repetir la regla sobre la historia")
    a = ap.parse_args(argv)
    ceses = cargar_ceses()
    registros = cargar_registros(Path(a.datos))
    if a.medir:
        _medir(registros, ceses)
        return 0
    ahora = _utc(a.ahora) if a.ahora else datetime.now(timezone.utc)
    v = evaluar(registros, ahora, ceses)
    txt = informe(v)
    print(txt)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(txt)
    return _ejecutar_issues(v) if a.issues else 0


if __name__ == "__main__":
    sys.exit(main())
