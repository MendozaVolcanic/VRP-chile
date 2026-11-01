"""Copias mutadas del .m de detección (control positivo de O1). El original nunca se edita: se lee y se escribe una
copia por mutación en mut_<nombre>/. Cada reemplazo se exige único (assert count == 1) para que una mutación que no
aplica falle en vez de dejar una copia idéntica."""
from pathlib import Path
AQUI = Path(__file__).resolve().parent
ORIG = AQUI.parents[1] / "_s158_d17_diseno" / "osf_codigo_mirova" / "MIROVA_VIIRS750_hotspot_detection.m"
src = ORIG.read_text(encoding="utf-8")
MUT = {
    "min2": [("minimumNTIcontrastROI2 = 0.003;", "minimumNTIcontrastROI2 = 0.03;")],
    "k1": [("absoluteNTIthreshold = -0.7;", "absoluteNTIthreshold = -0.8;")],
    "sigma": [("sigmaMultiplierROI1 = 10;", "sigmaMultiplierROI1 = 5;"),
              ("sigmaMultiplierROI2 = 5;\n\n        minimumNTIcontrastROI1 = 0.02;\n        minimumNTIcontrastROI2 = 0.003;",
               "sigmaMultiplierROI2 = 10;\n\n        minimumNTIcontrastROI1 = 0.02;\n        minimumNTIcontrastROI2 = 0.003;")],
    "sinp2": [("    %% 9. FINAL ALERT SYNTHESIS",
               "    alertsBOX0_pass2 = []; alertsROI1_pass2 = []; alertsROI2_pass2 = [];\n    %% 9. FINAL ALERT SYNTHESIS")],
}
for nombre, reps in MUT.items():
    s = src
    for a, b in reps:
        assert s.count(a) == 1, (nombre, a)
        s = s.replace(a, b)
    d = AQUI / f"mut_{nombre}"; d.mkdir(exist_ok=True)
    (d / ORIG.name).write_text(s, encoding="utf-8")
    print(nombre, "ok")
