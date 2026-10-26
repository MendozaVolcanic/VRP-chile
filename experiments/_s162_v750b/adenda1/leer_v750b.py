# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 1: lectura en un solo paso, con la compuerta de la adenda antes del analizador sellado.

POR QUÉ (verificador de la adenda, VAD-01). El compañero `cobertura_cajas_v750b.py` sólo sirve si alguien lo corre y
le hace caso: el analizador sellado no lo lee y, con una protegida sin caja, emite su veredicto sin marca. Este lector
corre primero el compañero y, si cierra, no deja pasar al analizador. No toca el analizador ni cambia ninguna regla.

  compañero SUFICIENTE                  -> corre analizar_v750b.py con los mismos argumentos; sale con su código.
  compañero INSUFICIENTE, cajas ilegibles -> no se lee (el analizador se caería o leería mal); sale 3.
  compañero INSUFICIENTE, sin ilegibles:
      sin --leer-con-faltantes          -> no se lee; relanzar con SOLO las faltantes (§4); sale 3.
      con --leer-con-faltantes MOTIVO   -> corre el analizador y marca su salida con «[LEÍDO CON FALTANTES DE LA
                                           ADENDA: MOTIVO]»; sale 5 (§9: la decisión es de la coordinadora con
                                           Nicolás).
Uso (rutas absolutas; los argumentos son los del analizador, §9):
  python <repo>/experiments/_s162_v750b/adenda1/leer_v750b.py --art <artefactos> --objetivos <...>/objetivos_v750b.json
      --sin-granulo <...>/sin_granulo_v750b.json --evaluador <evaluar_d25.py> --censo-art <...> --censo-objetivos <...>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
COMPANERO = AQUI / "cobertura_cajas_v750b.py"
ANALIZADOR = AQUI.parent / "analizar_v750b.py"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--art", nargs="+", required=True)
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--sin-granulo", required=True)
    ap.add_argument("--leer-con-faltantes", default="")
    ap.add_argument("--salida", default=str(AQUI.parent / "analizar_v750b_salida.txt"))
    a, _resto = ap.parse_known_args(argv)
    c = subprocess.run([sys.executable, str(COMPANERO), "--art", *a.art, "--objetivos", a.objetivos,
                        "--sin-granulo", a.sin_granulo], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    print(c.stdout, end="", flush=True)
    if c.returncode not in (0, 3) or "== cobertura con las cajas:" not in c.stdout:
        print(c.stderr, end="")
        print("== LECTOR: el compañero no dio veredicto de cobertura (se cayó): no se lee")
        return 2
    marca = ""
    if c.returncode == 3:
        m = re.search(r"cajas ilegibles: (\d+)", c.stdout)
        if m is None or int(m.group(1)) > 0:
            print("== LECTOR: hay cajas ilegibles (o el compañero no las informó): no se puede leer ni con faltantes; "
                  "relanzar esas pasadas con SOLO")
            return 3
        if not a.leer_con_faltantes:
            print("== LECTOR: cobertura con las cajas INSUFICIENTE: no se lee; relanzar con SOLO las faltantes (§4) o "
                  "decidir con Nicolás y usar --leer-con-faltantes (§9)")
            return 3
        marca = f"[LEÍDO CON FALTANTES DE LA ADENDA: {a.leer_con_faltantes}] "
    r = subprocess.run([sys.executable, str(ANALIZADOR), *argv], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    sal = r.stdout
    if marca:
        sal = "\n".join(marca + x if x.startswith("== ") else x for x in sal.splitlines()) + "\n"
        try:
            Path(a.salida).write_text(Path(a.salida).read_text(encoding="utf-8").replace("\n== ", "\n" + marca + "== "),
                                      encoding="utf-8")
        except OSError:
            pass
    print(sal, end="")
    print(r.stderr, end="", file=sys.stderr)
    if marca and r.returncode == 0:
        return 5
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
