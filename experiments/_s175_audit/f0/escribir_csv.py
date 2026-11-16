"""F0 S175: arma hallazgos.csv desde INFORME.md (§4) con el módulo csv, para que el CSV no diverja del informe."""
import csv, io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0"
texto = open(D + r"\INFORME.md", encoding="utf-8").read()
sec = texto.split("## 4. Hallazgos")[1].split("## 5.")[0]
EJE = {"101": "viirs750", "102": "viirs750", "106": "viirs750", "116": "viirs750", "117": "viirs750", "118": "viirs750",
       "122": "inventario_s160", "123": "inventario_s160", "129": "inventario_s160", "121": "decisiones_s160",
       "103": "decisiones_s160", "104": "decisiones_s160", "105": "cola_campo", "108": "cola_campo",
       "119": "decisiones_s160", "120": "decisiones_s160", "127": "decisiones_s160", "128": "decisiones_s160",
       "109": "pasadas_no_bajadas", "110": "pasadas_no_bajadas", "126": "pasadas_no_bajadas",
       "107": "vencimientos", "111": "vencimientos", "112": "vencimientos", "113": "vencimientos",
       "124": "vencimientos", "125": "vencimientos", "114": "trazabilidad_auditoria", "115": "inventario_s160"}
SAL = {"101": "f0_203_cumbre_cero_salida.txt", "109": "f0_pasadas_por_satelite_salida.txt",
       "110": "f0_pasadas_por_satelite_salida.txt", "126": "f0_pasadas_por_satelite_salida.txt",
       "111": "f0_proporcion_nrt_modis_salida.txt", "113": "f0_cadencias_salida.txt", "123": "f0_clasificador_salida.txt",
       "125": "f0_245_perdidas_vuelven_salida.txt"}
filas = []
for bloque in re.split(r"\n### ", "\n" + sec)[1:]:
    i = bloque.split("\n", 1)[0].strip()
    def campo(n):
        m = re.search(rf"^- {n}: (.*)$", bloque, re.M)
        return m.group(1).strip() if m else ""
    filas.append({"id": i, "titulo": campo("TÍTULO"), "archivo_linea": campo("ARCHIVO:LÍNEA"),
                  "confianza": campo("CONFIANZA"), "gravedad": campo("GRAVEDAD 1-5"), "eje": EJE.get(i, "f0"),
                  "comando_reproduccion": campo("CÓMO REPRODUCIRLO"),
                  "salida_cruda": D + "\\" + SAL.get(i, "f0_clasificador_salida.txt")})
with open(D + r"\hallazgos.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0]))
    w.writeheader(); w.writerows(filas)
# control: releer y contar campos
rows = list(csv.reader(open(D + r"\hallazgos.csv", encoding="utf-8")))
print("filas", len(rows) - 1, "campos por fila", sorted({len(r) for r in rows}), "vacíos", [(r[0], j) for r in rows[1:] for j, x in enumerate(r) if not x])
