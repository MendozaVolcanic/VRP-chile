"""S157: bateria de mutaciones con control (A110) sobre la busqueda por ventana, la cobertura y el driver de brazos.

POR QUE. Una prueba que pasa no dice que mira lo que dice mirar. Cada mutacion mete a proposito uno de los errores
que el cambio podria tener (el reparto por dia, la regla standard → NRT, la cobertura, el modo estricto, la cache de
los brazos) en una COPIA del codigo, corre las pruebas de S157 y cuenta si alguna la atrapa.

Cuenta como ATRAPADA solo la mutacion que hace fallar una prueba por ASERCION. Si las pruebas caen por un error de
otro tipo (import, sintaxis, excepcion no esperada), la mutacion se informa como CAIDA y no se cuenta (memoria S152:
una mutacion que cae no es atrapada). Control: la copia SIN mutar tiene que pasar entera; si no, la bateria no vale.

Uso: python experiments/_s157_busqueda_ventana/mutaciones.py [--salida resultado_mutaciones.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRUEBAS = ["tests/test_busqueda_ventana_s157.py", "tests/test_reproc_brazos_s157.py",
           "tests/test_unir_trozos_ab_s157.py"]

# (nombre, archivo, texto original, texto mutado). El original tiene que aparecer EXACTAMENTE una vez.
MUTACIONES = [
    ("borde superior excluyente", "pipeline/fetch.py",
     "if out[d] is not None and ini <= lim[d][1] and fin >= lim[d][0]:",
     "if out[d] is not None and ini < lim[d][1] and fin >= lim[d][0]:"),
    ("borde inferior excluyente", "pipeline/fetch.py",
     "if out[d] is not None and ini <= lim[d][1] and fin >= lim[d][0]:",
     "if out[d] is not None and ini <= lim[d][1] and fin > lim[d][0]:"),
    ("reparto corrido un dia", "pipeline/fetch.py",
     "datetime.strptime(d, \"%Y-%m-%d\") + timedelta(hours=23, minutes=59, seconds=59))",
     "datetime.strptime(d, \"%Y-%m-%d\") + timedelta(hours=47, minutes=59, seconds=59))"),
    ("sin margen de medianoche", "pipeline/fetch.py",
     "if abs((t - m).total_seconds()) <= _MARGEN_MEDIANOCHE_S:",
     "if False:"),
    ("sin la regla de 20", "pipeline/fetch.py",
     "if out[d] is not None and len(out[d]) >= _COUNT_POR_DIA:",
     "if False:"),
    ("NRT antes que standard", "pipeline/fetch.py",
     "    return out\n\n\ndef _parse_cmr",
     "    return list(reversed(out))\n\n\ndef _parse_cmr"),
    ("intento siguiente sobre toda la ventana", "pipeline/fetch.py",
     "                                 pendientes[0], pendientes[-1])",
     "                                 dias[0], dias[-1])"),
    ("dia ya resuelto se vuelve a pisar", "pipeline/fetch.py",
     "            if por_dia[d] is None or por_dia[d]:\n                resultado[d] = por_dia[d]\n            else:",
     "            if por_dia[d] is None or por_dia[d] or True:\n                resultado[d] = por_dia[d]\n            else:"),
    ("ventana truncada se usa igual", "pipeline/fetch.py",
     "        if len(res) >= _VENTANA_COUNT:  # truncada",
     "        if False:  # truncada"),
    ("sin reintento de la ventana", "pipeline/fetch.py",
     "_VENTANA_ESPERAS_S = [0, 20]   # un intento y un reintento",
     "_VENTANA_ESPERAS_S = [0]   # un intento y un reintento"),
    ("ventana fallida no se apaga", "pipeline/fetch.py",
     "                _VENTANA_APAGADA = True\n",
     "                pass\n"),
    ("cache en disco no se guarda", "pipeline/fetch.py",
     "            _guardar_cache(key, por_dia)\n",
     "            pass\n"),
    ("interruptor ignorado", "pipeline/fetch.py",
     "if os.environ.get(\"VRP_BUSQUEDA_VENTANA\", \"1\") == \"0\":",
     "if False:"),
    ("cortacircuito no registra", "pipeline/fetch.py",
     "        _registrar_falla(product_key, date_str, \"SEARCH_SKIP: CMR degradada esta corrida\")\n",
     ""),
    ("except generico no registra", "pipeline/fetch.py",
     "            _registrar_falla(producto, fecha_str, f\"{type(e).__name__}: {str(e)[:150]}\", etapa=etapa)\n",
     ""),
    ("descarga registrada como busqueda", "pipeline/fetch.py",
     "            etapa, producto = \"descarga\", l1b_key\n",
     "            producto = l1b_key\n"),
    ("estricto no sale con 3", "scripts/run_pipeline.py",
     "    return 3 if estricto else 0",
     "    return 0"),
    ("run_pipeline no configura la ventana", "scripts/run_pipeline.py",
     "        fetch.configurar_ventana(dates, cache_dir=os.environ.get(\"VRP_CACHE_BUSQUEDA_DIR\") or None,\n"
     "                                 ventana=ventana_env)\n",
     ""),
    ("conservar granulos ignorado", "scripts/run_pipeline.py",
     "if volcano_tmp.exists() and os.environ.get(\"VRP_CONSERVAR_GRANULOS\") != \"1\":",
     "if volcano_tmp.exists():"),
    ("driver borra antes del segundo brazo", "scripts/reproc_brazos.py",
     "            if r.returncode != 0:\n                fallidos.append((fecha, perfil, r.returncode))\n",
     "            if r.returncode != 0:\n                fallidos.append((fecha, perfil, r.returncode))\n"
     "            shutil.rmtree(granulos / volcan / fecha.replace(\"-\", \"\"), ignore_errors=True)\n"),
    ("driver brazo por fuera", "scripts/reproc_brazos.py",
     "    for fecha in fechas(ini, fin):\n        for perfil in perfiles:\n",
     "    for perfil in perfiles:\n        for fecha in fechas(ini, fin):\n"),
    ("driver sin cache de busqueda compartida", "scripts/reproc_brazos.py",
     "                r = ejecutar(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)",
     "                r = ejecutar(cmd, env=dict(env, VRP_CACHE_BUSQUEDA_DIR=str(trabajo / perfil)), stdout=fh, "
     "stderr=subprocess.STDOUT)"),
    ("driver estricto ignorado", "scripts/reproc_brazos.py",
     "        return 3 if estricto else 0",
     "        return 0"),
    ("driver ignora brazo caido", "scripts/reproc_brazos.py",
     "    if fallidos:\n",
     "    if False:\n"),
    ("union con merge-multiple (se pisan)", "scripts/unir_trozos_ab.py",
     "        if len(lista) == 1:\n",
     "        if True:\n            lista = lista[-1:]\n"),
    ("trozo de 37 dias fijo", "scripts/reproc_brazos.py",
     "    return max(1, int(_PRESUPUESTO_MIN // costo))",
     "    return 37"),
    # Hallazgos del verificador limpio de S157, con su arreglo:
    ("etiquetado fuera del finally", "pipeline/fetch.py",
     "        finally:\n            # finally y no despues del try",
     "        except BaseException:\n            raise\n        if True:\n            # finally y no despues del try"),
    ("dias recientes dentro de la ventana", "pipeline/fetch.py",
     "        if d.strftime(\"%Y-%m-%d\") < primer_reciente:",
     "        if True:"),
    ("ventana apagada deja de servir lo cargado", "pipeline/fetch.py",
     "    if _VENTANA is None or not (_VENTANA[\"ini\"] <= dia <= _VENTANA[\"fin\"]):",
     "    if _VENTANA is None or _VENTANA_APAGADA or not (_VENTANA[\"ini\"] <= dia <= _VENTANA[\"fin\"]):"),
    ("cache corrupta no se atrapa", "pipeline/fetch.py",
     "        except (OSError, ValueError, KeyError, TypeError) as e:",
     "        except ZeroDivisionError as e:"),
    ("cobertura del driver solo al final", "scripts/reproc_brazos.py",
     "        if cobertura_json:\n            Path(cobertura_json).parent",
     "        if cobertura_json and fecha == fin:\n            Path(cobertura_json).parent"),
]


# Mutaciones EQUIVALENTES, declaradas antes de correr: no cambian ninguna salida posible, asi que ninguna prueba puede
# atraparlas. Los bordes de la regla de traslape son 23:59:59 y 00:00:00, y todo granulo a menos de 2 s de una
# medianoche ya se manda a la consulta por dia (_MARGEN_MEDIANOCHE_S); por eso `<=` contra `<` en los bordes no
# cambia nada. Se corren igual para mostrarlo, y se cuentan aparte.
EQUIVALENTES = {"borde superior excluyente", "borde inferior excluyente"}


def _copia(dest: Path) -> None:
    for d in ("pipeline", "scripts", "tests"):
        shutil.copytree(RAIZ / d, dest / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in ("pytest.ini", "volcanoes.yaml"):
        shutil.copy2(RAIZ / f, dest / f)


def _correr(dest: Path) -> tuple[str, str]:
    env = dict(os.environ)
    env.pop("VRP_BUSQUEDA_VENTANA", None)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x", "--tb=line"] + PRUEBAS,
                       cwd=dest, capture_output=True, text=True, env=env, timeout=900)
    salida = r.stdout + r.stderr
    if r.returncode == 0:
        return "PASA", ""
    lineas = [x for x in salida.splitlines() if re.search(r"(Error|assert)", x)]
    if any(re.search(r"AssertionError|assert ", x) for x in lineas) and not re.search(
            r"(SyntaxError|ImportError|NameError|ModuleNotFoundError|IndentationError)", salida):
        return "ATRAPADA", (lineas[0] if lineas else "")[:200]
    return "CAIDA", (lineas[0] if lineas else salida[-300:])[:200]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(Path(__file__).with_name("resultado_mutaciones.json")))
    a = ap.parse_args()
    base = Path(tempfile.mkdtemp(prefix="mut_s157_"))
    try:
        ctl = base / "control"
        _copia(ctl)
        estado, det = _correr(ctl)
        print(f"CONTROL (sin mutar): {estado} {det}", flush=True)
        if estado != "PASA":
            print("la copia sin mutar no pasa: la bateria no vale")
            return 2
        res = []
        for nombre, archivo, orig, mut in MUTACIONES:
            dest = base / "m"
            if dest.exists():
                shutil.rmtree(dest)
            _copia(dest)
            p = dest / archivo
            txt = p.read_text(encoding="utf-8")
            n = txt.count(orig)
            if n != 1:
                res.append({"mutacion": nombre, "estado": "NO APLICADA", "detalle": f"original aparece {n} veces"})
                print(f"NO APLICADA {nombre}: {n}", flush=True)
                continue
            p.write_text(txt.replace(orig, mut), encoding="utf-8")
            estado, det = _correr(dest)
            if estado == "PASA" and nombre in EQUIVALENTES:
                estado = "EQUIVALENTE"
            res.append({"mutacion": nombre, "archivo": archivo, "estado": estado, "detalle": det})
            print(f"{estado:9s} {nombre} | {det[:120]}", flush=True)
        cuenta = {e: sum(1 for r in res if r["estado"] == e) for e in ("ATRAPADA", "PASA", "CAIDA", "EQUIVALENTE", "NO APLICADA")}
        print(json.dumps(cuenta))
        Path(a.salida).write_text(json.dumps({"control": "PASA", "cuenta": cuenta, "mutaciones": res},
                                             indent=1, ensure_ascii=False), encoding="utf-8")
        return 0 if cuenta["PASA"] == 0 and cuenta["NO APLICADA"] == 0 else 1
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
