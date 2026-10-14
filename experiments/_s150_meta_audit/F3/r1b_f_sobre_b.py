# -*- coding: utf-8 -*-
"""F3 R1b. Sobre las tablas cacheadas por r1 (mismas referencias congeladas), cuantas alertas que B publica
conserva F, con las tres varas. Reproduce el agregado de S150_RESULTADO_MESES §0 (946 de 988 completa,
684 de 708 tabla sola) como control del instrumento, y agrega la vara A119+S150.
P1: si la vara cambiara el veredicto, el cociente lo mostraria. P2: si L0 no da 946/988, el resto no vale."""
import json, sys, io
from pathlib import Path
# stdout ya lo envuelve el modulo importado
sys.path.insert(0, str(Path(__file__).parent))
from r1_recall_tramo_vara_corregida import VARAS
tmp = Path(sys.argv[1])
for vara, f in VARAS.items():
    nb = nf = 0; perdidas = []
    for mes in ("abril", "mayo", "junio", "julio", "agosto"):
        T = json.loads((tmp / ("tabla_%s.json" % mes)).read_text(encoding="utf-8"))
        for k, v in T["pasadas"].items():
            if k.split("|")[1] != "VIIRS375" or len(v) != 2: continue
            c, b = v["control"], v["brazo"]
            if f(k, c) and c["pub"]:
                nb += 1; nf += b["pub"]
                if not b["pub"] and (c["vrp_ref"] or 0) >= 0.2: perdidas.append((k, c["vrp_ref"], c["plataforma"], c["alerta_solo_ocr"]))
    print("%-14s B publica %4d alertas, F conserva %4d (%.1f %%) | perdidas de F con MIROVA >= 0,20 MW: %d %s" % (vara, nb, nf, 100*nf/nb, len(perdidas), perdidas[:12]))
