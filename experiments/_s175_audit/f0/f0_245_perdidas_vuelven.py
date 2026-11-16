"""F0 S175, 245: ¿cuántas filas de la unión histórica de perdidas (base 752d348bc) siguen fuera de la copia vigente
latest_consolidado.csv de la base? Llave (Fecha_Satelite_UTC, Volcan, Sensor). P1: control positivo, una fila de la
copia vigente siempre está (cuenta de la copia > 0); P2: si la unión no se leyera, n=0 y se ve."""
import csv, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = r"C:\Users\nmend\vrp-temporales\s175_audit"
def llaves(p):
    with open(p, encoding="utf-8") as fh:
        return {(r["Fecha_Satelite_UTC"].strip(), r["Volcan"].strip(), r["Sensor"].strip()): r for r in csv.DictReader(fh)}
perd = llaves(T + r"\f0\filas_perdidas_base.csv")
vig = llaves(T + r"\insumos\latest_consolidado_base.csv")
fuera = [k for k in perd if k not in vig]
al = [k for k in fuera if "ALERTA" in perd[k].get("Tipo_Registro", "")]
prot = [k for k in al if float(perd[k].get("VRP_MW") or 0) >= 1.0]
print(f"filas en la unión de perdidas: {len(perd)}; copia vigente: {len(vig)}")
print(f"perdidas que siguen fuera de la copia vigente: {len(fuera)}; con ALERTA: {len(al)}; ALERTA >= 1 MW: {len(prot)}")
for k in sorted(prot):
    print("  ", k, perd[k].get("VRP_MW"))
