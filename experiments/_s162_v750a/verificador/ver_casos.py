# -*- coding: utf-8 -*-
"""Verificador V750-A: escenarios MIOS (fuera de la bateria del autor) contra el analizador ORIGINAL, para comprobar
hallazgos concretos. Reusa Pob/base de probar_evaluar_v750a.py. Imprime las lineas que importan."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PADRE = AQUI.parent
sys.path.insert(0, str(PADRE))
spec = importlib.util.spec_from_file_location("probar", PADRE / "probar_evaluar_v750a.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
EV = sys.argv[1]
DEST = AQUI / "casos"
CLAVES = ("== §6", "== cobertura", "   observadas", "   protegidas", "   pasadas sin", "== compuerta", "== control",
          "== §6.1", "   SIN DATO", "Traceback", "KeyError", "TypeError", "   P distinto", "   S-1", "== S-1", "== sin veredicto")


def correr(nom, pob, fase="censo", args=(), sin_granulo=None, verde=P.VERDE):
    d = DEST / nom
    pob.escribir(d, verde=verde)
    if sin_granulo is not None:
        fo = d / "objetivos.json"
        sha = hashlib.sha256(fo.read_bytes()).hexdigest()
        (d / "sin_granulo.json").write_text(json.dumps({"objetivos_sha256": sha, "pasadas": sin_granulo}),
                                            encoding="utf-8")
    cmd = [sys.executable, str(PADRE / "evaluar_v750a.py"), "--fase", fase, "--art", str(d / "art"), "--objetivos",
           str(d / "objetivos.json"), "--evaluador", EV, "--sin-granulo", str(d / "sin_granulo.json"), "--salida",
           str(d / "salida.txt"), "--equivalencia-local", str(d / "equivalencia_local.txt")] + list(args)
    o = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = o.stdout + o.stderr
    (d / "stdout.txt").write_text(txt, encoding="utf-8")
    print(f"##### {nom} (rc {o.returncode})")
    for l in txt.splitlines():
        if l.startswith(CLAVES) or "Error" in l:
            print("  ", l[:420])
    sys.stdout.flush()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sel = sys.argv[2].split(",") if len(sys.argv) > 2 else None

    def quiere(n):
        return sel is None or n in sel

    # CA: la razon de M sin exigir K: 12 protegidas en O que K no publica y P publica al doble de MIROVA
    if quiere("CA"):
        def extra(pb):
            for n in range(12):
                pb.pasada(("Lascar", "Villarrica")[n % 2], f"2026-07-{15 + n:02d} 07:00", "pos", K=None, P=4.0,
                          mirova_vrp=2.0)
        correr("CA_razon_sin_K", P.base(extra=extra))

    # CB: estado None en un resultado
    if quiere("CB"):
        pb = P.base()
        pb.res[3]["estado"] = None
        correr("CB_estado_None", pb)

    # CC: sombra, P publica sin primary_cluster (record legado)
    if quiere("CC"):
        pb = P.esc_sombra()
        r = pb.res[0]["brazos"]["P"]["record"]
        r["primary_cluster"] = None
        r["vrp_mw"] = 2.0
        r["distance_class"] = "summit"
        correr("CC_sombra_sin_pc", pb, fase="sombra")

    # CD: una pasada sin granulo PROTEGIDA en el archivo del generador
    if quiere("CD"):
        correr("CD_sin_granulo_prot", P.base(), sin_granulo=[{"volcan": "Lascar", "hora_utc": "2026-04-10 06:10",
                                                              "protegida": True}])

    # CE: pasada fuera del granulo / sin cráter con protegida; y diurna
    if quiere("CE"):
        def extra(pb):
            pb.res[0]["estado"] = "volcan_fuera_del_granulo"
            pb.res[1]["cobertura"] = {"nan_7_crater": 3, "nan_crater": False}
            pb.res[2]["dayflag"] = 1
        correr("CE_fuera_sin_crater_diurna", P.base(extra=extra))

    # CF: diagnostico S-1 ausente en P de una pasada (SIN DATO)
    if quiere("CF"):
        def extra(pb):
            j = next(i for i, o in enumerate(pb.objs) if o["volcan"] == "PuyehueCordonCaulle")
            pb.res[j]["paquete"]["P"].pop("diag")
        correr("CF_sin_diag", P.base(extra=extra))

    # CG: Kgeo sin record
    if quiere("CG"):
        pb = P.base()
        pb.res[4]["brazos"]["Kgeo"] = {}
        correr("CG_kgeo_sin_record", pb)

    # CH: una alerta de MIROVA que deciden=False con P que no la publica
    if quiere("CH"):
        def extra(pb):
            pb.pasada("Villarrica", "2026-07-31 06:00", "pos", K=0.3, P=None, mirova_vrp=2.0)
            pb.objs[-1]["decide"] = False
        correr("CH_pos_no_decide", P.base(extra=extra))

    # CI: dos volcanes la misma noche, bloques noche-volcan: la prueba de signos por bloque
    if quiere("CI"):
        def extra(pb):
            for n in range(6):
                for vol in ("Lascar", "Villarrica"):
                    pb.pasada(vol, f"2026-05-{10 + n:02d} 05:00", "neg_limpio", K=0.2, P=None)
        correr("CI_dos_volcanes_misma_noche", P.base(negs_T="nada", extra=extra))

    # CJ: sombra sin ninguna protegida y sin negativos que importen: ¿CUMPLE vacio?
    if quiere("CJ"):
        pb = P.Pob()
        for n in range(8):
            pb.pasada("Lascar", f"2026-11-{4 + n:02d} 05:00", "neg_limpio", K=None, P=None)
        correr("CJ_sombra_vacia", pb, fase="sombra")

    # CK: sombra con una sola protegida y P2 sin sustrato
    if quiere("CK"):
        pb = P.Pob()
        pb.pasada("Lascar", "2026-11-04 06:00", "pos", K=1.0, P=2.0, mirova_vrp=2.0)
        for n in range(4):
            pb.pasada("Lascar", f"2026-11-{5 + n:02d} 05:00", "neg_limpio", K=None, P=None)
        correr("CK_sombra_una_prot", pb, fase="sombra")


main()
