# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 3: la regla N-3 sobre el analizador sellado. ESTE lector da el veredicto de V750-B.

POR QUÉ. Nicolás decidió (S166, para el auto-audit #924; S167, 2026-10-29, «Sí a todo», programa §12.5 punto 5, para
V750-B) que las protegidas que existen sólo por el OCR de Suomi NPP antes del 2026-10-09 se informan aparte y no
deciden, igual que en V375-E §8.13 y V750-A §6 ter. Físicamente: esas alertas salen de leer con OCR la imagen por
volcán de MIROVA, y en Suomi NPP ese canal llegó a traer la imagen de otra pasada (reference_ocr_imagen_de_otra_pasada,
Mirova-v1#20); hasta el 2026-10-09 no hay cómo saber si la protegida es de esa pasada. Una ROI no se debe descartar
por perder una alerta que quizás no estaba ahí.

Qué cambia, y nada más (adenda 3 §2):
  una protegida SIN alerta de la tabla (`alerta_tabla` falso), de Suomi NPP (`sensor == "VIIRS_SNPP_750"`) y con
  `hora_utc` anterior al 2026-10-09 no suma al P1 que veta (§5, §6.1). Se lista aparte por nombre, con qué brazos la
  publican, y cada línea de métricas imprime el P1 que veta al lado del que las cuenta todas. Lo demás (controles,
  cobertura, E, P2, la regla §6.2 y §6.3) es el analizador sellado, sin tocar.

Cómo, sin tocar lo sellado: se lee `analizar_v750b.py`, se exige su sha256 del tag `s162-v750b-sellado` (fin de línea
normalizado a LF), se aplican cinco reemplazos de texto exactos (cada uno tiene que aparecer una sola vez en el
original; si no, el lector se niega) y se ejecuta el resultado con el `__file__` del sellado, así que sus rutas,
el oráculo, el predicado del tablero con node y la prueba de signos son los mismos. El analizador sellado se puede
seguir corriendo tal cual: su salida es la regla sin N-3, que sólo informa.

La compuerta de la adenda 1 va primero (VA3-01 del verificador corto). La lectura sellada es
`adenda1/leer_v750b.py` (adenda 2 §8): corre el compañero `cobertura_cajas_v750b.py` y, si la cobertura con las cajas
no cierra, no deja pasar al analizador (salida 3; con `--leer-con-faltantes` marca y sigue). Este lector carga ese
lector sellado tal cual (sha256 del tag, igual que su compañero) y le cambia una sola cosa: el analizador que llama es
este archivo en su paso de analizador (`--n3-paso-analizador`), que corre el analizador sellado con la adenda 3. Así
la compuerta, sus salidas y su marca son las selladas, sin copiarlas.

Uso: los mismos argumentos que `adenda1/leer_v750b.py` (`--art`, `--objetivos`, `--evaluador`, `--sin-granulo`,
`--censo-art`, `--censo-objetivos`, `--leer-con-faltantes`, ...). `--salida` por defecto va a esta carpeta, no a la del
sellado.
Salidas: las de `leer_v750b.py` (0, 3, 4, 5); 2 si el analizador o el lector de la adenda 1 no son los sellados, si un
reemplazo no calza o si el compañero se cae.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ANALIZADOR = AQUI.parent / "analizar_v750b.py"
LECTOR_A1 = AQUI.parent / "adenda1" / "leer_v750b.py"
COMPANERO_A1 = AQUI.parent / "adenda1" / "cobertura_cajas_v750b.py"
SHA_ANALIZADOR_LF = "83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392"   # tag s162-v750b-sellado
SHA_LECTOR_A1_LF = "11e0ee91fe77d6685e2fd3ac06ffbe18cb237fadae8d5d7e73759199689b52e2"    # tag s162-v750b-adenda2-sellada
SHA_COMPANERO_A1_LF = "f250a926ae26435ba5101566b4f90abcf9a1e98d23de4f7a94ba95992fb1d70d"  # ídem
PASO = "--n3-paso-analizador"
SENSOR_N3 = "VIIRS_SNPP_750"
HITO_N3 = "2026-10-09"

# lo que se agrega al nivel del módulo, antes de main()
DEFINICION = f'''
SENSOR_N3 = "{SENSOR_N3}"
HITO_N3 = "{HITO_N3}"


def no_veta_n3(o):
    """Adenda 3 (N-3): protegida sólo del OCR (sin alerta de la tabla) de Suomi NPP anterior al 2026-10-09."""
    return (bool(o.get("protegida")) and not o.get("alerta_tabla") and o.get("sensor") == SENSOR_N3
            and o["hora_utc"][:10] < HITO_N3)

'''

REEMPLAZOS = (
    # 1. el veto: la protegida N-3 perdida no suma al P1 que veta; se cuenta aparte y en el total
    ('            if e == "prot" and not pb:\n                m["P1"] += 1\n',
     '            if e == "prot" and not pb:\n'
     '                m["P1_todas"] += 1\n'
     '                if no_veta_n3(o):\n'
     '                    m["P1_n3"] += 1\n'
     '                else:\n'
     '                    m["P1"] += 1\n'),
    # 2. cada línea de métricas lleva el P1 que veta al lado del que las cuenta todas
    ("f\"   {b:3s} prot {m['n_prot']:4d} P1 {m['P1']:3d} | P1b abajo",
     "f\"   {b:3s} prot {m['n_prot']:4d} P1 {m['P1']:3d} (que veta; todas {m['P1_todas']}, N-3 aparte "
     "{m['P1_n3']}) | P1b abajo"),
    # 3. después de los elegibles: la lista aparte y los elegibles que daría la regla contando todas
    ('    pr("\\n== §6.1 elegibles:", elegibles)\n',
     '    pr("\\n== §6.1 elegibles:", elegibles)\n'
     '    n3 = [i for i in oks if no_veta_n3(obj[i]) and etiqueta(obj[i], "todo") == "prot"]\n'
     '    pr("== adenda 3 (N-3), protegidas informadas aparte (sólo OCR, Suomi NPP, antes del 2026-10-09; no vetan):",\n'
     '       len(n3))\n'
     '    for i in n3:\n'
     '        pr(f"   {obj[i][\'volcan\']} {obj[i][\'hora_utc\']} ventana {\'O\' if obj[i][\'hora_utc\'] >= FRONTERA_OCR else \'T\'}"\n'
     '           f" | publican {[b for b in CANDIDATOS if pub(i, b)]} | no publican {[b for b in CANDIDATOS if not pub(i, b)]}")\n'
     '    elig_todas = [b for b in CANDIDATOS if metricas(b, "TO", "decide")["P1_todas"] == 0\n'
     '                  and metricas(b, "O", "tabla")["P1_todas"] == 0]\n'
     '    pr("   elegibles contando también las N-3 (regla sin la adenda 3; sólo informa):", elig_todas)\n'),
    # 4. el veredicto dice que es el de la adenda 3
    ('    pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo})")\n',
     '    pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo}) [con la adenda 3, regla N-3]")\n'),
    # 5. el encabezado de la salida
    ('    # ---------------------------------------------------------------- cobertura (§4, §9)\n',
     '    pr("== V750-B leído con la adenda 3 (regla N-3) sobre el analizador sellado (sha256 LF "\n'
     f'       "{SHA_ANALIZADOR_LF[:12]}...)")\n'
     '    # ---------------------------------------------------------------- cobertura (§4, §9)\n'),
)


def sha_lf(ruta):
    return hashlib.sha256(Path(ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def fuente_con_n3(ruta):
    """Texto del analizador con la adenda 3, o un motivo de rechazo (str que empieza con 'RECHAZO')."""
    if sha_lf(ruta) != SHA_ANALIZADOR_LF:
        return "RECHAZO: el analizador no es el sellado (sha256 distinto del tag s162-v750b-sellado)"
    src = Path(ruta).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    for k, (viejo, nuevo) in enumerate(REEMPLAZOS, 1):
        if src.count(viejo) != 1:
            return f"RECHAZO: el reemplazo {k} aparece {src.count(viejo)} veces en el analizador, no 1"
        src = src.replace(viejo, nuevo)
    ancla = "\ndef main():\n"
    if src.count(ancla) != 1:
        return "RECHAZO: no hay un único main() donde anclar la definición de N-3"
    return src.replace(ancla, DEFINICION + ancla)


def paso_analizador(argv):
    """El analizador sellado con la adenda 3. Lo llama el lector de la adenda 1, después de su compuerta."""
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--analizador", default=str(ANALIZADOR))   # sólo para las pruebas: uno ajeno se rechaza
    a, argv = ap.parse_known_args(argv)
    src = fuente_con_n3(a.analizador)
    if src.startswith("RECHAZO"):
        print(src, flush=True)
        return 2
    # las rutas del analizador (scripts, oráculo) son siempre las de la carpeta sellada (VA3-04)
    ns = {"__name__": "analizar_v750b_con_n3", "__file__": str(ANALIZADOR)}
    exec(compile(src, str(ANALIZADOR), "exec"), ns)
    sys.argv = [str(ANALIZADOR)] + argv
    return ns["main"]()


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if PASO in argv:
        return paso_analizador([x for x in argv if x != PASO])
    for ruta, sha, que in ((LECTOR_A1, SHA_LECTOR_A1_LF, "el lector de la adenda 1"),
                           (COMPANERO_A1, SHA_COMPANERO_A1_LF, "el compañero de cobertura de la adenda 1")):
        if sha_lf(ruta) != sha:
            print(f"RECHAZO: {que} no es el sellado (sha256 distinto del tag s162-v750b-adenda2-sellada)", flush=True)
            return 2
    # VA3-02: `--salida` se reconoce como lo haría argparse (también `--salida=ruta` y abreviaciones)
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--salida", default=None)
    if ap.parse_known_args(argv)[0].salida is None:
        argv = argv + ["--salida", str(AQUI / "leer_n3_v750b_salida.txt")]
    spec = importlib.util.spec_from_file_location("leer_v750b_sellado", LECTOR_A1)
    a1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a1)
    a1.ANALIZADOR = Path(__file__).resolve()     # su paso de analizador es este archivo con PASO
    return a1.main(argv + [PASO])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
