# -*- coding: utf-8 -*-
"""Agrega las secciones 7 a 12 al INFORME.md (se corre una vez; queda como registro de como se cerro el informe)."""
import re
import sys
from pathlib import Path

p = Path(__file__).resolve().parent / "INFORME.md"
s = p.read_text(encoding="utf-8")

hallazgos = """## 7. Hallazgos propios (ordenados por gravedad; también en `hallazgos.csv`)

### V34-01
- TÍTULO: La regla nueva de P2 no tiene calibración y con pocas noches decide en falso muy por encima del 5 % (24,8 % con el sustrato mínimo de 3 noches correlacionadas)
- SCRIPT:SALIDA: `cobertura_p2.py` : `cobertura_p2_salida_borde.txt` (B5 a B8), `cobertura_p2_salida_2000.txt` (A, B, B3, B4), `cobertura_p2_salida.txt` (todos, n = 400). Código: `experiments/_s157_prereg_d25/evaluar_d25.py:423-446` (`decidir_p2_bloques`); vara: ADENDA_GEMELO.md §5.3 a 5.6.
- QUÉ PASA: las pasadas de una misma noche comparten volcán y atmósfera, por eso el intervalo es por bloques noche-volcán; pero con B noches discordantes todas del mismo lado (probabilidad 2^(1−B) bajo un nulo donde el signo es de la noche) ningún remuestreo de bloques puede cruzar 0 y la regla decide GANA o PIERDE sin que haya efecto. Medido con la función real (10.000 remuestreos, semilla 157), n = 2.000 conjuntos por escenario: signo común por noche con 3 noches 24,8 %, 4 noches 13,0 %, 5 noches 6,5 %, 8 noches 7,0 %, 12 noches 4,0 %; nulo iid con 12 noches × 3 pasadas 6,5 %, noches desiguales 8,7 %, borde de 3 noches 6,5 %. M tiene su nulo que puede fallar (pre-registro §5, D-27) y deja INDECIDIBLE un estrato mal calibrado; P2 con D-34 adopta los mínimos de M (5 pasadas, 3 noches) sin la calibración de M. El código hace exactamente lo que la adenda sella: el defecto es de la regla sellada, no del código.
- CÓMO SE VE EN EL DASHBOARD: invisible (es el evaluador del A/B). Lo que tuerce es la decisión de adoptar D25: un GANA o PIERDE de P2 con 3 a 5 noches discordantes tiene entre 6,5 y 25 % de probabilidad de ser azar.
- CÓMO REPRODUCIRLO: `cd C:\\vrp-trabajo\\s159-evaluador && python experiments/_s159/instrumentos/verificador_d34/cobertura_p2.py 2000 B5,B6,B7,B8` (datos sintéticos; no hay volcán ni pasada real).
- CONFIANZA: CONFIRMADO (medido).
- GRAVEDAD: 3.

### V34-02
- TÍTULO: Bajo un nulo verdadero la variante BLOQUEA apaga CUMPLE en 37 a 48 % de los conjuntos
- SCRIPT:SALIDA: `cobertura_p2.py` : `cobertura_p2_salida_2000.txt` y `_borde.txt`, columna BLOQUEA. Código: `evaluar_d25.py:444-445` y `global_ventana` l. 690-695.
- QUÉ PASA: la variante bloquea cuando el neto puntual queda sobre 0 y el intervalo cruza 0. Sin efecto, el neto cae sobre 0 en casi la mitad de los conjuntos, así que la mitad de los nulos termina en DECIDE NICOLAS por P2 (A 40 %, B 37 %, B3 47 %, B4 48 %, B5 38 %). Es lo que la adenda pide (§5.5 «un neto en contra de D (estimación puntual sobre 0) que no alcance PIERDE da **BLOQUEA**») y Nicolás eligió la variante; lo anoto porque al leer el veredicto un BLOQUEA se puede leer como señal en contra de D cuando bajo el nulo es la moneda.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d34/cobertura_p2.py 2000 A,B,B3,B4`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### V34-03
- TÍTULO: La batería no vigila los números del intervalo de P2 (semilla, remuestreos, nivel 95 %, borde de PIERDE), el tope del 5 % de d′ en la comparación ni el alcance del INDECIDIBLE
- SCRIPT:SALIDA: `mutaciones_propias.py` : `mutaciones_propias_salida.txt` (m01 a m12) y `mutaciones_propias_salida_2.txt` (m13 a m23). Código: `evaluar_d25.py:436-438, 442, 290, 516`.
- QUÉ PASA: siete de 23 mutaciones propias pasan la batería en verde: m05 (semilla de P2 distinta de la de M), m06 (1.000 remuestreos), m15 (percentiles 5 y 95), m08 (`lo >= 0`), m16 (`f_mej <= 2 * MAX_FALSOS_CALIB`: tope 10 % en d′; la prueba de D-32 mira la constante, no la comparación, y las que fuerzan la calibración usan 0,5, que supera cualquier tope), m22 (INDECIDIBLE por d′ aunque d no dé MEJORA), m20 (la marca de validez no llega al `estado`; ésta sí la atrapa `probar_evaluar_d25.py`, caso `sellada_marca`, que el corredor de mutaciones no corre). Hoy el código cumple la adenda en los siete puntos (leído, afirmaciones 3, 4 y 5); lo que falta es el candado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s159/instrumentos/verificador_d34/mutaciones_propias.py` (control + 23; unos 40 min) o `... m15` para reanudar desde una.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### V34-04
- TÍTULO: `mutar_comparador.py` cuenta como ATRAPADA una mutación que falla por aserción en una prueba y por otra excepción en otra
- ARCHIVO:LÍNEA: `experiments/_s159/instrumentos/mutar_comparador.py:151` (`atrapada = bool(por_asercion) and not errores`; la lista `otras` no entra a la condición).
- QUÉ PASA: una mutación que rompa una prueba por aserción y cinco por `KeyError` se cuenta igual que una atrapada limpia; las «otras fallas» se imprimen aparte (l. 166-167), así que se ven, pero el RESUMEN no las descuenta. En la salida sellada y en mi re-corrida hay 0 «otra falla» y 0 errores en las 17, así que hoy no cambia ningún conteo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer la línea; `grep -c "otra falla" experiments/_s159/instrumentos/verificador_d34/mutaciones_rerun.txt` da 0.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1.

### V34-05
- TÍTULO: La fila D-34 de LOOP_OBJETIVOS define la unidad de P2 como «pasadas donde K y D publican distinto» y la adenda sellada como «error en un brazo y no en el otro»; el código sigue a la adenda
- ARCHIVO:LÍNEA: `tasks/LOOP_OBJETIVOS.md:527` contra `experiments/_s157_prereg_d25/ADENDA_GEMELO.md:52-53` y `evaluar_d25.py:418-420`.
- QUÉ PASA: una pasada con etiqueta `sin_info` o `far_ref`, o una alerta protegida, puede publicar distinto en K y D sin ser error de P2, y no entra al neto ni a la lista. La adenda la excluye a propósito («Las pasadas en que los dos aciertan o los dos se equivocan no entran»); la fila del loop es la paráfrasis del coordinador. No es desviación del código; es una diferencia entre las dos redacciones de la vara que conviene dejar dicha antes del tag.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las tres citas.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1.

## 8. SEGUIMIENTOS (fuera de mi eje)
"""
s = s.replace("## 7. Hallazgos propios\n\n(se completan abajo; ver también `hallazgos.csv`)\n\n## 8. SEGUIMIENTOS (fuera de mi eje)\n", hallazgos)

