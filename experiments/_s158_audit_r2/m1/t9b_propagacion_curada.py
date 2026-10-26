# M1 T9b. Propagacion A113 curada. Para cada afirmacion que la primera ronda rebaja o refuta (F2 tabla 22, F4, F5,
# F6), lista los pasajes que la repiten y dice si hay marca "S158" dentro de [-8,+12] lineas, en dos versiones:
#   HEAD = lo que dejo la primera ronda (git show HEAD:archivo; linea base de AUDIT_S158 parrafo 3)
#   TRAB = arbol de trabajo hoy (una sesion hermana, a113, esta editando CLAUDE.md, MISSION.md y MIROVA_DIVERGENCES.md)
# Pregunta 1: si un pasaje quedara sin marca, sale "0/n marcadas". Pregunta 2: si el ancla no se encontrara (archivo
# movido o texto cambiado) sale ANCLA_NO_ENCONTRADA (SIN DATO), nunca "marcada". Control positivo: el ancla K0
# (glosario "Cluster vs pixel" de CLAUDE.md) debe salir marcada en HEAD (la ronda 1 la marco).
import re, subprocess, os, sys

def head(path):
    r = subprocess.run(['git', 'show', 'HEAD:' + path], capture_output=True)
    return r.stdout.decode('utf-8', 'replace').split('\n') if r.returncode == 0 else None

def work(path):
    return open(path, encoding='utf-8', errors='replace').read().split('\n') if os.path.exists(path) else None

