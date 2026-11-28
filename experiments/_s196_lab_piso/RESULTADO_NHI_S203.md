# Resultado de la vara NHI para la zona A con s 3 y piso 0,0025: NO CUMPLE (S203, guardado en S204)

> ⚠️ **S204, corrección tras la ronda 6 de Codex (frente N), verificada por un Claude de contexto limpio** (A113;
> `D:\codex-vrp\_salida\ronda6\fn_r6_verificacion\VEREDICTO.md`; registro `D:\codex-vrp\_salida\ronda6\hallazgos_verificados.csv`).
> **El veredicto NO CUMPLE se mantiene**: la vara se reproduce campo por campo desde los insumos, y ninguno de los
> caminos encontrados la cambia. Lo que no se sostiene es parte de la lectura de este informe:
>
> 1. **«Instrumento sano» (§2) era falso en la cobertura** (R6FN-102, gravedad 3). La vara carga 232 pasadas MODIS de
>    día de producción (Terra 110, Aqua 122, todas desde el 2026-11-15) que el laboratorio no tiene; explican 117 de las
>    119 noches con cobertura desigual. El 3,9 a 4,6 % era casi entero ese artefacto, no una medida de salud. Sin el día,
>    la cobertura desigual baja a 0 a 0,7 % y el veredicto sigue NO CUMPLE con el mismo único exceso
>    (Planchón-Peteroa, 4 de 12 contra 2 de 45, p 0,015; Tupungatito 22/32, Chaitén 18/29; persistencia 0,642 contra
>    0,698, 935 extras): `resultado_nhi_s203_sin_modis_diurno_r6.json`, `salida_diurno_r6_verificador.txt`.
> 2. **La vara se habría invalidado sola en pocos días** (R6FN-V201, gravedad 3): cada día con MODIS diurno suma una
>    noche desigual por volcán, así que con fin entre el 2026-11-28 (Llaima) y el 11-30 habría dado INVALIDO sin que
>    nada del laboratorio cambiara (`salida_proyeccion_cobertura_r6_verificador.txt`). No afecta a esta corrida (fin
>    11-26), pero un segundo intento con esta vara tiene que arreglar antes el cargador, y eso exige pre-registro nuevo.
> 3. **El exceso mínimo de §3 no es la frontera de la prueba que votó** (R6FN-104): es la cuenta sin estratos de
>    nubosidad. Con estratos, el mínimo de Chaitén va de 5 a 11 alertas según cómo se repartan las nubes (8 plano).
> 4. **«Puntos fijos» (§4) no sale de la prueba** (R6FN-106): no superar al sorteo temporal no identifica un punto fijo;
>    en 9 de 10 volcanes lo persistente queda bajo el sorteo, y Llaima (0,029) y Copahue (0,000) casi no persisten.
> 5. **Chillán sí tiene más alertas NHI tras las noches «sólo laboratorio»** (2/13 = 0,154 contra 7/62 = 0,113,
>    R6FN-107): lo que falta es significancia (p 0,56), no aumento.
> 6. **«Para ella decide NHI» (§4) contradice la regla** (R6FN-112): CUMPLE exige exceso NHI **y** persistencia; una fuente
>    real fija con exceso NHI en los nueve volcanes igual da NO CUMPLE.
> 7. La unión del laboratorio admite huecos y solapes sin chequear las ventanas contra los datos (R6FN-103, gravedad 2):
>    en esta corrida no dejó huecos ni solapes; sí faltan 14 pasadas Aqua nocturnas del 25-nov en el laboratorio
>    (R6FN-110), causa SIN DATO, sin efecto en ningún voto.
>
> El texto de abajo se conserva tal como se escribió; cada frase afectada lleva su marca.

Paso 5 del plan S190 (`docs/PLAN_EXPERIMENTAL_S190.md` §7). Vara: la del pre-registro S194 (`experiments/_s194_lab_zona_a/PREREGISTRO.md` §3 y §4), que el S196 usa sin cambios (`PREREGISTRO.md` §6). Valor de la zona A: el ELEGIDO por calibrar (`RESULTADO_CALIBRAR_S203.md`), igual al perfil `laboratorio` encendido en #1144 (ficha v1.120).

