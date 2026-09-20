# -*- coding: utf-8 -*-
"""Frente G (S146): arma inventario.json y la tabla Markdown del inventario de caminos.
Los VALORES EFECTIVOS salen de perfil_efectivo.json (volcado de pipeline.profile) y las FECHAS de
fechas_mecanismos.json / declarado_vs_leido.json (git log). Ninguno se transcribe a mano.
Las filas (que mecanismo, donde, estado, origen) son la lectura del auditor y llevan su evidencia.
Solo lectura sobre el repo; escribe inventario.json y tabla_inventario.md en esta carpeta."""
import json, os
here = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(here, "perfil_efectivo.json"), encoding="utf-8"))
F = json.load(open(os.path.join(here, "fechas_mecanismos.json"), encoding="utf-8"))
DV = json.load(open(os.path.join(here, "declarado_vs_leido.json"), encoding="utf-8"))

PAPER, DECL, NODECL, NOSE = "ESTA EN EL PAPER (segun doc)", "NUESTRO Y DECLARADO", "NUESTRO Y NO DECLARADO", "NO SE SABE"
R = []
def fila(id, etapa, nombre, donde, attrs, sens, entro, justif, estado, evid, origen, ref):
    val = "; ".join(f"{a}={json.dumps(P[a], ensure_ascii=False)}" for a in attrs) if attrs else ""
    fechas = []
    for a in attrs[:2]:
        f = F.get(a, {}); d = DV.get(a, {})
        if f.get("primer_commit_profile_py"): fechas.append(f"{a}: entra {f['primer_commit_profile_py'][:18]}")
        if d.get("ultimo_commit_linea_yaml"): fechas.append(f"ultimo cambio YAML {d['ultimo_commit_linea_yaml'][:18]}")
        elif d.get("origen_del_valor", "").startswith("DEFAULT"): fechas.append("valor por DEFAULT de profile.py (no escrito en el YAML)")
    R.append({"id": id, "etapa": etapa, "mecanismo": nombre, "donde": donde, "valor_efectivo": val, "sensores": sens,
              "entro": entro, "fechas_git": fechas, "justificacion_de_entrada": justif, "estado_hoy": estado,
              "evidencia_estado": evid, "origen": origen, "referencia_origen": ref})

T = "los 3"
# ---------------- E0 adquisicion
fila("G-01","0 adquisicion","Filtro nocturno en tres capas (pre-descarga, por granulo, y red de seguridad al guardar); elevacion solar < 0",
     "pipeline/fetch.py:731-758; scripts/run_pipeline.py:116-118,180-192; pipeline/store.py:171-182,584-592",["ENABLE_DAYTIME_MODIS","NTI_K1_DAY","N_SIGMA_MIR_DAY","DNTI_CONTEXTUAL_C1_DAY"],T,
     "S1-S12 (fetch); S90 PR #257 (flag diurno MODIS)","decision de mision (MIR solo de noche)","VIVO",
     "los tres filtros usan el mismo umbral 0 grados; no hay records diurnos","%s" % DECL,"D27 (la Tabla 1 diurna esta escrita y nunca corre)")
fila("G-02","0 adquisicion","Standard primero, LANCE NRT de respaldo; al guardar, un Standard reemplaza al NRT ya publicado",
     "pipeline/fetch.py:167-225,468-530; pipeline/store.py:604-620",[],T,"S12","operacional (latencia)","VIVO",
     "product_version=nrt en 125/954 V375, 125/949 V750, 128/457 MODIS (huellas_en_records.json). Lo publicado puede cambiar dias despues",NODECL,"sin D; CLAUDE.md lo trata como constraint tecnico")
fila("G-03","0 adquisicion","Cortacircuitos por host (descarga y busqueda CMR): una pasada puede no procesarse",
     "pipeline/fetch.py:372-436,548-730",[],T,"S102 #364; S116","parche de incidente (A64)","VIVO (infra)",
     "no deja huella en el record: la pasada simplemente falta (A108). SIN DATO sobre cuantas faltan en el regimen",NODECL,"A64; sin D")
fila("G-04","0 adquisicion","Interruptores de sensor","scripts/run_pipeline.py:213-218",["SENSOR_MODIS","SENSOR_VIIRS_375","SENSOR_VIIRS_750"],T,"S9 (6dfcfe7f2)","configuracion","VIVO (los tres encendidos)","","no aplica","")
# ---------------- E1 lectura
fila("G-05","1 lectura","VIIRS I-band: pixeles saturados a NaN (bit 2 de quality_flags) y BT pegada al techo de la LUT (I04 361,77 K; I05 423,33 K) a NaN",
     "pipeline/process_viirs.py:364-401 (literales SAT_BIT_MASK, BT_LUT_MAX)",[],"VIIRS375","S73 F2.8","parche de un problema (outliers de vrp_tir de miles de MW)","VIVO",
     "sin huella en el record: el pixel desaparece. En un foco fuerte el pixel mas caliente (I04 satura ~367 K) queda fuera del NTI, de la mascara y de la magnitud. SIN DATO de frecuencia",NODECL,
     "D24 declara lo mismo SOLO para MODIS; para VIIRS nadie lo tiene como divergencia")
