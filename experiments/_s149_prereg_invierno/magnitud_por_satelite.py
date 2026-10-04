# S150. Mediana de (magnitud que publica el control / magnitud de MIROVA) en VIIRS 375, por satelite y por
# canal de la alerta (tabla o solo OCR). Pregunta: las dos perdidas de agosto (Suomi NPP al borde, B al
# 1-4 % de MIROVA) son un problema general de Suomi NPP?  Uso: python magnitud_por_satelite.py tabla.json ...
import json, sys, io, statistics as st, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
for ruta in sys.argv[1:]:
    D = json.load(open(ruta, encoding="utf-8")); g = collections.defaultdict(list)
    for k, v in D["pasadas"].items():
        if k.split("|")[1] != "VIIRS375" or len(v) != 2: continue
        c = v["control"]
        if c["lab"] == "pos" and c["vrp_ref"] and c["pub"]:
            g[(c["plataforma"], "ocr" if c["alerta_solo_ocr"] else "tabla")].append(c["disp"] / c["vrp_ref"])
    print(D["ventana"], " | ".join("%s/%s n %d mediana %.2f" % (p, o, len(x), st.median(x)) for (p, o), x in sorted(g.items())))
