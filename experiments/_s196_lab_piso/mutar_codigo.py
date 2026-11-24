# -*- coding: utf-8 -*-
"""S196: control de mutaciones del código del piso de la zona A (paso 2), en copias del árbol, nunca en el worktree.

POR QUÉ. Una prueba que no cae cuando el código está mal no vigila nada (S156). Cada mutación es un error plausible
de la implementación del piso, de sus perfiles, del workflow o del comparador; cuenta como ATRAPADA sólo si alguna
prueba falla por aserción y ninguna da error ni cae porque un subproceso no corrió (lección S152: una mutación que
rompe todo no está atrapada, está caída). Antes de las mutaciones corre el control sin mutar, que tiene que pasar
entero, y entre las mutaciones va un CONTROL DE CAÍDA (`control_caida`: el módulo de la vía no importa) que tiene que
salir NO ATRAPADA; si saliera atrapada, el contador estaría contando caídas como aciertos.
Molde: experiments/_s195_lab_paso3/mutar.py. Distinto de experiments/_s196_lab_piso/mutar.py, que muta el evaluador.

Uso: python experiments/_s196_lab_piso/mutar_codigo.py <carpeta_temporal> [nombre,nombre,...] [--paralelo N]
(salida: resultado_mutaciones_codigo.json aquí; con nombres corre sólo esas mutaciones, después del control, y agrega
su resultado al json que ya exista, para retomar una corrida cortada)
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
PRUEBAS = ["tests/test_laboratorio_piso_s196.py", "tests/test_laboratorio_paso3_s195.py",
           "tests/test_laboratorio_paso1_s193.py", "tests/test_guard_laboratorio_no_mas_ciego_s147.py"]
COPIAR = ["pipeline", "tests", "scripts", "experiments/_s194_lab_zona_a", "experiments/_s195_lab_paso3",
          "experiments/_s196_lab_piso", ".github/workflows", "frontend/index.html", "frontend/diario.html",
          "frontend/mosaico.html", "volcanoes.yaml"]
V = "pipeline/mirova_v750_codigo.py"
C = "experiments/_s196_lab_piso/comparar_donde_no_actua.py"
W = ".github/workflows/reproc-s196-lab-piso.yml"
MUTACIONES = [
    # el piso de la zona no llega al umbral (los dos contrastes, o sólo uno: el .m exige NTI y ETI a la vez)
    ("piso_ignorado_en_la_zona", V, (("    pn = n2 if piso_a is None else piso_a", "    pn = n2"),
                                     ("    pe = e2 if piso_a is None else piso_a", "    pe = e2")), None),
    ("piso_ignorado_en_nti", V, "    pn = n2 if piso_a is None else piso_a", "    pn = n2"),
    ("eti_con_n2_en_vez_de_piso_a", V, "    pe = e2 if piso_a is None else piso_a", "    pe = n2"),
    # el piso se fuga fuera de la zona: a la región sensible entera (u_nti2) o al anillo (u_nti1)
    ("piso_fuera_de_la_zona_u_nti2", V, "    u_nti2 = max(mu + s2 * sd, n2)", "    u_nti2 = max(mu + s2 * sd, pn)"),
    ("piso_fuera_de_la_zona_u_nti1", V, "    u_nti1 = max(mu + s1 * sd, n1)             # l. 306-308",
     "    u_nti1 = max(mu + s1 * sd, pn)             # l. 306-308"),
    ("piso_fuera_de_la_zona_u_eti1", V, "    u_eti1 = max(mu_e + s1 * sd_e, e1) if np.isfinite",
     "    u_eti1 = max(mu_e + s1 * sd_e, pe) if np.isfinite"),
    ("guard_del_piso_apagado", V, "    if zona_a is not None and piso_a is not None and not 0 < piso_a <= min(n2, e2):",
     "    if False:"),
    ("u_a_persistido_siempre", V, "            if v is not None and np.isfinite(v) and round(float(v), 6) != out[k2]:",
     "            if v is not None and np.isfinite(v):"),
    ("piso_zona_a_ignora_volcanes_fuera", V,
     "    zona = _zona_a_activa(nombre_volcan)\n    p = None if zona is None else zona.get(\"piso\")",
     "    from . import profile as _p\n    zona = _p.LAB_ZONA_A if _p.ENABLE_LAB_ZONA_A else None\n"
     "    p = None if zona is None else zona.get(\"piso\")"),
    ("piso_no_llega_al_detector", V, "zona_a=zona_a, s_a=s_a, piso_a=piso_zona_a(nombre_volcan))",
     "zona_a=zona_a, s_a=s_a, piso_a=None)"),
    ("perfil_acepta_piso_no_positivo", "pipeline/profile.py",
     "        if p is not None and (isinstance(p, bool) or not isinstance(p, (int, float)) or not p > 0):",
     "        if False:"),
    ("brazo_p150_con_piso_0002", "pipeline/profiles/_s196_lab_p150.yaml", "  piso: 0.0015", "  piso: 0.002"),
    ("control_con_s3", "pipeline/profiles/_s196_lab_control.yaml", "  valor: 5.0", "  valor: 3.0"),
    ("sinzona_con_zona_y_piso", "pipeline/profiles/_s196_lab_sinzona.yaml",
     (("  enable_lab_zona_a: false", "  enable_lab_zona_a: true"), ("  valor: null", "  valor: 5.0\n  piso: 0.003")),
     None),
    ("workflow_sin_comparador_no_actua", W, "            python experiments/_s196_lab_piso/comparar_donde_no_actua.py",
     "            python experiments/_s195_lab_paso3/comparar_control.py"),
    ("comparador_no_ve_el_dia", C, "    return (rec.get(\"diag_codigo_mirova\") or {}).get(\"dayflag\") == 1",
     "    return False"),
    ("comparador_ignora_vrp", C, "DESCRIPTIVOS = (\"processed_utc\", \"first_processed_utc\", \"regimen\")",
     "DESCRIPTIVOS = (\"processed_utc\", \"first_processed_utc\", \"regimen\", \"vrp_mw\")"),
    # CONTROL DE CAÍDA: tiene que salir NO ATRAPADA (todas las pruebas que importan la vía caen con error)
    ("control_caida", V, "\nimport numpy as np\n", "\nraise ImportError('control de caida')\nimport numpy as np\n"),
]


def copiar(dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    for rel in COPIAR:
        src, dst = RAIZ / rel, dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "salidas"))
        else:
            shutil.copy2(src, dst)


def correr_pruebas(arbol: Path) -> dict:
    """Clasifica cada prueba por el XML de JUnit de pytest (el resumen -rfE con --tb=line no trae el mensaje)."""
    xml = arbol / "junit.xml"
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", *PRUEBAS, "-q", "-p", "no:cacheprovider", "--tb=short",
                            f"--junitxml={xml}"], cwd=arbol, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=7200)
    except subprocess.TimeoutExpired:
        return {"rc": None, "por_asercion": 0, "caidas": 1, "resumen": "timeout de 7200 s", "ejemplos": []}
    por_asercion, caidas = [], []
    if not xml.exists():
        return {"rc": r.returncode, "por_asercion": 0, "caidas": 1, "resumen": "sin junit.xml", "ejemplos": []}
    for caso in ET.parse(xml).getroot().iter("testcase"):
        nombre = caso.get("classname", "") + "::" + caso.get("name", "")
        for f in caso.findall("failure"):
            msg = (f.get("message") or "")
            # cae (no atrapa): excepción que no es aserción, o un subproceso que no corrió
            if re.match(r"(AssertionError|assert |Failed: DID NOT RAISE)", msg) and "no corrió" not in msg:
                por_asercion.append(nombre + " :: " + msg[:120])
            else:
                caidas.append(nombre + " :: " + msg[:120])
        for e in caso.findall("error"):
            caidas.append(nombre + " :: ERROR " + (e.get("message") or "")[:120])
    resumen = next((l for l in reversed(r.stdout.splitlines()) if " passed" in l or " failed" in l or " error" in l), "")
    return {"rc": r.returncode, "por_asercion": len(por_asercion), "caidas": len(caidas), "resumen": resumen,
            "ejemplos": (por_asercion + caidas)[:4]}


def mutar_y_correr(tmp: Path, nombre: str, rel: str, viejo, nuevo) -> dict:
    arbol = tmp / nombre
    copiar(arbol)
    f = arbol / rel
    texto = f.read_text(encoding="utf-8")
    pares = viejo if isinstance(viejo, tuple) else ((viejo, nuevo),)   # una mutación puede cambiar varios textos
    for v, nv in pares:
        assert texto.count(v) == 1, f"{nombre}: el texto a mutar aparece {texto.count(v)} veces en {rel}"
        texto = texto.replace(v, nv, 1)
    f.write_bytes(texto.encode("utf-8"))
    r = correr_pruebas(arbol)
    r["atrapada"] = r["por_asercion"] > 0 and r["caidas"] == 0
    shutil.rmtree(arbol, ignore_errors=True)
    return r


def main() -> int:
    args = sys.argv[1:]
    paralelo = 1
    if "--paralelo" in args:
        i = args.index("--paralelo")
        paralelo = int(args[i + 1])
        del args[i:i + 2]
    tmp = Path(args[0])
    solo = set(args[1].split(",")) if len(args) > 1 else None
    salida = Path(__file__).parent / "resultado_mutaciones_codigo.json"
    res = {"control": None, "mutaciones": {}}
    if solo and salida.exists():
        res = json.loads(salida.read_text(encoding="utf-8"))
    base = tmp / "control"
    copiar(base)
    res["control"] = correr_pruebas(base)
    print("control sin mutar:", res["control"]["resumen"], flush=True)
    if res["control"]["rc"] != 0:
        print("EL CONTROL NO PASA: las mutaciones no significan nada")
        return 2
    shutil.rmtree(base, ignore_errors=True)
    elegidas = [m for m in MUTACIONES if solo is None or m[0] in solo]
    with ThreadPoolExecutor(max_workers=paralelo) as ex:
        futuros = {m[0]: ex.submit(mutar_y_correr, tmp, *m) for m in elegidas}
        for nombre, fut in futuros.items():
            r = fut.result()
            res["mutaciones"][nombre] = r
            print(f"{nombre:36s} {'ATRAPADA' if r['atrapada'] else 'NO ATRAPADA'}  aserción={r['por_asercion']} "
                  f"caídas={r['caidas']}  {r['resumen']}", flush=True)
            salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")   # parcial
    reales = {k: v for k, v in res["mutaciones"].items() if k != "control_caida"}
    n = sum(r["atrapada"] for r in reales.values())
    caidas = sorted(k for k, r in reales.items() if not r["atrapada"] and r["caidas"])
    cc = res["mutaciones"].get("control_caida")
    print(f"ATRAPADAS POR ASERCIÓN: {n} de {len(reales)} mutaciones reales; caídas aparte: {caidas or 'ninguna'}")
    if cc is not None:
        print(f"CONTROL DE CAÍDA: {'NO ATRAPADA (bien: el contador no cuenta caídas)' if not cc['atrapada'] else 'ATRAPADA (MAL: el contador cuenta caídas)'}"
              f", caídas={cc['caidas']}")
    salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0 if cc is None or not cc["atrapada"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
