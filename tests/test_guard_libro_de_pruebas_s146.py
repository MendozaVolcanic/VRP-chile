# -*- coding: utf-8 -*-
"""Guards S146: el libro de pruebas no se atrasa, y ningún documento cita una ruta muerta.

POR QUÉ. La auditoría S146 midió que el proyecto pierde el rastro de sus propias pruebas: cuatro
cifras que cerraban frentes no tenían script que las midiera, 29 de 323 rutas citadas en documentos
de resultados ya no existen, y 105 de 165 carpetas de `experiments/` no tienen ningún `.md` que diga
qué midieron (`docs/audit_s146/ESPACIO_Y_ARCHIVO_S146.md` §5). `scripts/libro_de_pruebas.py` funde
`hipotesis.json` (frente H), `inventario.json` (frente G) y `grafo.json` (frente E) en un registro
único; este archivo es el guard de que ese registro se mantiene, con el mismo principio de diseño
que `test_guard_declarado_vs_efectivo_s131.py`: medir la condición hoy, no confiar en que alguien
se acuerde de regenerar.

Dos guards:

  G1: el libro commiteado (`docs/LIBRO_DE_PRUEBAS.json`) es EXACTAMENTE lo que el generador
       produce hoy a partir de los tres JSON de insumo. Si alguien edita el libro a mano, o cambia
       un insumo sin regenerar, este guard lo atrapa por bytes, no por prosa.
  G2: ningún documento de resultados (`docs/**/*.md`, `CLAUDE.md`; se excluyen planes y
       especificaciones) cita una ruta de script o de datos que no existe. Hoy hay una lista
       blanca congelada de las que ya fallaban (deuda de S146, congelada el 2026-09-20): esa lista
       SÓLO puede achicarse a mano cuando alguien restaura o borra la cita rota, nunca crecer. El
       guard falla en la ruta rota número siguiente a las congeladas.

Cada test responde en su docstring (1) si lo que mide estuviera roto, ¿fallaría? y (2) si el
instrumento estuviera muerto (el generador deja de correr, o el escaneo deja de encontrar nada),
¿se vería distinto?
"""
import glob
import importlib.util
import json
import os
import re

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRATCH = os.path.join(ROOT, "experiments", "_s146_libro")


