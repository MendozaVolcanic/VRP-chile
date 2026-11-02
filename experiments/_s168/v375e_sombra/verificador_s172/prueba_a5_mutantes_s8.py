# -*- coding: utf-8 -*-
"""Verificador S172, A5 (parte barata): ¿las mutaciones S01 a S08 (y 6 mias) son atrapadas POR ASERCION por las pruebas
«S8 (S172)» y las S8 previas? No es el nulo del orquestador (no se corre mutar_sombra.py); es una re-medicion independiente
sobre copias del lector en CARPETA, con los casos copiados de probar_sombra.py (diff del commit aa3fdcf1).
Q1: si las pruebas S8 estuvieran rotas (siempre True), un mutante que cambia la salida no cambiaria el resultado: el control
    positivo es que las mutaciones deben dar al menos una aserción en rojo; el control negativo, la identidad debe dar 0 rojos.
Q2: si el instrumento estuviera muerto (excepcion al cargar), se distingue: estado CAIDA (no cuenta como atrapada).
Ventana: ninguna (casos sinteticos del propio commit; sin datos de ventana P)."""
import importlib.util, shutil, sys, os
from pathlib import Path
sys.dont_write_bytecode = True
W = Path("D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra")
C = Path("D:/vrp-trabajo/temporales/ver_s172_relector/mut"); C.mkdir(exist_ok=True)
sys.path.insert(0, str(W))
spec = importlib.util.spec_from_file_location("MS", W / "mutar_sombra.py"); MS = importlib.util.module_from_spec(spec); spec.loader.exec_module(MS)
SRC = (W / "leer_sombra_v375e.py").read_text(encoding="utf-8")
MUTS = {m[0]: m for m in MS.MUTACIONES if m[0].startswith("S") or m[0] == "R05"}
EXTRA = {
 "X1": ("X1", "return perfil_sin_otro_sensor(viejo) != perfil_sin_otro_sensor(nuevo)", "return False"),
 "X2": ("X2", "return perfil_sin_otro_sensor(viejo) != perfil_sin_otro_sensor(nuevo)", "return True"),
 "X3": ("X3", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)\n        d.pop('extends', None)"),
 "X4": ("X4", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)", "        for k in list(t):\n            if k.startswith('enable_modis') or k.startswith('enable_v'):\n                t.pop(k, None)"),
 "X5": ("X5", "except Exception:      # noqa: BLE001  perfil que no se lee: falla cerrada", "except ValueError:      # noqa: BLE001  perfil que no se lee: falla cerrada"),
 "X7": ("X7", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)\n            d.pop(k, None)"),
 "X8": ("X8", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            [v.pop(k, None) for v in d.values() if isinstance(v, dict)]"),
 "X9": ("X9", "        for k in CLAVES_PERFIL_OTRO_SENSOR:\n            t.pop(k, None)", "        for k in CLAVES_PERFIL_OTRO_SENSOR + ('enable_v375_codigo_mirova',):\n            t.pop(k, None)"),
 "X6": ("X6", "if ruta not in PERFILES_REGIMEN:\n            return False", "if ruta not in PERFILES_REGIMEN[:1]:\n            return False"),
}
MUTS.update(EXTRA)

def cargar(ruta):
    s = importlib.util.spec_from_file_location("LS_" + ruta.parent.name, ruta); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

COMMIT = "c" * 40
def cases(LS):
    """Devuelve lista de (nombre, ok) - las aserciones S8 (S172) y las S8 previas de perfiles, copiadas del commit."""
    out = []
    def chk(n, c, *_): out.append((n, bool(c)))
    def fake(vers):
        return (lambda a_, b_: list(vers)), (lambda rev, ruta: vers[ruta][0 if rev == COMMIT else 1])
    chk("lista cerrada", getattr(LS, "CLAVES_PERFIL_OTRO_SENSOR", None) == ("enable_modis_codigo_mirova", "enable_v750_codigo_mirova", "enable_modis_geo_mxd03", "enable_modis_crater_sin_dato", "enable_modis_dist_desde_crater"))
    me0 = ("extends: x\nthresholds:\n  anomaly_threshold_k: 4.0\n  enable_v375_codigo_mirova: false\n"
           "sensors:\n  modis: true\noutput:\n  data_subdir: mirova_equivalent\nenable_modis_b22_primary: true\n")
    so0 = ("extends: mirova_equivalent\nthresholds:\n  enable_v750_codigo_mirova: true\n"
           "  enable_v375_codigo_mirova: true\n  enable_modis_codigo_mirova: true\noutput:\n"
           "  data_subdir: sombra_codigo_mirova\n")
    ME, SO = "pipeline/profiles/mirova_equivalent.yaml", "pipeline/profiles/sombra_codigo_mirova.yaml"
    no_marcan = (
        ("encender MODIS prod", ME, me0.replace("  anomaly_threshold_k: 4.0\n", "  anomaly_threshold_k: 4.0\n  enable_modis_codigo_mirova: true\n")),
        ("apagar MODIS sombra", SO, so0.replace("enable_modis_codigo_mirova: true", "enable_modis_codigo_mirova: false")),
        ("quitar MODIS sombra", SO, so0.replace("  enable_modis_codigo_mirova: true\n", "")),
        ("apagar V750 sombra", SO, so0.replace("enable_v750_codigo_mirova: true", "enable_v750_codigo_mirova: false")),
        ("tres flags MxD03", ME, me0.replace("  anomaly_threshold_k: 4.0\n", "  anomaly_threshold_k: 4.0\n  enable_modis_geo_mxd03: true\n  enable_modis_crater_sin_dato: true\n  enable_modis_dist_desde_crater: true\n")),
        ("comentario", ME, "# comentario\n" + me0))
    for nom, ruta, nuevo in no_marcan:
        viejo = me0 if ruta == ME else so0
        nb, mo = fake({ruta: (viejo, nuevo)}); r = LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo)
        chk(f"{nom} no marca", r == [])
    marcan = (
        ("apagar V375 sombra", SO, so0.replace("enable_v375_codigo_mirova: true", "enable_v375_codigo_mirova: false")),
        ("encender V375 prod", ME, me0.replace("enable_v375_codigo_mirova: false", "enable_v375_codigo_mirova: true")),
        ("otro umbral", ME, me0.replace("anomaly_threshold_k: 4.0", "anomaly_threshold_k: 4.5")),
        ("MODIS en raiz", ME, me0 + "enable_modis_codigo_mirova: true\n"),
        ("MODIS en otra seccion", SO, so0.replace("output:\n", "output:\n  enable_modis_codigo_mirova: true\n")),
        ("clave MODIS no listada", ME, me0.replace("enable_modis_b22_primary: true", "enable_modis_b22_primary: false")),
        ("sensor apagado", ME, me0.replace("  modis: true", "  modis: false")),
        ("carpeta de salida", SO, so0.replace("data_subdir: sombra_codigo_mirova", "data_subdir: otra")),
        ("ilegible", ME, "thresholds: [: :\n"),
        ("deja de existir", ME, None))
    for nom, ruta, nuevo in marcan:
        viejo = me0 if ruta == ME else so0
        nb, mo = fake({ruta: (viejo, nuevo)}); r = LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo)
        chk(f"{nom} marca", r == [ruta])
    nb, mo = fake({ME: (None, me0)}); chk("aparece marca", LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo) == [ME])
    nb, mo = fake({"pipeline/profiles/experimental.yaml": ("a: 1\n", "thresholds: [: :\n")}); chk("ajeno ilegible no marca", LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo) == [])
    # previas
    nb, mo = fake({"pipeline/profiles/experimental.yaml": ("a: 1\n", "a: 2\n")}); chk("(VL169-03) perfil ajeno no marca", LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo) == [])
    for rr in (ME, SO):
        nb, mo = fake({rr: ("a: 1\n", "a: 2\n")}); chk(f"(VL169-03/04) cambio en {rr.split('/')[-1]} marca", LS.diff_git(COMMIT, "f" * 40, nombres=nb, mostrar=mo) == [rr])
    return out

def correr(id_, mut):
    d = C / id_; 
    if d.exists(): shutil.rmtree(d)
    d.mkdir(); src = SRC
    if mut:
        assert src.count(mut[1]) == 1, (id_, src.count(mut[1])); src = src.replace(mut[1], mut[2])
    (d / "leer_sombra_v375e.py").write_text(src, encoding="utf-8")
    try:
        LS = cargar(d / "leer_sombra_v375e.py"); res = cases(LS)
    except Exception as e:
        return "CAIDA", [repr(e)[:90]]
    rojos = [n for n, ok in res if not ok]
    return ("ATRAPADA" if rojos else "SOBREVIVE"), rojos

est, rojos = correr("identidad", None)
print(f"IDENTIDAD: {est} (rojos: {rojos}) | {'OK' if est == 'SOBREVIVE' else 'MAL: la identidad debe sobrevivir'}")
for id_ in sorted(MUTS):
    est, rojos = correr(id_, MUTS[id_])
    print(f"MUT {id_:3} {est:9} {rojos[:3]}")
