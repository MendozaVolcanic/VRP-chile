# S149: la conectiva `max` en mayo de 2026 (primera ventana del pre-registro v3)

> Run **35599902448**, despachado el 2026-09-21 12:30 UTC desde `0227dd7ac`, 23 de 23 jobs en verde.
> Criterios escritos y commiteados antes de correr (`experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`,
> v2 y enmienda A119 anteriores a esta evaluación). Evaluado con `evaluar_ventana.py`, probado antes
> sobre septiembre. Todos los números salen de `experiments/_s149_prereg_invierno/resultados/mayo_*.txt`.
> **Verificado con contexto limpio: se sostiene, con salvedades** (sección 6; una de ellas corrigió mi
> lectura de la sección 3). **Pendiente**: el control de determinismo (gemelo de Láscar, run 35599941522).
> **No autoriza nada en producción.**

## 0. En una frase

Mayo repite septiembre: con `max`, VIIRS 375 deja de publicar casi todo lo que publicaba donde MIROVA
no vio nada (30,1 a **2,3 %**), el recorte es selectivo, y por la regla pre-registrada (antes del
13 de junio decide la tabla de MIROVA sin OCR) **no se pierde ninguna pasada de 0,5 MW o más**.

## 1. Cobertura, antes de mirar nada

3.682 pasadas, las 3.682 en los dos brazos, 11 volcanes. Pareja.

## 2. VIIRS 375

| predicción | mayo | septiembre (ya publicado) | veredicto |
|---|---|---|---|
| P1, publicación en negativos limpios | 30,1 a **2,3 %** (n 349) | 29,8 a 2,7 % | CUMPLE |
| P2, razón borde sobre nadir | 2,33 a **0,58** | 2,17 a 0,25 | CUMPLE |
| P4, recall por pasada, **tabla sola (decide)** | conserva **187 de 195**, piso 164, 0 pérdidas de 0,5 MW o más | 105 de 107 | CUMPLE |
| P4 con OCR (se informa) | conserva 276 de 288, **2 pérdidas de 0,5 MW o más** | 135 de 137, 0 | ver sección 3 |
| P5, RUTINA en noche con alerta | razón 0,36 contra 0,62 de un apagado parejo (n 159) | 0,37 contra 0,47 | CUMPLE |
| C8b, selectividad a una cola | +0,883 contra +0,517 | +0,891 contra +0,377 | CUMPLE |

La supervivencia de lo que publica el control vuelve a ordenar los tres estratos igual que en
septiembre: negativos limpios **8 %**, RUTINA en noche con alerta **36 %**, positivas **96 %**.

**Villarrica**, que era la razón para mirar mayo (9 pasadas, 8 bajo 0,5 MW, entre 0,05 y 0,55 MW):
el control publica las 9 y `max` **conserva las 9**. Nevados de Chillán: 2 positivas, ninguno de los
dos brazos las publica (las pierde el control, no `max`).

Las 8 pérdidas que decide la tabla están todas entre 0,02 y 0,12 MW: Tupungatito 3, Cordón Caulle 2,
Chaitén 2, Isluga 1.

## 3. Las dos pérdidas grandes, que vienen sólo del OCR

| pasada | OCR de mayo | lo que vio nuestro control | contexto |
|---|---|---|---|
| Lastarria 2026-05-02 05:06, Suomi NPP | 2,36 MW | 0,033 MW, borde del barrido (60 grados) | en todo mayo la TABLA de MIROVA nunca pasó de 0,20 MW en Lastarria (35 alertas, mediana 0,07) |
| Isluga 2026-05-29 04:54, Suomi NPP | 0,86 MW | 0,013 MW a 4,9 km, borde (69 grados) | la tabla llega a 0,74 MW en Isluga ese mes (30 alertas, mediana 0,26) |

Las dos son filas del OCR versión 21, de cuando la geometría estaba mal calibrada y no se medía
distancia (A119), y las dos son de Suomi NPP, que la tabla casi no lista.

