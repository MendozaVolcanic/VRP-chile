# -*- coding: utf-8 -*-
"""M1 (frente D, S179). Tamano de lo que pages-deploy.yml copia al sitio publico, medido en blobs de git.

Las dos preguntas del instrumento:
1. Si lo que mido estuviera roto (por ejemplo, si data/ pesara el doble), esta medicion lo veria?  Si: suma el
   tamano de cada blob del commit con `git ls-tree -r -l`. NO ve lo que el paso de build agrega fuera de git
   (los *_recent.json que genera scripts/build_recent_json.py): eso se estima aparte y se rotula ESTIMADO.
2. Si el instrumento estuviera muerto, el resultado se veria distinto?  Si: control positivo abajo (la suma por carpeta
   tiene que igualar la suma total de data/; y el numero de archivos de data/mirova_equivalent tiene que ser 45 o mas).

Denominador: todos los blobs del commit bajo data/, frontend/, imagenes/ y los dos CSV que copia el workflow.
Ventana: el arbol del commit que se pasa por argumento (por defecto main 438a60a1e). No mide el sitio publicado.
Uso: python m1_pages_tamano.py <repo> [commit]
"""
import subprocess, sys, json, collections, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
repo = sys.argv[1]
commit = sys.argv[2] if len(sys.argv) > 2 else "438a60a1e"
MB = 1024 * 1024

def ls(path):
    o = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-l", commit, "--", path],
                       capture_output=True, text=True, encoding="utf-8", check=True).stdout
    out = []
    for line in o.splitlines():
        meta, name = line.split("\t", 1)
        size = meta.split()[3]
        out.append((name, int(size) if size != "-" else 0))
    return out

data = ls("data")
por = collections.Counter(); n = collections.Counter()
for name, size in data:
    partes = name.split("/")
    top = partes[1] if len(partes) > 2 else "(archivos sueltos en data/)"
    por[top] += size; n[top] += 1
total_data = sum(s for _, s in data)
assert sum(por.values()) == total_data, "control: la suma por carpeta no iguala el total"
assert n["mirova_equivalent"] >= 45, "control: faltan archivos de produccion"

# lo que pages-deploy.yml l. 81 borra del artefacto
EXCLUIDAS = ["sombra_34", "sombra_codigo_mirova", "guardia_k_modis", "guardia_k_viirs"]
excl = sum(por[k] for k in EXCLUIDAS)
frontend = sum(s for _, s in ls("frontend"))
imagenes = sum(s for _, s in ls("imagenes"))
csvs = sum(s for _, s in ls("latest_consolidado.csv")) + sum(s for _, s in ls("01_05_2026_registro_vrp_consolidado.csv"))

print(f"commit {commit}")
print(f"data/ total: {total_data/MB:.1f} MB en {len(data)} archivos")
print("por carpeta de data/ (MB, archivos), de mayor a menor:")
for k, v in por.most_common():
    marca = "  [EXCLUIDA del sitio, pages-deploy.yml l. 81]" if k in EXCLUIDAS else ""
    print(f"  {k:40s} {v/MB:8.1f} MB  {n[k]:5d}{marca}")
sitio_git = total_data - excl + frontend + imagenes + csvs
print(f"\ndata/ que SI va al sitio: {(total_data-excl)/MB:.1f} MB (excluidas {excl/MB:.1f} MB)")
print(f"frontend/: {frontend/MB:.1f} MB; imagenes/: {imagenes/MB:.1f} MB; CSV de referencia: {csvs/MB:.1f} MB")
print(f"SITIO, parte medida en git: {sitio_git/MB:.1f} MB")
# quien lee cada carpeta en el tablero: solo se declara lo que dice el comentario del workflow (l. 78-80)
LEE_EL_TABLERO = ["mirova_equivalent", "mirova", "experimental_v2", "alerts"]
no_leidas = {k: v for k, v in por.items() if k not in LEE_EL_TABLERO and k not in EXCLUIDAS}
print(f"\ncarpetas de data/ que van al sitio y que el comentario del workflow (l. 78-80) NO nombra como leidas por el tablero:")
for k, v in sorted(no_leidas.items(), key=lambda x: -x[1]):
    print(f"  {k:40s} {v/MB:8.1f} MB")
print(f"  suma: {sum(no_leidas.values())/MB:.1f} MB")
json.dump({"commit": commit, "data_total_mb": round(total_data/MB, 1), "por_carpeta_mb": {k: round(v/MB, 2) for k, v in por.items()},
           "excluidas_mb": round(excl/MB, 1), "frontend_mb": round(frontend/MB, 1), "imagenes_mb": round(imagenes/MB, 1),
           "csv_mb": round(csvs/MB, 1), "sitio_medido_git_mb": round(sitio_git/MB, 1),
           "no_leidas_por_tablero_mb": {k: round(v/MB, 2) for k, v in no_leidas.items()}},
          open(sys.argv[3] if len(sys.argv) > 3 else "m1_pages_tamano_salida.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
