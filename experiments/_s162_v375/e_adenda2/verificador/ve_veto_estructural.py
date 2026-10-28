# VE2: demostracion sintetica (escenas de la bateria del autor, ningun dato del marco) de que el veto de la RP (§8.5 paso 1) lo
# decide una protegida que K publica y que el port pierde en TODAS las posiciones (sin alertado en la caja: el caso documentado de
# las 3 OCR de Suomi NPP del lote S159, resultado_run40116289866/verificador/INFORME.md H5). P1: la demo ve el problema si la RP devuelve
# NINGUN BRAZO con 1 sola protegida independiente de la posicion. Control positivo: sin esa protegida, la misma escena da ELEGIDO CERCANO.
import sys, importlib.util, io
from pathlib import Path
E2 = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404/experiments/_s162_v375/e_adenda2")
sys.path[:0] = [str(E2), str(E2.parent), str(E2.parents[2]), str(E2.parents[2]/"scripts")]
spec = importlib.util.spec_from_file_location("bat", E2/"probar_adenda2.py"); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.LP = B.cargar("leer_posicion_v375e", E2); B.E, _ = B.LP.cargar_evaluar()
P = B.pasada
bajos = [P(100+k, B.celdas_lejana(), "pos_bajo", vol="Lascar", hora=f"2026-09-{10+k:02d} 05:00") for k in range(6)]  # cercano gana aqui
vacia = [P(20500, [], "far_tabla", vol="Lastarria", hora="2026-08-31 05:00", lote="FAR", pub_prod=0, dist_ref=20.0)]
sin = B.base_marco() + bajos + vacia
con = sin + [P(7, [], "pos_prot", vol="Tupungatito", hora="2026-08-01 05:00", tabla=False)]   # protegida OCR, K publica, 0 alertados
for nombre, lst in (("sin la protegida perdida por todos", sin), ("con 1 protegida solo-OCR que K publica y ningun brazo ve", con)):
    out, f = B.correr(lst)
    rp = out["regla_posicion"]
    print(f"{nombre}: fallas={f} -> {rp['veredicto']} | veto={ {a: len(v) for a, v in rp['detalle']['veto'].items()} } | tabla sola: {out['regla_posicion_tabla_sola']['veredicto']}")