fila("G-06","1 lectura","VIIRS M-band: mismo guard (M13 634 K; M15 343 K)","pipeline/process_viirs_mod.py:181-294",[],"VIIRS750","S73 F2.8; S132","idem","VIVO","idem G-05",NODECL,"idem G-05")
fila("G-07","1 lectura","MODIS: SI > 32767 a NaN (incluye 65533 saturado) y guard secundario BT > 500 K a NaN",
     "pipeline/process_modis.py:240-246,329,552-557",["ENABLE_BT_SAT_SECONDARY_GUARD","BT_SAT_MIR_K_MODIS"],"MODIS","S73 F2.8 (fcd3ba345)","parche (PP 695.431 MW)","VIVO","sin huella por record",DECL,"D24")
fila("G-08","1 lectura","MODIS: banda 21 primaria, 22 de respaldo; el VRP convierte BT a radiancia siempre con lambda de la banda 21",
     "pipeline/process_modis.py:544-550,563,1027-1031",["ENABLE_MODIS_B22_PRIMARY"],"MODIS","historico; flag S132 #582","historico del repo","VIVO (banda 21)","",DECL,"D21")
fila("G-09","1 lectura","MODIS: NTI con banda 31 (11 um) y no 32","pipeline/process_modis.py:559-565",[],"MODIS","historico","historico","VIVO","",DECL,"D20")
fila("G-10","1 lectura","Area de pixel fija al nadir (sin sec3); sin remuestreo a grilla UTM; area geolocalizada apagada",
     "pipeline/process_viirs.py:735-751; process_modis.py:504-512; process_viirs_mod.py:479-492; scan_geometry.py",
     ["ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS","ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS","ENABLE_GEOLOCATED_PIXEL_AREA","ENABLE_UTM_REGRID"],T,
     "S102 #354 (MODIS), S103 #368 (VIIRS)","medicion propia (calibracion S14 contra OSF) + A/B","VIVO","",DECL,"D17 (remuestreo abierto), A66/A67 con la salvedad S138")
fila("G-11","1 lectura","Mascara de nube por BT TIR","pipeline/process_viirs.py:823-831; process_modis.py:570,780; V750 no tiene ninguna",["CLOUD_MASK_BT_K"],"MODIS, VIIRS375","S1; apagada S29 en YAML, efectiva en V375 desde #535","historico","APAGADA (umbral 0 K)",
     "n_cloud_masked>0 en 0 records de los tres sensores",DECL,"D14 cerrada")
# ---------------- E2 geometria
fila("G-12","2 geometria","ROI = caja de +-radius_km (25 km Tier A, 5 km los otros 34) centrada en lat/lon del volcan, no en el centro de grilla de MIROVA",
     "pipeline/process_viirs.py:779; process_modis.py:534; process_viirs_mod.py:515; volcanoes.yaml radius_km",[],T,"S14 (5478bce66), S15 Tema E","replica de la grilla 51x51 de MIROVA","VIVO","",DECL,"D17 (get_grid_center nunca se cableo)")
fila("G-13","2 geometria","Fondo regional: anillo circular 5 a 25 km, mediana y desvio; minimo 10 pixeles (literal). Con menos de 10, MODIS devuelve None (no hay record) y VIIRS queda sin deteccion",
     "process_viirs.py:780,945-956; process_modis.py:535,571-580; detection_context.py:1042-1085",["BG_INNER_KM","BG_OUTER_KM"],T,"S9","historico","VIVO","t_bg_k presente en 949/954 V375",DECL,"D25 (fondo), D8. El minimo de 10 y el 'sin record' de MODIS no estan declarados")
fila("G-14","2 geometria","Ancla de deteccion = crater (vent_lat/lon) y no mirova_center; mirova_center queda solo como dato",
     "pipeline/geo_utils.py:get_detection_anchor; scripts/run_pipeline.py:234,277,324; volcanoes.yaml (11 con mirova_center, 11 con vent)",[],T,"S98; mirova_center S15/S80 #220","parche de regresion (A63)","VIVO","",DECL,"seccion S98 del catalogo, D17")
fila("G-15","2 geometria","ROI1 = circulo de radio inner_radius_km por volcan (3: Lastarria, PP; 4: Copahue; 5: seis volcanes; 7: Tupungatito; 20: PCC); el paper usa caja 5x5 km",
     "detection_context.py:299-325; volcanoes.yaml inner_radius_km",["ENABLE_ROI1_BOX_PAPER","ROI1_BOX_HALF_KM"],T,"S14 (5478bce66); PCC=20 revertido S62 #85","valores de los KML de MIROVA","VIVO (circulo)","",DECL,"D18")
# ---------------- E3 deteccion
fila("G-16","3 deteccion","Camino A, test de temperatura de brillo N sigma 5/10 (y piso 5 K, tope de sigma 999 K, umbral local p95 en MODIS y V750)",
     "process_viirs.py:984-998; process_modis.py:583-661; process_viirs_mod.py:586-640",
     ["ENABLE_DUAL_ROI_BT","ENABLE_BT_PATH_HOT","N_SIGMA_MIR_SUMMIT","N_SIGMA_MIR_SCENE","ANOMALY_THRESHOLD_K","MAX_SIGMA_COMPONENT_K","N_SIGMA","N_SIGMA_MIR","P95_VENT_EXCLUSION_MODIS_KM","P95_VENT_EXCLUSION_VIIRS750_KM"],T,
     "S26 (d90f89b31); apagado S40 (1b0c3bdb5)","lectura de Tabla 1","ANULADO por otro flag (la mascara se construye y se pone en cero)",
     "diag_n_bt_path>0 en 0 records de los tres sensores. OJO: su contador sigue decidiendo cosas, ver G-19",DECL,"AUDIT_S146 V-08; FASE1 seccion 0")
