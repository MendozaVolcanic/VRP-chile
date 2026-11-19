"""S190 (2026-11-18): el NRT parte del `main` vigente al arrancar cada trabajo, no del commit del despacho.

POR QUÉ: `actions/checkout` sin `ref` toma el SHA del evento, fijado cuando se despacha la corrida. Las corridas del
NRT comparten el grupo `push-main` y se encolan: la de las 10:10 UTC del 2026-11-18 (run 44282845368) esperó a la de
las 09:45 (run 44278853697), que subió a las 10:30 las pasadas VIIRS 750 de las 06:18 y 06:24 de Copahue. La segunda
partió del commit `abd7b0205` (09:57), sin esas pasadas, las procesó otra vez y el rebase del push dejó las dos copias
en `data/mirova_equivalent/Copahue.json` (P4 de `tests/test_guard_regla_c_s134.py` en rojo). Con `ref: ${{ github.ref }}`
el checkout baja la punta de la rama cuando arranca el trabajo, después del push de la corrida anterior.
"""
import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NRT = os.path.join(ROOT, ".github", "workflows", "nrt.yml")


def _pasos_checkout():
    with open(NRT, encoding="utf-8") as f:
        wf = yaml.safe_load(f)
    pasos = []
    for job in wf["jobs"].values():
        for paso in job.get("steps", []):
            if str(paso.get("uses", "")).startswith("actions/checkout@"):
                pasos.append(paso)
    return pasos


def test_nrt_tiene_un_checkout():
    """Control: si el paso cambiara de nombre o de acción, la prueba siguiente no miraría nada."""
    assert len(_pasos_checkout()) == 1


def test_nrt_checkout_baja_la_punta_de_la_rama():
    paso = _pasos_checkout()[0]
    ref = (paso.get("with") or {}).get("ref")
    assert ref == "${{ github.ref }}", (
        "el checkout del NRT debe bajar la punta de la rama al arrancar (ref: ${{ github.ref }}), "
        "no el SHA del despacho; sin eso una corrida encolada reprocesa pasadas ya subidas y las duplica")
