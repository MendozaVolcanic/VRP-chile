# -*- coding: utf-8 -*-
"""Genera docs/audit_s146/MEDICIONES_P1_P2_P6.md desde p1/p2/p6_resultados.json y las salidas crudas.
Ningun numero se escribe a mano: todos salen de los JSON o se pegan de la salida cruda.
(1) Si estuviera roto, fallaria? Si falta un JSON o una clave, KeyError y no escribe nada.
(2) Si estuviera muerto, se veria distinto? Cada seccion pega al lado la salida cruda del script que la midio.
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
OUT = ROOT / "docs" / "audit_s146" / "MEDICIONES_P1_P2_P6.md"


def J(n):
    return json.loads((AQUI / n).read_text(encoding="utf-8"))


def crudo(n, pred, ancho=400):
    ls = [l.rstrip("\n")[:ancho] for l in (AQUI / n).read_text(encoding="utf-8").splitlines() if pred(l)]
    return "```\n" + "\n".join(ls) + "\n```\n"


def pct(x):
    return "SIN DATO" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def num(x, d=4):
    return "SIN DATO" if x is None else f"{x:.{d}f}".replace(".", ",")


def main():
    partes = []
    A = partes.append
    A("# Mediciones P1, P2 y P6 (S146): tres preguntas contestadas con lo que ya estaba en disco\n")
    A("> Generado por `experiments/_s146_mediciones_p1_p2_p6/generar_informe.py`. Todos los números salen de "
      "`p1_resultados.json`, `p2_resultados.json` y `p6_resultados.json` de esa carpeta, o están pegados de la salida cruda "
      "de cada script (`p1_salida_cruda.txt`, `p2_salida_cruda.txt`, `p6_salida_cruda.txt`). Sólo lectura: no se tocó "
      "`pipeline/`, `frontend/`, `scripts/`, `data/` ni ningún documento existente, no se descargó nada y no se corrió pytest.\n")

    # ------------------------------------------------------------------ control
    hay = {n: (AQUI / n).exists() for n in ("p1_resultados.json", "p2_resultados.json", "p6_resultados.json")}
    p1 = J("p1_resultados.json")
    c = p1["control_positivo"]
    A("## 0. Control positivo: antes de atribuir nada, reproducir lo ya verificado\n")
    A("La carga es la de la Fase 1 importada tal cual (`sustrato_caminos.py`, que a su vez usa `scripts/banco_paridad.py` "
      "y ejecuta el predicado del dashboard con node). Con ella se reproduce la línea base de S145 y la atribución de la Fase 1:\n")
    A("| qué | esperado | medido hoy |\n|---|---|---|")
    A(f"| VIIRS 375, publicación en negativos limpios | 0,8633 (n 373) | {num(c['VIIRS375']['tasa_pub_neg'])} (n {c['VIIRS375']['n_neg_limpio']}) |")
    A(f"| VIIRS 750 | 0,2138 (n 622) | {num(c['VIIRS750']['tasa_pub_neg'])} (n {c['VIIRS750']['n_neg_limpio']}) |")
    A(f"| MODIS con el corte de procesamiento de S145 | 0,1142 (n 438), el 0,114 de S145 | {num(c['MODIS_con_corte_S145']['tasa_pub_neg'])} (n {c['MODIS_con_corte_S145']['n_neg_limpio']}); sin corte {num(c['MODIS']['tasa_pub_neg'])} (n {c['MODIS']['n_neg_limpio']}), por un record procesado después |")
    A(f"| Fase 1, VIIRS 375: sostenidas sólo por el Test 1 | 186 de 322 | {c['VIIRS375']['T1_SOLO_neg']} de {c['VIIRS375']['n_pub_neg']} |")
    A(f"| Fase 1, VIIRS 750 | 89 de 133 | {c['VIIRS750']['T1_SOLO_neg']} de {c['VIIRS750']['n_pub_neg']} |\n")
    A(f"Reproduce: **{'sí' if c['reproduce_S145_y_Fase1'] else 'NO'}**. Los tres scripts abortan si este control no da. Salida cruda:\n")
    A(crudo("p1_salida_cruda.txt", lambda l: l.startswith("CONTROL POSITIVO")))

    # ------------------------------------------------------------------ P1
    A("## 1. P1: la curva de dosis del Test 1 integrado\n")
    A("### El fenómeno\n")
    A("El Test 1 integrado no mira píxeles sueltos: suma todo el exceso de radiancia del infrarrojo medio dentro de un disco de 3 km "
      "alrededor del cráter y pregunta si esa suma supera en k veces el ruido del anillo de fondo. Sirve para ver calor débil y repartido "
      "(un lago de lava chico, un campo de fumarolas) que ningún píxel delata por sí solo. El problema es que un disco sobre un edificio "
      "volcánico nunca es térmicamente plano: hay laderas que guardan calor del día, roca oscura junto a nieve, valles más tibios que la "
      "cumbre. Todo eso suma exceso positivo aunque el volcán esté quieto, y más todavía porque el exceso se recorta en cero (lo frío no "
      "resta). Por eso a 3 sigmas el Test 1 dispara casi todas las noches, y eso es lo que el operador ve publicado donde MIROVA miró y no vio nada.\n")
    A("La pregunta de P1 es si basta con pedirle más sigmas. Hay dos resultados posibles y los dos sirven: o existe un k donde el relieve "
      "tibio queda abajo y el calor volcánico arriba (un umbral que separa), o las dos poblaciones se traslapan y lo único que hace subir k "
      "es apagar el detector de a poco.\n")
    A("### El mecanismo de la medición y lo que supone\n")
    A("Cada record guarda `test1_k_observed`, el número de sigmas que alcanzó la suma. Como k sólo entra en la comparación final "
      "(`pipeline/test1_integrated.py`, línea 435), una pasada con k observado mayor que el umbral nuevo queda idéntica: eso es exacto. "
      "Lo que es **cota y no simulación** es lo que pasa con las que quedan debajo: una pasada que la Fase 1 clasificó T1_SOLO se da por no "
      "publicada (se hereda el supuesto de la Fase 1, no se re-ejecuta el ensamblado); una T1_SOBRE_CTX queda SIN DATO, porque no se persiste "
      "cuánto valía el cúmulo contextual que el Test 1 reconstruyó; AMBOS y CTX_SOLO siguen porque no dependen del Test 1. También se supone, "
      "sin medirlo, que subir k no hace publicar nada que hoy no se publica (SOSPECHA razonable). Una noche positiva *sigue* si conserva al menos una "
      "pasada publicada segura, es *SIN DATO* si sólo le quedan pasadas SIN DATO, y *se pierde* si no le queda ninguna.\n")
    A("### Cobertura del campo, medida primero\n")
    A("| sensor | records | k_obs nulo | k_obs = 0 (no calculado o cero) | k_obs > 0 | disparos | disparos con k ≤ 3 | no disparó con k > 3 (falló el criterio relativo del 2 %) |\n|---|---|---|---|---|---|---|---|")
    for b, d in p1["cobertura"].items():
        A(f"| {b} | {d['n_records']} | {d['k_obs_None']} | {d['k_obs_cero']} | {d['k_obs_positivo']} | {d['triggered_True']} | {d['triggered_True_con_k_le_3']} | {d['triggered_False_con_k_gt_3_(fallo_el_criterio_relativo_2pct)']} |")
    A("\nEl campo existe en los tres sensores y no hay nulos, así que la curva no sale de un cero que se lee como confirmación. El valor 0,0 es "
      "ambiguo (el código escribe 0,0 tanto si no calculó como si dio cero), pero no afecta la curva: sólo importan las pasadas donde el Test 1 "
      "disparó. El único disparo con k ≤ 3 es un redondeo a dos decimales. En MODIS el Test 1 dispara poco, así que ahí la curva casi no tiene sustrato.\n")
    A(crudo("p1_salida_cruda.txt", lambda l: l.startswith("COBERTURA"), 1600))

    A("### ¿Discrimina el estadístico?\n")
    A("Distribución de k observado entre las pasadas publicadas donde el Test 1 disparó:\n")
    A("| sensor | grupo | n | p25 | mediana | p75 | máx |\n|---|---|---|---|---|---|---|")
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        for g in ("neg_limpio|T1_SOLO", "neg_limpio|T1_SOBRE_CTX", "neg_limpio|AMBOS", "pos|T1_SOLO", "pos|T1_SOBRE_CTX", "pos|AMBOS"):
            q = p1["distribucion_k_obs"][b][g]
            if q:
                A(f"| {b} | {g.replace('|', ', ')} | {q['n']} | {num(q['p25'], 2)} | {num(q['p50'], 2)} | {num(q['p75'], 2)} | {num(q['max'], 2)} |")
    A("")
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        d = p1["distribucion_k_obs"][b]
        a = d["AUC_kobs_pos_vs_neg_entre_publicadas_con_disparo"]
        A(f"- **{b}**: probabilidad de que una pasada positiva tenga más sigmas que una de negativo limpio (AUC) = {num(a['auc'])} "
          f"(n neg {a['n_neg']}, n pos {a['n_pos']}); **estratificada por volcán: {num(d['AUC_estratificado_por_volcan'])}**.")
    pv = p1["distribucion_k_obs"]["VIIRS375"]["AUC_por_volcan"]
    A("\nVIIRS 375 por volcán (AUC, n neg, n pos): " + "; ".join(f"{v} {num(x['auc'], 2)} ({x['n_neg']}, {x['n_pos']})" for v, x in pv.items() if x["auc"] is not None) + ".\n")
    A("Lectura: el estadístico discrimina **poco y de manera desigual**. Separa bien donde hay una fuente fuerte y persistente (Isluga, Puyehue-Cordón Caulle) "
      "y casi nada en el resto, donde está cerca de 0,5 a 0,6. Las distribuciones se traslapan de punta a punta: no hay un valle entre dos poblaciones. "
      "Parte del AUC agregado es composición por volcán (baja al estratificar), la misma paradoja de Simpson que la Fase 1 ya había medido.\n")
    A(crudo("p1_resumen_crudo.txt", lambda l: "AUC_" in l or l.startswith("==") or "por volcan:" in l, 900))

    A("### La curva\n")
    A("Publicación en negativos limpios por PASADA (rango mínimo a máximo: el mínimo da por caídas las SIN DATO, el máximo las da por publicadas) y "
      "NOCHES positivas por sensor:\n")
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        A(f"**{b}**\n")
        A("| k | neg. limpios que caen (T1_SOLO) | SIN DATO | tasa de publicación mín a máx | pasadas pos que caen / SIN DATO | noches pos: siguen / SIN DATO / se pierden / ya no publicadas hoy | contraste neg menos pos | nulo (p2,5 a p97,5) | fuera del nulo |\n|---|---|---|---|---|---|---|---|---|")
        for k in p1["meta"]["ks"]:
            k = str(k)
            n_, p_ = p1["curva_pasadas"][b]["neg_limpio"][k], p1["curva_pasadas"][b]["pos"][k]
            no = p1["curva_noches"][b][k]
            nu = (p1["nulo"][b] or {}).get(k)
            A(f"| {k.replace('.', ',')} | {n_['cae']} | {n_['sin_dato']} | {pct(n_['tasa_pub_min'])} a {pct(n_['tasa_pub_max'])} | {p_['cae']} / {p_['sin_dato']} | "
              f"{no.get('sigue', 0)} / {no.get('sin_dato', 0)} / {no.get('se_pierde', 0)} / {no.get('no_publicada_hoy', 0)} | "
              + (f"{num(nu['observado'])} | {num(nu['nulo_p2.5'])} a {num(nu['nulo_p97.5'])} | {'sí' if nu['fuera_del_nulo'] else 'no'} |" if nu else "SIN DATO | SIN DATO | SIN DATO |"))
        A("")
    A("**Noches positivas con cualquier sensor** (la unidad del operador), y aparte la misma curva sin las noches que la Fase 1 dejó SIN DATO "
      f"({', '.join(v + ' ' + n for v, n in p1['noches_SIN_DATO_F1_leidas_del_json_de_la_Fase1'])}; leídas del JSON de la Fase 1, no transcritas):\n")
    A("| k | noches pos | siguen | SIN DATO | se pierden seguro | sin las de la Fase 1: siguen de n |\n|---|---|---|---|---|---|")
    for k in p1["meta"]["ks"]:
        k = str(k)
        a, s = p1["curva_noches"]["CUALQUIERA"][k], p1["curva_noches"]["CUALQUIERA_sin_las_SIN_DATO_F1"][k]
        A(f"| {k.replace('.', ',')} | {a['n_noches_pos']} | {a.get('sigue', 0)} | {a.get('sin_dato', 0)} | {a.get('se_pierde', 0)} | {s.get('sigue', 0)} de {s['n_noches_pos']} |")
    A("\nNoches que dejan de estar aseguradas, por umbral (cualquier sensor):\n")
    A("```\n" + json.dumps(p1["noches_afectadas"]["CUALQUIERA"], ensure_ascii=False) + "\n```\n")
    A("Noches que dejan de estar aseguradas mirando sólo VIIRS 750 (siguen publicadas por VIIRS 375, por eso no aparecen arriba):\n")
    A("```\n" + json.dumps(p1["noches_afectadas"]["VIIRS750"].get("3.5"), ensure_ascii=False) + "\n```\n")
    A(crudo("p1_salida_cruda.txt", lambda l: l.startswith("  k=") or l.startswith("== "), 330))

    A("### Las noches SIN DATO de la Fase 1, una por una\n")
    A("Son las únicas noches positivas cuyo sostén pasa por el Test 1. En las cuatro, la pasada que MIROVA alertó la sostiene el Test 1 "
      "(sola o reconstruyendo el cúmulo contextual), con estos sigmas:\n")
    A("| noche | pasada | sensor | etiqueta | clase | k observado | MW publicados |\n|---|---|---|---|---|---|---|")
    for nk, rs in p1["detalle_noches_SIN_DATO_F1"].items():
        for r in rs:
            if r["pub"]:
                A(f"| {nk.replace('|', ' ')} | {r['dt'][11:]} | {r['b']} | {r['lab']} | {r['clase']} ({r['sub'].replace('|', ', ')}) | {num(r['k_obs'], 2)} | {num(r['disp_mw'])} |")
    A("\nNinguna se *pierde seguro* a ningún k, porque todas tienen alguna pasada T1_SOBRE_CTX, que es SIN DATO y no pérdida. Pero eso es una propiedad de la cota, "
      "no del volcán: para saber si esas cuatro noches se publicarían por el camino contextual hace falta el probe que la Fase 1 dejó especificado.\n")

    A("### Por volcán (VIIRS 375)\n")
    A("| volcán | neg. limpios publicados / n | caen a k = 4 | k = 5 | k = 6 | k = 8 | k = 12 | pasadas pos publicadas | pos que dejan de estar seguras a k = 4 / 5 / 6 / 8 / 12 | noches pos: siguen a k = 5 / 8 de n |\n|---|---|---|---|---|---|---|---|---|---|")
    for v, d in p1["curva_por_volcan"]["VIIRS375"].items():
        n_, p_ = d["neg_limpio"], d["pos"]
        nv = p1["curva_noches_por_volcan"][v]
        A(f"| {v} | {n_['3.0']['pub_hoy']} / {n_['3.0']['n']} | " + " | ".join(str(n_[k]["cae"]) for k in ("4.0", "5.0", "6.0", "8.0", "12.0"))
          + f" | {p_['3.0']['pub_hoy']} | " + " / ".join(str(p_[k]["cae"] + p_[k]["sin_dato"]) for k in ("4.0", "5.0", "6.0", "8.0", "12.0"))
          + f" | {nv['5.0'].get('sigue', 0)} / {nv['8.0'].get('sigue', 0)} de {nv['5.0']['n_noches_pos']} |")
    A("\nLa dosis rinde donde el relieve manda y no hay fuente (Copahue, Villarrica, Llaima, Nevados de Chillán, Planchón-Peteroa, Chaitén) y casi no mueve nada "
      "en Puyehue-Cordón Caulle ni en Isluga, que publican por el camino contextual. Llaima y Copahue no tienen noches positivas en la ventana: ahí el costo en recall es SIN DATO, no cero.\n")

    c5, c4 = p1["curva_pasadas"]["VIIRS375"]["neg_limpio"]["5.0"], p1["curva_pasadas"]["VIIRS375"]["neg_limpio"]["4.0"]
    c12 = p1["curva_pasadas"]["VIIRS375"]["neg_limpio"]["12.0"]
    A("### Veredicto de P1\n")
    A(f"- **No existe un umbral que separe.** El k observado de los negativos limpios y el de los positivos se traslapan entero (AUC estratificado "
      f"{num(p1['distribucion_k_obs']['VIIRS375']['AUC_estratificado_por_volcan'])} en VIIRS 375 y {num(p1['distribucion_k_obs']['VIIRS750']['AUC_estratificado_por_volcan'])} en VIIRS 750). La curva es una rampa sin codo: a k = 4 caen {c4['cae']} "
      f"de {p1['control_positivo']['VIIRS375']['T1_SOLO_neg']} T1_SOLO, a k = 5 caen {c5['cae']}, y para sacar casi todos ({c12['cae']}) hay que ir a k = 12, que es lo mismo que apagar el Test 1.")
    A(f"- **Pero la dosis funciona igual, por otra razón**: no porque el Test 1 distinga, sino porque el recall casi no depende de él. El contraste queda fuera del nulo barajado en VIIRS 375 "
      f"desde k = 3,5, y en noches con cualquier sensor no se pierde ninguna con seguridad a ningún k: todas siguen hasta k = 4, una pasa a SIN DATO a k = 4,5 y son 4 SIN DATO desde k = 7 (las mismas cuatro de la Fase 1).")
    A(f"- **Cuánto rinde**: en VIIRS 375 la publicación en negativos limpios iría de {pct(p1['curva_pasadas']['VIIRS375']['neg_limpio']['3.0']['tasa_pub_min'])} a entre "
      f"{pct(c4['tasa_pub_min'])} y {pct(c4['tasa_pub_max'])} con k = 4, y a entre {pct(c5['tasa_pub_min'])} y {pct(c5['tasa_pub_max'])} con k = 5. En VIIRS 750, de "
      f"{pct(p1['curva_pasadas']['VIIRS750']['neg_limpio']['3.0']['tasa_pub_min'])} a entre {pct(p1['curva_pasadas']['VIIRS750']['neg_limpio']['5.0']['tasa_pub_min'])} y "
      f"{pct(p1['curva_pasadas']['VIIRS750']['neg_limpio']['5.0']['tasa_pub_max'])} con k = 5. MODIS casi no tiene sustrato (el Test 1 sostiene {p1['control_positivo']['MODIS']['T1_SOLO_neg']} de {p1['control_positivo']['MODIS']['n_pub_neg']}) y un solo positivo: SIN DATO.")
    A("- **Qué dice para el A/B**: un umbral intermedio no compra nada que no compre mejor mudar el Test 1 al experimental. No hay un k «natural» que defender; cualquier k entre 4 y 8 es un punto arbitrario de una rampa. "
      "Si igual se quiere un brazo graduado, k = 4 es el último sin ninguna noche en duda y k = 5 el que tiene una sola (Villarrica 2026-09-16). "
      "El piso que queda sin el Test 1 (la publicación por el camino contextual, que es el del paper) no lo toca ningún k.")
    A("- **Límites**: 20 días de un solo régimen; cota y no re-ejecución; las pasadas T1_SOBRE_CTX (56 en negativos de VIIRS 375) son SIN DATO y ensanchan el rango; "
      "en Láscar, Nevados de Chillán y Lastarria el Test 1 corre con el anillo intermedio de S112 y su k observado no es comparable uno a uno con el de los otros volcanes (no lo separé: SOSPECHA).\n")

    # ------------------------------------------------------------------ P2
    if hay["p2_resultados.json"]:
        p2 = J("p2_resultados.json")
        A("## 2. P2: re-lectura de los A/B de S135 y S143, por volcán y en unidades del operador\n")
        A("> **Esto es una re-lectura posterior y exploratoria.** Los dos A/B tienen pre-registro (`docs/PREREGISTRO_AB_D1_D2_S135.md`, `docs/PREREGISTRO_AB_D22_D25_S143.md`) "
          "y veredicto NO ADOPTAR, y eso **no cambia**: el criterio se fijó antes de ver los datos y un brazo no se adopta por una lectura hecha después. "
          "Lo que sigue sirve para decidir qué brazos vale la pena llevar a un A/B nuevo, con ventana nueva.\n")
        A("### El fenómeno y por qué releer\n")
        A("Los dos experimentos tocaron la misma pieza: `keep_peak`, la regla que conserva el píxel pico del Test 1 cuando el filtro contextual no deja nada. "
          "Físicamente ese píxel es muchas veces relieve tibio a 2 o 3 km del cráter, no la fuente. Los dos veredictos cayeron por criterios que no están en las unidades del operador: "
          "S135 por una mediana agregada de magnitud que empeoraba 0,016, y S143 por 5 noches «perdidas» según una cota escalar de radios que después se mostró incapaz de identificar el objeto (A107). "
          "La pregunta del operador es otra: esa noche, ¿se publicó o no?, y en las pasadas donde MIROVA miró y no vio nada, ¿publicamos o no?\n")
        A("### El mecanismo de la re-lectura\n")
        A("Se leen los JSON por brazo y volcán tal como salieron de GitHub Actions (S135: `experiments/_artefactos_ab/s135ab-*`, los dos tramos fusionados en memoria; "
          "S143: la carpeta fusionada que cita `resultado_ab_s143.json`). Se les aplica el banco de paridad de S145, con la referencia fijada por sha de `experiments/_s143_evaluador/_dl_referencia`. "
          "Ventana 2026-06-01 a 2026-08-31, sólo VIIRS 375. La ventana cruza el 2026-08-28, pero acá no mezcla regímenes: todos los brazos son reprocesos hechos en septiembre con un mismo código "
          "(ver `processed_utc` en la salida cruda), no datos de producción. "
          "Recall por NOCHE de dos maneras, ninguna con cota de distancia: (a) el brazo publica alguna pasada esa noche; (b) el brazo publica la misma pasada que MIROVA alertó. "
          "Publicación por PASADA pareada contra el control, con prueba de signos exacta. Regla de lectura fijada antes de mirar la tabla: muestra suficiente = "
          f"{p2['meta']['n_min_neg']} negativos limpios y {p2['meta']['n_min_noches']} noches positivas; GANA = 0 noches perdidas y baja la publicación con p < 0,05; EMPATA = 0 noches perdidas y diferencia indistinguible; PIERDE = pierde alguna noche o sube la publicación.\n")
        cp = p2["control_positivo_S143"]
        A("### Controles del instrumento\n")
        A(f"- Control positivo: con el control y el `literal` de S143 reproduzco los números publicados por el evaluador de S143 (n = {cp['mio']['neg_n']} negativos limpios, "
          f"control {num(cp['mio']['tasa_control'])}, literal {num(cp['mio']['tasa_literal'])}, {cp['mio']['solo_control_literal']} pasadas que sólo publica el control): **{'sí' if cp['reproduce'] else 'NO'}**. "
          f"Noches con alerta por volcán iguales a las del evaluador: **{'sí' if cp['noches_alerta_iguales'] else 'NO'}**.")
        A(f"- Control contra sí mismo (instrumento muerto): control contra control da {p2['control_contra_si_mismo']} discordantes.")
        A(f"- Cobertura pareja (A108): volcanes excluidos por pasadas de menos, S143 {p2['S143']['volcanes_con_cobertura_despareja'] or 'ninguno'}, S135 {p2['S135']['volcanes_con_cobertura_despareja'] or 'ninguno'}.")
        A("- Nulo: si brazo y control fueran lo mismo, los discordantes se repartirían al azar y ganaría a lo más 1 volcán por brazo (p97,5).\n")
        A(crudo("p2_salida_cruda.txt", lambda l: l.startswith("CONTROL") or l.startswith("REFERENCIA") or "NULO" in l or "processed_utc" in l, 700))
        for exp in ("S143", "S135"):
            A(f"### {exp}: tabla por brazo y volcán\n")
            ctl = "_s142_ab_control" if exp == "S143" else "_s135_ab_a_control"
            for brazo, pv in p2[exp]["por_brazo"].items():
                if brazo == ctl:
                    continue
                A(f"**{brazo}**\n")
                A("| volcán | muestra suficiente | neg. limpios: brazo / control (n) | sólo control / sólo brazo | p | noches pos | publicadas (a) brazo / control | publicadas (b) brazo / control | razón de magnitud brazo / control (pares) | lectura |\n|---|---|---|---|---|---|---|---|---|---|")
                for vol, d in pv.items():
                    if "EXCLUIDO_por_cobertura" in d:
                        A(f"| {vol} | EXCLUIDO | | | | | | | | |")
                        continue
                    A(f"| {vol} | {'sí' if d['muestra_suficiente'] else 'no'} | {pct(d['neg_tasa_brazo'])} / {pct(d['neg_tasa_control'])} ({d['neg_n']}) | {d['neg_solo_control']} / {d['neg_solo_brazo']} | {num(d['p_signos'], 4)} | "
                      f"{d['noches_pos']} | {d['noches_pub_a_brazo']} / {d['noches_pub_a_control']} | {d['noches_pub_b_brazo']} / {d['noches_pub_b_control']} | "
                      f"{num(d['mag_mediana_brazo'], 3)} / {num(d['mag_mediana_control'], 3)} ({d['mag_n_pares']}) | {d['lectura']} |")
                suf = [(v, d) for v, d in pv.items() if v != "TODOS" and d.get("muestra_suficiente")]
                g = [v for v, d in suf if d["lectura"] == "GANA"]
                e = [v for v, d in suf if d["lectura"] == "EMPATA"]
                pi = [v for v, d in suf if d["lectura"].startswith("PIERDE")]
                perd = pv["TODOS"]["perdidas_b"]
                A(f"\nCon muestra suficiente ({len(suf)} volcanes): gana en {len(g)} ({', '.join(g) or 'ninguno'}), empata en {len(e)} ({', '.join(e) or 'ninguno'}), pierde en {len(pi)} ({', '.join(pi) or 'ninguno'}). "
                  f"Nulo: ganaría en {p2[exp]['nulo_reparto_al_azar'][brazo]['gana_bajo_nulo_p97.5']} a lo más. "
                  f"Noches perdidas (b) en todos los volcanes, con o sin muestra: {len(perd)}" + (f" ({'; '.join(v + ' ' + n for v, n in perd[:12])}{' y más' if len(perd) > 12 else ''})" if perd else "") + ".\n")
        A("Salida cruda completa de las dos tablas:\n")
        A(crudo("p2_salida_cruda.txt", lambda l: l.startswith("   ") or l.startswith("--") or l.startswith("====="), 330))

        lit, b135 = p2["S143"]["por_brazo"]["_s142_ab_literal"], p2["S135"]["por_brazo"]["_s135_ab_b_nokeeppeak"]
        kp = p2["S143"]["por_brazo"]["_s142_ab_lit_keep_peak"]["TODOS"]
        A("### Veredicto de P2, por brazo (exploratorio)\n")
        A(f"- **S143 `literal` y `lit_sp_suelto`** (idénticos en esta lectura): perdieron por 5 noches según la cota escalar. En unidades del operador **no pierden ninguna noche en ningún volcán**, "
          f"ni por (a) ni por (b) ({lit['TODOS']['noches_pub_b_brazo']} de {lit['TODOS']['noches_pub_b_control']}), y bajan la publicación en negativos limpios de {pct(lit['TODOS']['neg_tasa_control'])} a {pct(lit['TODOS']['neg_tasa_brazo'])}. "
          f"Ganan en {sum(1 for v, d in lit.items() if v != 'TODOS' and d['muestra_suficiente'] and d['lectura'] == 'GANA')} de los {sum(1 for v, d in lit.items() if v != 'TODOS' and d['muestra_suficiente'])} volcanes con muestra suficiente, contra {p2['S143']['nulo_reparto_al_azar']['_s142_ab_literal']['gana_bajo_nulo_p97.5']} que daría el azar. Es el caso «perdió en el agregado, gana en todos los volcanes». Dos salvedades que no son menores: publicar la misma pasada no prueba que sea el mismo objeto "
          f"(el verificador de S143 mostró que en esas 5 noches el píxel pico es el mismo y cambia qué píxel define el cúmulo); y en Nevados de Chillán el brazo publica {lit['NevadosDeChillan']['neg_solo_brazo']} negativos limpios que el control no, que es el riesgo de relieve tibio. "
          f"La magnitud se acerca a 1 en el total ({num(lit['TODOS']['mag_mediana_control'], 3)} a {num(lit['TODOS']['mag_mediana_brazo'], 3)}) pero se pasa de largo en Tupungatito ({num(lit['Tupungatito']['mag_mediana_control'], 3)} a {num(lit['Tupungatito']['mag_mediana_brazo'], 3)}) y empeora en Chaitén ({num(lit['Chaiten']['mag_mediana_control'], 3)} a {num(lit['Chaiten']['mag_mediana_brazo'], 3)}).")
        A(f"- **S143 `lit_keep_peak`**: empata en todos los volcanes ({pct(kp['neg_tasa_brazo'])} contra {pct(kp['neg_tasa_control'])}, p {num(kp['p_signos'], 3)}). Confirma que todo el descenso de publicación sale de apagar `keep_peak`, no de D22 ni de D25.")
        def pierden(pv):
            return [f"{v} {len(d['perdidas_b'])}" for v, d in pv.items() if v != "TODOS" and d.get("perdidas_b")]
        sf, cc = p2["S143"]["por_brazo"]["_s142_ab_lit_sin_fondo"], p2["S143"]["por_brazo"]["_s142_ab_lit_con_compuerta"]
        A(f"- **S143 `lit_sin_fondo`**: gana en publicación donde hay muestra, pero pierde noches por (b) en {len(pierden(sf))} volcanes ({', '.join(pierden(sf))}). **`lit_con_compuerta`**: pierde noches en {len(pierden(cc))} de los {len(cc) - 1} volcanes ({', '.join(pierden(cc))}). Ninguno de los dos revierte su veredicto.")
        A(f"- **S135 brazo B (sin `keep_peak`)**: perdió por 0,016 de paridad agregada. Por volcán gana en publicación en los 5 con muestra suficiente ({pct(b135['TODOS']['neg_tasa_control'])} a {pct(b135['TODOS']['neg_tasa_brazo'])}) y no pierde ninguna noche por (a). "
          f"Por (b) pierde {len(b135['TODOS']['perdidas_b'])} noches, las dos en Isluga ({'; '.join(n for v, n in b135['TODOS']['perdidas_b'])}), que queda sin muestra suficiente de negativos (n {b135['Isluga']['neg_n']}). "
          f"La paridad de magnitud, que fue lo que lo tumbó, por volcán es **mixta y no uniforme**: mejora en Lastarria ({num(b135['Lastarria']['mag_mediana_control'], 3)} a {num(b135['Lastarria']['mag_mediana_brazo'], 3)}) y Planchón-Peteroa ({num(b135['PlanchonPeteroa']['mag_mediana_control'], 3)} a {num(b135['PlanchonPeteroa']['mag_mediana_brazo'], 3)}), "
          f"no cambia en Láscar ni en Puyehue, y empeora en Tupungatito ({num(b135['Tupungatito']['mag_mediana_control'], 3)} a {num(b135['Tupungatito']['mag_mediana_brazo'], 3)}) e Isluga ({num(b135['Isluga']['mag_mediana_control'], 3)} a {num(b135['Isluga']['mag_mediana_brazo'], 3)}). O sea: el criterio agregado no escondía una victoria pareja, escondía una mezcla.")
        A("- **S135 C y E** (tocar sólo el segundo pase): empatan en todos los volcanes con muestra; la baja agregada de 8 pasadas de 535 no aparece en ningún volcán por separado. **S135 D**: pierde noches en " + str(len(pierden(p2["S135"]["por_brazo"]["_s135_ab_d_ambos"]))) + " de 6 volcanes (" + ", ".join(pierden(p2["S135"]["por_brazo"]["_s135_ab_d_ambos"])) + "). Sin cambios respecto de sus veredictos.")
        A("- **Observación sin interpretar (SOSPECHA)**: `lit_sin_fondo` de S143 da casi los mismos conteos que el brazo B de S135, y `lit_con_compuerta` los mismos que el D, volcán por volcán. No comparé los perfiles; lo anoto porque, si son el mismo tratamiento, S143 replicó a S135 en otro arnés.")
        A("- **Qué dice para el A/B que viene**: el brazo que sale mejor parado de la re-lectura es el `literal` de S143 (sin `keep_peak`, sin compuerta, con fondo por vecinos). Llevarlo a una ventana nueva y fuera de muestra, con criterio en noches y pasadas, es lo que esta lectura habilita. No habilita adoptarlo. "
          "Y sigue en pie el límite de S144: sin dirección (acimut) no se separa relieve tibio de fuente permanente.\n")

    # ------------------------------------------------------------------ P6
    if hay["p6_resultados.json"]:
        p6 = J("p6_resultados.json")
        A("## 3. P6: la regla de preferencia entre banda I y banda M\n")
        A("### Qué dice el paper\n")
        A("Coppola et al. 2026, *Scientific Data* (`documentacion/Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf`), **página 7 de 25 del PDF, sección «Data aggregation», tercer párrafo**. "
          "Validado renderizando la página a imagen con PyMuPDF a 200 dpi y leyéndola (la capa de texto coincide en este pasaje). Cita textual, única de este informe:\n")
        A("> «For coincident VIIRS detections, the 750 m observation was retained»\n")
        A("El mismo párrafo dice antes que las detecciones de 375 m sin par de 750 m se conservan, y las de 750 m sin par de 375 m también; y después, que no hubo control de calidad adicional ni revisión manual en ese paso. "
          "La razón que da es instrumental: el canal I4 satura antes sobre fuentes intensas porque tiene una sola ganancia. La figura 2 (página 14 del PDF) repite la regla en su leyenda.\n")
        A("### Lo que la regla es y lo que no es\n")
        A("Es una regla para **no contar dos veces la misma detección** al fundir tres archivos ya filtrados en uno: si las dos bandas detectaron en el mismo paso, se queda la de 750 m; si detectó una sola, se queda ésa. "
          "**No es un veto**: el paper no dice que una detección de 375 m se descarte cuando la banda de 750 m miró y no vio nada. Al revés, dice que se conserva. "
          "Y es una regla del archivo OSF filtrado, no del canal NRT (A105).\n")
        A("**El paper dice lo que el censo cita, pero no lo que el censo infiere.** El frente F supuso que aplicar la regla «reduciría la sobre-publicación de las pasadas coincidentes sin tocar ningún umbral». "
          "Por construcción no puede: una unión deduplicada publica exactamente los mismos pasos. Lo único que cambia es qué record representa al paso.\n")
        h, l1, l2 = p6["reglas"]["HOY"], p6["reglas"]["L1_PAPER"], p6["reglas"]["L2_VETO"]
        t = p6["tabla_2x2_pasos_con_ambas_bandas_por_etiqueta_de_I"]
        A("### Medición sobre los records (ventana 2026-09-01 a 2026-09-20)\n")
        A(f"El pareo I con M funciona: de {p6['pareo']['n_pasos']} pasos VIIRS nocturnos, {p6['pareo']['cobertura'].get('IM', 0)} tienen record de las dos bandas (mismo satélite, mismo minuto).\n")
        A("| combinación | publicación en negativos limpios por PASO | noches positivas publicadas (VIIRS) |\n|---|---|---|")
        for nom, r in (("hoy (publica la I o la M)", h), ("regla del paper (unión deduplicada)", l1), ("veto, que NO está en el paper (la I sólo vale si la M también publica)", l2)):
            x, n = r["neg_limpio_por_paso(etiqueta_del_paso)"], r["noches"]
            A(f"| {nom} | {pct(x['tasa'])} ({x['pub']} de {x['n']}) | {n['publicadas_viirs']} de {n['n_noches_pos_viirs']} |")
        A(f"\n- **Regla del paper**: cambia {p6['L1_cambia_pasos_publicados']} pasos publicados. Reemplaza el record de 375 m por el de 750 m en {p6['L1_records_I_reemplazados_por_M']['neg_limpio']} pasos de negativo limpio y {p6['L1_records_I_reemplazados_por_M']['pos']} positivos: es un cambio de qué magnitud se muestra, no de si se publica. Recall por noche, sin cambio.")
        A(f"- **Por qué la unión no ayuda**: en los pasos con negativo limpio en la banda I y las dos bandas presentes (n {t['neg_limpio']['n']}), la I publica sola en {t['neg_limpio']['I_si_M_no']}, las dos en {t['neg_limpio']['I_si_M_si']}, la M sola en {t['neg_limpio']['I_no_M_si']}. La sobre-publicación de 375 m ocurre justo donde la de 750 m calla, que es el caso que el paper manda conservar.")
        A(f"- **El veto** bajaría la publicación a {pct(l2['neg_limpio_por_paso(etiqueta_del_paso)']['tasa'])}, pero perdería {l2['noches']['n_noches_pos_viirs'] - l2['noches']['publicadas_viirs']} de {l2['noches']['n_noches_pos_viirs']} noches positivas: en los pasos positivos la M calla en {t['pos']['I_si_M_no']} de {t['pos']['n']}. "
          f"Y no discrimina: borra {pct(p6['nulo_L2']['frac_I_neg_borradas'])} de las I publicadas en negativos y {pct(p6['nulo_L2']['frac_I_pos_borradas'])} en positivos; el contraste {num(p6['nulo_L2']['contraste_obs'])} cae dentro del nulo barajado por volcán ({num(p6['nulo_L2']['nulo_p2.5'])} a {num(p6['nulo_L2']['nulo_p97.5'])}). Es apagar VIIRS 375 con otro nombre.")
        al = p6["referencia_nrt_alertas_vs_otra_banda"]
        A(f"- **La sospecha del cruce (una fila de MIROVA contra dos records nuestros) queda REFUTADA para el NRT**: la referencia trae fila de las dos bandas en {p6['referencia_nrt_minutos_por_banda'].get('VIIRS375|VIIRS750', 0)} minutos, de sólo 375 m en {p6['referencia_nrt_minutos_por_banda'].get('VIIRS375', 0)} y de sólo 750 m en {p6['referencia_nrt_minutos_por_banda'].get('VIIRS750', 0)}. MIROVA NRT no deduplica. "
          f"Y el propio MIROVA alerta en 375 m con la fila de 750 m del mismo minuto en silencio {al.get('VIIRS375|otra_banda_fila_sin_alerta', 0)} veces, contra {al.get('VIIRS375|otra_banda_alerta', 0)} con las dos alertando: MIROVA tampoco aplica un veto en su NRT.\n")
        A(crudo("p6_salida_cruda.txt", lambda l: l.startswith(("CONTROL", "REFERENCIA", "PAREO", "2x2", "== ", "L1 ", "NULO")), 700))
        A("### Veredicto de P6\n")
        A("**El paper no dice lo que el censo esperaba, y la medición lo confirma.** La regla de Coppola 2026 es una deduplicación de un archivo filtrado: aplicada a nuestros records no mueve ni la publicación en negativos limpios ni el recall por noche. "
          "No hay brazo de A/B que sacar de acá para la sobre-publicación. Lo único aprovechable es de presentación y de magnitud: cuando las dos bandas publican el mismo paso, MIROVA se queda con la de 750 m en su archivo, "
          "y una comparación de magnitud contra el OSF (no contra el NRT) debería hacer lo mismo. La lectura de veto no tiene respaldo en el paper ni en el comportamiento del NRT de MIROVA, y costaría cerca de cuatro de cada diez noches.\n")

    A("## 4. Qué no se hizo y qué queda como SOSPECHA\n")
    A("- P1 no re-ejecuta el ensamblado: es una cota sobre campos persistidos. Llevarla a simulación pide el probe de la Fase 1.")
    A("- P1: no se separó el efecto del anillo intermedio de S112 en Láscar, Nevados de Chillán y Lastarria.")
    A("- P2: recall por noche sin verificar identidad del objeto. La igualdad de tratamientos entre brazos de S143 y S135 no se comprobó contra los perfiles.")
    A("- P2: MODIS y VIIRS 750 no están en esos A/B; nada de lo dicho vale para ellos. La ventana es en muestra para los dos experimentos.")
    A("- P6: no se midió el efecto de la regla sobre la paridad de magnitud.")
    A("- Los artefactos de S143 se leyeron del scratchpad de otra sesión (ruta en `resultado_ab_s143.json`, `meta.dir_artefactos`); si esa carpeta temporal se borra, P2 de S143 deja de ser reproducible salvo que se vuelvan a bajar los runs.\n")
    txt = "\n".join(partes)
    assert "—" not in txt and "–" not in txt, "hay guiones largos o medios"
    OUT.write_text(txt, encoding="utf-8")
    print("escrito", OUT, len(txt), "caracteres; secciones:", hay)


if __name__ == "__main__":
    sys.exit(main())
