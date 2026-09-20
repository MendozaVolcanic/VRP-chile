"""Mutaciones del control de censo.py sobre COPIAS temporales (no toca el original).
Cada copia escribe sus salidas en el directorio temporal; ROOT se fija al repo."""
import subprocess, sys, tempfile, json, io, hashlib
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "experiments/_s145_censo_cierres/censo.py"
orig = SRC.read_text(encoding="utf-8")
h0 = hashlib.md5(SRC.read_bytes()).hexdigest()
MUT = {
 "M0 sin cambio": [],
 "M1 PATRONES vaciado": [('PATRONES = [\n', 'PATRONES = []\n_X = [\n')],
 "M2 regex cerrada rota": [(r'("cerrada", r"\bCERRADAS?\b|\bCERRADO\b")', r'("cerrada", r"\bZZZZ\b")')],
 "M3 detector de control invertido": [("return [n for n, rx in PATRONES if re.search(rx, linea)]", "return [n for n, rx in PATRONES if not re.search(rx, linea)]")],
 "M4 detector del BUCLE PRINCIPAL invertido (el que produce las filas)": [("tipos = [n for n, rx in PATRONES if re.search(rx, linea)]", "tipos = [n for n, rx in PATRONES if not re.search(rx, linea)]")],
 "M5 bucle principal solo mira 'cerrada'": [("tipos = [n for n, rx in PATRONES if re.search(rx, linea)]", "tipos = [n for n, rx in PATRONES[:1] if re.search(rx, linea)]")],
 "M6 RESPALDOS vaciado": [('RESPALDOS = [\n', 'RESPALDOS = []\n_Y = [\n')],
 "M7 patron que marca todo": [(r'("menor", r"\bABIERTA, menor\b|\bprioridad baja\b|\bimpacto menor\b")', r'("menor", r".")')],
}
for name, subs in MUT.items():
    src = orig
    for a, b in subs:
        assert a in src, (name, a)
        src = src.replace(a, b, 1)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = src.replace("ROOT = HERE.parents[1]", f"ROOT = Path(r'{REPO}')")
        (td / "censo.py").write_text(src, encoding="utf-8")
        r = subprocess.run([sys.executable, str(td / "censo.py")], capture_output=True, text=True, encoding="utf-8")
        try:
            j = json.loads((td / "censo_cierres.json").read_text(encoding="utf-8"))
            c = j["control_de_instrumento"]
            print(f"{name:70} exit={r.returncode} ok={c['ok']} n={j['n_afirmaciones']} sin_resp={j['n_sin_respaldo_citable']}")
        except Exception as e:
            print(f"{name:70} exit={r.returncode} ERROR {e} {r.stderr[-200:]}")
assert hashlib.md5(SRC.read_bytes()).hexdigest() == h0
print("original intacto md5", h0)
