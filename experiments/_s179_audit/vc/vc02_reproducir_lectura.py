# -*- coding: utf-8 -*-
"""Verificador VC, S179. vc02: re-corre el lector de la retrospectiva (leer_retro.py del worktree de la ref de lectura
s178-retro-lectura, sin modificarlo) paso por paso sobre los insumos de vc01, y guarda la tabla por pasada.

Repite los pasos de leer_retro.main (l. 1402 a 1462 de la ref de lectura) llamando a sus funciones, con los mismos
argumentos que la lectura: --caja-v750 B4, --v750a-sellado no, posicion radiante, montaje/excepciones/trozos de
experiments/_s178_lectura/ y referencias congeladas de _congelado/. OSF: data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv
del worktree.

PREGUNTAS DEL INSTRUMENTO. (1) Si la reproduccion estuviera rota (otros insumos, otro paso), lo veria? Si: el JSON de
sensores se compara campo a campo con experiments/_s178_lectura/lectura.json; un solo campo distinto se lista.
(2) Si el instrumento estuviera muerto? Sin filas o sin sensores, aborta; la comparacion con el JSON commiteado es el
control positivo (tiene que dar igual en los veredictos que la lectura imprimio).
Salida: D:/vrp-trabajo/temporales/s179-audit/vc/filas.pkl (filas con _t) y vc02_reproducir_lectura_salida.txt
"""
import collections, importlib.util, json, os, pickle, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
W = Path("D:/vrp-trabajo/worktrees/s178-lectura")
INS = Path("D:/vrp-trabajo/temporales/s179-audit/vc/insumos")
TMP = Path("D:/vrp-trabajo/temporales/s179-audit/vc")
L = W / "experiments/_s178_lectura"
spec = importlib.util.spec_from_file_location("leer_retro_vc", W / "experiments/_s172_retro_paquete/leer_retro.py")
LR = importlib.util.module_from_spec(spec)
sys.modules["leer_retro_vc"] = LR
spec.loader.exec_module(LR)
print("lector importado desde", LR.__file__, "| RAIZ", LR.RAIZ)
R = LR.Reglas()
pred = LR._predicado_por_defecto(R)
import banco_paridad as bp
import yaml
from referencia_mirova_unificada import cargar_referencia_unificada
print("banco_paridad desde", bp.__file__)
leer = lambda p: json.loads(Path(p).read_text(encoding="utf-8")) if p else None  # noqa: E731
cons, ocr = L / "_congelado/registro_vrp_consolidado.csv", L / "_congelado/registro_vrp_ocr.csv"
osf = W / "data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"
cand = LR.candado(leer(L / "manifiesto.json"), requeridos=LR.REQUERIDOS_MANIFIESTO + tuple(LR.rutas_referencias((cons, ocr, osf))))
print("candado:", cand["estado"])
via, rep_v = LR.cargar_carpeta(INS / "via")
k, rep_k = LR.cargar_carpeta(INS / "k_e7cfbaf54")
kg, _ = LR.cargar_carpeta(INS / "kgemelo")
coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
es_noche = lambda vol, b, dt: not bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt)  # noqa: E731
sdt = leer(L / "sin_dato_trozos.json") or []
filas = LR.armar_pasadas(via, k, kg, es_noche, inner, sdt)
if not filas:
    sys.exit("ABORTA: 0 filas")
no_r25 = [f for f in filas if f["tramo"] != "R25"]
ref = cargar_referencia_unificada(cons, ocr)
LR.etiquetar_tabla(no_r25, ref, coords)
sin_pasada = LR.alertas_sin_pasada(no_r25, ref, coords)
for f in filas:
    f.setdefault("lab", "sin_info")
    f.setdefault("vrp_mirova", None)
LR.tabla_publica(R, filas, pred)
volc = {v["name"]: v for v in yaml.safe_load((LR.RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
osf_filas = LR.leer_osf(osf, volc, es_noche)
osf_res = LR.p1_osf(filas, osf_filas)
exc = leer(L / "excepciones_ck.json") or []
comunes = {"candado": cand, "_repetidas": rep_v + rep_k, "c_k_puro": LR.c_k_puro(filas),
           "c_k": LR.c_k(filas, exc, LR.TIER_A, LR.sobras_kgemelo(kg, k)),
           "nulo_runner": LR.nulo_runner(R, filas, exc), "c_montaje": LR.validar_montaje(leer(L / "montaje.json"))}
res = {}
for s in LR.SENSORES:
    res[s] = LR.leer_sensor(R, filas, s, comunes, pred, False, "B4", "radiante", osf_res,
                            [f for f in filas if f["tramo"] == "R25"], None)
    print(LR.linea_veredicto("", s, res[s]))
ori = json.loads((L / "lectura.json").read_text(encoding="utf-8"))
mio = json.loads(json.dumps({"sensores": res, "osf": osf_res, "alertas_de_la_tabla_sin_pasada_nuestra": sin_pasada},
                            ensure_ascii=False, default=str))
for clave in ("sensores", "osf", "alertas_de_la_tabla_sin_pasada_nuestra"):
    print(f"control: {clave} igual al lectura.json commiteado: {mio[clave] == ori[clave]}")
    if mio[clave] != ori[clave] and isinstance(mio[clave], dict):
        for kk in mio[clave]:
            if mio[clave][kk] != ori[clave].get(kk):
                print("   difiere:", kk)
pickle.dump({"filas": filas, "osf_filas": osf_filas, "osf_res": osf_res, "res": res, "sin_pasada": sin_pasada,
             "ref_n": len(ref)}, open(TMP / "filas.pkl", "wb"))
print("filas:", len(filas), "| guardadas en", TMP / "filas.pkl")
