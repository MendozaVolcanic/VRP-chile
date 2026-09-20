# -*- coding: utf-8 -*-
"""OJO: M5 quita la guarda y el test real intenta escribir en data/mirova_equivalent/x; si se corre M5 hay que borrar esa carpeta despues (ya paso una vez, se limpio y se verifico md5 de los records).
V-17c: mutaciones sobre COPIAS (en el scratchpad) de scripts/clasificacion_referencia.py; los originales no se tocan.
Cada mutante se corre contra una copia del test cuyo unico cambio es de donde importa el modulo.
(1) roto? control: el mutante M0 (sin cambio) debe pasar 12/12; si no pasa, el arnes esta roto.
(2) muerto? se imprime passed/failed por mutante; un arnes muerto daria lo mismo en todos."""
import os, re, shutil, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
S = sys.argv[1]
src = open(os.path.join(ROOT, "scripts", "clasificacion_referencia.py"), encoding="utf-8").read()
cli = open(os.path.join(ROOT, "scripts", "clasificar_referencia.py"), encoding="utf-8").read()
tst = open(os.path.join(ROOT, "tests", "test_clasificacion_referencia_s146.py"), encoding="utf-8").read()
RL = repr(ROOT)
MUT = {
 "M0 sin cambio": [],
 "M1 precedencia: fuera-de-limite antes que misma-noche": [('    if alerta_esa_noche:\n        return "mirova_same_night"\n    if lab == "far_ref":\n        return "mirova_saw_outside"\n',
                                                   '    if lab == "far_ref":\n        return "mirova_saw_outside"\n    if alerta_esa_noche:\n        return "mirova_same_night"\n')],
 "M2 silencio y sin-dato intercambiados": [('    if lab == "neg_limpio":\n        return "mirova_silent"\n    return "no_reference"', '    if lab == "neg_limpio":\n        return "no_reference"\n    return "mirova_silent"')],
 "M3 sin dato -> silencio (todo lo no pareado es 'miro y callo')": [('    return "no_reference"\n\n\ndef clasificar', '    return "mirova_silent"\n\n\ndef clasificar')],
 "M4 misma-noche ignorada": [('    if alerta_esa_noche:\n', '    if False:\n')],
 "M5 guarda de escritura eliminada": [('        raise SystemExit("ERROR: la salida no puede vivir dentro', '        pass  # raise SystemExit("ERROR: la salida no puede vivir dentro')],
 "M6 hora de generacion en la salida": [('"ventana_ultima_corrida": list(ventana),', '"ventana_ultima_corrida": list(ventana), "generado": __import__("time").time(),')],
 "M7 etiqueta con palabra prohibida": [('"Solo nuestro: MIROVA miro', '"Posible artefacto: MIROVA miro')],
 "M8 pareo por noche de VOLCAN deja de usarse (usa noche vacia)": [('nv = noche_volcan.get((r["vol"], r["noche"]), {"alerta": False})', 'nv = {"alerta": False}')],
}
SOLO = sys.argv[2:]  # prefijos de mutantes a correr; vacio = todos
for nom, cambios in MUT.items():
    if SOLO and nom[:2] not in SOLO: continue
    d = os.path.join(S, "mut"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    m = src.replace("ROOT = Path(__file__).resolve().parents[1]", f"ROOT = Path({RL})")
    assert m != src
    for a, b in cambios:
        assert a in m, (nom, "patron no encontrado"); m = m.replace(a, b)
    open(os.path.join(d, "clasificacion_referencia.py"), "w", encoding="utf-8").write(m)
    open(os.path.join(d, "clasificar_referencia.py"), "w", encoding="utf-8").write(cli)
    t = tst.replace("ROOT = Path(__file__).resolve().parents[1]", f"ROOT = Path({RL})")
    t = t.replace('sys.path.insert(0, str(ROOT / "scripts"))', f'sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, {d!r})')
    t = t.replace('SCRIPT = ROOT / "scripts" / "clasificar_referencia.py"', f'SCRIPT = Path({d!r}) / "clasificar_referencia.py"')
    open(os.path.join(d, "test_mut.py"), "w", encoding="utf-8").write(t)
    r = subprocess.run([sys.executable, "-m", "pytest", "test_mut.py", "-q", "-p", "no:cacheprovider", "--no-header", "-x" if False else "-q", "--rootdir", d],
                       cwd=d, capture_output=True, text=True, timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    fall = re.findall(r"^FAILED \S+::(\S+)", r.stdout, re.M) + re.findall(r"^ERROR \S+::(\S+)", r.stdout, re.M)
    print(f"{nom:70s} -> {r.stdout.strip().splitlines()[-1]}  {fall}")
shutil.rmtree(os.path.join(S, "mut"), ignore_errors=True)
