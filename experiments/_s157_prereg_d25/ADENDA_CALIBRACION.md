# Adenda al pre-registro de D25 sobre K: la calibración de la magnitud (M)

**SELLADA por Nicolás el 2026-10-20 (D-27), sobre `0a91eb634`** (último commit que tocó esta adenda y
`evaluar_d25.py`). Respuesta textual de Nicolás, registrada por la sesión dueña del loop (S157): «Sello la adenda de
calibración de D25 con el nulo simétrico y la opción A (mejora en al menos dos volcanes).» Rige: §2 entero (sorteo
del signo de d por bloque noche-volcán, tope de 5 % de 200 por cola, colas exigidas según el estrato) y §3 opción A
(un MEJORA cuenta sólo si la mediana de d es negativa en al menos dos volcanes del estrato con 3 pares o más; Chillán
se informa aparte y por volcán). El evaluador corre con `--calibracion simetrica`. Con esto y el sello del
pre-registro (D-26) el candado queda completo; el despacho, desde un tag.

Estado previo: **BORRADOR PARA EL SELLO DE NICOLÁS.** Escrita el 2026-10-20 al armar el candado del §7, antes de correr ningún
brazo. Sin esta decisión el A/B no se despacha: con la calibración tal como quedó escrita en el §5, ni el control
positivo decide. Evidencia: `calibracion_previa_salida.txt` (pares reales de K en disco), `probar_salida.txt` (caso
`sellada`) y el verificador con contexto limpio del evaluador (`verificador_evaluador/INFORME.md`, hallazgos H1, H4, H5
y H6). Todo lo que esta adenda no toca rige como está en `PREREGISTRO.md`.

## 1. Qué falla y por qué

La regla de M decide MEJORA o EMPEORA con un intervalo al 95 % (por bloques de noche-volcán) de la mediana de
d = |log10(D/MIROVA)| − |log10(K/MIROVA)|. El §5 pide además calibrarla: con efectos del tamaño observado y signo al azar,
la regla no puede dar MEJORA o EMPEORA en más del 5 % de 200 repeticiones; si da más, el estrato queda INDECIDIBLE.
Dos cosas hacen que esa calibración no funcione:

1. **El tope es igual al nivel nominal.** Un intervalo al 95 % de dos colas se equivoca, por diseño, 5 % de las veces
   (2,5 % por cola). Con 200 repeticiones, una regla perfecta pasa del 5 % el 42 % de las veces (verificador, H5).
2. **El nulo escrito no está centrado en cero.** Cambiar al azar el signo de log10(D/K) **aleja** de MIROVA a las
   pasadas que ya calzan con ella (si K ya está cerca del VRP de MIROVA, moverse para cualquier lado empeora). Ese
   nulo da EMPEORA aunque D25 no haga nada sistemático, y por la misma razón subestima los falsos MEJORA.

**Medido con los pares reales de K** (efecto del tamaño que midió el probe de Chillán):

| | estratos que deciden | calibrados con la regla escrita | calibrados con la simétrica (§2) |
|---|---|---|---|
| V1 | 4 | 1 | 4 (falsos de 0 a 4 % por cola) |
| V2 | 4 | 2 | 4 (falsos de 1 a 3,5 % por cola) |

Y en las pruebas del evaluador, el caso `sellada` (D llevado a mitad de camino hacia MIROVA en VIIRS 750, o sea un
efecto real y grande) sale **INDECIDIBLE** con la regla escrita.

## 2. Lo que se propone (recomendado)

- **Nulo simétrico**: se sortea por bloque noche-volcán el **signo de d** (no el de log10(D/K)). Así el nulo tiene
  mediana cero por construcción y las dos colas se pueden medir por separado.
- **Un tope por cola**: 5 % de 200 por cola (nominal 2,5 %; una regla perfecta falla 1,3 % de las veces).
- **Qué colas se exigen**: las dos donde el estrato decide; sólo EMPEORA donde el estrato sólo bloquea (VIIRS 375 sin
  kernel con cenit sobre 40°, sello §8 a).
- **El sorteo es por bloque noche-volcán**, no por pasada: las pasadas de una noche comparten el estado del volcán y de
  la atmósfera. El texto del §5 decía «el signo al azar» sin decir la unidad; esta adenda la fija.

Implementado como `--calibracion simetrica` en `evaluar_d25.py`; las pruebas de magnitud corren con ella (27 de 27).

## 3. Lo que sigue sin resolverse: cada estrato lo domina un volcán (decisión aparte)

Medido (`calibracion_previa_salida.txt`): VIIRS 750 con cenit sobre 40° es **19 de 23 pares de Chillán** en V1 y **24 de
27 de Láscar** en V2; VIIRS 750 con cenit hasta 40° es 41 de 64 de Láscar en V2. Un efecto de D25 que depende del volcán
(1.14 midió ×1,72 en Isluga y ×2,37 en Tupungatito) es el mismo en todas las noches de ese volcán, y ni el bootstrap ni
la calibración por noche pueden verlo: con el signo sorteado por volcán la misma regla da MEJORA o EMPEORA en 13 a 55 %
de las repeticiones (verificador, H4). O sea, «MEJORA en cada ventana» podría salir sólo de Chillán en V1 y de Láscar en
V2.

- **Opción A (recomendada): un MEJORA cuenta sólo si la mediana de d es negativa en al menos dos volcanes del estrato con
  3 pares o más.** Costo: VIIRS 750 con cenit sobre 40° (el caso de Chillán que motivó todo) no puede dar MEJORA por sí
  solo en ninguna de las dos ventanas, porque tiene un solo volcán con 3 pares. Chillán se informa igual, aparte y por
  volcán. Implementado junto con la simétrica (`--calibracion simetrica`; caso `un_volcan` de las pruebas).
- **Opción B**: un MEJORA de un solo volcán cuenta, pero el veredicto lo dice en su primera línea y la decisión pasa a
  Nicolás.
- **Opción C**: dejarlo como límite escrito en el §9 y que decida la regla tal cual.

## 4. Dos aclaraciones del evaluador (no cambian el criterio, se dejan escritas)

- **«M empeora sin mejora»** no tiene fila en la tabla del §8 d. El sello §8 a dice que un EMPEORA *bloquea* CUMPLE, no
  que sea NO CUMPLE. El evaluador lo informa como **DECIDE NICOLÁS** (verificador, H6).
- **Una suma perdida (P2 PIERDE) es NO CUMPLE aunque algún estrato de M quede INDECIDIBLE**: un M sin decidir no puede
  esconder un error de detección (verificador, H2).

## 5. Para sellar

1. ¿Calibración simétrica por cola (§2) en lugar de la escrita? Recomendado: sí.
2. ¿Dependencia por volcán: opción A, B o C (§3)? Recomendado: A.
3. ¿Las dos aclaraciones del §4? Recomendado: sí.

Con el sello, `CALIB_MODO` de `evaluar_d25.py` pasa a `"simetrica"` (y, si se elige B o C, se ajusta la regla de
volcanes), se vuelven a correr las pruebas y las mutaciones, y un verificador limpio revisa ese cambio antes del tag.
