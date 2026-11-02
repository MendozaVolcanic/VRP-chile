"""VS34 V-2/V-3: tamano de un record de la via (json.dump indent=2 como pipeline/store.py:255), con y sin alertados, y
proyeccion del crecimiento de data/sombra_34/ y su efecto en el sitio de Pages (pages-deploy.yml hace cp -r data _site/data).
ESTIMACION: records/dia salen de los K de los 11 (Villarrica, ago-oct 2026), no de los 34. Q1: si el record fuera grande lo veria.
Q2: si el instrumento fallara, el tamano seria 0 o None y se imprime."""
import sys, os, json, subprocess, collections
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "D:/vrp-trabajo/worktrees/s172-sombra34"); sys.path.insert(0, "D:/vrp-trabajo/temporales/ver_s172_sombra34")
import numpy as np, yaml
exec(open("v4_vecinos_sintetico.py", encoding="utf-8").read().split("pares = [")[0])   # reutiliza granulo()/correr
v = vols["Hudson"]
def rec(focos, fam="VIIRS375"):
    rad, LA, LO, ang = granulo(v["lat"], v["lon"], fam, focos)
    r = MV.calcular_vrp_granulo(rad, LA, LO, ang, "Hudson", v["lat"], v["lon"], None, "VIIRS_SNPP", familia=fam)
    r.update({"granule": "VNP02IMG.A2026302.0536.002.2026302140919.nc", "product_version": "nrt", "datetime_utc": "2026-11-04 05:36",
              "processed_utc": "2026-11-04T16:57:05Z", "first_processed_utc": "2026-11-04T09:13:16Z",
              "regimen": {"perfil": "sombra_34", "codigo_sha": "a" * 40, "origen": "actions"}})
    return r
for nombre, focos in (("sin alertados", []), ("1 foco", [(v["lat"], v["lon"], 320.0)]), ("foco grande (cluster)", [(v["lat"] + d * 0.003, v["lon"], 330.0) for d in range(-6, 7)])):
    r = rec(focos); s = json.dumps(r, indent=2, ensure_ascii=False)
    print(f"record {nombre:22s}: n_anom={r['n_anomalous_pixels']:3d} bytes={len(s.encode()):6d}")
sin = len(json.dumps(rec([]), indent=2).encode())
# records por dia y volcan: K de Villarrica (ago-oct 2026) como proxy
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
d = json.loads(subprocess.run(["git", "-C", R, "show", "14fb62030:data/mirova_equivalent/Villarrica.json"], capture_output=True).stdout)
rs = [r for r in d["records"] if "2026-08-01" <= r["datetime_utc"][:10] <= "2026-10-31"]
dias = len({r["datetime_utc"][:10] for r in rs})
print(f"proxy Villarrica K ago-oct 2026: {len(rs)} records en {dias} dias con datos = {len(rs)/92:.1f} records/dia (denominador 92 dias)")
por_dia = len(rs) / 92
for nombre, tam in (("vacio", sin),):
    mb_dia_34 = por_dia * tam * 34 / 1e6
    print(f"34 volcanes x {por_dia:.1f} records/dia x {tam} B = {mb_dia_34:.2f} MB/dia = {mb_dia_34*365:.0f} MB/ano (cota baja: records sin alertados)")
    mb_dia_11 = por_dia * tam * 11 / 1e6
    print(f"(sombra de los 11 igual: {mb_dia_11*365:.0f} MB/ano)")
# crecimiento observado de data/mirova_equivalent (K): 173.8 MB en el corpus; records totales
tot = sum(len(json.loads(subprocess.run(["git","-C",R,"show",f"14fb62030:data/mirova_equivalent/{n}.json"],capture_output=True).stdout)["records"]) for n in ("Villarrica",))
print("Villarrica K records totales:", tot)
