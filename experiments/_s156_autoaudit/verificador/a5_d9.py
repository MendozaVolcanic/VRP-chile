"""A5: aplicar_d9 (audit) contra clase_mirova.aplicar_regla_minimas sobre la referencia unificada."""
import sys, os
from collections import Counter
W, REF = sys.argv[1:3]
sys.path.insert(0, W); sys.path.insert(0, os.path.join(W, "scripts"))
import scripts.auto_audit_weekly as aa
import clase_mirova as cm
from referencia_mirova_unificada import cargar_referencia_unificada
cons, ocr = os.path.join(REF, "registro_vrp_consolidado.csv"), os.path.join(REF, "registro_vrp_ocr.csv")
al = aa.alertas_mirova(cons, ocr)
filtradas = aa.aplicar_d9(al, "SN")
quitadas = {(a["volcano"], a["sensor_bucket"], (a["fecha_utc"] or "")[:16]) for a in al} - \
           {(a["volcano"], a["sensor_bucket"], (a["fecha_utc"] or "")[:16]) for a in filtradas}
uni = cargar_referencia_unificada(cons, ocr)
canon = cm.aplicar_regla_minimas(uni, "SN").minimas
pas_loader = {(a["volcano"], a["sensor_bucket"], (a["fecha_utc"] or "")[:16]) for a in al}
print("alertas loader:", len(al), "pasadas loader:", len(pas_loader))
print("minimas audit:", len(quitadas), " minimas canonicas:", len(canon), " canonicas presentes en loader:", len(canon & pas_loader))
print("audit quita y canon no:", sorted(quitadas - canon))
print("canon minima (en loader) y audit no quita:", sorted((canon & pas_loader) - quitadas))
# nivel noche: (vol,b,fecha) con alerta nocturna-agnostica
n_aud = {(k[0], k[1], k[2][:10]) for k in pas_loader - quitadas}
canon_rows = cm.aplicar_regla_minimas(uni, "SN").filas
n_can = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:10]) for f in canon_rows if f["tipo"] in cm.TIPOS_ALERTA}
print("noches alerta audit no en canon (todas):", len(n_aud - n_can), sorted(n_aud - n_can)[:15])
print("noches alerta canon no en audit (todas):", len(n_can - n_aud), sorted(n_can - n_aud)[:15])
w = lambda s: {k for k in s if "2026-08-20" <= k[2] <= "2026-10-19"}
print("en ventana: audit-canon", sorted(w(n_aud - n_can)), " canon-audit", sorted(w(n_can - n_aud)))
# filas con VRP vacio en alerta y marcas sin geometria con tipo ALERTA_TERMICA_OCR
import csv
for p, s in ((cons, "CONS"), (ocr, "OCR")):
    c = Counter()
    for r in csv.DictReader(open(p, encoding="utf-8")):
        t = (r.get("Tipo_Registro") or "").strip()
        if t in cm.TIPOS_ALERTA and not (r.get("VRP_MW") or "").strip(): c["alerta_vrp_vacio"] += 1
        if t in cm.TIPOS_ALERTA and ((r.get("Metodo_Validacion") or "").strip() == "vrp_sin_geometria_propia"
                                     or (r.get("Clasificacion Mirova") or "").strip() == "SIN_GEOMETRIA"): c["alerta_con_marca_singeo"] += 1
    print(s, dict(c))
