# Enmienda al plazo de la reversión pre-autorizada (MODIS §4.6 y VIIRS D3 §4.6): BORRADOR para Nicolás

Fecha: 2026-11-11. Origen: auditoría S179, decisión 2 (`docs/AUDIT_S179.md` §2), hallazgos 401, DEC-12 (MODIS) y 451
(VIIRS), confirmados por verificador. **DECIDIDO: «Deja el plazo»** (Nicolás, 2026-11-11 06:09 UTC, hora del servidor). No hay enmienda: las dos reglas siguen como se sellaron (29 protegidas o 120 días). Lo que queda de este documento es la medición y las opciones, por si se reabre. Al cerrarse el plazo de MODIS (hacia el 2026-11-19 o 11-20) el «29 de 29» será de Chillán: se lee como fin de la pre-autorización, no como prueba de que la vía no pierde alertas en otros volcanes (§1, §2).

Estado anterior: **BORRADOR, SIN SELLO, ronda 2** (la ronda 1 la leyó un verificador limpio
Fable 5.2: SELLABLE CON CAMBIOS; los seis cambios están aplicados, §7). Ninguna regla cambia hasta tu frase.

## 1. Qué pasa hoy, en lenguaje de volcán

Las dos reglas dejan que una sesión revierta la vía sin preguntarte si la vía calla una alerta de MIROVA de 1 MW o más
(una «protegida»). Esa autorización dura hasta que la guardia junta 29 protegidas o hasta 120 días desde el encendido,
lo que pase primero. El 29 viene de una cuenta de probabilidad: si la vía perdiera una de cada diez alertas, con 29
casos lo veríamos con 95 % de seguridad (1 menos 0,9 elevado a 29 = 0,953).

Esa cuenta supone 29 casos distintos entre sí. Medido, casi nunca lo son: **las 29 se juntan con un solo volcán activo**,
que da varias alertas fuertes por noche. Pasa con Chillán en erupción (2 a 37 MW, cierra en 11 a 18 días) y pasó también
con Láscar en abril y mayo (VIIRS, cierra en 16 a 23 días) y en marzo (MODIS). Una vía que ve bien las alertas fuertes y
repetidas de un volcán no dice nada sobre si ve una anomalía de 1 MW en otro volcán tranquilo, que es la alerta difícil.
Cuando el plazo se cierra así queda escrito «29 de 29, plazo cumplido» con evidencia de un solo volcán.

Hoy (vigilancia viva de MODIS, `data/audit_continuous/guardia_modis_latest.json` en main, generado 2026-11-11 02:15 UTC):
13 de 29, todas de Chillán. Si la erupción sigue igual, MODIS cierra el 2026-11-19 o 11-20; VIIRS, si se enciende,
cerraría en 11 a 13 días.

## 2. Qué haría cada forma de contar (medido)

Instrumento: `ritmo_protegidas.py` (en esta carpeta), sobre el banco de paridad de main `b68779c65`. Cuenta las pasadas
nuestras `pos` con alerta de MIROVA de 1 MW o más (tabla y OCR, como el vigilante) y simula un encendido en cada día del
2026-04-09 al 2026-07-12 (95 encendidos, cada uno con 120 días de datos por delante). Exige record de producción y no de
la guardia: los días que da son una cota inferior. Salida: `ritmo_protegidas_salida.txt`. Control positivo: con
encendido el 2026-11-03, la forma actual cuenta 11 protegidas de Chillán al 2026-11-09, igual que el vigilante real.
El verificador reprodujo la salida idéntica y midió por su cuenta, con un simulador propio, dos ventanas más
(`verificador/diag2_*.txt`): desde el 2026-03-01 y cortando los datos el 2026-09-27, antes de la erupción de Chillán.

**Sin tope (la regla de hoy), ¿con cuántos volcanes se cierra?**

