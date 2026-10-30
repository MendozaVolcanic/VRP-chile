# -*- coding: utf-8 -*-
"""S169 V375-E: ver en rojo cada aserción nueva de probar_sombra.py rompiendo a mano las reglas nuevas del §11.11.

POR QUÉ. Una aserción que nunca se vio fallar puede estar mirando otra cosa (A116). Esto NO es el nulo de mutaciones
(ese es mutar_sombra.py, una mutación por copia, y no se corre aquí): es una comprobación barata, de cuatro corridas de la
batería, cada una sobre una copia del lector con un GRUPO de reglas rotas a la vez. Las roturas son las mismas
mutaciones de mutar_sombra.py (ids N y V); en cada grupo se eligieron para que no se tapen entre sí. Para cada rotura se
listan las aserciones que la batería da en FALLA; la que se esperaba ver en rojo está en ESPERA.

Uso: python -I ver_en_rojo.py --grupo A|B|C|D|E|F|G|H|I|J|K|L [--salida <archivo>]
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
SOMBRA = RAIZ / "experiments" / "_s168" / "v375e_sombra"

GRUPOS = {
    "A": ["N06", "N07", "N27", "N37", "N38"],
    "B": ["V04", "V05", "V06", "N01", "N05", "N09", "N10", "N15", "N22", "N25", "N28", "N29", "N31", "N32", "N33",
          "N34", "N36"],
    "C": ["V01", "V02", "V03", "N02", "N03", "N08", "N11", "N12", "N14", "N23", "N30", "N35"],
    "E": ["N16", "V06"],   # repetición: en D el test de N16 no era sensible y en B V05 tapaba a V06
    "D": ["N04", "V14", "N13", "N16", "N17", "N18", "N19", "N20", "N21", "N24", "N26", "N39"],
    # ronda 2 (verificador de S169): las reglas de §11.12
    "G": ["R01", "R02", "R04", "R05", "R09", "R12", "R13", "R16", "R18", "R21", "R22"],
    "H": ["R03", "R06", "R10", "R11", "R14", "R17", "R19", "N05"],
    "I": ["R07", "R08", "R15", "N16"],
    "K": ["R20"],   # sola: sin el rechazo, cada corrida que debía rechazarse hace la lectura entera (más de 30 min)
    "L": ["R28"],   # ronda 3 (VL2-04)
    "J": ["R24", "R25", "R26", "R27", "R23", "N05"],   # la base de la ventana (precisión de la coordinadora)
    "F": ["CONTROL_SECCION"],   # VL169-02: tiene que salir con exit 2 (CAÍDA), no 1
}
# la aserción (prefijo del nombre en probar_sombra.py) que tiene que salir en FALLA con cada rotura
ESPERA = {
    "V14": "S1 (VS168-01): desde DESPUÉS", "N07": "main VS168-02: con S7 caído", "N09": "main VS168-02: con S1 caído",
    "N13": "S0 (VS168-04): banco_paridad.py distinto", "N16": "S8 (VS168-04): compara contra",
    "N17": "S8 (VS168-04): un perfil de la vía distinto", "N18": "S8 (VS168-04): el --commit también",
    "N19": "S8 (VS168-04): un record sin régimen", "N20": "S8 (VS168-04): un sha que git no resuelve",
    "N21": "S9 (VS168-05): tabla hasta 1 día", "N23": "S9 y S10 corren con la parada",
    "N24": "S10 (VS168-11): una pasada con alertados y sin distancias cae", "N26": "S4 (VS168-10): radiante a 0,0004",
    "N27": "S6 (VS168-08): sin sustrato (dos noches)", "N37": "main (VS168-14): sin --commit",
    "N39": "S7: la lista de SIN DATO va completa",
    "V02": "(b) sin neg_pub (VS168-08)", "V04": "cableado (VS168-08): P2 PIERDE", "V05": "cableado (VS168-08): la curva",
    "V06": "(d) (VS168-07): un control de la curva de K", "N10": "(a) (VS168-03): una protegida SIN DATO que K publica",
    "N15": "criterios (S8): con la marca de régimen (b)", "N22": "S9 (VS168-05): tabla hasta 1 día",
    "N25": "S10 (VS168-11): en analizar", "N28": "(c) (VS168-06): M SIN SUSTRATO",
    "N29": "VS168-07: los controles de la curva de K se calculan", "N31": "borde mixto (VS168-09): una lejana",
    "N32": "estado_final (VS168-09): la vuelta mixta", "N33": "main (VS168-12): las alertas de MIROVA sin record",
    "N34": "lejanas (VS168-12): far_ocr", "N36": "main (VS168-13)", "N38": "(b) sin neg_pub (VS168-08)",
    "V01": "S6 (VS168-08): en analizar", "V03": "cableado (VS168-08): M EMPEORA",
    "N01": "main (VS168-01): con --hasta posterior", "N02": "VS168-01: el corte que decide es la noche",
    "N03": "VS168-01: antes de la parada (30 y 40)", "N04": "parada (VS168-01): la noche N es la PRIMERA",
    "N05": "VL169-01: con el registro vacío, la guarda de la carpeta", "N06": "main: la lectura que decide sale 0",
    "N08": "main (VS168-02): antes de la parada los controles", "N11": "(a) (VS168-03): una SIN DATO que K calla",
    "N12": "main (VS168-03): la protegida SIN DATO", "N14": "S8 en analizar (VS168-04)",
    "N30": "borde: analizar lista las dos pasadas", "N35": "main (VS168-13)",
    "R01": "S0 (VS168-04): el sello del lector fija", "R02": "S0 (VL169-06): VRP_PROFILE con otro perfil",
    "R03": "S0 (VL169-06): sin VRP_PROFILE", "R04": "S8 (VL169-04): las rutas que compara",
    "R05": "S8 (VL169-03): sólo docstring", "R06": "S8 (VL169-03): sólo docstring",
    "R07": "S8 (VL169-03): un perfil ajeno", "R08": "S8 (VL169-03): un cambio sólo en roi_v750",
    "R09": "S8 (VL169-03 y 04): un cambio en x0", "R10": "S8 (VL169-03 y 04): una grilla ilegible",
    "R11": "S8 (VL169-03): un .py nuevo", "R12": "main (VS168-05 y VL169-07)",
    "R13": "VA168-01: S1 caído, analizar devuelve", "R14": "main (VL169-08)",
    "R15": "main: los contadores de la parada sí salen", "R16": "VL169-01: otra referencia en OTRA carpeta",
    "R17": "VL169-01: si loop/activo no se puede resolver", "R18": "VL169-01: desde otro checkout",
    "R19": "main (VL169-01): la lectura que decide deja una línea", "R20": "VL169-01 (probe_b1b): otra referencia en la MISMA",
    "R21": "VL169-01: una línea ilegible", "R22": "VL169-01: registro_remoto da [] si",
    "R23": "VL169-01: registro_remoto da None",
    "R24": "S8 (base de la ventana): la base es el codigo_sha", "R25": "S8 (base de la ventana): c42ee0eb7 contra la base",
    "R26": "S8 (base de la ventana): sin records de la vía", "R27": "S8 (base de la ventana): si cambia una noche del medio",
    "R28": "main (VL2-04): la lectura que decide no sale por pantalla",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--grupo", required=True, choices=sorted(GRUPOS))
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("mutar_sombra", SOMBRA / "mutar_sombra.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    mut = {m[0]: m for m in M.MUTACIONES}
    mut["CONTROL_SECCION"] = M.CONTROL_SECCION
    src = (SOMBRA / M.LS).read_text(encoding="utf-8")
    for k in GRUPOS[a.grupo]:
        _, viejo, nuevo = mut[k]
        assert src.count(viejo) == 1, (k, src.count(viejo))
        src = src.replace(viejo, nuevo)
    d = SOMBRA.parent / f"_rojo_s169_{a.grupo}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    try:
        (d / M.LS).write_text(src, encoding="utf-8")
        p = subprocess.run([sys.executable, "-I", str(SOMBRA / "probar_sombra.py"), "--dir", str(d)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5400)
    finally:
        shutil.rmtree(d)
    fallas = [x[6:].strip() for x in p.stdout.splitlines() if x.startswith("FALLA")]
    res = [x for x in p.stdout.splitlines() if x.startswith("RESULTADO")]
    out = [f"grupo {a.grupo}: roturas {GRUPOS[a.grupo]}", f"batería: exit {p.returncode} {res}",
           f"stderr (cola): {p.stderr.strip().splitlines()[-1:] if p.stderr.strip() else []}"]
    if a.grupo == "F":
        out.append(f"CONTROL_SECCION: exit {p.returncode} -> {'CAIDA (bien)' if p.returncode == 2 else 'NO ES CAIDA'}; "
                   f"líneas CAE: {[x[:90] for x in p.stdout.splitlines() if x.startswith('CAE')][:3]}")
    for k in [g for g in GRUPOS[a.grupo] if g in ESPERA]:
        vista = any(f.startswith(ESPERA[k]) for f in fallas)
        out.append(f"{k} {'EN ROJO' if vista else 'NO SE VIO'}: «{ESPERA[k]}»")
    out.append("")
    out.append(f"aserciones en FALLA ({len(fallas)}):")
    out += ["  " + f[:160] for f in fallas]
    txt = "\n".join(out) + "\n"
    sys.stdout.buffer.write(txt.encode("utf-8"))
    if a.salida:
        Path(a.salida).write_text(txt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
