# -*- coding: utf-8 -*-
"""Mutaciones del lector de la retrospectiva (pre-registro SELLADO PREREGISTRO_RETRO_PAQUETE.md §11: «mutaciones
atrapadas por aserción con control de caída»).

POR QUÉ. Una batería en verde no dice que pueda ponerse roja. Cada mutación de abajo rompe una regla del pre-registro
en una copia del lector, y la batería tests/test_leer_retro_s172.py se corre contra esa copia (LEER_RETRO_MODULO).
Cuenta como ATRAPADA sólo si alguna prueba falla por AssertionError; si las fallas son excepciones (el código cae), es
CAE y no cuenta como atrapada (S152: una mutación que cae no fue vista por ninguna aserción). La mutación de control
introduce un NameError a propósito: tiene que salir CAE, y si sale ATRAPADA el contador está roto.

La copia vive al lado del original con un nombre que empieza por `_mut_` (el lector calcula la raíz del repo desde su
propia carpeta) y se borra al terminar. No se edita el lector mientras corre la batería (A112): cada mutación es otra
copia.

Uso: python mutar_leer_retro.py [--solo PREFIJO[,PREFIJO...]] > mutar_leer_retro_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ORIGINAL = AQUI / "leer_retro.py"
BATERIA = RAIZ / "tests" / "test_leer_retro_s172.py"

MUTACIONES = [
    ("M1 fila 5 antes que la 4 (VPR172-03)",
     "    if f == 4 or motivos4:\n        return 4, NOMBRES_FILA[4], motivos4 + ([\"regla del sensor\"] if f == 4 else [])\n    if f == 5:\n        return 5, NOMBRES_FILA[5], []\n",
     "    if f == 5:\n        return 5, NOMBRES_FILA[5], []\n    if f == 4 or motivos4:\n        return 4, NOMBRES_FILA[4], motivos4 + ([\"regla del sensor\"] if f == 4 else [])\n"),
    ("M2 MODIS: el veto de P1 no cuenta",
     "\"_fila_regla\": (2 if x[\"p1\"][\"estado\"] == \"VETADO\" else",
     "\"_fila_regla\": (2 if x[\"p1\"][\"estado\"] == \"NUNCA\" else"),
    ("M3 C-via en F26 acepta records sin la marca",
     "        out[\"estado\"] = \"OK\" if not sin else f\"ROJO: {len(sin)} records de la vía sin la marca\"",
     "        out[\"estado\"] = \"OK\""),
    ("M4 VIIRS 375: SIN SUSTRATO de P2 pasa como CUMPLE (VPR2-02)",
     "    elif p2v == \"SIN SUSTRATO\":\n        fila = 5",
     "    elif p2v == \"NUNCA\":\n        fila = 5"),
    ("M5 C-K sin tope de excepciones (R-15)",
     "TOPE_EXCEPCIONES_CK = 3 ", "TOPE_EXCEPCIONES_CK = 30 "),
    ("M6 N-3 deshecho",
     "    return (\"SNPP\" in (f.get(\"sensor\") or \"\") and f[\"dt\"][:10] < HITO_N3",
     "    return (False and f[\"dt\"][:10] < HITO_N3"),
    ("M7 decide la unión con el OCR y no la tabla sola (§4.1)",
     "canales = {\"tabla\": [r for r in filas_ref_union if r[\"source\"] == \"CONS\"]",
     "canales = {\"tabla\": [r for r in filas_ref_union]"),
    ("M8 Tupungatito antes del 2026-02-23",
     "(vol == TUPUNGATITO and (t == \"R25\" or dia < INICIO_TUPUNGATITO))",
     "(vol == TUPUNGATITO and t == \"R25\")"),
    ("M9 V750-A sin sello no limita el techo (R-12)",
     "    elif p2[\"estado\"] == \"BLOQUEA\" or not sellado:",
     "    elif p2[\"estado\"] == \"BLOQUEA\":"),
    ("M10 el nulo del lector no exige el contador",
     "    ok3 = despues - antes == N_INYECTADOS", "    ok3 = True"),
    ("M11 cercano y radiante distintos no van a Nicolás (R-13)",
     "        extra[\"cercano_y_radiante_difieren\"] = rad[\"_fila_regla\"] != regla[\"_fila_regla\"]",
     "        extra[\"cercano_y_radiante_difieren\"] = False"),
    ("M12 la caja de VIIRS 750 no se comprueba (L2)",
     "                                      {\"estado\": \"OK\" if not malas else f\"ROJO: {len(malas)} records con otra caja\",",
     "                                      {\"estado\": \"OK\","),
    # S173, arreglos del verificador limpio de #940: una mutación que deshace cada arreglo
    ("N02a c_k_puro nunca cae (VPR940-02)",
     "    return {\"estado\": \"OK\" if not malos else f\"ROJO: {len(malos)} records de K de disco",
     "    return {\"estado\": \"OK\" if True else f\"ROJO: {len(malos)} records de K de disco"),
    ("N02b armar_pasadas no marca K con la marca de la vía (VPR940-02)",
     "        elif rk.get(\"via_codigo_mirova\") is True:", "        elif False:"),
    ("N03a C-K no exige los tres días de F26 (VPR940-03)",
     "        if len(dias_ok) < DIAS_F26_D3:", "        if False:"),
    ("N03b C-K ignora la cobertura del K-gemelo (VPR940-03)",
     "and not mal_formadas and cob[\"estado\"] == \"OK\" else", "and not mal_formadas else"),
    ("N04 el nulo de runner no descuenta las nombradas (VPR940-04)",
     "if \"KG\" in f[\"_t\"] and (f[\"vol\"], f[\"dt\"]) not in nombradas]", "if \"KG\" in f[\"_t\"]]"),
    ("N05 el placebo no mira P1 ni P2 (VPR940-05)",
     "sin causa de L7\" if sin_expl else \"OK\")", "sin causa de L7\" if False else \"OK\")"),
    ("N06 C-montaje acepta diferencias sin explicar (VPR940-06)",
     "        malas.append((\"sin explicar\", (x or {}).get(\"pasada\")))", "        pass"),
    ("N08 C-via del runner vuelve a dejar rojo el sensor vacío (VPR940-08)",
     "            lineas.append(f\"SENSOR_VACIO {s}\")\n            continue",
     "            codigo = max(codigo, 4)\n            continue", "controles_via.py"),
    ("N09 C-cobertura de R25 no se calcula (VPR940-09)",
     "            ctl[\"c_cobertura_r25\"] = c_cobertura(r25s, clave=\"lab_osf\", clases=(\"protegida_osf\",))",
     "            ctl[\"c_cobertura_r25\"] = {\"estado\": \"OK\"}"),
    ("N11 el sorteo baraja entre estratos (VPR940-11)",
     "        por[(f[\"vol\"], None if f.get(\"z\") is None else int(float(f[\"z\"]) // 10))].append(i)",
     "        por[0].append(i)"),
    ("N15 ENSAYO no se ve en la línea impresa (VPR940-15)",
     "        pref = \"ENSAYO (NO DECIDE) \" if a.ensayo else \"\"", "        pref = \"\""),
    # S173, seguimiento de #940: lecturas aprobadas por Nicolás y hallazgos del segundo verificador
    ("S01a M de 750 vuelve a exigir que el comparador separe (VPR940-01)",
     "    m_ok = bool(razon[\"en_banda_0_9_1_1\"])\n",
     "    m_ok = bool(razon[\"en_banda_0_9_1_1\"]) and _separa_provisional_d28(R, filas, b)\n"),
    ("S01b 750 sellado sin definición de separa no queda rojo (VPR940-01)",
     "        rojo_m = \"ROJO: V750-A sellado y sin definición", "        rojo_m = None and \"ROJO: V750-A sellado y sin definición"),
    ("S01c un comparador que no separa no deja rojo el placebo (VPR940-01)",
     "rojo_m = None if out[\"separa_v750\"] else", "rojo_m = None if True else"),
    ("S07a ENCIENDE DE MAS deja de ir a la fila 3 (VPR940-07)",
     "    elif p2v == \"PIERDE\" or p2lv == \"PIERDE\" or sil == \"ENCIENDE DE MAS\":",
     "    elif p2v == \"PIERDE\" or p2lv == \"PIERDE\":"),
    ("S07b P2-L PIERDE deja de ir a la fila 3 (VPR940-07)",
     "    elif p2v == \"PIERDE\" or p2lv == \"PIERDE\" or sil == \"ENCIENDE DE MAS\":",
     "    elif p2v == \"PIERDE\" or sil == \"ENCIENDE DE MAS\":"),
    ("S10 el defecto del lector OSF deja de ser control (VPR940-10)",
     "ctl[\"c_defecto_lector_osf\"] = {\"estado\": \"OK\" if not dfc else",
     "ctl[\"c_defecto_lector_osf\"] = {\"estado\": \"OK\" if True else"),
    ("Sb03 una excepción de C-K mal formada no deja rojo (VPR940b-03)",
     "and not sin_empate and not mal_formadas and", "and not sin_empate and"),
    ("Sb06a C-montaje acepta tags sin uno por origen (VPR940b-06)",
     "isinstance(tags, dict) and set(tags) == set(ORIGENES_MONTAJE)", "isinstance(tags, dict)"),
    ("Sb06b C-montaje acepta pasadas fuera de DM (VPR940b-06)",
     "        if not _pasada_de_dm((x or {}).get(\"pasada\")):", "        if False:"),
    ("Sb07a un volcán Tier A sin F26 en K no cuenta (VPR940b-07)",
     "    faltan += [(\"F26\", v, \"sin pasadas de K en F26\") for v in sin_f26]", "    pass"),
    ("Sb07b las sobras del K-gemelo no se listan (VPR940b-07)",
     "            out.append(key)", "            pass"),
    ("Sb08 sin aviso de R25 sin OSF (VPR940b-08)",
     "    if not a.osf:                                                   # VPR940b-08", "    if False:"),
    ("Sb01a el sorteo devuelve SIN SUSTRATO sin calcular P2 (P11b del verificador, VPR940b-01)",
     "        cuenta[R.F4.p2(barajar_en_estratos(filas, rng), brazos[0], brazos[1])[\"estado\"]] += 1",
     "        cuenta[\"SIN SUSTRATO\"] += 1"),
    ("Sb01b el informe del sorteo nunca dice SIN PODER (VPR940b-01)",
     "             if n and cuenta[\"SIN SUSTRATO\"] == n else \"puede variar\")",
     "             if False else \"puede variar\")"),
    ("Sc1 el candado acepta un manifiesto sin los requeridos (§11)",
     "    estado = (\"OK\" if not malos and not faltan else", "    estado = (\"OK\" if not malos else"),
    ("Gm1 el manifiesto lee el disco y no el blob del ref (§11)",
     "    return {r: sha256_lf_blob(_blob(ref, r)) for r in rutas}",
     "    return {r: L.sha256_lf(RAIZ / r) for r in rutas}", "armar_manifiesto.py"),
    ("Gm2 el pre-registro cambiado pasa como igual (§11)",
     "\"igual\": sello == actual}", "\"igual\": True}", "armar_manifiesto.py"),
    ("Gmo1 C-montaje sale OK con los comparadores pendientes (§6)",
     "    estado = \"PENDIENTE: \" + \"; \".join(PENDIENTES) if PENDIENTES else \"OK\"", "    estado = \"OK\"",
     "armar_montaje.py"),
    ("Gmo2 C-montaje no compara el VRP (§6)",
     "        if abs(_vrp(rv) - _vrp(ra)) > TOL_VRP:", "        if False:", "armar_montaje.py"),
    ("CONTROL de caída: NameError en regla_modis (tiene que salir CAE)",
     "    F4 = R.F4\n    x = {\"p1\": F4.p1(filas, b)", "    F4 = R.F4\n    x = {\"p1\": F4_NO_EXISTE.p1(filas, b)"),
]


OBJETIVOS = {  # archivo mutado -> (batería, variable de entorno con que la batería carga la copia)
    "leer_retro.py": (BATERIA, "LEER_RETRO_MODULO"),
    "controles_via.py": (RAIZ / "tests" / "test_retro_paquete_workflow_s172.py", "CONTROLES_VIA_MODULO"),
    "armar_manifiesto.py": (RAIZ / "tests" / "test_retro_seguimiento_s173.py", "ARMAR_MANIFIESTO_MODULO"),
    "armar_montaje.py": (RAIZ / "tests" / "test_retro_seguimiento_s173.py", "ARMAR_MONTAJE_MODULO"),
}


def correr(nombre, viejo, nuevo, archivo="leer_retro.py"):
    bateria, var = OBJETIVOS[archivo]
    src = (AQUI / archivo).read_text(encoding="utf-8")
    if src.count(viejo) != 1:
        return "NO APLICA (el texto a mutar aparece %d veces)" % src.count(viejo), ""
    mut = AQUI / f"_mut_{Path(archivo).stem}_{os.getpid()}.py"
    fd, nombre_xml = tempfile.mkstemp(suffix=".xml")
    os.close(fd)                    # en Windows el descriptor abierto impide borrar el archivo despues
    xml = Path(nombre_xml)
    try:
        mut.write_text(src.replace(viejo, nuevo), encoding="utf-8")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **{var: str(mut)})
        subprocess.run([sys.executable, "-m", "pytest", str(bateria), "-q", "-p", "no:cacheprovider",
                        f"--junitxml={xml}"], cwd=RAIZ, env=env, capture_output=True, text=True, timeout=3600)
        raiz = ET.parse(xml).getroot()
        fallas = [(c.get("name"), e.tag, e.get("message", "")[:120]) for c in raiz.iter("testcase")
                  for e in c if e.tag in ("failure", "error")]
        por_asercion = [x for x in fallas if x[1] == "failure" and x[2].startswith(("AssertionError", "assert"))]
        if por_asercion:
            # VPR940b-12: se cuentan también las pruebas que cayeron por excepción en la misma corrida
            caidas = [x for x in fallas if x not in por_asercion]
            return "ATRAPADA", "%s | caídas en la misma corrida: %d%s" % (
                ", ".join(x[0] for x in por_asercion), len(caidas),
                (" (" + ", ".join(x[0] for x in caidas[:3]) + ")") if caidas else "")
        if fallas:
            return "CAE", ", ".join(f"{x[0]}:{x[2][:40]}" for x in fallas[:3])
        return "SOBREVIVE", ""
    finally:
        mut.unlink(missing_ok=True)
        xml.unlink(missing_ok=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    cuenta = {}
    for nombre, viejo, nuevo, *archivo in MUTACIONES:
        if solo and not nombre.startswith(tuple(solo.split(","))):
            continue
        estado, detalle = correr(nombre, viejo, nuevo, *archivo)
        cuenta[estado] = cuenta.get(estado, 0) + 1
        print(f"{nombre}: {estado} | {detalle}", flush=True)
    reales = [m for m in MUTACIONES if not m[0].startswith("CONTROL") and (not solo or m[0].startswith(tuple(solo.split(","))))]
    print("resumen:", cuenta, "| mutaciones reales:", len(reales), "| control de caida: 1")


if __name__ == "__main__":
    main()