fila("G-17","3 deteccion","Camino B, NTI > K1 con compuerta bt > t_bg + 3 K: se calcula y se cuenta, no entra a la mascara",
     "process_viirs.py:1002-1011,1299; process_modis.py:662-668; process_viirs_mod.py:646-654",["NTI_K1_NIGHT","NTI_BT_SANITY_K"],T,"S9","Wright 2002 / Coppola (K1)","DIAGNOSTICO QUE DECIDE (ver G-19)",
     "diag_n_nti_path>0 en 5/954 V375 y 0 en los otros",DECL,"D23")
fila("G-18","3 deteccion","Camino D legacy, dNTI contextual dual con compuerta de 3 K y filtros de no aptos: se calcula y se cuenta, no entra a la mascara",
     "process_viirs.py:1055-1083; process_modis.py:683-712; process_viirs_mod.py:690-715; detection_context.py:208-400",
     ["ENABLE_DNTI_CONTEXTUAL_PATH","ENABLE_DNTI_DUAL_ROI","DNTI_CONTEXTUAL_C1_SUMMIT","DNTI_CONTEXTUAL_C1_SCENE","DNTI_CONTEXTUAL_C1"],T,"S15 P3.2/P3.1","Coppola 2016a (dNTI)","DIAGNOSTICO QUE DECIDE (ver G-19, G-31, G-37)",
     "diag_n_dnti_ctx_path>0 en 507/954 V375, 386/949 V750, 455/457 MODIS",NODECL,"el catalogo lo trata como diagnostico inerte (FASE1 seccion 0); su papel de arbitro no esta declarado")
fila("G-19","3 deteccion","Los contadores 'diagnosticos' deciden la FUENTE publicada: only_test1_source exige n_bt=n_nti=n_dnti_ctx=n_eti=0, aunque la mascara real (Tests 2 y 3) tenga pixeles",
     "process_viirs.py:1747-1753; process_modis.py:1275-1290; process_viirs_mod.py:1164-1178",[],T,"S44","parche (Tupungatito FN)","VIVO",
     "132 pasadas V375 y 16 V750 con Test 1 disparado, mascara contextual NO vacia y los contadores legacy en cero: el Test 1 gana por 'fuente unica' sin serlo (huellas_en_records.json)",NODECL,"0 menciones de only_test1 en el catalogo y en MISSION")
fila("G-20","3 deteccion","Tests 2 y 3, primer pase: conectiva min(C1, mu + C2 sigma), C1 0,003/0,010, C2 5/10, ETI por regresion cuadratica, dual ROI",
     "process_viirs.py:1242-1300; process_modis.py:842-890; process_viirs_mod.py:825-878; detection_context.py:413-563",
     ["ENABLE_FIRST_PASS_TESTS_2_AND_3","ENABLE_DUAL_ROI_FIRST_PASS","C2_DNTI_SUMMIT_NIGHT","C2_DNTI_SCENE_NIGHT","C2_DETI_SUMMIT_NIGHT","C2_DETI_SCENE_NIGHT","ENABLE_TESTS_23_PROSE_BRANCH","C1_SUMMIT_OVERRIDE","C2_SUMMIT_OVERRIDE","VIIRS_C2_OVERRIDE_NIGHT"],T,
     "S46 #4x (958a7a189), adoptado 3d25ea16e","paper","VIVO: ES la mascara","diag_n_first_pass_pixels>0 en 346 V375, 59 V750, 455 MODIS",PAPER,
     "CLAUDE.md reglas cientificas: Coppola 2016a Tabla 1 y p. 7; conectiva contradictoria segun S136. C2 sale del default de profile.py, no del YAML")
fila("G-21","3 deteccion","Compuerta de temperatura bt > t_bg + 3 K dentro del primer pase (el segundo pase no la tiene)",
     "detection_context.py:546; process_viirs.py:1297",["NTI_BT_SANITY_K","ENABLE_TESTS_23_NO_BT_GATE_VIIRS375"],"los 3 (flag para quitarla solo en V375)","S9; flag S142","historico","VIVO","",DECL,"D22")
fila("G-22","3 deteccion","Filtros de pixeles no aptos para mu y sigma (borde, dNTI/dETI < -0,1)",
     "detection_context.py:59-160; process_viirs.py:1272-1273",["ENABLE_UNSUITABLE_FILTERS_267_273"],T,"S72 (d58f7a46f)","paper","VIVO (por DEFAULT de profile.py; la clave no esta en el YAML)","",PAPER,
     "detection_context.py:42-60 cita 'Coppola 2016a parrafos 267-273' (lineas del .txt, sin pagina): localizador debil")
