# -*- coding: utf-8 -*-
"""S157 - Robustez del efecto de lado del pareo PASADA (medir_lado_del_barrido.py).

POR QUE. El lado del barrido no es una variable limpia: en una misma noche y plataforma
la pasada vista desde el ESTE es siempre la PRIMERA (la traza de cada orbita siguiente
cruza mas al oeste), asi que "este" tambien significa "~100 min antes" y, segun la
plataforma, otra hora de la noche. Un suelo que se enfria durante la noche, una
plataforma con otra calibracion o un canal de referencia (OCR) que cambio de calidad
(A119) pueden fabricar un "efecto de lado". Cada variante de abajo cambia UNA cosa y
vuelve a medir el efecto con su nulo por permutacion:

  base          celdas volcan x tramo de cenit (lo de medir_lado_del_barrido.py);
  +hora         celdas volcan x tramo x hora UTC entera: E contra O a la misma hora;
  +plataforma   celdas volcan x tramo x plataforma (SNPP / NOAA20 / NOAA21 / Terra / Aqua);
  solo_CONS     la alerta de MIROVA sale de latest.php, sin el canal OCR;
  desde_0613    pasadas desde el 2026-06-13 (A119: OCR con geometria y distancia medidas);
  sin_Isluga    el volcan con el efecto mas grande, fuera;
  tramo<35 / tramo>=35   el efecto deberia crecer con el cenit si es geometrico.

Solo C0 (todo el regimen previo a K), que es donde hay pares; K se informa en el script
principal y no alcanza para esto.
"""
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import medir_lado_del_barrido as m                                  # noqa: E402

OUT = os.path.join(HERE, "resultado_robustez.json")


def alertas_solo_cons():
    pas = defaultdict(dict)
    path = os.path.join(m.ROOT, m.FUENTES_GT[0])
    for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
        nom = (r.get("Volcan") or "").strip()
        vol = next((v for v, al in m.ALIAS.items() if nom in al), None)
        if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
            continue
        b = m.SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
        fecha = r.get("Fecha_Satelite_UTC") or ""
        if not b or not (m.VENTANA[0] <= fecha[:10] <= m.VENTANA[1]):
            continue
        try:
            v = float(r.get("VRP_MW") or 0)
        except ValueError:
            continue
        if v <= 0 or not (3 <= int(fecha[11:13] or 12) <= 9):
            continue
        t = datetime.fromisoformat(fecha[:19])
        pas[(vol, b)][t] = max(pas[(vol, b)].get(t, 0), v)
    return pas


def con_celda(filas, extra):
    """Copia de las filas con la celda ampliada: el 'bin' pasa a ser bin + clave extra."""
    return [dict(f, bin=f["bin"] + "|" + extra(f)) for f in filas]


def main():
    frontera = m.aa.leer_frontera_k()
    pas, noche = m.cargar_alertas()
    regs = m.leer_registros(frontera)
    base = m.parear(regs, pas, noche)["PASADA"]
    cons = m.parear(regs, alertas_solo_cons(), noche)["PASADA"]
    plat = lambda f: f["sensor"].replace("_750", "")                 # noqa: E731
    variantes = {
        "base": lambda fs: fs,
        "+hora": lambda fs: con_celda(fs, lambda f: f["dt"][11:13]),
        "+plataforma": lambda fs: con_celda(fs, plat),
        "desde_0613": lambda fs: [f for f in fs if f["dt"][:10] >= "2026-06-13"],
        "sin_Isluga": lambda fs: [f for f in fs if f["vol"] != "Isluga"],
        "tramo<35": lambda fs: [f for f in fs if abs(f["sz"]) < 35],
        "tramo>=35": lambda fs: [f for f in fs if abs(f["sz"]) >= 35],
    }
    res = {}
    print(f"{'sensor':6s} {'variante':12s} {'n':>5s} {'n_cel':>6s}  "
          f"{'nuestro E/O':>30s}  {'MIROVA E/O':>30s}  {'razon E/O':>30s}")
    for bk in ("v375", "v750"):
        for nom, fn in list(variantes.items()) + [("solo_CONS", None)]:
            src = cons if nom == "solo_CONS" else base
            fs = [f for f in src if "C0" in f["grupos"] and f["bk"] == bk]
            fs = fs if fn is None else fn(fs)
            e = m.con_nulo(fs, m.SEMILLA)
            res[f"{bk}|{nom}"] = e

            def fmt(x):
                if not x:
                    return f"{'s/d':>30s}"
                a, b = x["nulo_ic95"]
                return f"{x['factor_E_sobre_O']:6.3f} [{10**a:5.3f},{10**b:5.3f}] p{x['p_dos_colas']:.3f}"
            print(f"{bk:6s} {nom:12s} {e['n_pares']:5d} {e['n_en_celdas_validas']:6d}  "
                  f"{fmt(e['nuestro'])}  {fmt(e['mirova'])}  {fmt(e['razon'])}")
    # composicion: cuanto se separan E y O en hora y cenit dentro del pareo base
    comp = {}
    for bk in ("v375", "v750"):
        for lado in ("E", "O"):
            fs = [f for f in base if "C0" in f["grupos"] and f["bk"] == bk and f["lado"] == lado]
            horas = sorted(int(f["dt"][11:13]) + int(f["dt"][14:16]) / 60 for f in fs)
            comp[f"{bk}|{lado}"] = {
                "n": len(fs),
                "hora_utc_mediana": round(horas[len(horas) // 2], 2) if horas else None,
                "plataformas": dict(sorted(
                    {p: sum(1 for f in fs if plat(f) == p) for p in {plat(f) for f in fs}}.items())),
            }
    res["composicion"] = comp
    print("\ncomposicion E/O:", json.dumps(comp, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
