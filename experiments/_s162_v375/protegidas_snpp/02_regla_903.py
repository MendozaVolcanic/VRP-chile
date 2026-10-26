"""02: la regla de «protegida de cráter» de #903 aplicada TAL CUAL a las 6 pasadas.

Código: `_clase_mirova_903.py` es `scripts/clase_mirova.py` de `origin/instrumento/clase-pasada` (719e9c32e), copiado con
`git show` sin modificar (blob 2b59957f8a513f8320648fa89e2b9afc3dcd9127). La referencia se carga con
`scripts/referencia_mirova_unificada.py` de esta rama, idéntico al de la rama de #903 (`git diff` vacío).

Pregunta 1 del instrumento: si la regla devolviera «de cráter» para filas sólo OCR de Suomi NPP antes del hito, acá se
vería (se imprimen los motivos). Pregunta 2: control positivo = una protegida de la TABLA del mismo volcán y mes, que
debe salir de cráter; control negativo = una fila sólo OCR con distancia mayor al radio. Denominador: las 6 pasadas
(volcán, sensor VIIRS375, minuto) de la lista P1 de evaluar.json (run 40116289866, brazo C13|cercano), más controles.
"""
import sys, io, json, importlib.util
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
spec = importlib.util.spec_from_file_location("clase_903", AQUI / "_clase_mirova_903.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
from scripts.referencia_mirova_unificada import cargar_referencia_unificada
import yaml
V = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}

SEIS = [(279, "Tupungatito", "2026-08-01 05:00", "VIIRS_SNPP"), (285, "Lascar", "2026-08-22 05:06", "VIIRS_SNPP"),
        (288, "Isluga", "2026-09-09 06:06", "VIIRS_SNPP"), (289, "Tupungatito", "2026-09-14 06:18", "VIIRS_SNPP"),
        (294, "Tupungatito", "2026-09-28 05:18", "VIIRS_SNPP"), (295, "Tupungatito", "2026-09-29 04:54", "VIIRS_SNPP")]
