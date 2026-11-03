# -*- coding: utf-8 -*-
"""Escribe las mutaciones propias como archivos _fz_Vn.py (persistentes) para correr ver_fuzz.py --companero sobre ellas."""
import importlib.util, re, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vm", Path(__file__).with_name("ver_mutar.py")); VM = importlib.util.module_from_spec(spec); spec.loader.exec_module(VM)
src = VM.ORIG.read_text(encoding="utf-8")
src = src.replace("sys.path.insert(0, str(AQUI.parent))", f"sys.path.insert(0, {str(VM.V750B)!r})").replace("AQUI = Path(__file__).resolve().parent", f"AQUI = Path({str(VM.ADE)!r})")
for nombre, viejo, nuevo in VM.MUT:
    if viejo is None: continue
    cod = nombre.split(" ")[0]
    (VM.AQUI / f"_fz_{cod}.py").write_text(src.replace(viejo, nuevo), encoding="utf-8")
print("ok")
