# -*- coding: utf-8 -*-
"""S158: baja la carpeta MIROVA_Code_Repository del proyecto OSF de MIROVA (zm62w) y verifica cada hash.

POR QUÉ: Coppola et al. 2026 (Scientific Data, p. 21, «Code Availability») dice que el núcleo científico de
MIROVA (la detección de píxeles anómalos, MATLAB R2024) es público en https://doi.org/10.17605/OSF.IO/ZM62W.
Bajado con permiso de Nicolás (2026-10-21). Los .m se leen como texto; nada se ejecuta.
Uso: python -I bajar_codigo_osf.py <carpeta destino vacía>
"""
import hashlib, json, os, sys, time, urllib.request

RAIZ = "https://api.osf.io/v2/nodes/zm62w/files/osfstorage/?page%5Bsize%5D=100"


def get(u, binario=False):
    for i in range(4):
        try:
            with urllib.request.urlopen(u, timeout=120) as r:
                return r.read() if binario else json.load(r)
        except Exception as e:
            err = e
            time.sleep(2 + 2 * i)
    raise err


def carpeta(u, nombre):
    for f in get(u)["data"]:
        if f["attributes"]["name"] == nombre:
            return f["relationships"]["files"]["links"]["related"]["href"]
    raise SystemExit(f"no está la carpeta {nombre}")


def bajar(u, destino, rel=""):
    for f in get(u)["data"]:
        a = f["attributes"]
        ruta = os.path.join(destino, rel, a["name"])
        if a["kind"] == "folder":
            os.makedirs(ruta, exist_ok=True)
            bajar(f["relationships"]["files"]["links"]["related"]["href"], destino, os.path.join(rel, a["name"]))
            continue
        datos = get(f["links"]["download"], binario=True)
        sha = hashlib.sha256(datos).hexdigest()
        esperado = (a.get("extra") or {}).get("hashes", {}).get("sha256")
        estado = "OK" if sha == esperado else f"DISTINTO (OSF {esperado})"
        open(ruta, "wb").write(datos)
        print(f"{os.path.join(rel, a['name'])}: {len(datos)} bytes, sha256 {sha[:16]}... {estado}, modificado {a.get('date_modified')}")


if __name__ == "__main__":
    destino = sys.argv[1]
    os.makedirs(destino, exist_ok=True)
    bajar(carpeta(RAIZ, "MIROVA_Code_Repository"), destino)
