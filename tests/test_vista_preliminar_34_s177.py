# -*- coding: utf-8 -*-
"""S177, reducida en S183: lo que queda vigente de la vista preliminar de los 34 volcanes.

HISTORIA. En S177 los 34 volcanes que corren en sombra tenían una página aparte, `frontend/preliminar_34.html` con su
módulo `preliminar_34.js`, y este archivo probaba ese módulo en node: el corte de cumbre de 5 km, un píxel en la
cumbre aunque el cúmulo mayor esté lejos, el mismo foco visto desde dos volcanes, el resumen por ventana y la lista de
los 34 contra volcanoes.yaml.

POR QUÉ SE REDUJO (S183, 2026-11-13). Desde #992 los 34 están en el tablero principal, y Nicolás aprobó pasar al
tablero lo único que la página hacía y él no (el rótulo del píxel en la cumbre y la marca del foco compartido) y
retirar la página. Los dos archivos se borraron (`git grep` no encontró otro usuario), así que las pruebas del módulo
ya no tienen qué ejecutar. Lo que probaban vive ahora en `tests/test_tablero_absorbe_preliminar34_s183.py`, que
ejecuta en node las funciones reales de `frontend/index.html` (con el caso real de Carrán-Los Venados). La prueba
de la lista de los 34 contra volcanoes.yaml pasó allí también, ahora sobre la lista del tablero: al moverla apareció
Laguna del Maule a 8,2 km de las coordenadas del pipeline, y se corrigió. El corte de cumbre del tablero lo fija
`tests/test_tablero_34_y_pixeles_s180.py` (`derivarClaseSombra`).

LO QUE LA PÁGINA HACÍA Y EL TABLERO TODAVÍA NO: no contar una escena inválida (`diag_codigo_mirova.motivo_vacio`)
como pasada. En la sombra de origin/main del 2026-11-13 son 33 de 2.713 records; quedó anotado como pendiente en el
PR de S183, fuera de su alcance.

QUÉ SIGUE FIJANDO ESTE ARCHIVO: dónde se lee la sombra (sólo index.html y sólo para los 34) y el rótulo de los
volcanes sin datos.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_el_tablero_principal_lee_la_sombra_solo_para_los_34():
    """Hasta S180 esta prueba exigía que ninguna vista leyera la sombra (decisión S18: no mezclar los 34 con los 11).
    Nicolás la cambió el 2026-11-12 («todos deben tener la misma funcionalidad de los 11 de MIROVA, en la página
    principal con su mapa»): index.html muestra los 34 con los datos de la sombra, marcados «sin MIROVA · 1 vez al
    día». Lo que se sigue vigilando: (1) diario y mosaico, que son vistas de los 11 Tier A, no la leen; (2) index la
    lee en un solo lugar y sólo para los volcanes sin MIROVA, así que un Tier A nunca cae a la sombra. El resto de lo
    que index hace con los 34 está en tests/test_tablero_34_y_pixeles_s180.py."""
    for pagina in ("diario.html", "mosaico.html"):
        assert "data/sombra_34" not in (ROOT / "frontend" / pagina).read_text(encoding="utf-8"), pagina
    src = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert src.count("SOMBRA_34_BASE + v.name") == 1
    assert 'const sombra = v.fuente === "sombra_34";' in src
    assert 'v.hasMirova ? v : Object.assign({}, v, { fuente: "sombra_34"' in src


def test_la_pagina_aparte_se_retiro():
    """S183: si alguien la restaura, que sea a propósito y cambiando esta prueba y la de S183."""
    assert not (ROOT / "frontend" / "preliminar_34.html").exists()
    assert not (ROOT / "frontend" / "preliminar_34.js").exists()


def test_el_rotulo_no_afirma_que_se_proceso_cuando_pudo_fallar_la_carga():
    for pagina in ("index.html", "diario.html", "mosaico.html"):
        texto = (ROOT / "frontend" / pagina).read_text(encoding="utf-8")
        assert "procesado, sin publicar" not in texto and "sin datos en este tablero" in texto, pagina
