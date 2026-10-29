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

Uso: los mismos argumentos que `analizar_v750b.py` (`--art`, `--objetivos`, `--evaluador`, `--censo-art`,
`--censo-objetivos`, `--sin-granulo`, ...). `--salida` por defecto va a esta carpeta, no a la del sellado.
Salidas: 0, 3, 4 y 5 como el sellado; 2 si el analizador no es el sellado o un reemplazo no calza.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ANALIZADOR = AQUI.parent / "analizar_v750b.py"
SHA_ANALIZADOR_LF = "83b7159bd0666871b2e88a48c23feba4900ae28c24abd76b6cb3abf7b2593392"   # tag s162-v750b-sellado
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


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ruta = ANALIZADOR
    if "--analizador" in argv:          # sólo para las pruebas (un analizador ajeno tiene que ser rechazado)
        k = argv.index("--analizador")
        ruta = Path(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    if "--salida" not in argv:
        argv = argv + ["--salida", str(AQUI / "leer_n3_v750b_salida.txt")]
    src = fuente_con_n3(ruta)
    if src.startswith("RECHAZO"):
        print(src, flush=True)
        return 2
    ns = {"__name__": "analizar_v750b_con_n3", "__file__": str(ruta)}
    exec(compile(src, str(ruta), "exec"), ns)
    sys.argv = [str(ruta)] + argv
    return ns["main"]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
