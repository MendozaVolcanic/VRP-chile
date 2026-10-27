# -*- coding: utf-8 -*-
"""Punta a punta sin red: el arnes real (medir_record sobre la escena sintetica de la 1.17) escribe filas jsonl con el
formato del job, y el main del evaluador las lee junto a una poblacion de dos records. Prueba la E/S que las pruebas
unitarias no tocan: union poblacion-arnes por (volcan, hora), cabecera y procedencia, control de geometria (el record de
control S151 falta: tiene que dar INDECIDIBLE, no CUMPLE) y la escritura de resultado_mxd03.json.
Uso: python probar_punta_a_punta.py   (sale 1 si algo falla)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import probar_probe_mxd03_ab as T  # noqa: E402


def main():
    pres, aus, _ = T.correr()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        recs = []
        for k, (r, dt) in enumerate(((pres, "2026-03-14 07:05"), (aus, "2026-03-15 07:05"))):
            r = dict(r, tipo="record", estado="ok", dt=dt, nulo_geo_crater_km=0.0, lab="neg_limpio")
            recs.append(r)
        pob = {"checkout": "x", "tol_s": 120, "referencia": {}, "partes": [["A", "B"]],
               "granulos": [{"clave": "A", "records": [dict(T.fila_pob(), dt="2026-03-14 07:05", lab="neg_limpio",
                                                            pub_guardada=1, partida=False, hermanos_lab=[],
                                                            codigo_sha="abc", vrp_mirova=None)]},
                            {"clave": "B", "records": [dict(T.fila_pob(), dt="2026-03-15 07:05", lab="neg_limpio",
                                                            pub_guardada=0, partida=False, hermanos_lab=[],
                                                            codigo_sha="abc", vrp_mirova=None)]}]}
        (d / "poblacion.json").write_text(json.dumps(pob), encoding="utf-8")
        with open(d / "ab_parte00.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"tipo": "cabecera", "parte": 0, "commit": "c1"}) + "\n")
            for r in recs:
                fh.write(json.dumps(r, default=str) + "\n")
        p = subprocess.run([sys.executable, str(AQUI / "evaluar_mxd03.py"), "--art", str(d), "--poblacion",
                            str(d / "poblacion.json")], capture_output=True, text=True, encoding="utf-8")
        print(p.stdout[-2500:], p.stderr[-1500:])
        fallas = []
        if p.returncode != 0:
            fallas.append("el evaluador salio con %d" % p.returncode)
        res = json.loads((d / "resultado_mxd03.json").read_text(encoding="utf-8")) if (d / "resultado_mxd03.json").exists() else {}
        if res.get("veredicto") != "INDECIDIBLE":
            fallas.append("sin control S151 el veredicto tiene que ser INDECIDIBLE, dio %s" % res.get("veredicto"))
        if (res.get("controles", {}).get("geometria") or {}).get("estado") != "INDECIDIBLE":
            fallas.append("control de geometria no marco la falta del granulo S151")
        if res.get("controles", {}).get("cobertura", {}).get("estado") != "OK":
            fallas.append("cobertura no OK con los dos records presentes")
        if (res.get("controles", {}).get("union") or {}).get("estado") != "OK":
            fallas.append("la union poblacion-arnes marco diferencias que no hay")
        if res.get("p2", {}).get("delta_x") != -1:
            fallas.append("P2 delta_x esperado -1 (X apaga el negativo que K publica), dio %s" % res.get("p2", {}).get("delta_x"))
    print("FALLAS:" if fallas else "OK punta a punta", *fallas, sep="\n  ")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