## 1. Qué se preguntó, como fenómeno

En el cráter, de noche y con cielo quieto, el detector de MIROVA tiene un piso fijo que deja fuera focos chicos aunque contrasten con un fondo parejo. El laboratorio bajó ese freno sólo en la zona del cráter (s 3 y piso 0,0025) y publicó más noches que producción. La pregunta: esas noches de más, ¿son calor real? La vara no puede ser MIROVA (A115), porque lo agregado es justo lo que MIROVA no publica. Se usa el SWIR de alta resolución (NHI, Sentinel 2 y Landsat, de día): si las noches «sólo laboratorio» (S) son calor real, NHI debería ver calor en el volcán al día siguiente más a menudo que tras las noches en que nadie publica (N). Y lo que aparece de más debería repetirse en el mismo lugar más de lo que da el azar.

## 2. Resultado

`evaluar.py evaluar` corrido desde main 67c653d2d, ventana 2026-02-15 a 2026-11-26, laboratorio = unión del brazo p250 (31.933 records, 0 problemas; `unir_lab_p250.py`, `salida_unir_lab_p250_s203.txt`). Salida: `resultado_nhi_s203.json`, `salida_nhi_s203.txt`.

**NO CUMPLE.** Motivos del evaluador: exceso NHI con p < 0,05 en 1 volcán (hacían falta 4); la persistencia no supera al sorteo temporal.

| volcán | noches S | noches N | alertas NHI tras S | alertas NHI tras N | p | voto |
|---|---|---|---|---|---|---|
| Láscar | 3 | 20 | 0 | 2 | 1,0 | SIN PODER |
| Isluga | 3 | 13 | 0 | 6 | 1,0 | SIN PODER |
| Tupungatito | 21 | 30 | 0 | 2 | 1,0 | sin exceso |
| Planchón-Peteroa | 12 | 42 | 4 | 2 | 0,017 | **exceso** |
| Nevados de Chillán | 13 | 62 | 2 | 7 | 0,56 | sin exceso |
| Llaima | 2 | 91 | 0 | 33 | 1,0 | SIN PODER |
| Villarrica | 9 | 67 | 3 | 14 | 0,16 | SIN PODER |
| Copahue | 6 | 115 | 1 | 19 | 0,57 | SIN PODER |
| Chaitén | 17 | 27 | 2 | 4 | 0,76 | sin exceso |

Persistencia (sorteo temporal, el que vota): 912 detecciones extra, fracción persistente observada 0,637 contra 0,695 del sorteo, p 1,0: no supera. El sorteo uniforme, informativo, da 0,074 (p 0,0005): las extras no caen al azar dentro de la zona A, caen en lugares fijos.

(⚠️ S204: la parte de la cobertura no se sostiene, corrección 1 y 2 arriba.) Instrumento: control con las fechas NHI corridas ±15 días nulo (0 volcanes con exceso en cada desplazamiento); cobertura desigual de 3,9 a 4,6 % de las noches por volcán (el límite es 5 %). El NO CUMPLE no es una falla del instrumento.

## 3. Exceso mínimo detectable (lo que exige S194 §4.5 para un NO CUMPLE)

`exceso_minimo_s204.py` (salida `salida_exceso_minimo_s204.txt`) aplica la función sellada `minimo_detectable` (hipergeométrica exacta de una cola, sin los estratos de nubosidad de la prueba que votó: orden de magnitud, no frontera exacta) a los n reales de esta corrida.

