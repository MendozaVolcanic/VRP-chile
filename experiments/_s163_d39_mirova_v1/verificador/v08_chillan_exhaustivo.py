"""v08_chillan_exhaustivo.py (A6, instrumento propio): lee TODAS las versiones del consolidado en la linea
principal de main entre 2026-10-15 03:00 y 2026-10-17 03:00 UTC (no una muestra por hora) por
raw.githubusercontent.com, y registra toda fila de Nevados de Chillan con Fecha_Satelite_UTC del 15 o 16 de
octubre que haya existido en alguna version. Al final: cuales de esas llaves faltan hoy en main (clon), y si
alguna version tuvo fila a las horas de las alertas solo-OCR (05:00, 19:00 del 15; 06:18, 18:42 del 16)."""
import csv, io, subprocess, time, urllib.request, json, os
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
AQUI = os.path.dirname(os.path.abspath(__file__))
log = subprocess.run(["git", "-C", CLON, "log", "--first-parent", "--reverse", "--format=%H %cI",
                      "--since=2026-10-15T03:00:00Z", "--until=2026-10-17T03:00:00Z", "main", "--", RUTA],
                     capture_output=True, text=True).stdout.split("\n")
log = [l.split() for l in log if l]
print("versiones:", len(log), log[0][1] if log else None, "a", log[-1][1] if log else None, flush=True)
def leer(sha):
    url = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}"
    for i in range(6):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            print("   reintento", sha[:10], i, type(e).__name__, flush=True); time.sleep(3 * (i + 1)); err = e
    raise RuntimeError(f"{sha}: {err}")
OBJ = {"2026-10-15 05:00", "2026-10-15 19:00", "2026-10-16 06:18", "2026-10-16 18:42"}
vistas = {}   # llave -> (primera version, fila)
cerca = {}
for i, (sha, c) in enumerate(log):
    for f in csv.DictReader(io.StringIO(leer(sha))):
        if f["Volcan"] == "Nevados de Chillan" and f["Fecha_Satelite_UTC"][:10] in ("2026-10-15", "2026-10-16"):
            k = (f["timestamp"], f["Volcan"], f["Sensor"])
            vistas.setdefault(k, (c, f))
            if f["Fecha_Satelite_UTC"][:16] in OBJ:
                cerca.setdefault(k, c)
    if i % 50 == 0:
        print(f"... {i}/{len(log)} {c} llaves vistas {len(vistas)}", flush=True)
hoy = {(f["timestamp"], f["Volcan"], f["Sensor"]) for f in csv.DictReader(io.StringIO(
    subprocess.run(["git", "-C", CLON, "show", f"main:{RUTA}"], capture_output=True, check=True).stdout.decode("utf-8")))}
print("llaves de Chillan 15-16 oct vistas en alguna version:", len(vistas), flush=True)
falt = {k: v for k, v in vistas.items() if k not in hoy}
print("de esas, ausentes hoy en main:", len(falt), flush=True)
for k, (c, f) in sorted(falt.items()):
    print("   ", f["Fecha_Satelite_UTC"], f["Sensor"], f["VRP_MW"], f["Tipo_Registro"], "vista desde", c, flush=True)
print("filas a las horas de las alertas solo-OCR:", cerca, flush=True)
json.dump({"versiones": len(log), "vistas": [[list(k), c, f] for k, (c, f) in vistas.items()], "ausentes_hoy": [list(k) for k in falt]},
          open(os.path.join(AQUI, "v08_resultado.json"), "w"), indent=1)
print("FIN", flush=True)
