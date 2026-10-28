# -*- coding: utf-8 -*-
"""S166 V375-E, adenda 2: nulo de la batería por mutaciones de una línea (S156: cuenta como ATRAPADA sólo la mutación
que la batería rechaza por aserción; una que hace caer la batería con una excepción es CAÍDA y no cuenta).

Cada mutación cambia UN texto que aparece exactamente una vez en el archivo, en una copia propia de la carpeta
(`experiments/_s162_v375/_mut_adenda2_<id>/`, borrada al terminar; cuatro a la vez), y corre `probar_adenda2.py --dir <copia>`.
  ATRAPADA   la batería sale 1 con su línea RESULTADO (alguna aserción falló)
  SOBREVIVE  la batería sale 0 (la mutación no se ve)
  CAÍDA      la batería se cae (excepción, sin línea RESULTADO): no cuenta como atrapada
Controles: IDENTIDAD (la copia sin mutar tiene que PASAR) y CONTROL (una mutación que rompe la importación tiene que
salir CAÍDA, para mostrar que el clasificador distingue caída de aserción).
Uso: python -I mutar_adenda2.py  (escribe mutar_adenda2_salida.txt)
"""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MUT = AQUI.parent / "_mut_adenda2"
LP, GF = "leer_posicion_v375e.py", "objetivos_far_v375.py"
COPIAR = (LP, GF, "objetivos_run_far_v375.json", "objetivos_far_v375.json", "sin_granulo_far_v375.json")

