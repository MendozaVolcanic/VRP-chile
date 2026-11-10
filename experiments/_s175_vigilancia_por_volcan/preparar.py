# Copia mutaciones_vigilancia.py (rama de la auditoría S175) con dos cambios de montaje, sin tocar su lógica:
# MUT en una carpeta dada por MUT_DIR, y si VGM_VIEJO apunta a una carpeta, importa de ahí el vigilancia_guardia_modis
# de origin/main (código de antes) re-anclado al ROOT real.
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
dst = Path(sys.argv[2])
viejo = '''MUT = Path(ROOT).parent / "mutaciones"'''
assert src.count(viejo) == 1
src = src.replace(viejo, '''MUT = Path(os.environ["MUT_DIR"])''')
imp = "import vigilancia_guardia_modis as vgm  # noqa: E402"
assert src.count(imp) == 1
src = src.replace(imp, '''if os.environ.get("VGM_VIEJO"):
    sys.path.insert(0, os.environ["VGM_VIEJO"])
import vigilancia_guardia_modis as vgm  # noqa: E402
print("vigilancia importada de:", vgm.__file__, file=sys.stderr)
if os.environ.get("VGM_VIEJO"):
    vgm.ROOT = ROOT
    _j = os.path.join(ROOT, "experiments", "_s171_modd_adopcion", "sombra_pasadas_juzgadas_modis.json")
    vgm.leer_juzgadas = lambda path=_j: vgm.vs.leer_juzgadas(_j)''')
dst.write_text(src, encoding="utf-8")
print("ok", dst)