fila("G-23","3 deteccion","Segundo pase (recaptura de adyacentes), dual ROI, sin condicionar al conjunto activo",
     "process_viirs.py:1306-1357; detection_context.py:822-985",["ENABLE_SECOND_PASS_ADJACENT","ENABLE_DUAL_ROI_SECOND_PASS","ENABLE_SECOND_PASS_CONDITIONED"],T,"S37/S46 (3d25ea16e)","paper","VIVO",
     "diag_n_second_pass_recapture>0 en 433 V375, 161 V750, 452 MODIS: recaptura en MAS pasadas que el primer pase en V375 y V750",DECL,"D19 (corre sin conjunto activo), D26")
fila("G-24","3 deteccion","Cercas intra-radio S84/S85 y gate atmosferico / co-validacion / filtros finales por pixel",
     "process_modis.py:712,944; process_viirs.py:1347,1364,1383,1818",["ENABLE_PATH_D_INTRA_RADIO_GATE","ENABLE_SECOND_PASS_INTRA_RADIO_GATE","PATH_D_ATM_GATE_TBG_MIN_K","PATH_D_REQUIRES_COVALIDATION","ENABLE_FINAL_PIXEL_FILTER","ENABLE_TEST1_PIXEL_FILTER"],T,"S71, S83, S85, S32/S33","parches","APAGADOS","",DECL,"A85, D9, S33")
fila("G-25","3 deteccion","Zonas excluidas (lagos, salar) con lista blanca de lagos crater",
     "pipeline/exclusion_zones.py; process_viirs.py:1393-1398; volcanoes.yaml: Villarrica(2), Lascar(1), Copahue(1), Llaima(1), Tupungatito(1 + lista blanca)",["ENABLE_EXCLUDE_ZONES"],T,"S16 (6f879898f), S26; apagado S29","parche","ANULADO por flag (las zonas siguen escritas en 5 volcanes)","n_excluded_water>0 en 0 records",DECL,"MISSION anti-patrones")
fila("G-26","3 deteccion","Test 1 integrado en el ROI: suma de excesos positivos de radiancia MIR en el disco de 3 km contra la mediana del anillo 1 a 3 km; dispara si suma > 3 sigma raiz(N) Y suma > 2 % de L_bg por N",
     "pipeline/test1_integrated.py:317-470; process_viirs.py:1099-1150; process_modis.py:737-760; process_viirs_mod.py:731-760",
     ["ENABLE_TEST1_PATH","TEST1_K_SIGMA","TEST1_MIR_RELATIVE","TEST1_ROI_KM","TEST1_INNER_RING_KM"],T,"S25 (dc32ba0f5), adoptado S27/S29","medicion propia (6/6 Villarrica) con cita bibliografica falsa","VIVO: sostiene 57,8 % de los negativos publicados de V375 (FASE1)",
     "triggered_test1 en 800/954 V375, 200/949 V750, 16/457 MODIS. Los cuatro umbrales salen del DEFAULT de profile.py: no estan escritos en el YAML operacional",DECL,"D30 (hoy)")
fila("G-27","3 deteccion","El criterio 'absoluto' del Test 1 no es un 3 sigma: la suma de excesos recortados a cero tiene media positiva bajo ruido puro (~0,4 sigma N) y supera 3 sigma raiz(N) siempre que N > ~57. Lo unico que frena es el piso relativo de 2 %, que pasa con ~1 K de dispersion espacial en el disco",
     "pipeline/test1_integrated.py:419-437",[],"los 3; decisivo en VIIRS375 (N~208)","S25","no se midio el nulo al adoptar","VIVO",
     "nulo_test1_ruido_puro.json: con ruido gaussiano puro el criterio absoluto pasa 100 % en V375, ~40 % en V750, ~16 % en MODIS; dispara 84 % con 1 K y 100 % con 1,5 K en V375. k observado real: mediana 4,86 con 70 pixeles (k_observado_vs_nulo.json) contra 5,75 y 104 del nulo",NODECL,
     "D30 declara que el detector es propio; no declara que su estadistico dispara sin senal")
fila("G-28","3 deteccion","Variantes del Test 1 (integral de NTI, co-validacion NTI, fondo local NTI)","process_viirs.py:1101-1137 (solo V375)",["ENABLE_TEST1_NTI_INTEGRAL","ENABLE_TEST1_NTI_COVALIDATION","ENABLE_TEST1_LOCAL_BG_NTI"],"VIIRS375","S104/S105","A/B","APAGADAS","",DECL,"A69 (nota S125)")
fila("G-29","3 deteccion","Camino C NTI relativo, camino ETI de escena, vent-path","process_viirs.py:1020,1158,1654; process_modis.py:1223",["ENABLE_NTI_RELATIVE_PATH","ENABLE_ETI_QUADRATIC_SCENE","ENABLE_VENT_PATH","ENABLE_VENT_PATH_MODIS","ENABLE_ERUPTION_PATH"],T,"S10-S12, S37","historicos","APAGADOS (ENABLE_ERUPTION_PATH=True se importa y no se lee en ninguna condicion)",
     "n_nti_rel_path, diag_n_eti_path, vrp_vent_mw > 0 en 0 records",DECL,"MISSION")
# ---------------- E4 ensamblado
fila("G-30","4 ensamblado","Cumulos 8-conexos; gana el mas cercano al crater dentro del inner (vent_anchored), ignorando cumulos con VRP = 0",
     "pipeline/clustering.py:75-190",["ENABLE_VENT_ANCHORED_CLUSTERING"],T,"S38 (8a51df89d), S43","parche D8","VIVO","",DECL,"seccion D8' del catalogo; A85")
