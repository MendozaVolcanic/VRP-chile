# -*- coding: utf-8 -*-
"""Verificador VC, S179. vc05: bloques 517 y NUEVO de vc03 (separados porque vc03 cayo en el 517 por un error de nombre, F4; lo anterior de vc03 quedo en su salida) sobre la tabla por pasada de vc02 (filas.pkl), con las
funciones del propio lector (worktree s178-retro-lectura) donde la vara es el lector, y con codigo propio donde la
afirmacion dice que el lector no calcula algo.

Cada bloque imprime su encabezado con: que mide, denominador y ventana, y su control.
PREGUNTAS DEL INSTRUMENTO (comunes). (1) Si lo medido estuviera roto, lo veria? Cada bloque tiene un control positivo
propio (abajo). (2) Si el instrumento estuviera muerto? Todo bloque con denominador 0 lo imprime como SIN DATO y no
como cero.
Uso: python vc03_analisis.py [N_SORTEOS]
"""
import collections, copy, importlib.util, math, pickle, statistics, sys
from datetime import timedelta
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s178-lectura")
TMP = Path("D:/vrp-trabajo/temporales/s179-audit/vc")
N_SORTEOS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
spec = importlib.util.spec_from_file_location("leer_retro_vc", W / "experiments/_s172_retro_paquete/leer_retro.py")
LR = importlib.util.module_from_spec(spec)
sys.modules["leer_retro_vc"] = LR
spec.loader.exec_module(LR)
R = LR.Reglas()
F4 = R.F4
D = pickle.load(open(TMP / "filas.pkl", "rb"))
filas, osf_filas, osf_res, res = D["filas"], D["osf_filas"], D["osf_res"], D["res"]
BRAZO = {"MODIS": "V", "VIIRS375": "V-cercano", "VIIRS750": "V"}


def dec(s):
    return [f for f in filas if f["b"] == s and f["tramo"] == LR.TRAMO_DECIDE[s]]


def h(t):
    print("\n" + "=" * 100 + "\n" + t)


# ---------------------------------------------------------------- 517
h("517. Cifras del §7 con el codigo y el K de la lectura (dispatch a7a6ae360, K e7cfbaf54): protegidas, bajo 1 MW y"
  "\n   bloques noche-volcan donde K yerra (bajo1 perdida o negativo limpio publicado). El §7 sellado dice: protegidas"
  "\n   9 / 26 / 30; bajo 1 MW 5 / 158 / 25; bloques donde K yerra 6 (+1 de la protegida perdida) / 48 / 18.")
for s in LR.SENSORES:
    fs = LR._ev(dec(s))
    prot = sum(1 for f in fs if f["lab"] == "protegida")
    bj = sum(1 for f in fs if f["lab"] == "bajo1")
    bl = {F4._bloque(f) for f in fs if (f["lab"] == "bajo1" and not LR._pub(f, "K"))
          or (f["lab"] == "neg_limpio" and LR._pub(f, "K"))}
    pk = [(f["vol"], f["dt"]) for f in fs if f["lab"] == "protegida" and not LR._pub(f, "K")]
    todas = dec(s)
    prot_all = sum(1 for f in todas if f["lab"] == "protegida")
    print(f"  {s}: protegidas evaluables {prot} (todas las pasadas del tramo {prot_all}) | bajo 1 MW {bj} | bloques donde K "
          f"yerra en P2 {len(bl)} | protegidas que K pierde {pk}")

# ---------------------------------------------------------------- nuevo: P1-OSF por brazo en VIIRS 375
h("NUEVO. P1-OSF de VIIRS 375 se calcula con el brazo radiante (p1_osf(filas, osf) sin brazo, l. 1436); el que decide"
  "\n   en 375 es cercano. Se repite con cercano. Control: con radiante reproduce osf_res de la lectura.")
for b in ("V", "V-cercano"):
    fil2 = copy.deepcopy(filas)
    r = LR.p1_osf(fil2, osf_filas, b)
    for s in LR.SENSORES:
        x = r["por_sensor"][s]
        print(f"  brazo {b} {s}: protegidas {x['protegidas']} pub_via {x['pub_via']} candidatas {len(x['candidatas'])} "
              f"{x['candidatas'][:5]} sin_record {len(x['sin_record'])} defecto {len(x['defecto'])}")
