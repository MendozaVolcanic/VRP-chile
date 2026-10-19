"""C6: banco_paridad de origin/main contra el de 1eb2e6b75 sobre los mismos datos y referencia.
Compara cada record (sin 'perfil'), `pub`, y las etiquetas de etiquetar() con SN y con 'original'.
Además, el resumen de auto_audit_weekly que consume el banco. Uso: python c6_banco.py <copia> <ref> <banco_main.py>"""
import importlib.util
import os
import sys

copia, ref, banco_main = sys.argv[1:4]
sys.path.insert(0, copia)
sys.path.insert(0, os.path.join(copia, "scripts"))
os.chdir(copia)
import banco_paridad as nuevo  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

spec = importlib.util.spec_from_file_location("banco_main", banco_main)
viejo = importlib.util.module_from_spec(spec)
sys.modules["banco_main"] = viejo
spec.loader.exec_module(viejo)
assert viejo.DATA == nuevo.DATA, (viejo.DATA, nuevo.DATA)

coords = aa._coords_por_volcan()
filas = cargar_referencia_unificada(os.path.join(ref, "registro_vrp_consolidado.csv"),
                                    os.path.join(ref, "registro_vrp_ocr.csv"))
for win in [("2026-09-18", "2026-10-19"), ("2026-06-01", "2026-09-17")]:
    inner = nuevo.inner_desde_html()
    assert inner == viejo.inner_desde_html()
    rn = nuevo.cargar_nuestros(coords, inner, win)
    rv = viejo.cargar_nuestros(coords, inner, win)
    assert len(rn) == len(rv), (len(rn), len(rv))
    extra = set().union(*(set(a) - set(b) for a, b in zip(rn, rv)))
    dif = sum(1 for a, b in zip(rn, rv) if {k: v for k, v in a.items() if k != "perfil"} != b)
    print(win, "records", len(rn), "| campos nuevos:", extra, "| records distintos (sin perfil):", dif)
    for modo in ("SN", "original"):
        idx_n = nuevo.indexar_referencia(filas, coords, win, regla_minimas=modo)
        idx_v = viejo.indexar_referencia(filas, coords, win, regla_minimas=modo)
        nuevo.etiquetar(rn, *idx_n[:3])
        viejo.etiquetar(rv, *idx_v[:3])
        dl = sum(1 for a, b in zip(rn, rv) if a.get("lab") != b.get("lab") or a.get("pub") != b.get("pub"))
        claves = sorted({k for a in rn for k in a} - {"perfil"})
        dt = sum(1 for a, b in zip(rn, rv) if any(a.get(k) != b.get(k) for k in claves))
        print("   ", modo, "| etiquetas o pub distintas:", dl, "| algun campo distinto:", dt,
              "| labs:", sorted({a.get("lab") for a in rn}))