fila("G-31","4 ensamblado","Prioridad de fuente del Test 1: (1) Test 1 en cumbre y pixel suelto mas caliente lejos; (2) 'fuente unica' (G-19); (3) cumulo rival < 0,01 MW. Si gana, la magnitud y los pixeles publicados se rehacen SOLO con pixeles del Test 1",
     "pipeline/test1_integrated.py:156-182; process_viirs.py:1735-1767,1912-2030",["ENABLE_TEST1_PRIORITY_WEAK_CLUSTER","TEST1_WEAK_CLUSTER_EPS_MW"],"los 3 (rama 3 solo V375)","S26/S30 Regla D, S44, S111 (ea71c62c2)","parches","VIVO",
     "final_hotspot_source=test1_roi en 348/954 V375 y 138/949 V750",DECL,"MISSION tabla de anti-patrones (Regla D Test 1 'sigue activa'); D30. La rama 2 no esta declarada (G-19)")
fila("G-32","4 ensamblado","Ancla honesta: posicion = cumulo contextual, o el CRATER a 0,0 km cuando gana el Test 1 (modo vent)",
     "pipeline/anchor.py:67-96; process_viirs.py:2063-2098",["ENABLE_HONEST_ANCHOR","ENABLE_HONEST_ANCHOR_VIIRS750","ENABLE_HONEST_ANCHOR_MODIS","ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE","HONEST_ANCHOR_TEST1_MODE"],"VIIRS375 y VIIRS750 (MODIS apagado)","S106 (542fce8d1), S108","A/B","VIVO en VIIRS",
     "un Test 1 disparado queda SIEMPRE summit a 0,0 km: la cerca por distancia del dashboard no lo puede frenar",DECL,"D11-bis, D19")
fila("G-33","4 ensamblado","MODIS: cascada legacy (pixel suelto mas caliente decide distance_class) + rescate de cumulo en store (cluster_rescue) con geocerca = radius_km (25 km)",
     "process_modis.py:1275-1320; pipeline/store.py:307,336-394",["ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"],"MODIS (el rescate no pisa fuentes del ancla honesta)","F47 S77 (71adc9831)","parche (F47 H4)","VIVO",
     "distance_class=far en 399/457 MODIS; cluster_rescue en 4, las 4 publicadas",NODECL,"D12 y D13 hablan del efecto; el rescate F47 no tiene D propia (1 mencion incidental)")
fila("G-34","4 ensamblado","Guard de coherencia A46: summit pasa a far si el cumulo con energia esta fuera del inner","pipeline/store.py:472-478",[],T,"S113 #444","parche","VIVO, sustrato minimo","diag_a46_relabel en 1 record MODIS, 0 VIIRS",DECL,"A81, D13")
fila("G-35","4 ensamblado","Regla D vent en store: vrp_vent > 0 fuerza summit","pipeline/store.py:437-446",[],T,"S20","parche","SUSTRATO CERO (vent-path apagado)","vrp_vent_mw>0 en 0 records",DECL,"MISSION (removido S27)")
# ---------------- E5 magnitud
fila("G-36","5 magnitud","Wooster por sensor sobre exceso de radiancia; exceso negativo recortado a cero","process_viirs.py:1471-1475; process_modis.py:1058-1060",[],T,"S14, S26","paper (Wooster) + parche (recorte)","VIVO","",DECL,"D25")
fila("G-37","5 magnitud","Fondo de la MAGNITUD depende del camino y del volcan. Bloque contextual: nucleo 3x3 en Villarrica, PCC, Chaiten, PP y Lastarria (solo MODIS y V375; en V750 el parametro se acepta y no hace nada), anillo 5-25 km en el resto. Bloque Test 1: anillo intermedio 1,5-3 km SOLO en Lascar, NdC y Lastarria (V375), fondo global en esos tres (MODIS, V750), anillo 1-3 km del propio Test 1 en los otros ocho",
     "process_viirs.py:1438-1450,1866-1889; test1_integrated.py:129-153; process_modis.py:1044-1056,1351; process_viirs_mod.py:460-467,1230; volcanoes.yaml local_kernel_bg (5 true, 2 false), lbg_global_compatible (3)",
     ["ENABLE_LOCAL_KERNEL_BG","ENABLE_TEST1_LBG_GLOBAL","ENABLE_TEST1_INTERMEDIATE_BG","TEST1_INTERMEDIATE_BG_RING_KM","TEST1_INTERMEDIATE_BG_MIN_PIXELS"],T,
     "S33/S39 (lbg), S58-S63 (nucleo), S112 #439 (intermedio)","A/B por volcan","VIVO",
     "diag_L_bg_local presente en 97 V375 y 151 MODIS, solo en los 5 volcanes opt-in, 0 en V750. El anillo intermedio no deja campo en el record",DECL,
     "MISSION l. 90 (conmuta por volcan), D25, seccion D8. El anillo intermedio tiene 0 menciones en el catalogo y que aplique solo a 3 volcanes no esta escrito fuera del codigo")
