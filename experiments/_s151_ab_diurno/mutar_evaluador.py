# -*- coding: utf-8 -*-
"""Prueba de mutaciones de evaluar_diurno.py: ¿la autoprueba atrapa un evaluador roto a propósito?

POR QUÉ (A110, A116). Que la autoprueba dé todo en verde dice poco si también daría verde con el evaluador roto.
Este script es el equivalente, dentro del repo, del `mutar.py` del verificador con contexto limpio del PR #822
(mismas siete mutaciones, mismos textos de reemplazo): copia evaluar_diurno.py a un directorio temporal, le aplica
UNA mutación, la registra como el módulo `evaluar_diurno` y corre probar_evaluar_diurno.py contra ella, en un
proceso aparte por mutación. Una mutación queda ATRAPADA si la autoprueba sale con código distinto de 0; «ninguna»
(el evaluador sin tocar) tiene que salir con 0. Salida: mutaciones_salida.txt.

Uso: python mutar_evaluador.py            (todas)
     python mutar_evaluador.py <nombre>   (una, en este proceso)
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MUT = {
    "estrato_unico": ('        e = est[(k[0], k[1])]', '        e = est[("todo", "todo")]'),
    "g2_any": ('    if all(g == "CUMPLE" for g in g2):', '    if any(g == "CUMPLE" for g in g2):'),
    "volatiles": ('VOLATILES = ("updated", "processed_utc", "regimen", "first_processed_utc")', 'VOLATILES = ("updated", "regimen")'),
    "qneg_tabla": ('    neg = [k for k, c in cls.items() if c["ventana"] in ventanas and "neg" in c["pob"]',
                   '    neg = [k for k, c in cls.items() if c["ventana"] in ventanas and "tabla" in c["pob"]'),
    "binom_off1": ('    return float(stats.binom.sf(x - 1, n, p)) if n else None', '    return float(stats.binom.sf(x, n, p)) if n else None'),
    "nulo_angosto": ('    return X / P - (K - X) / N', '    return 0.3 * (X / P - (K - X) / N)'),
    "sin_w2_igual": ('SIN_W2 = ("W3", "W4", "W5", "W6")', 'SIN_W2 = ("W2", "W3", "W4", "W5", "W6")'),
}


def una(nombre):
    src = (AQUI / "evaluar_diurno.py").read_text(encoding="utf-8")
    src = src.replace("AQUI = Path(__file__).resolve().parent", "AQUI = Path(r\"%s\")" % AQUI)
    if nombre != "ninguna":
        a, b = MUT[nombre]
        if src.count(a) != 1:
            raise SystemExit("la mutación %s no encuentra su texto exactamente una vez" % nombre)
        src = src.replace(a, b)
    tmp = Path(tempfile.mkdtemp(prefix="mutar_diurno_"))
    ruta = tmp / "evaluar_diurno.py"
    ruta.write_text(src, encoding="utf-8")
    for p in (str(RAIZ / "scripts"), str(RAIZ), str(AQUI)):
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("evaluar_diurno", ruta)
    m = importlib.util.module_from_spec(spec)
    sys.modules["evaluar_diurno"] = m
    spec.loader.exec_module(m)
    buf, rc = io.StringIO(), 0
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(str(AQUI / "probar_evaluar_diurno.py"), run_name="__main__")
    except SystemExit as e:
        rc = e.code or 0
    lineas = [x for x in buf.getvalue().splitlines() if "AUTOPRUEBA" in x or "[FALLA]" in x]
    sys.__stdout__.write("MUTACION %s rc=%s\n%s\n" % (nombre, rc, "\n".join(lineas)))
    return rc


def main():
    if len(sys.argv) > 1:
        return 0 if una(sys.argv[1]) == 0 else 1
    sys.stdout.reconfigure(encoding="utf-8")
    resumen = []
    for nombre in ["ninguna"] + list(MUT):
        o = subprocess.run([sys.executable, str(Path(__file__)), nombre], capture_output=True, text=True,
                           encoding="utf-8", env=dict(__import__("os").environ, PYTHONIOENCODING="utf-8"))
        print(o.stdout.rstrip())
        rc = int(o.stdout.split("rc=")[1].split()[0]) if "rc=" in o.stdout else -1
        bien = (rc == 0) if nombre == "ninguna" else (rc != 0)
        resumen.append((nombre, rc, bien))
    print("\nRESUMEN")
    for nombre, rc, bien in resumen:
        print("   %-14s rc=%s -> %s" % (nombre, rc, ("autoprueba verde, como debe" if nombre == "ninguna" else "ATRAPADA") if bien
                                       else ("LA AUTOPRUEBA FALLA SIN MUTACION" if nombre == "ninguna" else "SOBREVIVE")))
    atrapadas = sum(1 for n, _, b in resumen if b and n != "ninguna")
    print("MUTACIONES ATRAPADAS: %d de %d" % (atrapadas, len(MUT)))
    return 0 if all(b for _, _, b in resumen) else 1


if __name__ == "__main__":
    sys.exit(main())
