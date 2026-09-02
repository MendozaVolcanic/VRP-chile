# -*- coding: utf-8 -*-
"""Guards S131 — «lo declarado coincide con lo efectivo» (regla B del protocolo de auditoría).

POR QUÉ. La auditoría S131 (docs/s131/agentes/DECLARADO_VS_EFECTIVO.md) midió 16 afirmaciones
FALSAS y 13 OBSOLETAS en los documentos vinculantes. Corregir el texto sin dejar un guard tiene
vida media de pocas sesiones (S127 corrigió A6 sin test; cuatro sesiones después había otras
cuatro citas drifteadas). Cada test de acá cierra un hallazgo por MEDICIÓN, no por prosa.

Principio de diseño: cuatro guards (G1, G2, G4, G6) DERIVAN la verdad del código en vez de fijar
una lista esperada — una lista copiada envejece, una condición derivada no. Los otros fijan
invariantes, no inventarios.

Prototipo original: experiments/_s131_audit/declarado_vs_efectivo/02_guards_propuestos.py.
"""
import glob
import json
import os
import re
import subprocess
import sys

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _leer(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()


@pytest.fixture(scope="module")
def flags_operacionales():
    """Flags ENABLE_* del perfil operacional, leídos de `pipeline.profile` (nunca del YAML, A89)."""
    code = ("import json,pipeline.profile as p;"
            "print(json.dumps({k:getattr(p,k) for k in dir(p) if k.startswith('ENABLE_')}))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT,
                         env={**os.environ, "VRP_PROFILE": "mirova_equivalent"})
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_g1_productos_nasa_declarados_existen_en_fetch():
    """Ningún documento publicable ni cabecera FICHA nombra un producto NASA que fetch.py no descarga.
    Cierra F1/F10: la ficha legal decía MOD14/MYD14 (producto de incendios)."""
    productos = set(re.findall(r'"short_name":\s*"([A-Z0-9_]+)"', _leer("pipeline/fetch.py")))
    assert productos, "fetch.py sin short_name: el guard no puede derivar la lista"
    vigilados = ["docs/FICHA_SDA_VRP_CHILE.md", "README.md"] + [
        os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "pipeline", "*.py"))]
    malos = []
    for f in vigilados:
        for cand in set(re.findall(r"\b(M[OY]D\d{2}[A-Z0-9]*)\b", _leer(f))):
            if cand not in productos and not cand.startswith(("MOD021", "MYD021", "MOD03", "MYD03")):
                # La FICHA puede NEGAR explícitamente el producto ("no consume ... MOD14")
                if f.endswith("FICHA_SDA_VRP_CHILE.md") and re.search(
                        r"no consume[^.]*" + cand, _leer(f)):
                    continue
                malos.append((f, cand))
    assert not malos, f"productos declarados que fetch.py no pide: {malos}"


def test_g2_mitigaciones_declaradas_en_ficha_estan_encendidas(flags_operacionales):
    """Toda mitigación que la FICHA declara como activa tiene su flag encendido en producción.
    Cierra F2/F3: «zonas de exclusión» y «mitigado normalizando por NTI» con los flags en False."""
    ficha = _leer("docs/FICHA_SDA_VRP_CHILE.md")
    ini = ficha.index("Evaluaciones de impacto")
    # Sólo el ítem de la ficha, no el historial de versiones (que cita el texto viejo por historia).
    fin = ficha.find("\n- **", ini + 1)
    bloque = ficha[ini:fin if fin > 0 else ini + 4000]
    mapa = {
        "zonas de exclusi": "ENABLE_EXCLUDE_ZONES",
        "mitigado normalizando por": "ENABLE_TEST1_NTI_INTEGRAL",
    }
    mal = [(frase, flag) for frase, flag in mapa.items()
           if frase in bloque and not flags_operacionales.get(flag, False)]
    assert not mal, f"la FICHA declara mitigaciones cuyo flag está apagado: {mal}"


def test_g3_sello_del_piso_implica_vrp_cero():
    """Invariante de store.py:99-103: `diag_vrp_floor_mw` se escribe junto con `vrp_mw = 0.0`.
    Un reproceso parcial (S130) restauró la magnitud y dejó el sello pegado en 1.635 records;
    S132 los limpió (tag `pre-s131-data-hygiene`) y desde entonces el guard corre en verde."""
    viol = tot = 0
    for f in glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for r in d.get("records", d):
            if r.get("diag_vrp_floor_mw") is not None:
                tot += 1
                if (r.get("vrp_mw") or 0) > 0:
                    viol += 1
    assert viol == 0, f"{viol} de {tot} records sellados por el piso tienen vrp_mw > 0"