| Ventana de encendidos | Sensor | Cierran por cuenta | Días | Cierres con 20 o más de las 29 de un solo volcán |
|---|---|---|---|---|
| 04-09 a 07-12, datos hasta 11-09 | MODIS | 4 de 95 | mediana 117,5 | 4 de 4 (Chillán) |
| | VIIRS 375 | 63 de 95 | 16 a 30 días en 16 casos; 91 a 119 en 40 | 25 de 63 |
| | VIIRS 750 | 51 de 95 | mínimo 21 | 46 de 51 |
| 04-09 en adelante, datos hasta 09-27 (sin la erupción) | MODIS | 0 de 52 | | |
| | VIIRS 375 | 27 de 52 | mediana 21 | 25 de 27 (Láscar) |
| | VIIRS 750 | 25 de 52 | mediana 42 | 25 de 25 (Láscar) |
| 03-01 en adelante, sin la erupción | MODIS | 14 de 91 | mediana 52 | 14 de 14 (29 de 29 de Láscar) |

Los cierres tardíos de VIIRS 375 (91 a 119 días) son los encendidos de junio y julio que alcanzan la erupción de Chillán,
desde el 2026-09-28.

**Con tope de 10 por volcán** (las 29 tienen que venir de 3 volcanes o más): cierran por cuenta 0, 4 y 0 de 95 (MODIS,
VIIRS 375, VIIRS 750), y 0 de 52 fuera de la erupción en los tres sensores. Los 4 de VIIRS 375 cierran el 10-04 y el
10-05, ya con Chillán. El resto vence a los 120 días. En MODIS, del 03-01 al 11-09 sólo tres volcanes dieron
protegidas (Chillán, Láscar y Villarrica): con el tope suman como mucho 10 + 10 + 1 = 21, así que nunca llegan a 29.

**Una por noche de volcán**: no resuelve nada; en VIIRS 750 sigue cerrando con 2 volcanes.

Otros topes en VIIRS 375 (ventana 04-09 a 07-12): 15 cierra 36 de 95; 12 cierra 11; 10 cierra 4; 8 cierra 0. En MODIS y
VIIRS 750 ningún tope entre 5 y 15 cierra.

## 3. Opciones

| | Qué cambia | Efecto | Costo |
|---|---|---|---|
| **B (recomendada)** | Se quita el 29: el plazo es 120 días desde el encendido, por sensor | MODIS pre-autorizado hasta el 2027-03-02; VIIRS, 120 días desde su encendido | Dos marcas A113; en `scripts/vigilancia_guardia_modis.py` el plazo deja de depender del `orden` (la vigilancia de VIIRS usa la misma función); reescribir tres pruebas y el texto del issue (§5) |
| A | Cada volcán aporta como máximo 10 a las 29, por sensor | En la práctica igual que B: en MODIS nunca cierra por cuenta; en VIIRS 375 cerró 4 de 95, y ya con Chillán | Igual que B más la lógica del tope y su prueba |
| C | Se deja como está | MODIS cierra el 11-19 o 11-20 con 29 de Chillán; desde ahí una candidata se sigue informando y decides tú | Ninguno. Riesgo: leer «29 de 29» como prueba general de la vía |

Recomiendo **B**. Lo que el 29 quería medir sólo vale con casos de varios volcanes, y en los datos de 2026 eso no ocurre
antes de los 120 días: con el tope (A) la cuenta casi nunca cierra, así que A termina siendo B con más código. B es lo
más simple y dice la verdad: la pre-autorización dura 120 días. Si quieres conservar una salida temprana para el día en
que sí haya alertas de varios volcanes, A la conserva (VIIRS 375 la usó en 4 de 95 simulaciones).

Qué significa B para la seguridad: durante 120 días, si la vía calla una protegida, una sesión revierte sin preguntarte
(como hoy dentro del plazo). Después, la candidata se informa y decides tú. No cambian las cotas de investigación (D1,
D2), el veredicto de reversión, la espera de 24 h ni el día después (§4.7). No se toca `pipeline/`.

## 4. Texto de la enmienda (para pegar si eliges B)

En cada regla, bajo la cabecera de sello, como marca A113 (el texto sellado se conserva):

