# T2. Pregunta 1: si el tachado estuviera roto (no tachara), ¿se veria? Si: el control positivo es una copia SIN tachar que contiene
# el token en el archivo (verificado antes de correr) y el resultado final lo busca.
# Pregunta 2: instrumento muerto -> si el script no corriera, el token seguiria en el archivo y el caso saldria SIGUE.
# Token FALSO de prueba, no es una credencial. Sobre scripts/tachar_secreto_log.py de cd8b7074f.
import os, subprocess, sys, pathlib, shutil, stat, json, base64
from urllib.parse import quote, quote_plus
PY = sys.executable
SC = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/arbol/scripts/tachar_secreto_log.py"
T = pathlib.Path("D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/medidas/tachar_tmp")
shutil.rmtree(T, ignore_errors=True); T.mkdir()
TOK = "eyJ0eXAiOiJKV1Qi/abc+def=.sig_ZZ-9"          # falso; con "/" "+" "=" para que las variantes difieran
def correr(env_tok, archivos, orden):
    for n, c in archivos.items():
        if isinstance(c, str): (T / n).write_text(c, encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("EARTHDATA_TOKEN", None)
    if env_tok is not None: env["EARTHDATA_TOKEN"] = env_tok
    return subprocess.run([PY, "-B", SC] + [str(T / n) for n in orden], capture_output=True, text=True, encoding="utf-8", env=env)
formas = {
 "literal": TOK, "url_quote": quote(TOK, safe=""), "url_quote_plus": quote_plus(TOK), "json_barra_escapada": TOK.replace("/", "\/"),
 "json_dumps": json.dumps(TOK)[1:-1], "base64": base64.b64encode(TOK.encode()).decode(), "partido_en_dos_lineas": TOK[:10] + "\n" + TOK[10:],
 "mayusculas": TOK.upper(),
}
for nombre, f in formas.items():
    assert f in f"x {f} y"  # trivial
    (T / "log.txt").write_text(f"linea previa\nBearer {f} fin\n", encoding="utf-8")
    antes = f in (T / "log.txt").read_text(encoding="utf-8")                       # control positivo: esta en el archivo
    r = correr(TOK, {}, ["log.txt"])
    despues = f in (T / "log.txt").read_text(encoding="utf-8")
    sale = (TOK in r.stdout + r.stderr) or (f in r.stdout + r.stderr)
    print(f"{nombre:24s} antes={antes} rc={r.returncode} sigue_en_archivo={despues} token_en_salida={sale}")
# fallo cerrado: log es directorio; cobertura se tacha igual; rc != 0
shutil.rmtree(T / "log.txt", ignore_errors=True); os.remove(T / "log.txt") if (T / "log.txt").is_file() else None
(T / "pipeline.log").mkdir(); (T / "cob.json").write_text(json.dumps({"m": TOK}), encoding="utf-8")
r = correr(TOK, {}, ["pipeline.log", "cob.json"])
print("directorio+cobertura: rc", r.returncode, "| cob tachada:", TOK not in (T / "cob.json").read_text(encoding="utf-8"), "| token en salida:", TOK in r.stdout + r.stderr)
print("   stdout:", r.stdout.strip().replace("\n", " || ")[:300])
# solo lectura: no se puede reescribir
(T / "ro.log").write_text("Bearer " + TOK, encoding="utf-8"); os.chmod(T / "ro.log", stat.S_IREAD)
r = correr(TOK, {}, ["ro.log"]); os.chmod(T / "ro.log", stat.S_IWRITE | stat.S_IREAD)
print("solo lectura: rc", r.returncode, "| sigue el token:", TOK in (T / "ro.log").read_text(encoding="utf-8"))
# token ausente / vacio / espacios
(T / "v.log").write_text("Bearer " + TOK, encoding="utf-8")
for etiqueta, valor in (("ausente", None), ("vacio", ""), ("espacios", "   ")):
    r = correr(valor, {}, ["v.log"])
    print(f"token {etiqueta}: rc {r.returncode} | archivo intacto: {(T / 'v.log').read_text(encoding='utf-8') == 'Bearer ' + TOK}")
# token con salto de linea final (strip)
(T / "s.log").write_text("Bearer " + TOK + " fin", encoding="utf-8")
r = correr(TOK + "\n", {}, ["s.log"]); print("token con salto final: rc", r.returncode, "| tachado:", TOK not in (T / "s.log").read_text(encoding="utf-8"))
# archivo inexistente
r = correr(TOK, {}, ["no_existe.log"]); print("archivo inexistente: rc", r.returncode)
