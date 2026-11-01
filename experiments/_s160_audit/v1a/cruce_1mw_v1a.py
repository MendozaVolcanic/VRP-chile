# -*- coding: utf-8 -*-
"""V1a, fila R11 por el camino de P3 (magnitud). REGLA_ADOPCION.md §5 reconoce que P3 no puede fallar en VIIRS 375
y pone en su lugar una regla: la magnitud no bloquea si ninguna protegida que C0 muestra sobre 1 MW queda bajo 1 MW
con K. Aqui se cuenta eso desde las tablas del evaluador original (disp = magnitud que muestra el tablero, node),
y tambien las alertas (cualquier VRP) que cruzan 1 MW en las dos direcciones. Ventanas y referencias como margen_k.
Preguntas del instrumento: (1) si hubiera cruces se verian (control: con umbral 0,1 MW el conteo tiene que subir);
(2) si disp estuviera vacio, 'publican los dos' seria 0."""
import json
D = r"D:/vrp-trabajo/temporales/s160_audit/v1a/"
for nom, f, dv in (("V1", D + "base_v1/tmp/t_C0_K.json", "0000"), ("V2 tabla sola", D + "tmp_v2_si/t_C0_K.json", "2026-04-01"),
                   ("V2 tabla+OCR", D + "tmp_v2_no/t_C0_K.json", "2026-04-01")):
    T = json.load(open(f, encoding="utf-8"))["pasadas"]
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        for U in (1.0, 0.1):
            ambos = baja_prot = sube_prot = baja = sube = 0; lista = []
            for k, v in T.items():
                if k.split("|")[1] != s or len(v) != 2: continue
                if s != "MODIS" and k.split("|")[2][:10] < dv: continue
                c, b = v["control"], v["brazo"]
                if not (c["pub"] and b["pub"] and c["lab"] == "pos"): continue
                ambos += 1; prot = (c["vrp_ref"] or 0) >= 1.0
                if c["disp"] >= U > b["disp"]:
                    baja += 1; baja_prot += prot
                    if prot and U == 1.0: lista.append("%s C0 %.2f K %.2f MIROVA %.2f" % (k, c["disp"], b["disp"], c["vrp_ref"]))
                if b["disp"] >= U > c["disp"]:
                    sube += 1; sube_prot += prot
            print("%-13s %-8s umbral %.1f | alertas que publican los dos %4d | cruzan hacia abajo %3d (protegidas %d) | hacia arriba %3d (protegidas %d)" % (
                nom, s, U, ambos, baja, baja_prot, sube, sube_prot))
            for l in lista: print("      protegida que cruza hacia abajo: " + l)
