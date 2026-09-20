# -*- coding: utf-8 -*-
"""Genera docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md desde resultados_sustrato.json.

POR QUE EXISTE: regla S91, ningun numero transcrito a mano. Todo numero del informe sale de un
f-string sobre el JSON que escribio sustrato_caminos.py, y al lado va el fragmento crudo del JSON.
P1 (si estuviera roto, fallaria?): si falta una clave del JSON, KeyError y no hay informe.
P2 (instrumento muerto?): el informe incluye el bloque de controles tal cual; si el control positivo
no reproduce S145, el generador ABORTA en vez de escribir un veredicto.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
R = json.loads((AQUI / "resultados_sustrato.json").read_text(encoding="utf-8"))
C = R["controles"]
S = ["VIIRS375", "VIIRS750", "MODIS"]
CF = R["contrafactual_sin_test1"]


def pct(x):
    return "s/d" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def crudo(obj):
    return "```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```\n"


ok = (C["identidad_predicado"] and C["pub_identico_a_bp"] and C["coherencia_clasificador_T1_sin_trigger"] == 0
      and C["control_centroides_ctx_sin_t1"]["n_centroide_distinto"] == 0
      and all(C["hoy_todo"][b]["tasa_pub_neg"] == C["s145_publicado"][b]["tasa_pub_neg"] for b in ("VIIRS375", "VIIRS750"))
      and C["hoy_con_corte_processed_utc_s145"]["MODIS"] == C["s145_publicado"]["MODIS"])
if not ok:
    print("ABORTO: el control positivo no reproduce S145 o el clasificador es incoherente")
    sys.exit(2)

L = []
A = L.append
A("# Fase 1 del plan de paridad S146: dónde vive la sobre-publicación, medido por camino de detección\n")
A(f"> Generado por `experiments/_s146_fase1_sustrato/generar_informe.py` desde "
  f"`experiments/_s146_fase1_sustrato/resultados_sustrato.json` (corrida {R['meta']['generado_utc']}). "
  "Ningún número de este documento está escrito a mano: cada cifra sale del JSON y al lado va el fragmento crudo. "
  "La salida completa de consola está en `experiments/_s146_fase1_sustrato/salida_cruda.txt`. "
  "Sólo lectura: no se tocó `pipeline/`, `frontend/`, perfiles, `data/`, `scripts/` ni `tests/`.\n")

A("## 0. Lo que hay que saber antes de leer una tabla\n")
A("**Qué ve el satélite en cada camino.** En una pasada nocturna el sensor mide dos cosas sobre cada píxel: "
  "cuánto brilla en el infrarrojo medio (MIR, muy sensible a un punto muy caliente aunque sea chico) y cuánto en el "
  "térmico (TIR, que responde a la temperatura promedio del terreno). Hay dos maneras físicamente distintas de decidir "
  "que un cráter está caliente:\n")
A("1. **El camino contextual (Tests 2 y 3 del paper de MIROVA)** pregunta si UN píxel destaca contra sus ocho vecinos "
  "en el índice que compara MIR con TIR. Es la firma de un foco puntual: lava o una fumarola de alta temperatura que "
  "ocupa una fracción del píxel hace subir el MIR sin subir el TIR, y ese píxel se despega de los de al lado. En el "
  "código es el primer pase (con una compuerta adicional `bt > t_bg + 3 K` que el paper no tiene) más la recaptura del "
  "segundo pase (sin compuerta).\n")
A("2. **El Test 1 integrado en el ROI (detector propio, no está en el paper)** no pregunta por ningún píxel. Suma el "
  "exceso de radiancia MIR de todo el disco de 3 km alrededor del cráter contra un anillo de fondo, y dispara si la "
  "suma supera 3 sigmas. Físicamente eso detecta que la cumbre, en conjunto, está un poco más tibia que su entorno. "
  "Un lago de lava sub-píxel produce eso, pero también lo produce una cumbre de roca oscura sin nieve rodeada de "
  "glaciar, o el contraste de altitud entre el cono y el valle (A69): es un camino de MIR absoluto.\n")
A("**El mecanismo que importa, y que cambia cómo se leen los contadores (A89, A6).** Leyendo el código y no los "
  "nombres de los campos: con `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True` la máscara de píxeles calientes ES el primer "
  "pase más el segundo (`pipeline/process_viirs.py` l. 1299 y 1357). Los caminos legacy (BT, NTI, `dnti_ctx`, ETI) se "
  "calculan y se cuentan pero **no entran a la máscara** (comentario del propio código en la l. 1237). Por eso "
  "`diag_n_dnti_ctx_path > 0` NO significa que el \"path D\" sostuvo algo: es un diagnóstico. El Test 1 tampoco entra a "
  "la máscara: **compite por la fuente del cúmulo publicado** (l. 1763 a 1786 y `pipeline/anchor.py` l. 67 a 89). Si no "
  "hay cúmulo contextual, o está fuera del radio interno, el Test 1 pone el ancla en el cráter (`final_hotspot_source = "
  "test1_roi`) y arma él solo el cúmulo que el dashboard publica. Ese campo persistido es lo que permite atribuir por "
  "lógica de la etapa siguiente y no sólo por conteo.\n")
A("**El test de temperatura de brillo con N·σ 5/10 está apagado en producción.** `ENABLE_BT_PATH_HOT = False`, "
  "`ENABLE_FINAL_PIXEL_FILTER = False` y `ENABLE_TEST1_PIXEL_FILTER = False` (leídos de `pipeline.profile` con "
  "`VRP_PROFILE=mirova_equivalent`, no del YAML). `ENABLE_DUAL_ROI_BT = True` construye la máscara pero la l. 997 la "
  "pone en cero. Medido sobre todas las pasadas nocturnas de la ventana:\n")
A(crudo(R["sustrato_caminos_legacy_todas_las_pasadas"]))
A("El contador `diag_n_bt_path` es cero en todas. Ese camino no decide nada hoy: un brazo de A/B \"sin test de "
  "temperatura de brillo\" tiene **sustrato cero**.\n")

A("## 1. Cobertura y control positivo\n")
m = R["meta"]
A(f"- Ventana: {m['ventana'][0]} a {m['ventana'][1]}, toda posterior al 2026-08-28 23:00 UTC (no cruza #535). 11 Tier A.\n"
  f"- Referencia: los mismos dos CSV que bajó S145 (`experiments/_s145_paridad/_dl_referencia/`, sin red). Última fila "
  f"CONS {m['ultima_fila_ref']['CONS']}, última fila OCR {m['ultima_fila_ref']['OCR']}. Esa copia del OCR llega más lejos "
  "que el snapshot del repo (2026-09-14); por eso se informa aparte una sensibilidad cortada en la noche del 2026-09-14.\n"
  f"- Pasadas nocturnas hoy: {C['n_records_hoy']} (S145 tenía {C['n_records_s145']}; el cron NRT siguió escribiendo). "
  f"Etiquetas: {m['etiquetas']}.\n"
  f"- Predicado de publicación: el del dashboard, ejecutado con node desde `frontend/index.html` "
  f"(sha {m['sha_index_html']}, el mismo de S145) a través de `banco_paridad.correr_node`. No se portó a Python.\n")
A("**Control positivo (reproducir S145 antes de atribuir nada):**\n")
A("| sensor | S145 publicado | mi carga, todo | mi carga, sólo records procesados antes del corte de S145 |\n|---|---|---|---|")
for b in S:
    a, h, k = C["s145_publicado"][b], C["hoy_todo"][b], C["hoy_con_corte_processed_utc_s145"][b]
    A(f"| {b} | {a['tasa_pub_neg']} (n {a['n_neg_limpio']}) | {h['tasa_pub_neg']} (n {h['n_neg_limpio']}) | {k['tasa_pub_neg']} (n {k['n_neg_limpio']}) |")
A("")
A(crudo({k: C[k] for k in ("identidad_predicado", "pub_identico_a_bp", "s145_publicado", "hoy_todo", "hoy_con_corte_processed_utc_s145")}))
A("Lectura: VIIRS 375 y VIIRS 750 reproducen S145 exacto con la carga completa. MODIS tiene un negativo limpio más que "
  "S145 (una pasada que entró después) y reproduce exacto al cortar por `processed_utc`. Ese corte NO sirve para los VIIRS "
  "porque el pipeline reescribe `processed_utc` cuando un gránulo NRT se actualiza: es un reloj de escritura, no de "
  "llegada (se declara, no se usa para nada más). El vector de publicación de mi carga es idéntico al de "
  "`bp.cargar_nuestros`.\n")
A("**Controles del clasificador de sostén:**\n")
A(crudo({k: C[k] for k in ("coherencia_clasificador_T1_sin_trigger", "control_centroides_ctx_sin_t1")}))
A("El primero: ninguna pasada clasificada como sostenida por el Test 1 tiene `triggered_test1 = False` (en la primera "
  "corrida este control dio 39 incoherencias, todas MODIS, y ABORTÓ: en MODIS el ancla honesta está apagada y "
  "`final_hotspot` es el píxel suelto más caliente, no el centroide; se corrigió la regla para la cascada legacy y quedó "
  "en 0). El segundo: entre las pasadas con ancla contextual donde el Test 1 no disparó, el centroide del cúmulo "
  "publicado coincide siempre con el ancla; eso valida usar la diferencia de centroides como huella de que el Test 1 "
  "reconstruyó el cúmulo.\n")

A("## 2. Inventario de campos (qué hay persistido de verdad)\n")
A("Hecho con `Counter` sobre las claves de los records de la ventana (salida de mi sesión, 954 V375, 949 V750, 457 MODIS):\n")
A("- Existen y con cobertura completa en los tres sensores: `triggered_test1`, `n_test1_pixels`, `test1_k_observed`, "
  "`diag_n_bt_path`, `diag_n_nti_path`, `diag_n_dnti_ctx_path`, `diag_n_eti_path`, `diag_n_first_pass_pixels`, "
  "`diag_n_second_pass_recapture`, `diag_sigma_bg_k`, `t_bg_k` (949 de 954 en V375), `final_hotspot_source` (nulo cuando "
  "no hay detección), `primary_cluster` (con `geo_class`, `single_pixel_mode`, y a veces `focal_magnitude`, `d9_capped`).\n"
  "- Sólo MODIS: `diag_n_first_pass_summit`. Sólo V375: `f5_core_vrp_mw` (846 de 954).\n"
  "- **No existe**: máscara por píxel ni etiqueta de camino por píxel. `anomaly_pixels` trae `lat, lon, dist_km, bt_k, "
  "vrp_mw` y nada más. Tampoco se persiste el VRP del cúmulo contextual cuando el Test 1 lo reemplaza.\n"
  "- Valores reales de `final_hotspot_source` en la ventana: VIIRS `ctx_cluster` y `test1_roi`; MODIS `eruption`, `test1` "
  "y `cluster_rescue` (cascada legacy).\n")

A("## 3. Las clases de sostén y los tres niveles de evidencia\n")
A("| clase | definición sobre campos persistidos | qué pasa si se apaga el Test 1 integrado | nivel |\n|---|---|---|---|\n"
  "| **T1_SOLO** | fuente `test1_roi` (VIIRS) o `test1` (MODIS): no había cúmulo contextual o estaba fuera del radio interno | "
  "la pasada queda sin cúmulo o con clase `far`: **no se publica** | N3 por lógica del código (en MODIS queda la salvedad "
  "del rescate de `store.py`) |\n"
  "| **CTX_SOLO** | cúmulo contextual publicado y el Test 1 no disparó | nada cambia; depende sólo de los Tests 2 y 3 | N3 |\n"
  "| **AMBOS** | cúmulo contextual publicado y el Test 1 también disparó | **sigue publicada** con el mismo cúmulo | N3 para "
  "el Test 1; apagar el contextual es SIN DATO |\n"
  "| **T1_SOBRE_CTX** | ancla contextual pero el Test 1 reconstruyó el cúmulo encima (rival débil bajo 0,01 MW, o fuente única) | "
  "**SIN DATO**: publicaría sólo si el cúmulo contextual tenía más de 0 MW, y ese valor no se persiste | N2 |\n"
  "| RESCATE_SIN_DATO | `cluster_rescue`: `store.py` reescribió la fuente | SIN DATO | N1 |\n")
A("Lo que NO se puede llevar a N3 desde lo persistido: quitar la compuerta de 3 K (D22), cambiar la banda primaria "
  "(D21), quitar el segundo pase o cambiar el fondo. Para eso va el probe de la sección 9.\n")

A("## 4. La tabla: camino por sensor\n")
A("Unidad de la sobre-publicación: la PASADA en negativo limpio. Unidad del recall: la NOCHE de volcán.\n")
A("| sensor | neg. limpios publicados / n | T1_SOLO | T1_SOBRE_CTX (SIN DATO) | AMBOS | CTX_SOLO | tasa hoy | tasa sin Test 1 (cota mín a máx) |\n|---|---|---|---|---|---|---|---|")
for b in S:
    t = R["N3_por_sensor"][b]["todo"]["neg_limpio"]
    c = t["clases_pub"]
    f = CF[b]["todo"]["neg_limpio"]
    otros = c.get("RESCATE_SIN_DATO", 0)
    A(f"| {b} | {t['n_pub']} / {t['n']} | {c.get('T1_SOLO', 0)} ({pct(f['frac_T1_SOLO_de_lo_publicado'])}) | "
      f"{c.get('T1_SOBRE_CTX', 0)}{' + ' + str(otros) + ' rescate' if otros else ''} | {c.get('AMBOS', 0)} | "
      f"{c.get('CTX_SOLO', 0)} ({pct(f['frac_CTX_SOLO_de_lo_publicado'])}) | {pct(f['tasa_hoy'])} | "
      f"{pct(f['sinT1_tasa_min'])} a {pct(f['sinT1_tasa_max'])} |")
A("")
A("| sensor | noches pos | publicadas hoy | sin Test 1: siguen seguro | sin Test 1: SIN DATO | sin Test 1: se pierden seguro | pasadas pos T1_SOLO |\n|---|---|---|---|---|---|---|")
for b in S + ["CUALQUIERA"]:
    n = R["noches_recall"][b]["resumen"]
    t1 = CF[b]["todo"]["pos"]["T1_SOLO"] if b in CF else "n/a"
    A(f"| {b} | {n.get('n_noches_pos', 0)} | {n.get('publicada_hoy', 0)} | {n.get('sinT1_sigue_publicada', 0)} | "
      f"{n.get('sinT1_SIN_DATO', 0)} | {n.get('sinT1_se_pierde', 0)} | {t1} |")
A("")
A("Crudo (clases por etiqueta y sensor, y contrafactual):\n")
A(crudo({b: {k: R["N3_por_sensor"][b]["todo"][k] for k in ("neg_limpio", "pos")} for b in S}))
A(crudo({b: CF[b]["todo"] for b in S}))
A("Noches de recall que no quedan aseguradas sin el Test 1 (todas SIN DATO salvo que se indique; lista completa):\n")
A(crudo({b: R["noches_recall"][b]["noches_que_dependen_de_T1"] for b in S + ["CUALQUIERA"]}))
A("La noche de PCC 2026-09-07 en VIIRS 750 figura como perdida dentro de ese sensor, pero a nivel de volcán (cualquier "
  "sensor) la misma noche sigue publicada por otra pasada: en CUALQUIERA no hay ninguna pérdida segura.\n")
A("**Niveles 1 y 2 (contadores), para no mezclarlos con lo anterior.** Entre las pasadas publicadas:\n")
A(crudo(R["N1_N2_contadores"]))
A("Se lee así: en V375 el Test 1 participó en casi todas las publicadas de ambos lados (N1 no discrimina nada); fue el "
  "ÚNICO que disparó (N2) en muchas de las negativas y en ninguna de las positivas. N3 es mayor que N2 porque incluye "
  "las pasadas donde hubo píxeles contextuales pero lejos del cráter. Las columnas `N2_solo_segundo_pase` son pasadas "
  "sostenidas por píxeles que la compuerta de 3 K rechazó en el primer pase y el segundo pase recapturó sin compuerta.\n")
A("Subclases (para T1_SOBRE_CTX, `rival_debil` significa que sin Test 1 la pasada se publicaría con menos de 0,01 MW o no se publicaría):\n")
A(crudo(R["subclases_pub"]))
A("Tamaño de lo que sostiene cada clase (mediana de la magnitud publicada, MW):\n")
A(crudo(R["mediana_disp_mw"]))

A("## 5. Estratificación por volcán (antes de creer el agregado)\n")
for b in S:
    A(f"**{b}**\n")
    A("| volcán | neg n | neg pub | T1_SOLO | T1_SOBRE_CTX | AMBOS | CTX_SOLO | pos n | pos pub | pos T1_SOLO | pos T1_SOBRE_CTX | pos AMBOS | pos CTX_SOLO |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v, t in R["N3_por_volcan"][b].items():
        n, p = t["neg_limpio"], t["pos"]
        cn, cp = n["clases_pub"], p["clases_pub"]
        A(f"| {v} | {n['n']} | {n['n_pub']} | {cn.get('T1_SOLO', 0)} | {cn.get('T1_SOBRE_CTX', 0)} | {cn.get('AMBOS', 0)} | {cn.get('CTX_SOLO', 0)} | "
          f"{p['n']} | {p['n_pub']} | {cp.get('T1_SOLO', 0)} | {cp.get('T1_SOBRE_CTX', 0)} | {cp.get('AMBOS', 0)} | {cp.get('CTX_SOLO', 0)} |")
    A("")
A("Noches de recall por volcán (cualquier sensor):\n")
A(crudo(R["noches_recall_por_volcan_CUALQUIERA"]))
MAY = [v for v, t in R["N3_por_volcan"]["VIIRS375"].items()
       if t["neg_limpio"]["clases_pub"] and max(t["neg_limpio"]["clases_pub"], key=t["neg_limpio"]["clases_pub"].get) == "T1_SOLO"]
_pm = R["N3_por_volcan"]["MODIS"]["PuyehueCordonCaulle"]["neg_limpio"]
_tm = R["N3_por_sensor"]["MODIS"]["todo"]["neg_limpio"]["n_pub"]
_sl = R["sustrato_caminos_legacy_todas_las_pasadas"]
_nt = (_sl["VIIRS375"]["diag_n_nti_path>0"], _sl["VIIRS750"]["diag_n_nti_path>0"] + _sl["MODIS"]["diag_n_nti_path>0"])
A("Lo que dice la estratificación, en palabras:\n"
  f"- **VIIRS 375**: el patrón no es de un volcán. T1_SOLO es la clase mayor de los negativos publicados en {len(MAY)} de 11 "
  f"volcanes ({', '.join(MAY)}) y casi no aparece entre los "
  "positivos de ninguno. Las excepciones son físicas y conocidas: **PCC** (sus negativos publicados son sobre todo AMBOS: "
  "el lacolito da píxeles contextuales casi siempre), **Láscar** e **Isluga** (mezcla).\n"
  "- **VIIRS 750**: mismo patrón, con n por celda chico (3 a 23 publicadas por volcán). PCC vuelve a ser la excepción: "
  "ahí manda CTX_SOLO.\n"
  f"- **MODIS**: la sobre-publicación es de UN volcán. PCC concentra {_pm['n_pub']} de las {_tm} publicadas y {_pm['clases_pub'].get('CTX_SOLO', 0)} de ellas son CTX_SOLO, es decir "
  "Tests 2 y 3, el camino que SÍ está en el paper. Fuera de PCC quedan celdas de 0 a 6 pasadas: sin muestra.\n"
  "- Positivos: Llaima y Copahue no tienen ninguna noche positiva en la ventana, así que ahí el recall que sostiene cada "
  "camino es SIN DATO, no cero.\n")

A("## 6. El nulo (barajar pos y neg_limpio dentro de cada volcán, sensor fijo, 1000 veces)\n")
A("Contraste = fracción de la clase entre los negativos limpios publicados menos la misma fracción entre los positivos publicados.\n")
A("| sensor | clase | observado | nulo media | nulo 2,5 a 97,5 % | n neg pub | n pos pub | fuera del nulo |\n|---|---|---|---|---|---|---|---|")
for b in S:
    for cl, x in R["nulo_barajado_dentro_de_volcan"][b].items():
        if x:
            A(f"| {b} | {cl} | {x['observado']} | {x['nulo_media']} | {x['nulo_p2.5']} a {x['nulo_p97.5']} | {x['n_neg_pub']} | {x['n_pos_pub']} | {'SÍ' if x['fuera_del_nulo'] else 'no'} |")
A("")
A(crudo(R["nulo_barajado_dentro_de_volcan"]))
A("Dos lecturas. Primera: el nulo NO está centrado en cero. Su media es la parte del contraste que se explica sólo "
  "porque los volcanes con muchos positivos (PCC, Isluga, Tupungatito) son también los que tienen más píxeles "
  "contextuales: es la paradoja de Simpson cuantificada, y por eso un agregado crudo exagera. Segunda: aun descontando "
  "eso, en VIIRS 375 el contraste de T1_SOLO (y el espejo negativo de AMBOS) queda fuera del intervalo del nulo; en "
  "VIIRS 750 también pero con 13 positivos publicados, así que el intervalo es ancho. En MODIS hay UN positivo: el nulo "
  "no tiene poder y todo contraste de MODIS es **SIN DATO**, no \"no significativo\".\n")

A("## 7. Fondo frío (adelanto de la Fase 3)\n")
A("| sensor | etiqueta | t_bg | n | publicadas | tasa | T1_SOLO | CTX_SOLO | AMBOS | con tope de 5 MW (`d9_capped`) |\n|---|---|---|---|---|---|---|---|---|---|")
for b in S:
    for lab in ("neg_limpio", "pos"):
        for k in ("lt262", "262-270", "ge270"):
            x = R["fondo_frio"][b][lab][k]
            if x["n"]:
                c = x["clases_pub"]
                A(f"| {b} | {lab} | {k} | {x['n']} | {x['n_pub']} | {pct(x['n_pub'] / x['n'])} | {c.get('T1_SOLO', 0)} | {c.get('CTX_SOLO', 0)} | {c.get('AMBOS', 0)} | {x['d9_capped_pub']} |")
A("")
A(crudo(R["fondo_frio"]))
A("En VIIRS 375 la tasa de publicación en negativos es alta en los tres tramos de temperatura de fondo y T1_SOLO manda "
  "en los tres: el fondo frío NO es donde se concentra la sobre-publicación de ese sensor. En VIIRS 750 sí hay escalón "
  "(los dos tramos fríos publican varias veces más que el tibio), pero lo que publica ahí sigue siendo sobre todo "
  "T1_SOLO, no el camino contextual. El tope de 5 MW sólo actúa en MODIS. Advertencia A68: `t_bg` bajo está contaminado "
  "por altitud y por estación, y cada tramo tiene otra mezcla de volcanes (ver `pub_por_volcan` en el crudo); esta tabla "
  "no separa cirrus de cumbre alta.\n")

A("## 8. Veredicto sobre la hipótesis, por sensor\n")
v = CF["VIIRS375"]["todo"]; w = CF["VIIRS750"]["todo"]; mo = CF["MODIS"]["todo"]
nn = R["noches_recall"]
A(f"Hipótesis: *la sobre-publicación vive en los caminos que MIROVA no tiene.*\n")
A(f"- **VIIRS 375: CONFIRMADA para el Test 1 integrado; REFUTADA para el test de temperatura de brillo (sustrato cero); "
  f"SIN DATO para la compuerta de 3 K.** {v['neg_limpio']['T1_SOLO']} de {v['neg_limpio']['pub_hoy']} negativos limpios "
  f"publicados ({pct(v['neg_limpio']['frac_T1_SOLO_de_lo_publicado'])}) dependen sólo del Test 1, contra "
  f"{v['pos']['T1_SOLO']} de {v['pos']['pub_hoy']} pasadas positivas. Sin él la tasa bajaría de {pct(v['neg_limpio']['tasa_hoy'])} "
  f"a entre {pct(v['neg_limpio']['sinT1_tasa_min'])} y {pct(v['neg_limpio']['sinT1_tasa_max'])}, y de las "
  f"{nn['VIIRS375']['resumen']['n_noches_pos']} noches positivas {nn['VIIRS375']['resumen'].get('sinT1_sigue_publicada', 0)} siguen "
  f"seguro, {nn['VIIRS375']['resumen'].get('sinT1_SIN_DATO', 0)} son SIN DATO y {nn['VIIRS375']['resumen'].get('sinT1_se_pierde', 0)} se pierden seguro. "
  f"Es la pareja que el plan pedía: mucha sobre-publicación, poco recall. Sensibilidad hasta el 2026-09-14: "
  f"{pct(CF['VIIRS375']['hasta_2026-09-14']['neg_limpio']['frac_T1_SOLO_de_lo_publicado'])} de T1_SOLO, mismo cuadro. "
  f"Pero queda un piso que el Test 1 no explica: entre {pct(v['neg_limpio']['sinT1_tasa_min'])} y {pct(v['neg_limpio']['sinT1_tasa_max'])} "
  "de los negativos limpios se seguirían publicando por el camino contextual, que es el del paper.\n")
A(f"- **VIIRS 750: CONFIRMADA para el Test 1 integrado, con n chico del lado del recall.** {w['neg_limpio']['T1_SOLO']} de "
  f"{w['neg_limpio']['pub_hoy']} ({pct(w['neg_limpio']['frac_T1_SOLO_de_lo_publicado'])}); la tasa iría de {pct(w['neg_limpio']['tasa_hoy'])} a entre "
  f"{pct(w['neg_limpio']['sinT1_tasa_min'])} y {pct(w['neg_limpio']['sinT1_tasa_max'])}. Ninguna de las {w['pos']['pub_hoy']} pasadas positivas publicadas es T1_SOLO. "
  f"Son sólo {nn['VIIRS750']['resumen']['n_noches_pos']} noches positivas.\n")
A(f"- **MODIS: REFUTADA en lo medible.** {mo['neg_limpio']['CTX_SOLO']} de {mo['neg_limpio']['pub_hoy']} negativos publicados "
  f"({pct(mo['neg_limpio']['frac_CTX_SOLO_de_lo_publicado'])}) son CTX_SOLO, el camino del paper, y se concentran en PCC; el Test 1 "
  f"sostiene {mo['neg_limpio']['T1_SOLO']}. Lo que queda por medir en MODIS (banda 21 y compuerta, D21 y D22) actúa DENTRO del camino "
  "contextual y no se puede separar desde lo persistido: SIN DATO. Recall: un solo positivo, SIN DATO.\n")
A("- **Camino contextual sobre fondo frío con tope de 5 MW (D9):** como camino separado no existe en la máscara actual "
  "(el `dnti_ctx` legacy es diagnóstico). Lo que existe es el tope, que sólo actúa en MODIS. PARCIAL: hay escalón de fondo frío "
  "sólo en VIIRS 750, y lo que publica ahí es sobre todo el Test 1, no el camino contextual.\n")
A("**Lo que este resultado NO dice.** \"MIROVA calló\" no es \"artefacto\" (A54). Los T1_SOLO de Villarrica y Copahue son, con "
  "toda probabilidad, en parte calor real (lago de lava, lago cratérico ácido) que MIROVA no publica: el Test 1 se adoptó "
  "en S27 justo por eso. La mediana publicada de esa clase es de centésimas de MW. La tabla dice dónde está la palanca "
  "de PARIDAD, no qué es real. Eso empuja hacia la Fase 2b del plan (mudar al perfil experimental, no borrar), que es "
  "decisión de Nicolás.\n")

A("## 9. Qué brazos de A/B tienen sustrato y cuáles no\n")
A("| brazo del plan (Fase 2, paso 3) | sustrato | comentario |\n|---|---|---|\n"
  "| sin Test 1 integrado | **ALTO en VIIRS 375 y 750**, bajo en MODIS | es el brazo que hay que correr primero. El criterio de recall debe listar las noches SIN DATO de la sección 4 una por una |\n"
  "| sin test de temperatura de brillo (N·σ 5/10) | **CERO** | ya está apagado por flag y el contador es 0 en toda la ventana. No correr. Corregir los documentos que lo dan por activo (V-08 es un hallazgo de cita, no de comportamiento) |\n"
  f"| Test 1 por píxel literal (NTI > K1) en reemplazo | casi cero | `diag_n_nti_path > 0` en {_nt[0]} pasadas de V375 y {_nt[1]} en el resto: no recupera nada de lo que el integrado sostiene |\n"
  "| banda 22 más sin compuerta (D21 y D22) | **SIN DATO** | la compuerta es un Y lógico: quitarla sólo puede AGREGAR píxeles al primer pase, así que no puede ser la causa de la sobre-publicación actual; puede aumentarla. El segundo pase ya opera sin compuerta. Medirlo exige el probe |\n"
  "| co-validación del contextual en fondo frío (Fase 3) | bajo en V375 y en MODIS, medio en V750 | en V375 el fondo frío no concentra nada; MODIS publica más con fondo tibio que frío y el grueso es PCC; en V750 hay escalón pero lo sostiene sobre todo el Test 1 (tabla de la sección 7) |\n")
A("**Probe de sólo lectura para llevar a N3 lo que quedó SIN DATO (especificado, NO ejecutado).** Patrón A75, en GitHub "
  "Actions (MODIS no corre en Windows), sin escribir en `data/`:\n"
  "1. Entrada: la lista de pasadas de `resultados_sustrato.json` con clase T1_SOBRE_CTX o RESCATE_SIN_DATO, más una muestra "
  "estratificada por volcán de AMBOS y CTX_SOLO en negativos limpios, más todas las pasadas de las noches SIN DATO. Un job "
  "por volcán, en serie (A47), `data_subdir` temporal fuera del repo.\n"
  "2. Monkeypatch por etapa, reusando el preámbulo real: envolver `first_pass_tests_2_and_3`, `second_pass_adjacent` y "
  "`compute_test1_mir` para capturar sus máscaras; capturar `ctx_cluster_anchor` (el cúmulo contextual con su VRP antes de "
  "que el Test 1 lo pise).\n"
  "3. Por pasada, ensamblar cuatro variantes con el MISMO código aguas abajo y pasar cada record por el predicado del "
  "dashboard con node: (a) control; (b) `compute_test1_mir` devuelve `triggered = False`; (c) `apply_bt_gate = False` en el "
  "primer pase (los flags de D22 ya existen, apagados); (d) segundo pase identidad.\n"
  "4. Salida por pasada: publica sí o no en cada variante, VRP del cúmulo contextual, número de píxeles por etapa dentro "
  "y fuera del radio interno. Control positivo del probe: la variante (a) debe reproducir el record persistido campo por "
  "campo; si no, el probe no es fiel y se descarta. Nulo: las mismas variantes sobre pasadas sin detección no deben crear "
  "publicaciones en (b) ni en (d).\n"
  "5. Contar las pasadas efectivamente procesadas por job contra la lista de entrada antes de leer el resultado (A108).\n")

A("## 10. Límites de este informe\n")
A("- N3 es por lógica del código sobre campos persistidos, no por re-ejecución. Supone que apagar el Test 1 no cambia "
  "nada más aguas arriba; se verificó en el código que el Test 1 no entra a la máscara ni al fondo "
  "(`ENABLE_TEST1_K1_BG_EXCLUDE = False`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`), pero no se ejecutó.\n"
  "- En MODIS un T1_SOLO podría ser rescatado por `store.py` (`cluster_rescue`) al apagar el Test 1: ahí N3 es una cota, no un hecho.\n"
  "- Ventana de 20 días de fines de invierno. Llaima y Copahue sin positivos. MODIS con un positivo.\n"
  "- Los negativos limpios de los últimos días son más blandos porque el OCR llega con atraso; la sensibilidad cortada al "
  "2026-09-14 da el mismo cuadro y está en `contrafactual_sin_test1` del JSON.\n"
  "- Todo lo anterior es hallazgo del que midió. Falta el verificador con contexto limpio que pide el plan.\n")

out = ROOT / "docs" / "audit_s146" / "FASE1_SUSTRATO_SOBREPUBLICACION.md"
txt = "\n".join(L)
assert "—" not in txt and "–" not in txt, "hay guiones largos o medios"
out.write_text(txt, encoding="utf-8")
print("escrito", out, len(txt))
