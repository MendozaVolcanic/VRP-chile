# Lista que verificas (de F1A: 3 de 6 hallazgos; gravedad 3 o más)

Sólo título, ubicación, gravedad y comando del auditor. No abras C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1a\INFORME.md; sí puedes correr sus scripts (están en C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1a).

## 161 (gravedad 5, CONFIRMADO)
- TÍTULO: El instrumento de K da CUMPLE a un placebo: el control con solo triggered_test1 en False (sin ganancia ni desplazamiento) cumple en V1 y en V2 porque la tolerancia de P2 es 0 y el predicado del tablero lee ese flag
- UBICACIÓN: experiments/_s151_prereg_fk_11/evaluar_fk.py:613-641 (ruido 0 con gemelo sin discordancias) y :502-503 (huella que obliga al disfraz); frontend/index.html:1612 (isSummitDetection lee triggered_test1)
- COMANDO DEL AUDITOR: python experiments/_s160_audit/f1a/medir_k2.py <v1_union> <v2a_union> <v2b_union> <salida> <produccion> <v1_rep.json> (casos solo_t1off x110_t1off x120_t1off t1keep)
- SALIDA CRUDA: experiments/_s160_audit/f1a/salidas/medir_k2_resumen.txt; salidas/medir_k/v1_solo_t1off.log; salidas/mecanismo_t1off.txt

## 162 (gravedad 3, CONFIRMADO)
- TÍTULO: El veredicto de K cambia con la version de la referencia: con la tabla sola CUMPLE en V1 y V2; con tabla y OCR en V2 queda PENDIENTE DE REPETICION por Lastarria VIIRS375 2026-04-18 04:42 (1.29 MW solo OCR) y esa repeticion nunca se corrio
- UBICACIÓN: experiments/_s151_prereg_fk_11/evaluar_fk.py:59-62 (solo_tabla fijo por ventana) y REGLA_ADOPCION.md §4.2 (se mira y no decide)
- COMANDO DEL AUDITOR: python experiments/_s151_prereg_fk_11/evaluar_fk.py --ventana V2 --raiz <v2a_union> --raiz <v2b_union> --logs ... --solo-tabla no --ruido-de <v1_rep.json> --out v2_con_ocr.json --produccion <main/data/mirova_equivalent>; luego --combinar v1_rep.json v2_con_ocr.json
- SALIDA CRUDA: experiments/_s160_audit/f1a/salidas/v2_con_ocr.log; salidas/v1_solo_tabla.log

## 163 (gravedad 3, CONFIRMADO)
- TÍTULO: Los datos con que se adopto K no estan en el repo: la rama de V1 trae solo el intento 1 (COBERTURA DESPAREJA) y la union evaluada vivia en un temporal borrado; se rehace con el intento 1 (rama) mas el 3 (artefacto que vence 2027-01-14) y reproduce v1.json; el intento 2 no esta en ninguna parte
- UBICACIÓN: origin/s146-ab/38639658446:experiments/_s146_ab_sin_test1/salidas/38639658446/cobertura.txt; experiments/_s153_fk_v2/README.md:4-6
- COMANDO DEL AUDITOR: git show origin/s146-ab/38639658446:experiments/_s146_ab_sin_test1/salidas/38639658446/cobertura.txt; gh run download 38639658446 -n s146ab-todo; python experiments/_s153_fk_v2/unir_ventana.py <rama> <artefacto> <union>; evaluar_fk.py --ventana V1 ...
- SALIDA CRUDA: experiments/_s160_audit/f1a/salidas/union_v1_i1_i3.txt; salidas/v1_rep.log

## Celdas FALLA de la matriz (se verifican todas, sin importar gravedad: plan §4)

- evaluar_fk.py (regla con que se adopto K; PREREGISTRO.md + REGLA_ADOPCION.md) | fila R6 | el auditor dice FALLA (su razonamiento no se entrega a propósito) | scripts: medir_k.py; medir_k2.py; barajar_r7.py; etiquetar_propio.py; prot_cruce_canales.py; r13_p2_por_volcan.txt; mecanismo_t1off.txt
- evaluar_fk.py (regla con que se adopto K; PREREGISTRO.md + REGLA_ADOPCION.md) | fila R11 | el auditor dice FALLA (su razonamiento no se entrega a propósito) | scripts: medir_k.py; medir_k2.py; barajar_r7.py; etiquetar_propio.py; prot_cruce_canales.py; r13_p2_por_volcan.txt; mecanismo_t1off.txt
- predicado del tablero (frontend/index.html ejecutado con node) | fila R17 | el auditor dice FALLA (su razonamiento no se entrega a propósito) | scripts: mecanismo_t1off.txt
