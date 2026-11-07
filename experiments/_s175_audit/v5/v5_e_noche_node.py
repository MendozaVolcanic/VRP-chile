# -*- coding: utf-8 -*-
"""V5-E: reconcilia 194 (audit, port, cualquier pasada) contra 190 (misma pasada) usando el predicado del tablero (node, campo pub) en vez del port.
Pregunta 1: si la diferencia 194-190 fuera diferencia de PREDICADO y no de PASADA, el recall nocturno con node (cualquier pasada del mismo
(volcan, bucket, noche), pub=1) daria ~190, no 194.
Pregunta 2: control: el mismo calculo con el port del audit tiene que reproducir 194 (control_port del auditor: 382=382 noches dash).
Universo: noches de alerta de MIROVA con record nuestro (A['mir'] filtrado como el auditor), detector K/VIA, ventana 2026-09-03..2026-11-02.
Importa funciones del auditor (re-corrida en v5/rerun) solo para obtener las noches de MIROVA; el calculo es mio."""
import collections, os, pickle, sys
sys.dont_write_bytecode = True
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "rerun"))
import f5_medir as fm
B = fm.cargar()
A = fm.audit_ventana(B)
aw, frontera, via = fm.aw, A["frontera"], A["via_modis"]
pub_por_noche = collections.defaultdict(lambda: [0, 0])   # (vol,b,noche) -> [n_pasadas, n_pub]
for r in B["recs"]:
    k = (r["vol"], r["b"], r["noche"])
    pub_por_noche[k][0] += 1
    pub_por_noche[k][1] += r["pub"]
cnt = collections.defaultdict(collections.Counter)
for (vol, b, fecha), v in A["mir"].items():
    if vol not in aw.VOLS or aw.detector_de_noche(fecha, frontera, b, via) not in ("K", "VIA_MODIS"):
        continue
    if (vol, b, fecha) not in A["vistos"]:
        continue
    cnt[b]["noches"] += 1
    cnt[b]["port_cualquier_pasada(audit)"] += bool(A["ours"].get((vol, b, fecha), {}).get("dash"))
    cnt[b]["node_cualquier_pasada(pub)"] += pub_por_noche.get((vol, b, fecha), [0, 0])[1] > 0
    cnt[b]["noche_sin_record_en_banco"] += (vol, b, fecha) not in pub_por_noche
for b, c in sorted(cnt.items()):
    print(b, dict(c))
