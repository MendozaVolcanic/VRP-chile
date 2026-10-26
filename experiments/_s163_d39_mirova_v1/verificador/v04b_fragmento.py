"""v04_perdidas_exhaustivo.py: recorre TODAS las versiones del consolidado en la linea principal de main
desde la base del PR (c48d24cad8) hasta el main del clon, una por una (no muestreo), bajando cada version
por raw.githubusercontent.com (no toca el clon). Para cada paso registra llaves perdidas respecto de la
version anterior, llaves repetidas y filas; al final dice que llaves perdidas en algun paso siguen ausentes
hoy. Llave cruda: (timestamp sin normalizar, Volcan, Sensor), con strip. Tambien informa si algun timestamp
no es un entero (para medir que la llave no normaliza nada)."""
import csv, io, json, os, subprocess, sys, time, urllib.request
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"
AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"
BASE = "c48d24cad8"
DESTINO = sys.argv[1] if len(sys.argv) > 1 else "main"
commits = subprocess.run(["git", "-C", CLON, "rev-list", "--first-parent", "--reverse", f"{BASE}..{DESTINO}", "--", RUTA],
                         capture_output=True, text=True).stdout.split()
commits = [BASE] + commits
# fragmento [a, b): el primero se lee solo como "anterior" (no se evalua)
A0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
B0 = int(sys.argv[3]) if len(sys.argv) > 3 else len(commits)
SUFIJO = f"_{A0}_{B0}" if len(sys.argv) > 2 else ""
commits = commits[max(A0 - 1, 0):B0] if A0 > 0 else commits[:B0]
print("versiones a leer:", len(commits), "fragmento", A0, B0, flush=True)

def leer(sha):
    url = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}"
    for intento in range(6):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            print("   reintento", sha[:10], intento, type(e).__name__, str(e)[:100], flush=True)
            time.sleep(3 * (intento + 1))
            err = e
    raise RuntimeError(f"{sha}: {err}")

def llaves(texto):
    out = []
    no_entero = 0
    protegidas = {}
    for f in csv.DictReader(io.StringIO(texto)):
        ts = (f.get("timestamp") or "").strip()
        if not ts.lstrip("-").isdigit():
            no_entero += 1
        k = (ts, (f.get("Volcan") or "").strip(), (f.get("Sensor") or "").strip())
        out.append(k)
        try:
            v = float(f.get("VRP_MW") or 0)
        except ValueError:
            v = 0
        if f.get("Tipo_Registro") == "ALERTA_TERMICA" and v >= 1.0:
            protegidas[k] = (f.get("Fecha_Satelite_UTC"), f.get("VRP_MW"), f.get("Distancia_km"))
    return out, no_entero, protegidas

pasos = []
prev_set = None
prev_sha = None
perdidas_alguna_vez = {}   # llave -> (sha donde se perdio, info protegida o None)
protegidas_vistas = {}
for i, sha in enumerate(commits):
    texto = leer(sha)
    ks, no_entero, prot = llaves(texto)
    protegidas_vistas.update(prot)
    cur = set(ks)
    rep = len(ks) - len(cur)
    if prev_set is not None:
        perd = prev_set - cur
        nuev = cur - prev_set
        for k in perd:
            perdidas_alguna_vez.setdefault(k, (sha, protegidas_vistas.get(k)))
        pasos.append({"sha": sha[:10], "filas": len(ks), "repetidas": rep, "perdidas": len(perd), "nuevas": len(nuev),
                      "no_entero": no_entero, "ej_perdidas": sorted(perd)[:3]})
        if perd or rep:
            print(f"{i:5d} {sha[:10]} filas {len(ks)} rep {rep} perdidas {len(perd)} nuevas {len(nuev)} no_entero {no_entero}", flush=True)
    else:
        pasos.append({"sha": sha[:10], "filas": len(ks), "repetidas": rep, "no_entero": no_entero})
        print(f"{i:5d} {sha[:10]} filas {len(ks)} rep {rep} no_entero {no_entero} (base)", flush=True)
    if i % 25 == 0:
        print(f"... {i}/{len(commits)}", flush=True)
    prev_set, prev_sha = cur, sha

hoy = set(llaves(subprocess.run(["git", "-C", CLON, "show", f"{DESTINO}:{RUTA}"], capture_output=True, check=True).stdout.decode("utf-8"))[0])
ausentes_hoy = {k: v for k, v in perdidas_alguna_vez.items() if k not in hoy}
print("RESUMEN versiones", len(commits), "llaves perdidas en algun paso", len(perdidas_alguna_vez),
      "siguen ausentes hoy", len(ausentes_hoy), flush=True)
por_sha = {}
for k, (sha, p) in ausentes_hoy.items():
    por_sha.setdefault(sha[:10], []).append(k)
for sha, ks in por_sha.items():
    print("  ausentes hoy perdidas en", sha, len(ks), flush=True)
prot_aus = {k: v for k, v in ausentes_hoy.items() if v[1]}
print("protegidas ausentes hoy:", len(prot_aus), flush=True)
for k, v in sorted(prot_aus.items()):
    print("   ", k, v, flush=True)
json.dump({"commits": commits, "pasos": pasos,
           "ausentes_hoy": [[list(k), v[0], v[1]] for k, v in ausentes_hoy.items()]},
          open(os.path.join(AQUI, f"v04_resultado{SUFIJO}.json"), "w"), indent=1)
print("FIN", flush=True)
