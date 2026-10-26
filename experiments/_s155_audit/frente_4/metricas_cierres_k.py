# -*- coding: utf-8 -*-
"""Re-mide, con los records de K (2026-09-18 a 2026-10-18) y con los de C0 de la ventana previa
(2026-08-18 a 2026-09-17), los numeros que sostienen cuatro cierres medidos bajo C0:
  A82  «hay cumulo con magnitud dentro del inner en 89,1 % de 4.800 pasadas MODIS negativas
        contra 93,7 % de 158 positivas» (sin contraste => el instrumento no separa)
  A81/D12 cara far->summit: distance_class 'far' con cumulo con magnitud dentro del inner
        (15-17 % de los records de cada mes, A81 S130)
  D13  fraccion de records con cumulo con magnitud que la cerca distance_class != summit oculta
        (31 % de los records, S124/S146)
  A23/D9 cumulos topados en 5,0 MW exacto y cumulos sobre 5 MW
Denominador: records NOCTURNOS (filtro de banco_paridad) de los 11 Tier A; etiquetas pos/neg_limpio
de banco_paridad (regla de minimas 'original'). Ventanas de 31 dias cada una: la estacion cambia
entre ventanas (agosto-septiembre contra septiembre-octubre), asi que la comparacion C0/K tiene un
confusor estacional declarado; las diferencias que se reportan son de un orden de magnitud.
P1: si K no hubiera cambiado nada, las dos ventanas darian fracciones parecidas; lo veriamos.
P2: control positivo: triggered_test1 > 0 en la ventana C0 y = 0 en la K (si el lector de campos
estuviera muerto, darian 0 las dos). Control de definicion: la cuenta far->summit se hace tambien
con el radio inner duplicado (debe subir o quedar igual, nunca bajar).
"""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
filas = B.cargar_referencia_unificada(B.SNAP_CONS, B.SNAP_OCR)
# triggered_test1 por record (no lo trae cargar_nuestros): indice aparte
t1 = {}
for v in B.VOLS:
    for r in json.load(open(B.DATA / f"{v}.json", encoding="utf-8"))["records"]:
        t1[(v, r.get("datetime_utc"), r.get("sensor"))] = bool(r.get("triggered_test1"))
out = {}
for nombre, ven in [("C0", ("2026-08-18", "2026-09-17")), ("K", ("2026-09-18", "2026-10-18"))]:
    por_vb, ns, nv, _ = B.indexar_referencia(filas, coords, ven)
    recs = B.cargar_nuestros(coords, inner, ven)
    B.etiquetar(recs, por_vb, ns, nv)
    res = {}
    for b in B.BUCKETS:
        R = [r for r in recs if r["b"] == b]
        def con_mag_inner(r, f=1.0):
            return (r["pc_vrp"] or 0) > 0 and r["pc_dist"] is not None and r["pc_dist"] <= f * inner[r["vol"]]
        neg = [r for r in R if r["lab"] == "neg_limpio"]; pos = [r for r in R if r["lab"] == "pos"]
        conmag = [r for r in R if (r["pc_vrp"] or 0) > 0]
        res[b] = {
            "n_records": len(R),
            "A82_inner_en_neg": f"{sum(map(con_mag_inner, neg))}/{len(neg)}",
            "A82_inner_en_pos": f"{sum(map(con_mag_inner, pos))}/{len(pos)}",
            "A81_far_con_mag_inner": f"{sum(1 for r in R if r['dc'] == 'far' and con_mag_inner(r))}/{len(R)}",
            "A81_ctrl_inner_x2": sum(1 for r in R if r['dc'] == 'far' and con_mag_inner(r, 2.0)),
            "D13_ocultos_por_cerca": f"{sum(1 for r in conmag if r['dc'] != 'summit')}/{len(conmag)}",
            "A23_topados_5": sum(1 for r in R if r["pc_vrp"] == 5.0),
            "A23_sobre_5": sum(1 for r in R if (r["pc_vrp"] or 0) > 5.0),
            "publica": sum(r["pub"] for r in R),
        }
    # control triggered_test1 (por volcan/fecha, cualquier sensor del bucket)
    n_t1 = 0
    for (v, dt, s), val in t1.items():
        if dt and ven[0] <= dt[:10] <= ven[1] and val:
            n_t1 += 1
    res["ctrl_triggered_test1_ventana"] = n_t1
    out[nombre] = res
    print(f"\n== {nombre} {ven}")
    for k, v in res.items():
        print(" ", k, v)
(Path(__file__).parent / "metricas_cierres_k.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
