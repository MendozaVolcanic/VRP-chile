# VE2: el lector arma los brazos editando el record POSTERIOR al almacen y solo comprueba la distance_class de una segunda pasada por
# el almacen (C6). Aqui: para las grillas de tests/datos_s165_v375 (fixtures, no el marco) y para escenas sinteticas con alertados
# lejos y cerca, paso cada variante por store.append_record y comparo la PUBLICACION (predicado del tablero con node) y el VRP del
# record almacenado contra la variante sin almacenar. P1: si el almacen cambiara publicacion o VRP de una variante, aparece; control
# positivo: una variante con el VRP puesto en 0 sale distinta. P2: n de variantes comparadas se imprime (si fuera 0 el resultado no valdria).
import sys, json, copy, tempfile
from pathlib import Path
import numpy as np
R = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/adoring-wright-dc0404")
V = R/"experiments/_s162_v375"
sys.path.insert(0, str(V/"e_adenda2")); sys.path.insert(0, str(V)); sys.path.insert(0, str(R)); sys.path.insert(0, str(R/"scripts"))
import leer_posicion_v375e as L, evaluar as E
import banco_paridad as B
from pipeline import mirova_v750_codigo as MV
Vs = E.volcanes(); ih = B.inner_desde_html()
esp = json.loads((R/"tests/datos_s165_v375/esperado.json").read_text(encoding="utf-8"))
def pub(recs, inner):
    return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inner] for r in recs])]
n = 0; dif = []
with tempfile.TemporaryDirectory() as tmp:
    for q in esp["pasadas"]:
        z = R/f"tests/datos_s165_v375/grilla_{q['id']}.npz"
        if not z.exists(): continue
        g_ = np.load(z); mir, tir = g_["mir"].astype(np.float64), g_["tir"].astype(np.float64)
        v = Vs[q["volcan"]]; g = MV.grilla_del_volcan(q["volcan"], paso_m=375.0, clave_roi="roi_v375")
        rec, mascara, pos = L.record_de_la_via({"sensor": q["sensor"]}, g, mir, tir, {"dayflag": q["dayflag"], "sunglint": q["sunglint"]}, v, MV)
        d = L.distancias(mascara, mir, pos, L.pos_ref(g), 0.375, MV._cumulo_del_mas_radiante)
        if d is None: continue
        ra = L.por_el_almacen(rec, q["volcan"], v, tmp, dt="2026-07-01 05:00")
        if ra is None: print(q["id"], "almacen no escribio"); continue
        inner = ih[q["volcan"]]
        for b in L.BRAZOS_POS:
            vb = L.variante(ra, d[b], v["inner_radius_km"])
            va = L.por_el_almacen(vb, q["volcan"], v, tmp, dt="2026-07-01 05:00")
            (pb, pa) = pub([vb, va], inner)
            n += 1
            same_vrp = abs((va.get("primary_cluster") or {}).get("vrp_mw", 0) - (vb.get("primary_cluster") or {}).get("vrp_mw", 0)) < 1e-9
            if pb != pa or not same_vrp or va["distance_class"] != vb["distance_class"]:
                dif.append((q["id"], q["volcan"], b, pb, pa, same_vrp))
        print(q["id"], q["volcan"], {b: round(d[b], 2) for b in L.BRAZOS_POS}, "inner", inner)
    # control positivo: variante con vrp 0 publica distinto
    x = copy.deepcopy(ra); x["primary_cluster"]["vrp_mw"] = 0.0; x["vrp_mw"] = 0.0
    print("control positivo (vrp=0) distinto de la original:", pub([ra, x], inner)[0] != pub([ra, x], inner)[1])
print("variantes comparadas:", n, "con diferencia tras el almacen:", dif)
