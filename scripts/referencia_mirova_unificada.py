# -*- coding: utf-8 -*-
"""Referencia MIROVA por pasada: consolidado + OCR + respaldo del 2026-04-08.

POR QUE (S139, Fase 0 tarea 2 del plan de paridad). Para medir cuanto publicamos de mas hacen
falta NEGATIVOS: pasadas donde MIROVA miro el volcan y no vio nada (RUTINA) o vio calor fuera del
crater (FALSO_POSITIVO). `pipeline.mirova_csv_loader.load_mirova_alertas` no sirve para eso porque
descarta toda fila que no sea alerta (l. 147-149). Este modulo lee los dos CSV primarios de
Mirova-v1 conservando TODAS las filas y reusa del loader solo la normalizacion.

Por que el respaldo: el consolidado de Mirova-v1 perdio filas en su historia (issue
MendozaVolcanic/Mirova-v1#19). Contra el respaldo local del 2026-04-08 faltan 244 pasadas de
enero a abril de 2026 (221 RUTINA, 17 ALERTA_TERMICA, 6 FALSO_POSITIVO), medido S140 contra el
remoto sha 502efc1d4. Ninguna pasada compartida cambia de tipo entre las dos copias, asi que la
union no introduce contradicciones: cuando la clave existe en ambas se conserva la principal.

Fuente: el REMOTO de Mirova-v1 (el snapshot del repo lo actualiza solo el auto-audit semanal y se
atrasa). `main()` lo baja, registra el sha y guarda copia ignorada en `experiments/**/_dl_*/`.
Los tests usan el snapshot commiteado, que es subconjunto exacto del remoto, para no depender de red.

Clave de una pasada: (volcano, sensor_bucket, Fecha_Satelite_UTC al minuto, source).

Union historica (S150, tarea 0.1 del loop). El respaldo de abril no alcanza: el consolidado volvio
a perder filas el 23-abr, 25-ago, 26-ago y 06-oct (docs/audit_s150/meta/VERIFICADOR_DATOS.md D1),
y la ultima caida se llevo 207 filas con 8 alertas. `--union-historica` recorre la historia del
consolidado en Mirova-v1 tomando la ultima version de cada dia (por la API, sin clonar: el repo
pesa 13 GB y el archivo tiene decenas de miles de versiones) y guarda en `HISTORICO_RECUPERADAS`
solo las filas que la version mas nueva ya no trae. Muestreo diario y no por commit porque las
filas perdidas son viejas (las 207 del 06-oct tienen fecha de satelite de enero a octubre): una
fila que naciera y se perdiera dentro del mismo dia se escaparia, y eso queda declarado.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.mirova_csv_loader import (normalize_sensor,  # noqa: E402
                                        normalize_volcano_name,
                                        parse_ocr_distance)

SNAP = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot"
SNAP_CONS = SNAP / "registro_vrp_consolidado.csv"
SNAP_OCR = SNAP / "registro_vrp_ocr.csv"
RESPALDO_20260408 = SNAP / "registro_vrp_consolidado_respaldo_20260408.csv"
UNION_DIR = ROOT / "data" / "mirova_reference" / "union_historica"
HISTORICO_RECUPERADAS = UNION_DIR / "consolidado_filas_perdidas.csv"
HISTORICO_PROCEDENCIA = UNION_DIR / "procedencia.json"

REPO_MIROVA = "MendozaVolcanic/Mirova-v1"
RUTA_REMOTA = "monitoreo_satelital"
URL_RAW = f"https://raw.githubusercontent.com/{REPO_MIROVA}/{{sha}}/{RUTA_REMOTA}/{{nombre}}"


def _float(v) -> Optional[float]:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def leer_pasadas(path: Path, source: str, origen: str) -> list[dict]:
    """Todas las filas Tier A de un CSV primario, normalizadas. No filtra por tipo.

    Si una clave se repite dentro del mismo archivo, gana la de `Ultima_Actualizacion` mas
    reciente. Caso real: el respaldo trae 3 pasadas de PlanchonPeteroa del 2026-01-16 dos veces
    (el dia del renombre Peteroa -> PlanchonPeteroa), identicas salvo la hora de actualizacion.
    """
    por_clave: dict[tuple, dict] = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            vol = normalize_volcano_name(r.get("Volcan"))
            fecha = (r.get("Fecha_Satelite_UTC") or "").strip()
            if vol is None or len(fecha) < 16:
                continue
            bucket = normalize_sensor(r.get("Sensor"))
            dist = _float(r.get("Distancia_km"))
            if source == "OCR" and not (dist and dist > 0):
                # Las filas OCR traen Distancia_km=0; la distancia vive en la nota (F-B2, S139).
                dist = parse_ocr_distance(r.get("Nota_Validacion", ""))
            fila = {
                "volcano": vol,
                "sensor_bucket": bucket,
                "sensor_raw": (r.get("Sensor") or "").strip(),
                "fecha_utc": fecha,
                "source": source,
                "origen": origen,
                "tipo": (r.get("Tipo_Registro") or "").strip(),
                "vrp_mw": _float(r.get("VRP_MW")),
                "dist_km": dist,
                "clasificacion": (r.get("Clasificacion Mirova") or "").strip(),
                "ultima_actualizacion": (r.get("Ultima_Actualizacion") or "").strip(),
            }
            k = clave(fila)
            previa = por_clave.get(k)
            if previa is None or fila["ultima_actualizacion"] > previa["ultima_actualizacion"]:
                por_clave[k] = fila
    return list(por_clave.values())


def clave(fila: dict) -> tuple:
    return (fila["volcano"], fila["sensor_bucket"], fila["fecha_utc"][:16], fila["source"])


def cargar_referencia_unificada(cons_path: Path = SNAP_CONS, ocr_path: Path = SNAP_OCR,
                                respaldo_path: Optional[Path] = RESPALDO_20260408,
                                historico_path: Optional[Path] = HISTORICO_RECUPERADAS) -> list[dict]:
    """Union de consolidado + OCR principales con la historia y el respaldo del consolidado.

    La fila principal gana siempre; despues entran las filas que la historia de Mirova-v1 tuvo y
    perdio (origen "historico") y al final las del respaldo, cada una solo si su clave no existe
    todavia. `historico_path=None` o `respaldo_path=None` apagan esa capa (control de instrumento).
    Desde S150 la historia entra por defecto: un experimento anterior (S141 a S149) que llame a esta
    funcion sin argumentos y se vuelva a correr hoy mide contra mas filas que cuando se congelo.
    """
    filas = {clave(f): f for f in leer_pasadas(Path(cons_path), "CONS", "principal")}
    for f in leer_pasadas(Path(ocr_path), "OCR", "principal"):
        filas.setdefault(clave(f), f)
    if historico_path is not None:
        for f in leer_pasadas(Path(historico_path), "CONS", "historico"):
            filas.setdefault(clave(f), f)
    if respaldo_path is not None:
        for f in leer_pasadas(Path(respaldo_path), "CONS", "respaldo_20260408"):
            filas.setdefault(clave(f), f)
    return sorted(filas.values(), key=lambda f: (f["fecha_utc"], f["volcano"], f["sensor_bucket"], f["source"]))


def sha_remoto(nombre: str) -> str:
    out = subprocess.run(
        ["gh", "api", f"repos/{REPO_MIROVA}/commits?path={RUTA_REMOTA}/{nombre}&per_page=1",
         "-q", ".[0].sha"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def bajar_remoto(dest: Path) -> dict:
    """Baja consolidado y OCR del remoto fijados a un sha. Devuelve rutas y shas."""
    dest.mkdir(parents=True, exist_ok=True)
    info = {}
    for nombre in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        sha = sha_remoto(nombre)
        destino = dest / nombre
        urllib.request.urlretrieve(URL_RAW.format(sha=sha, nombre=nombre), destino)
        info[nombre] = {"sha": sha, "path": str(destino)}
    return info


def _con_reintentos(fn, intentos: int = 4):
    """Reintenta ante fallos transitorios de red o de la API (verificador de #778: 318 llamadas
    seguidas sin reintento abortaban la union entera por un solo error)."""
    import time
    for i in range(intentos):
        try:
            return fn()
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(5 * (i + 1))


def versiones_diarias(nombre: str, desde: str, hasta: str) -> list[dict]:
    """Ultimo commit de cada dia que toco `nombre`, de `desde` a `hasta` (AAAA-MM-DD, UTC)."""
    from datetime import date, timedelta
    d, fin = date.fromisoformat(desde), date.fromisoformat(hasta)
    vistas, out = set(), []
    while d <= fin:
        cmd = ["gh", "api", f"repos/{REPO_MIROVA}/commits?path={RUTA_REMOTA}/{nombre}"
               f"&until={d.isoformat()}T23:59:59Z&per_page=1",
               "-q", '.[0] | .sha + " " + .commit.committer.date']
        partes = _con_reintentos(lambda: subprocess.run(cmd, capture_output=True, text=True,
                                                         check=True).stdout.split())
        if len(partes) == 2 and partes[0] not in vistas:
            vistas.add(partes[0])
            out.append({"dia": d.isoformat(), "sha": partes[0], "fecha_commit": partes[1]})
        d += timedelta(days=1)
    return out


def _bajar_version(nombre: str, sha: str) -> tuple[list[str], list[dict]]:
    """Encabezado y filas crudas de una version del CSV remoto, sin escribir a disco."""
    import io
    def _leer():
        with urllib.request.urlopen(URL_RAW.format(sha=sha, nombre=nombre), timeout=120) as resp:
            return resp.read().decode("utf-8")
    texto = _con_reintentos(_leer)
    lector = csv.DictReader(io.StringIO(texto))
    return list(lector.fieldnames or []), list(lector)


def _clave_cruda(r: dict) -> Optional[tuple]:
    vol = normalize_volcano_name(r.get("Volcan"))
    fecha = (r.get("Fecha_Satelite_UTC") or "").strip()
    if vol is None or len(fecha) < 16:
        return None
    return (vol, normalize_sensor(r.get("Sensor")), fecha[:16], "CONS")


def union_historica(desde: str, hasta: str, hilos: int = 6) -> dict:
    """Recorre las versiones diarias del consolidado y escribe las filas que la mas nueva perdio.

    Por clave se conserva la fila de la ULTIMA version que la tuvo. Devuelve la procedencia: por
    version, cuantas filas trae y cuantas de las perdidas aporta por ultima vez.
    """
    from concurrent.futures import ThreadPoolExecutor
    nombre = "registro_vrp_consolidado.csv"
    versiones = versiones_diarias(nombre, desde, hasta)
    ultima: dict[tuple, tuple[dict, str]] = {}
    tipos: dict[tuple, set] = {}
    columnas: list[str] = []
    claves_nueva: set = set()
    with ThreadPoolExecutor(hilos) as ex:
        for v, (cab, filas) in zip(versiones, ex.map(lambda v: _bajar_version(nombre, v["sha"]), versiones)):
            columnas += [c for c in cab if c not in columnas]
            claves_v = set()
            for r in filas:
                k = _clave_cruda(r)
                if k is None:
                    continue
                claves_v.add(k)
                ultima[k] = (r, v["sha"])
                tipos.setdefault(k, set()).add((r.get("Tipo_Registro") or "").strip())
            v["n_claves"] = len(claves_v)
            claves_nueva = claves_v
    perdidas = {k: ultima[k] for k in ultima if k not in claves_nueva}
    UNION_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORICO_RECUPERADAS, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas + ["Version_Mirova_v1"], extrasaction="ignore")
        w.writeheader()
        for k in sorted(perdidas):
            r, sha = perdidas[k]
            w.writerow({**r, "Version_Mirova_v1": sha})
    aporte = Counter(sha for _, sha in perdidas.values())
    for v in versiones:
        v["aporta_perdidas"] = aporte.get(v["sha"], 0)
    procedencia = {
        "repo": REPO_MIROVA, "archivo": f"{RUTA_REMOTA}/{nombre}", "muestreo": "ultima version de cada dia UTC",
        "desde": desde, "hasta": hasta, "n_versiones": len(versiones),
        "version_mas_nueva": versiones[-1] if versiones else None,
        "n_claves_union": len(ultima), "n_perdidas": len(perdidas),
        "perdidas_por_tipo": dict(Counter((r.get("Tipo_Registro") or "").strip() for r, _ in perdidas.values())),
        "claves_con_tipo_cambiante": sum(len(t) > 1 for t in tipos.values()),
        "versiones": versiones,
    }
    HISTORICO_PROCEDENCIA.write_text(json.dumps(procedencia, indent=1, ensure_ascii=False), encoding="utf-8")
    return procedencia


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", action="store_true",
                    help="usar el snapshot commiteado en vez del remoto (sin red)")
    ap.add_argument("--dest", default=str(ROOT / "experiments" / "_s140" / "_dl_referencia"))
    ap.add_argument("--salida", default=None, help="JSON con las filas y la procedencia")
    ap.add_argument("--union-historica", action="store_true",
                    help="regenerar las filas perdidas desde la historia de Mirova-v1 y salir")
    ap.add_argument("--desde", default="2025-12-01")
    ap.add_argument("--hasta", default=None, help="AAAA-MM-DD; por defecto hoy UTC")
    a = ap.parse_args(argv)

    if a.union_historica:
        from datetime import datetime, timezone
        hasta = a.hasta or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        p = union_historica(a.desde, hasta)
        resumen = {k: v for k, v in p.items() if k != "versiones"}
        print(json.dumps(resumen, indent=1, ensure_ascii=False))
        print("versiones que aportan perdidas:",
              [(v["dia"], v["aporta_perdidas"]) for v in p["versiones"] if v["aporta_perdidas"]])
        return 0

    if a.snapshot:
        procedencia = {"fuente": "snapshot", "cons": str(SNAP_CONS), "ocr": str(SNAP_OCR)}
        cons, ocr = SNAP_CONS, SNAP_OCR
    else:
        info = bajar_remoto(Path(a.dest))
        procedencia = {"fuente": "remoto", **info}
        cons = Path(info["registro_vrp_consolidado.csv"]["path"])
        ocr = Path(info["registro_vrp_ocr.csv"]["path"])
    procedencia["respaldo"] = str(RESPALDO_20260408)

    ref = cargar_referencia_unificada(cons, ocr)
    principal = {clave(f) for f in cargar_referencia_unificada(cons, ocr, respaldo_path=None)}
    del_respaldo = [f for f in ref if clave(f) not in principal]

    print(json.dumps(procedencia, indent=2, ensure_ascii=False))
    print(f"pasadas: {len(ref)}  (principal {len(principal)}, del respaldo {len(del_respaldo)})")
    print("por tipo:", dict(Counter(f["tipo"] for f in ref)))
    print("recuperadas del respaldo por tipo:", dict(Counter(f["tipo"] for f in del_respaldo)))
    if a.salida:
        Path(a.salida).write_text(json.dumps({"procedencia": procedencia, "filas": ref},
                                             ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
