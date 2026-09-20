# -*- coding: utf-8 -*-
"""V-01: '214 visibles frios+path-D, 207 (96,7 %) MIROVA-confirmados' y '199 far, 0 fuga' (D9, S113).
(1) Si roto fallaria? se barre una grilla de definiciones; si NINGUNA se acerca a 214/207 la cifra no se reproduce; se imprime n siempre.
(2) Instrumento muerto? control positivo: la definicion mas laxa de confirmacion (cualquier fila de referencia, incluida RUTINA,
    misma fecha) debe dar ~100 % en 2026; si diera 0 el pareo estaria roto.
Nota: el corpus de hoy incluye reprocesos posteriores a S113 (nadir, #535), asi que 'no se reproduce hoy' no prueba que no fuera cierto en junio."""
import io, sys, itertools, datetime as dt
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); REF = referencia()
def claves(tipos, modo):
    K = set()
    for f in REF:
        if f["tipo"] not in tipos: continue
        d0 = dt.date.fromisoformat(f["fecha"])
        if modo == "fecha+sensor": K.add((f["vol"], f["fecha"], f["b"]))
        elif modo == "fecha": K.add((f["vol"], f["fecha"]))
        elif modo == "fecha+-1":
            for k in (-1, 0, 1): K.add((f["vol"], str(d0 + dt.timedelta(days=k))))
    return K
AL = {"ALERTA_TERMICA"}; ALO = AL | {"ALERTA_TERMICA_OCR"}; TODO = ALO | {"FALSO_POSITIVO", "FALSO_POSITIVO_OCR"}; CUALQ = TODO | {"RUTINA"}
def pathd(r, modo):
    d = r.get("diag_n_dnti_ctx_path") or 0
    o = sum(r.get(k) or 0 for k in ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
    return (d > o) if modo == "dominante" else (d > 0 and o == 0) if modo == "solo" else d > 0
print("ventana | tbg< | pathD | n_far n_far_pc>5 | n_summit | conf ALERTA f+s | ALERTA+OCR f+s | ALERTA+OCR fecha | +FP fecha | fecha+-1 | control RUTINA-incl")
for w in (("2026-01-29", "2026-06-18"), ("2026-05-01", "2026-06-18"), ("2026-04-01", "2026-06-18")):
    for tb in (262, 270):
        for pm in ("dominante", "solo", "alguno"):
            far = []; su = []
            for v in VOLS:
                for r in D[v]:
                    f = r["datetime_utc"][:10]
                    if not (w[0] <= f <= w[1]): continue
                    pc = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
                    if pc <= 0 or r.get("t_bg_k") is None or r["t_bg_k"] >= tb or not pathd(r, pm): continue
                    (far if r.get("distance_class") == "far" else su if r.get("distance_class") == "summit" else []).append((v, f, bucket(r["sensor"]), pc))
            def c(tipos, modo):
                K = claves(tipos, modo)
                return sum(1 for v, f, b, _ in su if ((v, f, b) if modo == "fecha+sensor" else (v, f)) in K)
            n = len(su)
            print(w[0][5:], w[1][5:], "|", tb, "|", pm, "|", len(far), sum(1 for x in far if x[3] > 5), "|", n, "|",
                  *[f"{x} ({100*x/n:.1f}%)" if n else "SIN DATO" for x in (c(AL, "fecha+sensor"), c(ALO, "fecha+sensor"), c(ALO, "fecha"), c(TODO, "fecha"), c(ALO, "fecha+-1"), c(CUALQ, "fecha"))], sep="  ")
