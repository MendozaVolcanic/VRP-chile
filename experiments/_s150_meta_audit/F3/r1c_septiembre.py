# -*- coding: utf-8 -*-
"""F3 R1c. Lo mismo que r1 sobre la ventana de S148 (2026-09-01 a 2026-09-20; A118: recall 137 a 135 de 143).
No hay referencia congelada de septiembre en el repo: se usa la copia de hoy (latest_consolidado.csv del
2026-10-09 y el snapshot OCR), asi que L0 puede NO reproducir 143 si la referencia cambio (perdida de filas
del remoto, R5b). Se informa la diferencia en vez de esconderla.
P1/P2: como en r1; el control es que L0 de un n cercano a 143 y que L1 quite filas solo-OCR."""
import io, json, shutil, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI))
import r1_recall_tramo_vara_corregida as r1
tmp = Path(sys.argv[1]); cache = tmp / "tabla_septiembre.json"
if not cache.exists():
    t = tmp / "septiembre"; shutil.rmtree(t, ignore_errors=True); t.mkdir(parents=True)
    runs = ["35548121381", "35558196104"]
    sal = r1.extraer(runs, t)
    dc, db = r1.unir(sal, runs, r1.CONTROL, t / "u"), r1.unir(sal, runs, r1.BRAZO, t / "u")
    subprocess.run([sys.executable, str(r1.PRE / "armar_tabla.py"), "--control", str(dc), "--brazo", str(db),
                    "--cons", str(RAIZ / "latest_consolidado.csv"),
                    "--ocr", str(RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"),
                    "--desde", "2026-09-01", "--hasta", "2026-09-20", "--out", str(cache)], check=True,
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    shutil.rmtree(t, ignore_errors=True)
T = json.loads(cache.read_text(encoding="utf-8"))
for vara, f in r1.VARAS.items():
    pos = [(k, v) for k, v in T["pasadas"].items() if k.split("|")[1] == "VIIRS375" and len(v) == 2 and f(k, v["control"])]
    print("%-14s VIIRS375 positivas %3d | B publica %3d | F publica %3d | solo-OCR SNPP %d" % (
        vara, len(pos), sum(v["control"]["pub"] for k, v in pos), sum(v["brazo"]["pub"] for k, v in pos),
        sum(1 for k, v in pos if v["control"]["alerta_solo_ocr"] and r1.es_snpp(v["control"]))))
    perd = [(k, v["control"]["vrp_ref"], v["control"]["plataforma"], v["control"]["alerta_solo_ocr"]) for k, v in pos if v["control"]["pub"] and not v["brazo"]["pub"]]
    print("     perdidas de F sobre lo que B publica:", perd)
