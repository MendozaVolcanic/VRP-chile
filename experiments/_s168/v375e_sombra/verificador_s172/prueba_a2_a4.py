# -*- coding: utf-8 -*-
"""Verificador S172: pruebas propias de A2 y A4 sobre los perfiles REALES de origin/main (insumos/*.yaml), editados.

Preguntas del instrumento (se repiten en cada bloque):
1. Si cambio_significativo estuviera roto, ¿esto lo vería? Sí para los casos "marca"/"no marca" que difieren en una
   sola clave; cada caso lleva un par de control (el mismo cambio en una clave NO listada debe marcar).
2. Si el instrumento estuviera muerto (siempre False o siempre True), ¿el resultado cambiaría? Sí: hay casos que
   deben dar True y casos que deben dar False; un instrumento constante falla uno de los dos grupos.
Ventana: no hay datos de ventana P; sólo texto de perfiles y workflow de origin/main (sha en insumos/origin_main_sha.txt).
"""
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True
W = Path("D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
C = Path("D:/vrp-trabajo/temporales/ver_s172_relector")
spec = importlib.util.spec_from_file_location("LS", W)
LS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LS)

ME_P, SO_P = "pipeline/profiles/mirova_equivalent.yaml", "pipeline/profiles/sombra_codigo_mirova.yaml"
WF_P = ".github/workflows/sombra-codigo-mirova.yml"
ME = (C / "insumos/ME_main.yaml").read_text(encoding="utf-8")
SO = (C / "insumos/SO_main.yaml").read_text(encoding="utf-8")
WF = (C / "insumos/WF_main.yml").read_text(encoding="utf-8")

res = []


def caso(nombre, ruta, viejo, nuevo, esperado):
    got = LS.cambio_significativo(ruta, viejo, nuevo)
    ok = got == esperado
    res.append(ok)
    print(("OK   " if ok else "FALLA"), f"esperado={esperado!s:5} obtenido={got!s:5} | {nombre}")


def ins(texto, tras, linea):
    assert tras in texto, tras
    return texto.replace(tras, tras + linea, 1)


print("origin/main sha:", (C / "insumos/origin_main_sha.txt").read_text().strip())
print("lector:", W, "| claves:", LS.CLAVES_PERFIL_OTRO_SENSOR)
print("--- A2/A4: no deben marcar")
ME_ON = ins(ME, "thresholds:\n", "  enable_modis_codigo_mirova: true\n")
caso("ME real + enable_modis_codigo_mirova: true (el encendido de MODIS)", ME_P, ME, ME_ON, False)
caso("ME real + clave nueva + comentario de cabecera nuevo", ME_P, ME, "# S172 encendido de MODIS\n" + ME_ON, False)
caso("ME real + clave nueva con comentario al margen y sangria distinta de comentario",
     ME_P, ME, ins(ME, "thresholds:\n", "  # MOD-D\n  enable_modis_codigo_mirova: true   # MOD-D\n"), False)
caso("ME real + las 5 claves (4 en false) en thresholds", ME_P, ME,
     ins(ME, "thresholds:\n", "".join(f"  {k}: true\n" for k in LS.CLAVES_PERFIL_OTRO_SENSOR)), False)
caso("SO real con enable_modis_codigo_mirova: false (guardia K)", SO_P, SO,
     SO.replace("enable_modis_codigo_mirova: true", "enable_modis_codigo_mirova: false"), False)
caso("SO real sin la clave de MODIS", SO_P, SO, SO.replace("  enable_modis_codigo_mirova: true\n", ""), False)
caso("SO real con enable_v750_codigo_mirova: false", SO_P, SO,
     SO.replace("enable_v750_codigo_mirova: true", "enable_v750_codigo_mirova: false"), False)
caso("perfil ajeno (experimental) ilegible no marca", "pipeline/profiles/experimental.yaml", "a: 1\n", "x: [: :\n", False)
caso("perfil nuevo (guardia) no listado no marca", "pipeline/profiles/guardia_k.yaml", None,
     "extends: mirova_equivalent\nthresholds:\n  enable_modis_codigo_mirova: false\n", False)

print("--- A2: deben marcar (cada uno con su par de control: la misma edicion en una clave NO listada)")
caso("CONTROL de A1: ME real + enable_modis_b22_primary movida/otra clave nueva en thresholds", ME_P, ME,
     ins(ME, "thresholds:\n", "  enable_modis_otra_cosa: true\n"), True)
