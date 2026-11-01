# -*- coding: utf-8 -*-
"""Verificador S162 MxD03, hallazgo propio sobre evaluar_mxd03.cargar(): lee `**/ab_parte*.jsonl` recursivo y no
deduplica (vol, dt). El humo escribe ab_parte00.jsonl y la parte 0 de la tanda 1 tambien; si los artefactos de las
cuatro ramas se descargan a una misma carpeta, las filas del humo entran dos veces y P2 las cuenta dos veces.

Pregunta 1: si el defecto existe, con la misma fila en dos subcarpetas delta_x pasa de -1 a -2 (la fila sintetica de
punta a punta donde K publica y X no). Pregunta 2: control: con una sola copia da -1 (el instrumento distingue).
Reusa la fabrica de probar_punta_a_punta (escena sintetica de la 1.17 por el arnes real).
Uso: cd experiments/_s162_mxd03 && PYTHONIOENCODING=utf-8 python verificador/verif_duplicados_artefactos.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
AB = AQUI.parent
sys.path.insert(0, str(AB))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import probar_probe_mxd03_ab as T  # noqa: E402


def correr(copias):
    pres, aus, _ = T.correr()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        recs = []
        for r, dt in ((pres, "2026-03-14 07:05"), (aus, "2026-03-15 07:05")):
            recs.append(dict(r, tipo="record", estado="ok", dt=dt, nulo_geo_crater_km=0.0, lab="neg_limpio"))
        pob = {"checkout": "x", "tol_s": 120, "referencia": {}, "partes": [["A", "B"]],
               "granulos": [{"clave": "A", "records": [dict(T.fila_pob(), dt="2026-03-14 07:05", lab="neg_limpio",
                                                            pub_guardada=1, partida=False, hermanos_lab=[],
                                                            codigo_sha="abc", vrp_mirova=None)]},
                            {"clave": "B", "records": [dict(T.fila_pob(), dt="2026-03-15 07:05", lab="neg_limpio",
                                                            pub_guardada=0, partida=False, hermanos_lab=[],
                                                            codigo_sha="abc", vrp_mirova=None)]}]}
        (d / "poblacion.json").write_text(json.dumps(pob), encoding="utf-8")
        for k in range(copias):
            sub = d / ("s162-mxd03-humo-parte-0" if k == 0 else "s162-mxd03-t1-parte-0")
            sub.mkdir()
            with open(sub / "ab_parte00.jsonl", "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"tipo": "cabecera", "parte": 0, "commit": "c1"}) + "\n")
                for r in recs:
                    fh.write(json.dumps(r, default=str) + "\n")
        p = subprocess.run([sys.executable, str(AB / "evaluar_mxd03.py"), "--art", str(d), "--poblacion",
                            str(d / "poblacion.json")], capture_output=True, text=True, encoding="utf-8")
        res = json.loads((d / "resultado_mxd03.json").read_text(encoding="utf-8"))
        return res["p2"]["delta_x"], res["p2"]["n"], res["controles"]["cobertura"]["estado"], res["controles"]["union"]["estado"], res["veredicto"]


def main():
    uno = correr(1)
    dos = correr(2)
    print("una copia : delta_x=%s n=%s cobertura=%s union=%s veredicto=%s" % uno)
    print("dos copias: delta_x=%s n=%s cobertura=%s union=%s veredicto=%s" % dos)
    dup = dos[0] == 2 * uno[0] and dos[1] == 2 * uno[1]
    print("RESULTADO:", "DEFECTO CONFIRMADO: las filas duplicadas se cuentan dos veces y ningun control lo acusa"
          if dup else "no se reproduce la duplicacion")


if __name__ == "__main__":
    main()
