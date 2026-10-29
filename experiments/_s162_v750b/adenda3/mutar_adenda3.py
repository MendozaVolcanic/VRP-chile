# -*- coding: utf-8 -*-
"""Nulo de `probar_adenda3.py`: mutaciones de una línea del lector de la adenda 3 (`leer_n3_v750b.py`).

POR QUÉ (S156, A110). Una batería que pasa no dice nada si tampoco falla cuando la regla se deshace. Cada mutación es
una copia del lector con UNA línea cambiada y cuenta como atrapada sólo si la batería sale 1 con «FALLAS» (sale 2 si
alguna escena se cayó con traza, y eso no es atrapar). La identidad tiene que pasar y el control que se cae tiene que
salir CAÍDA. Las copias viven al lado del lector (su ruta del analizador sellado es relativa a su carpeta) y se borran
al terminar cada una: son temporales que crea y consume este mismo proceso.
Sin atrapar, declaradas por equivalentes en toda escena posible: quitar el «protegida» de `no_veta_n3` (la función sólo
se consulta sobre etiquetas «prot», que ya exigen protegida) y listar con el canal que decide en vez de «todo» (una
pasada sin alerta de la tabla sólo es etiqueta en O, donde los dos canales coinciden).
Uso: python mutar_adenda3.py --evaluador <evaluar_d25.py del tag s161-d25-lectura> --dest <carpeta temporal>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LECTOR = "leer_n3_v750b.py"
MUT = [
    ("identidad", None, None, "PASA"),
    ("A1 el hito incluye el 2026-10-09", 'and o["hora_utc"][:10] < HITO_N3)', 'and o["hora_utc"][:10] <= HITO_N3)',
     "ATRAPADA"),
    ("A2 cualquier plataforma", ' and o.get("sensor") == SENSOR_N3\n', "\n", "ATRAPADA"),
    ("A3 aunque la tabla tenga alerta", ' and not o.get("alerta_tabla")', "", "ATRAPADA"),
    ("A4 hito corrido al 2026-09-01", 'HITO_N3 = "2026-10-09"', 'HITO_N3 = "2026-09-01"', "ATRAPADA"),
    ("A5 sensor de la banda I", 'SENSOR_N3 = "VIIRS_SNPP_750"', 'SENSOR_N3 = "VIIRS_SNPP"', "ATRAPADA"),
    ("A6 la N-3 vuelve a vetar", "     '                if no_veta_n3(o):\\n'", "     '                if False:\\n'",
     "ATRAPADA"),
    ("A7 sin el total de P1", """     '                m["P1_todas"] += 1\\n'\n""", "", "ATRAPADA"),
    ("A8 la lista sin pedir etiqueta", ' and etiqueta(obj[i], "todo") == "prot"]', "]", "ATRAPADA"),
    ("A9 elegibles informativos con el P1 que veta", """metricas(b, "TO", "decide")["P1_todas"] == 0""",
     """metricas(b, "TO", "decide")["P1"] == 0""", "ATRAPADA"),
    ("A10 acepta cualquier analizador", "    if sha_lf(ruta) != SHA_ANALIZADOR_LF:", "    if False:", "ATRAPADA"),
    ("A11 el veredicto no dice que es el de la adenda",
     """     '    pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo}) [con la adenda 3, regla N-3]")\\n'""",
     """     '    pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo})")\\n'""", "ATRAPADA"),
    ("A12 la lista aparte no se imprime", "    for i in n3:\\n'", "    for i in []:\\n'", "ATRAPADA"),
    ("control que se cae", "    ruta = ANALIZADOR\n", '    raise RuntimeError("control: el lector se cae")\n', "CAÍDA"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--dest", required=True, type=Path)
    a = ap.parse_args()
    malas = 0
    src = (AQUI / LECTOR).read_text(encoding="utf-8")
    for nombre, viejo, nuevo, espera in MUT:
        if viejo is not None and src.count(viejo) != 1:
            print(f"{nombre}: la línea a mutar aparece {src.count(viejo)} veces, no 1: MUTACIÓN INVÁLIDA", flush=True)
            malas += 1
            continue
        copia = AQUI / f"_mut_{re.sub(r'[^A-Za-z0-9]+', '_', nombre)}.py"
        copia.write_text(src if viejo is None else src.replace(viejo, nuevo), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(AQUI / "probar_adenda3.py"), "--lector", str(copia),
                                "--evaluador", a.evaluador, "--dest", str(a.dest / copia.stem)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        finally:
            copia.unlink()
        out = r.stdout + r.stderr
        if r.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in out:
            estado = "PASA"
        elif r.returncode == 2 and "CAÍDA DEL LECTOR" in out:
            estado = "CAÍDA"
        elif r.returncode == 1 and "== PRUEBAS: FALLAS" in out:
            estado = "ATRAPADA"
        else:
            estado = f"OTRA (salida {r.returncode})"
        quien = re.findall(r"^(N\d) .*\| FALLA", out, re.M)
        print(f"{nombre}: {estado} (se espera {espera})" + (f" | escenas que fallan {quien}" if quien else ""),
              flush=True)
        malas += estado != espera
    n_mut = sum(1 for m in MUT if m[3] == "ATRAPADA")
    print(f"== mutaciones: {n_mut} que deben quedar atrapadas; "
          + ("TODAS COMO SE ESPERA, con identidad y control" if not malas else f"{malas} NO COMO SE ESPERA"))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