ref = cargar_referencia_unificada()
print("filas de la referencia:", len(ref))
salida = {}
for canal in ("union", "tabla"):
    pas = C.resumir_pasadas(ref, canal=canal)      # regla de mínimas SN por defecto, la decidida (D-9)
    idx = {}
    for p in pas:
        idx.setdefault((p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d %H:%M")), []).append(p)
    print(f"\n== canal {canal}: {len(pas)} pasadas")
    for i, vol, h, plat in SEIS:
        k = (vol, "VIIRS375", h)
        ps = idx.get(k)
        if not ps:
            # la pasada puede caer en el minuto anterior/siguiente por la ventana de 120 s desde la PRIMERA fila
            cand = [p for p in pas if p.volcano == vol and p.sensor_bucket == "VIIRS375"
                    and abs((p.instante - __import__("datetime").datetime.strptime(h, "%Y-%m-%d %H:%M")).total_seconds()) <= 120]
            ps = cand
        if not ps:
            print(f"  id {i} {vol} {h}: SIN PASADA en el canal {canal} (la tabla no la trae)")
            salida.setdefault(str(i), {})[canal] = {"estado": "sin_pasada"}
            continue
        p = ps[0]
        prot_A = C.es_protegida(p, "A"); prot_B = C.es_protegida(p, "B")
        r_con, m_con = C.protegida_de_crater(p, V[vol]["inner_radius_km"], plataforma=plat)
        r_sin, m_sin = C.protegida_de_crater(p, V[vol]["inner_radius_km"], plataforma=None)
        tipos = tuple(sorted({f.get("tipo") for f in p.filas}))
        print(f"  id {i} {vol} {h}: estado {p.estado} vrp {p.vrp_mw} dist {p.dist_km} fuente {p.fuente} solo_ocr {p.solo_ocr} "
              f"filas {len(p.filas)} {tipos} | protegida A {prot_A} B {prot_B} | de cráter (plataforma {plat}): {r_con} {m_con} "
              f"| (plataforma None): {r_sin} {m_sin} | radio {V[vol]['inner_radius_km']}")
        salida.setdefault(str(i), {})[canal] = {"estado": p.estado, "vrp": p.vrp_mw, "dist": p.dist_km, "fuente": p.fuente,
                                                 "solo_ocr": p.solo_ocr, "protegida_A": prot_A, "protegida_B": prot_B,
                                                 "de_crater": r_con, "motivos": list(m_con), "motivos_sin_plataforma": list(m_sin)}
# controles sobre el canal union
pas = C.resumir_pasadas(ref, canal="union")
print()
print("== controles (canal union)")
RAD = {n: v["inner_radius_km"] for n, v in V.items() if "inner_radius_km" in v}   # 11 Tier A
# positivo: protegidas A de VIIRS375 que vienen de la TABLA (no solo_ocr), desde el hito de distancia, con distancia
# dentro del radio del volcán: la regla tiene que decir «de cráter» (el hito de Suomi NPP no aplica a la tabla).
pos = [p for p in pas if p.sensor_bucket == "VIIRS375" and not p.solo_ocr and C.es_protegida(p, "A")
       and p.dist_km is not None and p.volcano in RAD and p.dist_km <= RAD[p.volcano]
       and p.instante.strftime("%Y-%m-%d") >= C.HITO_OCR_DISTANCIA]
okp = [C.protegida_de_crater(p, RAD[p.volcano], plataforma="VIIRS_SNPP")[0] for p in pos]
print(f"  control positivo: protegidas A de la TABLA, VIIRS375, dist <= radio, desde {C.HITO_OCR_DISTANCIA}: {len(pos)}; "
      f"de cráter según la regla: {sum(okp)} de {len(pos)}")
for p in pos[:3]:
    print(f"    {p.volcano} {p.instante} vrp {p.vrp_mw} dist {p.dist_km} -> {C.protegida_de_crater(p, RAD[p.volcano], plataforma='VIIRS_SNPP')}")
assert pos and all(okp), "control positivo FALLA"
# negativo: en la lectura A no existe ninguna protegida VIIRS375 con distancia mayor al radio del volcán (el scraper
# etiqueta FALSO_POSITIVO fuera de su radio), así que el control negativo es sintético: la misma pasada positiva movida a
# radio + 1 km tiene que dar «lejos_del_crater», y movida a «sólo OCR, Suomi NPP, antes del hito» tiene que dar el motivo
# de las 6. Y una sólo OCR de Suomi NPP EN el día del hito o después tiene que volver a ser de cráter.
neg_real = [p for p in pas if p.sensor_bucket == "VIIRS375" and C.es_protegida(p, "A") and p.dist_km is not None
            and p.volcano in RAD and p.dist_km > RAD[p.volcano]]
print(f"  protegidas A VIIRS375 con dist > radio en la referencia: {len(neg_real)} (0 esperado: la lectura A es «dentro del radio del scraper»)")
import datetime as _dt
p0 = pos[0]
lejos = p0._replace(dist_km=RAD[p0.volcano] + 1.0)
r_lejos = C.protegida_de_crater(lejos, RAD[p0.volcano], plataforma="VIIRS_SNPP")
snpp_antes = p0._replace(solo_ocr=True, fuente="OCR", instante=_dt.datetime(2026, 9, 9, 6, 6))
r_antes = C.protegida_de_crater(snpp_antes, RAD[p0.volcano], plataforma="VIIRS_SNPP")
snpp_hito = p0._replace(solo_ocr=True, fuente="OCR", instante=_dt.datetime(2026, 10, 9, 5, 0))
r_hito = C.protegida_de_crater(snpp_hito, RAD[p0.volcano], plataforma="VIIRS_SNPP")
n20_antes = p0._replace(solo_ocr=True, fuente="OCR", instante=_dt.datetime(2026, 9, 9, 6, 6))
r_n20 = C.protegida_de_crater(n20_antes, RAD[p0.volcano], plataforma="VIIRS_NOAA20")
print(f"  control negativo sintético (misma pasada positiva, dist = radio + 1): {r_lejos}")
print(f"  sintético «sólo OCR, Suomi NPP, 2026-09-09»: {r_antes} | mismo pero 2026-10-09 (día del hito): {r_hito} | sólo OCR NOAA-20 2026-09-09: {r_n20}")
assert not r_lejos[0] and r_lejos[1] == ("lejos_del_crater",), "control negativo sintético FALLA"
assert not r_antes[0] and r_antes[1] == ("ocr_snpp_antes_del_hito",) and r_hito[0] and r_n20[0], "controles del hito FALLAN"
# sensibilidad: la misma fila, movida al día del hito, con plataforma NOAA-20 (lo único que cambia es el motivo del hito)
# ¿cuántas protegidas A de VIIRS375 caen por el mismo motivo que las 6? (denominador: todas las protegidas A del canal union)
protA = [p for p in pas if p.sensor_bucket == "VIIRS375" and C.es_protegida(p, "A")]
snpp_hito = [p for p in protA if p.solo_ocr and p.instante.strftime("%Y-%m-%d") < C.HITO_OCR_SNPP]
print(f"  protegidas A VIIRS375 (unión, toda la referencia): {len(protA)}; sólo OCR antes del hito SNPP (plataforma por "
      f"decidir con el record): {len(snpp_hito)}; de la tabla: {sum(1 for p in protA if not p.solo_ocr)}")
json.dump(salida, open(AQUI / "02_regla_903.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
