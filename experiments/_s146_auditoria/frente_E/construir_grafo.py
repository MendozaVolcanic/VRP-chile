# -*- coding: utf-8 -*-
"""Frente E (S146): grafo dirigido de dependencias entre cierres.

Las dos preguntas del instrumento (PLAN_AUDITORIA_S146 seccion 4):
1. Si lo que mide estuviera roto, esta prueba fallaria? Este script NO mide el
   repositorio: serializa nodos y aristas que el auditor leyo y anoto a mano, con
   archivo:linea. Lo unico que calcula es estructura (arrastre, ciclos). Si una
   arista estuviera mal anotada, el script NO lo detecta. El control de esa parte
   es la evidencia textual de cada arista, verificable por un tercero.
2. Si el instrumento estuviera muerto, el resultado se veria distinto? Si: el
   control de abajo arma un grafo de juguete con un ciclo y un arrastre conocidos
   y aborta si el calculo no los reproduce.

Arista = (arriba -> abajo): "el cierre de arriba se apoya en, o hereda la premisa de, el de abajo".
Arrastre de un nodo = cuantos nodos llegan a el por algun camino (lo que cae si el cae).
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIV = "docs/MIROVA_DIVERGENCES.md"
CL = "CLAUDE.md"
MI = "docs/MISSION.md"
HY = "docs/HYPOTHESIS_LOG.md"

# ---------------------------------------------------------------- NODOS
# tipo: cierre | premisa | regla ; caido: None o por que el PROPIO proyecto lo declaro caido
N = {}
def nodo(i, etiqueta, donde, estado, tipo="cierre", censo=(), caido=None):
    N[i] = dict(id=i, etiqueta=etiqueta, donde=donde, estado_declarado=estado,
                tipo=tipo, lineas_censo=list(censo), caido_segun_el_proyecto=caido)

# --- premisas y raices
nodo("P_S114", "Auditoria de fidelidad S114 (file:line + adversarial)", [f"{CL}:112", f"{DIV}:1315"],
     "se cita como prueba de 'deteccion MODIS fiel'", "premisa", [f"{CL}:112", f"{CL}:965", f"{DIV}:1315"],
     caido=f"no miro geometria del ROI ({CL}:948-953, S124) ni los pasos previos a los Tests ({CL}:112-119, S137/S138)")
nodo("P_B21", "Configuracion banda 21 primaria (= D21 abierta)", [f"{DIV}:2232"], "ABIERTA", "premisa",
     caido=f"el paper usa B22 primaria ({DIV}:2234-2239); flag efectivo ENABLE_MODIS_B22_PRIMARY=False (leido hoy)")
nodo("P_GATE", "Compuerta bt > t_bg + 3 K en Tests 2 y 3 (= D22 abierta)", [f"{DIV}:2257"], "ABIERTA", "premisa",
     caido=f"la formula del paper no tiene condicion de temperatura ({DIV}:2261-2266); NTI_BT_SANITY_K=3.0 (leido hoy)")
nodo("P_MIN", "Conectiva min(C1, mu+C2 sigma) como lectura de MIROVA", ["experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md:8-10"],
     "produccion; ENABLE_TESTS_23_PROSE_BRANCH=False (leido hoy)", "premisa",
     caido=f"S136 midio que no reproduce a MIROVA: 3 de 3 negativos con falso positivo ({CL}:1152-1156)")
nodo("P_PISO", "'El piso C1 gobierna el 100 % de MODIS y el 99,9 % de VIIRS' (S136)",
     ["experiments/_s136/POR_QUE_EL_RUIDO_NO_MUEVE_LA_DETECCION.md:18-21"], "medido S136", "premisa",
     caido="S145: el script lee solo el dNTI (Test 2); en el dETI el sigma gobierna en 58,7 % de V375 y 75,0 % de V750 (docs/PLAN_AUDITORIA_S146.md:19; docs/audit_s145/DIVERGENCIAS_MENORES_VERIFICADAS.md:35)")
nodo("P_BAT", "Criterio de la bateria del Apendice A: 9 de 9, caja de 5 km desde la cumbre (S136)",
     ["experiments/_s136/conformidad_apendice.py:46", "docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md:75-92"], "fijado S136, 'no se mueve'", "premisa",
     caido="S138 H-S138-03: no mide lo que se le hace decir (docs/AUDIT_S138.md:35-40); S145: el unico fallo del mejor brazo es del criterio (docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md:82-85)")
nodo("P_S137_A2", "S137: 'la bateria guarda distancias pero no posiciones' (caso A2 no verificable)",
     ["experiments/_s137/RESULTADO_BATERIA_B22.md:46-53 (citado por A2_EL_FALLO...:71-73)"], "hipotesis no verificada", "premisa",
     caido="falso: cada pasada guarda pc_lat/pc_lon (docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md:75-78)")
nodo("P_535", "Regimen de datos previo al PR #535 (mascara de nube 260 K activa en V375) y al #571 (piso VRP)",
     [f"{CL}:1194-1196 (A104)", f"{DIV}:2163-2169"], "regla A104", "premisa",
     caido=f"A104: una ventana que cruza #535 mezcla dos regimenes; V375 pasa de 62,1 % a 87,1 % en negativos limpios ({CL}:1194-1196)")
nodo("P_A54", "A54 / AUDIT_S86: el 95,4 % de los 'FP' son anomalias fisicamente reales", [f"{CL}:642-661", f"{MI}:25-31"],
     "regla vinculante", "regla",
     caido=f"matizada: parte del extra en nevados son FP topograficos ({CL}:804-806; {DIV}:1300-1301); S145: no existe campo por record que separe (b) de (d), la clasificacion S86 fue por volcan y a mano (docs/audit_s145/CLASSIFICATION_SUSTRATO_Y_DISENO.md:23-25,146-155)")
nodo("P_S99", "Hecho canonico S99: MIROVA NRT = un algoritmo por sensor, uniforme entre volcanes", [f"{MI}:82-87"],
     "verificado S99", "premisa")
nodo("P_FENCE", "La cerca del frontend: mirovaEqVrp pone en cero todo record con distance_class != summit",
     [f"{DIV}:1475-1479"], "vigente (display)", "premisa")
nodo("P_PICO", "D10: 'el pixel pico = el crater' (justificacion de keep_peak)", [f"{DIV}:1207"], "adoptado S100", "premisa",
     caido=f"falso en los nevados de senal debil ({DIV}:2189-2192); keep_peak daba paridad por accidente ({CL}:1185)")
nodo("P_A13", "A13: Distancia_km de Villarrica fija en 0,84 km", [f"{CL}:241-250"], "FALSA (S124)", "regla",
     caido=f"{CL}:241-246: vale 0,0 en 3284 de 3338; {DIV}:1138-1144")
nodo("P_A12", "A12: ejemplo 'Lascar 21,6 K e Isluga ~20 K no necesitan kernel-bg'", [f"{CL}:232-240"], "ejemplo FALSO (S128/S131)", "regla",
     caido=f"{CL}:235-238: Lascar 16,9 K e Isluga 8,3 K")
nodo("P_31", "D13: 'la cerca apaga el 31 % de la MAGNITUD'", [f"{DIV}:1468"], "titulo vigente", "premisa",
     caido="S145: el 31 % era fraccion de records; en magnitud 70,7 % (docs/PLAN_AUDITORIA_S146.md:20; docs/audit_s145/D13_CERCA_FRONTEND_REMEDIDA.md:58,137,212-213)")
nodo("P_QC", "'MIROVA hace QC visual manual a posteriori' (el cap de 5 MW lo reemplaza)", [f"{DIV}:333"], "argumento S71", "premisa",
     caido=f"el propio proyecto sostiene que el NRT no se supervisa a mano ({HY}:690-691; {CL}:1197-1199 A105)")
nodo("P_F70", "Instrumento F70: nuestro regrid UTM (A/B de 4 brazos, S124)", [f"{DIV}:1859-1863"], "corrido S124", "premisa",
     caido=f"centrado en el punto equivocado ({DIV}:1959-1962, 6 de 11 con mas de media celda); vecino mas cercano con huecos (docs/AUDIT_S138.md:135-136,322); sin bow tie ({DIV}:2369-2371, y {DIV}:1937-1939: regridear sin de-solapar infla)")
nodo("P_FLAGK1", "S100: se juzgo ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK por su nombre ('controla el reporte')", [f"{DIV}:453-455"],
     "decision S100", "premisa", caido=f"S128: gobierna el POOL de mu/sigma, no el reporte ({DIV}:1326-1330)")
nodo("P_OSF", "Conteos del OSF v2.5 usados como si fueran el NRT", [f"{DIV}:437"], "F1.4 S71", "premisa",
     caido=f"A105: el OSF es filtrado, sus conteos no valen para el NRT ({CL}:1197-1199)")
nodo("P_A66", "A66/A67: area nadir fija = 'clon literal'", [f"{CL}:739", f"{CL}:754"], "adoptado; rebajado S138", "regla",
     caido=f"{CL}:739-740: el paper remuestrea; D17 sigue abierta")

# --- cierres
nodo("C_A82", "A82: far->summit MODIS 'irreducible a 1 km, agotado, no reabrir'", [f"{CL}:948-972", f"{DIV}:1365-1370"],
     "REBAJADA S124 y S138", censo=[f"{CL}:948", f"{CL}:952", f"{CL}:953", f"{CL}:963", f"{CL}:967", f"{CL}:968", f"{DIV}:1368"])
nodo("C_D11", "D11 cara far->summit: CERRADA S114, CONDICIONADA S138", [f"{DIV}:1259", f"{MI}:105-108", f"{CL}:1547-1550"],
     "cerrada/condicionada (tres redacciones distintas)", censo=[f"{DIV}:1259", f"{MI}:106", f"{MI}:107", f"{CL}:1513", f"{CL}:1515"])
nodo("C_A83", "A83: no existe discriminante fisico per-record; 'agotado'", [f"{CL}:974-988"], "vigente, sin marca", censo=[f"{CL}:983"])
nodo("C_A84", "A84: la posicion within-inner del ctx_cluster es irreducible; no re-anclar", [f"{CL}:989-1007"], "vigente, sin marca",
     censo=[f"{CL}:989", f"{CL}:996", f"{CL}:1001"])
nodo("C_D13", "D13: clasificacion CERRADA S126; 'no volver a plantearla'", [f"{DIV}:1501-1511", f"{DIV}:1545-1546"], "cerrada documental",
     censo=[f"{DIV}:1504", f"{DIV}:1509", f"{DIV}:1545"])
nodo("C_NEW8", "NEW-8 (filtros de no-aptos 267-273): 'sigue abierto, A/B F2.1 no accionable' (S116)", [f"{DIV}:478-494", f"{MI}:112"],
     "abierto con prioridad rebajada", censo=[f"{DIV}:435"])
nodo("C_D9", "D9 path-D cirrus: EFECTIVAMENTE RESUELTA en sus dos caras (S113)", [f"{DIV}:534-538", f"{MI}:102-103", f"{CL}:324", f"{CL}:1547"],
     "resuelta, no reabrir", censo=[f"{DIV}:289", f"{DIV}:515", f"{DIV}:534", f"{CL}:324", f"{CL}:1513"])
nodo("C_D9CAP", "D9: 'el cap de 5 MW NO es un parche' (S71)", [f"{DIV}:327-333"], "adoptado S71")
nodo("C_D12", "D12: camino 'distance_class desde el cluster' NO ADOPTAR (S121); C2 peak-of-kernel refutado (S122)", [f"{DIV}:1401-1406", f"{CL}:1546"],
     "fenomeno abierto, caminos cerrados", censo=[f"{DIV}:1403", f"{DIV}:1405", f"{CL}:1512"])
nodo("C_A85", "A85 / gates intra-radio S84-S85: flip OFF, 'MANTENER OFF, cerrado' (S118-S119)", [f"{DIV}:1441-1454", f"{MI}:113-116", f"{HY}:22", f"{CL}:1008-1020"],
     "resuelto", censo=[f"{DIV}:1421", f"{DIV}:1441", f"{MI}:110"])
nodo("C_A81", "A81: re-derivar distance_class simetrico es una trampa; no destapar NdC", [f"{CL}:929-947"], "vigente")
nodo("C_A94", "A94: el bug de la etiqueta far rinde 1 noche de 946 (no priorizar)", [f"{CL}:1132-1150"], "vigente")
nodo("C_D10", "D10 ctxpeak (filtro contextual + keep_peak): ADOPTADO S100, 'el unico que cura sin destruir recall'", [f"{DIV}:1201-1214"],
     "adoptado", censo=[f"{DIV}:1214"])
nodo("C_D5", "D5 magnitud: 'resuelta' / 'calibracion lograda'", [f"{MI}:100", f"{DIV}:145-146"], "resuelta en MISSION; abierta en el catalogo")
nodo("C_D26", "D26: segundo pase sin filtros de no-aptos, 'efecto nulo bajo min'", [f"{DIV}:2353-2359"], "abierta, efecto nulo", censo=[f"{DIV}:2353"])
nodo("C_S136_3", "S136: tres frentes cerrados sin A/B (pool de mu/sigma, retiro de los Test 1 del pool, ajustar C2)",
     ["experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md:44-46", f"{CL}:1152-1158"], "cerrados 'bajo min'")
nodo("C_S136_AR", "S136: banda 22 y remuestreo descartados 'por aritmetica' como palanca de deteccion",
     ["experiments/_s136/POR_QUE_EL_RUIDO_NO_MUEVE_LA_DETECCION.md:1-3,36-47"], "cerrado sin run")
nodo("C_GAPA115", "GAP #A: RESUELTO S115 = mislabel, NO reabrir", [f"{MI}:109-110", f"{DIV}:1318-1320", f"{CL}:120"],
     "resuelto en MISSION; REABIERTO S128 en el catalogo; marcado FALSO en CLAUDE.md", censo=[f"{DIV}:1319", f"{MI}:110", f"{CL}:119", f"{CL}:120"])
nodo("C_NEW7", "NEW-7 / drift #1 (S100): flag K1 'OFF permanentemente; el codigo actual ya es fiel'", [f"{DIV}:435", f"{DIV}:453-456", f"{DIV}:1028"],
     "cerrado S100, sin marca en el lugar", censo=[f"{DIV}:435", f"{DIV}:455"])
nodo("C_GAPA130", "GAP #A S130: 'documentado y dimensionado, sin mas inversion' (A/B sin sustrato)", [f"{DIV}:1335-1358"], "acotado, no cerrado")
nodo("C_D16", "D16: 'la grilla UTM NO explica el sub-reporte', CERRADA (refutada) S124, NO REABRIR", [f"{DIV}:1857", f"{DIV}:1898-1899"],
     "cerrada", censo=[f"{DIV}:1857", f"{DIV}:1886"])
nodo("C_D18", "D18 caja 5x5: A/B S130 NO ADOPTAR; 'diferenciacion summit/scene casi inerte'", [f"{DIV}:1999", f"{DIV}:2062-2093"],
     "abierta, prioridad baja", censo=[f"{DIV}:1999", f"{DIV}:2039", f"{DIV}:2067", f"{DIV}:2088"])
nodo("C_D8", "D8 fondo de anillo contaminado: RESUELTO (kernel-bg opt-in por volcan)", [f"{DIV}:1088-1127", f"{MI}:100"], "resuelto",
     censo=[f"{DIV}:1088", f"{DIV}:1090"])
nodo("C_DPCC", "D-PCC inner_radius: RESUELTO S62 ('inner=7 adoptado')", [f"{DIV}:1129-1136"], "resuelto", censo=[f"{DIV}:1129"])
nodo("C_S29", "S29: 'Lascar 64 % queda como limite fisico aceptado' del MODIS; D4 'cierra al limite del clon literal'", [f"{DIV}:789-801", f"{DIV}:577", f"{MI}:99"],
     "cerrado S27/S29")
nodo("C_D11B", "D11-bis: 'MIROVA nunca publica 0,0; incluso Villarrica da 0,84 fijo (A13)'", [f"{DIV}:1377-1380"], "divergencia formal")
nodo("C_HV084", "H_S61_MIROVA_DIST_FIXED_VILLARRICA: CONFIRMADA", [f"{HY}:361-373"], "confirmada, sin marca", censo=[f"{HY}:365"])
nodo("C_H13", "H13: '3 sigma no es problematico; mantener cap MAX_SIGMA_COMPONENT_K=7'", [f"{HY}:757-768"], "refutada/resuelta S19, sin marca")
nodo("C_HS68", "H_S68_ANTIPATRONES: 'anti-patrones mitigados, NO hay drift critico'", [f"{HY}:160-174"], "confirmada, sin marca", censo=[f"{HY}:163"])
nodo("C_D20", "D20 banda 31 vs 32: 'numericamente despreciable' (calculo Planck S128)", [f"{DIV}:2219-2222"], "hallazgo, despreciable",
     censo=[f"{DIV}:2194", f"{DIV}:2200", f"{DIV}:2205", f"{DIV}:2222"])
nodo("C_D21", "D21: 'ningun brazo cumple aun la bateria' (bloqueo)", [f"{DIV}:2232", f"{DIV}:2250-2251"], "abierta, bloqueada")
nodo("C_HA2", "H_S137_A2_FLANCO: 'active, pendiente'", [f"{HY}:1478-1485"], "active")
nodo("C_S143", "H_S143_D22_D25: NO ADOPTAR (VIIRS 375)", [f"{HY}:1507-1520"], "resuelta: no adoptar")
nodo("C_S133", "S133: A/B banda 22 en MODIS, NO ADOPTAR", ["docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md:148-155", f"{DIV}:2252"], "no adoptar")
nodo("C_THR", "S71: 'thresholds NO son el problema' (descarta tunear C2/sigma)", [f"{DIV}:403-405", f"{DIV}:504"], "refutacion bibliografica, 'no perseguir'")
nodo("C_F14", "F1.4: geofencing 25 km 'empiricamente optimo' (98,27 % de los records OSF)", [f"{DIV}:437", f"{DIV}:508"], "refutado/no cambiar")
nodo("C_S45", "S45: 'D9 cluster selection: summit-priority confirmado Lascar' (titulo)", [f"{DIV}:856", f"{DIV}:885"], "titulo dice confirmado")
nodo("C_D19N", "D19 (S134): 'D11/A82 quedan intactas'", [f"{DIV}:2189-2192"], "frase de relacion, sin marca")
nodo("C_A77", "A77: VIIRS375 cubre el recall que MODIS no resuelve", [f"{CL}:893-901"], "vigente")
nodo("C_D14", "D14 mascara de nube: CERRADA S128 (cita verbatim) y apagada", [f"{DIV}:1550", f"{DIV}:1632-1652", f"{MI}:142"], "cerrada",
     censo=[f"{DIV}:1550", f"{MI}:142"])
nodo("C_D25V", "D25 en M-band (S145): 'es fidelidad de magnitud, no recall'", [f"{DIV}:2322-2336"], "abierta, flag apagado")
nodo("C_HV2", "H_S141_VECINO_FOCO_V2: resuelta como no confirmada", [f"{HY}:1497-1505"], "no confirmada")
nodo("C_S144", "H_S144_DIRECCION / frente keep_peak con direccion: CERRADO sin correr", [f"{HY}:1536", f"{DIV}:2099-2108"], "cerrado", censo=[f"{HY}:1536"])

# ---------------------------------------------------------------- ARISTAS
E = []
X = []  # relaciones que NO son dependencia (contradiccion o tension): no entran al arrastre
def ar(a, b, clase, evidencia, nota="", rel="depende"):
    assert a in N and b in N, (a, b)
    assert clase in ("EXPLICITA", "INFERIDA")
    assert rel in ("depende", "contradicho_por", "tension")
    d = dict(arriba=a, abajo=b, clase=clase, relacion=rel, evidencia=evidencia, nota=nota)
    (E if rel == "depende" else X).append(d)

ar("C_A82", "P_S114", "EXPLICITA", f"{CL}:965-966 'La auditoria de fidelidad file:line+adversarial confirmo que la deteccion MODIS YA es fiel'; {CL}:948-950 'La auditoria S114 en que se apoya cubrio umbrales, tests, kernel y second-run, NO la geometria del ROI'")
ar("C_A82", "P_B21", "EXPLICITA", f"{CL}:948 'los ejes que la regla da por agotados se barrieron sobre records producidos con banda 21 primaria (D21) y compuerta (D22)'")
ar("C_A82", "P_GATE", "EXPLICITA", f"{CL}:948 (misma frase)")
ar("C_A82", "C_A77", "EXPLICITA", f"{CL}:970-971 'El recall MODIS lo cubre VIIRS375 (A77)'; {DIV}:1367-1368")
ar("C_D11", "C_A82", "EXPLICITA", f"{DIV}:1365 'Veredicto (A82)'; {MI}:107 'todos los ejes agotados, A82'")
ar("C_A82", "C_D11", "EXPLICITA", f"{CL}:957 'S114, cierre exhaustivo de D11-MODIS'; {CL}:971-972 'Detalle: docs/AUDIT_S114_PARITY_BY_SENSOR.md'", "cita mutua: forma ciclo con la arista anterior")
ar("C_D11", "P_S114", "EXPLICITA", f"{DIV}:1315-1317 'Auditoria de fidelidad file:line + adversarial: la deteccion MODIS YA es FIEL' (sin marca en el lugar)")
ar("C_D11", "P_B21", "EXPLICITA", f"{DIV}:1259 'valen solo bajo banda 21 primaria y compuerta de 3 K, D21 y D22'")
ar("C_D11", "P_GATE", "EXPLICITA", f"{DIV}:1259")
ar("C_D11", "C_GAPA115", "EXPLICITA", f"{DIV}:1318-1320 'Unico gap de fidelidad literal: GAP #A ... RESUELTO S115 = mislabel'")
ar("C_D11", "C_D21", "EXPLICITA", f"{DIV}:1259 'No se reabre el frente far->summit por la via espectral hasta consolidar D21/D22'; docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md:264-267")
ar("C_D21", "P_BAT", "EXPLICITA", f"{DIV}:2232 'ningun brazo cumple aun la bateria'; {DIV}:2250-2251")
ar("C_D21", "P_S137_A2", "EXPLICITA", f"{DIV}:2251 'la de Eyjafjallajokull es de la evaluacion'; docs/audit_s145/A2_EL_FALLO_ES_DEL_CRITERIO.md:69-78")
ar("C_HA2", "P_S137_A2", "EXPLICITA", f"{HY}:1482-1485 'no se contrasto ... Estado: active ... pendiente' contra A2_EL_FALLO...:75-78 (verificable desde S137)")
ar("C_S143", "P_BAT", "INFERIDA", "el A/B de S143 nace del pre-registro que hereda la atribucion de la bateria (D22/D25 como palancas de A6); docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md:156-162", "el veredicto de S143 en si esta medido sobre produccion; lo heredado es la eleccion de brazos")
ar("C_A83", "C_A82", "EXPLICITA", f"{CL}:981 'Mecanismo (A82): a 1 km el foco sub-pixel real y el ruido topografico difuso son el MISMO objeto'")
ar("C_A83", "P_B21", "EXPLICITA", "docs/AUDIT_S138.md:94-96 'A82, A83, A84, el camino de D12 y el no adoptar B22 de S134 heredan la configuracion que S137 puso en duda (banda 21, compuerta)'")
ar("C_A83", "P_GATE", "EXPLICITA", "docs/AUDIT_S138.md:94-96")
ar("C_A84", "C_A82", "EXPLICITA", f"{CL}:989-990 'irreducible igual que el far->summit (A82) ... instance-en-posicion de A82/A83'")
ar("C_A84", "C_A83", "EXPLICITA", f"{CL}:989-990, {CL}:994-995 'indistinguibles ... A83'")
ar("C_D12", "P_B21", "EXPLICITA", "docs/AUDIT_S138.md:94-96")
ar("C_D12", "P_GATE", "EXPLICITA", "docs/AUDIT_S138.md:94-96")
ar("C_S133", "P_GATE", "EXPLICITA", "docs/AUDIT_S138.md:94-96; docs/audit_s145/D21_D22_ESTADO_DEL_BLOQUEO.md:153-155 (paridad contra MIROVA con n=0 en tres casilleros)")
ar("C_D13", "C_A82", "EXPLICITA", f"{DIV}:1503-1504 'mas el artefacto topografico A69 en los nevados, que a 1 km es irreducible (A82)'")
ar("C_D13", "P_A54", "EXPLICITA", f"{DIV}:1501-1503 'es en buena parte la categoria (b) de A54'; {DIV}:1509-1510")
ar("C_D13", "P_31", "EXPLICITA", f"{DIV}:1468 (titulo) contra la tabla {DIV}:1483-1485, que rotula 'records apagados'")
ar("C_D13", "P_535", "EXPLICITA", f"{DIV}:1519-1520 ventana '2026-05-01 a 2026-08-28': entera antes de #535 (2026-08-28 23:00 UTC, {CL}:1194)")
ar("C_NEW8", "C_A82", "EXPLICITA", f"{DIV}:493 'aplicarlo removeria senal real, killer A82'")
ar("C_NEW8", "C_D9", "EXPLICITA", f"{DIV}:480-482 'ya esta mitigado por otros frentes: D9 cap path-D 5 MW + gate/guard A46 + nadir/focal'")
ar("C_NEW8", "P_A54", "EXPLICITA", f"{DIV}:490-492 'son cat-b real sub-umbral (A54)'")
ar("C_D9", "C_NEW8", "EXPLICITA", f"{DIV}:464-470 'Los 4 gaps documentales F1.2 explican mejor el drift remanente' (la causa raiz abierta de D9 apunta a NEW-8)", "con la arista anterior forma ciclo de justificacion mutua")
ar("C_D9", "P_FENCE", "EXPLICITA", f"{DIV}:516-517 '0 fuga al dashboard (el gate far de mirovaEqVrp los esconde)'; {DIV}:535")
ar("C_D9", "P_A66", "EXPLICITA", f"{DIV}:526-529 'CURADA por las adopciones nadir/focal S102-S109 ... mediana 0,53x = calibracion clon-literal sana'")
ar("C_D9", "C_D9CAP", "EXPLICITA", f"{DIV}:534-535 'FP de deteccion capeado (C, S71)'")
ar("C_D9CAP", "P_QC", "EXPLICITA", f"{DIV}:333 'El cap 5 MW reemplaza programaticamente el QC visual que MIROVA hace manualmente'")
ar("C_D9", "P_535", "INFERIDA", f"la verificacion S113 es de mayo-junio 2026 ({DIV}:527-528), regimen previo a #535; no re-medida despues", "SOSPECHA de alcance: D9 es sobre todo MODIS, cuya mascara ya valia 0.0")
ar("C_D12", "C_D9", "INFERIDA", f"{DIV}:1403-1404 el camino de D12 se rechazo porque 'destapa el path-D, PCC 117 MW': presupone que la magnitud path-D sigue viva detras de la etiqueta far, lo que D9 da por curado", "tension, no dependencia limpia", rel="tension")
ar("C_A85", "P_FENCE", "EXPLICITA", f"{DIV}:1446-1447 'costo = cola inflada 0,5-1,3 % (mayormente far, 42/46 filtradas por frontend)'")
ar("C_A85", "P_S99", "EXPLICITA", f"{DIV}:1449-1450 'gate per-volcan quedo EXCLUIDO por MISSION l.77'; {CL}:1018-1020")
ar("C_A85", "C_A82", "EXPLICITA", f"{DIV}:1447 'peor caso difuso A69/A82 no-MIROVA-conf'")
ar("C_A85", "P_535", "INFERIDA", "A/B run 28312968093 y verificacion S119 son de junio-julio 2026: regimen previo a #535; no re-verificado despues")
ar("C_A81", "C_A82", "INFERIDA", f"{CL}:940 '73 de NdC = artefacto A69 (NO destapar)': la clasificacion de artefacto es la de A69/A82")
ar("C_A94", "C_A81", "EXPLICITA", f"{CL}:1138-1139 'de las 4 noches que destaparia 3 son el artefacto de NdC que S113 ya dijo no destapar'")
ar("C_D10", "P_PICO", "EXPLICITA", f"{DIV}:1207 'conserva siempre el pixel pico (= crater)'; caida en {DIV}:2189-2192")
ar("P_A66", "C_D10", "EXPLICITA", f"{DIV}:1226-1228 'adoptar nadir + MANTENER ctxpeak'; {CL}:746-750")
ar("C_D5", "P_A66", "EXPLICITA", f"{MI}:100 'D5 magnitud (nadir S102/103 + ctxpeak D10 S100)'")
ar("C_D5", "C_D10", "EXPLICITA", f"{MI}:100")
ar("C_D26", "P_PISO", "EXPLICITA", f"{DIV}:2359 'el piso gobierna y el efecto sobre el umbral es nulo (S136 midio que mu + C2 sigma > C1 en el 100 % de MODIS)'")
ar("C_D26", "P_MIN", "EXPLICITA", f"{DIV}:2353 'efecto nulo bajo la conectiva min'")
ar("C_S136_3", "P_MIN", "EXPLICITA", f"{CL}:1154-1156; experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md:8-10")
ar("C_S136_3", "P_PISO", "EXPLICITA", "experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md:36-38")
ar("C_S136_AR", "P_PISO", "EXPLICITA", "experiments/_s136/POR_QUE_EL_RUIDO_NO_MUEVE_LA_DETECCION.md:18-21,36-47")
ar("C_S136_AR", "P_MIN", "EXPLICITA", "experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md:42-43 'correcta bajo min y falsa bajo max'")
ar("C_GAPA130", "C_S136_3", "INFERIDA", "el retiro de los Test 1 del pool es uno de los tres frentes de C_S136_3 (EL_CIERRE...:44-46); bajo min con piso gobernando, mover el pool no puede mover el umbral aunque hubiera sustrato: el nulo del A/B de S130 tiene dos explicaciones y el catalogo solo nombra una (sustrato)")
ar("C_GAPA130", "P_PISO", "INFERIDA", f"{DIV}:1331 dice que el K1 en el pool 'sube el umbral mu + C2 sigma'; eso solo importa donde el sigma gobierna: segun S136 nunca, segun S145 en 58,7-75 % de VIIRS")
ar("C_GAPA115", "C_NEW7", "EXPLICITA", f"{DIV}:1319-1321 repite la lectura de S100 ('fuera del pool m,sigma ... ya cubierto')")
ar("C_NEW7", "P_FLAGK1", "EXPLICITA", f"{DIV}:453-455 contra {DIV}:1326-1330 ('Se lo juzgo por su NOMBRE y no por como lo lee el codigo, A89')")
ar("C_D16", "P_F70", "EXPLICITA", f"{DIV}:1859-1863 (el A/B es el instrumento) contra {DIV}:1959-1962, docs/AUDIT_S138.md:135-136, {DIV}:1937-1939")
ar("C_D16", "P_535", "EXPLICITA", f"{DIV}:1863 'ventana 2026-06-25..08-24': entera antes de #535")
ar("C_S136_AR", "C_D16", "INFERIDA", "S136 descarta el remuestreo tratandolo como promediado de ruido blanco (EL_CIERRE...: seccion 'Sobre el punto 2'); D16 es el antecedente empirico de que 'la grilla no aporta'")
ar("C_D18", "C_A82", "EXPLICITA", f"{DIV}:2039-2041 y {DIV}:2065-2066 'refuta la hipotesis de que fuera la llave que A82 dejo abierta'")
ar("C_D18", "P_S99", "EXPLICITA", f"{DIV}:2031-2032 'Y es per-volcan, que MISSION excluye'")
ar("C_D18", "P_B21", "INFERIDA", f"{DIV}:2085-2090 'las detecciones pasan con margen suficiente': con B21 el sigma del dNTI es ~4x mayor y el primer paso tiene ~55-60 px por escena; con B22 queda vacio en 80 de 84 ({DIV}:2246-2247). El margen es propiedad de la configuracion")
ar("C_D8", "P_A12", "EXPLICITA", f"{DIV}:1100-1103 (tabla 'Bajo-Medio >20K: Lascar, Isluga, NO necesita') contra {CL}:235-238")
ar("C_D8", "P_S99", "INFERIDA", f"el fix es opt-in por volcan ({DIV}:1114-1127), lo que {MI}:82-87 excluye; {DIV}:2316 lo dice: 'D8 quedo marcada resuelta por el kernel opt-in, pero la divergencia literal sigue vigente'")
ar("C_D5", "C_D8", "INFERIDA", f"{MI}:100-101 lista D8 entre las resueltas que 'no justifican features nuevas'; D25 ({DIV}:2316) la reabre de hecho")
ar("C_DPCC", "C_D8", "INFERIDA", "misma tanda S60-S62, misma metodologia de preview offline (A18)")
ar("C_S29", "C_D12", "EXPLICITA", f"{DIV}:789-793 'el crater realmente NO tiene radiancia integrada detectable en MODIS' contra {DIV}:1408-1411 'El primary_cluster MODIS esta en el crater (mediana 1,46 km) pero el pixel suelto mas caliente cae en el Salar'", "D12 contradice la causa que S29 acepto como limite fisico", rel="contradicho_por")
ar("C_D11B", "P_A13", "EXPLICITA", f"{DIV}:1379-1380 'incluso Villarrica al crater da 0,84 km fijo, A13'")
ar("C_HV084", "P_A13", "EXPLICITA", f"{HY}:364-373 es el origen de A13; {CL}:241 la declara FALSA")
ar("C_D20", "P_PISO", "INFERIDA", f"{DIV}:2219-2222 compara el corrimiento (hasta 0,0054) contra el margen de K1 (~0,14); si el umbral que decide es el piso C1 = 0,003 (S136, A103 {CL}:1190-1193), la vara pertinente es 0,003 y el corrimiento no es uniforme en una escena con gradiente 250-290 K (A69)")
ar("C_THR", "P_B21", "INFERIDA", f"{DIV}:403-405 descarta 'C2/sigma ni umbral' con Laiolo 2017; H_S137_SIGMA_MIROVA ({HY}:1458-1462) mide nuestro sigma del dNTI 10x el del autor con B21")
ar("C_F14", "P_OSF", "EXPLICITA", f"{DIV}:437 '21,79 % records OSF v2.5 chilenos > 5 km ... cubre 98,27 % records'")
ar("C_S45", "C_D11", "INFERIDA", f"titulo {DIV}:856 'summit-priority confirmado' contra {DIV}:1070-1072 'Esto refuta hipotesis D9 summit-priority exclusiva' (mismo documento)", "contradiccion interna; no es dependencia real, se ancla aqui por ser el mismo objeto Lascar MODIS far->summit", rel="contradicho_por")
ar("C_D19N", "C_A82", "EXPLICITA", f"{DIV}:2191-2192 'D11/A82 quedan intactas' (S134) contra {DIV}:1259 (S138)")
ar("C_D25V", "C_HV2", "EXPLICITA", f"{DIV}:2331-2333 'en VIIRS 375 el fondo del cumulo ya se midio ... y no cerro la brecha en ningun volcan (H_S141_VECINO_FOCO_V2)'")
ar("C_HS68", "P_A54", "INFERIDA", f"{HY}:166-169 '14/2282 records (0,6 %) afectados por floors. Negligible' contra {MI}:143 'Alcance medido S124: 1564 de 23990 records summit (6,5 %)'", "contradiccion de numeros y de veredicto; se ancla aqui por ser la misma familia 'no tocar la precision'", rel="contradicho_por")
ar("C_H13", "P_S99", "INFERIDA", f"{HY}:764-766 'mantener n_sigma 3.0 + MAX_SIGMA_COMPONENT_K 7.0' contra {CL}:106-108 (3 sigma uniforme era el drift, resuelto) y {MI}:137 (cap neutralizado a 999; leido hoy MAX_SIGMA_COMPONENT_K=999.0)", rel="contradicho_por")

# ---------------------------------------------------------------- CALCULO
def ancestros(objetivo, aristas):
    padres = {}
    for e in aristas:
        padres.setdefault(e["abajo"], set()).add(e["arriba"])
    visto, pila = set(), [objetivo]
    while pila:
        x = pila.pop()
        for p in padres.get(x, ()):
            if p not in visto and p != objetivo:
                visto.add(p); pila.append(p)
    return visto

def ciclos(nodos, aristas):
    hijos = {}
    for e in aristas:
        hijos.setdefault(e["arriba"], set()).add(e["abajo"])
    encontrados = set()
    def dfs(inicio, x, camino):
        for h in hijos.get(x, ()):
            if h == inicio:
                c = camino[:]
                k = c.index(min(c)); encontrados.add(tuple(c[k:] + c[:k]))
            elif h not in camino and h > inicio:
                dfs(inicio, h, camino + [h])
    for n in sorted(nodos):
        dfs(n, n, [n])
    return [list(c) for c in sorted(encontrados)]

# control de instrumento: grafo de juguete con ciclo a<->b y c->a
_j = [dict(arriba="a", abajo="b"), dict(arriba="b", abajo="a"), dict(arriba="c", abajo="a")]
assert ancestros("b", _j) == {"a", "c"}, "control de arrastre roto"
assert ciclos({"a", "b", "c"}, _j) == [["a", "b"]], "control de ciclos roto"
assert ciclos({"a", "b"}, [dict(arriba="a", abajo="b")]) == [], "control negativo de ciclos roto"

arrastre = {i: sorted(ancestros(i, E)) for i in N}
for i in N:
    N[i]["arrastre_n"] = len(arrastre[i]); N[i]["arrastre"] = arrastre[i]
cyc = ciclos(set(N), E)

# cierres en falso: cierres que llegan por algun camino a un nodo caido
hijos = {}
for e in E:
    hijos.setdefault(e["arriba"], []).append(e)
def caidos_alcanzables(i):
    out, visto, pila = {}, set(), [(i, [], True)]
    while pila:
        x, cam, solo_expl = pila.pop()
        for e in hijos.get(x, []):
            b = e["abajo"]; ok = solo_expl and e["clase"] == "EXPLICITA"
            if N[b]["caido_segun_el_proyecto"]:
                prev = out.get(b)
                if prev is None or (ok and not prev["solo_explicitas"]):
                    out[b] = dict(camino=cam + [b], solo_explicitas=ok)
            if (b, ok) not in visto:
                visto.add((b, ok)); pila.append((b, cam + [b], ok))
    return out
for i in N:
    N[i]["premisas_caidas_heredadas"] = caidos_alcanzables(i) if N[i]["tipo"] == "cierre" else {}

aqui = os.path.dirname(os.path.abspath(__file__))
json.dump(dict(generado="2026-09-20", nota="aristas anotadas a mano por el auditor con archivo:linea leido en la sesion; el script solo calcula estructura",
               flags_leidos_de_pipeline_profile=dict(ENABLE_TESTS_23_PROSE_BRANCH=False, ENABLE_MODIS_B22_PRIMARY=False, NTI_BT_SANITY_K=3.0,
                   ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK=False, ENABLE_SECOND_PASS_CONDITIONED=False, ENABLE_UTM_REGRID=False, CLOUD_MASK_BT_K=0.0,
                   ENABLE_UNSUITABLE_FILTERS_267_273=True, ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True, ENABLE_PATH_D_INTRA_RADIO_GATE=False,
                   ENABLE_SECOND_PASS_INTRA_RADIO_GATE=False, ENABLE_LOCAL_KERNEL_BG=True, MAX_SIGMA_COMPONENT_K=999.0, PATH_D_ONLY_CAP_MW=5.0,
                   ENABLE_ROI1_BOX_PAPER=False, ENABLE_DAYTIME_MODIS=False),
               n_nodos=len(N), n_aristas=len(E), relaciones_no_dependencia=X, n_explicitas=sum(e["clase"] == "EXPLICITA" for e in E),
               n_inferidas=sum(e["clase"] == "INFERIDA" for e in E), ciclos=cyc, nodos=list(N.values()), aristas=E),
          open(os.path.join(aqui, "grafo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# mermaid
L = ["graph TD"]
_con_arista = {e["arriba"] for e in E + X} | {e["abajo"] for e in E + X}
for i, n in N.items():
    if i not in _con_arista:
        continue
    t = n["etiqueta"].replace('"', "'").replace("PR #", "PR ").replace("#", "PR ").replace("->", " a ").replace(">", " mayor que ")
    t = (t[:58] + "...") if len(t) > 61 else t
    forma = f'{i}["{t}"]' if n["tipo"] == "cierre" else f'{i}(["{t}"])'
    L.append("  " + forma)
for e in E:
    L.append(f'  {e["arriba"]} {"-->" if e["clase"] == "EXPLICITA" else "-.->"} {e["abajo"]}')
for e in X:
    L.append(f'  {e["arriba"]} -. {e["relacion"].replace("_", " ")} .-> {e["abajo"]}')
L.append("  classDef caido fill:#f8d7da,stroke:#a33;")
L.append("  class " + ",".join(i for i, n in N.items() if n["caido_segun_el_proyecto"]) + " caido;")
open(os.path.join(aqui, "grafo.mmd"), "w", encoding="utf-8").write("\n".join(L) + "\n")

print("nodos", len(N), "aristas", len(E), "explicitas", sum(e["clase"] == "EXPLICITA" for e in E), "inferidas", sum(e["clase"] == "INFERIDA" for e in E))
print("ciclos:", cyc)
print("\nARRASTRE (top):")
for i in sorted(N, key=lambda k: -N[k]["arrastre_n"])[:14]:
    print(f'  {N[i]["arrastre_n"]:>2}  {i:10s} caido={"SI" if N[i]["caido_segun_el_proyecto"] else "no"}  {arrastre[i]}')
print("\nCIERRES EN FALSO (heredan al menos una premisa caida):")
for i, n in N.items():
    if n["tipo"] == "cierre" and n["premisas_caidas_heredadas"]:
        ex = [k for k, v in n["premisas_caidas_heredadas"].items() if v["solo_explicitas"]]
        inf = [k for k, v in n["premisas_caidas_heredadas"].items() if not v["solo_explicitas"]]
        print(f"  {i:10s} por via solo EXPLICITA: {ex} | con algun tramo INFERIDO: {inf}")
limpios = [i for i, n in N.items() if n["tipo"] == "cierre" and not n["premisas_caidas_heredadas"]]
print("\nCIERRES DEL GRAFO SIN PREMISA CAIDA HEREDADA:", limpios)