**Mi primera lectura estaba mal y el verificador la corrigió.** Escribí que la de Lastarria parecía un
dígito mal leído. No lo es: en los dos gránulos hay una **fuente caliente lejana, real**. En Lastarria
un píxel de 304 K que el brazo F arma como un cúmulo de 1,107 MW a **19,5 km** del cráter; en Isluga
uno de 289 K, 0,49 MW a **18,6 km**. En pasadas vecinas la tabla de MIROVA lista falsos positivos de
magnitud parecida a 16 a 18 km, y esas mismas noches da el cráter en 0,10 a 0,49 MW. O sea que el OCR
leyó bien el número pero, como entonces no medía distancia, **rotuló como alerta del cráter algo que
MIROVA misma clasifica como lejano**: exactamente el defecto que describe A119. Perder esas dos
"alertas" es lo correcto.

**Y un efecto que sí importa**: en esas dos pasadas `max` **mueve el cúmulo primario del cráter a la
fuente lejana** (queda `far` y no se publica). El control veía en el cráter 0,033 y 0,013 MW. Es la
misma competencia por el ancla que frenó el A/B sin Test 1 en S147: cuando `max` apaga el píxel débil
del cráter, el cúmulo primario pasa a ser otro. Acá no cuesta una alerta real, pero es el mecanismo a
vigilar en las ventanas que siguen.

## 4. VIIRS 750 y MODIS (se informan)

- **VIIRS 750**: negativos limpios 9,3 a 1,0 % (P1 INDECIDIBLE por su cláusula: el control ya está bajo
  18 %); recall, conserva 39 de 40 (la perdida, Cordón Caulle con 0,39 MW).
- **MODIS**: con `max` y banda 21 el detector se apaga (0,0 % en negativos), como ya se sabía. Y un
  dato que no se buscaba: **de las 11 pasadas MODIS con alerta de Láscar en mayo, el control B (sin
  Test 1) publica 0**. Eso es del control, no de `max`, y es lo que el brazo de banda 22 (marzo a
  junio, en cola) viene a mirar.

## 5. Qué sigue

Determinismo (gemelo) y las ventanas que siguen en la cola. No se promedia con septiembre: son dos
ventanas que dicen lo mismo por separado.

## 6. Salvedades del verificador con contexto limpio

Informe: `docs/audit_s149/VERIFICADOR_RESULTADO_MAYO.md`. Reimplementó VIIRS 375 leyendo los JSON de
los brazos y los CSV congelados directamente, sin ninguna diferencia de número, y comprobó en los
registros de los 22 jobs que cada brazo leyó el flag que declara.

- **La enmienda de qué etiqueta decide (A119, commit de las 13:48 UTC) es anterior a la evaluación
  (17:32 UTC) pero no a todos los datos**: a esa hora ya habían terminado 6 de los 22 jobs, entre ellos
  los de Lastarria e Isluga. No los descargué ni los miré antes de evaluar (la primera extracción de
  este run es la de `evaluar_ventana.py`), pero eso no se puede probar desde el repo: queda declarado.
  Y no cambia el resultado: excluir las positivas del OCR no favorece a `max`, que entre ellas conserva
  89 de 93 (96 %), la misma tasa que en la tabla.
- **"Los negativos salen siempre de la tabla" no es exacto**: el etiquetador excluye del negativo limpio
  las noches con alerta del OCR. Con la tabla sola de punta a punta P1 da **31,3 a 3,7 %** (n 383) y
  sigue cumpliendo.
- **Por noche**: `max` pierde 2 de 138 noches con alerta de la tabla, Chaitén 05-19 e Isluga 05-25, las
  dos bajo 0,1 MW.
- De las 9 pasadas de Villarrica sólo 4 son de la tabla; las otras 5 vienen del OCR. `max` conserva las 9.
- La composición por volcán de los negativos limpios de mayo no se comparó con la de septiembre
  (SIN VERIFICAR).
- El veredicto "tabla sola" se agregó a `medir_predicciones.py` en el mismo commit del resultado; el
  cambio es mecánico y el verificador comprobó que no altera ningún número.
