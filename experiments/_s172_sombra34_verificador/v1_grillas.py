"""VS34 V-1: las 11 grillas no cambian y las 34 siguen la regla. Instrumento independiente del generador del autor:
reimplementa la proyeccion con pyproj directo (no importa generar_grillas_34).
Q1: si las 11 hubieran cambiado un byte, esta medicion lo ve (prefijo de bytes + dict por clave + control mutado).
Q2: si el instrumento estuviera muerto (p.ej. archivos vacios) fallaria en los asserts de longitud/conteo.
Ventana: archivos de la rama 30d9f9418 contra pre-s172-sombra-34 (main 14fb62030); volcanoes.yaml de la rama."""
import hashlib, subprocess, sys, math, itertools
import yaml
from pyproj import Transformer
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
W = "D:/vrp-trabajo/worktrees/s172-sombra34"
def show(ref, path):
    p = subprocess.run(["git", "-C", R, "show", f"{ref}:{path}"], capture_output=True)
    assert p.returncode == 0, p.stderr
    return p.stdout
old = show("pre-s172-sombra-34", "pipeline/grillas_mirova.yaml").replace(b"\r\n", b"\n")
new = show("30d9f9418", "pipeline/grillas_mirova.yaml").replace(b"\r\n", b"\n")
print("bytes viejo/nuevo:", len(old), len(new), "sha viejo", hashlib.sha256(old).hexdigest()[:16])
assert len(old) > 3000 and len(new) > len(old)
print("prefijo identico:", new.startswith(old), "| termina en LF el viejo:", old.endswith(b"\n"))
# control mutado: un byte cambiado en las 11 debe romper el prefijo
mut = bytearray(new); i = mut.find(b"692393.7"); mut[i] = ord("7")
print("control mutado (X0 de Chaiten 692393.7 -> 792393.7) rompe el prefijo:", not bytes(mut).startswith(old))
# claves duplicadas (yaml.safe_load se queda con la ultima sin avisar)
class Dup(yaml.SafeLoader): pass
dups = []
def cons(loader, node):
    keys = [loader.construct_object(k) for k, _ in node.value]
    for k, c in __import__("collections").Counter(keys).items():
        if c > 1: dups.append(k)
    return loader.construct_mapping(node)
Dup.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, cons)
gn = yaml.load(new.decode("utf-8"), Loader=Dup)["volcanes"]
go = yaml.safe_load(old.decode("utf-8"))["volcanes"]
print("claves duplicadas en el archivo nuevo:", dups)
print("11 viejas == 11 nuevas por clave:", all(gn[k] == go[k] for k in go), "| n viejas", len(go), "n nuevas", len(gn))
vols = yaml.safe_load(open(f"{W}/volcanoes.yaml", encoding="utf-8"))["volcanoes"]
nrt = set(yaml.safe_load(open(f"{W}/.github/workflows/nrt.yml", encoding="utf-8"))["jobs"]["process"]["strategy"]["matrix"]["volcano"])
print("nrt == las 11 con grilla vieja:", nrt == set(go), "| nombres yaml == claves nuevas:", {v['name'] for v in vols} == set(gn))
# regla independiente sobre las 34
bad = []
for v in vols:
    if v["name"] in go: continue
    e = gn[v["name"]]
    zona = 32700 + int((v["lon"] + 180) // 6) + 1
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{zona}", always_xy=True)
    x, y = t.transform(v["lon"], v["lat"])
    ok = (e["epsg"] == zona and abs(e["x0"] - x) < 0.06 and abs(e["y0"] - y) < 0.06 and e["centro_lat"] == round(v["lat"], 5)
          and e["centro_lon"] == round(v["lon"], 5) and e["roi_v750"] == "def")
    if not ok: bad.append((v["name"], e, zona, x, y))
print("34 que no siguen la regla (independiente):", bad)
# decimales de las coordenadas del yaml: 11 vs 34
def dec(x): s = repr(float(x)); return len(s.split(".")[1]) if "." in s else 0
print("decimales lat/lon yaml  Tier A:", sorted({max(dec(v['lat']), dec(v['lon'])) for v in vols if v['name'] in go}),
      " los 34:", sorted({max(dec(v['lat']), dec(v['lon'])) for v in vols if v['name'] not in go}))
print("Tier A coords yaml:", [(v['name'], v['lat'], v['lon']) for v in vols if v['name'] in go][:4])
# unicidad de coordenadas (volcan_por_coordenadas tol 1e-6)
mn = min(((abs(a['lat']-b['lat'])+abs(a['lon']-b['lon'])), a['name'], b['name']) for a, b in itertools.combinations(vols, 2))
print("par de volcanes mas cercano en grados (suma abs):", mn)
# frontera de zona -72
print("a menos de 0.15 deg de -72 O:", [(v['name'], v['lon'], gn[v['name']]['epsg']) for v in vols if abs(v['lon'] + 72) < 0.15])
print("lon>-72 con 32718 o lon<-72 con 32719:", [v['name'] for v in vols if (v['lon'] < -72) != (gn[v['name']]['epsg'] == 32718)])
