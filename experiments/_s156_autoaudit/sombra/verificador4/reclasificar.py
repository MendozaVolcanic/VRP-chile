# Reclasifica las fallas de la bateria v4 leyendo el TIPO de excepcion de la ultima linea del traceback
# ("archivo:linea: Tipo") en cada junit. Atrapada = al menos una falla por AssertionError / Failed.
import re, sys
import xml.etree.ElementTree as ET
from pathlib import Path
d = Path(sys.argv[1]); sal = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
nombres = [l for l in sal if l.startswith(("autor ", "v4 "))]
res = {"autor": [0, 0], "v4": [0, 0]}
for i, l in enumerate(nombres):
    quien, n = l.split()[0], l.split()[1]
    if "NO APLICA" in l:
        print(l); continue
    tipos = []
    for tc in ET.parse(d / f"j{i}.xml").getroot().iter("testcase"):
        for fl in list(tc.findall("failure")) + list(tc.findall("error")):
            m = re.findall(r":\d+: (\w+(?:\.\w+)*)\s*$", (fl.text or "").strip(), re.M)
            tipos.append(m[-1] if m else "?")
    asr = sum(t in ("AssertionError", "Failed") or t.endswith(".Failed") for t in tipos)
    res[quien][0] += asr > 0; res[quien][1] += 1
    otras = sorted({t for t in tipos if not (t in ("AssertionError", "Failed") or t.endswith(".Failed"))})
    print(f"{quien:5} {n:44s} {'ATRAPADA' if asr else 'NO ATRAPADA'} | fallas por asercion {asr} | otras {otras or '-'}")
for q, (k, n) in res.items():
    print(f"{q}: {k} de {n} atrapadas por asercion")