fila("G-38","5 magnitud","V375, filtro contextual del Test 1 con keep_peak: de los pixeles del Test 1 solo cuentan los que tambien marca el camino D legacy (G-18), mas el mas caliente",
     "process_viirs.py:1839-1850; pipeline/test1_contextual_filter.py",["ENABLE_TEST1_CONTEXTUAL_FILTER","ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK"],"VIIRS375","S99/S100 (5da0afdef)","A/B (Tupungatito 18,9x)","VIVO","",DECL,"D10, D19")
fila("G-39","5 magnitud","MODIS y V750, magnitud 'nucleo focal': solo pixeles del cumulo que tambien marca el camino D legacy, mas el pico. En MODIS en los dos bloques; en V750 SOLO en el bloque del Test 1",
     "process_modis.py:1155-1160,1405-1410; process_viirs_mod.py:1313-1318; pipeline/vrp_regimes.py:cluster_focal_vrp_mw",["ENABLE_FOCAL_CLUSTER_MAGNITUDE","ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750","FOCAL_CLUSTER_KEEP_PEAK"],"MODIS, VIIRS750","S109 #418 (7b085e8c5), S112 #442","A/B","VIVO",
     "pc.focal_magnitude en 456/457 MODIS y 157/949 V750",DECL,"D11, D19. La asimetria MODIS/V750 no esta declarada")
fila("G-40","5 magnitud","Tope de 5 MW cuando solo disparo lo contextual y t_bg < 270 K (al cumulo y a la suma de escena)",
     "pipeline/path_d_cap.py; process_viirs.py:1407-1414,1479,1551; process_modis.py:999-1006,1068,1162",["PATH_D_ONLY_CAP_MW","PATH_D_ONLY_CAP_TBG_MAX_K"],"los 3; en los hechos solo MODIS","S71 (dbba73e09)","parche D9","VIVO en MODIS, sustrato cero en VIIRS",
     "pc.d9_capped en 59/457 MODIS (7 publicadas), 0 en V375 y V750. Su condicion usa los contadores anulados n_bt y n_nti: con el camino A apagado, 'solo contextual' es casi siempre verdadero y el tope pasa a depender solo de t_bg",DECL,"D9 (cerrada S113); el acoplamiento con G-16 no esta declarado")
fila("G-41","5 magnitud","Modo de un pixel: si el cumulo tiene < 5 MW y <= 3 pixeles se publica el MAXIMO por pixel y no la suma",
     "pipeline/single_pixel_mode.py; process_viirs.py:1573-1578,2024-2029; process_modis.py:1185; process_viirs_mod.py:1094",["ENABLE_SINGLE_PIXEL_SUB_MW_MODE","SUB_MW_REGIME_THRESHOLD_MW","SINGLE_PIXEL_MAX_CLUSTER_PIXELS"],T,"S77 F52-B (6c92c7762)","parche (Tupungatito 30x)","VIVO",
     "single_pixel_mode=True en 837/849 cumulos V375, 185/331 V750, 227/456 MODIS; cambia el numero en 82, 20 y 105",NODECL,"0 menciones en el catalogo y en MISSION")
fila("G-42","5 magnitud","Corona Eq. 6, fondo por vecinos D25, Eq. 16 lago de lava, nucleo espacial del Test 1, VRP TIR (silenciado), VRPTIR Aveni, suma MIROVA-style",
     "process_viirs.py:627-697,1459,1628,1898,2038; store.py:568",["ENABLE_LOCAL_CLUSTER_MAGNITUDE","ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375","ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375","ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750","ENABLE_TEST1_LAVA_LAKE_EQ16","ENABLE_TEST1_SPATIAL_CORE","ENABLE_VRP_TIR_OUTPUT","ENABLE_VRP_TIR_CONSISTENCY_GATE","ENABLE_VRPTIR_AVENI","ENABLE_SUM_VRP_REPORTING"],T,"S99-S145","A/B","APAGADOS",
     "vrp_tir_mw>0, corona_degraded, diag_L_bg_vecinos, vrp_mw_sum_active, vrptir_aveni: 0 records. lava_lake_magmatic=true en Villarrica queda anulado por flag",DECL,"D25, D10")
# ---------------- E6 store
fila("G-43","6 guardado","Tope de 100 pixeles persistidos por record (los de mayor VRP)","process_viirs.py:1487; process_modis.py:1075; pipeline/anomaly_pixels.py",[],T,"S26","anti-bloat del JSON","VIVO",
     "n_anomalous_pixels>100 en 214/457 MODIS y 3/954 V375. Alimenta a G-44 y al nucleo F5 (G-47)",DECL,"MISSION l. 213 (lo da por infra)")
fila("G-44","6 guardado","Geocerca por pixel: los pixeles persistidos a mas de radius_km (25) del CENTRO del volcan se descartan y vrp_mir_mw se recalcula; si el pixel suelto sigue lejos, vrp_mw a cero",
     "pipeline/store.py:217-269,307-313,351-394",["ENABLE_PIXEL_LEVEL_DISTANCE_FILTER"],T,"S35 H8 #3, adoptado S38","parche (PCC)","VIVO",
     "discarded_reason=partial_eruption_hotspot_too_far en 432/457 MODIS, 19 V375, 4 V750: deshace las esquinas que la caja de G-12 recupera",NODECL,"H8 figura en el roadmap del catalogo como 'implementado', no como divergencia; 0 menciones de geocerca")