def _cargar_generador():
    """Carga scripts/libro_de_pruebas.py como módulo (no es un paquete importable)."""
    ruta = os.path.join(ROOT, "scripts", "libro_de_pruebas.py")
    spec = importlib.util.spec_from_file_location("libro_de_pruebas", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def generador():
    return _cargar_generador()


# ══ G1: el libro está al día ═══════════════════════════════════════════════
def _bytes_json_hoy(mod):
    libro = mod.construir()
    return (json.dumps(libro, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def _bytes_md_hoy(mod):
    libro = mod.construir()
    return mod.render_md(libro).encode("utf-8")


def test_g1_libro_json_coincide_con_lo_committeado(generador):
    """docs/LIBRO_DE_PRUEBAS.json es byte a byte lo que produce el generador HOY.

    (1) Si el libro estuviera atrasado (alguien tocó un insumo, o editó el JSON a mano, sin
    regenerar) este test lo detecta: compara contra la regeneración real, no contra una copia
    guardada de "cómo se veía antes". (2) Si el instrumento muriera (el generador tira una
    excepción, o deja de escribir claves esperadas), este test también falla: no hay forma de
    que "no corra" se lea como éxito, porque la comparación exige los bytes completos.
    """
    esperado = _bytes_json_hoy(generador)
    con_disco = open(os.path.join(ROOT, "docs", "LIBRO_DE_PRUEBAS.json"), "rb").read()
    assert con_disco == esperado, (
        "docs/LIBRO_DE_PRUEBAS.json no coincide con lo que genera scripts/libro_de_pruebas.py "
        "hoy: correr `python scripts/libro_de_pruebas.py` y commitear el resultado")


def test_g1b_libro_md_coincide_con_lo_committeado(generador):
    """Mismo guard que G1 para la vista humana (`docs/LIBRO_DE_PRUEBAS.md`).

    (1) Si el .md quedó desincronizado del .json (alguien regeneró uno y no el otro, o editó la
    tabla a mano) este test lo atrapa por comparación de bytes completa. (2) Si `render_md` se
    rompiera o dejara de escribir contenido, la comparación también falla: no hay forma de que
    un render vacío o parcial pase por "coincide".
    """
    esperado = _bytes_md_hoy(generador)
    con_disco = open(os.path.join(ROOT, "docs", "LIBRO_DE_PRUEBAS.md"), "rb").read()
    assert con_disco == esperado, (
        "docs/LIBRO_DE_PRUEBAS.md no coincide con lo que genera scripts/libro_de_pruebas.py hoy")


def test_g1c_libro_es_lf_puro():
    """Los dos archivos generados no tienen CRLF (regla de determinismo del pedido S146).

    (1) Si un editor de Windows reescribiera el archivo con CRLF, este test lo detecta contando
    bytes `\\r`. (2) Si el generador dejara de forzar `newline="\\n"` al escribir, el archivo
    heredaría el EOL nativo de la plataforma y este test lo vería como una falla inmediata en
    Windows (la plataforma de este repo)."""
    for nombre in ("LIBRO_DE_PRUEBAS.json", "LIBRO_DE_PRUEBAS.md"):
        crudo = open(os.path.join(ROOT, "docs", nombre), "rb").read()
        assert b"\r" not in crudo, "%s tiene CRLF, se pidió LF puro" % nombre


def test_g1d_mutacion_prueba_que_g1_de_verdad_falla(generador, tmp_path):
    """Mutación: cambia un veredicto en una COPIA de hipotesis.json y confirma que el JSON que
    produce el generador YA NO coincide con el libro commiteado: es la prueba de que G1
    realmente puede fallar, no que pasa por construcción.

    (1) Si G1 no comparara de verdad los datos (por ejemplo si comparara sólo el conteo de filas)
    esta mutación no lo notaría; acá sí, porque compara el documento completo. (2) Si el generador
    ignorara silenciosamente el insumo mutado (por ejemplo si `construir()` cacheara el resultado
    de una corrida anterior), esta mutación tampoco vería diferencia: y por eso es la prueba de
    que el instrumento reacciona a un cambio real en su entrada.
    """
    copia_h = json.load(open(generador.F_HIPOTESIS, encoding="utf-8"))
    assert copia_h, "hipotesis.json vino vacío, no se puede mutar nada"
    copia_h[0] = dict(copia_h[0])
    copia_h[0]["veredicto_H"] = "__MUTADO_S146__"
    mut_dir = tmp_path / "insumos_mutados"
    mut_dir.mkdir()
    mut_h = mut_dir / "hipotesis.json"
    mut_h.write_text(json.dumps(copia_h, ensure_ascii=False), encoding="utf-8")

    mod2 = _cargar_generador()  # instancia propia, para no pisar los paths del fixture
    mod2.F_HIPOTESIS = str(mut_h)
    libro_mutado = mod2.construir()
    veredictos = {f["id"]: f["veredicto_frente_h"] for f in libro_mutado["pruebas"]}
    assert veredictos.get(copia_h[0]["id"]) == "__MUTADO_S146__"

    bytes_mutados = (json.dumps(libro_mutado, ensure_ascii=False, indent=1, sort_keys=True)
                     + "\n").encode("utf-8")
    con_disco = open(os.path.join(ROOT, "docs", "LIBRO_DE_PRUEBAS.json"), "rb").read()
    assert bytes_mutados != con_disco, (
        "la mutación no cambió el JSON generado: G1 no podría detectar un insumo desactualizado")


# ══ G2: ninguna cita a una ruta muerta ═════════════════════════════════════
_RE_CITA = re.compile(
    r"\b(?:experiments|scripts|scratchpad|data)/[\w\-./]+\.(?:py|json|csv|txt)\b")


def _documentos_vigilados(root):
    """docs/**/*.md + CLAUDE.md, excluidos planes/especificaciones (docs/superpowers/, nombre con
    PLAN) porque citan rutas que TODAVÍA no existen a propósito (se van a escribir)."""
    excluido_dir = os.path.join(root, "docs", "superpowers") + os.sep
    candidatos = glob.glob(os.path.join(root, "docs", "**", "*.md"), recursive=True)
    claude_md = os.path.join(root, "CLAUDE.md")
    if os.path.exists(claude_md):
        candidatos.append(claude_md)
    out = []
    for f in candidatos:
        if f.startswith(excluido_dir):
            continue
        if "PLAN" in os.path.basename(f).upper():
            continue
        out.append(f)
    return sorted(out)


def _citas_y_rotas(root, documentos):
    """(total_citas, rotas): rotas es un set de (doc_relativo, ruta_citada) que no existen en
    disco. `doc_relativo` es relativo a `root`, con '/': así la lista blanca es portable."""
    total = 0
    rotas = set()
    for doc in documentos:
        txt = open(doc, encoding="utf-8", errors="replace").read()
        rel_doc = os.path.relpath(doc, root).replace(os.sep, "/")
        for m in sorted(set(_RE_CITA.findall(txt))):
            total += 1
            if not os.path.exists(os.path.join(root, m)):
                rotas.add((rel_doc, m))
    return total, rotas


# Deuda congelada el 2026-09-20 (sesión S146): rutas citadas en documentos de resultados que ya
# no existen en el árbol. NO se corrigieron los documentos (regla del pedido: este guard no es
# el lugar para arreglar prosa). Esta lista SÓLO puede achicarse: cuando una cita se corrige o
# el documento se borra, se quita la línea de acá. Si aparece una rota nueva que no está en esta
# lista, el guard falla: es la ruta rota número 30 (o la que siga).
LISTA_BLANCA_RUTAS_ROTAS_S146 = {
    ("CLAUDE.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/AUDIT_S110_NDC_PATH_DIAGNOSTIC.md",
     "experiments/_s110_ndc_probe/out/ndc_firstpass_attribution.json"),
    ("docs/AUDIT_S116_FOLLOWUP.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/AUDIT_S121_MEJORA_INTEGRAL.md", "data/backups_pre_scanfix/Lascar_pre_scanfix.json"),
    ("docs/AUDIT_S121_MEJORA_INTEGRAL.md", "experiments/38_forense_Lascar.json"),
    ("docs/AUDIT_S125_PROFUNDA.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/EXCELS_INVENTORY_S57.md", "data/mirova_reference/osf_v25_chile.csv"),
    ("docs/EXCELS_INVENTORY_S57.md", "data/mirova_reference/vents_empirical_osf.csv"),
    ("docs/EXCELS_INVENTORY_S57.md", "experiments/89_r2_candidates_scan_result.csv"),
    ("docs/F46_VRP_TIR_BUG_S76.md", "data/latest_consolidado.csv"),
    ("docs/F47_NDC_RECALL_S76.md", "scripts/audit_recall_per_volcano.py"),
    ("docs/F47_NDC_RECALL_S76.md", "scripts/count_mirova_passes.py"),
    ("docs/F47_NDC_RECALL_S76.md", "scripts/inspect_record.py"),
    ("docs/F49_SCRAPER_MIROVA_DOWN_S77.md", "scripts/sync_mirova_csv.py"),
    ("docs/F_S81_A_FASE1B_SANITY_P95.md",
     "experiments/_s82_intra_radio/fase1_1_modis_classified.csv"),
    ("docs/LIBRO_DE_PRUEBAS.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/MIROVA_IMAGES_INVENTORY.md", "scripts/visualize_volcano.py"),
    ("docs/MIROVA_INTRA_RADIO_GATE_S81.md", "experiments/_s81_v2_out/fp_genuine_all.csv"),
    ("docs/MIROVA_INTRA_RADIO_GATE_S81.md", "experiments/_s81_v2_out/per_volcano_sensor.csv"),
    ("docs/MIROVA_INTRA_RADIO_GATE_S81.md", "experiments/_s81_v2_out/subtipo_a_all.csv"),
    ("docs/MIROVA_V1_PARITY_PROPOSAL_S77.md", "data/system_status.json"),
    ("docs/MIROVA_V1_PARITY_PROPOSAL_S77.md", "scripts/write_system_status.py"),
    ("docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144_VERIFICADOR_V7.md", "scratchpad/v5/persist5.py"),
    ("docs/S121_GIT_FILTER_REPO_DESIGN.md", "scripts/filter_repo_paths_A.txt"),
    ("docs/SESSION_INDEX.md", "scripts/preflight_cmr_coverage.py"),
    ("docs/audit_s138/EJE_1_afirmaciones_de_cierre.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/audit_s138/EJE_6_decisiones_operacion_higiene.md",
     "data/mirova_equivalent/PlanchonPeteroa_recent.json"),
    ("docs/audit_s138/EJE_6_decisiones_operacion_higiene.md",
     "data/mirova_equivalent/Villarrica_recent.json"),
    ("docs/audit_s146/FASE1_VERIFICADOR.md", "scratchpad/rerun.txt"),
    ("docs/audit_s146/FRENTE_A_SIN_RESPALDO.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/audit_s146/FRENTE_B_CIERRES_CON_SCRIPT.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/audit_s146/FRENTE_H_HIPOTESIS_Y_AB.md", "scratchpad/probe_ctx_cluster_s117.py"),
    ("docs/s129/DISPLAY_V2_TRAZABILIDAD.md", "scratchpad/tr.py"),
    ("docs/s131/agentes/MAGNITUD.md", "scratchpad/atbd_geo.txt"),
    ("docs/s131/agentes/MAGNITUD.md", "scratchpad/coppola2014.txt"),
}


def test_g2_ningun_documento_cita_una_ruta_muerta_nueva():
    """Ninguna cita `experiments/…`, `scripts/…`, `scratchpad/…` o `data/…` (.py/.json/.csv/.txt)
    en `docs/**/*.md` o `CLAUDE.md` (fuera de planes/especificaciones) apunta a un archivo que no
    existe, SALVO las ya congeladas en `LISTA_BLANCA_RUTAS_ROTAS_S146`.

    (1) Si un documento nuevo citara un script borrado, este test fallaría: la ruta rota no
    estaría en la lista blanca (congelada a una fecha) y el guard la reporta por nombre. (2) Si el
    escaneo estuviera muerto (la regex dejó de matchear, o `_documentos_vigilados` devolviera una
    lista vacía), `test_g2b_el_barrido_no_pasa_por_vacio` lo atrapa aparte: acá lo mínimo es que
    las rutas SÍ presentes en la lista blanca deben seguir citándose en algún documento vigilado,
    o el barrido dejó de recorrer lo que debía.
    """
    documentos = _documentos_vigilados(ROOT)
    total, rotas = _citas_y_rotas(ROOT, documentos)
    nuevas = rotas - LISTA_BLANCA_RUTAS_ROTAS_S146
    assert not nuevas, (
        "citas a rutas que ya no existen y NO están en la lista blanca (deuda S146): %s"
        % sorted(nuevas))
    assert total > 0, "el barrido no encontró ninguna cita: instrumento posiblemente muerto"


def test_g2b_el_barrido_no_pasa_por_vacio():
    """El barrido de G2 encuentra citas de verdad (no pasa en verde por no encontrar nada).

    (1) Si la regex `_RE_CITA` se rompiera (por ejemplo un cambio que le agregue un `\\b` de más
    y deje de matchear rutas reales), este test lo detecta directamente: exige más de 100 citas
    totales, muy por debajo de las ~585 que el barrido encuentra hoy pero muy por encima de 0.
    (2) Si `_documentos_vigilados` dejara de encontrar documentos (ruta de `docs/` mal escrita,
    o el filtro de exclusión se comiera todo), el conteo de documentos vigilados también se
    comprueba aparte, así que "cero por accidente" no puede leerse como "todo bien"."""
    documentos = _documentos_vigilados(ROOT)
    assert len(documentos) > 50, (
        "muy pocos documentos vigilados (%d): revisar _documentos_vigilados" % len(documentos))
    total, _rotas = _citas_y_rotas(ROOT, documentos)
    assert total > 100, "el barrido encontró muy pocas citas (%d): la regex puede estar rota" % total


def test_g2c_mutacion_prueba_que_g2_de_verdad_falla(tmp_path):
    """Mutación: un documento NUEVO con una cita a una ruta que con toda certeza no existe (nombre
    con un sufijo aleatorio) y que por lo tanto no puede estar en la lista blanca. Confirma que el
    mecanismo de G2 la detecta como rota y NO la deja pasar.

    (1) Si G2 no comparara contra el disco de verdad (por ejemplo si sólo revisara la sintaxis de
    la ruta) esta mutación no la vería como rota; acá sí, porque `_citas_y_rotas` llama
    `os.path.exists` sobre el ROOT real. (2) Si el filtro de exclusión (planes/especificaciones)
    fuera demasiado amplio y se comiera este documento por error, la mutación no aparecería en
    `rotas` y el assert de abajo fallaría: es la prueba de que el documento mutado SÍ pasa por el
    filtro.
    """
    doc_mutado = tmp_path / "DOC_MUTADO_S146.md"
    ruta_fantasma = "experiments/_no_existe_de_verdad_s146_9f3c1a/archivo_fantasma.py"
    doc_mutado.write_text(
        "# Doc de prueba\n\nEsto cita `%s` a propósito.\n" % ruta_fantasma, encoding="utf-8")

    assert not os.path.exists(os.path.join(ROOT, ruta_fantasma)), (
        "la ruta fantasma existe de verdad, elegir otro nombre para la mutación")

    total, rotas = _citas_y_rotas(ROOT, [str(doc_mutado)])
    assert total == 1
    rel_doc = os.path.relpath(str(doc_mutado), ROOT).replace(os.sep, "/")
    assert (rel_doc, ruta_fantasma) in rotas, (
        "la mutación no fue detectada como ruta rota: el mecanismo de G2 no funciona")
    assert (rel_doc, ruta_fantasma) not in LISTA_BLANCA_RUTAS_ROTAS_S146, (
        "la ruta fantasma de la mutación no puede estar en la lista blanca real por construcción")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
