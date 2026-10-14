"""F4 (meta-auditoria S150): busca en las puertas de entrada las citas de lo que S147-S150 cambio,
y dice si la cita lleva marca (simbolo de advertencia o "S147".."S150" a <= 6 lineas).

Preguntas del instrumento:
1. Si una puerta siguiera afirmando lo caido sin marca, se veria: el patron encuentra la cita y la
   ventana de +-6 lineas no contiene marca. NO ve citas parafraseadas con otras palabras (sesgo hacia
   "no encontrada"): la cobertura es un piso, como el censo de S145.
2. Si el instrumento estuviera muerto (rutas o codificacion malas) no hallaria nada en ninguna fila;
   los controles positivos son dos citas que SI fueron marcadas en su sesion: A10 (rebajada S147) y
   A118 (arreglo S149). Deben salir MARCADA. Un "SIN MARCAR" de este script es candidato: la
   clasificacion final se hace leyendo la linea (el informe cita las que lei).
Ventana: archivos tal como estan en disco hoy (main en 13f5bb0dd mas lo no commiteado).
"""
import io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
MEM = "C:/Users/nmend/.claude/projects/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory/"
PUERTAS = {
    "CLAUDE.md": R + "CLAUDE.md",
    "MISSION.md": R + "docs/MISSION.md",
    "DIVERGENCES": R + "docs/MIROVA_DIVERGENCES.md",
    "BLOQUE_S150": R + "tasks/BLOQUE_ARRANQUE_S150.md",
    "INDEX.md": R + "docs/INDEX.md",
    "FICHA": R + "docs/FICHA_SDA_VRP_CHILE.md",
    "MEMORY.md": MEM + "MEMORY.md",
    "mem/feedback_mision_clon_mirova": MEM + "feedback_mision_clon_mirova.md",
    "mem/feedback_s143_primero_igualar": MEM + "feedback_s143_primero_igualar_a_mirova.md",
}
# (id, patron, que cambio y en que sesion)
ITEMS = [
    ("CTRL+ A10", r"A10\. .*REBAJADA S147", "control positivo: debe salir MARCADA"),
    ("CTRL+ A118", r"arreglado en S149", "control positivo: debe salir MARCADA"),
    ("S27 literal", r"literal puro|S27 Test1 cierra D4|NO APROB|recall cae 27", "S149: el literal de S27 no tenia Tests 2 y 3"),
    ("S27 empirico", r"resultado emp.rico de S27", "S147: el 50 a 80 % queda SIN EVIDENCIA; S149: medido sin Tests 2 y 3"),
    ("recall>precision", r"priorizamos recall", "S149: paridad en los dos sentidos"),
    ("cobertura primero", r"cobertura completa de lo que MIROVA publica|criterio que manda es \*\*no perder", "S149: paridad en los dos sentidos"),
    ("objetivo 2 sin gates", r"No se introducen gates adicionales|no eliminarlo", "S149/S150: lo extra va al experimental"),
    ("A94 946", r"946", "S149: por pasada en MODIS son 68 de 77"),
    ("A119 enero", r"enero no se usa|86 % en\s*$|86 % en enero", "S149 B-03: el 86 % era Tupungatito en el denominador"),
    ("A119 MODIS OCR", r"dependen del OCR", "S149: hay alertas MODIS solo OCR (medido aqui: 4)"),
    ("cron 12/dia", r"12 veces/d.a|cron cada 2h", "S150 V-3: 4,25 a 5 corridas por dia"),
    ("token fecha", r"vence el\s*$|2026-10-03", "S150: rotado 2026-10-08, vence 2026-12-07"),
    ("tope D9 funciona", r"tope de magnitud ya est. adoptado y funciona|tope de 5 MW s. funciona|tope de 5 MW se\s*$|tope de 5 MW y los", "S150 C-01: el tope recorta en erupcion y el tablero lo rotula artefacto"),
    ("vent_anchored", r"RESUELTO S38|vent-anchored es robusta", "S150: decision de Nicolas, gana la anomalia MAYOR"),
    ("D18 cableado", r"Arreglarlo toca|process_viirs.py:1313", "S149 #738 mergeado: la caja llega al segundo pase"),
    ("caja PR738 espera", r"#738.*ESPERA|SIN MERGEAR", "#738 mergeado 2026-09-21"),
    ("A/B sin Test 1 NO ADOPTAR", r"NO ADOPTAR porque apagarlo", "S149 frente D H1: el NO ADOPTAR cae"),
    ("D25 NO ADOPTAR", r"D22/D25 verificado NO ADOPTAR|A/B D22/D25 NO ADOPTAR", "S149 frente D H2: los veredictos de D25 caen"),
    ("NRT caido", r"TOKEN EARTHDATA VENCIDO|NRT caido", "S150: token rotado 2026-10-08, NRT verde"),
    ("5 perdidas", r"5 perdidas fuertes|mirar imagenes MIROVA", "S150 #764/#774: filas OCR con la imagen de otra pasada"),
    ("ficha version", r"Versi.n:\*\* v1\.4", "historial llega a v1.6"),
    ("ficha suma", r"suma .nicamente los p.xeles", "S150 C-03: bajo 5 MW se publica el pixel mas fuerte"),
    ("ficha 1 km indistinguible", r"f.sicamente indistinguibles", "S150: banda 22 separa en Lascar (68/73 contra 11/96)"),
    ("lab identico", r"laboratorio es \*\*id.ntico", "S150 #771: experimental congelado"),
    ("A64 LAADS", r"devuelve lo de LAADS", "S150 A-13: un timeout de LANCE veta tambien LAADS"),
]
MARCA = re.compile(r"⚠|S14[7-9]|S150")
textos = {}
for k, p in PUERTAS.items():
    try:
        textos[k] = open(p, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        textos[k] = None
        print("NO EXISTE", k, p)
for iid, pat, que in ITEMS:
    rx = re.compile(pat)
    hits = []
    for k, lines in textos.items():
        if not lines:
            continue
        for i, l in enumerate(lines):
            if rx.search(l):
                ventana = "\n".join(lines[max(0, i - 6): i + 7])
                hits.append((k, i + 1, "MARCADA?" if MARCA.search(ventana) else "SIN MARCA"))
    print(f"\n[{iid}] {que}")
    if not hits:
        print("   (sin coincidencias)")
    for k, n, m in hits:
        print(f"   {m:9s} {k}:{n}")
