# -*- coding: utf-8 -*-
"""Verificador S162 MxD03, camino A6.9 / A2.11: el workflow probe-s162-mxd03.yml instala
`earthaccess numpy h5py scipy pyyaml` (mas pyhdf). Los tres probes anteriores (1.17, 1.21, 1.23) instalaban ademas
`pyproj pandas`. Si algun modulo que el arnes importa en el runner necesita pandas, pyproj, matplotlib o requests, el job
muere al importar o al primer uso, y el despacho se pierde.

Pregunta 1 (¿lo veria si estuviera roto?): se bloquea la importacion de esos cuatro modulos con un meta_path finder que
levanta ImportError, y se corre el caso base del arnes sintetico (probar_probe_mxd03_ab.correr) mas la importacion de todo
lo que main() del probe y recorrer_en_sha.py importan en el runner. Si algo los necesita, falla aqui.
Pregunta 2 (¿y si el instrumento estuviera muerto?): control positivo al final: `import pandas` dentro del bloqueo tiene
que fallar con ImportError. Si no falla, el bloqueo no funciona y el resultado no vale.
Uso: cd D:/vrp-trabajo/s162-mxd03 && PYTHONIOENCODING=utf-8 python experiments/_s162_mxd03/verificador/verif_deps_bloqueadas.py
"""
import importlib.abc
import os
import sys
from pathlib import Path

BLOQUEADOS = ("pandas", "pyproj", "matplotlib", "requests")


class Bloqueo(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.intentos = []

    def find_spec(self, name, path, target=None):
        raiz = name.split(".")[0]
        if raiz in BLOQUEADOS:
            self.intentos.append(name)
            raise ImportError(f"[verificador] modulo bloqueado como en el runner: {name}")
        return None


def main():
    RAIZ = Path(__file__).resolve().parents[3]
    AB = RAIZ / "experiments/_s162_mxd03"
    for p in (AB, RAIZ / "experiments/_s151_mxd03_etiquetas", RAIZ / "scripts", RAIZ):
        sys.path.insert(0, str(p))
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    b = Bloqueo()
    sys.meta_path.insert(0, b)
    fallas = []
    # lo que importa el probe al cargar y en main(), y recorrer_en_sha
    for mod in ("probe_mxd03_ab", "run_pipeline", "pipeline.fetch", "banco_paridad", "referencia_mirova_unificada",
                "clase_mirova", "probar_probe_mxd03_ab", "evaluar_mxd03", "recorrer_en_sha"):
        try:
            importlib.import_module(mod)
            print("import", mod, "OK")
        except ImportError as e:
            fallas.append((mod, repr(e)))
            print("import", mod, "FALLA:", repr(e)[:200])
        except Exception as e:  # noqa: BLE001
            fallas.append((mod, repr(e)))
            print("import", mod, "EXCEPCION:", repr(e)[:200])
    # el caso base del arnes (calculate_vrp + append_record + node) con los modulos bloqueados
    try:
        import probar_probe_mxd03_ab as T
        pres, aus, sinr = T.correr()
        f = T.aserciones(pres, aus, sinr)
        print("caso base del arnes con dependencias bloqueadas:", "OK" if not f else "FALLAS " + " | ".join(f))
        if f:
            fallas.append(("caso base", f))
    except Exception as e:  # noqa: BLE001
        fallas.append(("caso base", repr(e)))
        print("caso base del arnes: EXCEPCION", repr(e)[:300])
    # control positivo del bloqueo
    try:
        import pandas  # noqa: F401
        print("CONTROL POSITIVO FALLA: pandas se importo pese al bloqueo; el resultado de arriba no vale")
        fallas.append(("control", "bloqueo inerte"))
    except ImportError:
        print("control positivo OK: pandas bloqueado levanta ImportError")
    print("modulos bloqueados que alguien intento importar:", sorted(set(b.intentos)))
    print("RESULTADO:", "LIMPIO" if not fallas else f"{len(fallas)} fallas")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
