"""V0-109b: una pasada de MIROVA CON ALERTA que nosotros nunca bajamos, cae en silencio?
Camino: banco_paridad.alertas_sin_record (la funcion de la base que cuenta justo eso) sobre 2 ventanas.
P1: si la funcion estuviera rota, daria 0 siempre; el control positivo es la mutacion: se quita de nuestros records
una pasada que SI tiene alerta de MIROVA y la cuenta tiene que subir en 1.
P2: si el instrumento estuviera muerto (sin referencia) devolveria Counter vacio y la mutacion no lo cambiaria.
Vara: arbol de la base extraido por el auditor (git archive de 752d348bc), SNAP_CONS/SNAP_OCR del arbol.
Ventanas: 2026-09-14 a 2026-11-06 y 2026-03-01 a 2026-11-06 (denominador: filas-alerta nocturnas de la referencia)."""
import io
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f0\arbol")
sys.path.insert(0, str(ARBOL / "scripts"))
sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
for ventana in [("2026-09-14", "2026-11-06"), ("2026-03-01", "2026-11-06")]:
    recs = bp.cargar_nuestros(coords, inner, ventana)
    por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)
    sr = bp.alertas_sin_record(por_vb, recs)
    n_alertas = sum(1 for k, lista in por_vb.items() for dt, f in lista if bp.es_alerta(f["tipo"]))
    print(f"\nventana {ventana}: pasadas nuestras {len(recs)}, filas-alerta de MIROVA en la referencia {n_alertas}, "
          f"alertas sin record nuestro {sum(sr.values())}  por (volcan, sensor): {dict(sr)}")
    r0 = next(r for r in recs if r["lab"] == "pos")
    mut = [r for r in recs if r is not r0]
    sr2 = bp.alertas_sin_record(por_vb, mut)
    print(f"  CONTROL positivo: se quita el record {r0['vol']} {r0['b']} {r0['dt']}: sin_record {sum(sr.values())} -> {sum(sr2.values())}")
