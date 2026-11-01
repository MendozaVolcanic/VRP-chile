"""Casos de vigilancia ciega que el script NO declara: referencia de MIROVA muerta y produccion muerta.
Uso: python ciega.py <raiz> <ref> <out>"""
import csv, os, sys, json
raiz, ref, out = sys.argv[1:4]
sys.path.insert(0, raiz); sys.path.insert(0, os.path.join(raiz, "scripts"))
import scripts.vigilancia_sombra as vs
def recortar(dst, hasta):
    os.makedirs(dst, exist_ok=True)
    for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        with open(os.path.join(ref, f), encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh); rows = [r for r in rd if r["Fecha_Satelite_UTC"][:10] <= hasta]; campos = rd.fieldnames
        with open(os.path.join(dst, f), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(rows)
def correr(nombre, refdir, hoy="2026-10-19", mod=None):
    vs.aa.CONS = os.path.join(refdir, "registro_vrp_consolidado.csv"); vs.aa.OCR = os.path.join(refdir, "registro_vrp_ocr.csv")
    orig = vs.cargar_insumos
    if mod:
        vs.cargar_insumos = lambda win: mod(*orig(win))
    try:
        o = vs.evaluar(hoy)
    finally:
        vs.cargar_insumos = orig
    print(f"{nombre:55s} veredicto={o['veredicto']} avisos={o.get('avisos')} n_pasadas={o.get('n_pasadas_alerta')}")
    return o
correr("referencia de hoy", ref)
recortar(os.path.join(out, "ref_hasta_0930"), "2026-09-30")
correr("referencia muerta desde 2026-09-30 (scraper caido 19 dias)", os.path.join(out, "ref_hasta_0930"))
recortar(os.path.join(out, "ref_vacia"), "0000")
correr("referencia vacia (solo encabezados)", os.path.join(out, "ref_vacia"))
def prod_muerta(filas, prod, sombra):
    return filas, [r for r in prod if r["noche"] < "2026-10-05"], sombra
correr("produccion muerta en los 11 volcanes desde 2026-10-05", ref, mod=prod_muerta)
def prod_vacia(filas, prod, sombra):
    return filas, [], sombra
correr("produccion vacia (0 records de K)", ref, mod=prod_vacia)
