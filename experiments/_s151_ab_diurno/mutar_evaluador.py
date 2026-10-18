# -*- coding: utf-8 -*-
"""Prueba de mutaciones de evaluar_diurno.py: ¿la autoprueba atrapa un evaluador roto a propósito?

POR QUÉ (A110, A116). Que la autoprueba dé todo en verde dice poco si también daría verde con el evaluador roto.
Este script es el equivalente, dentro del repo, del `mutar.py` del verificador con contexto limpio del PR #822
(las siete de entonces, mismos textos de reemplazo, más las seis g3_* de la desviación D2 del pre-registro y
u_sin_recorte_lleno y u_fuera_del_corte, que mutan unir_intentos.py): copia evaluar_diurno.py a un directorio temporal, le aplica
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
import types
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
    # Desviación D2 (2026-10-17): el G3 clasifica cada par con unir_intentos.comparar y el predicado del tablero.
    # Una mutación por categoría, para que cada una importe (A116), más la que se salta el predicado.
    "g3_orden_falla": ('G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")',
                       'G3_ADMITIDAS = ("igual", "tolerancia", "borde", "hotspot_escena")'),
    "g3_borde_falla": ('G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")',
                       'G3_ADMITIDAS = ("igual", "tolerancia", "orden", "hotspot_escena")'),
    "g3_escena_falla": ('G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")',
                        'G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde")'),
    "g3_tolerancia_falla": ('G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")',
                            'G3_ADMITIDAS = ("igual", "orden", "borde", "hotspot_escena")'),
    "g3_distinto_admitido": ('G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")',
                             'G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena", "distinto")'),
    "g3_sin_predicado": ('            malos = set(predicado([(x[1], x[2]) for x in lista], vol))',
                         '            malos = set()'),
    # Verificador del PR #847: la regla de la lista llena vive en unir_intentos.comparar; la mutación se aplica a
    # ESE archivo (tercer elemento) y el evaluador sin tocar la importa.
    "u_sin_recorte_lleno": ('    if conjunto and not (lista_llena(x) and lista_llena(y)):', '    if False:',
                            "unir_intentos.py"),
    # Verificador V2 del PR #847: con el recorte activo, sólo pueden cambiar los píxeles del puesto 100.
    "u_fuera_del_corte": ('    if conjunto and not solo_en_el_corte(x, y):', '    if False:', "unir_intentos.py"),
}


# Los mensajes de las guardas de coherencia de evaluar_diurno.py al importar (tolerancia y campos de proceso).
GUARDAS_DE_IMPORT = ("G3 y unir_intentos con tolerancias distintas",
                     "G3 y unir_intentos excluyen campos de proceso distintos")


def una(nombre):
    src = (AQUI / "evaluar_diurno.py").read_text(encoding="utf-8")
    src = src.replace("AQUI = Path(__file__).resolve().parent", "AQUI = Path(r\"%s\")" % AQUI)
    destino = MUT[nombre][2] if nombre != "ninguna" and len(MUT[nombre]) > 2 else "evaluar_diurno.py"
    tmp = Path(tempfile.mkdtemp(prefix="mutar_diurno_"))
    if destino != "evaluar_diurno.py":
        # el archivo mutado se registra con su nombre corto antes de importar el evaluador, que lo encuentra ahí
        otro = (AQUI / destino).read_text(encoding="utf-8")
        a, b = MUT[nombre][:2]
        if otro.count(a) != 1:
            raise SystemExit("la mutación %s no encuentra su texto exactamente una vez" % nombre)
        # se ejecuta con el __file__ del archivo real: `_predicado` arma la raíz del repo desde ahí
        mo = types.ModuleType(Path(destino).stem)
        mo.__file__ = str(AQUI / destino)
        sys.modules[Path(destino).stem] = mo
        exec(compile(otro.replace(a, b), str(AQUI / destino), "exec"), mo.__dict__)
    elif nombre != "ninguna":
        a, b = MUT[nombre][:2]
        if src.count(a) != 1:
            raise SystemExit("la mutación %s no encuentra su texto exactamente una vez" % nombre)
        src = src.replace(a, b)
    ruta = tmp / "evaluar_diurno.py"
    ruta.write_text(src, encoding="utf-8")
    for p in (str(RAIZ / "scripts"), str(RAIZ), str(AQUI)):
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("evaluar_diurno", ruta)
    m = importlib.util.module_from_spec(spec)
    sys.modules["evaluar_diurno"] = m
    try:
        spec.loader.exec_module(m)
    except AssertionError as e:
        # Desde D2 la mutación «volatiles» la para la guarda de coherencia con unir_intentos.PROCESO al importar,
        # antes de llegar a la autoprueba (el caso 17 ya no puede verla: comparar excluye PROCESO por su cuenta).
        # Sólo cuenta si es ESA guarda (verificador del PR #847): cualquier otra aserción del import es una caída.
        if str(e) not in GUARDAS_DE_IMPORT:
            raise
        sys.__stdout__.write("MUTACION %s rc=3\n   el evaluador mutado no importa: %s\n" % (nombre, e))
        return 3
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
    nombres = ["ninguna"] + list(MUT)

    def correr(nombre):
        return subprocess.run([sys.executable, str(Path(__file__)), nombre], capture_output=True, text=True,
                              encoding="utf-8", env=dict(__import__("os").environ, PYTHONIOENCODING="utf-8"))
    # Cuatro a la vez (cada autoprueba tarda ~10 min; en serie eran más de dos horas). Cada proceso tiene su propio
    # directorio temporal y sólo lee el árbol; la salida se imprime en el orden de la lista.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        salidas = list(ex.map(correr, nombres))
    for nombre, o in zip(nombres, salidas):
        print(o.stdout.rstrip())
        # Sin línea «rc=» el proceso se cayó antes de terminar la autoprueba (D2: así se escondió un KeyError del
        # propio evaluador mutado). Una caída NO cuenta como atrapada: se informa con su error.
        rc = int(o.stdout.split("rc=")[1].split()[0]) if "rc=" in o.stdout else -1
        if rc == -1:
            print("MUTACION %s SE CAYÓ: %s" % (nombre, " | ".join(o.stderr.strip().splitlines()[-3:])))
        bien = (rc == 0) if nombre == "ninguna" else (rc not in (0, -1))
        resumen.append((nombre, rc, bien))
    print("\nRESUMEN")
    for nombre, rc, bien in resumen:
        print("   %-20s rc=%s -> %s" % (nombre, rc, ("autoprueba verde, como debe" if nombre == "ninguna" else "ATRAPADA") if bien
                                         else ("LA AUTOPRUEBA FALLA SIN MUTACION" if nombre == "ninguna" else
                                               "SE CAE (no cuenta)" if rc == -1 else "SOBREVIVE")))
    atrapadas = sum(1 for n, _, b in resumen if b and n != "ninguna")
    print("MUTACIONES ATRAPADAS: %d de %d" % (atrapadas, len(MUT)))
    return 0 if all(b for _, _, b in resumen) else 1


if __name__ == "__main__":
    sys.exit(main())
