import sys, importlib.util, subprocess
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
AQUI = Path(__file__).resolve().parent
PADRE = AQUI.parent
sys.path.insert(0, str(PADRE))
spec = importlib.util.spec_from_file_location("probar", PADRE / "probar_evaluar_v750a.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
src = (PADRE / "evaluar_v750a.py").read_text(encoding="utf-8")
v = 'if etiqueta(obj[i], canal) == "prot" and en_ventana(obj[i], v) and pub(i, b)'
assert src.count(v) == 1
copia = PADRE / "_ver_V38CA_evaluar_v750a.py"
copia.write_text(src.replace(v, v + ' and pub(i, "K")'), encoding="utf-8")
try:
    def extra(pb):
        for n in range(12):
            pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-07-{15 + n:02d} 07:00", "pos", K=None, P=4.0, mirova_vrp=2.0)
    d = AQUI / "casos" / "CA_V38"
    pb = P.base(extra=extra)
    pb.escribir(d)
    cmd = [sys.executable, str(copia), "--fase", "censo", "--art", str(d / "art"), "--objetivos", str(d / "objetivos.json"),
           "--evaluador", sys.argv[1], "--sin-granulo", str(d / "sin_granulo.json"), "--salida", str(d / "salida.txt"),
           "--equivalencia-local", str(d / "equivalencia_local.txt")]
    o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for l in (o.stdout + o.stderr).splitlines():
        if l.startswith(("== §6 censo", "== §6.2 ventana O")) or "Error" in l:
            print(l[:330])
finally:
    copia.unlink(missing_ok=True)