| volcán | tasa NHI basal (N) | tasa tras S | mínimo detectable tras S | exceso mínimo |
|---|---|---|---|---|
| Tupungatito | 0,067 | 0,000 | 6 de 21 (0,286) | 0,219 |
| Planchón-Peteroa | 0,048 | 0,333 | 4 de 12 (0,333) | 0,286 |
| Nevados de Chillán | 0,113 | 0,154 | 5 de 13 (0,385) | 0,272 |
| Chaitén | 0,148 | 0,118 | 8 de 17 (0,471) | 0,322 |
| Villarrica (sin poder) | 0,209 | 0,333 | 5 de 9 (0,556) | 0,347 |
| Copahue (sin poder) | 0,165 | 0,167 | 4 de 6 (0,667) | 0,501 |
| Láscar (sin poder) | 0,100 | 0,000 | 3 de 3 (1,000) | 0,900 |
| Isluga, Llaima (sin poder) | 0,462 y 0,363 | 0 | ni con todas las noches S en alerta | sin mínimo |

(⚠️ S204: cuenta sin estratos, corrección 3 arriba.) Con nueve meses de NHI la vara sólo puede ver un exceso de 22 a 32 puntos porcentuales en los cuatro volcanes con poder. Un exceso real más chico que eso no se distingue: NO CUMPLE con este poder no es «no hay señal».

## 4. Lectura geológica

- (⚠️ S204: no sale de la prueba, y «para ella decide NHI» contradice la regla; correcciones 4 y 6 arriba.) **Lo que se ve de más está en lugares fijos.** Las extras se repiten a menos de 1 km de detecciones previas del laboratorio (0,637), pero igual o más cerca de detecciones de noches lejanas (0,695). Es la firma de un punto tibio de siempre (borde de cráter, campo fumarólico estable, relieve o nieve que contrasta de noche), no de un foco nuevo que aparece y se mantiene unos días. La salvedad del S194 (debilidad 5) sigue en pie: una fuente real que no se mueve en meses tampoco supera este sorteo; para ella decide NHI.
- (⚠️ S204: falso para Chillán, corrección 5 arriba.) **NHI no ve más calor tras las noches «sólo laboratorio»** en Tupungatito (0 de 21), Chillán (2 de 13 contra 7 de 62) ni Chaitén (2 de 17 contra 4 de 27).
- **Planchón-Peteroa es la excepción:** 4 de 12 contra 2 de 42. Que al menos uno de los cuatro volcanes con poder dé p < 0,05 por puro azar tiene probabilidad 0,185 (`E.prob_al_menos(1, 4, 0,05)`; 0,370 si fueran los nueve); el control con fechas corridas no lo repite, pero la prueba se diseñó para pedir 4 volcanes justamente por eso. Queda como pregunta abierta para el experimental, sin decidir nada (opción c del bloque S204).

## 5. Qué hace este resultado (S194 §4.5)

La zona A no llega a cron. Se anota en `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 (MEJ-5) con estos números. No se re-corre con otro umbral, otra ventana u otro estrato sin un pre-registro nuevo que diga que es el segundo intento. El perfil `laboratorio` encendido (#1144) no corre en ningún workflow ni publica.

## 6. Archivos

| archivo | qué |
|---|---|
| `resultado_nhi_s203.json` | salida de `evaluar.py evaluar` (copia de `D:\vrp-trabajo\temporales\s203\evaluar_nhi\resultado.json`) |
| `salida_nhi_s203.txt` | su salida de consola |
| `unir_lab_p250.py` | arma la carpeta del laboratorio (unión t1 a t10 del brazo p250 más t11 run 46013914740 y t12 run 46013941632) |
| `salida_unir_lab_p250_s203.txt` | su salida: records por volcán, 0 problemas |
| `exceso_minimo_s204.py` | exceso mínimo detectable por volcán con la función sellada |
| `salida_exceso_minimo_s204.txt` | su salida |

Reproducir: `python experiments/_s196_lab_piso/evaluar.py evaluar --lab <unión p250> --nhi-dir <carpeta> --bajar-nhi --fin 2026-11-26 --out resultado.json` (NHI de NHI-v1 `main` bajado al correr; la serie NHI crece, así que una corrida posterior puede diferir en las últimas noches) y `python experiments/_s196_lab_piso/exceso_minimo_s204.py experiments/_s196_lab_piso/resultado_nhi_s203.json`.
