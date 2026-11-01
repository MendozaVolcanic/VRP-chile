# M1 T9. Propagacion A113: para cada afirmacion que AUDIT_S158 / F2 rebaja o refuta, buscar TODAS las citas en los
# documentos que cada sesion hereda (CLAUDE.md, docs/MISSION.md, docs/MIROVA_DIVERGENCES.md, docs/SINTOMAS.md,
# docs/META_RULES_S80.md, docs/FICHA_SDA_VRP_CHILE.md, perfil yaml, docstrings de tests, preregistros D25/D1D2, memoria
# del agente) y decir si, a +-W lineas, hay una marca 'S158'. Pregunta 1: si una cita quedara sin marca, aparece en
# 'SIN_MARCA'. Pregunta 2: control positivo = el patron C1 debe encontrar CLAUDE.md glosario (que SI esta marcado) y
# tests/test_cluster_hotspots.py (que NO); si no encuentra el marcado, el buscador esta muerto.
# LIMITE: la ventana +-W puede dar falsos 'MARCADO' (una marca vecina de otra cosa): por eso se imprime la linea
# y W es chico (6). Es un PISO de cobertura, no un censo exhaustivo.
import re,os,glob,sys
W=6
MEM=r'C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory'
files=['CLAUDE.md','docs/MISSION.md','docs/MIROVA_DIVERGENCES.md','docs/SINTOMAS.md','docs/META_RULES_S80.md','docs/FICHA_SDA_VRP_CHILE.md',
 'pipeline/profiles/mirova_equivalent.yaml','pipeline/detection_context.py','pipeline/process_viirs_mod.py','pipeline/process_viirs.py','pipeline/process_modis.py','pipeline/vrp_regimes.py','pipeline/diurno.py',
 'experiments/_s157_prereg_d25/PREREGISTRO.md','experiments/_s157_prereg_d25/RESUMEN_SELLO.md','docs/PREREGISTRO_AB_D1_D2_S135.md','docs/DATA_SOURCES.md','docs/INDEX.md',
 'experiments/50_FACTOR_42_HALLAZGO.md','docs/HYPOTHESIS_LOG.md']
files+=sorted(glob.glob('tests/*.py'))
files+=[os.path.join(MEM,f) for f in ('MEMORY.md','project_s157_estado.md')]+sorted(glob.glob(os.path.join(MEM,'feedback_*.md')))+sorted(glob.glob(os.path.join(MEM,'reference_*.md')))
CL={
 'C01 MIROVA cuenta regiones/n_hotspots/factor 42':r"n_hotspots|factor 42|Cluster vs pixel|regiones espacialmente contiguas|cada cluster equivale",
 'C02 segundo pase condicionado = lo que manda el paper/MIROVA':r"condicionado como manda|pase condicionado|SECOND_PASS_CONDITIONED|solo adyacentes|sólo adyacentes|second.pass.{0,40}condicion",
 'C03 MIROVA no usa mascaras geograficas':r"no usa máscaras|NO usa máscaras|no hay máscaras geométricas|MIROVA no usa m[aá]scaras",
 'C04 VIIRS750 12 sigma/8 sigma (Di Bella) canonico':r"n=12 nocturno|12σ.{0,30}VIIRS|VIIRS_C2_OVERRIDE|viirs_c2_override",
 'C05 D8 kernel = Coppola 2024 L1129 literal':r"L1129",
 'C06 K1 diurno -0.6 para VIIRS':r"NTI_K1_DAY|nti_k1.{0,6}-0\.6|K1 ?= ?-0[.,]6",
 'C07 contraste 8 vecinos':r"8 vecinos|8-vec|ocho vecinos|eight neighbo|8-neighbo|8 neighbo",
 'C08 C1 scene 0.010 Table 2':r"Table 2|0\.010 scene|0,010 scene|C1 = 0\.003 summit / 0\.010",
 'C09 Test1 K1 = mascara de saturacion no reportable':r"MÁSCARA DE SATURACIÓN|test1_k1_saturation|TEST1_K1_RETIRE",
 'C10 recorte dL a cero (Wooster physics)':r"Wooster physics|vrp_negative_clip|clip delta_L|delta_L ?= ?np\.maximum|recorte a cero",
 'C11 piso -0.1 tambien en dETI':r"dETI.{0,40}-0\.1|unsuitable_filters|UNSUITABLE_FILTERS",
 'C12 A76 MIROVA limpia diurno por supervision manual / no gate':r"no gate autom|supervisión MANUAL|supervision manual",
 'C13 fondo vecinos = lo que hace MIROVA (D25)':r"lo que hace MIROVA|NEIGHBOR_MEAN|media de vecinos no alertados",
 'C14 Etna prueba produccion':r"es el que corri[oó] en producci",
 'C15 D17 cierra como mucho 23%':r"23 ?%|como mucho un 23",
 'C16 Cobertura completa con cero granulos':r"Cobertura: completa",
 'C17 recall_v750_dash libro 85,06':r"85[.,]06|85[.,]12",
 'C18 caja 5x5 km D18':r"5 ?[x×] ?5 km|caja de 5",
 'C19 n_hotspots_clustered paridad':r"n_hotspots_clustered",
 'C20 MIROVA no filtra nubes/ sin mascara':r"MIROVA no filtra nub|sin máscara de nube|no usa m[aá]scara de nube",
}
pat={k:re.compile(v,re.I) for k,v in CL.items()}
res={k:[] for k in CL}
for f in files:
    if not os.path.exists(f): continue
    try: L=open(f,encoding='utf-8',errors='replace').read().split('\n')
    except Exception as e: continue
    for i,ln in enumerate(L):
        for k,p in pat.items():
            if p.search(ln):
                lo,hi=max(0,i-W),min(len(L),i+W+1)
                marc=any('S158' in x for x in L[lo:hi])
                res[k].append((f.replace(chr(92),'/'),i+1,marc,ln.strip()[:110]))
for k in CL:
    h=res[k]; sm=[x for x in h if not x[2]]
    print(f'\n== {k}: {len(h)} citas, {len(sm)} sin marca S158 a +-{W} lineas')
    for f,i,m,t in h:
        if not m and ('tests/' in f or 'MEMORY' in f or 'memory' in f.lower() or f.endswith(('CLAUDE.md','MISSION.md','SINTOMAS.md','META_RULES_S80.md','mirova_equivalent.yaml','FICHA_SDA_VRP_CHILE.md')) or 'DIVERGENCES' in f or 'PREREG' in f.upper() or 'RESUMEN' in f):
            print(f'   SIN_MARCA {f}:{i}: {t}')