fila("G-45","6 guardado","Tope de Villarrica: si el cumulo tiene mas de 12 pixeles, vrp_mw a cero",
     "pipeline/store.py:405-412; volcanoes.yaml Villarrica max_cluster_pixels: 12",[],"los 3, solo Villarrica","S77 F52-A (b76dbba97)","parche (glaciar Pichillancahue 11x)","ANULADO AGUAS ABAJO en 8 de 13 casos",
     "apilamiento_f5_single_pixel.json: 13 records topados en el regimen; 8 se publican igual (los 7 de V750 y 1 de MODIS) porque el dashboard lee pc.vrp_mw y isSummitDetection deja pasar todo record con triggered_test1",NODECL,"0 menciones en el catalogo y en MISSION")
fila("G-46","6 guardado","Tope de cordura 50.000 MW con discriminacion por BT > 500 K; piso de VRP por sensor",
     "pipeline/store.py:64-153,73-105",["MIN_VRP_MW_MODIS","MIN_VRP_MW_VIIRS375","MIN_VRP_MW_VIIRS750"],T,"S19 (1a661c29d); piso S12, quitado S130 #571","parche de basura / decision","SUSTRATO CERO en el regimen","0 records con marcas del tope o del piso",DECL,"catalogo (1 mencion), A130")
fila("G-47","6 guardado","Nucleo F5': para V375 se persiste (y el dashboard publica) la suma del pixel pico mas los pixeles a <= 0,75 km o con BT >= 295 K, entre los persistidos a <= inner_km del centroide",
     "pipeline/f5_core.py:34-104; pipeline/store.py:551-554; frontend index 1119-1186",[],"VIIRS375","S96 display (809baa624); S132 #582 al pipeline","medicion propia (F5_CALIBRATION_S95; 0,68 vs 0,58)","VIVO",
     "f5_core_vrp_mw en 846/954. Distinto de pc.vrp_mw en 159: MAYOR en 152 y menor en 7",NODECL,"0 menciones de F5 en el catalogo y en MISSION; vive en CLAUDE.md A10 y en docs/F5_CALIBRATION_S95.md")
fila("G-48","6 guardado","geo_class (summit / extension / far) con catalogo de features: Lacolito PCC 4 km, Lazufre 5 km",
     "pipeline/store.py:522-538; pipeline/volcanic_features.yaml",[],T,"S88 #245","descriptivo","VIVO, no decide publicacion (solo color naranja en el mapa)","geo_class=extension en 1 record MODIS del regimen","no aplica","")
# ---------------- E7 dashboard
fila("G-49","7 dashboard","Cerca: distance_class debe ser summit Y el centroide del cumulo <= inner_km (toggle 'incluir lejanas' apagado por defecto)",
     "frontend/index.html:1043-1064; mosaico.html:245-256; diario.html:239-258",[],T,"S33 (e3bc1f80a), S36","parche de bug S33","VIVO","'valida pero no summit': 400/457 MODIS, 20 V750, 6 V375",DECL,"D13")
fila("G-50","7 dashboard","isValidDetection (cumulo con energia > 0) e isSummitDetection (un record descartado por el pipeline se oculta SALVO que triggered_test1)",
     "frontend/index.html:1466-1488; mosaico.html:393-407; diario.html NO las tiene",[],T,"S29, S77 (47f1ad226), S139","parches","VIVO",
     "publicadas con discarded_reason: 49 V375, 12 V750, 44 MODIS; publicadas con vrp_mw==0: 7 V750 y 1 MODIS (todas Villarrica, G-45)",NODECL,"0 menciones de isValidDetection en el catalogo")
fila("G-51","7 dashboard","Magnitud publicada = F5' en V375 (toggle por vista, encendido por defecto, con respaldo a pc.vrp_mw si F5 <= 0), pc.vrp_mw en MODIS y V750; tope 50.000",
     "frontend/index.html:1086,1166-1193",[],T,"S96/S100","medicion propia","VIVO","tres claves de sessionStorage distintas (vrp_f5_core, diario_f5_core, mosaico_f5_core): el estado del toggle no se comparte entre vistas",NODECL,"idem G-47")
fila("G-52","7 dashboard","Supresion de artefactos: cirrus (t_max < 273,15 K y > 10 MW) y campo difuso (>= 100 px, < 1 MW/px, t_max < 278,15 K, >= 50 MW); nunca sobre un record confirmado por MIROVA (cruce +-60 min con el CSV)",
     "frontend/index.html:1207-1238,1425-1455",[],T,"S90 #259, S93 #277","parche de display (A72 lo marca como candidato a migrar)","SUSTRATO CERO en el regimen","artefacto_termico = 0 de 2.360 pasadas",DECL,"catalogo (1 mencion c/u), D9")
