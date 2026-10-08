"""S150 frente A: cuanto atrasa el snapshot consolidado (semanal) contra el remoto de Mirova-v1.
Pregunta 1 del instrumento: si el snapshot estuviera congelado, el conteo de filas faltantes lo veria (crece).
Pregunta 2: si el remoto no bajo (archivo vacio), el script aborta (control: n_remoto > 0).
Control positivo: latest_consolidado.csv (sync horario) debe dar ~0 faltantes."""
import csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
def cargar(p):
    with open(p, encoding="utf-8", newline="") as f:
        return {(r["Fecha_Satelite_UTC"], r["Volcan"], r["Sensor"]): r for r in csv.DictReader(f)}
remoto = cargar(sys.argv[1]); assert len(remoto) > 1000
for nombre in sys.argv[2:]:
    loc = cargar(nombre)
    falt = [k for k in remoto if k not in loc]
    por = collections.Counter((k[1], k[0][:10] >= "2026-09-28") for k in falt)
    alertas = [k for k in falt if remoto[k]["Tipo_Registro"] != "RUTINA"]
    fechas = sorted(k[0] for k in falt)
    print(f"{nombre}: filas_local={len(loc)} remoto={len(remoto)} faltan={len(falt)} "
          f"(alertas no RUTINA={len(alertas)}) rango_faltante={fechas[0] if fechas else '-'}..{fechas[-1] if fechas else '-'}")
    ndc = [k for k in falt if k[1].startswith("Nevados")]
    print(f"   NdC faltantes={len(ndc)}; NdC alertas faltantes={sum(1 for k in ndc if remoto[k]['Tipo_Registro']!='RUTINA')}")
    print("   max Fecha_Satelite_UTC local:", max(k[0] for k in loc))
