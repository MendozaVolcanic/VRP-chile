import os, sys, collections
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
R = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s163-diurno-k-prereg-5c4f44"
sys.path[:0] = [R, R + r"\scripts", R + r"\experiments\_s163_diurno_k"]
import evaluar_diurno_k as ev, sustrato_k as sk, clase_mirova as cm
filas = sk.cargar_ref(sys.argv[1])
vent = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
pas = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN")
       if p.volcano in ev.coords() and p.sensor_bucket in ev.SENSORES_DIA and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in vent)]
al = [p for p in pas if p.estado == "alerta" and ev.es_dia_vol(p.volcano, p.instante) and p.sensor_bucket == "VIIRS375"]
print("V375 alertas diurnas", len(al), "volcan-dias", len({(p.volcano, p.instante.strftime('%Y-%m-%d')) for p in al}))
tab = [p for p in cm.resumir_pasadas(filas, canal="tabla", regla_minimas="SN")]
print("tabla: ultima pasada", max(p.instante for p in tab))
ocr = [p for p in cm.resumir_pasadas(filas, canal="union", regla_minimas="SN") if p.solo_ocr]
print("solo OCR: ultima pasada", max(p.instante for p in ocr))
# diurnas del OCR-only por estado, en las ventanas
c = collections.Counter((p.sensor_bucket, p.estado) for p in ocr if p.sensor_bucket in ev.SENSORES_DIA and ev.es_dia_vol(p.volcano, p.instante) and any(w[1] <= p.instante.strftime("%Y-%m-%d") <= w[2] for w in vent))
print("solo OCR diurnas en W2..W6 por estado:", dict(c))
