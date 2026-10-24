# -*- coding: utf-8 -*-
"""S162 instrumento: mutaciones contadas sólo si las atrapa una ASERCIÓN, con control de caída.

POR QUÉ (feedback S152 y S156): una mutación que hace caer las pruebas con una excepción (import roto, NameError,
TypeError) no prueba que las pruebas miren el comportamiento; sólo que el código explota. Se cuenta como «atrapada»
sólo si al menos una prueba falla por AssertionError y ninguna cae por otra excepción. El tipo de falla se lee del
JUnit XML (feedback S160), no del texto de la consola.

Uso: python -I experiments/_s162_instrumento/mutar.py <spec.json> <salida.txt>
spec: {"pruebas": ["tests/x.py", ...], "mutaciones": [{"id": "M1", "archivo": "scripts/y.py", "viejo": "...",
"nuevo": "...", "que": "..."}]}. Cada `viejo` tiene que aparecer exactamente una vez. El archivo se restaura byte a
byte después de cada mutación, también si algo falla. Correr con el árbol quieto (A112).
"""
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def clasificar(xml_path):
    raiz = ET.parse(xml_path).getroot()
    asercion = caida = total = 0
    for caso in raiz.iter("testcase"):
        total += 1
        for hijo in caso:
            if hijo.tag in ("failure", "error"):
                tipo = hijo.get("type") or ""
                msg = hijo.get("message") or ""
                if hijo.tag == "failure" and ("AssertionError" in tipo or "assert" in msg.lower()):
                    asercion += 1
                else:
                    caida += 1
    return asercion, caida, total


def correr(pruebas, xml):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml),
                        *pruebas], cwd=RAIZ, capture_output=True, text=True)
    return r.returncode


def main(spec_path, salida_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    pruebas = spec["pruebas"]
    lineas = []
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "r.xml"
        rc = correr(pruebas, xml)
        a, c, n = clasificar(xml)
        lineas.append("linea base: rc=%d, %d pruebas, %d fallas por asercion, %d caidas" % (rc, n, a, c))
        if rc != 0:
            lineas.append("LINEA BASE ROJA: no se corren mutaciones")
            Path(salida_path).write_text("\n".join(lineas) + "\n", encoding="utf-8")
            print("\n".join(lineas))
            return 1
        atrapadas = 0
        for m in spec["mutaciones"]:
            p = RAIZ / m["archivo"]
            original = p.read_bytes()
            texto = original.decode("utf-8")
            viejo = m["viejo"].replace("\n", "\r\n") if "\r\n" in texto and "\r\n" not in m["viejo"] else m["viejo"]
            nuevo = m["nuevo"].replace("\n", "\r\n") if "\r\n" in texto and "\r\n" not in m["nuevo"] else m["nuevo"]
            if texto.count(viejo) != 1:
                lineas.append("%s NO APLICA (aparece %d veces): %s" % (m["id"], texto.count(viejo), m["que"]))
                continue
            try:
                p.write_bytes(texto.replace(viejo, nuevo).encode("utf-8"))
                rc = correr(pruebas, xml)
                a, c, n = clasificar(xml)
            finally:
                p.write_bytes(original)
            ok = rc != 0 and a > 0 and c == 0
            atrapadas += ok
            estado = "ATRAPADA" if ok else ("CAIDA (no cuenta)" if c else "VIVA")
            lineas.append("%s %s: %d por asercion, %d caidas, rc=%d | %s" % (m["id"], estado, a, c, rc, m["que"]))
        lineas.append("atrapadas por asercion: %d de %d" % (atrapadas, len(spec["mutaciones"])))
    Path(salida_path).write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
