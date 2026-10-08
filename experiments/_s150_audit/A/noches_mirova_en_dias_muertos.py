"""S150 frente A (hallazgo A-4): noches volcan-sensor-dia con alerta de MIROVA (Tipo_Registro distinto
de RUTINA) en los dias sin ningun dato nuestro (2026-10-03 a 10-05), leidas del mismo snapshot que uso
la auditoria semanal del 2026-10-05 18:05 (commit 80b358f6, = checkout de hoy para esas rutas).
P1: si no hubiera alertas esos dias, da 0 (lo ve). P2: si los CSV no cargaran, el conteo total del
control (10-02, dia con datos) seria 0; se imprime para comprobarlo.
Limite: no aplica la exclusion de alertas diurnas que hace scripts/auto_audit_weekly.py."""
import csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
RUTAS = ["data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv",
         "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"]
noches = collections.defaultdict(set)
for p in RUTAS:
    for r in csv.DictReader(open(p, encoding="utf-8")):
        f = r["Fecha_Satelite_UTC"][:10]
        if "2026-10-02" <= f <= "2026-10-05" and r.get("Tipo_Registro", "") != "RUTINA":
            noches[(f, r["Sensor"])].add(r["Volcan"])
for k in sorted(noches):
    print(k, len(noches[k]), sorted(noches[k]))
muertos = sum(len(v) for (f, s), v in noches.items() if s == "VIIRS375" and f >= "2026-10-03")
print("VIIRS375, noches volcan-dia con alerta en 10-03..10-05:", muertos)
