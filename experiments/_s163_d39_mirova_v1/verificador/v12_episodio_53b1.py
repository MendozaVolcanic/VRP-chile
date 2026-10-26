"""v12_episodio_53b1.py (A1, instrumento propio, sin muestreo): el episodio 53b1e6d3c0 contra su padre y contra el
main del clon. Llave cruda (timestamp sin normalizar, Volcan, Sensor). Protegida = ALERTA_TERMICA con VRP >= 1."""
import csv, io, subprocess, time, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
def git(*a): return subprocess.run(["git", "-C", CLON] + list(a), capture_output=True, check=True).stdout.decode("utf-8")
def raw(sha):
    t = time.time(); d = urllib.request.urlopen(f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}", timeout=120).read().decode("utf-8")
    print(f"   bajado {sha[:10]} {len(d)} bytes en {time.time()-t:.1f} s"); return d
def tabla(t):
    rows = list(csv.DictReader(io.StringIO(t))); ks = [((f["timestamp"] or "").strip(), f["Volcan"].strip(), f["Sensor"].strip()) for f in rows]
    return rows, ks
padre = git("rev-parse", "53b1e6d3c0^").strip(); print("padre:", padre[:10])
rp, kp = tabla(raw(padre)); rh, kh = tabla(raw("53b1e6d3c0")); rm, km = tabla(git("show", f"main:{RUTA}"))
sp, sh, sm = set(kp), set(kh), set(km)
print(f"padre {len(kp)} filas ({len(sp)} llaves) | 53b1e6d3c0 {len(kh)} filas ({len(sh)} llaves, repetidas {len(kh)-len(sh)}) | main clon {len(km)} filas ({len(sm)} llaves, repetidas {len(km)-len(sm)})")
perd = sp - sh; print("llaves del padre ausentes en 53b1e6d3c0:", len(perd), "| de esas, ausentes hoy en main:", len(perd - sm), "| repuestas despues:", len(perd & sm))
nuevas = sh - sp; print("llaves nuevas en 53b1e6d3c0 (no estaban en el padre):", len(nuevas))
fp = {k: f for k, f in zip(kp, rp)}
import collections
print("tipos de las perdidas:", collections.Counter(fp[k]["Tipo_Registro"] for k in perd))
prot = [(k, fp[k]["Fecha_Satelite_UTC"], fp[k]["VRP_MW"], fp[k]["Distancia_km"]) for k in perd if fp[k]["Tipo_Registro"] == "ALERTA_TERMICA" and float(fp[k]["VRP_MW"] or 0) >= 1]
print("protegidas perdidas:", len(prot)); [print("   ", p) for p in sorted(prot)]
# contra el archivo de reposicion de s163 (las 241 agregadas) y el del PR
rep = list(csv.DictReader(io.StringIO(git("show", "s163/d39-reposicion-y-bucle:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv"))))
pr = list(csv.DictReader(io.StringIO(git("show", "pr26:monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv"))))
k241 = {((f["timestamp"] or "").strip(), f["Volcan"], f["Sensor"]) for f in rep[len(pr):]}
kpr = {((f["timestamp"] or "").strip(), f["Volcan"], f["Sensor"]) for f in pr}
print("perdidas en el PR (2110):", len(perd & kpr), "| perdidas == las 241 agregadas en s163:", perd == k241, "| diferencia:", len(perd ^ k241))
# llaves con timestamp no entero en alguna version
for nom, ks in (("padre", kp), ("53b1", kh), ("main", km)):
    print(nom, "timestamps no enteros:", sum(not k[0].lstrip('-').isdigit() for k in ks))
