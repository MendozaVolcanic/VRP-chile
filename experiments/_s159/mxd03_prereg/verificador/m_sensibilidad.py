"""Verificador S159 MxD03: ¿puede la prueba M (solo bloquea) bloquear por un cambio de magnitud fisicamente
despreciable? Mide, en las alertas MODIS que K publica con VRP de MIROVA, en que lado de MIROVA cae K: si K esta
casi siempre SOBRE MIROVA, un X que sube la magnitud 1-3 % (lo medido en M) da d > 0 en casi todos los pares.
Simula d con X = K * f para f en {0.97, 1.0, 1.03} y bootstrap por bloques noche-volcan (mediana, 95 %).
Pregunta 1: con f = 1.0 d es 0 exacto: si el instrumento no diera 0 estaria roto (control de identidad).
Pregunta 2: control positivo f = 1.03 / 0.97 debe dar signos opuestos si K esta de un solo lado.
No reemplaza la calibracion D-27 del evaluador de D25 (no la reimplementa): es un aviso de poder."""
import collections, io, math, random, sys
from pathlib import Path
ROOT = Path(r"C:\vrp-trabajo\s159-pruebas")
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
from auto_audit_weekly import _coords_por_volcan
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
data, dl = Path(sys.argv[1]), Path(sys.argv[2])
ventana = ("2026-03-01", "2026-10-16")
filas = cargar_referencia_unificada(dl / "registro_vrp_consolidado.csv", dl / "registro_vrp_ocr.csv")
coords = _coords_por_volcan(); inner = bp.inner_desde_html()
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
bp.etiquetar(recs, por_vb, ns, nv)
pares = []
for r in recs:
    if r["b"] != "MODIS" or r["lab"] != "pos" or not r["pub"]: continue
    al = [f for f in bp.parear(por_vb[(r["vol"], "MODIS")], r["dt"], 120) if bp.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0]
    if not al or not r["disp"] or r["disp"] <= 0: continue
    m = max(f["vrp_mw"] for f in al)
    pares.append((r["vol"], r["noche"], float(r["disp"]), m))
print("pares (alerta publicada por K con VRP MIROVA > 0):", len(pares), dict(collections.Counter(p[0] for p in pares)))
sobre = sum(1 for p in pares if p[2] > p[3]); print(f"K sobre MIROVA: {sobre} de {len(pares)}; K/MIROVA mediana {sorted(p[2]/p[3] for p in pares)[len(pares)//2]:.3f}")
bloques = collections.defaultdict(list)
for i, p in enumerate(pares): bloques[(p[0], p[1])].append(i)
B = list(bloques.values()); rng = random.Random(7)
for f in (0.97, 1.0, 1.03):
    d = [abs(math.log10(k * f / m)) - abs(math.log10(k / m)) for _, _, k, m in pares]
    meds = []
    for _ in range(2000):
        idx = [i for b in (rng.choice(B) for _ in B) for i in b]
        s = sorted(d[i] for i in idx); meds.append(s[len(s) // 2])
    meds.sort()
    print(f"f={f}: mediana d {sorted(d)[len(d)//2]:+.4f}, IC95 [{meds[50]:+.4f}, {meds[1949]:+.4f}], n bloques {len(B)}")
