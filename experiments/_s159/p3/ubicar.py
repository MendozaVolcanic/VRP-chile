# Ubica (NO cita) pasajes por palabra clave en la capa de texto de cada PDF.
# La capa de texto corrompe simbolos (A95): sólo sirve para elegir qué página renderizar.
import sys, re, fitz, os
DOC = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion"
PDFS = {
 "wright2002": "wright2002_rse_automated_volcanic_eruption_detection_10.1016-S0034-4257(02)00030-5.pdf",
 "wooster2003": "1-s2.0-S0034425703000701-main.pdf",
 "coppola2012": "coppola2012_jvgr_stromboli_10.1016-j.jvolgeores.2011.12.001.pdf",
 "coppola2014": "coppola2014_ijrs_strombolian_10.1080-01431161.2014.903354.pdf",
 "coppola2019": "Thermal_Remote_Sensing_for_Global_Volcano_Monitori.pdf",
 "coppola2023": "feart-11-1240107.pdf",
 "aveni2024": "Aveni_2024_TIRVolcH_RSE.pdf",
}
KW = sys.argv[2]
key = sys.argv[1]
d = fitz.open(os.path.join(DOC, PDFS[key]))
for i, p in enumerate(d):
    t = p.get_text().replace("\n", " ")
    for m in re.finditer(KW, t, flags=re.I):
        print(f"[{key} idx{i}] ..." + t[max(0, m.start()-220):m.end()+260] + "...\n")
