# -*- coding: utf-8 -*-
"""S141: remapeo de citas `archivo:línea` por contenido, no por aritmética.

POR QUÉ: insertar una línea en un procesador corre las citas `file:line` de CLAUDE.md, del
contrato G8 y de MIROVA_DIVERGENCES. S140 las remapeó dos veces a mano y la tarea 7 corrió 1, 2 y
3 líneas según la zona, así que sumar un desplazamiento fijo da citas falsas. El script alinea la
versión vieja y la nueva con difflib y sólo mueve citas que caen en bloques idénticos; lo que cae
en una línea editada se reporta para revisión humana. Validado contra el remapeo manual de S140.
"""
from scripts.remapear_citas import mapa_lineas, remapear_texto


def test_mapa_lineas_sigue_bloques_identicos_tras_insertar():
    m = mapa_lineas(["a", "b", "c", "d"], ["a", "NUEVA", "b", "c", "d"])
    assert m[1] == 1 and m[2] == 3 and m[3] == 4 and m[4] == 5


def test_linea_editada_no_tiene_mapa():
    m = mapa_lineas(["a", "b", "c"], ["a", "B editada", "c"])
    assert 2 not in m and m[3] == 3


def test_remapea_cita_simple_y_lista_con_barra():
    mapas = {"process_viirs.py": {212: 214, 1082: 1085}}
    txt = "vive en `process_viirs.py:212/1082` (era 211/1080 tras la 8b)"
    nuevo, cambios, pendientes = remapear_texto(txt, mapas)
    assert "process_viirs.py:214/1085" in nuevo
    assert "era 211/1080" in nuevo, "la nota histórica sin nombre de archivo no se toca"
    assert len(cambios) == 2 and not pendientes


def test_rango_se_remapea_extremo_por_extremo():
    """Caso real S140 T7: `process_viirs.py:676-683` pasó a `676-684`."""
    mapas = {"process_viirs.py": {676: 676, 683: 684}}
    nuevo, _, pendientes = remapear_texto("`pipeline/process_viirs.py:676-683` la aplica", mapas)
    assert "process_viirs.py:676-684" in nuevo and not pendientes


def test_cita_a_linea_editada_se_reporta_y_no_se_cambia():
    nuevo, _, pendientes = remapear_texto("ver store.py:10 y store.py:99", {"store.py": {10: 11}})
    assert "store.py:11" in nuevo and "store.py:99" in nuevo
    assert pendientes == [("store.py", 99)]


def test_contrato_g8_con_ruta_completa():
    txt = '    ("pipeline/process_modis.py", 59, "compute_test1_mir"),'
    nuevo, _, _ = remapear_texto(txt, {"process_modis.py": {59: 60}})
    assert '("pipeline/process_modis.py", 60, "compute_test1_mir")' in nuevo


def test_archivo_no_modificado_no_se_toca():
    nuevo, cambios, pendientes = remapear_texto("otro.py:5", {"process_modis.py": {5: 6}})
    assert nuevo == "otro.py:5" and not cambios and not pendientes


def test_no_confunde_prefijo_de_nombre():
    """`process_viirs_mod.py` no debe remapearse con el mapa de `process_viirs.py` (A92)."""
    nuevo, cambios, _ = remapear_texto("process_viirs_mod.py:5", {"process_viirs.py": {5: 6}})
    assert nuevo == "process_viirs_mod.py:5" and not cambios


def test_citas_historicas_con_nombre_de_archivo_no_se_mueven():
    """A6 y A49 citan líneas históricas CON nombre de archivo; S140 no las movió y hacía bien."""
    mapas = {"process_viirs.py": {518: 519}, "process_modis.py": {316: 317}}
    txt = "\n".join(["`process_viirs.py:518` (vent_dist=haversine(vent_lat,...)) y concluí",
                     "`process_modis.py:316` desempaca `None` -> `TypeError`",
                     "vigente: process_viirs.py:518"])
    lineas = remapear_texto(txt, mapas)[0].split("\n")
    assert "process_viirs.py:518" in lineas[0] and "process_modis.py:316" in lineas[1]
    assert "process_viirs.py:519" in lineas[2], "la misma cita fuera del contexto histórico sí se mueve"


def test_excluir_explicito():
    nuevo, cambios, _ = remapear_texto("a.py:5", {"a.py": {5: 6}}, excluir=[("a.py", 5)])
    assert nuevo == "a.py:5" and not cambios
