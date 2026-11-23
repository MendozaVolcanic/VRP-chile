# -*- coding: utf-8 -*-
"""S195: control de mutaciones de la zona A del laboratorio (paso 3), en copias del árbol, nunca en el worktree.

POR QUÉ. Una prueba que no cae cuando el código está mal no vigila nada (S156). Cada mutación es un error plausible
de la implementación o de su configuración; cuenta como ATRAPADA sólo si alguna prueba falla por aserción y ninguna da
error ni cae porque un subproceso no corrió (lección S152: una mutación que rompe todo no está atrapada, está caída).
Antes de las mutaciones corre el control sin mutar, que tiene que pasar entero.

Uso: python experiments/_s195_lab_paso3/mutar.py <carpeta_temporal> [nombre,nombre,...]
(salida: resultado_mutaciones.json aquí; con nombres corre sólo esas mutaciones, después del control, y agrega su
resultado al json que ya exista, para retomar una corrida cortada)
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[2]
PRUEBAS = ["tests/test_laboratorio_paso3_s195.py", "tests/test_laboratorio_paso1_s193.py",
           "tests/test_guard_laboratorio_no_mas_ciego_s147.py"]
COPIAR = ["pipeline", "tests", "scripts", "experiments/_s194_lab_zona_a", "experiments/_s195_lab_paso3",
          ".github/workflows", "frontend/index.html", "frontend/diario.html", "frontend/mosaico.html", "volcanoes.yaml"]
V = "pipeline/mirova_v750_codigo.py"
MUTACIONES = [
    ("piso_conservador_en_la_zona", V, "u_ntia = n2 if np.isnan(mu + s_a * sd) else max(mu + s_a * sd, n2)",
     "u_ntia = n2 if np.isnan(mu + s_a * sd) else max(mu + s_a * sd, n1)"),
    ("eti_sin_s_a", V, "u_etia = max(mu_e + s_a * sd_e, e2) if np.isfinite(mu_e + s_a * sd_e) else e2",
     "u_etia = max(mu_e + s2 * sd_e, e2) if np.isfinite(mu_e + s2 * sd_e) else e2"),
    ("umbrales_cruzados", V, "u_nti2 = np.where(zona_a, u_ntia, u_nti2)", "u_nti2 = np.where(zona_a, u_nti2, u_ntia)"),
    ("mascara_circulo_entero", V, "return (np.asarray(box) == 2) & (np.hypot(",
     "return (np.asarray(box) >= 0) & (np.hypot("),
    ("mascara_caja_entera", V, "q - pos_crater[1]) * paso_m / 1000.0 <= inner_km)",
     "q - pos_crater[1]) * paso_m / 1000.0 <= 1e9)"),
    ("zona_tambien_de_dia", V, "    if dayflag != 0 or s_a is None:", "    if s_a is None:"),
    ("cordon_caulle_dentro", V, "    if nombre_volcan in zona.get(\"volcanes_fuera\", []):\n        return None\n", ""),
    ("sin_tope_s2", V, "    if zona_a is not None and s_a > s2:", "    if False:"),
    ("zona_encendida_siempre", V, "    if not _perfil.ENABLE_LAB_ZONA_A:\n        return None\n",
     "    if not _perfil.ENABLE_LAB_ZONA_A:\n        return 1.0\n"),
    ("decisiva_sin_zona", V, "u_n, u_e = _umbral_de(dp, int(z), zona_a is not None and bool(zona_a[f, k]))",
     "u_n, u_e = _umbral_de(dp, int(z))"),
    ("perfil_encendida_sin_valor_carga", "pipeline/profile.py", "    if encendida and zona.get(\"valor\") is None:",
     "    if False:"),
    ("brazo_s45_con_valor_4", "pipeline/profiles/_s195_lab_s45.yaml", "  valor: 4.5", "  valor: 4.0"),
    ("brazo_s50_sin_b22", "pipeline/profiles/_s195_lab_s50.yaml", "enable_modis_b22_primary: true",
     "enable_modis_b22_primary: false"),
    # Encender la zona en el control sin valor hace que el perfil no cargue (G7, a propósito): todas las pruebas que lo
    # resuelven caen con error. Queda como «caída», no atrapada; la que sigue enciende la zona CON valor.
    ("control_con_zona", "pipeline/profiles/_s195_lab_control.yaml", "  enable_lab_zona_a: false",
     "  enable_lab_zona_a: true"),
    ("control_con_zona_y_valor_1", "pipeline/profiles/_s195_lab_control.yaml",
     (("  enable_lab_zona_a: false", "  enable_lab_zona_a: true"), ("  valor: null", "  valor: 1.0")), None),
    ("workflow_pushea_a_main", ".github/workflows/reproc-s195-lab-barrido.yml", "            if git push origin \"$RAMA\"; then",
     "            if git push origin main; then"),
    ("lectura_en_process_viirs", "pipeline/process_viirs.py", "\nimport ", "\nfrom pipeline.profile import LAB_ZONA_A  # noqa\nimport "),
    ("comparador_ignora_vrp", "experiments/_s195_lab_paso3/comparar_control.py",
     "DESCRIPTIVOS = (\"processed_utc\", \"first_processed_utc\", \"regimen\")",
     "DESCRIPTIVOS = (\"processed_utc\", \"first_processed_utc\", \"regimen\", \"vrp_mw\")"),
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


def main() -> int:
    tmp = Path(sys.argv[1])
    solo = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    salida = Path(__file__).parent / "resultado_mutaciones.json"
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
    for nombre, rel, viejo, nuevo in MUTACIONES:
        if solo is not None and nombre not in solo:
            continue
        arbol = tmp / nombre
        copiar(arbol)
        f = arbol / rel
        texto = f.read_text(encoding="utf-8")
        pares = viejo if isinstance(viejo, tuple) else ((viejo, nuevo),)   # una mutación puede cambiar varios textos
        for v, nv in pares:
            assert texto.count(v) >= 1, f"{nombre}: no encontré el texto a mutar en {rel}"
            texto = texto.replace(v, nv, 1)
        f.write_bytes(texto.encode("utf-8"))
        r = correr_pruebas(arbol)
        r["atrapada"] = r["por_asercion"] > 0 and r["caidas"] == 0
        res["mutaciones"][nombre] = r
        print(f"{nombre:34s} {'ATRAPADA' if r['atrapada'] else 'NO ATRAPADA'}  aserción={r['por_asercion']} "
              f"caídas={r['caidas']}  {r['resumen']}", flush=True)
        shutil.rmtree(arbol, ignore_errors=True)
        salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")   # parcial, por si se corta
    n = sum(r["atrapada"] for r in res["mutaciones"].values())
    print(f"ATRAPADAS: {n} de {len(res['mutaciones'])} corridas ({len(MUTACIONES)} definidas)")
    salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
