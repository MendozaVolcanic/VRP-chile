# -*- coding: utf-8 -*-
"""S158: baja el dataset de Vulcano VIIRS 375 de MIROVA (OSF jepv6, Campus et al. 2024) a una carpeta temporal.

POR QUÉ: jepv6 no declara licencia, así que sus archivos no se versionan en el repo. Este script los baja de nuevo,
verificando el sha256 que publica OSF, para que `jepv6_cenit.py` se pueda reproducir. Bajado con permiso de Nicolás
el 2026-10-21. Uso: python -I bajar_jepv6.py <carpeta destino vacía>  (después: jepv6_cenit.py <destino>/S1_MIROVA_Vulcano.csv)
"""
import hashlib, json, os, sys, time, urllib.request


def get(u, binario=False):
    for i in range(4):
        try:
            with urllib.request.urlopen(u, timeout=120) as r:
                return r.read() if binario else json.load(r)
        except Exception as e:
            err = e
            time.sleep(2 + 2 * i)
    raise err


destino = sys.argv[1]
os.makedirs(destino, exist_ok=True)
for f in get("https://api.osf.io/v2/nodes/jepv6/files/osfstorage/")["data"]:
    a = f["attributes"]
    d = get(f["links"]["download"], binario=True)
    ok = hashlib.sha256(d).hexdigest() == (a.get("extra") or {}).get("hashes", {}).get("sha256")
    open(os.path.join(destino, a["name"]), "wb").write(d)
    print(a["name"], len(d), "sha256 OK" if ok else "sha256 DISTINTO")
