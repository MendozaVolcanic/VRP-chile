"""v04c_rapido.py (A1): igual que v04 (todas las versiones del consolidado desde la base, linea principal) pero
parseando por posicion (las 9 primeras columnas del consolidado no llevan comas ni comillas: timestamp, fechas,
Volcan, Sensor, VRP_MW, Distancia_km, Tipo_Registro, Clasificacion) para no depender de csv.DictReader. Comprueba
en cada version que la cabecera empieza por las columnas esperadas; si una linea no tiene al menos 9 campos la
cuenta como rara."""
import json, os, subprocess, sys, time, urllib.request, collections, gzip
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"; BASE = "c48d24cad8"; DEST = sys.argv[1] if len(sys.argv) > 1 else "main"
CAB = "timestamp,Fecha_Satelite_UTC,Fecha_Captura_Chile,Volcan,Sensor,VRP_MW,Distancia_km,Tipo_Registro,Clasificacion Mirova"
commits = [BASE] + subprocess.run(["git", "-C", CLON, "rev-list", "--first-parent", "--reverse", f"{BASE}..{DEST}", "--", RUTA], capture_output=True, text=True).stdout.split()
print("versiones:", len(commits), flush=True)
def leer(sha):
    for i in range(8):
        try:
            req = urllib.request.Request(f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}", headers={"Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = r.read()
                if r.headers.get("Content-Encoding", "") == "gzip": d = gzip.decompress(d)
                return d.decode("utf-8")
        except Exception as e:
            print("   reintento", sha[:10], i, type(e).__name__, flush=True); time.sleep(5 * (i + 1)); err = e
    raise RuntimeError(err)
def llaves(texto):
    lineas = texto.split("\n")
    assert lineas[0].startswith(CAB), lineas[0][:120]
    ks = []; raras = 0; prot = {}
    for ln in lineas[1:]:
        if not ln: continue
        p = ln.split(",", 9)
        if len(p) < 9: raras += 1; continue
        k = (p[0].strip(), p[3].strip(), p[4].strip()); ks.append(k)
        if p[7] == "ALERTA_TERMICA":
            try:
                if float(p[5]) >= 1.0: prot[k] = (p[1], p[5], p[6])
            except ValueError: pass
    return ks, raras, prot
prev = None; perdidas = {}; prot_vistas = {}; pasos = []
for i, sha in enumerate(commits):
    ks, raras, prot = llaves(leer(sha)); prot_vistas.update(prot); cur = set(ks); rep = len(ks) - len(cur)
    if prev is not None:
        perd = prev - cur; nue = cur - prev
        for k in perd: perdidas.setdefault(k, sha)
        pasos.append([sha[:10], len(ks), rep, len(perd), len(nue), raras])
        if perd or rep or raras:
            print(f"{i:5d} {sha[:10]} filas {len(ks)} rep {rep} perdidas {len(perd)} nuevas {len(nue)} raras {raras}", flush=True)
    else:
        print(f"{i:5d} {sha[:10]} filas {len(ks)} rep {rep} raras {raras} (base)", flush=True)
    if i % 50 == 0: print(f"... {i}/{len(commits)}", flush=True)
    prev = cur
hoy = prev
aus = {k: v for k, v in perdidas.items() if k not in hoy}
print("RESUMEN versiones", len(commits), "llaves perdidas en algun paso", len(perdidas), "siguen ausentes hoy", len(aus), flush=True)
for sha, n in collections.Counter(v[:10] for v in aus.values()).items(): print("  ausentes hoy perdidas en", sha, n, flush=True)
pa = {k: prot_vistas[k] for k in aus if k in prot_vistas}
print("protegidas ausentes hoy:", len(pa), flush=True)
for k, v in sorted(pa.items()): print("   ", k, v, flush=True)
json.dump({"pasos": pasos, "ausentes_hoy": [[list(k), v] for k, v in aus.items()]}, open(os.path.join(AQUI, "v04c_resultado.json"), "w"), indent=1)
print("FIN", flush=True)
