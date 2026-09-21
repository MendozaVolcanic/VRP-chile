# S149: la conectiva `max` en mayo de 2026 (primera ventana del pre-registro v3)

> Run **35599902448**, despachado el 2026-09-21 12:30 UTC desde `0227dd7ac`, 23 de 23 jobs en verde.
> Criterios escritos y commiteados antes de correr (`experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`,
> v2 y enmienda A119 anteriores a esta evaluación). Evaluado con `evaluar_ventana.py`, probado antes
> sobre septiembre. Todos los números salen de `experiments/_s149_prereg_invierno/resultados/mayo_*.txt`.
> **Pendiente**: el control de determinismo (gemelo de Láscar, run 35599941522, corriendo al escribir
> esto) y un verificador con contexto limpio, obligatorio porque la mejora supera el 30 %.
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
distancia (A119), y las dos son de Suomi NPP, que la tabla casi no lista. La de Lastarria tiene todo
el aspecto de un dígito mal leído (doce veces el máximo del mes); la de Isluga es plausible.
**SIN VERIFICAR**: busqué las imágenes originales en el repo del scraper y esas carpetas ya no están.
No se descartan por conveniencia: la regla de que decide la tabla se escribió antes de evaluar, y acá
quedan informadas para que el verificador las mire.

## 4. VIIRS 750 y MODIS (se informan)

- **VIIRS 750**: negativos limpios 9,3 a 1,0 % (P1 INDECIDIBLE por su cláusula: el control ya está bajo
  18 %); recall, conserva 39 de 40 (la perdida, Cordón Caulle con 0,39 MW).
- **MODIS**: con `max` y banda 21 el detector se apaga (0,0 % en negativos), como ya se sabía. Y un
  dato que no se buscaba: **de las 11 pasadas MODIS con alerta de Láscar en mayo, el control B (sin
  Test 1) publica 0**. Eso es del control, no de `max`, y es lo que el brazo de banda 22 (marzo a
  junio, en cola) viene a mirar.

## 5. Qué sigue

Determinismo (gemelo), verificador con contexto limpio, y las ventanas que siguen en la cola. No se
promedia con septiembre: son dos ventanas que dicen lo mismo por separado.
