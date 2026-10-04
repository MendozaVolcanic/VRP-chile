# S150. Determinismo del gemelo de B contra B (no contra J), Lascar, por sensor.
# Uso: python determinismo_lascar.py <TMP> experiments/_s149_prereg_invierno
#   <TMP> es la carpeta --tmp de evaluar_ventana.py despues de correr marzo_lascar, abril_lascar, junio y
#   junio_lascar; ademas <TMP>/abril_B con el Lascar.json de B del run 35639417826, extraido con
#   git archive origin/s146-ab/35639417826 experiments/_s146_ab_sin_test1/salidas/35639417826/_s146_ab_sin_test1/Lascar.json
#   Hoy evaluar_ventana.py con --control-gemelo hace lo mismo; este script queda como la medicion de S150.
import json, subprocess, sys, shutil, collections, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
S = Path(sys.argv[1]); AQ = Path(sys.argv[2])
R = "runs/experiments/_s146_ab_sin_test1/salidas"
casos = {
  "marzo":  (S/"marzo_lascar"/R/"35632736532/_s146_ab_sin_test1", S/"marzo_lascar"/R/"35632736532/_s149_ab_sin_test1_gemelo", "2026-03-01", "2026-03-31", "marzo_lascar"),
  "abril":  (S/"abril_B/experiments/_s146_ab_sin_test1/salidas/35639417826/_s146_ab_sin_test1", S/"abril_lascar"/R/"35648804271/_s149_ab_sin_test1_gemelo", "2026-04-01", "2026-04-30", "abril"),
  "junio":  (S/"junio"/R/"35675490175/_s146_ab_sin_test1", S/"junio_lascar"/R/"35679063864/_s149_ab_sin_test1_gemelo", "2026-06-01", "2026-06-30", "junio"),
}
for n, (b, g, d, h, cong) in casos.items():
    C = AQ/"_congelado"/cong; out = S/("det_%s.json" % n)
    subprocess.run([sys.executable, str(AQ/"armar_tabla.py"), "--control", str(b), "--brazo", str(g), "--cons", str(C/"registro_vrp_consolidado.csv"),
                    "--ocr", str(C/"registro_vrp_ocr.csv"), "--desde", d, "--hasta", h, "--out", str(out)], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    P = json.loads(out.read_text(encoding="utf-8"))["pasadas"]
    c = collections.defaultdict(lambda: [0, 0, 0])
    for k, v in P.items():
        s = k.split("|")[1]; c[s][0] += 1
        if len(v) == 2:
            c[s][1] += 1; c[s][2] += v["control"]["pub"] == v["brazo"]["pub"]
    print(n, {s: "pasadas %d, en ambos %d, misma decision %d" % tuple(x) for s, x in sorted(c.items())})