> ⚠️ **Marca A113, 2026-11-«DD» (enmienda de Nicolás, «frase»; auditoría S179, hallazgos 401, DEC-12 y 451)**: en §4.6
> el plazo de la reversión pre-autorizada es 120 días desde el encendido, por sensor; las 29 protegidas dejan de cerrarlo.
> Se siguen contando e informando. Por qué: las 29 dan la potencia declarada (0,953 contra una pérdida de 1 de cada 10)
> sólo si son casos distintos, y medido no lo son. Sin tope, en los encendidos simulados del 2026-04-09 al 07-12 el plazo
> cerró por cuenta en 4, 63 y 51 de 95 (MODIS, VIIRS 375, VIIRS 750), y en 4, 25 y 46 de esos cierres 20 o más de las 29
> eran de un solo volcán (Láscar en abril y mayo, Chillán desde fines de septiembre); con un tope de 10 por volcán
> cerraban por cuenta 0, 4 y 0, y el resto vencía a los 120 días (`experiments/_s179_enmienda_plazo/`). Texto sellado
> conservado.

Si eliges A, la primera frase cambia a: «en §4.6 cada volcán aporta como máximo 10 protegidas a las 29 del plazo, por
sensor; las de un volcán que ya aportó 10 no cuentan ni avanzan el orden, y sus candidatas están dentro del plazo hasta
la 29.ª contada inclusive o mientras el plazo no se cierre».

## 5. Cómo se aplicaría (después de tu frase, no antes)

1. PR a main con: las dos marcas A113; en `scripts/vigilancia_guardia_modis.py::disparadores`, `dentro_de_plazo` pasa a
   ser sólo «anterior al vencimiento de 120 días» y `duracion.cumplida` sólo «hoy pasado el vencimiento» (el conteo de
   `vistas` se sigue informando); el texto del issue en `.github/workflows/vigilancia-guardia-modis.yml` l. 136
   («29 protegidas vistas o 120 días»).
2. Reescribir las tres pruebas vigentes que fijan el cierre con 29 protegidas: `tests/test_vigilancia_guardia_modis_s172.py`
   l. 215, `tests/test_vigilancia_guardia_por_volcan_s175.py` l. 76 a 86 y `tests/test_vigilancia_guardia_viirs_s176.py`
   l. 191. Prueba nueva: 30 protegidas de un volcán, la 30.ª callada, dentro de los 120 días, da REVERSION_CANDIDATA; su
   mutación (el cierre por 29 de vuelta) da CANDIDATA_FUERA_DE_PLAZO. (Para A: 26 de un volcán y 3 de otro; con tope
   cuenta 13 y no cierra, sin tope cuenta 29 y cierra.)
3. No es `pipeline/` ni `data/`: no pide tag A45. Sí pide CI verde, verificador limpio y «mergea #N».
4. Si no está en main antes de que MODIS junte su protegida 29 (hacia el 11-19), la vigilancia cerrará el plazo con la
   regla vieja; la enmienda lo reabre en la corrida siguiente, porque `evaluar` rehace `vistas` y `orden` en cada corrida
   desde los datos y nadie lee el `plazo_cumplido` anterior (comprobado por el verificador).

## 6. Lo que decides

«Enmienda B», «Enmienda A» o «Deja el plazo». Con A o B redacto el PR y lo paso por verificador antes de pedirte el merge.

## 7. Cambios de la ronda 2 (verificador limpio, Fable 5.2, 2026-11-11)

Carpeta del verificador, con sus scripts y salidas: `verificador/` (caminos, arnés sobre el `disparadores` real,
simulador propio). Cambios aplicados: (1) el OCR sí cuenta y el instrumento exige record de producción (la ronda 1 decía
lo contrario); (2) la lectura de §2 decía que en VIIRS la forma actual junta casos distintos en un año normal: es falso,
Láscar cierra solo en abril y mayo; (3) la ronda 1 decía que A no mueve nada en un año normal: en VIIRS pasa de cerrar a
los 21 o 42 días a los 120; (4) la marca A113 citaba sólo la fila del tope, sin la comparación; (5) la prueba de 13 + 3
no podía fallar (16 es menos de 29) y faltaban las tres pruebas vigentes y el texto del issue; (6) docstring del
instrumento corregido. Por (2) y (3) la recomendación pasó de A a B.
