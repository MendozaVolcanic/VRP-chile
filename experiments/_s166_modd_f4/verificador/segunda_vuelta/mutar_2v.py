# -*- coding: utf-8 -*-
"""Mutaciones PROPIAS de la segunda vuelta. Reusan el medidor del autor (mutar_evaluar_f4.correr: una copia del evaluador
con UNA linea cambiada, bateria entera contra la copia) sin modificarlo. Salida: mutar_2v_salida.txt en esta carpeta.
Uso: python mutar_2v.py [X01,X03,...]"""
import concurrent.futures as cf
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
F4 = AQUI.parents[1]
sys.path.insert(0, str(F4))
import mutar_evaluar_f4 as M

assert M.FUENTE == (F4 / "evaluar_f4.py").read_text(encoding="utf-8")

X = [
    ("CONTROL_ROTA", "PLACEBO = 1.2", "PLACEBO = = 1.2"),
    ("CONTROL_SYSEXIT", "def blob(ruta):", "import sys as _s\n_s.exit(1)\n\n\ndef blob(ruta):"),
    ("X01_inicio_e_18", 'INICIO_E = "2026-10-17"', 'INICIO_E = "2026-10-18"'),
    ("X02_inicio_e_exclusivo", "return str(dt)[:10] >= INICIO_E", "return str(dt)[:10] > INICIO_E"),
    ("X03_chillan_mag_mayor_que_cero", 'and _mag(f, "K") > 0 and _mag(f, b) > 0:', ":"),
    ("X04_eleg_vs_V_exige_sin_perdida", 'br[b]["p1_vs_V"]["estado"] != "VETADO"', 'br[b]["p1_vs_V"]["estado"] == "SIN PERDIDA"'),
    ("X05_identidad_total_o_mas", "ok = n_pob == n_grillas_censo and", "ok = n_pob >= n_grillas_censo and"),
    ("X06_otro_granulo_exclusivo", "frac_otro <= MAX_OTRO_GRANULO", "frac_otro < MAX_OTRO_GRANULO"),
    ("X08_otra_posicion_solo_tabla",
     'for x in p1(filas, bc, o)["perdidas"]})', 'for x in p1(filas, bc, o)["perdidas"] if not x["solo_ocr"]})'),
    ("X14_protegida_fuera_solo_tabla", 'if not f["_evaluable"] and _lab(f, True) == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]',
     'if not f["_evaluable"] and f["lab"] == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]'),
    ("X15_sin_filtro_E_en_sin_pasada", "[x for x in sin_pasada_nuestra if not _es_e(x[1])]", "sin_pasada_nuestra"),
    ("X16_e_excluido_sin_declarar", "res[\"e_excluido\"] = motivo", "res[\"e_excluido\"] = None"),
]

if __name__ == "__main__":
    sel = sys.argv[1].split(",") if len(sys.argv) > 1 else [x[0] for x in X]
    xs = [x for x in X if x[0] in sel or x[0].split("_")[0] in sel]
    with tempfile.TemporaryDirectory(prefix="mut2v_") as tmp, cf.ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda m: M.correr(*m, tmp), xs))
    lineas = ["%-40s %-10s %s" % r for r in res]
    txt = "\n".join(lineas)
    print(txt)
    (AQUI / "mutar_2v_salida.txt").write_text(txt + "\n", encoding="utf-8")
