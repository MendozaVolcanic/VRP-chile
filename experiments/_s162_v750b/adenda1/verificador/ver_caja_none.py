# -*- coding: utf-8 -*-
"""Verificador: qué hacen el analizador sellado y el compañero con una caja None o {} en una pasada ok.
Uso: python ver_caja_none.py <evaluar_d25.py> <dest> <none|vacio|ausente>"""
import importlib.util, json, subprocess, sys
from pathlib import Path
ADE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("pa", ADE / "probar_adenda1.py"); PA = importlib.util.module_from_spec(spec); spec.loader.exec_module(PA)
ev, dest, modo = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
p = PA.Pob()
for n in range(4):
    p.pasada(f"2026-05-{10+n:02d} 05:00", "pos", 1.5)
for n in range(4):   # PCC: B0 pierde, B1 publica (control positivo)
    i = p.pasada(f"2026-05-{15+n:02d} 05:00", "pos", 1.5, volcan="PuyehueCordonCaulle")
    p.res[i]["oraculo"]["B0"] = PA.NOPUB
for n in range(60):
    p.pasada(f"2026-04-{1 + n % 28:02d} {n // 28:02d}:00")
i = p.pasada("2026-08-01 05:00", "neg_limpio")
if modo == "none":
    p.res[i]["oraculo"]["B2"] = None
elif modo == "vacio":
    p.res[i]["oraculo"]["B2"] = {}
elif modo == "ausente":
    del p.res[i]["oraculo"]["B2"]
d = dest / modo; d.mkdir(parents=True, exist_ok=True); p.escribir(d)
r = subprocess.run([sys.executable, str(ADE.parent / "analizar_v750b.py"), "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
   "--evaluador", ev, "--sin-granulo", str(d / "sin_granulo.json"), "--censo-omitido-solo-pruebas",
   "--leer-con-faltantes", "prueba del verificador", "--salida", str(d / "an.txt")], capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout + r.stderr
print("ANALIZADOR rc", r.returncode)
for l in out.splitlines():
    if l.startswith("== cobertura") or "observadas:" in l or "compuerta" in l or "Error" in l or "Traceback" in l or "SIN DATO" in l:
        print("  ", l[:230])
print(out[-600:] if r.returncode not in (0, 4, 5) else "")
rc, c, o = PA.companero(ADE / "cobertura_cajas_v750b.py", d)
print("COMPAÑERO rc", rc, c)
