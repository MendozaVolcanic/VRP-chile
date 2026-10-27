# -*- coding: utf-8 -*-
"""Verificador de D-45: mutaciones PROPIAS que el corredor del implementador (signos_p2/mutar_signos_p2.py) no tiene.
Reusa su funcion `una` (copia del evaluador en experiments/_mut_<id>/, pytest con JUnit, clasificacion por tipo de
falla) para que la definicion de ATRAPADA sea la misma de la adenda §5: alguna prueba falla por aserción y ninguna por
otra excepcion ni error. Corre en serie, con un control sin mutar antes.

  vA  las sumas de bloque en orden INVERSO de clave: con B <= 20 no cambia nada (exacto); con B >= 21 cambia el
      resultado de los sorteos (medido en verif_matematica.py: 651 contra 697 de 10.001). La adenda no fija el orden.
      ¿Lo fija alguna prueba?
  vE  la cola de GANA con «menor estricto» (v < neto) en el exacto: la adenda dice «menor o igual».
  vF  la cola de PIERDE con «mayor estricto» en el exacto.
  vG  el +1 solo en el numerador de GANA (PIERDE y dos colas sin el +1) en los sorteos.
  vH  SIN SUSTRATO decidido sobre los bloques de suma no nula en vez de B (variante de la mutacion 5 en la regla).
Salida: mutaciones_propias_salida.json y este mismo texto por pantalla.
"""
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "signos_p2"))
import mutar_signos_p2 as M  # noqa: E402

MIAS = [
    ("vA", "orden inverso de las sumas de bloque (cambia los sorteos con B >= 21)",
     [("    sumas = [por_bloque[b] for b in sorted(por_bloque)]    #",
       "    sumas = [por_bloque[b] for b in sorted(por_bloque, reverse=True)]    #")]),
    ("vE", "cola de GANA con menor estricto (exacto)",
     [("k_gana = sum(k for v, k in dist.items() if v <= neto)", "k_gana = sum(k for v, k in dist.items() if v < neto)")]),
    ("vF", "cola de PIERDE con mayor estricto (exacto)",
     [("k_pierde = sum(k for v, k in dist.items() if v >= neto)", "k_pierde = sum(k for v, k in dist.items() if v > neto)")]),
    ("vG", "el +1 solo en GANA (sorteos)",
     [('"gana": [1 + m_gana, den], "pierde": [1 + m_pierde, den], "dos_colas": [1 + m_dos, den]',
       '"gana": [1 + m_gana, den], "pierde": [m_pierde, den], "dos_colas": [m_dos, den]')]),
    ("vH", "SIN SUSTRATO sobre los bloques de suma no nula",
     [("    return regla_signos_p2(neto, B, pr), det\n",
       "    return regla_signos_p2(neto, det[\"bloques_suma_no_nula\"], pr), det\n")]),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    src = (M.ORIG / "evaluar_d25.py").read_text(encoding="utf-8")
    for mid, _, cambios in MIAS:
        for a, _b in cambios:
            assert src.count(a) == 1, (mid, src.count(a), a[:80])
    res = {}
    t0 = time.time()
    ctrl = M.una("vctrl", [])
    ok = ctrl["n"] > 0 and not (ctrl["aser"] or ctrl["otras"] or ctrl["errores"])
    print("control sin mutar: %s (%d pruebas, %ds)" % ("OK 0 fallas" if ok else "FALLA", ctrl["n"], ctrl["seg"]), flush=True)
    res["control"] = dict(ctrl, ok=ok)
    for mid, nombre, cambios in MIAS:
        r = M.una(mid, cambios)
        atrapada = bool(r["aser"]) and not r["otras"] and not r["errores"]
        estado = "ATRAPADA" if atrapada else ("CAE (no cuenta)" if (r["otras"] or r["errores"]) else "NO ATRAPADA")
        res[mid] = dict(r, nombre=nombre, estado=estado)
        print("%-4s %-70s %s (%d pruebas, %d por asercion, %d otra, %d err, %ds)" % (
            mid, nombre, estado, r["n"], len(r["aser"]), len(r["otras"]), len(r["errores"]), r["seg"]), flush=True)
        for t, m in r["aser"][:5]:
            print("      asercion: %s" % t)
        for t, m in r["otras"] + r["errores"]:
            print("      NO CUENTA: %s %s" % (t, m))
    print("total %ds" % (time.time() - t0))
    (AQUI / "mutaciones_propias_salida.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
