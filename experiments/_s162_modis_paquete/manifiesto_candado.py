# -*- coding: utf-8 -*-
"""Manifiesto del candado de MOD-D (adenda 4, VCM-02 del verificador): el hash git (blob, con fin de línea LF) de cada
archivo del que dependen el arnés, el evaluador y sus pruebas.

POR QUÉ. El §10.3 del pre-registro promete un candado sobre el arnés y el evaluador, no sólo sobre el port. Sin esto,
un cambio en `probe_paquete.py`, `evaluar_paquete.py` o en uno de los módulos que importan (de MOD-B, de S159, de F/K)
entre el tag y la lectura no lo vería nadie. `pipeline/`, `scripts/`, `frontend/`, `volcanoes.yaml` y
`data/mirova_equivalent/` no van aquí: el workflow exige que sean iguales al main congelado.

CÓMO SE ARMA LA LISTA (no a mano): `escribir` importa el arnés y el evaluador en un proceso aparte y toma todo módulo
cargado desde `experiments/`, más los datos fijos que leen y el workflow. `comprobar` recalcula los hashes y devuelve
{"estado": "OK"|"INDECIDIBLE", ...}; lo llaman el workflow (antes de correr) y el evaluador (antes de decidir).

Las dos preguntas del instrumento: (1) si un archivo cambiara, ¿se vería? Sí: su hash cambia (prueba en
`probar_manifiesto`, que altera una copia). (2) Si el manifiesto estuviera vacío o le faltara un archivo, ¿se vería?
Sí: un manifiesto con menos de 20 archivos, sin el arnés o sin el evaluador, da INDECIDIBLE.
Uso: python manifiesto_candado.py --escribir | --comprobar
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MANIFIESTO = AQUI / "MANIFIESTO_CANDADO.json"
FIJOS = ["experiments/_s162_modis_paquete/grillas.json", "experiments/_s162_modis_paquete/PREREGISTRO.md",
         "experiments/_s162_mxd03/poblacion.json", "experiments/_s162_mxd03/MANIFIESTO.json",
         "experiments/_s162_mxd03/recorrer_en_sha.py", "experiments/_s162_mxd03/k_en_sha.py",
         "experiments/_s162_mxd03/poblacion_mxd03.py", "experiments/_s159/portes/objetivos_portes.json",
         "experiments/_s162_modis_paquete/probar_evaluar_paquete.py",
         "experiments/_s162_modis_paquete/probar_probe_paquete.py",
         "experiments/_s162_modis_paquete/evaluar_vacio.py", ".github/workflows/probe-s162-modd.yml",
         # los que se importan tarde (dentro de una funcion) y la sonda no ve, y los de prueba y medicion
         "experiments/_s162_modis_paquete/manifiesto_candado.py",
         "experiments/_s158_audit_r2/granulos/probe_granulos.py",
         "experiments/_s162_modis_paquete/mutar_evaluar_paquete.py",
         "experiments/_s162_modis_paquete/ensayo_en_seco.py"]
OBLIGATORIOS = ("experiments/_s162_modis_paquete/probe_paquete.py", "experiments/_s162_modis_paquete/evaluar_paquete.py",
                "experiments/_s159/portes/probe_portes.py", "experiments/_s159/portes/mirova_port.py")
SONDA = r"""
import sys, os, json
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, sys.argv[1])
import probe_paquete, evaluar_paquete
raiz = os.path.abspath(sys.argv[2])
print(json.dumps(sorted({os.path.abspath(m.__file__) for m in list(sys.modules.values())
                         if getattr(m, "__file__", None) and os.path.abspath(m.__file__).startswith(raiz)})))
"""


def blob(p):
    b = Path(p).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def lista():
    r = subprocess.run([sys.executable, "-I", "-c", SONDA, str(AQUI), str(RAIZ)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])
    mods = json.loads(r.stdout.strip().splitlines()[-1])
    rel = {Path(m).resolve().relative_to(RAIZ.resolve()).as_posix() for m in mods}
    rel = {x for x in rel if x.startswith("experiments/")}
    return sorted(rel | set(FIJOS) | {p.relative_to(RAIZ).as_posix() for p in
                                      sorted((AQUI / "referencia_s159").glob("resultados_MODIS_*.json"))})


def escribir():
    arch = lista()
    MANIFIESTO.write_text(json.dumps({a: blob(RAIZ / a) for a in arch}, indent=1) + "\n", encoding="utf-8")
    print("manifiesto:", len(arch), "archivos")


def comprobar(ruta=MANIFIESTO, raiz=RAIZ):
    try:
        m = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"estado": "INDECIDIBLE", "motivo": f"manifiesto ilegible: {e}"}
    faltan = [a for a in m if not (Path(raiz) / a).exists()]
    distintos = {a: blob(Path(raiz) / a) for a, h in m.items() if a not in faltan and blob(Path(raiz) / a) != h}
    incompleto = len(m) < 20 or any(o not in m for o in OBLIGATORIOS)
    ok = not faltan and not distintos and not incompleto
    return {"estado": "OK" if ok else "INDECIDIBLE", "n": len(m), "faltan": faltan, "distintos": distintos,
            "incompleto": incompleto}


def probar_manifiesto():
    """Una copia del manifiesto con un hash alterado tiene que dar INDECIDIBLE; uno vacío también."""
    import tempfile
    m = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        alt = dict(m)
        alt["experiments/_s162_modis_paquete/evaluar_paquete.py"] = "0" * 40
        p = Path(td) / "m.json"
        p.write_text(json.dumps(alt), encoding="utf-8")
        assert comprobar(p)["estado"] == "INDECIDIBLE", "un hash alterado no se vio"
        p.write_text("{}", encoding="utf-8")
        assert comprobar(p)["estado"] == "INDECIDIBLE", "un manifiesto vacio paso"
    return True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--escribir" in sys.argv:
        escribir()
    r = comprobar()
    print("comprobar:", {k: v for k, v in r.items() if k != "distintos"}, "distintos:", list(r.get("distintos", {}))[:10])
    print("prueba del manifiesto:", probar_manifiesto())
    sys.exit(0 if r["estado"] == "OK" else 1)
