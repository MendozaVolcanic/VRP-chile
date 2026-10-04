# S150. Agregado de las ventanas VIIRS (mayo a agosto) por sensor: negativos limpios, recall por pasada, P5. Etiqueta completa y tabla sola.
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
acc = collections.defaultdict(lambda: collections.Counter())
for ruta in sys.argv[1:]:
    T = json.load(open(ruta, encoding="utf-8"))["pasadas"]
    for k, v in T.items():
        s = k.split("|")[1]
        if len(v) != 2: continue
        c, f = v["control"], v["brazo"]; a = acc[s]
        if c["lab"] == "neg_limpio": a["neg"] += 1; a["neg_c"] += c["pub"]; a["neg_f"] += f["pub"]
        if c["lab"] == "pos":
            a["pos"] += 1; a["pos_c"] += c["pub"]; a["pos_f"] += c["pub"] and f["pub"]
            if not c.get("alerta_solo_ocr"): a["post"] += 1; a["post_c"] += c["pub"]; a["post_f"] += c["pub"] and f["pub"]
        if c.get("rutina_pasada") and c.get("noche_con_alerta_sensor"): a["rut"] += 1; a["rut_c"] += c["pub"]; a["rut_f"] += f["pub"]
for s, a in sorted(acc.items()):
    p = lambda x, n: "%d de %d (%.1f %%)" % (x, n, 100 * x / n if n else 0)
    print(s); print("  negativos limpios: control", p(a["neg_c"], a["neg"]), "| max", p(a["neg_f"], a["neg"]))
    print("  positivas, etiqueta completa: control", p(a["pos_c"], a["pos"]), "| max conserva", p(a["pos_f"], a["pos_c"]))
    print("  positivas, tabla sola:        control", p(a["post_c"], a["post"]), "| max conserva", p(a["post_f"], a["post_c"]))
    print("  RUTINA en noche con alerta:   control", p(a["rut_c"], a["rut"]), "| max", p(a["rut_f"], a["rut"]))
