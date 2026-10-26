# -*- coding: utf-8 -*-
"""Verificador: las mutaciones propias (_fz_Vn.py) contra el oráculo del §4 de ver_fuzz.py, en proceso (rápido).
Mide si cada mutación es NO equivalente (alguna población distingue) y si el diferencial aleatorio la mata.
Uso: python ver_fuzz_mut.py <dest> [n] [semilla]"""
import contextlib, importlib.util, io, random, re, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
def cargar(ruta, nombre):
    s = importlib.util.spec_from_file_location(nombre, ruta); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
FZ = cargar(AQUI / "ver_fuzz.py", "fz"); PA = FZ.PA
dest = Path(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 120; sem = int(sys.argv[3]) if len(sys.argv) > 3 else 5
rng = random.Random(sem)
pobs = []
for k in range(n):
    p = FZ.poblacion(rng, con_faltas=True)
    sg_modo = rng.choice(["valido"] * 8 + ["ajeno", "ausente"])
    sin_g = [{"volcan": "Lascar", "hora_utc": f"2027-01-{j+1:02d} 05:00", "protegida": rng.random() < 0.3} for j in range(rng.randint(1, 3))] if rng.random() < 0.4 else []
    d = dest / f"p{k:03d}"; d.mkdir(parents=True, exist_ok=True)
    p.escribir(d, sin_granulo=sin_g, sha_ajeno=(sg_modo == "ajeno"))
    if sg_modo == "ausente": (d / "sin_granulo.json").unlink()
    pobs.append((d, p, sin_g if sg_modo == "valido" else [], sg_modo == "valido"))
# borde exacto 2 % (2 sin caja de 100, ninguna protegida)
q = PA.Pob()
for i in range(4): q.pasada(f"2026-05-{10+i:02d} 05:00", "pos", 1.5)
for i in range(94): q.pasada(f"2026-04-{1 + i % 28:02d} {i // 28:02d}:00")
for i in range(2): q.pasada(f"2026-08-{1+i:02d} 05:00", sin_caja=("B3",))
d = dest / "borde"; d.mkdir(parents=True, exist_ok=True); q.escribir(d)
pobs.append((d, q, [], True))
def correr(ruta):
    m = cargar(ruta, "m_" + Path(ruta).stem)
    mal = 0
    for d, p, sg_ef, sg_ok in pobs:
        sys.argv = ["c", "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"), "--sin-granulo", str(d / "sin_granulo.json")]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = m.main()
        out = buf.getvalue()
        t = re.search(r"SIN DATO total: (\d+) \(analizador sellado (\d+), sin gránulo (\d+), falta caja (\d+)\)", out)
        c = re.search(r"== cobertura con las cajas: (SUFICIENTE|INSUFICIENTE)", out)
        o_total, o_sin, o_falta, o_cob = FZ.oraculo(p, sg_ef, sg_ok)
        if (int(t.group(1)), int(t.group(2)), int(t.group(4)), c.group(1)) != (o_total, o_sin, o_falta, o_cob) or rc != (0 if o_cob == "SUFICIENTE" else 3):
            mal += 1
    return mal
orig = AQUI.parent / "cobertura_cajas_v750b.py"
print("original:", correr(orig), "de", len(pobs), "poblaciones difieren del oráculo")
for f in sorted(AQUI.glob("_fz_V*.py"), key=lambda x: int(re.search(r"V(\d+)", x.name).group(1))):
    print(f.stem, "difiere en", correr(f), "de", len(pobs))