MEM = r'C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory'
BIB = r'C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\BIBLIOGRAPHY_SYNTHESIS.md'
IT = [
 ('K0 control CLAUDE.md glosario Cluster vs pixel', 'CLAUDE.md', r'Cluster vs pixel'),
 ('1 n_hotspots=regiones: D1', 'docs/MIROVA_DIVERGENCES.md', r'MIROVA junta pixels contiguos'),
 ('1 n_hotspots: MISSION cluster aggregation', 'docs/MISSION.md', r'Cluster aggregation \(S27\)'),
 ('1 n_hotspots: test', 'tests/test_cluster_hotspots.py', r'MIROVA reporta n_hotspots'),
 ('1 factor 42 hallazgo', 'experiments/50_FACTOR_42_HALLAZGO.md', r'MIROVA reporta'),
 ('1 HYPOTHESIS_LOG factor 42', 'docs/HYPOTHESIS_LOG.md', r'factor 42'),
 ('2 D19 condicionado como manda Coppola', 'docs/MIROVA_DIVERGENCES.md', r'condicionado como manda Coppola'),
 ('2 yaml second_pass_conditioned', 'pipeline/profiles/mirova_equivalent.yaml', r'enable_second_pass_conditioned'),
 ('2 docstring detection_context conditioned', 'pipeline/detection_context.py', r'DOS condiciones'),
 ('2 preregistro D1/D2 S135', 'docs/PREREGISTRO_AB_D1_D2_S135.md', r'segundo pase condicionado'),
 ('2 test s135', 'tests/test_second_pass_conditioned_s135.py', r'segundo pase condicionado'),
 ('3 exclude_zones MISSION', 'docs/MISSION.md', r'exclude_zones. \(Salar'),
 ('3 exclude_zones yaml', 'pipeline/profiles/mirova_equivalent.yaml', r'MIROVA NO usa m.scaras'),
 ('3 A4 CLAUDE.md sin mascaras', 'CLAUDE.md', r'no hay m.scaras geom.tricas'),
 ('3 test exclude_zones', 'tests/test_enable_exclude_zones_flag.py', r'NO est. en papers|no est. en papers'),
 ('4 BIBLIOGRAPHY 12 sigma V750 (fuera de git)', BIB, r'n=12 nocturno'),
 ('5 D8 kernel L1129 literal', 'docs/MIROVA_DIVERGENCES.md', r'Coppola 2024 L1129 literal'),
 ('5 CLAUDE.md A12 kernel-bg L1129', 'CLAUDE.md', r'Fix kernel-bg \(Coppola 2024 L1129'),
 ('5 yaml kernel 3x3 L1129', 'pipeline/profiles/mirova_equivalent.yaml', r'S61 ADOPCI.N'),
 ('5 test kernel local', 'tests/test_local_kernel_background.py', r'L1129'),
 ('6 D27 K1 diurno -0,6', 'docs/MIROVA_DIVERGENCES.md', r'De d.a los Tests 2 y 3 usan K1 = -0,6'),
 ('6 test rama diurna K1', 'tests/test_rama_diurna_viirs_s151.py', r'-0\.6'),
 ('6 preregistro AB diurno K1', 'experiments/_s151_ab_diurno/PREREGISTRO.md', r'-0[.,]6'),
 ('7 CLAUDE.md kernel 8-vecinos D1 resuelto', 'CLAUDE.md', r'Kernel 8-vecinos dNTI contextual'),
 ('7 CLAUDE.md kernel 8-vec aritmetico', 'CLAUDE.md', r'kernel 8-vec aritm.tico'),
 ('7 yaml 8-vecinos', 'pipeline/profiles/mirova_equivalent.yaml', r'dNTI contextual 8-vecinos'),
 ('8 yaml C1 scene Table 2', 'pipeline/profiles/mirova_equivalent.yaml', r'dual-ROI thresholds \(Coppola 2016a Table 2\)'),
 ('8 DIVERGENCES scene=0.010 Table 2', 'docs/MIROVA_DIVERGENCES.md', r'scene=0\.010 \(Coppola 2016a Table 2\)'),
 ('9 yaml K1 noche VIIRS', 'pipeline/profiles/mirova_equivalent.yaml', r'nti_k1_night'),
 ('10 comentario Test1 K1 mascara saturacion', 'pipeline/detection_context.py', r'M.SCARA DE SATURACI.N'),
 ('10 test drift1 test1 k1', 'tests/test_drift1_test1_k1_saturation.py', r'retire'),
 ('11 test clip dL', 'tests/test_vrp_negative_clip.py', r'Wooster|clip'),
 ('11 yaml recorte a cero', 'pipeline/profiles/mirova_equivalent.yaml', r'El recorte a cero no cambia'),
 ('12 test unsuitable', 'tests/test_unsuitable_filters.py', r'unsuitable'),
 ('12 MISSION unsuitable', 'docs/MISSION.md', r'ENABLE_UNSUITABLE_FILTERS_267_273'),
 ('13 D18 caja igual para todos', 'docs/MIROVA_DIVERGENCES.md', r'CAJA de 5 km igual para todos'),
 ('13 test guard caja', 'tests/test_guard_caja_llega_al_segundo_pase_s149.py', r'caja'),
 ('14 A76 memoria supervision manual', '__MEM__reference_mirova_daytime_cloud_artifact.md', r'SUPERVISI.N MANUAL'),
 ('14 memoria feedback sin supervision', '__MEM__feedback_mirova_no_human_supervision.md', r'supervisi.n manual'),
 ('15 D25 RESUMEN_SELLO fondo vecinos', 'experiments/_s157_prereg_d25/RESUMEN_SELLO.md', r'lo que hace MIROVA'),
 ('15 D25 PREREGISTRO', 'experiments/_s157_prereg_d25/PREREGISTRO.md', r'MIROVA'),
 ('16 DISENO_D17 3.6 23 por ciento', 'docs/DISENO_D17_REMUESTREO_UTM.md', r'23 ?%'),
 ('17 oraculo README prueba produccion', 'experiments/_s158_oraculo_mirova/README.md', r'en producci.n'),
 ('18 run_pipeline Cobertura completa', 'scripts/run_pipeline.py', r'Cobertura: completa'),
 ('19 MISSION codigo operacional', 'docs/MISSION.md', r'c.digo operacional'),
 ('19 CLAUDE.md codigo operacional V750', 'CLAUDE.md', r'public. su c.digo operacional'),
 ('19 DIVERGENCES D34 codigo operacional', 'docs/MIROVA_DIVERGENCES.md', r'D34: El c.digo operacional'),
 ('20 MEMORY.md codigo operacional OSF', '__MEM__MEMORY.md', r'operacional de MIROVA V750'),
 ('20 memoria reference_codigo_mirova_osf', '__MEM__reference_codigo_mirova_osf.md', r'operacional'),
 ('21 SINTOMAS codigo operacional', 'docs/SINTOMAS.md', r'c.digo operacional'),
]

def marks(L, rx, lo=8, hi=12):
    out = []
    for i, l in enumerate(L):
        if re.search(rx, l):
            a, b = max(0, i - lo), min(len(L), i + hi + 1)
            out.append((i + 1, any('S158' in x for x in L[a:b])))
    return out

print('%-52s %-30s %-30s' % ('item', 'HEAD', 'TRAB(hoy)'))
for nm, path, rx in IT:
    if path.startswith('__MEM__'):
        path = os.path.join(MEM, path[7:]); H = W = work(path)
    elif path == BIB:
        H = W = work(path)
    else:
        H = head(path); W = work(path)

    def fmt(L):
        if L is None:
            return 'ARCHIVO_NO_EXISTE'
        m = marks(L, rx)
        if not m:
            return 'ANCLA_NO_ENCONTRADA'
        s = sum(1 for _, x in m if x)
        return '%d/%d marcadas (l.%d)' % (s, len(m), m[0][0])
    print('%-52s %-30s %-30s' % (nm, fmt(H), fmt(W)))
