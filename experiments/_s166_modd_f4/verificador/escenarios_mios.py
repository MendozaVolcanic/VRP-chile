# -*- coding: utf-8 -*-
"""Escenarios PROPIOS del verificador (VF4) contra evaluar_f4.py del commit e1f6b197b. Reutilizan el mundo sintético y
el predicado sintético de probar_evaluar_f4.py (importado, no copiado). Uso: python escenarios_mios.py [S1,S2,...]"""
import copy, json, os, sys, tempfile
from pathlib import Path
AQUI = Path(__file__).resolve().parent
F4 = AQUI.parent
sys.path.insert(0, str(F4))
import probar_evaluar_f4 as P
P.EV = P.cargar(str(F4 / "evaluar_f4.py"))
EV = P.EV
F, mundo, dia, VOLS, correr, g = P.F, P.mundo, P.dia, P.VOLS, P.correr, P.g

def resumen(r):
    b = r["brazos"]
    return {"veredicto": r["veredicto"], "posicion": r["posicion_elegida"], "motivo": r["posicion_motivo"],
            "P1": {k: b[k]["p1"]["estado"] for k in b}, "P2": {k: (b[k]["p2"]["estado"], b[k]["p2"]["neto"], b[k]["p2"]["B"]) for k in b},
            "P2l_vs_K": {k: (b[k]["p2l_vs_K"]["estado"], b[k]["p2l_vs_K"]["neto"]) for k in b},
            "rojos": [k for k, c in r["controles"].items() if (c if isinstance(c, str) else c.get("estado")) != "OK"]}

def S1_pico_pierde_protegida_que_V_recupera():
    """V-pico arregla 6 publicaciones de más de V, pero pierde una protegida que V publica y K no. ¿La regla lo elige?"""
    f = mundo()
    for i in range(6):
        f.append(F(VOLS[i % 5], dia(100 + i) + " 05:00", "neg_limpio", v=0.2, vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}))
    f.append(F("NevadosDeChillan", dia(120) + " 07:20", "protegida", k=None, v=1.5, mir=1.6, z=58.0,
               vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0}))
    r = correr(f)
    print("S1", json.dumps(resumen(r), ensure_ascii=False))
    print("   P1 V-pico:", r["brazos"]["V-pico"]["p1"]["estado"], "| mirova_sin_ninguno:", r["brazos"]["V-pico"]["p1"]["mirova_sin_ninguno"])
    print("   descriptivas V-pico:", r["descriptivas_posicion"]["V-pico"][:3])

def S2_cercano_recupera_protegida_sin_credito():
    """V radiante la deja lejos (no publica), K tampoco, cercano sí la publica: la regla de posición no le da crédito."""
    f = mundo()
    f.append(F("Lascar", dia(120) + " 03:00", "protegida", k=None, v=2.0, mir=2.1, vd={"radiante": 9.0, "cercano": 0.5, "pico": 9.0}))
    r = correr(f)
    print("S2", json.dumps(resumen(r), ensure_ascii=False))
    print("   descriptivas V-cercano:", r["descriptivas_posicion"]["V-cercano"])

def S3_main_end_to_end_sin_sin_pasada():
    """evaluar_f4.main() de punta a punta con una población SIN la clave sin_pasada_nuestra y SIN pasada para una protegida de MIROVA."""
    import subprocess
    f = mundo()
    tmp = Path(tempfile.mkdtemp(prefix="vf4_e2e_", dir=str(AQUI)))
    art = tmp / "art"; art.mkdir()
    pob = {"pasadas": []}
    with open(art / "f4_parte01.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"tipo": "cabecera", "x": 1}) + "\n")
        for x in f:
            row = {k: v for k, v in x.items() if k not in ("id", "lab", "vrp_mirova", "tramo", "solo_ocr")}
            row["tipo"] = "record"
            fh.write(json.dumps(row) + "\n")
            pob["pasadas"].append({"vol": x["vol"], "dt": x["dt"], "lab": x["lab"], "vrp_mirova": x["vrp_mirova"], "tramo": x["tramo"], "solo_ocr": x["solo_ocr"]})
    (tmp / "pob.json").write_text(json.dumps(pob), encoding="utf-8")
    cg = [[x["vol"], x["dt"]] for x in f]
    (tmp / "idn.json").write_text(json.dumps({"con_grilla": cg, "pasadas": [{"vol": v, "dt": d, "mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for v, d in cg]}), encoding="utf-8")
    (tmp / "ext.json").write_text(json.dumps({k: {"estado": "OK"} for k in P.EXT_OK}), encoding="utf-8")
    p = subprocess.run([sys.executable, str(F4 / "evaluar_f4.py"), "--art", str(art), "--poblacion", str(tmp / "pob.json"),
                        "--identidad", str(tmp / "idn.json"), "--externos", str(tmp / "ext.json"), "--salida", str(tmp / "res.json")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print("S3 exit", p.returncode); print(p.stdout[-1800:]); print(p.stderr[-800:])

if __name__ == "__main__":
    sel = sys.argv[1].split(",") if len(sys.argv) > 1 else ["S1", "S2", "S3"]
    for n, fn in (("S1", S1_pico_pierde_protegida_que_V_recupera), ("S2", S2_cercano_recupera_protegida_sin_credito), ("S3", S3_main_end_to_end_sin_sin_pasada)):
        if n in sel: fn()

def S4_identidad_con_grilla_corta():
    """con_grilla viene del archivo de identidad, no se coteja con la población: si identidad_f4.py declara 1 pasada, el control da OK."""
    f = mundo()
    k0 = (f[0]["vol"], f[0]["dt"])
    idn = {k0: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True}}
    r = correr(f, ident=idn, con_grilla=[k0])
    print("S4 identidad con 1 de %d pasadas:" % len(f), r["controles"]["identidad"]["estado"], "| veredicto", r["veredicto"])

def S5_k_difiere_ausente():
    """Si el arnés no escribe k_difiere_de_guardado, el control K = producción no puede fallar por esa vía."""
    f = mundo()
    for x in f: x.pop("k_difiere_de_guardado", None)
    r = correr(f)
    print("S5 sin campo k_difiere_de_guardado:", r["controles"]["k_produccion"]["estado"])

if __name__ == "__main__":
    for n, fn in (("S4", S4_identidad_con_grilla_corta), ("S5", S5_k_difiere_ausente)):
        if len(sys.argv) > 1 and n in sys.argv[1].split(","): fn()
