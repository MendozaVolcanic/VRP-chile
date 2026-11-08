# -*- coding: utf-8 -*-
"""S176: cada prueba nueva del PR A falla por aserción al deshacer lo que vigila (A110).

POR QUÉ. Una prueba que pasa no dice nada si no se la vio fallar. Cada mutación deshace una pieza del PR en el árbol de trabajo,
corre las pruebas que la vigilan y restaura el archivo byte a byte. Sólo cuenta como atrapada si pytest termina con una falla
de aserción (S152: una mutación que hace caer el módulo no prueba nada). Ninguna mutación se commitea.

Uso: python -I experiments/_s176_v375e_adopcion/mutar_pr_a.py > salida.txt   (árbol limpio; un proceso a la vez)
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
G = "tests/test_guardia_k_viirs_s176.py"
V = "tests/test_vigilancia_guardia_viirs_s176.py"
A = "tests/test_auto_audit_via_viirs_s176.py"
F = "tests/test_cambio_detector_via_viirs_s176.py"
P = "pipeline/profiles/guardia_k_viirs.yaml"
W = ".github/workflows/guardia-k-viirs.yml"
WV = ".github/workflows/vigilancia-guardia-viirs.yml"
VM = "scripts/vigilancia_guardia_modis.py"
VV = "scripts/vigilancia_guardia_viirs.py"
RM = "scripts/revisar_guardia_modis.py"
RV = "scripts/revisar_guardia_viirs.py"
AA = "scripts/auto_audit_weekly.py"
VS = "scripts/vigilancia_sombra.py"
CD = "frontend/cambio_detector.js"

MUT = [
    ("P01 la vía de 375 encendida en la guardia", P, "enable_v375_codigo_mirova: false", "enable_v375_codigo_mirova: true", G),
    ("P02 la vía de 750 encendida en la guardia", P, "enable_v750_codigo_mirova: false", "enable_v750_codigo_mirova: true", G),
    ("P03 la guardia corre MODIS", P, "  modis: false", "  modis: true", G),
    ("P04 la guardia sin VIIRS 750", P, "  viirs_750: true", "  viirs_750: false", G),
    ("P05 la guardia escribe en producción", P, "data_subdir: guardia_k_viirs", "data_subdir: mirova_equivalent", G),
    ("P06 la guardia con el umbral cambiado", P, "enable_test1_path: false", "enable_test1_path: true", G),
    ("W01 cron en minuto ocupado", W, 'cron: "35 19 * * *"', 'cron: "0 19 * * *"', G),
    ("W02 cron antes del fin de la guardia MODIS", W, 'cron: "35 19 * * *"', 'cron: "35 18 * * *"', G),
    ("W03 sin corte por token vacío", W, 'if [ -z "$EARTHDATA_TOKEN" ]; then', 'if false; then', G),
    ("W04 la aserción no exige apagada la vía de 375", W, "assert not p.ENABLE_V375_CODIGO_MIROVA; ", "", G),
    ("W05 commitea otra carpeta", W, 'git add "data/guardia_k_viirs/', 'git add "data/mirova_equivalent/', G),
    ("W06 grupo de concurrencia ajeno", W, "group: guardia-k-viirs", "group: guardia-k-modis", G),
    ("W07 la revisión sólo si no falló nada", W, "if: always() && steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_guardia_viirs.py",
     "if: steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_guardia_viirs.py", G),
    ("W08 corre el perfil de producción", W, "--profile guardia_k_viirs", "--profile mirova_equivalent", G),
    ("R01 la revisión mira un solo VIIRS", RV, 'SENSORES = ("VIIRS375", "VIIRS750")', 'SENSORES = ("VIIRS375",)', G),
    ("R02 la revisión con el perfil de MODIS", RV, 'PERFIL = "guardia_k_viirs"', 'PERFIL = "guardia_k_modis"', G),
    ("R03 sin la regla del catálogo vacío", RM, "if len(sensores) > 1 and set(sensores) <= set(sin_pasada):", "if False:", G),
    ("R04 una guardia con marca de la vía pasa", RM, "    if con_via:\n", "    if False:\n", G),
    ("R05 cada sensor no se exige por separado", RM, "            if n_nuevos[s] == 0:", "            if sum(n_nuevos.values()) == 0:", G),
    ("V01 encendido sin filtrar el sensor", VM, 'if aa.our_bucket(str(r.get("sensor") or "")) != sensor:', 'if aa.our_bucket(str(r.get("sensor") or "")) != SENSOR:', V),
    ("V02 pasadas sin filtrar el sensor", VM, '        if p["sensor"] != sensor:', '        if p["sensor"] != SENSOR:', V),
    ("V03 sobrepublicación de otro sensor", VM, 'if (r["b"] != sensor or r.get("lab") != "neg_limpio"', 'if (r["b"] != SENSOR or r.get("lab") != "neg_limpio"', V),
    ("V04 nulo de otro sensor", VM, 'if g["b"] != sensor or not (desde <= g["dt"] < limite):', 'if not (desde <= g["dt"] < limite):', V),
    ("V05 la cota pendiente dispara", VM, 'cotas["muy_bajo"] is not None and len(mb) > cotas["muy_bajo"]', '(cotas["muy_bajo"] is None and len(mb) > 0) or (cotas["muy_bajo"] is not None and len(mb) > cotas["muy_bajo"])', V),
    ("V06 el flag de VIIRS 375 lee el de MODIS", VM, '"VIIRS375": "ENABLE_V375_CODIGO_MIROVA"', '"VIIRS375": "ENABLE_MODIS_CODIGO_MIROVA"', V),
    ("V07 los avisos dicen MODIS", VM, '"VIIRS375": "VIIRS 375"', '"VIIRS375": "MODIS"', V),
    ("V08 las cotas de MODIS en VIIRS", VV, "sensor=sensor,\n                        cotas=COTAS[sensor])", "sensor=sensor)", V),
    ("V09 sin D-9 en la vigilancia", VV, 'regla_minimas="SN"', 'regla_minimas="original"', V),
    ("V10 frescura de todos los sensores", VV, 'vs._avisos_frescura(guardia, hoy, "la guardia (K)", "guardia-k-viirs.yml", sensores=[sensor])',
     'vs._avisos_frescura(guardia, hoy, "la guardia (K)", "guardia-k-viirs.yml")', V),
    ("V11 sin frescura de la guardia", VV, 'vs._avisos_frescura(guardia, hoy, "la guardia (K)", "guardia-k-viirs.yml", sensores=[sensor])', "[]", V),
    ("V12 región sensible al revés", VV, "solo_g += gpub and not ppub", "solo_g += ppub and not gpub", V),
    ("V13 lista sensible equivocada", VV, 'd.get("roi_v750") == "sens"', 'd.get("roi_v750") == "def"', V),
    ("V14 salida sin la marca del sensor", VV, '"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sensor": sensor,', '"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sensor": "VIIRS375",', V),
    ("W09 la vigilancia cubre un solo sensor", WV, "sensor: [v375, v750]", "sensor: [v375]", V),
    ("W10 el workflow escucha otra guardia", WV, 'workflows: ["Guardia K de VIIRS (11 Tier A)"]', 'workflows: ["Guardia K de MODIS (11 Tier A)"]', V),
    ("W11 issues sin el sensor en el título", WV, 'abrir "Guardia K de $ETIQUETA: candidata a reversion"', 'abrir "Guardia K de VIIRS: candidata a reversion"', V),
    ("A01 un solo detector para los dos VIIRS", AA, '"VIIRS750": "VIA_V750"}', '"VIIRS750": "VIA_V375"}', A),
    ("A02 falta VIA_V375 en los regímenes", AA, '"VIA_MODIS", "VIA_V375", "VIA_V750")   # #571', '"VIA_MODIS", "VIA_V750")   # #571', A),
    ("A03 la vía sin distinguir sensor", AA, 'VIA_POR_SENSOR[sensor] if sensor in _fronteras(via_modis) else vigente', 'VIA_POR_SENSOR[sensor] if _fronteras(via_modis) else vigente', A),
    ("A04 la caída a K cuenta como vía", AA, 'return our_bucket(str(rec.get("sensor") or "")) if rec.get("via_codigo_mirova") is True else None', 'return our_bucket(str(rec.get("sensor") or "")) if rec.get("via_codigo_mirova") else None', A),
    ("A05 la fecha en texto deja de ser MODIS", AA, 'return {"MODIS": via_modis} if isinstance(via_modis, str) else via_modis', 'return {} if isinstance(via_modis, str) else via_modis', A),
    ("A06 sin juzgar al revés", AA, "        if n_via >= MIN_N_RECALL:\n            continue\n        det = VIA_POR_SENSOR[s_via]", "        if n_via < MIN_N_RECALL:\n            continue\n        det = VIA_POR_SENSOR[s_via]", A),
    ("A07 evaluación vigente siempre de K", AA, "        return por_detector[VIA_POR_SENSOR[s]] if s in fr else ev_k", "        return ev_k", A),
    ("A08 el banco no reconoce la vía de VIIRS", AA, 'via=VIA_POR_SENSOR.get(our_bucket(str(r.get("sensor") or ""))) if es_via else None)', 'via="VIA_MODIS" if es_via else None)', A),
    ("A09 detectores de la vía fuera", AA, "dets_via = tuple(d for s, d in VIA_POR_SENSOR.items() if s in via_modis)", "dets_via = ()", A),
    ("A10 sin fronteras en la salida", AA, 'if set(via_modis) != {"MODIS"}:', "if False:", A),
    ("A11 fronteras con la vía de MODIS sólo", AA, "    via_modis = fronteras_via(records_por_volcan)\n", '    via_modis = {k: v for k, v in fronteras_via(records_por_volcan).items() if k == "MODIS"}\n', A),
    ("A12 banda de recall recalibrada", AA, 'RECALL_MIN = {"VIIRS375": 93.4,', 'RECALL_MIN = {"VIIRS375": 80.0,', A),
    ("V15 cota pendiente sin aviso", VV, "              + avisos_cotas(flag, sensor))", "              )", V),
    ("K01 la vigilancia de K no saca la vía de VIIRS", VS, "return aa.claves_via(aa.cargar_records()[0])", "return aa.claves_via_modis(aa.cargar_records()[0])", A),
    ("K02 sigue exigiendo frescura de K", VS, "    return [s for s in aa.SENSORS if s not in con_via]", "    return list(aa.SENSORS)", A),
    ("F01 familia sin distinguir 750", CD, 'return /_750$/.test(s) ? "VIIRS750" : "VIIRS375";', 'return "VIIRS375";', F),
    ("F02 primeraVia ignora la familia", CD, "if (!r || familiaSensor(r.sensor) !== familia) continue;", "if (!r) continue;", F),
    ("F03 la caída a K cuenta como K previa", CD, "else if (r.via_codigo_mirova === undefined || r.via_codigo_mirova === null) {", "else {", F),
    ("F04 el aviso de 375 sin la advertencia", CD, "no quiere decir que el volcán crezca", "es normal", F),
    ("F05 la línea de 375 en otra serie", CD, "serie: /^VIIRS\\b.*375/", "serie: /^MODIS/", F),
    ("F06 notar sólo MODIS", CD, "    Object.keys(VIAS).forEach(familia => {\n      const t = primeraVia(records, familia);", '    ["MODIS"].forEach(familia => {\n      const t = primeraVia(records, familia);', F),
    ("F07 registra sólo el plugin de MODIS", CD, "Object.keys(VIAS).forEach(f => raiz.Chart.register(crearPluginVia(f)));", "raiz.Chart.register(crearPluginVia('MODIS'));", F),
    ("F08 la fecha no se corrige a la más temprana", CD, "if (t != null && (desdeVia[familia] == null || Date.parse(t) < Date.parse(desdeVia[familia]))) {", "if (t != null && desdeVia[familia] == null) {", F),
]


def correr(prueba):
    r = subprocess.run([sys.executable, "-m", "pytest", prueba, "-q", "-x", "--no-header", "-p", "no:cacheprovider"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout


def main():
    atrapadas, otras = 0, []
    for nombre, ruta, viejo, nuevo, prueba in MUT:
        p = RAIZ / ruta
        original = p.read_bytes()
        txt = original.decode("utf-8")
        crlf = "\r\n" in txt
        t = txt.replace("\r\n", "\n")
        assert t.count(viejo) == 1, (nombre, t.count(viejo))
        m = t.replace(viejo, nuevo)
        p.write_bytes((m.replace("\n", "\r\n") if crlf else m).encode("utf-8"))
        try:
            rc, out = correr(prueba)
        finally:
            p.write_bytes(original)
        cola = out.strip().splitlines()[-1] if out.strip() else ""
        de_asercion = rc == 1 and "failed" in cola and "error" not in cola.split("failed")[0]
        estado = "ATRAPADA POR ASERCION" if de_asercion else ("SOBREVIVE" if rc == 0 else "CAIDA")
        fallo = re.search(r"FAILED \S+::(\S+)", out)
        print(f"{nombre} | {estado} | {fallo.group(1) if fallo else cola[:100]}", flush=True)
        if de_asercion:
            atrapadas += 1
        else:
            otras.append(nombre)
    rc, out = 0, ""
    for prueba in (G, V, A, F):
        r, o = correr(prueba)
        rc |= r
        print(f"identidad {prueba}: {o.strip().splitlines()[-1]}", flush=True)
    print(f"\nMutaciones: {len(MUT)}; atrapadas por aserción: {atrapadas}; otras: {otras}")
    return 0 if atrapadas == len(MUT) and rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
