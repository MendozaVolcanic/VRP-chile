# -*- coding: utf-8 -*-
"""Verificador de la adenda K, pregunta 2: caminos por los que un brazo que NO es K pasaria el cableado de
evaluar_diurno.py con --base k. Solo lee el evaluador; escribe en un directorio temporal propio.
Uso: python -I p2_caminos_cableado.py
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import evaluar_diurno as ED  # noqa: E402

K = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True}
C0 = {"ENABLE_TEST1_PATH": True, "ENABLE_TESTS_23_PROSE_BRANCH": False, "ENABLE_MODIS_B22_PRIMARY": False}
KC, KD = "_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on"


def armar(tmp, flags_por_brazo, con_log=True, records=None):
    if tmp.exists():
        shutil.rmtree(tmp)
    for n, diurno in (("control", False), ("diurno", True)):
        b = ED.BRAZOS[n]
        (tmp / b).mkdir(parents=True)
        (tmp / b / "Lascar.json").write_text(json.dumps({"volcano": "Lascar", "records": records or []}), encoding="utf-8")
        if con_log:
            (tmp / "logs").mkdir(exist_ok=True)
            fl = dict(PROFILE_NAME=b, DATA_SUBDIR=b, ENABLE_DAYTIME_VIIRS=diurno, ENABLE_DAYTIME_MODIS=False)
            fl.update(flags_por_brazo[n])
            (tmp / "logs" / ("%s_Lascar.log" % b)).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n", encoding="utf-8")


def cab(tmp):
    return ED.cableado([str(tmp)], [str(tmp / "logs")], "control") + ED.cableado([str(tmp)], [str(tmp / "logs")], "diurno")


def main():
    base = Path(tempfile.mkdtemp(prefix="verif_adenda_k_"))
    try:
        filas = []
        ED.configurar_brazos(KC, KD, "k")
        casos = [
            ("a. los dos brazos K (base)", {"control": K, "diurno": K}, True, None, "OK"),
            ("b. control con conectiva min (PROSE False)", {"control": dict(K, ENABLE_TESTS_23_PROSE_BRANCH=False), "diurno": K}, True, None, "ROTO"),
            ("c. diurno con banda 21 MODIS (B22 False)", {"control": K, "diurno": dict(K, ENABLE_MODIS_B22_PRIMARY=False)}, True, None, "ROTO"),
            ("d. log de workflow viejo sin las claves de K", {"control": {}, "diurno": {}}, True, None, "ROTO"),
            ("e. los dos brazos C0 completos", {"control": C0, "diurno": C0}, True, None, "ROTO"),
            ("f. JSON sin log (raiz de unir_ventana.py)", {"control": K, "diurno": K}, False, None, "ROTO"),
            ("g. log K, pero los records traen test1_roi y triggered_test1 (record escrito por otro job)",
             {"control": K, "diurno": K}, True,
             [{"datetime_utc": "2026-06-24 17:36", "sensor": "VIIRS_SNPP", "final_hotspot_source": "test1_roi",
               "triggered_test1": True, "regimen": {"perfil": KD, "codigo_sha": "c0c0c0c"}}], "?"),
        ]
        for nom, flags, con_log, recs, esperado in casos:
            d = base / nom[0]
            armar(d, flags, con_log, recs)
            p = cab(d)
            filas.append((nom, esperado, "OK" if not p else "ROTO", p[:2]))
        # h. el mismo caso e (todo C0) evaluado SIN --base k (base por defecto c0) y con los nombres de K
        ED.configurar_brazos(KC, KD, "c0")
        d = base / "h"
        armar(d, {"control": C0, "diurno": C0})
        p = cab(d)
        filas.append(("h. todo C0 con --brazos K pero sin --base k (default c0)", "?", "OK" if not p else "ROTO", p[:2]))
        # i. el parser: --base por defecto
        a = ED.parser().parse_args(["--raiz", "x", "--brazos", "%s,%s" % (KC, KD)])
        filas.append(("i. parser con --brazos K y sin --base: base =", "?", a.base, []))
        for nom, esp, obt, det in filas:
            print("%-95s esperado %-4s obtenido %-5s %s" % (nom, esp, obt, det))
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
