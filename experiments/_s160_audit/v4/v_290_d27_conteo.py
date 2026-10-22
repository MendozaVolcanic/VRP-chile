# -*- coding: utf-8 -*-
"""V4 / 290: cuenta independiente de la marca S151 de D27 (filas ALERTA_TERMICA de latest_consolidado.csv,
2026-01-11 a 2026-10-14, hora satelital 13 a 21 UTC, VRP >= 1 MW, y protegidas de noche) sobre dos copias de la
tabla: la del commit de la marca (88e97d84e) y la congelada de main d516b9d8c. No usa el script del auditor.
Instrumento: pregunta 1, si la marca estuviera mal en su fecha, la copia de 88e97d84e lo mostraría; pregunta 2, el
control positivo es que la cuenta de main con la ventana abierta hasta hoy da más filas que con la ventana cerrada.
Definiciones mías (SOSPECHA de que coincidan con las de la marca, que no cita script): fila = fila del CSV (no pasada
deduplicada); 'de tarde' = 13 <= hora UTC < 21 ... se prueban 13-21 cerrado y semiabierto; 'noche' = hora < 13 o >= 21."""
import csv, sys, collections
def cuenta(p, hasta="2026-10-14"):
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    al = [r for r in rows if r["Tipo_Registro"] == "ALERTA_TERMICA" and "2026-01-11" <= r["Fecha_Satelite_UTC"][:10] <= hasta]
    def h(r): return int(r["Fecha_Satelite_UTC"][11:13])
    def v(r):
        try: return float(r["VRP_MW"])
        except ValueError: return 0.0
    tarde_c = [r for r in al if 13 <= h(r) <= 21]; tarde_s = [r for r in al if 13 <= h(r) < 21]
    prot_t = [r for r in tarde_c if v(r) >= 1.0]
    noche = [r for r in al if not (13 <= h(r) <= 21)]
    prot_n = [r for r in noche if v(r) >= 1.0]
    sens = collections.Counter(r["Sensor"] for r in prot_t); vol = collections.Counter(r["Volcan"] for r in prot_t)
    print(f"  alertas={len(al)} tarde[13,21]={len(tarde_c)} tarde[13,21)={len(tarde_s)} prot_tarde={len(prot_t)} "
          f"prot_noche={len(prot_n)}\n   por sensor {dict(sens)} por volcan {dict(vol)}")
for p in sys.argv[1:]:
    print(p, "ventana 2026-01-11..2026-10-14:"); cuenta(p)
    print(p, "ventana abierta hasta 2026-10-31 (control):"); cuenta(p, "2026-10-31")
