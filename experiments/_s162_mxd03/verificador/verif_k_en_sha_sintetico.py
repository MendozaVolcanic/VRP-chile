# -*- coding: utf-8 -*-
"""Verificador S162 MxD03, afirmacion A3: k_en_sha.py no tiene prueba local (pyhdf). Aqui se corre su main() REAL con
el arbol = este checkout (main congelado), reemplazando solo pm.read_modis_l1b por la escena sintetica de la 1.17 (la
misma que usa probar_probe_mxd03_ab). Lo que prueba: (1) el parche `store.DATA_DIR = Path(tmp)` SI redirige la escritura
(el record vuelve en el JSON de stdout); (2) el filtrado por firma no omite nada en main; (3) la ultima linea de stdout
es JSON parseable (recorrer_en_sha.py lee splitlines()[-1]); (4) el record reproducido es IGUAL al que da el brazo K del
arnes sobre la misma escena (control de identidad entre los dos caminos, sin marcas de hora).
Lo que NO prueba: el checkout de un codigo_sha viejo ni el `git worktree add` del runner.

Pregunta 1: si store.DATA_DIR no redirigiera, rec seria None y (4) fallaria. Pregunta 2: control positivo: con el
parche de DATA_DIR anulado (store escribe en su DATA_DIR real... NO se hace, escribiria en data/); en su lugar se
comprueba que data/mirova_equivalent/<vol>.json NO cambio (sha256 antes y despues).
Uso: cd D:/vrp-trabajo/s162-mxd03 && PYTHONIOENCODING=utf-8 python experiments/_s162_mxd03/verificador/verif_k_en_sha_sintetico.py
"""
import hashlib
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[3]
AB = RAIZ / "experiments/_s162_mxd03"
for p in (AB, RAIZ / "experiments/_s151_mxd03_etiquetas", RAIZ / "scripts", RAIZ):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402
import probar_probe_mxd03 as T  # noqa: E402  (escena 1.17)
import probe_mxd03_ab as A  # noqa: E402
from pipeline import process_modis as pm  # noqa: E402
import run_pipeline as rp  # noqa: E402  (el volcan sintetico no esta en volcanoes.yaml: se parchea el loader)
import k_en_sha  # noqa: E402


def main():
    vol = T.VOLCAN["name"]
    data_json = RAIZ / "data/mirova_equivalent" / f"{vol}.json"
    h_antes = hashlib.sha256(data_json.read_bytes()).hexdigest() if data_json.exists() else None
    verdad = T.escena()
    # grilla "interp" corrida 2 km al sur (como PRESENTE en la prueba del auditor): K publica
    interp = dict(verdad)
    interp["lat"] = (verdad["lat"].astype(np.float64) - 2.0 / 111.32).astype(np.float32)

    def lector(_p):
        return A.P._copia(interp)

    # 1) k_en_sha.main() real, con el arbol = este checkout
    argv = ["k_en_sha.py", "--arbol", str(RAIZ), "--l1b", str(T.L1B), "--geo", "geo.hdf", "--vol", vol]
    buf = io.StringIO()
    with patch.object(sys, "argv", argv), patch.object(pm, "read_modis_l1b", lector), \
            patch.object(rp, "load_volcanoes", lambda nombre: [T.VOLCAN]), redirect_stdout(buf):
        k_en_sha.main()
    lineas = buf.getvalue().strip().splitlines()
    salida = json.loads(lineas[-1])
    rec_sha = salida["rec"]
    print("lineas de stdout:", len(lineas), "| ultima parseable como JSON: OK")
    print("firma_omitidos:", salida["firma_omitidos"])
    print("rec devuelto:", "None" if rec_sha is None else f"pc_vrp={ (rec_sha.get('primary_cluster') or {}).get('vrp_mw') } dc={rec_sha.get('distance_class')}")
    # 2) el brazo K del arnes sobre la misma escena
    rec_k, _ = A.brazo(T.L1B, Path("geo.hdf"), T.VOLCAN, None, interp)
    iguales = A.P.registros_iguales(rec_k, rec_sha)
    print("k_en_sha reproduce el brazo K del arnes (sin marcas de hora):", iguales)
    pub = A.P.publica([rec_sha, rec_k], T.VOLCAN.get("inner_radius_km"))
    print("publica (sha, K):", pub)
    h_despues = hashlib.sha256(data_json.read_bytes()).hexdigest() if data_json.exists() else None
    print("data/mirova_equivalent intacto:", h_antes == h_despues)
    fallas = []
    if rec_sha is None:
        fallas.append("k_en_sha devolvio rec None: el parche de store.DATA_DIR no redirige o calculate_vrp fallo")
    if salida["firma_omitidos"]:
        fallas.append("en main no deberia omitirse ningun argumento")
    if not iguales:
        fallas.append("k_en_sha y el brazo K del arnes difieren sobre la misma escena")
    if h_antes != h_despues:
        fallas.append("data/ cambio: el parche escribio en produccion")
    print("RESULTADO:", "LIMPIO" if not fallas else " | ".join(fallas))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
