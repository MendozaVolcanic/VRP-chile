"""P2-03. ¿El manifiesto ata la LECTURA al commit del tag? Experimento en copia: se copia a una raíz falsa cada archivo
del manifiesto, se altera evaluar_f4.py (el que decide), se regenera su sha256 en la copia del manifiesto (lo que haría
un `--escribir` tras el cambio) y se llama comprobar(ruta, raiz) del módulo real.
Pregunta 1: si el manifiesto sí atara al tag, comprobar daría INDECIDIBLE aquí. Pregunta 2 (control positivo): la
misma copia alterada SIN regenerar el manifiesto tiene que dar INDECIDIBLE; si no, el instrumento está muerto.
No escribe en el árbol ni en el repo: todo en ./m03_raiz/."""
import json, shutil, sys, hashlib, importlib.util
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARB = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol")
C = ARB / "experiments/_s166_modd_f4"
spec = importlib.util.spec_from_file_location("mc", C / "manifiesto_candado_f4.py")
mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
m = json.loads((C / "MANIFIESTO_CANDADO_F4.json").read_text(encoding="utf-8"))
R = Path(__file__).resolve().parent / "m03_raiz"
if R.exists(): shutil.rmtree(R)

import subprocess
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
def desde_git(a):
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", REPO, "show", f"743e89c48:{a}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


faltan_arbol = []
for a in m["archivos"]:
    src = ARB / a
    if not src.exists():
        b = desde_git(a)
        if b is None:
            faltan_arbol.append(a); continue
        (R / a).parent.mkdir(parents=True, exist_ok=True); (R / a).write_bytes(b); continue
    (R / a).parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, R / a)
print("archivos del manifiesto:", len(m["archivos"]), "| ausentes del árbol extraído:", faltan_arbol)
print("tag/commit_tag en el manifiesto:", m.get("tag"), m.get("commit_tag"))
print("0) copia intacta:", mc.comprobar(C / "MANIFIESTO_CANDADO_F4.json", R)["estado"])
ev = R / "experiments/_s166_modd_f4/evaluar_f4.py"
ev.write_text(ev.read_text(encoding="utf-8").replace("def veredicto(res):", "def veredicto(res):\n    return 'PROPONER ADOPCIÓN'\n\ndef _veredicto_viejo(res):"), encoding="utf-8")
r1 = mc.comprobar(C / "MANIFIESTO_CANDADO_F4.json", R)
print("1) control positivo, evaluador alterado sin regenerar:", r1["estado"], list(r1["distintos"]))
m2 = json.loads(json.dumps(m)); m2["archivos"]["experiments/_s166_modd_f4/evaluar_f4.py"] = mc.sha256_lf(ev)
(R / "manifiesto_regenerado.json").write_text(json.dumps(m2), encoding="utf-8")
r2 = mc.comprobar(R / "manifiesto_regenerado.json", R)
print("2) evaluador alterado + manifiesto regenerado:", r2["estado"], "distintos:", list(r2["distintos"]))