MUTACIONES = [
    # ---- lector: las tres distancias y la variante
    ("L01", LP, "cer = min(celdas, key=", "cer = max(celdas, key="),
    ("L02", LP, "pico = max(cu, key=lambda p: m13[p])\n\n    def d(", "pico = min(cu, key=lambda p: m13[p])\n\n    def d("),
    ("L03", LP, "fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))\n    pico",
     "fr, fc = float(np.mean([b for _, b in cu])), float(np.mean([a for a, _ in cu]))\n    pico"),
    ("L04", LP, '"cercano_ref": d(cer[0], cer[1], ref)', '"cercano_ref": d(cer[0], cer[1], crater)'),
    ("L05", LP, 'return "summit" if dist <= inner else "far"', 'return "summit" if dist < inner else "far"'),
    ("L06", LP, '    r["distance_class"] = clase_dc(dist, inner)\n', '    pass\n'),
    ("L07", LP, '    r["primary_cluster"]["centroid_dist_km"] = round(dist, 3)\n', '    pass\n'),
    ("L08", LP, '"pico": d(pico[0], pico[1], crater),', '"pico": d(fr, fc, crater),'),
    ("L09", LP, '"cercano": float(min(p["dist_km"] for p in px))}', '"cercano": float(max(p["dist_km"] for p in px))}'),
    ("L10", LP, '"pico": float(rec["hotspot_dist_km"]),', '"pico": float(pc["centroid_dist_km"]),'),
    # ---- lector: error de posición y regla RP
    ("L11", LP, ' or (x["c"] == "far_tabla" and pub)', ''),
    ("L12", LP, ' or (x["c"] == "pos_prot" and not pub)', ''),
    ("L13", LP, 'if x["c"] == "pos_prot" and x["K"] and (x["tabla"] or not solo_tabla)]',
     'if x["c"] == "pos_prot" and (x["tabla"] or not solo_tabla)]'),
    ("L14", LP, 'all(veredicto_par(a, b) == "GANA" for b in vivos if b != a)]',
     'all(veredicto_par(a, b) != "PIERDE" for b in vivos if b != a)]'),
    ("L15", LP, '    if "radiante" in no_vencidos:\n', '    if False:\n'),
    ("L16", LP, '    if len(vivos) == 1:\n', '    if False:\n'),
    ("L17", LP, '    if not far_ok:\n        return "NO DECIDE', '    if False:\n        return "NO DECIDE'),
    ("L18", LP, 'far_ok = bool(far_tab) and art_far_presente and', 'far_ok = True and art_far_presente and'),
    ("L19", LP, 'blo[x["bloque"]] += x["w"] * (1 if ea else -1)', 'blo[x["bloque"]] += x["w"] * (-1 if ea else 1)'),
    ("L20", LP, 'regla_posicion(marco + far_t, E, far_ok=far_ok)', 'regla_posicion(marco + far, E, far_ok=far_ok)'),
    # ---- lector: controles
    ("L21", LP, '(variante(base, 9.0, 5.0), 5.0), (variante(variante(base, 9.0, 5.0), 0.5, 5.0), 5.0)]',
     '(variante(base, 0.5, 5.0), 5.0), (variante(variante(base, 9.0, 5.0), 0.5, 5.0), 5.0)]'),
    ("L22", LP, '    if not uno or malos_c1:\n', '    if malos_c1:\n'),
    ("L23", LP, '    if not con or malos_c5:\n', '    if not con:\n'),
    ("L24", LP, '    if malos_c6:\n', '    if False:\n'),
    ("L25", LP, 'and abs(pasadas[i]["m14"][1] - obj[i]["ref_M14"][1]) < 1e-6)))]',
     'and abs(pasadas[i]["m14"][1] - obj[i]["ref_M14"][1]) < 1.0)))]'),
    ("L26", LP, '    if s != SHA_EVALUAR_LF:\n', '    if False:\n'),
    ("L27", LP, 'if sg.get("objetivos_far_sha256") != sha256_lf(obj_far):',
     'if sg.get("objetivos_far_sha256") == sha256_lf(obj_far):'),
    ("L28", LP, 'if any(not (ID_FAR[0] <= i < ID_FAR[1]) for i in far):', 'if False:'),
    ("L29", LP, 'if any(o.get("clase") not in CLASES_FAR for o in far.values()):', 'if False:'),
    ("L30", LP, '    usa_rec = frac < E.UMBRAL_K_RECORRIDO\n', '    usa_rec = False\n'),
    # ---- lector: varas
    ("L31", LP, 'rp["vrp_mw"] = round(float(p["vrp_port"]), 3)', 'rp["vrp_mw"] = ra["vrp_mw"]'),
    ("L32", LP, 'and f.get("dist_km") is not None and (f.get("vrp_mw") or 0) > 0 and o["hora_utc"][:10] >= FRONTERA_OCR]',
     'and f.get("dist_km") is not None and (f.get("vrp_mw") or 0) > 0]'),
    ("L33", LP, 'out["alerta_tabla"] = max(t, key=lambda f: f["vrp_mw"])["dist_km"]',
     'out["alerta_tabla"] = min(t, key=lambda f: f["vrp_mw"])["dist_km"]'),
    ("L34", LP, '"a_una_celda": sum(1 for v in d if v <= 0.375),', '"a_una_celda": sum(1 for v in d if v <= 1.0),'),
    ("L35", LP, '"con_alertado": sum(1 for x in lst if x["npix"].get(("VIA", "radiante"), 0)),',
     '"con_alertado": len(lst),'),
    ("L36", LP, 'for x in marco if x["X"][("VIA", a)] != x["X"][("VIA", "radiante")]]',
     'for x in marco if x["X"][("VIA", a)] == x["X"][("VIA", "radiante")]]'),
    ("L37", LP, '            pesos[(obj[i]["clase"], obj[i]["estrato"])] = 1.0\n',
     '            pesos[(obj[i]["clase"], obj[i]["estrato"])] = 2.0\n'),
    ("L39", LP, 'vrp_ok = bool(con_vrp) and len(fuera) <= (1 - FRAC_VRP) * len(con_vrp)', 'vrp_ok = True'),
    ("L40", LP, 'and x["K"] and (x["tabla"] or not solo_tabla)]', 'and x["K"]]'),
    ("L41", LP, 'tramo_de[x["bloque"]] = x["tramo"]', 'tramo_de[x["bloque"]] = "T"'),
    ("L42", LP, r'b = Path(ruta).read_bytes().replace(b"\r\n", b"\n")', 'b = Path(ruta).read_bytes()'),
    ("L43", LP, '    return regla_matlab()', '    return vrp_port'),
    ("L45", LP, 'if 1 <= npix <= 4 and m is not None and m["npix"] == npix and abs(m["vrp_port_mw"] - vrp_port) <= 1e-6:',
     'if m is not None:'),
    ("L44", LP, 'if p.get("vrp_via") is not None and p.get("vrp_port") is not None]',
     'if p.get("vrp_via") is not None and p.get("vrp_port") is not None and False]'),
    ("L38", LP, 'str(f.get("tipo", "")).startswith("ALERTA") and f.get("source") == "CONS"',
     'str(f.get("tipo", "")).startswith("ALERTA")'),
    # ---- lector: arreglos del verificador (VE2-01, VE2-06, VE2-09) y sus mutaciones sobrevivientes (VE2-04, VE2-05)
    ("L46", LP, 'and any(x["X"][("VIA", b)] for b in BRAZOS_POS if b != a)]', ']'),
    ("L47", LP, '    if not no_vencidos:', '    if False:'),
    ("L48", LP, '    if otros:', '    if False:'),
    ("L49", LP, 'if x["tramo"] == tr]', ']'),
    ("L50", LP, 'pesos = {(c, h): v["N"] / n_ok[(c, h)]', 'pesos = {(c, h): 1.0'),
    ("L51", LP, 'return E.err(x, a) or', 'return False or'),
    ("L52", LP, '>= (1 - UMBRAL_COBERTURA) * len(far_tab)', '>= 0.5 * len(far_tab)'),
    ("L53", LP, 'or dif or not vivos:', 'or dif:'),
    ("L54", LP, 'if any(not (ID_CTLF[0] <= i < ID_CTLF[1]) for i in ctlf):', 'if False:'),
    ("L55", LP, 'vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])', 'vlat, vlon = v["lat"], v["lon"]'),
    ("L56", LP, 'return (g["ul_y"] - g["y0"]) / paso - 0.5, (g["x0"] - g["ul_x"]) / paso - 0.5',
     'return (g["x0"] - g["ul_x"]) / paso - 0.5, (g["ul_y"] - g["y0"]) / paso - 0.5'),
    ("L57", LP, '>= FRONTERA_OCR]', '> FRONTERA_OCR]'),
    ("L58", LP, 'dc_ok[b] = va is not None and va.get("distance_class") == vb.get("distance_class")', 'dc_ok[b] = True'),
    # ---- lector: N-1 y N-2 del verificador corto
    ("L59", LP, 'and resultado_rp(por_tramo[tr]) != resultado_rp(ver)]', 'and False]'),
    ("L60", LP, 'if por_tramo[tr] != "SIN PASADAS"', 'if True'),
    ("L61", LP, '        return veredicto.split()[1]', '        return "RADIANTE"'),
    ("L62", LP, 'fuera_v = [i for i in con_v if abs(pasadas[i]["vrp_via"] - pasadas[i]["vrp_port_vieja"]) > TOL_VRP_MW]',
     'fuera_v = []'),
    # ---- lector: §8.13 (N-3, sellado)
    ("L63", LP, '    prot_k = [x for x in prot_k if not no_veta_n3(x)]', '    prot_k = list(prot_k)'),
    ("L64", LP, 'and x.get("sensor") == SENSOR_SNPP and x["hora"][:10] < HITO_N3', 'and x["hora"][:10] < HITO_N3'),
    ("L65", LP, 'if x["c"] == "pos_prot" and x["K"] and not x["X"][("VIA", a)] and not no_veta_n3(x)]',
     'if x["c"] == "pos_prot" and x["K"] and not x["X"][("VIA", a)]]'),
    # ---- generador
    ("G19", GF, '"capas_locales": dep["capas"](),', '"capas_locales": {},'),
    ("G01", GF, 'for f in p.get("mirova") or []) else "far_ocr"', 'for f in p.get("mirova") or [] if False) else "far_ocr"'),
    ("G02", GF, 'return (cons or fp or [{"dist_km": None}])[0]["dist_km"]', 'return (fp or cons or [{"dist_km": None}])[0]["dist_km"]'),
    ("G03", GF, '    return a == b, len(a), len(b)\n', '    return True, len(a), len(b)\n'),
    ("G04", GF, '\n           and p["hora_utc"][:10] not in excluidos]', ']'),
    ("G05", GF, 'if p["lab"] == "far_ref" and p["b"] == "VIIRS375"', 'if p["lab"] == "far_ref"'),
    ("G06", GF, 'e.update({"id": ID0 + n,', 'e.update({"id": n,'),
    ("G07", GF, '    if dest.resolve() == Path(portes).resolve():\n', '    if False:\n'),
    ("G08", GF, '    previos = [n for n in SALIDAS if (dest / n).exists()]\n', '    previos = []\n'),
    ("G09", GF, '    if malos:\n', '    if False:\n'),
    ("G10", GF, '    if pob_d["meta"]["referencia"] != shas:\n', '    if False:\n'),
    ("G11", GF, '    if not igual:\n', '    if False:\n'),
    ("G12", GF, '{"objetivos_far_sha256": sha_obj, "pasadas": sin_g}', '{"objetivos_far_sha256": "x", "pasadas": sin_g}'),
    ("G13", GF, '    if n != 1:\n', '    if n > 1:\n'),
    ("G14", GF, 'o.update({"id": ID_CTLF + n,', 'o.update({"id": ID_CTLF,'),
    ("G15", GF, 'return hashlib.sha1(b"blob %d\\0" % len(b) + b).hexdigest()', 'return hashlib.sha1(b).hexdigest()'),
    ("G16", GF, 'return hashlib.sha256(b.replace(CRLF, LF)).hexdigest()', 'return hashlib.sha256(b).hexdigest()'),
    ("G18", GF, '        if crudo is not None and real != esperado:', '        if False:'),
    ("G17", GF, 'return "far_tabla" if any(str(f.get("tipo", "")).startswith("FALSO_POSITIVO") and f.get("source") == "CONS"',
     'return "far_tabla" if any(str(f.get("tipo", "")).startswith("FALSO_POSITIVO")'),
]
CONTROL = ("CONTROL", LP, "import numpy as np\n", "import numpy_no_existe as np\n")