def test_g4_pusher_a_main_tiene_push_main_o_retry():
    """Todo workflow que hace `git push` tiene `group: push-main` O su propio bucle de reintento.
    Mide la condición, no la lista de nombres (CLAUDE.md decía «6 workflows / 3 excepciones»)."""
    mal = []
    for f in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        txt = open(f, encoding="utf-8").read()
        if "git push" not in txt:
            continue
        grupo = (yaml.safe_load(txt).get("concurrency") or {}).get("group")
        retry = bool(re.search(r"for attempt in .*\n(?:.*\n){0,6}.*git push", txt))
        if grupo != "push-main" and not retry:
            mal.append(os.path.basename(f))
    assert not mal, f"pushean a main sin push-main ni retry: {mal}"


def test_g5_clave_on_quoted_en_todos_los_workflows():
    """A43 (Norway problem): `on` debe parsear como string, no como True."""
    mal = [os.path.basename(f) for f in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))
           if "on" not in yaml.safe_load(open(f, encoding="utf-8"))]
    assert not mal, f"'on' sin comillas (parsea como bool): {mal}"


def test_g6_index_lista_la_auditoria_mas_reciente():
    """docs/INDEX.md nombra la AUDIT_S<N>.md de mayor N presente en el directorio.
    Cuarta vez que se redescubre «INDEX congelado»; este guard es la única forma de que no haya quinta."""
    auds = [int(m.group(1)) for m in
            (re.search(r"AUDIT_S(\d+)", os.path.basename(f))
             for f in glob.glob(os.path.join(ROOT, "docs", "AUDIT_S*.md"))) if m]
    ultima = f"AUDIT_S{max(auds)}"
    assert ultima in _leer("docs/INDEX.md"), f"la última auditoría es {ultima} y no figura en docs/INDEX.md"


def test_g7_campo_con_flag_productor_apagado_queda_en_cero(flags_operacionales):
    """Un campo del schema no trae valor > 0 mientras su flag productor está OFF.
    Instancia: `vrp_tir_mw` con ENABLE_VRP_TIR_OUTPUT=False (README lo listaba como feature activa).
    Los 28 records de abril-2026 que lo violaban se limpiaron en S132."""
    if flags_operacionales.get("ENABLE_VRP_TIR_OUTPUT", True):
        pytest.skip("ENABLE_VRP_TIR_OUTPUT encendido: el invariante no aplica")
    nz = []
    for f in glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        nz += [(os.path.basename(f), r["datetime_utc"]) for r in d.get("records", d)
               if (r.get("vrp_tir_mw") or 0) > 0]
    assert not nz, f"{len(nz)} records con vrp_tir_mw > 0 y el flag apagado, p.ej. {nz[:3]}"


# Contrato explícito, no heurística: cada cita file:line que CLAUDE.md usa como evidencia.
CITAS_CLAUDE_MD = [
    ("scripts/run_pipeline.py", 234, "get_detection_anchor"),
    ("scripts/run_pipeline.py", 244, "local_kernel_bg"),
    ("pipeline/geo_utils.py", 29, "get_grid_center"),
    ("frontend/index.html", 1380, "isValidDetection"),
    ("pipeline/process_viirs.py", 80, "FLAG_DNS"),
    ("pipeline/process_viirs_mod.py", 416, "Villarrica/PP/Lastarria/Chaiten/PCC"),
    ("pipeline/process_viirs.py", 206, "compute_test1_nti"),
    ("pipeline/process_modis.py", 59, "compute_test1_mir"),
    ("pipeline/process_viirs_mod.py", 153, "compute_test1_mir"),
    ("scripts/build_c2ab_windows.py", 64, "registro_vrp_ocr.csv"),
]


@pytest.mark.parametrize("archivo,linea,token", CITAS_CLAUDE_MD)
def test_g8_citas_file_line_de_claude_md_apuntan_bien(archivo, linea, token):
    """Una cita `file:line` de CLAUDE.md sigue apuntando al símbolo que nombra.
    S127 corrigió A6 sin este test; cuatro sesiones después había cuatro citas drifteadas."""
    lineas = _leer(archivo).splitlines()
    assert linea <= len(lineas), f"{archivo} tiene {len(lineas)} líneas, la cita dice {linea}"
    assert token in lineas[linea - 1], f"{archivo}:{linea} ya no contiene {token!r}: {lineas[linea - 1].strip()[:90]}"
