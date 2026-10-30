"""R6: scripts/tachar_secreto_log.py de f743d7b8f. Control positivo: con token en el log, lo tacha. Control de
instrumento muerto: el script se corre de verdad (subprocess) y se compara el contenido de los archivos, no el rc.
Denominador: casos sinteticos con un token FALSO inventado; ningun secreto real."""
import os, sys, subprocess, tempfile, json, urllib.parse, base64
ARBOL = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/arbol"
SCRIPT = ARBOL + "/scripts/tachar_secreto_log.py"
TOK = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQiOiJmYWxzbyJ9.FIRMA-falsa_123"
base = tempfile.mkdtemp(dir="D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas")
res = []


def corre(env_tok, archivos, contenidos, nombre):
    d = tempfile.mkdtemp(dir=base)
    for a, c in zip(archivos, contenidos):
        if c is not None:
            with open(os.path.join(d, a), "wb") as fh:
                fh.write(c)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    env.pop("EARTHDATA_TOKEN", None)
    if env_tok is not None:
        env["EARTHDATA_TOKEN"] = env_tok
    p = subprocess.run([sys.executable, "-B", SCRIPT] + archivos, cwd=d, capture_output=True, text=True, encoding="utf-8", env=env)
    salida = {a: (open(os.path.join(d, a), "rb").read() if os.path.isfile(os.path.join(d, a)) else None) for a in archivos}
    return p, salida


def chk(nombre, cond, extra=""):
    res.append(cond)
    print(("OK   " if cond else "MAL  ") + nombre + (" | " + extra if extra else ""))


t = TOK.encode()
# 1 control positivo
p, s = corre(TOK, ["pipeline.log", "cobertura.json"], [b"a\nAuthorization: Bearer " + t + b"\n", b'{"m": "' + t + b'"}'], "c1")
chk("control: token en log y en cobertura.json se tacha en ambos", all(t not in v and b"***" in v for v in s.values()) and p.returncode == 0)
chk("el stdout/stderr no repite el token", TOK not in p.stdout + p.stderr, p.stdout.strip().replace("\n", " / ")[:150])
# 2 sin token en el archivo
p, s = corre(TOK, ["pipeline.log"], [b"nada\n"], "c2")
chk("log sin token queda intacto", s["pipeline.log"] == b"nada\n" and p.returncode == 0)
# 3 token vacio
p, s = corre("", ["pipeline.log"], [b"Bearer " + t + b"\n"], "c3")
chk("token vacio: no toca nada y sale 0 (el token que estuviera en el log sigue ahi)", s["pipeline.log"] == b"Bearer " + t + b"\n" and p.returncode == 0, p.stdout.strip())
p, s = corre(None, ["pipeline.log"], [b"x\n"], "c3b")
chk("sin variable: sale 0 con aviso", p.returncode == 0, p.stdout.strip())
# 4 solo espacios
p, s = corre("   \n", ["pipeline.log"], [b"hola mundo\n"], "c4")
chk("token solo espacios: se trata como vacio, no destroza el log", s["pipeline.log"] == b"hola mundo\n")
# 5 token con espacio interior / saltos (token pegado con \n al final)
p, s = corre(TOK + "\n", ["pipeline.log"], [b"k=" + t + b"\n"], "c5")
chk("token con \\n final en el entorno: se tacha igual", t not in s["pipeline.log"])
# 6 variantes: url-encoded, base64 del token, token partido, token en JSON escapado, mayusculas
tok2 = "ab/cd+ef=gh.ij-kl_mn"
variantes = {
    "url-encoded": urllib.parse.quote(tok2, safe="").encode(),
    "base64(token)": base64.b64encode(tok2.encode()),
    "json escapado (\\/)": tok2.replace("/", "\\/").encode(),
    "token partido en 2 lineas": (tok2[:8] + "\n" + tok2[8:]).encode(),
    "literal": tok2.encode(),
}
for k, v in variantes.items():
    p, s = corre(tok2, ["pipeline.log"], [b"x " + v + b" y\n"], "c6")
    sigue = v in s["pipeline.log"]
    print(("INFO  tachado " if not sigue else "INFO  SIGUE   ") + "variante " + k)
# 7 caracteres de regex en el token (el script usa str.replace, no re)
tok3 = "a.b*c+d(e)[f]{g}|h^i$j"
p, s = corre(tok3, ["pipeline.log"], [b"x " + tok3.encode() + b" y a.b*c+d(e)[f]{g}|h^i$jZ\n"], "c7")
chk("token con metacaracteres de regex se tacha literal", tok3.encode() not in s["pipeline.log"])
# 8 bytes no UTF-8 en el log: se reemplazan por U+FFFD; el token (ASCII) se tacha
p, s = corre(TOK, ["pipeline.log"], [b"\xff\xfe raro " + t + b" \x80\n"], "c8")
chk("log con bytes no UTF-8: se tacha el token y el archivo se reescribe", t not in s["pipeline.log"] and p.returncode == 0)
print("INFO  bytes tras la reescritura:", s["pipeline.log"][:30])
# 9 archivo que falla: un directorio en lugar de archivo -> excepcion
d = tempfile.mkdtemp(dir=base)
os.mkdir(os.path.join(d, "pipeline.log"))
open(os.path.join(d, "cobertura.json"), "wb").write(b'{"m":"' + t + b'"}')
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", EARTHDATA_TOKEN=TOK)
p = subprocess.run([sys.executable, "-B", SCRIPT, "pipeline.log", "cobertura.json"], cwd=d, capture_output=True, text=True, encoding="utf-8", env=env)
cj = open(os.path.join(d, "cobertura.json"), "rb").read()
print("INFO  pipeline.log como directorio: rc=", p.returncode, "| cobertura.json quedo tachado:", t not in cj, "| stderr:", p.stderr.strip().splitlines()[-1:])
# 10 no existe pipeline.log -> se salta
p, s = corre(TOK, ["pipeline.log", "cobertura.json"], [None, b'{"m":"' + t + b'"}'], "c10")
chk("archivo inexistente se salta y el otro se tacha", t not in s["cobertura.json"] and p.returncode == 0)
# 11 token como argv: el script no lee argv para el token
chk("el script lee el token solo de os.environ (no de argv)", "sys.argv[1:]" in open(SCRIPT, encoding="utf-8").read() and "os.environ.get(\"EARTHDATA_TOKEN\")" in open(SCRIPT, encoding="utf-8").read())
print("FALLAN", res.count(False), "de", len(res))
sys.exit(1 if False in res else 0)
