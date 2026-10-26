"""Verificador S159 MxD03: mediciones que el borrador no hizo.
(a) alertas MODIS nocturnas de MIROVA en la ventana SIN record nuestro a +-120 s (fuera del censo);
(b) cuantas protegidas / bajo1 dependen SOLO del OCR (A119 a: antes del 2026-06-13 decide la tabla sola);
(c) granulos MODIS distintos detras de los 5.465 records (costo);
(d) negativos limpios que son mitad de una pasada partida (otro record mismo volcan y plataforma a 5 min);
(e) que publica K en sin_info / far_ref (lo que P1 y P2 no ven).
Pregunta 1: si el conteo estuviera roto, (b) no reproduciria las 5 alertas OCR de Lascar que cita el borrador
y A119; (a) se contrasta con alertas_sin_record de banco_paridad. Pregunta 2: con referencia vacia (a) y (b)
darian 0 y el script imprime n de filas; control positivo de (d): las 18+130 del frente de pareo deben aparecer
como partidas en la ventana larga.
Uso: python extra_verif.py DIR_JSON DIR_DL"""
import collections, io, json, sys
from datetime import timedelta
from pathlib import Path
ROOT = Path(r"C:\vrp-trabajo\s159-pruebas")
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(Path(__file__).parent))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
from auto_audit_weekly import _coords_por_volcan

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    data, dl = Path(sys.argv[1]), Path(sys.argv[2])
    ventana = ("2026-03-01", "2026-10-16")
    filas = cargar_referencia_unificada(dl / "registro_vrp_consolidado.csv", dl / "registro_vrp_ocr.csv")
    coords = _coords_por_volcan(); inner = bp.inner_desde_html()
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
    print("filas ref indexadas", n_ref)
    recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
    bp.etiquetar(recs, por_vb, ns, nv)
    modis = [r for r in recs if r["b"] == "MODIS"]
    print("records MODIS", len(modis))
    # (a)
    sr = bp.alertas_sin_record(por_vb, recs)
    print("(a) alertas nocturnas SIN record a 120 s, MODIS:", {k: v for k, v in sr.items() if k[1] == "MODIS"})
    ts = collections.defaultdict(list)
    for r in modis: ts[r["vol"]].append(r["dt"])
    for (vol, b), lista in por_vb.items():
        if b != "MODIS": continue
        for dt, f in lista:
            if bp.es_alerta(f["tipo"]) and not any(abs((t - dt).total_seconds()) <= 120 for t in ts[vol]):
                near = sorted(ts[vol], key=lambda t: abs((t - dt).total_seconds()))[:1]
                print("   sin record:", vol, f["fecha_utc"], f["tipo"], f["source"], f.get("vrp_mw"), "record mas cercano", near)
    # (b)
    cnt = collections.Counter()
    for r in modis:
        if r["lab"] != "pos": continue
        fp = bp.parear(por_vb.get((r["vol"], "MODIS"), []), r["dt"], 120)
        al = [f for f in fp if bp.es_alerta(f["tipo"])]
        vmax = max((f["vrp_mw"] or 0) for f in al)
        cls = "protegida" if vmax >= 1 else "bajo1"
        cons = [f for f in al if f["source"] == "CONS"]
        vcons = max(((f["vrp_mw"] or 0) for f in cons), default=None)
        if not cons:
            fuente = "solo_OCR"
        elif vcons < 1 <= vmax:
            fuente = "CONS_bajo1_OCR_lleva_a_protegida"
        else:
            fuente = "CONS"
        cnt[(cls, fuente, r["pub"])] += 1
        if fuente != "CONS":
            print("   (b)", r["vol"], r["dt"], cls, fuente, "pubK", r["pub"], "z", r["z"], [(f["source"], f["tipo"], f["vrp_mw"]) for f in al])
    print("(b) (clase, fuente, pubK):", dict(sorted(cnt.items())))
    # (c)
    gr = set(); sin_g = 0
    for vol in bp.VOLS:
        d = json.load(open(data / f"{vol}.json", encoding="utf-8"))
        idx = {(r.get("datetime_utc"), r.get("sensor")): r.get("granule") for r in d["records"]}
        for r in modis:
            if r["vol"] != vol: continue
            g = idx.get((r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"]))
            if g: gr.add(g)
            else: sin_g += 1
    print(f"(c) granulos MODIS distintos: {len(gr)} para {len(modis)} records; records sin campo granule: {sin_g}")
    # (d)
    porvp = collections.defaultdict(list)
    for r in modis: porvp[(r["vol"], r["sensor"])].append(r)
    part = collections.Counter()
    for r in modis:
        hermano = [o for o in porvp[(r["vol"], r["sensor"])] if o is not r and abs((o["dt"] - r["dt"]).total_seconds()) == 300]
        if hermano:
            part[(r["lab"], r["pub"], tuple(sorted((h["lab"], h["pub"]) for h in hermano)))] += 1
    print("(d) records que son mitad de pasada partida (lab, pubK, hermanos):")
    for k, v in sorted(part.items(), key=lambda x: -x[1]): print("   ", k, v)
    print("    total partidas:", sum(part.values()), "de ellas neg_limpio:", sum(v for k, v in part.items() if k[0] == "neg_limpio"))
    # (e)
    e = collections.Counter((r["lab"], r["pub"]) for r in modis)
    print("(e) (lab, pubK):", dict(sorted(e.items())))
    # noche cubierta por VIIRS para neg publicados por K
    vpub = {(r["vol"], r["noche"]) for r in recs if r["b"] != "MODIS" and r["pub"]}
    print("(f) K publica en neg_limpio MODIS por volcan:", dict(collections.Counter(r["vol"] for r in modis if r["lab"] == "neg_limpio" and r["pub"])))

if __name__ == "__main__":
    main()


def detalle_neg_pub():
    """(g) negativos limpios que K publica: volcan, cenit, lado, distancia del cumulo, VRP; y cuantos estan a menos
    de DELTA del borde de inner (exposicion, misma regla del borrador)."""
    import sustrato_copia as s
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    data, dl = Path(sys.argv[1]), Path(sys.argv[2])
    ventana = ("2026-03-01", "2026-10-16")
    filas = cargar_referencia_unificada(dl / "registro_vrp_consolidado.csv", dl / "registro_vrp_ocr.csv")
    coords = _coords_por_volcan(); inner = bp.inner_desde_html()
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas="SN")
    recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
    bp.etiquetar(recs, por_vb, ns, nv)
    az = {}
    for vol in bp.VOLS:
        for r in json.load(open(data / f"{vol}.json", encoding="utf-8"))["records"]:
            az[(vol, r.get("datetime_utc"), r.get("sensor"))] = r.get("sensor_azimuth_deg")
    c = collections.Counter()
    for r in recs:
        if r["b"] != "MODIS" or r["lab"] != "neg_limpio" or not r["pub"]: continue
        t = s.tramo(r["z"]); l = s.lado(r["sensor"], az.get((r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"])))
        exp = r["pc_dist"] is not None and abs(r["pc_dist"] - inner[r["vol"]]) < s.DELTA.get((t, l), 0)
        c[(r["vol"], t, l, exp)] += 1
        print("  negpub", r["vol"], r["dt"], r["sensor"], t, l, "pc_dist", r["pc_dist"], "pc_vrp", r["pc_vrp"], "disp", r.get("disp"), "expuesta", exp)
    print("(g) negativos publicados por (volcan, tramo, lado, expuesta):")
    for k, v in sorted(c.items()): print("   ", k, v)
