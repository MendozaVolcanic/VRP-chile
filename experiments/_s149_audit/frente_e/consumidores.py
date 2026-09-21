# Frente E S149: para cada atributo en mayuscula de pipeline.profile, en que archivos de pipeline/ y scripts/run_pipeline.py
# aparece como palabra completa (frontera de palabra, A92) fuera de profile.py. Un 0 NO prueba que no se use (A89): se rotula.
import re, json, sys, io, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
perfil = json.load(open("experiments/_s149_audit/frente_e/perfil_mirova_equivalent.json", encoding="utf-8"))
files = [p for p in pathlib.Path("pipeline").glob("*.py") if p.name != "profile.py"] + [pathlib.Path("scripts/run_pipeline.py")]
src = {str(p): p.read_text(encoding="utf-8", errors="replace").splitlines() for p in files}
out = {}
for k in perfil:
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(k) + r"(?![A-Za-z0-9_])")
    hits = {}
    for f, lines in src.items():
        ls = [i + 1 for i, l in enumerate(lines) if pat.search(l) and not l.strip().startswith("#")]
        if ls: hits[pathlib.Path(f).name] = ls
    out[k] = hits
json.dump(out, open("experiments/_s149_audit/frente_e/consumidores.json", "w"), indent=1)
for k, h in out.items():
    print(k, "=", perfil[k] if not isinstance(perfil[k], (dict, list, str)) or len(str(perfil[k])) < 30 else "...", "|", {f: len(v) for f, v in h.items()} or "SIN CONSUMIDOR POR NOMBRE")
