"""Mide si las funciones del tablero que banco_paridad extrae (el predicado «publica») leen la marca de la via.
Pregunta 1: si el predicado leyera la marca, esta medicion lo ve? Si: busca las cadenas en el cuerpo de cada funcion.
Pregunta 2: si el instrumento estuviera muerto (cuerpo vacio), se ve: imprime el largo del cuerpo; un largo 0 o un -1 delata.
Control positivo: esAnclaHonesta (que SI contiene "codigo_mirova") se mide al final y tiene que dar True.
"""
import sys

src = open(sys.argv[1], encoding="utf-8").read()
FUNCS = ['_havKm', 'mirovaEqVrp', 'f5CoreMagnitude', 'mirovaEqVrpCore', 'mirovaEqVrpDisplay',
         'isCirrusArtifact', 'isDiffuseFieldArtifact', 'isThermalArtifact', 'isValidDetection',
         'isSummitDetection', 'esAnclaHonesta']
for nombre in FUNCS:
    i = src.find('function ' + nombre + '(')
    j = src.find('\nfunction ', i + 1)
    cuerpo = src[i:j] if i >= 0 else ''
    print("%-24s inicio=%7d largo=%6d final_hotspot_source=%s via_codigo_mirova=%s codigo_mirova=%s esAnclaHonesta=%s" % (
        nombre, i, len(cuerpo), 'final_hotspot_source' in cuerpo, 'via_codigo_mirova' in cuerpo,
        'codigo_mirova' in cuerpo, 'esAnclaHonesta(' in cuerpo))