caso("ME real + enable_v375_codigo_mirova: true", ME_P, ME, ins(ME, "thresholds:\n", "  enable_v375_codigo_mirova: true\n"), True)
caso("SO real con enable_v375_codigo_mirova: false", SO_P, SO,
     SO.replace("enable_v375_codigo_mirova: true", "enable_v375_codigo_mirova: false"), True)
caso("SO real con extends distinto", SO_P, SO, SO.replace("extends: mirova_equivalent", "extends: experimental"), True)
caso("ME real: un umbral numerico de thresholds", ME_P, ME, ME.replace("dnti_contextual_c1: 0.003", "dnti_contextual_c1: 0.004"), True)
caso("ME real: clave de MODIS en la raiz (fuera de thresholds)", ME_P, ME, ME + "\nenable_modis_codigo_mirova: true\n", True)
caso("ME real: clave de MODIS en output:", ME_P, ME, ME.replace("\noutput:\n", "\noutput:\n  enable_modis_codigo_mirova: true\n", 1), True)
caso("ME real: clave de MODIS en paths:", ME_P, ME, ME.replace("\npaths:\n", "\npaths:\n  enable_modis_codigo_mirova: true\n", 1), True)
caso("ME real: clave de V750 en sensors:", ME_P, ME, ME.replace("\nsensors:\n", "\nsensors:\n  enable_v750_codigo_mirova: true\n", 1), True)
caso("perfil que aparece (base None)", ME_P, None, ME, True)
caso("perfil que desaparece (nuevo None)", ME_P, ME, None, True)
caso("perfil ilegible en el nuevo", ME_P, ME, "thresholds: [: :\n", True)
caso("perfil ilegible en el viejo", ME_P, "thresholds: [: :\n", ME, True)
caso("perfil que pasa a vacio ('')", ME_P, ME, "", True)
caso("perfil que pasa a lista YAML", ME_P, ME, "- a\n- b\n", True)
caso("thresholds pasa a ser lista (no dict)", ME_P, "thresholds: [a]\n", "thresholds: [a, b]\n", True)
caso("thresholds: null en ambos y un cambio de otra seccion", ME_P, "thresholds:\nx: 1\n", "thresholds:\nx: 2\n", True)
caso("ambos perfiles vacios -> no marca (iguales)", ME_P, "", "", False)

print("--- A2: huecos de YAML (la mutacion de claves de otro sensor debe verse igual que en profile.py)")
dup = "thresholds:\n  a: 1\nthresholds:\n  enable_modis_codigo_mirova: true\n  a: 2\n"
caso("clave duplicada 'thresholds' (gana la ultima, igual que profile.py): cambia 'a'", ME_P,
     "thresholds:\n  a: 1\n", dup, True)
caso("ancla/merge: la clave de MODIS entra por <<:", ME_P,
     "base: &b\n  a: 1\nthresholds:\n  <<: *b\n", "base: &b\n  a: 1\n  enable_modis_codigo_mirova: true\nthresholds:\n  <<: *b\n", True)
caso("misma clave con valor entre comillas ('true' str) sigue sin marcar", ME_P, ME,
     ins(ME, "thresholds:\n", "  enable_modis_codigo_mirova: 'true'\n"), False)

print("--- A4: workflow de la sombra (texto entero)")
lin = WF.splitlines()
print("l.110 workflow origin/main:", lin[109][:140])
WF_ED = "\n".join(lin[:109] + [lin[109].replace("assert p.ENABLE_V750_CODIGO_MIROVA and p.ENABLE_V375_CODIGO_MIROVA and p.ENABLE_MODIS_CODIGO_MIROVA",
                                                  "assert p.ENABLE_V750_CODIGO_MIROVA and p.ENABLE_V375_CODIGO_MIROVA")] + lin[110:]) + "\n"
assert WF_ED != WF
caso("workflow de la sombra: se edita la asercion de la l.110 (quita MODIS)", WF_P, WF, WF_ED, True)
caso("workflow de la sombra: sin cambios", WF_P, WF, WF, False)
caso("workflow de la sombra: sólo un comentario", WF_P, WF, "# nuevo\n" + WF, True)

print("RESUMEN:", sum(res), "de", len(res), "como se esperaba")
sys.exit(0 if all(res) else 1)
