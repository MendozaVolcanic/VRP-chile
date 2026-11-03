# -*- coding: utf-8 -*-
import contextlib, importlib.util, io, re, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
def cargar(ruta, nombre):
    s = importlib.util.spec_from_file_location(nombre, ruta); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
PA = cargar(AQUI.parent / "probar_adenda1.py", "pa")
p = PA.Pob()
for i in range(4): p.pasada(f"2026-05-{10+i:02d} 05:00", "pos", 1.5)
for i in range(143): p.pasada(f"2026-04-{1 + i % 28:02d} {i // 28:02d}:00")
for i in range(2): p.pasada(f"2026-08-{1+i:02d} 05:00", estado="error_K")   # 149 objetivos, 2 error_K
d = AQUI / "tmp_v4"; d.mkdir(exist_ok=True)
p.escribir(d, sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-08-15 05:00", "protegida": False}])  # 1 sin gránulo -> 3 SIN DATO, den 150
for nom, ruta in (("original", AQUI.parent / "cobertura_cajas_v750b.py"), ("V4", AQUI / "_fz_V4.py")):
    m = cargar(ruta, "m_" + nom); sys.argv = ["c", "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"), "--sin-granulo", str(d / "sin_granulo.json")]
    b = io.StringIO()
    with contextlib.redirect_stdout(b): rc = m.main()
    print(nom, "rc", rc, re.search(r"SIN DATO total: .*", b.getvalue()).group(0)[:70], re.search(r"== cobertura con las cajas: (\w+)", b.getvalue()).group(1))