fila("G-53","7 dashboard","Niveles de alerta 1 / 10 / 100 / 1000 MW; titular = ultima deteccion valida de 48 h","frontend/index.html:780-791,1490-1512; mosaico.html:237,418",[],T,"S78","bandas de MIROVA","VIVO","identicas en index y mosaico; diario no tiene niveles",PAPER,"frontend cita 'bandas MIROVA'; sin localizador de paper en el repo: SOSPECHA")
fila("G-54","7 dashboard","El sitio carga por defecto <volcan>_recent.json (100 dias)","scripts/build_recent_json.py; .github/workflows/pages-deploy.yml:76",[],T,"S120","rendimiento","VIVO, no filtra por contenido","","no aplica","")
# ---------------- E8 despues
fila("G-55","8 despues","Auto-audit semanal (abre issue si recall o magnitud salen de banda; excepcion escrita para Lastarria)","scripts/auto_audit_weekly.py; .github/workflows/audit-weekly.yml",[],T,"S119-S124","control","VIVO; no cambia lo que ve el operador","","no aplica","")
fila("G-56","8 despues","Alertas por incidente del NRT (monitor, healthcheck): avisan de la salud del pipeline, no del volcan",".github/workflows/nrt-monitor.yml, nrt-healthcheck.yml",[],T,"S85, S123","control","VIVO; no cambia lo que ve el operador","","no aplica","")
fila("G-57","8 despues","Post-proceso de clasificacion 'confirmado por MIROVA / solo nuestro' a data/clasificacion_referencia/","scripts/clasificar_referencia.py, clasificacion_referencia.py",[],T,"S146 (6861a8dca)","eje de referencia","NO CABLEADO: ningun workflow lo corre y ningun HTML lee 'classification'",
     "grep de 'clasificar_referencia' en .github/workflows: solo un comentario en sync-mirova-csv.yml; grep de 'classification' en frontend: 0","no aplica","")

# ---------------- atributos que no son mecanismo propio: parametros de un camino apagado, o metadatos
DEP = {
 "meta (no decide nada)": ["DATA_SUBDIR","DEFAULT_PROFILE","PROFILES_DIR","PROFILE_NAME","VALID_PROFILES","VOLCANO_OVERRIDES"],
 "contracara GAP A / D23 (retiro de los Test 1 K1 del pool y de la mascara): APAGADOS": ["ENABLE_TEST1_K1_BG_EXCLUDE","ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK"],
 "parametros de la corona Eq. 6 (G-42, apagada)": ["LOCAL_CLUSTER_MAG_MIN_CORONA","LOCAL_CLUSTER_MAG_MODE","LOCAL_CLUSTER_MAG_RING_PX"],
 "parametros del vent-path (G-29, apagado)": ["MAX_VENT_SIGMA_CONTRIB_K","MIN_VENT_PIXELS","MODIS_VENT_THRESHOLD_K","MODIS_VENT_VRP_FLOOR_MW","N_SIGMA_VENT","VENT_THRESHOLD_K"],
 "parametros del camino C (G-29, apagado)": ["NTI_REL_MIN_FLOOR","NTI_REL_N_SIGMA"],
 "parametros del VRP TIR (G-42, salida silenciada)": ["N_SIGMA_TIR","TIR_THRESHOLD_K","VRP_TIR_FLOOR_K","VRP_TIR_N_SIGMA"],
 "parametros del nucleo espacial y Eq. 16 del Test 1 (G-42, apagados)": ["TEST1_CORE_BT_EXT_K","TEST1_CORE_R_KM","TEST1_LAVA_LAKE_EPS","TEST1_LAVA_LAKE_TE_K"],
 "parametros del fondo local NTI del Test 1 (G-28, apagado)": ["TEST1_LOCAL_BG_RING_IN_KM","TEST1_LOCAL_BG_RING_OUT_KM","TEST1_MIN_LOCAL_BG_PIXELS"],
 "parametros de VRPTIR Aveni (G-42, apagado; VRPTIR_K_TIR_I5 ademas no lo lee nadie)": ["VRPTIR_K_TIR_I5","VRPTIR_T_MAX_K","VRPTIR_T_MIN_K"],
 "parametro del fondo por vecinos D25 (G-42, apagado)": ["VRP_BG_NEIGHBOR_MAX_HALF_PX"],
}

json.dump({"generado_por": "experiments/_s146_auditoria/frente_G/construir_inventario.py", "perfil": "mirova_equivalent",
           "n_atributos_perfil": len(P), "regimen_de_las_huellas": ">= 2026-09-01", "filas": R, "atributos_dependientes": {k: {a: P[a] for a in v} for k, v in DEP.items()}},
          open(os.path.join(here, "inventario.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
cub = set(a for r in R for a in [x.split("=")[0] for x in r["valor_efectivo"].split("; ") if x])
no_cub = sorted(set(P) - cub - set(a for v in DEP.values() for a in v))
with open(os.path.join(here, "tabla_inventario.md"), "w", encoding="utf-8") as f:
    f.write("| id | etapa | mecanismo | donde | valor efectivo | sensores | entro | justificacion | estado hoy | evidencia | origen | referencia |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in R:
        entro = r["entro"] + ("<br>" + "<br>".join(r["fechas_git"]) if r["fechas_git"] else "")
        f.write("| " + " | ".join(str(x).replace("|", "/") for x in (r["id"], r["etapa"], r["mecanismo"], r["donde"], r["valor_efectivo"], r["sensores"], entro,
                r["justificacion_de_entrada"], r["estado_hoy"], r["evidencia_estado"], r["origen"], r["referencia_origen"])) + " |\n")
import collections
print("filas:", len(R), collections.Counter(r["origen"] for r in R))
print("atributos del perfil citados en alguna fila:", len(cub & set(P)), "de", len(P))
print("NO citados:", no_cub)