fin = """
## 9. VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

- Signo de P2 (afirmación 8): `evaluar_fk.py:357-367` + `evaluar_d25.py:418-420`, contra PREREGISTRO.md l. 165 y ADENDA_GEMELO.md §5.2; prueba `test_contar_usa_el_signo_de_errores_y_trae_la_lista` (asimétrica, 5 contra 1); mutaciones «signo invertido» (implementador) y m10 atrapadas.
- Misma maquinaria que M: `pesos_bloque` con defaults `N_BOOT=10000, SEMILLA=157` en M (l. 483) y P2 (l. 436); clave de bloque idéntica (l. 420 y 642). Vara: ADENDA_GEMELO.md §5.3.
- `neto == suma_D − suma_K` por construcción (diferencia simétrica sobre la misma definición que `suma_errores`), y el JSON lo autocontrola en `neto_igual_a_suma_D_menos_suma_K` (l. 627).
- GANA/PIERDE/EMPATE/BLOQUEA/SIN SUSTRATO: l. 435-446 contra §5.4 a 5.6; `global_ventana` l. 666-695 y `combinar` l. 962 contra §5.5; pruebas de P2 y mutaciones m01 a m04, m07, m09, m11 a m14 atrapadas.
- Listas informativas (a) y (b): l. 620, 464-469, 628; no deciden (`ver` toma `v_`, l. 624). Vara §5.8.
- D-30 (1), (2), (4) y D-32: l. 113-114, 287-290, 516-524, 699-708, 747, 893-894, 974-975 contra ADENDA_PLACEBO.md §5.1 y §5.3; las 11 mutaciones de la segunda vuelta y D-34 del implementador atrapadas; m17, m18, m19, m21, m23 atrapadas.
- Las tres guardas de H3 existen como pruebas de pytest en `tests/test_evaluar_d25_placebo_s159.py` l. 241, 250, 258 y se recogen en la suite (`pytest.ini` l. 6 `testpaths = tests`).
- Rojo antes: 11 de 11 por `AssertionError` (`rojo_p2_pre_d34.xml`); el guard de la opción A pasa también sobre `63e310af5` (candado, no prueba roja), lo que concuerda con «lo que falta es la guarda» (`verificador_comparador/INFORME.md:115`, TEXTO).
- Reproducibilidad de la calibración de d′: `calib_dprima_1000_rerun.txt` igual a la salida sellada en las 8 filas.
- Default `CALIB_MODO = "simetrica"` (l. 87) y `choices=("sellada", "simetrica")` (l. 989): no hay forma de pasar el flag mal escrito.
- El corredor de mutaciones distingue aserción de caída por el JUnit XML y tiene control sin mutar (l. 119-147); en 17 de 17 no hubo caídas.
- Nada escrito fuera de `verificador_d34/`; `git status` del repo igual antes y después de la suite; sin commit, checkout ni stash; disco C: 13 GB y D: 9,4 GB libres al cierre (sobre el límite de 3 GB).

## 10. SIN DATO

- Cuántas pasadas discordantes y cuántas noches tiene P2 en V1, V2a y V2b (si cae en SIN SUSTRATO, en el borde de 3 a 5 noches donde V34-01 pesa, o con noches suficientes): sale de los datos reales del A/B, prohibidos para mí.
- La curva de poder del comparador (ADENDA_PLACEBO.md §5.2) se midió con 200 repeticiones y la propia adenda dice que con 1.000 «**no se volvió a medir**»: queda declarado, no medido.
- Si los pares reales de K en `pares_k.json` (verificador anterior) siguen siendo los mismos que vería el evaluador hoy: no lo verifiqué; sólo reproduje el número que sale de ese archivo.
- Poder de P2 con efectos reales: sólo sintéticos (C, C2, D, E).

## 11. FUERA DE ALCANCE

- La implementación de D-28 (`b4258040c`): verificada PARCIAL por otro; sólo miré lo que el diff toca.
- `etiquetas_regla`, `armar_tabla.py` (predicado «publica» con node), `suma_errores` y `errores_por_pasada`: F/K, sin cambio en el diff; los usé como vara leída, no los auditi.
- El texto no normativo de las adendas (§1 a §4 de ADENDA_GEMELO.md: gemelo bit a bit, ruido entre máquinas de F/K): no es código.
- El veredicto de D25 y cualquier dato real del A/B.

## 12. Cierre

Hora del servidor al cerrar: Thu, 22 Oct 2026 05:51:57 GMT. Archivos de esta sesión en la CARPETA: `caminos.md` (sellado,
sha256 al pie), `INFORME.md`, `hallazgos.csv`, `_cerrar_informe.py`, `clasificar_junit.py`, `cobertura_p2.py` (+ 3 salidas),
`mutaciones_propias.py` (+ 2 salidas), re-corridas `pruebas_verde_rerun.txt/.xml`, `rojo_p2_pre_d34.txt/.xml`,
`rojo_placebo_pre_d30.txt/.xml`, `mutaciones_rerun.txt`, `probar_rerun.txt` (+ `tmp_probar/`, 527 MB),
`calib_dprima_1000_rerun.txt`, `suite_rerun.txt`, `suite_status_antes.txt`, `suite_status_despues.txt`, y
`raiz_falsa/` (junctions a `scripts/`, `frontend/` y tres `experiments/`, copia de `volcanoes.yaml`, copias de
`evaluar_d25.py` en `7cbee245a` y `63e310af5`).
"""
s = s.replace("## 9. VERIFICADO LIMPIO\n\n## 10. SIN DATO\n\n## 11. FUERA DE ALCANCE\n", "")
s = s.rstrip("\n") + "\n" + fin
p.write_text(s, encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print("guiones largos:", s.count("\u2014"), "| secciones:", re.findall(r"^## \d+\..*$", s, flags=re.M))
