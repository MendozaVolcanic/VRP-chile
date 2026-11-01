"""V2 / F2-H2, medición 2: qué hace el segundo pase en el código de MIROVA (oráculo en Python).

Tres preguntas, cada una con su control:
 (A) Etna 2023-05-19 (matriz de ejemplo publicada por MIROVA): ¿los píxeles del segundo pase son
     vecinos-8 de lo ya alertado (pase 1 + Test absoluto)? Si la condición (b) «sólo adyacentes»
     estuviera en el código, todos lo serían; si alguno no lo es, el código no restringe.
     (Si todos lo son, NO prueba que el código restrinja: Etna es un foco compacto. Por eso (C).)
 (B) Escena con el primer pase vacío: ¿el segundo pase devuelve vacío? (Se espera que sí por
     construcción: mismas entradas, misma función.) Control positivo del instrumento: la misma
     escena con un foco inyectado debe dar alertas > 0.
 (C) Escena sintética con un foco fuerte compacto y un píxel débil AISLADO a ~15 píxeles: ¿el
     código de MIROVA alerta el píxel aislado en el segundo pase? Si sí, la condición (b)
     (vecindad-8) lo perdería y se aparta del código.
Pregunta 2 (instrumento muerto): se imprime n de alertas por pase; si el oráculo no corriera,
(B-control) daría 0 y se ve.
"""
import sys, io
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from scipy.ndimage import binary_dilation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments/_s158_oraculo_mirova"))
import mirova_v750 as M

def idx2mask(idx, shape):
    m = np.zeros(int(np.prod(shape)), bool); m[np.asarray(idx, int)] = True
    return m.reshape(shape, order="F")

def corre(m13, m15, box, etiqueta):
    alert, d = M.hotspot_detection(m13, m15, box, 0, 90.0, devolver_diag=True)
    n1 = sum(d.get("n_pase1", [0])); n2 = sum(d.get("n_pase2", [0])); na = d.get("n_absolutas", 0)
    k1 = n1; ka = na
    p1 = alert[:k1]; ab = alert[k1:k1 + ka]; p2 = alert[k1 + ka:]
    prev = idx2mask(np.concatenate([p1, ab]), m13.shape)
    vec = binary_dilation(prev, structure=np.ones((3, 3), bool)) & ~prev
    p2m = idx2mask(p2, m13.shape)
    no_ady = int(np.count_nonzero(p2m & ~vec))
    print(f"[{etiqueta}] absolutas={na} pase1={d.get('n_pase1')} pase2={d.get('n_pase2')} "
          f"pase2_no_adyacentes={no_ady} de {int(p2m.sum())}")
    return d, p2m & ~vec

S = loadmat(ROOT / "experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
m13, m15, box = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float), S["BOX"].astype(float)
print("(A) Etna")
corre(m13, m15, box, "Etna")

# (B) Escena sin foco: reemplazar M13 por el M13 que predice el TIR (isotermo) más ruido chico.
rng = np.random.default_rng(0)
bt15 = M.radiance_to_temperature(m15, M.WAVELENGTH_M15)
m13_iso = M.temperature_to_radiance(bt15, M.WAVELENGTH_M13) * (1 + 0.01 * rng.standard_normal(m15.shape))
print("\n(B) escena isoterma con ruido (sin foco)")
corre(m13_iso, m15, box, "sin foco")
m13_ctrl = m13_iso.copy(); m13_ctrl[33, 33] *= 3.0
corre(m13_ctrl, m15, box, "control +: foco inyectado en (33,33)")

# (C) foco fuerte compacto en el centro + píxel débil aislado lejos, barriendo su intensidad.
print("\n(C) foco fuerte 3x3 en el centro + píxel débil aislado en (33,50), barrido de intensidad")
for f in (1.10, 1.15, 1.20, 1.25, 1.30, 1.40, 1.60):
    m = m13_iso.copy()
    m[32:35, 32:35] *= 8.0
    m[33, 50] *= f
    d, na = corre(m, m15, box, f"debil x{f:.2f}")
    if na.any():
        print("   píxeles del pase 2 NO adyacentes (fila, col):", list(zip(*np.nonzero(na))))
print("BOX en (33,50):", box[33, 50], " BOX en (33,33):", box[33, 33])

# (C2) Búsqueda: escena ruidosa (sigma gobierna sobre el mínimo), foco contextual (no absoluto) de
# 3x3 en el centro y píxel débil aislado en BOX0. Se buscan casos en que el pase 2 alerta un píxel
# NO adyacente a lo ya alertado. Se informa el primero de cada combinación y el total.
print("\n(C2) búsqueda en escena ruidosa")
hallados = 0; probados = 0
for ruido in (0.03, 0.05, 0.08):
    rng = np.random.default_rng(1)
    base = M.temperature_to_radiance(bt15, M.WAVELENGTH_M13) * (1 + ruido * rng.standard_normal(m15.shape))
    for foco in (1.5, 2.0, 3.0):
        for f in np.linspace(1.05, 2.0, 39):
            m = base.copy(); m[32:35, 32:35] *= foco; m[33, 50] *= f
            alert, d = M.hotspot_detection(m, m15, box, 0, 90.0, devolver_diag=True)
            probados += 1
            k1 = sum(d["n_pase1"]); ka = d["n_absolutas"]
            prev = idx2mask(alert[:k1 + ka], m.shape)
            vec = binary_dilation(prev, structure=np.ones((3, 3), bool))
            p2 = idx2mask(alert[k1 + ka:], m.shape)
            na = p2 & ~vec
            if na.any():
                hallados += 1
                if hallados <= 5:
                    print(f"  ruido={ruido} foco=x{foco} debil=x{f:.3f}: abs={ka} pase1={d['n_pase1']} "
                          f"pase2={d['n_pase2']} no_ady={list(zip(*np.nonzero(na)))} "
                          f"thrN1 p1={d['pase1']['thr_dnti_box0_roi1']:.4f} p2={d['pase2']['thr_dnti_box0_roi1']:.4f}")
print(f"(C2) casos con alertas del pase 2 no adyacentes: {hallados} de {probados} escenas probadas")
