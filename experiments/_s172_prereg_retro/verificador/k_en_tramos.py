# -*- coding: utf-8 -*-
"""VPR172 V-3/V-4: con K de disco (origin/main, records con codigo_sha) y la referencia de origin/main, cuenta por tramo y sensor
las etiquetas de nuestras pasadas, cuantas publica K y los BLOQUES noche-volcan donde K se equivoca (cota del poder de P2: la via
solo puede ser discordante con K en bloques donde K o la via yerran).
P1 (roto?): control positivo = tramo V2 (03-01..10-16) donde MOD-D sellado fija 50 protegidas y 42 bajo 1 MW en MODIS.
P2 (instrumento muerto): se imprime n records por tramo y n pareados; 0 records = SIN DATO."""
import sys, os, io, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts"); os.chdir(EXP)
import banco_paridad as bp
from clase_mirova import alerta_protegida
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas_all = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
filas_cons = [f for f in filas_all if f["source"]=="CONS"]
TR = {"F26-M": ("2026-02-01","2026-02-28",["MODIS"]), "F26-M3":("2026-03-01","2026-03-31",["MODIS"]),
      "F26-V":("2026-02-01","2026-03-31",["VIIRS375","VIIRS750"]),
      "V2c":("2026-03-01","2026-10-16",["MODIS","VIIRS375","VIIRS750"]),
      "DM":("2026-10-01","2026-10-16",["MODIS","VIIRS375","VIIRS750"])}
ventana_total = ("2026-02-01","2026-10-16")
recs = bp.cargar_nuestros(coords, inner, ventana_total)
print("records nocturnos 2026-02-01..10-16:", len(recs))
print("por sensor raw:", collections.Counter(r["sensor"] for r in recs))
print("regimen/perfil:", collections.Counter((r["perfil"]) for r in recs).most_common(5))
shas = collections.Counter((r["sha"] or "NA")[:9] for r in recs)
print("codigo_sha (top):", shas.most_common(6))
out = {}
for canal, fl in (("tabla", filas_cons), ("union", filas_all)):
    por_vb, ns, nv, n = bp.indexar_referencia(fl, coords, ventana_total, regla_minimas="SN")
    import copy
    rr = [dict(r) for r in recs]
    bp.etiquetar(rr, por_vb, ns, nv)
    for r in rr:
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        al = [f for f in filas if bp.es_alerta(f["tipo"])]
        r["prot"] = bool(al) and any(alerta_protegida(f) for f in al)
    for nombre,(d,h,bs) in TR.items():
        sel = [r for r in rr if d <= r["noche"] <= h and r["b"] in bs]
        if nombre.startswith("F26"):
            sel = [r for r in sel if not (r["vol"]=="Tupungatito" and r["noche"] < "2026-02-23")]
        for b in bs:
            s = [r for r in sel if r["b"]==b]
            lab = collections.Counter(r["lab"] for r in s)
            prot = [r for r in s if r["lab"]=="pos" and r["prot"]]
            bajo = [r for r in s if r["lab"]=="pos" and not r["prot"]]
            neg = [r for r in s if r["lab"]=="neg_limpio"]
            far = [r for r in s if r["lab"]=="far_ref"]
            kmiss_p = [r for r in prot if not r["pub"]]
            kmiss_b = [r for r in bajo if not r["pub"]]
            kfp = [r for r in neg if r["pub"]]
            kfp_far = [r for r in far if r["pub"]]
            bloques = {(r["vol"], r["noche"]) for r in kmiss_b+kfp}
            bloques_p2p = bloques | {(r["vol"], r["noche"]) for r in kfp_far}
            sens_sinfo = collections.Counter((r["sensor"], r["lab"]) for r in s if r["b"].startswith("VIIRS"))
            d_ = dict(canal=canal, tramo=nombre, bucket=b, n_rec=len(s), etiquetas=dict(lab), prot=len(prot), prot_K_pierde=len(kmiss_p),
                      bajo=len(bajo), bajo_K_pierde=len(kmiss_b), neg=len(neg), neg_K_publica=len(kfp), far=len(far), far_K_publica=len(kfp_far),
                      bloques_donde_K_yerra=len(bloques), bloques_con_far=len(bloques_p2p),
                      K_pub_prot_vol=dict(collections.Counter(r["vol"] for r in prot if r["pub"])))
            out[f"{canal}|{nombre}|{b}"] = d_
            print(json.dumps(d_, ensure_ascii=False))
            if b.startswith("VIIRS"):
                por_sat = collections.defaultdict(collections.Counter)
                for r in s: por_sat[r["sensor"]][r["lab"]] += 1
                print("    por satelite:", {k: dict(v) for k,v in por_sat.items()})
json.dump(out, open(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\k_en_tramos_salida.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
