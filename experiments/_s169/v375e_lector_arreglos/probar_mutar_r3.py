# -*- coding: utf-8 -*-
"""S169 ronda 3: prueba barata de mutar_sombra.py sin correr la batería (subprocess.run reemplazado).
Ve: TimeoutExpired -> CAIDA (VL2-01); retoma saltándose las escritas y escribe cada línea al terminar (VL2-01);
aborta con rc 2 si la identidad falla o si un control no sale CAIDA (VL2-02); rc 1 si sobrevive una no equivalente."""
import importlib.util
import subprocess
import sys
import types
from pathlib import Path

RAIZ = Path(sys.argv[1])
sp = importlib.util.spec_from_file_location("m", RAIZ / "experiments/_s168/v375e_sombra/mutar_sombra.py")
M = importlib.util.module_from_spec(sp)
sp.loader.exec_module(M)
RES = []


def chk(n, c, d=""):
    RES.append(bool(c))
    print(("PASA " if c else "FALLA"), n, "" if c else d, flush=True)


real_run = subprocess.run


def fake_factory(comport):
    """comport(dir) -> (rc, stdout) o 'timeout'."""
    def fake(cmd, **kw):
        if cmd and cmd[0] == "git":
            return real_run(cmd, **kw)
        r = comport(Path(cmd[-1]).name)
        if r == "timeout":
            raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
        return types.SimpleNamespace(returncode=r[0], stdout=r[1], stderr="")
    return fake


M.subprocess.run = fake_factory(lambda d: "timeout")
chk("TimeoutExpired es CAIDA y no lanza", M.correr(Path("x"))[0] == "CAIDA")
chk("el tope es 5400 s", M.TOPE_S == 5400)

salida = M.AQUI / "mutar_sombra_salida.txt"
assert not salida.exists(), "el archivo real de resultados ya existe: no se toca"
orig_aqui_salida = None
tmp = Path(sys.argv[2])
tmp.mkdir(parents=True, exist_ok=True)


REAL_AQUI, REAL_RAMA = M.AQUI, M.en_la_rama


def correr_main(comport, *args):
    M.subprocess.run = fake_factory(comport)
    if M.en_la_rama is REAL_RAMA:
        M.en_la_rama = lambda: (True, "claude/s169-v375e-lector")
    M.AQUI = tmp          # el archivo de resultados va al temporal; LS y probar_sombra no se leen (fake)
    M.preparar = lambda d, mut=None: d.mkdir(parents=True, exist_ok=True)
    M.comprobar_unicas = lambda: []
    orig = sys.stdout
    try:
        return M.main(list(args))
    finally:
        GUARDA.append(sys.stdout)     # main envuelve sys.stdout: se guarda para que el GC no cierre el buffer
        sys.stdout = orig


GUARDA = []


ok = lambda d: (0, "RESULTADO: 1 de 1\n")
cae = lambda d: (2, "CAE    sección «x»: E\nRESULTADO: 1 de 1; CAIDAS: 1\n")
atr = lambda d: (1, "FALLA  algo\nRESULTADO: 0 de 1\n")


def comp_bueno(d):
    if d.endswith("identidad"):
        return ok(d)
    if d.endswith("control") or d.endswith("control_seccion"):
        return cae(d)
    if d.endswith("M01"):
        return "timeout"
    if d.endswith("M02") or d.endswith("V04"):
        return ok(d)      # sobrevive
    return atr(d)


f = tmp / "mutar_sombra_repaso_salida.txt"   # con --solo el nulo escribe el archivo de repaso
if f.exists():
    f.unlink()
rc = correr_main(comp_bueno, "--solo", "M01,M02,M03,V04")
txt = f.read_text(encoding="utf-8")
chk("con una no equivalente viva sale 1", rc == 1, rc)
chk("cada mutación quedó escrita, M01 como CAIDA por el tope", "MUT M01 CAIDA" in txt and "MUT M03 ATRAPADA" in txt
    and "MUT M02 SOBREVIVE" in txt and "MUT V04 SOBREVIVE" in txt, txt)
# retoma: una segunda corrida no vuelve a correr las ya escritas
vistas = []


def comp_contar(d):
    vistas.append(d)
    return comp_bueno(d)


rc2 = correr_main(comp_contar, "--solo", "M01,M02,M03,V04,M04")
chk("retoma: la segunda corrida sólo corre identidad, controles y la mutación nueva",
    sorted(v.replace("_mut_sombra_", "") for v in vistas) == ["M04", "control", "control_seccion", "identidad"], vistas)
chk("retoma: el resumen cuenta todo el archivo", "RESULTADO: 2 de 5" in f.read_text(encoding="utf-8").splitlines()[-1],
    f.read_text(encoding="utf-8").splitlines()[-1])
# abortos
f.unlink()
rc3 = correr_main(lambda d: atr(d), "--solo", "M01")
chk("identidad que falla: aborta con 2 sin mutar", rc3 == 2 and "ABORTA" in f.read_text(encoding="utf-8")
    and "MUT " not in f.read_text(encoding="utf-8"))
f.unlink()
rc4 = correr_main(lambda d: ok(d), "--solo", "M01")
chk("un control que no sale CAIDA: aborta con 2 sin mutar", rc4 == 2 and "ABORTA: CONTROL no sale CAIDA"
    in f.read_text(encoding="utf-8") and "MUT " not in f.read_text(encoding="utf-8"))
f.unlink()
rc5 = correr_main(lambda d: comp_bueno(d) if not d.endswith("M01") else atr(d), "--solo", "M01,V04")
chk("sólo sobrevive la equivalente: sale 0", rc5 == 0, rc5)
fa = tmp / "mutar_sombra_arranque_salida.txt"
rc6 = correr_main(comp_contar, "--arranque")
chk("--arranque: identidad y controles, sale 0, escribe en _arranque y no muta", rc6 == 0 and fa.exists()
    and "ARRANQUE OK" in fa.read_text(encoding="utf-8") and "MUT " not in fa.read_text(encoding="utf-8"))
M.en_la_rama = lambda: (False, "loop/activo")
f.unlink()
rc7 = correr_main(comp_bueno, "--solo", "M01")
chk("fuera de la rama: aborta con 2 antes de la identidad", rc7 == 2 and "ABORTA: no corre en un checkout"
    in f.read_text(encoding="utf-8") and "IDENTIDAD" not in f.read_text(encoding="utf-8"))
M.AQUI = REAL_AQUI
M.subprocess.run = real_run
chk("en este checkout en_la_rama da sí", REAL_RAMA()[0], REAL_RAMA())
print(f"RESULTADO: {sum(RES)} de {len(RES)}")
sys.exit(0 if all(RES) else 1)