def preparar(d, mut=None):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    for n in COPIAR:
        shutil.copy2(AQUI / n, d / n)
    if mut:
        _id, arch, viejo, nuevo = mut
        src = (d / arch).read_text(encoding="utf-8")
        assert src.count(viejo) == 1, (_id, src.count(viejo))
        (d / arch).write_text(src.replace(viejo, nuevo), encoding="utf-8")


def correr(d):
    p = subprocess.run([sys.executable, "-I", str(AQUI / "probar_adenda2.py"), "--dir", str(d)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    falla = [x[6:].strip()[:70] for x in p.stdout.splitlines() if x.startswith("FALLA")]
    res = [x for x in p.stdout.splitlines() if x.startswith("RESULTADO")]
    if p.returncode == 0 and res:
        return "SOBREVIVE", falla
    if p.returncode == 1 and res:
        return "ATRAPADA", falla
    return "CAIDA", (p.stderr.strip().splitlines() or ["?"])[-1:]


def una(k, mut):
    """Corre una mutación en su propia copia (carpeta _mut_adenda2_<k>), la borra y devuelve (estado, fallas)."""
    d = AQUI.parent / f"{MUT.name}_{k}"
    try:
        preparar(d, mut)
        return correr(d)
    finally:
        if d.exists():
            shutil.rmtree(d)


def main():
    from concurrent.futures import ThreadPoolExecutor
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)
    try:
        e, f = una("identidad", None)
        pr(f"IDENTIDAD (copia sin mutar): {'PASA' if e == 'SOBREVIVE' else 'FALLA ' + e} {f[:3]}")
        e, f = una("control", CONTROL)
        pr(f"CONTROL (rompe la importación): {e} {f}  (tiene que ser CAIDA)")
        cuenta = {"ATRAPADA": 0, "SOBREVIVE": 0, "CAIDA": 0}
        with ThreadPoolExecutor(max_workers=4) as ex:      # cada mutación en su carpeta: no se pisan
            resultados = list(ex.map(lambda m: una(m[0], m), MUTACIONES))
        for m, (e, f) in zip(MUTACIONES, resultados):
            cuenta[e] += 1
            pr(f"{m[0]} {e:9s} {f[:2]}")
        pr("")
        pr(f"RESULTADO: {cuenta['ATRAPADA']} de {len(MUTACIONES)} atrapadas por aserción; sobreviven "
           f"{cuenta['SOBREVIVE']}; caídas {cuenta['CAIDA']}")
    finally:
        (AQUI / "mutar_adenda2_salida.txt").write_text("".join(x + chr(10) for x in L), encoding="utf-8")


if __name__ == "__main__":
    main()
